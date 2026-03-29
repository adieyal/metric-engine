"""
Financial calculations organized by business domain.

This package contains all financial calculations organized into specialized modules
with proper namespacing using the Collection system. Each module focuses on a
specific business domain:

- pricing: Pricing, tax, markup, and discount calculations
- profitability: Profit margins, ROI, and profitability ratios
- inventory: COGS, inventory management, and F&B specific calculations
- ratios: General ratio and percentage calculations
- variance: Variance analysis and percentage change calculations
- units: Unit economics and per-unit metrics
- growth: Growth rates and CAGR calculations
- utilities: Utility functions and helper calculations

All calculations can be registered into a specific registry when imported.
"""

from __future__ import annotations

import importlib
from types import ModuleType

from ..registry import Registry, default_registry
from ..registry_collections import Collection, using_registry

_MODULE_NAMES = (
    "growth",
    "inventory",
    "pricing",
    "profitability",
    "ratios",
    "unit_economics",
    "utilities",
    "variance",
)
_BUILTIN_GROUP = "metricengine.builtins"


def _get_module_collections(module: ModuleType) -> tuple[Collection, ...]:
    collections = getattr(module, "__collections__", None)
    if collections is None:
        raise RuntimeError(
            f"{module.__name__} must declare __collections__ for registration"
        )
    return tuple(collections)


def register_all(registry: Registry) -> None:
    """Register all built-in calculations into the provided registry."""
    if registry.is_loaded(_BUILTIN_GROUP):
        return

    package_name = __name__

    with using_registry(registry):
        modules = [
            importlib.import_module(f"{package_name}.{module_name}")
            for module_name in _MODULE_NAMES
        ]

    for module in modules:
        for collection in _get_module_collections(module):
            for func in collection.registered_functions():
                name = func._calc_name
                depends_on = tuple(func._calc_depends_on)
                if registry.is_registered(name):
                    continue
                registry.calc(name, depends_on=depends_on)(func)

    registry.mark_loaded(_BUILTIN_GROUP)


def load_all(registry: Registry | None = None) -> None:
    """Compatibility wrapper for built-in calculation registration."""
    register_all(registry or default_registry)
