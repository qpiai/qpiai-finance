"""Quoted reinsurance choices, joint loss states and financial mandates."""

from collections.abc import Mapping

import numpy as np
import pandas as pd
from scipy import sparse

from .._serialization import portable
from .._validation import confidence as checked_confidence
from .._validation import (
    copy_index,
    identifiers,
    matrix,
    matrix_input,
    numeric,
    same_labels,
    scalar,
    vector,
)
from .._validation import (
    probabilities as checked_probabilities,
)
from ..cashflows import _currency, _date


class ReinsuranceModel:
    """Select quoted contracts/programs against supplied joint claim scenarios.

    gross_losses has one nonnegative amount per scenario; recoveries has
    scenario rows and quoted-contract columns, with nonnegative contractual
    receipts no larger than gross loss. premiums are nonnegative fixed
    amounts paid when selected. All monetary inputs use one currency and
    consistent horizon/valuation basis. No pricing or discounting is inferred.

    recovery_composition must be explicit: 'exclusive' permits at most one
    quoted alternative (a column may be a complete jointly valued program).
    'additive' declares that the supplied contract recoveries AND contingent
    costs may validly be added for every permitted selection. Standalone
    overlapping payouts cannot establish that condition. A gross-loss cap
    is enforced, but cannot by itself validate contractual composition.

    Explicit probabilities define a distribution. Omit them for stress
    cases and choose minimize_premium with the required hard mandates.
    Expected-cost/tail objectives require probabilities. Default objective
    minimizes expected retained claims plus premium and contingent charges.
    """

    _needs_external = False

    def __init__(
        self,
        gross_losses,
        recoveries,
        premiums,
        *,
        recovery_composition,
        currency,
        horizon,
        as_of,
        probabilities=None,
        scenario_ids=None,
        contract_ids=None,
    ):
        if recovery_composition not in {"exclusive", "additive"}:
            raise ValueError(
                "recovery_composition must be 'exclusive' or 'additive'"
            )
        if isinstance(gross_losses, Mapping):
            gross_losses = pd.Series(gross_losses)
        if scenario_ids is None:
            scenario_ids = (
                gross_losses.index
                if isinstance(gross_losses, pd.Series)
                else range(len(gross_losses))
            )
        self._scenarios = identifiers(scenario_ids, "scenario_ids")
        self._gross = vector(gross_losses, self._scenarios, "gross_losses")
        if np.any(self._gross < 0):
            raise ValueError("gross_losses must be nonnegative")
        recoveries = matrix_input(recoveries)
        if len(np.shape(recoveries)) != 2:
            raise ValueError(
                "recoveries must have scenario rows and contract columns"
            )
        if contract_ids is None:
            contract_ids = (
                recoveries.columns
                if isinstance(recoveries, pd.DataFrame)
                else range(np.shape(recoveries)[1])
            )
        supplied = pd.Index(contract_ids, tupleize_cols=False)
        self._ids = (
            identifiers(supplied, "contract_ids")
            if len(supplied)
            else supplied.copy()
        )
        if len(self._ids):
            self._recoveries = matrix(
                recoveries, self._scenarios, self._ids, "recoveries"
            )
        else:
            if isinstance(recoveries, pd.DataFrame):
                same_labels(
                    recoveries.index, self._scenarios, "recovery scenarios"
                )
                recoveries = recoveries.reindex(self._scenarios).to_numpy(
                    dtype=float
                )
            self._recoveries = numeric(
                recoveries.toarray()
                if sparse.issparse(recoveries)
                else recoveries,
                "recoveries",
                ndim=2,
            )
            if self._recoveries.shape != (len(self._scenarios), 0):
                raise ValueError(
                    "recoveries must match scenarios and contract_ids"
                )
        entries = sparse.coo_matrix(self._recoveries)
        if np.any(entries.data < 0) or np.any(
            entries.data > self._gross[entries.row]
        ):
            raise ValueError(
                "contractual recoveries must lie between zero and gross loss"
            )
        self._premiums = self._contract_vector(premiums, "premiums")
        if np.any(self._premiums < 0):
            raise ValueError("premiums must be nonnegative")
        self._probabilities = (
            None
            if probabilities is None
            else checked_probabilities(probabilities, self._scenarios)
        )
        self._composition = recovery_composition
        self._currency = _currency(currency)
        self._as_of = _date(as_of, "as_of")
        if not isinstance(horizon, str) or not horizon.strip():
            raise ValueError(
                "horizon must describe the common insurance horizon"
            )
        self._horizon = horizon
        self._recoverability = 1.0
        self._charges = sparse.csr_matrix(self._recoveries.shape)
        self._lower, self._upper = (
            np.zeros(len(self._ids)),
            np.ones(len(self._ids)),
        )
        self._count = (0, len(self._ids))
        self._premium_limit = np.inf
        self._retained_limit = np.full(len(self._scenarios), np.inf)
        self._total_limit = self._retained_limit.copy()
        self._tail_limits = {}
        self._counterparty_limits = []
        self._exclusive_groups = []
        self._surplus = self._surplus_minimum = None
        self._objective = "reinsurance_cost"
        self._tail_weight = 0.0
        self._confidence = 0.95

    def _contract_vector(self, values, name, *, broadcast=False):
        if len(self._ids):
            return vector(values, self._ids, name, broadcast=broadcast)
        if broadcast and np.ndim(values) == 0:
            scalar(values, name)
            return np.zeros(0)
        if isinstance(values, (Mapping, pd.Series)) and len(values) == 0:
            return np.zeros(0)
        array = numeric(values, name, ndim=1)
        if array.shape != (0,):
            raise ValueError(
                f"{name} must be empty when no contracts are quoted"
            )
        return array

    @property
    def contract_ids(self):
        return copy_index(self._ids)

    @property
    def scenario_ids(self):
        return copy_index(self._scenarios)

    @property
    def currency(self):
        return self._currency

    @property
    def _objective_unit(self):
        return self._currency

    @property
    def _mixed_integer(self):
        return len(self._ids) > 0

    @property
    def _problem_class(self):
        return "MILP" if self._mixed_integer else "LP"

    def _require_distribution(self):
        if self._probabilities is None:
            raise ValueError(
                "expected values and tail risk require explicit probabilities"
            )

    def _check(self):
        if self._objective != "reinsurance_premium" or self._tail_limits:
            self._require_distribution()

    def minimize_expected_cost(self, *, tail_weight=0.0, confidence=0.95):
        """Minimize (1-w)*mean(total cost) + w*ES(total cost), w in [0,1].

        Scenario total cost = gross claims - collectible recoveries +
        selected fixed premiums + selected contingent charges. Mixing mean
        and tail with weights summing to one charges fixed premiums once.
        Hard risk/surplus/premium mandates remain active.
        """
        self._require_distribution()
        weight = scalar(tail_weight, "tail_weight", minimum=0, maximum=1)
        beta = checked_confidence(confidence)
        self._objective, self._tail_weight, self._confidence = (
            "reinsurance_cost",
            weight,
            beta,
        )
        return self

    def minimize_expected_shortfall(self, *, confidence=0.95):
        """Minimize upper-tail scenario total cost, with fixed premium once."""
        return self.minimize_expected_cost(
            tail_weight=1, confidence=confidence
        )

    def minimize_premium(self):
        """Minimize quoted fixed premiums under all original hard mandates.

        This objective needs no probabilities. Contingent costs remain
        in total-cost and surplus constraints, but not this base premium.
        Without coverage/risk mandates the empty selection may be cheapest.
        """
        self._objective = "reinsurance_premium"
        return self

    def set_recoverability(self, factors):
        """Apply supplied scenario-by-contract collectible fractions in [0,1].

        A scalar applies everywhere. Default one treats supplied recoveries
        as collectible. Do not adjust already net recoveries twice. Joint
        factors may encode counterparty/default/basis stresses; this method
        estimates none of them and does not certify regulatory treatment.
        """
        if np.ndim(factors) == 0:
            prepared = scalar(factors, "recoverability", minimum=0, maximum=1)
        else:
            prepared = matrix(
                factors, self._scenarios, self._ids, "recoverability"
            )
            data = prepared.data if sparse.issparse(prepared) else prepared
            if np.any(data < 0) or np.any(data > 1):
                raise ValueError("recoverability must lie in [0, 1]")
        self._recoverability = prepared
        return self

    def set_contingent_costs(self, costs):
        """Supply nonnegative scenario-by-contract charges paid if selected.

        Examples include supplied reinstatement premiums or settlement costs.
        They are additional to quoted fixed premiums; no charge formula,
        aggregate trigger or contract interaction is inferred.
        """
        prepared = matrix(
            costs, self._scenarios, self._ids, "contingent costs"
        )
        data = prepared.data if sparse.issparse(prepared) else prepared
        if np.any(data < 0):
            raise ValueError("contingent costs must be nonnegative")
        self._charges = prepared
        return self

    def limit_selections(self, *, lower=0.0, upper=1.0):
        """Fix eligibility/required choices with binary bounds per contract."""
        low = self._contract_vector(lower, "lower selections", broadcast=True)
        high = self._contract_vector(upper, "upper selections", broadcast=True)
        if (
            not np.isin(low, [0, 1]).all()
            or not np.isin(high, [0, 1]).all()
            or np.any(low > high)
        ):
            raise ValueError(
                "selection bounds must be zero or one, with lower <= upper"
            )
        self._lower, self._upper = low, high
        return self

    def limit_contract_count(self, *, minimum=0, maximum=None):
        """Bound selected quoted alternatives; exclusivity remains hard."""
        low = scalar(
            minimum, "minimum count", minimum=0, maximum=len(self._ids)
        )
        high = (
            len(self._ids)
            if maximum is None
            else scalar(
                maximum, "maximum count", minimum=0, maximum=len(self._ids)
            )
        )
        if int(low) != low or int(high) != high or low > high:
            raise ValueError(
                "contract counts must be integers with minimum <= maximum"
            )
        self._count = (int(low), int(high))
        return self

    def add_exclusive_group(self, contract_ids):
        """Allow at most one of these quoted alternatives in the program.

        Use for competing quotes, layer/retention alternatives or other
        supplied mutual exclusions. Groups may overlap; every call adds a
        hard rule. Remaining allowed selections still need the declared
        valid recovery composition, not inferred payout compatibility.
        """
        if isinstance(contract_ids, (str, bytes)):
            raise ValueError("supply a sequence of contract IDs")
        ids = identifiers(contract_ids, "exclusive contract IDs")
        if not ids.isin(self._ids).all():
            raise ValueError(
                "exclusive groups must reference quoted contracts"
            )
        self._exclusive_groups.append(ids)
        return self

    def limit_premium(self, maximum):
        """Bound quoted fixed premiums, excluding contingent charges."""
        self._premium_limit = scalar(maximum, "maximum premium", minimum=0)
        return self

    def limit_retained_loss(self, maximum):
        """Bound claims net of collectible recoveries per scenario."""
        values = vector(
            maximum, self._scenarios, "maximum retained loss", broadcast=True
        )
        if np.any(values < 0):
            raise ValueError("retained loss limits must be nonnegative")
        self._retained_limit = values
        return self

    def limit_total_cost(self, maximum):
        """Bound retained claims plus premiums and charges per case."""
        values = vector(
            maximum, self._scenarios, "maximum total cost", broadcast=True
        )
        if np.any(values < 0):
            raise ValueError("total cost limits must be nonnegative")
        self._total_limit = values
        return self

    def limit_expected_shortfall(
        self, maximum, *, confidence=0.95, measure="total_cost"
    ):
        """Set a hard ES cap for (measure, confidence), preserving other caps.

        measure is 'total_cost' or 'retained_loss'. Explicit probabilities
        are required; fractional mass at the VaR boundary is included.
        """
        self._require_distribution()
        if measure not in {"total_cost", "retained_loss"}:
            raise ValueError("measure must be 'total_cost' or 'retained_loss'")
        beta = checked_confidence(confidence)
        value = scalar(maximum, "maximum expected shortfall", minimum=0)
        self._tail_limits[(measure, beta)] = value
        return self

    def limit_counterparty_exposure(
        self, coefficients, *, maximum, exposure_ids=None
    ):
        """Bound supplied additive counterparty exposures per selected quote.

        Rows may overlap. Coefficients and bounds are in the model currency;
        the caller supplies the exposure basis (for example covered limit),
        not an inferred proxy for default risk or regulatory capital.
        """
        coefficients = matrix_input(coefficients)
        if len(np.shape(coefficients)) != 2:
            raise ValueError(
                "counterparty coefficients must be a row-by-contract matrix"
            )
        if exposure_ids is None:
            exposure_ids = (
                coefficients.index
                if isinstance(coefficients, pd.DataFrame)
                else range(np.shape(coefficients)[0])
            )
        ids = identifiers(exposure_ids, "exposure_ids")
        prepared = matrix(
            coefficients, ids, self._ids, "counterparty coefficients"
        )
        data = prepared.data if sparse.issparse(prepared) else prepared
        upper = vector(maximum, ids, "maximum exposure", broadcast=True)
        if np.any(data < 0) or np.any(upper < 0):
            raise ValueError(
                "counterparty exposures and limits must be nonnegative"
            )
        self._counterparty_limits.append((ids, prepared, upper))
        return self

    def set_surplus_before_claims(self, surplus):
        """Supply scenario assets minus OTHER liabilities before this plan.

        This state must EXCLUDE the modeled gross claims, recoveries, quoted
        premiums and contingent costs; they are applied exactly once.
        It may include supplied investment outcomes and other obligations.
        No asset repricing or regulatory capital formula is inferred.
        """
        self._surplus = vector(
            surplus, self._scenarios, "surplus before claims", broadcast=True
        )
        return self

    def require_surplus(self, minimum=0.0):
        """Require scenario surplus_after = supplied_before - total_cost."""
        if self._surplus is None:
            raise ValueError("supply surplus before claims first")
        self._surplus_minimum = vector(
            minimum, self._scenarios, "minimum surplus", broadcast=True
        )
        return self

    def _specification(self):
        return portable(
            {
                "model": "ReinsuranceModel",
                "currency": self._currency,
                "as_of": self._as_of,
                "horizon": self._horizon,
                "scenario_ids": self._scenarios,
                "contract_ids": self._ids,
                "gross_losses": self._gross,
                "recoveries": self._recoveries,
                "premiums": self._premiums,
                "probabilities": self._probabilities,
                "recovery_composition": self._composition,
                "recoverability": self._recoverability,
                "contingent_costs": self._charges,
                "lower": self._lower,
                "upper": self._upper,
                "contract_count": self._count,
                "premium_limit": self._premium_limit,
                "retained_loss_limits": self._retained_limit,
                "total_cost_limits": self._total_limit,
                "expected_shortfall_limits": [
                    {"measure": key[0], "confidence": key[1], "maximum": value}
                    for key, value in self._tail_limits.items()
                ],
                "counterparty_limits": self._counterparty_limits,
                "exclusive_groups": self._exclusive_groups,
                "surplus_before_claims": self._surplus,
                "minimum_surplus": self._surplus_minimum,
                "objective": self._objective,
                "tail_weight": self._tail_weight,
                "confidence": self._confidence,
            }
        )

    def to_matrix(self):
        """Return detached sparse Opt LP/MILP data in source quantities.

        selection_i is the binary choice for contract_ids[i]. retained_s and
        total_cost_s are model currency for scenario_ids[s]. Tail threshold
        and excess variables are auxiliary currency quantities, not claims.
        """
        from ._compile import matrix_problem

        return matrix_problem(self)

    def _financial_variables(self, variables):
        return {
            "selections": pd.Series(
                [variables[f"selection_{i}"] for i in range(len(self._ids))],
                index=copy_index(self._ids),
                name="selection",
                dtype=object,
            ),
            "premium": variables["premium"],
            "retained_losses": pd.Series(
                [
                    variables[f"retained_{s}"]
                    for s in range(len(self._scenarios))
                ],
                index=copy_index(self._scenarios),
                name="retained_loss",
                dtype=object,
            ),
            "total_costs": pd.Series(
                [
                    variables[f"total_cost_{s}"]
                    for s in range(len(self._scenarios))
                ],
                index=copy_index(self._scenarios),
                name="total_cost",
                dtype=object,
            ),
        }

    def to_model(self, *, return_variables=False):
        """Return the equivalent detached algebraic Opt LP/MILP.

        return_variables=True also returns contract-indexed selections,
        premium and scenario-indexed retained_losses/total_costs in the
        model's currency. Selections remain binary contract choices.
        """
        from .._solvers._expressions import export_model
        from ._compile import compile_model

        return export_model(compile_model(self), self, return_variables)

    def _compile_opt(self, *, mode):
        return self.to_model() if mode == "platform" else self.to_matrix()

    def _compile_cvxpy(self):
        from .._solvers.cvxpy import linear_problem

        return linear_problem(self.to_matrix())

    def to_cvxpy(self):
        """Return a CVXPY problem and financial expressions.

        selections uses contract IDs; premium, retained_losses and
        total_costs use the model's currency and supplied scenario IDs.
        """
        problem, variables = self._compile_cvxpy()
        return problem, self._financial_variables(variables)

    def evaluate(self, selections, *, tolerance=1e-7):
        """Rebuild recoveries, retained/total losses, surplus and mandates.

        Compare original amounts before rounding report columns to float64.
        Constraint residuals can retain differences hidden by rounded totals.
        """
        from ._evaluation import evaluate

        try:
            with np.errstate(over="raise", invalid="raise", divide="raise"):
                return evaluate(self, selections, tolerance=tolerance)
        except (FloatingPointError, OverflowError) as error:
            raise ValueError(
                "reinsurance quantities or values exceed float64 range"
            ) from error

    def _evaluate_solution(self, solution, *, tolerance):
        from ._evaluation import evaluate_solution

        try:
            with np.errstate(over="raise", invalid="raise", divide="raise"):
                return evaluate_solution(self, solution, tolerance=tolerance)
        except (FloatingPointError, OverflowError) as error:
            raise ValueError(
                "reinsurance quantities or values exceed float64 range"
            ) from error
