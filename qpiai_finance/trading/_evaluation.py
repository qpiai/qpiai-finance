"""Independent execution costs, order completion and chronological cash."""

from fractions import Fraction

import numpy as np
import pandas as pd

from .._arithmetic import (
    bound_check,
    bound_violation,
    product_sum,
    rounded_interval,
    row_products,
)
from .._validation import (
    copy_frame,
    copy_index,
    lot_quantities,
    lot_residual,
    scalar,
    vector,
)
from ..risk import FactorRisk, _quadratic_risk
from .costs import _power_costs, _quoted_cost, _ticket_cost


def _impact(execution, quantities, bits):
    values, errors = _power_costs(
        quantities, execution._quadratic, execution._power,
        original=True, bits=bits,
    )
    piecewise = np.full(len(quantities), Fraction(0), dtype=object)
    for j, identifier in enumerate(execution._op_ids):
        if identifier in execution._curves:
            piecewise[j] = _quoted_cost(
                quantities[j], execution._curves[identifier]
            )
    return values + piecewise, piecewise, errors


def evaluate(
    execution, executions, *, tolerance, return_state=False, _bits=106
):
    e = execution
    tolerance = scalar(tolerance, "tolerance", minimum=0)
    if len(e._op_ids):
        quantities = vector(executions, e._op_ids, "executions")
    else:
        if isinstance(executions, (dict, pd.Series)) and not len(executions):
            quantities = np.zeros(0)
        else:
            from .._validation import numeric

            quantities = numeric(executions, "executions", ndim=1)
            if len(quantities):
                raise ValueError(
                    "executions must be empty without opportunities"
                )
    opportunities = e._opportunities
    assets = e._ids.get_indexer(opportunities.asset)
    slots = e._slots.get_indexer(opportunities.slot)
    venues = e.venue_ids.get_indexer(opportunities.venue)
    size = np.abs(quantities)
    source_quantities = np.fromiter(map(Fraction, quantities), dtype=object)
    source_size = np.abs(source_quantities)
    active = size > 0
    side = np.where(
        quantities >= 0, opportunities.ask_price, opportunities.bid_price
    )
    source_fees = _ticket_cost(
        np.fromiter(
            (Fraction(rate) * q for rate, q in zip(e._fees, source_size)),
            dtype=object,
        ),
        np.fromiter(map(Fraction, e._fixed), dtype=object),
        active,
    )
    with np.errstate(over="raise", invalid="raise"):
        source_impact, source_piecewise, impact_error = _impact(e, size, _bits)
    impact = np.asarray(source_impact, float)
    piecewise = np.asarray(source_piecewise, float)
    needs_precision = any(
        rounded_interval(value, error) is None
        for value, error in zip(source_impact, impact_error) if error
    )
    source_spread = np.fromiter(
        (
            (Fraction(quote) - Fraction(mark)) * q
            for quote, mark, q in zip(
                side, opportunities.price, source_quantities
            )
        ),
        dtype=object,
    )
    source_price_change = np.fromiter(
        (
            (Fraction(mark) - Fraction(arrival)) * q
            for mark, arrival, q in zip(
                opportunities.price, e._arrival[assets], source_quantities
            )
        ),
        dtype=object,
    )
    source_shortfall = (
        source_price_change + source_spread + source_fees + source_impact
    )
    fees = np.asarray(source_fees, float)
    spread = np.asarray(source_spread, float)
    shortfall = np.asarray(source_shortfall, float)
    needs_precision |= any(
        rounded_interval(value, error) is None
        for value, error in zip(source_shortfall, impact_error) if error
    )
    t, n = len(e._slots), len(e._ids)
    trades = np.full((t, n), Fraction(0), dtype=object)
    np.add.at(trades, (slots, assets), source_quantities)
    cumulative = np.cumsum(trades, axis=0)
    orders = np.fromiter(map(Fraction, e._orders), dtype=object)
    opening = np.fromiter(map(Fraction, e._opening), dtype=object)
    positions = opening + cumulative
    remaining = orders - cumulative
    direction = e._direction.astype(int)
    remaining_magnitude = direction * remaining
    checks = []
    eligible = np.zeros(len(e._op_ids), dtype=bool)

    def check(name, value, low, high, unit, *, error=0):
        nonlocal needs_precision
        if isinstance(value, (bool, np.bool_)):
            value = int(value)
        reported = float(value)
        if not np.isfinite(reported):
            raise ValueError(
                "execution quantities or costs exceed float64 range"
            )
        violation = bound_violation(value, low, high)
        satisfied = (
            violation == 0 if unit == "boolean" else violation <= tolerance
        )
        if error:
            violation, verified = bound_check(
                value, low, high, tolerance, error=error
            )
            needs_precision |= verified is None or (
                rounded_interval(value, error) is None
            )
            satisfied = False if verified is None else verified
        checks.append(
            (
                name,
                reported,
                float(low),
                float(high),
                float(violation),
                satisfied,
                unit,
            )
        )

    for j, identifier in enumerate(e._op_ids):
        i, k = assets[j], slots[j]
        allowed = (
            e._release[i] <= e._times[k] <= e._deadlines[i]
            and opportunities.capacity.iloc[j] > 0
            and e._orders[i] != 0
        )
        eligible[j] = allowed
        check(
            f"eligible[{j}:{identifier}]",
            not active[j] or allowed,
            1,
            1,
            "boolean",
        )
        check(
            f"direction[{j}:{identifier}]",
            e._direction[i] * quantities[j],
            0,
            np.inf,
            "asset_units",
        )
        if e._orders[i] == 0:
            check(f"zero_order[{j}]", not active[j], 1, 1, "boolean")
        check(
            f"capacity[{j}]",
            size[j],
            0,
            opportunities.capacity.iloc[j],
            "asset_units",
        )
        minimum = e._minimum[j]
        if e._lots is not None:
            count = size[j] / e._lots[i]
            minimum = max(minimum, e._lots[i])
            check(
                f"lots[{j}]", lot_residual(size[j], e._lots[i]), 0, 0, "lots"
            )
            check(
                f"positive_lot[{j}]",
                not active[j] or np.rint(count) >= 1,
                1,
                1,
                "boolean",
            )
        if active[j] and minimum > 0:
            check(
                f"minimum_trade[{j}]", size[j], minimum, np.inf, "asset_units"
            )
        if identifier in e._curves:
            check(
                f"impact_domain[{j}]",
                size[j],
                0,
                e._curves[identifier].quantity.iloc[-1],
                "asset_units",
            )
        if quantities[j] < 0:
            check(
                f"sale_price[{j}]",
                Fraction(side[j]) * source_size[j] - source_impact[j],
                0,
                np.inf,
                e.currency,
                error=impact_error[j],
            )
    market_volume = np.full((t, n), Fraction(0), dtype=object)
    np.add.at(market_volume, (slots, assets), source_size)
    venue_notional = np.full((t, len(e.venue_ids)), Fraction(0), dtype=object)
    np.add.at(
        venue_notional,
        (slots, venues),
        np.fromiter(
            (
                Fraction(price) * q
                for price, q in zip(opportunities.price, source_size)
            ),
            dtype=object,
        ),
    )
    risk_variance = np.zeros(t)
    source_risk = np.full(t, Fraction(0), dtype=object)
    if e._risk is not None:
        for k, duration in enumerate(e._durations()):
            if duration == 0:
                continue
            variance_rate = _quadratic_risk(
                remaining[k],
                e._risk_apply(remaining[k], original=True),
                name="inventory price variance",
            )
            try:
                with np.errstate(over="raise", invalid="raise"):
                    source_risk[k] = Fraction(duration) * variance_rate
                    risk_variance[k] = float(source_risk[k])
            except FloatingPointError as error:
                raise ValueError(
                    "execution risk exceeds float64 range"
                ) from error
    closing = np.empty(t, dtype=object)
    before = np.zeros(t)
    prefunded = np.zeros(t)
    floor = np.maximum(-e._credit, e._cash_minimum)
    ledgers = []
    cash = Fraction(e._cash)
    cash_error = Fraction(0)
    for k, slot in enumerate(e._slots):
        opening_cash = cash
        indices = np.flatnonzero(slots == k)
        cash_before = cash + Fraction(e._flows[k])
        before_error = cash_error
        before[k] = float(cash_before)
        cost = sum(source_fees[indices]) + sum(source_impact[indices])
        slot_error = sum(impact_error[indices])
        cash_error += slot_error
        needs_precision |= rounded_interval(cost, slot_error) is None
        buys = indices[quantities[indices] > 0]
        sells = indices[quantities[indices] < 0]
        purchases = product_sum((side[buys], source_size[buys]))
        sales = product_sum((side[sells], source_size[sells]))
        prefunded_cash = cash_before - purchases - cost
        prefunded[k] = float(prefunded_cash)
        cash = prefunded_cash + sales
        closing[k] = cash
        check(
            f"cash_before[{k}:{slot}]",
            cash_before,
            floor[k],
            np.inf,
            e.currency,
            error=before_error,
        )
        check(
            f"cash_after[{k}:{slot}]", cash, floor[k], np.inf, e.currency,
            error=cash_error,
        )
        if e._settlement == "prefunded":
            check(
                f"prefunded_cash[{k}]",
                prefunded_cash,
                floor[k],
                np.inf,
                e.currency,
                error=cash_error,
            )
        ledgers.append(
            (
                slot,
                e._times[k],
                *(
                    float(value)
                    for value in (
                        e._flows[k],
                        opening_cash,
                        cash_before,
                        prefunded_cash
                        if e._settlement == "prefunded"
                        else np.nan,
                        purchases,
                        sales,
                        cost,
                        cash,
                        e._credit[k],
                        floor[k],
                        max(-cash, 0),
                        max(
                            -opening_cash,
                            -cash_before,
                            -cash,
                            -prefunded_cash
                            if e._settlement == "prefunded"
                            else 0,
                            0,
                        ),
                    )
                ),
            )
        )
        for i, asset in enumerate(e._ids):
            check(
                f"remaining[{k}:{i}:{asset}]",
                remaining_magnitude[k, i],
                0,
                abs(e._orders[i]),
                "asset_units",
            )
            check(
                f"borrow[{k}:{i}]",
                positions[k, i],
                -e._borrow[k, i],
                np.inf,
                "asset_units",
            )
            if e._position_limits is not None:
                check(
                    f"position[{k}:{i}]",
                    positions[k, i],
                    e._position_limits[0][k, i],
                    e._position_limits[1][k, i],
                    "asset_units",
                )
            if e._participation is not None:
                volume, rate = e._participation
                check(
                    f"participation[{k}:{i}]",
                    market_volume[k, i],
                    0,
                    Fraction(volume[k, i]) * Fraction(rate[k, i]),
                    "asset_units",
                )
        if e._venue_limits is not None:
            for v, venue in enumerate(e.venue_ids):
                check(
                    f"venue_notional[{k}:{v}:{venue}]",
                    venue_notional[k, v],
                    0,
                    e._venue_limits[k, v],
                    e.currency,
                )
        if e._gross_limit is not None:
            gross = product_sum((e._arrival, np.abs(positions[k])))
            check(
                f"gross_notional[{k}]", gross, 0, e._gross_limit[k], e.currency
            )
        for group, (ids, values, low, high, units) in enumerate(e._exposures):
            actual = list(row_products(values, positions[k]))
            for h, identifier in enumerate(ids):
                check(
                    f"exposure[{group}:{k}:{h}:{identifier}]",
                    actual[h],
                    low[k, h],
                    high[k, h],
                    units[h],
                )
    for i, asset in enumerate(e._ids):
        if e._hard[i]:
            check(
                f"completion[{i}:{asset}]",
                cumulative[-1, i],
                e._orders[i],
                e._orders[i],
                "asset_units",
            )
    turnover = product_sum((e._arrival[assets], source_size))
    if e._turnover_limit is not None:
        check("turnover_notional", turnover, 0, e._turnover_limit, e.currency)
    unfilled = np.maximum(remaining_magnitude[-1], 0)
    source_residual_cost = (
        np.full(n, Fraction(0), dtype=object)
        if e._underfill is None
        else np.fromiter(
            (
                Fraction(0) if required else Fraction(rate) * q
                for rate, q, required in zip(e._underfill, unfilled, e._hard)
            ),
            dtype=object,
        )
    )
    residual_cost = np.asarray(source_residual_cost, float)
    risk_costs = source_risk * Fraction(e._risk_aversion)
    risk_cost = float(sum(risk_costs))
    executed_shortfall = float(sum(source_shortfall))
    underfill_cost = float(sum(source_residual_cost))
    objective = float(
        sum(source_shortfall) + sum(source_residual_cost) + sum(risk_costs)
    )
    total_error = sum(impact_error)
    for value in (
        sum(source_impact), sum(source_shortfall),
        sum(source_shortfall) + sum(source_residual_cost) + sum(risk_costs),
    ):
        needs_precision |= rounded_interval(value, total_error) is None
    if needs_precision:
        return evaluate(
            execution, executions, tolerance=tolerance,
            return_state=return_state, _bits=_bits * 2,
        )
    reported_closing = np.asarray(closing, float)
    if not np.isfinite(
        np.r_[
            objective,
            fees,
            impact,
            shortfall,
            risk_variance,
            reported_closing,
            before,
            prefunded,
        ]
    ).all():
        raise ValueError("execution values exceed float64 range")
    schedule = copy_frame(opportunities)
    schedule["time"] = e._times[slots]
    schedule["quantity"] = quantities
    schedule["eligible"] = eligible
    schedule["order_side"] = np.where(
        e._direction[assets] > 0,
        "buy",
        np.where(e._direction[assets] < 0, "sell", "none"),
    )
    schedule["side_price"] = side
    schedule["spread_cost"] = spread
    schedule["fees"] = fees
    schedule["temporary_impact"] = impact
    schedule["piecewise_impact"] = piecewise
    schedule["predicted_shortfall"] = shortfall
    order_table = pd.DataFrame(
        {
            "target_quantity": e._orders,
            "opening_holdings": e._opening,
            "executed_quantity": np.asarray(cumulative[-1], float),
            "final_holdings": np.asarray(positions[-1], float),
            "signed_residual": np.asarray(remaining[-1], float),
            "unfilled_quantity": np.asarray(unfilled, float),
            "required": e._hard,
            "underfill_cost": residual_cost,
            "release": e._release,
            "deadline": e._deadlines,
        },
        index=copy_index(e._ids),
    )
    order_table["completion_status"] = np.where(
        unfilled <= tolerance,
        "complete",
        np.where(
            direction * cumulative[-1] > tolerance,
            "partial",
            "unfilled",
        ),
    )
    order_table.loc[
        direction * cumulative[-1] > np.abs(orders) + Fraction(tolerance),
        "completion_status",
    ] = "overfilled"
    ledger = pd.DataFrame(
        ledgers,
        columns=[
            "slot",
            "time",
            "external_flow",
            "opening_cash",
            "cash_before",
            "cash_before_sale_proceeds",
            "purchase_value",
            "sale_value",
            "charges",
            "cash_after",
            "credit_limit",
            "cash_floor",
            "credit_used",
            "peak_credit_used",
        ],
    ).set_index("slot")
    constraints = pd.DataFrame(
        checks,
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
    trades_table = pd.DataFrame(
        np.asarray(trades, float),
        index=copy_index(e._slots),
        columns=copy_index(e._ids),
    )
    positions_table = pd.DataFrame(
        np.asarray(positions, float),
        index=copy_index(e._slots),
        columns=copy_index(e._ids),
    )
    metrics = {
        "predicted_executed_shortfall": executed_shortfall,
        "price_change_cost": float(sum(source_price_change)),
        "spread_cost": float(sum(source_spread)),
        "execution_fees": float(sum(source_fees)),
        "temporary_impact": float(sum(source_impact)),
        "underfill_cost": underfill_cost,
        "price_risk_variance": float(sum(source_risk)),
        "price_risk_cost": risk_cost,
        "final_cash": float(closing[-1]),
        "cash_after": float(closing[-1]),
        "final_credit_used": max(-float(closing[-1]), 0),
        "peak_credit_used": float(ledger.peak_credit_used.max()),
        "incomplete_orders": int(np.sum(unfilled > tolerance)),
        "turnover_notional": float(turnover),
    }
    result = {
        "objective": objective,
        "feasible": bool(constraints.satisfied.all()),
        "metrics": metrics,
        "constraints": constraints,
        "decision": {
            "executions": pd.Series(
                quantities, index=copy_index(e._op_ids), name="quantity"
            ),
            "trades": trades_table,
            "holdings": positions_table,
            "remaining_orders": pd.DataFrame(
                np.asarray(remaining, float),
                index=copy_index(e._slots),
                columns=copy_index(e._ids),
            ),
            "unfilled": pd.Series(
                np.asarray(unfilled, float),
                index=copy_index(e._ids),
                name="quantity",
            ),
            "cash_balances": pd.Series(
                reported_closing,
                index=copy_index(e._slots), name="cash",
            ),
        },
        "tables": {
            "execution_schedule": schedule,
            "execution_orders": order_table,
            "execution_cash": ledger,
            "execution_holdings": positions_table,
            "execution_risk": pd.DataFrame(
                {
                    "seconds_to_next_slot": e._durations(),
                    "remaining_price_variance": risk_variance,
                    "risk_cost": np.asarray(risk_costs, float),
                },
                index=copy_index(e._slots),
            ),
        },
        "costs": {
            "currency": e.currency,
            "price_change": metrics["price_change_cost"],
            "spread": metrics["spread_cost"],
            "fees": metrics["execution_fees"],
            "impact": metrics["temporary_impact"],
            "underfill": underfill_cost,
            "risk": risk_cost,
        },
    }
    if return_state:
        return result, {
            "holdings": positions,
            "remaining_orders": remaining,
            "cash_balances": closing,
        }
    return result


def evaluate_solution(execution, solution, *, tolerance):
    e = execution
    assets = e._ids.get_indexer(e._opportunities.asset)
    slots = e._slots.get_indexer(e._opportunities.slot)
    residuals = []
    auxiliary = []
    quantities = np.zeros(len(e._op_ids))

    def residual(name, value, unit="asset_units"):
        residuals.append(
            (
                name,
                value,
                0.0,
                0.0,
                value,
                value <= tolerance,
                unit,
            )
        )

    def diagnostic(name, recorded, rebuilt, unit, relation):
        auxiliary.append(
            (
                name,
                float(recorded),
                float(rebuilt),
                float(Fraction(recorded) - Fraction(rebuilt)),
                unit,
                relation,
            )
        )

    for j, i in enumerate(assets):
        raw = scalar(solution[f"execution_{j}"], "solver execution")
        scale = 1.0 if e._lots is None else e._lots[i]
        value = max(raw, 0.0) if e._lots is None else np.rint(raw)
        if e._lots is not None:
            residual(f"execution_integrality[{j}]", abs(raw - value), "lots")
            value = max(value, 0.0)
        if e._minimum[j] > 0 or e._fixed[j] > 0:
            ticket = scalar(solution[f"ticket_{j}"], "solver ticket")
            chosen = np.rint(ticket)
            residual(
                f"ticket_integrality[{j}]", abs(ticket - chosen), "binary"
            )
            residual(
                f"ticket_domain[{j}]", max(-chosen, chosen - 1, 0), "binary"
            )
            if chosen == 0:
                value = 0.0
            residual(
                f"ticket_presence[{j}]", abs(chosen - (value > 0)), "binary"
            )
        allowed = (
            e._release[i] <= e._times[slots[j]] <= e._deadlines[i]
            and e._opportunities.capacity.iloc[j] > 0
            and e._orders[i] != 0
        )
        if not allowed:
            value = 0.0
        quantities[j] = e._direction[i] * lot_quantities(value, scale)
        residual(f"execution_reconstruction[{j}]", abs(value - raw) * scale)
    evaluation, state = evaluate(
        e, pd.Series(quantities, index=copy_index(e._op_ids)),
        tolerance=tolerance, return_state=True,
    )
    for j in range(len(quantities)):
        impact = evaluation["tables"][
            "execution_schedule"
        ].temporary_impact.iloc[j]
        diagnostic(
            f"impact_{j}",
            solution[f"impact_{j}"],
            impact,
            e.currency,
            "at_least",
        )
        if e._op_ids[j] in e._curves:
            actual = evaluation["tables"][
                "execution_schedule"
            ].piecewise_impact.iloc[j]
            diagnostic(
                f"piecewise_{j}",
                solution[f"piecewise_{j}"],
                actual,
                e.currency,
                "at_least",
            )
    remaining = evaluation["decision"]["remaining_orders"].to_numpy()
    if e._gross_limit is not None:
        opening = np.fromiter(map(Fraction, e._opening), dtype=object)
        gross_changes = abs(state["holdings"]) - abs(opening)
    cash_origin = Fraction(e._cash_origin)
    for k in range(len(e._slots)):
        diagnostic(
            f"cash_change_{k}",
            solution[f"cash_change_{k}"],
            state["cash_balances"][k] - cash_origin,
            e.currency,
            "at_most",
        )
        for i in np.flatnonzero(e._orders != 0):
            diagnostic(
                f"remaining_{k}_{i}",
                solution[f"remaining_{k}_{i}"],
                int(e._direction[i]) * state["remaining_orders"][k, i],
                "asset_units",
                "equal",
            )
            if e._gross_limit is not None:
                diagnostic(
                    f"position_abs_change_{k}_{i}",
                    solution[f"position_abs_change_{k}_{i}"],
                    gross_changes[k, i],
                    "asset_units",
                    "at_least",
                )
        if (
            e._has_risk
            and isinstance(e._risk, FactorRisk)
            and k < len(e._slots) - 1
        ):
            factors = e._risk.factor_exposures(
                pd.Series(remaining[k], index=copy_index(e._ids))
            )
            for f, value in enumerate(factors):
                diagnostic(
                    f"factor_{k}_{f}",
                    solution[f"factor_{k}_{f}"],
                    value,
                    "supplied_price_factor_units",
                    "equal",
                )
    diagnostics = pd.DataFrame(
        residuals,
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
    if not diagnostics.empty:
        evaluation["constraints"] = pd.concat(
            [evaluation["constraints"], diagnostics]
        )
    evaluation["feasible"] = bool(evaluation["constraints"].satisfied.all())
    # Costs and state variables can be rebuilt from the primary trades.
    # Lower cash limits remain valid when conservative cost slack is removed.
    evaluation["tables"]["execution_numerical_diagnostics"] = pd.DataFrame(
        auxiliary,
        columns=[
            "variable",
            "solver_value",
            "reconstructed_value",
            "difference",
            "unit",
            "relation",
        ],
    ).set_index("variable")
    evaluation["transformations"] = [
        {
            "type": "execution_reconstruction",
            "source_quantities_rechecked": True,
            "cash_origin": float(cash_origin),
            "primary_reconstruction": [
                {"constraint": row[0], "residual": row[1], "unit": row[-1]}
                for row in residuals
            ],
            "cost_epigraphs": "conservative_cash_recomputed_from_actual_costs",
            "impact": "supplied_temporary_costs",
        }
    ]
    return evaluation
