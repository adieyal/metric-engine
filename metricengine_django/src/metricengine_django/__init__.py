from typing import Optional


class Plugin:
    def initialize(self, context: Optional[dict] = None) -> None:
        try:
            import django  # noqa: F401
        except Exception as exc:
            raise RuntimeError("metric-engine-django requires Django.") from exc


__all__ = ["Plugin"]
