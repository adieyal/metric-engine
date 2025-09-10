from decimal import Decimal as D, InvalidOperation
from unittest.mock import patch

import pytest

import metricengine.value as value_mod
from metricengine.exceptions import CalculationError
from metricengine.null_behaviour import (
    NullBinaryMode,
    NullReductionMode,
    with_binary,
    with_reduction,
)
from metricengine.policy import DEFAULT_POLICY, Policy
from metricengine.policy_context import (
    PolicyResolution,
    use_policy,
    use_policy_resolution,
)
from metricengine.units import Dimensionless, Money, Percent, Ratio
from metricengine.value import FinancialValue as FV

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def fv_money(x, policy=None):
    return FV(x, policy=policy, unit=Money)


def fv_ratio(x, policy=None):
    return FV(x, policy=policy, unit=Ratio)


def fv_percent_from_ratio(x, policy=None):
    # store numeric as ratio, but display as percent
    return FV(x, policy=policy, unit=Percent, _is_percentage=True)


def fv_dimless(x, policy=None):
    return FV(x, policy=policy, unit=Dimensionless)


# ---------------------------------------------------------------------------
# Construction & basic representations
# ---------------------------------------------------------------------------


def test_construct_and_basic_repr_defaults():
    v = FV(123.456)
    assert v.unit is Dimensionless
    assert v.policy is not None
    # Default policy is 2 dp; quantizes/rounds via as_decimal
    assert v.as_decimal() == D("123.46")
    assert str(v) == "123.46"
    assert not v.is_percentage()


def test_none_handling():
    v = FV(None)
    assert v.is_none()
    assert v.as_decimal() is None
    # Fix linter error by asserting policy is not None
    assert v.policy is not None
    assert str(v) == v.policy.none_text


def test_with_policy_overrides_quantization():
    p = Policy(decimal_places=4)
    v = FV("1.23456", policy=p)
    assert v.as_decimal() == D("1.2346")
    assert str(v) == "1.2346"


def test_with_policy_method_creates_new_instance():
    p1 = Policy(decimal_places=2)
    p2 = Policy(decimal_places=4)
    v1 = FV("1.234", policy=p1)
    v2 = v1.with_policy(p2)
    # Fix linter errors by asserting policies are not None
    assert v1.policy is not None
    assert v2.policy is not None
    assert v1.policy.decimal_places == 2
    assert v2.policy.decimal_places == 4
    assert v1.as_decimal() == D("1.23")
    assert v2.as_decimal() == D("1.2340")


# ---------------------------------------------------------------------------
# Percent-as-display-only semantics
# ---------------------------------------------------------------------------


def test_percentage_display_percent_style_ratio():
    # Internally a ratio 0.153; with percent_style="ratio", as_decimal() returns ratio
    p = Policy(decimal_places=2, percent_style="ratio")
    m = fv_percent_from_ratio(D("0.153"), policy=p)
    # as_decimal (ratio mode) → 0.15
    assert m.as_decimal() == D("0.15")
    # display multiplies by 100 for string form in ratio mode
    assert str(m) == "15.00%"


def test_percentage_display_percent_style_percent():
    # With percent_style="percent", as_decimal() returns 15.30 (percent units)
    p = Policy(decimal_places=2, percent_style="percent")
    m = fv_percent_from_ratio(D("0.153"), policy=p)
    assert m.as_decimal() == D("15.30")
    assert str(m) == "15.30%"


def test_ratio_method_clears_percentage_flag():
    p = Policy(decimal_places=3, percent_style="ratio")
    m = fv_percent_from_ratio(D("0.2718"), policy=p)
    r = m.ratio()
    assert not r.is_percentage()
    assert r.unit is Ratio
    # as_decimal returns ratio, quantized to 3 dp
    assert r.as_decimal() == D("0.272")
    # string is plain number (no %)
    assert str(r) == "0.272"


def test_as_percentage_sets_display_flag_without_scaling():
    p = Policy(decimal_places=4, percent_style="ratio")
    r = fv_ratio(D("0.5"), policy=p)
    m = r.as_percentage()
    assert m.is_percentage()
    assert m.unit is Percent
    # no numeric scaling: still 0.5 under the hood, as_decimal returns ratio since style="ratio"
    assert m.as_decimal() == D("0.5000")
    assert str(m) == "50.00%"


def test_percentage_cap_applied_to_display_in_percent_mode():
    # cap at 120% in percent mode
    p = Policy(decimal_places=1, percent_style="percent", cap_percentage_at=D("120"))
    # underlying ratio 2.5 -> 250%, but capped to 120.0%
    m = fv_percent_from_ratio(D("2.5"), policy=p)
    assert m.as_decimal() == D("120.0")
    assert str(m) == "120.0%"


# ---------------------------------------------------------------------------
# Arithmetic: units & propagation
# ---------------------------------------------------------------------------


def test_addition_money_money_keeps_money_unit():
    a = fv_money(10)
    b = fv_money("2.345")
    c = a + b
    assert not c.is_none()
    assert c.unit is Money
    assert c.as_decimal() == D("12.35")  # default 2 dp rounding


def test_addition_money_ratio_is_invalid_propagates_none():
    a = fv_money(10)
    b = fv_ratio(D("0.1"))
    c = a + b
    assert c.is_none()


def test_addition_ratio_ratio_unit_and_percentage_flag():
    r1 = fv_percent_from_ratio(D("0.10"))  # percentage flag on
    r2 = fv_percent_from_ratio(D("0.05"))  # both flagged → result flagged
    s = r1 + r2
    assert not s.is_none()
    assert s.unit is Ratio
    assert s.is_percentage()

    # If only one operand flagged → result not flagged (by current semantics)
    r3 = fv_ratio(D("0.02"))
    s2 = r1 + r3
    assert not s2.is_percentage()


def test_subtraction_money_money_keeps_money_unit():
    a = fv_money(20)
    b = fv_money(5)
    c = a - b
    assert not c.is_none()
    assert c.unit is Money
    assert c.as_decimal() == D("15.00")


def test_subtraction_money_ratio_invalid():
    a = fv_money(20)
    b = fv_ratio(D("0.1"))
    c = a - b
    assert c.is_none()


def test_multiplication_money_ratio_money():
    a = fv_money("100.00")
    r = fv_ratio("0.157")
    p = a * r
    assert not p.is_none()
    assert p.unit is Money
    # default 2 dp rounding on 100 * 0.157 = 15.7 → 15.70
    assert p.as_decimal() == D("15.70")


def test_multiplication_ratio_money_money_reverse_order():
    r = fv_ratio("0.2")
    a = fv_money(50)
    p = r * a
    assert not p.is_none()
    assert p.unit is Money
    assert p.as_decimal() == D("10.00")


def test_multiplication_money_money_invalid():
    a = fv_money(2)
    b = fv_money(3)
    c = a * b
    assert c.is_none()


def test_division_money_money_ratio():
    a = fv_money(50)
    b = fv_money(200)
    r = a / b
    assert not r.is_none()
    assert r.unit is Ratio
    # 50/200 = 0.25 → 0.25 (2 dp)
    assert r.as_decimal() == D("0.25")


def test_division_money_ratio_money():
    m = fv_money(50)
    r = fv_ratio("0.5")
    out = m / r
    assert not out.is_none()
    assert out.unit is Money
    assert out.as_decimal() == D("100.00")


def test_division_by_zero_propagates_none():
    a = fv_money(50)
    z = fv_dimless(0)
    r = a / z
    assert r.is_none()
    # Fix linter error by using FV(0) instead of raw 0
    r2 = a / FV(0)
    assert r2.is_none()


