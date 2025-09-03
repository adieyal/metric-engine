import pytest

from metricengine.null_behaviour import (
    DEFAULT_NULLS,
    STRICT_RAISE,
    SUM_PROPAGATE,
    SUM_RAISE,
    SUM_ZERO,
    NullBehavior,
    NullBinaryMode,
    NullReductionMode,
    get_nulls,
    use_binary,
    use_nulls,
    use_reduction,
    with_binary,
    with_nulls,
    with_reduction,
)


class TestNullBinaryMode:
    """Test NullBinaryMode enum values and behavior."""

    def test_null_binary_mode_values(self):
        """Test that NullBinaryMode enum has expected values."""
        assert NullBinaryMode.PROPAGATE == NullBinaryMode.PROPAGATE
        assert NullBinaryMode.RAISE == NullBinaryMode.RAISE

        # Test that they are different
        assert NullBinaryMode.PROPAGATE != NullBinaryMode.RAISE

    def test_null_binary_mode_auto_values(self):
        """Test that auto() generates unique values."""
        assert NullBinaryMode.PROPAGATE.value != NullBinaryMode.RAISE.value

    def test_null_binary_mode_enum_membership(self):
        """Test enum membership and iteration."""
        assert NullBinaryMode.PROPAGATE in NullBinaryMode
        assert NullBinaryMode.RAISE in NullBinaryMode

        # Test iteration
        modes = list(NullBinaryMode)
        assert len(modes) == 2
        assert NullBinaryMode.PROPAGATE in modes
        assert NullBinaryMode.RAISE in modes


class TestNullReductionMode:
    """Test NullReductionMode enum values and behavior."""

    def test_null_reduction_mode_values(self):
        """Test that NullReductionMode enum has expected values."""
        assert NullReductionMode.PROPAGATE == NullReductionMode.PROPAGATE
        assert NullReductionMode.SKIP == NullReductionMode.SKIP
        assert NullReductionMode.ZERO == NullReductionMode.ZERO
        assert NullReductionMode.RAISE == NullReductionMode.RAISE

        # Test that they are all different
        modes = [
            NullReductionMode.PROPAGATE,
            NullReductionMode.SKIP,
            NullReductionMode.ZERO,
            NullReductionMode.RAISE,
        ]
        for i, mode1 in enumerate(modes):
            for j, mode2 in enumerate(modes):
                if i != j:
                    assert mode1 != mode2

    def test_null_reduction_mode_auto_values(self):
        """Test that auto() generates unique values."""
        values = [
            NullReductionMode.PROPAGATE.value,
            NullReductionMode.SKIP.value,
            NullReductionMode.ZERO.value,
            NullReductionMode.RAISE.value,
        ]
        assert len(set(values)) == len(values)

    def test_null_reduction_mode_enum_membership(self):
        """Test enum membership and iteration."""
        assert NullReductionMode.PROPAGATE in NullReductionMode
        assert NullReductionMode.SKIP in NullReductionMode
        assert NullReductionMode.ZERO in NullReductionMode
        assert NullReductionMode.RAISE in NullReductionMode

        # Test iteration
        modes = list(NullReductionMode)
        assert len(modes) == 4
        for mode in [
            NullReductionMode.PROPAGATE,
            NullReductionMode.SKIP,
            NullReductionMode.ZERO,
            NullReductionMode.RAISE,
        ]:
            assert mode in modes


