"""Numerical refinement of positive risk-budget equations."""

from time import perf_counter

import numpy as np
from scipy.optimize import root


def refine_positions(portfolio, solution, *, tolerance):
    started = perf_counter()
    positions = np.array(
        [solution[f"risk_position_{i}"] for i in range(len(portfolio._ids))]
    )
    if np.any(positions <= 0):
        raise ValueError("risk-budget positions must be positive")
    if float(positions @ portfolio._risk_apply(positions)) <= 0:
        raise ValueError("risk-budget positions have zero portfolio variance")
    volatility = np.sqrt(portfolio._risk_diagonal())
    budgets = portfolio._risk_budgets

    def residual(log_positions):
        scaled = np.exp(log_positions)
        original = scaled / volatility
        marginal = portfolio._risk_apply(original) / volatility
        return scaled * marginal - budgets

    initial = np.log(positions * volatility)
    before = float(np.max(np.abs(residual(initial))))
    accuracy = max(np.finfo(float).eps, min(tolerance / 10, 1e-12))
    details = {
        "method": "scipy-root-krylov",
        "residual_before": before,
        "residual_after": before,
        "accepted": False,
        "function_evaluations": 0,
        "settings": {
            "maxiter": portfolio._risk_budget_polish_maxiter,
            "fatol": accuracy,
            "line_search": "armijo",
        },
    }
    if before > accuracy:
        refined = root(
            residual,
            initial,
            method="krylov",
            options=details["settings"],
        )
        candidate = np.exp(refined.x) / volatility
        after = float(np.max(np.abs(residual(refined.x))))
        evaluations = refined.get("nfev")
        details["function_evaluations"] = (
            None if evaluations is None else int(evaluations)
        )
        details["message"] = str(refined.message)
        if np.isfinite(candidate).all() and after < before:
            positions = candidate
            details["residual_after"] = after
            details["accepted"] = True
    updated = solution.copy()
    weights = portfolio._net_weight * positions / positions.sum()
    for i in range(len(positions)):
        updated[f"risk_position_{i}"] = float(positions[i])
        updated[f"weight_{i}"] = float(weights[i])
    details["runtime_s"] = perf_counter() - started
    return updated, details
