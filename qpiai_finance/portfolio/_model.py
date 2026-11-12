"""Portfolio construction in source weight coordinates."""

from collections.abc import Mapping
from copy import deepcopy
from numbers import Integral

import numpy as np
import pandas as pd
from scipy import sparse

from .._validation import (
    _unit_sum,
    copy_frame,
    copy_index,
    identifiers,
    matrix,
    matrix_input,
    same_labels,
    scalar,
    vector,
)
from .._validation import confidence as checked_confidence
from .._validation import covariance as checked_covariance
from .._validation import lot_sizes as checked_lot_sizes
from ..risk import FactorRisk, _risk_product
from ..scenarios import Scenarios
from ._rebalancing import _Account

__all__ = ["PortfolioModel"]


class PortfolioModel:
    """A single-period portfolio allocation or rebalancing model.

    Expected arithmetic returns and covariance must share ``horizon``.
    Weights are fractions of the declared investment basis;
    sum(weights)=``net_weight``. With holdings, prices and cash, weights
    use initial portfolio value as their denominator; costs and the cash
    balance enter the self-financing equation. Weights relative to post-trade
    account value are reported separately. Explicitly supplied turnover is
    sum(abs(w-current_weights)), without the 1/2 convention. This
    model's compiled Opt model is detached; editing it does not edit
    Finance.
    """

    def __init__(
        self,
        expected_returns=None,
        covariance=None,
        *,
        horizon,
        asset_ids=None,
        net_weight=1.0,
        holdings=None,
        prices=None,
        cash=None,
        currency=None,
        bid_prices=None,
        ask_prices=None,
        cash_return=0.0,
    ):
        if not isinstance(horizon, str) or not horizon.strip():
            raise ValueError(
                "horizon must describe the common return/covariance horizon"
            )
        if expected_returns is None:
            if covariance is None:
                raise ValueError("provide covariance or expected_returns")
            if asset_ids is not None:
                ids = asset_ids
            elif isinstance(covariance, FactorRisk):
                ids = covariance.asset_ids
            elif isinstance(covariance, (pd.DataFrame, Mapping)):
                covariance = matrix_input(covariance)
                ids = covariance.index
            else:
                shape = np.shape(covariance)
                if len(shape) != 2:
                    raise ValueError("covariance must be a square matrix")
                ids = range(shape[0])
            supplied = None
        elif isinstance(expected_returns, (pd.Series, Mapping)):
            supplied = pd.Series(expected_returns)
            ids = supplied.index if asset_ids is None else asset_ids
        else:
            supplied = expected_returns
            ids = range(len(supplied)) if asset_ids is None else asset_ids
        self._ids = identifiers(ids)
        self._mu = (
            None
            if supplied is None
            else vector(supplied, self._ids, "expected_returns")
        )
        if isinstance(covariance, FactorRisk):
            same_labels(covariance.asset_ids, self._ids, "factor risk assets")
            self._covariance = deepcopy(covariance)
        else:
            self._covariance = (
                None
                if covariance is None
                else checked_covariance(covariance, self._ids)
            )
        self._horizon = horizon
        self._net_weight = scalar(net_weight, "net_weight")
        self._lower = np.zeros(len(self._ids))
        self._upper = np.ones(len(self._ids))
        self._objective = "variance"
        self._risk_aversion = 1.0
        self._benchmark = None
        self._minimum_return = None
        self._exposures = []
        self._leverage = None
        self._turnover = None
        self._scenarios = None
        self._confidence = None
        self._volatility_limit = None
        self._return_uncertainty = None
        self._account = None
        self._selection = None
        self._fixed_selection = None
        self._risk_budgets = None
        self._risk_budget_polish = True
        self._risk_budget_polish_maxiter = 20
        self._linkage_method = "single"
        self._moment_preferences = None
        account_inputs = (
            holdings,
            prices,
            cash,
            currency,
            bid_prices,
            ask_prices,
        )
        if any(value is not None for value in account_inputs):
            if any(
                value is None for value in (holdings, prices, cash, currency)
            ):
                raise ValueError(
                    "rebalancing requires holdings, prices, cash and currency"
                )
            self._account = _Account.create(
                self._ids,
                holdings,
                prices,
                cash,
                currency,
                bid_prices,
                ask_prices,
                cash_return,
            )
        elif scalar(cash_return, "cash_return") != 0:
            raise ValueError(
                "cash_return requires holdings, prices, cash and currency"
            )

    @property
    def asset_ids(self):
        return copy_index(self._ids)

    @property
    def expected_returns(self):
        return (
            None
            if self._mu is None
            else pd.Series(
                self._mu.copy(),
                index=copy_index(self._ids),
                name="expected_return",
            )
        )

    @property
    def horizon(self):
        return self._horizon

    @property
    def _objective_unit(self):
        if self._objective == "hrp":
            return None
        if self._objective == "risk_budgeting":
            return "dimensionless"
        if self._objective in {"variance", "tracking_error"}:
            return "return_fraction_squared"
        return "return_fraction"

    def minimize_variance(self):
        """Minimize w.T @ covariance @ w at the declared return horizon."""
        self._objective = "variance"
        self._benchmark = None
        return self

    def maximize_utility(self, *, risk_aversion):
        """Maximize expected return minus risk_aversion * variance / 2.

        risk_aversion is nonnegative. Expected return includes modeled cash
        income and transaction costs. It uses worst-case forecasts when
        robust_returns is active. Zero aversion maximizes return alone.
        """
        value = scalar(risk_aversion, "risk_aversion", minimum=0)
        self._objective = "utility"
        self._risk_aversion = value
        self._benchmark = None
        return self

    def minimize_tracking_error(self, *, benchmark):
        """Minimize active variance relative to supplied benchmark weights.

        benchmark aligns by asset ID or uses the model's array order.
        The objective is squared tracking error; reported tracking_error
        is its square root, at the model's return horizon.
        Results also report covariance-implied benchmark beta, which is
        undefined (NaN) if the supplied benchmark has zero variance.
        """
        value = vector(benchmark, self._ids, "benchmark")
        self._objective = "tracking_error"
        self._benchmark = value
        return self

    def allocate_risk(self, budgets=None, *, polish=True, polish_maxiter=20):
        """Allocate positive variance-risk budgets, equal by default.

        Budgets are fractions summing to one. The positive risk positions
        solve a convex logarithmic program and are then scaled to the
        investment basis. The returned weights must still satisfy every
        financial constraint and the requested risk contributions.
        """
        if not isinstance(polish, bool):
            raise TypeError("polish must be boolean")
        if (
            isinstance(polish_maxiter, (bool, np.bool_))
            or not isinstance(polish_maxiter, Integral)
            or polish_maxiter <= 0
        ):
            raise ValueError("polish_maxiter must be a positive integer")
        if budgets is None:
            values = np.full(len(self._ids), 1 / len(self._ids))
        else:
            values = vector(budgets, self._ids, "risk budgets")
        if np.any(values <= 0) or np.any(values > 1 + 1e-12) or not np.isclose(
            values.sum(), 1.0, rtol=0, atol=1e-12
        ):
            raise ValueError("risk budgets must be positive and sum to one")
        self._risk_budgets = _unit_sum(values)
        self._risk_budget_polish = polish
        self._risk_budget_polish_maxiter = int(polish_maxiter)
        self._objective = "risk_budgeting"
        self._benchmark = None
        return self

    def hierarchical_risk_parity(self, *, linkage_method="single"):
        """Construct a long-only HRP allocation using correlation distances.

        This is a portfolio construction heuristic, not a minimum-variance
        optimizer or a guarantee of equal risk contributions.
        """
        methods = {
            "single",
            "complete",
            "average",
            "weighted",
            "centroid",
            "median",
            "ward",
        }
        if (
            not isinstance(linkage_method, str)
            or linkage_method not in methods
        ):
            raise ValueError("linkage_method must be a SciPy linkage method")
        self._linkage_method = linkage_method
        self._objective = "hrp"
        self._benchmark = None
        return self

    def efficient_frontier(
        self,
        target_returns,
        *,
        client=None,
        solver=None,
        mode="local",
        allow_platform=False,
        tolerance=1e-7,
        **options,
    ):
        """Compute minimum-variance portfolios for the supplied return targets.

        Existing constraints are retained. The original model is unchanged,
        and infeasible targets remain in the returned table.
        """
        from ._frontier import efficient_frontier

        return efficient_frontier(
            self,
            target_returns,
            client=client,
            solver=solver,
            mode=mode,
            allow_platform=allow_platform,
            tolerance=tolerance,
            **options,
        )

    def _scenario_objective(self, scenarios, objective, beta=None):
        if not isinstance(scenarios, Scenarios):
            raise TypeError("scenarios must be Scenarios")
        same_labels(scenarios.asset_ids, self._ids, "scenario assets")
        if (
            scenarios.unit != "simple_return"
            or scenarios.horizon != self._horizon
        ):
            raise ValueError(
                "portfolio scenarios require simple_return units "
                "and the model horizon"
            )
        if scenarios.probabilities is None:
            raise ValueError(
                "risk optimization requires explicit scenario probabilities"
            )
        snapshot = deepcopy(scenarios)
        # Align scenario columns with the portfolio before compilation.
        values = snapshot.values.reindex(columns=self._ids)
        values = (
            values.sparse.to_coo().tocsr()
            if sparse.issparse(snapshot._values)
            else values.to_numpy()
        )
        snapshot._assets = copy_index(self._ids)
        snapshot._values = values
        self._objective = objective
        self._scenarios = snapshot
        self._confidence = beta
        self._benchmark = None
        return self

    def minimize_expected_shortfall(self, scenarios, *, confidence=0.95):
        """Minimize financial upper-tail loss ES under explicit probabilities.

        scenarios must be Scenarios with simple_return units and this
        model's horizon. confidence lies strictly between zero and one.
        Fractional mass at the tail boundary is included. This is distinct
        from lower-energy-tail aggregation in quantum optimization.
        """
        return self._scenario_objective(
            scenarios, "expected_shortfall", checked_confidence(confidence)
        )

    def maximize_moment_utility(
        self,
        scenarios,
        *,
        variance_aversion,
        skewness_preference=0.0,
        kurtosis_aversion=0.0,
    ):
        """Maximize mean minus variance, plus third, minus fourth moment.

        The mean uses expected_returns. Central moments use the supplied
        scenario distribution, without sample corrections or variance
        standardization. The three coefficients multiply raw moments
        directly; choose them so every term has return-fraction units.
        Binary optimization currently requires equal-weight selection.
        """
        preferences = tuple(
            scalar(value, name, minimum=0)
            for name, value in (
                ("variance_aversion", variance_aversion),
                ("skewness_preference", skewness_preference),
                ("kurtosis_aversion", kurtosis_aversion),
            )
        )
        self._scenario_objective(scenarios, "moment_utility")
        self._moment_preferences = preferences
        return self

    def minimize_mean_absolute_deviation(self, scenarios):
        """Minimize expected absolute deviation from scenario-weighted mean
        return.
        """
        return self._scenario_objective(scenarios, "mean_absolute_deviation")

    def minimize_downside_risk(self, scenarios, *, target=0.0):
        """Minimize expected shortfall below a return target (first lower
        partial moment).
        """
        target = scalar(target, "target")
        self._scenario_objective(scenarios, "downside")
        self._downside_target = target
        return self

    def require_return(self, *, minimum):
        """Require at least minimum net arithmetic return, as a fraction.

        Uses the model horizon and supplied forecasts. Modeled cash income
        and transaction costs enter net return; active return uncertainty
        replaces nominal return with its specified worst-case value.
        """
        self._minimum_return = scalar(minimum, "minimum")
        return self

    def limit_weights(self, *, lower=0.0, upper=1.0):
        """Set per-asset weight bounds as fractions of the investment basis.

        Scalars broadcast. Mappings/Series align by asset ID; arrays follow
        asset_ids. Negative lower bounds permit short weights, subject to
        any separately configured borrow availability and leverage limits.
        """
        lower_bounds = vector(lower, self._ids, "lower", broadcast=True)
        upper_bounds = vector(upper, self._ids, "upper", broadcast=True)
        if np.any(lower_bounds > upper_bounds):
            raise ValueError("lower weights must not exceed upper weights")
        self._lower, self._upper = lower_bounds, upper_bounds
        return self

    def limit_exposures(self, exposures, *, lower, upper, exposure_ids=None):
        """Bound exposure_matrix @ weights for exposure rows and asset columns.

        DataFrames and column mappings align by exposure and asset ID;
        arrays use exposure_ids and the model's asset order. Bounds use
        the resulting exposure units and may be scalar or one value per
        exposure. Exposure IDs
        must remain unique across calls. No currency conversion is implied.
        """
        exposures = matrix_input(exposures)
        if exposure_ids is None:
            exposure_ids = (
                exposures.index
                if isinstance(exposures, pd.DataFrame)
                else range(np.shape(exposures)[0])
            )
        ids = identifiers(exposure_ids, "exposure_ids")
        values = matrix(exposures, ids, self._ids, "exposures")
        lower_bounds = vector(lower, ids, "lower exposure", broadcast=True)
        upper_bounds = vector(upper, ids, "upper exposure", broadcast=True)
        if np.any(lower_bounds > upper_bounds):
            raise ValueError("lower exposures must not exceed upper exposures")
        if any(set(ids) & set(existing[0]) for existing in self._exposures):
            raise ValueError(
                "exposure IDs must be unique across exposure groups"
            )
        self._exposures.append((ids, values, lower_bounds, upper_bounds))
        return self

    def limit_leverage(self, *, maximum):
        """Bound gross investment-basis exposure sum(abs(weights))."""
        self._leverage = scalar(maximum, "maximum", minimum=0)
        return self

    def limit_volatility(self, *, maximum):
        """Bound volatility in return fractions at the model horizon."""
        self._volatility_limit = scalar(maximum, "maximum", minimum=0)
        return self

    def robust_returns(self, uncertainty, *, radius, uncertainty_ids=None):
        """Use min μᵀw = μ₀ᵀw−radius*||Uᵀw||₂ for μ=μ₀+Uu, ||u||₂≤radius.

        Applies to the utility objective and minimum-return constraint;
        covariance remains the supplied risk model. No statistical
        confidence is inferred. U has asset rows and
        uncertainty-coordinate columns, in return units.
        """
        uncertainty = matrix_input(uncertainty)
        if uncertainty_ids is None:
            uncertainty_ids = (
                uncertainty.columns
                if isinstance(uncertainty, pd.DataFrame)
                else range(np.shape(uncertainty)[1])
            )
        ids = identifiers(uncertainty_ids, "uncertainty_ids")
        values = matrix(uncertainty, self._ids, ids, "return_uncertainty")
        radius = scalar(radius, "radius", minimum=0)
        self._return_uncertainty = (ids, values, radius)
        return self

    @property
    def _needs_conic(self):
        return self._volatility_limit is not None or (
            self._return_uncertainty is not None
            and self._return_uncertainty[2] > 0
            and (
                self._objective == "utility"
                or self._minimum_return is not None
            )
        )

    def limit_turnover(self, current_weights=None, *, maximum):
        """Bound sum(abs(weights-current_weights)), without a factor of half.

        Inputs use investment-basis fractions. With a starting share/cash
        account, omitting current_weights uses its initial weights;
        otherwise a complete current allocation is required.
        """
        if current_weights is None:
            if self._account is None:
                raise ValueError(
                    "current_weights are required without a starting portfolio"
                )
            current_weights = self._account.initial_weights
        current = vector(current_weights, self._ids, "current_weights")
        maximum = scalar(maximum, "maximum", minimum=0)
        self._turnover = (current, maximum)
        return self

    def limit_cash(self, *, minimum=0.0, maximum=None):
        """Limit the post-trade cash balance in the account currency."""
        if self._account is None:
            raise ValueError("cash limits require a starting portfolio")
        lower_bounds = scalar(minimum, "minimum")
        upper_bounds = (
            self._account.initial_value
            if maximum is None
            else scalar(maximum, "maximum")
        )
        if lower_bounds > upper_bounds:
            raise ValueError("minimum cash must not exceed maximum cash")
        self._account.cash_lower = lower_bounds / self._account.initial_value
        self._account.cash_upper = upper_bounds / self._account.initial_value
        return self

    def set_trading_costs(
        self,
        *,
        buy_bps=0.0,
        sell_bps=0.0,
        buy_fixed=0.0,
        sell_fixed=0.0,
        minimum_trade=0.0,
    ):
        """Set fees in addition to bid/ask spread; fixed fees use account
        currency.

        Basis-point fees apply to actual ask/bid trade values.
        minimum_trade is in shares. Fixed fees need a positive minimum
        trade or an integer lot.
        """
        if self._account is None:
            raise ValueError("trading costs require a starting portfolio")
        values = {}
        for name, value in (
            ("buy_bps", buy_bps),
            ("sell_bps", sell_bps),
            ("buy_fixed", buy_fixed),
            ("sell_fixed", sell_fixed),
            ("minimum_trade", minimum_trade),
        ):
            array = vector(value, self._ids, name, broadcast=True)
            if np.any(array < 0):
                raise ValueError(f"{name} must be nonnegative")
            values[name] = array
        for name, value in values.items():
            setattr(self._account, name, value)
        return self

    def trade_in_lots(self, lot_sizes):
        """Restrict each signed share trade to an integer multiple of its
        lot size.
        """
        if self._account is None:
            raise ValueError("trade lots require a starting portfolio")
        self._account.lots = checked_lot_sizes(lot_sizes, self._ids)
        return self

    @property
    def tax_lots(self):
        """Return a detached acquisition-lot table, or None if unconfigured."""
        if self._account is None or self._account.tax_lots is None:
            return None
        return copy_frame(self._account.tax_lots.table)

    def set_tax_lots(self, lots, *, as_of, settlement):
        """Set owned long acquisition lots and institution-supplied tax rules.

        Required columns are asset, quantity, per-share cost_basis, acquired
        (calendar date), and gain tax_rate. Optional loss_credit_rate defaults
        to zero; eligible defaults True; quantity_step defaults to divisible
        quantities (zero). Taxable proceeds per unit default to the actual bid
        price; taxable_proceeds_per_unit can specify a supplied adjustment.
        Fees are not automatically deducted from taxable proceeds or basis.

        Every owned share must belong to exactly one supplied lot. Rates are
        fractions in [0,1], effective at as_of. No holding-period tax rate,
        wash-sale eligibility, tax netting or jurisdiction rule is inferred.
        settlement='immediate' pays or credits tax during the rebalance;
        'deferred' records the liability without using it as current cash.
        Both recognize tax in economic return. Existing tax limits remain.
        """
        from ._tax_lots import _TaxLots

        if self._account is None:
            raise ValueError("tax lots require a starting portfolio")
        book = _TaxLots(
            lots,
            self._ids,
            self._account.holdings,
            self._account.bid_prices,
            as_of=as_of,
            settlement=settlement,
        )
        if self._account.tax_lots is not None:
            book.minimum = self._account.tax_lots.minimum
            book.maximum = self._account.tax_lots.maximum
        self._account.tax_lots = book
        return self

    def limit_tax(self, *, minimum=None, maximum=None):
        """Bound net recognized tax in account currency; None unbounds a side.

        A negative minimum caps net loss credits. This is a net tax budget,
        not a gross-gains or jurisdiction-specific offset calculation.
        """
        if self._account is None or self._account.tax_lots is None:
            raise ValueError("tax limits require configured tax lots")
        low = None if minimum is None else scalar(minimum, "minimum tax")
        high = None if maximum is None else scalar(maximum, "maximum tax")
        if low is not None and high is not None and low > high:
            raise ValueError("minimum tax must not exceed maximum tax")
        self._account.tax_lots.minimum = low
        self._account.tax_lots.maximum = high
        return self

    def limit_short_positions(self, maximum):
        """Specify available borrow quantities in shares for each asset."""
        if self._account is None:
            raise ValueError(
                "borrow availability requires a starting portfolio"
            )
        values = vector(maximum, self._ids, "maximum", broadcast=True)
        if np.any(values < 0):
            raise ValueError("borrow availability must be nonnegative")
        self._account.short_available = values
        return self

    def select_assets(
        self,
        *,
        count=None,
        maximum=None,
        minimum_weight=0.0,
        equal_weight=False,
    ):
        """Limit selected names, optionally imposing a minimum absolute
        position.

        Exactly count names requires minimum_weight > 0, or
        equal_weight=True. Equal weights are nonnegative and sum to
        net_weight; in cash accounts this restriction is not combined
        with transaction costs.
        """
        if (count is None) == (maximum is None):
            raise ValueError("provide exactly one of count or maximum")
        value = count if count is not None else maximum
        if (
            isinstance(value, (bool, np.bool_))
            or not isinstance(value, Integral)
            or not 0 <= value <= len(self._ids)
        ):
            raise ValueError(
                "selected asset count must be an integer "
                "from 0 to the number of assets"
            )
        minimum_weight = scalar(minimum_weight, "minimum_weight", minimum=0)
        if not isinstance(equal_weight, bool):
            raise TypeError("equal_weight must be boolean")
        if equal_weight and (count is None or count == 0):
            raise ValueError("equal_weight requires a positive count")
        if count and minimum_weight == 0 and not equal_weight:
            raise ValueError(
                "an exact count requires a positive minimum_weight "
                "or equal_weight=True"
            )
        self._selection = {
            "count": count,
            "maximum": maximum,
            "minimum_weight": minimum_weight,
            "equal_weight": equal_weight,
        }
        return self

    def fix_selection(self, selected):
        """Fix asset-selection decisions and retain position-size controls.

        Configure select_assets first. Values are 1 for a selected long,
        -1 for a selected short and 0 for exclusion. Boolean masks select
        longs. Series/mappings align by asset ID; arrays use asset_ids.
        None restores the unfixed selection search. Replacement is atomic.

        All financial constraints, costs and objectives remain in force.
        Equal-weight selection keeps its specified weights; to optimize
        unequal sizes, use a separate model with a positive minimum_weight.
        With maximum and zero minimum_weight, a selected position may be
        zero. Other discrete trade/tax-lot rules remain discrete. Any
        optimum is conditional on this selection, not a certificate for
        the unfixed search. This method performs no solve or authentication.
        """
        if selected is None:
            self._fixed_selection = None
            return self
        if self._selection is None:
            raise ValueError("fix_selection requires select_assets first")
        if isinstance(selected, Mapping):
            selected = pd.Series(selected)
        if isinstance(selected, pd.Series):
            same_labels(selected.index, self._ids, "selected assets")
            selected = selected.reindex(self._ids).to_numpy()
        values = np.asarray(selected)
        if values.dtype.kind == "b":
            values = values.astype(int)
        values = vector(values, self._ids, "selected")
        if not np.isin(values, (-1, 0, 1)).all():
            raise ValueError("selected must contain only -1, 0 or 1")
        self._check_fixed_selection(values)
        self._fixed_selection = values.astype(int)
        return self

    def _check_fixed_selection(self, values):
        selection = self._selection
        number = np.count_nonzero(values)
        if selection["count"] is not None:
            if number != selection["count"]:
                raise ValueError("fixed selection must match count")
        elif number > selection["maximum"]:
            raise ValueError("fixed selection exceeds maximum")
        if selection["equal_weight"] and np.any(values < 0):
            raise ValueError("equal-weight selection does not permit shorts")

    def _fixed_weight_bounds(self):
        positive = (self._fixed_selection > 0).astype(float)
        negative = (self._fixed_selection < 0).astype(float)
        selection = self._selection
        if selection["equal_weight"]:
            weights = self._net_weight / selection["count"] * positive
            return weights, weights
        minimum = selection["minimum_weight"]
        return (
            minimum * positive + np.minimum(0, self._lower) * negative,
            np.maximum(0, self._upper) * positive - minimum * negative,
        )

    def _allocation_bounds(self):
        if self._fixed_selection is None:
            return self._lower, self._upper, None
        lower, upper = self._fixed_weight_bounds()
        lower = np.maximum(lower, self._lower)
        upper = np.minimum(upper, self._upper)
        conflicts = lower > upper
        # Conflicting mandates are infeasible models, not invalid variables.
        lower[conflicts] = self._lower[conflicts]
        upper[conflicts] = self._upper[conflicts]
        return lower, upper, conflicts

    @property
    def _mixed_integer(self):
        return (
            self._selection is not None and self._fixed_selection is None
        ) or (
            self._account is not None and self._account.mixed_integer
        )

    @property
    def _quadratic_objective(self):
        return self._objective in {"variance", "tracking_error"} or (
            self._objective == "utility" and self._risk_aversion > 0
        )

    @property
    def _needs_external(self):
        return (
            self._objective == "risk_budgeting"
            or self._needs_conic
            or (self._mixed_integer and self._quadratic_objective)
        )

    @property
    def _problem_class(self):
        if self._objective == "moment_utility":
            return "HUBO"
        if self._objective == "risk_budgeting":
            return "CONIC"
        if self._objective == "hrp":
            return "HEURISTIC"
        if self._needs_conic:
            return "MISOCP" if self._mixed_integer else "SOCP"
        if self._quadratic_objective:
            return "MIQP" if self._mixed_integer else "QP"
        return "MILP" if self._mixed_integer else "LP"

    def _risk_apply(self, weights, *, original=False):
        if isinstance(self._covariance, FactorRisk):
            risk = self._covariance
            order = self._ids.get_indexer(risk._assets)
            marginal = _risk_product(risk, weights[order], original=original)
            return marginal[risk._assets.get_indexer(self._ids)]
        return _risk_product(self._covariance, weights, original=original)

    def _risk_diagonal(self):
        risk = self._covariance
        if isinstance(risk, FactorRisk):
            loadings = sparse.csr_matrix(risk._b)
            cross = loadings @ sparse.csr_matrix(risk._f)
            diagonal = (
                np.asarray(cross.multiply(loadings).sum(axis=1)).ravel()
                + risk._d
            )
            return diagonal[risk._assets.get_indexer(self._ids)]
        return np.asarray(risk.diagonal()).ravel()

    def _check(self):
        if self._fixed_selection is not None:
            self._check_fixed_selection(self._fixed_selection)
            if self._objective in {"risk_budgeting", "hrp", "moment_utility"}:
                raise ValueError(
                    "fixed selection requires a position-allocation "
                    "objective, not a risk-construction or moment method"
                )
        if self._objective in {"risk_budgeting", "hrp"}:
            if self._covariance is None:
                raise ValueError("risk allocation requires covariance")
            if self._account is not None:
                raise ValueError(
                    "risk allocation constructs weights; use a separate "
                    "rebalancing model for share trades and costs"
                )
            if self._net_weight <= 0:
                raise ValueError(
                    "risk allocation requires positive net_weight"
                )
            if np.any(self._risk_diagonal() <= 0):
                raise ValueError(
                    "risk allocation requires positive asset variances"
                )
        if self._account is not None:
            if self._net_weight != 1:
                raise ValueError(
                    "rebalancing uses the self-financing budget; "
                    "net_weight must be 1"
                )
            self._account.validate(self._lower)
            if self._selection is not None and self._selection["equal_weight"]:
                raise ValueError(
                    "equal-weight selection requires an allocation model "
                    "without a cash account"
                )
        if (
            self._selection is not None
            and self._selection["equal_weight"]
            and self._net_weight <= 0
        ):
            raise ValueError(
                "equal-weight selection requires positive net_weight"
            )
        if self._selection is not None and self._selection["equal_weight"]:
            if (
                self._selection["minimum_weight"]
                > self._net_weight / self._selection["count"]
            ):
                raise ValueError(
                    "minimum_weight exceeds the specified equal weight"
                )
        if self._mu is None and (
            self._objective in {"utility", "moment_utility"}
            or self._minimum_return is not None
            or self._return_uncertainty is not None
        ):
            raise ValueError(
                "utility, return targets and robust forecasts "
                "require expected_returns"
            )
        if (
            self._volatility_limit is not None
            or self._objective in {"variance", "tracking_error"}
            or (self._objective == "utility" and self._risk_aversion > 0)
        ):
            if self._covariance is None:
                raise ValueError(
                    "the selected risk objective requires covariance"
                )

    def _financial_variables(self, variables):
        weight_values = variables.get("weights")
        weights = pd.Series(
            [
                weight_values[i]
                if weight_values is not None
                else variables[f"weight_{i}"]
                for i in range(len(self._ids))
            ],
            index=copy_index(self._ids),
            name="weight",
            dtype=object,
        )
        result = {"weights": weights}
        if self._objective == "risk_budgeting":
            result["unnormalized_weights"] = pd.Series(
                [
                    variables[f"risk_position_{i}"]
                    for i in range(len(self._ids))
                ],
                index=copy_index(self._ids),
                name="unnormalized_weight",
                dtype=object,
            )
        account = self._account
        if account is not None:
            try:
                with np.errstate(
                    over="raise", invalid="raise", divide="raise"
                ):
                    quantity_per_weight = (
                        account.initial_value / account.prices
                    )
            except FloatingPointError as error:
                raise ValueError(
                    "portfolio quantity expressions exceed float64 range; "
                    "rescale currency or quantity units"
                ) from error
            holdings = (weights * quantity_per_weight).rename("quantity")
            result.update(
                holdings=holdings,
                trades=holdings - account.holdings,
                cash_after=account.initial_value * variables["cash_weight"],
            )
            if account.tax_lots is not None:
                result["tax_lot_sales"] = account.tax_lots._sale_expressions(
                    variables
                )
        return result

    def to_model(self, *, return_variables=False):
        """Return an independent Opt model.

        return_variables=True also returns asset-indexed weights and,
        for rebalancing, actual holdings/trades, currency cash_after and
        supplied acquisition-lot tax_lot_sales where configured.
        """
        from .._solvers._expressions import export_model
        from ._opt import compile_model

        return export_model(compile_model(self), self, return_variables)

    def to_cvxpy(self):
        """Return a CVXPY problem and labeled financial expressions.

        weights are asset-indexed. Rebalancing also exposes actual
        holdings/trades, currency cash_after and supplied tax_lot_sales.
        Risk budgeting additionally exposes unnormalized_weights from its
        positive logarithmic construction program. Its normalized weights
        are generally non-affine expressions; adding constraints on them
        can violate DCP. Financial limits are checked by solve on the
        normalized allocation, not included in the construction program.
        """
        problem, variables = self._compile_cvxpy()
        return problem, self._financial_variables(variables)

    def _compile_cvxpy(self):
        from ._cvxpy import compile_model

        return compile_model(self)

    def _evaluate_solution(self, solution, *, tolerance):
        from ._evaluation import evaluate_solution

        return evaluate_solution(self, solution, tolerance=tolerance)

    def evaluate(self, weights, *, tax_lot_sales=None, tolerance=1e-7):
        """Check weights and configured lot disposals against source finances.

        tax_lot_sales supplies nonnegative disposal quantities by acquisition
        lot ID when tax lots are configured; weights alone cannot identify
        which lots were sold. No lot allocation is inferred or optimized.
        """
        from ._evaluation import evaluate_weights

        try:
            return evaluate_weights(
                self, weights, tax_lot_sales=tax_lot_sales, tolerance=tolerance
            )
        except (FloatingPointError, OverflowError) as error:
            raise ValueError(
                "portfolio calculations exceed float64 range"
            ) from error
