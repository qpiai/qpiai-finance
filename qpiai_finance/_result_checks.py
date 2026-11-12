"""Solver bookkeeping diagnostics alongside original financial checks."""

import pandas as pd


def record_reconciliation(evaluation, rows, *, tolerance):
    """Keep derived solver residuals separate from financial feasibility."""
    if not rows:
        return
    table = pd.DataFrame(
        rows, columns=["constraint", "residual", "unit"]
    ).set_index("constraint")
    table["within_tolerance"] = table.residual <= tolerance
    tables = evaluation["tables"]
    previous = tables.get("solver_reconciliation")
    tables["solver_reconciliation"] = (
        table if previous is None else pd.concat([previous, table])
    )
