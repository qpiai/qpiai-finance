"""Authenticated execution through CVXPY's installed solver interfaces."""

from importlib.metadata import version

import numpy as np


def solve_cvxpy(
    problem,
    variables,
    numerical_units=None,
    *,
    client,
    options,
    solver,
    problem_class,
    tolerance,
):
    import cvxpy as cp
    from qpiai_opt.opt_solvers import Client

    if not isinstance(client, Client):
        raise TypeError("client must be a qpiai_opt.opt_solvers.Client")
    selected = {"clarabel": cp.CLARABEL, "scip": cp.SCIP}[solver]
    if selected not in cp.installed_solvers():
        raise ValueError(
            f"the explicitly selected {selected} solver is not installed"
        )
    if problem.is_mixed_integer() and solver == "clarabel":
        raise ValueError(
            "Clarabel does not support integer decisions; select solver='scip'"
        )
    forbidden = {"solver", "solver_path", "gp", "qcp", "requires_grad"} & set(
        options
    )
    if forbidden:
        raise ValueError(
            f"unsupported solver route overrides: {sorted(forbidden)}"
        )
    requested_options = options.copy()
    if numerical_units is not None:
        from ._units import clarabel_options

        if solver != "clarabel":
            raise ValueError("these numerical units require Clarabel")
        if len(numerical_units["constraint_exponents"]) != len(
            problem.constraints
        ):
            raise ValueError("numerical dual units do not match constraints")
        options = clarabel_options(numerical_units, options, tolerance)
    client.verify_api_key()
    # Restore the objective constant when reporting a solver bound.
    _, _, inverse = problem.get_problem_data(selected)
    offset = float(np.asarray(inverse[-1].get("offset", 0)).item())
    problem.solve(solver=selected, **options)
    status = problem.status
    statuses = {
        cp.OPTIMAL: "optimal",
        cp.OPTIMAL_INACCURATE: "completed",
        cp.INFEASIBLE: "infeasible",
        cp.INFEASIBLE_INACCURATE: "unknown",
        cp.UNBOUNDED: "unbounded",
        cp.UNBOUNDED_INACCURATE: "unknown",
        cp.USER_LIMIT: "limit_reached",
    }
    termination = statuses.get(status, "unknown")
    solution = None
    coordinates = problem.variables()
    # Constants retain values even when the problem has no primal solution.
    has_primal = status in (
        cp.OPTIMAL, cp.OPTIMAL_INACCURATE, cp.USER_LIMIT
    ) and (
        not coordinates
        or any(coordinate.value is not None for coordinate in coordinates)
    )
    if has_primal:
        candidate = {}
        for name, expression in variables.items():
            if (
                expression.value is None
                or not np.isfinite(expression.value).all()
            ):
                raise ValueError(
                    "solver returned an incomplete or nonfinite "
                    f"{name} decision"
                )
            if name == "weights":
                candidate.update(
                    {
                        f"weight_{i}": float(x)
                        for i, x in enumerate(expression.value)
                    }
                )
            else:
                candidate[name] = float(np.asarray(expression.value).item())
        solution = candidate
    proof = status == cp.OPTIMAL
    objective = (
        float(problem.value)
        if solution is not None and np.isfinite(problem.value)
        else None
    )
    stats = problem.solver_stats
    details = {
        "solver_time_s": stats.solve_time,
        "iteration_count": stats.num_iters,
        "job_id": None,
        "problem_id": None,
        "status": status,
        "cvxpy_version": version("cvxpy"),
        "requested_options": requested_options,
    }
    if solver == "clarabel":
        import clarabel

        defaults = clarabel.DefaultSettings()
        settings = {
            name: getattr(defaults, name)
            for name in dir(defaults)
            if not name.startswith("_")
            and isinstance(getattr(defaults, name), (bool, int, float, str))
        }
        settings["verbose"] = options.get("verbose", False)
        settings.update(
            {key: value for key, value in options.items() if key in settings}
        )
        details["solver_version"] = version("clarabel")
        details["duals"] = [
            None if c.dual_value is None else np.asarray(c.dual_value).tolist()
            for c in problem.constraints
        ]
        method, solver_name = "interior-point", "Clarabel"
    else:
        extra = stats.extra_stats or {}
        native = extra.get("model")
        if native is None:
            # Older CVXPY releases do not expose SCIP's native statistics.
            settings = options.get("scip_params", {}).copy()
            details["native_statistics_available"] = False
            details["solver_version"] = None
            details["pyscipopt_version"] = version("pyscipopt")
            details["dual_bound"] = None
            details["solver_relative_gap"] = None
            method, solver_name = "branch-and-cut", "SCIP"
        else:
            details["native_statistics_available"] = True
            settings, scip_details = _scip_statistics(
                native, options, extra, problem.objective, offset
            )
            details.update(scip_details)
            native_status = scip_details["scip_status"]
            proof = proof and native_status == "optimal"
            if native_status in _SCIP_LIMITS:
                termination = "limit_reached"
            method, solver_name = "branch-and-cut", "SCIP"

    if numerical_units is not None:
        from ._units import binary_scale

        provider_values = {
            "source_objective": objective,
            "settings": settings.copy(),
            "duals": details["duals"],
        }
        money = numerical_units["objective_exponent"]
        try:
            if objective is not None:
                objective = float(binary_scale(objective, money))
            details["duals"] = [
                None if dual is None else binary_scale(dual, exponent).tolist()
                for dual, exponent in zip(
                    details["duals"], numerical_units["constraint_exponents"]
                )
            ]
            for name in ("tol_gap_abs", "reduced_tol_gap_abs"):
                settings[name] = float(binary_scale(settings[name], money))
        except FloatingPointError as error:
            raise ValueError(
                "solver diagnostics exceed source-unit range"
            ) from error
        details["numerical_units"] = numerical_units
        details["provider_values"] = provider_values
        details["numerical_options"] = options.copy()

    info = {
        "problem_class": problem_class,
        "execution_mode": "local",
        "provider": "cvxpy",
        "solver": solver_name,
        "method": method,
        "termination": termination,
        "has_usable_solution": solution is not None,
        "solution_feasible": None,
        "optimality_proven": proof,
        "guarantee": "global_optimum" if proof else "none",
        "source_objective": objective,
        "transformed": True,
        "settings": settings,
    }
    return solution, info, {**info, **details}


