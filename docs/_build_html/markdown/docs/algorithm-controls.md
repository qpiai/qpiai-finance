# Gate-based algorithm controls

Financial practitioners can use the [portfolio compiler](quantum.md) to express investment selection in portfolio terms. Researchers can then select the algorithm, parameterization, initial state, mixer, optimizer, and circuit execution settings on that same retained financial problem.

Import the controls on this page from `qpiai_opt.quantum`. Finance 1.0.3 uses Opt 0.0.9. These are dependency objects accepted by Finance's `algorithm` and `execution` arguments, rather than a separate Finance algorithm hierarchy. All Finance gate solves require an explicit pairwise QUBO/Ising `PortfolioEncoding`, an Opt client, and QCloud authentication. Native HUBO execution uses [solver options](solver-options.md) instead.

Algorithm configurations are frozen dataclasses. Initial parameter vectors, basis-bit sequences, and custom pools are copied to tuples. Auxiliary/execution configurations are frozen keyword-only Pydantic models; unknown fields are rejected. Circuit objects and callbacks remain caller-owned and must remain stable during inspection/execution. Invalid types and incompatible settings raise `TypeError`, `ValueError`, or Pydantic validation errors, before execution where the incompatibility can be checked.

## QAOA

```python
QAOA(
    reps=1, parameterization="standard", optimizer="cobyla",
    max_iterations=100, initial_point=None, aggregation=None,
    warm_start=None, mixer=None, initial_state=None,
)
```

| Parameter | Type, allowed values, and default behavior |
| --- | --- |
| `reps` | Positive Python integer, default `1`; number of cost/mixer layers. Booleans rejected. |
| `parameterization` | `"standard"` (default) or `"multi_angle"`; case-insensitive and hyphens become underscores. |
| `optimizer` | Named optimizer or supported callable, default `"cobyla"`; contracts below. |
| `max_iterations` | Positive Python integer, default `100`; optimizer budget. Meaning depends on the chosen optimizer. Booleans rejected. |
| `initial_point` | Finite real parameter sequence of exact parameter count, or `None` (default) for zero initial parameters. |
| `aggregation` | `CVaR` or `None` (default) for sampled expectation. |
| `warm_start` | `WarmStart` or `None` (default). Supplies both preparation and a tilted mixer; cannot combine with `mixer` or `initial_state`. |
| `mixer` | `XYMixer`, custom callable, or `None` (default) for X mixing. Custom mixers require standard parameterization; XY requires an explicit initial state. |
| `initial_state` | Basis-bit sequence in increasing qubit order, same-width unmeasured `Circuit`, or `None` (default) for uniform superposition. Finance requires a bit sequence when using XY mixing. |

Standard parameters are ordered `gamma[0:reps]`, then `beta[0:reps]`; count is `2*reps`. Multi-angle order is per layer: sorted nonzero Z fields, sorted nonzero ZZ couplings, then mixer generators. Count is `reps*(fields + couplings + mixer_generators)`. The identity constant has no parameter. X/warm mixing has one generator per qubit; XY has one per configured edge.

`algorithm.parameter_count(problem) -> int` computes this count for the explicit Opt QUBO/Ising representation, including encoded auxiliary bits. Use the encoding's exported problem, not the `PortfolioEncoding` wrapper, for dependency-level methods. `inspect(encoding, algorithm=algorithm)` performs the complete Finance/Opt compatibility check and reports register/circuit resources offline.

A custom mixer has signature `mixer(circuit, beta, layer)`. It mutates that supplied QpiAI `Circuit`, returning `None` or the same circuit, without adding measurements. `beta` is the layer angle and `layer` is its zero-based index. A custom mixer does not supply an inferred multi-angle generator layout.

## VQE and SamplingVQE

```python
VQE(
    ansatz="standard", optimizer="cobyla", max_iterations=100,
    initial_point=None,
)
SamplingVQE(
    ansatz="standard", optimizer="cobyla", max_iterations=100,
    initial_point=None, aggregation=None,
)
```

| Parameter | Type, allowed values, and default behavior |
| --- | --- |
| `ansatz` | `"standard"` (default), `"hardware_efficient"`, `"two_local"`, QpiAI `Circuit`, or `Callable[[int], Circuit]` receiving register width. Built-in names normalize case and hyphens. |
| `optimizer` | Named optimizer only, default `"cobyla"`. Custom optimizer callbacks are rejected. |
| `max_iterations` | Positive Python integer, default `100`, excluding booleans. |
| `initial_point` | Finite real sequence of exact bindable-angle count, or `None` (default). VQE uses Quantum SDK initialization; SamplingVQE draws uniformly on `[0, 2*pi)`. Local `QuantumRun.seed` controls supported random initialization. |
| `aggregation` | SamplingVQE only: `CVaR` or default `None` for sampled expectation. |

