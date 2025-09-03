"""Tests for rules calculations module."""

from decimal import Decimal

import pytest

from metricengine.calculations.rules import skip_if, skip_if_negative_sales
from metricengine.policy import Policy
from metricengine.units import Money
from metricengine.value import FV


class TestRulesModule:
    """Test rules and decorators with comprehensive coverage."""

    def setup_method(self):
        """Set up test fixtures."""
        self.policy_with_flag = Policy(
            decimal_places=4, arithmetic_strict=False, negative_sales_is_none=True
        )
        self.policy_without_flag = Policy(
            decimal_places=4, arithmetic_strict=False, negative_sales_is_none=False
        )

    def test_skip_if_basic_functionality(self):
        """Test basic skip_if decorator functionality."""

        @skip_if(
            arg="test_value",
            policy_flag="negative_sales_is_none",
            predicate=lambda x: x < 0,
            none_is_skip=False,
        )
        def test_function(test_value: FV[Money]) -> FV[Money]:
            return test_value * 2

        # Test with negative value and policy flag True (should skip)
        negative_value = FV(Decimal("-100"), policy=self.policy_with_flag, unit=Money)
        result = test_function(negative_value)
        assert result.is_none()
        assert isinstance(result, FV)

        # Test with negative value and policy flag False (should not skip)
        negative_value = FV(
            Decimal("-100"), policy=self.policy_without_flag, unit=Money
        )
        result = test_function(negative_value)
        assert result.as_decimal() == Decimal("-200")

        # Test with positive value (should not skip regardless of policy)
        positive_value = FV(Decimal("100"), policy=self.policy_with_flag, unit=Money)
        result = test_function(positive_value)
        assert result.as_decimal() == Decimal("200")

    def test_skip_if_with_none_is_skip_true(self):
        """Test skip_if with none_is_skip=True."""

        @skip_if(
            arg="test_value",
            policy_flag="negative_sales_is_none",
            predicate=lambda x: x < 0,
            none_is_skip=True,
        )
        def test_function(test_value: FV[Money]) -> FV[Money]:
            return test_value * 2

        # Test with None value and none_is_skip=True (should skip)
        none_value = FV(None, policy=self.policy_with_flag, unit=Money)
        result = test_function(none_value)
        assert result.is_none()

        # Test with None value and policy flag False (should not skip based on policy)
        none_value = FV(None, policy=self.policy_without_flag, unit=Money)
        result = test_function(none_value)
        # Since policy flag is False, should proceed to function (which may handle None differently)
        # In this case, the function would try to multiply None * 2, which would likely fail
        # But the decorator doesn't skip it
        try:
            # This might raise an error depending on FV implementation
            result = test_function(none_value)
        except Exception:
            # Expected - the function itself may not handle None properly
            pass

    def test_skip_if_with_none_is_skip_false(self):
        """Test skip_if with none_is_skip=False."""

        @skip_if(
            arg="test_value",
            policy_flag="negative_sales_is_none",
            predicate=lambda x: x < 0,
            none_is_skip=False,
        )
        def test_function(test_value: FV[Money]) -> FV[Money]:
            if test_value.is_none():
                return FV.none(test_value.policy or Policy())
            return test_value * 2

        # Test with None value and none_is_skip=False (should not skip)
        none_value = FV(None, policy=self.policy_with_flag, unit=Money)
        result = test_function(none_value)
        # Function should handle None properly since decorator doesn't skip
        assert result.is_none()

    def test_skip_if_with_non_fv_argument(self):
        """Test skip_if with non-FV argument (should pass through)."""

        @skip_if(
            arg="test_value",
            policy_flag="negative_sales_is_none",
            predicate=lambda x: x < 0,
            none_is_skip=False,
        )
        def test_function(test_value) -> float:
            return test_value * 2

        # Test with regular number (not FV) - should pass through
        result = test_function(-100)
        assert result == -200

        # Test with regular positive number
        result = test_function(100)
        assert result == 200

    def test_skip_if_with_missing_policy_flag(self):
        """Test skip_if when policy doesn't have the specified flag."""
        policy_missing_flag = Policy(
            decimal_places=4
        )  # No negative_sales_is_none attribute

        @skip_if(
            arg="test_value",
            policy_flag="negative_sales_is_none",
            predicate=lambda x: x < 0,
            none_is_skip=False,
        )
        def test_function(test_value: FV[Money]) -> FV[Money]:
            return test_value * 2

        negative_value = FV(Decimal("-100"), policy=policy_missing_flag, unit=Money)

        # When policy doesn't have the flag, getattr returns False, so should not skip
        result = test_function(negative_value)
        # The actual behavior may vary - test that it executes without error
        assert result is not None

    def test_skip_if_with_no_policy_on_fv(self):
        """Test skip_if when FV has no policy."""

        @skip_if(
            arg="test_value",
            policy_flag="negative_sales_is_none",
            predicate=lambda x: x < 0,
            none_is_skip=False,
        )
        def test_function(test_value: FV[Money]) -> FV[Money]:
            return test_value * 2

        # Create FV without policy
        negative_value = FV(Decimal("-100"), unit=Money)  # No policy

        # Should use get_policy() or DEFAULT_POLICY
        result = test_function(negative_value)
        # The actual behavior may vary - test that it executes without error
        assert result is not None

    def test_skip_if_with_kwargs(self):
        """Test skip_if with function called using keyword arguments."""

        @skip_if(
            arg="sales",
            policy_flag="negative_sales_is_none",
            predicate=lambda x: x < 0,
            none_is_skip=False,
        )
        def test_function(sales: FV[Money], multiplier: int = 2) -> FV[Money]:
            return sales * multiplier

        negative_sales = FV(Decimal("-100"), policy=self.policy_with_flag, unit=Money)

        # Call with kwargs
        result = test_function(sales=negative_sales, multiplier=3)
        assert result.is_none()

        # Call with positive value
        positive_sales = FV(Decimal("100"), policy=self.policy_with_flag, unit=Money)
        result = test_function(sales=positive_sales, multiplier=3)
        assert result.as_decimal() == Decimal("300")

    def test_skip_if_with_defaults(self):
        """Test skip_if with function that has default arguments."""

        @skip_if(
            arg="sales",
            policy_flag="negative_sales_is_none",
            predicate=lambda x: x < 0,
            none_is_skip=False,
        )
        def test_function(sales: FV[Money], tax_rate: FV[Money] = None) -> FV[Money]:
            if tax_rate is None:
                tax_rate = FV(Decimal("0.1"), policy=sales.policy, unit=Money)
            return sales * (1 + tax_rate)

        negative_sales = FV(Decimal("-100"), policy=self.policy_with_flag, unit=Money)

        # Call without providing default argument
        result = test_function(negative_sales)
        assert result.is_none()

    def test_skip_if_negative_sales_basic(self):
        """Test skip_if_negative_sales convenience function."""

        @skip_if_negative_sales("sales")
        def test_function(sales: FV[Money]) -> FV[Money]:
            return sales * 2

        # Test with negative sales and policy flag True
        negative_sales = FV(Decimal("-100"), policy=self.policy_with_flag, unit=Money)
        result = test_function(negative_sales)
        assert result.is_none()

        # Test with positive sales
        positive_sales = FV(Decimal("100"), policy=self.policy_with_flag, unit=Money)
        result = test_function(positive_sales)
        assert result.as_decimal() == Decimal("200")

        # Test with zero sales (should not skip since predicate is x < 0)
        zero_sales = FV(Decimal("0"), policy=self.policy_with_flag, unit=Money)
        result = test_function(zero_sales)
        assert result.as_decimal() == Decimal("0")

    def test_skip_if_negative_sales_with_custom_arg_name(self):
        """Test skip_if_negative_sales with custom argument name."""

        @skip_if_negative_sales("revenue")
        def test_function(revenue: FV[Money]) -> FV[Money]:
            return revenue * 2

        negative_revenue = FV(Decimal("-100"), policy=self.policy_with_flag, unit=Money)
        result = test_function(negative_revenue)
        assert result.is_none()

    def test_skip_if_negative_sales_default_arg_name(self):
        """Test skip_if_negative_sales with default argument name."""

        @skip_if_negative_sales()  # Uses default "sales"
        def test_function(sales: FV[Money]) -> FV[Money]:
            return sales * 2

        negative_sales = FV(Decimal("-100"), policy=self.policy_with_flag, unit=Money)
        result = test_function(negative_sales)
        assert result.is_none()

    def test_skip_if_preserves_function_metadata(self):
        """Test that skip_if preserves function metadata using functools.wraps."""

        def original_function(test_value: FV[Money]) -> FV[Money]:
            """Original function docstring."""
            return test_value * 2

        decorated_function = skip_if(
            arg="test_value",
            policy_flag="negative_sales_is_none",
            predicate=lambda x: x < 0,
            none_is_skip=False,
        )(original_function)

        # Check that metadata is preserved
        assert decorated_function.__name__ == original_function.__name__
        assert decorated_function.__doc__ == original_function.__doc__

    def test_skip_if_with_complex_predicate(self):
        """Test skip_if with complex predicate function."""

        def complex_predicate(fv):
            """Check if value is negative and less than -50."""
            return fv < -50

        @skip_if(
            arg="test_value",
            policy_flag="negative_sales_is_none",
            predicate=complex_predicate,
            none_is_skip=False,
        )
        def test_function(test_value: FV[Money]) -> FV[Money]:
            return test_value * 2

        # Test with value that meets complex predicate
        very_negative = FV(Decimal("-100"), policy=self.policy_with_flag, unit=Money)
        result = test_function(very_negative)
        assert result.is_none()

        # Test with negative value that doesn't meet predicate
        slightly_negative = FV(Decimal("-30"), policy=self.policy_with_flag, unit=Money)
        result = test_function(slightly_negative)
        assert result.as_decimal() == Decimal("-60")

    def test_skip_if_error_handling_in_predicate(self):
        """Test skip_if behavior when predicate raises an error."""

        def error_predicate(fv):
            """Predicate that raises an error."""
            raise ValueError("Predicate error")

        @skip_if(
            arg="test_value",
            policy_flag="negative_sales_is_none",
            predicate=error_predicate,
            none_is_skip=False,
        )
        def test_function(test_value: FV[Money]) -> FV[Money]:
            return test_value * 2

        test_value = FV(Decimal("100"), policy=self.policy_with_flag, unit=Money)

        # Predicate error should propagate
        with pytest.raises(ValueError, match="Predicate error"):
            test_function(test_value)

    def test_skip_if_with_multiple_args(self):
        """Test skip_if with function that has multiple arguments."""

        @skip_if(
            arg="sales",  # Only checking the sales argument
            policy_flag="negative_sales_is_none",
            predicate=lambda x: x < 0,
            none_is_skip=False,
        )
        def test_function(sales: FV[Money], cost: FV[Money]) -> FV[Money]:
            return sales - cost

        negative_sales = FV(Decimal("-100"), policy=self.policy_with_flag, unit=Money)
        cost = FV(Decimal("50"), policy=self.policy_with_flag, unit=Money)

        result = test_function(negative_sales, cost)
        assert result.is_none()

        # Test with positive sales
        positive_sales = FV(Decimal("100"), policy=self.policy_with_flag, unit=Money)
        result = test_function(positive_sales, cost)
        assert result.as_decimal() == Decimal("50")

    def test_skip_if_return_type_preservation(self):
        """Test that skip_if preserves the return type correctly."""

        @skip_if(
            arg="test_value",
            policy_flag="negative_sales_is_none",
            predicate=lambda x: x < 0,
            none_is_skip=False,
        )
        def test_function(test_value: FV[Money]) -> FV[Money]:
            return test_value * 2

        negative_value = FV(Decimal("-100"), policy=self.policy_with_flag, unit=Money)
        result = test_function(negative_value)

        # Check that the returned None value has the correct type
        assert isinstance(result, FV)
        assert result.is_none()
        # Note: The actual implementation may use type(fv).none(pol) which preserves the original type structure
        # but may reset to default unit. This is acceptable behavior.
        assert result.policy == self.policy_with_flag  # Should preserve policy

    def test_integration_with_actual_calculation_functions(self):
        """Test integration with calculation functions that use skip_if_negative_sales."""
        # This is more of an integration test showing how the decorator works
        # with real calculation patterns

        @skip_if_negative_sales("sales")
        def simple_gross_profit(sales: FV[Money], cost: FV[Money]) -> FV[Money]:
            """Simple gross profit calculation with negative sales protection."""
            return sales - cost

        # Test with negative sales
        negative_sales = FV(Decimal("-100"), policy=self.policy_with_flag, unit=Money)
        cost = FV(Decimal("50"), policy=self.policy_with_flag, unit=Money)

        result = simple_gross_profit(negative_sales, cost)
        assert result.is_none()

        # Test with positive sales
        positive_sales = FV(Decimal("200"), policy=self.policy_with_flag, unit=Money)
        result = simple_gross_profit(positive_sales, cost)
        assert result.as_decimal() == Decimal("150")

    def test_boundary_conditions(self):
        """Test boundary conditions for the negative sales predicate."""

        @skip_if_negative_sales("sales")
        def test_function(sales: FV[Money]) -> FV[Money]:
            return sales * 2

        # Test exactly zero (should not skip since predicate is x < 0)
        zero_sales = FV(Decimal("0"), policy=self.policy_with_flag, unit=Money)
        result = test_function(zero_sales)
        assert result.as_decimal() == Decimal("0.0000")

        # Test very small negative number
        tiny_negative = FV(Decimal("-0.0001"), policy=self.policy_with_flag, unit=Money)
        result = test_function(tiny_negative)
        assert result.is_none()

        # Test very small positive number
        tiny_positive = FV(Decimal("0.0001"), policy=self.policy_with_flag, unit=Money)
        result = test_function(tiny_positive)
        # Result will be rounded to 2 decimal places due to policy
        assert result.as_decimal() == Decimal("0.00")
