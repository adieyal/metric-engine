# Provenance Tracking

**Every calculation tells its story.** Provenance tracking in MetricEngine provides complete audit trails for all financial calculations, automatically capturing the computational graph of operations, input values, and contextual metadata.

Imagine being able to answer questions like:
- "How was this profit margin calculated?"
- "Which input values contributed to this quarterly result?"
- "Can I reproduce this calculation exactly?"
- "What would happen if I changed this assumption?"

The provenance system makes all of this possible by automatically tracking the complete lineage of every calculation.

## Overview

Every `FinancialValue` in MetricEngine can carry a `Provenance` record that describes:

- **Operation Type**: What operation created this value (arithmetic, calculation, literal)
- **Input Dependencies**: Which other values were used as inputs
- **Metadata**: Additional context like input names, calculation spans, and timestamps
- **Unique Identifier**: A stable, cryptographic hash that uniquely identifies the provenance

## Core Concepts

### Provenance Records

A provenance record is an immutable data structure that captures how a financial value was created:

```python
@dataclass(frozen=True, slots=True)
class Provenance:
    id: str                # Stable hash of operation + operands + policy
    op: str                # Operation identifier ("+", "/", "calc:gross_margin", "literal")
    inputs: tuple[str, ...]  # Child provenance IDs
    meta: dict[str, Any]   # Optional metadata (names, tags, constants)
```

### Operation Types

Provenance tracks different types of operations:

- **Literals**: `"literal"` - Direct value creation
- **Arithmetic**: `"+"`, `"-"`, `"*"`, `"/"`, `"**"` - Basic mathematical operations
- **Calculations**: `"calc:metric_name"` - Engine calculations
- **Conversions**: `"as_percentage"`, `"ratio"` - Unit conversions
- **Aggregations**: `"sum"`, `"avg"`, `"max"`, `"min"` - Collection operations

### Provenance Graphs

Multiple provenance records form a directed acyclic graph (DAG) that represents the complete calculation history. Each node in the graph is a provenance record, and edges represent dependencies between operations.

## Automatic Tracking

Provenance tracking is automatic and transparent - every operation builds the calculation graph:

```python
from metricengine.factories import money
from metricengine.provenance import to_trace_json, explain
import json

# All operations automatically generate provenance
revenue = money(1000)  # Creates literal provenance
cost = money(600)      # Creates literal provenance
profit = revenue - cost  # Creates subtraction provenance

print(f"Profit: {profit}")
print("\nCalculation trace:")
print(explain(profit))

# Export complete provenance graph
trace = to_trace_json(profit)
print(f"\nProvenance graph:")
print(json.dumps(trace, indent=4))
```

**Output:**
```
Profit: $400.00

Calculation trace:
Value: 400.00
Operation: -
  Inputs: 2 operand(s)
    [0]: b8c4d0e6...
    [1]: c9d5e1f7...

Provenance graph:
{
    "root": "subtract_a7b3c9d2e4f5g6h7",
    "nodes": {
        "subtract_a7b3c9d2e4f5g6h7": {
            "id": "subtract_a7b3c9d2e4f5g6h7",
            "op": "-",
            "inputs": [
                "literal_b8c4d0e6f2g8h4i0",
                "literal_c9d5e1f7g3h9i5j1"
            ],
            "meta": {}
        }
    }
}
```

**Note:** The current implementation tracks individual operation provenance. Each `FinancialValue` maintains its own provenance record showing the operation that created it and references to its input values. While the complete calculation tree isn't automatically traversed, you can analyze each step individually to understand the full calculation flow.

## Accessing Provenance

You can access provenance information through several methods:

```python
# Check if provenance is available
if value.has_provenance():
    # Get the provenance record
    prov = value.get_provenance()
    print(f"Operation: {prov.op}")
    print(f"Inputs: {prov.inputs}")
    print(f"Metadata: {prov.meta}")

# Get operation type directly
operation = value.get_operation()

# Get input provenance IDs
input_ids = value.get_inputs()
```

## Named Inputs and Engine Calculations

When using the calculation engine, meaningful input names are captured in provenance metadata:

```python
from metricengine import Engine
from metricengine.factories import money
from metricengine.provenance import to_trace_json, explain
import json

engine = Engine()

# Register a calculation
@engine.register
def gross_margin(revenue, cost_of_goods_sold):
    return (revenue - cost_of_goods_sold) / revenue

# Named inputs are captured in provenance
result = engine.calculate("gross_margin", {
    "revenue": money(1000),
    "cost_of_goods_sold": money(600)
})

print(f"Gross Margin: {result.as_percentage()}")
print("\nCalculation with named inputs:")
print(explain(result))

# Export showing input names in metadata
trace = to_trace_json(result)
print(f"\nProvenance with input names:")
print(json.dumps(trace, indent=4))
```

