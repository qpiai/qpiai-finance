"""Compile dated funding obligations and cash balances to an LP or MILP."""

from fractions import Fraction

import numpy as np

from .._arithmetic import float_upper_bound, weighted_mean
from .._validation import lot_capacity
from ..cashflows import _loan_amounts, _loan_cash_terms, _loan_expense


def expense_terms(funding, charges, transfers, *, schedules=None):
    """Separate decision expenses from unrounded contractual fixed costs."""
    expenses = [[] for _ in funding._periods]
    fixed = np.zeros(len(funding._periods), dtype=object)
    for key, source in funding._existing_debt.items():
        a = funding._ids.get_loc(source.account)
        fx = Fraction(funding._fx[funding._currencies.iloc[a]])
        _, _, due = (
            funding._schedule(None, source.repay_at)
            if schedules is None
            else schedules[key]
        )
        _, _, _, interest = _loan_amounts(
            source.principal, source.interest, original=True
        )
        for t in due:
            fixed[t] += (
                fx
                * _loan_expense(
                    interest,
                    repayment_discount=funding._discount[t, a],
                    original=True,
                )
            )
    for key, source in funding._funding.items():
        a = funding._ids.get_loc(source.account)
        start, _, due = (
            funding._schedule(source.draw_at, source.repay_at)
            if schedules is None
            else schedules[key]
        )
        fx = funding._fx[funding._currencies.iloc[a]]
        fees, interest = charges[key]
        expenses[start].append(
            fx
            * _loan_expense(
                0,
                fees,
                draw_discount=funding._discount[start, a],
            )
        )
        for t in due:
            expenses[t].append(
                fx
                * _loan_expense(
                    interest,
                    repayment_discount=funding._discount[t, a],
                )
            )
    for key, source in funding._transfers.items():
        a = funding._ids.get_loc(source.from_account)
        t = funding._periods.get_loc(source.at)
        fx = funding._fx[funding._currencies.iloc[a]]
        expenses[t].append(
            fx * funding._discount[t, a] * source.fee * transfers[key]
        )
    return expenses, fixed


def case_costs(tree, node_costs):
    """Sum expenses once along each actual information history."""
    return [sum(node_costs[t] for t in path) for path in tree._paths]


