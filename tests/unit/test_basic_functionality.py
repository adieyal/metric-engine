"""Basic functionality tests that demonstrate calculate_many working correctly."""

from decimal import Decimal

import pytest

from metricengine import (
    Engine,
    MissingInputError,
    inputs_needed_for,
)


class TestBasicFunctionality:
    """Test basic functionality without clearing the registry."""

    def setup_method(self):
        """Set up test fixtures."""
        # Don't clear registry - use production calculations
        self.engine = Engine()

    def test_simple_functionality(self):
        """Test basic functionality works."""
        ctx = {"sales": Decimal("1000"), "cost": Decimal("600")}
        result = self.engine.calculate("gross_profit", ctx)
        assert result.as_decimal() == Decimal("400")

    def test_calculate_many_basic(self):
        """Test calculate_many basic functionality."""
        ctx = {"sales": Decimal("1000"), "cost": Decimal("600")}
        targets = {"gross_profit", "gross_margin_percentage"}

        results = self.engine.calculate_many(targets, ctx)

        assert len(results) == 2
        assert results["gross_profit"].as_decimal() == Decimal("400")
        assert results["gross_margin_percentage"].as_decimal() == Decimal("40.00")

    def test_inputs_needed_for_basic(self):
        """Test inputs_needed_for basic functionality."""
        needed = inputs_needed_for({"gross_profit"})
        assert needed == {"sales", "cost"}

    def test_calculate_many_missing_input(self):
        """Test error when required inputs are missing."""
        ctx = {"sales": Decimal("1000")}  # cost is missing
        targets = {"gross_profit"}

        with pytest.raises(MissingInputError) as exc:
            self.engine.calculate_many(targets, ctx)

        assert "cost" in str(exc.value)

    def test_calculate_many_allow_partial(self):
        """Test partial calculation when allow_partial=True."""
        ctx = {
            "sales": Decimal("1000"),
            "cost": Decimal("600"),
            "part": Decimal("250"),
            "total": Decimal("1000"),
        }
        # variance_percentage needs actual and expected (missing), others have all inputs
        targets = {"gross_profit", "percentage_of_total", "variance_percentage"}

        results = self.engine.calculate_many(targets, ctx, allow_partial=True)

        # Should get the ones that can be calculated
        assert "gross_profit" in results
        assert "percentage_of_total" in results
        # Should not get the one with missing inputs
        assert "variance_percentage" not in results

        assert results["gross_profit"].as_decimal() == Decimal("400.00")
        assert results["percentage_of_total"].as_decimal() == Decimal("25.00")
