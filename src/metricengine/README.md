# FinancialValue - Immutable Financial Data Wrapper

The `FinancialValue` class provides an immutable, policy-aware wrapper for financial calculations with automatic formatting and safe arithmetic operations.

## Import

```python
from metricengine import FinancialValue as FV
```

## Basic Usage

### Creating FinancialValue Instances

```python
# Basic creation
price = FV(100.50)                    # From float
amount = FV("1,234.56")               # From string
quantity = FV(Decimal("42.00"))       # From Decimal
zero = FV.zero()                      # Zero value
missing = FV.none()                   # None/null value
constant = FV.constant(99.99)         # Explicit constant
```

### Default Behavior

```python
# Default policy: 2 decimal places, ROUND_HALF_UP
value = FV(123.456)
print(value.as_decimal())  # Decimal('123.46')
print(value.as_str())      # "123.46"
print(value.as_float())    # 123.46
```

## Arithmetic Operations

### Basic Math

```python
# Addition
revenue = FV(1000)
cost = FV(600)
profit = revenue + cost        # FV(1600)
gross_profit = revenue - cost  # FV(400)

# Multiplication and division
quantity = FV(5)
unit_price = FV(25.50)
total = quantity * unit_price  # FV(127.50)

# Division (safe - returns None for division by zero)
sales = FV(1000)
units = FV(0)
avg_price = sales / units      # FV(None) - safe division by zero

# Power operations
base = FV(2)
exponent = FV(3)
result = base ** exponent      # FV(8)
```

### Mixed Type Operations

```python
# Works with Python numbers
value = FV(100)
result = value + 50            # FV(150)
result = value * 1.5          # FV(150.00)
result = 200 - value          # FV(100)

# Works with strings
result = FV("50") + "25"      # FV(75)
```

### None Propagation

```python
# None values propagate through calculations
missing = FV.none()
value = FV(100)

result = missing + value       # FV(None)
result = value + missing       # FV(None)
result = missing * 0           # FV(None)
```

## Comparison Operations

```python
# Equality
a = FV(100)
b = FV(100)
c = FV(100.0)

print(a == b)                 # True
print(a == c)                 # True
print(a == 100)               # True
print(a == None)              # False

# Ordering
small = FV(50)
large = FV(150)

print(small < large)          # True
print(small <= large)         # True
print(small > large)          # False
print(small >= large)         # False

# None handling in comparisons
missing = FV.none()
print(missing < FV(100))      # True (None sorts before values)
print(missing <= FV(100))     # True
print(FV(100) > missing)      # True
```

## Percentage Handling

```python
# Create percentage values
margin = FV(0.15).as_percentage()  # 15%
ratio = FV(0.25).as_percentage()   # 25%

# Percentage formatting
print(margin.as_str())        # "15%" (default policy)
print(ratio.as_str())         # "25%"

# Convert back to ratio
print(margin.ratio())         # FV(0.15)
print(ratio.ratio())          # FV(0.25)
```

## Policy Configuration

### Custom Policy

```python
from metricengine import Policy

# Create custom policy
custom_policy = Policy(
    decimal_places=4,           # 4 decimal places
    rounding="ROUND_DOWN",      # Round down instead of up
    none_text="N/A",           # Custom text for None values
    percent_style="ratio",      # Show percentages as ratios (0.15) not (15%)
    cap_percentage_at=1000     # Cap percentages at 1000%
)

# Use custom policy
value = FV(123.456789, policy=custom_policy)
print(value.as_str())          # "123.4567" (4 decimals, rounded down)
print(value.as_str())          # "123.4567" (not "123.46")
```

### Policy Inheritance

```python
# Create base value with custom policy
base_policy = Policy(decimal_places=3, none_text="--")
base_value = FV(100.1234, policy=base_policy)

# New values inherit the policy
result = base_value + 50       # Uses base_policy
print(result.policy.decimal_places)  # 3
print(result.as_str())         # "150.123"
```

## Policy Context Management

The `policy_context.py` module provides context-aware policy management for financial calculations, allowing you to control how policies are resolved during operations.

### Context Variables

```python
from metricengine.policy_context import get_policy, get_resolution, PolicyResolution

# Get current context policy and resolution mode
current_policy = get_policy()
resolution_mode = get_resolution()
```

### Policy Resolution Strategies

```python
from metricengine.policy_context import PolicyResolution

# CONTEXT: Use the current context policy (default)
# LEFT_OPERAND: Preserve the left operand's policy during operations
# STRICT_MATCH: Raise an error if policies don't match
```