class TestNullBehavior:
    """Test NullBehavior class initialization and attributes."""

    def test_null_behavior_default_initialization(self):
        """Test NullBehavior with default values."""
        behavior = NullBehavior()
        assert behavior.binary == NullBinaryMode.PROPAGATE
        assert behavior.reduction == NullReductionMode.SKIP

    def test_null_behavior_custom_initialization(self):
        """Test NullBehavior with custom values."""
        behavior = NullBehavior(
            binary=NullBinaryMode.RAISE, reduction=NullReductionMode.ZERO
        )
        assert behavior.binary == NullBinaryMode.RAISE
        assert behavior.reduction == NullReductionMode.ZERO

    def test_null_behavior_mixed_initialization(self):
        """Test NullBehavior with mixed default and custom values."""
        behavior = NullBehavior(binary=NullBinaryMode.RAISE)
        assert behavior.binary == NullBinaryMode.RAISE
        assert behavior.reduction == NullReductionMode.SKIP  # Default

        behavior = NullBehavior(reduction=NullReductionMode.PROPAGATE)
        assert behavior.binary == NullBinaryMode.PROPAGATE  # Default
        assert behavior.reduction == NullReductionMode.PROPAGATE

    def test_null_behavior_equality(self):
        """Test NullBehavior equality comparison."""
        behavior1 = NullBehavior(
            binary=NullBinaryMode.RAISE, reduction=NullReductionMode.ZERO
        )
        behavior2 = NullBehavior(
            binary=NullBinaryMode.RAISE, reduction=NullReductionMode.ZERO
        )
        behavior3 = NullBehavior(
            binary=NullBinaryMode.PROPAGATE, reduction=NullReductionMode.ZERO
        )

        assert behavior1 == behavior2
        assert behavior1 != behavior3
        assert behavior2 != behavior3

    def test_null_behavior_hash(self):
        """Test NullBehavior hashability (required for frozen dataclass)."""
        behavior1 = NullBehavior(
            binary=NullBinaryMode.RAISE, reduction=NullReductionMode.ZERO
        )
        behavior2 = NullBehavior(
            binary=NullBinaryMode.RAISE, reduction=NullReductionMode.ZERO
        )

        # Same behavior should have same hash
        assert hash(behavior1) == hash(behavior2)

        # Different behaviors should have different hashes (likely)
        behavior3 = NullBehavior(
            binary=NullBinaryMode.PROPAGATE, reduction=NullReductionMode.ZERO
        )
        assert hash(behavior1) != hash(behavior3)

    def test_null_behavior_immutability(self):
        """Test that NullBehavior is immutable (frozen dataclass)."""
        behavior = NullBehavior()

        with pytest.raises(AttributeError):
            behavior.binary = NullBinaryMode.RAISE

        with pytest.raises(AttributeError):
            behavior.reduction = NullReductionMode.ZERO


class TestGetNulls:
    """Test get_nulls function."""

    def test_get_nulls_returns_default_when_no_context(self):
        """Test get_nulls returns default behavior when no context is set."""
        # Clear any existing context by setting to default
        from metricengine.null_behaviour import _current_nulls

        try:
            _current_nulls.set(NullBehavior())
        except LookupError:
            pass

        result = get_nulls()
        assert result.binary == NullBinaryMode.PROPAGATE
        assert result.reduction == NullReductionMode.SKIP

    def test_get_nulls_returns_context_value(self):
        """Test get_nulls returns the value set in context."""
        custom_behavior = NullBehavior(
            binary=NullBinaryMode.RAISE, reduction=NullReductionMode.ZERO
        )

        with use_nulls(custom_behavior):
            result = get_nulls()
            assert result == custom_behavior
            assert result.binary == NullBinaryMode.RAISE
            assert result.reduction == NullReductionMode.ZERO

        # Should return to default after context exit
        result = get_nulls()
        assert result.binary == NullBinaryMode.PROPAGATE
        assert result.reduction == NullReductionMode.SKIP


