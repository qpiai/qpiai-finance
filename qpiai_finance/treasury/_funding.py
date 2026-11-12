"""Funding contracts, account balances and dated liquidity requirements."""

from copy import deepcopy
from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd

from .._serialization import portable
from .._validation import confidence as checked_confidence
from .._validation import (
    copy_frame,
    copy_index,
    identifiers,
    instant,
    lot_capacity,
    numeric,
    same_labels,
    scalar,
)
from ..cashflows import (
    _bullet_loan_terms,
    _currency,
    _date,
    _dated_values,
    _dates,
    _loan_amounts,
    _loan_fixed_charge,
    _period_vector,
    _reporting_rates,
)


@dataclass
class _Funding:
    account: int | str
    draw_at: int | str | pd.Timestamp
    repay_at: int | str | pd.Timestamp
    maximum: float
    interest: float
    fee: float
    fixed_fee: float
    minimum: float
    lot_size: float | None


@dataclass
class _ExistingDebt:
    account: int | str
    principal: float
    repay_at: int | str | pd.Timestamp
    interest: float


@dataclass
class _Transfer:
    from_account: int | str
    to_account: int | str
    at: int | str | pd.Timestamp
    maximum: float
    exchange_rate: float
    fee: float


@dataclass
class _Investment:
    account: int | str
    purchase_at: int | str | pd.Timestamp
    price: float
    cash_flows: np.ndarray
    lower: float
    upper: float
    lot_size: float | None