def test_right_hand_numeric_operations():
    v = fv_money(10)
    s = 5 + v
    assert s.unit is Money and s.as_decimal() == D("15.00")
    d = 20 - v
    assert d.unit is Money and d.as_decimal() == D("10.00")
    p = 2 * v
    assert p.unit is Money and p.as_decimal() == D("20.00")
    q = 100 / v  # invalid per unit rules (dimless/money) -> None
    assert q.is_none()


def test_pow_integer_exponent_preserves_unit():
    v = fv_ratio(D("0.5"))
    out = v**2
    assert out.unit is Ratio
    assert out.as_decimal() == D("0.25")


def test_pow_fractional_negative_base_returns_none():
    v = fv_dimless(-2)
    out = v ** D("0.5")
    assert out.is_none()


def test_pow_zero_zero_is_one():
    v = fv_dimless(0)
    out = v**0
    assert out.as_decimal() == D("1.00")


# ---------------------------------------------------------------------------
# Policy resolution modes
# ---------------------------------------------------------------------------


def test_policy_resolution_context_wins_over_operands():
    a = fv_dimless("1.2345", policy=Policy(decimal_places=1))
    b = fv_dimless("2.2222", policy=Policy(decimal_places=3))
    with use_policy(Policy(decimal_places=4)):
        with use_policy_resolution(PolicyResolution.CONTEXT):
            c = a + b
            # context policy (4 dp) should drive quantization
            assert c.as_decimal() == D("3.4567")


def test_policy_resolution_left_operand():
    a = fv_dimless("1.2345", policy=Policy(decimal_places=1))
    b = fv_dimless("2.2222", policy=Policy(decimal_places=3))
    with use_policy_resolution(PolicyResolution.LEFT_OPERAND):
        c = a + b
        # left operand decimal_places=1 → sum 3.4567 → "3.5"
        assert c.as_decimal() == D("3.5")


def test_policy_resolution_strict_match_raises_on_mixed_policies():
    a = fv_dimless("1.23", policy=Policy(decimal_places=1))
    b = fv_dimless("2.22", policy=Policy(decimal_places=2))
    with use_policy_resolution(PolicyResolution.STRICT_MATCH):
        with pytest.raises(ValueError):
            _ = a + b


# ---------------------------------------------------------------------------
# Comparisons, hashing, truthiness, abs, neg
# ---------------------------------------------------------------------------


def test_equality_and_hash():
    x1 = fv_money(10)
    x2 = fv_money(D("10"))
    x3 = fv_money(11)
    assert x1 == x2
    assert x1 != x3
    assert hash(x1) == hash(x2)


def test_ordering_with_none_semantics():
    assert FV(None) < FV(1)  # None < value
    assert not (FV(1) < FV(None))
    assert FV(None) <= FV(None)


def test_bool_neg_abs():
    assert not FV(0)
    assert not FV(None)
    assert FV(5)
    v = FV(-3)
    assert abs(v).as_decimal() == D("3.00")
    assert (-v).as_decimal() == D("3.00")


# ---------------------------------------------------------------------------
# Mixed raw numerics
# ---------------------------------------------------------------------------


def test_mixing_raw_numerics_adopts_left_unit():
    m = fv_money(10)
    # Money + Dimensionless is invalid per unit rules
    out = m + FV(5)
    assert out.is_none()

    r = fv_ratio(D("0.3"))
    # Ratio * Dimensionless = Ratio (per unit rules)
    out2 = r * FV(2)
    assert out2.unit is Ratio and out2.as_decimal() == D("0.60")


def test_invalid_types_coerce_to_none():
    class Weird:
        pass

    v = FV(10)
    out = v + Weird()  # coerce fails → None propagation
    assert out.is_none()


# ---------------------------------------------------------------------------
# Null Behavior Testing
# ---------------------------------------------------------------------------


def test_null_binary_mode_propagate():
    """Test PROPAGATE mode for binary operations with None."""
    v1 = fv_money(100)
    v2 = FV.none()

    with with_binary(NullBinaryMode.PROPAGATE):
        result = v1 + v2
        assert result.is_none()


def test_null_binary_mode_raise():
    """Test RAISE mode for binary operations with None."""
    v1 = fv_money(100)
    v2 = FV.none()

    with with_binary(NullBinaryMode.RAISE):
        with pytest.raises(CalculationError):
            _ = v1 + v2


def test_null_reduction_mode_skip():
    """Test SKIP mode for reduction operations."""
    from metricengine.reductions import fv_sum

    values = [fv_money(100), FV.none(), fv_money(200)]

    with with_reduction(NullReductionMode.SKIP):
        result = fv_sum(values)
        assert result.as_decimal() == D("300.00")


def test_null_reduction_mode_propagate():
    """Test PROPAGATE mode for reduction operations."""
    from metricengine.reductions import fv_sum

    values = [fv_money(100), FV.none(), fv_money(200)]

    with with_reduction(NullReductionMode.PROPAGATE):
        result = fv_sum(values)
        assert result.is_none()


def test_null_reduction_mode_zero():
    """Test ZERO mode for reduction operations."""
    from metricengine.reductions import fv_sum

    values = [fv_money(100), FV.none(), fv_money(200)]

    with with_reduction(NullReductionMode.ZERO):
        result = fv_sum(values)
        assert result.as_decimal() == D("300.00")


def test_null_reduction_mode_raise():
    """Test RAISE mode for reduction operations."""
    from metricengine.reductions import fv_sum

    values = [fv_money(100), FV.none(), fv_money(200)]

    with with_reduction(NullReductionMode.RAISE):
        with pytest.raises(CalculationError):
            _ = fv_sum(values)


# ---------------------------------------------------------------------------
# Additional Coverage Tests for value.py
# ---------------------------------------------------------------------------


def test_mode_with_string_input():
    """Test _mode() with string input (line 85-87)"""
    with patch("metricengine.value.get_resolution", return_value="LEFT_OPERAND"):
        result = value_mod._mode()
        assert result is PolicyResolution.LEFT_OPERAND


def test_mode_with_int_input():
    """Test _mode() with int input (line 88-92)"""
    with patch(
        "metricengine.value.get_resolution",
        return_value=PolicyResolution.CONTEXT.value,
    ):
        result = value_mod._mode()
        assert result is PolicyResolution.CONTEXT


def test_mode_with_exception_fallback():
    """Test _mode() exception fallback (line 93-95)"""
    with patch("metricengine.value.get_resolution", side_effect=RuntimeError("test")):
        result = value_mod._mode()
        assert result is PolicyResolution.CONTEXT


def test_chosen_policy_context_fallback_to_default():
    """Test _chosen_policy() CONTEXT mode fallback to DEFAULT_POLICY (line 139-143)"""
    with patch("metricengine.value.get_policy", return_value=None):
        with patch(
            "metricengine.value.get_resolution",
            return_value=PolicyResolution.CONTEXT,
        ):
            left = 5
            right = FV(1, policy=Policy(decimal_places=4))
            result = value_mod._chosen_policy(left, right)
            assert result is DEFAULT_POLICY


def test_percentage_cap_ratio_style():
    """Test percentage capping in ratio style (line 264-265)"""
    p = Policy(decimal_places=2, percent_style="ratio", cap_percentage_at=D("1.2"))
    v = fv_percent_from_ratio(D("2.5"), policy=p)
    # In ratio style, cap should be applied to the ratio value (2.5 -> 1.2)
    assert v.as_decimal() == D("1.20")


def test_percentage_cap_fallback_style():
    """Test percentage fallback style (line 266-268)"""
    p = Policy(decimal_places=2, percent_style="unknown", cap_percentage_at=D("120"))
    v = fv_percent_from_ratio(D("0.5"), policy=p)
    # Fallback to percent style (multiply by 100)
    assert v.as_decimal() == D("50.00")


