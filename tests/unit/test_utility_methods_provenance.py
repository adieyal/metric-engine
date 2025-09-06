"""Tests for provenance tracking in FinancialValue utility methods."""
from decimal import Decimal

from metricengine import FinancialValue as FV
from metricengine import Policy
from metricengine.units import Dimensionless, Money, Percent, Ratio


class TestUtilityMethodsProvenance:
    """Test provenance tracking for FinancialValue utility methods."""

    def test_as_percentage_provenance(self):
        """Test that as_percentage() generates proper provenance."""
        # Create a base value
        base = FV(0.15)

        # Convert to percentage
        percentage = base.as_percentage()

        # Check that provenance was created
        assert percentage.has_provenance()
        prov = percentage.get_provenance()
        assert prov is not None
        assert prov.op == "as_percentage"
        assert len(prov.inputs) == 1
        assert prov.inputs[0] == base.get_provenance().id
        assert prov.meta["conversion"] == "to_percentage"

        # Check that the result has correct properties
        assert percentage.unit is Percent
        assert percentage.is_percentage()
        assert percentage._value == Decimal("0.15")

    def test_ratio_provenance(self):
        """Test that ratio() generates proper provenance."""
        # Create a percentage value
        percentage = FV(0.25).as_percentage()

        # Convert to ratio
        ratio = percentage.ratio()

        # Check that provenance was created
        assert ratio.has_provenance()
        prov = ratio.get_provenance()
        assert prov is not None
        assert prov.op == "ratio"
        assert len(prov.inputs) == 1
        assert prov.inputs[0] == percentage.get_provenance().id
        assert prov.meta["conversion"] == "to_ratio"

        # Check that the result has correct properties
        assert ratio.unit is Ratio
        assert not ratio.is_percentage()
        assert ratio._value == Decimal("0.25")

    def test_with_policy_provenance(self):
        """Test that with_policy() generates proper provenance."""
        # Create a base value with default policy
        base = FV(123.456)
        original_policy = base.policy

        # Create a new policy
        new_policy = Policy(decimal_places=4)

        # Apply new policy
        result = base.with_policy(new_policy)

        # Check that provenance was created
        assert result.has_provenance()
        prov = result.get_provenance()
        assert prov is not None
        assert prov.op == "with_policy"
        assert len(prov.inputs) == 1
        assert prov.inputs[0] == base.get_provenance().id
        assert prov.meta["policy_change"] == "applied"

        # Check that the result has correct properties
        assert result.policy == new_policy
        assert result.policy != original_policy
        assert result._value == base._value
        assert result.unit == base.unit

    def test_zero_class_method_provenance(self):
        """Test that zero() class method generates proper provenance."""
        # Create zero with default unit
        zero_default = FV.zero()

        # Check provenance
        assert zero_default.has_provenance()
        prov = zero_default.get_provenance()
        assert prov is not None
        assert prov.op == "zero"
        assert len(prov.inputs) == 0
        assert prov.meta["constant"] == "zero"
        assert prov.meta["unit"] == "Dimensionless"

        # Check value
        assert zero_default._value == Decimal("0")
        assert zero_default.unit is Dimensionless

        # Create zero with Money unit
        zero_money = FV.zero(unit=Money)

        # Check provenance
        assert zero_money.has_provenance()
        prov_money = zero_money.get_provenance()
        assert prov_money is not None
        assert prov_money.op == "zero"
        assert prov_money.meta["unit"] == "Money"

        # Different units should have different provenance IDs
        assert prov.id != prov_money.id

    def test_none_class_method_provenance(self):
        """Test that none() class method generates proper provenance."""
        # Create None value
        none_value = FV.none()

        # Check provenance
        assert none_value.has_provenance()
        prov = none_value.get_provenance()
        assert prov is not None
        assert prov.op == "none"
        assert len(prov.inputs) == 0
        assert prov.meta["constant"] == "none"

        # Check value
        assert none_value._value is None
        assert none_value.is_none()

    def test_none_with_unit_provenance(self):
        """Test that none_with_unit() generates proper provenance."""
        # Create None with Money unit
        none_money = FV.none_with_unit(Money)

        # Check provenance
        assert none_money.has_provenance()
        prov = none_money.get_provenance()
        assert prov is not None
        assert prov.op == "none_with_unit"
        assert len(prov.inputs) == 0
        assert prov.meta["constant"] == "none"
        assert prov.meta["unit"] == "Money"

        # Check value
        assert none_money._value is None
        assert none_money.unit is Money
        assert none_money.is_none()

    def test_constant_class_method_provenance(self):
        """Test that constant() class method generates proper provenance."""
        # Create constant value
        constant_val = FV.constant(42.5, unit=Money)

        # Check provenance
        assert constant_val.has_provenance()
        prov = constant_val.get_provenance()
        assert prov is not None
        assert prov.op == "constant"
        assert len(prov.inputs) == 0
        assert prov.meta["constant"] == "42.5"
        assert prov.meta["unit"] == "Money"

        # Check value
        assert constant_val._value == Decimal("42.5")
        assert constant_val.unit is Money

    def test_provenance_chain_through_conversions(self):
        """Test that provenance chains correctly through multiple conversions."""
        # Start with a base value
        base = FV(0.15)
        base_prov_id = base.get_provenance().id

        # Convert to percentage
        percentage = base.as_percentage()
        perc_prov_id = percentage.get_provenance().id

        # Convert back to ratio
        ratio = percentage.ratio()
        ratio_prov_id = ratio.get_provenance().id

        # Apply new policy
        new_policy = Policy(decimal_places=4)
        final = ratio.with_policy(new_policy)
        final_prov_id = final.get_provenance().id

        # Check the chain
        assert base_prov_id != perc_prov_id
        assert perc_prov_id != ratio_prov_id
        assert ratio_prov_id != final_prov_id

        # Check that each step references the previous
        assert percentage.get_provenance().inputs[0] == base_prov_id
        assert ratio.get_provenance().inputs[0] == perc_prov_id
        assert final.get_provenance().inputs[0] == ratio_prov_id

    def test_unit_conversion_maintains_provenance(self):
        """Test that unit conversions maintain proper provenance chains."""
        # Create a dimensionless value
        base = FV(0.25)

        # Convert to percentage
        percentage = base.as_percentage()
        assert percentage.unit is Percent
        assert percentage.get_provenance().op == "as_percentage"

        # Convert percentage to ratio
        ratio = percentage.ratio()
        assert ratio.unit is Ratio
        assert ratio.get_provenance().op == "ratio"

        # Check that values are preserved through conversions
        assert base._value == percentage._value == ratio._value

    def test_provenance_with_none_values(self):
        """Test provenance tracking with None values."""
        # Create None value using class method
        none_val = FV.none()
        assert none_val.has_provenance()
        assert none_val.get_provenance().op == "none"

        # Try to convert None to percentage
        none_percentage = none_val.as_percentage()
        assert none_percentage.has_provenance()
        assert none_percentage.get_provenance().op == "as_percentage"
        assert none_percentage.is_none()

    def test_provenance_deterministic_ids(self):
        """Test that provenance IDs are deterministic for identical operations."""
        # Create two identical base values
        base1 = FV(0.15)
        base2 = FV(0.15)

        # They should have the same provenance ID (same literal)
        assert base1.get_provenance().id == base2.get_provenance().id

        # Convert both to percentage
        perc1 = base1.as_percentage()
        perc2 = base2.as_percentage()

        # The percentage conversions should have the same provenance ID
        assert perc1.get_provenance().id == perc2.get_provenance().id

    def test_class_methods_with_different_policies(self):
        """Test that class methods generate different provenance for different policies."""
        policy1 = Policy(decimal_places=2)
        policy2 = Policy(decimal_places=4)

        # Create zero values with different policies
        zero1 = FV.zero(policy=policy1)
        zero2 = FV.zero(policy=policy2)

        # They should have different provenance IDs due to different policies
        assert zero1.get_provenance().id != zero2.get_provenance().id

        # Create constants with different policies
        const1 = FV.constant(100, policy=policy1)
        const2 = FV.constant(100, policy=policy2)

        # They should have different provenance IDs
        assert const1.get_provenance().id != const2.get_provenance().id

    def test_graceful_degradation_without_provenance_module(self):
        """Test that utility methods work even if provenance module fails."""
        # This test would require mocking the import, but we can at least
        # verify that the methods work correctly
        base = FV(0.15)

        # These should all work regardless of provenance
        percentage = base.as_percentage()
        assert percentage.unit is Percent
        assert percentage._value == Decimal("0.15")

        ratio = percentage.ratio()
        assert ratio.unit is Ratio

        new_policy = Policy(decimal_places=4)
        with_policy = base.with_policy(new_policy)
        assert with_policy.policy == new_policy

        # Class methods should work
        zero = FV.zero()
        assert zero._value == Decimal("0")

        none_val = FV.none()
        assert none_val.is_none()

        constant = FV.constant(42)
        assert constant._value == Decimal("42")
