"""Return conversion, compounding and moment scaling."""

from collections.abc import Mapping

import numpy as np
import pandas as pd
from scipy import sparse

from ._validation import (
    copy_frame,
    copy_index,
    identifiers,
    instant,
    numeric,
    scalar,
    vector,
)
from ._validation import covariance as checked_covariance
from .cashflows import _date

__all__ = [
    "returns_from_prices",
    "compound_returns",
    "rescale_moments",
    "history_as_of",
]


def _known_history(observations, *, as_of, observed_at, available_at):
    try:
        cutoff = _date(as_of, "as_of")
        parse = _date
    except (TypeError, ValueError):
        cutoff = instant(as_of, "as_of")
        parse = instant
    labeled = isinstance(observations, (pd.Series, pd.DataFrame))
    if np.ndim(observations) not in {1, 2}:
        raise ValueError(
            "history must be observations or observation by asset"
        )
    if observed_at is None:
        if not labeled or not isinstance(observations.index, pd.DatetimeIndex):
            raise ValueError("provide observed_at or a DatetimeIndex")
        observed_at = observations.index

    def times(values, name):
        if isinstance(values, pd.Series) and labeled:
            if (
                not values.index.is_unique
                or not observations.index.is_unique
                or len(values) != len(observations)
                or not observations.index.isin(values.index).all()
            ):
                raise ValueError(f"{name} labels must match history rows")
            values = values.reindex(observations.index)
        if isinstance(values, str) or np.ndim(values) != 1:
            raise ValueError(f"{name} must provide one timestamp per row")
        result = pd.DatetimeIndex([parse(value, name) for value in values])
        if len(result) != len(observations):
            raise ValueError(f"{name} must match the number of observations")
        return result

    observed = times(observed_at, "observed_at")
    if not observed.is_unique or not observed.is_monotonic_increasing:
        raise ValueError("observed_at must be unique and strictly increasing")
    available = (
        observed.copy(deep=True)
        if available_at is None
        else times(available_at, "available_at")
    )
    if np.any(available < observed):
        raise ValueError("availability must not precede observation time")
    positions = np.flatnonzero((observed <= cutoff) & (available <= cutoff))
    if labeled:
        selected = copy_frame(observations.iloc[positions])
    else:
        raw = np.asarray(
            observations,
            dtype=object if isinstance(observations, (list, tuple)) else None,
        )
        selected = raw[positions]
    return (
        selected,
        observed[positions],
        available[positions],
        positions,
        cutoff,
    )


def history_as_of(observations, *, as_of, observed_at=None, available_at=None):
    """Select observations known by a declared decision date or instant.

    A Series/DataFrame may use a DatetimeIndex; arrays require observed_at.
    available_at gives publication/availability per row and defaults to the
    observation time. Series timestamps align to labeled input rows.
    Both observation and availability must be no later than as_of.

    Calendar dates compare whole dates without intraday guarantees. Aware
    timestamps compare exact instants in UTC; do not mix these conventions.
    No sorting, filling, revision/vintage recovery or calendar inference is
    performed. Unavailable numeric values are not inspected or imputed.
    """
    return _known_history(
        observations,
        as_of=as_of,
        observed_at=observed_at,
        available_at=available_at,
    )[0]


