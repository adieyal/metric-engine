"""
Utility and helper calculations.

This module contains utility calculations, averages, and helper functions.
All calculations use the Collection namespace for proper organization.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import TypeVar

from ..null_behaviour import NullReductionMode
from ..policy import DEFAULT_POLICY, Policy
from ..policy_context import get_policy
from ..reductions import fv_mean, fv_weighted_mean
from ..registry_collections import Collection
from ..units import Dimensionless, Unit
from ..utils import SupportsDecimal
from ..value import FV

utilities = Collection("utilities")

U = TypeVar("U", bound=Unit)

# ── small local helpers ──────────────────────────────────────────────────────


def _resolve_policy_from_items(items: Iterable[object]) -> Policy:
    for x in items:
        if isinstance(x, FV) and x.policy:
            return x.policy
        if x is not None and not isinstance(x, FV):
            # raw value present → use ambient/default policy
            return get_policy() or DEFAULT_POLICY
    return get_policy() or DEFAULT_POLICY


def _first_unit_from_values(values: Iterable[object]):
    for x in values:
        if isinstance(x, FV) and not x.is_none():
            return x.unit
    return Dimensionless


def _none_with(unit, pol: Policy) -> FV:
    return FV(None, policy=pol, unit=unit)


# ── calculations ─────────────────────────────────────────────────────────────


@utilities.calc("average_value", depends_on=("values",))
def average_value(
    values: Sequence[SupportsDecimal | FV[U]],
) -> FV[U]:
    """
    Arithmetic mean of a sequence.

    Behavior:
      - Uses SKIP mode: None items are excluded from both sum and count.
      - Empty or all-None → returns None.
      - Result unit follows the first non-None item's unit (else Dimensionless).
    """
    if not values:
        pol = get_policy() or DEFAULT_POLICY
        unit = Dimensionless
        return _none_with(unit, pol)

    # Delegate to shared reducer (handles unit/policy resolution correctly)
    return fv_mean(values, mode=NullReductionMode.SKIP)


@utilities.calc("weighted_average", depends_on=("values", "weights"))
def weighted_average(
    values: Sequence[SupportsDecimal | FV[U]],
    weights: Sequence[SupportsDecimal | FV[Dimensionless]],
) -> FV[U]:
    """
    Weighted mean of `values` with `weights`.

    Behavior:
      - Uses SKIP mode: pairs with None in either value or weight are dropped.
      - Empty input or length mismatch → returns None (business rule).
      - Result unit follows the first non-None value's unit (else Dimensionless).
    """
    # Enforce business rule on basic shape before delegating
    if not values or not weights or len(values) != len(weights):
        pol = _resolve_policy_from_items(list(values) + list(weights))
        unit = _first_unit_from_values(values)
        return _none_with(unit, pol)

    pairs: list[
        tuple[SupportsDecimal | FV[U], SupportsDecimal | FV[Dimensionless]]
    ] = list(zip(values, weights))

    # Delegate to shared weighted reducer
    return fv_weighted_mean(pairs, mode=NullReductionMode.SKIP)
