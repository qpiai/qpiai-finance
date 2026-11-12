"""Portable numeric artifacts; no executable object serialization."""

import json
from datetime import date, datetime

import numpy as np
import pandas as pd
from scipy import sparse


def identifier_label(value):
    """Render a validated ID without merging integer and string labels."""
    return repr(int(value) if isinstance(value, np.integer) else value)


def portable(value):
    if value is pd.NaT or value is pd.NA:
        return None
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, (pd.DataFrame, pd.Series)):
        frame = value.to_frame() if isinstance(value, pd.Series) else value
        return {
            "index": portable(frame.index.tolist()),
            "columns": portable(frame.columns.tolist()),
            "data": portable(frame.to_numpy()),
        }
    if sparse.issparse(value):
        coo = value.tocoo()
        return {
            "format": "coo",
            "shape": list(coo.shape),
            "row": coo.row.tolist(),
            "col": coo.col.tolist(),
            "data": portable(coo.data.tolist()),
        }
    if isinstance(value, (np.ndarray, pd.Index)):
        return portable(value.tolist())
    if isinstance(value, np.generic):
        return portable(value.item())
    if isinstance(value, dict):
        result = {str(key): portable(item) for key, item in value.items()}
        if len(result) != len(value):
            raise ValueError(
                "report mapping keys must remain unique as text; "
                "use qpiai_finance.io.to_dict to preserve key types"
            )
        return result
    if isinstance(value, (tuple, list)):
        return [portable(item) for item in value]
    if isinstance(value, float) and not np.isfinite(value):
        # Diagnostic bounds can be infinite; some risk measures are undefined.
        return None
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError(f"unsupported artifact type: {type(value).__name__}")


def dumps(value):
    return json.dumps(
        value, sort_keys=True, allow_nan=False, separators=(",", ":")
    )
