"""Financial inputs expressed through public constructors and configuration."""

import numpy as np
import pandas as pd

from ._validation import copy_index
from .collateral import CollateralAllocationModel
from .credit import CreditAllocationModel
from .hedging import HedgeModel
from .insurance import ReinsuranceModel
from .portfolio import PortfolioModel
from .settlement import SettlementModel
from .trading import ExecutionModel, TradingModel
from .treasury import FundingModel, LiabilityMatchingModel
from .treasury._facilities import configuration as facility_configuration


class _Configuration(list):
    def add(self, method, **arguments):
        self.append((method, arguments))


def _optional_bound(values):
    return None if np.isinf(values).all() else values


def _portfolio(model):
    inputs = dict(
        expected_returns=model._mu,
        covariance=model._covariance,
        horizon=model.horizon,
        asset_ids=model.asset_ids,
        net_weight=model._net_weight,
    )
    settings = _Configuration()
    settings.add("limit_weights", lower=model._lower, upper=model._upper)
    account = model._account
    if account is not None:
        for name in (
            "holdings",
            "prices",
            "cash",
            "currency",
            "bid_prices",
            "ask_prices",
            "cash_return",
        ):
            inputs[name] = getattr(account, name)
        settings.add(
            "limit_cash",
            minimum=account.cash_lower * account.initial_value,
            maximum=account.cash_upper * account.initial_value,
        )
        settings.add(
            "set_trading_costs",
            **{
                name: getattr(account, name)
                for name in (
                    "buy_bps",
                    "sell_bps",
                    "buy_fixed",
                    "sell_fixed",
                    "minimum_trade",
                )
            },
        )
        if account.lots is not None:
            settings.add("trade_in_lots", lot_sizes=account.lots)
        if account.short_available is not None:
            settings.add(
                "limit_short_positions", maximum=account.short_available
            )
        if account.tax_lots is not None:
            book = account.tax_lots
            settings.add(
                "set_tax_lots",
                lots=book.table,
                as_of=book.as_of,
                settlement=book.settlement,
            )
            settings.add(
                "limit_tax", minimum=book.minimum, maximum=book.maximum
            )
    for ids, values, low, high in model._exposures:
        settings.add(
            "limit_exposures",
            exposures=values,
            lower=low,
            upper=high,
            exposure_ids=ids,
        )
    if model._minimum_return is not None:
        settings.add("require_return", minimum=model._minimum_return)
    if model._leverage is not None:
        settings.add("limit_leverage", maximum=model._leverage)
    if model._volatility_limit is not None:
        settings.add("limit_volatility", maximum=model._volatility_limit)
    if model._turnover is not None:
        current, maximum = model._turnover
        settings.add(
            "limit_turnover", current_weights=current, maximum=maximum
        )
    if model._return_uncertainty is not None:
        ids, values, radius = model._return_uncertainty
        settings.add(
            "robust_returns",
            uncertainty=values,
            radius=radius,
            uncertainty_ids=ids,
        )
    if model._selection is not None:
        settings.add("select_assets", **model._selection)
    if model._fixed_selection is not None:
        settings.add(
            "fix_selection",
            selected=model._fixed_selection,
        )

    # Public objective setters retain some inputs after an objective changes.
    # Restore those inputs first, and select the active objective last.
    if model._objective != "utility" and model._risk_aversion != 1:
        settings.add("maximize_utility", risk_aversion=model._risk_aversion)
    if model._objective != "hrp" and model._linkage_method != "single":
        settings.add(
            "hierarchical_risk_parity", linkage_method=model._linkage_method
        )
    if (
        model._objective != "risk_budgeting"
        and model._risk_budgets is not None
    ):
        settings.add(
            "allocate_risk",
            budgets=model._risk_budgets,
            polish=model._risk_budget_polish,
            polish_maxiter=model._risk_budget_polish_maxiter,
        )
    if model._scenarios is not None:
        if (
            model._moment_preferences is not None
            and model._objective != "moment_utility"
        ):
            variance, skewness, kurtosis = model._moment_preferences
            settings.add(
                "maximize_moment_utility",
                scenarios=model._scenarios,
                variance_aversion=variance,
                skewness_preference=skewness,
                kurtosis_aversion=kurtosis,
            )
        if (
            hasattr(model, "_downside_target")
            and model._objective != "downside"
        ):
            settings.add(
                "minimize_downside_risk",
                scenarios=model._scenarios,
                target=model._downside_target,
            )
        scenario_objectives = {
            "expected_shortfall",
            "mean_absolute_deviation",
            "downside",
            "moment_utility",
        }
        if model._objective not in scenario_objectives:
            if model._confidence is not None:
                settings.add(
                    "minimize_expected_shortfall",
                    scenarios=model._scenarios,
                    confidence=model._confidence,
                )
            else:
                settings.add(
                    "minimize_mean_absolute_deviation",
                    scenarios=model._scenarios,
                )

    objective = model._objective
    if objective == "variance":
        settings.add("minimize_variance")
    elif objective == "utility":
        settings.add("maximize_utility", risk_aversion=model._risk_aversion)
    elif objective == "tracking_error":
        settings.add("minimize_tracking_error", benchmark=model._benchmark)
    elif objective == "hrp":
        settings.add(
            "hierarchical_risk_parity", linkage_method=model._linkage_method
        )
    elif objective == "risk_budgeting":
        settings.add(
            "allocate_risk",
            budgets=model._risk_budgets,
            polish=model._risk_budget_polish,
            polish_maxiter=model._risk_budget_polish_maxiter,
        )
    elif objective == "expected_shortfall":
        settings.add(
            "minimize_expected_shortfall",
            scenarios=model._scenarios,
            confidence=model._confidence,
        )
    elif objective == "mean_absolute_deviation":
        settings.add(
            "minimize_mean_absolute_deviation", scenarios=model._scenarios
        )
    elif objective == "downside":
        settings.add(
            "minimize_downside_risk",
            scenarios=model._scenarios,
            target=model._downside_target,
        )
    elif objective == "moment_utility":
        variance, skewness, kurtosis = model._moment_preferences
        settings.add(
            "maximize_moment_utility",
            scenarios=model._scenarios,
            variance_aversion=variance,
            skewness_preference=skewness,
            kurtosis_aversion=kurtosis,
        )
    else:
        raise ValueError("unsupported portfolio objective for interchange")
    return inputs, settings


