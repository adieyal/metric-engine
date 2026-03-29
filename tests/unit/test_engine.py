"""Tests for the calculation engine."""

from decimal import Decimal

import pytest

from metricengine.engine import Engine
from metricengine.exceptions import (
    CalculationError,
    CircularDependencyError,
    MissingInputError,
)
from metricengine.null_behaviour import NullBinaryMode, with_binary
from metricengine.policy import Policy
from metricengine.registry import Registry
from metricengine.utils import SupportsDecimal
from metricengine.value import FinancialValue


@pytest.fixture(autouse=True)
def manage_registry():
    """Fixture to save and restore the calculation registry."""
    from metricengine.registry import (
        _dependencies,
        _registry,
        clear_registry,
    )

    # Save original registry state
    original_registry = _registry.copy()
    original_dependencies = _dependencies.copy()

    clear_registry()
    yield
    clear_registry()

    # Restore original registry state
    _registry.update(original_registry)
    _dependencies.update(original_dependencies)


def test_engine_can_skip_loading_default_calculations():
    """Engine can start with an empty registry when defaults are disabled."""
    from metricengine import set_default_calculations_autoload

    set_default_calculations_autoload(False)

    engine = Engine()

    assert engine.registry.list_calculations() == {}

    with pytest.raises(MissingInputError, match="gross_margin"):
        engine.calculate("gross_margin", {"sales": 100, "cost_of_goods_sold": 60})


def test_engine_does_not_accept_per_instance_default_loading_flag():
    """Engine loading is controlled at the package level only."""
    with pytest.raises(TypeError, match="load_defaults"):
        Engine(load_defaults=False)


def test_load_all_defaults_to_default_registry():
    """The calculations loader should preserve its no-arg compatibility API."""
    from metricengine.calculations import load_all
    from metricengine.registry import clear_registry, is_registered

    clear_registry()

    load_all()

    assert is_registered("gross_profit") is True


def test_builtin_calculation_modules_declare_explicit_collections():
    """Built-in calculation modules should declare their collections explicitly."""
    import importlib

    from metricengine.calculations import _MODULE_NAMES

    for module_name in _MODULE_NAMES:
        module = importlib.import_module(f"metricengine.calculations.{module_name}")
        assert hasattr(module, "__collections__")


def test_engine_creates_private_registry_when_none_provided():
    """Each engine should get its own registry by default."""
    engine_a = Engine()
    engine_b = Engine()

    @engine_a.registry.calc("engine_a_only")
    def engine_a_only():
        return 10

    assert engine_a.registry.is_registered("engine_a_only") is True
    assert engine_b.registry.is_registered("engine_a_only") is False


def test_engines_can_share_registry_when_explicitly_provided():
    """Engines using the same registry should share calculations."""
    shared = Registry()
    engine_a = Engine(registry=shared)
    engine_b = Engine(registry=shared)

    @shared.calc("shared_calc")
    def shared_calc():
        return 10

    assert engine_a.calculate("shared_calc").as_decimal() == Decimal("10")
    assert engine_b.calculate("shared_calc").as_decimal() == Decimal("10")


def test_engine_autoload_populates_only_its_own_registry():
    """Autoloaded built-ins should populate the engine registry, not the global one."""
    from metricengine import set_default_calculations_autoload
    from metricengine.registry import clear_registry, list_calculations

    clear_registry()
    set_default_calculations_autoload(True)

    engine = Engine(registry=Registry())

    assert engine.registry.is_registered("gross_profit") is True
    assert list_calculations() == {}


def test_unregistering_from_one_engine_registry_does_not_affect_another():
    """Mutating one engine registry should not affect another engine."""
    engine_a = Engine(registry=Registry())
    engine_b = Engine(registry=Registry())

    @engine_a.registry.calc("engine_a_only")
    def engine_a_only():
        return 10

    @engine_b.registry.calc("engine_b_only")
    def engine_b_only():
        return 20

    engine_a.registry.unregister("engine_a_only")

    assert engine_a.registry.is_registered("engine_a_only") is False
    assert engine_b.registry.is_registered("engine_b_only") is True


def test_shared_registry_mutation_is_visible_to_all_engines_using_it():
    """Mutating a shared registry should be visible to all engines using it."""
    shared = Registry()
    engine_a = Engine(registry=shared)
    engine_b = Engine(registry=shared)

    @shared.calc("shared_value")
    def shared_value():
        return 5

    shared.unregister("shared_value")

    assert engine_a.registry.is_registered("shared_value") is False
    assert engine_b.registry.is_registered("shared_value") is False


