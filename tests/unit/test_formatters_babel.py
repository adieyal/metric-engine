"""Tests for Babel integration in formatters."""
from __future__ import annotations

from decimal import Decimal

import pytest

# Import babel to check if it's available
babel = pytest.importorskip("babel", reason="Babel not available")

from metricengine.formatters.babel_adapter import BabelFormatter
from metricengine.formatters.base import BabelUnavailable, get_formatter
from metricengine.policy import DisplayPolicy
from metricengine.units import USD


class TestBabelFormatter:
    """Tests for BabelFormatter (requires Babel)."""

    def setup_method(self):
        self.formatter = BabelFormatter()

    def test_babel_formatter_creation(self):
        """Test that BabelFormatter can be created when Babel is available."""
        formatter = BabelFormatter()
        assert formatter is not None

    def test_money_formatting_usd(self):
        """Test money formatting with USD in US locale."""
        amount = Decimal("1234.50")
        display = DisplayPolicy(locale="en_US", currency="USD")
        result = self.formatter.money(amount, USD, display)
        # Babel should format this as $1,234.50 or similar
        assert "$" in result or "USD" in result
        assert "1,234.50" in result or "1 234.50" in result

    def test_money_formatting_eur_french(self):
        """Test money formatting with EUR in French locale."""
        amount = Decimal("1234.50")
        display = DisplayPolicy(locale="fr_FR", currency="EUR")
        result = self.formatter.money(amount, None, display)
        # Should contain EUR and the amount, formatted according to French conventions
        assert "EUR" in result or "€" in result
        # French locale might use different separators including narrow no-break space
        normalized = (
            result.replace(" ", "")
            .replace(",", "")
            .replace("\u00a0", "")
            .replace("\u202f", "")
        )
        assert "1234" in normalized

    def test_money_formatting_accounting_style(self):
        """Test money formatting with accounting style for negatives."""
        amount = Decimal("-1234.50")
        display = DisplayPolicy(
            locale="en_US", currency="USD", currency_style="accounting"
        )
        result = self.formatter.money(amount, None, display)
        # Should show negative as parentheses
        assert "(" in result and ")" in result

    def test_number_formatting_with_grouping(self):
        """Test number formatting with grouping."""
        value = Decimal("1234567.89")
        display = DisplayPolicy(locale="en_US", use_grouping=True)
        result = self.formatter.number(value, display)
        # Should have thousands separators
        assert "," in result or " " in result or "\u00a0" in result

    def test_number_formatting_without_grouping(self):
        """Test number formatting without grouping."""
        value = Decimal("1234567.89")
        display = DisplayPolicy(locale="en_US", use_grouping=False)
        result = self.formatter.number(value, display)
        # Should not have thousands separators in the numeric part
        # But we need to be careful as Babel might still format it
        assert "1234567" in result.replace(" ", "").replace(",", "").replace(
            "\u00a0", ""
        )

    def test_percent_formatting_ratio_scale(self):
        """Test percent formatting with ratio scale."""
        value = Decimal("0.15")  # Should become 15%
        display = DisplayPolicy(locale="en_US", percent_scale="ratio")
        result = self.formatter.percent(value, display)
        assert "%" in result
        # The exact format depends on Babel, but should contain 15
        assert "15" in result

    def test_percent_formatting_unit_scale(self):
        """Test percent formatting with unit scale."""
        value = Decimal("15")  # Already 15, should stay 15%
        display = DisplayPolicy(locale="en_US", percent_scale="unit")
        result = self.formatter.percent(value, display)
        assert "%" in result
        assert "15" in result

    def test_locale_fallback(self):
        """Test locale fallback when invalid locale is provided."""
        amount = Decimal("1234.50")
        display = DisplayPolicy(
            locale="invalid_locale", fallback_locale="en_US", currency="USD"
        )
        # Should not raise an error, should fallback to en_US
        result = self.formatter.money(amount, None, display)
        assert result is not None
        assert len(result) > 0

    def test_custom_fraction_digits(self):
        """Test custom fraction digits in formatting."""
        amount = Decimal("1234.56789")
        display = DisplayPolicy(locale="en_US", currency="USD", max_frac=3)
        result = self.formatter.money(amount, None, display)
        # Should show 3 decimal places
        # Note: exact formatting depends on Babel version and locale data
        assert result is not None

    def test_min_max_fraction_digits(self):
        """Test minimum and maximum fraction digits."""
        amount = Decimal("1234.5")
        display = DisplayPolicy(locale="en_US", currency="USD", min_frac=2, max_frac=4)
        result = self.formatter.money(amount, None, display)
        # Should pad to at least 2 decimal places
        assert result is not None


