"""Financial model compilation, optimization and constraint checks."""

from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
from importlib.metadata import version
from time import perf_counter

import numpy as np
import pandas as pd

from ._serialization import dumps, portable
from ._validation import copy_index, scalar
from .collateral import CollateralAllocationModel
from .credit import CreditAllocationModel
from .hedging import HedgeModel
from .insurance import ReinsuranceModel
from .portfolio import PortfolioModel
from .results import FinanceResult
from .risk import FactorRisk
from .settlement import SettlementModel
from .trading import ExecutionModel, TradingModel
from .treasury import FundingModel, LiabilityMatchingModel


def _require_model(model):
    if not isinstance(
        model,
        (
            PortfolioModel,
            FundingModel,
            LiabilityMatchingModel,
            HedgeModel,
            CreditAllocationModel,
            CollateralAllocationModel,
            ReinsuranceModel,
            SettlementModel,
            ExecutionModel,
            TradingModel,
        ),
    ):
        raise TypeError(
            "expected a PortfolioModel, FundingModel, "
            "LiabilityMatchingModel, HedgeModel, CreditAllocationModel, "
            "CollateralAllocationModel, ReinsuranceModel, SettlementModel, "
            "ExecutionModel or TradingModel"
        )


def _opt_input(model, *, mode, allow_platform=False):
    if mode == "auto":
        # Opt Platform accepts algebraic models, not LP matrix dictionaries.
        mode = "platform" if allow_platform else "local"
    compile_opt = getattr(model, "_compile_opt", None)
    return model.to_model() if compile_opt is None else compile_opt(mode=mode)


def _execution_mode(mode, allow_platform, solver):
    if not isinstance(mode, str) or mode.lower() not in {
        "local", "auto", "platform"
    }:
        raise ValueError("mode must be 'local', 'auto' or 'platform'")
    if not isinstance(allow_platform, bool):
        raise TypeError("allow_platform must be a boolean")
    mode = mode.lower()
    if solver != "qpiai":
        if mode != "local":
            raise ValueError("external solvers use mode='local'")
        if allow_platform:
            raise ValueError("allow_platform applies only to solver='qpiai'")
    return mode


def _specification(model):
    if not isinstance(model, PortfolioModel):
        return model._specification()
    risk = model._covariance
    if isinstance(risk, FactorRisk):
        risk = {
            "type": "factor",
            "asset_ids": risk._assets,
            "factor_ids": risk._factors,
            "exposures": risk._b,
            "factor_covariance": risk._f,
            "specific_variance": risk._d,
        }
    scenarios = model._scenarios
    account = None
    if model._account is not None:
        account = vars(model._account).copy()
        book = model._account.tax_lots
        account["tax_lots"] = None if book is None else book.specification()
    if scenarios is not None:
        scenario_metadata = scenarios.metadata
        scenarios = {
            "values": scenarios._values,
            "probabilities": scenarios._probabilities,
            "scenario_ids": scenarios._ids,
            "asset_ids": scenarios._assets,
            "horizon": scenarios.horizon,
            "unit": scenarios.unit,
            "origin": scenarios.origin,
            **({"metadata": scenario_metadata} if scenario_metadata else {}),
        }
    return portable(
        {
            "model": "PortfolioModel",
            "asset_ids": model._ids,
            "expected_returns": model._mu,
            "covariance": risk,
            "horizon": model._horizon,
            "net_weight": model._net_weight,
            "objective": None
            if model._objective == "hrp"
            else model._objective,
            "method": (
                "hierarchical_risk_parity"
                if model._objective == "hrp"
                else "risk_budgeting"
                if model._objective == "risk_budgeting"
                else "optimization"
            ),
            "risk_aversion": model._risk_aversion,
            "risk_budgets": model._risk_budgets,
            "risk_budget_polish": model._risk_budget_polish,
            "risk_budget_polish_maxiter": model._risk_budget_polish_maxiter,
            "linkage_method": model._linkage_method,
            "moment_preferences": model._moment_preferences,
            "benchmark": model._benchmark,
            "minimum_return": model._minimum_return,
            "lower_weights": model._lower,
            "upper_weights": model._upper,
            "exposures": model._exposures,
            "leverage": model._leverage,
            "turnover": model._turnover,
            "scenarios": scenarios,
            "confidence": model._confidence,
            "downside_target": getattr(model, "_downside_target", None),
            "volatility_limit": model._volatility_limit,
            "return_uncertainty": model._return_uncertainty,
            "selection": model._selection,
            "fixed_selection": model._fixed_selection,
            "account": account,
            "weight_basis": "initial_portfolio_value"
            if model._account is not None
            else "investment_basis",
        }
    )


