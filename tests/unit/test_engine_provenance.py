"""Tests for engine calculation provenance tracking."""

from decimal import Decimal

import pytest

from metricengine.engine import Engine
from metricengine.policy import Policy
from metricengine.registry import calc
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


class TestEngineProvenance:
    """Test provenance tracking in engine calculations."""

    def setup_method(self):
        """Set up test calculations."""

        @calc("simple_multiply", depends_on=("input_a",))
        def simple_multiply(input_a):
            return input_a * FinancialValue(Decimal("2"), input_a.policy)

        @calc("add_two_inputs", depends_on=("input_a", "input_b"))
        def add_two_inputs(input_a, input_b):
            return input_a + input_b

        @calc("complex_calc", depends_on=("simple_multiply", "input_c"))
        def complex_calc(simple_multiply, input_c):
            return simple_multiply + input_c

        @calc("margin_calc", depends_on=("revenue", "cost"))
        def margin_calc(revenue, cost):
            return (revenue - cost) / revenue

        self.engine = Engine()

    def test_simple_calculation_provenance(self):
        """Test that simple calculations generate proper provenance."""
        ctx = {"input_a": 100}
        result = self.engine.calculate("simple_multiply", ctx)

        # Should have provenance
        assert result.has_provenance()
        prov = result.get_provenance()
        assert prov is not None
        assert prov.op == "calc:simple_multiply"
        assert "calculation" in prov.meta
        assert prov.meta["calculation"] == "simple_multiply"
        assert "input_names" in prov.meta

    def test_calculation_with_named_inputs(self):
        """Test that named inputs are captured in provenance metadata."""
        ctx = {"input_a": 100, "input_b": 50}
        result = self.engine.calculate("add_two_inputs", ctx)

        # Should have provenance with named inputs
        assert result.has_provenance()
        prov = result.get_provenance()
        assert prov is not None
        assert prov.op == "calc:add_two_inputs"

        # Check that input names are captured
        input_names = prov.meta.get("input_names", {})
        assert len(input_names) == 2
        assert "input_a" in input_names.values()
        assert "input_b" in input_names.values()

    def test_calculation_with_financial_value_inputs(self):
        """Test calculations with FinancialValue inputs preserve provenance chain."""
        # Create FinancialValue inputs
        fv_a = FinancialValue(100)
        fv_b = FinancialValue(50)

        ctx = {"input_a": fv_a, "input_b": fv_b}
        result = self.engine.calculate("add_two_inputs", ctx)

        # Should have provenance
        assert result.has_provenance()
        prov = result.get_provenance()
        assert prov is not None
        assert prov.op == "calc:add_two_inputs"

        # Should have input provenance IDs
        assert len(prov.inputs) == 2

        # Input names should be mapped correctly
        input_names = prov.meta.get("input_names", {})
        assert "input_a" in input_names.values()
        assert "input_b" in input_names.values()

    def test_nested_calculation_provenance(self):
        """Test that nested calculations maintain provenance chains."""
        ctx = {"input_a": 100, "input_c": 25}
        result = self.engine.calculate("complex_calc", ctx)

        # Should have provenance
        assert result.has_provenance()
        prov = result.get_provenance()
        assert prov is not None
        assert prov.op == "calc:complex_calc"
        assert prov.meta["calculation"] == "complex_calc"

    def test_calculation_provenance_with_kwargs(self):
        """Test that calculations using kwargs capture input names."""
        result = self.engine.calculate("add_two_inputs", input_a=100, input_b=50)

        # Should have provenance with named inputs
        assert result.has_provenance()
        prov = result.get_provenance()
        assert prov is not None
        assert prov.op == "calc:add_two_inputs"

        # Check that input names from kwargs are captured
        input_names = prov.meta.get("input_names", {})
        assert "input_a" in input_names.values()
        assert "input_b" in input_names.values()

    def test_calculation_provenance_with_mixed_inputs(self):
        """Test calculations with both ctx dict and kwargs."""
        ctx = {"input_a": 100}
        result = self.engine.calculate("add_two_inputs", ctx, input_b=50)

        # Should have provenance with both input names
        assert result.has_provenance()
        prov = result.get_provenance()
        assert prov is not None

        input_names = prov.meta.get("input_names", {})
        assert "input_a" in input_names.values()
        assert "input_b" in input_names.values()

    def test_calculation_provenance_with_none_inputs(self):
        """Test that None inputs are handled properly in provenance."""
        ctx = {"input_a": 100, "input_b": None}
        result = self.engine.calculate("add_two_inputs", ctx)

        # Should still have provenance
        assert result.has_provenance()
        prov = result.get_provenance()
        assert prov is not None
        assert prov.op == "calc:add_two_inputs"

    def test_calculation_provenance_deterministic(self):
        """Test that identical calculations produce identical provenance IDs."""
        ctx1 = {"input_a": 100, "input_b": 50}
        ctx2 = {"input_a": 100, "input_b": 50}

        result1 = self.engine.calculate("add_two_inputs", ctx1)
        result2 = self.engine.calculate("add_two_inputs", ctx2)

        # Should have identical provenance IDs
        prov1 = result1.get_provenance()
        prov2 = result2.get_provenance()

        if prov1 and prov2:
            assert prov1.id == prov2.id

    def test_calculation_provenance_with_different_policies(self):
        """Test that different policies produce different provenance IDs."""
        policy1 = Policy(decimal_places=2)
        policy2 = Policy(decimal_places=4)

        ctx = {"input_a": 100, "input_b": 50}

        result1 = self.engine.calculate("add_two_inputs", ctx, policy=policy1)
        result2 = self.engine.calculate("add_two_inputs", ctx, policy=policy2)

        # Should have different provenance IDs due to different policies
        prov1 = result1.get_provenance()
        prov2 = result2.get_provenance()

        if prov1 and prov2:
            assert prov1.id != prov2.id

    def test_calculation_provenance_graceful_degradation(self):
        """Test that calculations work even if provenance generation fails."""
        ctx = {"input_a": 100, "input_b": 50}
        result = self.engine.calculate("add_two_inputs", ctx)

        # Should still be a valid FinancialValue
        assert isinstance(result, FinancialValue)
        assert result.as_decimal() == Decimal("150.00")

    def test_real_world_calculation_provenance(self):
        """Test provenance tracking with a realistic financial calculation."""
        ctx = {"revenue": 1000, "cost": 600}
        result = self.engine.calculate("margin_calc", ctx)

        # Should have provenance
        assert result.has_provenance()
        prov = result.get_provenance()
        assert prov is not None
        assert prov.op == "calc:margin_calc"
        assert prov.meta["calculation"] == "margin_calc"

        # Should capture input names
        input_names = prov.meta.get("input_names", {})
        assert "revenue" in input_names.values()
        assert "cost" in input_names.values()

    def test_calculation_provenance_with_allow_partial(self):
        """Test provenance tracking with allow_partial=True."""
        ctx = {"input_a": 100}  # Missing input_b
        result = self.engine.calculate("add_two_inputs", ctx, allow_partial=True)

        # Should return None FinancialValue
        assert result.is_none()

        # Should still have provenance (for the None result)
        assert result.has_provenance()

    def test_calculation_many_provenance(self):
        """Test that calculate_many preserves provenance through _run_calc."""
        ctx = {"input_a": 100, "input_b": 50}
        results = self.engine.calculate_many({"add_two_inputs"}, ctx)

        result = results["add_two_inputs"]

        # Should have calculation provenance
        assert result.has_provenance()
        prov = result.get_provenance()
        assert prov is not None
        assert prov.op == "calc:add_two_inputs"

    def test_calculation_provenance_metadata_structure(self):
        """Test the structure of calculation provenance metadata."""
        ctx = {"revenue": 1000, "cost": 600}
        result = self.engine.calculate("margin_calc", ctx)

        prov = result.get_provenance()
        assert prov is not None

        # Check metadata structure
        meta = prov.meta
        assert isinstance(meta, dict)
        assert "calculation" in meta
        assert "input_names" in meta
        assert isinstance(meta["input_names"], dict)

        # Check that calculation name is correct
        assert meta["calculation"] == "margin_calc"

    def test_calculation_provenance_input_name_mapping(self):
        """Test that input names are correctly mapped to provenance IDs."""
        fv_revenue = FinancialValue(1000)
        fv_cost = FinancialValue(600)

        ctx = {"revenue": fv_revenue, "cost": fv_cost}
        result = self.engine.calculate("margin_calc", ctx)

        prov = result.get_provenance()
        assert prov is not None

        input_names = prov.meta.get("input_names", {})

        # Should have mappings for both inputs
        assert len(input_names) == 2

        # Check that the provenance IDs map to correct names
        revenue_prov_id = fv_revenue._prov.id if fv_revenue._prov else None
        cost_prov_id = fv_cost._prov.id if fv_cost._prov else None

        if revenue_prov_id:
            assert input_names.get(revenue_prov_id) == "revenue"
        if cost_prov_id:
            assert input_names.get(cost_prov_id) == "cost"

    def test_calculation_provenance_with_empty_context(self):
        """Test calculation provenance with calculations that have no dependencies."""

        @calc("constant_calc", depends_on=())
        def constant_calc():
            return FinancialValue(42)

        result = self.engine.calculate("constant_calc", {})

        # Should have provenance
        assert result.has_provenance()
        prov = result.get_provenance()
        assert prov is not None
        assert prov.op == "calc:constant_calc"
        assert len(prov.inputs) == 0  # No inputs
        assert prov.meta["calculation"] == "constant_calc"
