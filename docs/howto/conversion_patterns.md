# Conversion Registration Patterns and Best Practices

This guide covers advanced patterns and best practices for registering and managing unit conversions in the Metric Engine unit system.

## Basic Registration Patterns

### Simple Fixed-Rate Conversions

For conversions with fixed rates that don't change:

```python
from metricengine import MoneyUnit, register_conversion, ConversionContext
from decimal import Decimal

usd = MoneyUnit("USD")
eur = MoneyUnit("EUR")

@register_conversion(usd, eur)
def usd_to_eur(value: Decimal, ctx: ConversionContext) -> Decimal:
    """Convert USD to EUR using fixed rate."""
    return value * Decimal("0.85")

@register_conversion(eur, usd)
def eur_to_usd(value: Decimal, ctx: ConversionContext) -> Decimal:
    """Convert EUR to USD using fixed rate."""
    return value * Decimal("1.176")  # 1 / 0.85
```

### Symmetric Rate Registration

Use a helper function to register both directions with inverse rates:

```python
def register_symmetric_conversion(unit1, unit2, rate):
    """Register bidirectional conversion with symmetric rates."""

    @register_conversion(unit1, unit2)
    def forward(value: Decimal, ctx: ConversionContext) -> Decimal:
        return value * rate

    @register_conversion(unit2, unit1)
    def reverse(value: Decimal, ctx: ConversionContext) -> Decimal:
        return value / rate

    return forward, reverse

# Usage
usd = MoneyUnit("USD")
gbp = MoneyUnit("GBP")
register_symmetric_conversion(usd, gbp, Decimal("0.79"))
```

## Dynamic Rate Patterns

### Context-Based Rate Lookup

Use the conversion context to access dynamic rates:

```python
@register_conversion(usd, gbp)
def usd_to_gbp_dynamic(value: Decimal, ctx: ConversionContext) -> Decimal:
    """Convert USD to GBP using context-provided rate."""

    # Priority 1: Explicit rate in metadata
    if "rate" in ctx.meta:
        rate = Decimal(ctx.meta["rate"])
        return value * rate

    # Priority 2: Historical rate for specific date
    if ctx.at:
        rate = get_historical_rate("USD", "GBP", ctx.at)
        return value * rate

    # Priority 3: Current market rate
    rate = get_current_rate("USD", "GBP")
    return value * rate

def get_historical_rate(from_currency: str, to_currency: str, date: str) -> Decimal:
    """Fetch historical exchange rate for specific date."""
    # Implementation would query historical rate database
    # This is a placeholder
    return Decimal("0.79")

def get_current_rate(from_currency: str, to_currency: str) -> Decimal:
    """Fetch current exchange rate from API."""
    # Implementation would call exchange rate API
    # This is a placeholder
    return Decimal("0.79")
```

### Rate Provider Pattern

Create a centralized rate provider for consistent rate management:

```python
from abc import ABC, abstractmethod
from typing import Optional

class RateProvider(ABC):
    """Abstract base class for exchange rate providers."""

    @abstractmethod
    def get_rate(self, from_unit: str, to_unit: str, at: Optional[str] = None) -> Decimal:
        """Get exchange rate between two currencies."""
        pass

class ECBRateProvider(RateProvider):
    """European Central Bank rate provider."""

    def get_rate(self, from_unit: str, to_unit: str, at: Optional[str] = None) -> Decimal:
        # Implementation would call ECB API
        return self._fetch_ecb_rate(from_unit, to_unit, at)

    def _fetch_ecb_rate(self, from_unit: str, to_unit: str, at: Optional[str]) -> Decimal:
        # Placeholder implementation
        return Decimal("0.85")

class CachedRateProvider(RateProvider):
    """Rate provider with caching for performance."""

    def __init__(self, underlying: RateProvider, cache_ttl: int = 300):
        self.underlying = underlying
        self.cache = {}
        self.cache_ttl = cache_ttl

    def get_rate(self, from_unit: str, to_unit: str, at: Optional[str] = None) -> Decimal:
        cache_key = (from_unit, to_unit, at)

        # Check cache first
        if cache_key in self.cache:
            rate, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                return rate

        # Fetch from underlying provider
        rate = self.underlying.get_rate(from_unit, to_unit, at)
        self.cache[cache_key] = (rate, time.time())
        return rate

# Global rate provider instance
_rate_provider = CachedRateProvider(ECBRateProvider())

def register_currency_pair(from_currency: str, to_currency: str):
    """Register conversion for a currency pair using the global rate provider."""
    from_unit = MoneyUnit(from_currency)
    to_unit = MoneyUnit(to_currency)

    @register_conversion(from_unit, to_unit)
    def convert_with_provider(value: Decimal, ctx: ConversionContext) -> Decimal:
        rate = _rate_provider.get_rate(from_currency, to_currency, ctx.at)
        return value * rate

    return convert_with_provider

# Register multiple currency pairs
register_currency_pair("USD", "EUR")
register_currency_pair("USD", "GBP")
register_currency_pair("EUR", "GBP")
```

