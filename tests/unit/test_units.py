"""Tests for the Unit dataclass and helper functions."""

import pytest

from metricengine.units import MoneyUnit as Money
from metricengine.units import NewUnit as Unit
from metricengine.units import Pct, Qty


class TestUnit:
    """Test the Unit dataclass."""

    def test_unit_creation(self):
        """Test basic Unit creation with category and code."""
        unit = Unit("Money", "USD")
        assert unit.category == "Money"
        assert unit.code == "USD"

    def test_unit_immutability(self):
        """Test that Unit instances are immutable (frozen)."""
        unit = Unit("Money", "USD")
        with pytest.raises(AttributeError):
            unit.category = "Quantity"
        with pytest.raises(AttributeError):
            unit.code = "EUR"

    def test_unit_equality(self):
        """Test Unit equality comparison."""
        unit1 = Unit("Money", "USD")
        unit2 = Unit("Money", "USD")
        unit3 = Unit("Money", "EUR")
        unit4 = Unit("Quantity", "USD")

        # Same category and code should be equal
        assert unit1 == unit2
        assert unit1 is not unit2  # Different instances

        # Different code should not be equal
        assert unit1 != unit3

        # Different category should not be equal
        assert unit1 != unit4

    def test_unit_hashing(self):
        """Test that Unit instances are hashable and can be used as dict keys."""
        unit1 = Unit("Money", "USD")
        unit2 = Unit("Money", "USD")
        unit3 = Unit("Money", "EUR")

        # Same units should have same hash
        assert hash(unit1) == hash(unit2)

        # Can be used as dict keys
        unit_dict = {unit1: "US Dollar", unit3: "Euro"}
        assert unit_dict[unit2] == "US Dollar"  # unit2 equals unit1
        assert len(unit_dict) == 2

    def test_unit_string_representation(self):
        """Test Unit string representation in 'Category[code]' format."""
        unit = Unit("Money", "USD")
        assert str(unit) == "Money[USD]"

        unit = Unit("Quantity", "kg")
        assert str(unit) == "Quantity[kg]"

        unit = Unit("Percent", "bp")
        assert str(unit) == "Percent[bp]"

        # Test with custom category and code
        unit = Unit("Custom", "seats")
        assert str(unit) == "Custom[seats]"

    def test_unit_repr(self):
        """Test Unit repr representation."""
        unit = Unit("Money", "USD")
        # Should be a valid Python expression that recreates the object
        assert repr(unit) == "NewUnit(category='Money', code='USD')"


class TestMoneyHelper:
    """Test the Money helper function."""

    def test_money_creation(self):
        """Test Money helper creates correct Unit."""
        usd = Money("USD")
        assert isinstance(usd, Unit)
        assert usd.category == "Money"
        assert usd.code == "USD"

    def test_money_string_representation(self):
        """Test Money unit string representation."""
        usd = Money("USD")
        assert str(usd) == "Money[USD]"

        eur = Money("EUR")
        assert str(eur) == "Money[EUR]"

        gbp = Money("GBP")
        assert str(gbp) == "Money[GBP]"

    def test_money_equality(self):
        """Test Money unit equality."""
        usd1 = Money("USD")
        usd2 = Money("USD")
        eur = Money("EUR")

        assert usd1 == usd2
        assert usd1 != eur

    def test_money_different_currencies(self):
        """Test Money helper with various currency codes."""
        currencies = ["USD", "EUR", "GBP", "JPY", "CAD", "AUD", "CHF"]

        for code in currencies:
            money_unit = Money(code)
            assert money_unit.category == "Money"
            assert money_unit.code == code
            assert str(money_unit) == f"Money[{code}]"


class TestQtyHelper:
    """Test the Qty helper function."""

    def test_qty_creation(self):
        """Test Qty helper creates correct Unit."""
        kg = Qty("kg")
        assert isinstance(kg, Unit)
        assert kg.category == "Quantity"
        assert kg.code == "kg"

    def test_qty_string_representation(self):
        """Test Qty unit string representation."""
        kg = Qty("kg")
        assert str(kg) == "Quantity[kg]"

        liter = Qty("L")
        assert str(liter) == "Quantity[L]"

        meter = Qty("m")
        assert str(meter) == "Quantity[m]"

    def test_qty_equality(self):
        """Test Qty unit equality."""
        kg1 = Qty("kg")
        kg2 = Qty("kg")
        liter = Qty("L")

        assert kg1 == kg2
        assert kg1 != liter

    def test_qty_different_units(self):
        """Test Qty helper with various quantity units."""
        units = ["kg", "L", "m", "cm", "g", "ml", "ft", "lb"]

        for code in units:
            qty_unit = Qty(code)
            assert qty_unit.category == "Quantity"
            assert qty_unit.code == code
            assert str(qty_unit) == f"Quantity[{code}]"


