"""Custom rendering system for FinancialValue instances.

This module provides a pluggable rendering system that allows FinancialValue
instances to be rendered in different formats (HTML, Markdown, plaintext, etc.)
without coupling the core library to any specific renderer.

The rendering system is unit-aware and can include currency symbols, unit codes,
and unit-specific formatting based on the FinancialValue's unit type.

Example:
    >>> from metricengine.factories import money
    >>> from metricengine.rendering import register_renderer
    >>>
    >>> # Register a custom HTML renderer
    >>> class HtmlRenderer:
    ...     def render(self, fv, *, context=None):
    ...         cls = "negative" if fv.is_negative() else "positive"
    ...         return f'<span class="amount {cls}">{fv.as_str()}</span>'
    >>>
    >>> register_renderer("html", HtmlRenderer())
    >>>
    >>> # Use the renderer
    >>> amount = money(1234.56)
    >>> html_output = amount.render("html")
    >>> print(html_output)  # <span class="amount positive">$1,234.56</span>
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    from .value import FinancialValue

__all__ = [
    "Renderer",
    "register_renderer",
    "get_renderer",
    "list_renderers",
    "TextRenderer",
    "HtmlRenderer",
    "MarkdownRenderer",
    "get_currency_symbol",
    "get_unit_display_info",
]


# Currency symbol mapping for Money units
CURRENCY_SYMBOLS = {
    "USD": "$",
    "EUR": "€",
    "GBP": "£",
    "JPY": "¥",
    "CNY": "¥",
    "KRW": "₩",
    "INR": "₹",
    "CAD": "C$",
    "AUD": "A$",
    "CHF": "CHF",
    "SEK": "kr",
    "NOK": "kr",
    "DKK": "kr",
    "PLN": "zł",
    "CZK": "Kč",
    "HUF": "Ft",
    "RUB": "₽",
    "BRL": "R$",
    "MXN": "$",
    "ZAR": "R",
    "SGD": "S$",
    "HKD": "HK$",
    "NZD": "NZ$",
    "THB": "฿",
    "TRY": "₺",
    "ILS": "₪",
    "AED": "د.إ",
    "SAR": "﷼",
}


def get_currency_symbol(currency_code: str) -> str:
    """Get the currency symbol for a given currency code.

    Args:
        currency_code: ISO 4217 currency code (e.g., "USD", "EUR")

    Returns:
        Currency symbol if known, otherwise the currency code itself

    Example:
        >>> get_currency_symbol("USD")
        '$'
        >>> get_currency_symbol("XYZ")  # Unknown currency
        'XYZ'
    """
    return CURRENCY_SYMBOLS.get(currency_code.upper(), currency_code)


def get_unit_display_info(fv: FinancialValue) -> dict[str, Any]:
    """Extract unit display information from a FinancialValue.

    Args:
        fv: FinancialValue instance to extract unit info from

    Returns:
        Dictionary containing unit display information:
        - unit_type: "money", "quantity", "percent", or None
        - unit_code: The unit code (e.g., "USD", "kg", "ratio")
        - unit_category: The unit category (e.g., "Money", "Quantity")
        - symbol: Currency symbol for money units, unit code for others
        - css_class: CSS class name for the unit type

    Example:
        >>> from metricengine.units import MoneyUnit
        >>> fv = FinancialValue(100, unit=MoneyUnit("USD"))
        >>> info = get_unit_display_info(fv)
        >>> info["symbol"]
        '$'
        >>> info["unit_type"]
        'money'
    """
    if not hasattr(fv, "unit") or fv.unit is None:
        return {
            "unit_type": None,
            "unit_code": None,
            "unit_category": None,
            "symbol": None,
            "css_class": None,
        }

    # Handle new Unit system (NewUnit dataclass)
    if hasattr(fv.unit, "category") and hasattr(fv.unit, "code"):
        category = fv.unit.category
        code = fv.unit.code

        if category == "Money":
            return {
                "unit_type": "money",
                "unit_code": code,
                "unit_category": category,
                "symbol": get_currency_symbol(code),
                "css_class": "money",
            }
        elif category == "Quantity":
            return {
                "unit_type": "quantity",
                "unit_code": code,
                "unit_category": category,
                "symbol": code,
                "css_class": "quantity",
            }
        elif category == "Percent":
            return {
                "unit_type": "percent",
                "unit_code": code,
                "unit_category": category,
                "symbol": "%" if code == "ratio" else code,
                "css_class": "percent",
            }
        else:
            return {
                "unit_type": "custom",
                "unit_code": code,
                "unit_category": category,
                "symbol": code,
                "css_class": "custom",
            }

    # Handle legacy unit system (class-based)
    unit_name = getattr(fv.unit, "__name__", str(fv.unit)).lower()

    if "money" in unit_name:
        # Try to get currency code from unit
        currency_code = getattr(fv.unit, "code", "USD")
        return {
            "unit_type": "money",
            "unit_code": currency_code,
            "unit_category": "Money",
            "symbol": get_currency_symbol(currency_code),
            "css_class": "money",
        }
    elif "percent" in unit_name:
        return {
            "unit_type": "percent",
            "unit_code": "percent",
            "unit_category": "Percent",
            "symbol": "%",
            "css_class": "percent",
        }
    elif "ratio" in unit_name:
        return {
            "unit_type": "ratio",
            "unit_code": "ratio",
            "unit_category": "Ratio",
            "symbol": "",
            "css_class": "ratio",
        }
    else:
        return {
            "unit_type": "dimensionless",
            "unit_code": unit_name,
            "unit_category": "Dimensionless",
            "symbol": "",
            "css_class": "dimensionless",
        }


@runtime_checkable
class Renderer(Protocol):
    """Protocol for custom FinancialValue renderers.

    Renderers must implement a render method that takes a FinancialValue
    and optional context, returning a string representation.
    """

    def render(
        self, fv: FinancialValue, *, context: dict[str, Any] | None = None
    ) -> str:
        """Render a FinancialValue to a string.

        Args:
            fv: The FinancialValue to render
            context: Optional context dictionary for rendering customization

        Returns:
            String representation of the FinancialValue
        """
        ...


# Global renderer registry
_renderers: dict[str, Renderer] = {}


def register_renderer(name: str, renderer: Renderer) -> None:
    """Register a renderer with the given name.

    Args:
        name: Unique name for the renderer (e.g., "html", "markdown")
        renderer: Renderer instance implementing the Renderer protocol

    Raises:
        TypeError: If renderer doesn't implement the Renderer protocol

    Example:
        >>> class CustomRenderer:
        ...     def render(self, fv, *, context=None):
        ...         return f"Custom: {fv.as_str()}"
        >>> register_renderer("custom", CustomRenderer())
    """
    if not isinstance(renderer, Renderer):
        raise TypeError(
            f"Renderer must implement the Renderer protocol, got {type(renderer)}"
        )

    _renderers[name] = renderer


def get_renderer(name: str) -> Renderer:
    """Get a registered renderer by name.

    Args:
        name: Name of the renderer to retrieve

    Returns:
        The registered renderer instance

    Raises:
        KeyError: If no renderer is registered with the given name

    Example:
        >>> renderer = get_renderer("html")
        >>> output = renderer.render(my_value)
    """
    if name not in _renderers:
        raise KeyError(
            f"No renderer registered with name '{name}'. Available: {list(_renderers.keys())}"
        )

    return _renderers[name]


def list_renderers() -> list[str]:
    """List all registered renderer names.

    Returns:
        List of registered renderer names

    Example:
        >>> list_renderers()
        ['text', 'html', 'markdown']
    """
    return list(_renderers.keys())


# Built-in renderers


class TextRenderer:
    """Default text renderer that uses the standard as_str() method with optional unit symbols."""

    def render(
        self, fv: FinancialValue, *, context: dict[str, Any] | None = None
    ) -> str:
        """Render as plain text with optional unit symbol inclusion.

        The context can contain:
        - 'include_symbol': Whether to include currency/unit symbols (default: False)
        - 'symbol_position': 'prefix' or 'suffix' for symbol placement (default: 'prefix')
        """
        context = context or {}
        base_text = fv.as_str()

        # Check if we should include unit symbols
        if not context.get("include_symbol", False):
            return base_text

        # Get unit display information
        unit_info = get_unit_display_info(fv)

        if unit_info["symbol"] and unit_info["unit_type"] == "money":
            symbol = unit_info["symbol"]
            position = context.get("symbol_position", "prefix")

            # Don't add symbol if it's already in the formatted text
            if symbol in base_text:
                return base_text

            if position == "prefix":
                return f"{symbol}{base_text}"
            else:
                return f"{base_text} {symbol}"

        return base_text


class HtmlRenderer:
    """HTML renderer that wraps values in styled spans with unit-aware attributes."""

    def render(
        self, fv: FinancialValue, *, context: dict[str, Any] | None = None
    ) -> str:
        """Render as HTML with CSS classes and data attributes for styling.

        The context can contain:
        - 'css_classes': Additional CSS classes to add
        - 'attributes': Additional HTML attributes as a dict
        - 'tag': HTML tag to use (default: 'span')
        - 'include_symbol': Whether to include currency/unit symbols in display (default: False)
        - 'symbol_position': 'prefix' or 'suffix' for symbol placement (default: 'prefix')
        """
        context = context or {}

        # Get unit display information
        unit_info = get_unit_display_info(fv)

        # Determine base CSS classes
        classes = ["fv"]

        if fv.is_none():
            classes.append("none")
        else:
            # Check if negative by comparing decimal value
            decimal_val = fv.as_decimal()
            if decimal_val is not None and decimal_val < 0:
                classes.append("negative")
            else:
                classes.append("positive")

        # Add unit-specific classes
        if unit_info["css_class"]:
            classes.append(f"unit-{unit_info['css_class']}")

        # Add percentage class if applicable
        if fv.is_percentage() or unit_info["unit_type"] == "percent":
            classes.append("percentage")

        # Add custom classes from context
        if "css_classes" in context:
            if isinstance(context["css_classes"], str):
                classes.extend(context["css_classes"].split())
            elif isinstance(context["css_classes"], (list, tuple)):
                classes.extend(context["css_classes"])

        # Build data attributes
        attrs = []

        # Add unit information as data attributes
        if unit_info["unit_type"]:
            attrs.append(f'data-unit-type="{unit_info["unit_type"]}"')

        if unit_info["unit_code"]:
            attrs.append(f'data-unit-code="{unit_info["unit_code"]}"')

        if unit_info["unit_category"]:
            attrs.append(f'data-unit-category="{unit_info["unit_category"]}"')

        # Add currency-specific data attributes for money values
        if unit_info["unit_type"] == "money":
            # Prioritize policy currency over unit currency for legacy compatibility
            currency_code = unit_info["unit_code"]
            currency_symbol = unit_info["symbol"]

            # Check if policy has currency information and override if present
            if fv.unit and hasattr(fv, "policy") and fv.policy:
                if hasattr(fv.policy, "display") and fv.policy.display:
                    currency_code = fv.policy.display.currency
                    currency_symbol = get_currency_symbol(currency_code)
                elif (
                    hasattr(fv.policy, "currency_symbol") and fv.policy.currency_symbol
                ):
                    currency_symbol = fv.policy.currency_symbol

            attrs.append(f'data-currency="{currency_code}"')
            if currency_symbol:
                attrs.append(f'data-currency-symbol="{currency_symbol}"')

            # Also add unit-specific currency info if different from policy
            if unit_info["unit_code"] != currency_code:
                attrs.append(f'data-unit-currency="{unit_info["unit_code"]}"')

        # Legacy support: Add additional policy attributes
        if fv.unit and hasattr(fv, "policy") and fv.policy:
            if hasattr(fv.policy, "display") and fv.policy.display:
                attrs.append(f'data-policy-currency="{fv.policy.display.currency}"')
            elif hasattr(fv.policy, "currency_symbol") and fv.policy.currency_symbol:
                attrs.append(
                    f'data-policy-currency-symbol="{fv.policy.currency_symbol}"'
                )

        # Add custom attributes from context
        if "attributes" in context:
            for key, value in context["attributes"].items():
                attrs.append(f'{key}="{value}"')

        # Determine tag
        tag = context.get("tag", "span")

        # Get display text (potentially with symbol)
        display_text = self._get_display_text(fv, unit_info, context)

        # Build the HTML
        class_attr = f'class="{" ".join(classes)}"'
        all_attrs = " ".join([class_attr] + attrs)

        return f"<{tag} {all_attrs}>{display_text}</{tag}>"

    def _get_display_text(
        self, fv: FinancialValue, unit_info: dict[str, Any], context: dict[str, Any]
    ) -> str:
        """Get the display text for the FinancialValue, optionally including unit symbols."""
        base_text = fv.as_str()

        # Check if we should include unit symbols
        if not context.get("include_symbol", False):
            return base_text

        # Only add symbols for money units to avoid duplication
        if unit_info["unit_type"] == "money" and unit_info["symbol"]:
            symbol = unit_info["symbol"]
            position = context.get("symbol_position", "prefix")

            # Don't add symbol if it's already in the formatted text
            if symbol in base_text:
                return base_text

            if position == "prefix":
                return f"{symbol}{base_text}"
            else:
                return f"{base_text} {symbol}"

        return base_text


class MarkdownRenderer:
    """Markdown renderer for financial values with unit-aware formatting."""

    def render(
        self, fv: FinancialValue, *, context: dict[str, Any] | None = None
    ) -> str:
        """Render as Markdown with optional formatting.

        The context can contain:
        - 'bold': Make negative values bold (default: True)
        - 'italic': Make percentage values italic (default: False)
        - 'code': Wrap in code blocks (default: False)
        - 'include_symbol': Whether to include currency/unit symbols (default: False)
        - 'symbol_position': 'prefix' or 'suffix' for symbol placement (default: 'prefix')
        """
        context = context or {}

        # Get unit display information
        unit_info = get_unit_display_info(fv)

        # Get base text (potentially with symbol)
        text = self._get_display_text(fv, unit_info, context)

        # Apply formatting based on context and value properties
        if context.get("code", False):
            text = f"`{text}`"

        # Make percentages italic if requested
        if context.get("italic", False) and (
            fv.is_percentage() or unit_info["unit_type"] == "percent"
        ):
            text = f"*{text}*"

        # Check if negative by comparing decimal value
        if context.get("bold", True) and not fv.is_none():
            decimal_val = fv.as_decimal()
            if decimal_val is not None and decimal_val < 0:
                text = f"**{text}**"

        return text

    def _get_display_text(
        self, fv: FinancialValue, unit_info: dict[str, Any], context: dict[str, Any]
    ) -> str:
        """Get the display text for the FinancialValue, optionally including unit symbols."""
        base_text = fv.as_str()

        # Check if we should include unit symbols
        if not context.get("include_symbol", False):
            return base_text

        # Only add symbols for money units to avoid duplication
        if unit_info["unit_type"] == "money" and unit_info["symbol"]:
            symbol = unit_info["symbol"]
            position = context.get("symbol_position", "prefix")

            # Don't add symbol if it's already in the formatted text
            if symbol in base_text:
                return base_text

            if position == "prefix":
                return f"{symbol}{base_text}"
            else:
                return f"{base_text} {symbol}"

        return base_text


# Register built-in renderers
register_renderer("text", TextRenderer())
register_renderer("html", HtmlRenderer())
register_renderer("markdown", MarkdownRenderer())
