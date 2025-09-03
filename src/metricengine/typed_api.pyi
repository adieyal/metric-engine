# Auto-generated — DO NOT EDIT.
from collections.abc import Sequence
from decimal import Decimal
from types import NoneType
from typing import Any, Literal, Protocol, SupportsFloat, TypeVar, Union, overload

from metricengine import Dimensionless, Money, Percent, Ratio, Unit
from metricengine import FinancialValue as FV

U = TypeVar("U", bound=Unit)

CalcName = Literal[
    "average_inventory",
    "average_value",
    "beverage_cost_percentage",
    "beverage_cost_ratio",
    "break_even_point",
    "cap_percentage",
    "cogs",
    "cogs_percentage",
    "cogs_ratio",
    "compound_growth_rate",
    "compound_growth_rate_percent",
    "contribution_margin",
    "contribution_margin_ratio",
    "contribution_margin_ratio_raw",
    "cost_per_unit",
    "cost_percent",
    "cost_percent_ex_tax",
    "cost_percentage_with_tax",
    "cost_ratio",
    "cost_ratio_ex_tax",
    "cost_ratio_with_tax",
    "delivery_fee_amount",
    "delivery_sales_net",
    "discount_percentage",
    "discount_ratio",
    "ebitda_margin",
    "ebitda_margin_ratio",
    "fnb_cost",
    "fnb_sales",
    "food_cost_percentage",
    "food_cost_ratio",
    "gross_margin_percentage",
    "gross_margin_percentage_ex_tax",
    "gross_margin_ratio",
    "gross_margin_ratio_ex_tax",
    "gross_profit",
    "gross_profit_ex_tax",
    "inventory_turnover",
    "markup_percentage",
    "markup_ratio",
    "net_margin_percentage",
    "net_margin_ratio",
    "net_margin_with_tax",
    "net_margin_with_tax_ratio",
    "net_profit",
    "net_profit_with_tax",
    "operating_margin",
    "operating_margin_ratio",
    "original_delivery_sales",
    "percentage_change",
    "percentage_change_ratio",
    "percentage_of_total",
    "percentage_to_ratio",
    "price_ex_tax",
    "profit_per_unit",
    "ratio",
    "ratio_to_percentage",
    "revenue_per_unit",
    "roi",
    "roi_ratio",
    "sales_ex_tax",
    "sales_with_tax",
    "simple_growth_rate",
    "tax_amount",
    "total_cost",
    "variance_amount",
    "variance_percentage",
    "variance_percentage_from_components",
    "variance_ratio",
    "variance_ratio_from_components",
    "weighted_average",
]

class Calc_average_inventory(Protocol):
    """\
    Average inventory = (opening_inventory + closing_inventory) / 2
    """
    def __call__(
        self, opening_inventory: FV[Money], closing_inventory: FV[Money]
    ) -> FV[Money]: ...

class Calc_average_value(Protocol):
    """\
    Arithmetic mean of a sequence.

    Behavior:
      - Uses SKIP mode: None items are excluded from both sum and count.
      - Empty or all-None → returns None.
      - Result unit follows the first non-None item's unit (else Dimensionless).
    """
    def __call__(
        self,
        values: Sequence[
            Union[int, float, str, Decimal, SupportsFloat, NoneType, FV, FV[U]]
        ],
    ) -> FV[U]: ...

class Calc_beverage_cost_percentage(Protocol):
    """\
    Beverage cost as a percent (e.g., 0.20 -> '20%').
    """
    def __call__(self, beverage_cost_ratio: FV[Ratio]) -> FV[Percent]: ...

class Calc_beverage_cost_ratio(Protocol):
    """\
    Beverage cost ratio = beverage_cost / beverage_sales_ex_tax
    """
    def __call__(
        self, beverage_cost: FV[Money], beverage_sales_ex_tax: FV[Money]
    ) -> FV[Ratio]: ...

class Calc_break_even_point(Protocol):
    """\
    Break-even point (units) = fixed_costs / (price_per_unit - variable_cost_per_unit)

    Returns a Dimensionless count of units (not a ratio).
    """
    def __call__(
        self,
        fixed_costs: FV[Money],
        price_per_unit: FV[Money],
        variable_cost_per_unit: FV[Money],
    ) -> FV[Dimensionless]: ...

class Calc_cap_percentage(Protocol):
    """\
    Cap a percentage at a maximum value.

    Returns None if either input is None.
    """
    def __call__(
        self, percentage: FV[Percent], max_percentage: FV[Percent]
    ) -> FV[Percent]: ...

