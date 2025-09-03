# Units

Metric Engine's unit system provides type-safe dimensional analysis for financial calculations, preventing meaningless operations and ensuring mathematical correctness. Units act as compile-time and runtime guards that encode the semantic meaning of financial values, making calculations more robust and self-documenting.

## What are Units?

Units in Metric Engine are type markers that encode the dimensional meaning of financial values. They serve three critical purposes:

1. **Type Safety** - Prevent nonsensical operations like adding dollars to percentages
2. **Semantic Clarity** - Make code self-documenting by encoding business meaning
3. **Mathematical Correctness** - Ensure operations follow proper financial mathematics

Unlike traditional unit systems that focus on physical dimensions, Metric Engine's units are designed specifically for financial semantics and business logic.

## Core Unit Types

Metric Engine provides four fundamental unit types, each designed for specific financial use cases:

### Money

Represents monetary amounts and currency values:

```python
from metricengine import money, Policy

# Create monetary values
revenue = money(100_000)
cost = money(75_000)
profit = revenue - cost

print(revenue)  # "$100,000.00"
print(cost)     # "$75,000.00"
print(profit)   # "$25,000.00"

# Type safety: Money operations are validated
valid_total = revenue + cost      # ✓ Money + Money = Money
# invalid_mix = revenue + 0.25    # Would return None - no units to guide operation
```

**Money Unit Properties:**
- Represents currency amounts (dollars, euros, etc.)
- Supports addition, subtraction with other Money values
- Multiplication/division with dimensionless values and ratios
- Cannot be directly added to percentages or non-monetary units
- Formatted with currency symbols and thousands separators

### Percent

Represents percentage values with automatic display formatting:

```python
from metricengine import percent

# Input as percentage (15.5% -> stored as 0.155)
tax_rate = percent(15.5, input="percent")
print(tax_rate)  # "15.50%"

# Input as ratio (0.155 -> displayed as 15.5%)
growth_rate = percent(0.155, input="ratio")
print(growth_rate)  # "15.50%"

# Both methods store the same internal value
assert tax_rate.as_decimal() == growth_rate.as_decimal()  # Both are 0.155

# Type safety in action
revenue = money(100_000)
taxable_income = revenue * tax_rate  # ✓ Money * Percent = Money
print(taxable_income)  # "$15,500.00"
```

**Percent Unit Properties:**
- Stores values as ratios (0.155 for 15.5%) internally
- Displays with percentage formatting (15.50%)
- Inherits from Ratio for mathematical operations
- Automatically handles ratio/percentage conversion
- Used for rates, margins, growth percentages

### Ratio

Represents pure ratios and multipliers without percentage formatting:

```python
from metricengine import ratio

# Pure ratios for calculations
multiplier = ratio(1.25)        # 25% increase multiplier
efficiency = ratio(0.85)        # 85% efficiency
exchange_rate = ratio(1.18)     # Currency exchange rate

print(multiplier)    # "1.25" (not "125%")
print(efficiency)    # "0.85" (not "85%")
print(exchange_rate) # "1.18" (not "118%")

# Mathematical operations
base_amount = money(1000)
adjusted_amount = base_amount * multiplier
print(adjusted_amount)  # "$1,250.00"

# Convert to percentage for display if needed
efficiency_percent = efficiency.as_percentage()
print(efficiency_percent)  # "85.00%"
```

**Ratio Unit Properties:**
- Stores and displays as decimal values (not percentages)
- Used for multipliers, scaling factors, exchange rates
- Parent class for Percent unit
- No automatic percentage formatting
- Ideal for pure mathematical relationships

### Dimensionless

Represents quantities without specific units - counts, indices, pure numbers:

```python
from metricengine import dimensionless

# Quantities and counts
shares_outstanding = dimensionless(1_000_000)
employee_count = dimensionless(250)
quarter_number = dimensionless(3)

print(shares_outstanding)  # "1,000,000.00"
print(employee_count)      # "250.00"
print(quarter_number)      # "3.00"

# Pure mathematical operations
revenue_per_employee = money(500_000) / employee_count
print(revenue_per_employee)  # "$2,000.00" (Money ÷ Dimensionless = Money)

# Scaling operations
total_compensation = money(75_000) * employee_count
print(total_compensation)  # "$18,750,000.00"
```

