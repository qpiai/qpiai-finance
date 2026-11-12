"""Matplotlib views of verified financial results and risk measures."""

import numpy as np

from ._validation import identifiers
from .portfolio import FrontierResult
from .results import FinanceResult

__all__ = [
    "weights",
    "holdings",
    "trades",
    "risk_contributions",
    "loss_distribution",
    "risk_budgets",
    "efficient_frontier",
    "cash_ladder",
    "funding_schedule",
    "facility_utilization",
    "liability_coverage",
    "hedge_exposure",
    "hedge_losses",
    "allocations",
    "credit_resources",
    "credit_concentration",
    "collateral_coverage",
    "collateral_inventory",
    "reinsurance_losses",
    "reinsurance_surplus",
    "settlement_balances",
    "payment_queue",
    "execution_schedule",
    "execution_costs",
    "execution_balances",
    "tax_lot_sales",
    "tax_liability",
    "investment_wealth",
    "investment_trades",
    "investment_funding",
    "quantum_samples",
    "quantum_convergence",
]


def _require_result(result):
    if not isinstance(result, FinanceResult) or not result.feasible:
        raise ValueError(
            "plots require a FinanceResult that passed "
            "financial constraint checks"
        )


def _axes(ax):
    if ax is None:
        import matplotlib.pyplot as plt

        _, ax = plt.subplots(layout="constrained")
    return ax


def _identifier_labels(values):
    values = list(values)
    labels = [str(value) for value in values]
    if len(set(labels)) != len(labels):
        labels = [
            repr(value) if isinstance(value, str) else str(value)
            for value in values
        ]
    return labels


def quantum_samples(result, *, ax=None):
    """Plot recorded candidate probabilities and financial feasibility."""
    if (
        not isinstance(result, FinanceResult)
        or "quantum_samples" not in result.tables
    ):
        raise ValueError("result has no quantum sample diagnostics")
    data = result.tables["quantum_samples"]
    if not {"probability", "feasible"} <= set(data.columns):
        raise ValueError("result has no measured quantum candidates")
    data = data.loc[data.probability.notna()].sort_values(
        "probability", ascending=False, kind="stable"
    )
    if data.empty:
        raise ValueError("result has no measured quantum candidates")
    from matplotlib.patches import Patch

    ax = _axes(ax)
    ax.bar(
        data.index,
        data.probability,
        color=np.where(data.feasible, "tab:blue", "tab:gray"),
    )
    ax.set(
        xlabel="Bitstring (most significant bit first)",
        ylabel="Probability within reported candidates",
        title=f"Quantum samples · {result.status}",
    )
    ax.legend(
        handles=[
            Patch(color="tab:blue", label="Financially feasible"),
            Patch(color="tab:gray", label="Financially infeasible"),
        ]
    )
    return ax


def quantum_convergence(result, *, ax=None):
    """Plot recorded provider training values without changing their scale."""
    if (
        not isinstance(result, FinanceResult)
        or "quantum_history" not in result.tables
    ):
        raise ValueError("result has no quantum training history")
    data = result.tables["quantum_history"]
    if data.empty or "training_objective" not in data:
        raise ValueError("result has no quantum training history")
    ax = _axes(ax)
    ax.plot(data.index, data.training_objective, marker="o")
    ax.set(
        xlabel="Reported evaluation",
        ylabel="Backend training objective",
        title=f"Quantum training · {result.status}",
    )
    return ax


def _investment_case(result, case):
    _require_result(result)
    if "investment_information" not in result.tables:
        raise ValueError("result has no multi-period investment accounts")
    information = result.tables["investment_information"]
    identifiers([case], "case")
    if case not in information.index:
        raise ValueError("case must be a supplied investment scenario ID")
    return information.loc[case].tolist()


