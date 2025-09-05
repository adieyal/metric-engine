"""Custom rendering system for FinancialValue instances.

This module provides a pluggable rendering system that allows FinancialValue
instances to be rendered in different formats (HTML, Markdown, plaintext, etc.)
without coupling the core library to any specific renderer.

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

from typing import TYPE_CHECKING, Any, Dict, Protocol, runtime_checkable

if TYPE_CHECKING:
    from .value import FinancialValue

__all__ = [
    "Renderer",
    "register_renderer", 
    "get_renderer",
    "list_renderers",
    "TextRenderer",
    "HtmlRenderer",
    "MarkdownRenderer"
]


@runtime_checkable
class Renderer(Protocol):
    """Protocol for custom FinancialValue renderers.
    
    Renderers must implement a render method that takes a FinancialValue
    and optional context, returning a string representation.
    """
    
    def render(self, fv: "FinancialValue", *, context: Dict[str, Any] | None = None) -> str:
        """Render a FinancialValue to a string.
        
        Args:
            fv: The FinancialValue to render
            context: Optional context dictionary for rendering customization
            
        Returns:
            String representation of the FinancialValue
        """
        ...


# Global renderer registry
_renderers: Dict[str, Renderer] = {}


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
        raise TypeError(f"Renderer must implement the Renderer protocol, got {type(renderer)}")
    
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
        raise KeyError(f"No renderer registered with name '{name}'. Available: {list(_renderers.keys())}")
    
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
    """Default text renderer that uses the standard as_str() method."""
    
    def render(self, fv: "FinancialValue", *, context: Dict[str, Any] | None = None) -> str:
        """Render as plain text using the value's as_str() method."""
        return fv.as_str()


class HtmlRenderer:
    """HTML renderer that wraps values in styled spans."""
    
    def render(self, fv: "FinancialValue", *, context: Dict[str, Any] | None = None) -> str:
        """Render as HTML with CSS classes for styling.
        
        The context can contain:
        - 'css_classes': Additional CSS classes to add
        - 'attributes': Additional HTML attributes as a dict
        - 'tag': HTML tag to use (default: 'span')
        """
        context = context or {}
        
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
        if fv.unit:
            unit_name = getattr(fv.unit, '__name__', str(fv.unit)).lower()
            classes.append(f"unit-{unit_name}")
            
        # Add percentage class if applicable
        if fv.is_percentage() or (fv.unit and getattr(fv.unit, '__name__', '') == 'Percent'):
            classes.append("percentage")
            
        # Add custom classes from context
        if 'css_classes' in context:
            if isinstance(context['css_classes'], str):
                classes.extend(context['css_classes'].split())
            elif isinstance(context['css_classes'], (list, tuple)):
                classes.extend(context['css_classes'])
        
        # Build attributes
        attrs = []
        
        # Add currency data attribute for money values
        if fv.unit and getattr(fv.unit, '__name__', '').startswith('Money'):
            if fv.policy and fv.policy.display:
                attrs.append(f'data-currency="{fv.policy.display.currency}"')
            elif fv.policy and fv.policy.currency_symbol:
                attrs.append(f'data-currency-symbol="{fv.policy.currency_symbol}"')
        
        # Add custom attributes from context
        if 'attributes' in context:
            for key, value in context['attributes'].items():
                attrs.append(f'{key}="{value}"')
        
        # Determine tag
        tag = context.get('tag', 'span')
        
        # Build the HTML
        class_attr = f'class="{" ".join(classes)}"'
        all_attrs = " ".join([class_attr] + attrs)
        
        return f'<{tag} {all_attrs}>{fv.as_str()}</{tag}>'


class MarkdownRenderer:
    """Markdown renderer for financial values."""
    
    def render(self, fv: "FinancialValue", *, context: Dict[str, Any] | None = None) -> str:
        """Render as Markdown with optional formatting.
        
        The context can contain:
        - 'bold': Make negative values bold (default: True)
        - 'italic': Make percentage values italic (default: False)
        - 'code': Wrap in code blocks (default: False)
        """
        context = context or {}
        
        text = fv.as_str()
        
        # Apply formatting based on context and value properties
        if context.get('code', False):
            text = f"`{text}`"
            
        if context.get('italic', False) and (fv.is_percentage() or (fv.unit and getattr(fv.unit, '__name__', '') == 'Percent')):
            text = f"*{text}*"
            
        # Check if negative by comparing decimal value
        if context.get('bold', True) and not fv.is_none():
            decimal_val = fv.as_decimal()
            if decimal_val is not None and decimal_val < 0:
                text = f"**{text}**"
            
        return text


# Register built-in renderers
register_renderer("text", TextRenderer())
register_renderer("html", HtmlRenderer())
register_renderer("markdown", MarkdownRenderer())