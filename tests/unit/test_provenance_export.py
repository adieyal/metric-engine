"""Tests for provenance export and analysis functions."""

from metricengine.policy import Policy
from metricengine.provenance import (
    calc_span,
    explain,
    get_provenance_graph,
    to_trace_json,
)
from metricengine.value import FinancialValue


class TestProvenanceExport:
    """Test provenance export and analysis functions."""

    def test_get_provenance_graph_simple(self):
        """Test get_provenance_graph with a simple FinancialValue."""
        from metricengine.provenance_config import provenance_config

        # Ensure provenance is enabled for this test
        with provenance_config(enabled=True, track_literals=True):
            fv = FinancialValue(100)

            graph = get_provenance_graph(fv)

            # Should contain one provenance record
            assert len(graph) == 1

            # Should contain the root provenance
            root_prov = fv.get_provenance()
            assert root_prov.id in graph
            assert graph[root_prov.id] == root_prov

    def test_get_provenance_graph_no_provenance(self):
        """Test get_provenance_graph with FinancialValue without provenance."""
        # Create a FinancialValue and manually remove provenance
        fv = FinancialValue(100)
        object.__setattr__(fv, "_prov", None)

        graph = get_provenance_graph(fv)

        # Should return empty graph
        assert len(graph) == 0
        assert graph == {}

    def test_get_provenance_graph_arithmetic_result(self):
        """Test get_provenance_graph with result of arithmetic operation."""
        fv1 = FinancialValue(100)
        fv2 = FinancialValue(50)
        result = fv1 + fv2

        graph = get_provenance_graph(result)

        # Should contain only the result's provenance (not the full tree)
        assert len(graph) == 1

        result_prov = result.get_provenance()
        assert result_prov.id in graph
        assert graph[result_prov.id] == result_prov
        assert graph[result_prov.id].op == "+"

    def test_to_trace_json_simple(self):
        """Test to_trace_json with a simple FinancialValue."""
        fv = FinancialValue(100)

        trace = to_trace_json(fv)

        # Should have root and nodes
        assert "root" in trace
        assert "nodes" in trace

        # Root should be the provenance ID
        root_prov = fv.get_provenance()
        assert trace["root"] == root_prov.id

        # Should have one node
        assert len(trace["nodes"]) == 1
        assert root_prov.id in trace["nodes"]

        # Node should have correct structure
        node = trace["nodes"][root_prov.id]
        assert node["id"] == root_prov.id
        assert node["op"] == "literal"
        assert node["inputs"] == []
        assert isinstance(node["meta"], dict)

    def test_to_trace_json_no_provenance(self):
        """Test to_trace_json with FinancialValue without provenance."""
        # Create a FinancialValue and manually remove provenance
        fv = FinancialValue(100)
        object.__setattr__(fv, "_prov", None)

        trace = to_trace_json(fv)

        # Should return empty trace
        assert trace["root"] is None
        assert trace["nodes"] == {}

    def test_to_trace_json_arithmetic_result(self):
        """Test to_trace_json with result of arithmetic operation."""
        fv1 = FinancialValue(100)
        fv2 = FinancialValue(50)
        result = fv1 + fv2

        trace = to_trace_json(result)

        # Should have root and nodes
        assert "root" in trace
        assert "nodes" in trace

        # Root should be the result's provenance ID
        result_prov = result.get_provenance()
        assert trace["root"] == result_prov.id

        # Should have one node (only the result, not the full tree)
        assert len(trace["nodes"]) == 1
        assert result_prov.id in trace["nodes"]

        # Node should have correct structure
        node = trace["nodes"][result_prov.id]
        assert node["id"] == result_prov.id
        assert node["op"] == "+"
        assert len(node["inputs"]) == 2
        assert isinstance(node["meta"], dict)

    def test_to_trace_json_with_metadata(self):
        """Test to_trace_json preserves metadata correctly."""
        fv1 = FinancialValue(100)
        fv2 = FinancialValue(50)

        # Create result with span context
        with calc_span("test_calculation", purpose="testing"):
            result = fv1 + fv2

        trace = to_trace_json(result)

        # Check that metadata is preserved
        result_prov = result.get_provenance()
        node = trace["nodes"][result_prov.id]

        # Should have span information in metadata
        assert "span" in node["meta"]
        assert node["meta"]["span"] == "test_calculation"
        assert "span_attrs" in node["meta"]
        assert node["meta"]["span_attrs"]["purpose"] == "testing"

    def test_explain_simple(self):
        """Test explain function with a simple FinancialValue."""
        fv = FinancialValue(100)

        explanation = explain(fv)

        # Should contain value and operation info
        assert "100.00" in explanation
        assert "Literal" in explanation
        assert "Value:" in explanation

    def test_explain_no_provenance(self):
        """Test explain function with FinancialValue without provenance."""
        # Create a FinancialValue and manually remove provenance
        fv = FinancialValue(100)
        object.__setattr__(fv, "_prov", None)

        explanation = explain(fv)

        # Should indicate no provenance available
        assert "100.00" in explanation
        assert "no provenance available" in explanation

    def test_explain_arithmetic_result(self):
        """Test explain function with result of arithmetic operation."""
        fv1 = FinancialValue(100)
        fv2 = FinancialValue(50)
        result = fv1 + fv2

        explanation = explain(result)

        # Should contain result value and operation info
        assert "150.00" in explanation
        assert "Operation: +" in explanation
        assert "Inputs: 2 operand(s)" in explanation
        assert "Value:" in explanation

    def test_explain_with_span_metadata(self):
        """Test explain function includes span information."""
        fv1 = FinancialValue(100)
        fv2 = FinancialValue(50)

        # Create result with span context
        with calc_span("quarterly_analysis", quarter="Q1"):
            result = fv1 + fv2

        explanation = explain(result)

        # Should include span information
        assert "span: quarterly_analysis" in explanation
        assert "Operation: +" in explanation

    def test_explain_max_depth(self):
        """Test explain function respects max_depth parameter."""
        fv = FinancialValue(100)

        # Test with very low max_depth
        explanation = explain(fv, max_depth=0)

        # Should still work but might be truncated
        assert "100.00" in explanation
        assert "Value:" in explanation

    def test_explain_complex_calculation(self):
        """Test explain function with more complex calculation."""
        fv1 = FinancialValue(100)
        fv2 = FinancialValue(50)
        fv3 = FinancialValue(25)

        # Create a more complex calculation
        intermediate = fv1 + fv2  # 150
        result = intermediate * fv3  # 3750

        explanation = explain(result)

        # Should show the multiplication operation (value might be formatted with commas)
        assert "3750.00" in explanation or "3,750.00" in explanation
        assert "Operation: *" in explanation
        assert "Inputs: 2 operand(s)" in explanation

    def test_json_serialization_roundtrip(self):
        """Test that JSON export can be serialized and deserialized."""
        import json

        fv1 = FinancialValue(100)
        fv2 = FinancialValue(50)
        result = fv1 + fv2

        trace = to_trace_json(result)

        # Should be JSON serializable
        json_str = json.dumps(trace)
        assert isinstance(json_str, str)

        # Should be deserializable
        deserialized = json.loads(json_str)
        assert deserialized == trace

    def test_export_functions_with_different_policies(self):
        """Test export functions work with different policies."""
        policy = Policy(decimal_places=4)
        fv = FinancialValue(100.123456, policy=policy)

        # Test all export functions
        graph = get_provenance_graph(fv)
        trace = to_trace_json(fv)
        explanation = explain(fv)

        # Should all work without errors
        assert len(graph) == 1
        assert trace["root"] is not None
        assert "100.1235" in explanation  # Should show formatted value

    def test_export_functions_with_none_values(self):
        """Test export functions handle None values correctly."""
        fv = FinancialValue(None)

        # Test all export functions
        graph = get_provenance_graph(fv)
        trace = to_trace_json(fv)
        explanation = explain(fv)

        # Should all work without errors
        assert len(graph) == 1
        assert trace["root"] is not None
        # None values might be displayed as "—" or other formatting
        assert (
            "None" in explanation or "null" in explanation.lower() or "—" in explanation
        )

    def test_large_calculation_performance(self):
        """Test export functions perform reasonably with larger calculations."""
        # Create a chain of calculations
        result = FinancialValue(1)
        for i in range(10):
            result = result + FinancialValue(i)

        # Test export functions don't crash or take too long
        graph = get_provenance_graph(result)
        trace = to_trace_json(result)
        explanation = explain(result)

        # Should complete successfully
        assert len(graph) >= 1
        assert trace["root"] is not None
        assert len(explanation) > 0
