"""Class-matched optimization representations of signed hedge decisions."""

from math import fsum

import numpy as np
from scipy import sparse

from .._solvers._expressions import linear, quadratic


def _difference_parts(before, target):
    """Keep the rounding remainder of an affine constant difference."""
    before, target = float(before), float(target)
    high = before - target
    if not np.isfinite(high):
        return before, -target
    return high, fsum((before, -high, -target))


def _relative_opt(model, change, before, target, name):
    from qpiai_opt.opt_modeller import Continuous

    high, low = _difference_parts(before, target)
    if low == 0:
        return change + high
    shifted = model.add_variable(
        Continuous(f"{name}_shift", -float("inf"), float("inf"))
    )
    model.add_constraint(
        shifted == change + high, label=f"{name}_shift_balance"
    )
    return shifted + low


def _relative_cvxpy(change, before, target, constraints, name):
    import cvxpy as cp

    parts = np.array([_difference_parts(a, b) for a, b in zip(before, target)])
    high, low = parts[:, 0], parts[:, 1]
    if not np.any(low):
        return change + high
    shifted = cp.Variable(len(before), name=f"{name}_shift")
    constraints.append(shifted == change + high)
    return shifted + low


def compile_opt(hedge):
    from qpiai_opt.opt_modeller import Continuous, Integer, Model

    if hedge._needs_external:
        raise ValueError("integer quadratic hedging requires solver='scip'")
    model = Model("hedging")
    raw = model.add_variables(
        [
            (Continuous if hedge._lots is None else Integer)(
                f"hedge_{i}",
                -float("inf"),
                float("inf"),
            )
            for i in range(len(hedge._ids))
        ]
    )
    quantities = (
        raw
        if hedge._lots is None
        else [float(lot) * variable for lot, variable in zip(hedge._lots, raw)]
    )
    scales = np.ones(len(raw)) if hedge._lots is None else hedge._lots
    buys = model.add_variables(
        [Continuous(f"buy_{i}") for i in range(len(raw))]
    )
    sells = model.add_variables(
        [Continuous(f"sell_{i}") for i in range(len(raw))]
    )
    buy_cost = hedge._buy_cost + (hedge._ask - hedge._prices)
    sell_cost = hedge._sell_cost + (hedge._prices - hedge._bid)
    costs = linear(buys, buy_cost) + linear(sells, sell_cost)
    for i, quantity in enumerate(quantities):
        model.add_constraint(
            quantity == buys[i] - sells[i], label=f"trade_balance_{i}"
        )
        for low, high, before, name in (
            (hedge._lower[i], hedge._upper[i], 0, "trade"),
            (
                hedge._position_lower[i],
                hedge._position_upper[i],
                hedge._current[i],
                "position",
            ),
        ):
            if np.isfinite(low):
                model.add_constraint(
                    _relative_opt(
                        model, quantity, before, low, f"{name}_lower_{i}"
                    )
                    >= 0,
                    label=f"{name}_lower_{i}",
                )
            if np.isfinite(high):
                model.add_constraint(
                    _relative_opt(
                        model, quantity, before, high, f"{name}_upper_{i}"
                    )
                    <= 0,
                    label=f"{name}_upper_{i}",
                )
    residuals = []
    rows = sparse.csr_matrix(hedge._sensitivities)
    for i in range(len(hedge._risks)):
        row = rows.getrow(i)
        change = linear(
            [raw[j] for j in row.indices], row.data * scales[row.indices]
        )
        if np.isfinite(hedge._risk_lower[i]) and (
            row.nnz or hedge._exposure[i] < hedge._risk_lower[i]
        ):
            model.add_constraint(
                _relative_opt(
                    model,
                    change,
                    hedge._exposure[i],
                    hedge._risk_lower[i],
                    f"risk_lower_{i}",
                )
                >= 0,
                label=f"risk_lower_{i}",
            )
        if np.isfinite(hedge._risk_upper[i]) and (
            row.nnz or hedge._exposure[i] > hedge._risk_upper[i]
        ):
            model.add_constraint(
                _relative_opt(
                    model,
                    change,
                    hedge._exposure[i],
                    hedge._risk_upper[i],
                    f"risk_upper_{i}",
                )
                <= 0,
                label=f"risk_upper_{i}",
            )
        if hedge._objective == "hedge_cost" and (
            row.nnz or hedge._exposure[i] != hedge._target[i]
        ):
            model.add_constraint(
                _relative_opt(
                    model,
                    change,
                    hedge._exposure[i],
                    hedge._target[i],
                    f"exact_match_{i}",
                )
                == 0,
                label=f"exact_match_{i}",
            )
        if hedge._objective == "hedge_mismatch":
            residual = model.add_variable(
                Continuous(f"risk_residual_{i}", -float("inf"), float("inf"))
            )
            model.add_constraint(
                residual
                == _relative_opt(
                    model,
                    change,
                    hedge._exposure[i],
                    hedge._target[i],
                    f"residual_{i}",
                ),
                label=f"residual_balance_{i}",
            )
            residuals.append(residual)
    if hedge._cash is not None:
        model.add_constraint(
            linear(raw, hedge._prices * scales) + costs <= hedge._cash,
            label="execution_cash",
        )
    if hedge._capital is not None:
        coefficients, maximum = hedge._capital
        absolute = model.add_variables(
            [Continuous(f"position_abs_{i}") for i in range(len(raw))]
        )
        for i, value in enumerate(absolute):
            position = quantities[i] + float(hedge._current[i])
            model.add_constraint(value >= position)
            model.add_constraint(value >= -position)
        model.add_constraint(
            linear(absolute, coefficients) <= maximum, label="capital"
        )
    objective = costs
    if hedge._objective == "hedge_mismatch":
        objective = (
            quadratic(residuals, hedge._weights) + hedge._cost_weight * costs
        )
    from ._scenarios import compile_opt as scenario_objective

    scenario = scenario_objective(hedge, model, raw, scales, costs)
    if scenario is not None:
        objective = scenario
    model.minimize(objective)
    return model


