"""Check portfolio constraints and calculate financial results."""

from fractions import Fraction

import numpy as np
import pandas as pd

from .._arithmetic import (
    bound_violation,
    centered_numerators,
    probability_masses,
    product_sum,
    row_products,
    square_root,
    subtract_square_root,
    weighted_mean,
)
from .._result_checks import record_reconciliation
from .._serialization import identifier_label
from .._validation import copy_index, scalar, vector
from ..risk import (
    FactorRisk,
    _portfolio_beta,
    _position_totals,
    _quadratic_risk,
    _risk_contributions,
    _tail_mean,
)


def evaluate_solution(portfolio, solution, *, tolerance):
    weights = np.array(
        [solution[f"weight_{i}"] for i in range(len(portfolio._ids))]
    )
    original = weights.copy()
    residuals = {}
    reconciliation = []
    if portfolio._account is not None:
        weights, account_residuals = portfolio._account.recover(
            weights, solution
        )
        residuals.update(account_residuals)
    allocation = portfolio._objective in {"risk_budgeting", "hrp"}
    if portfolio._selection is not None and not allocation:
        for i in range(len(weights)):
            if portfolio._fixed_selection is None:
                positive = solution[f"selected_positive_{i}"]
                negative = solution[f"selected_negative_{i}"]
            else:
                positive = int(portfolio._fixed_selection[i] > 0)
                negative = int(portfolio._fixed_selection[i] < 0)
            residuals[f"positive_selection[{i}]"] = float(
                abs(positive - np.rint(positive))
            )
            residuals[f"negative_selection[{i}]"] = float(
                abs(negative - np.rint(negative))
            )
            if np.rint(positive) == 0 and np.rint(negative) == 0:
                weights[i] = 0
    tax_lot_sales = None
    if (
        portfolio._account is not None
        and portfolio._account.tax_lots is not None
    ):
        tax_lot_sales, tax_residuals = portfolio._account.tax_lots.recover(
            solution
        )
        residuals.update(tax_residuals)
    evaluation = portfolio.evaluate(
        weights, tax_lot_sales=tax_lot_sales, tolerance=tolerance
    )
    evaluation.setdefault(
        "decision",
        {
            "weights": pd.Series(
                weights, index=copy_index(portfolio._ids), name="weight"
            )
        },
    )
    residuals["weight_reconstruction"] = float(
        np.max(np.abs(weights - original))
    )
    if portfolio._objective == "risk_budgeting":
        positions = np.array(
            [solution[f"risk_position_{i}"] for i in range(len(weights))]
        )
        variance_residual = abs(
            float(
                _quadratic_risk(
                    positions,
                    portfolio._risk_apply(positions, original=True),
                    name="risk-budget position variance",
                )
                - 1
            )
        )
        reconciliation.append(
            ("risk_position_variance", variance_residual, "dimensionless")
        )
        evaluation["transformations"] = [
            {
                "type": "risk_budget_normalization",
                "position_scaling": "asset_volatility",
                "position_sum": float(positions.sum()),
                "investment_basis": portfolio._net_weight,
                "risk_contributions_rechecked": True,
            }
        ]
    if portfolio._account is not None:
        reconciliation.append(
            (
                "solver_cash_reconciliation",
                abs(
                    solution["cash_weight"]
                    - evaluation["metrics"]["cash_weight"]
                ),
                "weight",
            )
        )
    rows = [
        (name, value, 0.0, 0.0, value, value <= tolerance)
        for name, value in residuals.items()
    ]
    diagnostics = pd.DataFrame(
        rows,
        columns=[
            "constraint",
            "value",
            "lower",
            "upper",
            "violation",
            "satisfied",
        ],
    ).set_index("constraint")
    evaluation["constraints"] = pd.concat(
        [evaluation["constraints"], diagnostics]
    )
    evaluation["feasible"] = bool(evaluation["constraints"].satisfied.all())
    record_reconciliation(evaluation, reconciliation, tolerance=tolerance)
    if portfolio._mixed_integer and not allocation:
        evaluation["transformations"] = [
            {
                "type": "integer_reconstruction",
                "maximum_weight_residual": residuals["weight_reconstruction"],
                "constraints_rechecked": True,
            }
        ]
    return evaluation


