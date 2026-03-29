"""Shared configuration for default calculation loading."""

_autoload_default_calculations = True


def set_default_calculations_autoload(enabled: bool) -> None:
    """Enable or disable automatic loading of built-in calculations."""
    global _autoload_default_calculations
    _autoload_default_calculations = enabled


def should_autoload_default_calculations() -> bool:
    """Return whether built-in calculations should auto-load."""
    return _autoload_default_calculations
