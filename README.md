# Metric Engine

**Robust Python library for precision calculations with strong typing, policy-driven behavior, and bulletproof error handling.**

Metric Engine provides a comprehensive foundation for building applications that require type-safe calculations, decimal precision, and graceful handling of missing data. Perfect for financial applications, business metrics, scientific calculations, or any domain where precision and type safety matter.

## Key Features

🏷️ **Strongly Typed Values**
- Values carry their unit type (Money, Ratio, Percent) and policy information
- Prevents unit mismatches and ensures consistent formatting across your application

🔒 **Immutable & Safe**
- All operations return new instances - no mutations, no surprises
- Division by zero and invalid operations return `None` instead of crashing
- Configurable strict vs. lenient behavior via policies

📐 **Decimal Precision**
- Built on Python's `Decimal` type to eliminate floating-point precision issues
- Critical for calculations where precision matters

🔧 **Extensible Calculation Engine**
- Register custom calculations in organized collections
- Automatic dependency resolution and circular dependency detection
- Policy-driven formatting and rounding behavior

🌐 **Internationalization Ready**
- Optional Babel integration for currency and percentage formatting
- Support for multiple locales and currency symbols

⚡ **Production Ready**
- Comprehensive test suite with >95% coverage
- Type hints throughout for IDE support and static analysis
- Plugin system for framework integrations (Django, etc.)

## Installation

Basic install:

```bash
pip install metric-engine
```

With optional extras (Babel only here):

```bash
pip install "metric-engine[babel]"
```

## Quick Start

### Basic Values

```python
from metricengine.factories import money, percent, ratio

# Create type-safe values
revenue = money(150000)
tax_rate = percent(25, input="percent")  # 25%
growth_rate = ratio(0.15)  # 15% as ratio

# Safe arithmetic with automatic type handling
taxes = revenue * tax_rate    # Returns money value
net_income = revenue - taxes  # Returns money value

print(f"Revenue: {revenue}")           # Revenue: 150,000.00
print(f"Taxes: {taxes}")               # Taxes: 37,500.00
print(f"Net Income: {net_income}")     # Net Income: 112,500.00

# Graceful handling of missing data
missing_data = None
safe_calc = revenue * missing_data     # Returns None value, doesn't crash
print(safe_calc.is_none())             # True
```

### Using the Calculation Engine

```python
from metricengine import Engine
from metricengine.factories import money, percent

# Initialize calculation engine
engine = Engine()

# Define data
data = {
    "sales": money(850000),
    "cost_of_goods_sold": money(510000),
    "operating_expenses": money(180000),
    "tax_rate": percent(21, input="percent"),
}

# Calculate metrics using built-in calculations
gross_profit = engine.calculate("profitability.gross_profit", data)
gross_margin = engine.calculate("profitability.gross_margin", data)
operating_profit = engine.calculate("profitability.operating_profit", data)

print(f"Gross Profit: {gross_profit}")      # $340,000.00
print(f"Gross Margin: {gross_margin}")      # 40.00%
print(f"Operating Profit: {operating_profit}")  # $160,000.00
```

### Custom Calculations

```python
from metricengine import calc, FV
from metricengine.units import Money
from metricengine.factories import money

@calc("monthly_revenue", depends_on=("annual_revenue",))
def monthly_revenue(annual_revenue: FV[Money]) -> FV[Money]:
    """Calculate monthly revenue from annual."""
    if annual_revenue.is_none():
        return FV.none(Money)
    return (annual_revenue / 12)

# Register and use your calculation
context = {"annual_revenue": money(1200000)}
monthly = engine.calculate("monthly_revenue", context)
print(f"Monthly Revenue: {monthly}")  # 100,000.00
```

## What Makes It Different

Unlike basic calculation libraries, Metric Engine is designed for **production software** where correctness, safety, and maintainability are paramount:

- **No silent errors**: Invalid operations return `None` or raise clear exceptions based on policy
- **Policy consistency**: Rounding, formatting, and error handling follow configurable policies
- **Calculation traceability**: Dependencies between calculations are explicit and validated
- **Framework integration**: Optional Django plugins and extensible architecture
- **Type safety**: Prevents unit mismatches at compile time with proper type hints

## Development

### Setup

```bash
# Clone and setup virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install with development dependencies
pip install -e .[dev,babel]
```

### Testing

```bash
# Run all tests
make test
# OR
pytest

# Run specific test
pytest tests/unit/test_value.py::test_construct_and_basic_repr_defaults

# Run with coverage
pytest --cov=metricengine
make test  # Includes coverage by default
```

### Code Quality

```bash
# Lint code
make lint
# OR
ruff check .

# Format code
ruff format .

# Type checking (if mypy is installed)
mypy src/metricengine
```

### Documentation

```bash
# Install docs dependencies
pip install .[docs]

# Build documentation
make docs
# OR
cd docs && python -m sphinx -b html . _build/html

# View documentation
open docs/_build/html/index.html
```

## Building and publishing

```bash
python -m build
twine check dist/*
twine upload dist/*
```

## Documentation

Comprehensive documentation is available at [Read the Docs](https://metric-engine.readthedocs.io/) (when published).

Key documentation sections:
- **[Quickstart Guide](docs/quickstart.md)** - Get up and running in 5 minutes
- **[Core Concepts](docs/concepts/)** - Values, Units, Policy, Engine
- **[Tutorials](docs/tutorials/)** - Step-by-step guides for common scenarios
- **[How-To Guides](docs/howto/)** - Solutions for specific problems
- **[API Reference](docs/reference/)** - Complete API documentation

### Framework Integrations

**Django Integration** is provided separately as `metric-engine-django`:

```bash
pip install metric-engine-django
```

The Django integration provides:
- Model fields for values
- Form fields with proper validation
- Admin interface integration
- Template filters for formatting

It registers automatically via the `metricengine.plugins` entry point system.

## License

MIT