### Context Managers

```python
from metricengine.policy_context import use_policy, use_policy_resolution

# Temporarily set a policy for a block of code
with use_policy(custom_policy):
    result = FV(100) + FV(200)  # Uses custom_policy
    # ... other operations

# Temporarily set policy resolution mode
with use_policy_resolution(PolicyResolution.LEFT_OPERAND):
    result = value1 + value2  # Preserves value1's policy
```

### Example: Policy Scoping

```python
# Set a high-precision policy for financial calculations
high_precision = Policy(decimal_places=6, rounding="ROUND_HALF_UP")

with use_policy(high_precision):
    # All operations in this block use high_precision
    revenue = FV(1000.123456)
    cost = FV(600.789012)
    profit = revenue - cost

    print(profit.as_str())  # "399.334444" (6 decimal places)

# Outside the block, operations use the default policy
other_value = FV(100.123456)
print(other_value.as_str())  # "100.12" (2 decimal places)
```

## Reduction Operations

The `reductions.py` module provides safe aggregation functions for collections of financial values with configurable null handling.

### Null Reduction Modes

```python
from metricengine.null_behaviour import NullReductionMode

# RAISE: Raise an error if any None values are encountered
# PROPAGATE: Return None if any None values are present
# SKIP: Ignore None values and process only valid values
# ZERO: Treat None values as zero
```

### Sum Operations

```python
from metricengine.reductions import fv_sum

# Basic sum with default null handling
values = [FV(100), FV(200), FV(300)]
total = fv_sum(values)  # FV(600)

# Sum with explicit null handling
values_with_nulls = [FV(100), FV.none(), FV(300)]

# Skip nulls
total_skip = fv_sum(values_with_nulls, mode=NullReductionMode.SKIP)  # FV(400)

# Propagate nulls
total_propagate = fv_sum(values_with_nulls, mode=NullReductionMode.PROPAGATE)  # FV(None)

# Treat nulls as zero
total_zero = fv_sum(values_with_nulls, mode=NullReductionMode.ZERO)  # FV(400)

# Raise on nulls
try:
    total_raise = fv_sum(values_with_nulls, mode=NullReductionMode.RAISE)
except ValueError as e:
    print(f"Error: {e}")  # "Error: Reduction encountered None"
```

### Mean Operations

```python
from metricengine.reductions import fv_mean

# Calculate mean with null handling
prices = [FV(10.50), FV(15.75), FV(12.25), FV.none()]

# Skip nulls and calculate mean of valid values
avg_skip = fv_mean(prices, mode=NullReductionMode.SKIP)  # FV(12.83)

# Return None if any nulls present
avg_propagate = fv_mean(prices, mode=NullReductionMode.PROPAGATE)  # FV(None)

# Treat nulls as zero
avg_zero = fv_mean(prices, mode=NullReductionMode.ZERO)  # FV(9.63)
```

### Mixed Type Support

```python
# Reductions work with mixed types
mixed_values = [FV(100), 200, 300.5, "400", None]

# Automatic type conversion and policy selection
total = fv_sum(mixed_values, mode=NullReductionMode.SKIP)
print(total.as_str())  # "1000.50"

# Explicit policy override
custom_policy = Policy(decimal_places=3)
total_custom = fv_sum(mixed_values, policy=custom_policy)
print(total_custom.as_str())  # "1000.500"
```

### Policy Resolution in Reductions

```python
# Reductions automatically select the appropriate policy
values = [FV(100, policy=Policy(decimal_places=2)),
          FV(200, policy=Policy(decimal_places=4))]

# Uses the first non-None FinancialValue's policy
result = fv_sum(values)
print(result.policy.decimal_places)  # 2

# Override with explicit policy
result_custom = fv_sum(values, policy=Policy(decimal_places=6))
print(result_custom.policy.decimal_places)  # 6
```

## Real-World Examples

### Sales Calculations

```python
# Calculate order totals
def calculate_order_total(items):
    total = FV.zero()
    for item in items:
        quantity = FV(item['quantity'])
        unit_price = FV(item['unit_price'])
        line_total = quantity * unit_price
        total = total + line_total
    return total

# Usage
items = [
    {'quantity': 2, 'unit_price': 15.99},
    {'quantity': 1, 'unit_price': 29.99},
    {'quantity': 3, 'unit_price': 5.50}
]

order_total = calculate_order_total(items)
print(f"Order total: ${order_total.as_str()}")  # "Order total: $82.97"
```

### Financial Ratios

