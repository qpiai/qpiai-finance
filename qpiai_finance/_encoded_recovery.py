"""Recover original financial decisions through a retained Opt decoder."""

from copy import deepcopy
from importlib.metadata import version
from time import perf_counter

import numpy as np
import pandas as pd

from ._validation import scalar


def recover(raw, *, model, opt_model, tolerance):
    from qpiai_opt.opt_modeller import Model

    from ._opt_recovery import (
        _finish_recovery,
        _recorded_metadata,
        _source_data,
    )
    from ._solvers.opt import _result_data
    from ._workflow import _financial_result
    from .quantum._execution import _observations, _quantum_info

    started = perf_counter()
    if not isinstance(opt_model, Model):
        raise TypeError(
            "polynomial/gate recovery requires opt_model: the retained "
            "Opt Model after explicit binary compilation; for "
            "compile_portfolio records, pass the original "
            "PortfolioEncoding as model"
        )
    tolerance = scalar(tolerance, "tolerance", minimum=0)
    raw = type(raw).model_validate(raw.model_dump(mode="python"))
    quantum = hasattr(raw, "quantum")
    if raw.problem_class not in {"QUBO", "HUBO", "ISING"}:
        raise ValueError("Hamiltonian estimation has no financial decision")
    snapshot, decoder = deepcopy(model), deepcopy(opt_model)
    preparation_started = perf_counter()
    _, data = _source_data(snapshot, mode=raw.execution_mode)
    names = {variable.name for variable in decoder.variables()}
    if names != set(data["variable_names"]):
        raise ValueError("opt_model must contain exactly the source variables")
    if decoder.sense.lower() != data["sense"]:
        raise ValueError("opt_model sense does not match the financial model")
    if getattr(raw, "sense", None) not in {None, decoder.sense}:
        raise ValueError("recorded sense does not match opt_model")
    if not any(
        item.get("stage") == "objective_normalization"
        for item in decoder.transformations()
    ):
        raise ValueError("opt_model has no retained binary compilation")
    if raw.problem_class == "HUBO":
        decode = decoder.decode_hubo_sample
        encoded_names = decoder.hubo_variable_names
    else:
        decode = decoder.decode_qubo_sample
        encoded_names = decoder.qubo_variable_names
    build_time = perf_counter() - preparation_started

    def evaluate(sample, assignment, objective):
        values = np.asarray(sample)
        allowed = (-1, 1) if raw.problem_class == "ISING" else (0, 1)
        if (
            values.shape != (len(encoded_names),)
            or not np.isin(values, allowed).all()
        ):
            raise ValueError("sample must match the retained binary register")
        bits = (values + 1) // 2 if raw.problem_class == "ISING" else values
        decoded = decode(bits.tolist())
        if set(decoded) != names or assignment != decoded:
            raise ValueError("recorded assignment disagrees with Opt decoding")
        value = decoder.evaluate_objective(decoded)
        if objective is None or not np.isclose(
            value, objective, atol=tolerance, rtol=1e-7
        ):
            raise ValueError(
                "recorded source objective disagrees with Opt model"
            )
        checked = snapshot._evaluate_solution(decoded, tolerance=tolerance)
        native_feasible = decoder.is_feasible(decoded, tolerance=tolerance)
        bitstring = "".join(str(int(bit)) for bit in reversed(bits))
        return bitstring, decoded, checked, native_feasible

    records, choices = [], []

    def register(
        point,
        reported,
        *,
        count=None,
        probability=None,
        energy=None,
        reported_feasible=None,
        primary=False,
    ):
        bitstring, decoded, checked, native_feasible = point
        feasible = checked["feasible"] and native_feasible
        records.append(
            {
                "bitstring": bitstring,
                "count": count,
                "probability": probability,
                "reported_count": raw.quantum.counts.get(bitstring, 0),
                "reported_objective": reported,
                "objective": checked["objective"],
                "feasible": feasible,
                "financial_feasible": checked["feasible"],
                "opt_model_feasible": native_feasible,
                "reported_feasible": reported_feasible,
                "energy": energy,
                "maximum_violation": float(
                    checked["constraints"].violation.max()
                ),
                "reported_primary": primary,
            }
        )
        if feasible:
            sign = 1 if data["sense"] == "min" else -1
            choices.append(
                (
                    sign * checked["objective"],
                    bitstring,
                    decoded,
                    reported,
                    native_feasible,
                )
            )

    selected = None
    if quantum:
        if raw.solve_info is None:
            raise ValueError(
                "recorded quantum result requires solve information"
            )
        _quantum_info(raw, tolerance)
        measured, observations = _observations(raw)
        for sample in measured:
            point = evaluate(
                sample.solution, sample.variable_assignment, sample.objective
            )
            if point[0] != sample.bitstring:
                raise ValueError(
                    "quantum sample disagrees with MSB-first bit order"
                )
            register(
                point,
                sample.objective,
                count=sample.count,
                probability=sample.probability,
                energy=sample.internal_energy,
                reported_feasible=sample.feasible,
            )
        if raw.solution is not None:
            point = evaluate(
                raw.solution, raw.variable_assignment, raw.objective
            )
            primary = point[0]
            matching = next(
                (row for row in records if row["bitstring"] == primary), None
            )
            if matching is None:
                register(point, raw.objective, primary=True)
            else:
                matching["reported_primary"] = True
        if choices:
            selected = min(choices, key=lambda item: item[:2])
    elif raw.solution is not None:
        bitstring, decoded, _, native_feasible = evaluate(
            raw.solution, raw.variable_assignment, raw.objective
        )
        selected = (0, bitstring, decoded, raw.objective, native_feasible)

    _, info, recorded = _result_data(raw)
    solution = None if selected is None else selected[2]
    info, details = _recorded_metadata(
        info, recorded, has_solution=solution is not None
    )
    if selected is not None:
        info["source_objective"] = selected[3]
        details["source_objective"] = selected[3]
        details["selected_bitstring"] = selected[1]
    else:
        info["source_objective"] = details["source_objective"] = None
    details.update(
        financial_problem_class=data["problem_type"],
        verification_scope="decoded_source_decision_and_objective",
        sample_decoding_verified=bool(records or selected is not None),
        encoded_energy_verified=False,
        encoding_auxiliaries_verified=False,
    )
    if quantum:
        details["quantum"] = raw.quantum.model_dump(mode="json")
        details["candidate_observations"] = observations
    result = _financial_result(
        snapshot,
        solution,
        info,
        details,
        tolerance=tolerance,
        build_time=build_time,
        solve_time=None,
    )
    if selected is not None:
        valid = selected[4]
        result.constraints.loc["opt_model_constraints"] = {
            "value": float(valid),
            "lower": 1.0,
            "upper": 1.0,
            "violation": float(not valid),
            "satisfied": valid,
            "unit": "dimensionless",
        }
        result.feasible = bool(result.feasible and valid)
        if not valid:
            result.status = "verification_failed"
    result.transformations.extend(decoder.transformations())
    if quantum:
        result.tables["quantum_samples"] = (
            pd.DataFrame(records).set_index("bitstring")
            if records
            else pd.DataFrame()
        )
        result.tables["quantum_samples"].attrs.update(
            encoded_energy_verified=False,
            encoding_auxiliaries_verified=False,
            probability_scope=raw.quantum.algorithm_metadata.get(
                "candidate_distribution", "provider candidates"
            ),
        )
        result.tables["quantum_history"] = pd.DataFrame(
            {"training_objective": raw.quantum.objective_history}
        ).rename_axis("evaluation")
        result.provenance["quantum_result_origin"] = (
            "recorded_opt_quantum_result"
        )
        result.provenance["versions"]["qpiai-quantum"] = version(
            "qpiai-quantum"
        )
    return _finish_recovery(
        result, has_solution=solution is not None, started=started
    )
