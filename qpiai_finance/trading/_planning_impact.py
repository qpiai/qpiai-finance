"""Supplied temporary costs and exact graphs for investment cash accounts."""

import numpy as np
import pandas as pd

from .._validation import identifiers, numeric
from .costs import (
    _curve_segments,
    _cvxpy_power_costs,
    _power_costs,
    _quoted_cost,
)


def prepare_curves(model, curves):
    if curves is None:
        return {}
    fields = {"node", "asset", "quantity", "cost"}
    if not isinstance(curves, pd.DataFrame):
        raise TypeError("curves must be a node/asset/quantity/cost DataFrame")
    if not curves.columns.is_unique or set(curves.columns) != fields:
        raise ValueError(
            "curves require node, asset, quantity and cost columns"
        )
    if curves.empty:
        return {}
    identifiers(curves.node, "curve nodes", unique=False)
    identifiers(curves.asset, "curve assets", unique=False)
    if (
        not curves.node.isin(model._nodes).all()
        or not curves.asset.isin(model._ids).all()
    ):
        raise ValueError("impact curves reference unknown nodes or assets")
    result = {}
    for (node, asset), points in curves.groupby(["node", "asset"], sort=False):
        x = numeric(points.quantity.to_numpy(), "curve quantities", ndim=1)
        y = numeric(points.cost.to_numpy(), "curve costs", ndim=1)
        _curve_segments(x, y)
        k, i = model._nodes.get_loc(node), model._ids.get_loc(asset)
        result[k, i] = pd.DataFrame({"quantity": x, "cost": y})
    return result


def curve_table(model):
    frames = []
    for (k, i), points in model._impact_curves.items():
        frame = points.copy(deep=True)
        frame.insert(0, "asset", model._ids[i])
        frame.insert(0, "node", model._nodes[k])
        frames.append(frame)
    return pd.concat(frames, ignore_index=True) if frames else None


def costs(model, quantities, *, original=False, bits=106):
    magnitude = np.abs(quantities)
    computed = _power_costs(
        magnitude, model._impact_quadratic, model._impact_power,
        original=original, bits=bits,
    )
    values = computed[0] if original else computed
    for position, points in model._impact_curves.items():
        size = magnitude[position]
        if size > points.quantity.iloc[-1]:
            raise ValueError("trade exceeds the supplied impact curve domain")
        quoted = _quoted_cost(size, points)
        values[position] += quoted if original else float(quoted)
    return (values, computed[1]) if original else values


def add_cost_graph(model, k, i, terms, variable, constraint):
    """Add the exact quoted PWL graph; return its cost column, if supplied."""
    points = model._impact_curves.get((k, i))
    if points is None:
        return None
    x, y = points.quantity.to_numpy(), points.cost.to_numpy()
    cost = variable(f"piecewise_impact_{k}_{i}", high=y[-1])
    weights = [
        variable(f"impact_weight_{k}_{i}_{j}", high=1)
        for j in range(len(x))
    ]
    constraint([(column, 1) for column in weights], 1, 1,
               f"impact_weights_{k}_{i}")
    constraint(
        list(terms) + [(column, -value) for column, value in zip(weights, x)],
        0, 0, f"impact_size_{k}_{i}",
    )
    constraint(
        [(cost, 1)] + [(column, -value) for column, value in zip(weights, y)],
        0, 0, f"impact_cost_{k}_{i}",
    )
    if len(x) > 2:
        active = [
            variable(f"impact_segment_{k}_{i}_{j}", high=1, integer=True)
            for j in range(len(x) - 1)
        ]
        constraint([(column, 1) for column in active], 1, 1,
                   f"impact_segment_choice_{k}_{i}")
        for j, column in enumerate(weights):
            neighbors = active[max(0, j - 1):min(len(active), j + 1)]
            constraint(
                [(column, 1)] + [(neighbor, -1) for neighbor in neighbors],
                -np.inf, 0, f"impact_adjacency_{k}_{i}_{j}",
            )
    return cost


def compile_scip(model):
    from pyscipopt import quicksum

    from .._solvers.scip import linear_model

    data = model._linear_data()
    native, variables = linear_model(data)
    buy, sell = model._capacities()
    scales = np.where(model._lots > 0, model._lots, 1.0)
    for k, i in np.ndindex(model._prices.shape):
        quad, power = model._impact_quadratic[k, i], model._impact_power[k, i]
        if max(buy[k, i], sell[k, i]) == 0 or (quad == 0 and power == 0):
            continue
        terms = [
            variables[f"{side}_{k}_{i}"] * scales[k, i]
            for side, capacities in (("buy", buy), ("sell", sell))
            if capacities[k, i] > 0
        ]
        size = native.addVar(name=f"impact_size_scaled_{k}_{i}", lb=0, ub=1)
        variables[f"impact_size_scaled_{k}_{i}"] = size
        maximum = float(max(buy[k, i], sell[k, i]))
        native.addCons(
            maximum * size == quicksum(terms),
            name=f"impact_quantity_scale_{k}_{i}",
        )
        expression = 0
        if quad > 0:
            expression += float((quad * maximum) * maximum) * size**2
        if power > 0:
            expression += (
                float((power * maximum) * np.sqrt(maximum)) * size**1.5
            )
        cost = variables[f"nonlinear_impact_{k}_{i}"]
        # Without cash ceilings, reconstructing the true (lower) cost only
        # increases subsequent cash and cannot worsen any wealth/tail test.
        # Otherwise the actual cost graph is required to prevent cash waste.
        native.addCons(
            cost >= expression if model._cash_monotone else cost == expression,
            name=f"impact_cost_{k}_{i}",
        )
    return native, variables


def compile_cvxpy(model):
    import cvxpy as cp

    from .._solvers.cvxpy import linear_problem

    problem, variables = linear_problem(model._linear_data())
    constraints = list(problem.constraints)
    buy, sell = model._capacities()
    scales = np.where(model._lots > 0, model._lots, 1.0)
    for k, i in np.ndindex(model._prices.shape):
        quad, power = model._impact_quadratic[k, i], model._impact_power[k, i]
        maximum = max(buy[k, i], sell[k, i])
        if maximum == 0 or (quad == 0 and power == 0):
            continue
        size = cp.Variable(nonneg=True)
        quantity = sum(
            variables[f"{side}_{k}_{i}"] * scales[k, i]
            for side, cap in (("buy", buy), ("sell", sell))
            if cap[k, i] > 0
        )
        constraints.extend([maximum * size == quantity, size <= 1])
        cost = _cvxpy_power_costs(
            size,
            (quad * maximum) * maximum,
            (power * maximum) * np.sqrt(maximum),
            signed=False,
        )
        constraints.append(variables[f"nonlinear_impact_{k}_{i}"] >= cost)
    return cp.Problem(problem.objective, constraints), variables
