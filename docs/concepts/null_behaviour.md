# Null Behaviour

Metric Engine provides sophisticated null handling that lets you control how missing, invalid, or undefined values are processed throughout your financial calculations. This system ensures predictable behavior when dealing with incomplete datasets or calculation errors.

## What is Null Behaviour?

Null behaviour defines how Metric Engine handles `None` values and invalid data in two key contexts:

1. **Binary Operations** - Arithmetic between two values (`a + b`, `a * b`, etc.)
2. **Reduction Operations** - Aggregations over collections (`sum()`, `mean()`, etc.)

The system is context-aware, thread-safe, and provides different strategies for different use cases, from strict data validation to flexible data analysis.

## Core Concepts

### Binary Operations

Control how `None` values are handled in arithmetic operations:

```python
from metricengine import money, NullBinaryMode, use_binary

# Default behavior: PROPAGATE - None spreads through calculations
amount = money(100)
invalid = money(None)
result = amount + invalid  # Returns None (safe)

# RAISE mode: Fail fast on None values
with use_binary(NullBinaryMode.RAISE):
    try:
        result = amount + invalid  # Raises CalculationError
    except CalculationError:
        print("Calculation failed due to None value")
```

### Reduction Operations

Control how `None` values are handled in aggregation operations:

```python
from metricengine import money, fv_sum, NullReductionMode, use_reduction

# Sample data with missing values
revenues = [money(1000), money(None), money(1500), money(2000)]

# SKIP mode (default): Ignore None values
with use_reduction(NullReductionMode.SKIP):
    total = fv_sum(revenues)  # $4,500 (skips None)

# PROPAGATE mode: None if any value is None
with use_reduction(NullReductionMode.PROPAGATE):
    total = fv_sum(revenues)  # None (any None makes result None)

# ZERO mode: Treat None as zero
with use_reduction(NullReductionMode.ZERO):
    total = fv_sum(revenues)  # $4,500 (None becomes 0)

# RAISE mode: Fail on any None
with use_reduction(NullReductionMode.RAISE):
    try:
        total = fv_sum(revenues)  # Raises CalculationError
    except CalculationError:
        print("Cannot sum data containing None values")
```

## Null Modes Explained

### Binary Operation Modes

#### PROPAGATE (Default)
Safe mode where any `None` operand results in `None`:

```python
from metricengine import money

# Any None operand makes the result None
valid_amount = money(100)
invalid_amount = money(None)

result1 = valid_amount + invalid_amount    # None
result2 = valid_amount * invalid_amount    # None
result3 = invalid_amount / valid_amount    # None

print(result1.is_none())  # True
```

#### RAISE
Strict mode that raises exceptions when encountering `None`:

```python
from metricengine import use_binary, NullBinaryMode, CalculationError

with use_binary(NullBinaryMode.RAISE):
    try:
        result = money(100) + money(None)  # Raises CalculationError
    except CalculationError as e:
        print(f"Calculation failed: {e}")
```

### Reduction Operation Modes

#### SKIP (Default)
Ignores `None` values and processes only valid values:

```python
from metricengine import fv_sum, fv_mean

data = [money(100), money(None), money(200), money(300)]

total = fv_sum(data)     # $600 (skips None)
average = fv_mean(data)  # $200 (600/3, skips None)
```

#### PROPAGATE
Returns `None` if any `None` values are present:

```python
from metricengine import use_reduction, NullReductionMode

with use_reduction(NullReductionMode.PROPAGATE):
    clean_data = [money(100), money(200), money(300)]
    dirty_data = [money(100), money(None), money(300)]

    clean_total = fv_sum(clean_data)  # $600
    dirty_total = fv_sum(dirty_data)  # None
```

#### ZERO
Treats `None` values as zero for calculations:

```python
with use_reduction(NullReductionMode.ZERO):
    data = [money(100), money(None), money(200)]

    total = fv_sum(data)    # $300 (None becomes $0)
    average = fv_mean(data) # $100 (300/3, None counted as 0)
```

