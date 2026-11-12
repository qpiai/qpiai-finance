"""Financial upper-tail risk and optimization input estimates.

All return moments remain at the supplied observation horizon. No
missing-value imputation, annualization, covariance repair, or currency
conversion is implicit.
"""

from collections.abc import Mapping
from fractions import Fraction
from math import frexp

import numpy as np
import pandas as pd
from scipy import sparse

from ._arithmetic import (
    probability_masses,
    product_sum,
    row_products,
    square_root,
)
from ._gaussian import posterior as _gaussian_posterior
from ._validation import confidence as checked_confidence
from ._validation import (
    copy_index,
    identifiers,
    matrix,
    matrix_input,
    numeric,
    same_labels,
    scalar,
    vector,
)
from ._validation import covariance as checked_covariance
from ._validation import probabilities as checked_probabilities
from ._validation import probability_weights as checked_probability_weights

__all__ = [
    "value_at_risk",
    "expected_shortfall",
    "expected_shortfall_epigraph",
    "sample_moments",
    "exponential_moments",
    "shrink_covariance",
    "portfolio_metrics",
    "risk_contributions",
    "FactorRisk",
    "black_litterman",
]


def _loss_distribution(losses, weights):
    if isinstance(losses, Mapping):
        losses = pd.Series(losses)
    ids = identifiers(
        losses.index if isinstance(losses, pd.Series) else range(len(losses)),
        "scenario_ids",
    )
    losses = vector(losses, ids, "losses")
    p = (
        np.full(len(ids), 1 / len(ids))
        if weights is None
        else checked_probability_weights(weights, ids)
    )
    keep = p > 0
    order = np.argsort(losses[keep], kind="stable")
    return losses[keep][order], p[keep][order]


def value_at_risk(losses, *, confidence=0.95, probabilities=None):
    """Left inverse CDF: smallest loss with cumulative probability ≥
    confidence.

    Omitted probabilities mean equal empirical observations.
    Zero-probability cases are excluded. Losses are signed; negative
    risk values are not clipped. Cumulative probability is accumulated
    without intermediate rounding, then compared in binary64.
    """
    beta = checked_confidence(confidence)
    losses, p = _loss_distribution(losses, probabilities)
    masses, total = probability_masses(p)
    cumulative = np.cumsum(masses)
    lower, upper = 0, len(losses)
    while lower < upper:
        middle = (lower + upper) // 2
        if cumulative[middle] / total >= beta:
            upper = middle
        else:
            lower = middle + 1
    return float(losses[lower])


def expected_shortfall(losses, *, confidence=0.95, probabilities=None):
    """Mean upper loss tail, including fractional boundary probability.

    Supplied probabilities are normalized. Original binary64 probability
    ratios and weighted losses are retained through tail selection; only
    the final mean is rounded to binary64. Signed losses are not clipped.
    """
    beta = checked_confidence(confidence)
    losses, p = _loss_distribution(losses, probabilities)
    masses, total = probability_masses(p[::-1])
    return float(_tail_mean(losses[::-1], masses, total, beta))


def _tail_mean(losses, masses, total, confidence):
    """Unrounded mean for losses ordered from greatest to least."""
    numerator, denominator = confidence.as_integer_ratio()
    capacity = total * (denominator - numerator)
    remaining = capacity
    included_losses, included_masses = [], []
    for loss, mass in zip(losses, masses):
        if mass == 0:
            continue
        included = min(int(mass) * denominator, remaining)
        included_losses.append(loss)
        included_masses.append(included)
        remaining -= included
        if remaining == 0:
            break
    return product_sum((included_masses, included_losses)) / capacity


