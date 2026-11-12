"""Sparse dated inventory and adjusted-value coverage constraints."""

import numpy as np
from scipy import sparse

from .._arithmetic import float_upper_bound
from .._validation import lot_capacity
from ._valuation import _pledge_values


def matrix_problem(collateral):
    pledges = collateral._pledges
    requirements = collateral._requirements
    assets, dates = collateral._assets, collateral._dates
    n, m = len(pledges), len(requirements)
    asset_positions = assets.get_indexer(pledges.asset)
    scales = (
        np.ones(n)
        if collateral._lots is None
        else collateral._lots[asset_positions]
    )
    coverage_rows, coverage_cols, coverage_values = [], [], []
    lock_rows, lock_cols, outgoing_rows, incoming_rows = [], [], [], []
    requirement_groups = {
        obligation: rows.index.to_numpy()
        for obligation, rows in requirements.reset_index(drop=True).groupby(
            "obligation", sort=False, observed=True
        )
    }
    requirement_date_positions = dates.get_indexer(requirements.date)
    for j, (_, pledge) in enumerate(pledges.iterrows()):
        asset = asset_positions[j]
        start, arrival, release, stop = dates.get_indexer(
            [
                pledge.pledge_date,
                pledge.delivery_date,
                pledge.release_date,
                pledge.return_date,
            ]
        )
        lock_rows.extend(t * len(assets) + asset for t in range(start, stop))
        lock_cols.extend([j] * (stop - start))
        outgoing_rows.append(start * len(assets) + asset)
        incoming_rows.append(stop * len(assets) + asset)
        rows = requirement_groups[pledge.obligation]
        date_positions = requirement_date_positions[rows]
        rows = rows[(date_positions >= arrival) & (date_positions < release)]
        coverage_rows.extend(rows)
        coverage_cols.extend([j] * len(rows))
        date_positions = requirement_date_positions[rows]
        _, _, _, adjusted = _pledge_values(
            collateral, pledge, j, asset, date_positions
        )
        coverage_values.extend(adjusted)
    coverage = sparse.coo_matrix(
        (coverage_values, (coverage_rows, coverage_cols)), shape=(m, n)
    ).tocsr()
    coverage.eliminate_zeros()
    row_count = len(dates) * len(assets)
    locks = sparse.coo_matrix(
        (np.ones(len(lock_cols)), (lock_rows, lock_cols)), shape=(row_count, n)
    ).tocsr()
    outgoing = sparse.coo_matrix(
        (np.ones(n), (outgoing_rows, np.arange(n))), shape=(row_count, n)
    ).tocsr()
    incoming = sparse.coo_matrix(
        (np.ones(n), (incoming_rows, np.arange(n))), shape=(row_count, n)
    ).tocsr()
    blocks = [
        sparse.hstack(
            [coverage.multiply(scales), -sparse.eye(m)], format="csr"
        ),
        sparse.hstack(
            [locks.multiply(scales), sparse.csr_matrix((row_count, m))],
            format="csr",
        ),
    ]
    lower = [np.zeros(m), np.zeros(row_count)]
    available = collateral._available
    if available is None:
        available = np.broadcast_to(
            np.fromiter(
                map(float_upper_bound, collateral._free_inventory()),
                dtype=float,
            ),
            (len(dates), len(assets)),
        )
    upper = [np.zeros(m), available.ravel()]
    labels = [f"coverage_balance_{k}" for k in range(m)] + [
        f"inventory_{k}" for k in range(row_count)
    ]
    if collateral._mixed_integer:
        assignment_lower = np.zeros(n)
        assignment_upper = np.array(
            [
                lot_capacity(value, scale) if np.isfinite(value) else value
                for value, scale in zip(collateral._upper, scales)
            ]
        )
        minimum = np.flatnonzero(collateral._lower > 0)
        if len(minimum):
            blocks.append(
                sparse.coo_matrix(
                    (scales[minimum], (np.arange(len(minimum)), minimum)),
                    shape=(len(minimum), n + m),
                ).tocsr()
            )
            lower.append(collateral._lower[minimum])
            upper.append(np.full(len(minimum), np.inf))
            labels.extend(f"minimum_assignment_{j}" for j in minimum)
    else:
        assignment_lower = collateral._lower / scales
        assignment_upper = collateral._upper / scales
    for name, movements, limits in (
        ("pledged", outgoing, collateral._pledge_limits),
        ("returned", incoming, collateral._return_limits),
    ):
        finite = np.flatnonzero(np.isfinite(limits.ravel()))
        if len(finite):
            blocks.append(
                sparse.hstack(
                    [
                        movements[finite].multiply(scales),
                        sparse.csr_matrix((len(finite), m)),
                    ],
                    format="csr",
                )
            )
            lower.append(np.zeros(len(finite)))
            upper.append(limits.ravel()[finite])
            labels.extend(f"{name}_{k}" for k in finite)
    for block, (groups, group_ids, shares) in enumerate(
        collateral._concentrations
    ):
        shares_by_id = dict(zip(group_ids, shares))
        rows, cols, values, names = [], [], [], []
        for k in range(m):
            row = coverage.getrow(k)
            members = {}
            for j, value in zip(row.indices, row.data):
                group = groups[asset_positions[j]]
                members.setdefault(group, []).append((j, value))
            for group, entries in members.items():
                index = len(names)
                for j, value in entries:
                    rows.append(index)
                    cols.append(j)
                    values.append(value * scales[j])
                rows.append(index)
                cols.append(n + k)
                values.append(-shares_by_id[group])
                names.append(f"concentration_{block}_{k}_{len(names)}")
        blocks.append(
            sparse.coo_matrix(
                (values, (rows, cols)), shape=(len(names), n + m)
            ).tocsr()
        )
        lower.append(np.full(len(names), -np.inf))
        upper.append(np.zeros(len(names)))
        labels.extend(names)
    coefficients = np.r_[pledges.unit_cost.to_numpy() * scales, np.zeros(m)]
    result = {
        "name": "collateral_allocation",
        "problem_type": collateral._problem_class,
        "format": "matrix",
        "sense": "min",
        "variable_names": [f"assignment_{j}" for j in range(n)]
        + [f"coverage_{k}" for k in range(m)],
        "objective": coefficients,
        "objective_offset": 0.0,
        "constraint_matrix": sparse.vstack(blocks, format="csr"),
        "row_lower": np.concatenate(lower),
        "row_upper": np.concatenate(upper),
        "constraint_names": labels,
        "lower_bounds": np.r_[
            assignment_lower, requirements.amount.to_numpy()
        ],
        "upper_bounds": np.r_[assignment_upper, collateral._coverage_upper],
        "integrality": np.r_[
            np.full(n, int(collateral._mixed_integer)), np.zeros(m, dtype=int)
        ],
    }
    if (
        not np.isfinite(result["constraint_matrix"].data).all()
        or not np.isfinite(coefficients).all()
    ):
        raise ValueError("collateral coefficients exceed float64 range")
    return result


def compile_model(collateral):
    from .._solvers._expressions import linear_model

    return linear_model(matrix_problem(collateral))
