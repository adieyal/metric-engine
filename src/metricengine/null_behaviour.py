"""
Null Behavior Management Module for Metric Engine

This module provides a comprehensive system for controlling how None values are handled
during financial calculations. It implements a context-aware approach using Python's
ContextVar to manage null handling behavior across different operations without
requiring explicit parameter passing.

Core Components:
    - NullBinaryMode: Controls None handling in binary operations (+, -, *, /)
    - NullReductionMode: Controls None handling in reduction operations (sum, mean)
    - NullBehavior: Configuration class combining both modes
    - Context managers for temporary behavior changes
    - Predefined behavior configurations for common scenarios

Null Binary Modes:
    - PROPAGATE (default): Safe mode where any None operand results in None
    - RAISE: Strict mode that raises exceptions when encountering None values

Null Reduction Modes:
    - PROPAGATE: Returns None if any None values are present in collections
    - SKIP (default): Ignores None values and processes only valid values
    - ZERO: Treats None values as zero for additive reductions
    - RAISE: Raises exceptions when encountering None values

Usage Examples:
    # Set global null behavior
    with use_nulls(NullBehavior(reduction=NullReductionMode.RAISE)):
        result = fv_sum([FV(100), FV.none(), FV(200)])  # Raises exception

    # Temporary reduction mode change
    with with_reduction(NullReductionMode.ZERO):
        total = fv_sum([FV(100), FV.none(), FV(200)])  # Result: FV(300)

    # Predefined behaviors
    with use_nulls(SUM_ZERO):  # Treat None as zero
        revenue_total = fv_sum(revenue_data)

Thread Safety:
    Uses ContextVar for thread-local storage, making it safe for multi-threaded
    applications. Each thread maintains its own null behavior context.

Integration:
    Works seamlessly with FinancialValue arithmetic operations and reduction
    functions like fv_sum and fv_mean throughout the metric engine.
"""

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar, Token
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Callable, TypeVar

__all__ = [
    "NullBinaryMode",
    "NullReductionMode",
    "NullBehavior",
    "use_nulls",
    "use_reduction",
    "use_binary",
    "with_reduction",  # alias
    "with_binary",  # alias
    "get_nulls",
    "DEFAULT_NULLS",
    "STRICT_RAISE",
    "SUM_ZERO",
    "SUM_PROPAGATE",
    "SUM_RAISE",
    "with_nulls",  # decorator
]


class NullBinaryMode(Enum):
    """How None is handled in binary ops (a ⊕ b)."""

    PROPAGATE = auto()  # any None → None
    RAISE = auto()  # any None → raise


class NullReductionMode(Enum):
    """How None is handled in reductions (sum/avg/etc.)."""

    PROPAGATE = auto()  # any None in iterable → None
    SKIP = auto()  # drop None (like pandas skipna=True)
    ZERO = auto()  # treat None as 0 for additive reductions
    RAISE = auto()  # any None → raise


@dataclass(frozen=True, eq=True)
class NullBehavior:
    """Combined null-handling strategy for binary ops and reductions."""

    binary: NullBinaryMode = NullBinaryMode.PROPAGATE
    reduction: NullReductionMode = NullReductionMode.SKIP


# Global context variable for storing current null behavior
_current_nulls: ContextVar[NullBehavior] = ContextVar(
    "_current_nulls", default=NullBehavior()
)


class use_nulls:
    """
    Context manager for temporarily setting null behavior.
    Usage:
        with use_nulls(STRICT_RAISE):
            ...
    """

    def __init__(self, behavior: NullBehavior):
        self.behavior = behavior
        self._token: Token[NullBehavior] | None = None

    def __enter__(self) -> "use_nulls":
        self._token = _current_nulls.set(self.behavior)
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._token is not None:
            _current_nulls.reset(self._token)
            self._token = None


def get_nulls() -> NullBehavior:
    """Return the currently active null behavior."""
    return _current_nulls.get()


@contextmanager
def use_reduction(mode: NullReductionMode) -> Iterator[None]:
    """
    Temporarily override reduction mode only.
    """
    cur = get_nulls()
    token = _current_nulls.set(NullBehavior(binary=cur.binary, reduction=mode))
    try:
        yield
    finally:
        _current_nulls.reset(token)


@contextmanager
def use_binary(mode: NullBinaryMode) -> Iterator[None]:
    """
    Temporarily override binary mode only.
    """
    cur = get_nulls()
    token = _current_nulls.set(NullBehavior(binary=mode, reduction=cur.reduction))
    try:
        yield
    finally:
        _current_nulls.reset(token)


# Back-compat aliases (optional)
with_reduction = use_reduction
with_binary = use_binary


# Predefined behaviors (clear naming)
DEFAULT_NULLS = NullBehavior()  # binary: PROPAGATE, reduction: SKIP
STRICT_RAISE = NullBehavior(
    binary=NullBinaryMode.RAISE, reduction=NullReductionMode.RAISE
)
SUM_ZERO = NullBehavior(reduction=NullReductionMode.ZERO)
SUM_PROPAGATE = NullBehavior(reduction=NullReductionMode.PROPAGATE)
SUM_RAISE = NullBehavior(reduction=NullReductionMode.RAISE)


# Decorator helper
F = TypeVar("F", bound=Callable[..., Any])


def with_nulls(behavior: NullBehavior) -> Callable[[F], F]:
    """
    Decorator to run a function under a specific null behavior.

    @with_nulls(STRICT_RAISE)
    def compute(...):
        ...
    """

    def deco(fn: F) -> F:
        def wrapped(*args, **kwargs):
            with use_nulls(behavior):
                return fn(*args, **kwargs)

        # type: ignore[assignment]
        return wrapped  # preserve F for type checkers

    return deco
