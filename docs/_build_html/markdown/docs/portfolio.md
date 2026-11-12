# Portfolio construction and rebalancing

`PortfolioModel` describes a single-period allocation or a rebalance of supplied holdings and cash. Choose the financial objective and investment restrictions first. Solve the supported formulation directly, or compile an eligible equal-weight selection for quantum-inspired or gate-based optimization. The financial model remains the reference for recovered weights, costs, and feasibility.

Import `PortfolioModel` and `FrontierResult` from `qpiai_finance.portfolio`. Common execution is described in [solving](solving.md); binary representations and algorithm controls are described in [quantum optimization](quantum.md).

## Construct the model

```python
PortfolioModel(
    expected_returns=None, covariance=None, *, horizon, asset_ids=None,
    net_weight=1.0, holdings=None, prices=None, cash=None, currency=None,
    bid_prices=None, ask_prices=None, cash_return=0.0,
)
```

| Parameter | Type and meaning |
| --- | --- |
| `expected_returns` | Optional finite arithmetic-return vector, Series, or mapping, one value per asset. Required for utility, return targets, and robust forecasts. |
| `covariance` | Optional aligned square covariance DataFrame, column mapping, dense/sparse matrix, or `FactorRisk`. Required for variance-based objectives or limits and risk construction. |
| `horizon` | Required nonblank string describing the common forecast and risk horizon. It does not rescale inputs. |
| `asset_ids` | Optional unique string/integer asset identifiers. Labeled expected returns define the default order. When expected returns are omitted, factor-risk or labeled covariance identifiers define it. Unlabeled expected returns use positional integers unless `asset_ids` is supplied, even when covariance is labeled. Explicit identifiers define array order. |
| `net_weight` | Finite real target for the sum of asset weights in allocation-only models; default `1.0`. A rebalancing account requires exactly `1.0` and uses its self-financing equation instead. |
| `holdings` | Starting signed share/quantity vector. Supplying any account input requires all of `holdings`, `prices`, `cash`, and `currency`. |
| `prices` | Finite valuation-price vector, one positive price per asset, in account currency per share/quantity unit. |
| `cash` | Finite starting cash amount in account currency. Initial cash plus marked holdings must have strictly positive finite value. |
| `currency` | Uppercase three-letter account currency code. No FX conversion is inferred. |
| `bid_prices`, `ask_prices` | Optional aligned vectors; each defaults to `prices`. Must satisfy `0 < bid_prices <= prices <= ask_prices`. |
| `cash_return` | Finite cash return fraction over the model horizon, at least `-1`; default zero. Requires an account when nonzero. |

At least one of expected returns and covariance must be supplied. All arrays and labeled inputs follow [data conventions](data.md). Default asset bounds are `0 <= w_i <= 1`; the default objective minimizes variance. A return-only model therefore needs an appropriate configured objective before validation or solving.

Read-only properties are `asset_ids` (detached pandas Index), `expected_returns` (detached Series named `expected_return`, or `None`), `horizon` (string), and `tax_lots` (detached acquisition-lot DataFrame, or `None`).

Objective and constraint configuration methods below modify the model and return `self`. Selecting another objective retains existing financial constraints unless a method explicitly replaces their settings. Setting an objective clears the previous benchmark; `minimize_tracking_error` supplies its own benchmark. Repeated calls to an ordinary limit setter replace that limit; exposure groups accumulate under unique identifiers.

## Weight and cash conventions

Without an account, asset weights use the declared investment basis and satisfy $\sum_iw_i=\texttt{net\_weight}$. With an account, define $V_0=C_0+\sum_ip_iq_i^0$. Then $w_i=p_iq_i^+/V_0$. These weights use initial value. The result separately reports `post_trade_weights`, whose denominator is the positive marked account value after trades, `portfolio_value = cash_after + sum(prices * holdings)`. Deferred recognized tax remains outside that denominator; `net_value_after_tax` additionally deducts unpaid recognized tax. `post_trade_weights` is absent when `portfolio_value <= 0`.

For buys $b_i\geq0$ and sells $s_i\geq0$, quantities satisfy $q_i^+=q_i^0+b_i-s_i$. Cash uses actual ask and bid prices, fees, and immediately settled tax:

$$
C^+=C_0-\sum_i\operatorname{ask}_i b_i+\sum_i\operatorname{bid}_i s_i-\operatorname{fees}-\operatorname{tax}_{\mathrm{paid}}.
$$


The self-financing equation includes the resulting cash, spread costs, fees, and immediately settled tax. Default final cash lies between zero and initial portfolio value. Recognized deferred tax affects economic return but is not paid from current cash.

Net forecast return is $\mu^\top w+r_cC^+/V_0-(\operatorname{spread}+\operatorname{fees}+\operatorname{recognized\ tax})/V_0$. The account metric `gross_expected_return` is the asset contribution $\mu^\top w$. The input `cash_return` is the rate $r_c$; the result metric of that name is its return contribution $r_cC^+/V_0$. `expected_return` is the net forecast above. Variance is calculated on the asset weights at the supplied horizon. Cash return is deterministic in this model.

## Objectives

### Variance, utility, and benchmark risk

```python
model.minimize_variance()
model.maximize_utility(*, risk_aversion)
model.minimize_tracking_error(*, benchmark)
```

`minimize_variance` minimizes $w^\top\Sigma w$. `maximize_utility` maximizes net forecast return minus `risk_aversion * variance / 2`; aversion must be a finite nonnegative real scalar. Zero aversion maximizes return alone and does not require covariance unless another setting needs it. If robust forecasts are active, utility uses their specified worst-case return.

`benchmark` is a complete finite weight vector, Series, or mapping aligned by asset. Tracking-error minimization minimizes active variance $(w-b)^\top\Sigma(w-b)$; the reported tracking error is its square root. The benchmark is not normalized. The result also reports covariance-implied beta; beta is NaN if benchmark variance is zero.

### Scenario risk

```python
model.minimize_expected_shortfall(scenarios, *, confidence=0.95)
model.minimize_mean_absolute_deviation(scenarios)
model.minimize_downside_risk(scenarios, *, target=0.0)
```

`scenarios` must be a `Scenarios` instance with exactly the model's assets, `unit="simple_return"`, matching `horizon`, and explicit probabilities. Finance takes a detached copy and aligns its asset columns. Use [scenario contracts](scenarios.md) for construction.

Expected shortfall minimizes the upper tail of losses equal to negative net scenario returns. `confidence` is strictly between zero and one; fractional boundary probability is included. Mean absolute deviation minimizes expected absolute deviation from the scenario-weighted mean; deterministic cash income and transaction costs cancel in this deviation. Downside risk minimizes the first lower partial moment $E[(\texttt{target}-r_s)_+]$, where `target` is a finite return fraction. It is not a pathwise drawdown measure.

### Higher-moment utility

```python
model.maximize_moment_utility(
    scenarios, *, variance_aversion, skewness_preference=0.0,
    kurtosis_aversion=0.0,
)
```

The scenario requirements above apply. All three coefficients are finite nonnegative real scalars. The objective is forecast mean minus `variance_aversion` times the second central scenario moment, plus `skewness_preference` times the third, minus `kurtosis_aversion` times the fourth. The mean comes from `expected_returns`; central moments come from the supplied scenario distribution.

These are raw central moments, without sample corrections or standardization by volatility. Choose coefficient units so each contribution has return-fraction units. The variance coefficient has no extra factor of one-half. This formulation requires equal-weight selection for binary optimization; use [portfolio compilation](quantum.md). Direct `solve(model, ...)` uses native HUBO. `to_model` and `to_cvxpy` reject this nonconvex polynomial objective.

### Risk budgets

```python
model.allocate_risk(budgets=None, *, polish=True, polish_maxiter=20)
```

`budgets` is a positive complete vector, Series, or mapping summing to one within absolute `1e-12`; omitted means equal budgets. `polish` is a Python boolean. `polish_maxiter` is a positive integer excluding booleans.

The construction minimizes $\frac12x^\top\Sigma x-\sum_ib_i\log x_i$ for positive risk positions, then scales them to `net_weight`. It requires covariance with positive asset variances, positive `net_weight`, and no rebalancing account. The default solver is Clarabel. Optional refinement uses a SciPy root calculation on the risk-budget equations and accepts a finite candidate only when it reduces the residual. Refinement settings and outcomes appear in `solver_info["refinement"]`.

