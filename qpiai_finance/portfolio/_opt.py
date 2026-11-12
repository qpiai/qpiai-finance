"""Compile portfolio decisions to QpiAI Opt models."""

import numpy as np
from scipy import sparse

from .._arithmetic import product_sum, row_products
from .._solvers._expressions import linear as _linear
from .._solvers._expressions import quadratic as _quadratic
from ..risk import FactorRisk, expected_shortfall_epigraph


def _add_selection_constraints(portfolio, model, weights, fixed_conflicts):
    from qpiai_opt.opt_modeller import Binary, quicksum

    if portfolio._selection is None:
        return
    if portfolio._fixed_selection is not None:
        if not fixed_conflicts.any():
            return
        lower, upper = portfolio._fixed_weight_bounds()
        for i in np.flatnonzero(fixed_conflicts):
            model.add_constraint(weights[i] >= float(lower[i]))
            model.add_constraint(weights[i] <= float(upper[i]))
        return
    selection = portfolio._selection
    positive = model.add_variables(
        [Binary(f"selected_positive_{i}") for i in range(len(weights))]
    )
    negative = model.add_variables(
        [Binary(f"selected_negative_{i}") for i in range(len(weights))]
    )
    for i, weight in enumerate(weights):
        model.add_constraint(positive[i] + negative[i] <= 1)
        if selection["equal_weight"]:
            model.add_constraint(negative[i] == 0)
            model.add_constraint(
                weight
                == portfolio._net_weight / selection["count"] * positive[i]
            )
        else:
            minimum = selection["minimum_weight"]
            model.add_constraint(
                weight
                >= minimum * positive[i]
                + min(0.0, float(portfolio._lower[i])) * negative[i]
            )
            model.add_constraint(
                weight
                <= max(0.0, float(portfolio._upper[i])) * positive[i]
                - minimum * negative[i]
            )
    chosen = quicksum(positive) + quicksum(negative)
    if selection["count"] is not None:
        model.add_constraint(
            chosen == selection["count"], label="selected_asset_count"
        )
    else:
        model.add_constraint(
            chosen <= selection["maximum"], label="selected_asset_count"
        )


def _variance_expression(portfolio, model, weights):
    from qpiai_opt.opt_modeller import Continuous

    benchmark = portfolio._benchmark
    if benchmark is None:
        benchmark = np.zeros(len(weights))

    if not isinstance(portfolio._covariance, FactorRisk):
        variance = _quadratic(weights, portfolio._covariance)
        if portfolio._benchmark is not None:
            covariance_benchmark = portfolio._risk_apply(
                benchmark, original=True
            )
            variance += _linear(weights, -2 * covariance_benchmark)
            variance += float(product_sum((benchmark, covariance_benchmark)))
        return variance

    risk = portfolio._covariance
    asset_order = portfolio._ids.get_indexer(risk._assets)
    ordered_weights = [weights[i] for i in asset_order]
    ordered_benchmark = benchmark[asset_order]
    factor_exposures = model.add_variables(
        [
            Continuous(f"factor_{i}", -float("inf"), float("inf"))
            for i in range(len(risk._factors))
        ]
    )

    loadings = sparse.csr_matrix(risk._b.T)
    for i, exposure in enumerate(factor_exposures):
        row = loadings.getrow(i)
        positions = [ordered_weights[j] for j in row.indices]
        portfolio_exposure = _linear(positions, row.data)
        benchmark_exposure = float(next(row_products(row, ordered_benchmark)))
        model.add_constraint(
            exposure == portfolio_exposure - benchmark_exposure,
            label=f"factor_balance_{i}",
        )

    systematic_risk = _quadratic(factor_exposures, risk._f)
    specific_risk = 0
    for variance, weight, benchmark_weight in zip(
        risk._d, ordered_weights, ordered_benchmark
    ):
        active_weight = weight - float(benchmark_weight)
        specific_risk += float(variance) * active_weight**2
    return systematic_risk + specific_risk


