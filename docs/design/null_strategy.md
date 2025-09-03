# Null Strategy Design

Design decisions around null value handling.

## Null Representation

Metric Engine uses:
- `None` for missing values
- `NaN` for invalid calculations
- Custom `Null` type for typed nulls

## Strategy Pattern

```python
class NullStrategy:
    def handle_null(self, value, context):
        raise NotImplementedError

class RaiseStrategy(NullStrategy):
    def handle_null(self, value, context):
        raise NullValueError()

class SkipStrategy(NullStrategy):
    def handle_null(self, value, context):
        return SKIP_MARKER
```

## Integration Points

- Input validation
- Calculation operations
- Output formatting
- Aggregation functions

## Trade-offs

- **Performance**: Null checks add overhead
- **Safety**: Explicit null handling prevents errors
- **Usability**: Different strategies for different use cases
