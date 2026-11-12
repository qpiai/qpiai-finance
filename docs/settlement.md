# Payment settlement

`SettlementModel` schedules whole payments over ordered processing positions, subject to payment windows, account liquidity, and explicit dependencies. It minimizes supplied delay, queue, prefunding, and peak-credit costs. Import it from `qpiai_finance.settlement`.

The output is a proposed settlement plan. Account currencies remain separate; reporting currency applies to economic cost coefficients. Payment release, finality, FX conversion, and legal permission to net are outside the model.

## Constructor and input tables

```python
SettlementModel(
    accounts, payments, *, as_of, slots, reporting_currency,
    settlement_method="rtgs", slot_ids=None,
)
```

`accounts` and `payments` are pandas DataFrames with unique string/integer row identifiers. Unknown or duplicate columns are rejected. Accounts must be nonempty; payments may be empty with the required columns retained.

| Argument | Type, allowed values, and meaning |
| --- | --- |
| `as_of` | Required timezone-aware timestamp. Naive timestamps are rejected. |
| `slots` | Required nonempty sequence of timezone-aware timestamps, nondecreasing and beginning at `as_of`. Duplicate timestamps represent distinct ordered processing positions. |
| `reporting_currency` | Required uppercase three-letter currency code for all cost coefficients and the objective. |
| `settlement_method` | `"rtgs"` by default: one whole payment per position. `"atomic"` additionally permits explicitly registered batches; individual payments remain available. No batch is inferred. |
| `slot_ids` | Optional unique string/integer identifier sequence with one entry per position. Default positional integers `0, ..., len(slots)-1`. Position order is input order, independent of identifier sorting. |

### Accounts

| Column | Type, default, and meaning |
| --- | --- |
| `cash` | Required finite signed opening balance in the account's native currency. |
| `currency` | Required uppercase three-letter account currency. |
| `credit_limit` | Optional finite nonnegative approved opening overdraft capacity; default zero. Opening `cash` must be at least `-credit_limit`. This capacity initially applies at every slot. |

### Payments

| Column | Type, default, and meaning |
| --- | --- |
| `sender`, `receiver` | Required supplied account identifiers, distinct and in the same currency. |
| `amount` | Required strictly positive finite native-currency amount. Payments cannot be split. |
| `release`, `deadline` | Required timezone-aware timestamps with `release <= deadline`. Settlement must occur at a supplied slot within this inclusive window. Window endpoints need not be slots. |
| `currency` | Optional uppercase three-letter code; inferred from the accounts when omitted. If supplied, must match both accounts. |
| `required` | Optional boolean, default `True`. Required payments must settle once; optional payments may remain queued. |
| `eligible` | Optional boolean, default `True`. False prevents settlement in any unit, including a batch. A required ineligible payment makes the formulation infeasible. |
| `delay_cost` | Optional finite nonnegative reporting-currency cost per second after release; default zero. |
| `unsettled_cost` | Optional finite nonnegative reporting-currency penalty for a payment still unsettled at the horizon and already released; default zero. |

Delay and queue charges affect the objective; they are not cash-debited payment fees. Each settled payment incurs delay through its settlement time. An unsettled payment incurs delay through the last slot, floored at zero, plus its queue penalty if released by that time. A future unreleased payment incurs neither charge. A required payment whose window contains no eligible position cannot be satisfied.

## Properties

All properties return detached pandas objects.

| Property | Return type and contents |
| --- | --- |
| `account_ids` | `pandas.Index` in account input order. |
| `payment_ids` | `pandas.Index` in payment input order. |
| `slot_ids` | `pandas.Index` in processing order. |
| `slot_times` | Timezone-aware timestamp Series named `time`, indexed by slot ID. |
| `execution_units` | DataFrame indexed by integer `position`, with `kind`, `id`, `payments`. All single payments come first, followed by registered batches. `payments` contains tuples of payment IDs. Kinds are `"payment"` and `"atomic_batch"`. |

## Liquidity and funding controls

```python
model.set_external_flows(flows)
model.set_credit_limits(limits)
model.allow_prefunding(maximum, *, cost_per_unit)
model.set_credit_costs(cost_per_unit)
model.limit_final_balances(lower=0.0)
```

These methods mutate the model and return `self`. Numeric inputs must be finite. Complete labelled inputs are aligned by identifier; missing, extra, or duplicate labels are rejected. [Data conventions](data.md) describes supported array, Series, mapping, DataFrame, and sparse forms.

