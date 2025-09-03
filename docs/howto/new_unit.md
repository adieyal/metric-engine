# Creating New Units

How to add custom unit types to the system.

## Basic Unit

```python
from metricengine.units import register_unit, Unit

@register_unit
class Shares(Unit):
    """Stock shares unit."""
    symbol = "shares"
    dimension = "count"

    def __str__(self):
        return f"{self.value} {self.symbol}"
```

## Unit with Conversions

```python
@register_unit
class Points(Unit):
    """Basis points (1/100th of a percent)."""
    symbol = "bp"
    dimension = "percentage"

    def to_percentage(self):
        return Percentage(self.value / 100)

    @classmethod
    def from_percentage(cls, percent):
        return cls(percent.value * 100)
```

## Validation

```python
@register_unit
class PositiveShares(Shares):
    """Shares that must be positive."""

    def __init__(self, value):
        if value <= 0:
            raise ValueError("Shares must be positive")
        super().__init__(value)
```
