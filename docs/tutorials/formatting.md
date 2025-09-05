# Formatting Financial Values Tutorial

Learn how to format financial values for display, reporting, and internationalization using Metric Engine's powerful formatting system.

## Prerequisites

This tutorial assumes you have Metric Engine installed. For full internationalization features, install with Babel support:

```bash
pip install "metric-engine[babel]"
```

## Basic Formatting

Let's start with simple value formatting:

```python
from metricengine.factories import money, percent, ratio
from metricengine.policy import DisplayPolicy

# Create some financial values
revenue = money(1234567.89)
growth_rate = percent(12.5, input="percent")
profit_margin = ratio(0.185)  # 18.5% as a ratio

# Basic formatting with default policy
print(revenue)        # $1,234,567.89
print(growth_rate)    # 12.50%
print(profit_margin)  # 0.185
```

## Using Display Policies

Display policies give you fine control over formatting:

```python
from metricengine.policy import DisplayPolicy

# Create a custom display policy
policy = DisplayPolicy(
    locale="en_US",
    currency="USD",
    max_frac=2,           # Maximum 2 decimal places
    min_frac=2,           # Minimum 2 decimal places
    use_grouping=True,    # Use thousands separators
    negative_parens=False # Use minus sign for negatives
)

# Apply the policy
amount = money(1234.56)
formatted = amount.format(policy)
print(formatted)  # $1,234.56
```

## International Formatting

With Babel installed, you get full locale support:

```python
# Different locales for the same amount
amount = money(1234567.89)

locales = [
    ("en_US", "USD"),  # United States
    ("de_DE", "EUR"),  # Germany
    ("ja_JP", "JPY"),  # Japan
    ("en_GB", "GBP"),  # United Kingdom
]

for locale, currency in locales:
    policy = DisplayPolicy(locale=locale, currency=currency)
    if currency == "JPY":
        policy = DisplayPolicy(locale=locale, currency=currency, max_frac=0)

    formatted = amount.format(policy)
    print(f"{locale}: {formatted}")
```

Output:
```
en_US: $1,234,567.89
de_DE: 1.234.567,89 €
ja_JP: ¥1,234,568
en_GB: £1,234,567.89
```

## Percentage Formatting

Handle percentages with different input formats:

```python
# Different ways to create percentages
percent_input = percent(25, input="percent")      # 25%
ratio_input = percent(0.25, input="ratio")        # 25% from 0.25

# Format with different policies
us_policy = DisplayPolicy(locale="en_US", max_frac=1)
de_policy = DisplayPolicy(locale="de_DE", max_frac=1)

print("US format:")
print(f"  Percent input: {percent_input.format(us_policy)}")
print(f"  Ratio input: {ratio_input.format(us_policy)}")

print("German format:")
print(f"  Percent input: {percent_input.format(de_policy)}")
print(f"  Ratio input: {ratio_input.format(de_policy)}")
```

## Accounting Style Formatting

For financial reports, use accounting style with parentheses for negatives:

```python
# Create positive and negative amounts
profit = money(50000)
loss = money(-25000)

# Accounting style policy
accounting_policy = DisplayPolicy(
    locale="en_US",
    currency="USD",
    currency_style="accounting",
    negative_parens=True,
    max_frac=2
)

print("Accounting Style:")
print(f"Profit: {profit.format(accounting_policy)}")   # $50,000.00
print(f"Loss: {loss.format(accounting_policy)}")       # ($25,000.00)
```

## Building a Financial Report

Let's create a complete financial report with proper formatting:

```python
from metricengine.factories import money, percent

def create_financial_report(locale="en_US", currency="USD"):
    """Create a formatted financial report."""

    # Sample financial data
    data = {
        "revenue": money(2500000),
        "cost_of_goods": money(1500000),
        "operating_expenses": money(600000),
        "tax_rate": percent(21, input="percent")
    }

    # Calculate derived metrics
    gross_profit = data["revenue"] - data["cost_of_goods"]
    operating_profit = gross_profit - data["operating_expenses"]
    taxes = operating_profit * data["tax_rate"]
    net_profit = operating_profit - taxes

    # Create formatting policy
    policy = DisplayPolicy(
        locale=locale,
        currency=currency,
        max_frac=0,  # No decimals for this report
        use_grouping=True,
        currency_style="accounting",
        negative_parens=True
    )

    # Format the report
    report = f"""
Financial Report ({locale})
{'=' * 40}
Revenue:              {data['revenue'].format(policy)}
Cost of Goods Sold:   {data['cost_of_goods'].format(policy)}
Gross Profit:         {gross_profit.format(policy)}

Operating Expenses:   {data['operating_expenses'].format(policy)}
Operating Profit:     {operating_profit.format(policy)}

Tax Rate:             {data['tax_rate'].format(policy)}
Taxes:                {taxes.format(policy)}
Net Profit:           {net_profit.format(policy)}
"""

    return report

# Generate reports for different locales
print(create_financial_report("en_US", "USD"))
print(create_financial_report("de_DE", "EUR"))
print(create_financial_report("ja_JP", "JPY"))
```

## Custom Formatting Functions

Create reusable formatting functions for your application:

```python
def format_currency_compact(amount, locale="en_US"):
    """Format currency in compact style (e.g., $1.2M)."""
    policy = DisplayPolicy(
        locale=locale,
        currency="USD" if locale.startswith("en") else "EUR",
        max_frac=1,
        compact="short"  # This may not be supported in all Babel versions
    )
    return amount.format(policy)

def format_percentage_precise(percentage, locale="en_US"):
    """Format percentage with high precision."""
    policy = DisplayPolicy(
        locale=locale,
        max_frac=4,
        min_frac=2
    )
    return percentage.format(policy)

# Usage
large_amount = money(1234567)
precise_rate = percent(0.12345, input="ratio")

print(format_currency_compact(large_amount))
print(format_percentage_precise(precise_rate))
```

## Handling Edge Cases

Deal with common formatting challenges:

```python
# Very small amounts
tiny_amount = money(0.001)
policy = DisplayPolicy(locale="en_US", currency="USD", max_frac=3)
print(f"Tiny amount: {tiny_amount.format(policy)}")  # $0.001

# Very large amounts
huge_amount = money(999999999999.99)
policy = DisplayPolicy(locale="en_US", currency="USD", max_frac=2)
print(f"Huge amount: {huge_amount.format(policy)}")

# Zero values
zero_amount = money(0)
policy = DisplayPolicy(locale="en_US", currency="USD", max_frac=2)
print(f"Zero: {zero_amount.format(policy)}")  # $0.00

# None values (missing data)
from metricengine import FV
from metricengine.units import Money

none_amount = FV.none(Money)
print(f"Missing: {none_amount}")  # None
```

## Performance Tips

For applications that format many values:

```python
# Cache display policies
class FormattingService:
    def __init__(self):
        self.policies = {
            "usd": DisplayPolicy(locale="en_US", currency="USD"),
            "eur": DisplayPolicy(locale="de_DE", currency="EUR"),
            "jpy": DisplayPolicy(locale="ja_JP", currency="JPY", max_frac=0),
        }

    def format_money(self, amount, currency_code="usd"):
        policy = self.policies.get(currency_code, self.policies["usd"])
        return amount.format(policy)

# Use the service
formatter = FormattingService()
amounts = [money(100), money(200), money(300)]

for amount in amounts:
    print(formatter.format_money(amount, "eur"))
```

## Testing Your Formatting

Always test formatting across your target locales:

```python
def test_formatting_consistency():
    """Test that formatting works consistently across locales."""
    test_amount = money(1234.56)

    locales = ["en_US", "de_DE", "fr_FR", "ja_JP"]

    for locale in locales:
        policy = DisplayPolicy(locale=locale, currency="USD")
        result = test_amount.format(policy)

        # Basic checks
        assert "1234" in result or "1 234" in result  # Number present
        assert len(result) > 5  # Reasonable length
        print(f"{locale}: {result}")

test_formatting_consistency()
```

## Next Steps

- Read the [Formatting Concepts](../concepts/formatting.md) for deeper understanding
- Check out the [Internationalization How-To](../howto/internationalization.md) for production usage
- Explore the [Policy documentation](../concepts/policy.md) for advanced policy configuration

This tutorial covered the essentials of formatting financial values. The key takeaways are:

1. Use `DisplayPolicy` to control formatting behavior
2. Install Babel for full internationalization support
3. Cache policies for better performance
4. Test across your target locales
5. Handle edge cases like zero and missing values
