# Collateral allocation

`CollateralAllocationModel` assigns owned inventory to explicitly permitted dated pledges. It minimizes supplied full-term opportunity and movement costs while preserving inventory, delivery timing, adjusted coverage, and concentration rules. Import it and `haircut_adjusted_value` from `qpiai_finance.collateral`.

The model is deterministic planning on a calendar-date grid. Permitted pledge rows encode the institution's legal-entity, location, eligibility, and settlement restrictions. It does not infer those rules or book collateral movements.

## Constructor

```python
CollateralAllocationModel(
    inventory, requirements, pledges, *, as_of, dates, reporting_currency,
)
```

The first three arguments are pandas DataFrames with unique string/integer row identifiers and exactly the columns below. Unknown or duplicate columns are rejected. `as_of` is a calendar date; `dates` is a nonempty unique increasing calendar-date sequence beginning at `as_of`. Every requirement and pledge date must belong to this grid. `reporting_currency` is an uppercase three-letter code for the supplied cost objective.

### Inventory table

| Column | Type, default, and meaning |
| --- | --- |
| `quantity` | Required finite nonnegative owned quantity in physical asset units. |
| `price` | Required strictly positive finite native-currency price per unit. |
| `currency` | Required uppercase three-letter price currency. |
| `encumbered` | Optional finite quantity in `[0, quantity]`; default zero. Unavailable throughout the planning horizon. |

Each row represents distinct owned inventory; repeating the same physical quantity in several rows would duplicate availability. Inventory must be nonempty. Free inventory is owned quantity less persistent encumbrances.

### Requirement table

| Column | Type and meaning |
| --- | --- |
| `obligation` | Required string/integer obligation identifier. |
| `date` | Required planning date. |
| `amount` | Required finite nonnegative coverage amount. |
| `currency` | Required uppercase three-letter obligation currency. |

The table must be nonempty. Each obligation/date pair is unique and each obligation uses one currency. Row identifiers distinguish requirements; no netting is inferred.

### Permitted pledge table

| Column | Type, default, and meaning |
| --- | --- |
| `asset` | Required inventory-row identifier. |
| `obligation` | Required supplied obligation identifier. |
| `pledge_date` | Required date when inventory becomes committed. |
| `delivery_date` | Required date when coverage begins. |
| `release_date` | Required date when coverage ends. |
| `return_date` | Required date when inventory becomes available again. |
| `haircut` | Required finite fraction in `[0,1]`. A haircut of one gives zero adjusted coverage. |
| `unit_cost` | Required finite nonnegative full-term cost per physical asset unit in `reporting_currency`. |
| `fx_rate` | Optional strictly positive valuation rate in obligation-currency units per inventory-currency unit. Required for cross-currency pledges; same-currency values must equal one. |

Dates must satisfy `pledge_date <= delivery_date < release_date <= return_date`. Each pledge must cover at least one supplied obligation/date. Empty pledge tables are allowed when they retain the required columns. There is one fixed assignment quantity per pledge alternative.

Inventory is locked on `[pledge_date, return_date)`; coverage applies on `[delivery_date, release_date)`. Returned inventory is available before new commitments on the same date. Quantities awaiting return do not cover margin and are not free inventory. This is distinct from intraday sequencing or received-collateral reuse.

Read-only properties return detached `asset_ids`, `pledge_ids`, and `dates` Indices, plus the string `reporting_currency`.

## Coverage and objective

For pledge quantity $q_j$, its delivered adjusted value at a covered requirement date is $q_jp_{t,a(j)}(1-h_{tj})f_{tj}$. Coverage for an obligation/date is the sum over its delivered permitted pledges. Prices are native currency, haircuts are fractions, and $f$ converts valuation to the obligation currency. This FX rate values collateral; it does not execute a currency trade.

The objective is $\sum_j\texttt{unit_cost}_j q_j$ in reporting currency. Unit costs already cover the full term. Finance does not annualize them or convert them from inventory/obligation currencies.

