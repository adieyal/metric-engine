import pytest

from metricengine.policy import DEFAULT_POLICY, Policy
from metricengine.policy_context import (
    PolicyResolution,
    _current_policy,
    _current_resolution,
    get_active_policy,
    get_policy,
    get_resolution,
    use_policy,
    use_policy_resolution,
)


class TestPolicyResolution:
    """Test PolicyResolution enum values."""

    def test_policy_resolution_values(self):
        """Test that PolicyResolution enum has expected values."""
        assert PolicyResolution.CONTEXT == PolicyResolution.CONTEXT
        assert PolicyResolution.LEFT_OPERAND == PolicyResolution.LEFT_OPERAND
        assert PolicyResolution.STRICT_MATCH == PolicyResolution.STRICT_MATCH

        # Test that they are different
        assert PolicyResolution.CONTEXT != PolicyResolution.LEFT_OPERAND
        assert PolicyResolution.LEFT_OPERAND != PolicyResolution.STRICT_MATCH
        assert PolicyResolution.STRICT_MATCH != PolicyResolution.CONTEXT


class TestGetPolicy:
    """Test get_policy function."""

    def test_get_policy_returns_none_when_no_context(self):
        """Test get_policy returns None when no context is set."""
        # Clear any existing context
        try:
            _current_policy.set(None)
        except LookupError:
            pass

        result = get_policy()
        assert result is None

    def test_get_policy_returns_context_value(self):
        """Test get_policy returns the value set in context."""
        custom_policy = Policy(decimal_places=4, none_text="N/A")

        with use_policy(custom_policy):
            result = get_active_policy()
            assert result == custom_policy
            assert result.decimal_places == 4
            assert result.none_text == "N/A"

        # Should return to default after context exit
        result = get_active_policy()
        assert result == DEFAULT_POLICY


class TestGetResolution:
    """Test get_resolution function."""

    def test_get_resolution_returns_default_when_no_context(self):
        """Test get_resolution returns default CONTEXT when no context is set."""
        # Clear any existing context
        try:
            _current_resolution.set(PolicyResolution.CONTEXT)
        except LookupError:
            pass

        result = get_resolution()
        assert result == PolicyResolution.CONTEXT

    def test_get_resolution_returns_context_value(self):
        """Test get_resolution returns the value set in context."""
        custom_resolution = PolicyResolution.STRICT_MATCH

        with use_policy_resolution(custom_resolution):
            result = get_resolution()
            assert result == custom_resolution

        # Should return to default after context exit
        result = get_resolution()
        assert result == PolicyResolution.CONTEXT


class TestUsePolicy:
    """Test use_policy context manager."""

    def test_use_policy_sets_and_restores_context(self):
        """Test that use_policy properly sets and restores context."""
        custom_policy = Policy(decimal_places=3, rounding="ROUND_DOWN")

        # Before context
        original_policy = get_active_policy()

        with use_policy(custom_policy) as ctx:
            # Inside context
            current_policy = get_active_policy()
            assert current_policy == custom_policy
            assert current_policy.decimal_places == 3
            assert current_policy.rounding == "ROUND_DOWN"
            assert ctx._policy == custom_policy

        # After context
        restored_policy = get_active_policy()
        assert restored_policy == original_policy

    def test_use_policy_restores_context_on_exception(self):
        """Test that use_policy restores context even when exception occurs."""
        custom_policy = Policy(decimal_places=5)
        original_policy = get_policy()

        with pytest.raises(ValueError):
            with use_policy(custom_policy):
                raise ValueError("Test exception")

        # Context should still be restored
        restored_policy = get_policy()
        assert restored_policy == original_policy

    def test_use_policy_nested_contexts(self):
        """Test nested use_policy contexts work correctly."""
        policy1 = Policy(decimal_places=2)
        policy2 = Policy(decimal_places=4)
        original_policy = get_policy()

        with use_policy(policy1):
            assert get_policy() == policy1

            with use_policy(policy2):
                assert get_policy() == policy2

            # Inner context should be restored
            assert get_policy() == policy1

        # Outer context should be restored
        assert get_policy() == original_policy

    def test_use_policy_token_management(self):
        """Test that tokens are properly managed."""
        custom_policy = Policy(decimal_places=6)

        with use_policy(custom_policy) as ctx:
            assert ctx._token is not None
            assert isinstance(ctx._token, object)  # ContextVar token

        # Token should be cleared after exit
        assert ctx._token is None


