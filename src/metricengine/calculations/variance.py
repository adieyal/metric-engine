"""
Variance and analysis calculations.

This module contains calculations for variance analysis, percentage changes, and related metrics.
All calculations use the Collection namespace for proper organization.
"""

from __future__ import annotations

from typing import TypeVar

from ..exceptions import CalculationError
from ..policy import DEFAULT_POLICY, Policy
from ..policy_context import get_policy
from ..registry_collections import Collection
from ..units import Money, Percent, Ratio, Unit
from ..value import FV

variance = Collection("variance")

U = TypeVar("U", bound=Unit)

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


# ── variance amount ──────────────────────────────────────────────────────────


@variance.calc("variance_amount", depends_on=("actual", "expected"))
def variance_amount(
    actual: FV[U],
    expected: FV[U],
) -> FV[U]:
    """
    Variance amount = actual - expected
    """
    pol = _resolve_policy(actual, expected)
    if actual.is_none() or expected.is_none():
        return _none_with_unit(
            actual.unit if not actual.is_none() else expected.unit, pol
        )
    return actual - expected


# ── variance ratio + wrapper ─────────────────────────────────────────────────


@variance.calc("variance_ratio", depends_on=("actual", "expected"))
def variance_ratio(
    actual: FV[U],
    expected: FV[U],
) -> FV[Ratio]:
    """
    Variance ratio = (actual - expected) / expected
    """
    pol = _resolve_policy(actual, expected)
    if actual.is_none() or expected.is_none():
        return _none_with_unit(Ratio, pol)
    if _is_zero(expected):
        if pol.arithmetic_strict:
            raise CalculationError("Variance ratio undefined for expected == 0")
        return _none_with_unit(Ratio, pol)
    return _ratio_with_policy((actual - expected) / expected, pol)


@variance.calc("variance_percentage", depends_on=("variance_ratio",))
def variance_percentage(variance_ratio: FV[Ratio]) -> FV[Percent]:
    """
    Variance as percent (positive = over, negative = under).
    """
    pol = _resolve_policy(variance_ratio)
    if variance_ratio.is_none():
        return _none_with_unit(Percent, pol)
    return variance_ratio.as_percentage()


# ── percentage change (old→new) ratio + wrapper ──────────────────────────────


@variance.calc("percentage_change_ratio", depends_on=("old_value", "new_value"))
def percentage_change_ratio(
    old_value: FV[U],
    new_value: FV[U],
) -> FV[Ratio]:
    """
    Percentage change (ratio) = (new_value - old_value) / old_value
    """
    pol = _resolve_policy(old_value, new_value)
    if old_value.is_none() or new_value.is_none():
        return _none_with_unit(Ratio, pol)
    if _is_zero(old_value):
        if pol.arithmetic_strict:
            raise CalculationError("Percentage change undefined for old_value == 0")
        return _none_with_unit(Ratio, pol)
    return _ratio_with_policy((new_value - old_value) / old_value, pol)


@variance.calc("percentage_change", depends_on=("percentage_change_ratio",))
def percentage_change(percentage_change_ratio: FV[Ratio]) -> FV[Percent]:
    """
    Percentage change as percent (e.g., 0.20 -> '20%').
    """
    pol = _resolve_policy(percentage_change_ratio)
    if percentage_change_ratio.is_none():
        return _none_with_unit(Percent, pol)
    return percentage_change_ratio.as_percentage()


# ── components-based variance ratio + wrapper ────────────────────────────────


@variance.calc(
    "variance_ratio_from_components",
    depends_on=("actual_closing", "opening", "purchases", "sold"),
)
def variance_ratio_from_components(
    actual_closing: FV[Money],
    opening: FV[Money],
    purchases: FV[Money],
    sold: FV[Money],
) -> FV[Ratio]:
    """
    Variance ratio from inventory components:
      expected_closing = opening + purchases - sold
      variance_ratio   = (actual_closing - expected_closing) / expected_closing
    """
    pol = _resolve_policy(actual_closing, opening, purchases, sold)
    if (
        actual_closing.is_none()
        or opening.is_none()
        or purchases.is_none()
        or sold.is_none()
    ):
        return _none_with_unit(Ratio, pol)

    expected_closing = opening + purchases - sold
    if expected_closing.is_none() or _is_zero(expected_closing):
        if pol.arithmetic_strict:
            raise CalculationError("Variance ratio undefined for expected_closing == 0")
        return _none_with_unit(Ratio, pol)

    return _ratio_with_policy(
        (actual_closing - expected_closing) / expected_closing, pol
    )


@variance.calc(
    "variance_percentage_from_components",
    depends_on=("variance_ratio_from_components",),
)
def variance_percentage_from_components(
    vrc: FV[Ratio],
) -> FV[Percent]:
    """
    Variance (from components) as percent.
    """
    pol = _resolve_policy(vrc)
    if vrc.is_none():
        return _none_with_unit(Percent, pol)
    return vrc.as_percentage()
