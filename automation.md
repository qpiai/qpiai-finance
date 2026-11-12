# Automation and agent workflows

Use this guide to choose a financial operation, construct the correct model, select execution, and verify its result. The linked manual defines financial assumptions, signatures, parameters, and outputs.

## Establish the task

1. Identify the financial decision: weights, trades, funding, hedge quantities, facility allocations, contracts, collateral assignments, or payment schedules.
2. Obtain the authoritative inputs, identifiers, units, currency, dates, return horizon, objective, and hard constraints. Keep forecasts separate from observations that become available later.
3. Establish the required guarantee, verification tolerance, compute budget, and permitted execution routes. Select paid execution only when the caller has authorized it.
4. Select the applicable model or reusable calculation below. Read its complete input and method contract before calling it. Do not infer parameters from a similarly named API in another library.

For quantum-inspired or gate-based work, start from the financial decision and retain its interpretation through compilation, execution, and recovery.

## Discover the installed API

```python
from importlib.metadata import version

from qpiai_finance.automation import capabilities, guide

installed_version = version("qpiai-finance")
entry_point = guide()
catalog = capabilities()
```

`guide(document="automation.md")` returns the installed entry point as a string. Its other accepted document is `"README.md"`; another name raises `ValueError`. In a source checkout it reads the current file. In an installed distribution it reads packaged documentation. A missing document raises `FileNotFoundError`.

`capabilities()` returns a dictionary with `schema_version`, distribution and version, task records, public operation signatures and docstrings, and execution capabilities. Each task contains `purpose`, `reference`, and `api`. Class API records contain callable public methods; properties and detailed data contracts are defined in the manual. The execution record includes Opt provider capabilities, installed Clarabel/SCIP availability, allowed modes, and authentication requirements. This operation does not authenticate, optimize, or submit work. Availability alone does not prove that a particular model is feasible.

The returned dictionary is JSON-compatible and has this schema:

| Field | Type and value |
| --- | --- |
| `schema_version` | Integer `1`. |
| `distribution` | String `"qpiai-finance"`. |
| `version` | Installed distribution version as a string. |
| `automation_guide` | String `"qpiai_finance.automation.guide()"`. |
| `tasks` | Dictionary keyed by task identifier. Each value contains `purpose: str`, `reference: str` (a relative README link), and `api: list[dict]`. |
| `operations` | Dictionary with keys `"inspect"`, `"validate"`, and `"solve"`. Each value is an API record with the additional boolean `authentication_required`, true only for `solve`. |
| `execution` | Dictionary described below. |

An API record contains `import: str` (the qualified import name), `kind: "class" | "function"`, `signature: str`, and `documentation: str`. An unavailable docstring produces an empty string. A class record also contains `methods`, a dictionary keyed by public callable name. Each method record contains `signature: str` and `documentation: str`. Signatures reflect the installed Python objects; an unbound method signature can include `self`.

| `execution` field | Type and value |
| --- | --- |
| `default_mode` | String `"local"`. |
| `modes` | List `['local', 'auto', 'platform']`; individual routes impose further restrictions. |
| `automatic_paid_fallback_by_default` | Boolean `False`. |
| `auto_platform_permission` | String `"allow_platform=True"`. |
| `external_solver_modes` | List `['local']`. |
| `gate_algorithm_modes` | List `['local', 'platform']`. |
| `opt_providers` | List of Opt provider capability dictionaries. Each contains `name: str`, `mode: str`, `problem_classes: list[str]`, `exact: bool`, `heuristic: bool`, `requires_authentication: bool`, `diagnostics: list[str]`, and `problem_capabilities: dict[str, dict]`. Each problem-class record has boolean `exact` and `heuristic` fields; use these class-specific flags when selecting a route. |
| `external_solvers` | Dictionary with boolean `clarabel` and `scip` values indicating availability through the installed CVXPY solver interfaces. |
| `all_solves_require_opt_authentication` | Boolean `True`. |
| `finance_gate_based_execution` | Boolean `True`. |

The `tasks` dictionary uses these identifiers. Each entry follows the task/API record schema above.