def _shortfall_form(probabilities, confidence, *, scenario_ids=None):
    """Return the ES coefficients and eta + excess >= loss matrix.

    The first auxiliary is unrestricted eta; the remaining auxiliaries
    are nonnegative excess losses. Loss units are preserved.
    """
    ids = (
        identifiers(range(len(probabilities)), "scenario_ids")
        if scenario_ids is None
        else scenario_ids
    )
    p = checked_probabilities(probabilities, ids)
    beta = checked_confidence(confidence)
    return np.r_[1.0, p / (1 - beta)], sparse.hstack(
        [np.ones((len(p), 1)), sparse.eye(len(p), format="csr")],
        format="csr",
    )


def expected_shortfall_epigraph(
    losses,
    *,
    probabilities,
    confidence=0.95,
    scenario_ids=None,
    name="expected_shortfall",
    backend="opt",
):
    """Build a weighted upper-loss-tail ES term for a custom model.

    Return ``(upper_bound, constraints)`` for scenario losses in consistent
    units: affine Opt expressions or convex CVXPY expressions. Add every
    returned constraint to the model, then
    minimize ``upper_bound``, penalize it with a nonnegative weight in a
    minimization objective, or constrain it from above. This epigraph
    does not enforce equality to ES and cannot be used to maximize ES
    or impose an ES lower bound. Recompute actual risk from the financial
    decision using ``expected_shortfall`` after solving.

    ``backend='opt'`` returns public Opt expressions and constraints;
    ``'cvxpy'`` returns CVXPY objects. No existing model is mutated and
    its objective is not changed. Use a distinct ``name`` for each risk
    block. Losses may be a one-dimensional sequence or labeled mapping/
    Series; CVXPY also accepts a vector expression. Explicit probabilities
    align by scenario ID for labeled inputs; arrays follow scenario_ids,
    or positional order when IDs are omitted. Zero-probability cases do
    not contribute risk; any stress limits must be imposed separately.

    Construction is offline. Solve the resulting model through its
    authenticated Opt or supported external execution route. Custom
    financial rules remain the user's responsibility to verify.
    """
    if backend not in {"opt", "cvxpy"}:
        raise ValueError("backend must be 'opt' or 'cvxpy'")
    if (
        not isinstance(name, str)
        or not name.strip()
        or any(character in name for character in "\x00\r\n")
    ):
        raise ValueError("name must be a nonempty single-line string")
    if isinstance(losses, Mapping):
        losses = pd.Series(losses, dtype=object)
    if isinstance(losses, pd.Series):
        ids = identifiers(losses.index, "scenario_ids")
        if scenario_ids is not None:
            ids = identifiers(scenario_ids, "scenario_ids")
            same_labels(losses.index, ids, "losses")
            losses = losses.reindex(ids)
        losses = losses.tolist()
    else:
        shape = np.shape(losses)
        if len(shape) != 1:
            raise ValueError("losses must be a one-dimensional vector")
        ids = identifiers(
            range(shape[0]) if scenario_ids is None else scenario_ids,
            "scenario_ids",
        )
        if len(ids) != shape[0]:
            raise ValueError("losses must have one value per scenario ID")
    coefficients, lhs = _shortfall_form(
        probabilities, confidence, scenario_ids=ids
    )
    if backend == "cvxpy":
        import cvxpy as cp

        values = (
            losses
            if isinstance(losses, cp.Expression)
            else cp.hstack(
                [
                    loss
                    if isinstance(loss, cp.Expression)
                    else scalar(loss, "losses")
                    for loss in losses
                ]
            )
        )
        if values.shape != (len(ids),) or not values.is_convex():
            raise ValueError("losses must be a convex scenario vector")
        for constant in values.constants():
            numeric(constant.value, "loss coefficients", ndim=constant.ndim)
        eta = cp.Variable(name=f"{name}_threshold")
        excess = cp.Variable(len(ids), nonneg=True, name=f"{name}_excess")
        auxiliaries = cp.hstack([eta, excess])
        return coefficients @ auxiliaries, [lhs @ auxiliaries >= values]

    from qpiai_opt.opt_modeller import Continuous, Expression, Variable

    from ._solvers._expressions import linear

    values = []
    for loss in losses:
        if isinstance(loss, Variable):
            loss = loss + 0
        elif not isinstance(loss, Expression):
            loss = Expression(constant=scalar(loss, "losses"))
        if loss.degree() > 1:
            raise ValueError("losses must be affine expressions")
        values.append(loss)
    auxiliaries = [Continuous(f"{name}_threshold", -np.inf, np.inf)] + [
        Continuous(f"{name}_excess_{s}") for s in range(len(ids))
    ]
    constraints = []
    for s, loss in enumerate(values):
        row = lhs.getrow(s)
        constraints.append(
            linear([auxiliaries[j] for j in row.indices], row.data) >= loss
        )
    return linear(auxiliaries, coefficients), constraints


