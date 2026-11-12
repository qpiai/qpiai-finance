"""Condition Gaussian moments without losing original view contributions."""

from fractions import Fraction
from math import lcm

import numpy as np
from scipy.linalg import cholesky, solve_triangular

from ._arithmetic import binary_units


def _add(left, left_power, right, right_power):
    power = min(left_power, right_power)
    return (
        (left << (left_power - power)) + (right << (right_power - power)),
        power,
    )


def _report(numbers, power, denominator=1):
    denominator <<= max(-power, 0)
    return np.asarray((numbers << max(power, 0)) / denominator, dtype=float)


def _report_interval(numbers, power, error, error_power):
    lower, exponent = _add(numbers, power, -error, error_power)
    upper, _ = _add(numbers, power, error, error_power)

    def endpoints(values):
        try:
            return _report(values, exponent)
        except OverflowError:
            pass
        denominator = 1 << max(-exponent, 0)
        result = np.empty(values.shape)
        for index, value in np.ndenumerate(values):
            numerator = int(value) << max(exponent, 0)
            try:
                result[index] = numerator / denominator
            except OverflowError:
                result[index] = np.inf if numerator > 0 else -np.inf
        return result

    low, high = endpoints(lower), endpoints(upper)
    if not np.array_equal(low, high):
        return None
    if not np.isfinite(low).all():
        raise OverflowError("posterior exceeds float64 range")
    return low


