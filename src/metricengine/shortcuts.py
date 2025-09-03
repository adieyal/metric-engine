"""Convenience helper functions for the Metric Engine."""

from __future__ import annotations

from collections.abc import Iterable

from .registry import deps as reg_deps
from .registry import is_registered


def inputs_needed_for(targets: Iterable[str]) -> set[str]:
    """
    Determine base inputs needed for the given targets by walking dependencies.

    A "base input" is any dependency name that is not a registered calculation.
    Registered calculations that have no dependencies are *not* counted as inputs.
    """
    todo: set[str] = set(targets)
    needed: set[str] = set()
    visited: set[str] = set()

    while todo:
        name = todo.pop()
        if name in visited:
            continue
        visited.add(name)

        if not is_registered(name):
            needed.add(name)
            continue

        dep_names = reg_deps(name)  # set[str]
        if not dep_names:
            # A registered calc with no deps: no base inputs required for it.
            continue

        todo.update(dep_names)

    return needed


def _expand_graph(
    targets: Iterable[str],
) -> tuple[set[str], set[str], dict[str, set[str]]]:
    """
    Expand the dependency graph reachable from targets.

    Returns:
        registered_nodes: all registered calc names reachable from targets
        base_inputs: names that are not registered (leaf inputs)
        edges: mapping registered name -> its dependency set (names)
    """
    stack: set[str] = set(targets)
    registered_nodes: set[str] = set()
    base_inputs: set[str] = set()
    edges: dict[str, set[str]] = {}

    while stack:
        name = stack.pop()
        if is_registered(name):
            if name in registered_nodes:
                continue
            registered_nodes.add(name)
            d = reg_deps(name)
            edges[name] = set(d)
            stack.update(d)
        else:
            base_inputs.add(name)

    return registered_nodes, base_inputs, edges


def can_calculate(targets: Iterable[str], available: Iterable[str]) -> bool:
    """
    Return True iff all targets can be computed from the given available inputs.

    Handles:
      - missing inputs
      - chains of dependencies
      - cycles (returns False even if no inputs are missing)
    """
    targets_set = set(targets)
    available_set = set(available)

    regs, base_inputs, edges = _expand_graph(targets_set)

    # If any base inputs are required but missing, we might still have zero-dep calcs
    # but overall cannot compute the targets unless all needed are present.
    missing = base_inputs - available_set

    # Resolve registered nodes whose deps are satisfied by known names.
    known: set[str] = set(available_set) | (base_inputs - missing)
    unresolved: set[str] = set(regs)

    progressed = True
    while progressed and unresolved:
        progressed = False
        for node in list(unresolved):
            deps_ok = True
            for d in edges.get(node, ()):
                # If dep is a registered calc, it must itself be resolved (in known).
                # If dep is a base (unregistered), it must be in known (i.e., available).
                if is_registered(d):
                    if d not in known:
                        deps_ok = False
                        break
                else:
                    if d not in known:
                        deps_ok = False
                        break
            if deps_ok:
                known.add(node)
                unresolved.remove(node)
                progressed = True

    # All targets are computable if every target (registered or not) is in 'known'.
    # For unregistered targets, being in 'known' means it's an available base input.
    for t in targets_set:
        if is_registered(t):
            if t not in known:
                return False
        else:
            if t not in known:
                return False

    # If we got here, all targets are known.
    # Still ensure no cycles blocked us (unresolved non-targets left are ok only if they aren't needed).
    return True if not missing else False


def missing_inputs_for(targets: Iterable[str], available: Iterable[str]) -> set[str]:
    """
    Return the set of missing base inputs required to calculate the targets.

    Note:
      - In the presence of pure cycles with no base inputs, this returns an empty set,
        but `can_calculate(...)` will still return False.
    """
    targets_set = set(targets)
    available_set = set(available)
    needed = inputs_needed_for(targets_set)
    return needed - available_set