Refinement runs when `polish=True` and the solver returns a candidate. Its record contains:

| Field | Type and meaning |
| --- | --- |
| `method` | String `"scipy-root-krylov"`; the equations are $x_i(\Sigma x)_i-b_i=0$. |
| `residual_before`, `residual_after` | Floats giving the maximum absolute equation residual before and after accepted refinement. |
| `accepted` | Boolean; true only for a finite candidate with a strictly smaller residual. |
| `function_evaluations` | Integer count, zero when refinement was unnecessary, or `None` when the root routine supplies no count. |
| `settings` | Dictionary with `maxiter=polish_maxiter`, `fatol=max(2**-52, min(tolerance/10, 1e-12))`, and `line_search="armijo"`. |
| `message` | Root-routine message string, present only if that routine ran. |
| `runtime_s` | Float elapsed refinement time in seconds, included in the overall solve duration. |

If the initial residual already meets `fatol`, the root routine is skipped and `accepted=False`. A rejected proposal retains the original positions and `residual_after=residual_before`. The returned allocation still undergoes Finance's financial and risk-budget checks.

Financial restrictions are checked on the normalized weights; they are not imposed in the logarithmic construction program. A construction can therefore fail a requested weight, return, exposure, or other financial limit. Check `result.feasible` and the risk-budget residuals.

### Hierarchical risk parity

```python
model.hierarchical_risk_parity(*, linkage_method="single")
```

`linkage_method` is one of `"single"`, `"complete"`, `"average"`, `"weighted"`, `"centroid"`, `"median"`, or `"ward"`. The method clusters correlation distances and recursively allocates inverse cluster-risk shares. Zero-risk sibling clusters split equally.

HRP requires positive asset variances, positive `net_weight`, and no account. Its implementation materializes asset covariance, including for factor inputs. This is a long-only construction heuristic, not a minimum-variance solution or a guarantee of equal risk contributions. Financial constraints remain checked on the resulting weights. The default solver selection is `"hrp"`; authentication is still required. HRP has no numerical optimization objective or optimality proof, and no Opt or CVXPY program export.

## Return and risk limits

```python
model.require_return(*, minimum)
model.limit_leverage(*, maximum)
model.limit_volatility(*, maximum)
```

`minimum` is a finite net arithmetic-return fraction over the model horizon. It requires expected returns, includes account cash income and recognized transaction/tax costs, and uses worst-case expected return when configured. `limit_leverage` bounds $\sum_i|w_i|$ by its finite nonnegative `maximum`. `limit_volatility` bounds $\sqrt{w^\top\Sigma w}$ by a finite nonnegative horizon return fraction and requires covariance.

A volatility constraint is a conic/quadratically constrained formulation, not an ordinary QP with linear constraints. It uses a supported external route, with SCIP for integer variants.

```python
model.robust_returns(uncertainty, *, radius, uncertainty_ids=None)
```

`uncertainty` is an asset × uncertainty-coordinate matrix $U$: DataFrame, column mapping, dense array, or sparse matrix. `uncertainty_ids` are optional unique string/integer column identifiers, inferred from labeled columns or positional integers. `radius` is a finite nonnegative real scalar.

Under $\mu=\mu_0+Uu$ with $\lVert u\rVert_2\leq\rho$, worst-case return is $\mu_0^\top w-\rho\lVert U^\top w\rVert_2$. This affects utility and the return floor; it does not change covariance. No statistical confidence or out-of-sample guarantee is inferred from the radius. A positive radius with an active utility/return constraint requires a conic route; zero radius removes its effect on the formulation.

## Holdings and exposure limits

```python
model.limit_weights(*, lower=0.0, upper=1.0)
model.limit_exposures(exposures, *, lower, upper, exposure_ids=None)
model.limit_turnover(current_weights=None, *, maximum)
```

`limit_weights` accepts finite scalar bounds that broadcast to all assets, or complete vectors, Series, or mappings. Every lower bound must be at most its upper bound. Negative bounds permit short weights; rebalancing additionally requires borrow availability.

