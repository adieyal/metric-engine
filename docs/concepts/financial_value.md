# Financial Value

The core abstraction in Metric Engine - a type-safe, policy-aware container for financial data that handles arithmetic operations, unit conversions, and null propagation automatically.

## What is a Financial Value?

A `FinancialValue` is an immutable wrapper around financial data that combines:

- **Numerical value** - The amount (automatically converted to `Decimal` for precision)
- **Unit type** - Money, Percent, Ratio, or Dimensionless
- **Policy** - Formatting rules, decimal places, rounding behavior
- **Null safety** - Automatic handling of invalid/missing data

Think of it as a smart number that knows how to behave in financial calculations.

## Core Design Principles

### 1. **Immutability**
Every operation returns a new `FinancialValue` - no mutations, no surprises:

```python
from metricengine import FinancialValue as FV

price = FV(100.00)
total = price * 3  # Creates new FV(300.00), price unchanged
```

### 2. **Type Safety with Units**
Units prevent meaningless operations and ensure mathematical correctness:

```python
from metricengine import money, percent

revenue = money(100_000)
margin = percent(15.5, input="percent")  # 15.5%

# Valid: Money * Percent = Money
profit = revenue * margin  # FV($15,500)

# Invalid: Money + Percent would return None
# invalid = revenue + margin  # None - can't add dollars to percentages
```

### 3. **Automatic Precision Handling**
All values use `Decimal` internally to avoid floating-point errors:

```python
# No precision loss
price = FV(0.1) + FV(0.2)  # Exactly 0.3, not 0.30000000000000004
print(price.as_str())  # "0.30"
```

### 4. **Null Propagation**
Invalid operations return `None` values that propagate safely through calculations:

```python
valid = FV(100)
invalid = FV("invalid_input")  # None

result = valid + invalid  # None (doesn't crash)
final = result * 2        # Still None

print(final.is_none())    # True
```

## Unit System

Metric Engine provides four core unit types, each with specific behaviors:

### Money
Represents currency amounts with automatic formatting:

```python
from metricengine import money

amount = money(1234.56)
print(amount)  # "$1,234.56" (with default policy)

# Money arithmetic rules:
# Money + Money = Money ✓
# Money * Ratio = Money ✓
# Money + Percent = None ✗ (meaningless)
```

### Percent
For percentage values with intelligent display:

```python
from metricengine import percent

# Input as percentage (15.5%)
tax_rate = percent(15.5, input="percent")
print(tax_rate)  # "15.50%"

# Input as ratio (0.155)
growth_rate = percent(0.155, input="ratio")
print(growth_rate)  # "15.50%"

# Both store the same value internally (0.155)
assert tax_rate.as_decimal() == growth_rate.as_decimal()
```

### Ratio
For pure ratios without percentage formatting:

```python
from metricengine import ratio

multiplier = ratio(1.25)
print(multiplier)  # "1.25"

# Useful for calculations that shouldn't display as percentages
debt_to_equity = ratio(0.75)  # Not "75%" - just "0.75"
```

### Dimensionless
For quantities without units:

```python
from metricengine import dimensionless

units_sold = dimensionless(150)
employee_count = dimensionless(42)
```

## Policy-Driven Formatting

Policies control how values are displayed and rounded:

```python
from metricengine import Policy, money

# Custom policy
euro_policy = Policy(
    decimal_places=2,
    currency_symbol="€",
    currency_position="suffix",
    thousands_sep=True
)

amount = money(1234.567, policy=euro_policy)
print(amount)  # "1,234.57 €"
```

## Real-World Example: Revenue Calculation

```python
from metricengine import money, percent, ratio

# Sales data
units_sold = 1_250
unit_price = money(89.99)
discount_rate = percent(12, input="percent")
tax_rate = percent(8.25, input="percent")

# Calculate step by step
gross_revenue = unit_price * units_sold
discount_amount = gross_revenue * discount_rate
net_revenue = gross_revenue - discount_amount
tax_amount = net_revenue * tax_rate
final_revenue = net_revenue + tax_amount

print(f"Gross Revenue: {gross_revenue}")      # "$112,487.50"
print(f"Discount: {discount_amount}")         # "$13,498.50"
print(f"Net Revenue: {net_revenue}")          # "$98,989.00"
print(f"Tax: {tax_amount}")                   # "$8,166.59"
print(f"Final Revenue: {final_revenue}")      # "$107,155.59"

# All operations are type-safe and precision-preserving
```

## Advanced Features

### Safe Division
Division by zero returns `None` instead of crashing:

```python
result = FV(100) / FV(0)
print(result.is_none())  # True

# Configure to raise exceptions instead
from metricengine import NullBinaryMode
with null_binary_mode(NullBinaryMode.RAISE):
    result = FV(100) / FV(0)  # Raises ZeroDivisionError
```

### Policy Inheritance
Operations inherit policies intelligently:

```python
high_precision = Policy(decimal_places=4)
value1 = money(100.1234, policy=high_precision)
value2 = money(200)  # Default policy (2 decimal places)

result = value1 + value2  # Inherits high_precision policy
print(result)  # "$300.1234"
```

### Percentage Conversions
Easy switching between percentage and ratio representations:

```python
growth = percent(15, input="percent")  # 15%
as_ratio = growth.ratio()              # 0.15 (for calculations)
back_to_percent = as_ratio.as_percentage()  # 15% (for display)
```

## Best Practices

### 1. Use Factory Functions
Prefer the factory functions over direct constructor calls:

```python
# Good
revenue = money(100_000)
margin = percent(12.5, input="percent")

# Also valid, but more verbose
from metricengine import FinancialValue, Money, Percent
revenue = FinancialValue(100_000, unit=Money)
```

### 2. Handle Null Values
Always check for None results in uncertain operations:

```python
def safe_divide(a, b):
    result = a / b
    if result.is_none():
        return "Division not possible"
    return result
```

### 3. Use Appropriate Units
Choose the right unit for your use case:

```python
# Good: Clear intent
profit_margin = percent(15, input="percent")    # Display as 15%
price_multiplier = ratio(1.15)                  # Display as 1.15
revenue = money(50_000)                         # Display as $50,000

# Avoid: Confusing mixed units
# margin = ratio(0.15)  # Displays as 0.15, not 15%
```

## Common Patterns

### Financial Calculations
```python
# Revenue growth analysis
q1_revenue = money(250_000)
q2_revenue = money(280_000)

growth_amount = q2_revenue - q1_revenue  # $30,000
growth_rate = (q2_revenue / q1_revenue - ratio(1)).as_percentage()  # 12%
```

### Portfolio Returns
```python
initial_value = money(10_000)
final_value = money(11_500)

total_return = (final_value / initial_value - ratio(1)).as_percentage()
print(f"Total return: {total_return}")  # "15.00%"
```

### Margin Analysis
```python
revenue = money(100_000)
costs = money(75_000)

gross_profit = revenue - costs
margin = (gross_profit / revenue).as_percentage()
print(f"Gross margin: {margin}")  # "25.00%"
```

Financial Values provide the foundation for all calculations in Metric Engine, ensuring your financial computations are accurate, type-safe, and properly formatted.
