"""Eligible collateral assignment with dated coverage and inventory locks."""

from ._model import CollateralAllocationModel
from ._valuation import haircut_adjusted_value

__all__ = ["CollateralAllocationModel", "haircut_adjusted_value"]
