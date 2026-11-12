"""Dated cash-flow discounting and explicit currency conversion."""

from collections.abc import Mapping
from datetime import date, datetime
from fractions import Fraction
from itertools import repeat
from math import frexp, ldexp

import numpy as np
import pandas as pd

from ._arithmetic import float_upper_bound, product_sum
from ._validation import (
    copy_frame,
    identifiers,
    numeric,
    same_labels,
    scalar,
    vector,
)

__all__ = ["bullet_loan_cash_flows", "discount_cash_flows", "present_value"]


def _date(value, name):
    if isinstance(value, str):
        if len(value) != 10 or value[4] != "-" or value[7] != "-":
            raise ValueError(f"{name} must use an ISO YYYY-MM-DD date")
    elif not isinstance(value, (date, datetime, pd.Timestamp, np.datetime64)):
        raise TypeError(f"{name} must be a calendar date")
    try:
        parsed = pd.Timestamp(value)
    except (ValueError, TypeError) as error:
        raise ValueError(f"{name} is not a valid calendar date") from error
    if (
        pd.isna(parsed)
        or parsed.tzinfo is not None
        or parsed != parsed.normalize()
    ):
        raise ValueError(f"{name} must be a date without time or timezone")
    return parsed


def _dates(values, name, *, ordered=False):
    parsed = pd.DatetimeIndex([_date(value, name) for value in values])
    if not len(parsed) or not parsed.is_unique:
        raise ValueError(f"{name} must be nonempty and unique")
    if ordered and not parsed.is_monotonic_increasing:
        raise ValueError(f"{name} must be strictly increasing")
    return parsed


def _period_index(index, periods, name):
    index = (
        _dates(index, name)
        if isinstance(periods, pd.DatetimeIndex)
        else identifiers(index, name)
    )
    if set(index) != set(periods):
        raise ValueError(f"{name} must match the planning periods")
    return index


def _period_vector(values, periods, name, *, broadcast=True):
    if isinstance(values, Mapping):
        values = pd.Series(values)
    if isinstance(values, pd.Series):
        values = values.copy()
        values.index = _period_index(values.index, periods, name)
        values = values.reindex(periods).to_numpy()
    return vector(values, periods, name, broadcast=broadcast)


def _currency(value):
    if (
        not isinstance(value, str)
        or len(value) != 3
        or not value.isascii()
        or not value.isalpha()
        or value != value.upper()
    ):
        raise ValueError("currency must be an uppercase three-letter code")
    return value


def _loan_rates(interest, fee, fixed_fee):
    return {
        "interest": scalar(interest, "interest", minimum=-1),
        "fee": scalar(fee, "fee", minimum=0),
        "fixed_fee": scalar(fixed_fee, "fixed_fee", minimum=0),
    }


def _bullet_loan_terms(
    *, maximum, interest, fee, fixed_fee, minimum, lot_size
):
    maximum = scalar(maximum, "maximum", minimum=0)
    minimum = scalar(minimum, "minimum", minimum=0, maximum=maximum)
    rates = _loan_rates(interest, fee, fixed_fee)
    if lot_size is not None:
        lot_size = scalar(lot_size, "lot_size", minimum=0)
        if lot_size == 0:
            raise ValueError("lot_size must be positive")
    if rates["fixed_fee"] and not (minimum > 0 or lot_size is not None):
        raise ValueError("a fixed fee requires a positive minimum or lot")
    return dict(maximum=maximum, **rates, minimum=minimum, lot_size=lot_size)


def _loan_fixed_charge(principal, fixed_fee, active):
    if not fixed_fee:
        return 0
    activation = principal > 0 if active is None else active
    return fixed_fee * activation