def _funding(model):
    from .treasury._balance_sheet import (
        configuration as exposure_configuration,
    )

    inputs = dict(
        cash_flows=model._flows,
        balances=pd.DataFrame(
            {
                "currency": model._currencies,
                "cash": model._opening,
            },
            index=copy_index(model._ids),
        ),
        as_of=model._as_of,
        **(
            {"dates": model.dates}
            if model._tree is None
            else {"tree": model.tree}
        ),
        reporting_currency=model.reporting_currency,
        fx_rates=model._fx.to_dict(),
        deposit_returns=model._returns,
        discount_factors=model._discount,
    )
    settings = _Configuration()
    settings.add(
        "limit_cash",
        minimum=model._cash_lower,
        maximum=_optional_bound(model._cash_upper),
    )
    if np.isfinite(model._debt_upper).all():
        settings.add("limit_debt", maximum=model._debt_upper)
    for method, identifier, contracts in (
        ("add_funding", "funding_id", model._funding),
        ("add_existing_debt", "debt_id", model._existing_debt),
        ("add_transfer", "transfer_id", model._transfers),
        ("add_investment", "investment_id", model._investments),
    ):
        for key, contract in contracts.items():
            settings.add(
                method,
                **{identifier: key, **model._contract_arguments(contract)},
            )
    for key, arguments in facility_configuration(
        model._facilities, model._periods
    ):
        settings.add("limit_facility", facility_id=key, **arguments)
    for key, arguments in exposure_configuration(model):
        settings.add("limit_exposure", exposure_id=key, **arguments)
    if model._cost_measure == "worst_case":
        settings.add("minimize_worst_case_cost")
    elif model._cost_measure == "expected_shortfall":
        settings.add(
            "minimize_expected_shortfall", confidence=model._confidence
        )
    if model._tail_limit is not None:
        maximum, confidence = model._tail_limit
        settings.add(
            "limit_expected_shortfall", maximum=maximum, confidence=confidence
        )
    return inputs, settings


