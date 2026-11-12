# Execution scheduling

`ExecutionModel` distributes signed target orders across supplied time and venue opportunities. It combines predicted execution shortfall, optional underfill penalties, and the price risk of outstanding orders. Import it from `qpiai_finance.trading`.

Orders remain in physical asset units. Positive quantities buy; negative quantities sell. Each asset trades only in its target direction, without overfill or round trips. The model proposes a schedule from supplied prices, capacities, and costs; it does not submit orders or guarantee fills. For investment decisions that determine the target book itself, use [multi-period investment planning](trading.md).

## Constructor

```python
ExecutionModel(
    orders, opportunities, *, arrival_prices, holdings, cash, currency,
    as_of, slots, cash_settlement, asset_ids=None, slot_ids=None,
    credit_limit=0.0, borrow_limits=0.0,
)
```

All numeric inputs are finite. Vectors follow model order or use complete Series/mappings aligned by IDs; incomplete, duplicate, or extra labels are rejected.

| Argument | Type, default, and meaning |
| --- | --- |
| `orders` | Required finite signed vector, Series, or mapping of target changes by asset. Zero orders are permitted. No scalar broadcasting. |
| `opportunities` | Required DataFrame of permitted execution alternatives, with columns below. May be empty with required columns retained. |
| `arrival_prices` | Required strictly positive asset vector, Series, or mapping of benchmark currency per asset unit; no scalar broadcasting. |
| `holdings` | Required signed scalar or complete asset vector of opening quantities. |
| `cash` | Required signed currency scalar, at least `-credit_limit`. |
| `currency` | Required uppercase three-letter code for all prices, fees, cash, and objective costs. No FX conversion is inferred. |
| `as_of` | Required timezone-aware timestamp. |
| `slots` | Required nonempty sequence of strictly increasing timezone-aware timestamps starting at `as_of`. |
| `cash_settlement` | Required `"net"` or `"prefunded"`. Net permits same-slot sale proceeds to fund purchases; prefunded requires purchases and all execution charges to be funded before sale proceeds. |
| `asset_ids` | Optional unique nonblank string/integer identifiers. Default order labels, otherwise positional integers. |
| `slot_ids` | Optional unique string/integer identifiers, one per timestamp. Default positional integers. |
| `credit_limit` | Nonnegative opening cash overdraft capacity; default zero. Initially applied to every slot. |
| `borrow_limits` | Nonnegative scalar or complete asset vector of approved opening short quantities; default zero. Opening holdings must respect these limits. Initially applied to every slot. |

### Execution opportunities

Each row has a unique string/integer opportunity ID. Unknown or duplicate columns are rejected. Each `(asset, slot, venue)` triple must be unique; venues are nonblank string/integer IDs. An omitted asset/time/venue route is unavailable.

| Column | Type, default, and meaning |
| --- | --- |
| `asset` | Required supplied asset ID. |
| `slot` | Required supplied slot ID. |
| `venue` | Required venue identifier. |
| `price` | Required positive reference price in currency per asset unit. |
| `capacity` | Required nonnegative absolute executable quantity in that asset's units. |
| `bid_price`, `ask_price` | Optional positive execution quotes; default to `price`. Require `0 < bid_price <= price <= ask_price`. |

## Properties and input forms

Detached properties `asset_ids`, `opportunity_ids`, `slot_ids`, and `venue_ids` return pandas indices. Venues follow first occurrence in the opportunity table. `slot_times` is a timestamp Series named `time`, indexed by slot ID; `currency` is a string.

Setters below mutate the specification and return `self`. A slot-by-asset grid accepts a finite DataFrame or two-dimensional array/sparse matrix, a complete asset vector/Series/mapping broadcast over slots, or a scalar broadcast over the grid. A slot-by-venue or slot-by-exposure grid follows the same convention using its column IDs. Two-dimensional inputs must have the full grid shape; labelled axes must match exactly. See [data conventions](data.md).

## Fees, lots, and temporary impact

```python
model.set_execution_costs(*, per_unit=0.0, fixed=0.0, minimum_trade=0.0)
model.trade_in_lots(lot_sizes)
model.set_market_impact(*, quadratic=0.0, power_3_2=0.0, curves=None)
```

