#!/usr/bin/env python3
"""
Demonstration of the Metric Engine Unit System

This example shows how to use the unit system for type-safe financial
calculations with explicit unit conversions.
"""

from decimal import Decimal

from metricengine import (
    ConversionContext,
    ConversionPolicy,
    FinancialValue,
    MoneyUnit,
    Pct,
    Qty,
    register_conversion,
    use_conversions,
)


def main():
    print("=== Metric Engine Unit System Demo ===\n")

    # 1. Basic Unit Creation
    print("1. Creating Units")
    print("-" * 20)

    usd = MoneyUnit("USD")
    gbp = MoneyUnit("GBP")
    eur = MoneyUnit("EUR")

    kg = Qty("kg")
    lb = Qty("lb")

    ratio = Pct("ratio")
    percent = Pct("percent")

    print(f"Currency units: {usd}, {gbp}, {eur}")
    print(f"Weight units: {kg}, {lb}")
    print(f"Percentage units: {ratio}, {percent}")
    print()

    # 2. Unit-Aware FinancialValues
    print("2. Unit-Aware FinancialValues")
    print("-" * 30)

    price_usd = FinancialValue(Decimal("100.00"), unit=usd)
    price_gbp = FinancialValue(Decimal("79.00"), unit=gbp)
    weight_kg = FinancialValue(Decimal("10.5"), unit=kg)
    tax_rate = FinancialValue(Decimal("0.15"), unit=ratio)

    print(f"USD Price: {price_usd}")
    print(f"GBP Price: {price_gbp}")
    print(f"Weight: {weight_kg}")
    print(f"Tax Rate: {tax_rate}")
    print()

    # 3. Unit Safety in Arithmetic
    print("3. Unit Safety in Arithmetic")
    print("-" * 28)

    # This works - same units
    total_usd = price_usd + FinancialValue(Decimal("50.00"), unit=usd)
    print(f"USD total: {price_usd} + $50.00 = {total_usd}")

    # This would raise an error - uncomment to see
    # try:
    #     invalid = price_usd + price_gbp  # Different units!
    # except ValueError as e:
    #     print(f"Error: {e}")

    print("✓ Unit safety prevents mixing incompatible units")
    print()

    # 4. Registering Conversions
    print("4. Registering Unit Conversions")
    print("-" * 31)

    @register_conversion(usd, gbp)
    def usd_to_gbp(value: Decimal, ctx: ConversionContext) -> Decimal:
        """Convert USD to GBP using example rate."""
        rate = Decimal("0.79")
        print(f"  Converting ${value} USD to GBP at rate {rate}")
        return value * rate

    @register_conversion(gbp, usd)
    def gbp_to_usd(value: Decimal, ctx: ConversionContext) -> Decimal:
        """Convert GBP to USD using example rate."""
        rate = Decimal("1.27")
        print(f"  Converting £{value} GBP to USD at rate {rate}")
        return value * rate

    @register_conversion(usd, eur)
    def usd_to_eur(value: Decimal, ctx: ConversionContext) -> Decimal:
        """Convert USD to EUR using example rate."""
        rate = Decimal("0.85")
        print(f"  Converting ${value} USD to EUR at rate {rate}")
        return value * rate

    @register_conversion(kg, lb)
    def kg_to_lb(value: Decimal, ctx: ConversionContext) -> Decimal:
        """Convert kg to lb."""
        rate = Decimal("2.20462")
        print(f"  Converting {value} kg to lb at rate {rate}")
        return value * rate

    print("✓ Registered USD↔GBP, USD→EUR, and kg→lb conversions")
    print()

    # 5. Performing Conversions
    print("5. Performing Unit Conversions")
    print("-" * 30)

    # Direct conversion
    price_gbp_converted = price_usd.to(gbp)
    print(f"Direct: {price_usd} → {price_gbp_converted}")

    # Multi-hop conversion (USD → GBP → USD)
    price_usd_roundtrip = price_usd.to(gbp).to(usd)
    print(f"Round-trip: {price_usd} → GBP → {price_usd_roundtrip}")

    # Weight conversion
    weight_lb = weight_kg.to(lb)
    print(f"Weight: {weight_kg} → {weight_lb}")
    print()

    # 6. Multi-Hop Conversions
    print("6. Multi-Hop Conversions")
    print("-" * 25)

    # This will automatically find the path USD → GBP → USD → EUR
    # (since we don't have direct GBP → EUR)
    try:
        # First convert some GBP to EUR via USD
        gbp_amount = FinancialValue(Decimal("100"), unit=gbp)
        eur_amount = gbp_amount.to(eur)
        print(f"Multi-hop: {gbp_amount} → {eur_amount}")
        print("  (Path: GBP → USD → EUR)")
    except Exception as e:
        print(f"Multi-hop conversion failed: {e}")
    print()

    # 7. Conversion Policies
    print("7. Conversion Policies")
    print("-" * 22)

    # Strict policy (default) - raises on missing conversions
    print("Strict policy (default):")
    try:
        # This will fail because we don't have EUR → GBP
        eur_amount = FinancialValue(Decimal("100"), unit=eur)
        gbp_from_eur = eur_amount.to(gbp)
        print(f"  {eur_amount} → {gbp_from_eur}")
    except Exception as e:
        print(f"  Error: {type(e).__name__}: {str(e)[:60]}...")

    # Permissive policy - returns original on missing conversions
    print("\nPermissive policy:")
    permissive_policy = ConversionPolicy(strict=False, allow_paths=True)
    with use_conversions(permissive_policy):
        eur_amount = FinancialValue(Decimal("100"), unit=eur)
        result = eur_amount.to(gbp)  # Should return original EUR amount
        print(f"  {eur_amount} → {result} (returned original)")
    print()

    # 8. Conversion with Context
    print("8. Conversion with Context")
    print("-" * 26)

    @register_conversion(eur, gbp)
    def eur_to_gbp_with_context(value: Decimal, ctx: ConversionContext) -> Decimal:
        """Convert EUR to GBP using context for rate lookup."""
        # Check if rate is provided in context
        if "rate" in ctx.meta:
            rate = Decimal(ctx.meta["rate"])
            print(f"  Using context rate: {rate}")
        else:
            rate = Decimal("0.93")  # Default rate
            print(f"  Using default rate: {rate}")

        return value * rate

    # Convert with context metadata
    eur_amount = FinancialValue(Decimal("100"), unit=eur)
    gbp_with_context = eur_amount.to(
        gbp, at="2025-09-06T10:30:00Z", meta={"rate": "0.95", "source": "ECB"}
    )
    print(f"With context: {eur_amount} → {gbp_with_context}")
    print()

    # 9. Summary
    print("9. Summary")
    print("-" * 10)
    print("✓ Created type-safe units for different measurement categories")
    print("✓ Demonstrated unit safety in arithmetic operations")
    print("✓ Registered and used unit conversions")
    print("✓ Showed multi-hop conversion path finding")
    print("✓ Explored strict vs permissive conversion policies")
    print("✓ Used conversion context for dynamic rate lookup")
    print("\nThe unit system provides type safety, explicit conversions,")
    print("and flexible policies for robust financial calculations!")


if __name__ == "__main__":
    main()