def _observations(returns):
    if isinstance(returns, pd.Series):
        returns = returns.to_frame()
    if np.ndim(returns) == 1:
        array = numeric(returns, "returns", ndim=1)[:, None]
    else:
        array = numeric(returns, "returns", ndim=2)
    if array.shape[0] < 2 or array.shape[1] == 0:
        raise ValueError(
            "return estimates need at least two observations and one asset"
        )
    ids = identifiers(
        returns.columns
        if isinstance(returns, pd.DataFrame)
        else range(array.shape[1])
    )
    if isinstance(returns, pd.DataFrame):
        if (
            not returns.index.is_unique
            or not returns.index.is_monotonic_increasing
        ):
            raise ValueError(
                "return observations must have unique increasing time labels"
            )
    return array, ids


def sample_moments(returns):
    """Arithmetic sample mean and unbiased sample covariance (T−1
    denominator).
    """
    array, ids = _observations(returns)
    mean, cov = _moment_estimates(array, probabilities=None, unbiased=True)
    return pd.Series(mean, index=ids, name="expected_return"), pd.DataFrame(
        cov, index=ids, columns=ids
    )


def _symmetric_covariance(values):
    """Average derived covariance roundoff without losing finite extremes."""
    with np.errstate(over="ignore", invalid="raise"):
        result = (values + values.T) / 2
        overflow = np.isinf(result)
        if overflow.any():
            result[overflow] = values[overflow] / 2 + values.T[overflow] / 2
    return result


def _moment_estimates(observations, *, probabilities, unbiased):
    """Compute moments in place on an owned observation array.

    None denotes uniform observations; explicit probabilities are normalized.
    Recenter residuals to preserve covariance about a rounded large mean.
    Scale centered rows before forming their Gram matrix so a representable
    covariance does not require an overflowing sum of unscaled squares.
    """
    try:
        with np.errstate(over="raise", invalid="raise"):
            if probabilities is None:
                try:
                    mean = observations.mean(axis=0)
                except FloatingPointError:
                    try:
                        mean = (observations / len(observations)).sum(axis=0)
                    except FloatingPointError:
                        return _exact_moment_estimates(
                            observations, probabilities, unbiased
                        )
                scale = 1 / np.sqrt(len(observations) - int(unbiased))
            else:
                denominator = (
                    1 - probabilities @ probabilities if unbiased else 1.0
                )
                if denominator <= np.finfo(float).eps:
                    raise ValueError(
                        "effective observations are insufficient "
                        "for unbiased covariance"
                    )
                try:
                    mean = probabilities @ observations
                except FloatingPointError:
                    return _exact_moment_estimates(
                        observations, probabilities, unbiased
                    )
                scale = np.sqrt(probabilities / denominator)[:, None]
            if np.any(np.abs(mean) > np.sqrt(np.finfo(float).max)):
                minimum = observations.min(axis=0)
                maximum = observations.max(axis=0)
                constant = minimum == maximum
                mean[constant] = minimum[constant]
                with np.errstate(over="ignore"):
                    outside = np.isinf(minimum - mean) | np.isinf(
                        maximum - mean
                    )
                if outside.any():
                    return _exact_moment_estimates(
                        observations, probabilities, unbiased
                    )
            observations -= mean
            correction = (
                observations.mean(axis=0)
                if probabilities is None
                else probabilities @ observations
            )
            observations -= correction
            mean += correction
            observations *= scale
            cov = _symmetric_covariance(observations.T @ observations)
    except FloatingPointError as error:
        raise ValueError("return moments exceed float64 range") from error
    if not np.isfinite(mean).all() or not np.isfinite(cov).all():
        raise ValueError("return moments exceed float64 range")
    return mean, cov