def validate(model):
    """Validate financial inputs and compiled mathematics without
    authentication.

    This is structural validation, not an assertion that constraints are
    feasible.
    """
    from .quantum import PortfolioEncoding

    if isinstance(model, PortfolioEncoding):
        return model.inspect()["optimization"]["problem_class"]
    _require_model(model)
    if getattr(model, "_requires_scip", False):
        model._compile_scip()
        return model._problem_class
    if model._objective == "moment_utility":
        from .quantum import compile_portfolio

        return compile_portfolio(model).problem.problem_type
    if model._objective == "hrp":
        model._check()
        return "HEURISTIC"
    if model._needs_external:
        model._compile_cvxpy()
        return model._problem_class
    from qpiai_opt.opt_solvers import inspect as opt_inspect

    return opt_inspect(_opt_input(model, mode="local"))["problem_class"]


def inspect(model, *, algorithm=None):
    """Inspect financial settings and Opt's real execution
    capabilities/size limits.
    """
    from qpiai_opt.opt_solvers import inspect as opt_inspect

    from .quantum import PortfolioEncoding

    if isinstance(model, PortfolioEncoding):
        return model.inspect(algorithm=algorithm)
    if algorithm is not None:
        raise ValueError("algorithm inspection requires a PortfolioEncoding")
    _require_model(model)
    if getattr(model, "_requires_scip", False):
        native, variables = model._compile_scip()
        return {
            "financial_model": _specification(model),
            "optimization": {
                "problem_class": model._problem_class,
                "valid": True,
                "representation": "SCIP",
                "default_solver": "scip",
                "convex": model._cash_monotone and not model._mixed_integer,
                "cash_reconstruction": "monotone_cost_epigraph"
                if model._cash_monotone
                else "exact_cost_graph",
                "native_opt_supported": False,
                "variables": len(variables),
                "constraints": native.getNConss(),
                "financial_limits_in_solver": True,
                "financial_limits_checked_on_result": True,
            },
        }
    if model._objective == "moment_utility":
        from .quantum import compile_portfolio

        return compile_portfolio(model).inspect()
    if model._objective == "hrp":
        model._check()
        return {
            "financial_model": _specification(model),
            "optimization": {
                "problem_class": "HEURISTIC",
                "valid": True,
                "method": "hierarchical-risk-parity",
                "default_solver": "hrp",
                "native_opt_supported": False,
                "assets": len(model._ids),
            },
        }
    if model._needs_external:
        solver = _resolve_solver(model, None)
        compiler = getattr(model, "_compile_cvxpy_for_solve", None)
        compiled = (
            model._compile_cvxpy()
            if compiler is None
            else compiler(solver=solver)
        )
        problem = compiled[0]
        construction = model._objective == "risk_budgeting"
        units = {"numerical_units": compiled[2]} if len(compiled) == 3 else {}
        return {
            "financial_model": _specification(model),
            "optimization": {
                "problem_class": model._problem_class,
                "valid": problem.is_dcp(),
                "representation": "CVXPY",
                "default_solver": solver,
                "variables": problem.size_metrics.num_scalar_variables,
                "native_opt_supported": False,
                "financial_limits_in_solver": not construction,
                "financial_limits_checked_on_result": True,
                **units,
            },
        }
    native = _opt_input(model, mode="local")
    optimization = opt_inspect(native)
    from ._solvers.opt import _objective_scale

    optimization["objective_scaling"] = _objective_scale(
        native, model._problem_class
    )
    return {
        "financial_model": _specification(model),
        "optimization": optimization,
    }


