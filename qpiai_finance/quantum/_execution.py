"""Authoritative gate execution and independent financial sample recovery."""

from copy import deepcopy
from dataclasses import fields, is_dataclass
from importlib.metadata import version
from time import perf_counter

import numpy as np
import pandas as pd

from .._validation import scalar


def check_algorithm(encoding, algorithm):
    from qpiai_opt.quantum import (
        ADAPTQAOA,
        QAOA,
        VQE,
        RecursiveQAOA,
        SamplingVQE,
        XYMixer,
    )

    if not isinstance(
        algorithm, (QAOA, VQE, SamplingVQE, RecursiveQAOA, ADAPTQAOA)
    ):
        raise TypeError(
            "algorithm must be an authoritative Opt quantum algorithm"
        )
    if encoding._details["representation"] == "hubo":
        raise ValueError(
            "Opt gate algorithms require pairwise QUBO or Ising; "
            "compile explicitly with representation='qubo' or 'ising'"
        )
    inner = (
        algorithm.qaoa if isinstance(algorithm, RecursiveQAOA) else algorithm
    )
    if isinstance(inner, QAOA) and isinstance(inner.mixer, XYMixer):
        if not isinstance(inner.initial_state, (list, tuple)):
            raise ValueError(
                "Finance XY mixing requires an explicit initial bit sequence"
            )
        count = len(encoding._names)
        if (
            sum(inner.initial_state[:count])
            != encoding._details["selection_count"]
        ):
            raise ValueError(
                "XY initial selection must match the financial asset count"
            )
        for group in inner.mixer.groups:
            if any(i < count for i in group) and any(
                i >= count for i in group
            ):
                raise ValueError(
                    "XY groups cannot mix asset selections and auxiliaries"
                )


