"""Tests for the calculation registry."""

from threading import Thread

import pytest

from metricengine.exceptions import CalculationError
from metricengine.registry import (
    calc,
    clear_registry,
    dependency_graph,
    deps,
    detect_cycles,
    get,
    is_registered,
    list_calculations,
    unregister,
)


@pytest.fixture(autouse=True)
def clean_registry():
    """Fixture to clean the registry before and after each test."""
    from metricengine.registry import _dependencies, _registry

    # Save original registry state
    original_registry = _registry.copy()
    original_dependencies = _dependencies.copy()

    clear_registry()
    yield
    clear_registry()

    # Restore original registry state
    _registry.update(original_registry)
    _dependencies.update(original_dependencies)


class TestCalcDecorator:
    """Test the @calc decorator."""

    def test_calc_decorator_registers_function(self):
        """Test that @calc decorator registers a function."""

        @calc("test_calc")
        def test_function():
            return 42

        assert is_registered("test_calc")
        assert get("test_calc") is test_function

    def test_calc_decorator_with_dependencies(self):
        """Test @calc decorator with dependencies."""

        @calc("test_calc", depends_on=("dep1", "dep2"))
        def test_function():
            return 42

        assert is_registered("test_calc")
        assert deps("test_calc") == {"dep1", "dep2"}

    def test_calc_decorator_adds_metadata(self):
        """Test that @calc decorator adds metadata to function."""

        @calc("test_calc", depends_on=("dep1",))
        def test_function():
            return 42

        assert hasattr(test_function, "_calc_name")
        assert hasattr(test_function, "_calc_depends_on")
        assert test_function._calc_name == "test_calc"
        assert test_function._calc_depends_on == ("dep1",)

    def test_calc_decorator_empty_name_raises_error(self):
        """Test that empty name raises CalculationError."""
        with pytest.raises(CalculationError, match="must be a non-empty string"):

            @calc("")
            def test_function():
                return 42

    def test_calc_decorator_whitespace_name_raises_error(self):
        """Test that whitespace-only name raises CalculationError."""
        with pytest.raises(CalculationError, match="must be a non-empty string"):

            @calc("   ")
            def test_function():
                return 42

    def test_calc_decorator_non_string_name_raises_error(self):
        """Test that non-string name raises CalculationError."""
        with pytest.raises(CalculationError, match="must be a non-empty string"):

            @calc(123)
            def test_function():
                return 42

    def test_calc_decorator_self_dependency_raises_error(self):
        """Test that self-dependency raises CalculationError."""
        with pytest.raises(CalculationError, match="cannot depend on itself"):

            @calc("test_calc", depends_on=("test_calc",))
            def test_function():
                return 42

    def test_calc_decorator_duplicate_registration_raises_error(self):
        """Test that duplicate registration raises CalculationError."""

        @calc("test_calc")
        def test_function1():
            return 42

        with pytest.raises(CalculationError, match="already registered"):

            @calc("test_calc")
            def test_function2():
                return 24


class TestGetFunction:
    """Test the get() function."""

    def test_get_existing_calculation(self):
        """Test getting an existing calculation."""

        @calc("test_calc")
        def test_function():
            return 42

        retrieved = get("test_calc")
        assert retrieved is test_function

    def test_get_nonexistent_calculation_raises_keyerror(self):
        """Test that getting nonexistent calculation raises KeyError."""
        with pytest.raises(KeyError, match="not found in registry"):
            get("nonexistent")


class TestDepsFunction:
    """Test the deps() function."""

    def test_deps_existing_calculation(self):
        """Test getting dependencies of existing calculation."""

        @calc("test_calc", depends_on=("dep1", "dep2"))
        def test_function():
            return 42

        dependencies = deps("test_calc")
        assert dependencies == {"dep1", "dep2"}

    def test_deps_no_dependencies(self):
        """Test getting dependencies when none exist."""

        @calc("test_calc")
        def test_function():
            return 42

        dependencies = deps("test_calc")
        assert dependencies == set()

    def test_deps_nonexistent_calculation_raises_keyerror(self):
        """Test that getting deps of nonexistent calculation raises KeyError."""
        with pytest.raises(KeyError, match="not found in registry"):
            deps("nonexistent")

    def test_deps_returns_copy(self):
        """Test that deps() returns a copy of the dependencies."""

        @calc("test_calc", depends_on=("dep1",))
        def test_function():
            return 42

        dependencies1 = deps("test_calc")
        dependencies2 = deps("test_calc")

        # Modify one copy
        dependencies1.add("new_dep")

        # Other copy should be unchanged
        assert dependencies2 == {"dep1"}


