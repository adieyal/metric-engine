"""Tests for arithmetic unit safety checks (Task 3)."""

from decimal import Decimal as D

import pytest

from metricengine.units import MoneyUnit, Pct, Qty
from metricengine.value import FinancialValue as FV


class TestArithmeticUnitSafety:
    """Test arithmetic operations with unit safety checks."""

    def test_add_same_units_success(self):
        """Test addition with same units succeeds."""
        usd = MoneyUnit("USD")
        a = FV(100, unit=usd)
        b = FV(50, unit=usd)

        result = a + b
        assert result.as_decimal() == D("150.00")
        assert result.unit == usd

    def test_add_different_units_raises_error(self):
        """Test addition with different units raises ValueError."""
        usd = MoneyUnit("USD")
        gbp = MoneyUnit("GBP")
        a = FV(100, unit=usd)
        b = FV(50, unit=gbp)

        with pytest.raises(
            ValueError,
            match="Incompatible units for \\+: Money\\[USD\\] \\+ Money\\[GBP\\]",
        ):
            a + b

    def test_add_unit_with_none_preserves_unit(self):
        """Test addition of unit with None preserves the unit."""
        usd = MoneyUnit("USD")
        a = FV(100, unit=usd)
        b = FV(50, unit=None)

        result = a + b
        assert result.as_decimal() == D("150.00")
        assert result.unit == usd

    def test_add_none_with_unit_preserves_unit(self):
        """Test addition of None with unit preserves the unit."""
        usd = MoneyUnit("USD")
        a = FV(100, unit=None)
        b = FV(50, unit=usd)

        result = a + b
        assert result.as_decimal() == D("150.00")
        assert result.unit == usd

    def test_add_both_none_units_preserves_none(self):
        """Test addition with both None units preserves None."""
        a = FV(100, unit=None)
        b = FV(50, unit=None)

        result = a + b
        assert result.as_decimal() == D("150.00")
        assert result.unit is None

    def test_sub_same_units_success(self):
        """Test subtraction with same units succeeds."""
        kg = Qty("kg")
        a = FV(100, unit=kg)
        b = FV(30, unit=kg)

        result = a - b
        assert result.as_decimal() == D("70.00")
        assert result.unit == kg

    def test_sub_different_units_raises_error(self):
        """Test subtraction with different units raises ValueError."""
        kg = Qty("kg")
        lbs = Qty("lbs")
        a = FV(100, unit=kg)
        b = FV(30, unit=lbs)

        with pytest.raises(
            ValueError,
            match="Incompatible units for -: Quantity\\[kg\\] - Quantity\\[lbs\\]",
        ):
            a - b

    def test_sub_unit_with_none_preserves_unit(self):
        """Test subtraction of unit with None preserves the unit."""
        pct = Pct("ratio")
        a = FV(0.5, unit=pct)
        b = FV(0.1, unit=None)

        result = a - b
        assert result.as_decimal() == D("0.40")
        assert result.unit == pct

    def test_sub_none_with_unit_preserves_unit(self):
        """Test subtraction of None with unit preserves the unit."""
        pct = Pct("bp")
        a = FV(500, unit=None)
        b = FV(100, unit=pct)

        result = a - b
        assert result.as_decimal() == D("400.00")
        assert result.unit == pct

    def test_mul_preserves_left_operand_unit(self):
        """Test multiplication preserves left operand's unit (conservative)."""
        usd = MoneyUnit("USD")
        ratio = Pct("ratio")
        a = FV(100, unit=usd)
        b = FV(0.5, unit=ratio)

        result = a * b
        assert result.as_decimal() == D("50.00")
        assert result.unit == usd  # Left operand's unit preserved

    def test_mul_different_units_preserves_left(self):
        """Test multiplication with different units preserves left operand's unit."""
        kg = Qty("kg")
        meters = Qty("m")
        a = FV(10, unit=kg)
        b = FV(5, unit=meters)

        result = a * b
        assert result.as_decimal() == D("50.00")
        assert result.unit == kg  # Left operand's unit preserved

    def test_mul_with_none_unit_preserves_left(self):
        """Test multiplication with None unit preserves left operand's unit."""
        usd = MoneyUnit("USD")
        a = FV(100, unit=usd)
        b = FV(2, unit=None)

        result = a * b
        assert result.as_decimal() == D("200.00")
        assert result.unit == usd

    def test_mul_none_with_unit_preserves_none(self):
        """Test multiplication of None unit with unit preserves None."""
        usd = MoneyUnit("USD")
        a = FV(100, unit=None)
        b = FV(2, unit=usd)

        result = a * b
        assert result.as_decimal() == D("200.00")
        assert result.unit is None  # Left operand's None preserved

    def test_div_preserves_left_operand_unit(self):
        """Test division preserves left operand's unit (conservative)."""
        usd = MoneyUnit("USD")
        ratio = Pct("ratio")
        a = FV(100, unit=usd)
        b = FV(0.5, unit=ratio)

        result = a / b
        assert result.as_decimal() == D("200.00")
        assert result.unit == usd  # Left operand's unit preserved

    def test_div_different_units_preserves_left(self):
        """Test division with different units preserves left operand's unit."""
        kg = Qty("kg")
        seconds = Qty("s")
        a = FV(100, unit=kg)
        b = FV(5, unit=seconds)

        result = a / b
        assert result.as_decimal() == D("20.00")
        assert result.unit == kg  # Left operand's unit preserved

    def test_div_with_none_unit_preserves_left(self):
        """Test division with None unit preserves left operand's unit."""
        kg = Qty("kg")
        a = FV(100, unit=kg)
        b = FV(4, unit=None)

        result = a / b
        assert result.as_decimal() == D("25.00")
        assert result.unit == kg

    def test_div_none_with_unit_preserves_none(self):
        """Test division of None unit with unit preserves None."""
        kg = Qty("kg")
        a = FV(100, unit=None)
        b = FV(4, unit=kg)

        result = a / b
        assert result.as_decimal() == D("25.00")
        assert result.unit is None  # Left operand's None preserved

    def test_radd_with_raw_value(self):
        """Test reverse addition with raw value."""
        usd = MoneyUnit("USD")
        a = FV(100, unit=usd)

        result = 50 + a  # Raw value + FinancialValue
        assert result.as_decimal() == D("150.00")
        assert result.unit == usd

    def test_rsub_with_raw_value(self):
        """Test reverse subtraction with raw value."""
        usd = MoneyUnit("USD")
        a = FV(30, unit=usd)

        result = 100 - a  # Raw value - FinancialValue
        assert result.as_decimal() == D("70.00")
        assert result.unit == usd

    def test_rmul_with_raw_value(self):
        """Test reverse multiplication with raw value."""
        usd = MoneyUnit("USD")
        a = FV(50, unit=usd)

        result = 2 * a  # Raw value * FinancialValue
        assert result.as_decimal() == D("100.00")
        assert result.unit == usd

    def test_rtruediv_with_raw_value(self):
        """Test reverse division with raw value."""
        ratio = Pct("ratio")
        a = FV(0.5, unit=ratio)

        result = 100 / a  # Raw value / FinancialValue
        assert result.as_decimal() == D("200.00")
        # For rtruediv, the result should have None unit since raw values have no unit
        assert result.unit is None

    def test_mixed_category_units_addition_fails(self):
        """Test addition of different category units fails."""
        usd = MoneyUnit("USD")
        kg = Qty("kg")
        a = FV(100, unit=usd)
        b = FV(50, unit=kg)

        with pytest.raises(
            ValueError,
            match="Incompatible units for \\+: Money\\[USD\\] \\+ Quantity\\[kg\\]",
        ):
            a + b

    def test_mixed_category_units_subtraction_fails(self):
        """Test subtraction of different category units fails."""
        pct = Pct("ratio")
        kg = Qty("kg")
        a = FV(0.5, unit=pct)
        b = FV(10, unit=kg)

        with pytest.raises(
            ValueError,
            match="Incompatible units for -: Percent\\[ratio\\] - Quantity\\[kg\\]",
        ):
            a - b

    def test_same_category_different_code_addition_fails(self):
        """Test addition of same category but different code units fails."""
        usd = MoneyUnit("USD")
        eur = MoneyUnit("EUR")
        a = FV(100, unit=usd)
        b = FV(50, unit=eur)

        with pytest.raises(
            ValueError,
            match="Incompatible units for \\+: Money\\[USD\\] \\+ Money\\[EUR\\]",
        ):
            a + b

    def test_multiplication_different_categories_preserves_left(self):
        """Test multiplication of different categories preserves left unit."""
        usd = MoneyUnit("USD")
        kg = Qty("kg")
        a = FV(100, unit=usd)
        b = FV(5, unit=kg)

        result = a * b
        assert result.as_decimal() == D("500.00")
        assert result.unit == usd  # Left operand preserved

    def test_division_different_categories_preserves_left(self):
        """Test division of different categories preserves left unit."""
        kg = Qty("kg")
        pct = Pct("ratio")
        a = FV(100, unit=kg)
        b = FV(0.25, unit=pct)

        result = a / b
        assert result.as_decimal() == D("400.00")
        assert result.unit == kg  # Left operand preserved


class TestLegacyUnitCompatibility:
    """Test that legacy unit system still works."""

    def test_legacy_units_still_work(self):
        """Test that legacy unit system is not broken by new unit safety."""
        from metricengine.units import Money

        a = FV(100, unit=Money)
        b = FV(50, unit=Money)

        result = a + b
        assert result.as_decimal() == D("150.00")
        assert result.unit is Money

    def test_legacy_incompatible_units_return_none(self):
        """Test that legacy incompatible units still return None."""
        from metricengine.units import Money, Ratio

        a = FV(100, unit=Money)
        b = FV(0.5, unit=Ratio)

        result = a + b
        assert result.is_none()  # Legacy behavior: returns None instead of raising
