"""Supplied trading-cost functions in quantity and currency coordinates."""

from collections.abc import Mapping
from fractions import Fraction

import numpy as np
import pandas as pd

from .._arithmetic import square_root_bounds
from .._validation import (
    copy_index,
    lot_capacity,
    lot_quantities,
    nonnegative_coefficients,
    numeric,
    scalar,
)

__all__ = ["transaction_fees", "market_impact_cost"]


def _ticket_cost(variable_costs, fixed_cost, active):
    return variable_costs + fixed_cost * active


def _check_curve_capacity(points, maximum, lot_size, minimum, name):
    if lot_size > 0:
        maximum = lot_quantities(lot_capacity(maximum, lot_size), lot_size)
    if maximum < minimum:
        maximum = 0.0
    if points.quantity.iloc[-1] < maximum:
        raise ValueError(
            f"{name} must cover the permitted trade quantity {maximum:g}; "
            "configure quantity limits and lots before the impact curve"
        )


def _curve_segments(x, y):
    """Validate convex quotes using their original rational differences."""
    if len(x) < 2 or x[0] != 0 or y[0] != 0 or np.any(x[1:] <= x[:-1]):
        raise ValueError(
            "curves must start at (0,0) with increasing quantities"
        )
    segments = []
    for left in range(len(x) - 1):
        start_x, start_y = Fraction(x[left]), Fraction(y[left])
        width = Fraction(x[left + 1]) - start_x
        change = Fraction(y[left + 1]) - start_y
        if change < 0 or (
            segments and change * segments[-1][0] < segments[-1][1] * width
        ):
            raise ValueError(
                "curve slopes must be nonnegative and nondecreasing"
            )
        segments.append((width, change, width * start_y - change * start_x))
    return segments


def _curve_rows(points, *, scale=1.0):
    """Use homogeneous epigraph rows only when float64 retains them exactly."""
    rows = []
    for row in _curve_segments(
        points.quantity.to_numpy(), points.cost.to_numpy()
    ):
        row = (row[0], row[1] * Fraction(float(scale)), row[2])
        try:
            reported = tuple(map(float, row))
        except OverflowError:
            return None
        if any(Fraction(number) != original for number, original in zip(
            reported, row
        )):
            return None
        rows.append(reported)
    return rows


def transaction_fees(quantities, *, per_unit=0.0, fixed=0.0):
    """Return per-unit fees plus one fixed charge per nonzero trade.

    Quantities are signed actual traded units. per_unit is nonnegative
    currency per unit; fixed is nonnegative currency per execution ticket.
    Each entry represents one ticket. A zero quantity has no fee; every
    nonzero quantity incurs its full fixed charge, without a tolerance.
    Spreads, price changes, market impact and tax are separate components.

    Arrays broadcast coefficients to quantities' shape. Series coefficients
    align to a quantity Series' index or a DataFrame's columns; DataFrame
    coefficients align both axes. Mappings represent labeled Series.
    Inputs are not modified; labeled inputs retain their axes in the result.

    This evaluates numeric decisions without solving. A custom optimization
    can use per-unit coefficients directly. Fixed charges require correctly
    linked activation variables; they are not proportional to trade size.
    Direction-dependent fees can be evaluated separately on buy and sell
    quantities, using each side's actual quoted per-unit and fixed charges.
    """
    if isinstance(quantities, Mapping):
        quantities = pd.Series(quantities)
    if isinstance(quantities, (pd.Series, pd.DataFrame)):
        if not quantities.index.is_unique or (
            isinstance(quantities, pd.DataFrame)
            and not quantities.columns.is_unique
        ):
            raise ValueError("quantity labels must be unique")
        raw = quantities.to_numpy()
    else:
        raw = quantities
    shape = np.shape(raw)
    values = numeric(raw, "quantities", ndim=len(shape))
    rates = nonnegative_coefficients(per_unit, quantities, shape, "per_unit")
    charges = nonnegative_coefficients(fixed, quantities, shape, "fixed")
    try:
        with np.errstate(over="raise", invalid="raise"):
            result = _ticket_cost(rates * np.abs(values), charges, values != 0)
    except FloatingPointError as error:
        raise ValueError("transaction fees exceed float64 range") from error
    if isinstance(quantities, pd.Series):
        return pd.Series(
            result, index=copy_index(quantities.index), name="transaction_fees"
        )
    if isinstance(quantities, pd.DataFrame):
        return pd.DataFrame(
            result,
            index=copy_index(quantities.index),
            columns=copy_index(quantities.columns),
        )
    return float(result) if not shape else result


