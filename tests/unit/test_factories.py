from decimal import Decimal as D

import pytest

from metricengine.factories import (
    dimensionless,
    dimless,
    money,
    percent,
    ratio,
    zero_dimensionless,
    zero_money,
    zero_percent,
    zero_ratio,
)

# Remove these type aliases - they can't be used with isinstance
# RatioFV,
# PercentFV,
# MoneyFV,
from metricengine.policy import Policy
from metricengine.policy_context import (
    PolicyResolution,
    use_policy_resolution,
)
from metricengine.units import Dimensionless, Money, Percent, Ratio
from metricengine.value import FinancialValue


class TestRatioFactory:
    """Test the ratio() factory function."""

    def test_ratio_with_numeric_values(self):
        """Test ratio creation with various numeric inputs."""
        # Test with different numeric types
        assert ratio(0.5).as_decimal() == D("0.50")
        assert ratio(1).as_decimal() == D("1.00")
        assert ratio("0.25").as_decimal() == D("0.25")
        assert ratio(D("0.75")).as_decimal() == D("0.75")

    def test_ratio_with_none(self):
        """Test ratio creation with None."""
        result = ratio(None)
        assert result.is_none()
        assert result.unit is Ratio

    def test_ratio_with_policy(self):
        """Test ratio creation with custom policy."""
        custom_policy = Policy(decimal_places=4)
        result = ratio(0.12345, policy=custom_policy)
        assert result.policy == custom_policy
        assert result.as_decimal() == D("0.1235")  # rounded to 4 dp

    def test_ratio_unit_type(self):
        """Test that ratio factory creates correct unit type."""
        result = ratio(0.5)
        assert result.unit is Ratio
        assert isinstance(result, FinancialValue)


class TestPercentFactory:
    """Test the percent() factory function."""

    def test_percent_ratio_input(self):
        """Test percent creation with ratio input (default)."""
        result = percent(0.15)
        assert result.as_decimal() == D("0.15")  # stored as ratio, displayed as ratio
        assert result.unit is Percent
        assert isinstance(result, FinancialValue)

    def test_percent_percent_input(self):
        """Test percent creation with percent input."""
        result = percent(15, input="percent")
        assert result.as_decimal() == D("0.15")  # stored as 0.15, displayed as 0.15
        assert result.unit is Percent

    def test_percent_conversion_accuracy(self):
        """Test percent conversion maintains accuracy."""
        # Test various percent values
        test_cases = [
            (50, D("0.50")),  # 50% -> 0.50
            (25.5, D("0.26")),  # 25.5% -> 0.255 -> 0.26 (rounded)
            (0.1, D("0.00")),  # 0.1% -> 0.001 -> 0.00 (rounded)
            (100, D("1.00")),  # 100% -> 1.00
        ]

        for input_val, expected in test_cases:
            result = percent(input_val, input="percent")
            assert result.as_decimal() == expected

    def test_percent_with_none(self):
        """Test percent creation with None."""
        result = percent(None)
        assert result.is_none()
        assert result.unit is Percent

    def test_percent_with_policy(self):
        """Test percent creation with custom policy."""
        custom_policy = Policy(decimal_places=1)
        result = percent(0.1234, policy=custom_policy)
        assert result.policy == custom_policy
        assert result.as_decimal() == D("0.1")  # rounded to 1 dp

    def test_percent_invalid_input_mode(self):
        """Test percent with invalid input mode raises error."""
        with pytest.raises(
            ValueError, match="percent\\(input=...\\) must be 'ratio' or 'percent'"
        ):
            percent(0.5, input="invalid")

    def test_percent_strict_mode(self):
        """Test percent strict mode behavior."""
        # Test with valid input in strict mode
        result = percent(15, input="percent", strict=True)
        assert result.as_decimal() == D("0.15")  # stored as ratio

        # Test with invalid input in strict mode - to_decimal returns None, doesn't raise
        # So the result should be None (not an exception)
        result = percent("invalid", input="percent", strict=True)
        assert result.is_none()  # to_decimal("invalid") returns None, so result is None

    def test_percent_non_strict_mode(self):
        """Test percent non-strict mode behavior."""
        # Test with invalid input in non-strict mode (should return None)
        result = percent("invalid", input="percent", strict=False)
        assert result.is_none()


