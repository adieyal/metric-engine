from __future__ import annotations

from collections.abc import Iterable, Sequence

from .exceptions import CalculationError
from .null_behaviour import NullReductionMode, get_nulls
from .policy import Policy
from .policy_context import PolicyResolution, get_policy, use_policy_resolution
from .units import Dimensionless
from .utils import SupportsDecimal
from .value import FinancialValue as FV


def _active_policy(fallback: Policy | None = None) -> Policy:
    """
    Return a non-None policy: prefer ambient, else provided fallback, else DEFAULT_POLICY.
    Late-import DEFAULT_POLICY to avoid circulars at package import time.
    """
    pol = get_policy()
    if pol is not None:
        return pol
    if fallback is not None:
        return fallback
    from .policy import DEFAULT_POLICY  # late import

    return DEFAULT_POLICY


def _is_noneish(x: FV | None | object) -> bool:
    return (x is None) or (isinstance(x, FV) and x.is_none())


def _pick_policy_for_items(
    items: Iterable[SupportsDecimal],
    explicit_policy: Policy | None = None,
) -> Policy:
    """
    Choose a concrete Policy:
      1) explicit_policy (if provided) - takes precedence
      2) First non-None FV's policy
      3) Else active/ambient (or DEFAULT)
    """
    # Explicit policy takes precedence
    if explicit_policy is not None:
        return explicit_policy

    for x in items:
        if isinstance(x, FV) and not x.is_none():
            return x.policy
        if (x is not None) and not isinstance(x, FV):
            # first primitive value: use active/default
            return _active_policy()
    return _active_policy()


def _pick_unit_for_items(items: Iterable[SupportsDecimal]) -> type:
    """First non-None FV's unit; otherwise Dimensionless."""
    for x in items:
        if isinstance(x, FV) and not x.is_none():
            return x.unit
    return Dimensionless


def _to_fv(x: SupportsDecimal, *, policy: Policy, unit: type) -> FV:
    """Coerce primitive or FV to FV with the chosen policy/unit."""
    return x if isinstance(x, FV) else FV(x, policy=policy, unit=unit)


def fv_sum(
    items: Sequence[SupportsDecimal],
    *,
    mode: NullReductionMode | None = None,
    policy: Policy | None = None,
) -> FV:
    mode = mode or get_nulls().reduction
    seq = list(items)

    result_policy = _pick_policy_for_items(seq, explicit_policy=policy)
    result_unit = _pick_unit_for_items(seq)

    total = FV.zero(result_policy, unit=result_unit)

    saw_none = False
    saw_value = False

    # Preserve accumulator's policy
    with use_policy_resolution(PolicyResolution.LEFT_OPERAND):
        for x in seq:
            if _is_noneish(x):
                saw_none = True
                if mode is NullReductionMode.RAISE:
                    raise CalculationError("Reduction encountered None")
                continue
            total = total + _to_fv(x, policy=result_policy, unit=result_unit)
            saw_value = True

    if mode is NullReductionMode.PROPAGATE and saw_none:
        return FV.none(result_policy)

    if mode is NullReductionMode.SKIP:
        return total if saw_value else FV.none(result_policy)

    if mode is NullReductionMode.ZERO:
        # sum([] of None) ⇒ 0 per your test note
        return total

    # Fallback behaves like SKIP
    return total if saw_value else FV.none(result_policy)


