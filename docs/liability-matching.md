# Liability cash-flow matching

`LiabilityMatchingModel` chooses nonnegative asset purchases and an initial reserve to meet dated liabilities in one currency. It minimizes the required initial capital. Later asset proceeds cannot fund the original purchase; cash is conserved at every planning date.

Import the class from `qpiai_finance.treasury`. Use [funding](funding.md) when the decision also includes funding sources, debt, investments, or explicit multi-currency account transfers. Supplied sensitivity matching is an additional local-risk constraint, not a substitute for dated payment coverage.

## Constructor

```python
LiabilityMatchingModel(
    prices, cash_flows, liabilities, *, currency, as_of, dates,
    asset_ids=None, deposit_returns=0.0,
)
```

| Parameter | Type and meaning |
| --- | --- |
| `prices` | Strictly positive finite purchase-price vector, Series, or mapping, in declared currency per instrument unit. |
| `cash_flows` | Planning-date × asset matrix of signed per-unit cash receipts: aligned DataFrame, supported column mapping, dense array, or sparse matrix. All entries at `as_of` must be zero. |
| `liabilities` | Complete nonnegative finite payment vector, Series, or mapping over planning dates. |
| `currency` | Uppercase three-letter currency code for prices, cash flows, liabilities, capital, and cash. |
| `as_of` | Calendar purchase/valuation date. |
| `dates` | Nonempty unique strictly increasing calendar dates; the first must equal `as_of`. |
| `asset_ids` | Optional unique string/integer asset identifiers; inferred from labeled prices or assigned positional integers. |
| `deposit_returns` | Finite interval return fractions, scalar or complete dated vector, Series, or mapping. Values must be at least `-1`; the first date's return must be zero. A scalar is broadcast and its first entry set to zero. |

Date-indexed inputs align to the complete planning grid; array rows follow `dates` and columns follow `asset_ids`. Dated payment, return, and cash-bound inputs accept Series or mappings for labels; DataFrames are accepted for the asset cash-flow matrix. The model does not price instruments, interpolate omitted cash-flow dates, infer interest accrual, or convert currencies. See [data](data.md) and [cash flows](cashflows.md) for the numeric and date conventions.

Read-only properties are `asset_ids` (detached Index), `dates` (detached DatetimeIndex), and `currency` (string).

## Cash and initial-capital equations

For holdings $q_i\geq0$, capital $K$, prices $p_i$, per-unit receipts $A_{ti}$, liabilities $L_t$, and deposit returns $r_t$:

$$
C_0=K-p^\top q-L_0,\qquad C_t=(1+r_t)C_{t-1}+A_tq-L_t\quad(t>0).
$$


Minimize $K$ while satisfying all holdings, cash, capital, lot, and configured sensitivity constraints. Cash cannot be negative by default. The linear formulation eliminates $K$ using purchase outlay plus `cash_0` plus the as-of liability; the source objective and results restore the initial capital.

## Configure holdings and liquidity

All configuration methods modify the model and return `self`.

```python
model.limit_holdings(*, lower=0.0, upper=None)
model.buy_in_lots(lot_sizes)
model.limit_cash(*, minimum=0.0, maximum=None)
model.limit_initial_capital(*, maximum)
```

`limit_holdings` uses instrument quantities. Bounds are finite scalars or complete asset vectors, Series, or mappings. `lower` must be nonnegative and must not exceed `upper`; `upper=None` leaves the upper side unbounded. Default holdings range from zero to infinity.

`buy_in_lots` accepts a strictly positive finite scalar or complete asset vector and requires holdings to be integer multiples of those quantities. It changes the class from LP to MILP. Quantities, not lot counts, are returned in financial results.

`limit_cash` accepts nonnegative finite scalar or complete dated bounds using the same dated formats as `deposit_returns`. The minimum must not exceed the maximum; `maximum=None` leaves the upper side unbounded. Default cash has a zero floor and no upper bound at every date. `limit_initial_capital` sets a finite nonnegative amount cap. The capital cap is imposed on purchase outlay, initial retained cash, and the as-of liability together.

## Match supplied sensitivities

```python
model.match_sensitivities(
    sensitivities, target, *, risk_units, risk_ids=None,
)
```

