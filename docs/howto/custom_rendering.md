# How to Create Custom Renderers

This guide shows you how to create and use custom renderers for FinancialValue instances, allowing you to output values in different formats like HTML, Markdown, JSON, or any custom format.

## Quick Start

### Using Built-in Renderers

Metric Engine comes with three built-in renderers:

```python
from metricengine.factories import money

amount = money(1234.56)

# Text rendering (default)
print(amount.render("text"))      # $1,234.56
print(amount.render())            # $1,234.56 (text is default)

# HTML rendering
print(amount.render("html"))      # <span class="fv positive unit-money">$1,234.56</span>

# Markdown rendering
negative_amount = money(-500)
print(negative_amount.render("markdown"))  # **-$500.00** (bold for negatives)
```

## Creating Custom Renderers

### 1. Basic Custom Renderer

Create a class that implements the `Renderer` protocol:

```python
from metricengine.rendering import register_renderer

class CompactRenderer:
    """Renderer that shows values in compact notation (K, M, B)."""
    
    def render(self, fv, *, context=None):
        if fv.is_none():
            return "N/A"
            
        value = fv.as_decimal()
        
        # Determine if this is a money value for currency symbol
        is_money = fv.unit and getattr(fv.unit, '__name__', '') == 'Money'
        currency_symbol = "$" if is_money else ""
        
        if abs(value) >= 1_000_000_000:
            return f"{currency_symbol}{value / 1_000_000_000:.1f}B"
        elif abs(value) >= 1_000_000:
            return f"{currency_symbol}{value / 1_000_000:.1f}M"
        elif abs(value) >= 1_000:
            return f"{currency_symbol}{value / 1_000:.1f}K"
        else:
            return fv.as_str()

# Register the renderer
register_renderer("compact", CompactRenderer())

# Use it
revenue = money(1_234_567)
print(revenue.render("compact"))  # $1.2M

large_amount = money(2_500_000_000)
print(large_amount.render("compact"))  # $2.5B

small_amount = money(500)
print(small_amount.render("compact"))  # 500.00
```

### 2. JSON Renderer

Create a renderer that outputs structured data:

```python
import json
from metricengine.rendering import register_renderer

class JsonRenderer:
    """Renderer that outputs FinancialValue as JSON."""
    
    def render(self, fv, *, context=None):
        data = {
            "value": str(fv.as_decimal()) if not fv.is_none() else None,
            "formatted": fv.as_str(),
            "unit": fv.unit.__name__ if fv.unit else None,
            "is_negative": fv.is_negative(),
            "is_percentage": fv.is_percentage(),
            "is_none": fv.is_none(),
        }
        
        # Add context data if provided
        if context:
            data["context"] = context
            
        return json.dumps(data, indent=2)

register_renderer("json", JsonRenderer())

# Usage
amount = money(1234.56)
print(amount.render("json"))
```

Output:
```json
{
  "value": "1234.56",
  "formatted": "$1,234.56",
  "unit": "Money",
  "is_negative": false,
  "is_percentage": false,
  "is_none": false
}
```

### 3. CSV Renderer

Create a renderer for tabular data:

```python
class CsvRenderer:
    """Renderer that outputs FinancialValue as CSV row."""
    
    def render(self, fv, *, context=None):
        context = context or {}
        separator = context.get("separator", ",")
        include_headers = context.get("include_headers", False)
        
        # Define the fields
        fields = [
            str(fv.as_decimal()) if not fv.is_none() else "",
            fv.as_str(),
            fv.unit.__name__ if fv.unit else "",
            str(fv.is_negative()).lower(),
            str(fv.is_percentage()).lower(),
        ]
        
        result = separator.join(fields)
        
        if include_headers:
            headers = ["raw_value", "formatted", "unit", "is_negative", "is_percentage"]
            header_row = separator.join(headers)
            result = f"{header_row}\n{result}"
            
        return result

register_renderer("csv", CsvRenderer())

# Usage
amounts = [money(1234.56), money(-500), percent(15.5, input="percent")]

# With headers
print(amounts[0].render("csv", include_headers=True))
# raw_value,formatted,unit,is_negative,is_percentage
# 1234.56,$1,234.56,Money,false,false

# Custom separator
for amount in amounts:
    print(amount.render("csv", separator="|"))
```

