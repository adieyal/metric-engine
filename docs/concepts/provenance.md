# Provenance Tracking

Provenance tracking in MetricEngine provides complete audit trails for all financial calculations, enabling you to understand exactly how any value was derived. This feature automatically captures the computational graph of operations, including input values, operations performed, and contextual metadata.

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

Provenance tracking is automatic and transparent:

```python
# All operations automatically generate provenance
revenue = FinancialValue(1000)  # Creates literal provenance
cost = FinancialValue(600)      # Creates literal provenance
margin = revenue - cost         # Creates subtraction provenance

# Engine calculations also track provenance
result = engine.calculate("gross_margin", {"revenue": 1000, "cost": 600})
```

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

## Named Inputs

When using the calculation engine, you can provide meaningful names for inputs that will be captured in provenance metadata:

```python
# Named inputs are captured in provenance
result = engine.calculate("gross_margin", {
    "revenue": 1000,
    "cost": 600
})

# The provenance will include input names in metadata
prov = result.get_provenance()
print(prov.meta["input_names"])  # {"input_id_1": "revenue", "input_id_2": "cost"}
```

## Calculation Spans

Group related operations under named spans for better organization:

```python
from metricengine import calc_span

with calc_span("quarterly_analysis", quarter="Q1", year=2025):
    revenue = FinancialValue(1000)
    cost = FinancialValue(600)
    margin = revenue - cost

# All operations within the span include span information in metadata
prov = margin.get_provenance()
print(prov.meta["span"])  # "quarterly_analysis"
print(prov.meta["quarter"])  # "Q1"
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
