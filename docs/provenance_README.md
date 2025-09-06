# Provenance Tracking in MetricEngine

Provenance tracking provides complete audit trails for all financial calculations in MetricEngine, enabling you to understand exactly how any value was derived. This feature automatically captures the computational graph of operations, including input values, operations performed, and contextual metadata.

## Quick Start

Provenance tracking works automatically without any code changes:

```python
from metricengine import FinancialValue

# Create values - provenance is tracked automatically
revenue = FinancialValue(1000)
cost = FinancialValue(600)
margin = revenue - cost

# Access provenance information
if margin.has_provenance():
    prov = margin.get_provenance()
    print(f"Operation: {prov.op}")  # "-"
    print(f"Inputs: {len(prov.inputs)}")  # 2
```

## Key Features

### 🔍 **Automatic Tracking**
Every operation automatically generates provenance records without requiring code changes.

### 🏷️ **Named Inputs**
Provide meaningful names for calculation inputs that appear in audit trails.

### 📊 **Calculation Spans**
Group related operations under named spans for better organization and context.

### 📤 **Export & Analysis**
Export provenance data as JSON or generate human-readable explanations.

### ⚡ **Performance Optimized**
Minimal overhead with configurable performance tuning options.

### 🔒 **Tamper-Evident**
Cryptographic hashing ensures provenance integrity and prevents tampering.

## Basic Usage

### Engine Calculations with Named Inputs

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

### Calculation Spans

```python
from metricengine.provenance import calc_span

# Group related calculations under a span
with calc_span("quarterly_analysis", quarter="Q1", year=2025):
    revenue = FinancialValue(1000)
    cost = FinancialValue(600)
    margin = revenue - cost

# All operations include span information
prov = margin.get_provenance()
print(prov.meta["span"])  # "quarterly_analysis"
print(prov.meta["quarter"])  # "Q1"
```

### Export and Analysis

```python
from metricengine.provenance import to_trace_json, explain

# Export complete provenance graph as JSON
trace_data = to_trace_json(result)

# Generate human-readable explanation
explanation = explain(result, max_depth=5)
print(explanation)
```

## Configuration

### Quick Configuration

```python
from metricengine.provenance_config import (
    enable_provenance,
    disable_provenance,
    set_performance_mode,
    set_debug_mode
)

# Enable/disable globally
enable_provenance()
disable_provenance()

# Optimize for performance
set_performance_mode()

# Enable full debugging features
set_debug_mode()
```

### Temporary Configuration

```python
from metricengine.provenance_config import provenance_config

# Temporarily disable provenance for performance-critical code
with provenance_config(enabled=False):
    result = expensive_calculation()

# Multiple configuration overrides
with provenance_config(
    track_literals=False,
    enable_spans=False,
    max_history_depth=100
):
    result = optimized_calculation()
```

### Environment-Specific Configuration

```python
from metricengine.provenance_config import ProvenanceConfig, set_global_config

# Production configuration
prod_config = ProvenanceConfig(
    enabled=True,
    track_literals=False,      # Skip literals for performance
    track_operations=True,
    track_calculations=True,
    fail_on_error=False,       # Always degrade gracefully
    max_history_depth=500,     # Limit history depth
    enable_id_interning=True,  # Enable memory optimizations
)

set_global_config(prod_config)
```

## Documentation

### Concepts
- [Provenance Concepts](concepts/provenance.md) - Core concepts and architecture
- [Financial Value Integration](concepts/financial_value.md) - How provenance integrates with FinancialValue

### How-To Guides
- [Configuration Guide](howto/provenance_configuration.md) - Detailed configuration options
- [Usage Guide](howto/provenance_usage.md) - Practical usage examples
- [Best Practices](howto/provenance_best_practices.md) - Production deployment and optimization

### API Reference
- [Provenance API](reference/provenance.rst) - Complete API documentation

## Examples

See [examples/provenance_example.py](../examples/provenance_example.py) for comprehensive examples covering:

- Basic provenance tracking
- Engine calculations with named inputs
- Calculation spans
- Configuration options
- Export functionality
- Performance considerations
- Error handling

## Performance

Provenance tracking is designed to have minimal performance impact:

- **Typical Overhead**: 2-5% for most operations
- **Memory Efficient**: Uses `__slots__` and string interning
- **Configurable**: Can be tuned or disabled for performance-critical paths
- **Lazy Evaluation**: Provenance graphs are only fully constructed when needed

### Performance Tuning

```python
# For high-performance applications
from metricengine.provenance_config import update_global_config

update_global_config(
    track_literals=False,          # Skip literal tracking
    enable_spans=False,            # Disable span tracking
    max_history_depth=50,          # Very limited history
    enable_id_interning=True,      # Memory optimization
)
```

## Security and Compliance

### Tamper Evidence
- **Cryptographic Hashing**: SHA-256 ensures integrity
- **Immutable Records**: Cannot be modified after creation
- **Deterministic IDs**: Same inputs always produce same provenance IDs

### Audit Trails
```python
def generate_audit_trail(result, filename):
    """Generate comprehensive audit trail for compliance."""

    trace_data = to_trace_json(result)
    explanation = explain(result)

    audit_report = {
        "timestamp": datetime.now().isoformat(),
        "result_value": str(result),
        "calculation_tree": explanation,
        "provenance_graph": trace_data,
    }

    with open(filename, "w") as f:
        json.dump(audit_report, f, indent=2)

    return audit_report
```

## Error Handling

Provenance tracking is designed to degrade gracefully:

```python
# Provenance failures never break core functionality
result = FinancialValue(100) + FinancialValue(50)  # Always works

# Check for provenance availability
if result.has_provenance():
    # Use provenance features
    explanation = explain(result)
else:
    # Fallback behavior
    log_calculation_without_provenance(result)
```

## Migration

Provenance tracking is fully backward compatible:

1. **No Code Changes Required**: Existing code works unchanged
2. **Gradual Adoption**: Enable features incrementally
3. **Optional Features**: All provenance features are optional

```python
# Existing code works without changes
revenue = FinancialValue(1000)
cost = FinancialValue(600)
margin = revenue - cost  # Provenance tracked automatically

# New features are opt-in
if margin.has_provenance():
    # Use new provenance features
    audit_trail = to_trace_json(margin)
```

## Support

- **Documentation**: Comprehensive guides and API reference
- **Examples**: Working examples for common use cases
- **Configuration**: Flexible configuration for different environments
- **Testing**: Extensive test suite ensures reliability

## Requirements

- Python 3.8+
- MetricEngine core library
- Optional: Additional dependencies for advanced features

## License

Provenance tracking is included with MetricEngine under the same license terms.
