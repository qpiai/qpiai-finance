# Financial results and verification

Finance returns proposed decisions in the original financial coordinates. A result separates the decision, recalculated economics, constraint checks, and the solver's evidence. Check these fields before passing quantities to another system.

## `FinanceResult`

Import from `qpiai_finance.results`. Solving and recorded-result recovery create this dataclass:

```text
FinanceResult(
    status, feasible, optimality_proven, decision, objective, objective_unit,
    metrics, constraints, solver_info, provenance, tables=<factory>,
    transformations=<factory>, costs=<factory>,
)
```

The last three arguments receive independent empty dictionary/list factories: `tables={}`, `transformations=[]`, and `costs={}` in meaning, without shared mutable defaults. Direct dataclass construction assigns fields; it does not perform a solve or financial verification. Use the library's solve, recovery, or validated interchange operation to obtain their documented semantics.

| Field | Type and meaning |
| --- | --- |
| `status` | String describing termination or a Finance verification outcome. |
| `feasible` | Boolean: original financial constraints and required primary-decision reconstruction checks pass. |
| `optimality_proven` | Boolean: Finance accepts the backend's proof claim after financial feasibility, objective reconciliation, and applicable solver reconstruction checks. |
| `decision` | Dictionary of string keys to pandas Series/DataFrames in financial coordinates. |
| `objective` | Recalculated source financial objective as a float, or `None` without an incumbent or for HRP. |
| `objective_unit` | Unit string for the configured objective, or `None` where no objective exists. |
| `metrics` | Dictionary of applicable financial measurements. Keys and units follow the model reference. |
| `constraints` | DataFrame with source checks and reconstruction checks. |
| `solver_info` | Dictionary of solver route, termination, settings, proof evidence, and available diagnostics. |
| `provenance` | Dictionary of source financial inputs, input fingerprint, versions, timestamp, verification settings, and timing. |
| `tables` | Dictionary of string keys to financial/diagnostic DataFrames; independent empty default. |
| `transformations` | List of transformation dictionaries; independent empty default. |
| `costs` | Dictionary of applicable cost components; independent empty default. |

Without a primary incumbent, ordinary solves return an empty decision, metrics, and financial evaluation tables, with `objective=None` and both flags false. Route-specific structural tables, such as encoded variable mappings or HRP hierarchy information, can still be present. A candidate that fails verification can retain its evaluated decision and diagnostics; presence alone does not establish feasibility.

## Status and proof scope

Solver termination can indicate `optimal`, `completed`, `infeasible`, `unbounded`, `limit_reached`, `interrupted`, `failed`, or `unknown`, depending on the route. `failed` records a provider-reported failure; use the decision and verification flags to determine whether any candidate is usable. Preserve the backend status in `solver_info`; it can provide more detail than the common termination.

Finance additionally reports:

| Status | Meaning |
| --- | --- |
| `verification_failed` | A recovered decision failed original financial or required reconstruction checks. |
| `objective_mismatch` | A proof claim or recorded result objective disagrees with the recalculated financial objective under the applicable reconciliation rules. |
| `feasible` | Recovered/accepted feasible decision without a new global proof, or an ordinary candidate whose solver bookkeeping does not support retaining its proof claim. |
| `no_solution` | Recorded native Opt recovery has no primary candidate. |
| `no_feasible_sample` | Gate-based recovery found no financially feasible reported sample. |

`feasible` and `optimality_proven` are separate from status. A resource limit may leave a usable incumbent. Gate-based samples and HRP do not establish global optimality. Fixing a portfolio selection restricts the proof to that selection, recorded as `solver_info["optimality_scope"]="fixed_asset_selection"`. A newly loaded historical record retains recorded flags; loading does not re-prove them.

## Constraint and reconciliation tables

`constraints` has `value`, `lower`, `upper`, `violation`, and `satisfied` columns, indexed by constraint name. Some models add a `unit` column. Bounds can be infinite; rows can represent boolean or integer/lot residual checks as well as ordinary financial limits. Consult the domain reference for each row's units.

`tolerance` is an absolute Finance check tolerance, applied in those row units. Numeric objective reconciliation uses absolute `tolerance` and relative `1e-7`. A floating-point tolerance does not establish ledger-exact payment or accounting finality.

