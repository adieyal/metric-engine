"""metricengine public API.

This package provides a pluggable metric engine with optional integrations
via entry points. It includes a calculation registry and utility
formatters with optional Babel support.
"""

from importlib.metadata import PackageNotFoundError, version
from typing import Optional

try:
    __version__ = version("metric-engine")
except PackageNotFoundError:  # pragma: no cover - during editable installs
    __version__ = "0.0.0"

# Core value types and units
# Integrations (internal)
from . import integrations as _integrations

# Base classes
from .base import CalculationService
from .engine import Engine

# Equality mode configuration
from .equality_mode import EqualityMode, fv_equality_mode

# Exceptions
from .exceptions import (
    CalculationError,
    CircularDependencyError,
    MetricEngineError,
    MissingInputError,
)

# Formatting utilities
from .formatting import format_currency, format_percent

# Rendering system
from .rendering import Renderer, get_renderer, list_renderers, register_renderer

# Null behavior configuration
from .null_behaviour import NullBinaryMode, get_nulls

# Policy and configuration
from .policy import DEFAULT_POLICY, Policy
from .policy_context import PolicyResolution, get_policy, use_policy

# Registry and calculation system
from .registry import calc, deps, get, is_registered, list_calculations

# Shortcuts and utilities
from .shortcuts import inputs_needed_for
from .typed_api import get_calc
from .units import Dimensionless, Money, Percent, Ratio, Unit
from .value import FV, FinancialValue


def load_plugins(context: Optional[dict] = None) -> int:
    """Load all available plugins with optional context."""
    return _integrations.load_plugins(context)


# Public API - organized by category
__all__ = [
    # Version
    "__version__",
    # Core value types
    "FinancialValue",
    "FV",
    # Units
    "Unit",
    "Dimensionless",
    "Ratio",
    "Percent",
    "Money",
    # Policy and configuration
    "Policy",
    "DEFAULT_POLICY",
    "get_policy",
    "use_policy",
    "PolicyResolution",
    # Exceptions
    "MetricEngineError",
    "MissingInputError",
    "CircularDependencyError",
    "CalculationError",
    # Registry and calculations
    "calc",
    "get",
    "list_calculations",
    "deps",
    "is_registered",
    "Engine",
    # Formatting
    "format_currency",
    "format_percent",
    # Rendering
    "Renderer",
    "register_renderer",
    "get_renderer", 
    "list_renderers",
    # Utilities
    "inputs_needed_for",
    "CalculationService",
    # Configuration
    "get_nulls",
    "NullBinaryMode",
    "EqualityMode",
    "fv_equality_mode",
    # Plugin system
    "load_plugins",
    # Typed API
    "get_calc",
]
