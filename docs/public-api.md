# Public Python API

Use the domain namespace that owns the financial operation. The references below define constructors, parameters, units, results, and failure behavior. Root-level imports contain only the common financial workflow operations.

```python
from qpiai_finance import inspect, solve, validate
from qpiai_finance.portfolio import PortfolioModel
from qpiai_finance.quantum import compile_portfolio
```

Gate-based algorithms and execution settings are imported from `qpiai_opt.quantum`. Finance-specific compilation and source mappings live in `qpiai_finance.quantum`. Private modules whose names begin with an underscore are implementation details.

## Common workflow

Import from `qpiai_finance`.

| Export | Reference |
| --- | --- |
| `solve` | [Common workflow](solving.md) |
| `inspect` | [Common workflow](solving.md) |
| `validate` | [Common workflow](solving.md) |

## Portfolios

Import from `qpiai_finance.portfolio`.

| Export | Reference |
| --- | --- |
| `PortfolioModel` | [Portfolios](portfolio.md) |
| `FrontierResult` | [Portfolios](portfolio.md) |

### `PortfolioModel` members

```text
PortfolioModel(expected_returns=None, covariance=None, *, horizon, asset_ids=None, net_weight=1.0, holdings=None, prices=None, cash=None, currency=None, bid_prices=None, ask_prices=None, cash_return=0.0)
```

| Method | Signature |
| --- | --- |
| `allocate_risk` | `allocate_risk(budgets=None, *, polish=True, polish_maxiter=20)` |
| `efficient_frontier` | `efficient_frontier(target_returns, *, client=None, solver=None, mode='local', allow_platform=False, tolerance=1e-07, **options)` |
| `evaluate` | `evaluate(weights, *, tax_lot_sales=None, tolerance=1e-07)` |
| `fix_selection` | `fix_selection(selected)` |
| `hierarchical_risk_parity` | `hierarchical_risk_parity(*, linkage_method='single')` |
| `limit_cash` | `limit_cash(*, minimum=0.0, maximum=None)` |
| `limit_exposures` | `limit_exposures(exposures, *, lower, upper, exposure_ids=None)` |
| `limit_leverage` | `limit_leverage(*, maximum)` |
| `limit_short_positions` | `limit_short_positions(maximum)` |
| `limit_tax` | `limit_tax(*, minimum=None, maximum=None)` |
| `limit_turnover` | `limit_turnover(current_weights=None, *, maximum)` |
| `limit_volatility` | `limit_volatility(*, maximum)` |
| `limit_weights` | `limit_weights(*, lower=0.0, upper=1.0)` |
| `maximize_moment_utility` | `maximize_moment_utility(scenarios, *, variance_aversion, skewness_preference=0.0, kurtosis_aversion=0.0)` |
| `maximize_utility` | `maximize_utility(*, risk_aversion)` |
| `minimize_downside_risk` | `minimize_downside_risk(scenarios, *, target=0.0)` |
| `minimize_expected_shortfall` | `minimize_expected_shortfall(scenarios, *, confidence=0.95)` |
| `minimize_mean_absolute_deviation` | `minimize_mean_absolute_deviation(scenarios)` |
| `minimize_tracking_error` | `minimize_tracking_error(*, benchmark)` |
| `minimize_variance` | `minimize_variance()` |
| `require_return` | `require_return(*, minimum)` |
| `robust_returns` | `robust_returns(uncertainty, *, radius, uncertainty_ids=None)` |
| `select_assets` | `select_assets(*, count=None, maximum=None, minimum_weight=0.0, equal_weight=False)` |
| `set_tax_lots` | `set_tax_lots(lots, *, as_of, settlement)` |
| `set_trading_costs` | `set_trading_costs(*, buy_bps=0.0, sell_bps=0.0, buy_fixed=0.0, sell_fixed=0.0, minimum_trade=0.0)` |
| `to_cvxpy` | `to_cvxpy()` |
| `to_model` | `to_model(*, return_variables=False)` |
| `trade_in_lots` | `trade_in_lots(lot_sizes)` |

