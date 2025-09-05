# Formatting and Internationalization

Metric Engine provides flexible formatting capabilities for displaying financial values, numbers, and percentages with proper locale support through optional Babel integration.

## Overview

The formatting system is built around two key components:

1. **Display Policies** - Control how values should be formatted (decimal places, grouping, currency symbols, etc.)
2. **Formatters** - Handle the actual formatting logic with locale awareness

## Formatter Architecture

Metric Engine uses a plugin-based formatter system:

```python
from metricengine.formatters.base import get_formatter

# Automatically selects the best available formatter
formatter = get_formatter()
```

### Available Formatters

**BabelFormatter** (when Babel is installed)
- Full internationalization support
- Locale-aware currency, number, and percentage formatting
- CLDR-compliant formatting patterns
- Support for multiple currencies and locales

**BuiltinFormatter** (fallback)
- Basic formatting without external dependencies
- Simple currency symbols and decimal formatting
- Used when Babel is not available

## Display Policies

Display policies control formatting behavior:

```python
from metricengine.policy import DisplayPolicy

# Basic policy
policy = DisplayPolicy(
    locale="en_US",
    currency="USD",
    max_frac=2,
    use_grouping=True
)

# Advanced policy with accounting style
accounting_policy = DisplayPolicy(
    locale="en_US",
    currency="USD",
    max_frac=2,
    currency_style="accounting",
    negative_parens=True,
    use_grouping=True
)
```

### Key Policy Options

- `locale`: Target locale (e.g., "en_US", "de_DE", "ja_JP")
- `currency`: Currency code (e.g., "USD", "EUR", "JPY")
- `max_frac`/`min_frac`: Control decimal places
- `use_grouping`: Enable/disable thousands separators
- `currency_style`: "standard" or "accounting"
- `negative_parens`: Use parentheses for negative values
- `percent_scale`: "ratio" (0.15) or "percent" (15) input interpretation

## Babel Integration

### Installation

Install Metric Engine with Babel support:

```bash
pip install "metric-engine[babel]"
```

### Locale-Aware Formatting

With Babel installed, you get full internationalization support:

```python
from metricengine.factories import money, percent
from metricengine.policy import DisplayPolicy

# Create values
revenue = money(1234567.89)
growth = percent(15.5, input="percent")

# US English formatting
us_policy = DisplayPolicy(locale="en_US", currency="USD")
print(revenue.format(us_policy))  # $1,234,567.89
print(growth.format(us_policy))   # 15.50%

# German formatting
de_policy = DisplayPolicy(locale="de_DE", currency="EUR")
print(revenue.format(de_policy))  # 1.234.567,89 €
print(growth.format(de_policy))   # 15,50 %

# Japanese formatting
jp_policy = DisplayPolicy(locale="ja_JP", currency="JPY", max_frac=0)
print(revenue.format(jp_policy))  # ¥1,234,568
```

### Currency Formatting

Babel provides sophisticated currency formatting:

```python
from metricengine.factories import money
from metricengine.policy import DisplayPolicy

amount = money(1234.56)

# Different locales, same currency
policies = [
    DisplayPolicy(locale="en_US", currency="USD"),  # $1,234.56
    DisplayPolicy(locale="en_GB", currency="USD"),  # US$1,234.56
    DisplayPolicy(locale="fr_FR", currency="USD"),  # 1 234,56 $US
]

for policy in policies:
    print(f"{policy.locale}: {amount.format(policy)}")
```

### Accounting Style

For financial applications, use accounting style formatting:

```python
from metricengine.factories import money
from metricengine.policy import DisplayPolicy

profit = money(1000)
loss = money(-1000)

accounting_policy = DisplayPolicy(
    locale="en_US",
    currency="USD",
    currency_style="accounting",
    negative_parens=True
)

print(profit.format(accounting_policy))  # $1,000.00
print(loss.format(accounting_policy))    # ($1,000.00)
```

## Percentage Formatting

Handle both ratio and percentage inputs correctly:

```python
from metricengine.factories import percent
from metricengine.policy import DisplayPolicy

# Ratio input (0.15 = 15%)
ratio_value = percent(0.15, input="ratio")

# Percentage input (15 = 15%)
percent_value = percent(15, input="percent")

policy = DisplayPolicy(
    locale="en_US",
    max_frac=2,
    percent_scale="ratio"  # How to interpret the stored value
)

print(ratio_value.format(policy))   # 15.00%
print(percent_value.format(policy)) # 15.00%
```

## Number Formatting

Format plain numbers with locale-specific conventions:

```python
from metricengine.factories import ratio
from metricengine.policy import DisplayPolicy

large_number = ratio(1234567.89)

# US formatting
us_policy = DisplayPolicy(locale="en_US", max_frac=2)
print(large_number.format(us_policy))  # 1,234,567.89

# European formatting
eu_policy = DisplayPolicy(locale="de_DE", max_frac=2)
print(large_number.format(eu_policy))  # 1.234.567,89

# No grouping
no_group_policy = DisplayPolicy(locale="en_US", max_frac=2, use_grouping=False)
print(large_number.format(no_group_policy))  # 1234567.89
```

## Fallback Behavior

When Babel is not available, Metric Engine gracefully falls back to basic formatting:

```python
# This works whether Babel is installed or not
from metricengine.factories import money
from metricengine.policy import DisplayPolicy

amount = money(1234.56)
policy = DisplayPolicy(currency="USD", max_frac=2)

# With Babel: $1,234.56
# Without Babel: USD 1,234.56
print(amount.format(policy))
```

## Custom Formatting

For advanced use cases, you can work directly with formatters:

```python
from metricengine.formatters.base import get_formatter
from metricengine.policy import DisplayPolicy
from decimal import Decimal

formatter = get_formatter()
policy = DisplayPolicy(locale="en_US", currency="USD", max_frac=2)

# Format different value types
money_result = formatter.money(Decimal("1234.56"), None, policy)
number_result = formatter.number(Decimal("1234.56"), policy)
percent_result = formatter.percent(Decimal("0.1556"), policy)

print(f"Money: {money_result}")    # Money: $1,234.56
print(f"Number: {number_result}")  # Number: 1,234.56
print(f"Percent: {percent_result}") # Percent: 15.56%
```

## Error Handling

The formatting system handles errors gracefully:

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

## Best Practices

1. **Use Display Policies**: Always format through display policies rather than direct formatter calls
2. **Install Babel for Production**: Use `pip install "metric-engine[babel]"` for full internationalization
3. **Test Multiple Locales**: Verify your formatting works across target locales
4. **Handle Fallbacks**: Design your application to work with or without Babel
5. **Cache Policies**: Reuse display policy instances for better performance

## Supported Locales

With Babel, Metric Engine supports all CLDR locales. Common examples:

- `en_US` - US English
- `en_GB` - British English
- `de_DE` - German (Germany)
- `fr_FR` - French (France)
- `ja_JP` - Japanese
- `zh_CN` - Chinese (Simplified)
- `es_ES` - Spanish (Spain)
- `pt_BR` - Portuguese (Brazil)

## Performance Considerations

- Formatter instances are lightweight and can be cached
- Display policies are immutable and safe to reuse
- Babel formatting is slightly slower than builtin but provides much better locale support
- Consider using the factory function `get_formatter()` to automatically select the best available formatter