**Dimensionless Unit Properties:**
- No specific semantic meaning - pure quantities
- Acts as mathematical "unit-less" multiplier
- Used for counts, indices, scaling factors
- Default fallback unit for operations
- Preserves other units in multiplication/division

## Unit Algebra and Type Safety

Metric Engine implements sophisticated unit algebra that prevents meaningless operations while enabling valid financial mathematics:

### Addition and Subtraction Rules

```python
from metricengine import money, percent, ratio, dimensionless

# Valid same-unit operations
revenue_q1 = money(100_000)
revenue_q2 = money(120_000)
total_revenue = revenue_q1 + revenue_q2  # ✓ Money + Money = Money

# Valid ratio/percent combinations
base_rate = ratio(0.05)
adjustment = percent(2, input="percent")  # 2% -> 0.02
combined_rate = base_rate + adjustment    # ✓ Ratio + Percent = Ratio (both are ratioish)

# Invalid cross-unit operations
try:
    invalid = revenue_q1 + base_rate      # Money + Ratio = None (invalid)
    print(f"Invalid result: {invalid.is_none()}")  # True
except:
    print("Operation blocked by type system")

# Dimensionless operations
count_a = dimensionless(100)
count_b = dimensionless(50)
total_count = count_a + count_b          # ✓ Dimensionless + Dimensionless = Dimensionless
```

### Multiplication Rules

```python
# Money multiplication rules
principal = money(10_000)
interest_rate = percent(5, input="percent")
multiplier = ratio(1.25)
years = dimensionless(3)

# Valid multiplications
interest = principal * interest_rate     # ✓ Money × Percent = Money
scaled_amount = principal * multiplier   # ✓ Money × Ratio = Money
compound_growth = principal * years      # ✓ Money × Dimensionless = Money

# Invalid multiplications
try:
    invalid = principal * money(5000)    # Money × Money = None (invalid - no unit²)
    print(f"Invalid: {invalid.is_none()}")
except:
    print("Invalid operation blocked")

# Ratio multiplication
efficiency = ratio(0.9)
utilization = percent(80, input="percent")
combined_factor = efficiency * utilization  # ✓ Ratio × Percent = Ratio
```

### Division Rules

```python
# Money division rules
total_revenue = money(1_000_000)
total_costs = money(750_000)
employee_count = dimensionless(100)

# Valid divisions
profit_margin = total_revenue / total_costs    # ✓ Money ÷ Money = Ratio
revenue_per_employee = total_revenue / employee_count  # ✓ Money ÷ Dimensionless = Money

# Ratio divisions
rate_a = percent(10, input="percent")
rate_b = percent(5, input="percent")
rate_ratio = rate_a / rate_b              # ✓ Percent ÷ Percent = Ratio

# Invalid divisions
try:
    invalid = rate_a / total_revenue      # Percent ÷ Money = None (invalid)
    print(f"Invalid: {invalid.is_none()}")
except:
    print("Invalid operation blocked")
```

## Unit Conversion and Display

### Automatic Unit Inference

Financial values automatically determine appropriate result units:

```python
# Result units follow mathematical logic
revenue = money(100_000)
margin_ratio = ratio(0.15)
margin_percent = percent(15, input="percent")

# Both produce the same result (Money), different input representations
profit_from_ratio = revenue * margin_ratio    # Money × Ratio = Money
profit_from_percent = revenue * margin_percent # Money × Percent = Money

assert profit_from_ratio.as_decimal() == profit_from_percent.as_decimal()  # Same value
assert profit_from_ratio.unit == profit_from_percent.unit  # Same unit (Money)
```

### Unit Conversion Methods

Convert between related unit types when semantically appropriate:

```python
# Ratio ↔ Percentage conversion
efficiency_ratio = ratio(0.85)
efficiency_percent = efficiency_ratio.as_percentage()

print(efficiency_ratio)    # "0.85"
print(efficiency_percent)  # "85.00%"

# Back to ratio
converted_back = efficiency_percent.ratio()
print(converted_back)      # "0.85"

# Maintain mathematical equivalence
revenue = money(1000)
result1 = revenue * efficiency_ratio
result2 = revenue * efficiency_percent
assert result1.as_decimal() == result2.as_decimal()  # Same mathematical result
```

### Policy-Aware Unit Formatting

Units respect policy settings for consistent display:

```python
from metricengine import Policy

# Currency-specific formatting
usd_policy = Policy(currency_symbol="$", currency_position="prefix")
eur_policy = Policy(currency_symbol="€", currency_position="suffix")

amount = 1234.56

usd_amount = money(amount, policy=usd_policy)
eur_amount = money(amount, policy=eur_policy)

print(usd_amount)  # "$1,234.56"
print(eur_amount)  # "1,234.56€"

# Percentage formatting
percent_policy = Policy(decimal_places=1, percent_display="percent")
ratio_policy = Policy(decimal_places=3, percent_display="ratio")

rate_value = 0.155

rate_as_percent = percent(rate_value, input="ratio", policy=percent_policy)
rate_as_ratio = ratio(rate_value, policy=ratio_policy)

print(rate_as_percent)  # "15.5%"
print(rate_as_ratio)    # "0.155"
```

## Real-World Applications

### Financial Statement Analysis

```python
# Income statement calculations with proper units
revenue = money(1_000_000)
cost_of_goods_sold = money(600_000)
operating_expenses = money(250_000)

# Financial calculations with type safety
gross_profit = revenue - cost_of_goods_sold        # Money - Money = Money
operating_income = gross_profit - operating_expenses # Money - Money = Money

# Ratio calculations
gross_margin = (gross_profit / revenue).as_percentage()     # (Money ÷ Money).as_percentage() = Percent
operating_margin = (operating_income / revenue).as_percentage()  # Same pattern

print(f"Revenue: {revenue}")                # "$1,000,000.00"
print(f"Gross Profit: {gross_profit}")     # "$400,000.00"
print(f"Operating Income: {operating_income}")  # "$150,000.00"
print(f"Gross Margin: {gross_margin}")     # "40.00%"
print(f"Operating Margin: {operating_margin}")  # "15.00%"
```

### Portfolio Analysis

```python
# Portfolio performance with mixed units
initial_value = money(100_000)
final_value = money(125_000)
time_period = dimensionless(2)  # 2 years

# Calculate returns with proper unit handling
absolute_return = final_value - initial_value     # Money - Money = Money
return_ratio = final_value / initial_value        # Money ÷ Money = Ratio
return_percent = (return_ratio - ratio(1)).as_percentage()  # (Ratio - Ratio).as_percentage() = Percent

# Annualized calculations
annualized_ratio = return_ratio ** (dimensionless(1) / time_period)  # Ratio^(Dimensionless÷Dimensionless) = Ratio
annualized_percent = (annualized_ratio - ratio(1)).as_percentage()

print(f"Initial Value: {initial_value}")       # "$100,000.00"
print(f"Final Value: {final_value}")           # "$125,000.00"
print(f"Absolute Return: {absolute_return}")   # "$25,000.00"
print(f"Total Return: {return_percent}")       # "25.00%"
print(f"Annualized Return: {annualized_percent}") # "11.80%"
```

### Pricing and Margin Analysis