#### RAISE
Raises exceptions when encountering `None` values:

```python
with use_reduction(NullReductionMode.RAISE):
    try:
        data = [money(100), money(None), money(200)]
        total = fv_sum(data)  # Raises CalculationError
    except CalculationError:
        print("Strict mode: no None values allowed")
```

## Context Management

### Combined Null Behavior

Set both binary and reduction modes together:

```python
from metricengine import NullBehavior, use_nulls

# Create combined behavior
strict_behavior = NullBehavior(
    binary=NullBinaryMode.RAISE,
    reduction=NullReductionMode.RAISE
)

# Apply to entire calculation block
with use_nulls(strict_behavior):
    # All operations will raise on None
    amount1 = money(100)
    amount2 = money(200)
    amounts = [amount1, amount2, money(300)]

    subtotal = amount1 + amount2      # Works: no None values
    total = fv_sum(amounts)           # Works: no None values
    # Any None would raise CalculationError
```

### Selective Mode Override

Override just one mode temporarily:

```python
from metricengine import use_binary, use_reduction

# Override just binary mode
with use_binary(NullBinaryMode.RAISE):
    # Binary ops raise on None, but reductions still use default (SKIP)
    result = money(100) + money(200)  # Works

    data_with_none = [money(100), money(None), money(200)]
    total = fv_sum(data_with_none)    # $300 (skips None)

# Override just reduction mode
with use_reduction(NullReductionMode.ZERO):
    # Reductions treat None as zero, binary ops still propagate None
    mixed_result = money(100) + money(None)  # None (propagates)

    data_with_none = [money(100), money(None), money(200)]
    total = fv_sum(data_with_none)           # $300 (None as zero)
```

## Predefined Behaviors

Metric Engine provides convenient predefined behaviors for common scenarios:

### DEFAULT_NULLS
Standard safe behavior (binary: PROPAGATE, reduction: SKIP):

```python
from metricengine import DEFAULT_NULLS, use_nulls

with use_nulls(DEFAULT_NULLS):
    # Safe binary operations
    safe_result = money(100) + money(None)  # None

    # Skip None in reductions
    data = [money(100), money(None), money(200)]
    total = fv_sum(data)  # $300
```

### STRICT_RAISE
Fail-fast on any None (binary: RAISE, reduction: RAISE):

```python
from metricengine import STRICT_RAISE

with use_nulls(STRICT_RAISE):
    # Both binary ops and reductions raise on None
    try:
        result = money(100) + money(None)  # Raises
    except CalculationError:
        print("No None values allowed anywhere")
```

### Specialized Reduction Behaviors

```python
from metricengine import SUM_ZERO, SUM_PROPAGATE, SUM_RAISE

# Treat None as zero in reductions
with use_nulls(SUM_ZERO):
    total = fv_sum([money(100), money(None), money(200)])  # $300

# Propagate None in reductions
with use_nulls(SUM_PROPAGATE):
    total = fv_sum([money(100), money(None), money(200)])  # None

# Raise on None in reductions
with use_nulls(SUM_RAISE):
    try:
        total = fv_sum([money(100), money(None), money(200)])  # Raises
    except CalculationError:
        print("Reduction failed due to None")
```

## Real-World Applications

### Data Cleaning Pipeline

```python
from metricengine import use_reduction, NullReductionMode, fv_sum, fv_mean

# Raw data with missing values
quarterly_revenues = [
    money(250_000),  # Q1
    money(None),     # Q2 - missing data
    money(280_000),  # Q3
    money(310_000)   # Q4
]

# Skip missing data for summary statistics
with use_reduction(NullReductionMode.SKIP):
    total_revenue = fv_sum(quarterly_revenues)      # $840,000
    average_revenue = fv_mean(quarterly_revenues)   # $280,000 (3 quarters)

    print(f"Total revenue (3 quarters): {total_revenue}")
    print(f"Average revenue: {average_revenue}")

# Conservative analysis: treat missing as zero revenue
with use_reduction(NullReductionMode.ZERO):
    conservative_total = fv_sum(quarterly_revenues)    # $840,000
    conservative_average = fv_mean(quarterly_revenues) # $210,000 (4 quarters)

    print(f"Conservative average: {conservative_average}")
```