def _matching(model):
    inputs = dict(
        prices=model._prices,
        cash_flows=model._flows,
        liabilities=model._liabilities,
        currency=model.currency,
        as_of=model._as_of,
        dates=model.dates,
        asset_ids=model.asset_ids,
        deposit_returns=model._returns,
    )
    settings = _Configuration()
    settings.add(
        "limit_holdings",
        lower=model._lower,
        upper=_optional_bound(model._upper),
    )
    settings.add(
        "limit_cash",
        minimum=model._cash_lower,
        maximum=_optional_bound(model._cash_upper),
    )
    if np.isfinite(model._capital_limit):
        settings.add("limit_initial_capital", maximum=model._capital_limit)
    if model._lots is not None:
        settings.add("buy_in_lots", lot_sizes=model._lots)
    if model._sensitivities is not None:
        ids, values, target, units = model._sensitivities
        settings.add(
            "match_sensitivities",
            sensitivities=values,
            target=target,
            risk_units=units,
            risk_ids=ids,
        )
    return inputs, settings


def _hedging(model):
    inputs = dict(
        current_exposures=model._exposure if len(model._risks) else None,
        sensitivities=model._sensitivities if len(model._risks) else None,
        risk_units=model._units if len(model._risks) else None,
        currency=model.currency,
        as_of=model._as_of,
        instrument_ids=model.instrument_ids,
        risk_ids=model.risk_ids if len(model._risks) else None,
        current_positions=model._current,
    )
    if model._pnl_scenarios is not None:
        inputs.update(
            current_pnl=model._current_pnl,
            pnl_scenarios=model.pnl_scenarios,
            cost_factors=model._cost_factors,
        )
    settings = _Configuration()
    settings.add(
        "limit_trades",
        lower=_optional_bound(model._lower),
        upper=_optional_bound(model._upper),
    )
    settings.add(
        "limit_positions",
        lower=_optional_bound(model._position_lower),
        upper=_optional_bound(model._position_upper),
    )
    settings.add(
        "set_transaction_costs", buy=model._buy_cost, sell=model._sell_cost
    )
    if len(model._risks) and np.isfinite(model._risk_lower).all():
        settings.add(
            "limit_exposures", lower=model._risk_lower, upper=model._risk_upper
        )
    if model._cash is not None:
        settings.add(
            "set_cash_account",
            cash=model._cash,
            prices=model._prices,
            bid_prices=model._bid,
            ask_prices=model._ask,
        )
    if model._capital is not None:
        values, maximum = model._capital
        settings.add("limit_capital", capital_per_unit=values, maximum=maximum)
    if model._lots is not None:
        settings.add("trade_in_lots", lot_sizes=model._lots)
    if model._loss_limit is not None:
        settings.add("limit_scenario_loss", maximum=model._loss_limit)
    if model._es_limit is not None:
        maximum, level = model._es_limit
        settings.add(
            "limit_expected_shortfall", maximum=maximum, confidence=level
        )
    if model._weights is not None:
        settings.add(
            "minimize_mismatch",
            weights=model._weights,
            target=model._target,
            cost_weight=model._cost_weight,
        )
    elif model._objective != "hedge_cost" and np.any(model._target != 0):
        settings.add("match_exposures", target=model._target)
    if model._objective == "hedge_cost":
        settings.add("match_exposures", target=model._target)
    elif model._objective == "hedge_expected_shortfall":
        settings.add(
            "minimize_expected_shortfall", confidence=model._confidence
        )
    elif model._objective == "hedge_worst_loss":
        settings.add("minimize_worst_case_loss")
    return inputs, settings


