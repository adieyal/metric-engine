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

All calculations are automatically registered with the global registry when imported.
"""


# calculations/__init__.py
def load_all() -> None:
    # Import modules for their registration side-effects only
    from . import (
        growth,  # noqa: F401
        inventory,  # noqa: F401
        pricing,  # noqa: F401
        profitability,  # noqa: F401
        ratios,  # noqa: F401
        unit_economics,  # noqa: F401
        utilities,  # noqa: F401
        variance,  # noqa: F401
    )
