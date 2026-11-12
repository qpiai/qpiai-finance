"""Minimum-variance frontier sweeps with a reusable optimization model."""

from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass
from time import perf_counter

import numpy as np
import pandas as pd

from .._serialization import dumps, portable
from .._validation import copy_index, identifiers, numeric, scalar, vector
from ..results import FinanceResult


@dataclass(frozen=True)
class FrontierResult:
    """Portfolio results in the same order as the requested return targets."""

    targets: pd.Series
    results: tuple[FinanceResult, ...]
    horizon: str

    @property
    def table(self):
        rows = []
        for target, result in zip(self.targets, self.results):
            rows.append(
                {
                    "target_return": target,
                    "effective_target": result.provenance["inputs"][
                        "minimum_return"
                    ],
                    "status": result.status,
                    "feasible": result.feasible,
                    "optimality_proven": result.optimality_proven,
                    "objective": result.objective,
                    **result.metrics,
                }
            )
        frame = pd.DataFrame(rows, index=copy_index(self.targets.index))
        frame.attrs["horizon"] = self.horizon
        return frame

    def to_dict(self):
        """Return a numeric report; use io.to_dict for interchange."""
        return {
            "schema_version": 1,
            "type": "efficient_frontier",
            "horizon": self.horizon,
            "targets": portable(self.targets),
            "results": [result.to_dict() for result in self.results],
        }

    def to_json(self):
        """Return report JSON; use io.dumps for reversible interchange."""
        return dumps(portable(self.to_dict()))


def efficient_frontier(
    portfolio,
    target_returns,
    *,
    client=None,
    solver=None,
    mode="local",
    allow_platform=False,
    tolerance=1e-7,
    **options,
):
    from .._workflow import _execution_mode, _resolve_solver, _solve_snapshot

    if isinstance(target_returns, Mapping):
        target_returns = pd.Series(target_returns)
    if isinstance(target_returns, pd.Series):
        ids = identifiers(target_returns.index, "target IDs")
        targets = vector(target_returns, ids, "target returns")
    else:
        targets = numeric(target_returns, "target returns", ndim=1)
        ids = identifiers(range(len(targets)), "target IDs")
    targets = pd.Series(targets, index=ids, name="target_return")
    tolerance = scalar(tolerance, "tolerance", minimum=0)
    if client is None:
        raise ValueError("frontier solves require an authenticated Opt Client")

    started = perf_counter()
    snapshot = deepcopy(portfolio)
    snapshot.minimize_variance()
    minimum = snapshot._minimum_return
    effective_targets = targets.to_numpy(copy=True)
    if minimum is not None:
        effective_targets = np.maximum(effective_targets, minimum)
    snapshot.require_return(minimum=float(effective_targets[0]))
    selected = _resolve_solver(snapshot, solver)
    mode = _execution_mode(mode, allow_platform, selected)
    if selected == "qpiai":
        options["allow_platform"] = allow_platform
    target_parameter = None
    if selected == "qpiai":
        compiled = snapshot.to_model()
    else:
        import cvxpy as cp

        from ._cvxpy import compile_model

        target_parameter = cp.Parameter(value=float(effective_targets[0]))
        compiled = compile_model(snapshot, minimum_return=target_parameter)
    initial_build_time = perf_counter() - started

    results = []
    for i, target in enumerate(effective_targets):
        update_started = perf_counter()
        snapshot.require_return(minimum=float(target))
        if target_parameter is None:
            compiled.set_constraint_rhs("minimum_return", float(target))
        else:
            target_parameter.value = float(target)
        build_time = perf_counter() - update_started
        if i == 0:
            build_time += initial_build_time
        result = _solve_snapshot(
            snapshot,
            compiled,
            client=client,
            mode=mode,
            solver=selected,
            tolerance=tolerance,
            options=options,
            build_time=build_time,
        )
        results.append(result)
    return FrontierResult(targets.copy(), tuple(results), portfolio.horizon)
