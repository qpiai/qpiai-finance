"""Sparse payment-window MILP with pre/post-position liquidity constraints."""

from fractions import Fraction

import numpy as np
from scipy import sparse

from .._validation import seconds as _seconds


def matrix_problem(settlement):
    payments, accounts = settlement._payments, settlement._accounts
    units = settlement._units()
    a, t, p = len(accounts), len(settlement._slots), len(payments)
    executions = [
        (u, k)
        for u, (_, _, members) in enumerate(units)
        for k in settlement._eligible(members)
    ]
    e = len(executions)
    by_payment = [[] for _ in range(p)]
    by_slot = [[] for _ in range(t)]
    by_payment_slot = {}
    unit_deltas = [settlement._movement(members) for _, _, members in units]
    movement = {}
    for j, (u, k) in enumerate(executions):
        by_slot[k].append(j)
        for payment in units[u][2]:
            by_payment[payment].append(j)
            by_payment_slot.setdefault((payment, k), []).append(j)
        for account, amount in unit_deltas[u].items():
            movement.setdefault((k, account), []).append((j, -amount))
    prefunding_start, balance_start, peak_start = e, e + a, e + a + t * a
    constrained = {
        identifier
        for before, after, _ in settlement._precedences
        for identifier in (before, after)
    }
    completion_ids = [
        i
        for i, identifier in enumerate(settlement._ids)
        if identifier in constrained
    ]
    unsettled_start = peak_start + a
    completion_start = unsettled_start + p
    completion = {
        (payment, k): completion_start + j * t + k
        for j, payment in enumerate(completion_ids)
        for k in range(t)
    }
    width = completion_start + len(completion)
    rows, columns, values, lower, upper, labels = [], [], [], [], [], []

    def add(entries, low, high, label):
        index = len(labels)
        for column, value in entries:
            if value != 0:
                rows.append(index)
                columns.append(column)
                values.append(float(value))
        lower.append(float(low))
        upper.append(float(high))
        labels.append(label)

    for i, row in enumerate(payments.itertuples()):
        add(
            [(j, 1) for j in by_payment[i]] + [(unsettled_start + i, 1)],
            1,
            1,
            f"payment_once_{i}",
        )
    for k in range(t):
        add([(j, 1) for j in by_slot[k]], 0, 1, f"slot_capacity_{k}")
        for account in range(a):
            current = balance_start + k * a + account
            peak = peak_start + account
            flow = settlement._flows[k, account]
            credit = settlement._credit_limits[k, account]
            if k == 0:
                previous = prefunding_start + account
                rhs = Fraction(accounts.cash.iloc[account]) + Fraction(flow)
            else:
                previous = balance_start + (k - 1) * a + account
                rhs = Fraction(flow)
            add(
                [(current, 1), (previous, -1)]
                + movement.get((k, account), []),
                rhs,
                rhs,
                f"cash_balance_{k}_{account}",
            )
            # Previous balance plus this slot's external flows must already
            # respect limits before any outgoing/incoming settlement unit.
            add(
                [(previous, 1)],
                -Fraction(credit) - rhs,
                np.inf,
                f"pre_slot_liquidity_{k}_{account}",
            )
            add(
                [(peak, 1), (previous, 1)],
                -rhs,
                np.inf,
                f"pre_slot_peak_{k}_{account}",
            )
            add(
                [(peak, 1), (current, 1)],
                0,
                np.inf,
                f"post_slot_peak_{k}_{account}",
            )
    for payment in completion_ids:
        for k in range(t):
            entries = [(completion[payment, k], 1)]
            if k:
                entries.append((completion[payment, k - 1], -1))
            entries.extend(
                (j, -1) for j in by_payment_slot.get((payment, k), [])
            )
            add(entries, 0, 0, f"completion_{payment}_{k}")
    for i, (before, after, same_batch) in enumerate(settlement._precedences):
        before = settlement._ids.get_loc(before)
        after = settlement._ids.get_loc(after)
        for k in range(t):
            entries = [(completion[after, k], 1)]
            previous = k if same_batch else k - 1
            if previous >= 0:
                entries.append((completion[before, previous], -1))
            add(entries, -np.inf, 0, f"precedence_{i}_{k}")
    queued = np.array(
        [
            Fraction(row.delay_cost)
            * max(
                _seconds(settlement._times[-1] - row.release, original=True), 0
            )
            + (
                Fraction(row.unsettled_cost)
                if row.release <= settlement._times[-1]
                else 0
            )
            for row in payments.itertuples()
        ],
        dtype=float,
    )
    objective = np.zeros(width, dtype=object)
    for j, (u, k) in enumerate(executions):
        for payment in units[u][2]:
            row = payments.iloc[payment]
            wait = _seconds(settlement._times[k] - row.release, original=True)
            objective[j] += Fraction(row.delay_cost) * wait
    objective[prefunding_start : prefunding_start + a] = (
        settlement._prefunding_cost
    )
    objective[peak_start : peak_start + a] = settlement._credit_cost
    objective[unsettled_start : unsettled_start + p] = queued
    objective = np.asarray(objective, dtype=float)
    cash_lower = -settlement._credit_limits.copy()
    if settlement._final_lower is not None:
        cash_lower[-1] = np.maximum(cash_lower[-1], settlement._final_lower)
    peak_lower = np.maximum(-accounts.cash.to_numpy(), 0)
    peak_upper = np.maximum(
        accounts.credit_limit.to_numpy(), settlement._credit_limits.max(axis=0)
    )
    names = (
        [f"execution_{u}_{k}" for u, k in executions]
        + [f"prefunding_{i}" for i in range(a)]
        + [f"balance_{k}_{i}" for k in range(t) for i in range(a)]
        + [f"peak_credit_{i}" for i in range(a)]
        + [f"unsettled_{i}" for i in range(p)]
        + [
            f"completion_{payment}_{k}"
            for payment in completion_ids
            for k in range(t)
        ]
    )
    result = {
        "name": "settlement",
        "format": "matrix",
        "sense": "min",
        "problem_type": "MILP" if e else "LP",
        "variable_names": names,
        "objective": objective,
        "objective_offset": 0.0,
        "constraint_matrix": sparse.coo_matrix(
            (values, (rows, columns)), shape=(len(labels), width)
        ).tocsr(),
        "row_lower": np.array(lower),
        "row_upper": np.array(upper),
        "constraint_names": labels,
        "lower_bounds": np.r_[
            np.zeros(e + a),
            cash_lower.ravel(),
            peak_lower,
            np.zeros(p),
            np.zeros(len(completion)),
        ],
        "upper_bounds": np.r_[
            np.ones(e),
            settlement._prefunding_limit,
            np.full(t * a, np.inf),
            peak_upper,
            1 - payments.required.to_numpy(dtype=int),
            np.ones(len(completion)),
        ],
        "integrality": np.r_[
            np.ones(e, dtype=int), np.zeros(width - e, dtype=int)
        ],
    }
    if (
        not np.isfinite(result["constraint_matrix"].data).all()
        or not np.isfinite(objective).all()
        or not np.isfinite(result["objective_offset"])
    ):
        raise ValueError("settlement coefficients exceed float64 range")
    return result