def _credit(model):
    inputs = dict(
        income_rates=model._income,
        funding_costs=model._funding_cost,
        expected_loss_rates=model._expected_loss,
        capital_requirements=model._capital,
        capacity=model._capacity,
        currency=model.currency,
        horizon=model._horizon,
        as_of=model._as_of,
        facility_ids=model.facility_ids,
        funding_requirements=model._funding,
        exposure_per_unit=model._ead,
        current_allocations=model._current,
    )
    settings = _Configuration()
    settings.add("limit_allocations", lower=model._lower, upper=model._upper)
    settings.add(
        "set_transaction_costs",
        increase=model._increase_cost,
        decrease=model._decrease_cost,
    )
    if model._default_risk is not None:
        pd_rate, lgd, ead = model._default_risk
        settings.add(
            "set_default_risk",
            probability_of_default=pd_rate,
            loss_given_default=lgd,
            exposure_at_default=ead,
        )
    for method, maximum in (
        ("limit_funding", model._funding_limit),
        ("limit_capital", model._capital_limit),
    ):
        if np.isfinite(maximum):
            settings.add(method, maximum=maximum)
    if model._lots is not None:
        settings.add("allocate_in_lots", lot_sizes=model._lots)
    if model._selection is not None:
        minimum, count = model._selection
        settings.add("select_facilities", minimum=minimum, maximum_count=count)
    for ids, values, low, high in model._exposures:
        settings.add(
            "limit_exposures",
            coefficients=values,
            lower=low,
            upper=high,
            exposure_ids=ids,
        )
    for groups, _, shares in model._concentrations:
        settings.add(
            "limit_concentration", groups=groups, maximum_share=shares
        )
    if model._scenarios is not None:
        settings.add("set_loss_scenarios", scenarios=model._scenarios)
    if model._scenario_limit is not None:
        settings.add("limit_scenario_loss", maximum=model._scenario_limit)
    if model._tail_limit is not None:
        maximum, beta = model._tail_limit
        settings.add(
            "limit_expected_shortfall", maximum=maximum, confidence=beta
        )
    settings.add(
        "maximize_risk_adjusted_income",
        capital_charge=model._capital_charge,
        risk_aversion=model._risk_aversion,
        confidence=model._confidence,
    )
    return inputs, settings


def _collateral(model):
    inputs = dict(
        inventory=model._inventory,
        requirements=model._requirements,
        pledges=model._pledges,
        as_of=model._as_of,
        dates=model.dates,
        reporting_currency=model.reporting_currency,
    )
    settings = _Configuration()
    if model._available is not None:
        settings.add("set_availability", quantities=model._available)
    if len(model.pledge_ids):
        settings.add(
            "limit_assignments", lower=model._lower, upper=model._upper
        )
    for method, argument, value in (
        ("set_prices", "prices", model._prices),
        ("set_haircuts", "haircuts", model._haircuts),
        ("set_fx_rates", "fx_rates", model._fx_rates),
        ("pledge_in_lots", "lot_sizes", model._lots),
    ):
        if value is not None:
            settings.add(method, **{argument: value})
    if np.isfinite(model._coverage_upper).all():
        settings.add("limit_coverage", maximum=model._coverage_upper)
    pledged = _optional_bound(model._pledge_limits)
    returned = _optional_bound(model._return_limits)
    if pledged is not None or returned is not None:
        settings.add("limit_movements", pledged=pledged, returned=returned)
    for groups, _, shares in model._concentrations:
        settings.add(
            "limit_concentration", groups=groups, maximum_share=shares
        )
    return inputs, settings


def _reinsurance(model):
    inputs = dict(
        gross_losses=model._gross,
        recoveries=model._recoveries,
        premiums=model._premiums,
        recovery_composition=model._composition,
        currency=model.currency,
        horizon=model._horizon,
        as_of=model._as_of,
        probabilities=model._probabilities,
        scenario_ids=model.scenario_ids,
        contract_ids=model.contract_ids,
    )
    settings = _Configuration()
    settings.add("set_recoverability", factors=model._recoverability)
    settings.add("set_contingent_costs", costs=model._charges)
    settings.add("limit_selections", lower=model._lower, upper=model._upper)
    settings.add(
        "limit_contract_count",
        minimum=model._count[0],
        maximum=model._count[1],
    )
    for group in model._exclusive_groups:
        settings.add("add_exclusive_group", contract_ids=group)
    for method, value in (
        ("limit_premium", model._premium_limit),
        ("limit_retained_loss", model._retained_limit),
        ("limit_total_cost", model._total_limit),
    ):
        if np.isfinite(value).all():
            settings.add(method, maximum=value)
    for (measure, beta), maximum in model._tail_limits.items():
        settings.add(
            "limit_expected_shortfall",
            maximum=maximum,
            confidence=beta,
            measure=measure,
        )
    for ids, values, maximum in model._counterparty_limits:
        settings.add(
            "limit_counterparty_exposure",
            coefficients=values,
            maximum=maximum,
            exposure_ids=ids,
        )
    if model._surplus is not None:
        settings.add("set_surplus_before_claims", surplus=model._surplus)
    if model._surplus_minimum is not None:
        settings.add("require_surplus", minimum=model._surplus_minimum)
    if model._probabilities is not None:
        settings.add(
            "minimize_expected_cost",
            tail_weight=model._tail_weight,
            confidence=model._confidence,
        )
    if model._objective == "reinsurance_premium":
        settings.add("minimize_premium")
    return inputs, settings