class TestListCalculations:
    """Test the list_calculations() function."""

    def test_list_calculations_empty_registry(self):
        """Test listing calculations when registry is empty."""
        result = list_calculations()
        assert result == {}

    def test_list_calculations_with_calculations(self):
        """Test listing calculations with registered functions."""

        @calc("calc1", depends_on=("dep1",))
        def function1():
            return 1

        @calc("calc2", depends_on=("dep1", "dep2"))
        def function2():
            return 2

        @calc("calc3")
        def function3():
            return 3

        result = list_calculations()
        expected = {
            "calc1": {"dep1"},
            "calc2": {"dep1", "dep2"},
            "calc3": set(),
        }
        assert result == expected

    def test_list_calculations_returns_copies(self):
        """Test that list_calculations() returns copies of dependencies."""

        @calc("test_calc", depends_on=("dep1",))
        def test_function():
            return 42

        result1 = list_calculations()
        result2 = list_calculations()

        # Modify one result
        result1["test_calc"].add("new_dep")

        # Other result should be unchanged
        assert result2["test_calc"] == {"dep1"}


class TestIsRegistered:
    """Test the is_registered() function."""

    def test_is_registered_true(self):
        """Test is_registered returns True for registered calculation."""

        @calc("test_calc")
        def test_function():
            return 42

        assert is_registered("test_calc") is True

    def test_is_registered_false(self):
        """Test is_registered returns False for unregistered calculation."""
        assert is_registered("nonexistent") is False


class TestClearRegistry:
    """Test the clear_registry() function."""

    def test_clear_registry_removes_all(self):
        """Test that clear_registry removes all calculations."""

        @calc("calc1")
        def function1():
            return 1

        @calc("calc2", depends_on=("dep1",))
        def function2():
            return 2

        assert is_registered("calc1")
        assert is_registered("calc2")

        clear_registry()

        assert not is_registered("calc1")
        assert not is_registered("calc2")
        assert list_calculations() == {}


class TestUnregister:
    """Test the unregister() function."""

    def test_unregister_existing_calculation(self):
        """Test unregistering an existing calculation."""

        @calc("test_calc", depends_on=("dep1",))
        def test_function():
            return 42

        assert is_registered("test_calc")

        unregister("test_calc")

        assert not is_registered("test_calc")

    def test_unregister_nonexistent_calculation(self):
        """Test unregistering a nonexistent calculation (should not raise)."""
        unregister("nonexistent")  # Should not raise

    def test_unregister_removes_from_dependencies(self):
        """Test that unregister removes calculation from other dependencies."""

        @calc("calc1")
        def function1():
            return 1

        @calc("calc2", depends_on=("calc1",))
        def function2():
            return 2

        @calc("calc3", depends_on=("calc1", "calc2"))
        def function3():
            return 3

        assert deps("calc2") == {"calc1"}
        assert deps("calc3") == {"calc1", "calc2"}

        unregister("calc1")

        assert not is_registered("calc1")
        assert deps("calc2") == set()
        assert deps("calc3") == {"calc2"}


class TestDependencyGraph:
    """Test the dependency_graph() function."""

    def test_dependency_graph_empty(self):
        """Test dependency graph when empty."""
        result = dependency_graph()
        assert result == {}

    def test_dependency_graph_with_calculations(self):
        """Test dependency graph with calculations."""

        @calc("calc1", depends_on=("input1",))
        def function1():
            return 1

        @calc("calc2", depends_on=("calc1", "input2"))
        def function2():
            return 2

        result = dependency_graph()
        expected = {
            "calc1": {"input1"},
            "calc2": {"calc1", "input2"},
        }
        assert result == expected

    def test_dependency_graph_returns_copies(self):
        """Test that dependency_graph returns copies."""

        @calc("test_calc", depends_on=("dep1",))
        def test_function():
            return 42

        result1 = dependency_graph()
        result2 = dependency_graph()

        # Modify one result
        result1["test_calc"].add("new_dep")

        # Other result should be unchanged
        assert result2["test_calc"] == {"dep1"}


