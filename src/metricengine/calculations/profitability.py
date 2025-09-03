"""
Profitability and margin calculations.

This module contains calculations for profit margins, profitability ratios, and related metrics.
All calculations use the Collection namespace for proper organization.
"""

from __future__ import annotations

from decimal import Decimal

from ..exceptions import CalculationError
from ..policy import DEFAULT_POLICY, Policy
from ..policy_context import get_policy
from ..registry_collections import Collection
from ..units import Dimensionless, Money, Percent, Ratio
from ..value import FV
from .rules import skip_if_negative_sales

profitability = Collection("profitability")

# ── small local helpers ──────────────────────────────────────────────────────


def _resolve_policy(*fvs: FV | None) -> Policy:
    for fv in fvs:
        if isinstance(fv, FV) and fv.policy:
            return fv.policy
    return get_policy() or DEFAULT_POLICY


def _none_with_unit(unit, pol: Policy) -> FV:
    return FV(None, policy=pol, unit=unit)


def _ratio_with_policy(value: FV, pol: Policy) -> FV[Ratio]:
    """Create a ratio FinancialValue without polluting the policy with percent_style='ratio'."""
    return FV(value._value, policy=pol, unit=Ratio, _is_percentage=False)


def _is_zero(fv: FV) -> bool:
    d = fv.as_decimal()
    return (d is not None) and (d == 0)


# ── core profitability amounts ───────────────────────────────────────────────


@profitability.calc("gross_profit", depends_on=("sales", "cost"))
@skip_if_negative_sales("sales")
def gross_profit(
    sales: FV[Money],
    cost: FV[Money],
) -> FV[Money]:
    """Gross profit = sales - cost"""
    pol = _resolve_policy(sales, cost)
    if sales.is_none() or cost.is_none():
        return _none_with_unit(Money, pol)
    return sales - cost


@profitability.calc("gross_profit_ex_tax", depends_on=("sales_ex_tax", "cost"))
@skip_if_negative_sales("sales_ex_tax")
def gross_profit_ex_tax(
    sales_ex_tax: FV[Money],
    cost: FV[Money],
) -> FV[Money]:
    """Gross profit (ex tax) = sales_ex_tax - cost"""
    pol = _resolve_policy(sales_ex_tax, cost)
    if sales_ex_tax.is_none() or cost.is_none():
        return _none_with_unit(Money, pol)
    return sales_ex_tax - cost


# ── gross margin (ratio + wrapper) ───────────────────────────────────────────


@profitability.calc("gross_margin_ratio", depends_on=("gross_profit", "sales"))
@skip_if_negative_sales("sales")
def gross_margin_ratio(
    gross_profit: FV[Money],
    sales: FV[Money],
) -> FV[Ratio]:
    """Gross margin ratio = gross_profit / sales"""
    pol = _resolve_policy(gross_profit, sales)
    if gross_profit.is_none() or sales.is_none():
        return _none_with_unit(Ratio, pol)
    if _is_zero(sales):
        if pol.arithmetic_strict:
            raise CalculationError("Gross margin undefined for sales == 0")
        return _none_with_unit(Ratio, pol)
    return _ratio_with_policy(gross_profit / sales, pol)


@profitability.calc("gross_margin_percentage", depends_on=("gross_margin_ratio",))
def gross_margin_percentage(gross_margin_ratio: FV[Ratio]) -> FV[Percent]:
    """Gross margin as percent (e.g., 0.35 -> '35%')."""
    pol = _resolve_policy(gross_margin_ratio)
    if gross_margin_ratio.is_none():
        return _none_with_unit(Percent, pol)
    return gross_margin_ratio.as_percentage()


@profitability.calc(
    "gross_margin_ratio_ex_tax", depends_on=("gross_profit_ex_tax", "sales_ex_tax")
)
@skip_if_negative_sales("sales_ex_tax")
def gross_margin_ratio_ex_tax(
    gross_profit_ex_tax: FV[Money],
    sales_ex_tax: FV[Money],
) -> FV[Ratio]:
    """Gross margin ratio (ex tax) = gross_profit_ex_tax / sales_ex_tax"""
    pol = _resolve_policy(gross_profit_ex_tax, sales_ex_tax)
    if gross_profit_ex_tax.is_none() or sales_ex_tax.is_none():
        return _none_with_unit(Ratio, pol)
    if _is_zero(sales_ex_tax):
        if pol.arithmetic_strict:
            raise CalculationError(
                "Gross margin (ex tax) undefined for sales_ex_tax == 0"
            )
        return _none_with_unit(Ratio, pol)
    return _ratio_with_policy(gross_profit_ex_tax / sales_ex_tax, pol)