def solve(
    model,
    *,
    client=None,
    mode="local",
    solver=None,
    algorithm=None,
    execution=None,
    allow_platform=False,
    tolerance=1e-7,
    **options,
):
    """Optimize a financial model and independently verify its constraints.

    Every solve, including local, requires Opt authentication through
    ``client``. Select Platform directly with mode='platform'.
    Opt's mode='auto' tries local execution and permits
    Platform fallback only with allow_platform=True. Opt owns routing and
    provider options. ``tolerance`` is Finance's absolute
    source-constraint tolerance in each row's source units. It does not
    alter backend feasibility tolerances or financial constraints.
    Gate algorithms and QuantumRun execution settings require an explicit
    PortfolioEncoding and Quantum runtime authentication in addition to Opt.
    """
    from .quantum import PortfolioEncoding, compile_portfolio

    if isinstance(model, PortfolioEncoding) or (
        isinstance(model, PortfolioModel)
        and model._objective == "moment_utility"
    ):
        if solver not in {None, "qpiai"}:
            raise ValueError("binary portfolio encodings use solver='qpiai'")
        encoding = (
            model
            if isinstance(model, PortfolioEncoding)
            else compile_portfolio(model)
        )
        return encoding.solve(
            client=client,
            mode=mode,
            algorithm=algorithm,
            execution=execution,
            allow_platform=allow_platform,
            tolerance=tolerance,
            **options,
        )
    if algorithm is not None or execution is not None:
        raise ValueError(
            "gate execution requires an explicit PortfolioEncoding; "
            "compile a supported financial portfolio first"
        )
    _require_model(model)
    solver = _resolve_solver(model, solver)
    mode = _execution_mode(mode, allow_platform, solver)
    tolerance = scalar(tolerance, "tolerance", minimum=0)
    if client is None:
        raise ValueError(
            "solving requires an authenticated "
            "qpiai_opt.opt_solvers.Client, including locally"
        )
    if solver == "qpiai":
        options["allow_platform"] = allow_platform
    snapshot = deepcopy(model)
    stage_started = perf_counter()
    if solver == "hrp":
        snapshot._check()
        optimization_model = None
    elif solver == "qpiai":
        optimization_model = _opt_input(
            snapshot, mode=mode, allow_platform=allow_platform
        )
    elif getattr(snapshot, "_requires_scip", False):
        optimization_model = snapshot._compile_scip()
    else:
        compiler = getattr(snapshot, "_compile_cvxpy_for_solve", None)
        optimization_model = (
            snapshot._compile_cvxpy()
            if compiler is None
            else compiler(solver=solver)
        )
    build_time = perf_counter() - stage_started
    return _solve_snapshot(
        snapshot,
        optimization_model,
        client=client,
        mode=mode,
        solver=solver,
        tolerance=tolerance,
        options=options,
        build_time=build_time,
    )


def _resolve_solver(model, solver):
    if getattr(model, "_requires_scip", False):
        if solver not in {None, "scip"}:
            raise ValueError(
                "exact nonlinear investment cash costs require solver='scip'"
            )
        return "scip"
    if solver is None:
        if model._objective == "hrp":
            return "hrp"
        if model._objective == "risk_budgeting":
            return "clarabel"
        if model._needs_external:
            return "scip" if model._mixed_integer else "clarabel"
        return "qpiai"
    if solver not in {"qpiai", "clarabel", "scip", "hrp"}:
        raise ValueError("solver must be 'qpiai', 'clarabel', 'scip' or 'hrp'")
    if (model._objective == "hrp") != (solver == "hrp"):
        raise ValueError("HRP requires the hierarchical_risk_parity method")
    if model._objective == "risk_budgeting" and solver == "scip":
        raise ValueError(
            "risk budgeting requires logarithmic cones; "
            "select solver='clarabel'"
        )
    return solver


def _solve_snapshot(
    snapshot,
    optimization_model,
    *,
    client,
    mode,
    solver,
    tolerance,
    options,
    build_time,
):
    stage_started = perf_counter()
    if solver == "qpiai":
        from ._solvers.opt import solve_opt

        problem_class = (
            optimization_model["problem_type"]
            if isinstance(optimization_model, dict)
            and "problem_type" in optimization_model
            else snapshot._problem_class
        )
        solver_solution, solve_info, solver_info = solve_opt(
            optimization_model,
            client=client,
            mode=mode,
            options=options,
            problem_class=problem_class,
        )
    elif solver == "hrp":
        from .portfolio._hierarchical import construct_portfolio

        solver_solution, solve_info, solver_info = construct_portfolio(
            snapshot, client=client, options=options
        )
    elif getattr(snapshot, "_requires_scip", False):
        from ._solvers.scip import solve_scip

        solver_solution, solve_info, solver_info = solve_scip(
            *optimization_model,
            client=client,
            options=options,
            problem_class=snapshot._problem_class,
        )
    else:
        from ._solvers.cvxpy import solve_cvxpy

        options = options.copy()
        solver_solution, solve_info, solver_info = solve_cvxpy(
            *optimization_model,
            client=client,
            options=options,
            solver=solver,
            problem_class=snapshot._problem_class,
            tolerance=tolerance,
        )
        if (
            solver_solution is not None
            and snapshot._objective == "risk_budgeting"
            and snapshot._risk_budget_polish
        ):
            from .portfolio._risk_budgeting import refine_positions

            solver_solution, refinement = refine_positions(
                snapshot, solver_solution, tolerance=tolerance
            )
            solver_info["refinement"] = refinement
    solve_time = perf_counter() - stage_started
    return _financial_result(
        snapshot,
        solver_solution,
        solve_info,
        solver_info,
        tolerance=tolerance,
        build_time=build_time,
        solve_time=solve_time,
    )


