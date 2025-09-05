"""FinancialValue wrapper for immutable financial data with policy-aware formatting.

This module provides the core FinancialValue class that wraps financial data with
immutable, policy-aware behavior. FinancialValue instances support safe arithmetic
operations, automatic formatting, and None propagation through calculations.

Key Features:
    - Immutable financial data wrapper with automatic Decimal conversion
    - Policy-aware formatting and rounding (decimal places, rounding mode)
    - Safe arithmetic operations (division by zero returns None)
    - None propagation through calculations
    - Percentage formatting and ratio conversion
    - Type-flexible input (int, float, str, Decimal, FinancialValue)
    - Hashable and comparable instances

Example:
    >>> from metricengine import FinancialValue as FV
    >>> price = FV(100.50)
    >>> quantity = FV(3)
    >>> total = price * quantity
    >>> print(total.as_str())  # "301.50"
    >>> print(total.as_decimal())  # Decimal('301.50')

    >>> # Safe operations
    >>> result = FV(100) / FV(0)  # Returns FV(None), not error
    >>> print(result.is_none())  # True

    >>> # Percentage handling
    >>> margin = FV(0.15).as_percentage()
    >>> print(margin.as_str())  # "15%"
    >>> print(margin.ratio())   # FV(0.15)

    >>> # Policy inheritance
    >>> custom_policy = Policy(decimal_places=4)
    >>> value = FV(123.4567, policy=custom_policy)
    >>> result = value + 50  # Inherits custom_policy
    >>> print(result.as_str())  # "173.4567"

See README.md for comprehensive usage examples and best practices.
"""
from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from decimal import Decimal as D
from enum import Enum, auto
from typing import Callable, Generic, Optional, TypeVar, overload

from .null_behaviour import NullBinaryMode, get_nulls
from .policy import DEFAULT_POLICY, Policy, default_quantizer_factory
from .policy_context import PolicyResolution, get_policy, get_resolution
from .units import Dimensionless, Money, Percent, Ratio, Unit
from .utils import SupportsDecimal, to_decimal

U = TypeVar("U", bound=Unit)

Binary = Callable[[Decimal, Decimal], Decimal]
UnitRule = Callable[[type[Unit], type[Unit]], Optional[type[Unit]]]

BinaryOp = Callable[[Decimal, Decimal], Decimal]

# ------------------------ Equality Mode Configuration --------------------------


class EqualityMode(Enum):
    VALUE_ONLY = auto()
    VALUE_AND_UNIT = auto()
    VALUE_UNIT_AND_POLICY = auto()


fv_equality_mode = ContextVar("fv_equality_mode", default=EqualityMode.VALUE_AND_UNIT)

# ------------------------ Policy resolution helpers --------------------------


def _mode() -> PolicyResolution:
    """
    Return a concrete PolicyResolution member, resilient to odd storage formats.
    """
    try:
        m = get_resolution()
        if isinstance(m, PolicyResolution):
            return m
        if isinstance(m, str):
            # e.g. "LEFT_OPERAND"
            return PolicyResolution[m]
        if isinstance(m, int):
            # auto() values are ints; map by value if needed
            for pr in PolicyResolution:
                if pr.value == m:
                    return pr
    except Exception:
        pass
    return PolicyResolution.CONTEXT


def _resolve_policy_for_op(a, b) -> Policy:
    """
    Decide policy for a binary op, honoring the current PolicyResolution.
    Also performs STRICT_MATCH validation.
    """
    mode = _mode()

    if mode is PolicyResolution.STRICT_MATCH:
        if (
            isinstance(a, FinancialValue)
            and isinstance(b, FinancialValue)
            and a.policy != b.policy
        ):
            raise ValueError("Mixed policies under STRICT_MATCH")
        # fall through to choose a policy after validation

    if mode is PolicyResolution.LEFT_OPERAND:
        return getattr(a, "policy", None) or getattr(b, "policy", None) or get_policy()

    # CONTEXT: prefer active context; if no context, use DEFAULT_POLICY; otherwise operands
    from .policy import DEFAULT_POLICY

    context_policy = get_policy()
    if context_policy is not None:
        return context_policy
    # No context set - fall back to default policy for CONTEXT mode
    return DEFAULT_POLICY


