"""Authenticated SCIP execution for exact nonlinear financial constraints."""

from copy import deepcopy
from importlib.metadata import version

import numpy as np


def linear_model(data):
    """Translate the shared linear portion using PySCIPOpt's public API."""
    from pyscipopt import Model, quicksum

    model = Model(data["name"])
    for field in (
        "lower_bounds",
        "upper_bounds",
        "row_lower",
        "row_upper",
        "objective",
    ):
        for number in data[field]:
            if np.isfinite(number) and model.isInfinity(abs(float(number))):
                raise ValueError(
                    "financial bounds exceed SCIP's numerical range; "
                    "use compatible units"
                )
    if any(
        model.isInfinity(abs(float(c))) for c in data["constraint_matrix"].data
    ):
        raise ValueError(
            "financial coefficients exceed SCIP's numerical range"
        )
    variables = {}
    for name, low, high, integer in zip(
        data["variable_names"],
        data["lower_bounds"],
        data["upper_bounds"],
        data["integrality"],
    ):
        variables[name] = model.addVar(
            name=name,
            vtype="I" if integer else "C",
            lb=None if np.isneginf(low) else float(low),
            ub=None if np.isposinf(high) else float(high),
        )
    ordered = list(variables.values())
    matrix = data["constraint_matrix"].tocsr()
    for j, (low, high, name) in enumerate(
        zip(data["row_lower"], data["row_upper"], data["constraint_names"])
    ):
        row = matrix.getrow(j)
        value = quicksum(
            float(c) * ordered[i] for i, c in zip(row.indices, row.data)
        )
        if low == high:
            model.addCons(value == float(low), name=name)
        else:
            if np.isfinite(low):
                model.addCons(value >= float(low), name=f"{name}_lower")
            if np.isfinite(high):
                model.addCons(value <= float(high), name=f"{name}_upper")
    objective = quicksum(
        float(c) * variable
        for c, variable in zip(data["objective"], ordered)
        if c != 0
    )
    objective += float(data["objective_offset"])
    model.setObjective(
        objective, "minimize" if data["sense"] == "min" else "maximize"
    )
    return model, variables


def solve_scip(model, variables, *, client, options, problem_class):
    from qpiai_opt.opt_solvers import Client

    if not isinstance(client, Client):
        raise TypeError("client must be a qpiai_opt.opt_solvers.Client")
    options = deepcopy(options)
    unknown = set(options) - {"scip_params", "verbose"}
    if unknown:
        raise ValueError(f"unsupported direct SCIP options: {sorted(unknown)}")
    params = options.get("scip_params", {})
    if type(params) is not dict or any(
        not isinstance(key, str) for key in params
    ):
        raise TypeError("scip_params must be a dictionary with string keys")
    verbose = options.get("verbose", False)
    if type(verbose) is not bool:
        raise TypeError("verbose must be a boolean")
    default_feastol = model.getParam("numerics/feastol")
    default_epsilon = model.getParam("numerics/epsilon")
    settings = {"numerics/feastol": 1e-9, **params}
    model.setParams(settings)
    feastol = model.getParam("numerics/feastol")
    if "numerics/epsilon" not in params and feastol < default_feastol:
        # Preserve SCIP's separation between zero and feasibility tolerances.
        # SCIP permits epsilon values down to 1e-20.
        epsilon = max(1e-20, default_epsilon * (feastol / default_feastol))
        model.setRealParam("numerics/epsilon", epsilon)
        settings["numerics/epsilon"] = epsilon
    model.hideOutput(not verbose)
    client.verify_api_key()
    model.optimize()
    status = str(model.getStatus())
    solution = None
    objective = None
    if model.getNSols() > 0:
        best = model.getBestSol()
        solution = {
            name: float(model.getSolVal(best, value))
            for name, value in variables.items()
        }
        objective = float(model.getSolObjVal(best))
        if not np.isfinite([objective, *solution.values()]).all():
            raise ValueError("SCIP returned a nonfinite financial candidate")
    proven = status == "optimal" and solution is not None
    termination = {
        "optimal": "optimal",
        "infeasible": "infeasible",
        "unbounded": "unbounded",
        "inforunbd": "unknown",
        "userinterrupt": "interrupted",
    }.get(status, "limit_reached" if status.endswith("limit") else "unknown")
    details = {
        "provider": "pyscipopt",
        "solver": "SCIP",
        "status": status,
        "scip_status": status,
        "native_statistics_available": True,
        "solver_version": (
            f"{model.getMajorVersion()}.{model.getMinorVersion()}."
            f"{model.getTechVersion()}"
        ),
        "pyscipopt_version": version("pyscipopt"),
        "node_count": model.getNNodes(),
        "solver_time_s": model.getSolvingTime(),
        "requested_options": options.copy(),
        "effective_settings": {
            key: model.getParam(key)
            for key in {
                "limits/time",
                "limits/gap",
                "limits/absgap",
                "limits/nodes",
                "numerics/feastol",
                "numerics/epsilon",
                "parallel/maxnthreads",
                "randomization/randomseedshift",
                *params,
            }
        },
        "job_id": None,
        "problem_id": None,
        "optimality_proven": proven,
    }
    bound = model.getDualbound()
    if np.isfinite(bound) and not model.isInfinity(abs(bound)):
        details["dual_bound"] = float(bound)
        details["dual_bound_sense"] = (
            "lower" if model.getObjectiveSense() == "minimize" else "upper"
        )
    gap = model.getGap()
    if np.isfinite(gap) and not model.isInfinity(abs(gap)):
        details["solver_relative_gap"] = float(gap)
    info = {
        "problem_class": problem_class,
        "execution_mode": "local",
        "provider": "pyscipopt",
        "solver": "SCIP",
        "method": "spatial-branch-and-bound",
        "termination": termination,
        "has_usable_solution": solution is not None,
        "solution_feasible": None,
        "optimality_proven": proven,
        "guarantee": "global_optimum" if proven else "none",
        "transformed": True,
        "settings": details["effective_settings"],
        "source_objective": objective,
        "job_id": None,
        "problem_id": None,
    }
    details.update(info)
    return solution, info, details
