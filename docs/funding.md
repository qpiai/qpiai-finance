# Funding and liquidity

`FundingModel` plans account cash, explicit borrowing, currency transfers, and bounded investments against contractual cash obligations. It minimizes discounted funding expense, with expected, worst-case, and expected-shortfall measures for adaptive plans. Import it from `qpiai_finance.treasury`.

Native account currencies govern cash conservation. Reporting FX values expense; explicit transfer quotes exchange cash; facility FX values commitment usage. These three inputs have different purposes. Cash flows within a planning bucket net simultaneously. For ordered intraday payment processing, use [payment settlement](settlement.md).

## Constructor and planning grid

```python
FundingModel(
    cash_flows, *, balances, as_of, dates=None, tree=None,
    reporting_currency=None, fx_rates=None,
    deposit_returns=0.0, discount_factors=1.0,
)
```

Supply exactly one of `dates` or `tree`.

| Argument | Type, default, and meaning |
| --- | --- |
| `cash_flows` | Required pandas DataFrame with exactly `account`, `date`, `amount` for a dated plan, or `account`, `node`, `amount` for an adaptive plan. Rows have unique string/integer IDs when nonempty. Empty tables retaining these columns are allowed. Amounts are finite signed native-account currency: positive receipts, negative obligations. Repeated account/period pairs are summed. |
| `balances` | Required nonempty account-indexed DataFrame with exactly `currency`, `cash`. IDs are unique nonblank strings/integers; currencies are uppercase three-letter codes. Opening `cash` is finite nonnegative native currency, available immediately before `as_of` events. Represent opening debt separately. |
| `as_of` | Required calendar date for a dated plan or date-clock tree; timezone-aware instant for an aware tree. Must equal the first planning time exactly. |
| `dates` | Optional nonempty unique strictly increasing calendar-date sequence beginning at `as_of`. All contractual dates must belong to this grid. |
| `tree` | Optional `ScenarioTree`, copied on input. Rows of account grids use its node IDs. Tree time begins at `as_of`. See [information trees](scenarios.md). |
| `reporting_currency` | Optional uppercase three-letter code. Inferred only when every account has the same currency; required otherwise. |
| `fx_rates` | Optional finite strictly positive complete currency vector, Series, or mapping of reporting-currency units per native-currency unit at `as_of`. Required for any non-reporting currency. A reporting-currency entry must equal one. Default `None` uses one only when all accounts use reporting currency. |
| `deposit_returns` | Finite period-by-account grid; scalar, aligned DataFrame, or ordered two-dimensional array. Default zero. Parent-to-period simple returns must be at least `-1`; the root/first row must be zero. Scalar input is broadcast with its first row reset to zero. |
| `discount_factors` | Strictly positive finite period-by-account grid in the same forms; default one. First/root factors must equal one. These discount expense in native currency before fixed reporting FX conversion. |

Here and below, **period** means date for dated plans and node for adaptive plans. Account grids have exactly all period rows and account columns. A scalar broadcasts across the whole grid; per-account one-dimensional vectors do not. Labelled grids align both axes, rejecting missing/extra/duplicate labels. Full period vectors accept scalars, complete Series/mappings, or ordered one-dimensional arrays unless explicitly stated otherwise.

In a tree, a decision at one observed node is shared by all cases passing through it. Child cash starts from that child's actual parent; alternative branches never share cash. A conditional loan repays at every descendant node at its maturity stage, once on each realized history. Hard limits apply to every node, including zero-probability and probability-free stress cases.

## Properties

| Property | Type and contents |
| --- | --- |
| `account_ids` | Detached pandas Index in account input order. |
| `investment_ids` | Index named `investment_id`, in purchase-opportunity insertion order. |
| `funding_ids` | Index named `funding_id`: new funding IDs in insertion order, then opening-debt IDs in insertion order. Defines unlabelled funding-exposure coefficient order. |
| `dates` | Detached ordered stage-time index, including aware timestamps for an aware tree. For a tree this is the stage clock, not one row per node. |
| `tree` | Detached `ScenarioTree`, or `None`. |
| `node_ids` | Detached node index for an adaptive plan; raises `ValueError` for a dated plan. |
| `reporting_currency` | `str` currency of the expense objective. |

