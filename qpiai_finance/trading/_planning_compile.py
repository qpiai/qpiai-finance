"""Sparse extensive-form investment balances and terminal risk."""

from fractions import Fraction

import numpy as np
from scipy import sparse

from .._arithmetic import float_upper_bound, product_sum
from .._validation import lot_capacity
from ..risk import _shortfall_form
from ._planning_funding import cash_capacity, compile_funding
from ._planning_impact import add_cost_graph


def compile_matrix(model):
    m = model
    count, assets = m._prices.shape
    buys, sells = m._capacities()
    scales = np.where(m._lots > 0, m._lots, 1.0)
    parents = m._tree._parents

    names, lows, highs, integers, objective = [], [], [], [], []
    rows, columns, coefficients, row_low, row_high, labels = (
        [],
        [],
        [],
        [],
        [],
        [],
    )

    def variable(name, low=0.0, high=np.inf, integer=False):
        position = len(names)
        names.append(name)
        lows.append(float(low))
        highs.append(float(high))
        integers.append(int(integer))
        objective.append(0.0)
        return position

    def constraint(terms, low, high, name):
        position = len(labels)
        for column, value in terms:
            if value != 0:
                rows.append(position)
                columns.append(column)
                coefficients.append(float(value))
        row_low.append(float(low))
        row_high.append(float(high))
        labels.append(name)

    funding_events, funding_constants = compile_funding(
        m, variable, constraint
    )
    # Bound cash from the same net obligations used in its equations.
    # Receipts and repayments must cancel before rounding the upper bound.
    qlow, qhigh = np.empty_like(buys), np.empty_like(buys)
    cash_high = np.empty(count)
    funding_cash = cash_capacity(m)
    for k, parent in enumerate(parents):
        low = m._opening if parent < 0 else m._splits[k] * qlow[parent]
        high = m._opening if parent < 0 else m._splits[k] * qhigh[parent]
        qlow[k], qhigh[k] = low - sells[k], high + buys[k]
        available = Fraction(m._cash)
        if parent >= 0:
            previous = cash_high[parent]
            available = Fraction(previous) * Fraction(
                m._deposit[k] if previous >= 0 else m._borrowing[k]
            )
            paying = np.flatnonzero(m._dividends[k])
            dividends = m._dividends[k, paying]
            available += product_sum((
                dividends,
                np.where(dividends >= 0, qhigh[parent, paying],
                         qlow[parent, paying]),
            ))
        maximum = (
            available + Fraction(m._flows[k]) + funding_constants[k]
            + funding_cash[k] + product_sum((m._bid[k], sells[k]))
        )
        cash_high[k] = float_upper_bound(max(Fraction(-m._credit[k]), maximum))
    if not all(np.isfinite(v).all() for v in (qlow, qhigh, cash_high)):
        raise ValueError("planning state bounds exceed float64 range")

    holdings = np.array(
        [
            [
                variable(f"holding_{k}_{i}", qlow[k, i], qhigh[k, i])
                for i in range(assets)
            ]
            for k in range(count)
        ]
    )
    cash = np.array(
        [
            variable(f"cash_{k}", -m._credit[k], cash_high[k])
            for k in range(count)
        ]
    )
    negative_parts = {}

    def negative_part(column, low, high, name):
        if low >= 0:
            return []
        if high <= 0:
            return [(column, -1.0)]
        if column not in negative_parts:
            negative = variable(name, high=-low)
            sign = variable(f"{name}_active", high=1, integer=True)
            constraint(
                [(negative, 1), (column, 1)], 0, np.inf, f"{name}_lower"
            )
            constraint(
                [(negative, 1), (sign, low)], -np.inf, 0, f"{name}_sign"
            )
            constraint(
                [(negative, 1), (column, 1), (sign, high)],
                -np.inf,
                high,
                f"{name}_upper",
            )
            negative_parts[column] = negative
        return [(negative_parts[column], 1.0)]

    for k, parent in enumerate(parents):
        cash_terms = [(cash[k], 1)]
        cash_terms.extend(
            (column, -value) for column, value in funding_events[k]
        )
        balance = (
            Fraction(m._cash) if parent < 0 else 0
        ) + funding_constants[k]
        if parent >= 0:
            cash_terms.append((cash[parent], -m._deposit[k]))
            if m._deposit[k] != m._borrowing[k]:
                cash_terms.extend(
                    (column, -(m._deposit[k] - m._borrowing[k]) * value)
                    for column, value in negative_part(
                        cash[parent],
                        -m._credit[parent],
                        cash_high[parent],
                        f"cash_debt_{parent}",
                    )
                )
        turnover_terms, sale_terms, fixed_terms = [], [], []
        for i in range(assets):
            terms = [(holdings[k, i], 1)]
            impact_size = []
            opening = m._opening[i] if parent < 0 else 0.0
            if parent >= 0:
                terms.append((holdings[parent, i], -m._splits[k, i]))
                cash_terms.append((holdings[parent, i], -m._dividends[k, i]))
                if m._short_fees[k, i] > 0:
                    low = max(qlow[parent, i], -m._borrow[parent, i])
                    high = qhigh[parent, i]
                    if m._position_limits is not None:
                        low = max(low, m._position_limits[0][parent, i])
                        high = min(high, m._position_limits[1][parent, i])
                    cash_terms.extend(
                        (column, m._short_fees[k, i] * value)
                        for column, value in negative_part(
                            holdings[parent, i],
                            low,
                            high,
                            f"short_quantity_{parent}_{i}",
                        )
                    )
            active = []
            friction = (
                m._ask[k, i] != m._bid[k, i]
                or m._buy_fees[k, i] > 0
                or m._sell_fees[k, i] > 0
                or m._fixed[k, i] > 0
                or m._minimum[k, i] > 0
                or m._impact_quadratic[k, i] > 0
                or m._impact_power[k, i] > 0
                or (k, i) in m._impact_curves
            )
            for side, cap, sign, price, fee in (
                ("buy", buys[k, i], 1, m._ask[k, i], m._buy_fees[k, i]),
                ("sell", sells[k, i], -1, m._bid[k, i], m._sell_fees[k, i]),
            ):
                if cap <= 0:
                    continue
                scale = scales[k, i]
                lots = m._lots[k, i] > 0
                maximum = lot_capacity(cap, scale) if lots else cap
                quantity = variable(
                    f"{side}_{k}_{i}", high=maximum, integer=lots
                )
                terms.append((quantity, -sign * scale))
                impact_size.append((quantity, scale))
                cash_terms.append((quantity, (sign * price + fee) * scale))
                turnover_terms.append((quantity, m._prices[k, i] * scale))
                if side == "sell":
                    sale_terms.append((quantity, -price * scale))
                if friction and (
                    (buys[k, i] > 0 and sells[k, i] > 0)
                    or m._fixed[k, i] > 0
                    or m._minimum[k, i] > 0
                ):
                    ticket = variable(
                        f"{side}_active_{k}_{i}", high=1, integer=True
                    )
                    active.append(ticket)
                    constraint(
                        [(quantity, scale), (ticket, -cap)],
                        -np.inf,
                        0,
                        f"{side}_capacity_{k}_{i}",
                    )
                    minimum = max(m._minimum[k, i], m._lots[k, i])
                    constraint(
                        [(quantity, scale), (ticket, -minimum)],
                        0,
                        np.inf,
                        f"{side}_minimum_{k}_{i}",
                    )
                    fixed_terms.append((ticket, m._fixed[k, i]))
            if len(active) > 1:
                constraint(
                    [(v, 1) for v in active], -np.inf, 1, f"direction_{k}_{i}"
                )
            maximum = max(buys[k, i], sells[k, i])
            if maximum > 0:
                impact = add_cost_graph(
                    m, k, i, impact_size, variable, constraint
                )
                if impact is not None:
                    cash_terms.append((impact, 1))
                if m._impact_quadratic[k, i] > 0 or m._impact_power[k, i] > 0:
                    high = 0.0
                    if m._impact_quadratic[k, i] > 0:
                        high += (m._impact_quadratic[k, i] * maximum) * maximum
                    if m._impact_power[k, i] > 0:
                        high += (m._impact_power[k, i] * maximum) * np.sqrt(
                            maximum
                        )
                    cost = variable(f"nonlinear_impact_{k}_{i}", high=high)
                    cash_terms.append((cost, 1))
            constraint(terms, opening, opening, f"quantity_balance_{k}_{i}")
            low, high = -m._borrow[k, i], np.inf
            if m._position_limits is not None:
                low = max(low, m._position_limits[0][k, i])
                high = m._position_limits[1][k, i]
            constraint([(holdings[k, i], 1)], low, high, f"positions_{k}_{i}")
        balance += Fraction(m._flows[k])
        constraint(
            cash_terms + fixed_terms, balance, balance, f"cash_balance_{k}"
        )
        if m._settlement == "prefunded":
            constraint(
                [(cash[k], 1)] + sale_terms,
                -m._credit[k],
                np.inf,
                f"prefunding_{k}",
            )
        if m._cash_limits is not None:
            constraint(
                [(cash[k], 1)],
                m._cash_limits[0][k],
                m._cash_limits[1][k],
                f"cash_limits_{k}",
            )
        if m._turnover is not None:
            constraint(
                turnover_terms, -np.inf, m._turnover[k], f"turnover_{k}"
            )
        if m._gross is not None:
            gross = []
            for i in range(assets):
                absolute = variable(f"absolute_holding_{k}_{i}")
                constraint(
                    [(absolute, 1), (holdings[k, i], -1)],
                    0,
                    np.inf,
                    f"gross_long_{k}_{i}",
                )
                constraint(
                    [(absolute, 1), (holdings[k, i], 1)],
                    0,
                    np.inf,
                    f"gross_short_{k}_{i}",
                )
                gross.append((absolute, m._prices[k, i]))
            constraint(gross, -np.inf, m._gross[k], f"gross_{k}")
        for block, (ids, exposures, low, high, _) in enumerate(m._exposures):
            exposures = sparse.csr_matrix(exposures)
            for j in range(len(ids)):
                row = exposures.getrow(j)
                constraint(
                    [
                        (holdings[k, i], v)
                        for i, v in zip(row.indices, row.data)
                    ],
                    low[k, j],
                    high[k, j],
                    f"exposure_{block}_{k}_{j}",
                )

    terminal = [
        [(cash[k], 1)]
        + [(holdings[k, i], m._prices[k, i]) for i in range(assets)]
        for k in m._tree._paths[:, -1]
    ]
    probabilities = m._tree._probabilities
    if m._terminal_minimum is not None:
        for s, terms in enumerate(terminal):
            constraint(
                terms, m._terminal_minimum[s], np.inf, f"terminal_floor_{s}"
            )

    def tail(target, level, name):
        coefficients, inequalities = _shortfall_form(probabilities, level)
        eta = variable(f"{name}_var", low=-np.inf)
        auxiliaries = [eta] + [
            variable(f"{name}_excess_{s}") for s in range(len(terminal))
        ]
        for s, terms in enumerate(terminal):
            row = inequalities.getrow(s)
            constraint(
                [
                    (auxiliaries[j], value)
                    for j, value in zip(row.indices, row.data)
                ]
                + terms,
                target[s],
                np.inf,
                f"{name}_loss_{s}",
            )
        return list(zip(auxiliaries, coefficients))

    sense = "max"
    if m._objective == "expected_wealth":
        for s, terms in enumerate(terminal):
            for column, value in terms:
                objective[column] += probabilities[s] * value
    elif m._objective == "worst_case_wealth":
        worst = variable("worst_case_wealth", low=-np.inf)
        objective[worst] = 1.0
        for s, terms in enumerate(terminal):
            constraint(terms + [(worst, -1)], 0, np.inf, f"worst_case_{s}")
    else:
        sense = "min"
        for column, value in tail(m._target, m._confidence, "objective_tail"):
            objective[column] += value
    if m._tail_limit is not None:
        cap, target, level = m._tail_limit
        constraint(
            tail(target, level, "hard_tail"),
            -np.inf,
            cap,
            "hard_expected_shortfall",
        )

    values = sparse.coo_matrix(
        (coefficients, (rows, columns)), shape=(len(labels), len(names))
    ).tocsr()
    if not np.isfinite(values.data).all() or not np.isfinite(objective).all():
        raise ValueError("planning coefficients exceed float64 range")
    return {
        "name": "multi_period_investment",
        "format": "matrix",
        "problem_type": "MILP" if any(integers) else "LP",
        "sense": sense,
        "variable_names": names,
        "objective": np.asarray(objective),
        "objective_offset": 0.0,
        "constraint_matrix": values,
        "row_lower": np.asarray(row_low),
        "row_upper": np.asarray(row_high),
        "constraint_names": labels,
        "lower_bounds": np.asarray(lows),
        "upper_bounds": np.asarray(highs),
        "integrality": np.asarray(integers),
    }
