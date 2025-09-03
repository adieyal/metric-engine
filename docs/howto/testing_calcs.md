# Testing Calculations

Best practices for testing financial calculations.

## Basic Test Structure

```python
import pytest
from metricengine import Money, Percentage

def test_roi_calculation():
    revenue = Money(120, "USD")
    cost = Money(100, "USD")

    result = roi(revenue, cost)

    assert result == Percentage(20)
```

## Edge Cases

```python
def test_roi_zero_cost():
    revenue = Money(100, "USD")
    cost = Money(0, "USD")

    with pytest.raises(ZeroDivisionError):
        roi(revenue, cost)
```

## Parameterized Tests

```python
@pytest.mark.parametrize("revenue,cost,expected", [
    (Money(120, "USD"), Money(100, "USD"), Percentage(20)),
    (Money(100, "USD"), Money(100, "USD"), Percentage(0)),
    (Money(80, "USD"), Money(100, "USD"), Percentage(-20)),
])
def test_roi_cases(revenue, cost, expected):
    assert roi(revenue, cost) == expected
```

## Policy Testing

```python
def test_roi_with_strict_policy():
    with strict_policy():
        # Test behavior under strict policy
        pass
```
