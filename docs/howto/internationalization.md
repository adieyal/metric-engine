# How to Internationalize Your Application

This guide shows you how to use Metric Engine's Babel integration to create applications that work across different locales and currencies.

## Quick Setup

### 1. Install with Babel Support

```bash
pip install "metric-engine[babel]"
```

### 2. Basic Multi-Locale Example

```python
from metricengine.factories import money, percent
from metricengine.policy import DisplayPolicy

# Your business data
revenue = money(1234567.89)
growth_rate = percent(12.5, input="percent")
profit_margin = percent(0.185, input="ratio")  # 18.5%

# Define locale-specific policies
locales = {
    "us": DisplayPolicy(locale="en_US", currency="USD"),
    "uk": DisplayPolicy(locale="en_GB", currency="GBP"),
    "germany": DisplayPolicy(locale="de_DE", currency="EUR"),
    "japan": DisplayPolicy(locale="ja_JP", currency="JPY", max_frac=0),
}

# Format for each locale
for region, policy in locales.items():
    print(f"\n{region.upper()} Formatting:")
    print(f"  Revenue: {revenue.format(policy)}")
    print(f"  Growth: {growth_rate.format(policy)}")
    print(f"  Margin: {profit_margin.format(policy)}")
```

Output:
```
US Formatting:
  Revenue: $1,234,567.89
  Growth: 12.50%
  Margin: 18.50%

UK Formatting:
  Revenue: £1,234,567.89
  Growth: 12.50%
  Margin: 18.50%

GERMANY Formatting:
  Revenue: 1.234.567,89 €
  Growth: 12,50 %
  Margin: 18,50 %

JAPAN Formatting:
  Revenue: ¥1,234,568
  Growth: 13%
  Margin: 19%
```

## Building a Multi-Currency Dashboard

### 1. Create a Formatter Service

```python
from typing import Dict
from metricengine.formatters.base import get_formatter
from metricengine.policy import DisplayPolicy

class LocalizationService:
    """Service for handling multi-locale formatting."""

    def __init__(self):
        self.formatter = get_formatter()
        self.policies = self._create_policies()

    def _create_policies(self) -> Dict[str, DisplayPolicy]:
        """Create standard policies for supported locales."""
        return {
            "en_US": DisplayPolicy(
                locale="en_US",
                currency="USD",
                max_frac=2,
                use_grouping=True
            ),
            "en_GB": DisplayPolicy(
                locale="en_GB",
                currency="GBP",
                max_frac=2,
                use_grouping=True
            ),
            "de_DE": DisplayPolicy(
                locale="de_DE",
                currency="EUR",
                max_frac=2,
                use_grouping=True
            ),
            "fr_FR": DisplayPolicy(
                locale="fr_FR",
                currency="EUR",
                max_frac=2,
                use_grouping=True
            ),
            "ja_JP": DisplayPolicy(
                locale="ja_JP",
                currency="JPY",
                max_frac=0,  # Yen doesn't use decimal places
                use_grouping=True
            ),
        }

    def format_for_locale(self, value, locale: str):
        """Format a value for a specific locale."""
        policy = self.policies.get(locale, self.policies["en_US"])
        return value.format(policy)

    def get_accounting_policy(self, locale: str) -> DisplayPolicy:
        """Get accounting-style policy for financial reports."""
        base_policy = self.policies.get(locale, self.policies["en_US"])
        return DisplayPolicy(
            locale=base_policy.locale,
            currency=base_policy.currency,
            max_frac=base_policy.max_frac,
            use_grouping=base_policy.use_grouping,
            currency_style="accounting",
            negative_parens=True
        )

# Usage
localization = LocalizationService()
```

### 2. Create Financial Reports

```python
from metricengine.factories import money

def generate_financial_report(data: dict, locale: str = "en_US"):
    """Generate a localized financial report."""

    localization = LocalizationService()
    accounting_policy = localization.get_accounting_policy(locale)

    # Calculate key metrics
    revenue = data["revenue"]
    expenses = data["expenses"]
    net_income = revenue - expenses

    # Format with accounting style
    report = f"""
Financial Report ({locale})
{'=' * 30}
Revenue:     {revenue.format(accounting_policy)}
Expenses:    {expenses.format(accounting_policy)}
Net Income:  {net_income.format(accounting_policy)}
"""

    return report

# Example usage
financial_data = {
    "revenue": money(500000),
    "expenses": money(350000)
}

# Generate reports for different locales
for locale in ["en_US", "de_DE", "ja_JP"]:
    print(generate_financial_report(financial_data, locale))
```

## Handling User Preferences

