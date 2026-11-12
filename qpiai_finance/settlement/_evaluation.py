"""Independent payment replay, queue costs and native account ledgers."""

from collections.abc import Mapping
from fractions import Fraction

import numpy as np
import pandas as pd

from .._arithmetic import bound_violation, product_sum
from .._result_checks import record_reconciliation
from .._validation import (
    copy_frame,
    copy_index,
    identifiers,
    same_labels,
    scalar,
    vector,
)
from .._validation import seconds as _seconds


def _schedule_events(settlement, schedule):
    if isinstance(schedule, Mapping):
        schedule = pd.Series(schedule, dtype=object)
    if isinstance(schedule, pd.Series) and len(settlement._ids):
        same_labels(schedule.index, settlement._ids, "schedule payments")
        schedule = schedule.reindex(settlement._ids).to_numpy(dtype=object)
    values = np.asarray(schedule, dtype=object)
    if values.ndim != 1 or len(values) != len(settlement._ids):
        raise ValueError(
            "schedule must contain a slot ID or None for every payment"
        )
    scheduled = []
    for payment, value in enumerate(values):
        if value is None or value is pd.NA or value is pd.NaT:
            continue
        if isinstance(value, (float, np.floating)) and np.isnan(value):
            continue
        scheduled.append((payment, value))
    if scheduled:
        identifiers(
            [value for _, value in scheduled],
            "schedule slot IDs",
            unique=False,
        )
    assigned = {}
    for payment, value in scheduled:
        if value not in settlement._slots:
            raise ValueError(
                "schedule values must be supplied slot IDs or None"
            )
        assigned.setdefault(settlement._slots.get_loc(value), []).append(
            payment
        )
    units = settlement._units()
    batches = {
        frozenset(members): u
        for u, (kind, _, members) in enumerate(units)
        if kind == "atomic_batch"
    }
    events = []
    for slot, members in assigned.items():
        batch = batches.get(frozenset(members))
        if len(members) > 1 and batch is not None:
            events.append((batch, slot))
        else:
            events.extend((payment, slot) for payment in members)
    return events


def evaluate(settlement, schedule, *, prefunding, tolerance):
    return _replay(
        settlement,
        _schedule_events(settlement, schedule),
        prefunding,
        tolerance=tolerance,
    )


