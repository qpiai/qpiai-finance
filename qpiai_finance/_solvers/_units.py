"""Reversible binary units for numerical interoperability."""

from fractions import Fraction

import numpy as np


def binary_exponent(amount, *, even=False):
    amount = abs(Fraction(amount))
    if not amount:
        return 0
    exponent = amount.numerator.bit_length() - amount.denominator.bit_length()
    exponent += Fraction(2) ** exponent < amount
    if even:
        exponent += exponent % 2
    return min(max(exponent, -1022), 1022 if even else 1023)


def binary_scale(values, exponents):
    """Change units without losing any finite original binary64 term."""
    values = np.asarray(values, dtype=float)
    with np.errstate(over="raise", invalid="raise", under="ignore"):
        scaled = np.ldexp(values, exponents)
        restored = np.ldexp(scaled, -np.asarray(exponents))
    finite = np.isfinite(values)
    if not np.array_equal(values[finite], restored[finite]):
        raise FloatingPointError("binary unit conversion loses a coefficient")
    return scaled


def scale_matrix(data, columns, objective_exponent):
    """Return x=D*y, normalized rows and objective, preserving domains."""
    if np.any(columns[np.asarray(data["integrality"], bool)] != 0):
        raise ValueError(
            "integer coordinates must retain their original units"
        )
    matrix = data["constraint_matrix"].tocoo(copy=True)
    magnitude = np.maximum(
        np.where(np.isfinite(data["row_lower"]), abs(data["row_lower"]), 0),
        np.where(np.isfinite(data["row_upper"]), abs(data["row_upper"]), 0),
    )
    mantissa, exponent = np.frexp(magnitude)
    rows = exponent - (mantissa == 0.5)
    missing = np.iinfo(rows.dtype).min
    rows[magnitude == 0] = missing
    mantissa, exponent = np.frexp(abs(matrix.data))
    coefficient_units = exponent - (mantissa == 0.5) + columns[matrix.col]
    nonzero = matrix.data != 0
    np.maximum.at(rows, matrix.row[nonzero], coefficient_units[nonzero])
    rows[rows == missing] = 0
    rows = np.clip(rows, -1022, 1023).astype(int)
    matrix.data = binary_scale(
        matrix.data, columns[matrix.col] - rows[matrix.row]
    )
    scaled = dict(
        data,
        objective=binary_scale(
            data["objective"], columns - objective_exponent
        ),
        objective_offset=float(
            binary_scale(data["objective_offset"], -objective_exponent)
        ),
        constraint_matrix=matrix.tocsr(),
        row_lower=binary_scale(data["row_lower"], -rows),
        row_upper=binary_scale(data["row_upper"], -rows),
        lower_bounds=binary_scale(data["lower_bounds"], -columns),
        upper_bounds=binary_scale(data["upper_bounds"], -columns),
    )
    return scaled, rows


def clarabel_options(context, options, tolerance):
    import clarabel

    from .._validation import scalar

    prepared = options.copy()
    defaults = clarabel.DefaultSettings()
    with np.errstate(over="ignore", under="ignore"):
        target = float(
            np.ldexp(tolerance, -context["maximum_coordinate_exponent"])
        )
    for name in ("tol_feas", "tol_gap_rel", "tol_gap_abs"):
        if name not in prepared:
            prepared[name] = min(getattr(defaults, name), target)
    for name in ("tol_gap_abs", "reduced_tol_gap_abs"):
        if name not in options:
            continue
        value = scalar(options[name], name, minimum=0)
        try:
            prepared[name] = float(
                binary_scale(value, -context["objective_exponent"])
            )
        except FloatingPointError as error:
            raise ValueError(
                "absolute objective tolerance exceeds numerical range"
            ) from error
    return prepared