### 1. User Preference System

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class UserPreferences:
    """User's localization preferences."""
    locale: str = "en_US"
    currency: str = "USD"
    decimal_places: int = 2
    use_accounting_style: bool = False
    show_currency_symbol: bool = True

class UserLocalizer:
    """Handles user-specific formatting preferences."""

    def __init__(self, preferences: UserPreferences):
        self.preferences = preferences
        self.formatter = get_formatter()

    def create_policy(self) -> DisplayPolicy:
        """Create a display policy from user preferences."""
        return DisplayPolicy(
            locale=self.preferences.locale,
            currency=self.preferences.currency,
            max_frac=self.preferences.decimal_places,
            min_frac=self.preferences.decimal_places,
            use_grouping=True,
            currency_style="accounting" if self.preferences.use_accounting_style else "standard",
            negative_parens=self.preferences.use_accounting_style
        )

    def format_money(self, amount):
        """Format money according to user preferences."""
        policy = self.create_policy()
        return amount.format(policy)

    def format_percentage(self, percentage):
        """Format percentage according to user preferences."""
        policy = self.create_policy()
        return percentage.format(policy)

# Example usage
user_prefs = UserPreferences(
    locale="de_DE",
    currency="EUR",
    decimal_places=2,
    use_accounting_style=True
)

localizer = UserLocalizer(user_prefs)
amount = money(1234.56)
print(localizer.format_money(amount))  # 1.234,56 €
```

### 2. Dynamic Locale Switching

```python
class DynamicFormatter:
    """Formatter that can switch locales dynamically."""

    def __init__(self):
        self.formatter = get_formatter()
        self.current_locale = "en_US"
        self.policies_cache = {}

    def set_locale(self, locale: str, currency: str = None):
        """Switch to a different locale."""
        self.current_locale = locale
        if currency:
            # Update cached policy for this locale
            self.policies_cache[locale] = DisplayPolicy(
                locale=locale,
                currency=currency,
                max_frac=2,
                use_grouping=True
            )

    def get_policy(self) -> DisplayPolicy:
        """Get policy for current locale."""
        if self.current_locale not in self.policies_cache:
            # Create default policy for locale
            currency_map = {
                "en_US": "USD", "en_GB": "GBP", "de_DE": "EUR",
                "fr_FR": "EUR", "ja_JP": "JPY", "zh_CN": "CNY"
            }
            currency = currency_map.get(self.current_locale, "USD")

            self.policies_cache[self.current_locale] = DisplayPolicy(
                locale=self.current_locale,
                currency=currency,
                max_frac=2 if currency != "JPY" else 0,
                use_grouping=True
            )

        return self.policies_cache[self.current_locale]

    def format_value(self, value):
        """Format value with current locale."""
        policy = self.get_policy()
        return value.format(policy)

# Usage example
formatter = DynamicFormatter()
amount = money(1234.56)

# Switch between locales
locales = ["en_US", "de_DE", "ja_JP", "fr_FR"]
for locale in locales:
    formatter.set_locale(locale)
    print(f"{locale}: {formatter.format_value(amount)}")
```

## Web Application Integration

### 1. Flask Example

```python
from flask import Flask, request, session
from metricengine.factories import money, percent
from metricengine.policy import DisplayPolicy

app = Flask(__name__)
app.secret_key = 'your-secret-key'

def get_user_locale():
    """Get user's preferred locale from session or browser."""
    return session.get('locale', request.accept_languages.best_match(['en_US', 'de_DE', 'fr_FR', 'ja_JP']))

def create_display_policy(locale: str) -> DisplayPolicy:
    """Create display policy for locale."""
    currency_map = {
        'en_US': 'USD', 'de_DE': 'EUR',
        'fr_FR': 'EUR', 'ja_JP': 'JPY'
    }

    return DisplayPolicy(
        locale=locale,
        currency=currency_map.get(locale, 'USD'),
        max_frac=2 if locale != 'ja_JP' else 0,
        use_grouping=True
    )

@app.route('/dashboard')
def dashboard():
    """Display localized financial dashboard."""
    locale = get_user_locale()
    policy = create_display_policy(locale)

    # Sample financial data
    revenue = money(1500000)
    expenses = money(1200000)
    profit = revenue - expenses
    margin = percent(0.20, input="ratio")

    return f"""
    <h1>Financial Dashboard</h1>
    <p>Locale: {locale}</p>
    <ul>
        <li>Revenue: {revenue.format(policy)}</li>
        <li>Expenses: {expenses.format(policy)}</li>
        <li>Profit: {profit.format(policy)}</li>
        <li>Margin: {margin.format(policy)}</li>
    </ul>
    """