def compile_cvxpy(hedge):
    import cvxpy as cp

    raw = cp.Variable(len(hedge._ids), integer=hedge._mixed_integer)
    quantities = raw if hedge._lots is None else cp.multiply(hedge._lots, raw)
    positions = hedge._current + quantities
    change = hedge._sensitivities @ quantities if len(hedge._risks) else None
    costs = (hedge._buy_cost + (hedge._ask - hedge._prices)) @ cp.pos(
        quantities
    ) + (hedge._sell_cost + (hedge._prices - hedge._bid)) @ cp.pos(-quantities)
    constraints = []
    changing = (
        hedge._sensitivities.getnnz(axis=1) > 0
        if sparse.issparse(hedge._sensitivities)
        else np.any(hedge._sensitivities != 0, axis=1)
    )
    if hedge._objective == "hedge_cost":
        required = changing | (hedge._exposure != hedge._target)
        if required.any():
            constraints.append(
                _relative_cvxpy(
                    change[required],
                    hedge._exposure[required],
                    hedge._target[required],
                    constraints,
                    "exact_match",
                )
                == 0
            )
    for value, before, low, high, name in (
        (
            quantities,
            np.zeros(len(hedge._ids)),
            hedge._lower,
            hedge._upper,
            "trade",
        ),
        (
            quantities,
            hedge._current,
            hedge._position_lower,
            hedge._position_upper,
            "position",
        ),
        (
            change,
            hedge._exposure,
            hedge._risk_lower,
            hedge._risk_upper,
            "risk",
        ),
    ):
        if value is None:
            continue
        fixed = np.isfinite(low) & (low == high)
        lower = np.isfinite(low) & ~fixed
        upper = np.isfinite(high) & ~fixed
        if name == "risk":
            fixed &= changing | (before != low)
            lower &= changing | (before < low)
            upper &= changing | (before > high)
        for selected, bounds, side in (
            (fixed, low, "fixed"),
            (lower, low, "lower"),
            (upper, high, "upper"),
        ):
            if not selected.any():
                continue
            relative = _relative_cvxpy(
                value[selected],
                before[selected],
                bounds[selected],
                constraints,
                f"{name}_{side}",
            )
            if side == "fixed":
                constraints.append(relative == 0)
            elif side == "lower":
                constraints.append(relative >= 0)
            else:
                constraints.append(relative <= 0)
    if hedge._cash is not None:
        constraints.append(hedge._prices @ quantities + costs <= hedge._cash)
    if hedge._capital is not None:
        coefficients, maximum = hedge._capital
        constraints.append(coefficients @ cp.abs(positions) <= maximum)
    objective = costs
    if hedge._objective == "hedge_mismatch":
        residual = _relative_cvxpy(
            change,
            hedge._exposure,
            hedge._target,
            constraints,
            "risk_residual",
        )
        objective = cp.quad_form(residual, cp.psd_wrap(hedge._weights))
        objective += hedge._cost_weight * costs
    from ._scenarios import compile_cvxpy as scenario_objective

    scenario = scenario_objective(hedge, quantities, costs, constraints)
    if scenario is not None:
        objective = scenario
    variables = {f"hedge_{i}": raw[i] for i in range(len(hedge._ids))}
    return cp.Problem(cp.Minimize(objective), constraints), variables
