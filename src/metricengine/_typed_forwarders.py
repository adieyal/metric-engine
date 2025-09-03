# Auto-generated — DO NOT EDIT.
from __future__ import annotations

from typing import Any

from .registry import get as _get


def average_inventory(*args: Any, **kwargs: Any):
    """\n    Average inventory = (opening_inventory + closing_inventory) / 2"""
    return _get("average_inventory")(*args, **kwargs)


def average_value(*args: Any, **kwargs: Any):
    """\n    Arithmetic mean of a sequence.

    Behavior:
      - Uses SKIP mode: None items are excluded from both sum and count.
      - Empty or all-None → returns None.
      - Result unit follows the first non-None item's unit (else Dimensionless).
    """
    return _get("average_value")(*args, **kwargs)


def beverage_cost_percentage(*args: Any, **kwargs: Any):
    """\n    Beverage cost as a percent (e.g., 0.20 -> '20%')."""
    return _get("beverage_cost_percentage")(*args, **kwargs)


def beverage_cost_ratio(*args: Any, **kwargs: Any):
    """\n    Beverage cost ratio = beverage_cost / beverage_sales_ex_tax"""
    return _get("beverage_cost_ratio")(*args, **kwargs)


def break_even_point(*args: Any, **kwargs: Any):
    """\n    Break-even point (units) = fixed_costs / (price_per_unit - variable_cost_per_unit)

    Returns a Dimensionless count of units (not a ratio).
    """
    return _get("break_even_point")(*args, **kwargs)


def cap_percentage(*args: Any, **kwargs: Any):
    """\n    Cap a percentage at a maximum value.

    Returns None if either input is None.
    """
    return _get("cap_percentage")(*args, **kwargs)