def test_as_float_with_none():
    """Test as_float() with None value (line 273-274)"""
    v = FV(None)
    assert v.as_float() is None


def test_as_int_with_none():
    """Test as_int() with None value (line 277-278)"""
    v = FV(None)
    assert v.as_int() is None


def test_money_negative_parentheses_no_thousands_sep():
    """Test money negative parentheses without thousands separator (line 312)"""
    p = Policy(
        decimal_places=2,
        currency_symbol="$",
        negative_parentheses=True,
        thousands_sep=False,
    )
    v = fv_money(-123.45, policy=p)
    assert v.as_str() == "$(123.45)"


def test_money_negative_parentheses_currency_suffix():
    """Test money negative parentheses with currency suffix (line 316)"""
    p = Policy(
        decimal_places=2,
        currency_symbol="$",
        currency_position="suffix",
        negative_parentheses=True,
    )
    v = fv_money(-123.45, policy=p)
    assert v.as_str() == "(123.45)$"


def test_repr_includes_all_fields():
    """Test __repr__ includes all non-default fields (line 328)"""
    # Use a policy that differs from DEFAULT_POLICY to ensure it's included
    p = Policy(decimal_places=4)  # Different from default (2)
    v = FV(10, policy=p, unit=Money, _is_percentage=True)
    s = repr(v)
    assert "FinancialValue" in s
    assert "policy=" in s
    assert "unit=Money" in s
    assert "is_percentage=True" in s


def test_rtruediv_with_none_operand():
    """Test right division with None operand (line 390)"""
    result = 5 / FV(None)
    assert result.is_none()


def test_rtruediv_with_zero_operand():
    """Test right division with zero operand (line 390)"""
    result = 5 / FV(0)
    assert result.is_none()


def test_rtruediv_policy_selection_left_operand_mode():
    """Test right division policy selection in LEFT_OPERAND mode (line 397-402)"""
    p_right = Policy(decimal_places=3)
    with use_policy_resolution(PolicyResolution.LEFT_OPERAND):
        result = 10 / fv_dimless(2, policy=p_right)
        assert result.policy == p_right
        assert result.unit is Dimensionless
        assert result.as_decimal() == D("5.000")


def test_rtruediv_policy_selection_context_mode():
    """Test right division policy selection in CONTEXT mode (line 401-402)"""
    ctx_policy = Policy(decimal_places=4)
    with use_policy(ctx_policy), use_policy_resolution(PolicyResolution.CONTEXT):
        result = 10 / fv_dimless(4, policy=Policy(decimal_places=1))
        assert result.policy == ctx_policy
        assert result.as_decimal() == D("2.5000")


def test_pow_with_none_operand():
    """Test power with None operand (line 411)"""
    result = FV(None) ** 2
    assert result.is_none()


def test_pow_with_money_unit_rejected():
    """Test power with money unit rejected (line 426)"""
    result = fv_money(2) ** 3
    assert result.is_none()


def test_pow_integer_exponent_exception():
    """Test power integer exponent with exception (line 441-442)"""

    # Create a scenario where the power operation raises an exception
    # We can't patch Decimal.__pow__ directly, so let's create a custom Decimal-like object
    class FailingDecimal:
        def __init__(self, value):
            self.value = value

        def __pow__(self, other):
            raise Exception("test")

        def to_integral_value(self):
            return self.value

    # Create a FinancialValue that will trigger the exception path
    with patch("metricengine.value.to_decimal", return_value=FailingDecimal(2)):
        result = fv_dimless(2) ** 3
        assert result.is_none()


def test_pow_sqrt_positive_base():
    """Test power sqrt with positive base (line 447-449)"""
    result = fv_dimless(4) ** D("0.5")
    assert result.unit is Dimensionless
    assert result.as_decimal() == D("2.00")


def test_le_with_none_operand():
    """Test __le__ with None operand (line 492-494)"""
    # Test the actual behavior - the comparison should return boolean values
    none_fv = FV(None)
    one_fv = FV(1)

    # Test that the comparison returns boolean values
    result1 = none_fv <= one_fv
    result2 = one_fv <= none_fv

    # Based on __le__ logic: if a is None, return True; if b is None, return False
    assert result1 is True  # a is None -> True
    assert result2 is False  # b is None -> False


def test_gt_with_none_operand():
    """Test __gt__ with None operand (line 499, 501)"""
    # Test the actual behavior - the comparison should return boolean values
    none_fv = FV(None)
    one_fv = FV(1)

    # Test that the comparison returns boolean values
    result1 = one_fv > none_fv
    result2 = none_fv > one_fv

    # Based on __gt__ logic: if b is None, return a is not None; if a is None, return False
    assert result1 is True  # b is None, a is not None -> True
    assert result2 is False  # a is None -> False


def test_ge_with_none_operand():
    """Test __ge__ with None operand (line 505-510)"""
    # Test the actual behavior - the comparison should return boolean values
    none_fv = FV(None)
    one_fv = FV(1)

    # Test that the comparison returns boolean values
    result1 = one_fv >= none_fv
    result2 = none_fv >= one_fv

    # Based on __ge__ logic: if b is None, return True; if a is None, return False
    assert result1 is True  # b is None -> True
    assert result2 is False  # a is None -> False


def test_neg_with_none():
    """Test __neg__ with None value (line 515)"""
    result = -FV(None)
    assert result.is_none()


def test_abs_with_none():
    """Test __abs__ with None value (line 534)"""
    result = abs(FV(None))
    assert result.is_none()


def test_none_with_unit():
    """Test none_with_unit class method (line 584)"""
    result = FV.none_with_unit(Money)
    assert result.unit is Money
    assert result.is_none()


def test_constant_class_method():
    """Test constant class method (line 593)"""
    result = FV.constant("1.23", unit=Money)
    assert result.unit is Money
    assert result.as_decimal() == D("1.23")


def test_is_noneish_class_method():
    """Test _is_noneish class method (line 597)"""
    assert FV._is_noneish(None) is True
    assert FV._is_noneish(FV.none()) is True
    assert FV._is_noneish(FV(0)) is False


def test_binary_operation_exception_handling():
    """Test _binary operation exception handling (line 643)"""
    v = FV(1)
    with with_binary(NullBinaryMode.PROPAGATE):
        # This should trigger the exception handling path
        result = v + "invalid"
        assert result.is_none()


def test_div_result_unit_ratio_ratio():
    """Test _div_result_unit with ratio/ratio (line 185)"""
    result = value_mod._div_result_unit(Ratio, Ratio)
    assert result is Ratio


def test_coerce_with_exception():
    """Test _coerce with exception (line 228-229)"""
    # This should trigger the exception path in _coerce
    result = FV._coerce("invalid_decimal")
    assert result is None


def test_unit_of_with_financial_value():
    """Test _unit_of with FinancialValue (line 236)"""
    fv = fv_money(100)
    result = FV._unit_of(fv, Dimensionless)
    assert result is Money


def test_post_init_invalid_conversion_with_coerce_false():
    """Test __post_init__ with invalid conversion and coerce_invalid_to_none=False (line 213-216)"""

    # Create a policy that doesn't coerce invalid values to None
    class StrictPolicy(Policy):
        def __init__(self):
            super().__init__()
            # Set the attribute directly since it doesn't exist by default
            object.__setattr__(self, "coerce_invalid_to_none", False)

    # Patch to_decimal to raise an exception
    with patch("metricengine.value.to_decimal", side_effect=ValueError("test")):
        with pytest.raises(ValueError):
            FV("some_value", policy=StrictPolicy())


