# QpiAI Finance

QpiAI Finance is a Python library for financial modeling, optimization, and risk analysis, with quantum-inspired solvers and gate-based quantum optimization through QpiAI Opt. 

The library covers investment portfolios, trading and execution, hedging, lending, treasury, reinsurance, collateral, and payment settlement. Shared risk, scenario, cash-flow, and cost calculations also support custom financial models. LP, MILP, QP, conic, and mixed-integer methods complement QUBO, HUBO, Ising, and gate-based quantum optimization where the financial formulation requires them.

QpiAI Opt's native higher-order HUBO solver solves the polynomial in its natural higher-order form, preserving its energy landscape without reductions or reduction-induced approximations. Finance retains the original financial objective and checks the recovered decision against the financial constraints.

Read the [user manual](docs/index.md), [getting started guide](docs/getting-started.md), or [API index](docs/public-api.md). Agents and workflow authors start with [automation.md](automation.md).

## Install

```bash
pip install qpiai-finance
```

The distribution is `qpiai-finance`; the Python namespace is `qpiai_finance`. The package declares Python 3.10–3.14 support and installs its numerical, optimization, plotting, and QpiAI dependencies. See [installation and dependencies](docs/getting-started.md) for the complete dependency contract and environment checks.

## Portfolio optimization

Create the financial model, choose its objective, and state the investment restrictions. An equal-weight selection has a direct binary interpretation: each selected asset receives the specified allocation. Compile that model for a quantum-inspired solver or QpiAI QPU without replacing asset identifiers with a separate financial model.

```python
import os
import pandas as pd

from qpiai_opt.opt_solvers import Client

from qpiai_finance import inspect, solve
from qpiai_finance.portfolio import PortfolioModel
from qpiai_finance.quantum import compile_portfolio

expected_returns = pd.Series({"equity": 0.08, "bonds": 0.04, "credit": 0.06})
covariance = pd.DataFrame(
    [[0.040, 0.002, 0.010], [0.002, 0.009, 0.003], [0.010, 0.003, 0.025]],
    index=expected_returns.index,
    columns=expected_returns.index,
)

portfolio = PortfolioModel(expected_returns, covariance, horizon="one year")
portfolio.maximize_utility(risk_aversion=3.0)
portfolio.select_assets(count=2, equal_weight=True)

encoding = compile_portfolio(portfolio, representation="hubo")
report = inspect(encoding)
client = Client(api_key=os.environ["QPIAI_OPT_API_KEY"])
result = solve(encoding, client=client)

if result.feasible:
    print(result.weights)
    print(result.objective, result.metrics)
else:
    print(result.status, result.constraints)
```

For continuous allocation, omit `select_assets` and call `solve(portfolio, client=client)`. The same portfolio interface supports minimum variance, tracking error, expected shortfall, downside risk, risk budgets, hierarchical risk parity, robust return forecasts, efficient frontiers, and rebalancing with costs, tax lots, and discrete trades. See [portfolios](docs/portfolio.md).

## Binary portfolio formulations

`compile_portfolio` produces HUBO, QUBO, or Ising representations for equal-weight selection with variance, tracking-error, mean-variance, or higher-moment utility objectives. Its `PortfolioEncoding` retains the selection-to-asset mapping, financial model, penalties, and conversion details. Decode samples into portfolio weights, evaluate original feasibility, or recover a recorded Opt result without another solve.

Gate-based quantum optimization uses algorithms and execution settings from `qpiai_opt.quantum`. Compile explicitly to QUBO or Ising, inspect compatibility, then pass the algorithm and `QuantumRun` to Finance's `solve`. Research controls include algorithm parameters, sampling, execution selection, penalties, and quadratization settings. Finance's direct binary compiler accepts its documented portfolio subset; other supported financial models expose customizable formulations for compilation and result recovery. See [quantum-inspired and gate-based optimization](docs/quantum.md) and [custom financial models](docs/custom-models.md).

## Multi-period investment planning

`TradingModel` plans trades, cash, borrowing, term funding, and terminal wealth on a `ScenarioTree`. Decisions belong to information nodes, so scenarios with the same observed history share decisions. Objectives include expected wealth, worst-case wealth, and expected shortfall. Costs, market impact, liabilities, lots, participation, exposures, and funding limits enter the financial model. See [investment planning](docs/trading.md).

## Execution scheduling

`ExecutionModel` schedules signed orders over time and venues subject to completion, market capacity, participation, inventory, borrowing, cash, and exposure limits. Supplied spread, fee, market-impact, and price-risk assumptions determine modeled execution costs and inventory risk. Results contain proposed executions and residual orders. See [execution scheduling](docs/execution.md).

## Hedging

`HedgeModel` uses supplied sensitivities or repriced scenario P&L to choose hedge quantities. Match exposures, minimize weighted mismatch, or optimize tail or worst-case loss with position, trade, capital, and cash restrictions. Delta, beta, DV01, and other sensitivities keep their supplied units. See [hedging](docs/hedging.md).

## Credit allocation

`CreditAllocationModel` allocates facility amounts within funding, capital, exposure, concentration, lot, and selection limits. Supplied default-risk parameters and loss scenarios support expected-loss and tail-risk analysis. Existing allocations and transaction costs support changes to a credit book. See [credit allocation](docs/credit.md).

## Funding and cash flows

