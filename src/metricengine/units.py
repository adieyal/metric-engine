import inspect
import logging
from collections import deque
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Callable, Optional

# ============================================================================
# Legacy unit classes for backward compatibility
# These will be replaced in future tasks but are kept for now to avoid breaking existing code
# ============================================================================


class Unit:
    """Base unit class."""

    pass


class Dimensionless(Unit):
    """Unit for dimensionless values."""

    pass


class Ratio(Unit):
    """Unit for ratio values."""

    pass


class Percent(Ratio):
    """Unit for percentage values (inherits from Ratio)."""

    pass  # Inherits from Ratio since it's just display-tagged


class Money(Unit):
    """Unit for monetary values."""

    code: str = "USD"  # Default currency code

    def __init_subclass__(cls, code: str = "USD", **kwargs):
        super().__init_subclass__(**kwargs)
        cls.code = code


# Helper function to create Money units with specific currencies
def currency_unit(code: str) -> type[Money]:
    """Create a Money unit class with a specific currency code."""

    class CurrencyMoney(Money, code=code):
        pass

    CurrencyMoney.__name__ = f"Money_{code}"
    return CurrencyMoney


# Common currency units
USD = currency_unit("USD")
EUR = currency_unit("EUR")
GBP = currency_unit("GBP")
ZAR = currency_unit("ZAR")


# ============================================================================
# New Unit system - Task 1 implementation
# ============================================================================


@dataclass(frozen=True)
class NewUnit:
    """Generic unit with category and code dimensions.

    A unit represents a measurement dimension with both a category (the type of
    measurement) and a specific code (the particular unit within that category).
    Units are immutable and hashable, making them suitable for use as dictionary
    keys in conversion registries.

    Attributes:
        category: The category of measurement (e.g., "Money", "Quantity", "Percent")
        code: The specific unit code within the category (e.g., "USD", "kg", "ratio")

    Examples:
        >>> usd = NewUnit("Money", "USD")
        >>> str(usd)
        'Money[USD]'
        >>> kg = NewUnit("Quantity", "kg")
        >>> str(kg)
        'Quantity[kg]'
        >>> ratio = NewUnit("Percent", "ratio")
        >>> str(ratio)
        'Percent[ratio]'
    """

    category: str  # "Money", "Quantity", "Percent", "Custom"
    code: str  # "USD", "GBP", "kg", "L", "bp", "seats"

    def __str__(self) -> str:
        """Return string representation in 'Category[code]' format.

        Returns:
            String in the format "Category[code]" for easy identification
        """
        return f"{self.category}[{self.code}]"


# Helper functions for convenient unit creation
def MoneyUnit(code: str) -> NewUnit:
    """Create a Money unit with the specified currency code.

    Args:
        code: Currency code (e.g., "USD", "GBP", "EUR")

    Returns:
        NewUnit with "Money" category and the specified code

    Example:
        >>> usd = MoneyUnit("USD")
        >>> str(usd)
        'Money[USD]'
    """
    return NewUnit("Money", code)


def Qty(code: str) -> NewUnit:
    """Create a Quantity unit with the specified unit code.

    Args:
        code: Quantity unit code (e.g., "kg", "L", "m")

    Returns:
        NewUnit with "Quantity" category and the specified code

    Example:
        >>> kg = Qty("kg")
        >>> str(kg)
        'Quantity[kg]'
    """
    return NewUnit("Quantity", code)


def Pct(code: str = "ratio") -> NewUnit:
    """Create a Percent unit with the specified code.

    Args:
        code: Percent unit code, defaults to "ratio"

    Returns:
        NewUnit with "Percent" category and the specified code

    Example:
        >>> ratio = Pct()
        >>> str(ratio)
        'Percent[ratio]'
        >>> bp = Pct("bp")
        >>> str(bp)
        'Percent[bp]'
    """
    return NewUnit("Percent", code)


# ============================================================================
# Conversion System Foundation - Task 4 implementation
# ============================================================================


@dataclass(frozen=True)
class ConversionContext:
    """Context information for unit conversions.

    Provides metadata and timing information that conversion functions
    can use to perform dynamic rate lookups or apply business rules.
    This allows conversion functions to access external data sources
    like exchange rate APIs or historical rate databases.

    Attributes:
        at: Optional timestamp or date string for rate lookups
        meta: Dictionary of additional metadata (rates, tenant info, etc.)

    Examples:
        >>> # Simple context with timestamp
        >>> ctx = ConversionContext(at="2025-09-06T10:30:00Z")
        >>>
        >>> # Context with metadata
        >>> ctx = ConversionContext(
        ...     at="2025-09-06",
        ...     meta={"rate": "0.79", "source": "ECB"}
        ... )
    """

    at: Optional[str] = None  # timestamp, date for rate lookups
    meta: dict[str, str] = field(default_factory=dict)  # rates, tenant info, etc.


