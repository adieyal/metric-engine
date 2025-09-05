"""Tests for the custom rendering system."""
from __future__ import annotations

import pytest

from metricengine.factories import money, percent, ratio
from metricengine.policy import DisplayPolicy, Policy
from metricengine.rendering import (
    HtmlRenderer,
    MarkdownRenderer,
    Renderer,
    TextRenderer,
    get_renderer,
    list_renderers,
    register_renderer,
)
from metricengine.value import FV
from metricengine.units import Money


class TestRendererProtocol:
    """Test the Renderer protocol and registration system."""
    
    def test_register_and_get_renderer(self):
        """Test registering and retrieving renderers."""
        class CustomRenderer:
            def render(self, fv, *, context=None):
                return f"Custom: {fv.as_str()}"
        
        renderer = CustomRenderer()
        register_renderer("custom", renderer)
        
        retrieved = get_renderer("custom")
        assert retrieved is renderer
    
    def test_get_nonexistent_renderer_raises_keyerror(self):
        """Test that getting a non-existent renderer raises KeyError."""
        with pytest.raises(KeyError, match="No renderer registered with name 'nonexistent'"):
            get_renderer("nonexistent")
    
    def test_register_invalid_renderer_raises_typeerror(self):
        """Test that registering an invalid renderer raises TypeError."""
        class InvalidRenderer:
            pass  # Missing render method
        
        with pytest.raises(TypeError, match="Renderer must implement the Renderer protocol"):
            register_renderer("invalid", InvalidRenderer())
    
    def test_list_renderers(self):
        """Test listing registered renderers."""
        # Built-in renderers should be registered
        renderers = list_renderers()
        assert "text" in renderers
        assert "html" in renderers
        assert "markdown" in renderers
        
        # Register a custom one
        class TestRenderer:
            def render(self, fv, *, context=None):
                return "test"
        
        register_renderer("test", TestRenderer())
        
        updated_renderers = list_renderers()
        assert "test" in updated_renderers
        assert len(updated_renderers) >= len(renderers) + 1


class TestTextRenderer:
    """Test the built-in text renderer."""
    
    def test_text_renderer_basic(self):
        """Test basic text rendering."""
        renderer = TextRenderer()
        amount = money(1234.56)
        
        result = renderer.render(amount)
        assert result == amount.as_str()
    
    def test_text_renderer_with_context(self):
        """Test that text renderer ignores context."""
        renderer = TextRenderer()
        amount = money(1234.56)
        
        result = renderer.render(amount, context={"ignored": "value"})
        assert result == amount.as_str()


class TestHtmlRenderer:
    """Test the built-in HTML renderer."""
    
    def test_html_renderer_positive_amount(self):
        """Test HTML rendering of positive amounts."""
        renderer = HtmlRenderer()
        amount = money(1234.56)
        
        result = renderer.render(amount)
        
        assert '<span class="fv positive unit-money"' in result
        assert '1,234.56</span>' in result
    
    def test_html_renderer_negative_amount(self):
        """Test HTML rendering of negative amounts."""
        renderer = HtmlRenderer()
        amount = money(-1234.56)
        
        result = renderer.render(amount)
        
        assert '<span class="fv negative unit-money"' in result
        assert '-1,234.56</span>' in result or '(1,234.56)</span>' in result
    
    def test_html_renderer_none_value(self):
        """Test HTML rendering of None values."""
        renderer = HtmlRenderer()
        none_amount = FV.none_with_unit(Money)
        
        result = renderer.render(none_amount)
        
        assert '<span class="fv none unit-money"' in result
        assert '—</span>' in result  # Default none_text
    
    def test_html_renderer_percentage(self):
        """Test HTML rendering of percentages."""
        renderer = HtmlRenderer()
        rate = percent(15.5, input="percent")
        
        result = renderer.render(rate)
        
        assert '<span class="fv positive unit-percent percentage"' in result
        # The percent factory converts 15.5% to 0.155 ratio, which formats as 0.16%
        assert '%</span>' in result
    
    def test_html_renderer_with_custom_classes(self):
        """Test HTML rendering with custom CSS classes."""
        renderer = HtmlRenderer()
        amount = money(1234.56)
        
        result = renderer.render(amount, context={"css_classes": "highlight important"})
        
        assert 'class="fv positive unit-money highlight important"' in result
    
    def test_html_renderer_with_custom_classes_list(self):
        """Test HTML rendering with custom CSS classes as list."""
        renderer = HtmlRenderer()
        amount = money(1234.56)
        
        result = renderer.render(amount, context={"css_classes": ["highlight", "important"]})
        
        assert 'class="fv positive unit-money highlight important"' in result
    
    def test_html_renderer_with_custom_attributes(self):
        """Test HTML rendering with custom attributes."""
        renderer = HtmlRenderer()
        amount = money(1234.56)
        
        result = renderer.render(amount, context={
            "attributes": {"data-test": "value", "id": "amount-1"}
        })
        
        assert 'data-test="value"' in result
        assert 'id="amount-1"' in result
    
    def test_html_renderer_with_custom_tag(self):
        """Test HTML rendering with custom tag."""
        renderer = HtmlRenderer()
        amount = money(1234.56)
        
        result = renderer.render(amount, context={"tag": "div"})
        
        assert result.startswith('<div class="fv positive unit-money"')
        assert result.endswith('</div>')
    
    def test_html_renderer_with_currency_data_attribute(self):
        """Test HTML rendering includes currency data attribute."""
        renderer = HtmlRenderer()
        policy = Policy(display=DisplayPolicy(currency="EUR"))
        amount = money(1234.56, policy=policy)
        
        result = renderer.render(amount)
        
        assert 'data-currency="EUR"' in result
        
    def test_html_renderer_with_currency_formatting(self):
        """Test HTML rendering with proper currency formatting."""
        from metricengine.policy import Policy, DisplayPolicy
        
        renderer = HtmlRenderer()
        policy = Policy(display=DisplayPolicy(locale="en_US", currency="USD"))
        amount = money(1234.56, policy=policy)
        
        result = renderer.render(amount)
        
        assert '<span class="fv positive unit-money"' in result
        # With display policy, should show currency symbol
        assert '$' in result or 'USD' in result