class Calc_cogs(Protocol):
    """\
    Calculate Cost of Goods Sold (COGS) using the standard inventory formula.

    COGS represents the direct costs attributable to the production of goods sold
    by a company. This includes the cost of materials and labor directly used to
    create the product, but excludes indirect expenses such as distribution costs
    and sales force costs.

    Formula:
        COGS = Opening Inventory + Purchases - Closing Inventory

    Where:
        - Opening Inventory: Value of inventory at the beginning of the period
        - Purchases: Cost of additional inventory purchased during the period
        - Closing Inventory: Value of inventory at the end of the period

    Args:
        opening_inventory: FV[Money] - The monetary value of inventory at the
            start of the accounting period. Must be non-negative in most cases.
        purchases: FV[Money] - The total cost of inventory purchased during
            the period, including freight and other direct costs.
        closing_inventory: FV[Money] - The monetary value of inventory remaining
            at the end of the accounting period.

    Returns:
        FV[Money] - The calculated cost of goods sold. Returns FV(None) if any
            input parameter is None, following the metricengine's null propagation
            behavior.

    Policy Behavior:
        - Inherits policy from input parameters (opening_inventory, purchases,
          closing_inventory) in that order of precedence
        - Falls back to context policy or DEFAULT_POLICY if no input has a policy
        - Maintains Money unit type for proper financial calculations

    Examples:
        >>> # Basic COGS calculation
        >>> opening = FV(1000)  # $1,000 opening inventory
        >>> purchases = FV(5000)  # $5,000 in purchases
        >>> closing = FV(1500)  # $1,500 closing inventory
        >>> result = cogs(opening, purchases, closing)
        >>> result.as_decimal()  # Decimal('4500.00')

        >>> # With None values (null propagation)
        >>> result = cogs(FV(1000), FV(None), FV(1500))
        >>> result.is_none()  # True

        >>> # Using engine calculation
        >>> ctx = {
        ...     "opening_inventory": 200,
        ...     "purchases": 800,
        ...     "closing_inventory": 150
        ... }
        >>> result = engine.calculate("cogs", ctx)
        >>> result.as_decimal()  # Decimal('850.00')

    Business Context:
        COGS is a critical metric for:
        - Calculating gross profit (Sales - COGS)
        - Determining gross margin percentage
        - Inventory turnover analysis
        - Cost control and pricing decisions
        - Financial statement preparation (Income Statement)

    Notes:
        - This calculation assumes FIFO (First In, First Out) inventory method
        - Does not include indirect costs like overhead or administrative expenses
        - Negative COGS values are possible but may indicate data quality issues
        - All inputs must be in the same currency for meaningful results
        - The function handles None values gracefully by returning FV(None)

    See Also:
        - cogs_ratio: COGS as a ratio of sales
        - cogs_percentage: COGS as a percentage of sales
        - inventory_turnover: How efficiently inventory is being used
        - average_inventory: Average inventory level calculation
    """
    def __call__(
        self,
        opening_inventory: FV[Money],
        purchases: FV[Money],
        closing_inventory: FV[Money],
    ) -> FV[Money]: ...

class Calc_cogs_percentage(Protocol):
    """\
    COGS as a percent (e.g., 0.48 -> '48%').
    """
    def __call__(self, cogs_ratio: FV[Ratio]) -> FV[Percent]: ...

class Calc_cogs_ratio(Protocol):
    """\
    COGS ratio = cogs / sales
    """
    def __call__(self, cogs: FV[Money], sales: FV[Money]) -> FV[Ratio]: ...

class Calc_compound_growth_rate(Protocol):
    """\
    Compound annual growth rate (CAGR) as a ratio (0..1):

        CAGR = exp( ln(final / initial) / periods ) - 1

    Notes:
        - Requires strictly positive initial, final, and periods.
        - Returns None on invalid inputs unless policy.arithmetic_strict, in which case raises.
    """
    def __call__(
        self, initial_value: FV[U], final_value: FV[U], periods: FV[Dimensionless]
    ) -> FV[Ratio]: ...

class Calc_compound_growth_rate_percent(Protocol):
    """\
    CAGR as a percent (e.g., 0.10 -> '10%').
    """
    def __call__(self, compound_growth_rate: FV[Ratio]) -> FV[Percent]: ...

class Calc_contribution_margin(Protocol):
    """\
    Contribution margin = revenue - variable_costs
    """
    def __call__(self, revenue: FV[Money], variable_costs: FV[Money]) -> FV[Money]: ...

class Calc_contribution_margin_ratio(Protocol):
    """\
    Contribution margin ratio as percent.
    """
    def __call__(self, contribution_margin_ratio_raw: FV[Ratio]) -> FV[Percent]: ...

class Calc_contribution_margin_ratio_raw(Protocol):
    """\
    Contribution margin ratio = contribution_margin / revenue
    """
    def __call__(
        self, contribution_margin: FV[Money], revenue: FV[Money]
    ) -> FV[Ratio]: ...

class Calc_cost_per_unit(Protocol):
    """\
    Cost per unit = total_cost / units
    """
    def __call__(
        self, total_cost: FV[Money], units: FV[Dimensionless]
    ) -> FV[Money]: ...

class Calc_cost_percent(Protocol):
    """\
    Cost as percent.
    """
    def __call__(self, cost_ratio: FV[Ratio]) -> FV[Percent]: ...

class Calc_cost_percent_ex_tax(Protocol):
    """\
    Cost percent (ex tax).
    """
    def __call__(self, cost_ratio_ex_tax: FV[Ratio]) -> FV[Percent]: ...