@dataclass(frozen=True)
class Conversion:
    """Represents a registered conversion between two units.

    Contains the source unit, destination unit, and the function
    that performs the actual conversion calculation. Conversion
    functions receive the value to convert and a context object
    that can provide additional information like exchange rates.

    Attributes:
        src: Source unit for the conversion
        dst: Destination unit for the conversion
        fn: Function that performs the conversion, taking (Decimal, ConversionContext) -> Decimal

    Examples:
        >>> usd = MoneyUnit("USD")
        >>> gbp = MoneyUnit("GBP")
        >>>
        >>> def usd_to_gbp(value: Decimal, ctx: ConversionContext) -> Decimal:
        ...     return value * Decimal("0.79")
        >>>
        >>> conversion = Conversion(usd, gbp, usd_to_gbp)
    """

    src: NewUnit
    dst: NewUnit
    fn: Callable[[Decimal, ConversionContext], Decimal]


# Global conversion registry
_conversion_registry: dict[tuple[NewUnit, NewUnit], Conversion] = {}

# Logger for conversion system
_logger = logging.getLogger(__name__)


def register_conversion(src: NewUnit, dst: NewUnit):
    """Decorator for registering conversion functions between units.

    The decorated function must accept a Decimal value and ConversionContext,
    and return a Decimal result.

    Args:
        src: Source unit for the conversion
        dst: Destination unit for the conversion

    Returns:
        Decorator function that registers the conversion

    Raises:
        ValueError: If the function signature is invalid

    Example:
        >>> usd = MoneyUnit("USD")
        >>> gbp = MoneyUnit("GBP")
        >>>
        >>> @register_conversion(usd, gbp)
        ... def usd_to_gbp(value: Decimal, ctx: ConversionContext) -> Decimal:
        ...     # Simple fixed rate for example
        ...     return value * Decimal("0.79")
    """

    def decorator(fn: Callable[[Decimal, ConversionContext], Decimal]):
        # Validate function signature
        sig = inspect.signature(fn)
        params = list(sig.parameters.keys())

        if len(params) != 2:
            raise ValueError(
                f"Conversion function must accept exactly 2 parameters (value, context), "
                f"got {len(params)}: {params}"
            )

        # Check parameter types if annotations are present
        param_values = list(sig.parameters.values())
        if param_values[0].annotation not in (inspect.Parameter.empty, Decimal):
            raise ValueError(
                f"First parameter must be Decimal, got {param_values[0].annotation}"
            )
        if param_values[1].annotation not in (
            inspect.Parameter.empty,
            ConversionContext,
        ):
            raise ValueError(
                f"Second parameter must be ConversionContext, got {param_values[1].annotation}"
            )

        # Check return type if annotation is present
        if sig.return_annotation not in (inspect.Parameter.empty, Decimal):
            raise ValueError(
                f"Return type must be Decimal, got {sig.return_annotation}"
            )

        # Register the conversion
        conversion = Conversion(src, dst, fn)
        _conversion_registry[(src, dst)] = conversion

        return fn

    return decorator


def get_conversion(src: NewUnit, dst: NewUnit) -> Conversion:
    """Get a registered conversion between two units.

    Args:
        src: Source unit
        dst: Destination unit

    Returns:
        Conversion object containing the conversion function

    Raises:
        KeyError: If no conversion is registered for the unit pair
    """
    try:
        return _conversion_registry[(src, dst)]
    except KeyError as e:
        # Create descriptive error message with available conversions
        available_from_src = [
            dst_unit
            for (src_unit, dst_unit) in _conversion_registry.keys()
            if src_unit == src
        ]
        available_to_dst = [
            src_unit
            for (src_unit, dst_unit) in _conversion_registry.keys()
            if dst_unit == dst
        ]

        error_msg = f"No conversion registered from {src} to {dst}"

        if available_from_src:
            error_msg += f". Available conversions from {src}: {[str(unit) for unit in available_from_src]}"

        if available_to_dst:
            error_msg += f". Available conversions to {dst}: {[str(unit) for unit in available_to_dst]}"

        if not available_from_src and not available_to_dst:
            total_conversions = len(_conversion_registry)
            if total_conversions == 0:
                error_msg += ". No conversions are currently registered"
            else:
                error_msg += f". {total_conversions} conversions are registered for other unit pairs"

        raise KeyError(error_msg) from e


