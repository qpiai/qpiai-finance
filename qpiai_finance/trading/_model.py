"""Target order completion through supplied venue and time opportunities."""

from collections.abc import Mapping
from copy import deepcopy
from datetime import datetime
from fractions import Fraction

import numpy as np
import pandas as pd
from scipy import sparse

from .._serialization import portable
from .._validation import (
    copy_frame,
    copy_index,
    covariance,
    identifiers,
    instant,
    matrix,
    matrix_input,
    numeric,
    same_labels,
    scalar,
    seconds,
    unit_labels,
    vector,
)
from .._validation import lot_sizes as checked_lot_sizes
from ..cashflows import _currency
from ..risk import FactorRisk, _risk_product
from .costs import _check_curve_capacity, _curve_segments


def _grid(values, rows, columns, name):
    if isinstance(values, Mapping):
        values = pd.Series(values)
    if isinstance(values, pd.Series):
        values = vector(values, columns, name)
    if not isinstance(values, pd.DataFrame) and np.ndim(values) < 2:
        values = np.broadcast_to(
            vector(values, columns, name, broadcast=True),
            (len(rows), len(columns)),
        )
    result = matrix(values, rows, columns, name)
    return result.toarray() if sparse.issparse(result) else result


class ExecutionModel:
    """Plan signed target orders across supplied venue/time opportunities.

    orders is a signed quantity per asset: positive buys, negative sells.
    holdings and arrival_prices describe the starting book and benchmark.
    All prices, fees and cash use one declared currency. Opportunities are
    a DataFrame with asset, slot, venue, price and capacity columns; optional
    bid_price/ask_price default to price. Rows are permitted alternatives,
    not inferred venue access. Capacity uses that asset's quantity units.

    slots are strictly increasing aware timestamps beginning at as_of.
    Trades occur at each slot; the next interval carries post-trade risk.
    cash_settlement='net' nets slot purchases and sales. 'prefunded' requires
    purchases and all execution charges to be funded before sale proceeds.
    Incremental external flows arrive before that slot's trades.

    Completion is hard unless allow_underfill is configured. Each asset
    trades only in its target direction, without overfill or round trips.
    Temporary impact is supplied, not calibrated or inferred. This model
    proposes a schedule; it does not submit orders or guarantee market fills.
    """

    _objective = "execution_cost"

    def __init__(
        self,
        orders,
        opportunities,
        *,
        arrival_prices,
        holdings,
        cash,
        currency,
        as_of,
        slots,
        cash_settlement,
        asset_ids=None,
        slot_ids=None,
        credit_limit=0.0,
        borrow_limits=0.0,
    ):
        if isinstance(orders, Mapping):
            orders = pd.Series(orders)
        if asset_ids is None:
            asset_ids = (
                orders.index
                if isinstance(orders, pd.Series)
                else range(len(orders))
            )
        self._ids = identifiers(asset_ids)
        self._orders = vector(orders, self._ids, "orders")
        self._direction = np.sign(self._orders)
        self._arrival = vector(arrival_prices, self._ids, "arrival_prices")
        if np.any(self._arrival <= 0):
            raise ValueError("arrival_prices must be positive")
        self._opening = vector(holdings, self._ids, "holdings", broadcast=True)
        self._target_positions = np.fromiter(
            (
                Fraction(opening) + Fraction(order)
                for opening, order in zip(self._opening, self._orders)
            ),
            dtype=object,
        )
        try:
            if not np.isfinite(
                np.asarray(self._target_positions, float)
            ).all():
                raise ValueError("target holdings exceed float64 range")
        except OverflowError as error:
            raise ValueError("target holdings exceed float64 range") from error
        self._opening_borrow = vector(
            borrow_limits, self._ids, "borrow_limits", broadcast=True
        )
        if np.any(self._opening_borrow < 0) or np.any(
            self._opening < -self._opening_borrow
        ):
            raise ValueError(
                "opening holdings must respect nonnegative borrow limits"
            )
        self._currency = _currency(currency)
        self._opening_credit = scalar(credit_limit, "credit_limit", minimum=0)
        self._cash = scalar(cash, "cash", minimum=-self._opening_credit)
        if cash_settlement not in {"net", "prefunded"}:
            raise ValueError("cash_settlement must be 'net' or 'prefunded'")
        self._settlement = cash_settlement
        self._as_of = instant(as_of, "as_of")
        self._times = pd.DatetimeIndex(
            [instant(value, "slot time") for value in slots]
        )
        if (
            not len(self._times)
            or not self._times.is_unique
            or not self._times.is_monotonic_increasing
            or self._times[0] != self._as_of
        ):
            raise ValueError(
                "slots must be strictly increasing and begin at as_of"
            )
        self._slots = identifiers(
            range(len(self._times)) if slot_ids is None else slot_ids,
            "slot_ids",
        )
        if len(self._slots) != len(self._times):
            raise ValueError("slot_ids must match slot times")
        required = {"asset", "slot", "venue", "price", "capacity"}
        optional = {"bid_price", "ask_price"}
        if not isinstance(opportunities, pd.DataFrame):
            raise TypeError("opportunities must be a DataFrame")
        if (
            not opportunities.columns.is_unique
            or not required <= set(opportunities.columns)
            or set(opportunities.columns) - required - optional
        ):
            raise ValueError(
                "opportunities require asset, slot, venue, price and "
                "capacity; bid_price and ask_price are optional"
            )
        if len(opportunities):
            identifiers(opportunities.index, "opportunity IDs")
            for field in ("asset", "slot", "venue"):
                identifiers(
                    opportunities[field], f"opportunity {field}", unique=False
                )
        if opportunities.duplicated(["asset", "slot", "venue"]).any():
            raise ValueError(
                "each asset/slot/venue opportunity must be unique"
            )
        self._opportunities = copy_frame(opportunities)
        self._op_ids = copy_index(opportunities.index)
        if (
            not opportunities.asset.isin(self._ids).all()
            or not opportunities.slot.isin(self._slots).all()
        ):
            raise ValueError(
                "opportunities must reference supplied asset and slot IDs"
            )
        for name in ("price", "capacity", "bid_price", "ask_price"):
            if name not in self._opportunities:
                self._opportunities[name] = self._opportunities.price.copy()
            values = self._opportunities[name].to_numpy()
            self._opportunities[name] = numeric(
                values.astype(float) if not len(values) else values,
                name,
                ndim=1,
            )
        rows = self._opportunities
        if (
            np.any(rows.capacity < 0)
            or np.any(rows.bid_price <= 0)
            or np.any(rows.bid_price > rows.price)
            or np.any(rows.price > rows.ask_price)
        ):
            raise ValueError(
                "capacity must be nonnegative; "
                "prices require 0 < bid <= price <= ask"
            )
        n, m, t = len(self._ids), len(rows), len(self._slots)
        self._fees = self._fixed = self._minimum = np.zeros(m)
        self._quadratic = self._power = np.zeros(m)
        self._curves = {}
        self._lots = None
        self._hard = np.ones(n, dtype=bool)
        self._underfill = None
        self._release = pd.DatetimeIndex([self._as_of] * n)
        self._deadlines = pd.DatetimeIndex([self._times[-1]] * n)
        self._flows = np.zeros(t)
        self._credit = np.full(t, self._opening_credit)
        self._cash_minimum = np.full(t, -np.inf)
        self._borrow = np.broadcast_to(self._opening_borrow, (t, n)).copy()
        self._position_limits = None
        self._participation = self._venue_limits = self._gross_limit = None
        self._turnover_limit = None
        self._exposures = []
        self._risk = None
        self._risk_nonzero = False
        self._risk_aversion = 0.0

    @property
    def asset_ids(self):
        return copy_index(self._ids)

    @property
    def opportunity_ids(self):
        return copy_index(self._op_ids)

    @property
    def slot_ids(self):
        return copy_index(self._slots)

    @property
    def slot_times(self):
        return pd.Series(
            self._times,
            index=copy_index(self._slots),
            name="time",
            copy=True,
        )

    @property
    def venue_ids(self):
        return copy_index(
            pd.Index(self._opportunities.venue).drop_duplicates()
        )

    @property
    def currency(self):
        return self._currency

    @property
    def _objective_unit(self):
        return self._currency

    @property
    def _mixed_integer(self):
        return self._lots is not None or bool(
            np.any(self._fixed > 0) or np.any(self._minimum > 0)
        )

    @property
    def _has_risk(self):
        return (
            self._risk_nonzero
            and self._risk_aversion > 0
            and len(self._slots) > 1
            and np.any(self._orders != 0)
        )

    @property
    def _needs_conic(self):
        return bool(np.any(self._quadratic > 0) or np.any(self._power > 0))

    @property
    def _needs_external(self):
        return self._needs_conic or (self._mixed_integer and self._has_risk)

    @property
    def _problem_class(self):
        if self._needs_conic:
            return "MISOCP" if self._mixed_integer else "SOCP"
        if self._has_risk:
            return "MIQP" if self._mixed_integer else "QP"
        return "MILP" if self._mixed_integer else "LP"

    def set_execution_costs(
        self, *, per_unit=0.0, fixed=0.0, minimum_trade=0.0
    ):
        """Set opportunity fees in currency/unit, currency/ticket and units.

        Fees are additional to the supplied bid/ask spread and impact.
        Fixed charges require a positive minimum or an integer trade lot.
        """
        values = []
        for name, value in (
            ("per_unit", per_unit),
            ("fixed", fixed),
            ("minimum_trade", minimum_trade),
        ):
            prepared = self._op_vector(value, name)
            if np.any(prepared < 0):
                raise ValueError(f"{name} must be nonnegative")
            values.append(prepared)
        self._fees, self._fixed, self._minimum = values
        return self

    def _op_vector(self, value, name):
        if len(self._op_ids):
            return vector(value, self._op_ids, name, broadcast=True)
        if isinstance(value, (Mapping, pd.Series)) and len(value) == 0:
            return np.zeros(0)
        if np.ndim(value) == 0:
            scalar(value, name)
            return np.zeros(0)
        prepared = numeric(value, name, ndim=1)
        if len(prepared):
            raise ValueError(f"{name} must be empty without opportunities")
        return prepared

    def trade_in_lots(self, lot_sizes):
        """Require each opportunity trade to be a whole positive asset lot."""
        self._lots = checked_lot_sizes(lot_sizes, self._ids)
        return self

    def set_market_impact(self, *, quadratic=0.0, power_3_2=0.0, curves=None):
        """Replace additive, nonnegative temporary impact costs by opportunity.

        Coefficients use currency/unit**2 and currency/unit**1.5. Curves map
        opportunity IDs to DataFrames with quantity/cost columns. Each curve
        starts at (0,0), has increasing quantities and nonnegative increasing
        slopes, and covers the possible trade size. Its linear interpolant
        is the specified cost, not an exact underlying nonlinear function.
        No permanent/cross-impact or market calibration is inferred.
        Configure quantity limits and lots before quoted curves. Coverage
        uses the largest permitted whole lot and is checked again on use
        if those controls change. Omitted cost components are reset.
        """
        quad = self._op_vector(quadratic, "quadratic impact")
        power = self._op_vector(power_3_2, "power_3_2 impact")
        if np.any(quad < 0) or np.any(power < 0):
            raise ValueError("impact coefficients must be nonnegative")
        if curves is not None and not isinstance(curves, Mapping):
            raise TypeError("curves must map opportunity IDs to cost tables")
        if curves:
            identifiers(list(curves), "impact curve opportunity IDs")
        prepared = {}
        for key, curve in (curves or {}).items():
            if key not in self._op_ids:
                raise ValueError("impact curve references unknown opportunity")
            if (
                not isinstance(curve, pd.DataFrame)
                or not curve.columns.is_unique
                or set(curve.columns) != {"quantity", "cost"}
            ):
                raise ValueError(
                    "impact curves require quantity and cost columns"
                )
            x = numeric(curve.quantity.to_numpy(), "curve quantities", ndim=1)
            y = numeric(curve.cost.to_numpy(), "curve costs", ndim=1)
            _curve_segments(x, y)
            prepared[key] = pd.DataFrame({"quantity": x, "cost": y})
        self._check_impact_curves(prepared)
        self._quadratic, self._power, self._curves = quad, power, prepared
        return self

    def _capacities(self, assets, slots):
        maximum = np.minimum(
            self._opportunities.capacity.to_numpy(),
            np.abs(self._orders[assets]),
        )
        times = self._times.take(slots)
        eligible = (times >= self._release.take(assets)) & (
            times <= self._deadlines.take(assets)
        )
        maximum[~eligible] = 0
        if self._participation is not None:
            volumes, rates = self._participation
            maximum = np.minimum(
                maximum, volumes[slots, assets] * rates[slots, assets]
            )
        return maximum

    def _check_impact_curves(self, curves):
        if not curves:
            return
        assets = self._ids.get_indexer(self._opportunities.asset)
        slots = self._slots.get_indexer(self._opportunities.slot)
        maximum = self._capacities(assets, slots)
        for key, points in curves.items():
            j = self._op_ids.get_loc(key)
            lot = 0.0 if self._lots is None else self._lots[assets[j]]
            _check_curve_capacity(
                points, maximum[j], lot, self._minimum[j],
                f"impact curve {key!r}",
            )

    def allow_underfill(self, penalty):
        """Permit unfilled orders at a supplied currency/unit penalty."""
        values = vector(
            penalty, self._ids, "underfill penalty", broadcast=True
        )
        if np.any(values < 0):
            raise ValueError("underfill penalties must be nonnegative")
        self._underfill = values
        self._hard = np.zeros(len(self._ids), dtype=bool)
        return self

    def require_completion(self, asset_ids=None):
        """Require completion for selected assets, or all by default."""
        ids = self._ids if asset_ids is None else identifiers(asset_ids)
        if not ids.isin(self._ids).all():
            raise ValueError("completion IDs must reference supplied orders")
        hard = self._hard.copy()
        hard[self._ids.get_indexer(ids)] = True
        self._hard = hard
        return self

    def set_order_windows(self, *, release=None, deadline=None):
        """Set exact aware release/deadline instants for each asset's order."""

        def times(value, default, name):
            if value is None:
                return pd.DatetimeIndex([default] * len(self._ids))
            if isinstance(value, (str, datetime, pd.Timestamp)):
                return pd.DatetimeIndex(
                    [instant(value, name)] * len(self._ids)
                )
            if isinstance(value, Mapping):
                value = pd.Series(value)
            if isinstance(value, pd.Series):
                same_labels(value.index, self._ids, name)
                value = value.reindex(self._ids).tolist()
            values = pd.DatetimeIndex([instant(item, name) for item in value])
            if len(values) != len(self._ids):
                raise ValueError(f"{name} must match asset IDs")
            return values

        starts = times(release, self._as_of, "release")
        ends = times(deadline, self._times[-1], "deadline")
        if np.any(starts > ends):
            raise ValueError("release must not follow deadline")
        self._release, self._deadlines = starts, ends
        return self

    def limit_participation(self, volumes, *, maximum_rate):
        """Cap all venue fills combined by supplied slot/asset market volume.

        Volumes use each asset's own units, rates lie in [0,1]. Values are
        slot-by-asset DataFrames/arrays, per-asset vectors or scalars.
        """
        values = _grid(volumes, self._slots, self._ids, "market volumes")
        rates = _grid(
            maximum_rate, self._slots, self._ids, "participation rates"
        )
        if np.any(values < 0) or np.any(rates < 0) or np.any(rates > 1):
            raise ValueError(
                "volumes must be nonnegative and participation rates in [0,1]"
            )
        self._participation = values, rates
        return self

    def limit_venue_notional(self, maximum):
        """Cap slot/venue gross reference-price notional, excluding charges."""
        if not len(self.venue_ids):
            raise ValueError("there are no supplied execution venues")
        limits = _grid(maximum, self._slots, self.venue_ids, "venue notional")
        if np.any(limits < 0):
            raise ValueError("venue notional limits must be nonnegative")
        self._venue_limits = limits
        return self

    def set_cash_flows(self, flows):
        """Set incremental cash flows arriving before each slot's trades."""
        self._flows = vector(flows, self._slots, "cash flows", broadcast=True)
        return self

    def set_credit_limits(self, maximum):
        """Set approved overdraft limits effective before each slot."""
        values = vector(maximum, self._slots, "credit limits", broadcast=True)
        if np.any(values < 0):
            raise ValueError("credit limits must be nonnegative")
        self._credit = values
        return self

    def limit_cash(self, minimum):
        """Require pre-trade and post-trade cash buffers alongside credit."""
        self._cash_minimum = vector(
            minimum, self._slots, "cash buffers", broadcast=True
        )
        return self

    def set_borrow_limits(self, maximum):
        """Set approved short quantities by slot and asset, without costs."""
        values = _grid(maximum, self._slots, self._ids, "borrow limits")
        if np.any(values < 0):
            raise ValueError("borrow limits must be nonnegative")
        self._borrow = values
        return self

    def limit_positions(self, *, lower=None, upper=None):
        """Bound post-trade quantities; None leaves that side unbounded."""
        shape = (len(self._slots), len(self._ids))
        low = (
            np.full(shape, -np.inf)
            if lower is None
            else _grid(lower, self._slots, self._ids, "lower positions")
        )
        high = (
            np.full(shape, np.inf)
            if upper is None
            else _grid(upper, self._slots, self._ids, "upper positions")
        )
        if np.any(low > high):
            raise ValueError("lower positions must not exceed upper positions")
        self._position_limits = (
            None if lower is None and upper is None else (low, high)
        )
        return self

    def limit_gross_notional(self, maximum):
        """Cap post-trade gross holdings at arrival prices, in currency."""
        values = vector(maximum, self._slots, "gross notional", broadcast=True)
        if np.any(values < 0):
            raise ValueError("gross notional limits must be nonnegative")
        self._gross_limit = values
        return self

    def limit_turnover(self, maximum):
        """Cap total absolute trade notional at arrival prices, in currency."""
        self._turnover_limit = scalar(maximum, "turnover limit", minimum=0)
        return self

    def limit_exposures(
        self, coefficients, *, lower, upper, risk_units, exposure_ids=None
    ):
        """Bound supplied linear risk rows on holdings at every slot.

        coefficients has exposure rows and asset columns. Bounds use each
        declared row's risk_units and may vary by slot. This is local supplied
        risk, not a repricing, forecast or universal regulatory model.
        """
        coefficients = matrix_input(coefficients)
        if exposure_ids is None:
            exposure_ids = (
                coefficients.index
                if isinstance(coefficients, pd.DataFrame)
                else range(np.shape(coefficients)[0])
            )
        ids = identifiers(exposure_ids, "exposure_ids")
        values = matrix(coefficients, ids, self._ids, "exposures")
        low = _grid(lower, self._slots, ids, "lower exposures")
        high = _grid(upper, self._slots, ids, "upper exposures")
        if np.any(low > high) or any(
            set(ids) & set(old[0]) for old in self._exposures
        ):
            raise ValueError(
                "exposure bounds must be ordered and IDs unique across calls"
            )
        units = unit_labels(risk_units, ids)
        self._exposures.append((ids, values, low, high, units))
        return self

    def set_price_risk(self, covariance_rate, *, risk_aversion):
        """Price remaining orders using independent Brownian price increments.

        covariance_rate is joint price-change covariance PER SECOND, in
        currency**2/(asset_unit_i*asset_unit_j*second), or an equivalent
        FactorRisk. Post-trade target gaps are exposed until the next slot;
        the final slot has zero subsequent horizon here. Risk cost is
        risk_aversion * sum(dt * remaining.T @ covariance_rate @ remaining).
        risk_aversion uses inverse currency. No returns/annualization or
        statistical calibration is inferred; this is not strategic book risk.
        """
        aversion = scalar(risk_aversion, "risk_aversion", minimum=0)
        if isinstance(covariance_rate, FactorRisk):
            same_labels(covariance_rate.asset_ids, self._ids, "risk assets")
            risk = deepcopy(covariance_rate)
        else:
            risk = covariance(
                covariance_rate, self._ids, "price covariance rate"
            )
        active = np.flatnonzero(self._orders != 0)
        if isinstance(risk, FactorRisk):
            order = risk.asset_ids.get_indexer(self._ids[active])
            loadings = sparse.csr_matrix(risk._b)[order]
            cross = loadings @ sparse.csr_matrix(risk._f)
            diagonal = (
                np.asarray(cross.multiply(loadings).sum(axis=1)).ravel()
                + risk._d[order]
            )
        else:
            diagonal = np.asarray(risk.diagonal()).ravel()[active]
        if not np.isfinite(diagonal).all():
            raise ValueError("price risk coefficients exceed float64 range")
        self._risk, self._risk_aversion = risk, aversion
        self._risk_nonzero = bool(np.any(diagonal != 0))
        return self

    def _durations(self):
        return np.array(
            [
                seconds(self._times[t + 1] - self._times[t])
                for t in range(len(self._slots) - 1)
            ]
            + [0.0]
        )

    @property
    def _cash_origin(self):
        if self._cash == 0:
            return 0.0
        floors = np.maximum(-self._credit, self._cash_minimum)
        if all(
            abs(Fraction(bound) - Fraction(self._cash))
            <= Fraction(np.finfo(float).max)
            for bound in (floors.min(), floors.max())
        ):
            return self._cash
        return 0.0

    def _risk_apply(self, values, *, original=False):
        if isinstance(self._risk, FactorRisk):
            risk = self._risk
            order = self._ids.get_indexer(risk._assets)
            marginal = _risk_product(risk, values[order], original=original)
            return marginal[risk._assets.get_indexer(self._ids)]
        return _risk_product(self._risk, values, original=original)

    def _check(self):
        self._check_impact_curves(self._curves)
        if self._lots is None and np.any(
            (self._fixed > 0) & (self._minimum == 0)
        ):
            raise ValueError(
                "fixed execution fees require a minimum trade or lot"
            )

    def _specification(self):
        from .._value_io import encode

        return portable(
            {
                "model": "ExecutionModel",
                "objective": self._objective,
                "objective_definition": (
                    "predicted_executed_shortfall + underfill_cost "
                    "+ price_risk_cost"
                ),
                "asset_ids": self._ids,
                "orders": self._orders,
                "arrival_prices": self._arrival,
                "holdings": self._opening,
                "cash": self._cash,
                "currency": self.currency,
                "as_of": self._as_of,
                "slot_ids": self._slots,
                "slot_times": self._times,
                "cash_settlement": self._settlement,
                "opening_credit_limit": self._opening_credit,
                "opening_borrow_limits": self._opening_borrow,
                "opportunities": self._opportunities,
                "fees": self._fees,
                "fixed_fees": self._fixed,
                "minimum_trades": self._minimum,
                "lot_sizes": self._lots,
                "quadratic_impact": self._quadratic,
                "power_3_2_impact": self._power,
                "piecewise_impact": list(
                    (key, table) for key, table in self._curves.items()
                ),
                "hard_completion": self._hard.tolist(),
                "underfill_penalty": self._underfill,
                "release": self._release,
                "deadline": self._deadlines,
                "cash_flows": self._flows,
                "credit_limits": self._credit,
                "cash_minimum": self._cash_minimum,
                "borrow_limits": self._borrow,
                "position_limits": self._position_limits,
                "participation": self._participation,
                "venue_limits": self._venue_limits,
                "gross_limit": self._gross_limit,
                "turnover_limit": self._turnover_limit,
                "exposures": self._exposures,
                "price_covariance_rate": None
                if self._risk is None
                else encode(self._risk),
                "risk_aversion": self._risk_aversion,
                "risk_timing": "post_trade_until_next_slot",
                "impact_model": "supplied_temporary_costs_only",
            }
        )

    def to_matrix(self):
        """Return detached sparse Opt data for a linear execution model."""
        from ._compile import linear_backbone

        self._check()
        if self._has_risk or self._needs_conic:
            raise ValueError(
                "to_matrix requires a linear model; use to_model or to_cvxpy"
            )
        return linear_backbone(self)[0]

    def _financial_variables(self, variables):
        assets = self._ids.get_indexer(self._opportunities.asset)
        scales = (
            np.ones(len(assets)) if self._lots is None else self._lots[assets]
        )
        executions = pd.Series(
            [
                float(self._direction[i] * scale) * variables[f"execution_{j}"]
                for j, (i, scale) in enumerate(zip(assets, scales))
            ],
            index=copy_index(self._op_ids),
            name="quantity",
            dtype=object,
        )
        zero = 0 * next(iter(variables.values()))
        slots = self._slots.get_indexer(self._opportunities.slot)
        by_slot = [[] for _ in self._slots]
        for j, k in enumerate(slots):
            by_slot[k].append(j)
        cumulative = [zero for _ in self._ids]
        cash_origin = self._cash_origin
        remaining, holdings = [], []
        for k in range(len(self._slots)):
            for j in by_slot[k]:
                i = assets[j]
                cumulative[i] = cumulative[i] + executions.iloc[j]
            row = [
                float(self._direction[i])
                * variables.get(f"remaining_{k}_{i}", zero)
                for i in range(len(self._ids))
            ]
            remaining.append(row)
            holdings.append(
                [
                    float(self._opening[i]) + value
                    for i, value in enumerate(cumulative)
                ]
            )
        return {
            "executions": executions,
            "remaining_orders": pd.DataFrame(
                remaining,
                index=copy_index(self._slots),
                columns=copy_index(self._ids),
            ),
            "holdings": pd.DataFrame(
                holdings,
                index=copy_index(self._slots),
                columns=copy_index(self._ids),
            ),
            "cash_balances": pd.Series(
                [
                    cash_origin + variables[f"cash_change_{k}"]
                    for k in range(len(self._slots))
                ],
                index=copy_index(self._slots),
                name="cash",
                dtype=object,
            ),
        }

    def to_model(self, *, return_variables=False):
        """Return a complete detached native Opt LP/MILP or continuous QP.

        return_variables=True also returns opportunity-indexed signed
        executions, slot/asset remaining_orders and holdings, and slot
        cash_balances. Quantity expressions use actual units, not lots.
        """
        from .._solvers._expressions import export_model
        from ._compile import compile_opt

        self._check()
        return export_model(compile_opt(self), self, return_variables)

    def _compile_opt(self, *, mode):
        return (
            self.to_model()
            if mode == "platform" or self._has_risk
            else self.to_matrix()
        )

    def _compile_cvxpy(self):
        from ._compile import compile_cvxpy

        self._check()
        return compile_cvxpy(self)

    def _compile_cvxpy_for_solve(self, *, solver):
        from ._compile import compile_cvxpy

        self._check()
        return compile_cvxpy(
            self,
            numerical=(
                solver == "clarabel"
                and self._needs_conic
                and not self._mixed_integer
            ),
        )

    def to_cvxpy(self):
        """Return a CVXPY problem and signed actual-quantity expressions.

        executions uses opportunity IDs; remaining_orders and holdings
        use slots/assets; cash_balances uses slots in the declared currency.
        """
        problem, variables = self._compile_cvxpy()
        return problem, self._financial_variables(variables)

    def evaluate(self, executions, *, tolerance=1e-7):
        """Replay signed quantities and original financial limits."""
        from ._evaluation import evaluate

        self._check()
        try:
            return evaluate(self, executions, tolerance=tolerance)
        except (FloatingPointError, OverflowError) as error:
            raise ValueError(
                "execution calculations exceed float64 range"
            ) from error

    def _evaluate_solution(self, solution, *, tolerance):
        from ._evaluation import evaluate_solution

        self._check()
        try:
            return evaluate_solution(self, solution, tolerance=tolerance)
        except (FloatingPointError, OverflowError) as error:
            raise ValueError(
                "execution calculations exceed float64 range"
            ) from error