class FundingModel:
    """Plan account funding and currency transfers under cash obligations.

    balances is an account-indexed DataFrame with currency and cash columns.
    cash_flows has account, date and signed amount columns, one row per
    contractual flow. Opening cash is available immediately before as_of
    events. dates is a strictly increasing daily planning grid beginning
    at as_of; every flow, draw, transfer and repayment must lie on it.

    Within each date, flows are netted simultaneously. This is bucket-end
    liquidity planning, not an intraday payment settlement guarantee.
    Cash cannot be negative. Borrowing is represented by explicit funding
    contracts with repayments within the planning horizon.

    Supply exactly one of dates or a ScenarioTree. With tree, cash_flows
    uses node instead of date; account grids have node rows. A decision at
    one observed node is shared by every case passing through it. Each
    descendant maturity node receives its contractual repayment; alternative
    branches never share cash. The tree clock begins exactly at as_of.
    deposit_returns apply from parent to node; root returns are zero.
    discount_factors value expense in each account's currency before the
    fixed as-of reporting FX conversion. Root discount factors equal one.
    Both grids may be scalars, labeled DataFrames or ordered arrays.

    Expected cost is the default and requires explicit case probabilities.
    minimize_worst_case_cost permits probability-free stress planning.
    minimize_expected_shortfall and limit_expected_shortfall control the
    upper cost tail under explicit probabilities and independent confidences.
    Hard cash, debt and facility limits apply at every node regardless of
    probability. Reporting FX, transfer quotes and facility FX are separate.
    add_investment includes bounded purchases and their supplied later cash
    flows in those same native-account equations. Purchase cash and proceeds
    remain distinct from the funding-expense objective. limit_exposure
    applies supplied capital/sensitivity/value coefficients to the actual
    investment, live-debt and closing-cash book at each date or node.
    """

    _objective = "funding_cost"
    _needs_external = False

    def __init__(
        self,
        cash_flows,
        *,
        balances,
        as_of,
        dates=None,
        tree=None,
        reporting_currency=None,
        fx_rates=None,
        deposit_returns=0.0,
        discount_factors=1.0,
    ):
        if not isinstance(balances, pd.DataFrame):
            raise TypeError("balances must be a DataFrame")
        if not balances.columns.is_unique or set(balances.columns) != {
            "currency", "cash"
        }:
            raise ValueError(
                "balances requires unique currency and cash columns"
            )
        self._ids = identifiers(balances.index, "account IDs")
        self._currencies = pd.Series(
            [_currency(value) for value in balances.currency],
            index=copy_index(self._ids),
        )
        self._opening = numeric(
            balances.cash.to_numpy(), "opening cash", ndim=1
        )
        if np.any(self._opening < 0):
            raise ValueError(
                "opening cash must be nonnegative; model debt separately"
            )
        if (dates is None) == (tree is None):
            raise ValueError("provide exactly one of dates or tree")
        self._tree = None
        if tree is None:
            self._dates = _dates(dates, "dates", ordered=True)
            self._periods = self._dates
            self._parents = np.arange(len(self._periods)) - 1
            self._as_of = _date(as_of, "as_of")
        else:
            from ..scenarios import ScenarioTree

            if not isinstance(tree, ScenarioTree):
                raise TypeError("tree must be a ScenarioTree")
            self._tree = deepcopy(tree)
            self._dates = copy_index(tree._times)
            self._periods = tree.node_ids
            self._parents = tree._parents.copy()
            parse = _date if self._dates.tz is None else instant
            self._as_of = parse(as_of, "as_of")
        if self._dates[0] != self._as_of:
            raise ValueError("planning times must begin at as_of")
        self._axis = "date" if self._tree is None else "node"
        self._cost_measure = "expected"
        self._confidence = 0.95
        self._tail_limit = None
        if not isinstance(cash_flows, pd.DataFrame):
            raise TypeError("cash_flows must be a DataFrame")
        if not cash_flows.columns.is_unique or set(cash_flows.columns) != {
            "account", self._axis, "amount"
        }:
            raise ValueError(
                f"cash_flows requires unique account, {self._axis} "
                "and amount columns"
            )
        if len(cash_flows):
            identifiers(cash_flows.index, "cash-flow IDs")
            identifiers(cash_flows.account, "cash-flow accounts", unique=False)
        flows = copy_frame(cash_flows)
        if not flows.account.isin(self._ids).all():
            raise ValueError("cash flows contain unknown account IDs")
        if self._tree is None:
            flows["date"] = [
                _date(value, "cash-flow date") for value in flows.date
            ]
        elif len(flows):
            identifiers(flows.node, "cash-flow nodes", unique=False)
        if not flows[self._axis].isin(self._periods).all():
            raise ValueError(
                f"cash-flow {self._axis}s must belong to the planning grid"
            )
        flows["amount"] = numeric(
            flows.amount.tolist(), "cash-flow amounts", ndim=1
        )
        self._flows = flows
        currencies = self._currencies.drop_duplicates()
        if reporting_currency is None:
            if len(currencies) != 1:
                raise ValueError(
                    "multiple currencies require reporting_currency"
                )
            reporting_currency = currencies.iloc[0]
        self._reporting_currency = _currency(reporting_currency)
        self._fx = _reporting_rates(currencies, reporting_currency, fx_rates)
        self._returns = self._values(deposit_returns, "deposit_returns")
        if np.ndim(deposit_returns) == 0:
            self._returns[0] = 0
        if np.any(self._returns < -1) or np.any(self._returns[0] != 0):
            raise ValueError(
                "deposit returns must be at least -1, with zero at as_of"
            )
        self._discount = self._values(discount_factors, "discount_factors")
        if np.any(self._discount <= 0) or np.any(self._discount[0] != 1):
            raise ValueError(
                "discount factors must be positive, with one at as_of"
            )
        shape = (len(self._periods), len(self._ids))
        self._cash_lower = np.zeros(shape)
        self._cash_upper = np.full(shape, np.inf)
        self._debt_upper = np.full(shape, np.inf)
        self._funding = {}
        self._existing_debt = {}
        self._transfers = {}
        self._investments = {}
        self._facilities = {}
        self._exposure_limits = {}

    @property
    def account_ids(self):
        return copy_index(self._ids)

    @property
    def investment_ids(self):
        """Purchase opportunity IDs in coefficient-array order."""
        return pd.Index(list(self._investments), name="investment_id")

    @property
    def funding_ids(self):
        """New and opening-debt IDs in coefficient-array order."""
        return pd.Index(
            list(self._funding) + list(self._existing_debt), name="funding_id"
        )

    @property
    def dates(self):
        """Ordered stage times, including aware instants for an aware tree."""
        return copy_index(self._dates)

    @property
    def tree(self):
        """Detached information tree, or None for a dated plan."""
        return deepcopy(self._tree)

    @property
    def node_ids(self):
        """Information node IDs; unavailable for a dated plan."""
        if self._tree is None:
            raise ValueError("a dated funding plan has no information nodes")
        return copy_index(self._periods)

    def _values(self, values, name):
        if self._tree is None:
            return _dated_values(values, self._periods, self._ids, name)
        if isinstance(values, pd.DataFrame):
            labels = identifiers(values.index, f"{name} nodes")
            same_labels(labels, self._periods, f"{name} nodes")
            same_labels(values.columns, self._ids, f"{name} accounts")
            values = values.reindex(
                index=self._periods, columns=self._ids
            ).to_numpy()
        elif np.ndim(values) == 0:
            values = np.full(
                (len(self._periods), len(self._ids)), scalar(values, name)
            )
        array = numeric(values, name, ndim=2)
        if array.shape != (len(self._periods), len(self._ids)):
            raise ValueError(
                f"{name} must have shape "
                f"{(len(self._periods), len(self._ids))}"
            )
        return array

    def _schedule(self, draw_at, repay_at):
        if self._tree is None:
            start = 0 if draw_at is None else self._periods.get_loc(draw_at)
            end = self._periods.get_loc(repay_at)
            return start, range(start, end), [end]
        from ._contracts import schedule

        node = self._tree.root if draw_at is None else draw_at
        live, due = schedule(self._tree, node, repay_at)
        return self._tree._position(node), live, due

    def _contract_arguments(self, source):
        arguments = asdict(source)
        for internal, dated, adaptive in (
            ("purchase_at", "purchase_date", "purchase_node"),
            ("draw_at", "draw_date", "draw_node"),
            ("repay_at", "repayment_date", "repayment_stage"),
            ("at", "date", "node"),
        ):
            if internal in arguments:
                key = dated if self._tree is None else adaptive
                arguments[key] = arguments.pop(internal)
        return arguments

    def minimize_expected_cost(self):
        """Minimize expected discounted expense under supplied case weights.

        Scenario probabilities are required for an adaptive plan. Reporting
        FX values expense; explicit transfers alone exchange cash currencies.
        """
        if self._tree is not None and self._tree._probabilities is None:
            raise ValueError("expected cost requires scenario probabilities")
        self._cost_measure = "expected"
        return self

    def minimize_worst_case_cost(self):
        """Minimize the largest complete-path discounted funding expense.

        All supplied cases count, including zero-probability stress cases.
        No scenario probabilities are required.
        """
        self._cost_measure = "worst_case"
        return self

    def _require_probabilities(self):
        if self._tree is None or self._tree._probabilities is None:
            raise ValueError(
                "expected shortfall requires a scenario tree "
                "with probabilities"
            )

    def minimize_expected_shortfall(self, *, confidence=0.95):
        """Minimize upper-tail mean discounted funding expense.

        Costs are complete-path interest, origination and transfer fees in
        reporting currency. Principal repayment is excluded from expense.
        A scenario tree with explicit probabilities is required. Signed
        costs are preserved; zero-probability cases do not enter this risk
        measure. Hard cash/debt/facility limits still apply to every node.
        confidence must be strictly between zero and one.
        """
        self._require_probabilities()
        level = checked_confidence(confidence)
        self._cost_measure = "expected_shortfall"
        self._confidence = level
        return self

    def limit_expected_shortfall(self, maximum, *, confidence=0.95):
        """Cap funding-cost ES in reporting currency under any objective.

        The cap uses its own confidence, independent of the objective's.
        Negative caps require a sufficiently negative upper-tail expense.
        Supplied case probabilities are required; no weights are inferred.
        confidence must be strictly between zero and one.
        Reusing this method replaces the cap after complete validation.
        """
        self._require_probabilities()
        cap = scalar(maximum, "maximum expected shortfall")
        level = checked_confidence(confidence)
        self._tail_limit = cap, level
        return self

    def _check_cost_measure(self):
        if self._cost_measure == "expected":
            if self._tree is not None and self._tree._probabilities is None:
                raise ValueError(
                    "expected cost requires scenario probabilities; "
                    "choose minimize_worst_case_cost for a stress tree"
                )

    @property
    def reporting_currency(self):
        return self._reporting_currency

    @property
    def _objective_unit(self):
        return self._reporting_currency

    @property
    def _mixed_integer(self):
        return any(
            source.lot_size is not None
            or source.minimum > 0
            or source.fixed_fee > 0
            for source in self._funding.values()
        ) or any(
            source.lot_size is not None
            for source in self._investments.values()
        )

    @property
    def _problem_class(self):
        return "MILP" if self._mixed_integer else "LP"

    def _account(self, account):
        identifiers([account], "account")
        if account not in self._ids:
            raise ValueError(f"unknown account: {account!r}")
        return self._ids.get_loc(account)

    def _planning_date(self, value, name):
        value = _date(value, name)
        if value not in self._dates:
            raise ValueError(f"{name} must belong to the planning dates")
        return value

    def add_funding(
        self,
        funding_id,
        *,
        account,
        draw_date=None,
        repayment_date=None,
        draw_node=None,
        repayment_stage=None,
        maximum,
        interest=0.0,
        fee=0.0,
        fixed_fee=0.0,
        minimum=0.0,
        lot_size=None,
    ):
        """Add a bounded bullet funding opportunity in the account currency.

        interest is the total term interest fraction of principal, paid
        at repayment, not an annual rate. fee is a principal fraction paid
        at draw. fixed_fee is an origination charge in account currency.
        minimum permits either zero borrowing or at least that amount.
        lot_size restricts principal to integer multiples. Fixed charges
        require a positive minimum or lot to link activation to a real draw.
        For an adaptive plan, use draw_node and repayment_stage instead of
        dates. Borrowing is conditional on reaching draw_node; repayment
        occurs on each descendant at the supplied stage.
        """
        identifiers([funding_id], "funding_id")
        if funding_id in self._funding or funding_id in self._existing_debt:
            raise ValueError("funding_id must be unique")
        self._account(account)
        if self._tree is None:
            if draw_node is not None or repayment_stage is not None:
                raise ValueError("dated funding uses draw_date/repayment_date")
            start = self._planning_date(draw_date, "draw_date")
            end = self._planning_date(repayment_date, "repayment_date")
            if end <= start:
                raise ValueError("repayment_date must follow draw_date")
        else:
            from ._contracts import stage_position

            if draw_date is not None or repayment_date is not None:
                raise ValueError(
                    "adaptive funding uses draw_node/repayment_stage"
                )
            k = self._tree._position(draw_node)
            depth = stage_position(self._tree, repayment_stage)
            if depth <= self._tree._depths[k]:
                raise ValueError("repayment_stage must follow the draw stage")
            start, end = self._periods[k], self._tree._stages[depth]
        terms = _bullet_loan_terms(
            maximum=maximum,
            interest=interest,
            fee=fee,
            fixed_fee=fixed_fee,
            minimum=minimum,
            lot_size=lot_size,
        )
        self._funding[funding_id] = _Funding(account, start, end, **terms)
        return self

    def add_existing_debt(
        self,
        debt_id,
        *,
        account,
        principal,
        repayment_date=None,
        repayment_stage=None,
        interest=0.0,
    ):
        """Declare opening debt without adding its historical draw to cash.

        Principal is outstanding at as_of and repaid on repayment_date.
        interest is the remaining interest payment as a principal fraction,
        not an annual rate. Both payments must fall within this horizon.
        Adaptive plans use repayment_stage instead of repayment_date and
        repay opening debt on every case reaching that maturity stage.
        """
        identifiers([debt_id], "debt_id")
        if debt_id in self._existing_debt or debt_id in self._funding:
            raise ValueError("debt and funding IDs must be unique")
        self._account(account)
        principal = scalar(principal, "principal", minimum=0)
        if principal == 0:
            raise ValueError("existing debt principal must be positive")
        if self._tree is None:
            if repayment_stage is not None:
                raise ValueError("dated debt uses repayment_date")
            end = self._planning_date(repayment_date, "repayment_date")
        else:
            from ._contracts import stage_position

            if repayment_date is not None:
                raise ValueError("adaptive debt uses repayment_stage")
            depth = stage_position(self._tree, repayment_stage)
            end = self._tree._stages[depth]
        self._existing_debt[debt_id] = _ExistingDebt(
            account,
            principal,
            end,
            scalar(interest, "interest", minimum=-1),
        )
        return self

    def add_transfer(
        self,
        transfer_id,
        *,
        from_account,
        to_account,
        date=None,
        node=None,
        maximum,
        exchange_rate=None,
        fee=0.0,
    ):
        """Allow a dated transfer, optionally with an explicit FX quote.

        The decision is an amount in the source currency. The destination
        receives exchange_rate times that amount. fee is an additional
        source-currency fraction, debited from the sending account.
        Reporting FX rates do not authorize transfers. Adaptive plans use
        node instead of date; that transfer is available only at that node.
        """
        identifiers([transfer_id], "transfer_id")
        if transfer_id in self._transfers:
            raise ValueError("transfer_id must be unique")
        self._account(from_account)
        self._account(to_account)
        if from_account == to_account:
            raise ValueError("a transfer requires different accounts")
        if self._tree is None:
            if node is not None:
                raise ValueError("dated transfers use date")
            when = self._planning_date(date, "transfer date")
        else:
            if date is not None:
                raise ValueError("adaptive transfers use node")
            when = self._periods[self._tree._position(node)]
        same_currency = (
            self._currencies[from_account] == self._currencies[to_account]
        )
        if exchange_rate is None:
            if not same_currency:
                raise ValueError(
                    "cross-currency transfers require exchange_rate"
                )
            exchange_rate = 1.0
        exchange_rate = scalar(exchange_rate, "exchange_rate", minimum=0)
        if exchange_rate == 0 or (same_currency and exchange_rate != 1):
            raise ValueError(
                "exchange_rate must be positive; "
                "same-currency transfers require one"
            )
        self._transfers[transfer_id] = _Transfer(
            from_account,
            to_account,
            when,
            scalar(maximum, "maximum", minimum=0),
            exchange_rate,
            scalar(fee, "fee", minimum=0),
        )
        return self

    def add_investment(
        self,
        investment_id,
        *,
        account,
        price,
        cash_flows,
        upper,
        lower=0.0,
        lot_size=None,
        purchase_date=None,
        purchase_node=None,
    ):
        """Add a bounded purchase with supplied per-unit future cash flows.

        price is positive all-in purchase cash per instrument unit in the
        account's currency. cash_flows supplies signed native-currency cash
        per unit on the complete date/node grid, as a labeled Series/mapping
        or ordered vector. Payouts must be zero at/before purchase and on
        other information histories. Later negative flows are capital calls.

        lower/upper bound actual purchased units; lower is a mandatory
        minimum position, not a conditional minimum trade. lot_size permits
        only whole lots. With a tree, purchase_node makes this opportunity
        conditional on reaching that observed node. Cases sharing it share
        one purchase quantity and its applicable descendant cash flows.

        Purchase outlay and future flows enter native cash conservation.
        The objective continues to measure funding interest and fees.
        investment_id identifies this purchase opportunity; use distinct IDs
        for separate conditional purchases, even of the same instrument.
        """
        identifiers([investment_id], "investment_id")
        if investment_id in self._investments:
            raise ValueError("investment_id must be unique")
        self._account(account)
        price = scalar(price, "price", minimum=0)
        if price == 0:
            raise ValueError("price must be positive")
        upper = scalar(upper, "upper", minimum=0)
        lower = scalar(lower, "lower", minimum=0, maximum=upper)
        if lot_size is not None:
            lot_size = scalar(lot_size, "lot_size", minimum=0)
            if lot_size == 0:
                raise ValueError("lot_size must be positive")
            lot_capacity(upper, lot_size)
        if self._tree is None:
            if purchase_node is not None:
                raise ValueError("dated investments use purchase_date")
            when = self._planning_date(purchase_date, "purchase_date")
            start = self._periods.get_loc(when)
            eligible = np.arange(len(self._periods)) > start
        else:
            if purchase_date is not None:
                raise ValueError("adaptive investments use purchase_node")
            start = self._tree._position(purchase_node)
            when = self._periods[start]
            _, live, due = self._schedule(when, self._tree._stages[-1])
            eligible = np.zeros(len(self._periods), dtype=bool)
            eligible[live] = True
            eligible[due] = True
            eligible[start] = False
        flows = _period_vector(
            cash_flows, self._periods, "investment cash_flows", broadcast=False
        )
        if np.any(flows[~eligible] != 0):
            raise ValueError(
                "investment cash flows must follow purchase "
                "on its realized history"
            )
        self._investments[investment_id] = _Investment(
            account, when, price, flows, lower, upper, lot_size
        )
        return self

    def limit_cash(self, *, minimum=0.0, maximum=None):
        """Set date/node account cash buffers and bounds in native currency."""
        lower = self._values(minimum, "minimum cash")
        upper = (
            np.full(lower.shape, np.inf)
            if maximum is None
            else self._values(maximum, "maximum cash")
        )
        if np.any(lower < 0) or np.any(lower > upper):
            raise ValueError("cash bounds require 0 <= minimum <= maximum")
        self._cash_lower, self._cash_upper = lower, upper
        return self

    def limit_debt(self, *, maximum):
        """Limit native principal after each date/node draw and repayment."""
        limits = self._values(maximum, "maximum debt")
        if np.any(limits < 0):
            raise ValueError("maximum debt must be nonnegative")
        self._debt_upper = limits
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
        """Cap shared outstanding principal for explicitly named contracts.

        funding_ids names already added funding opportunities/existing debt.
        Membership may overlap to represent aggregate limits and sublimits.
        maximum and reserved are nonnegative scalars, date/node-indexed Series
        or mappings, or ordered vectors in facility currency. reserved is
        utilization outside this model; it does not move cash. A reserved
        amount exceeding capacity makes the plan infeasible.

        FX quotes value each principal currency in facility-currency units.
        Supply a currency-indexed Series/mapping/vector for fixed quotes or
        a date/node-by-currency DataFrame/array. A scalar quote requires
        one native currency. Same-currency quotes equal one; cross-currency
        valuation requires explicit quotes and never creates a cash transfer.

        Principal counts on [draw_date, repayment_date), including existing
        debt until repayment. Capacity is checked after that date's draws
        and repayments. It is not lifetime cumulative borrowing, an intraday
        guarantee or inferred legal rollover permission. Reusing facility_id
        replaces its limit atomically; other facilities remain unchanged.
        With a tree, only principal drawn on that node's history counts;
        all nodes are checked, including zero-probability stress nodes.
        """
        from ._facilities import prepare

        currencies = {
            key: self._currencies[source.account]
            for contracts in (self._funding, self._existing_debt)
            for key, source in contracts.items()
        }
        facility = prepare(
            facility_id,
            funding_ids,
            periods=self._periods,
            contract_currencies=currencies,
            maximum=maximum,
            currency=currency,
            fx_rates=fx_rates,
            reserved=reserved,
        )
        self._facilities[facility_id] = facility
        return self

    def limit_exposure(
        self,
        exposure_id,
        *,
        unit,
        investment_coefficients=None,
        funding_coefficients=None,
        cash_coefficients=None,
        external_exposure=0.0,
        lower=None,
        upper=None,
    ):
        """Bound one supplied financial exposure at every date or node.

        Coefficients use unit per purchased instrument unit, outstanding
        native funding principal or native closing cash. Signed coefficients
        permit supplied sensitivity matching and net-value floors; supplied
        additive capital charges permit capital budgets. No pricing, FX,
        risk-weight calibration or regulatory classification is inferred.

        Series/mappings identify fixed coefficients for named members;
        DataFrames have complete date/node rows and selected member columns.
        Scalars/arrays use all current investment_ids, funding_ids or
        account_ids in their public order. Purchases count only on their
        realized post-purchase history; debt counts before its repayment.
        Supply zero investment coefficients after derecognition: cash-flow
        receipt alone does not determine remaining instrument ownership.

        external_exposure is signed outside-book exposure, with lower/upper
        bounds in the same explicit unit. Scalars or full period vectors
        are accepted. Outside liability values must exclude amounts already
        represented in modeled balances. Equal bounds impose matching.
        Zero-probability and probability-free stress nodes remain hard.

        Reusing exposure_id replaces its mandate after validation. Members
        are fixed at configuration; adding positions does not extend an old
        mandate. Configure again to include the new positions.
        """
        from ._balance_sheet import prepare

        block = prepare(
            self,
            exposure_id,
            unit=unit,
            investment_coefficients=investment_coefficients,
            funding_coefficients=funding_coefficients,
            cash_coefficients=cash_coefficients,
            external_exposure=external_exposure,
            lower=lower,
            upper=upper,
        )
        self._exposure_limits[exposure_id] = block
        return self

    def _facility_active(self):
        active = {
            key: self._schedule(None, source.repay_at)[1]
            for key, source in self._existing_debt.items()
        }
        active.update(
            {
                key: self._schedule(source.draw_at, source.repay_at)[1]
                for key, source in self._funding.items()
            }
        )
        return active

    def _specification(self):
        from .._value_io import encode
        from ._balance_sheet import configuration as exposure_configuration
        from ._facilities import configuration

        return portable(
            {
                "model": "FundingModel",
                "tree": None if self._tree is None else encode(self._tree),
                "as_of": self._as_of,
                "dates": self._dates,
                "account_ids": self._ids,
                "currencies": self._currencies,
                "opening_cash": self._opening,
                "cash_flows": self._flows,
                "deposit_returns": self._returns,
                "discount_factors": self._discount,
                "reporting_currency": self._reporting_currency,
                "reporting_fx_rates": self._fx,
                "cash_lower": self._cash_lower,
                "cash_upper": self._cash_upper,
                "debt_upper": self._debt_upper,
                "facilities": [
                    {"id": key, **terms}
                    for key, terms in configuration(
                        self._facilities, self._periods
                    )
                ],
                "funding": [
                    {"id": key, **self._contract_arguments(value)}
                    for key, value in self._funding.items()
                ],
                "existing_debt": [
                    {"id": key, **self._contract_arguments(value)}
                    for key, value in self._existing_debt.items()
                ],
                "investments": [
                    {"id": key, **self._contract_arguments(value)}
                    for key, value in self._investments.items()
                ],
                "transfers": [
                    {"id": key, **self._contract_arguments(value)}
                    for key, value in self._transfers.items()
                ],
                "objective": self._objective,
                "exposure_limits": [
                    {"id": key, **arguments}
                    for key, arguments in exposure_configuration(self)
                ],
                "cost_measure": self._cost_measure,
                "confidence": (
                    self._confidence
                    if self._cost_measure == "expected_shortfall"
                    else None
                ),
                "expected_shortfall_limit": self._tail_limit,
                "timing_convention": "simultaneous_cash_flows_within_bucket",
            }
        )

    def _financial_variables(self, variables):
        draws = pd.Series(
            {
                identifier: float(source.lot_size or 1)
                * variables[f"funding_{i}"]
                for i, (identifier, source) in enumerate(self._funding.items())
            },
            name="principal",
            dtype=object,
        )
        transfers = pd.Series(
            {
                identifier: variables[f"transfer_{i}"]
                for i, identifier in enumerate(self._transfers)
            },
            name="sent",
            dtype=object,
        )
        cash = pd.Series(
            [
                variables[f"cash_{t}_{a}"]
                for t in range(len(self._periods))
                for a in range(len(self._ids))
            ],
            index=pd.MultiIndex.from_product(
                [copy_index(self._periods), copy_index(self._ids)],
                names=[self._axis, "account"],
            ),
            name="cash",
            dtype=object,
        )
        result = {
            "draws": draws,
            "transfers": transfers,
            "cash_balances": cash,
        }
        if self._investments:
            result["investments"] = pd.Series(
                {
                    key: float(source.lot_size or 1)
                    * variables[f"investment_{i}"]
                    for i, (key, source) in enumerate(
                        self._investments.items()
                    )
                },
                name="quantity",
                dtype=object,
            )
        if self._tree is not None:
            from ._funding_compile import case_costs, expense_terms

            active = {
                key: variables[f"active_{i}"]
                if source.minimum > 0 or source.fixed_fee > 0
                else 0
                for i, (key, source) in enumerate(self._funding.items())
            }
            charges = {}
            for i, (key, source) in enumerate(self._funding.items()):
                principal = variables.get(f"funding_{i}_principal", draws[key])
                _, _, fees, interest = _loan_amounts(
                    principal, source.interest, source.fee, source.fixed_fee,
                    active=active[key],
                )
                if f"funding_{i}_variable_fee" in variables:
                    fees = variables[f"funding_{i}_variable_fee"] + (
                        _loan_fixed_charge(
                            principal, source.fixed_fee, active[key]
                        )
                    )
                charges[key] = (
                    fees,
                    variables.get(f"funding_{i}_interest", interest),
                )
            expenses, fixed = expense_terms(self, charges, transfers)
            nodes = [sum(terms) for terms in expenses]
            costs = case_costs(self._tree, nodes)
            if any(fixed):
                costs = [
                    cost + float(constant)
                    for cost, constant in zip(
                        costs, case_costs(self._tree, fixed)
                    )
                ]
            result["scenario_costs"] = pd.Series(
                costs,
                index=self._tree.scenario_ids,
                name="discounted_funding_cost",
                dtype=object,
            )
        if self._facilities:
            from ._facilities import financial_variables

            principals = {
                key: source.principal
                for key, source in self._existing_debt.items()
            }
            principals.update(draws.to_dict())
            result["facility_utilization"] = financial_variables(
                self._facilities,
                self._facility_active(),
                principals,
                self._periods,
                self._axis,
                0 * next(iter(variables.values())),
            )
        if self._exposure_limits:
            from fractions import Fraction

            from ._balance_sheet import terms

            positions = {
                "investments": result.get("investments", {}),
                "funding": draws,
                "cash": {
                    key: [
                        variables[f"cash_{k}_{a}"]
                        for k in range(len(self._periods))
                    ]
                    for a, key in enumerate(self._ids)
                },
            }
            values, labels = [], []
            zero = 0 * next(iter(variables.values()))
            try:
                for key, block in self._exposure_limits.items():
                    for k, period in enumerate(self._periods):
                        fixed = (
                            Fraction(block["external"][k])
                            + block["fixed_funding"][k]
                        )
                        values.append(
                            sum(terms(block, k, positions), zero)
                            + float(fixed)
                        )
                        labels.append((period, key))
            except OverflowError as error:
                raise ValueError("exposures exceed float64 range") from error
            result["exposures"] = pd.Series(
                values,
                index=pd.MultiIndex.from_tuples(
                    labels, names=[self._axis, "exposure"]
                ),
                name="exposure",
                dtype=object,
            )
        return result

    def to_model(self, *, return_variables=False):
        """Return a detached Opt LP/MILP.

        return_variables=True also returns draws by funding ID, transfers
        by transfer ID and cash_balances by (date, account) or (node, account).
        Draws are actual principal; transfers use the sending currency,
        and cash uses each account's native currency. No FX is inferred.
        Configured facility_utilization uses (date, facility) or
        (node, facility) labels, including reserved utilization in each
        facility's capacity currency. Adaptive scenario_costs uses case IDs
        and reporting-currency discounted interest and fees. It supports
        direct custom composition with risk.expected_shortfall_epigraph.
        Configured investments exposes actual purchased units by investment
        opportunity ID, with purchase and future cash in the same balances.
        Configured exposures use (date/node, exposure) labels and the
        declared exposure unit, including signed outside-book amounts.
        """
        from .._solvers._expressions import export_model
        from ._funding_compile import compile_model

        try:
            with np.errstate(over="raise", invalid="raise"):
                model = compile_model(self)
        except (FloatingPointError, OverflowError) as error:
            raise ValueError(
                "funding coefficients exceed float64 range"
            ) from error
        return export_model(model, self, return_variables)

    def _compile_cvxpy(self):
        from .._solvers.cvxpy import linear_problem

        return linear_problem(self.to_model())

    def to_cvxpy(self):
        """Return a CVXPY problem and financial expressions.

        draws and transfers retain contract IDs; cash_balances is indexed
        by (date, account) or (node, account). Values use native currency,
        not lot counts or reporting-currency conversions.
        Configured facility_utilization uses (date, facility) or
        (node, facility) labels, including reserved utilization in each
        facility's capacity currency. Adaptive scenario_costs uses case IDs
        and reporting-currency discounted interest and fees. It supports
        direct custom composition with risk.expected_shortfall_epigraph.
        Configured investments exposes actual purchased units by investment
        opportunity ID, with purchase and future cash in the same balances.
        Configured exposures use (date/node, exposure) labels and the
        declared exposure unit, including signed outside-book amounts.
        """
        problem, variables = self._compile_cvxpy()
        return problem, self._financial_variables(variables)

    def evaluate(
        self, draws=None, transfers=None, *, investments=None, tolerance=1e-7
    ):
        """Reconstruct the source-currency funding and cash schedule.

        Cash and debt bounds use original amounts before rounding. Reported
        balances and monetary tables use float64; constraint residuals retain
        differences that those rounded balances may not display. Supply
        complete investments when purchase opportunities are configured.
        """
        from ._funding_evaluate import evaluate

        return evaluate(
            self,
            draws,
            transfers,
            investments=investments,
            tolerance=tolerance,
        )

    def _evaluate_solution(self, solution, *, tolerance):
        from ._funding_evaluate import evaluate_solution

        return evaluate_solution(self, solution, tolerance=tolerance)