Properties: `asset_ids`, `expected_returns`, `horizon`, `tax_lots`.

### `FrontierResult` members

```text
FrontierResult(targets: pandas.Series, results: tuple[qpiai_finance.results.FinanceResult, ...], horizon: str) -> None
```

| Method | Signature |
| --- | --- |
| `to_dict` | `to_dict()` |
| `to_json` | `to_json()` |

Properties: `table`.

Record fields: `targets`, `results`, `horizon`.

## Quantum-inspired and gate-based optimization

Import from `qpiai_finance.quantum`.

| Export | Reference |
| --- | --- |
| `compile_portfolio` | [Quantum-inspired and gate-based optimization](quantum.md) |
| `PortfolioEncoding` | [Quantum-inspired and gate-based optimization](quantum.md) |

### `PortfolioEncoding` members

```text
PortfolioEncoding(portfolio, problem, names, objective, violations, details, conversion, build_time)
```

| Method | Signature |
| --- | --- |
| `decode` | `decode(sample)` |
| `decode_result` | `decode_result(result, *, tolerance=1e-07)` |
| `encode_selection` | `encode_selection(selected)` |
| `energy` | `energy(sample)` |
| `evaluate` | `evaluate(sample, *, tolerance=1e-07)` |
| `evaluate_samples` | `evaluate_samples(samples, *, tolerance=1e-07)` |
| `inspect` | `inspect(*, algorithm=None)` |
| `solve` | `solve(*, client=None, mode='local', algorithm=None, execution=None, allow_platform=False, tolerance=1e-07, **options)` |

Properties: `compilation_settings`, `objective_polynomial`, `problem`, `transformations`, `variable_mapping`, `variable_names`.

## Investment planning and execution

Import from `qpiai_finance.trading`.

| Export | Reference |
| --- | --- |
| `ExecutionModel` | [Investment planning and execution](execution.md) |
| `TradingModel` | [Investment planning and execution](trading.md) |

### `ExecutionModel` members

```text
ExecutionModel(orders, opportunities, *, arrival_prices, holdings, cash, currency, as_of, slots, cash_settlement, asset_ids=None, slot_ids=None, credit_limit=0.0, borrow_limits=0.0)
```

| Method | Signature |
| --- | --- |
| `allow_underfill` | `allow_underfill(penalty)` |
| `evaluate` | `evaluate(executions, *, tolerance=1e-07)` |
| `limit_cash` | `limit_cash(minimum)` |
| `limit_exposures` | `limit_exposures(coefficients, *, lower, upper, risk_units, exposure_ids=None)` |
| `limit_gross_notional` | `limit_gross_notional(maximum)` |
| `limit_participation` | `limit_participation(volumes, *, maximum_rate)` |
| `limit_positions` | `limit_positions(*, lower=None, upper=None)` |
| `limit_turnover` | `limit_turnover(maximum)` |
| `limit_venue_notional` | `limit_venue_notional(maximum)` |
| `require_completion` | `require_completion(asset_ids=None)` |
| `set_borrow_limits` | `set_borrow_limits(maximum)` |
| `set_cash_flows` | `set_cash_flows(flows)` |
| `set_credit_limits` | `set_credit_limits(maximum)` |
| `set_execution_costs` | `set_execution_costs(*, per_unit=0.0, fixed=0.0, minimum_trade=0.0)` |
| `set_market_impact` | `set_market_impact(*, quadratic=0.0, power_3_2=0.0, curves=None)` |
| `set_order_windows` | `set_order_windows(*, release=None, deadline=None)` |
| `set_price_risk` | `set_price_risk(covariance_rate, *, risk_aversion)` |
| `to_cvxpy` | `to_cvxpy()` |
| `to_matrix` | `to_matrix()` |
| `to_model` | `to_model(*, return_variables=False)` |
| `trade_in_lots` | `trade_in_lots(lot_sizes)` |

Properties: `asset_ids`, `currency`, `opportunity_ids`, `slot_ids`, `slot_times`, `venue_ids`.

