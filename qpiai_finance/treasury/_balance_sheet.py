"""Dated, unit-aware exposures of financed investments and account cash."""

from collections.abc import Mapping
from fractions import Fraction

import numpy as np
import pandas as pd
from scipy import sparse

from .._arithmetic import float_upper_bound, product_sum, row_products
from .._serialization import identifier_label
from .._validation import copy_index, identifiers, matrix, vector
from ..cashflows import _period_index, _period_vector


def _presence(model, kind, member):
    if kind == "cash":
        return range(len(model._periods))
    if kind == "funding":
        if member in model._existing_debt:
            source = model._existing_debt[member]
            return model._schedule(None, source.repay_at)[1]
        source = model._funding[member]
        return model._schedule(source.draw_at, source.repay_at)[1]
    source = model._investments[member]
    if model._tree is None:
        return range(
            model._periods.get_loc(source.purchase_at), len(model._periods)
        )
    _, live, due = model._schedule(source.purchase_at, model._tree._stages[-1])
    return np.concatenate((live, due))


def _coefficients(model, kind, values):
    known = getattr(model, {
        "investments": "investment_ids",
        "funding": "funding_ids",
        "cash": "account_ids",
    }[kind])
    if isinstance(values, Mapping):
        values = pd.Series(values)
    if isinstance(values, pd.DataFrame):
        members = identifiers(values.columns, f"{kind} exposure members")
        frame = values.copy(deep=False)
        frame.index = _period_index(
            values.index, model._periods, f"{kind} exposure periods"
        )
        values = frame.reindex(
            index=model._periods, columns=members
        ).to_numpy()
    elif isinstance(values, pd.Series):
        members = identifiers(values.index, f"{kind} exposure members")
    else:
        members = known
    if not len(members) or not members.isin(known).all():
        raise ValueError(f"{kind} coefficients must name known positions")
    if not sparse.issparse(values) and np.ndim(values) <= 1:
        weights = vector(
            values, members, f"{kind} coefficients", broadcast=True
        )
        values = np.broadcast_to(weights, (len(model._periods), len(members)))
    data = sparse.csc_matrix(
        matrix(values, model._periods, members, f"{kind} coefficients")
    )
    for j, member in enumerate(members):
        start, stop = data.indptr[j : j + 2]
        if start == stop:
            continue
        present = np.zeros(len(model._periods), dtype=bool)
        present[list(_presence(model, kind, member))] = True
        data.data[start:stop] *= present[data.indices[start:stop]]
    data.eliminate_zeros()
    return copy_index(members), data.tocsr()


def prepare(
    model,
    exposure_id,
    *,
    investment_coefficients,
    funding_coefficients,
    cash_coefficients,
    external_exposure,
    lower,
    upper,
    unit,
):
    identifiers([exposure_id], "exposure_id")
    if not isinstance(unit, str) or not unit.strip():
        raise ValueError("unit must be nonempty text")
    if lower is None and upper is None:
        raise ValueError("provide a lower or upper exposure limit")
    periods = model._periods
    low = (
        np.full(len(periods), -np.inf)
        if lower is None
        else _period_vector(lower, periods, "lower exposure")
    )
    high = (
        np.full(len(periods), np.inf)
        if upper is None
        else _period_vector(upper, periods, "upper exposure")
    )
    if np.any(low > high):
        raise ValueError("lower exposure must not exceed upper exposure")
    outside = _period_vector(external_exposure, periods, "external_exposure")
    parts = {}
    for kind, values in (
        ("investments", investment_coefficients),
        ("funding", funding_coefficients),
        ("cash", cash_coefficients),
    ):
        if values is not None:
            parts[kind] = _coefficients(model, kind, values)
    existing = {}
    fixed = np.zeros(len(periods), dtype=object)
    if "funding" in parts:
        members, values = parts["funding"]
        columns = [
            j for j, key in enumerate(members) if key in model._existing_debt
        ]
        existing = {
            members[j]: model._existing_debt[members[j]].principal
            for j in columns
        }
        fixed = np.asarray(
            list(
                row_products(
                    values[:, columns],
                    np.asarray(list(existing.values()), dtype=float),
                )
            ),
            dtype=object,
        )
    return dict(
        unit=unit,
        lower=low,
        upper=high,
        external=outside,
        parts=parts,
        existing=existing,
        fixed_funding=fixed,
    )


