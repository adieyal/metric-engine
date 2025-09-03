from decimal import Decimal as D
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
    """Test __repr__ includes all fields (line 328)"""
    p = Policy(decimal_places=2)
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
    assert result1 == True  # a is None -> True
    assert result2 == False  # b is None -> False


def test_gt_with_none_operand():
    """Test __gt__ with None operand (line 499, 501)"""
    # Test the actual behavior - the comparison should return boolean values
    none_fv = FV(None)
    one_fv = FV(1)

    # Test that the comparison returns boolean values
    result1 = one_fv > none_fv
    result2 = none_fv > one_fv

    # Based on __gt__ logic: if b is None, return a is not None; if a is None, return False
    assert result1 == True  # b is None, a is not None -> True
    assert result2 == False  # a is None -> False


def test_ge_with_none_operand():
    """Test __ge__ with None operand (line 505-510)"""
    # Test the actual behavior - the comparison should return boolean values
    none_fv = FV(None)
    one_fv = FV(1)

    # Test that the comparison returns boolean values
    result1 = one_fv >= none_fv
    result2 = none_fv >= one_fv

    # Based on __ge__ logic: if b is None, return True; if a is None, return False
    assert result1 == True  # b is None -> True
    assert result2 == False  # a is None -> False


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