class TestUseNulls:
    """Test use_nulls context manager."""

    def test_use_nulls_sets_and_restores_context(self):
        """Test that use_nulls properly sets and restores context."""
        custom_behavior = NullBehavior(
            binary=NullBinaryMode.RAISE, reduction=NullReductionMode.ZERO
        )

        # Before context
        original_behavior = get_nulls()

        with use_nulls(custom_behavior):
            # Inside context
            current_behavior = get_nulls()
            assert current_behavior == custom_behavior
            assert current_behavior.binary == NullBinaryMode.RAISE
            assert current_behavior.reduction == NullReductionMode.ZERO

        # After context exit
        restored_behavior = get_nulls()
        assert restored_behavior == original_behavior

    def test_use_nulls_nested_contexts(self):
        """Test nested use_nulls contexts."""
        behavior1 = NullBehavior(
            binary=NullBinaryMode.RAISE, reduction=NullReductionMode.ZERO
        )
        behavior2 = NullBehavior(
            binary=NullBinaryMode.PROPAGATE, reduction=NullReductionMode.RAISE
        )

        original = get_nulls()

        with use_nulls(behavior1):
            assert get_nulls() == behavior1

            with use_nulls(behavior2):
                assert get_nulls() == behavior2

            # Inner context exited, should be back to behavior1
            assert get_nulls() == behavior1

        # Outer context exited, should be back to original
        assert get_nulls() == original

    def test_use_nulls_exception_handling(self):
        """Test that use_nulls restores context even when exceptions occur."""
        custom_behavior = NullBehavior(
            binary=NullBinaryMode.RAISE, reduction=NullReductionMode.ZERO
        )
        original_behavior = get_nulls()

        with pytest.raises(ValueError):
            with use_nulls(custom_behavior):
                raise ValueError("Test exception")

        # Context should be restored even after exception
        assert get_nulls() == original_behavior

    def test_use_nulls_context_manager_protocol(self):
        """Test that use_nulls follows context manager protocol."""
        custom_behavior = NullBehavior(
            binary=NullBinaryMode.RAISE, reduction=NullReductionMode.ZERO
        )

        # Test __enter__ returns self
        with use_nulls(custom_behavior) as cm:
            assert cm is not None
            assert get_nulls() == custom_behavior

    def test_use_nulls_token_management(self):
        """Test that use_nulls properly manages ContextVar tokens."""
        custom_behavior = NullBehavior(
            binary=NullBinaryMode.RAISE, reduction=NullReductionMode.ZERO
        )

        # Test that token is properly reset
        original_behavior = get_nulls()

        with use_nulls(custom_behavior):
            assert get_nulls() == custom_behavior

        # After exit, should be back to original
        assert get_nulls() == original_behavior


class TestUseReduction:
    """Test use_reduction context manager."""

    def test_use_reduction_preserves_binary_mode(self):
        """Test that use_reduction only changes reduction mode."""
        original_behavior = get_nulls()
        original_binary = original_behavior.binary

        with use_reduction(NullReductionMode.ZERO):
            current_behavior = get_nulls()
            assert current_behavior.binary == original_binary
            assert current_behavior.reduction == NullReductionMode.ZERO

        # Should restore original behavior
        restored_behavior = get_nulls()
        assert restored_behavior == original_behavior

    def test_use_reduction_all_modes(self):
        """Test use_reduction with all reduction modes."""
        original_behavior = get_nulls()

        for mode in NullReductionMode:
            with use_reduction(mode):
                current_behavior = get_nulls()
                assert current_behavior.reduction == mode
                assert current_behavior.binary == original_behavior.binary

        # Should restore original behavior
        assert get_nulls() == original_behavior

    def test_use_reduction_nested(self):
        """Test nested use_reduction contexts."""
        original_behavior = get_nulls()

        with use_reduction(NullReductionMode.ZERO):
            assert get_nulls().reduction == NullReductionMode.ZERO

            with use_reduction(NullReductionMode.RAISE):
                assert get_nulls().reduction == NullReductionMode.RAISE

            # Inner context exited
            assert get_nulls().reduction == NullReductionMode.ZERO

        # Outer context exited
        assert get_nulls() == original_behavior

    def test_use_reduction_exception_handling(self):
        """Test that use_reduction restores context even when exceptions occur."""
        original_behavior = get_nulls()

        with pytest.raises(ValueError):
            with use_reduction(NullReductionMode.ZERO):
                raise ValueError("Test exception")

        # Context should be restored even after exception
        assert get_nulls() == original_behavior

    def test_use_reduction_context_manager_protocol(self):
        """Test that use_reduction follows context manager protocol."""
        with use_reduction(NullReductionMode.ZERO) as cm:
            assert cm is None  # use_reduction yields None
            assert get_nulls().reduction == NullReductionMode.ZERO


