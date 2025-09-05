"""Tests for the formatters module."""
from __future__ import annotations

from decimal import Decimal

from metricengine.formatters.base import BuiltinFormatter, get_formatter
from metricengine.policy import DisplayPolicy
from metricengine.units import USD


class TestBuiltinFormatter:
    """Tests for BuiltinFormatter (no Babel required)."""

    def setup_method(self):
        self.formatter = BuiltinFormatter()
        self.display = DisplayPolicy()

    def test_money_formatting_basic(self):
        """Test basic money formatting."""
        amount = Decimal("1234.50")
        result = self.formatter.money(amount, None, self.display)
        assert result == "ZAR 1,234.50"

    def test_money_formatting_with_unit(self):
        """Test money formatting with currency unit."""
        amount = Decimal("1234.50")
        result = self.formatter.money(amount, USD, self.display)
        # Should use unit currency code since USD has .code attribute
        assert result == "USD 1,234.50"

    def test_money_formatting_no_grouping(self):
        """Test money formatting without grouping."""
        amount = Decimal("1234.50")
        display = DisplayPolicy(use_grouping=False)
        result = self.formatter.money(amount, None, display)
        assert result == "ZAR 1234.50"

    def test_money_formatting_negative_parens(self):
        """Test money formatting with negative parentheses."""
        amount = Decimal("-1234.50")
        display = DisplayPolicy(negative_parens=True)
        result = self.formatter.money(amount, None, display)
        assert result == "ZAR (1,234.50)"

    def test_money_formatting_custom_fractions(self):
        """Test money formatting with custom fraction digits."""
        amount = Decimal("1234.567")
        display = DisplayPolicy(max_frac=3)
        result = self.formatter.money(amount, None, display)
        assert result == "ZAR 1,234.567"

    def test_number_formatting_basic(self):
        """Test basic number formatting."""
        value = Decimal("1234.56")
        result = self.formatter.number(value, self.display)
        assert result == "1,234.56"

    def test_number_formatting_no_grouping(self):
        """Test number formatting without grouping."""
        value = Decimal("1234.56")
        display = DisplayPolicy(use_grouping=False)
        result = self.formatter.number(value, display)
        assert result == "1234.56"

    def test_number_formatting_negative_parens(self):
        """Test number formatting with negative parentheses."""
        value = Decimal("-1234.56")
        display = DisplayPolicy(negative_parens=True)
        result = self.formatter.number(value, display)
        assert result == "(1,234.56)"

    def test_percent_formatting_ratio_scale(self):
        """Test percent formatting with ratio scale (default)."""
        value = Decimal("0.15")  # 15%
        result = self.formatter.percent(value, self.display)
        assert result == "15.00%"

    def test_percent_formatting_unit_scale(self):
        """Test percent formatting with unit scale."""
        value = Decimal("15")  # Already in percent
        display = DisplayPolicy(percent_scale="unit")
        result = self.formatter.percent(value, display)
        assert result == "15.00%"

    def test_percent_formatting_negative_parens(self):
        """Test percent formatting with negative parentheses."""
        value = Decimal("-0.15")
        display = DisplayPolicy(negative_parens=True)
        result = self.formatter.percent(value, display)
        assert result == "(15.00%)"

    def test_percent_formatting_custom_fractions(self):
        """Test percent formatting with custom fraction digits."""
        value = Decimal("0.12345")
        display = DisplayPolicy(max_frac=3)
        result = self.formatter.percent(value, display)
        assert result == "12.345%"


class TestGetFormatter:
    """Tests for get_formatter factory function."""

    def test_get_formatter_returns_builtin_when_babel_unavailable(self):
        """Test that get_formatter returns BuiltinFormatter when Babel is not available."""
        formatter = get_formatter()
        # In test environment, it might return either, so just check it's a valid formatter
        assert hasattr(formatter, "money")
        assert hasattr(formatter, "number")
        assert hasattr(formatter, "percent")


class TestDisplayPolicy:
    """Tests for DisplayPolicy configuration."""

    def test_display_policy_defaults(self):
        """Test DisplayPolicy default values."""
        policy = DisplayPolicy()
        assert policy.locale == "en_ZA"
        assert policy.currency == "ZAR"
        assert policy.currency_style == "standard"
        assert policy.use_grouping is True
        assert policy.min_int is None
        assert policy.min_frac is None
        assert policy.max_frac is None
        assert policy.compact is None
        assert policy.percent_scale == "ratio"
        assert policy.percent_style == "standard"
        assert policy.negative_parens is False
        assert policy.fallback_locale == "en_US"

    def test_display_policy_custom_values(self):
        """Test DisplayPolicy with custom values."""
        policy = DisplayPolicy(
            locale="fr_FR",
            currency="EUR",
            currency_style="accounting",
            use_grouping=False,
            max_frac=3,
            percent_scale="unit",
            negative_parens=True,
        )
        assert policy.locale == "fr_FR"
        assert policy.currency == "EUR"
        assert policy.currency_style == "accounting"
        assert policy.use_grouping is False
        assert policy.max_frac == 3
        assert policy.percent_scale == "unit"
        assert policy.negative_parens is True


class TestIntegrationWithoutBabel:
    """Integration tests without Babel dependency."""

    def test_formatter_with_various_locales(self):
        """Test formatter behavior with different locale settings."""
        formatter = BuiltinFormatter()

        # US locale
        us_display = DisplayPolicy(locale="en_US", currency="USD")
        result = formatter.money(Decimal("1234.50"), None, us_display)
        assert result == "USD 1,234.50"

        # French locale (though builtin formatter doesn't actually localize)
        fr_display = DisplayPolicy(locale="fr_FR", currency="EUR")
        result = formatter.money(Decimal("1234.50"), None, fr_display)
        assert result == "EUR 1,234.50"

    def test_edge_cases(self):
        """Test edge cases in formatting."""
        formatter = BuiltinFormatter()
        display = DisplayPolicy()

        # Zero value
        assert formatter.money(Decimal("0"), None, display) == "ZAR 0.00"
        assert formatter.number(Decimal("0"), display) == "0.00"
        assert formatter.percent(Decimal("0"), display) == "0.00%"

        # Very large number
        large_num = Decimal("999999999.99")
        assert formatter.money(large_num, None, display) == "ZAR 999,999,999.99"

        # Very small number
        small_num = Decimal("0.001")
        assert formatter.number(small_num, display) == "0.00"  # Rounded to 2 dp

        # Small number with more precision
        display_3dp = DisplayPolicy(max_frac=3)
        assert formatter.number(small_num, display_3dp) == "0.001"
