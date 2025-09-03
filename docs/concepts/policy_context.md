# Policy Context

Policy contexts provide sophisticated, thread-safe scope management for financial calculations, allowing you to apply specific policies to code blocks without affecting global state. This system enables fine-grained control over calculation behavior across different parts of your application.

## What is Policy Context?

Policy context is a thread-safe, scoped configuration system that manages two key aspects:

1. **Policy Application** - Which specific `Policy` settings apply to calculations
2. **Policy Resolution** - How policy conflicts are resolved when operations involve values with different policies

The context system uses Python's `ContextVar` for thread-local storage, ensuring that policy changes in one thread don't affect other threads, making it safe for concurrent financial applications.

## Core Components

### Policy Context Management

Apply policies to specific code blocks without affecting global state:

```python
from metricengine import use_policy, Policy, money

# Global/default behavior
amount = money(123.456)  # Uses default policy
print(amount)  # "$123.46" (2 decimal places)

# Scoped policy application
high_precision = Policy(decimal_places=4)
with use_policy(high_precision):
    precise_amount = money(123.456789)
    print(precise_amount)  # "$123.4567" (4 decimal places)

    # All operations in this block use high precision
    calculation = precise_amount * 2
    print(calculation)  # "$246.9135"

# Back to default behavior
normal_amount = money(123.456)
print(normal_amount)  # "$123.46" (2 decimal places again)
```

### Policy Resolution Modes

Control how policy conflicts are resolved when operations involve values with different policies:

```python
from metricengine import use_policy_resolution, PolicyResolution, Policy

# Create values with different policies
amount1 = money(100, policy=Policy(decimal_places=2))  # 2 decimal places
amount2 = money(200, policy=Policy(decimal_places=4))  # 4 decimal places

# CONTEXT mode (default): Use active context policy
context_policy = Policy(decimal_places=6)
with use_policy(context_policy):
    with use_policy_resolution(PolicyResolution.CONTEXT):
        result = amount1 + amount2  # Uses context policy (6 decimal places)
        print(result)  # "$300.000000"

# LEFT_OPERAND mode: Use left operand's policy
with use_policy_resolution(PolicyResolution.LEFT_OPERAND):
    result = amount1 + amount2  # Uses amount1's policy (2 decimal places)
    print(result)  # "$300.00"

# STRICT_MATCH mode: Require identical policies
with use_policy_resolution(PolicyResolution.STRICT_MATCH):
    try:
        result = amount1 + amount2  # Raises ValueError
    except ValueError as e:
        print("Policies must match exactly")
```

## Policy Resolution Strategies

### CONTEXT Mode (Default)

Uses the active context policy, falling back to default policy:

```python
from metricengine import use_policy, PolicyResolution, use_policy_resolution

# No context set - uses default policy
amount1 = money(100, policy=Policy(decimal_places=1))
amount2 = money(200, policy=Policy(decimal_places=5))

result = amount1 + amount2  # Uses default policy (2 decimal places)
print(result)  # "$300.00"

# Context set - uses context policy
precision_policy = Policy(decimal_places=3)
with use_policy(precision_policy):
    result = amount1 + amount2  # Uses context policy (3 decimal places)
    print(result)  # "$300.000"
```

### LEFT_OPERAND Mode

Uses the policy from the left operand, with fallback logic:

```python
with use_policy_resolution(PolicyResolution.LEFT_OPERAND):
    # Left operand policy takes precedence
    high_precision = money(100, policy=Policy(decimal_places=4))
    low_precision = money(200, policy=Policy(decimal_places=1))

    result1 = high_precision + low_precision  # Uses high precision (4dp)
    result2 = low_precision + high_precision  # Uses low precision (1dp)

    print(result1)  # "$300.0000"
    print(result2)  # "$300.0"

    # Mixed with raw values
    raw_result = high_precision + 50  # Raw value adopts left operand's policy
    print(raw_result)  # "$150.0000"
```

### STRICT_MATCH Mode

Requires all operands to have identical policies:

```python
with use_policy_resolution(PolicyResolution.STRICT_MATCH):
    # Identical policies - works fine
    policy = Policy(decimal_places=3)
    amount1 = money(100, policy=policy)
    amount2 = money(200, policy=policy)
    result = amount1 + amount2  # Works: identical policies
    print(result)  # "$300.000"

    # Different policies - raises error
    different_amount = money(300, policy=Policy(decimal_places=2))
    try:
        error_result = amount1 + different_amount  # Raises ValueError
    except ValueError:
        print("STRICT_MATCH requires identical policies")
```

## Context Nesting and Composition

### Nested Policy Contexts

Inner contexts override outer contexts with automatic restoration:

```python
# Base policy
base_policy = Policy(decimal_places=2, currency_symbol="$")

# Nested context application
with use_policy(base_policy):
    amount = money(123.456)
    print(f"Base: {amount}")  # "$123.46"

    # Override with higher precision
    precise_policy = Policy(decimal_places=4, currency_symbol="$")
    with use_policy(precise_policy):
        precise_amount = money(123.456789)
        print(f"Precise: {precise_amount}")  # "$123.4567"

        # Even higher precision
        ultra_precise = Policy(decimal_places=6, currency_symbol="$")
        with use_policy(ultra_precise):
            ultra_amount = money(123.456789123)
            print(f"Ultra: {ultra_amount}")  # "$123.456789"

        # Back to precise
        print(f"Back to precise: {money(123.456789)}")  # "$123.4567"

    # Back to base
    print(f"Back to base: {money(123.456)}")  # "$123.46"

# Back to default
print(f"Default: {money(123.456)}")  # "$123.46"
```

### Combined Policy and Resolution Contexts

Use both context types together for complete control:

```python
# High precision analysis context
analysis_policy = Policy(
    decimal_places=6,
    currency_symbol="$",
    thousands_sep=False  # Clean numbers for analysis
)

with use_policy(analysis_policy):
    with use_policy_resolution(PolicyResolution.CONTEXT):
        # All operations use analysis policy regardless of operand policies
        mixed_data = [
            money(100.123, policy=Policy(decimal_places=2)),
            money(200.456, policy=Policy(decimal_places=3)),
            money(300.789, policy=Policy(decimal_places=4))
        ]

        # All calculations use analysis_policy (6 decimal places)
        total = sum(mixed_data[1:], mixed_data[0])  # Start with first element
        average = total / 3

        print(f"Total: {total}")    # "$601.368000"
        print(f"Average: {average}") # "$200.456000"
```

## Real-World Applications

### Financial Reporting Pipeline

```python
def generate_financial_report(revenue_data, expense_data):
    """Generate financial report with consistent formatting."""

    # Standard reporting policy
    reporting_policy = Policy(
        decimal_places=2,
        currency_symbol="$",
        thousands_sep=True,
        negative_parentheses=True  # Accounting style
    )

    with use_policy(reporting_policy):
        with use_policy_resolution(PolicyResolution.CONTEXT):
            # All calculations use consistent reporting format
            total_revenue = sum(revenue_data)
            total_expenses = sum(expense_data)
            net_income = total_revenue - total_expenses
            margin = (net_income / total_revenue).as_percentage()

            return {
                'revenue': str(total_revenue),    # "$1,234,567.00"
                'expenses': str(total_expenses),  # "$987,654.00"
                'net_income': str(net_income),    # "$246,913.00"
                'margin': str(margin)             # "20.02%"
            }

# Usage with mixed-precision input data
revenue_data = [
    money(500_000.123, policy=Policy(decimal_places=3)),  # High precision
    money(734_567, policy=Policy(decimal_places=0))       # Whole numbers
]

expense_data = [
    money(300_000.45, policy=Policy(decimal_places=2)),   # Standard precision
    money(687_654.321, policy=Policy(decimal_places=3))   # High precision
]

report = generate_financial_report(revenue_data, expense_data)
print(report)
```