def _exact_moment_estimates(
    observations, probabilities, unbiased, *, decay=None
):
    """Retain finite moments across extreme intermediate scales."""
    if np.all(observations == observations[0]):
        return observations[0].copy(), np.zeros((observations.shape[1],) * 2)
    if decay is None:
        masses, total = (
            (np.ones(len(observations), dtype=object), len(observations))
            if probabilities is None
            else probability_masses(probabilities)
        )
        first = list(row_products(observations.T, masses))
        squared_mass = sum(int(p) ** 2 for p in masses)
    else:
        decay = Fraction(decay)
        power = decay ** len(observations)
        total = (1 - power) / (1 - decay)
        squared_mass = (1 - power**2) / (1 - decay**2)
        first = np.zeros(observations.shape[1], dtype=object)
        for row in observations:
            first = decay * first + np.fromiter(
                map(Fraction, row), dtype=object
            )
    means = [value / total for value in first]
    denominator = (
        1 - Fraction(squared_mass, total**2)
        if unbiased else Fraction(1)
    )
    cov = np.empty((len(means), len(means)))
    try:
        for i, column in enumerate(observations.T):
            if decay is None:
                weighted = np.fromiter(
                    (int(p) * Fraction(x) for p, x in zip(masses, column)),
                    dtype=object,
                )
                crosses = row_products(observations[:, i:].T, weighted)
            else:
                crosses = np.zeros(len(means) - i, dtype=object)
                for row in observations:
                    products = np.fromiter(
                        (Fraction(row[i]) * Fraction(x) for x in row[i:]),
                        dtype=object,
                    )
                    crosses = decay * crosses + products
            for j, cross in enumerate(crosses, start=i):
                value = float(
                    (cross / total - means[i] * means[j]) / denominator
                )
                cov[i, j] = cov[j, i] = value
        mean = np.array([float(value) for value in means])
    except OverflowError as error:
        raise ValueError("return moments exceed float64 range") from error
    return mean, cov


def _negligible_weight_roundoff(
    observations, decay, subnormals, mean, cov, unbiased
):
    """Bound subnormal weight errors below a quarter ulp of each moment."""
    info = np.finfo(float)
    smallest = info.minexp - info.nmant
    uncertainty = smallest + (subnormals - 1).bit_length()
    amplitude = np.maximum(
        np.abs(observations.min(axis=0)),
        np.abs(observations.max(axis=0)),
    )
    powers = np.frexp(amplitude)[1]
    mean_ulp = np.where(
        mean == 0, smallest,
        np.maximum(np.frexp(mean)[1] - info.nmant - 1, smallest),
    )
    if not np.all(
        (amplitude == 0) | (uncertainty + powers + 2 <= mean_ulp - 2)
    ):
        return False
    cov_ulp = np.where(
        cov == 0, smallest,
        np.maximum(np.frexp(cov)[1] - info.nmant - 1, smallest),
    )
    denominator_power = (
        frexp(decay)[1] - 2 * (len(observations) - 1).bit_length()
        if unbiased else 0
    )
    # Subnormal rounding contributes probability error <=4*R*q, where R
    # counts affected weights and q is the smallest float64 quantum.
    # The last two cases give D >=2*decay/N**2. After bias correction the
    # covariance error is bounded by 64*R*q*A_i*A_j/D**2.
    bound = uncertainty + powers[:, None] + powers[None, :] + 6
    bound -= 2 * denominator_power
    zero = (amplitude[:, None] == 0) | (amplitude[None, :] == 0)
    return bool(np.all(zero | (bound <= cov_ulp - 2)))


