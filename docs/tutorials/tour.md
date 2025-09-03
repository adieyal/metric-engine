# Metric Engine Tour

A comprehensive tour of Metric Engine's capabilities.

## Getting Started

```python
from metricengine import Money, Percentage
```

## Basic Operations

### Creating Values

```python
# Monetary values
principal = Money(1000, "USD")
rate = Percentage(5.0)

# Calculations
interest = principal * rate / 100
```

### Working with Policies

```python
from metricengine import strict_policy

with strict_policy():
    result = calculate_roi(revenue, cost)
```

## Advanced Features

- Custom calculations
- Policy configuration
- Unit conversions
- Error handling

## Next Steps

Continue with specific tutorials for detailed topics.
