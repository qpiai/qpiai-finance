"""Explicit JSON representations for labeled financial data."""

from datetime import date, datetime
from math import prod

import numpy as np
import pandas as pd
from scipy import sparse

from .risk import FactorRisk
from .scenarios import ScenarioPaths, Scenarios, ScenarioTree


def fields(value, expected):
    if type(value) is not dict or set(value) != set(expected):
        raise ValueError(f"expected fields: {', '.join(sorted(expected))}")


def _mapping_key(value, diagnostics):
    if isinstance(value, (np.datetime64, np.timedelta64)):
        return False
    if isinstance(value, np.generic):
        value = value.item()
    if type(value) in (str, int):
        return True
    if not diagnostics:
        return False
    if (
        value is None
        or type(value) is bool
        or isinstance(value, (date, datetime))
    ):
        return value is not pd.NaT
    if type(value) is float:
        return bool(np.isfinite(value))
    return isinstance(value, tuple) and all(
        _mapping_key(item, True) for item in value
    )


def encode(value, *, diagnostics=False):
    if value is None or isinstance(value, (str, bool)):
        return value
    if value is pd.NaT or value is pd.NA:
        if diagnostics:
            return {
                "type": "missing",
                "value": "NaT" if value is pd.NaT else "NA",
            }
        raise ValueError("missing values cannot be model inputs")
    if (
        diagnostics
        and isinstance(value, date)
        and not isinstance(value, datetime)
    ):
        return {"type": "date", "value": value.isoformat()}
    if (
        diagnostics
        and isinstance(value, datetime)
        and not isinstance(value, pd.Timestamp)
    ):
        return {"type": "datetime", "value": value.isoformat()}
    if isinstance(value, np.datetime64):
        return encode(pd.Timestamp(value), diagnostics=diagnostics)
    if isinstance(value, np.timedelta64):
        raise TypeError("timedelta scalars require explicit numeric units")
    if isinstance(value, (date, datetime)):
        return {"type": "timestamp", "value": pd.Timestamp(value).isoformat()}
    if isinstance(value, np.generic):
        item = value.item()
        if isinstance(item, np.generic):
            raise TypeError(f"unsupported NumPy scalar type: {value.dtype}")
        return encode(item, diagnostics=diagnostics)
    if isinstance(value, int):
        # Preserve large integer identifiers through IEEE-754 JSON consumers.
        if abs(value) > 2**53 - 1:
            return {"type": "integer", "value": str(value)}
        return value
    if isinstance(value, float):
        if not np.isfinite(value):
            if diagnostics:
                return {
                    "type": "nonfinite",
                    "value": (
                        "nan"
                        if np.isnan(value)
                        else "+inf"
                        if value > 0
                        else "-inf"
                    ),
                }
            raise ValueError("model inputs must be finite")
        return value
    if diagnostics and isinstance(value, pd.MultiIndex):
        return {
            "type": "multi_index",
            "levels": [
                encode(level, diagnostics=True) for level in value.levels
            ],
            "codes": [code.tolist() for code in value.codes],
            "names": encode(value.names, diagnostics=True),
        }
    if diagnostics and isinstance(value, pd.DatetimeIndex):
        return {
            "type": "datetime_index",
            "timezone": str(value.tz) if value.tz else None,
            "values": encode(value.tolist(), diagnostics=True),
            "name": encode(value.name, diagnostics=True),
        }
    if isinstance(value, pd.Index):
        record = {
            "type": "index",
            "values": encode(value.tolist(), diagnostics=diagnostics),
            "name": encode(value.name, diagnostics=diagnostics),
        }
        if diagnostics:
            record["storage"] = _storage(value)
        return record
    if diagnostics and isinstance(value, pd.Series):
        return {
            "type": "series",
            "index": encode(value.index, diagnostics=True),
            "name": encode(value.name, diagnostics=True),
            "values": encode(value.tolist(), diagnostics=True),
            "storage": _storage(value),
            "attrs": encode(value.attrs, diagnostics=True),
        }
    if isinstance(value, pd.DataFrame):
        record = {
            "type": "table",
            "index": encode(value.index, diagnostics=diagnostics),
            "columns": encode(value.columns, diagnostics=diagnostics),
            "values": [
                encode(value.iloc[:, i].tolist(), diagnostics=diagnostics)
                for i in range(len(value.columns))
            ],
        }
        if diagnostics:
            record["storage"] = [
                _storage(value.iloc[:, i]) for i in range(len(value.columns))
            ]
            record["attrs"] = encode(value.attrs, diagnostics=True)
        return record
    if isinstance(value, np.ndarray):
        if value.dtype.kind not in ("biuf" if diagnostics else "iuf"):
            raise TypeError("model arrays must contain real numbers")
        record = {
            "type": "array",
            "shape": list(value.shape),
            "values": encode(value.ravel().tolist(), diagnostics=diagnostics),
        }
        if diagnostics:
            record["storage"] = _storage(value)
        return record
    if sparse.issparse(value):
        coo = value.tocoo()
        record = {
            "type": "sparse",
            "shape": list(coo.shape),
            "rows": coo.row.tolist(),
            "columns": coo.col.tolist(),
            "values": encode(coo.data.tolist(), diagnostics=diagnostics),
        }
        if diagnostics:
            record["storage"] = _storage(coo.data)
        return record
    if type(value) is Scenarios:
        return {
            "type": "scenarios",
            "arguments": encode_arguments(
                dict(
                    values=value._values,
                    horizon=value.horizon,
                    unit=value.unit,
                    probabilities=value._probabilities,
                    asset_ids=value.asset_ids,
                    scenario_ids=value.scenario_ids,
                    origin=value.origin,
                    **(
                        {"metadata": value.metadata} if value._metadata else {}
                    ),
                )
            ),
        }
    if type(value) is ScenarioPaths:
        return {
            "type": "scenario_paths",
            "arguments": encode_arguments(
                dict(
                    values=value._values,
                    horizon=value.horizon,
                    step_horizon=value.step_horizon,
                    unit=value.unit,
                    probabilities=value._probabilities,
                    asset_ids=value.asset_ids,
                    scenario_ids=value.scenario_ids,
                    step_ids=value.step_ids,
                    origin=value.origin,
                    metadata=value.metadata,
                )
            ),
        }
    if type(value) is ScenarioTree:
        return {
            "type": "scenario_tree",
            "arguments": encode_arguments(
                dict(
                    information=value.information,
                    times=value._times,
                    probabilities=value._probabilities,
                    origin=value.origin,
                    metadata=value.metadata,
                )
            ),
        }
    if type(value) is FactorRisk:
        return {
            "type": "factor_risk",
            "arguments": encode_arguments(
                dict(
                    exposures=value._b,
                    factor_covariance=value._f,
                    specific_variance=value._d,
                    asset_ids=value.asset_ids,
                    factor_ids=value._factors,
                )
            ),
        }
    if isinstance(value, tuple):
        return {
            "type": "tuple",
            "values": [
                encode(item, diagnostics=diagnostics) for item in value
            ],
        }
    if isinstance(value, list):
        return [encode(item, diagnostics=diagnostics) for item in value]
    if isinstance(value, dict):
        if any(not _mapping_key(key, diagnostics) for key in value):
            raise ValueError("unsupported financial mapping key")
        return {
            "type": "mapping",
            "items": [
                [
                    encode(key, diagnostics=diagnostics),
                    encode(item, diagnostics=diagnostics),
                ]
                for key, item in value.items()
            ],
        }
    raise TypeError(f"unsupported model input type: {type(value).__name__}")


