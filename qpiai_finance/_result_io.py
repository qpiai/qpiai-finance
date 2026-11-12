"""Typed financial result records and their structural consistency checks."""

from dataclasses import fields as dataclass_fields

import numpy as np
import pandas as pd

from ._validation import identifiers, scalar, vector
from ._value_io import (
    decode,
    decode_arguments,
    encode,
    encode_arguments,
    fields,
)
from .results import FinanceResult


def _check(result):
    if not isinstance(result.status, str) or not result.status.strip():
        raise ValueError("result status must be nonempty text")
    if (
        type(result.feasible) is not bool
        or type(result.optimality_proven) is not bool
    ):
        raise ValueError(
            "result feasibility and optimality flags must be boolean"
        )
    if result.objective is not None:
        scalar(result.objective, "result objective")
    if result.objective_unit is not None and (
        not isinstance(result.objective_unit, str)
        or not result.objective_unit.strip()
    ):
        raise ValueError("objective_unit must be nonempty text or None")
    for name in (
        "decision",
        "metrics",
        "solver_info",
        "provenance",
        "tables",
        "costs",
    ):
        value = getattr(result, name)
        if type(value) is not dict or any(
            not isinstance(key, str) for key in value
        ):
            raise ValueError(
                f"result {name} must be a mapping with string keys"
            )
    for value in result.decision.values():
        if (
            not isinstance(value, (pd.Series, pd.DataFrame))
            or not value.index.is_unique
            or (
                isinstance(value, pd.DataFrame) and not value.columns.is_unique
            )
        ):
            raise ValueError(
                "decisions require labeled tables/series with unique indices"
            )
    if any(
        not isinstance(value, pd.DataFrame) for value in result.tables.values()
    ):
        raise ValueError("result tables must contain DataFrames")
    if type(result.transformations) is not list or any(
        type(item) is not dict for item in result.transformations
    ):
        raise ValueError("result transformations must be a list of mappings")
    checks = result.constraints
    if (
        not isinstance(checks, pd.DataFrame)
        or not checks.columns.is_unique
        or not {
            "value",
            "lower",
            "upper",
            "violation",
            "satisfied",
        }
        <= set(checks.columns)
    ):
        raise ValueError(
            "constraints require value/lower/upper/violation/satisfied columns"
        )
    if any(
        not isinstance(item, (bool, np.bool_)) for item in checks.satisfied
    ):
        raise ValueError("constraint satisfaction flags must be boolean")
    if result.feasible and (not result.decision or not checks.satisfied.all()):
        raise ValueError(
            "a feasible result requires a decision and satisfied constraints"
        )
    if result.optimality_proven and (
        not result.feasible
        or result.objective is None
        or result.solver_info.get("objective_reconciled") is not True
        or result.solver_info.get("optimality_proven") is not True
        or result.solver_info.get("solver_reconciled") is False
    ):
        raise ValueError(
            "optimality requires feasibility, objective reconciliation "
            "and consistent solver reconstruction"
        )
    if not result.decision and result.objective is not None:
        raise ValueError(
            "a missing decision cannot have a financial objective"
        )


def to_dict(result):
    _check(result)
    names = {item.name for item in dataclass_fields(FinanceResult)}
    if set(vars(result)) != names:
        raise ValueError("result has unsupported extra fields")
    return {
        "format": "qpiai-finance-result",
        "schema_version": 1,
        **encode_arguments(vars(result), diagnostics=True),
    }


def from_dict(document):
    names = {item.name for item in dataclass_fields(FinanceResult)}
    fields(document, {"format", "schema_version", *names})
    arguments = decode_arguments(
        {name: document[name] for name in names},
        diagnostics=True,
    )
    result = FinanceResult(**arguments)
    _check(result)
    return result


def _check_frontier(frontier):
    if not isinstance(frontier.targets, pd.Series):
        raise ValueError("frontier targets must be a Series")
    identifiers(frontier.targets.index, "target IDs")
    targets = vector(
        frontier.targets, frontier.targets.index, "target returns"
    )
    if not isinstance(frontier.horizon, str) or not frontier.horizon.strip():
        raise ValueError("frontier horizon must be nonempty text")
    if type(frontier.results) is not tuple or len(frontier.results) != len(
        targets
    ):
        raise ValueError("frontier results must match target count and order")
    for target, result in zip(targets, frontier.results):
        if type(result) is not FinanceResult:
            raise ValueError("frontier entries must be FinanceResult records")
        _check(result)
        inputs = result.provenance.get("inputs")
        if (
            not isinstance(inputs, dict)
            or inputs.get("model") != "PortfolioModel"
            or inputs.get("horizon") != frontier.horizon
        ):
            raise ValueError(
                "frontier records must share its portfolio horizon"
            )
        effective = scalar(inputs.get("minimum_return"), "effective target")
        if effective < target:
            raise ValueError(
                "effective target must retain the requested return"
            )


def frontier_to_dict(frontier):
    _check_frontier(frontier)
    return {
        "format": "qpiai-finance-frontier",
        "schema_version": 1,
        "targets": encode(frontier.targets, diagnostics=True),
        "horizon": frontier.horizon,
        "results": [to_dict(result) for result in frontier.results],
    }


def frontier_from_dict(document):
    from .portfolio import FrontierResult

    fields(
        document, {"format", "schema_version", "targets", "horizon", "results"}
    )
    if type(document["results"]) is not list:
        raise ValueError("frontier results must be a list")
    results = []
    for record in document["results"]:
        if (
            type(record) is not dict
            or record.get("format") != "qpiai-finance-result"
            or type(record.get("schema_version")) is not int
            or record["schema_version"] != 1
        ):
            raise ValueError(
                "unsupported frontier result record format/version"
            )
        results.append(from_dict(record))
    frontier = FrontierResult(
        decode(document["targets"], diagnostics=True),
        tuple(results),
        document["horizon"],
    )
    _check_frontier(frontier)
    return frontier