Where applicable, `tables["solver_reconciliation"]` records derived solver bookkeeping separately. It has `residual`, `unit`, and `within_tolerance` columns indexed by reconciliation name; each residual is compared with the solve's Finance tolerance. `solver_info["solver_reconciled"]` summarizes these checks. Original financial feasibility and solver bookkeeping are not interchangeable: inconsistent derived values can remove a proof without invalidating an independently feasible primary decision.

## Decision properties

The following properties return the indicated decision entry, or `None` when absent. Except `cash_after`, each is a financial Series/DataFrame defined by its model; axis order and units are documented on that model's page.

| Property | Decision key or source | Meaning |
| --- | --- | --- |
| `weights` | `weights` | Portfolio weights on the declared investment basis. |
| `holdings` | `holdings` | Asset quantities. |
| `trades` | `trades` | Signed asset trade quantities. |
| `cash_after` | `metrics["cash_after"]` | Cash amount as a float, when supplied by the model's metrics. |
| `post_trade_weights` | `post_trade_weights` | Asset weights relative to positive post-trade `portfolio_value`, before deducting unpaid deferred tax; see [portfolio value conventions](portfolio.md#weight-and-cash-conventions). |
| `tax_lot_sales` | `tax_lot_sales` | Acquisition-lot disposal quantities. |
| `draws` | `draws` | Funding draw quantities. |
| `transfers` | `transfers` | Explicit account transfer decisions. |
| `investments` | `investments` | Purchased investment-opportunity quantities. |
| `cash_balances` | `cash_balances` | Dated/node/account cash balances. |
| `hedges` | `hedges` | Hedge quantities. |
| `positions` | `positions` | Resulting signed positions. |
| `risk_exposures` | `risk_exposures` | Recomputed risk exposures. |
| `allocations` | `allocations` | Final credit facility amounts. |
| `allocation_changes` | `allocation_changes` | Changes from the supplied existing credit book. |
| `assignments` | `assignments` | Collateral quantities by permitted pledge. |
| `selections` | `selections` | Reinsurance contract/program indicators. |
| `settlement_schedule` | `schedule` | Payment-to-slot assignment; `None` values identify unsettled payments. |
| `prefunding` | `prefunding` | Outside prefunding by settlement account. |
| `peak_credit` | `peak_credit` | Maximum actual settlement overdraft per account. |
| `executions` | `executions` | Signed execution quantities by opportunity. |
| `remaining_orders` | `remaining_orders` | Signed target quantities remaining after each execution slot. |
| `unfilled` | `unfilled` | Nonnegative residual order quantities at the horizon. |

Additional domain entries are available through `decision`, metrics, costs, and tables. Their absence is not represented by fabricated zero values.

## Solver and input records

`solver_info` retains the provider, solver/method, problem class, execution mode, termination, solution availability, guarantee, source objective, and settings where available. Native Opt records include solver/compute times and platform problem/job identifiers. External routes retain their supported versions, requested options, recorded settings, iteration statistics, duals, bounds, or gaps; unavailable evidence remains absent or `None`. The [solver option reference](solver-options.md) defines which settings each interface records.

The common solver fields are:

| Field | Type and meaning |
| --- | --- |
| `problem_class` | String identifying the executed mathematical or construction class; see [validated classes](solving.md#validate). |
| `execution_mode` | `"local"` or `"platform"`, identifying where execution actually ran. Opt's separate `requested_execution_mode` can be `"auto"`. |
| `provider` | String identifying the provider or integration that executed the computation. |
| `solver`, `method` | Solver and computational-method strings, or `None` when unidentified. HRP records its construction method with `solver=None`. |
| `termination` | Common termination string from the status list above. The separate backend `status` can use provider-specific names. |
| `has_usable_solution` | Boolean provider/recovery assessment of candidate availability. |
| `solution_feasible` | Boolean provider/recovery assessment, or `None` when not established at that layer. |
| `optimality_proven` | Boolean provider proof assessment, or `None` when unknown. Finance's accepted proof is the top-level result field. |
| `guarantee` | String from the guarantee table below. |
| `source_objective` | Float objective in source optimization coordinates, or `None` when unavailable. |
| `transformed` | Boolean indicating compilation or conversion, or `None` when unknown. |
| `settings` | Dictionary of setting-name strings to recorded scalar values (`bool`, `int`, `float`, or `str`). Route-specific recording limits are defined in the solver reference. |

| `guarantee` | Meaning of the recorded evidence |
| --- | --- |
| `"global_optimum"` | Provider claims a proven global optimum. |
| `"best_found"` | Best available sampled or heuristic candidate; no global proof. |
| `"best_bound"` | A bound is the strongest reported guarantee. |
| `"feasible_only"` | A feasible candidate is established without an optimum claim. |
| `"infeasibility_proven"` | Provider claims the executed problem is infeasible. |
| `"unboundedness_proven"` | Provider claims the executed objective is unbounded. |
| `"none"` | No guarantee is established by that record. |
| `"unknown"` | The guarantee could not be determined. |

`solver_info["finance_objective"]` is the recalculated financial objective. `objective_reconciled` reports the comparison with the backend's source-coordinate objective. Conditional scopes, numerical scaling, risk-budget refinement, and quantum diagnostics remain explicitly recorded. The domain and [solver references](solving.md) define route-specific fields.

Nested solver fields describe the backend's evidence. Its `optimality_proven`, `has_usable_solution`, or `guarantee` can retain a claim that Finance's subsequent financial checks reject. The top-level `feasible` and `optimality_proven` fields report Finance's accepted conclusions. `objective_reconciled` is a boolean when a financial objective was evaluated and `None` when that comparison is inapplicable.

`provenance` includes `inputs`, their `input_sha256`, UTC `created_at`, relevant package `versions`, `verification_tolerance`, `probability_sum_tolerance`, and `timing_s`. Ordinary timing records measure `build`, `solve`, and `postprocess` in seconds. Recorded recovery uses its own recovery time and does not invent a new solve duration. Inputs and hashes support consistency checks; they do not authenticate a remote solver or prove historical model identity. Records can contain complete confidential financial inputs.

`transformations` records applicable encodings, fixed-selection scope, risk-budget normalization, numerical unit scaling, or integer reconstruction. Use these records when interpreting a result or restoring a separately executed model.

## Numeric reports

```python
result.to_dict()
result.to_json()
```

`to_dict` returns a numeric report with `schema_version=1` and the result fields. Tables become objects containing `index`, `columns`, and row-wise `data`; Series use a one-column table form. Dates become ISO strings, arrays become lists, and sparse matrices become COO records. Mapping keys become strings; collisions raise `ValueError`. Nonfinite diagnostic values become JSON null, including unbounded sides and undefined metrics. `to_json` returns the corresponding strict JSON string.

This report is not reversible typed interchange. Use `qpiai_finance.io` to preserve supported labeled structures, diagnostic bounds, and result metadata.

## Re-evaluate a financial decision

```python
result.evaluate(model, *, tolerance=1e-7)
```

`model` must be an exact supported source Finance model type matching the recorded financial model. `tolerance` is a finite nonnegative real scalar. Missing primary decisions raise. The operation copies the source model, recomputes financial evaluation, and leaves both inputs unchanged. It requires no authentication, execution, or new optimization.

The evaluation uses primary decisions rather than stored metric claims:

| Model | Replayed inputs |
| --- | --- |
| Portfolio | Weights and configured tax-lot disposals. |
| Funding | Draws, transfers, and configured investments. |
| Liability matching | Holdings and recorded `metrics["initial_capital"]`. |
| Hedge | Hedge quantities. |
| Credit | Final allocations. |
| Collateral | Assignments. |
| Reinsurance | Selection indicators. |
| Settlement | Schedule and prefunding. |
| Execution | Execution quantities. |
| Trading | Trades and configured funding draws. |

Returns the model's fresh evaluation dictionary plus `recorded_objective`, `objective_matches`, and `input_fingerprint_matches`. Objective comparison uses absolute tolerance plus relative `1e-7`. A matching fingerprint compares the supplied source specification with the recorded input hash; it does not authenticate historical evidence. Replay does not check every backend auxiliary or establish a new optimum.

## Recover a recorded Opt result

```python
from_opt(
    result, *, model, opt_model=None, objective_scaling=None, tolerance=1e-7,
)
```

Import `from_opt` from `qpiai_finance.results`. It returns a `FinanceResult` without authentication, solve, or submission.

| Parameter | Type and contract |
| --- | --- |
| `result` | Typed native Opt LP/MILP/QP, QUBO/HUBO/Ising, or supported `QuantumResult`. Restore JSON with its original Opt result class first. |
| `model` | Original supported source Finance model, or its retained `PortfolioEncoding` for direct financial binary compilation. |
| `opt_model` | Actual Opt `Model` retaining its explicit polynomial compilation and decoder, required for transformed polynomial/gate recovery outside a `PortfolioEncoding`. Rejected for ordinary LP/MILP/QP records. |
| `objective_scaling` | Optional retained exact power-of-two scaling metadata for conditioned raw LP/MILP records. Rejected for QP or polynomial/gate results. |
| `tolerance` | Finite nonnegative verification scalar, default `1e-7`. |

For native LP/MILP/QP, class, objective sense, and complete variable names must match the restored financial formulation. For other transformed results, the retained Opt decoder checks the sample-to-source mapping; finite encoding bounds and any explicit continuous grid remain part of Opt's compilation contract.

With a `PortfolioEncoding`, recovery checks encoded energy and product auxiliaries as described in [quantum optimization](quantum.md). General `opt_model` recovery checks decoded assignments, retained Opt source constraints, original Finance constraints, and source objectives. It does not independently verify encoded energy or every penalty/slack auxiliary; its verification scope is recorded in `solver_info`.

For objective scaling, retain the record from Finance inspection or a Finance result rather than deriving a scale from observed costs. The record requires `base=2` and a Python integer exponent in `[0, 1073]`. Accepted additional fields are `type="objective_scaling"`, boolean `range_limited`, `exact`, and `source_units_restored`, plus a `provider_values` mapping. `exact=False`, unknown fields, invalid flag types, and incompatible source classes are rejected.

Recorded native recovery always sets `optimality_proven=False`. Matching coordinates and objective do not establish which feasible set the recorded solver optimized. Historical solver evidence remains under `solver_info["recorded_solver"]`. Results report feasible-only or no guarantee, with `feasible`, `verification_failed`, `objective_mismatch`, or `no_solution` status as applicable. Gate-based recovery selects the best freshly feasible reported financial candidate and makes no global proof claim. Direct `PortfolioEncoding` recovery distinguishes measured and declared residual candidates as described in its [candidate table](quantum.md#candidate-table). General compiled-model recovery distinguishes measured candidates and the provider's reported primary candidate.

### Compiled-model recovery diagnostics

Recovery through a retained `opt_model` adds the following `solver_info` fields:

| Field | Type and meaning |
| --- | --- |
| `financial_problem_class` | String class of the source financial Opt formulation. |
| `verification_scope` | String `"decoded_source_decision_and_objective"`. |
| `sample_decoding_verified` | Boolean; at least one sample was decoded and checked. |
| `encoded_energy_verified` | `False`; recovery does not recalculate the encoded energy. |
| `encoding_auxiliaries_verified` | `False`; recovery does not independently check encoding penalty/slack auxiliaries. |
| `selected_bitstring` | MSB-first string identifying the selected decoded candidate; absent without a selection. |

For gate records, `tables["quantum_samples"]` has a separate schema from direct portfolio compilation:

| Column | Type and meaning |
| --- | --- |
| `count`, `probability` | Positive integer measured count and float candidate-distribution probability; missing for an unmeasured reported primary candidate. |
| `reported_count` | Integer from the provider's reported-count dictionary, or zero if absent. |
| `reported_objective` | Float source objective checked against the retained Opt model. |
| `objective` | Float recalculated Finance objective. A changed Opt objective can differ from Finance's original objective. |
| `feasible` | Boolean conjunction of Finance feasibility and retained Opt constraint feasibility. |
| `financial_feasible`, `opt_model_feasible` | Boolean component feasibility checks. |
| `reported_feasible` | Provider's candidate feasibility flag, or missing for an unmeasured primary candidate; retained as reported evidence. |
| `energy` | Reported encoded/internal energy for a measured candidate, or missing for an unmeasured primary candidate. This value is unverified. |
| `maximum_violation` | Float maximum residual in the Finance constraint table. |
| `reported_primary` | Boolean marking the provider's primary solution. |

The index is the MSB-first `bitstring`. Missing values can promote integer count columns to floating dtype. An empty candidate set produces an empty DataFrame without these columns. Attributes contain `encoded_energy_verified=False`, `encoding_auxiliaries_verified=False`, and the provider's `probability_scope`. The full provider diagnostics remain in `solver_info["quantum"]`; `candidate_observations` is the total measured count. `tables["quantum_history"]` contains `training_objective`, indexed by optimizer `evaluation`.

## Interchange and plotting

Use [interchange](interchange.md) for supported result and frontier round trips, format validation, and file/stream operations. Use [plotting](plotting.md) to render the corresponding financial tables. Plotting does not replace the result acceptance checks above.