def investment_wealth(result, *, case, ax=None):
    """Plot verified marked wealth and cash along one supplied case."""
    nodes = _investment_case(result, case)
    data = result.tables["investment_accounts"].loc[nodes]
    times = result.tables["investment_stage_times"].time
    ax = _axes(ax)
    positions = np.arange(len(nodes))
    ax.plot(positions, data.wealth, marker="o", label="Marked wealth")
    ax.plot(positions, data.closing_cash, marker="o", label="Cash balance")
    ax.set_xticks(positions, [value.isoformat() for value in times])
    ax.set(
        xlabel="Decision stage time",
        ylabel=f"Amount ({data.attrs['currency']})",
        title=f"Investment accounts · {case!r} · {result.status}",
    )
    ax.legend()
    return ax


def investment_trades(result, *, case, asset, ax=None):
    """Plot one asset's verified adaptive trades along a supplied case."""
    nodes = _investment_case(result, case)
    identifiers([asset], "asset")
    if asset not in result.trades.columns:
        raise ValueError("asset must be a supplied investment asset ID")
    ax = _axes(ax)
    positions = np.arange(len(nodes))
    ax.bar(positions, result.trades.loc[nodes, asset])
    ax.set_xticks(positions, [repr(value) for value in nodes])
    ax.set(
        xlabel="Information node",
        ylabel="Asset quantity",
        title=f"Investment trades · {asset!r} · {case!r} · {result.status}",
    )
    return ax


def investment_funding(result, *, case, ax=None):
    """Plot contractual funding and closing term principal along one case."""
    nodes = _investment_case(result, case)
    data = result.tables["investment_accounts"].loc[nodes]
    required = {
        "funding_draws",
        "principal_repayments",
        "funding_interest",
        "funding_fees",
        "outstanding_debt",
    }
    if not required <= set(data.columns):
        raise ValueError("result has no investment funding ledger")
    ax = _axes(ax)
    positions = np.arange(len(nodes))
    ax.bar(positions, data.funding_draws, label="Principal drawn")
    ax.bar(
        positions,
        -data.principal_repayments,
        label="Principal repaid",
    )
    ax.plot(
        positions,
        data.outstanding_debt,
        marker="o",
        label="Outstanding term principal",
    )
    ax.plot(
        positions,
        data.funding_interest + data.funding_fees,
        marker="o",
        label="Interest and fees paid",
    )
    ax.set_xticks(positions, [repr(value) for value in nodes])
    ax.set(
        xlabel="Information node",
        ylabel=f"Amount ({data.attrs['currency']})",
        title=f"Investment funding · {case!r} · {result.status}",
    )
    ax.legend()
    return ax


def _tax_lot_table(result, asset):
    _require_result(result)
    if "tax_lots" not in result.tables:
        raise ValueError("result has no acquisition tax lots")
    table = result.tables["tax_lots"]
    if asset is not None:
        identifiers([asset], "asset")
        if asset not in set(table.asset):
            raise ValueError("asset must belong to the tax lot table")
        table = table.loc[table.asset == asset]
    if table.empty:
        raise ValueError("result has no acquisition tax lots to plot")
    return table


def tax_lot_sales(result, *, asset, ax=None):
    """Plot sold and remaining acquisition-lot quantities for one asset."""
    table = _tax_lot_table(result, asset)
    if asset is None:
        raise ValueError("asset must select one tax lot asset")
    ax = _axes(ax)
    table[["sold", "remaining"]].plot.bar(stacked=True, ax=ax)
    ax.set_xticks(np.arange(len(table)), _identifier_labels(table.index))
    ax.set(
        xlabel="Acquisition lot",
        ylabel="Quantity (shares)",
        title=f"Tax lot disposals · {asset!r} · {result.status}",
    )
    return ax


