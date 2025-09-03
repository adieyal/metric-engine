# Creating Domain Packages

How to create domain-specific calculation packages.

## Overview

Domain packages organize related calculations:
- Growth calculations
- Profitability metrics
- Risk assessments
- Custom business logic

## Package Structure

```python
# my_domain/__init__.py
from .calculations import calculate_metric
from .types import CustomValue

__all__ = ['calculate_metric', 'CustomValue']
```

## Calculation Functions

```python
# my_domain/calculations.py
from metricengine import register_calculation

@register_calculation
def my_metric(revenue, cost):
    return (revenue - cost) / revenue
```

## Integration

Register your package with Metric Engine for seamless integration.
