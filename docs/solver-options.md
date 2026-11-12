# Solver option reference

Pass these options to `qpiai_finance.solve` after selecting the financial model and execution route. This reference describes Finance 1.0.3 with QpiAI Opt 0.0.9 and Clarabel 0.11.1. SCIP's parameter catalogue depends on its installed native build. [Solving](solving.md) defines routing, authentication, return types, and verification; [algorithm controls](algorithm-controls.md) covers gate-based optimization.

Solver tolerances are separate from Finance's `tolerance=1e-7`, which checks the recovered financial decision. Options for another route are rejected rather than silently translated into an unrelated method.

## Opt local options

The complete direct option set for local Finance Opt execution is:

| Option | Classes | Type and allowed values | Default and meaning |
| --- | --- | --- | --- |
| `time_limit` | LP, MILP, QP | Finite real `> 0`, excluding booleans; `None` selects default. | `60.0` seconds of solver computation. |
| `mip_rel_gap` | MILP | Finite real `>= 0`, excluding booleans; `None` selects default. | `1e-4`; relative incumbent/bound gap target. |
| `node_limit` | MILP | Positive Python integer, excluding booleans; `None` leaves unset. | No node cap. |
| `num_reads` | QUBO, HUBO, Ising | Positive Python integer, excluding booleans; `None` selects default. | `8` independent annealing runs. |
| `num_sweeps` | QUBO, HUBO, Ising | Positive Python integer, excluding booleans; `None` selects default. | `500` sweeps per run. |
| `seed` | QUBO, HUBO, Ising | Python integer in `[0, 2**32-1]`, excluding booleans; `None` selects default. | `0`; sampling seed. |

The local polynomial solver chooses exhaustive enumeration when there are at most 20 active variables and exact work is at most 2,000,000. An active variable occurs in a nonzero nonconstant term. Exact work is `2**active_variables * max(1, active_variables + sum(nonconstant_term_degrees))`. Otherwise it uses native annealing. Enumeration does not use read/sweep/seed controls and records an empty effective-settings dictionary. The strategy follows the compiled problem, including auxiliaries and interactions; it is not an option to request a global proof above those limits.

### Local capacity

Limits are inclusive and apply to the compiled optimization representation rather than merely the count of original financial assets.

| Class | Variables | Rows | Nonzero terms/coefficients | Reads | Sweeps |
| --- | --- | --- | --- | --- | --- |
| LP, MILP | 20,000 | 20,000 | 1,000,000 matrix nonzeros | — | — |
| QP | 1,000 | 20,000 | 1,000,000 matrix and 100,000 Hessian nonzeros | — | — |
| QUBO, Ising | 250 | — | 5,000 polynomial terms | 16 | 5,000 |
| HUBO | 100 | — | 1,500 polynomial terms; no separate degree cap | 16 | 2,500 |

Polynomial annealing work cannot exceed 10,000,000. With nonconstant term degrees `d`, it is `num_reads * (sum(max(1,d)) + num_sweeps * (active_variables + sum(d*max(1,d-1))))`. LP/MILP file inputs additionally have a 50,000,000-byte limit. Local linear/Hessian nonzero coefficients require `1e-9 < abs(value) < 1e15`; objective coefficients and finite bounds require magnitude below `1e20`. Exactly represented integer data have magnitude at most `2**53`. Use compatible financial units when coefficients exceed the numerical range.