# ---------------------------------------------------------------------------
# Repr Optimization Tests (Task 3) - Default Value Cases
# ---------------------------------------------------------------------------


def test_repr_all_default_values_shows_only_value():
    """Test FinancialValue with all default values shows only value parameter."""
    # Create FV with all default values: DEFAULT_POLICY, Dimensionless unit, _is_percentage=False
    fv = FV(100)
    result = repr(fv)
    expected = "FinancialValue(value=100)"
    assert result == expected


def test_repr_financial_value_100_shows_only_value():
    """Test FinancialValue(100) expecting 'FinancialValue(value=100)'."""
    fv = FV(100)
    result = repr(fv)
    expected = "FinancialValue(value=100)"
    assert result == expected


def test_repr_financial_value_none_with_default_values():
    """Test FinancialValue(None) with default values shows only value=None."""
    fv = FV(None)
    result = repr(fv)
    expected = "FinancialValue(value=None)"
    assert result == expected


def test_repr_decimal_values_with_default_parameters():
    """Test FinancialValue with Decimal values and default parameters."""
    # Test with Decimal input
    fv_decimal = FV(D("123.456"))
    result = repr(fv_decimal)
    expected = "FinancialValue(value=123.456)"
    assert result == expected

    # Test with string that converts to Decimal
    fv_string = FV("99.99")
    result = repr(fv_string)
    expected = "FinancialValue(value=99.99)"
    assert result == expected

    # Test with float that converts to Decimal
    fv_float = FV(42.5)
    result = repr(fv_float)
    expected = "FinancialValue(value=42.5)"
    assert result == expected

    # Test with integer
    fv_int = FV(0)
    result = repr(fv_int)
    expected = "FinancialValue(value=0)"
    assert result == expected


def test_repr_negative_values_with_defaults():
    """Test repr with negative values and default parameters."""
    fv = FV(-50.25)
    result = repr(fv)
    expected = "FinancialValue(value=-50.25)"
    assert result == expected


def test_repr_zero_with_defaults():
    """Test repr with zero value and default parameters."""
    fv = FV(0)
    result = repr(fv)
    expected = "FinancialValue(value=0)"
    assert result == expected


def test_repr_large_decimal_with_defaults():
    """Test repr with large decimal values and default parameters."""
    fv = FV(D("999999.123456789"))
    result = repr(fv)
    expected = "FinancialValue(value=999999.123456789)"
    assert result == expected


def test_repr_small_decimal_with_defaults():
    """Test repr with small decimal values and default parameters."""
    fv = FV(D("0.000001"))
    result = repr(fv)
    expected = "FinancialValue(value=0.000001)"
    assert result == expected


# ---------------------------------------------------------------------------
# Repr Optimization Tests (Task 4) - Single Non-Default Parameter Cases
# ---------------------------------------------------------------------------


def test_repr_custom_policy_only():
    """Test FinancialValue with custom policy only shows value and policy."""
    # Create a custom policy that differs from DEFAULT_POLICY
    custom_policy = Policy(decimal_places=4)
    fv = FV(100, policy=custom_policy)
    result = repr(fv)
    expected = f"FinancialValue(value=100, policy={custom_policy})"
    assert result == expected


def test_repr_non_dimensionless_unit_money():
    """Test FinancialValue with Money unit only shows value and unit."""
    fv = FV(100, unit=Money)
    result = repr(fv)
    expected = "FinancialValue(value=100, unit=Money)"
    assert result == expected


def test_repr_non_dimensionless_unit_ratio():
    """Test FinancialValue with Ratio unit only shows value and unit."""
    fv = FV(0.5, unit=Ratio)
    result = repr(fv)
    expected = "FinancialValue(value=0.5, unit=Ratio)"
    assert result == expected


def test_repr_non_dimensionless_unit_percent():
    """Test FinancialValue with Percent unit only shows value and unit."""
    fv = FV(0.15, unit=Percent)
    result = repr(fv)
    expected = "FinancialValue(value=0.15, unit=Percent)"
    assert result == expected


def test_repr_is_percentage_true_only():
    """Test FinancialValue with _is_percentage=True only shows value and is_percentage."""
    fv = FV(0.15, _is_percentage=True)
    result = repr(fv)
    expected = "FinancialValue(value=0.15, is_percentage=True)"
    assert result == expected


def test_repr_new_unit_system_money_unit():
    """Test FinancialValue with NewUnit MoneyUnit shows value and unit."""
    from metricengine.units import MoneyUnit

    usd = MoneyUnit("USD")
    fv = FV(100.5, unit=usd)
    result = repr(fv)
    expected = "FinancialValue(value=100.5, unit=Money[USD])"
    assert result == expected


def test_repr_new_unit_system_quantity_unit():
    """Test FinancialValue with NewUnit Qty shows value and unit."""
    from metricengine.units import Qty

    kg = Qty("kg")
    fv = FV(25.5, unit=kg)
    result = repr(fv)
    expected = "FinancialValue(value=25.5, unit=Quantity[kg])"
    assert result == expected


def test_repr_new_unit_system_percent_unit():
    """Test FinancialValue with NewUnit Pct shows value and unit."""
    from metricengine.units import Pct

    ratio = Pct()
    fv = FV(0.15, unit=ratio)
    result = repr(fv)
    expected = "FinancialValue(value=0.15, unit=Percent[ratio])"
    assert result == expected


def test_repr_new_unit_system_custom_percent_unit():
    """Test FinancialValue with NewUnit custom Pct shows value and unit."""
    from metricengine.units import Pct

    bp = Pct("bp")  # basis points
    fv = FV(150, unit=bp)
    result = repr(fv)
    expected = "FinancialValue(value=150, unit=Percent[bp])"
    assert result == expected


def test_repr_new_unit_system_generic_new_unit():
    """Test FinancialValue with generic NewUnit shows value and unit."""
    from metricengine.units import NewUnit

    custom_unit = NewUnit("Custom", "test")
    fv = FV(42, unit=custom_unit)
    result = repr(fv)
    expected = "FinancialValue(value=42, unit=Custom[test])"
    assert result == expected


def test_repr_none_unit_in_new_system():
    """Test FinancialValue with None unit shows value and unit=None."""
    fv = FV(50, unit=None)
    result = repr(fv)
    expected = "FinancialValue(value=50, unit=None)"
    assert result == expected


def test_repr_custom_policy_different_decimal_places():
    """Test FinancialValue with custom policy having different decimal places."""
    custom_policy = Policy(decimal_places=6)
    fv = FV(D("123.456789"), policy=custom_policy)
    result = repr(fv)
    expected = f"FinancialValue(value=123.456789, policy={custom_policy})"
    assert result == expected


def test_repr_custom_policy_different_rounding():
    """Test FinancialValue with custom policy having different rounding."""
    from decimal import ROUND_DOWN

    custom_policy = Policy(rounding=ROUND_DOWN)
    fv = FV(100, policy=custom_policy)
    result = repr(fv)
    expected = f"FinancialValue(value=100, policy={custom_policy})"
    assert result == expected


def test_repr_custom_policy_different_none_text():
    """Test FinancialValue with custom policy having different none_text."""
    custom_policy = Policy(none_text="N/A")
    fv = FV(100, policy=custom_policy)
    result = repr(fv)
    expected = f"FinancialValue(value=100, policy={custom_policy})"
    assert result == expected


