# Quickstart Guide

Get up and running with Metric Engine in 5 minutes. This guide covers the essential features you need to start building financial applications with confidence.

## Installation

```bash
pip install metric-engine
```

For development or documentation features:
```bash
pip install metric-engine[dev]  # Includes docs, testing tools
pip install metric-engine[babel]  # Adds international formatting
```

## Core Concepts

Metric Engine revolves around **type-safe financial values** that carry their units and formatting policies. Think of it as supercharged numbers that know whether they represent money, percentages, or ratios.

## Basic Financial Values

### Creating Values

```python
from metricengine import FV
from metricengine.units import Money, Percent, Ratio

# Create monetary amounts
revenue = FV(150000, Money)
cost = FV(90000, Money)

# Create percentages and ratios
tax_rate = FV(0.25, Percent)  # 25%
growth_rate = FV(0.15, Ratio)  # 15% as ratio (0.15)

print(revenue)      # $150,000.00
print(tax_rate)     # 25.00%
print(growth_rate)  # 0.15
```

### Safe Arithmetic

All operations are **null-safe** and **unit-aware**:

```python
# Standard calculations
gross_profit = revenue - cost
net_income = gross_profit * (1 - tax_rate)

print(f"Gross Profit: {gross_profit}")  # $60,000.00
print(f"Net Income: {net_income}")      # $45,000.00

# Handle missing data gracefully
incomplete_data = FV(None, Money)
safe_result = revenue + incomplete_data  # Returns None, doesn't crash
print(safe_result.is_none())            # True
```

### Unit Safety

The type system prevents common errors:

```python
# This works - same units
total_cost = cost + FV(5000, Money)

# This fails gracefully - mixed units
# mixed = revenue + tax_rate  # Would return None or raise based on policy
```

## Factory Functions (Recommended)

For more convenient value creation:

```python
from metricengine.factories import money, percent, ratio

# Cleaner syntax
revenue = money(150000)
margin = percent(15, input="percent")  # 15% -> stored as 0.15
growth = ratio(0.12)

# Arithmetic just works
projected_revenue = revenue * (1 + growth)
print(f"Projected: {projected_revenue}")  # $168,000.00
```

## Working with Calculations

### Built-in Calculation Engine

```python
from metricengine import Engine

# Create an engine for calculations
engine = Engine()

# Define your data
context = {
    "sales": money(100000),
    "cost": money(65000),
    "operating_expenses": money(20000)
}

# Let the engine calculate dependencies
gross_profit = engine.calculate("profitability.gross_profit", context)
operating_margin = engine.calculate("profitability.operating_margin", context)

print(f"Gross Profit: {gross_profit}")      # $35,000.00
print(f"Operating Margin: {operating_margin}")  # 15.00%
```

### Custom Calculations

Register your own business logic:

```python
from metricengine import calc
from metricengine.units import Money, Ratio

@calc("monthly_revenue", depends_on=("annual_revenue",))
def monthly_revenue(annual_revenue: FV[Money]) -> FV[Money]:
    """Calculate monthly revenue from annual."""
    if annual_revenue.is_none():
        return FV.none().money()
    return (annual_revenue / 12).money()

# Use your calculation
context = {"annual_revenue": money(1200000)}
monthly = engine.calculate("monthly_revenue", context)
print(f"Monthly Revenue: {monthly}")  # $100,000.00
```

## Policy-Driven Formatting

Control how values display across your application:

```python
from metricengine.policy import Policy

# Create custom formatting policies
high_precision = Policy(decimal_places=4)
accounting_format = Policy(
    decimal_places=2,
    currency_symbol="$",
    negative_parentheses=True
)

# Apply policies to values
precise_rate = FV(0.123456, Ratio, policy=high_precision)
loss = FV(-5000, Money, policy=accounting_format)

print(precise_rate)  # 0.1235
print(loss)          # ($5,000.00)
```

## Real-World Example: Financial Dashboard

Here's a complete example calculating key business metrics:

```python
from metricengine import Engine
from metricengine.factories import money, ratio

# Initialize engine and data
engine = Engine()

# Q1 Financial Data
financial_data = {
    "sales": money(850000),
    "cost_of_goods_sold": money(510000),
    "operating_expenses": money(180000),
    "interest_expense": money(15000),
    "tax_rate": ratio(0.21),
}

# Calculate key metrics using built-in calculations
metrics = {}
metrics["gross_profit"] = engine.calculate("profitability.gross_profit", financial_data)
metrics["gross_margin"] = engine.calculate("profitability.gross_margin", financial_data)
metrics["operating_profit"] = engine.calculate("profitability.operating_profit", financial_data)
metrics["operating_margin"] = engine.calculate("profitability.operating_margin", financial_data)

# Display results
print("Q1 Financial Summary")
print("=" * 30)
for name, value in metrics.items():
    print(f"{name.replace('_', ' ').title()}: {value}")

# Output:
# Q1 Financial Summary
# ==============================
# Gross Profit: $340,000.00
# Gross Margin: 40.00%
# Operating Profit: $160,000.00
# Operating Margin: 18.82%
```

## Error Handling & Validation

Metric Engine handles edge cases gracefully:

```python
# Division by zero
safe_ratio = money(100) / money(0)  # Returns None instead of crashing
print(safe_ratio.is_none())  # True

# Invalid input
invalid_amount = money("not_a_number")  # Returns None
print(invalid_amount.is_none())  # True

# Strict mode for validation
from metricengine.policy import Policy
strict_policy = Policy(arithmetic_strict=True)

# This would raise CalculationError instead of returning None
# risky_calc = FV(100, Money, policy=strict_policy) / FV(0, Money, policy=strict_policy)
```

## Next Steps

Now that you've seen the basics, explore these areas:

### 📚 **Core Concepts**
- [Financial Value](concepts/financial_value.md) - Deep dive into the core abstraction
- [Units](concepts/units.md) - Money, Percent, Ratio, and Dimensionless types
- [Policy](concepts/policy.md) - Control formatting and behavior

### 🎓 **Tutorials**
- [Complete Tour](tutorials/tour.md) - Comprehensive walkthrough
- [Money, Tax & Percentages](tutorials/money_tax_percent.md) - Common scenarios
- [Building Domain Packages](tutorials/domain_package.md) - Organize calculations

### 🔧 **How-To Guides**
- [Custom Calculations](howto/new_calc.md) - Register business logic
- [Custom Units](howto/new_unit.md) - Create domain-specific types
- [Testing Financial Code](howto/testing_calcs.md) - Best practices

### 🏗️ **Architecture**
- [Calculation Engine](concepts/engine.md) - Dependency resolution
- [Collections & Registry](concepts/registry_collections.md) - Organization
- [Null Behavior](concepts/null_behaviour.md) - Handling missing data

Ready to build robust financial applications! 🚀
