"""Dedicated-portfolio cash-flow matching and supplied risk equalities."""

from collections.abc import Mapping

import numpy as np
import pandas as pd
from scipy import sparse

from .._serialization import portable
from .._validation import (
    copy_index,
    identifiers,
    matrix,
    matrix_input,
    numeric,
    same_labels,
    scalar,
    unit_labels,
    vector,
)
from .._validation import lot_sizes as checked_lot_sizes
from ..cashflows import _currency, _date, _dated_values, _dates


class LiabilityMatchingModel:
    """Minimize initial capital for dated liabilities in one declared currency.

    Buy nonnegative instrument quantities at as_of using supplied per-unit
    prices and dated per-unit cash flows. Retain surplus in cash at explicit
    interval deposit returns. Initial capital pays purchases and any as-of
    liability; later asset cash flows cannot fund that initial purchase.
    All liability payments and cash buffers are hard dated requirements.
    Optional supplied sensitivity equalities are additional local-risk
    constraints, not a substitute for cash availability.
    """

    _objective = "initial_capital"
    _needs_external = False

    def __init__(
        self,
        prices,
        cash_flows,
        liabilities,
        *,
        currency,
        as_of,
        dates,
        asset_ids=None,
        deposit_returns=0.0,
    ):
        if isinstance(prices, Mapping):
            prices = pd.Series(prices)
        if asset_ids is None:
            asset_ids = (
                prices.index
                if isinstance(prices, pd.Series)
                else range(len(prices))
            )
        self._ids = identifiers(asset_ids)
        self._prices = vector(prices, self._ids, "prices")
        if np.any(self._prices <= 0):
            raise ValueError("purchase prices must be positive")
        self._currency = _currency(currency)
        self._as_of = _date(as_of, "as_of")
        self._dates = _dates(dates, "dates", ordered=True)
        if self._dates[0] != self._as_of:
            raise ValueError("planning dates must begin at as_of")
        cash_flows = matrix_input(cash_flows)
        if isinstance(cash_flows, pd.DataFrame):
            frame = cash_flows.copy()
            frame.index = _dates(frame.index, "asset cash-flow dates")
            if set(frame.index) != set(self._dates):
                raise ValueError(
                    "asset cash-flow dates must match planning dates"
                )
            same_labels(frame.columns, self._ids, "asset cash-flow columns")
            cash_flows = frame.reindex(
                index=self._dates, columns=self._ids
            ).to_numpy()
        self._flows = matrix(
            cash_flows, range(len(self._dates)), self._ids, "cash_flows"
        )
        first = (
            self._flows.getrow(0).toarray()
            if sparse.issparse(self._flows)
            else self._flows[0]
        )
        if np.any(first != 0):
            raise ValueError(
                "asset cash flows must be zero at the purchase date"
            )
        self._liabilities = self._dated_vector(liabilities, "liabilities")
        if np.any(self._liabilities < 0):
            raise ValueError("liabilities must be nonnegative payment amounts")
        self._returns = self._dated_vector(
            deposit_returns, "deposit_returns", broadcast=True
        )
        if np.ndim(deposit_returns) == 0:
            self._returns[0] = 0
        if np.any(self._returns < -1) or self._returns[0] != 0:
            raise ValueError(
                "deposit returns must be at least -1, with zero at as_of"
            )
        self._lower = np.zeros(len(self._ids))
        self._upper = np.full(len(self._ids), np.inf)
        self._cash_lower = np.zeros(len(self._dates))
        self._cash_upper = np.full(len(self._dates), np.inf)
        self._capital_limit = np.inf
        self._lots = None
        self._sensitivities = None

    def _dated_vector(self, values, name, *, broadcast=False):
        if isinstance(values, Mapping):
            values = pd.Series(values)
        if isinstance(values, pd.Series):
            values = values.to_frame(name="value")
        elif np.ndim(values) != 0:
            values = numeric(values, name, ndim=1)[:, None]
        elif not broadcast:
            raise ValueError(f"{name} requires one value per planning date")
        return _dated_values(
            values, self._dates, pd.Index(["value"]), name
        ).ravel()

    @property
    def asset_ids(self):
        return copy_index(self._ids)

    @property
    def dates(self):
        return copy_index(self._dates)

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
    def _problem_class(self):
        return "MILP" if self._mixed_integer else "LP"

    def limit_holdings(self, *, lower=0.0, upper=None):
        """Bound nonnegative purchased quantities in instrument units."""
        low = vector(lower, self._ids, "lower holdings", broadcast=True)
        high = (
            np.full(len(self._ids), np.inf)
            if upper is None
            else vector(upper, self._ids, "upper holdings", broadcast=True)
        )
        if np.any(low < 0) or np.any(low > high):
            raise ValueError("holdings require 0 <= lower <= upper")
        self._lower, self._upper = low, high
        return self

    def buy_in_lots(self, lot_sizes):
        """Restrict purchases to integer multiples of positive lot sizes."""
        self._lots = checked_lot_sizes(lot_sizes, self._ids)
        return self

    def limit_cash(self, *, minimum=0.0, maximum=None):
        """Set per-date retained cash bounds in the declared currency."""
        low = self._dated_vector(minimum, "minimum cash", broadcast=True)
        high = (
            np.full(len(self._dates), np.inf)
            if maximum is None
            else self._dated_vector(maximum, "maximum cash", broadcast=True)
        )
        if np.any(low < 0) or np.any(low > high):
            raise ValueError("cash requires 0 <= minimum <= maximum")
        self._cash_lower, self._cash_upper = low, high
        return self

    def limit_initial_capital(self, *, maximum):
        """Limit the initial reserve, in currency units."""
        self._capital_limit = scalar(maximum, "maximum", minimum=0)
        return self

    def match_sensitivities(
        self, sensitivities, target, *, risk_units, risk_ids=None
    ):
        """Require sensitivities @ holdings == supplied total liability risk.

        Matrix rows carry explicit physical risk_units, columns are assets.
        target is total signed sensitivity, not unweighted duration or a
        percentage. This configures one complete matching matrix; it does
        not price instruments or infer liability Greeks from cash flows.
        """
        sensitivities = matrix_input(sensitivities)
        if len(np.shape(sensitivities)) != 2:
            raise ValueError("sensitivities must be a risk-by-asset matrix")
        if risk_ids is None:
            risk_ids = (
                sensitivities.index
                if isinstance(sensitivities, pd.DataFrame)
                else range(np.shape(sensitivities)[0])
            )
        risks = identifiers(risk_ids, "risk_ids")
        values = matrix(sensitivities, risks, self._ids, "sensitivities")
        targets = vector(target, risks, "target")
        units = unit_labels(risk_units, risks)
        self._sensitivities = risks, values, targets, units
        return self

    def _specification(self):
        return portable(
            {
                "model": "LiabilityMatchingModel",
                "as_of": self._as_of,
                "dates": self._dates,
                "currency": self._currency,
                "asset_ids": self._ids,
                "prices": self._prices,
                "cash_flows": self._flows,
                "liabilities": self._liabilities,
                "deposit_returns": self._returns,
                "lower_holdings": self._lower,
                "upper_holdings": self._upper,
                "cash_lower": self._cash_lower,
                "cash_upper": self._cash_upper,
                "capital_limit": self._capital_limit,
                "lot_sizes": self._lots,
                "sensitivity_matching": self._sensitivities,
                "objective": self._objective,
            }
        )

    def _financial_variables(self, variables):
        from qpiai_opt.opt_modeller import Variable

        scales = np.ones(len(self._ids)) if self._lots is None else self._lots
        raw = [variables[f"holding_{i}"] for i in range(len(self._ids))]
        if isinstance(raw[0], Variable):
            from .._solvers._expressions import linear

            purchase = linear(raw, self._prices * scales)
        else:
            import cvxpy as cp

            purchase = (self._prices * scales) @ cp.hstack(raw)
        capital = purchase + variables["cash_0"] + float(self._liabilities[0])
        return {
            "holdings": pd.Series(
                [
                    float(scale) * variables[f"holding_{i}"]
                    for i, scale in enumerate(scales)
                ],
                index=copy_index(self._ids),
                name="quantity",
                dtype=object,
            ),
            "cash_balances": pd.Series(
                [variables[f"cash_{t}"] for t in range(len(self._dates))],
                index=copy_index(self._dates),
                name="cash",
                dtype=object,
            ),
            "initial_capital": capital,
        }

    def to_model(self, *, return_variables=False):
        """Return a detached Opt LP/MILP with dated cash constraints.

        return_variables=True also returns instrument-indexed holdings
        in actual quantities, dated cash_balances and an initial_capital
        expression in the declared currency. The export is independent
        of this source.
        """
        from .._solvers._expressions import export_model
        from ._matching_compile import compile_model

        return export_model(compile_model(self), self, return_variables)

    def _compile_cvxpy(self):
        from .._solvers.cvxpy import linear_problem

        return linear_problem(self.to_matrix())

    def to_matrix(self):
        """Return equivalent sparse data for Opt's public LP/MILP matrix input.

        Variable names retain source decoding. This representation avoids
        symbolic construction overhead; to_model provides an algebraic
        view of the same formulation for inspection and interoperability.
        holding_i is quantity, or lot count when lots are configured;
        cash_t uses the declared currency. Initial capital is purchase
        outlay plus the as-of liability and cash_0, with any reserve cap
        imposed on that sum.
        """
        from ._matching_compile import matrix_problem

        return matrix_problem(self)

    def _compile_opt(self, *, mode):
        return self.to_model() if mode == "platform" else self.to_matrix()

    def to_cvxpy(self):
        """Return a CVXPY problem and financial expressions.

        holdings uses actual instrument quantities; cash_balances and
        initial_capital use the model's currency.
        """
        problem, variables = self._compile_cvxpy()
        return problem, self._financial_variables(variables)

    def evaluate(self, holdings, *, initial_capital, tolerance=1e-7):
        """Check holdings and initial reserve against every dated liability.

        Cash and sensitivity constraints use original input products before
        rounding. Reported amounts use float64; constraint residuals retain
        differences that the rounded totals may not display.
        """
        from ._matching_evaluate import evaluate

        return evaluate(self, holdings, initial_capital, tolerance=tolerance)

    def _evaluate_solution(self, solution, *, tolerance):
        from ._matching_evaluate import evaluate_solution

        return evaluate_solution(self, solution, tolerance=tolerance)