def compile_model(funding):
    from qpiai_opt.opt_modeller import (
        Binary,
        Continuous,
        Integer,
        Model,
        quicksum,
    )

    funding._check_cost_measure()
    model = Model("funding")
    declarations = []

    def variable(definition):
        declarations.append(definition)
        return definition

    def continuous(name, low, high):
        return variable(Continuous(name, low, high))

    def equation(terms, name):
        model.add_constraint(
            quicksum(coefficient * value for value, coefficient in terms) == 0,
            label=name,
        )

    dates, accounts = funding._periods, funding._ids
    events = [[[] for _ in accounts] for _ in dates]
    debt = [[[] for _ in accounts] for _ in dates]
    fixed_cash = np.zeros((len(dates), len(accounts)), dtype=object)
    existing_debt = np.zeros_like(fixed_cash)
    principals, transfer_decisions = {}, {}
    charges = {}
    investment_quantities = {}
    schedules = {}
    cash = [
        [
            variable(
                Continuous(
                    f"cash_{t}_{a}",
                    float(funding._cash_lower[t, a]),
                    float(funding._cash_upper[t, a]),
                )
            )
            for a in range(len(accounts))
        ]
        for t in range(len(dates))
    ]
    for key, source in funding._existing_debt.items():
        a = accounts.get_loc(source.account)
        schedules[key] = funding._schedule(None, source.repay_at)
        _, live, due = schedules[key]
        _, repayment, _, _ = _loan_amounts(
            source.principal, source.interest, original=True
        )
        for t in live:
            existing_debt[t, a] += Fraction(source.principal)
        for t in due:
            fixed_cash[t, a] -= repayment
    for i, (key, source) in enumerate(funding._funding.items()):
        a = accounts.get_loc(source.account)
        schedules[key] = funding._schedule(source.draw_at, source.repay_at)
        start, live, due = schedules[key]
        if source.lot_size is None:
            draw = variable(Continuous(f"funding_{i}", 0, source.maximum))
            principal, scale, maximum = draw, 1.0, source.maximum
        else:
            maximum_units = lot_capacity(source.maximum, source.lot_size)
            units = variable(Integer(f"funding_{i}", 0, maximum_units))
            draw = source.lot_size * units
            principal, scale = units, source.lot_size
            maximum = Fraction(maximum_units) * Fraction(scale)
        principals[key] = draw
        active = 0
        if source.minimum > 0 or source.fixed_fee > 0:
            active = variable(Binary(f"active_{i}"))
            minimum = max(source.minimum, source.lot_size or 0)
            model.add_constraint(
                draw >= minimum * active, label=f"minimum_draw_{i}"
            )
            model.add_constraint(
                draw <= source.maximum * active, label=f"draw_activation_{i}"
            )
        proceeds, repayment, fees, interest = _loan_cash_terms(
            principal, scale, source.interest, source.fee, maximum=maximum,
            fixed_fee=source.fixed_fee, active=active, name=f"funding_{i}",
            variable=continuous, equation=equation,
        )
        charges[key] = (
            quicksum(rate * value for value, rate in fees),
            quicksum(rate * value for value, rate in interest),
        )
        events[start][a].append(
            quicksum(rate * value for value, rate in proceeds)
        )
        for t in live:
            debt[t][a].append(draw)
        for t in due:
            events[t][a].append(
                -quicksum(rate * value for value, rate in repayment)
            )
    for i, (key, transfer) in enumerate(funding._transfers.items()):
        source = accounts.get_loc(transfer.from_account)
        destination = accounts.get_loc(transfer.to_account)
        t = dates.get_loc(transfer.at)
        amount = variable(Continuous(f"transfer_{i}", 0, transfer.maximum))
        events[t][source].append(-(1 + transfer.fee) * amount)
        events[t][destination].append(transfer.exchange_rate * amount)
        transfer_decisions[key] = amount
    if funding._facilities:
        from ._facilities import capacity_rows

        existing = {
            key: source.principal
            for key, source in funding._existing_debt.items()
        }
        for block, t, terms, upper in capacity_rows(
            funding._facilities,
            {key: schedule[1] for key, schedule in schedules.items()},
            existing,
        ):
            use = quicksum(
                rate * principals[key]
                for key, rate in terms
                if key in principals
            )
            model.add_constraint(
                0 * cash[0][0] + use <= upper,
                label=f"facility_{block}_{t}",
            )
    for i, (key, source) in enumerate(funding._investments.items()):
        a = accounts.get_loc(source.account)
        start = dates.get_loc(source.purchase_at)
        if source.lot_size is None:
            amount = variable(
                Continuous(f"investment_{i}", source.lower, source.upper)
            )
        else:
            amount = source.lot_size * variable(
                Integer(
                    f"investment_{i}",
                    0,
                    lot_capacity(source.upper, source.lot_size),
                )
            )
            if source.lower > 0:
                model.add_constraint(
                    amount >= source.lower, label=f"investment_lower_{i}"
                )
        events[start][a].append(-source.price * amount)
        if funding._exposure_limits:
            investment_quantities[key] = amount
        for t in np.flatnonzero(source.cash_flows):
            events[t][a].append(float(source.cash_flows[t]) * amount)
    for flow in funding._flows.itertuples():
        t, a = (
            dates.get_loc(getattr(flow, funding._axis)),
            accounts.get_loc(flow.account),
        )
        fixed_cash[t, a] += Fraction(flow.amount)
    for t in range(len(dates)):
        for a in range(len(accounts)):
            parent = funding._parents[t]
            constant = fixed_cash[t, a]
            closing = quicksum(events[t][a])
            if parent < 0:
                constant += (
                    1 + Fraction(funding._returns[t, a])
                ) * Fraction(funding._opening[a])
            else:
                closing += (
                    1 + float(funding._returns[t, a])
                ) * cash[parent][a]
            try:
                closing += float(constant)
            except OverflowError as error:
                raise ValueError(
                    "funding cash balances exceed float64 range"
                ) from error
            model.add_constraint(
                cash[t][a] == closing, label=f"cash_balance_{t}_{a}"
            )
            if np.isfinite(funding._debt_upper[t, a]):
                model.add_constraint(
                    0 * cash[t][a] + quicksum(debt[t][a])
                    <= float_upper_bound(
                        Fraction(funding._debt_upper[t, a])
                        - existing_debt[t, a]
                    ),
                    label=f"debt_limit_{t}_{a}",
                )
    if funding._exposure_limits:
        from ._balance_sheet import bounds, terms

        positions = {
            "investments": investment_quantities,
            "funding": principals,
            "cash": {
                key: [row[a] for row in cash] for a, key in enumerate(accounts)
            },
        }
        zero = 0 * cash[0][0]
        for i, block in enumerate(funding._exposure_limits.values()):
            for k in range(len(dates)):
                activity = zero + quicksum(terms(block, k, positions))
                low, high = bounds(block, k)
                if np.isfinite(low):
                    model.add_constraint(
                        activity >= low, label=f"exposure_{i}_{k}_lower"
                    )
                if np.isfinite(high):
                    model.add_constraint(
                        activity <= high, label=f"exposure_{i}_{k}_upper"
                    )
    expenses, fixed_expenses = expense_terms(
        funding,
        charges,
        transfer_decisions,
        schedules=schedules,
    )
    node_costs = [quicksum(terms) for terms in expenses]
    paths = None
    fixed_paths = (
        None if funding._tree is None or not any(fixed_expenses)
        else case_costs(funding._tree, fixed_expenses)
    )
    if funding._tree is not None and (
        funding._cost_measure != "expected" or funding._tail_limit is not None
    ):
        paths = case_costs(funding._tree, node_costs)
        if fixed_paths is not None:
            paths = [
                cost + float(fixed) for cost, fixed in zip(paths, fixed_paths)
            ]

    def tail(level, name):
        from ..risk import expected_shortfall_epigraph

        bound, constraints = expected_shortfall_epigraph(
            paths,
            probabilities=funding._tree._probabilities,
            confidence=level,
            name=name,
        )
        for i, constraint in enumerate(constraints):
            model.add_constraint(constraint, label=f"{name}_loss_{i}")
        return bound

    if funding._tree is None:
        objective = quicksum(node_costs) + float(sum(fixed_expenses))
    elif funding._cost_measure == "expected":
        objective = quicksum(
            float(p) * cost
            for p, cost in zip(funding._tree._node_probabilities, node_costs)
            if p > 0
        )
        if fixed_paths is not None:
            objective += float(weighted_mean(
                fixed_paths, funding._tree._probabilities
            ))
    elif funding._cost_measure == "expected_shortfall":
        objective = tail(funding._confidence, "funding_objective_es")
    else:
        objective = variable(Continuous("worst_case_cost", -np.inf, np.inf))
        for case, cost in enumerate(paths):
            model.add_constraint(
                objective >= cost,
                label=f"worst_case_cost_{case}",
            )
    if funding._tail_limit is not None:
        maximum, confidence = funding._tail_limit
        model.add_constraint(
            tail(confidence, "funding_hard_es") <= maximum,
            label="funding_expected_shortfall_limit",
        )
    model.minimize(objective)
    model.add_variables(declarations)
    return model