| Task identifier | API records |
| --- | --- |
| `multi_period_investment` | `TradingModel`. |
| `execution_scheduling` | `ExecutionModel`. |
| `result_interchange` | `FinanceResult`, `FrontierResult`, and the six public `io` functions. |
| `settlement` | `SettlementModel`. |
| `reinsurance` | `ReinsuranceModel`, `excess_of_loss`, and `quota_share`. |
| `collateral_allocation` | `CollateralAllocationModel` and `haircut_adjusted_value`. |
| `credit_allocation` | `CreditAllocationModel`. |
| `portfolio` | `PortfolioModel`. |
| `funding` | `FundingModel`. |
| `liability_matching` | `LiabilityMatchingModel`. |
| `hedging` | `HedgeModel`. |
| `discount_cash_flows` | `bullet_loan_cash_flows`, `discount_cash_flows`, and `present_value`. |
| `scenarios` | `Scenarios`, `ScenarioPaths`, and `ScenarioTree`. |
| `model_interchange` | The six public `io` functions. |
| `trading_costs` | Public functions in `trading.costs`. |
| `risk` | Public functions and classes in `risk`. |
| `data` | Public functions in `data`. |
| `binary_portfolio` | `compile_portfolio` and `PortfolioEncoding`. |
| `plotting` | Public functions in `plot`. |
| `opt_result_recovery` | `results.from_opt`. |

Use the installed version and signatures when detecting a mismatch with external documentation. Do not use a package from another environment to infer the current API. The published HTML manual provides Markdown links and `llms.txt`. Locate the reference body in the current environment as follows. Distribution metadata supplies its usual installed location; the additional paths support source checkouts and `pip --target` installations:

```python
from importlib.metadata import distribution
from pathlib import Path

import qpiai_finance

package = distribution("qpiai-finance")
project = Path(qpiai_finance.__file__).resolve().parent.parent
candidates = [
    Path(package.locate_file(entry)) for entry in package.files or []
    if entry.as_posix().endswith("/doc/qpiai-finance/docs/index.md")
]
if (project / "pyproject.toml").is_file():
    candidates.insert(0, project / "docs" / "index.md")
candidates.append(
    project / "share" / "doc" / "qpiai-finance" / "docs" / "index.md"
)
manual_path = next((path for path in candidates if path.is_file()), None)
if manual_path is None:
    raise FileNotFoundError("The Finance manual is not installed")
```

Read `manual_path` and resolve its relative chapter links from that directory. The public [manual](docs/index.md) is the same reference body.

## Select a capability

| Task | Public API | Required reference |
| --- | --- | --- |
| Construct or rebalance a portfolio; risk budgets or frontier | `portfolio.PortfolioModel` | [Portfolios](docs/portfolio.md) |
| Encode equal-weight selection; sample or gate-based research | `quantum.compile_portfolio`, `quantum.PortfolioEncoding` | [Quantum-inspired and gate-based optimization](docs/quantum.md) |
| Build a custom financial formulation or extend a detached model | Shared finance calculations; model `to_model`/other supported exports | [Custom models and compilation](docs/custom-models.md) |
| Plan adaptive trades, cash, funding, and terminal wealth | `trading.TradingModel` | [Investment planning](docs/trading.md) |
| Schedule signed orders across intervals and venues | `trading.ExecutionModel` | [Execution scheduling](docs/execution.md) |
| Match exposures or hedge supplied scenario P&L | `hedging.HedgeModel` | [Hedging](docs/hedging.md) |
| Allocate credit within funding, capital, and risk limits | `credit.CreditAllocationModel` | [Credit](docs/credit.md) |
| Plan cash, debt, investments, facilities, and transfers | `treasury.FundingModel` | [Funding](docs/funding.md) |
| Purchase assets to meet dated liabilities | `treasury.LiabilityMatchingModel` | [Liability matching](docs/liability-matching.md) |
| Select reinsurance contracts or programs | `insurance.ReinsuranceModel` | [Insurance](docs/insurance.md) |
| Calculate stated layer or quota-share payouts | `insurance.excess_of_loss`, `insurance.quota_share` | [Insurance](docs/insurance.md) |
| Assign dated collateral inventory | `collateral.CollateralAllocationModel` | [Collateral](docs/collateral.md) |
| Calculate haircut-adjusted collateral value | `collateral.haircut_adjusted_value` | [Collateral](docs/collateral.md) |
| Schedule payments and permitted atomic batches | `settlement.SettlementModel` | [Settlement](docs/settlement.md) |
| Prepare returns or filter observations as of a decision | `data` | [Data](docs/data.md) |
| Estimate risk or construct financial risk terms | `risk` | [Risk](docs/risk.md) |
| Construct scenarios, paths, or information trees | `scenarios` | [Scenarios](docs/scenarios.md) |
| Calculate loan cash flows or discount supplied flows | `cashflows` | [Cash flows](docs/cashflows.md) |
| Calculate fees or supplied impact terms | `trading.costs` | [Trading costs](docs/trading-costs.md) |
| Save or restore supported models, scenarios, and results | `io` | [Interchange](docs/interchange.md) |
| Recover a recorded Opt result or replay a financial decision | `results.from_opt`, `FinanceResult.evaluate` | [Results](docs/results.md) |
| Plot supported financial result records | `plot` | [Plotting](docs/plotting.md) |

