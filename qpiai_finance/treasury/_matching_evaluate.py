"""Source accounting of purchased instruments, reserve and liability cover."""

from fractions import Fraction

import numpy as np
import pandas as pd

from .._arithmetic import bound_violation, product_sum, row_products
from .._result_checks import record_reconciliation
from .._validation import (
    copy_index,
    lot_quantities,
    lot_residual,
    scalar,
    vector,
)


def evaluate(matching, holdings, initial_capital, *, tolerance):
    tolerance = scalar(tolerance, "tolerance", minimum=0)
    capital = scalar(initial_capital, "initial_capital")
    holdings = vector(holdings, matching._ids, "holdings")
    purchase_total = product_sum((matching._prices, holdings))
    asset_totals = list(row_products(matching._flows, holdings))
    try:
        purchase_cost = float(purchase_total)
        asset_flows = np.asarray(asset_totals, dtype=float)
    except OverflowError as error:
        raise ValueError(
            "liability matching quantities exceed float64 range"
        ) from error
    opening = np.zeros(len(matching._dates))
    closing = opening.copy()
    interest = opening.copy()
    rows = []

    def check(name, value, lower, upper, unit):
        violation = bound_violation(value, lower, upper)
        try:
            report = float(value), float(violation)
        except OverflowError as error:
            raise ValueError(
                "liability matching quantities exceed float64 range"
            ) from error
        rows.append(
            (
                name,
                report[0],
                lower,
                upper,
                report[1],
                violation <= tolerance,
                unit,
            )
        )

    check(
        "initial_capital",
        capital,
        0,
        matching._capital_limit,
        matching._currency,
    )
    for i, asset in enumerate(matching._ids):
        check(
            f"holding[{i}:{asset}]",
            holdings[i],
            matching._lower[i],
            matching._upper[i],
            "instrument_units",
        )
        if matching._lots is not None:
            check(
                f"holding_lots[{i}]",
                lot_residual(holdings[i], matching._lots[i]),
                0,
                0,
                "lots",
            )
    balance = Fraction(capital)
    try:
        for t in range(len(matching._dates)):
            opening[t] = float(balance)
            earned = balance * Fraction(matching._returns[t])
            balance += earned + asset_totals[t]
            balance -= Fraction(matching._liabilities[t])
            if t == 0:
                balance -= purchase_total
            interest[t], closing[t] = float(earned), float(balance)
            check(
                f"cash[{t}]",
                balance,
                matching._cash_lower[t],
                matching._cash_upper[t],
                matching._currency,
            )
        with np.errstate(over="raise", invalid="raise"):
            purchase_values = matching._prices * holdings
        uninvested_cash = float(Fraction(capital) - purchase_total)
    except (OverflowError, FloatingPointError) as error:
        raise ValueError(
            "liability matching quantities exceed float64 range"
        ) from error
    tables = {
        "liability_coverage": pd.DataFrame(
            {
                "opening_cash": opening,
                "deposit_interest": interest,
                "asset_cash_flow": asset_flows,
                "liability": matching._liabilities,
                "purchase_outlay": [purchase_cost] + [0] * (len(opening) - 1),
                "closing_cash": closing,
                "cash_buffer": matching._cash_lower,
                "currency": matching._currency,
            },
            index=copy_index(matching._dates),
        ),
        "holdings": pd.DataFrame(
            {
                "quantity": holdings,
                "price": matching._prices,
                "purchase_value": purchase_values,
                "currency": matching._currency,
            },
            index=copy_index(matching._ids),
        ),
    }
    if matching._sensitivities is not None:
        risks, values, targets, units = matching._sensitivities
        totals = list(row_products(values, holdings))
        try:
            actual = np.asarray(totals, dtype=float)
            residuals = np.asarray(
                [
                    value - Fraction(target)
                    for value, target in zip(totals, targets)
                ],
                dtype=float,
            )
        except OverflowError as error:
            raise ValueError(
                "sensitivity exposures exceed float64 range"
            ) from error
        for i, risk in enumerate(risks):
            check(
                f"sensitivity[{i}:{risk}]",
                totals[i],
                targets[i],
                targets[i],
                units[i],
            )
        tables["sensitivity_matching"] = pd.DataFrame(
            {
                "actual": actual,
                "target": targets,
                "residual": residuals,
                "unit": units,
            },
            index=copy_index(risks),
        )
    metrics = {
        "initial_capital": capital,
        "purchase_cost": purchase_cost,
        "initial_uninvested_cash": uninvested_cash,
        "final_cash": float(closing[-1]),
    }
    if not np.isfinite(
        [*metrics.values(), *asset_flows, *closing, *interest]
    ).all():
        raise ValueError("liability matching quantities exceed float64 range")
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
        "objective": capital,
        "feasible": bool(constraints.satisfied.all()),
        "constraints": constraints,
        "metrics": metrics,
        "tables": tables,
        "decision": {
            "holdings": pd.Series(
                holdings, index=copy_index(matching._ids), name="quantity"
            ),
            "cash_balances": pd.Series(
                closing, index=copy_index(matching._dates), name="cash"
            ),
        },
        "costs": {
            "initial_capital": capital,
            "purchase_cost": purchase_cost,
            "currency": matching._currency,
        },
    }


def evaluate_solution(matching, solution, *, tolerance):
    raw = np.array(
        [
            scalar(solution[f"holding_{i}"], "solver holding")
            for i in range(len(matching._ids))
        ]
    )
    holdings = (
        raw
        if matching._lots is None
        else lot_quantities(np.rint(raw), matching._lots)
    )
    scales = (
        np.ones(len(matching._ids))
        if matching._lots is None
        else matching._lots
    )
    # Preserve the raw implied reserve before reconstructing whole lots.
    reserve = product_sum((matching._prices * scales, raw))
    reserve += Fraction(scalar(solution["cash_0"], "solver cash"))
    reserve += Fraction(matching._liabilities[0])
    try:
        capital = float(reserve)
    except OverflowError as error:
        raise ValueError("initial capital exceeds float64 range") from error
    evaluation = evaluate(matching, holdings, capital, tolerance=tolerance)
    evaluation["transformations"] = [
        {
            "type": "variable_elimination",
            "variable": "initial_capital",
            "expression": "purchase_outlay + as_of_liability + opening_cash",
            "exact": True,
        }
    ]
    diagnostics = []
    if matching._lots is not None:
        diagnostics.append(
            (
                "integer_reconstruction",
                float(np.max(np.abs(raw - np.rint(raw)))),
                "lots",
            )
        )
        evaluation["transformations"].append(
            {
                "type": "holding_lot_reconstruction",
                "constraints_rechecked": True,
            }
        )
    reconciliation = []
    for t, balance in enumerate(evaluation["decision"]["cash_balances"]):
        reconciliation.append(
            (
                f"cash_reconciliation[{t}]",
                abs(scalar(solution[f"cash_{t}"], "solver cash") - balance),
                matching._currency,
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
