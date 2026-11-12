"""Reconstruct funding cash movements from original financial contracts."""

from collections.abc import Mapping
from fractions import Fraction

import numpy as np
import pandas as pd

from .._arithmetic import bound_violation, probability_masses, weighted_mean
from .._result_checks import record_reconciliation
from .._serialization import identifier_label
from .._validation import lot_quantities, lot_residual, scalar, vector
from ..cashflows import _loan_amounts, _loan_expense
from ..risk import _tail_mean


def _decision(values, keys, name):
    keys = pd.Index(list(keys))
    if not len(keys):
        if values is not None:
            empty = np.asarray(
                list(values.values())
                if isinstance(values, Mapping)
                else values
            )
            if empty.ndim != 1 or empty.size:
                raise ValueError(
                    f"no {name} configured: decision must be empty"
                )
        return np.empty(0)
    if values is None:
        raise ValueError(f"provide a complete {name} decision")
    return vector(values, keys, name)


def evaluate(
    funding,
    draws,
    transfers,
    *,
    tolerance,
    investments=None,
    worst_case_cost=None,
    risk_auxiliaries=None,
):
    funding._check_cost_measure()
    tolerance = scalar(tolerance, "tolerance", minimum=0)
    draws = _decision(draws, funding._funding, "draws")
    transfers = _decision(transfers, funding._transfers, "transfers")
    investments = _decision(investments, funding._investments, "investments")
    accounts, dates = funding._ids, funding._periods
    shape = (len(dates), len(accounts))
    movements = {
        name: np.zeros(shape, dtype=object)
        for name in (
            "contractual_inflows",
            "contractual_outflows",
            "draws",
            "principal_repayments",
            "interest",
            "funding_fees",
            "transfer_in",
            "transfer_out",
            "transfer_fees",
            "outstanding_debt",
        )
    }
    investment_tables = {}
    if funding._investments:
        movements["investment_purchases"] = np.zeros(shape, dtype=object)
        movements["investment_cash_flows"] = np.zeros(shape, dtype=object)
    net_funding = np.zeros(shape, dtype=object)
    rows, source_rows, transfer_rows = [], [], []
    reconciliation = []

    def check(name, value, lower, upper, unit, *, solver_auxiliary=False):
        violation = bound_violation(value, lower, upper)
        try:
            report = float(value), float(violation)
        except OverflowError as error:
            raise ValueError(
                "funding cash flows exceed float64 range"
            ) from error
        if solver_auxiliary:
            reconciliation.append((name, report[1], unit))
            return
        rows.append(
            (
                name,
                report[0],
                lower,
                upper,
                report[1],
                violation <= tolerance,
                unit,
            )
        )

    for flow in funding._flows.itertuples():
        t, a = (
            dates.get_loc(getattr(flow, funding._axis)),
            accounts.get_loc(flow.account),
        )
        name = (
            "contractual_inflows"
            if flow.amount >= 0
            else "contractual_outflows"
        )
        movements[name][t, a] += abs(Fraction(flow.amount))
    node_costs = np.zeros((len(dates), 4), dtype=object)

    def loan(key, source, amount, kind, draw_at):
        a = accounts.get_loc(source.account)
        currency = funding._currencies.iloc[a]
        start, live, due = funding._schedule(draw_at, source.repay_at)
        existing = kind == "existing_debt"
        fee = 0 if existing else source.fee
        fixed_fee = 0 if existing else source.fixed_fee
        proceeds, repayment, fees, interest = _loan_amounts(
            amount, source.interest, fee, fixed_fee, original=True
        )
        amount = Fraction(amount)
        fx = Fraction(funding._fx[currency])
        origination = fx * _loan_expense(
            0,
            fees,
            draw_discount=funding._discount[start, a],
            original=True,
        )
        movements["outstanding_debt"][list(live), a] += amount
        if not existing:
            net_funding[start, a] += proceeds
            movements["draws"][start, a] += amount
            movements["funding_fees"][start, a] += fees
            node_costs[start, 0] += origination
            node_costs[start, 2] += fx * fees
        present_cost = origination
        for t in due:
            net_funding[t, a] -= repayment
            movements["principal_repayments"][t, a] += amount
            movements["interest"][t, a] += interest
            expense = fx * _loan_expense(
                interest,
                repayment_discount=funding._discount[t, a],
                original=True,
            )
            node_costs[t, 0] += expense
            node_costs[t, 1] += fx * interest
            present_cost += expense
            if funding._tree is not None:
                source_rows.append(
                    dict(
                        funding_id=key,
                        kind=kind,
                        account=source.account,
                        currency=currency,
                        node=dates[t],
                        event="repayment",
                        principal=amount,
                        interest=interest,
                        origination_fee=0,
                        total_repayment=repayment,
                        discounted_cost_reporting=expense,
                    )
                )
        if funding._tree is not None:
            if not existing:
                source_rows.append(
                    dict(
                        funding_id=key,
                        kind=kind,
                        account=source.account,
                        currency=currency,
                        node=dates[start],
                        event="draw",
                        principal=amount,
                        interest=0,
                        origination_fee=fees,
                        total_repayment=0,
                        discounted_cost_reporting=origination,
                    )
                )
        else:
            source_rows.append(
                dict(
                    funding_id=key,
                    kind=kind,
                    account=source.account,
                    currency=currency,
                    draw_date=draw_at,
                    repayment_date=source.repay_at,
                    principal=amount,
                    interest=interest,
                    origination_fee=fees,
                    total_repayment=repayment,
                    discounted_cost_reporting=present_cost,
                )
            )

    for key, source in funding._existing_debt.items():
        loan(key, source, source.principal, "existing_debt", None)
    for i, (key, source) in enumerate(funding._funding.items()):
        amount = Fraction(draws[i])
        currency = funding._currencies[source.account]
        label = identifier_label(key)
        check(f"draw[{label}]", amount, 0.0, source.maximum, currency)
        if amount != 0:
            check(
                f"minimum_draw[{label}]",
                amount,
                source.minimum,
                np.inf,
                currency,
            )
        if source.lot_size is not None:
            check(
                f"draw_lots[{label}]",
                lot_residual(amount, source.lot_size),
                0,
                0,
                "lots",
            )
        loan(key, source, amount, "new_funding", source.draw_at)
    for i, (key, transfer) in enumerate(funding._transfers.items()):
        amount = Fraction(transfers[i])
        source = accounts.get_loc(transfer.from_account)
        destination = accounts.get_loc(transfer.to_account)
        t = dates.get_loc(transfer.at)
        currency = funding._currencies.iloc[source]
        check(
            f"transfer[{identifier_label(key)}]",
            amount,
            0,
            transfer.maximum,
            currency,
        )
        fee = Fraction(transfer.fee) * amount
        received = Fraction(transfer.exchange_rate) * amount
        movements["transfer_out"][t, source] += amount
        movements["transfer_fees"][t, source] += fee
        movements["transfer_in"][t, destination] += received
        fx = Fraction(funding._fx[currency])
        present_cost = fx * Fraction(funding._discount[t, source]) * fee
        node_costs[t, 0] += present_cost
        node_costs[t, 3] += fx * fee
        transfer_rows.append(
            {
                "transfer_id": key,
                funding._axis: transfer.at,
                "from_account": transfer.from_account,
                "to_account": transfer.to_account,
                "source_currency": currency,
                "destination_currency": funding._currencies.iloc[destination],
                "sent": amount,
                "fee": fee,
                "received": received,
                "exchange_rate": transfer.exchange_rate,
                "discounted_cost_reporting": present_cost,
            }
        )
    if funding._investments:
        try:
            purchases, events = [], []
            purchase_label = (
                "purchase_date" if funding._tree is None else "purchase_node"
            )
            for i, (key, source) in enumerate(funding._investments.items()):
                quantity = Fraction(investments[i])
                label = identifier_label(key)
                a = accounts.get_loc(source.account)
                start = dates.get_loc(source.purchase_at)
                currency = funding._currencies.iloc[a]
                check(
                    f"investment[{label}]",
                    quantity,
                    source.lower,
                    source.upper,
                    "instrument_units",
                )
                if source.lot_size is not None:
                    check(
                        f"investment_lots[{label}]",
                        lot_residual(quantity, source.lot_size),
                        0,
                        0,
                        "lots",
                    )
                outlay = Fraction(source.price) * quantity
                movements["investment_purchases"][start, a] += outlay
                purchases.append(
                    {
                        "investment_id": key,
                        "account": source.account,
                        "currency": currency,
                        purchase_label: source.purchase_at,
                        "quantity": float(quantity),
                        "price": source.price,
                        "purchase_outlay": float(outlay),
                        "lower": source.lower,
                        "upper": source.upper,
                        "lot_size": source.lot_size,
                    }
                )
                entries = [(start, "purchase", -source.price)]
                entries.extend(
                    (t, "cash_flow", source.cash_flows[t])
                    for t in np.flatnonzero(source.cash_flows)
                )
                for t, event, coefficient in entries:
                    amount = Fraction(float(coefficient)) * quantity
                    if event == "cash_flow":
                        movements["investment_cash_flows"][t, a] += amount
                    events.append(
                        {
                            "investment_id": key,
                            funding._axis: dates[t],
                            "event": event,
                            "account": source.account,
                            "currency": currency,
                            "quantity": float(quantity),
                            "unit_cash_flow": coefficient,
                            "cash_flow": float(amount),
                        }
                    )
            if not all(np.isfinite(row["cash_flow"]) for row in events):
                raise ValueError("investment cash flows exceed float64 range")
            investment_tables = {
                "investments": pd.DataFrame(purchases).set_index(
                    "investment_id"
                ),
                "investment_schedule": pd.DataFrame(events).set_index(
                    ["investment_id", funding._axis, "event"]
                ),
            }
        except OverflowError as error:
            raise ValueError(
                "investment cash flows exceed float64 range"
            ) from error
    opening, deposit_interest, closing = (
        np.zeros(shape, dtype=object) for _ in range(3)
    )
    for t in range(len(dates)):
        opening[t] = (
            list(map(Fraction, funding._opening))
            if funding._parents[t] < 0
            else closing[funding._parents[t]]
        )
        deposit_interest[t] = opening[t] * list(
            map(Fraction, funding._returns[t])
        )
        closing[t] = (
            opening[t]
            + deposit_interest[t]
            + movements["contractual_inflows"][t]
            - movements["contractual_outflows"][t]
            + net_funding[t]
            + movements["transfer_in"][t]
            - movements["transfer_out"][t]
            - movements["transfer_fees"][t]
        )
        if funding._investments:
            closing[t] += (
                movements["investment_cash_flows"][t]
                - movements["investment_purchases"][t]
            )
        for a, account in enumerate(accounts):
            currency = funding._currencies.iloc[a]
            check(
                f"cash[{t}:{identifier_label(account)}]",
                closing[t, a],
                funding._cash_lower[t, a],
                funding._cash_upper[t, a],
                currency,
            )
            check(
                f"debt[{t}:{identifier_label(account)}]",
                movements["outstanding_debt"][t, a],
                0,
                funding._debt_upper[t, a],
                currency,
            )
    exposure_tables = {}
    if funding._exposure_limits:
        from ._balance_sheet import evaluate as evaluate_exposures

        principals = dict(zip(funding._funding, draws))
        principals.update(
            {
                key: source.principal
                for key, source in funding._existing_debt.items()
            }
        )
        positions = {
            "investments": dict(zip(funding._investments, investments)),
            "funding": principals,
            "cash": {key: closing[:, a] for a, key in enumerate(accounts)},
        }
        try:
            exposure_tables = evaluate_exposures(
                funding._exposure_limits,
                positions,
                dates,
                funding._axis,
                check,
            )
        except OverflowError as error:
            raise ValueError(
                "balance-sheet exposures exceed float64 range"
            ) from error
    facility_tables = {}
    if funding._facilities:
        from ._facilities import evaluate as evaluate_facilities

        principals = dict(zip(funding._funding, draws))
        principals.update(
            {
                key: source.principal
                for key, source in funding._existing_debt.items()
            }
        )
        facility_tables = evaluate_facilities(
            funding._facilities,
            funding._facility_active(),
            principals,
            dates,
            funding._axis,
            check,
        )
    try:
        cost_columns = [
            "discounted_funding_cost",
            "interest_reporting",
            "funding_fees_reporting",
            "transfer_fees_reporting",
        ]
        if funding._tree is None:
            totals = node_costs.sum(axis=0)
            discounted_cost = totals[0]
            metrics = dict(zip(cost_columns, map(float, totals)))
            scenario_tables = {}
        else:
            tree = funding._tree
            path_costs = np.array(
                [node_costs[path].sum(axis=0) for path in tree._paths],
                dtype=object,
            )
            if worst_case_cost is not None:
                for case, cost in zip(tree._cases, path_costs[:, 0]):
                    check(
                        f"worst_case_cost[{identifier_label(case)}]",
                        cost,
                        -np.inf,
                        worst_case_cost,
                        funding._reporting_currency,
                        solver_auxiliary=True,
                    )
            worst = max(path_costs[:, 0])
            metrics = {"worst_case_funding_cost": float(worst)}
            discounted_cost = worst
            if tree._probabilities is not None:
                expected = weighted_mean(path_costs[:, 0], tree._probabilities)
                metrics["expected_funding_cost"] = float(expected)
                if funding._cost_measure == "expected":
                    discounted_cost = expected
            if (
                funding._cost_measure == "expected_shortfall"
                or funding._tail_limit is not None
            ):
                masses, total = probability_masses(tree._probabilities)
                order = np.argsort(path_costs[:, 0], kind="stable")[::-1]

                def tail(level):
                    return _tail_mean(
                        path_costs[order, 0], masses[order], total, level
                    )

                blocks = []
                if funding._cost_measure == "expected_shortfall":
                    discounted_cost = tail(funding._confidence)
                    metrics["funding_cost_expected_shortfall"] = float(
                        discounted_cost
                    )
                    metrics["expected_shortfall_confidence"] = (
                        funding._confidence
                    )
                    blocks.append(
                        ("funding_objective_es", funding._confidence, None)
                    )
                if funding._tail_limit is not None:
                    cap, level = funding._tail_limit
                    risk = tail(level)
                    metrics["hard_funding_cost_expected_shortfall"] = float(
                        risk
                    )
                    metrics["hard_expected_shortfall_confidence"] = level
                    check(
                        "funding_cost_expected_shortfall",
                        risk,
                        -np.inf,
                        cap,
                        funding._reporting_currency,
                    )
                    blocks.append(("funding_hard_es", level, cap))
                if risk_auxiliaries is not None:
                    for name, level, cap in blocks:
                        eta, excess = risk_auxiliaries[name]
                        for case, cost, value in zip(
                            tree._cases, path_costs[:, 0], excess
                        ):
                            label = identifier_label(case)
                            check(
                                f"{name}_excess[{label}]",
                                value,
                                0,
                                np.inf,
                                funding._reporting_currency,
                                solver_auxiliary=True,
                            )
                            check(
                                f"{name}_loss[{label}]",
                                eta + value - cost,
                                0,
                                np.inf,
                                funding._reporting_currency,
                                solver_auxiliary=True,
                            )
                        if cap is not None:
                            upper = eta + weighted_mean(
                                excess, tree._probabilities
                            ) / (1 - Fraction(level))
                            check(
                                f"{name}_bound",
                                upper,
                                -np.inf,
                                cap,
                                funding._reporting_currency,
                                solver_auxiliary=True,
                            )
            metrics["discounted_funding_cost"] = float(discounted_cost)
            scenario_tables = {
                "funding_information": tree.information,
                "funding_nodes": tree.nodes,
                "funding_scenarios": pd.DataFrame(
                    np.asarray(path_costs, dtype=float),
                    index=tree.scenario_ids,
                    columns=cost_columns,
                ),
            }
            scenario_tables["funding_scenarios"].attrs["currency"] = (
                funding._reporting_currency
            )
            if tree._probabilities is not None:
                scenario_tables["funding_scenarios"]["probability"] = (
                    tree._probabilities
                )
    except OverflowError as error:
        raise ValueError("funding cash flows exceed float64 range") from error
    try:
        movements = {
            name: np.asarray(values, dtype=float)
            for name, values in movements.items()
        }
        opening, deposit_interest, closing, net_funding = (
            np.asarray(values, dtype=float)
            for values in (opening, deposit_interest, closing, net_funding)
        )
        discounted_cost = float(discounted_cost)
        for row in source_rows:
            for name in (
                "principal",
                "interest",
                "origination_fee",
                "total_repayment",
                "discounted_cost_reporting",
            ):
                row[name] = float(row[name])
        for row in transfer_rows:
            for name in (
                "sent",
                "fee",
                "received",
                "discounted_cost_reporting",
            ):
                row[name] = float(row[name])
    except OverflowError as error:
        raise ValueError("funding cash flows exceed float64 range") from error
    if (
        not all(
            np.isfinite(values).all()
            for values in (
                *movements.values(),
                opening,
                closing,
                deposit_interest,
            )
        )
        or not np.isfinite(list(metrics.values())).all()
        or not np.isfinite(np.asarray(node_costs, dtype=float)).all()
    ):
        raise ValueError("funding cash flows exceed float64 range")
    index = pd.MultiIndex.from_product(
        [dates, accounts], names=[funding._axis, "account"]
    )
    ladder = pd.DataFrame(
        {
            "currency": np.tile(funding._currencies.to_numpy(), len(dates)),
            "opening_cash": opening.ravel(),
            "deposit_interest": deposit_interest.ravel(),
            **{name: values.ravel() for name, values in movements.items()},
            "net_funding_cash_flow": net_funding.ravel(),
            "closing_cash": closing.ravel(),
            "cash_buffer": funding._cash_lower.ravel(),
            "cash_upper": funding._cash_upper.ravel(),
            "debt_limit": funding._debt_upper.ravel(),
        },
        index=index,
    )
    constraints = pd.DataFrame(
        rows,
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
    sources = pd.DataFrame(
        source_rows,
        columns=[
            "funding_id",
            "kind",
            "account",
            "currency",
            *(
                ["draw_date", "repayment_date"]
                if funding._tree is None
                else ["node", "event"]
            ),
            "principal",
            "interest",
            "origination_fee",
            "total_repayment",
            "discounted_cost_reporting",
        ],
    ).set_index(
        "funding_id"
        if funding._tree is None
        else ["funding_id", "node", "event"]
    )
    transfers_table = pd.DataFrame(
        transfer_rows,
        columns=[
            "transfer_id",
            funding._axis,
            "from_account",
            "to_account",
            "source_currency",
            "destination_currency",
            "sent",
            "fee",
            "received",
            "exchange_rate",
            "discounted_cost_reporting",
        ],
    ).set_index("transfer_id")
    decision = {
        "draws": pd.Series(
            draws, index=pd.Index(list(funding._funding)), name="principal"
        ),
        "transfers": pd.Series(
            transfers,
            index=pd.Index(list(funding._transfers)),
            name="sent",
        ),
        "cash_balances": pd.Series(closing.ravel(), index=index, name="cash"),
    }
    if funding._investments:
        decision["investments"] = pd.Series(
            investments,
            index=pd.Index(list(funding._investments)),
            name="quantity",
        )
    evaluation = {
        "objective": float(discounted_cost),
        "feasible": bool(constraints.satisfied.all()),
        "constraints": constraints,
        "decision": decision,
        "metrics": metrics,
        "costs": {
            "discounted_funding_cost": float(discounted_cost),
            "currency": funding._reporting_currency,
            "measure": funding._cost_measure,
        },
        "tables": {
            "cash_ladder": ladder,
            "funding": sources,
            "transfers": transfers_table,
            **facility_tables,
            **scenario_tables,
            **investment_tables,
            **exposure_tables,
        },
    }
    record_reconciliation(evaluation, reconciliation, tolerance=tolerance)
    return evaluation


def evaluate_solution(funding, solution, *, tolerance):
    draws = []
    diagnostics = []
    for i, (key, source) in enumerate(funding._funding.items()):
        raw = scalar(solution[f"funding_{i}"], "solver funding decision")
        amount = raw
        label = identifier_label(key)
        if source.lot_size is not None:
            diagnostics.append(
                (f"integer_lots[{label}]", abs(raw - np.rint(raw)), "lots")
            )
            amount = lot_quantities(np.rint(raw), source.lot_size)
        draws.append(amount)
        if source.minimum > 0 or source.fixed_fee > 0:
            active = scalar(solution[f"active_{i}"], "solver activation")
            diagnostics.append(
                (
                    f"funding_activation[{label}]",
                    abs(active - (amount > 0)),
                    "binary",
                )
            )
    transfers = [
        scalar(solution[f"transfer_{i}"], "solver transfer decision")
        for i in range(len(funding._transfers))
    ]
    investments = []
    for i, (key, source) in enumerate(funding._investments.items()):
        raw = scalar(solution[f"investment_{i}"], "solver investment decision")
        amount = raw
        if source.lot_size is not None:
            diagnostics.append(
                (
                    f"integer_investment_lots[{identifier_label(key)}]",
                    abs(raw - np.rint(raw)),
                    "lots",
                )
            )
            amount = lot_quantities(np.rint(raw), source.lot_size)
        investments.append(amount)
    worst_case_cost = None
    if funding._tree is not None and funding._cost_measure == "worst_case":
        worst_case_cost = scalar(
            solution["worst_case_cost"], "solver worst-case cost"
        )
    risk_auxiliaries = {}
    names = []
    if funding._cost_measure == "expected_shortfall":
        names.append("funding_objective_es")
    if funding._tail_limit is not None:
        names.append("funding_hard_es")
    for name in names:
        eta = Fraction(scalar(solution[f"{name}_threshold"], name))
        excess = [
            Fraction(scalar(solution[f"{name}_excess_{s}"], name))
            for s in range(len(funding._tree._cases))
        ]
        risk_auxiliaries[name] = eta, excess
    evaluation = evaluate(
        funding,
        draws,
        transfers,
        tolerance=tolerance,
        investments=investments,
        worst_case_cost=worst_case_cost,
        risk_auxiliaries=risk_auxiliaries,
    )
    if "constant_constraint_zero" in solution:
        residual = abs(
            scalar(solution["constant_constraint_zero"], "constant row guard")
        )
        diagnostics.append(("constant_constraint_zero", residual, "numeric"))
        evaluation.setdefault("transformations", []).append(
            {
                "type": "constant_constraint_encoding",
                "zero_residual": residual,
            }
        )
    cash = (
        evaluation["decision"]["cash_balances"]
        .to_numpy()
        .reshape(len(funding._periods), len(funding._ids))
    )
    reconciliation = []
    for t in range(len(funding._periods)):
        for a in range(len(funding._ids)):
            raw = scalar(solution[f"cash_{t}_{a}"], "solver cash decision")
            reconciliation.append(
                (
                    f"cash_reconciliation[{t},{a}]",
                    abs(raw - cash[t, a]),
                    funding._currencies.iloc[a],
                )
            )
    for name, residual, unit in diagnostics:
        evaluation["constraints"].loc[name] = [
            residual,
            0,
            0,
            residual,
            residual <= tolerance,
            unit,
        ]
    evaluation["feasible"] = bool(evaluation["constraints"].satisfied.all())
    record_reconciliation(evaluation, reconciliation, tolerance=tolerance)
    for kind, contracts in (
        ("funding", funding._funding),
        ("investment", funding._investments),
    ):
        if any(source.lot_size is not None for source in contracts.values()):
            evaluation.setdefault("transformations", []).append(
                {
                    "type": f"{kind}_lot_reconstruction",
                    "constraints_rechecked": True,
                }
            )
    return evaluation