def list_conversions() -> dict[tuple[NewUnit, NewUnit], Conversion]:
    """Get a copy of all registered conversions.

    Returns:
        Dictionary mapping unit pairs to their conversions
    """
    return _conversion_registry.copy()


def _neighbors(unit: NewUnit) -> list[NewUnit]:
    """Find all units that can be directly converted from the given unit.

    Args:
        unit: The source unit to find neighbors for

    Returns:
        List of units that have direct conversions from the source unit
    """
    neighbors = []
    for src, dst in _conversion_registry.keys():
        if src == unit:
            neighbors.append(dst)
    return neighbors


def _find_path(src: NewUnit, dst: NewUnit) -> list[Conversion]:
    """Find the shortest conversion path between two units using BFS.

    Uses breadth-first search to find the shortest path (fewest hops) between
    the source and destination units through the conversion registry.

    Args:
        src: Source unit
        dst: Destination unit

    Returns:
        List of Conversion objects representing the path from src to dst

    Raises:
        KeyError: If no path exists between the units
    """
    if src == dst:
        return []

    # BFS to find shortest path

    # Queue contains tuples of (current_unit, path_to_current)
    queue = deque([(src, [])])
    visited = {src}

    while queue:
        current_unit, path = queue.popleft()

        # Check all neighbors of current unit
        for neighbor in _neighbors(current_unit):
            if neighbor == dst:
                # Found destination, return complete path
                conversion = _conversion_registry[(current_unit, neighbor)]
                return path + [conversion]

            if neighbor not in visited:
                visited.add(neighbor)
                conversion = _conversion_registry[(current_unit, neighbor)]
                queue.append((neighbor, path + [conversion]))

    # No path found - create descriptive error message
    all_units = set()
    for src_unit, dst_unit in _conversion_registry.keys():
        all_units.add(src_unit)
        all_units.add(dst_unit)

    error_msg = f"No conversion path found from {src} to {dst}"

    if src not in all_units:
        error_msg += f". Source unit {src} has no registered conversions"
    elif dst not in all_units:
        error_msg += f". Destination unit {dst} has no registered conversions"
    else:
        # Both units exist in registry but no path between them
        src_neighbors = _neighbors(src)
        dst_sources = [
            src_unit
            for (src_unit, dst_unit) in _conversion_registry.keys()
            if dst_unit == dst
        ]

        error_msg += f". {src} can convert to: {[str(unit) for unit in src_neighbors]}"
        error_msg += (
            f". {dst} can be converted from: {[str(unit) for unit in dst_sources]}"
        )
        error_msg += ". These conversion networks are not connected"

    raise KeyError(error_msg)


# ============================================================================
# Conversion Policy System - Task 7 implementation
# ============================================================================


@dataclass(frozen=True)
class ConversionPolicy:
    """Policy configuration for unit conversions.

    Controls the behavior of the conversion system, including whether to
    raise errors on missing conversions and whether to allow multi-hop
    conversion paths through intermediate units.

    Attributes:
        strict: If True, raise KeyError on missing conversions; if False, return original value
        allow_paths: If True, enable multi-hop conversions; if False, only direct conversions

    Examples:
        >>> # Strict policy (default) - raises on missing conversions
        >>> strict_policy = ConversionPolicy(strict=True, allow_paths=True)
        >>>
        >>> # Permissive policy - returns original value on missing conversions
        >>> permissive_policy = ConversionPolicy(strict=False, allow_paths=True)
        >>>
        >>> # Direct-only policy - no multi-hop conversions
        >>> direct_only = ConversionPolicy(strict=True, allow_paths=False)
    """

    strict: bool = True  # Raise on missing conversion vs return original
    allow_paths: bool = True  # Enable multi-hop conversions


# Context variable for scoped conversion policy
_current_conversion_policy: ContextVar[ConversionPolicy] = ContextVar(
    "_current_conversion_policy", default=ConversionPolicy()
)


@contextmanager
def use_conversions(policy: ConversionPolicy):
    """Context manager for scoped conversion policy.

    Temporarily sets the conversion policy for the duration of the context.
    The previous policy is restored when the context exits.

    Args:
        policy: ConversionPolicy to use within the context

    Example:
        >>> permissive_policy = ConversionPolicy(strict=False, allow_paths=True)
        >>> with use_conversions(permissive_policy):
        ...     # Conversions within this block use permissive policy
        ...     result = convert_decimal(value, usd, gbp)
    """
    token = _current_conversion_policy.set(policy)
    try:
        yield
    finally:
        _current_conversion_policy.reset(token)