## New funding contracts

```python
model.add_funding(
    funding_id, *, account, draw_date=None, repayment_date=None,
    draw_node=None, repayment_stage=None, maximum,
    interest=0.0, fee=0.0, fixed_fee=0.0, minimum=0.0, lot_size=None,
)
```

All configuration methods return `self`. IDs are nonblank strings/integers. New funding and opening-debt IDs must be unique across those two contract collections. `account` must be supplied in `balances`.

| Parameter | Type, default, and meaning |
| --- | --- |
| `draw_date`, `repayment_date` | Calendar dates on the dated grid, with repayment strictly after draw. Both are required in a dated plan despite their signature defaults. |
| `draw_node`, `repayment_stage` | Supplied node ID and later stage ID for an adaptive plan. Required in that mode. Stage timestamps use the tree's date/aware clock when timestamp-labelled. Date arguments must remain `None`. |
| `maximum` | Required finite nonnegative principal cap in account currency. |
| `interest` | Finite total-term interest fraction, at least `-1`, paid at repayment; default zero. It is not an annual rate. |
| `fee` | Finite nonnegative principal fraction, paid at draw; default zero. No upper bound is imposed; fees above principal can make net draw proceeds negative. |
| `fixed_fee` | Finite nonnegative origination charge in account currency; default zero. Positive charges require a positive `minimum` or configured `lot_size`. |
| `minimum` | Finite amount in `[0, maximum]`; default zero. Permits zero borrowing or at least this amount. |
| `lot_size` | Optional strictly positive finite principal step; default `None` allows continuous principal. With lots, activation requires at least one lot. |

For principal `p`, draw proceeds are `(1-fee)*p - fixed_fee` when active, and repayment is `(1+interest)*p`. Origination fees and full-term interest are expense; principal repayment is cash movement. Fixed charges apply only to positive draws. Available borrowing is exactly the set of supplied contracts, each with repayment within the planning horizon.

## Opening debt and cash transfers

```python
model.add_existing_debt(
    debt_id, *, account, principal, repayment_date=None,
    repayment_stage=None, interest=0.0,
)
model.add_transfer(
    transfer_id, *, from_account, to_account, date=None, node=None,
    maximum, exchange_rate=None, fee=0.0,
)
```

Opening debt takes a strictly positive finite `principal` in the account's currency. `interest` is its remaining full-term interest fraction, at least `-1`, default zero. Supply a repayment grid date for a dated plan or a supplied maturity stage for a tree; the other argument must remain `None`. Maturity may be the initial stage. It repays principal and remaining interest without adding a historical draw to opening cash.

Transfer IDs are unique within transfers. `from_account` and `to_account` are distinct supplied accounts. Supply a grid `date` for a dated plan or supplied `node` for an adaptive plan. Required finite nonnegative `maximum` caps the sent amount in source currency. Finite nonnegative `fee` defaults to zero and is an additional source-currency fraction. Strictly positive finite `exchange_rate` gives destination units per source unit; it is required across currencies, defaults to one for same-currency transfers, and must equal one for those transfers. Sending `x` debits `(1+fee)*x` from the source and credits `exchange_rate*x` to the destination in that bucket.

## Investment purchases

```python
model.add_investment(
    investment_id, *, account, price, cash_flows, upper, lower=0.0,
    lot_size=None, purchase_date=None, purchase_node=None,
)
```

An investment ID identifies one purchase opportunity and must be unique within investments. Use separate IDs for conditional purchases of the same instrument at different nodes.

`price` is strictly positive finite all-in account-currency cash per purchased unit. Required finite `upper` and default-zero `lower` bound actual nonnegative units, with `lower <= upper`. Lower is a mandatory quantity, not a conditional activation minimum. Optional strictly positive finite `lot_size` restricts purchased units to whole lots.

Supply the dated-grid `purchase_date` or adaptive `purchase_node`, with the other argument `None`. Required `cash_flows` is a complete finite signed period vector, Series, or mapping of native-currency flows per purchased unit; scalar broadcasting is disabled. It must be zero at/before purchase and on every other information history. Later negative amounts represent capital calls. Purchase outlay and subsequent flows enter native cash conservation. They are not added to the funding-expense objective as investment performance.