def test_repr_legacy_currency_units():
    """Test FinancialValue with legacy currency units shows proper unit names."""
    from metricengine.units import EUR, GBP, USD

    # Test USD
    fv_usd = FV(100, unit=USD)
    result = repr(fv_usd)
    expected = "FinancialValue(value=100, unit=Money_USD)"
    assert result == expected

    # Test EUR
    fv_eur = FV(200, unit=EUR)
    result = repr(fv_eur)
    expected = "FinancialValue(value=200, unit=Money_EUR)"
    assert result == expected

    # Test GBP
    fv_gbp = FV(300, unit=GBP)
    result = repr(fv_gbp)
    expected = "FinancialValue(value=300, unit=Money_GBP)"
    assert result == expected


# ---------------------------------------------------------------------------
# New Unit System Tests (Task 2)
# ---------------------------------------------------------------------------


def test_financial_value_with_new_unit_creation():
    """Test FinancialValue creation with NewUnit instances."""
    from metricengine.units import MoneyUnit, Pct, Qty

    # Test with Money unit
    usd = MoneyUnit("USD")
    fv_usd = FV(100.50, unit=usd)
    assert fv_usd.unit == usd
    assert fv_usd.as_decimal() == D("100.50")

    # Test with Quantity unit
    kg = Qty("kg")
    fv_kg = FV(25.5, unit=kg)
    assert fv_kg.unit == kg
    assert fv_kg.as_decimal() == D("25.50")

    # Test with Percent unit
    ratio = Pct()
    fv_pct = FV(0.15, unit=ratio)
    assert fv_pct.unit == ratio
    assert fv_pct.as_decimal() == D("0.15")


def test_financial_value_with_none_unit():
    """Test FinancialValue creation with None unit (new system default)."""
    fv = FV(42.0, unit=None)
    assert fv.unit is None
    assert fv.as_decimal() == D("42.00")


def test_financial_value_unit_validation():
    """Test unit validation in __post_init__."""
    from metricengine.units import NewUnit

    # Valid NewUnit instance
    unit = NewUnit("Custom", "test")
    fv = FV(10, unit=unit)
    assert fv.unit == unit

    # Invalid unit type should raise TypeError
    with pytest.raises(TypeError, match="Unit must be NewUnit instance"):
        FV(10, unit="invalid")


def test_financial_value_repr_with_new_units():
    """Test __repr__ method includes new unit information correctly."""
    from metricengine.units import MoneyUnit

    # Test with NewUnit
    usd = MoneyUnit("USD")
    fv_usd = FV(100, unit=usd)
    repr_str = repr(fv_usd)
    assert "Money[USD]" in repr_str
    assert "unit=Money[USD]" in repr_str

    # Test with None unit
    fv_none = FV(50, unit=None)
    repr_str = repr(fv_none)
    assert "unit=None" in repr_str

    # Test with legacy unit (backward compatibility)
    fv_legacy = FV(75, unit=Money)
    repr_str = repr(fv_legacy)
    assert "unit=Money" in repr_str


def test_unit_preservation_through_arithmetic():
    """Test that units are preserved through arithmetic operations."""
    from metricengine.units import MoneyUnit

    usd = MoneyUnit("USD")
    fv1 = FV(100, unit=usd)
    fv2 = FV(50, unit=usd)

    # Addition should preserve unit (for now - task 3 will add compatibility checks)
    result = fv1 + fv2
    assert result.unit == usd
    assert result.as_decimal() == D("150.00")

    # Subtraction should preserve unit
    result = fv1 - fv2
    assert result.unit == usd
    assert result.as_decimal() == D("50.00")

    # Multiplication should preserve left operand's unit
    result = fv1 * 2
    assert result.unit == usd
    assert result.as_decimal() == D("200.00")

    # Division should preserve left operand's unit
    result = fv1 / 2
    assert result.unit == usd
    assert result.as_decimal() == D("50.00")


def test_unit_preservation_with_none_unit():
    """Test arithmetic operations with None units."""
    fv1 = FV(100, unit=None)
    fv2 = FV(50, unit=None)

    # Operations with None units should preserve None
    result = fv1 + fv2
    assert result.unit is None
    assert result.as_decimal() == D("150.00")

    result = fv1 * 3
    assert result.unit is None
    assert result.as_decimal() == D("300.00")


def test_mixed_new_and_legacy_units():
    """Test that new and legacy unit systems can coexist."""
    from metricengine.units import MoneyUnit, NewUnit

    # New unit system
    usd = MoneyUnit("USD")
    fv_new = FV(100, unit=usd)

    # Legacy unit system
    fv_legacy = FV(200, unit=Money)

    # Both should work independently
    assert fv_new.unit == usd
    assert fv_legacy.unit == Money
    assert isinstance(fv_new.unit, NewUnit)
    assert isinstance(fv_legacy.unit, type)


def test_provenance_includes_unit_information():
    """Test that provenance metadata includes unit information."""
    from metricengine.units import MoneyUnit

    usd = MoneyUnit("USD")
    fv = FV(100, unit=usd)

    # Check that literal provenance includes unit
    if fv.has_provenance():
        prov = fv.get_provenance()
        assert prov.meta.get("unit") == "Money[USD]"

    # Test arithmetic operation provenance
    fv2 = FV(50, unit=usd)
    result = fv + fv2

    if result.has_provenance():
        prov = result.get_provenance()
        assert prov.meta.get("unit") == "Money[USD]"


def test_provenance_with_none_unit():
    """Test provenance with None units."""
    fv = FV(100, unit=None)

    # None units should not add unit metadata
    if fv.has_provenance():
        prov = fv.get_provenance()
        assert "unit" not in prov.meta or prov.meta.get("unit") == ""


def test_new_unit_helper_functions():
    """Test the helper functions for creating new units."""
    from metricengine.units import MoneyUnit, Pct, Qty

    # Test MoneyUnit helper
    usd = MoneyUnit("USD")
    assert usd.category == "Money"
    assert usd.code == "USD"
    assert str(usd) == "Money[USD]"

    # Test Qty helper
    kg = Qty("kg")
    assert kg.category == "Quantity"
    assert kg.code == "kg"
    assert str(kg) == "Quantity[kg]"

    # Test Pct helper with default
    pct_default = Pct()
    assert pct_default.category == "Percent"
    assert pct_default.code == "ratio"
    assert str(pct_default) == "Percent[ratio]"

    # Test Pct helper with custom code
    bp = Pct("bp")
    assert bp.category == "Percent"
    assert bp.code == "bp"
    assert str(bp) == "Percent[bp]"


def test_backward_compatibility_with_legacy_units():
    """Test that legacy unit system still works unchanged."""
    # Legacy unit creation should still work
    fv_money = FV(100, unit=Money)
    fv_ratio = FV(0.15, unit=Ratio)
    fv_percent = FV(0.15, unit=Percent)
    fv_dimless = FV(42, unit=Dimensionless)

    # All should preserve their legacy behavior
    assert fv_money.unit == Money
    assert fv_ratio.unit == Ratio
    assert fv_percent.unit == Percent
    assert fv_dimless.unit == Dimensionless

    # Arithmetic should still work with legacy units
    result = fv_money + FV(50, unit=Money)
    assert result.unit == Money
    assert result.as_decimal() == D("150.00")


# ---------------------------------------------------------------------------
# Repr Optimization Tests (Task 5) - Multiple Non-Default Parameter Combinations
# ---------------------------------------------------------------------------


def test_repr_custom_policy_plus_custom_unit():
    """Test FinancialValue with custom policy + custom unit combination."""
    # Create a custom policy that differs from DEFAULT_POLICY
    custom_policy = Policy(decimal_places=4)
    fv = FV(100, policy=custom_policy, unit=Money)
    result = repr(fv)
    expected = f"FinancialValue(value=100, policy={custom_policy}, unit=Money)"
    assert result == expected