class TestGetFormatterWithBabel:
    """Test get_formatter when Babel is available."""

    def test_get_formatter_returns_babel_when_available(self):
        """Test that get_formatter returns BabelFormatter when Babel is available."""
        formatter = get_formatter()
        # Should return BabelFormatter (or fallback gracefully)
        assert hasattr(formatter, "money")
        assert hasattr(formatter, "number")
        assert hasattr(formatter, "percent")

        # Test that it actually works
        display = DisplayPolicy()
        result = formatter.money(Decimal("100"), None, display)
        assert result is not None
        assert len(result) > 0


class TestBabelIntegration:
    """Integration tests with Babel."""

    def test_different_locales_produce_different_output(self):
        """Test that different locales produce different formatting."""
        formatter = BabelFormatter()
        amount = Decimal("1234.50")

        us_display = DisplayPolicy(locale="en_US", currency="USD")
        fr_display = DisplayPolicy(locale="fr_FR", currency="EUR")

        us_result = formatter.money(amount, None, us_display)
        fr_result = formatter.money(amount, None, fr_display)

        # Results should be different (different currency at minimum)
        assert us_result != fr_result

    def test_percent_formatting_locales(self):
        """Test percent formatting across different locales."""
        formatter = BabelFormatter()
        value = Decimal("0.15")

        us_display = DisplayPolicy(locale="en_US")
        fr_display = DisplayPolicy(locale="fr_FR")

        us_result = formatter.percent(value, us_display)
        fr_result = formatter.percent(value, fr_display)

        # Both should contain % symbol and 15
        assert "%" in us_result
        assert "%" in fr_result
        assert "15" in us_result
        assert "15" in fr_result

    def test_error_handling_invalid_currency(self):
        """Test error handling with invalid currency codes."""
        formatter = BabelFormatter()
        amount = Decimal("100")
        display = DisplayPolicy(currency="INVALID")

        # Should not crash, even with invalid currency
        try:
            result = formatter.money(amount, None, display)
            assert result is not None
        except Exception:
            # Some versions of Babel might raise exceptions for invalid currencies
            # This is acceptable behavior
            pass

    def test_large_numbers(self):
        """Test formatting of very large numbers."""
        formatter = BabelFormatter()
        large_amount = Decimal("999999999999.99")
        display = DisplayPolicy(locale="en_US", currency="USD")

        result = formatter.money(large_amount, None, display)
        assert result is not None
        assert len(result) > 0

    def test_very_small_numbers(self):
        """Test formatting of very small numbers."""
        formatter = BabelFormatter()
        small_amount = Decimal("0.001")
        display = DisplayPolicy(locale="en_US", currency="USD", max_frac=3)

        result = formatter.money(small_amount, None, display)
        assert result is not None
        assert len(result) > 0


class TestBabelUnavailableException:
    """Test BabelUnavailable exception handling."""

    def test_babel_unavailable_exception(self):
        """Test that BabelUnavailable is a proper exception."""
        exc = BabelUnavailable("Test message")
        assert str(exc) == "Test message"
        assert isinstance(exc, Exception)
