"""Compile portfolio decisions to convex and mixed-integer CVXPY models."""

import numpy as np

from .._arithmetic import product_sum, row_products
from ..risk import FactorRisk, expected_shortfall_epigraph


def _variance_expression(portfolio, positions, *, benchmark=None):
    import cvxpy as cp

    risk = portfolio._covariance
    if isinstance(risk, FactorRisk):
        order = portfolio._ids.get_indexer(risk._assets)
        ordered = positions[order]
        factor_exposure = risk._b.T @ ordered
        if benchmark is not None:
            ordered_benchmark = benchmark[order]
            benchmark_exposure = np.fromiter(
                (
                    float(value)
                    for value in row_products(risk._b.T, ordered_benchmark)
                ),
                dtype=float,
            )
            factor_exposure -= benchmark_exposure
            ordered = ordered - ordered_benchmark
        systematic = cp.quad_form(factor_exposure, cp.psd_wrap(risk._f))
        specific = cp.sum(cp.multiply(risk._d, cp.square(ordered)))
        return systematic + specific
    variance = cp.quad_form(positions, cp.psd_wrap(risk))
    if benchmark is not None:
        marginal = portfolio._risk_apply(benchmark, original=True)
        variance -= 2 * np.asarray(marginal, float) @ positions
        variance += float(product_sum((benchmark, marginal)))
    return variance


def compile_model(portfolio, *, minimum_return=None):
    import cvxpy as cp

    portfolio._check()
    if portfolio._objective == "moment_utility":
        raise ValueError(
            "moment utility is a nonconvex polynomial; "
            "use quantum.compile_portfolio with equal-weight selection"
        )
    if portfolio._objective == "hrp":
        raise ValueError("HRP is a construction method, not a CVXPY program")
    if portfolio._objective == "risk_budgeting":
        scaled_positions = cp.Variable(len(portfolio._ids), pos=True)
        volatility = np.sqrt(portfolio._risk_diagonal())
        positions = cp.multiply(1 / volatility, scaled_positions)
        weights = portfolio._net_weight * positions / cp.sum(positions)
        objective = cp.Minimize(
            0.5 * _variance_expression(portfolio, positions)
            - portfolio._risk_budgets @ cp.log(positions)
        )
        problem = cp.Problem(objective)
        variables = {"weights": weights}
        variables.update(
            {
                f"risk_position_{i}": positions[i]
                for i in range(len(portfolio._ids))
            }
        )
        return problem, variables
    lower, upper, fixed_conflicts = portfolio._allocation_bounds()
    weights = cp.Variable(
        len(portfolio._ids),
        name="weights",
        bounds=[lower.copy(), upper.copy()],
    )
    constraints = []
    variables = {"weights": weights}
    costs, cash_income = 0, 0
    if portfolio._account is None:
        constraints.append(cp.sum(weights) == portfolio._net_weight)
    else:
        cash, costs, account_variables = portfolio._account.add_cvxpy(
            weights, portfolio._lower, portfolio._upper, constraints
        )
        cash_income = portfolio._account.cash_return * cash
        variables.update(account_variables)
    if portfolio._fixed_selection is not None:
        if fixed_conflicts.any():
            lower, upper = portfolio._fixed_weight_bounds()
            constraints.extend(
                [
                    weights[fixed_conflicts] >= lower[fixed_conflicts],
                    weights[fixed_conflicts] <= upper[fixed_conflicts],
                ]
            )
    elif portfolio._selection is not None:
        selection = portfolio._selection
        positive = cp.Variable(
            len(portfolio._ids), boolean=True, name="selected_positive"
        )
        negative = cp.Variable(
            len(portfolio._ids), boolean=True, name="selected_negative"
        )
        constraints.append(positive + negative <= 1)
        if selection["equal_weight"]:
            constraints.extend(
                [
                    negative == 0,
                    weights
                    == portfolio._net_weight / selection["count"] * positive,
                ]
            )
        else:
            minimum = selection["minimum_weight"]
            constraints.extend(
                [
                    weights
                    >= minimum * positive
                    + cp.multiply(np.minimum(0, portfolio._lower), negative),
                    weights
                    <= cp.multiply(np.maximum(0, portfolio._upper), positive)
                    - minimum * negative,
                ]
            )
        chosen = cp.sum(positive + negative)
        constraints.append(
            chosen == selection["count"]
            if selection["count"] is not None
            else chosen <= selection["maximum"]
        )
        variables.update(
            {
                f"selected_positive_{i}": positive[i]
                for i in range(len(portfolio._ids))
            }
        )
        variables.update(
            {
                f"selected_negative_{i}": negative[i]
                for i in range(len(portfolio._ids))
            }
        )
    forecast_return = (
        None if portfolio._mu is None else portfolio._mu @ weights
    )
    if portfolio._return_uncertainty is not None:
        _, u, radius = portfolio._return_uncertainty
        if radius > 0:
            forecast_return -= radius * cp.norm(u.T @ weights, 2)
    if forecast_return is not None:
        forecast_return += cash_income - costs
    if portfolio._minimum_return is not None:
        target = (
            portfolio._minimum_return
            if minimum_return is None
            else minimum_return
        )
        constraints.append(forecast_return >= target)
    for _, a, lower_bounds, upper_bounds in portfolio._exposures:
        constraints.extend(
            [a @ weights >= lower_bounds, a @ weights <= upper_bounds]
        )
    if portfolio._leverage is not None:
        constraints.append(cp.norm1(weights) <= portfolio._leverage)
    if portfolio._turnover is not None:
        current, maximum = portfolio._turnover
        constraints.append(cp.norm1(weights - current) <= maximum)

    def variance(x):
        return _variance_expression(portfolio, x)

    if portfolio._volatility_limit is not None:
        constraints.append(variance(weights) <= portfolio._volatility_limit**2)
    if portfolio._objective == "variance":
        objective = cp.Minimize(variance(weights))
    elif portfolio._objective == "tracking_error":
        objective = cp.Minimize(
            _variance_expression(
                portfolio, weights, benchmark=portfolio._benchmark
            )
        )
    elif portfolio._objective == "utility":
        risk_term = (
            portfolio._risk_aversion / 2 * variance(weights)
            if portfolio._risk_aversion
            else 0
        )
        objective = cp.Maximize(forecast_return - risk_term)
    else:
        scenarios = portfolio._scenarios
        r, probabilities = (
            scenarios._values @ weights + cash_income - costs,
            scenarios._probabilities,
        )
        if portfolio._objective == "expected_shortfall":
            expression, inequalities = expected_shortfall_epigraph(
                -r,
                probabilities=probabilities,
                confidence=portfolio._confidence,
                backend="cvxpy",
            )
            constraints.extend(inequalities)
            objective = cp.Minimize(expression)
        elif portfolio._objective == "mean_absolute_deviation":
            objective = cp.Minimize(
                probabilities @ cp.abs(r - probabilities @ r)
            )
        else:
            objective = cp.Minimize(
                probabilities @ cp.pos(portfolio._downside_target - r)
            )
    problem = cp.Problem(objective, constraints)
    if not problem.is_dcp():
        raise ValueError("financial formulation is not a convex DCP model")
    return problem, variables