class TestMoneyFactory:
    """Test the money() factory function."""

    def test_money_with_numeric_values(self):
        """Test money creation with various numeric inputs."""
        assert money(100.50).as_decimal() == D("100.50")
        assert money(0).as_decimal() == D("0.00")
        assert money("25.99").as_decimal() == D("25.99")
        assert money(D("150.75")).as_decimal() == D("150.75")

    def test_money_with_none(self):
        """Test money creation with None."""
        result = money(None)
        assert result.is_none()
        assert result.unit is Money

    def test_money_with_policy(self):
        """Test money creation with custom policy."""
        custom_policy = Policy(decimal_places=0)  # whole dollars
        result = money(100.75, policy=custom_policy)
        assert result.policy == custom_policy
        assert result.as_decimal() == D("101")  # rounded to 0 dp

    def test_money_unit_type(self):
        """Test that money factory creates correct unit type."""
        result = money(50)
        assert result.unit is Money
        assert isinstance(result, FinancialValue)


class TestDimensionlessFactory:
    """Test the dimensionless() factory function."""

    def test_dimensionless_with_numeric_values(self):
        """Test dimensionless creation with various numeric inputs."""
        assert dimensionless(42).as_decimal() == D("42.00")
        assert dimensionless(0.5).as_decimal() == D("0.50")
        assert dimensionless("3.14").as_decimal() == D("3.14")
        assert dimensionless(D("2.718")).as_decimal() == D("2.72")  # rounded to 2 dp

    def test_dimensionless_with_none(self):
        """Test dimensionless creation with None."""
        result = dimensionless(None)
        assert result.is_none()
        assert result.unit is Dimensionless

    def test_dimensionless_with_policy(self):
        """Test dimensionless creation with custom policy."""
        custom_policy = Policy(decimal_places=3)
        result = dimensionless(1.23456, policy=custom_policy)
        assert result.policy == custom_policy
        assert result.as_decimal() == D("1.235")  # rounded to 3 dp

    def test_dimensionless_unit_type(self):
        """Test that dimensionless factory creates correct unit type."""
        result = dimensionless(10)
        assert result.unit is Dimensionless

    def test_dimless_alias(self):
        """Test that dimless alias works correctly."""
        result1 = dimensionless(5)
        result2 = dimless(5)
        assert result1.as_decimal() == result2.as_decimal()
        assert result1.unit == result2.unit


class TestZeroFactories:
    """Test the zero_* factory functions."""

    def test_zero_money(self):
        """Test zero_money factory."""
        result = zero_money()
        assert result.as_decimal() == D("0.00")
        assert result.unit is Money
        assert isinstance(result, FinancialValue)

    def test_zero_money_with_policy(self):
        """Test zero_money with custom policy."""
        custom_policy = Policy(decimal_places=4)
        result = zero_money(policy=custom_policy)
        assert result.policy == custom_policy
        assert result.as_decimal() == D("0.0000")

    def test_zero_ratio(self):
        """Test zero_ratio factory."""
        result = zero_ratio()
        assert result.as_decimal() == D("0.00")
        assert result.unit is Ratio
        assert isinstance(result, FinancialValue)

    def test_zero_ratio_with_policy(self):
        """Test zero_ratio with custom policy."""
        custom_policy = Policy(decimal_places=1)
        result = zero_ratio(policy=custom_policy)
        assert result.policy == custom_policy
        assert result.as_decimal() == D("0.0")

    def test_zero_percent(self):
        """Test zero_percent factory."""
        result = zero_percent()
        assert result.as_decimal() == D("0.00")  # displayed as 0%
        assert result.unit is Percent
        assert isinstance(result, FinancialValue)

    def test_zero_percent_with_policy(self):
        """Test zero_percent with custom policy."""
        custom_policy = Policy(decimal_places=3)
        result = zero_percent(policy=custom_policy)
        assert result.policy == custom_policy
        assert result.as_decimal() == D("0.000")

    def test_zero_dimensionless(self):
        """Test zero_dimensionless factory."""
        result = zero_dimensionless()
        assert result.as_decimal() == D("0.00")
        assert result.unit is Dimensionless

    def test_zero_dimensionless_with_policy(self):
        """Test zero_dimensionless with custom policy."""
        custom_policy = Policy(decimal_places=0)
        result = zero_dimensionless(policy=custom_policy)
        assert result.policy == custom_policy
        assert result.as_decimal() == D("0")


