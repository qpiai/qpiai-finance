# Credit allocation

`CreditAllocationModel` chooses final facility amounts within approved capacity, funding, capital, exposure, and loss limits. Existing allocations and supplied increase/reduction costs support changes to a credit book. Decisions are final amounts, not cash-flow schedules or individual underwriting approvals.

Import from `qpiai_finance.credit`. Inputs use one currency and declared horizon. Allocation economics, expected loss, capital consumption, and exposure attribution remain separate supplied quantities.

## Constructor

```python
CreditAllocationModel(
    income_rates, *, funding_costs, expected_loss_rates,
    capital_requirements, capacity, currency, horizon, as_of,
    facility_ids=None, funding_requirements=1.0, exposure_per_unit=1.0,
    current_allocations=0.0,
)
```

| Parameter | Type, default, and meaning |
| --- | --- |
| `income_rates` | Required finite facility vector, Series, or mapping of expected income per allocated currency unit, before separately supplied costs and losses. |
| `funding_costs` | Required finite scalar or complete facility vector of funding cost per allocated unit; signed values are allowed. |
| `expected_loss_rates` | Required nonnegative finite scalar or complete vector of expected credit loss per allocated unit. |
| `capital_requirements` | Required nonnegative finite scalar or complete vector of capital currency consumed per allocated currency unit. |
| `capacity` | Required nonnegative finite scalar or complete vector of approved maximum amounts. Zero forbids allocation. |
| `currency` | Required uppercase three-letter code for amounts. |
| `horizon` | Required nonblank common forecast/loss horizon description. |
| `as_of` | Required calendar decision date. |
| `facility_ids` | Optional unique string/integer identifiers; infer from labeled income or use positional integers. |
| `funding_requirements` | Nonnegative finite scalar or complete vector; default `1.0` currency of final funding use per allocated unit. |
| `exposure_per_unit` | Nonnegative finite scalar or complete vector; default `1.0`, the policy exposure attributed per allocated unit. |
| `current_allocations` | Nonnegative finite scalar or complete vector of existing amounts; default zero. |

Complete vectors accept arrays, Series, and mappings aligned by facility identifier; scalars broadcast for the parameters explicitly described above. Bounds initially allow zero through approved capacity; no aggregate funding or capital cap is imposed until configured. Current allocations are an economic reference, not automatically a lower bound. Read-only `facility_ids` returns a detached Index; `currency` returns the code. See [data conventions](data.md).

## Objective and expected loss

Configuration methods modify the model and return `self`.

```python
model.maximize_risk_adjusted_income(
    *, capital_charge=0.0, risk_aversion=0.0, confidence=0.95,
)
```

`capital_charge` and `risk_aversion` are finite nonnegative real scalars. `confidence` is strictly in `(0,1)`. The objective is expected income minus funding costs, expected credit losses, costs of changing the existing book, `capital_charge * capital_used`, and any `risk_aversion * ES(scenario_loss)` term. All terms use model currency over the declared horizon. Zero risk aversion is the default; a positive value requires probabilistic loss scenarios already configured.

Expected-loss rates are not scenario tail risk or capital. An ES preference is an additional risk tradeoff and does not silently replace the supplied expected-loss estimate.

```python
model.set_default_risk(
    probability_of_default, loss_given_default, exposure_at_default,
)
```

Each argument accepts a scalar or complete finite facility vector, Series, or mapping. PD and conditional mean LGD lie in `[0,1]`; EAD is nonnegative exposure currency per allocated currency unit. The method replaces expected-loss rates with the supplied `PD * LGD * EAD`, retaining the factors for financial calculation. It does not change the separate `exposure_per_unit` policy basis or estimate loss correlation, tail risk, capital, provisions, or jurisdictional rules.

## Amount, resource, and discrete limits

```python
model.limit_allocations(*, lower=0.0, upper=None)
model.limit_funding(maximum)
model.limit_capital(maximum)
model.allocate_in_lots(lot_sizes)
model.select_facilities(*, minimum, maximum_count=None)
model.set_transaction_costs(*, increase=0.0, decrease=0.0)
```

