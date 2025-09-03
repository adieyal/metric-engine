"""
Unit economics and per-unit calculations.

This module contains calculations for unit economics, per-unit metrics, and break-even analysis.
All calculations use the Collection namespace for proper organization.
"""

from __future__ import annotations

from ..exceptions import CalculationError
from ..policy import DEFAULT_POLICY, Policy
from ..policy_context import get_policy
from ..registry_collections import Collection
from ..units import Dimensionless, Money
from ..value import FV

unit_economics = Collection("unit_economics")

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


def _is_non_positive(fv: FV) -> bool:
    d = fv.as_decimal()
    return (d is not None) and (d <= 0)


# ── calculations ─────────────────────────────────────────────────────────────


@unit_economics.calc("revenue_per_unit", depends_on=("total_revenue", "units_sold"))
def revenue_per_unit(
    total_revenue: FV[Money],
    units_sold: FV[Dimensionless],
) -> FV[Money]:
    """
    Revenue per unit = total_revenue / units_sold
    """
    pol = _resolve_policy(total_revenue, units_sold)
    if total_revenue.is_none() or units_sold.is_none():
        return _none_with_unit(Money, pol)

    if _is_zero(units_sold):
        if pol.arithmetic_strict:
            raise CalculationError("revenue_per_unit undefined for units_sold == 0")
        return _none_with_unit(Money, pol)

    return total_revenue / units_sold


@unit_economics.calc("cost_per_unit", depends_on=("total_cost", "units"))
def cost_per_unit(
    total_cost: FV[Money],
    units: FV[Dimensionless],
) -> FV[Money]:
    """
    Cost per unit = total_cost / units
    """
    pol = _resolve_policy(total_cost, units)
    if total_cost.is_none() or units.is_none():
        return _none_with_unit(Money, pol)

    if _is_zero(units):
        if pol.arithmetic_strict:
            raise CalculationError("cost_per_unit undefined for units == 0")
        return _none_with_unit(Money, pol)

    return total_cost / units


@unit_economics.calc("profit_per_unit", depends_on=("total_profit", "units_sold"))
def profit_per_unit(
    total_profit: FV[Money],
    units_sold: FV[Dimensionless],
) -> FV[Money]:
    """
    Profit per unit = total_profit / units_sold
    """
    pol = _resolve_policy(total_profit, units_sold)
    if total_profit.is_none() or units_sold.is_none():
        return _none_with_unit(Money, pol)

    if _is_zero(units_sold):
        if pol.arithmetic_strict:
            raise CalculationError("profit_per_unit undefined for units_sold == 0")
        return _none_with_unit(Money, pol)

    return total_profit / units_sold


@unit_economics.calc(
    "break_even_point",
    depends_on=("fixed_costs", "price_per_unit", "variable_cost_per_unit"),
)
def break_even_point(
    fixed_costs: FV[Money],
    price_per_unit: FV[Money],
    variable_cost_per_unit: FV[Money],
) -> FV[Dimensionless]:
    """
    Break-even point (units) = fixed_costs / (price_per_unit - variable_cost_per_unit)

    Returns a Dimensionless count of units (not a ratio).
    """
    pol = _resolve_policy(fixed_costs, price_per_unit, variable_cost_per_unit)
    if (
        fixed_costs.is_none()
        or price_per_unit.is_none()
        or variable_cost_per_unit.is_none()
    ):
        return _none_with_unit(Dimensionless, pol)

    contrib = price_per_unit - variable_cost_per_unit

    # Domain: contribution per unit must be > 0
    if contrib.is_none() or _is_non_positive(contrib):
        if pol.arithmetic_strict:
            raise CalculationError(
                "break_even_point undefined when price_per_unit - variable_cost_per_unit <= 0"
            )
        return _none_with_unit(Dimensionless, pol)

    # Money / Money returns Ratio; we want a count (dimensionless).
    ratio_units = fixed_costs / contrib
    if ratio_units.is_none():
        return _none_with_unit(Dimensionless, pol)

    # Re-wrap value as Dimensionless (avoid private attrs; use as_decimal())
    return FV(ratio_units.as_decimal(), policy=pol, unit=Dimensionless)
