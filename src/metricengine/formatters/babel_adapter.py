"""Babel-based formatter for locale-aware formatting."""
from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ..policy import DisplayPolicy
    from ..units import Unit

try:
    from babel import numbers as bn
    from babel.core import Locale

    BABEL_AVAILABLE = True
except ImportError:
    BABEL_AVAILABLE = False
    bn = None
    Locale = None

from .base import BabelUnavailable, Formatter


class BabelFormatter(Formatter):
    """Babel-backed formatter for locale-aware formatting."""

    def __init__(self):
        if not BABEL_AVAILABLE:
            raise BabelUnavailable("Babel is not installed")

    def _locale(self, display: DisplayPolicy):
        """Get a valid Locale object, falling back if needed."""
        if Locale is None:
            raise BabelUnavailable("Babel is not available")
        try:
            return Locale.parse(display.locale)
        except Exception:
            return Locale.parse(display.fallback_locale)

    def money(
        self, amount: Decimal, unit: Optional[type], display: DisplayPolicy
    ) -> str:
        """Format money using Babel's currency formatting."""
        loc = self._locale(display)

        # Determine currency code
        from ..units import Money

        currency = display.currency
        if (
            unit is not None
            and hasattr(unit, "code")
            and isinstance(unit, type)
            and issubclass(unit, Money)
        ):
            currency = getattr(unit, "code", display.currency)
        elif unit is not None and getattr(unit, "__name__", None) == "Money":
            # For the simple Money class case, use display currency
            currency = display.currency

        # Build formatting arguments
        kwargs = {
            "locale": loc,
            "currency": currency,
            "grouping": display.use_grouping,
        }

        # Handle fraction digits via pattern
        pattern = None
        if display.max_frac is not None:
            frac = display.max_frac
            min_frac = display.min_frac if display.min_frac is not None else 0
            if min_frac > frac:
                min_frac = frac

            # Build CLDR-style pattern like ¤#,##0.00
            pattern = "¤#,##0"
            if frac > 0:
                pattern += "." + ("0" * min_frac) + ("#" * (frac - min_frac))

            kwargs["format"] = pattern

        # Format using Babel
        if bn is None:
            raise BabelUnavailable("Babel is not available")

        # Format arguments for Babel
        format_args = {
            "currency": currency,
            "locale": loc,
            "decimal_quantization": False,
        }

        if kwargs.get("format"):
            format_args["format"] = kwargs["format"]

        # Only add grouping if supported by this Babel version
        try:
            s = bn.format_currency(amount, grouping=display.use_grouping, **format_args)
        except TypeError:
            # Fallback for older Babel versions that don't support grouping parameter
            s = bn.format_currency(amount, **format_args)

        # Handle accounting style / parentheses
        if (
            display.currency_style == "accounting" or display.negative_parens
        ) and s.startswith("-"):
            s = f"({s[1:]})"

        return s

    def number(self, value: Decimal, display: DisplayPolicy) -> str:
        """Format a number using Babel's decimal formatting."""
        loc = self._locale(display)

        # Try compact formatting first
        if display.compact in ("short", "long"):
            try:
                if bn is None:
                    raise BabelUnavailable("Babel is not available")
                return bn.format_decimal(
                    value,
                    locale=loc,
                    format=None,
                    decimal_quantization=False,
                    grouping=display.use_grouping,
                    # Note: compact parameter might not be supported in all Babel versions
                )
            except (TypeError, AttributeError):
                # Fallback to non-compact formatting
                pass

        # Build pattern for fraction digits control
        pattern = None
        if display.max_frac is not None:
            frac = display.max_frac
            min_frac = display.min_frac if display.min_frac is not None else 0
            if min_frac > frac:
                min_frac = frac

            # Pattern like '#,##0.00##'
            pattern = "#,##0"
            if frac > 0:
                pattern += "." + ("0" * min_frac) + ("#" * (frac - min_frac))

        if bn is None:
            raise BabelUnavailable("Babel is not available")

        # Format arguments
        format_args = {
            "locale": loc,
            "format": pattern,
            "decimal_quantization": False,
        }

        # Try with grouping parameter, fallback if not supported
        try:
            s = bn.format_decimal(value, grouping=display.use_grouping, **format_args)
        except TypeError:
            s = bn.format_decimal(value, **format_args)

        if display.negative_parens and s.startswith("-"):
            s = f"({s[1:]})"

        return s

    def percent(self, ratio_or_percent: Decimal, display: DisplayPolicy) -> str:
        """Format a percentage using Babel's percent formatting."""
        loc = self._locale(display)

        # Scale if using ratio semantics
        value = (
            ratio_or_percent * Decimal(100)
            if display.percent_scale == "ratio"
            else ratio_or_percent
        )

        # Build pattern for fraction control
        pattern = None
        if display.max_frac is not None:
            frac = display.max_frac
            min_frac = display.min_frac if display.min_frac is not None else 0
            if min_frac > frac:
                min_frac = frac

            # CLDR percent pattern like '#,##0.00%'
            pattern = "#,##0"
            if frac > 0:
                pattern += "." + ("0" * min_frac) + ("#" * (frac - min_frac))
            pattern += "%"

        if bn is None:
            raise BabelUnavailable("Babel is not available")

        # Format arguments
        format_args = {
            "locale": loc,
            "format": pattern,
            "decimal_quantization": False,
        }

        # Convert to ratio for Babel (it expects 0.15 for 15%, not 15)
        ratio_value = value / 100

        # Try with grouping parameter, fallback if not supported
        try:
            s = bn.format_percent(
                ratio_value, grouping=display.use_grouping, **format_args
            )
        except TypeError:
            s = bn.format_percent(ratio_value, **format_args)

        if (
            display.percent_style == "accounting" or display.negative_parens
        ) and s.startswith("-"):
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

        For Babel formatter, we can fall back to the builtin implementation
        since this is legacy functionality that doesn't need locale awareness.
        """
        from .base import BuiltinFormatter

        builtin = BuiltinFormatter()
        return builtin.format_decimal_legacy(
            d=d,
            unit=unit,
            decimal_places=decimal_places,
            thousands_sep=thousands_sep,
            currency_symbol=currency_symbol,
            currency_position=currency_position,
            negative_parentheses=negative_parentheses,
        )