def exponential_moments(returns, *, decay, unbiased=True):
    """Normalized exponential weights, newest observation weight
    proportional to 1.

    ``decay`` is in (0,1]. Unbiased weighted covariance divides by
    ``1-sum(p**2)``; population covariance uses denominator 1.
    Observations are independent for the unbiased interpretation. No
    effective-sample fallback.
    """
    array, ids = _observations(returns)
    decay = scalar(decay, "decay", minimum=0, maximum=1)
    if decay == 0:
        raise ValueError("decay must be positive")
    if not isinstance(unbiased, bool):
        raise TypeError("unbiased must be boolean")
    with np.errstate(under="ignore"):
        p = decay ** np.arange(len(array) - 1, -1, -1, dtype=float)
        p /= p.sum()
    if len(p) > 2 and p[0] < np.finfo(float).tiny:
        subnormals = int(np.searchsorted(p, np.finfo(float).tiny))
        start = int(np.searchsorted(p, 0, side="right"))
        try:
            mean, cov = _moment_estimates(
                array[start:].copy(), probabilities=p[start:],
                unbiased=unbiased,
            )
        except ValueError:
            if unbiased and 1 - p @ p <= np.finfo(float).eps:
                raise
            mean, cov = _exact_moment_estimates(
                array, None, unbiased, decay=decay
            )
        else:
            if not _negligible_weight_roundoff(
                array, decay, subnormals, mean, cov, unbiased
            ):
                mean, cov = _exact_moment_estimates(
                    array, None, unbiased, decay=decay
                )
    else:
        mean, cov = _moment_estimates(
            array, probabilities=p, unbiased=unbiased
        )
    return pd.Series(mean, index=ids, name="expected_return"), pd.DataFrame(
        cov, index=ids, columns=ids
    )


def shrink_covariance(covariance, *, intensity, target=None):
    """Explicit (1−intensity)Σ+intensity F; default F is diagonal sample
    variance.

    Intensity is supplied, not claimed to be an estimated Ledoit–Wolf
    coefficient. Mixing dense and sparse inputs returns a dense array;
    a labeled covariance input retains its DataFrame labels.
    """
    covariance = matrix_input(covariance)
    ids = identifiers(
        covariance.index
        if isinstance(covariance, pd.DataFrame)
        else range(np.shape(covariance)[0])
    )
    cov = checked_covariance(covariance, ids)
    intensity = scalar(intensity, "intensity", minimum=0, maximum=1)
    if target is None:
        target = (
            sparse.diags(cov.diagonal(), format="csr")
            if sparse.issparse(cov)
            else np.diag(np.diag(cov))
        )
    target = checked_covariance(target, ids, "target")
    if sparse.issparse(cov) != sparse.issparse(target):
        if sparse.issparse(cov):
            cov = sparse.csr_array(cov, copy=False)
        else:
            target = sparse.csr_array(target, copy=False)
    result = (1 - intensity) * cov + intensity * target
    if isinstance(covariance, pd.DataFrame):
        return pd.DataFrame(np.asarray(result), index=ids, columns=ids)
    return result


