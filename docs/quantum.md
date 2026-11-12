# Quantum-inspired and gate-based optimization

Start with a financial objective and a defined decision. Finance translates supported portfolio selections into polynomial models and restores solver samples to asset weights. Researchers can inspect the polynomial, penalties, variable mapping, conversion, and execution details while practitioners continue to evaluate the result in financial coordinates.

Two workflows share this principle. The direct portfolio compiler below provides a validated equal-weight selection encoding. Supported financial models also expose detached Opt formulations that can be compiled explicitly using Opt's representation controls. [Custom models and compilation](custom-models.md) describes that broader workflow and its recovery requirements.

## Financial selection and polynomial representations

For exactly $k$ selected assets, let $x_i\in\{0,1\}$ denote selection and set $w_i=(W/k)x_i$, where $W$ is `net_weight`. Cardinality is $\sum_ix_i=k$. This is a fixed allocation per selected asset, not a discretization of unrestricted continuous weights.

Variance and tracking-error objectives are quadratic in selection bits. Higher-moment utility can contain third- and fourth-order interactions. QpiAI Opt's native higher-order HUBO solver solves such polynomials in their natural higher-order form, preserving the original energy landscape without reductions or reduction-induced approximations. Pairwise QUBO or Ising compilation instead uses Opt's recorded quadratization when required; that conversion introduces product auxiliaries with an explicit inverse mapping.

## `compile_portfolio`

Import from `qpiai_finance.quantum`:

```python
compile_portfolio(
    model, *, representation="hubo", penalty=None,
    quadratization_strength=None,
)
```

Returns a `PortfolioEncoding` containing a detached financial snapshot, authoritative Opt problem, and inverse mapping.

| Parameter | Type and meaning |
| --- | --- |
| `model` | `PortfolioModel` configured with `select_assets(count=..., equal_weight=True)`. |
| `representation` | Exactly `"hubo"`, `"qubo"`, or `"ising"`; default `"hubo"`. |
| `penalty` | Optional strictly positive finite real selection/weight-validity penalty. `None` selects a value exceeding the compiler's objective-range bound. |
| `quadratization_strength` | Optional finite non-Boolean real strength for pairwise product penalties. `None` selects the sufficient value defined below; smaller explicit values are rejected. Rejected for `representation="hubo"`. |

Supported objectives are minimum variance, tracking-error variance, mean-variance utility, and higher-moment utility. The compiler represents cardinality, individual weight bounds, and the implication of the configured gross-exposure limit for a nonnegative equal-weight portfolio. A leverage limit below `net_weight` is infeasible and remains reflected in the penalty; compilation does not make it feasible.

Cash accounts, return floors, exposure groups, turnover, volatility limits, robust-return uncertainty, and fixed selections are rejected by this direct compiler. Other portfolio objectives have no direct compilation here. The error lists unsupported configured restrictions; do not remove a required restriction merely to make compilation succeed. Use another supported financial formulation and explicit Opt compilation where appropriate.

## Objective and penalty meaning

The encoded representation minimizes an objective. For a source maximization, Finance negates the financial objective. Let $f(x)$ be this minimization polynomial before penalties. The compiler bounds its range by the sum of absolute nonconstant coefficients:

$$
B=\sum_{S\ne\varnothing}|a_S|,\qquad f(x)=a_{\varnothing}+\sum_{S\ne\varnothing}a_S\prod_{i\in S}x_i.
$$

The cardinality penalty is $(\sum_ix_i-k)^2$. Additional terms count forbidden zero/selected choices under individual bounds and any unavoidable leverage conflict. Each positive violation is at least one. If a feasible selection exists, a penalty strictly greater than $B$ is sufficient for a global minimizer to prefer feasibility. This is a property of the encoded global problem, not a certificate for a heuristic sample.

For `B > 0`, the default is `max(1.01*B, numpy.nextafter(B, numpy.inf))`; for `B=0`, it is `1.0`. An explicit penalty at or below $B$ is recorded as `penalty_guarantee="heuristic"`; a larger value is `"sufficient_if_feasible"`. All recovered samples still undergo financial checks. Quadratic product penalties have their separate Opt conversion settings and records.

