"""Exact selection-to-weight portfolio polynomial compilation."""

from collections import Counter, defaultdict
from copy import deepcopy
from fractions import Fraction
from itertools import combinations_with_replacement
from math import factorial, fsum
from time import perf_counter

import numpy as np
from scipy import sparse

from .._arithmetic import (
    centered_numerators,
    probability_masses,
    product_sum,
    row_products,
    weighted_mean,
)
from .._validation import scalar
from ..portfolio import PortfolioModel
from ..risk import FactorRisk
from ._encoding import PortfolioEncoding


def _moment_terms(portfolio, names, weight):
    scenarios = portfolio._scenarios
    probabilities = scenarios._probabilities
    values = scenarios._values
    if sparse.issparse(values):
        values = values.tocsc()
    masses, total = probability_masses(probabilities)
    means = [value / total for value in row_products(values.T, masses)]

    def centered_column(index):
        column = values[:, index]
        if sparse.issparse(column):
            column = column.toarray().ravel()
        return centered_numerators(
            np.asarray(column).ravel(), means[index], total
        )

    aversion, preference, tail_aversion = portfolio._moment_preferences
    for power, coefficient in (
        (2, aversion),
        (3, -preference),
        (4, tail_aversion),
    ):
        if coefficient == 0:
            continue
        for indices in combinations_with_replacement(range(len(names)), power):
            product = np.full(len(probabilities), Fraction(1), dtype=object)
            multiplicity = factorial(power)
            for index, repeats in Counter(indices).items():
                product *= centered_column(index) ** repeats
                multiplicity //= factorial(repeats)
            value = (
                Fraction(coefficient)
                * Fraction(weight) ** power
                * multiplicity
                * weighted_mean(product, probabilities)
                / total**power
            )
            yield tuple(names[i] for i in sorted(set(indices))), value


def _objective_terms(portfolio, names, weight):
    objective = portfolio._objective
    weight = Fraction(weight)
    if objective in {"utility", "moment_utility"}:
        for name, forecast in zip(names, portfolio._mu):
            yield (name,), -weight * Fraction(forecast)
    if objective == "moment_utility":
        yield from _moment_terms(portfolio, names, weight)
        return
    multiplier = (
        Fraction(portfolio._risk_aversion) / 2
        if objective == "utility"
        else Fraction(1)
    )
    if multiplier == 0:
        return
    covariance = portfolio._covariance
    if sparse.issparse(covariance):
        covariance = covariance.tocsc()
    for i, name in enumerate(names):
        if isinstance(covariance, FactorRisk):
            unit = np.zeros(len(names))
            unit[i] = 1
            column = portfolio._risk_apply(unit, original=True)
        elif sparse.issparse(covariance):
            column = covariance[:, i].toarray().ravel()
        else:
            column = covariance[:, i]
        yield (name,), multiplier * weight**2 * Fraction(column[i])
        for j in range(i + 1, len(names)):
            yield (
                (name, names[j]),
                (2 * multiplier * weight**2 * Fraction(column[j])),
            )
    if objective == "tracking_error":
        marginal = portfolio._risk_apply(portfolio._benchmark, original=True)
        yield (), product_sum((portfolio._benchmark, marginal))
        for name, value in zip(names, marginal):
            yield (name,), -2 * weight * value


def _aggregate(terms):
    contributions = defaultdict(list)
    for term, value in terms:
        if not isinstance(value, Fraction) and not np.isfinite(value):
            raise ValueError("binary coefficients exceed float64 range")
        contributions[tuple(sorted(set(term)))].append(value)
    try:
        result = {
            term: (
                float(sum(map(Fraction, values)))
                if any(isinstance(value, Fraction) for value in values)
                else fsum(values)
            )
            for term, values in contributions.items()
        }
    except OverflowError as error:
        raise ValueError("binary coefficients exceed float64 range") from error
    return {term: value for term, value in result.items() if value != 0}


