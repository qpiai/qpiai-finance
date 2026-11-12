# Model, scenario, and result interchange

Use `qpiai_finance.io` to preserve supported financial models, scenarios, and result records as versioned JSON. Interchange reads and writes data. It does not authenticate, run a solver, submit a job, or restore an executable session.

## Python API

```python
to_dict(value)
from_dict(document)
dumps(value)
loads(text)
dump(value, fp)
load(fp)
```

| Function | Inputs | Return |
| --- | --- | --- |
| `to_dict` | Supported exact Finance model/result/scenario instance. | Detached JSON-compatible dictionary with format and schema version. |
| `from_dict` | Dictionary in a supported interchange format. | Restored model, scenario object, `FinanceResult`, or `FrontierResult`. |
| `dumps` | Same objects as `to_dict`. | Strict JSON string with compact separators. |
| `loads` | JSON `str`, `bytes`, or `bytearray` accepted by Python's JSON parser. | Restored supported object. |
| `dump` | Supported object and writable text stream `fp`. | `None`; writes the JSON string to the stream. |
| `load` | Readable text stream `fp` whose `.read()` returns JSON text. | Restored supported object. |

Open files with UTF-8 encoding. `dump` finishes serialization before calling the stream's `write`, so an invalid source object does not write a partial serialized document. Stream and filesystem failures still follow the supplied stream's behavior.

```python
from qpiai_finance import io

with open("portfolio.json", "w", encoding="utf-8") as stream:
    io.dump(portfolio, stream)

with open("portfolio.json", encoding="utf-8") as stream:
    restored_portfolio = io.load(stream)
```

Here `portfolio` is a configured supported model. The restored object has the recorded financial settings; it is not a solved or approved financial decision.

## Supported objects and formats

All formats below require `schema_version` to be the Python/JSON integer `1`, excluding booleans. Unknown versions are rejected.

| Format | Supported value | Top-level fields |
| --- | --- | --- |
| `qpiai-finance-model` | `PortfolioModel`, `TradingModel`, `ExecutionModel`, `FundingModel`, `LiabilityMatchingModel`, `HedgeModel`, `CreditAllocationModel`, `CollateralAllocationModel`, `ReinsuranceModel`, `SettlementModel` | `format`, `schema_version`, `model`, `inputs`, `configuration`. |
| `qpiai-finance-scenarios` | `Scenarios`, `ScenarioPaths`, `ScenarioTree` | `format`, `schema_version`, `data`. |
| `qpiai-finance-result` | `FinanceResult` | `format`, `schema_version`, and every dataclass field listed in [results](results.md). |
| `qpiai-finance-frontier` | `FrontierResult` | `format`, `schema_version`, `targets`, `horizon`, `results`. |

Subclasses and custom extensions are rejected. `FactorRisk` can appear as an embedded model input; it is not a standalone top-level `io.to_dict` value. `PortfolioEncoding`, Opt/CVXPY/SCIP models, gate algorithms, clients, callbacks, circuits, credentials, and executable job objects are not supported top-level interchange objects.

## Financial model records

`model` identifies the supported Finance class. `inputs` maps constructor argument names to encoded values. `configuration` is a list of objects with exactly `method` and `arguments`, describing the allowed public modeling operations required to reconstruct the financial settings.

Loading decodes the inputs, constructs the model through its validated public constructor, then applies the supported configuration methods. Unknown class names, methods, fields, and malformed arguments fail explicitly; no partially restored model is returned. The record preserves the active objective, supplied financial assumptions, hard limits, labels, and supported sparse/factor representations. It does not record arbitrary Python mutations or added constraints on detached Opt/CVXPY exports.

Configuration steps are the financial setters, objective selectors, and activation/completion methods in the corresponding [model API reference](public-api.md). Evaluation, exports, and execution are excluded. The sequence reconstructs the current specification and can differ from the application's original call history.

The output is a financial specification, not a solver checkpoint. Reinspect or validate the restored model before selecting a route. Package versions and execution settings needed for reproducibility should be retained with the application's records; loading does not guess an older implementation's semantics.

## Encoded financial values

JSON scalars and lists are supplemented with explicit typed records. Use `to_dict` to produce them rather than manually converting pandas objects to untyped lists.

