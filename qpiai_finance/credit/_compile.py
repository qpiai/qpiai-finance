"""Credit allocation LP/MILP with exact policy and scenario constraints."""

from fractions import Fraction

import numpy as np
from scipy import sparse

from .._solvers._expressions import linear
from .._validation import group_members, lot_capacity, lot_minimum
from ..risk import _shortfall_form


def compile_model(credit):
    from qpiai_opt.opt_modeller import Binary, Continuous, Integer, Model

    model = Model("credit_allocation")
    count = len(credit._ids)
    scales = np.ones(count) if credit._lots is None else credit._lots
    variables = model.add_variables(
        [
            (Continuous if credit._lots is None else Integer)(
                f"allocation_{i}",
                0,
                float(credit._upper[i])
                if credit._lots is None
                else lot_capacity(credit._upper[i], scales[i]),
            )
            for i in range(count)
        ]
    )
    amounts = [float(scale) * value for scale, value in zip(scales, variables)]
    for i, variable in enumerate(variables):
        if credit._lower[i] > 0:
            minimum = (
                credit._lower[i]
                if credit._lots is None
                else lot_minimum(credit._lower[i], scales[i])
            )
            model.add_constraint(
                variable >= float(minimum), label=f"minimum_{i}"
            )
    if credit._selection is not None:
        minimum, maximum_count = credit._selection
        active = model.add_variables(
            [Binary(f"selected_{i}") for i in range(count)]
        )
        for i, variable in enumerate(variables):
            lower = minimum[i]
            upper = credit._upper[i]
            if credit._lots is not None:
                lower = lot_minimum(lower, scales[i])
                upper = lot_capacity(upper, scales[i])
            model.add_constraint(
                variable >= float(lower) * active[i],
                label=f"active_minimum_{i}",
            )
            model.add_constraint(
                variable <= float(upper) * active[i],
                label=f"active_upper_{i}",
            )
        model.add_constraint(
            linear(active, np.ones(count)) <= maximum_count,
            label="facility_count",
        )
    for name, coefficients, maximum in (
        ("funding", credit._funding, credit._funding_limit),
        ("capital", credit._capital, credit._capital_limit),
    ):
        if np.isfinite(maximum):
            model.add_constraint(
                linear(variables, coefficients * scales) <= float(maximum),
                label=name,
            )
    for block, (ids, values, lower, upper) in enumerate(credit._exposures):
        values = sparse.csr_matrix(values)
        for i in range(len(ids)):
            row = values.getrow(i)
            exposure = linear(
                [variables[j] for j in row.indices],
                row.data * scales[row.indices],
            )
            model.add_constraint(
                exposure >= float(lower[i]),
                label=f"exposure_lower_{block}_{i}",
            )
            model.add_constraint(
                exposure <= float(upper[i]),
                label=f"exposure_upper_{block}_{i}",
            )
    if credit._concentrations:
        total_exposure = model.add_variable(
            Continuous("total_exposure", 0, float("inf"))
        )
        model.add_constraint(
            total_exposure == linear(variables, credit._ead * scales),
            label="total_exposure_balance",
        )
    for block, (groups, ids, shares) in enumerate(credit._concentrations):
        for i, positions in enumerate(group_members(groups, ids)):
            members = np.asarray(positions, dtype=int)
            model.add_constraint(
                linear(
                    [variables[j] for j in members],
                    credit._ead[members] * scales[members],
                )
                <= float(shares[i]) * total_exposure,
                label=f"concentration_{block}_{i}",
            )
    _, margin = credit._income_margins()
    try:
        coefficients = np.fromiter(
            (value * Fraction(scale) for value, scale in zip(margin, scales)),
            dtype=float,
        )
    except OverflowError as error:
        raise ValueError(
            "credit income coefficients exceed float64 range"
        ) from error
    objective = linear(variables, coefficients)
    cost_indices = np.flatnonzero(
        (credit._increase_cost != 0) | (credit._decrease_cost != 0)
    )
    costs = []
    if len(cost_indices):
        costs = model.add_variables(
            [
                Continuous(f"change_cost_{i}", 0, float("inf"))
                for i in cost_indices
            ]
        )
        objective -= linear(costs, np.ones(len(costs)))
    for i, cost in zip(cost_indices, costs):
        increase, decrease = credit._increase_cost[i], credit._decrease_cost[i]
        change = amounts[i] - float(credit._current[i])
        model.add_constraint(
            cost >= float(increase) * change, label=f"increase_cost_{i}"
        )
        model.add_constraint(
            cost >= -float(decrease) * change, label=f"decrease_cost_{i}"
        )

    scenarios = credit._scenarios
    if (
        credit._scenario_limit is not None
        or credit._risk_aversion > 0
        or credit._tail_limit is not None
    ):
        values = sparse.csr_matrix(scenarios._values)
        losses = []
        for s in range(len(scenarios._ids)):
            row = values.getrow(s)
            loss = linear(
                [variables[j] for j in row.indices],
                row.data * scales[row.indices],
            )
            losses.append(loss)
            if credit._scenario_limit is not None:
                model.add_constraint(
                    loss <= float(credit._scenario_limit[s]),
                    label=f"scenario_loss_{s}",
                )
        tail_confidences = set()
        if credit._risk_aversion > 0:
            tail_confidences.add(credit._confidence)
        if credit._tail_limit is not None:
            tail_confidences.add(credit._tail_limit[1])
        for k, beta in enumerate(sorted(tail_confidences)):
            coefficients, inequalities = _shortfall_form(
                scenarios._probabilities, beta
            )
            # Nonnegative credit losses allow a nonnegative VaR threshold.
            threshold = model.add_variable(
                Continuous(f"tail_threshold_{k}", 0, float("inf"))
            )
            excess = model.add_variables(
                [
                    Continuous(f"tail_excess_{k}_{s}", 0, float("inf"))
                    for s in range(len(losses))
                ]
            )
            auxiliaries = [threshold] + excess
            for s, loss in enumerate(losses):
                row = inequalities.getrow(s)
                model.add_constraint(
                    linear([auxiliaries[j] for j in row.indices], row.data)
                    >= loss,
                    label=f"tail_loss_{k}_{s}",
                )
            tail = linear(auxiliaries, coefficients)
            if credit._risk_aversion > 0 and beta == credit._confidence:
                objective -= credit._risk_aversion * tail
            if (
                credit._tail_limit is not None
                and beta == credit._tail_limit[1]
            ):
                model.add_constraint(
                    tail <= credit._tail_limit[0],
                    label="expected_shortfall_limit",
                )
    model.maximize(objective)
    return model
