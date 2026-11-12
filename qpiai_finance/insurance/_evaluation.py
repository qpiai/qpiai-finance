"""Independent reinsurance cash-loss, recovery and surplus accounting."""

from collections.abc import Mapping
from fractions import Fraction

import numpy as np
import pandas as pd
from scipy import sparse

from .._arithmetic import (
    bound_violation,
    probability_masses,
    product_sum,
    row_products,
    weighted_mean,
)
from .._result_checks import record_reconciliation
from .._validation import copy_index, same_labels, scalar
from ..risk import _tail_mean


def _selections(values, ids):
    if isinstance(values, Mapping):
        values = pd.Series(values)
    if isinstance(values, pd.Series) and len(ids):
        same_labels(values.index, ids, "selections")
        values = values.reindex(ids).to_numpy()
    array = np.asarray(values)
    if array.ndim != 1 or len(array) != len(ids):
        raise ValueError("selections must have one value per contract")
    if len(ids) == 0:
        return np.zeros(0)
    if array.dtype.kind not in "biuf" or not np.isfinite(array).all():
        raise ValueError("selections must be finite numeric or boolean values")
    return array.astype(float, copy=True)


def evaluate(insurance, selections, *, tolerance):
    insurance._check()
    tolerance = scalar(tolerance, "tolerance", minimum=0)
    choices = _selections(selections, insurance._ids)
    contractual = np.fromiter(
        row_products(insurance._recoveries, choices), dtype=object
    )
    factors = insurance._recoverability
    if np.ndim(factors) == 0:
        recovered = contractual * Fraction(factors)
    else:
        recoveries = sparse.csr_matrix(insurance._recoveries)
        factors = factors.tocsr() if sparse.issparse(factors) else factors
        recovered = np.zeros(len(insurance._scenarios), dtype=object)
        for s, (start, end) in enumerate(
            zip(recoveries.indptr[:-1], recoveries.indptr[1:])
        ):
            columns = recoveries.indices[start:end]
            rates = (
                factors[s : s + 1, columns].toarray().ravel()
                if sparse.issparse(factors)
                else factors[s, columns]
            )
            collectible_choices = (
                Fraction(choice) * Fraction(rate)
                for choice, rate in zip(choices[columns], rates)
            )
            recovered[s] = product_sum(
                (recoveries.data[start:end], collectible_choices)
            )
    premium = product_sum((insurance._premiums, choices))
    charges = np.fromiter(
        row_products(insurance._charges, choices), dtype=object
    )
    retained = np.fromiter(
        (
            Fraction(gross) - value
            for gross, value in zip(insurance._gross, recovered)
        ),
        dtype=object,
    )
    total = retained + premium + charges
    checks = []

    def check(name, value, low, high, unit=None):
        reported = float(value)
        if not np.isfinite(reported):
            raise ValueError(
                "reinsurance quantities or values exceed float64 range"
            )
        violation = bound_violation(value, low, high)
        checks.append(
            (
                name,
                reported,
                low,
                high,
                float(violation),
                violation <= tolerance,
                unit or insurance._currency,
            )
        )

    for i, contract in enumerate(insurance._ids):
        check(
            f"selection[{i}:{contract}]",
            choices[i],
            insurance._lower[i],
            insurance._upper[i],
            "binary",
        )
        check(
            f"selection_integer[{i}]",
            abs(choices[i] - np.rint(choices[i])),
            0,
            0,
            "binary",
        )
    count = sum(map(Fraction, choices))
    check("contract_count", count, *insurance._count, unit="contracts")
    if insurance._composition == "exclusive":
        check("exclusive_alternatives", count, 0, 1, "contracts")
    for k, ids in enumerate(insurance._exclusive_groups):
        selected = sum(map(Fraction, choices[insurance._ids.get_indexer(ids)]))
        check(f"exclusive_group[{k}]", selected, 0, 1, "contracts")
    check("premium", premium, 0, insurance._premium_limit)
    for s, scenario in enumerate(insurance._scenarios):
        check(
            f"contractual_recovery[{s}:{scenario}]",
            contractual[s],
            0,
            insurance._gross[s],
        )
        check(
            f"retained_loss[{s}:{scenario}]",
            retained[s],
            0,
            min(insurance._gross[s], insurance._retained_limit[s]),
        )
        check(
            f"total_cost[{s}:{scenario}]",
            total[s],
            0,
            insurance._total_limit[s],
        )
    amounts = {
        "gross_loss": insurance._gross,
        "contractual_recovery": contractual,
        "collectible_recovery": recovered,
        "recovery_shortfall": contractual - recovered,
        "retained_loss": retained,
        "premium": premium,
        "contingent_cost": charges,
        "total_cost": total,
    }
    scenarios = pd.DataFrame(
        {
            name: np.asarray(values, dtype=float)
            for name, values in amounts.items()
        },
        index=copy_index(insurance._scenarios),
    )
    scenarios["currency"] = insurance._currency
    if insurance._surplus is not None:
        after = np.fromiter(
            (
                Fraction(before) - cost
                for before, cost in zip(insurance._surplus, total)
            ),
            dtype=object,
        )
        reported_after = np.asarray(after, dtype=float)
        if not np.isfinite(reported_after).all():
            raise ValueError("insurance surplus exceeds float64 range")
        scenarios["surplus_before_claims"] = insurance._surplus
        scenarios["surplus_after"] = reported_after
        if insurance._surplus_minimum is not None:
            scenarios["minimum_surplus"] = insurance._surplus_minimum
            for s in range(len(total)):
                check(
                    f"surplus[{s}]",
                    after[s],
                    insurance._surplus_minimum[s],
                    np.inf,
                )
    metrics = {
        "premium": float(premium),
        "selected_contracts": int(np.count_nonzero(choices > 0)),
    }
    objective = premium
    if insurance._probabilities is not None:
        p = insurance._probabilities
        scenarios["probability"] = p
        expected = {
            name: weighted_mean(amounts[name], p)
            for name in (
                "gross_loss",
                "contractual_recovery",
                "collectible_recovery",
                "retained_loss",
                "contingent_cost",
                "total_cost",
            )
        }
        metrics.update(
            {
                f"expected_{name}": float(value)
                for name, value in expected.items()
            }
        )

        def tail_mean(losses, confidence):
            order = np.argsort(losses, kind="stable")[::-1]
            masses, mass = probability_masses(p)
            return _tail_mean(losses[order], masses[order], mass, confidence)

        if insurance._objective == "reinsurance_cost":
            objective = expected["total_cost"]
            if insurance._tail_weight > 0:
                tail = tail_mean(total, insurance._confidence)
                metrics["objective_expected_shortfall"] = float(tail)
                weight = Fraction(insurance._tail_weight)
                objective = (1 - weight) * objective + weight * tail
    tails = []
    for (measure, beta), maximum in insurance._tail_limits.items():
        loss = retained if measure == "retained_loss" else total
        actual = tail_mean(loss, beta)
        check(f"expected_shortfall[{measure}:{beta!r}]", actual, 0, maximum)
        tails.append(
            (measure, beta, float(actual), maximum, insurance._currency)
        )
    tables = {
        "reinsurance_scenarios": scenarios,
        "reinsurance_contracts": pd.DataFrame(
            {
                "selection": choices,
                "quoted_premium": insurance._premiums,
                "premium_paid": np.fromiter(
                    (
                        Fraction(quote) * Fraction(choice)
                        for quote, choice in zip(insurance._premiums, choices)
                    ),
                    dtype=float,
                ),
                "minimum_selection": insurance._lower,
                "maximum_selection": insurance._upper,
                "currency": insurance._currency,
            },
            index=copy_index(insurance._ids),
        ),
    }
    if tails:
        tables["expected_shortfall_limits"] = pd.DataFrame(
            tails,
            columns=["measure", "confidence", "actual", "maximum", "currency"],
        )
    exposure_rows = []
    for block, (ids, coefficients, limits) in enumerate(
        insurance._counterparty_limits
    ):
        actual = list(row_products(coefficients, choices))
        for i, identifier in enumerate(ids):
            check(
                f"counterparty[{block}:{i}:{identifier}]",
                actual[i],
                0,
                limits[i],
            )
            exposure_rows.append(
                (
                    block,
                    identifier,
                    float(actual[i]),
                    limits[i],
                    insurance._currency,
                )
            )
    if exposure_rows:
        tables["counterparty_exposures"] = pd.DataFrame(
            exposure_rows,
            columns=[
                "classification",
                "exposure",
                "amount",
                "maximum",
                "currency",
            ],
        )
    objective = float(objective)
    if not np.isfinite(
        np.asarray(
            [
                objective,
                *metrics.values(),
                *contractual,
                *recovered,
                *retained,
                *charges,
                *total,
            ],
            dtype=float,
        )
    ).all():
        raise ValueError(
            "reinsurance quantities or values exceed float64 range"
        )
    constraints = pd.DataFrame(
        checks,
        columns=[
            "constraint",
            "value",
            "lower",
            "upper",
            "violation",
            "satisfied",
            "unit",
        ],
    ).set_index("constraint")
    costs = {"premium": float(premium), "currency": insurance._currency}
    if "expected_contingent_cost" in metrics:
        costs["expected_contingent_cost"] = metrics["expected_contingent_cost"]
    return {
        "objective": objective,
        "feasible": bool(constraints.satisfied.all()),
        "constraints": constraints,
        "decision": {
            "selections": pd.Series(
                choices, index=copy_index(insurance._ids), name="selection"
            )
        },
        "metrics": metrics,
        "tables": tables,
        "costs": costs,
    }


