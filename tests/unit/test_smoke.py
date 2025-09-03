"""Smoke tests to verify the Metric Engine works correctly."""

from decimal import Decimal

import pytest

from metricengine import (
    Engine,
    FinancialValue,
    MissingInputError,
    Policy,
)
from metricengine.policy import PercentDisplay
from metricengine.policy_context import use_policy


class TestMetricEngineSmoke:
    """Smoke tests for Metric Engine functionality."""

    def test_basic_functionality(self):
        """Test basic functionality of the engine."""
        # Create engine with custom policy
        policy = Policy(decimal_places=2)
        engine = Engine(policy)

        # Test simple calculation
        result = engine.calculate(
            "gross_margin_percentage", {"sales": 1000, "cost": 300}
        )
        assert result.as_decimal() == Decimal("70.00")

        # Test tax calculation
        result = engine.calculate("sales_ex_tax", {"sales": 110, "tax_rate": 0.1})
        assert result.as_decimal() == Decimal("100.00")

        # Test complex dependency chain
        result = engine.calculate(
            "gross_margin_percentage_ex_tax",
            {"sales": 110, "cost": 30, "tax_rate": 0.1},
        )
        assert result.as_decimal() == Decimal("70.00")

    def test_error_handling(self):
        """Test error handling."""
        engine = Engine()

        # Test missing input error
        with pytest.raises(MissingInputError):
            engine.calculate("gross_margin_percentage", {"sales": 1000})

        # Test invalid calculation name
        with pytest.raises(MissingInputError):
            engine.calculate("nonexistent_calc", {"input": 123})

    def test_financial_value(self):
        """Test FinancialValue functionality."""
        policy = Policy(decimal_places=2)

        # Test creation and basic operations
        value1 = FinancialValue(Decimal("100.456"), policy)
        value2 = FinancialValue(Decimal("50.123"), policy)

        # Test quantization
        assert value1.as_decimal() == Decimal("100.46")

        # Test arithmetic
        result = value1 + value2
        assert isinstance(result, FinancialValue)
        assert result.as_decimal() == Decimal("150.58")  # 100.46 + 50.12

        # Test comparison
        assert value1 > value2

        # Test string representation
        assert str(value1) == "100.46"

    def test_policy(self):
        """Test Policy functionality."""
        # Test default policy
        policy = Policy()
        assert policy.decimal_places == 2

        # Test custom policy
        custom_policy = Policy(decimal_places=4, none_text="N/A", percent_style="ratio")
        assert custom_policy.decimal_places == 4
        assert custom_policy.none_text == "N/A"

        # Test immutability
        with pytest.raises(AttributeError):
            policy.decimal_places = 5  # type: ignore

    def test_calculations_portfolio(self):
        """Test a portfolio of calculations."""
        engine = Engine(Policy(decimal_places=4))

        test_cases = [
            # (calculation_name, context, expected_result)
            ("cost_percent", {"cost": 300, "sales": 1000}, "30.0000"),
            ("variance_percentage", {"actual": 120, "expected": 100}, "20.0000"),
            (
                "cogs",
                {"opening_inventory": 200, "purchases": 800, "closing_inventory": 150},
                "850.0000",
            ),
            ("percentage_of_total", {"part": 250, "total": 1000}, "25.0000"),
            ("fnb_sales", {"food_sales": 600, "beverage_sales": 400}, "1000.0000"),
        ]

        for calc_name, ctx, expected in test_cases:
            result = engine.calculate(calc_name, ctx)
            assert result.as_decimal() == Decimal(
                expected
            ), f"{calc_name}: expected {expected}, got {result.as_decimal()}"

    def test_convenience_imports(self):
        """Test that convenience imports work correctly."""
        # Test importing from metricengine directly
        from metricengine import Engine as ConvenienceEngine
        from metricengine import Engine as DirectEngine

        # Should be the same class
        assert ConvenienceEngine is DirectEngine

        # Test using kwargs syntax
        engine = ConvenienceEngine()
        result = engine.calculate("gross_profit", sales=1000, cost=650)
        assert result.as_decimal() == Decimal("350.00")

    @pytest.mark.parametrize(
        ("mode", "expected_margin"),
        [
            ("percent", Decimal("35.00")),
            ("ratio", Decimal("0.35")),
            (None, Decimal("35.00")),
        ],
    )
    def test_ratio_conversion(self, mode: PercentDisplay, expected_margin: Decimal):
        """Test the ratio() method for percentage conversions."""
        engine = Engine()

        # Calculate a percentage
        with use_policy(Policy(percent_style=mode)):
            margin = engine.calculate("gross_margin_percentage", sales=1000, cost=650)
            assert margin.as_decimal() == expected_margin

        # Convert to ratio
        ratio = margin.ratio()
        assert ratio.as_decimal() == Decimal("0.35")

        # Test with undefined value
        undefined = engine.calculate("variance_percentage", actual=100, expected=0)
        assert undefined.is_none()
        assert undefined.ratio().is_none()

    @pytest.mark.parametrize(
        ("mode", "expected_margin", "expected_cost_percent"),
        [
            ("percent", Decimal("35.00"), Decimal("65.00")),
            ("ratio", Decimal("0.35"), Decimal("0.65")),
            (None, Decimal("35.00"), Decimal("65.00")),
        ],
    )
    def test_calculate_many_with_kwargs(
        self,
        mode: PercentDisplay,
        expected_margin: Decimal,
        expected_cost_percent: Decimal,
    ):
        """Test calculate_many with keyword arguments."""
        engine = Engine()

        with use_policy(Policy(percent_style=mode)):
            results = engine.calculate_many(
                {"gross_profit", "gross_margin_percentage", "cost_percent"},
                sales=1000,
                cost=650,
            )

            assert len(results) == 3
            assert results["gross_profit"].as_decimal() == Decimal("350.00")
            assert results["gross_margin_percentage"].as_decimal() == expected_margin
            assert results["cost_percent"].as_decimal() == expected_cost_percent
