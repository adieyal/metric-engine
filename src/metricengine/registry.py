"""Registry for financial calculations with dependency tracking."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping
from threading import RLock
from typing import Any, Callable

from .exceptions import CalculationError


class Registry:
    """Thread-safe registry of calculation functions and dependencies."""

    def __init__(self) -> None:
        self._registry: dict[str, Callable[..., Any]] = {}
        self._dependencies: dict[str, set[str]] = defaultdict(set)
        self._loaded_groups: set[str] = set()
        self._lock = RLock()

    def calc(
        self, name: str, *, depends_on: tuple[str, ...] = ()
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
            with self._lock:
                if name in self._registry:
                    raise CalculationError(f"Calculation '{name}' already registered")
                self._registry[name] = fn
                self._dependencies[name].update(depends_on)

            fn._calc_name = name
            fn._calc_depends_on = depends_on
            return fn

        return decorator

    def get(self, name: str) -> Callable[..., Any]:
        """Get a registered calculation function by name."""
        with self._lock:
            try:
                return self._registry[name]
            except KeyError as e:
                raise KeyError(f"Calculation '{name}' not found in registry") from e

    def deps(self, name: str) -> set[str]:
        """Get dependencies for a calculation (copy)."""
        with self._lock:
            if name not in self._registry:
                raise KeyError(f"Calculation '{name}' not found in registry")
            return set(self._dependencies[name])

    def list_calculations(self) -> dict[str, set[str]]:
        """List all registered calculations and their dependencies (copies)."""
        with self._lock:
            return {
                calc_name: set(dep_set)
                for calc_name, dep_set in self._dependencies.items()
            }

    def clear(self) -> None:
        """Clear all registered calculations. Primarily for testing."""
        with self._lock:
            self._registry.clear()
            self._dependencies.clear()
            self._loaded_groups.clear()

    def is_registered(self, name: str) -> bool:
        """Check if a calculation is registered."""
        with self._lock:
            return name in self._registry

    def unregister(self, name: str) -> None:
        """Remove a calculation from the registry (and its edges)."""
        with self._lock:
            if name in self._registry:
                del self._registry[name]
            if name in self._dependencies:
                del self._dependencies[name]
            for dep_set in self._dependencies.values():
                dep_set.discard(name)

    def dependency_graph(self) -> Mapping[str, set[str]]:
        """Get a read-only view of the dependency graph (copies of sets)."""
        with self._lock:
            return {k: set(v) for k, v in self._dependencies.items()}

    def detect_cycles(self) -> set[tuple[str, ...]]:
        """
        Return a set of cycles detected in the dependency graph (as tuples).

        Simple DFS; fine for small graphs.
        """
        with self._lock:
            graph = {k: set(v) for k, v in self._dependencies.items()}

        cycles: set[tuple[str, ...]] = set()
        visiting: set[str] = set()
        visited: set[str] = set()
        stack: list[str] = []

        def dfs(node: str) -> None:
            if node in visited:
                return
            if node in visiting:
                if node in stack:
                    i = stack.index(node)
                    cycles.add(tuple(stack[i:] + [node]))
                return
            visiting.add(node)
            stack.append(node)
            for nei in graph.get(node, ()):
                dfs(nei)
            stack.pop()
            visiting.remove(node)
            visited.add(node)

        for node in list(graph):
            dfs(node)
        return cycles

    def get_all(self) -> dict[str, dict[str, Any]]:
        """Return calculation metadata for all registered calculations."""
        with self._lock:
            return {
                name: {
                    "function": calc_func,
                    "depends_on": set(self._dependencies[name]),
                    "docstring": calc_func.__doc__ or "",
                }
                for name, calc_func in self._registry.items()
            }

    def mark_loaded(self, group: str) -> None:
        """Mark a logical registration group as loaded into this registry."""
        with self._lock:
            self._loaded_groups.add(group)

    def is_loaded(self, group: str) -> bool:
        """Check whether a logical registration group has been loaded."""
        with self._lock:
            return group in self._loaded_groups


default_registry = Registry()
_registry = default_registry._registry
_dependencies = default_registry._dependencies


def calc(
    name: str, *, depends_on: tuple[str, ...] = ()
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Register a calculation in the default registry."""
    return default_registry.calc(name, depends_on=depends_on)


def get(name: str) -> Callable[..., Any]:
    """Get a registered calculation function by name from the default registry."""
    return default_registry.get(name)


def deps(name: str) -> set[str]:
    """Get dependencies for a calculation from the default registry."""
    return default_registry.deps(name)


def list_calculations() -> dict[str, set[str]]:
    """List all registered calculations in the default registry."""
    return default_registry.list_calculations()


def clear_registry() -> None:
    """Clear the default registry. Primarily for testing."""
    default_registry.clear()


def is_registered(name: str) -> bool:
    """Check if a calculation is registered in the default registry."""
    return default_registry.is_registered(name)


def unregister(name: str) -> None:
    """Remove a calculation from the default registry."""
    default_registry.unregister(name)


def dependency_graph() -> Mapping[str, set[str]]:
    """Get a read-only view of the default registry dependency graph."""
    return default_registry.dependency_graph()


def detect_cycles() -> set[tuple[str, ...]]:
    """Return cycles detected in the default registry dependency graph."""
    return default_registry.detect_cycles()
