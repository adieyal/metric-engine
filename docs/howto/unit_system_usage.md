# Unit System Usage Guide

The Metric Engine unit system provides type-safe financial calculations with explicit unit handling and conversion capabilities. This guide demonstrates how to use the unit system effectively.

## Basic Unit Creation

### Using Helper Functions

The easiest way to create units is using the provided helper functions:

```python
from metricengine import MoneyUnit, Qty, Pct, FinancialValue

# Create currency units
usd = MoneyUnit("USD")
gbp = MoneyUnit("GBP")
eur = MoneyUnit("EUR")

# Create quantity units
kg = Qty("kg")
liters = Qty("L")
meters = Qty("m")

# Create percentage units
ratio = Pct()           # Default: Percent[ratio]
basis_points = Pct("bp") # Percent[bp]
```

### Using NewUnit Directly

For custom unit categories, use `NewUnit` directly:

```python
from metricengine import NewUnit

# Custom units
seats = NewUnit("Capacity", "seats")
hours = NewUnit("Time", "hours")
points = NewUnit("Score", "points")
```

## Creating Unit-Aware FinancialValues

```python
from metricengine import FinancialValue, MoneyUnit
from decimal import Decimal

usd = MoneyUnit("USD")
gbp = MoneyUnit("GBP")

# Create FinancialValues with units
price_usd = FinancialValue(Decimal("100.00"), unit=usd)
price_gbp = FinancialValue(Decimal("79.00"), unit=gbp)

print(price_usd)  # 100.00 (Money[USD])
print(price_gbp)  # 79.00 (Money[GBP])
```

## Unit Safety in Arithmetic

The unit system prevents unsafe operations between incompatible units:

```python
from metricengine import FinancialValue, MoneyUnit

usd = MoneyUnit("USD")
gbp = MoneyUnit("GBP")

price_usd = FinancialValue(100, unit=usd)
price_gbp = FinancialValue(79, unit=gbp)

# This works - same units
total_usd = price_usd + FinancialValue(50, unit=usd)
print(total_usd)  # 150.00 (Money[USD])

# This raises ValueError - incompatible units
try:
    invalid = price_usd + price_gbp  # ValueError!
except ValueError as e:
    print(f"Error: {e}")
```

## Unit Conversions

### Registering Conversions

Register conversion functions between units using the decorator:

```python
from metricengine import (
    MoneyUnit, register_conversion, ConversionContext
)
from decimal import Decimal

usd = MoneyUnit("USD")
gbp = MoneyUnit("GBP")
eur = MoneyUnit("EUR")

@register_conversion(usd, gbp)
def usd_to_gbp(value: Decimal, ctx: ConversionContext) -> Decimal:
    """Convert USD to GBP using fixed rate for example."""
    return value * Decimal("0.79")

@register_conversion(gbp, usd)
def gbp_to_usd(value: Decimal, ctx: ConversionContext) -> Decimal:
    """Convert GBP to USD."""
    return value * Decimal("1.27")

@register_conversion(usd, eur)
def usd_to_eur(value: Decimal, ctx: ConversionContext) -> Decimal:
    """Convert USD to EUR."""
    return value * Decimal("0.85")
```

### Using Dynamic Rates

Conversion functions can access external data through the context:

```python
@register_conversion(usd, gbp)
def usd_to_gbp_dynamic(value: Decimal, ctx: ConversionContext) -> Decimal:
    """Convert USD to GBP using dynamic rates."""
    # Get rate from context metadata
    if "rate" in ctx.meta:
        rate = Decimal(ctx.meta["rate"])
    else:
        # Fallback to API call or default rate
        rate = get_exchange_rate("USD", "GBP", ctx.at)

    return value * rate

def get_exchange_rate(from_currency: str, to_currency: str, at: str = None) -> Decimal:
    """Fetch exchange rate from external API."""
    # Implementation would call actual exchange rate API
    return Decimal("0.79")  # Placeholder
```

### Performing Conversions

Use the `to()` method to convert between units:

```python
from metricengine import FinancialValue, MoneyUnit

usd = MoneyUnit("USD")
gbp = MoneyUnit("GBP")

price_usd = FinancialValue(100, unit=usd)

# Convert to GBP
price_gbp = price_usd.to(gbp)
print(price_gbp)  # 79.00 (Money[GBP])

# Convert with context
price_gbp_with_context = price_usd.to(
    gbp,
    at="2025-09-06T10:30:00Z",
    meta={"rate": "0.78", "source": "ECB"}
)
```

### Multi-Hop Conversions

The system automatically finds conversion paths through intermediate units:

```python
# With USD->GBP and USD->EUR registered, GBP->EUR works automatically
gbp_amount = FinancialValue(100, unit=gbp)
eur_amount = gbp_amount.to(eur)  # Goes GBP->USD->EUR
```

## Conversion Policies

Control conversion behavior using policies:

```python
from metricengine import ConversionPolicy, use_conversions

# Strict policy (default) - raises on missing conversions
strict_policy = ConversionPolicy(strict=True, allow_paths=True)

# Permissive policy - returns original value on missing conversions
permissive_policy = ConversionPolicy(strict=False, allow_paths=True)

# Direct-only policy - no multi-hop conversions
direct_only = ConversionPolicy(strict=True, allow_paths=False)

# Use policy in context
with use_conversions(permissive_policy):
    # Missing conversions return original value instead of raising
    result = some_value.to(unknown_unit)
```

## Working with Quantities

The unit system works with any type of measurement:

```python
from metricengine import Qty, FinancialValue, register_conversion

# Weight units
kg = Qty("kg")
lb = Qty("lb")

@register_conversion(kg, lb)
def kg_to_lb(value: Decimal, ctx: ConversionContext) -> Decimal:
    return value * Decimal("2.20462")

@register_conversion(lb, kg)
def lb_to_kg(value: Decimal, ctx: ConversionContext) -> Decimal:
    return value * Decimal("0.453592")

# Use weight units
weight_kg = FinancialValue(10, unit=kg)
weight_lb = weight_kg.to(lb)
print(weight_lb)  # 22.0462 (Quantity[lb])
```

## Percentage Units

Handle different percentage representations:

```python
from metricengine import Pct, FinancialValue, register_conversion

ratio = Pct("ratio")      # Percent[ratio] - 0.15 = 15%
percent = Pct("percent")  # Percent[percent] - 15 = 15%
bp = Pct("bp")           # Percent[bp] - 1500 = 15%

@register_conversion(ratio, percent)
def ratio_to_percent(value: Decimal, ctx: ConversionContext) -> Decimal:
    return value * 100

@register_conversion(ratio, bp)
def ratio_to_bp(value: Decimal, ctx: ConversionContext) -> Decimal:
    return value * 10000

# Convert between percentage representations
rate_ratio = FinancialValue(Decimal("0.15"), unit=ratio)
rate_percent = rate_ratio.to(percent)  # 15.00 (Percent[percent])
rate_bp = rate_ratio.to(bp)           # 1500.00 (Percent[bp])
```

## Best Practices

### 1. Register Bidirectional Conversions

Always register conversions in both directions:

```python
@register_conversion(usd, gbp)
def usd_to_gbp(value: Decimal, ctx: ConversionContext) -> Decimal:
    return value * Decimal("0.79")

@register_conversion(gbp, usd)
def gbp_to_usd(value: Decimal, ctx: ConversionContext) -> Decimal:
    return value / Decimal("0.79")  # Or use inverse rate
```

### 2. Use Context for Dynamic Data

Leverage the conversion context for dynamic rates and metadata:

```python
@register_conversion(usd, gbp)
def usd_to_gbp_with_context(value: Decimal, ctx: ConversionContext) -> Decimal:
    # Use timestamp for historical rates
    if ctx.at:
        rate = get_historical_rate("USD", "GBP", ctx.at)
    else:
        rate = get_current_rate("USD", "GBP")

    # Log conversion for audit trail
    if "audit" in ctx.meta:
        log_conversion("USD", "GBP", value, rate, ctx.meta["audit"])

    return value * rate
```

### 3. Handle Conversion Errors Gracefully

Use appropriate policies for your use case:

```python
# For user-facing calculations - use permissive mode
with use_conversions(ConversionPolicy(strict=False)):
    result = calculate_total_in_base_currency(mixed_currency_values)

# For critical financial operations - use strict mode (default)
result = critical_calculation.to(required_currency)  # Raises on missing conversion
```

### 4. Organize Units by Domain

Create domain-specific unit modules:

```python
# currencies.py
from metricengine import MoneyUnit

USD = MoneyUnit("USD")
GBP = MoneyUnit("GBP")
EUR = MoneyUnit("EUR")
JPY = MoneyUnit("JPY")

# measurements.py
from metricengine import Qty

KG = Qty("kg")
LB = Qty("lb")
LITER = Qty("L")
GALLON = Qty("gal")
```

### 5. Test Conversion Round-Trips

Ensure conversion accuracy with round-trip tests:

```python
def test_usd_gbp_roundtrip():
    original = FinancialValue(100, unit=USD)
    converted = original.to(GBP).to(USD)

    # Allow for small rounding differences
    assert abs(original.as_decimal() - converted.as_decimal()) < Decimal("0.01")
```

## Integration with Existing Code

The unit system is designed for gradual adoption:

```python
# Existing code without units continues to work
old_value = FinancialValue(100)  # No unit
new_value = FinancialValue(100, unit=usd)  # With unit

# Mixed operations work when one operand has no unit
result = old_value + new_value  # Result has USD unit
```

This allows you to incrementally add unit safety to your codebase without breaking existing functionality.