## Cash, debt, and shared facilities

```python
model.limit_cash(*, minimum=0.0, maximum=None)
model.limit_debt(*, maximum)
model.limit_facility(
    facility_id, funding_ids, *, maximum, currency,
    fx_rates=None, reserved=0.0,
)
```

`limit_cash` sets period-by-account native-currency closing-cash bounds. `minimum` defaults to zero; `maximum=None` removes upper limits. Configured inputs must be finite and satisfy `0 <= minimum <= maximum`. `limit_debt` takes a required finite nonnegative account grid bounding outstanding principal after the period's draws and repayments. Initially debt has no upper limit. Cash must always remain nonnegative; there is no implicit overdraft.

`limit_facility` sets one shared commitment cap in a declared uppercase three-letter `currency`. `funding_ids` is a required nonempty sequence of distinct already-added new funding/opening-debt IDs. Membership may overlap across facilities to represent aggregate limits and sublimits. Reusing `facility_id` replaces that limit after validation; other facilities remain.

Required `maximum` and default-zero `reserved` are finite nonnegative period vectors in facility currency. Reserved usage represents outside-model commitments and moves no cash. Reserved usage above capacity makes the constraints infeasible. Principal counts on `[draw, repayment)` on its actual history; same-period repayments release capacity before closing utilization is measured. This is not lifetime cumulative borrowing or intraday rollover certification.

Facility `fx_rates` value native principal in facility-currency units per native unit. Supply fixed currency-indexed vectors/Series/mappings or full period-by-currency DataFrames/arrays. Currency columns follow first occurrence among facility members. A scalar quote is allowed only for one native currency. Rates must be finite strictly positive; facility-currency rates equal one. Default `None` is valid only when all member principals use facility currency. These rates neither use reporting FX implicitly nor create cash transfers.

## Balance-sheet exposures

```python
model.limit_exposure(
    exposure_id, *, unit, investment_coefficients=None,
    funding_coefficients=None, cash_coefficients=None,
    external_exposure=0.0, lower=None, upper=None,
)
```

This method bounds one supplied additive exposure at each period. Required `unit` is a nonblank string. Signed coefficients can express sensitivity matching or net-value floors; nonnegative capital coefficients can express capital budgets. Pricing, FX, regulatory classification, and risk weights are supplied inputs.

Each optional coefficient block accepts a finite scalar or complete ordered member vector/array, a Series/mapping selecting known member IDs with fixed coefficients, or a DataFrame with complete period rows and selected member columns. Two-dimensional arrays/sparse matrices use every current member in public order. Omitted blocks contribute zero. Coefficients are in declared exposure units per purchased investment unit, outstanding native-currency principal, or native-currency closing cash. At least one bound is required, but an exposure may consist entirely of outside-book amounts.

`external_exposure` is a finite signed period vector, default zero. `lower` and `upper` are optional finite signed period vectors; `None` leaves that side unbounded. Require lower no greater than upper. Equal bounds impose matching. Outside liability values must exclude amounts already represented in model balances.

Investment exposure counts on the post-purchase realized history through the final stage. Cash-flow receipt does not determine derecognition: supply zero coefficients after the asset ceases to belong in the exposure. Funding principal counts until, excluding, repayment. Cash uses each closing balance. Reusing an exposure ID replaces that mandate; adding contracts afterward does not expand existing membership. Configure it again to include new positions.

## Expense measures

```python
model.minimize_expected_cost()
model.minimize_worst_case_cost()
model.minimize_expected_shortfall(*, confidence=0.95)
model.limit_expected_shortfall(maximum, *, confidence=0.95)
```

Expense is discounted new/opening-debt interest, new-funding origination fees, and transfer fees in reporting currency. It excludes principal, investment outlays/proceeds, and deposit interest earned on cash. Negative full-term loan interest can produce signed expense.

