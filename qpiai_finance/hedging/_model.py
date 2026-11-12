"""Source exposures, scenario P&L and controls for hedge quantities."""

from copy import deepcopy

import numpy as np
import pandas as pd
from scipy import sparse

from .._serialization import portable
from .._validation import confidence as checked_confidence
from .._validation import (
    copy_index,
    covariance,
    identifiers,
    matrix,
    matrix_input,
    scalar,
    unit_labels,
    vector,
)
from .._validation import lot_sizes as checked_lot_sizes
from ..cashflows import _currency, _date
from ..scenarios import Scenarios


class HedgeModel:
    """Adjust signed hedges using supplied sensitivities or scenario P&L.

    sensitivities has risk rows and instrument columns, per traded unit.
    current_exposures includes existing hedge positions already; supplied
    current_positions is used only for post-trade position accounting.
    risk_units declares each row's physical units. Sensitivity inputs initially
    match zero exposure exactly at minimum transaction cost. Sensitivities
    are local risk approximations, not scenario repricing or payoff models.

    Alternatively supply current_pnl and pnl_scenarios without sensitivities.
    Scenarios contain per-unit P&L changes, unit='pnl_per_unit', in currency
    over their declared horizon. current_pnl includes existing hedges already.
    Costs are deducted once using cost_factors (default one, no carrying).
    This mode initially minimizes worst-case loss. Either input mode may
    also use scenario loss limits; data setters do not change objectives.
    """

    def __init__(
        self,
        current_exposures=None,
        sensitivities=None,
        *,
        risk_units=None,
        currency,
        as_of,
        instrument_ids=None,
        risk_ids=None,
        current_positions=0.0,
        current_pnl=None,
        pnl_scenarios=None,
        cost_factors=None,
    ):
        if pnl_scenarios is not None and type(pnl_scenarios) is not Scenarios:
            raise TypeError("pnl_scenarios must be Scenarios")
        has_sensitivities = (
            current_exposures is not None or sensitivities is not None
        )
        if has_sensitivities:
            if current_exposures is None or sensitivities is None:
                raise ValueError(
                    "supply both current_exposures and sensitivities"
                )
            if risk_units is None:
                raise ValueError("risk_units is required for sensitivities")
            sensitivities = matrix_input(sensitivities)
            if len(np.shape(sensitivities)) != 2:
                raise ValueError(
                    "sensitivities require risk rows and instrument columns"
                )
            if risk_ids is None:
                risk_ids = (
                    sensitivities.index
                    if isinstance(sensitivities, pd.DataFrame)
                    else pd.Series(current_exposures).index
                )
            if instrument_ids is None:
                instrument_ids = (
                    sensitivities.columns
                    if isinstance(sensitivities, pd.DataFrame)
                    else range(np.shape(sensitivities)[1])
                )
            self._risks = identifiers(risk_ids, "risk_ids")
            self._ids = identifiers(instrument_ids, "instrument_ids")
            self._exposure = vector(
                current_exposures, self._risks, "current_exposures"
            )
            self._sensitivities = matrix(
                sensitivities, self._risks, self._ids, "sensitivities"
            )
            self._units = unit_labels(risk_units, self._risks)
        else:
            if pnl_scenarios is None:
                raise ValueError(
                    "supply sensitivity exposures or P&L scenarios"
                )
            if risk_units is not None or risk_ids is not None:
                raise ValueError("risk units/IDs require sensitivity inputs")
            self._ids = identifiers(
                pnl_scenarios.asset_ids
                if instrument_ids is None
                else instrument_ids,
                "instrument_ids",
            )
            self._risks = pd.Index([], dtype=object)
            self._exposure = np.empty(0)
            self._sensitivities = sparse.csr_matrix((0, len(self._ids)))
            self._units = []
        self._currency = _currency(currency)
        self._as_of = _date(as_of, "as_of")
        self._current = vector(
            current_positions, self._ids, "current_positions", broadcast=True
        )
        self._lower = np.full(len(self._ids), -np.inf)
        self._upper = np.full(len(self._ids), np.inf)
        self._position_lower = self._lower.copy()
        self._position_upper = self._upper.copy()
        self._target = np.zeros(len(self._risks))
        self._risk_lower = np.full(len(self._risks), -np.inf)
        self._risk_upper = np.full(len(self._risks), np.inf)
        self._weights = None
        self._objective = (
            "hedge_cost" if has_sensitivities else "hedge_worst_loss"
        )
        self._cost_weight = 1.0
        self._buy_cost = np.zeros(len(self._ids))
        self._sell_cost = np.zeros(len(self._ids))
        self._cash = None
        self._prices = np.zeros(len(self._ids))
        self._bid = self._prices.copy()
        self._ask = self._prices.copy()
        self._lots = None
        self._capital = None
        self._pnl_scenarios = None
        self._current_pnl = self._cost_factors = None
        self._loss_limit = self._es_limit = None
        self._confidence = 0.95
        if pnl_scenarios is not None:
            if current_pnl is None:
                raise ValueError("current_pnl is required with pnl_scenarios")
            self.set_pnl_scenarios(
                pnl_scenarios,
                current_pnl=current_pnl,
                cost_factors=1.0 if cost_factors is None else cost_factors,
            )
        elif current_pnl is not None or cost_factors is not None:
            raise ValueError("current_pnl/cost_factors require pnl_scenarios")

    @property
    def instrument_ids(self):
        return copy_index(self._ids)

    @property
    def risk_ids(self):
        return copy_index(self._risks)

    @property
    def pnl_scenarios(self):
        """Detached per-unit P&L scenarios, or None when not supplied."""
        return deepcopy(self._pnl_scenarios)

    @property
    def current_pnl(self):
        """Detached total existing-book scenario P&L, or None."""
        if self._pnl_scenarios is None:
            return None
        return pd.Series(
            self._current_pnl.copy(),
            index=self._pnl_scenarios.scenario_ids,
            name="current_pnl",
        )

    @property
    def currency(self):
        return self._currency

    @property
    def _objective_unit(self):
        return self._currency

    @property
    def _mixed_integer(self):
        return self._lots is not None

    @property
    def _quadratic(self):
        return self._objective == "hedge_mismatch" and (
            self._weights.nnz > 0
            if sparse.issparse(self._weights)
            else np.any(self._weights != 0)
        )

    @property
    def _needs_external(self):
        return self._mixed_integer and self._quadratic

    @property
    def _problem_class(self):
        return (
            ("MIQP" if self._mixed_integer else "QP")
            if self._quadratic
            else ("MILP" if self._mixed_integer else "LP")
        )

    def match_exposures(self, target=0.0):
        """Match signed target exposures at minimum transaction cost."""
        self._require_sensitivities()
        target = vector(target, self._risks, "target", broadcast=True)
        self._target = target
        self._objective = "hedge_cost"
        return self

    def minimize_mismatch(self, weights, *, target=0.0, cost_weight=1.0):
        """Minimize residual.T @ weights @ residual + cost_weight * costs.

        weights must be a symmetric PSD matrix. Its (i,j) entry is in
        currency/(risk_unit_i*risk_unit_j), so mixed sensitivity units are
        scaled intentionally. No automatic identity weighting is inferred.
        This replaces exact matching with a soft objective; use
        limit_exposures for any hard risk limits that must also hold.
        """
        self._require_sensitivities()
        weights = covariance(weights, self._risks, "mismatch weights")
        target = vector(target, self._risks, "target", broadcast=True)
        cost_weight = scalar(cost_weight, "cost_weight", minimum=0)
        self._weights, self._target = weights, target
        self._cost_weight = cost_weight
        self._objective = "hedge_mismatch"
        return self

    def limit_exposures(self, *, lower, upper):
        """Bound post-hedge risk rows in their declared physical units."""
        self._require_sensitivities()
        low = vector(lower, self._risks, "lower exposures", broadcast=True)
        high = vector(upper, self._risks, "upper exposures", broadcast=True)
        if np.any(low > high):
            raise ValueError("lower exposures must not exceed upper exposures")
        self._risk_lower, self._risk_upper = low, high
        return self

    def _require_sensitivities(self):
        if not len(self._risks):
            raise ValueError("sensitivity exposures were not supplied")

    def set_pnl_scenarios(self, scenarios, *, current_pnl, cost_factors=1.0):
        """Replace supplied repriced P&L per hedge unit and total book P&L.

        scenarios requires unit='pnl_per_unit'; values are mark-to-horizon
        P&L changes including supplied distributions/financing, excluding
        trade costs. current_pnl includes the existing hedge book, aligned
        by case. Terminal payoff alone is not a P&L change. All use currency.
        Positive cost_factors carry upfront fees/spread to the same horizon;
        one explicitly means no carrying. Upfront principal is separate cash
        accounting and is not deducted again from scenario P&L.
        This changes data, not the objective or existing hard case limits.
        """
        from ._scenarios import prepare

        scenarios, baseline, factors, limits = prepare(
            self, scenarios, current_pnl, cost_factors
        )
        self._pnl_scenarios = scenarios
        self._current_pnl, self._cost_factors = baseline, factors
        self._loss_limit = limits
        return self

    def limit_scenario_loss(self, maximum):
        """Cap net loss in every supplied case, including zero-probability.

        Loss is minus (book P&L + hedge-unit P&L - carried trading cost).
        No probabilities are needed for stress limits. Bounds use currency;
        negative bounds require a minimum gain. Limits align by case ID.
        """
        self._require_scenarios()
        values = vector(
            maximum,
            self._pnl_scenarios.scenario_ids,
            "scenario loss limits",
            broadcast=True,
        )
        self._loss_limit = values
        return self

    def limit_expected_shortfall(self, maximum, *, confidence=0.95):
        """Cap net-loss ES using its own confidence and explicit weights."""
        self._require_scenarios(probabilities=True)
        value = scalar(maximum, "maximum expected shortfall")
        level = checked_confidence(confidence)
        self._es_limit = value, level
        return self

    def minimize_expected_shortfall(self, *, confidence=0.95):
        """Minimize net-loss ES, including carried trading cost once.

        Replaces exact sensitivity matching with tail-risk minimization.
        Exposure bounds remain hard; use equal lower/upper exposure limits
        for a mandatory sensitivity target under any objective.
        """
        self._require_scenarios(probabilities=True)
        level = checked_confidence(confidence)
        self._confidence = level
        self._objective = "hedge_expected_shortfall"
        return self

    def minimize_worst_case_loss(self):
        """Minimize maximum net loss across all cases, including stress cases.

        Replaces exact sensitivity matching; hard exposure limits remain.
        Does not require probabilities and does not infer equal weights.
        """
        self._require_scenarios()
        self._objective = "hedge_worst_loss"
        return self

    def _require_scenarios(self, *, probabilities=False):
        if self._pnl_scenarios is None:
            raise ValueError("supply P&L scenarios first")
        if probabilities and self._pnl_scenarios._probabilities is None:
            raise ValueError(
                "expected shortfall requires explicit probabilities"
            )

    def limit_trades(self, *, lower=None, upper=None):
        """Bound signed hedge changes; None leaves that side unbounded."""
        low = (
            np.full(len(self._ids), -np.inf)
            if lower is None
            else vector(lower, self._ids, "lower trades", broadcast=True)
        )
        high = (
            np.full(len(self._ids), np.inf)
            if upper is None
            else vector(upper, self._ids, "upper trades", broadcast=True)
        )
        if np.any(low > high):
            raise ValueError("lower trades must not exceed upper trades")
        self._lower, self._upper = low, high
        return self

    def limit_positions(self, *, lower=None, upper=None):
        """Bound current_positions plus hedge changes in instrument units."""
        low = (
            np.full(len(self._ids), -np.inf)
            if lower is None
            else vector(lower, self._ids, "lower positions", broadcast=True)
        )
        high = (
            np.full(len(self._ids), np.inf)
            if upper is None
            else vector(upper, self._ids, "upper positions", broadcast=True)
        )
        if np.any(low > high):
            raise ValueError("lower positions must not exceed upper positions")
        self._position_lower, self._position_upper = low, high
        return self

    def set_transaction_costs(self, *, buy=0.0, sell=0.0):
        """Set per-unit fees in currency, excluding execution spread."""
        buy = vector(buy, self._ids, "buy costs", broadcast=True)
        sell = vector(sell, self._ids, "sell costs", broadcast=True)
        if np.any(buy < 0) or np.any(sell < 0):
            raise ValueError("transaction costs must be nonnegative")
        self._buy_cost, self._sell_cost = buy, sell
        return self

    def set_cash_account(
        self, *, cash, prices, bid_prices=None, ask_prices=None
    ):
        """Account for upfront execution cash with supplied per-unit prices.

        Prices are actual upfront cash amounts, not futures face values or
        inferred margin. Spread enters costs once relative to prices.
        Borrowing is not implicit: post-trade cash must be nonnegative.
        """
        cash = scalar(cash, "cash", minimum=0)
        prices = vector(prices, self._ids, "prices", broadcast=True)
        bid = (
            prices.copy()
            if bid_prices is None
            else vector(bid_prices, self._ids, "bid_prices", broadcast=True)
        )
        ask = (
            prices.copy()
            if ask_prices is None
            else vector(ask_prices, self._ids, "ask_prices", broadcast=True)
        )
        if np.any(bid > prices) or np.any(prices > ask):
            raise ValueError("prices require bid <= valuation price <= ask")
        self._cash, self._prices, self._bid, self._ask = cash, prices, bid, ask
        return self

    def limit_capital(self, capital_per_unit, *, maximum):
        """Bound supplied capital_per_unit @ abs(post-trade positions)."""
        coefficients = vector(
            capital_per_unit, self._ids, "capital_per_unit", broadcast=True
        )
        if np.any(coefficients < 0):
            raise ValueError("capital_per_unit must be nonnegative")
        self._capital = (coefficients, scalar(maximum, "maximum", minimum=0))
        return self

    def trade_in_lots(self, lot_sizes):
        """Restrict signed changes to integer multiples of positive lots."""
        self._lots = checked_lot_sizes(lot_sizes, self._ids)
        return self

    def _specification(self):
        from .._value_io import encode

        return portable(
            {
                "model": "HedgeModel",
                "as_of": self._as_of,
                "instrument_ids": self._ids,
                "risk_ids": self._risks,
                "risk_units": self._units,
                "currency": self._currency,
                "current_exposures": self._exposure
                if len(self._risks)
                else None,
                "sensitivities": self._sensitivities
                if len(self._risks)
                else None,
                "current_positions": self._current,
                "objective": self._objective,
                "target": self._target,
                "exact_matching": self._objective == "hedge_cost",
                "mismatch_weights": self._weights,
                "cost_weight": self._cost_weight,
                "risk_lower": self._risk_lower,
                "risk_upper": self._risk_upper,
                "trade_lower": self._lower,
                "trade_upper": self._upper,
                "position_lower": self._position_lower,
                "position_upper": self._position_upper,
                "buy_cost": self._buy_cost,
                "sell_cost": self._sell_cost,
                "cash": self._cash,
                "prices": self._prices,
                "bid_prices": self._bid,
                "ask_prices": self._ask,
                "lot_sizes": self._lots,
                "capital_limit": self._capital,
                **(
                    {
                        "pnl_scenarios": encode(self._pnl_scenarios),
                        "current_pnl": self._current_pnl,
                        "cost_factors": self._cost_factors,
                        "scenario_loss_limits": self._loss_limit,
                        "expected_shortfall_limit": self._es_limit,
                        "scenario_confidence": (
                            self._confidence
                            if self._objective == "hedge_expected_shortfall"
                            else None
                        ),
                    }
                    if self._pnl_scenarios is not None
                    else {}
                ),
            }
        )

    def _financial_variables(self, variables):
        scales = np.ones(len(self._ids)) if self._lots is None else self._lots
        hedges = pd.Series(
            [
                float(scale) * variables[f"hedge_{i}"]
                for i, scale in enumerate(scales)
            ],
            index=copy_index(self._ids),
            name="hedge_quantity",
            dtype=object,
        )
        return {
            "hedges": hedges,
            "positions": (hedges + self._current).rename("position"),
        }

    def to_model(self, *, return_variables=False):
        """Return an independent Opt model for a supported LP/MILP/QP.

        return_variables=True also returns instrument-indexed hedges and
        positions in signed actual quantities, not lot counts.
        """
        from .._solvers._expressions import export_model
        from ._compile import compile_opt

        try:
            with np.errstate(over="raise", invalid="raise", divide="raise"):
                return export_model(compile_opt(self), self, return_variables)
        except (FloatingPointError, OverflowError) as error:
            raise ValueError(
                "hedge coefficients exceed float64 range"
            ) from error

    def _compile_cvxpy(self):
        from ._compile import compile_cvxpy

        try:
            with np.errstate(over="raise", invalid="raise", divide="raise"):
                return compile_cvxpy(self)
        except (FloatingPointError, OverflowError) as error:
            raise ValueError(
                "hedge coefficients exceed float64 range"
            ) from error

    def to_cvxpy(self):
        """Return a CVXPY problem and instrument-indexed hedges/positions.

        Both mappings use signed actual quantities, including with lots.
        """
        problem, variables = self._compile_cvxpy()
        return problem, self._financial_variables(variables)

    def evaluate(self, hedges, *, tolerance=1e-7):
        """Recompute risk, positions, costs, cash and original limits.

        Risk, cash and capital balances retain their component sums and
        products until the final binary64 rounding, including risk targets
        and limits. Scenario P&L retains original costs through carrying,
        netting and tail-risk checks. Position violations retain small
        trades against large opening positions. Displayed totals are binary64;
        risk_exposures also reports the signed change and target residual.
        """
        from ._evaluation import evaluate

        try:
            with np.errstate(over="raise", invalid="raise", divide="raise"):
                return evaluate(self, hedges, tolerance=tolerance)
        except (FloatingPointError, OverflowError) as error:
            raise ValueError(
                "hedge calculations exceed float64 range"
            ) from error

    def _evaluate_solution(self, solution, *, tolerance):
        from ._evaluation import evaluate_solution

        try:
            with np.errstate(over="raise", invalid="raise", divide="raise"):
                return evaluate_solution(self, solution, tolerance=tolerance)
        except (FloatingPointError, OverflowError) as error:
            raise ValueError(
                "hedge calculations exceed float64 range"
            ) from error
