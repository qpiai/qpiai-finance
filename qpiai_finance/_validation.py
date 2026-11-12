"""Numeric and label checks shared by financial calculations and models."""

from collections.abc import Mapping
from fractions import Fraction
from math import fsum
from numbers import Real

import numpy as np
import pandas as pd
from scipy import sparse
from scipy.linalg import eigvalsh
from scipy.sparse.linalg import eigsh


def instant(value, name):
    """Normalize an explicitly timezone-aware timestamp to UTC."""
    from datetime import datetime

    if not isinstance(value, (str, datetime, pd.Timestamp)):
        raise TypeError(f"{name} must be a timezone-aware timestamp")
    try:
        parsed = pd.Timestamp(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{name} must be a valid timestamp") from error
    if pd.isna(parsed) or parsed.tzinfo is None:
        raise ValueError(
            f"{name} must include an explicit timezone/UTC offset"
        )
    return parsed.tz_convert("UTC")


def seconds(elapsed, *, original=False):
    """Return elapsed seconds without dropping nanosecond precision."""
    if original:
        return Fraction(elapsed.days * 86400 + elapsed.seconds) + Fraction(
            elapsed.microseconds * 1000 + elapsed.nanoseconds, 1_000_000_000
        )
    return float(elapsed / pd.Timedelta(seconds=1))


def scalar(value, name, *, minimum=None, maximum=None):
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
        raise TypeError(f"{name} must be a finite real number")
    value = float(value)
    if not np.isfinite(value):
        raise ValueError(f"{name} must be finite")
    if minimum is not None and value < minimum:
        raise ValueError(f"{name} must be at least {minimum}")
    if maximum is not None and value > maximum:
        raise ValueError(f"{name} must be at most {maximum}")
    return value


def numeric(value, name, *, ndim):
    if isinstance(value, (list, tuple)):
        original = np.asarray(value, dtype=object)
        boolean_types = (bool, np.bool_)
        for item in original.flat:
            if isinstance(item, boolean_types):
                raise ValueError(f"{name} must not contain boolean values")
        del original
    array = np.asarray(value)
    if array.ndim != ndim or array.dtype.kind not in "iuf":
        raise ValueError(
            f"{name} must be a {ndim}-dimensional real numeric array"
        )
    array = array.astype(np.float64, copy=type(value) not in (list, tuple))
    if not np.isfinite(array).all():
        raise ValueError(f"{name} must contain only finite values")
    return array


def nonnegative_coefficients(values, quantities, shape, name):
    if isinstance(values, Mapping):
        values = pd.Series(values)
    if isinstance(values, (pd.Series, pd.DataFrame)):
        if isinstance(values, pd.Series):
            if isinstance(quantities, pd.Series):
                expected = quantities.index
            elif isinstance(quantities, pd.DataFrame):
                expected = quantities.columns
            else:
                raise ValueError(f"labeled {name} requires a labeled input")
            axes = [(values.index, expected)]
            order = {"index": expected}
        elif isinstance(quantities, pd.DataFrame):
            axes = [
                (values.index, quantities.index),
                (values.columns, quantities.columns),
            ]
            order = {"index": quantities.index, "columns": quantities.columns}
        else:
            raise ValueError(f"labeled {name} requires a labeled input")
        for actual, expected in axes:
            if (
                not actual.is_unique
                or len(actual) != len(expected)
                or not actual.isin(expected).all()
            ):
                raise ValueError(f"{name} labels must match the input")
        values = values.reindex(**order).to_numpy()
    values = numeric(values, name, ndim=np.ndim(values))
    if np.any(values < 0):
        raise ValueError(f"{name} must be nonnegative")
    try:
        return np.broadcast_to(values, shape)
    except ValueError as error:
        raise ValueError(f"{name} must broadcast to the input") from error


def lot_capacity(maximum, lot_size):
    """Count whole lots using the supplied quantities' decimal values.

    Both inputs are already validated nonnegative/positive quantities.
    Exact decimal division avoids losing a lot at .30/.10 or admitting
    one when capacity is genuinely below a boundary. The integer bound
    must remain exact when passed to the float64 optimization matrices.
    """
    maximum, lot_size = float(maximum), float(lot_size)
    exact_integer = (1 << 53) - 1
    if (
        maximum <= exact_integer
        and lot_size <= exact_integer
        and (maximum.is_integer() and lot_size.is_integer())
    ):
        count = int(maximum) // int(lot_size)
    else:
        count = Fraction(str(maximum)) // Fraction(str(lot_size))
    if count > exact_integer:
        raise ValueError(
            "lot count exceeds the exact float64 integer range; "
            "rescale quantity units"
        )
    return count


def lot_minimum(minimum, lot_size):
    """Smallest whole lot count meeting the declared quantity minimum."""
    count = lot_capacity(minimum, lot_size)
    quantity = count * Fraction(str(lot_size))
    return count + int(quantity < Fraction(str(minimum)))


def _decimal_lot_quantity(count, lot_size):
    return float(Fraction(str(count)) * Fraction(str(lot_size)))


def lot_residual(quantity, lot_size):
    """Distance to whole lots, respecting decimal quantity reconstruction.

    Quantities and positive lot sizes are already validated. A reconstructed
    whole-lot quantity is valid even when its float representation cannot
    retain every decimal digit of the product. Other residuals are in lots.
    """
    quantity = abs(float(quantity))
    if quantity == 0 or (lot_size == 1 and quantity.is_integer()):
        return 0.0
    count = Fraction(str(quantity)) / Fraction(str(lot_size))
    if count.denominator == 1:
        return 0.0
    lower = count.numerator // count.denominator
    for candidate in (lower, lower + 1):
        try:
            if _decimal_lot_quantity(candidate, lot_size) == quantity:
                return 0.0
        except OverflowError:
            # The next whole lot may exceed the finite quantity range.
            continue
    residual = float(min(count - lower, lower + 1 - count))
    # Underflow must not turn a fractional lot into an exact whole lot.
    return residual if residual > 0 else float(np.nextafter(0.0, 1.0))


def lot_quantities(counts, lot_sizes):
    """Restore physical quantities from declared decimal lot sizes.

    Counts are not rounded here. Callers retain their original integrality
    checks when reconstructing a discrete decision from numerical output.
    """
    if np.ndim(counts) == 0 and np.ndim(lot_sizes) == 0:
        count, size = float(counts), float(lot_sizes)
        exact_integer = (1 << 53) - 1
        integer_product = (
            count.is_integer()
            and size.is_integer()
            and abs(count) <= exact_integer
            and abs(size) <= exact_integer
        )
        try:
            value = (
                count * size
                if size == 1 or integer_product
                else _decimal_lot_quantity(counts, lot_sizes)
            )
        except OverflowError as error:
            raise ValueError("lot quantities exceed float64 range") from error
        if not np.isfinite(value):
            raise ValueError("lot quantities exceed float64 range")
        return value
    counts, sizes = np.broadcast_arrays(
        np.asarray(counts, dtype=float), np.asarray(lot_sizes, dtype=float)
    )
    try:
        with np.errstate(over="raise", invalid="raise"):
            quantities = np.array(counts * sizes, dtype=float)
    except FloatingPointError as error:
        raise ValueError("lot quantities exceed float64 range") from error
    fractional = (
        (sizes != 1)
        & (
            (sizes != np.floor(sizes))
            | (np.abs(sizes) > (1 << 53) - 1)
            | (counts != np.floor(counts))
            | (np.abs(counts) > (1 << 53) - 1)
        )
        & (counts != 0)
    )
    for j in np.flatnonzero(fractional):
        quantities.flat[j] = lot_quantities(counts.flat[j], sizes.flat[j])
    if not np.isfinite(quantities).all():
        raise ValueError("lot quantities exceed float64 range")
    return quantities


def copy_index(index):
    """Own label storage, including categorical values on older pandas."""
    if isinstance(index, pd.RangeIndex):
        return pd.RangeIndex(
            index.start, index.stop, index.step, name=index.name
        )
    if isinstance(index, pd.MultiIndex):
        return pd.MultiIndex(
            levels=[copy_index(level) for level in index.levels],
            codes=[code.copy() for code in index.codes],
            names=index.names,
            sortorder=index.sortorder,
            verify_integrity=False,
        )
    result = index.copy(deep=True)
    if isinstance(result, pd.CategoricalIndex):
        result = result.set_categories(copy_index(index.categories))
    return result


def copy_frame(frame):
    """Copy a financial table and own both its data and label storage."""
    result = frame.copy(deep=True)
    if isinstance(frame, pd.Series):
        if isinstance(frame.dtype, pd.CategoricalDtype):
            result = result.cat.set_categories(
                copy_index(frame.cat.categories)
            )
    else:
        for position, dtype in enumerate(frame.dtypes):
            if isinstance(dtype, pd.CategoricalDtype):
                column = result.iloc[:, position]
                result.isetitem(
                    position,
                    column.cat.set_categories(
                        copy_index(column.cat.categories)
                    ),
                )
    result.index = copy_index(frame.index)
    if isinstance(frame, pd.DataFrame):
        result.columns = copy_index(frame.columns)
    return result


def identifiers(values, name="asset_ids", *, unique=True):
    index = pd.Index(values, tupleize_cols=False)
    # Restrict IDs to portable, unambiguous scalar financial identifiers.
    if any(
        isinstance(item, (bool, np.bool_))
        or not isinstance(item, (str, int, np.integer))
        or (isinstance(item, str) and not item.strip())
        for item in index
    ):
        raise ValueError(
            f"{name} must contain nonempty strings or integer IDs"
        )
    if len(index) == 0 or (unique and not index.is_unique):
        raise ValueError(f"{name} must be nonempty and unique")
    return copy_index(index)


def same_labels(actual, expected, name):
    actual = identifiers(actual, name)
    actual_set, expected_set = set(actual), set(expected)
    if len(actual) != len(expected) or actual_set != expected_set:
        missing = [value for value in expected if value not in actual_set]
        unexpected = [value for value in actual if value not in expected_set]
        raise ValueError(
            f"{name} labels must match; "
            f"missing {missing[:5]!r} ({len(missing)} total), "
            f"unexpected {unexpected[:5]!r} ({len(unexpected)} total)"
        )


def concentration_groups(groups, ids, maximum_share):
    """Align one classification per instrument and its group share limits."""
    if isinstance(groups, Mapping):
        groups = pd.Series(groups)
    if isinstance(groups, pd.Series):
        same_labels(groups.index, ids, "group assignments")
        groups = groups.reindex(ids).tolist()
    else:
        if isinstance(groups, (str, bytes)) or np.ndim(groups) != 1:
            raise ValueError("groups requires one label per instrument")
        groups = list(groups)
    if len(groups) != len(ids):
        raise ValueError("groups requires one label per instrument")
    labels = identifiers(groups, "group labels", unique=False)
    group_ids = identifiers(labels.unique(), "group labels")
    shares = vector(maximum_share, group_ids, "maximum_share", broadcast=True)
    if np.any(shares < 0) or np.any(shares > 1):
        raise ValueError("maximum_share must lie in [0, 1]")
    return groups, group_ids, shares


def group_members(groups, ids):
    """Partition validated instrument positions in declared group order."""
    members = [[] for _ in ids]
    for position, group in enumerate(ids.get_indexer(groups)):
        members[group].append(position)
    return members


def table(value, required, optional, name, *, allow_empty=False):
    """Validate a labeled financial input table and retain an owned copy."""
    if not isinstance(value, pd.DataFrame):
        raise TypeError(f"{name} must be a DataFrame")
    if (
        not value.columns.is_unique
        or not required <= set(value.columns)
        or set(value.columns) - required - optional
    ):
        raise ValueError(
            f"{name} requires {sorted(required)}; "
            f"optional columns: {sorted(optional)}"
        )
    if not (allow_empty and value.empty):
        identifiers(value.index, f"{name} IDs")
    return copy_frame(value)


def unit_labels(values, ids, name="risk_units"):
    if isinstance(values, str):
        values = [values] * len(ids)
    elif isinstance(values, (Mapping, pd.Series)):
        values = pd.Series(values)
        same_labels(values.index, ids, name)
        values = values.reindex(ids).tolist()
    else:
        values = list(values)
    if len(values) != len(ids) or any(
        not isinstance(value, str) or not value.strip() for value in values
    ):
        raise ValueError(f"{name} requires one nonempty unit per row")
    return values


def vector(values, ids, name, *, broadcast=False):
    if isinstance(values, Mapping):
        values = pd.Series(values)
    if isinstance(values, pd.Series):
        same_labels(values.index, ids, name)
        values = values.reindex(ids).to_numpy()
    elif broadcast and np.ndim(values) == 0:
        values = np.full(len(ids), scalar(values, name))
    array = numeric(values, name, ndim=1)
    if array.shape != (len(ids),):
        raise ValueError(f"{name} must have one value per ID ({len(ids)})")
    return array


def lot_sizes(values, ids):
    """Align strictly positive quantity steps to financial identifiers."""
    lots = vector(values, ids, "lot_sizes", broadcast=True)
    if np.any(lots <= 0):
        raise ValueError("lot_sizes must be positive")
    return lots


def matrix_input(values):
    """Normalize column mappings before discovering financial matrix axes."""
    if isinstance(values, Mapping):
        values = pd.DataFrame({
            key: dict(column)
            if isinstance(column, Mapping) and not isinstance(column, dict)
            else column
            for key, column in values.items()
        })
    return values


def matrix(values, rows, columns, name):
    values = matrix_input(values)
    if isinstance(values, pd.DataFrame):
        same_labels(values.index, rows, f"{name} rows")
        same_labels(values.columns, columns, f"{name} columns")
        values = values.reindex(index=rows, columns=columns).to_numpy()
    if sparse.issparse(values):
        if values.shape != (len(rows), len(columns)):
            raise ValueError(
                f"{name} must have shape {(len(rows), len(columns))}"
            )
        if values.dtype.kind not in "iuf":
            raise ValueError(f"{name} must be real numeric")
        result = sparse.csr_matrix(values, dtype=np.float64, copy=True)
        result.sum_duplicates()
        result.eliminate_zeros()
        if not np.isfinite(result.data).all():
            raise ValueError(f"{name} must contain only finite values")
    else:
        result = numeric(values, name, ndim=2)
    if result.shape != (len(rows), len(columns)):
        raise ValueError(f"{name} must have shape {(len(rows), len(columns))}")
    return result


def covariance(values, ids, name="covariance"):
    result = matrix(values, ids, ids, name)
    if sparse.issparse(result):
        difference = result - result.T
        symmetric = difference.nnz == 0
        scale = float(np.max(np.abs(result.data))) if result.nnz else 0.0
    else:
        symmetric = np.array_equal(result, result.T)
        scale = float(np.max(np.abs(result)))
    # Do not silently symmetrize or project a supplied risk model.
    if not symmetric:
        raise ValueError(
            f"{name} must be symmetric; any repair must be explicit"
        )
    if scale == 0:
        return result
    if sparse.issparse(result):
        scaled = result.copy()
        scaled.data /= scale
    else:
        scaled = result / scale
    norm = (
        float(abs(scaled).sum(axis=1).max())
        if sparse.issparse(scaled)
        else float(np.linalg.norm(scaled, ord=np.inf))
    )
    if sparse.issparse(scaled) and len(ids) > 256:
        smallest = float(
            eigsh(scaled, k=1, which="SA", return_eigenvectors=False)[0]
        )
    else:
        dense = scaled.toarray() if sparse.issparse(scaled) else scaled
        smallest = float(eigvalsh(dense, subset_by_index=[0, 0])[0])
    if smallest < -1e-12 * norm:
        raise ValueError(f"{name} must be positive semidefinite")
    return result


def confidence(value):
    value = scalar(value, "confidence")
    if not 0 < value < 1:
        raise ValueError("confidence must be strictly between 0 and 1")
    return value


def probability_weights(values, ids):
    """Validate relative probability weights without altering their ratios."""
    result = vector(values, ids, "probabilities")
    if np.any(result < 0) or np.any(result > 1 + 1e-12) or not np.isclose(
        result.sum(), 1, rtol=0, atol=1e-12
    ):
        raise ValueError(
            "probabilities must be nonnegative and sum to one within 1e-12"
        )
    return result


def probabilities(values, ids):
    result = probability_weights(values, ids)
    return _unit_sum(result)


def _unit_sum(values):
    """Normalize owned nonnegative weights without repeated rounding drift."""
    if np.ptp(values) == 0:
        values.fill(1 / len(values))
    else:
        total = fsum(values)
        # Division of unit-sum float64 weights can leave two ulps of error.
        if abs(total - 1) > 2 * np.finfo(float).eps:
            values /= total
    return values