class FactorRisk:
    """Σ=B F Bᵀ+diag(d), retained as exposures, factor covariance and
    specific variance.
    """

    def __init__(
        self,
        exposures,
        factor_covariance,
        specific_variance,
        *,
        asset_ids=None,
        factor_ids=None,
    ):
        exposures = matrix_input(exposures)
        shape = np.shape(exposures)
        if len(shape) != 2:
            raise ValueError("exposures must be an asset × factor matrix")
        if isinstance(exposures, pd.DataFrame):
            assets = exposures.index if asset_ids is None else asset_ids
            factors = exposures.columns if factor_ids is None else factor_ids
        else:
            assets = range(shape[0]) if asset_ids is None else asset_ids
            factors = range(shape[1]) if factor_ids is None else factor_ids
        self._assets = identifiers(assets)
        self._factors = identifiers(factors, "factor_ids")
        self._b = matrix(exposures, self._assets, self._factors, "exposures")
        self._f = checked_covariance(
            factor_covariance, self._factors, "factor_covariance"
        )
        self._d = vector(specific_variance, self._assets, "specific_variance")
        if np.any(self._d < 0):
            raise ValueError("specific variances must be nonnegative")

    @property
    def asset_ids(self):
        return copy_index(self._assets)

    def apply(self, weights):
        """Compute Σw without materializing asset covariance."""
        w = vector(weights, self._assets, "weights")
        try:
            result = np.asarray(_risk_product(self, w, original=True), float)
        except OverflowError as error:
            raise ValueError(
                "factor covariance products exceed float64 range"
            ) from error
        if not np.isfinite(result).all():
            raise ValueError("factor covariance products exceed float64 range")
        return result

    def factor_exposures(self, weights):
        """Return B.T @ weights labeled by factor ID.

        Labeled weights align by asset ID; arrays use asset_ids order.
        The units follow the supplied loadings and weights.
        """
        w = vector(weights, self._assets, "weights")
        try:
            exposures = np.asarray(
                _risk_product(self._b.T, w, original=True), float
            )
        except OverflowError as error:
            raise ValueError(
                "factor exposures exceed float64 range"
            ) from error
        return pd.Series(
            exposures,
            index=copy_index(self._factors),
            name="exposure",
        )

    def _components(self, weights, *, original):
        exposures = _risk_product(self._b.T, weights, original=original)
        factors = _risk_product(self._f, exposures, original=original)
        specific = (
            np.fromiter(
                (
                    Fraction(d) * w
                    for d, w in zip(self._d, map(Fraction, weights))
                ),
                dtype=object,
            )
            if original
            else self._d * weights
        )
        return exposures, factors, specific

    def risk_contributions(self, weights):
        """Decompose portfolio risk into factors and specific asset risk.

        Return a table indexed by (component, id), where component is
        'factor' or 'specific'. Exposure is B.T @ weights for factors and
        the asset weight for specific risk. Variance contributions are
        exposure * (F @ exposure) and specific_variance * weight**2.
        Volatility contributions divide these by total volatility and
        are NaN when total volatility is zero. Correlated factors can
        have negative contributions. No covariance is materialized and
        weights are not normalized; labels align by asset ID.
        """
        w = vector(weights, self._assets, "weights")
        exposures, factors, specific = self._components(w, original=True)
        coordinates = np.r_[exposures, w]
        marginal = np.r_[factors, specific]
        variance = _quadratic_risk(
            coordinates, marginal, name="portfolio variance"
        )
        values = _risk_contributions(coordinates, marginal, variance)
        try:
            values["exposure"] = np.asarray(coordinates, float)
        except OverflowError as error:
            raise ValueError(
                "factor exposures exceed float64 range"
            ) from error
        index = pd.MultiIndex.from_tuples(
            [("factor", name) for name in self._factors]
            + [("specific", name) for name in self._assets],
            names=["component", "id"],
        )
        return pd.DataFrame(
            values, index=index, columns=["exposure", "variance", "volatility"]
        )


def _risk_product(matrix, weights, *, original=False):
    """Apply validated risk data without materializing factor covariance.

    Source verification retains original products. Numerical solver
    iterations use their ordinary floating-point matrix kernels.
    """
    try:
        with np.errstate(over="raise", invalid="raise"):
            if isinstance(matrix, FactorRisk):
                _, factors, specific = matrix._components(
                    weights, original=original
                )
                marginal = _risk_product(matrix._b, factors, original=original)
                marginal += specific
            elif original:
                marginal = np.fromiter(
                    row_products(matrix, weights), dtype=object
                )
            else:
                marginal = np.asarray(matrix @ weights).ravel()
    except FloatingPointError as error:
        raise ValueError(
            "portfolio risk calculations exceed float64 range"
        ) from error
    if not original and not np.isfinite(marginal).all():
        raise ValueError("portfolio risk calculations exceed float64 range")
    return marginal