### `TradingModel` members

```text
TradingModel(prices, *, tree, holdings, cash, currency, buy_limits, sell_limits, cash_settlement, asset_ids=None, credit_limits=0.0, borrow_limits=0.0)
```

| Method | Signature |
| --- | --- |
| `add_existing_debt` | `add_existing_debt(debt_id, *, principal, repayment_stage, interest=0.0)` |
| `add_funding` | `add_funding(funding_id, *, draw_node, repayment_stage, maximum, interest=0.0, fee=0.0, fixed_fee=0.0, minimum=0.0, lot_size=None)` |
| `evaluate` | `evaluate(trades, *, draws=None, tolerance=1e-07)` |
| `limit_cash` | `limit_cash(*, minimum=None, maximum=None)` |
| `limit_debt` | `limit_debt(*, maximum)` |
| `limit_expected_shortfall` | `limit_expected_shortfall(maximum, *, target, confidence=0.95)` |
| `limit_exposures` | `limit_exposures(coefficients, *, lower, upper, risk_units, exposure_ids=None)` |
| `limit_facility` | `limit_facility(facility_id, funding_ids, *, maximum, currency, fx_rates=None, reserved=0.0)` |
| `limit_gross_notional` | `limit_gross_notional(maximum)` |
| `limit_participation` | `limit_participation(volumes, *, maximum_rate)` |
| `limit_positions` | `limit_positions(*, lower=None, upper=None)` |
| `limit_terminal_wealth` | `limit_terminal_wealth(minimum)` |
| `limit_turnover` | `limit_turnover(maximum)` |
| `maximize_expected_wealth` | `maximize_expected_wealth()` |
| `maximize_worst_case_wealth` | `maximize_worst_case_wealth()` |
| `minimize_expected_shortfall` | `minimize_expected_shortfall(*, target, confidence=0.95)` |
| `set_borrow_limits` | `set_borrow_limits(maximum)` |
| `set_carry` | `set_carry(*, deposit_factors=1.0, borrowing_factors=1.0, dividends=0.0, share_factors=1.0, short_fees=0.0)` |
| `set_cash_flows` | `set_cash_flows(flows)` |
| `set_credit_limits` | `set_credit_limits(maximum)` |
| `set_market_impact` | `set_market_impact(*, quadratic=0.0, power_3_2=0.0, curves=None)` |
| `set_trading_costs` | `set_trading_costs(*, bid_prices=None, ask_prices=None, buy_per_unit=0.0, sell_per_unit=0.0, fixed=0.0, minimum_trade=0.0)` |
| `to_cvxpy` | `to_cvxpy()` |
| `to_matrix` | `to_matrix()` |
| `to_model` | `to_model(*, return_variables=False)` |
| `to_scip` | `to_scip()` |
| `trade_in_lots` | `trade_in_lots(lot_sizes)` |

Properties: `asset_ids`, `currency`, `node_ids`, `tree`.

## Hedging

Import from `qpiai_finance.hedging`.

| Export | Reference |
| --- | --- |
| `HedgeModel` | [Hedging](hedging.md) |

### `HedgeModel` members

```text
HedgeModel(current_exposures=None, sensitivities=None, *, risk_units=None, currency, as_of, instrument_ids=None, risk_ids=None, current_positions=0.0, current_pnl=None, pnl_scenarios=None, cost_factors=None)
```