def tax_liability(result, *, asset=None, ax=None):
    """Plot recognized tax by acquisition lot, including explicit credits."""
    table = _tax_lot_table(result, asset)
    ax = _axes(ax)
    table.tax_liability.plot.bar(ax=ax)
    ax.set_xticks(np.arange(len(table)), _identifier_labels(table.index))
    ax.set(
        xlabel="Acquisition lot",
        ylabel=f"Recognized tax ({table.attrs['currency']})",
        title=(
            f"Tax liability · {table.attrs['as_of'].date()} · {result.status}"
        ),
    )
    return ax


def execution_schedule(result, *, asset, ax=None):
    """Plot signed planned trades and remaining orders for one asset."""
    _require_result(result)
    identifiers([asset], "asset")
    if (
        "execution_orders" not in result.tables
        or asset not in result.trades.columns
    ):
        raise ValueError("asset must belong to a financial execution result")
    ax = _axes(ax)
    slots = np.arange(len(result.trades))
    ax.bar(slots, result.trades[asset], label="Planned trade")
    ax.step(
        slots,
        result.remaining_orders[asset],
        where="post",
        label="Remaining order",
    )
    ax.set_xticks(slots, [repr(value) for value in result.trades.index])
    ax.set(
        xlabel="Execution slot",
        ylabel="Asset quantity",
        title=f"Execution plan · {asset!r} · {result.status}",
    )
    ax.legend()
    return ax


def execution_costs(result, *, ax=None):
    """Show forecast price, spread, fee, impact, underfill and risk costs."""
    _require_result(result)
    if "execution_orders" not in result.tables:
        raise ValueError("result has no execution cost decomposition")
    names = ["price_change", "spread", "fees", "impact", "underfill", "risk"]
    ax = _axes(ax)
    ax.bar(names, [result.costs[name] for name in names])
    ax.set(
        xlabel="Cost component",
        ylabel=f"Cost ({result.costs['currency']})",
        title=f"Predicted execution cost · {result.status}",
    )
    return ax


def execution_balances(result, *, ax=None):
    """Plot pre-trade, prefunding and post-trade cash against actual floors."""
    _require_result(result)
    if "execution_cash" not in result.tables:
        raise ValueError("result has no execution cash ledger")
    table = result.tables["execution_cash"]
    values, floors, labels = [], [], []
    for slot, row in table.iterrows():
        for name in ("cash_before", "cash_before_sale_proceeds", "cash_after"):
            if np.isfinite(row[name]):
                values.append(row[name])
                floors.append(row.cash_floor)
                labels.append(f"{slot!r} · {name.replace('_', ' ')}")
    ax = _axes(ax)
    ax.plot(values, marker="o", label="Cash balance")
    ax.plot(floors, linestyle="--", label="Cash floor")
    ax.set_xticks(np.arange(len(labels)), labels, rotation=30, ha="right")
    ax.set(
        xlabel="Execution checkpoint",
        ylabel=f"Cash ({result.costs['currency']})",
        title=f"Execution liquidity · {result.status}",
    )
    ax.legend()
    return ax


def settlement_balances(result, *, account, ax=None):
    """Plot every ordered balance checkpoint and approved credit floor."""
    _require_result(result)
    if "settlement_ledger" not in result.tables:
        raise ValueError("result has no settlement ledger")
    data = result.tables["settlement_ledger"]
    identifiers([account], "account")
    if account not in data.index.get_level_values("account"):
        raise ValueError("account is not present in the settlement ledger")
    data = data.xs(account, level="account")
    ax = _axes(ax)
    ax.plot(data.index, data.balance, marker="o", label="Balance")
    ax.plot(
        data.index,
        -data.credit_limit,
        linestyle="--",
        label="Approved credit floor",
    )
    ax.set(
        xlabel="Ordered checkpoint",
        ylabel=f"Balance ({data.currency.iloc[0]})",
        title=f"Settlement liquidity · {account} · {result.status}",
    )
    ax.legend()
    return ax


