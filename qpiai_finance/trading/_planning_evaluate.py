"""Financial replay of an adaptive signed-quantity investment policy."""

from fractions import Fraction

import numpy as np
import pandas as pd
from scipy import sparse

from .._arithmetic import (
    bound_check,
    bound_violation,
    probability_masses,
    product_sum,
    rounded_interval,
    row_products,
    weighted_mean,
)
from .._serialization import identifier_label
from .._validation import lot_residual, matrix, scalar
from ..risk import _tail_mean
from ._planning_funding import evaluate_funding
from ._planning_impact import costs as impact_costs
from .costs import _ticket_cost


def evaluate(model, trades, *, draws, tolerance, _bits=106):
    m = model
    tolerance = scalar(tolerance, "tolerance", minimum=0)
    values = matrix(trades, m._nodes, m._ids, "trades")
    if sparse.issparse(values):
        values = values.toarray()
    buy, sell = np.maximum(values, 0), np.maximum(-values, 0)
    capacity_buy, capacity_sell = m._capacities()
    original_trades = np.fromiter(
        map(Fraction, values.flat), dtype=object
    ).reshape(values.shape)
    holdings = np.empty(values.shape, dtype=object)
    count = len(m._nodes)
    closing, available, interest, dividends, short_fees = (
        np.zeros(count, dtype=object) for _ in range(5)
    )
    purchases = np.asarray(
        [
            product_sum((quotes, quantities))
            for quotes, quantities in zip(m._ask, buy)
        ],
        dtype=object,
    )
    proceeds = np.asarray(
        [
            product_sum((quotes, quantities))
            for quotes, quantities in zip(m._bid, sell)
        ],
        dtype=object,
    )
    # A nonzero ticket incurs its full fee, independent of verification tol.
    rates = np.where(values >= 0, m._buy_fees, m._sell_fees)
    fees = np.asarray(
        [
            sum(
                _ticket_cost(Fraction(rate) * abs(q), Fraction(fixed), q != 0)
                for rate, fixed, q in zip(row, charges, quantities)
            )
            for row, charges, quantities in zip(
                rates, m._fixed, original_trades
            )
        ],
        dtype=object,
    )
    cost_values, cost_errors = impact_costs(
        m, values, original=True, bits=_bits
    )
    impact = np.asarray([sum(row) for row in cost_values], dtype=object)
    impact_error = np.asarray([sum(row) for row in cost_errors], dtype=object)
    cash_error = np.full(count, Fraction(0), dtype=object)
    available_error, interest_error = cash_error.copy(), cash_error.copy()
    needs_precision = any(
        rounded_interval(value, error) is None
        for value, error in zip(impact, impact_error) if error
    )
    spreads = (
        purchases
        - proceeds
        - np.asarray(
            [
                product_sum((prices, quantities))
                for prices, quantities in zip(m._prices, values)
            ],
            dtype=object,
        )
    )
    rows = []

    def check(name, value, low, high, unit, *, error=0):
        nonlocal needs_precision
        reported = float(value)
        if not np.isfinite(reported):
            raise ValueError("planning calculations exceed float64 range")
        violation = bound_violation(value, low, high)
        satisfied = violation <= tolerance
        if error:
            violation, verified = bound_check(
                value, low, high, tolerance, error=error
            )
            needs_precision |= verified is None or (
                rounded_interval(value, error) is None
            )
            satisfied = False if verified is None else verified
        rows.append(
            (
                name,
                reported,
                low,
                high,
                float(violation),
                satisfied,
                unit,
            )
        )

    funding, draws, funding_table, facility_tables = evaluate_funding(
        m, draws, check
    )
    for k, parent in enumerate(m._tree._parents):
        opening = (
            np.fromiter(map(Fraction, m._opening), dtype=object)
            if parent < 0
            else np.fromiter(
                (
                    Fraction(factor) * q
                    for factor, q in zip(m._splits[k], holdings[parent])
                ),
                dtype=object,
            )
        )
        available[k] = Fraction(m._cash) if parent < 0 else closing[parent]
        if parent >= 0:
            previous = closing[parent]
            error = cash_error[parent]
            if error:
                if previous - error >= 0:
                    factor = Fraction(m._deposit[k])
                    interest_factor = abs(factor - 1)
                elif previous + error <= 0:
                    factor = Fraction(m._borrowing[k])
                    interest_factor = abs(factor - 1)
                else:
                    factor = Fraction(max(m._deposit[k], m._borrowing[k]))
                    interest_factor = max(
                        abs(Fraction(m._deposit[k]) - 1),
                        abs(Fraction(m._borrowing[k]) - 1),
                    )
                available_error[k] = factor * error
                interest_error[k] = interest_factor * error
            interest[k] = (Fraction(m._deposit[k]) - 1) * max(previous, 0) - (
                Fraction(m._borrowing[k]) - 1
            ) * max(-previous, 0)
            dividends[k] = product_sum((m._dividends[k], holdings[parent]))
            short_fees[k] = product_sum(
                (m._short_fees[k], np.maximum(-holdings[parent], 0))
            )
            available[k] += interest[k] + dividends[k] - short_fees[k]
        available[k] += Fraction(m._flows[k])
        available[k] += funding["net_funding_cash_flow"][k]
        holdings[k] = opening + original_trades[k]
        closing[k] = (
            available[k] - purchases[k] + proceeds[k] - fees[k] - impact[k]
        )
        cash_error[k] = available_error[k] + impact_error[k]
        check(
            f"credit[{k}]", closing[k], -m._credit[k], np.inf, m.currency,
            error=cash_error[k],
        )
        if m._settlement == "prefunded":
            check(
                f"prefunding[{k}]",
                available[k] - purchases[k] - fees[k] - impact[k],
                -m._credit[k],
                np.inf,
                m.currency,
                error=cash_error[k],
            )
        if m._cash_limits is not None:
            check(
                f"cash[{k}]",
                closing[k],
                m._cash_limits[0][k],
                m._cash_limits[1][k],
                m.currency,
                error=cash_error[k],
            )
        for i in range(len(m._ids)):
            check(
                f"buy[{k},{i}]",
                buy[k, i],
                0,
                capacity_buy[k, i],
                "asset_units",
            )
            check(
                f"sell[{k},{i}]",
                sell[k, i],
                0,
                capacity_sell[k, i],
                "asset_units",
            )
            check(
                f"borrow[{k},{i}]",
                holdings[k, i],
                -m._borrow[k, i],
                np.inf,
                "asset_units",
            )
            if m._position_limits is not None:
                check(
                    f"position[{k},{i}]",
                    holdings[k, i],
                    m._position_limits[0][k, i],
                    m._position_limits[1][k, i],
                    "asset_units",
                )
            if values[k, i] != 0:
                check(
                    f"minimum_trade[{k},{i}]",
                    abs(values[k, i]),
                    m._minimum[k, i],
                    np.inf,
                    "asset_units",
                )
            if m._lots[k, i] > 0:
                check(
                    f"lots[{k},{i}]",
                    lot_residual(values[k, i], m._lots[k, i]),
                    0,
                    0,
                    "lots",
                )
        if m._turnover is not None:
            check(
                f"turnover[{k}]",
                product_sum((m._prices[k], abs(original_trades[k]))),
                0,
                m._turnover[k],
                m.currency,
            )
        if m._gross is not None:
            check(
                f"gross[{k}]",
                product_sum((m._prices[k], abs(holdings[k]))),
                0,
                m._gross[k],
                m.currency,
            )
        for ids, coefficients, low, high, units in m._exposures:
            actual = row_products(coefficients, holdings[k])
            for j, (name, total) in enumerate(zip(ids, actual)):
                check(
                    f"exposure[{k},{identifier_label(name)}]",
                    total,
                    low[k, j],
                    high[k, j],
                    units[j],
                )

    gross_assets = closing + np.asarray(
        [
            product_sum((prices, quantities))
            for prices, quantities in zip(m._prices, holdings)
        ],
        dtype=object,
    )
    wealth = gross_assets - funding["outstanding_debt"]
    terminal_nodes = m._tree._paths[:, -1]
    terminal = wealth[terminal_nodes]
    terminal_error = cash_error[terminal_nodes]
    uncertain_terminal = any(terminal_error)
    if m._terminal_minimum is not None:
        for s, value in enumerate(terminal):
            check(
                f"terminal_wealth[{s}]",
                value,
                m._terminal_minimum[s],
                np.inf,
                m.currency,
                error=terminal_error[s],
            )
    probabilities = m._tree._probabilities
    source_mean = (
        None
        if probabilities is None
        else weighted_mean(terminal, probabilities)
    )
    mean_error = (
        0
        if probabilities is None or not uncertain_terminal
        else weighted_mean(terminal_error, probabilities)
    )
    mean = None if source_mean is None else float(source_mean)
    if source_mean is not None:
        needs_precision |= rounded_interval(source_mean, mean_error) is None
    worst = float(min(terminal))
    worst_error = 0 if not uncertain_terminal else max(
        min(terminal) - min(terminal - terminal_error),
        min(terminal + terminal_error) - min(terminal),
    )
    needs_precision |= rounded_interval(min(terminal), worst_error) is None
    objective = mean if m._objective == "expected_wealth" else worst
    tail = None
    if (
        m._objective == "terminal_expected_shortfall"
        or m._tail_limit is not None
    ):
        masses, total = probability_masses(probabilities)

    def expected_shortfall(target, confidence, wealth_values=terminal):
        losses = np.asarray(
            [
                Fraction(value) - wealth
                for value, wealth in zip(target, wealth_values)
            ],
            dtype=object,
        )
        order = np.argsort(losses, kind="stable")[::-1]
        measure = _tail_mean(losses[order], masses[order], total, confidence)
        return losses, measure

    def tail_error(target, confidence, value):
        if not uncertain_terminal:
            return 0
        lower = expected_shortfall(
            target, confidence, terminal + terminal_error
        )[1]
        upper = expected_shortfall(
            target, confidence, terminal - terminal_error
        )[1]
        return max(value - lower, upper - value)

    if m._objective == "terminal_expected_shortfall":
        losses, source_tail = expected_shortfall(m._target, m._confidence)
        tail = float(source_tail)
        error = tail_error(m._target, m._confidence, source_tail)
        needs_precision |= rounded_interval(source_tail, error) is None
        objective = tail
    if m._tail_limit is not None:
        cap, target, level = m._tail_limit
        hard_losses, source_tail = expected_shortfall(target, level)
        hard_tail = float(source_tail)
        check(
            "expected_shortfall", source_tail, -np.inf, cap, m.currency,
            error=tail_error(target, level, source_tail),
        )
    else:
        hard_tail = None
    for amounts, errors in (
        (closing, cash_error), (available, available_error),
        (wealth, cash_error), (interest, interest_error),
    ):
        needs_precision |= any(
            rounded_interval(value, error) is None
            for value, error in zip(amounts, errors) if error
        )
    if needs_precision:
        return evaluate(
            model, trades, draws=draws, tolerance=tolerance, _bits=_bits * 2
        )
    holdings, closing, available, interest, dividends, short_fees = (
        np.asarray(v, dtype=float)
        for v in (
            holdings,
            closing,
            available,
            interest,
            dividends,
            short_fees,
        )
    )
    purchases, proceeds, fees, impact, spreads = (
        np.asarray(v, dtype=float)
        for v in (purchases, proceeds, fees, impact, spreads)
    )
    gross_assets, wealth, terminal = (
        np.asarray(v, dtype=float) for v in (gross_assets, wealth, terminal)
    )
    funding = {name: np.asarray(v, dtype=float) for name, v in funding.items()}
    if not all(
        np.isfinite(v).all()
        for v in (
            wealth,
            closing,
            available,
            holdings,
            interest,
            dividends,
            short_fees,
            purchases,
            proceeds,
            fees,
            impact,
            spreads,
            *funding.values(),
        )
    ) or not np.isfinite(objective):
        raise ValueError("planning calculations exceed float64 range")
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
    ledger = m._tree.nodes
    ledger["available_cash"] = available
    ledger["interest"] = interest
    ledger["dividends"] = dividends
    ledger["short_fees"] = short_fees
    ledger["external_flow"] = m._flows.copy()
    for name, amounts in funding.items():
        ledger[name] = amounts
    ledger["purchase_outlay"] = purchases
    ledger["sale_proceeds"] = proceeds
    ledger["trading_fees"] = fees
    ledger["market_impact"] = impact
    ledger["spread_cost"] = spreads
    ledger["closing_cash"] = closing
    ledger["wealth"] = wealth
    ledger["gross_assets"] = gross_assets
    ledger.attrs["currency"] = m.currency
    cases = pd.DataFrame(
        {"terminal_wealth": terminal}, index=m._tree.scenario_ids
    )
    if probabilities is not None:
        cases["probability"] = probabilities.copy()
    if m._objective == "terminal_expected_shortfall":
        cases["target"] = m._target.copy()
        cases["loss"] = np.asarray(losses, dtype=float)
    if m._tail_limit is not None:
        cases["hard_tail_target"] = m._tail_limit[1].copy()
        cases["hard_tail_loss"] = np.asarray(hard_losses, dtype=float)
    cases.attrs["currency"] = m.currency
    return {
        "objective": float(objective),
        "transformations": (
            [
                {
                    "type": "market_impact_epigraph",
                    "cash_upper_bounds_absent": True,
                    "source_cash_recomputed": True,
                    "exact_financial_projection": True,
                }
            ]
            if m._has_nonlinear_impact and m._cash_monotone
            else []
        ),
        "feasible": bool(constraints.satisfied.all()),
        "constraints": constraints,
        "decision": {
            **({"draws": draws} if m._funding else {}),
            "trades": pd.DataFrame(
                values.copy(), index=m.node_ids, columns=m.asset_ids
            ),
            "holdings": pd.DataFrame(
                holdings, index=m.node_ids, columns=m.asset_ids
            ),
            "cash_balances": pd.Series(closing, index=m.node_ids, name="cash"),
        },
        "metrics": {
            "expected_terminal_wealth": mean,
            "worst_terminal_wealth": worst,
            "terminal_expected_shortfall": tail,
            "hard_expected_shortfall": hard_tail,
            "currency": m.currency,
        },
        "tables": {
            "investment_funding": funding_table,
            "investment_accounts": ledger,
            "investment_scenarios": cases,
            "investment_information": m._tree.information,
            "investment_stage_times": m._tree.times.to_frame(),
            **facility_tables,
        },
        "costs": {
            "funding_interest_by_node": funding["funding_interest"].tolist(),
            "funding_fees_by_node": funding["funding_fees"].tolist(),
            "impact_by_node": impact.tolist(),
            "trading_fees_by_node": fees.tolist(),
            "spread_by_node": spreads.tolist(),
            "short_fees_by_node": short_fees.tolist(),
            "currency": m.currency,
        },
    }
