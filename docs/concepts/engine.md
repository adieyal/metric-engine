# Calculation Engine

The heart of Metric Engine: dependency-driven, policy-aware, and robust financial computation.

## What is the Calculation Engine?

The **Engine** is the orchestrator that evaluates financial calculations, resolves dependencies, enforces policies, and ensures correctness. It builds a dependency graph (DAG), executes calculations in the right order, and handles nulls and errors gracefully.

## Why Use the Engine?

- **Automatic dependency resolution**: Just specify what you want to compute; the engine figures out the rest.
- **Policy enforcement**: All calculations respect your formatting, rounding, and error-handling policies.
- **Null safety**: Missing or invalid data propagates safely—no crashes, no surprises.
- **Batch evaluation**: Compute many metrics at once, with shared dependency resolution and caching.
- **Extensibility**: Plug in your own calculations and policies.

## How the Engine Works

- **Dependency Graph**: The engine analyzes calculation dependencies and builds a directed acyclic graph (DAG).
- **Topological Execution**: Calculations are executed in dependency order, so all prerequisites are computed first.
- **Null Propagation**: If any input is missing or invalid, the result is a `FinancialValue(None)`—never a crash.
- **Policy Selection**: Policies can be set globally, per-engine, per-metric, or per-call.
- **Error Handling**: You can choose to raise exceptions or allow partial results with `allow_partial=True`.

## Usage Examples

### Basic Calculation

```python
from metricengine import Engine

engine = Engine()

# Compute a single metric
gross_profit = engine.calculate("gross_profit", sales=1000, cost=650)
print(gross_profit)  # e.g., $350.00
```

### Batch Calculation

```python
results = engine.calculate_many(
    {"gross_profit", "gross_margin_percentage"},
    sales=1000, cost=650
)
print(results["gross_profit"])            # $350.00
print(results["gross_margin_percentage"]) # 35.00%
```

### Using Context Dictionaries

```python
context = {"sales": 1000, "cost": 650}
result = engine.calculate("gross_profit", ctx=context)
```

### Handling Missing Data

```python
try:
    result = engine.calculate("gross_profit", cost=650)  # Missing 'sales'
except Exception as e:
    print(f"Error: {e}")

# Or allow partial results (returns None for missing)
result = engine.calculate("gross_profit", cost=650, allow_partial=True)
print(result.is_none())  # True
```

### Custom Policies

```python
from metricengine import Policy

custom_policy = Policy(decimal_places=3)
result = engine.calculate("gross_profit", sales=1000, cost=650, policy=custom_policy)
print(result)  # $350.000
```

## Advanced Features

- **Constant and Zero Values**: `engine.constant(42)`, `engine.zero()`, `engine.none()`
- **Dependency Inspection**: `engine.get_dependencies("gross_profit")` returns all dependencies
- **Validation**: `engine.validate_dependencies("gross_profit")` checks for missing or circular dependencies
- **Per-metric Policy**: `engine.set_metric_policy("gross_profit", custom_policy)`

## Extending the Engine

You can subclass `Engine` to customize calculation behavior, logging, or error handling. You can also register your own calculations and policies.

```python
from metricengine import Engine

class MyEngine(Engine):
    def _run_calc(self, name, ctx, allow_partial=False):
        # Custom logic here
        return super()._run_calc(name, ctx, allow_partial=allow_partial)
```

## Best Practices

- **Declare all required inputs** for calculations
- **Use batch calculation** (`calculate_many`) for efficiency when computing multiple metrics
- **Set policies at the right level** (global, per-engine, per-metric, or per-call)
- **Handle None results** gracefully in your application logic
- **Validate dependencies** when adding new calculations

## Common Pitfalls

- Forgetting to provide required inputs will raise `MissingInputError` (unless `allow_partial=True`)
- Circular dependencies are not allowed and will raise `CircularDependencyError`
- Registering calculations with the same name will raise an error

## Real-World Patterns

- **Financial Reporting**: Compute all KPIs for a report in one batch for consistency and performance
- **Scenario Analysis**: Swap input contexts to model different business scenarios
- **Custom Engines**: Extend the engine for domain-specific logic, logging, or integration

---

The Calculation Engine is the backbone of Metric Engine—use it to build robust, maintainable, and extensible financial applications with confidence.
