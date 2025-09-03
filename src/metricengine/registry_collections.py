from .registry import calc as _calc


class Collection:
    def __init__(self, namespace: str = ""):
        self.ns = namespace.strip(".")

    def _qualify(self, name: str) -> str:
        # Flatten names for public API; allow explicit absolute via ":" prefix
        return name.lstrip(":")

    def calc(self, name: str, *, depends_on: tuple[str, ...] = ()):
        full = self._qualify(name)
        deps = tuple(self._qualify(d) for d in depends_on)
        return _calc(full, depends_on=deps)