def payment_queue(result, *, currency, ax=None):
    """Show unsettled amounts in one currency; an empty queue stays empty."""
    _require_result(result)
    if "payment_queue" not in result.tables:
        raise ValueError("result has no payment queue")
    if currency not in set(result.tables["settlement_accounts"].currency):
        raise ValueError("currency is not present in settlement accounts")
    data = result.tables["payment_queue"]
    data = data.loc[data.currency == currency]
    ax = _axes(ax)
    positions = np.arange(len(data))
    ax.bar(positions, data.amount)
    ax.set_xticks(positions, _identifier_labels(data.index))
    ax.set(
        xlabel="Payment",
        ylabel=f"Queued amount ({currency})",
        title=f"Payment queue · {result.status}",
    )
    return ax


def reinsurance_losses(result, *, ax=None):
    """Show retained/recovered claims and total cost per scenario."""
    _require_result(result)
    if "reinsurance_scenarios" not in result.tables:
        raise ValueError("result has no reinsurance loss scenarios")
    data = result.tables["reinsurance_scenarios"]
    ax = _axes(ax)
    positions = np.arange(len(data))
    ax.bar(positions, data.retained_loss, label="Retained claims")
    ax.bar(
        positions,
        data.collectible_recovery,
        bottom=data.retained_loss,
        label="Collectible recovery",
    )
    ax.scatter(positions, data.total_cost, marker="x", label="Total cost")
    ax.set_xticks(positions, _identifier_labels(data.index))
    ax.set(
        xlabel="Scenario",
        ylabel=f"Amount ({data.currency.iloc[0]})",
        title=f"Reinsurance losses and cost · {result.status}",
    )
    ax.legend()
    return ax


def reinsurance_surplus(result, *, ax=None):
    """Compare supplied pre-claims surplus and actual post-plan surplus."""
    _require_result(result)
    if (
        "reinsurance_scenarios" not in result.tables
        or "surplus_after" not in result.tables["reinsurance_scenarios"]
    ):
        raise ValueError("result has no insurance surplus accounting")
    data = result.tables["reinsurance_scenarios"]
    ax = _axes(ax)
    positions = np.arange(len(data))
    ax.plot(
        positions,
        data.surplus_before_claims,
        marker="o",
        label="Before claims/costs",
    )
    ax.plot(
        positions,
        data.surplus_after,
        marker="o",
        label="After reinsurance/costs",
    )
    if "minimum_surplus" in data:
        ax.plot(
            positions,
            data.minimum_surplus,
            linestyle="--",
            label="Minimum surplus",
        )
    ax.set_xticks(positions, _identifier_labels(data.index))
    ax.set(
        xlabel="Scenario",
        ylabel=f"Amount ({data.currency.iloc[0]})",
        title=f"Insurance surplus · {result.status}",
    )
    ax.legend()
    return ax


def collateral_coverage(result, *, obligation, ax=None):
    """Compare dated margin and adjusted coverage for one obligation."""
    _require_result(result)
    if "collateral_coverage" not in result.tables:
        raise ValueError("result has no collateral coverage")
    identifiers([obligation], "obligation")
    data = result.tables["collateral_coverage"]
    data = data.loc[data.obligation == obligation].sort_values("date")
    if data.empty:
        raise ValueError("obligation is not present in collateral coverage")
    ax = _axes(ax)
    ax.plot(data.date, data.required, marker="o", label="Required")
    ax.plot(
        data.date, data.adjusted_value, marker="o", label="Adjusted coverage"
    )
    ax.set(
        xlabel="Date",
        ylabel=f"Amount ({data.currency.iloc[0]})",
        title=f"Collateral coverage · {obligation} · {result.status}",
    )
    ax.legend()
    return ax


