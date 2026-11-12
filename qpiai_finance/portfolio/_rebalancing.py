"""Self-financing share transactions for portfolio models."""

from dataclasses import dataclass
from fractions import Fraction
from math import prod

import numpy as np
import pandas as pd

from .._arithmetic import bound_violation, product_sum
from .._validation import (
    copy_index,
    lot_quantities,
    lot_residual,
    scalar,
    vector,
)
from ..cashflows import _currency
from ..trading.costs import _ticket_cost
from ._tax_lots import _TaxLots


def _scaled_products(*factors, divisor=1.0):
    """Scale account values without losing an intermediate product's range."""
    try:
        with np.errstate(over="raise", invalid="raise", under="raise"):
            result = factors[0]
            for factor in factors[1:]:
                result = result * factor
            return result / divisor
    except FloatingPointError:
        arrays = np.broadcast_arrays(*factors, divisor)
        try:
            return np.fromiter(
                (
                    prod(map(Fraction, values[:-1])) / Fraction(values[-1])
                    for values in zip(*(array.flat for array in arrays))
                ),
                dtype=float,
            ).reshape(arrays[0].shape)
        except OverflowError as error:
            raise ValueError(
                "portfolio values exceed float64 range"
            ) from error


@dataclass
class _Account:
    holdings: np.ndarray
    prices: np.ndarray
    bid_prices: np.ndarray
    ask_prices: np.ndarray
    cash: float
    currency: str
    initial_value: float
    cash_return: float
    initial_weights: np.ndarray
    cash_lower: float
    cash_upper: float
    buy_bps: np.ndarray
    sell_bps: np.ndarray
    buy_fixed: np.ndarray
    sell_fixed: np.ndarray
    minimum_trade: np.ndarray
    lots: np.ndarray | None = None
    short_available: np.ndarray | None = None
    tax_lots: _TaxLots | None = None

    @classmethod
    def create(
        cls,
        ids,
        holdings,
        prices,
        cash,
        currency,
        bid_prices,
        ask_prices,
        cash_return,
    ):
        currency = _currency(currency)
        holdings = vector(holdings, ids, "holdings")
        prices = vector(prices, ids, "prices")
        bid_prices = (
            prices.copy()
            if bid_prices is None
            else vector(bid_prices, ids, "bid_prices")
        )
        ask_prices = (
            prices.copy()
            if ask_prices is None
            else vector(ask_prices, ids, "ask_prices")
        )
        if (
            np.any(bid_prices <= 0)
            or np.any(prices < bid_prices)
            or np.any(ask_prices < prices)
        ):
            raise ValueError(
                "prices must satisfy 0 < bid_prices <= prices <= ask_prices"
            )
        cash = scalar(cash, "cash")
        cash_return = scalar(cash_return, "cash_return", minimum=-1)
        try:
            initial_value = scalar(
                float(Fraction(cash) + product_sum((prices, holdings))),
                "initial portfolio value",
                minimum=0,
            )
        except OverflowError as error:
            raise ValueError(
                "initial portfolio value exceeds float64 range"
            ) from error
        if initial_value == 0:
            raise ValueError("initial portfolio value must be positive")
        return cls(
            holdings=holdings,
            prices=prices,
            bid_prices=bid_prices,
            ask_prices=ask_prices,
            cash=cash,
            currency=currency,
            initial_value=initial_value,
            cash_return=cash_return,
            initial_weights=_scaled_products(
                prices, holdings, divisor=initial_value
            ),
            cash_lower=0.0,
            cash_upper=1.0,
            buy_bps=np.zeros(len(ids)),
            sell_bps=np.zeros(len(ids)),
            buy_fixed=np.zeros(len(ids)),
            sell_fixed=np.zeros(len(ids)),
            minimum_trade=np.zeros(len(ids)),
        )

    def coefficients(self):
        buy_spread = (self.ask_prices - self.prices) / self.prices
        sell_spread = (self.prices - self.bid_prices) / self.prices
        buy_fee = (self.ask_prices / self.prices) * self.buy_bps / 10000
        sell_fee = (self.bid_prices / self.prices) * self.sell_bps / 10000
        return buy_spread + buy_fee, sell_spread + sell_fee

    @property
    def direction_mask(self):
        buy_cost, sell_cost = self.coefficients()
        return (
            (buy_cost > 0)
            | (sell_cost > 0)
            | (self.buy_fixed > 0)
            | (self.sell_fixed > 0)
            | (self.minimum_trade > 0)
            | (False if self.tax_lots is None else self.tax_lots.mask)
        )

    @property
    def mixed_integer(self):
        return self.lots is not None or bool(self.direction_mask.any())

    @property
    def _minimum_trade_weights(self):
        quantities = (
            self.minimum_trade if self.lots is None
            else np.maximum(self.minimum_trade, self.lots)
        )
        weights = _scaled_products(
            self.prices, quantities, divisor=self.initial_value
        )
        if np.any((quantities > 0) & (weights == 0)):
            raise ValueError("minimum trade weight is below float64 range")
        return weights

    def validate(self, lower):
        if self.tax_lots is not None and np.any(lower < 0):
            raise ValueError(
                "acquisition tax lots require nonnegative weights"
            )
        if np.any(lower < 0) and self.short_available is None:
            raise ValueError(
                "short positions require borrow availability; "
                "call limit_short_positions"
            )
        fixed = (self.buy_fixed > 0) | (self.sell_fixed > 0)
        if self.lots is None and np.any(fixed & (self.minimum_trade <= 0)):
            raise ValueError(
                "fixed trading fees require minimum_trade or trade_in_lots"
            )

    def add_opt(self, model, weights, lower, upper):
        from qpiai_opt.opt_modeller import (
            Binary,
            Continuous,
            Integer,
            quicksum,
        )

        cash_weight = model.add_variable(
            Continuous("cash_weight", self.cash_lower, self.cash_upper)
        )
        transaction_cost = 0
        sales = {}
        buy_coefficient, sell_coefficient = self.coefficients()
        direction_mask = self.direction_mask
        minimum_weights = (
            self._minimum_trade_weights if direction_mask.any() else None
        )
        lot_weights = (
            None if self.lots is None else _scaled_products(
                self.prices, self.lots, divisor=self.initial_value
            )
        )
        if lot_weights is not None and np.any(lot_weights == 0):
            raise ValueError("trade lot weights are below float64 range")
        short_weights = (
            None if self.short_available is None else _scaled_products(
                self.prices, self.short_available, divisor=self.initial_value
            )
        )
        for i, weight in enumerate(weights):
            trade = weight - float(self.initial_weights[i])
            if self.lots is not None:
                lot_weight = float(lot_weights[i])
                minimum_lots = int(
                    np.floor((lower[i] - self.initial_weights[i]) / lot_weight)
                )
                maximum_lots = int(
                    np.ceil((upper[i] - self.initial_weights[i]) / lot_weight)
                )
                trade_lots = model.add_variable(
                    Integer(f"trade_lots_{i}", minimum_lots, maximum_lots)
                )
                model.add_constraint(
                    trade == lot_weight * trade_lots,
                    label=f"trade_lot_size_{i}",
                )
            if self.short_available is not None:
                model.add_constraint(
                    weight
                    >= -float(short_weights[i])
                )
            if not direction_mask[i]:
                continue
            buy = model.add_variable(Continuous(f"buy_{i}"))
            sell = model.add_variable(Continuous(f"sell_{i}"))
            sales[i] = sell
            buy_active = model.add_variable(Binary(f"buy_active_{i}"))
            sell_active = model.add_variable(Binary(f"sell_active_{i}"))
            model.add_constraint(
                trade == buy - sell, label=f"position_transition_{i}"
            )
            model.add_constraint(
                buy_active + sell_active <= 1, label=f"trade_direction_{i}"
            )
            model.add_constraint(
                buy
                <= max(0.0, float(upper[i] - self.initial_weights[i]))
                * buy_active
            )
            model.add_constraint(
                sell
                <= max(0.0, float(self.initial_weights[i] - lower[i]))
                * sell_active
            )
            minimum_weight = float(minimum_weights[i])
            model.add_constraint(buy >= minimum_weight * buy_active)
            model.add_constraint(sell >= minimum_weight * sell_active)
            transaction_cost += _ticket_cost(
                float(buy_coefficient[i]) * buy,
                float(self.buy_fixed[i] / self.initial_value),
                buy_active,
            )
            transaction_cost += _ticket_cost(
                float(sell_coefficient[i]) * sell,
                float(self.sell_fixed[i] / self.initial_value),
                sell_active,
            )
        tax = (
            0
            if self.tax_lots is None
            else self.tax_lots.add_opt(
                model, sales, self.prices, self.initial_value
            )
        )
        cash_tax = (
            tax
            if self.tax_lots is not None
            and self.tax_lots.settlement == "immediate"
            else 0
        )
        model.add_constraint(
            quicksum(weights) + cash_weight + transaction_cost + cash_tax == 1,
            label="self_financing",
        )
        return cash_weight, transaction_cost + tax

    def add_cvxpy(self, weights, lower, upper, constraints):
        import cvxpy as cp

        cash_weight = cp.Variable(name="cash_weight")
        variables = {"cash_weight": cash_weight}
        constraints.extend(
            [cash_weight >= self.cash_lower, cash_weight <= self.cash_upper]
        )
        buy_coefficient, sell_coefficient = self.coefficients()
        transaction_cost = 0
        sales = {}
        if self.lots is not None:
            lot_weights = _scaled_products(
                self.prices, self.lots, divisor=self.initial_value
            )
            if np.any(lot_weights == 0):
                raise ValueError("trade lot weights are below float64 range")
            counts = cp.Variable(
                len(self.holdings), integer=True, name="trade_lots"
            )
            constraints.append(
                weights - self.initial_weights
                == cp.multiply(
                    lot_weights, counts
                )
            )
            variables.update(
                {
                    f"trade_lots_{i}": counts[i]
                    for i in range(len(self.holdings))
                }
            )
        if self.short_available is not None:
            constraints.append(
                weights
                >= -_scaled_products(
                    self.prices, self.short_available,
                    divisor=self.initial_value,
                )
            )
        direction_mask = self.direction_mask
        minimum_weights = (
            self._minimum_trade_weights if direction_mask.any() else None
        )
        for i in np.flatnonzero(direction_mask):
            buy, sell = cp.Variable(nonneg=True), cp.Variable(nonneg=True)
            sales[i] = sell
            buy_active, sell_active = (
                cp.Variable(boolean=True),
                cp.Variable(boolean=True),
            )
            constraints.extend(
                [
                    weights[i] - self.initial_weights[i] == buy - sell,
                    buy_active + sell_active <= 1,
                    buy
                    <= max(0.0, float(upper[i] - self.initial_weights[i]))
                    * buy_active,
                    sell
                    <= max(0.0, float(self.initial_weights[i] - lower[i]))
                    * sell_active,
                ]
            )
            minimum_weight = float(minimum_weights[i])
            constraints.extend(
                [
                    buy
                    >= minimum_weight * buy_active,
                    sell
                    >= minimum_weight * sell_active,
                ]
            )
            transaction_cost += _ticket_cost(
                buy_coefficient[i] * buy,
                self.buy_fixed[i] / self.initial_value,
                buy_active,
            )
            transaction_cost += _ticket_cost(
                sell_coefficient[i] * sell,
                self.sell_fixed[i] / self.initial_value,
                sell_active,
            )
            variables.update(
                {
                    f"buy_active_{i}": buy_active,
                    f"sell_active_{i}": sell_active,
                }
            )
        tax = 0
        if self.tax_lots is not None:
            tax, lot_variables = self.tax_lots.add_cvxpy(
                sales, self.prices, self.initial_value, constraints
            )
            variables.update(lot_variables)
        cash_tax = (
            tax
            if self.tax_lots is not None
            and self.tax_lots.settlement == "immediate"
            else 0
        )
        constraints.append(
            cp.sum(weights) + cash_weight + transaction_cost + cash_tax == 1
        )
        return cash_weight, transaction_cost + tax, variables

    def recover(self, weights, solution):
        recovered_weights = weights.copy()
        residuals = {}
        if self.lots is not None:
            holdings_after = self.holdings.copy()
            for i in range(len(recovered_weights)):
                lot_count = solution[f"trade_lots_{i}"]
                integer_count = np.rint(lot_count)
                residuals[f"integer_trade[{i}]"] = float(
                    abs(lot_count - integer_count)
                )
                holdings_after[i] = self.holdings[i] + lot_quantities(
                    integer_count, self.lots[i]
                )
            recovered_weights = _scaled_products(
                self.prices, holdings_after, divisor=self.initial_value
            )
        for i in np.flatnonzero(self.direction_mask):
            buy_active, sell_active = (
                solution[f"buy_active_{i}"],
                solution[f"sell_active_{i}"],
            )
            residuals[f"buy_indicator[{i}]"] = float(
                abs(buy_active - np.rint(buy_active))
            )
            residuals[f"sell_indicator[{i}]"] = float(
                abs(sell_active - np.rint(sell_active))
            )
            if np.rint(buy_active) == 0 and np.rint(sell_active) == 0:
                recovered_weights[i] = self.initial_weights[i]
            residuals[f"trade_direction[{i}]"] = max(
                float(buy_active + sell_active - 1),
                float(-buy_active),
                float(buy_active - 1),
                float(-sell_active),
                float(sell_active - 1),
                0,
            )
        residuals["position_reconstruction"] = float(
            np.max(np.abs(recovered_weights - weights))
        )
        return recovered_weights, residuals

    def evaluate(self, weights, ids, tolerance, *, tax_lot_sales=None):
        ids = copy_index(ids)
        try:
            with np.errstate(over="raise", invalid="raise"):
                trade_weights = weights - self.initial_weights
                holdings_after = np.where(
                    trade_weights == 0,
                    self.holdings,
                    self.holdings + _scaled_products(
                        trade_weights, self.initial_value,
                        divisor=self.prices,
                    ),
                )
                trades = holdings_after - self.holdings
        except FloatingPointError as error:
            raise ValueError(
                "portfolio accounting exceeds float64 range"
            ) from error
        buys = np.maximum(trades, 0)
        sells = np.maximum(-trades, 0)
        tax = (
            None
            if self.tax_lots is None
            else self.tax_lots.evaluate(
                tax_lot_sales, sells, tolerance, currency=self.currency
            )
        )
        if self.tax_lots is None and tax_lot_sales is not None:
            raise ValueError("tax_lot_sales requires configured tax lots")
        tax_liability = 0.0 if tax is None else tax["tax"]
        cash_tax = (
            tax_liability
            if tax is not None and self.tax_lots.settlement == "immediate"
            else 0.0
        )
        try:
            with np.errstate(over="raise", invalid="raise"):
                buy_fees = _ticket_cost(
                    _scaled_products(
                        self.ask_prices, buys, self.buy_bps, divisor=10000
                    ),
                    self.buy_fixed,
                    trades > 0,
                )
                sell_fees = _ticket_cost(
                    _scaled_products(
                        self.bid_prices, sells, self.sell_bps, divisor=10000
                    ),
                    self.sell_fixed,
                    trades < 0,
                )
                spread = (self.ask_prices - self.prices) * buys + (
                    self.prices - self.bid_prices
                ) * sells
        except FloatingPointError as error:
            raise ValueError(
                "portfolio accounting exceeds float64 range"
            ) from error
        if not all(
            np.isfinite(values).all()
            for values in (holdings_after, buy_fees, sell_fees, spread)
        ):
            raise ValueError("portfolio accounting exceeds float64 range")
        units = np.ones(len(weights))
        fees = product_sum((buy_fees, units), (sell_fees, units))
        spread_cost = product_sum((spread, units))
        cash_amount = (
            Fraction(self.cash)
            + product_sum((-self.ask_prices, buys), (self.bid_prices, sells))
            - fees
            - Fraction(cash_tax)
        )
        value = cash_amount + product_sum((self.prices, holdings_after))
        try:
            total_fees = float(fees)
            cash_after = float(cash_amount)
            transaction_cost = float(
                spread_cost + fees + Fraction(tax_liability)
            )
            portfolio_value = float(value)
        except OverflowError as error:
            raise ValueError(
                "portfolio accounting exceeds float64 range"
            ) from error
        if not np.isfinite(
            [cash_after, transaction_cost, portfolio_value]
        ).all():
            raise ValueError("portfolio accounting exceeds float64 range")
        rows = []

        def check(name, value, lower, upper):
            violation = bound_violation(value, lower, upper)
            satisfied = violation <= tolerance
            rows.append(
                (name, float(value), lower, upper, float(violation), satisfied)
            )

        check(
            "self_financing",
            product_sum((weights, units))
            + (cash_amount + spread_cost + fees + Fraction(cash_tax))
            / Fraction(self.initial_value),
            1,
            1,
        )
        check(
            "cash_balance",
            cash_amount / Fraction(self.initial_value),
            self.cash_lower,
            self.cash_upper,
        )
        check(
            "portfolio_value",
            value / Fraction(self.initial_value),
            np.finfo(float).tiny,
            np.inf,
        )
        if self.short_available is not None:
            position_weights = _scaled_products(
                self.prices, holdings_after, divisor=self.initial_value
            )
            available_weights = _scaled_products(
                self.prices, self.short_available, divisor=self.initial_value
            )
        minimum_weights = (
            _scaled_products(
                self.prices, self.minimum_trade, divisor=self.initial_value
            )
            if np.any(trades != 0) else None
        )
        for i in range(len(ids)):
            if self.lots is not None:
                check(
                    f"trade_lot_size[{i}]",
                    lot_residual(trades[i], self.lots[i]),
                    0,
                    0,
                )
            if self.short_available is not None:
                check(
                    f"borrow_availability[{i}]",
                    float(-position_weights[i]),
                    -np.inf,
                    float(available_weights[i]),
                )
            if trades[i] != 0:
                minimum = minimum_weights[i]
                check(
                    f"minimum_trade[{i}]",
                    float(abs(trade_weights[i])),
                    float(minimum),
                    np.inf,
                )
        holdings = pd.Series(holdings_after, index=ids, name="quantity")
        decision = {
            "weights": pd.Series(weights, index=ids, name="weight"),
            "holdings": holdings,
            "trades": pd.Series(trades, index=ids, name="quantity"),
        }
        if portfolio_value > 0:
            decision["post_trade_weights"] = pd.Series(
                _scaled_products(
                    self.prices, holdings_after, divisor=portfolio_value
                ),
                index=ids,
                name="weight",
            )
        metrics = {
            "cash_after": cash_after,
            "initial_value": self.initial_value,
            "portfolio_value": portfolio_value,
            "transaction_cost": transaction_cost,
            "cash_weight": float(cash_amount / Fraction(self.initial_value)),
            "turnover": float(np.abs(trade_weights).sum()),
        }
        tables = {
            "trades": pd.DataFrame(
                {
                    "before": self.holdings,
                    "after": holdings_after,
                    "trade": trades,
                    "buy": buys,
                    "sell": sells,
                    "spread_cost": spread,
                    "fees": buy_fees + sell_fees,
                },
                index=ids,
            )
        }
        if tax is not None:
            decision["tax_lot_sales"] = tax["sales"]
            tables["tax_lots"] = tax["table"]
            metrics.update(
                tax_liability=float(tax_liability),
                tax_paid=float(cash_tax),
                unpaid_tax_liability=float(tax_liability - cash_tax),
                realized_taxable_gain=tax["realized_gain"],
                net_value_after_tax=float(value - tax_liability + cash_tax),
            )
        return {
            "decision": decision,
            "metrics": metrics,
            "tables": tables,
            "rows": rows,
            "tax_constraints": None if tax is None else tax["constraints"],
            "costs": {
                "spread": float(spread_cost),
                "fees": total_fees,
                **({"tax": float(tax_liability)} if tax is not None else {}),
                "total": transaction_cost,
            },
        }