`exposures` is an exposure × asset matrix; DataFrames and column mappings align by both axes, while dense/sparse arrays use `exposure_ids` and model asset order. Exposure identifiers are inferred from row labels or positional integers if omitted. `lower` and `upper` are finite scalars or complete exposure vectors. Each lower bound must not exceed its upper bound. Constraints are `lower <= exposures @ weights <= upper`, in the supplied exposure units. Identifiers must be unique across all exposure groups, including repeated calls.

Turnover is $\sum_i|w_i-w_i^0|$, without a factor of one-half. `current_weights` is a complete finite asset vector; omitted means account initial weights and otherwise raises without an account. `maximum` is a finite nonnegative investment-basis fraction. Supplying current weights changes this turnover reference, not the account's actual initial holdings.

## Rebalancing controls

```python
model.limit_cash(*, minimum=0.0, maximum=None)
model.set_trading_costs(
    *, buy_bps=0.0, sell_bps=0.0, buy_fixed=0.0,
    sell_fixed=0.0, minimum_trade=0.0,
)
model.trade_in_lots(lot_sizes)
model.limit_short_positions(maximum)
```

All four require a starting account. Cash limits are finite amounts in account currency; `maximum=None` means initial portfolio value, not an unbounded upper side. `minimum` must not exceed the effective maximum. A negative lower cash bound explicitly permits borrowing under the model's declared cash-return convention.

Each cost parameter accepts a finite nonnegative scalar or complete asset vector, Series, or mapping. Basis-point fees apply to actual ask/bid transaction values, in addition to spread. Fixed fees are amounts in account currency. `minimum_trade` is a share/quantity threshold. A positive fixed fee requires a positive minimum trade or configured lot size. Buy/sell direction indicators prevent simultaneous opposing trades. Even proportional fees or spreads can introduce integer direction decisions in this formulation; inspect the resulting class.

`lot_sizes` is a positive finite scalar or complete asset vector. Each signed trade must be an integer multiple of its lot size; initial holdings need not themselves be whole lots. `limit_short_positions` supplies a finite nonnegative scalar or complete vector of available borrow quantities in shares. Rebalancing with negative weight bounds requires this setting. It does not itself change weight bounds.

## Tax-lot decisions

```python
model.set_tax_lots(lots, *, as_of, settlement)
model.limit_tax(*, minimum=None, maximum=None)
```

`lots` is a DataFrame indexed by unique acquisition-lot identifiers. An empty table is allowed when no shares are owned. Required and optional columns are:

| Column | Contract |
| --- | --- |
| `asset` | Model asset identifier; an asset may have multiple lots. |
| `quantity` | Positive owned quantity. Supplied lots must cover all starting owned holdings within relative `1e-12`. |
| `cost_basis` | Finite nonnegative basis per share/quantity unit in account currency. |
| `acquired` | Calendar acquisition date, no later than `as_of`. |
| `tax_rate` | Gain tax rate fraction in `[0, 1]`. |
| `loss_credit_rate` | Optional loss credit fraction in `[0, 1]`; default zero. |
| `eligible` | Optional boolean disposal eligibility; default `True`. |
| `quantity_step` | Optional nonnegative disposal step; zero means divisible, positive values require whole step counts. |
| `taxable_proceeds_per_unit` | Optional finite supplied taxable proceeds adjustment; defaults to the asset's actual bid price. |

`as_of` is a calendar date: ISO `YYYY-MM-DD`, `datetime.date`, or supported midnight timezone-naive date-like value. `settlement` is exactly `"immediate"` or `"deferred"`. Tax-lot accounting requires nonnegative owned holdings and nonnegative weight bounds. Each share belongs to the supplied acquisition inventory; no lot identity is inferred after solving.

For each disposal, taxable gain is `(taxable proceeds - cost basis) * quantity sold`. Positive gains use `tax_rate`; negative gains use `loss_credit_rate`. Fees are not automatically deducted from proceeds or basis. Both settlement choices recognize tax in economic return; immediate settlement also changes current cash. Holding-period rates, wash-sale eligibility, tax netting, and jurisdiction-specific rules must be supplied externally.

