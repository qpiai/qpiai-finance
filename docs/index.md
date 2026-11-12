# QpiAI Finance user manual

QpiAI Finance expresses optimization in financial terms and preserves those terms through quantum-inspired, gate-based, and standard numerical methods. Start with the decision and its constraints, select a supported representation, then inspect the recovered financial result.

## Start using the library

Read [getting started](getting-started.md) for installation, financial input preparation, authentication, and a first portfolio workflow. Use [data conventions](data.md) to establish identifier order, units, horizons, dates, and covariance validity. [Solver selection and execution](solving.md) explains route selection, options, limits, and verification.

## Financial models

Choose the model that owns the decision:

| Decision | Reference |
| --- | --- |
| Portfolio weights, asset selection, rebalancing, risk budgets, frontier | [Portfolios](portfolio.md) |
| Adaptive investment, cash, funding, and terminal wealth | [Multi-period investment planning](trading.md) |
| Order quantities across intervals and venues | [Execution scheduling](execution.md) |
| Sensitivity or repriced scenario hedges | [Hedging](hedging.md) |
| Loan/facility allocations and resource limits | [Credit allocation](credit.md) |
| Funding draws, repayments, investments, and transfers | [Funding and liquidity](funding.md) |
| Asset purchases against dated obligations | [Liability matching](liability-matching.md) |
| Reinsurance contract or program selection | [Reinsurance](insurance.md) |
| Dated eligible collateral assignments | [Collateral](collateral.md) |
| Payment schedules, liquidity, and permitted atomic batches | [Settlement](settlement.md) |

## Representations and research controls

[Quantum-inspired and gate-based quantum optimization](quantum.md) covers portfolio polynomial compilation, native higher-order solving, QUBO and Ising, penalties, samples, algorithm configuration, execution, and recovery. [Custom financial models](custom-models.md) explains reuse of financial calculations, detached model exports, explicit Opt compilation, and verification of added financial rules.

The [algorithm control reference](algorithm-controls.md) lists circuit, optimizer, mixer, initialization, and execution settings. The [solver option reference](solver-options.md) defines local/platform numerical controls and links to the complete native SCIP parameter catalogue.

## Shared calculations

[Risk analytics](risk.md) covers estimates, factor covariance, risk contributions, Black–Litterman views, VaR, and expected shortfall. [Scenarios](scenarios.md) defines weighted outcomes, paths, sampling, and information trees. [Cash flows](cashflows.md) covers loan schedules, discounting, and present values. [Trading costs](trading-costs.md) defines fee and market-impact calculations.

## Results and integration

Read [results and verification](results.md) for financial decisions, metrics, tables, statuses, reconciliation, replay, and recorded Opt recovery. Use [interchange](interchange.md) for supported model, scenario, and result JSON. [Plotting](plotting.md) provides the Matplotlib API and required result data.

The [public API index](public-api.md) maps imports to their reference pages. [automation.md](../automation.md) supplies task selection and execution procedures for automated workflows. [Contributing](../CONTRIBUTING.md), [bug reporting](../REPORTING_BUGS.md), and [feature requests](../FEATURE_REQUESTS.md) describe project participation. Source is hosted at [qpiai/qpiai-finance](https://github.com/qpiai/qpiai-finance).
