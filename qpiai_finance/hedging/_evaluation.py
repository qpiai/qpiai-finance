"""Independent hedge risk, position and upfront execution accounting."""

from fractions import Fraction
from math import fsum

import numpy as np
import pandas as pd

from .._arithmetic import offset_totals, product_sum, row_products
from .._result_checks import record_reconciliation
from .._validation import (
    copy_index,
    lot_quantities,
    lot_residual,
    scalar,
    vector,
)
from ..risk import _quadratic_risk, _risk_product


def _affine_difference(before, change, target):
    """Retain small affine changes without subtracting rounded totals."""
    values = -target.copy()
    for i in np.flatnonzero(np.isfinite(target)):
        opening, increment, limit = before[i], change[i], target[i]
        try:
            values[i] = fsum((opening, increment, -limit))
        except OverflowError:
            values[i] = fsum((opening, -limit, increment))
    return values


def evaluate(hedge, quantities, *, tolerance):
    tolerance = scalar(tolerance, "tolerance", minimum=0)
    quantities = vector(quantities, hedge._ids, "hedges")
    positions = hedge._current + quantities
    change, exposure, residual, lower_residual, upper_residual = np.empty(
        (5, len(hedge._risks))
    )
    source_residual = np.empty(len(hedge._risks), dtype=object)
    changes = row_products(hedge._sensitivities, quantities)
    for i, (before, increment) in enumerate(zip(hedge._exposure, changes)):
        (
            change[i],
            exposure[i],
            lower_residual[i],
            upper_residual[i],
        ) = offset_totals(
            increment,
            offsets=(
                (),
                (before,),
                (before, -hedge._risk_lower[i]),
                (before, -hedge._risk_upper[i]),
            ),
        )
        source_residual[i] = (
            increment + Fraction(before) - Fraction(hedge._target[i])
        )
        residual[i] = float(source_residual[i])
    quotes = np.where(quantities >= 0, hedge._ask, hedge._bid)
    rates = np.where(quantities >= 0, hedge._buy_cost, hedge._sell_cost)
    fees = rates * np.abs(quantities)
    fee_total = product_sum((rates, np.abs(quantities)))
    spreads, spread_total = np.zeros(len(quantities)), Fraction(0)
    for i in np.flatnonzero((quantities != 0) & (quotes != hedge._prices)):
        spread = product_sum(
            ([quotes[i], -hedge._prices[i]], [quantities[i], quantities[i]])
        )
        spreads[i] = float(spread)
        spread_total += spread
    total_cost = spread_total + fee_total
    cost = float(total_cost)
    spread_cost, fee_cost = float(spread_total), float(fee_total)
    position_lower = _affine_difference(
        hedge._current, quantities, hedge._position_lower
    )
    position_upper = _affine_difference(
        hedge._current, quantities, hedge._position_upper
    )
    rows = []

    def check(name, value, lower, upper, unit, *, violation=None):
        if violation is None:
            violation = max(lower - value, value - upper, 0.0)
        rows.append(
            (
                name,
                value,
                lower,
                upper,
                violation,
                violation <= tolerance,
                unit,
            )
        )

    for i, instrument in enumerate(hedge._ids):
        check(
            f"trade[{i}:{instrument}]",
            quantities[i],
            hedge._lower[i],
            hedge._upper[i],
            "instrument_units",
        )
        check(
            f"position[{i}:{instrument}]",
            positions[i],
            hedge._position_lower[i],
            hedge._position_upper[i],
            "instrument_units",
            violation=max(-position_lower[i], position_upper[i], 0.0),
        )
        if hedge._lots is not None:
            check(
                f"trade_lots[{i}]",
                lot_residual(quantities[i], hedge._lots[i]),
                0,
                0,
                "lots",
            )
    for i, risk in enumerate(hedge._risks):
        check(
            f"risk[{i}:{risk}]",
            exposure[i],
            hedge._risk_lower[i],
            hedge._risk_upper[i],
            hedge._units[i],
            violation=max(-lower_residual[i], upper_residual[i], 0.0),
        )
        if hedge._objective == "hedge_cost":
            check(
                f"exact_match[{i}]",
                exposure[i],
                hedge._target[i],
                hedge._target[i],
                hedge._units[i],
                violation=abs(residual[i]),
            )
    metrics = {
        "transaction_cost": cost,
        "spread_cost": spread_cost,
        "fees": fee_cost,
    }
    if hedge._cash is not None:
        (cash,) = offset_totals(
            product_sum((-quotes, quantities)),
            offsets=((hedge._cash, -fee_total),),
        )
        check("execution_cash", cash, 0, np.inf, hedge._currency)
        metrics["cash_after"] = cash
    if hedge._capital is not None:
        coefficients, maximum = hedge._capital
        signed_coefficients = coefficients * np.sign(positions)
        capital, excess = offset_totals(
            product_sum(
                (signed_coefficients, hedge._current),
                (signed_coefficients, quantities),
            ),
            offsets=((), (-maximum,)),
        )
        metrics["capital_used"] = capital
        check(
            "capital",
            capital,
            0,
            maximum,
            hedge._currency,
            violation=max(excess, 0.0),
        )
    objective = cost
    if hedge._objective == "hedge_mismatch":
        mismatch = _quadratic_risk(
            source_residual,
            _risk_product(hedge._weights, source_residual, original=True),
            name="mismatch cost",
        )
        metrics["mismatch_cost"] = float(mismatch)
        objective = float(mismatch + Fraction(hedge._cost_weight) * total_cost)
    if not np.isfinite(
        [objective, *metrics.values(), *exposure, *positions]
    ).all():
        raise ValueError("hedge quantities or metrics exceed float64 range")
    from ._scenarios import evaluate as evaluate_scenarios

    scenario_objective, scenario_metrics, scenario_table = evaluate_scenarios(
        hedge, quantities, total_cost, check
    )
    if scenario_objective is not None:
        objective = scenario_objective
    metrics.update(scenario_metrics)
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
    result = {
        "objective": float(objective),
        "feasible": bool(constraints.satisfied.all()),
        "constraints": constraints,
        "metrics": metrics,
        "decision": {
            "hedges": pd.Series(
                quantities, index=copy_index(hedge._ids), name="hedge_quantity"
            ),
            "positions": pd.Series(
                positions, index=copy_index(hedge._ids), name="position"
            ),
            "risk_exposures": pd.Series(
                exposure, index=copy_index(hedge._risks), name="exposure"
            ),
        },
        "costs": {
            "currency": hedge._currency,
            "spread": spread_cost,
            "fees": fee_cost,
        },
        "tables": {
            "hedges": pd.DataFrame(
                {
                    "before": hedge._current,
                    "trade": quantities,
                    "after": positions,
                    "spread": spreads,
                    "fees": fees,
                },
                index=copy_index(hedge._ids),
            ),
            "risk_exposures": pd.DataFrame(
                {
                    "before": hedge._exposure,
                    "change": change,
                    "after": exposure,
                    "target": hedge._target,
                    "residual": residual,
                    "unit": hedge._units,
                },
                index=copy_index(hedge._risks),
            ),
        },
    }
    if not len(hedge._risks):
        del result["decision"]["risk_exposures"]
        del result["tables"]["risk_exposures"]
    if scenario_table is not None:
        result["tables"]["hedge_scenarios"] = scenario_table
    return result


