"""Tests for Policy configuration."""

from decimal import ROUND_DOWN, ROUND_HALF_UP, ROUND_UP, Decimal
from unittest.mock import patch

import pytest

from metricengine.policy import Policy, default_quantizer_factory
from metricengine.units import Money


class TestDefaultQuantizerFactory:
    """Test the default_quantizer_factory function."""

    def test_default_quantizer_factory(self):
        """Test default quantizer factory function."""
        # Test various decimal places
        assert default_quantizer_factory(0) == Decimal("1")
        assert default_quantizer_factory(1) == Decimal("0.1")
        assert default_quantizer_factory(2) == Decimal("0.01")
        assert default_quantizer_factory(3) == Decimal("0.001")
        assert default_quantizer_factory(4) == Decimal("0.0001")

    def test_default_quantizer_factory_negative(self):
        """Test default quantizer factory with negative decimal places."""
        assert default_quantizer_factory(-1) == Decimal("10")
        assert default_quantizer_factory(-2) == Decimal("100")


class TestPolicy:
    """Test Policy configuration class."""

    def test_default_policy(self):
        """Test default policy values."""
        policy = Policy()
        assert policy.decimal_places == 2
        assert policy.rounding == ROUND_HALF_UP
        assert policy.none_text == "—"
        assert policy.percent_display == "percent"
        assert policy.cap_percentage_at == Decimal("99999.99")
        assert policy.negative_sales_is_none is True
        assert policy.compare_none_as_minus_infinity is False
        assert policy.arithmetic_strict is False
        assert policy.thousands_sep is True
        assert policy.currency_symbol is None
        assert policy.currency_position == "prefix"
        assert policy.negative_parentheses is False
        assert policy.locale is None
        assert policy.quantizer_factory == default_quantizer_factory

    def test_custom_policy(self):
        """Test creating custom policy with various parameters."""
        policy = Policy(
            decimal_places=4,
            rounding=ROUND_DOWN,
            none_text="N/A",
            percent_display="ratio",
            cap_percentage_at=Decimal("100.00"),
            negative_sales_is_none=False,
            compare_none_as_minus_infinity=True,
            arithmetic_strict=True,
            thousands_sep=False,
            currency_symbol="$",
            currency_position="suffix",
            negative_parentheses=True,
            locale="en_US",
        )
        assert policy.decimal_places == 4
        assert policy.rounding == ROUND_DOWN
        assert policy.none_text == "N/A"
        assert policy.percent_display == "ratio"
        assert policy.cap_percentage_at == Decimal("100.00")
        assert policy.negative_sales_is_none is False
        assert policy.compare_none_as_minus_infinity is True
        assert policy.arithmetic_strict is True
        assert policy.thousands_sep is False
        assert policy.currency_symbol == "$"
        assert policy.currency_position == "suffix"
        assert policy.negative_parentheses is True
        assert policy.locale == "en_US"

    def test_policy_immutable(self):
        """Test that policy is immutable (frozen dataclass)."""
        policy = Policy()
        with pytest.raises(AttributeError):
            policy.decimal_places = 3  # type: ignore

    def test_policy_validation_decimal_places(self):
        """Test policy parameter validation for decimal_places."""
        # Valid decimal_places should work
        Policy(decimal_places=0)
        Policy(decimal_places=10)

        # Invalid decimal_places should raise
        with pytest.raises(ValueError, match="decimal_places must be non-negative"):
            Policy(decimal_places=-1)

    def test_policy_validation_cap_percentage_at(self):
        """Test policy parameter validation for cap_percentage_at."""
        # Valid cap_percentage_at should work
        Policy(cap_percentage_at=Decimal("0"))
        Policy(cap_percentage_at=Decimal("100"))

        # Invalid cap_percentage_at should raise
        with pytest.raises(ValueError, match="cap_percentage_at must be non-negative"):
            Policy(cap_percentage_at=Decimal("-1"))

    def test_policy_validation_currency_symbol(self):
        """Test policy parameter validation for currency_symbol."""
        # Valid currency_symbol should work
        Policy(currency_symbol="$")
        Policy(currency_symbol="€")
        Policy(currency_symbol=None)

        # Empty string currency_symbol should raise
        with pytest.raises(
            ValueError, match="currency_symbol must be non-empty or None"
        ):
            Policy(currency_symbol="")

        # Whitespace-only currency_symbol should raise
        with pytest.raises(
            ValueError, match="currency_symbol must be non-empty or None"
        ):
            Policy(currency_symbol="   ")

    def test_quantize_method(self):
        """Test the quantize method."""
        policy = Policy(decimal_places=2, rounding=ROUND_HALF_UP)

        # Test basic quantization
        assert policy.quantize(Decimal("123.456")) == Decimal("123.46")
        assert policy.quantize(Decimal("123.454")) == Decimal("123.45")
        assert policy.quantize(Decimal("123.455")) == Decimal("123.46")  # ROUND_HALF_UP

        # Test with different decimal places
        policy_4dp = Policy(decimal_places=4, rounding=ROUND_DOWN)
        assert policy_4dp.quantize(Decimal("123.456789")) == Decimal("123.4567")

    def test_quantize_with_different_rounding(self):
        """Test quantize method with different rounding modes."""
        # Test ROUND_DOWN
        policy_down = Policy(decimal_places=2, rounding=ROUND_DOWN)
        assert policy_down.quantize(Decimal("123.456")) == Decimal("123.45")

        # Test ROUND_UP
        policy_up = Policy(decimal_places=2, rounding=ROUND_UP)
        assert policy_up.quantize(Decimal("123.451")) == Decimal("123.46")

    def test_custom_quantizer_factory(self):
        """Test custom quantizer factory."""

        def custom_factory(dp: int) -> Decimal:
            return Decimal("0.5") ** dp

        policy = Policy(quantizer_factory=custom_factory, decimal_places=2)
        quantizer = policy.quantizer_factory(2)
        assert quantizer == Decimal("0.25")  # 0.5^2

        # Test that quantize method uses the custom factory
        assert policy.quantize(Decimal("123.456")) == Decimal("123.46")

    @patch("metricengine.units.Money")
    @patch("metricengine.units.Unit")
    def test_format_decimal_basic(self, mock_unit, mock_money):
        """Test format_decimal method with basic formatting."""
        policy = Policy(decimal_places=2, thousands_sep=True)

        # Test basic number formatting with thousands separator
        result = policy.format_decimal(Decimal("1234.56"), mock_unit)
        assert result == "1,234.56"

        # Test without thousands separator
        policy_no_sep = Policy(decimal_places=2, thousands_sep=False)
        result = policy_no_sep.format_decimal(Decimal("1234.56"), mock_unit)
        assert result == "1234.56"

    @patch("metricengine.units.Money")
    @patch("metricengine.units.Unit")
    def test_format_decimal_currency_prefix(self, mock_unit, mock_money):
        """Test format_decimal method with currency symbol as prefix."""
        policy = Policy(
            decimal_places=2,
            thousands_sep=True,
            currency_symbol="$",
            currency_position="prefix",
        )

        result = policy.format_decimal(Decimal("1234.56"), mock_money)
        assert result == "$1,234.56"

    @patch("metricengine.units.Money")
    @patch("metricengine.units.Unit")
    def test_format_decimal_currency_suffix(self, mock_unit, mock_money):
        """Test format_decimal method with currency symbol as suffix."""
        policy = Policy(
            decimal_places=2,
            thousands_sep=True,
            currency_symbol="€",
            currency_position="suffix",
        )

        result = policy.format_decimal(Decimal("1234.56"), mock_money)
        assert result == "1,234.56€"

    @patch("metricengine.units.Money")
    @patch("metricengine.units.Unit")
    def test_format_decimal_negative_parentheses(self, mock_unit, mock_money):
        """Test format_decimal method with negative parentheses."""
        policy = Policy(
            decimal_places=2,
            thousands_sep=True,
            currency_symbol="$",
            currency_position="prefix",
            negative_parentheses=True,
        )

        result = policy.format_decimal(Decimal("-1234.56"), mock_money)
        assert result == "($1,234.56)"

    @patch("metricengine.units.Money")
    @patch("metricengine.units.Unit")
    def test_format_decimal_non_money_unit(self, mock_unit, mock_money):
        """Test format_decimal method with non-money unit (no currency symbol)."""
        policy = Policy(
            decimal_places=2,
            thousands_sep=True,
            currency_symbol="$",
            currency_position="prefix",
        )

        result = policy.format_decimal(Decimal("1234.56"), mock_unit)
        assert result == "1,234.56"  # No currency symbol for non-money units

    def test_format_percent_ratio_display(self):
        """Test format_percent method with ratio display."""
        policy = Policy(percent_display="ratio", decimal_places=3)

        result = policy.format_percent(Decimal("0.1234"))
        assert result == "0.123"  # Should be quantized to 3 decimal places

    def test_format_percent_percent_display(self):
        """Test format_percent method with percent display."""
        policy = Policy(percent_display="percent", decimal_places=1)

        result = policy.format_percent(Decimal("0.1234"))
        assert result == "12.3%"  # 0.1234 * 100 = 12.34, quantized to 1 dp = 12.3

    def test_format_percent_cap_percentage(self):
        """Test format_percent method with percentage capping."""
        policy = Policy(
            percent_display="percent",
            decimal_places=2,
            cap_percentage_at=Decimal("100.00"),
        )

        # Test normal percentage
        result = policy.format_percent(Decimal("0.5"))
        assert result == "50.00%"

        # Test capped percentage
        result = policy.format_percent(Decimal("2.0"))  # 200%
        assert result == "100.00%"  # Should be capped

    def test_format_percent_zero_cap(self):
        """Test format_percent method with zero cap."""
        policy = Policy(
            percent_display="percent", decimal_places=2, cap_percentage_at=Decimal("0")
        )

        result = policy.format_percent(Decimal("0.5"))
        assert result == "0.00%"  # Should be capped at 0

    def test_policy_repr(self):
        """Test policy string representation."""
        policy = Policy()
        repr_str = repr(policy)
        assert "Policy(" in repr_str
        assert "decimal_places=2" in repr_str
        assert "percent_display='percent'" in repr_str

    def test_policy_equality(self):
        """Test policy equality comparison."""
        policy1 = Policy()
        policy2 = Policy()
        policy3 = Policy(decimal_places=3)

        assert policy1 == policy2
        assert policy1 != policy3

    def test_policy_hash(self):
        """Test that policy is hashable (required for frozen dataclass)."""
        policy = Policy()
        # Should not raise an exception
        hash(policy)

        # Different policies should have different hashes
        policy1 = Policy()
        policy2 = Policy(decimal_places=3)
        assert hash(policy1) != hash(policy2)

    def test_policy_copy(self):
        """Test that policy can be copied."""
        from copy import copy

        policy = Policy(decimal_places=3)
        policy_copy = copy(policy)

        assert policy == policy_copy
        assert policy is not policy_copy  # Different objects

    def test_policy_deepcopy(self):
        """Test that policy can be deep copied."""
        from copy import deepcopy

        policy = Policy(decimal_places=3)
        policy_deepcopy = deepcopy(policy)

        assert policy == policy_deepcopy
        assert policy is not policy_deepcopy  # Different objects