def _loan_amounts(
    principal, interest, fee=0.0, fixed_fee=0.0, *, active=None, original=False
):
    """Calculate net proceeds, repayment, fees and full-term interest."""
    if original:
        principal, interest, fee, fixed_fee = map(
            Fraction, (principal, interest, fee, fixed_fee)
        )
    fixed_charge = _loan_fixed_charge(principal, fixed_fee, active)
    return (
        (1 - fee) * principal - fixed_charge,
        (1 + interest) * principal,
        fee * principal + fixed_charge,
        interest * principal,
    )


def _loan_expense(
    interest,
    fees=0.0,
    *,
    draw_discount=1.0,
    repayment_discount=1.0,
    original=False,
):
    """Discount contractual interest and origination fee amounts."""
    if original:
        interest, fees = map(Fraction, (interest, fees))
        draw_discount, repayment_discount = map(
            Fraction, (draw_discount, repayment_discount)
        )
    return fees * draw_discount + interest * repayment_discount


def _loan_cash_terms(
    principal, scale, interest, fee, *, maximum, fixed_fee, active,
    name, variable, equation,
):
    """Compile draw/repayment terms without merging an unrepresentable rate.

    The callbacks declare bounded continuous amounts and zero-valued linear
    equations. Terms are (variable, coefficient) pairs for either algebraic
    or sparse model builders. Keep the compact form when its coefficients
    are exact; otherwise link actual principal, interest and origination
    fees separately using the original contract coefficients.
    """
    maximum = Fraction(maximum)
    if maximum == 0:
        return [], [], [], []

    def amount_equation(terms, label):
        nonzero = [abs(value) for _, value in terms if value]
        smallest, largest = min(nonzero), max(nonzero)
        # Keep linked amounts inside the supported matrix range when possible.
        # Binary scaling preserves each original coefficient exactly.
        power = min(max(0, -25 - frexp(smallest)[1]),
                    46 - frexp(largest)[1])
        if power:
            scaled = [(column, ldexp(value, power)) for column, value in terms]
            if all(Fraction(new) == Fraction(old) * Fraction(2)**power
                   for (_, old), (_, new) in zip(terms, scaled)):
                terms = scaled
        equation(terms, label)

    def coefficients(unit):
        result = []
        for value in _loan_amounts(unit, interest, fee, original=True):
            try:
                number = float(value)
                exact = Fraction(number) == value
            except OverflowError:
                exact = False
            result.append(number if exact else None)
        return result

    proceeds, repayment, fees, interest_amount = coefficients(scale)
    if any(value is None for value in (
        proceeds, repayment, fees, interest_amount
    )):
        if scale != 1:
            amount = variable(
                f"{name}_principal", 0, float_upper_bound(maximum)
            )
            amount_equation(
                [(amount, 1), (principal, -scale)], f"{name}_principal"
            )
            principal = amount
        proceeds, repayment, fees, interest_amount = coefficients(1)
    if proceeds is None:
        maximum_fee = Fraction(fee) * maximum
        charge = variable(
            f"{name}_variable_fee", 0, float_upper_bound(maximum_fee)
        )
        amount_equation(
            [(charge, 1), (principal, -fee)], f"{name}_variable_fee"
        )
        draw = [(principal, 1), (charge, -1)]
        fees = [(charge, 1)]
    else:
        draw = [(principal, proceeds)]
        fees = [(principal, fees)]
    if fixed_fee:
        draw.append((active, -fixed_fee))
        fees.append((active, fixed_fee))
    if repayment is None:
        maximum_interest = Fraction(interest) * maximum
        charge = variable(
            f"{name}_interest",
            -float_upper_bound(-min(maximum_interest, 0)),
            float_upper_bound(max(maximum_interest, 0)),
        )
        amount_equation(
            [(charge, 1), (principal, -interest)], f"{name}_interest"
        )
        due = [(principal, 1), (charge, 1)]
        interest_amount = [(charge, 1)]
    else:
        due = [(principal, repayment)]
        interest_amount = [(principal, interest_amount)]
    return draw, due, fees, interest_amount


