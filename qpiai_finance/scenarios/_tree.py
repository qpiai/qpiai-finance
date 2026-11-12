"""Explicit information histories for financial scenario decisions."""

from copy import deepcopy

import numpy as np
import pandas as pd
from scipy import sparse

from .._arithmetic import probability_masses, weighted_mean
from .._validation import (
    copy_index,
    identifiers,
    instant,
    matrix,
    numeric,
    same_labels,
    scalar,
    vector,
)
from .._validation import probabilities as checked_probabilities
from ..cashflows import _date
from ._models import _metadata
from ._paths import ScenarioPaths, _step_ids


class ScenarioTree:
    """Information nodes shared by scenarios on an ordered decision grid.

    information is a scenario-by-stage table of integer or string node IDs.
    Cases sharing a node have the same observed history at that stage. Every
    case starts at the same root; histories may branch but cannot recombine.
    Node IDs are globally unique across stages. Distinct cases may share a
    complete information path, including its terminal node.

    times supplies strictly increasing calendar dates or timezone-aware
    instants, optionally as a Series indexed by stage ID. It can be omitted
    when the information table has actual dated columns. No calendar,
    information history or scenario probabilities are inferred from values.
    Omit probabilities for a probability-free stress tree.
    """

    def __init__(
        self,
        information,
        *,
        times=None,
        probabilities=None,
        scenario_ids=None,
        stage_ids=None,
        origin=None,
        metadata=None,
    ):
        if isinstance(information, pd.DataFrame):
            cases = identifiers(
                information.index if scenario_ids is None else scenario_ids,
                "scenario_ids",
            )
            stages = _step_ids(
                information.columns if stage_ids is None else stage_ids
            )
            same_labels(information.index, cases, "information scenarios")
            source_stages = _step_ids(information.columns, ordered=False)
            if (
                len(stages) != len(source_stages)
                or not stages.isin(source_stages).all()
            ):
                raise ValueError("information stages must match stage_ids")
            source = information.copy(deep=False)
            source.columns = source_stages
            values = source.reindex(index=cases, columns=stages).to_numpy(
                dtype=object, copy=True
            )
        else:
            values = np.array(information, dtype=object, copy=True)
            if values.ndim != 2 or 0 in values.shape:
                raise ValueError("information must be a nonempty matrix")
            cases = identifiers(
                range(values.shape[0])
                if scenario_ids is None
                else scenario_ids,
                "scenario_ids",
            )
            stages = _step_ids(
                range(values.shape[1]) if stage_ids is None else stage_ids
            )
            if values.shape != (len(cases), len(stages)):
                raise ValueError("information dimensions must match IDs")
        if times is None:
            if not isinstance(stages, pd.DatetimeIndex):
                raise ValueError("times is required for undated stage IDs")
            times = stages
        elif isinstance(times, pd.Series):
            labels = _step_ids(times.index, ordered=False)
            if len(labels) != len(stages) or not stages.isin(labels).all():
                raise ValueError("times must align with stage_ids")
            times = times.copy(deep=False)
            times.index = labels
            times = times.reindex(stages).tolist()
        else:
            times = list(times)
        if len(times) != len(stages):
            raise ValueError("times must contain one time per stage")
        try:
            _date(times[0], "stage time")
        except (TypeError, ValueError):
            parse = instant
        else:
            parse = _date
        clock = pd.DatetimeIndex([parse(t, "stage time") for t in times])
        if not clock.is_unique or not clock.is_monotonic_increasing:
            raise ValueError("stage times must be strictly increasing")

        # One parent per node encodes the complete observed history.
        identifiers(values.ravel(), "information nodes", unique=False)
        if np.any(values[:, 0] != values[0, 0]):
            raise ValueError("all scenarios must share one root node")
        node_positions, node_ids, parents, depths = {}, [], [], []
        paths = np.empty(values.shape, dtype=np.intp)
        for stage in range(len(stages)):
            for case in range(len(cases)):
                node = values[case, stage]
                if isinstance(node, np.integer):
                    node = int(node)
                    values[case, stage] = node
                parent = -1 if stage == 0 else paths[case, stage - 1]
                if node not in node_positions:
                    node_positions[node] = len(node_ids)
                    node_ids.append(node)
                    parents.append(parent)
                    depths.append(stage)
                position = node_positions[node]
                if depths[position] != stage or parents[position] != parent:
                    raise ValueError(
                        "each information node must have one stage and "
                        "one parent; histories cannot recombine"
                    )
                paths[case, stage] = position
        if origin is not None and (
            not isinstance(origin, str) or not origin.strip()
        ):
            raise ValueError("origin must be nonempty text when supplied")
        self._probabilities = (
            None
            if probabilities is None
            else checked_probabilities(probabilities, cases)
        )
        self._information = values
        self._cases = cases.copy(deep=True)
        self._stages = stages.copy(deep=True)
        self._times = clock.copy(deep=True)
        self._node_ids = identifiers(node_ids, "node_ids")
        self._node_positions = node_positions
        self._parents = np.asarray(parents, dtype=np.intp)
        self._depths = np.asarray(depths, dtype=np.intp)
        self._paths = paths
        self._node_probabilities = None
        self._conditional_probabilities = None
        if self._probabilities is not None:
            masses, total = probability_masses(self._probabilities)
            node_masses = np.zeros(len(node_ids), dtype=object)
            np.add.at(
                node_masses,
                paths.ravel(),
                np.repeat(masses, len(stages)),
            )
            self._node_probabilities = np.fromiter(
                (mass / total for mass in node_masses), dtype=float
            )
            self._conditional_probabilities = np.fromiter(
                (
                    1.0
                    if parent < 0
                    else (
                        mass / node_masses[parent]
                        if node_masses[parent] > 0
                        else np.nan
                    )
                    for mass, parent in zip(node_masses, parents)
                ),
                dtype=float,
            )
        self.origin = origin
        self._metadata = _metadata(metadata)

    @property
    def scenario_ids(self):
        """Case IDs, including distinct cases with identical node paths."""
        return copy_index(self._cases)

    @property
    def stage_ids(self):
        """Stage labels in chronological order."""
        return copy_index(self._stages)

    @property
    def node_ids(self):
        """Node IDs ordered by stage, then first occurrence among cases."""
        return copy_index(self._node_ids)

    @property
    def root(self):
        """The common initial information node ID."""
        return self._node_ids[0]

    @property
    def information(self):
        """Detached scenario-by-stage information node table."""
        return pd.DataFrame(
            self._information.copy(),
            index=self.scenario_ids,
            columns=self.stage_ids,
        )

    @property
    def times(self):
        """Detached stage times; aware instants are normalized to UTC."""
        return pd.Series(
            self._times.copy(deep=True),
            index=self.stage_ids,
            name="time",
        )

    @property
    def probabilities(self):
        """Case probabilities, or None for a stress tree."""
        if self._probabilities is None:
            return None
        return pd.Series(
            self._probabilities.copy(),
            index=self.scenario_ids,
            name="probability",
        )

    @property
    def metadata(self):
        """Detached declared construction records."""
        return deepcopy(self._metadata)

    @property
    def nodes(self):
        """Node parents, stages, times and probability diagnostics.

        probability is unconditional node mass. conditional_probability is
        relative to the parent, with root probability one. Conditioning on
        a zero-mass parent is undefined (NaN). Both probability columns are
        NaN for stress trees. Zero-probability nodes are retained.
        """
        count = len(self._node_ids)
        masses = self._node_probabilities
        return pd.DataFrame(
            {
                "parent": pd.Series(
                    [
                        None if parent < 0 else self._node_ids[parent]
                        for parent in self._parents
                    ],
                    index=self.node_ids,
                    dtype=object,
                ),
                "stage": self.stage_ids.take(self._depths),
                "time": self._times.take(self._depths),
                "probability": (
                    np.full(count, np.nan) if masses is None else masses.copy()
                ),
                "conditional_probability": (
                    np.full(count, np.nan)
                    if masses is None
                    else self._conditional_probabilities.copy()
                ),
            },
            index=self.node_ids,
        )

    def _position(self, node):
        identifiers([node], "node")
        if node not in self._node_positions:
            raise ValueError(f"unknown information node: {node!r}")
        return self._node_positions[node]

    def children(self, node):
        """Immediate child node IDs in tree order."""
        return self.node_ids[self._parents == self._position(node)]

    def ancestors(self, node):
        """Node IDs from the root through the node's parent; excludes node."""
        position = self._position(node)
        result = []
        while self._parents[position] >= 0:
            position = self._parents[position]
            result.append(position)
        return self.node_ids.take(result[::-1])

    def expected(self, values, *, given=None):
        """Expected scalar case values, optionally conditional on a node.

        values is a case-indexed Series/mapping or an array in scenario order.
        No probabilities are invented for stress trees or zero-mass events.
        This calculation does not establish a decision's feasibility.
        Original probability ratios and values are retained until the final
        expected value is rounded to float64, including when conditioning.
        """
        if self._probabilities is None:
            raise ValueError("expected values require explicit probabilities")
        values = vector(values, self._cases, "case values")
        weights = self._probabilities
        if given is not None:
            position = self._position(given)
            cases = self._paths[:, self._depths[position]] == position
            values, weights = values[cases], weights[cases]
            if not np.any(weights > 0):
                raise ValueError("cannot condition on a zero-probability node")
        return float(weighted_mean(values, weights))

    def paths(self, values, *, horizon, step_horizon, unit, asset_ids=None):
        """Expand supplied node-by-instrument values into ScenarioPaths.

        Includes every stage, including the root. Values at a shared node
        are identical across its cases. It is the caller's responsibility to
        supply values in the declared units, including root-period values;
        no return, price, cash flow or discount factor is inferred.
        """
        if isinstance(values, pd.DataFrame):
            assets = values.columns if asset_ids is None else asset_ids
        else:
            shape = (
                values.shape if sparse.issparse(values) else np.shape(values)
            )
            if len(shape) != 2:
                raise ValueError("node values must be a matrix")
            assets = range(shape[1]) if asset_ids is None else asset_ids
        assets = identifiers(assets)
        values = matrix(values, self._node_ids, assets, "node values")
        expanded = values[self._paths.ravel()]
        if sparse.issparse(expanded):
            expanded = expanded.toarray()
        return ScenarioPaths(
            expanded.reshape(*self._paths.shape, len(assets)),
            horizon=horizon,
            step_horizon=step_horizon,
            unit=unit,
            probabilities=self._probabilities,
            scenario_ids=self._cases,
            step_ids=self._stages,
            asset_ids=assets,
            origin=self.origin,
            metadata={
                "source": self.metadata,
                "information": self._information.tolist(),
                "stage_times": [time.isoformat() for time in self._times],
            },
        )

    def validate_policy(
        self, decisions, *, timing="after_observation", tolerance=1e-7
    ):
        """Check decision agreement within each stage's information groups.

        decisions is ScenarioPaths or a scenario-by-stage-by-control array.
        after_observation permits conditioning on the current node;
        before_observation permits only the preceding stage's information
        (the root at stage zero). All cases participate, including stress and
        zero-probability cases. Decisions are neither averaged nor repaired.
        violation is max minus min within each information group, measured
        in decision units; tolerance is absolute in those same units.
        This checks information timing, not financial feasibility/optimality.
        """
        if timing not in {"after_observation", "before_observation"}:
            raise ValueError(
                "timing must be 'after_observation' or 'before_observation'"
            )
        tolerance = scalar(tolerance, "tolerance", minimum=0)
        unit = "decision_units"
        if isinstance(decisions, ScenarioPaths):
            same_labels(decisions.scenario_ids, self._cases, "policy cases")
            steps = decisions.step_ids
            if (
                len(steps) != len(self._stages)
                or not self._stages.isin(steps).all()
            ):
                raise ValueError("policy periods must match tree stages")
            values = decisions._values[
                decisions.scenario_ids.get_indexer(self._cases)
            ][:, steps.get_indexer(self._stages)]
            controls = decisions.asset_ids
            unit = decisions.unit
        else:
            values = numeric(decisions, "decisions", ndim=3)
            if values.shape[:2] != self._paths.shape or values.shape[2] == 0:
                raise ValueError(
                    "decisions require one row per scenario/stage and "
                    "at least one control"
                )
            controls = pd.RangeIndex(values.shape[2])
        frames = []
        for stage, stage_id in enumerate(self._stages):
            observed = (
                stage if timing == "after_observation" else max(0, stage - 1)
            )
            nodes, groups = np.unique(
                self._paths[:, observed], return_inverse=True
            )
            minimum = np.full((len(nodes), len(controls)), np.inf)
            maximum = np.full_like(minimum, -np.inf)
            np.minimum.at(minimum, groups, values[:, stage])
            np.maximum.at(maximum, groups, values[:, stage])
            with np.errstate(over="ignore", invalid="ignore"):
                violation = maximum - minimum
            if not np.isfinite(violation).all():
                raise ValueError("policy differences exceed float64 range")
            index = pd.MultiIndex.from_product(
                [[stage_id], self._node_ids.take(nodes), controls],
                names=["stage", "information_node", "control"],
            )
            frames.append(
                pd.DataFrame(
                    {
                        "minimum": minimum.ravel(),
                        "maximum": maximum.ravel(),
                        "violation": violation.ravel(),
                        "satisfied": (violation <= tolerance).ravel(),
                    },
                    index=index,
                )
            )
        result = pd.concat(frames)
        result.attrs.update(unit=unit, timing=timing, tolerance=tolerance)
        return result