def _quadratic_risk(weights, marginal, *, name):
    """Evaluate PSD risk with the relative negative-value tolerance."""
    variance = product_sum((weights, marginal))
    error = Fraction(1e-12) * product_sum((np.abs(weights), np.abs(marginal)))
    # Scale negative-value tolerance by the evaluated quadratic terms.
    if variance < -error:
        raise ValueError(f"negative {name} beyond roundoff tolerance")
    return max(variance, Fraction(0))


def _risk_inputs(weights, covariance):
    if isinstance(weights, Mapping):
        weights = pd.Series(weights)
    if isinstance(covariance, FactorRisk):
        ids = covariance.asset_ids
        w = vector(weights, ids, "weights")
    else:
        covariance = matrix_input(covariance)
        ids = identifiers(
            covariance.index
            if isinstance(covariance, pd.DataFrame)
            else weights.index
            if isinstance(weights, pd.Series)
            else range(np.shape(covariance)[0])
        )
        w = vector(weights, ids, "weights")
        covariance = checked_covariance(covariance, ids)
    marginal = _risk_product(covariance, w, original=True)
    return (
        ids,
        w,
        covariance,
        marginal,
        _quadratic_risk(w, marginal, name="portfolio variance"),
    )


def _risk_contributions(weights, marginal, variance):
    """Decompose variance and volatility from the same covariance product."""
    try:
        original = np.fromiter(
            (Fraction(w) * Fraction(m) for w, m in zip(weights, marginal)),
            dtype=object,
        )
        contributions = np.asarray(original, float)
        volatility = (
            np.asarray(original / square_root(variance), float)
            if variance > 0
            else np.full(len(weights), np.nan)
        )
    except (FloatingPointError, OverflowError) as error:
        raise ValueError("risk contributions exceed float64 range") from error
    if not np.isfinite(contributions).all() or (
        variance > 0 and not np.isfinite(volatility).all()
    ):
        raise ValueError("risk contributions exceed float64 range")
    return {"variance": contributions, "volatility": volatility}


def risk_contributions(weights, covariance):
    """Variance contributions sum to variance; volatility contributions to
    volatility.

    Volatility contributions are undefined (NaN) at zero volatility.
    """
    ids, w, _, marginal, variance = _risk_inputs(weights, covariance)
    return pd.DataFrame(
        _risk_contributions(w, marginal, variance),
        index=ids,
    )


def _position_totals(weights):
    """Original net and gross position totals in the supplied units."""
    units = np.ones(len(weights))
    return product_sum((weights, units)), product_sum((np.abs(weights), units))


def _portfolio_beta(benchmark, marginal, active_marginal):
    """Reuse original Σw and Σ(w-b) products; their exact difference is Σb."""
    variance = _quadratic_risk(
        benchmark, marginal - active_marginal, name="benchmark variance"
    )
    if variance == 0:
        return np.nan
    try:
        return float(product_sum((benchmark, marginal)) / variance)
    except OverflowError as error:
        raise ValueError("portfolio beta exceeds float64 range") from error


