"""Historical windows and paired bootstrap indices for financial paths."""

from hashlib import sha256
from numbers import Integral

import numpy as np
import pandas as pd

from .._validation import identifiers, numeric, same_labels
from ..data import _known_history


def _integer(value, name, minimum=1):
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Integral):
        raise TypeError(f"{name} must be an integer")
    value = int(value)
    if value < minimum:
        raise ValueError(f"{name} must be at least {minimum}")
    return value


def _history(
    observations,
    *,
    as_of,
    observed_at,
    available_at,
    asset_ids,
    unit,
    horizon,
    step_horizon,
):
    for name, value in (
        ("unit", unit),
        ("horizon", horizon),
        ("step_horizon", step_horizon),
    ):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{name} must describe its financial convention")
    selected, observed, available, positions, cutoff = _known_history(
        observations,
        as_of=as_of,
        observed_at=observed_at,
        available_at=available_at,
    )
    if not len(selected):
        raise ValueError("history has no observations available as_of")
    if isinstance(selected, pd.Series):
        selected = selected.to_frame(
            0 if selected.name is None else selected.name
        )
    if isinstance(selected, pd.DataFrame):
        assets = identifiers(
            selected.columns if asset_ids is None else asset_ids
        )
        same_labels(selected.columns, assets, "history assets")
        selected = selected.reindex(columns=assets).to_numpy()
    else:
        selected = np.asarray(selected)
        if selected.ndim == 1:
            selected = selected[:, None]
        assets = identifiers(
            range(selected.shape[1]) if asset_ids is None else asset_ids
        )
    # Unavailable rows may contain placeholders; validate only selected values.
    values = numeric(
        selected.tolist() if selected.dtype.kind == "O" else selected,
        "available history",
        ndim=2,
    )
    if values.shape != (len(observed), len(assets)) or not len(observed):
        raise ValueError(
            "history must contain available observations and aligned assets"
        )
    if unit == "simple_return" and np.any(values < -1):
        raise ValueError("simple asset returns cannot be below -1")

    def timestamp(value):
        return (
            value.date().isoformat()
            if cutoff.tzinfo is None
            else value.isoformat()
        )

    metadata = {
        "as_of": timestamp(cutoff),
        "time_basis": "calendar_date"
        if cutoff.tzinfo is None
        else "aware_instant",
        "availability": "observation_time"
        if available_at is None
        else "supplied",
        "observation_times": [timestamp(value) for value in observed],
        "available_at": [timestamp(value) for value in available],
        "source_positions": positions.tolist(),
        "source_values_sha256": sha256(
            np.asarray(values, dtype="<f8", order="C").data
        ).hexdigest(),
    }
    return values, assets, positions, metadata


def historical(
    cls,
    observations,
    *,
    as_of,
    periods,
    step_horizon,
    horizon,
    unit,
    probabilities,
    stride,
    observed_at,
    available_at,
    asset_ids,
    scenario_ids,
    step_ids,
):
    periods = _integer(periods, "periods")
    stride = _integer(stride, "stride")
    values, assets, positions, metadata = _history(
        observations,
        as_of=as_of,
        observed_at=observed_at,
        available_at=available_at,
        asset_ids=asset_ids,
        unit=unit,
        horizon=horizon,
        step_horizon=step_horizon,
    )
    if periods > len(values):
        raise ValueError("periods exceed available history")
    starts = np.arange(len(values) - periods + 1)
    starts = starts[(positions[starts] - positions[0]) % stride == 0]
    # Endpoint separation suffices since source positions strictly increase.
    starts = starts[
        positions[starts + periods - 1] - positions[starts] == periods - 1
    ]
    if not len(starts):
        raise ValueError(
            "no complete consecutive historical windows are available"
        )
    indices = starts[:, None] + np.arange(periods)
    if isinstance(probabilities, str):
        if probabilities != "equal":
            raise ValueError(
                "probabilities must be 'equal', None or explicit weights"
            )
        probabilities = np.full(len(starts), 1 / len(starts))
    metadata.update(
        method="historical", stride=stride, sample_indices=indices.tolist()
    )
    return cls(
        values[indices],
        horizon=horizon,
        step_horizon=step_horizon,
        unit=unit,
        probabilities=probabilities,
        asset_ids=assets,
        scenario_ids=scenario_ids,
        step_ids=step_ids,
        origin="historical",
        metadata=metadata,
    )


def bootstrap(
    cls,
    observations,
    *,
    as_of,
    periods,
    samples,
    step_horizon,
    horizon,
    unit,
    method,
    seed,
    block_size,
    observed_at,
    available_at,
    asset_ids,
    scenario_ids,
    step_ids,
):
    periods, samples = (
        _integer(periods, "periods"),
        _integer(samples, "samples"),
    )
    seed = _integer(seed, "seed", minimum=0)
    if method not in {"iid", "moving_block", "circular_block"}:
        raise ValueError(
            "method must be 'iid', 'moving_block' or 'circular_block'"
        )
    if method == "iid" and block_size is not None:
        raise ValueError("iid sampling does not use block_size")
    if method != "iid":
        block_size = _integer(block_size, "block_size")
    values, assets, positions, metadata = _history(
        observations,
        as_of=as_of,
        observed_at=observed_at,
        available_at=available_at,
        asset_ids=asset_ids,
        unit=unit,
        horizon=horizon,
        step_horizon=step_horizon,
    )
    count = len(values)
    rng = np.random.Generator(np.random.PCG64(seed))
    if method == "iid":
        indices = rng.integers(count, size=(samples, periods))
    else:
        if block_size > count:
            raise ValueError("block_size exceeds available history")
        if np.any(np.diff(positions) != 1):
            raise ValueError(
                "block sampling requires contiguous available history"
            )
        blocks = (periods + block_size - 1) // block_size
        limit = count if method == "circular_block" else count - block_size + 1
        starts = rng.integers(limit, size=(samples, blocks))
        offsets = np.arange(periods)
        indices = starts[:, offsets // block_size] + offsets % block_size
        if method == "circular_block":
            indices %= count
    metadata.update(
        method=method,
        seed=seed,
        block_size=block_size,
        bit_generator="PCG64",
        numpy_version=np.__version__,
        sample_indices=indices.tolist(),
        probability_model="uniform_empirical",
    )
    return cls(
        values[indices],
        horizon=horizon,
        step_horizon=step_horizon,
        unit=unit,
        probabilities=np.full(samples, 1 / samples),
        asset_ids=assets,
        scenario_ids=scenario_ids,
        step_ids=step_ids,
        origin="bootstrap",
        metadata=metadata,
    )