Custom circuits must have exactly the compiled problem width, no measurements, and at least one bindable parameter. Each parametric gate must have one bindable angle; binding follows circuit operation order. Inspection reports the parameter count. VQE minimizes a Hamiltonian expectation; SamplingVQE minimizes an aggregate of sampled computational-basis energies. For Finance both return observed financial candidates, with the original constraints re-evaluated separately. The optimized variational aggregate need not equal the selected candidate's financial objective.

## Recursive QAOA

```python
RecursiveQAOA(qaoa=QAOA(), min_variables=10, eliminations_per_step=1)
```

Each omitted `qaoa` creates a separate default QAOA configuration.

| Parameter | Type, allowed values, and meaning |
| --- | --- |
| `qaoa` | `QAOA`, default configuration above. Its `initial_point`, `initial_state`, `warm_start`, and `mixer` must remain `None` because register size changes during reduction. Both parameterizations and CVaR are supported. |
| `min_variables` | Python integer in `[1,20]`, default `10`; desired residual width. Excludes booleans. Reduction can continue further to satisfy exact residual-work limits. |
| `eliminations_per_step` | Positive Python integer, default `1`; maximum disjoint pair relations committed in each reduction stage. Excludes booleans. |

The algorithm estimates correlations from optimized-stage samples, fixes selected spin relations, reduces the problem, solves the residual through Opt's exact local Ising route, and reconstructs full-register candidates. An exact residual does not prove the original optimum because correlation-based elimination is heuristic. It requires the compiled local runtime and QCloud authentication in both execution modes.

A problem already within the residual threshold can execute locally with no circuit stage; diagnostics identify that exact residual route. Platform zero-stage requests are rejected because they would execute no platform circuit. Lower `min_variables` when a reduction stage is intended. There is no static `build_circuit` method for this changing-register algorithm.

## ADAPT-QAOA

```python
ADAPTQAOA(
    operator_pool="single", optimizer="nelder_mead", max_iterations=100,
    max_layers=10, gradient_tolerance=1e-3, selection_gamma=0.01,
)
```

| Parameter | Type, allowed values, and meaning |
| --- | --- |
| `operator_pool` | Case-insensitive `"single"` (default), `"multi"`, or nonempty distinct custom Pauli-string sequence. |
| `optimizer` | Named optimizer or supported callable; default `"nelder_mead"`. |
| `max_iterations` | Positive Python integer, default `100`; optimizer budget for each layer's joint parameter search. |
| `max_layers` | Positive Python integer, default `10`; maximum committed mixer selections. |
| `gradient_tolerance` | Positive finite non-Boolean real, default `1e-3`; Euclidean pool-gradient stopping threshold. |
| `selection_gamma` | Positive finite non-Boolean real, default `0.01`; trial cost-evolution angle for operator selection. |

The single pool includes each X and Y operator plus their register-wide sums. Multi adds every two-qubit Pauli product over X/Y/Z on distinct pairs. A custom pool is a sequence of operators such as `[[(0, "X"), (1, "Y")], [(2, "Z")]]`. Each operator is a nonempty sequence of `(qubit_index, pauli)` pairs with distinct nonnegative non-Boolean integer indices in register range and Pauli labels X, Y, or Z. Duplicate operators are rejected.

The algorithm selects the largest-gradient pool operator, then jointly optimizes accumulated cost and mixer angles, stopping at the gradient threshold or layer cap. Local selection uses statevector expectations; platform selection estimates grouped Pauli measurements. It has no static circuit builder. CVaR, warm starts, custom initial states, and XY mixing are not accepted fields.

## Named and custom optimizers

Allowed names are `"cobyla"`, `"spsa"`, `"nelder_mead"`, and `"powell"`, case-insensitive with hyphens normalized to underscores. There is no separate optimizer-options dictionary in these constructors. `max_iterations` is passed to the selected implementation; it is not a universal circuit-execution count.

QAOA and ADAPT-QAOA also accept:

```python
optimizer(objective, initial_parameters, max_iterations)
# -> (parameters, value) or (parameters, value, info)
```

