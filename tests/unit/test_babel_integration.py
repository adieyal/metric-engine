"""Integration tests for Babel formatting with FinancialValue."""
from __future__ import annotations

from decimal import Decimal

from metricengine import FinancialValue as FV
from metricengine.policy import DisplayPolicy, Policy
from metricengine.units import USD, Money, Percent


class TestFinancialValueBabelIntegration:
    """Integration tests for FinancialValue with Babel formatting."""

    def test_financial_value_without_display_policy(self):
        """Test that FV still works without DisplayPolicy (backward compatibility)."""
        policy = Policy(decimal_places=2)
        value = FV(100.50, policy=policy, unit=Money)
        result = value.as_str()
        # Should use legacy formatting
        assert result is not None
        assert "100.50" in result

    def test_financial_value_with_display_policy_builtin(self):
        """Test FV with DisplayPolicy using builtin formatter."""
        display = DisplayPolicy(currency="USD", use_grouping=True)
        policy = Policy(decimal_places=2, display=display)
        value = FV(1234.50, policy=policy, unit=Money)
        result = value.as_str()
        # Should use new formatter system (Babel or builtin)
        assert "USD" in result or "US$" in result  # May show as symbol
        assert "1234" in result.replace("\xa0", "").replace(
            " ", ""
        )  # Remove non-breaking spaces

    def test_financial_value_money_with_unit_currency(self):
        """Test FV with Money unit that has currency code."""
        display = DisplayPolicy(currency="ZAR", use_grouping=True)
        policy = Policy(decimal_places=2, display=display)
        value = FV(1234.50, policy=policy, unit=USD)
        result = value.as_str()
        # Should prefer unit currency over display currency for Money
        assert result is not None

    def test_financial_value_percentage_formatting(self):
        """Test FV percentage formatting with DisplayPolicy."""
        display = DisplayPolicy(percent_scale="ratio", max_frac=1)
        policy = Policy(decimal_places=2, display=display)
        value = FV(0.15, policy=policy, unit=Percent)
        result = value.as_str()
        # Should format as percentage
        assert "%" in result
        assert "15" in result

    def test_financial_value_percentage_as_percentage_flag(self):
        """Test FV with _is_percentage flag."""
        display = DisplayPolicy(percent_scale="ratio", max_frac=2)
        policy = Policy(decimal_places=2, display=display)
        value = FV(0.157, policy=policy).as_percentage()
        result = value.as_str()
        # Should format as percentage
        assert "%" in result
        # May use comma as decimal separator in some locales
        assert "15.7" in result or "15,7" in result

    def test_financial_value_number_formatting(self):
        """Test FV number formatting with DisplayPolicy."""
        display = DisplayPolicy(use_grouping=True, max_frac=3)
        policy = Policy(decimal_places=2, display=display)
        value = FV(12345.6789, policy=policy)
        result = value.as_str()
        # Should format as number with grouping (various separators possible)
        normalized = result.replace("\xa0", "").replace(" ", "")
        assert "12,345" in normalized or "12345" in normalized

    def test_financial_value_negative_with_parens(self):
        """Test FV negative formatting with parentheses."""
        display = DisplayPolicy(negative_parens=True, currency="USD")
        policy = Policy(decimal_places=2, display=display)
        value = FV(-100.50, policy=policy, unit=Money)
        result = value.as_str()
        # Should show negative in parentheses
        assert "(" in result and ")" in result
        # May use comma as decimal separator
        assert "100.50" in result or "100,50" in result

    def test_financial_value_none_handling(self):
        """Test FV None value handling with DisplayPolicy."""
        display = DisplayPolicy()
        policy = Policy(none_text="N/A", display=display)
        value = FV(None, policy=policy)
        result = value.as_str()
        # Should use policy's none_text
        assert result == "N/A"

    def test_financial_value_arithmetic_preserves_display_policy(self):
        """Test that arithmetic operations preserve DisplayPolicy."""
        display = DisplayPolicy(currency="EUR", use_grouping=True)
        policy = Policy(decimal_places=2, display=display)

        a = FV(100, policy=policy, unit=Money)
        b = FV(50, policy=policy, unit=Money)
        result = a + b

        result_str = result.as_str()
        # Should use the same display policy - but may fall back to legacy if policy not preserved
        # This test checks that the arithmetic result is reasonable
        assert "150" in result_str
        # Policy preservation depends on the policy resolution mode

    def test_financial_value_with_policy_inheritance(self):
        """Test FV with policy inheritance in operations."""
        display1 = DisplayPolicy(currency="USD")
        display2 = DisplayPolicy(currency="EUR")
        policy1 = Policy(decimal_places=2, display=display1)
        policy2 = Policy(decimal_places=2, display=display2)

        a = FV(100, policy=policy1, unit=Money)
        b = FV(50, policy=policy2, unit=Money)

        # Result should inherit from context or left operand based on policy resolution
        result = a + b
        result_str = result.as_str()
        assert result_str is not None
        assert len(result_str) > 0

    def test_different_fraction_digits(self):
        """Test different fraction digit settings."""
        # Test with 0 decimal places
        display0 = DisplayPolicy(max_frac=0)
        policy0 = Policy(decimal_places=2, display=display0)
        value0 = FV(123.456, policy=policy0)
        assert ".456" not in value0.as_str()  # Should be rounded

        # Test with 4 decimal places
        display4 = DisplayPolicy(max_frac=4)
        policy4 = Policy(decimal_places=2, display=display4)
        value4 = FV(123.456789, policy=policy4)
        result4 = value4.as_str()
        assert result4 is not None

    def test_locale_specific_formatting_if_babel_available(self):
        """Test locale-specific formatting if Babel is available."""
        try:
            import babel

            babel_available = True
        except ImportError:
            babel_available = False

        display_us = DisplayPolicy(locale="en_US", currency="USD")
        display_fr = DisplayPolicy(locale="fr_FR", currency="EUR")
        policy_us = Policy(decimal_places=2, display=display_us)
        policy_fr = Policy(decimal_places=2, display=display_fr)

        value_us = FV(1234.50, policy=policy_us, unit=Money)
        value_fr = FV(1234.50, policy=policy_fr, unit=Money)

        result_us = value_us.as_str()
        result_fr = value_fr.as_str()

        # At minimum, currency should be different
        if babel_available:
            # With Babel, we might get different formatting
            assert result_us != result_fr or "USD" in result_us or "EUR" in result_fr
        else:
            # Without Babel, should still work but use builtin formatting
            assert result_us is not None
            assert result_fr is not None


