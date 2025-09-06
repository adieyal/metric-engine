# Configuring Provenance Tracking

This guide covers how to configure provenance tracking in MetricEngine for different use cases, from development and debugging to production environments.

## Quick Start

### Enable/Disable Provenance

```python
from metricengine.provenance_config import enable_provenance, disable_provenance

# Disable provenance globally
disable_provenance()

# Re-enable provenance
enable_provenance()
```

### Performance Mode

For production environments where performance is critical:

```python
from metricengine.provenance_config import set_performance_mode

# Configure for optimal performance
set_performance_mode()
```

### Debug Mode

For development and debugging:

```python
from metricengine.provenance_config import set_debug_mode

# Enable all features and detailed logging
set_debug_mode()
```

## Configuration Options

### Core Feature Toggles

```python
from metricengine.provenance_config import update_global_config

# Control which types of operations are tracked
update_global_config(
    enabled=True,              # Master switch for all provenance
    track_literals=True,       # Track literal value creation
    track_operations=True,     # Track arithmetic operations
    track_calculations=True,   # Track engine calculations
)
```

### Error Handling

```python
# Configure error handling behavior
update_global_config(
    fail_on_error=False,       # Degrade gracefully on errors
    log_errors=True,           # Log provenance errors
    log_level=logging.WARNING, # Log level for errors
)
```

### Performance Controls

```python
# Tune performance-related settings
update_global_config(
    max_history_depth=1000,        # Limit provenance chain depth
    enable_spans=True,             # Enable calculation spans
    enable_id_interning=True,      # Intern IDs to save memory
    max_hash_cache_size=10000,     # Cache size for hash operations
)
```

### Memory Management

```python
# Configure memory usage
update_global_config(
    enable_weak_refs=False,        # Use weak references in graphs
    max_graph_size=10000,          # Maximum nodes in provenance graph
    enable_history_truncation=True, # Enable history truncation
)
```

### Debugging Options

```python
# Enable debugging features
update_global_config(
    debug_mode=True,               # Enable debug information
    include_stack_traces=True,     # Include stack traces in errors
)
```

## Context-Specific Configuration

Use the `provenance_config` context manager for temporary configuration changes:

```python
from metricengine.provenance_config import provenance_config

# Temporarily disable provenance for performance-critical code
with provenance_config(enabled=False):
    # Provenance tracking disabled in this block
    result = expensive_calculation()

# Provenance tracking restored outside the block
```

### Multiple Overrides

```python
# Override multiple settings temporarily
with provenance_config(
    track_literals=False,
    enable_spans=False,
    max_history_depth=100
):
    # Reduced provenance tracking for this block
    results = batch_calculations()
```

## Environment-Specific Configurations

### Development Environment

```python
from metricengine.provenance_config import ProvenanceConfig, set_global_config

# Full-featured configuration for development
dev_config = ProvenanceConfig(
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
    enable_spans=True,
)

set_global_config(dev_config)
```

### Production Environment

```python
# Optimized configuration for production
prod_config = ProvenanceConfig(
    enabled=True,
    track_literals=False,      # Skip literals for performance
    track_operations=True,
    track_calculations=True,
    fail_on_error=False,       # Always degrade gracefully
    log_errors=True,
    log_level=logging.ERROR,   # Only log serious errors
    debug_mode=False,
    include_stack_traces=False,
    max_history_depth=500,     # Limit history depth
    enable_spans=False,        # Disable spans for performance
    enable_id_interning=True,  # Enable memory optimizations
    max_hash_cache_size=5000,
    enable_weak_refs=True,
    enable_history_truncation=True,
)

set_global_config(prod_config)
```

### Testing Environment

```python
# Configuration for automated testing
test_config = ProvenanceConfig(
    enabled=True,
    track_literals=True,
    track_operations=True,
    track_calculations=True,
    fail_on_error=True,        # Fail fast in tests
    log_errors=False,          # Reduce test noise
    debug_mode=False,
    max_history_depth=1000,
    enable_spans=True,
)

set_global_config(test_config)
```

## Performance Tuning

### High-Performance Applications

For applications where every microsecond counts:

```python
# Minimal provenance tracking
update_global_config(
    track_literals=False,          # Skip literal tracking
    enable_spans=False,            # Disable span tracking
    max_history_depth=50,          # Very limited history
    enable_id_interning=True,      # Memory optimization
    max_hash_cache_size=1000,      # Smaller cache
    enable_weak_refs=True,         # Prevent memory leaks
)
```

### Memory-Constrained Environments

For environments with limited memory:

```python
# Memory-optimized configuration
update_global_config(
    max_history_depth=100,         # Limit history depth
    max_graph_size=1000,           # Limit graph size
    enable_id_interning=True,      # Intern strings
    enable_weak_refs=True,         # Use weak references
    enable_history_truncation=True, # Enable truncation
    max_hash_cache_size=500,       # Smaller cache
)
```

## Monitoring and Diagnostics

### Check Configuration Status

```python
from metricengine.provenance_config import get_config

# Get current configuration
config = get_config()
print(f"Provenance enabled: {config.enabled}")
print(f"Track operations: {config.track_operations}")
print(f"Max history depth: {config.max_history_depth}")
```

### Check Provenance Availability

```python
from metricengine.provenance_config import is_provenance_available

if is_provenance_available():
    print("Provenance tracking is available and functional")
else:
    print("Provenance tracking is disabled or unavailable")
```

### Error Logging

Configure logging to monitor provenance issues:

```python
import logging

# Set up logging for provenance errors
logging.getLogger('metricengine.provenance_config').setLevel(logging.WARNING)

# Enable detailed error logging
update_global_config(
    log_errors=True,
    log_level=logging.INFO,
    include_stack_traces=True,
)
```

## Best Practices

### 1. Environment-Specific Configuration

Always configure provenance based on your environment:

- **Development**: Enable all features for debugging
- **Testing**: Enable strict error handling
- **Production**: Optimize for performance and stability

### 2. Gradual Rollout

When enabling provenance in production:

1. Start with minimal tracking (`track_calculations=True` only)
2. Monitor performance impact
3. Gradually enable more features as needed

### 3. Memory Management

For long-running applications:

- Enable history truncation
- Set reasonable limits on graph size
- Use weak references to prevent memory leaks
- Monitor memory usage over time

### 4. Error Handling

Configure error handling appropriately:

- **Development**: `fail_on_error=False` with detailed logging
- **Production**: `fail_on_error=False` with minimal logging
- **Testing**: `fail_on_error=True` to catch issues early

### 5. Performance Testing

Always benchmark your specific use case:

```python
import time
from metricengine.provenance_config import provenance_config

# Benchmark with and without provenance
def benchmark_calculation():
    start = time.time()
    # Your calculation here
    result = complex_calculation()
    return time.time() - start

# Test with provenance
with_provenance = benchmark_calculation()

# Test without provenance
with provenance_config(enabled=False):
    without_provenance = benchmark_calculation()

overhead = (with_provenance - without_provenance) / without_provenance * 100
print(f"Provenance overhead: {overhead:.2f}%")
```

## Troubleshooting

### High Memory Usage

If provenance is using too much memory:

1. Reduce `max_history_depth`
2. Enable `enable_history_truncation`
3. Use `enable_weak_refs=True`
4. Reduce `max_graph_size`

### Performance Issues

If provenance is impacting performance:

1. Disable literal tracking: `track_literals=False`
2. Disable spans: `enable_spans=False`
3. Reduce cache size: `max_hash_cache_size=1000`
4. Use performance mode: `set_performance_mode()`

### Missing Provenance Data

If provenance data is missing:

1. Check if provenance is enabled: `get_config().enabled`
2. Verify specific tracking is enabled (literals, operations, calculations)
3. Check for error logs that might indicate failures
4. Ensure you're not in a context with provenance disabled

### Error Messages

Common error scenarios and solutions:

- **"Unknown configuration option"**: Check spelling of configuration keys
- **"Provenance generation failed"**: Enable error logging to see details
- **"Hash collision detected"**: Extremely rare; contact support if this occurs
- **"Graph size limit exceeded"**: Increase `max_graph_size` or enable truncation
