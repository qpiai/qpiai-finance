"""Execution and result information from QpiAI Opt."""

from copy import copy
from importlib.metadata import version
from math import frexp, ldexp

import numpy as np


def solve_opt(model, *, client, mode, options, problem_class):
    from qpiai_opt.opt_solvers import solve

    prepared, options, scaling = _linear_objective_units(
        model, options, problem_class
    )
    result = solve(prepared, client=client, mode=mode, **options)
    solution, summary, details = _result_data(result)
    if scaling is not None:
        _restore_objective_units(summary, details, scaling)
    details["input_representation"] = (
        "matrix" if isinstance(model, dict) else type(model).__name__
    )
    details["requested_execution_mode"] = mode
    details["allow_platform"] = options.get("allow_platform", False)
    return solution, summary, details


def _objective_scale(model, problem_class):
    """Keep small linear costs above the solver's absolute dual tolerance.

    One positive power of two preserves the complete objective, constraints
    and integer domains exactly. The smallest nonzero coefficient is moved
    into [0.5, 1), subject to the pinned Opt runtime's finite cost range.
    Financial model exports remain in their original units.
    """
    if problem_class not in {"LP", "MILP"}:
        return None
    matrix = isinstance(model, dict)
    coefficients = (
        np.asarray(model["objective"])
        if matrix
        else np.array([term.coefficient for term in model.objective.terms])
    )
    nonzero = np.abs(coefficients[coefficients != 0])
    if not len(nonzero):
        return None
    target = max(0, -frexp(float(nonzero.min()))[1])
    if not target:
        return None
    offset = (
        model.get("objective_offset", 0.0)
        if matrix
        else model.objective.constant
    )
    largest = max(float(nonzero.max()), abs(float(offset)))
    # Opt 0.0.9 rejects finite linear costs at or above 1e20.
    headroom = frexp(1e20)[1] - frexp(largest)[1]
    if ldexp(largest, headroom) >= 1e20:
        headroom -= 1
    exponent = min(target, max(0, headroom))
    return {
        "type": "objective_scaling",
        "base": 2,
        "exponent": exponent,
        "range_limited": exponent < target,
        "exact": True,
        "source_units_restored": True,
    }


def _linear_objective_units(model, options, problem_class):
    scaling = _objective_scale(model, problem_class)
    if scaling is None:
        return model, options, None
    exponent = scaling["exponent"]
    if not exponent:
        return model, options, scaling
    matrix = isinstance(model, dict)
    offset = (
        model.get("objective_offset", 0.0)
        if matrix
        else model.objective.constant
    )
    if matrix:
        prepared = {
            **model,
            "objective": np.ldexp(model["objective"], exponent),
            "objective_offset": ldexp(float(offset), exponent),
        }
    else:
        from qpiai_opt.opt_modeller import Expression, Term

        prepared = copy(model)
        prepared.objective = Expression(
            terms=[
                Term(ldexp(term.coefficient, exponent), term.variables)
                for term in model.objective.terms
            ],
            constant=ldexp(float(offset), exponent),
        )
    config = options.get("config")
    if config is not None:
        from qpiai_opt.opt_solvers.milp.models import MILPSolverConfig

        config = MILPSolverConfig.model_validate(config)
        fields = config.model_fields_set & {
            "objective_bound",
            "objective_target",
            "mip_abs_gap",
            "dual_feasibility_tolerance",
        }
        converted = {}
        for field in fields:
            value = getattr(config, field)
            if value is not None:
                try:
                    converted[field] = ldexp(value, exponent)
                except OverflowError as error:
                    raise ValueError(
                        f"config.{field} exceeds float64 range after "
                        "objective scaling; use compatible objective units"
                    ) from error
        if converted:
            options = {
                **options,
                "config": config.model_copy(update=converted),
            }
    return prepared, options, scaling


def _restore_objective_units(summary, details, scaling):
    """Restore financial objective, bound and dual units after optimization."""
    exponent = scaling["exponent"]
    provider_values = {}
    for name in (
        "source_objective",
        "best_bound",
    ):
        value = details.get(name)
        if value is not None:
            provider_values[name] = value
            details[name] = ldexp(value, -exponent)
    for name in ("dual_values", "reduced_costs"):
        if details.get(name) is not None:
            provider_values[name] = details[name]
            details[name] = {
                key: ldexp(value, -exponent)
                for key, value in details[name].items()
            }
    settings = details["settings"].copy()
    cost_settings = {
        "objective_bound",
        "objective_target",
        "mip_abs_gap",
        "dual_feasibility_tolerance",
    }
    provider_values["settings"] = {
        name: settings[name] for name in cost_settings if name in settings
    }
    for name in cost_settings & settings.keys():
        if settings[name] is not None:
            settings[name] = ldexp(settings[name], -exponent)
    summary["settings"] = details["settings"] = settings
    summary["source_objective"] = details["source_objective"]
    summary["transformed"] = bool(exponent) or summary["transformed"]
    details["transformed"] = summary["transformed"]
    details["objective_scaling"] = {
        **scaling,
        "provider_values": provider_values,
    }


def _result_data(result):
    """Read an authoritative Opt result without renaming its diagnostics."""
    summary = result.info().model_dump(mode="json")
    details = {
        **summary,
        "qpiai_opt_version": version("qpiai-opt"),
        "solver_time_s": result.solver_time_s,
        "compute_time_s": result.compute_time_s,
        "job_id": result.job_id,
        "problem_id": result.problem_id,
        "status": getattr(result, "status", summary["termination"]),
    }
    diagnostics = {
        "iteration_count",
        "optimality_gap",
        "best_bound",
        "num_nodes",
        "num_variables",
        "dual_values",
        "reduced_costs",
    }
    details.update(result.model_dump(mode="json", include=diagnostics))
    return result.solution, summary, details