def evaluate_solution(insurance, solution, *, tolerance):
    raw = np.array(
        [
            scalar(solution[f"selection_{i}"], "solver selection")
            for i in range(len(insurance._ids))
        ]
    )
    choices = np.rint(raw)
    evaluation = insurance.evaluate(choices, tolerance=tolerance)
    reconciliation = [
        (
            "premium_reconciliation",
            abs(
                scalar(solution["premium"], "solver premium")
                - evaluation["metrics"]["premium"]
            ),
        )
    ]
    for s, row in enumerate(
        evaluation["tables"]["reinsurance_scenarios"].itertuples()
    ):
        reconciliation.append(
            (
                f"retained_reconciliation[{s}]",
                abs(
                    scalar(solution[f"retained_{s}"], "solver retained loss")
                    - row.retained_loss
                ),
            )
        )
        reconciliation.append(
            (
                f"total_cost_reconciliation[{s}]",
                abs(
                    scalar(solution[f"total_cost_{s}"], "solver total cost")
                    - row.total_cost
                ),
            )
        )
    record_reconciliation(
        evaluation,
        [(name, value, insurance._currency) for name, value in reconciliation],
        tolerance=tolerance,
    )
    if len(raw):
        value = float(np.max(np.abs(raw - choices)))
        evaluation["constraints"].loc["integer_reconstruction"] = [
            value,
            0,
            0,
            value,
            value <= tolerance,
            "binary",
        ]
        evaluation["transformations"] = [
            {
                "type": "contract_selection_reconstruction",
                "constraints_rechecked": True,
            }
        ]
    if "constant_constraint_zero" in solution:
        value = abs(
            scalar(solution["constant_constraint_zero"], "constant row guard")
        )
        evaluation["constraints"].loc["constant_constraint_zero"] = [
            value,
            0,
            0,
            value,
            value <= tolerance,
            "numeric",
        ]
    evaluation["feasible"] = bool(evaluation["constraints"].satisfied.all())
    return evaluation
