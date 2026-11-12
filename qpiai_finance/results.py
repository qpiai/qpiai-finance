"""Financial decisions, independent constraint checks and execution
evidence.
"""

from dataclasses import dataclass, field

import pandas as pd

from ._serialization import dumps, portable

__all__ = ["FinanceResult", "from_opt"]


def from_opt(
    result, *, model, opt_model=None, objective_scaling=None, tolerance=1e-7
):
    """Recover financial decisions from a recorded native Opt result.

    Supply the original financial model for LP/MILP/QP, or its original
    PortfolioEncoding for direct portfolio QUBO/HUBO/Ising/gate records.
    For other polynomial/gate records, also retain opt_model: the actual
    Opt Model after its explicit QUBO/HUBO/Ising compilation. Its public
    decoder verifies the sample-to-source assignment. Finite bounds and
    any explicit continuous grid are Opt's compilation contract.
    This offline operation rechecks complete native coordinates,
    original financial constraints
    and the objective. It performs no authentication, solve or submission.
    PortfolioEncoding verifies encoded energy and product auxiliaries.
    opt_model recovery instead checks decoded assignments, native source
    constraints, original financial constraints and source objectives.
    It does not verify encoded energies or penalty/slack auxiliaries.
    Those verification scopes remain explicit in solver_info. Gate records
    select the best freshly feasible reported financial candidate; measured
    counts and reported primary/residual candidates remain distinct.
    Keep the original Opt result type when loading its JSON with Opt.

    For a raw LP/MILP job result submitted with Finance's objective
    conditioning, also supply the objective_scaling metadata saved from
    inspect(model)['optimization'] or the Finance result's solver_info.
    This restores its declared units without inferring a scale from costs.

    Recorded solver evidence is retained under solver_info['recorded_solver'].
    Matching coordinates and objective do not prove which constraints were
    optimized: optimality_proven is always False. Status is feasible,
    verification_failed, objective_mismatch or no_solution. Versions and
    recovery timings describe the current verification environment.
    """
    from ._opt_recovery import recover

    return recover(
        result,
        model=model,
        opt_model=opt_model,
        objective_scaling=objective_scaling,
        tolerance=tolerance,
    )


@dataclass
class FinanceResult:
    """One solve record in source financial coordinates.

    ``feasible`` reflects Finance's original financial constraints and
    required decision reconstruction checks. Derived solver bookkeeping
    appears separately in tables['solver_reconciliation'] when applicable.
    ``optimality_proven`` additionally requires the backend's proof
    claim, objective reconciliation and consistent solver reconstruction.
    A missing incumbent has no
    decision, objective or financial tables. Tables are ordinary pandas
    objects suitable for downstream analysis.

    Restored records retain historical claims. Loading does not repeat
    financial verification or prove optimality; evaluate against a trusted
    source model for fresh source checks.
    """

    status: str
    feasible: bool
    optimality_proven: bool
    decision: dict[str, pd.Series | pd.DataFrame]
    objective: float | None
    objective_unit: str | None
    metrics: dict
    constraints: pd.DataFrame
    solver_info: dict
    provenance: dict
    tables: dict[str, pd.DataFrame] = field(default_factory=dict)
    transformations: list[dict] = field(default_factory=list)
    costs: dict = field(default_factory=dict)

    @property
    def weights(self):
        """Source portfolio weights, or None when no portfolio incumbent
        exists.
        """
        return self.decision.get("weights")

    @property
    def holdings(self):
        return self.decision.get("holdings")

    @property
    def trades(self):
        return self.decision.get("trades")

    @property
    def cash_after(self):
        return self.metrics.get("cash_after")

    @property
    def post_trade_weights(self):
        return self.decision.get("post_trade_weights")

    @property
    def tax_lot_sales(self):
        """Disposal quantities by acquisition lot, when modeled."""
        return self.decision.get("tax_lot_sales")

    @property
    def draws(self):
        return self.decision.get("draws")

    @property
    def transfers(self):
        return self.decision.get("transfers")

    @property
    def investments(self):
        """Purchased units by investment opportunity, when modeled."""
        return self.decision.get("investments")

    @property
    def cash_balances(self):
        return self.decision.get("cash_balances")

    @property
    def hedges(self):
        return self.decision.get("hedges")

    @property
    def positions(self):
        return self.decision.get("positions")

    @property
    def risk_exposures(self):
        return self.decision.get("risk_exposures")

    @property
    def allocations(self):
        """Final credit facility amounts, or None without such an incumbent."""
        return self.decision.get("allocations")

    @property
    def allocation_changes(self):
        """Changes from the supplied existing credit book, if available."""
        return self.decision.get("allocation_changes")

    @property
    def assignments(self):
        """Collateral quantities by permitted pledge, when available."""
        return self.decision.get("assignments")

    @property
    def selections(self):
        """Chosen reinsurance contract/program indicators, when available."""
        return self.decision.get("selections")

    @property
    def settlement_schedule(self):
        """Payment-to-slot assignments; None denotes unsettled instructions."""
        return self.decision.get("schedule")

    @property
    def prefunding(self):
        """Outside prefunding by settlement account, when available."""
        return self.decision.get("prefunding")

    @property
    def peak_credit(self):
        """Actual maximum overdraft used per settlement account."""
        return self.decision.get("peak_credit")

    @property
    def executions(self):
        """Signed quantities by execution opportunity, when available."""
        return self.decision.get("executions")

    @property
    def remaining_orders(self):
        """Signed target quantities remaining after each execution slot."""
        return self.decision.get("remaining_orders")

    @property
    def unfilled(self):
        """Nonnegative residual order quantities at the execution horizon."""
        return self.decision.get("unfilled")

    def to_dict(self):
        """Versioned JSON-compatible record; null denotes an
        absent/undefined value.

        This numeric report is not reversible. Use qpiai_finance.io.to_dict
        for interchange preserving labeled structures and diagnostic bounds.
        """
        return portable({"schema_version": 1, **vars(self)})

    def to_json(self):
        """Return the numeric report as JSON; use io.dumps for interchange."""
        return dumps(self.to_dict())

    def evaluate(self, model, *, tolerance=1e-7):
        """Recompute the primary decision against a supplied source model.

        Returns the model's fresh financial evaluation, plus
        recorded_objective, objective_matches and input_fingerprint_matches.
        Stored metrics, tables and proof flags do not determine feasibility.
        Liability matching additionally uses recorded initial_capital, and
        settlement uses recorded prefunding as primary decision inputs.
        Objective comparison uses the absolute tolerance plus relative 1e-7,
        matching solve's reconciliation convention.

        This is offline financial replay, without solving, authentication or
        a new optimality proof. It does not authenticate historical evidence
        or check backend auxiliary variables. Missing decisions and mismatched
        financial model types raise. The result and source model are unchanged.
        """
        from ._result_evaluation import evaluate

        return evaluate(self, model, tolerance=tolerance)