class TestPolicyEdgeCases:
    """Test edge cases and boundary conditions for Policy."""

    def test_zero_decimal_places(self):
        """Test policy with zero decimal places."""
        policy = Policy(decimal_places=0)
        assert policy.quantize(Decimal("123.456")) == Decimal("123")
        assert policy.quantize(Decimal("123.6")) == Decimal("124")  # ROUND_HALF_UP

    def test_high_decimal_places(self):
        """Test policy with high decimal places."""
        policy = Policy(decimal_places=10)
        result = policy.quantize(Decimal("123.123456789012345"))
        assert result == Decimal("123.1234567890")

    def test_very_large_cap_percentage(self):
        """Test policy with very large cap percentage."""
        policy = Policy(cap_percentage_at=Decimal("999999.99"), thousands_sep=False)
        result = policy.format_percent(Decimal("1000.0"))  # 100,000%
        assert result == "100000.00%"

    def test_currency_symbol_edge_cases(self):
        """Test currency symbol edge cases."""
        # Unicode currency symbols
        policy = Policy(currency_symbol="¥", currency_position="prefix")
        assert policy.currency_symbol == "¥"

        # Multi-character currency symbols
        policy = Policy(currency_symbol="USD", currency_position="suffix")
        assert policy.currency_symbol == "USD"

    def test_locale_edge_cases(self):
        """Test locale edge cases."""
        # Standard locale
        policy = Policy(locale="en_US")
        assert policy.locale == "en_US"

        # Locale with country
        policy = Policy(locale="fr_FR")
        assert policy.locale == "fr_FR"

        # Locale without country
        policy = Policy(locale="en")
        assert policy.locale == "en"