`limit_tax` bounds net recognized tax in account currency. Each side is a finite scalar or `None` for no bound. A negative minimum limits net credits; this is not a gross-gain budget. Replacing the lot table preserves existing tax limits. In evaluation, supply the actual `tax_lot_sales` vector; weights alone do not identify which acquisition lots were sold.

## Asset selection and conditional allocation

```python
model.select_assets(
    *, count=None, maximum=None, minimum_weight=0.0, equal_weight=False,
)
model.fix_selection(selected)
```

Supply exactly one of `count` or `maximum`: an integer from zero to the number of assets, excluding booleans. `count` specifies exactly that many selected names; `maximum` specifies an upper limit. `minimum_weight` is a finite nonnegative minimum absolute weight for a selected position. A positive exact count requires positive `minimum_weight` or `equal_weight=True`.

`equal_weight` is a Python boolean. Equal weighting requires a positive exact count, positive `net_weight`, no cash account, and `minimum_weight <= net_weight/count`. Weights are nonnegative and each selected name receives `net_weight/count`. This direct selection meaning supports [binary portfolio compilation](quantum.md).

For unequal allocation, selection indicators link signed positions to the configured finite weight bounds. With only a maximum and zero minimum weight, an activated position may remain zero. Other financial limits remain effective.

`fix_selection` requires configured selection when supplying a mask. It accepts a complete Series/mapping or positional vector with `1` for a selected long, `-1` for a selected short, and `0` for exclusion. Boolean masks select longs. The mask must match the exact count or maximum; equal weighting rejects shorts. `None` clears any fixed mask and is also accepted before selection is configured. Replacement validates before changing the stored mask.

Fixing selection retains sizing constraints, costs, and other discrete trading/tax rules. An optimum is conditional on that mask; results record `optimality_scope="fixed_asset_selection"`. The method rejects risk-budgeting, HRP, and moment objectives at model checking. For a hybrid sizing stage, use a separate unequal-allocation model with a positive minimum weight and apply the proposed selection; verify the complete resulting decision.

## Export and evaluate

```python
model.to_model(*, return_variables=False)
model.to_cvxpy()
model.evaluate(weights, *, tax_lot_sales=None, tolerance=1e-7)
```

`to_model` returns a detached Opt `Model` for its supported LP/MILP/QP formulation. `return_variables` must be a Python boolean; `True` returns `(model, expressions)`. The expression dictionary has asset-indexed `weights`; an account also provides `holdings`, `trades`, and account-currency `cash_after`, plus lot-indexed `tax_lot_sales` when configured. Export rejects formulations requiring conic or mixed-integer quadratic backends, moment utility, and HRP.

`to_cvxpy` returns `(problem, expressions)` with a CVXPY Problem and the same financial expression meanings. It supports eligible convex and mixed-integer formulations and rejects HRP or moment utility. Risk budgeting additionally exposes `unnormalized_weights`; normalized weights are generally non-affine expressions, so adding constraints to them can violate CVXPY's DCP rules. Finance's original model is unchanged by mutations to either exported representation.

`evaluate` accepts a complete finite weight vector, Series, or mapping. `tax_lot_sales` is required when acquisition lots are configured, including an empty disposal vector for an empty lot table; otherwise it must be `None`. For risk-budgeting models, supplied weights and evaluated variance must be strictly positive, or evaluation raises `ValueError`. `tolerance` is a finite nonnegative absolute scalar. It returns a dictionary with `objective`, `metrics`, `constraints`, `tables`, and `feasible`, plus `decision` and `costs` for accounts. This operation does not solve or authenticate. It evaluates the supplied decision without optimizing missing tax-lot quantities or repairing a selection.

Constraint rows contain `value`, `lower`, `upper`, `violation`, and `satisfied`. Weight, leverage, turnover, and account cash-balance checks use investment-basis fractions; lot residuals use lot units, exposures use supplied exposure units, and tax rows declare their units. Solver reconstruction residuals are added during solving and are separate from direct weight evaluation. See [results](results.md) for common guarantee and reconciliation rules.

## Portfolio result data