def encode_arguments(arguments, *, diagnostics=False):
    return {
        key: encode(value, diagnostics=diagnostics)
        for key, value in arguments.items()
    }


def _list(value):
    if type(value) is not list:
        raise ValueError("expected a JSON array")
    return value


def _shape(value):
    shape = _list(value)
    if any(type(item) is not int or item < 0 for item in shape):
        raise ValueError("array dimensions must be nonnegative integers")
    return tuple(shape)


def _numbers(value, *, diagnostics=False, storage=None):
    values = [decode(item, diagnostics=diagnostics) for item in _list(value)]
    if diagnostics:
        if type(storage) is not dict or storage.get("kind") not in {
            "boolean",
            "integer",
            "unsigned_integer",
            "float",
        }:
            raise ValueError(
                "numeric array storage must declare a numeric kind"
            )
        return _column(values, pd.RangeIndex(len(values)), storage).to_numpy()
    if any(type(item) not in (int, float) for item in values):
        raise ValueError("array values must be real numbers")
    array = np.asarray(values, dtype=float)
    if not np.isfinite(array).all():
        raise ValueError("array values must be finite")
    return array


def decode(value, *, diagnostics=False):
    if value is None or type(value) in (str, int, bool):
        return value
    if type(value) is float:
        if not np.isfinite(value):
            raise ValueError("model inputs must be finite")
        return value
    if type(value) is list:
        return [decode(item, diagnostics=diagnostics) for item in value]
    if type(value) is not dict or not isinstance(value.get("type"), str):
        raise ValueError("expected a JSON value or a typed model input")
    kind = value["type"]
    if diagnostics and kind in {"date", "datetime"}:
        fields(value, {"type", "value"})
        if not isinstance(value["value"], str):
            raise ValueError("calendar values must be canonical ISO text")
        parsed = (date if kind == "date" else datetime).fromisoformat(
            value["value"]
        )
        if parsed.isoformat() != value["value"]:
            raise ValueError("calendar values must be canonical ISO text")
        return parsed
    if diagnostics and kind in {"nonfinite", "missing"}:
        fields(value, {"type", "value"})
        choices = (
            {"nan": float("nan"), "+inf": float("inf"), "-inf": -float("inf")}
            if kind == "nonfinite"
            else {"NA": pd.NA, "NaT": pd.NaT}
        )
        if (
            not isinstance(value["value"], str)
            or value["value"] not in choices
        ):
            raise ValueError(f"invalid {kind} value")
        return choices[value["value"]]
    if diagnostics and kind == "datetime_index":
        fields(value, {"type", "timezone", "values", "name"})
        items = decode(_list(value["values"]), diagnostics=True)
        zone = value["timezone"]
        return _datetime_index(
            items, zone, decode(value["name"], diagnostics=True)
        )
    if diagnostics and kind == "multi_index":
        fields(value, {"type", "levels", "codes", "names"})
        levels = [
            decode(level, diagnostics=True) for level in _list(value["levels"])
        ]
        codes = _list(value["codes"])
        names = decode(_list(value["names"]), diagnostics=True)
        if (
            not levels
            or len(codes) != len(levels)
            or len(names) != len(levels)
        ):
            raise ValueError("multi-index levels, codes and names must align")
        length = len(_list(codes[0]))
        for level, positions in zip(levels, codes):
            if (
                not isinstance(level, pd.Index)
                or len(_list(positions)) != length
            ):
                raise ValueError("multi-index codes must have equal length")
            if any(
                type(i) is not int or not -1 <= i < len(level)
                for i in positions
            ):
                raise ValueError("multi-index codes must be in-range integers")
        return pd.MultiIndex(
            levels=levels, codes=codes, names=names, verify_integrity=True
        )
    if diagnostics and kind == "series":
        fields(value, {"type", "index", "name", "values", "storage", "attrs"})
        index = decode(value["index"], diagnostics=True)
        if not isinstance(index, pd.Index):
            raise ValueError("series index must be an index record")
        items = decode(_list(value["values"]), diagnostics=True)
        series = _column(items, index, value["storage"])
        series.name = decode(value["name"], diagnostics=True)
        attrs = decode(value["attrs"], diagnostics=True)
        if type(attrs) is not dict:
            raise ValueError("series attrs must be a mapping")
        series.attrs = attrs
        return series
    if kind == "tuple":
        fields(value, {"type", "values"})
        return tuple(
            decode(item, diagnostics=diagnostics)
            for item in _list(value["values"])
        )
    if kind == "integer":
        fields(value, {"type", "value"})
        number = value["value"]
        if not isinstance(number, str):
            raise ValueError("integer value must be decimal text")
        integer = int(number)
        if str(integer) != number:
            raise ValueError("integer value must use canonical decimal text")
        return integer
    if kind == "timestamp":
        fields(value, {"type", "value"})
        if not isinstance(value["value"], str):
            raise ValueError("timestamp value must be ISO-8601 text")
        timestamp = pd.Timestamp(value["value"])
        if pd.isna(timestamp):
            raise ValueError("timestamp must not be missing")
        canonical = value["value"]
        if canonical.endswith("Z"):
            canonical = canonical[:-1] + "+00:00"
        if timestamp.isoformat() != canonical:
            raise ValueError("timestamp must use canonical ISO-8601 text")
        return timestamp
    if kind == "index":
        if diagnostics:
            fields(value, {"type", "values", "name", "storage"})
            items = decode(_list(value["values"]), diagnostics=True)
            series = _column(
                items, pd.RangeIndex(len(items)), value["storage"]
            )
            return pd.Index(
                series,
                dtype=series.dtype,
                name=decode(value["name"], diagnostics=True),
                tupleize_cols=False,
            )
        fields(value, {"type", "values", "name"})
        return pd.Index(
            decode(_list(value["values"]), diagnostics=diagnostics),
            name=decode(value["name"], diagnostics=diagnostics),
            tupleize_cols=False,
        )
    if kind == "array":
        fields(
            value,
            {"type", "shape", "values"}
            | ({"storage"} if diagnostics else set()),
        )
        shape = _shape(value["shape"])
        numbers = _numbers(
            value["values"],
            diagnostics=diagnostics,
            storage=value.get("storage"),
        )
        if prod(shape) != len(numbers):
            raise ValueError("array values do not match shape")
        return numbers.reshape(shape)
    if kind == "sparse":
        fields(
            value,
            {"type", "shape", "rows", "columns", "values"}
            | ({"storage"} if diagnostics else set()),
        )
        shape = _shape(value["shape"])
        if len(shape) != 2:
            raise ValueError("sparse inputs require two dimensions")
        numbers = _numbers(
            value["values"],
            diagnostics=diagnostics,
            storage=value.get("storage"),
        )
        rows, columns = _list(value["rows"]), _list(value["columns"])
        if len(rows) != len(numbers) or len(columns) != len(numbers):
            raise ValueError("sparse coordinates must match values")
        for positions, size in zip((rows, columns), shape):
            if any(type(i) is not int or not 0 <= i < size for i in positions):
                raise ValueError(
                    "sparse coordinates must be in-range integers"
                )
        # COO storage depends on entries, not an unvalidated row count.
        return sparse.coo_matrix((numbers, (rows, columns)), shape=shape)
    if kind == "table":
        if diagnostics:
            fields(
                value,
                {"type", "index", "columns", "values", "storage", "attrs"},
            )
            index = decode(value["index"], diagnostics=True)
            columns = decode(value["columns"], diagnostics=True)
            if not isinstance(index, pd.Index) or not isinstance(
                columns, pd.Index
            ):
                raise ValueError("table axes must be index records")
            values, storage = _list(value["values"]), _list(value["storage"])
            if len(values) != len(columns) or len(storage) != len(columns):
                raise ValueError("table values and storage must match columns")
            series = [
                _column(decode(_list(items), diagnostics=True), index, kind)
                for items, kind in zip(values, storage)
            ]
            frame = (
                pd.concat(series, axis=1)
                if series
                else pd.DataFrame(index=index)
            )
            frame.columns = columns
            attrs = decode(value["attrs"], diagnostics=True)
            if type(attrs) is not dict:
                raise ValueError("table attrs must be a mapping")
            frame.attrs = attrs
            return frame
        fields(value, {"type", "index", "columns", "values"})
        index, columns = decode(value["index"]), decode(value["columns"])
        if not isinstance(index, pd.Index) or not isinstance(
            columns, pd.Index
        ):
            raise ValueError("table axes must be index records")
        if not index.is_unique or not columns.is_unique:
            raise ValueError("table axes must be unique")
        values = _list(value["values"])
        if len(values) != len(columns):
            raise ValueError("table values must match columns")
        frame = pd.DataFrame(index=index)
        for column, items in zip(columns, values):
            items = decode(_list(items))
            if len(items) != len(index):
                raise ValueError("table column length must match index")
            frame[column] = items
        frame.columns = columns
        return frame
    if kind == "mapping":
        fields(value, {"type", "items"})
        mapping = {}
        for entry in _list(value["items"]):
            if type(entry) is not list or len(entry) != 2:
                raise ValueError("mapping entries must be key/value pairs")
            key, item = (
                decode(entry[0], diagnostics=diagnostics),
                decode(entry[1], diagnostics=diagnostics),
            )
            if not _mapping_key(key, diagnostics):
                raise ValueError("unsupported financial mapping key")
            if key in mapping:
                raise ValueError("mapping keys must be unique")
            mapping[key] = item
        return mapping
    if kind in {"scenarios", "scenario_paths", "scenario_tree", "factor_risk"}:
        fields(value, {"type", "arguments"})
        constructor = {
            "scenarios": Scenarios,
            "scenario_paths": ScenarioPaths,
            "scenario_tree": ScenarioTree,
            "factor_risk": FactorRisk,
        }[kind]
        return constructor(**decode_arguments(value["arguments"]))
    raise ValueError(f"unsupported model input type: {kind!r}")


