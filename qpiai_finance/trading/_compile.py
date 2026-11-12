"""Sparse chronological execution balances with convex cost and risk terms."""

from fractions import Fraction

import numpy as np
from scipy import sparse

from .._arithmetic import product_sum, row_products
from .._solvers._expressions import linear_model, quadratic
from .._validation import lot_capacity
from ..risk import FactorRisk
from .costs import _curve_rows


def linear_backbone(execution):
    e = execution
    opportunities = e._opportunities
    m, t = len(opportunities), len(e._slots)
    active = np.flatnonzero(e._orders != 0)
    active_set = set(active)
    assets = e._ids.get_indexer(opportunities.asset)
    slots = e._slots.get_indexer(opportunities.slot)
    venues = e.venue_ids.get_indexer(opportunities.venue)
    direction = e._direction[assets]
    scales = np.ones(m) if e._lots is None else e._lots[assets]
    side_price = np.where(
        direction >= 0, opportunities.ask_price, opportunities.bid_price
    )
    target = e._target_positions
    maximum = e._capacities(assets, slots)
    names, lower, upper, integers, objective = [], [], [], [], []

    def variable(name, low=0.0, high=np.inf, integer=False, cost=0.0):
        index = len(names)
        names.append(name)
        lower.append(float(low))
        upper.append(float(high))
        integers.append(int(integer))
        objective.append(float(cost))
        return index

    quantity = np.array(
        [
            variable(
                f"execution_{j}",
                high=maximum[j]
                if e._lots is None
                else lot_capacity(maximum[j], scales[j]),
                integer=e._lots is not None,
                cost=(
                    direction[j] * (side_price[j] - e._arrival[assets[j]])
                    + e._fees[j]
                )
                * scales[j],
            )
            for j in range(m)
        ],
        dtype=int,
    )
    remaining = {
        (k, i): variable(
            f"remaining_{k}_{i}",
            high=0.0 if k == t - 1 and e._hard[i] else abs(e._orders[i]),
            cost=e._underfill[i]
            if k == t - 1 and e._underfill is not None and not e._hard[i]
            else 0.0,
        )
        for k in range(t)
        for i in active
    }
    floor = np.maximum(-e._credit, e._cash_minimum)
    cash_origin = Fraction(e._cash_origin)
    cash = np.array([
        variable(
            f"cash_change_{k}",
            low=float(Fraction(floor[k]) - cash_origin),
        )
        for k in range(t)
    ])
    impact = np.array(
        [
            variable(
                f"impact_{j}",
                high=np.inf
                if e._quadratic[j] > 0
                or e._power[j] > 0
                or e._op_ids[j] in e._curves
                else 0.0,
                cost=1.0,
            )
            for j in range(m)
        ],
        dtype=int,
    )
    tickets = {
        j: variable(f"ticket_{j}", high=1.0, integer=True, cost=e._fixed[j])
        for j in range(m)
        if e._fixed[j] > 0 or e._minimum[j] > 0
    }
    piecewise = {
        j: variable(f"piecewise_{j}")
        for j in range(m)
        if e._op_ids[j] in e._curves
    }
    factor = {}
    risk = e._risk
    if e._has_risk and isinstance(risk, FactorRisk):
        factor = {
            (k, f): variable(f"factor_{k}_{f}", low=-np.inf)
            for k in range(t - 1)
            for f in range(len(risk._factors))
        }
    gross = (
        {
            (k, i): variable(
                f"position_abs_change_{k}_{i}",
                low=-abs(e._orders[i]),
                high=abs(e._orders[i]),
            )
            for k in range(t)
            for i in active
        }
        if e._gross_limit is not None
        else {}
    )
    row_index, column_index, coefficients, lows, highs, labels = (
        [],
        [],
        [],
        [],
        [],
        [],
    )
    gross_opening = (
        product_sum((e._arrival, np.abs(e._opening)))
        if e._gross_limit is not None
        else None
    )

    def add(entries, low, high, label, *, constant=None):
        entries = [(column, value) for column, value in entries if value != 0]
        if constant is not None:
            low = Fraction(low) - constant if np.isfinite(low) else low
            high = Fraction(high) - constant if np.isfinite(high) else high
        try:
            reported_low, reported_high = float(low), float(high)
        except OverflowError:
            # Drop an unreportable bound only if the variable box proves it
            # redundant; an impossible row stays explicitly infeasible.
            least = most = Fraction(0)
            for column, value in entries:
                coefficient = Fraction(value)
                start, stop = lower[column], upper[column]
                if coefficient < 0:
                    start, stop = stop, start
                if not np.isfinite(start):
                    least = None
                elif least is not None:
                    least += coefficient * Fraction(start)
                if not np.isfinite(stop):
                    most = None
                elif most is not None:
                    most += coefficient * Fraction(stop)
            least = -np.inf if least is None else least
            most = np.inf if most is None else most
            if low > most or high < least:
                entries, reported_low, reported_high = [], 1.0, np.inf
            else:
                maximum = Fraction(np.finfo(float).max)
                if (low > least and abs(low) > maximum) or (
                    high < most and abs(high) > maximum
                ):
                    raise ValueError("execution limits exceed float64 range")
                reported_low = -np.inf if low <= least else float(low)
                reported_high = np.inf if high >= most else float(high)
        low, high = reported_low, reported_high
        if np.isnan(low) or np.isnan(high) or low == np.inf or high == -np.inf:
            raise ValueError("execution limits exceed float64 range")
        if low == -np.inf and high == np.inf:
            return
        if not entries and low <= 0 <= high:
            return
        row = len(labels)
        for column, value in entries:
            row_index.append(row)
            column_index.append(column)
            coefficients.append(float(value))
        lows.append(float(low))
        highs.append(float(high))
        labels.append(label)

    by_slot = [[] for _ in range(t)]
    by_asset_slot = {}
    by_venue_slot = {}
    for j, (k, i, venue) in enumerate(zip(slots, assets, venues)):
        by_slot[k].append(j)
        by_asset_slot.setdefault((k, i), []).append(j)
        by_venue_slot.setdefault((k, venue), []).append(j)
    for k in range(t):
        for i in active:
            entries = [(remaining[k, i], 1.0)]
            entries.extend(
                (quantity[j], scales[j]) for j in by_asset_slot.get((k, i), [])
            )
            rhs = abs(e._orders[i]) if k == 0 else 0.0
            if k:
                entries.append((remaining[k - 1, i], -1.0))
            add(entries, rhs, rhs, f"order_balance_{k}_{i}")
        entries = [(cash[k], 1.0)]
        if k:
            entries.append((cash[k - 1], -1.0))
        rhs = Fraction(e._flows[k])
        if k == 0:
            rhs += Fraction(e._cash) - cash_origin
        for j in by_slot[k]:
            entries.extend(
                [
                    (
                        quantity[j],
                        (direction[j] * side_price[j] + e._fees[j])
                        * scales[j],
                    ),
                    (impact[j], 1.0),
                ]
            )
            if j in tickets:
                entries.append((tickets[j], e._fixed[j]))
        add(entries, rhs, rhs, f"cash_balance_{k}")
        before = [] if k == 0 else [(cash[k - 1], 1.0)]
        before_constant = (
            Fraction(e._cash) if k == 0 else cash_origin
        ) + Fraction(e._flows[k])
        add(
            before,
            floor[k],
            np.inf,
            f"before_trade_cash_{k}",
            constant=before_constant,
        )
        if e._settlement == "prefunded":
            entries = list(before)
            for j in by_slot[k]:
                debit = (side_price[j] if direction[j] > 0 else 0.0) + e._fees[
                    j
                ]
                entries.extend(
                    [(quantity[j], -debit * scales[j]), (impact[j], -1.0)]
                )
                if j in tickets:
                    entries.append((tickets[j], -e._fixed[j]))
            add(
                entries,
                floor[k],
                np.inf,
                f"prefunded_cash_{k}",
                constant=before_constant,
            )
        for i in range(len(e._ids)):
            entries = (
                [(remaining[k, i], -e._direction[i])]
                if i in active_set
                else []
            )
            add(
                entries,
                -e._borrow[k, i],
                np.inf,
                f"borrow_{k}_{i}",
                constant=target[i],
            )
            if e._position_limits is not None:
                add(
                    entries,
                    e._position_limits[0][k, i],
                    e._position_limits[1][k, i],
                    f"position_{k}_{i}",
                    constant=target[i],
                )
        if e._gross_limit is not None:
            for i in active:
                add(
                    [(gross[k, i], 1), (remaining[k, i], e._direction[i])],
                    target[i] - Fraction(abs(e._opening[i])),
                    np.inf,
                    f"gross_positive_{k}_{i}",
                )
                add(
                    [(gross[k, i], 1), (remaining[k, i], -e._direction[i])],
                    -target[i] - Fraction(abs(e._opening[i])),
                    np.inf,
                    f"gross_negative_{k}_{i}",
                )
            add(
                [(gross[k, i], e._arrival[i]) for i in active],
                -np.inf,
                e._gross_limit[k],
                f"gross_notional_{k}",
                constant=gross_opening,
            )
    for j in range(m):
        if j in tickets:
            minimum = max(e._minimum[j], 0.0 if e._lots is None else scales[j])
            add(
                [(quantity[j], scales[j]), (tickets[j], -minimum)],
                0,
                np.inf,
                f"ticket_minimum_{j}",
            )
            add(
                [(quantity[j], scales[j]), (tickets[j], -maximum[j])],
                -np.inf,
                0,
                f"ticket_maximum_{j}",
            )
        piece = piecewise.get(j)
        if piece is not None:
            curve = e._curves[e._op_ids[j]]
            rows = _curve_rows(curve, scale=scales[j])
            for segment, (width, change, offset) in enumerate(rows or []):
                add(
                    [(piece, width), (quantity[j], -change)],
                    offset,
                    np.inf,
                    f"impact_segment_{j}_{segment}",
                )
            if rows is None:
                weights = [
                    variable(f"impact_weight_{j}_{point}", high=1)
                    for point in range(len(curve))
                ]
                add([(column, 1) for column in weights], 1, 1,
                    f"impact_weights_{j}")
                add(
                    [(quantity[j], scales[j])]
                    + [(column, -value) for column, value in zip(
                        weights, curve.quantity
                    )],
                    0, 0, f"impact_quantity_{j}",
                )
                add(
                    [(piece, 1)]
                    + [(column, -value) for column, value in zip(
                        weights, curve.cost
                    )],
                    0, np.inf, f"impact_quotes_{j}",
                )
        if e._quadratic[j] == 0 and e._power[j] == 0:
            add(
                [(impact[j], 1)] + ([] if piece is None else [(piece, -1)]),
                0,
                np.inf,
                f"impact_cost_{j}",
            )
        if direction[j] < 0:
            add(
                [(impact[j], 1), (quantity[j], -side_price[j] * scales[j])],
                -np.inf,
                0,
                f"nonnegative_sale_price_{j}",
            )
    if e._participation is not None:
        volumes, rates = e._participation
        for (k, i), indices in by_asset_slot.items():
            add(
                [(quantity[j], scales[j]) for j in indices],
                0,
                volumes[k, i] * rates[k, i],
                f"participation_{k}_{i}",
            )
    if e._turnover_limit is not None:
        add(
            [
                (quantity[j], e._arrival[assets[j]] * scales[j])
                for j in range(m)
            ],
            0,
            e._turnover_limit,
            "turnover_notional",
        )
    if e._venue_limits is not None:
        for (k, venue), indices in by_venue_slot.items():
            add(
                [
                    (quantity[j], opportunities.price.iloc[j] * scales[j])
                    for j in indices
                ],
                0,
                e._venue_limits[k, venue],
                f"venue_notional_{k}_{venue}",
            )
    for block, (ids, values, low, high, _) in enumerate(e._exposures):
        rows = sparse.csr_matrix(values)
        constant = list(row_products(rows, target))
        for k in range(t):
            for h in range(len(ids)):
                row = rows.getrow(h)
                entries = [
                    (remaining[k, i], -value * e._direction[i])
                    for i, value in zip(row.indices, row.data)
                    if i in active_set
                ]
                add(
                    entries,
                    low[k, h],
                    high[k, h],
                    f"exposure_{block}_{k}_{h}",
                    constant=constant[h],
                )
    q_rows, q_columns, q_values = [], [], []

    def risk_block(indices, covariance, scale):
        coo = sparse.coo_matrix(covariance)
        q_rows.extend(indices[coo.row])
        q_columns.extend(indices[coo.col])
        q_values.extend(coo.data * scale)

    if e._has_risk:
        if isinstance(risk, FactorRisk):
            order = risk.asset_ids.get_indexer(e._ids)
            loadings = sparse.csr_matrix(risk._b)[order][:, :].T.tocsr()
            specific = risk._d[order]
            for k, duration in enumerate(e._durations()[:-1]):
                for f in range(len(risk._factors)):
                    row = loadings.getrow(f)
                    add(
                        [(factor[k, f], 1)]
                        + [
                            (remaining[k, i], -value * e._direction[i])
                            for i, value in zip(row.indices, row.data)
                            if i in active_set
                        ],
                        0,
                        0,
                        f"factor_balance_{k}_{f}",
                    )
                risk_block(
                    np.array(
                        [factor[k, f] for f in range(len(risk._factors))]
                    ),
                    risk._f,
                    duration * e._risk_aversion,
                )
                risk_block(
                    np.array([remaining[k, i] for i in active]),
                    sparse.diags(specific[active]),
                    duration * e._risk_aversion,
                )
        else:
            covariance = sparse.csr_matrix(risk)[active][:, active]
            signs = sparse.diags(e._direction[active])
            covariance = signs @ covariance @ signs
            for k, duration in enumerate(e._durations()[:-1]):
                risk_block(
                    np.array([remaining[k, i] for i in active]),
                    covariance,
                    duration * e._risk_aversion,
                )
    width = len(names)
    hessian = sparse.coo_matrix(
        (q_values, (q_rows, q_columns)), shape=(width, width)
    ).tocsr()
    hessian.eliminate_zeros()
    data = {
        "name": "trade_execution",
        "problem_type": "MILP" if any(integers) else "LP",
        "format": "matrix",
        "sense": "min",
        "variable_names": names,
        "objective": np.array(objective),
        "objective_offset": 0.0,
        "constraint_matrix": sparse.coo_matrix(
            (coefficients, (row_index, column_index)),
            shape=(len(labels), width),
        ).tocsr(),
        "row_lower": np.array(lows),
        "row_upper": np.array(highs),
        "constraint_names": labels,
        "lower_bounds": np.array(lower),
        "upper_bounds": np.array(upper),
        "integrality": np.array(integers, dtype=int),
    }
    if (
        not np.isfinite(data["constraint_matrix"].data).all()
        or not np.isfinite(data["objective"]).all()
        or not np.isfinite(hessian.data).all()
    ):
        raise ValueError("execution coefficients exceed float64 range")
    return data, hessian


