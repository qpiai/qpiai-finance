# Plot financial results

Import plotting functions from `qpiai_finance.plot`. Each returns a Matplotlib `Axes` and draws the applicable financial result data. No plot performs a new solve, recalculates a different risk model, submits work, or displays a window automatically.

## Axes and result requirements

Every function accepts keyword-only `ax=None`. Supply an existing Matplotlib Axes to compose a figure; omit it to create an Axes with a constrained-layout figure. Save or display through Matplotlib:

```python
from qpiai_finance import plot

ax = plot.weights(result)
ax.figure.savefig("portfolio-weights.png", dpi=160)
```

Here `result` is a financially feasible portfolio result. Other model plots require their corresponding result tables. These functions accept result objects, not raw arrays or arbitrary DataFrames.

Except the two quantum diagnostic functions and the frontier function, plots require a `FinanceResult` with `feasible=True`. They do not rerun verification of a manually constructed or restored record; use trusted result data and [replay](results.md) when fresh checks are needed. Failed result, domain-table, or selector checks raise `ValueError`; `efficient_frontier` raises `TypeError` for a non-frontier result. The supplied record must contain the full domain schemas defined in its model reference.

Identifiers such as `asset`, `account`, `facility`, `risk_id`, `obligation`, and `case` are actual string/integer identifiers from the model, not positional indices. Selectors must exist in the relevant result table. Single-result plot titles identify result status; the frontier title identifies its horizon. Axes use the relevant currency, quantity, horizon, or risk units where supplied.

## Portfolio allocation and risk

| Signature | Required data and plotted meaning |
| --- | --- |
| `weights(result, *, ax=None)` | Source portfolio weight Series; draws weights without renormalization or visual rounding. The denominator is the declared investment basis. |
| `holdings(result, *, ax=None)` | Portfolio `trades` table with `before` and `after` quantities; compares opening and post-trade shares. |
| `trades(result, *, ax=None)` | Single-period signed share trades; positive means purchase. Multi-period investment and execution results must use their dedicated plots below. |
| `risk_contributions(result, *, kind="variance", by="asset", ax=None)` | Existing asset risk contributions, or factor/specific contributions when `by="factor"`. `kind` is `"variance"` or `"volatility"`; `by` is `"asset"` or `"factor"`. Negative contributions stay signed. |
| `risk_budgets(result, *, ax=None)` | `risk_budgets` table; compares requested budgets and realized fractions of portfolio variance. |
| `loss_distribution(result, *, ax=None)` | Portfolio `scenarios` table with `loss` and `probability`; probability-weighted loss histogram. Adds an ES line when `expected_shortfall` and `confidence` metrics are present. |

Factor contribution plotting requires a result constructed with `FactorRisk`. Undefined/nonfinite risk contributions are rejected, including volatility contributions at zero portfolio volatility. Loss-distribution plots use return-fraction loss and the original horizon; use domain-specific loss plots for monetary hedge or insurance scenarios.

### Efficient frontier

```python
efficient_frontier(result, *, ax=None)
```

`result` must be a `FrontierResult`. The plot selects financially feasible rows, sorts them by realized volatility, and draws realized expected return versus volatility. The legend reports feasible versus requested target counts and how many feasible points have proven optimality. An all-infeasible frontier raises `ValueError`. The title records the horizon; filtering for plotting does not remove unsuccessful records from the frontier itself.

## Acquisition-lot analysis

```python
tax_lot_sales(result, *, asset, ax=None)
tax_liability(result, *, asset=None, ax=None)
```

Both require a nonempty `tax_lots` result table. `tax_lot_sales` requires one asset and displays sold and remaining shares by acquisition lot. `asset=None` is rejected for this quantity plot.

