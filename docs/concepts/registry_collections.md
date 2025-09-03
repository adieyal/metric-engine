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

A collection is created by instantiating the `Collection` class with a namespace. You then use the `.calc()` decorator to register functions under that namespace, optionally specifying dependencies.

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
from metricengine.calculations import growth

cagr = growth.compound_annual_growth_rate(start_value, end_value, years)
```

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

my_metrics = Collection("my_metrics")

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

## Real-World Example: Custom Domain Package

Suppose you want to add a set of KPIs for your business domain:

```python
from metricengine.registry_collections import Collection

kpi = Collection("my_kpi")

@kpi.calc("customer_lifetime_value", depends_on=("avg_purchase_value", "purchase_frequency", "customer_lifespan"))
def customer_lifetime_value(avg_purchase_value, purchase_frequency, customer_lifespan):
    return avg_purchase_value * purchase_frequency * customer_lifespan
```

Now you can use `customer_lifetime_value` as part of your calculation engine, with all dependencies resolved automatically.

---

Registry Collections are the foundation for building robust, modular, and maintainable financial calculation libraries in Metric Engine. Use them to organize your logic, manage dependencies, and extend the metric engine for your own domain needs.