class TestDetectCycles:
    """Test the detect_cycles() function."""

    def test_detect_cycles_no_cycles(self):
        """Test detect_cycles with no cycles."""

        @calc("calc1", depends_on=("input1",))
        def function1():
            return 1

        @calc("calc2", depends_on=("calc1",))
        def function2():
            return 2

        @calc("calc3", depends_on=("calc2",))
        def function3():
            return 3

        cycles = detect_cycles()
        assert cycles == set()

    def test_detect_cycles_simple_cycle(self):
        """Test detect_cycles with a simple cycle."""

        @calc("calc1", depends_on=("calc2",))
        def function1():
            return 1

        @calc("calc2", depends_on=("calc1",))
        def function2():
            return 2

        cycles = detect_cycles()
        # Should detect a cycle involving calc1 and calc2
        assert len(cycles) > 0
        cycle = next(iter(cycles))
        assert "calc1" in cycle and "calc2" in cycle

    def test_detect_cycles_complex_cycle(self):
        """Test detect_cycles with a more complex cycle."""

        @calc("calc1", depends_on=("calc2",))
        def function1():
            return 1

        @calc("calc2", depends_on=("calc3",))
        def function2():
            return 2

        @calc("calc3", depends_on=("calc1",))
        def function3():
            return 3

        cycles = detect_cycles()
        assert len(cycles) > 0
        cycle = next(iter(cycles))
        assert all(calc in cycle for calc in ["calc1", "calc2", "calc3"])

    def test_detect_cycles_with_isolated_calculations(self):
        """Test detect_cycles with both cycles and isolated calculations."""

        @calc("isolated", depends_on=("input1",))
        def isolated_function():
            return 42

        @calc("calc1", depends_on=("calc2",))
        def function1():
            return 1

        @calc("calc2", depends_on=("calc1",))
        def function2():
            return 2

        cycles = detect_cycles()
        # Should only detect cycle in calc1/calc2, not isolated
        assert len(cycles) > 0
        cycle = next(iter(cycles))
        assert "isolated" not in cycle


class TestThreadSafety:
    """Test thread safety of registry operations."""

    def test_concurrent_registration(self):
        """Test that concurrent registration is thread-safe."""

        def register_calculation(name):
            @calc(f"calc_{name}")
            def calculation():
                return name

        threads = []
        for i in range(10):
            thread = Thread(target=register_calculation, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # All calculations should be registered
        for i in range(10):
            assert is_registered(f"calc_{i}")

    def test_concurrent_access(self):
        """Test that concurrent access to registry is thread-safe."""

        @calc("shared_calc")
        def shared_calculation():
            return 42

        results = []

        def access_calculation():
            try:
                func = get("shared_calc")
                deps_result = deps("shared_calc")
                is_reg = is_registered("shared_calc")
                results.append((func, deps_result, is_reg))
            except Exception as e:
                results.append(e)

        threads = []
        for _ in range(10):
            thread = Thread(target=access_calculation)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # All results should be successful and consistent
        assert len(results) == 10
        for result in results:
            assert isinstance(result, tuple)
            func, deps_result, is_reg = result
            assert func is shared_calculation
            assert deps_result == set()
            assert is_reg is True


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_decorator_with_none_dependencies(self):
        """Test decorator handles None dependencies gracefully."""

        # This should work as depends_on defaults to empty tuple
        @calc("test_calc")
        def test_function():
            return 42

        assert deps("test_calc") == set()

    def test_large_dependency_chain(self):
        """Test with a large dependency chain."""
        # Create a chain of 100 calculations
        for i in range(100):
            if i == 0:

                @calc(f"calc_{i}")
                def base_calc():
                    return i
            else:
                exec(
                    f"""
@calc("calc_{i}", depends_on=("calc_{i-1}",))
def calc_{i}():
    return {i}
""",
                    {"calc": calc},
                )

        # Verify all are registered with correct dependencies
        for i in range(100):
            assert is_registered(f"calc_{i}")
            if i == 0:
                assert deps(f"calc_{i}") == set()
            else:
                assert deps(f"calc_{i}") == {f"calc_{i-1}"}

    def test_function_without_decorator_metadata(self):
        """Test that regular functions don't have calc metadata."""

        def regular_function():
            return 42

        assert not hasattr(regular_function, "_calc_name")
        assert not hasattr(regular_function, "_calc_depends_on")
