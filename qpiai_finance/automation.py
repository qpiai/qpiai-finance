"""Platform-independent library discovery for automated financial workflows."""

from importlib.metadata import distribution, version
from inspect import getdoc, isclass, signature
from pathlib import Path

__all__ = ["capabilities", "guide"]


def guide(document="automation.md"):
    """Read automation.md or README.md locally, without network access."""
    if document not in {"automation.md", "README.md"}:
        raise ValueError("document must be 'automation.md' or 'README.md'")
    # Editable checkouts read the current source, including knowledge edits.
    project = Path(__file__).resolve().parent.parent
    if (project / "pyproject.toml").is_file():
        return (project / document).read_text(encoding="utf-8")
    package = distribution("qpiai-finance")
    for entry in package.files or []:
        if (
            str(entry)
            .replace("\\", "/")
            .endswith(f"share/doc/qpiai-finance/{document}")
        ):
            path = Path(package.locate_file(entry))
            if path.is_file():
                return path.read_text(encoding="utf-8")
    # pip --target relocates data files beneath its target directory.
    path = project / "share" / "doc" / "qpiai-finance" / document
    if path.is_file():
        return path.read_text(encoding="utf-8")
    raise FileNotFoundError(f"the Finance distribution has no {document}")


def _describe(value, qualified_name):
    record = {
        "import": qualified_name,
        "kind": "class" if isclass(value) else "function",
        "signature": str(signature(value)),
        "documentation": getdoc(value) or "",
    }
    if isclass(value):
        record["methods"] = {
            name: {
                "signature": str(signature(method)),
                "documentation": getdoc(method) or "",
            }
            for name in dir(value)
            if not name.startswith("_")
            and callable(method := getattr(value, name))
        }
    return record