def bullet_loan_cash_flows(
    principal,
    *,
    draw_date,
    repayment_date,
    currency,
    interest=0.0,
    fee=0.0,
    fixed_fee=0.0,
):
    """Return a borrower's dated cash flows for a supplied bullet principal.

    Principal is nonnegative in currency units. interest is the full-term
    principal fraction paid at repayment, not an annual rate; fee is the
    fraction charged at draw. fixed_fee is charged once for a nonzero draw.
    Negative interest down to -1 is permitted. A zero principal has no fees.

    The returned DataFrame has date, currency and signed amount columns,
    with draw and repayment rows. Receipts are positive: net draw proceeds
    are (1-fee)*principal minus the applicable fixed fee; repayment is
    -(1+interest)*principal. Net amounts avoid cancellation between large
    principal and charge entries. Pass the table to discount_cash_flows or
    present_value. Dates are explicit calendar dates with repayment after
    draw; no calendar, accrual, refinancing or FX assumptions are made.
    This calculates cash flows; it neither chooses nor executes a loan.
    """
    principal = scalar(principal, "principal", minimum=0)
    draw = _date(draw_date, "draw_date")
    repayment = _date(repayment_date, "repayment_date")
    if repayment <= draw:
        raise ValueError("repayment_date must follow draw_date")
    currency = _currency(currency)
    rates = _loan_rates(interest, fee, fixed_fee)
    proceeds, repayment_amount, _, _ = _loan_amounts(
        principal, **rates, original=True
    )
    try:
        values = [float(proceeds), float(-repayment_amount)]
    except OverflowError as error:
        raise ValueError("loan cash flows exceed float64 range") from error
    amounts = numeric(
        values,
        "loan cash flows",
        ndim=1,
    )
    return pd.DataFrame(
        {
            "date": [draw, repayment],
            "currency": currency,
            "amount": amounts,
        },
        index=["draw", "repayment"],
    )


def _reporting_rates(currencies, reporting_currency, fx_rates):
    _currency(reporting_currency)
    currencies = pd.Index(currencies).drop_duplicates()
    for currency in currencies:
        _currency(currency)
    if fx_rates is None:
        if any(currency != reporting_currency for currency in currencies):
            raise ValueError(
                "multiple currencies require explicit reporting FX rates"
            )
        return pd.Series(1.0, index=currencies, name="fx_rate")
    rates = vector(fx_rates, currencies, "fx_rates")
    if np.any(rates <= 0):
        raise ValueError("FX rates must be strictly positive")
    if reporting_currency in currencies:
        if rates[currencies.get_loc(reporting_currency)] != 1.0:
            raise ValueError("reporting-currency FX rate must equal one")
    return pd.Series(rates, index=currencies, name="fx_rate")


def _dated_values(values, dates, columns, name):
    if isinstance(values, pd.DataFrame):
        values = values.copy()
        values.index = _dates(values.index, f"{name} dates")
        if set(values.index) != set(dates):
            raise ValueError(f"{name} dates must match the planning dates")
        same_labels(values.columns, columns, f"{name} columns")
        values = values.reindex(index=dates, columns=columns).to_numpy()
    elif np.ndim(values) == 0:
        values = np.full((len(dates), len(columns)), scalar(values, name))
    array = numeric(values, name, ndim=2)
    if array.shape != (len(dates), len(columns)):
        raise ValueError(
            f"{name} must have shape {(len(dates), len(columns))}"
        )
    return array


