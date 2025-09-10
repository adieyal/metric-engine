"""Tests for the conversion system foundation."""

from decimal import Decimal

import pytest

from metricengine.units import (
    Conversion,
    ConversionContext,
    MoneyUnit,
    Pct,
    Qty,
    _conversion_registry,
    get_conversion,
    list_conversions,
    register_conversion,
)


class TestConversionContext:
    """Test ConversionContext dataclass."""

    def test_default_creation(self):
        """Test creating ConversionContext with defaults."""
        ctx = ConversionContext()
        assert ctx.at is None
        assert ctx.meta == {}

    def test_creation_with_at(self):
        """Test creating ConversionContext with timestamp."""
        ctx = ConversionContext(at="2025-09-06T10:30:00Z")
        assert ctx.at == "2025-09-06T10:30:00Z"
        assert ctx.meta == {}

    def test_creation_with_meta(self):
        """Test creating ConversionContext with metadata."""
        meta = {"rate": "0.79", "source": "ECB"}
        ctx = ConversionContext(meta=meta)
        assert ctx.at is None
        assert ctx.meta == meta

    def test_creation_with_all_fields(self):
        """Test creating ConversionContext with all fields."""
        meta = {"rate": "0.79", "source": "ECB"}
        ctx = ConversionContext(at="2025-09-06T10:30:00Z", meta=meta)
        assert ctx.at == "2025-09-06T10:30:00Z"
        assert ctx.meta == meta

    def test_immutability(self):
        """Test that ConversionContext is immutable."""
        ctx = ConversionContext(at="2025-09-06T10:30:00Z")
        with pytest.raises(AttributeError):
            ctx.at = "2025-09-07T10:30:00Z"

    def test_equality(self):
        """Test ConversionContext equality."""
        ctx1 = ConversionContext(at="2025-09-06T10:30:00Z", meta={"rate": "0.79"})
        ctx2 = ConversionContext(at="2025-09-06T10:30:00Z", meta={"rate": "0.79"})
        ctx3 = ConversionContext(at="2025-09-07T10:30:00Z", meta={"rate": "0.79"})

        assert ctx1 == ctx2
        assert ctx1 != ctx3