def compile_opt(execution):
    if execution._needs_external:
        raise ValueError(
            "conic or integer quadratic execution requires "
            "a compatible external solver"
        )
    data, hessian = linear_backbone(execution)
    model = linear_model(data)
    if hessian.nnz:
        indices = np.unique(hessian.nonzero()[0])
        by_name = {variable.name: variable for variable in model.variables()}
        selected = [by_name[data["variable_names"][i]] for i in indices]
        model.minimize(
            model.objective + quadratic(selected, hessian[indices][:, indices])
        )
    return model


def compile_cvxpy(execution, *, numerical=False):
    import cvxpy as cp

    from .._solvers._units import binary_scale, scale_matrix
    from .._solvers.cvxpy import matrix_problem
    from ._units import execution_units, order_totals
    from .costs import _cvxpy_power_costs

    data, original_hessian = linear_backbone(execution)
    if numerical:
        data = order_totals(data)
    names = data["variable_names"]
    positions = {name: i for i, name in enumerate(names)}
    assets = execution._ids.get_indexer(execution._opportunities.asset)
    active = np.flatnonzero(
        (execution._quadratic > 0) | (execution._power > 0)
    )
    indices = np.array(
        [positions[f"execution_{j}"] for j in active], dtype=int
    )
    lots = (
        np.ones(len(active))
        if execution._lots is None
        else execution._lots[assets[active]]
    )
    range_limited = False
    for condition in (True, False) if numerical else (False,):
        columns = np.zeros(len(names), dtype=int)
        quantities = np.zeros(len(execution._ids), dtype=int)
        money = 0
        if condition:
            columns, quantities, money = execution_units(execution, data)
        try:
            if condition:
                compiled, rows = scale_matrix(data, columns, money)
            else:
                compiled, rows = data, np.zeros(len(data["row_lower"]), int)
            hessian = original_hessian.tocoo(copy=True)
            hessian.data = binary_scale(
                hessian.data,
                columns[hessian.row] + columns[hessian.col] - money,
            )
            quantity_units = quantities[assets[active]]
            factors = binary_scale(lots, columns[indices] - quantity_units)
            quadratic_cost = binary_scale(
                execution._quadratic[active], 2 * quantity_units - money
            )
            power_cost = binary_scale(
                execution._power[active], 3 * quantity_units // 2 - money
            )
        except FloatingPointError as error:
            if not condition:
                raise ValueError(
                    "execution units exceed float64 range"
                ) from error
            range_limited = True
        else:
            break
    base, normalized, values, bindings = matrix_problem(
        compiled, zero_constants=numerical
    )
    variables = {
        name: np.ldexp(1.0, int(columns[i])) * normalized[name]
        for i, name in enumerate(names)
    }
    variables.update(
        {
            name: value
            for name, value in normalized.items()
            if name not in positions
        }
    )
    constraints = list(base.constraints)
    dual_exponents = []
    for kind, locations in bindings:
        if kind == "guard":
            dual_exponents.append(money)
        else:
            units = columns if kind == "column" else rows
            dual_exponents.append((money - units[locations]).tolist())
    objective = base.objective.expr
    if hessian.nnz:
        objective += cp.quad_form(values, cp.psd_wrap(hessian.tocsr()))
    if len(active):
        cost = _cvxpy_power_costs(
            cp.multiply(factors, values[indices]),
            quadratic_cost,
            power_cost,
            signed=False,
        )
        curves = [
            (i, positions[f"piecewise_{j}"])
            for i, j in enumerate(active)
            if execution._op_ids[j] in execution._curves
        ]
        if curves:
            cost += (
                sparse.coo_matrix(
                    (np.ones(len(curves)), tuple(zip(*curves))),
                    shape=(len(active), len(names)),
                ).tocsr()
                @ values
            )
        constraints.append(
            values[[positions[f"impact_{j}"] for j in active]] >= cost
        )
        dual_exponents.append([0] * len(active))
    problem = cp.Problem(cp.Minimize(objective), constraints)
    if not numerical:
        return problem, variables
    context = {
        "type": "financial_units",
        "base": 2,
        "applied": bool(condition),
        "range_limited": range_limited,
        "objective_exponent": money,
        "maximum_coordinate_exponent": int(
            max(np.max(columns), np.max(rows), money)
        ),
        "variable_exponents": dict(zip(names, columns.tolist())),
        "row_exponents": dict(zip(data["constraint_names"], rows.tolist())),
        "constraint_exponents": dual_exponents,
        "integer_domains_unchanged": True,
        "fixed_zero_coordinates": [
            name for name in names if isinstance(normalized[name], cp.Constant)
        ],
        "order_total_constraints": [
            name
            for name in data["constraint_names"]
            if name.startswith("order_total_")
        ],
    }
    return problem, variables, context