def capabilities():
    """Return JSON-compatible tasks, public signatures and execution routes.

    This operation reads installed public APIs and provider capabilities.
    It performs no authentication, optimization, submission or paid work.
    Solver availability does not prove a specific financial model is
    feasible or supported by every provider: inspect that model first.
    """
    import cvxpy
    from qpiai_opt.opt_solvers import provider_capabilities

    from . import data, io, plot, quantum, risk, solve, validate
    from . import inspect as inspect_model
    from .cashflows import (
        bullet_loan_cash_flows,
        discount_cash_flows,
        present_value,
    )
    from .collateral import CollateralAllocationModel, haircut_adjusted_value
    from .credit import CreditAllocationModel
    from .hedging import HedgeModel
    from .insurance import ReinsuranceModel, excess_of_loss, quota_share
    from .portfolio import FrontierResult, PortfolioModel
    from .results import FinanceResult
    from .results import from_opt as recover_opt_result
    from .scenarios import ScenarioPaths, Scenarios, ScenarioTree
    from .settlement import SettlementModel
    from .trading import ExecutionModel, TradingModel
    from .trading import costs as trading_costs
    from .treasury import FundingModel, LiabilityMatchingModel

    tasks = {
        "multi_period_investment": {
            "purpose": (
                "Plan adaptive asset trades, cash, shared term funding "
                "and liability-aware terminal wealth "
                "on an explicit financial information tree."
            ),
            "reference": "README.md#multi-period-investment-planning",
            "api": [
                _describe(TradingModel, "qpiai_finance.trading.TradingModel")
            ],
        },
        "execution_scheduling": {
            "purpose": "Schedule signed orders within cash and market limits.",
            "reference": "README.md#execution-scheduling",
            "api": [
                _describe(
                    ExecutionModel, "qpiai_finance.trading.ExecutionModel"
                )
            ],
        },
        "result_interchange": {
            "purpose": "Restore results and replay financial decisions.",
            "reference": "README.md#result-interchange",
            "api": [
                _describe(
                    FinanceResult, "qpiai_finance.results.FinanceResult"
                ),
                _describe(
                    FrontierResult, "qpiai_finance.portfolio.FrontierResult"
                ),
                *[
                    _describe(getattr(io, name), f"qpiai_finance.io.{name}")
                    for name in io.__all__
                ],
            ],
        },
        "settlement": {
            "purpose": "Sequence payments with prefix-checked liquidity.",
            "reference": "README.md#payment-settlement",
            "api": [
                _describe(
                    SettlementModel, "qpiai_finance.settlement.SettlementModel"
                )
            ],
        },
        "reinsurance": {
            "purpose": "Choose reinsurance under claim and surplus risks.",
            "reference": "README.md#insurance-and-reinsurance",
            "api": [
                _describe(
                    ReinsuranceModel,
                    "qpiai_finance.insurance.ReinsuranceModel",
                ),
                _describe(
                    excess_of_loss, "qpiai_finance.insurance.excess_of_loss"
                ),
                _describe(quota_share, "qpiai_finance.insurance.quota_share"),
            ],
        },
        "collateral_allocation": {
            "purpose": "Assign collateral with dated inventory limits.",
            "reference": "README.md#collateral-allocation",
            "api": [
                _describe(
                    CollateralAllocationModel,
                    "qpiai_finance.collateral.CollateralAllocationModel",
                ),
                _describe(
                    haircut_adjusted_value,
                    "qpiai_finance.collateral.haircut_adjusted_value",
                ),
            ],
        },
        "credit_allocation": {
            "purpose": "Allocate credit within resource and risk limits.",
            "reference": "README.md#credit-allocation",
            "api": [
                _describe(
                    CreditAllocationModel,
                    "qpiai_finance.credit.CreditAllocationModel",
                )
            ],
        },
        "portfolio": {
            "purpose": "Construct portfolios and plan trades with tax lots.",
            "reference": "README.md#portfolio-optimization",
            "api": [
                _describe(
                    PortfolioModel, "qpiai_finance.portfolio.PortfolioModel"
                )
            ],
        },
        "funding": {
            "purpose": (
                "Plan dated or adaptive multi-currency investments, "
                "funding, "
                "shared facilities, exposure limits, expected shortfall "
                "and explicit account transfers."
            ),
            "reference": "README.md#funding-and-cash-flows",
            "api": [
                _describe(FundingModel, "qpiai_finance.treasury.FundingModel")
            ],
        },
        "liability_matching": {
            "purpose": "Buy a dedicated portfolio meeting dated liabilities.",
            "reference": "README.md#liability-matching",
            "api": [
                _describe(
                    LiabilityMatchingModel,
                    "qpiai_finance.treasury.LiabilityMatchingModel",
                )
            ],
        },
        "hedging": {
            "purpose": (
                "Match signed sensitivities or hedge supplied repriced "
                "P&L using tail/worst-case loss and hard mandates."
            ),
            "reference": "README.md#hedging",
            "api": [_describe(HedgeModel, "qpiai_finance.hedging.HedgeModel")],
        },
        "discount_cash_flows": {
            "purpose": "Calculate loan cash flows and present values.",
            "reference": "README.md#funding-and-cash-flows",
            "api": [
                _describe(
                    bullet_loan_cash_flows,
                    "qpiai_finance.cashflows.bullet_loan_cash_flows",
                ),
                _describe(
                    discount_cash_flows,
                    "qpiai_finance.cashflows.discount_cash_flows",
                ),
                _describe(
                    present_value, "qpiai_finance.cashflows.present_value"
                ),
            ],
        },
        "scenarios": {
            "purpose": (
                "Build financial scenarios, paths and information trees; "
                "check policy information timing."
            ),
            "reference": "README.md#historical-and-bootstrap-scenarios",
            "api": [
                _describe(Scenarios, "qpiai_finance.scenarios.Scenarios"),
                _describe(
                    ScenarioPaths, "qpiai_finance.scenarios.ScenarioPaths"
                ),
                _describe(
                    ScenarioTree, "qpiai_finance.scenarios.ScenarioTree"
                ),
            ],
        },
    }
    for task, module, purpose, reference in (
        (
            "model_interchange",
            io,
            "Save and restore validated source models without running jobs.",
            "README.md#model-interchange",
        ),
        (
            "trading_costs",
            trading_costs,
            "Evaluate supplied per-unit and fixed ticket fees or temporary "
            "market-impact costs; build convex impact expressions in "
            "a custom financial model.",
            "README.md#trading-cost-functions",
        ),
        (
            "risk",
            risk,
            "Estimate moments, measure financial upper-tail risk and build "
            "risk terms for custom financial models.",
            "README.md#risk-analysis-and-plots",
        ),
        (
            "data",
            data,
            "Convert returns and compound or explicitly rescale moments.",
            "README.md#risk-analysis-and-plots",
        ),
        (
            "binary_portfolio",
            quantum,
            "Encode equal-weight portfolios, run explicit Opt gate algorithms "
            "and verify or recover source financial candidates.",
            "README.md#binary-portfolio-formulations",
        ),
        (
            "plotting",
            plot,
            "Plot verified result data on Matplotlib axes.",
            "README.md#risk-analysis-and-plots",
        ),
    ):
        tasks[task] = {
            "purpose": purpose,
            "reference": reference,
            "api": [
                _describe(getattr(module, name), f"{module.__name__}.{name}")
                for name in module.__all__
            ],
        }
    tasks["opt_result_recovery"] = {
        "purpose": (
            "Recover and verify financial decisions from a recorded "
            "native Opt LP/MILP/QP, encoded QUBO/HUBO/Ising or gate result "
            "without another solve."
        ),
        "reference": "README.md#recovering-opt-solver-results",
        "api": [
            _describe(recover_opt_result, "qpiai_finance.results.from_opt")
        ],
    }
    installed = set(cvxpy.installed_solvers())
    return {
        "schema_version": 1,
        "distribution": "qpiai-finance",
        "version": version("qpiai-finance"),
        "automation_guide": "qpiai_finance.automation.guide()",
        "tasks": tasks,
        "operations": {
            name: {
                **_describe(operation, f"qpiai_finance.{name}"),
                "authentication_required": name == "solve",
            }
            for name, operation in (
                ("inspect", inspect_model),
                ("validate", validate),
                ("solve", solve),
            )
        },
        "execution": {
            "default_mode": "local",
            "modes": ["local", "auto", "platform"],
            "automatic_paid_fallback_by_default": False,
            "auto_platform_permission": "allow_platform=True",
            "external_solver_modes": ["local"],
            "gate_algorithm_modes": ["local", "platform"],
            "opt_providers": provider_capabilities(),
            "external_solvers": {
                "clarabel": "CLARABEL" in installed,
                "scip": "SCIP" in installed,
            },
            "all_solves_require_opt_authentication": True,
            "finance_gate_based_execution": True,
        },
    }
