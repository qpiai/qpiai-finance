# Scenarios, paths, and information trees

Import `Scenarios`, `ScenarioPaths`, and `ScenarioTree` from `qpiai_finance.scenarios`. Use `Scenarios` for one outcome vector per case, `ScenarioPaths` for ordered realizations, and `ScenarioTree` for information available when decisions are made. Construction and evaluation require no authentication.

## Common conventions

Values are finite real numbers. Asset and scenario identifiers are nonempty unique strings or integers. Labeled inputs align by identifier; arrays follow declared axis order. Horizon and unit descriptions are nonblank strings and do not rescale values.

Supply probabilities to describe a distribution. Omit them for deterministic stress cases; Finance does not infer equal weights. Explicit probabilities must be nonnegative and sum to one within absolute `1e-12`, and matching labeled inputs align by scenario. Accepted probabilities retain their normalized relative meaning. Zero-probability cases remain available for hard stress and policy checks.

`origin` is optional nonblank descriptive text. `metadata` is an optional dictionary of finite JSON-compatible data with string keys; default empty. It is normalized through JSON, so tuples become lists. It records supplied construction information, not executable behavior. Descriptive fields such as `horizon`, `unit`, and `origin` are ordinary attributes initialized from the constructor arguments. Copies of metadata and property tables are detached. Dates and instants follow [data conventions](data.md).

## `Scenarios`

```python
Scenarios(
    values, *, horizon, unit, probabilities=None, asset_ids=None,
    scenario_ids=None, origin=None, metadata=None,
)
```

`values` is a nonempty scenario × asset DataFrame, supported column mapping, dense array, or sparse matrix. `asset_ids` and `scenario_ids` are optional axis identifiers, inferred from a DataFrame or assigned positional integers otherwise. Explicit identifiers must match the supplied dimensions and labeled sets.

| Member | Type and meaning |
| --- | --- |
| `asset_ids`, `scenario_ids` | Detached pandas Indices defining axis order. |
| `values` | Detached DataFrame indexed by scenario and asset; retains sparse columns for sparse storage. |
| `probabilities` | Detached Series named `probability`, or `None`. |
| `metadata` | Detached dictionary. |
| `horizon`, `unit` | String attributes holding the declared financial horizon and unit. |
| `origin` | String attribute or `None`, holding the declared origin. |

```python
scenarios.evaluate(quantities)
scenarios.expected(quantities)
```

`quantities` is a complete finite asset vector, Series, or mapping. `evaluate` returns the linear aggregate `values @ quantities` as a scenario-indexed Series named after `unit`. `expected` requires explicit probabilities and returns a float equal to the probability-weighted aggregate. The output units are the supplied value unit multiplied by quantity units; no portfolio normalization, currency conversion, or annualization is inferred.

For portfolio scenario objectives, use `unit="simple_return"` and a horizon equal to the portfolio's horizon. Other consumers specify their own required financial coordinate. A generic `Scenarios` unit string does not automatically validate every domain-specific bound.

## `ScenarioPaths`

```python
ScenarioPaths(
    values, *, horizon, step_horizon, unit, probabilities=None,
    asset_ids=None, scenario_ids=None, step_ids=None,
    origin=None, metadata=None,
)
```

`values` is a nonempty three-dimensional scenario × step × asset array, or a DataFrame with a two-level `(scenario, period)` index and asset columns. A path table must contain every scenario/period pair exactly once and the same assets for every pair. Sparse three-dimensional storage is not a supported path input.

`horizon` describes the full path and `step_horizon` each row's observation interval. `step_ids` defines the common step order; infer it from table labels or positional integers when omitted. String/integer labels use their declared order. Actual date-like labels must be unique and strictly increasing; calendar dates have no time/timezone, while aware instants normalize to UTC. ISO strings used as step identifiers are identifiers unless the relevant operation explicitly parses them as dates.

`unit="simple_return"` additionally requires each input return to be at least `-1`. Probabilities and other arguments follow the common conventions.

| Member | Type and meaning |
| --- | --- |
| `asset_ids`, `scenario_ids`, `step_ids` | Detached pandas Indices. |
| `values` | Detached DataFrame with index names `scenario`, `period` and asset columns. |
| `probabilities` | Scenario-indexed Series named `probability`, or `None`. |
| `metadata` | Detached construction dictionary. |
| `horizon`, `step_horizon`, `unit` | String attributes holding the full horizon, observation interval, and financial unit. |
| `origin` | String attribute or `None`, holding the declared origin. |

```python
paths.evaluate(quantities)
paths.expected(quantities)
paths.aggregate(*, method)
```

`quantities` is a complete fixed instrument vector, Series, or mapping. `evaluate` returns a scenario × step DataFrame of linear instrument aggregates, with `attrs["unit"]` and `attrs["horizon"]` describing the supplied unit and step horizon. `expected` requires probabilities and returns a step-indexed Series of weighted aggregates, named after `unit`, with the step horizon in attributes. Neither operation models changing holdings or compounded portfolio wealth.

