# Equality and Hashing

Design for value equality and hashing in Metric Engine.

## Equality Semantics

### Value Equality
Two financial values are equal if:
- Same numerical value
- Same unit type
- Same currency (for monetary values)

### Approximate Equality
For floating-point values:
- Configurable tolerance (default: 1e-6)
- Relative vs absolute comparison
- Unit-aware comparison

## Hashing Strategy

```python
class FinancialValue:
    def __hash__(self):
        return hash((
            round(self.value, 6),  # Normalized precision
            self.unit.symbol,
            self.unit.dimension
        ))
```

## Equality Modes

- **Strict**: Exact equality only
- **Approximate**: Floating-point tolerant
- **Unit-aware**: Consider unit compatibility

## Use Cases

- Set membership
- Dictionary keys
- Comparison operations
- Sorting algorithms

## Performance

- Cached hash values
- Fast path for same-object comparison
- Optimized unit comparison
