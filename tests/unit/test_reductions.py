from decimal import Decimal

import pytest

from metricengine.exceptions import CalculationError
from metricengine.null_behaviour import NullReductionMode
from metricengine.policy import Policy
from metricengine.reductions import (
    _is_noneish,
    _pick_policy_for_items,
    _pick_unit_for_items,
    fv_mean,
    fv_sum,
    fv_weighted_mean,
)
from metricengine.units import Dimensionless, Money
from metricengine.value import FinancialValue as FV


class TestReductions:
    def test_sum_basic(self):
        """Test basic sum functionality."""
        values = [FV(10), FV(20), FV(30)]
        result = fv_sum(values)
        assert result.as_decimal() == Decimal("60")

    def test_sum_with_none_values_skip_mode(self):
        """Test sum with None values in SKIP mode."""
        from metricengine.null_behaviour import (
            NullReductionMode,
        )

        values = [FV(10), None, FV(30), FV.none()]
        result = fv_sum(values, mode=NullReductionMode.SKIP)
        assert result.as_decimal() == Decimal("40")

    def test_sum_with_none_values_zero_mode(self):
        """Test sum with None values in ZERO mode."""
        from metricengine.null_behaviour import (
            NullReductionMode,
        )

        values = [FV(10), None, FV(30), FV.none()]
        result = fv_sum(values, mode=NullReductionMode.ZERO)
        assert result.as_decimal() == Decimal("40")

    def test_sum_with_none_values_propagate_mode(self):
        """Test sum with None values in PROPAGATE mode."""
        from metricengine.null_behaviour import (
            NullReductionMode,
        )

        values = [FV(10), None, FV(30)]
        result = fv_sum(values, mode=NullReductionMode.PROPAGATE)
        assert result.is_none()

    def test_sum_with_none_values_raise_mode(self):
        """Test sum with None values in RAISE mode."""
        from metricengine.null_behaviour import (
            NullReductionMode,
        )

        values = [FV(10), None, FV(30)]
        with pytest.raises(CalculationError, match="Reduction encountered None"):
            fv_sum(values, mode=NullReductionMode.RAISE)

    def test_sum_all_none_values_skip_mode(self):
        """Test sum with all None values in SKIP mode."""
        from metricengine.null_behaviour import (
            NullReductionMode,
        )

        values = [None, FV.none(), None]
        result = fv_sum(values, mode=NullReductionMode.SKIP)
        assert result.is_none()

    def test_sum_all_none_values_zero_mode(self):
        """Test sum with all None values in ZERO mode."""
        from metricengine.null_behaviour import (
            NullReductionMode,
        )

        values = [None, FV.none(), None]
        result = fv_sum(values, mode=NullReductionMode.ZERO)
        assert result.as_decimal() == Decimal("0")

    def test_sum_empty_iterable(self):
        """Test sum with empty iterable."""
        result = fv_sum([])
        assert result.is_none()

    def test_sum_mixed_types(self):
        """Test sum with mixed types (raw values and FinancialValue)."""
        values = [10, FV(20), 30.5, FV(40)]
        result = fv_sum(values)
        assert result.as_decimal() == Decimal("100.50")

    def test_sum_default_mode(self):
        """Test sum with default mode (should use context default)."""
        values = [FV(10), FV(20)]
        result = fv_sum(values)  # No mode specified
        assert result.as_decimal() == Decimal("30")

    def test_mean_basic(self):
        """Test basic mean functionality."""
        values = [FV(10), FV(20), FV(30)]
        result = fv_mean(values)
        assert result.as_decimal() == Decimal("20")

    def test_mean_with_none_values_skip_mode(self):
        """Test mean with None values in SKIP mode."""
        from metricengine.null_behaviour import (
            NullReductionMode,
        )

        values = [FV(10), None, FV(30), FV.none()]
        result = fv_mean(values, mode=NullReductionMode.SKIP)
        assert result.as_decimal() == Decimal("20")  # (10 + 30) / 2

    def test_mean_with_none_values_zero_mode(self):
        """Test mean with None values in ZERO mode."""
        from metricengine.null_behaviour import (
            NullReductionMode,
        )

        values = [FV(10), None, FV(30), FV.none()]
        result = fv_mean(values, mode=NullReductionMode.ZERO)
        assert result.as_decimal() == Decimal("10")  # (10 + 0 + 30 + 0) / 4

    def test_mean_with_none_values_propagate_mode(self):
        """Test mean with None values in PROPAGATE mode."""
        from metricengine.null_behaviour import (
            NullReductionMode,
        )

        values = [FV(10), None, FV(30)]
        result = fv_mean(values, mode=NullReductionMode.PROPAGATE)
        assert result.is_none()

    def test_mean_with_none_values_raise_mode(self):
        """Test mean with None values in RAISE mode."""
        from metricengine.null_behaviour import (
            NullReductionMode,
        )

        values = [FV(10), None, FV(30)]
        with pytest.raises(CalculationError, match="Reduction encountered None"):
            fv_mean(values, mode=NullReductionMode.RAISE)

    def test_mean_all_none_values_skip_mode(self):
        """Test mean with all None values in SKIP mode."""
        from metricengine.null_behaviour import (
            NullReductionMode,
        )

        values = [None, FV.none(), None]
        result = fv_mean(values, mode=NullReductionMode.SKIP)
        assert result.is_none()

    def test_mean_all_none_values_zero_mode(self):
        """Test mean with all None values in ZERO mode."""
        from metricengine.null_behaviour import (
            NullReductionMode,
        )

        values = [None, FV.none(), None]
        result = fv_mean(values, mode=NullReductionMode.ZERO)
        assert result.is_none()  # Empty list case

    def test_mean_empty_iterable(self):
        """Test mean with empty iterable."""
        result = fv_mean([])
        assert result.is_none()

    def test_mean_mixed_types(self):
        """Test mean with mixed types (raw values and FinancialValue)."""
        values = [10, FV(20), 30.5, FV(40)]
        result = fv_mean(values)
        assert result.as_decimal() == Decimal("25.13")  # (10 + 20 + 30.5 + 40) / 4

    def test_mean_default_mode(self):
        """Test mean with default mode (should use context default)."""
        values = [FV(10), FV(20)]
        result = fv_mean(values)  # No mode specified
        assert result.as_decimal() == Decimal("15")

    def test_mean_precision(self):
        """Test mean calculation precision."""
        values = [FV("1.333"), FV("2.667")]
        result = fv_mean(values)
        # Should be (1.33 + 2.67) / 2 = 2.00
        assert result.as_decimal() == Decimal("2.00")

    def test_sum_and_mean_consistency(self):
        """Test that sum and mean are consistent with each other."""
        values = [FV(10), FV(20), FV(30)]

        total = fv_sum(values)
        mean = fv_mean(values)
        count = len(values)

        # mean * count should equal sum
        assert (mean * count).as_decimal() == total.as_decimal()

    def test_sum_with_policy_inheritance(self):
        """Test that sum inherits policy from first non-None value."""
        custom_policy = Policy(decimal_places=3)
        values = [FV(10, policy=custom_policy), FV(20)]

        result = fv_sum(values)
        assert result.policy == custom_policy
        assert result.as_decimal() == Decimal("30.000")

    def test_mean_with_policy_inheritance(self):
        """Test that mean inherits policy from first non-None value."""
        custom_policy = Policy(decimal_places=3)
        values = [FV(10, policy=custom_policy), FV(20)]

        result = fv_mean(values)
        assert result.policy == custom_policy
        assert result.as_decimal() == Decimal("15.000")

    def test_sum_edge_cases(self):
        """Test sum with edge cases."""
        # Single value
        result = fv_sum([FV(42)])
        assert result.as_decimal() == Decimal("42")

        # Zero values
        result = fv_sum([FV(0), FV(0)])
        assert result.as_decimal() == Decimal("0")

        # Negative values
        result = fv_sum([FV(-10), FV(20)])
        assert result.as_decimal() == Decimal("10")

    def test_mean_edge_cases(self):
        """Test mean with edge cases."""
        # Single value
        result = fv_mean([FV(42)])
        assert result.as_decimal() == Decimal("42")

        # Zero values
        result = fv_mean([FV(0), FV(0)])
        assert result.as_decimal() == Decimal("0")

        # Negative values
        result = fv_mean([FV(-10), FV(20)])
        assert result.as_decimal() == Decimal("5")

    def test_sum_noneish_detection(self):
        """Test that _is_noneish correctly identifies None-like values."""
        values = [None, FV.none(), FV(10)]

        # Should treat both None and FinancialValue.none() as None
        result = fv_sum(values, mode=NullReductionMode.SKIP)
        assert result.as_decimal() == Decimal("10")

    def test_mean_noneish_detection(self):
        """Test that _is_noneish correctly identifies None-like values."""
        values = [None, FV.none(), FV(10)]

        # Should treat both None and FinancialValue.none() as None
        result = fv_mean(values, mode=NullReductionMode.SKIP)
        assert result.as_decimal() == Decimal("10")

    def test_fv_weighted_mean_basic(self):
        """Test basic weighted mean functionality."""
        pairs = [(FV(10), FV(2)), (FV(20), FV(3)), (FV(30), FV(1))]
        result = fv_weighted_mean(pairs)
        # (10*2 + 20*3 + 30*1) / (2+3+1) = (20+60+30)/6 = 110/6 = 18.33
        assert result.as_decimal() == Decimal("18.33")

    def test_fv_weighted_mean_with_none_values_skip_mode(self):
        """Test weighted mean with None values in SKIP mode."""
        from metricengine.null_behaviour import (
            NullReductionMode,
        )

        pairs = [(FV(10), FV(2)), (None, FV(3)), (FV(30), None), (FV(40), FV(1))]
        result = fv_weighted_mean(pairs, mode=NullReductionMode.SKIP)
        # Only (10,2) and (40,1) are valid: (10*2 + 40*1) / (2+1) = 60/3 = 20
        assert result.as_decimal() == Decimal("20")

    def test_fv_weighted_mean_with_none_values_zero_mode(self):
        """Test weighted mean with None values in ZERO mode."""
        from metricengine.null_behaviour import (
            NullReductionMode,
        )

        pairs = [(FV(10), FV(2)), (None, FV(3)), (FV(30), None), (FV(40), FV(1))]
        result = fv_weighted_mean(pairs, mode=NullReductionMode.ZERO)
        # (10*2 + 0*3 + 30*0 + 40*1) / (2+3+0+1) = (20+0+0+40)/6 = 60/6 = 10
        assert result.as_decimal() == Decimal("10")

    def test_fv_weighted_mean_with_none_values_propagate_mode(self):
        """Test weighted mean with None values in PROPAGATE mode."""
        from metricengine.null_behaviour import (
            NullReductionMode,
        )

        pairs = [(FV(10), FV(2)), (None, FV(3)), (FV(30), FV(1))]
        result = fv_weighted_mean(pairs, mode=NullReductionMode.PROPAGATE)
        assert result.is_none()

    def test_fv_weighted_mean_with_none_values_raise_mode(self):
        """Test weighted mean with None values in RAISE mode."""
        from metricengine.null_behaviour import (
            NullReductionMode,
        )

        pairs = [(FV(10), FV(2)), (None, FV(3)), (FV(30), FV(1))]
        with pytest.raises(CalculationError, match="Reduction encountered None"):
            fv_weighted_mean(pairs, mode=NullReductionMode.RAISE)

    def test_fv_weighted_mean_empty_iterable(self):
        """Test weighted mean with empty iterable."""
        result = fv_weighted_mean([])
        assert result.is_none()

    def test_fv_weighted_mean_all_none_values_zero_mode(self):
        """Test weighted mean with all None values in ZERO mode."""
        from metricengine.null_behaviour import (
            NullReductionMode,
        )

        pairs = [(None, FV(2)), (FV(10), None), (None, None)]
        result = fv_weighted_mean(pairs, mode=NullReductionMode.ZERO)
        # (0*2 + 10*0 + 0*0) / (2+0+0) = 0/2 = 0
        assert result.as_decimal() == Decimal("0")

    def test_fv_weighted_mean_zero_total_weight(self):
        """Test weighted mean when total weight is zero."""
        pairs = [(FV(10), FV(0)), (FV(20), FV(0))]
        result = fv_weighted_mean(pairs)
        assert result.is_none()  # Division by zero case

    def test_fv_weighted_mean_mixed_types(self):
        """Test weighted mean with mixed types."""
        pairs = [(10, 2), (FV(20), 3.5), (30.5, FV(1))]
        result = fv_weighted_mean(pairs)
        # (10*2 + 20*3.5 + 30.5*1) / (2+3.5+1) = (20+70+30.5)/6.5 = 120.5/6.5 = 18.54
        assert result.as_decimal() == Decimal("18.54")

    def test_fv_weighted_mean_policy_inheritance(self):
        """Test that weighted mean inherits policy from values."""
        custom_policy = Policy(decimal_places=3)
        pairs = [(FV(10, policy=custom_policy), FV(2)), (FV(20), FV(3))]
        result = fv_weighted_mean(pairs)
        assert result.policy == custom_policy
        assert result.as_decimal() == Decimal("16.000")

    def test_fv_weighted_mean_edge_cases(self):
        """Test weighted mean with edge cases."""
        # Single pair
        result = fv_weighted_mean([(FV(42), FV(1))])
        assert result.as_decimal() == Decimal("42")

        # Equal weights (should behave like regular mean)
        pairs = [(FV(10), FV(1)), (FV(20), FV(1)), (FV(30), FV(1))]
        result = fv_weighted_mean(pairs)
        assert result.as_decimal() == Decimal("20")  # Same as regular mean

        # Negative values
        pairs = [(FV(-10), FV(2)), (FV(20), FV(3))]
        result = fv_weighted_mean(pairs)
        # (-10*2 + 20*3) / (2+3) = (-20+60)/5 = 40/5 = 8
        assert result.as_decimal() == Decimal("8")

    def test_unit_consistency_sum(self):
        """Test that sum preserves units correctly."""

        values = [FV(10, unit=Money), FV(20, unit=Money)]
        result = fv_sum(values)
        assert result.unit == Money
        assert result.as_decimal() == Decimal("30")

    def test_unit_consistency_mean(self):
        """Test that mean preserves units correctly."""

        values = [FV(10, unit=Money), FV(20, unit=Money)]
        result = fv_mean(values)
        assert result.unit == Money
        assert result.as_decimal() == Decimal("15")

    def test_unit_consistency_weighted_mean(self):
        """Test that weighted mean preserves units correctly."""

        pairs = [(FV(10, unit=Money), FV(2)), (FV(20, unit=Money), FV(3))]
        result = fv_weighted_mean(pairs)
        assert result.unit == Money
        assert result.as_decimal() == Decimal("16")

    def test_explicit_policy_override(self):
        """Test that explicit policy parameter overrides item policies."""
        custom_policy = Policy(decimal_places=4)
        override_policy = Policy(decimal_places=1)

        values = [FV(10, policy=custom_policy), FV(20, policy=custom_policy)]
        result = fv_sum(values, policy=override_policy)
        assert result.policy == override_policy
        assert result.as_decimal() == Decimal("30.0")  # 1 decimal place

    def test_explicit_policy_override_mean(self):
        """Test that explicit policy parameter overrides item policies for mean."""
        custom_policy = Policy(decimal_places=4)
        override_policy = Policy(decimal_places=1)

        values = [FV(10, policy=custom_policy), FV(20, policy=custom_policy)]
        result = fv_mean(values, policy=override_policy)
        assert result.policy == override_policy
        assert result.as_decimal() == Decimal("15.0")  # 1 decimal place

    def test_explicit_policy_override_weighted_mean(self):
        """Test that explicit policy parameter overrides item policies for weighted mean."""
        custom_policy = Policy(decimal_places=4)
        override_policy = Policy(decimal_places=1)

        pairs = [
            (FV(10, policy=custom_policy), FV(2)),
            (FV(20, policy=custom_policy), FV(3)),
        ]
        result = fv_weighted_mean(pairs, policy=override_policy)
        assert result.policy == override_policy
        assert result.as_decimal() == Decimal("16.0")  # 1 decimal place

    def test_error_message_specificity(self):
        """Test that error messages are specific and helpful."""
        values = [FV(10), None, FV(30)]

        with pytest.raises(CalculationError) as exc_info:
            fv_sum(values, mode=NullReductionMode.RAISE)
        assert "Reduction encountered None" in str(exc_info.value)

        with pytest.raises(CalculationError) as exc_info:
            fv_mean(values, mode=NullReductionMode.RAISE)
        assert "Reduction encountered None" in str(exc_info.value)

        pairs = [(FV(10), FV(2)), (None, FV(3))]
        with pytest.raises(CalculationError) as exc_info:
            fv_weighted_mean(pairs, mode=NullReductionMode.RAISE)
        assert "Reduction encountered None" in str(exc_info.value)

    def test_helper_functions_edge_cases(self):
        """Test helper functions with edge cases."""
        # Test _is_noneish with various inputs
        assert _is_noneish(None) is True
        assert _is_noneish(FV.none()) is True
        assert _is_noneish(FV(10)) is False
        assert _is_noneish(10) is False

        # Test _pick_policy_for_items with all None values
        result_policy = _pick_policy_for_items([None, FV.none()])
        assert result_policy is not None  # Should return default policy

        # Test _pick_unit_for_items with all None values
        result_unit = _pick_unit_for_items([None, FV.none()])
        assert result_unit == Dimensionless

    def test_large_numbers_precision(self):
        """Test precision with large numbers."""
        large_values = [FV("999999999.99"), FV("0.01")]
        result = fv_sum(large_values)
        assert result.as_decimal() == Decimal("1000000000.00")

        result = fv_mean(large_values)
        assert result.as_decimal() == Decimal("500000000.00")

    def test_very_small_numbers_precision(self):
        """Test precision with very small numbers."""
        # Use a policy with more decimal places to preserve precision
        high_precision_policy = Policy(decimal_places=4)
        small_values = [
            FV("0.0001", policy=high_precision_policy),
            FV("0.0001", policy=high_precision_policy),
        ]
        result = fv_sum(small_values)
        assert result.as_decimal() == Decimal("0.0002")

        result = fv_mean(small_values)
        assert result.as_decimal() == Decimal("0.0001")
