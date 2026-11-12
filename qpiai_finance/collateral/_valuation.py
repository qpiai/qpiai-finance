"""Haircut-adjusted collateral values from supplied marks and FX quotes."""

from collections.abc import Mapping
from fractions import Fraction

import numpy as np
import pandas as pd

from .._validation import copy_index, nonnegative_coefficients, numeric


def _adjusted_values(market_values, haircuts, fx_rates, *, original=False):
    market_values, haircuts, fx_rates = np.broadcast_arrays(
        market_values, haircuts, fx_rates
    )
    values = np.fromiter(
        (
            Fraction(value) * (1 - Fraction(haircut)) * Fraction(rate)
            for value, haircut, rate in zip(
                market_values.flat, haircuts.flat, fx_rates.flat
            )
        ),
        dtype=object,
    ).reshape(market_values.shape)
    if original:
        return values
    try:
        return np.asarray(values, dtype=float)
    except OverflowError as error:
        raise ValueError("collateral values exceed float64 range") from error


def _pledge_values(
    collateral, pledge, j, asset, date_positions, *, original=False
):
    shape = (len(date_positions),)
    prices = np.broadcast_to(
        collateral._inventory.price.iloc[asset]
        if collateral._prices is None
        else collateral._prices[date_positions, asset],
        shape,
    )
    haircuts = np.broadcast_to(
        pledge.haircut
        if collateral._haircuts is None
        else collateral._haircuts[date_positions, j],
        shape,
    )
    fx_rates = np.broadcast_to(
        pledge.fx_rate
        if collateral._fx_rates is None
        else collateral._fx_rates[date_positions, j],
        shape,
    )
    return (
        prices,
        haircuts,
        fx_rates,
        _adjusted_values(prices, haircuts, fx_rates, original=original),
    )


def haircut_adjusted_value(market_values, *, haircuts, fx_rates=1.0):
    """Return market_values * (1-haircuts) * fx_rates per collateral item.

    Supply nonnegative market values, haircut fractions in [0,1] and
    positive valuation FX quotes in target-currency units per native unit.
    With fx_rates=1, values remain in their native currency; amounts in
    different currencies must not be summed without explicit conversion.
    Prices may be supplied instead of total market values to calculate
    per-unit coefficients for a custom Opt or CVXPY financial model.

    Arrays broadcast coefficients to market_values' shape. A Series of
    haircuts or FX quotes aligns to a value Series' index or a value
    DataFrame's columns; a DataFrame aligns both axes. Mappings represent
    labeled Series. Labeled coefficients require labeled market values.
    Scalar inputs return a float; Series/DataFrame labels are preserved.

    This is an offline valuation calculation. It does not establish legal
    eligibility, available inventory, concentration limits or settlement
    rights, estimate haircuts or FX, or implement a regulatory rulebook.
    Sum values explicitly when a total in one currency is required.
    """
    if isinstance(market_values, Mapping):
        market_values = pd.Series(market_values)
    if isinstance(market_values, (pd.Series, pd.DataFrame)):
        if not market_values.index.is_unique or (
            isinstance(market_values, pd.DataFrame)
            and not market_values.columns.is_unique
        ):
            raise ValueError("market value labels must be unique")
        raw = market_values.to_numpy()
    else:
        raw = market_values
    shape = np.shape(raw)
    values = numeric(raw, "market_values", ndim=len(shape))
    if np.any(values < 0):
        raise ValueError("market_values must be nonnegative")
    h = nonnegative_coefficients(haircuts, market_values, shape, "haircuts")
    fx = nonnegative_coefficients(fx_rates, market_values, shape, "fx_rates")
    if np.any(h > 1):
        raise ValueError("haircuts must lie in [0,1]")
    if np.any(fx <= 0):
        raise ValueError("fx_rates must be positive")
    result = _adjusted_values(values, h, fx)
    if isinstance(market_values, pd.Series):
        return pd.Series(
            result,
            index=copy_index(market_values.index),
            name="collateral_value",
        )
    if isinstance(market_values, pd.DataFrame):
        return pd.DataFrame(
            result,
            index=copy_index(market_values.index),
            columns=copy_index(market_values.columns),
        )
    return float(result) if not shape else result