| Method input | Type, default, and meaning |
| --- | --- |
| `flows` | Required signed slot-by-account matrix of incremental native-currency external receipts/outflows. Applied before settlement at each position. Default model flows are zero; values are not cumulative funding balances. |
| `limits` | Required nonnegative slot-by-account matrix of approved native-currency overdraft capacities. Replaces capacities at processing positions; the account table still defines the opening limit. |
| Prefunding `maximum` | Required nonnegative scalar or complete account vector, Series, or mapping of native-currency outside funds available before the first slot. Default capacity is zero. |
| Prefunding `cost_per_unit` | Required nonnegative scalar or complete account vector of reporting-currency cost per native unit for the horizon. |
| Credit `cost_per_unit` | Required nonnegative scalar or complete account vector of reporting-currency cost per native unit of actual peak overdraft. Default zero allows free approved credit and provides no incentive to minimize its use. |
| Final `lower` | Finite signed scalar or complete account vector of native-currency final balance floors; default argument zero requires repayment of overdrafts. No final floor is imposed until this method is called. |

Opening balances are checked against opening credit. Prefunding is then added. Each slot applies external flows, checks the resulting balance, executes its unit, and checks the post-settlement balance. Incoming settlement cannot cure a pre-slot liquidity breach. Peak overdraft includes opening, prefunded, pre-slot, and post-settlement checkpoints. Prefunding is an explicitly available outside contribution; no funding contract, repayment, or reusable funding source is inferred.

## Batches and precedence

```python
model.add_atomic_batch(batch_id, payment_ids)
model.add_precedence(before, after, *, allow_same_batch=False)
model.require_payments(payment_ids)
```

Each method returns `self`.

`add_atomic_batch` requires `settlement_method="atomic"`. `batch_id` is a string/integer unique among batch IDs. `payment_ids` is a sequence of at least two distinct supplied payment IDs; a single string is rejected. An identical membership set cannot be registered twice. Membership is stored in payment input order. All members settle in one position within their common window, provided all are eligible. The account limits apply to the net movement of that explicitly authorised unit. Batches may overlap, but no payment can execute more than once. Authorization applies only to the exact supplied groups.

`add_precedence` takes two distinct supplied payment IDs. By default the predecessor must complete at an earlier position than the successor. Boolean `allow_same_batch=True` permits completion in the same authorised batch. An unsettled predecessor blocks its successor. Cyclic or contradictory dependencies are retained as constraints and may make required payments infeasible.

`require_payments` sets `required=True` for every ID in its supplied nonempty distinct-ID sequence; it does not clear other requirements. It rejects a single string, empty sequence, or unknown identifiers.

Positions are ordered even when timestamps are equal. Separate positions never net together. One position can contain at most one single payment or one authorised batch.

## Export and execution

```python
model.to_matrix()
model.to_model(*, return_variables=False)
model.to_cvxpy()
```

The formulation is MILP when any payment/batch has an eligible position, otherwise LP. The default solve route is Opt. [Solving](solving.md) defines authentication, execution modes, solver controls, and result acceptance. [Custom models](custom-models.md) covers further Opt compilation and recovery.

`to_matrix()` returns a sparse Opt matrix-data dictionary: `name="settlement"`, `format="matrix"`, `sense="min"`, `problem_type`, `variable_names`, `objective`, `objective_offset=0.0`, CSR `constraint_matrix`, `row_lower`, `row_upper`, `constraint_names`, `lower_bounds`, `upper_bounds`, and `integrality`. Coefficient vectors are NumPy arrays. Infinite row/bound endpoints represent absent limits. Internal variables follow these positional conventions:

| Name | Domain and interpretation |
| --- | --- |
| `execution_u_k` | Binary selection of execution-unit position `u` at slot position `k`; only eligible pairs exist. |
| `prefunding_a` | Native-currency outside funding for account position `a`. |
| `balance_k_a` | Native-currency post-slot account cash. |
| `peak_credit_a` | Nonnegative native-currency peak-overdraft auxiliary, bounded below by opening use and all later observed use. |
| `unsettled_p` | Continuous `[0,1]` auxiliary equal to one minus execution count for payment position `p`; fixed zero for required payments. |
| `completion_p_k` | Cumulative completion auxiliary for payments participating in precedence constraints. |

`to_model()` returns a detached algebraic Opt model. Boolean `return_variables=True` returns `(model, expressions)`. `to_cvxpy()` returns `(cvxpy.Problem, expressions)`. The expression dictionary contains pandas Series: `release_indicators` indexed by `(kind, unit, slot)` for eligible pairs, `cash_balances` indexed by `(slot, account)`, account-indexed `prefunding` and `peak_credit`, and payment-indexed `unsettled`. The financial expression keys retain source IDs and native amounts. Modifying an export does not mutate the financial model.