def cogs(*args: Any, **kwargs: Any):
    """\n    Calculate Cost of Goods Sold (COGS) using the standard inventory formula.

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
    return _get("cogs")(*args, **kwargs)


def cogs_percentage(*args: Any, **kwargs: Any):
    """\n    COGS as a percent (e.g., 0.48 -> '48%')."""
    return _get("cogs_percentage")(*args, **kwargs)


def cogs_ratio(*args: Any, **kwargs: Any):
    """\n    COGS ratio = cogs / sales"""
    return _get("cogs_ratio")(*args, **kwargs)


def compound_growth_rate(*args: Any, **kwargs: Any):
    """\n    Compound annual growth rate (CAGR) as a ratio (0..1):

        CAGR = exp( ln(final / initial) / periods ) - 1

    Notes:
        - Requires strictly positive initial, final, and periods.
        - Returns None on invalid inputs unless policy.arithmetic_strict, in which case raises.
    """
    return _get("compound_growth_rate")(*args, **kwargs)


def compound_growth_rate_percent(*args: Any, **kwargs: Any):
    """\n    CAGR as a percent (e.g., 0.10 -> '10%')."""
    return _get("compound_growth_rate_percent")(*args, **kwargs)


def contribution_margin(*args: Any, **kwargs: Any):
    """\n    Contribution margin = revenue - variable_costs"""
    return _get("contribution_margin")(*args, **kwargs)


def contribution_margin_ratio(*args: Any, **kwargs: Any):
    """\n    Contribution margin ratio as percent."""
    return _get("contribution_margin_ratio")(*args, **kwargs)


def contribution_margin_ratio_raw(*args: Any, **kwargs: Any):
    """\n    Contribution margin ratio = contribution_margin / revenue"""
    return _get("contribution_margin_ratio_raw")(*args, **kwargs)


def cost_per_unit(*args: Any, **kwargs: Any):
    """\n    Cost per unit = total_cost / units"""
    return _get("cost_per_unit")(*args, **kwargs)


def cost_percent(*args: Any, **kwargs: Any):
    """\n    Cost as percent."""
    return _get("cost_percent")(*args, **kwargs)


def cost_percent_ex_tax(*args: Any, **kwargs: Any):
    """\n    Cost percent (ex tax)."""
    return _get("cost_percent_ex_tax")(*args, **kwargs)


def cost_percentage_with_tax(*args: Any, **kwargs: Any):
    """\n    Cost percentage with tax."""
    return _get("cost_percentage_with_tax")(*args, **kwargs)


def cost_ratio(*args: Any, **kwargs: Any):
    """\n    Cost ratio = cost / sales"""
    return _get("cost_ratio")(*args, **kwargs)


def cost_ratio_ex_tax(*args: Any, **kwargs: Any):
    """\n    Cost ratio (ex tax) = cost / sales_ex_tax"""
    return _get("cost_ratio_ex_tax")(*args, **kwargs)


def cost_ratio_with_tax(*args: Any, **kwargs: Any):
    """\n    Cost ratio with tax info:
    denominator is sales ex tax, i.e. cost / (sales / (1 + tax_rate))
    """
    return _get("cost_ratio_with_tax")(*args, **kwargs)


def delivery_fee_amount(*args: Any, **kwargs: Any):
    """\n    Delivery fee amount = delivery_sales * delivery_fee_percentage"""
    return _get("delivery_fee_amount")(*args, **kwargs)


def delivery_sales_net(*args: Any, **kwargs: Any):
    """\n    Net delivery sales = delivery_sales * (1 - delivery_fee_percentage)"""
    return _get("delivery_sales_net")(*args, **kwargs)


def discount_percentage(*args: Any, **kwargs: Any):
    """\n    Discount as percent (e.g., 0.20 -> '20%')."""
    return _get("discount_percentage")(*args, **kwargs)


def discount_ratio(*args: Any, **kwargs: Any):
    """\n    Discount ratio = (original_price - discounted_price) / original_price"""
    return _get("discount_ratio")(*args, **kwargs)


def ebitda_margin(*args: Any, **kwargs: Any):
    """\n    EBITDA margin as percent."""
    return _get("ebitda_margin")(*args, **kwargs)


def ebitda_margin_ratio(*args: Any, **kwargs: Any):
    """\n    EBITDA margin ratio = ebitda / revenue"""
    return _get("ebitda_margin_ratio")(*args, **kwargs)


def fnb_cost(*args: Any, **kwargs: Any):
    """\n    F&B cost = food_cost + beverage_cost"""
    return _get("fnb_cost")(*args, **kwargs)


def fnb_sales(*args: Any, **kwargs: Any):
    """\n    F&B sales = food_sales + beverage_sales"""
    return _get("fnb_sales")(*args, **kwargs)


def food_cost_percentage(*args: Any, **kwargs: Any):
    """\n    Food cost as a percent (e.g., 0.30 -> '30%')."""
    return _get("food_cost_percentage")(*args, **kwargs)


def food_cost_ratio(*args: Any, **kwargs: Any):
    """\n    Food cost ratio = food_cost / food_sales_ex_tax"""
    return _get("food_cost_ratio")(*args, **kwargs)


def gross_margin_percentage(*args: Any, **kwargs: Any):
    """\n    Gross margin as percent (e.g., 0.35 -> '35%')."""
    return _get("gross_margin_percentage")(*args, **kwargs)


def gross_margin_percentage_ex_tax(*args: Any, **kwargs: Any):
    """\n    Gross margin (ex tax) as percent."""
    return _get("gross_margin_percentage_ex_tax")(*args, **kwargs)


def gross_margin_ratio(*args: Any, **kwargs: Any):
    """\n    Gross margin ratio = gross_profit / sales"""
    return _get("gross_margin_ratio")(*args, **kwargs)


def gross_margin_ratio_ex_tax(*args: Any, **kwargs: Any):
    """\n    Gross margin ratio (ex tax) = gross_profit_ex_tax / sales_ex_tax"""
    return _get("gross_margin_ratio_ex_tax")(*args, **kwargs)


def gross_profit(*args: Any, **kwargs: Any):
    """\n    Gross profit = sales - cost"""
    return _get("gross_profit")(*args, **kwargs)


def gross_profit_ex_tax(*args: Any, **kwargs: Any):
    """\n    Gross profit (ex tax) = sales_ex_tax - cost"""
    return _get("gross_profit_ex_tax")(*args, **kwargs)


def inventory_turnover(*args: Any, **kwargs: Any):
    """\n    Inventory turnover = cogs / average_inventory"""
    return _get("inventory_turnover")(*args, **kwargs)


def markup_percentage(*args: Any, **kwargs: Any):
    """\n    Markup as percent (e.g., 0.25 -> '25%')."""
    return _get("markup_percentage")(*args, **kwargs)


def markup_ratio(*args: Any, **kwargs: Any):
    """\n    Markup ratio = (selling_price - cost) / cost"""
    return _get("markup_ratio")(*args, **kwargs)


def net_margin_percentage(*args: Any, **kwargs: Any):
    """\n    Net margin as percent."""
    return _get("net_margin_percentage")(*args, **kwargs)


def net_margin_ratio(*args: Any, **kwargs: Any):
    """\n    Net margin ratio = net_profit / revenue"""
    return _get("net_margin_ratio")(*args, **kwargs)


def net_margin_with_tax(*args: Any, **kwargs: Any):
    """\n    Net margin with tax as percent."""
    return _get("net_margin_with_tax")(*args, **kwargs)


def net_margin_with_tax_ratio(*args: Any, **kwargs: Any):
    """\n    Net margin (tax-adjusted) ratio = net_profit_with_tax / sales_ex_tax"""
    return _get("net_margin_with_tax_ratio")(*args, **kwargs)


def net_profit(*args: Any, **kwargs: Any):
    """\n    Net profit = revenue - total_costs"""
    return _get("net_profit")(*args, **kwargs)


def net_profit_with_tax(*args: Any, **kwargs: Any):
    """\n    Net profit (tax-adjusted) = (sales / (1 + tax_rate)) - cost"""
    return _get("net_profit_with_tax")(*args, **kwargs)


def operating_margin(*args: Any, **kwargs: Any):
    """\n    Operating margin as percent."""
    return _get("operating_margin")(*args, **kwargs)


def operating_margin_ratio(*args: Any, **kwargs: Any):
    """\n    Operating margin ratio = operating_income / revenue"""
    return _get("operating_margin_ratio")(*args, **kwargs)


def original_delivery_sales(*args: Any, **kwargs: Any):
    """\n    Original delivery sales = delivery_sales_net / (1 - delivery_fee_percentage)"""
    return _get("original_delivery_sales")(*args, **kwargs)


def percentage_change(*args: Any, **kwargs: Any):
    """\n    Percentage change as percent (e.g., 0.20 -> '20%')."""
    return _get("percentage_change")(*args, **kwargs)


def percentage_change_ratio(*args: Any, **kwargs: Any):
    """\n    Percentage change (ratio) = (new_value - old_value) / old_value"""
    return _get("percentage_change_ratio")(*args, **kwargs)


def percentage_of_total(*args: Any, **kwargs: Any):
    """\n    Percentage of total = (part / total), returned as Percent.

    Business rule: if total <= 0 → return 0% (not None).
    """
    return _get("percentage_of_total")(*args, **kwargs)


def percentage_to_ratio(*args: Any, **kwargs: Any):
    """\n    Convert a percent value to a ratio (e.g., 25% -> 0.25)."""
    return _get("percentage_to_ratio")(*args, **kwargs)


def price_ex_tax(*args: Any, **kwargs: Any):
    """\n    Price excluding tax = price_inc_tax / (1 + tax_rate)"""
    return _get("price_ex_tax")(*args, **kwargs)


def profit_per_unit(*args: Any, **kwargs: Any):
    """\n    Profit per unit = total_profit / units_sold"""
    return _get("profit_per_unit")(*args, **kwargs)


def ratio(*args: Any, **kwargs: Any):
    """\n    Simple ratio = numerator / denominator.

    Default behavior:
      - If denominator == 0 → return None (unless policy.arithmetic_strict, then raise).
      - None inputs propagate to None.
    """
    return _get("ratio")(*args, **kwargs)


def ratio_to_percentage(*args: Any, **kwargs: Any):
    """\n    Convert a ratio (0..1) to percent representation."""
    return _get("ratio_to_percentage")(*args, **kwargs)


def revenue_per_unit(*args: Any, **kwargs: Any):
    """\n    Revenue per unit = total_revenue / units_sold"""
    return _get("revenue_per_unit")(*args, **kwargs)


def roi(*args: Any, **kwargs: Any):
    """\n    ROI as percent."""
    return _get("roi")(*args, **kwargs)


def roi_ratio(*args: Any, **kwargs: Any):
    """\n    ROI ratio = gain_from_investment / cost_of_investment"""
    return _get("roi_ratio")(*args, **kwargs)


def sales_ex_tax(*args: Any, **kwargs: Any):
    """\n    Sales excluding tax = sales / (1 + tax_rate)"""
    return _get("sales_ex_tax")(*args, **kwargs)


def sales_with_tax(*args: Any, **kwargs: Any):
    """\n    Sales including tax = sales_ex_tax * (1 + tax_rate)"""
    return _get("sales_with_tax")(*args, **kwargs)


def simple_growth_rate(*args: Any, **kwargs: Any):
    """\n    Simple growth rate as a ratio: (final - initial) / initial.

    Returns:
        FV[Ratio] in 0..1 (can be negative if shrinking), or None if inputs invalid.
    """
    return _get("simple_growth_rate")(*args, **kwargs)


def tax_amount(*args: Any, **kwargs: Any):
    """\n    Tax amount = sales - (sales / (1 + tax_rate))"""
    return _get("tax_amount")(*args, **kwargs)


def total_cost(*args: Any, **kwargs: Any):
    """\n    Total cost = unit_cost * quantity"""
    return _get("total_cost")(*args, **kwargs)


def variance_amount(*args: Any, **kwargs: Any):
    """\n    Variance amount = actual - expected"""
    return _get("variance_amount")(*args, **kwargs)


def variance_percentage(*args: Any, **kwargs: Any):
    """\n    Variance as percent (positive = over, negative = under)."""
    return _get("variance_percentage")(*args, **kwargs)


def variance_percentage_from_components(*args: Any, **kwargs: Any):
    """\n    Variance (from components) as percent."""
    return _get("variance_percentage_from_components")(*args, **kwargs)


def variance_ratio(*args: Any, **kwargs: Any):
    """\n    Variance ratio = (actual - expected) / expected"""
    return _get("variance_ratio")(*args, **kwargs)


def variance_ratio_from_components(*args: Any, **kwargs: Any):
    """\n    Variance ratio from inventory components:
    expected_closing = opening + purchases - sold
    variance_ratio   = (actual_closing - expected_closing) / expected_closing
    """
    return _get("variance_ratio_from_components")(*args, **kwargs)


def weighted_average(*args: Any, **kwargs: Any):
    """\n    Weighted mean of `values` with `weights`.

    Behavior:
      - Uses SKIP mode: pairs with None in either value or weight are dropped.
      - Empty input or length mismatch → returns None (business rule).
      - Result unit follows the first non-None value's unit (else Dimensionless).
    """
    return _get("weighted_average")(*args, **kwargs)
