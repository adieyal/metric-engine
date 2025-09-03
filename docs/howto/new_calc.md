# How to Create New Calculations

Step-by-step guide to adding new calculation functions.

## Basic Calculation

```python
from metricengine import register_calculation

@register_calculation
def roi(revenue, cost):
    """Calculate Return on Investment."""
    return (revenue - cost) / cost * 100
```

## With Type Hints

```python
from metricengine import Money, Percentage

@register_calculation
def roi(revenue: Money, cost: Money) -> Percentage:
    """Calculate Return on Investment."""
    return (revenue - cost) / cost * 100
```

## Validation

Add input validation for robust calculations:

```python
@register_calculation
def roi(revenue: Money, cost: Money) -> Percentage:
    if cost <= 0:
        raise ValueError("Cost must be positive")
    return (revenue - cost) / cost * 100
```

## Registration

Register calculations in appropriate modules for discovery.
