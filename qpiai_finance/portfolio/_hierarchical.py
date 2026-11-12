"""Hierarchical risk parity using correlation clustering and bisection."""

from importlib.metadata import version
from time import perf_counter

import numpy as np
from scipy import sparse
from scipy.cluster.hierarchy import leaves_list, linkage
from scipy.spatial.distance import squareform

from ..risk import FactorRisk, _quadratic_risk, _risk_product


def _covariance(portfolio):
    risk = portfolio._covariance
    if isinstance(risk, FactorRisk):
        loadings = sparse.csr_matrix(risk._b)
        covariance = loadings @ sparse.csr_matrix(risk._f) @ loadings.T
        covariance += sparse.diags(risk._d)
        order = risk._assets.get_indexer(portfolio._ids)
        return covariance[order][:, order].toarray()
    return risk.toarray() if sparse.issparse(risk) else risk


def _cluster_variance(covariance, assets):
    subset = covariance[np.ix_(assets, assets)]
    variances = np.diag(subset)
    weights = variances.min() / variances
    weights /= weights.sum()
    return _quadratic_risk(
        weights,
        _risk_product(subset, weights, original=True),
        name="cluster variance",
    )


def construct_portfolio(portfolio, *, client, options):
    from qpiai_opt.opt_solvers import Client

    portfolio._check()
    if options:
        raise ValueError("configure HRP through hierarchical_risk_parity")
    if not isinstance(client, Client):
        raise TypeError("client must be a qpiai_opt.opt_solvers.Client")
    client.verify_api_key()
    started = perf_counter()
    covariance = _covariance(portfolio)
    count = len(portfolio._ids)
    weights = np.ones(count)
    hierarchy = np.empty((0, 4))
    order = np.arange(count)
    if count > 1:
        volatility = np.sqrt(np.diag(covariance))
        correlation = covariance / volatility[:, None] / volatility[None, :]
        if np.any(np.abs(correlation) > 1 + 1e-12):
            raise ValueError("covariance implies an invalid correlation")
        correlation = np.clip(correlation, -1, 1)
        distance = np.sqrt((1 - correlation) / 2)
        np.fill_diagonal(distance, 0)
        hierarchy = linkage(
            squareform(distance, checks=False),
            method=portfolio._linkage_method,
        )
        order = leaves_list(hierarchy)
        clusters = [order]
        while clusters:
            children = []
            for cluster in clusters:
                if len(cluster) == 1:
                    continue
                midpoint = len(cluster) // 2
                left, right = cluster[:midpoint], cluster[midpoint:]
                left_risk = _cluster_variance(covariance, left)
                right_risk = _cluster_variance(covariance, right)
                total_risk = left_risk + right_risk
                left_share = (
                    0.5 if total_risk == 0 else float(right_risk / total_risk)
                )
                weights[left] *= left_share
                weights[right] *= 1 - left_share
                children.extend([left, right])
            clusters = children
    weights *= portfolio._net_weight
    if not np.isfinite(weights).all():
        raise ValueError("HRP produced nonfinite allocation weights")
    summary = {
        "problem_class": "HEURISTIC",
        "execution_mode": "local",
        "provider": "scipy",
        "solver": None,
        "method": "hierarchical-risk-parity",
        "termination": "completed",
        "has_usable_solution": True,
        "solution_feasible": None,
        "optimality_proven": False,
        "guarantee": "none",
        "source_objective": None,
        "transformed": False,
        "settings": {
            "linkage_method": portfolio._linkage_method,
            "zero_risk_cluster_split": "equal",
        },
    }
    details = {
        **summary,
        "scipy_version": version("scipy"),
        "linkage": hierarchy.tolist(),
        "asset_order": portfolio._ids[order].tolist(),
        "algorithm_time_s": perf_counter() - started,
    }
    solution = {f"weight_{i}": float(value) for i, value in enumerate(weights)}
    return solution, summary, details