def decode_arguments(arguments, *, diagnostics=False):
    if type(arguments) is not dict or any(
        not isinstance(key, str) for key in arguments
    ):
        raise ValueError("arguments must be a JSON object with string keys")
    return {
        key: decode(value, diagnostics=diagnostics)
        for key, value in arguments.items()
    }


def _storage(series):
    kind = series.dtype.kind
    if kind == "M":
        zone = series.dt.tz
        return {"kind": "datetime", "timezone": str(zone) if zone else None}
    if kind in "biuf" and pd.api.types.is_extension_array_dtype(series.dtype):
        kind = "O"
    names = {
        "b": "boolean",
        "i": "integer",
        "u": "unsigned_integer",
        "f": "float",
        "O": "object",
    }
    if kind not in names:
        raise TypeError(f"unsupported result column dtype: {series.dtype}")
    return {"kind": names[kind]}


def _datetime_index(items, zone, name=None):
    if zone is not None and not isinstance(zone, str):
        raise ValueError("timezone must be text or None")
    if any(
        item is not pd.NaT and not isinstance(item, pd.Timestamp)
        for item in items
    ):
        raise ValueError("datetime values must be timestamp or NaT records")
    if any(
        item is not pd.NaT and (item.tzinfo is None) != (zone is None)
        for item in items
    ):
        raise ValueError("datetime timezone must match timestamp awareness")
    if zone is None:
        return pd.DatetimeIndex(items, name=name)
    try:
        return pd.DatetimeIndex(
            pd.to_datetime(items, utc=True), name=name
        ).tz_convert(zone)
    except (KeyError, ValueError) as error:
        raise ValueError("datetime timezone is not recognized") from error


def _column(items, index, storage):
    if len(items) != len(index):
        raise ValueError("column length must match index")
    if type(storage) is not dict or not isinstance(storage.get("kind"), str):
        raise ValueError("column storage must declare its kind")
    kind = storage["kind"]
    if kind == "datetime":
        fields(storage, {"kind", "timezone"})
        return pd.Series(
            _datetime_index(items, storage["timezone"]), index=index
        )
    fields(storage, {"kind"})
    if kind == "object":
        return pd.Series(items, index=index, dtype=object)
    if kind == "boolean" and all(type(item) is bool for item in items):
        return pd.Series(items, index=index, dtype=bool)
    if kind in {"integer", "unsigned_integer"} and all(
        type(item) is int for item in items
    ):
        lower, upper = (
            (-(2**63), 2**63 - 1) if kind == "integer" else (0, 2**64 - 1)
        )
        if all(lower <= item <= upper for item in items):
            return pd.Series(
                items,
                index=index,
                dtype="int64" if kind == "integer" else "uint64",
            )
    if kind == "float" and all(type(item) in (int, float) for item in items):
        return pd.Series(items, index=index, dtype=float)
    raise ValueError("column values do not match declared storage")
