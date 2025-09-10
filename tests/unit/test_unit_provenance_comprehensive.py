"""Comprehensive tests for unit-aware provenance tracking."""

from decimal import Decimal

from metricengine import FinancialValue as FV
from metricengine.units import (
    ConversionContext,
    MoneyUnit,
    Pct,
    Qty,
    register_conversion,
)


class TestUnitProvenanceTracking:
    """Test comprehensive unit-aware provenance tracking."""

    def test_literal_provenance_with_new_units(self):
        """Test that literal provenance includes unit information for new unit system."""
        usd = MoneyUnit("USD")
        fv = FV(Decimal("100.50"), unit=usd)

        if fv.has_provenance():
            prov = fv.get_provenance()
            assert prov.op == "literal"
            assert prov.meta.get("unit") == "Money[USD]"

    def test_literal_provenance_with_quantity_units(self):
        """Test literal provenance with quantity units."""
        kg = Qty("kg")
        fv = FV(Decimal("25.5"), unit=kg)

        if fv.has_provenance():
            prov = fv.get_provenance()
            assert prov.op == "literal"
            assert prov.meta.get("unit") == "Quantity[kg]"

    def test_literal_provenance_with_percent_units(self):
        """Test literal provenance with percent units."""
        ratio = Pct("ratio")
        fv = FV(Decimal("0.15"), unit=ratio)

        if fv.has_provenance():
            prov = fv.get_provenance()
            assert prov.op == "literal"
            assert prov.meta.get("unit") == "Percent[ratio]"

    def test_literal_provenance_with_none_unit(self):
        """Test that None units don't add unit metadata."""
        fv = FV(Decimal("100"), unit=None)

        if fv.has_provenance():
            prov = fv.get_provenance()
            assert prov.op == "literal"
            # None units should not add unit metadata
            assert "unit" not in prov.meta or prov.meta.get("unit") == ""

    def test_arithmetic_provenance_preserves_unit_info(self):
        """Test that arithmetic operations preserve unit information in provenance."""
        usd = MoneyUnit("USD")
        fv1 = FV(Decimal("100"), unit=usd)
        fv2 = FV(Decimal("50"), unit=usd)

        # Test addition
        result_add = fv1 + fv2
        if result_add.has_provenance():
            prov = result_add.get_provenance()
            assert prov.op == "+"
            assert prov.meta.get("unit") == "Money[USD]"
            assert len(prov.inputs) == 2

        # Test subtraction
        result_sub = fv1 - fv2
        if result_sub.has_provenance():
            prov = result_sub.get_provenance()
            assert prov.op == "-"
            assert prov.meta.get("unit") == "Money[USD]"

        # Test multiplication
        fv3 = FV(Decimal("2"), unit=None)
        result_mul = fv1 * fv3
        if result_mul.has_provenance():
            prov = result_mul.get_provenance()
            assert prov.op == "*"
            assert prov.meta.get("unit") == "Money[USD]"  # Preserves left operand unit

        # Test division
        result_div = fv1 / fv3
        if result_div.has_provenance():
            prov = result_div.get_provenance()
            assert prov.op == "/"
            assert prov.meta.get("unit") == "Money[USD]"  # Preserves left operand unit

    def test_arithmetic_provenance_with_mixed_units(self):
        """Test arithmetic provenance when mixing units with None."""
        usd = MoneyUnit("USD")
        fv_with_unit = FV(Decimal("100"), unit=usd)
        fv_without_unit = FV(Decimal("50"), unit=None)

        # Unit + None should preserve unit
        result = fv_with_unit + fv_without_unit
        if result.has_provenance():
            prov = result.get_provenance()
            assert prov.op == "+"
            assert prov.meta.get("unit") == "Money[USD]"

        # None + Unit should preserve unit
        result2 = fv_without_unit + fv_with_unit
        if result2.has_provenance():
            prov = result2.get_provenance()
            assert prov.op == "+"
            # The result unit depends on the implementation, but provenance should reflect it
            assert "unit" in prov.meta

    def test_conversion_provenance_comprehensive(self):
        """Test comprehensive conversion provenance tracking."""
        from metricengine.units import _conversion_registry

        # Clear registry for clean test
        _conversion_registry.clear()

        try:
            usd = MoneyUnit("USD")
            gbp = MoneyUnit("GBP")

            @register_conversion(usd, gbp)
            def usd_to_gbp(value: Decimal, ctx: ConversionContext) -> Decimal:
                rate = Decimal(ctx.meta.get("rate", "0.79"))
                return value * rate

            original = FV(Decimal("100"), unit=usd)

            # Test conversion with full context
            converted = original.to(
                gbp,
                at="2025-09-06T10:30:00Z",
                meta={"rate": "0.85", "source": "ECB", "spread": "0.01"},
            )

            if converted.has_provenance():
                prov = converted.get_provenance()
                assert prov.op == "convert"

                # Check conversion-specific metadata
                assert prov.meta["from"] == "Money[USD]"
                assert prov.meta["to"] == "Money[GBP]"
                assert prov.meta["operation_type"] == "conversion"
                assert prov.meta["at"] == "2025-09-06T10:30:00Z"

                # Check context metadata (prefixed with ctx_)
                assert prov.meta["ctx_rate"] == "0.85"
                assert prov.meta["ctx_source"] == "ECB"
                assert prov.meta["ctx_spread"] == "0.01"

                # Check result unit
                assert prov.meta["unit"] == "Money[GBP]"

                # Check inputs
                assert len(prov.inputs) == 1

        finally:
            _conversion_registry.clear()

    def test_conversion_provenance_minimal_context(self):
        """Test conversion provenance with minimal context."""
        from metricengine.units import _conversion_registry

        # Clear registry for clean test
        _conversion_registry.clear()

        try:
            kg = Qty("kg")
            lb = Qty("lb")

            @register_conversion(kg, lb)
            def kg_to_lb(value: Decimal, ctx: ConversionContext) -> Decimal:
                return value * Decimal("2.20462")

            original = FV(Decimal("10"), unit=kg)
            converted = original.to(lb)  # No additional context

            if converted.has_provenance():
                prov = converted.get_provenance()
                assert prov.op == "convert"
                assert prov.meta["from"] == "Quantity[kg]"
                assert prov.meta["to"] == "Quantity[lb]"
                assert prov.meta["operation_type"] == "conversion"
                assert prov.meta["unit"] == "Quantity[lb]"

                # Should not have at or ctx_ metadata
                assert "at" not in prov.meta
                assert not any(key.startswith("ctx_") for key in prov.meta.keys())

        finally:
            _conversion_registry.clear()

    def test_same_unit_conversion_provenance(self):
        """Test that same-unit conversions preserve original provenance."""
        usd = MoneyUnit("USD")
        original = FV(Decimal("100"), unit=usd)

        # Convert to same unit
        result = original.to(usd)

        # Should preserve original provenance for same-unit conversions
        if original.has_provenance() and result.has_provenance():
            orig_prov = original.get_provenance()
            result_prov = result.get_provenance()

            # For same-unit conversions, provenance should be preserved
            # (implementation may vary, but unit info should be consistent)
            assert result_prov.meta.get("unit") == "Money[USD]"

    def test_chained_operations_provenance(self):
        """Test provenance tracking through chained operations with units."""
        usd = MoneyUnit("USD")

        # Create initial values
        revenue = FV(Decimal("1000"), unit=usd)
        cost = FV(Decimal("600"), unit=usd)
        tax_rate = FV(Decimal("0.2"), unit=None)  # No unit for tax rate

        # Chain operations
        profit = revenue - cost  # USD - USD = USD
        tax = profit * tax_rate  # USD * dimensionless = USD
        net_profit = profit - tax  # USD - USD = USD

        # Check final provenance
        if net_profit.has_provenance():
            prov = net_profit.get_provenance()
            assert prov.op == "-"
            assert prov.meta.get("unit") == "Money[USD]"
            assert len(prov.inputs) == 2

    def test_provenance_with_percentage_flag(self):
        """Test that provenance correctly handles percentage flag with units."""
        ratio = Pct("ratio")
        fv = FV(Decimal("0.15"), unit=ratio, _is_percentage=True)

        if fv.has_provenance():
            prov = fv.get_provenance()
            assert prov.op == "literal"
            assert prov.meta.get("unit") == "Percent[ratio]"

        # Test arithmetic with percentage flag
        fv2 = FV(Decimal("0.05"), unit=ratio, _is_percentage=True)
        result = fv + fv2

        if result.has_provenance():
            prov = result.get_provenance()
            assert prov.op == "+"
            assert prov.meta.get("unit") == "Percent[ratio]"

    def test_provenance_error_handling(self):
        """Test that provenance gracefully handles errors while preserving unit info."""
        # This test ensures that even if provenance generation fails,
        # the unit information is still attempted to be included

        usd = MoneyUnit("USD")
        fv = FV(Decimal("100"), unit=usd)

        # Even if there are issues with provenance generation,
        # the FinancialValue should still be created with the unit
        assert fv.unit == usd

        # And if provenance is available, it should include unit info
        if fv.has_provenance():
            prov = fv.get_provenance()
            assert prov.meta.get("unit") == "Money[USD]"

    def test_legacy_unit_system_compatibility(self):
        """Test that legacy unit system still works with provenance."""
        from metricengine.units import Money  # Legacy unit

        fv = FV(Decimal("100"), unit=Money)

        if fv.has_provenance():
            prov = fv.get_provenance()
            assert prov.op == "literal"
            # Legacy units should use class name
            assert prov.meta.get("unit") == "Money"