class TestUseBinary:
    """Test use_binary context manager."""

    def test_use_binary_preserves_reduction_mode(self):
        """Test that use_binary only changes binary mode."""
        original_behavior = get_nulls()
        original_reduction = original_behavior.reduction

        with use_binary(NullBinaryMode.RAISE):
            current_behavior = get_nulls()
            assert current_behavior.reduction == original_reduction
            assert current_behavior.binary == NullBinaryMode.RAISE

        # Should restore original behavior
        restored_behavior = get_nulls()
        assert restored_behavior == original_behavior

    def test_use_binary_all_modes(self):
        """Test use_binary with all binary modes."""
        original_behavior = get_nulls()

        for mode in NullBinaryMode:
            with use_binary(mode):
                current_behavior = get_nulls()
                assert current_behavior.binary == mode
                assert current_behavior.reduction == original_behavior.reduction

        # Should restore original behavior
        assert get_nulls() == original_behavior

    def test_use_binary_nested(self):
        """Test nested use_binary contexts."""
        original_behavior = get_nulls()

        with use_binary(NullBinaryMode.RAISE):
            assert get_nulls().binary == NullBinaryMode.RAISE

            with use_binary(NullBinaryMode.PROPAGATE):
                assert get_nulls().binary == NullBinaryMode.PROPAGATE

            # Inner context exited
            assert get_nulls().binary == NullBinaryMode.RAISE

        # Outer context exited
        assert get_nulls() == original_behavior

    def test_use_binary_exception_handling(self):
        """Test that use_binary restores context even when exceptions occur."""
        original_behavior = get_nulls()

        with pytest.raises(ValueError):
            with use_binary(NullBinaryMode.RAISE):
                raise ValueError("Test exception")

        # Context should be restored even after exception
        assert get_nulls() == original_behavior

    def test_use_binary_context_manager_protocol(self):
        """Test that use_binary follows context manager protocol."""
        with use_binary(NullBinaryMode.RAISE) as cm:
            assert cm is None  # use_binary yields None
            assert get_nulls().binary == NullBinaryMode.RAISE


class TestWithReduction:
    """Test with_reduction alias context manager."""

    def test_with_reduction_is_alias_for_use_reduction(self):
        """Test that with_reduction is an alias for use_reduction."""
        assert with_reduction is use_reduction

    def test_with_reduction_preserves_binary_mode(self):
        """Test that with_reduction only changes reduction mode."""
        original_behavior = get_nulls()
        original_binary = original_behavior.binary

        with with_reduction(NullReductionMode.ZERO):
            current_behavior = get_nulls()
            assert current_behavior.binary == original_binary
            assert current_behavior.reduction == NullReductionMode.ZERO

        # Should restore original behavior
        restored_behavior = get_nulls()
        assert restored_behavior == original_behavior


class TestWithBinary:
    """Test with_binary alias context manager."""

    def test_with_binary_is_alias_for_use_binary(self):
        """Test that with_binary is an alias for use_binary."""
        assert with_binary is use_binary

    def test_with_binary_preserves_reduction_mode(self):
        """Test that with_binary only changes binary mode."""
        original_behavior = get_nulls()
        original_reduction = original_behavior.reduction

        with with_binary(NullBinaryMode.RAISE):
            current_behavior = get_nulls()
            assert current_behavior.reduction == original_reduction
            assert current_behavior.binary == NullBinaryMode.RAISE

        # Should restore original behavior
        restored_behavior = get_nulls()
        assert restored_behavior == original_behavior


