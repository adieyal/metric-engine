"""Tests for unit-aware rendering system."""
from __future__ import annotations

from metricengine.rendering import (
    HtmlRenderer,
    MarkdownRenderer,
    TextRenderer,
    get_currency_symbol,
    get_unit_display_info,
)
from metricengine.units import MoneyUnit, NewUnit, Pct, Qty
from metricengine.value import FinancialValue as FV


class TestCurrencySymbolMapping:
    """Test currency symbol mapping functionality."""

    def test_get_currency_symbol_known_currencies(self):
        """Test getting symbols for known currencies."""
        assert get_currency_symbol("USD") == "$"
        assert get_currency_symbol("EUR") == "€"
        assert get_currency_symbol("GBP") == "£"
        assert get_currency_symbol("JPY") == "¥"
        assert get_currency_symbol("ZAR") == "R"

    def test_get_currency_symbol_case_insensitive(self):
        """Test that currency symbol lookup is case insensitive."""
        assert get_currency_symbol("usd") == "$"
        assert get_currency_symbol("Eur") == "€"
        assert get_currency_symbol("gbp") == "£"

    def test_get_currency_symbol_unknown_currency(self):
        """Test fallback to currency code for unknown currencies."""
        assert get_currency_symbol("XYZ") == "XYZ"
        assert get_currency_symbol("UNKNOWN") == "UNKNOWN"


class TestUnitDisplayInfo:
    """Test unit display information extraction."""

    def test_get_unit_display_info_dimensionless_unit(self):
        """Test unit display info for FinancialValue with default Dimensionless unit."""
        fv = FV(100)  # Defaults to Dimensionless unit
        info = get_unit_display_info(fv)

        assert info["unit_type"] == "dimensionless"
        assert info["unit_code"] == "dimensionless"
        assert info["unit_category"] == "Dimensionless"
        assert info["symbol"] == ""
        assert info["css_class"] == "dimensionless"

    def test_get_unit_display_info_money_unit(self):
        """Test unit display info for Money units."""
        usd = MoneyUnit("USD")
        fv = FV(100, unit=usd)
        info = get_unit_display_info(fv)

        assert info["unit_type"] == "money"
        assert info["unit_code"] == "USD"
        assert info["unit_category"] == "Money"
        assert info["symbol"] == "$"
        assert info["css_class"] == "money"

    def test_get_unit_display_info_quantity_unit(self):
        """Test unit display info for Quantity units."""
        kg = Qty("kg")
        fv = FV(100, unit=kg)
        info = get_unit_display_info(fv)

        assert info["unit_type"] == "quantity"
        assert info["unit_code"] == "kg"
        assert info["unit_category"] == "Quantity"
        assert info["symbol"] == "kg"
        assert info["css_class"] == "quantity"

    def test_get_unit_display_info_percent_unit(self):
        """Test unit display info for Percent units."""
        ratio = Pct()
        fv = FV(0.15, unit=ratio)
        info = get_unit_display_info(fv)

        assert info["unit_type"] == "percent"
        assert info["unit_code"] == "ratio"
        assert info["unit_category"] == "Percent"
        assert info["symbol"] == "%"
        assert info["css_class"] == "percent"

    def test_get_unit_display_info_percent_unit_with_code(self):
        """Test unit display info for Percent units with custom code."""
        bp = Pct("bp")
        fv = FV(150, unit=bp)
        info = get_unit_display_info(fv)

        assert info["unit_type"] == "percent"
        assert info["unit_code"] == "bp"
        assert info["unit_category"] == "Percent"
        assert info["symbol"] == "bp"
        assert info["css_class"] == "percent"

    def test_get_unit_display_info_custom_unit(self):
        """Test unit display info for custom units."""
        custom = NewUnit("Custom", "widgets")
        fv = FV(100, unit=custom)
        info = get_unit_display_info(fv)

        assert info["unit_type"] == "custom"
        assert info["unit_code"] == "widgets"
        assert info["unit_category"] == "Custom"
        assert info["symbol"] == "widgets"
        assert info["css_class"] == "custom"