For pairwise compilation, Opt first substitutes shared products in the complete penalized polynomial. Let `R` be the sum of absolute nonconstant coefficients after those substitutions, before product penalties. Its default and minimum accepted `quadratization_strength` is `max(1.0, R + max(1.0, R*1e-6))`. A finite explicit value must be at least that threshold, including when the polynomial already has degree at most two. Each auxiliary `y=x_i*x_j` receives the Rosenberg penalty `strength*(x_i*x_j - 2*x_i*y - 2*x_j*y + 3*y)`. Source and product penalties have different purposes and remain separately recorded.

For a valid auxiliary assignment, financial objective recovery removes the selection penalty and restores the source sense. Encoded energy includes penalties and offsets. It must not substitute for the financial objective.

## `PortfolioEncoding` properties

Create an encoding with `compile_portfolio`; its constructor is the compiler's assembly interface rather than an alternative financial input API:

```python
PortfolioEncoding(
    portfolio, problem, names, objective, violations, details,
    conversion, build_time,
)
```

All constructor arguments are required; the following types describe the records assembled by `compile_portfolio`.

| Argument | Type and meaning |
| --- | --- |
| `portfolio` | Detached `PortfolioModel` snapshot with a supported exact equal-weight selection. |
| `problem` | Matching Opt `HUBOProblem`, `QUBOProblem`, or `IsingProblem`, including encoded penalties, names, and offset. |
| `names` | Ordered tuple of original selection-variable strings, one per source asset. Excludes product auxiliaries. |
| `objective` | `dict[tuple[str, ...], float]` of the binary minimization objective before penalties. Empty-tuple keys denote constants. |
| `violations` | The same polynomial-dictionary type, describing cardinality, invalid weight choices, and any unavoidable leverage conflict before multiplying by selection penalty. |
| `details` | Compilation dictionary with the transformation fields described below; contains financial selection count/weight, representation, penalties, and conversion records. |
| `conversion` | Opt `HUBOToQUBOConvert` for QUBO/Ising, or `None` for HUBO. Provides the exact product-auxiliary mapping. |
| `build_time` | Float build duration in seconds. |

These objects must describe the same compiled model. Direct construction stores the supplied objects without financial validation or copying; it does not build an encoding from arbitrary inputs. `compile_portfolio` performs the validation and creates the detached snapshot used by the documented workflow.

Use these read-only views to inspect an encoding:

| Property | Type and contract |
| --- | --- |
| `problem` | Detached `HUBOProblem`, `QUBOProblem`, or `IsingProblem` from Opt. Mutating it does not change the encoding. |
| `variable_names` | Tuple of complete encoded variable names, including product auxiliaries. Defines sample order. |
| `variable_mapping` | DataFrame with `variable`, `asset_id`, `selected_weight`, covering original financial selection variables. |
| `objective_polynomial` | Copy of the binary minimization coefficient dictionary before penalties; tuple-of-name keys, including `()` for the constant where present. Uses binary coordinates even for an Ising encoding. |
| `transformations` | Detached list containing the financial compilation record. |
| `compilation_settings` | Detached dictionary of `representation`, effective `penalty`, and requested `quadratization_strength` for rebuilding from the retained financial model. |

The transformation record has the following fields. Retain the source inputs and package versions alongside these settings for later recovery.