def collateral_inventory(result, *, asset, ax=None):
    """Plot one collateral lot's availability and committed quantities."""
    _require_result(result)
    if "collateral_inventory" not in result.tables:
        raise ValueError("result has no collateral inventory accounting")
    data = result.tables["collateral_inventory"]
    identifiers([asset], "asset")
    if asset not in data.index.get_level_values("asset"):
        raise ValueError("asset is not present in collateral inventory")
    data = data.xs(asset, level="asset")
    ax = _axes(ax)
    for column, label in (
        ("available_before_plan", "Available before plan"),
        ("committed", "Committed"),
        ("awaiting_return", "Awaiting return"),
    ):
        ax.plot(data.index, data[column], marker="o", label=label)
    ax.set(
        xlabel="Date",
        ylabel=f"{asset} (asset units)",
        title=f"Collateral inventory · {result.status}",
    )
    ax.legend()
    return ax


def allocations(result, *, ax=None):
    """Compare existing and proposed credit facility amounts in currency."""
    _require_result(result)
    if "allocations" not in result.tables:
        raise ValueError("result has no credit allocations")
    data = result.tables["allocations"]
    ax = _axes(ax)
    positions = np.arange(len(data))
    ax.bar(positions - 0.2, data.current_amount, width=0.4, label="Existing")
    ax.bar(positions + 0.2, data.allocated_amount, width=0.4, label="Proposed")
    ax.set_xticks(positions, _identifier_labels(data.index))
    ax.set(
        xlabel="Facility",
        ylabel=f"Amount ({data.currency.iloc[0]})",
        title=f"Credit allocation · {result.status}",
    )
    ax.legend()
    return ax


def credit_resources(result, *, ax=None):
    """Plot credit funding/capital use and finite supplied limits."""
    _require_result(result)
    if "resources" not in result.tables or result.allocations is None:
        raise ValueError("result has no credit resource accounting")
    data = result.tables["resources"]
    ax = _axes(ax)
    positions = np.arange(len(data))
    ax.bar(positions, data.used, label="Used")
    finite = np.isfinite(data.limit.to_numpy())
    ax.scatter(
        positions[finite], data.limit[finite], marker="_", s=200, label="Limit"
    )
    ax.set_xticks(positions, [str(value).capitalize() for value in data.index])
    ax.set(
        ylabel=f"Amount ({data.currency.iloc[0]})",
        title=f"Credit resources · {result.status}",
    )
    ax.legend()
    return ax


def credit_concentration(result, *, classification=0, ax=None):
    """Compare verified credit group exposure shares and supplied limits.

    classification is the zero-based order of limit_concentration calls.
    A zero-exposure book has undefined shares and cannot produce this plot.
    """
    _require_result(result)
    if "concentrations" not in result.tables:
        raise ValueError("result has no credit concentration accounting")
    data = result.tables["concentrations"]
    if isinstance(classification, (bool, np.bool_)) or not isinstance(
        classification, (int, np.integer)
    ):
        raise ValueError("classification must be an integer call index")
    data = data.loc[data.classification == classification]
    if data.empty or data.share.isna().any():
        raise ValueError("classification must have defined exposure shares")
    ax = _axes(ax)
    positions = np.arange(len(data))
    ax.bar(positions, data.share, label="Exposure share")
    ax.scatter(
        positions, data.maximum_share, marker="_", s=200, label="Maximum share"
    )
    ax.set_xticks(positions, _identifier_labels(data.group))
    ax.set(
        xlabel="Group",
        ylabel="Fraction of total exposure",
        title=f"Credit concentration · {result.status}",
    )
    ax.legend()
    return ax


def liability_coverage(result, *, ax=None):
    """Plot dated asset receipts, liabilities and retained cash in currency."""
    _require_result(result)
    if "liability_coverage" not in result.tables:
        raise ValueError("result has no dated liability coverage")
    data = result.tables["liability_coverage"]
    ax = _axes(ax)
    for column, label in (
        ("asset_cash_flow", "Asset cash flow"),
        ("liability", "Liability payment"),
        ("closing_cash", "Retained cash"),
    ):
        ax.plot(data.index, data[column], marker="o", label=label)
    ax.set(
        xlabel="Date",
        ylabel=f"Amount ({data.currency.iloc[0]})",
        title=f"Liability coverage · {result.status}",
    )
    ax.legend()
    return ax


