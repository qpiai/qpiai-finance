"""Independent source credit income, loss, resource and policy accounting."""

from fractions import Fraction

import numpy as np
import pandas as pd

from .._arithmetic import (
    bound_violation,
    probability_masses,
    product_sum,
    row_products,
    weighted_mean,
)
from .._result_checks import record_reconciliation
from .._validation import (
    copy_index,
    group_members,
    lot_quantities,
    lot_residual,
    scalar,
    vector,
)
from ..risk import _tail_mean


def evaluate(credit, allocations, *, tolerance):
    tolerance = scalar(tolerance, "tolerance", minimum=0)
    amounts = vector(allocations, credit._ids, "allocations")
    loss_rates = credit._loss_rates()
    expected_loss = np.fromiter(
        (
            Fraction(rate) * Fraction(amount)
            for rate, amount in zip(loss_rates, amounts)
        ),
        dtype=float,
    )
    with np.errstate(over="raise", invalid="raise"):
        changes = amounts - credit._current
        increases, reductions = np.maximum(changes, 0), np.maximum(-changes, 0)
        income = credit._income * amounts
        funding_cost = credit._funding_cost * amounts
        capital = credit._capital * amounts
        funding = credit._funding * amounts
        exposure = credit._ead * amounts
    fee_rates = np.where(
        amounts >= credit._current,
        credit._increase_cost,
        -credit._decrease_cost,
    )
    fee_total = product_sum(
        (fee_rates, amounts), (-fee_rates, credit._current)
    )
    net_rate, contribution_rate = credit._income_margins()
    change_cost, contribution, capital_cost = np.empty((3, len(amounts)))
    for i, amount in enumerate(amounts):
        quantity = Fraction(amount)
        fee = Fraction(fee_rates[i]) * (
            quantity - Fraction(credit._current[i])
        )
        change_cost[i] = float(fee)
        contribution[i] = float(contribution_rate[i] * quantity - fee)
        capital_cost[i] = float(
            Fraction(credit._capital_charge)
            * Fraction(credit._capital[i])
            * quantity
        )
    original_funding = product_sum((credit._funding, amounts))
    original_capital = product_sum((credit._capital, amounts))
    original_exposure = product_sum((credit._ead, amounts))
    rows = []

    def check(name, value, lower, upper, unit=None):
        reported = float(value)
        if not np.isfinite(reported):
            raise ValueError(
                "credit quantities or metrics exceed float64 range"
            )
        violation = bound_violation(value, lower, upper)
        rows.append(
            (
                name,
                reported,
                lower,
                upper,
                float(violation),
                violation <= tolerance,
                unit or credit._currency,
            )
        )

    for i, facility in enumerate(credit._ids):
        check(
            f"allocation[{i}:{facility}]",
            amounts[i],
            credit._lower[i],
            credit._upper[i],
        )
        if credit._lots is not None:
            check(
                f"allocation_lots[{i}]",
                lot_residual(amounts[i], credit._lots[i]),
                0,
                0,
                "lots",
            )
    selected = amounts > 0
    if credit._selection is not None:
        minimum, maximum_count = credit._selection
        for i in range(len(amounts)):
            check(
                f"active_minimum[{i}]",
                amounts[i],
                minimum[i] if selected[i] else 0,
                credit._upper[i],
            )
        check(
            "facility_count",
            float(selected.sum()),
            0,
            maximum_count,
            "facilities",
        )
    metrics = {
        "allocated_amount": float(
            product_sum((amounts, np.ones(len(amounts))))
        ),
        "expected_income": float(product_sum((credit._income, amounts))),
        "funding_cost": float(product_sum((credit._funding_cost, amounts))),
        "expected_credit_loss": float(product_sum((loss_rates, amounts))),
        "transaction_cost": float(fee_total),
        "capital_cost": float(
            Fraction(credit._capital_charge) * original_capital
        ),
        "capital_used": float(original_capital),
        "funding_used": float(original_funding),
        "exposure_at_default": float(original_exposure),
        "net_income": float(product_sum((net_rate, amounts)) - fee_total),
    }
    check("funding", original_funding, 0, credit._funding_limit)
    check("capital", original_capital, 0, credit._capital_limit)
    tables = {
        "allocations": pd.DataFrame(
            {
                "current_amount": credit._current,
                "allocated_amount": amounts,
                "increase": increases,
                "reduction": reductions,
                "capacity": credit._capacity,
                "expected_income": income,
                "funding_cost": funding_cost,
                "expected_credit_loss": expected_loss,
                "transaction_cost": change_cost,
                "capital_cost": capital_cost,
                "net_contribution": contribution,
                "capital_used": capital,
                "funding_used": funding,
                "exposure_at_default": exposure,
                "currency": credit._currency,
            },
            index=copy_index(credit._ids),
        ),
        "resources": pd.DataFrame(
            {
                "used": [metrics["funding_used"], metrics["capital_used"]],
                "limit": [credit._funding_limit, credit._capital_limit],
                "currency": credit._currency,
            },
            index=["funding", "capital"],
        ),
    }
    exposure_rows = []
    for block, (ids, coefficients, lower, upper) in enumerate(
        credit._exposures
    ):
        actual = list(row_products(coefficients, amounts))
        for i, identifier in enumerate(ids):
            check(
                f"exposure[{block}:{i}:{identifier}]",
                actual[i],
                lower[i],
                upper[i],
            )
            exposure_rows.append(
                (
                    block,
                    identifier,
                    float(actual[i]),
                    lower[i],
                    upper[i],
                    credit._currency,
                )
            )
    if exposure_rows:
        tables["exposures"] = pd.DataFrame(
            exposure_rows,
            columns=[
                "classification",
                "exposure",
                "amount",
                "lower",
                "upper",
                "currency",
            ],
        )
    concentration_rows = []
    for block, (groups, ids, shares) in enumerate(credit._concentrations):
        total = original_exposure
        for i, members in enumerate(group_members(groups, ids)):
            amount = product_sum((credit._ead[members], amounts[members]))
            check(
                f"concentration[{block}:{i}:{ids[i]}]",
                amount - Fraction(shares[i]) * total,
                -np.inf,
                0,
            )
            concentration_rows.append(
                (
                    block,
                    ids[i],
                    float(amount),
                    float(total),
                    float(amount / total) if total > 0 else np.nan,
                    shares[i],
                    credit._currency,
                )
            )
    if concentration_rows:
        tables["concentrations"] = pd.DataFrame(
            concentration_rows,
            columns=[
                "classification",
                "group",
                "amount",
                "total_exposure",
                "share",
                "maximum_share",
                "currency",
            ],
        )
    objective = product_sum((contribution_rate, amounts)) - fee_total
    scenarios = credit._scenarios
    if scenarios is not None:
        source_losses = np.fromiter(
            row_products(scenarios._values, amounts), dtype=object
        )
        losses = np.asarray(source_losses, dtype=float)
        tables["scenario_losses"] = pd.DataFrame(
            {"loss": losses, "currency": credit._currency},
            index=copy_index(scenarios._ids),
        )
        if scenarios._probabilities is not None:
            tables["scenario_losses"]["probability"] = scenarios._probabilities
            metrics["scenario_expected_loss"] = float(
                weighted_mean(source_losses, scenarios._probabilities)
            )
        if credit._scenario_limit is not None:
            tables["scenario_losses"]["maximum"] = credit._scenario_limit
            for s, scenario in enumerate(scenarios._ids):
                check(
                    f"scenario_loss[{s}:{scenario}]",
                    source_losses[s],
                    0,
                    credit._scenario_limit[s],
                )
        if credit._risk_aversion > 0 or credit._tail_limit is not None:
            order = np.argsort(source_losses, kind="stable")[::-1]
            masses, total = probability_masses(scenarios._probabilities)

            def tail_mean(confidence):
                return _tail_mean(
                    source_losses[order], masses[order], total, confidence
                )

        if credit._risk_aversion > 0:
            tail = tail_mean(credit._confidence)
            risk_cost = Fraction(credit._risk_aversion) * tail
            metrics["objective_expected_shortfall"] = float(tail)
            metrics["tail_risk_cost"] = float(risk_cost)
            objective -= risk_cost
        if credit._tail_limit is not None:
            maximum, beta = credit._tail_limit
            tail = tail_mean(beta)
            metrics["constrained_expected_shortfall"] = float(tail)
            check("expected_shortfall", tail, 0, maximum)
    objective = float(objective)
    if not np.isfinite([objective, *metrics.values()]).all():
        raise ValueError("credit quantities or metrics exceed float64 range")
    constraints = pd.DataFrame(
        rows,
        columns=[
            "constraint",
            "value",
            "lower",
            "upper",
            "violation",
            "satisfied",
            "unit",
        ],
    ).set_index("constraint")
    return {
        "objective": objective,
        "feasible": bool(constraints.satisfied.all()),
        "constraints": constraints,
        "decision": {
            "allocations": pd.Series(
                amounts, index=copy_index(credit._ids), name="allocated_amount"
            ),
            "allocation_changes": pd.Series(
                changes, index=copy_index(credit._ids), name="change"
            ),
        },
        "metrics": metrics,
        "tables": tables,
        "costs": {
            name: metrics[name]
            for name in (
                "funding_cost",
                "expected_credit_loss",
                "transaction_cost",
                "capital_cost",
                "tail_risk_cost",
            )
            if name in metrics
        },
    }