## Advanced Rendering Techniques

### 1. Context-Aware HTML Renderer

Create a renderer that uses context for advanced styling:

```python
class AdvancedHtmlRenderer:
    """Advanced HTML renderer with context-aware styling."""
    
    def render(self, fv, *, context=None):
        context = context or {}
        
        # Base classes
        classes = ["financial-value"]
        
        # Add state classes
        if fv.is_none():
            classes.append("null-value")
        elif fv.is_negative():
            classes.append("negative")
        else:
            classes.append("positive")
            
        # Add unit classes
        if fv.unit:
            unit_name = fv.unit.__name__.lower()
            classes.append(f"unit-{unit_name}")
            
        # Add threshold-based classes
        threshold = context.get("threshold")
        if threshold and not fv.is_none():
            value = fv.as_decimal()
            if value > threshold:
                classes.append("above-threshold")
            elif value < -threshold:
                classes.append("below-threshold")
                
        # Add custom classes
        custom_classes = context.get("css_classes", [])
        if isinstance(custom_classes, str):
            custom_classes = custom_classes.split()
        classes.extend(custom_classes)
        
        # Build attributes
        attrs = [f'class="{" ".join(classes)}"']
        
        # Add data attributes
        if not fv.is_none():
            attrs.append(f'data-raw-value="{fv.as_decimal()}"')
            
        if fv.unit:
            attrs.append(f'data-unit="{fv.unit.__name__}"')
            
        # Add custom attributes
        custom_attrs = context.get("attributes", {})
        for key, value in custom_attrs.items():
            attrs.append(f'{key}="{value}"')
            
        # Choose tag
        tag = context.get("tag", "span")
        
        # Build final HTML
        attr_string = " ".join(attrs)
        return f'<{tag} {attr_string}>{fv.as_str()}</{tag}>'

register_renderer("advanced_html", AdvancedHtmlRenderer())

# Usage
amount = money(1500)
html = amount.render("advanced_html", 
                    threshold=1000,
                    css_classes="highlight important",
                    attributes={"data-id": "revenue-2024"},
                    tag="div")

print(html)
# <div class="financial-value positive unit-money above-threshold highlight important" 
#      data-raw-value="1500" data-unit="Money" data-id="revenue-2024">$1,500.00</div>
```

### 2. Template-Based Renderer

Create a renderer that uses string templates:

```python
from string import Template

class TemplateRenderer:
    """Renderer that uses string templates for flexible formatting."""
    
    def __init__(self, template_string=None):
        self.default_template = template_string or "${formatted}"
        
    def render(self, fv, *, context=None):
        context = context or {}
        template_string = context.get("template", self.default_template)
        
        template = Template(template_string)
        
        # Prepare template variables
        variables = {
            "formatted": fv.as_str(),
            "raw": str(fv.as_decimal()) if not fv.is_none() else "null",
            "unit": fv.unit.__name__ if fv.unit else "none",
            "sign": "-" if fv.is_negative() else "+",
            "abs_formatted": fv.abs().as_str() if not fv.is_none() else fv.as_str(),
        }
        
        # Add context variables
        variables.update(context.get("variables", {}))
        
        return template.substitute(variables)

# Register with different default templates
register_renderer("template", TemplateRenderer())
register_renderer("accounting", TemplateRenderer("${unit}: ${formatted}"))
register_renderer("debug", TemplateRenderer("${formatted} (raw: ${raw}, unit: ${unit})"))

# Usage
amount = money(1234.56)

# Custom template
result = amount.render("template", 
                      template="Amount: ${formatted} [${unit}]")
print(result)  # Amount: $1,234.56 [Money]

# With variables
result = amount.render("template",
                      template="Q${quarter} Revenue: ${formatted}",
                      variables={"quarter": "4"})
print(result)  # Q4 Revenue: $1,234.56
```

## Built-in Renderer Details

### TextRenderer

The simplest renderer that just calls `as_str()`:

```python
amount = money(1234.56)
print(amount.render("text"))  # $1,234.56
```

### HtmlRenderer

Generates HTML with CSS classes for styling:

```python
amount = money(-1234.56)
html = amount.render("html")
# <span class="fv negative unit-money">-$1,234.56</span>

# With custom options
html = amount.render("html",
                    css_classes="highlight error",
                    attributes={"data-field": "balance"},
                    tag="div")
# <div class="fv negative unit-money highlight error" data-field="balance">-$1,234.56</div>
```

