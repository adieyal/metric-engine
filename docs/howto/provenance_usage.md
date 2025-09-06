# Using Provenance Tracking

This guide provides practical examples of how to use provenance tracking in MetricEngine for debugging, auditing, and understanding complex financial calculations.

## Basic Usage

### Automatic Provenance Tracking

Provenance tracking works automatically without any code changes:

```python
from metricengine import FinancialValue

# Create values - provenance is tracked automatically
revenue = FinancialValue(1000)
cost = FinancialValue(600)
margin = revenue - cost

# Check if provenance is available
if margin.has_provenance():
    prov = margin.get_provenance()
    print(f"Operation: {prov.op}")  # "-"
    print(f"Inputs: {prov.inputs}")  # IDs of revenue and cost provenance
```

### Accessing Provenance Information

```python
# Get provenance record
provenance = value.get_provenance()

# Get operation type directly
operation = value.get_operation()  # e.g., "+", "calc:gross_margin"

# Get input provenance IDs
input_ids = value.get_inputs()  # tuple of parent provenance IDs

# Check if value has provenance
has_prov = value.has_provenance()
```

## Engine Calculations with Named Inputs

### Basic Named Inputs

```python
from metricengine import Engine

engine = Engine()

# Use named inputs for better provenance
result = engine.calculate("gross_margin", {
    "revenue": 1000,
    "cost": 600
})

# Provenance includes input names
prov = result.get_provenance()
print(prov.meta["input_names"])  # Maps provenance IDs to names
```

### Complex Calculations

```python
# Multi-step calculation with named inputs
quarterly_data = {
    "q1_revenue": 1000,
    "q1_cost": 600,
    "q2_revenue": 1200,
    "q2_cost": 700,
}

q1_margin = engine.calculate("gross_margin", {
    "revenue": quarterly_data["q1_revenue"],
    "cost": quarterly_data["q1_cost"]
})

q2_margin = engine.calculate("gross_margin", {
    "revenue": quarterly_data["q2_revenue"],
    "cost": quarterly_data["q2_cost"]
})

# Calculate growth
growth = engine.calculate("growth_rate", {
    "current": q2_margin,
    "previous": q1_margin
})

# Full provenance chain is maintained
print(explain(growth))
```

## Calculation Spans

### Basic Spans

```python
from metricengine import calc_span

# Group related calculations under a span
with calc_span("quarterly_analysis"):
    revenue = FinancialValue(1000)
    cost = FinancialValue(600)
    margin = revenue - cost

    # All operations include span information
    prov = margin.get_provenance()
    print(prov.meta["span"])  # "quarterly_analysis"
```

### Spans with Attributes

```python
# Add attributes to spans for better context
with calc_span("quarterly_analysis", quarter="Q1", year=2025, analyst="john"):
    revenue = FinancialValue(1000, "Q1 Revenue")
    cost = FinancialValue(600, "Q1 Cost")
    margin = revenue - cost

    # Span attributes are included in metadata
    prov = margin.get_provenance()
    print(prov.meta["quarter"])  # "Q1"
    print(prov.meta["analyst"])  # "john"
```

### Nested Spans

```python
# Spans can be nested for hierarchical organization
with calc_span("annual_analysis", year=2025):
    annual_revenue = FinancialValue(0)

    for quarter in ["Q1", "Q2", "Q3", "Q4"]:
        with calc_span("quarterly_analysis", quarter=quarter):
            q_revenue = FinancialValue(1000)  # Simplified
            annual_revenue = annual_revenue + q_revenue

# Provenance maintains the complete span hierarchy
```

## Export and Analysis

### JSON Export

```python
from metricengine.provenance import to_trace_json

# Export complete provenance graph
trace_data = to_trace_json(result)

# Save to file
import json
with open("calculation_trace.json", "w") as f:
    json.dump(trace_data, f, indent=2)

# The JSON includes all nodes and their relationships
print(trace_data["root"])  # Root provenance ID
print(trace_data["nodes"])  # All provenance records
```

### Human-Readable Explanations

```python
from metricengine.provenance import explain

# Generate explanation with default depth
explanation = explain(result)
print(explanation)

# Limit explanation depth for complex calculations
short_explanation = explain(result, max_depth=3)
print(short_explanation)
```

Example output:
```
gross_margin (calc:gross_margin)
├── revenue: 1000.00 (literal)
└── cost: 600.00 (literal)
```

### Provenance Graph Analysis

```python
from metricengine.provenance import get_provenance_graph

# Get complete provenance graph as dictionary
graph = get_provenance_graph(result)

# Analyze the graph
print(f"Total nodes: {len(graph)}")
print(f"Root operation: {graph[result.get_provenance().id].op}")

# Find all literal inputs
literals = [prov for prov in graph.values() if prov.op == "literal"]
print(f"Literal inputs: {len(literals)}")

# Find all calculations
calculations = [prov for prov in graph.values() if prov.op.startswith("calc:")]
print(f"Calculations: {len(calculations)}")
```

## Debugging with Provenance

### Tracing Calculation Errors

```python
def debug_calculation(value):
    """Debug a financial value by examining its provenance."""
    if not value.has_provenance():
        print("No provenance available")
        return

    prov = value.get_provenance()
    print(f"Value: {value}")
    print(f"Operation: {prov.op}")

    if prov.meta:
        print("Metadata:")
        for key, val in prov.meta.items():
            print(f"  {key}: {val}")

    if prov.inputs:
        print(f"Depends on {len(prov.inputs)} inputs")
        # Could recursively debug inputs here

# Use for debugging
problematic_result = complex_calculation()
debug_calculation(problematic_result)
```