def compile_portfolio(
    model,
    *,
    representation="hubo",
    penalty=None,
    quadratization_strength=None,
):
    """Compile an equal-weight selection portfolio to HUBO, QUBO or Ising.

    Each selected asset receives net_weight/count, with no discretization
    of a continuous allocation. Supported objectives are variance,
    tracking error, mean-variance utility and moment utility. Cardinality
    and individual weight bounds are encoded. Other constraints currently
    require another supported financial formulation and are rejected here.

    The default selection penalty exceeds a certified objective-range
    bound. A smaller explicit penalty is labeled heuristic. Native HUBO
    preserves higher-order terms; QUBO and pairwise Ising use Opt's exact
    quadratization and retain its auxiliary mapping.
    """
    from qpiai_opt.opt_modeller import hubo_to_qubo, qubo_to_ising
    from qpiai_opt.opt_solvers.hubo import HUBOProblem
    from qpiai_opt.opt_solvers.ising import IsingProblem
    from qpiai_opt.opt_solvers.qubo import QUBOProblem

    started = perf_counter()
    if not isinstance(model, PortfolioModel):
        raise TypeError("model must be a PortfolioModel")
    if representation not in {"hubo", "qubo", "ising"}:
        raise ValueError("representation must be 'hubo', 'qubo' or 'ising'")
    if representation == "hubo" and quadratization_strength is not None:
        raise ValueError("native HUBO does not use quadratization_strength")
    portfolio = deepcopy(model)
    portfolio._check()
    selection = portfolio._selection
    if selection is None or not selection["equal_weight"]:
        raise ValueError(
            "binary portfolio compilation requires "
            "select_assets(count=..., equal_weight=True)"
        )
    if portfolio._objective not in {
        "variance",
        "utility",
        "tracking_error",
        "moment_utility",
    }:
        raise ValueError("this portfolio objective has no binary compilation")
    unsupported = {
        "fixed selection": portfolio._fixed_selection is not None,
        "cash account": portfolio._account is not None,
        "minimum return": portfolio._minimum_return is not None,
        "exposures": bool(portfolio._exposures),
        "turnover": portfolio._turnover is not None,
        "volatility": portfolio._volatility_limit is not None,
        "robust returns": portfolio._return_uncertainty is not None,
    }
    missing = [name for name, present in unsupported.items() if present]
    if missing:
        raise ValueError(
            "binary compilation does not encode: "
            + ", ".join(missing)
            + "; use another supported financial formulation "
            "for these constraints"
        )
    names = tuple(f"selected_{i}" for i in range(len(portfolio._ids)))
    count = selection["count"]
    weight = portfolio._net_weight / count
    objective = _aggregate(_objective_terms(portfolio, names, weight))
    try:
        objective_range = fsum(abs(v) for t, v in objective.items() if t)
    except OverflowError as error:
        raise ValueError("objective range exceeds float64 range") from error
    if penalty is None:
        penalty = (
            max(objective_range * 1.01, np.nextafter(objective_range, np.inf))
            if objective_range > 0
            else 1.0
        )
    penalty = scalar(penalty, "penalty", minimum=0)
    if penalty == 0:
        raise ValueError("penalty must be strictly positive")

    # Squared integer count error has minimum positive value one.
    violations = [((), float(count**2))]
    for i, name in enumerate(names):
        violations.append(((name,), float(1 - 2 * count)))
        for other in names[i + 1 :]:
            violations.append(((name, other), 2.0))
        lower, upper = portfolio._lower[i], portfolio._upper[i]
        zero_invalid = int(not lower <= 0 <= upper)
        one_invalid = int(not lower <= weight <= upper)
        violations.extend(
            [
                ((), zero_invalid),
                ((name,), one_invalid - zero_invalid),
            ]
        )
    if (
        portfolio._leverage is not None
        and portfolio._net_weight > portfolio._leverage
    ):
        violations.append(((), 1.0))
    violations = _aggregate(violations)
    polynomial = _aggregate(
        [
            *objective.items(),
            *((term, penalty * value) for term, value in violations.items()),
        ]
    )
    conversion = None
    if representation == "hubo":
        problem = HUBOProblem(
            num_variables=len(names),
            variable_names=names,
            polynomial_dict=polynomial,
        )
    else:
        conversion = hubo_to_qubo(
            polynomial,
            variable_names=names,
            matrix_format="upper",
            strength=quadratization_strength,
        )
        if representation == "qubo":
            problem = QUBOProblem(
                num_variables=conversion.num_variables,
                variable_names=conversion.variable_names,
                qubo_dict=conversion.qubo,
                offset=conversion.offset,
                matrix_format="upper",
            )
        else:
            spins = qubo_to_ising(
                conversion.qubo,
                constant=conversion.offset,
                num_variables=conversion.num_variables,
                variable_names=conversion.variable_names,
            )
            problem = IsingProblem(
                num_variables=spins.num_variables,
                variable_names=spins.variable_names,
                linear=spins.linear,
                quadratic=spins.quadratic,
                offset=spins.offset,
            )
    details = {
        "type": "binary_portfolio",
        "representation": representation,
        "source_sense": "MAX"
        if portfolio._objective in {"utility", "moment_utility"}
        else "MIN",
        "weight_per_selected_asset": weight,
        "selection_count": count,
        "objective_range_bound": objective_range,
        "minimum_positive_violation_penalty": 1.0,
        "penalty": penalty,
        "penalty_guarantee": (
            "sufficient_if_feasible"
            if penalty > objective_range
            else "heuristic"
        ),
        "source_degree": max(map(len, objective), default=0),
        "encoded_degree": max(map(len, polynomial), default=0),
        "auxiliary_variables": 0
        if conversion is None
        else len(conversion.auxiliary_products),
        "spin_convention": "s = 2*x - 1",
        "discretization": None,
        "quadratization": []
        if conversion is None
        else conversion.transformations,
        "quadratization_strength": (
            None
            if quadratization_strength is None
            else scalar(quadratization_strength, "quadratization_strength")
        ),
    }
    return PortfolioEncoding(
        portfolio,
        problem,
        names,
        objective,
        violations,
        details,
        conversion,
        perf_counter() - started,
    )