In `mode="auto"`, only `LocalLimitExceeded` permits fallback, and only with `allow_platform=True`. Platform-only options are not accepted by the local attempt. HUBO read/sweep/seed names remain supported on the platform; QUBO/Ising platform routes reject those direct controls instead of discarding them. LP/MILP high-level `time_limit`, `mip_rel_gap`, and `node_limit` translate to platform configuration fields when applicable. These contracts and limits are defined by the pinned [Opt local runtime](https://github.com/qpiai/qpiai-opt/blob/main/docs/local-solving.md).

## Opt platform options

Platform calls may consume credits. Finance constructs the algebraic/file representation where the provider requires it; QP remains local-only. The allowed blocking-call options are the common lifecycle fields below, plus the class-specific fields in subsequent tables.

| Option | Type and allowed values | Default and meaning |
| --- | --- | --- |
| `timeout` | Finite real `> 0`, excluding booleans. | LP/MILP `600.0` seconds; polynomial classes `5400.0`. Job-wait budget beginning after submission, not an overall end-to-end deadline. Expiry does not cancel the job. |
| `poll_interval` | Finite real `> 0`, excluding booleans. | `5.0` seconds between status polls. |
| `request_timeout` | Positive finite non-Boolean real or `None`. | `None` uses client request timeout, normally 60 seconds. Applies separately to submission/result requests. |
| `name` | Nonblank stripped string or `None`. | `None` generates a problem name. |
| `experiment_id` | Path-safe nonempty string or `None`. | `None` uses client/solver experiment selection. |
| `experiment_name` | Nonblank stripped string or `None`. | `None` uses configured/default experiment name. |
| `compute_resource_id` | Path-safe nonempty string or `None`. | `None` permits provider resource selection. |
| `queue` | Python boolean; QUBO/HUBO/Ising only. | `True` enables event-stream monitoring; `False` uses polling. |
| `workspace_id`, `project_id` | Path-safe nonempty strings or `None`; LP/MILP only. | `None` uses storage defaults. Scope uploaded model storage. |

Path-safe IDs use ASCII letters, digits, `.`, `_`, `-`, `~`; `.` and `..` are rejected. Experiment ID/name select context rather than financial data. A failed or ambiguous wait/submission does not authorize duplicate work; retain returned problem/job identifiers and reconcile them before retrying.

### Platform LP/MILP configuration

`config=None` uses a new `MILPSolverConfig()` from `qpiai_opt.opt_solvers.milp`. Supply that typed configuration object for explicit control. Its keyword-only fields are all listed below. Unknown fields raise a Pydantic validation error. Real values must be finite and non-Boolean; integer and Boolean fields use strict types. Case is normalized for enum strings, without stripping surrounding whitespace.

| Field | Allowed type/values | Default | Meaning |
| --- | --- | --- | --- |
| `time_limit` | Real `>= 0` | `300.0` | Solver wall-clock seconds; zero leaves unset. |
| `mip_max_nodes` | Integer `>= -1` | `-1` | Branch-and-bound node cap; `-1` unset. |
| `solution_limit` | Integer `-1` or `> 0` | `-1` | Feasible MIP solution count before stopping; one stops at the first. |
| `objective_bound` | Real or `None` | `None` | Stop when the dual bound reaches this value; for minimization, lower bound at least this value. |
| `objective_target` | Real or `None` | `None` | Stop at a feasible objective at least as good; for minimization, incumbent no greater than target. |
| `mip_rel_gap` | Real `>= 0` | `1e-4` | Relative MIP objective-gap target. |
| `mip_abs_gap` | Real `>= 0` | `1e-6` | Absolute MIP objective-gap target. |
| `primal_feasibility_tolerance` | Real `> 0` | `1e-7` | Solver primal constraint tolerance. |
| `dual_feasibility_tolerance` | Real `> 0` | `1e-7` | LP dual feasibility tolerance. |
| `mip_feasibility_tolerance` | Real `> 0` | `1e-6` | Distance-to-integer tolerance. |
| `threads` | Integer `>= 0` | `0` | Thread count; zero selects automatically. |
| `presolve` | `"on"`, `"off"`, `"choose"` | `"choose"` | Enable, disable, or delegate presolve. |
| `solver_algorithm` | `"simplex"`, `"ipm"`, `"choose"` | `"choose"` | LP simplex, interior point, or provider-selected algorithm. |
| `mip_heuristic_effort` | Real in `[0,1]` | `0.05` | MIP heuristic effort. |
| `output_flag` | Boolean | `False` | Console solver output. |
| `log_file` | Nonblank string or `None` | `None` | Log path on the solver host. |
| `include_dual_info` | Boolean | `False` | Request LP/relaxation shadow prices and reduced costs. |
| `compute_ranging` | Boolean | `False` | Request coefficient/RHS sensitivity ranges; requires a simplex basis. |
| `compute_iis` | Boolean | `True` | Request an irreducible infeasible set on infeasibility. |
| `collect_solution_pool` | Boolean | `False` | Collect improving MIP solutions; memory grows with stored assignments. |

The optional high-level aliases `time_limit` (LP/MILP), `mip_rel_gap` and `node_limit` (MILP only) populate `config.time_limit`, `.mip_rel_gap`, and `.mip_max_nodes`. Their platform domains are finite non-Boolean real `time_limit > 0`, finite non-Boolean real `mip_rel_gap >= 0`, and positive Python integer `node_limit`, excluding booleans. Explicit `None` is rejected; omit an alias to retain its default. Do not combine aliases with the `config` keyword, including `config=None`.

`warm_start=None` means no supplied start. A start is `qpiai_opt.opt_solvers.milp.WarmStart(*, col_values=None, col_basis_status=None, row_basis_status=None)`. `col_values` is a finite real dictionary keyed by nonempty optimization-variable names; missing variables form a partial start. Basis fields are lists of `"lower"`, `"basic"`, `"upper"`, `"zero"`, or `"nonbasic"`, in exported column/row order, case-insensitive. Both basis lists must be supplied together. At least column values or a complete basis is required. Unknown fields fail validation. Starts use the actual exported optimization coordinates and are not financial decision dictionaries.

Finance can scale an entire small LP/MILP objective by a positive power of two. It converts explicitly set configuration fields `objective_bound`, `objective_target`, `mip_abs_gap`, and `dual_feasibility_tolerance` to solver units, then restores source objective, bound, and dual units in results. Unset fields keep their provider-unit defaults; the restored settings show their source-unit values. Source constraints and the financial objective are preserved. Retain the scaling record for later recovery.

### Platform polynomial controls

QUBO and Ising blocking routes expose only the common polynomial lifecycle/context options. They do not expose public arbitrary sampling controls through Finance `solve`. The QUBO problem container uses its default evaluation budget; execution details returned by the provider remain in result diagnostics.

HUBO additionally accepts `solver_config: dict | omitted`, with exactly these keys, or the same keys directly as solve options. Direct values override dictionary values. Omitted values are left to the platform resource; the SDK does not define numerical defaults for those fields. This is distinct from the explicit local defaults.

| Key | Allowed type/values | Meaning |
| --- | --- | --- |
| `num_reads` | Positive Python integer, excluding booleans | Independent runs. |
| `num_sweeps` | Positive Python integer, excluding booleans | Sweeps per run. |
| `beta_min`, `beta_max` | Positive finite non-Boolean real | Initial/final inverse temperature. When both supplied, minimum cannot exceed maximum. |
| `num_threads` | Positive Python integer, excluding booleans | Requested thread count. |
| `temperature_schedule` | `"LINEAR"` or `"GEOMETRIC"`, case-insensitive | Inverse-temperature schedule. |
| `seed` | Python integer, excluding booleans | Requested platform random seed. |

Unknown keys and explicit `None` configuration values are rejected; omit unset fields. Platform HUBO requires active variables and cannot retain isolated encoded variables. Zero-coefficient QUBO platform inputs are also rejected. These are representation restrictions, independent of financial feasibility.

## CVXPY controls

Clarabel and CVXPY-backed SCIP accept the following common CVXPY solve controls. Defaults here are CVXPY defaults; Finance creates a fresh problem for each solve, so a cached warm start generally has no previous Finance solve to reuse. Version-dependent details below cover CVXPY 1.7.5 and 1.9.3, within Finance's supported dependency range.

| Option | Type/default | Meaning |
| --- | --- | --- |
| `verbose` | Boolean, `False` | Compilation and solver output. |
| `solver_verbose` | Boolean, `False` | Solver output without full CVXPY logging. |
| `bibtex` | Boolean, `False` | Print CVXPY, problem-grammar, and solver citations when `verbose=True`. |
| `warm_start` | Boolean, `True` | Permit an interface-supported cached start. |
| `enforce_dpp` | Boolean, `False` | Raise for non-DPP parameterized problems. |
| `ignore_dpp` | Boolean, `False` | Treat parameterized problems as non-DPP. Cannot combine true with `enforce_dpp=True`. |
| `canon_backend` | `None` by default, or a case-sensitive string from the backend table below | Canonicalization backend; `None` uses CVXPY selection, normally `"CPP"`. |

| Backend | Meaning and availability |
| --- | --- |
| `"CPP"` | C++ canonicalization. Available in both documented versions; restricted expression types may require a Python backend. |
| `"SCIPY"` | Python canonicalization using SciPy sparse matrices. Available in both documented versions. |
| `"NUMPY"` | Dense NumPy canonicalization in CVXPY 1.7.5; removed in 1.8. |
| `"COO"` | Sparse three-dimensional coordinate tensors, added in CVXPY 1.8. Available in 1.9.3. |
| `"RUST"` | Experimental Rust canonicalization through the optional `cvxpy_rust` extension module. The backend name exists in both documented versions; the extension must be installed. |

Unknown names or unavailable backend dependencies raise. Consult the installed [CVXPY canonicalization reference](https://www.cvxpy.org/tutorial/advanced/index.html#canonicalization-backends) when using another supported release.

The following controls apply specifically to Clarabel through CVXPY, rather than to Clarabel's native settings object:

| Option | Type/default | Meaning |
| --- | --- | --- |
| `use_quad_obj` | Boolean, `True` | Retain a supported quadratic objective during canonicalization instead of converting it to cones. SCIP does not accept this keyword. |
| `accept_unknown` | Boolean; omitted by default | CVXPY 1.8+ can recover an `InsufficientProgress` iterate when both primal and dual vectors exist. CVXPY 1.7.5 rejects this keyword. In 1.9.3, presence of the keyword enables recovery even with `False`; omit it to disable recovery. Finance reports the recovered candidate without an optimality proof and still checks its original financial constraints. |

Finance rejects route overrides `solver`, `solver_path`, `gp`, `qcp`, and `requires_grad`. Provider-specific unsupported names raise rather than being ignored. The installed [CVXPY solve API](https://www.cvxpy.org/tutorial/solvers/index.html) governs canonicalization controls; direct SCIP bypasses this interface and accepts only the two fields below.

CVXPY 1.9 also exposes `nlp: bool = False` to select its nonlinear-programming route. Finance's Clarabel and SCIP interfaces use convex/conic canonicalization; leave `nlp` omitted or false. `nlp=True` selects a provider route that does not support these solver selections and raises. Earlier CVXPY versions reject it as an unknown solver option. The versioned [Clarabel interface](https://github.com/cvxpy/cvxpy/blob/v1.9.3/cvxpy/reductions/solvers/conic_solvers/clarabel_conif.py) defines the recovery behavior above.

## Clarabel settings

Pass fields directly as solve keywords. The table covers every field of Clarabel 0.11.1's Python `DefaultSettings`; Finance/CVXPY makes verbosity false by default. `uint32` means a Python integer in `[0, 2**32-1]`; `float` means a real floating-point setting. The native settings validator checks string choices and requires a direct KKT solver, but does not generally sanity-check numeric ranges. For meaningful numerical controls, use nonnegative tolerances, positive scaling/regularization magnitudes, ordered scaling bounds, and step fractions in `(0,1)`. These numerical conditions describe appropriate algorithm inputs rather than additional Finance validation. Defaults below are from the Python runtime and [versioned settings contract](https://raw.githubusercontent.com/oxfordcontrol/Clarabel.rs/v0.11.1/src/solver/implementations/default/settings.rs).

| Field | Type | Default | Meaning |
| --- | --- | --- | --- |
| `max_iter` | `uint32` | `200` | Iteration cap. |
| `time_limit` | `float` | `float("inf")` | Runtime seconds. |
| `verbose` | `bool` | `False` through CVXPY | Solver output. |
| `max_step_fraction` | `float` | `0.99` | Maximum step fraction. |
| `tol_gap_abs` | `float` | `1e-8` | Absolute duality gap. |
| `tol_gap_rel` | `float` | `1e-8` | Relative duality gap. |
| `tol_feas` | `float` | `1e-8` | Primal/dual feasibility tolerance. |
| `tol_infeas_abs` | `float` | `1e-8` | Absolute infeasibility threshold. |
| `tol_infeas_rel` | `float` | `1e-8` | Relative infeasibility threshold. |
| `tol_ktratio` | `float` | `1e-6` | Homogeneous embedding ratio threshold. |
| `reduced_tol_gap_abs` | `float` | `5e-5` | Reduced-accuracy absolute gap. |
| `reduced_tol_gap_rel` | `float` | `5e-5` | Reduced-accuracy relative gap. |
| `reduced_tol_feas` | `float` | `1e-4` | Reduced-accuracy feasibility. |
| `reduced_tol_infeas_abs` | `float` | `5e-12` | Reduced-accuracy absolute infeasibility. |
| `reduced_tol_infeas_rel` | `float` | `5e-5` | Reduced-accuracy relative infeasibility. |
| `reduced_tol_ktratio` | `float` | `1e-4` | Reduced-accuracy embedding ratio. |
| `equilibrate_enable` | `bool` | `True` | Enable data equilibration. |
| `equilibrate_max_iter` | `uint32` | `10` | Scaling iteration cap. |
| `equilibrate_min_scaling` | `float` | `1e-4` | Minimum scaling factor. |
| `equilibrate_max_scaling` | `float` | `1e4` | Maximum scaling factor. |
| `linesearch_backtrack_step` | `float` | `0.8` | Backtracking multiplier. |
| `min_switch_step_length` | `float` | `0.1` | Asymmetric-cone scaling-switch threshold. |
| `min_terminate_step_length` | `float` | `1e-4` | Small-step termination threshold. |
| `max_threads` | `uint32` | `0` | Linear-solver threads; zero automatic. |
| `direct_kkt_solver` | `bool` | `True` | Direct KKT solve; must remain true. |
| `direct_solve_method` | `str` | `"auto"` | `"auto"`, `"qdldl"`, or build-enabled `"faer"`, `"mkl"`, `"panua"`; Pardiso choices also require an available runtime. |
| `static_regularization_enable` | `bool` | `True` | Enable static regularization. |
| `static_regularization_constant` | `float` | `1e-8` | Static diagonal shift. |
| `static_regularization_proportional` | `float` | `4.930380657631324e-32` | Diagonal-relative static shift. |
| `dynamic_regularization_enable` | `bool` | `True` | Enable dynamic regularization. |
| `dynamic_regularization_eps` | `float` | `1e-13` | Dynamic pivot threshold. |
| `dynamic_regularization_delta` | `float` | `2e-7` | Dynamic pivot shift. |
| `iterative_refinement_enable` | `bool` | `True` | Refine linear solves. |
| `iterative_refinement_reltol` | `float` | `1e-13` | Relative refinement tolerance. |
| `iterative_refinement_abstol` | `float` | `1e-12` | Absolute refinement tolerance. |
| `iterative_refinement_max_iter` | `uint32` | `10` | Refinement iteration cap. |
| `iterative_refinement_stop_ratio` | `float` | `5.0` | Refinement stalling threshold. |
| `presolve_enable` | `bool` | `True` | Presolve constraint reduction. |
| `input_sparse_dropzeros` | `bool` | `False` | Drop explicit sparse zeros. |
| `chordal_decomposition_enable` | `bool` | `True` | Decompose semidefinite cones. |
| `chordal_decomposition_merge_method` | `str` | `"clique_graph"` | `"clique_graph"`, `"parent_child"`, or `"none"`. |
| `chordal_decomposition_compact` | `bool` | `True` | Compact decomposed system. |
| `chordal_decomposition_complete_dual` | `bool` | `True` | Complete decomposed PSD dual. |
| `pardiso_iparm` | `list[int32]` | 64 entries of `-2147483648` | Signed 32-bit integer sequence of length 64; sentinel entries keep Pardiso defaults. |
| `pardiso_verbose` | `bool` | `False` | Pardiso output. |

When Finance records numerical financial-unit scaling, omitted `tol_feas`, `tol_gap_rel`, and `tol_gap_abs` become `min(native_default, tolerance * 2**(-maximum_coordinate_exponent))`, evaluated with binary floating-point scaling. The exponent comes from the inspection record. Explicit `tol_gap_abs` and `reduced_tol_gap_abs` are interpreted in source objective units and converted. Requested/numerical options and restored dual units are retained in results. See the [Clarabel settings guide](https://clarabel.org/stable/api_settings/) for the underlying interior-point method.

The result's `settings` record reconstructs scalar native defaults and supplied overrides. It omits list-valued `pardiso_iparm` and does not incorporate CVXPY's separate `solver_verbose` logging override. `requested_options` retains the supplied controls; `numerical_options` retains the converted controls when financial-unit scaling applies.

## SCIP controls

`scip_params` is a dictionary of native parameter-name strings to typed values. Default `{}` retains backend defaults, except Finance's direct-execution feasibility settings below. `verbose` is a Python boolean, default `False`. Direct SCIP accepts exactly these two top-level options. CVXPY-backed SCIP also accepts common CVXPY controls and native parameter names as direct keywords; prefer `scip_params` for consistent routing. In that interface, dictionary entries take precedence over duplicate direct native names.

The complete [SCIP parameter catalogue](scip-parameters.md) lists every native name, type, range, default, and meaning for the documented build. Unknown names and incompatible values are rejected by SCIP. The installed solver is authoritative when a different supported build exposes another catalogue; `Model.getParams()` supplies current values and `Model.writeParams(..., comments=True, onlychanged=False)` supplies full type/range/default descriptions without running optimization.

Finance's direct SCIP execution starts with `numerics/feastol=1e-9`, unless explicitly overridden. If this is tighter than the native default and `numerics/epsilon` is omitted, it reduces epsilon in proportion, bounded below by `1e-20`. CVXPY-backed execution retains that interface's setup: for a continuous linear problem it disables presolve, heuristics, and propagation to obtain dual information.

For CVXPY-backed execution with native statistics available, `settings` records actual values of `limits/time`, `limits/gap`, `limits/nodes`, `numerics/feastol`, `numerics/epsilon`, `randomization/randomseedshift`, `parallel/maxnthreads`, and every key supplied in `scip_params`. Additional native names passed directly as keywords remain in `requested_options` but are not automatically added to `settings`. Older CVXPY interfaces may not expose the native model: then `native_statistics_available=False`, `settings` contains only supplied `scip_params`, and the native version, bound, and gap are `None`.