class TestUnitAwareTextRenderer:
    """Test unit-aware text rendering."""

    def test_text_renderer_basic_no_symbol(self):
        """Test basic text rendering without symbols."""
        renderer = TextRenderer()
        usd = MoneyUnit("USD")
        amount = FV(1234.56, unit=usd)

        result = renderer.render(amount)
        assert result == amount.as_str()
        assert "$" not in result  # No symbol by default

    def test_text_renderer_with_symbol_prefix(self):
        """Test text rendering with currency symbol prefix."""
        renderer = TextRenderer()
        usd = MoneyUnit("USD")
        amount = FV(1234.56, unit=usd)

        result = renderer.render(amount, context={"include_symbol": True})
        # Only add symbol if not already present in formatted text
        if "$" not in amount.as_str():
            assert result.startswith("$")
        else:
            assert result == amount.as_str()

    def test_text_renderer_with_symbol_suffix(self):
        """Test text rendering with currency symbol suffix."""
        renderer = TextRenderer()
        eur = MoneyUnit("EUR")
        amount = FV(1234.56, unit=eur)

        result = renderer.render(
            amount, context={"include_symbol": True, "symbol_position": "suffix"}
        )
        # Only add symbol if not already present in formatted text
        if "€" not in amount.as_str():
            assert result.endswith(" €")
        else:
            assert result == amount.as_str()

    def test_text_renderer_non_money_unit(self):
        """Test text rendering with non-money units doesn't add symbols."""
        renderer = TextRenderer()
        kg = Qty("kg")
        amount = FV(100, unit=kg)

        result = renderer.render(amount, context={"include_symbol": True})
        assert result == amount.as_str()  # No symbol added for non-money units


class TestUnitAwareHtmlRenderer:
    """Test unit-aware HTML rendering."""

    def test_html_renderer_money_unit_classes_and_attributes(self):
        """Test HTML rendering includes proper classes and data attributes for money units."""
        renderer = HtmlRenderer()
        usd = MoneyUnit("USD")
        amount = FV(1234.56, unit=usd)

        result = renderer.render(amount)

        # Check CSS classes
        assert 'class="fv positive unit-money"' in result

        # Check data attributes
        assert 'data-unit-type="money"' in result
        assert 'data-unit-code="USD"' in result
        assert 'data-unit-category="Money"' in result
        assert 'data-currency="USD"' in result
        assert 'data-currency-symbol="$"' in result

    def test_html_renderer_quantity_unit_attributes(self):
        """Test HTML rendering includes proper attributes for quantity units."""
        renderer = HtmlRenderer()
        kg = Qty("kg")
        amount = FV(100, unit=kg)

        result = renderer.render(amount)

        # Check CSS classes
        assert 'class="fv positive unit-quantity"' in result

        # Check data attributes
        assert 'data-unit-type="quantity"' in result
        assert 'data-unit-code="kg"' in result
        assert 'data-unit-category="Quantity"' in result
        # No currency attributes for quantity units
        assert "data-currency=" not in result

    def test_html_renderer_percent_unit_attributes(self):
        """Test HTML rendering includes proper attributes for percent units."""
        renderer = HtmlRenderer()
        ratio = Pct()
        amount = FV(0.15, unit=ratio)

        result = renderer.render(amount)

        # Check CSS classes
        assert 'class="fv positive unit-percent percentage"' in result

        # Check data attributes
        assert 'data-unit-type="percent"' in result
        assert 'data-unit-code="ratio"' in result
        assert 'data-unit-category="Percent"' in result

    def test_html_renderer_negative_amount(self):
        """Test HTML rendering of negative amounts with units."""
        renderer = HtmlRenderer()
        usd = MoneyUnit("USD")
        amount = FV(-1234.56, unit=usd)

        result = renderer.render(amount)

        assert 'class="fv negative unit-money"' in result
        assert 'data-currency="USD"' in result

    def test_html_renderer_none_value_with_unit(self):
        """Test HTML rendering of None values with units."""
        renderer = HtmlRenderer()
        usd = MoneyUnit("USD")
        none_amount = FV.none_with_unit(usd)

        result = renderer.render(none_amount)

        assert 'class="fv none unit-money"' in result
        assert 'data-unit-type="money"' in result

    def test_html_renderer_with_symbol_display(self):
        """Test HTML rendering with symbol display enabled."""
        renderer = HtmlRenderer()
        gbp = MoneyUnit("GBP")
        amount = FV(1234.56, unit=gbp)

        result = renderer.render(amount, context={"include_symbol": True})

        # Should include currency symbol in display if not already present
        if "£" not in amount.as_str():
            assert "£" in result
        assert 'data-currency-symbol="£"' in result

    def test_html_renderer_custom_tag_with_units(self):
        """Test HTML rendering with custom tag and unit attributes."""
        renderer = HtmlRenderer()
        usd = MoneyUnit("USD")
        amount = FV(1234.56, unit=usd)

        result = renderer.render(amount, context={"tag": "div"})

        assert result.startswith('<div class="fv positive unit-money"')
        assert 'data-currency="USD"' in result
        assert result.endswith("</div>")

    def test_html_renderer_custom_attributes_with_units(self):
        """Test HTML rendering with custom attributes alongside unit attributes."""
        renderer = HtmlRenderer()
        eur = MoneyUnit("EUR")
        amount = FV(1234.56, unit=eur)

        result = renderer.render(
            amount, context={"attributes": {"data-test": "value", "id": "amount-1"}}
        )

        # Should have both custom and unit attributes
        assert 'data-test="value"' in result
        assert 'id="amount-1"' in result
        assert 'data-currency="EUR"' in result
        assert 'data-currency-symbol="€"' in result