`objective` takes a finite one-dimensional NumPy parameter vector and returns a finite float; calling it may execute circuits. `initial_parameters` is a detached NumPy vector. Return a finite parameter vector of the same length and a finite real `value`. Optional `info` is a mapping: recognized `nfev`, `nit` are nonnegative integral counts or `None`; `history` is a finite objective-value sequence; `param_history` contains finite vectors of the same parameter length. Missing histories default to empty lists and counts to `None`. Invalid diagnostics fail before final circuit execution. The callback owns stopping behavior and must respect the chosen computation budget.

## Sample aggregation

```python
CVaR(*, alpha=1.0)
aggregation.aggregate(distribution)  # -> float
```

`alpha` is a finite non-Boolean real in `(0,1]`, default `1.0`. This algorithmic CVaR averages the **lowest-energy** probability mass and is separate from financial upper-loss-tail expected shortfall. `distribution` is a nonempty energy-to-probability mapping with finite non-Boolean real entries, nonnegative probabilities, and total mass close to one (`rel_tol=1e-10`, `abs_tol=1e-12`). Accepted mass is normalized; zero mass is ignored; fractional boundary mass is included. `alpha=1` is sampled expectation. Unrepresentable nonzero aggregates raise rather than silently underflowing.

## Warm-start preparation

```python
WarmStart(*, epsilon=0.25, relaxed_solution=None)
```

`epsilon` is a finite non-Boolean real in `[0,0.5]`, default `0.25`. `relaxed_solution` accepts `None`, a complete per-variable probability sequence, complete variable-name mapping, or consecutive index mapping `0..n-1`. All entries are finite non-Boolean reals in `[0,1]`. Names/length must cover the entire compiled register, including auxiliary variables. The configuration copies the numeric data and clips probabilities to `[epsilon, 1-epsilon]` for preparation and tilted mixing.

Default `None` requests a bounded local continuous relaxation using L-BFGS-B, starting at zero spins with bounds `[-1,1]` and `maxiter=200`. Its local optimization is not a proof of a global relaxation optimum or financial feasibility. WarmStart defines its own initial state/mixer and cannot combine with QAOA's other preparation/mixing controls.

## XY mixer

```python
XYMixer(*, groups, topology="ring")
mixer.edges()  # -> tuple[tuple[int, int], ...]
```

Required `groups` is a nonempty sequence of disjoint groups, each with at least two distinct nonnegative Python integer qubit indices, excluding booleans. `topology` is case-insensitive `"ring"` (default) or `"full"`. `edges()` returns stable unique sorted endpoint pairs. Register indices are checked with the problem. Groups need not cover the whole register; only configured edges mix.

Paired XX/YY rotations preserve group Hamming weight. Finance additionally requires an explicit initial bit sequence with the requested number of original asset selections; groups cannot mix original selection bits and product auxiliaries. Group conservation does not establish arbitrary financial constraints or auxiliary consistency.

## Inspection report

`inspect(encoding, algorithm=algorithm)["optimization"]["quantum"]` is a dictionary describing the compiled register and configured algorithm. Integer counts refer to the logical circuit before device routing; they are not estimates of total algorithm executions or physical-device cost.

| Common field | Type and meaning |
| --- | --- |
| `algorithm` | String algorithm class name. |
| `compatible` | Boolean `True` after successful compatibility checks; incompatible configurations raise. |
| `qubits` | Integer compiled register width, including auxiliary bits. |
| `hamiltonian_terms` | Integer number of retained Pauli terms, including a nonzero identity offset. |
| `linear_terms`, `quadratic_terms` | Integer field/coupling counts. |
| `max_locality` | Integer largest number of qubits in a retained term; zero for a constant problem. |
| `diagonal` | Boolean; true for Finance's eligible QUBO/Ising encodings. |
| `logical_circuit` | `None` or dictionary with `depth: int`, `size: int`, and `gate_counts: dict[str, int]`. Custom QAOA mixers, ADAPT-QAOA, and RecursiveQAOA report `None` because inspection does not build their final circuit. |

The following fields depend on the algorithm:

| Algorithm | Additional fields |
| --- | --- |
| QAOA | `parameter_count: int`; `reps: int`; normalized `parameterization: str`; `mixer: str` (`"x"`, `"xy"`, `"warm_start"`, or `"custom"`); `aggregation` (float alpha or `"expectation"`); `warm_start` (float epsilon or `None`); `initial_state: bool`, true for explicit or warm-start preparation. |
| VQE, SamplingVQE | `parameter_count: int`; `ansatz: str` (configured built-in name or `"custom"`); normalized `optimizer: str`. SamplingVQE also includes `aggregation` (float alpha or `"expectation"`). |
| RecursiveQAOA | `min_variables: int`, `eliminations_per_step: int`, and `inner_qaoa: dict`, the QAOA report on the full input register. |
| ADAPT-QAOA | `operator_pool: str` (`"single"`, `"multi"`, or `"custom"`); `operator_pool_size: int`; `max_layers: int`; `gradient_tolerance: float`; `selection_gamma: float`. |

