# Formatting Financial Values

How to format financial values for display and reporting.

## Basic Formatting

```python
from metricengine import Money
from metricengine.formatting import format_currency

amount = Money(1234.56, "USD")
formatted = format_currency(amount)  # "$1,234.56"
```

## Formatting Options

- **Precision**: Decimal places
- **Locale**: Regional formatting
- **Symbols**: Currency symbols
- **Separators**: Thousands separators

## Custom Formatters

```python
from metricengine.formatting import Formatter

formatter = Formatter(
    precision=2,
    locale='en_US',
    show_symbol=True
)

result = formatter.format(amount)
```

## Templates

Use formatting templates for consistent output across applications.
