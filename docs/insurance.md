# Insurance and reinsurance decisions

`ReinsuranceModel` selects quoted contracts or prevalued programs against supplied joint claim scenarios. It balances premium and retained risk while enforcing the specified coverage, counterparty, cost, and surplus limits. Finance does not price a treaty or infer how overlapping contract terms interact.

Import `ReinsuranceModel`, `excess_of_loss`, and `quota_share` from `qpiai_finance.insurance`. Liability-driven investment and cash planning use the shared [portfolio](portfolio.md), [liability matching](liability-matching.md), and [funding](funding.md) models.

## Constructor

```python
ReinsuranceModel(
    gross_losses, recoveries, premiums, *, recovery_composition,
    currency, horizon, as_of, probabilities=None, scenario_ids=None,
    contract_ids=None,
)
```

| Parameter | Contract |
| --- | --- |
| `gross_losses` | Nonempty finite nonnegative scenario vector, Series, or mapping in model currency. |
| `recoveries` | Scenario × quoted-contract matrix: DataFrame, supported column mapping, dense array, or sparse matrix. Every standalone recovery must lie between zero and that scenario's gross loss. |
| `premiums` | Complete finite nonnegative contract vector, Series, or mapping of fixed quoted premiums. |
| `recovery_composition` | Required `"exclusive"` or `"additive"`, with the meanings below. |
| `currency` | Uppercase three-letter currency code for every monetary input. |
| `horizon` | Nonblank common insurance horizon description. |
| `as_of` | Calendar valuation/decision date. |
| `probabilities` | Optional complete finite nonnegative scenario vector, Series, or mapping, summing to one within absolute `1e-12`. Required for expected/tail objectives or limits. |
| `scenario_ids` | Optional unique string/integer case identifiers, inferred from labeled gross losses or positional order. |
| `contract_ids` | Optional unique string/integer quote identifiers, inferred from recovery columns or positional order. An empty quote set is allowed with an empty matching premium vector and a scenario × zero-column recovery matrix. |

Inputs share one currency and consistent horizon/valuation basis; no discounting, price calibration, or FX conversion is inferred. Labeled inputs align by identifier. Read-only `contract_ids` and `scenario_ids` return detached Indices; `currency` returns the declared code.

Initially, recoverability is one and contingent costs are zero. Each quote is optional, the contract-count range is zero through the number of quotes, and there is no premium cap, counterparty limit, surplus floor, or expected-shortfall cap. The declared composition and gross-loss recovery cap still apply.

### Contract composition

`"exclusive"` permits at most one quoted alternative. One column may represent a complete jointly valued program, allowing comparison of several valid programs.

`"additive"` declares that supplied contract recoveries and contingent costs can be added for every permitted selection. The caller must establish this contractual compatibility, including inuring order, triggers, exhaustion, and other interactions. The gross-loss cap is a feasibility constraint on summed contractual recovery; it does not validate an overlapping payout model. Use jointly valued program alternatives when standalone recoveries cannot be added correctly.

## Financial equations and objectives

For binary selections $z_k$, quoted premiums $P_k$, contractual recoveries $R_{sk}$, collectible fractions $a_{sk}$, and contingent charges $C_{sk}$:

$$
\operatorname{premium}=\sum_kP_kz_k,\qquad N_s=X_s-\sum_ka_{sk}R_{sk}z_k,\qquad T_s=N_s+\operatorname{premium}+\sum_kC_{sk}z_k.
$$

$N_s$ is retained claims and $T_s$ total scenario cost. The default objective minimizes expected total cost and therefore requires probabilities. Configuration methods modify the model and return `self`.

```python
model.minimize_expected_cost(*, tail_weight=0.0, confidence=0.95)
model.minimize_expected_shortfall(*, confidence=0.95)
model.minimize_premium()
```

`tail_weight` is a finite real in `[0,1]`; `confidence` lies strictly in `(0,1)`. Expected-cost optimization minimizes `(1-tail_weight) * E[T] + tail_weight * ES(T)`. `minimize_expected_shortfall` sets the tail weight to one. Both concern total cost, including fixed premium exactly once, and require probabilities. Tail risk uses the financial upper loss tail with fractional boundary mass.

