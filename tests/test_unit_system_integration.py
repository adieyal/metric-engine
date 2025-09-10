"""
Comprehensive integration tests for the unit type system.

This module tests the complete unit-aware FinancialValue system through complex
multi-step financial calculations, conversion workflows, and policy interactions.

These tests verify that:
1. End-to-end currency conversion workflows work correctly
2. Multi-currency financial calculations handle units properly
3. Policy inheritance and scoping work in complex conversion scenarios
4. Conversion registry works with multiple unit types (Money, Quantity, Percent)
5. Provenance tracking works through conversion chains
6. Performance stays within acceptable limits for conversion operations

Requirements covered: 10.1, 10.2, 10.3, 10.4, 10.5
"""

import time
from decimal import Decimal

import pytest

from metricengine import Engine
from metricengine import FinancialValue as FV
from metricengine.policy import Policy
from metricengine.provenance import explain, to_trace_json
from metricengine.registry import calc, clear_registry
from metricengine.units import (
    ConversionContext,
    ConversionPolicy,
    MoneyUnit,
    Pct,
    Qty,
    _conversion_registry,
    get_conversion,
    list_conversions,
    register_conversion,
    use_conversions,
)


class TestEndToEndCurrencyConversionWorkflows:
    """Test complete currency conversion workflows from start to finish."""

    def setup_method(self):
        """Set up conversion registry for each test."""
        _conversion_registry.clear()

        # Set up common currency conversions
        usd = MoneyUnit("USD")
        eur = MoneyUnit("EUR")
        gbp = MoneyUnit("GBP")
        jpy = MoneyUnit("JPY")

        @register_conversion(usd, eur)
        def usd_to_eur(value: Decimal, ctx: ConversionContext) -> Decimal:
            rate = Decimal(ctx.meta.get("rate", "0.85"))
            return value * rate

        @register_conversion(eur, usd)
        def eur_to_usd(value: Decimal, ctx: ConversionContext) -> Decimal:
            rate = Decimal(ctx.meta.get("rate", "1.18"))
            return value * rate

        @register_conversion(usd, gbp)
        def usd_to_gbp(value: Decimal, ctx: ConversionContext) -> Decimal:
            rate = Decimal(ctx.meta.get("rate", "0.79"))
            return value * rate

        @register_conversion(gbp, usd)
        def gbp_to_usd(value: Decimal, ctx: ConversionContext) -> Decimal:
            rate = Decimal(ctx.meta.get("rate", "1.27"))
            return value * rate

        @register_conversion(usd, jpy)
        def usd_to_jpy(value: Decimal, ctx: ConversionContext) -> Decimal:
            rate = Decimal(ctx.meta.get("rate", "110.0"))
            return value * rate

        @register_conversion(jpy, usd)
        def jpy_to_usd(value: Decimal, ctx: ConversionContext) -> Decimal:
            rate = Decimal(ctx.meta.get("rate", "0.0091"))
            return value * rate

    def teardown_method(self):
        """Clean up conversion registry after each test."""
        _conversion_registry.clear()

    def test_simple_currency_conversion_workflow(self):
        """Test basic currency conversion from USD to EUR."""
        usd = MoneyUnit("USD")
        eur = MoneyUnit("EUR")

        # Create USD amount
        amount_usd = FV(Decimal("1000.00"), unit=usd)

        # Convert to EUR with specific rate
        amount_eur = amount_usd.to(eur, meta={"rate": "0.85"})

        # Verify conversion
        assert amount_eur.as_decimal() == Decimal("850.00")
        assert amount_eur.unit == eur
        assert amount_eur.policy == amount_usd.policy

        # Verify provenance was created
        assert amount_eur.has_provenance()
        prov = amount_eur.get_provenance()
        assert prov.op == "convert"
        assert "from" in prov.meta
        assert "to" in prov.meta
        assert prov.meta["from"] == "Money[USD]"
        assert prov.meta["to"] == "Money[EUR]"

    def test_round_trip_conversion_workflow(self):
        """Test round-trip conversion maintains approximate value."""
        usd = MoneyUnit("USD")
        eur = MoneyUnit("EUR")

        # Start with USD
        original = FV(Decimal("1000.00"), unit=usd)

        # Convert to EUR and back
        eur_amount = original.to(eur, meta={"rate": "0.85"})
        back_to_usd = eur_amount.to(usd, meta={"rate": "1.18"})

        # Should be approximately the same (within rounding)
        # 1000 * 0.85 * 1.18 = 1003
        assert back_to_usd.as_decimal() == Decimal("1003.00")
        assert back_to_usd.unit == usd

        # Both conversions should have provenance
        assert eur_amount.has_provenance()
        assert back_to_usd.has_provenance()

    def test_multi_currency_portfolio_conversion(self):
        """Test converting a portfolio with multiple currencies."""
        usd = MoneyUnit("USD")
        eur = MoneyUnit("EUR")
        gbp = MoneyUnit("GBP")
        jpy = MoneyUnit("JPY")

        # Create portfolio in different currencies
        portfolio = {
            "us_stocks": FV(Decimal("5000.00"), unit=usd),
            "eu_bonds": FV(Decimal("3000.00"), unit=eur),
            "uk_property": FV(Decimal("2000.00"), unit=gbp),
            "jp_cash": FV(Decimal("100000.00"), unit=jpy),
        }

        # Convert everything to USD for reporting
        usd_portfolio = {}
        for name, amount in portfolio.items():
            if amount.unit == usd:
                usd_portfolio[name] = amount
            else:
                usd_portfolio[name] = amount.to(usd)

        # Verify all conversions
        assert usd_portfolio["us_stocks"].as_decimal() == Decimal("5000.00")
        assert usd_portfolio["eu_bonds"].as_decimal() == Decimal(
            "3540.00"
        )  # 3000 * 1.18
        assert usd_portfolio["uk_property"].as_decimal() == Decimal(
            "2540.00"
        )  # 2000 * 1.27
        assert usd_portfolio["jp_cash"].as_decimal() == Decimal(
            "910.00"
        )  # 100000 * 0.0091

        # Calculate total portfolio value
        total = sum(amount for amount in usd_portfolio.values())
        assert total.as_decimal() == Decimal("11990.00")
        assert total.unit == usd

    def test_time_series_conversion_workflow(self):
        """Test conversion with different rates over time."""
        usd = MoneyUnit("USD")
        eur = MoneyUnit("EUR")

        amount = FV(Decimal("1000.00"), unit=usd)

        # Convert with different rates for different dates
        jan_rate = amount.to(eur, at="2025-01-01T00:00:00Z", meta={"rate": "0.85"})
        feb_rate = amount.to(eur, at="2025-02-01T00:00:00Z", meta={"rate": "0.87"})
        mar_rate = amount.to(eur, at="2025-03-01T00:00:00Z", meta={"rate": "0.83"})

        # Verify different conversion results
        assert jan_rate.as_decimal() == Decimal("850.00")
        assert feb_rate.as_decimal() == Decimal("870.00")
        assert mar_rate.as_decimal() == Decimal("830.00")

        # All should have timestamp in provenance
        for converted in [jan_rate, feb_rate, mar_rate]:
            assert converted.has_provenance()
            prov = converted.get_provenance()
            assert "at" in prov.meta


