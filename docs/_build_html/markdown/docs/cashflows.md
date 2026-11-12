# Cash-flow calculations

Import `bullet_loan_cash_flows`, `discount_cash_flows`, and `present_value` from `qpiai_finance.cashflows`. These functions evaluate supplied contracts and valuation inputs. They do not choose funding, calibrate curves, or execute transactions.

Calendar dates accept ISO `YYYY-MM-DD` strings, `datetime.date`, or midnight `datetime.datetime`, `pandas.Timestamp`, and `numpy.datetime64` values without a timezone. Currency codes are uppercase ASCII three-letter strings. Amounts and rates are finite real numbers under the [numeric conventions](data.md).

## Bullet-loan cash flows

```python
bullet_loan_cash_flows(
    principal, *, draw_date, repayment_date, currency,
    interest=0.0, fee=0.0, fixed_fee=0.0,
)
```

| Parameter | Contract |
| --- | --- |
| `principal` | Finite nonnegative real amount in `currency`. |
| `draw_date` | Calendar draw date. |
| `repayment_date` | Calendar date strictly after the draw. |
| `currency` | Three-letter currency code for all amounts. |
| `interest` | Full-term principal fraction paid at repayment; at least `-1`. It is not an annual rate. |
| `fee` | Nonnegative principal fraction charged at draw. |
| `fixed_fee` | Nonnegative amount charged once if principal is nonzero. |

Returns a DataFrame indexed by `draw` and `repayment`, with `date`, `currency`, and signed `amount`. Borrower receipts are positive. Net draw proceeds are `(1-fee)*principal-fixed_fee` for a nonzero draw; repayment is `-(1+interest)*principal`. A zero principal incurs no fixed fee. Negative full-term interest down to `-1` is supported. The function makes no calendar adjustment, day-count accrual, refinancing, or FX assumption.

```python
from qpiai_finance.cashflows import bullet_loan_cash_flows

flows = bullet_loan_cash_flows(
    1_000_000,
    draw_date="2027-01-04",
    repayment_date="2027-07-05",
    currency="USD",
    interest=0.03,
    fee=0.002,
)
```

The two amounts are `998000` and `-1030000` USD. Use explicit discount factors for valuation.

## Discount supplied cash flows

```python
discount_cash_flows(
    cash_flows, discount_factors, *, as_of,
    reporting_currency=None, fx_rates=None,
)
```

`cash_flows` is a nonempty DataFrame indexed by unique string/integer cash-flow identifiers. It must have exactly `date`, `currency`, and `amount` columns. Amounts are signed, finite native-currency values; dates must be on or after the calendar `as_of` date.

`discount_factors` is one of:

- A strictly positive finite scalar applying to every date/currency combination.
- A date × currency DataFrame with exactly the distinct flow dates and currencies. Labels align explicitly.
- A finite positive two-dimensional array in sorted distinct flow-date order and first-occurrence currency order.

Factors on `as_of` must equal exactly one. No curve fitting, interpolation, market calendar, interest-rate conversion, or annualization is inferred.

`reporting_currency` optionally requests valuation in a specified currency. `fx_rates` then supplies a complete vector, Series, or mapping over the distinct native currencies: reporting-currency units per native-currency unit at `as_of`. Unlabeled vectors follow first-occurrence currency order in `cash_flows`; labeled inputs align by currency. Rates must be strictly positive; the reporting currency's own rate, when present, must equal one. Omit FX rates only if every flow is already in reporting currency. Supplying FX rates without a reporting currency raises.

Returns a detached DataFrame retaining flow identifiers and the source fields, plus `discount_factor` and native-currency `present_value`. With reporting conversion it additionally contains `fx_rate`, `reporting_present_value`, and `reporting_currency`.

FX conversion here values cash flows. It does not make one currency available to pay obligations in another currency; model actual transfers explicitly in `FundingModel` when required.

## Aggregate present value

```python
present_value(
    cash_flows, discount_factors, *, as_of,
    reporting_currency=None, fx_rates=None,
)
```

Inputs and validation follow `discount_cash_flows`. Without a reporting currency, returns a Series named `present_value`, indexed by `currency` in first-occurrence order. With a reporting currency, returns one float in that currency. Original discounted products are accumulated before rounding each reported total.

Invalid columns, identifiers, dates, currencies, factors, rates, and unrepresentable values raise `TypeError` or `ValueError`. Calculations require no credentials or network access.