`aggregate` returns terminal `Scenarios`. Choose `method` explicitly:

| Method | Accepted unit and calculation |
| --- | --- |
| `"compound"` | `simple_return`: compound each instrument's step returns. `log_return`: sum step log returns and convert with `expm1`. Output unit is `simple_return`. Other units are rejected. |
| `"sum"` | Sum declared additive values or log returns without interest or discounting. The unit is retained. Summing simple asset returns is rejected. |

The output retains scenario and asset identifiers, probabilities, full horizon, origin, and recorded aggregation settings. This represents instrument paths under the declared operation. Dynamic portfolio wealth requires its actual holdings and cash recursion; use `TradingModel` for that decision problem.

## Historical windows

```python
ScenarioPaths.historical(
    observations, *, as_of, periods, step_horizon, horizon, unit,
    probabilities, stride=1, observed_at=None, available_at=None,
    asset_ids=None, scenario_ids=None, step_ids=None,
)
```

Returns `ScenarioPaths` made from consecutive known observations. `observations` is a one-dimensional history/Series or observation × asset array/DataFrame. A Series becomes one asset, using its name or identifier `0` when unnamed. DataFrame columns supply asset identifiers unless `asset_ids` is explicit.

| Parameter | Type and meaning |
| --- | --- |
| `as_of` | Required decision date or aware instant. |
| `periods` | Positive integer window length, excluding booleans; cannot exceed available history. |
| `step_horizon`, `horizon`, `unit` | Required nonblank descriptions of observation interval, complete path, and financial values. |
| `probabilities` | Required choice: `"equal"` for an empirical distribution, `None` for stress paths, or explicit matching probabilities. |
| `stride` | Positive integer spacing of eligible starts measured in original input rows, anchored at the first available row; default one. |
| `observed_at` | One time per row, required for arrays; pandas DatetimeIndex can supply it. |
| `available_at` | Optional publication/availability times; defaults to observation time. |
| `asset_ids`, `scenario_ids`, `step_ids` | Optional identifiers matching the resulting axes. |

Observation times must be unique and increasing; availability cannot precede observation. Rows must be both observed and available by `as_of`. Unknown rows are excluded before numeric validation. Excluded interior rows break historical windows: the constructor does not join nonconsecutive source rows into a new window. Eligible starts also respect `stride` relative to original source positions. Missing complete windows raise.

Metadata records the as-of basis, selected observation and availability times, original row positions, value fingerprint, stride, and sampled window indices. No calendar cadence, revisions, missing values, or future prices are inferred.

## Bootstrap paths

```python
ScenarioPaths.bootstrap(
    observations, *, as_of, periods, samples, step_horizon, horizon, unit,
    method, seed, block_size=None, observed_at=None, available_at=None,
    asset_ids=None, scenario_ids=None, step_ids=None,
)
```

The history and time arguments follow `historical`. `periods` and `samples` are positive integers; `seed` is a required nonnegative integer; booleans are rejected. Sampling with replacement permits paths longer than the available history. Resampling always retains the joint asset row, preserving the observed cross-asset pairing. The returned paths have equal empirical probabilities.

| `method` | Meaning and requirements |
| --- | --- |
| `"iid"` | Independently resample rows from the available empirical distribution. `block_size` must be `None`. |
| `"moving_block"` | Sample consecutive nonwrapping blocks. Requires a positive integer `block_size` no greater than available history. |
| `"circular_block"` | Sample consecutive blocks that may wrap at the history boundary. Same block-size requirement. |

Block methods require contiguous available source rows; gaps raise. The last block is truncated to the requested output length. IID sampling assumes suitable independent identically distributed observations; block methods require a suitable stationary time series. This is path generation, not a confidence interval, calibrated forecast, or decision policy.

Sampling uses NumPy's PCG64 generator. Metadata retains the method, seed, block size, generator, NumPy version, and actual sampled indices, in addition to history metadata. Preserve those records when reproducing the sample.

## Construction records

Historical and bootstrap paths return the following fields in `metadata`:

| Field | Type and meaning |
| --- | --- |
| `as_of` | ISO string for the decision date or UTC instant. |
| `time_basis` | `"calendar_date"` or `"aware_instant"`. |
| `availability` | `"observation_time"` when `available_at` was omitted, otherwise `"supplied"`. |
| `observation_times`, `available_at` | Lists of ISO strings for the selected history rows, in source order. |
| `source_positions` | List of zero-based integer positions of those rows in the original input. |
| `source_values_sha256` | SHA-256 hex string for the selected observation × asset values encoded as a C-order little-endian float64 array. |
| `sample_indices` | Scenario × step nested integer lists indexing the selected history. `source_positions[sample_indices[s][t]]` gives the original input row used at scenario `s`, step `t`. |
| `method` | `"historical"`, `"iid"`, `"moving_block"`, or `"circular_block"`. |
| `stride` | Integer start spacing; historical paths only. |
| `seed`, `block_size` | Bootstrap seed and block length as integers; `block_size=None` for IID sampling. |
| `bit_generator`, `numpy_version` | Bootstrap generator name `"PCG64"` and NumPy version string. |
| `probability_model` | `"uniform_empirical"`; bootstrap paths only. |

