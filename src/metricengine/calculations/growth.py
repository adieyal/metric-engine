"""
Growth and CAGR calculations.

This module defines growth-rate calculations using namespaced registration.
It returns ratios (0..1) by default for composability, with a separate
percent-returning wrapper if needed.
"""

from __future__ import annotations

from decimal import Context, Decimal, DivisionByZero, InvalidOperation, getcontext
from typing import TypeVar

from ..exceptions import CalculationError
from ..policy import DEFAULT_POLICY
from ..policy_context import get_policy
from ..registry_collections import Collection
from ..units import Dimensionless, Percent, Ratio, Unit  # phantom units
from ..value import FV

U = TypeVar("U", bound=Unit)

growth = Collection("growth")


@growth.calc("simple_growth_rate", depends_on=("initial_value", "final_value"))
def simple_growth_rate(
    initial_value: FV[U],
    final_value: FV[U],
) -> FV[Ratio]:
    """
    Simple growth rate as a ratio: (final - initial) / initial.

    Returns:
        FV[Ratio] in 0..1 (can be negative if shrinking), or None if inputs invalid.
    """
    pol = initial_value.policy or final_value.policy or get_policy() or DEFAULT_POLICY

    # Propagate None
    if initial_value.is_none() or final_value.is_none():
        return FV.none(pol).ratio()

    # Use raw decimals to avoid premature quantization
    i = initial_value._value  # internal raw Decimal or None
    f = final_value._value
    if i is None or f is None:
        return FV.none(pol).ratio()

    # Domain checks: initial must be non-zero (cannot divide by 0)
    if i == 0:
        if pol.arithmetic_strict:
            raise CalculationError("Simple growth undefined for initial_value == 0")
        return FV.none(pol).ratio()

    # Compute as Decimal, then wrap as Ratio
    g = (f - i) / i
    return FV(g, policy=pol, unit=Ratio)


@growth.calc(
    "compound_growth_rate", depends_on=("initial_value", "final_value", "periods")
)
def compound_growth_rate(
    initial_value: FV[U],
    final_value: FV[U],
    periods: FV[Dimensionless],
) -> FV[Ratio]:
    """
    Compound annual growth rate (CAGR) as a ratio (0..1):

        CAGR = exp( ln(final / initial) / periods ) - 1

    Notes:
        - Requires strictly positive initial, final, and periods.
        - Returns None on invalid inputs unless policy.arithmetic_strict, in which case raises.
    """
    pol = (
        initial_value.policy
        or final_value.policy
        or periods.policy
        or get_policy()
        or DEFAULT_POLICY
    )

    # Propagate None
    if initial_value.is_none() or final_value.is_none() or periods.is_none():
        return FV.none(pol).ratio()

    # Use raw decimals to avoid early rounding
    i = initial_value._value
    f = final_value._value
    n = periods._value
    if i is None or f is None or n is None:
        return FV.none(pol).ratio()

    # Domain: strictly positive
    if i <= 0 or f <= 0 or n <= 0:
        if pol.arithmetic_strict:
            raise CalculationError(
                "CAGR undefined for non-positive initial/final/periods"
            )
        return FV.none(pol).ratio()

    # High-precision Decimal ln/exp (avoid float pow fallback)
    ctx: Context = getcontext().copy()
    ctx.prec = max(ctx.prec, pol.decimal_places + 10, 28)  # headroom over display dp

    try:
        ratio = f / i  # Decimal > 0
        ln_ratio = ctx.ln(ratio)  # Decimal
        inv_n = ctx.divide(Decimal(1), n)  # Decimal
        growth_factor = ctx.exp(ln_ratio * inv_n)
        cagr = growth_factor - Decimal(1)
    except (InvalidOperation, DivisionByZero) as e:
        if pol.arithmetic_strict:
            raise CalculationError(f"CAGR computation failed: {e}") from e
        return FV.none(pol).ratio()

    return FV(cagr, policy=pol, unit=Ratio)


# Convenience wrapper returning percent
@growth.calc("compound_growth_rate_percent", depends_on=("compound_growth_rate",))
def compound_growth_rate_percent(compound_growth_rate: FV[Ratio]) -> FV[Percent]:
    """
    CAGR as a percent (e.g., 0.10 -> '10%').
    """
    pol = compound_growth_rate.policy or get_policy() or DEFAULT_POLICY
    if compound_growth_rate.is_none():
        return FV.none(pol).as_percentage()
    return compound_growth_rate.as_percentage()