### Multi-Currency Trading System

```python
def execute_currency_trades(trades_data):
    """Execute trades with currency-specific policies."""

    results = {}

    # USD trades - standard precision
    usd_policy = Policy(
        decimal_places=2,
        currency_symbol="$",
        currency_position="prefix"
    )

    # Crypto trades - high precision
    crypto_policy = Policy(
        decimal_places=8,
        currency_symbol="₿",
        currency_position="prefix",
        thousands_sep=False
    )

    # Process USD trades
    with use_policy(usd_policy):
        with use_policy_resolution(PolicyResolution.CONTEXT):
            usd_trades = [money(amt) for amt in trades_data['usd']]
            usd_total = sum(usd_trades[1:], usd_trades[0])
            results['usd_total'] = str(usd_total)  # "$12,345.67"

    # Process crypto trades
    with use_policy(crypto_policy):
        with use_policy_resolution(PolicyResolution.CONTEXT):
            crypto_trades = [money(amt) for amt in trades_data['crypto']]
            crypto_total = sum(crypto_trades[1:], crypto_trades[0])
            results['crypto_total'] = str(crypto_total)  # "₿1.23456789"

    return results

# Execute trades
trades = {
    'usd': [1000.50, 2500.75, 8844.42],
    'crypto': [0.12345678, 0.87654321, 0.23456789]
}

trade_results = execute_currency_trades(trades)
print(trade_results)
```

### Risk Analysis with Different Precision Requirements

```python
def perform_risk_analysis(portfolio_data):
    """Perform risk analysis with different precision for different metrics."""

    # High precision for internal calculations
    calculation_policy = Policy(decimal_places=10, currency_symbol=None)

    # Standard precision for reporting
    reporting_policy = Policy(decimal_places=2, currency_symbol="$")

    results = {}

    # High-precision calculations
    with use_policy(calculation_policy):
        with use_policy_resolution(PolicyResolution.CONTEXT):
            # Detailed risk calculations
            values = [money(amount) for amount in portfolio_data]
            total_value = sum(values[1:], values[0])

            # Calculate variance with high precision
            mean_value = total_value / len(values)
            squared_diffs = [(v - mean_value) ** 2 for v in values]
            variance = sum(squared_diffs[1:], squared_diffs[0]) / len(squared_diffs)

            # Store high-precision intermediate results
            results['internal_mean'] = mean_value
            results['internal_variance'] = variance

    # Convert to reporting format
    with use_policy(reporting_policy):
        with use_policy_resolution(PolicyResolution.CONTEXT):
            # Convert high-precision results to reporting format
            results['reported_total'] = str(results['internal_mean'] * len(portfolio_data))
            results['reported_mean'] = str(results['internal_mean'])
            results['reported_risk'] = str(results['internal_variance'] ** 0.5)  # Standard deviation

    return results

# Portfolio analysis
portfolio = [100_000, 125_000, 98_500, 110_750, 105_250]
risk_metrics = perform_risk_analysis(portfolio)

print(f"Portfolio Total: {risk_metrics['reported_total']}")  # "$539,500.00"
print(f"Average Value: {risk_metrics['reported_mean']}")     # "$107,900.00"
print(f"Risk Metric: {risk_metrics['reported_risk']}")       # "$9,234.56"
```

### Batch Processing with Dynamic Policies

