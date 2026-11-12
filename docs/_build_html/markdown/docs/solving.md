# Solvers, execution, and verification

Construct a financial model, inspect its mathematical representation, select execution, and check the resulting financial decision. Finance's `solve` returns financial coordinates and recalculates source constraints and economics. It uses QpiAI Opt, Clarabel, SCIP, or the configured portfolio construction method according to the model and selected solver.

## Authentication and execution modes

Every Finance solve requires `client=Client(api_key=...)` from `qpiai_opt.opt_solvers`. This includes Clarabel, SCIP, HRP, and local gate-based optimization. Key verification requires connectivity. Local execution refers to where computation runs, not disconnected authentication. Register for an Opt key at [QpiAI Opt](https://opt.qpiai.tech/) and load it from the application's secret store.

Gate-based quantum execution additionally requires active QCloud authentication using `QpiAIQuantumAuth` from `qpiai_opt.quantum`. Obtain its key from [QpiAI QCloud](https://qcloud.qpiai.tech/).

The supported execution choices are:

| Route | Modes | Behavior |
| --- | --- | --- |
| QpiAI Opt without a gate algorithm | `local`, `auto`, `platform` | `local` is the default. `auto` follows Opt's local-first routing. Paid fallback requires `allow_platform=True`. `platform` explicitly selects platform execution. |
| Gate-based quantum optimization | `local`, `platform` | Requires an explicit QUBO/Ising `PortfolioEncoding` and an Opt algorithm. `auto` and `allow_platform=True` are rejected. |
| Clarabel, SCIP, HRP | `local` | Other modes and `allow_platform=True` are rejected. |

Platform execution can consume credits. QpiAI Opt's current platform route supports its documented MILP and binary-polynomial classes; QP is local-only. An authentication, validation, or transport failure does not authorize a different route or a paid retry. See [Opt routing](https://github.com/qpiai/qpiai-opt/blob/main/docs/local-solving.md) for native capacity limits, provider settings, and fallback behavior.

## Default solver selection

Finance uses the configured financial formulation to select a default. Explicit selection does not request a fallback search among unrelated providers.

| Model structure | Default `solver` |
| --- | --- |
| Supported Opt LP, MILP, or continuous convex QP | `"qpiai"` |
| Supported continuous conic formulation | `"clarabel"` |
| Supported external mixed-integer formulation | `"scip"` |
| Portfolio risk budgeting | `"clarabel"` |
| Portfolio hierarchical risk parity | `"hrp"` |
| Investment planning requiring the exact nonlinear cash-cost formulation | `"scip"` |
| `PortfolioEncoding` or portfolio moment utility | `"qpiai"` |

The accepted solver names are exactly `"qpiai"`, `"clarabel"`, `"scip"`, and `"hrp"`. Select external names in lowercase. Clarabel does not support integer decisions. Portfolio risk budgeting requires logarithmic cones and rejects SCIP. HRP requires the portfolio's `hierarchical_risk_parity` method. The exact nonlinear investment formulation accepts only SCIP. A compiled portfolio encoding accepts only the QpiAI solver.

Inspection and the individual model references identify which financial constraints are represented in a solver and which construction methods check them after allocation. In particular, risk budgeting constructs and normalizes risk positions; requested financial limits are checked on the normalized result, not imposed in that construction program. HRP is a portfolio construction heuristic.

## Common Python operations

Import the following functions from `qpiai_finance`.

### `validate`

```python
validate(model)
```

`model` is a supported Finance model or `PortfolioEncoding`. Returns the mathematical class of its validated representation as a string:

| Class | Meaning |
| --- | --- |
| `LP`, `MILP` | Linear or mixed-integer linear program. |
| `QP`, `MIQP` | Continuous or mixed-integer quadratic-objective program. |
| `QCQP`, `MIQCP` | Continuous or mixed-integer quadratically constrained program, including an exact quadratic cash-cost graph where required. |
| `SOCP`, `MISOCP` | Continuous or mixed-integer second-order-cone formulation, including supported power-impact costs. |
| `CONIC` | Portfolio logarithmic risk-budget construction. |
| `NLP`, `MINLP` | Continuous or mixed-integer nonlinear investment formulation with an exact power-impact cash-cost graph. |
| `HEURISTIC` | Hierarchical risk parity construction. |
| `QUBO`, `HUBO`, `ISING` | The selected binary/spin polynomial representation. |

Validation compiles or checks the applicable representation. It requires no credentials and does not solve or prove financial feasibility. Invalid types, financial settings, unsupported combinations, or compilation errors raise rather than returning a false validity flag.

### `inspect`

```python
inspect(model, *, algorithm=None)
```

Accepts the same models as `validate`. Returns a dictionary with `financial_model` and `optimization` records. `financial_model` contains the actual financial inputs and settings; handle it with the same confidentiality as the source data. `optimization` describes the representation, class, validity, and relevant size or route information.

The optimization record has the following route-specific fields. Counts are integers; flags are booleans.

| Route | Fields and meaning |
| --- | --- |
| Native Opt | `problem_class`: validated class string; `representation`: normalized Python representation's class name; `valid=True`; `metrics`: size/work dictionary described below. Ordinary financial models also include `objective_scaling`, either `None` or the record below. |
| CVXPY | `problem_class`: financial class string; `representation="CVXPY"`; `valid`: the compiled problem's `is_dcp()` result; `default_solver`: `"clarabel"` or `"scip"`; `variables`: scalar optimization-variable count; `native_opt_supported=False`; `financial_limits_in_solver`: false for risk-budget construction, true otherwise; `financial_limits_checked_on_result=True`. A scaled formulation additionally includes `numerical_units`. |
| Direct SCIP investment formulation | `problem_class`: financial class string; `representation="SCIP"`; `valid=True`; `default_solver="scip"`; `variables`: exported decision-expression count; `constraints`: native constraint count; `convex`: true only for a continuous formulation with monotone cash-cost reconstruction; `cash_reconstruction`: `"monotone_cost_epigraph"` or `"exact_cost_graph"`; `native_opt_supported=False`; both `financial_limits_in_solver` and `financial_limits_checked_on_result` are true. |
| HRP | `problem_class="HEURISTIC"`; `valid=True`; `method="hierarchical-risk-parity"`; `default_solver="hrp"`; `native_opt_supported=False`; `assets`: asset count. |

Native Opt `metrics` contains:

| Class | Metric names and meaning |
| --- | --- |
| LP/MILP | `variables`, `constraints`, `nonzeros`: column count, row count, and constraint-matrix nonzeros. |
| QP | The LP metrics plus `hessian_nonzeros`: objective-Hessian nonzeros. |
| QUBO/HUBO/Ising | `variables`: declared variable count; `active_variables`: variables in nonconstant terms; `terms`: retained polynomial-term count; `degree`: maximum term degree; `exact_enumeration_work`: native enumeration work estimate. `annealing_work` is also present when the exact-enumeration size/work cutoffs are exceeded, using stored or default read/sweep settings. The [local option reference](solver-options.md#opt-local-options) defines those formulas and limits. |

For small LP/MILP objectives, `objective_scaling` describes multiplication of the entire objective by `2**exponent`:

| Field | Type and meaning |
| --- | --- |
| `type`, `base` | String `"objective_scaling"` and integer `2`. |
| `exponent` | Nonnegative integer power; zero is possible when numerical headroom prevents scaling. |
| `range_limited` | Boolean: the provider's finite coefficient range prevents the desired scaling. |
| `exact`, `source_units_restored` | Both true: scaling preserves the objective, and result diagnostics are reported in source units. Inspection itself does not execute or restore a result. |

The CVXPY `numerical_units` dictionary records reversible changes of financial units:

| Field | Type and meaning |
| --- | --- |
| `type`, `base` | String `"financial_units"` and integer `2`. |
| `applied`, `range_limited` | Booleans indicating conditioned compilation and a numerical-range limit on conditioning. |
| `objective_exponent` | Integer `e` with source objective equal to numerical objective times `2**e`. |
| `maximum_coordinate_exponent` | Integer maximum across variable, row, and objective exponents; used to prepare omitted Clarabel tolerances. |
| `variable_exponents` | Dictionary from exported variable names to integer `e`, with source coordinate equal to numerical coordinate times `2**e`. |
| `row_exponents` | Dictionary from source linear row names to integer scaling exponents. Numerical rows divide their source expressions and bounds by `2**e`. |
| `constraint_exponents` | List in compiled CVXPY constraint order; each entry is an integer or list of integers. Multiply each numerical dual by its corresponding `2**e` to restore source units. |
| `integer_domains_unchanged` | True; integer coordinates retain their original units. |
| `fixed_zero_coordinates` | List of exported variable names represented by zero constants. |
| `order_total_constraints` | List of source row names identifying order-total constraints. |

`algorithm` must be an authoritative Opt gate-based algorithm and is accepted only with `PortfolioEncoding`. Encoded inspection adds top-level `transformations` and a pandas `variable_mapping` DataFrame, as defined in the [encoding reference](quantum.md). Portfolio moment utility is inspected through its default HUBO encoding and returns those fields too. Algorithm inspection also checks compatibility and adds the Opt circuit/resource report as `optimization["quantum"]`. No circuits execute, no credential is verified, and no job is submitted. Inspection is not a feasibility proof or a guarantee that a particular solver can finish within a resource budget.

### `solve`

```python
solve(
    model, *, client=None, mode="local", solver=None, algorithm=None,
    execution=None, allow_platform=False, tolerance=1e-7, **options,
)
```

| Parameter | Type and meaning |
| --- | --- |
| `model` | `PortfolioModel`, `TradingModel`, `ExecutionModel`, `HedgeModel`, `CreditAllocationModel`, `FundingModel`, `LiabilityMatchingModel`, `ReinsuranceModel`, `CollateralAllocationModel`, `SettlementModel`, or `PortfolioEncoding`. Arbitrary Opt or CVXPY models are not Finance model inputs. |
| `client` | Required authenticated Opt `Client` for execution; the signature's `None` default raises when no client is supplied. |
| `mode` | `"local"`, `"auto"`, or `"platform"`; ordinary Finance model routing accepts case-insensitive mode spelling. The route restrictions above apply. |
| `solver` | Supported lowercase name or `None` for the model's default. |
| `algorithm` | Optional Opt `QAOA`, `VQE`, `SamplingVQE`, `RecursiveQAOA`, or `ADAPTQAOA` instance. Requires explicit eligible `PortfolioEncoding`. |
| `execution` | Opt `QuantumRun` for a gate algorithm; `None` uses its default. Rejected without an algorithm. |
| `allow_platform` | Python boolean; default `False`. Permits Opt's automatic paid fallback only in its supported route. |
| `tolerance` | Finite nonnegative real scalar; absolute Finance verification tolerance in each constraint row's source units. Default `1e-7`. |
| `**options` | Settings for the selected solver route, described below. |

Returns a `FinanceResult`. Ordinary solves copy the financial model before compilation and retain its input specification in the result. A `PortfolioEncoding` retains the financial snapshot created during compilation. Changing a source model after creating an encoding does not change that encoding.

`tolerance` governs Finance's constraint verification. It does not relax the financial model or directly set every backend feasibility tolerance. Objective reconciliation uses this absolute tolerance plus relative `1e-7`. Solver-specific settings remain separate; inspect the effective settings in `result.solver_info`.

Portfolio moment utility uses native HUBO compilation automatically when passed directly to `solve`. Select another representation explicitly with `compile_portfolio`.

## Solver options

### QpiAI Opt

Finance forwards supported `**options` to `qpiai_opt.opt_solvers.solve`, together with execution mode and fallback permission. The [solver option reference](solver-options.md) lists every supported local option, platform lifecycle field, LP/MILP configuration field, and HUBO control with types, allowed values, defaults, and meanings. An option for another mathematical class is not interchangeable.

For LP/MILP objectives with small coefficients, Finance can multiply the whole objective by a positive power of two for numerical conditioning. It restores objectives, bounds, dual values, reduced costs, and applicable objective-unit settings to source units. This preserves the financial objective and feasible set. The inspection report and result retain the scaling record. Save that record when recovering a separately submitted Opt job result.

### Clarabel through CVXPY

Options are passed to `cvxpy.Problem.solve(solver=CLARABEL, **options)`. The [complete Clarabel settings table](solver-options.md#clarabel-settings) defines all fields and defaults; [CVXPY controls](solver-options.md#cvxpy-controls) defines canonicalization, output, and warm-start options.

Finance rejects route overrides named `solver`, `solver_path`, `gp`, `qcp`, or `requires_grad`. When a formulation uses recorded numerical unit scaling, Finance converts applicable absolute-gap settings and dual units; the result records requested and numerical options. An incompatible explicit solver raises.

### SCIP

Use `scip_params` for native SCIP parameter names and `verbose` for output:

```python
result = solve(
    model,
    client=client,
    solver="scip",
    scip_params={"limits/time": 120.0, "limits/gap": 0.001},
    verbose=False,
)
```

The model must support SCIP. CVXPY-backed SCIP uses CVXPY's solver interface. Direct SCIP execution for exact nonlinear investment models accepts only `scip_params` and `verbose`. `scip_params` must be a dictionary with string keys; `verbose` must be a Python boolean. The [SCIP controls](solver-options.md#scip-controls) and [full parameter catalogue](scip-parameters.md) define fields, native defaults, ranges, and meanings. Direct execution starts with `numerics/feastol=1e-9` unless explicitly overridden, adjusts `numerics/epsilon` consistently when needed, and records effective settings. Native bounds and gaps are reported when available.

### HRP and gate algorithms

HRP accepts no solve options; configure linkage through the portfolio method. Gate-based solve options belong to the algorithm object and `QuantumRun`, rather than arbitrary `**options`. See [quantum-inspired and gate-based quantum optimization](quantum.md) for compatibility, controls, samples, and recovery.

## Result acceptance

Use `result.feasible` to determine whether the recovered primary decision satisfies Finance's original constraints. Use `result.optimality_proven` independently when the application requires an optimum. A limit termination can still have a feasible incumbent; inspect both the status and decision evidence.

Without an incumbent, ordinary financial results contain no decision, objective, or financial evaluation tables. A recovered candidate that fails original financial checks has `status="verification_failed"`. For a feasible candidate, if a backend claims an optimum but its objective disagrees with the recalculated financial objective, the result has `status="objective_mismatch"` and no proven optimum. Inconsistent solver reconstruction also removes the proof claim.

Full fields, domain tables, proof scope, interchange, and replay are described in [results and verification](results.md).

## Failures and recovery

| Condition | Action |
| --- | --- |
| Invalid data, labels, options, or unsupported formulation | Correct the input or choose a supported explicit representation. Do not silently discard a financial rule. |
| Authentication failure | Correct the credential or connectivity. Do not change the solver or authorize remote execution implicitly. |
| Opt local limit exceeded | Inspect the reported capacity and choose a supported smaller formulation or an explicitly authorized route. |
| Solver infeasibility | Inspect the model and constraints; a structural validation result does not imply feasibility. |
| Limit with incumbent | Check source feasibility, objective, and available bound/gap against application requirements. |
| Ambiguous platform submission | Reconcile existing jobs using Opt's job API before retrying. A timeout does not establish that no job was created. |
| Recorded result available | Retain the original model and compilation metadata; recover with `results.from_opt` or `PortfolioEncoding.decode_result`. |

Finance has no separate nonblocking job scheduler. For explicit asynchronous Opt work, use [Opt's submission and retrieval API](https://github.com/qpiai/qpiai-opt/blob/main/automation.md#nonblocking-platform-lifecycle), retain the exact submitted representation and metadata, and perform Finance result recovery after retrieval.
