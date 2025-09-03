"""Tests for metric engine shortcuts."""

from unittest.mock import patch

from metricengine.shortcuts import (
    _expand_graph,
    can_calculate,
    inputs_needed_for,
    missing_inputs_for,
)


class TestInputsNeededFor:
    """Test the inputs_needed_for function."""

    @patch("metricengine.shortcuts.is_registered")
    @patch("metricengine.shortcuts.reg_deps")
    def test_single_base_input(self, mock_deps, mock_is_registered):
        """Test with a single base input (not registered)."""
        mock_is_registered.return_value = False

        result = inputs_needed_for(["base_input"])

        assert result == {"base_input"}
        mock_is_registered.assert_called_once_with("base_input")
        mock_deps.assert_not_called()

    @patch("metricengine.shortcuts.is_registered")
    @patch("metricengine.shortcuts.reg_deps")
    def test_registered_calc_with_no_deps(self, mock_deps, mock_is_registered):
        """Test registered calculation with no dependencies."""
        mock_is_registered.return_value = True
        mock_deps.return_value = set()

        result = inputs_needed_for(["calc_no_deps"])

        assert result == set()
        mock_is_registered.assert_called_once_with("calc_no_deps")
        mock_deps.assert_called_once_with("calc_no_deps")

    @patch("metricengine.shortcuts.is_registered")
    @patch("metricengine.shortcuts.reg_deps")
    def test_registered_calc_with_base_deps(self, mock_deps, mock_is_registered):
        """Test registered calculation with base input dependencies."""

        def mock_is_registered_side_effect(name):
            return name == "calc_with_deps"

        def mock_deps_side_effect(name):
            if name == "calc_with_deps":
                return {"base_input1", "base_input2"}
            return set()

        mock_is_registered.side_effect = mock_is_registered_side_effect
        mock_deps.side_effect = mock_deps_side_effect

        result = inputs_needed_for(["calc_with_deps"])

        assert result == {"base_input1", "base_input2"}

    @patch("metricengine.shortcuts.is_registered")
    @patch("metricengine.shortcuts.reg_deps")
    def test_nested_dependencies(self, mock_deps, mock_is_registered):
        """Test with nested dependencies."""

        def mock_is_registered_side_effect(name):
            return name in ["calc1", "calc2"]

        def mock_deps_side_effect(name):
            if name == "calc1":
                return {"base_input"}
            elif name == "calc2":
                return {"calc1"}
            return set()

        mock_is_registered.side_effect = mock_is_registered_side_effect
        mock_deps.side_effect = mock_deps_side_effect

        result = inputs_needed_for(["calc2"])

        assert result == {"base_input"}

    @patch("metricengine.shortcuts.is_registered")
    @patch("metricengine.shortcuts.reg_deps")
    def test_multiple_targets(self, mock_deps, mock_is_registered):
        """Test with multiple targets."""

        def mock_is_registered_side_effect(name):
            return name in ["calc1", "calc2"]

        def mock_deps_side_effect(name):
            if name == "calc1":
                return {"input1"}
            elif name == "calc2":
                return {"input2"}
            return set()

        mock_is_registered.side_effect = mock_is_registered_side_effect
        mock_deps.side_effect = mock_deps_side_effect

        result = inputs_needed_for(["calc1", "calc2", "base_input"])

        assert result == {"input1", "input2", "base_input"}

    @patch("metricengine.shortcuts.is_registered")
    @patch("metricengine.shortcuts.reg_deps")
    def test_duplicate_targets(self, mock_deps, mock_is_registered):
        """Test with duplicate targets."""

        def mock_is_registered_side_effect(name):
            return name == "calc1"

        def mock_deps_side_effect(name):
            if name == "calc1":
                return {"input1"}
            return set()

        mock_is_registered.side_effect = mock_is_registered_side_effect
        mock_deps.side_effect = mock_deps_side_effect

        result = inputs_needed_for(["calc1", "calc1", "calc1"])

        assert result == {"input1"}

    @patch("metricengine.shortcuts.is_registered")
    @patch("metricengine.shortcuts.reg_deps")
    def test_empty_targets(self, mock_deps, mock_is_registered):
        """Test with empty targets."""
        result = inputs_needed_for([])

        assert result == set()
        mock_is_registered.assert_not_called()
        mock_deps.assert_not_called()