### Finding Specific Operations

```python
def find_operations(value, operation_type):
    """Find all operations of a specific type in the provenance chain."""
    graph = get_provenance_graph(value)

    matching_ops = []
    for prov in graph.values():
        if prov.op == operation_type:
            matching_ops.append(prov)

    return matching_ops

# Find all division operations
divisions = find_operations(result, "/")
print(f"Found {len(divisions)} division operations")

# Find all engine calculations
calculations = find_operations(result, "calc:gross_margin")
print(f"Found {len(calculations)} gross margin calculations")
```

## Performance Optimization

### Selective Provenance Tracking

```python
from metricengine.provenance_config import provenance_config

# Disable provenance for performance-critical sections
def fast_calculation():
    with provenance_config(enabled=False):
        # No provenance overhead here
        result = expensive_operation()
    return result

# Enable only essential tracking
def optimized_calculation():
    with provenance_config(
        track_literals=False,  # Skip literal tracking
        enable_spans=False,    # Disable spans
    ):
        result = calculation_with_many_literals()
    return result
```

### Batch Processing

```python
# For batch processing, consider disabling provenance
def process_batch(items):
    results = []

    with provenance_config(enabled=False):
        for item in items:
            # Process without provenance for speed
            result = process_item(item)
            results.append(result)

    return results

# Or use minimal provenance
def process_batch_with_minimal_provenance(items):
    results = []

    with provenance_config(
        track_literals=False,
        track_operations=True,  # Keep operation tracking
        enable_spans=False,
    ):
        for item in items:
            result = process_item(item)
            results.append(result)

    return results
```

## Auditing and Compliance

### Audit Trail Generation

```python
def generate_audit_trail(result, filename):
    """Generate a comprehensive audit trail for a calculation."""

    # Get complete provenance information
    trace_data = to_trace_json(result)
    explanation = explain(result)

    # Create audit report
    audit_report = {
        "timestamp": datetime.now().isoformat(),
        "result_value": str(result),
        "calculation_tree": explanation,
        "provenance_graph": trace_data,
        "metadata": {
            "total_operations": len(trace_data["nodes"]),
            "root_operation": trace_data["nodes"][trace_data["root"]]["op"],
        }
    }

    # Save audit trail
    with open(filename, "w") as f:
        json.dump(audit_report, f, indent=2)

    return audit_report

# Generate audit trail
audit = generate_audit_trail(important_result, "audit_trail.json")
```

### Compliance Verification

```python
def verify_calculation_compliance(result, required_inputs):
    """Verify that a calculation used all required inputs."""

    graph = get_provenance_graph(result)

    # Find all literal inputs
    literal_inputs = []
    for prov in graph.values():
        if prov.op == "literal" and "input_name" in prov.meta:
            literal_inputs.append(prov.meta["input_name"])

    # Check compliance
    missing_inputs = set(required_inputs) - set(literal_inputs)

    if missing_inputs:
        raise ValueError(f"Missing required inputs: {missing_inputs}")

    return True

# Verify compliance
required = ["revenue", "cost", "tax_rate"]
verify_calculation_compliance(result, required)
```

## Best Practices

### 1. Use Meaningful Names

```python
# Good: Use descriptive names for inputs
result = engine.calculate("net_profit", {
    "gross_revenue": 1000,
    "operating_expenses": 300,
    "tax_rate": 0.25
})

# Avoid: Generic names that don't help with debugging
result = engine.calculate("net_profit", {
    "input1": 1000,
    "input2": 300,
    "input3": 0.25
})
```

### 2. Use Spans for Context

```python
# Group related calculations under meaningful spans
with calc_span("monthly_financial_analysis", month="January", year=2025):
    # All calculations inherit the span context
    revenue = calculate_monthly_revenue()
    expenses = calculate_monthly_expenses()
    profit = revenue - expenses
```

### 3. Export for Documentation

```python
# Document complex calculations by exporting provenance
def document_calculation(result, description):
    """Document a calculation with its provenance."""

    explanation = explain(result)

    documentation = f"""
# {description}

## Result
{result}

## Calculation Tree
```
{explanation}
```

## Generated on: {datetime.now().isoformat()}
"""

    return documentation

# Use for documentation
doc = document_calculation(quarterly_profit, "Q1 2025 Profit Calculation")
```

### 4. Handle Missing Provenance Gracefully

```python
def safe_provenance_access(value):
    """Safely access provenance information."""

    if not value.has_provenance():
        return "No provenance available"

    try:
        prov = value.get_provenance()
        return f"Operation: {prov.op}, Inputs: {len(prov.inputs)}"
    except Exception as e:
        return f"Error accessing provenance: {e}"

# Always check before accessing provenance
info = safe_provenance_access(some_value)
```

### 5. Monitor Performance Impact

```python
import time

def benchmark_with_provenance():
    """Benchmark calculation with and without provenance."""

    # Test with provenance
    start = time.time()
    result_with = complex_calculation()
    time_with = time.time() - start

    # Test without provenance
    with provenance_config(enabled=False):
        start = time.time()
        result_without = complex_calculation()
        time_without = time.time() - start

    overhead = (time_with - time_without) / time_without * 100
    print(f"Provenance overhead: {overhead:.2f}%")

    return overhead

# Monitor overhead regularly
overhead = benchmark_with_provenance()
```