```python
def process_financial_batch(batch_config, data_batches):
    """Process financial data batches with different policy requirements."""

    results = []

    for batch_name, config in batch_config.items():
        batch_data = data_batches[batch_name]

        # Create policy from config
        policy = Policy(
            decimal_places=config['precision'],
            currency_symbol=config['currency'],
            thousands_sep=config['use_separators'],
            negative_parentheses=config.get('accounting_style', False)
        )

        # Apply policy to entire batch
        with use_policy(policy):
            with use_policy_resolution(PolicyResolution.CONTEXT):
                batch_amounts = [money(amount) for amount in batch_data]
                batch_total = sum(batch_amounts[1:], batch_amounts[0])
                batch_average = batch_total / len(batch_amounts)

                results.append({
                    'batch': batch_name,
                    'total': str(batch_total),
                    'average': str(batch_average),
                    'count': len(batch_amounts)
                })

    return results

# Configuration for different batch types
config = {
    'us_retail': {
        'precision': 2,
        'currency': '$',
        'use_separators': True,
        'accounting_style': False
    },
    'crypto_trading': {
        'precision': 8,
        'currency': '₿',
        'use_separators': False,
        'accounting_style': False
    },
    'accounting_entries': {
        'precision': 2,
        'currency': '$',
        'use_separators': True,
        'accounting_style': True  # Negative values in parentheses
    }
}

# Data batches
batches = {
    'us_retail': [1234.56, 2345.67, 3456.78],
    'crypto_trading': [0.12345678, 0.23456789, 0.34567890],
    'accounting_entries': [5000.00, -1500.00, 2750.00]
}

batch_results = process_financial_batch(config, batches)
for result in batch_results:
    print(f"{result['batch']}: Total={result['total']}, Average={result['average']}")
```

## Thread Safety

### Concurrent Processing

Policy contexts are thread-safe using `ContextVar`:

```python
import threading
from metricengine import use_policy, Policy, money

def worker_thread(thread_id, amounts, policy_config):
    """Process amounts in a separate thread with its own policy context."""

    # Each thread gets its own policy context
    thread_policy = Policy(**policy_config)

    with use_policy(thread_policy):
        thread_amounts = [money(amount) for amount in amounts]
        total = sum(thread_amounts[1:], thread_amounts[0])

        print(f"Thread {thread_id}: {total} (precision: {policy_config['decimal_places']})")
        return total

# Launch multiple threads with different policies
threads = []
thread_configs = [
    {'decimal_places': 2, 'currency_symbol': '$'},   # Thread 0: Standard
    {'decimal_places': 4, 'currency_symbol': '$'},   # Thread 1: High precision
    {'decimal_places': 0, 'currency_symbol': '$'},   # Thread 2: Whole numbers
    {'decimal_places': 6, 'currency_symbol': '$'}    # Thread 3: Ultra precision
]

amounts = [123.456789, 234.567890, 345.678901]

for i, config in enumerate(thread_configs):
    thread = threading.Thread(
        target=worker_thread,
        args=(i, amounts, config)
    )
    threads.append(thread)
    thread.start()

# Wait for all threads
for thread in threads:
    thread.join()

# Each thread maintains its own policy context independently
```

## Performance Considerations

### Context Manager Efficiency

```python
# Efficient: Set policy once for multiple operations
high_precision = Policy(decimal_places=6)
data = [123.456789, 234.567890, 345.678901] * 1000  # Large dataset

with use_policy(high_precision):
    # All operations share the same policy context
    results = []
    for value in data:
        amount = money(value)
        doubled = amount * 2
        results.append(doubled)

# Less efficient: Create new context for each operation
results = []
for value in data:
    with use_policy(high_precision):  # Context overhead per operation
        amount = money(value)
        doubled = amount * 2
        results.append(doubled)
```

### Policy Reuse

```python
# Create reusable policies
STANDARD_REPORTING = Policy(decimal_places=2, currency_symbol="$", thousands_sep=True)
HIGH_PRECISION = Policy(decimal_places=8, currency_symbol="$", thousands_sep=False)
ACCOUNTING_FORMAT = Policy(decimal_places=2, currency_symbol="$", negative_parentheses=True)

def process_with_standard_format(data):
    with use_policy(STANDARD_REPORTING):
        return [money(amount) for amount in data]

def process_with_high_precision(data):
    with use_policy(HIGH_PRECISION):
        return [money(amount) for amount in data]

def process_for_accounting(data):
    with use_policy(ACCOUNTING_FORMAT):
        return [money(amount) for amount in data]
```

## Best Practices

### 1. Use Appropriate Resolution Modes

