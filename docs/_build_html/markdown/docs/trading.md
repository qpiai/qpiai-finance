# Multi-period investment planning

`TradingModel` chooses an investment policy on an explicit financial information tree. Decisions use signed asset quantities and a cash account, with costs, carry, liabilities, term funding, and risk limits in financial units. Import it from `qpiai_finance.trading`.

Each observed node has one shared decision for every scenario passing through it. This enforces the supplied information structure: a future scenario cannot change a trade before its information is available. Prices, probabilities, trade capacities, and financing terms are supplied inputs. The model neither estimates a trading signal nor submits orders. For scheduling a fixed set of target orders across venues, use [execution scheduling](execution.md).

## Constructor

```python
TradingModel(
    prices, *, tree, holdings, cash, currency, buy_limits, sell_limits,
    cash_settlement, asset_ids=None, credit_limits=0.0, borrow_limits=0.0,
)
```

| Argument | Type, default, and meaning |
| --- | --- |
| `prices` | Required finite nonnegative node-by-asset valuation-price grid, in currency per asset unit. Zero prices are allowed. |
| `tree` | Required exact `ScenarioTree` instance, copied on input. Defines observed information, stage clock, and optional case probabilities. |
| `holdings` | Required finite signed scalar or complete asset vector, Series, or mapping of quantities before root flows/trades. |
| `cash` | Required finite signed scalar of cash before root events. Post-event revolving-credit limits are checked separately; no opening feasibility check is inferred. |
| `currency` | Required uppercase three-letter code for the account, prices, costs, debt, and wealth. |
| `buy_limits`, `sell_limits` | Required finite nonnegative node-by-asset grids of maximum bought/sold quantities. Set terminal-node capacities to zero for valuation without terminal trading. |
| `cash_settlement` | Required `"net"` or `"prefunded"`. Net combines node flows, purchases, sales, and charges. Prefunded additionally requires purchases and charges to be financed before sale proceeds. |
| `asset_ids` | Optional unique nonblank string/integer IDs, inferred from price DataFrame columns or Series/mapping keys, otherwise two-dimensional price-array columns use positional integers. Supply IDs explicitly when a scalar or otherwise unlabelled constant vector cannot identify assets. |
| `credit_limits` | Finite nonnegative scalar or complete node vector, Series, or mapping of approved revolving negative-cash capacity; default zero. |
| `borrow_limits` | Finite nonnegative node-by-asset grid of approved post-trade short quantities; default zero. |

A node-by-asset grid accepts an aligned DataFrame, ordered two-dimensional array/sparse matrix, complete per-asset vector/Series/mapping broadcast over nodes, or scalar broadcast over the full grid. Node-by-exposure grids follow the same convention with exposure columns. Node vectors accept a scalar or complete ordered vector, Series, or mapping. All numeric values must be finite unless an absent bound is represented by its documented `None` argument. Labelled axes must match exactly; missing/extra/duplicate labels are rejected. [Data conventions](data.md) defines the common input rules.

Properties `asset_ids` and `node_ids` return detached pandas indices; `tree` returns a detached `ScenarioTree`; `currency` is a string. All setters below mutate the financial specification and return `self`.

## Trading costs and quantity steps

```python
model.set_trading_costs(
    *, bid_prices=None, ask_prices=None, buy_per_unit=0.0,
    sell_per_unit=0.0, fixed=0.0, minimum_trade=0.0,
)
model.trade_in_lots(lot_sizes)
model.set_market_impact(*, quadratic=0.0, power_3_2=0.0, curves=None)
```

| Parameter | Type, default, and meaning |
| --- | --- |
| `bid_prices`, `ask_prices` | Optional nonnegative node-by-asset grids of execution quotes. Default `None` resets to valuation prices. Require `0 <= bid <= valuation price <= ask`. |
| `buy_per_unit`, `sell_per_unit` | Nonnegative node-by-asset grids of additional currency fees per bought/sold unit; default zero. Bid/ask already charges spread. |
| `fixed` | Nonnegative node-by-asset grid of currency charges per active trade; default zero. Positive charges at an available trade require a positive minimum quantity or lot when the model is used. |
| `minimum_trade` | Nonnegative node-by-asset grid of minimum absolute quantity when active; default zero. Zero trade remains allowed. |
| `lot_sizes` | Required nonnegative node-by-asset grid of quantity steps. Positive entries require whole lots; zero means divisible quantity. Default model steps are zero. |
| `quadratic` | Nonnegative node-by-asset grid of temporary cost coefficients in currency/unit²; default zero. |
| `power_3_2` | Nonnegative node-by-asset grid in currency/unit^1.5; default zero. |
| `curves` | Optional DataFrame containing exactly `node`, `asset`, `quantity`, `cost`, in point order within each supplied node/asset curve. Default `None` removes quoted curves; an empty table with those columns is also allowed. |