def test_builtins_can_autoload_into_multiple_private_registries():
    """Built-ins should be registerable into separate registries without conflicts."""
    from metricengine import set_default_calculations_autoload

    set_default_calculations_autoload(True)

    engine_a = Engine(registry=Registry())
    engine_b = Engine(registry=Registry())

    assert engine_a.registry.is_registered("gross_profit") is True
    assert engine_b.registry.is_registered("gross_profit") is True


class TestEngine:
    """Test the calculation engine."""

    def setup_method(self):
        self.engine = Engine(registry=Registry())

        # Register some test calculations
        @self.engine.registry.calc("simple_calc", depends_on=("input_a",))
        def simple_calc(input_a):
            return input_a * FinancialValue(Decimal("2"), input_a.policy)

        @self.engine.registry.calc(
            "dependent_calc", depends_on=("simple_calc", "input_b")
        )
        def dependent_calc(simple_calc, input_b):
            return simple_calc + input_b

        @self.engine.registry.calc(
            "complex_calc", depends_on=("dependent_calc", "input_c")
        )
        def complex_calc(dependent_calc, input_c):
            return dependent_calc * input_c

    def test_simple_calculation(self):
        """Test simple calculation with direct input."""
        ctx = {"input_a": 10}
        result = self.engine.calculate("simple_calc", ctx)

        assert isinstance(result, FinancialValue)
        assert result._value == Decimal("20")

    def test_dependent_calculation(self):
        """Test calculation with dependencies."""
        ctx = {"input_a": 10, "input_b": 5}
        result = self.engine.calculate("dependent_calc", ctx)

        # simple_calc = 10 * 2 = 20
        # dependent_calc = 20 + 5 = 25
        assert result._value == Decimal("25")

    def test_complex_calculation(self):
        """Test multi-level dependency calculation."""
        ctx = {"input_a": 10, "input_b": 5, "input_c": 3}
        result = self.engine.calculate("complex_calc", ctx)

        # simple_calc = 10 * 2 = 20
        # dependent_calc = 20 + 5 = 25
        # complex_calc = 25 * 3 = 75
        assert result._value == Decimal("75")

    def test_missing_input_error(self):
        """Test error when required input is missing."""
        ctx = {"input_a": 10}  # Missing input_b

        with pytest.raises(MissingInputError) as exc_info:
            self.engine.calculate("dependent_calc", ctx)

        assert "input_b" in str(exc_info.value)
        assert exc_info.value.missing_inputs == ["input_b"]

    def test_circular_dependency_error(self):
        """Test detection of circular dependencies."""

        # Create circular dependency
        @self.engine.registry.calc("calc_a", depends_on=("calc_b",))
        def calc_a(calc_b):
            return calc_b + Decimal("1")

        @self.engine.registry.calc("calc_b", depends_on=("calc_c",))
        def calc_b(calc_c):
            return calc_c + Decimal("1")

        @self.engine.registry.calc("calc_c", depends_on=("calc_a",))
        def calc_c(calc_a):
            return calc_a + Decimal("1")

        ctx = {}
        with pytest.raises(CircularDependencyError) as exc_info:
            self.engine.calculate("calc_a", ctx)

        assert "calc_a" in exc_info.value.cycle
        assert "calc_b" in exc_info.value.cycle
        assert "calc_c" in exc_info.value.cycle

    def test_unregistered_calculation_error(self):
        """Test error for unregistered calculation."""
        ctx = {"input_a": 10}

        with pytest.raises(MissingInputError) as exc_info:
            self.engine.calculate("nonexistent_calc", ctx)

        assert "nonexistent_calc" in str(exc_info.value)

    def test_policy_application(self):
        """Test that policy is applied to results."""
        policy = Policy(decimal_places=4)
        ctx = {"input_a": Decimal("10.123456")}

        result = self.engine.calculate("simple_calc", ctx, policy=policy)

        assert result.policy == policy
        assert result.as_decimal() == Decimal("20.2469")  # Quantized to 4 dp

    def test_default_policy(self):
        """Test engine with default policy."""
        engine = Engine(Policy(decimal_places=1), registry=self.engine.registry)
        ctx = {"input_a": Decimal("10.567")}

        result = engine.calculate("simple_calc", ctx)
        assert result.as_decimal() == Decimal("21.1")  # Quantized to 1 dp

    def test_type_conversion(self):
        """Test automatic type conversion of inputs."""
        # Test various input types
        ctx = {
            "input_a": "10.5",  # string
            "input_b": 5,  # int
        }

        result = self.engine.calculate("dependent_calc", ctx)
        # simple_calc = 10.5 * 2 = 21
        # dependent_calc = 21 + 5 = 26
        assert result._value == Decimal("26")

    def test_none_input_propagation(self):
        """Test that None input propagates through calculations."""
        ctx = {"input_a": None}

        # With the new FinancialValue approach, None is wrapped and propagated
        result = self.engine.calculate("simple_calc", ctx)

        # The result should be a FinancialValue wrapping None
        assert isinstance(result, FinancialValue)
        assert result.is_none()
        assert result.as_decimal() is None

    def test_invalid_input_type(self):
        """Test error with invalid input type."""
        ctx: dict[str, SupportsDecimal] = {"input_a": "not a number"}

        with with_binary(NullBinaryMode.RAISE):
            with pytest.raises(CalculationError):
                self.engine.calculate("simple_calc", ctx)

    def test_calculation_returns_none(self):
        """Test calculation that returns None is handled as valid undefined value."""

        @self.engine.registry.calc("null_calc", depends_on=("input_a",))
        def null_calc(input_a):  # noqa: ARG001
            return None

        ctx = {"input_a": 10}

        # None should be a valid result for undefined operations
        result = self.engine.calculate("null_calc", ctx)
        assert result.is_none()
        assert str(result) == "—"

    def test_calculation_exception(self):
        """Test handling of exceptions in calculations."""

        @self.engine.registry.calc("error_calc", depends_on=("input_a",))
        def error_calc(input_a):  # noqa: ARG001
            raise ValueError("Test error")

        ctx = {"input_a": 10}

        with pytest.raises(CalculationError) as exc_info:
            self.engine.calculate("error_calc", ctx)

        # Calculations that fail are treated as missing
        assert (
            "error_calc" in str(exc_info.value)
            or len(exc_info.value.missing_inputs) == 0
        )

    def test_get_dependencies(self):
        """Test getting all dependencies for a calculation."""
        deps = self.engine.get_dependencies("complex_calc")

        expected_deps = {
            "simple_calc",
            "dependent_calc",
            "input_a",
            "input_b",
            "input_c",
        }
        assert deps == expected_deps

    def test_get_dependencies_unregistered(self):
        """Test getting dependencies for unregistered calculation."""
        with pytest.raises(CalculationError):
            self.engine.get_dependencies("nonexistent")

    def test_validate_dependencies(self):
        """Test dependency validation."""
        registered, unregistered = self.engine.validate_dependencies("complex_calc")

        assert "simple_calc" in registered
        assert "dependent_calc" in registered
        assert "input_a" in unregistered
        assert "input_b" in unregistered
        assert "input_c" in unregistered

    def test_caching_behavior(self):
        """Test that intermediate results are cached."""
        call_count = 0

        @self.engine.registry.calc("counting_calc", depends_on=("input_a",))
        def counting_calc(input_a):
            nonlocal call_count
            call_count += 1
            return input_a * Decimal("2")

        @self.engine.registry.calc(
            "uses_counting_twice", depends_on=("counting_calc", "input_b")
        )
        def uses_counting_twice(counting_calc, input_b):
            # This would call counting_calc twice without caching
            return counting_calc + (counting_calc * input_b)

        # This calculation should use counting_calc result twice
        # but only calculate it once due to caching
        ctx = {"input_a": 10, "input_b": 2}
        result = self.engine.calculate("uses_counting_twice", ctx)

        # counting_calc = 20, result = 20 + (20 * 2) = 60
        assert result._value == Decimal("60")
        # Should only be called once due to caching
        assert call_count == 1

    def test_direct_input_overrides_calculation(self):
        """Test that direct inputs override calculated values."""
        # Provide direct value for simple_calc instead of calculating it
        ctx = {
            "input_a": 10,
            "input_b": 5,
            "simple_calc": 100,  # Override the calculated value
        }

        result = self.engine.calculate("dependent_calc", ctx)

        # Should use provided simple_calc value (100) instead of calculated (20)
        # dependent_calc = 100 + 5 = 105
        assert result._value == Decimal("105")