| Method | Signature |
| --- | --- |
| `evaluate` | `evaluate(hedges, *, tolerance=1e-07)` |
| `limit_capital` | `limit_capital(capital_per_unit, *, maximum)` |
| `limit_expected_shortfall` | `limit_expected_shortfall(maximum, *, confidence=0.95)` |
| `limit_exposures` | `limit_exposures(*, lower, upper)` |
| `limit_positions` | `limit_positions(*, lower=None, upper=None)` |
| `limit_scenario_loss` | `limit_scenario_loss(maximum)` |
| `limit_trades` | `limit_trades(*, lower=None, upper=None)` |
| `match_exposures` | `match_exposures(target=0.0)` |
| `minimize_expected_shortfall` | `minimize_expected_shortfall(*, confidence=0.95)` |
| `minimize_mismatch` | `minimize_mismatch(weights, *, target=0.0, cost_weight=1.0)` |
| `minimize_worst_case_loss` | `minimize_worst_case_loss()` |
| `set_cash_account` | `set_cash_account(*, cash, prices, bid_prices=None, ask_prices=None)` |
| `set_pnl_scenarios` | `set_pnl_scenarios(scenarios, *, current_pnl, cost_factors=1.0)` |
| `set_transaction_costs` | `set_transaction_costs(*, buy=0.0, sell=0.0)` |
| `to_cvxpy` | `to_cvxpy()` |
| `to_model` | `to_model(*, return_variables=False)` |
| `trade_in_lots` | `trade_in_lots(lot_sizes)` |

Properties: `currency`, `current_pnl`, `instrument_ids`, `pnl_scenarios`, `risk_ids`.

## Credit allocation

Import from `qpiai_finance.credit`.

| Export | Reference |
| --- | --- |
| `CreditAllocationModel` | [Credit allocation](credit.md) |

### `CreditAllocationModel` members

```text
CreditAllocationModel(income_rates, *, funding_costs, expected_loss_rates, capital_requirements, capacity, currency, horizon, as_of, facility_ids=None, funding_requirements=1.0, exposure_per_unit=1.0, current_allocations=0.0)
```

| Method | Signature |
| --- | --- |
| `allocate_in_lots` | `allocate_in_lots(lot_sizes)` |
| `evaluate` | `evaluate(allocations, *, tolerance=1e-07)` |
| `limit_allocations` | `limit_allocations(*, lower=0.0, upper=None)` |
| `limit_capital` | `limit_capital(maximum)` |
| `limit_concentration` | `limit_concentration(groups, *, maximum_share)` |
| `limit_expected_shortfall` | `limit_expected_shortfall(maximum, *, confidence=0.95)` |
| `limit_exposures` | `limit_exposures(coefficients, *, upper, lower=0.0, exposure_ids=None)` |
| `limit_funding` | `limit_funding(maximum)` |
| `limit_scenario_loss` | `limit_scenario_loss(maximum)` |
| `maximize_risk_adjusted_income` | `maximize_risk_adjusted_income(*, capital_charge=0.0, risk_aversion=0.0, confidence=0.95)` |
| `select_facilities` | `select_facilities(*, minimum, maximum_count=None)` |
| `set_default_risk` | `set_default_risk(probability_of_default, loss_given_default, exposure_at_default)` |
| `set_loss_scenarios` | `set_loss_scenarios(scenarios)` |
| `set_transaction_costs` | `set_transaction_costs(*, increase=0.0, decrease=0.0)` |
| `to_cvxpy` | `to_cvxpy()` |
| `to_model` | `to_model(*, return_variables=False)` |

Properties: `currency`, `facility_ids`.

## Funding and liability matching

Import from `qpiai_finance.treasury`.

| Export | Reference |
| --- | --- |
| `FundingModel` | [Funding and liability matching](funding.md) |
| `LiabilityMatchingModel` | [Funding and liability matching](liability-matching.md) |

### `FundingModel` members

```text
FundingModel(cash_flows, *, balances, as_of, dates=None, tree=None, reporting_currency=None, fx_rates=None, deposit_returns=0.0, discount_factors=1.0)
```

