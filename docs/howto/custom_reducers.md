# Custom Reducers

Creating custom reduction operations for financial data.

## Basic Reducer

```python
from metricengine.reductions import register_reducer

@register_reducer
def weighted_average(values, weights):
    """Calculate weighted average."""
    total_weight = sum(weights)
    weighted_sum = sum(v * w for v, w in zip(values, weights))
    return weighted_sum / total_weight
```

## Null-Aware Reducer

```python
@register_reducer
def safe_sum(values):
    """Sum values, skipping nulls."""
    return sum(v for v in values if v is not None)
```

## Type-Specific Reducers

```python
from metricengine import Money

@register_reducer
def sum_money(values: list[Money]) -> Money:
    """Sum monetary values with currency validation."""
    if not values:
        return Money(0, "USD")

    currency = values[0].currency
    total = sum(v.amount for v in values if v.currency == currency)
    return Money(total, currency)
```