```python
# Product pricing with unit validation
cost_per_unit = money(50.00)
target_margin = percent(40, input="percent")  # 40% margin
markup_multiplier = ratio(1) / (ratio(1) - target_margin.ratio())

# Calculate selling price
selling_price = cost_per_unit * markup_multiplier

# Validate the margin
actual_margin = ((selling_price - cost_per_unit) / selling_price).as_percentage()

print(f"Cost per Unit: {cost_per_unit}")       # "$50.00"
print(f"Target Margin: {target_margin}")       # "40.00%"
print(f"Markup Multiplier: {markup_multiplier}") # "1.67"
print(f"Selling Price: {selling_price}")       # "$83.33"
print(f"Actual Margin: {actual_margin}")       # "40.00%"

# Volume calculations
units_sold = dimensionless(1000)
total_revenue = selling_price * units_sold      # Money × Dimensionless = Money
total_cost = cost_per_unit * units_sold         # Money × Dimensionless = Money
total_profit = total_revenue - total_cost       # Money - Money = Money

print(f"Units Sold: {units_sold}")             # "1,000.00"
print(f"Total Revenue: {total_revenue}")       # "$83,333.33"
print(f"Total Profit: {total_profit}")         # "$33,333.33"
```

### Multi-Currency Operations

```python
# Currency operations with exchange rates
usd_amount = money(1000, policy=Policy(currency_symbol="$"))
eur_usd_rate = ratio(1.18)  # 1 EUR = 1.18 USD

# Convert currencies using ratios
eur_amount = usd_amount / eur_usd_rate
eur_amount = eur_amount.with_policy(Policy(currency_symbol="€", currency_position="suffix"))

print(f"USD Amount: {usd_amount}")    # "$1,000.00"
print(f"EUR/USD Rate: {eur_usd_rate}") # "1.18"
print(f"EUR Amount: {eur_amount}")     # "847.46€"

# Validate round-trip conversion
converted_back = eur_amount * eur_usd_rate
converted_back = converted_back.with_policy(Policy(currency_symbol="$"))
print(f"Converted Back: {converted_back}")  # "$1,000.00" (approximately)
```

## Advanced Unit Patterns

### Custom Unit Semantics

While Metric Engine provides core units, you can create semantic meaning through careful unit selection:

```python
# Use Dimensionless for different semantic categories
shares_outstanding = dimensionless(1_000_000)  # Share count
days_in_period = dimensionless(365)            # Time periods
basis_points = dimensionless(100)              # 100 basis points = 1%

# Convert basis points to percentage
bps_to_percent = basis_points / dimensionless(10_000)  # 100/10000 = 0.01
interest_rate = bps_to_percent.as_percentage()
print(interest_rate)  # "1.00%"

# Market value calculations
share_price = money(45.50)
market_value = share_price * shares_outstanding
print(f"Market Value: {market_value}")  # "$45,500,000.00"
```

### Unit-Safe Financial Formulas

```python
def calculate_compound_interest(
    principal: money,
    annual_rate: percent,
    years: dimensionless,
    compounds_per_year: dimensionless = None
) -> money:
    """Calculate compound interest with unit validation."""

    if compounds_per_year is None:
        compounds_per_year = dimensionless(1)  # Annual compounding

    # Convert percentage to ratio for calculation
    rate = annual_rate.ratio()

    # Compound interest formula: A = P(1 + r/n)^(nt)
    rate_per_period = rate / compounds_per_year
    total_periods = compounds_per_year * years

    # (1 + rate_per_period) is dimensionless, so we can raise to a power
    compound_factor = (ratio(1) + rate_per_period) ** total_periods

    return principal * compound_factor

# Example usage
initial_investment = money(10_000)
annual_rate = percent(8, input="percent")  # 8%
investment_years = dimensionless(10)
quarterly_compounding = dimensionless(4)

final_amount = calculate_compound_interest(
    initial_investment,
    annual_rate,
    investment_years,
    quarterly_compounding
)

print(f"Initial Investment: {initial_investment}")    # "$10,000.00"
print(f"Annual Rate: {annual_rate}")                  # "8.00%"
print(f"Years: {investment_years}")                   # "10.00"
print(f"Final Amount: {final_amount}")                # "$22,080.40"
```

### Error Prevention Through Units

