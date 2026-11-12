"""Collateral inventory, permitted pledges and dated margin requirements."""

from fractions import Fraction

import numpy as np
import pandas as pd

from .._arithmetic import float_upper_bound
from .._serialization import portable
from .._validation import (
    concentration_groups,
    copy_index,
    identifiers,
    numeric,
    table,
    vector,
)
from .._validation import lot_sizes as checked_lot_sizes
from ..cashflows import _currency, _date, _dated_values, _dates


class CollateralAllocationModel:
    """Minimize full-term costs of explicitly permitted, dated pledges.

    inventory rows are distinct owned lots/pools with quantity, native
    per-unit price and currency; optional encumbered units are unavailable
    throughout the horizon. Do not repeat the same physical inventory in
    multiple rows. requirements rows have obligation, date, amount and
    currency; each obligation/date is unique, with no inferred netting.

    pledges rows are permitted alternatives with asset, obligation,
    pledge_date, delivery_date, release_date, return_date, haircut and
    unit_cost. Optional fx_rate values collateral in obligation currency
    per inventory-currency unit; cross-currency pledges require it explicitly.
    unit_cost includes full-term opportunity/movement costs per asset unit,
    in reporting_currency. No annualization, cash FX trade or pricing occurs.

    A fixed chosen quantity locks inventory on [pledge_date, return_date)
    and covers requirements on [delivery_date, release_date). Supplied
    permitted alternatives must encode legal/entity/location/settlement
    eligibility. Returns at a date are available before new pledges at that
    date. This is deterministic bucket planning, not intraday settlement,
    received-collateral reuse or a collateral management/booking system.
    """

    _objective = "collateral_cost"
    _needs_external = False

    def __init__(
        self,
        inventory,
        requirements,
        pledges,
        *,
        as_of,
        dates,
        reporting_currency,
    ):
        self._as_of = _date(as_of, "as_of")
        self._dates = _dates(dates, "dates", ordered=True)
        if self._dates[0] != self._as_of:
            raise ValueError("planning dates must begin at as_of")
        self._currency = _currency(reporting_currency)
        self._inventory = table(
            inventory,
            {"quantity", "price", "currency"},
            {"encumbered"},
            "inventory",
        )
        self._assets = copy_index(self._inventory.index)
        for name in ("quantity", "price"):
            self._inventory[name] = numeric(
                self._inventory[name].to_numpy(), name, ndim=1
            )
        if np.any(self._inventory.quantity < 0) or np.any(
            self._inventory.price <= 0
        ):
            raise ValueError("inventory requires quantity >= 0 and price > 0")
        encumbered = (
            numeric(
                self._inventory.encumbered.to_numpy(), "encumbered", ndim=1
            )
            if "encumbered" in self._inventory
            else np.zeros(len(self._assets))
        )
        if np.any(encumbered < 0) or np.any(
            encumbered > self._inventory.quantity
        ):
            raise ValueError(
                "encumbered units must lie between zero and quantity"
            )
        self._inventory["encumbered"] = encumbered
        self._inventory["currency"] = [
            _currency(value) for value in self._inventory.currency
        ]
        self._requirements = table(
            requirements,
            {"obligation", "date", "amount", "currency"},
            set(),
            "requirements",
        )
        for value in self._requirements.obligation:
            identifiers([value], "obligation IDs")
        self._requirements["date"] = [
            self._grid_date(value, "requirement date")
            for value in self._requirements.date
        ]
        self._requirements["currency"] = [
            _currency(value) for value in self._requirements.currency
        ]
        self._requirements["amount"] = numeric(
            self._requirements.amount.to_numpy(), "requirements", ndim=1
        )
        if (
            np.any(self._requirements.amount < 0)
            or self._requirements.duplicated(["obligation", "date"]).any()
        ):
            raise ValueError(
                "requirements need nonnegative amounts and "
                "unique obligation/date pairs"
            )
        if (
            self._requirements.groupby(
                "obligation", sort=False, observed=True
            ).currency.nunique()
            != 1
        ).any():
            raise ValueError("each obligation must use one currency")
        self._pledges = table(
            pledges,
            {
                "asset",
                "obligation",
                "pledge_date",
                "delivery_date",
                "release_date",
                "return_date",
                "haircut",
                "unit_cost",
            },
            {"fx_rate"},
            "pledges",
            allow_empty=True,
        )
        self._ids = copy_index(self._pledges.index)
        for name in ("haircut", "unit_cost"):
            self._pledges[name] = numeric(
                self._pledges[name].to_numpy(dtype=float)
                if self._pledges.empty
                else self._pledges[name].to_numpy(),
                name,
                ndim=1,
            )
        if (
            np.any(self._pledges.haircut < 0)
            or np.any(self._pledges.haircut > 1)
            or np.any(self._pledges.unit_cost < 0)
        ):
            raise ValueError(
                "haircuts must lie in [0, 1] and unit costs be nonnegative"
            )
        for name in (
            "pledge_date",
            "delivery_date",
            "release_date",
            "return_date",
        ):
            self._pledges[name] = pd.to_datetime(
                [self._grid_date(value, name) for value in self._pledges[name]]
            )
        obligation_dates = {
            obligation: pd.DatetimeIndex(rows.date)
            for obligation, rows in self._requirements.groupby(
                "obligation", sort=False, observed=True
            )
        }
        for _, pledge in self._pledges.iterrows():
            identifiers([pledge.asset], "pledge asset")
            identifiers([pledge.obligation], "pledge obligation")
            if (
                pledge.asset not in self._assets
                or pledge.obligation not in obligation_dates
            ):
                raise ValueError(
                    "pledges must refer to supplied inventory and obligations"
                )
            if not (
                pledge.pledge_date
                <= pledge.delivery_date
                < pledge.release_date
                <= pledge.return_date
            ):
                raise ValueError(
                    "dates require pledge <= delivery < release <= return"
                )
            covered_dates = obligation_dates[pledge.obligation]
            if not (
                (covered_dates >= pledge.delivery_date)
                & (covered_dates < pledge.release_date)
            ).any():
                raise ValueError(
                    "each pledge must cover a supplied obligation/date"
                )
        obligation_currency = self._requirements.groupby(
            "obligation", sort=False, observed=True
        ).currency.first()
        source_currencies = self._pledges.asset.map(self._inventory.currency)
        target_currencies = self._pledges.obligation.map(obligation_currency)
        same_currency = source_currencies == target_currencies
        if "fx_rate" not in self._pledges:
            if not same_currency.all():
                raise ValueError(
                    "cross-currency pledges require explicit fx_rate"
                )
            self._pledges["fx_rate"] = np.ones(len(self._ids))
        fx = numeric(
            self._pledges.fx_rate.to_numpy(dtype=float)
            if self._pledges.empty
            else self._pledges.fx_rate.to_numpy(),
            "fx_rate",
            ndim=1,
        )
        if np.any(fx <= 0) or np.any(fx[same_currency.to_numpy()] != 1):
            raise ValueError(
                "FX rates must be positive; same-currency FX must equal one"
            )
        self._pledges["fx_rate"] = fx
        free = np.fromiter(
            map(float_upper_bound, self._free_inventory()), dtype=float
        )
        self._available = None
        self._lower = np.zeros(len(self._ids))
        self._upper = self._pledges.asset.map(
            pd.Series(free, index=copy_index(self._assets))
        ).to_numpy(dtype=float)
        self._coverage_upper = np.full(len(self._requirements), np.inf)
        self._pledge_limits = self._return_limits = np.full(
            (len(self._dates), len(self._assets)), np.inf
        )
        self._lots = None
        self._concentrations = []
        self._prices = self._haircuts = self._fx_rates = None

    def _grid_date(self, value, name):
        parsed = _date(value, name)
        if parsed not in self._dates:
            raise ValueError(f"{name} must belong to the planning dates")
        return parsed

    @property
    def asset_ids(self):
        return copy_index(self._assets)

    @property
    def pledge_ids(self):
        return copy_index(self._ids)

    @property
    def dates(self):
        return copy_index(self._dates)

    @property
    def reporting_currency(self):
        return self._currency

    @property
    def _objective_unit(self):
        return self._currency

    @property
    def _mixed_integer(self):
        return self._lots is not None and len(self._ids) > 0

    @property
    def _problem_class(self):
        return "MILP" if self._mixed_integer else "LP"

    def set_availability(self, quantities):
        """Set date-by-asset free inventory before proposed pledge locks.

        Values cannot exceed owned quantity less persistent encumbrances.
        This can reserve inventory for external uses or delay its availability;
        it does not create assets, lending or received-collateral reuse.
        """
        values = _dated_values(
            quantities, self._dates, self._assets, "availability"
        )
        free = self._free_inventory()
        if np.any(values < 0) or any(
            Fraction(value) > maximum
            for row in values
            for value, maximum in zip(row, free)
        ):
            raise ValueError(
                "availability must lie between zero and unencumbered inventory"
            )
        self._available = values
        return self

    def _free_inventory(self):
        return np.fromiter(
            (
                Fraction(quantity) - Fraction(encumbered)
                for quantity, encumbered in zip(
                    self._inventory.quantity, self._inventory.encumbered
                )
            ),
            dtype=object,
        )

    def set_prices(self, prices):
        """Supply a date-by-inventory native price path, replacing flat prices.

        Prices are positive currency per physical unit. The whole supplied
        path, including as_of, is authoritative; no price forecast, curve,
        interpolation or scenario probabilities are inferred.
        """
        values = _dated_values(prices, self._dates, self._assets, "prices")
        if np.any(values <= 0):
            raise ValueError("prices must be positive")
        self._prices = values
        return self

    def set_haircuts(self, haircuts):
        """Supply date-by-pledge haircuts in [0, 1] instead of flat terms."""
        values = _dated_values(haircuts, self._dates, self._ids, "haircuts")
        if np.any(values < 0) or np.any(values > 1):
            raise ValueError("haircuts must lie in [0, 1]")
        self._haircuts = values
        return self

    def set_fx_rates(self, fx_rates):
        """Supply positive date-by-pledge valuation FX, never currency trades.

        Quotes are obligation-currency units per inventory-currency unit.
        Same-currency quotes must be one at every date.
        """
        values = _dated_values(fx_rates, self._dates, self._ids, "fx_rates")
        obligation_currency = self._requirements.groupby(
            "obligation", sort=False, observed=True
        ).currency.first()
        same_currency = (
            self._pledges.asset.map(self._inventory.currency).to_numpy()
            == self._pledges.obligation.map(obligation_currency).to_numpy()
        )
        if np.any(values <= 0) or np.any(values[:, same_currency] != 1):
            raise ValueError(
                "FX rates must be positive; same-currency FX is one"
            )
        self._fx_rates = values
        return self

    def limit_assignments(self, *, lower=0.0, upper=None):
        """Bound pledge quantities in their assets' physical units."""
        if len(self._ids) == 0:
            raise ValueError("there are no permitted pledges to bound")
        low = vector(lower, self._ids, "lower assignment", broadcast=True)
        high = (
            self._upper.copy()
            if upper is None
            else vector(upper, self._ids, "upper assignment", broadcast=True)
        )
        if np.any(low < 0) or np.any(low > high):
            raise ValueError("assignments require 0 <= lower <= upper")
        self._lower, self._upper = low, high
        return self

    def pledge_in_lots(self, lot_sizes):
        """Restrict pledges to positive per-asset lots."""
        self._lots = checked_lot_sizes(lot_sizes, self._assets)
        return self

    def limit_coverage(self, maximum):
        """Bound adjusted coverage per requirement in its native currency."""
        upper = vector(
            maximum,
            self._requirements.index,
            "maximum coverage",
            broadcast=True,
        )
        if np.any(upper < self._requirements.amount):
            raise ValueError(
                "maximum coverage must be at least the required amount"
            )
        self._coverage_upper = upper
        return self

    def limit_movements(self, *, pledged=None, returned=None):
        """Bound dated outgoing/incoming units separately for each asset.

        Values are date-by-asset arrays or labeled DataFrames, not totals
        across unlike securities. An omitted side retains its prior limits.
        """
        if pledged is None and returned is None:
            raise ValueError("supply pledged or returned movement limits")
        new_pledge = (
            self._pledge_limits
            if pledged is None
            else _dated_values(
                pledged, self._dates, self._assets, "pledge limits"
            )
        )
        new_return = (
            self._return_limits
            if returned is None
            else _dated_values(
                returned, self._dates, self._assets, "return limits"
            )
        )
        if np.any(new_pledge < 0) or np.any(new_return < 0):
            raise ValueError("movement limits must be nonnegative")
        self._pledge_limits, self._return_limits = new_pledge, new_return
        return self

    def limit_concentration(self, groups, *, maximum_share):
        """Cap each asset group's share of adjusted value per obligation/date.

        The denominator is actual delivered, haircut/FX-adjusted coverage,
        not required margin or unadjusted market value. Multiple calls add
        classifications. No legal or jurisdictional policy is inferred.
        """
        self._concentrations.append(
            concentration_groups(groups, self._assets, maximum_share)
        )
        return self

    def _specification(self):
        return portable(
            {
                "model": "CollateralAllocationModel",
                "as_of": self._as_of,
                "dates": self._dates,
                "reporting_currency": self._currency,
                "inventory": self._inventory,
                "requirements": self._requirements,
                "permitted_pledges": self._pledges,
                "availability": self._available,
                "lower": self._lower,
                "upper": self._upper,
                "maximum_coverage": self._coverage_upper,
                "lot_sizes": self._lots,
                "pledge_limits": self._pledge_limits,
                "return_limits": self._return_limits,
                "concentrations": self._concentrations,
                "prices": self._prices,
                "haircuts": self._haircuts,
                "fx_rates": self._fx_rates,
            }
        )

    def to_matrix(self):
        """Return detached sparse Opt LP/MILP data.

        assignment_i denotes physical units or configured lot count for
        pledge_ids[i]. coverage_k is adjusted value in the native currency
        of requirements row k. Every original financial check remains active.
        """
        from ._compile import matrix_problem

        return matrix_problem(self)

    def _financial_variables(self, variables):
        assets = self._assets.get_indexer(self._pledges.asset)
        scales = (
            np.ones(len(self._ids))
            if self._lots is None
            else self._lots[assets]
        )
        return {
            "assignments": pd.Series(
                [
                    float(scale) * variables[f"assignment_{j}"]
                    for j, scale in enumerate(scales)
                ],
                index=copy_index(self._ids),
                name="quantity",
                dtype=object,
            ),
            "coverage": pd.Series(
                [
                    variables[f"coverage_{k}"]
                    for k in range(len(self._requirements))
                ],
                index=copy_index(self._requirements.index),
                name="adjusted_value",
                dtype=object,
            ),
        }

    def to_model(self, *, return_variables=False):
        """Return the equivalent detached algebraic Opt LP/MILP.

        return_variables=True also returns pledge-indexed assignments in
        actual quantities and requirement-indexed coverage in each row's
        native currency. Coverage retains price, haircut and valuation FX.
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

        assignments uses pledge IDs and actual quantities; coverage uses
        requirement IDs and each requirement's native currency.
        """
        problem, variables = self._compile_cvxpy()
        return problem, self._financial_variables(variables)

    def evaluate(self, assignments, *, tolerance=1e-7):
        """Rebuild dated coverage, locked inventory, movements and costs.

        Compare original quantities and valuation products before rounding.
        Reported amounts use float64; residuals can expose differences that
        the rounded inventory and coverage totals do not display.
        """
        from ._evaluation import evaluate

        try:
            with np.errstate(over="raise", invalid="raise", divide="raise"):
                return evaluate(self, assignments, tolerance=tolerance)
        except (FloatingPointError, OverflowError) as error:
            raise ValueError(
                "collateral quantities or values exceed float64 range"
            ) from error

    def _evaluate_solution(self, solution, *, tolerance):
        from ._evaluation import evaluate_solution

        try:
            with np.errstate(over="raise", invalid="raise", divide="raise"):
                return evaluate_solution(self, solution, tolerance=tolerance)
        except (FloatingPointError, OverflowError) as error:
            raise ValueError(
                "collateral quantities or values exceed float64 range"
            ) from error
