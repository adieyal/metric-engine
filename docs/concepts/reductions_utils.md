# Reductions & Utilities

Robust, policy-aware aggregation and helper functions for financial data.

## What Are Reductions Utilities?

**Reductions** are operations that combine multiple values into a single result—like sum, mean, or weighted mean. In Metric Engine, reductions are:
- **Type-safe**: Work with FinancialValue objects and units
- **Policy-driven**: Respect formatting, rounding, and null-handling policies
- **Null-safe**: Flexible handling of missing or invalid data

**Utilities** are helper functions for validation, formatting, and type conversion, supporting robust financial workflows.

## Why Use Reductions?

- **Aggregate financial data** (e.g., total revenue, average margin)
- **Handle missing data** gracefully (skip, propagate, treat as zero, or raise)
- **Enforce consistent policies** across all calculations
- **Support advanced analytics** (weighted averages, custom aggregations)

## How Reductions Work

Reductions utilities operate on sequences of values (numbers or FinancialValue objects) and:
- Choose the correct policy and unit for the result
- Handle None/missing values according to the current null reduction mode:
  - **SKIP**: Ignore None values (default)
  - **PROPAGATE**: Any None → result is None
  - **ZERO**: Treat None as zero
  - **RAISE**: Raise an error if any None is present
- Return a FinancialValue with the correct type, unit, and policy

## Usage Examples

### Summing Financial Values

```python
from metricengine.reductions import fv_sum
from metricengine import money

amounts = [money(100), money(200), None, money(50)]
total = fv_sum(amounts)  # SKIP mode by default
print(total)  # $350.00
```

### Mean (Average) Calculation

```python
from metricengine.reductions import fv_mean

values = [money(100), money(200), None]
avg = fv_mean(values)  # SKIP mode: ignores None
print(avg)  # $150.00
```

### Weighted Mean

```python
from metricengine.reductions import fv_weighted_mean

# (value, weight) pairs
pairs = [(money(100), 2), (money(200), 1), (None, 3)]
weighted = fv_weighted_mean(pairs)  # SKIP mode: skips pairs with None
print(weighted)  # $133.33
```

### Custom Null Handling

```python
from metricengine.reductions import fv_sum, fv_mean
from metricengine.null_behaviour import NullReductionMode

# Propagate: any None → result is None
result = fv_sum([money(100), None], mode=NullReductionMode.PROPAGATE)
print(result.is_none())  # True

# Zero: treat None as zero
result = fv_mean([money(100), None, money(200)], mode=NullReductionMode.ZERO)
print(result)  # $100.00 (mean of 100, 0, 200)
```

## Best Practices

- **Use FinancialValue objects** for type safety and policy enforcement
- **Choose the right null handling mode** for your use case
- **Document your aggregation logic** for maintainability
- **Validate input data** before aggregation if needed

## Common Pitfalls

- Forgetting to handle None values can lead to unexpected results
- Using PROPAGATE or RAISE modes without checking for missing data may cause errors
- Mixing units in a single reduction is not allowed—ensure all values are compatible

## Real-World Patterns

- **Portfolio analysis**: Aggregate returns, calculate weighted averages
- **Financial reporting**: Sum revenues, compute average margins
- **Data cleaning**: Use SKIP or ZERO modes to handle incomplete datasets

---

Reductions utilities are essential for robust, maintainable, and policy-consistent financial analytics in Metric Engine. Use them to aggregate, analyze, and report on your financial data with confidence.