def evaluate_weights(
    portfolio, weights, *, tax_lot_sales=None, tolerance=1e-7
):
    """Recompute source economics/constraints without using compiled
    auxiliaries.
    """
    portfolio._check()
    tolerance = scalar(tolerance, "tolerance", minimum=0)
    weights = vector(weights, portfolio._ids, "weights")
    net, gross = _position_totals(weights)
    metrics = {"gross_exposure": float(gross), "net_exposure": float(net)}
    account = (
        None
        if portfolio._account is None
        else portfolio._account.evaluate(
            weights, portfolio._ids, tolerance, tax_lot_sales=tax_lot_sales
        )
    )
    if portfolio._account is None and tax_lot_sales is not None:
        raise ValueError("tax_lot_sales requires configured tax lots")
    cash_income, cost_fraction = 0.0, 0.0
    if account is not None:
        metrics.update(account["metrics"])
        cash_income = portfolio._account.cash_return * metrics["cash_weight"]
        cost_fraction = (
            metrics["transaction_cost"] / portfolio._account.initial_value
        )
        metrics["cash_return"] = cash_income
    effective_return = source_return = None
    if portfolio._mu is not None:
        forecast = product_sum((portfolio._mu, weights))
        gross_return = float(forecast)
        source_return = (
            forecast + Fraction(cash_income) - Fraction(cost_fraction)
        )
        effective_return = float(source_return)
        metrics["expected_return"] = effective_return
        if account is not None:
            metrics["gross_expected_return"] = gross_return
    uncertainty_squared = Fraction(0)
    if portfolio._return_uncertainty is not None:
        _, uncertainty, radius = portfolio._return_uncertainty
        if radius > 0:
            exposures = np.fromiter(
                row_products(uncertainty.T, weights), dtype=object
            )
            uncertainty_squared = Fraction(radius) ** 2 * product_sum(
                (exposures, exposures)
            )
        effective_return = float(
            subtract_square_root(source_return, uncertainty_squared)
        )
        metrics["worst_case_expected_return"] = effective_return
    rows = [] if account is None else account["rows"]

    def check(name, value, lower, upper):
        violation = bound_violation(value, lower, upper)
        rows.append(
            (
                name,
                float(value),
                lower,
                upper,
                float(violation),
                violation <= tolerance,
            )
        )

    if account is None:
        check(
            "investment_basis",
            net,
            portfolio._net_weight,
            portfolio._net_weight,
        )
    for i, asset in enumerate(portfolio._ids):
        check(
            f"weight[{i}:{asset}]",
            float(weights[i]),
            float(portfolio._lower[i]),
            float(portfolio._upper[i]),
        )
    if portfolio._minimum_return is not None:
        minimum = portfolio._minimum_return
        if portfolio._return_uncertainty is None:
            check("minimum_return", source_return, minimum, np.inf)
        else:
            offset = source_return - Fraction(minimum)
            violation = max(
                -subtract_square_root(offset, uncertainty_squared), 0
            )
            allowed = offset + Fraction(tolerance)
            rows.append(
                (
                    "minimum_return",
                    effective_return,
                    minimum,
                    np.inf,
                    float(violation),
                    allowed >= 0 and allowed**2 >= uncertainty_squared,
                )
            )
    if portfolio._leverage is not None:
        check("gross_exposure", gross, 0, portfolio._leverage)
    if portfolio._turnover is not None:
        current, limit = portfolio._turnover
        direction = np.where(weights >= current, 1.0, -1.0)
        turnover = product_sum((direction, weights), (-direction, current))
        metrics["turnover"] = float(turnover)
        check("turnover", turnover, 0, limit)
    for ids, values, lower_bounds, upper_bounds in portfolio._exposures:
        exposures = list(row_products(values, weights))
        for i, label in enumerate(ids):
            check(
                f"exposure[{identifier_label(label)}]",
                exposures[i],
                float(lower_bounds[i]),
                float(upper_bounds[i]),
            )

    if portfolio._selection is not None:
        selection = portfolio._selection
        selected = weights != 0
        number = int(np.count_nonzero(selected))
        count, maximum = selection["count"], selection["maximum"]
        check(
            "selected_asset_count",
            number,
            count if count is not None else 0,
            count if count is not None else maximum,
        )
        for i in np.flatnonzero(selected):
            check(
                f"minimum_position[{i}]",
                float(abs(weights[i])),
                selection["minimum_weight"],
                np.inf,
            )
            if selection["equal_weight"]:
                target = portfolio._net_weight / count
                check(f"equal_weight[{i}]", float(weights[i]), target, target)

    tables = {} if account is None else account["tables"]
    if portfolio._fixed_selection is not None:
        lower, upper = portfolio._fixed_weight_bounds()
        for i, weight in enumerate(weights):
            check(
                f"fixed_selection[{identifier_label(portfolio._ids[i])}]",
                float(weight),
                float(lower[i]),
                float(upper[i]),
            )
        tables["asset_selection"] = pd.DataFrame(
            {
                "selection": portfolio._fixed_selection.copy(),
                "weight": weights.copy(),
            },
            index=copy_index(portfolio._ids),
        )
    if portfolio._covariance is not None:
        covariance_weights = portfolio._risk_apply(weights, original=True)
        variance = _quadratic_risk(
            weights, covariance_weights, name="portfolio variance"
        )
        volatility = square_root(variance)
        metrics.update(variance=float(variance), volatility=float(volatility))
        if portfolio._volatility_limit is not None:
            maximum = Fraction(portfolio._volatility_limit)
            violation = max(-subtract_square_root(maximum, variance), 0)
            rows.append(
                (
                    "volatility",
                    float(volatility),
                    0,
                    float(maximum),
                    float(violation),
                    variance <= (maximum + Fraction(tolerance)) ** 2,
                )
            )
        contributions = _risk_contributions(
            weights, covariance_weights, variance
        )
        tables["risk_contributions"] = pd.DataFrame(
            contributions,
            index=copy_index(portfolio._ids),
        )
        if isinstance(portfolio._covariance, FactorRisk):
            attribution = portfolio._covariance.risk_contributions(
                pd.Series(weights, index=copy_index(portfolio._ids))
            )
            factors = attribution.xs("factor", level="component")[["exposure"]]
            factors.index = copy_index(portfolio._covariance._factors)
            tables["factor_exposures"] = factors
            tables["factor_risk_contributions"] = attribution
        if account is not None and metrics["portfolio_value"] > 0:
            actual = account["decision"]["post_trade_weights"].to_numpy()
            actual_variance = _quadratic_risk(
                actual,
                portfolio._risk_apply(actual, original=True),
                name="post-trade variance",
            )
            metrics["post_trade_variance"] = float(actual_variance)
            metrics["post_trade_volatility"] = float(
                square_root(actual_variance)
            )
    if portfolio._objective == "risk_budgeting":
        if variance <= 0 or np.any(weights <= 0):
            raise ValueError(
                "risk-budgeted weights require positive weights and variance"
            )
        shares = np.fromiter(
            (
                float(product_sum(([w], [m])) / variance)
                for w, m in zip(weights, covariance_weights)
            ),
            dtype=float,
        )
        errors = shares - portfolio._risk_budgets
        for i, contribution in enumerate(shares):
            target = float(portfolio._risk_budgets[i])
            check(f"risk_budget[{i}]", float(contribution), target, target)
        metrics["risk_budget_error"] = float(np.max(np.abs(errors)))
        tables["risk_budgets"] = pd.DataFrame(
            {
                "budget": portfolio._risk_budgets,
                "contribution": shares,
                "difference": errors,
            },
            index=copy_index(portfolio._ids),
        )
        risk_positions = np.fromiter(
            (float(Fraction(w) / volatility) for w in weights), dtype=float
        )
        objective = 0.5 - float(
            portfolio._risk_budgets @ np.log(risk_positions)
        )
    elif portfolio._objective == "hrp":
        objective = None
    elif portfolio._objective == "variance":
        objective = float(variance)
    elif portfolio._objective == "utility":
        objective = float(
            subtract_square_root(
                source_return
                - Fraction(portfolio._risk_aversion)
                / 2
                * (variance if portfolio._covariance is not None else 0),
                uncertainty_squared,
            )
        )
    elif portfolio._objective == "tracking_error":
        active = np.fromiter(
            (
                Fraction(w) - Fraction(b)
                for w, b in zip(weights, portfolio._benchmark)
            ),
            dtype=object,
        )
        active_marginal = portfolio._risk_apply(active, original=True)
        active_variance = _quadratic_risk(
            active, active_marginal, name="active variance"
        )
        metrics["tracking_error"] = float(square_root(active_variance))
        if portfolio._mu is not None:
            metrics["active_return"] = float(
                product_sum(
                    (portfolio._mu, weights),
                    (-portfolio._mu, portfolio._benchmark),
                )
            )
        objective = float(active_variance)
        tables["active_weights"] = pd.DataFrame(
            {
                "weight": weights,
                "benchmark": portfolio._benchmark,
                "active": np.asarray(active, float),
            },
            index=copy_index(portfolio._ids),
        )
    else:
        scenarios = portfolio._scenarios
        income = Fraction(cash_income) - Fraction(cost_fraction)
        source_returns = np.fromiter(
            (
                value + income
                for value in row_products(scenarios._values, weights)
            ),
            dtype=object,
        )
        scenario_returns = np.asarray(source_returns, dtype=float)
        probabilities = scenarios._probabilities
        losses = -scenario_returns
        mean = weighted_mean(source_returns, probabilities)
        metrics["scenario_expected_return"] = float(mean)
        if portfolio._objective == "expected_shortfall":
            source_losses = -source_returns
            order = np.argsort(source_losses, kind="stable")[::-1]
            masses, total = probability_masses(probabilities)
            objective = float(
                _tail_mean(
                    source_losses[order],
                    masses[order],
                    total,
                    portfolio._confidence,
                )
            )
            metrics["expected_shortfall"] = objective
            metrics["confidence"] = portfolio._confidence
        elif portfolio._objective in {
            "mean_absolute_deviation",
            "moment_utility",
        }:
            # Integer probability units retain a common denominator. Centered
            # numerators remain dyadic even when the mean itself is not.
            _, total = probability_masses(probabilities)
            centered = centered_numerators(source_returns, mean, total)
            if portfolio._objective == "mean_absolute_deviation":
                objective = float(
                    weighted_mean(np.abs(centered), probabilities) / total
                )
                metrics["mean_absolute_deviation"] = objective
            else:
                variance, third, fourth = (
                    weighted_mean(centered**power, probabilities)
                    / total**power
                    for power in (2, 3, 4)
                )
                aversion, preference, tail_aversion = (
                    portfolio._moment_preferences
                )
                source_terms = {
                    "expected_return": source_return,
                    "variance": -Fraction(aversion) * variance,
                    "third_central_moment": Fraction(preference) * third,
                    "fourth_central_moment": -Fraction(tail_aversion) * fourth,
                }
                objective = float(sum(source_terms.values()))
                metrics.update(
                    moment_variance=float(variance),
                    third_central_moment=float(third),
                    fourth_central_moment=float(fourth),
                )
                tables["objective_terms"] = pd.DataFrame(
                    {
                        "contribution": {
                            name: float(value)
                            for name, value in source_terms.items()
                        }
                    }
                ).rename_axis("term")
        else:
            shortfall = np.maximum(
                Fraction(portfolio._downside_target) - source_returns, 0
            )
            objective = float(weighted_mean(shortfall, probabilities))
            metrics["downside_risk"] = objective
            metrics["downside_target"] = portfolio._downside_target
        tables["scenarios"] = pd.DataFrame(
            {
                "return": scenario_returns,
                "loss": losses,
                "probability": probabilities,
            },
            index=copy_index(scenarios._ids),
        )
    constraints = pd.DataFrame(
        rows,
        columns=[
            "constraint",
            "value",
            "lower",
            "upper",
            "violation",
            "satisfied",
        ],
    ).set_index("constraint")
    if account is not None and account["tax_constraints"] is not None:
        constraints = pd.concat([constraints, account["tax_constraints"]])
    if (objective is not None and not np.isfinite(objective)) or not all(
        np.isfinite(x) for x in metrics.values()
    ):
        raise ValueError("source objective or metrics exceed float64 range")
    if portfolio._objective == "tracking_error":
        metrics["beta"] = _portfolio_beta(
            portfolio._benchmark,
            covariance_weights,
            active_marginal,
        )
    result = {
        "objective": None if objective is None else float(objective),
        "metrics": metrics,
        "constraints": constraints,
        "tables": tables,
        "feasible": bool(constraints.satisfied.all()),
    }
    if account is not None:
        result["decision"], result["costs"] = (
            account["decision"],
            account["costs"],
        )
    return result