| Field | Type and meaning |
| --- | --- |
| `type` | String `"binary_portfolio"`. |
| `representation` | `"hubo"`, `"qubo"`, or `"ising"`. |
| `source_sense` | `"MAX"` for utility objectives, otherwise `"MIN"`. |
| `weight_per_selected_asset` | Float `net_weight / selection_count`. |
| `selection_count` | Integer required asset count. |
| `objective_range_bound` | Float $B$ for the minimization polynomial before penalties. |
| `minimum_positive_violation_penalty` | Float `1.0`, the lower bound on a positive violation-polynomial value before multiplying by `penalty`. |
| `penalty` | Effective positive float selection/weight-validity penalty. |
| `penalty_guarantee` | `"sufficient_if_feasible"` or `"heuristic"`, according to the bound above. |
| `source_degree` | Integer maximum degree of the objective before penalties; zero for a constant polynomial. |
| `encoded_degree` | Integer degree of the penalized binary polynomial **before** pairwise quadratization. This can exceed two even when the requested output is QUBO or Ising. |
| `auxiliary_variables` | Integer product-auxiliary count; zero for HUBO. |
| `spin_convention` | String `"s = 2*x - 1"`. |
| `discretization` | `None`; selected-asset weights are fixed by the financial model. |
| `quadratization_strength` | Requested float strength or `None` for Opt's automatic rule. The effective strength is in the quadratization record. |
| `quadratization` | Empty list for HUBO; otherwise Opt's list of conversion dictionaries described below. |

The pairwise conversion dictionary contains `transformation="hubo_quadratization"`, `method="shared Rosenberg products"`, `auxiliary_products` mapping each auxiliary name to its pair of factor names, and the effective float `penalty_strength`. Its `original_sense` is `"MIN"`, since Finance has already converted the financial objective to minimization; `decode="discard auxiliary product variables"` describes restoration of the original selection coordinates. These conversion fields are separate from the financial `source_sense` and selection penalty.

## Inspect, encode, decode, and evaluate

```python
encoding.inspect(*, algorithm=None)
encoding.encode_selection(selected)
encoding.decode(sample)
encoding.energy(sample)
encoding.evaluate(sample, *, tolerance=1e-7)
encoding.evaluate_samples(samples, *, tolerance=1e-7)
```

