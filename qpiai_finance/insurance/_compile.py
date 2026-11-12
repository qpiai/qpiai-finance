"""Sparse exact scenario-cost MILP for supplied recovery compositions."""

import numpy as np
from scipy import sparse

from ..risk import _shortfall_form


def matrix_problem(insurance):
    insurance._check()
    n, s = len(insurance._ids), len(insurance._scenarios)
    recoveries = sparse.csr_matrix(insurance._recoveries)
    collectible = recoveries.multiply(insurance._recoverability).tocsr()
    charges = sparse.csr_matrix(insurance._charges)
    keys = list(insurance._tail_limits)
    objective_key = ("total_cost", insurance._confidence)
    if (
        insurance._objective == "reinsurance_cost"
        and insurance._tail_weight > 0
        and objective_key not in keys
    ):
        keys.append(objective_key)
    base = n + 1 + 2 * s
    width = base + len(keys) * (1 + s)
    retained_start, total_start = n + 1, n + 1 + s
    blocks, lower, upper, labels = [], [], [], []

    def add(coefficients, low, high, names):
        blocks.append(sparse.csr_matrix(coefficients))
        lower.append(np.broadcast_to(low, (len(names),)))
        upper.append(np.broadcast_to(high, (len(names),)))
        labels.extend(names)

    premium_row = sparse.csr_matrix(
        np.r_[-insurance._premiums, 1, np.zeros(width - n - 1)][None, :]
    )
    add(premium_row, 0, 0, ["premium_balance"])
    add(
        sparse.hstack(
            [
                collectible,
                sparse.csr_matrix((s, 1)),
                sparse.eye(s),
                sparse.csr_matrix((s, width - retained_start - s)),
            ]
        ),
        insurance._gross,
        insurance._gross,
        [f"retained_balance_{i}" for i in range(s)],
    )
    add(
        sparse.hstack(
            [
                -charges,
                -sparse.csr_matrix(np.ones((s, 1))),
                -sparse.eye(s),
                sparse.eye(s),
                sparse.csr_matrix((s, width - base)),
            ]
        ),
        0,
        0,
        [f"total_cost_balance_{i}" for i in range(s)],
    )
    add(
        sparse.hstack([recoveries, sparse.csr_matrix((s, width - n))]),
        0,
        insurance._gross,
        [f"contractual_recovery_{i}" for i in range(s)],
    )
    count = sparse.csr_matrix(np.r_[np.ones(n), np.zeros(width - n)][None, :])
    low_count, high_count = insurance._count
    add(count, low_count, high_count, ["contract_count"])
    if insurance._composition == "exclusive":
        add(count, 0, 1, ["exclusive_alternatives"])
    for k, ids in enumerate(insurance._exclusive_groups):
        positions = insurance._ids.get_indexer(ids)
        group = sparse.coo_matrix(
            (np.ones(len(ids)), (np.zeros(len(ids), dtype=int), positions)),
            shape=(1, width),
        )
        add(group, 0, 1, [f"exclusive_group_{k}"])
    for block, (ids, coefficients, limits) in enumerate(
        insurance._counterparty_limits
    ):
        add(
            sparse.hstack(
                [
                    sparse.csr_matrix(coefficients),
                    sparse.csr_matrix((len(ids), width - n)),
                ]
            ),
            0,
            limits,
            [f"counterparty_{block}_{i}" for i in range(len(ids))],
        )
    if insurance._surplus_minimum is not None:
        add(
            sparse.hstack(
                [
                    sparse.csr_matrix((s, total_start)),
                    sparse.eye(s),
                    sparse.csr_matrix((s, width - total_start - s)),
                ]
            ),
            -np.inf,
            insurance._surplus - insurance._surplus_minimum,
            [f"surplus_{i}" for i in range(s)],
        )
    objective = np.zeros(width)
    if insurance._objective == "reinsurance_premium":
        objective[n] = 1
    else:
        objective[total_start : total_start + s] = (
            1 - insurance._tail_weight
        ) * insurance._probabilities
    names = (
        [f"selection_{i}" for i in range(n)]
        + ["premium"]
        + [f"retained_{i}" for i in range(s)]
        + [f"total_cost_{i}" for i in range(s)]
    )
    for k, (measure, beta) in enumerate(keys):
        coefficients, inequalities = _shortfall_form(
            insurance._probabilities, beta
        )
        threshold = base + k * (1 + s)
        excess = threshold + 1 + np.arange(s)
        auxiliaries = np.r_[threshold, excess]
        start = retained_start if measure == "retained_loss" else total_start
        block = inequalities.tocoo()
        tail_rows = sparse.coo_matrix(
            (block.data, (block.row, auxiliaries[block.col])),
            shape=(s, width),
        )
        loss_rows = sparse.coo_matrix(
            (np.ones(s), (np.arange(s), start + np.arange(s))),
            shape=(s, width),
        )
        add(
            tail_rows - loss_rows,
            0,
            np.inf,
            [f"tail_loss_{k}_{i}" for i in range(s)],
        )
        tail = sparse.coo_matrix(
            (
                coefficients,
                (np.zeros(s + 1, dtype=int), auxiliaries),
            ),
            shape=(1, width),
        ).tocsr()
        key = (measure, beta)
        if key in insurance._tail_limits:
            add(
                tail, -np.inf, insurance._tail_limits[key], [f"tail_limit_{k}"]
            )
        if (
            insurance._objective == "reinsurance_cost"
            and insurance._tail_weight > 0
            and key == objective_key
        ):
            objective += insurance._tail_weight * tail.toarray().ravel()
        names.extend(
            [f"tail_threshold_{k}"]
            + [f"tail_excess_{k}_{i}" for i in range(s)]
        )
    result = {
        "name": "reinsurance",
        "problem_type": insurance._problem_class,
        "format": "matrix",
        "sense": "min",
        "variable_names": names,
        "objective": objective,
        "objective_offset": 0.0,
        "constraint_matrix": sparse.vstack(blocks, format="csr"),
        "row_lower": np.concatenate(lower),
        "row_upper": np.concatenate(upper),
        "constraint_names": labels,
        "lower_bounds": np.r_[insurance._lower, np.zeros(width - n)],
        "upper_bounds": np.r_[
            insurance._upper,
            insurance._premium_limit,
            np.minimum(insurance._gross, insurance._retained_limit),
            insurance._total_limit,
            np.full(width - base, np.inf),
        ],
        "integrality": np.r_[
            np.ones(n, dtype=int), np.zeros(width - n, dtype=int)
        ],
    }
    if (
        not np.isfinite(result["constraint_matrix"].data).all()
        or not np.isfinite(objective).all()
    ):
        raise ValueError("reinsurance coefficients exceed float64 range")
    return result


def compile_model(insurance):
    from .._solvers._expressions import linear_model

    return linear_model(matrix_problem(insurance))
