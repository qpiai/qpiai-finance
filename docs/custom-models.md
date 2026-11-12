# Custom financial models and compilation

Use shared financial calculations and supported model exports to express a decision beyond a predefined workflow. Keep the financial inputs, objective, constraints, and verification explicit. QpiAI Opt supplies algebra and computational representations; Finance supplies reusable financial mathematics and interpretation.

For quantum-inspired and gate-based research, begin with a financial model whose variables have a defined economic meaning. Select a representation that retains those meanings through decoding. The direct [portfolio compiler](quantum.md) provides one such workflow; exported Opt models support additional explicit compilation under Opt's domain and encoding rules.

## Reuse financial mathematics

The following operations can support a custom formulation or its independent evaluation:

| Financial calculation | Reference |
| --- | --- |
| Return conversion, compounding, as-of data filtering, explicit moment scaling | [Data](data.md) |
| Weighted upper-loss-tail risk and an expected-shortfall epigraph for Opt/CVXPY | [Risk](risk.md) |
| Factor covariance products, exposures, and risk contributions | [Risk](risk.md) |
| Supplied scenarios, path aggregation, conditional expectations, nonanticipativity checks | [Scenarios](scenarios.md) |
| Bullet-loan cash flows, supplied-factor discounting, currency valuation | [Cash flows](cashflows.md) |
| Per-ticket fees and numeric or convex CVXPY impact costs | [Trading costs](trading-costs.md) |
| Quota-share or excess-of-loss recovery calculations | [Reinsurance](insurance.md) |
| Supplied haircut and FX valuation | [Collateral](collateral.md) |

For a custom expected-shortfall objective, add all constraints returned by `expected_shortfall_epigraph`; its expression is an upper bound that becomes the requested risk term in the documented minimization or upper-limit use. Recalculate the actual scenario losses and expected shortfall from the resulting primary decision. Costs, covariance uncertainty, and cash terms need their stated units and valid curvature.

## Export a financial formulation

Every supported financial model provides:

```python
model.to_model(*, return_variables=False)
model.to_cvxpy()
```

These operations require no authentication and do not solve. Availability depends on the configured mathematical formulation, as defined by the individual model reference.

`to_model` returns an independent Opt `Model` for a supported Opt formulation. With the Python boolean `return_variables=True`, it returns `(opt_model, financial_expressions)`. The expression dictionary uses labeled domain coordinates: weights, quantities, allocations, cash, schedules, or other expressions documented for that model. Use these expressions rather than depending on private generated variable names when adding a financial rule.

`to_cvxpy` returns `(problem, financial_expressions)` for its supported CVXPY formulation. The expressions belong to that returned problem. Their curvature still governs which constraints or objectives can be added. A normalized risk-budget weight, for instance, need not be affine or suitable for an added DCP constraint.

Exports are detached. Adding a constraint, replacing an objective, or changing a bound on the export does not modify the original Finance model. Calling Finance `solve` on the original model therefore solves the original financial specification. To execute an edited export, use its actual computational API and verify the added financial rules in addition to Finance's original evaluation.

## Linear matrix exports

`ExecutionModel`, `TradingModel`, `LiabilityMatchingModel`, `ReinsuranceModel`, `CollateralAllocationModel`, and `SettlementModel` expose `to_matrix()` for their supported linear formulations. The dictionary uses the Opt matrix contract: objective coefficients and offset, sense, variable names and bounds, integrality, sparse constraint matrix, constraint names, and lower/upper row bounds. Domain references define restrictions on when this export is available.

For `n` variables and `m` constraint rows, the fields are:

| Field | Type and meaning |
| --- | --- |
| `name` | String identifying the financial formulation. |
| `problem_type` | String `"LP"` or `"MILP"`. |
| `format` | String `"matrix"`. |
| `sense` | String `"min"` or `"max"`. |
| `variable_names` | List of `n` strings defining column order. |
| `objective` | Finite floating NumPy array of shape `(n,)`; objective is `objective @ x + objective_offset`. |
| `objective_offset` | Finite float constant in objective units. |
| `constraint_matrix` | SciPy CSR matrix of shape `(m,n)` with finite floating coefficients. |
| `constraint_names` | List of `m` strings defining row order. |
| `row_lower`, `row_upper` | Floating NumPy arrays of shape `(m,)`; infinite bounds denote an absent side. Equal endpoints define equality rows. |
| `lower_bounds`, `upper_bounds` | Floating NumPy arrays of shape `(n,)` in exported coordinate units; infinite bounds denote an absent side. |
| `integrality` | Integral NumPy array of shape `(n,)`; `0` means continuous and `1` means integer. Binary domains combine `1` with bounds `[0,1]`. |