Requires `sensitivities @ holdings == target`. `sensitivities` is a risk × asset matrix: DataFrame, supported column mapping, dense array, or sparse matrix. `risk_ids` optionally supplies unique row identifiers; labeled rows or positional integers are used otherwise. `target` is a complete finite risk vector, Series, or mapping of total signed liability sensitivities.

`risk_units` is a nonblank string applied to all rows, or one nonblank string per risk row as a sequence/Series/mapping. A target is a total economic sensitivity in those units; an unweighted duration or percentage is not automatically the correct target. Repeated calls replace the complete matching matrix. Prices and liability Greeks are not inferred from cash flows.

## Solve and inspect

Use root `validate`, `inspect`, and `solve` with the [execution contract](solving.md). The mathematical class is LP without lots and MILP with lots. Default execution uses Opt locally; supported explicit platform execution and external solver selection follow their normal capability rules. Every Finance solve requires an Opt client.

```python
model.to_matrix()
model.to_model(*, return_variables=False)
model.to_cvxpy()
```

`to_matrix` returns a sparse Opt matrix-input dictionary for the complete equivalent LP/MILP. `holding_i` columns are quantities, or integer lot counts when lots are configured; `cash_t` columns are currency amounts. The objective includes the initial liability as its constant offset.

`to_model` returns a detached Opt model. With a Python boolean `return_variables=True`, it returns `(model, expressions)`. `to_cvxpy` returns `(problem, expressions)`. Both expression dictionaries contain asset-indexed `holdings` in actual instrument units, dated `cash_balances`, and scalar `initial_capital` in currency units. Mutating an export does not alter the source Finance model. See [custom models](custom-models.md) for explicit Opt compilation and recovery.

## Evaluate a proposed reserve

```python
model.evaluate(holdings, *, initial_capital, tolerance=1e-7)
```

`holdings` is a complete finite vector, Series, or mapping of instrument quantities. `initial_capital` is a finite real amount supplied explicitly; negative amounts fail the financial constraint check. `tolerance` is a finite nonnegative absolute scalar, default `1e-7`.

Returns `objective`, `feasible`, `constraints`, `metrics`, `tables`, `decision`, and `costs`. It recalculates purchase cost, every dated cash balance, holdings/lot limits, initial capital, and supplied sensitivity equalities. Cash and sensitivity residuals use original products before reported rounding. Units are included in constraint rows. Evaluation requires no authentication and does not optimize an omitted reserve.

## Result contract

The objective and `objective_unit` are initial capital and the declared currency. `decision["holdings"]` is an asset-indexed Series named `quantity`; `decision["cash_balances"]` is a dated Series named `cash`. Convenience properties expose both.

| Location | Contents |
| --- | --- |
| `metrics` | `initial_capital`, `purchase_cost`, `initial_uninvested_cash`, `final_cash`. Initial uninvested cash is capital minus purchases, before paying the as-of liability. |
| `costs` | `initial_capital`, `purchase_cost`, `currency`. |
| `tables["liability_coverage"]` | Date-indexed `opening_cash`, `deposit_interest`, `asset_cash_flow`, `liability`, `purchase_outlay`, `closing_cash`, `cash_buffer`, `currency`. |
| `tables["holdings"]` | Asset-indexed `quantity`, `price`, `purchase_value`, `currency`. |
| `tables["sensitivity_matching"]` | When configured: risk-indexed `actual`, `target`, `residual`, `unit`. |

Solving additionally checks lot reconstruction and reconciles solver cash columns with independently calculated balances. The variable-elimination transformation records how capital was restored. Check financial feasibility and proof scope as described in [results](results.md). For replay, the result's recorded initial capital is a primary input alongside its holdings.

Numeric decision entries, metrics, and monetary table columns are floats. On the first date, `opening_cash` is the supplied initial capital; thereafter it is the previous closing cash. `purchase_outlay` is charged only on the first date. `cash_buffer` is the configured minimum closing balance. Sensitivity `residual` is actual minus target in the declared risk unit. Holding-bound constraints use `instrument_units`, lot residuals use `lots`, cash/capital constraints use currency, and sensitivity equalities use their declared risk units.

Invalid prices, labels, dates, first-date cash flows, deposit returns, bounds, or sensitivity dimensions raise `TypeError` or `ValueError`. Contradictory but structurally valid liabilities and limits can produce an infeasible optimization result. Plot the dated outcome with `plot.liability_coverage`.