| Method | Signature |
| --- | --- |
| `add_existing_debt` | `add_existing_debt(debt_id, *, account, principal, repayment_date=None, repayment_stage=None, interest=0.0)` |
| `add_funding` | `add_funding(funding_id, *, account, draw_date=None, repayment_date=None, draw_node=None, repayment_stage=None, maximum, interest=0.0, fee=0.0, fixed_fee=0.0, minimum=0.0, lot_size=None)` |
| `add_investment` | `add_investment(investment_id, *, account, price, cash_flows, upper, lower=0.0, lot_size=None, purchase_date=None, purchase_node=None)` |
| `add_transfer` | `add_transfer(transfer_id, *, from_account, to_account, date=None, node=None, maximum, exchange_rate=None, fee=0.0)` |
| `evaluate` | `evaluate(draws=None, transfers=None, *, investments=None, tolerance=1e-07)` |
| `limit_cash` | `limit_cash(*, minimum=0.0, maximum=None)` |
| `limit_debt` | `limit_debt(*, maximum)` |
| `limit_expected_shortfall` | `limit_expected_shortfall(maximum, *, confidence=0.95)` |
| `limit_exposure` | `limit_exposure(exposure_id, *, unit, investment_coefficients=None, funding_coefficients=None, cash_coefficients=None, external_exposure=0.0, lower=None, upper=None)` |
| `limit_facility` | `limit_facility(facility_id, funding_ids, *, maximum, currency, fx_rates=None, reserved=0.0)` |
| `minimize_expected_cost` | `minimize_expected_cost()` |
| `minimize_expected_shortfall` | `minimize_expected_shortfall(*, confidence=0.95)` |
| `minimize_worst_case_cost` | `minimize_worst_case_cost()` |
| `to_cvxpy` | `to_cvxpy()` |
| `to_model` | `to_model(*, return_variables=False)` |

Properties: `account_ids`, `dates`, `funding_ids`, `investment_ids`, `node_ids`, `reporting_currency`, `tree`.

### `LiabilityMatchingModel` members

```text
LiabilityMatchingModel(prices, cash_flows, liabilities, *, currency, as_of, dates, asset_ids=None, deposit_returns=0.0)
```

| Method | Signature |
| --- | --- |
| `buy_in_lots` | `buy_in_lots(lot_sizes)` |
| `evaluate` | `evaluate(holdings, *, initial_capital, tolerance=1e-07)` |
| `limit_cash` | `limit_cash(*, minimum=0.0, maximum=None)` |
| `limit_holdings` | `limit_holdings(*, lower=0.0, upper=None)` |
| `limit_initial_capital` | `limit_initial_capital(*, maximum)` |
| `match_sensitivities` | `match_sensitivities(sensitivities, target, *, risk_units, risk_ids=None)` |
| `to_cvxpy` | `to_cvxpy()` |
| `to_matrix` | `to_matrix()` |
| `to_model` | `to_model(*, return_variables=False)` |

Properties: `asset_ids`, `currency`, `dates`.

## Reinsurance

Import from `qpiai_finance.insurance`.

| Export | Reference |
| --- | --- |
| `ReinsuranceModel` | [Reinsurance](insurance.md) |
| `excess_of_loss` | [Reinsurance](insurance.md) |
| `quota_share` | [Reinsurance](insurance.md) |

### `ReinsuranceModel` members

```text
ReinsuranceModel(gross_losses, recoveries, premiums, *, recovery_composition, currency, horizon, as_of, probabilities=None, scenario_ids=None, contract_ids=None)
```

| Method | Signature |
| --- | --- |
| `add_exclusive_group` | `add_exclusive_group(contract_ids)` |
| `evaluate` | `evaluate(selections, *, tolerance=1e-07)` |
| `limit_contract_count` | `limit_contract_count(*, minimum=0, maximum=None)` |
| `limit_counterparty_exposure` | `limit_counterparty_exposure(coefficients, *, maximum, exposure_ids=None)` |
| `limit_expected_shortfall` | `limit_expected_shortfall(maximum, *, confidence=0.95, measure='total_cost')` |
| `limit_premium` | `limit_premium(maximum)` |
| `limit_retained_loss` | `limit_retained_loss(maximum)` |
| `limit_selections` | `limit_selections(*, lower=0.0, upper=1.0)` |
| `limit_total_cost` | `limit_total_cost(maximum)` |
| `minimize_expected_cost` | `minimize_expected_cost(*, tail_weight=0.0, confidence=0.95)` |
| `minimize_expected_shortfall` | `minimize_expected_shortfall(*, confidence=0.95)` |
| `minimize_premium` | `minimize_premium()` |
| `require_surplus` | `require_surplus(minimum=0.0)` |
| `set_contingent_costs` | `set_contingent_costs(costs)` |
| `set_recoverability` | `set_recoverability(factors)` |
| `set_surplus_before_claims` | `set_surplus_before_claims(surplus)` |
| `to_cvxpy` | `to_cvxpy()` |
| `to_matrix` | `to_matrix()` |
| `to_model` | `to_model(*, return_variables=False)` |

