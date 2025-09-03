"""Registry for financial calculations with dependency tracking."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping
from threading import RLock
from typing import Any, Callable

from .exceptions import CalculationError

# Global registry storage (protected by _LOCK)
_registry: dict[str, Callable[..., Any]] = {}
_dependencies: dict[str, set[str]] = defaultdict(set)
_LOCK = RLock()


def calc(
    name: str, *, depends_on: tuple[str, ...] = ()
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator to register a calculation function with its dependencies.

    Args:
        name: Unique name for the calculation
        depends_on: Tuple of calculation names this function depends on

    Raises:
        CalculationError: If the name is invalid, already registered, or self-dependent.
    """
    if not isinstance(name, str) or not name.strip():
        raise CalculationError("Calculation name must be a non-empty string.")
    if name in depends_on:
        raise CalculationError(f"Calculation '{name}' cannot depend on itself.")

    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        # We do NOT wrap: attach metadata to the same function object we store.
        with _LOCK:
            if name in _registry:
                raise CalculationError(f"Calculation '{name}' already registered")
            _registry[name] = fn
            _dependencies[name].update(depends_on)

        # Store metadata on the function for introspection
        fn._calc_name = name
        fn._calc_depends_on = depends_on

        return fn

    return decorator


def get(name: str) -> Callable[..., Any]:
    """Get a registered calculation function by name."""
    with _LOCK:
        try:
            return _registry[name]
        except KeyError as e:
            raise KeyError(f"Calculation '{name}' not found in registry") from e


def deps(name: str) -> set[str]:
    """Get dependencies for a calculation (copy)."""
    with _LOCK:
        if name not in _registry:
            raise KeyError(f"Calculation '{name}' not found in registry")
        return set(_dependencies[name])


def list_calculations() -> dict[str, set[str]]:
    """List all registered calculations and their dependencies (copies)."""
    with _LOCK:
        return {calc_name: set(dep_set) for calc_name, dep_set in _dependencies.items()}


def clear_registry() -> None:
    """Clear all registered calculations. Primarily for testing."""
    with _LOCK:
        _registry.clear()
        _dependencies.clear()


def is_registered(name: str) -> bool:
    """Check if a calculation is registered."""
    with _LOCK:
        return name in _registry


# ---- Optional: small helpers you may find useful ----


def unregister(name: str) -> None:
    """Remove a calculation from the registry (and its edges)."""
    with _LOCK:
        if name in _registry:
            del _registry[name]
        if name in _dependencies:
            del _dependencies[name]
        # remove from others' dependency sets
        for dep_set in _dependencies.values():
            dep_set.discard(name)


def dependency_graph() -> Mapping[str, set[str]]:
    """Get a read-only view of the dependency graph (copies of sets)."""
    with _LOCK:
        return {k: set(v) for k, v in _dependencies.items()}


def detect_cycles() -> set[tuple[str, ...]]:
    """
    Return a set of cycles detected in the dependency graph (as tuples).
    Simple DFS; fine for small graphs.
    """
    with _LOCK:
        graph = {k: set(v) for k, v in _dependencies.items()}
    cycles: set[tuple[str, ...]] = set()
    visiting: set[str] = set()
    visited: set[str] = set()
    stack: list[str] = []

    def dfs(node: str) -> None:
        if node in visited:
            return
        if node in visiting:
            # found a back-edge → record cycle
            if node in stack:
                i = stack.index(node)
                cyc = tuple(stack[i:] + [node])
                cycles.add(cyc)
            return
        visiting.add(node)
        stack.append(node)
        for nei in graph.get(node, ()):
            dfs(nei)
        stack.pop()
        visiting.remove(node)
        visited.add(node)

    for n in list(graph):
        dfs(n)
    return cycles
