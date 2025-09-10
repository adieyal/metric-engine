"""Policy configuration for Metric Engine calculations."""

from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Callable, Literal, Optional


def default_quantizer_factory(decimal_places: int) -> Decimal:
    """Exact, fast quantizer for given dp: e.g., dp=2 -> Decimal('0.01')."""
    return Decimal(1).scaleb(-decimal_places)


PercentDisplay = Literal["ratio", "percent"]

# Keep imports at module scope so tests can patch
from .units import Unit


@dataclass(frozen=True)
class DisplayPolicy:
    """
    Immutable configuration for locale-aware formatting.

    This policy controls how financial values are formatted for display,
    including currency symbols, number formatting, and locale-specific
    conventions.
    """
 

    # Locale/Currency
    locale: str = "en_ZA"  # BCP-47 or ICU id; e.g., "en_US", "fr_FR", "en_ZA"
    currency: str = "ZAR"  # ISO 4217 code (fallback if FV.unit is not Money)
    currency_style: str = "standard"  # "standard" | "accounting"

    # Number formatting
    use_grouping: bool = True
    min_int: Optional[int] = None
    min_frac: Optional[int] = None
    max_frac: Optional[int] = None
    compact: Optional[str] = None  # None | "short" | "long" (e.g. 1.2K / 1.2 thousand)

    # Percent formatting
    percent_scale: str = "ratio"  # "ratio" (0.15 -> 15%) | "unit" (15 -> 15%)
    percent_style: str = (
        "standard"  # reserved: "standard" | "accounting" (same parens rules)
    )

    # Sign display
    negative_parens: bool = (
        False  # force (1.23) instead of -1.23 even outside accounting
    )

    # Fallbacks
    fallback_locale: str = "en_US"  # used if locale invalid/unavailable


@dataclass(frozen=True)
class Policy:
    """
    Immutable configuration for financial calculations and formatting.
    """

    decimal_places: int = 2
    rounding: str = ROUND_HALF_UP
    none_text: str = "—"

    # Display preference for percents
    percent_display: PercentDisplay = "percent"
    cap_percentage_at: Optional[Decimal] = field(
        default_factory=lambda: Decimal("99999.99")
    )
    # Legacy alias, kept for compatibility
    percent_style: str = "percent"

    quantizer_factory: Callable[[int], Decimal] = field(
        default=default_quantizer_factory
    )

    # Behavior toggles
    negative_sales_is_none: bool = True
    compare_none_as_minus_infinity: bool = False
    arithmetic_strict: bool = False

    # Formatting options
    thousands_sep: bool = True
    currency_symbol: Optional[str] = None
    currency_position: Literal["prefix", "suffix"] = "prefix"
    negative_parentheses: bool = False
    locale: Optional[str] = None

    # Display policy for advanced formatting
    display: Optional[DisplayPolicy] = None

    def __post_init__(self):
        if self.decimal_places < 0:
            raise ValueError("decimal_places must be non-negative")
        if self.cap_percentage_at is not None and self.cap_percentage_at < 0:
            raise ValueError("cap_percentage_at must be non-negative")
        if self.currency_symbol is not None and not self.currency_symbol.strip():
            raise ValueError("currency_symbol must be non-empty or None")

    # ---------- Helpers ----------

    def quantize(self, d: Decimal) -> Decimal:
        """
        Quantize according to policy.
        Supports arbitrary step sizes (e.g., 0.5) by rounding to nearest step.
        """
        q = self.quantizer_factory(self.decimal_places)

        # If quantizer is a power of ten, use normal quantize
        expected_power_ten = Decimal(1).scaleb(-self.decimal_places)
        if q == expected_power_ten or q.normalize() == expected_power_ten.normalize():
            return d.quantize(q, rounding=self.rounding)

        # For non power-of-ten quantizers:
        # - Use step rounding only for coarse resolutions (dp <= 1), e.g., 0.5 at 1dp
        # - Otherwise, fall back to standard dp quantization
        try:
            if self.decimal_places <= 1:
                steps = (d / q).to_integral_value(rounding=self.rounding)
                return (steps * q).quantize(q, rounding=self.rounding)
            else:
                ten_quant = expected_power_ten
                return d.quantize(ten_quant, rounding=self.rounding)
        except (InvalidOperation, ZeroDivisionError):
            return d  # fallback

    def format_decimal(self, d: Decimal, unit: "type[Unit]") -> str:
        """
        Format a decimal with thousands separators, currency, and negative style.

        This method is deprecated and will delegate to the built-in formatter
        for backward compatibility.
        """
        from .formatters.base import get_formatter

        formatter = get_formatter()
        return formatter.format_decimal_legacy(
            d=d,
            unit=unit,
            decimal_places=self.decimal_places,
            thousands_sep=self.thousands_sep,
            currency_symbol=self.currency_symbol,
            currency_position=self.currency_position,
            negative_parentheses=self.negative_parentheses,
        )

    def format_percent(self, ratio_value: Decimal) -> str:
        """
        Render ratio (0..1) as percent text.
        Always clamp to cap_percentage_at if provided.
        """
        if self.percent_display == "percent":
            # Convert to percentage scale and apply quantization/clamping
            v = ratio_value * Decimal(100)
            if self.cap_percentage_at is not None:
                v = min(v, self.cap_percentage_at)

            # Apply quantization (this matches original behavior)
            v = self.quantize(v)

            # Convert back to ratio for formatter (since we use percent_scale="ratio")
            ratio_for_formatter = v / Decimal(100)

            # Always delegate to formatter
            from .formatters.base import get_formatter

            formatter = get_formatter()

            # Use display policy if available, otherwise create one that matches legacy settings
            if self.display is not None:
                display = self.display
            else:
                # Create a DisplayPolicy that matches the Policy's legacy formatting settings
                display = DisplayPolicy(
                    locale="en_US",  # Use a locale that doesn't add spaces in numbers
                    use_grouping=self.thousands_sep,
                    max_frac=self.decimal_places,
                    min_frac=self.decimal_places,
                    negative_parens=self.negative_parentheses,
                )
            return formatter.percent(ratio_for_formatter, display)
        else:
            # ratio mode
            return self.format_decimal(self.quantize(ratio_value), unit=Unit)


# Default policy instance
DEFAULT_POLICY = Policy()