| Method parameter | Type, default, and meaning |
| --- | --- |
| Allocation `lower`, `upper` | Nonnegative finite scalar or complete facility vector. Default lower zero; `upper=None` restores approved capacity. Require `lower <= upper <= capacity`. |
| Funding `maximum` | Required finite nonnegative amount bounding `funding_requirements @ allocations`. It concerns the final book, not origination cash or sale proceeds. |
| Capital `maximum` | Required finite nonnegative amount bounding `capital_requirements @ allocations`. |
| `lot_sizes` | Required positive finite scalar or complete facility vector of final-allocation currency steps. |
| Selection `minimum` | Required strictly positive finite scalar or complete vector of amounts per active facility. Each facility must receive zero or at least that amount. Zero approved capacity remains ineligible. |
| `maximum_count` | Optional whole-valued finite real in `[0, number_of_facilities]`, excluding booleans; default all facilities. |
| `increase`, `decrease` | Nonnegative finite scalars or complete facility vectors of change cost per currency unit; default zero. Applied to positive increases and reductions from `current_allocations`, respectively. |

Lots and optional-facility activation introduce integer decisions. Reductions may represent permitted sales/runoffs under supplied economics; the model does not infer settlement proceeds, contractual sale prices, or legal permission. Allocation bounds define the permissible final book.

## Policy exposures and concentrations

```python
model.limit_exposures(
    coefficients, *, upper, lower=0.0, exposure_ids=None,
)
model.limit_concentration(groups, *, maximum_share)
```

Exposure `coefficients` form a finite nonnegative exposure × facility matrix: aligned DataFrame, supported column mapping, dense array, or sparse matrix. `exposure_ids` optionally specifies unique row identifiers; otherwise use row labels or positional integers. `lower` and `upper` are finite scalar or complete exposure vectors, Series, or mappings, with `0 <= lower <= upper`. Every call adds a block of `lower <= coefficients @ allocations <= upper`. Coefficients express exposure currency per allocated currency unit. Rows may overlap, including connected-party exposure rules.

`groups` is a complete sequence, Series, or mapping assigning one nonblank string/integer classification per facility. `maximum_share` is a finite scalar or complete group-indexed vector in `[0,1]`; group order follows first occurrence. Each call adds a classification. Group exposure is `sum(exposure_per_unit[i] * allocation[i])`; its cap is the given fraction of total exposure. A zero-total book has zero group amounts and satisfies these constraints; its reported shares are NaN. Overlapping groups require explicit exposure rows rather than a single classification label per facility.

## Scenario and tail loss

```python
model.set_loss_scenarios(scenarios)
model.limit_scenario_loss(maximum)
model.limit_expected_shortfall(maximum, *, confidence=0.95)
```

`scenarios` is a `Scenarios` object with `unit="loss_fraction"`, matching model horizon, exactly the facility identifiers, and nonnegative loss per allocated currency unit. It is copied and aligned. Omitted probabilities describe stress cases; ES requires explicit probabilities. Scenario mean loss is reported separately and does not replace expected-loss rates.

`limit_scenario_loss` requires configured scenarios. Its `maximum` is a nonnegative finite scalar or complete scenario vector, Series, or mapping in currency. Replacing scenarios preserves these limits by scenario identifier; changing identifiers while such limits exist raises.

The ES cap is one finite nonnegative currency amount, with confidence strictly in `(0,1)` and default `0.95`. It has its own confidence independent of objective risk aversion. Repeating this setter replaces the previous ES cap. It does not impose a per-scenario maximum. Replacing scenarios without probabilities is rejected while a probabilistic ES setting is active.

## Execution, export, and evaluation

```python
model.to_model(*, return_variables=False)
model.to_cvxpy()
model.evaluate(allocations, *, tolerance=1e-7)
```