def _replay(settlement, events, prefunding, *, tolerance):
    tolerance = scalar(tolerance, "tolerance", minimum=0)
    funding = vector(
        prefunding, settlement._account_ids, "prefunding", broadcast=True
    )
    payments, accounts = settlement._payments, settlement._accounts
    units = settlement._units()
    balances = np.fromiter(map(Fraction, accounts.cash), dtype=object)
    peak = np.maximum(-balances, 0)
    closing = np.zeros(settlement._flows.shape, dtype=object)
    by_slot = [[] for _ in settlement._slots]
    for unit, slot in events:
        by_slot[slot].append(unit)
    occurrences = [[] for _ in settlement._ids]
    checks, ledger, event_rows = [], [], []
    checkpoint = 0

    def check(name, value, low, high, unit):
        reported = float(value)
        if not np.isfinite(reported):
            raise ValueError(
                "settlement quantities or costs exceed float64 range"
            )
        violation = bound_violation(value, low, high)
        exact = unit in {"boolean", "payments", "execution_units"}
        satisfied = violation == 0 if exact else violation <= tolerance
        checks.append(
            (name, reported, low, high, float(violation), satisfied, unit)
        )

    def record(kind, time, slot, limits, movements):
        nonlocal checkpoint, peak
        for a, account in enumerate(settlement._account_ids):
            check(
                f"balance[{checkpoint}:{a}:{account}]",
                balances[a],
                -limits[a],
                np.inf,
                accounts.currency.iloc[a],
            )
            ledger.append(
                (
                    checkpoint,
                    account,
                    kind,
                    slot,
                    time,
                    float(movements[a]),
                    float(balances[a]),
                    limits[a],
                    float(max(-balances[a], 0)),
                    accounts.currency.iloc[a],
                )
            )
        peak = np.maximum(peak, np.maximum(-balances, 0))
        checkpoint += 1

    record(
        "opening",
        settlement._as_of,
        None,
        accounts.credit_limit.to_numpy(),
        np.zeros(len(accounts)),
    )
    for a, account in enumerate(settlement._account_ids):
        check(
            f"prefunding[{a}:{account}]",
            funding[a],
            0,
            settlement._prefunding_limit[a],
            accounts.currency.iloc[a],
        )
    balances += np.fromiter(map(Fraction, funding), dtype=object)
    record(
        "prefunding",
        settlement._as_of,
        None,
        accounts.credit_limit.to_numpy(),
        funding,
    )
    for k, slot in enumerate(settlement._slots):
        time = settlement._times[k]
        limits = settlement._credit_limits[k]
        flows = settlement._flows[k]
        balances += np.fromiter(map(Fraction, flows), dtype=object)
        record("pre_slot", time, slot, limits, flows)
        check(
            f"slot_capacity[{k}:{slot}]",
            len(by_slot[k]),
            0,
            1,
            "execution_units",
        )
        for u in by_slot[k]:
            kind, identifier, members = units[u]
            movement = np.zeros(len(accounts), dtype=object)
            for payment in members:
                row = payments.iloc[payment]
                occurrences[payment].append(k)
                check(
                    f"eligible[{len(event_rows)}:{payment}]",
                    int(row.eligible),
                    1,
                    1,
                    "boolean",
                )
                outside_window = int(not (row.release <= time <= row.deadline))
                check(
                    f"window[{len(event_rows)}:{payment}]",
                    outside_window,
                    0,
                    0,
                    "boolean",
                )
            for a, change in settlement._movement(members).items():
                movement[a] = change
            balances += movement
            record("post_settlement", time, slot, limits, movement)
            event_rows.append(
                (
                    slot,
                    time,
                    kind,
                    identifier,
                    tuple(settlement._ids[p] for p in members),
                )
            )
        closing[k] = balances
    schedule_values, payment_rows = [], []
    delay_cost = queue_cost = 0
    for p, (identifier, row) in enumerate(payments.iterrows()):
        selected = occurrences[p]
        count = len(selected)
        check(
            f"payment_once[{p}:{identifier}]",
            count,
            int(row.required),
            1,
            "payments",
        )
        if selected:
            first = min(selected)
            settled_at = settlement._times[first]
            wait = sum(
                max(
                    _seconds(
                        settlement._times[k] - row.release, original=True
                    ),
                    0,
                )
                for k in selected
            )
            penalty = 0
            status = "settled" if count == 1 else "duplicate_execution"
            slot = settlement._slots[first]
        else:
            settled_at, slot = pd.NaT, None
            wait = max(
                _seconds(settlement._times[-1] - row.release, original=True), 0
            )
            penalty = (
                Fraction(row.unsettled_cost)
                if row.release <= settlement._times[-1]
                else 0
            )
            status = (
                "ineligible"
                if not row.eligible
                else "not_released"
                if row.release > settlement._times[-1]
                else "cutoff_expired"
                if row.deadline <= settlement._times[-1]
                else "queued"
            )
        delay = wait * Fraction(row.delay_cost)
        delay_cost += delay
        queue_cost += penalty
        schedule_values.append(slot)
        payment_rows.append(
            (
                identifier,
                row.sender,
                row.receiver,
                row.amount,
                row.currency,
                row.release,
                row.deadline,
                row.required,
                count,
                slot,
                settled_at,
                status,
                float(wait),
                float(delay),
                float(penalty),
            )
        )
    for i, (before, after, same_batch) in enumerate(settlement._precedences):
        before = settlement._ids.get_loc(before)
        after = settlement._ids.get_loc(after)
        for slot in occurrences[after]:
            valid = any(
                prior <= slot if same_batch else prior < slot
                for prior in occurrences[before]
            )
            check(f"precedence[{i}:{slot}]", int(valid), 1, 1, "boolean")
    if settlement._final_lower is not None:
        for a, account in enumerate(settlement._account_ids):
            check(
                f"final_balance[{a}:{account}]",
                balances[a],
                settlement._final_lower[a],
                np.inf,
                accounts.currency.iloc[a],
            )
    funding_cost = product_sum((settlement._prefunding_cost, funding))
    credit_cost = product_sum((settlement._credit_cost, peak))
    objective = float(delay_cost + queue_cost + funding_cost + credit_cost)
    delay_cost, queue_cost, funding_cost, credit_cost = map(
        float, (delay_cost, queue_cost, funding_cost, credit_cost)
    )
    balances = np.asarray(balances, dtype=float)
    peak = np.asarray(peak, dtype=float)
    if not np.isfinite(
        [
            objective,
            delay_cost,
            queue_cost,
            funding_cost,
            credit_cost,
            *balances,
            *peak,
        ]
    ).all():
        raise ValueError("settlement quantities or costs exceed float64 range")
    payment_table = pd.DataFrame(
        payment_rows,
        columns=[
            "payment",
            "sender",
            "receiver",
            "amount",
            "currency",
            "release",
            "deadline",
            "required",
            "execution_count",
            "slot",
            "settled_at",
            "status",
            "delay_seconds",
            "delay_cost",
            "unsettled_cost",
        ],
    ).set_index("payment")
    payment_table["cost_currency"] = settlement._currency
    account_table = copy_frame(accounts)
    account_table["prefunding"] = funding
    account_table["final_cash"] = balances
    account_table["peak_credit_used"] = peak
    ledger_table = pd.DataFrame(
        ledger,
        columns=[
            "checkpoint",
            "account",
            "phase",
            "slot",
            "time",
            "movement",
            "balance",
            "credit_limit",
            "credit_used",
            "currency",
        ],
    ).set_index(["checkpoint", "account"])
    cash_index = pd.MultiIndex.from_product(
        [settlement._slots, settlement._account_ids], names=["slot", "account"]
    )
    return {
        "objective": objective,
        "feasible": bool(all(row[5] for row in checks)),
        "constraints": pd.DataFrame(
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
        ).set_index("constraint"),
        "decision": {
            "schedule": pd.Series(
                schedule_values,
                index=copy_index(settlement._ids),
                dtype=object,
                name="slot",
            ),
            "prefunding": pd.Series(
                funding,
                index=copy_index(settlement._account_ids),
                name="prefunding",
            ),
            "peak_credit": pd.Series(
                peak,
                index=copy_index(settlement._account_ids),
                name="peak_credit_used",
            ),
            "cash_balances": pd.Series(
                np.asarray(closing, dtype=float).ravel(),
                index=cash_index,
                name="cash",
            ),
        },
        "metrics": {
            "delay_cost": delay_cost,
            "unsettled_cost": queue_cost,
            "prefunding_cost": funding_cost,
            "credit_cost": credit_cost,
            "total_cost": objective,
            "settled_payments": int(sum(len(x) == 1 for x in occurrences)),
            "unsettled_payments": int(sum(not x for x in occurrences)),
        },
        "tables": {
            "settlement_schedule": payment_table,
            "payment_queue": payment_table.loc[
                payment_table.execution_count == 0
            ].copy(),
            "settlement_accounts": account_table,
            "settlement_ledger": ledger_table,
            "settlement_events": pd.DataFrame(
                event_rows, columns=["slot", "time", "kind", "id", "payments"]
            ),
        },
        "costs": {
            "delay_cost": delay_cost,
            "unsettled_cost": queue_cost,
            "prefunding_cost": funding_cost,
            "credit_cost": credit_cost,
            "currency": settlement._currency,
        },
    }


