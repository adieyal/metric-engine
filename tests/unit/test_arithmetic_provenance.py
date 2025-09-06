"""Tests for provenance tracking in arithmetic operations."""
from decimal import Decimal

import pytest

from metricengine.policy import DEFAULT_POLICY, Policy
from metricengine.units import Money, Percent
from metricengine.value import FinancialValue


class TestArithmeticProvenance:
    """Test provenance tracking for all arithmetic operations."""

    def test_addition_provenance(self):
        """Test that addition operations generate proper provenance."""
        fv1 = FinancialValue(100)
        fv2 = FinancialValue(50)

        result = fv1 + fv2

        # Verify result value
        assert result.as_decimal() == Decimal("150.00")

        # Verify provenance
        assert result.has_provenance()
        prov = result.get_provenance()
        assert prov is not None
        assert prov.op == "+"
        assert len(prov.inputs) == 2

        # Verify parent provenance IDs are included
        parent_ids = set(prov.inputs)
        assert fv1.get_provenance().id in parent_ids
        assert fv2.get_provenance().id in parent_ids

    def test_subtraction_provenance(self):
        """Test that subtraction operations generate proper provenance."""
        fv1 = FinancialValue(100)
        fv2 = FinancialValue(30)

        result = fv1 - fv2

        # Verify result value
        assert result.as_decimal() == Decimal("70.00")

        # Verify provenance
        assert result.has_provenance()
        prov = result.get_provenance()
        assert prov is not None
        assert prov.op == "-"
        assert len(prov.inputs) == 2

        # Verify parent provenance IDs are included
        parent_ids = set(prov.inputs)
        assert fv1.get_provenance().id in parent_ids
        assert fv2.get_provenance().id in parent_ids

    def test_multiplication_provenance(self):
        """Test that multiplication operations generate proper provenance."""
        fv1 = FinancialValue(10)
        fv2 = FinancialValue(5)

        result = fv1 * fv2

        # Verify result value
        assert result.as_decimal() == Decimal("50.00")

        # Verify provenance
        assert result.has_provenance()
        prov = result.get_provenance()
        assert prov is not None
        assert prov.op == "*"
        assert len(prov.inputs) == 2

        # Verify parent provenance IDs are included
        parent_ids = set(prov.inputs)
        assert fv1.get_provenance().id in parent_ids
        assert fv2.get_provenance().id in parent_ids

    def test_division_provenance(self):
        """Test that division operations generate proper provenance."""
        fv1 = FinancialValue(100)
        fv2 = FinancialValue(4)

        result = fv1 / fv2

        # Verify result value
        assert result.as_decimal() == Decimal("25.00")

        # Verify provenance
        assert result.has_provenance()
        prov = result.get_provenance()
        assert prov is not None
        assert prov.op == "/"
        assert len(prov.inputs) == 2

        # Verify parent provenance IDs are included
        parent_ids = set(prov.inputs)
        assert fv1.get_provenance().id in parent_ids
        assert fv2.get_provenance().id in parent_ids

    def test_power_provenance(self):
        """Test that power operations generate proper provenance."""
        fv1 = FinancialValue(2)
        fv2 = FinancialValue(3)

        result = fv1**fv2

        # Verify result value
        assert result.as_decimal() == Decimal("8.00")

        # Verify provenance
        assert result.has_provenance()
        prov = result.get_provenance()
        assert prov is not None
        assert prov.op == "**"
        assert len(prov.inputs) == 2
        assert prov.meta.get("exponent_type") == "integer"

        # Verify parent provenance IDs are included
        parent_ids = set(prov.inputs)
        assert fv1.get_provenance().id in parent_ids
        assert fv2.get_provenance().id in parent_ids

    def test_power_special_case_provenance(self):
        """Test that 0^0 power operation generates proper provenance."""
        fv1 = FinancialValue(0)
        fv2 = FinancialValue(0)

        result = fv1**fv2

        # Verify result value (0^0 = 1)
        assert result.as_decimal() == Decimal("1.00")

        # Verify provenance
        assert result.has_provenance()
        prov = result.get_provenance()
        assert prov is not None
        assert prov.op == "**"
        assert len(prov.inputs) == 2
        assert prov.meta.get("special_case") == "0^0"

    def test_sqrt_provenance(self):
        """Test that square root (0.5 power) generates proper provenance."""
        fv1 = FinancialValue(16)
        fv2 = FinancialValue(0.5)

        result = fv1**fv2

        # Verify result value
        assert result.as_decimal() == Decimal("4.00")

        # Verify provenance
        assert result.has_provenance()
        prov = result.get_provenance()
        assert prov is not None
        assert prov.op == "**"
        assert len(prov.inputs) == 2
        assert prov.meta.get("exponent_type") == "sqrt"

    def test_negation_provenance(self):
        """Test that negation operations generate proper provenance."""
        fv = FinancialValue(100)

        result = -fv

        # Verify result value
        assert result.as_decimal() == Decimal("-100.00")

        # Verify provenance
        assert result.has_provenance()
        prov = result.get_provenance()
        assert prov is not None
        assert prov.op == "neg"
        assert len(prov.inputs) == 1
        assert fv.get_provenance().id in prov.inputs

    def test_absolute_value_provenance(self):
        """Test that absolute value operations generate proper provenance."""
        fv = FinancialValue(-100)

        result = abs(fv)

        # Verify result value
        assert result.as_decimal() == Decimal("100.00")

        # Verify provenance
        assert result.has_provenance()
        prov = result.get_provenance()
        assert prov is not None
        assert prov.op == "abs"
        assert len(prov.inputs) == 1
        assert fv.get_provenance().id in prov.inputs

    def test_reverse_addition_provenance(self):
        """Test that reverse addition (raw + FV) generates proper provenance."""
        fv = FinancialValue(50)

        result = 100 + fv  # This calls __radd__

        # Verify result value
        assert result.as_decimal() == Decimal("150.00")

        # Verify provenance
        assert result.has_provenance()
        prov = result.get_provenance()
        assert prov is not None
        assert prov.op == "+"
        assert len(prov.inputs) == 2

    def test_reverse_subtraction_provenance(self):
        """Test that reverse subtraction (raw - FV) generates proper provenance."""
        fv = FinancialValue(30)

        result = 100 - fv  # This calls __rsub__

        # Verify result value
        assert result.as_decimal() == Decimal("70.00")

        # Verify provenance
        assert result.has_provenance()
        prov = result.get_provenance()
        assert prov is not None
        assert prov.op == "-"
        assert len(prov.inputs) == 2

    def test_reverse_multiplication_provenance(self):
        """Test that reverse multiplication (raw * FV) generates proper provenance."""
        fv = FinancialValue(5)

        result = 10 * fv  # This calls __rmul__

        # Verify result value
        assert result.as_decimal() == Decimal("50.00")

        # Verify provenance
        assert result.has_provenance()
        prov = result.get_provenance()
        assert prov is not None
        assert prov.op == "*"
        assert len(prov.inputs) == 2

    def test_reverse_division_provenance(self):
        """Test that reverse division (raw / FV) generates proper provenance."""
        fv = FinancialValue(4)

        result = 100 / fv  # This calls __rtruediv__

        # Verify result value
        assert result.as_decimal() == Decimal("25.00")

        # Verify provenance
        assert result.has_provenance()
        prov = result.get_provenance()
        assert prov is not None
        assert prov.op == "/"
        assert len(prov.inputs) == 2

    def test_chained_operations_provenance(self):
        """Test that chained operations maintain proper provenance chains."""
        fv1 = FinancialValue(100)
        fv2 = FinancialValue(50)
        fv3 = FinancialValue(2)

        # (100 + 50) * 2
        intermediate = fv1 + fv2
        result = intermediate * fv3

        # Verify intermediate result
        assert intermediate.as_decimal() == Decimal("150.00")
        assert intermediate.has_provenance()
        intermediate_prov = intermediate.get_provenance()
        assert intermediate_prov.op == "+"

        # Verify final result
        assert result.as_decimal() == Decimal("300.00")
        assert result.has_provenance()
        result_prov = result.get_provenance()
        assert result_prov.op == "*"

        # Verify provenance chain
        assert intermediate_prov.id in result_prov.inputs
        assert fv3.get_provenance().id in result_prov.inputs

    def test_provenance_id_consistency(self):
        """Test that identical operations produce identical provenance IDs."""
        # Create identical operations
        fv1a = FinancialValue(100, policy=DEFAULT_POLICY)
        fv2a = FinancialValue(50, policy=DEFAULT_POLICY)
        result_a = fv1a + fv2a

        fv1b = FinancialValue(100, policy=DEFAULT_POLICY)
        fv2b = FinancialValue(50, policy=DEFAULT_POLICY)
        result_b = fv1b + fv2b

        # Verify that identical inputs produce identical provenance IDs
        assert fv1a.get_provenance().id == fv1b.get_provenance().id
        assert fv2a.get_provenance().id == fv2b.get_provenance().id
        assert result_a.get_provenance().id == result_b.get_provenance().id

    def test_different_policies_different_provenance(self):
        """Test that different policies produce different provenance IDs."""
        policy1 = Policy(decimal_places=2)
        policy2 = Policy(decimal_places=4)

        fv1 = FinancialValue(100, policy=policy1)
        fv2 = FinancialValue(100, policy=policy2)

        # Should have different provenance IDs due to different policies
        prov1 = fv1.get_provenance()
        prov2 = fv2.get_provenance()
        assert prov1.id != prov2.id

    def test_none_operand_handling(self):
        """Test that operations with None operands are handled gracefully."""
        fv1 = FinancialValue(100)
        fv2 = FinancialValue(None)

        result = fv1 + fv2

        # Should return None result
        assert result.is_none()

        # May or may not have provenance depending on implementation
        # The important thing is that it doesn't crash

    def test_division_by_zero_provenance(self):
        """Test that division by zero is handled gracefully."""
        fv1 = FinancialValue(100)
        fv2 = FinancialValue(0)

        result = fv1 / fv2

        # Should return None result for division by zero
        assert result.is_none()

        # May or may not have provenance depending on implementation
        # The important thing is that it doesn't crash

    def test_arithmetic_with_different_units(self):
        """Test arithmetic operations with different units maintain provenance."""
        money1 = FinancialValue(100, unit=Money)
        money2 = FinancialValue(50, unit=Money)

        result = money1 + money2

        # Verify result
        assert result.as_decimal() == Decimal("150.00")
        assert result.unit is Money

        # Verify provenance
        assert result.has_provenance()
        prov = result.get_provenance()
        assert prov is not None
        assert prov.op == "+"
        assert len(prov.inputs) == 2

    def test_percentage_operations_provenance(self):
        """Test that percentage operations maintain provenance."""
        pct1 = FinancialValue(0.15, unit=Percent, _is_percentage=True)
        pct2 = FinancialValue(0.05, unit=Percent, _is_percentage=True)

        result = pct1 + pct2

        # Verify result
        assert result.as_decimal() == Decimal("20.00")  # 15% + 5% = 20%
        assert result._is_percentage

        # Verify provenance
        assert result.has_provenance()
        prov = result.get_provenance()
        assert prov is not None
        assert prov.op == "+"
        assert len(prov.inputs) == 2


if __name__ == "__main__":
    pytest.main([__file__])