def fv_mean(
    items: Iterable[SupportsDecimal],
    *,
    mode: NullReductionMode | None = None,
    policy: Policy | None = None,
) -> FV:
    mode = mode or get_nulls().reduction
    seq = list(items)

    result_policy = _pick_policy_for_items(seq, explicit_policy=policy)
    result_unit = _pick_unit_for_items(seq)

    if mode is NullReductionMode.RAISE:
        if any(_is_noneish(x) for x in seq):
            raise CalculationError("Reduction encountered None")

    if mode is NullReductionMode.PROPAGATE:
        if any(_is_noneish(x) for x in seq):
            return FV.none(result_policy)
        n = len(seq)
        if n == 0:
            return FV.none(result_policy)
        s = fv_sum(seq, mode=NullReductionMode.SKIP, policy=result_policy)
        with use_policy_resolution(PolicyResolution.LEFT_OPERAND):
            return s / FV(n, policy=result_policy, unit=Dimensionless)

    if mode is NullReductionMode.SKIP:
        non_nulls: list[FV] = [
            _to_fv(x, policy=result_policy, unit=result_unit)
            for x in seq
            if not _is_noneish(x)
        ]
        if not non_nulls:
            return FV.none(result_policy)
        s = fv_sum(non_nulls, mode=NullReductionMode.SKIP, policy=result_policy)
        if s == 0:
            return FV.zero(s.policy, unit=result_unit)
        with use_policy_resolution(PolicyResolution.LEFT_OPERAND):
            return s / FV(len(non_nulls), policy=result_policy, unit=Dimensionless)

    if mode is NullReductionMode.ZERO:
        n = len(seq)
        if n == 0:
            return FV.none(result_policy)
        if all(_is_noneish(x) for x in seq):
            # explicit test expectation
            return FV.none(result_policy)
        s = fv_sum(seq, mode=NullReductionMode.ZERO, policy=result_policy)
        with use_policy_resolution(PolicyResolution.LEFT_OPERAND):
            return s / FV(n, policy=result_policy, unit=Dimensionless)

    # Fallback → SKIP behaviour
    non_nulls: list[FV] = [
        _to_fv(x, policy=result_policy, unit=result_unit)
        for x in seq
        if not _is_noneish(x)
    ]
    if not non_nulls:
        return FV.none(result_policy)
    s = fv_sum(non_nulls, mode=NullReductionMode.SKIP, policy=result_policy)
    with use_policy_resolution(PolicyResolution.LEFT_OPERAND):
        return s / FV(len(non_nulls), policy=result_policy, unit=Dimensionless)


def fv_weighted_mean(
    items: Iterable[tuple[SupportsDecimal, SupportsDecimal]],
    *,
    mode: NullReductionMode | None = None,
    policy: Policy | None = None,
) -> FV:
    """
    Weighted mean of values (v_i) with weights (w_i): sum(v_i * w_i) / sum(w_i).

    ZERO mode semantics:
      - Treat value None as 0 (weight still counts).
      - Treat weight None as 0 (pair contributes nothing).
    SKIP mode semantics:
      - Skip pairs where value or weight is None.
    PROPAGATE mode semantics:
      - Any None → propagate None (handled early).
    RAISE mode semantics:
      - Any None → raise (handled early).
    """
    mode = mode or get_nulls().reduction
    seq = list(items)

    values = [v for v, _ in seq]
    weights = [w for _, w in seq]

    result_policy = _pick_policy_for_items(values + weights, explicit_policy=policy)
    result_unit = _pick_unit_for_items(values)

    if mode is NullReductionMode.RAISE:
        if any(_is_noneish(x) for x in values + weights):
            raise CalculationError("Reduction encountered None")

    if mode is NullReductionMode.PROPAGATE:
        if any(_is_noneish(x) for x in values + weights):
            return FV.none(result_policy)
        if not seq:
            return FV.none(result_policy)

    valid_pairs: list[tuple[FV, FV]] = []
    for val, weight in seq:
        v_is_none = _is_noneish(val)
        w_is_none = _is_noneish(weight)

        if mode is NullReductionMode.SKIP:
            if v_is_none or w_is_none:
                continue
            v_fv = _to_fv(val, policy=result_policy, unit=result_unit)
            w_fv = _to_fv(weight, policy=result_policy, unit=Dimensionless)
            valid_pairs.append((v_fv, w_fv))
            continue

        if mode is NullReductionMode.ZERO:
            # value None → treat as 0 with weight included
            v_fv = (
                FV.zero(result_policy, unit=result_unit)
                if v_is_none
                else _to_fv(val, policy=result_policy, unit=result_unit)
            )
            # weight None → treat as 0 (drops pair contribution)
            w_fv = (
                FV.zero(result_policy, unit=Dimensionless)
                if w_is_none
                else _to_fv(weight, policy=result_policy, unit=Dimensionless)
            )
            # If weight becomes zero, this pair won't affect numerator nor denominator
            valid_pairs.append((v_fv, w_fv))
            continue

        # Fallback (SKIP-like): keep only fully valid pairs
        if not v_is_none and not w_is_none:
            v_fv = _to_fv(val, policy=result_policy, unit=result_unit)
            w_fv = _to_fv(weight, policy=result_policy, unit=Dimensionless)
            valid_pairs.append((v_fv, w_fv))

    if not valid_pairs:
        # In ZERO mode an all-None set ⇒ 0/0 → None by convention
        return FV.none(result_policy)

    weighted_sum = FV.zero(result_policy, unit=result_unit)
    total_weight = FV.zero(result_policy, unit=Dimensionless)

    with use_policy_resolution(PolicyResolution.LEFT_OPERAND):
        for v, w in valid_pairs:
            weighted_sum = weighted_sum + (v * w)
            total_weight = total_weight + w

        if total_weight == 0:
            return FV.none(result_policy)

        return weighted_sum / total_weight