The default `minimize_expected_cost` uses supplied tree case probabilities; no probabilities are inferred. A probability-free tree can be constructed, but must select worst-case cost before export, evaluation, validation, or solve. For a dated plan the complete-path expense is the objective under either expected or worst-case selection.

Worst-case selection considers every complete path, including zero-probability cases. Both ES methods require a scenario tree with explicit probabilities. `confidence` is finite and strictly in `(0,1)`, default `0.95`. ES is the weighted upper-tail mean expense with fractional boundary mass. `maximum` is a required finite signed reporting-currency scalar; a negative cap requires sufficiently negative tail expense. The hard cap has its own confidence, remains under any objective, and is replaced on repeated calls. Zero-probability cases do not enter ES but retain all hard node limits.

## Export, execution, and evaluation

```python
model.to_model(*, return_variables=False)
model.to_cvxpy()
model.evaluate(
    draws=None, transfers=None, *, investments=None, tolerance=1e-7,
)
```

The model is LP unless funding lots, conditional minimum draws, fixed origination fees, or investment lots introduce integer decisions, giving MILP. Opt is the default execution route. Every Finance solve requires Opt authentication; [solving](solving.md) defines options and modes. Eligible algebraic exports also support the explicit representation controls described in [custom models](custom-models.md).

`to_model()` returns a detached Opt model; boolean `return_variables=True` returns `(model, expressions)`. `to_cvxpy()` returns `(cvxpy.Problem, expressions)`. The financial expression mapping contains:

| Key | pandas expression structure and units |
| --- | --- |
| `draws` | New funding-ID Series named `principal`, in actual native principal, including with lots. |
| `transfers` | Transfer-ID Series named `sent`, in sending currency. |
| `cash_balances` | `(date, account)` or `(node, account)` Series named `cash`, in native account currency. |
| `investments` | When configured, investment-ID Series named `quantity`, in actual purchased units. |
| `scenario_costs` | For adaptive plans, case-ID Series named `discounted_funding_cost`, in reporting currency. Supports direct composition with `risk.expected_shortfall_epigraph`. |
| `facility_utilization` | When configured, `(date/node, facility)` Series named `utilization`, including reserved usage in each facility's currency. |
| `exposures` | When configured, `(date/node, exposure)` Series named `exposure`, including outside-book amounts in the declared unit. |

Exports do not mutate the source financial specification. For evaluation, each configured decision collection requires a complete finite vector, Series, or mapping in insertion order, without scalar broadcasting. `None` is valid only for an unconfigured collection, where an empty decision is also allowed. Draws contain only new loans; opening-debt principal is fixed. `tolerance` is a finite nonnegative absolute scalar, default `1e-7`.

`evaluate` returns `objective`, `feasible`, `constraints`, `decision`, `metrics`, `tables`, and `costs` without authentication or solving. It reconstructs cash, debt, facility usage, exposures, expenses, and configured risk measures from original contracts. Original arithmetic determines monetary residuals before binary64 reporting. A rounded displayed total may conceal a retained small violation; decisions are checked rather than repaired.

## Result fields

`result.draws`, `transfers`, `cash_balances`, and configured `investments` expose the same numeric Series structures as above. Scenario costs, facility usage, and exposure reports are in tables rather than additional decision properties. Objective units are reporting currency.