def evaluate_solution(hedge, solution, *, tolerance):
    raw = np.array(
        [
            scalar(solution[f"hedge_{i}"], "solver hedge quantity")
            for i in range(len(hedge._ids))
        ]
    )
    quantities = (
        raw
        if hedge._lots is None
        else lot_quantities(np.rint(raw), hedge._lots)
    )
    evaluation = evaluate(hedge, quantities, tolerance=tolerance)
    if hedge._lots is not None:
        residual = float(np.max(np.abs(raw - np.rint(raw))))
        evaluation["constraints"].loc["integer_reconstruction"] = [
            residual,
            0,
            0,
            residual,
            residual <= tolerance,
            "lots",
        ]
        evaluation["feasible"] &= residual <= tolerance
        evaluation["transformations"] = [
            {
                "type": "hedge_lot_reconstruction",
                "maximum_lot_residual": residual,
                "constraints_rechecked": True,
            }
        ]
    reconciliation = []
    for i in range(len(hedge._risks)):
        if f"risk_residual_{i}" in solution:
            value = abs(
                scalar(solution[f"risk_residual_{i}"], "solver risk residual")
                - evaluation["tables"]["risk_exposures"].residual.iloc[i]
            )
            reconciliation.append(
                (f"risk_reconciliation[{i}]", value, hedge._units[i])
            )
    evaluation["feasible"] = bool(evaluation["constraints"].satisfied.all())
    record_reconciliation(evaluation, reconciliation, tolerance=tolerance)
    return evaluation
