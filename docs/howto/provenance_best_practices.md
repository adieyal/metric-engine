# Provenance Best Practices

This guide provides best practices for using provenance tracking effectively in MetricEngine applications, covering performance optimization, debugging strategies, and production deployment considerations.

## General Principles

### 1. Start Simple, Scale Gradually

Begin with basic provenance tracking and add complexity as needed:

```python
# Start with default configuration
from metricengine import FinancialValue

# Basic usage - provenance works automatically
revenue = FinancialValue(1000)
cost = FinancialValue(600)
margin = revenue - cost

# Add complexity gradually
from metricengine.provenance import calc_span

with calc_span("analysis"):
    # More structured approach
    detailed_analysis()
```

### 2. Use Meaningful Names

Always provide descriptive names for inputs and spans:

```python
# Good: Descriptive names
result = engine.calculate("gross_margin", {
    "total_revenue": 1000,
    "cost_of_goods_sold": 600,
    "operating_expenses": 200
})

with calc_span("quarterly_financial_analysis", quarter="Q1", year=2025):
    # Clear context for all operations
    pass

# Avoid: Generic names
result = engine.calculate("calc1", {"x": 1000, "y": 600})
with calc_span("span1"):
    pass
```

### 3. Design for Auditability

Structure your code to support audit requirements:

```python
def auditable_calculation(inputs, metadata):
    """Perform calculation with full audit trail."""

    with calc_span("audit_calculation", **metadata):
        # Use named inputs
        result = engine.calculate("target_metric", inputs)

        # Export audit trail
        audit_trail = to_trace_json(result)

        # Store for compliance
        store_audit_trail(audit_trail, metadata)

        return result
```

## Performance Best Practices

### 1. Profile Before Optimizing

Always measure the actual performance impact:

```python
import time
from metricengine.provenance_config import provenance_config

def benchmark_provenance_impact():
    """Measure provenance overhead for your specific use case."""

    def test_calculation():
        # Your actual calculation logic
        return complex_financial_calculation()

    # Benchmark with provenance
    start = time.time()
    result_with = test_calculation()
    time_with = time.time() - start

    # Benchmark without provenance
    with provenance_config(enabled=False):
        start = time.time()
        result_without = test_calculation()
        time_without = time.time() - start

    overhead = (time_with - time_without) / time_without * 100
    print(f"Provenance overhead: {overhead:.2f}%")

    return overhead

# Run benchmark regularly
overhead = benchmark_provenance_impact()
if overhead > 10:  # Adjust threshold as needed
    print("Consider optimizing provenance configuration")
```

### 2. Use Selective Tracking

Enable only the provenance features you need:

```python
from metricengine.provenance_config import update_global_config

# For high-frequency calculations
update_global_config(
    track_literals=False,      # Skip literal tracking
    enable_spans=False,        # Disable spans
    max_history_depth=100,     # Limit history
)

# For batch processing
def process_batch(items):
    with provenance_config(
        track_operations=True,     # Keep operation tracking
        track_calculations=True,   # Keep calculation tracking
        track_literals=False,      # Skip literals for performance
    ):
        return [process_item(item) for item in items]
```

### 3. Optimize Memory Usage

Configure memory management for long-running applications:

```python
# Memory-optimized configuration
update_global_config(
    enable_id_interning=True,      # Reduce string duplication
    enable_weak_refs=True,         # Prevent memory leaks
    enable_history_truncation=True, # Limit history growth
    max_graph_size=5000,           # Prevent unbounded growth
    max_hash_cache_size=2000,      # Reasonable cache size
)
```

### 4. Use Context Managers for Temporary Changes

Avoid global configuration changes in production:

```python
# Good: Temporary configuration changes
def performance_critical_section():
    with provenance_config(enabled=False):
        # High-performance calculation
        return fast_calculation()

# Avoid: Global changes that affect other code
def bad_performance_optimization():
    disable_provenance()  # Affects entire application
    result = fast_calculation()
    enable_provenance()   # May not be called if exception occurs
    return result
```

## Development and Debugging

### 1. Use Debug Mode During Development

Enable comprehensive tracking and logging:

```python
from metricengine.provenance_config import set_debug_mode

# In development environment
set_debug_mode()

# Or configure manually
update_global_config(
    debug_mode=True,
    include_stack_traces=True,
    log_errors=True,
    log_level=logging.DEBUG,
    max_history_depth=10000,  # Deep history for debugging
)
```

### 2. Create Debugging Utilities

Build tools to help with provenance analysis:

```python
def debug_provenance_chain(value, max_depth=5):
    """Print detailed provenance information for debugging."""

    if not value.has_provenance():
        print("No provenance available")
        return

    def print_node(prov_id, depth=0, visited=None):
        if visited is None:
            visited = set()

        if prov_id in visited or depth > max_depth:
            return

        visited.add(prov_id)
        graph = get_provenance_graph(value)
        prov = graph.get(prov_id)

        if not prov:
            return

        indent = "  " * depth
        print(f"{indent}{prov.op} (ID: {prov_id[:8]}...)")

        if prov.meta:
            for key, val in prov.meta.items():
                print(f"{indent}  {key}: {val}")

        for input_id in prov.inputs:
            print_node(input_id, depth + 1, visited)

    root_prov = value.get_provenance()
    print_node(root_prov.id)

# Use for debugging
debug_provenance_chain(problematic_result)
```