def _power_costs(size, quadratic, power_3_2, *, original=False, bits=106):
    """Evaluate validated per-trade coefficients without redundant copies."""
    if original:
        costs = np.full(size.shape, Fraction(0), dtype=object)
        errors = costs.copy()
        selected = np.flatnonzero((quadratic > 0) | (power_3_2 > 0))
        for position in selected:
            quantity = Fraction(float(size.flat[position]))
            if quadratic.flat[position] > 0:
                costs.flat[position] = Fraction(
                    float(quadratic.flat[position])
                ) * quantity**2
            if power_3_2.flat[position] > 0 and quantity:
                low, high = square_root_bounds(quantity, bits)
                coefficient = Fraction(
                    float(power_3_2.flat[position])
                ) * quantity
                costs.flat[position] += coefficient * (low + high) / 2
                errors.flat[position] = coefficient * (high - low) / 2
        return costs, errors
    costs = np.zeros_like(size)
    selected = quadratic > 0
    with np.errstate(over="raise", invalid="raise"):
        costs[selected] = (quadratic[selected] * size[selected]) * size[
            selected
        ]
        selected = power_3_2 > 0
        costs[selected] += (power_3_2[selected] * size[selected]) * np.sqrt(
            size[selected]
        )
    return costs


def _quoted_cost(quantity, points):
    """Interpolate original quotes; end segments cover diagnostic overruns."""
    x, y = points.quantity.to_numpy(), points.cost.to_numpy()
    right = int(np.searchsorted(x, quantity))
    if right < len(x) and quantity == x[right]:
        return Fraction(y[right])
    right = min(max(right, 1), len(x) - 1)
    left_x, right_x = Fraction(x[right - 1]), Fraction(x[right])
    left_y, right_y = Fraction(y[right - 1]), Fraction(y[right])
    return left_y + (Fraction(quantity) - left_x) * (
        right_y - left_y
    ) / (right_x - left_x)


def _cvxpy_power_costs(quantities, quadratic, power_3_2, *, signed):
    """Compile validated quantities, retaining known nonnegative domains."""
    import cvxpy as cp

    cost = cp.Constant(np.zeros(quantities.shape))
    if np.any(quadratic > 0):
        cost += cp.multiply(quadratic, cp.square(quantities))
    if np.any(power_3_2 > 0):
        size = (
            cp.abs(quantities)
            if signed and not quantities.is_nonneg()
            else quantities
        )
        cost += cp.multiply(power_3_2, cp.power(size, 1.5))
    return cost


def market_impact_cost(
    quantities, *, quadratic=0.0, power_3_2=0.0, backend="numpy"
):
    """Return per-trade temporary impact a*abs(q)**2 + b*abs(q)**1.5.

    Quantities are signed actual trade quantities, not portfolio weights.
    Supply nonnegative coefficients in currency/unit**2 and
    currency/unit**1.5. No volume, volatility, coefficient calibration,
    permanent impact, spread, fixed fee or quoted piecewise curve is
    inferred. Sum the returned costs explicitly when a total is needed.

    NumPy broadcasting applies to array coefficients. Series coefficients
    align to a quantity Series' index or a quantity DataFrame's columns;
    DataFrame coefficients align both axes. Labeled coefficients require
    labeled quantities. Inputs are not modified.

    backend='numpy' evaluates finite numeric quantities and preserves a
    Series/DataFrame's labels. backend='cvxpy' returns a convex CVXPY
    expression for affine quantities, including signed variables. It is
    the actual cost function, not a free cost variable. An equality between
    a convex cost and a cash variable is generally nonconvex; an epigraph
    is exact only when the surrounding model justifies it. Neither route
    changes an existing model, sets an objective or performs a solve.
    """
    if backend not in {"numpy", "cvxpy"}:
        raise ValueError("backend must be 'numpy' or 'cvxpy'")
    if isinstance(quantities, Mapping):
        quantities = pd.Series(quantities)
    if isinstance(quantities, (pd.Series, pd.DataFrame)):
        if not quantities.index.is_unique or (
            isinstance(quantities, pd.DataFrame)
            and not quantities.columns.is_unique
        ):
            raise ValueError("quantity labels must be unique")
        values = quantities.to_numpy()
    else:
        values = quantities
    shape = np.shape(values)
    a = nonnegative_coefficients(quadratic, quantities, shape, "quadratic")
    b = nonnegative_coefficients(power_3_2, quantities, shape, "power_3_2")
    if backend == "numpy":
        values = numeric(values, "quantities", ndim=len(shape))
        costs = _power_costs(np.abs(values), a, b)
        if isinstance(quantities, pd.Series):
            return pd.Series(
                costs,
                index=copy_index(quantities.index),
                name="market_impact_cost",
            )
        if isinstance(quantities, pd.DataFrame):
            return pd.DataFrame(
                costs,
                index=copy_index(quantities.index),
                columns=copy_index(quantities.columns),
            )
        return float(costs) if not shape else costs

    import cvxpy as cp

    if isinstance(values, cp.Expression):
        expression = values
    else:
        entries = [
            value
            if isinstance(value, cp.Expression)
            else scalar(value, "quantities")
            for value in np.asarray(values, dtype=object).flat
        ]
        if not entries:
            raise ValueError("CVXPY quantities must be nonempty")
        expression = cp.reshape(cp.hstack(entries), shape, order="C")
    if not expression.is_affine() or expression.is_complex():
        raise ValueError("CVXPY quantities must be real affine expressions")
    for constant in expression.constants():
        numeric(constant.value, "quantity coefficients", ndim=constant.ndim)
    return _cvxpy_power_costs(expression, a, b, signed=True)