Namespaces in the table are relative to `qpiai_finance`. Use the [API index](docs/public-api.md) for imports and the [manual](docs/index.md) for the full reference body.

## Prepare and inspect

1. Align inputs by their financial identifiers. Use [data conventions](docs/data.md) for labeled inputs, numeric values, dates, covariance, and horizon semantics.
2. Construct the selected model. Apply its public objective and constraint methods. Complete all required financial settings before compiling.
3. Call `validate(model)` to validate the representation and obtain its mathematical class. Validation does not prove feasibility.
4. Call `inspect(model)` to read the financial specification, representation, and applicable size or route information. An inspection report may contain complete source data; do not log it to an unapproved destination.
5. Choose the representation and execution route from the inspected model and the caller's policy. Retain the source model and any compiled representation and recovery metadata.

```python
from qpiai_finance import inspect, validate

problem_class = validate(model)
report = inspect(model)
```

These operations require no credentials and do not solve or submit jobs. Read [solving](docs/solving.md) for the report fields and route restrictions.

## Choose a computational route

Use the simplest supported representation that preserves the financial objective and hard constraints. Do not replace holdings with arbitrary selection bits or discard constraints to fit a preferred algorithm.

| Required route | Procedure |
| --- | --- |
| Finance's supported direct binary portfolio formulation | Configure equal-weight `select_assets`; call `compile_portfolio` with the desired `representation`; inspect the returned encoding. |
| Native higher-order polynomial solving | Retain `representation="hubo"`; execute through Opt. |
| Gate-based portfolio optimization | Compile to `"qubo"` or `"ising"`; construct an authoritative Opt algorithm; call `inspect(encoding, algorithm=algorithm)`; select `QuantumRun` and an explicit local/platform mode. |
| Explicit Opt compilation of another supported financial formulation | Export its detached Opt model; compile with supported Opt options; retain the exact Opt model with its decoding metadata; recover the result against the original financial model. |
| Standard financial optimization or construction | Call Finance `solve(model, ...)` with the appropriate default or an explicitly supported solver. |
| Custom financial constraints on an exported model | Solve the exported representation through its supported API and verify the added rules separately; the original Finance model does not acquire those mutations. |

See [quantum](docs/quantum.md) for the direct compiler's supported objectives and constraints, penalty guarantees, higher-order terms, variable order, auxiliaries, sample evaluation, and gate controls. See [custom models](docs/custom-models.md) for detached export semantics and general Opt compilation.

## Execute a blocking solve

Create an Opt client using a credential supplied by the application's secret store. Never place credentials in financial inputs, interchange documents, results, or logs.

```python
import os

from qpiai_opt.opt_solvers import Client
from qpiai_finance import solve

client = Client(api_key=os.environ["QPIAI_OPT_API_KEY"])
result = solve(model, client=client)
```