class TestExpandGraph:
    """Test the _expand_graph function."""

    @patch("metricengine.shortcuts.is_registered")
    @patch("metricengine.shortcuts.reg_deps")
    def test_single_base_input(self, mock_deps, mock_is_registered):
        """Test with a single base input."""
        mock_is_registered.return_value = False

        reg_nodes, base_inputs, edges = _expand_graph(["base_input"])

        assert reg_nodes == set()
        assert base_inputs == {"base_input"}
        assert edges == {}
        mock_is_registered.assert_called_once_with("base_input")
        mock_deps.assert_not_called()

    @patch("metricengine.shortcuts.is_registered")
    @patch("metricengine.shortcuts.reg_deps")
    def test_single_registered_calc(self, mock_deps, mock_is_registered):
        """Test with a single registered calculation."""

        def mock_is_registered_side_effect(name):
            return (
                name == "calc1"
            )  # Only calc1 is registered, input1 and input2 are not

        mock_is_registered.side_effect = mock_is_registered_side_effect
        mock_deps.return_value = {"input1", "input2"}

        reg_nodes, base_inputs, edges = _expand_graph(["calc1"])

        assert reg_nodes == {"calc1"}
        assert base_inputs == {"input1", "input2"}
        assert edges == {"calc1": {"input1", "input2"}}

    @patch("metricengine.shortcuts.is_registered")
    @patch("metricengine.shortcuts.reg_deps")
    def test_nested_dependencies(self, mock_deps, mock_is_registered):
        """Test with nested dependencies."""

        def mock_is_registered_side_effect(name):
            return name in ["calc1", "calc2"]

        def mock_deps_side_effect(name):
            if name == "calc1":
                return {"input1"}
            elif name == "calc2":
                return {"calc1"}
            return set()

        mock_is_registered.side_effect = mock_is_registered_side_effect
        mock_deps.side_effect = mock_deps_side_effect

        reg_nodes, base_inputs, edges = _expand_graph(["calc2"])

        assert reg_nodes == {"calc1", "calc2"}
        assert base_inputs == {"input1"}
        assert edges == {"calc1": {"input1"}, "calc2": {"calc1"}}

    @patch("metricengine.shortcuts.is_registered")
    @patch("metricengine.shortcuts.reg_deps")
    def test_duplicate_nodes(self, mock_deps, mock_is_registered):
        """Test with duplicate nodes in the graph."""

        def mock_is_registered_side_effect(name):
            return name == "calc1"

        def mock_deps_side_effect(name):
            if name == "calc1":
                return {"input1"}
            return set()

        mock_is_registered.side_effect = mock_is_registered_side_effect
        mock_deps.side_effect = mock_deps_side_effect

        reg_nodes, base_inputs, edges = _expand_graph(["calc1", "calc1"])

        assert reg_nodes == {"calc1"}
        assert base_inputs == {"input1"}
        assert edges == {"calc1": {"input1"}}


class TestCanCalculate:
    """Test the can_calculate function."""

    @patch("metricengine.shortcuts._expand_graph")
    @patch("metricengine.shortcuts.is_registered")
    def test_all_targets_available_base_inputs(
        self, mock_is_registered, mock_expand_graph
    ):
        """Test when all targets are available base inputs."""
        mock_expand_graph.return_value = (set(), {"input1", "input2"}, {})
        mock_is_registered.return_value = False

        result = can_calculate(["input1", "input2"], ["input1", "input2", "extra"])

        assert result is True

    @patch("metricengine.shortcuts._expand_graph")
    @patch("metricengine.shortcuts.is_registered")
    def test_missing_base_inputs(self, mock_is_registered, mock_expand_graph):
        """Test when base inputs are missing."""
        mock_expand_graph.return_value = (set(), {"input1", "input2"}, {})
        mock_is_registered.return_value = False

        result = can_calculate(["input1", "input2"], ["input1"])

        assert result is False

    @patch("metricengine.shortcuts._expand_graph")
    @patch("metricengine.shortcuts.is_registered")
    def test_registered_calcs_resolvable(self, mock_is_registered, mock_expand_graph):
        """Test when registered calculations can be resolved."""
        mock_expand_graph.return_value = ({"calc1"}, {"input1"}, {"calc1": {"input1"}})

        def mock_is_registered_side_effect(name):
            return name == "calc1"

        mock_is_registered.side_effect = mock_is_registered_side_effect

        result = can_calculate(["calc1"], ["input1"])

        assert result is True

    @patch("metricengine.shortcuts._expand_graph")
    @patch("metricengine.shortcuts.is_registered")
    def test_registered_calcs_unresolvable(self, mock_is_registered, mock_expand_graph):
        """Test when registered calculations cannot be resolved."""
        mock_expand_graph.return_value = ({"calc1"}, {"input1"}, {"calc1": {"input1"}})

        def mock_is_registered_side_effect(name):
            return name == "calc1"

        mock_is_registered.side_effect = mock_is_registered_side_effect

        result = can_calculate(["calc1"], [])  # Missing input1

        assert result is False

    @patch("metricengine.shortcuts._expand_graph")
    @patch("metricengine.shortcuts.is_registered")
    def test_mixed_targets(self, mock_is_registered, mock_expand_graph):
        """Test with mixed registered and base input targets."""
        mock_expand_graph.return_value = ({"calc1"}, {"input1"}, {"calc1": {"input1"}})

        def mock_is_registered_side_effect(name):
            return name == "calc1"

        mock_is_registered.side_effect = mock_is_registered_side_effect

        result = can_calculate(["calc1", "base_input"], ["input1", "base_input"])

        assert result is True

    @patch("metricengine.shortcuts._expand_graph")
    @patch("metricengine.shortcuts.is_registered")
    def test_cycle_detection(self, mock_is_registered, mock_expand_graph):
        """Test cycle detection returns False."""
        mock_expand_graph.return_value = (
            {"calc1", "calc2"},
            set(),
            {"calc1": {"calc2"}, "calc2": {"calc1"}},
        )

        def mock_is_registered_side_effect(name):
            return name in ["calc1", "calc2"]

        mock_is_registered.side_effect = mock_is_registered_side_effect

        result = can_calculate(["calc1"], [])

        assert result is False

    @patch("metricengine.shortcuts._expand_graph")
    @patch("metricengine.shortcuts.is_registered")
    def test_empty_targets(self, mock_is_registered, mock_expand_graph):
        """Test with empty targets."""
        mock_expand_graph.return_value = (set(), set(), {})

        result = can_calculate([], ["any_input"])

        assert result is True


