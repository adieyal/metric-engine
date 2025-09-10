"""metricengine public API.

This package provides a pluggable metric engine with optional integrations
via entry points. It includes a calculation registry, utility formatters
with optional Babel support, and a comprehensive unit system for type-safe
financial calculations with explicit unit conversions.

Key Features:
- Type-safe FinancialValue objects with unit awareness
- Comprehensive unit system with Money, Quantity, and Percent units
- Conversion registry with multi-hop routing capabilities
- Policy-driven conversion behavior (strict vs permissive)
- Provenance tracking for unit conversions and calculations
- Unit-aware rendering and formatting
"""

from importlib.metadata import PackageNotFoundError, version
from typing import Optional

__version__ = "0.1.0"

try:
    _installed_version = version("metric-engine")
    # Use installed version if available and different (for development)
    if _installed_version != __version__:
        __version__ = _installed_version
except PackageNotFoundError:
    # Use the hardcoded version (during development/build)
    pass

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

# Null behavior configuration
from .null_behaviour import NullBinaryMode, get_nulls

# Policy and configuration
from .policy import DEFAULT_POLICY, Policy
from .policy_context import PolicyResolution, get_policy, use_policy

# Provenance and tracing
from .provenance import calc_span, explain, get_provenance_graph, to_trace_json

# Registry and calculation system
from .registry import calc, deps, get, is_registered, list_calculations

# Rendering system
from .rendering import Renderer, get_renderer, list_renderers, register_renderer

# Shortcuts and utilities
from .shortcuts import inputs_needed_for
from .typed_api import get_calc
from .units import (
    Conversion,
    # Conversion system
    ConversionContext,
    ConversionPolicy,
    # Legacy units (backward compatibility)
    Dimensionless,
    Money,
    MoneyUnit,
    # New unit system
    NewUnit,
    Pct,
    Percent,
    Qty,
    Ratio,
    Unit,
    convert_decimal,
    get_conversion,
    get_current_conversion_policy,
    list_conversions,
    register_conversion,
    use_conversions,
)
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
    # Units (legacy - backward compatibility)
    "Unit",
    "Dimensionless",
    "Ratio",
    "Percent",
    "Money",
    # New unit system
    "NewUnit",
    "MoneyUnit",
    "Qty",
    "Pct",
    # Conversion system
    "ConversionContext",
    "ConversionPolicy",
    "Conversion",
    "register_conversion",
    "get_conversion",
    "list_conversions",
    "convert_decimal",
    "use_conversions",
    "get_current_conversion_policy",
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
    # Provenance and tracing
    "calc_span",
    "explain",
    "get_provenance_graph",
    "to_trace_json",
]
