"""Supplied repriced hedge P&L, cost carry and finite-scenario loss risk."""

from fractions import Fraction

import numpy as np
import pandas as pd
from scipy import sparse

from .._arithmetic import probability_masses, row_products, weighted_mean
from .._solvers._expressions import linear
from .._validation import same_labels, vector
from ..risk import _tail_mean, expected_shortfall_epigraph
from ..scenarios import Scenarios


def prepare(hedge, scenarios, current_pnl, cost_factors):
    if type(scenarios) is not Scenarios:
        raise TypeError("scenarios must be Scenarios")
    if scenarios.unit != "pnl_per_unit":
        raise ValueError("hedge scenarios require unit='pnl_per_unit'")
    same_labels(scenarios.asset_ids, hedge._ids, "scenario instruments")
    cases = scenarios.scenario_ids
    baseline = vector(current_pnl, cases, "current_pnl", broadcast=True)
    factors = vector(cost_factors, cases, "cost_factors", broadcast=True)
    if np.any(factors <= 0):
        raise ValueError("cost_factors must be positive")
    if scenarios._probabilities is None and (
        hedge._es_limit is not None
        or hedge._objective == "hedge_expected_shortfall"
    ):
        raise ValueError(
            "configured expected shortfall requires probabilities"
        )
    limits = hedge._loss_limit
    if limits is not None:
        previous = hedge._pnl_scenarios.scenario_ids
        same_labels(cases, previous, "cases with configured loss limits")
        limits = pd.Series(limits, index=previous).reindex(cases).to_numpy()
    values = scenarios._values[:, scenarios.asset_ids.get_indexer(hedge._ids)]
    data = Scenarios(
        values,
        horizon=scenarios.horizon,
        unit=scenarios.unit,
        probabilities=scenarios._probabilities,
        asset_ids=hedge._ids,
        scenario_ids=cases,
        origin=scenarios.origin,
        metadata=scenarios.metadata,
    )
    return data, baseline, factors, limits


def compile_opt(hedge, model, raw, scales, costs):
    from qpiai_opt.opt_modeller import Continuous

    h = hedge
    if h._pnl_scenarios is None or (
        h._loss_limit is None
        and h._es_limit is None
        and h._objective
        not in {"hedge_expected_shortfall", "hedge_worst_loss"}
    ):
        return None
    # Reuse one cost column rather than repeating every instrument fee in
    # every scenario row, especially when the repricing matrix is sparse.
    total = model.add_variable(Continuous("scenario_trade_cost"))
    model.add_constraint(total == costs, label="scenario_cost_balance")
    rows = sparse.csr_matrix(h._pnl_scenarios._values)
    losses = []
    for s in range(len(h._current_pnl)):
        row = rows.getrow(s)
        loss = (
            -float(h._current_pnl[s])
            - linear(
                [raw[i] for i in row.indices], row.data * scales[row.indices]
            )
            + float(h._cost_factors[s]) * total
        )
        losses.append(loss)
        if h._loss_limit is not None:
            model.add_constraint(
                loss <= float(h._loss_limit[s]), label=f"scenario_loss_{s}"
            )

    def tail(level, name):
        expression, constraints = expected_shortfall_epigraph(
            losses,
            probabilities=h._pnl_scenarios._probabilities,
            confidence=level,
            name=name,
        )
        for s, constraint in enumerate(constraints):
            model.add_constraint(constraint, label=f"{name}_tail_{s}")
        return expression

    if h._es_limit is not None:
        cap, level = h._es_limit
        model.add_constraint(
            tail(level, "hard_hedge_es") <= cap,
            label="hedge_expected_shortfall",
        )
    if h._objective == "hedge_expected_shortfall":
        return tail(h._confidence, "objective_hedge_es")
    if h._objective == "hedge_worst_loss":
        worst = model.add_variable(
            Continuous("worst_hedge_loss", -float("inf"), float("inf"))
        )
        for s, loss in enumerate(losses):
            model.add_constraint(worst >= loss, label=f"worst_case_{s}")
        return worst
    return None