def evaluate_solution(settlement, solution, *, tolerance):
    events, raw_values = [], []
    units = settlement._units()
    for u, (_, _, members) in enumerate(units):
        for k in settlement._eligible(members):
            value = scalar(solution[f"execution_{u}_{k}"], "solver execution")
            if value < -tolerance or value > 1 + tolerance:
                raise ValueError(
                    "solver execution is outside the binary domain"
                )
            raw_values.append(value)
            if np.rint(value) == 1:
                events.append((u, k))
    prefunding = [
        scalar(solution[f"prefunding_{a}"], "solver prefunding")
        for a in range(len(settlement._account_ids))
    ]
    evaluation = _replay(settlement, events, prefunding, tolerance=tolerance)
    diagnostics = []
    if raw_values:
        raw = np.array(raw_values)
        diagnostics.append(
            (
                "integer_reconstruction",
                float(np.max(np.abs(raw - np.rint(raw)))),
                "binary",
            )
        )
        evaluation["transformations"] = [
            {
                "type": "settlement_execution_reconstruction",
                "constraints_rechecked": True,
            }
        ]
    reconciliation = []
    for k in range(len(settlement._slots)):
        for a, account in enumerate(settlement._account_ids):
            source = evaluation["decision"]["cash_balances"].iloc[
                k * len(settlement._account_ids) + a
            ]
            reconciliation.append(
                (
                    f"cash_reconciliation[{k}:{a}]",
                    abs(
                        scalar(solution[f"balance_{k}_{a}"], "solver cash")
                        - source
                    ),
                    settlement._accounts.currency.iloc[a],
                )
            )
    for a in range(len(settlement._account_ids)):
        actual = evaluation["decision"]["peak_credit"].iloc[a]
        reconciliation.append(
            (
                f"peak_credit_understatement[{a}]",
                max(
                    actual
                    - scalar(
                        solution[f"peak_credit_{a}"], "solver peak credit"
                    ),
                    0,
                ),
                settlement._accounts.currency.iloc[a],
            )
        )
    for payment, count in enumerate(
        evaluation["tables"]["settlement_schedule"].execution_count
    ):
        reconciliation.append(
            (
                f"unsettled_reconciliation[{payment}]",
                abs(
                    scalar(solution[f"unsettled_{payment}"], "solver queue")
                    - int(count == 0)
                ),
                "payments",
            )
        )
    constrained = {
        identifier
        for before, after, _ in settlement._precedences
        for identifier in (before, after)
    }
    completion_times = {}
    for u, slot in events:
        for payment in units[u][2]:
            completion_times.setdefault(payment, []).append(slot)
    completion_times = {
        payment: np.sort(slots) for payment, slots in completion_times.items()
    }
    for payment, identifier in enumerate(settlement._ids):
        if identifier in constrained:
            for k in range(len(settlement._slots)):
                actual = np.searchsorted(
                    completion_times.get(payment, []), k, side="right"
                )
                reconciliation.append(
                    (
                        f"completion_reconciliation[{payment}:{k}]",
                        abs(
                            scalar(
                                solution[f"completion_{payment}_{k}"],
                                "solver completion",
                            )
                            - actual
                        ),
                        "payments",
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
