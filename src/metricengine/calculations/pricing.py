"""
Pricing and tax-related calculations.

This module contains calculations for pricing, tax handling, and markup/discount operations.
All calculations use the Collection namespace for proper organization.
"""

from __future__ import annotations

from decimal import Decimal

from ..exceptions import CalculationError
from ..policy import DEFAULT_POLICY, Policy
from ..policy_context import get_policy
from ..registry_collections import Collection
from ..units import Dimensionless, Money, Percent, Ratio  # phantom units
from ..value import FV
from .rules import skip_if_negative_sales

pricing = Collection("pricing")

# ── small local helpers ──────────────────────────────────────────────────────


def _resolve_policy(*fvs: FV | None) -> Policy:
    for fv in fvs:
        if isinstance(fv, FV) and fv.policy:
            return fv.policy
    return get_policy() or DEFAULT_POLICY


def _none_with_unit(unit, pol: Policy) -> FV:
    return FV(None, policy=pol, unit=unit)


def _is_zero(fv: FV) -> bool:
    d = fv.as_decimal()
    return (d is not None) and (d == 0)


def _ratio_with_policy(value: FV, pol: Policy) -> FV[Ratio]:
    """Create a ratio FinancialValue without polluting the policy with percent_style='ratio'."""
    return FV(value._value, policy=pol, unit=Ratio, _is_percentage=False)


# ── calculations ─────────────────────────────────────────────────────────────


@pricing.calc("total_cost", depends_on=("unit_cost", "quantity"))
def total_cost(
    unit_cost: FV[Money],
    quantity: FV[Dimensionless],
) -> FV[Money]:
    """
    Total cost = unit_cost * quantity
    """
    pol = _resolve_policy(unit_cost, quantity)
    if unit_cost.is_none() or quantity.is_none():
        return _none_with_unit(Money, pol)
    return unit_cost * quantity


@pricing.calc("sales_ex_tax", depends_on=("sales", "tax_rate"))
@skip_if_negative_sales("sales")
def sales_ex_tax(
    sales: FV[Money],
    tax_rate: FV[Percent],  # tax rate as percent/ratio (e.g., 10% -> 0.10)
) -> FV[Money]:
    """
    Sales excluding tax = sales / (1 + tax_rate)
    """
    pol = _resolve_policy(sales, tax_rate)
    if sales.is_none() or tax_rate.is_none():
        return _none_with_unit(Money, pol)

    one = FV(Decimal("1"), policy=pol, unit=Dimensionless)
    denom = one + tax_rate
    if _is_zero(denom):
        if pol.arithmetic_strict:
            raise CalculationError("sales_ex_tax undefined when 1 + tax_rate == 0")
        return _none_with_unit(Money, pol)

    return sales / denom


@pricing.calc("sales_with_tax", depends_on=("sales_ex_tax", "tax_rate"))
@skip_if_negative_sales("sales_ex_tax")
def sales_with_tax(
    sales_ex_tax: FV[Money],
    tax_rate: FV[Percent],
) -> FV[Money]:
    """
    Sales including tax = sales_ex_tax * (1 + tax_rate)
    """
    pol = _resolve_policy(sales_ex_tax, tax_rate)
    if sales_ex_tax.is_none() or tax_rate.is_none():
        return _none_with_unit(Money, pol)

    one = FV(Decimal("1"), policy=pol, unit=Dimensionless)
    return sales_ex_tax * (one + tax_rate)


@pricing.calc("tax_amount", depends_on=("sales", "tax_rate"))
@skip_if_negative_sales("sales")
def tax_amount(
    sales: FV[Money],
    tax_rate: FV[Percent],
) -> FV[Money]:
    """
    Tax amount = sales - (sales / (1 + tax_rate))
    """
    pol = _resolve_policy(sales, tax_rate)
    if sales.is_none() or tax_rate.is_none():
        return _none_with_unit(Money, pol)

    one = FV(Decimal("1"), policy=pol, unit=Dimensionless)
    denom = one + tax_rate
    if _is_zero(denom):
        if pol.arithmetic_strict:
            raise CalculationError("tax_amount undefined when 1 + tax_rate == 0")
        return _none_with_unit(Money, pol)

    return sales - (sales / denom)


@pricing.calc("price_ex_tax", depends_on=("price_inc_tax", "tax_rate"))
def price_ex_tax(
    price_inc_tax: FV[Money],
    tax_rate: FV[Percent],
) -> FV[Money]:
    """
    Price excluding tax = price_inc_tax / (1 + tax_rate)
    """
    pol = _resolve_policy(price_inc_tax, tax_rate)
    if price_inc_tax.is_none() or tax_rate.is_none():
        return _none_with_unit(Money, pol)

    one = FV(Decimal("1"), policy=pol, unit=Dimensionless)
    denom = one + tax_rate
    if _is_zero(denom):
        if pol.arithmetic_strict:
            raise CalculationError("price_ex_tax undefined when 1 + tax_rate == 0")
        return _none_with_unit(Money, pol)

    return price_inc_tax / denom


@pricing.calc("markup_ratio", depends_on=("cost", "selling_price"))
def markup_ratio(
    cost: FV[Money],
    selling_price: FV[Money],
) -> FV[Ratio]:
    """
    Markup ratio = (selling_price - cost) / cost
    """
    pol = _resolve_policy(cost, selling_price)
    if cost.is_none() or selling_price.is_none():
        return _none_with_unit(Ratio, pol)

    if _is_zero(cost):
        if pol.arithmetic_strict:
            raise CalculationError("markup ratio undefined for cost == 0")
        return _none_with_unit(Ratio, pol)

    return _ratio_with_policy((selling_price - cost) / cost, pol)


@pricing.calc("markup_percentage", depends_on=("markup_ratio",))
def markup_percentage(markup_ratio: FV[Ratio]) -> FV[Percent]:
    """
    Markup as percent (e.g., 0.25 -> '25%').
    """
    pol = _resolve_policy(markup_ratio)
    if markup_ratio.is_none():
        return _none_with_unit(Percent, pol)
    return markup_ratio.as_percentage()


@pricing.calc("discount_ratio", depends_on=("original_price", "discounted_price"))
def discount_ratio(
    original_price: FV[Money],
    discounted_price: FV[Money],
) -> FV[Ratio]:
    """
    Discount ratio = (original_price - discounted_price) / original_price
    """
    pol = _resolve_policy(original_price, discounted_price)
    if original_price.is_none() or discounted_price.is_none():
        return _none_with_unit(Ratio, pol)

    if _is_zero(original_price):
        if pol.arithmetic_strict:
            raise CalculationError("discount ratio undefined for original_price == 0")
        return _none_with_unit(Ratio, pol)

    return _ratio_with_policy((original_price - discounted_price) / original_price, pol)


@pricing.calc("discount_percentage", depends_on=("discount_ratio",))
def discount_percentage(discount_ratio: FV[Ratio]) -> FV[Percent]:
    """
    Discount as percent (e.g., 0.20 -> '20%').
    """
    pol = _resolve_policy(discount_ratio)
    if discount_ratio.is_none():
        return _none_with_unit(Percent, pol)
    return discount_ratio.as_percentage()