@profitability.calc(
    "gross_margin_percentage_ex_tax", depends_on=("gross_margin_ratio_ex_tax",)
)
def gross_margin_percentage_ex_tax(
    gross_margin_ratio_ex_tax: FV[Ratio],
) -> FV[Percent]:
    """Gross margin (ex tax) as percent."""
    pol = _resolve_policy(gross_margin_ratio_ex_tax)
    if gross_margin_ratio_ex_tax.is_none():
        return _none_with_unit(Percent, pol)
    return gross_margin_ratio_ex_tax.as_percentage()


# ── cost ratios (ratio + wrappers) ───────────────────────────────────────────


@profitability.calc("cost_ratio", depends_on=("cost", "sales"))
@skip_if_negative_sales("sales")
def cost_ratio(cost: FV[Money], sales: FV[Money]) -> FV[Ratio]:
    """Cost ratio = cost / sales"""
    pol = _resolve_policy(cost, sales)
    if cost.is_none() or sales.is_none():
        return _none_with_unit(Ratio, pol)
    if _is_zero(sales):
        if pol.arithmetic_strict:
            raise CalculationError("Cost ratio undefined for sales == 0")
        return _none_with_unit(Ratio, pol)
    return _ratio_with_policy(cost / sales, pol)


@profitability.calc("cost_percent", depends_on=("cost_ratio",))
def cost_percent(cost_ratio: FV[Ratio]) -> FV[Percent]:
    """Cost as percent."""
    pol = _resolve_policy(cost_ratio)
    if cost_ratio.is_none():
        return _none_with_unit(Percent, pol)
    return cost_ratio.as_percentage()


@profitability.calc("cost_ratio_ex_tax", depends_on=("cost", "sales_ex_tax"))
@skip_if_negative_sales("sales_ex_tax")
def cost_ratio_ex_tax(
    cost: FV[Money],
    sales_ex_tax: FV[Money],
) -> FV[Ratio]:
    """Cost ratio (ex tax) = cost / sales_ex_tax"""
    pol = _resolve_policy(cost, sales_ex_tax)
    if cost.is_none() or sales_ex_tax.is_none():
        return _none_with_unit(Ratio, pol)
    if _is_zero(sales_ex_tax):
        if pol.arithmetic_strict:
            raise CalculationError(
                "Cost ratio (ex tax) undefined for sales_ex_tax == 0"
            )
        return _none_with_unit(Ratio, pol)
    return _ratio_with_policy(cost / sales_ex_tax, pol)


@profitability.calc("cost_percent_ex_tax", depends_on=("cost_ratio_ex_tax",))
def cost_percent_ex_tax(cost_ratio_ex_tax: FV[Ratio]) -> FV[Percent]:
    """Cost percent (ex tax)."""
    pol = _resolve_policy(cost_ratio_ex_tax)
    if cost_ratio_ex_tax.is_none():
        return _none_with_unit(Percent, pol)
    return cost_ratio_ex_tax.as_percentage()


# ── net profit & net margin ──────────────────────────────────────────────────


@profitability.calc("net_profit", depends_on=("revenue", "total_costs"))
def net_profit(
    revenue: FV[Money],
    total_costs: FV[Money],
) -> FV[Money]:
    """Net profit = revenue - total_costs"""
    pol = _resolve_policy(revenue, total_costs)
    if revenue.is_none() or total_costs.is_none():
        return _none_with_unit(Money, pol)
    return revenue - total_costs


@profitability.calc("net_margin_ratio", depends_on=("net_profit", "revenue"))
def net_margin_ratio(
    net_profit: FV[Money],
    revenue: FV[Money],
) -> FV[Ratio]:
    """Net margin ratio = net_profit / revenue"""
    pol = _resolve_policy(net_profit, revenue)
    if net_profit.is_none() or revenue.is_none():
        return _none_with_unit(Ratio, pol)
    if _is_zero(revenue):
        if pol.arithmetic_strict:
            raise CalculationError("Net margin undefined for revenue == 0")
        return _none_with_unit(Ratio, pol)
    return _ratio_with_policy(net_profit / revenue, pol)


@profitability.calc("net_margin_percentage", depends_on=("net_margin_ratio",))
def net_margin_percentage(net_margin_ratio: FV[Ratio]) -> FV[Percent]:
    """Net margin as percent."""
    pol = _resolve_policy(net_margin_ratio)
    if net_margin_ratio.is_none():
        return _none_with_unit(Percent, pol)
    return net_margin_ratio.as_percentage()


# ── tax-adjusted net margin ──────────────────────────────────────────────────


