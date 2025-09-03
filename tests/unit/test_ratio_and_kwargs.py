"""Test ratio() method and **kwargs support."""

from decimal import Decimal

import pytest

from metricengine import Engine, FinancialValue, Policy


class TestRatioMethod:
    """Test the ratio() method on FinancialValue."""

    def test_ratio_conversion(self):
        """Test converting percentage to ratio."""
        policy = Policy()

        # Test regular percentage
        percentage = FinancialValue(Decimal("0.35"), policy)
        ratio = percentage.ratio()
        assert ratio.policy is not None
        assert ratio.policy.percent_style == "ratio"
        assert ratio._is_percentage == False  # Should be False for ratio
        assert ratio.as_decimal() == Decimal("0.35")

        # Test 100%
        percentage = FinancialValue(Decimal("1"), policy)
        ratio = percentage.ratio()
        assert ratio.as_decimal() == Decimal("1.00")

        # Test 0%
        percentage = FinancialValue(Decimal("0"), policy)
        ratio = percentage.ratio()
        assert ratio.as_decimal() == Decimal("0.00")

    def test_ratio_with_none(self):
        """Test ratio() with None value."""
        policy = Policy()
        none_value = FinancialValue(None, policy)
        ratio = none_value.ratio()

        assert ratio.is_none()
        assert str(ratio) == "—"

    def test_ratio_with_calculation(self):
        """Test ratio() on actual calculation results."""
        engine = Engine()

        # Calculate a percentage
        margin = engine.calculate("gross_margin_percentage", sales=1000, cost=650)
        assert margin.as_decimal() == Decimal("35.00")

        # Convert to ratio
        ratio = margin.ratio()
        assert ratio.as_decimal() == Decimal("0.35")


class TestKwargsSupport:
    """Test **kwargs support in Engine methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.engine = Engine()

    def test_calculate_with_kwargs(self):
        """Test calculate() with keyword arguments."""
        # Using kwargs
        result1 = self.engine.calculate("gross_profit", sales=1000, cost=650)

        # Using dict
        result2 = self.engine.calculate("gross_profit", {"sales": 1000, "cost": 650})

        assert result1.as_decimal() == result2.as_decimal() == Decimal("350.00")

    def test_calculate_with_mixed_inputs(self):
        """Test calculate() with both dict and kwargs."""
        # kwargs should override dict values
        result = self.engine.calculate(
            "gross_profit",
            {"sales": 900, "cost": 600},  # These should be ignored
            sales=1000,
            cost=650,
        )

        assert result.as_decimal() == Decimal("350.00")  # Uses kwargs values

    def test_calculate_with_none_ctx(self):
        """Test calculate() with ctx=None."""
        result = self.engine.calculate("gross_profit", None, sales=1000, cost=650)
        assert result.as_decimal() == Decimal("350.00")

    def test_calculate_many_with_kwargs(self):
        """Test calculate_many() with keyword arguments."""
        results = self.engine.calculate_many(
            {"gross_profit", "gross_margin_percentage"}, sales=1000, cost=650
        )

        assert len(results) == 2
        assert results["gross_profit"].as_decimal() == Decimal("350.00")
        assert results["gross_margin_percentage"].as_decimal() == Decimal("35.00")

    def test_calculate_many_with_mixed_inputs(self):
        """Test calculate_many() with both dict and kwargs."""
        results = self.engine.calculate_many(
            {"gross_profit", "sales_ex_tax"},
            {"sales": 900, "tax_rate": 0.15},  # sales should be overridden
            sales=1000,
            cost=650,
            tax_rate=0.1,  # This overrides the dict value
        )

        assert results["gross_profit"].as_decimal() == Decimal("350.00")
        assert results["sales_ex_tax"].as_decimal() == Decimal("909.09")

    def test_empty_kwargs(self):
        """Test that empty kwargs work correctly."""
        # Should raise MissingInputError
        with pytest.raises(Exception) as exc_info:
            self.engine.calculate("gross_profit")

        assert "MissingInputError" in str(type(exc_info.value))


class TestCombinedFeatures:
    """Test using ratio() and kwargs together."""

    def test_percentage_calculations_with_kwargs(self):
        """Test calculating percentages with kwargs and converting to ratios."""
        engine = Engine()

        # Calculate multiple percentages using kwargs
        results = engine.calculate_many(
            {"gross_margin_percentage", "cost_percent"}, sales=1000, cost=650
        )

        # Check percentages
        assert results["gross_margin_percentage"].as_decimal() == Decimal("35.00")
        assert results["cost_percent"].as_decimal() == Decimal("65.00")

        # Convert to ratios
        gm_ratio = results["gross_margin_percentage"].ratio()
        cost_ratio = results["cost_percent"].ratio()

        assert gm_ratio.as_decimal() == Decimal("0.35")
        assert cost_ratio.as_decimal() == Decimal("0.65")

        # Ratios should sum to 1
        assert (gm_ratio + cost_ratio).as_decimal() == Decimal("1.00")