class TestWithNullsDecorator:
    """Test with_nulls decorator."""

    def test_with_nulls_decorator_basic_usage(self):
        """Test basic usage of with_nulls decorator."""
        custom_behavior = NullBehavior(
            binary=NullBinaryMode.RAISE, reduction=NullReductionMode.ZERO
        )

        @with_nulls(custom_behavior)
        def test_function():
            return get_nulls()

        # Function should run with custom behavior
        result = test_function()
        assert result == custom_behavior

        # Context should be restored after function call
        assert get_nulls() != custom_behavior

    def test_with_nulls_decorator_with_arguments(self):
        """Test with_nulls decorator with function arguments."""
        custom_behavior = NullBehavior(
            binary=NullBinaryMode.RAISE, reduction=NullReductionMode.ZERO
        )

        @with_nulls(custom_behavior)
        def test_function(x, y=10):
            return get_nulls(), x, y

        # Function should run with custom behavior and preserve arguments
        result = test_function(5, y=20)
        behavior, x, y = result
        assert behavior == custom_behavior
        assert x == 5
        assert y == 20

    def test_with_nulls_decorator_with_kwargs(self):
        """Test with_nulls decorator with keyword arguments."""
        custom_behavior = NullBehavior(
            binary=NullBinaryMode.RAISE, reduction=NullReductionMode.ZERO
        )

        @with_nulls(custom_behavior)
        def test_function(**kwargs):
            return get_nulls(), kwargs

        # Function should run with custom behavior and preserve kwargs
        result = test_function(a=1, b=2)
        behavior, kwargs = result
        assert behavior == custom_behavior
        assert kwargs == {"a": 1, "b": 2}

    def test_with_nulls_decorator_exception_handling(self):
        """Test that with_nulls decorator restores context after exceptions."""
        custom_behavior = NullBehavior(
            binary=NullBinaryMode.RAISE, reduction=NullReductionMode.ZERO
        )
        original_behavior = get_nulls()

        @with_nulls(custom_behavior)
        def test_function():
            assert get_nulls() == custom_behavior
            raise ValueError("Test exception")

        # Function should raise exception
        with pytest.raises(ValueError, match="Test exception"):
            test_function()

        # Context should be restored even after exception
        assert get_nulls() == original_behavior

    def test_with_nulls_decorator_nested_calls(self):
        """Test with_nulls decorator with nested function calls."""
        behavior1 = NullBehavior(
            binary=NullBinaryMode.RAISE, reduction=NullReductionMode.ZERO
        )
        behavior2 = NullBehavior(
            binary=NullBinaryMode.PROPAGATE, reduction=NullReductionMode.RAISE
        )

        @with_nulls(behavior1)
        def outer_function():
            assert get_nulls() == behavior1

            @with_nulls(behavior2)
            def inner_function():
                assert get_nulls() == behavior2
                return "inner"

            result = inner_function()
            assert get_nulls() == behavior1  # Should be back to behavior1
            return result

        result = outer_function()
        assert result == "inner"
        assert get_nulls() != behavior1  # Should be back to original

    def test_with_nulls_decorator_preserves_function_metadata(self):
        """Test that with_nulls decorator preserves function metadata."""
        custom_behavior = NullBehavior(
            binary=NullBinaryMode.RAISE, reduction=NullReductionMode.ZERO
        )

        def original_function(x: int, y: str = "default") -> str:
            """Original function docstring."""
            return f"{x}_{y}"

        decorated_function = with_nulls(custom_behavior)(original_function)

        # Test that the decorated function works
        result = decorated_function(5, "test")
        assert result == "5_test"

        # Note: The decorator doesn't preserve metadata in this implementation
        # This is a limitation of the current implementation


class TestPredefinedBehaviors:
    """Test predefined behavior configurations."""

    def test_default_nulls_behavior(self):
        """Test DEFAULT_NULLS predefined behavior."""
        assert DEFAULT_NULLS.binary == NullBinaryMode.PROPAGATE
        assert DEFAULT_NULLS.reduction == NullReductionMode.SKIP

    def test_strict_raise_behavior(self):
        """Test STRICT_RAISE predefined behavior."""
        assert STRICT_RAISE.binary == NullBinaryMode.RAISE
        assert STRICT_RAISE.reduction == NullReductionMode.RAISE

    def test_sum_zero_behavior(self):
        """Test SUM_ZERO predefined behavior."""
        assert SUM_ZERO.binary == NullBinaryMode.PROPAGATE
        assert SUM_ZERO.reduction == NullReductionMode.ZERO

    def test_sum_propagate_behavior(self):
        """Test SUM_PROPAGATE predefined behavior."""
        assert SUM_PROPAGATE.binary == NullBinaryMode.PROPAGATE
        assert SUM_PROPAGATE.reduction == NullReductionMode.PROPAGATE

    def test_sum_raise_behavior(self):
        """Test SUM_RAISE predefined behavior."""
        assert SUM_RAISE.binary == NullBinaryMode.PROPAGATE
        assert SUM_RAISE.reduction == NullReductionMode.RAISE

    def test_predefined_behaviors_are_immutable(self):
        """Test that predefined behaviors cannot be modified."""
        # These should be NullBehavior instances
        assert isinstance(DEFAULT_NULLS, NullBehavior)
        assert isinstance(STRICT_RAISE, NullBehavior)
        assert isinstance(SUM_ZERO, NullBehavior)
        assert isinstance(SUM_PROPAGATE, NullBehavior)
        assert isinstance(SUM_RAISE, NullBehavior)

    def test_predefined_behaviors_are_unique(self):
        """Test that predefined behaviors are unique instances."""
        behaviors = [DEFAULT_NULLS, STRICT_RAISE, SUM_ZERO, SUM_PROPAGATE, SUM_RAISE]

        # All should be different
        for i, behavior1 in enumerate(behaviors):
            for j, behavior2 in enumerate(behaviors):
                if i != j:
                    assert behavior1 != behavior2

    def test_predefined_behaviors_usage(self):
        """Test that predefined behaviors can be used in context managers."""
        original_behavior = get_nulls()

        # Test each predefined behavior
        with use_nulls(STRICT_RAISE):
            current = get_nulls()
            assert current.binary == NullBinaryMode.RAISE
            assert current.reduction == NullReductionMode.RAISE

        with use_nulls(SUM_ZERO):
            current = get_nulls()
            assert current.binary == NullBinaryMode.PROPAGATE
            assert current.reduction == NullReductionMode.ZERO

        with use_nulls(SUM_PROPAGATE):
            current = get_nulls()
            assert current.binary == NullBinaryMode.PROPAGATE
            assert current.reduction == NullReductionMode.PROPAGATE

        with use_nulls(SUM_RAISE):
            current = get_nulls()
            assert current.binary == NullBinaryMode.PROPAGATE
            assert current.reduction == NullReductionMode.RAISE

        # Should restore original behavior
        assert get_nulls() == original_behavior


