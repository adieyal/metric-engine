"""
Inventory and COGS calculations.

This module defines inventory and cost-of-goods-sold calculations using namespaced registration.
It returns ratios (0..1) by default for composability, with separate percent-returning wrappers if needed.
"""

from __future__ import annotations

from decimal import Decimal

from ..exceptions import CalculationError
from ..policy import DEFAULT_POLICY, Policy
from ..policy_context import get_policy
from ..registry_collections import Collection
from ..units import Dimensionless, Money, Percent, Ratio  # phantom units
from ..value import FV

inventory = Collection("inventory")

# ---- small helpers (module-local) -------------------------------------------


def _resolve_policy(*fvs: FV | None) -> Policy:
    for fv in fvs:
        if isinstance(fv, FV) and fv.policy:
            return fv.policy
    return get_policy() or DEFAULT_POLICY


def _none_with_unit(unit, pol) -> FV:
    return FV(None, policy=pol, unit=unit)


def _is_zero(fv: FV) -> bool:
    d = fv.as_decimal()
    return (d is not None) and (d == 0)


# ---- calculations -----------------------------------------------------------


@inventory.calc(
    "cogs", depends_on=("opening_inventory", "purchases", "closing_inventory")
)
def cogs(
    opening_inventory: FV[Money],
    purchases: FV[Money],
    closing_inventory: FV[Money],
) -> FV[Money]:
    """
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
    pol = _resolve_policy(opening_inventory, purchases, closing_inventory)

    if (
        opening_inventory.is_none()
        or purchases.is_none()
        or closing_inventory.is_none()
    ):
        return _none_with_unit(Money, pol)

    return opening_inventory + purchases - closing_inventory


@inventory.calc("cogs_ratio", depends_on=("cogs", "sales"))
def cogs_ratio(
    cogs: FV[Money],
    sales: FV[Money],
) -> FV[Ratio]:
    """COGS ratio = cogs / sales"""
    pol = _resolve_policy(cogs, sales)

    if cogs.is_none() or sales.is_none():
        return _none_with_unit(Ratio, pol)

    if _is_zero(sales):
        if pol.arithmetic_strict:
            raise CalculationError("COGS ratio undefined for sales == 0")
        return _none_with_unit(Ratio, pol)

    return (cogs / sales).ratio()


@inventory.calc("cogs_percentage", depends_on=("cogs_ratio",))
def cogs_percentage(cogs_ratio: FV[Ratio]) -> FV[Percent]:
    """COGS as a percent (e.g., 0.48 -> '48%')."""
    pol = _resolve_policy(cogs_ratio)
    if cogs_ratio.is_none():
        return _none_with_unit(Percent, pol)
    return cogs_ratio.as_percentage()


@inventory.calc("inventory_turnover", depends_on=("cogs", "average_inventory"))
def inventory_turnover(
    cogs: FV[Money],
    average_inventory: FV[Money],
) -> FV[Ratio]:
    """Inventory turnover = cogs / average_inventory"""
    pol = _resolve_policy(cogs, average_inventory)

    if cogs.is_none() or average_inventory.is_none():
        return _none_with_unit(Ratio, pol)

    if _is_zero(average_inventory):
        if pol.arithmetic_strict:
            raise CalculationError(
                "Inventory turnover undefined for average_inventory == 0"
            )
        return _none_with_unit(Ratio, pol)

    return (cogs / average_inventory).ratio()


@inventory.calc(
    "average_inventory", depends_on=("opening_inventory", "closing_inventory")
)
def average_inventory(
    opening_inventory: FV[Money],
    closing_inventory: FV[Money],
) -> FV[Money]:
    """Average inventory = (opening_inventory + closing_inventory) / 2"""
    pol = _resolve_policy(opening_inventory, closing_inventory)

    if opening_inventory.is_none() or closing_inventory.is_none():
        return _none_with_unit(Money, pol)

    two = FV(Decimal("2"), policy=pol, unit=Dimensionless)
    return (opening_inventory + closing_inventory) / two


@inventory.calc("fnb_sales", depends_on=("food_sales", "beverage_sales"))
def fnb_sales(
    food_sales: FV[Money],
    beverage_sales: FV[Money],
) -> FV[Money]:
    """F&B sales = food_sales + beverage_sales"""
    pol = _resolve_policy(food_sales, beverage_sales)
    if food_sales.is_none() or beverage_sales.is_none():
        return _none_with_unit(Money, pol)
    return food_sales + beverage_sales


@inventory.calc("fnb_cost", depends_on=("food_cost", "beverage_cost"))
def fnb_cost(
    food_cost: FV[Money],
    beverage_cost: FV[Money],
) -> FV[Money]:
    """F&B cost = food_cost + beverage_cost"""
    pol = _resolve_policy(food_cost, beverage_cost)
    if food_cost.is_none() or beverage_cost.is_none():
        return _none_with_unit(Money, pol)
    return food_cost + beverage_cost


@inventory.calc("food_cost_ratio", depends_on=("food_cost", "food_sales_ex_tax"))
def food_cost_ratio(
    food_cost: FV[Money],
    food_sales_ex_tax: FV[Money],
) -> FV[Ratio]:
    """Food cost ratio = food_cost / food_sales_ex_tax"""
    pol = _resolve_policy(food_cost, food_sales_ex_tax)

    if food_cost.is_none() or food_sales_ex_tax.is_none():
        return _none_with_unit(Ratio, pol)

    if _is_zero(food_sales_ex_tax):
        if pol.arithmetic_strict:
            raise CalculationError(
                "Food cost ratio undefined for food_sales_ex_tax == 0"
            )
        return _none_with_unit(Ratio, pol)

    return (food_cost / food_sales_ex_tax).ratio()


@inventory.calc("food_cost_percentage", depends_on=("food_cost_ratio",))
def food_cost_percentage(food_cost_ratio: FV[Ratio]) -> FV[Percent]:
    """Food cost as a percent (e.g., 0.30 -> '30%')."""
    pol = _resolve_policy(food_cost_ratio)
    if food_cost_ratio.is_none():
        return _none_with_unit(Percent, pol)
    return food_cost_ratio.as_percentage()


@inventory.calc(
    "beverage_cost_ratio", depends_on=("beverage_cost", "beverage_sales_ex_tax")
)
def beverage_cost_ratio(
    beverage_cost: FV[Money],
    beverage_sales_ex_tax: FV[Money],
) -> FV[Ratio]:
    """Beverage cost ratio = beverage_cost / beverage_sales_ex_tax"""
    pol = _resolve_policy(beverage_cost, beverage_sales_ex_tax)

    if beverage_cost.is_none() or beverage_sales_ex_tax.is_none():
        return _none_with_unit(Ratio, pol)

    if _is_zero(beverage_sales_ex_tax):
        if pol.arithmetic_strict:
            raise CalculationError(
                "Beverage cost ratio undefined for beverage_sales_ex_tax == 0"
            )
        return _none_with_unit(Ratio, pol)

    return (beverage_cost / beverage_sales_ex_tax).ratio()


@inventory.calc("beverage_cost_percentage", depends_on=("beverage_cost_ratio",))
def beverage_cost_percentage(beverage_cost_ratio: FV[Ratio]) -> FV[Percent]:
    """Beverage cost as a percent (e.g., 0.20 -> '20%')."""
    pol = _resolve_policy(beverage_cost_ratio)
    if beverage_cost_ratio.is_none():
        return _none_with_unit(Percent, pol)
    return beverage_cost_ratio.as_percentage()


@inventory.calc(
    "delivery_fee_amount", depends_on=("delivery_sales", "delivery_fee_percentage")
)
def delivery_fee_amount(
    delivery_sales: FV[Money],
    delivery_fee_percentage: FV[Percent],
) -> FV[Money]:
    """Delivery fee amount = delivery_sales * delivery_fee_percentage"""
    pol = _resolve_policy(delivery_sales, delivery_fee_percentage)
    if delivery_sales.is_none() or delivery_fee_percentage.is_none():
        return _none_with_unit(Money, pol)
    result = delivery_sales * delivery_fee_percentage
    return FV(result._value, policy=pol, unit=Money)


@inventory.calc(
    "delivery_sales_net", depends_on=("delivery_sales", "delivery_fee_percentage")
)
def delivery_sales_net(
    delivery_sales: FV[Money],
    delivery_fee_percentage: FV[Percent],
) -> FV[Money]:
    """Net delivery sales = delivery_sales * (1 - delivery_fee_percentage)"""
    pol = _resolve_policy(delivery_sales, delivery_fee_percentage)
    if delivery_sales.is_none() or delivery_fee_percentage.is_none():
        return _none_with_unit(Money, pol)
    one = FV(Decimal("1"), policy=pol, unit=Dimensionless)
    return delivery_sales * (one - delivery_fee_percentage)


@inventory.calc(
    "original_delivery_sales",
    depends_on=("delivery_sales_net", "delivery_fee_percentage"),  # fixed name
)
def original_delivery_sales(
    delivery_sales_net: FV[Money],
    delivery_fee_percentage: FV[Percent],
) -> FV[Money]:
    """Original delivery sales = delivery_sales_net / (1 - delivery_fee_percentage)"""
    pol = _resolve_policy(delivery_sales_net, delivery_fee_percentage)

    if delivery_sales_net.is_none() or delivery_fee_percentage.is_none():
        return _none_with_unit(Money, pol)

    one = FV(Decimal("1"), policy=pol, unit=Dimensionless)
    denom = one - delivery_fee_percentage

    if _is_zero(denom):
        if pol.arithmetic_strict:
            raise CalculationError(
                "Original delivery sales undefined when delivery_fee_percentage == 1"
            )
        return _none_with_unit(Money, pol)

    return delivery_sales_net / denom