def hedge_losses(result, *, ax=None):
    """Compare supplied book losses and verified net losses after hedging."""
    _require_result(result)
    if "hedge_scenarios" not in result.tables:
        raise ValueError("result has no supplied hedge P&L scenarios")
    data = result.tables["hedge_scenarios"]
    ax = _axes(ax)
    positions = np.arange(len(data))
    ax.bar(positions - 0.2, -data.before_pnl, width=0.4, label="Before hedge")
    ax.bar(
        positions + 0.2, data.loss, width=0.4, label="After hedge and costs"
    )
    ax.set_xticks(positions, [repr(value) for value in data.index])
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set(
        xlabel="Scenario",
        ylabel=f"Loss ({data.attrs['currency']})",
        title=f"Scenario hedge · {data.attrs['horizon']} · {result.status}",
    )
    ax.legend()
    return ax


def hedge_exposure(result, *, risk_id, ax=None):
    """Compare one signed risk before/after hedging and against its target."""
    _require_result(result)
    if "risk_exposures" not in result.tables:
        raise ValueError("result has no hedge risk exposures")
    data = result.tables["risk_exposures"]
    identifiers([risk_id], "risk_id")
    if risk_id not in data.index:
        raise ValueError("risk_id is not present in the hedge exposures")
    risk = data.loc[risk_id]
    ax = _axes(ax)
    ax.bar(
        ["Before", "After", "Target"],
        risk[["before", "after", "target"]].to_numpy(dtype=float),
    )
    ax.axhline(0, linewidth=0.8, color="black")
    ax.set(
        xlabel="Exposure",
        ylabel=f"{risk_id} ({risk['unit']})",
        title=f"Hedge exposure · {result.status}",
    )
    return ax


def _account_ladder(result, account, case=None):
    _require_result(result)
    if "cash_ladder" not in result.tables:
        raise ValueError("result has no dated cash ladder")
    ladder = result.tables["cash_ladder"]
    identifiers([account], "account")
    if account not in ladder.index.get_level_values("account"):
        raise ValueError("account is not present in the cash ladder")
    data = ladder.xs(account, level="account")
    if "node" in ladder.index.names:
        if case is None:
            raise ValueError(
                "select a scenario case for an adaptive cash ladder"
            )
        identifiers([case], "case")
        information = result.tables["funding_information"]
        if case not in information.index:
            raise ValueError("unknown funding scenario case")
        data = data.loc[information.loc[case].tolist()].copy()
        data.index = result.tables["funding_nodes"].loc[data.index, "time"]
    elif case is not None:
        raise ValueError("a dated cash ladder has no scenario cases")
    return data


def cash_ladder(result, *, account, case=None, ax=None):
    """Plot an account's cash balance and buffer in its native currency."""
    data = _account_ladder(result, account, case)
    ax = _axes(ax)
    ax.plot(data.index, data.closing_cash, marker="o", label="Closing cash")
    ax.plot(data.index, data.cash_buffer, linestyle="--", label="Cash buffer")
    ax.set(
        xlabel="Date",
        ylabel=f"Cash ({data.currency.iloc[0]})",
        title=f"Cash ladder · {account} · {result.status}",
    )
    ax.legend()
    return ax


def funding_schedule(result, *, account, case=None, ax=None):
    """Plot dated principal draws and repayments in one account's currency."""
    data = _account_ladder(result, account, case)
    ax = _axes(ax)
    ax.plot(data.index, data.draws, marker="o", label="Principal drawn")
    ax.plot(
        data.index,
        data.principal_repayments,
        marker="o",
        label="Principal repaid",
    )
    ax.set(
        xlabel="Date",
        ylabel=f"Principal ({data.currency.iloc[0]})",
        title=f"Funding schedule · {account} · {result.status}",
    )
    ax.legend()
    return ax