@profitability.calc("net_profit_with_tax", depends_on=("sales", "cost", "tax_rate"))
@skip_if_negative_sales("sales")
def net_profit_with_tax(
    sales: FV[Money],
    cost: FV[Money],
    tax_rate: FV[Percent],
) -> FV[Money]:
    """
    Net profit (tax-adjusted) = (sales / (1 + tax_rate)) - cost
    """
    pol = _resolve_policy(sales, cost, tax_rate)
    if sales.is_none() or cost.is_none() or tax_rate.is_none():
        return _none_with_unit(Money, pol)

    one = FV(Decimal("1"), policy=pol, unit=Dimensionless)
    denom = one + tax_rate
    if _is_zero(denom):
        if pol.arithmetic_strict:
            raise CalculationError(
                "net_profit_with_tax undefined when 1 + tax_rate == 0"
            )
        return _none_with_unit(Money, pol)

    return (sales / denom) - cost


@profitability.calc(
    "net_margin_with_tax_ratio", depends_on=("net_profit_with_tax", "sales_ex_tax")
)
@skip_if_negative_sales("sales_ex_tax")
def net_margin_with_tax_ratio(
    net_profit_with_tax: FV[Money],
    sales_ex_tax: FV[Money],
) -> FV[Ratio]:
    """Net margin (tax-adjusted) ratio = net_profit_with_tax / sales_ex_tax"""
    pol = _resolve_policy(net_profit_with_tax, sales_ex_tax)
    if net_profit_with_tax.is_none() or sales_ex_tax.is_none():
        return _none_with_unit(Ratio, pol)
    if _is_zero(sales_ex_tax):
        if pol.arithmetic_strict:
            raise CalculationError(
                "Net margin (tax-adjusted) undefined for sales_ex_tax == 0"
            )
        return _none_with_unit(Ratio, pol)
    return _ratio_with_policy(net_profit_with_tax / sales_ex_tax, pol)


@profitability.calc("net_margin_with_tax", depends_on=("net_margin_with_tax_ratio",))
def net_margin_with_tax(net_margin_with_tax_ratio: FV[Ratio]) -> FV[Percent]:
    """Net margin with tax as percent."""
    pol = _resolve_policy(net_margin_with_tax_ratio)
    if net_margin_with_tax_ratio.is_none():
        return _none_with_unit(Percent, pol)
    return net_margin_with_tax_ratio.as_percentage()


# ── cost % with tax info provided (ex-tax denominator) ───────────────────────


@profitability.calc("cost_ratio_with_tax", depends_on=("cost", "sales", "tax_rate"))
@skip_if_negative_sales("sales")
def cost_ratio_with_tax(
    cost: FV[Money],
    sales: FV[Money],
    tax_rate: FV[Percent],
) -> FV[Ratio]:
    """
    Cost ratio with tax info:
      denominator is sales ex tax, i.e. cost / (sales / (1 + tax_rate))
    """
    pol = _resolve_policy(cost, sales, tax_rate)
    if cost.is_none() or sales.is_none() or tax_rate.is_none():
        return _none_with_unit(Ratio, pol)

    one = FV(Decimal("1"), policy=pol, unit=Dimensionless)
    denom = one + tax_rate
    if _is_zero(denom):
        if pol.arithmetic_strict:
            raise CalculationError(
                "cost_ratio_with_tax undefined when 1 + tax_rate == 0"
            )
        return _none_with_unit(Ratio, pol)

    sales_ex = sales / denom
    if _is_zero(sales_ex):
        if pol.arithmetic_strict:
            raise CalculationError(
                "cost_ratio_with_tax undefined for sales_ex_tax == 0"
            )
        return _none_with_unit(Ratio, pol)

    return _ratio_with_policy(cost / sales_ex, pol)


@profitability.calc("cost_percentage_with_tax", depends_on=("cost_ratio_with_tax",))
def cost_percentage_with_tax(cost_ratio_with_tax: FV[Ratio]) -> FV[Percent]:
    """Cost percentage with tax."""
    pol = _resolve_policy(cost_ratio_with_tax)
    if cost_ratio_with_tax.is_none():
        return _none_with_unit(Percent, pol)
    return cost_ratio_with_tax.as_percentage()


# ── contribution margin ──────────────────────────────────────────────────────


@profitability.calc("contribution_margin", depends_on=("revenue", "variable_costs"))
def contribution_margin(
    revenue: FV[Money],
    variable_costs: FV[Money],
) -> FV[Money]:
    """Contribution margin = revenue - variable_costs"""
    pol = _resolve_policy(revenue, variable_costs)
    if revenue.is_none() or variable_costs.is_none():
        return _none_with_unit(Money, pol)
    return revenue - variable_costs


