# Policy

Policies are immutable configuration objects that control how financial calculations are performed, formatted, and displayed throughout Metric Engine. They provide consistent, predictable behavior across all operations.

## What is a Policy?

A `Policy` defines the rules for:

- **Formatting** - Decimal places, thousands separators, currency symbols
- **Rounding** - How numbers are rounded during calculations and display
- **Display preferences** - How percentages, money, and null values appear
- **Behavior controls** - Error handling, validation rules, arithmetic modes
- **Localization** - Currency positioning, regional formatting preferences

Policies ensure consistent behavior across all financial calculations and provide fine-grained control over how results are presented.

## Core Configuration Options

### Precision and Rounding

```python
from metricengine import Policy, money
from decimal import ROUND_DOWN, ROUND_UP

# Default policy: 2 decimal places, round half up
default_policy = Policy()
amount = money(123.456, policy=default_policy)
print(amount)  # "$123.46"

# High precision policy
precision_policy = Policy(decimal_places=4, rounding=ROUND_DOWN)
precise_amount = money(123.456789, policy=precision_policy)
print(precise_amount)  # "$123.4567"

# Conservative rounding for financial reporting
conservative_policy = Policy(decimal_places=2, rounding=ROUND_DOWN)
conservative_amount = money(999.999, policy=conservative_policy)
print(conservative_amount)  # "$999.99"
```

### Currency Formatting

```python
# US Dollar formatting (default)
usd_policy = Policy(
    currency_symbol="$",
    currency_position="prefix",
    thousands_sep=True,
    negative_parentheses=False
)

# European Euro formatting
eur_policy = Policy(
    currency_symbol="€",
    currency_position="suffix",
    thousands_sep=True,
    decimal_places=2
)

# Accounting style with parentheses for negatives
accounting_policy = Policy(
    currency_symbol="$",
    currency_position="prefix",
    negative_parentheses=True,
    thousands_sep=True
)

amount = money(1234.56)
usd_amount = amount.with_policy(usd_policy)
eur_amount = amount.with_policy(eur_policy)
accounting_negative = money(-1234.56, policy=accounting_policy)

print(usd_amount)           # "$1,234.56"
print(eur_amount)           # "1,234.56€"
print(accounting_negative)  # "($1,234.56)"
```

### Percentage Display

```python
from metricengine import percent, Policy

# Standard percentage display (multiply by 100)
percent_policy = Policy(percent_display="percent", decimal_places=2)
growth = percent(0.155, input="ratio", policy=percent_policy)
print(growth)  # "15.50%"

# Ratio display (show as decimal)
ratio_policy = Policy(percent_display="ratio", decimal_places=3)
multiplier = percent(0.155, input="ratio", policy=ratio_policy)
print(multiplier)  # "0.155"

# Capped percentages for display purposes
capped_policy = Policy(
    percent_display="percent",
    cap_percentage_at=Decimal("100.00"),  # Cap at 100%
    decimal_places=1
)
```

### Null Value Handling

```python
# Custom null text
custom_null_policy = Policy(none_text="N/A")
invalid_amount = money(None, policy=custom_null_policy)
print(invalid_amount)  # "N/A"

# Different null representations
dash_policy = Policy(none_text="—")        # Em dash (default)
blank_policy = Policy(none_text="")        # Empty string
na_policy = Policy(none_text="Not Available")  # Descriptive text
```

## Policy Context Management

### Using Policies with Context Managers

Metric Engine provides context managers for applying policies across multiple operations:

```python
from metricengine import use_policy, Policy, money, percent

# Create some data
base_amount = money(10000)
growth_rate = percent(15, input="percent")

# Standard precision context
standard_policy = Policy(decimal_places=2)
with use_policy(standard_policy):
    result = base_amount * growth_rate
    final = base_amount + result
    print(final)  # "$11,500.00"

# High precision context for detailed analysis
analysis_policy = Policy(decimal_places=4)
with use_policy(analysis_policy):
    precise_result = base_amount * growth_rate
    precise_final = base_amount + precise_result
    print(precise_final)  # "$11,500.0000"
```

### Policy Resolution Modes

Control how policies are chosen when operations involve values with different policies:

```python
from metricengine import use_policy_resolution, PolicyResolution
from metricengine import Policy, money

# Create values with different policies
amount1 = money(100, policy=Policy(decimal_places=2))
amount2 = money(200, policy=Policy(decimal_places=4))

# LEFT_OPERAND: Use policy from left operand
with use_policy_resolution(PolicyResolution.LEFT_OPERAND):
    result = amount1 + amount2  # Uses 2 decimal places
    print(result)  # "$300.00"

# CONTEXT: Use active context policy
high_precision = Policy(decimal_places=6)
with use_policy(high_precision):
    with use_policy_resolution(PolicyResolution.CONTEXT):
        result = amount1 + amount2  # Uses context policy (6 decimal places)
        print(result)  # "$300.000000"

# STRICT_MATCH: Require matching policies
with use_policy_resolution(PolicyResolution.STRICT_MATCH):
    try:
        result = amount1 + amount2  # Raises ValueError
    except ValueError as e:
        print("Policies must match in STRICT_MATCH mode")
```

## Advanced Policy Features

### Custom Quantizer Functions

Create specialized rounding behaviors:

```python
from decimal import Decimal

def quarter_rounding(decimal_places: int) -> Decimal:
    """Round to nearest quarter (0.25)."""
    if decimal_places == 2:
        return Decimal("0.25")
    return Decimal(1).scaleb(-decimal_places)

quarter_policy = Policy(
    quantizer_factory=quarter_rounding,
    decimal_places=2
)

# Prices rounded to nearest quarter
price = money(12.37, policy=quarter_policy)
print(price)  # "$12.25" (rounded down to nearest quarter)

price2 = money(12.63, policy=quarter_policy)
print(price2)  # "$12.75" (rounded up to nearest quarter)
```

### Behavior Control Flags

```python
# Control specific calculation behaviors
strict_policy = Policy(
    negative_sales_is_none=True,      # Treat negative sales as None
    arithmetic_strict=True,           # Strict arithmetic error handling
    compare_none_as_minus_infinity=False  # None comparison behavior
)

# Apply to calculations
from metricengine import Engine
engine = Engine(policy=strict_policy)
```

## Real-World Policy Applications

### Financial Reporting

```python
# GAAP-compliant financial reporting policy
gaap_policy = Policy(
    decimal_places=2,
    currency_symbol="$",
    currency_position="prefix",
    thousands_sep=True,
    negative_parentheses=True,  # Standard accounting format
    none_text="—"
)

# International reporting
ifrs_policy = Policy(
    decimal_places=2,
    currency_symbol="€",
    currency_position="suffix",
    thousands_sep=True,
    negative_parentheses=False,
    none_text="N/A"
)
```

### Trading Systems

```python
# High-frequency trading: maximum precision
hft_policy = Policy(
    decimal_places=8,
    rounding=ROUND_DOWN,  # Conservative rounding
    thousands_sep=False,  # Clean numeric display
    currency_symbol=None  # No currency decoration
)

# Portfolio analysis: balanced precision and readability
portfolio_policy = Policy(
    decimal_places=4,
    currency_symbol="$",
    thousands_sep=True,
    percent_display="percent",
    none_text="No Data"
)
```

### Dashboard Applications

```python
# Executive dashboard: clean, readable format
dashboard_policy = Policy(
    decimal_places=0,           # Round to whole dollars
    thousands_sep=True,
    currency_symbol="$",
    negative_parentheses=False
)

# Analyst dashboard: detailed precision
analyst_policy = Policy(
    decimal_places=2,
    thousands_sep=True,
    currency_symbol="$",
    percent_display="percent",
    cap_percentage_at=Decimal("999.99")  # Cap extreme percentages
)

# Create dashboard metrics
revenue = money(1_234_567.89)
print(revenue.with_policy(dashboard_policy))  # "$1,234,568"
print(revenue.with_policy(analyst_policy))    # "$1,234,567.89"
```

## Policy Inheritance and Propagation

### Automatic Policy Inheritance

Financial values inherit policies through operations:

```python
# Base policy
base_policy = Policy(decimal_places=3, currency_symbol="$")
amount = money(100.1234, policy=base_policy)

# Operations inherit the policy
doubled = amount * 2
print(doubled)  # "$200.247" (3 decimal places inherited)

# Percentage calculations maintain policy context
rate = percent(10, input="percent")
increase = amount * rate
print(increase)  # "$10.012" (policy inherited from amount)
```

### Policy Precedence Rules

1. **Context Policy** (via `use_policy`) takes highest precedence
2. **Operand Policies** - resolved based on resolution mode
3. **Default Policy** - fallback when no specific policy is set

```python
# Demonstrate policy precedence
amount1 = money(100, policy=Policy(decimal_places=1))
amount2 = money(200, policy=Policy(decimal_places=3))

# Context overrides operand policies
context_policy = Policy(decimal_places=5)
with use_policy(context_policy):
    result = amount1 + amount2
    print(result.policy.decimal_places)  # 5 (context wins)
```

## Performance Considerations

### Policy Reuse

Policies are immutable and can be safely reused:

```python
# Create shared policies for performance
STANDARD_MONEY = Policy(decimal_places=2, currency_symbol="$", thousands_sep=True)
HIGH_PRECISION = Policy(decimal_places=6, currency_symbol="$")

# Reuse across many values
amounts = [money(val, policy=STANDARD_MONEY) for val in [100, 200, 300]]
precise_amounts = [money(val, policy=HIGH_PRECISION) for val in [1.234567, 2.345678]]
```

### Context Manager Efficiency

Use context managers for batch operations:

```python
# Efficient: Set policy once for many operations
with use_policy(STANDARD_MONEY):
    results = []
    for value in large_dataset:
        processed = money(value) * growth_rate
        results.append(processed)

# Less efficient: Set policy per operation
results = []
for value in large_dataset:
    processed = money(value, policy=STANDARD_MONEY) * growth_rate
    results.append(processed)
```

## Best Practices

### 1. Define Domain-Specific Policies

```python
# Create policies for specific use cases
ACCOUNTING_POLICY = Policy(
    decimal_places=2,
    currency_symbol="$",
    negative_parentheses=True,
    thousands_sep=True
)

TRADING_POLICY = Policy(
    decimal_places=4,
    currency_symbol=None,
    thousands_sep=False,
    rounding=ROUND_DOWN
)

REPORTING_POLICY = Policy(
    decimal_places=2,
    currency_symbol="$",
    thousands_sep=True,
    none_text="N/A"
)
```

### 2. Use Context Managers for Consistency

```python
def generate_financial_report(data):
    with use_policy(REPORTING_POLICY):
        revenue = money(data['revenue'])
        costs = money(data['costs'])
        profit = revenue - costs
        margin = (profit / revenue).as_percentage()

        return {
            'revenue': str(revenue),
            'costs': str(costs),
            'profit': str(profit),
            'margin': str(margin)
        }
```

### 3. Validate Policy Configuration

```python
def create_validated_policy(**kwargs):
    """Create policy with validation."""
    if 'decimal_places' in kwargs and kwargs['decimal_places'] < 0:
        raise ValueError("decimal_places must be non-negative")

    if 'currency_symbol' in kwargs:
        symbol = kwargs['currency_symbol']
        if symbol is not None and not symbol.strip():
            raise ValueError("currency_symbol must be non-empty or None")

    return Policy(**kwargs)
```

### 4. Document Policy Choices

```python
class PolicyPresets:
    """Standard policy configurations for different use cases."""

    # General purpose financial calculations
    STANDARD = Policy(
        decimal_places=2,
        currency_symbol="$",
        thousands_sep=True,
        negative_parentheses=False
    )

    # High-precision scientific calculations
    SCIENTIFIC = Policy(
        decimal_places=10,
        currency_symbol=None,
        thousands_sep=False,
        rounding=ROUND_HALF_UP
    )

    # Accounting and financial reporting
    ACCOUNTING = Policy(
        decimal_places=2,
        currency_symbol="$",
        thousands_sep=True,
        negative_parentheses=True,  # Standard accounting format
        none_text="—"
    )
```

Policies provide the foundation for consistent, predictable financial calculations throughout Metric Engine, ensuring your results are formatted correctly and calculations behave as expected across different contexts and use cases.
