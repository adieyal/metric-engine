"""Tests for provenance access and query methods in FinancialValue."""
from decimal import Decimal

import pytest

from metricengine.provenance import Provenance, calc_span
from metricengine.value import FinancialValue


class TestProvenanceAccessMethods:
    """Test suite for provenance access and query methods."""

    def test_get_provenance_basic(self):
        """Test basic get_provenance functionality."""
        fv = FinancialValue(100)

        # Should have provenance
        prov = fv.get_provenance()
        assert prov is not None
        assert isinstance(prov, Provenance)
        assert prov.op == "literal"
        assert prov.inputs == ()
        assert isinstance(prov.id, str)
        assert len(prov.id) > 0

    def test_get_provenance_none_value(self):
        """Test get_provenance with None value."""
        fv = FinancialValue(None)

        prov = fv.get_provenance()
        assert prov is not None
        assert prov.op == "literal"
        assert prov.inputs == ()

    def test_has_provenance_basic(self):
        """Test has_provenance method."""
        fv = FinancialValue(100)
        assert fv.has_provenance() is True

        # Test with None value
        fv_none = FinancialValue(None)
        assert fv_none.has_provenance() is True

    def test_get_operation_literal(self):
        """Test get_operation for literal values."""
        fv = FinancialValue(100)
        assert fv.get_operation() == "literal"

        fv_none = FinancialValue(None)
        assert fv_none.get_operation() == "literal"

    def test_get_operation_arithmetic(self):
        """Test get_operation for arithmetic operations."""
        a = FinancialValue(10)
        b = FinancialValue(5)

        # Test addition
        result_add = a + b
        assert result_add.get_operation() == "+"

        # Test subtraction
        result_sub = a - b
        assert result_sub.get_operation() == "-"

        # Test multiplication
        result_mul = a * b
        assert result_mul.get_operation() == "*"

        # Test division
        result_div = a / b
        assert result_div.get_operation() == "/"

        # Test power
        result_pow = a**2
        assert result_pow.get_operation() == "**"

    def test_get_operation_unary(self):
        """Test get_operation for unary operations."""
        a = FinancialValue(10)

        # Test negation
        result_neg = -a
        assert result_neg.get_operation() == "neg"

        # Test absolute value
        result_abs = abs(a)
        assert result_abs.get_operation() == "abs"

    def test_get_operation_conversions(self):
        """Test get_operation for conversion methods."""
        a = FinancialValue(0.15)

        # Test as_percentage
        result_pct = a.as_percentage()
        assert result_pct.get_operation() == "as_percentage"

        # Test ratio
        result_ratio = a.ratio()
        assert result_ratio.get_operation() == "ratio"

    def test_get_inputs_literal(self):
        """Test get_inputs for literal values."""
        fv = FinancialValue(100)
        inputs = fv.get_inputs()
        assert inputs == ()
        assert len(inputs) == 0

    def test_get_inputs_arithmetic(self):
        """Test get_inputs for arithmetic operations."""
        a = FinancialValue(10)
        b = FinancialValue(5)

        result = a + b
        inputs = result.get_inputs()
        assert len(inputs) == 2
        assert isinstance(inputs, tuple)

        # Inputs should be provenance IDs (strings)
        for input_id in inputs:
            assert isinstance(input_id, str)
            assert len(input_id) > 0

    def test_get_inputs_unary(self):
        """Test get_inputs for unary operations."""
        a = FinancialValue(10)

        result = -a
        inputs = result.get_inputs()
        assert len(inputs) == 1
        assert isinstance(inputs[0], str)

    def test_get_provenance_metadata_basic(self):
        """Test get_provenance_metadata for basic operations."""
        a = FinancialValue(10)

        # Literal should have unit metadata
        meta = a.get_provenance_metadata()
        assert isinstance(meta, dict)
        assert meta.get("unit") == "Dimensionless"

    def test_get_provenance_metadata_with_span(self):
        """Test get_provenance_metadata with calculation spans."""
        with calc_span("test_analysis", quarter="Q1", year=2024):
            a = FinancialValue(10)
            b = FinancialValue(5)
            result = a + b

        meta = result.get_provenance_metadata()
        assert isinstance(meta, dict)
        assert meta.get("span") == "test_analysis"
        assert "span_attrs" in meta
        assert meta["span_attrs"]["quarter"] == "Q1"
        assert meta["span_attrs"]["year"] == 2024

    def test_get_provenance_id(self):
        """Test get_provenance_id method."""
        fv = FinancialValue(100)

        prov_id = fv.get_provenance_id()
        assert isinstance(prov_id, str)
        assert len(prov_id) > 0

        # Should be consistent
        assert prov_id == fv.get_provenance_id()

        # Should match the provenance record
        prov = fv.get_provenance()
        assert prov_id == prov.id

    def test_trace_calculation_literal(self):
        """Test trace_calculation for literal values."""
        fv = FinancialValue(100)

        trace = fv.trace_calculation()
        assert isinstance(trace, str)
        assert "100.00" in trace
        assert "Literal" in trace

    def test_trace_calculation_arithmetic(self):
        """Test trace_calculation for arithmetic operations."""
        a = FinancialValue(10)
        b = FinancialValue(5)
        result = a + b

        trace = result.trace_calculation()
        assert isinstance(trace, str)
        assert "15.00" in trace  # Result value
        assert "Operation: +" in trace
        assert "Inputs: 2" in trace

    def test_get_calculation_summary(self):
        """Test get_calculation_summary method."""
        # Test literal
        literal = FinancialValue(100)
        summary = literal.get_calculation_summary()
        assert isinstance(summary, str)
        assert "literal" in summary.lower() or "no provenance" in summary.lower()

        # Test arithmetic operation
        a = FinancialValue(10)
        b = FinancialValue(5)
        result = a + b
        summary = result.get_calculation_summary()
        assert isinstance(summary, str)
        assert "+" in summary or "Op:" in summary

    def test_export_provenance_graph(self):
        """Test export_provenance_graph method."""
        a = FinancialValue(10)
        b = FinancialValue(5)
        result = a + b

        graph = result.export_provenance_graph()
        assert isinstance(graph, dict)
        assert "root" in graph
        assert "nodes" in graph
        assert isinstance(graph["nodes"], dict)

        # Should have at least the root node
        if graph["root"] is not None:
            assert graph["root"] in graph["nodes"]

    def test_has_operation(self):
        """Test has_operation method."""
        # Test literal
        literal = FinancialValue(100)
        assert literal.has_operation("literal") is True
        assert literal.has_operation("+") is False

        # Test arithmetic
        a = FinancialValue(10)
        b = FinancialValue(5)
        result = a + b
        assert result.has_operation("+") is True
        assert result.has_operation("-") is False
        assert result.has_operation("literal") is False

    def test_is_literal(self):
        """Test is_literal method."""
        # Test literal values
        literal = FinancialValue(100)
        assert literal.is_literal() is True

        literal_none = FinancialValue(None)
        assert literal_none.is_literal() is True

        # Test computed values
        a = FinancialValue(10)
        b = FinancialValue(5)
        computed = a + b
        assert computed.is_literal() is False

    def test_is_computed(self):
        """Test is_computed method."""
        # Test literal values
        literal = FinancialValue(100)
        assert literal.is_computed() is False

        # Test computed values
        a = FinancialValue(10)
        b = FinancialValue(5)
        computed = a + b
        assert computed.is_computed() is True

        # Test conversions
        percentage = literal.as_percentage()
        assert percentage.is_computed() is True

    def test_get_input_count(self):
        """Test get_input_count method."""
        # Test literal
        literal = FinancialValue(100)
        assert literal.get_input_count() == 0

        # Test binary operation
        a = FinancialValue(10)
        b = FinancialValue(5)
        binary_result = a + b
        assert binary_result.get_input_count() == 2

        # Test unary operation
        unary_result = -a
        assert unary_result.get_input_count() == 1

    def test_edge_cases_no_provenance(self):
        """Test edge cases where provenance might not be available."""
        # Create a FinancialValue with explicit None provenance
        # This simulates cases where provenance generation might fail
        from metricengine.policy import DEFAULT_POLICY

        fv = FinancialValue.__new__(FinancialValue)
        object.__setattr__(fv, "_value", Decimal("100"))
        object.__setattr__(fv, "policy", DEFAULT_POLICY)
        object.__setattr__(
            fv, "unit", FinancialValue.__dataclass_fields__["unit"].default
        )
        object.__setattr__(fv, "_is_percentage", False)
        object.__setattr__(fv, "_prov", None)

        # All methods should handle missing provenance gracefully
        assert fv.has_provenance() is False
        assert fv.get_provenance() is None
        assert fv.get_operation() is None
        assert fv.get_inputs() == ()
        assert fv.get_provenance_metadata() == {}
        assert fv.get_provenance_id() is None
        assert fv.has_operation("literal") is False
        assert fv.is_literal() is False
        assert fv.is_computed() is False
        assert fv.get_input_count() == 0

        # These should still work
        trace = fv.trace_calculation()
        assert isinstance(trace, str)

        summary = fv.get_calculation_summary()
        assert isinstance(summary, str)

        graph = fv.export_provenance_graph()
        assert isinstance(graph, dict)

    def test_nested_operations(self):
        """Test provenance access methods with nested operations."""
        a = FinancialValue(10)
        b = FinancialValue(5)
        c = FinancialValue(2)

        # Create nested operation: (a + b) * c
        intermediate = a + b
        result = intermediate * c

        # Test intermediate result
        assert intermediate.get_operation() == "+"
        assert intermediate.get_input_count() == 2
        assert intermediate.is_computed() is True

        # Test final result
        assert result.get_operation() == "*"
        assert result.get_input_count() == 2
        assert result.is_computed() is True

        # Trace should show the nested structure
        trace = result.trace_calculation()
        assert "Operation: *" in trace

    def test_consistency_across_methods(self):
        """Test that different access methods are consistent with each other."""
        a = FinancialValue(10)
        b = FinancialValue(5)
        result = a + b

        # Consistency checks
        prov = result.get_provenance()
        assert result.get_operation() == prov.op
        assert result.get_inputs() == prov.inputs
        assert result.get_provenance_metadata() == dict(prov.meta)
        assert result.get_provenance_id() == prov.id

        # Boolean methods should be consistent
        assert result.has_provenance() == (prov is not None)
        assert result.is_literal() == (result.get_operation() == "literal")
        assert result.is_computed() == (
            result.has_provenance() and not result.is_literal()
        )
        assert result.get_input_count() == len(result.get_inputs())


if __name__ == "__main__":
    pytest.main([__file__])
