# Registry Collections

Organize, extend, and manage financial calculations by domain.

## What Are Registry Collections?

A **Registry Collection** is a namespace for grouping related financial calculations in Metric Engine. Collections help you:
- Organize calculations by domain (e.g., profitability, growth, inventory)
- Register functions with explicit names and dependencies
- Build extensible, maintainable calculation libraries
- Avoid naming collisions and enable modularity

Think of a collection as a toolbox for a specific domain—each with its own set of calculation tools.

## Why Use Collections?

- **Clarity**: Group related calculations for easier discovery and maintenance
- **Extensibility**: Add or override calculations in your own domain packages
- **Dependency Management**: Explicitly declare calculation dependencies for safe, automatic resolution
- **Isolation**: Prevent accidental name clashes between unrelated calculations

## How Collections Work

A collection is created by instantiating the `Collection` class with a
namespace. You then use the `.calc()` decorator to register functions under
that namespace, optionally specifying dependencies.

Collections bind to a registry at creation time:
- `Collection("name")` uses the active registration context when one exists
- otherwise it falls back to the shared `default_registry`
- `Collection("name", registry=my_registry)` binds explicitly to a specific registry

### Example: Defining a Collection

```python
from metricengine.registry_collections import Collection

profitability = Collection("profitability")

@profitability.calc("gross_profit", depends_on=("sales", "cost"))
def gross_profit(sales, cost):
    return sales - cost

@profitability.calc("net_profit", depends_on=("gross_profit", "expenses"))
def net_profit(gross_profit, expenses):
    return gross_profit - expenses
```

- Each calculation is registered with a unique name (e.g., `gross_profit`)
- Dependencies are declared by name, enabling automatic resolution
- Built-in calculation modules declare their collections explicitly via
  `__collections__` so they can be loaded into any registry instance

## Built-in Collections

Metric Engine provides several built-in collections:

- **growth**: Growth rate calculations
- **profitability**: Margin and profitability metrics
- **ratios**: Financial ratio calculations
- **inventory**: Inventory management calculations
- **pricing**: Price-related calculations
- **variance**: Variance and volatility metrics
- **utilities**: Miscellaneous helpers

You can import and use these collections directly:

```python
from metricengine import Engine
from metricengine.calculations import load_all
from metricengine.registry import Registry

registry = Registry()
load_all(registry)
engine = Engine(registry=registry)

cagr = engine.calculate(
    "compound_growth_rate",
    initial_value=100,
    final_value=150,
    periods=3,
)
```

Calling `load_all()` with no arguments still loads the built-in calculations
into `default_registry` for compatibility with the module-level API.

## Dependency Management

Each calculation can declare dependencies on other calculations by name. The registry engine:
- Resolves dependencies automatically when evaluating calculations
- Detects and prevents circular dependencies
- Allows you to build complex calculation graphs safely

### Example: Dependency Graph

```python
@profitability.calc("operating_margin", depends_on=("operating_income", "sales"))
def operating_margin(operating_income, sales):
    return operating_income / sales
```

- When you request `operating_margin`, the engine ensures `operating_income` and `sales` are computed first.

## Extending with Custom Collections

You can define your own collections for domain-specific logic:

```python
from metricengine.registry_collections import Collection

my_metrics = Collection("my_metrics", registry=engine.registry)

@my_metrics.calc("custom_kpi", depends_on=("input1", "input2"))
def custom_kpi(input1, input2):
    # Your custom calculation
    return (input1 + input2) / 2
```

- Use a unique namespace to avoid conflicts
- Register as many calculations as needed

## Best Practices

- **Use clear, descriptive names** for calculations
- **Declare all dependencies** explicitly for safety and traceability
- **Group related calculations** in the same collection
- **Avoid circular dependencies**—the engine will detect and prevent them
- **Document your collections** for maintainability

## Common Pitfalls

- Registering two calculations with the same name in the same collection will raise an error
- Forgetting to declare a dependency may result in missing or incorrect results
- Circular dependencies are not allowed and will be detected at registration
- Assuming module-level `@calc(...)` decorators automatically appear in private
  engines will lead to missing-calculation errors; use `engine.registry.calc(...)`
  or pass `registry=default_registry` if you want explicit sharing

## Real-World Example: Custom Domain Package

Suppose you want to add a set of KPIs for your business domain:

```python
from metricengine.registry_collections import Collection

kpi = Collection("my_kpi", registry=engine.registry)

@kpi.calc("customer_lifetime_value", depends_on=("avg_purchase_value", "purchase_frequency", "customer_lifespan"))
def customer_lifetime_value(avg_purchase_value, purchase_frequency, customer_lifespan):
    return avg_purchase_value * purchase_frequency * customer_lifespan
```

Now you can use `customer_lifetime_value` as part of your calculation engine, with all dependencies resolved automatically.

---

Registry Collections are the foundation for building robust, modular, and maintainable financial calculation libraries in Metric Engine. Use them to organize your logic, manage dependencies, and extend the metric engine for your own domain needs.
