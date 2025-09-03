from importlib.metadata import entry_points
from typing import Optional


def _load_entry_points(group: str):
    eps = entry_points()
    select = getattr(eps, "select", None)
    if callable(select):
        return select(group=group)
    return eps.get(group, [])


def load_plugins(context: Optional[dict] = None) -> int:
    processed = 0

    for ep in _load_entry_points("metricengine.plugins"):
        try:
            obj = ep.load()
            plugin = obj() if isinstance(obj, type) else obj
            initialize = getattr(plugin, "initialize", None)
            if callable(initialize):
                initialize(context=context)
            processed += 1
        except Exception:
            continue

    for ep in _load_entry_points("metricengine.calculations"):
        try:
            obj = ep.load()
            collection = obj() if isinstance(obj, type) else obj
            register_all = getattr(collection, "register_all", None)
            if callable(register_all):
                # Late import to avoid heavy import cost if unused
                from .registry import calc as _calc

                def _register(name: Optional[str] = None):
                    return _calc(name or "")

                register_all(register=_register)
            processed += 1
        except Exception:
            continue

    return processed