## Quantity Conversion Patterns

### Unit System Conversions

For physical quantities, organize conversions by measurement system:

```python
from metricengine import Qty

# Metric system
kg = Qty("kg")
g = Qty("g")
mg = Qty("mg")

# Imperial system
lb = Qty("lb")
oz = Qty("oz")

# Metric internal conversions
@register_conversion(kg, g)
def kg_to_g(value: Decimal, ctx: ConversionContext) -> Decimal:
    return value * 1000

@register_conversion(g, kg)
def g_to_kg(value: Decimal, ctx: ConversionContext) -> Decimal:
    return value / 1000

# Cross-system conversions
@register_conversion(kg, lb)
def kg_to_lb(value: Decimal, ctx: ConversionContext) -> Decimal:
    return value * Decimal("2.20462")

@register_conversion(lb, kg)
def lb_to_kg(value: Decimal, ctx: ConversionContext) -> Decimal:
    return value / Decimal("2.20462")
```

### Conversion Chain Registration

Register conversion chains for complex unit systems:

```python
def register_conversion_chain(units_and_factors):
    """Register conversions for a chain of related units.

    Args:
        units_and_factors: List of (unit, factor_to_next) tuples
    """
    for i in range(len(units_and_factors) - 1):
        current_unit, factor = units_and_factors[i]
        next_unit, _ = units_and_factors[i + 1]

        @register_conversion(current_unit, next_unit)
        def forward_conversion(value: Decimal, ctx: ConversionContext, f=factor) -> Decimal:
            return value * f

        @register_conversion(next_unit, current_unit)
        def reverse_conversion(value: Decimal, ctx: ConversionContext, f=factor) -> Decimal:
            return value / f

# Usage for length units
length_chain = [
    (Qty("mm"), Decimal("10")),
    (Qty("cm"), Decimal("100")),
    (Qty("m"), Decimal("1000")),
    (Qty("km"), None)  # Last unit doesn't need factor
]

register_conversion_chain(length_chain)
```

## Error Handling Patterns

### Graceful Degradation

Handle conversion errors gracefully with fallback strategies:

```python
@register_conversion(usd, gbp)
def usd_to_gbp_with_fallback(value: Decimal, ctx: ConversionContext) -> Decimal:
    """Convert USD to GBP with multiple fallback strategies."""

    try:
        # Try primary rate source
        rate = get_primary_rate("USD", "GBP", ctx.at)
        return value * rate
    except RateServiceError:
        try:
            # Fallback to secondary source
            rate = get_secondary_rate("USD", "GBP", ctx.at)
            return value * rate
        except RateServiceError:
            # Final fallback to cached rate
            rate = get_cached_rate("USD", "GBP")
            if rate is None:
                raise ValueError("No exchange rate available for USD to GBP")
            return value * rate

class RateServiceError(Exception):
    """Exception raised when rate service is unavailable."""
    pass
```

### Validation and Bounds Checking

Add validation to conversion functions:

```python
@register_conversion(usd, gbp)
def usd_to_gbp_validated(value: Decimal, ctx: ConversionContext) -> Decimal:
    """Convert USD to GBP with rate validation."""

    rate = get_exchange_rate("USD", "GBP", ctx.at)

    # Validate rate is within reasonable bounds
    min_rate = Decimal("0.5")
    max_rate = Decimal("1.5")

    if not (min_rate <= rate <= max_rate):
        raise ValueError(f"Exchange rate {rate} is outside valid range [{min_rate}, {max_rate}]")

    # Validate input value
    if value < 0:
        raise ValueError("Cannot convert negative currency amounts")

    return value * rate
```

## Performance Optimization Patterns

### Batch Conversion Registration

Register multiple conversions efficiently:

```python
def register_currency_matrix(currencies, rate_matrix):
    """Register conversions for a matrix of currencies.

    Args:
        currencies: List of currency codes
        rate_matrix: 2D list where rate_matrix[i][j] is rate from currencies[i] to currencies[j]
    """
    for i, from_currency in enumerate(currencies):
        for j, to_currency in enumerate(currencies):
            if i != j:  # Skip self-conversions
                from_unit = MoneyUnit(from_currency)
                to_unit = MoneyUnit(to_currency)
                rate = Decimal(str(rate_matrix[i][j]))

                @register_conversion(from_unit, to_unit)
                def convert_with_rate(value: Decimal, ctx: ConversionContext, r=rate) -> Decimal:
                    return value * r

# Usage
currencies = ["USD", "EUR", "GBP", "JPY"]
rates = [
    [1.0,   0.85,  0.79,  110.0],  # USD rates
    [1.176, 1.0,   0.93,  129.4],  # EUR rates
    [1.266, 1.075, 1.0,   139.2],  # GBP rates
    [0.009, 0.008, 0.007, 1.0]     # JPY rates
]

register_currency_matrix(currencies, rates)
```

### Lazy Registration

Register conversions only when needed:

```python
class LazyConversionRegistry:
    """Registry that loads conversions on demand."""

    def __init__(self):
        self._registered = set()
        self._loaders = {}

    def register_loader(self, from_unit, to_unit, loader_func):
        """Register a function that will create the conversion when needed."""
        self._loaders[(from_unit, to_unit)] = loader_func

    def ensure_conversion(self, from_unit, to_unit):
        """Ensure conversion is registered, loading if necessary."""
        pair = (from_unit, to_unit)

        if pair not in self._registered:
            if pair in self._loaders:
                loader = self._loaders[pair]
                loader()  # This should call register_conversion
                self._registered.add(pair)
            else:
                raise KeyError(f"No loader registered for {from_unit} to {to_unit}")

# Global lazy registry
_lazy_registry = LazyConversionRegistry()

def register_lazy_conversion(from_unit, to_unit, conversion_func):
    """Register a conversion that will be loaded on demand."""
    def loader():
        register_conversion(from_unit, to_unit)(conversion_func)

    _lazy_registry.register_loader(from_unit, to_unit, loader)
```

## Testing Patterns

### Conversion Testing Utilities

Create utilities for testing conversions:

```python
def test_conversion_roundtrip(unit1, unit2, test_value=Decimal("100"), tolerance=Decimal("0.01")):
    """Test that conversion round-trip preserves value within tolerance."""
    from metricengine import FinancialValue

    original = FinancialValue(test_value, unit=unit1)
    converted = original.to(unit2).to(unit1)

    difference = abs(original.as_decimal() - converted.as_decimal())
    assert difference <= tolerance, f"Round-trip error {difference} exceeds tolerance {tolerance}"

def test_conversion_symmetry(unit1, unit2, test_value=Decimal("100")):
    """Test that A->B->A and B->A->B produce consistent results."""
    from metricengine import FinancialValue

    # Test A -> B -> A
    value_a = FinancialValue(test_value, unit=unit1)
    roundtrip_a = value_a.to(unit2).to(unit1)

    # Test B -> A -> B
    value_b = FinancialValue(test_value, unit=unit2)
    roundtrip_b = value_b.to(unit1).to(unit2)

    # Both should have same relative error
    error_a = abs(value_a.as_decimal() - roundtrip_a.as_decimal()) / value_a.as_decimal()
    error_b = abs(value_b.as_decimal() - roundtrip_b.as_decimal()) / value_b.as_decimal()

    assert abs(error_a - error_b) < Decimal("0.001"), "Asymmetric conversion errors detected"

# Usage in tests
def test_usd_gbp_conversions():
    usd = MoneyUnit("USD")
    gbp = MoneyUnit("GBP")

    test_conversion_roundtrip(usd, gbp)
    test_conversion_symmetry(usd, gbp)
```

### Mock Rate Providers

Create mock providers for testing:

```python
class MockRateProvider(RateProvider):
    """Mock rate provider for testing."""

    def __init__(self, rates=None):
        self.rates = rates or {}
        self.call_count = 0

    def get_rate(self, from_unit: str, to_unit: str, at: Optional[str] = None) -> Decimal:
        self.call_count += 1
        key = (from_unit, to_unit, at)

        if key in self.rates:
            return self.rates[key]

        # Fallback to key without timestamp
        key_no_time = (from_unit, to_unit, None)
        if key_no_time in self.rates:
            return self.rates[key_no_time]

        raise RateServiceError(f"No mock rate for {from_unit} to {to_unit}")

    def set_rate(self, from_unit: str, to_unit: str, rate: Decimal, at: Optional[str] = None):
        """Set a mock rate for testing."""
        self.rates[(from_unit, to_unit, at)] = rate

# Usage in tests
def test_conversion_with_mock_rates():
    mock_provider = MockRateProvider()
    mock_provider.set_rate("USD", "GBP", Decimal("0.79"))

    # Replace global provider for test
    global _rate_provider
    original_provider = _rate_provider
    _rate_provider = mock_provider

    try:
        # Test conversion
        usd_value = FinancialValue(100, unit=MoneyUnit("USD"))
        gbp_value = usd_value.to(MoneyUnit("GBP"))

        assert gbp_value.as_decimal() == Decimal("79.00")
        assert mock_provider.call_count == 1
    finally:
        # Restore original provider
        _rate_provider = original_provider
```

## Best Practices Summary

1. **Always register bidirectional conversions** - Users expect to convert in both directions
2. **Use context for dynamic data** - Leverage timestamps and metadata for flexible conversions
3. **Validate rates and inputs** - Add bounds checking and input validation
4. **Handle errors gracefully** - Provide fallback strategies for rate service failures
5. **Test round-trip accuracy** - Ensure conversions preserve value within acceptable tolerance
6. **Organize by domain** - Group related conversions together for maintainability
7. **Cache expensive operations** - Use caching for rate lookups and API calls
8. **Document rate sources** - Clearly document where rates come from and their update frequency
9. **Use appropriate precision** - Choose decimal precision appropriate for your use case
10. **Monitor conversion usage** - Log conversions for debugging and audit purposes

These patterns provide a solid foundation for building robust, maintainable conversion systems in the Metric Engine unit system.