def facility_utilization(result, *, facility, ax=None):
    """Show modeled/reserved principal capacity and its dated or node limit.

    Select one declared facility. Values use its capacity currency, which
    may differ from account/reporting currencies. Information nodes remain
    separate states; bars do not join mutually exclusive branches as a path.
    """
    _require_result(result)
    identifiers([facility], "facility")
    if "funding_facilities" not in result.tables:
        raise ValueError("result has no facility utilization")
    table = result.tables["funding_facilities"]
    if facility not in table.index.get_level_values("facility"):
        raise ValueError("unknown facility")
    data = table.xs(facility, level="facility")
    ax = _axes(ax)
    positions = np.arange(len(data))
    ax.bar(positions, data.modelled_utilization, label="Modeled principal")
    ax.bar(
        positions,
        data.reserved_utilization,
        bottom=data.modelled_utilization,
        label="Reserved utilization",
    )
    ax.scatter(
        positions,
        data.maximum,
        marker="_",
        s=200,
        color="black",
        label="Limit",
    )
    labels = (
        data.index.strftime("%Y-%m-%d")
        if data.index.name == "date"
        else _identifier_labels(data.index)
    )
    ax.set_xticks(positions, labels)
    ax.set(
        xlabel="Date" if data.index.name == "date" else "Information node",
        ylabel=f"Utilization ({data.currency.iloc[0]})",
        title=f"Funding facility · {facility} · {result.status}",
    )
    ax.legend()
    return ax


def holdings(result, *, ax=None):
    """Compare opening and post-trade share quantities."""
    _require_result(result)
    if "trades" not in result.tables:
        raise ValueError("result has no share holdings")
    ax = _axes(ax)
    result.tables["trades"][["before", "after"]].plot.bar(ax=ax)
    ax.set_xticks(
        np.arange(len(result.tables["trades"])),
        _identifier_labels(result.tables["trades"].index),
    )
    ax.set(
        xlabel="Asset",
        ylabel="Quantity (shares)",
        title=f"Portfolio holdings · {result.status}",
    )
    return ax


def trades(result, *, ax=None):
    """Plot signed share trades: positive for purchases, negative for sales."""
    _require_result(result)
    if "investment_accounts" in result.tables:
        raise ValueError(
            "use investment_trades(result, case=..., asset=...) "
            "for multi-period plans"
        )
    if "execution_schedule" in result.tables:
        raise ValueError(
            "use execution_schedule(result, asset=...) for execution plans"
        )
    if result.trades is None:
        raise ValueError("result has no share trades")
    ax = _axes(ax)
    result.trades.plot.bar(ax=ax)
    ax.set_xticks(
        np.arange(len(result.trades)), _identifier_labels(result.trades.index)
    )
    ax.set(
        xlabel="Asset",
        ylabel="Trade quantity (shares)",
        title=f"Proposed trades · {result.status}",
    )
    return ax


def weights(result, *, ax=None):
    """Source portfolio weights; no visual rounding or renormalization."""
    _require_result(result)
    if result.weights is None:
        raise ValueError("result has no portfolio weights")
    ax = _axes(ax)
    result.weights.plot.bar(ax=ax)
    ax.set_xticks(
        np.arange(len(result.weights)),
        _identifier_labels(result.weights.index),
    )
    ax.set(
        ylabel="Weight (fraction of investment basis)",
        xlabel="Asset",
        title=f"Portfolio weights · {result.status}",
    )
    return ax