def _exact_solve(system, right):
    """Fraction-free SPD elimination; return a common-denominator solution."""
    if np.count_nonzero(system) == len(system):
        # Independent views need scalar divisions, not matrix elimination.
        diagonal = system.diagonal()
        denominator = lcm(*(int(value) for value in diagonal))
        return right * (denominator // diagonal)[:, None], denominator
    matrix, rhs = system.copy(), right.copy()
    previous = 1
    for k in range(len(matrix) - 1):
        pivot = matrix[k, k]
        if pivot <= 0:
            raise ValueError(
                "view observation covariance must be positive definite"
            )
        column = matrix[k + 1:, k].copy()
        matrix[k + 1:, k + 1:] = (
            pivot * matrix[k + 1:, k + 1:]
            - np.outer(column, matrix[k, k + 1:])
        ) // previous
        rhs[k + 1:] = (
            pivot * rhs[k + 1:] - np.outer(column, rhs[k])
        ) // previous
        matrix[k + 1:, k] = 0
        previous = pivot
    determinant = int(matrix[-1, -1])
    if determinant <= 0:
        raise ValueError(
            "view observation covariance must be positive definite"
        )
    solution = np.empty(rhs.shape, dtype=object)
    for k in range(len(matrix) - 1, -1, -1):
        solution[k] = (
            determinant * rhs[k] - matrix[k, k + 1:] @ solution[k + 1:]
        ) // matrix[k, k]
    return solution, determinant


def _inverse_approximations(matrix, power, right):
    """Yield dyadic solutions with certified infinity-norm error bounds.

    R is an exact positive definite Gram matrix. If ||I-RA|| <= 1/2,
    A is positive definite and the Neumann series bounds solution error.
    Newton's inverse update squares this residual without a floating
    subtraction. A failed certificate leaves the exact solve in charge.
    """
    try:
        lower = cholesky(_report(matrix, power), lower=True)
        inverse_lower = solve_triangular(
            lower, np.eye(len(matrix)), lower=True
        )
    except (np.linalg.LinAlgError, OverflowError):
        return
    if not np.isfinite(inverse_lower).all():
        return
    inverse, exponent = binary_units(inverse_lower)
    preconditioner, scale = inverse.T @ inverse, 2 * exponent
    identity = np.diag(np.ones(len(matrix), dtype=object))
    residual, residual_power = _add(
        identity, 0, -preconditioner @ matrix, scale + power
    )
    norm = int(abs(residual).sum(axis=1).max())
    if norm * Fraction(2) ** residual_power > Fraction(1, 2):
        return
    for _ in range(2):
        preconditioner, scale = _add(
            preconditioner, scale,
            residual @ preconditioner, residual_power + scale,
        )
        solution = preconditioner @ right
        # The new residual is E**2. Its norm is <= ||E||**2 <= 1/4,
        # so 2*||E||**2*||solution|| encloses the solution error.
        error = 2 * norm**2 * abs(solution).max(axis=0)
        yield solution, scale, error, 2 * residual_power + scale
        residual = residual @ residual
        residual_power *= 2
        norm = int(abs(residual).sum(axis=1).max())


def posterior(prior, covariance, views, observed, noise, tau):
    """Return Gaussian conditional mean and both posterior covariances.

    Integer binary units preserve the supplied covariance, innovation and
    projections through cancellation and intermediate range extremes.
    Only the final moments are rounded to binary64. Most larger systems
    use a certified approximate inverse; small or unresolved systems use
    fraction-free elimination.
    """
    pi, pi_power = binary_units(prior)
    cov, cov_power = binary_units(covariance)
    p, p_power = binary_units(views)
    q, q_power = binary_units(observed)
    omega, omega_power = binary_units(noise)
    t, tau_power = binary_units([tau])
    t = int(t[0])
    cross = (p @ cov) * t
    cross_power = p_power + cov_power + tau_power
    system, system_power = _add(
        cross @ p.T, cross_power + p_power, omega, omega_power
    )
    innovation, innovation_power = _add(
        q, q_power, -p @ pi, p_power + pi_power
    )
    if any(value <= 0 for value in system.diagonal()):
        raise ValueError(
            "view observation covariance must be positive definite"
        )

    # A power-of-two congruence places each diagonal in [1, 4), retaining
    # every original coefficient and each right-hand side's separate scale.
    diagonal_powers = np.array([
        (int(value).bit_length() - 1 + system_power) // 2
        for value in system.diagonal()
    ], dtype=np.int64)
    maximum = int(diagonal_powers.max())
    shifts = maximum - diagonal_powers
    matrix = system << (shifts[:, None] + shifts[None, :])
    matrix_power = system_power - 2 * maximum
    right = np.column_stack((innovation, cross)) << shifts[:, None]
    h = right[:, 1:]
    h_power = cross_power - maximum
    b_power = innovation_power - maximum
    row_sums = abs(h).sum(axis=0)

    def moments(solution, power, denominator=1, error=None, error_power=0):
        def report(values, exponent, radius, radius_power):
            if error is None:
                return _report(values, exponent, denominator)
            return _report_interval(values, exponent, radius, radius_power)

        mean, exponent = _add(
            pi * denominator, pi_power,
            h.T @ solution[:, 0], h_power + b_power + power,
        )
        radius = 0 if error is None else row_sums * error[0]
        mean = report(mean, exponent, radius, h_power + b_power + error_power)
        if mean is None:
            return None
        uncertainty, predictive = np.empty(cov.shape), np.empty(cov.shape)
        for i in range(len(pi)):
            # The source covariance is symmetric. Compute each conditional
            # covariance once, then share its rounded value across axes.
            prior_row = cov[i, :i + 1]
            row, exponent = _add(
                prior_row * t * denominator, cov_power + tau_power,
                -h[:, i] @ solution[:, 1:i + 2], 2 * h_power + power,
            )
            radius = 0 if error is None else row_sums[i] * error[1:i + 2]
            enclosed = report(
                row, exponent, radius, 2 * h_power + error_power
            )
            if enclosed is None:
                return None
            uncertainty[i, :i + 1] = enclosed
            uncertainty[:i, i] = enclosed[:i]
            row, exponent = _add(
                prior_row * denominator, cov_power, row, exponent
            )
            enclosed = report(
                row, exponent, radius, 2 * h_power + error_power
            )
            if enclosed is None:
                return None
            predictive[i, :i + 1] = enclosed
            predictive[:i, i] = enclosed[:i]
        return mean, uncertainty, predictive

    # For a few views elimination avoids the preconditioner setup cost.
    if len(matrix) > 4 and np.count_nonzero(matrix) > len(matrix):
        for solution, power, error, error_power in _inverse_approximations(
            matrix, matrix_power, right
        ):
            result = moments(
                solution, power, error=error, error_power=error_power
            )
            if result is not None:
                return result
    solution, denominator = _exact_solve(matrix, right)
    return moments(solution, -matrix_power, denominator)
