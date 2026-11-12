"""Adaptive investment decisions in shares and a single cash account."""

from collections.abc import Mapping
from copy import deepcopy

import numpy as np
import pandas as pd

from .._validation import confidence as checked_confidence
from .._validation import (
    copy_index,
    identifiers,
    lot_quantities,
    matrix,
    matrix_input,
    scalar,
    unit_labels,
    vector,
)
from ..cashflows import _bullet_loan_terms, _currency
from ..scenarios import ScenarioTree
from ._model import _grid
from .costs import _check_curve_capacity


class TradingModel:
    """Plan trades on an explicit financial information tree.

    prices is node-by-asset nonnegative valuation prices in one currency.
    tree declares the information available before each node's trades.
    buy_limits/sell_limits are finite nonnegative quantities per node/asset;
    set terminal-node limits to zero for valuation without terminal trading.
    Prices are a node-by-asset DataFrame/array, or a constant per-asset
    Series/mapping. Labeled prices supply asset IDs when not specified.
    holdings and cash describe the book before the root's flows and trades.

    cash_settlement='net' nets node flows, purchases, sales and fees.
    'prefunded' deducts node obligations, purchases and fees before sale
    proceeds, with positive flows available. Credit limits apply at closing
    and, under prefunding, before sale proceeds. Credit is revolving negative
    cash. Explicit term funding uses add_funding/add_existing_debt, with
    contractual repayments on the information tree. Prices and future
    information are supplied, without calibration or trading execution.
    """

    def __init__(
        self,
        prices,
        *,
        tree,
        holdings,
        cash,
        currency,
        buy_limits,
        sell_limits,
        cash_settlement,
        asset_ids=None,
        credit_limits=0.0,
        borrow_limits=0.0,
    ):
        if type(tree) is not ScenarioTree:
            raise TypeError("tree must be a ScenarioTree")
        self._tree = deepcopy(tree)
        self._nodes = tree.node_ids
        if isinstance(prices, Mapping):
            prices = pd.Series(prices)
        if asset_ids is None:
            asset_ids = (
                prices.columns
                if isinstance(prices, pd.DataFrame)
                else prices.index
                if isinstance(prices, pd.Series)
                else range(np.shape(prices)[1])
                if np.ndim(prices) == 2
                else []
            )
        self._ids = identifiers(asset_ids)
        self._prices = _grid(prices, self._nodes, self._ids, "prices")
        if np.any(self._prices < 0):
            raise ValueError("prices must be nonnegative")
        self._opening = vector(holdings, self._ids, "holdings", broadcast=True)
        self._currency = _currency(currency)
        if cash_settlement not in {"net", "prefunded"}:
            raise ValueError("cash_settlement must be 'net' or 'prefunded'")
        self._settlement = cash_settlement
        self._buy = _grid(buy_limits, self._nodes, self._ids, "buy limits")
        self._sell = _grid(sell_limits, self._nodes, self._ids, "sell limits")
        self._credit = vector(
            credit_limits, self._nodes, "credit limits", broadcast=True
        )
        self._borrow = _grid(
            borrow_limits, self._nodes, self._ids, "borrow limits"
        )
        if any(
            np.any(v < 0)
            for v in (self._buy, self._sell, self._credit, self._borrow)
        ):
            raise ValueError(
                "trade, credit and borrow limits must be nonnegative"
            )
        self._cash = scalar(cash, "cash")
        shape = self._prices.shape
        self._bid, self._ask = self._prices.copy(), self._prices.copy()
        self._buy_fees, self._sell_fees = np.zeros(shape), np.zeros(shape)
        self._fixed, self._minimum, self._lots = (
            np.zeros(shape),
            np.zeros(shape),
            np.zeros(shape),
        )
        self._splits, self._dividends, self._short_fees = (
            np.ones(shape),
            np.zeros(shape),
            np.zeros(shape),
        )
        self._deposit, self._borrowing = (
            np.ones(len(self._nodes)),
            np.ones(len(self._nodes)),
        )
        self._flows = np.zeros(len(self._nodes))
        self._cash_limits = self._position_limits = None
        self._turnover = self._gross = self._participation = None
        self._terminal_minimum = self._tail_limit = None
        self._exposures = []
        self._objective = "expected_wealth"
        self._target, self._confidence = None, 0.95
        self._impact_quadratic = np.zeros(shape)
        self._impact_power = np.zeros(shape)
        self._impact_curves = {}
        self._funding, self._existing_debt = {}, {}
        self._debt_limits = None
        self._facilities = {}

    @property
    def asset_ids(self):
        """Asset IDs in financial quantity order."""
        return copy_index(self._ids)

    @property
    def node_ids(self):
        """Information node IDs in chronological tree order."""
        return copy_index(self._nodes)

    @property
    def tree(self):
        """Detached information tree, including case weights and clock."""
        return deepcopy(self._tree)

    @property
    def currency(self):
        """The account and price currency."""
        return self._currency

    @property
    def _objective_unit(self):
        return self.currency

    @property
    def _problem_class(self):
        linear = self._linear_data()["problem_type"]
        if not self._has_nonlinear_impact:
            return linear
        if self._cash_monotone:
            return "MISOCP" if linear == "MILP" else "SOCP"
        buy, sell = self._capacities()
        if np.any((np.maximum(buy, sell) > 0) & (self._impact_power > 0)):
            return "MINLP" if linear == "MILP" else "NLP"
        return "MIQCP" if linear == "MILP" else "QCQP"

    @property
    def _mixed_integer(self):
        return self._linear_data()["problem_type"] == "MILP"

    @property
    def _has_nonlinear_impact(self):
        buy, sell = self._capacities()
        active = np.maximum(buy, sell) > 0
        return bool(
            np.any(
                active
                & ((self._impact_quadratic > 0) | (self._impact_power > 0))
            )
        )

    @property
    def _needs_external(self):
        return self._has_nonlinear_impact

    @property
    def _cash_monotone(self):
        return (
            self._cash_limits is None
            or not np.isfinite(self._cash_limits[1]).any()
        )

    @property
    def _requires_scip(self):
        return self._has_nonlinear_impact and not self._cash_monotone

    def set_trading_costs(
        self,
        *,
        bid_prices=None,
        ask_prices=None,
        buy_per_unit=0.0,
        sell_per_unit=0.0,
        fixed=0.0,
        minimum_trade=0.0,
    ):
        """Replace bid/ask and additional fees in currency per asset unit.

        Bid/ask default to valuation prices. fixed is currency per active
        node/asset trade; minimum_trade is its nonzero quantity minimum.
        Fixed fees require a positive minimum or lot when solving. Spreads
        are charged by bid/ask and are not added again as fees.
        """
        values = [
            self._prices.copy()
            if value is None
            else _grid(value, self._nodes, self._ids, name)
            for value, name in (
                (bid_prices, "bid prices"),
                (ask_prices, "ask prices"),
            )
        ]
        bid, ask = values
        fees = [
            _grid(value, self._nodes, self._ids, name)
            for value, name in (
                (buy_per_unit, "buy fees"),
                (sell_per_unit, "sell fees"),
                (fixed, "fixed fees"),
                (minimum_trade, "minimum trades"),
            )
        ]
        if (
            np.any(bid < 0)
            or np.any(bid > self._prices)
            or np.any(ask < self._prices)
        ):
            raise ValueError(
                "prices require 0 <= bid <= valuation price <= ask"
            )
        if any(np.any(v < 0) for v in fees):
            raise ValueError("fees and minimum trades must be nonnegative")
        self._bid, self._ask = bid, ask
        self._buy_fees, self._sell_fees, self._fixed, self._minimum = fees
        return self

    def trade_in_lots(self, lot_sizes):
        """Set node/asset quantity steps; zero denotes divisible quantities."""
        values = _grid(lot_sizes, self._nodes, self._ids, "lot sizes")
        if np.any(values < 0):
            raise ValueError("lot sizes must be nonnegative")
        self._lots = values
        return self

    def set_market_impact(self, *, quadratic=0.0, power_3_2=0.0, curves=None):
        """Replace additive temporary costs by node and asset.

        Cost is quadratic*abs(trade)**2 + power_3_2*abs(trade)**1.5 plus
        any quoted PWL curve. Coefficients use currency/unit**2 or
        currency/unit**1.5. curves is a DataFrame with node, asset, quantity
        and cost columns, ordered within each node/asset curve. Curves must
        start at (0,0), have nonnegative nondecreasing slopes and cover the
        permitted trade size. The linear interpolant is the specified cost,
        without an inferred nonlinear approximation or market calibration.
        All costs are paid from node cash. A monotone formulation uses conic
        solvers; finite cash ceilings require an exact graph and SCIP.
        PWL graphs use LP/MILP. No permanent/cross-impact is inferred.
        Configure quantity limits and lots before quoted curves. Coverage
        uses the largest permitted whole lot and is checked again on use
        if those controls change. Omitted cost components are reset.
        """
        from ._planning_impact import prepare_curves

        quad = _grid(quadratic, self._nodes, self._ids, "quadratic impact")
        power = _grid(power_3_2, self._nodes, self._ids, "power_3_2 impact")
        if np.any(quad < 0) or np.any(power < 0):
            raise ValueError("impact coefficients must be nonnegative")
        try:
            prepared = prepare_curves(self, curves)
        except (FloatingPointError, OverflowError) as error:
            raise ValueError(
                "impact curve coefficients exceed float64 range"
            ) from error
        if prepared:
            self._check_impact_curves(prepared, *self._capacities())
        self._impact_quadratic, self._impact_power, self._impact_curves = (
            quad,
            power,
            prepared,
        )

        return self

    def set_cash_flows(self, flows):
        """Replace external native-currency flows at each node.

        Positive values deposit cash; negative values include supplied
        liabilities/withdrawals, subject to the chosen net/prefunded cash
        convention. Use an earlier node for an earlier payment deadline.
        Wealth includes these flows, without a flow-adjusted return claim.
        Exclude financing already supplied through explicit loan contracts.
        """
        self._flows = vector(flows, self._nodes, "cash flows", broadcast=True)
        return self

    def set_carry(
        self,
        *,
        deposit_factors=1.0,
        borrowing_factors=1.0,
        dividends=0.0,
        share_factors=1.0,
        short_fees=0.0,
    ):
        """Replace supplied incoming-edge carry terms at non-root nodes.

        Scalars broadcast; labeled inputs contain NON-ROOT node rows only.
        Cash factors are positive gross factors over that incoming interval,
        not annual rates. Dividends and nonnegative short fees use currency
        per PARENT holding unit, before the positive share adjustment factor.
        Dividends on shorts are paid, not received. Deposit/borrowing factors
        apply to the positive/negative parent cash balance separately.
        No split/dividend total-return adjustment is inferred from prices.
        """
        nodes = self._nodes[1:]
        if not len(nodes):
            raise ValueError(
                "carry terms require a tree with an incoming edge"
            )
        deposit = vector(
            deposit_factors, nodes, "deposit factors", broadcast=True
        )
        borrowing = vector(
            borrowing_factors, nodes, "borrowing factors", broadcast=True
        )
        split = _grid(share_factors, nodes, self._ids, "share factors")
        dividend = _grid(dividends, nodes, self._ids, "dividends")
        fees = _grid(short_fees, nodes, self._ids, "short fees")
        if (
            np.any(deposit <= 0)
            or np.any(borrowing <= 0)
            or np.any(split <= 0)
        ):
            raise ValueError("cash and share factors must be positive")
        if np.any(fees < 0):
            raise ValueError("short fees must be nonnegative")
        self._deposit, self._borrowing = np.r_[1, deposit], np.r_[1, borrowing]
        self._splits = np.vstack([np.ones(len(self._ids)), split])
        self._dividends = np.vstack([np.zeros(len(self._ids)), dividend])
        self._short_fees = np.vstack([np.zeros(len(self._ids)), fees])
        return self

    def set_credit_limits(self, maximum):
        """Set approved post-trade revolving credit by node, in currency."""
        values = vector(maximum, self._nodes, "credit limits", broadcast=True)
        if np.any(values < 0):
            raise ValueError("credit limits must be nonnegative")
        self._credit = values
        return self

    def add_funding(
        self,
        funding_id,
        *,
        draw_node,
        repayment_stage,
        maximum,
        interest=0.0,
        fee=0.0,
        fixed_fee=0.0,
        minimum=0.0,
        lot_size=None,
    ):
        """Add a bullet loan available at one observed information node.

        Principal is chosen once at draw_node and repaid at every descendant
        node of repayment_stage, which must follow draw and lie within the
        horizon. interest is the full-term principal fraction paid at
        maturity, not an annual rate. fee is a principal fraction paid at
        draw; fixed_fee is currency per nonzero draw. minimum permits zero
        or at least that principal. lot_size is the principal quantity step.
        A fixed fee requires a positive minimum or lot.

        Terms are fixed when drawn. Funding events net within a node before
        trade prefunding; no intraday ordering,rollover or collateral rights
        are inferred. Use limit_facility for shared commitment limits.
        """
        from ..treasury._contracts import stage_position

        self._funding_id(funding_id)
        start = self._tree._position(draw_node)
        end = stage_position(self._tree, repayment_stage)
        if end <= self._tree._depths[start]:
            raise ValueError("repayment_stage must follow the draw node")
        terms = _bullet_loan_terms(
            maximum=maximum,
            interest=interest,
            fee=fee,
            fixed_fee=fixed_fee,
            minimum=minimum,
            lot_size=lot_size,
        )
        self._funding[funding_id] = dict(
            draw_node=self._nodes[start],
            repayment_stage=self._tree._stages[end],
            **terms,
        )
        return self

    def add_existing_debt(
        self, debt_id, *, principal, repayment_stage, interest=0.0
    ):
        """Declare opening term principal and its remaining interest.

        Opening cash already reflects the historical borrowing; this adds
        no new deposit. Principal and full remaining term interest are paid
        at each node of repayment_stage, including the root when specified.
        Interest is paid at maturity; no accrual or debt fair value is
        inferred for intermediate wealth. All repayments lie in the horizon.
        """
        from ..treasury._contracts import stage_position

        self._funding_id(debt_id)
        end = stage_position(self._tree, repayment_stage)
        principal = scalar(principal, "principal", minimum=0)
        if principal == 0:
            raise ValueError("existing debt principal must be positive")
        interest = scalar(interest, "interest", minimum=-1)
        self._existing_debt[debt_id] = dict(
            principal=principal,
            repayment_stage=self._tree._stages[end],
            interest=interest,
        )
        return self

    def _funding_id(self, value):
        identifiers([value], "funding ID")
        if value in self._funding or value in self._existing_debt:
            raise ValueError("debt and funding IDs must be unique")

    def limit_debt(self, *, maximum):
        """Cap post-event outstanding term principal at every node.

        Includes declared opening debt and new contracts, separately from
        negative-cash credit limits. Maturing principal is removed before
        this closing limit is checked; repayment cash is still required.
        """
        values = vector(maximum, self._nodes, "maximum debt", broadcast=True)
        if np.any(values < 0):
            raise ValueError("maximum debt must be nonnegative")
        self._debt_limits = values
        return self

    def limit_facility(
        self,
        facility_id,
        funding_ids,
        *,
        maximum,
        currency,
        fx_rates=None,
        reserved=0.0,
    ):
        """Cap shared funding principal on each realized information path.

        funding_ids names already added loans/existing debt. Membership can
        overlap for aggregate limits and sublimits. maximum and reserved
        are nonnegative scalars or node-indexed Series/mappings/vectors in
        facility currency. reserved consumes capacity outside this model,
        without creating cash. An overused reservation makes the plan
        infeasible.

        Count outstanding principal after each node's draws and repayments,
        only on that contract's ancestor/descendant path. Distinct future
        branches do not consume capacity simultaneously. All nodes, including
        zero-probability stress nodes, retain their hard limits. Interest and
        fees do not change the principal counted. No intraday sequencing or
        legal rollover right is inferred.

        FX quotes are facility-currency units per account-currency unit.
        Supply fixed currency-indexed Series/mappings/vectors, a scalar for
        the single account currency, or node-by-currency DataFrames/arrays.
        Same-currency quotes equal one; cross-currency quotes are explicit
        capacity valuation, not a cash FX trade. Reusing facility_id replaces
        that limit atomically; other facility limits remain unchanged.
        """
        from ..treasury._facilities import prepare

        currencies = {
            key: self._currency
            for contracts in (self._funding, self._existing_debt)
            for key in contracts
        }
        facility = prepare(
            facility_id,
            funding_ids,
            periods=self._nodes,
            contract_currencies=currencies,
            maximum=maximum,
            currency=currency,
            fx_rates=fx_rates,
            reserved=reserved,
        )
        self._facilities[facility_id] = facility
        return self

    def _facility_active(self):
        from ..treasury._contracts import schedule

        active = {
            key: schedule(
                self._tree, self._tree.root, source["repayment_stage"]
            )[0]
            for key, source in self._existing_debt.items()
        }
        active.update(
            {
                key: schedule(
                    self._tree, source["draw_node"], source["repayment_stage"]
                )[0]
                for key, source in self._funding.items()
            }
        )
        return active

    def set_borrow_limits(self, maximum):
        """Replace approved post-trade short quantities by node and asset."""
        values = _grid(maximum, self._nodes, self._ids, "borrow limits")
        if np.any(values < 0):
            raise ValueError("borrow limits must be nonnegative")
        self._borrow = values
        return self

    def limit_cash(self, *, minimum=None, maximum=None):
        """Bound post-trade cash by node; None leaves that side unbounded."""
        low, high = self._bounds(minimum, maximum, assets=False)
        self._cash_limits = None if minimum is maximum is None else (low, high)
        return self

    def limit_positions(self, *, lower=None, upper=None):
        """Bound post-trade asset quantities by node, without normalization."""
        low, high = self._bounds(lower, upper, assets=True)
        self._position_limits = None if lower is upper is None else (low, high)
        return self

    def _bounds(self, lower, upper, *, assets):
        shape = self._prices.shape if assets else (len(self._nodes),)

        def read(value, name):
            return (
                _grid(value, self._nodes, self._ids, name)
                if assets
                else vector(value, self._nodes, name, broadcast=True)
            )

        low = (
            np.full(shape, -np.inf)
            if lower is None
            else read(lower, "lower bound")
        )
        high = (
            np.full(shape, np.inf)
            if upper is None
            else read(upper, "upper bound")
        )
        if np.any(low > high):
            raise ValueError("lower bounds must not exceed upper bounds")
        return low, high

    def limit_turnover(self, maximum):
        """Cap absolute trade notional per node at that node's mark prices."""
        values = vector(maximum, self._nodes, "turnover", broadcast=True)
        if np.any(values < 0):
            raise ValueError("turnover must be nonnegative")
        self._turnover = values
        return self

    def limit_gross_notional(self, maximum):
        """Cap each node's marked gross holdings, in currency."""
        values = vector(maximum, self._nodes, "gross notional", broadcast=True)
        if np.any(values < 0):
            raise ValueError("gross notional must be nonnegative")
        self._gross = values
        return self

    def limit_exposures(
        self, coefficients, *, lower, upper, risk_units, exposure_ids=None
    ):
        """Bound supplied linear exposures with node-varying limits."""
        coefficients = matrix_input(coefficients)
        if exposure_ids is None:
            if isinstance(coefficients, pd.DataFrame):
                exposure_ids = coefficients.index
            else:
                shape = np.shape(coefficients)
                if len(shape) != 2:
                    raise ValueError("exposure coefficients must be a matrix")
                exposure_ids = range(shape[0])
        ids = identifiers(exposure_ids, "exposure_ids")
        values = matrix(coefficients, ids, self._ids, "exposures")
        low, high = (
            _grid(lower, self._nodes, ids, "lower exposures"),
            _grid(upper, self._nodes, ids, "upper exposures"),
        )
        if np.any(low > high) or any(
            set(ids) & set(old[0]) for old in self._exposures
        ):
            raise ValueError("exposure bounds must be ordered and IDs unique")
        units = unit_labels(risk_units, ids)
        self._exposures.append((ids, values, low, high, units))
        return self

    def limit_participation(self, volumes, *, maximum_rate):
        """Cap each node/asset trade by supplied quantity volume times rate."""
        volume = _grid(volumes, self._nodes, self._ids, "volumes")
        rate = _grid(
            maximum_rate, self._nodes, self._ids, "participation rates"
        )
        if np.any(volume < 0) or np.any(rate < 0) or np.any(rate > 1):
            raise ValueError("volumes must be nonnegative and rates in [0, 1]")
        self._participation = volume, rate
        return self

    def _capacities(self):
        if self._participation is None:
            return self._buy, self._sell
        volume, rate = self._participation
        return np.minimum(self._buy, volume * rate), np.minimum(
            self._sell, volume * rate
        )

    def limit_terminal_wealth(self, minimum):
        """Require terminal wealth per case, including zero-mass cases."""
        self._terminal_minimum = vector(
            minimum, self._tree.scenario_ids, "terminal wealth", broadcast=True
        )
        return self

    def limit_expected_shortfall(self, maximum, *, target, confidence=0.95):
        """Cap upper-tail loss ES of target minus marked terminal wealth.

        target uses currency per case, not a return fraction. Probabilities
        are required; the hard tail constraint retains its own confidence.
        """
        cap = scalar(maximum, "maximum expected shortfall")
        level = checked_confidence(confidence)
        values = vector(
            target, self._tree.scenario_ids, "target", broadcast=True
        )
        self._tail_limit = cap, values, level
        return self

    def maximize_expected_wealth(self):
        """Maximize terminal wealth using explicit case probabilities."""
        self._objective = "expected_wealth"
        return self

    def maximize_worst_case_wealth(self):
        """Maximize the minimum terminal wealth across every supplied case."""
        self._objective = "worst_case_wealth"
        return self

    def minimize_expected_shortfall(self, *, target, confidence=0.95):
        """Minimize weighted ES of target minus marked terminal wealth."""
        level = checked_confidence(confidence)
        values = vector(
            target, self._tree.scenario_ids, "target", broadcast=True
        )
        self._target, self._confidence = values, level
        self._objective = "terminal_expected_shortfall"
        return self

    def _check_impact_curves(self, curves, buy, sell):
        for (k, i), points in curves.items():
            _check_curve_capacity(
                points, max(buy[k, i], sell[k, i]), self._lots[k, i],
                self._minimum[k, i],
                f"impact curve at node {self._nodes[k]!r}, "
                f"asset {self._ids[i]!r}",
            )

    def _check(self):
        if self._tree._probabilities is None and (
            self._objective != "worst_case_wealth"
            or self._tail_limit is not None
        ):
            raise ValueError(
                "this objective/tail constraint requires "
                "explicit probabilities"
            )
        buy, sell = self._capacities()
        self._check_impact_curves(self._impact_curves, buy, sell)
        active = (buy > 0) | (sell > 0)
        if np.any(
            active
            & (self._fixed > 0)
            & (self._minimum == 0)
            & (self._lots == 0)
        ):
            raise ValueError(
                "fixed fees require a positive minimum trade or lot"
            )

    def to_matrix(self):
        """Return a detached complete sparse Opt LP/MILP formulation."""
        if self._has_nonlinear_impact:
            raise ValueError(
                "nonlinear cash costs require to_cvxpy() or to_scip(); "
                "an LP/MILP matrix cannot represent them"
            )
        return self._linear_data()

    def _linear_data(self):
        from ._planning_compile import compile_matrix

        self._check()
        try:
            with np.errstate(over="raise", invalid="raise", divide="raise"):
                return compile_matrix(self)
        except (FloatingPointError, OverflowError) as error:
            raise ValueError(
                "planning coefficients exceed float64 range"
            ) from error

    def _financial_variables(self, variables):
        scales = np.where(self._lots > 0, self._lots, 1.0)
        zero = 0 * next(iter(variables.values()))
        trades, holdings = [], []
        for k in range(len(self._nodes)):
            trades.append(
                [
                    float(scales[k, i])
                    * (
                        variables.get(f"buy_{k}_{i}", zero)
                        - variables.get(f"sell_{k}_{i}", zero)
                    )
                    for i in range(len(self._ids))
                ]
            )
            holdings.append(
                [variables[f"holding_{k}_{i}"] for i in range(len(self._ids))]
            )
        result = {
            "trades": pd.DataFrame(
                trades, index=self.node_ids, columns=self.asset_ids
            ),
            "holdings": pd.DataFrame(
                holdings, index=self.node_ids, columns=self.asset_ids
            ),
            "cash_balances": pd.Series(
                [variables[f"cash_{k}"] for k in range(len(self._nodes))],
                index=self.node_ids,
                name="cash",
                dtype=object,
            ),
        }
        if self._funding:
            result["draws"] = pd.Series(
                {
                    identifier: float(source["lot_size"] or 1)
                    * variables[f"funding_{i}"]
                    for i, (identifier, source) in enumerate(
                        self._funding.items()
                    )
                },
                name="principal",
                dtype=object,
            )
        if self._facilities:
            from ..treasury._facilities import financial_variables

            principals = {
                key: source["principal"]
                for key, source in self._existing_debt.items()
            }
            if self._funding:
                principals.update(result["draws"].to_dict())
            result["facility_utilization"] = financial_variables(
                self._facilities,
                self._facility_active(),
                principals,
                self._nodes,
                "node",
                zero,
            )
        return result

    def to_model(self, *, return_variables=False):
        """Return the same financial LP/MILP as an Opt algebraic Model.

        return_variables=True also returns node/asset signed trades and
        holdings, node cash_balances and contract-ID draws where configured.
        Expressions use actual quantities and currency amounts, not lots.
        Configured facility_utilization uses (node, facility) labels and
        includes reserved utilization in each facility's capacity currency.
        """
        from .._solvers._expressions import export_model, linear_model

        return export_model(
            linear_model(self.to_matrix()), self, return_variables
        )

    def _compile_opt(self, *, mode):
        return self.to_model() if mode == "platform" else self.to_matrix()

    def to_cvxpy(self):
        """Return a CVXPY problem and financial expressions.

        trades and holdings are node-by-asset actual quantities;
        cash_balances uses nodes and draws uses funding contract IDs.
        Supports complete linear/PWL or monotone conic formulations.
        Configured facility_utilization uses (node, facility) labels and
        includes reserved utilization in each facility's capacity currency.
        """
        problem, variables = self._compile_cvxpy()
        return problem, self._financial_variables(variables)

    def _compile_cvxpy(self):
        from .._solvers.cvxpy import linear_problem

        if self._has_nonlinear_impact:
            if not self._cash_monotone:
                raise ValueError(
                    "cash ceilings require an exact cost graph; use to_scip()"
                )
            from ._planning_impact import compile_cvxpy

            return compile_cvxpy(self)
        return linear_problem(self.to_matrix())

    def to_scip(self):
        """Return a native PySCIPOpt model and financial expressions.

        Cash ceilings use exact nonlinear graphs. Otherwise a monotone cost
        epigraph preserves the financial feasible set under cash replay.
        The native representation may be nonconvex QCQP/MINLP.
        trades/holdings use node-by-asset actual quantities, cash_balances
        uses nodes, and draws retains funding IDs and actual principal.
        Configured facility_utilization uses (node, facility) labels and
        includes reserved utilization in each facility's capacity currency.
        Export is offline; execution through Finance requires an Opt Client.
        """
        native, variables = self._compile_scip()
        return native, self._financial_variables(variables)

    def _compile_scip(self):
        from ._planning_impact import compile_scip

        self._check()
        try:
            with np.errstate(over="raise", invalid="raise", divide="raise"):
                return compile_scip(self)
        except (FloatingPointError, OverflowError) as error:
            raise ValueError(
                "impact coefficients exceed float64 range"
            ) from error

    def evaluate(self, trades, *, draws=None, tolerance=1e-7):
        """Rebuild shares, cash, costs, terminal risk and hard limits offline.

        trades is node-by-asset signed quantities. One shared decision per
        information node is required; no future-case-specific trade exists.
        draws supplies every funding contract's principal by ID or in
        insertion order. Required when funding opportunities are configured;
        zero draws must be explicit. Opening debt needs no draw decision.

        Replay and constraint checks retain original financial amounts before
        rounding. Reported quantities and monetary tables use float64;
        residuals can expose differences hidden by those rounded totals.
        """
        from ._planning_evaluate import evaluate

        self._check()
        try:
            with np.errstate(over="raise", invalid="raise", divide="raise"):
                return evaluate(self, trades, draws=draws, tolerance=tolerance)
        except (FloatingPointError, OverflowError) as error:
            raise ValueError(
                "planning calculations exceed float64 range"
            ) from error

    def _evaluate_solution(self, solution, *, tolerance):
        values = np.zeros(self._prices.shape)
        buy, sell = self._capacities()
        for k, i in np.ndindex(values.shape):
            scale = self._lots[k, i] or 1.0
            if buy[k, i] > 0:
                values[k, i] += lot_quantities(
                    scalar(solution[f"buy_{k}_{i}"], "buy"), scale
                )
            if sell[k, i] > 0:
                values[k, i] -= lot_quantities(
                    scalar(solution[f"sell_{k}_{i}"], "sell"), scale
                )
        draws = [
            lot_quantities(
                scalar(solution[f"funding_{i}"], "funding draw"),
                source["lot_size"] or 1.0,
            )
            for i, source in enumerate(self._funding.values())
        ]
        return self.evaluate(values, draws=draws, tolerance=tolerance)

    def _specification(self):
        from .._model_io import _trading
        from .._value_io import encode_arguments

        inputs, settings = _trading(self)
        return {
            "model": "TradingModel",
            "objective": self._objective,
            "inputs": encode_arguments(inputs),
            "configuration": [
                {"method": method, "arguments": encode_arguments(arguments)}
                for method, arguments in settings
            ],
        }