def risk_budgets(result, *, ax=None):
    """Compare requested and realized fractions of variance risk."""
    _require_result(result)
    if "risk_budgets" not in result.tables:
        raise ValueError("result has no risk budgets")
    ax = _axes(ax)
    result.tables["risk_budgets"][["budget", "contribution"]].plot.bar(ax=ax)
    ax.set_xticks(
        np.arange(len(result.tables["risk_budgets"])),
        _identifier_labels(result.tables["risk_budgets"].index),
    )
    ax.set(
        xlabel="Asset",
        ylabel="Fraction of portfolio variance",
        title=f"Risk allocation · {result.status}",
    )
    return ax


def efficient_frontier(result, *, ax=None):
    """Plot verified portfolios against their realized risk and return."""
    if not isinstance(result, FrontierResult):
        raise TypeError("result must be a FrontierResult")
    table = result.table
    feasible = table.loc[table.feasible]
    if feasible.empty:
        raise ValueError("frontier has no financially feasible portfolios")
    feasible = feasible.sort_values("volatility")
    optimal = int(feasible.optimality_proven.sum())
    ax = _axes(ax)
    ax.plot(
        feasible.volatility,
        feasible.expected_return,
        marker="o",
        label=(
            f"{len(feasible)} feasible of {len(table)} targets; "
            f"{optimal} optimal"
        ),
    )
    ax.set(
        xlabel="Volatility (return fraction)",
        ylabel="Expected return (fraction)",
        title=f"Efficient frontier · {result.horizon}",
    )
    ax.legend()
    return ax


def risk_contributions(result, *, kind="variance", by="asset", ax=None):
    """Plot calculated risk by asset or by factor and specific risk.

    by='factor' requires a portfolio result with FactorRisk. Negative
    contributions remain signed; no risk is recalculated for the plot.
    """
    _require_result(result)
    if kind not in {"variance", "volatility"}:
        raise ValueError("kind must be 'variance' or 'volatility'")
    if by not in {"asset", "factor"}:
        raise ValueError("by must be 'asset' or 'factor'")
    table = (
        "risk_contributions" if by == "asset" else "factor_risk_contributions"
    )
    if table not in result.tables:
        raise ValueError("result has no covariance risk contributions")
    values = result.tables[table][kind]
    if not np.isfinite(values).all():
        raise ValueError("risk contributions are undefined at zero volatility")
    ax = _axes(ax)
    values.plot.bar(ax=ax)
    if by == "factor":
        labels = np.empty(len(values), dtype=object)
        components = values.index.get_level_values("component")
        for component in ("factor", "specific"):
            selected = components == component
            names = values.index.get_level_values("id")[selected]
            labels[selected] = [
                f"{component.capitalize()}: {name}"
                for name in _identifier_labels(names)
            ]
    else:
        labels = _identifier_labels(values.index)
    ax.set_xticks(np.arange(len(values)), labels)
    unit = "return fraction²" if kind == "variance" else "return fraction"
    ax.set(
        ylabel=f"{kind.capitalize()} contribution ({unit})",
        xlabel="Asset" if by == "asset" else "Risk source",
        title=(
            "Risk contributions · "
            f"{result.provenance['inputs']['horizon']} · {result.status}"
        ),
    )
    return ax


def loss_distribution(result, *, ax=None):
    """Plot scenario losses, probabilities and expected shortfall."""
    _require_result(result)
    if "scenarios" not in result.tables:
        raise ValueError("result has no scenario loss distribution")
    ax = _axes(ax)
    data = result.tables["scenarios"]
    edges = np.histogram_bin_edges(data.loss, bins="auto")
    ax.hist(data.loss, weights=data.probability, bins=edges, edgecolor="white")
    if "expected_shortfall" in result.metrics:
        beta = result.metrics["confidence"]
        ax.axvline(
            result.metrics["expected_shortfall"],
            label=f"ES ({beta:.1%})",
            color="darkred",
        )
        ax.legend()
    ax.set(
        xlabel="Loss (return fraction)",
        ylabel="Scenario probability",
        title=(
            "Scenario losses · "
            f"{result.provenance['inputs']['horizon']} · {result.status}"
        ),
    )
    return ax