def portfolio_metrics(
    weights, covariance, *, expected_returns=None, benchmark=None
):
    """Metrics in supplied return-horizon units; no hidden normalization of
    weights.

    With benchmark weights, beta is their covariance with the portfolio
    divided by benchmark variance under the supplied covariance model.
    It is NaN for a zero-variance benchmark; no market proxy is inferred.
    """
    ids, w, risk, marginal, variance = _risk_inputs(weights, covariance)
    try:
        with np.errstate(over="raise", invalid="raise"):
            net, gross = _position_totals(w)
            result = {
                "variance": float(variance),
                "volatility": float(square_root(variance)),
                "gross_exposure": float(gross),
                "net_exposure": float(net),
            }
            if expected_returns is not None:
                mu = vector(expected_returns, ids, "expected_returns")
                result["expected_return"] = float(product_sum((mu, w)))
            if benchmark is not None:
                b = vector(benchmark, ids, "benchmark")
                active = np.fromiter(
                    (Fraction(wi) - Fraction(bi) for wi, bi in zip(w, b)),
                    dtype=object,
                )
                active_marginal = _risk_product(risk, active, original=True)
                active_variance = _quadratic_risk(
                    active, active_marginal, name="active variance"
                )
                result["tracking_error"] = float(square_root(active_variance))
                if expected_returns is not None:
                    result["active_return"] = float(
                        product_sum((mu, w), (-mu, b))
                    )
    except (FloatingPointError, OverflowError) as error:
        raise ValueError("portfolio metrics exceed float64 range") from error
    if not all(np.isfinite(value) for value in result.values()):
        raise ValueError("portfolio metrics are outside float64 range")
    if benchmark is not None:
        result["beta"] = _portfolio_beta(b, marginal, active_marginal)
    return result


def black_litterman(
    prior, covariance, views, view_returns, view_covariance, *, tau
):
    """Gaussian posterior mean, mean uncertainty, and predictive return
    covariance.

    C=tau*Σ. Observation system P C Pᵀ+Ω must be positive definite.
    Return covariance of future returns is Σ+posterior mean uncertainty;
    the latter alone is not a return risk model. All inputs share one
    horizon. Mappings use the same labeled conventions as Series and
    DataFrames. A labeled prior defines asset order; otherwise a labeled
    covariance defines the order of the prior array. View rows supply view
    IDs; for an array of views, labeled view returns or their covariance
    supply its row order.
    """
    if isinstance(prior, Mapping):
        prior = pd.Series(prior)
    covariance = matrix_input(covariance)
    views = matrix_input(views)
    if isinstance(view_returns, Mapping):
        view_returns = pd.Series(view_returns)
    view_covariance = matrix_input(view_covariance)
    ids = identifiers(
        prior.index
        if isinstance(prior, pd.Series)
        else covariance.index
        if isinstance(covariance, pd.DataFrame)
        else range(len(prior))
    )
    pi = vector(prior, ids, "prior")
    cov = checked_covariance(covariance, ids)
    cov = cov.toarray() if sparse.issparse(cov) else cov
    view_ids = identifiers(
        views.index
        if isinstance(views, pd.DataFrame)
        else view_returns.index
        if isinstance(view_returns, pd.Series)
        else view_covariance.index
        if isinstance(view_covariance, pd.DataFrame)
        else range(np.shape(views)[0]),
        "view_ids",
    )
    p = matrix(views, view_ids, ids, "views")
    p = p.toarray() if sparse.issparse(p) else p
    q = vector(view_returns, view_ids, "view_returns")
    omega = checked_covariance(view_covariance, view_ids, "view_covariance")
    omega = omega.toarray() if sparse.issparse(omega) else omega
    tau = scalar(tau, "tau", minimum=0)
    if tau == 0:
        raise ValueError("tau must be positive")
    try:
        mean, uncertainty, predictive = _gaussian_posterior(
            pi, cov, p, q, omega, tau
        )
    except (FloatingPointError, OverflowError) as error:
        raise ValueError("posterior exceeds float64 range") from error
    if not all(
        np.isfinite(value).all() for value in (mean, uncertainty, predictive)
    ):
        raise ValueError("posterior exceeds float64 range")
    return {
        "expected_returns": pd.Series(mean, index=ids),
        "mean_covariance": pd.DataFrame(uncertainty, index=ids, columns=ids),
        "predictive_covariance": pd.DataFrame(
            predictive, index=ids, columns=ids
        ),
    }