class Calc_cost_percentage_with_tax(Protocol):
    """\
    Cost percentage with tax.
    """
    def __call__(self, cost_ratio_with_tax: FV[Ratio]) -> FV[Percent]: ...

class Calc_cost_ratio(Protocol):
    """\
    Cost ratio = cost / sales
    """
    def __call__(self, cost: FV[Money], sales: FV[Money]) -> FV[Ratio]: ...

class Calc_cost_ratio_ex_tax(Protocol):
    """\
    Cost ratio (ex tax) = cost / sales_ex_tax
    """
    def __call__(self, cost: FV[Money], sales_ex_tax: FV[Money]) -> FV[Ratio]: ...

class Calc_cost_ratio_with_tax(Protocol):
    """\
    Cost ratio with tax info:
      denominator is sales ex tax, i.e. cost / (sales / (1 + tax_rate))
    """
    def __call__(
        self, cost: FV[Money], sales: FV[Money], tax_rate: FV[Percent]
    ) -> FV[Ratio]: ...

class Calc_delivery_fee_amount(Protocol):
    """\
    Delivery fee amount = delivery_sales * delivery_fee_percentage
    """
    def __call__(
        self, delivery_sales: FV[Money], delivery_fee_percentage: FV[Percent]
    ) -> FV[Money]: ...

class Calc_delivery_sales_net(Protocol):
    """\
    Net delivery sales = delivery_sales * (1 - delivery_fee_percentage)
    """
    def __call__(
        self, delivery_sales: FV[Money], delivery_fee_percentage: FV[Percent]
    ) -> FV[Money]: ...

class Calc_discount_percentage(Protocol):
    """\
    Discount as percent (e.g., 0.20 -> '20%').
    """
    def __call__(self, discount_ratio: FV[Ratio]) -> FV[Percent]: ...

class Calc_discount_ratio(Protocol):
    """\
    Discount ratio = (original_price - discounted_price) / original_price
    """
    def __call__(
        self, original_price: FV[Money], discounted_price: FV[Money]
    ) -> FV[Ratio]: ...

class Calc_ebitda_margin(Protocol):
    """\
    EBITDA margin as percent.
    """
    def __call__(self, ebitda_margin_ratio: FV[Ratio]) -> FV[Percent]: ...

class Calc_ebitda_margin_ratio(Protocol):
    """\
    EBITDA margin ratio = ebitda / revenue
    """
    def __call__(self, ebitda: FV[Money], revenue: FV[Money]) -> FV[Ratio]: ...

class Calc_fnb_cost(Protocol):
    """\
    F&B cost = food_cost + beverage_cost
    """
    def __call__(self, food_cost: FV[Money], beverage_cost: FV[Money]) -> FV[Money]: ...

class Calc_fnb_sales(Protocol):
    """\
    F&B sales = food_sales + beverage_sales
    """
    def __call__(
        self, food_sales: FV[Money], beverage_sales: FV[Money]
    ) -> FV[Money]: ...

class Calc_food_cost_percentage(Protocol):
    """\
    Food cost as a percent (e.g., 0.30 -> '30%').
    """
    def __call__(self, food_cost_ratio: FV[Ratio]) -> FV[Percent]: ...

class Calc_food_cost_ratio(Protocol):
    """\
    Food cost ratio = food_cost / food_sales_ex_tax
    """
    def __call__(
        self, food_cost: FV[Money], food_sales_ex_tax: FV[Money]
    ) -> FV[Ratio]: ...

class Calc_gross_margin_percentage(Protocol):
    """\
    Gross margin as percent (e.g., 0.35 -> '35%').
    """
    def __call__(self, gross_margin_ratio: FV[Ratio]) -> FV[Percent]: ...

class Calc_gross_margin_percentage_ex_tax(Protocol):
    """\
    Gross margin (ex tax) as percent.
    """
    def __call__(self, gross_margin_ratio_ex_tax: FV[Ratio]) -> FV[Percent]: ...

class Calc_gross_margin_ratio(Protocol):
    """\
    Gross margin ratio = gross_profit / sales
    """
    def __call__(self, gross_profit: FV[Money], sales: FV[Money]) -> FV[Ratio]: ...

class Calc_gross_margin_ratio_ex_tax(Protocol):
    """\
    Gross margin ratio (ex tax) = gross_profit_ex_tax / sales_ex_tax
    """
    def __call__(
        self, gross_profit_ex_tax: FV[Money], sales_ex_tax: FV[Money]
    ) -> FV[Ratio]: ...

class Calc_gross_profit(Protocol):
    """\
    Gross profit = sales - cost
    """
    def __call__(self, sales: FV[Money], cost: FV[Money]) -> FV[Money]: ...

class Calc_gross_profit_ex_tax(Protocol):
    """\
    Gross profit (ex tax) = sales_ex_tax - cost
    """
    def __call__(self, sales_ex_tax: FV[Money], cost: FV[Money]) -> FV[Money]: ...

class Calc_inventory_turnover(Protocol):
    """\
    Inventory turnover = cogs / average_inventory
    """
    def __call__(self, cogs: FV[Money], average_inventory: FV[Money]) -> FV[Ratio]: ...