`tax_liability` displays recognized tax by lot, retaining signed loss credits and account-currency units. Omit `asset` to include all lots or supply an asset to filter. The title includes the supplied tax as-of date and result status. See [portfolio tax-lot accounting](portfolio.md#tax-lot-decisions).

## Multi-period investments

| Signature | Meaning |
| --- | --- |
| `investment_wealth(result, *, case, ax=None)` | Marked wealth and closing cash along the chosen scenario case; uses recorded stage times and currency. |
| `investment_trades(result, *, case, asset, ax=None)` | Signed quantities for one asset along that case's information-node path. |
| `investment_funding(result, *, case, ax=None)` | Principal drawn, principal repaid, outstanding term debt, and paid interest/fees along the case. |

`case` must be a scenario identifier in `investment_information`; `asset` must be a column of the investment trade decision. The funding plot requires funding-ledger columns in `investment_accounts`. These plots select an actual case path rather than connecting mutually exclusive branches. See [investment planning](trading.md).

## Treasury and liabilities

| Signature | Meaning |
| --- | --- |
| `cash_ladder(result, *, account, case=None, ax=None)` | Closing cash and buffer in the selected funding account's native currency. |
| `funding_schedule(result, *, account, case=None, ax=None)` | Principal draws and repayments in that account currency. |
| `facility_utilization(result, *, facility, ax=None)` | Modeled and reserved principal use versus capacity for one shared facility. Uses its capacity currency. |
| `liability_coverage(result, *, ax=None)` | Dated purchased-asset receipts, liability payments, and retained cash in the liability-matching currency. |

Cash/funding plots require the `cash_ladder` table. For adaptive funding, supply `case` to select its node path; omitting it raises. A deterministic dated ladder rejects a non-`None` case. Facility plots use `funding_facilities`, with dates or separate information-node bars; they do not join branches into a chronological scenario path. Liability matching uses its own `liability_coverage` table. See [funding](funding.md) and [liability matching](liability-matching.md).

## Hedges and credit

| Signature | Meaning |
| --- | --- |
| `hedge_exposure(result, *, risk_id, ax=None)` | Before, after, and target for one signed risk exposure, using its supplied physical unit. |
| `hedge_losses(result, *, ax=None)` | Before-hedge book loss versus after-hedge loss including costs for supplied P&L scenarios. |
| `allocations(result, *, ax=None)` | Existing versus proposed facility amounts in the credit currency. |
| `credit_resources(result, *, ax=None)` | Credit funding/capital use with markers for finite resource limits. |
| `credit_concentration(result, *, classification=0, ax=None)` | Group exposure shares versus maximum shares for one concentration classification. |

Hedge plots require `risk_exposures` or `hedge_scenarios`; `risk_id` selects a row of the former. Credit allocation/resource plots require their corresponding credit tables and decision. `classification` is the nonboolean integer index of the `limit_concentration` call, starting at zero. A missing classification or undefined shares from a zero-exposure book raise. See [hedging](hedging.md) and [credit](credit.md).

## Reinsurance and collateral

| Signature | Meaning |
| --- | --- |
| `reinsurance_losses(result, *, ax=None)` | Stacks retained claims and collectible recovery per scenario, with total-cost markers. |
| `reinsurance_surplus(result, *, ax=None)` | Before-claims surplus, surplus after the reinsurance plan, and the configured minimum when present. |
| `collateral_coverage(result, *, obligation, ax=None)` | Required margin and adjusted coverage over dates for one obligation. |
| `collateral_inventory(result, *, asset, ax=None)` | Available inventory before the plan, committed quantities, and quantities awaiting return for one asset. |

Reinsurance plots use `reinsurance_scenarios`; surplus plotting requires its configured surplus accounting. Collateral plots use `collateral_coverage` and `collateral_inventory`, respectively. Obligation and asset selectors are validated against those tables. Coverage amounts use the obligation currency; inventory uses asset quantity units. See [reinsurance](insurance.md) and [collateral](collateral.md).

## Settlement and execution

| Signature | Meaning |
| --- | --- |
| `settlement_balances(result, *, account, ax=None)` | Every ordered balance checkpoint and approved credit floor for one settlement account. |
| `payment_queue(result, *, currency, ax=None)` | Unsettled payment amounts in a currency present in settlement accounts. A valid empty queue remains an empty plot. |
| `execution_schedule(result, *, asset, ax=None)` | Signed planned trades and remaining order quantities by execution slot for one asset. |
| `execution_costs(result, *, ax=None)` | Predicted `price_change`, `spread`, `fees`, `impact`, `underfill`, and `risk` components in currency. |
| `execution_balances(result, *, ax=None)` | Finite pre-trade, before-sale-proceeds, and post-trade cash checkpoints against the recorded cash floor. |

The settlement account must occur in `settlement_ledger`. Execution plots require the execution result tables; `asset` must occur in the trade columns. These figures describe modeled schedules and costs, not actual market fills or payment release. See [settlement](settlement.md) and [execution](execution.md).

## Quantum diagnostic plots

```python
quantum_samples(result, *, ax=None)
quantum_convergence(result, *, ax=None)
```

These accept a `FinanceResult` with the relevant diagnostics even if no financially feasible primary decision was found. This permits inspection of unsuccessful research runs without displaying them as accepted financial recommendations.

`quantum_samples` requires a `quantum_samples` table with `probability` and `feasible` columns and at least one measured candidate. It excludes rows with missing probability, such as unsampled residual candidates, and sorts measured candidates by descending probability. Bars distinguish financially feasible and infeasible samples. Probabilities refer to the provider's reported candidate scope; they are not necessarily the final circuit distribution. Printed bitstrings are most-significant-bit first.

`quantum_convergence` requires a nonempty `quantum_history` table with `training_objective`. It plots reported training values against evaluation order without converting them to source financial objectives or changing their scale. Both titles include result status. See [quantum result semantics](quantum.md#gate-based-result-data).