`minimize_premium` minimizes fixed quoted premium only. It needs no probabilities when no probabilistic hard limits remain. Contingent costs still enter total-cost and surplus constraints. Without coverage/risk mandates, an empty selection may be cheapest. Hard constraints remain active when changing objectives.

## Recovery and contingent-cost assumptions

```python
model.set_recoverability(factors)
model.set_contingent_costs(costs)
```

`factors` is a scalar or a complete scenario × contract matrix of finite collectible fractions in `[0,1]`; the default is one. Matrix input supports aligned DataFrames, column mappings, dense arrays, or sparse matrices. Do not apply collectibility twice to already-net recoveries. Supplied factors can represent joint counterparty/default/basis scenarios; Finance does not estimate them.

`costs` is a complete finite nonnegative scenario × contract matrix in model currency, using the same matrix formats. These are charges in addition to quoted fixed premium, such as supplied reinstatement charges. No formula or contract interaction is inferred. Repeated setters replace the corresponding matrix/assumption.

## Selection and premium limits

```python
model.limit_selections(*, lower=0.0, upper=1.0)
model.limit_contract_count(*, minimum=0, maximum=None)
model.add_exclusive_group(contract_ids)
model.limit_premium(maximum)
```

Selection bounds are numeric `0/1` scalars or complete contract vectors, Series, or mappings, with `lower <= upper`. They fix required or forbidden alternatives. Numeric boolean arrays are not the general finite-real configuration input; use numeric zero/one bounds.

Contract-count limits are whole-valued finite real numbers from zero to the number of quotes, excluding booleans, with `minimum <= maximum`. `maximum=None` means the total number of quotes. Global exclusive composition still limits the count to one.

`add_exclusive_group` takes a nonempty unique sequence/Index of quoted contract identifiers, not one string. Each call adds an at-most-one rule. Groups may overlap. This is additional selection logic, not a declaration that all other recoveries compose correctly.

`limit_premium` takes a finite nonnegative currency amount and caps fixed premium only, excluding contingent charges.

## Loss, tail, and counterparty limits

```python
model.limit_retained_loss(maximum)
model.limit_total_cost(maximum)
model.limit_expected_shortfall(
    maximum, *, confidence=0.95, measure="total_cost",
)
model.limit_counterparty_exposure(
    coefficients, *, maximum, exposure_ids=None,
)
```

The first two `maximum` arguments are finite nonnegative scalars or complete scenario vectors, Series, or mappings in model currency. They bound retained claims or total scenario costs separately. Defaults have no additional upper limits beyond gross-loss and nonnegative-loss requirements.

Expected-shortfall limits require probabilities. `maximum` is a finite nonnegative currency amount; `confidence` is in `(0,1)`; `measure` is exactly `"total_cost"` or `"retained_loss"`. Each `(measure, confidence)` pair has its own cap; another call with that pair replaces it while preserving other caps.

Counterparty `coefficients` form a nonnegative exposure × contract matrix of additive currency exposure per selected quote. Supported formats are DataFrame, column mapping, dense array, and sparse matrix. `exposure_ids` optionally supplies unique row identifiers; otherwise labels or positional integers define them. `maximum` is a finite nonnegative scalar or complete exposure vector. Every call adds its rows; overlapping classifications are allowed. The caller supplies the exposure basis, such as covered limits. These values are not inferred default risk or regulatory capital.

## Surplus requirements

```python
model.set_surplus_before_claims(surplus)
model.require_surplus(minimum=0.0)
```

`surplus` and `minimum` are finite scalars or complete scenario vectors, Series, or mappings in model currency; signed values are allowed. Supply surplus before requiring a floor.

The starting state is assets minus other liabilities before the modeled claims and reinsurance plan. It must exclude these gross claims, recoveries, premiums, and contingent costs. Finance applies them once as `surplus_after = surplus_before_claims - total_cost`. Investment outcomes and unrelated liabilities may already be included in the supplied state. No asset repricing or regulatory capital formula is inferred.

## Export, execution, and evaluation

```python
model.to_matrix()
model.to_model(*, return_variables=False)
model.to_cvxpy()
model.evaluate(selections, *, tolerance=1e-7)
```

Quoted selections form a MILP; an empty quote set gives an LP. Default Finance solving uses the Opt route. Follow [solving](solving.md) for authentication, modes, and supported external selection. With stress cases, select `minimize_premium` and use hard scenario mandates rather than inventing probabilities.