def test_repr_custom_unit_plus_is_percentage_true():
    """Test FinancialValue with custom unit + is_percentage=True combination."""
    fv = FV(0.15, unit=Percent, _is_percentage=True)
    result = repr(fv)
    expected = "FinancialValue(value=0.15, unit=Percent, is_percentage=True)"
    assert result == expected


def test_repr_custom_policy_plus_is_percentage_true():
    """Test FinancialValue with custom policy + is_percentage=True combination."""
    custom_policy = Policy(decimal_places=3)
    fv = FV(0.125, policy=custom_policy, _is_percentage=True)
    result = repr(fv)
    expected = (
        f"FinancialValue(value=0.125, policy={custom_policy}, is_percentage=True)"
    )
    assert result == expected


def test_repr_all_three_non_default_parameters():
    """Test FinancialValue with all three non-default parameters together."""
    custom_policy = Policy(decimal_places=5)
    fv = FV(0.12345, policy=custom_policy, unit=Ratio, _is_percentage=True)
    result = repr(fv)
    expected = f"FinancialValue(value=0.12345, policy={custom_policy}, unit=Ratio, is_percentage=True)"
    assert result == expected


def test_repr_custom_policy_plus_money_unit():
    """Test FinancialValue with custom policy + Money unit combination."""
    custom_policy = Policy(decimal_places=1, currency_symbol="€")
    fv = FV(99.9, policy=custom_policy, unit=Money)
    result = repr(fv)
    expected = f"FinancialValue(value=99.9, policy={custom_policy}, unit=Money)"
    assert result == expected


def test_repr_custom_policy_plus_ratio_unit():
    """Test FinancialValue with custom policy + Ratio unit combination."""
    custom_policy = Policy(decimal_places=6)
    fv = FV(D("0.123456"), policy=custom_policy, unit=Ratio)
    result = repr(fv)
    expected = f"FinancialValue(value=0.123456, policy={custom_policy}, unit=Ratio)"
    assert result == expected


def test_repr_ratio_unit_plus_is_percentage_true():
    """Test FinancialValue with Ratio unit + is_percentage=True combination."""
    fv = FV(0.25, unit=Ratio, _is_percentage=True)
    result = repr(fv)
    expected = "FinancialValue(value=0.25, unit=Ratio, is_percentage=True)"
    assert result == expected


def test_repr_money_unit_plus_is_percentage_true():
    """Test FinancialValue with Money unit + is_percentage=True combination."""
    # This is an unusual combination but should still work
    fv = FV(100, unit=Money, _is_percentage=True)
    result = repr(fv)
    expected = "FinancialValue(value=100, unit=Money, is_percentage=True)"
    assert result == expected


def test_repr_new_unit_system_combinations():
    """Test FinancialValue with NewUnit system + other non-default parameters."""
    from metricengine.units import MoneyUnit

    # Custom policy + NewUnit
    custom_policy = Policy(decimal_places=3)
    usd = MoneyUnit("USD")
    fv = FV(123.456, policy=custom_policy, unit=usd)
    result = repr(fv)
    expected = f"FinancialValue(value=123.456, policy={custom_policy}, unit=Money[USD])"
    assert result == expected

    # NewUnit + is_percentage=True
    fv2 = FV(0.15, unit=usd, _is_percentage=True)
    result2 = repr(fv2)
    expected2 = "FinancialValue(value=0.15, unit=Money[USD], is_percentage=True)"
    assert result2 == expected2

    # All three with NewUnit
    fv3 = FV(0.12345, policy=custom_policy, unit=usd, _is_percentage=True)
    result3 = repr(fv3)
    expected3 = f"FinancialValue(value=0.12345, policy={custom_policy}, unit=Money[USD], is_percentage=True)"
    assert result3 == expected3


def test_repr_none_unit_combinations():
    """Test FinancialValue with None unit + other non-default parameters."""
    # Custom policy + None unit
    custom_policy = Policy(decimal_places=4)
    fv = FV(42.1234, policy=custom_policy, unit=None)
    result = repr(fv)
    expected = f"FinancialValue(value=42.1234, policy={custom_policy}, unit=None)"
    assert result == expected

    # None unit + is_percentage=True
    fv2 = FV(0.15, unit=None, _is_percentage=True)
    result2 = repr(fv2)
    expected2 = "FinancialValue(value=0.15, unit=None, is_percentage=True)"
    assert result2 == expected2

    # All three with None unit
    fv3 = FV(0.12345, policy=custom_policy, unit=None, _is_percentage=True)
    result3 = repr(fv3)
    expected3 = f"FinancialValue(value=0.12345, policy={custom_policy}, unit=None, is_percentage=True)"
    assert result3 == expected3


def test_repr_complex_policy_combinations():
    """Test FinancialValue with complex policy configurations + other parameters."""
    from decimal import ROUND_UP

    # Complex policy with multiple non-default settings
    complex_policy = Policy(
        decimal_places=3, rounding=ROUND_UP, currency_symbol="£", none_text="N/A"
    )

    # Complex policy + Money unit
    fv = FV(99.9999, policy=complex_policy, unit=Money)
    result = repr(fv)
    expected = f"FinancialValue(value=99.9999, policy={complex_policy}, unit=Money)"
    assert result == expected

    # Complex policy + is_percentage=True
    fv2 = FV(0.1234, policy=complex_policy, _is_percentage=True)
    result2 = repr(fv2)
    expected2 = (
        f"FinancialValue(value=0.1234, policy={complex_policy}, is_percentage=True)"
    )
    assert result2 == expected2

    # All three with complex policy
    fv3 = FV(0.5678, policy=complex_policy, unit=Ratio, _is_percentage=True)
    result3 = repr(fv3)
    expected3 = f"FinancialValue(value=0.5678, policy={complex_policy}, unit=Ratio, is_percentage=True)"
    assert result3 == expected3


def test_repr_parameter_ordering_consistency():
    """Test that parameter ordering is consistent across different combinations."""
    custom_policy = Policy(decimal_places=4)

    # Test different combinations maintain consistent ordering: value, policy, unit, is_percentage

    # Policy + Unit
    fv1 = FV(100, policy=custom_policy, unit=Money)
    result1 = repr(fv1)
    assert result1.find("policy=") < result1.find("unit=")

    # Policy + is_percentage
    fv2 = FV(0.15, policy=custom_policy, _is_percentage=True)
    result2 = repr(fv2)
    assert result2.find("policy=") < result2.find("is_percentage=")

    # Unit + is_percentage
    fv3 = FV(0.25, unit=Ratio, _is_percentage=True)
    result3 = repr(fv3)
    assert result3.find("unit=") < result3.find("is_percentage=")

    # All three parameters
    fv4 = FV(0.125, policy=custom_policy, unit=Percent, _is_percentage=True)
    result4 = repr(fv4)
    assert result4.find("policy=") < result4.find("unit=")
    assert result4.find("unit=") < result4.find("is_percentage=")


def test_repr_edge_case_combinations():
    """Test edge case combinations of non-default parameters."""
    # Zero value with non-default parameters
    custom_policy = Policy(decimal_places=1)
    fv_zero = FV(0, policy=custom_policy, unit=Money, _is_percentage=True)
    result = repr(fv_zero)
    expected = f"FinancialValue(value=0, policy={custom_policy}, unit=Money, is_percentage=True)"
    assert result == expected

    # Negative value with non-default parameters
    fv_negative = FV(-50.5, policy=custom_policy, unit=Ratio, _is_percentage=True)
    result = repr(fv_negative)
    expected = f"FinancialValue(value=-50.5, policy={custom_policy}, unit=Ratio, is_percentage=True)"
    assert result == expected

    # None value with non-default parameters
    fv_none = FV(None, policy=custom_policy, unit=Money, _is_percentage=True)
    result = repr(fv_none)
    expected = f"FinancialValue(value=None, policy={custom_policy}, unit=Money, is_percentage=True)"
    assert result == expected

    # Large decimal with non-default parameters
    fv_large = FV(
        D("999999.123456"), policy=custom_policy, unit=Percent, _is_percentage=True
    )
    result = repr(fv_large)
    expected = f"FinancialValue(value=999999.123456, policy={custom_policy}, unit=Percent, is_percentage=True)"
    assert result == expected


