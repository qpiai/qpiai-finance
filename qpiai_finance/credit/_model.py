"""Facility amounts, economic contributions and credit policy constraints."""

from collections.abc import Mapping
from copy import deepcopy
from fractions import Fraction

import numpy as np
import pandas as pd
from scipy import sparse

from .._serialization import portable
from .._validation import (
    concentration_groups,
    copy_index,
    identifiers,
    matrix,
    matrix_input,
    same_labels,
    scalar,
    vector,
)
from .._validation import (
    confidence as checked_confidence,
)
from .._validation import lot_sizes as checked_lot_sizes
from ..cashflows import _currency, _date
from ..scenarios import Scenarios


def _default_loss_rates(probabilities, severities, exposures):
    """Expected loss rates from validated PD, conditional LGD and EAD."""
    return np.fromiter(
        (
            Fraction(probability) * Fraction(severity) * Fraction(exposure)
            for probability, severity, exposure in zip(
                probabilities, severities, exposures
            )
        ),
        dtype=object,
    )


class CreditAllocationModel:
    """Allocate nonnegative final facility amounts in one currency/horizon.

    All rates and resource coefficients are per currency unit of allocated
    principal or commitment. income_rates are expected income before the
    separately supplied funding_costs and expected_loss_rates. Capital is
    supplied capital_requirements @ allocation; funding is supplied
    funding_requirements @ allocation. Neither is inferred from expected
    loss. Capacity is a finite approved limit, with zero meaning ineligible.

    current_allocations describe the existing book. Decisions are final
    amounts; increases/reductions and their supplied costs are reported
    separately. Funding limits concern final resource use, not origination
    cash or sale proceeds. This is a single-horizon allocation model, not
    an underwriting, regulatory-capital or contractual cash-flow engine.
    """

    _objective = "risk_adjusted_income"
    _needs_external = False

    def __init__(
        self,
        income_rates,
        *,
        funding_costs,
        expected_loss_rates,
        capital_requirements,
        capacity,
        currency,
        horizon,
        as_of,
        facility_ids=None,
        funding_requirements=1.0,
        exposure_per_unit=1.0,
        current_allocations=0.0,
    ):
        if isinstance(income_rates, Mapping):
            income_rates = pd.Series(income_rates)
        if facility_ids is None:
            facility_ids = (
                income_rates.index
                if isinstance(income_rates, pd.Series)
                else range(len(income_rates))
            )
        self._ids = identifiers(facility_ids, "facility_ids")
        self._income = vector(income_rates, self._ids, "income_rates")
        self._funding_cost = vector(
            funding_costs, self._ids, "funding_costs", broadcast=True
        )
        self._expected_loss = self._nonnegative(
            expected_loss_rates, "expected_loss_rates"
        )
        self._capital = self._nonnegative(
            capital_requirements, "capital_requirements"
        )
        self._funding = self._nonnegative(
            funding_requirements, "funding_requirements"
        )
        self._ead = self._nonnegative(exposure_per_unit, "exposure_per_unit")
        self._capacity = self._nonnegative(capacity, "capacity")
        self._current = self._nonnegative(
            current_allocations, "current_allocations"
        )
        self._currency = _currency(currency)
        self._as_of = _date(as_of, "as_of")
        if not isinstance(horizon, str) or not horizon.strip():
            raise ValueError("horizon must describe the common credit horizon")
        self._horizon = horizon
        self._lower = np.zeros(len(self._ids))
        self._upper = self._capacity.copy()
        self._funding_limit = self._capital_limit = np.inf
        self._capital_charge = self._risk_aversion = 0.0
        self._confidence = 0.95
        self._lots = self._selection = self._default_risk = None
        self._increase_cost = np.zeros(len(self._ids))
        self._decrease_cost = np.zeros(len(self._ids))
        self._exposures = []
        self._concentrations = []
        self._scenarios = self._scenario_limit = self._tail_limit = None

    def _nonnegative(self, values, name):
        result = vector(values, self._ids, name, broadcast=True)
        if np.any(result < 0):
            raise ValueError(f"{name} must be nonnegative")
        return result

    def _income_margins(self):
        """Original net and capital-adjusted rates before book-change costs."""
        net = np.fromiter(
            (
                Fraction(income) - Fraction(funding) - Fraction(loss)
                for income, funding, loss in zip(
                    self._income, self._funding_cost, self._loss_rates()
                )
            ),
            dtype=object,
        )
        contribution = np.fromiter(
            (
                margin - Fraction(self._capital_charge) * Fraction(capital)
                for margin, capital in zip(net, self._capital)
            ),
            dtype=object,
        )
        return net, contribution

    def _loss_rates(self):
        return (
            self._expected_loss
            if self._default_risk is None
            else _default_loss_rates(*self._default_risk)
        )

    @property
    def facility_ids(self):
        return copy_index(self._ids)

    @property
    def currency(self):
        return self._currency

    @property
    def _objective_unit(self):
        return self._currency

    @property
    def _mixed_integer(self):
        return self._lots is not None or self._selection is not None

    @property
    def _problem_class(self):
        return "MILP" if self._mixed_integer else "LP"

    def maximize_risk_adjusted_income(
        self, *, capital_charge=0.0, risk_aversion=0.0, confidence=0.95
    ):
        """Maximize net income minus capital charge and an explicit ES penalty.

        Net income subtracts supplied funding, expected loss and change
        costs once. capital_charge multiplies capital used over the common
        horizon. risk_aversion multiplies upper-loss expected shortfall of
        supplied joint scenarios; this is an additional risk preference,
        not another estimate of mean loss. Hard risk limits remain active.
        """
        charge = scalar(capital_charge, "capital_charge", minimum=0)
        aversion = scalar(risk_aversion, "risk_aversion", minimum=0)
        beta = checked_confidence(confidence)
        if aversion > 0:
            self._require_distribution()
        self._capital_charge, self._risk_aversion = charge, aversion
        self._confidence = beta
        return self

    def set_default_risk(
        self, probability_of_default, loss_given_default, exposure_at_default
    ):
        """Replace expected loss rates with supplied PD * LGD * EAD per unit.

        PD and conditional mean LGD must be in [0, 1]; EAD is currency per
        allocated currency unit. Inputs refer to the declared horizon.
        This simplified expected loss does not estimate correlation, tail
        risk, capital, accounting provisions or jurisdictional compliance.
        It does not change the separate exposure_per_unit policy basis.
        The supplied factors are retained through financial loss evaluation
        and allocation-unit scaling.
        """
        pd_rate = self._nonnegative(
            probability_of_default, "probability_of_default"
        )
        lgd = self._nonnegative(loss_given_default, "loss_given_default")
        ead = self._nonnegative(exposure_at_default, "exposure_at_default")
        if np.any(pd_rate > 1) or np.any(lgd > 1):
            raise ValueError("PD and LGD must lie in [0, 1]")
        losses = np.asarray(
            _default_loss_rates(pd_rate, lgd, ead), dtype=float
        )
        self._default_risk = (pd_rate, lgd, ead)
        self._expected_loss = losses
        return self

    def limit_allocations(self, *, lower=0.0, upper=None):
        """Bound final amounts within approved capacities."""
        low = self._nonnegative(lower, "lower allocations")
        high = (
            self._capacity.copy()
            if upper is None
            else self._nonnegative(upper, "upper allocations")
        )
        if np.any(low > high) or np.any(high > self._capacity):
            raise ValueError("amounts require 0 <= lower <= upper <= capacity")
        self._lower, self._upper = low, high
        return self

    def limit_funding(self, maximum):
        """Bound total final funding_requirements @ allocations in currency."""
        self._funding_limit = scalar(maximum, "maximum funding", minimum=0)
        return self

    def limit_capital(self, maximum):
        """Bound supplied additive capital use in the declared currency."""
        self._capital_limit = scalar(maximum, "maximum capital", minimum=0)
        return self

    def allocate_in_lots(self, lot_sizes):
        """Restrict final facility amounts to positive currency-sized lots."""
        self._lots = checked_lot_sizes(lot_sizes, self._ids)
        return self

    def select_facilities(self, *, minimum, maximum_count=None):
        """Require zero or at least minimum per active facility; cap count.

        Minimum amounts must be positive. Zero approved capacity continues
        to forbid allocation even when a positive minimum is supplied.
        """
        minimum = self._nonnegative(minimum, "minimum allocation")
        if np.any(minimum == 0):
            raise ValueError("minimum allocations must be positive")
        count = (
            len(self._ids)
            if maximum_count is None
            else scalar(
                maximum_count,
                "maximum_count",
                minimum=0,
                maximum=len(self._ids),
            )
        )
        if int(count) != count:
            raise ValueError("maximum_count must be an integer")
        self._selection = (minimum, int(count))
        return self

    def set_transaction_costs(self, *, increase=0.0, decrease=0.0):
        """Charge supplied currency per unit of increase or reduction.

        Reductions of the existing book are proposed sales/runoffs under
        supplied economic costs. No sale price, settlement cash or legal
        permission is inferred. Bounds encode permitted final amounts.
        """
        buy = self._nonnegative(increase, "increase costs")
        sell = self._nonnegative(decrease, "decrease costs")
        self._increase_cost, self._decrease_cost = buy, sell
        return self

    def limit_exposures(
        self, coefficients, *, upper, lower=0.0, exposure_ids=None
    ):
        """Add linear linked-party or policy exposure bounds in currency.

        Rows may overlap. Coefficients are nonnegative exposure currency
        per allocated currency unit, explicitly supplied rather than
        inferred from borrower identity. Each call adds a constraint block.
        """
        coefficients = matrix_input(coefficients)
        if len(np.shape(coefficients)) != 2:
            raise ValueError(
                "coefficients must be an exposure by facility matrix"
            )
        if exposure_ids is None:
            exposure_ids = (
                coefficients.index
                if isinstance(coefficients, pd.DataFrame)
                else range(np.shape(coefficients)[0])
            )
        ids = identifiers(exposure_ids, "exposure_ids")
        values = matrix(coefficients, ids, self._ids, "exposure coefficients")
        data = values.data if sparse.issparse(values) else values
        if np.any(data < 0):
            raise ValueError("exposure coefficients must be nonnegative")
        low = vector(lower, ids, "lower exposure", broadcast=True)
        high = vector(upper, ids, "upper exposure", broadcast=True)
        if np.any(low < 0) or np.any(low > high):
            raise ValueError("exposures require 0 <= lower <= upper")
        self._exposures.append((ids, values, low, high))
        return self

    def limit_concentration(self, groups, *, maximum_share):
        """Cap each group's share of total exposure_per_unit @ allocations.

        groups assigns one supplied sector/region/party label per facility.
        Each call adds a classification. Overlapping connected-party limits
        use limit_exposures instead. A zero-total book has zero group
        amounts and satisfies the constraints without a fabricated ratio.
        """
        self._concentrations.append(
            concentration_groups(groups, self._ids, maximum_share)
        )
        return self

    def set_loss_scenarios(self, scenarios):
        """Supply joint nonnegative credit losses per allocated currency unit.

        Requires Scenarios with unit='loss_fraction' and the same horizon.
        Explicit probabilities are needed for ES, but not per-case stress
        limits. Scenario mean loss is reported separately and never silently
        replaces expected_loss_rates. Replacements preserve per-case limits
        by scenario ID; changing those IDs with limits configured raises.
        Configured ES limits/preferences must remain meaningful.
        """
        if not isinstance(scenarios, Scenarios):
            raise TypeError("scenarios must be a Scenarios object")
        if (
            scenarios.unit != "loss_fraction"
            or scenarios.horizon != self._horizon
        ):
            raise ValueError(
                "loss scenarios require loss_fraction and the same horizon"
            )
        same_labels(scenarios._assets, self._ids, "scenario facilities")
        prepared = deepcopy(scenarios)
        order = prepared._assets.get_indexer(self._ids)
        prepared._values = prepared._values[:, order]
        prepared._assets = copy_index(self._ids)
        values = prepared._values
        data = values.data if sparse.issparse(values) else values
        if np.any(data < 0):
            raise ValueError("credit loss scenarios must be nonnegative")
        if prepared._probabilities is None and (
            self._risk_aversion > 0 or self._tail_limit is not None
        ):
            raise ValueError("configured ES requires explicit probabilities")
        if self._scenario_limit is not None:
            same_labels(
                prepared._ids, self._scenarios._ids, "limited scenario IDs"
            )
            order = prepared._ids.get_indexer(self._scenarios._ids)
            prepared._values = prepared._values[order, :]
            if prepared._probabilities is not None:
                prepared._probabilities = prepared._probabilities[order]
            prepared._ids = copy_index(self._scenarios._ids)
        self._scenarios = prepared
        return self

    def _require_distribution(self):
        if self._scenarios is None or self._scenarios._probabilities is None:
            raise ValueError(
                "expected shortfall requires explicit loss probabilities"
            )

    def limit_scenario_loss(self, maximum):
        """Bound each scenario's loss in currency, including stress cases."""
        if self._scenarios is None:
            raise ValueError(
                "supply loss scenarios before setting loss limits"
            )
        limits = vector(
            maximum,
            self._scenarios._ids,
            "maximum scenario loss",
            broadcast=True,
        )
        if np.any(limits < 0):
            raise ValueError("scenario loss limits must be nonnegative")
        self._scenario_limit = limits
        return self

    def limit_expected_shortfall(self, maximum, *, confidence=0.95):
        """Bound upper-tail loss in currency, including fractional VaR mass.

        This hard constraint has its own confidence, independent of any
        objective risk preference. It does not impose a per-scenario cap.
        """
        self._require_distribution()
        limit = scalar(maximum, "maximum expected shortfall", minimum=0)
        beta = checked_confidence(confidence)
        self._tail_limit = (limit, beta)
        return self

    def _specification(self):
        scenarios = self._scenarios
        return portable(
            {
                "model": "CreditAllocationModel",
                "facility_ids": self._ids,
                "currency": self._currency,
                "as_of": self._as_of,
                "horizon": self._horizon,
                "income_rates": self._income,
                "funding_costs": self._funding_cost,
                "expected_loss_rates": self._expected_loss,
                "default_risk": self._default_risk,
                "capital_requirements": self._capital,
                "funding_requirements": self._funding,
                "exposure_per_unit": self._ead,
                "capacity": self._capacity,
                "current_allocations": self._current,
                "lower": self._lower,
                "upper": self._upper,
                "funding_limit": self._funding_limit,
                "capital_limit": self._capital_limit,
                "capital_charge": self._capital_charge,
                "risk_aversion": self._risk_aversion,
                "confidence": self._confidence,
                "lots": self._lots,
                "selection": self._selection,
                "increase_cost": self._increase_cost,
                "decrease_cost": self._decrease_cost,
                "exposure_limits": self._exposures,
                "concentrations": self._concentrations,
                "loss_scenarios": None
                if scenarios is None
                else {
                    "values": scenarios._values,
                    "probabilities": scenarios._probabilities,
                    "scenario_ids": scenarios._ids,
                    "origin": scenarios.origin,
                    **(
                        {"metadata": scenarios.metadata}
                        if scenarios._metadata
                        else {}
                    ),
                },
                "scenario_limits": self._scenario_limit,
                "expected_shortfall_limit": self._tail_limit,
            }
        )

    def _financial_variables(self, variables):
        scales = np.ones(len(self._ids)) if self._lots is None else self._lots
        amounts = pd.Series(
            [
                float(scale) * variables[f"allocation_{i}"]
                for i, scale in enumerate(scales)
            ],
            index=copy_index(self._ids),
            name="allocated_amount",
            dtype=object,
        )
        return {
            "allocations": amounts,
            "allocation_changes": (amounts - self._current).rename("change"),
        }

    def to_model(self, *, return_variables=False):
        """Return a detached Opt LP/MILP.

        return_variables=True also returns a mapping of facility-indexed
        allocations and allocation_changes in actual currency amounts.
        Editing the export does not change this financial specification.
        """
        from .._solvers._expressions import export_model
        from ._compile import compile_model

        return export_model(compile_model(self), self, return_variables)

    def _compile_cvxpy(self):
        from .._solvers.cvxpy import linear_problem

        return linear_problem(self.to_model())

    def to_cvxpy(self):
        """Return a CVXPY problem and facility-indexed financial expressions.

        allocations and allocation_changes use actual currency amounts,
        including when the program's integer variables count lots.
        """
        problem, variables = self._compile_cvxpy()
        return problem, self._financial_variables(variables)

    def evaluate(self, allocations, *, tolerance=1e-7):
        """Check source amounts, income, losses and policy limits."""
        from ._evaluation import evaluate

        try:
            return evaluate(self, allocations, tolerance=tolerance)
        except (FloatingPointError, OverflowError) as error:
            raise ValueError(
                "credit calculations exceed float64 range"
            ) from error

    def _evaluate_solution(self, solution, *, tolerance):
        from ._evaluation import evaluate_solution

        return evaluate_solution(self, solution, tolerance=tolerance)