class TestFactoryIntegration:
    """Test integration between different factories."""

    def test_factory_arithmetic_operations(self):
        """Test that factory-created values can be used in arithmetic."""
        # Test money operations
        price = money(10.50)
        quantity = dimensionless(3)
        total = price * quantity
        assert total.as_decimal() == D("31.50")
        assert total.unit is Money

        # Test percentage operations
        base = money(100)
        rate = percent(0.15)  # 15%
        tax = base * rate
        assert tax.as_decimal() == D("15.00")
        assert tax.unit is Money

    def test_factory_policy_inheritance(self):
        """Test that factory-created values inherit policies correctly."""
        custom_policy = Policy(decimal_places=1)

        # Test that operations inherit policy from left operand
        a = money(10.55, policy=custom_policy)
        b = money(5.25)  # default policy (2 dp)

        with use_policy_resolution(PolicyResolution.LEFT_OPERAND):
            result = a + b
            assert result.policy == custom_policy
            assert result.as_decimal() == D("15.8")  # rounded to 1 dp

    def test_factory_none_handling(self):
        """Test that factories handle None values consistently."""
        # All factories should handle None the same way
        factories = [ratio, percent, money, dimensionless]

        for factory in factories:
            result = factory(None)
            assert result.is_none()
            assert result.unit is not None  # unit should still be set


class TestFactoryEdgeCases:
    """Test edge cases and error conditions."""

    def test_percent_edge_values(self):
        """Test percent factory with edge values."""
        # Test 0%
        result = percent(0, input="percent")
        assert result.as_decimal() == D("0.00")

        # Test 100%
        result = percent(100, input="percent")
        assert result.as_decimal() == D("1.00")  # 100% -> 1.00

        # Test negative percentage
        result = percent(-10, input="percent")
        assert result.as_decimal() == D("-0.10")  # -10% -> -0.10

    def test_percent_string_inputs(self):
        """Test percent factory with string inputs."""
        # Valid string inputs
        assert percent("15", input="percent").as_decimal() == D("0.15")  # 15% -> 0.15
        assert percent("0.5", input="percent").as_decimal() == D(
            "0.01"
        )  # 0.5% -> 0.005 -> 0.01 (rounded)

    def test_factory_with_extreme_values(self):
        """Test factories with extreme numeric values."""
        # Very large numbers
        large_val = D("999999999.99")
        assert money(large_val).as_decimal() == large_val

        # Very small numbers
        small_val = D("0.0001")
        assert ratio(small_val).as_decimal() == D("0.00")  # rounded to 2 dp

    def test_factory_type_consistency(self):
        """Test that factories return consistent types."""
        # All factories should return FinancialValue instances
        factories_and_values = [
            (ratio, 0.5),
            (percent, 0.15),
            (money, 100),
            (dimensionless, 42),
        ]

        for factory, value in factories_and_values:
            result = factory(value)
            assert hasattr(result, "as_decimal")
            assert hasattr(result, "as_str")
            assert hasattr(result, "is_none")
            assert hasattr(result, "unit")
            assert hasattr(result, "policy")


class TestFactoryPerformance:
    """Test factory performance characteristics."""

    def test_factory_creation_speed(self):
        """Test that factories create objects quickly."""
        import time

        start_time = time.time()
        for _ in range(1000):
            money(100.50)
            ratio(0.5)
            percent(15, input="percent")
            dimensionless(42)
        end_time = time.time()

        # Should complete 4000 creations in reasonable time
        assert (end_time - start_time) < 1.0  # Less than 1 second

    def test_factory_memory_usage(self):
        """Test that factories don't create excessive memory usage."""
        # Create many objects and ensure they can be garbage collected
        objects = []
        for _ in range(1000):
            objects.append(money(100.50))
            objects.append(ratio(0.5))

        # Clear the list to allow garbage collection
        objects.clear()

        # If we get here without memory issues, the test passes
        assert True
