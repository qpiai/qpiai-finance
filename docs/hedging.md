# Hedging

`HedgeModel` chooses signed hedge trades from supplied sensitivities or repriced profit-and-loss scenarios. Instruments retain their own quantity units, while each risk row declares its physical unit. Import the class from `qpiai_finance.hedging`.

A sensitivity matrix describes a local risk approximation. Scenario inputs describe supplied changes in value over a horizon. The model does not price instruments, infer sensitivities, or convert a terminal payoff into P&L. Choose the representation appropriate to the risk question and retain hard exposure limits when changing objectives.

## Constructor

```python
HedgeModel(
    current_exposures=None, sensitivities=None, *, risk_units=None,
    currency, as_of, instrument_ids=None, risk_ids=None,
    current_positions=0.0, current_pnl=None, pnl_scenarios=None,
    cost_factors=None,
)
```

Supply both sensitivity arguments, P&L scenarios, or both input families. With sensitivities the initial objective matches zero risk exposure exactly at minimum transaction cost. Without sensitivities it minimizes worst-case scenario loss. Supplying additional scenario data does not itself change a sensitivity model's objective.

| Argument | Type, default, and meaning |
| --- | --- |
| `current_exposures` | Optional finite signed risk vector, Series, or mapping. Required with `sensitivities`; already includes existing hedge positions. No scalar broadcasting. |
| `sensitivities` | Optional finite risk-by-instrument matrix: labelled DataFrame, supported column mapping, dense array, or sparse matrix. Entry `(r,i)` is exposure change in risk row `r` per signed traded unit of instrument `i`. Required with `current_exposures`. |
| `risk_units` | Required with sensitivities: nonblank string broadcast to all risk rows, or complete sequence, Series, or mapping of nonblank labels, one per row. Rejected without sensitivities. |
| `currency` | Required uppercase three-letter code for costs, capital, prices, and scenario P&L. |
| `as_of` | Required calendar date. |
| `instrument_ids` | Optional unique nonblank string/integer IDs. Inferred from sensitivity DataFrame columns, otherwise positional integers; in scenario-only mode defaults to scenario asset IDs. Must match scenario IDs when scenarios are supplied. |
| `risk_ids` | Optional unique string/integer risk IDs. Defaults to sensitivity DataFrame rows, otherwise the index inferred from `current_exposures`. Rejected without sensitivities. |
| `current_positions` | Finite signed scalar or complete instrument vector, Series, or mapping; default zero. Used for post-trade positions and capital. Existing hedges must already be included in `current_exposures` and `current_pnl`; they are not added again to those baselines. |
| `current_pnl` | Optional finite signed scalar or complete scenario vector, Series, or mapping in currency. Required with `pnl_scenarios`; rejected otherwise. Existing-book P&L, including existing hedges. |
| `pnl_scenarios` | Optional exact `Scenarios` instance with `unit="pnl_per_unit"`. Columns are instruments; values are signed P&L changes per traded unit, over the declared scenario horizon. |
| `cost_factors` | Optional strictly positive finite scalar or complete scenario vector, Series, or mapping. Requires scenarios. Default `None` becomes one: no carrying of upfront costs to the scenario horizon. |

Labelled inputs must cover exactly the relevant identifier set and are aligned by labels. Other vectors/matrices follow model order. [Data conventions](data.md) gives supported forms and validation rules.

The detached properties are `instrument_ids: pandas.Index`, `risk_ids: pandas.Index`, `pnl_scenarios: Scenarios | None`, `current_pnl: pandas.Series | None` named `current_pnl`, and `currency: str`. Scenario-only models have an empty risk index.

## Sensitivity objectives and limits

For signed trade quantities `q`, post-hedge exposure is

\[
e=e_0+Sq,
\]

where `e0` includes the existing hedge book. These methods require sensitivity inputs and return `self`:

```python
model.match_exposures(target=0.0)
model.minimize_mismatch(weights, *, target=0.0, cost_weight=1.0)
model.limit_exposures(*, lower, upper)
```

`target` is a finite signed scalar or complete risk vector, Series, or mapping, default zero, in each risk row's declared units. `match_exposures` imposes `e == target` and minimizes transaction costs.

`minimize_mismatch` instead minimizes