class TestMultiCurrencyFinancialCalculations:
    """Test financial calculations involving multiple currencies with proper unit handling."""

    def setup_method(self):
        """Set up conversion registry and calculations for each test."""
        _conversion_registry.clear()

        # Set up currency conversions
        usd = MoneyUnit("USD")
        eur = MoneyUnit("EUR")
        gbp = MoneyUnit("GBP")

        @register_conversion(eur, usd)
        def eur_to_usd(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("1.18")

        @register_conversion(gbp, usd)
        def gbp_to_usd(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("1.27")

        @register_conversion(usd, eur)
        def usd_to_eur(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("0.85")

        @register_conversion(usd, gbp)
        def usd_to_gbp(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("0.79")

        # Set up calculation registry
        from metricengine.registry import _dependencies, _registry

        self.original_registry = _registry.copy()
        self.original_dependencies = _dependencies.copy()
        clear_registry()

        @calc("total_revenue", depends_on=("us_revenue", "eu_revenue", "uk_revenue"))
        def total_revenue(us_revenue, eu_revenue, uk_revenue):
            # Convert all to USD for calculation
            us_usd = us_revenue  # Already in USD
            eu_usd = eu_revenue.to(MoneyUnit("USD"))
            uk_usd = uk_revenue.to(MoneyUnit("USD"))
            return us_usd + eu_usd + uk_usd

        @calc("profit_margin", depends_on=("profit", "revenue"))
        def profit_margin(profit, revenue):
            return (profit / revenue).as_percentage()

    def teardown_method(self):
        """Clean up registries after each test."""
        _conversion_registry.clear()

        # Restore calculation registry
        from metricengine.registry import _dependencies, _registry

        clear_registry()
        _registry.update(self.original_registry)
        _dependencies.update(self.original_dependencies)

    def test_multi_currency_revenue_calculation(self):
        """Test calculating total revenue from multiple currencies."""
        usd = MoneyUnit("USD")
        eur = MoneyUnit("EUR")
        gbp = MoneyUnit("GBP")

        engine = Engine()

        # Revenue in different currencies
        inputs = {
            "us_revenue": FV(Decimal("10000.00"), unit=usd),
            "eu_revenue": FV(Decimal("8000.00"), unit=eur),
            "uk_revenue": FV(Decimal("5000.00"), unit=gbp),
        }

        # Calculate total revenue (should convert to USD)
        total = engine.calculate("total_revenue", inputs)

        # Verify calculation: 10000 + (8000 * 1.18) + (5000 * 1.27)
        expected = Decimal("10000.00") + Decimal("9440.00") + Decimal("6350.00")
        assert total.as_decimal() == expected  # 25790.00
        assert total.unit == usd

        # Verify provenance includes conversion information
        assert total.has_provenance()
        prov = total.get_provenance()
        assert prov.op == "calc:total_revenue"

    def test_multi_currency_profit_margin_calculation(self):
        """Test calculating profit margin with multi-currency inputs."""
        usd = MoneyUnit("USD")
        eur = MoneyUnit("EUR")

        engine = Engine()

        # Profit in EUR, Revenue in USD - should handle conversion
        profit_eur = FV(Decimal("2000.00"), unit=eur)
        revenue_usd = FV(Decimal("10000.00"), unit=usd)

        # Convert profit to USD for margin calculation
        profit_usd = profit_eur.to(usd)  # 2000 * 1.18 = 2360

        margin = engine.calculate(
            "profit_margin", {"profit": profit_usd, "revenue": revenue_usd}
        )

        # Verify margin calculation: (2360 / 10000) * 100 = 23.6%
        assert margin.as_decimal() == Decimal("23.60")
        # The as_percentage() method returns legacy Percent unit for backward compatibility
        from metricengine.units import Percent

        assert margin.unit == Percent  # Should be legacy Percent unit
        assert margin._is_percentage is True

    def test_currency_arithmetic_safety(self):
        """Test that arithmetic operations enforce currency compatibility."""
        usd = MoneyUnit("USD")
        eur = MoneyUnit("EUR")

        amount_usd = FV(Decimal("1000.00"), unit=usd)
        amount_eur = FV(Decimal("850.00"), unit=eur)

        # Direct addition should fail due to incompatible units
        with pytest.raises(ValueError, match="Incompatible units for \\+"):
            amount_usd + amount_eur

        # Must convert first
        amount_eur_as_usd = amount_eur.to(usd)
        total = amount_usd + amount_eur_as_usd

        assert total.as_decimal() == Decimal("2003.00")  # 1000 + (850 * 1.18)
        assert total.unit == usd

    def test_mixed_unit_financial_calculation(self):
        """Test financial calculation mixing currencies and percentages."""
        usd = MoneyUnit("USD")
        eur = MoneyUnit("EUR")
        pct = Pct("ratio")

        # Base amount in USD
        principal = FV(Decimal("10000.00"), unit=usd)

        # Interest rate as percentage
        interest_rate = FV(Decimal("0.05"), unit=pct)  # 5%

        # Fee in EUR
        fee_eur = FV(Decimal("100.00"), unit=eur)
        fee_usd = fee_eur.to(usd)  # Convert to USD

        # Calculate: principal * (1 + interest_rate) - fee
        interest_amount = principal * interest_rate
        gross_amount = principal + interest_amount
        net_amount = gross_amount - fee_usd

        # Verify calculation
        # Interest: 10000 * 0.05 = 500
        # Gross: 10000 + 500 = 10500
        # Fee in USD: 100 * 1.18 = 118
        # Net: 10500 - 118 = 10382
        assert net_amount.as_decimal() == Decimal("10382.00")
        assert net_amount.unit == usd


class TestPolicyInheritanceAndScoping:
    """Test policy inheritance and scoping in complex conversion scenarios."""

    def setup_method(self):
        """Set up conversion registry for each test."""
        _conversion_registry.clear()

        usd = MoneyUnit("USD")
        eur = MoneyUnit("EUR")

        @register_conversion(usd, eur)
        def usd_to_eur(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("0.85")

        @register_conversion(eur, usd)
        def eur_to_usd(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("1.18")

    def teardown_method(self):
        """Clean up conversion registry after each test."""
        _conversion_registry.clear()

    def test_conversion_preserves_policy(self):
        """Test that unit conversion preserves the original policy."""
        usd = MoneyUnit("USD")
        eur = MoneyUnit("EUR")

        # Create custom policy
        custom_policy = Policy(decimal_places=4, currency_symbol="$")

        # Create FinancialValue with custom policy
        amount = FV(Decimal("1000.123456"), unit=usd, policy=custom_policy)

        # Convert to EUR
        converted = amount.to(eur)

        # Verify policy is preserved
        assert converted.policy == custom_policy
        assert converted.policy.decimal_places == 4
        assert converted.policy.currency_symbol == "$"

        # Verify formatting uses the preserved policy
        formatted = converted.as_str()
        assert "850.1049" in formatted  # 1000.123456 * 0.85, rounded to 4 places

    def test_conversion_policy_scoping(self):
        """Test conversion policy scoping with context managers."""
        usd = MoneyUnit("USD")
        eur = MoneyUnit("EUR")

        amount = FV(Decimal("1000.00"), unit=usd)

        # Test strict mode (default)
        converted_strict = amount.to(eur)
        assert converted_strict.as_decimal() == Decimal("850.00")

        # Test permissive mode
        permissive_policy = ConversionPolicy(strict=False, allow_paths=True)

        with use_conversions(permissive_policy):
            # This should still work since we have the conversion registered
            converted_permissive = amount.to(eur)
            assert converted_permissive.as_decimal() == Decimal("850.00")

            # Test with missing conversion (should return original in permissive mode)
            jpy = MoneyUnit("JPY")
            try:
                # This should fail even in permissive mode since we don't have USD->JPY
                # But the error handling might be different
                converted_missing = amount.to(jpy)
                # If it doesn't raise, it should return original value
                assert converted_missing.unit == usd  # Should keep original unit
            except KeyError:
                # This is also acceptable behavior
                pass

    def test_nested_conversion_policy_scoping(self):
        """Test nested conversion policy scoping."""
        usd = MoneyUnit("USD")
        eur = MoneyUnit("EUR")

        amount = FV(Decimal("1000.00"), unit=usd)

        # Outer scope: permissive
        outer_policy = ConversionPolicy(strict=False, allow_paths=True)

        with use_conversions(outer_policy):
            # Inner scope: strict
            inner_policy = ConversionPolicy(strict=True, allow_paths=False)

            with use_conversions(inner_policy):
                # Should use inner (strict) policy
                converted = amount.to(eur)
                assert converted.as_decimal() == Decimal("850.00")

            # Back to outer (permissive) policy
            converted_outer = amount.to(eur)
            assert converted_outer.as_decimal() == Decimal("850.00")

    def test_policy_inheritance_in_arithmetic(self):
        """Test policy inheritance in arithmetic operations with converted values."""
        usd = MoneyUnit("USD")
        eur = MoneyUnit("EUR")

        # Create amounts with different policies
        policy1 = Policy(decimal_places=2)
        policy2 = Policy(decimal_places=4)

        amount1 = FV(Decimal("1000.00"), unit=usd, policy=policy1)
        amount2_eur = FV(Decimal("500.00"), unit=eur, policy=policy2)

        # Convert second amount to USD
        amount2_usd = amount2_eur.to(usd)  # Should preserve policy2

        # Add them (policy resolution will determine result policy)
        total = amount1 + amount2_usd

        # Verify the calculation
        expected = Decimal("1000.00") + (Decimal("500.00") * Decimal("1.18"))
        assert total.as_decimal() == expected  # 1590.00
        assert total.unit == usd


class TestConversionRegistryMultipleUnitTypes:
    """Test conversion registry with multiple unit types (Money, Quantity, Percent)."""

    def setup_method(self):
        """Set up conversion registry with multiple unit types."""
        _conversion_registry.clear()

        # Money conversions
        usd = MoneyUnit("USD")
        eur = MoneyUnit("EUR")

        @register_conversion(usd, eur)
        def usd_to_eur(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("0.85")

        # Quantity conversions
        kg = Qty("kg")
        lb = Qty("lb")

        @register_conversion(kg, lb)
        def kg_to_lb(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("2.20462")

        @register_conversion(lb, kg)
        def lb_to_kg(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("0.453592")

        # Percent conversions
        ratio = Pct("ratio")
        bp = Pct("bp")  # basis points

        @register_conversion(ratio, bp)
        def ratio_to_bp(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("10000")

        @register_conversion(bp, ratio)
        def bp_to_ratio(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("0.0001")

        # Cross-category conversion (unusual but possible)
        shares = Qty("shares")

        @register_conversion(usd, shares)
        def usd_to_shares(value: Decimal, ctx: ConversionContext) -> Decimal:
            # Convert dollars to shares at given price
            share_price = Decimal(ctx.meta.get("share_price", "10.00"))
            return value / share_price

    def teardown_method(self):
        """Clean up conversion registry after each test."""
        _conversion_registry.clear()

    def test_money_unit_conversions(self):
        """Test money unit conversions work correctly."""
        usd = MoneyUnit("USD")
        eur = MoneyUnit("EUR")

        amount = FV(Decimal("1000.00"), unit=usd)
        converted = amount.to(eur)

        assert converted.as_decimal() == Decimal("850.00")
        assert converted.unit == eur

    def test_quantity_unit_conversions(self):
        """Test quantity unit conversions work correctly."""
        kg = Qty("kg")
        lb = Qty("lb")

        weight_kg = FV(Decimal("10.00"), unit=kg)
        weight_lb = weight_kg.to(lb)

        assert weight_lb.as_decimal() == Decimal(
            "22.05"
        )  # Rounded to 2 decimal places by default policy
        assert weight_lb.unit == lb

        # Test round trip
        back_to_kg = weight_lb.to(kg)
        # Should be approximately 10 (within rounding)
        assert abs(back_to_kg.as_decimal() - Decimal("10.00")) < Decimal("0.01")

    def test_percent_unit_conversions(self):
        """Test percent unit conversions work correctly."""
        ratio = Pct("ratio")
        bp = Pct("bp")

        rate_ratio = FV(Decimal("0.0125"), unit=ratio)  # 1.25%
        rate_bp = rate_ratio.to(bp)

        assert rate_bp.as_decimal() == Decimal("125")  # 125 basis points
        assert rate_bp.unit == bp

        # Test round trip
        back_to_ratio = rate_bp.to(ratio)
        assert back_to_ratio.as_decimal() == Decimal(
            "0.01"
        )  # Rounded to 2 decimal places by default policy

    def test_cross_category_conversions(self):
        """Test conversions between different unit categories."""
        usd = MoneyUnit("USD")
        shares = Qty("shares")

        money = FV(Decimal("1000.00"), unit=usd)

        # Convert money to shares at $25 per share
        share_count = money.to(shares, meta={"share_price": "25.00"})

        assert share_count.as_decimal() == Decimal("40")  # 1000 / 25
        assert share_count.unit == shares

    def test_registry_inspection(self):
        """Test that conversion registry can be inspected."""
        conversions = list_conversions()

        # Should have all registered conversions
        assert len(conversions) >= 6  # At least the ones we registered

        # Check specific conversions exist
        usd = MoneyUnit("USD")
        eur = MoneyUnit("EUR")
        kg = Qty("kg")
        lb = Qty("lb")

        assert (usd, eur) in conversions
        assert (kg, lb) in conversions
        assert (lb, kg) in conversions

        # Test getting specific conversion
        usd_eur_conversion = get_conversion(usd, eur)
        assert usd_eur_conversion.src == usd
        assert usd_eur_conversion.dst == eur

    def test_mixed_unit_type_calculations(self):
        """Test calculations involving multiple unit types."""
        # Create values with different unit types
        price_usd = FV(Decimal("50.00"), unit=MoneyUnit("USD"))
        weight_kg = FV(Decimal("2.5"), unit=Qty("kg"))
        tax_rate = FV(Decimal("0.08"), unit=Pct("ratio"))  # 8%

        # Convert weight to pounds for calculation
        weight_lb = weight_kg.to(Qty("lb"))

        # Calculate: price per pound * weight in pounds * (1 + tax_rate)
        price_per_lb = price_usd  # Assume price is per pound after conversion
        subtotal = price_per_lb * weight_lb.as_decimal()  # Mix units carefully
        tax_amount = subtotal * tax_rate
        total = subtotal + tax_amount

        # Verify calculation
        # Weight: 2.5 kg = 5.51155 lb
        # Subtotal: $50 * 5.51155 = $275.58 (approximately)
        # Tax: $275.58 * 0.08 = $22.05 (approximately)
        # Total: $275.58 + $22.05 = $297.63 (approximately)

        assert total.unit == MoneyUnit("USD")
        assert total.as_decimal() > Decimal("290.00")  # Approximate check
        assert total.as_decimal() < Decimal("300.00")


class TestProvenanceTrackingThroughConversions:
    """Test provenance tracking through conversion chains."""

    def setup_method(self):
        """Set up conversion registry for provenance testing."""
        _conversion_registry.clear()

        # Set up conversion chain: USD -> EUR -> GBP
        usd = MoneyUnit("USD")
        eur = MoneyUnit("EUR")
        gbp = MoneyUnit("GBP")

        @register_conversion(usd, eur)
        def usd_to_eur(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("0.85")

        @register_conversion(eur, gbp)
        def eur_to_gbp(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("0.93")

        @register_conversion(usd, gbp)
        def usd_to_gbp_direct(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("0.79")

    def teardown_method(self):
        """Clean up conversion registry after each test."""
        _conversion_registry.clear()

    def test_single_conversion_provenance(self):
        """Test provenance tracking for single conversion."""
        usd = MoneyUnit("USD")
        eur = MoneyUnit("EUR")

        original = FV(Decimal("1000.00"), unit=usd)
        converted = original.to(eur, at="2025-09-06T10:30:00Z", meta={"rate": "0.85"})

        # Check provenance exists
        assert converted.has_provenance()
        prov = converted.get_provenance()

        # Check provenance details
        assert prov.op == "convert"
        assert len(prov.inputs) == 1
        assert prov.inputs[0] == original.get_provenance().id

        # Check metadata
        assert "from" in prov.meta
        assert "to" in prov.meta
        assert "at" in prov.meta
        assert prov.meta["from"] == "Money[USD]"
        assert prov.meta["to"] == "Money[EUR]"
        assert prov.meta["at"] == "2025-09-06T10:30:00Z"

    def test_conversion_chain_provenance(self):
        """Test provenance tracking through conversion chain."""
        usd = MoneyUnit("USD")
        eur = MoneyUnit("EUR")
        gbp = MoneyUnit("GBP")

        # Create conversion chain: USD -> EUR -> GBP
        original = FV(Decimal("1000.00"), unit=usd)
        step1 = original.to(eur, meta={"rate": "0.85", "source": "ECB"})
        step2 = step1.to(gbp, meta={"rate": "0.93", "source": "BOE"})

        # Check each step has provenance
        assert original.has_provenance()
        assert step1.has_provenance()
        assert step2.has_provenance()

        # Check final provenance
        final_prov = step2.get_provenance()
        assert final_prov.op == "convert"
        assert "from" in final_prov.meta
        assert "to" in final_prov.meta
        assert final_prov.meta["from"] == "Money[EUR]"
        assert final_prov.meta["to"] == "Money[GBP]"

        # Check provenance chain
        step1_prov = step1.get_provenance()
        assert step1_prov.op == "convert"
        assert step1_prov.meta["from"] == "Money[USD]"
        assert step1_prov.meta["to"] == "Money[EUR]"

    def test_arithmetic_with_converted_values_provenance(self):
        """Test provenance when doing arithmetic with converted values."""
        usd = MoneyUnit("USD")
        eur = MoneyUnit("EUR")

        # Add missing EUR to USD conversion for this test
        @register_conversion(eur, usd)
        def eur_to_usd_temp(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("1.18")

        # Create two amounts and convert one
        amount1 = FV(Decimal("1000.00"), unit=usd)
        amount2_eur = FV(Decimal("500.00"), unit=eur)
        amount2_usd = amount2_eur.to(usd)

        # Add them
        total = amount1 + amount2_usd

        # Check provenance
        assert total.has_provenance()
        total_prov = total.get_provenance()
        assert total_prov.op == "+"
        assert len(total_prov.inputs) == 2

        # The inputs should include both the original amount1 and converted amount2
        input_ids = set(total_prov.inputs)
        assert amount1.get_provenance().id in input_ids
        assert amount2_usd.get_provenance().id in input_ids

    def test_provenance_export_with_conversions(self):
        """Test exporting provenance that includes conversions."""
        usd = MoneyUnit("USD")
        eur = MoneyUnit("EUR")

        original = FV(Decimal("1000.00"), unit=usd)
        converted = original.to(eur, at="2025-09-06T10:30:00Z")

        # Export provenance to JSON
        trace_json = to_trace_json(converted)

        # Check JSON structure
        assert "root" in trace_json
        assert "nodes" in trace_json
        assert isinstance(trace_json["nodes"], dict)

        # Check that conversion node is included
        conversion_node = None
        for node_id, node_data in trace_json["nodes"].items():
            if node_data["op"] == "convert":
                conversion_node = node_data
                break

        assert conversion_node is not None
        assert "from" in conversion_node["meta"]
        assert "to" in conversion_node["meta"]
        assert conversion_node["meta"]["from"] == "Money[USD]"
        assert conversion_node["meta"]["to"] == "Money[EUR]"

    def test_provenance_explanation_with_conversions(self):
        """Test human-readable explanation includes conversion information."""
        usd = MoneyUnit("USD")
        eur = MoneyUnit("EUR")

        original = FV(Decimal("1000.00"), unit=usd)
        converted = original.to(eur)

        # Get explanation
        explanation = explain(converted, max_depth=10)

        # Should be a string with conversion information
        assert isinstance(explanation, str)
        assert len(explanation) > 0

        # Should mention conversion or units
        explanation_lower = explanation.lower()
        assert any(
            word in explanation_lower for word in ["convert", "usd", "eur", "money"]
        )


class TestConversionPerformance:
    """Test performance of conversion registry lookup and path finding."""

    def setup_method(self):
        """Set up large conversion registry for performance testing."""
        _conversion_registry.clear()

        # Create many currency conversions for performance testing
        currencies = [
            "USD",
            "EUR",
            "GBP",
            "JPY",
            "CAD",
            "AUD",
            "CHF",
            "CNY",
            "INR",
            "BRL",
        ]

        # Create conversions between all currency pairs (simplified rates)
        for i, from_curr in enumerate(currencies):
            for j, to_curr in enumerate(currencies):
                if i != j:  # Don't create self-conversions
                    from_unit = MoneyUnit(from_curr)
                    to_unit = MoneyUnit(to_curr)

                    # Use a simple rate based on currency indices
                    rate = Decimal("1.0") + (Decimal(str(j - i)) * Decimal("0.1"))
                    if rate <= 0:
                        rate = Decimal("0.5")

                    # Create a closure to capture the rate value
                    def make_converter(conversion_rate):
                        @register_conversion(from_unit, to_unit)
                        def convert_currency(
                            value: Decimal, ctx: ConversionContext
                        ) -> Decimal:
                            return value * conversion_rate

                        return convert_currency

                    make_converter(rate)

    def teardown_method(self):
        """Clean up conversion registry after each test."""
        _conversion_registry.clear()

    def test_direct_conversion_performance(self):
        """Test performance of direct conversions."""
        usd = MoneyUnit("USD")
        eur = MoneyUnit("EUR")

        amount = FV(Decimal("1000.00"), unit=usd)

        # Time multiple conversions
        iterations = 100
        start_time = time.perf_counter()

        for _ in range(iterations):
            converted = amount.to(eur)
            assert converted.unit == eur

        end_time = time.perf_counter()
        total_time = end_time - start_time

        # Should complete reasonably quickly
        assert total_time < 2.0  # Less than 2 seconds for 100 conversions

        avg_time_per_conversion = total_time / iterations
        assert avg_time_per_conversion < 0.02  # Less than 20ms per conversion

    def test_conversion_registry_lookup_performance(self):
        """Test performance of conversion registry lookups."""
        currencies = ["USD", "EUR", "GBP", "JPY", "CAD"]

        # Time multiple registry lookups
        iterations = 1000
        start_time = time.perf_counter()

        for i in range(iterations):
            from_curr = currencies[i % len(currencies)]
            to_curr = currencies[(i + 1) % len(currencies)]

            from_unit = MoneyUnit(from_curr)
            to_unit = MoneyUnit(to_curr)

            try:
                conversion = get_conversion(from_unit, to_unit)
                assert conversion is not None
            except KeyError:
                # Some conversions might not exist, that's okay
                pass

        end_time = time.perf_counter()
        total_time = end_time - start_time

        # Should complete very quickly
        assert total_time < 1.0  # Less than 1 second for 1000 lookups

        avg_time_per_lookup = total_time / iterations
        assert avg_time_per_lookup < 0.001  # Less than 1ms per lookup

    def test_large_conversion_registry_memory(self):
        """Test memory usage with large conversion registry."""
        # This is more of a smoke test - if we get here without OOM, we're good

        # Check registry size
        conversions = list_conversions()
        assert len(conversions) > 50  # Should have many conversions

        # Test that we can still do conversions efficiently
        usd = MoneyUnit("USD")
        eur = MoneyUnit("EUR")

        amount = FV(Decimal("1000.00"), unit=usd)
        converted = amount.to(eur)

        assert converted.unit == eur
        assert converted.as_decimal() > Decimal("0")  # Should have some positive value

    def test_conversion_with_complex_calculations(self):
        """Test performance of conversions within complex calculations."""
        usd = MoneyUnit("USD")
        eur = MoneyUnit("EUR")
        gbp = MoneyUnit("GBP")

        # Create multiple amounts in different currencies
        amounts = [
            FV(Decimal("1000.00"), unit=usd),
            FV(Decimal("850.00"), unit=eur),
            FV(Decimal("790.00"), unit=gbp),
        ]

        # Time conversion and summation
        iterations = 50
        start_time = time.perf_counter()

        for _ in range(iterations):
            # Convert all to USD and sum
            total = FV(Decimal("0"), unit=usd)
            for amount in amounts:
                if amount.unit == usd:
                    total = total + amount
                else:
                    converted = amount.to(usd)
                    total = total + converted

            assert total.unit == usd
            assert total.as_decimal() > Decimal("2000")  # Should be substantial

        end_time = time.perf_counter()
        total_time = end_time - start_time

        # Should complete reasonably quickly
        assert total_time < 5.0  # Less than 5 seconds for 50 iterations

        avg_time_per_iteration = total_time / iterations
        assert avg_time_per_iteration < 0.1  # Less than 100ms per complex calculation


if __name__ == "__main__":
    pytest.main([__file__])
