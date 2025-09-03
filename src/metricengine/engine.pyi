# Auto-generated — DO NOT EDIT.
from collections.abc import Mapping, Sequence
from decimal import Decimal
from types import NoneType
from typing import Any, Literal, SupportsFloat, TypeVar, Union, overload

from metricengine import Dimensionless, Money, Percent, Policy, Ratio, Unit
from metricengine import FinancialValue as FV
from metricengine.utils import SupportsDecimal

U = TypeVar("U", bound=Unit)

class Engine:
    def __init__(self, *args: Any, **kwargs: Any) -> None: ...
    @overload
    def calculate(
        self,
        name: Literal["average_inventory"],
        ctx: Mapping[str, SupportsDecimal] | None = ...,
        *,
        policy: Policy | None = ...,
        allow_partial: bool = ...,
        opening_inventory: FV[Money],
        closing_inventory: FV[Money],
    ) -> FV[Money]:
        """\
        Average inventory = (opening_inventory + closing_inventory) / 2
        """
        ...

    @overload
    def calculate(
        self,
        name: Literal["average_value"],
        ctx: Mapping[str, SupportsDecimal] | None = ...,
        *,
        policy: Policy | None = ...,
        allow_partial: bool = ...,
        values: Sequence[
            Union[int, float, str, Decimal, SupportsFloat, NoneType, FV, FV[U]]
        ],
    ) -> FV[U]:
        """\
        Arithmetic mean of a sequence.

        Behavior:
          - Uses SKIP mode: None items are excluded from both sum and count.
          - Empty or all-None → returns None.
          - Result unit follows the first non-None item's unit (else Dimensionless).
        """
        ...

    @overload
    def calculate(
        self,
        name: Literal["beverage_cost_percentage"],
        ctx: Mapping[str, SupportsDecimal] | None = ...,
        *,
        policy: Policy | None = ...,
        allow_partial: bool = ...,
        beverage_cost_ratio: FV[Ratio],
    ) -> FV[Percent]:
        """\
        Beverage cost as a percent (e.g., 0.20 -> '20%').
        """
        ...

    @overload
    def calculate(
        self,
        name: Literal["beverage_cost_ratio"],
        ctx: Mapping[str, SupportsDecimal] | None = ...,
        *,
        policy: Policy | None = ...,
        allow_partial: bool = ...,
        beverage_cost: FV[Money],
        beverage_sales_ex_tax: FV[Money],
    ) -> FV[Ratio]:
        """\
        Beverage cost ratio = beverage_cost / beverage_sales_ex_tax
        """
        ...

    @overload
    def calculate(
        self,
        name: Literal["break_even_point"],
        ctx: Mapping[str, SupportsDecimal] | None = ...,
        *,
        policy: Policy | None = ...,
        allow_partial: bool = ...,
        fixed_costs: FV[Money],
        price_per_unit: FV[Money],
        variable_cost_per_unit: FV[Money],
    ) -> FV[Dimensionless]:
        """\
        Break-even point (units) = fixed_costs / (price_per_unit - variable_cost_per_unit)

        Returns a Dimensionless count of units (not a ratio).
        """
        ...

    @overload
    def calculate(
        self,
        name: Literal["cap_percentage"],
        ctx: Mapping[str, SupportsDecimal] | None = ...,
        *,
        policy: Policy | None = ...,
        allow_partial: bool = ...,
        percentage: FV[Percent],
        max_percentage: FV[Percent],
    ) -> FV[Percent]:
        """\
        Cap a percentage at a maximum value.

        Returns None if either input is None.
        """
        ...

    @overload
    def calculate(
        self,
        name: Literal["cogs"],
        ctx: Mapping[str, SupportsDecimal] | None = ...,
        *,
        policy: Policy | None = ...,
        allow_partial: bool = ...,
        opening_inventory: FV[Money],
        purchases: FV[Money],
        closing_inventory: FV[Money],
    ) -> FV[Money]:
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
        ...

    @overload
    def calculate(
        self,
        name: Literal["cogs_percentage"],
        ctx: Mapping[str, SupportsDecimal] | None = ...,
        *,
        policy: Policy | None = ...,
        allow_partial: bool = ...,
        cogs_ratio: FV[Ratio],
    ) -> FV[Percent]:
        """\
        COGS as a percent (e.g., 0.48 -> '48%').
        """
        ...

    @overload
    def calculate(
        self,
        name: Literal["cogs_ratio"],
        ctx: Mapping[str, SupportsDecimal] | None = ...,
        *,
        policy: Policy | None = ...,
        allow_partial: bool = ...,
        cogs: FV[Money],
        sales: FV[Money],
    ) -> FV[Ratio]:
        """\
        COGS ratio = cogs / sales
        """
        ...

    @overload
    def calculate(
        self,
        name: Literal["compound_growth_rate"],
        ctx: Mapping[str, SupportsDecimal] | None = ...,
        *,
        policy: Policy | None = ...,
        allow_partial: bool = ...,
        initial_value: FV[U],
        final_value: FV[U],
        periods: FV[Dimensionless],
    ) -> FV[Ratio]:
        """\
        Compound annual growth rate (CAGR) as a ratio (0..1):

            CAGR = exp( ln(final / initial) / periods ) - 1

        Notes:
            - Requires strictly positive initial, final, and periods.
            - Returns None on invalid inputs unless policy.arithmetic_strict, in which case raises.
        """
        ...

    @overload
    def calculate(
        self,
        name: Literal["compound_growth_rate_percent"],
        ctx: Mapping[str, SupportsDecimal] | None = ...,
        *,
        policy: Policy | None = ...,
        allow_partial: bool = ...,
        compound_growth_rate: FV[Ratio],
    ) -> FV[Percent]:
        """\
        CAGR as a percent (e.g., 0.10 -> '10%').
        """
        ...

    @overload
    def calculate(
        self,
        name: Literal["contribution_margin"],
        ctx: Mapping[str, SupportsDecimal] | None = ...,
        *,
        policy: Policy | None = ...,
        allow_partial: bool = ...,
        revenue: FV[Money],
        variable_costs: FV[Money],
    ) -> FV[Money]:
        """\
        Contribution margin = revenue - variable_costs
        """
        ...

    @overload
    def calculate(
        self,
        name: Literal["contribution_margin_ratio"],
        ctx: Mapping[str, SupportsDecimal] | None = ...,
        *,
        policy: Policy | None = ...,
        allow_partial: bool = ...,
        contribution_margin_ratio_raw: FV[Ratio],
    ) -> FV[Percent]:
        """\
        Contribution margin ratio as percent.
        """
        ...

    @overload
    def calculate(
        self,
        name: Literal["contribution_margin_ratio_raw"],
        ctx: Mapping[str, SupportsDecimal] | None = ...,
        *,
        policy: Policy | None = ...,
        allow_partial: bool = ...,
        contribution_margin: FV[Money],
        revenue: FV[Money],
    ) -> FV[Ratio]:
        """\
        Contribution margin ratio = contribution_margin / revenue
        """
        ...

    @overload
    def calculate(
        self,
        name: Literal["cost_per_unit"],
        ctx: Mapping[str, SupportsDecimal] | None = ...,
        *,
        policy: Policy | None = ...,
        allow_partial: bool = ...,
        total_cost: FV[Money],
        units: FV[Dimensionless],
    ) -> FV[Money]:
        """\
        Cost per unit = total_cost / units
        """
        ...

    @overload
    def calculate(
        self,
        name: Literal["cost_percent"],
        ctx: Mapping[str, SupportsDecimal] | None = ...,
        *,
        policy: Policy | None = ...,
        allow_partial: bool = ...,
        cost_ratio: FV[Ratio],
    ) -> FV[Percent]:
        """\
        Cost as percent.
        """
        ...

    @overload
    def calculate(
        self,
        name: Literal["cost_percent_ex_tax"],
        ctx: Mapping[str, SupportsDecimal] | None = ...,
        *,
        policy: Policy | None = ...,
        allow_partial: bool = ...,
        cost_ratio_ex_tax: FV[Ratio],
    ) -> FV[Percent]:
        """\
        Cost percent (ex tax).
        """
        ...

    @overload
    def calculate(
        self,
        name: Literal["cost_percentage_with_tax"],
        ctx: Mapping[str, SupportsDecimal] | None = ...,
        *,
        policy: Policy | None = ...,
        allow_partial: bool = ...,
        cost_ratio_with_tax: FV[Ratio],
    ) -> FV[Percent]:
        """\
        Cost percentage with tax.
        """
        ...

    @overload
    def calculate(
        self,
        name: Literal["cost_ratio"],
        ctx: Mapping[str, SupportsDecimal] | None = ...,
        *,
        policy: Policy | None = ...,
        allow_partial: bool = ...,
        cost: FV[Money],
        sales: FV[Money],
    ) -> FV[Ratio]:
        """\
        Cost ratio = cost / sales
        """
        ...

    @overload
    def calculate(
        self,
        name: Literal["cost_ratio_ex_tax"],
        ctx: Mapping[str, SupportsDecimal] | None = ...,
        *,
        policy: Policy | None = ...,
        allow_partial: bool = ...,
        cost: FV[Money],
        sales_ex_tax: FV[Money],
    ) -> FV[Ratio]:
        """\
        Cost ratio (ex tax) = cost / sales_ex_tax
        """
        ...

    @overload
    def calculate(
        self,
        name: Literal["cost_ratio_with_tax"],
        ctx: Mapping[str, SupportsDecimal] | None = ...,
        *,
        policy: Policy | None = ...,
        allow_partial: bool = ...,
        cost: FV[Money],
        sales: FV[Money],
        tax_rate: FV[Percent],
    ) -> FV[Ratio]:
        """\
        Cost ratio with tax info:
          denominator is sales ex tax, i.e. cost / (sales / (1 + tax_rate))
        """
        ...

    @overload
    def calculate(
        self,
        name: Literal["delivery_fee_amount"],
        ctx: Mapping[str, SupportsDecimal] | None = ...,
        *,
        policy: Policy | None = ...,
        allow_partial: bool = ...,
        delivery_sales: FV[Money],
        delivery_fee_percentage: FV[Percent],
    ) -> FV[Money]:
        """\
        Delivery fee amount = delivery_sales * delivery_fee_percentage
        """
        ...

    @overload
    def calculate(
        self,
        name: Literal["delivery_sales_net"],
        ctx: Mapping[str, SupportsDecimal] | None = ...,
        *,
        policy: Policy | None = ...,
        allow_partial: bool = ...,
        delivery_sales: FV[Money],
        delivery_fee_percentage: FV[Percent],
    ) -> FV[Money]:
        """\
        Net delivery sales = delivery_sales * (1 - delivery_fee_percentage)
        """
        ...

    @overload
    def calculate(
        self,
        name: Literal["discount_percentage"],
        ctx: Mapping[str, SupportsDecimal] | None = ...,
        *,
        policy: Policy | None = ...,
        allow_partial: bool = ...,
        discount_ratio: FV[Ratio],
    ) -> FV[Percent]:
        """\
        Discount as percent (e.g., 0.20 -> '20%').
        """
        ...

    @overload
    def calculate(
        self,
        name: Literal["discount_ratio"],
        ctx: Mapping[str, SupportsDecimal] | None = ...,
        *,
        policy: Policy | None = ...,
        allow_partial: bool = ...,
        original_price: FV[Money],
        discounted_price: FV[Money],
    ) -> FV[Ratio]:
        """\
        Discount ratio = (original_price - discounted_price) / original_price
        """
        ...

    @overload
    def calculate(
        self,
        name: Literal["ebitda_margin"],
        ctx: Mapping[str, SupportsDecimal] | None = ...,
        *,
        policy: Policy | None = ...,
        allow_partial: bool = ...,
        ebitda_margin_ratio: FV[Ratio],
    ) -> FV[Percent]:
        """\
        EBITDA margin as percent.
        """
        ...

    @overload
    def calculate(
        self,
        name: Literal["ebitda_margin_ratio"],
        ctx: Mapping[str, SupportsDecimal] | None = ...,
        *,
        policy: Policy | None = ...,
        allow_partial: bool = ...,
        ebitda: FV[Money],
        revenue: FV[Money],
    ) -> FV[Ratio]:
        """\
        EBITDA margin ratio = ebitda / revenue
        """
        ...

    @overload
    def calculate(
        self,
        name: Literal["fnb_cost"],
        ctx: Mapping[str, SupportsDecimal] | None = ...,
        *,
        policy: Policy | None = ...,
        allow_partial: bool = ...,
        food_cost: FV[Money],
        beverage_cost: FV[Money],
    ) -> FV[Money]:
        """\
        F&B cost = food_cost + beverage_cost
        """
        ...

    @overload
    def calculate(
        self,
        name: Literal["fnb_sales"],
        ctx: Mapping[str, SupportsDecimal] | None = ...,
        *,
        policy: Policy | None = ...,
        allow_partial: bool = ...,
        food_sales: FV[Money],
        beverage_sales: FV[Money],
    ) -> FV[Money]:
        """\
        F&B sales = food_sales + beverage_sales
        """
        ...

    @overload
    def calculate(
        self,
        name: Literal["food_cost_percentage"],
        ctx: Mapping[str, SupportsDecimal] | None = ...,
        *,
        policy: Policy | None = ...,
        allow_partial: bool = ...,
        food_cost_ratio: FV[Ratio],
    ) -> FV[Percent]:
        """\
        Food cost as a percent (e.g., 0.30 -> '30%').
        """
        ...

    @overload
    def calculate(
        self,
        name: Literal["food_cost_ratio"],
        ctx: Mapping[str, SupportsDecimal] | None = ...,
        *,
        policy: Policy | None = ...,
        allow_partial: bool = ...,
        food_cost: FV[Money],
        food_sales_ex_tax: FV[Money],
    ) -> FV[Ratio]:
        """\
        Food cost ratio = food_cost / food_sales_ex_tax
        """
        ...

    @overload
    def calculate(
        self,
        name: Literal["gross_margin_percentage"],
        ctx: Mapping[str, SupportsDecimal] | None = ...,
        *,
        policy: Policy | None = ...,
        allow_partial: bool = ...,
        gross_margin_ratio: FV[Ratio],
    ) -> FV[Percent]:
        """\
        Gross margin as percent (e.g., 0.35 -> '35%').
        """
        ...

    @overload
    def calculate(
        self,
        name: Literal["gross_margin_percentage_ex_tax"],
        ctx: Mapping[str, SupportsDecimal] | None = ...,
        *,
        policy: Policy | None = ...,
        allow_partial: bool = ...,
        gross_margin_ratio_ex_tax: FV[Ratio],
    ) -> FV[Percent]:
        """\
        Gross margin (ex tax) as percent.
        """
        ...

    @overload
    def calculate(
        self,
        name: Literal["gross_margin_ratio"],
        ctx: Mapping[str, SupportsDecimal] | None = ...,
        *,
        policy: Policy | None = ...,
        allow_partial: bool = ...,
        gross_profit: FV[Money],
        sales: FV[Money],
    ) -> FV[Ratio]:
        """\
        Gross margin ratio = gross_profit / sales
        """
        ...

    @overload
    def calculate(
        self,
        name: Literal["gross_margin_ratio_ex_tax"],
        ctx: Mapping[str, SupportsDecimal] | None = ...,
        *,
        policy: Policy | None = ...,
        allow_partial: bool = ...,
        gross_profit_ex_tax: FV[Money],
        sales_ex_tax: FV[Money],
    ) -> FV[Ratio]:
        """\
        Gross margin ratio (ex tax) = gross_profit_ex_tax / sales_ex_tax
        """
        ...

    @overload
    def calculate(
        self,
        name: Literal["gross_profit"],
        ctx: Mapping[str, SupportsDecimal] | None = ...,
        *,
        policy: Policy | None = ...,
        allow_partial: bool = ...,
        sales: FV[Money],
        cost: FV[Money],
    ) -> FV[Money]:
        """\
        Gross profit = sales - cost
        """
        ...

    @overload
    def calculate(
        self,
        name: Literal["gross_profit_ex_tax"],
        ctx: Mapping[str, SupportsDecimal] | None = ...,
        *,
        policy: Policy | None = ...,
        allow_partial: bool = ...,
        sales_ex_tax: FV[Money],
        cost: FV[Money],
    ) -> FV[Money]:
        """\
        Gross profit (ex tax) = sales_ex_tax - cost
        """
        ...

    @overload
    def calculate(
        self,
        name: Literal["inventory_turnover"],
        ctx: Mapping[str, SupportsDecimal] | None = ...,
        *,
        policy: Policy | None = ...,
        allow_partial: bool = ...,
        cogs: FV[Money],
        average_inventory: FV[Money],
    ) -> FV[Ratio]:
        """\
        Inventory turnover = cogs / average_inventory
        """
        ...

    @overload
    def calculate(
        self,
        name: Literal["markup_percentage"],
        ctx: Mapping[str, SupportsDecimal] | None = ...,
        *,
        policy: Policy | None = ...,
        allow_partial: bool = ...,
        markup_ratio: FV[Ratio],
    ) -> FV[Percent]:
        """\
        Markup as percent (e.g., 0.25 -> '25%').
        """
        ...

    @overload
    def calculate(
        self,
        name: Literal["markup_ratio"],
        ctx: Mapping[str, SupportsDecimal] | None = ...,
        *,
        policy: Policy | None = ...,
        allow_partial: bool = ...,
        cost: FV[Money],
        selling_price: FV[Money],
    ) -> FV[Ratio]:
        """\
        Markup ratio = (selling_price - cost) / cost
        """
        ...

    @overload
    def calculate(
        self,
        name: Literal["net_margin_percentage"],
        ctx: Mapping[str, SupportsDecimal] | None = ...,
        *,
        policy: Policy | None = ...,
        allow_partial: bool = ...,
        net_margin_ratio: FV[Ratio],
    ) -> FV[Percent]:
        """\
        Net margin as percent.
        """
        ...

    @overload
    def calculate(
        self,
        name: Literal["net_margin_ratio"],
        ctx: Mapping[str, SupportsDecimal] | None = ...,
        *,
        policy: Policy | None = ...,
        allow_partial: bool = ...,
        net_profit: FV[Money],
        revenue: FV[Money],
    ) -> FV[Ratio]:
        """\
        Net margin ratio = net_profit / revenue
        """
        ...

    @overload
    def calculate(
        self,
        name: Literal["net_margin_with_tax"],
        ctx: Mapping[str, SupportsDecimal] | None = ...,
        *,
        policy: Policy | None = ...,
        allow_partial: bool = ...,
        net_margin_with_tax_ratio: FV[Ratio],
    ) -> FV[Percent]:
        """\
        Net margin with tax as percent.
        """
        ...

    @overload
    def calculate(
        self,
        name: Literal["net_margin_with_tax_ratio"],
        ctx: Mapping[str, SupportsDecimal] | None = ...,
        *,
        policy: Policy | None = ...,
        allow_partial: bool = ...,
        net_profit_with_tax: FV[Money],
        sales_ex_tax: FV[Money],
    ) -> FV[Ratio]:
        """\
        Net margin (tax-adjusted) ratio = net_profit_with_tax / sales_ex_tax
        """
        ...

    @overload
    def calculate(
        self,
        name: Literal["net_profit"],
        ctx: Mapping[str, SupportsDecimal] | None = ...,
        *,
        policy: Policy | None = ...,
        allow_partial: bool = ...,
        revenue: FV[Money],
        total_costs: FV[Money],
    ) -> FV[Money]:
        """\
        Net profit = revenue - total_costs
        """
        ...

    @overload
    def calculate(
        self,
        name: Literal["net_profit_with_tax"],
        ctx: Mapping[str, SupportsDecimal] | None = ...,
        *,
        policy: Policy | None = ...,
        allow_partial: bool = ...,
        sales: FV[Money],
        cost: FV[Money],
        tax_rate: FV[Percent],
    ) -> FV[Money]:
        """\
        Net profit (tax-adjusted) = (sales / (1 + tax_rate)) - cost
        """
        ...

    @overload
    def calculate(
        self,
        name: Literal["operating_margin"],
        ctx: Mapping[str, SupportsDecimal] | None = ...,
        *,
        policy: Policy | None = ...,
        allow_partial: bool = ...,
        operating_margin_ratio: FV[Ratio],
    ) -> FV[Percent]:
        """\
        Operating margin as percent.
        """
        ...

    @overload
    def calculate(
        self,
        name: Literal["operating_margin_ratio"],
        ctx: Mapping[str, SupportsDecimal] | None = ...,
        *,
        policy: Policy | None = ...,
        allow_partial: bool = ...,
        operating_income: FV[Money],
        revenue: FV[Money],
    ) -> FV[Ratio]:
        """\
        Operating margin ratio = operating_income / revenue
        """
        ...

    @overload
    def calculate(
        self,
        name: Literal["original_delivery_sales"],
        ctx: Mapping[str, SupportsDecimal] | None = ...,
        *,
        policy: Policy | None = ...,
        allow_partial: bool = ...,
        delivery_sales_net: FV[Money],
        delivery_fee_percentage: FV[Percent],
    ) -> FV[Money]:
        """\
        Original delivery sales = delivery_sales_net / (1 - delivery_fee_percentage)
        """
        ...

    @overload
    def calculate(
        self,
        name: Literal["percentage_change"],
        ctx: Mapping[str, SupportsDecimal] | None = ...,
        *,
        policy: Policy | None = ...,
        allow_partial: bool = ...,
        percentage_change_ratio: FV[Ratio],
    ) -> FV[Percent]:
        """\
        Percentage change as percent (e.g., 0.20 -> '20%').
        """
        ...

    @overload
    def calculate(
        self,
        name: Literal["percentage_change_ratio"],
        ctx: Mapping[str, SupportsDecimal] | None = ...,
        *,
        policy: Policy | None = ...,
        allow_partial: bool = ...,
        old_value: FV[U],
        new_value: FV[U],
    ) -> FV[Ratio]:
        """\
        Percentage change (ratio) = (new_value - old_value) / old_value
        """
        ...

    @overload
    def calculate(
        self,
        name: Literal["percentage_of_total"],
        ctx: Mapping[str, SupportsDecimal] | None = ...,
        *,
        policy: Policy | None = ...,
        allow_partial: bool = ...,
        part: FV[U],
        total: FV[U],
    ) -> FV[Percent]:
        """\
        Percentage of total = (part / total), returned as Percent.

        Business rule: if total <= 0 → return 0% (not None).
        """
        ...

    @overload
    def calculate(
        self,
        name: Literal["percentage_to_ratio"],
        ctx: Mapping[str, SupportsDecimal] | None = ...,
        *,
        policy: Policy | None = ...,
        allow_partial: bool = ...,
        percentage: FV[Percent],
    ) -> FV[Ratio]:
        """\
        Convert a percent value to a ratio (e.g., 25% -> 0.25).
        """
        ...

    @overload
    def calculate(
        self,
        name: Literal["price_ex_tax"],
        ctx: Mapping[str, SupportsDecimal] | None = ...,
        *,
        policy: Policy | None = ...,
        allow_partial: bool = ...,
        price_inc_tax: FV[Money],
        tax_rate: FV[Percent],
    ) -> FV[Money]:
        """\
        Price excluding tax = price_inc_tax / (1 + tax_rate)
        """
        ...

    @overload
    def calculate(
        self,
        name: Literal["profit_per_unit"],
        ctx: Mapping[str, SupportsDecimal] | None = ...,
        *,
        policy: Policy | None = ...,
        allow_partial: bool = ...,
        total_profit: FV[Money],
        units_sold: FV[Dimensionless],
    ) -> FV[Money]:
        """\
        Profit per unit = total_profit / units_sold
        """
        ...

    @overload
    def calculate(
        self,
        name: Literal["ratio"],
        ctx: Mapping[str, SupportsDecimal] | None = ...,
        *,
        policy: Policy | None = ...,
        allow_partial: bool = ...,
        numerator: FV[U],
        denominator: FV[U],
    ) -> FV[Ratio]:
        """\
        Simple ratio = numerator / denominator.

        Default behavior:
          - If denominator == 0 → return None (unless policy.arithmetic_strict, then raise).
          - None inputs propagate to None.
        """
        ...

    @overload
    def calculate(
        self,
        name: Literal["ratio_to_percentage"],
        ctx: Mapping[str, SupportsDecimal] | None = ...,
        *,
        policy: Policy | None = ...,
        allow_partial: bool = ...,
        ratio: FV[Ratio],
    ) -> FV[Percent]:
        """\
        Convert a ratio (0..1) to percent representation.
        """
        ...

    @overload
    def calculate(
        self,
        name: Literal["revenue_per_unit"],
        ctx: Mapping[str, SupportsDecimal] | None = ...,
        *,
        policy: Policy | None = ...,
        allow_partial: bool = ...,
        total_revenue: FV[Money],
        units_sold: FV[Dimensionless],
    ) -> FV[Money]:
        """\
        Revenue per unit = total_revenue / units_sold
        """
        ...

    @overload
    def calculate(
        self,
        name: Literal["roi"],
        ctx: Mapping[str, SupportsDecimal] | None = ...,
        *,
        policy: Policy | None = ...,
        allow_partial: bool = ...,
        roi_ratio: FV[Ratio],
    ) -> FV[Percent]:
        """\
        ROI as percent.
        """
        ...

    @overload
    def calculate(
        self,
        name: Literal["roi_ratio"],
        ctx: Mapping[str, SupportsDecimal] | None = ...,
        *,
        policy: Policy | None = ...,
        allow_partial: bool = ...,
        gain_from_investment: FV[Money],
        cost_of_investment: FV[Money],
    ) -> FV[Ratio]:
        """\
        ROI ratio = gain_from_investment / cost_of_investment
        """
        ...

    @overload
    def calculate(
        self,
        name: Literal["sales_ex_tax"],
        ctx: Mapping[str, SupportsDecimal] | None = ...,
        *,
        policy: Policy | None = ...,
        allow_partial: bool = ...,
        sales: FV[Money],
        tax_rate: FV[Percent],
    ) -> FV[Money]:
        """\
        Sales excluding tax = sales / (1 + tax_rate)
        """
        ...

    @overload
    def calculate(
        self,
        name: Literal["sales_with_tax"],
        ctx: Mapping[str, SupportsDecimal] | None = ...,
        *,
        policy: Policy | None = ...,
        allow_partial: bool = ...,
        sales_ex_tax: FV[Money],
        tax_rate: FV[Percent],
    ) -> FV[Money]:
        """\
        Sales including tax = sales_ex_tax * (1 + tax_rate)
        """
        ...

    @overload
    def calculate(
        self,
        name: Literal["simple_growth_rate"],
        ctx: Mapping[str, SupportsDecimal] | None = ...,
        *,
        policy: Policy | None = ...,
        allow_partial: bool = ...,
        initial_value: FV[U],
        final_value: FV[U],
    ) -> FV[Ratio]:
        """\
        Simple growth rate as a ratio: (final - initial) / initial.

        Returns:
            FV[Ratio] in 0..1 (can be negative if shrinking), or None if inputs invalid.
        """
        ...

    @overload
    def calculate(
        self,
        name: Literal["tax_amount"],
        ctx: Mapping[str, SupportsDecimal] | None = ...,
        *,
        policy: Policy | None = ...,
        allow_partial: bool = ...,
        sales: FV[Money],
        tax_rate: FV[Percent],
    ) -> FV[Money]:
        """\
        Tax amount = sales - (sales / (1 + tax_rate))
        """
        ...

    @overload
    def calculate(
        self,
        name: Literal["total_cost"],
        ctx: Mapping[str, SupportsDecimal] | None = ...,
        *,
        policy: Policy | None = ...,
        allow_partial: bool = ...,
        unit_cost: FV[Money],
        quantity: FV[Dimensionless],
    ) -> FV[Money]:
        """\
        Total cost = unit_cost * quantity
        """
        ...

    @overload
    def calculate(
        self,
        name: Literal["variance_amount"],
        ctx: Mapping[str, SupportsDecimal] | None = ...,
        *,
        policy: Policy | None = ...,
        allow_partial: bool = ...,
        actual: FV[U],
        expected: FV[U],
    ) -> FV[U]:
        """\
        Variance amount = actual - expected
        """
        ...

    @overload
    def calculate(
        self,
        name: Literal["variance_percentage"],
        ctx: Mapping[str, SupportsDecimal] | None = ...,
        *,
        policy: Policy | None = ...,
        allow_partial: bool = ...,
        variance_ratio: FV[Ratio],
    ) -> FV[Percent]:
        """\
        Variance as percent (positive = over, negative = under).
        """
        ...

    @overload
    def calculate(
        self,
        name: Literal["variance_percentage_from_components"],
        ctx: Mapping[str, SupportsDecimal] | None = ...,
        *,
        policy: Policy | None = ...,
        allow_partial: bool = ...,
        vrc: FV[Ratio],
    ) -> FV[Percent]:
        """\
        Variance (from components) as percent.
        """
        ...

    @overload
    def calculate(
        self,
        name: Literal["variance_ratio"],
        ctx: Mapping[str, SupportsDecimal] | None = ...,
        *,
        policy: Policy | None = ...,
        allow_partial: bool = ...,
        actual: FV[U],
        expected: FV[U],
    ) -> FV[Ratio]:
        """\
        Variance ratio = (actual - expected) / expected
        """
        ...

    @overload
    def calculate(
        self,
        name: Literal["variance_ratio_from_components"],
        ctx: Mapping[str, SupportsDecimal] | None = ...,
        *,
        policy: Policy | None = ...,
        allow_partial: bool = ...,
        actual_closing: FV[Money],
        opening: FV[Money],
        purchases: FV[Money],
        sold: FV[Money],
    ) -> FV[Ratio]:
        """\
        Variance ratio from inventory components:
          expected_closing = opening + purchases - sold
          variance_ratio   = (actual_closing - expected_closing) / expected_closing
        """
        ...

    @overload
    def calculate(
        self,
        name: Literal["weighted_average"],
        ctx: Mapping[str, SupportsDecimal] | None = ...,
        *,
        policy: Policy | None = ...,
        allow_partial: bool = ...,
        values: Sequence[
            Union[int, float, str, Decimal, SupportsFloat, NoneType, FV, FV[U]]
        ],
        weights: Sequence[
            Union[
                int, float, str, Decimal, SupportsFloat, NoneType, FV, FV[Dimensionless]
            ]
        ],
    ) -> FV[U]:
        """\
        Weighted mean of `values` with `weights`.

        Behavior:
          - Uses SKIP mode: pairs with None in either value or weight are dropped.
          - Empty input or length mismatch → returns None (business rule).
          - Result unit follows the first non-None value's unit (else Dimensionless).
        """
        ...

    def calculate(
        self,
        name: str,
        ctx: Mapping[str, SupportsDecimal] | None = ...,
        *,
        policy: Policy | None = ...,
        allow_partial: bool = ...,
        **kwargs: SupportsDecimal,
    ) -> FV: ...