The class is LP without lots/activation and MILP otherwise; it uses the Opt route by default. Root `validate`, `inspect`, and `solve` follow [solving](solving.md). Every Finance solve requires Opt authentication.

`to_model` returns a detached Opt formulation; a Python boolean `return_variables=True` returns `(model, expressions)`. `to_cvxpy` returns `(problem, expressions)`. Both expose facility-indexed `allocations` and `allocation_changes` in actual currency amounts, including when solver variables count lots. Mutating an export does not change the financial specification. [Custom models](custom-models.md) explains explicit representation compilation and source recovery.

`evaluate` accepts a complete finite allocation vector, Series, or mapping; `tolerance` is a finite nonnegative absolute scalar. It returns `objective`, `feasible`, `constraints`, `decision`, `metrics`, `tables`, and `costs`. It recalculates economics, amounts, lots/activation, resources, concentrations, and configured scenario limits without solving or authenticating. Negative or fractional-lot decisions are checked against the source constraints rather than repaired.

## Result fields

`result.allocations` is a facility-indexed Series named `allocated_amount`; `allocation_changes` is a Series named `change`. Objective unit is model currency.

| Location | Contents |
| --- | --- |
| `metrics` | `allocated_amount`, `expected_income`, `funding_cost`, `expected_credit_loss`, `transaction_cost`, `capital_cost`, `capital_used`, `funding_used`, `exposure_at_default`, `net_income`; optional `scenario_expected_loss`, `objective_expected_shortfall`, `tail_risk_cost`, `constrained_expected_shortfall`. `net_income` subtracts funding, expected loss, and change costs, before the separately reported capital and tail charges. |
| `costs` | Applicable `funding_cost`, `expected_credit_loss`, `transaction_cost`, `capital_cost`, and `tail_risk_cost`. |
| `allocations` table | `current_amount`, `allocated_amount`, `increase`, `reduction`, `capacity`, `expected_income`, `funding_cost`, `expected_credit_loss`, `transaction_cost`, `capital_cost`, `net_contribution`, `capital_used`, `funding_used`, `exposure_at_default`, `currency`. |
| `resources` table | Funding/capital rows with `used`, `limit`, `currency`. |
| `exposures` table | Configured `classification`, `exposure`, `amount`, `lower`, `upper`, `currency`. |
| `concentrations` table | `classification`, `group`, `amount`, `total_exposure`, `share`, `maximum_share`, `currency`. |
| `scenario_losses` table | Scenario-indexed `loss`, `currency`, optional `probability` and configured `maximum`. |

Tables are under `result.tables`. Solving additionally checks integer/activation reconstruction and reconciles derived total exposure. [Results](results.md) defines proof and feasibility acceptance; [plotting](plotting.md) covers allocations, resources, and concentration figures.

Amounts, income, losses, costs, and resource metrics are floats in model currency. In both metrics and tables, `exposure_at_default` means `exposure_per_unit * allocations` summed where appropriate; it retains that policy basis after `set_default_risk`. Expected credit loss separately uses the supplied PD, LGD, and EAD factors. The allocation table's `net_contribution` deducts funding, expected loss, change costs, and the capital charge; it excludes the portfolio-level tail-risk charge. The objective is `net_income - capital_cost - tail_risk_cost`, taking the last term as zero when inactive.

Allocation and scenario tables retain their identifier indices. `resources` is indexed by `funding` and `capital`; `exposures` and `concentrations` use a positional row index, with zero-based `classification` numbers identifying the corresponding configuration calls. Concentration `share` and `maximum_share` are dimensionless floats. Constraint units are currency except `allocation_lots` residuals in lot counts and `facility_count` in facilities. Selection treats every strictly positive allocation as active, independently of the verification tolerance.

Invalid dimensions, labels, rate domains, limits, scenario units, or unrepresentable calculations raise `TypeError` or `ValueError`. A structurally valid set of contradictory policy limits can produce an infeasible solve. Financial policy, capital rules, underwriting eligibility, and appropriate institution-specific treatment are supplied inputs.
