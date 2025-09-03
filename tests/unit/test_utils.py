"""Tests for metric engine utility functions."""

from decimal import Decimal

import pytest

from metricengine.exceptions import CalculationError
from metricengine.null_behaviour import (
    NullBehavior,
    NullBinaryMode,
    use_nulls,
)
from metricengine.utils import to_decimal
from metricengine.value import FinancialValue


class TestToDecimal:
    """Test the to_decimal utility function."""

    def test_decimal_input(self):
        """Test that Decimal inputs are returned as-is."""
        value = Decimal("123.45")
        result = to_decimal(value)
        assert result == value
        assert isinstance(result, Decimal)

    def test_none_input(self):
        """Test that None inputs are propagated."""
        result = to_decimal(None)
        assert result is None

    def test_financial_value_input(self):
        """Test that FinancialValue inputs return their internal value."""
        # Test with valid value
        fv = FinancialValue(Decimal("99.99"))
        result = to_decimal(fv)
        assert result == Decimal("99.99")
        assert isinstance(result, Decimal)

        # Test with None value
        fv_none = FinancialValue(None)
        result = to_decimal(fv_none)
        assert result is None

    def test_int_input(self):
        """Test that int inputs are converted to Decimal."""
        result = to_decimal(42)
        assert result == Decimal("42")
        assert isinstance(result, Decimal)

        result = to_decimal(0)
        assert result == Decimal("0")
        assert isinstance(result, Decimal)

        result = to_decimal(-100)
        assert result == Decimal("-100")
        assert isinstance(result, Decimal)

    def test_str_input_valid(self):
        """Test that valid string inputs are converted to Decimal."""
        result = to_decimal("123.45")
        assert result == Decimal("123.45")
        assert isinstance(result, Decimal)

        result = to_decimal("0")
        assert result == Decimal("0")
        assert isinstance(result, Decimal)

        result = to_decimal("-99.99")
        assert result == Decimal("-99.99")
        assert isinstance(result, Decimal)

        # Test that comma-separated strings fail to parse (as expected)
        result = to_decimal("1,234.56")
        assert result is None  # Decimal constructor doesn't handle commas

    def test_str_input_invalid(self):
        """Test that invalid string inputs are handled according to null behavior."""
        # Test with default null behavior (PROPAGATE)
        result = to_decimal("not a number")
        assert result is None

        # Test with RAISE null behavior
        with use_nulls(NullBehavior(binary=NullBinaryMode.RAISE)):
            with pytest.raises(CalculationError) as exc_info:
                to_decimal("not a number")
            assert "Invalid operation: not a number" in str(exc_info.value)

    def test_float_input_valid(self):
        """Test that valid float inputs are converted to Decimal."""
        result = to_decimal(123.45)
        assert result == Decimal("123.45")
        assert isinstance(result, Decimal)

        result = to_decimal(0.0)
        assert result == Decimal("0.0")
        assert isinstance(result, Decimal)

        result = to_decimal(-99.99)
        assert result == Decimal("-99.99")
        assert isinstance(result, Decimal)

    def test_float_input_special_values(self):
        """Test that special float values are handled correctly."""
        # Python's Decimal constructor accepts inf and nan
        result = to_decimal(float("inf"))
        assert result == Decimal("Infinity")
        assert isinstance(result, Decimal)

        result = to_decimal(float("nan"))
        # NaN doesn't equal itself, so check the string representation
        assert str(result) == "NaN"
        assert isinstance(result, Decimal)

    def test_supports_float_input(self):
        """Test that SupportsFloat objects are converted via float()."""

        class MockSupportsFloat:
            def __float__(self):
                return 42.5

        result = to_decimal(MockSupportsFloat())
        assert result == Decimal("42.5")
        assert isinstance(result, Decimal)

    def test_supports_float_input_special_values(self):
        """Test that SupportsFloat objects with special values are handled correctly."""

        class MockInfSupportsFloat:
            def __float__(self):
                return float("inf")

        class MockNaNSupportsFloat:
            def __float__(self):
                return float("nan")

        # These don't raise InvalidOperation, so they're converted successfully
        result = to_decimal(MockInfSupportsFloat())
        assert result == Decimal("Infinity")
        assert isinstance(result, Decimal)

        result = to_decimal(MockNaNSupportsFloat())
        # NaN doesn't equal itself, so check the string representation
        assert str(result) == "NaN"
        assert isinstance(result, Decimal)

    def test_unsupported_type(self):
        """Test that unsupported types are handled according to null behavior."""
        # Test with default null behavior (PROPAGATE)
        result = to_decimal([1, 2, 3])
        assert result is None

        result = to_decimal({"key": "value"})
        assert result is None

        # Test with RAISE null behavior
        with use_nulls(NullBehavior(binary=NullBinaryMode.RAISE)):
            with pytest.raises(TypeError) as exc_info:
                to_decimal([1, 2, 3])
            assert "Unsupported type for Decimal conversion: list" in str(
                exc_info.value
            )

            with pytest.raises(TypeError) as exc_info:
                to_decimal({"key": "value"})
            assert "Unsupported type for Decimal conversion: dict" in str(
                exc_info.value
            )

    def test_null_behavior_context_switching(self):
        """Test that null behavior context switching works correctly."""
        # Test switching between PROPAGATE and RAISE modes
        with use_nulls(NullBehavior(binary=NullBinaryMode.RAISE)):
            # Should raise with RAISE mode
            with pytest.raises(CalculationError):
                to_decimal("invalid string")

        # Should return None with default PROPAGATE mode
        result = to_decimal("invalid string")
        assert result is None

    def test_mixed_type_conversions(self):
        """Test mixed type conversions in sequence."""
        # Test various types in sequence
        assert to_decimal(42) == Decimal("42")
        assert to_decimal("99.99") == Decimal("99.99")
        assert to_decimal(Decimal("123.45")) == Decimal("123.45")
        assert to_decimal(None) is None
        assert to_decimal(FinancialValue(50)) == Decimal("50")

    def test_decimal_precision_preservation(self):
        """Test that decimal precision is preserved during conversion."""
        # Test high precision values
        high_precision = Decimal("123.4567890123456789")
        result = to_decimal(high_precision)
        assert result == high_precision
        assert str(result) == "123.4567890123456789"

        # Test string with high precision
        result = to_decimal("123.4567890123456789")
        assert result == Decimal("123.4567890123456789")

    def test_negative_values(self):
        """Test negative value handling."""
        # Test negative integers
        assert to_decimal(-42) == Decimal("-42")
        assert to_decimal(-0) == Decimal("0")

        # Test negative floats
        assert to_decimal(-123.45) == Decimal("-123.45")
        assert to_decimal(-0.0) == Decimal("-0.0")

        # Test negative strings
        assert to_decimal("-99.99") == Decimal("-99.99")
        assert to_decimal("-0") == Decimal("-0")

    def test_zero_values(self):
        """Test zero value handling."""
        # Test various zero representations
        assert to_decimal(0) == Decimal("0")
        assert to_decimal(0.0) == Decimal("0.0")
        assert to_decimal("0") == Decimal("0")
        assert to_decimal("0.0") == Decimal("0.0")
        assert to_decimal(Decimal("0")) == Decimal("0")

    def test_empty_string_handling(self):
        """Test empty string handling."""
        # Empty strings should fail to parse
        result = to_decimal("")
        assert result is None

        # Whitespace-only strings should fail to parse
        result = to_decimal("   ")
        assert result is None

        # Test with RAISE null behavior
        with use_nulls(NullBehavior(binary=NullBinaryMode.RAISE)):
            with pytest.raises(CalculationError):
                to_decimal("")

    def test_whitespace_handling(self):
        """Test whitespace handling in strings."""
        # Strings with leading/trailing whitespace should work
        assert to_decimal("  123.45  ") == Decimal("123.45")
        assert to_decimal("\t42\n") == Decimal("42")
        assert to_decimal("  -99.99  ") == Decimal("-99.99")

    def test_scientific_notation(self):
        """Test scientific notation handling."""
        # Scientific notation should work
        assert to_decimal("1.23e-4") == Decimal("1.23E-4")
        assert to_decimal("1.23E+4") == Decimal("1.23E+4")
        assert to_decimal("1.23e4") == Decimal("1.23E+4")

    def test_currency_symbols(self):
        """Test currency symbol handling."""
        # Currency symbols should cause parsing to fail
        result = to_decimal("$123.45")
        assert result is None

        result = to_decimal("€99.99")
        assert result is None

        result = to_decimal("£50.00")
        assert result is None

        # Test with RAISE null behavior
        with use_nulls(NullBehavior(binary=NullBinaryMode.RAISE)):
            with pytest.raises(CalculationError):
                to_decimal("$123.45")

    def test_fraction_input(self):
        """Test fraction input handling."""
        # Fractions should work via SupportsFloat
        from fractions import Fraction

        result = to_decimal(Fraction(1, 2))
        assert result == Decimal("0.5")
        assert isinstance(result, Decimal)

        result = to_decimal(Fraction(3, 4))
        assert result == Decimal("0.75")
        assert isinstance(result, Decimal)

    def test_numpy_compatibility(self):
        """Test numpy array compatibility."""
        try:
            import numpy as np

            # Test numpy scalar types
            result = to_decimal(np.float64(42.5))
            assert result == Decimal("42.5")
            assert isinstance(result, Decimal)

            result = to_decimal(np.int64(100))
            assert result == Decimal("100")
            assert isinstance(result, Decimal)

        except ImportError:
            # Skip if numpy is not available
            pytest.skip("numpy not available")

    def test_error_message_content(self):
        """Test that error messages contain useful information."""
        with use_nulls(NullBehavior(binary=NullBinaryMode.RAISE)):
            # Test string parsing error
            with pytest.raises(CalculationError) as exc_info:
                to_decimal("invalid")
            assert "Invalid operation: invalid" in str(exc_info.value)

            # Test unsupported type error
            with pytest.raises(TypeError) as exc_info:
                to_decimal([1, 2, 3])
            assert "Unsupported type for Decimal conversion: list" in str(
                exc_info.value
            )

    def test_context_restoration(self):
        """Test that null behavior context is properly restored."""
        # Test that context switching works correctly
        with use_nulls(NullBehavior(binary=NullBinaryMode.RAISE)):
            # Should raise
            with pytest.raises(CalculationError):
                to_decimal("invalid")

        # Should be back to PROPAGATE mode
        result = to_decimal("invalid")
        assert result is None
