"""Tests for profitability calculations module."""

from decimal import Decimal

import pytest

from metricengine.engine import Engine
from metricengine.exceptions import CalculationError
from metricengine.policy import Policy
from metricengine.units import Money
from metricengine.value import FV


class TestProfitabilityCalculations:
    """Test profitability calculations with comprehensive coverage."""

    def setup_method(self):
        """Set up test fixtures."""
        self.engine = Engine(Policy(decimal_places=4, arithmetic_strict=False))
        self.strict_engine = Engine(Policy(decimal_places=4, arithmetic_strict=True))

    # ── gross profit tests ───────────────────────────────────────────────────────

    def test_gross_profit_basic(self):
        """Test basic gross profit calculation."""
        ctx = {"sales": 1000, "cost": 600}
        result = self.engine.calculate("gross_profit", ctx)
        assert result.as_decimal() == Decimal("400.0000")

    def test_gross_profit_with_none_values(self):
        """Test gross profit with None inputs."""
        # None sales
        ctx = {"sales": None, "cost": 600}
        result = self.engine.calculate("gross_profit", ctx)
        assert result.is_none()

        # None cost
        ctx = {"sales": 1000, "cost": None}
        result = self.engine.calculate("gross_profit", ctx)
        assert result.is_none()

    def test_gross_profit_ex_tax_basic(self):
        """Test gross profit excluding tax calculation."""
        ctx = {"sales_ex_tax": 900, "cost": 600}
        result = self.engine.calculate("gross_profit_ex_tax", ctx)
        assert result.as_decimal() == Decimal("300.0000")

    def test_gross_profit_ex_tax_with_none_values(self):
        """Test gross profit ex tax with None inputs."""
        # None sales_ex_tax
        ctx = {"sales_ex_tax": None, "cost": 600}
        result = self.engine.calculate("gross_profit_ex_tax", ctx)
        assert result.is_none()

        # None cost
        ctx = {"sales_ex_tax": 900, "cost": None}
        result = self.engine.calculate("gross_profit_ex_tax", ctx)
        assert result.is_none()

    # ── gross margin tests ───────────────────────────────────────────────────────

    def test_gross_margin_ratio_basic(self):
        """Test basic gross margin ratio calculation."""
        ctx = {"sales": 1000, "cost": 600}
        result = self.engine.calculate("gross_margin_ratio", ctx)
        # (1000 - 600) / 1000 = 0.4
        assert result.as_decimal() == Decimal("0.4000")

    def test_gross_margin_ratio_with_none_values(self):
        """Test gross margin ratio with None inputs."""
        # None gross_profit (derived from sales/cost)
        ctx = {"sales": None, "cost": 600}
        result = self.engine.calculate("gross_margin_ratio", ctx)
        assert result.is_none()

        # None sales
        ctx = {"sales": None, "cost": 600}
        result = self.engine.calculate("gross_margin_ratio", ctx)
        assert result.is_none()

    def test_gross_margin_ratio_zero_sales_strict(self):
        """Test gross margin ratio with zero sales in strict mode."""
        ctx = {"sales": 0, "cost": 600}
        with pytest.raises(
            CalculationError, match="Gross margin undefined for sales == 0"
        ):
            self.strict_engine.calculate("gross_margin_ratio", ctx)

    def test_gross_margin_ratio_zero_sales_safe(self):
        """Test gross margin ratio with zero sales in safe mode."""
        ctx = {"sales": 0, "cost": 600}
        result = self.engine.calculate("gross_margin_ratio", ctx)
        assert result.is_none()

    def test_gross_margin_percentage_basic(self):
        """Test gross margin percentage calculation."""
        ctx = {"sales": 1000, "cost": 300}
        result = self.engine.calculate("gross_margin_percentage", ctx)
        # ((1000 - 300) / 1000) * 100 = 70%
        assert result.as_decimal() == Decimal("70.0000")

    def test_gross_margin_percentage_with_none_ratio(self):
        """Test gross margin percentage with None ratio."""
        ctx = {"sales": 0, "cost": 300}  # This will produce None ratio
        result = self.engine.calculate("gross_margin_percentage", ctx)
        assert result.is_none()

    def test_gross_margin_ratio_ex_tax_basic(self):
        """Test gross margin ratio excluding tax calculation."""
        ctx = {"sales_ex_tax": 900, "cost": 540}
        result = self.engine.calculate("gross_margin_ratio_ex_tax", ctx)
        # (900 - 540) / 900 = 360/900 = 0.4
        assert result.as_decimal() == Decimal("0.4000")

    def test_gross_margin_ratio_ex_tax_with_none_values(self):
        """Test gross margin ratio ex tax with None inputs."""
        # None gross_profit_ex_tax
        ctx = {"sales_ex_tax": None, "cost": 540}
        result = self.engine.calculate("gross_margin_ratio_ex_tax", ctx)
        assert result.is_none()

        # None sales_ex_tax
        ctx = {"sales_ex_tax": None, "cost": 540}
        result = self.engine.calculate("gross_margin_ratio_ex_tax", ctx)
        assert result.is_none()

    def test_gross_margin_ratio_ex_tax_zero_sales_strict(self):
        """Test gross margin ratio ex tax with zero sales in strict mode."""
        ctx = {"sales_ex_tax": 0, "cost": 540}
        with pytest.raises(
            CalculationError,
            match="Gross margin \\(ex tax\\) undefined for sales_ex_tax == 0",
        ):
            self.strict_engine.calculate("gross_margin_ratio_ex_tax", ctx)

    def test_gross_margin_ratio_ex_tax_zero_sales_safe(self):
        """Test gross margin ratio ex tax with zero sales in safe mode."""
        ctx = {"sales_ex_tax": 0, "cost": 540}
        result = self.engine.calculate("gross_margin_ratio_ex_tax", ctx)
        assert result.is_none()

    def test_gross_margin_percentage_ex_tax_basic(self):
        """Test gross margin percentage excluding tax calculation."""
        ctx = {"sales_ex_tax": 800, "cost": 480}
        result = self.engine.calculate("gross_margin_percentage_ex_tax", ctx)
        # ((800 - 480) / 800) * 100 = 40%
        assert result.as_decimal() == Decimal("40.0000")

    def test_gross_margin_percentage_ex_tax_with_none_ratio(self):
        """Test gross margin percentage ex tax with None ratio."""
        ctx = {"sales_ex_tax": 0, "cost": 480}  # This will produce None ratio
        result = self.engine.calculate("gross_margin_percentage_ex_tax", ctx)
        assert result.is_none()

    # ── cost ratio tests ─────────────────────────────────────────────────────────

    def test_cost_ratio_basic(self):
        """Test basic cost ratio calculation."""
        ctx = {"cost": 600, "sales": 1000}
        result = self.engine.calculate("cost_ratio", ctx)
        # 600 / 1000 = 0.6
        assert result.as_decimal() == Decimal("0.6000")

    def test_cost_ratio_with_none_values(self):
        """Test cost ratio with None inputs."""
        # None cost
        ctx = {"cost": None, "sales": 1000}
        result = self.engine.calculate("cost_ratio", ctx)
        assert result.is_none()

        # None sales
        ctx = {"cost": 600, "sales": None}
        result = self.engine.calculate("cost_ratio", ctx)
        assert result.is_none()

    def test_cost_ratio_zero_sales_strict(self):
        """Test cost ratio with zero sales in strict mode."""
        ctx = {"cost": 600, "sales": 0}
        with pytest.raises(
            CalculationError, match="Cost ratio undefined for sales == 0"
        ):
            self.strict_engine.calculate("cost_ratio", ctx)

    def test_cost_ratio_zero_sales_safe(self):
        """Test cost ratio with zero sales in safe mode."""
        ctx = {"cost": 600, "sales": 0}
        result = self.engine.calculate("cost_ratio", ctx)
        assert result.is_none()

    def test_cost_percent_basic(self):
        """Test cost percent calculation."""
        ctx = {"cost": 400, "sales": 1000}
        result = self.engine.calculate("cost_percent", ctx)
        # (400 / 1000) * 100 = 40%
        assert result.as_decimal() == Decimal("40.0000")

    def test_cost_percent_with_none_ratio(self):
        """Test cost percent with None ratio."""
        ctx = {"cost": 400, "sales": 0}  # This will produce None ratio
        result = self.engine.calculate("cost_percent", ctx)
        assert result.is_none()

    def test_cost_ratio_ex_tax_basic(self):
        """Test cost ratio excluding tax calculation."""
        ctx = {"cost": 540, "sales_ex_tax": 900}
        result = self.engine.calculate("cost_ratio_ex_tax", ctx)
        # 540 / 900 = 0.6
        assert result.as_decimal() == Decimal("0.6000")

    def test_cost_ratio_ex_tax_with_none_values(self):
        """Test cost ratio ex tax with None inputs."""
        # None cost
        ctx = {"cost": None, "sales_ex_tax": 900}
        result = self.engine.calculate("cost_ratio_ex_tax", ctx)
        assert result.is_none()

        # None sales_ex_tax
        ctx = {"cost": 540, "sales_ex_tax": None}
        result = self.engine.calculate("cost_ratio_ex_tax", ctx)
        assert result.is_none()

    def test_cost_ratio_ex_tax_zero_sales_strict(self):
        """Test cost ratio ex tax with zero sales in strict mode."""
        ctx = {"cost": 540, "sales_ex_tax": 0}
        with pytest.raises(
            CalculationError,
            match="Cost ratio \\(ex tax\\) undefined for sales_ex_tax == 0",
        ):
            self.strict_engine.calculate("cost_ratio_ex_tax", ctx)

    def test_cost_ratio_ex_tax_zero_sales_safe(self):
        """Test cost ratio ex tax with zero sales in safe mode."""
        ctx = {"cost": 540, "sales_ex_tax": 0}
        result = self.engine.calculate("cost_ratio_ex_tax", ctx)
        assert result.is_none()

    def test_cost_percent_ex_tax_basic(self):
        """Test cost percent excluding tax calculation."""
        ctx = {"cost": 360, "sales_ex_tax": 900}
        result = self.engine.calculate("cost_percent_ex_tax", ctx)
        # (360 / 900) * 100 = 40%
        assert result.as_decimal() == Decimal("40.0000")

    def test_cost_percent_ex_tax_with_none_ratio(self):
        """Test cost percent ex tax with None ratio."""
        ctx = {"cost": 360, "sales_ex_tax": 0}  # This will produce None ratio
        result = self.engine.calculate("cost_percent_ex_tax", ctx)
        assert result.is_none()

    # ── net profit & margin tests ────────────────────────────────────────────────

    def test_net_profit_basic(self):
        """Test basic net profit calculation."""
        ctx = {"revenue": 1000, "total_costs": 700}
        result = self.engine.calculate("net_profit", ctx)
        # 1000 - 700 = 300
        assert result.as_decimal() == Decimal("300.0000")

    def test_net_profit_with_none_values(self):
        """Test net profit with None inputs."""
        # None revenue
        ctx = {"revenue": None, "total_costs": 700}
        result = self.engine.calculate("net_profit", ctx)
        assert result.is_none()

        # None total_costs
        ctx = {"revenue": 1000, "total_costs": None}
        result = self.engine.calculate("net_profit", ctx)
        assert result.is_none()

    def test_net_margin_ratio_basic(self):
        """Test basic net margin ratio calculation."""
        ctx = {"revenue": 1000, "total_costs": 700}
        result = self.engine.calculate("net_margin_ratio", ctx)
        # (1000 - 700) / 1000 = 0.3
        assert result.as_decimal() == Decimal("0.3000")

    def test_net_margin_ratio_with_none_values(self):
        """Test net margin ratio with None inputs."""
        # None net_profit (derived from revenue/total_costs)
        ctx = {"revenue": None, "total_costs": 700}
        result = self.engine.calculate("net_margin_ratio", ctx)
        assert result.is_none()

        # None revenue
        ctx = {"revenue": None, "total_costs": 700}
        result = self.engine.calculate("net_margin_ratio", ctx)
        assert result.is_none()

    def test_net_margin_ratio_zero_revenue_strict(self):
        """Test net margin ratio with zero revenue in strict mode."""
        ctx = {"revenue": 0, "total_costs": 700}
        with pytest.raises(
            CalculationError, match="Net margin undefined for revenue == 0"
        ):
            self.strict_engine.calculate("net_margin_ratio", ctx)

    def test_net_margin_ratio_zero_revenue_safe(self):
        """Test net margin ratio with zero revenue in safe mode."""
        ctx = {"revenue": 0, "total_costs": 700}
        result = self.engine.calculate("net_margin_ratio", ctx)
        assert result.is_none()

    def test_net_margin_percentage_basic(self):
        """Test net margin percentage calculation."""
        ctx = {"revenue": 1000, "total_costs": 700}
        result = self.engine.calculate("net_margin_percentage", ctx)
        # ((1000 - 700) / 1000) * 100 = 30%
        assert result.as_decimal() == Decimal("30.0000")

    def test_net_margin_percentage_with_none_ratio(self):
        """Test net margin percentage with None ratio."""
        ctx = {"revenue": 0, "total_costs": 700}  # This will produce None ratio
        result = self.engine.calculate("net_margin_percentage", ctx)
        assert result.is_none()

    # ── tax-adjusted net margin tests ────────────────────────────────────────────

    def test_net_profit_with_tax_basic(self):
        """Test net profit with tax calculation."""
        ctx = {"sales": 1100, "cost": 600, "tax_rate": 0.1}
        result = self.engine.calculate("net_profit_with_tax", ctx)
        # (1100 / 1.1) - 600 = 1000 - 600 = 400
        assert result.as_decimal() == Decimal("400.0000")

    def test_net_profit_with_tax_with_none_values(self):
        """Test net profit with tax with None inputs."""
        # None sales
        ctx = {"sales": None, "cost": 600, "tax_rate": 0.1}
        result = self.engine.calculate("net_profit_with_tax", ctx)
        assert result.is_none()

        # None cost
        ctx = {"sales": 1100, "cost": None, "tax_rate": 0.1}
        result = self.engine.calculate("net_profit_with_tax", ctx)
        assert result.is_none()

        # None tax_rate
        ctx = {"sales": 1100, "cost": 600, "tax_rate": None}
        result = self.engine.calculate("net_profit_with_tax", ctx)
        assert result.is_none()

    def test_net_profit_with_tax_zero_denominator_strict(self):
        """Test net profit with tax with zero denominator in strict mode."""
        ctx = {"sales": 1100, "cost": 600, "tax_rate": -1.0}  # 1 + (-1) = 0
        with pytest.raises(
            CalculationError,
            match="net_profit_with_tax undefined when 1 \\+ tax_rate == 0",
        ):
            self.strict_engine.calculate("net_profit_with_tax", ctx)

    def test_net_profit_with_tax_zero_denominator_safe(self):
        """Test net profit with tax with zero denominator in safe mode."""
        ctx = {"sales": 1100, "cost": 600, "tax_rate": -1.0}  # 1 + (-1) = 0
        result = self.engine.calculate("net_profit_with_tax", ctx)
        assert result.is_none()

    def test_net_margin_with_tax_ratio_basic(self):
        """Test net margin with tax ratio calculation."""
        ctx = {"sales": 1100, "cost": 600, "tax_rate": 0.1, "sales_ex_tax": 1000}
        result = self.engine.calculate("net_margin_with_tax_ratio", ctx)
        # ((1100 / 1.1) - 600) / 1000 = (1000 - 600) / 1000 = 0.4
        assert result.as_decimal() == Decimal("0.4000")

    def test_net_margin_with_tax_ratio_with_none_values(self):
        """Test net margin with tax ratio with None inputs."""
        # None net_profit_with_tax
        ctx = {"sales": None, "cost": 600, "tax_rate": 0.1, "sales_ex_tax": 1000}
        result = self.engine.calculate("net_margin_with_tax_ratio", ctx)
        assert result.is_none()

        # None sales_ex_tax
        ctx = {"sales": 1100, "cost": 600, "tax_rate": 0.1, "sales_ex_tax": None}
        result = self.engine.calculate("net_margin_with_tax_ratio", ctx)
        assert result.is_none()

    def test_net_margin_with_tax_ratio_zero_sales_strict(self):
        """Test net margin with tax ratio with zero sales ex tax in strict mode."""
        ctx = {"sales": 1100, "cost": 600, "tax_rate": 0.1, "sales_ex_tax": 0}
        with pytest.raises(
            CalculationError,
            match="Net margin \\(tax-adjusted\\) undefined for sales_ex_tax == 0",
        ):
            self.strict_engine.calculate("net_margin_with_tax_ratio", ctx)

    def test_net_margin_with_tax_ratio_zero_sales_safe(self):
        """Test net margin with tax ratio with zero sales ex tax in safe mode."""
        ctx = {"sales": 1100, "cost": 600, "tax_rate": 0.1, "sales_ex_tax": 0}
        result = self.engine.calculate("net_margin_with_tax_ratio", ctx)
        assert result.is_none()

    def test_net_margin_with_tax_basic(self):
        """Test net margin with tax percentage calculation."""
        ctx = {"sales": 1100, "cost": 600, "tax_rate": 0.1, "sales_ex_tax": 1000}
        result = self.engine.calculate("net_margin_with_tax", ctx)
        # ((1100 / 1.1) - 600) / 1000 * 100 = 40%
        assert result.as_decimal() == Decimal("40.0000")

    def test_net_margin_with_tax_with_none_ratio(self):
        """Test net margin with tax with None ratio."""
        ctx = {
            "sales": 1100,
            "cost": 600,
            "tax_rate": 0.1,
            "sales_ex_tax": 0,
        }  # This will produce None ratio
        result = self.engine.calculate("net_margin_with_tax", ctx)
        assert result.is_none()

    # ── cost ratio with tax tests ────────────────────────────────────────────────

    def test_cost_ratio_with_tax_basic(self):
        """Test cost ratio with tax calculation."""
        ctx = {"cost": 600, "sales": 1100, "tax_rate": 0.1}
        result = self.engine.calculate("cost_ratio_with_tax", ctx)
        # 600 / (1100 / 1.1) = 600 / 1000 = 0.6
        assert result.as_decimal() == Decimal("0.6000")

    def test_cost_ratio_with_tax_with_none_values(self):
        """Test cost ratio with tax with None inputs."""
        # None cost
        ctx = {"cost": None, "sales": 1100, "tax_rate": 0.1}
        result = self.engine.calculate("cost_ratio_with_tax", ctx)
        assert result.is_none()

        # None sales
        ctx = {"cost": 600, "sales": None, "tax_rate": 0.1}
        result = self.engine.calculate("cost_ratio_with_tax", ctx)
        assert result.is_none()

        # None tax_rate
        ctx = {"cost": 600, "sales": 1100, "tax_rate": None}
        result = self.engine.calculate("cost_ratio_with_tax", ctx)
        assert result.is_none()

    def test_cost_ratio_with_tax_zero_tax_denominator_strict(self):
        """Test cost ratio with tax with zero tax denominator in strict mode."""
        ctx = {"cost": 600, "sales": 1100, "tax_rate": -1.0}  # 1 + (-1) = 0
        with pytest.raises(
            CalculationError,
            match="cost_ratio_with_tax undefined when 1 \\+ tax_rate == 0",
        ):
            self.strict_engine.calculate("cost_ratio_with_tax", ctx)

    def test_cost_ratio_with_tax_zero_tax_denominator_safe(self):
        """Test cost ratio with tax with zero tax denominator in safe mode."""
        ctx = {"cost": 600, "sales": 1100, "tax_rate": -1.0}  # 1 + (-1) = 0
        result = self.engine.calculate("cost_ratio_with_tax", ctx)
        assert result.is_none()

    def test_cost_ratio_with_tax_zero_sales_ex_strict(self):
        """Test cost ratio with tax with zero sales ex tax in strict mode."""
        ctx = {"cost": 600, "sales": 0, "tax_rate": 0.1}  # sales_ex = 0 / 1.1 = 0
        with pytest.raises(
            CalculationError,
            match="cost_ratio_with_tax undefined for sales_ex_tax == 0",
        ):
            self.strict_engine.calculate("cost_ratio_with_tax", ctx)

    def test_cost_ratio_with_tax_zero_sales_ex_safe(self):
        """Test cost ratio with tax with zero sales ex tax in safe mode."""
        ctx = {"cost": 600, "sales": 0, "tax_rate": 0.1}  # sales_ex = 0 / 1.1 = 0
        result = self.engine.calculate("cost_ratio_with_tax", ctx)
        assert result.is_none()

    def test_cost_percentage_with_tax_basic(self):
        """Test cost percentage with tax calculation."""
        ctx = {"cost": 500, "sales": 1100, "tax_rate": 0.1}
        result = self.engine.calculate("cost_percentage_with_tax", ctx)
        # (500 / (1100 / 1.1)) * 100 = (500 / 1000) * 100 = 50%
        assert result.as_decimal() == Decimal("50.0000")

    def test_cost_percentage_with_tax_with_none_ratio(self):
        """Test cost percentage with tax with None ratio."""
        ctx = {"cost": 500, "sales": 0, "tax_rate": 0.1}  # This will produce None ratio
        result = self.engine.calculate("cost_percentage_with_tax", ctx)
        assert result.is_none()

    # ── contribution margin tests ────────────────────────────────────────────────

    def test_contribution_margin_basic(self):
        """Test basic contribution margin calculation."""
        ctx = {"revenue": 1000, "variable_costs": 600}
        result = self.engine.calculate("contribution_margin", ctx)
        # 1000 - 600 = 400
        assert result.as_decimal() == Decimal("400.0000")

    def test_contribution_margin_with_none_values(self):
        """Test contribution margin with None inputs."""
        # None revenue
        ctx = {"revenue": None, "variable_costs": 600}
        result = self.engine.calculate("contribution_margin", ctx)
        assert result.is_none()

        # None variable_costs
        ctx = {"revenue": 1000, "variable_costs": None}
        result = self.engine.calculate("contribution_margin", ctx)
        assert result.is_none()

    def test_contribution_margin_ratio_raw_basic(self):
        """Test contribution margin ratio raw calculation."""
        ctx = {"revenue": 1000, "variable_costs": 600}
        result = self.engine.calculate("contribution_margin_ratio_raw", ctx)
        # (1000 - 600) / 1000 = 0.4
        assert result.as_decimal() == Decimal("0.4000")

    def test_contribution_margin_ratio_raw_with_none_values(self):
        """Test contribution margin ratio raw with None inputs."""
        # None contribution_margin
        ctx = {"revenue": None, "variable_costs": 600}
        result = self.engine.calculate("contribution_margin_ratio_raw", ctx)
        assert result.is_none()

        # None revenue
        ctx = {"revenue": None, "variable_costs": 600}
        result = self.engine.calculate("contribution_margin_ratio_raw", ctx)
        assert result.is_none()

    def test_contribution_margin_ratio_raw_zero_revenue_strict(self):
        """Test contribution margin ratio raw with zero revenue in strict mode."""
        ctx = {"revenue": 0, "variable_costs": 600}
        with pytest.raises(
            CalculationError, match="Contribution margin undefined for revenue == 0"
        ):
            self.strict_engine.calculate("contribution_margin_ratio_raw", ctx)

    def test_contribution_margin_ratio_raw_zero_revenue_safe(self):
        """Test contribution margin ratio raw with zero revenue in safe mode."""
        ctx = {"revenue": 0, "variable_costs": 600}
        result = self.engine.calculate("contribution_margin_ratio_raw", ctx)
        assert result.is_none()

    def test_contribution_margin_ratio_basic(self):
        """Test contribution margin ratio calculation."""
        ctx = {"revenue": 1000, "variable_costs": 400}
        result = self.engine.calculate("contribution_margin_ratio", ctx)
        # ((1000 - 400) / 1000) * 100 = 60%
        assert result.as_decimal() == Decimal("60.0000")

    def test_contribution_margin_ratio_with_none_ratio_raw(self):
        """Test contribution margin ratio with None ratio raw."""
        ctx = {"revenue": 0, "variable_costs": 400}  # This will produce None ratio_raw
        result = self.engine.calculate("contribution_margin_ratio", ctx)
        assert result.is_none()

    # ── operating & EBITDA margin tests ───────────────────────────────────────────

    def test_operating_margin_ratio_basic(self):
        """Test operating margin ratio calculation."""
        ctx = {"operating_income": 200, "revenue": 1000}
        result = self.engine.calculate("operating_margin_ratio", ctx)
        # 200 / 1000 = 0.2
        assert result.as_decimal() == Decimal("0.2000")

    def test_operating_margin_ratio_with_none_values(self):
        """Test operating margin ratio with None inputs."""
        # None operating_income
        ctx = {"operating_income": None, "revenue": 1000}
        result = self.engine.calculate("operating_margin_ratio", ctx)
        assert result.is_none()

        # None revenue
        ctx = {"operating_income": 200, "revenue": None}
        result = self.engine.calculate("operating_margin_ratio", ctx)
        assert result.is_none()

    def test_operating_margin_ratio_zero_revenue_strict(self):
        """Test operating margin ratio with zero revenue in strict mode."""
        ctx = {"operating_income": 200, "revenue": 0}
        with pytest.raises(
            CalculationError, match="Operating margin undefined for revenue == 0"
        ):
            self.strict_engine.calculate("operating_margin_ratio", ctx)

    def test_operating_margin_ratio_zero_revenue_safe(self):
        """Test operating margin ratio with zero revenue in safe mode."""
        ctx = {"operating_income": 200, "revenue": 0}
        result = self.engine.calculate("operating_margin_ratio", ctx)
        assert result.is_none()

    def test_operating_margin_basic(self):
        """Test operating margin calculation."""
        ctx = {"operating_income": 150, "revenue": 1000}
        result = self.engine.calculate("operating_margin", ctx)
        # (150 / 1000) * 100 = 15%
        assert result.as_decimal() == Decimal("15.0000")

    def test_operating_margin_with_none_ratio(self):
        """Test operating margin with None ratio."""
        ctx = {"operating_income": 150, "revenue": 0}  # This will produce None ratio
        result = self.engine.calculate("operating_margin", ctx)
        assert result.is_none()

    def test_ebitda_margin_ratio_basic(self):
        """Test EBITDA margin ratio calculation."""
        ctx = {"ebitda": 300, "revenue": 1000}
        result = self.engine.calculate("ebitda_margin_ratio", ctx)
        # 300 / 1000 = 0.3
        assert result.as_decimal() == Decimal("0.3000")

    def test_ebitda_margin_ratio_with_none_values(self):
        """Test EBITDA margin ratio with None inputs."""
        # None ebitda
        ctx = {"ebitda": None, "revenue": 1000}
        result = self.engine.calculate("ebitda_margin_ratio", ctx)
        assert result.is_none()

        # None revenue
        ctx = {"ebitda": 300, "revenue": None}
        result = self.engine.calculate("ebitda_margin_ratio", ctx)
        assert result.is_none()

    def test_ebitda_margin_ratio_zero_revenue_strict(self):
        """Test EBITDA margin ratio with zero revenue in strict mode."""
        ctx = {"ebitda": 300, "revenue": 0}
        with pytest.raises(
            CalculationError, match="EBITDA margin undefined for revenue == 0"
        ):
            self.strict_engine.calculate("ebitda_margin_ratio", ctx)

    def test_ebitda_margin_ratio_zero_revenue_safe(self):
        """Test EBITDA margin ratio with zero revenue in safe mode."""
        ctx = {"ebitda": 300, "revenue": 0}
        result = self.engine.calculate("ebitda_margin_ratio", ctx)
        assert result.is_none()

    def test_ebitda_margin_basic(self):
        """Test EBITDA margin calculation."""
        ctx = {"ebitda": 250, "revenue": 1000}
        result = self.engine.calculate("ebitda_margin", ctx)
        # (250 / 1000) * 100 = 25%
        assert result.as_decimal() == Decimal("25.0000")

    def test_ebitda_margin_with_none_ratio(self):
        """Test EBITDA margin with None ratio."""
        ctx = {"ebitda": 250, "revenue": 0}  # This will produce None ratio
        result = self.engine.calculate("ebitda_margin", ctx)
        assert result.is_none()

    # ── ROI tests ─────────────────────────────────────────────────────────────────

    def test_roi_ratio_basic(self):
        """Test ROI ratio calculation."""
        ctx = {"gain_from_investment": 200, "cost_of_investment": 1000}
        result = self.engine.calculate("roi_ratio", ctx)
        # 200 / 1000 = 0.2
        assert result.as_decimal() == Decimal("0.2000")

    def test_roi_ratio_with_none_values(self):
        """Test ROI ratio with None inputs."""
        # None gain_from_investment
        ctx = {"gain_from_investment": None, "cost_of_investment": 1000}
        result = self.engine.calculate("roi_ratio", ctx)
        assert result.is_none()

        # None cost_of_investment
        ctx = {"gain_from_investment": 200, "cost_of_investment": None}
        result = self.engine.calculate("roi_ratio", ctx)
        assert result.is_none()

    def test_roi_ratio_zero_cost_strict(self):
        """Test ROI ratio with zero cost in strict mode."""
        ctx = {"gain_from_investment": 200, "cost_of_investment": 0}
        with pytest.raises(
            CalculationError, match="ROI undefined for cost_of_investment == 0"
        ):
            self.strict_engine.calculate("roi_ratio", ctx)

    def test_roi_ratio_zero_cost_safe(self):
        """Test ROI ratio with zero cost in safe mode."""
        ctx = {"gain_from_investment": 200, "cost_of_investment": 0}
        result = self.engine.calculate("roi_ratio", ctx)
        assert result.is_none()

    def test_roi_basic(self):
        """Test ROI percentage calculation."""
        ctx = {"gain_from_investment": 150, "cost_of_investment": 1000}
        result = self.engine.calculate("roi", ctx)
        # (150 / 1000) * 100 = 15%
        assert result.as_decimal() == Decimal("15.0000")

    def test_roi_with_none_ratio(self):
        """Test ROI with None ratio."""
        ctx = {
            "gain_from_investment": 150,
            "cost_of_investment": 0,
        }  # This will produce None ratio
        result = self.engine.calculate("roi", ctx)
        assert result.is_none()

    # ── edge cases and special scenarios ─────────────────────────────────────────

    def test_negative_gross_profit(self):
        """Test calculations with negative gross profit."""
        ctx = {"sales": 800, "cost": 1000}
        result = self.engine.calculate("gross_profit", ctx)
        assert result.as_decimal() == Decimal("-200.0000")

        # Gross margin ratio with negative profit
        result = self.engine.calculate("gross_margin_ratio", ctx)
        # (800 - 1000) / 800 = -200/800 = -0.25
        assert result.as_decimal() == Decimal("-0.2500")

    def test_negative_net_profit(self):
        """Test calculations with negative net profit."""
        ctx = {"revenue": 800, "total_costs": 1000}
        result = self.engine.calculate("net_profit", ctx)
        assert result.as_decimal() == Decimal("-200.0000")

        # Net margin ratio with negative profit
        result = self.engine.calculate("net_margin_ratio", ctx)
        # (800 - 1000) / 800 = -200/800 = -0.25
        assert result.as_decimal() == Decimal("-0.2500")

    def test_cost_higher_than_sales(self):
        """Test cost ratio when cost is higher than sales."""
        ctx = {"cost": 1200, "sales": 1000}
        result = self.engine.calculate("cost_ratio", ctx)
        # 1200 / 1000 = 1.2 (cost is 120% of sales)
        assert result.as_decimal() == Decimal("1.2000")

    def test_zero_variable_costs(self):
        """Test contribution margin with zero variable costs."""
        ctx = {"revenue": 1000, "variable_costs": 0}
        result = self.engine.calculate("contribution_margin", ctx)
        # 1000 - 0 = 1000
        assert result.as_decimal() == Decimal("1000.0000")

        result = self.engine.calculate("contribution_margin_ratio", ctx)
        # (1000 - 0) / 1000 * 100 = 100%
        assert result.as_decimal() == Decimal("100.0000")

    def test_negative_operating_income(self):
        """Test operating margin with negative operating income."""
        ctx = {"operating_income": -100, "revenue": 1000}
        result = self.engine.calculate("operating_margin_ratio", ctx)
        # -100 / 1000 = -0.1
        assert result.as_decimal() == Decimal("-0.1000")

        result = self.engine.calculate("operating_margin", ctx)
        # -10%
        assert result.as_decimal() == Decimal("-10.0000")

    def test_very_small_margins(self):
        """Test calculations with very small margins."""
        ctx = {"sales": 1000000, "cost": 999999}
        result = self.engine.calculate("gross_margin_ratio", ctx)
        # (1000000 - 999999) / 1000000 = 1/1000000 = 0.000001
        assert result.as_decimal() == Decimal("0.0000")  # Rounded to 4 decimal places

    def test_policy_resolution_from_fv_objects(self):
        """Test that policy is correctly resolved from FV objects."""
        policy = Policy(decimal_places=2)
        sales = FV(1000, policy=policy, unit=Money)
        cost = FV(600, unit=Money)  # No policy

        ctx = {"sales": sales, "cost": cost}
        result = self.engine.calculate("gross_profit", ctx)

        # Should complete without errors
        assert result.as_decimal() == Decimal("400.0000")
