"""Accounts, payment windows and explicitly permitted settlement mechanisms."""

from bisect import bisect_left, bisect_right
from fractions import Fraction

import numpy as np
import pandas as pd

from .._serialization import portable
from .._validation import (
    copy_index,
    identifiers,
    matrix,
    numeric,
    table,
    vector,
)
from .._validation import instant as _instant
from ..cashflows import _currency


class SettlementModel:
    """Plan whole payments over ordered positions without releasing them.

    accounts rows have cash and currency, plus optional credit_limit>=0.
    payments rows have sender, receiver, amount>0, release and deadline;
    optional required/eligible boolean flags default True. Optional delay_cost
    is reporting currency per second; unsettled_cost is a reporting-currency
    horizon penalty. These are economic costs, not cash-debited payment fees.

    slots is a nondecreasing sequence of timezone-aware timestamps starting
    at as_of. Duplicate times are distinct ordered positions. Each position
    allows at most one single payment or explicitly authorized atomic batch.
    RTGS never nets separate positions or simultaneous unapproved payments.
    settlement_method='atomic' permits add_atomic_batch; no batch is inferred.

    Native account currencies remain separate. Reporting currency applies
    only to supplied economic cost coefficients; no FX trade is performed.
    The model proposes a plan, not payment execution, finality certification
    or an inferred legal permission to net obligations.
    """

    _objective = "settlement_cost"
    _needs_external = False

    def __init__(
        self,
        accounts,
        payments,
        *,
        as_of,
        slots,
        reporting_currency,
        settlement_method="rtgs",
        slot_ids=None,
    ):
        if settlement_method not in {"rtgs", "atomic"}:
            raise ValueError("settlement_method must be 'rtgs' or 'atomic'")
        self._method = settlement_method
        self._as_of = _instant(as_of, "as_of")
        self._times = pd.DatetimeIndex(
            [_instant(value, "slot time") for value in slots]
        )
        if (
            not len(self._times)
            or not self._times.is_monotonic_increasing
            or self._times[0] != self._as_of
        ):
            raise ValueError(
                "slot times must be nondecreasing and begin at as_of"
            )
        self._slots = identifiers(
            range(len(self._times)) if slot_ids is None else slot_ids,
            "slot_ids",
        )
        if len(self._slots) != len(self._times):
            raise ValueError(
                "slot_ids must have one ID per processing position"
            )
        self._currency = _currency(reporting_currency)
        self._accounts = table(
            accounts, {"cash", "currency"}, {"credit_limit"}, "accounts"
        )
        self._account_ids = copy_index(self._accounts.index)
        self._accounts["cash"] = numeric(
            self._accounts.cash.to_numpy(), "opening cash", ndim=1
        )
        self._accounts["currency"] = [
            _currency(value) for value in self._accounts.currency
        ]
        if "credit_limit" not in self._accounts:
            self._accounts["credit_limit"] = 0.0
        credit = numeric(
            self._accounts.credit_limit.to_numpy(), "credit_limit", ndim=1
        )
        if np.any(credit < 0) or np.any(
            self._accounts.cash.to_numpy() < -credit
        ):
            raise ValueError(
                "opening cash must respect nonnegative approved credit limits"
            )
        self._accounts["credit_limit"] = credit
        self._payments = table(
            payments,
            {"sender", "receiver", "amount", "release", "deadline"},
            {
                "currency",
                "required",
                "eligible",
                "delay_cost",
                "unsettled_cost",
            },
            "payments",
            allow_empty=True,
        )
        self._ids = copy_index(self._payments.index)
        for field in ("required", "eligible"):
            if field not in self._payments:
                self._payments[field] = True
            if any(
                not isinstance(value, (bool, np.bool_))
                for value in self._payments[field]
            ):
                raise ValueError(f"{field} must contain boolean flags")
            self._payments[field] = self._payments[field].astype(bool)
        for field in ("amount", "delay_cost", "unsettled_cost"):
            if field not in self._payments:
                self._payments[field] = 0.0
            values = (
                self._payments[field].to_numpy(dtype=float)
                if self._payments.empty
                else self._payments[field].to_numpy()
            )
            self._payments[field] = numeric(values, field, ndim=1)
        if (
            np.any(self._payments.amount <= 0)
            or np.any(self._payments.delay_cost < 0)
            or np.any(self._payments.unsettled_cost < 0)
        ):
            raise ValueError(
                "payments need positive amounts and nonnegative costs"
            )
        for field in ("release", "deadline"):
            self._payments[field] = pd.DatetimeIndex(
                [_instant(value, field) for value in self._payments[field]]
            )
        if (self._payments.release > self._payments.deadline).any():
            raise ValueError("release must not be after deadline")
        currencies = []
        for _, payment in self._payments.iterrows():
            for account in (payment.sender, payment.receiver):
                identifiers([account], "payment account")
                if account not in self._account_ids:
                    raise ValueError(
                        "payments must reference supplied accounts"
                    )
            if payment.sender == payment.receiver:
                raise ValueError(
                    "sender and receiver must be different accounts"
                )
            currency = self._accounts.currency.loc[payment.sender]
            if currency != self._accounts.currency.loc[payment.receiver]:
                raise ValueError(
                    "payments cannot convert between account currencies"
                )
            if (
                "currency" in self._payments
                and _currency(payment.currency) != currency
            ):
                raise ValueError("payment currency must match both accounts")
            currencies.append(currency)
        self._payments["currency"] = currencies
        self._flows = np.zeros((len(self._slots), len(self._account_ids)))
        self._credit_limits = np.broadcast_to(credit, self._flows.shape).copy()
        self._prefunding_limit = np.zeros(len(self._account_ids))
        self._prefunding_cost = self._prefunding_limit.copy()
        self._credit_cost = self._prefunding_limit.copy()
        self._final_lower = None
        self._batches = []
        self._precedences = []

    @property
    def account_ids(self):
        return copy_index(self._account_ids)

    @property
    def payment_ids(self):
        return copy_index(self._ids)

    @property
    def slot_ids(self):
        return copy_index(self._slots)

    @property
    def slot_times(self):
        return pd.Series(
            self._times, index=copy_index(self._slots), name="time", copy=True
        )

    @property
    def execution_units(self):
        """Detached units: single payments, then approved atomic batches."""
        return pd.DataFrame(
            [
                (kind, identifier, tuple(self._ids[i] for i in members))
                for kind, identifier, members in self._units()
            ],
            columns=["kind", "id", "payments"],
        ).rename_axis("position")

    def _units(self):
        return [
            ("payment", identifier, (i,))
            for i, identifier in enumerate(self._ids)
        ] + [
            ("atomic_batch", identifier, tuple(self._ids.get_indexer(ids)))
            for identifier, ids in self._batches
        ]

    def _eligible(self, members):
        rows = self._payments.iloc[list(members)]
        if not rows.eligible.all():
            return range(0)
        start = bisect_left(self._times, rows.release.max())
        stop = bisect_right(self._times, rows.deadline.min())
        return range(start, max(start, stop))

    def _movement(self, members):
        """Net one permitted execution unit in original account amounts."""
        movement = {}
        for payment in members:
            row = self._payments.iloc[payment]
            amount = Fraction(row.amount)
            for account, change in (
                (row.sender, -amount),
                (row.receiver, amount),
            ):
                position = self._account_ids.get_loc(account)
                movement[position] = movement.get(position, 0) + change
        return {
            account: amount for account, amount in movement.items() if amount
        }

    @property
    def _mixed_integer(self):
        return any(
            len(self._eligible(members)) for _, _, members in self._units()
        )

    @property
    def _problem_class(self):
        return "MILP" if self._mixed_integer else "LP"

    @property
    def _objective_unit(self):
        return self._currency

    def add_atomic_batch(self, batch_id, payment_ids):
        """Authorize this exact whole group as one atomic net settlement unit.

        Requires settlement_method='atomic'. All members settle together,
        within every member's window, with post-batch native account limits.
        This authorization includes caller-supplied finality/eligibility rules;
        the library does not establish legal permission or infer other batches.
        """
        if self._method != "atomic":
            raise ValueError(
                "atomic batches require settlement_method='atomic'"
            )
        identifiers([batch_id], "batch_id")
        if isinstance(payment_ids, (str, bytes)):
            raise ValueError("supply a sequence of payment IDs")
        ids = identifiers(payment_ids, "batch payments")
        if len(ids) < 2 or not ids.isin(self._ids).all():
            raise ValueError(
                "a batch needs at least two distinct supplied payments"
            )
        if any(
            batch_id == known or set(ids) == set(members)
            for known, members in self._batches
        ):
            raise ValueError("batch IDs and member sets must be unique")
        # Canonical membership follows the original payment order.
        self._batches.append((batch_id, self._ids[self._ids.isin(ids)]))
        return self

    def add_precedence(self, before, after, *, allow_same_batch=False):
        """Require before to complete before any settlement of after.

        If allow_same_batch=True, both may settle in the same authorized
        atomic unit. An unsettled predecessor blocks its successor. This
        is a hard priority/dependency rule, not a weighted-delay preference.
        """
        ids = identifiers([before, after], "precedence payments")
        if not ids.isin(self._ids).all():
            raise ValueError("precedence needs two distinct supplied payments")
        if not isinstance(allow_same_batch, (bool, np.bool_)):
            raise ValueError("allow_same_batch must be boolean")
        self._precedences.append((before, after, bool(allow_same_batch)))
        return self

    def set_external_flows(self, flows):
        """Set incremental slot-by-account receipts/outflows before settlement.

        Rows use slot IDs, including distinct positions at the same time.
        Values are native account currency, not cumulative funding. Balance
        limits apply after these flows and before the slot's settlement.
        """
        self._flows = matrix(
            flows, self._slots, self._account_ids, "external flows"
        )
        if hasattr(self._flows, "toarray"):
            self._flows = self._flows.toarray()
        return self

    def set_credit_limits(self, limits):
        """Set nonnegative slot-by-account approved overdraft capacities."""
        values = matrix(
            limits, self._slots, self._account_ids, "credit limits"
        )
        if hasattr(values, "toarray"):
            values = values.toarray()
        if np.any(values < 0):
            raise ValueError("credit limits must be nonnegative")
        self._credit_limits = values
        return self

    def allow_prefunding(self, maximum, *, cost_per_unit):
        """Allocate explicitly available outside funds before the first slot.

        Maximum is native currency per account; cost_per_unit is reporting
        currency per native unit for the horizon. This is outside prefunding,
        not an inferred loan. No repayment or funding-source reuse is invented.
        """
        limits = vector(
            maximum, self._account_ids, "maximum prefunding", broadcast=True
        )
        costs = vector(
            cost_per_unit, self._account_ids, "prefunding cost", broadcast=True
        )
        if np.any(limits < 0) or np.any(costs < 0):
            raise ValueError("prefunding limits and costs must be nonnegative")
        self._prefunding_limit, self._prefunding_cost = limits, costs
        return self

    def set_credit_costs(self, cost_per_unit):
        """Price actual peak overdraft per account in reporting currency.

        Zero charges permit free approved credit and do not claim minimal
        liquidity use. Peak includes opening and every pre/post-slot balance.
        """
        costs = vector(
            cost_per_unit, self._account_ids, "credit cost", broadcast=True
        )
        if np.any(costs < 0):
            raise ValueError("credit costs must be nonnegative")
        self._credit_cost = costs
        return self

    def limit_final_balances(self, lower=0.0):
        """Require native final buffers; zero requires overdraft repayment."""
        self._final_lower = vector(
            lower, self._account_ids, "final lower balances", broadcast=True
        )
        return self

    def require_payments(self, payment_ids):
        """Require the supplied payments to settle within their windows."""
        if isinstance(payment_ids, (str, bytes)):
            raise ValueError("supply a sequence of payment IDs")
        ids = identifiers(payment_ids, "required payments")
        if not ids.isin(self._ids).all():
            raise ValueError("required IDs must reference supplied payments")
        self._payments.loc[ids, "required"] = True
        return self

    def _specification(self):
        return portable(
            {
                "model": "SettlementModel",
                "as_of": self._as_of,
                "slot_ids": self._slots,
                "slot_times": self._times,
                "reporting_currency": self._currency,
                "settlement_method": self._method,
                "accounts": self._accounts,
                "payments": self._payments,
                "external_flows": self._flows,
                "credit_limits": self._credit_limits,
                "prefunding_limits": self._prefunding_limit,
                "prefunding_costs": self._prefunding_cost,
                "credit_costs": self._credit_cost,
                "final_lower_balances": self._final_lower,
                "atomic_batches": [
                    {"id": identifier, "payments": members}
                    for identifier, members in self._batches
                ],
                "precedences": self._precedences,
            }
        )

    def to_matrix(self):
        """Return sparse Opt data; execution_units maps unit positions.

        execution_u_k chooses unit position u at slot position k. prefunding_a,
        balance_k_a and peak_credit_a use account_ids[a]'s native currency.
        Optional completion_p_k auxiliaries are cumulative payment indicators.
        unsettled_p indicates a queued payment; p follows payment_ids order.
        Slots and units follow their public property order, not sorted IDs.
        """
        from ._compile import matrix_problem

        try:
            with np.errstate(over="raise", invalid="raise", divide="raise"):
                return matrix_problem(self)
        except (FloatingPointError, OverflowError) as error:
            raise ValueError(
                "settlement coefficients exceed float64 range"
            ) from error

    def _financial_variables(self, variables):
        pairs, releases = [], []
        for u, (kind, identifier, members) in enumerate(self._units()):
            for k in self._eligible(members):
                pairs.append((kind, identifier, self._slots[k]))
                releases.append(variables[f"execution_{u}_{k}"])
        cash_index = pd.MultiIndex.from_product(
            [copy_index(self._slots), copy_index(self._account_ids)],
            names=["slot", "account"],
        )
        result = {
            "release_indicators": pd.Series(
                releases,
                index=pd.MultiIndex.from_tuples(
                    pairs, names=["kind", "unit", "slot"]
                ),
                name="release_indicator",
                dtype=object,
            ),
            "cash_balances": pd.Series(
                [
                    variables[f"balance_{k}_{a}"]
                    for k in range(len(self._slots))
                    for a in range(len(self._account_ids))
                ],
                index=cash_index,
                name="cash",
                dtype=object,
            ),
            "unsettled": pd.Series(
                [variables[f"unsettled_{i}"] for i in range(len(self._ids))],
                index=copy_index(self._ids),
                name="unsettled",
                dtype=object,
            ),
        }
        for key in ("prefunding", "peak_credit"):
            result[key] = pd.Series(
                [
                    variables[f"{key}_{a}"]
                    for a in range(len(self._account_ids))
                ],
                index=copy_index(self._account_ids),
                name="peak_credit_used" if key == "peak_credit" else key,
                dtype=object,
            )
        return result

    def to_model(self, *, return_variables=False):
        """Return the equivalent detached algebraic Opt LP/MILP.

        return_variables=True also returns sparse release_indicators by
        (kind, unit ID, slot ID), account prefunding/peak_credit, unsettled
        payment indicators and cash_balances by (slot, account). Individual
        payments and approved atomic batches retain distinct identities.
        """
        from .._solvers._expressions import export_model, linear_model

        return export_model(
            linear_model(self.to_matrix()), self, return_variables
        )

    def _compile_opt(self, *, mode):
        return self.to_model() if mode == "platform" else self.to_matrix()

    def _compile_cvxpy(self):
        from .._solvers.cvxpy import linear_problem

        return linear_problem(self.to_matrix())

    def to_cvxpy(self):
        """Return a CVXPY problem and financial expressions.

        release_indicators is sparse by (kind, unit ID, slot ID).
        prefunding/peak_credit retain account IDs; cash_balances uses
        (slot, account); unsettled retains payment IDs.
        """
        problem, variables = self._compile_cvxpy()
        return problem, self._financial_variables(variables)

    def evaluate(self, schedule, *, prefunding=0.0, tolerance=1e-7):
        """Replay payment-to-slot assignments and all intermediate balances.

        Supply every payment ID, with a slot ID or None when unsettled.
        Slot IDs are integers or strings. Use object or nullable Int64 dtype
        for a pandas Series with integer IDs and unsettled payments; finite
        floating-point IDs are rejected because they can lose precision.
        None, pandas NA/NaT and floating-point NaN denote unsettled payments.
        Shared positions require exactly one approved atomic group; otherwise
        occupancy and sequential-prefix violations are retained explicitly.
        Original balances and costs are checked before float64 reporting;
        constraint residuals can retain differences hidden by rounded totals.
        """
        from ._evaluation import evaluate

        try:
            with np.errstate(over="raise", invalid="raise", divide="raise"):
                return evaluate(
                    self, schedule, prefunding=prefunding, tolerance=tolerance
                )
        except (FloatingPointError, OverflowError) as error:
            raise ValueError(
                "settlement quantities or costs exceed float64 range"
            ) from error

    def _evaluate_solution(self, solution, *, tolerance):
        from ._evaluation import evaluate_solution

        try:
            with np.errstate(over="raise", invalid="raise", divide="raise"):
                return evaluate_solution(self, solution, tolerance=tolerance)
        except (FloatingPointError, OverflowError) as error:
            raise ValueError(
                "settlement quantities or costs exceed float64 range"
            ) from error
