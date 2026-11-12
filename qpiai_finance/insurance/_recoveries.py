"""Basic recovery functions before contract-specific adjustments."""

import numpy as np
import pandas as pd

from .._validation import copy_index, numeric, scalar


def _recover(losses, calculation):
    values = (
        losses.to_numpy()
        if isinstance(losses, (pd.Series, pd.DataFrame))
        else losses
    )
    values = numeric(values, "losses", ndim=np.ndim(values))
    if np.any(values < 0):
        raise ValueError("gross losses must be nonnegative")
    recovered = calculation(values)
    if isinstance(losses, pd.Series):
        return pd.Series(
            recovered, index=copy_index(losses.index), name="recovery"
        )
    if isinstance(losses, pd.DataFrame):
        return pd.DataFrame(
            recovered,
            index=copy_index(losses.index),
            columns=copy_index(losses.columns),
        )
    return float(recovered) if recovered.ndim == 0 else recovered


def excess_of_loss(losses, *, attachment, limit):
    """Return min(max(loss - attachment, 0), limit) per supplied loss.

    This is a fixed layer before deductibles, event/annual aggregates,
    reinstatements, exclusions, coinsurance, counterparty risk or inuring
    order. Apply it to the correct covered loss basis, not automatically
    to an annual aggregate or losses already ceded elsewhere. It does not
    price a contract or compose overlapping recoveries.
    """
    attachment = scalar(attachment, "attachment", minimum=0)
    limit = scalar(limit, "limit", minimum=0)
    return _recover(
        losses,
        lambda values: np.minimum(np.maximum(values - attachment, 0), limit),
    )


def quota_share(losses, *, share):
    """Return share * supplied gross loss before other contractual terms.

    share is in [0, 1]. Commission, premium, exclusions, limits, inuring
    order and collectibility are separate inputs. This does not establish
    that standalone recoveries may be added to other contracts.
    """
    share = scalar(share, "share", minimum=0, maximum=1)
    return _recover(losses, lambda values: share * values)