```python
def calculate_break_even_analysis(
    fixed_costs: money,
    variable_cost_per_unit: money,
    selling_price_per_unit: money
) -> dimensionless:
    """Calculate break-even units with type safety."""

    # Unit algebra prevents errors
    contribution_margin = selling_price_per_unit - variable_cost_per_unit  # Money - Money = Money

    # Break-even formula: Fixed Costs ÷ Contribution Margin per Unit
    break_even_units = fixed_costs / contribution_margin  # Money ÷ Money = Dimensionless (units)

    return break_even_units

# Example with type validation
monthly_fixed_costs = money(50_000)
variable_cost = money(25.00)
selling_price = money(45.00)

break_even = calculate_break_even_analysis(monthly_fixed_costs, variable_cost, selling_price)
print(f"Break-even Units: {break_even}")  # "2,500.00"

# Validation calculations
total_contribution = break_even * (selling_price - variable_cost)  # Dimensionless × Money = Money
print(f"Total Contribution at Break-even: {total_contribution}")   # "$50,000.00"
```

## Best Practices

### 1. Choose Appropriate Units for Business Context

```python
# Good: Units match business semantics
profit_margin = percent(15, input="percent")        # Display as percentage
exchange_rate = ratio(1.18)                         # Display as ratio
revenue = money(100_000)                            # Currency amount
employee_count = dimensionless(50)                  # Pure quantity

# Less clear: Units don't match semantics
# margin_as_ratio = ratio(0.15)                    # Confusing - is this 15% or 0.15%?
# count_as_money = money(50)                        # Nonsensical - employees aren't currency
```

### 2. Use Type Hints for Clarity

```python
from metricengine import money, percent, ratio, dimensionless, MoneyFV, PercentFV

def calculate_tax_impact(
    gross_income: MoneyFV,
    tax_rate: PercentFV,
    deduction: MoneyFV
) -> tuple[MoneyFV, MoneyFV]:
    """Calculate tax with clear type signatures."""
    taxable_income = gross_income - deduction
    tax_amount = taxable_income * tax_rate
    net_income = taxable_income - tax_amount

    return tax_amount, net_income
```

### 3. Validate Unit Compatibility

```python
def safe_financial_calculation(*values):
    """Safely handle mixed unit operations."""
    result = values[0]

    for value in values[1:]:
        operation_result = result + value
        if operation_result.is_none():
            print(f"Warning: Incompatible units {result.unit} and {value.unit}")
            continue
        result = operation_result

    return result

# Example usage
mixed_values = [
    money(1000),
    money(500),
    # percent(10, input="percent"),  # Would trigger warning
    # ratio(0.15),                   # Would trigger warning
]

total = safe_financial_calculation(*mixed_values)
print(f"Safe Total: {total}")  # "$1,500.00"
```

### 4. Document Unit Expectations

```python
class FinancialMetrics:
    """Financial metrics calculator with documented unit requirements.

    All monetary amounts should use Money units.
    All rates and percentages should use Percent units.
    All ratios and multipliers should use Ratio units.
    All counts and quantities should use Dimensionless units.
    """

    def calculate_roe(
        self,
        net_income: MoneyFV,      # Annual net income in Money units
        equity: MoneyFV,          # Total shareholder equity in Money units
    ) -> PercentFV:
        """Calculate Return on Equity as a percentage.

        Returns: ROE as Percent unit (e.g., "15.5%" for 15.5% ROE)
        """
        roe_ratio = net_income / equity  # Money ÷ Money = Ratio
        return roe_ratio.as_percentage() # Convert to Percent for display

    def calculate_debt_to_equity(
        self,
        total_debt: MoneyFV,      # Total debt in Money units
        total_equity: MoneyFV,    # Total equity in Money units
    ) -> ratio:
        """Calculate Debt-to-Equity ratio.

        Returns: D/E ratio as Ratio unit (e.g., "1.25" for 1.25:1 ratio)
        """
        return total_debt / total_equity  # Money ÷ Money = Ratio
```

Metric Engine's unit system provides robust type safety and semantic clarity for financial calculations. By encoding business meaning into the type system, units help prevent errors, improve code readability, and ensure mathematical correctness in financial applications.
