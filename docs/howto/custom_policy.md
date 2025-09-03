# Custom Policies

Creating custom policies for calculation behavior.

## Basic Policy

```python
from metricengine.policy import Policy

class MyPolicy(Policy):
    def handle_division_by_zero(self, dividend, divisor):
        # Custom zero division handling
        return 0

    def handle_null_value(self, context):
        # Custom null handling
        return self.default_value
```

## Policy with Configuration

```python
class ConfigurablePolicy(Policy):
    def __init__(self, zero_strategy='raise', null_strategy='skip'):
        self.zero_strategy = zero_strategy
        self.null_strategy = null_strategy

    def handle_division_by_zero(self, dividend, divisor):
        if self.zero_strategy == 'raise':
            raise ZeroDivisionError()
        elif self.zero_strategy == 'return_inf':
            return float('inf')
        return 0
```

## Context Manager

```python
from contextlib import contextmanager

@contextmanager
def my_policy():
    old_policy = get_current_policy()
    set_policy(MyPolicy())
    try:
        yield
    finally:
        set_policy(old_policy)
```