class TestUsePolicyResolution:
    """Test use_policy_resolution context manager."""

    def test_use_policy_resolution_sets_and_restores_context(self):
        """Test that use_policy_resolution properly sets and restores context."""
        custom_resolution = PolicyResolution.LEFT_OPERAND

        # Before context
        original_resolution = get_resolution()

        with use_policy_resolution(custom_resolution) as ctx:
            # Inside context
            current_resolution = get_resolution()
            assert current_resolution == custom_resolution
            assert ctx._mode == custom_resolution

        # After context
        restored_resolution = get_resolution()
        assert restored_resolution == original_resolution

    def test_use_policy_resolution_restores_context_on_exception(self):
        """Test that use_policy_resolution restores context even when exception occurs."""
        custom_resolution = PolicyResolution.STRICT_MATCH
        original_resolution = get_resolution()

        with pytest.raises(RuntimeError):
            with use_policy_resolution(custom_resolution):
                raise RuntimeError("Test exception")

        # Context should still be restored
        restored_resolution = get_resolution()
        assert restored_resolution == original_resolution

    def test_use_policy_resolution_nested_contexts(self):
        """Test nested use_policy_resolution contexts work correctly."""
        resolution1 = PolicyResolution.CONTEXT
        resolution2 = PolicyResolution.STRICT_MATCH
        original_resolution = get_resolution()

        with use_policy_resolution(resolution1):
            assert get_resolution() == resolution1

            with use_policy_resolution(resolution2):
                assert get_resolution() == resolution2

            # Inner context should be restored
            assert get_resolution() == resolution1

        # Outer context should be restored
        assert get_resolution() == original_resolution

    def test_use_policy_resolution_token_management(self):
        """Test that tokens are properly managed."""
        custom_resolution = PolicyResolution.LEFT_OPERAND

        with use_policy_resolution(custom_resolution) as ctx:
            assert ctx._token is not None
            assert isinstance(ctx._token, object)  # ContextVar token

        # Token should be cleared after exit
        assert ctx._token is None


class TestContextVariables:
    """Test the context variables directly."""

    def test_current_policy_context_var(self):
        """Test _current_policy ContextVar behavior."""
        assert _current_policy.get() is None

        custom_policy = Policy(decimal_places=1)
        token = _current_policy.set(custom_policy)
        assert _current_policy.get() == custom_policy

        _current_policy.reset(token)
        assert _current_policy.get() is None

    def test_current_resolution_context_var(self):
        """Test _current_resolution ContextVar behavior."""
        assert _current_resolution.get() == PolicyResolution.CONTEXT

        custom_resolution = PolicyResolution.STRICT_MATCH
        token = _current_resolution.set(custom_resolution)
        assert _current_resolution.get() == custom_resolution

        _current_resolution.reset(token)
        assert _current_resolution.get() == PolicyResolution.CONTEXT


class TestIntegration:
    """Integration tests for policy context usage."""

    def test_policy_and_resolution_work_together(self):
        """Test that policy and resolution contexts work together."""
        custom_policy = Policy(decimal_places=3)
        custom_resolution = PolicyResolution.LEFT_OPERAND

        with use_policy(custom_policy):
            with use_policy_resolution(custom_resolution):
                assert get_policy() == custom_policy
                assert get_resolution() == custom_resolution

            # Resolution should be restored, policy should remain
            assert get_policy() == custom_policy
            assert get_resolution() == PolicyResolution.CONTEXT

        # Both should be restored
        assert get_policy() is None
        assert get_resolution() == PolicyResolution.CONTEXT

    def test_multiple_policy_changes(self):
        """Test multiple policy changes in sequence."""
        policies = [
            Policy(decimal_places=1),
            Policy(decimal_places=2),
            Policy(decimal_places=3),
        ]

        for i, policy in enumerate(policies):
            with use_policy(policy):
                assert get_active_policy().decimal_places == i + 1

        # Should return to default
        assert get_active_policy() == DEFAULT_POLICY


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_context_manager_with_none_token(self):
        """Test context manager behavior when token is None."""
        # This shouldn't happen in normal usage, but let's test it
        with use_policy(DEFAULT_POLICY) as ctx:
            ctx._token = None

        # Should not raise an error
        assert get_policy() is None

    def test_context_manager_reuse(self):
        """Test that context managers can be reused."""
        custom_policy = Policy(decimal_places=4)
        ctx = use_policy(custom_policy)

        # First use
        with ctx:
            assert get_policy() == custom_policy

        # Second use
        with ctx:
            assert get_policy() == custom_policy

        # Should return to default
        assert get_policy() is None


class TestGetActivePolicy:
    """Test get_active_policy function."""

    def test_get_active_policy_returns_current_policy(self):
        """Test get_active_policy returns the current policy in context."""
        custom_policy = Policy(decimal_places=2, rounding="ROUND_UP")

        with use_policy(custom_policy):
            result = get_active_policy()
            assert result == custom_policy
            assert result.decimal_places == 2
            assert result.rounding == "ROUND_UP"

    def test_get_active_policy_returns_default_when_none(self):
        """Test get_active_policy returns DEFAULT_POLICY when current policy is None."""
        # Clear any existing context
        try:
            _current_policy.set(None)
        except LookupError:
            pass

        result = get_active_policy()
        assert result == DEFAULT_POLICY

    def test_get_active_policy_ignores_default_when_policy_exists(self):
        """Test get_active_policy ignores default when current policy exists."""
        current_policy = Policy(decimal_places=1)

        with use_policy(current_policy):
            result = get_active_policy()
            assert result == current_policy
            assert result.decimal_places == 1