## Dated assumptions

Configuration methods modify the model and return `self`.

```python
model.set_availability(quantities)
model.set_prices(prices)
model.set_haircuts(haircuts)
model.set_fx_rates(fx_rates)
```

All arguments accept a finite scalar broadcast over the relevant grid, a complete two-dimensional array, or an aligned DataFrame. Rows cover every planning date. Columns are inventory identifiers for availability/prices and pledge identifiers for haircuts/FX. DataFrames align both axes; arrays follow `dates` and the corresponding identifier order.

| Argument | Domain, default, and meaning |
| --- | --- |
| `quantities` | Nonnegative available free inventory per date/asset, never above owned quantity less persistent encumbrances. Default is that free inventory at every date. Can reserve external uses or delay availability, not create inventory. |
| `prices` | Strictly positive per-unit price path in each asset's native currency. Default is the flat inventory price. The entire supplied path, including `as_of`, replaces it. |
| `haircuts` | Fractions in `[0,1]` by date/pledge. Default is the pledge's flat haircut. |
| `fx_rates` | Strictly positive obligation/native valuation rates by date/pledge. Default is the pledge's flat rate. Same-currency rates must be exactly one at every date. |

No interpolation, forecast model, or scenario probability is inferred. Repeating a setter replaces the corresponding path.

## Assignment, coverage, and movement limits

```python
model.limit_assignments(*, lower=0.0, upper=None)
model.pledge_in_lots(lot_sizes)
model.limit_coverage(maximum)
model.limit_movements(*, pledged=None, returned=None)
model.limit_concentration(groups, *, maximum_share)
```

| Parameter | Type, default, and meaning |
| --- | --- |
| Assignment `lower`, `upper` | Finite scalars or complete pledge vectors/Series/mappings in physical quantity units, with `0 <= lower <= upper`. Default lower zero; `upper=None` retains the previously configured upper bounds. Initial uppers are available free quantities for each asset. Bounding an empty pledge set raises. |
| `lot_sizes` | Positive finite scalar or complete inventory-asset vector/Series/mapping. Each pledge quantity is an integer multiple of its asset's lot size. |
| Coverage `maximum` | Finite scalar or complete requirement-indexed vector/Series/mapping in each requirement's currency. Must be at least the required amount. Default coverage upper bounds are unbounded. |
| `pledged`, `returned` | Optional nonnegative finite scalar or date × asset array/DataFrame limiting outgoing and incoming quantities separately. Supply at least one side. An omitted side retains its previous limits; both initially have no upper limit. |
| `groups` | Complete asset classification sequence/Series/mapping with nonblank string/integer group labels. |
| `maximum_share` | Finite scalar or complete group-indexed vector/Series/mapping in `[0,1]`; groups follow first occurrence. |

Concentration caps each group's delivered, haircut/FX-adjusted share of actual total coverage at each obligation/date. The denominator is delivered adjusted value, not required margin or unadjusted inventory value. Every concentration call adds a classification. Cash quantities or unlike asset units are not combined in movement limits.

## Execution, export, and evaluation

```python
model.to_matrix()
model.to_model(*, return_variables=False)
model.to_cvxpy()
model.evaluate(assignments, *, tolerance=1e-7)
```

The formulation is LP for divisible assignments and MILP when lots are configured and pledge alternatives exist. It uses the Opt route by default; [solving](solving.md) defines authentication, local/platform modes, and compatible external selection.

`to_matrix` returns a detached sparse Opt matrix dictionary. Assignment columns are physical quantities or configured lot counts; coverage columns are each requirement's native-currency adjusted amount. `to_model` returns a detached Opt model; `return_variables=True` (Python boolean) returns `(model, expressions)`. `to_cvxpy` returns `(problem, expressions)`. Both mappings contain pledge-indexed `assignments` in physical units and requirement-indexed `coverage` in native currency. [Custom models](custom-models.md) describes explicit compilation and recovery.