Properties: `contract_ids`, `currency`, `scenario_ids`.

## Collateral

Import from `qpiai_finance.collateral`.

| Export | Reference |
| --- | --- |
| `CollateralAllocationModel` | [Collateral](collateral.md) |
| `haircut_adjusted_value` | [Collateral](collateral.md) |

### `CollateralAllocationModel` members

```text
CollateralAllocationModel(inventory, requirements, pledges, *, as_of, dates, reporting_currency)
```

| Method | Signature |
| --- | --- |
| `evaluate` | `evaluate(assignments, *, tolerance=1e-07)` |
| `limit_assignments` | `limit_assignments(*, lower=0.0, upper=None)` |
| `limit_concentration` | `limit_concentration(groups, *, maximum_share)` |
| `limit_coverage` | `limit_coverage(maximum)` |
| `limit_movements` | `limit_movements(*, pledged=None, returned=None)` |
| `pledge_in_lots` | `pledge_in_lots(lot_sizes)` |
| `set_availability` | `set_availability(quantities)` |
| `set_fx_rates` | `set_fx_rates(fx_rates)` |
| `set_haircuts` | `set_haircuts(haircuts)` |
| `set_prices` | `set_prices(prices)` |
| `to_cvxpy` | `to_cvxpy()` |
| `to_matrix` | `to_matrix()` |
| `to_model` | `to_model(*, return_variables=False)` |

Properties: `asset_ids`, `dates`, `pledge_ids`, `reporting_currency`.

## Settlement

Import from `qpiai_finance.settlement`.

| Export | Reference |
| --- | --- |
| `SettlementModel` | [Settlement](settlement.md) |

### `SettlementModel` members

```text
SettlementModel(accounts, payments, *, as_of, slots, reporting_currency, settlement_method='rtgs', slot_ids=None)
```

| Method | Signature |
| --- | --- |
| `add_atomic_batch` | `add_atomic_batch(batch_id, payment_ids)` |
| `add_precedence` | `add_precedence(before, after, *, allow_same_batch=False)` |
| `allow_prefunding` | `allow_prefunding(maximum, *, cost_per_unit)` |
| `evaluate` | `evaluate(schedule, *, prefunding=0.0, tolerance=1e-07)` |
| `limit_final_balances` | `limit_final_balances(lower=0.0)` |
| `require_payments` | `require_payments(payment_ids)` |
| `set_credit_costs` | `set_credit_costs(cost_per_unit)` |
| `set_credit_limits` | `set_credit_limits(limits)` |
| `set_external_flows` | `set_external_flows(flows)` |
| `to_cvxpy` | `to_cvxpy()` |
| `to_matrix` | `to_matrix()` |
| `to_model` | `to_model(*, return_variables=False)` |

Properties: `account_ids`, `execution_units`, `payment_ids`, `slot_ids`, `slot_times`.

## Financial data

Import from `qpiai_finance.data`.

| Export | Reference |
| --- | --- |
| `returns_from_prices` | [Financial data](data.md) |
| `compound_returns` | [Financial data](data.md) |
| `rescale_moments` | [Financial data](data.md) |
| `history_as_of` | [Financial data](data.md) |

## Risk analytics

Import from `qpiai_finance.risk`.

