"""Shared funding commitments in a declared dated capacity currency."""

from fractions import Fraction

import numpy as np
import pandas as pd

from .._arithmetic import float_upper_bound, product_sum
from .._serialization import identifier_label
from .._validation import copy_index, identifiers, numeric, same_labels, vector
from ..cashflows import _currency, _period_index, _period_vector


def prepare(
    facility_id,
    funding_ids,
    *,
    periods,
    contract_currencies,
    maximum,
    currency,
    fx_rates,
    reserved,
):
    identifiers([facility_id], "facility_id")
    members = identifiers(funding_ids, "facility funding_ids")
    if any(key not in contract_currencies for key in members):
        raise ValueError(
            "facility funding_ids must name existing funding or debt"
        )
    currency = _currency(currency)
    native = pd.Index([contract_currencies[key] for key in members])
    currencies = native.drop_duplicates()
    limits = _period_vector(maximum, periods, "maximum facility utilization")
    outside = _period_vector(
        reserved, periods, "reserved facility utilization"
    )
    if np.any(limits < 0) or np.any(outside < 0):
        raise ValueError("facility maximum and reserved must be nonnegative")
    if fx_rates is None:
        if any(code != currency for code in currencies):
            raise ValueError("cross-currency facility limits require fx_rates")
        rates = np.ones((len(periods), len(currencies)))
    elif isinstance(fx_rates, pd.DataFrame):
        frame = fx_rates.copy()
        frame.index = _period_index(
            frame.index, periods, "facility FX periods"
        )
        same_labels(frame.columns, currencies, "facility FX currencies")
        rates = numeric(
            frame.reindex(index=periods, columns=currencies).to_numpy(),
            "facility fx_rates",
            ndim=2,
        )
    elif np.ndim(fx_rates) == 2:
        rates = numeric(fx_rates, "facility fx_rates", ndim=2)
    else:
        static = vector(
            fx_rates,
            currencies,
            "facility fx_rates",
            broadcast=len(currencies) == 1,
        )
        rates = np.broadcast_to(static, (len(periods), len(currencies)))
    if rates.shape != (len(periods), len(currencies)):
        raise ValueError(
            "facility fx_rates must have period rows and currency columns"
        )
    if np.any(rates <= 0):
        raise ValueError("facility FX rates must be positive")
    if currency in currencies and np.any(
        rates[:, currencies.get_loc(currency)] != 1
    ):
        raise ValueError("facility-currency FX rates must equal one")
    return dict(
        funding_ids=members,
        maximum=limits,
        currency=currency,
        fx_rates=rates,
        reserved=outside,
        currencies=copy_index(currencies),
        currency_columns=currencies.get_indexer(native),
    )


def configuration(facilities, periods):
    for key, facility in facilities.items():
        yield (
            key,
            dict(
                funding_ids=copy_index(facility["funding_ids"]),
                maximum=facility["maximum"],
                currency=facility["currency"],
                reserved=facility["reserved"],
                fx_rates=pd.DataFrame(
                    facility["fx_rates"],
                    index=copy_index(periods),
                    columns=copy_index(facility["currencies"]),
                ),
            ),
        )


def rows(facilities, active):
    """Yield actual live contract weights for each hard commitment limit."""
    for block, (key, facility) in enumerate(facilities.items()):
        terms = [[] for _ in facility["maximum"]]
        for member, column in zip(
            facility["funding_ids"], facility["currency_columns"]
        ):
            for k in active[member]:
                terms[k].append(
                    (member, float(facility["fx_rates"][k, column]))
                )
        for k, values in enumerate(terms):
            yield block, key, k, values, facility


def capacity_upper(terms, facility, k, existing):
    fixed = [(key, rate) for key, rate in terms if key in existing]
    used = Fraction(facility["reserved"][k]) + product_sum(
        ([rate for _, rate in fixed], [existing[key] for key, _ in fixed])
    )
    try:
        return float_upper_bound(Fraction(facility["maximum"][k]) - used)
    except OverflowError as error:
        raise ValueError("facility capacity exceeds float64 range") from error


def capacity_rows(facilities, active, existing):
    """Yield principal terms and bounds for nontrivial capacity limits."""
    for block, _, k, terms, facility in rows(facilities, active):
        if not terms and facility["reserved"][k] < facility["maximum"][k]:
            continue
        upper = capacity_upper(terms, facility, k, existing)
        # Keep zero, including an outward-rounded negative zero. Positive
        # spare capacity with no adjustable principal is a tautology.
        if upper <= 0 or any(key not in existing for key, _ in terms):
            yield block, k, terms, upper


def financial_variables(facilities, active, principals, periods, axis, zero):
    amounts, labels = [], []
    for _, key, k, terms, facility in rows(facilities, active):
        amounts.append(
            sum(
                (rate * principals[member] for member, rate in terms),
                zero + float(facility["reserved"][k]),
            )
        )
        labels.append((periods[k], key))
    return pd.Series(
        amounts,
        index=pd.MultiIndex.from_tuples(
            labels,
            names=[axis, "facility"],
        ),
        name="utilization",
        dtype=object,
    )


def evaluate(facilities, active, principals, periods, axis, check):
    summary, components = [], []
    for block, key, k, terms, facility in rows(facilities, active):
        modelled = product_sum(
            (
                [rate for _, rate in terms],
                [principals[member] for member, _ in terms],
            )
        )
        reserved = Fraction(facility["reserved"][k])
        used = modelled + reserved
        maximum = facility["maximum"][k]
        check(
            f"facility[{block}:{k}:{identifier_label(key)}]",
            used,
            0,
            maximum,
            facility["currency"],
        )
        try:
            summary.append(
                (
                    periods[k],
                    key,
                    float(modelled),
                    float(reserved),
                    float(used),
                    maximum,
                    float(Fraction(maximum) - used),
                    facility["currency"],
                )
            )
            for member, rate in terms:
                column = facility["funding_ids"].get_loc(member)
                native = facility["currencies"][
                    facility["currency_columns"][column]
                ]
                principal = principals[member]
                components.append(
                    (
                        periods[k],
                        key,
                        member,
                        float(principal),
                        native,
                        rate,
                        float(Fraction(principal) * Fraction(rate)),
                        facility["currency"],
                    )
                )
        except OverflowError as error:
            raise ValueError(
                "facility utilization exceeds float64 range"
            ) from error
    usage = pd.DataFrame(
        summary,
        columns=[
            axis,
            "facility",
            "modelled_utilization",
            "reserved_utilization",
            "total_utilization",
            "maximum",
            "remaining_capacity",
            "currency",
        ],
    ).set_index([axis, "facility"])
    detail = pd.DataFrame(
        components,
        columns=[
            axis,
            "facility",
            "funding_id",
            "outstanding_principal",
            "principal_currency",
            "fx_rate",
            "utilization",
            "currency",
        ],
    )
    if not np.isfinite(
        usage.select_dtypes(include="number").to_numpy()
    ).all() or (
        not np.isfinite(
            detail.select_dtypes(include="number").to_numpy()
        ).all()
    ):
        raise ValueError("facility utilization exceeds float64 range")
    return {"funding_facilities": usage, "funding_facility_components": detail}
