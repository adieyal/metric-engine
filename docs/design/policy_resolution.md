# Policy Resolution

How policies are resolved and applied in Metric Engine.

## Policy Hierarchy

1. **Context Policy**: Currently active policy context
2. **Thread Policy**: Thread-local policy settings
3. **Global Policy**: System-wide default policy
4. **Built-in Policy**: Framework default behavior

## Resolution Algorithm

```python
def resolve_policy():
    return (
        get_context_policy() or
        get_thread_policy() or
        get_global_policy() or
        get_builtin_policy()
    )
```

## Policy Inheritance

- Child contexts inherit parent policies
- Explicit settings override inherited values
- Null policies fall back to parent

## Performance Considerations

- Policy resolution is cached per calculation
- Context switches invalidate cache
- Minimal overhead in hot paths