| Export | Reference |
| --- | --- |
| `value_at_risk` | [Risk analytics](risk.md) |
| `expected_shortfall` | [Risk analytics](risk.md) |
| `expected_shortfall_epigraph` | [Risk analytics](risk.md) |
| `sample_moments` | [Risk analytics](risk.md) |
| `exponential_moments` | [Risk analytics](risk.md) |
| `shrink_covariance` | [Risk analytics](risk.md) |
| `portfolio_metrics` | [Risk analytics](risk.md) |
| `risk_contributions` | [Risk analytics](risk.md) |
| `FactorRisk` | [Risk analytics](risk.md) |
| `black_litterman` | [Risk analytics](risk.md) |

### `FactorRisk` members

```text
FactorRisk(exposures, factor_covariance, specific_variance, *, asset_ids=None, factor_ids=None)
```

| Method | Signature |
| --- | --- |
| `apply` | `apply(weights)` |
| `factor_exposures` | `factor_exposures(weights)` |
| `risk_contributions` | `risk_contributions(weights)` |

Properties: `asset_ids`.

## Scenarios

Import from `qpiai_finance.scenarios`.

| Export | Reference |
| --- | --- |
| `Scenarios` | [Scenarios](scenarios.md) |
| `ScenarioPaths` | [Scenarios](scenarios.md) |
| `ScenarioTree` | [Scenarios](scenarios.md) |

### `Scenarios` members

```text
Scenarios(values, *, horizon, unit, probabilities=None, asset_ids=None, scenario_ids=None, origin=None, metadata=None)
```

| Method | Signature |
| --- | --- |
| `evaluate` | `evaluate(quantities)` |
| `expected` | `expected(quantities)` |

Properties: `asset_ids`, `metadata`, `probabilities`, `scenario_ids`, `values`.

Attributes: `horizon`, `origin`, `unit`.

### `ScenarioPaths` members

```text
ScenarioPaths(values, *, horizon, step_horizon, unit, probabilities=None, asset_ids=None, scenario_ids=None, step_ids=None, origin=None, metadata=None)
```

| Method | Signature |
| --- | --- |
| `aggregate` | `aggregate(*, method)` |
| `bootstrap` | `bootstrap(observations, *, as_of, periods, samples, step_horizon, horizon, unit, method, seed, block_size=None, observed_at=None, available_at=None, asset_ids=None, scenario_ids=None, step_ids=None)` |
| `evaluate` | `evaluate(quantities)` |
| `expected` | `expected(quantities)` |
| `historical` | `historical(observations, *, as_of, periods, step_horizon, horizon, unit, probabilities, stride=1, observed_at=None, available_at=None, asset_ids=None, scenario_ids=None, step_ids=None)` |

Properties: `asset_ids`, `metadata`, `probabilities`, `scenario_ids`, `step_ids`, `values`.

Attributes: `horizon`, `origin`, `step_horizon`, `unit`.

### `ScenarioTree` members

```text
ScenarioTree(information, *, times=None, probabilities=None, scenario_ids=None, stage_ids=None, origin=None, metadata=None)
```

| Method | Signature |
| --- | --- |
| `ancestors` | `ancestors(node)` |
| `children` | `children(node)` |
| `expected` | `expected(values, *, given=None)` |
| `paths` | `paths(values, *, horizon, step_horizon, unit, asset_ids=None)` |
| `validate_policy` | `validate_policy(decisions, *, timing='after_observation', tolerance=1e-07)` |

Properties: `information`, `metadata`, `node_ids`, `nodes`, `probabilities`, `root`, `scenario_ids`, `stage_ids`, `times`.

Attributes: `origin`.

## Cash-flow calculations

Import from `qpiai_finance.cashflows`.

| Export | Reference |
| --- | --- |
| `bullet_loan_cash_flows` | [Cash-flow calculations](cashflows.md) |
| `discount_cash_flows` | [Cash-flow calculations](cashflows.md) |
| `present_value` | [Cash-flow calculations](cashflows.md) |

## Trading costs

Import from `qpiai_finance.trading.costs`.

| Export | Reference |
| --- | --- |
| `transaction_fees` | [Trading costs](trading-costs.md) |
| `market_impact_cost` | [Trading costs](trading-costs.md) |

## Results and recovery

Import from `qpiai_finance.results`.