class TestMarkdownRenderer:
    """Test the built-in Markdown renderer."""
    
    def test_markdown_renderer_basic(self):
        """Test basic Markdown rendering."""
        renderer = MarkdownRenderer()
        amount = money(1234.56)
        
        result = renderer.render(amount)
        assert result == amount.as_str()
    
    def test_markdown_renderer_negative_bold(self):
        """Test Markdown rendering makes negatives bold by default."""
        renderer = MarkdownRenderer()
        amount = money(-1234.56)
        
        result = renderer.render(amount)
        
        # Should be wrapped in ** for bold
        assert result.startswith("**")
        assert result.endswith("**")
    
    def test_markdown_renderer_negative_no_bold(self):
        """Test Markdown rendering can disable bold for negatives."""
        renderer = MarkdownRenderer()
        amount = money(-1234.56)
        
        result = renderer.render(amount, context={"bold": False})
        
        # Should not be wrapped in **
        assert not result.startswith("**")
        assert not result.endswith("**")
    
    def test_markdown_renderer_percentage_italic(self):
        """Test Markdown rendering can make percentages italic."""
        renderer = MarkdownRenderer()
        rate = percent(15.5, input="percent")
        
        result = renderer.render(rate, context={"italic": True})
        
        # Should be wrapped in * for italic
        assert result.startswith("*")
        assert result.endswith("*")
    
    def test_markdown_renderer_code_blocks(self):
        """Test Markdown rendering with code blocks."""
        renderer = MarkdownRenderer()
        amount = money(1234.56)
        
        result = renderer.render(amount, context={"code": True})
        
        # Should be wrapped in ` for code
        assert result.startswith("`")
        assert result.endswith("`")
    
    def test_markdown_renderer_combined_formatting(self):
        """Test Markdown rendering with multiple formatting options."""
        renderer = MarkdownRenderer()
        rate = percent(-15.5, input="percent")
        
        result = renderer.render(rate, context={
            "bold": True,
            "italic": True,
            "code": True
        })
        
        # Should have all formatting: `**_text_**`
        assert "`" in result
        assert "**" in result
        assert "*" in result


