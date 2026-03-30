from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Callable

from .registry import Registry, default_registry

_active_registry: ContextVar[Registry | None] = ContextVar(
    "metricengine_active_registry", default=None
)


@contextmanager
def using_registry(registry: Registry) -> Iterator[None]:
    """Temporarily bind collection registration to a specific registry."""
    token = _active_registry.set(registry)
    try:
        yield
    finally:
        _active_registry.reset(token)


def get_active_registry() -> Registry:
    """Return the currently active collection registry, if any."""
    return _active_registry.get() or default_registry


class Collection:
    def __init__(self, namespace: str = "", registry: Registry | None = None):
        self.ns = namespace.strip(".")
        self.registry = registry or get_active_registry()
        self._registered_functions: list[Callable[..., object]] = []
        self._registered_function_set: set[Callable[..., object]] = set()

    def _qualify(self, name: str) -> str:
        # Flatten names for public API; allow explicit absolute via ":" prefix
        return name.lstrip(":")

    def calc(self, name: str, *, depends_on: tuple[str, ...] = ()):
        full = self._qualify(name)
        deps = tuple(self._qualify(d) for d in depends_on)
        registry_decorator = self.registry.calc(full, depends_on=deps)

        def decorator(fn: Callable[..., object]) -> Callable[..., object]:
            registered = registry_decorator(fn)
            if registered not in self._registered_function_set:
                self._registered_functions.append(registered)
                self._registered_function_set.add(registered)
            return registered

        return decorator

    def registered_functions(self) -> tuple[Callable[..., object], ...]:
        """Return the functions registered through this collection."""
        return tuple(self._registered_functions)