Every Finance solve requires Opt authentication. Key verification requires connectivity. Modeling, inspection, evaluation, recovery, and interchange do not require authentication. Obtain an Opt key at [QpiAI Opt](https://opt.qpiai.tech/).

| Selection | Call or setting | Execution boundary |
| --- | --- | --- |
| Default local route | `solve(model, client=client)` | Authenticated local execution using the model's supported default solver. |
| Explicit external solver | `solve(model, client=client, solver="clarabel")` or `solver="scip"` | Requires a compatible financial formulation and installed solver. |
| Local-first Opt route | `solve(model, client=client, solver="qpiai", mode="auto")` | Paid fallback remains disabled. |
| Authorized Opt fallback | Add `allow_platform=True` to the local-first route | Can create paid platform work after Opt's supported local-limit failure. |
| Explicit Opt Platform | `solve(model, client=client, solver="qpiai", mode="platform")` | Creates platform work for supported classes and can consume credits. |
| Local gate-based route | `solve(encoding, client=client, algorithm=algorithm, execution=execution)` | Requires additional QCloud authentication. |
| QpiAI gate-based route | Add `mode="platform"` to the gate-based call | Can consume QCloud credits. |

For gates, import algorithms, `QuantumRun`, and `QpiAIQuantumAuth` from `qpiai_opt.quantum`; authenticate with `QpiAIQuantumAuth.login(api_key=...)`. Obtain the QCloud key at [QpiAI QCloud](https://qcloud.qpiai.tech/). Finance's `quantum` namespace contains its financial compiler and encoding, not duplicate algorithm classes. Gate algorithms reject `mode="auto"`, `allow_platform=True`, and arbitrary solve options. Configure them through their algorithm and execution objects.

The `tolerance` argument is Finance's absolute source-check tolerance, in each row's source units. It is not a universal backend tolerance or a relaxation of the financial constraints. Use the [solver option contracts](docs/solver-options.md) to set backend controls and the [algorithm control reference](docs/algorithm-controls.md) for gate configurations.

## Accept or reject the result

1. Read `result.status`, `result.feasible`, `result.optimality_proven`, and `result.solver_info`.
2. If no primary decision exists, report the termination and skip financial decision processing. Do not fabricate holdings, quantities, or a zero objective.
3. If `feasible` is false, inspect `result.constraints` and relevant reconciliation tables. Do not use the candidate as a valid financial decision.
4. If the caller requires a proven optimum, also require `optimality_proven`. A feasible incumbent or best sampled bitstring does not satisfy this requirement.
5. Consume the domain decisions, metrics, costs, and tables only within their documented units and guarantee scope. A fixed-selection optimum is conditional on that selection.
6. Preserve the source model, result, versions, effective settings, transformations, and job identifiers needed by the application. Apply the application's retention and confidentiality policies to these financial records.

Finance recomputes financial objectives and constraints from the recovered decision. Do not substitute the solver-reported cost or encoded energy for that objective. For encoded samples, retain auxiliary validation and source feasibility. See [results](docs/results.md) for fields, statuses, and recovery guarantees.

## Preserve and replay

Use `io.to_dict`, `io.from_dict`, `io.dumps`, `io.loads`, `io.dump`, and `io.load` for reversible supported interchange. Use `FinanceResult.to_dict` or `.to_json` only when a numeric report is sufficient. These are different formats.

Loading a result preserves recorded claims without repeating financial verification. For a trusted source model, call `restored_result.evaluate(model)` to recompute the primary financial decision. This does not authenticate the historical solver evidence or establish a new optimum.

To recover an existing native or transformed Opt result, use `results.from_opt` with the original Finance model or encoding. For general transformed results, retain and supply the actual compiled Opt model. For conditioned raw LP/MILP job results, supply the saved objective-scaling metadata. Keep the typed Opt result when restoring Opt JSON. See [interchange](docs/interchange.md) and [result recovery](docs/results.md).

## Nonblocking Opt work

Finance does not expose its own `submit`, `status`, `result`, or `cancel` functions. For a compatible explicit platform workflow, export the Opt formulation and use the [Opt job API](https://github.com/qpiai/qpiai-opt/blob/main/automation.md#nonblocking-platform-lifecycle).

Submit once and preserve identifiers, the financial model, and the exact submitted representation. Poll or retrieve that job by its existing identifier. After an ambiguous timeout, inspect existing jobs before considering another submission. A polling timeout is not evidence that the job failed or vanished. Recover the completed typed result through Finance's documented recovery operation. Do not infer a Finance proof from matching a recorded objective and coordinates.

## Failure handling

| Failure | Required action |
| --- | --- |
| Invalid type, label, dimensions, units, covariance, or options | Correct the source input using the relevant reference. Do not silently fill, normalize holdings, or remove constraints. |
| Missing capability or incompatible explicit solver | Inspect the formulation and choose a supported route within the caller's policy. |
| Authentication or connectivity failure | Correct authentication or connectivity. Do not authorize another route. |
| Local capacity exceeded | Read Opt's actual limit report. Reduce the workload or select an authorized supported route. |
| Infeasible model | Report infeasibility and relevant diagnostics. Change financial requirements only under the caller's instruction. |
| Resource limit with candidate | Apply the source-feasibility and guarantee checks above. Report the remaining gap or unproven status. |
| Verification failure or objective mismatch | Retain diagnostics and reject the claimed financial guarantee. Do not repair a decision by silent rounding or normalization. |
| Unknown or corrupt interchange format | Reject it. Do not guess a schema version, execute serialized Python, or infer missing financial inputs. |
| Ambiguous submission | Reconcile existing jobs before retrying to avoid duplicate work. |

The library returns proposed financial decisions. It does not place orders, release payments, book loans, or update an accounting ledger.