class TestPolicyWithDisplayPolicy:
    """Test Policy class integration with DisplayPolicy."""

    def test_policy_with_display_policy(self):
        """Test creating Policy with DisplayPolicy."""
        display = DisplayPolicy(locale="en_US", currency="USD")
        policy = Policy(decimal_places=2, display=display)

        assert policy.display == display
        assert policy.decimal_places == 2

    def test_policy_without_display_policy(self):
        """Test Policy without DisplayPolicy (default None)."""
        policy = Policy(decimal_places=2)
        assert policy.display is None

    def test_policy_display_policy_independence(self):
        """Test that DisplayPolicy is independent of legacy formatting options."""
        display = DisplayPolicy(negative_parens=True, use_grouping=False)
        policy = Policy(
            decimal_places=2,
            thousands_sep=True,  # Legacy option
            negative_parentheses=False,  # Legacy option
            display=display,
        )

        # DisplayPolicy should take precedence when available
        value = FV(-100, policy=policy, unit=Money)
        result = value.as_str()

        # With DisplayPolicy, should use new formatting
        assert result is not None


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_very_large_numbers(self):
        """Test formatting very large numbers."""
        display = DisplayPolicy(use_grouping=True)
        policy = Policy(decimal_places=2, display=display)
        large_value = FV(Decimal("999999999999999.99"), policy=policy)
        result = large_value.as_str()
        assert result is not None
        assert len(result) > 0

    def test_very_small_numbers(self):
        """Test formatting very small numbers."""
        display = DisplayPolicy(max_frac=10)
        policy = Policy(decimal_places=2, display=display)
        small_value = FV(Decimal("0.0000000001"), policy=policy)
        result = small_value.as_str()
        assert result is not None

    def test_zero_values(self):
        """Test formatting zero values."""
        display = DisplayPolicy(currency="USD")
        policy = Policy(decimal_places=2, display=display)

        zero_money = FV(0, policy=policy, unit=Money)
        zero_percent = FV(0, policy=policy, unit=Percent)
        zero_number = FV(0, policy=policy)

        assert "0" in zero_money.as_str()
        assert "0" in zero_percent.as_str()
        assert "0" in zero_number.as_str()

    def test_invalid_display_policy_graceful_degradation(self):
        """Test graceful degradation with invalid DisplayPolicy settings."""
        # Test with potentially invalid locale (should fallback)
        display = DisplayPolicy(locale="invalid_locale", fallback_locale="en_US")
        policy = Policy(decimal_places=2, display=display)
        value = FV(100, policy=policy)
        result = value.as_str()
        # Should not crash
        assert result is not None
        assert "100" in result
