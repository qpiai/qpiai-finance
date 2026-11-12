"""Contractual draws, branch repayments and outstanding term principal."""

from fractions import Fraction

import numpy as np
import pandas as pd

from .._arithmetic import float_upper_bound
from .._serialization import identifier_label
from .._validation import (
    lot_capacity,
    lot_residual,
    vector,
)
from ..cashflows import _loan_amounts, _loan_cash_terms
from ..treasury._contracts import schedule


def cash_capacity(model):
    """Bound new cash from draws; fees/repayments can only reduce it."""
    maximum = np.zeros(len(model._nodes), dtype=object)
    for source in model._funding.values():
        k = model._tree._position(source["draw_node"])
        maximum[k] += max(1 - Fraction(source["fee"]), 0) * Fraction(
            source["maximum"]
        )
    return maximum


def compile_funding(model, variable, constraint):
    count = len(model._nodes)
    events, debt = ([[] for _ in range(count)] for _ in range(2))
    constants, existing = np.zeros(count, dtype=object), np.zeros(
        count, dtype=object
    )
    principals = {}

    def equation(terms, name):
        constraint(terms, 0, 0, name)
    for source in model._existing_debt.values():
        live, due = schedule(
            model._tree, model._tree.root, source["repayment_stage"]
        )
        existing[live] += Fraction(source["principal"])
        _, repayment, _, _ = _loan_amounts(
            source["principal"], source["interest"], original=True
        )
        constants[due] -= repayment
    for i, (key, source) in enumerate(model._funding.items()):
        lot = source["lot_size"]
        scale = lot or 1.0
        maximum = (
            lot_capacity(source["maximum"], lot)
            if lot is not None
            else source["maximum"]
        )
        draw = variable(
            f"funding_{i}",
            high=maximum,
            integer=lot is not None,
        )
        if model._facilities:
            principals[key] = (draw, scale)
        start = model._tree._position(source["draw_node"])
        active = None
        if source["minimum"] > 0 or source["fixed_fee"] > 0:
            active = variable(f"funding_active_{i}", high=1, integer=True)
            constraint(
                [(draw, scale), (active, -source["maximum"])],
                -np.inf,
                0,
                f"funding_capacity_{i}",
            )
            constraint(
                [(draw, scale), (active, -max(source["minimum"], lot or 0))],
                0,
                np.inf,
                f"funding_minimum_{i}",
            )
        proceeds, repayment, _, _ = _loan_cash_terms(
            draw, scale, source["interest"], source["fee"],
            maximum=Fraction(maximum) * Fraction(scale),
            fixed_fee=source["fixed_fee"], active=active, name=f"funding_{i}",
            variable=variable, equation=equation,
        )
        events[start].extend(proceeds)
        live, due = schedule(
            model._tree, source["draw_node"], source["repayment_stage"]
        )
        for k in live:
            debt[k].append((draw, scale))
        for k in due:
            events[k].extend((column, -rate) for column, rate in repayment)
    if model._facilities:
        from ..treasury._facilities import capacity_rows

        fixed = {
            key: source["principal"]
            for key, source in model._existing_debt.items()
        }
        for block, k, terms, upper in capacity_rows(
            model._facilities, model._facility_active(), fixed
        ):
            coefficients = [
                (principals[key][0], rate * principals[key][1])
                for key, rate in terms
                if key in principals
            ]
            constraint(
                coefficients,
                -np.inf,
                upper,
                f"facility_{block}_{k}",
            )
    if model._debt_limits is not None:
        for k in range(count):
            constraint(
                debt[k],
                -np.inf,
                np.inf if np.isposinf(model._debt_limits[k]) else
                float_upper_bound(
                    Fraction(model._debt_limits[k]) - existing[k]
                ),
                f"term_debt_limit_{k}",
            )
    if not np.isfinite(np.asarray(existing, float)).all():
        raise ValueError("funding coefficients exceed float64 range")
    return events, constants


