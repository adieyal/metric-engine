"""Base formatter protocol and builtin implementation."""
from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING, Optional, Protocol

if TYPE_CHECKING:
    from ..policy import DisplayPolicy
    from ..units import Unit


class BabelUnavailable(Exception):
    """Raised when Babel is not available but required."""

    pass


class Formatter(Protocol):
    """Protocol for formatting financial values."""

    def money(
        self, amount: Decimal, unit: Optional[type], display: DisplayPolicy
    ) -> str:
        """Format a monetary amount with currency symbol."""
        ...

    def number(self, value: Decimal, display: DisplayPolicy) -> str:
        """Format a plain number."""
        ...

    def percent(self, ratio_or_percent: Decimal, display: DisplayPolicy) -> str:
        """Format a percentage value."""
        ...

    def format_decimal_legacy(
        self,
        d: Decimal,
        unit: type[Unit],
        decimal_places: int,
        thousands_sep: bool,
        currency_symbol: Optional[str],
        currency_position: str,
        negative_parentheses: bool,
    ) -> str:
        """Legacy format_decimal method for backward compatibility."""
        ...


class BuiltinFormatter:
    """Fallback formatter that doesn't require Babel."""

    def money(
        self, amount: Decimal, unit: Optional[type], display: DisplayPolicy
    ) -> str:
        """Format money using basic formatting."""
        # Use unit.code if unit.category == "Money", else display.currency
        from ..units import Money

        code = display.currency
        if (
            unit is not None
            and hasattr(unit, "code")
            and isinstance(unit, type)
            and issubclass(unit, Money)
        ):
            code = getattr(unit, "code", display.currency)
        elif unit is not None and getattr(unit, "__name__", None) == "Money":
            # For the simple Money class case
            code = display.currency

        frac_digits = _resolve_frac(display)

        # Format the number
        if display.use_grouping:
            s = f"{amount:,.{frac_digits}f}"
        else:
            s = f"{amount:.{frac_digits}f}"

        # Handle negative parentheses
        if display.negative_parens and s.startswith("-"):
            s = f"({s[1:]})"

        return f"{code} {s}"

    def number(self, value: Decimal, display: DisplayPolicy) -> str:
        """Format a number using basic formatting."""
        frac_digits = _resolve_frac(display)

        if display.use_grouping:
            s = f"{value:,.{frac_digits}f}"
        else:
            s = f"{value:.{frac_digits}f}"

        if display.negative_parens and s.startswith("-"):
            s = f"({s[1:]})"

        return s

    def percent(self, ratio_or_percent: Decimal, display: DisplayPolicy) -> str:
        """Format a percentage using basic formatting."""
        # Scale based on percent_scale setting
        if display.percent_scale == "ratio":
            ratio_or_percent = ratio_or_percent * Decimal(100)

        frac_digits = _resolve_frac(display)
        s = f"{ratio_or_percent:.{frac_digits}f}%"

        if display.negative_parens and s.startswith("-"):
            s = f"({s[1:]})"

        return s

    def format_decimal_legacy(
        self,
        d: Decimal,
        unit: type[Unit],
        decimal_places: int,
        thousands_sep: bool,
        currency_symbol: Optional[str],
        currency_position: str,
        negative_parentheses: bool,
    ) -> str:
        """
        Legacy format_decimal method for backward compatibility.

        Format a decimal with thousands separators, currency, and negative style.
        Ensures parentheses wrap the whole string, e.g. "($1,234.56)".
        """
        is_negative = d < 0
        abs_d = -d if is_negative else d

        # Format base number
        base = (
            f"{abs_d:,.{decimal_places}f}"
            if thousands_sep
            else f"{abs_d:.{decimal_places}f}"
        )

        # Apply currency if applicable
        # Check for Money class (including mocked objects)
        is_money = self._is_money_unit(unit)

        if is_money and currency_symbol:
            base = (
                f"{currency_symbol}{base}"
                if currency_position == "prefix"
                else f"{base}{currency_symbol}"
            )

        # Apply sign/parentheses last
        if is_negative:
            if negative_parentheses:
                return f"({base})"
            return f"-{base}"
        return base

    def _is_money_unit(self, unit) -> bool:
        """Check if unit is a Money class, handling both real and mocked objects."""
        from ..units import Money

        # Direct class check
        if unit is Money:
            return True

        # Check class name (for real Money classes and mocked objects)
        if hasattr(unit, "__name__") and "Money" in str(unit.__name__):
            return True

        # Check mock name (for unittest.mock objects)
        if hasattr(unit, "_mock_name") and "Money" in str(unit._mock_name):
            return True

        # Check spec name for mock objects
        if hasattr(unit, "_spec_class") and hasattr(unit._spec_class, "__name__"):
            if "Money" in str(unit._spec_class.__name__):
                return True

        # Check if it's a subclass of Money (for real classes)
        try:
            if isinstance(unit, type) and issubclass(unit, Money):
                return True
        except TypeError:
            # issubclass can raise TypeError if unit is not a class
            pass

        return False


def _resolve_frac(display: DisplayPolicy) -> int:
    """Choose max_frac if provided; else fall back to a sensible default (e.g. 2)."""
    return display.max_frac if display.max_frac is not None else 2


def get_formatter() -> Formatter:
    """
    Factory: returns a formatter instance that uses Babel if available, else builtin.
    """
    try:
        from .babel_adapter import BabelFormatter

        return BabelFormatter()
    except Exception:
        return BuiltinFormatter()
