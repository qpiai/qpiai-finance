"""Source pledge valuation, coverage and chronological inventory accounting."""

from collections.abc import Mapping
from fractions import Fraction

import numpy as np
import pandas as pd

from .._arithmetic import bound_violation
from .._result_checks import record_reconciliation
from .._validation import (
    copy_frame,
    copy_index,
    lot_quantities,
    lot_residual,
    scalar,
    vector,
)
from ._valuation import _pledge_values


def evaluate(collateral, assignments, *, tolerance):
    tolerance = scalar(tolerance, "tolerance", minimum=0)
    if len(collateral._ids):
        quantities = vector(assignments, collateral._ids, "assignments")
    else:
        if (
            not isinstance(
                assignments, (Mapping, pd.Series, list, tuple, np.ndarray)
            )
            or len(assignments) != 0
        ):
            raise ValueError("no permitted pledges: assignments must be empty")
        quantities = np.zeros(0)
    inventory, pledges = collateral._inventory, collateral._pledges
    requirements = collateral._requirements
    assets, dates = collateral._assets, collateral._dates
    shape = (len(dates), len(assets))
    available = (
        np.broadcast_to(collateral._free_inventory(), shape)
        if collateral._available is None
        else np.fromiter(
            map(Fraction, collateral._available.flat), dtype=object
        ).reshape(shape)
    )
    original_quantities = np.fromiter(map(Fraction, quantities), dtype=object)
    committed, outbound, delivered, waiting, outgoing, incoming = [
        np.zeros(shape, dtype=object) for _ in range(6)
    ]
    coverage = np.zeros(len(requirements), dtype=object)
    costs = np.zeros(len(pledges), dtype=object)
    coverage_components = []
    covered_routes = [[] for _ in range(len(requirements))]
    requirement_positions = {}
    for k, row in enumerate(requirements.itertuples()):
        requirement_positions.setdefault(row.obligation, []).append(k)
    requirement_positions = {
        key: np.asarray(rows) for key, rows in requirement_positions.items()
    }
    requirement_dates = requirements.date.tolist()
    requirement_currencies = requirements.currency.tolist()
    requirement_date_positions = dates.get_indexer(requirements.date)
    checks = []

    def check(name, value, low, high, unit):
        reported = float(value)
        if not np.isfinite(reported):
            raise ValueError(
                "collateral quantities or values exceed float64 range"
            )
        violation = bound_violation(value, low, high)
        checks.append(
            (
                name,
                reported,
                float(low),
                float(high),
                float(violation),
                violation <= tolerance,
                unit,
            )
        )

    for j, (_, pledge) in enumerate(pledges.iterrows()):
        quantity = original_quantities[j]
        a = assets.get_loc(pledge.asset)
        start, arrival, release, end = [
            dates.get_loc(value)
            for value in (
                pledge.pledge_date,
                pledge.delivery_date,
                pledge.release_date,
                pledge.return_date,
            )
        ]
        committed[start:end, a] += quantity
        outbound[start:arrival, a] += quantity
        delivered[arrival:release, a] += quantity
        waiting[release:end, a] += quantity
        outgoing[start, a] += quantity
        incoming[end, a] += quantity
        costs[j] = quantity * Fraction(pledge.unit_cost)
        candidates = requirement_positions[pledge.obligation]
        candidate_dates = requirement_date_positions[candidates]
        covered = candidates[
            (candidate_dates >= arrival) & (candidate_dates < release)
        ]
        positions = requirement_date_positions[covered]
        prices, haircuts, fx_rates, adjusted = _pledge_values(
            collateral, pledge, j, a, positions, original=True
        )
        values = adjusted * quantity
        coverage[covered] += values
        for position, k in enumerate(covered):
            covered_routes[k].append((a, values[position]))
            coverage_components.append(
                (
                    requirements.index[k],
                    collateral._ids[j],
                    requirement_dates[k],
                    pledge.asset,
                    prices[position],
                    haircuts[position],
                    fx_rates[position],
                    float(quantity),
                    float(adjusted[position]),
                    float(values[position]),
                    requirement_currencies[k],
                )
            )
        check(
            f"assignment[{j}:{collateral._ids[j]}]",
            quantity,
            collateral._lower[j],
            collateral._upper[j],
            "asset_units",
        )
        if collateral._lots is not None:
            check(
                f"pledge_lots[{j}]",
                lot_residual(quantity, collateral._lots[a]),
                0,
                0,
                "lots",
            )
    coverage_table = copy_frame(requirements)
    coverage_table = coverage_table.rename(columns={"amount": "required"})
    coverage_table["adjusted_value"] = np.asarray(coverage, dtype=float)
    coverage_table["surplus"] = np.asarray(
        [
            value - Fraction(required)
            for value, required in zip(coverage, requirements.amount)
        ],
        dtype=float,
    )
    coverage_table["maximum"] = collateral._coverage_upper
    for k, (identifier, requirement) in enumerate(requirements.iterrows()):
        check(
            f"coverage[{k}:{identifier}]",
            coverage[k],
            requirement.amount,
            collateral._coverage_upper[k],
            requirement.currency,
        )
    for t in range(len(dates)):
        for a, asset in enumerate(assets):
            check(
                f"inventory[{t}:{a}:{asset}]",
                committed[t, a],
                0,
                available[t, a],
                "asset_units",
            )
            for name, movements, limits in (
                ("pledged", outgoing, collateral._pledge_limits),
                ("returned", incoming, collateral._return_limits),
            ):
                if np.isfinite(limits[t, a]):
                    check(
                        f"{name}[{t}:{a}:{asset}]",
                        movements[t, a],
                        0,
                        limits[t, a],
                        "asset_units",
                    )
    index = pd.MultiIndex.from_product(
        [dates, assets], names=["date", "asset"]
    )
    inventory_table = pd.DataFrame(
        {
            "available_before_plan": np.asarray(
                available, dtype=float
            ).ravel(),
            "externally_encumbered": np.tile(
                inventory.encumbered.to_numpy(), len(dates)
            ),
            "committed": np.asarray(committed, dtype=float).ravel(),
            "outbound": np.asarray(outbound, dtype=float).ravel(),
            "delivered": np.asarray(delivered, dtype=float).ravel(),
            "awaiting_return": np.asarray(waiting, dtype=float).ravel(),
            "unallocated": np.asarray(
                available - committed, dtype=float
            ).ravel(),
            "pledged": np.asarray(outgoing, dtype=float).ravel(),
            "returned": np.asarray(incoming, dtype=float).ravel(),
            "unit": "asset_units",
        },
        index=index,
    )
    pledge_table = copy_frame(pledges)
    pledge_table["quantity"] = quantities
    pledge_table["total_cost"] = np.asarray(costs, dtype=float)
    pledge_table["reporting_currency"] = collateral._currency
    tables = {
        "collateral_coverage": coverage_table,
        "collateral_inventory": inventory_table,
        "collateral_assignments": pledge_table,
        "collateral_coverage_components": pd.DataFrame(
            coverage_components,
            columns=[
                "requirement",
                "pledge",
                "date",
                "asset",
                "price",
                "haircut",
                "fx_rate",
                "quantity",
                "adjusted_value_per_unit",
                "adjusted_value",
                "currency",
            ],
        ),
    }
    concentration_rows = []
    for block, (groups, group_ids, shares) in enumerate(
        collateral._concentrations
    ):
        share_by_id = dict(zip(group_ids, shares))
        for k, covered in enumerate(covered_routes):
            actual = {}
            for asset, value in covered:
                group = groups[asset]
                actual[group] = actual.get(group, 0) + value
            for g, (group, value) in enumerate(actual.items()):
                maximum = Fraction(share_by_id[group])
                requirement = requirements.iloc[k]
                check(
                    f"concentration[{block}:{k}:{g}:{group}]",
                    value - maximum * coverage[k],
                    -np.inf,
                    0,
                    requirement.currency,
                )
                concentration_rows.append(
                    (
                        block,
                        requirements.index[k],
                        group,
                        float(value),
                        float(coverage[k]),
                        float(value / coverage[k])
                        if coverage[k] > 0
                        else np.nan,
                        float(maximum),
                        requirement.currency,
                    )
                )
    if concentration_rows:
        tables["collateral_concentrations"] = pd.DataFrame(
            concentration_rows,
            columns=[
                "classification",
                "requirement",
                "group",
                "adjusted_value",
                "total_coverage",
                "share",
                "maximum_share",
                "currency",
            ],
        )
    objective = float(costs.sum())
    if not np.isfinite(
        np.asarray(
            [
                objective,
                *costs,
                *committed.ravel(),
                *outbound.ravel(),
                *delivered.ravel(),
                *waiting.ravel(),
                *coverage,
            ],
            dtype=float,
        )
    ).all():
        raise ValueError(
            "collateral quantities or values exceed float64 range"
        )
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
    return {
        "objective": objective,
        "feasible": bool(constraints.satisfied.all()),
        "constraints": constraints,
        "decision": {
            "assignments": pd.Series(
                quantities, index=copy_index(collateral._ids), name="quantity"
            )
        },
        "metrics": {
            "total_cost": objective,
            "active_pledges": int(np.count_nonzero(quantities > 0)),
        },
        "tables": tables,
        "costs": {
            "collateral_cost": objective,
            "currency": collateral._currency,
        },
    }


def evaluate_solution(collateral, solution, *, tolerance):
    raw = np.array(
        [
            scalar(solution[f"assignment_{j}"], "solver assignment")
            for j in range(len(collateral._ids))
        ]
    )
    quantities = raw
    if collateral._lots is not None:
        scales = collateral._lots[
            collateral._assets.get_indexer(collateral._pledges.asset)
        ]
        quantities = lot_quantities(np.rint(raw), scales)
    evaluation = collateral.evaluate(quantities, tolerance=tolerance)
    diagnostics = []
    if collateral._lots is not None and len(raw):
        diagnostics.append(
            (
                "integer_reconstruction",
                float(np.max(np.abs(raw - np.rint(raw)))),
                "lots",
            )
        )
        evaluation["transformations"] = [
            {
                "type": "collateral_lot_reconstruction",
                "constraints_rechecked": True,
            }
        ]
    reconciliation = []
    for k, coverage in enumerate(
        evaluation["tables"]["collateral_coverage"].adjusted_value
    ):
        reconciliation.append(
            (
                f"coverage_reconciliation[{k}]",
                abs(
                    scalar(solution[f"coverage_{k}"], "solver coverage")
                    - coverage
                ),
                collateral._requirements.currency.iloc[k],
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
