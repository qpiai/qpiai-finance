"""Replay primary financial decisions against caller-supplied source models."""

from copy import deepcopy
from hashlib import sha256

import numpy as np
import pandas as pd

from ._model_io import MODELS
from ._serialization import dumps
from ._validation import scalar, vector


def evaluate(result, model, *, tolerance):
    from ._workflow import _specification

    name = type(model).__name__
    if name not in MODELS or type(model) is not MODELS[name][0]:
        raise TypeError("model must be a supported source Finance model")
    if (
        type(result.provenance) is not dict
        or type(result.decision) is not dict
    ):
        raise ValueError("result provenance and decision must be mappings")
    inputs = result.provenance.get("inputs")
    if not isinstance(inputs, dict) or inputs.get("model") != name:
        raise ValueError("result and source financial model types must match")
    if not result.decision:
        raise ValueError("result has no decision to evaluate")
    tolerance = scalar(tolerance, "tolerance", minimum=0)
    primary = {
        "PortfolioModel": ("weights",),
        "FundingModel": ("draws", "transfers"),
        "LiabilityMatchingModel": ("holdings",),
        "HedgeModel": ("hedges",),
        "CreditAllocationModel": ("allocations",),
        "CollateralAllocationModel": ("assignments",),
        "ReinsuranceModel": ("selections",),
        "SettlementModel": ("schedule", "prefunding"),
        "ExecutionModel": ("executions",),
        "TradingModel": ("trades",),
    }[name]
    missing = set(primary) - result.decision.keys()
    if missing:
        raise ValueError(
            f"result is missing primary decisions: {sorted(missing)}"
        )
    snapshot = deepcopy(model)
    arguments = [result.decision[key] for key in primary]
    keywords = {"tolerance": tolerance}
    if name == "PortfolioModel":
        if "tax_lot_sales" in result.decision:
            keywords["tax_lot_sales"] = result.decision["tax_lot_sales"]
        elif (
            snapshot._account is not None
            and snapshot._account.tax_lots is not None
        ):
            raise ValueError(
                "result is missing primary decisions: tax_lot_sales"
            )
    if name == "FundingModel":
        if "investments" in result.decision:
            keywords["investments"] = result.decision["investments"]
        elif snapshot._investments:
            raise ValueError(
                "result is missing primary decisions: investments"
            )
    if name == "LiabilityMatchingModel":
        if (
            type(result.metrics) is not dict
            or "initial_capital" not in result.metrics
        ):
            raise ValueError("liability result is missing initial_capital")
        keywords["initial_capital"] = result.metrics["initial_capital"]
    elif name == "SettlementModel":
        keywords["prefunding"] = arguments.pop()
    elif name == "TradingModel":
        if "draws" in result.decision:
            keywords["draws"] = result.decision["draws"]
        elif snapshot._funding:
            raise ValueError("result is missing primary decisions: draws")
    evaluation = snapshot.evaluate(*arguments, **keywords)
    if name == "PortfolioModel" and "decision" not in evaluation:
        evaluation["decision"] = {
            "weights": pd.Series(
                vector(arguments[0], snapshot.asset_ids, "weights"),
                index=snapshot.asset_ids,
                name="weight",
            ),
        }
    recorded = (
        None
        if result.objective is None
        else scalar(result.objective, "recorded objective")
    )
    current = evaluation["objective"]
    matches = recorded is None and current is None
    if recorded is not None and current is not None:
        matches = bool(
            np.isclose(recorded, current, atol=tolerance, rtol=1e-7)
        )
    fingerprint = sha256(dumps(_specification(snapshot)).encode()).hexdigest()
    recorded_fingerprint = result.provenance.get("input_sha256")
    evaluation.update(
        recorded_objective=recorded,
        objective_matches=matches,
        input_fingerprint_matches=isinstance(recorded_fingerprint, str)
        and recorded_fingerprint == fingerprint,
    )
    return evaluation
