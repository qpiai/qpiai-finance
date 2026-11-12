"""Versioned JSON interchange for financial models, scenarios and results.

Interchange is offline: it neither authenticates nor solves. Models use
validated public constructors and modeling methods. Results retain recorded
evidence and job identifiers as data; executable jobs, clients, credentials
and executable Python objects are excluded.
"""

import json

from ._model_io import MODELS
from ._value_io import (
    decode,
    decode_arguments,
    encode,
    encode_arguments,
    fields,
)
from .portfolio import FrontierResult
from .results import FinanceResult
from .scenarios import ScenarioPaths, Scenarios, ScenarioTree

__all__ = ["to_dict", "from_dict", "dumps", "loads", "dump", "load"]


def to_dict(value):
    """Return a detached financial record with schema_version=1.

    Preserves supported models' financial inputs, labels, sparse/factor
    representations, active objective and hard mandates. Subclasses and
    custom extensions are rejected. Results retain recorded solver evidence;
    restoring it does not perform fresh financial or optimality verification.
    Clients and executable solver job/session objects are excluded.
    Scenarios, ScenarioPaths and ScenarioTree retain values, labels,
    probability/information semantics and declared construction metadata as
    data, without rerunning sampling.
    """
    if type(value) is FinanceResult:
        from ._result_io import to_dict as result_to_dict

        return result_to_dict(value)
    if type(value) is FrontierResult:
        from ._result_io import frontier_to_dict

        return frontier_to_dict(value)
    if type(value) in {Scenarios, ScenarioPaths, ScenarioTree}:
        return {
            "format": "qpiai-finance-scenarios",
            "schema_version": 1,
            "data": encode(value),
        }
    for name, (constructor, export, _) in MODELS.items():
        if type(value) is constructor:
            inputs, settings = export(value)
            return {
                "format": "qpiai-finance-model",
                "schema_version": 1,
                "model": name,
                "inputs": encode_arguments(inputs),
                "configuration": [
                    {
                        "method": method,
                        "arguments": encode_arguments(arguments),
                    }
                    for method, arguments in settings
                ],
            }
    raise TypeError(
        "value must be a Finance model, result or scenario data; "
        "subclasses are unsupported"
    )


def from_dict(document):
    """Restore a financial model or structurally validated result record.

    Accepts qpiai-finance-model, qpiai-finance-result,
    qpiai-finance-frontier and qpiai-finance-scenarios schema 1.
    Unknown types, fields and methods fail
    explicitly; no partial object is returned on failure.
    A restored model is not a financial approval or a verified solution.
    """
    if type(document) is not dict:
        raise ValueError("expected a financial interchange document")
    if (
        type(document.get("schema_version")) is not int
        or document["schema_version"] != 1
    ):
        raise ValueError("unsupported schema_version; expected 1")
    if document.get("format") == "qpiai-finance-result":
        from ._result_io import from_dict as result_from_dict

        return result_from_dict(document)
    if document.get("format") == "qpiai-finance-frontier":
        from ._result_io import frontier_from_dict

        return frontier_from_dict(document)
    if document.get("format") == "qpiai-finance-scenarios":
        fields(document, {"format", "schema_version", "data"})
        payload = document["data"]
        if type(payload) is not dict or payload.get("type") not in {
            "scenarios",
            "scenario_paths",
            "scenario_tree",
        }:
            raise ValueError("expected financial scenario data")
        return decode(payload)
    fields(
        document,
        {
            "format",
            "schema_version",
            "model",
            "inputs",
            "configuration",
        },
    )
    if document["format"] != "qpiai-finance-model":
        raise ValueError("expected a qpiai-finance-model document")
    name = document["model"]
    if not isinstance(name, str) or name not in MODELS:
        raise ValueError("unsupported financial model type")
    constructor, _, allowed = MODELS[name]
    configuration = document["configuration"]
    if type(configuration) is not list:
        raise ValueError("configuration must be a list")
    prepared = []
    for setting in configuration:
        fields(setting, {"method", "arguments"})
        method = setting["method"]
        if not isinstance(method, str) or method not in allowed:
            raise ValueError(f"unsupported {name} configuration method")
        prepared.append((method, decode_arguments(setting["arguments"])))
    model = constructor(**decode_arguments(document["inputs"]))
    for method, arguments in prepared:
        getattr(model, method)(**arguments)
    return model


def dumps(value):
    """Serialize financial model, scenario or result data to strict JSON."""
    return json.dumps(to_dict(value), allow_nan=False, separators=(",", ":"))


def _pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError(f"duplicate JSON field: {key!r}")
        result[key] = value
    return result


def _constant(value):
    raise ValueError(f"non-finite JSON number: {value}")


def loads(text):
    """Restore financial data, rejecting duplicate JSON fields.

    Loading validates modeling inputs but never authenticates, submits or
    solves. Unknown schema versions fail rather than being guessed.
    """
    return from_dict(
        json.loads(
            text,
            object_pairs_hook=_pairs,
            parse_constant=_constant,
        )
    )


def dump(value, fp):
    """Write financial data to a text stream, following json.dump's API.

    Open the destination with UTF-8 encoding. Serialization is completed
    before writing, so invalid models do not write a partial JSON document.
    """
    fp.write(dumps(value))


def load(fp):
    """Restore financial data from a JSON text stream."""
    return loads(fp.read())