## Evaluate a proposed schedule

```python
model.evaluate(schedule, *, prefunding=0.0, tolerance=1e-7)
```

`schedule` is a complete payment-indexed mapping or Series, or a one-dimensional sequence in payment input order. Each value is a supplied slot ID or an unsettled marker: `None`, `pandas.NA`, `pandas.NaT`, or floating NaN. Other floating-point IDs are rejected. Use object or nullable integer dtype for a Series mixing integer slot IDs and unsettled payments.

`prefunding` is a finite scalar or complete account vector, Series, or mapping in native currency; default zero. Values outside authorised limits produce constraint violations. `tolerance` is a finite nonnegative absolute scalar, default `1e-7`; boolean, payment-count, and position-capacity checks require exact satisfaction.

Evaluation returns a dictionary with `objective`, `feasible`, `constraints`, `decision`, `metrics`, `tables`, and `costs`. It replays balances and original economic costs without authentication or solving. Payments assigned to a shared position form an atomic event only when their exact set is registered. Otherwise they remain separate events, with position-capacity and intermediate balance violations reported. Original arithmetic is checked before float64 reporting; a displayed rounded balance need not expose every retained residual.

## Results and reporting

The objective is total cost in reporting currency. `result.settlement_schedule` is the payment-indexed Series named `slot`; `prefunding`, `peak_credit`, and `cash_balances` retain the indices described above. In the evaluation `decision` dictionary, the schedule key is `schedule`; the other keys match their result property names.

| Location | Fields and meaning |
| --- | --- |
| `metrics` | Reporting-currency `delay_cost`, `unsettled_cost`, `prefunding_cost`, `credit_cost`, `total_cost`; integer counts `settled_payments` and `unsettled_payments`. Settled count includes payments executed exactly once. |
| `costs` | `delay_cost`, `unsettled_cost`, `prefunding_cost`, `credit_cost`, `currency`. |
| `settlement_schedule` table | Payment-indexed `sender`, `receiver`, `amount`, `currency`, `release`, `deadline`, `required`, `execution_count`, `slot`, `settled_at`, `status`, `delay_seconds`, `delay_cost`, `unsettled_cost`, `cost_currency`. |
| `payment_queue` table | The same columns, restricted to payments with zero executions. |
| `settlement_accounts` table | Account input columns plus native-currency `prefunding`, `final_cash`, and `peak_credit_used`. |
| `settlement_ledger` table | Indexed by `(checkpoint, account)`: `phase`, `slot`, `time`, `movement`, `balance`, `credit_limit`, `credit_used`, `currency`. Phases are `opening`, `prefunding`, `pre_slot`, and `post_settlement`. |
| `settlement_events` table | One row per executed unit: `slot`, `time`, `kind`, `id`, and tuple `payments`. |

Payment `status` is `settled` for one execution or `duplicate_execution` for repeated execution. Unsettled statuses are chosen in order: `ineligible`, `not_released`, `cutoff_expired` when deadline is at or before the horizon, otherwise `queued`. Status alone does not establish feasibility; inspect all constraints.

Numeric amounts, balances, costs, and delays are floats; execution counts are integers and `required` is boolean. The decision's `schedule` Series has object dtype and retains exact slot identifiers with `None` for unsettled payments. Use it for replay; report-table slot columns can acquire a floating dtype when integer IDs are mixed with missing entries. `settled_at` is an aware timestamp or `NaT`.

Ledger checkpoints are numbered consecutively: opening, prefunding, each pre-slot state, then each executed unit's post-settlement state. Idle slots have a pre-slot checkpoint and still appear in `decision["cash_balances"]`. Opening/prefunding ledger rows have no slot identifier. `settlement_events` uses a positional row index and includes only executed units. The numeric Series names are `prefunding`, `peak_credit_used`, and `cash` for prefunding, peak credit, and closing balances, respectively.

Solver recovery checks binary reconstruction and reconciles cash balances, understated peak credit, queue indicators, and precedence completion auxiliaries with the replay. [Results](results.md) explains these checks and retained solver evidence. [Plotting](plotting.md) documents queue and liquidity figures.

Invalid tables, timestamps, identifiers, dimensions, flags, or numerical domains raise `TypeError` or `ValueError`. Unrepresentable coefficient or reporting calculations raise `ValueError`. Contradictory valid requirements produce an infeasible optimization result; evaluation reports violated financial rules without repairing the proposal.