`FundingModel` plans dated or scenario-dependent cash, investments, funding draws, debt, and explicit account transfers. Model shared facilities, repayments, liquidity buffers, exposure limits, and expected, worst-case, or tail funding costs. Cash stays in its account currency; transfers use explicit conversion assumptions. `cashflows` provides bullet-loan schedules, discounting, and present values. See [funding and liquidity](docs/funding.md) and [cash-flow calculations](docs/cashflows.md).

## Liability matching

`LiabilityMatchingModel` buys asset quantities to meet dated liabilities while respecting cash, initial capital, holdings, lots, and supplied sensitivity constraints. Results include the cash ladder and liability coverage. See [liability matching](docs/liability-matching.md).

## Insurance and reinsurance

`ReinsuranceModel` selects supplied contracts or programs using gross-loss scenarios, recoveries, premiums, contingent costs, and recoverability assumptions. Optimize expected cost, expected shortfall, or premium with coverage, exclusivity, counterparty, retained-loss, and surplus requirements. `excess_of_loss` and `quota_share` calculate the stated payout structures. See [reinsurance](docs/insurance.md).

## Collateral allocation

`CollateralAllocationModel` assigns inventory to permitted dated pledges using explicit prices, haircuts, FX rates, and obligation coverage. Quantity, availability, concentration, movement, and lot limits govern feasible assignments. Results report coverage, remaining inventory, and movement costs. See [collateral allocation](docs/collateral.md).

## Payment settlement

`SettlementModel` schedules payments with participant liquidity checked at each execution step. Explicit atomic batches support permitted simultaneous settlement; precedence, releases, deadlines, credit, prefunding, and final balances remain part of the model. Results contain proposed schedules, balances, and queued payments. See [settlement](docs/settlement.md).

## Historical and bootstrap scenarios

`Scenarios` stores weighted scenario outcomes; `ScenarioPaths` stores paths with ordered steps; `ScenarioTree` represents information available at each decision stage. Historical and bootstrap construction supports explicit as-of and availability times. Scenario values retain their declared horizon, units, probabilities, and identifiers. See [scenarios and information timing](docs/scenarios.md).

## Trading cost functions

`transaction_fees` evaluates proportional and fixed trading fees. `market_impact_cost` evaluates supplied impact coefficients or builds convex CVXPY expressions for custom models. These calculations use the caller's quantity and cost conventions. See [trading costs](docs/trading-costs.md).

## Risk analysis and plots

Estimate sample or exponentially weighted moments, apply explicit covariance shrinkage, retain factor risk, combine prior forecasts with Black–Litterman views, and calculate portfolio risk contributions, VaR, or expected shortfall. Calculations preserve the supplied horizon; loss-tail risk uses scenario probabilities and fractional boundary mass.

`qpiai_finance.plot` creates Matplotlib axes from financial results: portfolio weights and risk, trades and tax lots, efficient frontiers, loss distributions, funding and liquidity, hedges, credit, reinsurance, collateral, settlement, execution, and quantum samples. Results also provide pandas tables for existing reporting systems. See [data conventions](docs/data.md), [risk analytics](docs/risk.md), and [plotting](docs/plotting.md).

## Execution and verification

Every Finance solve requires an authenticated `qpiai_opt.opt_solvers.Client`, including local execution and external solvers. Register for an Opt API key at [QpiAI Opt](https://opt.qpiai.tech/). Gate-based quantum optimization additionally requires QCloud authentication through `QpiAIQuantumAuth`; obtain its key at [QpiAI QCloud](https://qcloud.qpiai.tech/). Keep credentials in the application's secret store.

The default execution mode is `local`. QpiAI routes support `local`, `auto`, and `platform`; automatic paid fallback requires `allow_platform=True`. Clarabel, SCIP, and HRP use local execution. Platform execution is explicit and can consume credits. Modeling, inspection, evaluation, and interchange require no authentication. See [solver selection, options, and execution](docs/solving.md).

Check `result.feasible` before consuming a decision and `result.optimality_proven` when a proof is required. Finance recalculates the original financial objective, constraints, and accounting from the recovered decision. A solver incumbent, a low encoded energy, and a verified financial optimum carry different guarantees. See [results and verification](docs/results.md).

## Model interchange

Use `qpiai_finance.io` to save and restore supported financial models and scenarios as versioned JSON, preserving labels and supported sparse and factor representations. Loading validates the stored representation and does not execute work. See [interchange](docs/interchange.md).

## Result interchange

Use `io.dumps(result)` and `io.loads(text)` for reversible result interchange. `result.to_dict()` and `result.to_json()` produce numeric reports. Re-evaluate a restored record against a trusted source model for fresh financial checks; loading preserves historical claims without proving them again. See [results](docs/results.md) and [interchange](docs/interchange.md).

## Recovering Opt solver results

`qpiai_finance.results.from_opt` reconstructs and checks a recorded Opt result against the original financial model or portfolio encoding. Retain the compiled Opt model and its decoding metadata for transformed results, and objective-scaling metadata where required. Recovery performs no new solve and does not establish a new optimality proof. See [result recovery](docs/results.md).

## Development and citation

Development takes place in [qpiai/qpiai-finance](https://github.com/qpiai/qpiai-finance). See [contribution guidelines](CONTRIBUTING.md), [bug reporting](REPORTING_BUGS.md), and [feature requests](FEATURE_REQUESTS.md). The library is licensed under the [Apache License 2.0](LICENSE).

When the library supports published work, cite the version used. Structured metadata is in [CITATION.cff](CITATION.cff).

```bibtex
@software{qpiai_finance,
  author = {{QpiAI}},
  title = {QpiAI Finance},
  version = {1.0.3},
  url = {https://github.com/qpiai/qpiai-finance}
}
```