class TestConversion:
    """Test Conversion dataclass."""

    def test_creation(self):
        """Test creating Conversion object."""
        usd = MoneyUnit("USD")
        gbp = MoneyUnit("GBP")

        def convert_fn(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("0.79")

        conversion = Conversion(usd, gbp, convert_fn)
        assert conversion.src == usd
        assert conversion.dst == gbp
        assert conversion.fn == convert_fn

    def test_immutability(self):
        """Test that Conversion is immutable."""
        usd = MoneyUnit("USD")
        gbp = MoneyUnit("GBP")

        def convert_fn(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("0.79")

        conversion = Conversion(usd, gbp, convert_fn)
        with pytest.raises(AttributeError):
            conversion.src = MoneyUnit("EUR")

    def test_equality(self):
        """Test Conversion equality."""
        usd = MoneyUnit("USD")
        gbp = MoneyUnit("GBP")

        def convert_fn1(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("0.79")

        def convert_fn2(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("0.79")

        conversion1 = Conversion(usd, gbp, convert_fn1)
        conversion2 = Conversion(usd, gbp, convert_fn1)  # Same function
        conversion3 = Conversion(usd, gbp, convert_fn2)  # Different function

        assert conversion1 == conversion2
        assert conversion1 != conversion3  # Different function objects


class TestConversionRegistry:
    """Test conversion registry functionality."""

    def setup_method(self):
        """Clear registry before each test."""
        _conversion_registry.clear()

    def teardown_method(self):
        """Clear registry after each test."""
        _conversion_registry.clear()

    def test_register_conversion_decorator(self):
        """Test basic conversion registration."""
        usd = MoneyUnit("USD")
        gbp = MoneyUnit("GBP")

        @register_conversion(usd, gbp)
        def usd_to_gbp(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("0.79")

        # Check that conversion was registered
        conversion = get_conversion(usd, gbp)
        assert conversion.src == usd
        assert conversion.dst == gbp
        assert conversion.fn == usd_to_gbp

    def test_register_multiple_conversions(self):
        """Test registering multiple conversions."""
        usd = MoneyUnit("USD")
        gbp = MoneyUnit("GBP")
        eur = MoneyUnit("EUR")

        @register_conversion(usd, gbp)
        def usd_to_gbp(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("0.79")

        @register_conversion(usd, eur)
        def usd_to_eur(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("0.85")

        # Check both conversions are registered
        usd_gbp_conversion = get_conversion(usd, gbp)
        usd_eur_conversion = get_conversion(usd, eur)

        assert usd_gbp_conversion.fn == usd_to_gbp
        assert usd_eur_conversion.fn == usd_to_eur

    def test_get_conversion_missing(self):
        """Test getting non-existent conversion raises KeyError."""
        usd = MoneyUnit("USD")
        gbp = MoneyUnit("GBP")

        with pytest.raises(
            KeyError,
            match="No conversion registered from Money\\[USD\\] to Money\\[GBP\\]",
        ):
            get_conversion(usd, gbp)

    def test_list_conversions_empty(self):
        """Test listing conversions when registry is empty."""
        conversions = list_conversions()
        assert conversions == {}

    def test_list_conversions_with_data(self):
        """Test listing conversions with registered data."""
        usd = MoneyUnit("USD")
        gbp = MoneyUnit("GBP")

        @register_conversion(usd, gbp)
        def usd_to_gbp(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("0.79")

        conversions = list_conversions()
        assert len(conversions) == 1
        assert (usd, gbp) in conversions
        assert conversions[(usd, gbp)].fn == usd_to_gbp

    def test_list_conversions_returns_copy(self):
        """Test that list_conversions returns a copy, not the original registry."""
        usd = MoneyUnit("USD")
        gbp = MoneyUnit("GBP")

        @register_conversion(usd, gbp)
        def usd_to_gbp(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("0.79")

        conversions = list_conversions()
        conversions.clear()  # Modify the returned dict

        # Original registry should still have the conversion
        assert len(_conversion_registry) == 1
        assert get_conversion(usd, gbp).fn == usd_to_gbp


class TestConversionFunctionValidation:
    """Test conversion function signature validation."""

    def setup_method(self):
        """Clear registry before each test."""
        _conversion_registry.clear()

    def teardown_method(self):
        """Clear registry after each test."""
        _conversion_registry.clear()

    def test_valid_function_no_annotations(self):
        """Test valid function without type annotations."""
        usd = MoneyUnit("USD")
        gbp = MoneyUnit("GBP")

        @register_conversion(usd, gbp)
        def usd_to_gbp(value, ctx):
            return value * Decimal("0.79")

        # Should register successfully
        conversion = get_conversion(usd, gbp)
        assert conversion.fn == usd_to_gbp

    def test_valid_function_with_annotations(self):
        """Test valid function with correct type annotations."""
        usd = MoneyUnit("USD")
        gbp = MoneyUnit("GBP")

        @register_conversion(usd, gbp)
        def usd_to_gbp(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("0.79")

        # Should register successfully
        conversion = get_conversion(usd, gbp)
        assert conversion.fn == usd_to_gbp

    def test_invalid_parameter_count_too_few(self):
        """Test function with too few parameters."""
        usd = MoneyUnit("USD")
        gbp = MoneyUnit("GBP")

        with pytest.raises(ValueError, match="must accept exactly 2 parameters"):

            @register_conversion(usd, gbp)
            def invalid_fn(value):
                return value * Decimal("0.79")

    def test_invalid_parameter_count_too_many(self):
        """Test function with too many parameters."""
        usd = MoneyUnit("USD")
        gbp = MoneyUnit("GBP")

        with pytest.raises(ValueError, match="must accept exactly 2 parameters"):

            @register_conversion(usd, gbp)
            def invalid_fn(value, ctx, extra):
                return value * Decimal("0.79")

    def test_invalid_first_parameter_type(self):
        """Test function with wrong first parameter type annotation."""
        usd = MoneyUnit("USD")
        gbp = MoneyUnit("GBP")

        with pytest.raises(ValueError, match="First parameter must be Decimal"):

            @register_conversion(usd, gbp)
            def invalid_fn(value: str, ctx: ConversionContext) -> Decimal:
                return Decimal(value) * Decimal("0.79")

    def test_invalid_second_parameter_type(self):
        """Test function with wrong second parameter type annotation."""
        usd = MoneyUnit("USD")
        gbp = MoneyUnit("GBP")

        with pytest.raises(
            ValueError, match="Second parameter must be ConversionContext"
        ):

            @register_conversion(usd, gbp)
            def invalid_fn(value: Decimal, ctx: dict) -> Decimal:
                return value * Decimal("0.79")

    def test_invalid_return_type(self):
        """Test function with wrong return type annotation."""
        usd = MoneyUnit("USD")
        gbp = MoneyUnit("GBP")

        with pytest.raises(ValueError, match="Return type must be Decimal"):

            @register_conversion(usd, gbp)
            def invalid_fn(value: Decimal, ctx: ConversionContext) -> str:
                return str(value * Decimal("0.79"))


class TestConversionFunctionExecution:
    """Test that registered conversion functions work correctly."""

    def setup_method(self):
        """Clear registry before each test."""
        _conversion_registry.clear()

    def teardown_method(self):
        """Clear registry after each test."""
        _conversion_registry.clear()

    def test_simple_conversion_execution(self):
        """Test executing a simple conversion function."""
        usd = MoneyUnit("USD")
        gbp = MoneyUnit("GBP")

        @register_conversion(usd, gbp)
        def usd_to_gbp(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("0.79")

        conversion = get_conversion(usd, gbp)
        ctx = ConversionContext()
        result = conversion.fn(Decimal("100"), ctx)

        assert result == Decimal("79.00")

    def test_conversion_with_context(self):
        """Test conversion function that uses context."""
        usd = MoneyUnit("USD")
        gbp = MoneyUnit("GBP")

        @register_conversion(usd, gbp)
        def usd_to_gbp(value: Decimal, ctx: ConversionContext) -> Decimal:
            # Use rate from context if available, otherwise default
            rate = Decimal(ctx.meta.get("rate", "0.79"))
            return value * rate

        conversion = get_conversion(usd, gbp)

        # Test with default rate
        ctx1 = ConversionContext()
        result1 = conversion.fn(Decimal("100"), ctx1)
        assert result1 == Decimal("79.00")

        # Test with custom rate from context
        ctx2 = ConversionContext(meta={"rate": "0.85"})
        result2 = conversion.fn(Decimal("100"), ctx2)
        assert result2 == Decimal("85.00")

    def test_conversion_with_timestamp_context(self):
        """Test conversion function that uses timestamp context."""
        usd = MoneyUnit("USD")
        gbp = MoneyUnit("GBP")

        @register_conversion(usd, gbp)
        def usd_to_gbp(value: Decimal, ctx: ConversionContext) -> Decimal:
            # Different rates based on date (simplified example)
            if ctx.at and "2025-09-06" in ctx.at:
                rate = Decimal("0.79")
            else:
                rate = Decimal("0.80")  # Default rate
            return value * rate

        conversion = get_conversion(usd, gbp)

        # Test with specific date
        ctx1 = ConversionContext(at="2025-09-06T10:30:00Z")
        result1 = conversion.fn(Decimal("100"), ctx1)
        assert result1 == Decimal("79.00")

        # Test with different date
        ctx2 = ConversionContext(at="2025-09-07T10:30:00Z")
        result2 = conversion.fn(Decimal("100"), ctx2)
        assert result2 == Decimal("80.00")


class TestConversionWithDifferentUnitTypes:
    """Test conversions between different unit types."""

    def setup_method(self):
        """Clear registry before each test."""
        _conversion_registry.clear()

    def teardown_method(self):
        """Clear registry after each test."""
        _conversion_registry.clear()

    def test_quantity_conversion(self):
        """Test conversion between quantity units."""
        kg = Qty("kg")
        lb = Qty("lb")

        @register_conversion(kg, lb)
        def kg_to_lb(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("2.20462")

        conversion = get_conversion(kg, lb)
        ctx = ConversionContext()
        result = conversion.fn(Decimal("10"), ctx)

        assert result == Decimal("22.0462")

    def test_percent_conversion(self):
        """Test conversion between percent units."""
        ratio = Pct("ratio")
        bp = Pct("bp")  # basis points

        @register_conversion(ratio, bp)
        def ratio_to_bp(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("10000")  # 1 ratio = 10000 bp

        conversion = get_conversion(ratio, bp)
        ctx = ConversionContext()
        result = conversion.fn(Decimal("0.01"), ctx)  # 1%

        assert result == Decimal("100")  # 100 basis points

    def test_mixed_unit_types_not_allowed(self):
        """Test that conversions between different unit categories work if registered."""
        money = MoneyUnit("USD")
        qty = Qty("shares")

        # This should be allowed if someone registers it (e.g., for share price conversions)
        @register_conversion(money, qty)
        def money_to_shares(value: Decimal, ctx: ConversionContext) -> Decimal:
            # Example: convert dollars to shares at $10 per share
            share_price = Decimal(ctx.meta.get("share_price", "10"))
            return value / share_price

        conversion = get_conversion(money, qty)
        ctx = ConversionContext(meta={"share_price": "25"})
        result = conversion.fn(Decimal("100"), ctx)  # $100

        assert result == Decimal("4")  # 4 shares at $25 each


class TestConvertDecimal:
    """Test the convert_decimal function for direct unit conversion."""

    def setup_method(self):
        """Clear registry before each test."""
        _conversion_registry.clear()

    def teardown_method(self):
        """Clear registry after each test."""
        _conversion_registry.clear()

    def test_same_unit_conversion(self):
        """Test converting between same units returns original value."""
        from metricengine.units import convert_decimal

        usd = MoneyUnit("USD")
        value = Decimal("100.50")

        result = convert_decimal(value, usd, usd)
        assert result == value
        assert result is value  # Should be the exact same object

    def test_direct_conversion_no_context(self):
        """Test direct conversion without context parameters."""
        from metricengine.units import convert_decimal

        usd = MoneyUnit("USD")
        gbp = MoneyUnit("GBP")

        @register_conversion(usd, gbp)
        def usd_to_gbp(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("0.79")

        result = convert_decimal(Decimal("100"), usd, gbp)
        assert result == Decimal("79.00")

    def test_direct_conversion_with_at_parameter(self):
        """Test direct conversion with timestamp parameter."""
        from metricengine.units import convert_decimal

        usd = MoneyUnit("USD")
        gbp = MoneyUnit("GBP")

        @register_conversion(usd, gbp)
        def usd_to_gbp(value: Decimal, ctx: ConversionContext) -> Decimal:
            # Different rates based on date
            if ctx.at and "2025-09-06" in ctx.at:
                rate = Decimal("0.79")
            else:
                rate = Decimal("0.80")
            return value * rate

        # Test with specific timestamp
        result1 = convert_decimal(Decimal("100"), usd, gbp, at="2025-09-06T10:30:00Z")
        assert result1 == Decimal("79.00")

        # Test with different timestamp
        result2 = convert_decimal(Decimal("100"), usd, gbp, at="2025-09-07T10:30:00Z")
        assert result2 == Decimal("80.00")

    def test_direct_conversion_with_meta_parameter(self):
        """Test direct conversion with metadata parameter."""
        from metricengine.units import convert_decimal

        usd = MoneyUnit("USD")
        gbp = MoneyUnit("GBP")

        @register_conversion(usd, gbp)
        def usd_to_gbp(value: Decimal, ctx: ConversionContext) -> Decimal:
            rate = Decimal(ctx.meta.get("rate", "0.79"))
            return value * rate

        # Test with custom rate
        result1 = convert_decimal(Decimal("100"), usd, gbp, meta={"rate": "0.85"})
        assert result1 == Decimal("85.00")

        # Test with default rate (no meta)
        result2 = convert_decimal(Decimal("100"), usd, gbp)
        assert result2 == Decimal("79.00")

    def test_direct_conversion_with_both_parameters(self):
        """Test direct conversion with both at and meta parameters."""
        from metricengine.units import convert_decimal

        usd = MoneyUnit("USD")
        gbp = MoneyUnit("GBP")

        @register_conversion(usd, gbp)
        def usd_to_gbp(value: Decimal, ctx: ConversionContext) -> Decimal:
            # Use rate from meta if available, otherwise use date-based rate
            if "rate" in ctx.meta:
                rate = Decimal(ctx.meta["rate"])
            elif ctx.at and "2025-09-06" in ctx.at:
                rate = Decimal("0.79")
            else:
                rate = Decimal("0.80")
            return value * rate

        result = convert_decimal(
            Decimal("100"),
            usd,
            gbp,
            at="2025-09-06T10:30:00Z",
            meta={"rate": "0.85", "source": "ECB"},
        )
        assert result == Decimal("85.00")  # Should use meta rate, not date rate

    def test_direct_conversion_missing_conversion(self):
        """Test direct conversion with missing conversion raises KeyError."""
        from metricengine.units import convert_decimal

        usd = MoneyUnit("USD")
        gbp = MoneyUnit("GBP")

        with pytest.raises(
            KeyError, match="No conversion.*from Money\\[USD\\] to Money\\[GBP\\]"
        ):
            convert_decimal(Decimal("100"), usd, gbp)

    def test_direct_conversion_quantity_units(self):
        """Test direct conversion with quantity units."""
        from metricengine.units import convert_decimal

        kg = Qty("kg")
        lb = Qty("lb")

        @register_conversion(kg, lb)
        def kg_to_lb(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("2.20462")

        result = convert_decimal(Decimal("5"), kg, lb)
        assert result == Decimal("11.0231")

    def test_direct_conversion_percent_units(self):
        """Test direct conversion with percent units."""
        from metricengine.units import convert_decimal

        ratio = Pct("ratio")
        bp = Pct("bp")

        @register_conversion(ratio, bp)
        def ratio_to_bp(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("10000")

        result = convert_decimal(Decimal("0.0125"), ratio, bp)  # 1.25%
        assert result == Decimal("125")  # 125 basis points


class TestFinancialValueToMethod:
    """Test the FinancialValue.to() method for unit conversion."""

    def setup_method(self):
        """Clear registry before each test."""
        _conversion_registry.clear()

    def teardown_method(self):
        """Clear registry after each test."""
        _conversion_registry.clear()

    def test_same_unit_conversion(self):
        """Test converting to same unit returns equivalent FinancialValue."""
        from metricengine import FinancialValue as FV

        usd = MoneyUnit("USD")
        original = FV(Decimal("100.50"), unit=usd)

        result = original.to(usd)

        # Should be different object but equivalent values
        assert result is not original
        assert result._value == original._value
        assert result.unit == usd
        assert result.policy == original.policy
        assert result._is_percentage == original._is_percentage

    def test_direct_conversion_basic(self):
        """Test basic unit conversion with FinancialValue.to()."""
        from metricengine import FinancialValue as FV

        usd = MoneyUnit("USD")
        gbp = MoneyUnit("GBP")

        @register_conversion(usd, gbp)
        def usd_to_gbp(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("0.79")

        original = FV(Decimal("100"), unit=usd)
        result = original.to(gbp)

        assert result._value == Decimal("79.00")
        assert result.unit == gbp
        assert result.policy == original.policy
        assert result._is_percentage == original._is_percentage

    def test_conversion_with_at_parameter(self):
        """Test conversion with timestamp parameter."""
        from metricengine import FinancialValue as FV

        usd = MoneyUnit("USD")
        gbp = MoneyUnit("GBP")

        @register_conversion(usd, gbp)
        def usd_to_gbp(value: Decimal, ctx: ConversionContext) -> Decimal:
            if ctx.at and "2025-09-06" in ctx.at:
                rate = Decimal("0.79")
            else:
                rate = Decimal("0.80")
            return value * rate

        original = FV(Decimal("100"), unit=usd)

        result1 = original.to(gbp, at="2025-09-06T10:30:00Z")
        assert result1._value == Decimal("79.00")

        result2 = original.to(gbp, at="2025-09-07T10:30:00Z")
        assert result2._value == Decimal("80.00")

    def test_conversion_with_meta_parameter(self):
        """Test conversion with metadata parameter."""
        from metricengine import FinancialValue as FV

        usd = MoneyUnit("USD")
        gbp = MoneyUnit("GBP")

        @register_conversion(usd, gbp)
        def usd_to_gbp(value: Decimal, ctx: ConversionContext) -> Decimal:
            rate = Decimal(ctx.meta.get("rate", "0.79"))
            return value * rate

        original = FV(Decimal("100"), unit=usd)

        result1 = original.to(gbp, meta={"rate": "0.85", "source": "ECB"})
        assert result1._value == Decimal("85.00")

        result2 = original.to(gbp)  # No meta, should use default
        assert result2._value == Decimal("79.00")

    def test_conversion_with_both_parameters(self):
        """Test conversion with both at and meta parameters."""
        from metricengine import FinancialValue as FV

        usd = MoneyUnit("USD")
        gbp = MoneyUnit("GBP")

        @register_conversion(usd, gbp)
        def usd_to_gbp(value: Decimal, ctx: ConversionContext) -> Decimal:
            # Prefer meta rate over date-based rate
            if "rate" in ctx.meta:
                rate = Decimal(ctx.meta["rate"])
            elif ctx.at and "2025-09-06" in ctx.at:
                rate = Decimal("0.79")
            else:
                rate = Decimal("0.80")
            return value * rate

        original = FV(Decimal("100"), unit=usd)
        result = original.to(
            gbp, at="2025-09-06T10:30:00Z", meta={"rate": "0.85", "source": "ECB"}
        )

        assert result._value == Decimal("85.00")

    def test_conversion_preserves_policy(self):
        """Test that conversion preserves the original policy."""
        from metricengine import FinancialValue as FV
        from metricengine.policy import Policy

        usd = MoneyUnit("USD")
        gbp = MoneyUnit("GBP")

        @register_conversion(usd, gbp)
        def usd_to_gbp(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("0.79")

        custom_policy = Policy(decimal_places=4, currency_symbol="$")
        original = FV(Decimal("100"), unit=usd, policy=custom_policy)
        result = original.to(gbp)

        assert result.policy == custom_policy
        assert result.policy.decimal_places == 4
        assert result.policy.currency_symbol == "$"

    def test_conversion_preserves_percentage_flag(self):
        """Test that conversion preserves the percentage flag."""
        from metricengine import FinancialValue as FV

        ratio1 = Pct("ratio")
        ratio2 = Pct("decimal")

        @register_conversion(ratio1, ratio2)
        def ratio_to_decimal(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value  # Same value, different representation

        original = FV(Decimal("0.15"), unit=ratio1, _is_percentage=True)
        result = original.to(ratio2)

        assert result._is_percentage is True
        assert result.unit == ratio2

    def test_conversion_none_value_raises_error(self):
        """Test that converting None value raises ValueError."""
        from metricengine import FinancialValue as FV

        usd = MoneyUnit("USD")
        gbp = MoneyUnit("GBP")

        original = FV(None, unit=usd)

        with pytest.raises(
            ValueError, match="Cannot convert FinancialValue with None value"
        ):
            original.to(gbp)

    def test_conversion_legacy_unit_raises_error(self):
        """Test that converting legacy unit raises TypeError."""
        from metricengine import FinancialValue as FV
        from metricengine.units import Money  # Legacy unit

        gbp = MoneyUnit("GBP")
        original = FV(Decimal("100"), unit=Money)  # Legacy unit system

        with pytest.raises(
            TypeError, match="Conversion only supported for new unit system"
        ):
            original.to(gbp)

    def test_conversion_missing_conversion_raises_error(self):
        """Test that missing conversion raises KeyError."""
        from metricengine import FinancialValue as FV

        usd = MoneyUnit("USD")
        gbp = MoneyUnit("GBP")

        original = FV(Decimal("100"), unit=usd)

        with pytest.raises(
            KeyError,
            match="Failed to convert FinancialValue.*No conversion.*from Money\\[USD\\] to Money\\[GBP\\]",
        ):
            original.to(gbp)

    def test_conversion_with_quantity_units(self):
        """Test conversion with quantity units."""
        from metricengine import FinancialValue as FV

        kg = Qty("kg")
        lb = Qty("lb")

        @register_conversion(kg, lb)
        def kg_to_lb(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("2.20462")

        original = FV(Decimal("10"), unit=kg)
        result = original.to(lb)

        assert result._value == Decimal("22.0462")
        assert result.unit == lb

    def test_conversion_with_percent_units(self):
        """Test conversion with percent units."""
        from metricengine import FinancialValue as FV

        ratio = Pct("ratio")
        bp = Pct("bp")

        @register_conversion(ratio, bp)
        def ratio_to_bp(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("10000")

        original = FV(Decimal("0.0125"), unit=ratio)  # 1.25%
        result = original.to(bp)

        assert result._value == Decimal("125")  # 125 basis points
        assert result.unit == bp

    def test_conversion_provenance_tracking(self):
        """Test that conversion creates proper provenance."""
        from metricengine import FinancialValue as FV

        usd = MoneyUnit("USD")
        gbp = MoneyUnit("GBP")

        @register_conversion(usd, gbp)
        def usd_to_gbp(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("0.79")

        original = FV(Decimal("100"), unit=usd)
        result = original.to(gbp, at="2025-09-06T10:30:00Z", meta={"rate": "0.79"})

        # Check that provenance was created
        assert result._prov is not None
        assert result._prov.op == "convert"
        assert len(result._prov.inputs) == 1

        # Check conversion metadata
        assert result._prov.meta["from"] == "Money[USD]"
        assert result._prov.meta["to"] == "Money[GBP]"
        assert result._prov.meta["operation_type"] == "conversion"
        assert result._prov.meta["at"] == "2025-09-06T10:30:00Z"
        assert result._prov.meta["ctx_rate"] == "0.79"


class TestMultiHopConversion:
    """Test multi-hop conversion path finding and execution."""

    def setup_method(self):
        """Clear registry before each test."""
        _conversion_registry.clear()

    def teardown_method(self):
        """Clear registry after each test."""
        _conversion_registry.clear()

    def test_neighbors_function_empty_registry(self):
        """Test _neighbors function with empty registry."""
        from metricengine.units import _neighbors

        usd = MoneyUnit("USD")
        neighbors = _neighbors(usd)
        assert neighbors == []

    def test_neighbors_function_single_conversion(self):
        """Test _neighbors function with single conversion."""
        from metricengine.units import _neighbors

        usd = MoneyUnit("USD")
        gbp = MoneyUnit("GBP")

        @register_conversion(usd, gbp)
        def usd_to_gbp(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("0.79")

        neighbors = _neighbors(usd)
        assert neighbors == [gbp]

        # GBP should have no neighbors
        gbp_neighbors = _neighbors(gbp)
        assert gbp_neighbors == []

    def test_neighbors_function_multiple_conversions(self):
        """Test _neighbors function with multiple conversions from same unit."""
        from metricengine.units import _neighbors

        usd = MoneyUnit("USD")
        gbp = MoneyUnit("GBP")
        eur = MoneyUnit("EUR")
        cad = MoneyUnit("CAD")

        @register_conversion(usd, gbp)
        def usd_to_gbp(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("0.79")

        @register_conversion(usd, eur)
        def usd_to_eur(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("0.85")

        @register_conversion(usd, cad)
        def usd_to_cad(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("1.35")

        neighbors = _neighbors(usd)
        assert set(neighbors) == {gbp, eur, cad}

    def test_find_path_same_unit(self):
        """Test _find_path with same source and destination unit."""
        from metricengine.units import _find_path

        usd = MoneyUnit("USD")
        path = _find_path(usd, usd)
        assert path == []

    def test_find_path_direct_conversion(self):
        """Test _find_path with direct conversion available."""
        from metricengine.units import _find_path

        usd = MoneyUnit("USD")
        gbp = MoneyUnit("GBP")

        @register_conversion(usd, gbp)
        def usd_to_gbp(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("0.79")

        path = _find_path(usd, gbp)
        assert len(path) == 1
        assert path[0].src == usd
        assert path[0].dst == gbp
        assert path[0].fn == usd_to_gbp

    def test_find_path_two_hop_conversion(self):
        """Test _find_path with two-hop conversion (A->B->C)."""
        from metricengine.units import _find_path

        usd = MoneyUnit("USD")
        eur = MoneyUnit("EUR")
        gbp = MoneyUnit("GBP")

        @register_conversion(usd, eur)
        def usd_to_eur(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("0.85")

        @register_conversion(eur, gbp)
        def eur_to_gbp(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("0.93")

        path = _find_path(usd, gbp)
        assert len(path) == 2
        assert path[0].src == usd
        assert path[0].dst == eur
        assert path[0].fn == usd_to_eur
        assert path[1].src == eur
        assert path[1].dst == gbp
        assert path[1].fn == eur_to_gbp

    def test_find_path_shortest_path_selection(self):
        """Test _find_path selects shortest path when multiple paths exist."""
        from metricengine.units import _find_path

        usd = MoneyUnit("USD")
        eur = MoneyUnit("EUR")
        gbp = MoneyUnit("GBP")
        cad = MoneyUnit("CAD")

        # Direct path: USD -> GBP (1 hop)
        @register_conversion(usd, gbp)
        def usd_to_gbp_direct(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("0.79")

        # Longer path: USD -> EUR -> GBP (2 hops)
        @register_conversion(usd, eur)
        def usd_to_eur(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("0.85")

        @register_conversion(eur, gbp)
        def eur_to_gbp(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("0.93")

        # Even longer path: USD -> CAD -> EUR -> GBP (3 hops)
        @register_conversion(usd, cad)
        def usd_to_cad(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("1.35")

        @register_conversion(cad, eur)
        def cad_to_eur(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("0.63")

        path = _find_path(usd, gbp)
        # Should select the direct path (1 hop)
        assert len(path) == 1
        assert path[0].src == usd
        assert path[0].dst == gbp
        assert path[0].fn == usd_to_gbp_direct

    def test_find_path_no_path_exists(self):
        """Test _find_path raises KeyError when no path exists."""
        from metricengine.units import _find_path

        usd = MoneyUnit("USD")
        gbp = MoneyUnit("GBP")
        eur = MoneyUnit("EUR")

        # Register conversion that doesn't help (EUR -> GBP, but no USD -> EUR)
        @register_conversion(eur, gbp)
        def eur_to_gbp(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("0.93")

        with pytest.raises(
            KeyError,
            match="No conversion path found from Money\\[USD\\] to Money\\[GBP\\]",
        ):
            _find_path(usd, gbp)

    def test_find_path_complex_graph(self):
        """Test _find_path in a complex conversion graph."""
        from metricengine.units import _find_path

        usd = MoneyUnit("USD")
        eur = MoneyUnit("EUR")
        gbp = MoneyUnit("GBP")
        jpy = MoneyUnit("JPY")
        cad = MoneyUnit("CAD")

        # Create a complex graph:
        # USD -> EUR, CAD
        # EUR -> GBP, JPY
        # CAD -> JPY
        # JPY -> GBP

        @register_conversion(usd, eur)
        def usd_to_eur(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("0.85")

        @register_conversion(usd, cad)
        def usd_to_cad(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("1.35")

        @register_conversion(eur, gbp)
        def eur_to_gbp(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("0.93")

        @register_conversion(eur, jpy)
        def eur_to_jpy(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("130")

        @register_conversion(cad, jpy)
        def cad_to_jpy(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("95")

        @register_conversion(jpy, gbp)
        def jpy_to_gbp(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("0.0072")

        # Find path from USD to GBP
        path = _find_path(usd, gbp)
        # Should find shortest path: USD -> EUR -> GBP (2 hops)
        assert len(path) == 2
        assert path[0].src == usd
        assert path[0].dst == eur
        assert path[1].src == eur
        assert path[1].dst == gbp

    def test_convert_decimal_multi_hop_two_hops(self):
        """Test convert_decimal with two-hop conversion."""
        from metricengine.units import convert_decimal

        usd = MoneyUnit("USD")
        eur = MoneyUnit("EUR")
        gbp = MoneyUnit("GBP")

        @register_conversion(usd, eur)
        def usd_to_eur(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("0.85")

        @register_conversion(eur, gbp)
        def eur_to_gbp(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("0.93")

        # Convert $100 USD -> GBP via EUR
        result = convert_decimal(Decimal("100"), usd, gbp)

        # $100 * 0.85 = €85, €85 * 0.93 = £79.05
        expected = Decimal("100") * Decimal("0.85") * Decimal("0.93")
        assert result == expected
        assert result == Decimal("79.05")

    def test_convert_decimal_multi_hop_with_context(self):
        """Test convert_decimal multi-hop with context parameters."""
        from metricengine.units import convert_decimal

        usd = MoneyUnit("USD")
        eur = MoneyUnit("EUR")
        gbp = MoneyUnit("GBP")

        @register_conversion(usd, eur)
        def usd_to_eur(value: Decimal, ctx: ConversionContext) -> Decimal:
            rate = Decimal(ctx.meta.get("usd_eur_rate", "0.85"))
            return value * rate

        @register_conversion(eur, gbp)
        def eur_to_gbp(value: Decimal, ctx: ConversionContext) -> Decimal:
            rate = Decimal(ctx.meta.get("eur_gbp_rate", "0.93"))
            return value * rate

        # Test with custom rates
        result = convert_decimal(
            Decimal("100"),
            usd,
            gbp,
            meta={"usd_eur_rate": "0.90", "eur_gbp_rate": "0.95"},
        )

        # $100 * 0.90 = €90, €90 * 0.95 = £85.50
        expected = Decimal("100") * Decimal("0.90") * Decimal("0.95")
        assert result == expected
        assert result == Decimal("85.50")

    def test_convert_decimal_prefers_direct_over_multi_hop(self):
        """Test convert_decimal prefers direct conversion over multi-hop."""
        from metricengine.units import convert_decimal

        usd = MoneyUnit("USD")
        eur = MoneyUnit("EUR")
        gbp = MoneyUnit("GBP")

        # Direct conversion
        @register_conversion(usd, gbp)
        def usd_to_gbp_direct(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("0.79")  # Direct rate

        # Multi-hop path (should not be used)
        @register_conversion(usd, eur)
        def usd_to_eur(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("0.85")

        @register_conversion(eur, gbp)
        def eur_to_gbp(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("0.93")

        result = convert_decimal(Decimal("100"), usd, gbp)

        # Should use direct conversion: $100 * 0.79 = £79
        assert result == Decimal("79.00")
        # Not multi-hop: $100 * 0.85 * 0.93 = £79.05

    def test_convert_decimal_multi_hop_three_hops(self):
        """Test convert_decimal with three-hop conversion."""
        from metricengine.units import convert_decimal

        usd = MoneyUnit("USD")
        eur = MoneyUnit("EUR")
        jpy = MoneyUnit("JPY")
        gbp = MoneyUnit("GBP")

        @register_conversion(usd, eur)
        def usd_to_eur(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("0.85")

        @register_conversion(eur, jpy)
        def eur_to_jpy(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("130")

        @register_conversion(jpy, gbp)
        def jpy_to_gbp(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("0.0072")

        result = convert_decimal(Decimal("100"), usd, gbp)

        # $100 * 0.85 = €85
        # €85 * 130 = ¥11,050
        # ¥11,050 * 0.0072 = £79.56
        expected = Decimal("100") * Decimal("0.85") * Decimal("130") * Decimal("0.0072")
        assert result == expected
        assert result == Decimal("79.56")

    def test_convert_decimal_multi_hop_no_path_error(self):
        """Test convert_decimal raises KeyError when no path exists."""
        from metricengine.units import convert_decimal

        usd = MoneyUnit("USD")
        gbp = MoneyUnit("GBP")
        eur = MoneyUnit("EUR")

        # Register unrelated conversion
        @register_conversion(eur, gbp)
        def eur_to_gbp(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("0.93")

        with pytest.raises(
            KeyError, match="No conversion.*from Money\\[USD\\] to Money\\[GBP\\]"
        ):
            convert_decimal(Decimal("100"), usd, gbp)

    def test_convert_decimal_multi_hop_quantity_units(self):
        """Test convert_decimal multi-hop with quantity units."""
        from metricengine.units import convert_decimal

        kg = Qty("kg")
        lb = Qty("lb")
        oz = Qty("oz")

        @register_conversion(kg, lb)
        def kg_to_lb(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("2.20462")

        @register_conversion(lb, oz)
        def lb_to_oz(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("16")

        result = convert_decimal(Decimal("1"), kg, oz)

        # 1 kg * 2.20462 = 2.20462 lb
        # 2.20462 lb * 16 = 35.27392 oz
        expected = Decimal("1") * Decimal("2.20462") * Decimal("16")
        assert result == expected
        assert result == Decimal("35.27392")

    def test_convert_decimal_multi_hop_mixed_unit_categories(self):
        """Test convert_decimal multi-hop across different unit categories."""
        from metricengine.units import convert_decimal

        money = MoneyUnit("USD")
        shares = Qty("shares")
        ratio = Pct("ratio")

        # USD -> shares (at share price)
        @register_conversion(money, shares)
        def money_to_shares(value: Decimal, ctx: ConversionContext) -> Decimal:
            share_price = Decimal(ctx.meta.get("share_price", "10"))
            return value / share_price

        # shares -> ratio (as ownership percentage)
        @register_conversion(shares, ratio)
        def shares_to_ratio(value: Decimal, ctx: ConversionContext) -> Decimal:
            total_shares = Decimal(ctx.meta.get("total_shares", "1000"))
            return value / total_shares

        result = convert_decimal(
            Decimal("500"),
            money,
            ratio,
            meta={"share_price": "25", "total_shares": "2000"},
        )

        # $500 / $25 = 20 shares
        # 20 shares / 2000 total = 0.01 ratio (1%)
        expected = Decimal("500") / Decimal("25") / Decimal("2000")
        assert result == expected
        assert result == Decimal("0.01")


class TestFinancialValueMultiHopConversion:
    """Test FinancialValue.to() method with multi-hop conversions."""

    def setup_method(self):
        """Clear registry before each test."""
        _conversion_registry.clear()

    def teardown_method(self):
        """Clear registry after each test."""
        _conversion_registry.clear()

    def test_financial_value_multi_hop_conversion(self):
        """Test FinancialValue.to() with multi-hop conversion."""
        from metricengine import FinancialValue as FV

        usd = MoneyUnit("USD")
        eur = MoneyUnit("EUR")
        gbp = MoneyUnit("GBP")

        @register_conversion(usd, eur)
        def usd_to_eur(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("0.85")

        @register_conversion(eur, gbp)
        def eur_to_gbp(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("0.93")

        original = FV(Decimal("100"), unit=usd)
        result = original.to(gbp)

        # $100 * 0.85 * 0.93 = £79.05
        assert result._value == Decimal("79.05")
        assert result.unit == gbp
        assert result.policy == original.policy

    def test_financial_value_multi_hop_with_context(self):
        """Test FinancialValue.to() multi-hop with context parameters."""
        from metricengine import FinancialValue as FV

        usd = MoneyUnit("USD")
        eur = MoneyUnit("EUR")
        gbp = MoneyUnit("GBP")

        @register_conversion(usd, eur)
        def usd_to_eur(value: Decimal, ctx: ConversionContext) -> Decimal:
            rate = Decimal(ctx.meta.get("usd_eur_rate", "0.85"))
            return value * rate

        @register_conversion(eur, gbp)
        def eur_to_gbp(value: Decimal, ctx: ConversionContext) -> Decimal:
            rate = Decimal(ctx.meta.get("eur_gbp_rate", "0.93"))
            return value * rate

        original = FV(Decimal("100"), unit=usd)
        result = original.to(
            gbp,
            at="2025-09-06T10:30:00Z",
            meta={"usd_eur_rate": "0.90", "eur_gbp_rate": "0.95"},
        )

        # $100 * 0.90 * 0.95 = £85.50
        assert result._value == Decimal("85.50")
        assert result.unit == gbp

    def test_financial_value_multi_hop_preserves_properties(self):
        """Test that multi-hop conversion preserves FinancialValue properties."""
        from metricengine import FinancialValue as FV
        from metricengine.policy import Policy

        usd = MoneyUnit("USD")
        eur = MoneyUnit("EUR")
        gbp = MoneyUnit("GBP")

        @register_conversion(usd, eur)
        def usd_to_eur(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("0.85")

        @register_conversion(eur, gbp)
        def eur_to_gbp(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("0.93")

        custom_policy = Policy(decimal_places=4, currency_symbol="$")
        original = FV(
            Decimal("100"), unit=usd, policy=custom_policy, _is_percentage=False
        )
        result = original.to(gbp)

        assert result.policy == custom_policy
        assert result._is_percentage is False
        assert result.unit == gbp

    def test_financial_value_multi_hop_no_path_error(self):
        """Test FinancialValue.to() raises KeyError when no multi-hop path exists."""
        from metricengine import FinancialValue as FV

        usd = MoneyUnit("USD")
        gbp = MoneyUnit("GBP")

        original = FV(Decimal("100"), unit=usd)

        with pytest.raises(
            KeyError,
            match="Failed to convert FinancialValue.*No conversion.*from Money\\[USD\\] to Money\\[GBP\\]",
        ):
            original.to(gbp)


class TestConversionPolicy:
    """Test ConversionPolicy dataclass and policy management."""

    def test_default_policy_creation(self):
        """Test creating ConversionPolicy with defaults."""
        from metricengine.units import ConversionPolicy

        policy = ConversionPolicy()
        assert policy.strict is True
        assert policy.allow_paths is True

    def test_custom_policy_creation(self):
        """Test creating ConversionPolicy with custom values."""
        from metricengine.units import ConversionPolicy

        policy = ConversionPolicy(strict=False, allow_paths=False)
        assert policy.strict is False
        assert policy.allow_paths is False

    def test_policy_immutability(self):
        """Test that ConversionPolicy is immutable."""
        from metricengine.units import ConversionPolicy

        policy = ConversionPolicy()
        with pytest.raises(AttributeError):
            policy.strict = False

    def test_policy_equality(self):
        """Test ConversionPolicy equality."""
        from metricengine.units import ConversionPolicy

        policy1 = ConversionPolicy(strict=True, allow_paths=False)
        policy2 = ConversionPolicy(strict=True, allow_paths=False)
        policy3 = ConversionPolicy(strict=False, allow_paths=False)

        assert policy1 == policy2
        assert policy1 != policy3


class TestConversionPolicyContext:
    """Test conversion policy context management."""

    def setup_method(self):
        """Clear registry before each test."""
        _conversion_registry.clear()

    def teardown_method(self):
        """Clear registry after each test."""
        _conversion_registry.clear()

    def test_default_policy_context(self):
        """Test that default policy is strict with paths enabled."""
        from metricengine.units import get_current_conversion_policy

        policy = get_current_conversion_policy()
        assert policy.strict is True
        assert policy.allow_paths is True

    def test_use_conversions_context_manager(self):
        """Test use_conversions context manager."""
        from metricengine.units import (
            ConversionPolicy,
            get_current_conversion_policy,
            use_conversions,
        )

        # Check default policy
        default_policy = get_current_conversion_policy()
        assert default_policy.strict is True
        assert default_policy.allow_paths is True

        # Use custom policy in context
        custom_policy = ConversionPolicy(strict=False, allow_paths=False)
        with use_conversions(custom_policy):
            current_policy = get_current_conversion_policy()
            assert current_policy.strict is False
            assert current_policy.allow_paths is False

        # Check that policy is restored after context
        restored_policy = get_current_conversion_policy()
        assert restored_policy.strict is True
        assert restored_policy.allow_paths is True

    def test_nested_policy_contexts(self):
        """Test nested policy contexts."""
        from metricengine.units import (
            ConversionPolicy,
            get_current_conversion_policy,
            use_conversions,
        )

        policy1 = ConversionPolicy(strict=False, allow_paths=True)
        policy2 = ConversionPolicy(strict=True, allow_paths=False)

        with use_conversions(policy1):
            assert get_current_conversion_policy() == policy1

            with use_conversions(policy2):
                assert get_current_conversion_policy() == policy2

            # Should restore to policy1
            assert get_current_conversion_policy() == policy1

        # Should restore to default
        default_policy = get_current_conversion_policy()
        assert default_policy.strict is True
        assert default_policy.allow_paths is True

    def test_context_manager_exception_handling(self):
        """Test that policy is restored even if exception occurs."""
        from metricengine.units import (
            ConversionPolicy,
            get_current_conversion_policy,
            use_conversions,
        )

        custom_policy = ConversionPolicy(strict=False, allow_paths=False)

        try:
            with use_conversions(custom_policy):
                assert get_current_conversion_policy() == custom_policy
                raise ValueError("Test exception")
        except ValueError:
            pass

        # Policy should be restored despite exception
        restored_policy = get_current_conversion_policy()
        assert restored_policy.strict is True
        assert restored_policy.allow_paths is True


class TestConversionPolicyEnforcement:
    """Test that conversion policies are properly enforced."""

    def setup_method(self):
        """Clear registry before each test."""
        _conversion_registry.clear()

    def teardown_method(self):
        """Clear registry after each test."""
        _conversion_registry.clear()

    def test_strict_mode_missing_conversion_raises(self):
        """Test that strict mode raises KeyError for missing conversions."""
        from metricengine.units import (
            ConversionPolicy,
            convert_decimal,
            use_conversions,
        )

        usd = MoneyUnit("USD")
        gbp = MoneyUnit("GBP")

        # Default strict mode should raise
        with pytest.raises(
            KeyError, match="No conversion.*from Money\\[USD\\] to Money\\[GBP\\]"
        ):
            convert_decimal(Decimal("100"), usd, gbp)

        # Explicit strict mode should also raise
        strict_policy = ConversionPolicy(strict=True, allow_paths=True)
        with use_conversions(strict_policy):
            with pytest.raises(
                KeyError, match="No conversion.*from Money\\[USD\\] to Money\\[GBP\\]"
            ):
                convert_decimal(Decimal("100"), usd, gbp)

    def test_permissive_mode_missing_conversion_returns_original(self):
        """Test that permissive mode returns original value for missing conversions."""
        from metricengine.units import (
            ConversionPolicy,
            convert_decimal,
            use_conversions,
        )

        usd = MoneyUnit("USD")
        gbp = MoneyUnit("GBP")
        original_value = Decimal("100")

        permissive_policy = ConversionPolicy(strict=False, allow_paths=True)
        with use_conversions(permissive_policy):
            result = convert_decimal(original_value, usd, gbp)
            assert result == original_value
            assert result is original_value  # Should be same object

    def test_allow_paths_enabled_uses_multi_hop(self):
        """Test that allow_paths=True enables multi-hop conversions."""
        from metricengine.units import (
            ConversionPolicy,
            convert_decimal,
            use_conversions,
        )

        usd = MoneyUnit("USD")
        eur = MoneyUnit("EUR")
        gbp = MoneyUnit("GBP")

        # Register indirect path: USD -> EUR -> GBP
        @register_conversion(usd, eur)
        def usd_to_eur(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("0.85")

        @register_conversion(eur, gbp)
        def eur_to_gbp(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("0.93")

        # Default policy (allow_paths=True) should use multi-hop
        result = convert_decimal(Decimal("100"), usd, gbp)
        expected = Decimal("100") * Decimal("0.85") * Decimal("0.93")
        assert result == expected

        # Explicit allow_paths=True should also work
        policy = ConversionPolicy(strict=True, allow_paths=True)
        with use_conversions(policy):
            result = convert_decimal(Decimal("100"), usd, gbp)
            assert result == expected

    def test_allow_paths_disabled_strict_mode_raises(self):
        """Test that allow_paths=False with strict=True raises for indirect conversions."""
        from metricengine.units import (
            ConversionPolicy,
            convert_decimal,
            use_conversions,
        )

        usd = MoneyUnit("USD")
        eur = MoneyUnit("EUR")
        gbp = MoneyUnit("GBP")

        # Register indirect path: USD -> EUR -> GBP (no direct USD -> GBP)
        @register_conversion(usd, eur)
        def usd_to_eur(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("0.85")

        @register_conversion(eur, gbp)
        def eur_to_gbp(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("0.93")

        # Policy with paths disabled should raise for indirect conversion
        policy = ConversionPolicy(strict=True, allow_paths=False)
        with use_conversions(policy):
            with pytest.raises(
                KeyError,
                match="No conversion registered from Money\\[USD\\] to Money\\[GBP\\]",
            ):
                convert_decimal(Decimal("100"), usd, gbp)

    def test_allow_paths_disabled_permissive_mode_returns_original(self):
        """Test that allow_paths=False with strict=False returns original for indirect conversions."""
        from metricengine.units import (
            ConversionPolicy,
            convert_decimal,
            use_conversions,
        )

        usd = MoneyUnit("USD")
        eur = MoneyUnit("EUR")
        gbp = MoneyUnit("GBP")
        original_value = Decimal("100")

        # Register indirect path: USD -> EUR -> GBP (no direct USD -> GBP)
        @register_conversion(usd, eur)
        def usd_to_eur(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("0.85")

        @register_conversion(eur, gbp)
        def eur_to_gbp(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("0.93")

        # Policy with paths disabled and permissive mode should return original
        policy = ConversionPolicy(strict=False, allow_paths=False)
        with use_conversions(policy):
            result = convert_decimal(original_value, usd, gbp)
            assert result == original_value
            assert result is original_value

    def test_direct_conversion_works_with_paths_disabled(self):
        """Test that direct conversions work even when paths are disabled."""
        from metricengine.units import (
            ConversionPolicy,
            convert_decimal,
            use_conversions,
        )

        usd = MoneyUnit("USD")
        gbp = MoneyUnit("GBP")

        @register_conversion(usd, gbp)
        def usd_to_gbp(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("0.79")

        # Direct conversion should work even with paths disabled
        policy = ConversionPolicy(strict=True, allow_paths=False)
        with use_conversions(policy):
            result = convert_decimal(Decimal("100"), usd, gbp)
            assert result == Decimal("79.00")

    def test_policy_affects_financialvalue_to_method(self):
        """Test that conversion policy affects FinancialValue.to() method."""
        from metricengine import FinancialValue as FV
        from metricengine.units import ConversionPolicy, use_conversions

        usd = MoneyUnit("USD")
        gbp = MoneyUnit("GBP")
        original = FV(Decimal("100"), unit=usd)

        # Strict mode should raise for missing conversion
        with pytest.raises(KeyError):
            original.to(gbp)

        # Permissive mode should return original FinancialValue unchanged
        # when conversion fails (no unit change should occur)
        permissive_policy = ConversionPolicy(strict=False, allow_paths=True)
        with use_conversions(permissive_policy):
            result = original.to(gbp)
            assert result._value == original._value  # Same value
            assert result.unit == original.unit  # Original unit (conversion failed)
            assert result.unit == usd  # Should still be USD

    def test_policy_with_multi_hop_financialvalue_conversion(self):
        """Test policy enforcement with multi-hop FinancialValue conversions."""
        from metricengine import FinancialValue as FV
        from metricengine.units import ConversionPolicy, use_conversions

        usd = MoneyUnit("USD")
        eur = MoneyUnit("EUR")
        gbp = MoneyUnit("GBP")

        # Register indirect path: USD -> EUR -> GBP
        @register_conversion(usd, eur)
        def usd_to_eur(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("0.85")

        @register_conversion(eur, gbp)
        def eur_to_gbp(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("0.93")

        original = FV(Decimal("100"), unit=usd)

        # Default policy should allow multi-hop
        result1 = original.to(gbp)
        expected = Decimal("100") * Decimal("0.85") * Decimal("0.93")
        assert result1._value == expected

        # Policy with paths disabled should raise
        policy = ConversionPolicy(strict=True, allow_paths=False)
        with use_conversions(policy):
            with pytest.raises(
                KeyError,
                match="Failed to convert FinancialValue.*No conversion registered",
            ):
                original.to(gbp)


class TestConversionPolicyIntegration:
    """Test integration of conversion policy with other system components."""

    def setup_method(self):
        """Clear registry before each test."""
        _conversion_registry.clear()

    def teardown_method(self):
        """Clear registry after each test."""
        _conversion_registry.clear()

    def test_policy_with_context_parameters(self):
        """Test that policy works correctly with context parameters."""
        from metricengine.units import (
            ConversionPolicy,
            convert_decimal,
            use_conversions,
        )

        usd = MoneyUnit("USD")
        gbp = MoneyUnit("GBP")

        @register_conversion(usd, gbp)
        def usd_to_gbp(value: Decimal, ctx: ConversionContext) -> Decimal:
            rate = Decimal(ctx.meta.get("rate", "0.79"))
            return value * rate

        # Test with permissive policy and context parameters
        permissive_policy = ConversionPolicy(strict=False, allow_paths=True)
        with use_conversions(permissive_policy):
            result = convert_decimal(
                Decimal("100"),
                usd,
                gbp,
                at="2025-09-06T10:30:00Z",
                meta={"rate": "0.85"},
            )
            assert result == Decimal("85.00")

    def test_policy_with_same_unit_conversion(self):
        """Test that policy doesn't affect same-unit conversions."""
        from metricengine.units import (
            ConversionPolicy,
            convert_decimal,
            use_conversions,
        )

        usd = MoneyUnit("USD")
        original_value = Decimal("100")

        # Same-unit conversion should work regardless of policy
        strict_policy = ConversionPolicy(strict=True, allow_paths=False)
        with use_conversions(strict_policy):
            result = convert_decimal(original_value, usd, usd)
            assert result == original_value
            assert result is original_value

        permissive_policy = ConversionPolicy(strict=False, allow_paths=False)
        with use_conversions(permissive_policy):
            result = convert_decimal(original_value, usd, usd)
            assert result == original_value
            assert result is original_value

    def test_policy_with_different_unit_types(self):
        """Test policy enforcement with different unit types."""
        from metricengine.units import (
            ConversionPolicy,
            convert_decimal,
            use_conversions,
        )

        money = MoneyUnit("USD")
        qty = Qty("shares")

        # No conversion registered between different unit types
        permissive_policy = ConversionPolicy(strict=False, allow_paths=True)
        with use_conversions(permissive_policy):
            result = convert_decimal(Decimal("100"), money, qty)
            assert result == Decimal("100")  # Returns original

        strict_policy = ConversionPolicy(strict=True, allow_paths=True)
        with use_conversions(strict_policy):
            with pytest.raises(KeyError):
                convert_decimal(Decimal("100"), money, qty)

    def test_policy_thread_safety(self):
        """Test that policy context is thread-local."""
        import threading

        from metricengine.units import (
            ConversionPolicy,
            get_current_conversion_policy,
            use_conversions,
        )

        results = {}

        def thread_function(thread_id, policy):
            with use_conversions(policy):
                # Small delay to ensure threads overlap
                import time

                time.sleep(0.01)
                results[thread_id] = get_current_conversion_policy()

        policy1 = ConversionPolicy(strict=True, allow_paths=False)
        policy2 = ConversionPolicy(strict=False, allow_paths=True)

        thread1 = threading.Thread(target=thread_function, args=(1, policy1))
        thread2 = threading.Thread(target=thread_function, args=(2, policy2))

        thread1.start()
        thread2.start()

        thread1.join()
        thread2.join()

        # Each thread should have seen its own policy
        assert results[1] == policy1
        assert results[2] == policy2

        # Main thread should still have default policy
        main_policy = get_current_conversion_policy()
        assert main_policy.strict is True
        assert main_policy.allow_paths is True


class TestConversionErrorHandling:
    """Test comprehensive error handling in the conversion system."""

    def setup_method(self):
        """Clear registry before each test."""
        _conversion_registry.clear()

    def teardown_method(self):
        """Clear registry after each test."""
        _conversion_registry.clear()

    def test_get_conversion_missing_with_descriptive_error(self):
        """Test that missing conversion provides descriptive error with available options."""
        usd = MoneyUnit("USD")
        gbp = MoneyUnit("GBP")
        eur = MoneyUnit("EUR")

        # Register some conversions but not the one we want
        @register_conversion(usd, eur)
        def usd_to_eur(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("0.85")

        @register_conversion(eur, gbp)
        def eur_to_gbp(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("0.93")

        with pytest.raises(KeyError) as exc_info:
            get_conversion(usd, gbp)

        error_msg = str(exc_info.value)
        assert "No conversion registered from Money[USD] to Money[GBP]" in error_msg
        assert "Available conversions from Money[USD]: ['Money[EUR]']" in error_msg
        assert "Available conversions to Money[GBP]: ['Money[EUR]']" in error_msg

    def test_get_conversion_no_conversions_registered(self):
        """Test error message when no conversions are registered at all."""
        usd = MoneyUnit("USD")
        gbp = MoneyUnit("GBP")

        with pytest.raises(KeyError) as exc_info:
            get_conversion(usd, gbp)

        error_msg = str(exc_info.value)
        assert "No conversion registered from Money[USD] to Money[GBP]" in error_msg
        assert "No conversions are currently registered" in error_msg

    def test_get_conversion_other_conversions_exist(self):
        """Test error message when other conversions exist but not the requested one."""
        usd = MoneyUnit("USD")
        gbp = MoneyUnit("GBP")
        eur = MoneyUnit("EUR")
        cad = MoneyUnit("CAD")

        # Register conversions that don't involve USD or GBP
        @register_conversion(eur, cad)
        def eur_to_cad(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("1.45")

        with pytest.raises(KeyError) as exc_info:
            get_conversion(usd, gbp)

        error_msg = str(exc_info.value)
        assert "No conversion registered from Money[USD] to Money[GBP]" in error_msg
        assert "1 conversions are registered for other unit pairs" in error_msg

    def test_find_path_source_unit_not_in_registry(self):
        """Test path finding error when source unit has no conversions."""
        from metricengine.units import _find_path

        usd = MoneyUnit("USD")
        gbp = MoneyUnit("GBP")
        eur = MoneyUnit("EUR")
        cad = MoneyUnit("CAD")

        # Register conversion that doesn't involve USD
        @register_conversion(eur, cad)
        def eur_to_cad(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("1.45")

        with pytest.raises(KeyError) as exc_info:
            _find_path(usd, gbp)

        error_msg = str(exc_info.value)
        assert "No conversion path found from Money[USD] to Money[GBP]" in error_msg
        assert "Source unit Money[USD] has no registered conversions" in error_msg

    def test_find_path_destination_unit_not_in_registry(self):
        """Test path finding error when destination unit has no conversions."""
        from metricengine.units import _find_path

        usd = MoneyUnit("USD")
        gbp = MoneyUnit("GBP")
        eur = MoneyUnit("EUR")

        # Register conversion from USD but not to GBP
        @register_conversion(usd, eur)
        def usd_to_eur(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("0.85")

        with pytest.raises(KeyError) as exc_info:
            _find_path(usd, gbp)

        error_msg = str(exc_info.value)
        assert "No conversion path found from Money[USD] to Money[GBP]" in error_msg
        assert "Destination unit Money[GBP] has no registered conversions" in error_msg

    def test_find_path_disconnected_networks(self):
        """Test path finding error when units exist but networks are disconnected."""
        from metricengine.units import _find_path

        usd = MoneyUnit("USD")
        gbp = MoneyUnit("GBP")
        eur = MoneyUnit("EUR")
        cad = MoneyUnit("CAD")

        # Create two disconnected conversion networks
        @register_conversion(usd, eur)
        def usd_to_eur(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("0.85")

        @register_conversion(cad, gbp)
        def cad_to_gbp(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("0.58")

        with pytest.raises(KeyError) as exc_info:
            _find_path(usd, gbp)

        error_msg = str(exc_info.value)
        assert "No conversion path found from Money[USD] to Money[GBP]" in error_msg
        assert "Money[USD] can convert to: ['Money[EUR]']" in error_msg
        assert "Money[GBP] can be converted from: ['Money[CAD]']" in error_msg
        assert "These conversion networks are not connected" in error_msg

    def test_convert_decimal_conversion_function_exception_strict_mode(self):
        """Test that conversion function exceptions are handled in strict mode."""
        from metricengine.units import convert_decimal

        usd = MoneyUnit("USD")
        gbp = MoneyUnit("GBP")

        @register_conversion(usd, gbp)
        def failing_conversion(value: Decimal, ctx: ConversionContext) -> Decimal:
            raise ValueError("Rate lookup failed")

        with pytest.raises(ValueError) as exc_info:
            convert_decimal(Decimal("100"), usd, gbp)

        error_msg = str(exc_info.value)
        assert "Conversion function failed for Money[USD] to Money[GBP]" in error_msg
        assert "ValueError: Rate lookup failed" in error_msg

    def test_convert_decimal_conversion_function_exception_permissive_mode(self):
        """Test that conversion function exceptions return original value in permissive mode."""
        from metricengine.units import (
            ConversionPolicy,
            convert_decimal,
            use_conversions,
        )

        usd = MoneyUnit("USD")
        gbp = MoneyUnit("GBP")

        @register_conversion(usd, gbp)
        def failing_conversion(value: Decimal, ctx: ConversionContext) -> Decimal:
            raise ValueError("Rate lookup failed")

        permissive_policy = ConversionPolicy(strict=False)
        with use_conversions(permissive_policy):
            result = convert_decimal(Decimal("100"), usd, gbp)

        assert result == Decimal("100")  # Original value returned

    def test_convert_decimal_path_conversion_function_exception_strict_mode(self):
        """Test that path conversion function exceptions are handled in strict mode."""
        from metricengine.units import convert_decimal

        usd = MoneyUnit("USD")
        gbp = MoneyUnit("GBP")
        eur = MoneyUnit("EUR")

        @register_conversion(usd, eur)
        def usd_to_eur(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("0.85")

        @register_conversion(eur, gbp)
        def failing_eur_to_gbp(value: Decimal, ctx: ConversionContext) -> Decimal:
            raise ValueError("EUR to GBP rate unavailable")

        with pytest.raises(ValueError) as exc_info:
            convert_decimal(Decimal("100"), usd, gbp)

        error_msg = str(exc_info.value)
        assert "Conversion function failed in path step 2" in error_msg
        assert "Money[EUR] to Money[GBP]" in error_msg
        assert "ValueError: EUR to GBP rate unavailable" in error_msg

    def test_convert_decimal_path_conversion_function_exception_permissive_mode(self):
        """Test that path conversion function exceptions return original value in permissive mode."""
        from metricengine.units import (
            ConversionPolicy,
            convert_decimal,
            use_conversions,
        )

        usd = MoneyUnit("USD")
        gbp = MoneyUnit("GBP")
        eur = MoneyUnit("EUR")

        @register_conversion(usd, eur)
        def usd_to_eur(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("0.85")

        @register_conversion(eur, gbp)
        def failing_eur_to_gbp(value: Decimal, ctx: ConversionContext) -> Decimal:
            raise ValueError("EUR to GBP rate unavailable")

        permissive_policy = ConversionPolicy(strict=False)
        with use_conversions(permissive_policy):
            result = convert_decimal(Decimal("100"), usd, gbp)

        assert result == Decimal("100")  # Original value returned

    def test_convert_decimal_missing_conversion_strict_mode(self):
        """Test missing conversion error in strict mode."""
        from metricengine.units import convert_decimal

        usd = MoneyUnit("USD")
        gbp = MoneyUnit("GBP")

        with pytest.raises(KeyError) as exc_info:
            convert_decimal(Decimal("100"), usd, gbp)

        error_msg = str(exc_info.value)
        # The error comes from path finding since no direct conversion exists
        assert "No conversion path found from Money[USD] to Money[GBP]" in error_msg

    def test_convert_decimal_missing_conversion_permissive_mode(self):
        """Test missing conversion returns original value in permissive mode."""
        from metricengine.units import (
            ConversionPolicy,
            convert_decimal,
            use_conversions,
        )

        usd = MoneyUnit("USD")
        gbp = MoneyUnit("GBP")

        permissive_policy = ConversionPolicy(strict=False)
        with use_conversions(permissive_policy):
            result = convert_decimal(Decimal("100"), usd, gbp)

        assert result == Decimal("100")  # Original value returned

    def test_convert_decimal_paths_disabled_strict_mode(self):
        """Test that disabling paths in strict mode raises error for indirect conversions."""
        from metricengine.units import (
            ConversionPolicy,
            convert_decimal,
            use_conversions,
        )

        usd = MoneyUnit("USD")
        gbp = MoneyUnit("GBP")
        eur = MoneyUnit("EUR")

        # Register indirect path but no direct conversion
        @register_conversion(usd, eur)
        def usd_to_eur(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("0.85")

        @register_conversion(eur, gbp)
        def eur_to_gbp(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("0.93")

        no_paths_policy = ConversionPolicy(strict=True, allow_paths=False)
        with use_conversions(no_paths_policy):
            with pytest.raises(KeyError) as exc_info:
                convert_decimal(Decimal("100"), usd, gbp)

        error_msg = str(exc_info.value)
        # When paths are disabled, it tries direct conversion first and fails with descriptive error
        assert "No conversion registered from Money[USD] to Money[GBP]" in error_msg

    def test_convert_decimal_paths_disabled_permissive_mode(self):
        """Test that disabling paths in permissive mode returns original value."""
        from metricengine.units import (
            ConversionPolicy,
            convert_decimal,
            use_conversions,
        )

        usd = MoneyUnit("USD")
        gbp = MoneyUnit("GBP")
        eur = MoneyUnit("EUR")

        # Register indirect path but no direct conversion
        @register_conversion(usd, eur)
        def usd_to_eur(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("0.85")

        @register_conversion(eur, gbp)
        def eur_to_gbp(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("0.93")

        no_paths_policy = ConversionPolicy(strict=False, allow_paths=False)
        with use_conversions(no_paths_policy):
            result = convert_decimal(Decimal("100"), usd, gbp)

        assert result == Decimal("100")  # Original value returned


class TestFinancialValueConversionErrorHandling:
    """Test error handling in FinancialValue.to() method."""

    def setup_method(self):
        """Clear registry before each test."""
        _conversion_registry.clear()

    def teardown_method(self):
        """Clear registry after each test."""
        _conversion_registry.clear()

    def test_to_method_missing_conversion_enhanced_error(self):
        """Test that FinancialValue.to() provides enhanced error context."""
        from metricengine import FinancialValue as FV

        usd = MoneyUnit("USD")
        gbp = MoneyUnit("GBP")

        fv = FV(Decimal("100"), unit=usd)

        with pytest.raises(KeyError) as exc_info:
            fv.to(gbp)

        error_msg = str(exc_info.value)
        assert (
            "Failed to convert FinancialValue from Money[USD] to Money[GBP]"
            in error_msg
        )
        # The actual error comes from path finding since no direct conversion exists
        assert "No conversion path found from Money[USD] to Money[GBP]" in error_msg

    def test_to_method_conversion_function_exception_enhanced_error(self):
        """Test that FinancialValue.to() provides enhanced error context for function exceptions."""
        from metricengine import FinancialValue as FV

        usd = MoneyUnit("USD")
        gbp = MoneyUnit("GBP")

        @register_conversion(usd, gbp)
        def failing_conversion(value: Decimal, ctx: ConversionContext) -> Decimal:
            raise ValueError("Rate service unavailable")

        fv = FV(Decimal("100"), unit=usd)

        with pytest.raises(ValueError) as exc_info:
            fv.to(gbp)

        error_msg = str(exc_info.value)
        assert (
            "Failed to convert FinancialValue from Money[USD] to Money[GBP]"
            in error_msg
        )
        assert "Conversion function failed for Money[USD] to Money[GBP]" in error_msg
        assert "ValueError: Rate service unavailable" in error_msg

    def test_to_method_permissive_mode_returns_original(self):
        """Test that FinancialValue.to() returns original in permissive mode on failure."""
        from metricengine import FinancialValue as FV
        from metricengine.units import ConversionPolicy, use_conversions

        usd = MoneyUnit("USD")
        gbp = MoneyUnit("GBP")

        original = FV(Decimal("100"), unit=usd)

        permissive_policy = ConversionPolicy(strict=False)
        with use_conversions(permissive_policy):
            result = original.to(gbp)

        # Should return original FinancialValue unchanged
        assert result._value == original._value
        assert result.unit == original.unit
        assert result.policy == original.policy
        assert result._is_percentage == original._is_percentage

    def test_to_method_conversion_function_exception_permissive_mode(self):
        """Test that FinancialValue.to() handles function exceptions in permissive mode."""
        from metricengine import FinancialValue as FV
        from metricengine.units import ConversionPolicy, use_conversions

        usd = MoneyUnit("USD")
        gbp = MoneyUnit("GBP")

        @register_conversion(usd, gbp)
        def failing_conversion(value: Decimal, ctx: ConversionContext) -> Decimal:
            raise ValueError("Rate service unavailable")

        original = FV(Decimal("100"), unit=usd)

        permissive_policy = ConversionPolicy(strict=False)
        with use_conversions(permissive_policy):
            result = original.to(gbp)

        # Should return original FinancialValue unchanged
        assert result._value == original._value
        assert result.unit == original.unit
        assert result.policy == original.policy
        assert result._is_percentage == original._is_percentage


class TestConversionLogging:
    """Test logging behavior in conversion system."""

    def setup_method(self):
        """Clear registry before each test."""
        _conversion_registry.clear()

    def teardown_method(self):
        """Clear registry after each test."""
        _conversion_registry.clear()

    def test_conversion_logging_with_caplog(self, caplog):
        """Test that conversions are logged appropriately."""
        import logging

        from metricengine.units import convert_decimal

        # Set logging level to capture debug messages
        caplog.set_level(logging.DEBUG, logger="metricengine.units")

        usd = MoneyUnit("USD")
        gbp = MoneyUnit("GBP")

        @register_conversion(usd, gbp)
        def usd_to_gbp(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("0.79")

        result = convert_decimal(Decimal("100"), usd, gbp)

        # Check that debug log was created
        assert (
            "Direct conversion from Money[USD] to Money[GBP]: 100 -> 79.00"
            in caplog.text
        )

    def test_multi_hop_conversion_logging_with_caplog(self, caplog):
        """Test that multi-hop conversions are logged appropriately."""
        import logging

        from metricengine.units import convert_decimal

        # Set logging level to capture debug messages
        caplog.set_level(logging.DEBUG, logger="metricengine.units")

        usd = MoneyUnit("USD")
        gbp = MoneyUnit("GBP")
        eur = MoneyUnit("EUR")

        @register_conversion(usd, eur)
        def usd_to_eur(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("0.85")

        @register_conversion(eur, gbp)
        def eur_to_gbp(value: Decimal, ctx: ConversionContext) -> Decimal:
            return value * Decimal("0.93")

        result = convert_decimal(Decimal("100"), usd, gbp)

        # Check that path finding and step logs were created
        assert (
            "Found 2-hop conversion path from Money[USD] to Money[GBP]" in caplog.text
        )
        assert "Path step 1: Money[USD] to Money[EUR]: 100 -> 85.00" in caplog.text
        assert "Path step 2: Money[EUR] to Money[GBP]: 85.00 -> 79.05" in caplog.text
        assert (
            "Multi-hop conversion from Money[USD] to Money[GBP]: 100 -> 79.05"
            in caplog.text
        )

    def test_conversion_error_logging_with_caplog(self, caplog):
        """Test that conversion errors are logged appropriately."""
        import logging

        from metricengine.units import (
            ConversionPolicy,
            convert_decimal,
            use_conversions,
        )

        # Set logging level to capture error messages
        caplog.set_level(logging.ERROR, logger="metricengine.units")

        usd = MoneyUnit("USD")
        gbp = MoneyUnit("GBP")

        @register_conversion(usd, gbp)
        def failing_conversion(value: Decimal, ctx: ConversionContext) -> Decimal:
            raise ValueError("Rate lookup failed")

        permissive_policy = ConversionPolicy(strict=False)
        with use_conversions(permissive_policy):
            result = convert_decimal(Decimal("100"), usd, gbp)

        # Check that error was logged
        assert (
            "Conversion function failed for Money[USD] to Money[GBP]: ValueError: Rate lookup failed"
            in caplog.text
        )

    def test_missing_conversion_logging_with_caplog(self, caplog):
        """Test that missing conversions are logged appropriately."""
        import logging

        from metricengine.units import (
            ConversionPolicy,
            convert_decimal,
            use_conversions,
        )

        # Set logging level to capture info and warning messages
        caplog.set_level(logging.INFO, logger="metricengine.units")

        usd = MoneyUnit("USD")
        gbp = MoneyUnit("GBP")

        permissive_policy = ConversionPolicy(strict=False)
        with use_conversions(permissive_policy):
            result = convert_decimal(Decimal("100"), usd, gbp)

        # Check that warning and info messages were logged
        assert "No conversion path found from Money[USD] to Money[GBP]" in caplog.text
        assert (
            "Returning original value due to missing conversion path in permissive mode"
            in caplog.text
        )