# ---------------------------------------------------------------------------
# Repr Optimization Tests (Task 6) - Edge Cases and Error Handling
# ---------------------------------------------------------------------------


def test_repr_none_unit_in_new_unit_system():
    """Test FinancialValue with None unit in new unit system shows unit=None."""
    # Test None unit explicitly set
    fv = FV(100, unit=None)
    result = repr(fv)
    expected = "FinancialValue(value=100, unit=None)"
    assert result == expected

    # Test None unit with other non-default parameters
    custom_policy = Policy(decimal_places=3)
    fv_with_policy = FV(50.123, policy=custom_policy, unit=None)
    result = repr(fv_with_policy)
    expected = f"FinancialValue(value=50.123, policy={custom_policy}, unit=None)"
    assert result == expected

    # Test None unit with is_percentage=True
    fv_with_percentage = FV(0.25, unit=None, _is_percentage=True)
    result = repr(fv_with_percentage)
    expected = "FinancialValue(value=0.25, unit=None, is_percentage=True)"
    assert result == expected


def test_repr_policy_comparison_edge_cases():
    """Test policy comparison edge cases in repr."""
    # Test with policy that equals DEFAULT_POLICY but is different instance
    policy_copy = Policy(
        decimal_places=DEFAULT_POLICY.decimal_places,
        rounding=DEFAULT_POLICY.rounding,
        currency_symbol=DEFAULT_POLICY.currency_symbol,
        currency_position=DEFAULT_POLICY.currency_position,
        thousands_sep=DEFAULT_POLICY.thousands_sep,
        negative_parentheses=DEFAULT_POLICY.negative_parentheses,
        none_text=DEFAULT_POLICY.none_text,
        percent_style=DEFAULT_POLICY.percent_style,
        cap_percentage_at=DEFAULT_POLICY.cap_percentage_at,
    )

    # Since policies are equal by value, it should NOT be included (correct behavior)
    fv = FV(100, policy=policy_copy)
    result = repr(fv)
    # Should NOT include policy since it equals DEFAULT_POLICY by value
    expected = "FinancialValue(value=100)"
    assert result == expected

    # Test with DEFAULT_POLICY instance (should not be included)
    fv_default = FV(100, policy=DEFAULT_POLICY)
    result = repr(fv_default)
    expected = "FinancialValue(value=100)"
    assert result == expected

    # Test policy comparison with None (edge case during construction)
    # This tests the robustness of policy comparison
    fv_none_policy = FV(100)  # Uses DEFAULT_POLICY internally
    result = repr(fv_none_policy)
    expected = "FinancialValue(value=100)"
    assert result == expected


def test_repr_unit_representation_failure_scenarios():
    """Test unit representation failure scenarios with fallback."""
    from unittest.mock import patch

    # Test the _get_unit_repr method directly with edge cases
    fv = FV(100)

    # Test with None unit
    fv_none = FV(100, unit=None)
    unit_repr = fv_none._get_unit_repr()
    assert unit_repr == "None"

    # Test with NewUnit
    from metricengine.units import NewUnit

    new_unit = NewUnit("Test", "code")
    fv_new = FV(100, unit=new_unit)
    unit_repr = fv_new._get_unit_repr()
    assert unit_repr == "Test[code]"

    # Test with legacy Unit subclass
    fv_money = FV(100, unit=Money)
    unit_repr = fv_money._get_unit_repr()
    assert unit_repr == "Money"

    # Test that _get_unit_repr method exists and handles different unit types
    # Test with Ratio unit
    fv_ratio = FV(0.5, unit=Ratio)
    unit_repr = fv_ratio._get_unit_repr()
    assert unit_repr == "Ratio"

    # Test with Percent unit
    fv_percent = FV(0.15, unit=Percent)
    unit_repr = fv_percent._get_unit_repr()
    assert unit_repr == "Percent"

    # Test with Dimensionless unit
    fv_dimensionless = FV(100, unit=Dimensionless)
    unit_repr = fv_dimensionless._get_unit_repr()
    assert unit_repr == "Dimensionless"

    # Test that repr method calls _get_unit_repr for non-default units
    # This tests the integration between __repr__ and _get_unit_repr
    fv_money_repr = FV(100, unit=Money)
    result = repr(fv_money_repr)
    expected = "FinancialValue(value=100, unit=Money)"
    assert result == expected

    # Test with NewUnit in repr
    fv_new_repr = FV(100, unit=new_unit)
    result = repr(fv_new_repr)
    expected = "FinancialValue(value=100, unit=Test[code])"
    assert result == expected

    # Test error handling by patching _get_unit_repr to raise an exception
    with patch.object(FV, "_get_unit_repr") as mock_get_unit_repr:
        mock_get_unit_repr.side_effect = RuntimeError("Unit repr failed")

        fv_with_unit = FV(100, unit=Money)

        # The repr should propagate the exception since there's no error handling
        # This documents the current behavior
        try:
            result = repr(fv_with_unit)
            # If we get here, there might be error handling we didn't expect
            assert "FinancialValue" in result
        except RuntimeError as e:
            # This is the expected behavior - the exception propagates
            assert "Unit repr failed" in str(e)


def test_repr_mixed_unit_system_scenarios():
    """Test mixed unit system scenarios (NewUnit vs legacy Unit)."""
    from metricengine.units import MoneyUnit, NewUnit, Pct, Qty

    # Test NewUnit Money vs legacy Money
    new_money_unit = MoneyUnit("USD")
    legacy_money_unit = Money

    fv_new = FV(100, unit=new_money_unit)
    fv_legacy = FV(100, unit=legacy_money_unit)

    result_new = repr(fv_new)
    result_legacy = repr(fv_legacy)

    expected_new = "FinancialValue(value=100, unit=Money[USD])"
    expected_legacy = "FinancialValue(value=100, unit=Money)"

    assert result_new == expected_new
    assert result_legacy == expected_legacy

    # Test NewUnit Percent vs legacy Percent
    new_percent_unit = Pct("ratio")
    legacy_percent_unit = Percent

    fv_new_pct = FV(0.15, unit=new_percent_unit)
    fv_legacy_pct = FV(0.15, unit=legacy_percent_unit)

    result_new_pct = repr(fv_new_pct)
    result_legacy_pct = repr(fv_legacy_pct)

    expected_new_pct = "FinancialValue(value=0.15, unit=Percent[ratio])"
    expected_legacy_pct = "FinancialValue(value=0.15, unit=Percent)"

    assert result_new_pct == expected_new_pct
    assert result_legacy_pct == expected_legacy_pct

    # Test NewUnit Quantity (no legacy equivalent)
    qty_unit = Qty("kg")
    fv_qty = FV(25.5, unit=qty_unit)
    result_qty = repr(fv_qty)
    expected_qty = "FinancialValue(value=25.5, unit=Quantity[kg])"
    assert result_qty == expected_qty

    # Test generic NewUnit
    generic_unit = NewUnit("Custom", "test")
    fv_generic = FV(42, unit=generic_unit)
    result_generic = repr(fv_generic)
    expected_generic = "FinancialValue(value=42, unit=Custom[test])"
    assert result_generic == expected_generic

    # Test mixed systems with other non-default parameters
    custom_policy = Policy(decimal_places=4)

    # NewUnit + custom policy
    fv_mixed_new = FV(123.4567, policy=custom_policy, unit=new_money_unit)
    result_mixed_new = repr(fv_mixed_new)
    expected_mixed_new = (
        f"FinancialValue(value=123.4567, policy={custom_policy}, unit=Money[USD])"
    )
    assert result_mixed_new == expected_mixed_new

    # Legacy unit + custom policy
    fv_mixed_legacy = FV(123.4567, policy=custom_policy, unit=legacy_money_unit)
    result_mixed_legacy = repr(fv_mixed_legacy)
    expected_mixed_legacy = (
        f"FinancialValue(value=123.4567, policy={custom_policy}, unit=Money)"
    )
    assert result_mixed_legacy == expected_mixed_legacy

    # Test with is_percentage flag
    fv_new_pct_flag = FV(0.15, unit=new_percent_unit, _is_percentage=True)
    result_new_pct_flag = repr(fv_new_pct_flag)
    expected_new_pct_flag = (
        "FinancialValue(value=0.15, unit=Percent[ratio], is_percentage=True)"
    )
    assert result_new_pct_flag == expected_new_pct_flag

    fv_legacy_pct_flag = FV(0.15, unit=legacy_percent_unit, _is_percentage=True)
    result_legacy_pct_flag = repr(fv_legacy_pct_flag)
    expected_legacy_pct_flag = (
        "FinancialValue(value=0.15, unit=Percent, is_percentage=True)"
    )
    assert result_legacy_pct_flag == expected_legacy_pct_flag


