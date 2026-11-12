"""Supplied acquisition lots, disposal quantities and recognized tax costs."""

from fractions import Fraction

import numpy as np
import pandas as pd

from .._arithmetic import bound_violation, product_sum
from .._validation import (
    copy_frame,
    copy_index,
    identifiers,
    lot_capacity,
    lot_quantities,
    lot_residual,
    numeric,
    scalar,
    vector,
)
from ..cashflows import _date


class _TaxLots:
    def __init__(self, lots, ids, holdings, bid_prices, *, as_of, settlement):
        required = {"asset", "quantity", "cost_basis", "acquired", "tax_rate"}
        optional = {
            "loss_credit_rate",
            "eligible",
            "quantity_step",
            "taxable_proceeds_per_unit",
        }
        if not isinstance(lots, pd.DataFrame):
            raise TypeError("tax lots must be a DataFrame")
        if (
            not lots.columns.is_unique
            or not required <= set(lots.columns)
            or set(lots.columns) - required - optional
        ):
            raise ValueError(
                f"tax lots require {sorted(required)}; "
                f"optional columns: {sorted(optional)}"
            )
        if settlement not in {"immediate", "deferred"}:
            raise ValueError(
                "tax settlement must be 'immediate' or 'deferred'"
            )
        if np.any(holdings < 0):
            raise ValueError(
                "acquisition tax lots require long owned holdings"
            )
        self.as_of = _date(as_of, "tax as_of")
        self.settlement = settlement
        self.table = copy_frame(lots)
        if len(lots):
            identifiers(lots.index, "tax lot IDs")
            identifiers(lots.asset, "tax lot assets", unique=False)
        self.assets = ids.get_indexer(lots.asset)
        if np.any(self.assets < 0):
            raise ValueError("tax lots must reference supplied asset IDs")
        self._by_asset = {}
        for j, i in enumerate(self.assets):
            self._by_asset.setdefault(int(i), []).append(j)
        self.ids = ids.copy(deep=True)
        defaults = {
            "loss_credit_rate": 0.0,
            "quantity_step": 0.0,
            "taxable_proceeds_per_unit": bid_prices[self.assets],
        }
        for field in (
            "quantity",
            "cost_basis",
            "tax_rate",
            *defaults,
        ):
            if field not in self.table:
                self.table[field] = defaults[field]
            values = self.table[field].to_numpy()
            self.table[field] = numeric(
                values.astype(float) if not len(values) else values,
                field,
                ndim=1,
            )
        table = self.table
        if (
            np.any(table.quantity <= 0)
            or np.any(table.cost_basis < 0)
            or np.any(table.quantity_step < 0)
            or np.any(table.tax_rate < 0)
            or np.any(table.tax_rate > 1)
            or np.any(table.loss_credit_rate < 0)
            or np.any(table.loss_credit_rate > 1)
        ):
            raise ValueError(
                "lot quantities must be positive, basis/steps nonnegative "
                "and tax/credit rates in [0,1]"
            )
        if "eligible" not in table:
            table["eligible"] = True
        if any(
            not isinstance(value, (bool, np.bool_)) for value in table.eligible
        ):
            raise TypeError("tax lot eligibility must contain booleans")
        table["acquired"] = [
            _date(value, "acquired") for value in table.acquired
        ]
        if any(value > self.as_of for value in table.acquired):
            raise ValueError("acquisition dates must not follow tax as_of")
        quantities = table.quantity.to_numpy()
        units = np.ones(len(table))
        for i, holding in enumerate(holdings):
            indices = self._by_asset.get(i, [])
            owned = product_sum((quantities[indices], units[indices]))
            if abs(owned - Fraction(holding)) > (
                Fraction(1e-12) * abs(Fraction(holding))
            ):
                raise ValueError(
                    "tax lot quantities must cover all owned holdings"
                )
        try:
            with np.errstate(over="raise", invalid="raise"):
                steps = table.quantity_step.to_numpy()
                counts = quantities[steps > 0] / steps[steps > 0]
                if not np.isfinite(counts).all():
                    raise ValueError("tax lot counts exceed float64 range")
                self.gain_per_unit = np.fromiter(
                    (
                        Fraction(proceeds) - Fraction(basis)
                        for proceeds, basis in zip(
                            table.taxable_proceeds_per_unit, table.cost_basis
                        )
                    ),
                    dtype=object,
                )
                self.tax_per_unit = self.gain_per_unit * np.fromiter(
                    map(
                        Fraction,
                        np.where(
                            self.gain_per_unit >= 0,
                            table.tax_rate,
                            table.loss_credit_rate,
                        ),
                    ),
                    dtype=object,
                )
                if not np.isfinite(
                    np.asarray([self.gain_per_unit, self.tax_per_unit], float)
                ).all():
                    raise ValueError(
                        "tax lot coefficients exceed float64 range"
                    )
        except (FloatingPointError, OverflowError) as error:
            raise ValueError(
                "tax lot coefficients exceed float64 range"
            ) from error
        self.minimum = self.maximum = None

    @property
    def mask(self):
        return np.bincount(self.assets, minlength=len(self.ids)) > 0

    def specification(self):
        return {
            "lots": self.table,
            "as_of": self.as_of,
            "settlement": self.settlement,
            "minimum_tax": self.minimum,
            "maximum_tax": self.maximum,
        }

    def _variable(self, j):
        step = self.table.quantity_step.iloc[j]
        return (
            f"tax_lot_count_{j}" if step else f"tax_lot_sale_{j}",
            step if step else 1.0,
        )

    def _sale_expressions(self, variables):
        quantities = []
        for j in range(len(self.table)):
            name, scale = self._variable(j)
            quantities.append(float(scale) * variables[name])
        return pd.Series(
            quantities,
            index=copy_index(self.table.index),
            name="quantity",
            dtype=object,
        )

    def add_opt(self, model, sales, prices, initial_value):
        from qpiai_opt.opt_modeller import Continuous, Integer, quicksum

        quantities = []
        for j in range(len(self.table)):
            name, scale = self._variable(j)
            maximum = (
                self.table.quantity.iloc[j] / scale
                if self.table.eligible.iloc[j]
                else 0.0
            )
            kind = Integer if self.table.quantity_step.iloc[j] else Continuous
            if kind is Integer:
                maximum = (
                    lot_capacity(self.table.quantity.iloc[j], scale)
                    if self.table.eligible.iloc[j]
                    else 0
                )
            quantity = model.add_variable(kind(name, 0, maximum)) * float(
                scale
            )
            quantities.append(quantity)
        for i, indices in self._by_asset.items():
            total = quicksum(quantities[j] for j in indices)
            model.add_constraint(
                total * float(prices[i] / initial_value) == sales[i],
                label=f"tax_lot_disposal_{i}",
            )
        tax = quicksum(
            quantity * float(rate / Fraction(initial_value))
            for quantity, rate in zip(quantities, self.tax_per_unit)
        )
        if self.minimum is not None:
            model.add_constraint(
                tax >= self.minimum / initial_value, label="minimum_tax"
            )
        if self.maximum is not None:
            model.add_constraint(
                tax <= self.maximum / initial_value, label="maximum_tax"
            )
        return tax

    def add_cvxpy(self, sales, prices, initial_value, constraints):
        import cvxpy as cp

        quantities, variables = [], {}
        for j in range(len(self.table)):
            name, scale = self._variable(j)
            maximum = (
                self.table.quantity.iloc[j] / scale
                if self.table.eligible.iloc[j]
                else 0.0
            )
            if self.table.quantity_step.iloc[j]:
                maximum = (
                    lot_capacity(self.table.quantity.iloc[j], scale)
                    if self.table.eligible.iloc[j]
                    else 0
                )
            raw = cp.Variable(
                integer=bool(self.table.quantity_step.iloc[j]),
                name=name,
                bounds=[0, maximum],
            )
            variables[name] = raw
            quantities.append(raw * scale)
        for i, indices in self._by_asset.items():
            constraints.append(
                cp.sum([quantities[j] for j in indices])
                * float(Fraction(prices[i]) / Fraction(initial_value))
                == sales[i]
            )
        tax = cp.sum(
            [
                quantity * float(rate / Fraction(initial_value))
                for quantity, rate in zip(quantities, self.tax_per_unit)
            ]
        )
        if not np.any(self.tax_per_unit) and (
            self.minimum is not None or self.maximum is not None
        ):
            # Preserve constant budget rows through SCIP's CVXPY interface.
            guard = cp.Variable(name="tax_budget_zero")
            variables["tax_budget_zero"] = guard
            constraints.append(guard == 0)
            tax += guard
        if self.minimum is not None:
            constraints.append(tax >= self.minimum / initial_value)
        if self.maximum is not None:
            constraints.append(tax <= self.maximum / initial_value)
        return tax, variables

    def recover(self, solution):
        quantities, residuals = [], {}
        for j in range(len(self.table)):
            name, scale = self._variable(j)
            raw = scalar(solution[name], name)
            recovered = (
                np.rint(raw) if self.table.quantity_step.iloc[j] else raw
            )
            if self.table.quantity_step.iloc[j]:
                residuals[f"tax_lot_integrality[{j}]"] = abs(raw - recovered)
            if not self.table.eligible.iloc[j]:
                recovered = 0.0
            recovered = max(recovered, 0.0)
            residuals[f"tax_lot_reconstruction[{j}]"] = (
                abs(raw - recovered) * scale
            )
            quantities.append(lot_quantities(recovered, scale))
        return pd.Series(
            quantities, index=copy_index(self.table.index), dtype=float
        ), residuals

    def evaluate(self, disposals, sales, tolerance, *, currency):
        if disposals is None:
            raise ValueError(
                "tax_lot_sales is required with configured tax lots"
            )
        if len(self.table):
            quantities = vector(disposals, self.table.index, "tax_lot_sales")
        else:
            quantities = numeric(list(disposals), "tax_lot_sales", ndim=1)
            if len(quantities):
                raise ValueError(
                    "tax_lot_sales must be empty without tax lots"
                )
        rows = []

        def check(name, value, low, high, unit):
            if isinstance(value, (bool, np.bool_)):
                value = int(value)
            reported = float(value)
            if not np.isfinite(reported):
                raise ValueError("tax lot calculations exceed float64 range")
            violation = 0
            if isinstance(value, Fraction) or not low <= value <= high:
                violation = bound_violation(value, low, high)
            satisfied = (
                violation == 0 if unit == "boolean" else violation <= tolerance
            )
            rows.append(
                (name, reported, low, high, float(violation), satisfied, unit)
            )

        for j, quantity in enumerate(quantities):
            check(
                f"tax_lot_quantity[{j}]",
                quantity,
                0,
                self.table.quantity.iloc[j],
                "shares",
            )
            check(
                f"tax_lot_eligibility[{j}]",
                quantity == 0 or self.table.eligible.iloc[j],
                1,
                1,
                "boolean",
            )
            step = self.table.quantity_step.iloc[j]
            if step:
                check(
                    f"tax_lot_step[{j}]",
                    lot_residual(quantity, step),
                    0,
                    0,
                    "lot_units",
                )
        units = np.ones(len(quantities))
        for i in range(len(self.ids)):
            indices = self._by_asset.get(i, [])
            check(
                f"tax_lot_sale_balance[{i}]",
                product_sum((quantities[indices], units[indices])),
                sales[i],
                sales[i],
                "shares",
            )
        source_quantities = np.fromiter(
            map(Fraction, quantities), dtype=object
        )
        gains = self.gain_per_unit * source_quantities
        taxes = self.tax_per_unit * source_quantities
        liability = product_sum((taxes, units))
        realized_gain = float(product_sum((gains, units)))
        reported_gains = np.asarray(gains, float)
        reported_taxes = np.asarray(taxes, float)
        if not np.isfinite([reported_gains, reported_taxes]).all():
            raise ValueError("tax lot calculations exceed float64 range")
        check(
            "tax_liability",
            liability,
            -np.inf if self.minimum is None else self.minimum,
            np.inf if self.maximum is None else self.maximum,
            currency,
        )
        table = copy_frame(self.table)
        table["holding_days"] = [
            (self.as_of.date() - value.date()).days for value in table.acquired
        ]
        table["sold"] = quantities
        table["remaining"] = table.quantity - quantities
        table["taxable_gain"] = reported_gains
        table["tax_liability"] = reported_taxes
        table.attrs.update(
            currency=currency, as_of=self.as_of, settlement=self.settlement
        )
        return {
            "tax": liability,
            "realized_gain": realized_gain,
            "sales": pd.Series(
                quantities, index=copy_index(table.index), name="quantity"
            ),
            "table": table,
            "constraints": pd.DataFrame(
                rows,
                columns=[
                    "constraint",
                    "value",
                    "lower",
                    "upper",
                    "violation",
                    "satisfied",
                    "unit",
                ],
            ).set_index("constraint"),
        }
