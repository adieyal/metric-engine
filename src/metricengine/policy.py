"""Policy configuration for Metric Engine calculations."""

from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Callable, Literal, Optional


def default_quantizer_factory(decimal_places: int) -> Decimal:
    """Exact, fast quantizer for given dp: e.g., dp=2 -> Decimal('0.01')."""
    return Decimal(1).scaleb(-decimal_places)


PercentDisplay = Literal["ratio", "percent"]

# Keep imports at module scope so tests can patch
from .units import Money, Unit


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
        Ensures parentheses wrap the whole string, e.g. "($1,234.56)".
        """
        is_negative = d < 0
        abs_d = -d if is_negative else d

        # Format base number
        base = (
            f"{abs_d:,.{self.decimal_places}f}"
            if self.thousands_sep
            else f"{abs_d:.{self.decimal_places}f}"
        )

        # Apply currency if applicable
        if unit is Money and self.currency_symbol:
            base = (
                f"{self.currency_symbol}{base}"
                if self.currency_position == "prefix"
                else f"{base}{self.currency_symbol}"
            )

        # Apply sign/parentheses last
        if is_negative:
            if self.negative_parentheses:
                return f"({base})"
            return f"-{base}"
        return base

    def format_percent(self, ratio_value: Decimal) -> str:
        """
        Render ratio (0..1) as percent text.
        Always clamp to cap_percentage_at if provided.
        """
        if self.percent_display == "percent":
            v = ratio_value * Decimal(100)
            if self.cap_percentage_at is not None:
                v = min(v, self.cap_percentage_at)
            return f"{self.quantize(v)}%"
        # ratio mode
        return self.format_decimal(self.quantize(ratio_value), unit=Unit)


# Default policy instance
DEFAULT_POLICY = Policy()