class TestFinancialValueRenderMethod:
    """Test the render method on FinancialValue instances."""
    
    def test_fv_render_text(self):
        """Test FV.render() with text renderer."""
        amount = money(1234.56)
        
        result = amount.render("text")
        assert result == amount.as_str()
    
    def test_fv_render_html(self):
        """Test FV.render() with HTML renderer."""
        amount = money(1234.56)
        
        result = amount.render("html")
        assert '<span class="fv positive unit-money"' in result
        assert '1,234.56</span>' in result
    
    def test_fv_render_markdown(self):
        """Test FV.render() with Markdown renderer."""
        amount = money(-1234.56)
        
        result = amount.render("markdown")
        # Should be bold by default for negatives
        assert result.startswith("**")
        assert result.endswith("**")
    
    def test_fv_render_with_context(self):
        """Test FV.render() passes context to renderer."""
        amount = money(1234.56)
        
        result = amount.render("html", css_classes="highlight")
        assert "highlight" in result
    
    def test_fv_render_default_text(self):
        """Test FV.render() defaults to text renderer."""
        amount = money(1234.56)
        
        result = amount.render()
        assert result == amount.as_str()
    
    def test_fv_render_nonexistent_renderer(self):
        """Test FV.render() with non-existent renderer raises KeyError."""
        amount = money(1234.56)
        
        with pytest.raises(KeyError):
            amount.render("nonexistent")


class TestCustomRenderers:
    """Test custom renderer implementations."""
    
    def test_custom_json_renderer(self):
        """Test a custom JSON-style renderer."""
        import json
        
        class JsonRenderer:
            def render(self, fv, *, context=None):
                # Check if negative by comparing decimal value
                is_negative = False
                if not fv.is_none():
                    decimal_val = fv.as_decimal()
                    is_negative = decimal_val is not None and decimal_val < 0
                
                data = {
                    "value": str(fv.as_decimal()) if not fv.is_none() else None,
                    "formatted": fv.as_str(),
                    "unit": fv.unit.__name__ if fv.unit else None,
                    "is_negative": is_negative,
                    "is_percentage": fv.is_percentage(),
                }
                return json.dumps(data)
        
        register_renderer("json", JsonRenderer())
        
        amount = money(1234.56)
        result = amount.render("json")
        
        data = json.loads(result)
        assert data["value"] == "1234.56"
        assert data["formatted"] == "1,234.56"  # No currency symbol without display policy
        assert data["unit"] == "Money"
        assert data["is_negative"] is False
        assert data["is_percentage"] is False
    
    def test_custom_csv_renderer(self):
        """Test a custom CSV-style renderer."""
        class CsvRenderer:
            def render(self, fv, *, context=None):
                context = context or {}
                separator = context.get("separator", ",")
                
                # Check if negative by comparing decimal value
                is_negative = False
                if not fv.is_none():
                    decimal_val = fv.as_decimal()
                    is_negative = decimal_val is not None and decimal_val < 0
                
                fields = [
                    str(fv.as_decimal()) if not fv.is_none() else "",
                    fv.as_str(),
                    fv.unit.__name__ if fv.unit else "",
                    str(is_negative).lower(),
                    str(fv.is_percentage()).lower(),
                ]
                
                return separator.join(fields)
        
        register_renderer("csv", CsvRenderer())
        
        amount = money(1234.56)
        result = amount.render("csv")
        
        assert result == "1234.56,1,234.56,Money,false,false"  # No currency symbol without display policy
        
        # Test with custom separator
        result_pipe = amount.render("csv", separator="|")
        assert result_pipe == "1234.56|1,234.56|Money|false|false"  # No currency symbol without display policy


class TestRenderingIntegration:
    """Test rendering system integration with different value types."""
    
    def test_money_rendering(self):
        """Test rendering money values."""
        amount = money(1234.56)
        
        text_result = amount.render("text")
        html_result = amount.render("html")
        md_result = amount.render("markdown")
        
        assert "1,234.56" in text_result
        assert "1,234.56" in html_result
        assert "1,234.56" in md_result
    
    def test_percentage_rendering(self):
        """Test rendering percentage values."""
        rate = percent(15.5, input="percent")
        
        text_result = rate.render("text")
        html_result = rate.render("html")
        md_result = rate.render("markdown")
        
        # The percent factory converts input to ratio, so 15.5% becomes ~0.16%
        assert "%" in text_result
        assert "%" in html_result
        assert "%" in md_result
        
        # HTML should have percentage class
        assert "percentage" in html_result
    
    def test_ratio_rendering(self):
        """Test rendering ratio values."""
        growth = ratio(0.15)
        
        text_result = growth.render("text")
        html_result = growth.render("html")
        
        assert "0.15" in text_result
        assert "0.15" in html_result
    
    def test_none_value_rendering(self):
        """Test rendering None values."""
        none_amount = FV.none_with_unit(Money)
        
        text_result = none_amount.render("text")
        html_result = none_amount.render("html")
        
        assert "—" in text_result  # Default none_text
        assert "—" in html_result
        assert "none" in html_result  # CSS class