### 3. Validate Provenance Integrity

Create tests to ensure provenance is working correctly:

```python
def test_provenance_integrity():
    """Test that provenance tracking is working correctly."""

    # Test basic operations
    a = FinancialValue(100)
    b = FinancialValue(50)
    c = a + b

    assert c.has_provenance()
    assert c.get_operation() == "+"
    assert len(c.get_inputs()) == 2

    # Test engine calculations
    result = engine.calculate("test_calc", {"input1": 100, "input2": 50})
    assert result.has_provenance()
    assert result.get_operation().startswith("calc:")

    # Test export functionality
    trace = to_trace_json(result)
    assert "root" in trace
    assert "nodes" in trace

    print("Provenance integrity test passed")

# Run regularly in test suite
test_provenance_integrity()
```

## Production Deployment

### 1. Environment-Specific Configuration

Use different configurations for different environments:

```python
import os
from metricengine.provenance_config import ProvenanceConfig, set_global_config

def configure_provenance_for_environment():
    """Configure provenance based on environment."""

    env = os.getenv("ENVIRONMENT", "development")

    if env == "production":
        # Production: Optimized for performance and stability
        config = ProvenanceConfig(
            enabled=True,
            track_literals=False,
            track_operations=True,
            track_calculations=True,
            fail_on_error=False,
            log_errors=True,
            log_level=logging.ERROR,
            max_history_depth=500,
            enable_spans=False,
            enable_id_interning=True,
            enable_weak_refs=True,
        )
    elif env == "staging":
        # Staging: Similar to production but with more debugging
        config = ProvenanceConfig(
            enabled=True,
            track_literals=True,
            track_operations=True,
            track_calculations=True,
            fail_on_error=False,
            log_errors=True,
            log_level=logging.WARNING,
            max_history_depth=1000,
            enable_spans=True,
        )
    else:  # development
        # Development: Full features for debugging
        config = ProvenanceConfig(
            enabled=True,
            track_literals=True,
            track_operations=True,
            track_calculations=True,
            fail_on_error=False,
            log_errors=True,
            log_level=logging.DEBUG,
            debug_mode=True,
            include_stack_traces=True,
            max_history_depth=10000,
        )

    set_global_config(config)

# Call during application startup
configure_provenance_for_environment()
```

### 2. Monitor Performance in Production

Set up monitoring for provenance overhead:

```python
import logging
import time
from contextlib import contextmanager

# Set up performance monitoring
perf_logger = logging.getLogger("provenance.performance")

@contextmanager
def monitor_provenance_performance(operation_name):
    """Monitor performance impact of provenance tracking."""

    start = time.time()
    try:
        yield
    finally:
        duration = time.time() - start

        # Log if operation takes too long
        if duration > 1.0:  # Adjust threshold as needed
            perf_logger.warning(
                f"Slow operation with provenance: {operation_name} took {duration:.2f}s"
            )

# Use in critical paths
def critical_calculation():
    with monitor_provenance_performance("critical_calculation"):
        return complex_calculation()
```

### 3. Implement Graceful Degradation

Ensure your application works even if provenance fails:

```python
def safe_provenance_operation(func, *args, **kwargs):
    """Execute function with provenance, falling back gracefully on errors."""

    try:
        return func(*args, **kwargs)
    except Exception as e:
        # Log the error
        log_provenance_error(e, func.__name__)

        # Try without provenance
        with provenance_config(enabled=False):
            return func(*args, **kwargs)

# Use for critical operations
def important_calculation():
    return safe_provenance_operation(complex_calculation)
```

## Testing Strategies

### 1. Test Provenance Behavior

Include provenance in your test suite:

```python
def test_calculation_provenance():
    """Test that calculations produce correct provenance."""

    # Test arithmetic operations
    a = FinancialValue(100)
    b = FinancialValue(50)
    result = a + b

    assert result.has_provenance()
    assert result.get_operation() == "+"

    # Test that provenance IDs are stable
    a2 = FinancialValue(100)
    b2 = FinancialValue(50)
    result2 = a2 + b2

    # Same inputs should produce same provenance ID
    assert result.get_provenance().id == result2.get_provenance().id

def test_provenance_export():
    """Test provenance export functionality."""

    result = create_test_calculation()

    # Test JSON export
    trace = to_trace_json(result)
    assert isinstance(trace, dict)
    assert "root" in trace
    assert "nodes" in trace

    # Test explanation
    explanation = explain(result)
    assert isinstance(explanation, str)
    assert len(explanation) > 0
```

### 2. Test Configuration Changes

Verify that configuration changes work correctly:

```python
def test_configuration_changes():
    """Test that configuration changes affect behavior correctly."""

    # Test disabling provenance
    with provenance_config(enabled=False):
        result = FinancialValue(100) + FinancialValue(50)
        assert not result.has_provenance()

    # Test selective tracking
    with provenance_config(track_literals=False, track_operations=True):
        literal = FinancialValue(100)
        # Literal might not have provenance (implementation dependent)

        result = literal + FinancialValue(50)
        # Operation should have provenance
        assert result.has_provenance()
```

### 3. Performance Regression Tests

Include performance tests to catch regressions:

```python
def test_provenance_performance():
    """Test that provenance overhead stays within acceptable limits."""

    def benchmark_operation():
        start = time.time()
        for _ in range(1000):
            result = FinancialValue(100) + FinancialValue(50)
        return time.time() - start

    # Benchmark with provenance
    time_with = benchmark_operation()

    # Benchmark without provenance
    with provenance_config(enabled=False):
        time_without = benchmark_operation()

    # Calculate overhead
    overhead = (time_with - time_without) / time_without * 100

    # Assert overhead is within acceptable limits
    assert overhead < 20, f"Provenance overhead too high: {overhead:.2f}%"
```

## Error Handling and Logging

### 1. Configure Appropriate Logging

Set up logging to capture provenance issues without noise:

```python
import logging

# Configure provenance logging
provenance_logger = logging.getLogger("metricengine.provenance_config")
provenance_logger.setLevel(logging.WARNING)

# Add handler for provenance errors
handler = logging.StreamHandler()
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
handler.setFormatter(formatter)
provenance_logger.addHandler(handler)

# Configure error handling
update_global_config(
    log_errors=True,
    log_level=logging.WARNING,
    include_stack_traces=False,  # Avoid noise in production
)
```

### 2. Handle Missing Provenance Gracefully

Always check for provenance availability:

```python
def safe_provenance_access(value):
    """Safely access provenance information."""

    try:
        if not value.has_provenance():
            return {"status": "no_provenance"}

        prov = value.get_provenance()
        return {
            "status": "success",
            "operation": prov.op,
            "inputs": len(prov.inputs),
            "metadata": dict(prov.meta)
        }
    except Exception as e:
        log_provenance_error(e, "safe_provenance_access")
        return {"status": "error", "error": str(e)}

# Use in production code
prov_info = safe_provenance_access(calculation_result)
if prov_info["status"] == "success":
    # Use provenance information
    process_provenance(prov_info)
```

## Security and Compliance

### 1. Sanitize Sensitive Data

Be careful about sensitive information in provenance metadata:

```python
def sanitize_metadata(metadata):
    """Remove sensitive information from provenance metadata."""

    sensitive_keys = ["password", "api_key", "secret", "token"]
    sanitized = {}

    for key, value in metadata.items():
        if any(sensitive in key.lower() for sensitive in sensitive_keys):
            sanitized[key] = "[REDACTED]"
        else:
            sanitized[key] = value

    return sanitized

# Use when creating spans with metadata
with calc_span("secure_calculation", **sanitize_metadata(user_metadata)):
    result = secure_calculation()
```

### 2. Implement Retention Policies

Configure appropriate data retention:

```python
# Configure retention policies
update_global_config(
    max_history_depth=1000,        # Limit history depth
    enable_history_truncation=True, # Enable automatic truncation
    max_graph_size=5000,           # Limit graph size
)

def cleanup_old_provenance():
    """Implement custom provenance cleanup logic."""
    # Implementation depends on your storage mechanism
    # This is a placeholder for custom cleanup logic
    pass
```

## Migration and Adoption

### 1. Gradual Rollout

Introduce provenance tracking gradually:

```python
# Phase 1: Enable basic tracking
update_global_config(
    enabled=True,
    track_calculations=True,  # Start with calculations only
    track_operations=False,   # Add later
    track_literals=False,     # Add later
)

# Phase 2: Add operation tracking
# update_global_config(track_operations=True)

# Phase 3: Add literal tracking if needed
# update_global_config(track_literals=True)
```

### 2. Backward Compatibility

Ensure your code works with and without provenance:

```python
def calculation_with_optional_provenance():
    """Calculation that works with or without provenance."""

    result = perform_calculation()

    # Optional provenance processing
    if result.has_provenance():
        # Enhanced functionality with provenance
        audit_trail = generate_audit_trail(result)
        store_audit_trail(audit_trail)
    else:
        # Fallback for legacy behavior
        log_calculation_result(result)

    return result
```

### 3. Training and Documentation

Provide clear guidance for your team:

```python
# Create utility functions for common patterns
def create_auditable_calculation(name, inputs, metadata=None):
    """Standard pattern for auditable calculations."""

    metadata = metadata or {}
    metadata.update({
        "timestamp": datetime.now().isoformat(),
        "user": get_current_user(),
    })

    with calc_span(f"auditable_{name}", **metadata):
        return engine.calculate(name, inputs)

# Document usage patterns
def example_usage():
    """Example of recommended provenance usage patterns."""

    # Use meaningful names
    result = create_auditable_calculation("gross_margin", {
        "revenue": 1000,
        "cost": 600
    }, {"department": "sales", "region": "north"})

    # Export for audit
    audit_trail = to_trace_json(result)

    return result, audit_trail
```