class TestPolicyIntegration:
    """Test Policy integration with other components."""

    def test_quantizer_factory_integration(self):
        """Test that quantizer_factory integrates properly with quantize method."""

        def custom_factory(dp: int) -> Decimal:
            # Custom factory that returns different quantizers
            if dp == 0:
                return Decimal("1")
            elif dp == 1:
                return Decimal("0.5")  # Half-dollar precision
            else:
                return Decimal("0.1") ** dp

        policy = Policy(quantizer_factory=custom_factory, decimal_places=1)

        # Should use the custom factory
        quantizer = policy.quantizer_factory(1)
        assert quantizer == Decimal("0.5")

        # quantize method should use the custom factory
        result = policy.quantize(Decimal("123.7"))
        assert result == Decimal("123.5")  # Quantized to 0.5 precision

    def test_format_methods_consistency(self):
        """Test that format methods are consistent with policy settings."""
        policy = Policy(
            decimal_places=3,
            thousands_sep=False,
            currency_symbol="€",
            currency_position="suffix",
            negative_parentheses=True,
        )

        # Test that both format methods respect decimal_places
        decimal_result = policy.format_decimal(Decimal("1234.5678"), Money)
        assert decimal_result == "1234.568€"  # 3 decimal places

        percent_result = policy.format_percent(Decimal("0.12345"))
        assert percent_result == "12.345%"  # 3 decimal places

    def test_policy_immutability_preserved(self):
        """Test that policy immutability is preserved in all operations."""
        policy = Policy(decimal_places=2)
        original_decimal_places = policy.decimal_places

        # All these operations should not modify the original policy
        policy.quantize(Decimal("123.456"))
        policy.format_decimal(Decimal("123.456"), Money)
        policy.format_percent(Decimal("0.123"))

        assert policy.decimal_places == original_decimal_places
        assert policy.decimal_places == 2