class TestUnitAwareMarkdownRenderer:
    """Test unit-aware Markdown rendering."""

    def test_markdown_renderer_basic_with_units(self):
        """Test basic Markdown rendering with units."""
        renderer = MarkdownRenderer()
        usd = MoneyUnit("USD")
        amount = FV(1234.56, unit=usd)

        result = renderer.render(amount)
        assert result == amount.as_str()

    def test_markdown_renderer_negative_bold_with_units(self):
        """Test Markdown rendering makes negatives bold with units."""
        renderer = MarkdownRenderer()
        gbp = MoneyUnit("GBP")
        amount = FV(-1234.56, unit=gbp)

        result = renderer.render(amount)

        # Should be wrapped in ** for bold
        assert result.startswith("**")
        assert result.endswith("**")

    def test_markdown_renderer_percentage_italic_with_units(self):
        """Test Markdown rendering can make percentages italic with units."""
        renderer = MarkdownRenderer()
        ratio = Pct()
        rate = FV(0.155, unit=ratio)

        result = renderer.render(rate, context={"italic": True})

        # Should be wrapped in * for italic
        assert result.startswith("*")
        assert result.endswith("*")

    def test_markdown_renderer_with_symbol_display(self):
        """Test Markdown rendering with symbol display enabled."""
        renderer = MarkdownRenderer()
        jpy = MoneyUnit("JPY")
        amount = FV(1234, unit=jpy)

        result = renderer.render(amount, context={"include_symbol": True})

        # Should include currency symbol if not already present
        if "¥" not in amount.as_str():
            assert "¥" in result

    def test_markdown_renderer_combined_formatting_with_units(self):
        """Test Markdown rendering with multiple formatting options and units."""
        renderer = MarkdownRenderer()
        bp = Pct("bp")
        rate = FV(-155, unit=bp)

        result = renderer.render(
            rate, context={"bold": True, "italic": True, "code": True}
        )

        # Should have all formatting
        assert "`" in result
        assert "**" in result
        assert "*" in result


class TestRenderingBackwardCompatibility:
    """Test that unit-aware rendering maintains backward compatibility."""

    def test_legacy_money_unit_rendering(self):
        """Test rendering with legacy Money unit classes."""
        from metricengine.units import Money

        renderer = HtmlRenderer()
        amount = FV(1234.56, unit=Money)

        result = renderer.render(amount)

        # Should still work with legacy units
        assert 'class="fv positive unit-money"' in result
        # May not have all new data attributes but should not crash

    def test_dimensionless_unit_rendering(self):
        """Test that rendering with default Dimensionless unit works correctly."""
        renderer = HtmlRenderer()
        amount = FV(1234.56)  # Defaults to Dimensionless unit

        result = renderer.render(amount)

        # Should have dimensionless unit attributes
        assert 'class="fv positive unit-dimensionless"' in result
        assert 'data-unit-type="dimensionless"' in result
        # Should not have currency attributes for dimensionless units
        assert "data-currency=" not in result

    def test_explicit_none_unit_rendering(self):
        """Test rendering with explicitly set None unit."""
        renderer = HtmlRenderer()
        amount = FV(1234.56, unit=None)

        result = renderer.render(amount)

        # Should work without unit attributes
        assert 'class="fv positive"' in result
        # Should not have unit-specific attributes
        assert "data-unit-type" not in result
        assert "data-currency" not in result

    def test_existing_context_options_still_work(self):
        """Test that existing context options continue to work."""
        renderer = HtmlRenderer()
        usd = MoneyUnit("USD")
        amount = FV(1234.56, unit=usd)

        result = renderer.render(
            amount,
            context={
                "css_classes": "highlight important",
                "attributes": {"data-test": "value"},
                "tag": "div",
            },
        )

        # Should have both old and new features
        assert 'class="fv positive unit-money highlight important"' in result
        assert 'data-test="value"' in result
        assert 'data-currency="USD"' in result
        assert result.startswith("<div")
        assert result.endswith("</div>")