`FinanceResult.weights` is the source-weight Series. Account results additionally expose `holdings`, `trades`, `cash_after`, `post_trade_weights`, and configured `tax_lot_sales`. Costs contain `spread`, `fees`, optional `tax`, and `total` in account currency. Ordinary variance/benchmark objectives have `objective_unit="return_fraction_squared"`; utility, moment, and scenario-risk objectives use `"return_fraction"`; risk-budget construction uses `"dimensionless"`; HRP has no objective unit.

Available metrics follow the configured inputs and objective:

| Group | Metrics and tables |
| --- | --- |
| All evaluated allocations | `gross_exposure`, `net_exposure`; weight and financial constraint rows. |
| Forecasts | `expected_return`; account `gross_expected_return`; robust `worst_case_expected_return`. |
| Covariance | `variance`, `volatility`; `tables["risk_contributions"]` with asset variance/volatility contributions. |
| Factor risk | `factor_exposures` table and `factor_risk_contributions` table. |
| Tracking error | `tracking_error`, optional `active_return`, `beta`; `active_weights` table with `weight`, `benchmark`, `active`. |
| Scenario objectives | `scenario_expected_return`; `scenarios` table with `return`, `loss`, `probability`; relevant `expected_shortfall`/`confidence`, `mean_absolute_deviation`, or `downside_risk`/`downside_target`. |
| Moment utility | `moment_variance`, `third_central_moment`, `fourth_central_moment`; `objective_terms` table of weighted contributions. |
| Risk budgets | `risk_budget_error`; `risk_budgets` table with `budget`, `contribution`, `difference`. |
| HRP | `hierarchy` table with `left`, `right`, `distance`, `size`; `cluster_order` table with `asset_id`. |
| Account | `initial_value`, `portfolio_value`, `cash_after`, `cash_weight`, `cash_return`, `transaction_cost`, `turnover`, `post_trade_variance`, `post_trade_volatility` where covariance is supplied; `trades` table with `before`, `after`, `trade`, `buy`, `sell`, `spread_cost`, `fees`. |
| Tax lots | `tax_liability`, `tax_paid`, `unpaid_tax_liability`, `realized_taxable_gain`, `net_value_after_tax`; `tax_lots` table retaining inputs and `holding_days`, `sold`, `remaining`, `taxable_gain`, `tax_liability`. |
| Fixed selection | `asset_selection` table with `selection`, `weight`; recorded conditional proof scope. |

Undefined volatility contributions and zero-variance benchmark beta are NaN. A result without a primary incumbent does not acquire these financial tables. Use [plotting](plotting.md) for portfolio, frontier, trade, tax-lot, factor, and tail-risk figures.

## Efficient frontier

```python
model.efficient_frontier(
    target_returns, *, client=None, solver=None, mode="local",
    allow_platform=False, tolerance=1e-7, **options,
)
```

`target_returns` is a nonempty finite vector, Series, or mapping. Series/mapping keys are unique target identifiers; arrays receive positional integers. The operation copies the portfolio, selects minimum variance, retains existing constraints, and solves each target in supplied order. A previously configured return floor remains effective: each target is replaced by the greater of the requested target and that floor.

Execution arguments follow [solve](solving.md). Each solve requires Opt authentication. Stable Opt constraints or CVXPY parameters are reused where supported. Infeasible targets remain in the returned result sequence; the original model is unchanged.

The return type is `FrontierResult`:

```python
FrontierResult(targets, results, horizon)
```

`targets` is the requested-return Series; `results` is a tuple of `FinanceResult` records in the same order; `horizon` is the portfolio horizon string. The frozen dataclass's `table` property creates a DataFrame indexed by target identifier with `target_return`, `effective_target`, `status`, `feasible`, `optimality_proven`, `objective`, and each result's financial metrics. Its `attrs["horizon"]` records the horizon.

The constructor stores its arguments without validation; records returned by `efficient_frontier` have consistent target/result ordering. The `table` property expects every result to retain `provenance["inputs"]["minimum_return"]` for its effective target. Freezing the dataclass prevents field reassignment; contained Series and financial result objects remain mutable.

`to_dict()` returns a dictionary; `to_json()` returns a JSON string. These numeric reports contain schema version one, type `efficient_frontier`, horizon, targets, and result reports. Use [io interchange](interchange.md) to preserve reversible pandas and result structures. Plot with `plot.efficient_frontier`.
