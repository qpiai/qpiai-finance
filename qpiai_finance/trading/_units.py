"""Financial quantity and currency units for execution cones."""

from fractions import Fraction

import numpy as np
from scipy import sparse

from .._arithmetic import product_sum
from .._solvers._units import binary_exponent


def execution_units(execution, data):
    e = execution
    assets = e._ids.get_indexer(e._opportunities.asset)
    half_power = np.zeros(len(e._ids), dtype=bool)
    np.logical_or.at(half_power, assets, e._power > 0)
    quantities = np.array(
        [
            binary_exponent(abs(order), even=half)
            for order, half in zip(e._orders, half_power)
        ],
        dtype=int,
    )
    prices = np.maximum(
        e._opportunities.ask_price, e._opportunities.bid_price
    ).to_numpy()
    asset_prices = np.zeros(len(e._ids))
    np.maximum.at(asset_prices, assets, prices)
    cash = (
        abs(Fraction(e._cash))
        + sum(map(Fraction, abs(e._flows).tolist()), Fraction(0))
        + product_sum((asset_prices, abs(e._orders)))
    )
    money = binary_exponent(cash)
    columns = np.full(len(data["variable_names"]), money, dtype=int)
    for j, name in enumerate(data["variable_names"]):
        if name.startswith("execution_"):
            columns[j] = quantities[assets[int(name.split("_")[1])]]
        elif name.startswith("remaining_"):
            columns[j] = quantities[int(name.rsplit("_", 1)[1])]
        elif name.startswith("position_abs_change_"):
            i = int(name.rsplit("_", 1)[1])
            columns[j] = quantities[i]
        elif name.startswith("factor_"):
            factor = int(name.rsplit("_", 1)[1])
            row = (
                sparse.csr_matrix(e._risk._b).getcol(factor).toarray().ravel()
            )
            orders = abs(e._orders[e._ids.get_indexer(e._risk.asset_ids)])
            columns[j] = binary_exponent(product_sum((abs(row), orders)))
        elif name.startswith("ticket_"):
            columns[j] = 0
    columns[np.asarray(data["integrality"], dtype=bool)] = 0
    return columns, quantities, money


def order_totals(data):
    """Sum the existing recursions to reinforce total order conservation."""
    rows = [
        (row, int(name.rsplit("_", 1)[1]))
        for row, name in enumerate(data["constraint_names"])
        if name.startswith("order_balance_")
    ]
    if not rows:
        return data
    assets = sorted({asset for _, asset in rows})
    positions = {asset: i for i, asset in enumerate(assets)}
    total = sparse.coo_matrix(
        (
            np.ones(len(rows)),
            ([positions[a] for _, a in rows], [row for row, _ in rows]),
        ),
        shape=(len(assets), len(data["constraint_names"])),
    ).tocsr()
    return dict(
        data,
        constraint_matrix=sparse.vstack(
            [data["constraint_matrix"], total @ data["constraint_matrix"]],
            format="csr",
        ),
        row_lower=np.r_[data["row_lower"], total @ data["row_lower"]],
        row_upper=np.r_[data["row_upper"], total @ data["row_upper"]],
        constraint_names=data["constraint_names"]
        + [f"order_total_{i}" for i in assets],
    )
