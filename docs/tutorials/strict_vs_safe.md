# Strict vs Safe Mode

Understanding the difference between strict and safe calculation modes.

## Strict Mode

Strict mode provides:
- Fail-fast behavior
- Type validation
- Unit checking
- Error propagation

```python
from metricengine import strict_policy

with strict_policy():
    # Will raise on any validation error
    result = risky_calculation()
```

## Safe Mode

Safe mode offers:
- Graceful degradation
- Warning instead of errors
- Default value fallbacks
- Continued execution

```python
from metricengine import safe_policy

with safe_policy():
    # Will warn and continue with defaults
    result = risky_calculation()
```

## When to Use Each

- **Strict**: Production calculations, critical operations
- **Safe**: Data exploration, batch processing