def _chosen_policy(left, right):
    mode = _mode()  # your enum-based helper
    if mode is PolicyResolution.LEFT_OPERAND:
        # If left is raw, fall back to right's policy
        return (
            (left.policy if isinstance(left, FinancialValue) else None)
            or (right.policy if isinstance(right, FinancialValue) else None)
            or get_policy()
        )
    # Use the same fallback logic as _resolve_policy_for_op
    from .policy import DEFAULT_POLICY

    context_policy = get_policy()
    if context_policy is not None:
        return context_policy
    # No context set - fall back to default policy for CONTEXT mode
    return DEFAULT_POLICY


# ------------------------ Unit helpers ---------------------------------------


def _is_money(u: type[Unit]) -> bool:
    return u is Money


def _is_ratioish(u: type[Unit]) -> bool:
    return u in (Ratio, Percent)


def _add_sub_result_unit(a: type[Unit], b: type[Unit]) -> type[Unit] | None:
    # Money +/- Money -> Money; cross with non-money invalid
    if _is_money(a) and _is_money(b):
        return Money
    if _is_money(a) != _is_money(b):
        return None
    # Non-money: if either ratioish -> Ratio; else dimensionless
    if _is_ratioish(a) or _is_ratioish(b):
        return Ratio
    return Dimensionless


def _mul_result_unit(a: type[Unit], b: type[Unit]) -> type[Unit] | None:
    if _is_money(a) and _is_money(b):
        return None
    if _is_money(a) or _is_money(b):
        return Money
    if _is_ratioish(a) or _is_ratioish(b):
        return Ratio
    return Dimensionless


def _div_result_unit(a: type[Unit], b: type[Unit]) -> type[Unit] | None:
    if _is_money(a) and _is_money(b):
        return Ratio
    if _is_money(a) and not _is_money(b):
        return Money
    if _is_ratioish(a) and _is_ratioish(b):
        return Ratio
    if _is_ratioish(a) and _is_money(b):
        return None
    if a is Dimensionless and _is_money(b):
        return None
    return a