def discount_cash_flows(
    cash_flows,
    discount_factors,
    *,
    as_of,
    reporting_currency=None,
    fx_rates=None,
):
    """Discount a table of date, currency and signed amount cash flows.

    Rows have unique cash-flow identifiers. Discount factors are supplied
    explicitly as a date-by-currency DataFrame or ordered array; a scalar
    applies to every flow. No curve fitting, interpolation, calendar
    adjustment or rate annualization is inferred. As-of cash flows use
    factor one. Earlier cash flows are rejected.

    FX rates, if requested, are reporting-currency units per native unit
    at as_of. This values cash flows; it does not execute currency trades
    or make one currency available to pay another currency's obligations.
    """
    table, native, reporting = _cash_flow_values(
        cash_flows,
        discount_factors,
        as_of=as_of,
        reporting_currency=reporting_currency,
        fx_rates=fx_rates,
    )
    try:
        table.insert(
            table.columns.get_loc("discount_factor") + 1,
            "present_value",
            np.asarray(native, dtype=float),
        )
        if reporting is not None:
            table["reporting_present_value"] = np.asarray(
                reporting, dtype=float
            )
            table["reporting_currency"] = reporting_currency
    except OverflowError as error:
        raise ValueError(
            "discounted cash flows exceed float64 range"
        ) from error
    numeric(
        table.select_dtypes(include=np.number).to_numpy(),
        "discounted cash flows",
        ndim=2,
    )
    return table


def _cash_flow_values(
    cash_flows, discount_factors, *, as_of, reporting_currency, fx_rates
):
    """Align contractual inputs and retain original discounted FX values."""
    as_of = _date(as_of, "as_of")
    if not isinstance(cash_flows, pd.DataFrame):
        raise TypeError("cash_flows must be a DataFrame")
    if set(cash_flows.columns) != {"date", "currency", "amount"}:
        raise ValueError(
            "cash_flows requires date, currency and amount columns"
        )
    identifiers(cash_flows.index, "cash-flow IDs")
    table = copy_frame(cash_flows)
    table["date"] = [_date(value, "cash-flow date") for value in table.date]
    if (table.date < as_of).any():
        raise ValueError("cash flows before as_of are not future cash flows")
    table["currency"] = [_currency(value) for value in table.currency]
    table["amount"] = numeric(table.amount.to_numpy(), "amount", ndim=1)
    dates = pd.DatetimeIndex(table.date.unique()).sort_values()
    currencies = pd.Index(table.currency.unique())
    factors = _dated_values(
        discount_factors, dates, currencies, "discount_factors"
    )
    if np.any(factors <= 0):
        raise ValueError("discount factors must be strictly positive")
    if as_of in dates and np.any(factors[dates.get_loc(as_of)] != 1):
        raise ValueError("as-of discount factors must equal one")
    row = dates.get_indexer(table.date)
    column = currencies.get_indexer(table.currency)
    table["discount_factor"] = factors[row, column]
    native = [
        Fraction(amount) * Fraction(factor)
        for amount, factor in zip(table.amount, table.discount_factor)
    ]
    reporting = None
    if reporting_currency is not None:
        rates = _reporting_rates(currencies, reporting_currency, fx_rates)
        table["fx_rate"] = table.currency.map(rates)
        reporting = [
            value * Fraction(rate)
            for value, rate in zip(native, table.fx_rate)
        ]
    elif fx_rates is not None:
        raise ValueError("FX rates require reporting_currency")
    return table, native, reporting


def present_value(
    cash_flows,
    discount_factors,
    *,
    as_of,
    reporting_currency=None,
    fx_rates=None,
):
    """Return a value by currency, or an explicit reporting-currency value.

    Accumulate original discounted cash flows before rounding currency totals.
    """
    table, native, reporting = _cash_flow_values(
        cash_flows,
        discount_factors,
        as_of=as_of,
        reporting_currency=reporting_currency,
        fx_rates=fx_rates,
    )
    try:
        if reporting is not None:
            total = float(product_sum((repeat(1), reporting)))
            return scalar(total, "present value")
        groups = table.groupby("currency", sort=False).indices
        values = [
            float(product_sum((repeat(1), (native[i] for i in indices))))
            for indices in groups.values()
        ]
    except OverflowError as error:
        raise ValueError("present value exceeds float64 range") from error
    return pd.Series(
        numeric(values, "present value", ndim=1),
        index=pd.Index(groups, name="currency"),
        name="present_value",
    )