| Export | Reference |
| --- | --- |
| `FinanceResult` | [Results and recovery](results.md) |
| `from_opt` | [Results and recovery](results.md) |

### `FinanceResult` members

```text
FinanceResult(status: str, feasible: bool, optimality_proven: bool, decision: dict[str, pandas.Series | pandas.DataFrame], objective: float | None, objective_unit: str | None, metrics: dict, constraints: pandas.DataFrame, solver_info: dict, provenance: dict, tables: dict[str, pandas.DataFrame] = <factory>, transformations: list[dict] = <factory>, costs: dict = <factory>) -> None
```

| Method | Signature |
| --- | --- |
| `evaluate` | `evaluate(model, *, tolerance=1e-07)` |
| `to_dict` | `to_dict()` |
| `to_json` | `to_json()` |

Properties: `allocation_changes`, `allocations`, `assignments`, `cash_after`, `cash_balances`, `draws`, `executions`, `hedges`, `holdings`, `investments`, `peak_credit`, `positions`, `post_trade_weights`, `prefunding`, `remaining_orders`, `risk_exposures`, `selections`, `settlement_schedule`, `tax_lot_sales`, `trades`, `transfers`, `unfilled`, `weights`.

Record fields: `status`, `feasible`, `optimality_proven`, `decision`, `objective`, `objective_unit`, `metrics`, `constraints`, `solver_info`, `provenance`, `tables`, `transformations`, `costs`.

## Interchange

Import from `qpiai_finance.io`.

| Export | Reference |
| --- | --- |
| `to_dict` | [Interchange](interchange.md) |
| `from_dict` | [Interchange](interchange.md) |
| `dumps` | [Interchange](interchange.md) |
| `loads` | [Interchange](interchange.md) |
| `dump` | [Interchange](interchange.md) |
| `load` | [Interchange](interchange.md) |

## Plotting

Import from `qpiai_finance.plot`.

| Export | Reference |
| --- | --- |
| `weights` | [Plotting](plotting.md) |
| `holdings` | [Plotting](plotting.md) |
| `trades` | [Plotting](plotting.md) |
| `risk_contributions` | [Plotting](plotting.md) |
| `loss_distribution` | [Plotting](plotting.md) |
| `risk_budgets` | [Plotting](plotting.md) |
| `efficient_frontier` | [Plotting](plotting.md) |
| `cash_ladder` | [Plotting](plotting.md) |
| `funding_schedule` | [Plotting](plotting.md) |
| `facility_utilization` | [Plotting](plotting.md) |
| `liability_coverage` | [Plotting](plotting.md) |
| `hedge_exposure` | [Plotting](plotting.md) |
| `hedge_losses` | [Plotting](plotting.md) |
| `allocations` | [Plotting](plotting.md) |
| `credit_resources` | [Plotting](plotting.md) |
| `credit_concentration` | [Plotting](plotting.md) |
| `collateral_coverage` | [Plotting](plotting.md) |
| `collateral_inventory` | [Plotting](plotting.md) |
| `reinsurance_losses` | [Plotting](plotting.md) |
| `reinsurance_surplus` | [Plotting](plotting.md) |
| `settlement_balances` | [Plotting](plotting.md) |
| `payment_queue` | [Plotting](plotting.md) |
| `execution_schedule` | [Plotting](plotting.md) |
| `execution_costs` | [Plotting](plotting.md) |
| `execution_balances` | [Plotting](plotting.md) |
| `tax_lot_sales` | [Plotting](plotting.md) |
| `tax_liability` | [Plotting](plotting.md) |
| `investment_wealth` | [Plotting](plotting.md) |
| `investment_trades` | [Plotting](plotting.md) |
| `investment_funding` | [Plotting](plotting.md) |
| `quantum_samples` | [Plotting](plotting.md) |
| `quantum_convergence` | [Plotting](plotting.md) |

## Automation discovery

Import from `qpiai_finance.automation`.

| Export | Reference |
| --- | --- |
| `capabilities` | [Automation discovery](../automation.md) |
| `guide` | [Automation discovery](../automation.md) |