class TestAdditionalEdgeCases:
    """Additional edge cases and integration tests."""

    def test_all_accessor_functions_consistency(self):
        """Test that all accessor functions are consistent."""
        custom_policy = Policy(decimal_places=7, none_text="EMPTY")

        with use_policy(custom_policy):
            # All should return the same policy
            assert get_active_policy() == custom_policy
            assert get_policy() == custom_policy

            # All should have the same attributes
            assert get_active_policy().decimal_places == 7
            assert get_policy().decimal_places == 7

    def test_mixed_context_managers(self):
        """Test mixing different context managers."""
        policy1 = Policy(decimal_places=1)
        policy2 = Policy(decimal_places=2)
        resolution1 = PolicyResolution.CONTEXT
        resolution2 = PolicyResolution.STRICT_MATCH

        with use_policy(policy1):
            with use_policy_resolution(resolution1):
                with use_policy(policy2):
                    # Clear policy to None
                    _current_policy.set(None)
                    assert get_policy() is None
                    assert get_active_policy() == DEFAULT_POLICY
                    assert get_resolution() == resolution1

                    # Restore policy2
                    _current_policy.set(policy2)
                    assert get_policy() == policy2
                    assert get_resolution() == resolution1

                # Policy should restore to policy1
                assert get_policy() == policy1
                assert get_resolution() == resolution1

            # Resolution should restore to default
            assert get_policy() == policy1
            assert get_resolution() == PolicyResolution.CONTEXT

    def test_context_manager_return_values(self):
        """Test that context managers return themselves."""
        custom_policy = Policy(decimal_places=3)
        custom_resolution = PolicyResolution.LEFT_OPERAND

        with use_policy(custom_policy) as policy_ctx:
            assert policy_ctx is not None
            assert hasattr(policy_ctx, "_policy")
            assert policy_ctx._policy == custom_policy

        with use_policy_resolution(custom_resolution) as resolution_ctx:
            assert resolution_ctx is not None
            assert hasattr(resolution_ctx, "_mode")
            assert resolution_ctx._mode == custom_resolution

    def test_policy_context_isolation(self):
        """Test that policy contexts are properly isolated."""
        # Test that changes in one context don't affect others
        policy1 = Policy(decimal_places=1)
        policy2 = Policy(decimal_places=2)

        with use_policy(policy1):
            assert get_policy() == policy1

            # Nested context with different policy
            with use_policy(policy2):
                assert get_policy() == policy2

            # Should still be policy1
            assert get_policy() == policy1

    def test_resolution_context_isolation(self):
        """Test that resolution contexts are properly isolated."""
        resolution1 = PolicyResolution.CONTEXT
        resolution2 = PolicyResolution.STRICT_MATCH

        with use_policy_resolution(resolution1):
            assert get_resolution() == resolution1

            # Nested context with different resolution
            with use_policy_resolution(resolution2):
                assert get_resolution() == resolution2

            # Should still be resolution1
            assert get_resolution() == resolution1

    def test_complex_nested_scenarios(self):
        """Test complex nested scenarios with multiple context managers."""
        policy1 = Policy(decimal_places=1)
        policy2 = Policy(decimal_places=2)
        resolution1 = PolicyResolution.CONTEXT
        resolution2 = PolicyResolution.LEFT_OPERAND

        # Start with default state
        original_policy = get_policy()
        original_resolution = get_resolution()

        with use_policy(policy1):
            with use_policy_resolution(resolution1):
                with use_policy(policy2):
                    with use_policy_resolution(resolution2):
                        # Clear policy to None
                        _current_policy.set(None)
                        # Deepest level - no policy, custom resolution
                        assert get_policy() is None
                        assert get_active_policy() == DEFAULT_POLICY
                        assert get_resolution() == resolution2

                        # Restore policy2
                        _current_policy.set(policy2)
                        # One level up - policy2, resolution2
                        assert get_policy() == policy2
                        assert get_resolution() == resolution2

                    # One level up - policy2, resolution1
                    assert get_policy() == policy2
                    assert get_resolution() == resolution1

                # One level up - policy1, resolution1
                assert get_policy() == policy1
                assert get_resolution() == resolution1

            # One level up - policy1, original resolution
            assert get_policy() == policy1
            assert get_resolution() == original_resolution

        # Back to original state
        assert get_policy() == original_policy
        assert get_resolution() == original_resolution