`to_matrix` returns equivalent detached sparse Opt matrix data. Selection columns are binary choices; retained/total costs and tail auxiliaries use model currency. `to_model` returns an independent Opt model, or `(model, expressions)` when the Python boolean `return_variables=True`. `to_cvxpy` returns `(problem, expressions)`. Both expose contract-indexed `selections`, scalar `premium`, and scenario-indexed `retained_losses`/`total_costs`. See [custom models](custom-models.md) for explicit compilation and verification scope.

`evaluate` accepts one finite numeric or boolean selection per quote, as an array, Series, or mapping. It checks bounds and integrality rather than silently rounding fractions. `tolerance` is a finite nonnegative absolute scalar. Returns `objective`, `feasible`, `constraints`, `decision`, `metrics`, `tables`, and `costs` after recomputing contractual and collectible recovery, retained/total loss, surplus, and all mandates. No solver or credential is used.

## Result fields

`decision["selections"]` is a contract-indexed Series named `selection`, also exposed by `result.selections`. The objective unit is model currency. The following fields are conditional on supplied probabilities and settings:

| Location | Contents |
| --- | --- |
| `metrics` | `premium`, `selected_contracts`; with probabilities, `expected_gross_loss`, `expected_contractual_recovery`, `expected_collectible_recovery`, `expected_retained_loss`, `expected_contingent_cost`, `expected_total_cost`. Active tail-weighted objectives additionally report `objective_expected_shortfall`. |
| `costs` | `premium`, `currency`, and `expected_contingent_cost` when available. |
| `reinsurance_scenarios` table | `gross_loss`, `contractual_recovery`, `collectible_recovery`, `recovery_shortfall`, `retained_loss`, `premium`, `contingent_cost`, `total_cost`, `currency`; optional `probability`, `surplus_before_claims`, `surplus_after`, `minimum_surplus`. |
| `reinsurance_contracts` table | `selection`, `quoted_premium`, `premium_paid`, `minimum_selection`, `maximum_selection`, `currency`. |
| `expected_shortfall_limits` table | Configured `measure`, `confidence`, `actual`, `maximum`, `currency`. |
| `counterparty_exposures` table | `classification`, `exposure`, `amount`, `maximum`, `currency`. |

Tables are under `result.tables`. Constraint rows include their units. Solving additionally checks selection reconstruction and reconciles solver premium, retained-loss, and total-cost columns with recalculated amounts. See [results](results.md) for feasibility and proof acceptance. Plot with `plot.reinsurance_losses` and `plot.reinsurance_surplus`.

Monetary metrics and table columns are floats in model currency. `selected_contracts` is an integer counting strictly positive selection entries, including when an invalid fractional proposal is being evaluated. Selection values, bounds, and probabilities are dimensionless floats. Scenario and contract tables retain their identifier indices; tail-limit and counterparty tables use positional indices. `classification` numbers identify counterparty-limit calls in zero-based order. Selection checks use `binary` units, count/exclusivity checks use `contracts`, and other constraints use currency. `recovery_shortfall` is contractual minus collectible recovery.

## Recovery calculation API

```python
excess_of_loss(losses, *, attachment, limit)
quota_share(losses, *, share)
```

`losses` is a finite nonnegative numeric scalar, array-like input, Series, or DataFrame in one loss unit. `attachment` and `limit` are finite nonnegative scalars in that unit. The layer recovery is `min(max(loss-attachment, 0), limit)`. `share` is a finite scalar in `[0,1]`; quota-share recovery is `share*loss`.

Return type follows the input: float for a scalar, ndarray for other array-like inputs, Series named `recovery`, or DataFrame retaining axes. These functions evaluate the stated basic payout before deductibles, aggregates, reinstatements, exclusions, commission, co-insurance, counterparty collectibility, or inuring-order adjustments. Apply them to the correct covered loss basis. They neither price a contract nor establish that its standalone recovery can be added to another contract.

Invalid loss domains, composition, probabilities, labels, bounds, risk measures, or unrepresentable outputs raise `TypeError` or `ValueError`. Structurally valid but incompatible hard mandates can produce an infeasible optimization result.
