"""Tests for calculate_many functionality."""

from decimal import Decimal

import pytest

from metricengine import (
    Engine,
    MissingInputError,
    inputs_needed_for,
)


class TestCalculateMany:
    """Test the calculate_many method and related functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.engine = Engine()

    def test_calculate_many_success(self):
        """Test successful calculation of multiple targets."""
        ctx = {"sales": Decimal("1000"), "cost": Decimal("600")}
        targets = {"gross_profit", "gross_margin_percentage"}

        results = self.engine.calculate_many(targets, ctx)

        assert len(results) == 2
        assert "gross_profit" in results
        assert "gross_margin_percentage" in results
        assert results["gross_profit"].as_decimal() == Decimal("400")
        assert results["gross_margin_percentage"].as_decimal() == Decimal("40.00")

    def test_calculate_many_shared_dependencies(self):
        """Test that shared dependencies are calculated only once."""
        # For this test, we'll verify behavior through results
        # The DAG resolution ensures shared dependencies are calculated once
        ctx = {
            "sales": Decimal("1000"),
            "cost": Decimal("600"),
            "tax_rate": Decimal("0.1"),
        }

        # These calculations share dependencies:
        # - gross_margin_percentage depends on gross_profit
        # - gross_margin_percentage_ex_tax depends on gross_profit_ex_tax
        # - gross_profit_ex_tax depends on sales_ex_tax
        targets = {
            "gross_profit",
            "gross_margin_percentage",
            "gross_profit_ex_tax",
            "gross_margin_percentage_ex_tax",
        }

        results = self.engine.calculate_many(targets, ctx)

        # All should be calculated successfully
        assert len(results) == 4
        assert results["gross_profit"].as_decimal() == Decimal("400")
        assert results["gross_margin_percentage"].as_decimal() == Decimal("40.00")

        # Verify the ex_tax calculations too
        sales_ex_tax = Decimal("1000") / Decimal("1.1")  # ~909.09
        gross_profit_ex_tax = sales_ex_tax - Decimal("600")
        assert abs(
            results["gross_profit_ex_tax"].as_decimal() - gross_profit_ex_tax
        ) < Decimal("0.01")

    def test_calculate_many_missing_input(self):
        """Test error when required inputs are missing."""
        ctx = {"sales": Decimal("1000")}  # cost is missing
        targets = {"gross_profit"}

        with pytest.raises(MissingInputError) as exc:
            self.engine.calculate_many(targets, ctx)

        assert "cost" in str(exc.value)
        assert "gross_profit" in str(exc.value)

    def test_calculate_many_allow_partial(self):
        """Test partial calculation when allow_partial=True."""
        ctx = {
            "sales": Decimal("1000"),
            "part": Decimal("250"),
            "total": Decimal("1000"),
        }
        # gross_profit needs cost (missing), percentage_of_total has all inputs
        targets = {"gross_profit", "percentage_of_total"}

        results = self.engine.calculate_many(targets, ctx, allow_partial=True)

        # Should only get percentage_of_total
        assert len(results) == 1
        assert "percentage_of_total" in results
        assert "gross_profit" not in results
        assert results["percentage_of_total"].as_decimal() == Decimal("25.00")

    def test_calculate_many_with_lists(self):
        """Test calculation with list inputs."""
        ctx = {"values": [10, 20, 30, 40], "weights": [1, 2, 3, 4]}
        targets = {"average_value", "weighted_average"}

        results = self.engine.calculate_many(targets, ctx)

        assert len(results) == 2
        assert results["average_value"].as_decimal() == Decimal("25.00")
        # (10*1 + 20*2 + 30*3 + 40*4) / (1+2+3+4) = 300/10 = 30
        assert results["weighted_average"].as_decimal() == Decimal("30.00")

    def test_calculate_many_empty_targets(self):
        """Test with empty targets set."""
        ctx = {"sales": Decimal("1000")}
        results = self.engine.calculate_many(set(), ctx)

        assert results == {}

    def test_calculate_many_unregistered_target(self):
        """Test with unregistered calculation."""
        ctx = {"sales": Decimal("1000")}
        targets = {"nonexistent_calculation"}

        with pytest.raises(MissingInputError) as exc:
            self.engine.calculate_many(targets, ctx)

        assert "nonexistent_calculation" in str(exc.value)

    def test_calculate_many_mixed_success_failure(self):
        """Test mixed success and failure without allow_partial."""
        ctx = {
            "sales": Decimal("1000"),
            "cost": Decimal("600"),
            # Missing data for other calculations
        }
        targets = {
            "gross_profit",
            "variance_percentage",
        }  # variance needs actual and expected

        with pytest.raises(MissingInputError) as exc:
            self.engine.calculate_many(targets, ctx)

        # Should mention the missing inputs for variance_percentage
        assert "variance_percentage" in str(exc.value)
        assert "actual" in str(exc.value) or "expected" in str(exc.value)

    def test_calculate_many_complex_dependencies(self):
        """Test with complex nested dependencies."""
        ctx = {
            "sales": Decimal("1100"),
            "tax_rate": Decimal("0.1"),
            "cost": Decimal("600"),
        }
        targets = {
            "sales_ex_tax",
            "gross_profit_ex_tax",
            "gross_margin_percentage_ex_tax",
        }

        results = self.engine.calculate_many(targets, ctx)

        assert len(results) == 3
        assert results["sales_ex_tax"].as_decimal() == Decimal("1000.00")
        assert results["gross_profit_ex_tax"].as_decimal() == Decimal("400.00")
        assert results["gross_margin_percentage_ex_tax"].as_decimal() == Decimal(
            "40.00"
        )


class TestInputHelpers:
    """Test the helper functions."""

    def test_inputs_needed_for_simple(self):
        """Test finding inputs for simple calculations."""
        # gross_profit needs sales and cost
        needed = inputs_needed_for({"gross_profit"})
        assert needed == {"sales", "cost"}

    def test_inputs_needed_for_multiple(self):
        """Test finding inputs for multiple calculations."""
        # Both need sales and cost
        needed = inputs_needed_for({"gross_profit", "gross_margin_percentage"})
        assert needed == {"sales", "cost"}

    def test_inputs_needed_for_nested(self):
        """Test finding inputs for nested calculations."""
        # gross_margin_percentage depends on gross_profit which needs sales and cost
        needed = inputs_needed_for({"gross_margin_percentage"})
        assert needed == {"sales", "cost"}

    def test_inputs_needed_for_complex(self):
        """Test finding inputs for complex calculations."""
        needed = inputs_needed_for(
            {"gross_profit_ex_tax", "gross_margin_percentage_ex_tax"}
        )
        # Should need sales, tax_rate, and cost
        assert needed == {"sales", "tax_rate", "cost"}

    def test_inputs_needed_for_unregistered(self):
        """Test with unregistered calculations."""
        # Unregistered calculations are treated as base inputs
        needed = inputs_needed_for({"unregistered_metric"})
        assert needed == {"unregistered_metric"}

    def test_inputs_needed_for_mixed(self):
        """Test with mix of registered and unregistered."""
        needed = inputs_needed_for({"gross_profit", "custom_input"})
        assert needed == {"sales", "cost", "custom_input"}


class TestEngineIntegration:
    """Integration tests for Engine with calculate_many."""

    def setup_method(self):
        """Set up test fixtures."""
        self.engine = Engine()

    def test_calculate_single_via_many(self):
        """Test that calculate() properly delegates to calculate_many()."""
        ctx = {"sales": Decimal("1000"), "cost": Decimal("600")}

        # Calculate single metric
        single_result = self.engine.calculate("gross_profit", ctx)

        # Calculate via many
        many_results = self.engine.calculate_many({"gross_profit"}, ctx)

        assert single_result.as_decimal() == many_results["gross_profit"].as_decimal()

    def test_real_world_dashboard_scenario(self):
        """Test a realistic dashboard scenario with multiple KPIs."""
        # Simulate data from database
        ctx = {
            "sales": Decimal("50000"),
            "cost": Decimal("30000"),
            "tax_rate": Decimal("0.15"),
            "opening_inventory": Decimal("5000"),
            "purchases": Decimal("25000"),
            "closing_inventory": Decimal("3000"),
            "operating_income": Decimal("15000"),
            "revenue": Decimal("50000"),
        }

        # KPIs for dashboard
        kpis = {
            "gross_profit",
            "gross_margin_percentage",
            "sales_ex_tax",
            "cogs",
            "operating_margin",
        }

        results = self.engine.calculate_many(kpis, ctx)

        assert len(results) == 5
        assert all(kpi in results for kpi in kpis)

        # Verify some calculations
        assert results["gross_profit"].as_decimal() == Decimal("20000.00")
        assert results["gross_margin_percentage"].as_decimal() == Decimal("40.00")
        assert results["cogs"].as_decimal() == Decimal("27000.00")

    def test_partial_dashboard_graceful_degradation(self):
        """Test dashboard with incomplete data using allow_partial."""
        # Some data is missing
        ctx = {
            "sales": Decimal("50000"),
            "cost": Decimal("30000"),
            "part": Decimal("5000"),
            "total": Decimal("50000"),
            # Missing: tax_rate, inventory data, etc.
        }

        # Request many KPIs
        kpis = {
            "gross_profit",
            "gross_margin_percentage",
            "sales_ex_tax",  # Needs tax_rate (missing)
            "cogs",  # Needs inventory data (missing)
            "percentage_of_total",  # Has all inputs
        }

        results = self.engine.calculate_many(kpis, ctx, allow_partial=True)

        # Should get what's possible
        assert "gross_profit" in results
        assert "gross_margin_percentage" in results
        assert "percentage_of_total" in results

        # Should not get what needs missing data
        assert "sales_ex_tax" not in results
        assert "cogs" not in results

        # Verify calculated values
        assert results["gross_profit"].as_decimal() == Decimal("20000.00")
        assert results["percentage_of_total"].as_decimal() == Decimal("10.00")