| Parameter | Type, default, and meaning |
| --- | --- |
| `per_unit` | Nonnegative scalar or complete opportunity vector of currency fees per absolute unit; default zero. Additional to spread and impact. |
| `fixed` | Nonnegative scalar or complete opportunity vector of currency fees per active opportunity; default zero. Positive fixed fees require positive `minimum_trade` or configured lots. This condition is checked on export, evaluation, validation, and solve. |
| `minimum_trade` | Nonnegative scalar or complete opportunity vector of minimum quantity when active; default zero. Zero execution remains allowed. Positive minima introduce activation decisions. |
| `lot_sizes` | Required strictly positive scalar or complete asset vector of quantity steps. Every opportunity execution must be a whole asset lot; activation minimum is at least one lot. |
| `quadratic` | Nonnegative scalar or complete opportunity vector in currency/unit²; default zero. Cost is coefficient times absolute quantity squared. |
| `power_3_2` | Nonnegative scalar or complete opportunity vector in currency/unit^1.5; default zero. Cost is coefficient times absolute quantity^1.5. |
| `curves` | Optional mapping from supplied opportunity IDs to DataFrames containing exactly `quantity`, `cost`. Default `None` removes quoted curves. Quantities are physical units; costs are currency. |

Every call to `set_execution_costs` or `set_market_impact` replaces all of that method's components, including omitted components with their defaults. Quadratic, power, and quoted costs add together. No permanent impact, cross-impact, or calibration is inferred.

Each quoted curve starts at `(0,0)`, has strictly increasing finite quantities, finite costs, and nonnegative nondecreasing segment slopes. Its linear interpolant is the specified cost function. Configure quantity restrictions and lots before curves: each curve must cover the largest permitted whole-lot execution, accounting for opportunity capacity, target size, order windows, and participation. Coverage is rechecked if controls later change. An execution outside a curve's domain is a violation. Temporary impact on a sale cannot exceed its quoted sale proceeds; the effective sale value must remain nonnegative before fees.

For an out-of-domain proposal, replay extends the end segment to report its cost and marks the `impact_domain` constraint violated.

For empty opportunity tables, opportunity controls accept a finite scalar or empty vector/Series/mapping and retain an empty setting.

## Completion, timing, and capacity

```python
model.allow_underfill(penalty)
model.require_completion(asset_ids=None)
model.set_order_windows(*, release=None, deadline=None)
model.limit_participation(volumes, *, maximum_rate)
model.limit_venue_notional(maximum)
```

All orders initially require full completion at the last slot. `allow_underfill` permits underfill for every asset and sets a nonnegative scalar or complete asset vector of currency penalties per unfilled unit. It resets all hard-completion flags. `require_completion` restores hard completion for a nonempty unique sequence of supplied asset IDs, or all assets with default `None`, while retaining other flags and penalties. Unfilled penalties apply only to orders whose completion is optional.

`release` and `deadline` accept timezone-aware scalar timestamp/string/datetime values or complete asset-indexed timestamp sequences, Series, or mappings. Defaults reset release to `as_of` and deadline to the last slot. Windows are inclusive and need not end at supplied slots; require release no later than deadline.

`volumes` is a required nonnegative slot-by-asset grid in physical units. Required `maximum_rate` is a grid with entries in `[0,1]`. Their product caps combined absolute fills across all venues for each asset/slot. It is not a separate allowance per venue.

Venue `maximum` is a required nonnegative slot-by-venue grid of currency limits. It caps gross absolute execution quantity times each opportunity's reference `price`, excluding charges. This method requires at least one supplied venue.

## Cash and position limits

```python
model.set_cash_flows(flows)
model.set_credit_limits(maximum)
model.limit_cash(minimum)
model.set_borrow_limits(maximum)
model.limit_positions(*, lower=None, upper=None)
model.limit_gross_notional(maximum)
model.limit_turnover(maximum)
```

| Input | Type, default, and meaning |
| --- | --- |
| `flows` | Required signed scalar or complete slot vector of incremental external currency flows arriving before trading. Default model flows are zero. |
| Credit `maximum` | Required nonnegative scalar or complete slot vector of approved cash overdraft capacities, effective before trading. Replaces the slot schedule; opening capacity remains the constructor input. |
| Cash `minimum` | Required finite signed scalar or complete slot vector of currency buffers. Applies before and after trading, and before sale proceeds under prefunding. Effective floor is `max(minimum, -credit_limit)`. Initially no additional buffer. |
| Borrow `maximum` | Required nonnegative slot-by-asset grid of approved short quantities. Replaces post-trade short limits; no borrowing fee is inferred. Opening approval remains separately checked. |
| Position `lower`, `upper` | Optional finite signed slot-by-asset grids of post-trade quantities. `None` resets that side to unbounded; both `None` removes this constraint. Require lower no greater than upper. |
| Gross `maximum` | Required nonnegative scalar or complete slot vector of currency limits on `sum(arrival_prices * abs(post_trade_holdings))`. |
| Turnover `maximum` | Required nonnegative currency scalar bounding total absolute execution notional at arrival prices over the entire horizon. No factor of one-half. |