def compile_cvxpy(hedge, quantities, costs, constraints):
    import cvxpy as cp

    h = hedge
    if h._pnl_scenarios is None or (
        h._loss_limit is None
        and h._es_limit is None
        and h._objective
        not in {"hedge_expected_shortfall", "hedge_worst_loss"}
    ):
        return None
    losses = (
        -h._current_pnl
        - h._pnl_scenarios._values @ quantities
        + cp.multiply(h._cost_factors, costs)
    )
    if h._loss_limit is not None:
        constraints.append(losses <= h._loss_limit)

    def tail(level):
        expression, inequalities = expected_shortfall_epigraph(
            losses,
            probabilities=h._pnl_scenarios._probabilities,
            confidence=level,
            backend="cvxpy",
        )
        constraints.extend(inequalities)
        return expression

    if h._es_limit is not None:
        cap, level = h._es_limit
        constraints.append(tail(level) <= cap)
    if h._objective == "hedge_expected_shortfall":
        return tail(h._confidence)
    if h._objective == "hedge_worst_loss":
        worst = cp.Variable()
        constraints.append(worst >= losses)
        return worst
    return None


def evaluate(hedge, quantities, cost, check):
    h = hedge
    scenarios = h._pnl_scenarios
    if scenarios is None:
        return None, {}, None
    pnl, carried_cost, net, losses = np.empty((4, len(h._current_pnl)))
    source_losses = np.empty(len(h._current_pnl), dtype=object)
    changes = row_products(scenarios._values, quantities)
    for s, (before, change) in enumerate(zip(h._current_pnl, changes)):
        carried = Fraction(h._cost_factors[s]) * cost
        after = Fraction(before) + change - carried
        loss = -after
        source_losses[s] = loss
        pnl[s], carried_cost[s], net[s], losses[s] = map(
            float, (change, carried, after, loss)
        )
        if h._loss_limit is not None:
            check(
                f"scenario_loss[{s}:{scenarios.scenario_ids[s]}]",
                losses[s],
                -np.inf,
                h._loss_limit[s],
                h.currency,
                violation=float(max(loss - Fraction(h._loss_limit[s]), 0)),
            )
    if not all(np.isfinite(v).all() for v in (pnl, carried_cost, net, losses)):
        raise ValueError("hedge scenario P&L exceeds float64 range")
    probabilities = scenarios._probabilities
    expected_pnl = None
    if probabilities is not None:
        expected_pnl = -float(weighted_mean(source_losses, probabilities))
    metrics = {
        "worst_case_loss": float(max(source_losses)),
        "expected_pnl": expected_pnl,
        "scenario_horizon": scenarios.horizon,
    }
    if metrics["expected_pnl"] is not None and not np.isfinite(
        metrics["expected_pnl"]
    ):
        raise ValueError("expected hedge P&L exceeds float64 range")

    if h._objective == "hedge_expected_shortfall" or h._es_limit is not None:
        masses, total = probability_masses(probabilities)
        order = np.argsort(source_losses, kind="stable")[::-1]
        ordered_losses = source_losses[order]

    def tail(level):
        return _tail_mean(ordered_losses, masses[order], total, level)

    objective = None
    if h._objective == "hedge_expected_shortfall":
        objective = float(tail(h._confidence))
        metrics["expected_shortfall"] = objective
        metrics["expected_shortfall_confidence"] = h._confidence
    elif h._objective == "hedge_worst_loss":
        objective = metrics["worst_case_loss"]
    if h._es_limit is not None:
        maximum, level = h._es_limit
        value = tail(level)
        check(
            "expected_shortfall",
            float(value),
            -np.inf,
            maximum,
            h.currency,
            violation=float(max(value - Fraction(maximum), 0)),
        )
        metrics["constrained_expected_shortfall"] = float(value)
        metrics["constrained_expected_shortfall_confidence"] = level
    table = pd.DataFrame(
        {
            "before_pnl": h._current_pnl.copy(),
            "hedge_pnl": pnl,
            "trading_cost_at_horizon": carried_cost,
            "net_pnl": net,
            "loss": losses,
        },
        index=scenarios.scenario_ids,
    )
    if probabilities is not None:
        table["probability"] = probabilities.copy()
    if h._loss_limit is not None:
        table["maximum_loss"] = h._loss_limit.copy()
    table.attrs.update(currency=h.currency, horizon=scenarios.horizon)
    return objective, metrics, table