### Financial Validation

```python
def validate_financial_data(revenues, expenses):
    """Strict validation requiring complete data."""
    with use_nulls(STRICT_RAISE):
        try:
            # All operations will fail if any None present
            total_revenue = fv_sum(revenues)
            total_expenses = fv_sum(expenses)
            profit = total_revenue - total_expenses
            margin = (profit / total_revenue).as_percentage()

            return {
                'revenue': total_revenue,
                'expenses': total_expenses,
                'profit': profit,
                'margin': margin
            }
        except CalculationError as e:
            raise ValueError(f"Data validation failed: {e}")

# Example usage
try:
    results = validate_financial_data(
        revenues=[money(100_000), money(120_000), money(None)],
        expenses=[money(80_000), money(90_000), money(85_000)]
    )
except ValueError as e:
    print(f"Validation error: {e}")  # Fails due to None revenue
```

### Scenario Analysis

```python
def analyze_scenarios(base_revenue, growth_rates):
    """Analyze revenue scenarios, handling invalid growth rates gracefully."""
    scenarios = []

    # Use SKIP to ignore invalid scenarios
    with use_reduction(NullReductionMode.SKIP):
        for i, rate in enumerate(growth_rates):
            if rate is None:
                continue

            # Binary operations propagate None safely
            projected_revenue = base_revenue * (1 + rate)

            if not projected_revenue.is_none():
                scenarios.append({
                    'scenario': i + 1,
                    'growth_rate': rate.as_percentage() if hasattr(rate, 'as_percentage') else f"{rate*100}%",
                    'projected_revenue': projected_revenue
                })

        if scenarios:
            revenues = [s['projected_revenue'] for s in scenarios]
            avg_projection = fv_mean(revenues)
            return {
                'scenarios': scenarios,
                'average_projection': avg_projection
            }

    return {'scenarios': [], 'average_projection': None}

# Example with mixed valid/invalid data
from metricengine import percent
base = money(1_000_000)
growth_scenarios = [
    percent(5, input="percent"),   # 5% growth
    None,                          # Invalid scenario
    percent(10, input="percent"),  # 10% growth
    percent(-2, input="percent")   # -2% decline
]

results = analyze_scenarios(base, growth_scenarios)
print(f"Average projection: {results['average_projection']}")
```

### Portfolio Risk Analysis

```python
def calculate_portfolio_metrics(returns_data):
    """Calculate portfolio metrics with different null handling for different purposes."""

    # For mean return: skip missing data points
    with use_reduction(NullReductionMode.SKIP):
        mean_return = fv_mean(returns_data)

    # For risk assessment: missing data means unknown risk (propagate None)
    with use_reduction(NullReductionMode.PROPAGATE):
        # This would return None if any returns are missing
        risk_assessment = fv_mean(returns_data) if not any(r.is_none() for r in returns_data if hasattr(r, 'is_none')) else None

    # For conservative total: treat missing as zero return
    with use_reduction(NullReductionMode.ZERO):
        conservative_total = fv_sum(returns_data)

    return {
        'mean_return': mean_return,
        'risk_assessment': risk_assessment,
        'conservative_total': conservative_total
    }

# Portfolio with some missing data
monthly_returns = [
    percent(2.5, input="percent"),   # Jan: +2.5%
    percent(None),                   # Feb: missing data
    percent(-1.2, input="percent"),  # Mar: -1.2%
    percent(3.8, input="percent")    # Apr: +3.8%
]

metrics = calculate_portfolio_metrics(monthly_returns)
print(f"Mean return (excluding missing): {metrics['mean_return']}")
print(f"Conservative total return: {metrics['conservative_total']}")
```

## Advanced Patterns

### Decorator-Based Null Handling