def get_current_conversion_policy() -> ConversionPolicy:
    """Get the current conversion policy from context.

    Returns:
        Current ConversionPolicy in effect
    """
    return _current_conversion_policy.get()


def convert_decimal(
    value: Decimal,
    src: NewUnit,
    dst: NewUnit,
    *,
    at: Optional[str] = None,
    meta: Optional[dict[str, str]] = None,
) -> Decimal:
    """Convert a decimal value from one unit to another.

    This function performs unit-to-unit conversion using the registered
    conversion functions. It handles same-unit conversions by returning the
    original value unchanged, and supports multi-hop conversions through
    intermediate units when no direct conversion exists.

    The behavior is controlled by the current ConversionPolicy:
    - strict=True: Raises KeyError on missing conversions
    - strict=False: Returns original value on missing conversions
    - allow_paths=True: Enables multi-hop conversions
    - allow_paths=False: Only allows direct conversions

    Args:
        value: The decimal value to convert
        src: Source unit
        dst: Destination unit
        at: Optional timestamp for rate lookups
        meta: Optional metadata dictionary for conversion context

    Returns:
        Converted decimal value, or original value if conversion fails
        and strict=False

    Raises:
        KeyError: If no conversion path exists and strict=True
        ValueError: If conversion function raises an exception and strict=True

    Example:
        >>> usd = MoneyUnit("USD")
        >>> gbp = MoneyUnit("GBP")
        >>>
        >>> # Strict mode (default) - raises on missing conversion
        >>> result = convert_decimal(Decimal("100"), usd, gbp)
        >>>
        >>> # Permissive mode - returns original on missing conversion
        >>> policy = ConversionPolicy(strict=False)
        >>> with use_conversions(policy):
        ...     result = convert_decimal(Decimal("100"), usd, gbp)
        ...     # Returns Decimal("100") if no conversion exists
    """
    # Handle same-unit conversions
    if src == dst:
        return value

    # Get current policy
    policy = get_current_conversion_policy()

    # Create conversion context
    context = ConversionContext(at=at, meta=meta or {})

    # Try direct conversion first
    try:
        conversion = get_conversion(src, dst)
        try:
            result = conversion.fn(value, context)
            _logger.debug(f"Direct conversion from {src} to {dst}: {value} -> {result}")
            return result
        except Exception as e:
            # Conversion function raised an exception
            error_msg = f"Conversion function failed for {src} to {dst}: {type(e).__name__}: {e}"
            _logger.error(error_msg)

            if policy.strict:
                raise ValueError(error_msg) from e
            else:
                _logger.warning(
                    "Returning original value due to conversion function error in permissive mode"
                )
                return value

    except KeyError as direct_error:
        # No direct conversion available
        _logger.debug(f"No direct conversion from {src} to {dst}: {direct_error}")

        if not policy.allow_paths:
            # Multi-hop conversions disabled by policy
            _logger.info(f"Multi-hop conversions disabled by policy for {src} to {dst}")

            if policy.strict:
                raise direct_error
            else:
                _logger.warning(
                    "Returning original value due to missing direct conversion in permissive mode"
                )
                return value

        # Try multi-hop path finding
        try:
            path = _find_path(src, dst)
            _logger.debug(f"Found {len(path)}-hop conversion path from {src} to {dst}")

            # Chain conversions along the path
            current_value = value
            for i, conversion in enumerate(path):
                try:
                    previous_value = current_value
                    current_value = conversion.fn(current_value, context)
                    _logger.debug(
                        f"Path step {i+1}: {conversion.src} to {conversion.dst}: {previous_value} -> {current_value}"
                    )
                except Exception as e:
                    # Conversion function in path raised an exception
                    error_msg = f"Conversion function failed in path step {i+1} ({conversion.src} to {conversion.dst}): {type(e).__name__}: {e}"
                    _logger.error(error_msg)

                    if policy.strict:
                        raise ValueError(error_msg) from e
                    else:
                        _logger.warning(
                            f"Returning original value due to conversion function error in path step {i+1}"
                        )
                        return value

            _logger.info(
                f"Multi-hop conversion from {src} to {dst}: {value} -> {current_value}"
            )
            return current_value

        except KeyError as path_error:
            # No path found
            _logger.warning(
                f"No conversion path found from {src} to {dst}: {path_error}"
            )

            if policy.strict:
                raise path_error
            else:
                _logger.info(
                    "Returning original value due to missing conversion path in permissive mode"
                )
                return value