def evaluate_solution(credit, solution, *, tolerance):
    raw = np.array(
        [
            scalar(solution[f"allocation_{i}"], "solver allocation")
            for i in range(len(credit._ids))
        ]
    )
    amounts = (
        raw
        if credit._lots is None
        else lot_quantities(np.rint(raw), credit._lots)
    )
    evaluation = credit.evaluate(amounts, tolerance=tolerance)
    diagnostics = []
    if credit._lots is not None:
        diagnostics.append(
            (
                "integer_reconstruction",
                float(np.max(np.abs(raw - np.rint(raw)))),
                "lots",
            )
        )
        evaluation["transformations"] = [
            {
                "type": "allocation_lot_reconstruction",
                "constraints_rechecked": True,
            }
        ]
    if credit._selection is not None:
        for i, amount in enumerate(amounts):
            active = scalar(solution[f"selected_{i}"], "solver selection")
            diagnostics.append(
                (
                    f"selection_reconciliation[{i}]",
                    abs(active - float(amount > 0)),
                    "binary",
                )
            )
    reconciliation = []
    if credit._concentrations:
        reconciliation.append(
            (
                "exposure_reconciliation",
                abs(
                    scalar(solution["total_exposure"], "solver total exposure")
                    - evaluation["metrics"]["exposure_at_default"]
                ),
                credit._currency,
            )
        )
    if "constant_constraint_zero" in solution:
        diagnostics.append(
            (
                "constant_constraint_zero",
                abs(
                    scalar(
                        solution["constant_constraint_zero"],
                        "constant row guard",
                    )
                ),
                "numeric",
            )
        )
    for name, value, unit in diagnostics:
        evaluation["constraints"].loc[name] = [
            value,
            0,
            0,
            value,
            value <= tolerance,
            unit,
        ]
    evaluation["feasible"] = bool(evaluation["constraints"].satisfied.all())
    record_reconciliation(evaluation, reconciliation, tolerance=tolerance)
    return evaluation