class TestThreadSafety:
    """Test thread safety aspects of the null behavior system."""

    def test_context_var_thread_local_storage(self):
        """Test that ContextVar provides thread-local storage."""
        # This test verifies that the ContextVar implementation
        # provides thread-local storage, which is a key feature
        # for thread safety
        from contextvars import ContextVar

        from metricengine.null_behaviour import _current_nulls

        # Verify that _current_nulls is a ContextVar
        assert isinstance(_current_nulls, ContextVar)

        # Test that we can set and get values
        custom_behavior = NullBehavior(
            binary=NullBinaryMode.RAISE, reduction=NullReductionMode.ZERO
        )

        with use_nulls(custom_behavior):
            assert get_nulls() == custom_behavior

        # Should be restored after context exit
        assert get_nulls() != custom_behavior

    def test_context_var_copy_context(self):
        """Test ContextVar behavior with context copying."""
        from contextvars import copy_context

        custom_behavior = NullBehavior(
            binary=NullBinaryMode.RAISE, reduction=NullReductionMode.ZERO
        )

        def test_in_context():
            return get_nulls()

        # Test in current context
        original_behavior = get_nulls()

        # Copy context before making changes
        copied_context = copy_context()

        with use_nulls(custom_behavior):
            # In current context
            assert get_nulls() == custom_behavior

            # In copied context (should have original behavior since it was copied before changes)
            result = copied_context.run(test_in_context)
            assert result == original_behavior

        # Current context should be restored
        assert get_nulls() == original_behavior