`aggregate` stores the preceding metadata under `source` and adds an `aggregation` dictionary. Its fields are `method`, `input_unit`, `step_horizon`, integer `periods`, and the ordered `step_ids` list. Date-like step identifiers become ISO strings; `step_time_basis` is `"calendar_date"`, `"aware_instant"`, or `None` for ordinary identifiers.

## `ScenarioTree`

```python
ScenarioTree(
    information, *, times=None, probabilities=None, scenario_ids=None,
    stage_ids=None, origin=None, metadata=None,
)
```

`information` is a nonempty scenario × stage DataFrame or two-dimensional array of integer/string node identifiers. Cases sharing a node have the same information history at that stage. All cases start at one root; a node has exactly one stage and one parent. Node identifiers cannot be reused across stages or recombining histories. Distinct scenarios may share an entire path, including their terminal node.

`scenario_ids` and `stage_ids` optionally define axis order. `times` is one strictly increasing calendar date or aware instant per stage, supplied as a sequence or a Series aligned by stage identifier. Omit `times` only when stage labels are actual date-like values. No information tree or probabilities are inferred from numerical outcomes.

| Member | Type and meaning |
| --- | --- |
| `scenario_ids`, `stage_ids`, `node_ids` | Detached pandas Indices. Nodes are ordered by stage, then first occurrence among cases. |
| `root` | Common root node identifier. |
| `information` | Detached scenario × stage node DataFrame. |
| `times` | Stage-indexed Series named `time`; aware instants use UTC. |
| `probabilities` | Case probability Series or `None`. |
| `metadata` | Detached dictionary. |
| `nodes` | Node-indexed DataFrame with `parent`, `stage`, `time`, `probability`, and `conditional_probability`. |
| `origin` | String attribute or `None`, holding the declared origin. |

Node probability is unconditional case mass passing through the node. Conditional probability is relative to its parent; the probabilistic root has conditional probability one. Conditioning on a zero-mass parent is undefined and reported as NaN. Both probability columns are NaN for probability-free stress trees. Zero-probability nodes are retained.

In `nodes`, `parent` contains a node identifier or `None` for the root, `stage` contains the stage identifier, and `time` contains pandas Timestamps. The two probability columns have float64 values.

### Tree operations

```python
tree.children(node)
tree.ancestors(node)
tree.expected(values, *, given=None)
tree.paths(values, *, horizon, step_horizon, unit, asset_ids=None)
```

`node` must be an existing valid node identifier. `children` returns its immediate child identifiers as an Index in tree order. `ancestors` returns an Index from root through the parent, excluding the node; the root has no ancestors.

For `expected`, `values` is a complete finite scalar case vector, Series, or mapping. Returns the weighted mean as a float. `given` optionally selects a known node and conditions on cases passing through it. Stress trees and zero-probability conditioning events raise instead of inventing weights.

For `paths`, `values` is a node × instrument DataFrame, dense array, or sparse matrix. `asset_ids` optionally defines instrument order, inferred from columns or positional integers otherwise. The method expands node values into a `ScenarioPaths` object over every stage, including the root. `horizon`, `step_horizon`, and `unit` are required descriptions. Shared-node cases receive identical supplied values. The caller must define root-period values and economic meaning; no return or cash-flow value is inferred. Expansion creates a dense path array.

The expanded paths' metadata contains `source` (the tree's metadata), `information` (a scenario × stage nested list of node identifiers), and `stage_times` (ISO timestamp strings in stage order).

### Policy information timing

```python
tree.validate_policy(
    decisions, *, timing="after_observation", tolerance=1e-7,
)
```

`decisions` is a `ScenarioPaths` object aligned by case/stage, or a finite scenario × stage × control array with at least one control. `timing` is `"after_observation"`, allowing decisions to depend on the current node, or `"before_observation"`, allowing only the preceding stage's information (the root at stage zero). `tolerance` is a finite nonnegative absolute scalar in decision units.

Returns a DataFrame indexed by `(stage, information_node, control)` with `minimum`, `maximum`, `violation`, and `satisfied`. Violation is the maximum minus minimum decision within the allowed information group. Attributes record `unit`, `timing`, and `tolerance`. ScenarioPaths provide the control identifiers and unit; raw arrays use positional controls and `decision_units`.

All cases participate, including stress and zero-probability cases. Decisions are not averaged or repaired. This operation checks nonanticipativity, not financial feasibility, forecasting validity, or optimality. Use the relevant financial model's evaluation for those checks.

## Errors and interchange

Invalid dimensions, incomplete path grids, incompatible labels or times, invalid probabilities, nonrecombining-tree violations, unsupported sampling choices, and unrepresentable outputs raise `TypeError` or `ValueError`. Save and restore all three scenario types with [io interchange](interchange.md); loading restores recorded values without running a sampler again.
