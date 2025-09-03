# Handling Zero Denominators

Strategies for dealing with division by zero in financial calculations.

## Policy-Based Handling

```python
from metricengine import ZeroDivisionPolicy

# Raise exception (strict)
with ZeroDivisionPolicy.RAISE:
    ratio = numerator / denominator

# Return infinity
with ZeroDivisionPolicy.INFINITY:
    ratio = numerator / denominator

# Return zero
with ZeroDivisionPolicy.ZERO:
    ratio = numerator / denominator
```

## Custom Handling

```python
def safe_divide(numerator, denominator, default=None):
    if denominator == 0:
        if default is not None:
            return default
        raise ZeroDivisionError("Cannot divide by zero")
    return numerator / denominator
```

## Business Logic

```python
def debt_to_equity_ratio(debt, equity):
    """Calculate debt-to-equity ratio."""
    if equity == 0:
        # Business rule: infinite leverage
        return float('inf')
    return debt / equity
```
