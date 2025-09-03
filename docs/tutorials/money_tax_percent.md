# Money, Tax, and Percentages

Working with monetary values, tax calculations, and percentages.

## Money Basics

```python
from metricengine import Money

# Create money values
price = Money(100, "USD")
tax_rate = Percentage(8.25)

# Calculate tax
tax = price * tax_rate / 100
total = price + tax
```

## Tax Calculations

Common tax scenarios:
- Sales tax
- Income tax
- VAT calculations

## Percentage Operations

```python
# Percentage of a value
discount = Percentage(15)
discount_amount = price * discount / 100

# Percentage change
old_price = Money(90, "USD")
new_price = Money(100, "USD")
change = ((new_price - old_price) / old_price) * 100
```