| Typed record | Meaning |
| --- | --- |
| `integer` | Canonical decimal text preserves integer identifiers beyond JSON consumers' exact binary64 integer range. |
| `timestamp` | Canonical ISO timestamp representing a validated date/time value. |
| `index` | Ordered labels and index name. |
| `table` | Encoded row/column indices and values stored by column. |
| `array` | Numeric values with declared shape. |
| `sparse` | Two-dimensional shape, row/column coordinates, and numeric values. |
| `mapping` | Explicit key/value pairs, preserving integer versus string keys. |
| `tuple` | Ordered tuple items, distinct from an ordinary JSON list. |
| `factor_risk` | Validated factor exposures, factor covariance, specific variances, and identifiers. |
| `scenarios`, `scenario_paths`, `scenario_tree` | Constructor arguments preserving their values, identifiers, probability/information semantics, origin, and declared metadata. |

Model input arrays remain real and finite. Mapping keys in ordinary financial input records are strings or integers. Sparse storage remains sparse; the loaded object's normal constructor applies its supported representation checks. Sampling metadata is restored as data, without resampling.

## Result and frontier records

Result interchange preserves labeled Series/DataFrames, supported index structures, names, attributes, and diagnostic values. Additional typed records preserve datetime indices, MultiIndex levels/codes/names, date/datetime values, missing `NA`/`NaT`, and tagged `nan`, `+inf`, or `-inf` diagnostics. Nonfinite values do not appear as invalid bare JSON numbers.

Supported result storage describes boolean, signed/unsigned integer, floating, object, and datetime columns. Numeric widths are restored to the supported canonical representation rather than promising every original NumPy or extension dtype. Arbitrary custom objects, unsupported result column dtypes, NumPy timedelta scalars, cyclic data, and executable values are not interchange data. A diagnostic tuple or date key can be retained where supported; ordinary model identifier rules remain stricter.

| Recorded storage kind | Restored dtype and allowed values |
| --- | --- |
| `boolean` | NumPy/pandas `bool`; Boolean values only. |
| `integer` | `int64`; integers in `[-2**63, 2**63-1]`, excluding booleans. |
| `unsigned_integer` | `uint64`; integers in `[0, 2**64-1]`, excluding booleans. |
| `float` | `float64`; real numbers and tagged nonfinite diagnostics. |
| `object` | pandas `object`; supported encoded diagnostic values. Nullable Boolean/integer/float extension columns are stored this way, preserving missing markers without restoring the extension dtype. |
| `datetime` | pandas datetime column with the recorded timezone, or naive when its `timezone` is `None`; timestamp values and `NaT`. |

Diagnostic array and sparse-value storage uses the first four numeric kinds. Ordinary model arrays restore as finite `float64`; sparse inputs restore as COO matrices before the receiving model's constructor chooses its supported representation.

Result restoration checks field structure and consistency. Decisions must be labeled Series/DataFrames with unique axes. Constraints require `value`, `lower`, `upper`, `violation`, and boolean `satisfied` columns. A recorded feasible flag requires a decision and satisfied constraints. A recorded proof additionally requires feasibility, a financial objective, `solver_info["objective_reconciled"] is True`, `solver_info["optimality_proven"] is True`, and no explicit `solver_reconciled=False`. Missing solver-reconciliation evidence is permitted by this structural check. A record without a decision must have `objective=None`. These checks validate the record's internal structure; they do not repeat the financial calculation or authenticate the solver's claims.

A frontier requires a target Series with valid identifiers, a matching tuple of result records, a nonblank horizon, and consistent portfolio horizons. Each effective return target must retain the requested minimum.

After restoration, use `result.evaluate(trusted_model)` for fresh primary-decision checks. Use `results.from_opt` when the input is a retained typed Opt result rather than a Finance interchange document. Neither loading nor replay establishes a new optimum. See [results and recovery](results.md).

## Numeric reports versus interchange

`FinanceResult.to_dict()`/`.to_json()` and `FrontierResult.to_dict()`/`.to_json()` produce numeric reports. They are intended for reporting and do not use the reversible `format` records above. Reports convert undefined/unbounded diagnostics to null and do not preserve all pandas structure or mapping key types.

Use `io.to_dict(result)` or `io.dumps(result)` when the record must round-trip. Passing a numeric report to `io.from_dict` or `io.loads` does not convert it into typed result interchange.

## Errors and data handling

`loads` rejects duplicate JSON fields and bare nonfinite JSON numbers. Loading rejects unknown types, extra or missing fields, invalid dimensions, out-of-range sparse/index coordinates, duplicate mapping keys, and incompatible storage declarations. Python JSON parsing and stream errors propagate; structural and financial validation errors use `ValueError` or `TypeError`.

Interchange contains financial data and recorded job identifiers. Keep it within the application's access and retention controls. Clients and secrets are not serialized by the supported model API; do not insert credentials into otherwise permitted metadata dictionaries.
