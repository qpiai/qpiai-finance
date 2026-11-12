"""Retain original float components until a financial balance is reported."""

from fractions import Fraction
from math import fsum, inf, isfinite, isqrt, nextafter, sqrt

import numpy as np
from scipy import sparse


def float_upper_bound(value):
    """Round an original quantity upward to a float64 upper bound."""
    reported = float(value)
    return nextafter(reported, inf) if Fraction(reported) < value else reported


def _rational_root(value):
    numerator = isqrt(value.numerator)
    denominator = isqrt(value.denominator)
    if numerator**2 == value.numerator and denominator**2 == value.denominator:
        return Fraction(numerator, denominator)
    return None


def square_root(value):
    """Retain root scale and exact rational roots until final reporting."""
    root = _rational_root(value)
    if root is not None:
        return root
    exponent = (
        value.numerator.bit_length() - value.denominator.bit_length()
    ) // 2
    scaled = value / Fraction(2) ** (2 * exponent)
    return Fraction(sqrt(float(scaled))) * Fraction(2) ** exponent


def square_root_bounds(value, bits):
    """Enclose a nonnegative rational root without floating intermediates."""
    root = _rational_root(value)
    if root is not None:
        return root, root
    exponent = (
        value.numerator.bit_length() - value.denominator.bit_length()
    ) // 2
    step = Fraction(2) ** (exponent - bits)
    scaled = value / step**2
    units = isqrt(scaled.numerator // scaled.denominator)
    return units * step, (units + 1) * step


def rounded_interval(value, error):
    """Report a balance only when both enclosing endpoints round alike."""
    if not error:
        return float(value)
    endpoints = []
    for endpoint in (value - error, value + error):
        try:
            endpoints.append(float(endpoint))
        except OverflowError:
            endpoints.append(inf if endpoint > 0 else -inf)
    if endpoints[0] != endpoints[1]:
        return None
    if not isfinite(endpoints[0]):
        raise OverflowError("financial amount exceeds float64 range")
    return endpoints[0]


def subtract_square_root(total, squared):
    """Rationalize positive offsets to retain a small original difference."""
    if squared == 0:
        return total
    root = square_root(squared)
    if total > 0:
        return (total**2 - squared) / (total + root)
    return total - root


def _float_parts(values):
    """Express finite binary64 values as integer significands times 2**e."""
    bits = values.view(np.uint64)
    exponents = ((bits >> 52) & 2047).astype(np.int16)
    mantissas = bits & ((1 << 52) - 1)
    mantissas[exponents > 0] |= 1 << 52
    significands = mantissas.astype(object)
    significands[bits >> 63 != 0] *= -1
    return significands, np.maximum(exponents, 1) - 1075


def binary_units(values):
    """Represent a finite binary64 array as integers times one power of two."""
    values = np.asarray(values, dtype=np.float64)
    numbers, exponents = _float_parts(values)
    nonzero = values != 0
    exponent = int(exponents[nonzero].min()) if nonzero.any() else 0
    numbers <<= np.maximum(exponents - exponent, 0)
    common = None
    for value in numbers.flat:
        if value:
            trailing = (int(value) & -int(value)).bit_length() - 1
            common = trailing if common is None else min(common, trailing)
            if common == 0:
                break
    if common:
        numbers >>= common
        exponent += common
    return numbers, exponent


def product_sum(*terms):
    """Accumulate original rational products without intermediate rounding.

    Float ratios have power-of-two denominators. Integer accumulation
    preserves small components and permits cancellation of individually
    overflowing products. The rational result can be reused in subsequent
    balance calculations; public amounts are still reported as binary64.
    """
    total, scale, other = 0, 0, 0
    for left, right in terms:
        for a, b in zip(left, right):
            if a == 0 or b == 0:
                continue
            numerator_a, denominator_a = a.as_integer_ratio()
            numerator_b, denominator_b = b.as_integer_ratio()
            if denominator_a & (denominator_a - 1) or (
                denominator_b & (denominator_b - 1)
            ):
                other += Fraction(numerator_a, denominator_a) * Fraction(
                    numerator_b, denominator_b
                )
                continue
            exponent = denominator_a.bit_length() + denominator_b.bit_length()
            exponent -= 2
            if exponent > scale:
                total <<= exponent - scale
                scale = exponent
            total += (numerator_a * numerator_b) << (scale - exponent)
    result = Fraction(total, 1 << scale)
    return result + other if other else result


def _dense_row_products(values, quantities):
    """Reduce long dense rows using common integer quantity units."""
    if quantities.dtype == np.float64:
        units, exponent = binary_units(quantities)
    else:
        ratios = [value.as_integer_ratio() for value in quantities]
        if any(denominator & (denominator - 1) for _, denominator in ratios):
            for row in values:
                yield product_sum((row, quantities))
            return
        scale = max(denominator.bit_length() - 1 for _, denominator in ratios)
        units = np.fromiter(
            (
                numerator << (scale - denominator.bit_length() + 1)
                for numerator, denominator in ratios
            ),
            dtype=object,
        )
        exponent = -scale
    for row in values:
        significands, exponents = _float_parts(row)
        smallest = int(exponents[row != 0].min()) if np.any(row != 0) else 0
        # Multiply before shifting to avoid needlessly wide integer products.
        products = (significands * units) << np.maximum(
            exponents - smallest, 0
        )
        total = int(products.sum())
        power = smallest + exponent
        yield Fraction(total << max(power, 0), 1 << max(-power, 0))


def row_products(values, quantities):
    """Yield unrounded instrument totals for validated dense or CSR rows."""
    if sparse.issparse(values):
        rows = values.tocsr(copy=False)
        for start, stop in zip(rows.indptr[:-1], rows.indptr[1:]):
            yield product_sum(
                (rows.data[start:stop], quantities[rows.indices[start:stop]])
            )
    elif len(quantities) >= 256:
        # Short rows avoid the setup cost of temporary object arrays.
        yield from _dense_row_products(values, quantities)
    else:
        for row in values:
            yield product_sum((row, quantities))


def probability_masses(probabilities):
    """Represent validated float64 probabilities in common integer units."""
    if np.all(probabilities == probabilities[0]):
        return np.ones(len(probabilities), dtype=object), len(probabilities)
    mantissas, exponents = _float_parts(probabilities)
    smallest = int(exponents[probabilities > 0].min())
    masses = mantissas << np.maximum(exponents - smallest, 0)
    return masses, sum(masses)


def weighted_mean(values, probabilities):
    """Retain validated probability ratios and original binary-rational values.

    Values may be an iterator of unrounded instrument totals. The caller
    must supply at least one positive weight, including when conditioning.
    """
    masses, total = probability_masses(probabilities)
    return product_sum((masses, values)) / total


def centered_numerators(values, mean, mass):
    """Retain dyadic centered values in common integer probability units."""
    return np.fromiter(
        ((Fraction(value) - mean) * mass for value in values), dtype=object
    )


def offset_totals(total, *, offsets=((),)):
    """Report balances and residuals from an unrounded product total."""
    values = []
    for components in offsets:
        if any(not isfinite(offset) for offset in components):
            values.append(fsum(components))
        else:
            values.append(float(total + sum(map(Fraction, components))))
    return values


def bound_violation(value, lower, upper):
    """Compare original amounts with bounds before reporting a residual."""
    value = Fraction(value)
    return max(
        Fraction(lower) - value if isfinite(lower) else 0,
        value - Fraction(upper) if isfinite(upper) else 0,
        0,
    )


def bound_check(value, lower, upper, tolerance, *, error=0):
    """Verify the complete enclosing interval, or request more precision."""
    violation = bound_violation(value, lower, upper)
    if not error:
        return violation, violation <= tolerance
    tolerance = Fraction(tolerance)
    left, right = value - error, value + error
    low_violation = bound_violation(left, lower, upper)
    high_violation = bound_violation(right, lower, upper)
    if max(low_violation, high_violation) <= tolerance:
        satisfied = True
    elif (isfinite(lower) and right < Fraction(lower) - tolerance) or (
        isfinite(upper) and left > Fraction(upper) + tolerance
    ):
        satisfied = False
    else:
        return violation, None
    minimum = (
        0 if left <= upper and right >= lower
        else min(low_violation, high_violation)
    )
    maximum = max(low_violation, high_violation)
    if float(minimum) != float(maximum):
        return violation, None
    return violation, satisfied