| Location | Fields |
| --- | --- |
| `metrics`, dated plan | `discounted_funding_cost`, `interest_reporting`, `funding_fees_reporting`, `transfer_fees_reporting`. The last three are undiscounted reporting-FX totals. |
| `metrics`, adaptive plan | `discounted_funding_cost` for the selected measure, `worst_case_funding_cost`, optional `expected_funding_cost`; ES objective adds `funding_cost_expected_shortfall`, `expected_shortfall_confidence`; hard ES adds `hard_funding_cost_expected_shortfall`, `hard_expected_shortfall_confidence`. |
| `costs` | `discounted_funding_cost`, `currency`, `measure` (`expected`, `worst_case`, `expected_shortfall`). |
| `cash_ladder` table | Indexed by `(date/node, account)`: `currency`, `opening_cash`, `deposit_interest`, `contractual_inflows`, `contractual_outflows`, `draws`, `principal_repayments`, `interest`, `funding_fees`, `transfer_in`, `transfer_out`, `transfer_fees`, `outstanding_debt`, `net_funding_cash_flow`, `closing_cash`, `cash_buffer`, `cash_upper`, `debt_limit`; configured investments add `investment_purchases`, `investment_cash_flows`. Native-currency inflow/outflow columns show nonnegative magnitudes for valid decisions; `interest`, `deposit_interest`, `net_funding_cash_flow`, and `investment_cash_flows` can be signed. |
| `funding` table | Dated: funding-ID index, `kind`, `account`, `currency`, `draw_date`, `repayment_date`, `principal`, `interest`, `origination_fee`, `total_repayment`, `discounted_cost_reporting`. Adaptive: `(funding_id, node, event)` index instead of date columns; events `draw`/`repayment`. Kinds are `new_funding`/`existing_debt`. |
| `transfers` table | Transfer-ID index, `date` or `node`, `from_account`, `to_account`, `source_currency`, `destination_currency`, `sent`, `fee`, `received`, `exchange_rate`, `discounted_cost_reporting`. |
| `funding_facilities` table | Configured `(date/node, facility)` index: `modelled_utilization`, `reserved_utilization`, `total_utilization`, `maximum`, `remaining_capacity`, `currency`. |
| `funding_facility_components` table | `date` or `node`, `facility`, `funding_id`, `outstanding_principal`, `principal_currency`, `fx_rate`, `utilization`, `currency`. |
| `investments` table | Configured investment-ID index: `account`, `currency`, `purchase_date` or `purchase_node`, `quantity`, `price`, `purchase_outlay`, `lower`, `upper`, `lot_size`. |
| `investment_schedule` table | Configured `(investment_id, date/node, event)` index: `account`, `currency`, `quantity`, `unit_cash_flow`, `cash_flow`. Event is `purchase` or `cash_flow`. |
| `exposures` table | Configured `(date/node, exposure)` index: `investment_exposure`, `funding_exposure`, `cash_exposure`, `external_exposure`, `total_exposure`, `lower`, `upper`, `unit`. |
| `exposure_components` table | Configured `(date/node, exposure, kind, position)` index: `quantity`, `coefficient`, `contribution`, `unit`. Kind is `investments`, `funding`, or `cash`. |
| `funding_information`, `funding_nodes` tables | Adaptive tree information and node metadata, with the schemas in [scenarios](scenarios.md). |
| `funding_scenarios` table | Adaptive case-indexed `discounted_funding_cost`, `interest_reporting`, `funding_fees_reporting`, `transfer_fees_reporting`, optional `probability`. Currency is a DataFrame attribute. |

Numeric decisions, monetary metrics, and reported amounts are floats. `net_funding_cash_flow` equals `draws - funding_fees - principal_repayments - interest`; contractual flows, transfers, and investments enter closing cash separately. `opening_cash` is the supplied opening balance at the root/first date and the parent's closing balance thereafter. `cash_buffer` is the configured minimum closing balance. A dated opening-debt row has `draw_date=None`.

Investment schedules use negative purchase outlay for the `purchase` event and signed supplied receipts/calls for `cash_flow` events. Facility-component rows cover each live member, including zero drawn principal; their index is positional. Exposure-component rows contain retained nonzero coefficients on the applicable history. Monetary constraints use the account, reporting, or facility currency; investment quantities use `instrument_units`, lot residuals use `lots`, activation checks use `binary`, and exposure mandates use their declared unit.

Solver recovery checks lot/activation reconstruction and reconciles cash and configured risk auxiliaries against financial replay. [Results](results.md) defines acceptance and retained solver evidence. [Plotting](plotting.md) documents cash ladders, funding, transfers, investments, and exposure figures.

Invalid schemas, IDs, dates/stages, domains, incomplete decisions, or missing required probabilities raise `TypeError` or `ValueError`; unrepresentable calculations raise `ValueError`. Valid but contradictory liquidity, commitment, or exposure limits can produce an infeasible optimization result. Contract availability, legal borrowing/transfer permissions, curves, and financial coefficients are supplied inputs.
