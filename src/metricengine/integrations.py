from importlib.metadata import entry_points
from typing import Optional

from .registry import Registry, default_registry


def _load_entry_points(group: str):
    eps = entry_points()
    select = getattr(eps, "select", None)
    if callable(select):
        return select(group=group)
    return eps.get(group, [])


def load_plugins(
    context: Optional[dict] = None,
    registry: Registry | None = None,
) -> int:
    processed = 0
    target_registry = registry or default_registry
    effective_context = {} if context is None else dict(context)
    effective_context.setdefault("registry", target_registry)

    for ep in _load_entry_points("metricengine.plugins"):
        try:
            obj = ep.load()
            plugin = obj() if isinstance(obj, type) else obj
            initialize = getattr(plugin, "initialize", None)
            if callable(initialize):
                initialize(context=effective_context)
            processed += 1
        except Exception:
            continue

    for ep in _load_entry_points("metricengine.calculations"):
        try:
            obj = ep.load()
            collection = obj() if isinstance(obj, type) else obj
            register_all = getattr(collection, "register_all", None)
            if callable(register_all):

                def _register(name: Optional[str] = None, *, depends_on=()):
                    return target_registry.calc(name or "", depends_on=depends_on)

                register_all(register=_register)
            processed += 1
        except Exception:
            continue

    return processed