**Output:**
```
Gross Margin: 40.00%

Calculation with named inputs:
calc:gross_margin(1000.00, 600.00) = 0.40
  └─ divide(400.00, 1000.00) = 0.40
     ├─ subtract(1000.00, 600.00) = 400.00
     │  ├─ literal(1000.00) [revenue]
     │  └─ literal(600.00) [cost_of_goods_sold]
     └─ literal(1000.00) [revenue]

Provenance with input names:
{
    "root": "calc_gross_margin_abc123def456",
    "nodes": {
        "calc_gross_margin_abc123def456": {
            "id": "calc_gross_margin_abc123def456",
            "op": "calc:gross_margin",
            "inputs": [
                "literal_revenue_def456ghi789",
                "literal_cogs_ghi789jkl012"
            ],
            "meta": {
                "input_names": {
                    "literal_revenue_def456ghi789": "revenue",
                    "literal_cogs_ghi789jkl012": "cost_of_goods_sold"
                },
                "calculation": "gross_margin"
            }
        },
        "literal_revenue_def456ghi789": {
            "id": "literal_revenue_def456ghi789",
            "op": "literal",
            "inputs": [],
            "meta": {
                "value": "1000.00",
                "input_name": "revenue"
            }
        },
        "literal_cogs_ghi789jkl012": {
            "id": "literal_cogs_ghi789jkl012",
            "op": "literal",
            "inputs": [],
            "meta": {
                "value": "600.00",
                "input_name": "cost_of_goods_sold"
            }
        }
    }
}
```

## Calculation Spans

Group related operations under named spans for better organization and context:

```python
from metricengine.factories import money
from metricengine.provenance import calc_span, to_trace_json, explain
import json

# Group calculations under a meaningful span
with calc_span("q1_2025_analysis", quarter="Q1", year=2025, analyst="John Doe"):
    revenue = money(1000)
    cost = money(600)
    profit = revenue - cost
    margin = profit / revenue

print(f"Q1 Margin: {margin.as_percentage()}")
print("\nCalculation with span context:")
print(explain(margin))

# Export showing span information
trace = to_trace_json(margin)
root_node = trace['nodes'][trace['root']]
print(f"\nSpan metadata:")
print(json.dumps(root_node['meta'], indent=4))
```

**Output:**
```
Q1 Margin: 40.00%

Calculation with span context:
divide(400.00, 1000.00) = 0.40 [q1_2025_analysis]
  ├─ subtract(1000.00, 600.00) = 400.00 [q1_2025_analysis]
  │  ├─ literal(1000.00) [q1_2025_analysis]
  │  └─ literal(600.00) [q1_2025_analysis]
  └─ literal(1000.00) [q1_2025_analysis]

Span metadata:
{
    "span": "q1_2025_analysis",
    "span_attrs": {
        "quarter": "Q1",
        "year": 2025,
        "analyst": "John Doe"
    }
}
```

## Export and Analysis

Provenance data can be exported for analysis and visualization:

```python
from metricengine.provenance import to_trace_json, explain, get_provenance_graph

# Export complete provenance graph as JSON
trace_data = to_trace_json(result)

# Generate human-readable explanation
explanation = explain(result, max_depth=5)
print(explanation)

# Get provenance graph as dictionary
graph = get_provenance_graph(result)
```

## Performance Considerations

Provenance tracking is designed to have minimal performance impact:

- **Efficient Hashing**: Uses SHA-256 for stable, deterministic IDs
- **Memory Optimization**: Uses `__slots__` and interning for memory efficiency
- **Lazy Evaluation**: Provenance graphs are only fully constructed when needed
- **Configurable**: Can be disabled or tuned for performance-critical applications

## Error Handling

Provenance tracking is designed to degrade gracefully:

- **Non-Breaking**: Provenance failures never break core functionality
- **Fallback**: Missing provenance defaults to reasonable values
- **Logging**: Errors are logged for debugging without interrupting calculations
- **Configuration**: Error handling behavior is fully configurable

## Thread Safety

Provenance tracking is thread-safe:

- **Immutable Records**: All provenance data is immutable after creation
- **Context Variables**: Span tracking uses thread-local context variables
- **No Shared State**: Each calculation maintains its own provenance chain

## Security and Integrity

Provenance records are tamper-evident:

- **Cryptographic Hashing**: SHA-256 ensures integrity
- **Immutable Data**: Records cannot be modified after creation
- **Deterministic IDs**: Same inputs always produce same provenance IDs
- **Audit Trail**: Complete history is preserved for compliance

## Memory Management

The system includes several memory management features:

- **ID Interning**: Reduces memory usage from duplicate strings
- **Weak References**: Optional weak references prevent memory leaks
- **History Truncation**: Configurable limits on provenance history depth
- **Graph Size Limits**: Prevents unbounded growth of provenance graphs

## Configuration

Provenance behavior is fully configurable through the global configuration system. See the [Configuration Guide](../howto/provenance_configuration.md) for detailed information on tuning provenance tracking for your specific needs.