def configuration(model):
    known = {
        "investments": model.investment_ids,
        "funding": model.funding_ids,
        "cash": model.account_ids,
    }
    for key, block in model._exposure_limits.items():
        arguments = dict(
            unit=block["unit"],
            external_exposure=block["external"],
            lower=None
            if np.isneginf(block["lower"]).all()
            else block["lower"],
            upper=None
            if np.isposinf(block["upper"]).all()
            else block["upper"],
        )
        for kind, (members, values) in block["parts"].items():
            name = "investment" if kind == "investments" else kind
            coo = values.tocoo(copy=False)
            columns = known[kind].get_indexer(members)
            arguments[f"{name}_coefficients"] = sparse.coo_matrix(
                (coo.data, (coo.row, columns[coo.col])),
                shape=(len(model._periods), len(known[kind])),
            ).tocsr()
        yield key, arguments


def terms(block, k, positions):
    for kind, (members, values) in block["parts"].items():
        start, stop = values.indptr[k : k + 2]
        for j, coefficient in zip(
            values.indices[start:stop], values.data[start:stop]
        ):
            key = members[j]
            if kind == "funding" and key in block["existing"]:
                continue
            value = positions[kind][key]
            yield float(coefficient) * (value[k] if kind == "cash" else value)


def bounds(block, k):
    fixed = Fraction(block["external"][k]) + block["fixed_funding"][k]
    low, high = block["lower"][k], block["upper"][k]
    try:
        return (
            -np.inf
            if np.isneginf(low)
            else -float_upper_bound(fixed - Fraction(low)),
            np.inf
            if np.isposinf(high)
            else float_upper_bound(Fraction(high) - fixed),
        )
    except OverflowError as error:
        raise ValueError("exposure bounds exceed float64 range") from error


def evaluate(exposures, positions, periods, axis, check):
    summary, components = [], []
    for block_id, (key, block) in enumerate(exposures.items()):
        totals = {
            kind: np.zeros(len(periods), dtype=object)
            for kind in ("investments", "funding", "cash")
        }
        for kind, (members, values) in block["parts"].items():
            if kind != "cash":
                quantities = np.asarray(
                    [positions[kind][member] for member in members],
                    dtype=float,
                )
                totals[kind] = list(row_products(values, quantities))
            for k in range(len(periods)):
                start, stop = values.indptr[k : k + 2]
                columns, rates = (
                    values.indices[start:stop],
                    values.data[start:stop],
                )
                quantities = [
                    positions[kind][members[j]][k]
                    if kind == "cash"
                    else positions[kind][members[j]]
                    for j in columns
                ]
                if kind == "cash":
                    totals[kind][k] = product_sum((rates, quantities))
                for j, rate, quantity in zip(columns, rates, quantities):
                    components.append(
                        (
                            periods[k],
                            key,
                            kind,
                            members[j],
                            float(quantity),
                            float(rate),
                            float(Fraction(rate) * Fraction(quantity)),
                            block["unit"],
                        )
                    )
        for k, period in enumerate(periods):
            outside = Fraction(block["external"][k])
            total = outside + sum(totals[kind][k] for kind in totals)
            check(
                f"exposure[{block_id}:{k}:{identifier_label(key)}]",
                total,
                block["lower"][k],
                block["upper"][k],
                block["unit"],
            )
            summary.append(
                (
                    period,
                    key,
                    *(float(totals[kind][k]) for kind in totals),
                    float(outside),
                    float(total),
                    block["lower"][k],
                    block["upper"][k],
                    block["unit"],
                )
            )
    table = pd.DataFrame(
        summary,
        columns=[
            axis,
            "exposure",
            "investment_exposure",
            "funding_exposure",
            "cash_exposure",
            "external_exposure",
            "total_exposure",
            "lower",
            "upper",
            "unit",
        ],
    ).set_index([axis, "exposure"])
    detail = pd.DataFrame(
        components,
        columns=[
            axis,
            "exposure",
            "kind",
            "position",
            "quantity",
            "coefficient",
            "contribution",
            "unit",
        ],
    ).set_index([axis, "exposure", "kind", "position"])
    numeric = [
        "investment_exposure",
        "funding_exposure",
        "cash_exposure",
        "external_exposure",
        "total_exposure",
    ]
    if (
        not np.isfinite(table[numeric].to_numpy(dtype=float)).all()
        or not np.isfinite(
            detail[["quantity", "coefficient", "contribution"]].to_numpy(
                dtype=float
            )
        ).all()
    ):
        raise ValueError("balance-sheet exposures exceed float64 range")
    return {"exposures": table, "exposure_components": detail}