QAOA/VQE inspection constructs circuits at zero parameters to report structure. Warm-start inspection substitutes probabilities of `0.5` for circuit structure; it does not run the default relaxation. Recursive/adaptive reports describe configuration rather than predicting the number of stages, selected operators, or eventual circuit.

## Circuit construction and execution

QAOA, VQE, and SamplingVQE expose dependency-level methods:

```python
algorithm.build_circuit(problem, parameters, measurements=False)  # -> Circuit
algorithm.run(problem, *, execution=None, mode="local")          # -> QuantumResult
```

Here `problem` is the explicit exported Opt QUBO/Ising problem. `parameters` is a finite real sequence of exact parameter count; `measurements` is a Boolean. Construction is offline. The module function `build_circuit(problem, *, algorithm, parameters=None, measurements=False) -> Circuit` has the same contract; when parameters are omitted the algorithm must supply `initial_point`.

Direct `.run` returns an Opt `QuantumResult`; it does not perform Finance's source-model recovery. For a financial result, call `solve(encoding, client=client, algorithm=algorithm, execution=execution, mode=...)`, or recover a retained record with `encoding.decode_result(...)`. Finance returns `FinanceResult`, rechecks original financial constraints, and selects among financially feasible candidates.

```python
QuantumRun(
    *, shots=1024, experiment_name=None, timeout=None,
    seed=None, device_name=None,
)
```

| Field | Type, allowed values, and default behavior |
| --- | --- |
| `shots` | Strict positive integer, default `1024`; shots per circuit execution. |
| `experiment_name` | Nonblank stripped string or `None` (default). Platform omission selects `"Default Experiment"`; an explicit name must identify an existing experiment. |
| `timeout` | Positive finite non-Boolean real or `None` (default). Platform per-circuit timeout in seconds; rejected locally. It is not a whole-algorithm deadline. |
| `seed` | Strict integer in `[0,2**32-1]` or `None` (default). Local sampling, supported initialization, and SPSA randomness; rejected on the platform. |
| `device_name` | Nonblank stripped string or `None` (default). Platform omission selects `"QpiAI-Indus-1"`; rejected locally. `"QpiAI-QSV-Local"` is not a platform device. Available platform names follow QCloud device access. |

