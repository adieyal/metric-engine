from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from typing import Any

from .policy import Policy
from .utils import SupportsDecimal
from .value import FinancialValue as FV


class CalculationService:
    """Utility class for calculation services."""

    def __init__(self, policy: Policy | None = None):
        self._policy = policy or Policy()

    def _fv(self, x: SupportsDecimal) -> FV:
        return FV(x, policy=self._policy)

    def _d(self, v) -> Decimal | None:
        """Coerce anything into FV with policy, then to Decimal or None."""
        fv = self._fv(v)
        return None if fv.is_none() else fv.as_decimal()

    def _fv_dict(self, x: SupportsDecimal) -> dict[Any, FV]:
        return defaultdict(lambda: self._fv(x))