Each cost setter replaces all its components, resetting omitted arguments to their defaults. For signed trade `q`, temporary impact is `quadratic*abs(q)**2 + power_3_2*abs(q)**1.5` plus any quoted curve cost. All costs debit node cash. No permanent impact, cross-impact, or market calibration is inferred.

Curve points must be finite, start at `(0,0)`, have strictly increasing quantities and nonnegative nondecreasing slopes. The linear interpolant is the specified cost function. Configure capacities, participation, and lots before curves. Coverage must reach the largest permitted whole-lot trade and is rechecked on use. Trading beyond a quoted domain raises `ValueError` during replay. Exact piecewise graphs can introduce integer segment choices even when quantities are divisible. Bid/ask, fees, or other trading frictions may also require direction decisions to exclude simultaneous buying and selling.

## Cash flows and carry

```python
model.set_cash_flows(flows)
model.set_carry(
    *, deposit_factors=1.0, borrowing_factors=1.0, dividends=0.0,
    share_factors=1.0, short_fees=0.0,
)
```

`flows` is a finite signed node vector of incremental external account cash: deposits positive, liabilities/withdrawals negative. Default zero. Do not duplicate financing represented by loan contracts. Wealth includes these external flows; it is not a flow-adjusted return measure. Encode an earlier payment deadline at an earlier node.

Carry setters use **non-root nodes only**: each row describes the incoming parent-to-node interval. A root-only tree rejects `set_carry`. Defaults are reset on every call.

| Parameter | Type, default, and meaning |
| --- | --- |
| `deposit_factors` | Strictly positive finite non-root node vector of gross factors on positive parent cash; default one. These are interval factors, not annual rates. |
| `borrowing_factors` | Strictly positive finite non-root node vector of gross factors on negative parent cash; default one. |
| `dividends` | Finite signed non-root-node-by-asset grid of currency payments per parent holding unit, before share adjustment; default zero. Shorts pay positive dividends. |
| `share_factors` | Strictly positive finite non-root-node-by-asset grid multiplying parent quantities before node trades; default one. |
| `short_fees` | Nonnegative finite non-root-node-by-asset grid of currency fees per absolute short parent holding unit; default zero. |

No total-return, split, dividend, or annualization adjustment is inferred from the price grid. Before node trades, cash includes parent cash with the appropriate carry factor, parent-unit dividends, less short fees, plus external and net funding flows. Holdings start from share-adjusted parent quantities. Root cash and holdings come from the constructor.

## Revolving credit and term borrowing

```python
model.set_credit_limits(maximum)
model.set_borrow_limits(maximum)
model.add_funding(
    funding_id, *, draw_node, repayment_stage, maximum,
    interest=0.0, fee=0.0, fixed_fee=0.0, minimum=0.0, lot_size=None,
)
model.add_existing_debt(
    debt_id, *, principal, repayment_stage, interest=0.0,
)
model.limit_debt(*, maximum)
model.limit_facility(
    facility_id, funding_ids, *, maximum, currency,
    fx_rates=None, reserved=0.0,
)
```

`set_credit_limits` replaces a nonnegative node vector of revolving negative-cash capacity; `set_borrow_limits` replaces a nonnegative node-by-asset grid of short approvals. Term borrowing is a separate explicit principal liability and does not expand either of these controls automatically.

Funding/debt IDs are nonblank strings/integers and unique across those two collections. `draw_node` is a supplied observed node. `repayment_stage` is a supplied later stage for new funding; stage timestamps use the tree's date/aware clock. One draw decision applies whenever that node is reached and repays at every descendant maturity node, once per realized path. Existing-debt maturity may be the root and adds no historical draw to cash.

