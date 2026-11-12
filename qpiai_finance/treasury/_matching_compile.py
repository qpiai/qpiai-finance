"""Cash-flow-matching LP/MILP in physical quantities and reserve currency."""

import numpy as np
from scipy import sparse

from .._solvers._expressions import linear_model


def compile_model(matching):
    return linear_model(matrix_problem(matching))


def matrix_problem(matching):
    """Assemble the equivalent sparse Opt LP/MILP without symbolic objects."""
    assets, periods = len(matching._ids), len(matching._dates)
    scales = np.ones(assets) if matching._lots is None else matching._lots
    flows = sparse.csr_matrix(matching._flows).multiply(scales).tocsr()
    names = [f"holding_{i}" for i in range(assets)] + [
        f"cash_{t}" for t in range(periods)
    ]
    holdings = sparse.hstack(
        [
            sparse.diags(scales),
            sparse.csr_matrix((assets, periods)),
        ],
        format="csr",
    )
    cash = sparse.eye(periods, format="csr")
    if periods > 1:
        cash -= sparse.diags(
            1 + matching._returns[1:], offsets=-1, shape=(periods, periods)
        )
    balances = sparse.hstack([-flows[1:], cash[1:]], format="csr")
    blocks = [holdings, balances]
    row_lower = [matching._lower, -matching._liabilities[1:]]
    row_upper = [matching._upper, -matching._liabilities[1:]]
    labels = [f"holding_bounds_{i}" for i in range(assets)] + [
        f"cash_balance_{t}" for t in range(1, periods)
    ]
    if matching._sensitivities is not None:
        risks, values, targets, _ = matching._sensitivities
        values = sparse.csr_matrix(values).multiply(scales)
        blocks.append(
            sparse.hstack(
                [
                    values,
                    sparse.csr_matrix((len(risks), periods)),
                ],
                format="csr",
            )
        )
        row_lower.append(targets)
        row_upper.append(targets)
        labels.extend(f"sensitivity_{i}" for i in range(len(risks)))
    # Initial conservation gives K = purchase outlay + cash_0 + liability_0.
    objective = np.r_[matching._prices * scales, 1.0, np.zeros(periods - 1)]
    initial_liability = float(matching._liabilities[0])
    if np.isfinite(matching._capital_limit):
        blocks.append(sparse.csr_matrix(objective))
        row_lower.append(np.array([-np.inf]))
        row_upper.append(
            np.array([matching._capital_limit - initial_liability])
        )
        labels.append("initial_capital")
    return {
        "name": "liability_matching",
        "problem_type": matching._problem_class,
        "format": "matrix",
        "sense": "min",
        "variable_names": names,
        "objective": objective,
        "objective_offset": initial_liability,
        "constraint_matrix": sparse.vstack(blocks, format="csr"),
        "row_lower": np.concatenate(row_lower),
        "row_upper": np.concatenate(row_upper),
        "constraint_names": labels,
        "lower_bounds": np.r_[np.zeros(assets), matching._cash_lower],
        "upper_bounds": np.r_[
            np.full(assets, np.inf),
            matching._cash_upper,
        ],
        "integrality": np.r_[
            np.full(assets, int(matching._mixed_integer)),
            np.zeros(periods, dtype=int),
        ],
    }