class TestRenderingIntegrationWithUnits:
    """Test rendering system integration with different unit types."""

    def test_money_rendering_different_currencies(self):
        """Test rendering different currency units."""
        renderer = HtmlRenderer()

        # Test various currencies
        currencies = [
            ("USD", "$"),
            ("EUR", "€"),
            ("GBP", "£"),
            ("JPY", "¥"),
            ("ZAR", "R"),
        ]

        for code, symbol in currencies:
            unit = MoneyUnit(code)
            amount = FV(1234.56, unit=unit)
            result = amount.render("html")

            assert f'data-currency="{code}"' in result
            assert f'data-currency-symbol="{symbol}"' in result

    def test_quantity_rendering_different_units(self):
        """Test rendering different quantity units."""
        renderer = HtmlRenderer()

        quantities = ["kg", "L", "m", "ft", "pieces"]

        for unit_code in quantities:
            unit = Qty(unit_code)
            amount = FV(100, unit=unit)
            result = amount.render("html")

            assert f'data-unit-code="{unit_code}"' in result
            assert 'data-unit-type="quantity"' in result
            assert 'class="fv positive unit-quantity"' in result

    def test_percent_rendering_different_codes(self):
        """Test rendering different percent unit codes."""
        renderer = HtmlRenderer()

        # Default ratio
        ratio = Pct()
        amount = FV(0.15, unit=ratio)
        result = amount.render("html")

        assert 'data-unit-code="ratio"' in result
        assert 'data-unit-type="percent"' in result
        assert 'class="fv positive unit-percent percentage"' in result

        # Basis points
        bp = Pct("bp")
        amount_bp = FV(150, unit=bp)
        result_bp = amount_bp.render("html")

        assert 'data-unit-code="bp"' in result_bp
        assert 'data-unit-type="percent"' in result_bp

    def test_custom_unit_rendering(self):
        """Test rendering custom unit types."""
        renderer = HtmlRenderer()

        custom = NewUnit("Custom", "widgets")
        amount = FV(100, unit=custom)
        result = amount.render("html")

        assert 'data-unit-type="custom"' in result
        assert 'data-unit-code="widgets"' in result
        assert 'data-unit-category="Custom"' in result
        assert 'class="fv positive unit-custom"' in result


class TestFinancialValueRenderMethodWithUnits:
    """Test the render method on FinancialValue instances with units."""

    def test_fv_render_html_with_units(self):
        """Test FV.render() with HTML renderer and units."""
        usd = MoneyUnit("USD")
        amount = FV(1234.56, unit=usd)

        result = amount.render("html")
        assert 'class="fv positive unit-money"' in result
        assert 'data-currency="USD"' in result

    def test_fv_render_with_unit_context(self):
        """Test FV.render() passes unit-aware context to renderer."""
        gbp = MoneyUnit("GBP")
        amount = FV(1234.56, unit=gbp)

        result = amount.render("html", include_symbol=True, css_classes="highlight")
        assert "highlight" in result
        assert 'data-currency-symbol="£"' in result

    def test_fv_render_text_with_symbol(self):
        """Test FV.render() with text renderer and symbol display."""
        eur = MoneyUnit("EUR")
        amount = FV(1234.56, unit=eur)

        result = amount.render("text", include_symbol=True)
        # Only add symbol if not already in formatted text
        if "€" not in amount.as_str():
            assert "€" in result

    def test_fv_render_markdown_with_units(self):
        """Test FV.render() with Markdown renderer and units."""
        jpy = MoneyUnit("JPY")
        amount = FV(-1234, unit=jpy)

        result = amount.render("markdown")
        # Should be bold by default for negatives
        assert result.startswith("**")
        assert result.endswith("**")