def returns_from_prices(prices, *, kind="simple"):
    """Calculate simple or log returns from adjusted prices.

    Prices must already reflect the desired distributions/corporate
    actions. Missing data are rejected. No filling, adjustment or
    annualization is performed.
    """
    if kind not in {"simple", "log"}:
        raise ValueError("kind must be 'simple' or 'log'")
    dimension = np.ndim(prices)
    if dimension not in {1, 2}:
        raise ValueError("prices must be a time series or time × asset matrix")
    array = numeric(prices, "prices", ndim=dimension)
    if (
        array.shape[0] < 2
        or (dimension == 2 and array.shape[1] == 0)
        or np.any(array <= 0)
    ):
        raise ValueError(
            "prices require at least two rows and strictly positive prices"
        )
    if isinstance(prices, (pd.Series, pd.DataFrame)):
        if isinstance(prices, pd.DataFrame):
            identifiers(prices.columns)
        if (
            not prices.index.is_unique
            or not prices.index.is_monotonic_increasing
        ):
            raise ValueError(
                "price observations must have unique, increasing time labels"
            )
    before, after = array[:-1], array[1:]
    try:
        with np.errstate(
            over="raise" if kind == "simple" else "ignore",
            under="ignore",
            divide="ignore",
            invalid="raise",
        ):
            result = after - before
            np.divide(result, before, out=result)
            if kind == "log":
                # Large losses lose precision in 1 + change; extreme gains
                # can overflow that ratio even though their log is finite.
                other = (result < -0.5) | np.isinf(result)
                np.log1p(result, out=result)
                if other.any():
                    first, last = before[other], after[other]
                    ratios = last / first
                    normal = np.isfinite(ratios) & (
                        ratios >= np.finfo(float).tiny
                    )
                    logs = np.empty_like(ratios)
                    logs[normal] = np.log(ratios[normal])
                    logs[~normal] = np.log(last[~normal]) - np.log(
                        first[~normal]
                    )
                    result[other] = logs
    except FloatingPointError as error:
        raise ValueError("price returns exceed float64 range") from error
    if isinstance(prices, pd.DataFrame):
        return pd.DataFrame(
            result,
            index=copy_index(prices.index[1:]),
            columns=copy_index(prices.columns),
        )
    if isinstance(prices, pd.Series):
        return pd.Series(
            result, index=copy_index(prices.index[1:]), name=prices.name
        )
    return result


def _compound_simple_returns(returns, *, axis):
    """Compound validated simple returns along their time axis."""
    if returns.shape[axis] == 1:
        return np.take(returns, 0, axis=axis)
    # A complete loss contributes -inf log growth and exactly -1 return.
    with np.errstate(divide="ignore"):
        return np.expm1(np.log1p(returns).sum(axis=axis))


def compound_returns(returns, *, kind="simple"):
    """Compound time × asset observations into one return per asset."""
    dimension = np.ndim(returns)
    if dimension not in {1, 2}:
        raise ValueError(
            "returns must be a time series or time × asset matrix"
        )
    array = numeric(returns, "returns", ndim=dimension)
    if 0 in array.shape:
        raise ValueError("returns must be nonempty")
    if kind not in {"simple", "log"}:
        raise ValueError("kind must be 'simple' or 'log'")
    if kind == "simple" and np.any(array < -1):
        raise ValueError("simple returns cannot be below -1")
    try:
        with np.errstate(over="raise", invalid="raise"):
            result = (
                _compound_simple_returns(array, axis=0)
                if kind == "simple"
                else array.sum(axis=0)
            )
    except FloatingPointError as error:
        raise ValueError(
            "compounded return is outside float64 range"
        ) from error
    if not np.isfinite(result).all():
        raise ValueError("compounded return is outside float64 range")
    if isinstance(returns, pd.DataFrame):
        identifiers(returns.columns)
        return pd.Series(
            result, index=copy_index(returns.columns), name=f"{kind}_return"
        )
    if dimension == 1:
        return float(result)
    return result


def rescale_moments(expected_returns, covariance, *, periods, assumption):
    """Scale moments under an explicit iid additive assumption.

    Select ``assumption='iid_additive'`` explicitly. This applies to
    additive period P&L or log-return moments, not exact compounded
    simple-return moments.
    """
    if assumption != "iid_additive":
        raise ValueError("the supported assumption is 'iid_additive'")
    periods = scalar(periods, "periods", minimum=0)
    if periods == 0:
        raise ValueError("periods must be positive")
    if isinstance(expected_returns, Mapping):
        expected_returns = pd.Series(expected_returns)
    ids = identifiers(
        expected_returns.index
        if isinstance(expected_returns, pd.Series)
        else range(len(expected_returns))
    )
    mean = vector(expected_returns, ids, "expected_returns")
    cov = checked_covariance(covariance, ids)
    try:
        with np.errstate(over="raise", invalid="raise"):
            scaled_mean, scaled = periods * mean, periods * cov
    except FloatingPointError as error:
        raise ValueError("scaled moments exceed float64 range") from error
    values = scaled.data if sparse.issparse(scaled) else scaled
    if not np.isfinite(scaled_mean).all() or not np.isfinite(values).all():
        raise ValueError("scaled moments exceed float64 range")
    if not sparse.issparse(scaled):
        scaled = pd.DataFrame(scaled, index=ids, columns=ids)
    return pd.Series(scaled_mean, index=ids), scaled
