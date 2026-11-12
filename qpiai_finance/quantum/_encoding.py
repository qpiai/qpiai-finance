"""Portfolio decoding and execution of native binary representations."""

from copy import deepcopy
from math import fsum
from time import perf_counter

import numpy as np
import pandas as pd

from .._validation import copy_index, numeric, same_labels, scalar, vector


def _polynomial_value(polynomial, assignment):
    return fsum(
        coefficient * np.prod([assignment[name] for name in term])
        for term, coefficient in polynomial.items()
    )


class PortfolioEncoding:
    """A detached financial model, Opt problem and inverse asset mapping.

    Create with compile_portfolio. Samples use the variable order exposed
    by variable_names, or mappings keyed by those names. Ising samples
    contain -1/+1 spins; QUBO and HUBO samples contain 0/1 bits. Source
    weights retain the fixed allocation size even for infeasible samples.
    """

    def __init__(
        self,
        portfolio,
        problem,
        names,
        objective,
        violations,
        details,
        conversion,
        build_time,
    ):
        self._portfolio = portfolio
        self._problem = problem
        self._names = names
        self._objective = objective
        self._violations = violations
        self._details = details
        self._conversion = conversion
        self._build_time = build_time

    @property
    def problem(self):
        """Return a detached authoritative Opt problem."""
        return deepcopy(self._problem)

    @property
    def variable_names(self):
        return tuple(self._problem.variable_names)

    @property
    def variable_mapping(self):
        """Original selection variables and their fixed investment weights."""
        return pd.DataFrame(
            {
                "variable": self._names,
                "asset_id": copy_index(self._portfolio._ids),
                "selected_weight": self._details["weight_per_selected_asset"],
            }
        )

    @property
    def transformations(self):
        return [deepcopy(self._details)]

    @property
    def objective_polynomial(self):
        """Return the binary minimization objective before penalties."""
        return self._objective.copy()

    @property
    def compilation_settings(self):
        """Detached compile_portfolio arguments for source-model recovery.

        Retain the source model and package versions alongside these values.
        None strength retains Opt's automatic quadratization rule; actual
        auxiliary coefficients and guarantees remain in transformations.
        """
        return {
            "representation": self._details["representation"],
            "penalty": self._details["penalty"],
            "quadratization_strength": self._details.get(
                "quadratization_strength"
            ),
        }

    def inspect(self, *, algorithm=None):
        """Inspect source settings, Opt capacity metrics and binary mappings.

        The report includes original financial inputs and transformations;
        variable_mapping is a pandas DataFrame. No solve or authentication
        occurs, and structural validity does not establish feasibility.
        An Opt quantum algorithm adds its actual compatibility and logical
        circuit/resource report without executing circuits.
        """
        from qpiai_opt.opt_solvers import inspect

        from .._workflow import _specification

        if algorithm is not None:
            from ._execution import check_algorithm

            check_algorithm(self, algorithm)
        return {
            "financial_model": _specification(self._portfolio),
            "optimization": inspect(self._problem, algorithm=algorithm),
            "transformations": self.transformations,
            "variable_mapping": self.variable_mapping,
        }

    def _sample(self, sample):
        values = vector(sample, pd.Index(self.variable_names), "sample")
        allowed = (
            (-1, 1) if self._details["representation"] == "ising" else (0, 1)
        )
        if not np.isin(values, allowed).all():
            raise ValueError(f"sample values must belong to {allowed}")
        return values.astype(int)

    def _binary_assignment(self, values):
        if self._details["representation"] == "ising":
            values = (values + 1) // 2
        return dict(zip(self.variable_names, values))

    def decode(self, sample):
        """Restore portfolio weights without repairing a sample."""
        values = self._sample(sample)
        assignment = self._binary_assignment(values)
        weight = self._details["weight_per_selected_asset"]
        return pd.Series(
            [weight * assignment[name] for name in self._names],
            index=copy_index(self._portfolio._ids),
            name="weight",
        )

    def encode_selection(self, selected):
        """Encode asset selection bits, completing any product auxiliaries.

        Mappings use asset identifiers; arrays use the source asset order.
        This operation does not require a financially feasible selection.
        """
        bits = vector(selected, self._portfolio._ids, "selected")
        if not np.isin(bits, (0, 1)).all():
            raise ValueError("selected must contain only 0/1 bits")
        sample = bits.astype(int).tolist()
        if self._conversion is not None:
            sample = self._conversion.complete_sample(sample)
        if self._details["representation"] == "ising":
            sample = [2 * bit - 1 for bit in sample]
        return sample

    def energy(self, sample):
        """Evaluate the minimized representation, including all penalties."""
        values = self._sample(sample)
        representation = self._details["representation"]
        if representation == "ising":
            return self._problem.energy(values)
        if representation == "hubo":
            return float(
                _polynomial_value(
                    self._problem.polynomial_dict,
                    dict(zip(self.variable_names, values)),
                )
            )
        return fsum(
            [
                self._problem.offset,
                *(
                    coefficient * values[i] * values[j]
                    for (i, j), coefficient in self._problem.qubo_dict.items()
                ),
            ]
        )

    def evaluate(self, sample, *, tolerance=1e-7):
        """Check a complete sample against original financial constraints."""
        tolerance = scalar(tolerance, "tolerance", minimum=0)
        values = self._sample(sample)
        assignment = self._binary_assignment(values)
        weights = self.decode(sample)
        evaluation = self._portfolio.evaluate(weights, tolerance=tolerance)
        evaluation["decision"] = {"weights": weights}
        evaluation["energy"] = self.energy(sample)
        evaluation["selection_penalty"] = self._details[
            "penalty"
        ] * _polynomial_value(self._violations, assignment)
        valid = (
            self._conversion is None
            or self._conversion.verify_auxiliaries(assignment)
        )
        evaluation["auxiliaries_valid"] = valid
        evaluation["constraints"].loc["product_auxiliaries"] = [
            float(valid),
            1.0,
            1.0,
            float(not valid),
            valid,
        ]
        evaluation["feasible"] = evaluation["feasible"] and valid
        return evaluation

    def evaluate_samples(self, samples, *, tolerance=1e-7):
        """Return source feasibility and objectives for a matrix of samples.

        DataFrame columns must be the complete variable names. Rows retain
        their identifiers; arrays use variable_names column order.
        """
        tolerance = scalar(tolerance, "tolerance", minimum=0)
        if isinstance(samples, pd.DataFrame):
            same_labels(
                samples.columns,
                pd.Index(self.variable_names),
                "sample columns",
            )
            if not samples.index.is_unique:
                raise ValueError("sample row identifiers must be unique")
            rows = [(index, row) for index, row in samples.iterrows()]
        else:
            if np.ndim(samples) != 2:
                raise ValueError("samples must be a two-dimensional matrix")
            values = numeric(samples, "samples", ndim=2)
            if values.shape[1] != len(self.variable_names):
                raise ValueError("samples must have one column per variable")
            rows = list(enumerate(values))
        records = []
        for index, sample in rows:
            evaluation = self.evaluate(sample, tolerance=tolerance)
            records.append(
                {
                    "sample": index,
                    "objective": evaluation["objective"],
                    "feasible": evaluation["feasible"],
                    "energy": evaluation["energy"],
                    "selection_penalty": evaluation["selection_penalty"],
                    "auxiliaries_valid": evaluation["auxiliaries_valid"],
                }
            )
        return pd.DataFrame(
            records,
            columns=[
                "sample",
                "objective",
                "feasible",
                "energy",
                "selection_penalty",
                "auxiliaries_valid",
            ],
        ).set_index("sample")

    def decode_result(self, result, *, tolerance=1e-7):
        """Recover a FinanceResult from a recorded Opt result offline.

        Native QUBO/HUBO/Ising records must match this encoding's named
        sample order and energy. QuantumResult records additionally verify
        measured and declared residual candidates, selecting the best valid
        original financial objective. Counts retain their reported scope.
        No sample is repaired and no authentication or execution is asserted.
        Recorded results never establish new global financial optimality.
        """
        from qpiai_opt.quantum import QuantumResult

        from ._execution import recover

        if isinstance(result, QuantumResult):
            return recover(self, result, tolerance=tolerance)
        return self._native_result(
            result, tolerance=tolerance, solve_time=None
        )

    def _financial_solution(self, sample, evaluation):
        assignment = self._binary_assignment(self._sample(sample))
        weights = evaluation["decision"]["weights"].to_numpy()
        solution = {}
        for i, name in enumerate(self._names):
            solution[f"weight_{i}"] = weights[i]
            solution[f"selected_positive_{i}"] = assignment[name]
            solution[f"selected_negative_{i}"] = 0
        return solution

    def solve(
        self,
        *,
        client=None,
        mode="local",
        algorithm=None,
        execution=None,
        allow_platform=False,
        tolerance=1e-7,
        **options,
    ):
        """Run an Opt native or explicitly selected gate-based algorithm.

        Every solve verifies an Opt Client. Gate execution additionally uses
        Opt's QpiAIQuantumAuth and QuantumRun, including local simulation.
        Supply an authoritative Opt algorithm explicitly; QUBO/Ising gate
        results are heuristic and checked against original finance. Native
        HUBO remains available without an algorithm. Native mode='auto'
        follows Opt routing, with Platform fallback only when
        allow_platform=True. Gate algorithms require local/platform mode.
        """
        from qpiai_opt.opt_solvers import solve

        from .._workflow import _execution_mode

        tolerance = scalar(tolerance, "tolerance", minimum=0)
        mode = _execution_mode(mode, allow_platform, "qpiai")
        if client is None:
            raise ValueError("solving requires an authenticated Opt Client")
        if algorithm is not None:
            from ._execution import run

            if allow_platform:
                raise ValueError(
                    "allow_platform is not valid for gate algorithms; "
                    "choose mode='local' or 'platform' explicitly"
                )
            if mode == "auto":
                raise ValueError(
                    "mode='auto' is not supported for gate algorithms; "
                    "choose 'local' or 'platform'"
                )
            return run(
                self,
                algorithm,
                execution,
                client=client,
                mode=mode,
                tolerance=tolerance,
                options=options,
            )
        if execution is not None:
            raise ValueError(
                "execution requires an explicit quantum algorithm"
            )
        started = perf_counter()
        raw = solve(
            self._problem,
            client=client,
            mode=mode,
            allow_platform=allow_platform,
            **options,
        )
        elapsed = perf_counter() - started
        result = self._native_result(
            raw, tolerance=tolerance, solve_time=elapsed
        )
        result.solver_info["requested_execution_mode"] = mode
        result.solver_info["allow_platform"] = allow_platform
        return result

    def _native_result(self, raw, *, tolerance, solve_time):
        from qpiai_opt.opt_solvers import IsingSolveResult
        from qpiai_opt.opt_solvers.hubo import SolveResult as HUBOSolveResult
        from qpiai_opt.opt_solvers.qubo import SolveResult as QUBOSolveResult

        from .._opt_recovery import _finish_recovery, _recorded_metadata
        from .._solvers.opt import _result_data
        from .._workflow import _financial_result

        postprocess_started = perf_counter()
        recorded = solve_time is None
        tolerance = scalar(tolerance, "tolerance", minimum=0)
        if type(raw) not in (
            QUBOSolveResult,
            HUBOSolveResult,
            IsingSolveResult,
        ):
            raise TypeError(
                "result must be an Opt QUBO, HUBO or Ising SolveResult"
            )
        if recorded:
            raw = type(raw).model_validate(raw.model_dump(mode="python"))
        if raw.problem_class != self._details["representation"].upper():
            raise ValueError(
                "result class must match the encoded representation"
            )
        if raw.solution is not None:
            values = self._sample(raw.solution)
            if raw.variable_assignment != dict(
                zip(self.variable_names, values)
            ):
                raise ValueError(
                    "result variable mapping must match sample order"
                )
        _, info, details = _result_data(raw)
        if recorded:
            info, details = _recorded_metadata(
                info, details, has_solution=raw.solution is not None
            )
        details["reported_encoded_objective"] = raw.objective
        details["encoded_objective"] = None
        details["compilation_settings"] = self.compilation_settings
        solution = None
        if raw.solution is not None:
            evaluation = self.evaluate(raw.solution, tolerance=tolerance)
            energy = evaluation["energy"]
            details["encoded_objective"] = energy
            if not np.isclose(
                raw.objective, energy, atol=tolerance, rtol=1e-7
            ):
                raise ValueError(
                    "solver objective disagrees with encoded energy"
                )
            sign = -1 if self._details["source_sense"] == "MAX" else 1
            info["source_objective"] = sign * (
                energy - evaluation["selection_penalty"]
            )
            details["source_objective"] = info["source_objective"]
            solution = self._financial_solution(raw.solution, evaluation)
            details["selection_penalty"] = evaluation["selection_penalty"]
            details["auxiliaries_valid"] = evaluation["auxiliaries_valid"]
            info["optimality_proven"] &= evaluation["auxiliaries_valid"]
        result = _financial_result(
            self._portfolio,
            solution,
            info,
            details,
            tolerance=tolerance,
            build_time=None if recorded else self._build_time,
            solve_time=solve_time,
        )
        result.transformations.extend(self.transformations)
        result.tables["binary_variables"] = self.variable_mapping
        if solution is not None:
            valid = details["auxiliaries_valid"]
            result.constraints.loc["product_auxiliaries"] = [
                float(valid),
                1.0,
                1.0,
                float(not valid),
                valid,
            ]
            if not valid:
                result.feasible = result.optimality_proven = False
                result.status = "verification_failed"
        result.provenance["timing_s"]["postprocess"] = (
            perf_counter() - postprocess_started
        )
        if recorded:
            return _finish_recovery(
                result,
                has_solution=solution is not None,
                started=postprocess_started,
            )
        return result
