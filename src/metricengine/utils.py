"""Utility functions for the Metric Engine."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import (
    TYPE_CHECKING,
    SupportsFloat,
    Union,
)

from .exceptions import CalculationError

if TYPE_CHECKING:
    from .value import FinancialValue  # for typing only

# Values we’re willing to coerce to Decimal (or None to propagate)
SupportsDecimal = Union[int, float, str, Decimal, SupportsFloat, None, "FinancialValue"]


def to_decimal(val: SupportsDecimal) -> Decimal | None:
    """
    Best-effort conversion that respects FinancialValue wrappers and the
    current null-behaviour policy. Returns None on invalid/None inputs unless
    NullBinaryMode.RAISE is active, in which case it raises CalculationError.

    Accepted:
      - Decimal: returned as-is
      - int (but not bool): exact
      - float / SupportsFloat: via repr() to preserve round-trip
      - str: via Decimal(str), after strip()
      - FinancialValue: returns its raw Decimal (or None)
      - None: returns None
    """
    # Lazy imports to avoid cycles
    from .null_behaviour import NullBinaryMode, get_nulls
    from .value import FinancialValue  # type: ignore

    nulls = get_nulls()

    def _fail(exc: Exception, msg: str) -> Decimal | None:
        if nulls.binary == NullBinaryMode.RAISE:
            if isinstance(exc, TypeError):
                raise exc
            raise CalculationError(msg) from exc
        return None

    # Fast paths
    if val is None:
        return None
    if isinstance(val, Decimal):
        return val

    # FinancialValue: use raw decimal (could be None)
    if isinstance(val, FinancialValue):
        # NOTE: using a private attr; consider adding a public accessor.
        return val._value  # type: ignore[attr-defined]

    # Reject bools explicitly (bool is a subclass of int)
    if isinstance(val, bool):
        return _fail(TypeError("bool not allowed"), "Unsupported type: bool")

    # Exact int
    if isinstance(val, int):
        return Decimal(val)

    # Clean string
    if isinstance(val, str):
        s = val.strip()
        if not s:
            return _fail(InvalidOperation("empty string"), "Invalid operation: ")
        try:
            return Decimal(s)
        except InvalidOperation as e:
            return _fail(e, f"Invalid operation: {val}")

    # Native float
    if isinstance(val, float):
        try:
            return Decimal(repr(val))
        except InvalidOperation as e:
            return _fail(e, f"Invalid float: {val!r}")

    # Generic SupportsFloat
    if isinstance(val, SupportsFloat):
        try:
            return Decimal(repr(float(val)))
        except (InvalidOperation, ValueError, TypeError) as e:
            return _fail(e, f"Invalid float-like: {val!r}")

    # Anything else is unsupported
    return _fail(
        TypeError(f"Unsupported type for Decimal conversion: {type(val).__name__}"),
        f"Unsupported type for Decimal conversion: {type(val).__name__}",
    )