class TestMissingInputsFor:
    """Test the missing_inputs_for function."""

    @patch("metricengine.shortcuts.inputs_needed_for")
    def test_no_missing_inputs(self, mock_inputs_needed):
        """Test when no inputs are missing."""
        mock_inputs_needed.return_value = {"input1", "input2"}

        result = missing_inputs_for(["target1"], ["input1", "input2", "extra"])

        assert result == set()
        mock_inputs_needed.assert_called_once_with({"target1"})

    @patch("metricengine.shortcuts.inputs_needed_for")
    def test_some_missing_inputs(self, mock_inputs_needed):
        """Test when some inputs are missing."""
        mock_inputs_needed.return_value = {"input1", "input2", "input3"}

        result = missing_inputs_for(["target1"], ["input1"])

        assert result == {"input2", "input3"}
        mock_inputs_needed.assert_called_once_with({"target1"})

    @patch("metricengine.shortcuts.inputs_needed_for")
    def test_all_missing_inputs(self, mock_inputs_needed):
        """Test when all inputs are missing."""
        mock_inputs_needed.return_value = {"input1", "input2"}

        result = missing_inputs_for(["target1"], [])

        assert result == {"input1", "input2"}
        mock_inputs_needed.assert_called_once_with({"target1"})

    @patch("metricengine.shortcuts.inputs_needed_for")
    def test_no_needed_inputs(self, mock_inputs_needed):
        """Test when no inputs are needed."""
        mock_inputs_needed.return_value = set()

        result = missing_inputs_for(["target1"], ["any_input"])

        assert result == set()
        mock_inputs_needed.assert_called_once_with({"target1"})

    @patch("metricengine.shortcuts.inputs_needed_for")
    def test_multiple_targets(self, mock_inputs_needed):
        """Test with multiple targets."""
        mock_inputs_needed.return_value = {"input1", "input2", "input3"}

        result = missing_inputs_for(["target1", "target2"], ["input1"])

        assert result == {"input2", "input3"}
        mock_inputs_needed.assert_called_once_with({"target1", "target2"})

    @patch("metricengine.shortcuts.inputs_needed_for")
    def test_empty_targets(self, mock_inputs_needed):
        """Test with empty targets."""
        mock_inputs_needed.return_value = set()

        result = missing_inputs_for([], ["any_input"])

        assert result == set()
        mock_inputs_needed.assert_called_once_with(set())