Rows encode `row_lower <= constraint_matrix @ x <= row_upper`. Variable integrality and quantity units must be retained. An external solver translation must preserve objective offsets, minimization/maximization sense, and source coordinates; matching matrix dimensions alone is insufficient. The [Opt matrix reference](https://github.com/qpiai/qpiai-opt/blob/main/docs/api-solvers.md) defines the supported native dictionary fields.

`TradingModel.to_scip()` additionally exposes its supported exact SCIP formulation and labeled financial expressions. It is distinct from a CVXPY conic representation. Its model reference explains nonlinear cost and cash-reconstruction conditions.

## Explicit Opt compilation

An exported Opt `Model` supports `opt_model.compile(target=None, **options)`. Compilation selects a mathematical representation without authentication or execution. `target=None` uses the detected class, normalizing detected `MIP` to `MILP`. Explicit case-insensitive targets are exactly `"LP"`, `"MILP"`, `"QP"`, `"QUBO"`, `"HUBO"`, and `"ISING"`; explicit `"MIP"` is rejected. Finance does not add a second generic compilation interface.

| Target | Return type | Accepted options and restrictions |
| --- | --- | --- |
| `LP`, `MILP` | Opt `MILPProblem` with independent source snapshot | Only `config=None`, a `MILPSolverConfig` or validated field dictionary; fields are in the [solver reference](solver-options.md#platform-lpmilp-configuration). Explicit LP rejects retained integer decisions. |
| `QP` | Independent Opt `Model` | No options. Continuous quadratic matrix export and curvature checks must succeed. |
| `QUBO` | Opt `QUBOProblem` | Encoding/penalty controls below, plus positive non-Boolean integer `max_evaluations=10000` for the platform container and optional `solver_config=None`. Objective/constraint compilation must produce degree at most two. |
| `HUBO` | Opt `HUBOProblem` | Encoding/penalty controls below and optional `solver_config=None`. Higher source polynomial degree is retained. |
| `ISING` | Opt `IsingProblem` | Encoding/penalty controls below for supported binary/nonbinary sources. Native all-spin sources accept no options. Pairwise source degree is required. |

Unknown targets raise Opt `ModelValidationError`; unknown options raise `TypeError`. Unsupported financial exports still fail at `to_model` before generic compilation. Successful compilation retains an independent source decoder; a failed compilation restores the preceding compilation state rather than publishing a partial mapping.

### Encoding and penalty controls

For QUBO/HUBO and non-spin Ising targets, the complete shared controls are:

| Option | Type, allowed values, default, and meaning |
| --- | --- |
| `continuous_bits` | Positive non-Boolean integral count or `None` (default). A nonfixed continuous variable on `[lower, upper]` receives `2**bits` uniformly spaced levels, including endpoints; step is `(upper-lower)/(2**bits-1)`. Cannot combine with precision. |
| `continuous_precision` | Nonnegative non-Boolean integral decimal-place count or `None` (default). Step is `10**(-precision)` from the declared lower bound. The interval width must be a whole number of steps; the lower bound need not itself be a step multiple. Cannot combine with bits. |
| `max_bits` | Non-Boolean integral value in `[1,53]`, default `20`. Per-continuous-variable bit ceiling; a requested/generated resolution above it raises. |
| `strict_penalties` | Python boolean, default `False`. An explicitly configured hard-constraint weight below Opt's sufficient threshold emits `UserWarning`; true instead raises `ConstraintValidationError`. Omitted weights use automatic sufficient selection in either mode. |

Finite variable bounds are required for integer/continuous binary encodings. A continuous resolution is never inferred by `compile`; omitted bits and precision raise when a continuous variable requires encoding. Fixed continuous variables still require the explicit resolution setting at this interface but introduce no free bits. Integers use exact bounded binary weights; fixed-point variables use their declared decimal grid. Binary variables need no domain encoding. Semi-continuous, semi-integer, mixed, and spin/non-spin mixtures are not generic binary compilation domains. Indicators and SOS are not converted by the polynomial path.

QUBO's packaged matrix is symmetric: mirrored off-diagonal entries share the direct polynomial coefficient. `compile(target="QUBO")` does not accept `matrix_format`; for raw upper/symmetric export use `opt_model.to_qubo_dict(matrix_format="symmetric", **encoding_options) -> (dict[tuple[int, int], float], float)`. The second tuple item is the constant offset. Canonical formats are `"symmetric"` and `"upper"`; aliases are `"fully_symmetric"` and `"upper_triangular"`. Names are stripped, lowercased, and hyphens become underscores before validation.

`to_hubo_dict(**encoding_options)` returns `dict[tuple[str, ...], float]`, a minimization polynomial whose empty-tuple key is the constant. `to_ising_dict(**encoding_options)` returns a dictionary with `problem_type="ISING"`, `num_variables: int`, source `sense: str` (`"MIN"` or `"MAX"`), `offset: float`, `variable_names: tuple[str, ...]`, `linear: dict[int, float]`, and `quadratic: dict[tuple[int, int], float]`. Its coefficients and offset use the stated source sense; spins are `-1/+1`. These methods update the retained export's decoding maps and do not solve.

QUBO `solver_config` accepts `dict[str, Any] | None` at the Opt container boundary. It is opaque platform configuration rather than an encoding control: the SDK defines no public platform key allowlist or per-key defaults, and acceptance by the container does not establish acceptance by a particular server resource. Local execution accepts only stored `num_reads`, `num_sweeps`, and `seed` with the [local domains](solver-options.md#opt-local-options). HUBO `solver_config` has exactly the [platform HUBO keys](solver-options.md#platform-polynomial-controls); local execution again accepts only the read/sweep/seed subset. Ising compilation has no solver-configuration argument. Container configuration does not authorize a platform route.

Hard equalities receive nonnegative residual penalties; inequalities use supported exact binary identities or bounded slack on the expression's rational coefficient lattice. Automatic weights separate the infeasible energy from the complete unconstrained objective range. Weights belong to configured Opt constraints, not a generic `penalty=` compile keyword. For a custom exported rule, `opt_model.add_constraint(constraint, penalty_weight=None, label=None)` returns the supplied constraint and uses automatic weighting by default; explicit weights are finite positive non-Boolean reals. An explicit `label` is a nonempty, unique single-line string without NUL characters; `None` uses the constraint's effective or generated name. `opt_model.estimate_penalty_weight(constraint, **encoding_options) -> float` estimates on a snapshot after the objective is set. The selector is a constraint object, effective label, or zero-based non-Boolean integer index; a redundant constraint returns zero. Custom soft penalties are not hard-feasibility conditions and have no automatic hard weight.

QUBO/Ising compilation does not silently reduce a higher-degree objective. For a higher-order source, retain `HUBO`, or use Opt's explicit recorded HUBO-to-QUBO conversion with product mapping and sufficient strength. The direct [portfolio compiler](quantum.md#objective-and-penalty-meaning) performs that recorded conversion for its supported financial selection workflow.

For a valid Opt export, binary compilation may require finite variable bounds, a continuous grid, and constraint penalty controls. Exact bounded integer encodings and explicit discretization of a continuous decision are different operations. A continuous grid restricts the set of admissible positions and can change the attainable financial optimum. Record its resolution and assess its effect on the required financial quantities.

HUBO retains supported higher-order polynomial terms. Pairwise QUBO and Ising have their own degree/conversion requirements. Indicators, SOS, unsupported variable domains, curvature, coefficient ranges, and downstream solver capacity follow Opt's actual compilation contract; the existence of `to_model` does not imply every target accepts every exported formulation.

Use these Opt references for precise controls and failure conditions:

- [Modeller API](https://github.com/qpiai/qpiai-opt/blob/main/docs/api-modeller.md): targets, bounds, source evaluation, and compilation methods.
- [QUBO modeling](https://github.com/qpiai/qpiai-opt/blob/main/docs/qubo-modeller.md): variable grids, constraints, penalties, and decoding.
- [HUBO modeling](https://github.com/qpiai/qpiai-opt/blob/main/docs/hubo-modeller.md): higher-order polynomial representation and supported encodings.
- [Ising modeling](https://github.com/qpiai/qpiai-opt/blob/main/docs/ising-modeller.md): spin convention, offsets, and source conversion.
- [Transformation inspection](https://github.com/qpiai/qpiai-opt/blob/main/docs/transformations.md): retained maps and sample decoding.

## Execute and restore the decision

For unchanged supported Finance models, root `solve` provides automatic financial reconstruction and checks. For an explicitly compiled or edited Opt export, execute through `qpiai_opt.opt_solvers.solve` with its actual authentication and execution configuration. Gate-based execution uses Opt algorithms and `QuantumRun`. Read [execution boundaries](solving.md) before selecting local or paid platform work.

Retain the original Finance model, the exact exported Opt model after compilation, its transformations and variable order, and the typed Opt result. For supported records, `qpiai_finance.results.from_opt` restores financial coordinates and recalculates the original Finance constraints and objective. General polynomial/gate recovery requires the retained `opt_model` decoder; a bare coefficient dictionary is insufficient.

Recovery checks complete coordinates and original financial feasibility. It does not bind a historical proof to the exact model that was executed, and therefore does not establish a new financial optimality proof. General retained-model recovery also has a narrower encoded verification scope than the direct `PortfolioEncoding`: read [result recovery](results.md) for the energy, auxiliary, and source checks.

If an export contains additional financial constraints, independently verify them as well. If its objective has changed, Finance's original objective remains an evaluation of the original financial model and may correctly disagree with the edited solver objective. Do not relabel the edited model's optimum as a verified optimum of an unchanged Finance specification.

## Solver interoperability

Finance's root `solve` accepts only its documented solver names. A CVXPY export can be used with another separately installed compatible solver through CVXPY's API; this does not create a new Finance `solver` option or package that solver's license. Use the [CVXPY solver capability reference](https://www.cvxpy.org/tutorial/solvers/index.html) to match integer domains and required cones. Preserve source feasibility, cash accounting, objective units, and proof scope when restoring such a result in the application.

Custom models and edits on detached exports are not serialized by Finance's model interchange. Save their specifications using the owning modeling system and retain the financial inputs needed for independent verification. The standard Finance [interchange](interchange.md) applies to its exact supported models, scenarios, and result types.