`evaluate` accepts a complete finite assignment vector, Series, or mapping in pledge order. When no pledges exist, supply an empty mapping, Series, list, tuple, or ndarray. `tolerance` is a finite nonnegative absolute scalar. It returns `objective`, `feasible`, `constraints`, `decision`, `metrics`, `tables`, and `costs` after rebuilding inventory locks, movements, valuations, coverage, concentration, and costs. It requires no authentication and does not optimize or repair the supplied quantities.

## Result fields

`result.assignments` is a pledge-indexed Series named `quantity`. Objective and cost units are `reporting_currency`. Metrics are `total_cost` and `active_pledges`; costs contain `collateral_cost` and `currency`.

| Table under `result.tables` | Columns and axes |
| --- | --- |
| `collateral_coverage` | Requirement-indexed original `obligation`, `date`, `currency`, plus `required`, `adjusted_value`, `surplus`, `maximum`. |
| `collateral_inventory` | Index `(date, asset)`; `available_before_plan`, `externally_encumbered`, `committed`, `outbound`, `delivered`, `awaiting_return`, `unallocated`, `pledged`, `returned`, `unit`. |
| `collateral_assignments` | Pledge input fields plus chosen `quantity`, `total_cost`, and `reporting_currency`. |
| `collateral_coverage_components` | `requirement`, `pledge`, `date`, `asset`, `price`, `haircut`, `fx_rate`, `quantity`, `adjusted_value_per_unit`, `adjusted_value`, `currency`. |
| `collateral_concentrations` | Configured groups with covered pledge routes: `classification`, `requirement`, `group`, `adjusted_value`, `total_coverage`, `share`, `maximum_share`, `currency`. Zero-coverage shares are NaN; the table is absent when there are no group rows. |

Constraint rows identify physical units, lot units, or the relevant currency. Solving also checks integer reconstruction and reconciles solver coverage with recomputed values. See [results](results.md) for feasibility and proof scope. Plot with `plot.collateral_coverage` and `plot.collateral_inventory`.

Quantities and monetary values are floats. `active_pledges` is an integer counting strictly positive assignment quantities, independently of tolerance. `collateral_assignments` retains the pledge index; coverage-component and concentration tables use positional indices. `classification` identifies concentration calls in zero-based order. Concentration shares and haircuts are dimensionless fractions; `adjusted_value_per_unit` uses obligation currency per physical asset unit.

In the inventory table, `committed = outbound + delivered + awaiting_return`. `pledged` and `returned` are movements on that date, while the other three columns are quantities in each state. `unallocated = available_before_plan - committed`. `externally_encumbered` retains the inventory table's persistent encumbrance; additional reservations supplied through `set_availability` reduce `available_before_plan`.

## `haircut_adjusted_value`

```python
haircut_adjusted_value(market_values, *, haircuts, fx_rates=1.0)
```

`market_values` is a finite nonnegative numeric scalar, array-like input, Series, DataFrame, or mapping. `haircuts` is a required finite coefficient in `[0,1]`; `fx_rates` is a strictly positive finite coefficient, default one, in target-currency units per native unit. Each coefficient accepts a scalar, broadcastable array, or compatible labeled input.

Returns `market_values * (1-haircuts) * fx_rates` per entry: float for a scalar, ndarray for an array-like input, Series named `collateral_value` for a Series/mapping, or DataFrame preserving axes. A coefficient Series/mapping aligns to a value Series' index or DataFrame columns; a coefficient DataFrame aligns both axes. Labeled coefficients require labeled values. Axes must be unique.

Use per-unit prices instead of total market values to prepare valuation coefficients for custom models. Sum explicitly only after establishing compatible currency units. This calculation does not establish eligibility, inventory availability, settlement rights, or a regulatory treatment.

Invalid tables, dates, identifiers, domains, label alignment, or unrepresentable values raise `TypeError` or `ValueError`. Structurally valid but insufficient inventory or incompatible hard limits can produce an infeasible optimization result.
