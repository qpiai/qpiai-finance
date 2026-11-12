# Getting started

Use QpiAI Finance to describe a financial decision, choose its objective and restrictions, then obtain and verify the financial outcome. The same domain model provides an entry to supported quantum-inspired representations and standard numerical formulations.

## Install and check the environment

```bash
pip install qpiai-finance
python -m pip check
python -c "from importlib.metadata import version; print(version('qpiai-finance'))"
```

The package declares Python `>=3.10,<3.15`. Installation also requires compatible distributions of its dependencies for the selected Python version, operating system, and architecture. Runtime dependencies are:

| Distribution | Declared requirement | Role |
| --- | --- | --- |
| `qpiai-opt[quantum]` | `==0.0.9` | Opt modeling, solver execution, polynomial representations, gate-based integration, and compatible Quantum SDK dependency. |
| `numpy` | `>=1.26,<3` | Numeric arrays and linear algebra. |
| `scipy` | `>=1.15,<2` | Sparse matrices, statistical/numerical calculations, and clustering. |
| `pandas` | `>=2.2,<4` | Labeled financial inputs and result tables. |
| `cvxpy` | `>=1.7.5,<2` | Supported convex and mixed-integer formulations. |
| `clarabel` | `>=0.11.1,<0.12` | Continuous conic solving. |
| `pyscipopt` | `>=6.3,<7` | SCIP integration for supported mixed-integer and nonlinear models. |
| `matplotlib` | `>=3.8,<4` | Financial result and analysis plots. |

The `dev` extra adds development tools. QpiAI Opt's pinned quantum extra selects `qpiai-quantum==0.3.0`.

## Prepare financial inputs

Use adjusted prices, supplied forecasts, or outputs from existing institutional data and risk systems. Finance does not download market data or price instruments. For a portfolio, align expected arithmetic returns and covariance at the same horizon.

```python
import pandas as pd

from qpiai_finance.portfolio import PortfolioModel

expected_returns = pd.Series({"equity": 0.08, "bonds": 0.04, "credit": 0.06})
covariance = pd.DataFrame(
    [[0.040, 0.002, 0.010], [0.002, 0.009, 0.003], [0.010, 0.003, 0.025]],
    index=expected_returns.index,
    columns=expected_returns.index,
)
portfolio = PortfolioModel(expected_returns, covariance, horizon="one year")
portfolio.maximize_utility(risk_aversion=3.0)
```

Returns are fractions. `0.08` means 8% over the declared year. The covariance uses squared-return units over that same year. The horizon string records the convention; it does not annualize either input. Default portfolio bounds are long-only, from zero to one. See [data conventions](data.md) and [portfolio parameters](portfolio.md).

## Select and inspect a binary portfolio

For a portfolio with exactly two equal-weight holdings:

```python
from qpiai_finance import inspect, validate
from qpiai_finance.quantum import compile_portfolio

portfolio.select_assets(count=2, equal_weight=True)
encoding = compile_portfolio(portfolio, representation="hubo")
problem_class = validate(encoding)
report = inspect(encoding)
print(problem_class)
print(encoding.variable_mapping)
```

The two selected assets each receive weight `0.5`. The encoding retains the objective, cardinality restriction, asset mapping, and original financial model. `hubo` retains higher-order polynomial terms when present. `qubo` and `ising` select pairwise representations, with recorded auxiliary conversions when required. See [quantum-inspired and gate-based quantum optimization](quantum.md) for supported objectives, constraints, penalties, and execution controls.

Validation and inspection do not solve, authenticate, or prove feasibility. Inspection can include full financial inputs. Handle the report accordingly.

## Authenticate and solve

Register for an Opt API key at [QpiAI Opt](https://opt.qpiai.tech/) and place it in the application's environment or secret store. Every Finance solve verifies an Opt client, including local computation and external solvers.

```python
import os

from qpiai_opt.opt_solvers import Client
from qpiai_finance import solve

client = Client(api_key=os.environ["QPIAI_OPT_API_KEY"])
result = solve(encoding, client=client)
```

This selects the local Opt route. Key verification requires connectivity. Platform work is selected explicitly and can consume credits. Gate-based quantum optimization additionally requires QCloud authentication and an explicitly selected Opt algorithm and execution settings. [Solving](solving.md) defines the full execution contract.

## Check the financial outcome

```python
print(result.status, result.feasible, result.optimality_proven)

if result.feasible:
    print(result.weights)
    print(result.objective, result.objective_unit)
    print(result.metrics)
else:
    print(result.constraints)
```

The objective is recalculated in financial units. `feasible` reports the original financial checks; `optimality_proven` is a separate guarantee. Do not treat the smallest observed polynomial energy or a completed job as proof of a financial optimum. See [results](results.md).

## Use another financial formulation

For continuous allocation, create a portfolio without `select_assets` and solve it directly. Add weight, exposure, return, leverage, turnover, or other documented restrictions through the model methods. For actual rebalancing, supply holdings, prices, cash, and currency; results then include proposed quantities and cash accounting.

For a custom financial model, reuse risk, cash-flow, scenario, and cost calculations with an explicit Opt or supported external formulation. Supported Finance models expose detached formulations and labeled financial expressions. Changes to those exports do not modify the original Finance model. [Custom models](custom-models.md) explains compilation and result recovery.

Use the [manual](index.md) to select trading, treasury, credit, hedging, reinsurance, collateral, or settlement workflows. [automation.md](../automation.md) provides discovery and procedural guidance for automated use.