def _configuration(value):
    """Record public provider settings without serializing callback objects."""
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (list, tuple)):
        return [_configuration(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _configuration(item) for key, item in value.items()}
    if is_dataclass(value):
        return {
            item.name: _configuration(getattr(value, item.name))
            for item in fields(value)
            if not item.name.startswith("_")
        }
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    return {
        "user_defined": True,
        "type": f"{type(value).__module__}.{type(value).__qualname__}",
        **(
            {"callable": f"{value.__module__}.{value.__qualname__}"}
            if callable(value) and hasattr(value, "__qualname__")
            else {}
        ),
    }


def run(encoding, algorithm, execution, *, client, mode, tolerance, options):
    from qpiai_opt.opt_solvers import Client, inspect, solve
    from qpiai_opt.quantum import QuantumRun

    if not isinstance(client, Client):
        raise TypeError("client must be an authenticated Opt Client")
    if options:
        raise ValueError(
            "gate settings belong to the Opt algorithm and QuantumRun; "
            f"unexpected options: {sorted(options)}"
        )
    build_started = perf_counter()
    check_algorithm(encoding, algorithm)
    execution = QuantumRun() if execution is None else execution
    if not isinstance(execution, QuantumRun):
        raise TypeError("execution must be an Opt QuantumRun")
    algorithm = deepcopy(algorithm)
    structure = inspect(encoding._problem, algorithm=algorithm)["quantum"]
    configuration = _configuration(algorithm)
    build_time = perf_counter() - build_started
    started = perf_counter()
    client.verify_api_key()
    raw = solve(
        encoding._problem, algorithm=algorithm, execution=execution, mode=mode
    )
    elapsed = perf_counter() - started
    result = recover(encoding, raw, tolerance=tolerance, solve_time=elapsed)
    result.solver_info.update(
        algorithm_configuration=configuration,
        execution_settings=execution.model_dump(mode="json"),
        quantum_structure=structure,
    )
    result.provenance["quantum_result_origin"] = (
        "authenticated_finance_execution"
    )
    result.provenance["timing_s"]["build"] += build_time
    return result


def _observations(raw):
    measured = raw.quantum.candidates
    total = sum(sample.count for sample in measured)
    if any(
        sample.count <= 0
        or not np.isclose(
            sample.probability, sample.count / total, atol=1e-12, rtol=0
        )
        for sample in measured
    ):
        raise ValueError(
            "candidate probabilities must match positive observed counts"
        )
    observed = {sample.bitstring: sample.count for sample in measured}
    if len(observed) != len(measured):
        raise ValueError(
            "quantum candidates require unique full-register bitstrings"
        )
    if any(
        key not in observed or value > observed[key]
        for key, value in raw.quantum.counts.items()
    ):
        raise ValueError(
            "reported counts are not a subset of observed candidates"
        )
    return measured, total


def _quantum_info(raw, tolerance):
    info = raw.info().model_dump(mode="json")
    if info["execution_mode"] != raw.execution_mode or (
        raw.objective is not None
        and (
            info["source_objective"] is None
            or not np.isclose(
                info["source_objective"],
                raw.objective,
                atol=tolerance,
                rtol=1e-7,
            )
        )
    ):
        raise ValueError("recorded quantum solve information is inconsistent")
    return info


def recover(encoding, raw, *, tolerance, solve_time=0.0):
    started = perf_counter()
    from qpiai_opt.quantum import QuantumResult

    from .._workflow import _financial_result

    if not isinstance(raw, QuantumResult):
        raise TypeError("result must be an Opt QuantumResult")
    raw = deepcopy(raw)
    raw = QuantumResult.model_validate(raw.model_dump(mode="python"))
    if raw.solve_info is None:
        raise ValueError("recorded quantum result requires solve information")
    expected = encoding._details["representation"].upper()
    if raw.problem_class != expected or expected not in {"QUBO", "ISING"}:
        raise ValueError(
            "quantum result class must match the encoded representation"
        )
    tolerance = scalar(tolerance, "tolerance", minimum=0)
    records, selections = [], []
    seen = set()

    def candidate(
        bitstring, sample, assignment, energy, count, probability, residual
    ):
        if (
            len(bitstring) != len(encoding.variable_names)
            or not set(bitstring) <= {"0", "1"}
            or bitstring in seen
        ):
            raise ValueError(
                "quantum candidates require unique full-register bitstrings"
            )
        seen.add(bitstring)
        bits = np.array([int(bit) for bit in reversed(bitstring)])
        expected_sample = 2 * bits - 1 if expected == "ISING" else bits
        values = encoding._sample(sample)
        if not np.array_equal(values, expected_sample):
            raise ValueError(
                "quantum sample disagrees with MSB-first bit order"
            )
        named = dict(zip(encoding.variable_names, values))
        if assignment is None or assignment != named:
            raise ValueError(
                "quantum sample variable mapping does not match encoding"
            )
        evaluation = encoding.evaluate(values, tolerance=tolerance)
        if energy is None or not np.isclose(
            energy, evaluation["energy"], atol=tolerance, rtol=1e-7
        ):
            raise ValueError(
                "quantum candidate energy disagrees with the source encoding"
            )
        sign = -1 if encoding._details["source_sense"] == "MAX" else 1
        if evaluation["auxiliaries_valid"] and not np.isclose(
            evaluation["objective"],
            sign * (evaluation["energy"] - evaluation["selection_penalty"]),
            atol=tolerance,
            rtol=1e-7,
        ):
            raise ValueError(
                "encoded and original financial objectives disagree"
            )
        feasible = bool(evaluation["feasible"])
        records.append(
            {
                "bitstring": bitstring,
                "count": count,
                "probability": probability,
                "reported_count": raw.quantum.counts.get(bitstring, 0),
                "energy": evaluation["energy"],
                "objective": evaluation["objective"],
                "feasible": feasible,
                "auxiliaries_valid": evaluation["auxiliaries_valid"],
                "selection_penalty": evaluation["selection_penalty"],
                "maximum_violation": float(
                    evaluation["constraints"].violation.max()
                ),
                "classical_residual": residual,
            }
        )
        if feasible:
            selections.append(
                (sign * evaluation["objective"], bitstring, values, evaluation)
            )

    measured, total = _observations(raw)
    for sample in measured:
        candidate(
            sample.bitstring,
            sample.solution,
            sample.variable_assignment,
            sample.objective,
            sample.count,
            sample.probability,
            False,
        )
        if not np.isclose(
            sample.internal_energy,
            records[-1]["energy"],
            atol=tolerance,
            rtol=1e-7,
        ):
            raise ValueError(
                "internal quantum energy disagrees with the encoded energy"
            )
    residual = raw.quantum.algorithm_metadata.get("residual_candidate")
    if residual is not None:
        if (
            not isinstance(residual, dict)
            or not {"bitstring", "objective", "feasible"} <= residual.keys()
            or type(residual["feasible"]) is not bool
        ):
            raise ValueError("invalid declared residual candidate")
        bitstring = residual["bitstring"]
        if not isinstance(bitstring, str) or not set(bitstring) <= {"0", "1"}:
            raise ValueError("invalid declared residual bitstring")
        bits = [int(bit) for bit in reversed(bitstring)]
        sample = [2 * bit - 1 for bit in bits] if expected == "ISING" else bits
        energy = scalar(residual["objective"], "residual objective")
        if not np.isclose(
            encoding.energy(sample), energy, atol=tolerance, rtol=1e-7
        ):
            raise ValueError(
                "declared residual energy disagrees with encoding"
            )
        if bitstring in seen:
            next(row for row in records if row["bitstring"] == bitstring)[
                "classical_residual"
            ] = True
        else:
            candidate(
                bitstring,
                sample,
                dict(zip(encoding.variable_names, sample)),
                residual["objective"],
                None,
                None,
                True,
            )
    if raw.solution is not None:
        values = encoding._sample(raw.solution)
        bits = (values + 1) // 2 if expected == "ISING" else values
        bitstring = "".join(str(bit) for bit in reversed(bits))
        if (
            bitstring not in seen
            or raw.variable_assignment
            != dict(zip(encoding.variable_names, values))
            or not np.isclose(
                raw.objective,
                encoding.energy(values),
                atol=tolerance,
                rtol=1e-7,
            )
        ):
            raise ValueError(
                "reported quantum best does not match a verified candidate"
            )
    info = _quantum_info(raw, tolerance)
    details = {
        **info,
        "backend_solve_info": deepcopy(info),
        "backend_encoded_best": raw.objective,
        "recorded_solver_time_s": raw.solver_time_s,
        "recorded_compute_time_s": raw.compute_time_s,
        "quantum": raw.quantum.model_dump(mode="json"),
        "candidate_observations": total,
        "compilation_settings": encoding.compilation_settings,
        "optimality_proven": False,
    }
    solution = None
    if selections:
        _, bitstring, values, evaluation = min(
            selections, key=lambda item: item[:2]
        )
        solution = encoding._financial_solution(values, evaluation)
        sign = -1 if encoding._details["source_sense"] == "MAX" else 1
        info["source_objective"] = sign * (
            evaluation["energy"] - evaluation["selection_penalty"]
        )
        details.update(
            selected_bitstring=bitstring,
            encoded_objective=evaluation["energy"],
            source_objective=info["source_objective"],
        )
    else:
        info["termination"] = "no_feasible_sample"
        info["source_objective"] = None
    info["optimality_proven"] = False
    details.update(
        has_usable_solution=solution is not None,
        solution_feasible=solution is not None,
        guarantee="best_found" if solution is not None else "none",
    )
    result = _financial_result(
        encoding._portfolio,
        solution,
        info,
        details,
        tolerance=tolerance,
        build_time=encoding._build_time,
        solve_time=solve_time,
    )
    result.transformations.extend(encoding.transformations)
    result.transformations.extend(raw.quantum.transformations)
    result.tables["binary_variables"] = encoding.variable_mapping
    result.tables["quantum_samples"] = (
        pd.DataFrame(records).set_index("bitstring")
        if records
        else pd.DataFrame()
    )
    result.tables["quantum_history"] = pd.DataFrame(
        {"training_objective": raw.quantum.objective_history}
    ).rename_axis("evaluation")
    result.tables["quantum_samples"].attrs["probability_scope"] = (
        raw.quantum.algorithm_metadata.get(
            "candidate_distribution", "provider candidates"
        )
    )
    result.provenance["versions"]["qpiai-quantum"] = version("qpiai-quantum")
    result.provenance["quantum_result_origin"] = "recorded_opt_quantum_result"
    result.provenance["timing_s"]["postprocess"] = perf_counter() - started
    return result