@profitability.calc(
    "contribution_margin_ratio_raw", depends_on=("contribution_margin", "revenue")
)
def contribution_margin_ratio_raw(
    contribution_margin: FV[Money],
    revenue: FV[Money],
) -> FV[Ratio]:
    """Contribution margin ratio = contribution_margin / revenue"""
    pol = _resolve_policy(contribution_margin, revenue)
    if contribution_margin.is_none() or revenue.is_none():
        return _none_with_unit(Ratio, pol)
    if _is_zero(revenue):
        if pol.arithmetic_strict:
            raise CalculationError("Contribution margin undefined for revenue == 0")
        return _none_with_unit(Ratio, pol)
    return _ratio_with_policy(contribution_margin / revenue, pol)


# Keep original public name returning percent:
@profitability.calc(
    "contribution_margin_ratio", depends_on=("contribution_margin_ratio_raw",)
)
def contribution_margin_ratio(contribution_margin_ratio_raw: FV[Ratio]) -> FV[Percent]:
    """Contribution margin ratio as percent."""
    pol = _resolve_policy(contribution_margin_ratio_raw)
    if contribution_margin_ratio_raw.is_none():
        return _none_with_unit(Percent, pol)
    return contribution_margin_ratio_raw.as_percentage()


# ── operating & EBITDA margins ───────────────────────────────────────────────


@profitability.calc(
    "operating_margin_ratio", depends_on=("operating_income", "revenue")
)
def operating_margin_ratio(
    operating_income: FV[Money],
    revenue: FV[Money],
) -> FV[Ratio]:
    """Operating margin ratio = operating_income / revenue"""
    pol = _resolve_policy(operating_income, revenue)
    if operating_income.is_none() or revenue.is_none():
        return _none_with_unit(Ratio, pol)
    if _is_zero(revenue):
        if pol.arithmetic_strict:
            raise CalculationError("Operating margin undefined for revenue == 0")
        return _none_with_unit(Ratio, pol)
    return _ratio_with_policy(operating_income / revenue, pol)


@profitability.calc("operating_margin", depends_on=("operating_margin_ratio",))
def operating_margin(operating_margin_ratio: FV[Ratio]) -> FV[Percent]:
    """Operating margin as percent."""
    pol = _resolve_policy(operating_margin_ratio)
    if operating_margin_ratio.is_none():
        return _none_with_unit(Percent, pol)
    return operating_margin_ratio.as_percentage()


@profitability.calc("ebitda_margin_ratio", depends_on=("ebitda", "revenue"))
def ebitda_margin_ratio(
    ebitda: FV[Money],
    revenue: FV[Money],
) -> FV[Ratio]:
    """EBITDA margin ratio = ebitda / revenue"""
    pol = _resolve_policy(ebitda, revenue)
    if ebitda.is_none() or revenue.is_none():
        return _none_with_unit(Ratio, pol)
    if _is_zero(revenue):
        if pol.arithmetic_strict:
            raise CalculationError("EBITDA margin undefined for revenue == 0")
        return _none_with_unit(Ratio, pol)
    return _ratio_with_policy(ebitda / revenue, pol)


@profitability.calc("ebitda_margin", depends_on=("ebitda_margin_ratio",))
def ebitda_margin(ebitda_margin_ratio: FV[Ratio]) -> FV[Percent]:
    """EBITDA margin as percent."""
    pol = _resolve_policy(ebitda_margin_ratio)
    if ebitda_margin_ratio.is_none():
        return _none_with_unit(Percent, pol)
    return ebitda_margin_ratio.as_percentage()


# ── ROI (ratio + wrapper) ───────────────────────────────────────────────────


@profitability.calc(
    "roi_ratio", depends_on=("gain_from_investment", "cost_of_investment")
)
def roi_ratio(
    gain_from_investment: FV[Money],
    cost_of_investment: FV[Money],
) -> FV[Ratio]:
    """ROI ratio = gain_from_investment / cost_of_investment"""
    pol = _resolve_policy(gain_from_investment, cost_of_investment)
    if gain_from_investment.is_none() or cost_of_investment.is_none():
        return _none_with_unit(Ratio, pol)
    if _is_zero(cost_of_investment):
        if pol.arithmetic_strict:
            raise CalculationError("ROI undefined for cost_of_investment == 0")
        return _none_with_unit(Ratio, pol)
    return _ratio_with_policy(gain_from_investment / cost_of_investment, pol)


@profitability.calc("roi", depends_on=("roi_ratio",))
def roi(roi_ratio: FV[Ratio]) -> FV[Percent]:
    """ROI as percent."""
    pol = _resolve_policy(roi_ratio)
    if roi_ratio.is_none():
        return _none_with_unit(Percent, pol)
    return roi_ratio.as_percentage()