def evaluate_funding(model, draws, check):
    ids = pd.Index(list(model._funding))
    if not len(ids) and draws is None:
        values = np.empty(0)
    else:
        if draws is None:
            raise ValueError("provide a complete draws decision")
        values = vector(draws, ids, "draws")
    movements = {
        name: np.zeros(len(model._nodes), dtype=object)
        for name in (
            "funding_draws",
            "principal_repayments",
            "funding_interest",
            "funding_fees",
            "outstanding_debt",
            "net_funding_cash_flow",
        )
    }
    records = []

    def record(key, k, event, principal, interest, fees, cash_flow):
        records.append(
            {
                "funding_id": key,
                "node": model._nodes[k],
                "stage": model._tree._stages[model._tree._depths[k]],
                "time": model._tree._times[model._tree._depths[k]],
                "event": event,
                "principal": float(principal),
                "interest": float(interest),
                "fees": float(fees),
                "cash_flow": float(cash_flow),
            }
        )

    for key, source in model._existing_debt.items():
        live, due = schedule(
            model._tree, model._tree.root, source["repayment_stage"]
        )
        amount = Fraction(source["principal"])
        _, repayment, _, interest = _loan_amounts(
            amount, source["interest"], original=True
        )
        movements["net_funding_cash_flow"][due] -= repayment
        movements["outstanding_debt"][live] += amount
        movements["principal_repayments"][due] += amount
        movements["funding_interest"][due] += interest
        for k in due:
            record(
                key,
                k,
                "existing_debt_repayment",
                amount,
                interest,
                0.0,
                -repayment,
            )
    for i, (key, source) in enumerate(model._funding.items()):
        amount = Fraction(values[i])
        label = identifier_label(key)
        check(f"draw[{label}]", amount, 0, source["maximum"], model.currency)
        if amount != 0:
            check(
                f"minimum_draw[{label}]",
                amount,
                source["minimum"],
                np.inf,
                model.currency,
            )
        if source["lot_size"] is not None:
            check(
                f"funding_lots[{label}]",
                lot_residual(amount, source["lot_size"]),
                0,
                0,
                "lots",
            )
        start = model._tree._position(source["draw_node"])
        live, due = schedule(
            model._tree, source["draw_node"], source["repayment_stage"]
        )
        proceeds, repayment, fees, interest = _loan_amounts(
            amount,
            source["interest"],
            source["fee"],
            source["fixed_fee"],
            original=True,
        )
        movements["net_funding_cash_flow"][start] += proceeds
        movements["net_funding_cash_flow"][due] -= repayment
        movements["funding_draws"][start] += amount
        movements["funding_fees"][start] += fees
        movements["outstanding_debt"][live] += amount
        movements["principal_repayments"][due] += amount
        movements["funding_interest"][due] += interest
        record(key, start, "draw", amount, 0.0, fees, proceeds)
        for k in due:
            record(key, k, "repayment", amount, interest, 0.0, -repayment)
    for k, amount in enumerate(movements["outstanding_debt"]):
        if model._debt_limits is not None:
            check(
                f"term_debt[{k}]",
                amount,
                0,
                model._debt_limits[k],
                model.currency,
            )
    facility_tables = {}
    if model._facilities:
        from ..treasury._facilities import evaluate as evaluate_facilities

        principals = dict(zip(model._funding, values))
        principals.update(
            {
                key: source["principal"]
                for key, source in model._existing_debt.items()
            }
        )
        facility_tables = evaluate_facilities(
            model._facilities,
            model._facility_active(),
            principals,
            model._nodes,
            "node",
            check,
        )
    table = pd.DataFrame(
        records,
        columns=[
            "funding_id",
            "node",
            "stage",
            "time",
            "event",
            "principal",
            "interest",
            "fees",
            "cash_flow",
        ],
    ).set_index(["funding_id", "node", "event"])
    table.attrs["currency"] = model.currency
    return (
        movements,
        pd.Series(values, index=ids, name="principal"),
        table,
        facility_tables,
    )