def test_repr_unit_comparison_edge_cases():
    """Test edge cases in unit comparison for repr optimization."""
    # Test with Dimensionless unit (should not be included in repr)
    fv_dimensionless = FV(100, unit=Dimensionless)
    result = repr(fv_dimensionless)
    expected = "FinancialValue(value=100)"
    assert result == expected

    # Test unit comparison with None vs Dimensionless
    fv_none_unit = FV(100, unit=None)
    result_none = repr(fv_none_unit)
    expected_none = "FinancialValue(value=100, unit=None)"
    assert result_none == expected_none

    # Test that None != Dimensionless for repr purposes
    assert None is not Dimensionless

    # Test with subclass of Dimensionless (should be included since it's not exactly Dimensionless)
    class CustomDimensionless(Dimensionless):
        pass

    # We can't easily create FV with CustomDimensionless through normal construction,
    # but we can test the comparison logic
    assert CustomDimensionless != Dimensionless

    # Test unit equality vs identity
    # Two instances of the same unit class should be equal
    money1 = Money
    money2 = Money
    assert money1 == money2
    assert money1 is money2  # Same class object

    # Test with different unit instances that might be equal
    from metricengine.units import MoneyUnit

    usd1 = MoneyUnit("USD")
    usd2 = MoneyUnit("USD")

    # These should be equal NewUnit instances
    assert usd1 == usd2
    assert str(usd1) == str(usd2)

    fv_usd1 = FV(100, unit=usd1)
    fv_usd2 = FV(100, unit=usd2)

    result_usd1 = repr(fv_usd1)
    result_usd2 = repr(fv_usd2)

    # Both should produce the same repr
    expected_usd = "FinancialValue(value=100, unit=Money[USD])"
    assert result_usd1 == expected_usd
    assert result_usd2 == expected_usd


def test_repr_error_handling_robustness():
    """Test repr robustness with various error conditions."""
    # Test with very large numbers
    large_value = D("9" * 100)  # Very large decimal
    fv_large = FV(large_value)
    result = repr(fv_large)
    assert "FinancialValue(value=" in result
    assert str(large_value) in result

    # Test with very small numbers
    small_value = D("1E-50")
    fv_small = FV(small_value)
    result = repr(fv_small)
    assert "FinancialValue(value=" in result
    assert str(small_value) in result

    # Test with special Decimal values
    fv_zero = FV(D("0"))
    result_zero = repr(fv_zero)
    assert result_zero == "FinancialValue(value=0)"

    # Test with negative zero
    fv_neg_zero = FV(D("-0"))
    result_neg_zero = repr(fv_neg_zero)
    assert "FinancialValue(value=" in result_neg_zero

    # Test with Decimal NaN (should be handled by FV construction)
    try:
        fv_nan = FV(D("NaN"))
        result_nan = repr(fv_nan)
        # If NaN is allowed, repr should handle it
        assert "FinancialValue" in result_nan
    except (ValueError, InvalidOperation):
        # If NaN is rejected during construction, that's also valid
        pass

    # Test with Decimal Infinity (should be handled by FV construction)
    try:
        fv_inf = FV(D("Infinity"))
        result_inf = repr(fv_inf)
        # If Infinity is allowed, repr should handle it
        assert "FinancialValue" in result_inf
    except (ValueError, InvalidOperation):
        # If Infinity is rejected during construction, that's also valid
        pass

    # Test repr with all parameters at edge values
    custom_policy = Policy(decimal_places=0)  # Minimum decimal places
    fv_edge = FV(D("0.999"), policy=custom_policy, unit=Money, _is_percentage=True)
    result_edge = repr(fv_edge)
    expected_edge = f"FinancialValue(value=0.999, policy={custom_policy}, unit=Money, is_percentage=True)"
    assert result_edge == expected_edge


def test_repr_parameter_ordering_edge_cases():
    """Test parameter ordering consistency in edge cases."""
    custom_policy = Policy(decimal_places=3)

    # Test all possible combinations to ensure consistent ordering
    # Order should always be: value, policy, unit, is_percentage

    # All parameters present
    fv_all = FV(100, policy=custom_policy, unit=Money, _is_percentage=True)
    result_all = repr(fv_all)
    expected_all = f"FinancialValue(value=100, policy={custom_policy}, unit=Money, is_percentage=True)"
    assert result_all == expected_all

    # Skip policy, include unit and is_percentage
    fv_no_policy = FV(100, unit=Money, _is_percentage=True)
    result_no_policy = repr(fv_no_policy)
    expected_no_policy = "FinancialValue(value=100, unit=Money, is_percentage=True)"
    assert result_no_policy == expected_no_policy

    # Skip unit, include policy and is_percentage
    fv_no_unit = FV(100, policy=custom_policy, _is_percentage=True)
    result_no_unit = repr(fv_no_unit)
    expected_no_unit = (
        f"FinancialValue(value=100, policy={custom_policy}, is_percentage=True)"
    )
    assert result_no_unit == expected_no_unit

    # Skip is_percentage, include policy and unit
    fv_no_percentage = FV(100, policy=custom_policy, unit=Money)
    result_no_percentage = repr(fv_no_percentage)
    expected_no_percentage = (
        f"FinancialValue(value=100, policy={custom_policy}, unit=Money)"
    )
    assert result_no_percentage == expected_no_percentage

    # Only policy
    fv_only_policy = FV(100, policy=custom_policy)
    result_only_policy = repr(fv_only_policy)
    expected_only_policy = f"FinancialValue(value=100, policy={custom_policy})"
    assert result_only_policy == expected_only_policy

    # Only unit
    fv_only_unit = FV(100, unit=Money)
    result_only_unit = repr(fv_only_unit)
    expected_only_unit = "FinancialValue(value=100, unit=Money)"
    assert result_only_unit == expected_only_unit

    # Only is_percentage
    fv_only_percentage = FV(100, _is_percentage=True)
    result_only_percentage = repr(fv_only_percentage)
    expected_only_percentage = "FinancialValue(value=100, is_percentage=True)"
    assert result_only_percentage == expected_only_percentage