def _financial_result(
    snapshot,
    solver_solution,
    solve_info,
    solver_info,
    *,
    tolerance,
    build_time,
    solve_time,
):
    specification = _specification(snapshot)
    stage_started = perf_counter()
    provenance = {
        "input_sha256": sha256(dumps(specification).encode()).hexdigest(),
        "inputs": specification,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "versions": {
            name: version(name)
            for name in (
                "qpiai-finance",
                "qpiai-opt",
                "numpy",
                "scipy",
                "pandas",
            )
        },
        "verification_tolerance": tolerance,
        "probability_sum_tolerance": 1e-12,
    }
    decision = {}
    metrics = {}
    tables = {}
    evaluation = {}
    constraints = pd.DataFrame(
        columns=["value", "lower", "upper", "violation", "satisfied"]
    )
    objective = None
    feasible = optimality_proven = False
    status = solve_info["termination"]
    if solver_solution is not None:
        evaluation = snapshot._evaluate_solution(
            solver_solution, tolerance=tolerance
        )
        objective = evaluation["objective"]
        decision = evaluation["decision"]
        metrics, tables = evaluation["metrics"], evaluation["tables"]
        constraints = evaluation["constraints"]
        feasible = evaluation["feasible"]
        reconciliation = tables.get("solver_reconciliation")
        solver_reconciled = True
        if reconciliation is not None:
            solver_reconciled = bool(reconciliation.within_tolerance.all())
            solver_info["solver_reconciled"] = solver_reconciled
        # A solver optimum must agree with the financial objective.
        backend_objective = solve_info.get("source_objective")
        objective_matches = None
        if objective is not None:
            objective_matches = backend_objective is not None and np.isclose(
                objective, backend_objective, atol=tolerance, rtol=1e-7
            )
        solver_info["objective_reconciled"] = (
            None if objective_matches is None else bool(objective_matches)
        )
        solver_info["finance_objective"] = objective
        optimality_proven = (
            feasible
            and bool(solve_info["optimality_proven"])
            and bool(objective_matches)
            and solver_reconciled
        )
        if not feasible:
            status = "verification_failed"
        elif solve_info["optimality_proven"] and not objective_matches:
            status = "objective_mismatch"
        elif solve_info["optimality_proven"] and not solver_reconciled:
            status = "feasible"
    objective_unit = snapshot._objective_unit
    if snapshot._objective == "hrp":
        tables["hierarchy"] = pd.DataFrame(
            solver_info["linkage"],
            columns=["left", "right", "distance", "size"],
        )
        tables["cluster_order"] = pd.DataFrame(
            {
                "asset_id": solver_info["asset_order"],
            }
        )
    provenance["timing_s"] = {
        "build": build_time,
        "solve": solve_time,
        "postprocess": perf_counter() - stage_started,
    }
    transformations = evaluation.get("transformations", [])
    if "numerical_units" in solver_info:
        transformations.append(solver_info["numerical_units"])
    if "objective_scaling" in solver_info:
        transformations.append(
            {
                key: value
                for key, value in solver_info["objective_scaling"].items()
                if key != "provider_values"
            }
        )
    if (
        isinstance(snapshot, PortfolioModel)
        and snapshot._fixed_selection is not None
    ):
        solver_info["optimality_scope"] = "fixed_asset_selection"
        transformations.append(
            {
                "type": "fixed_asset_selection",
                "selected": portable(
                    pd.Series(
                        snapshot._fixed_selection,
                        index=copy_index(snapshot._ids),
                        name="selection",
                    )
                ),
                "unrestricted_optimality_proven": False,
            }
        )
    return FinanceResult(
        status=status,
        feasible=feasible,
        optimality_proven=optimality_proven,
        decision=decision,
        objective=objective,
        objective_unit=objective_unit,
        metrics=metrics,
        constraints=constraints,
        solver_info=solver_info,
        provenance=provenance,
        tables=tables,
        costs=evaluation.get("costs", {}),
        transformations=transformations,
    )
