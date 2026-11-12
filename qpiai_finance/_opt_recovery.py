"""Offline financial recovery and evidence policy for native Opt results."""

from copy import deepcopy
from time import perf_counter

from ._validation import scalar


def recover(raw, *, model, tolerance, opt_model=None, objective_scaling=None):
    from qpiai_opt.opt_solvers import IsingSolveResult, QPSolveResult, classify
    from qpiai_opt.opt_solvers.hubo import SolveResult as HUBOSolveResult
    from qpiai_opt.opt_solvers.milp import SolveResult as MILPSolveResult
    from qpiai_opt.opt_solvers.qubo import SolveResult as QUBOSolveResult

    from ._solvers.opt import _result_data
    from ._workflow import _financial_result, _require_model
    from .quantum import PortfolioEncoding

    started = perf_counter()
    if isinstance(model, PortfolioEncoding):
        if objective_scaling is not None:
            raise ValueError(
                "objective_scaling applies only to LP/MILP records"
            )
        if opt_model is not None:
            raise ValueError("PortfolioEncoding already retains its mapping")
        return model.decode_result(raw, tolerance=tolerance)
    _require_model(model)
    quantum = False
    if type(raw).__name__ == "QuantumResult":
        from qpiai_opt.quantum import QuantumResult

        quantum = type(raw) is QuantumResult
    if quantum or type(raw) in (
        QUBOSolveResult,
        HUBOSolveResult,
        IsingSolveResult,
    ):
        if objective_scaling is not None:
            raise ValueError(
                "objective_scaling applies only to LP/MILP records"
            )
        from ._encoded_recovery import recover as recover_encoded

        return recover_encoded(
            raw, model=model, opt_model=opt_model, tolerance=tolerance
        )
    if opt_model is not None:
        raise ValueError("opt_model is used only for polynomial/gate results")
    if type(raw) not in (MILPSolveResult, QPSolveResult):
        raise TypeError(
            "result must be an Opt LP, MILP or QP SolveResult; "
            "polynomial/gate results require their retained decoding model"
        )
    tolerance = scalar(tolerance, "tolerance", minimum=0)
    raw = type(raw).model_validate(raw.model_dump(mode="python"))
    snapshot = deepcopy(model)
    preparation_started = perf_counter()
    native, data = _source_data(snapshot, mode=raw.execution_mode)
    if classify(native) != raw.problem_class:
        raise ValueError("result class does not match the financial model")
    if raw.sense is not None and raw.sense.lower() != data["sense"]:
        raise ValueError("result objective sense does not match the model")
    if raw.solution is not None and set(raw.solution) != set(
        data["variable_names"]
    ):
        raise ValueError("result must contain exactly the model variables")
    build_time = perf_counter() - preparation_started
    solution, info, recorded = _result_data(raw)
    if objective_scaling is not None:
        from ._solvers.opt import _restore_objective_units

        if raw.problem_class not in {"LP", "MILP"}:
            raise ValueError(
                "objective_scaling applies only to LP/MILP records"
            )
        scaling = _checked_scaling(objective_scaling)
        _restore_objective_units(info, recorded, scaling)
    info, details = _recorded_metadata(
        info, recorded, has_solution=solution is not None
    )
    result = _financial_result(
        snapshot,
        solution,
        info,
        details,
        tolerance=tolerance,
        build_time=build_time,
        solve_time=None,
    )
    return _finish_recovery(
        result, has_solution=solution is not None, started=started
    )


def _source_data(model, *, mode):
    from qpiai_opt.opt_solvers import classify

    from ._workflow import _opt_input

    native = _opt_input(model, mode=mode)
    if isinstance(native, dict):
        data = native
    elif classify(native) == "QP":
        data = native.to_qp_matrix()
    else:
        data = native.to_lp_matrix()
    return native, data


def _recorded_metadata(info, recorded, *, has_solution):
    recorded.pop("qpiai_opt_version", None)
    # External records do not bind a solver proof to this feasible set.
    info = info.copy()
    info.update(
        optimality_proven=False,
        termination="completed" if has_solution else "unknown",
        guarantee="none",
    )
    details = {
        **info,
        "recorded_solver": recorded,
        "job_id": recorded["job_id"],
        "problem_id": recorded["problem_id"],
    }
    if "objective_scaling" in recorded:
        details["objective_scaling"] = recorded["objective_scaling"]
    return info, details


def _checked_scaling(value):
    from collections.abc import Mapping

    if not isinstance(value, Mapping):
        raise TypeError("objective_scaling must be a mapping")
    allowed = {
        "type",
        "base",
        "exponent",
        "range_limited",
        "exact",
        "source_units_restored",
        "provider_values",
    }
    if set(value) - allowed:
        raise ValueError("objective_scaling contains unknown fields")
    if value.get("type", "objective_scaling") != "objective_scaling":
        raise ValueError("objective_scaling has an unsupported type")
    for flag in ("range_limited", "exact", "source_units_restored"):
        if flag in value and type(value[flag]) is not bool:
            raise TypeError(f"objective_scaling.{flag} must be a boolean")
    if not value.get("exact", True):
        raise ValueError(
            "objective_scaling must be exact power-of-two scaling"
        )
    if "provider_values" in value and not isinstance(
        value["provider_values"], Mapping
    ):
        raise TypeError("objective_scaling.provider_values must be a mapping")
    exponent = value.get("exponent")
    if (
        value.get("base") != 2
        or isinstance(value.get("base"), bool)
        or type(exponent) is not int
        or not 0 <= exponent <= 1073
    ):
        raise ValueError(
            "objective_scaling requires base=2 and an integer exponent "
            "between 0 and 1073"
        )
    return {
        "type": "objective_scaling",
        "base": 2,
        "exponent": exponent,
        "range_limited": bool(value.get("range_limited", False)),
        "exact": True,
        "source_units_restored": True,
    }


def _finish_recovery(result, *, has_solution, started):
    if not has_solution:
        result.status = "no_solution"
    elif result.feasible:
        result.status = (
            "objective_mismatch"
            if result.solver_info["source_objective"] is not None
            and result.solver_info["objective_reconciled"] is False
            else "feasible"
        )
    result.solver_info.update(
        has_usable_solution=result.feasible,
        solution_feasible=result.feasible if has_solution else None,
        guarantee="feasible_only" if result.feasible else "none",
    )
    result.provenance.update(
        result_origin="recorded_opt_result",
        source_identity_verified=False,
    )
    result.provenance["timing_s"]["recovery"] = perf_counter() - started
    return result
