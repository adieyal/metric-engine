# Cross-Package Dependencies

Managing dependencies between calculation packages.

## Dependency Declaration

```python
# my_package/__init__.py
from metricengine import depends_on

@depends_on(['growth', 'profitability'])
class MyCalculations:
    def complex_metric(self, ...):
        # Use calculations from other packages
        pass
```

## Lazy Loading

Avoid circular dependencies with lazy loading:

```python
def my_calculation():
    from metricengine.calculations.growth import cagr
    return cagr(...)
```

## Best Practices

- Minimize cross-package dependencies
- Use dependency injection where possible
- Document package relationships
- Test dependency resolution
