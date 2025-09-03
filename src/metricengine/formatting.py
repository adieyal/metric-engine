from typing import Optional


def _import_babel_numbers():
    try:
        from babel import numbers as _numbers  # type: ignore

        return _numbers
    except Exception:
        return None


def format_currency(
    amount: float, currency: str = "USD", *, locale: Optional[str] = None
) -> str:
    """Format currency, using Babel if available and a locale is provided.

    Falls back to a simple "1,234.56 USD" style when Babel or locale is not available.
    """

    numbers = _import_babel_numbers()
    if numbers is not None and locale:
        try:
            return numbers.format_currency(amount, currency, locale=locale)
        except Exception:
            pass

    if currency:
        return f"{amount:,.2f} {currency}"
    return f"{amount:,.2f}"


def format_percent(
    value: float, *, locale: Optional[str] = None, precision: int = 2
) -> str:
    """Format a percentage, using Babel if available and a locale is provided.

    Falls back to a simple "12.34%" style when Babel or locale is not available.
    """

    numbers = _import_babel_numbers()
    if numbers is not None and locale:
        try:
            return numbers.format_percent(value, locale=locale)
        except Exception:
            pass

    return f"{value * 100:.{precision}f}%"