def compile_model(portfolio):
    """Compile an independent Opt Model, retaining sparse and factor
    structure.
    """
    from qpiai_opt.opt_modeller import Continuous, Model, quicksum

    portfolio._check()
    if portfolio._objective == "moment_utility":
        raise ValueError(
            "use quantum.compile_portfolio for binary moment utility"
        )
    if portfolio._objective == "hrp":
        raise ValueError("HRP is a construction method, not an Opt program")
    if portfolio._needs_external:
        solver = "clarabel"
        if (
            portfolio._mixed_integer
            and portfolio._objective != "risk_budgeting"
        ):
            solver = "scip"
        raise ValueError(
            "this formulation requires a conic backend or "
            "mixed-integer quadratic solver; "
            f"select solver='{solver}'"
        )
    model = Model("portfolio")
    lower, upper, fixed_conflicts = portfolio._allocation_bounds()
    weights = model.add_variables(
        [
            Continuous(f"weight_{i}", float(lower_bounds), float(upper_bounds))
            for i, (lower_bounds, upper_bounds) in enumerate(
                zip(lower, upper)
            )
        ]
    )
    cash, costs = None, 0
    if portfolio._account is None:
        model.add_constraint(
            quicksum(weights) == portfolio._net_weight,
            label="investment_basis",
        )
    else:
        cash, costs = portfolio._account.add_opt(
            model, weights, portfolio._lower, portfolio._upper
        )
    _add_selection_constraints(portfolio, model, weights, fixed_conflicts)
    forecast = (
        None if portfolio._mu is None else _linear(weights, portfolio._mu)
    )
    cash_income = 0 if cash is None else portfolio._account.cash_return * cash
    if forecast is not None:
        forecast = forecast + cash_income - costs
    if portfolio._minimum_return is not None:
        model.add_constraint(
            forecast >= portfolio._minimum_return, label="minimum_return"
        )
    for ids, values, lower_bounds, upper_bounds in portfolio._exposures:
        rows = sparse.csr_matrix(values)
        for i in range(len(ids)):
            row = rows.getrow(i)
            expr = _linear([weights[j] for j in row.indices], row.data)
            group = len(model.constraints)
            model.add_constraint(
                expr >= float(lower_bounds[i]),
                label=f"exposure_lower_{group}",
            )
            model.add_constraint(
                expr <= float(upper_bounds[i]),
                label=f"exposure_upper_{group}",
            )
    if portfolio._leverage is not None:
        absolute = model.add_variables(
            [Continuous(f"absolute_{i}") for i in range(len(weights))]
        )
        for i in range(len(weights)):
            model.add_constraint(absolute[i] >= weights[i])
            model.add_constraint(absolute[i] >= -weights[i])
        model.add_constraint(
            quicksum(absolute) <= portfolio._leverage, label="gross_exposure"
        )
    if portfolio._turnover is not None:
        current, limit = portfolio._turnover
        changes = model.add_variables(
            [Continuous(f"turnover_{i}") for i in range(len(weights))]
        )
        for i in range(len(weights)):
            model.add_constraint(changes[i] >= weights[i] - float(current[i]))
            model.add_constraint(changes[i] >= float(current[i]) - weights[i])
        model.add_constraint(quicksum(changes) <= limit, label="turnover")

    if portfolio._objective == "utility":
        variance = 0
        if portfolio._risk_aversion > 0:
            variance = _variance_expression(portfolio, model, weights)
        model.maximize(forecast - portfolio._risk_aversion / 2 * variance)
    elif portfolio._objective in {"variance", "tracking_error"}:
        model.minimize(_variance_expression(portfolio, model, weights))
    else:
        scenarios = portfolio._scenarios
        returns = sparse.csr_matrix(scenarios._values)
        probabilities = scenarios._probabilities
        auxiliaries = (
            []
            if portfolio._objective == "expected_shortfall"
            else model.add_variables(
                [Continuous(f"tail_{i}") for i in range(len(probabilities))]
            )
        )
        losses = []
        if portfolio._objective == "mean_absolute_deviation":
            mean = np.asarray(probabilities @ returns).ravel()
        for i in range(len(probabilities)):
            row = returns.getrow(i)
            scenario_return = (
                _linear([weights[j] for j in row.indices], row.data)
                + cash_income
                - costs
            )
            if portfolio._objective == "expected_shortfall":
                losses.append(-scenario_return)
            elif portfolio._objective == "mean_absolute_deviation":
                deviation = scenario_return - (
                    _linear(weights, mean) + cash_income - costs
                )
                model.add_constraint(auxiliaries[i] >= deviation)
                model.add_constraint(auxiliaries[i] >= -deviation)
            else:
                model.add_constraint(
                    auxiliaries[i]
                    >= portfolio._downside_target - scenario_return
                )
        if portfolio._objective == "expected_shortfall":
            expression, constraints = expected_shortfall_epigraph(
                losses,
                probabilities=probabilities,
                confidence=portfolio._confidence,
            )
            for constraint in constraints:
                model.add_constraint(constraint)
            model.minimize(expression)
        else:
            model.minimize(_linear(auxiliaries, probabilities))
    return model