def linear_problem(model):
    """Translate a detached Opt LP/MILP using its public matrix API."""
    data = model if isinstance(model, dict) else model.to_lp_matrix()
    problem, variables, _, _ = matrix_problem(data)
    return problem, variables


def matrix_problem(data, *, zero_constants=False):
    """Build linear expressions and retain constraint-coordinate bindings."""
    import cvxpy as cp
    from scipy import sparse

    if np.any(~np.isin(data["integrality"], (0, 1))):
        raise ValueError(
            "this linear adapter requires continuous or integer domains"
        )
    fixed_zero = (
        (data["lower_bounds"] == 0)
        & (data["upper_bounds"] == 0)
        & (data["integrality"] == 0)
        & zero_constants
    )
    if fixed_zero.all():
        fixed_zero[:] = False
    free = np.flatnonzero(~fixed_zero)
    integer_columns = np.flatnonzero(data["integrality"][free] == 1)
    coordinates = cp.Variable(
        len(free),
        integer=(integer_columns.tolist(),) if len(integer_columns) else False,
    )
    if fixed_zero.any():
        projection = sparse.coo_matrix(
            (np.ones(len(free)), (free, np.arange(len(free)))),
            shape=(len(data["variable_names"]), len(free)),
        ).tocsr()
        values = projection @ coordinates
    else:
        values = coordinates
    constraints, bindings = [], []
    matrix = data["constraint_matrix"][:, free]
    constant_rows = np.asarray(matrix.getnnz(axis=1) == 0)
    contradictions = constant_rows & (
        (data["row_lower"] > 0) | (data["row_upper"] < 0)
    )
    # Some solver interfaces discard zero-coefficient rows. Remove only
    # identities; preserve contradictions with a variable constrained to zero.
    keep = ~constant_rows | contradictions
    zero = None
    groups = [
        (
            "column",
            free,
            data["lower_bounds"][free],
            data["upper_bounds"][free],
            coordinates,
        ),
    ]
    if keep.any():
        activity = matrix[keep] @ coordinates
        if contradictions.any():
            zero = cp.Variable(name="constant_constraint_zero")
            constraints.append(zero == 0)
            bindings.append(("guard", np.array([0])))
            activity += contradictions[keep].astype(float) * zero
        groups.append((
            "row",
            np.flatnonzero(keep),
            data["row_lower"][keep],
            data["row_upper"][keep],
            activity,
        ))
    for kind, indices, lower, upper, expression in groups:
        fixed = np.isfinite(lower) & (lower == upper)
        low = np.isfinite(lower) & ~fixed
        high = np.isfinite(upper) & ~fixed
        if fixed.any():
            constraints.append(expression[fixed] == lower[fixed])
            bindings.append((kind, indices[fixed]))
        if low.any():
            constraints.append(expression[low] >= lower[low])
            bindings.append((kind, indices[low]))
        if high.any():
            constraints.append(expression[high] <= upper[high])
            bindings.append((kind, indices[high]))
    objective = data["objective"] @ values + data["objective_offset"]
    objective = (
        cp.Minimize(objective)
        if data["sense"] == "min"
        else cp.Maximize(objective)
    )
    problem = cp.Problem(objective, constraints)
    variables = {
        name: cp.Constant(0.0) if fixed_zero[i] else values[i]
        for i, name in enumerate(data["variable_names"])
    }
    if zero is not None:
        variables["constant_constraint_zero"] = zero
    return problem, variables, values, bindings


_SCIP_LIMITS = {
    "timelimit",
    "nodelimit",
    "gaplimit",
    "sollimit",
    "memlimit",
    "stallnodelimit",
    "totalnodelimit",
    "restartlimit",
    "bestsollimit",
}


def _scip_statistics(native, options, extra, objective, offset):
    import cvxpy as cp

    parameter_names = {
        "limits/time",
        "limits/gap",
        "limits/nodes",
        "numerics/feastol",
        "numerics/epsilon",
        "randomization/randomseedshift",
        "parallel/maxnthreads",
        *options.get("scip_params", {}),
    }
    settings = {name: native.getParam(name) for name in parameter_names}
    details = {
        "solver_version": (
            f"{native.getMajorVersion()}."
            f"{native.getMinorVersion()}."
            f"{native.getTechVersion()}"
        ),
        "pyscipopt_version": version("pyscipopt"),
        "scip_status": str(extra.get("scip_status", "unknown")),
        "node_count": native.getNNodes(),
        "canonical_objective_offset": offset,
    }
    bound = native.getDualbound()
    if np.isfinite(bound) and not native.isInfinity(abs(bound)):
        sign = 1 if isinstance(objective, cp.Minimize) else -1
        details["dual_bound"] = sign * (float(bound) + offset)
        details["dual_bound_sense"] = "lower" if sign == 1 else "upper"
    gap = native.getGap()
    if np.isfinite(gap) and not native.isInfinity(gap):
        details["solver_relative_gap"] = float(gap)
    return settings, details