class Calc_markup_percentage(Protocol):
    """\
    Markup as percent (e.g., 0.25 -> '25%').
    """
    def __call__(self, markup_ratio: FV[Ratio]) -> FV[Percent]: ...

class Calc_markup_ratio(Protocol):
    """\
    Markup ratio = (selling_price - cost) / cost
    """
    def __call__(self, cost: FV[Money], selling_price: FV[Money]) -> FV[Ratio]: ...

class Calc_net_margin_percentage(Protocol):
    """\
    Net margin as percent.
    """
    def __call__(self, net_margin_ratio: FV[Ratio]) -> FV[Percent]: ...

class Calc_net_margin_ratio(Protocol):
    """\
    Net margin ratio = net_profit / revenue
    """
    def __call__(self, net_profit: FV[Money], revenue: FV[Money]) -> FV[Ratio]: ...

class Calc_net_margin_with_tax(Protocol):
    """\
    Net margin with tax as percent.
    """
    def __call__(self, net_margin_with_tax_ratio: FV[Ratio]) -> FV[Percent]: ...

class Calc_net_margin_with_tax_ratio(Protocol):
    """\
    Net margin (tax-adjusted) ratio = net_profit_with_tax / sales_ex_tax
    """
    def __call__(
        self, net_profit_with_tax: FV[Money], sales_ex_tax: FV[Money]
    ) -> FV[Ratio]: ...

class Calc_net_profit(Protocol):
    """\
    Net profit = revenue - total_costs
    """
    def __call__(self, revenue: FV[Money], total_costs: FV[Money]) -> FV[Money]: ...

class Calc_net_profit_with_tax(Protocol):
    """\
    Net profit (tax-adjusted) = (sales / (1 + tax_rate)) - cost
    """
    def __call__(
        self, sales: FV[Money], cost: FV[Money], tax_rate: FV[Percent]
    ) -> FV[Money]: ...

class Calc_operating_margin(Protocol):
    """\
    Operating margin as percent.
    """
    def __call__(self, operating_margin_ratio: FV[Ratio]) -> FV[Percent]: ...

class Calc_operating_margin_ratio(Protocol):
    """\
    Operating margin ratio = operating_income / revenue
    """
    def __call__(
        self, operating_income: FV[Money], revenue: FV[Money]
    ) -> FV[Ratio]: ...

class Calc_original_delivery_sales(Protocol):
    """\
    Original delivery sales = delivery_sales_net / (1 - delivery_fee_percentage)
    """
    def __call__(
        self, delivery_sales_net: FV[Money], delivery_fee_percentage: FV[Percent]
    ) -> FV[Money]: ...

class Calc_percentage_change(Protocol):
    """\
    Percentage change as percent (e.g., 0.20 -> '20%').
    """
    def __call__(self, percentage_change_ratio: FV[Ratio]) -> FV[Percent]: ...

class Calc_percentage_change_ratio(Protocol):
    """\
    Percentage change (ratio) = (new_value - old_value) / old_value
    """
    def __call__(self, old_value: FV[U], new_value: FV[U]) -> FV[Ratio]: ...

class Calc_percentage_of_total(Protocol):
    """\
    Percentage of total = (part / total), returned as Percent.

    Business rule: if total <= 0 → return 0% (not None).
    """
    def __call__(self, part: FV[U], total: FV[U]) -> FV[Percent]: ...

class Calc_percentage_to_ratio(Protocol):
    """\
    Convert a percent value to a ratio (e.g., 25% -> 0.25).
    """
    def __call__(self, percentage: FV[Percent]) -> FV[Ratio]: ...

class Calc_price_ex_tax(Protocol):
    """\
    Price excluding tax = price_inc_tax / (1 + tax_rate)
    """
    def __call__(
        self, price_inc_tax: FV[Money], tax_rate: FV[Percent]
    ) -> FV[Money]: ...

class Calc_profit_per_unit(Protocol):
    """\
    Profit per unit = total_profit / units_sold
    """
    def __call__(
        self, total_profit: FV[Money], units_sold: FV[Dimensionless]
    ) -> FV[Money]: ...

class Calc_ratio(Protocol):
    """\
    Simple ratio = numerator / denominator.

    Default behavior:
      - If denominator == 0 → return None (unless policy.arithmetic_strict, then raise).
      - None inputs propagate to None.
    """
    def __call__(self, numerator: FV[U], denominator: FV[U]) -> FV[Ratio]: ...

class Calc_ratio_to_percentage(Protocol):
    """\
    Convert a ratio (0..1) to percent representation.
    """
    def __call__(self, ratio: FV[Ratio]) -> FV[Percent]: ...

class Calc_revenue_per_unit(Protocol):
    """\
    Revenue per unit = total_revenue / units_sold
    """
    def __call__(
        self, total_revenue: FV[Money], units_sold: FV[Dimensionless]
    ) -> FV[Money]: ...

class Calc_roi(Protocol):
    """\
    ROI as percent.
    """
    def __call__(self, roi_ratio: FV[Ratio]) -> FV[Percent]: ...