@app.route('/set_locale/<locale>')
def set_locale(locale):
    """Allow users to change their locale preference."""
    session['locale'] = locale
    return f"Locale set to {locale}"
```

### 2. Django Integration

```python
# views.py
from django.shortcuts import render
from django.utils import translation
from metricengine.factories import money, percent
from metricengine.policy import DisplayPolicy

def get_display_policy(request):
    """Create display policy from Django's locale system."""
    locale = translation.get_language()

    # Map Django locale codes to display policies
    locale_map = {
        'en': DisplayPolicy(locale='en_US', currency='USD'),
        'de': DisplayPolicy(locale='de_DE', currency='EUR'),
        'fr': DisplayPolicy(locale='fr_FR', currency='EUR'),
        'ja': DisplayPolicy(locale='ja_JP', currency='JPY', max_frac=0),
    }

    lang_code = locale.split('-')[0]  # 'en-us' -> 'en'
    return locale_map.get(lang_code, locale_map['en'])

def financial_report(request):
    """Generate localized financial report."""
    policy = get_display_policy(request)

    # Your business logic here
    data = {
        'revenue': money(2000000).format(policy),
        'profit': money(400000).format(policy),
        'margin': percent(0.20, input="ratio").format(policy),
    }

    return render(request, 'financial_report.html', data)
```

## Testing Internationalization

### 1. Test Multiple Locales

```python
import pytest
from metricengine.factories import money, percent
from metricengine.policy import DisplayPolicy

class TestInternationalization:
    """Test formatting across different locales."""

    @pytest.mark.parametrize("locale,currency,expected_symbol", [
        ("en_US", "USD", "$"),
        ("de_DE", "EUR", "€"),
        ("ja_JP", "JPY", "¥"),
        ("en_GB", "GBP", "£"),
    ])
    def test_currency_symbols(self, locale, currency, expected_symbol):
        """Test that currency symbols appear correctly."""
        amount = money(100)
        policy = DisplayPolicy(locale=locale, currency=currency)
        result = amount.format(policy)
        assert expected_symbol in result

    def test_decimal_separators(self):
        """Test locale-specific decimal separators."""
        amount = money(1234.56)

        # US uses period
        us_policy = DisplayPolicy(locale="en_US", currency="USD")
        us_result = amount.format(us_policy)
        assert "1,234.56" in us_result

        # Germany uses comma
        de_policy = DisplayPolicy(locale="de_DE", currency="EUR")
        de_result = amount.format(de_policy)
        assert "1.234,56" in de_result

    def test_percentage_formatting(self):
        """Test percentage formatting across locales."""
        rate = percent(15.5, input="percent")

        locales = ["en_US", "de_DE", "fr_FR"]
        for locale in locales:
            policy = DisplayPolicy(locale=locale)
            result = rate.format(policy)
            assert "15" in result
            assert "%" in result
```

### 2. Fallback Testing

```python
def test_babel_fallback():
    """Test that formatting works without Babel."""
    # Mock Babel as unavailable
    import sys
    babel_modules = [mod for mod in sys.modules if mod.startswith('babel')]
    for mod in babel_modules:
        del sys.modules[mod]

    # Should still work with builtin formatter
    from metricengine.factories import money
    from metricengine.policy import DisplayPolicy

    amount = money(1234.56)
    policy = DisplayPolicy(currency="USD")
    result = amount.format(policy)

    # Should contain currency and amount
    assert "USD" in result
    assert "1234.56" in result or "1,234.56" in result
```

## Performance Tips

1. **Cache Display Policies**: Create policies once and reuse them
2. **Cache Formatter Instances**: The formatter can be reused across requests
3. **Batch Formatting**: Format multiple values with the same policy together
4. **Lazy Loading**: Only import Babel when actually needed

```python
# Good: Cache policies
class CachedLocalizer:
    def __init__(self):
        self._policies = {}
        self._formatter = None

    @property
    def formatter(self):
        if self._formatter is None:
            self._formatter = get_formatter()
        return self._formatter

    def get_policy(self, locale: str) -> DisplayPolicy:
        if locale not in self._policies:
            self._policies[locale] = DisplayPolicy(locale=locale)
        return self._policies[locale]
```

## Common Pitfalls

1. **Don't assume Babel is available** - Always handle the fallback case
2. **Test with real locale data** - Some locales have surprising formatting rules
3. **Handle currency edge cases** - Not all currencies use 2 decimal places
4. **Consider RTL languages** - Some locales read right-to-left
5. **Validate locale codes** - Invalid locales should fall back gracefully

This guide should get you started with internationalizing your Metric Engine application. The key is to use display policies consistently and test across your target locales.
