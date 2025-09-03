"""Tests for unit economics calculations module."""

from decimal import Decimal

import pytest

from metricengine.engine import Engine
from metricengine.exceptions import CalculationError
from metricengine.policy import Policy
from metricengine.units import Dimensionless, Money
from metricengine.value import FV


class TestUnitEconomicsCalculations:
    """Test unit economics calculations with comprehensive coverage."""

    def setup_method(self):
        """Set up test fixtures."""
        self.engine = Engine(Policy(decimal_places=4, arithmetic_strict=False))
        self.strict_engine = Engine(Policy(decimal_places=4, arithmetic_strict=True))

    def test_revenue_per_unit_basic(self):
        """Test basic revenue per unit calculation."""
        ctx = {"total_revenue": 10000, "units_sold": 500}
        result = self.engine.calculate("revenue_per_unit", ctx)
        # 10000 / 500 = 20
        assert result.as_decimal() == Decimal("20.0000")

    def test_revenue_per_unit_with_none_values(self):
        """Test revenue per unit with None inputs."""
        # None total_revenue
        ctx = {"total_revenue": None, "units_sold": 500}
        result = self.engine.calculate("revenue_per_unit", ctx)
        assert result.is_none()

        # None units_sold
        ctx = {"total_revenue": 10000, "units_sold": None}
        result = self.engine.calculate("revenue_per_unit", ctx)
        assert result.is_none()

        # Both None
        ctx = {"total_revenue": None, "units_sold": None}
        result = self.engine.calculate("revenue_per_unit", ctx)
        assert result.is_none()

    def test_revenue_per_unit_zero_units_strict(self):
        """Test revenue per unit with zero units in strict mode."""
        ctx = {"total_revenue": 10000, "units_sold": 0}
        with pytest.raises(
            CalculationError, match="revenue_per_unit undefined for units_sold == 0"
        ):
            self.strict_engine.calculate("revenue_per_unit", ctx)

    def test_revenue_per_unit_zero_units_safe(self):
        """Test revenue per unit with zero units in safe mode."""
        ctx = {"total_revenue": 10000, "units_sold": 0}
        result = self.engine.calculate("revenue_per_unit", ctx)
        assert result.is_none()

    def test_revenue_per_unit_zero_revenue(self):
        """Test revenue per unit with zero revenue."""
        ctx = {"total_revenue": 0, "units_sold": 500}
        result = self.engine.calculate("revenue_per_unit", ctx)
        # 0 / 500 = 0
        assert result.as_decimal() == Decimal("0.0000")

    def test_revenue_per_unit_negative_values(self):
        """Test revenue per unit with negative values."""
        # Negative revenue (e.g., refunds)
        ctx = {"total_revenue": -1000, "units_sold": 100}
        result = self.engine.calculate("revenue_per_unit", ctx)
        assert result.as_decimal() == Decimal("-10.0000")

        # Negative units (not realistic but mathematically valid)
        ctx = {"total_revenue": 1000, "units_sold": -100}
        result = self.engine.calculate("revenue_per_unit", ctx)
        assert result.as_decimal() == Decimal("-10.0000")

    def test_revenue_per_unit_fractional_units(self):
        """Test revenue per unit with fractional units."""
        ctx = {"total_revenue": 1000, "units_sold": 33.33}
        result = self.engine.calculate("revenue_per_unit", ctx)
        # 1000 / 33.33 ≈ 30.003
        assert abs(result.as_decimal() - Decimal("30.0030")) < Decimal("0.0001")

    def test_cost_per_unit_basic(self):
        """Test basic cost per unit calculation."""
        ctx = {"total_cost": 7500, "units": 250}
        result = self.engine.calculate("cost_per_unit", ctx)
        # 7500 / 250 = 30
        assert result.as_decimal() == Decimal("30.0000")

    def test_cost_per_unit_with_none_values(self):
        """Test cost per unit with None inputs."""
        # None total_cost
        ctx = {"total_cost": None, "units": 250}
        result = self.engine.calculate("cost_per_unit", ctx)
        assert result.is_none()

        # None units
        ctx = {"total_cost": 7500, "units": None}
        result = self.engine.calculate("cost_per_unit", ctx)
        assert result.is_none()

        # Both None
        ctx = {"total_cost": None, "units": None}
        result = self.engine.calculate("cost_per_unit", ctx)
        assert result.is_none()

    def test_cost_per_unit_zero_units_strict(self):
        """Test cost per unit with zero units in strict mode."""
        ctx = {"total_cost": 7500, "units": 0}
        with pytest.raises(
            CalculationError, match="cost_per_unit undefined for units == 0"
        ):
            self.strict_engine.calculate("cost_per_unit", ctx)

    def test_cost_per_unit_zero_units_safe(self):
        """Test cost per unit with zero units in safe mode."""
        ctx = {"total_cost": 7500, "units": 0}
        result = self.engine.calculate("cost_per_unit", ctx)
        assert result.is_none()

    def test_cost_per_unit_zero_cost(self):
        """Test cost per unit with zero cost."""
        ctx = {"total_cost": 0, "units": 250}
        result = self.engine.calculate("cost_per_unit", ctx)
        # 0 / 250 = 0
        assert result.as_decimal() == Decimal("0.0000")

    def test_cost_per_unit_negative_values(self):
        """Test cost per unit with negative values."""
        # Negative cost (e.g., cost savings/rebates)
        ctx = {"total_cost": -500, "units": 100}
        result = self.engine.calculate("cost_per_unit", ctx)
        assert result.as_decimal() == Decimal("-5.0000")

        # Negative units
        ctx = {"total_cost": 500, "units": -100}
        result = self.engine.calculate("cost_per_unit", ctx)
        assert result.as_decimal() == Decimal("-5.0000")

    def test_profit_per_unit_basic(self):
        """Test basic profit per unit calculation."""
        ctx = {"total_profit": 2500, "units_sold": 100}
        result = self.engine.calculate("profit_per_unit", ctx)
        # 2500 / 100 = 25
        assert result.as_decimal() == Decimal("25.0000")

    def test_profit_per_unit_with_none_values(self):
        """Test profit per unit with None inputs."""
        # None total_profit
        ctx = {"total_profit": None, "units_sold": 100}
        result = self.engine.calculate("profit_per_unit", ctx)
        assert result.is_none()

        # None units_sold
        ctx = {"total_profit": 2500, "units_sold": None}
        result = self.engine.calculate("profit_per_unit", ctx)
        assert result.is_none()

        # Both None
        ctx = {"total_profit": None, "units_sold": None}
        result = self.engine.calculate("profit_per_unit", ctx)
        assert result.is_none()

    def test_profit_per_unit_zero_units_strict(self):
        """Test profit per unit with zero units in strict mode."""
        ctx = {"total_profit": 2500, "units_sold": 0}
        with pytest.raises(
            CalculationError, match="profit_per_unit undefined for units_sold == 0"
        ):
            self.strict_engine.calculate("profit_per_unit", ctx)

    def test_profit_per_unit_zero_units_safe(self):
        """Test profit per unit with zero units in safe mode."""
        ctx = {"total_profit": 2500, "units_sold": 0}
        result = self.engine.calculate("profit_per_unit", ctx)
        assert result.is_none()

    def test_profit_per_unit_zero_profit(self):
        """Test profit per unit with zero profit (break-even)."""
        ctx = {"total_profit": 0, "units_sold": 100}
        result = self.engine.calculate("profit_per_unit", ctx)
        # 0 / 100 = 0
        assert result.as_decimal() == Decimal("0.0000")

    def test_profit_per_unit_negative_profit(self):
        """Test profit per unit with negative profit (loss)."""
        ctx = {"total_profit": -1000, "units_sold": 100}
        result = self.engine.calculate("profit_per_unit", ctx)
        # -1000 / 100 = -10 (loss per unit)
        assert result.as_decimal() == Decimal("-10.0000")

    def test_break_even_point_basic(self):
        """Test basic break-even point calculation."""
        ctx = {"fixed_costs": 10000, "price_per_unit": 50, "variable_cost_per_unit": 30}
        result = self.engine.calculate("break_even_point", ctx)
        # 10000 / (50 - 30) = 10000 / 20 = 500
        assert result.as_decimal() == Decimal("500.0000")

    def test_break_even_point_with_none_values(self):
        """Test break-even point with None inputs."""
        # None fixed_costs
        ctx = {"fixed_costs": None, "price_per_unit": 50, "variable_cost_per_unit": 30}
        result = self.engine.calculate("break_even_point", ctx)
        assert result.is_none()

        # None price_per_unit
        ctx = {
            "fixed_costs": 10000,
            "price_per_unit": None,
            "variable_cost_per_unit": 30,
        }
        result = self.engine.calculate("break_even_point", ctx)
        assert result.is_none()

        # None variable_cost_per_unit
        ctx = {
            "fixed_costs": 10000,
            "price_per_unit": 50,
            "variable_cost_per_unit": None,
        }
        result = self.engine.calculate("break_even_point", ctx)
        assert result.is_none()

        # All None
        ctx = {
            "fixed_costs": None,
            "price_per_unit": None,
            "variable_cost_per_unit": None,
        }
        result = self.engine.calculate("break_even_point", ctx)
        assert result.is_none()

    def test_break_even_point_zero_contribution_strict(self):
        """Test break-even point with zero contribution margin in strict mode."""
        # Price equals variable cost (zero contribution)
        ctx = {"fixed_costs": 10000, "price_per_unit": 30, "variable_cost_per_unit": 30}
        with pytest.raises(
            CalculationError,
            match="break_even_point undefined when price_per_unit - variable_cost_per_unit <= 0",
        ):
            self.strict_engine.calculate("break_even_point", ctx)

    def test_break_even_point_zero_contribution_safe(self):
        """Test break-even point with zero contribution margin in safe mode."""
        # Price equals variable cost (zero contribution)
        ctx = {"fixed_costs": 10000, "price_per_unit": 30, "variable_cost_per_unit": 30}
        result = self.engine.calculate("break_even_point", ctx)
        assert result.is_none()

    def test_break_even_point_negative_contribution_strict(self):
        """Test break-even point with negative contribution margin in strict mode."""
        # Variable cost higher than price
        ctx = {"fixed_costs": 10000, "price_per_unit": 25, "variable_cost_per_unit": 30}
        with pytest.raises(
            CalculationError,
            match="break_even_point undefined when price_per_unit - variable_cost_per_unit <= 0",
        ):
            self.strict_engine.calculate("break_even_point", ctx)

    def test_break_even_point_negative_contribution_safe(self):
        """Test break-even point with negative contribution margin in safe mode."""
        # Variable cost higher than price
        ctx = {"fixed_costs": 10000, "price_per_unit": 25, "variable_cost_per_unit": 30}
        result = self.engine.calculate("break_even_point", ctx)
        assert result.is_none()

    def test_break_even_point_zero_fixed_costs(self):
        """Test break-even point with zero fixed costs."""
        ctx = {"fixed_costs": 0, "price_per_unit": 50, "variable_cost_per_unit": 30}
        result = self.engine.calculate("break_even_point", ctx)
        # 0 / (50 - 30) = 0 (break-even immediately)
        assert result.as_decimal() == Decimal("0.0000")

    def test_break_even_point_negative_fixed_costs(self):
        """Test break-even point with negative fixed costs (subsidies)."""
        ctx = {"fixed_costs": -5000, "price_per_unit": 50, "variable_cost_per_unit": 30}
        result = self.engine.calculate("break_even_point", ctx)
        # -5000 / (50 - 30) = -5000 / 20 = -250 (profit from first unit)
        assert result.as_decimal() == Decimal("-250.0000")

    def test_break_even_point_fractional_result(self):
        """Test break-even point with fractional result."""
        ctx = {"fixed_costs": 10000, "price_per_unit": 33, "variable_cost_per_unit": 17}
        result = self.engine.calculate("break_even_point", ctx)
        # 10000 / (33 - 17) = 10000 / 16 = 625
        assert result.as_decimal() == Decimal("625.0000")

    def test_break_even_point_very_small_contribution(self):
        """Test break-even point with very small contribution margin."""
        ctx = {
            "fixed_costs": 1000,
            "price_per_unit": 10.01,
            "variable_cost_per_unit": 10.00,
        }
        result = self.engine.calculate("break_even_point", ctx)
        # 1000 / (10.01 - 10.00) = 1000 / 0.01 = 100000
        assert result.as_decimal() == Decimal("100000.0000")

    def test_break_even_point_large_contribution(self):
        """Test break-even point with large contribution margin."""
        ctx = {"fixed_costs": 1000, "price_per_unit": 100, "variable_cost_per_unit": 10}
        result = self.engine.calculate("break_even_point", ctx)
        # 1000 / (100 - 10) = 1000 / 90 ≈ 11.1111
        assert abs(result.as_decimal() - Decimal("11.1111")) < Decimal("0.0001")

    def test_unit_economics_with_fv_objects(self):
        """Test unit economics calculations with FV objects."""
        policy = Policy(decimal_places=2)
        total_revenue = FV(Decimal("5000"), policy=policy, unit=Money)
        units_sold = FV(Decimal("200"), policy=policy, unit=Dimensionless)

        ctx = {"total_revenue": total_revenue, "units_sold": units_sold}
        result = self.engine.calculate("revenue_per_unit", ctx)
        assert result.as_decimal() == Decimal("25.0000")

    def test_very_large_values(self):
        """Test calculations with very large values."""
        ctx = {"total_revenue": Decimal("1000000000"), "units_sold": Decimal("1000000")}
        result = self.engine.calculate("revenue_per_unit", ctx)
        # 1,000,000,000 / 1,000,000 = 1,000
        assert result.as_decimal() == Decimal("1000.0000")

    def test_very_small_values(self):
        """Test calculations with very small values."""
        ctx = {"total_cost": Decimal("0.0001"), "units": Decimal("0.0002")}
        result = self.engine.calculate("cost_per_unit", ctx)
        # 0.0001 / 0.0002 = 0.5
        assert result.as_decimal() == Decimal("0.5000")

    def test_break_even_dimensionless_result(self):
        """Test that break-even point returns Dimensionless unit."""
        ctx = {"fixed_costs": 1000, "price_per_unit": 50, "variable_cost_per_unit": 30}
        result = self.engine.calculate("break_even_point", ctx)

        # Verify the result has the correct unit type
        assert result.unit == Dimensionless
        assert result.as_decimal() == Decimal("50.0000")

    def test_policy_resolution_from_multiple_fvs(self):
        """Test that policy is correctly resolved from multiple FV inputs."""
        policy1 = Policy(decimal_places=2)
        policy2 = Policy(decimal_places=3)

        # First FV has policy, should be used
        fixed_costs = FV(1000, policy=policy1, unit=Money)
        price_per_unit = FV(Decimal("50"), unit=Money)  # No policy
        variable_cost_per_unit = FV(Decimal("30"), unit=Money)  # No policy

        ctx = {
            "fixed_costs": fixed_costs,
            "price_per_unit": price_per_unit,
            "variable_cost_per_unit": variable_cost_per_unit,
        }
        result = self.engine.calculate("break_even_point", ctx)

        # Should complete without errors
        assert result.as_decimal() == Decimal("50.0000")

    def test_contribution_calculation_edge_cases(self):
        """Test edge cases in contribution margin calculation within break-even."""
        # Test when contribution calculation results in None (edge case)
        policy = Policy(decimal_places=4)
        fixed_costs = FV(1000, policy=policy, unit=Money)
        price_per_unit = FV(None, policy=policy, unit=Money)  # None price
        variable_cost_per_unit = FV(Decimal("30"), policy=policy, unit=Money)

        ctx = {
            "fixed_costs": fixed_costs,
            "price_per_unit": price_per_unit,
            "variable_cost_per_unit": variable_cost_per_unit,
        }
        result = self.engine.calculate("break_even_point", ctx)
        assert result.is_none()

    def test_precision_with_recurring_decimals(self):
        """Test precision handling with calculations that produce recurring decimals."""
        ctx = {"fixed_costs": 1000, "price_per_unit": 37, "variable_cost_per_unit": 10}
        result = self.engine.calculate("break_even_point", ctx)
        # 1000 / (37 - 10) = 1000 / 27 ≈ 37.037037...
        assert abs(result.as_decimal() - Decimal("37.0370")) < Decimal("0.0001")

    def test_negative_break_even_scenarios(self):
        """Test various negative break-even scenarios."""
        # Negative fixed costs with positive contribution
        ctx = {"fixed_costs": -2000, "price_per_unit": 60, "variable_cost_per_unit": 40}
        result = self.engine.calculate("break_even_point", ctx)
        # -2000 / (60 - 40) = -2000 / 20 = -100
        assert result.as_decimal() == Decimal("-100.0000")

    def test_unit_economics_consistency(self):
        """Test consistency between related unit economics calculations."""
        # Calculate revenue per unit and cost per unit, then verify they work together
        revenue_ctx = {"total_revenue": 10000, "units_sold": 200}
        cost_ctx = {"total_cost": 6000, "units": 200}

        revenue_per_unit = self.engine.calculate("revenue_per_unit", revenue_ctx)
        cost_per_unit = self.engine.calculate("cost_per_unit", cost_ctx)

        # Revenue per unit should be 50, cost per unit should be 30
        assert revenue_per_unit.as_decimal() == Decimal("50.0000")
        assert cost_per_unit.as_decimal() == Decimal("30.0000")

        # Profit per unit should be the difference: 20
        profit_ctx = {"total_profit": 4000, "units_sold": 200}  # 10000 - 6000 = 4000
        profit_per_unit = self.engine.calculate("profit_per_unit", profit_ctx)
        assert profit_per_unit.as_decimal() == Decimal("20.0000")