```python
# Data analysis: Use CONTEXT for consistent formatting
def analyze_mixed_data(data):
    analysis_policy = Policy(decimal_places=4)
    with use_policy(analysis_policy):
        with use_policy_resolution(PolicyResolution.CONTEXT):
            # All results formatted consistently
            return process_financial_data(data)

# Chain calculations: Use LEFT_OPERAND to preserve original precision
def chain_calculations(initial_value):
    with use_policy_resolution(PolicyResolution.LEFT_OPERAND):
        # Preserves initial_value's policy through chain
        result = initial_value * 1.05  # 5% increase
        result = result + 100          # Add $100
        return result

# Validation: Use STRICT_MATCH for exact requirements
def validate_matching_policies(amounts):
    with use_policy_resolution(PolicyResolution.STRICT_MATCH):
        return sum(amounts[1:], amounts[0])  # Requires all same policy
```

### 2. Design Context Hierarchies

```python
class FinancialProcessor:
    """Financial processor with hierarchical policy contexts."""

    def __init__(self):
        self.base_policy = Policy(decimal_places=2, currency_symbol="$")

    def process_standard_report(self, data):
        """Standard report with base formatting."""
        with use_policy(self.base_policy):
            return self._process_data(data)

    def process_detailed_analysis(self, data):
        """Detailed analysis with high precision."""
        analysis_policy = Policy(decimal_places=6, currency_symbol="$")
        with use_policy(analysis_policy):
            return self._process_data(data)

    def process_accounting_report(self, data):
        """Accounting report with parentheses for negatives."""
        accounting_policy = Policy(
            decimal_places=2,
            currency_symbol="$",
            negative_parentheses=True
        )
        with use_policy(accounting_policy):
            return self._process_data(data)

    def _process_data(self, data):
        # This method inherits the active policy context
        return [money(amount) for amount in data]
```

### 3. Handle Context Errors Gracefully

```python
def safe_strict_calculation(amounts):
    """Safely perform strict policy calculation with fallback."""
    try:
        with use_policy_resolution(PolicyResolution.STRICT_MATCH):
            return sum(amounts[1:], amounts[0])
    except ValueError as e:
        # Policies don't match - fall back to context mode
        print(f"Strict match failed ({e}), using context mode")
        with use_policy_resolution(PolicyResolution.CONTEXT):
            return sum(amounts[1:], amounts[0])

# Example usage
mixed_amounts = [
    money(100, policy=Policy(decimal_places=2)),
    money(200, policy=Policy(decimal_places=4))  # Different policy
]

result = safe_strict_calculation(mixed_amounts)  # Falls back gracefully
```

### 4. Document Context Usage

```python
def calculate_portfolio_metrics(holdings):
    """
    Calculate portfolio metrics with specific policy requirements.

    Policy Context:
    - Uses high-precision (8 decimal places) for internal calculations
    - Uses standard precision (2 decimal places) for reporting
    - Resolution: CONTEXT mode to ensure consistent formatting

    Args:
        holdings: List of portfolio holdings amounts

    Returns:
        dict: Portfolio metrics formatted for reporting
    """
    # High precision for calculations
    calc_policy = Policy(decimal_places=8, currency_symbol=None)

    # Standard precision for reporting
    report_policy = Policy(decimal_places=2, currency_symbol="$")

    # Internal calculations
    with use_policy(calc_policy):
        with use_policy_resolution(PolicyResolution.CONTEXT):
            amounts = [money(amount) for amount in holdings]
            total = sum(amounts[1:], amounts[0])
            mean = total / len(amounts)

    # Convert to reporting format
    with use_policy(report_policy):
        with use_policy_resolution(PolicyResolution.CONTEXT):
            return {
                'total_value': str(total),
                'average_holding': str(mean),
                'count': len(holdings)
            }
```

Policy contexts provide powerful, flexible control over financial calculations while maintaining thread safety and performance. Use them to ensure consistent formatting, handle policy conflicts intelligently, and create maintainable financial applications with predictable behavior.