def _settlement(model):
    inputs = dict(
        accounts=model._accounts,
        payments=model._payments,
        as_of=model._as_of,
        slots=model._times,
        reporting_currency=model._currency,
        settlement_method=model._method,
        slot_ids=model.slot_ids,
    )
    settings = _Configuration()
    settings.add("set_external_flows", flows=model._flows)
    settings.add("set_credit_limits", limits=model._credit_limits)
    settings.add(
        "allow_prefunding",
        maximum=model._prefunding_limit,
        cost_per_unit=model._prefunding_cost,
    )
    settings.add("set_credit_costs", cost_per_unit=model._credit_cost)
    if model._final_lower is not None:
        settings.add("limit_final_balances", lower=model._final_lower)
    for identifier, ids in model._batches:
        settings.add("add_atomic_batch", batch_id=identifier, payment_ids=ids)
    for before, after, same in model._precedences:
        settings.add(
            "add_precedence", before=before, after=after, allow_same_batch=same
        )
    return inputs, settings


def _execution(model):
    inputs = dict(
        orders=model._orders,
        opportunities=model._opportunities,
        arrival_prices=model._arrival,
        holdings=model._opening,
        cash=model._cash,
        currency=model.currency,
        as_of=model._as_of,
        slots=model._times,
        cash_settlement=model._settlement,
        asset_ids=model.asset_ids,
        slot_ids=model.slot_ids,
        credit_limit=model._opening_credit,
        borrow_limits=model._opening_borrow,
    )
    settings = _Configuration()
    settings.add(
        "set_execution_costs",
        per_unit=model._fees,
        fixed=model._fixed,
        minimum_trade=model._minimum,
    )
    if model._lots is not None:
        settings.add("trade_in_lots", lot_sizes=model._lots)
    if model._underfill is not None:
        settings.add("allow_underfill", penalty=model._underfill)
        if model._hard.any():
            settings.add(
                "require_completion", asset_ids=model._ids[model._hard]
            )
    settings.add(
        "set_order_windows",
        release=list(model._release),
        deadline=list(model._deadlines),
    )
    settings.add("set_cash_flows", flows=model._flows)
    settings.add("set_credit_limits", maximum=model._credit)
    if np.isfinite(model._cash_minimum).all():
        settings.add("limit_cash", minimum=model._cash_minimum)
    settings.add("set_borrow_limits", maximum=model._borrow)
    if model._position_limits is not None:
        settings.add(
            "limit_positions",
            lower=_optional_bound(model._position_limits[0]),
            upper=_optional_bound(model._position_limits[1]),
        )
    if model._participation is not None:
        settings.add(
            "limit_participation",
            volumes=model._participation[0],
            maximum_rate=model._participation[1],
        )
    settings.add(
        "set_market_impact",
        quadratic=model._quadratic,
        power_3_2=model._power,
        curves=model._curves,
    )
    if model._venue_limits is not None:
        settings.add("limit_venue_notional", maximum=model._venue_limits)
    if model._gross_limit is not None:
        settings.add("limit_gross_notional", maximum=model._gross_limit)
    if model._turnover_limit is not None:
        settings.add("limit_turnover", maximum=model._turnover_limit)
    for ids, values, low, high, units in model._exposures:
        settings.add(
            "limit_exposures",
            coefficients=values,
            lower=low,
            upper=high,
            risk_units=units,
            exposure_ids=ids,
        )
    if model._risk is not None:
        settings.add(
            "set_price_risk",
            covariance_rate=model._risk,
            risk_aversion=model._risk_aversion,
        )
    return inputs, settings


