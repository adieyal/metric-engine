"""Custom exceptions for the Metric Engine."""

from collections.abc import Sequence
from typing import Optional


class MetricEngineError(Exception):
    """Base exception for all Metric Engine errors."""

    pass


class MissingInputError(MetricEngineError):
    """Raised when required inputs are missing for a calculation."""

    def __init__(self, message: str, missing_inputs: Optional[Sequence[str]] = None):
        super().__init__(message)
        self.missing_inputs = missing_inputs or []

    def __repr__(self) -> str:
        return f"MissingInputError('{self}', missing_inputs={self.missing_inputs})"


class CircularDependencyError(MetricEngineError):
    """Raised when a circular dependency is detected in calculations."""

    def __init__(self, cycle: Sequence[str]):
        self.cycle = tuple(cycle)
        cycle_str = " -> ".join(self.cycle)
        super().__init__(f"Circular dependency detected: {cycle_str}")

    def __repr__(self) -> str:
        return f"CircularDependencyError({self.cycle})"


class CalculationError(MetricEngineError):
    """Generic calculation error."""

    def __init__(self, message: str, calculation_name: Optional[str] = None):
        super().__init__(message)
        self.calculation_name = calculation_name

    def __repr__(self) -> str:
        return f"CalculationError('{self}', calculation_name='{self.calculation_name}')"