```python
def calculate_gross_margin(revenue, cost):
    if revenue.is_none() or cost.is_none():
        return FV.none()

    gross_profit = revenue - cost
    margin = (gross_profit / revenue).as_percentage()
    return margin

# Usage
revenue = FV(10000)
cost = FV(6000)
margin = calculate_gross_margin(revenue, cost)
print(f"Gross margin: {margin.as_str()}")  # "Gross margin: 40%"
```

### Safe Aggregations

```python
def safe_average(values):
    if not values:
        return FV.none()

    total = FV.zero()
    count = 0

    for value in values:
        if not value.is_none():
            total = total + value
            count += 1

    if count == 0:
        return FV.none()

    return total / FV(count)

# Usage
prices = [FV(10.50), FV.none(), FV(15.75), FV(12.25)]
avg_price = safe_average(prices)
print(f"Average price: ${avg_price.as_str()}")  # "Average price: $12.83"
```

### Advanced Aggregation with Context

```python
from metricengine.reductions import fv_sum, fv_mean
from metricengine.policy_context import use_policy

def analyze_financial_data(data_points):
    # Use high-precision policy for analysis
    analysis_policy = Policy(decimal_places=6, rounding="ROUND_HALF_UP")

    with use_policy(analysis_policy):
        # Extract financial values
        revenues = [point['revenue'] for point in data_points]
        costs = [point['cost'] for point in data_points]

        # Calculate aggregates with null handling
        total_revenue = fv_sum(revenues, mode=NullReductionMode.SKIP)
        total_cost = fv_sum(costs, mode=NullReductionMode.SKIP)
        avg_revenue = fv_mean(revenues, mode=NullReductionMode.SKIP)

        # Calculate profit margin
        if not total_revenue.is_none() and not total_cost.is_none():
            profit = total_revenue - total_cost
            margin = (profit / total_revenue).as_percentage()
        else:
            margin = FV.none()

        return {
            'total_revenue': total_revenue,
            'total_cost': total_cost,
            'avg_revenue': avg_revenue,
            'profit_margin': margin
        }

# Usage
data = [
    {'revenue': FV(1000.50), 'cost': FV(600.25)},
    {'revenue': FV(1500.75), 'cost': FV(900.50)},
    {'revenue': FV.none(), 'cost': FV(750.00)},  # Missing revenue data
    {'revenue': FV(800.25), 'cost': FV(500.75)}
]

results = analyze_financial_data(data)
print(f"Total Revenue: ${results['total_revenue'].as_str()}")
print(f"Total Cost: ${results['total_cost'].as_str()}")
print(f"Average Revenue: ${results['avg_revenue'].as_str()}")
print(f"Profit Margin: {results['profit_margin'].as_str()}")
```

## Error Handling

```python
# Invalid conversions raise TypeError
try:
    invalid = FV("not a number")
except TypeError as e:
    print(f"Error: {e}")  # "Error: Cannot convert 'not a number' to Decimal: ..."

# Division by zero returns None (safe)
result = FV(100) / FV(0)
print(result.is_none())  # True
print(result.as_str())   # "—" (or custom none_text)

# Policy conflicts can be handled with resolution modes
try:
    with use_policy_resolution(PolicyResolution.STRICT_MATCH):
        value1 = FV(100, policy=Policy(decimal_places=2))
        value2 = FV(200, policy=Policy(decimal_places=4))
        result = value1 + value2  # May raise error depending on implementation
except Exception as e:
    print(f"Policy conflict: {e}")
```

## Best Practices

1. **Use the alias**: `from metricengine import FinancialValue as FV` for cleaner code
2. **Immutable by design**: All operations return new instances
3. **Policy inheritance**: New values inherit policy from operands
4. **Safe operations**: Division by zero and invalid operations return `None`
5. **Type flexibility**: Accepts int, float, str, Decimal, or other FinancialValue instances
6. **None propagation**: Missing values propagate naturally through calculations
7. **Context management**: Use `use_policy()` for temporary policy overrides
8. **Null handling**: Choose appropriate null reduction modes for your use case
9. **Policy resolution**: Understand how policies are resolved during operations
10. **Aggregation safety**: Use reduction functions for safe collection operations

## Performance Notes

- `FinancialValue` instances are immutable and hashable
- Arithmetic operations create new instances (consider this for high-frequency operations)
- Policy objects are shared and immutable, so memory overhead is minimal
- String formatting is lazy - only computed when `as_str()` is called
- Context variables provide efficient policy switching without object creation
- Reduction functions optimize policy selection and null handling