# Loading can configure financial models, but never execute jobs or code.
def _trading(model):
    inputs = dict(
        prices=model._prices,
        tree=model.tree,
        holdings=model._opening,
        cash=model._cash,
        currency=model.currency,
        buy_limits=model._buy,
        sell_limits=model._sell,
        cash_settlement=model._settlement,
        asset_ids=model.asset_ids,
        credit_limits=model._credit,
        borrow_limits=model._borrow,
    )
    settings = _Configuration()
    for key, source in model._funding.items():
        settings.add("add_funding", funding_id=key, **source)
    for key, source in model._existing_debt.items():
        settings.add("add_existing_debt", debt_id=key, **source)
    for key, arguments in facility_configuration(
        model._facilities, model._nodes
    ):
        settings.add("limit_facility", facility_id=key, **arguments)
    if model._debt_limits is not None:
        settings.add("limit_debt", maximum=model._debt_limits)
    settings.add(
        "set_trading_costs",
        bid_prices=model._bid,
        ask_prices=model._ask,
        buy_per_unit=model._buy_fees,
        sell_per_unit=model._sell_fees,
        fixed=model._fixed,
        minimum_trade=model._minimum,
    )
    settings.add("trade_in_lots", lot_sizes=model._lots)
    settings.add("set_cash_flows", flows=model._flows)
    if len(model._nodes) > 1:
        settings.add(
            "set_carry",
            deposit_factors=model._deposit[1:],
            borrowing_factors=model._borrowing[1:],
            dividends=model._dividends[1:],
            share_factors=model._splits[1:],
            short_fees=model._short_fees[1:],
        )
    for method, limits, names in (
        ("limit_cash", model._cash_limits, ("minimum", "maximum")),
        ("limit_positions", model._position_limits, ("lower", "upper")),
    ):
        if limits is not None:
            settings.add(
                method, **dict(zip(names, map(_optional_bound, limits)))
            )
    for method, values in (
        ("limit_turnover", model._turnover),
        ("limit_gross_notional", model._gross),
        ("limit_terminal_wealth", model._terminal_minimum),
    ):
        if values is not None:
            settings.add(
                method,
                **{
                    "minimum"
                    if method == "limit_terminal_wealth"
                    else "maximum": values
                },
            )
    if model._participation is not None:
        settings.add(
            "limit_participation",
            volumes=model._participation[0],
            maximum_rate=model._participation[1],
        )
    for ids, coefficients, low, high, units in model._exposures:
        settings.add(
            "limit_exposures",
            coefficients=coefficients,
            lower=low,
            upper=high,
            risk_units=units,
            exposure_ids=ids,
        )
    if model._tail_limit is not None:
        maximum, target, level = model._tail_limit
        settings.add(
            "limit_expected_shortfall",
            maximum=maximum,
            target=target,
            confidence=level,
        )
    if (
        np.any(model._impact_quadratic > 0)
        or np.any(model._impact_power > 0)
        or model._impact_curves
    ):
        from .trading._planning_impact import curve_table

        settings.add(
            "set_market_impact",
            quadratic=model._impact_quadratic,
            power_3_2=model._impact_power,
            curves=curve_table(model),
        )
    if model._target is not None:
        settings.add(
            "minimize_expected_shortfall",
            target=model._target,
            confidence=model._confidence,
        )
    if model._objective == "expected_wealth":
        settings.add("maximize_expected_wealth")
    elif model._objective == "worst_case_wealth":
        settings.add("maximize_worst_case_wealth")
    return inputs, settings


