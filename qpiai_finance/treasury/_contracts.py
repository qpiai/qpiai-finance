"""Contract lifetimes on observed financial information histories."""

import numpy as np
import pandas as pd

from .._validation import identifiers, instant
from ..cashflows import _date


def stage_position(tree, stage):
    stages = tree.stage_ids
    if isinstance(stages, pd.DatetimeIndex):
        stage = (
            _date(stage, "repayment_stage")
            if stages.tz is None
            else instant(stage, "repayment_stage")
        )
    else:
        identifiers([stage], "repayment_stage")
    if stage not in stages:
        raise ValueError("repayment_stage must belong to the planning stages")
    return stages.get_loc(stage)


def schedule(tree, draw_node, repayment_stage):
    """Return active and repayment nodes, counting each shared node once."""
    start = tree._position(draw_node)
    end = stage_position(tree, repayment_stage)
    descendants = np.zeros(len(tree._node_ids), dtype=bool)
    descendants[start] = True
    for k in range(start + 1, len(descendants)):
        descendants[k] = descendants[tree._parents[k]]
    return (
        np.flatnonzero(descendants & (tree._depths < end)),
        np.flatnonzero(descendants & (tree._depths == end)),
    )