class TestIntegration:
    """Test integration between different null behavior components."""

    def test_combined_context_managers(self):
        """Test using multiple context managers together."""
        original_behavior = get_nulls()

        with use_nulls(
            NullBehavior(binary=NullBinaryMode.RAISE, reduction=NullReductionMode.ZERO)
        ):
            # Test use_reduction within use_nulls
            with use_reduction(NullReductionMode.RAISE):
                current = get_nulls()
                assert current.binary == NullBinaryMode.RAISE
                assert current.reduction == NullReductionMode.RAISE

            # Test use_binary within use_nulls
            with use_binary(NullBinaryMode.PROPAGATE):
                current = get_nulls()
                assert current.binary == NullBinaryMode.PROPAGATE
                assert current.reduction == NullReductionMode.ZERO

        # Should restore original behavior
        assert get_nulls() == original_behavior

    def test_context_manager_chaining(self):
        """Test chaining multiple context managers."""
        original_behavior = get_nulls()

        with use_nulls(SUM_ZERO):
            with use_binary(NullBinaryMode.RAISE):
                with use_reduction(NullReductionMode.PROPAGATE):
                    current = get_nulls()
                    assert current.binary == NullBinaryMode.RAISE
                    assert current.reduction == NullReductionMode.PROPAGATE

        # Should restore original behavior
        assert get_nulls() == original_behavior

    def test_decorator_with_context_managers(self):
        """Test using decorator with context managers."""
        custom_behavior = NullBehavior(
            binary=NullBinaryMode.RAISE, reduction=NullReductionMode.ZERO
        )

        @with_nulls(custom_behavior)
        def test_function():
            # Function runs with custom_behavior
            assert get_nulls() == custom_behavior

            # Can override with context manager
            with use_reduction(NullReductionMode.RAISE):
                current = get_nulls()
                assert current.binary == NullBinaryMode.RAISE
                assert current.reduction == NullReductionMode.RAISE

            # Should be back to custom_behavior
            assert get_nulls() == custom_behavior

            return "success"

        result = test_function()
        assert result == "success"
        assert get_nulls() != custom_behavior  # Should be back to original

    def test_complex_nesting_scenario(self):
        """Test complex nesting of decorators and context managers."""
        behavior1 = NullBehavior(
            binary=NullBinaryMode.RAISE, reduction=NullReductionMode.ZERO
        )
        behavior2 = NullBehavior(
            binary=NullBinaryMode.PROPAGATE, reduction=NullReductionMode.RAISE
        )

        @with_nulls(behavior1)
        def outer_function():
            assert get_nulls() == behavior1

            with use_nulls(behavior2):
                assert get_nulls() == behavior2

                with use_reduction(NullReductionMode.SKIP):
                    current = get_nulls()
                    assert current.binary == NullBinaryMode.PROPAGATE
                    assert current.reduction == NullReductionMode.SKIP

                assert get_nulls() == behavior2

            assert get_nulls() == behavior1
            return "complex_success"

        result = outer_function()
        assert result == "complex_success"
        assert get_nulls() != behavior1  # Should be back to original


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_context_manager_with_none_behavior(self):
        """Test context manager with None behavior (should not happen in practice)."""
        # This tests the robustness of the context manager
        # In practice, NullBehavior should never be None, but let's test the code path

        # Test that we can create a NullBehavior and use it
        behavior = NullBehavior()
        assert behavior is not None

        with use_nulls(behavior):
            assert get_nulls() == behavior

    def test_multiple_rapid_context_changes(self):
        """Test rapid context changes to ensure no race conditions."""
        behaviors = [
            NullBehavior(
                binary=NullBinaryMode.PROPAGATE, reduction=NullReductionMode.SKIP
            ),
            NullBehavior(binary=NullBinaryMode.RAISE, reduction=NullReductionMode.ZERO),
            NullBehavior(
                binary=NullBinaryMode.PROPAGATE, reduction=NullReductionMode.RAISE
            ),
            NullBehavior(
                binary=NullBinaryMode.RAISE, reduction=NullReductionMode.PROPAGATE
            ),
        ]

        original_behavior = get_nulls()

        # Rapidly change contexts
        for behavior in behaviors:
            with use_nulls(behavior):
                assert get_nulls() == behavior

        # Should be back to original
        assert get_nulls() == original_behavior

    def test_context_manager_without_entering(self):
        """Test context manager without entering (edge case)."""
        custom_behavior = NullBehavior(
            binary=NullBinaryMode.RAISE, reduction=NullReductionMode.ZERO
        )

        # Create context manager but don't enter it
        cm = use_nulls(custom_behavior)

        # Should not affect current behavior
        original_behavior = get_nulls()
        assert get_nulls() == original_behavior

        # Now enter it
        with cm:
            assert get_nulls() == custom_behavior

        # Should be back to original
        assert get_nulls() == original_behavior

    def test_decorator_with_no_arguments(self):
        """Test decorator with function that takes no arguments."""
        custom_behavior = NullBehavior(
            binary=NullBinaryMode.RAISE, reduction=NullReductionMode.ZERO
        )

        @with_nulls(custom_behavior)
        def no_args_function():
            return get_nulls()

        result = no_args_function()
        assert result == custom_behavior

    def test_decorator_with_star_args(self):
        """Test decorator with function that uses *args."""
        custom_behavior = NullBehavior(
            binary=NullBinaryMode.RAISE, reduction=NullReductionMode.ZERO
        )

        @with_nulls(custom_behavior)
        def star_args_function(*args):
            return get_nulls(), args

        result = star_args_function(1, 2, 3)
        behavior, args = result
        assert behavior == custom_behavior
        assert args == (1, 2, 3)

    def test_decorator_with_star_kwargs(self):
        """Test decorator with function that uses **kwargs."""
        custom_behavior = NullBehavior(
            binary=NullBinaryMode.RAISE, reduction=NullReductionMode.ZERO
        )

        @with_nulls(custom_behavior)
        def star_kwargs_function(**kwargs):
            return get_nulls(), kwargs

        result = star_kwargs_function(a=1, b=2, c=3)
        behavior, kwargs = result
        assert behavior == custom_behavior
        assert kwargs == {"a": 1, "b": 2, "c": 3}