\[
(e-t)^\mathsf{T}W(e-t)+\lambda C(q).
\]

`weights` is a required finite symmetric positive-semidefinite risk-by-risk matrix with matching labels when labelled. Entry `(i,j)` has units currency divided by `risk_unit_i * risk_unit_j`; scale mixed risk units intentionally. No identity matrix is inferred. `cost_weight` is finite nonnegative dimensionless `lambda`, default one. Exact matching is replaced by this soft penalty. The zero matrix leaves a linear objective.

`limit_exposures` replaces hard signed risk bounds. Both `lower` and `upper` are required finite scalars or complete risk vectors, with `lower <= upper`. Equal bounds impose a mandatory target under any objective. Initially both sides are unbounded. Changing objectives preserves these bounds.

## Quantities, cash, and capital

```python
model.limit_trades(*, lower=None, upper=None)
model.limit_positions(*, lower=None, upper=None)
model.set_transaction_costs(*, buy=0.0, sell=0.0)
model.set_cash_account(*, cash, prices, bid_prices=None, ask_prices=None)
model.limit_capital(capital_per_unit, *, maximum)
model.trade_in_lots(lot_sizes)
```

Each setter returns `self` and replaces its previous setting.

| Parameter | Type, default, and meaning |
| --- | --- |
| Trade `lower`, `upper` | Optional finite signed scalar or complete instrument vector, Series, or mapping bounding changes `q`. `None` resets that side to unbounded. Require lower no greater than upper. |
| Position `lower`, `upper` | Same input forms, bounding `current_positions + q`. `None` resets that side to unbounded. Initial trade and position bounds are unbounded. |
| `buy`, `sell` | Finite nonnegative scalar or complete instrument vector of fees in currency per unit bought/sold; both default zero. Excludes execution spread. |
| `cash` | Required finite nonnegative scalar of available upfront cash in currency. Configuring the account requires nonnegative post-trade cash; no borrowing is inferred. |
| `prices` | Required finite signed scalar or complete instrument vector of upfront valuation cash amounts per unit. These are not inferred face values or margins. |
| `bid_prices`, `ask_prices` | Optional finite signed scalars or complete instrument vectors. Default to `prices`; require `bid <= prices <= ask`. Negative and zero prices are permitted. |
| `capital_per_unit` | Required finite nonnegative scalar or complete instrument vector in currency per absolute unit of final position. |
| Capital `maximum` | Required finite nonnegative currency scalar; bounds `capital_per_unit @ abs(current_positions + q)`. |
| `lot_sizes` | Required finite strictly positive scalar or complete instrument vector of quantity steps. Signed trades must be integer multiples; final positions need not be lot multiples when opening positions are not. |

For `q >= 0`, fees are `buy*q` and spread cost is `(ask-prices)*q`; for `q < 0`, fees are `sell*abs(q)` and spread is `(bid-prices)*q`. Total transaction cost `C(q)` includes both. Cash after trading is opening cash minus executed quote times signed quantity minus fees. The model charges spread once. Without a configured account it uses zero prices/spreads and does not constrain upfront cash.

## Scenario P&L and tail risk

```python
model.set_pnl_scenarios(scenarios, *, current_pnl, cost_factors=1.0)
model.limit_scenario_loss(maximum)
model.limit_expected_shortfall(maximum, *, confidence=0.95)
model.minimize_expected_shortfall(*, confidence=0.95)
model.minimize_worst_case_loss()
```

All return `self`. The first method takes the same `Scenarios`, current-book P&L, and cost-factor contracts as the constructor. Values describe mark-to-horizon P&L changes including supplied distributions and financing, excluding upfront transaction costs. For case `s`, net loss is

\[
L_s=-\bigl(P_s+S_s q-f_s C(q)\bigr).
\]

Upfront principal remains separate cash accounting and is not subtracted again from P&L. Strictly positive `f_s` carries transaction costs to the scenario horizon; one explicitly means no carrying. Scenarios are copied and aligned. Replacing them preserves configured per-case limits by ID and rejects a changed case set while those limits exist. It does not change the objective.