class TestPctHelper:
    """Test the Pct helper function."""

    def test_pct_creation_default(self):
        """Test Pct helper creates correct Unit with default code."""
        ratio = Pct()
        assert isinstance(ratio, Unit)
        assert ratio.category == "Percent"
        assert ratio.code == "ratio"

    def test_pct_creation_custom_code(self):
        """Test Pct helper creates correct Unit with custom code."""
        bp = Pct("bp")
        assert isinstance(bp, Unit)
        assert bp.category == "Percent"
        assert bp.code == "bp"

    def test_pct_string_representation(self):
        """Test Pct unit string representation."""
        ratio = Pct()
        assert str(ratio) == "Percent[ratio]"

        bp = Pct("bp")
        assert str(bp) == "Percent[bp]"

        percent = Pct("%")
        assert str(percent) == "Percent[%]"

    def test_pct_equality(self):
        """Test Pct unit equality."""
        ratio1 = Pct()
        ratio2 = Pct("ratio")  # Explicit default
        bp = Pct("bp")

        assert ratio1 == ratio2
        assert ratio1 != bp

    def test_pct_different_codes(self):
        """Test Pct helper with various percent codes."""
        codes = ["ratio", "bp", "%", "pct", "percent"]

        for code in codes:
            pct_unit = Pct(code)
            assert pct_unit.category == "Percent"
            assert pct_unit.code == code
            assert str(pct_unit) == f"Percent[{code}]"


class TestHelperFunctionInteraction:
    """Test interactions between different helper functions."""

    def test_different_helpers_not_equal(self):
        """Test that units from different helpers are not equal even with same code."""
        money_usd = Money("USD")
        qty_usd = Qty("USD")  # Unusual but possible

        assert money_usd != qty_usd
        assert money_usd.code == qty_usd.code
        assert money_usd.category != qty_usd.category

    def test_helper_functions_return_unit_instances(self):
        """Test that all helper functions return Unit instances."""
        money = Money("USD")
        qty = Qty("kg")
        pct = Pct("bp")

        assert isinstance(money, Unit)
        assert isinstance(qty, Unit)
        assert isinstance(pct, Unit)

    def test_mixed_unit_collection(self):
        """Test that units from different helpers can be stored together."""
        units = [
            Money("USD"),
            Money("EUR"),
            Qty("kg"),
            Qty("L"),
            Pct("ratio"),
            Pct("bp"),
        ]

        # All should be Unit instances
        assert all(isinstance(unit, Unit) for unit in units)

        # Should be able to use as set (hashable)
        unit_set = set(units)
        assert len(unit_set) == len(units)  # All unique

        # Should be able to use as dict keys
        unit_dict = {unit: str(unit) for unit in units}
        assert len(unit_dict) == len(units)


class TestUnitEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_strings(self):
        """Test Unit creation with empty strings."""
        unit = Unit("", "")
        assert unit.category == ""
        assert unit.code == ""
        assert str(unit) == "[]"

    def test_special_characters(self):
        """Test Unit creation with special characters."""
        unit = Unit("Money/Currency", "USD$")
        assert unit.category == "Money/Currency"
        assert unit.code == "USD$"
        assert str(unit) == "Money/Currency[USD$]"

    def test_unicode_characters(self):
        """Test Unit creation with unicode characters."""
        unit = Unit("货币", "¥")
        assert unit.category == "货币"
        assert unit.code == "¥"
        assert str(unit) == "货币[¥]"

    def test_long_strings(self):
        """Test Unit creation with long strings."""
        long_category = "A" * 100
        long_code = "B" * 50
        unit = Unit(long_category, long_code)
        assert unit.category == long_category
        assert unit.code == long_code
        assert str(unit) == f"{long_category}[{long_code}]"

    def test_helper_with_empty_code(self):
        """Test helper functions with empty code."""
        money = Money("")
        qty = Qty("")
        pct = Pct("")

        assert str(money) == "Money[]"
        assert str(qty) == "Quantity[]"
        assert str(pct) == "Percent[]"
