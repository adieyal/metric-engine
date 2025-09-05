# Formatting Reference

Quick reference for Metric Engine's formatting capabilities.

## Installation

```bash
# Basic installation
pip install metric-engine

# With Babel for internationalization
pip install "metric-engine[babel]"
```

## Quick Start

```python
from metricengine.factories import money, percent
from metricengine.policy import DisplayPolicy

# Create values
amount = money(1234.56)
rate = percent(12.5, input="percent")

# Format with policy
policy = DisplayPolicy(locale="en_US", currency="USD")
print(amount.format(policy))  # $1,234.56
print(rate.format(policy))    # 12.50%
```

## DisplayPolicy Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `locale` | str | "en_US" | Locale code (e.g., "en_US", "de_DE") |
| `currency` | str | "USD" | Currency code (e.g., "USD", "EUR", "JPY") |
| `max_frac` | int | 2 | Maximum decimal places |
| `min_frac` | int | 0 | Minimum decimal places |
| `use_grouping` | bool | True | Use thousands separators |
| `currency_style` | str | "standard" | "standard" or "accounting" |
| `negative_parens` | bool | False | Use parentheses for negatives |
| `percent_scale` | str | "percent" | "percent" or "ratio" |
| `compact` | str | None | "short" or "long" (Babel only) |
| `fallback_locale` | str | "en_US" | Fallback if locale fails |

## Common Locale Examples

```python
# United States
DisplayPolicy(locale="en_US", currency="USD")
# Output: $1,234.56

# Germany
DisplayPolicy(locale="de_DE", currency="EUR")
# Output: 1.234,56 €

# Japan
DisplayPolicy(locale="ja_JP", currency="JPY", max_frac=0)
# Output: ¥1,235

# United Kingdom
DisplayPolicy(locale="en_GB", currency="GBP")
# Output: £1,234.56

# France
DisplayPolicy(locale="fr_FR", currency="EUR")
# Output: 1 234,56 €
```

## Formatter Classes

### get_formatter()

Factory function that returns the best available formatter:

```python
from metricengine.formatters.base import get_formatter

formatter = get_formatter()
# Returns BabelFormatter if Babel is available, else BuiltinFormatter
```

### BabelFormatter

Full-featured formatter with Babel integration:

```python
from metricengine.formatters.babel_adapter import BabelFormatter

try:
    formatter = BabelFormatter()
except BabelUnavailable:
    # Babel not installed
    pass
```

**Methods:**
- `money(amount, unit, display_policy)` - Format currency
- `number(value, display_policy)` - Format plain numbers
- `percent(ratio_or_percent, display_policy)` - Format percentages

### BuiltinFormatter

Fallback formatter without external dependencies:

```python
from metricengine.formatters.base import BuiltinFormatter

formatter = BuiltinFormatter()
# Same interface as BabelFormatter but basic formatting
```

## Value Factory Functions

```python
from metricengine.factories import money, percent, ratio

# Money values
usd_amount = money(1234.56)                    # Defaults to USD
eur_amount = money(1234.56, currency="EUR")    # Specify currency

# Percentages
percent_input = percent(25, input="percent")   # 25%
ratio_input = percent(0.25, input="ratio")    # 25% from 0.25 ratio

# Plain ratios
growth_ratio = ratio(0.15)                     # 0.15 (15% growth)
```

## Formatting Methods

### Direct Formatting

```python
# Using the format() method
amount = money(1234.56)
policy = DisplayPolicy(locale="en_US", currency="USD")
result = amount.format(policy)
```

### Formatter Interface

```python
from metricengine.formatters.base import get_formatter
from decimal import Decimal

formatter = get_formatter()
policy = DisplayPolicy(locale="en_US", currency="USD")

# Format different types
money_result = formatter.money(Decimal("1234.56"), None, policy)
number_result = formatter.number(Decimal("1234.56"), policy)
percent_result = formatter.percent(Decimal("0.1556"), policy)
```

## Accounting Style

For financial reports with parentheses for negatives:

```python
policy = DisplayPolicy(
    locale="en_US",
    currency="USD",
    currency_style="accounting",
    negative_parens=True
)

profit = money(1000)
loss = money(-1000)

print(profit.format(policy))  # $1,000.00
print(loss.format(policy))    # ($1,000.00)
```

## Error Handling

```python
from metricengine.formatters.base import BabelUnavailable

try:
    from metricengine.formatters.babel_adapter import BabelFormatter
    formatter = BabelFormatter()
except BabelUnavailable:
    print("Babel not available, using builtin formatter")
    from metricengine.formatters.base import BuiltinFormatter
    formatter = BuiltinFormatter()
```

## Supported Currencies

Common currency codes (with Babel):

| Code | Currency | Symbol |
|------|----------|--------|
| USD | US Dollar | $ |
| EUR | Euro | € |
| GBP | British Pound | £ |
| JPY | Japanese Yen | ¥ |
| CAD | Canadian Dollar | C$ |
| AUD | Australian Dollar | A$ |
| CHF | Swiss Franc | CHF |
| CNY | Chinese Yuan | ¥ |

## Supported Locales

Common locale codes:

| Code | Language/Region |
|------|----------------|
| en_US | English (United States) |
| en_GB | English (United Kingdom) |
| de_DE | German (Germany) |
| fr_FR | French (France) |
| es_ES | Spanish (Spain) |
| it_IT | Italian (Italy) |
| ja_JP | Japanese (Japan) |
| zh_CN | Chinese (Simplified) |
| pt_BR | Portuguese (Brazil) |
| ru_RU | Russian (Russia) |

## Performance Tips

1. **Cache DisplayPolicy instances:**
   ```python
   # Good
   policy = DisplayPolicy(locale="en_US", currency="USD")
   for amount in amounts:
       result = amount.format(policy)
   ```

2. **Cache formatter instances:**
   ```python
   # Good
   formatter = get_formatter()
   for amount in amounts:
       result = formatter.money(amount, None, policy)
   ```

3. **Reuse policies across similar values:**
   ```python
   # Good
   usd_policy = DisplayPolicy(locale="en_US", currency="USD")
   eur_policy = DisplayPolicy(locale="de_DE", currency="EUR")
   ```

## Common Patterns

### Multi-locale Application

```python
class LocaleFormatter:
    def __init__(self):
        self.policies = {
            'us': DisplayPolicy(locale="en_US", currency="USD"),
            'de': DisplayPolicy(locale="de_DE", currency="EUR"),
            'jp': DisplayPolicy(locale="ja_JP", currency="JPY", max_frac=0),
        }

    def format_for_region(self, amount, region='us'):
        policy = self.policies.get(region, self.policies['us'])
        return amount.format(policy)
```

### Financial Reports

```python
def format_financial_report(data, locale="en_US"):
    policy = DisplayPolicy(
        locale=locale,
        currency="USD",
        currency_style="accounting",
        negative_parens=True,
        max_frac=2
    )

    return {
        'revenue': data['revenue'].format(policy),
        'expenses': data['expenses'].format(policy),
        'profit': (data['revenue'] - data['expenses']).format(policy)
    }
```

### User Preferences

```python
def create_user_policy(user_prefs):
    return DisplayPolicy(
        locale=user_prefs.get('locale', 'en_US'),
        currency=user_prefs.get('currency', 'USD'),
        max_frac=user_prefs.get('decimal_places', 2),
        use_grouping=user_prefs.get('use_grouping', True),
        negative_parens=user_prefs.get('accounting_style', False)
    )
```

## Troubleshooting

**Babel not found:**
```bash
pip install "metric-engine[babel]"
```

**Invalid locale:**
```python
# Use fallback_locale in DisplayPolicy
policy = DisplayPolicy(
    locale="invalid_locale",
    fallback_locale="en_US"
)
```

**Currency not displaying:**
- Check that currency code is valid (ISO 4217)
- Verify locale supports the currency
- Use `currency_style="standard"` for basic symbol display

**Decimal places not working:**
- Set both `max_frac` and `min_frac` for exact control
- Some currencies (like JPY) don't use decimal places

**Grouping not working:**
- Ensure `use_grouping=True` in DisplayPolicy
- Check that locale supports grouping separators