`limit_scenario_loss(maximum)` requires configured scenarios. `maximum` is a finite signed scalar or complete case vector, Series, or mapping in currency; a negative cap requires a minimum gain. Every case is constrained, including cases with probability zero. Probabilities are unnecessary for these stress limits and for worst-case minimization.

Both ES methods require explicit scenario probabilities and `confidence` strictly in `(0,1)`, default `0.95`. ES uses the finite weighted loss distribution with fractional mass at the tail boundary. `limit_expected_shortfall` takes a finite signed currency `maximum`, replaces the previous ES cap, and retains its own confidence. It does not impose an individual case cap.

The two minimization methods replace exact sensitivity matching or the mismatch objective. Hard exposure, trade, position, cash, capital, and configured scenario limits remain. Expected-shortfall objective confidence is independent of a hard ES cap's confidence. Replacing scenarios with unweighted stress cases is rejected while ES is active. No equal probabilities are inferred.

## Exports, solving, and evaluation

```python
model.to_model(*, return_variables=False)
model.to_cvxpy()
model.evaluate(hedges, *, tolerance=1e-7)
```

The problem is LP or MILP for exact matching and scenario objectives, and QP or MIQP for a nonzero mismatch matrix. Lots introduce integer variables. Integer quadratic models require `solver="scip"` and cannot be exported to Opt with `to_model`; other classes use Opt by default. [Solving](solving.md) documents the full execution and authentication contract.

`to_model()` returns a detached Opt model; boolean `return_variables=True` returns `(model, expressions)`. `to_cvxpy()` returns `(cvxpy.Problem, expressions)`. Both expression mappings contain instrument-indexed Series `hedges` named `hedge_quantity` and `positions` named `position`. Values are signed physical quantities, including when the underlying variables count lots. Export mutations do not change the source specification. See [custom models](custom-models.md) for additional compilation and recovery controls.

`evaluate` takes a complete finite signed instrument vector, Series, or mapping of trades. It does not broadcast a scalar. `tolerance` is a finite nonnegative absolute scalar, default `1e-7`. The returned dictionary contains `objective`, `feasible`, `constraints`, `decision`, `metrics`, `tables`, and `costs`. Evaluation checks the original economics and configured rules without solving, authenticating, or repairing the proposal. Fractional lots and trades outside bounds are retained as violations.

## Result fields

`result.hedges` and `result.positions` are instrument-indexed Series. With sensitivities, `result.risk_exposures` is a risk-indexed Series named `exposure`; otherwise that decision and table are absent. Objective units are currency.

| Location | Fields and meaning |
| --- | --- |
| `metrics` | `transaction_cost`, `spread_cost`, `fees`; optional `cash_after`, `capital_used`, `mismatch_cost`. Scenario inputs add `worst_case_loss`, `expected_pnl` (`None` without probabilities), and `scenario_horizon`. ES objective adds `expected_shortfall`, `expected_shortfall_confidence`; hard ES adds `constrained_expected_shortfall`, `constrained_expected_shortfall_confidence`. |
| `costs` | `currency`, `spread`, `fees`. |
| `hedges` table | Instrument-indexed `before`, signed `trade`, `after`, currency `spread`, `fees`. |
| `risk_exposures` table | Risk-indexed `before`, signed `change`, `after`, `target`, signed target `residual`, `unit`. Available only with sensitivities. A retained target is a hard equality only under exact matching. |
| `hedge_scenarios` table | Case-indexed `before_pnl`, `hedge_pnl`, `trading_cost_at_horizon`, `net_pnl`, `loss`; optional `probability`, `maximum_loss`. DataFrame attributes record `currency` and `horizon`. |

Original sums/products are retained through risk targets, bounds, carried costs, and tail calculations before binary64 reporting. Small residuals may remain meaningful even when displayed totals round to the same value. Solver recovery also checks lot reconstruction and any residual auxiliaries against financial replay. [Results](results.md) explains feasibility and solver evidence; [plotting](plotting.md) covers hedge, risk, and scenario figures.

Invalid input modes, dimensions, labels, units, rate domains, or unsupported exports raise `TypeError` or `ValueError`; unrepresentable numerical calculations raise `ValueError`. Valid but incompatible hard limits can yield an infeasible result. Prices, repricing, risk scaling, capital coefficients, and permitted instrument trades remain supplied financial inputs.
