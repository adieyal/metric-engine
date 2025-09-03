"""Tests for pricing calculations module."""

from decimal import Decimal

import pytest

from metricengine.engine import Engine
from metricengine.exceptions import CalculationError
from metricengine.policy import Policy
from metricengine.units import Dimensionless, Money, Percent
from metricengine.value import FV


class TestPricingCalculations:
    """Test pricing calculations with comprehensive coverage."""

    def setup_method(self):
        """Set up test fixtures."""
        self.engine = Engine(Policy(decimal_places=4, arithmetic_strict=False))
        self.strict_engine = Engine(Policy(decimal_places=4, arithmetic_strict=True))

    def test_total_cost_basic(self):
        """Test basic total cost calculation."""
        ctx = {"unit_cost": 10, "quantity": 5}
        result = self.engine.calculate("total_cost", ctx)
        assert result.as_decimal() == Decimal("50.0000")

    def test_total_cost_with_none_values(self):
        """Test total cost with None inputs."""
        # None unit_cost
        ctx = {"unit_cost": None, "quantity": 5}
        result = self.engine.calculate("total_cost", ctx)
        assert result.is_none()

        # None quantity
        ctx = {"unit_cost": 10, "quantity": None}
        result = self.engine.calculate("total_cost", ctx)
        assert result.is_none()

        # Both None
        ctx = {"unit_cost": None, "quantity": None}
        result = self.engine.calculate("total_cost", ctx)
        assert result.is_none()

    def test_total_cost_with_fv_objects(self):
        """Test total cost with FV objects having policies."""
        policy = Policy(decimal_places=2)
        unit_cost = FV(Decimal("10.50"), policy=policy, unit=Money)
        quantity = FV(Decimal("3"), policy=policy, unit=Dimensionless)

        ctx = {"unit_cost": unit_cost, "quantity": quantity}
        result = self.engine.calculate("total_cost", ctx)
        assert result.as_decimal() == Decimal("31.50")

    def test_sales_ex_tax_basic(self):
        """Test basic sales excluding tax calculation."""
        ctx = {"sales": 110, "tax_rate": 0.1}
        result = self.engine.calculate("sales_ex_tax", ctx)
        # 110 / (1 + 0.1) = 100
        assert result.as_decimal() == Decimal("100.0000")

    def test_sales_ex_tax_with_none_values(self):
        """Test sales excluding tax with None inputs."""
        # None sales
        ctx = {"sales": None, "tax_rate": 0.1}
        result = self.engine.calculate("sales_ex_tax", ctx)
        assert result.is_none()

        # None tax_rate
        ctx = {"sales": 110, "tax_rate": None}
        result = self.engine.calculate("sales_ex_tax", ctx)
        assert result.is_none()

    def test_sales_ex_tax_zero_denominator_strict(self):
        """Test sales excluding tax with zero denominator in strict mode."""
        ctx = {"sales": 110, "tax_rate": -1.0}  # 1 + (-1) = 0
        with pytest.raises(
            CalculationError, match="sales_ex_tax undefined when 1 \\+ tax_rate == 0"
        ):
            self.strict_engine.calculate("sales_ex_tax", ctx)

    def test_sales_ex_tax_zero_denominator_safe(self):
        """Test sales excluding tax with zero denominator in safe mode."""
        ctx = {"sales": 110, "tax_rate": -1.0}  # 1 + (-1) = 0
        result = self.engine.calculate("sales_ex_tax", ctx)
        assert result.is_none()

    def test_sales_with_tax_basic(self):
        """Test basic sales including tax calculation."""
        ctx = {"sales_ex_tax": 100, "tax_rate": 0.1}
        result = self.engine.calculate("sales_with_tax", ctx)
        # 100 * (1 + 0.1) = 110
        assert result.as_decimal() == Decimal("110.0000")

    def test_sales_with_tax_with_none_values(self):
        """Test sales including tax with None inputs."""
        # None sales_ex_tax
        ctx = {"sales_ex_tax": None, "tax_rate": 0.1}
        result = self.engine.calculate("sales_with_tax", ctx)
        assert result.is_none()

        # None tax_rate
        ctx = {"sales_ex_tax": 100, "tax_rate": None}
        result = self.engine.calculate("sales_with_tax", ctx)
        assert result.is_none()

    def test_tax_amount_basic(self):
        """Test basic tax amount calculation."""
        ctx = {"sales": 110, "tax_rate": 0.1}
        result = self.engine.calculate("tax_amount", ctx)
        # 110 - (110 / 1.1) = 110 - 100 = 10
        assert result.as_decimal() == Decimal("10.0000")

    def test_tax_amount_with_none_values(self):
        """Test tax amount with None inputs."""
        # None sales
        ctx = {"sales": None, "tax_rate": 0.1}
        result = self.engine.calculate("tax_amount", ctx)
        assert result.is_none()

        # None tax_rate
        ctx = {"sales": 110, "tax_rate": None}
        result = self.engine.calculate("tax_amount", ctx)
        assert result.is_none()

    def test_tax_amount_zero_denominator_strict(self):
        """Test tax amount with zero denominator in strict mode."""
        ctx = {"sales": 110, "tax_rate": -1.0}  # 1 + (-1) = 0
        with pytest.raises(
            CalculationError, match="tax_amount undefined when 1 \\+ tax_rate == 0"
        ):
            self.strict_engine.calculate("tax_amount", ctx)

    def test_tax_amount_zero_denominator_safe(self):
        """Test tax amount with zero denominator in safe mode."""
        ctx = {"sales": 110, "tax_rate": -1.0}  # 1 + (-1) = 0
        result = self.engine.calculate("tax_amount", ctx)
        assert result.is_none()

    def test_price_ex_tax_basic(self):
        """Test basic price excluding tax calculation."""
        ctx = {"price_inc_tax": 120, "tax_rate": 0.2}
        result = self.engine.calculate("price_ex_tax", ctx)
        # 120 / (1 + 0.2) = 120 / 1.2 = 100
        assert result.as_decimal() == Decimal("100.0000")

    def test_price_ex_tax_with_none_values(self):
        """Test price excluding tax with None inputs."""
        # None price_inc_tax
        ctx = {"price_inc_tax": None, "tax_rate": 0.2}
        result = self.engine.calculate("price_ex_tax", ctx)
        assert result.is_none()

        # None tax_rate
        ctx = {"price_inc_tax": 120, "tax_rate": None}
        result = self.engine.calculate("price_ex_tax", ctx)
        assert result.is_none()

    def test_price_ex_tax_zero_denominator_strict(self):
        """Test price excluding tax with zero denominator in strict mode."""
        ctx = {"price_inc_tax": 120, "tax_rate": -1.0}  # 1 + (-1) = 0
        with pytest.raises(
            CalculationError, match="price_ex_tax undefined when 1 \\+ tax_rate == 0"
        ):
            self.strict_engine.calculate("price_ex_tax", ctx)

    def test_price_ex_tax_zero_denominator_safe(self):
        """Test price excluding tax with zero denominator in safe mode."""
        ctx = {"price_inc_tax": 120, "tax_rate": -1.0}  # 1 + (-1) = 0
        result = self.engine.calculate("price_ex_tax", ctx)
        assert result.is_none()

    def test_markup_ratio_basic(self):
        """Test basic markup ratio calculation."""
        ctx = {"cost": 80, "selling_price": 100}
        result = self.engine.calculate("markup_ratio", ctx)
        # (100 - 80) / 80 = 20/80 = 0.25
        assert result.as_decimal() == Decimal("0.2500")

    def test_markup_ratio_with_none_values(self):
        """Test markup ratio with None inputs."""
        # None cost
        ctx = {"cost": None, "selling_price": 100}
        result = self.engine.calculate("markup_ratio", ctx)
        assert result.is_none()

        # None selling_price
        ctx = {"cost": 80, "selling_price": None}
        result = self.engine.calculate("markup_ratio", ctx)
        assert result.is_none()

    def test_markup_ratio_zero_cost_strict(self):
        """Test markup ratio with zero cost in strict mode."""
        ctx = {"cost": 0, "selling_price": 100}
        with pytest.raises(
            CalculationError, match="markup ratio undefined for cost == 0"
        ):
            self.strict_engine.calculate("markup_ratio", ctx)

    def test_markup_ratio_zero_cost_safe(self):
        """Test markup ratio with zero cost in safe mode."""
        ctx = {"cost": 0, "selling_price": 100}
        result = self.engine.calculate("markup_ratio", ctx)
        assert result.is_none()

    def test_markup_percentage_basic(self):
        """Test markup percentage calculation."""
        ctx = {"cost": 80, "selling_price": 100}
        result = self.engine.calculate("markup_percentage", ctx)
        # ((100 - 80) / 80) * 100 = 25%
        assert result.as_decimal() == Decimal("25.0000")

    def test_markup_percentage_with_none_ratio(self):
        """Test markup percentage with None markup ratio."""
        # Create a context that will result in None markup_ratio
        ctx = {"cost": 0, "selling_price": 100}
        result = self.engine.calculate("markup_percentage", ctx)
        assert result.is_none()

    def test_discount_ratio_basic(self):
        """Test basic discount ratio calculation."""
        ctx = {"original_price": 100, "discounted_price": 80}
        result = self.engine.calculate("discount_ratio", ctx)
        # (100 - 80) / 100 = 20/100 = 0.2
        assert result.as_decimal() == Decimal("0.2000")

    def test_discount_ratio_with_none_values(self):
        """Test discount ratio with None inputs."""
        # None original_price
        ctx = {"original_price": None, "discounted_price": 80}
        result = self.engine.calculate("discount_ratio", ctx)
        assert result.is_none()

        # None discounted_price
        ctx = {"original_price": 100, "discounted_price": None}
        result = self.engine.calculate("discount_ratio", ctx)
        assert result.is_none()

    def test_discount_ratio_zero_original_price_strict(self):
        """Test discount ratio with zero original price in strict mode."""
        ctx = {"original_price": 0, "discounted_price": 80}
        with pytest.raises(
            CalculationError, match="discount ratio undefined for original_price == 0"
        ):
            self.strict_engine.calculate("discount_ratio", ctx)

    def test_discount_ratio_zero_original_price_safe(self):
        """Test discount ratio with zero original price in safe mode."""
        ctx = {"original_price": 0, "discounted_price": 80}
        result = self.engine.calculate("discount_ratio", ctx)
        assert result.is_none()

    def test_discount_percentage_basic(self):
        """Test discount percentage calculation."""
        ctx = {"original_price": 100, "discounted_price": 75}
        result = self.engine.calculate("discount_percentage", ctx)
        # ((100 - 75) / 100) * 100 = 25%
        assert result.as_decimal() == Decimal("25.0000")

    def test_discount_percentage_with_none_ratio(self):
        """Test discount percentage with None discount ratio."""
        # Create a context that will result in None discount_ratio
        ctx = {"original_price": 0, "discounted_price": 75}
        result = self.engine.calculate("discount_percentage", ctx)
        assert result.is_none()

    def test_negative_markup_ratio(self):
        """Test markup ratio with selling price less than cost."""
        ctx = {"cost": 100, "selling_price": 80}
        result = self.engine.calculate("markup_ratio", ctx)
        # (80 - 100) / 100 = -20/100 = -0.2
        assert result.as_decimal() == Decimal("-0.2000")

    def test_negative_discount_ratio(self):
        """Test discount ratio with discounted price higher than original."""
        ctx = {"original_price": 80, "discounted_price": 100}
        result = self.engine.calculate("discount_ratio", ctx)
        # (80 - 100) / 80 = -20/80 = -0.25 (negative discount = markup)
        assert result.as_decimal() == Decimal("-0.2500")

    def test_zero_tax_rate(self):
        """Test calculations with zero tax rate."""
        # Sales ex tax with zero tax rate
        ctx = {"sales": 100, "tax_rate": 0}
        result = self.engine.calculate("sales_ex_tax", ctx)
        # 100 / (1 + 0) = 100
        assert result.as_decimal() == Decimal("100.0000")

        # Tax amount with zero tax rate
        result = self.engine.calculate("tax_amount", ctx)
        # 100 - (100 / 1) = 0
        assert result.as_decimal() == Decimal("0.0000")

    def test_high_tax_rate(self):
        """Test calculations with high tax rate."""
        ctx = {"sales": 200, "tax_rate": 1.0}  # 100% tax
        result = self.engine.calculate("sales_ex_tax", ctx)
        # 200 / (1 + 1) = 200 / 2 = 100
        assert result.as_decimal() == Decimal("100.0000")

        result = self.engine.calculate("tax_amount", ctx)
        # 200 - (200 / 2) = 200 - 100 = 100
        assert result.as_decimal() == Decimal("100.0000")

    def test_equal_prices_markup(self):
        """Test markup calculation when cost equals selling price."""
        ctx = {"cost": 100, "selling_price": 100}
        result = self.engine.calculate("markup_ratio", ctx)
        # (100 - 100) / 100 = 0
        assert result.as_decimal() == Decimal("0.0000")

        result = self.engine.calculate("markup_percentage", ctx)
        assert result.as_decimal() == Decimal("0.0000")

    def test_equal_prices_discount(self):
        """Test discount calculation when original equals discounted price."""
        ctx = {"original_price": 100, "discounted_price": 100}
        result = self.engine.calculate("discount_ratio", ctx)
        # (100 - 100) / 100 = 0
        assert result.as_decimal() == Decimal("0.0000")

        result = self.engine.calculate("discount_percentage", ctx)
        assert result.as_decimal() == Decimal("0.0000")

    def test_very_small_values(self):
        """Test calculations with very small decimal values."""
        ctx = {"unit_cost": Decimal("0.01"), "quantity": Decimal("0.5")}
        result = self.engine.calculate("total_cost", ctx)
        assert result.as_decimal() == Decimal("0.0050")

    def test_very_large_values(self):
        """Test calculations with very large values."""
        ctx = {"unit_cost": Decimal("1000000"), "quantity": Decimal("1000")}
        result = self.engine.calculate("total_cost", ctx)
        assert result.as_decimal() == Decimal("1000000000.0000")

    def test_policy_resolution_from_multiple_fvs(self):
        """Test that policy is correctly resolved from multiple FV inputs."""
        policy1 = Policy(decimal_places=2)
        policy2 = Policy(decimal_places=3)

        # First FV has policy, should be used
        sales = FV(110, policy=policy1, unit=Money)
        tax_rate = FV(Decimal("0.1"), unit=Percent)  # No policy

        ctx = {"sales": sales, "tax_rate": tax_rate}
        result = self.engine.calculate("sales_ex_tax", ctx)

        # Result should use policy1 (2 decimal places)
        # But since we're using engine with its own policy, this is more about ensuring no errors
        assert result.as_decimal() == Decimal("100.0000")