class TestIntegration:
    """Integration tests using actual registry functions."""

    @patch("metricengine.shortcuts.is_registered")
    @patch("metricengine.shortcuts.reg_deps")
    def test_complex_scenario(self, mock_deps, mock_is_registered):
        """Test a complex scenario with multiple calculations and dependencies."""
        # Set up a complex dependency graph:
        # calc3 -> calc2 -> calc1 -> base_input1
        # calc3 -> base_input2
        # calc4 -> base_input3

        def mock_is_registered_side_effect(name):
            return name in ["calc1", "calc2", "calc3", "calc4"]

        def mock_deps_side_effect(name):
            if name == "calc1":
                return {"base_input1"}
            elif name == "calc2":
                return {"calc1"}
            elif name == "calc3":
                return {"calc2", "base_input2"}
            elif name == "calc4":
                return {"base_input3"}
            return set()

        mock_is_registered.side_effect = mock_is_registered_side_effect
        mock_deps.side_effect = mock_deps_side_effect

        # Test inputs_needed_for
        needed = inputs_needed_for(["calc3", "calc4"])
        assert needed == {"base_input1", "base_input2", "base_input3"}

        # Test can_calculate
        assert can_calculate(["calc3"], ["base_input1", "base_input2"]) is True
        assert can_calculate(["calc3"], ["base_input1"]) is False  # Missing base_input2
        assert (
            can_calculate(
                ["calc3", "calc4"], ["base_input1", "base_input2", "base_input3"]
            )
            is True
        )

        # Test missing_inputs_for
        missing = missing_inputs_for(["calc3", "calc4"], ["base_input1", "base_input2"])
        assert missing == {"base_input3"}

    @patch("metricengine.shortcuts.is_registered")
    @patch("metricengine.shortcuts.reg_deps")
    def test_cycle_handling(self, mock_deps, mock_is_registered):
        """Test handling of cycles in dependency graph."""
        # Create a cycle: calc1 -> calc2 -> calc1

        def mock_is_registered_side_effect(name):
            return name in ["calc1", "calc2"]

        def mock_deps_side_effect(name):
            if name == "calc1":
                return {"calc2"}
            elif name == "calc2":
                return {"calc1"}
            return set()

        mock_is_registered.side_effect = mock_is_registered_side_effect
        mock_deps.side_effect = mock_deps_side_effect

        # inputs_needed_for should handle cycles gracefully
        needed = inputs_needed_for(["calc1"])
        assert needed == set()  # No base inputs in the cycle

        # can_calculate should return False for cycles
        assert can_calculate(["calc1"], []) is False

        # missing_inputs_for should return empty set for pure cycles
        missing = missing_inputs_for(["calc1"], [])
        assert missing == set()


class TestEdgeCases:
    """Test edge cases and error conditions."""

    @patch("metricengine.shortcuts.is_registered")
    @patch("metricengine.shortcuts.reg_deps")
    def test_none_values(self, mock_deps, mock_is_registered):
        """Test handling of None values."""
        mock_is_registered.return_value = False

        # Should handle None gracefully
        result = inputs_needed_for([None])
        assert result == {None}

    @patch("metricengine.shortcuts.is_registered")
    @patch("metricengine.shortcuts.reg_deps")
    def test_empty_strings(self, mock_deps, mock_is_registered):
        """Test handling of empty strings."""
        mock_is_registered.return_value = False

        result = inputs_needed_for([""])
        assert result == {""}

    @patch("metricengine.shortcuts.is_registered")
    @patch("metricengine.shortcuts.reg_deps")
    def test_very_large_dependency_graph(self, mock_deps, mock_is_registered):
        """Test with a very large dependency graph."""

        # Create a chain of 100 calculations
        def mock_is_registered_side_effect(name):
            return name.startswith("calc_")

        def mock_deps_side_effect(name):
            if name == "calc_0":
                return {"base_input"}
            elif name.startswith("calc_"):
                num = int(name.split("_")[1])
                if num > 0:
                    return {f"calc_{num-1}"}
            return set()

        mock_is_registered.side_effect = mock_is_registered_side_effect
        mock_deps.side_effect = mock_deps_side_effect

        result = inputs_needed_for(["calc_99"])
        assert result == {"base_input"}

    def test_iterable_types(self):
        """Test that functions work with different iterable types."""
        with patch("metricengine.shortcuts.is_registered") as mock_is_reg:
            with patch("metricengine.shortcuts.reg_deps") as mock_deps:
                mock_is_reg.return_value = False

                # Test with list
                result1 = inputs_needed_for(["input1", "input2"])
                assert result1 == {"input1", "input2"}

                # Test with tuple
                result2 = inputs_needed_for(("input1", "input2"))
                assert result2 == {"input1", "input2"}

                # Test with set
                result3 = inputs_needed_for({"input1", "input2"})
                assert result3 == {"input1", "input2"}
