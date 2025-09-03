from functools import lru_cache
from typing import Any, Callable

from .exceptions import CalculationError
from .registry import deps
from .registry import get as _get
from .registry import list_calculations as _list

try:
    from ._typed_forwarders import *  # noqa: F401,F403
except Exception:
    # ok before first generation or in minimal envs
    pass


# Ensure calculations are loaded when this module is imported
def _ensure_calculations_loaded():
    """Ensure all calculation modules are imported and registered."""
    try:
        # Import the calculations module and call load_all
        import importlib

        calculations_module = importlib.import_module(
            ".calculations", package=__package__
        )
        calculations_module.load_all()
    except Exception:
        # Be resilient if calculation modules are unavailable
        pass


# Load calculations on module import
_ensure_calculations_loaded()


@lru_cache(maxsize=128)
def get_calc(name: str) -> Callable[..., Any]:
    """
    Get a registered calculation function by name.

    Args:
        name: The name of the calculation to retrieve

    Returns:
        The calculation function

    Raises:
        CalculationError: If the calculation is not found or name is invalid

    Example:
        >>> cogs = get_calc("cogs")
        >>> result = cogs(opening_inventory=FV(100), purchases=FV(150), closing_inventory=FV(100))
    """
    if not isinstance(name, str) or not name.strip():
        raise CalculationError("Calculation name must be a non-empty string")

    try:
        func = _get(name)
        return func
    except KeyError as e:
        available = sorted(_list().keys())
        raise CalculationError(
            f"Calculation '{name}' not found. Available calculations: {available}"
        ) from e


def calc_names() -> list[str]:
    """Get a sorted list of all available calculation names."""
    return sorted(_list().keys())


def is_calc_available(name: str) -> bool:
    """Check if a calculation is available without raising an exception."""
    return name in _list()


def get_calc_info(name: str) -> dict[str, Any]:
    """Get comprehensive information about a calculation."""
    calc_func = get_calc(name)
    return {
        "name": name,
        "function": calc_func,
        "docstring": calc_func.__doc__,
        "dependencies": deps(name),
    }


def search_calcs(query: str) -> list[str]:
    """Search for calculations by name (case-insensitive)."""
    query = query.lower()
    return [name for name in calc_names() if query in name.lower()]