**CSS Classes Added:**
- `fv` - Always present
- `positive` / `negative` / `none` - Based on value state
- `unit-{unitname}` - Based on unit type (e.g., `unit-money`)
- `percentage` - For percentage values

### MarkdownRenderer

Generates Markdown with optional formatting:

```python
negative_amount = money(-500)
percentage = percent(15.5, input="percent")

# Default (bold negatives)
print(negative_amount.render("markdown"))  # **-$500.00**

# Custom formatting
print(percentage.render("markdown", italic=True))  # *15.50%*
print(amount.render("markdown", code=True))        # `$1,234.56`

# Combined formatting
print(negative_amount.render("markdown", bold=True, code=True))  # `**-$500.00**`
```

## Renderer Management

### Listing Available Renderers

```python
from metricengine.rendering import list_renderers

print(list_renderers())  # ['text', 'html', 'markdown', 'custom', ...]
```

### Getting Renderer Instances

```python
from metricengine.rendering import get_renderer

html_renderer = get_renderer("html")
result = html_renderer.render(amount, context={"css_classes": "highlight"})
```

### Error Handling

```python
try:
    result = amount.render("nonexistent")
except KeyError as e:
    print(f"Renderer not found: {e}")
    # Fallback to text
    result = amount.render("text")
```

## Real-World Examples

### 1. Financial Report Generator

```python
class ReportRenderer:
    """Renderer for financial reports."""
    
    def render(self, fv, *, context=None):
        context = context or {}
        report_type = context.get("report_type", "summary")
        
        if report_type == "summary":
            return f"{fv.as_str()}"
        elif report_type == "detailed":
            return f"{fv.as_str()} ({fv.unit.__name__ if fv.unit else 'N/A'})"
        elif report_type == "audit":
            return f"{fv.as_str()} [Raw: {fv.as_decimal()}, Policy: {fv.policy.decimal_places}dp]"
        else:
            return fv.as_str()

register_renderer("report", ReportRenderer())

# Usage in reports
revenue = money(1500000)
expenses = money(1200000)
profit = revenue - expenses

print("Financial Summary:")
print(f"Revenue: {revenue.render('report', report_type='summary')}")
print(f"Expenses: {expenses.render('report', report_type='summary')}")
print(f"Profit: {profit.render('report', report_type='detailed')}")
```

### 2. Web API Serializer

```python
class ApiRenderer:
    """Renderer for web API responses."""
    
    def render(self, fv, *, context=None):
        context = context or {}
        
        data = {
            "value": str(fv.as_decimal()) if not fv.is_none() else None,
            "display": fv.as_str(),
            "currency": None,
            "unit_type": fv.unit.__name__ if fv.unit else None,
        }
        
        # Add currency info for money values
        if fv.unit and fv.unit.__name__ == "Money":
            if fv.policy and fv.policy.display:
                data["currency"] = fv.policy.display.currency
            elif fv.policy and fv.policy.currency_symbol:
                data["currency"] = fv.policy.currency_symbol
                
        # Add API metadata
        if context.get("include_metadata", False):
            data["metadata"] = {
                "is_negative": fv.is_negative(),
                "is_percentage": fv.is_percentage(),
                "decimal_places": fv.policy.decimal_places if fv.policy else None,
            }
            
        return json.dumps(data)

register_renderer("api", ApiRenderer())

# Usage
amount = money(1234.56)
api_response = amount.render("api", include_metadata=True)
print(api_response)
```

## Best Practices

1. **Keep renderers focused**: Each renderer should handle one output format well
2. **Use context effectively**: Allow customization through the context parameter
3. **Handle edge cases**: Always check for None values and missing data
4. **Provide sensible defaults**: Make renderers work without requiring context
5. **Document context options**: Clearly document what context parameters your renderer accepts
6. **Test thoroughly**: Test with different value types, units, and edge cases

## Performance Considerations

- Renderers are called frequently, so keep them lightweight
- Cache expensive operations when possible
- Consider using `__slots__` for renderer classes if creating many instances
- For template-based renderers, compile templates once and reuse them

This rendering system gives you complete control over how financial values are displayed across different contexts and output formats.