Cash debits include executed bid/ask values, fees, and supplied impact. Underfill penalties and price-risk charges are objective terms rather than execution cash debits. Incremental external flows are applied once per slot. Both cash-settlement modes require the pre-trade balance to respect its floor; incoming trades cannot cure a pre-trade breach.

## Exposures and outstanding-order risk

```python
model.limit_exposures(
    coefficients, *, lower, upper, risk_units, exposure_ids=None,
)
model.set_price_risk(covariance_rate, *, risk_aversion)
```

`coefficients` is a required finite signed exposure-by-asset matrix of supplied exposure per asset unit. `exposure_ids` optionally supplies unique string/integer row IDs, otherwise inferred from DataFrame rows or positional integers. IDs must remain unique across calls; each call adds a block. Required finite signed `lower` and `upper` are slot-by-exposure grids with ordered bounds. `risk_units` is a nonblank string broadcast to all rows, or a complete sequence, Series, or mapping of one nonblank unit label per exposure. Bounds constrain linear exposures of post-trade holdings at every slot. They do not perform repricing or infer regulatory policy.

`covariance_rate` is a required finite symmetric positive-semidefinite asset matrix or equivalent `FactorRisk`, with matching asset labels. Its units are currency² divided by `(asset_unit_i * asset_unit_j * second)`. Required nonnegative scalar `risk_aversion` has inverse-currency units. This setter replaces the price-risk model. For signed remaining orders `r_k` after slot `k`, risk cost is

\[
\lambda\sum_k \Delta t_k\,r_k^\mathsf{T}\Sigma_{\rm second}r_k.
\]

The final slot has no subsequent interval and contributes zero risk. This assumes independent Brownian price increments over each interval. It prices the target gap rather than strategic book risk. The method neither estimates covariance nor converts return/annualized covariance into price covariance per second.

## Objective, exports, and execution

For signed execution `q_j`, predicted executed shortfall is `(side_price_j - arrival_price_asset)*q_j + fees_j + impact_j`. The minimized objective adds underfill penalties and outstanding-order risk cost. Favourable supplied prices can produce negative shortfall.

```python
model.to_matrix()
model.to_model(*, return_variables=False)
model.to_cvxpy()
model.evaluate(executions, *, tolerance=1e-7)
```

`to_matrix()` returns detached sparse Opt LP/MILP data only for a linear model, including quoted piecewise costs. The dictionary contains `name="trade_execution"`, `format="matrix"`, `sense="min"`, `problem_type`, `variable_names`, `objective`, `objective_offset=0.0`, CSR `constraint_matrix`, `row_lower`, `row_upper`, `constraint_names`, `lower_bounds`, `upper_bounds`, and `integrality`. Vectors are NumPy arrays; infinite bound endpoints mean no bound. Nonlinear impact or active price risk rejects this export.

`to_model()` exports detached Opt LP/MILP or continuous QP; boolean `return_variables=True` returns `(model, expressions)`. Nonzero quadratic or power impact requires conic execution and rejects this export. Active quadratic price risk with integer decisions also requires an external solver. `to_cvxpy()` returns `(cvxpy.Problem, expressions)` for all supported classes. Financial expressions are opportunity-indexed signed `executions` Series, slot-by-asset `remaining_orders` and `holdings` DataFrames, and slot-indexed `cash_balances` Series. They use physical quantities and currency, including with integer lots.

With nonlinear impact the class is SOCP or MISOCP. Otherwise active price risk gives QP or MIQP; remaining models are LP or MILP. Lots, fixed fees, or minimum executions introduce integer decisions. Default routing selects Clarabel for continuous conic models, SCIP for integer conic/quadratic models, and Opt for supported LP/MILP/QP. Every Finance solve requires Opt authentication. [Solving](solving.md) defines options and execution modes; [custom models](custom-models.md) explains further compilation of eligible Opt exports.