```python
from metricengine import with_nulls

@with_nulls(STRICT_RAISE)
def calculate_roi(investment, returns):
    """Calculate ROI with strict validation."""
    total_return = fv_sum(returns)
    roi = (total_return / investment).as_percentage()
    return roi

# Function will raise on any None values
try:
    roi = calculate_roi(
        money(100_000),
        [money(15_000), money(None), money(20_000)]  # Contains None
    )
except CalculationError:
    print("ROI calculation requires complete data")
```

### Conditional Null Handling

```python
def adaptive_calculation(data, strict_mode=False):
    """Adapt null handling based on context."""

    behavior = STRICT_RAISE if strict_mode else DEFAULT_NULLS

    with use_nulls(behavior):
        try:
            return fv_sum(data)
        except CalculationError:
            if strict_mode:
                raise
            # Fallback to lenient mode
            with use_nulls(DEFAULT_NULLS):
                return fv_sum(data)

# Strict mode
try:
    result = adaptive_calculation([money(100), money(None)], strict_mode=True)
except CalculationError:
    print("Strict mode failed")

# Lenient mode
result = adaptive_calculation([money(100), money(None)], strict_mode=False)
print(f"Lenient result: {result}")  # $100
```

## Best Practices

### 1. Choose Appropriate Modes for Your Use Case

```python
# Data analysis: Skip missing values
with use_reduction(NullReductionMode.SKIP):
    clean_average = fv_mean(noisy_data)

# Risk assessment: Propagate uncertainty
with use_reduction(NullReductionMode.PROPAGATE):
    risk_metric = calculate_risk(uncertain_data)

# Validation: Fail on incomplete data
with use_nulls(STRICT_RAISE):
    validated_result = process_critical_data(complete_data)
```

### 2. Document Null Handling Decisions

```python
class FinancialCalculator:
    """Financial calculator with explicit null handling policies."""

    def calculate_revenue_metrics(self, revenue_data):
        """
        Calculate revenue metrics.

        Null handling: Skips missing data points for summary statistics,
        as partial data is still meaningful for trend analysis.
        """
        with use_reduction(NullReductionMode.SKIP):
            return {
                'total': fv_sum(revenue_data),
                'average': fv_mean(revenue_data),
                'count': len([x for x in revenue_data if not x.is_none()])
            }

    def validate_regulatory_report(self, financial_data):
        """
        Validate data for regulatory reporting.

        Null handling: Strict mode - all data must be complete
        for regulatory compliance.
        """
        with use_nulls(STRICT_RAISE):
            return self._process_regulatory_data(financial_data)
```

### 3. Handle Edge Cases

```python
def safe_division_with_null_handling(numerator_data, denominator_data):
    """Safely divide datasets with proper null handling."""

    with use_reduction(NullReductionMode.SKIP):
        numerator_sum = fv_sum(numerator_data)
        denominator_sum = fv_sum(denominator_data)

    # Check for division by zero or None
    if denominator_sum.is_none() or denominator_sum.as_decimal() == 0:
        return money(None)  # Return None for invalid division

    if numerator_sum.is_none():
        return money(None)

    return numerator_sum / denominator_sum

# Example usage
ratios = safe_division_with_null_handling(
    [money(100), money(None), money(200)],  # Numerator: partial data
    [money(50), money(75), money(25)]       # Denominator: complete data
)
```

### 4. Thread Safety Considerations

```python
import threading
from metricengine import use_nulls, DEFAULT_NULLS

def worker_function(data, thread_id):
    """Each thread can have its own null handling context."""

    # Each thread gets its own context
    behavior = DEFAULT_NULLS if thread_id % 2 == 0 else STRICT_RAISE

    with use_nulls(behavior):
        return fv_sum(data)

# Multiple threads with different null handling
threads = []
for i in range(4):
    thread = threading.Thread(
        target=worker_function,
        args=([money(100), money(None)], i)
    )
    threads.append(thread)
    thread.start()
```

Metric Engine's null behaviour system provides the flexibility to handle missing and invalid data appropriately for your specific use case, whether you need strict validation, graceful error handling, or flexible data analysis capabilities.