class Calc_roi_ratio(Protocol):
    """\
    ROI ratio = gain_from_investment / cost_of_investment
    """
    def __call__(
        self, gain_from_investment: FV[Money], cost_of_investment: FV[Money]
    ) -> FV[Ratio]: ...

class Calc_sales_ex_tax(Protocol):
    """\
    Sales excluding tax = sales / (1 + tax_rate)
    """
    def __call__(self, sales: FV[Money], tax_rate: FV[Percent]) -> FV[Money]: ...

class Calc_sales_with_tax(Protocol):
    """\
    Sales including tax = sales_ex_tax * (1 + tax_rate)
    """
    def __call__(self, sales_ex_tax: FV[Money], tax_rate: FV[Percent]) -> FV[Money]: ...

class Calc_simple_growth_rate(Protocol):
    """\
    Simple growth rate as a ratio: (final - initial) / initial.

    Returns:
        FV[Ratio] in 0..1 (can be negative if shrinking), or None if inputs invalid.
    """
    def __call__(self, initial_value: FV[U], final_value: FV[U]) -> FV[Ratio]: ...

class Calc_tax_amount(Protocol):
    """\
    Tax amount = sales - (sales / (1 + tax_rate))
    """
    def __call__(self, sales: FV[Money], tax_rate: FV[Percent]) -> FV[Money]: ...

class Calc_total_cost(Protocol):
    """\
    Total cost = unit_cost * quantity
    """
    def __call__(
        self, unit_cost: FV[Money], quantity: FV[Dimensionless]
    ) -> FV[Money]: ...

class Calc_variance_amount(Protocol):
    """\
    Variance amount = actual - expected
    """
    def __call__(self, actual: FV[U], expected: FV[U]) -> FV[U]: ...

class Calc_variance_percentage(Protocol):
    """\
    Variance as percent (positive = over, negative = under).
    """
    def __call__(self, variance_ratio: FV[Ratio]) -> FV[Percent]: ...

class Calc_variance_percentage_from_components(Protocol):
    """\
    Variance (from components) as percent.
    """
    def __call__(self, vrc: FV[Ratio]) -> FV[Percent]: ...

class Calc_variance_ratio(Protocol):
    """\
    Variance ratio = (actual - expected) / expected
    """
    def __call__(self, actual: FV[U], expected: FV[U]) -> FV[Ratio]: ...

class Calc_variance_ratio_from_components(Protocol):
    """\
    Variance ratio from inventory components:
      expected_closing = opening + purchases - sold
      variance_ratio   = (actual_closing - expected_closing) / expected_closing
    """
    def __call__(
        self,
        actual_closing: FV[Money],
        opening: FV[Money],
        purchases: FV[Money],
        sold: FV[Money],
    ) -> FV[Ratio]: ...

class Calc_weighted_average(Protocol):
    """\
    Weighted mean of `values` with `weights`.

    Behavior:
      - Uses SKIP mode: pairs with None in either value or weight are dropped.
      - Empty input or length mismatch → returns None (business rule).
      - Result unit follows the first non-None value's unit (else Dimensionless).
    """
    def __call__(
        self,
        values: Sequence[
            Union[int, float, str, Decimal, SupportsFloat, NoneType, FV, FV[U]]
        ],
        weights: Sequence[
            Union[
                int, float, str, Decimal, SupportsFloat, NoneType, FV, FV[Dimensionless]
            ]
        ],
    ) -> FV[U]: ...

