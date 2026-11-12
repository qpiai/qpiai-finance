"""Labeled financial scenarios, stress cases and construction metadata."""

import json
from copy import deepcopy

import numpy as np
import pandas as pd
from scipy import sparse

from .._arithmetic import row_products, weighted_mean
from .._validation import copy_index, identifiers, matrix, matrix_input, vector
from .._validation import probabilities as checked_probabilities

__all__ = ["Scenarios"]


def _metadata(value):
    if value is None:
        return {}
    if type(value) is not dict:
        raise TypeError("metadata must be a JSON-compatible dictionary")
    pending, seen = [value], set()
    while pending:
        item = pending.pop()
        if isinstance(item, (dict, list, tuple)) and id(item) not in seen:
            seen.add(id(item))
            if isinstance(item, dict):
                if any(type(key) is not str for key in item):
                    raise TypeError("metadata keys must be strings")
                pending.extend(item.values())
            else:
                pending.extend(item)
    try:
        return json.loads(json.dumps(value, allow_nan=False))
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError("metadata must contain finite JSON data") from error


class Scenarios:
    """Scenario × instrument values in declared units and common horizon.

    Supply probabilities for a distribution. Omit them for deterministic
    stress cases. Equal weighting is an explicit choice, e.g.
    ``np.full(n, 1/n)``. Inputs are copied; returned tables are detached
    copies. DataFrames and column mappings supply scenario and instrument
    labels; arrays use the supplied IDs or positional labels.
    """

    def __init__(
        self,
        values,
        *,
        horizon,
        unit,
        probabilities=None,
        asset_ids=None,
        scenario_ids=None,
        origin=None,
        metadata=None,
    ):
        if not isinstance(horizon, str) or not horizon.strip():
            raise ValueError("horizon must describe the scenario horizon")
        if not isinstance(unit, str) or not unit.strip():
            raise ValueError("unit must describe the scenario values")
        values = matrix_input(values)
        if isinstance(values, pd.DataFrame):
            assets = values.columns if asset_ids is None else asset_ids
            scenarios = values.index if scenario_ids is None else scenario_ids
        else:
            shape = (
                values.shape if sparse.issparse(values) else np.shape(values)
            )
            if len(shape) != 2:
                raise ValueError("scenario values must be a matrix")
            assets = range(shape[1]) if asset_ids is None else asset_ids
            scenarios = (
                range(shape[0])
                if scenario_ids is None
                else scenario_ids
            )
        self._assets = identifiers(assets)
        self._ids = identifiers(scenarios, "scenario_ids")
        self._values = matrix(values, self._ids, self._assets, "scenarios")
        self._probabilities = (
            None
            if probabilities is None
            else checked_probabilities(probabilities, self._ids)
        )
        self.horizon = horizon
        self.unit = unit
        if origin is not None and (
            not isinstance(origin, str) or not origin.strip()
        ):
            raise ValueError("origin must be nonempty text when supplied")
        self.origin = origin
        self._metadata = _metadata(metadata)

    @property
    def metadata(self):
        """Return detached construction records."""
        return deepcopy(self._metadata)

    @property
    def asset_ids(self):
        return copy_index(self._assets)

    @property
    def scenario_ids(self):
        return copy_index(self._ids)

    @property
    def values(self):
        if sparse.issparse(self._values):
            return pd.DataFrame.sparse.from_spmatrix(
                self._values, index=self.scenario_ids, columns=self.asset_ids
            )
        return pd.DataFrame(
            self._values.copy(),
            index=self.scenario_ids,
            columns=self.asset_ids,
        )

    @property
    def probabilities(self):
        if self._probabilities is None:
            return None
        return pd.Series(
            self._probabilities.copy(),
            index=self.scenario_ids,
            name="probability",
        )

    def evaluate(self, quantities):
        """Aggregate supplied scenario values by instrument quantity."""
        quantities = vector(quantities, self._assets, "quantities")
        try:
            values = np.fromiter(
                row_products(self._values, quantities), dtype=float
            )
        except OverflowError as error:
            raise ValueError(
                "scenario exposures exceed float64 range"
            ) from error
        return pd.Series(
            values,
            index=self.scenario_ids,
            name=self.unit,
        )

    def expected(self, quantities):
        """Return the probability-weighted aggregate for supplied quantities.

        Requires explicit scenario probabilities. Quantity labels align by
        asset ID; arrays follow asset_ids. The result retains the supplied
        value/quantity units and horizon without implicit annualization.
        Instrument products and probability ratios are retained until the
        final mean is rounded; individual cases need not fit in float64.
        """
        if self._probabilities is None:
            raise ValueError(
                "expected values require explicit scenario probabilities"
            )
        quantities = vector(quantities, self._assets, "quantities")
        try:
            return float(
                weighted_mean(
                    row_products(self._values, quantities),
                    self._probabilities,
                )
            )
        except OverflowError as error:
            raise ValueError(
                "expected scenario exposure exceeds float64 range"
            ) from error
