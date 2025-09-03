"""
Ratio and percentage calculations.

This module contains calculations for ratios, percentages, and related mathematical operations.
All calculations use the Collection namespace for proper organization.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TypeVar

from ..exceptions import CalculationError
from ..policy import DEFAULT_POLICY, Policy
from ..policy_context import get_policy
from ..registry_collections import Collection
from ..units import Percent, Ratio, Unit
from ..value import FV

U = TypeVar("U", bound=Unit)

ratios = Collection("ratios")

# ── small local helpers ──────────────────────────────────────────────────────


def _resolve_policy(*fvs: FV | None) -> Policy:
    for fv in fvs:
        if isinstance(fv, FV) and fv.policy:
            return fv.policy
    return get_policy() or DEFAULT_POLICY


def _none_with_unit(unit, pol: Policy) -> FV:
    return FV(None, policy=pol, unit=unit)


def _zero_with_unit(unit, pol: Policy) -> FV:
    return FV(Decimal("0"), policy=pol, unit=unit)


def _is_zero(fv: FV) -> bool:
    d = fv.as_decimal()
    return (d is not None) and (d == 0)


def _is_non_positive(fv: FV) -> bool:
    d = fv.as_decimal()
    return (d is not None) and (d <= 0)


def _ratio_with_policy(value: FV, pol: Policy) -> FV[Ratio]:
    """Create a ratio FinancialValue without polluting the policy with percent_style='ratio'."""
    return FV(value._value, policy=pol, unit=Ratio, _is_percentage=False)


# ── calculations ─────────────────────────────────────────────────────────────


@ratios.calc("ratio", depends_on=("numerator", "denominator"))
def ratio(
    numerator: FV[U],
    denominator: FV[U],
) -> FV[Ratio]:
    """
    Simple ratio = numerator / denominator.

    Default behavior:
      - If denominator == 0 → return None (unless policy.arithmetic_strict, then raise).
      - None inputs propagate to None.
    """
    pol = _resolve_policy(numerator, denominator)
    if numerator.is_none() or denominator.is_none():
        return _none_with_unit(Ratio, pol)

    if _is_zero(denominator):
        if pol.arithmetic_strict:
            raise CalculationError("Ratio undefined for denominator == 0")
        return _none_with_unit(Ratio, pol)

    # FV division handles units (Money/Money -> Ratio, etc.).
    # We explicitly create a ratio to normalize the unit to Ratio for the public API.
    return _ratio_with_policy(numerator / denominator, pol)


@ratios.calc("percentage_of_total", depends_on=("part", "total"))
def percentage_of_total(
    part: FV[U],
    total: FV[U],
) -> FV[Percent]:
    """
    Percentage of total = (part / total), returned as Percent.

    Business rule: if total <= 0 → return 0% (not None).
    """
    pol = _resolve_policy(part, total)
    if part.is_none() or total.is_none():
        return _none_with_unit(Percent, pol)

    # Business rule: non-positive total -> 0%
    if _is_non_positive(total):
        return _zero_with_unit(Ratio, pol).as_percentage()

    return _ratio_with_policy(part / total, pol).as_percentage()


@ratios.calc("ratio_to_percentage", depends_on=("ratio",))
def ratio_to_percentage(ratio: FV[Ratio]) -> FV[Percent]:
    """
    Convert a ratio (0..1) to percent representation.
    """
    pol = _resolve_policy(ratio)
    if ratio.is_none():
        return _none_with_unit(Percent, pol)
    return ratio.as_percentage()


@ratios.calc("percentage_to_ratio", depends_on=("percentage",))
def percentage_to_ratio(percentage: FV[Percent]) -> FV[Ratio]:
    """
    Convert a percent value to a ratio (e.g., 25% -> 0.25).
    """
    pol = _resolve_policy(percentage)
    if percentage.is_none():
        return _none_with_unit(Ratio, pol)
    return _ratio_with_policy(percentage, pol)


@ratios.calc("cap_percentage", depends_on=("percentage", "max_percentage"))
def cap_percentage(
    percentage: FV[Percent],
    max_percentage: FV[Percent],
) -> FV[Percent]:
    """
    Cap a percentage at a maximum value.

    Returns None if either input is None.
    """
    pol = _resolve_policy(percentage, max_percentage)
    if percentage.is_none() or max_percentage.is_none():
        return _none_with_unit(Percent, pol)

    # Compare by value; respect policy for any strict-mode differences elsewhere.
    # Using FV comparisons would also work, but we keep this explicit for clarity.
    p = percentage.as_decimal()
    m = max_percentage.as_decimal()
    if p is None or m is None:
        return _none_with_unit(Percent, pol)

    return percentage if p <= m else max_percentage