Omitted Finance `execution` uses `QuantumRun()`. Modes are exactly local/platform; automatic fallback and arbitrary solve options are rejected. QCloud authentication is required for both, and Finance additionally verifies the Opt client. A variational run can execute many circuits, plus final measurements and adaptive selection work. Shots and timeout are per circuit, not aggregate budgets. [Quantum results](quantum.md#gate-based-result-data) defines candidate, history, and execution diagnostics; [Opt's gate API](https://github.com/qpiai/qpiai-opt/blob/main/docs/api-quantum.md) covers its full dependency-level result types.

## Recorded algorithm diagnostics

Finance stores Opt's JSON-form diagnostics in `result.solver_info["quantum"]`. The fields describe the recorded computation; Finance's recovered candidate tables provide the separate financial checks.

| Field | Type and meaning |
| --- | --- |
| `algorithm`, `backend` | Strings identifying the algorithm and actual execution backend. A zero-stage RecursiveQAOA result identifies the local exact Ising route. |
| `shots` | Positive integer requested per circuit. |
| `optimizer` | Optimizer name string or `None` when none ran. |
| `evaluations`, `iterations` | Nonnegative integer counts or `None` when unavailable. The provider's optimizer defines what it counts. |
| `optimized_parameters` | List of finite floats for the final variational parameters; empty if none. RecursiveQAOA retains its last stage's parameters. |
| `objective_history` | List of finite objective floats in optimizer evaluation order. Variational aggregate values may differ from an individual candidate's objective. |
| `parameter_history` | List of finite-float parameter lists retained by the optimizer; empty if unavailable. Adaptive layers can have different vector lengths. |
| `counts` | Dictionary from MSB-first bitstrings to positive integer counts. QAOA, VQE, SamplingVQE, and ADAPT-QAOA report final measurements here; RecursiveQAOA reports reconstructed observations across stages. |
| `candidates` | List of sample dictionaries described below; the observation scope can include more circuits than `counts`. |
| `job_ids` | List of platform job-ID strings, empty when none. |
| `logical_circuit` | `None` or the `depth`, `size`, and `gate_counts` dictionary defined in the inspection report. This describes the final circuit, or last QAOA stage for RecursiveQAOA. |
| `qpu_metadata` | List of JSON-compatible backend metadata dictionaries. Keys depend on the backend response; local execution may supply simulator metadata. |
| `transformations` | List of JSON-compatible transformation dictionaries retaining representation and spin-to-Pauli conversions. |
| `algorithm_metadata` | JSON-compatible algorithm-specific dictionary described below. |

Each `candidates` entry contains `bitstring: str`, `count: int`, `probability: float`, `internal_energy: float`, `objective: float | None`, `feasible: bool | None`, `solution: list[int | float] | None`, and `variable_assignment: dict[str, int | float] | None`. These are provider values for the encoded optimization problem. `internal_energy` uses its minimization convention; `objective` restores the encoded problem's declared sense. `solution` follows the encoded variable order and `variable_assignment` uses its names. Finance independently verifies these against the retained encoding and original financial model. A recursive residual-only candidate is recorded separately in `algorithm_metadata`, without invented measurement observations.

### Algorithm metadata

| Algorithm | Fields and meanings |
| --- | --- |
| QAOA | `reps: int`, `parameterization: str`, `parameter_order: str`, `mixer: str`, and `aggregation` (float alpha or `"expectation"`) describe the configured circuit/search. `optimized_aggregate: float` is the optimizer's returned value; `optimization_offset: float` records the excluded optimization constant; `candidate_distribution: str` states the observation scope. Warm starts additionally record the fields below. |
| VQE | `ansatz: str` (configured name or `"custom"`), `variational_energy: float`, `optimizer_message: str`, and `candidate_distribution: str`. An optimization input also includes `optimization_offset: float`. The variational energy is not a financial feasibility or optimality certificate. |
| SamplingVQE | `ansatz: str`, `aggregation` (float alpha or `"expectation"`), `optimized_aggregate: float`, and `candidate_distribution: str`; an optimization input also includes `optimization_offset: float`. |
| ADAPT-QAOA | `operator_pool: str`, `operator_pool_size: int`, `optimization_offset: float`, `operator_sequence: list[str]`, `layers: int`, `selection_gamma: float`, `gradient_tolerance: float`, `final_gradient_norm: float`, `selection_history: list[dict]`, and `candidate_distribution: str`. Each selection record contains zero-based `layer: int`, `gradient_norm: float`, `selected_operator: str`, and signed `selected_gradient: float`. |
| RecursiveQAOA | `reductions: list[dict]`, `quantum_stages: int`, `quantum_execution_performed: bool`, `residual_variables: int`, `residual_solver: str`, `residual_objective: float`, `optimization_offset: float`, `reconstructed_internal_energy: float`, `residual_candidate: dict`, and `candidate_distribution: str`. The residual candidate has `bitstring: str`, `objective: float`, and `feasible: bool`. |

A recursive reduction record contains `input_variables: int`, `output_variables: int`, `relations: list[dict]`, and two-element integer lists `objective_history_range` and `parameter_history_range`. The ranges are half-open slices of the combined histories. Each relation contains original-register indices `eliminated: int`, `retained: int`, `sign: int` (`-1` or `1`), `correlation: float`, and `absolute_correlation: float`; it imposes `spin[eliminated] = sign * spin[retained]`. Residual objective and reconstructed internal energy belong to different representations and must not be compared as financial objectives without the recorded conversion.

Warm-start metadata contains `relaxation_method: str`, `relaxation_global: bool | None`, `relaxed_solution: list[float]`, and `clipped_solution: list[float]`. Automatically computed relaxation also includes `relaxation_success: bool`, `relaxation_objective: float`, `relaxation_offset: float`, and `relaxation_message: str`. Its source polynomial value includes the recorded offset. Supplied probabilities report `relaxation_global=None` and do not claim a relaxation solve.

Live Finance execution also records `algorithm_configuration`, `execution_settings`, and `quantum_structure` in `solver_info`. The first contains public algorithm dataclass fields recursively, the second contains all `QuantumRun` fields including `None` defaults, and the third is the inspection report above. Lists replace tuples. Caller-defined circuit/callback objects are recorded by `user_defined=True` and qualified `type` strings, with a qualified `callable` name when available; these records do not serialize executable objects.