MODELS = {
    "TradingModel": (
        TradingModel,
        _trading,
        frozenset(
            {
                "add_funding",
                "add_existing_debt",
                "limit_debt",
                "limit_facility",
                "set_trading_costs",
                "set_market_impact",
                "trade_in_lots",
                "set_cash_flows",
                "set_carry",
                "set_credit_limits",
                "set_borrow_limits",
                "limit_cash",
                "limit_positions",
                "limit_turnover",
                "limit_gross_notional",
                "limit_exposures",
                "limit_participation",
                "limit_terminal_wealth",
                "limit_expected_shortfall",
                "maximize_expected_wealth",
                "maximize_worst_case_wealth",
                "minimize_expected_shortfall",
            }
        ),
    ),
    "ExecutionModel": (
        ExecutionModel,
        _execution,
        frozenset(
            {
                "set_execution_costs",
                "trade_in_lots",
                "set_market_impact",
                "allow_underfill",
                "require_completion",
                "set_order_windows",
                "set_cash_flows",
                "set_credit_limits",
                "limit_cash",
                "set_borrow_limits",
                "limit_positions",
                "limit_participation",
                "limit_venue_notional",
                "limit_gross_notional",
                "limit_turnover",
                "limit_exposures",
                "set_price_risk",
            }
        ),
    ),
    "PortfolioModel": (
        PortfolioModel,
        _portfolio,
        frozenset(
            {
                "limit_weights",
                "limit_cash",
                "set_trading_costs",
                "set_tax_lots",
                "limit_tax",
                "trade_in_lots",
                "limit_short_positions",
                "limit_exposures",
                "require_return",
                "limit_leverage",
                "limit_volatility",
                "limit_turnover",
                "robust_returns",
                "select_assets",
                "fix_selection",
                "minimize_variance",
                "maximize_utility",
                "minimize_tracking_error",
                "allocate_risk",
                "hierarchical_risk_parity",
                "minimize_expected_shortfall",
                "minimize_mean_absolute_deviation",
                "minimize_downside_risk",
                "maximize_moment_utility",
            }
        ),
    ),
    "FundingModel": (
        FundingModel,
        _funding,
        frozenset(
            {
                "minimize_expected_cost",
                "minimize_expected_shortfall",
                "limit_expected_shortfall",
                "minimize_worst_case_cost",
                "limit_exposure",
                "limit_cash",
                "limit_debt",
                "limit_facility",
                "add_investment",
                "add_funding",
                "add_existing_debt",
                "add_transfer",
            }
        ),
    ),
    "LiabilityMatchingModel": (
        LiabilityMatchingModel,
        _matching,
        frozenset(
            {
                "limit_holdings",
                "limit_cash",
                "limit_initial_capital",
                "buy_in_lots",
                "match_sensitivities",
            }
        ),
    ),
    "HedgeModel": (
        HedgeModel,
        _hedging,
        frozenset(
            {
                "limit_trades",
                "limit_positions",
                "set_transaction_costs",
                "limit_exposures",
                "set_cash_account",
                "limit_capital",
                "trade_in_lots",
                "minimize_mismatch",
                "match_exposures",
                "set_pnl_scenarios",
                "limit_scenario_loss",
                "limit_expected_shortfall",
                "minimize_expected_shortfall",
                "minimize_worst_case_loss",
            }
        ),
    ),
    "CreditAllocationModel": (
        CreditAllocationModel,
        _credit,
        frozenset(
            {
                "limit_allocations",
                "set_transaction_costs",
                "set_default_risk",
                "limit_funding",
                "limit_capital",
                "allocate_in_lots",
                "select_facilities",
                "limit_exposures",
                "limit_concentration",
                "set_loss_scenarios",
                "limit_scenario_loss",
                "limit_expected_shortfall",
                "maximize_risk_adjusted_income",
            }
        ),
    ),
    "CollateralAllocationModel": (
        CollateralAllocationModel,
        _collateral,
        frozenset(
            {
                "set_availability",
                "limit_assignments",
                "set_prices",
                "set_haircuts",
                "set_fx_rates",
                "pledge_in_lots",
                "limit_coverage",
                "limit_movements",
                "limit_concentration",
            }
        ),
    ),
    "ReinsuranceModel": (
        ReinsuranceModel,
        _reinsurance,
        frozenset(
            {
                "set_recoverability",
                "set_contingent_costs",
                "limit_selections",
                "limit_contract_count",
                "add_exclusive_group",
                "limit_premium",
                "limit_retained_loss",
                "limit_total_cost",
                "limit_expected_shortfall",
                "limit_counterparty_exposure",
                "set_surplus_before_claims",
                "require_surplus",
                "minimize_premium",
                "minimize_expected_cost",
                "minimize_expected_shortfall",
            }
        ),
    ),
    "SettlementModel": (
        SettlementModel,
        _settlement,
        frozenset(
            {
                "set_external_flows",
                "set_credit_limits",
                "allow_prefunding",
                "set_credit_costs",
                "limit_final_balances",
                "add_atomic_batch",
                "add_precedence",
                "require_payments",
            }
        ),
    ),
}