`inspect` has the same encoded report as root `inspect`: financial specification, Opt optimization information, transformations, and `variable_mapping`. Optional `algorithm` adds compatibility and logical circuit/resource inspection without execution or authentication. The [inspection report fields](algorithm-controls.md#inspection-report) define counts, parameterization, and algorithm-specific structure.

`selected` is a complete vector, Series, or mapping of exact `0/1` asset selections. Labeled inputs align by source asset identifier. `encode_selection` returns a Python list in complete encoded variable order, filling product auxiliaries using the recorded conversion. Ising output contains spins. An infeasible financial selection may still be encoded; evaluate it separately.

`sample` is a complete finite vector, Series, or mapping keyed by `variable_names`. Arrays follow that order. HUBO/QUBO values must be exactly `0` or `1`; Ising values must be exactly `-1` or `1`. `decode` returns an asset-indexed Series named `weight`. It retains the fixed weight per selected name even if cardinality is wrong; it does not normalize or repair the sample. `energy` returns a float including all encoded penalties and offsets.

`evaluate` returns the source portfolio evaluation plus `decision={"weights": ...}`, `energy`, `selection_penalty`, and `auxiliaries_valid`. It adds a `product_auxiliaries` constraint row. Financial feasibility requires both original financial constraints and consistent product auxiliaries. `tolerance` is a finite nonnegative scalar, default `1e-7`; bit/spin domain validation remains exact.

`samples` is a two-dimensional numeric array or DataFrame. DataFrame columns must exactly cover all encoded variable names, and row identifiers must be unique. Arrays follow `variable_names` and receive positional row identifiers. `evaluate_samples` returns a DataFrame indexed by `sample` with `objective`, `feasible`, `energy`, `selection_penalty`, and `auxiliaries_valid`.

## Native execution

```python
encoding.solve(
    *, client=None, mode="local", algorithm=None, execution=None,
    allow_platform=False, tolerance=1e-7, **options,
)
```

Root `solve(encoding, ...)` delegates to this method; its optional solver must be `None` or `"qpiai"`. Without an algorithm, execution calls Opt's native polynomial route, accepting `local`, `auto`, or `platform` and the applicable Opt options. Every solve requires an Opt client. `auto` permits paid fallback only with `allow_platform=True`. An `execution` object without an algorithm is rejected.

Results are `FinanceResult` records with original weights, objective, constraints, financial metrics, `binary_variables` table, and compilation transformations. Source optimality requires a genuine backend proof, consistent auxiliaries, objective reconciliation, and financial feasibility. Paid work and local limits follow [solving](solving.md).

## Gate-based quantum algorithms and research controls

Finance uses the quantum algorithms from `qpiai_opt.quantum`. It does not implement a parallel algorithm hierarchy or re-export them from its own `quantum` namespace. Available accepted algorithm types are `QAOA`, `VQE`, `SamplingVQE`, `RecursiveQAOA`, and `ADAPTQAOA`.

Compile to `representation="qubo"` or `"ising"` before gate-based execution; direct HUBO gate execution is rejected. Register width includes any product auxiliaries. Inspect the actual encoding and algorithm rather than assuming one qubit per asset after quadratization.

```python
from qpiai_opt.quantum import QAOA, QuantumRun
from qpiai_finance import inspect
from qpiai_finance.quantum import compile_portfolio

encoding = compile_portfolio(portfolio, representation="ising")
algorithm = QAOA(reps=2, max_iterations=100)
execution = QuantumRun(shots=2048, seed=7)
report = inspect(encoding, algorithm=algorithm)
```

This code constructs and inspects the problem without running circuits. The `portfolio` must meet the compiler contract above. Research controls are organized by their actual role:

| Purpose | Controls |
| --- | --- |
| QAOA depth and parameterization | `reps`, standard/multi-angle parameterization, initial parameter vector. |
| Variational search | Supported optimizer, iteration controls, and custom optimizer callbacks where the algorithm accepts them. |
| Initial states and constrained mixing | QAOA initial state, `WarmStart`, `XYMixer`, or compatible custom mixer. |
| VQE family circuit choice | Built-in or supported custom ansatz and initial parameters. |
| Recursive/adaptive search | Recursive reduction controls or ADAPT operator pool, layer, and gradient controls. |
| Sample aggregation | `CVaR` where supported, with its lower-energy-tail semantics. |
| Circuit execution | `QuantumRun` shots, local seed, explicit platform device/experiment, and per-circuit timeout where supported. |

The [algorithm control reference](algorithm-controls.md) defines every accepted constructor, field, allowed value, default, parameter order, and callback contract for Finance's gate workflow. It also covers offline circuit construction and the difference between dependency-level execution and financial result recovery. Algorithm objects are not serialized as financial model inputs.

### XY mixing

Finance requires an explicit initial bit sequence for QAOA with `XYMixer`. Its original asset-selection bits must contain exactly the requested selection count. An XY group cannot mix original selections with product auxiliaries. Opt also checks register width and mixer validity. XY mixing preserves its group Hamming weights; it does not establish arbitrary financial feasibility or auxiliary consistency.

### Authentication and execution budget

```python
import os

from qpiai_opt.quantum import QpiAIQuantumAuth
from qpiai_finance import solve

QpiAIQuantumAuth.login(api_key=os.environ["QCLOUD_API_KEY"])
result = solve(
    encoding, client=client, algorithm=algorithm,
    execution=execution, mode="local",
)
```

`client` is the Opt client described in [getting started](getting-started.md). Gate-based quantum computation requires both Opt and QCloud authentication. `mode` must be `"local"` or `"platform"`; `auto`, paid fallback, and arbitrary `**options` are rejected. Selecting platform execution can consume credits.

`QuantumRun.shots` counts shots per circuit execution, not the whole variational run. An optimizer can evaluate many circuits. Its platform timeout is a per-circuit timeout, not an overall algorithm deadline. Local seeds are not platform options. Select and budget the complete algorithm using Opt's execution contract.

## Bit order and source verification

The Opt spin convention is $s_i=2x_i-1$. Computational-basis Pauli values use $Z_i=1-2x_i=-s_i$. `variable_names` and `sample` use increasing variable order. Printed measurement bitstrings are most-significant-bit first: their rightmost character is variable/qubit zero.

Finance checks that reported samples, names, bitstrings, energies, and internal energies agree with the retained encoding. It recalculates all reported candidate financial objectives and constraints, including product auxiliaries. Among feasible reported candidates it chooses the best original financial objective, with bitstring order as a deterministic tie-break. It does not simply accept the provider's minimum-energy primary sample.

Reported measurement candidates and an explicitly declared recursive residual candidate retain distinct meanings. A residual candidate is not assigned fabricated measurement counts or probabilities. Gate-based results carry no new global financial optimality proof.

## Gate-based quantum result data

In addition to common financial fields, results provide:

| Location | Meaning |
| --- | --- |
| `tables["binary_variables"]` | Original selection-to-asset mapping. |
| `tables["quantum_samples"]` | Candidate table indexed by MSB-first bitstring; columns are defined below. |
| Quantum sample table `attrs["probability_scope"]` | Provider-declared candidate distribution scope. Counts from several stages need not describe only the final circuit. |
| `tables["quantum_history"]` | `training_objective` by optimizer evaluation; it is not a sequence of final financial objectives. |
| `solver_info["quantum"]` | Recorded Opt quantum diagnostics, including available counts, candidate distribution, parameters, jobs, logical circuit, and backend metadata. |
| `solver_info["candidate_observations"]` | Total observations across the reported measured candidates. |
| `solver_info["selected_bitstring"]` | Selected feasible candidate when one exists. |
| `solver_info["encoded_objective"]` | Recomputed encoded energy of the selected candidate when one exists. |
| Live execution `solver_info["algorithm_configuration"]`, `execution_settings`, `quantum_structure` | Recorded algorithm controls, QuantumRun settings, and inspected circuit/resource structure. |

If no reported candidate is financially feasible, the result has no fabricated decision and reports `no_feasible_sample`. [Results](results.md) defines the common verification fields. [Plotting](plotting.md) describes sample and convergence figures.

The [recorded algorithm diagnostics](algorithm-controls.md#recorded-algorithm-diagnostics) define every quantum diagnostic field, algorithm metadata record, and live configuration record.

### Candidate table

| Column | Type and meaning |
| --- | --- |
| `count` | Positive integer observations in the provider's candidate record; missing for an unmeasured residual-only candidate. |
| `probability` | Float `count / candidate_observations`; missing for an unmeasured residual-only candidate. |
| `reported_count` | Integer count in the provider's separate reported-count dictionary, or zero when absent there. It need not equal the candidate's `count`. |
| `energy` | Float recomputed encoded energy, including offsets and penalties. |
| `objective` | Float recomputed original financial objective. |
| `feasible` | Boolean result of the original financial and product-auxiliary checks. |
| `auxiliaries_valid` | Boolean consistency of every product auxiliary. |
| `selection_penalty` | Float selection/weight-validity penalty contribution; excludes product-auxiliary penalties. |
| `maximum_violation` | Float maximum residual in the candidate's constraint table. |
| `classical_residual` | Boolean marking an explicitly declared recursive residual candidate, which may also have been observed. |

Missing counts/probabilities appear as pandas missing values; a missing count can promote the count column to floating dtype. The typed provider record in `solver_info["quantum"]` retains its integer counts. With no measured or declared residual candidates, the sample table is empty and has no candidate columns. No observations are invented for a residual-only candidate.

## Recover a recorded Opt result

```python
encoding.decode_result(result, *, tolerance=1e-7)
```

`result` is a typed Opt QUBO/HUBO/Ising SolveResult matching the encoding, or an Opt `QuantumResult` for its pairwise gate representation. Native records must match sample order, variable assignment, class, and encoded energy. Gate records additionally require valid solve information, consistent measurement counts and probabilities, and matching declared candidates.

Returns a freshly evaluated `FinanceResult` without authentication or execution. Native recorded recovery does not establish a new global financial optimum. Gate records always remain best-found candidates. Keep the original model, compilation settings, versions, and typed Opt record; numeric report JSON is not a substitute for that representation.

`results.from_opt(record, model=encoding, ...)` delegates to this recovery. Supplying a separate Opt model or LP/MILP objective scaling with a `PortfolioEncoding` is rejected because the encoding already owns its mapping. For other explicitly compiled financial models, use the separate recovery contract in [results](results.md).
