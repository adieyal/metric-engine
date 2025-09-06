"""Execution engine for financial calculations with DAG resolution."""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

from .exceptions import CalculationError, CircularDependencyError, MissingInputError
from .policy import DEFAULT_POLICY, Policy
from .policy_context import get_policy, use_policy
from .registry import deps, get, is_registered
from .utils import SupportsDecimal, to_decimal
from .value import FinancialValue

logger = logging.getLogger(__name__)


class Engine:
    """
    Execution engine for financial calculations.

    Builds dependency graphs, detects circular dependencies, caches results,
    and executes calculations in the correct order.
    """

    def __init__(self, default_policy: Policy | None = None):
        """
        Initialize the engine with an optional default policy.

        Args:
            default_policy: Default policy for calculations. Uses DEFAULT_POLICY if None.
        """
        self.default_policy: Policy = default_policy or DEFAULT_POLICY
        self.metric_policy: dict[str, Policy] = {}  # optional per-metric override

        # Ensure calculations are registered on engine creation
        try:
            from .calculations import load_all

            load_all()
        except Exception as e:
            # Don't silently ignore exceptions during development
            import warnings

            warnings.warn(f"Failed to load calculations: {e}", stacklevel=2)
            # Re-raise in debug mode for development
            if __debug__:
                raise

    def _choose_policy(self, name: str, override: Policy | None) -> Policy:
        """
        Choose a non-None policy with a single rule:
          explicit override > metric override > ambient > engine default > DEFAULT_POLICY
        """
        ambient = get_policy()
        return (
            override
            or self.metric_policy.get(name)
            or ambient
            or self.default_policy
            or DEFAULT_POLICY
        )

    def calculate(
        self,
        name: str,
        ctx: dict[str, SupportsDecimal] | None = None,
        *,
        policy: Policy | None = None,
        allow_partial: bool = False,
        **kwargs: SupportsDecimal,
    ) -> FinancialValue:
        """
        Calculate a target metric given a context of input values.

        The engine follows a "let calculations validate" philosophy:
        - None values propagate naturally through calculations
        - No need for defensive checks before calling calculate
        - Each calculation determines what inputs are valid
        - FinancialValue results can be passed directly to other calculations

        Args:
            name: Name of the calculation to compute
            ctx: Dictionary of input values (optional if using kwargs)
            policy: Optional policy to override default
            allow_partial: If True, return None on failure instead of raising
            **kwargs: Input values as keyword arguments (can include None)

        Returns:
            FinancialValue containing the result (may wrap None)

        Raises:
            MissingInputError: If required non-None inputs are missing
            CircularDependencyError: If circular dependencies are detected
            CalculationError: If calculation fails
        """
        # Merge ctx and kwargs, with kwargs taking precedence
        ctx = {} if ctx is None else dict(ctx)
        ctx.update(kwargs)

        effective_policy = self._choose_policy(name, policy)

        try:
            with use_policy(effective_policy):
                result = self._run_calc(name, ctx, allow_partial=allow_partial)

            if not isinstance(result, FinancialValue):
                result = FinancialValue(
                    None if result is None else to_decimal(result), effective_policy
                )
            return result

        except MissingInputError as exc:
            if allow_partial:
                logger.error(f"Calculation '{name}' failed: {exc}")
                return FinancialValue(None, effective_policy)
            raise

        except CircularDependencyError as exc:
            if allow_partial:
                logger.error(f"Calculation '{name}' failed: {exc}")
                return FinancialValue(None, effective_policy)
            raise

        except Exception as exc:
            if allow_partial:
                logger.error(f"Calculation '{name}' failed: {exc}")
                return FinancialValue(None, effective_policy)
            raise CalculationError(f"Error in calculation '{name}': {exc}") from exc

    def _run_calc(self, name: str, ctx: dict, *, allow_partial: bool = False):
        """
        Internal method to run a single calculation.

        This method handles the actual calculation execution and can be overridden
        by subclasses to customize calculation behavior.
        """
        # Delegate to calculate_many for consistency
        results = self.calculate_many({name}, ctx, allow_partial=allow_partial)
        result = results.get(name)

        # Add calculation-specific provenance if result is a FinancialValue
        if isinstance(result, FinancialValue) and result is not None:
            result = self._add_calculation_provenance(name, result, ctx)

        return result

    def _add_calculation_provenance(
        self, calc_name: str, result: FinancialValue, ctx: dict
    ) -> FinancialValue:
        """Add calculation-specific provenance to a result.

        Args:
            calc_name: Name of the calculation
            result: The calculated FinancialValue result
            ctx: Context dictionary with input names and values

        Returns:
            FinancialValue with calculation provenance
        """
        try:
            from .provenance import Provenance, hash_node
            from .provenance_config import (
                log_provenance_error,
                should_fail_on_error,
                should_track_calculations,
            )

            # Check if calculation tracking is enabled
            if not should_track_calculations():
                return result

            # Extract parent FinancialValues from context with error handling
            parents = []
            input_names = {}

            for key, value in ctx.items():
                try:
                    if isinstance(value, FinancialValue):
                        parents.append(value)
                        if hasattr(value, "_prov") and value._prov:
                            input_names[value._prov.id] = str(key)
                    else:
                        # Create a temporary FinancialValue for non-FV inputs (including None) to get provenance
                        try:
                            temp_fv = FinancialValue(value, policy=result.policy)
                            parents.append(temp_fv)
                            if hasattr(temp_fv, "_prov") and temp_fv._prov:
                                input_names[temp_fv._prov.id] = str(key)
                        except Exception as temp_error:
                            log_provenance_error(
                                temp_error,
                                "_add_calculation_provenance_temp_fv",
                                calculation=calc_name,
                                input_key=key,
                            )
                            # Continue without this input

                except Exception as input_error:
                    log_provenance_error(
                        input_error,
                        "_add_calculation_provenance_input",
                        calculation=calc_name,
                        input_key=key,
                    )
                    # Continue with other inputs

            # Create metadata with input names and calculation context
            try:
                meta = {"calculation": str(calc_name), "input_names": input_names}
            except Exception as meta_error:
                log_provenance_error(
                    meta_error,
                    "_add_calculation_provenance_meta",
                    calculation=calc_name,
                )
                meta = {"calculation": str(calc_name)}

            # Generate provenance ID for this calculation with error handling
            try:
                op = f"calc:{calc_name}"
                prov_id = hash_node(op, tuple(parents), result.policy, meta)
            except Exception as hash_error:
                log_provenance_error(
                    hash_error,
                    "_add_calculation_provenance_hash",
                    calculation=calc_name,
                )
                if should_fail_on_error():
                    raise
                return result  # Graceful degradation

            # Create new provenance record with error handling
            try:
                parent_ids = []
                for parent in parents:
                    try:
                        if hasattr(parent, "_prov") and parent._prov:
                            parent_ids.append(parent._prov.id)
                    except Exception as parent_error:
                        log_provenance_error(
                            parent_error,
                            "_add_calculation_provenance_parent_id",
                            calculation=calc_name,
                        )
                        # Continue with other parents

                prov = Provenance(
                    id=prov_id, op=op, inputs=tuple(parent_ids), meta=meta
                )

                # Return new FinancialValue with calculation provenance
                return FinancialValue(
                    result._value,
                    policy=result.policy,
                    unit=result.unit,
                    _is_percentage=result._is_percentage,
                    _prov=prov,
                )

            except Exception as prov_error:
                log_provenance_error(
                    prov_error,
                    "_add_calculation_provenance_create",
                    calculation=calc_name,
                )
                if should_fail_on_error():
                    raise
                return result  # Graceful degradation

        except ImportError:
            # Provenance module not available - graceful degradation
            return result
        except Exception as e:
            # Log unexpected errors
            try:
                from .provenance_config import (
                    log_provenance_error,
                    should_fail_on_error,
                )

                log_provenance_error(
                    e, "_add_calculation_provenance", calculation=calc_name
                )

                if should_fail_on_error():
                    raise
            except ImportError:
                pass

            # Graceful degradation - return original result if provenance fails
            return result

    def constant(self, value: int | float | Decimal | None) -> FinancialValue:
        """
        Create a constant FinancialValue.

        Args:
            value: The constant value to wrap
        """
        if value is None:
            return self.none()
        # use active policy for constants so they respect ambient/use_policy
        pol = get_policy() or self.default_policy or DEFAULT_POLICY
        return FinancialValue(to_decimal(value), pol)

    def zero(self) -> FinancialValue:
        """
        Create a zero FinancialValue.
        """
        pol = get_policy() or self.default_policy or DEFAULT_POLICY
        return FinancialValue(to_decimal(0), pol)

    def none(self) -> FinancialValue:
        """
        Create a None FinancialValue.
        """
        pol = get_policy() or self.default_policy or DEFAULT_POLICY
        return FinancialValue(None, pol)

    def calculate_many(
        self,
        targets: set[str],
        ctx: dict[str, Any] | None = None,
        *,
        policy: Policy | None = None,
        allow_partial: bool = False,
        **kwargs: Any,
    ) -> dict[str, FinancialValue]:
        """
        Resolve all targets in one pass with shared dependency resolution.

        Parameters
        ----------
        targets        : Set of metric names you want
        ctx           : Inputs you already have (optional if using kwargs)
        policy        : Optional Policy override
        allow_partial : If True, return what can be computed and
                       leave missing ones out instead of raising.
        **kwargs      : Input values as keyword arguments

        Returns
        -------
        Dictionary mapping metric name to FinancialValue

        Raises
        ------
        MissingInputError: If any targets cannot be computed (unless allow_partial=True)
        CircularDependencyError: If circular dependencies are detected
        CalculationError: If any calculation fails

        Examples:
            # Using context dict
            >>> results = engine.calculate_many(
            ...     {"gross_profit", "gross_margin_percentage"},
            ...     {"sales": 1000, "cost": 650}
            ... )

            # Using keyword arguments
            >>> results = engine.calculate_many(
            ...     {"gross_profit", "gross_margin_percentage"},
            ...     sales=1000, cost=650
            ... )
        """
        # Merge ctx and kwargs
        ctx = {} if ctx is None else dict(ctx)
        ctx.update(kwargs)

        # IMPORTANT: respect whichever policy is already active in context
        # (e.g., set by calculate()) when no explicit policy is given.
        batch_policy = policy or get_policy() or self.default_policy or DEFAULT_POLICY
        cache: dict[str, Any] = {}  # Can hold Decimal or lists

        # track invalid provided inputs during resolve()
        invalid_inputs: set[str] = set()

        def resolve(name: str, stack: tuple[str, ...] = ()) -> bool:
            """
            Recursively resolve a calculation and its dependencies.

            Args:
                name: Name of calculation to resolve
                stack: Current resolution stack for cycle detection

            Returns:
                True if successfully resolved, False otherwise
            """
            # Already resolved
            if name in cache:
                return True

            # Check for circular dependency
            if name in stack:
                raise CircularDependencyError(stack + (name,))

            # Base case: value provided in context
            if name in ctx:
                value = ctx[name]
                # Pass through sequences (calc decides what to do)
                if isinstance(value, (list, tuple)):
                    cache[name] = value
                    return True
                try:
                    if isinstance(value, FinancialValue):
                        cache[name] = value
                    else:
                        cache[name] = FinancialValue(to_decimal(value), batch_policy)
                    return True
                except (ValueError, TypeError, CalculationError) as exc:
                    # Convert input conversion errors to CalculationError
                    raise CalculationError(
                        f"Invalid input type for '{name}': {exc}"
                    ) from exc

            # Check if calculation is registered
            if not is_registered(name):
                return False

            # Resolve all dependencies first
            calculation_deps = deps(name)
            all_resolved = True

            for dep in calculation_deps:
                if not resolve(dep, stack + (name,)):
                    all_resolved = False

            # If any dependency failed, we can't compute this
            if not all_resolved:
                return False

            # Execute the calculation
            try:
                # before calling calc_func in resolve(...)
                calc_func = get(name)
                dep_values = {d: cache[d] for d in calculation_deps}

                # choose policy per metric
                pol_for_this = self._choose_policy(name, override=policy)

                with use_policy(pol_for_this):
                    result = calc_func(**dep_values)

                # store result; keep its own policy if it returns FV, else wrap with pol_for_this
                if isinstance(result, FinancialValue):
                    cache[name] = result
                else:
                    cache[name] = FinancialValue(to_decimal(result), pol_for_this)

                return True

            except Exception as exc:
                if allow_partial:
                    logger.warning(f"Calculation '{name}' failed: {exc}")
                    return False
                else:
                    raise CalculationError(
                        f"Error in calculation '{name}': {exc}"
                    ) from exc

        # Kick off resolution for each requested target and collect failed ones
        failed_targets = set()
        with use_policy(batch_policy):
            for target in targets:
                try:
                    if not resolve(target):
                        failed_targets.add(target)
                except CircularDependencyError:
                    raise  # Re-raise circular dependency errors immediately
                except CalculationError:
                    raise  # Re-raise calculation errors immediately

        # If any targets failed and partial results not allowed, analyze what's missing
        if failed_targets and not allow_partial:
            # Find the missing base inputs by analyzing what couldn't be resolved
            def find_missing(name: str, visited: set[str] | None = None) -> set[str]:
                if visited is None:
                    visited = set()

                if name in visited:
                    return set()
                visited.add(name)

                # If in cache, it was resolved successfully
                if name in cache:
                    return set()

                if name in ctx and name in invalid_inputs:
                    # Explicitly mark as invalid (not missing)
                    return set()

                # If in context but failed to convert, it's a bad input
                if name in ctx:
                    return {name}

                # If not registered, it's a missing input
                if not is_registered(name):
                    return {name}

                # For registered calculations, check dependencies
                missing_deps = set()
                for dep in deps(name):
                    missing_deps.update(find_missing(dep, visited))

                return missing_deps

            # build 'missing' as before
            all_missing = set()
            for target in failed_targets:
                all_missing.update(find_missing(target))

            details = []
            if all_missing:
                details.append("missing: " + ", ".join(sorted(all_missing)))
            if invalid_inputs:
                details.append("invalid: " + ", ".join(sorted(invalid_inputs)))

            if len(targets) == 1:
                only = next(iter(targets))
                raise MissingInputError(
                    f"Cannot compute '{only}' due to "
                    + ("; ".join(details) or "unspecified failure"),
                    sorted(all_missing),
                )

            # For multiple targets, include the failed target names
            failed_target_names = ", ".join(sorted(failed_targets))
            raise MissingInputError(
                f"Cannot compute targets [{failed_target_names}]. Details → "
                + "; ".join(details),
                sorted(all_missing),
            )

        # result collection
        result = {}
        for key in targets:
            if key in cache and key not in failed_targets:
                cached_result = cache[key]
                # Add calculation provenance if this is a registered calculation
                if is_registered(key) and isinstance(cached_result, FinancialValue):
                    result[key] = self._add_calculation_provenance(
                        key, cached_result, ctx
                    )
                else:
                    result[key] = cached_result  # should be FinancialValue already
        return result

    def set_metric_policy(self, name: str, policy: Policy) -> None:
        self.metric_policy[name] = policy

    def clear_metric_policy(self, name: str) -> None:
        self.metric_policy.pop(name, None)

    def get_dependencies(self, target: str) -> set[str]:
        """
        Get all dependencies (direct and transitive) for a calculation.

        Args:
            target: Name of the calculation

        Returns:
            Set of all dependency names

        Raises:
            CircularDependencyError: If circular dependencies detected
        """
        if not is_registered(target):
            raise CalculationError(f"Calculation '{target}' is not registered")

        all_deps: set[str] = set()
        visited: set[str] = set()

        def collect_deps(name: str, stack: tuple[str, ...] = ()) -> None:
            if name in stack:
                cycle = stack + (name,)
                raise CircularDependencyError(cycle)

            if name in visited:
                return

            visited.add(name)

            if is_registered(name):
                for dep in deps(name):
                    all_deps.add(dep)
                    collect_deps(dep, stack + (name,))

        collect_deps(target)
        return all_deps

    def validate_dependencies(self, target: str) -> tuple[set[str], set[str]]:
        """
        Validate dependencies for a calculation.

        Args:
            target: Name of the calculation to validate

        Returns:
            Tuple of (registered_deps, unregistered_deps)

        Raises:
            CircularDependencyError: If circular dependencies detected
        """
        all_deps = self.get_dependencies(target)
        registered = {dep for dep in all_deps if is_registered(dep)}
        unregistered = all_deps - registered
        return registered, unregistered

    def get_all_calculations(self) -> dict[str, dict[str, Any]]:
        """
        Get information about all registered calculations.

        Returns:
            Dict mapping calculation names to their metadata including:
            - function: The calculation function
            - depends_on: Set of dependencies
            - docstring: The function's docstring
        """
        from .registry import _dependencies, _registry

        result = {}
        for name, calc_func in _registry.items():
            result[name] = {
                "function": calc_func,
                "depends_on": _dependencies[name].copy(),
                "docstring": calc_func.__doc__ or "",
            }
        return result