@overload
def get_calc(name: Literal["average_inventory"]) -> Calc_average_inventory: ...
@overload
def get_calc(name: Literal["average_value"]) -> Calc_average_value: ...
@overload
def get_calc(
    name: Literal["beverage_cost_percentage"]
) -> Calc_beverage_cost_percentage: ...
@overload
def get_calc(name: Literal["beverage_cost_ratio"]) -> Calc_beverage_cost_ratio: ...
@overload
def get_calc(name: Literal["break_even_point"]) -> Calc_break_even_point: ...
@overload
def get_calc(name: Literal["cap_percentage"]) -> Calc_cap_percentage: ...
@overload
def get_calc(name: Literal["cogs"]) -> Calc_cogs: ...
@overload
def get_calc(name: Literal["cogs_percentage"]) -> Calc_cogs_percentage: ...
@overload
def get_calc(name: Literal["cogs_ratio"]) -> Calc_cogs_ratio: ...
@overload
def get_calc(name: Literal["compound_growth_rate"]) -> Calc_compound_growth_rate: ...
@overload
def get_calc(
    name: Literal["compound_growth_rate_percent"]
) -> Calc_compound_growth_rate_percent: ...
@overload
def get_calc(name: Literal["contribution_margin"]) -> Calc_contribution_margin: ...
@overload
def get_calc(
    name: Literal["contribution_margin_ratio"]
) -> Calc_contribution_margin_ratio: ...
@overload
def get_calc(
    name: Literal["contribution_margin_ratio_raw"]
) -> Calc_contribution_margin_ratio_raw: ...
@overload
def get_calc(name: Literal["cost_per_unit"]) -> Calc_cost_per_unit: ...
@overload
def get_calc(name: Literal["cost_percent"]) -> Calc_cost_percent: ...
@overload
def get_calc(name: Literal["cost_percent_ex_tax"]) -> Calc_cost_percent_ex_tax: ...
@overload
def get_calc(
    name: Literal["cost_percentage_with_tax"]
) -> Calc_cost_percentage_with_tax: ...
@overload
def get_calc(name: Literal["cost_ratio"]) -> Calc_cost_ratio: ...
@overload
def get_calc(name: Literal["cost_ratio_ex_tax"]) -> Calc_cost_ratio_ex_tax: ...
@overload
def get_calc(name: Literal["cost_ratio_with_tax"]) -> Calc_cost_ratio_with_tax: ...
@overload
def get_calc(name: Literal["delivery_fee_amount"]) -> Calc_delivery_fee_amount: ...
@overload
def get_calc(name: Literal["delivery_sales_net"]) -> Calc_delivery_sales_net: ...
@overload
def get_calc(name: Literal["discount_percentage"]) -> Calc_discount_percentage: ...
@overload
def get_calc(name: Literal["discount_ratio"]) -> Calc_discount_ratio: ...
@overload
def get_calc(name: Literal["ebitda_margin"]) -> Calc_ebitda_margin: ...
@overload
def get_calc(name: Literal["ebitda_margin_ratio"]) -> Calc_ebitda_margin_ratio: ...
@overload
def get_calc(name: Literal["fnb_cost"]) -> Calc_fnb_cost: ...
@overload
def get_calc(name: Literal["fnb_sales"]) -> Calc_fnb_sales: ...
@overload
def get_calc(name: Literal["food_cost_percentage"]) -> Calc_food_cost_percentage: ...
@overload
def get_calc(name: Literal["food_cost_ratio"]) -> Calc_food_cost_ratio: ...
@overload
def get_calc(
    name: Literal["gross_margin_percentage"]
) -> Calc_gross_margin_percentage: ...
@overload
def get_calc(
    name: Literal["gross_margin_percentage_ex_tax"]
) -> Calc_gross_margin_percentage_ex_tax: ...
@overload
def get_calc(name: Literal["gross_margin_ratio"]) -> Calc_gross_margin_ratio: ...
@overload
def get_calc(
    name: Literal["gross_margin_ratio_ex_tax"]
) -> Calc_gross_margin_ratio_ex_tax: ...
@overload
def get_calc(name: Literal["gross_profit"]) -> Calc_gross_profit: ...
@overload
def get_calc(name: Literal["gross_profit_ex_tax"]) -> Calc_gross_profit_ex_tax: ...
@overload
def get_calc(name: Literal["inventory_turnover"]) -> Calc_inventory_turnover: ...
@overload
def get_calc(name: Literal["markup_percentage"]) -> Calc_markup_percentage: ...
@overload
def get_calc(name: Literal["markup_ratio"]) -> Calc_markup_ratio: ...
@overload
def get_calc(name: Literal["net_margin_percentage"]) -> Calc_net_margin_percentage: ...
@overload
def get_calc(name: Literal["net_margin_ratio"]) -> Calc_net_margin_ratio: ...
@overload
def get_calc(name: Literal["net_margin_with_tax"]) -> Calc_net_margin_with_tax: ...
@overload
def get_calc(
    name: Literal["net_margin_with_tax_ratio"]
) -> Calc_net_margin_with_tax_ratio: ...
@overload
def get_calc(name: Literal["net_profit"]) -> Calc_net_profit: ...
@overload
def get_calc(name: Literal["net_profit_with_tax"]) -> Calc_net_profit_with_tax: ...
@overload
def get_calc(name: Literal["operating_margin"]) -> Calc_operating_margin: ...
@overload
def get_calc(
    name: Literal["operating_margin_ratio"]
) -> Calc_operating_margin_ratio: ...
@overload
def get_calc(
    name: Literal["original_delivery_sales"]
) -> Calc_original_delivery_sales: ...
@overload
def get_calc(name: Literal["percentage_change"]) -> Calc_percentage_change: ...
@overload
def get_calc(
    name: Literal["percentage_change_ratio"]
) -> Calc_percentage_change_ratio: ...
@overload
def get_calc(name: Literal["percentage_of_total"]) -> Calc_percentage_of_total: ...
@overload
def get_calc(name: Literal["percentage_to_ratio"]) -> Calc_percentage_to_ratio: ...
@overload
def get_calc(name: Literal["price_ex_tax"]) -> Calc_price_ex_tax: ...
@overload
def get_calc(name: Literal["profit_per_unit"]) -> Calc_profit_per_unit: ...
@overload
def get_calc(name: Literal["ratio"]) -> Calc_ratio: ...
@overload
def get_calc(name: Literal["ratio_to_percentage"]) -> Calc_ratio_to_percentage: ...
@overload
def get_calc(name: Literal["revenue_per_unit"]) -> Calc_revenue_per_unit: ...
@overload
def get_calc(name: Literal["roi"]) -> Calc_roi: ...
@overload
def get_calc(name: Literal["roi_ratio"]) -> Calc_roi_ratio: ...
@overload
def get_calc(name: Literal["sales_ex_tax"]) -> Calc_sales_ex_tax: ...
@overload
def get_calc(name: Literal["sales_with_tax"]) -> Calc_sales_with_tax: ...
@overload
def get_calc(name: Literal["simple_growth_rate"]) -> Calc_simple_growth_rate: ...
@overload
def get_calc(name: Literal["tax_amount"]) -> Calc_tax_amount: ...
@overload
def get_calc(name: Literal["total_cost"]) -> Calc_total_cost: ...
@overload
def get_calc(name: Literal["variance_amount"]) -> Calc_variance_amount: ...
@overload
def get_calc(name: Literal["variance_percentage"]) -> Calc_variance_percentage: ...
@overload
def get_calc(
    name: Literal["variance_percentage_from_components"]
) -> Calc_variance_percentage_from_components: ...
@overload
def get_calc(name: Literal["variance_ratio"]) -> Calc_variance_ratio: ...
@overload
def get_calc(
    name: Literal["variance_ratio_from_components"]
) -> Calc_variance_ratio_from_components: ...
@overload
def get_calc(name: Literal["weighted_average"]) -> Calc_weighted_average: ...
def get_calc(name: str) -> Any: ...
def calc_names() -> list[CalcName]: ...
def average_inventory(
    opening_inventory: FV[Money], closing_inventory: FV[Money]
) -> FV[Money]: ...
def average_value(
    values: Sequence[
        Union[int, float, str, Decimal, SupportsFloat, NoneType, FV, FV[U]]
    ],
) -> FV[U]: ...
def beverage_cost_percentage(beverage_cost_ratio: FV[Ratio]) -> FV[Percent]: ...
def beverage_cost_ratio(
    beverage_cost: FV[Money], beverage_sales_ex_tax: FV[Money]
) -> FV[Ratio]: ...
def break_even_point(
    fixed_costs: FV[Money], price_per_unit: FV[Money], variable_cost_per_unit: FV[Money]
) -> FV[Dimensionless]: ...
def cap_percentage(
    percentage: FV[Percent], max_percentage: FV[Percent]
) -> FV[Percent]: ...
def cogs(
    opening_inventory: FV[Money], purchases: FV[Money], closing_inventory: FV[Money]
) -> FV[Money]: ...
def cogs_percentage(cogs_ratio: FV[Ratio]) -> FV[Percent]: ...
def cogs_ratio(cogs: FV[Money], sales: FV[Money]) -> FV[Ratio]: ...
def compound_growth_rate(
    initial_value: FV[U], final_value: FV[U], periods: FV[Dimensionless]
) -> FV[Ratio]: ...
def compound_growth_rate_percent(compound_growth_rate: FV[Ratio]) -> FV[Percent]: ...
def contribution_margin(revenue: FV[Money], variable_costs: FV[Money]) -> FV[Money]: ...
def contribution_margin_ratio(
    contribution_margin_ratio_raw: FV[Ratio]
) -> FV[Percent]: ...
def contribution_margin_ratio_raw(
    contribution_margin: FV[Money], revenue: FV[Money]
) -> FV[Ratio]: ...
def cost_per_unit(total_cost: FV[Money], units: FV[Dimensionless]) -> FV[Money]: ...
def cost_percent(cost_ratio: FV[Ratio]) -> FV[Percent]: ...
def cost_percent_ex_tax(cost_ratio_ex_tax: FV[Ratio]) -> FV[Percent]: ...
def cost_percentage_with_tax(cost_ratio_with_tax: FV[Ratio]) -> FV[Percent]: ...
def cost_ratio(cost: FV[Money], sales: FV[Money]) -> FV[Ratio]: ...
def cost_ratio_ex_tax(cost: FV[Money], sales_ex_tax: FV[Money]) -> FV[Ratio]: ...
def cost_ratio_with_tax(
    cost: FV[Money], sales: FV[Money], tax_rate: FV[Percent]
) -> FV[Ratio]: ...
def delivery_fee_amount(
    delivery_sales: FV[Money], delivery_fee_percentage: FV[Percent]
) -> FV[Money]: ...
def delivery_sales_net(
    delivery_sales: FV[Money], delivery_fee_percentage: FV[Percent]
) -> FV[Money]: ...
def discount_percentage(discount_ratio: FV[Ratio]) -> FV[Percent]: ...
def discount_ratio(
    original_price: FV[Money], discounted_price: FV[Money]
) -> FV[Ratio]: ...
def ebitda_margin(ebitda_margin_ratio: FV[Ratio]) -> FV[Percent]: ...
def ebitda_margin_ratio(ebitda: FV[Money], revenue: FV[Money]) -> FV[Ratio]: ...
def fnb_cost(food_cost: FV[Money], beverage_cost: FV[Money]) -> FV[Money]: ...
def fnb_sales(food_sales: FV[Money], beverage_sales: FV[Money]) -> FV[Money]: ...
def food_cost_percentage(food_cost_ratio: FV[Ratio]) -> FV[Percent]: ...
def food_cost_ratio(
    food_cost: FV[Money], food_sales_ex_tax: FV[Money]
) -> FV[Ratio]: ...
def gross_margin_percentage(gross_margin_ratio: FV[Ratio]) -> FV[Percent]: ...
def gross_margin_percentage_ex_tax(
    gross_margin_ratio_ex_tax: FV[Ratio]
) -> FV[Percent]: ...
def gross_margin_ratio(gross_profit: FV[Money], sales: FV[Money]) -> FV[Ratio]: ...
def gross_margin_ratio_ex_tax(
    gross_profit_ex_tax: FV[Money], sales_ex_tax: FV[Money]
) -> FV[Ratio]: ...
def gross_profit(sales: FV[Money], cost: FV[Money]) -> FV[Money]: ...
def gross_profit_ex_tax(sales_ex_tax: FV[Money], cost: FV[Money]) -> FV[Money]: ...
def inventory_turnover(cogs: FV[Money], average_inventory: FV[Money]) -> FV[Ratio]: ...
def markup_percentage(markup_ratio: FV[Ratio]) -> FV[Percent]: ...
def markup_ratio(cost: FV[Money], selling_price: FV[Money]) -> FV[Ratio]: ...
def net_margin_percentage(net_margin_ratio: FV[Ratio]) -> FV[Percent]: ...
def net_margin_ratio(net_profit: FV[Money], revenue: FV[Money]) -> FV[Ratio]: ...
def net_margin_with_tax(net_margin_with_tax_ratio: FV[Ratio]) -> FV[Percent]: ...
def net_margin_with_tax_ratio(
    net_profit_with_tax: FV[Money], sales_ex_tax: FV[Money]
) -> FV[Ratio]: ...
def net_profit(revenue: FV[Money], total_costs: FV[Money]) -> FV[Money]: ...
def net_profit_with_tax(
    sales: FV[Money], cost: FV[Money], tax_rate: FV[Percent]
) -> FV[Money]: ...
def operating_margin(operating_margin_ratio: FV[Ratio]) -> FV[Percent]: ...
def operating_margin_ratio(
    operating_income: FV[Money], revenue: FV[Money]
) -> FV[Ratio]: ...
def original_delivery_sales(
    delivery_sales_net: FV[Money], delivery_fee_percentage: FV[Percent]
) -> FV[Money]: ...
def percentage_change(percentage_change_ratio: FV[Ratio]) -> FV[Percent]: ...
def percentage_change_ratio(old_value: FV[U], new_value: FV[U]) -> FV[Ratio]: ...
def percentage_of_total(part: FV[U], total: FV[U]) -> FV[Percent]: ...
def percentage_to_ratio(percentage: FV[Percent]) -> FV[Ratio]: ...
def price_ex_tax(price_inc_tax: FV[Money], tax_rate: FV[Percent]) -> FV[Money]: ...
def profit_per_unit(
    total_profit: FV[Money], units_sold: FV[Dimensionless]
) -> FV[Money]: ...
def ratio(numerator: FV[U], denominator: FV[U]) -> FV[Ratio]: ...
def ratio_to_percentage(ratio: FV[Ratio]) -> FV[Percent]: ...
def revenue_per_unit(
    total_revenue: FV[Money], units_sold: FV[Dimensionless]
) -> FV[Money]: ...
def roi(roi_ratio: FV[Ratio]) -> FV[Percent]: ...
def roi_ratio(
    gain_from_investment: FV[Money], cost_of_investment: FV[Money]
) -> FV[Ratio]: ...
def sales_ex_tax(sales: FV[Money], tax_rate: FV[Percent]) -> FV[Money]: ...
def sales_with_tax(sales_ex_tax: FV[Money], tax_rate: FV[Percent]) -> FV[Money]: ...
def simple_growth_rate(initial_value: FV[U], final_value: FV[U]) -> FV[Ratio]: ...
def tax_amount(sales: FV[Money], tax_rate: FV[Percent]) -> FV[Money]: ...
def total_cost(unit_cost: FV[Money], quantity: FV[Dimensionless]) -> FV[Money]: ...
def variance_amount(actual: FV[U], expected: FV[U]) -> FV[U]: ...
def variance_percentage(variance_ratio: FV[Ratio]) -> FV[Percent]: ...
def variance_percentage_from_components(vrc: FV[Ratio]) -> FV[Percent]: ...
def variance_ratio(actual: FV[U], expected: FV[U]) -> FV[Ratio]: ...
def variance_ratio_from_components(
    actual_closing: FV[Money], opening: FV[Money], purchases: FV[Money], sold: FV[Money]
) -> FV[Ratio]: ...
def weighted_average(
    values: Sequence[
        Union[int, float, str, Decimal, SupportsFloat, NoneType, FV, FV[U]]
    ],
    weights: Sequence[
        Union[int, float, str, Decimal, SupportsFloat, NoneType, FV, FV[Dimensionless]]
    ],
) -> FV[U]: ...