`evaluate` requires a complete finite signed opportunity vector, Series, or mapping, without scalar broadcasting. With no opportunities, supply an empty vector/Series/mapping. It returns `objective`, `feasible`, `constraints`, `decision`, `metrics`, `tables`, and `costs`, without solving or authenticating. `tolerance` is a finite nonnegative absolute scalar, default `1e-7`; boolean checks are exact. Evaluation retains wrong directions, overfill, fractional lots, capacity breaches, and other violations rather than repairing the input.

## Result fields

Decisions are `executions` (opportunity Series named `quantity`), `trades`, `holdings`, and signed `remaining_orders` (slot-by-asset DataFrames), `unfilled` (nonnegative final residual asset Series named `quantity`), and `cash_balances` (slot Series named `cash`). All are accessible through their `FinanceResult` properties. Objective units are currency.

| Location | Fields |
| --- | --- |
| `metrics` | `predicted_executed_shortfall`, `price_change_cost`, `spread_cost`, `execution_fees`, `temporary_impact`, `underfill_cost`, `price_risk_variance` (currency²), `price_risk_cost`, `final_cash`, `cash_after` (same final cash), `final_credit_used`, `peak_credit_used`, integer `incomplete_orders`, `turnover_notional`. |
| `costs` | `currency`, `price_change`, `spread`, `fees`, `impact`, `underfill`, `risk`. |
| `execution_schedule` table | Opportunity input columns, `time`, signed `quantity`, boolean `eligible`, `order_side` (`buy`, `sell`, `none`), `side_price`, `spread_cost`, `fees`, `temporary_impact`, `piecewise_impact`, `predicted_shortfall`. |
| `execution_orders` table | Asset-indexed `target_quantity`, `opening_holdings`, `executed_quantity`, `final_holdings`, `signed_residual`, `unfilled_quantity`, `required`, `underfill_cost`, `release`, `deadline`, `completion_status`. Status is `complete`, `partial`, `unfilled`, or `overfilled`, using evaluation tolerance. Check constraints as well as status. |
| `execution_cash` table | Slot-indexed `time`, `external_flow`, `opening_cash`, `cash_before`, `cash_before_sale_proceeds` (NaN under netting), `purchase_value`, `sale_value`, `charges`, `cash_after`, `credit_limit`, `cash_floor`, `credit_used`, `peak_credit_used`. The last field is peak use within that slot including opening cash. |
| `execution_holdings` table | Slot-by-asset post-trade quantities. |
| `execution_risk` table | Slot-indexed `seconds_to_next_slot`, `remaining_price_variance`, `risk_cost`. |
| `execution_numerical_diagnostics` table | Added during solver recovery, indexed by `variable`: `solver_value`, `reconstructed_value`, signed `difference`, `unit`, `relation`. Relations `equal`, `at_least`, or `at_most` describe the auxiliary relative to the reconstructed value. |

Recovery reconstructs physical executions from nonnegative or integer quantities and ticket decisions, records reconstruction residuals as constraints, and rechecks the financial schedule. It recomputes actual costs and cash from primary trades. Conservative cost epigraph slack can therefore differ from reconstructed costs; numerical diagnostics retain that difference. See [results](results.md) for acceptance and retained solver evidence, and [plotting](plotting.md) for execution, completion, cash, and risk figures.

Numeric decisions, costs, and non-count metrics are floats. `execution_schedule` retains opportunity IDs; the orders table retains asset IDs, and cash/risk tables retain slot IDs. `temporary_impact` includes the separately reported `piecewise_impact`. `execution_risk.remaining_price_variance` already includes the seconds to the next slot, in currency squared; its sum is `price_risk_variance`, and multiplication by risk aversion gives the risk cost. Variance can be reported with zero risk aversion even though it contributes no objective charge.

Recovery adds a transformation with `type="execution_reconstruction"`, `source_quantities_rechecked=True`, float `cash_origin`, and `primary_reconstruction`: a list of dictionaries with string `constraint`, float `residual`, and string `unit`. It also records `cost_epigraphs="conservative_cash_recomputed_from_actual_costs"` and `impact="supplied_temporary_costs"`. The cash origin is the reference subtracted from internal cash coordinates. Direct evaluation does not add this recovery record. Quantity constraints use `asset_units`, lot residuals use `lots`, ticket reconstruction uses `binary`, eligibility/zero-order/positive-lot checks use exact `boolean`, and financial constraints use currency or the declared exposure unit.

Invalid shapes, labels, windows, capacity/rate domains, missing curve coverage, or unsupported exports raise `TypeError` or `ValueError`; unrepresentable numerical values raise `ValueError`. Valid but incompatible completion, cash, capacity, or position requirements can yield an infeasible result.