# ----------------------------------------------------------------------------
# FinancialValue
# ----------------------------------------------------------------------------
@dataclass(frozen=True)
class FinancialValue(Generic[U]):
    _value: SupportsDecimal
    policy: Policy | None = None
    unit: type[Unit] = Dimensionless
    _is_percentage: bool = field(default=False, compare=False)

    # ------------------------------------------------------------------ init
    def __post_init__(self) -> None:
        if self.policy is None:
            object.__setattr__(self, "policy", DEFAULT_POLICY)
        v = self._value
        if v is None:
            return
        try:
            object.__setattr__(self, "_value", to_decimal(v))
        except (InvalidOperation, TypeError, ValueError):
            if self.policy and getattr(self.policy, "coerce_invalid_to_none", True):
                object.__setattr__(self, "_value", None)
            else:
                raise

    # ------------------------------------------------ internal helpers
    @staticmethod
    def _coerce(x: FinancialValue | SupportsDecimal | None) -> Decimal | None:
        """Return Decimal or None from FV or raw value (invalid → None)."""
        if x is None:
            return None
        if isinstance(x, FinancialValue):
            return x._value
        try:
            return to_decimal(x)
        except Exception:
            return None

    @staticmethod
    def _unit_of(
        other: FinancialValue | SupportsDecimal | None, fallback: type[Unit]
    ) -> type[Unit]:
        if isinstance(other, FinancialValue):
            return other.unit
        return fallback

    # ------------------------------------------------- basic representations
    def as_decimal(self) -> Decimal | None:
        # use the already-parsed value
        dec = self._value
        if dec is None:
            return None

        policy = self.policy
        rounding = policy.rounding if policy else ROUND_HALF_UP
        dp = policy.decimal_places if policy else 2
        quantizer = (
            policy.quantizer_factory(dp) if policy else default_quantizer_factory(2)
        )

        if self._is_percentage:
            percent_style = (
                getattr(policy, "percent_style", "percent") if policy else "percent"
            )
            if percent_style == "percent" or percent_style is None:
                # Display as percent (multiply by 100) - treat None as percent
                dec = dec * D("100")
                if policy and policy.cap_percentage_at is not None:
                    dec = min(dec, D(policy.cap_percentage_at))
            elif percent_style == "ratio":
                # Display as ratio (do not multiply)
                if policy and policy.cap_percentage_at is not None:
                    dec = min(dec, D(policy.cap_percentage_at))
            else:
                # Fallback to percent for any other value
                dec = dec * D("100")

        return dec.quantize(quantizer, rounding=rounding)

    def as_float(self) -> float | None:
        d = self.as_decimal()
        return float(d) if d is not None else None

    def as_int(self) -> int | None:
        d = self.as_decimal()
        return int(d) if d is not None else None

    def as_str(self) -> str:
        d = self.as_decimal()
        if d is None:
            return self.policy.none_text

        # Check if we should use the new formatter system
        if self.policy and self.policy.display:
            from .formatters.base import get_formatter

            fmt = get_formatter()
            display = self.policy.display

            # Determine formatting category
            if self.unit and getattr(self.unit, "__name__", "").startswith("Money"):
                return fmt.money(d, self.unit, display)
            elif self.unit is Percent or self._is_percentage:
                # For percentages, use the raw value since formatter will handle scaling
                raw_value = self._value
                if raw_value is None:
                    return self.policy.none_text
                return fmt.percent(raw_value, display)
            else:
                return fmt.number(d, display)

        # Legacy formatting (backward compatibility)
        if self.unit is Percent:
            # For Percent unit, check if we need to multiply by 100
            # If percent_style="percent", as_decimal() already did the conversion
            if self.policy and self.policy.percent_style == "percent":
                # Value is already in percent format (e.g., 15.30 for 15.30%)
                # Use policy's decimal places
                dp = self.policy.decimal_places
                q = self.policy.quantizer_factory(dp)
                disp = d.quantize(q, rounding=self.policy.rounding)
                return f"{disp}%"
            else:
                # Value is in ratio format (e.g., 0.153 for 15.3%), need to multiply by 100
                # Always use 2 decimal places for ratio-style percentage display
                dp = 2
                q = self.policy.quantizer_factory(dp)
                disp = (d * D("100")).quantize(q, rounding=self.policy.rounding)
                return f"{disp}%"
        # Money-specific override: currency outside parentheses for negatives
        if (
            self.unit is Money
            and d < 0
            and self.policy.currency_symbol
            and self.policy.negative_parentheses
        ):
            abs_d = -d
            if self.policy.thousands_sep:
                num = f"{abs_d:,.{self.policy.decimal_places}f}"
            else:
                num = f"{abs_d:.{self.policy.decimal_places}f}"
            if self.policy.currency_position == "prefix":
                return f"{self.policy.currency_symbol}({num})"
            else:
                return f"({num}){self.policy.currency_symbol}"
        # Use policy formatter for Money and other units
        return self.policy.format_decimal(d, self.unit)

    def is_percentage(self) -> bool:
        return self._is_percentage

    def render(self, fmt: str = "text", **context) -> str:
        """Render this FinancialValue using a registered renderer.
        
        Args:
            fmt: Name of the renderer to use (default: "text")
            **context: Additional context passed to the renderer
            
        Returns:
            Rendered string representation
            
        Raises:
            KeyError: If the specified renderer is not registered
            
        Example:
            >>> amount = money(1234.56)
            >>> amount.render("html")  # '<span class="fv positive">$1,234.56</span>'
            >>> amount.render("html", css_classes="highlight")
        """
        from .rendering import get_renderer
        
        renderer = get_renderer(fmt)
        return renderer.render(self, context=context)

    def __str__(self):
        # Delegate to as_str so Percent, Money and other units honor policy formatting
        return self.as_str()

    def __repr__(self) -> str:
        return (
            f"FinancialValue(value={self._value}, "
            f"policy={self.policy}, unit={self.unit.__name__}, "
            f"is_percentage={self._is_percentage})"
        )

    # ------------------------------------------------ arithmetic dunders

    @overload
    def __add__(self: FinancialValue[U], other: FinancialValue[U]) -> FinancialValue[U]:
        ...

    def __add__(self, other):
        return self._binary(other, lambda x, y: x + y, _add_sub_result_unit, self.unit)

    def __radd__(self, other):
        # raw + FV behaves like FV.__add__(raw) (raw adopts FV's unit for +/- in unit check)
        return self.__add__(other)

    @overload
    def __sub__(self: FinancialValue[U], other: FinancialValue[U]) -> FinancialValue[U]:
        ...

    def __sub__(self, other):
        return self._binary(other, lambda x, y: x - y, _add_sub_result_unit, self.unit)

    def __rsub__(self, other):  # other - self
        return FinancialValue(other, policy=self.policy, unit=self.unit)._binary(
            self, lambda x, y: x - y, _add_sub_result_unit, self.unit
        )

    @overload
    def __mul__(self, other: FinancialValue[Ratio]) -> FinancialValue[U]:
        ...

    def __mul__(self, other):
        return self._binary(other, lambda x, y: x * y, _mul_result_unit, Dimensionless)

    def __rmul__(self, other):
        return self.__mul__(other)

    @overload
    def __truediv__(self, other: FinancialValue[Ratio]) -> FinancialValue[U]:
        ...

    def __truediv__(self, other):
        def div(x, y):
            if y == 0:
                # Check null behavior mode
                nulls = get_nulls()
                if nulls.binary is NullBinaryMode.RAISE:
                    raise ZeroDivisionError("Division by zero")
                return None
            return x / y

        return self._binary(other, div, _div_result_unit, Dimensionless)

    def __rtruediv__(self, other):
        mode = _mode()
        b = self._coerce(self._value)
        a = self._coerce(other)
        if a is None or b in (None, D(0)):
            return FinancialValue.none(self.policy)

        other_unit = self._unit_of(other, Dimensionless)
        result_unit = _div_result_unit(other_unit, self.unit)
        if result_unit is None:
            return FinancialValue.none(self.policy)

        policy = (
            (other.policy if isinstance(other, FinancialValue) else self.policy)
            or get_policy()
            if mode is PolicyResolution.LEFT_OPERAND
            else _resolve_policy_for_op(other, self)
        )
        return FinancialValue(
            a / b, policy=policy, unit=result_unit, _is_percentage=False
        )

    def __pow__(self, other) -> FinancialValue:
        base = self._coerce(self._value)
        exp = self._coerce(other)
        if base is None or exp is None:
            return FinancialValue.none(self.policy)

        # Special case: 0^0 = 1
        if base == 0 and exp == 0:
            policy = _resolve_policy_for_op(self, other)
            return FinancialValue(
                D("1"),
                policy=policy,
                unit=self.unit,
                _is_percentage=self._is_percentage,
            )

        # unit guards
        base_unit = self.unit
        if base_unit not in (Dimensionless, Ratio, Percent):
            return FinancialValue.none(self.policy)

        # integer exponent path
        exp_int = exp.to_integral_value()
        is_int = exp == exp_int
        policy = _resolve_policy_for_op(self, other)
        if is_int:
            try:
                # For integer exponents, preserve the original unit and percentage flag
                return FinancialValue(
                    base ** int(exp_int),
                    policy=policy,
                    unit=self.unit,
                    _is_percentage=self._is_percentage,
                )
            except Exception:
                return FinancialValue.none(self.policy)

        # fractional exponents: support only safe cases (sqrt) to avoid float fallback
        if exp == D("0.5") and base >= 0:
            # Decimal has sqrt via context; emulate safely
            from decimal import getcontext

            return FinancialValue(
                getcontext().sqrt(base), policy=policy, unit=Dimensionless
            )

        return FinancialValue.none(self.policy)

    # ------------------------------------------------ comparisons & misc

    def _cmp_pair(self, other):
        a = self._coerce(self._value)
        b = self._coerce(other)
        if a is None or b is None:
            # Default behavior: None is less than any value
            return a, b  # keep None; comparisons below treat None<Decimal
        return a, b

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FinancialValue):
            return False
        mode = fv_equality_mode.get()
        if mode is EqualityMode.VALUE_ONLY:
            return self._value == other._value
        if mode is EqualityMode.VALUE_AND_UNIT:
            return (self.unit is other.unit) and (self._value == other._value)
        # VALUE_UNIT_AND_POLICY
        return (
            (self.unit is other.unit)
            and (self.policy == other.policy)
            and (self._value == other._value)
        )

    def __lt__(self, other):
        a, b = self._cmp_pair(other)
        if a is None:
            return b is not None
        if b is None:
            return False
        return a < b

    def __le__(self, other):
        a, b = self._cmp_pair(other)
        if a is None:
            return True
        if b is None:
            return False
        return a <= b

    def __gt__(self, other):
        a, b = self._cmp_pair(other)
        if b is None:
            return a is not None
        if a is None:
            return False
        return a > b

    def __ge__(self, other):
        a, b = self._cmp_pair(other)
        if b is None:
            return True
        if a is None:
            return False
        return a >= b

    def __neg__(self):
        a = self._coerce(self._value)
        if a is None:
            return FinancialValue.none(self.policy)
        return FinancialValue(
            -a, policy=self.policy, unit=self.unit, _is_percentage=self._is_percentage
        )

    def __hash__(self) -> int:
        mode = fv_equality_mode.get()
        if mode is EqualityMode.VALUE_ONLY:
            return hash((self._value,))
        if mode is EqualityMode.VALUE_AND_UNIT:
            return hash((self._value, self.unit))
        return hash((self._value, self.unit, self.policy))

    def __bool__(self) -> bool:
        return self._value not in (None, D(0))

    def __abs__(self):
        a = self._coerce(self._value)
        if a is None:
            return FinancialValue.none(self.policy)
        return FinancialValue(
            abs(a),
            policy=self.policy,
            unit=self.unit,
            _is_percentage=self._is_percentage,
        )

    # ------------------------------------------------ helpers

    def is_none(self) -> bool:
        return self._value is None

    def as_percentage(self) -> FinancialValue[Percent]:
        return FinancialValue(
            self._value, policy=self.policy, unit=Percent, _is_percentage=True
        )

    def ratio(self) -> FinancialValue[Ratio]:
        # Create a new policy with percent_style="ratio" for ratio display
        if self.policy:
            from dataclasses import replace

            new_policy = replace(self.policy, percent_style="ratio")
        else:
            new_policy = None
        return FinancialValue(
            self._value, policy=new_policy, unit=Ratio, _is_percentage=False
        )

    def with_policy(self, policy: Policy) -> FinancialValue:
        return FinancialValue(
            self._value,
            policy=policy,
            unit=self.unit,
            _is_percentage=self._is_percentage,
        )

    @classmethod
    def zero(cls, policy: Policy | None = None, unit: type[Unit] = Dimensionless):
        return cls(0, policy=policy, unit=unit)

    @classmethod
    def none(cls, policy: Policy | None = None) -> FinancialValue:
        return cls(None, policy=policy)

    @classmethod
    def none_with_unit(
        cls, unit: type[Unit], policy: Policy | None = None
    ) -> FinancialValue:
        return cls(None, policy=policy, unit=unit)

    @classmethod
    def constant(
        cls,
        value: SupportsDecimal,
        policy: Policy | None = None,
        unit: type[Unit] = Dimensionless,
    ):
        return cls(value, policy=policy, unit=unit)

    @classmethod
    def _is_noneish(cls, x) -> bool:
        return (x is None) or (isinstance(x, FinancialValue) and x.is_none())

    def _binary(
        self, other, op: Binary, unit_rule: UnitRule, raw_default_unit: type[Unit]
    ) -> FinancialValue:
        a = self._coerce(self._value)
        b = self._coerce(other)
        if a is None or b is None:
            # Check null behavior mode
            nulls = get_nulls()
            if nulls.binary is NullBinaryMode.RAISE:
                from .exceptions import CalculationError

                raise CalculationError("Binary operation encountered None")
            return _invalid_op("None operand")
        left_u, right_u = (
            self.unit,
            (other.unit if isinstance(other, FinancialValue) else raw_default_unit),
        )
        result_u = unit_rule(left_u, right_u)
        if result_u is None:
            return _invalid_op("incompatible units")
        policy = _resolve_policy_for_op(self, other)

        # Preserve percentage flag if both operands are percentages
        preserve_percentage = (
            self._is_percentage
            and isinstance(other, FinancialValue)
            and other._is_percentage
        )

        try:
            return FinancialValue(
                op(a, b),
                policy=policy,
                unit=result_u,
                _is_percentage=preserve_percentage,
            )
        except Exception as e:
            # Check if it's a ZeroDivisionError and we're in RAISE mode
            nulls = get_nulls()
            if (
                isinstance(e, ZeroDivisionError)
                and nulls.binary is NullBinaryMode.RAISE
            ):
                raise
            return _invalid_op("arithmetic failure")


# Alias
FV = FinancialValue

# ------------------------ Helper functions --------------------------


def _invalid_op(reason: str) -> FinancialValue:
    """Return a None FinancialValue for invalid operations."""
    return FinancialValue.none()
