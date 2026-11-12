"""Financial values across scenarios, ordered periods and instruments."""

from copy import deepcopy
from datetime import date, datetime

import numpy as np
import pandas as pd

from .._arithmetic import row_products, weighted_mean
from .._validation import copy_index, identifiers, instant, numeric, vector
from ..cashflows import _date
from ..data import _compound_simple_returns
from ._models import Scenarios, _metadata


def _step_ids(values, *, ordered=True):
    labels = pd.Index(values, tupleize_cols=False)
    if len(labels) and all(
        isinstance(value, (date, datetime, pd.Timestamp, np.datetime64))
        for value in labels
    ):
        parse = _date if pd.Timestamp(labels[0]).tzinfo is None else instant
        times = pd.DatetimeIndex(
            [parse(value, "step time") for value in labels]
        )
        if not times.is_unique or (
            ordered and not times.is_monotonic_increasing
        ):
            raise ValueError(
                "dated periods must be unique and strictly increasing"
            )
        return times
    return identifiers(labels, "step_ids")


class ScenarioPaths:
    """Scenario by period by instrument values in declared financial units.

    values is a three-dimensional array or a DataFrame whose two index levels
    are scenario and period. Every scenario has the same ordered periods and
    assets. Supply probabilities for a distribution; omit them for stress
    paths. horizon describes the complete path, step_horizon each input row.
    These paths contain realizations, not a nonanticipative decision policy.
    """

    def __init__(
        self,
        values,
        *,
        horizon,
        step_horizon,
        unit,
        probabilities=None,
        asset_ids=None,
        scenario_ids=None,
        step_ids=None,
        origin=None,
        metadata=None,
    ):
        if not isinstance(step_horizon, str) or not step_horizon.strip():
            raise ValueError(
                "step_horizon must describe each observation period"
            )
        if isinstance(values, pd.DataFrame):
            if (
                not isinstance(values.index, pd.MultiIndex)
                or values.index.nlevels != 2
            ):
                raise ValueError(
                    "path tables require scenario/period index levels"
                )
            if not values.index.is_unique:
                raise ValueError("path scenario/period pairs must be unique")
            assets = identifiers(
                values.columns if asset_ids is None else asset_ids
            )
            scenarios = identifiers(
                values.index.get_level_values(0).unique()
                if scenario_ids is None
                else scenario_ids,
                "scenario_ids",
            )
            steps = _step_ids(
                values.index.get_level_values(1).unique()
                if step_ids is None
                else step_ids,
            )
            if isinstance(steps, pd.DatetimeIndex):
                parse = _date if steps.tz is None else instant
                source = values.copy(deep=False)
                source.index = pd.MultiIndex.from_arrays(
                    [
                        values.index.get_level_values(0),
                        [
                            parse(value, "step time")
                            for value in values.index.get_level_values(1)
                        ],
                    ],
                    names=values.index.names,
                )
            else:
                source = values
            expected = pd.MultiIndex.from_product([scenarios, steps])
            if (
                len(source) != len(expected)
                or not expected.isin(source.index).all()
                or len(assets) != len(values.columns)
                or not assets.isin(values.columns).all()
            ):
                raise ValueError(
                    "path table must cover every scenario, period and asset"
                )
            array = numeric(
                source.reindex(index=expected, columns=assets).to_numpy(),
                "paths",
                ndim=2,
            ).reshape(len(scenarios), len(steps), len(assets))
        else:
            array = numeric(values, "paths", ndim=3)
            if 0 in array.shape:
                raise ValueError("path dimensions must be nonempty")
            scenarios = identifiers(
                range(array.shape[0])
                if scenario_ids is None
                else scenario_ids,
                "scenario_ids",
            )
            steps = _step_ids(
                range(array.shape[1]) if step_ids is None else step_ids,
            )
            assets = identifiers(
                range(array.shape[2]) if asset_ids is None else asset_ids
            )
            if array.shape != (len(scenarios), len(steps), len(assets)):
                raise ValueError(
                    "path IDs must match all three array dimensions"
                )
        base = Scenarios(
            array[:, 0, :],
            horizon=horizon,
            unit=unit,
            probabilities=probabilities,
            scenario_ids=scenarios,
            asset_ids=assets,
            origin=origin,
        )
        if unit == "simple_return" and np.any(array < -1):
            raise ValueError("simple asset returns cannot be below -1")
        self._values = array
        self._assets = assets.copy(deep=True)
        self._ids = scenarios.copy(deep=True)
        self._steps = steps.copy(deep=True)
        self._probabilities = base._probabilities
        self.horizon, self.step_horizon, self.unit = (
            horizon,
            step_horizon,
            unit,
        )
        self.origin = origin
        self._metadata = _metadata(metadata)

    @property
    def asset_ids(self):
        """Instrument identifiers in the array's final-axis order."""
        return copy_index(self._assets)

    @property
    def scenario_ids(self):
        """Scenario identifiers in path order."""
        return copy_index(self._ids)

    @property
    def step_ids(self):
        """Period identifiers in chronological path order."""
        return copy_index(self._steps)

    @property
    def values(self):
        """Return detached values indexed by scenario and period."""
        index = pd.MultiIndex.from_product(
            [self.scenario_ids, self.step_ids], names=["scenario", "period"]
        )
        return pd.DataFrame(
            self._values.reshape(-1, len(self._assets)).copy(),
            index=index,
            columns=self.asset_ids,
        )

    @property
    def probabilities(self):
        """Return explicit scenario probabilities, or None for stress paths."""
        if self._probabilities is None:
            return None
        return pd.Series(
            self._probabilities.copy(),
            index=self.scenario_ids,
            name="probability",
        )

    @property
    def metadata(self):
        """Return detached construction records."""
        return deepcopy(self._metadata)

    def evaluate(self, quantities):
        """Aggregate instruments by fixed quantities separately in each period.

        This is a linear period exposure, not compounded portfolio wealth or
        a trading/backtesting policy. Quantities align by instrument ID.
        """
        quantities = vector(quantities, self._assets, "quantities")
        try:
            values = np.array(
                [
                    list(row_products(path, quantities))
                    for path in self._values
                ],
                dtype=float,
            )
        except OverflowError as error:
            raise ValueError("path exposures exceed float64 range") from error
        result = pd.DataFrame(
            values, index=self.scenario_ids, columns=self.step_ids
        )
        result.attrs.update(unit=self.unit, horizon=self.step_horizon)
        return result

    def expected(self, quantities):
        """Return the weighted fixed-quantity exposure per period.

        Instrument products and probability ratios are retained through the
        mean; rounding occurs only at each reported period's exposure.
        """
        if self._probabilities is None:
            raise ValueError(
                "expected values require explicit scenario probabilities"
            )
        quantities = vector(quantities, self._assets, "quantities")
        try:
            values = np.fromiter(
                (
                    weighted_mean(
                        row_products(self._values[:, period, :], quantities),
                        self._probabilities,
                    )
                    for period in range(len(self._steps))
                ),
                dtype=float,
            )
        except OverflowError as error:
            raise ValueError(
                "expected path exposure exceeds float64 range"
            ) from error
        result = pd.Series(values, index=self.step_ids, name=self.unit)
        result.attrs["horizon"] = self.step_horizon
        return result

    def aggregate(self, *, method):
        """Return terminal Scenarios using explicit 'compound' or 'sum'.

        compound accepts simple_return or log_return paths and returns
        simple_return scenarios for buy-and-hold instruments. sum adds
        log_return or declared additive P&L/cash-flow values without interest
        or discounting. Summing simple asset returns is rejected. Portfolio
        wealth with changing quantities requires its actual cash/holdings
        dynamics, not a sum of this table or a foresight trading policy.
        """
        if method not in {"compound", "sum"}:
            raise ValueError("method must be 'compound' or 'sum'")
        unit = self.unit
        try:
            with np.errstate(over="raise", invalid="raise"):
                if method == "compound":
                    if unit == "simple_return":
                        values = _compound_simple_returns(self._values, axis=1)
                    elif unit != "log_return":
                        raise ValueError(
                            "compound requires asset return units"
                        )
                elif unit == "simple_return":
                    raise ValueError(
                        "simple asset returns require compounding"
                    )
                if method == "sum" or unit == "log_return":
                    periods = np.ones(len(self._steps))
                    totals = (
                        total
                        for path in self._values
                        for total in row_products(path.T, periods)
                    )
                    if method == "compound":
                        # A negative sum below float64 range has zero gross
                        # growth; expm1 therefore rounds to -1.
                        minimum = -np.finfo(float).max
                        totals = (max(total, minimum) for total in totals)
                    values = np.fromiter(totals, dtype=float).reshape(
                        len(self._ids), len(self._assets)
                    )
                    if method == "compound":
                        values = np.expm1(values)
                if method == "compound":
                    unit = "simple_return"
        except (FloatingPointError, OverflowError) as error:
            raise ValueError(
                "aggregated paths exceed float64 range"
            ) from error
        metadata = {
            "source": self.metadata,
            "aggregation": {
                "method": method,
                "input_unit": self.unit,
                "step_horizon": self.step_horizon,
                "periods": len(self._steps),
                "step_ids": [
                    (
                        value.date().isoformat()
                        if value.tzinfo is None
                        else value.isoformat()
                    )
                    if isinstance(value, pd.Timestamp)
                    else value
                    for value in self._steps.tolist()
                ],
                "step_time_basis": (
                    "calendar_date"
                    if self._steps.tz is None
                    else "aware_instant"
                )
                if isinstance(self._steps, pd.DatetimeIndex)
                else None,
            },
        }
        return Scenarios(
            values,
            horizon=self.horizon,
            unit=unit,
            probabilities=self._probabilities,
            asset_ids=self._assets,
            scenario_ids=self._ids,
            origin=self.origin,
            metadata=metadata,
        )

    @classmethod
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
        stride=1,
        observed_at=None,
        available_at=None,
        asset_ids=None,
        scenario_ids=None,
        step_ids=None,
    ):
        """Construct historical windows from observations known as_of.

        probabilities='equal' explicitly selects the empirical distribution;
        None produces unweighted historical stress paths. Other probabilities
        align to resulting scenario IDs. stride counts input observations.
        Unavailable interior rows break a window; no gap is silently bridged.
        Row horizons/cadence are caller supplied, without calendar inference.
        """
        from ._sampling import historical

        return historical(
            cls,
            observations,
            as_of=as_of,
            periods=periods,
            step_horizon=step_horizon,
            horizon=horizon,
            unit=unit,
            probabilities=probabilities,
            stride=stride,
            observed_at=observed_at,
            available_at=available_at,
            asset_ids=asset_ids,
            scenario_ids=scenario_ids,
            step_ids=step_ids,
        )

    @classmethod
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
        block_size=None,
        observed_at=None,
        available_at=None,
        asset_ids=None,
        scenario_ids=None,
        step_ids=None,
    ):
        """Resample joint instrument rows into equally weighted paths.

        Select method='iid', 'moving_block' or 'circular_block' explicitly.
        IID assumes independent identically distributed observations; block
        methods assume a suitable stationary time series and require an
        explicit positive block_size. Cross-asset pairing is always retained.
        Seeds are nonnegative integers; recorded indices and NumPy version
        make the actual sample auditable. This samples paths, not confidence
        intervals or nonanticipative policies. Future prices are not inferred.
        """
        from ._sampling import bootstrap

        return bootstrap(
            cls,
            observations,
            as_of=as_of,
            periods=periods,
            samples=samples,
            step_horizon=step_horizon,
            horizon=horizon,
            unit=unit,
            method=method,
            seed=seed,
            block_size=block_size,
            observed_at=observed_at,
            available_at=available_at,
            asset_ids=asset_ids,
            scenario_ids=scenario_ids,
            step_ids=step_ids,
        )