| Funding term | Type, default, and meaning |
| --- | --- |
| `maximum` | Required finite nonnegative new-principal cap in account currency. |
| `principal` | Required finite strictly positive opening-debt amount. |
| `interest` | Finite remaining total-term fraction, at least `-1`, default zero. Paid at maturity; no intermediate accrual or fair value is inferred. |
| `fee` | Finite nonnegative new-principal fraction paid at draw, default zero. No upper cap is imposed. |
| `fixed_fee` | Finite nonnegative currency charge per positive new draw, default zero. Requires positive `minimum` or a lot. |
| `minimum` | Finite amount in `[0, maximum]`, default zero. New borrowing is zero or at least this quantity. |
| `lot_size` | Optional finite strictly positive new-principal step, default `None` for continuous principal. |

New draw proceeds are `(1-fee)*principal - active_fixed_fee`; repayment is `(1+interest)*principal`. Funding events net within the node before trade prefunding. No intraday sequence, rollover, or collateral rights are inferred.

`limit_debt(maximum=...)` takes a finite nonnegative node vector capping outstanding term principal after draws and repayments, separately from negative cash. Initially there is no debt cap.

`limit_facility` uses the shared-commitment contract documented in [funding facilities](funding.md#cash-debt-and-shared-facilities). `funding_ids` is a nonempty distinct sequence of already configured contracts; `maximum` and default-zero `reserved` are nonnegative node vectors in facility currency. Capacity counts live principal on the realized path after repayments/draws; overlapping facilities are allowed. Reservation moves no cash and may make the model infeasible. Reusing the ID replaces that facility.

All principals here use the single account currency. Optional facility `fx_rates` is a positive scalar, single-currency vector/Series/mapping, or node-by-single-currency DataFrame/array in facility units per account-currency unit. Cross-currency valuation requires explicit quotes; same-currency rates equal one. These quotes do not trade FX or change the account currency.

## Financial limits

```python
model.limit_cash(*, minimum=None, maximum=None)
model.limit_positions(*, lower=None, upper=None)
model.limit_turnover(maximum)
model.limit_gross_notional(maximum)
model.limit_exposures(
    coefficients, *, lower, upper, risk_units, exposure_ids=None,
)
model.limit_participation(volumes, *, maximum_rate)
model.limit_terminal_wealth(minimum)
```

| Control | Input types, defaults, and meaning |
| --- | --- |
| Cash `minimum`, `maximum` | Optional finite signed node vectors bounding post-trade cash. `None` removes that side; both `None` removes these bounds. Revolving-credit floors still apply. Finite cash ceilings affect nonlinear-impact formulation as described below. |
| Position `lower`, `upper` | Optional finite signed node-by-asset grids bounding post-trade quantities. `None` removes that side; both `None` removes these bounds. Short approvals still apply. |
| Turnover `maximum` | Required nonnegative node vector of currency caps on absolute trades at that node's valuation prices. No factor of one-half. |
| Gross `maximum` | Required nonnegative node vector capping `sum(prices * abs(post_trade_holdings))` in currency. |
| Exposure `coefficients` | Required finite signed exposure-by-asset matrix of supplied per-unit sensitivities/amounts, with aligned labels when labelled. |
| Exposure `lower`, `upper` | Required finite signed node-by-exposure grids of ordered bounds. Equal bounds impose matching. |
| `risk_units` | Required nonblank unit string broadcast to all exposure rows, or complete sequence, Series, or mapping of nonblank physical-unit labels. |
| `exposure_ids` | Optional unique nonblank string/integer row IDs, inferred from DataFrame rows or positional integers. IDs must be unique across calls; each call adds a block. |
| `volumes`, `maximum_rate` | Required nonnegative quantity grid and rate grid in `[0,1]`. Their product caps absolute node/asset trading along with buy/sell capacities. |
| Terminal `minimum` | Required finite signed scalar or complete case vector, Series, or mapping of minimum terminal currency wealth. Applies to every case, including zero-probability cases. |

Bounds require lower no greater than upper. Except added exposure blocks and the separately identified facilities, setters replace their prior settings.

Closing cash is available cash minus purchases plus sales minus fees and impact. Net settlement checks closing credit. Prefunded settlement also checks available cash minus purchases and charges against the revolving-credit floor before adding sales. Additional `limit_cash` bounds apply to closing cash. Intermediate pre-node cash is not a separate settlement checkpoint.

At any node, reported wealth equals cash plus marked holdings minus outstanding term principal. Terminal wealth includes all configured loan repayments because maturities lie within the horizon. Intermediate principal accounting does not infer debt fair value or accrued remaining interest. Asset eligibility, valuation, sensitivities, volumes, and legal financing permissions remain supplied inputs.

## Wealth and tail-risk objectives

```python
model.maximize_expected_wealth()
model.maximize_worst_case_wealth()
model.minimize_expected_shortfall(*, target, confidence=0.95)
model.limit_expected_shortfall(maximum, *, target, confidence=0.95)
```

Expected terminal wealth is the default objective and requires explicit tree case probabilities. Worst-case selection maximizes the minimum wealth over every supplied case and permits probability-free stress planning. No equal weights are inferred.

Both ES methods require probabilities when the model is exported, validated, evaluated, or solved. Required `target` is a finite signed scalar or complete case vector, Series, or mapping in currency. Case loss is `target - terminal_wealth`, without clipping gains. `confidence` is strictly in `(0,1)`, default `0.95`. ES is the finite weighted upper-tail mean with fractional boundary mass. Minimization changes the objective; a hard cap remains under every objective. Required hard `maximum` is a finite signed currency scalar. Its target and confidence are independent of those used by the objective. Repeated calls replace the corresponding setting.

## Exports and execution

```python
model.to_matrix()
model.to_model(*, return_variables=False)
model.to_cvxpy()
model.to_scip()
```

`to_matrix()` returns detached complete sparse Opt LP/MILP data for models without active quadratic or power impact. Quoted piecewise costs retain their exact interpolant. The dictionary contains `name="multi_period_investment"`, `format="matrix"`, `problem_type`, `sense` (`max` wealth or `min` ES), `variable_names`, `objective`, `objective_offset=0.0`, CSR `constraint_matrix`, `row_lower`, `row_upper`, `constraint_names`, `lower_bounds`, `upper_bounds`, and `integrality`. Vectors are NumPy arrays; infinite endpoints indicate absent bounds.

`to_model()` returns the equivalent detached algebraic Opt formulation; boolean `return_variables=True` returns `(model, expressions)`. These linear exports permit explicit further compilation as described in [custom models](custom-models.md).

`to_cvxpy()` returns `(cvxpy.Problem, expressions)` for complete linear/piecewise models and nonlinear-impact models without finite cash ceilings. `to_scip()` returns `(pyscipopt.Model, expressions)`, including exact nonlinear cost graphs when cash ceilings are present. Every financial expression mapping has node-by-asset DataFrames `trades`, `holdings` and node Series `cash_balances` named `cash`; configured new loans add funding-ID Series `draws` named `principal`; facilities add `(node, facility)` Series `facility_utilization` named `utilization`. Values use actual asset units, native principal, and facility-currency utilization, including reserved usage; they are not lot counts. Export changes do not change the source specification.

Without nonlinear impact the class is LP or MILP. Integers may arise from lots, fixed/minimum trades, trading direction, exact cash/short carry pieces, funding activation, or piecewise curve segments. With quadratic/power impact and no cash ceilings the formulation is SOCP or MISOCP. A cost epigraph permits reconstruction of true costs and no less cash; all financial limits and wealth/tail tests are rechecked. With finite cash ceilings an epigraph could artificially spend cash, so an exact graph is required: quadratic costs give QCQP/MIQCP and active power costs give NLP/MINLP. These routes require SCIP; Opt linear exports and `to_cvxpy` reject them.

[Solving](solving.md) defines authentication, routing, and options. Defaults select Opt for linear models, Clarabel for continuous conic models, and SCIP where integer conic or exact nonlinear execution is required. Every Finance solve requires Opt authentication. Export and evaluation are offline.

## Evaluate a policy and inspect results

```python
model.evaluate(trades, *, draws=None, tolerance=1e-7)
```

`trades` is a complete finite signed node-by-asset matrix: aligned DataFrame, supported column mapping, ordered dense array, or sparse matrix. Unlike setter grids, evaluation does not broadcast scalar or per-asset decisions. `draws` requires a complete finite new-funding vector, Series, or mapping in insertion order when loans are configured, including explicit zero draws. Opening debt has no decision. Default `None` is valid without new funding. `tolerance` is a finite nonnegative absolute scalar, default `1e-7`.

Evaluation replays the complete policy and original financial limits without authentication or solving. It returns `objective`, `feasible`, `constraints`, `decision`, `metrics`, `tables`, `costs`, and `transformations`. Original sums/products determine residuals before binary64 reporting, including carry, liabilities, financing, nonlinear costs, and terminal risk. It checks fractional lots and violated bounds rather than repairing decisions.

`result.trades` and `result.holdings` are node-by-asset DataFrames; `cash_balances` is a node Series named `cash`; configured `draws` is a new-funding Series named `principal`. Objective and wealth units are currency.

| Location | Fields |
| --- | --- |
| `metrics` | `expected_terminal_wealth` (`None` without probabilities), `worst_terminal_wealth`, `terminal_expected_shortfall` (`None` unless ES objective), `hard_expected_shortfall` (`None` without a hard cap), `currency`. |
| `costs` | Node-order lists `funding_interest_by_node`, `funding_fees_by_node`, `impact_by_node`, `trading_fees_by_node`, `spread_by_node`, `short_fees_by_node`; `currency`. These lists follow nodes, not whole-path totals. |
| `investment_accounts` table | Tree-node metadata plus `available_cash`, `interest` (signed revolving cash carry), `dividends`, `short_fees`, `external_flow`, `funding_draws`, `principal_repayments`, `funding_interest`, `funding_fees`, `outstanding_debt`, `net_funding_cash_flow`, `purchase_outlay`, `sale_proceeds`, `trading_fees`, `market_impact`, `spread_cost`, `closing_cash`, `wealth`, `gross_assets`. Currency is a DataFrame attribute. |
| `investment_funding` table | Indexed by `(funding_id, node, event)`: `stage`, `time`, `principal`, `interest`, `fees`, `cash_flow`. Events are `draw`, `repayment`, or `existing_debt_repayment`. Currency is a DataFrame attribute. |
| `investment_scenarios` table | Case-indexed `terminal_wealth`, optional `probability`; ES objective adds `target`, `loss`; hard ES adds `hard_tail_target`, `hard_tail_loss`. Currency is an attribute. |
| `investment_information` table | Case/stage information-node mapping from the tree. |
| `investment_stage_times` table | Stage-indexed `time` column from the tree's clock. |
| `funding_facilities`, `funding_facility_components` | When configured, the utilization and principal-contribution schemas in [funding results](funding.md#result-fields), with node rows. |

Numeric decisions, metrics, account amounts, and cost-list entries are floats; the documented inactive metrics remain `None`. `investment_accounts` retains node order. `gross_assets` is closing cash plus the signed marked value of holdings, before subtracting term principal; the gross-notional limit separately uses absolute holding values. `available_cash` is after carry, external flows, and net loan events, before node trades. `net_funding_cash_flow` equals funding draws minus principal repayments, funding interest, and funding fees. Purchases and sales include their execution quotes; `spread_cost` reports the quote-versus-valuation difference already paid in those cash flows.

For nonlinear impact without cash ceilings, evaluation includes one transformation with `type="market_impact_epigraph"` and boolean fields `cash_upper_bounds_absent=True`, `source_cash_recomputed=True`, and `exact_financial_projection=True`. Other formulations return an empty transformation list from direct evaluation. Asset-quantity constraints use `asset_units`, trade/funding lot residuals use `lots`, monetary limits use currency, and exposure bounds use their declared physical units.

Solving recovers signed financial trades and draws and replays the policy. [Results](results.md) defines source feasibility, solver evidence, and acceptance; [plotting](plotting.md) covers policy, wealth, cash, and scenario figures.

Invalid dimensions, labels, factors, bounds, missing probabilities, curve domains, or unsupported exports raise `TypeError` or `ValueError`; unrepresentable calculations raise `ValueError`. Valid but incompatible mandates may produce an infeasible solve. A scenario policy describes decisions conditional on supplied observations, not a forecast guarantee.
