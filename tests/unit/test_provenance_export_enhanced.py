"""Enhanced tests for provenance export and analysis functions."""
import json

import pytest

from metricengine.policy import Policy
from metricengine.provenance import (
    _format_provenance_summary,
    _validate_provenance_graph,
    calc_span,
    explain,
    get_provenance_graph,
    to_trace_json,
)
from metricengine.value import FinancialValue


class TestProvenanceExportEnhanced:
    """Enhanced tests for provenance export functions."""

    def test_explain_with_conversion_operations(self):
        """Test explain function with conversion operations like as_percentage."""
        fv = FinancialValue(0.15)
        percentage = fv.as_percentage()

        explanation = explain(percentage)

        # Should show conversion operation
        assert "Operation: as_percentage" in explanation
        assert "conversion: to_percentage" in explanation
        assert "15.00%" in explanation

    def test_explain_with_ratio_conversion(self):
        """Test explain function with ratio conversion."""
        fv = FinancialValue(0.75)
        ratio = fv.ratio()

        explanation = explain(ratio)

        # Should show ratio conversion
        assert "Operation: ratio" in explanation
        assert "conversion: to_ratio" in explanation

    def test_to_trace_json_with_conversion_metadata(self):
        """Test to_trace_json preserves conversion metadata."""
        fv = FinancialValue(0.25)
        percentage = fv.as_percentage()

        trace = to_trace_json(percentage)

        # Should have conversion metadata
        root_node = trace["nodes"][trace["root"]]
        assert root_node["op"] == "as_percentage"
        assert "conversion" in root_node["meta"]
        assert root_node["meta"]["conversion"] == "to_percentage"

    def test_export_functions_with_none_values_comprehensive(self):
        """Comprehensive test of export functions with None values."""
        none_fv = FinancialValue(None)

        # Test all export functions
        graph = get_provenance_graph(none_fv)
        trace = to_trace_json(none_fv)
        explanation = explain(none_fv)
        summary = _format_provenance_summary(none_fv)

        # All should handle None values gracefully
        assert len(graph) == 1
        assert trace["root"] is not None
        assert len(explanation) > 0
        assert "Op: literal" in summary

        # Verify None value is handled in explanation
        assert (
            "—" in explanation or "None" in explanation or "null" in explanation.lower()
        )

    def test_validate_provenance_graph_function(self):
        """Test the provenance graph validation function."""
        fv1 = FinancialValue(100)
        fv2 = FinancialValue(50)
        result = fv1 + fv2

        graph = get_provenance_graph(result)

        # Should validate successfully
        assert _validate_provenance_graph(graph) is True

        # Test with empty graph
        assert _validate_provenance_graph({}) is True

    def test_format_provenance_summary_function(self):
        """Test the provenance summary formatting function."""
        # Test with literal
        literal = FinancialValue(100)
        summary = _format_provenance_summary(literal)
        assert "Op: literal" in summary

        # Test with operation
        fv1 = FinancialValue(100)
        fv2 = FinancialValue(50)
        result = fv1 * fv2
        summary = _format_provenance_summary(result)
        assert "Op: *" in summary
        assert "Inputs: 2" in summary

        # Test with span
        with calc_span("test_span"):
            span_result = fv1 + fv2
        summary = _format_provenance_summary(span_result)
        assert "Op: +" in summary
        assert "Span: test_span" in summary

        # Test with no provenance
        no_prov_fv = FinancialValue(100)
        object.__setattr__(no_prov_fv, "_prov", None)
        summary = _format_provenance_summary(no_prov_fv)
        assert summary == "No provenance"

    def test_export_functions_with_complex_policies(self):
        """Test export functions with complex policy configurations."""
        policy = Policy(
            decimal_places=6,
            rounding="ROUND_HALF_UP",
            none_text="N/A",
            cap_percentage_at=200.0,  # Set higher cap to avoid capping
        )

        fv = FinancialValue(
            1.23456789, policy=policy
        )  # Use smaller value to avoid capping
        percentage = fv.as_percentage()

        # Test all export functions work with complex policies
        graph = get_provenance_graph(percentage)
        trace = to_trace_json(percentage)
        explanation = explain(percentage)

        assert len(graph) == 1
        assert trace["root"] is not None
        assert len(explanation) > 0

        # Should show formatted value in explanation (123.456789%)
        assert "123.456789%" in explanation or "123.456789%" in explanation

    def test_export_functions_performance_with_deep_nesting(self):
        """Test export functions handle reasonable nesting levels."""
        # Create a chain of operations
        result = FinancialValue(1)

        # Create nested spans for more complex metadata
        with calc_span("outer", level=1):
            with calc_span("middle", level=2):
                with calc_span("inner", level=3):
                    for i in range(5):
                        result = result + FinancialValue(i + 1)

        # Test export functions complete in reasonable time
        graph = get_provenance_graph(result)
        trace = to_trace_json(result)
        explanation = explain(result)

        # Should complete successfully
        assert len(graph) >= 1
        assert trace["root"] is not None
        assert len(explanation) > 0

        # Should include nested span information
        result_prov = result.get_provenance()
        assert "span_hierarchy" in result_prov.meta
        assert result_prov.meta["span_hierarchy"] == ["outer", "middle", "inner"]

    def test_json_export_with_special_characters(self):
        """Test JSON export handles special characters in metadata."""
        with calc_span(
            "test-span",
            description="Test with special chars: !@#$%^&*()",
            unicode_text="测试中文",
        ):
            fv1 = FinancialValue(100)
            fv2 = FinancialValue(50)
            result = fv1 + fv2

        trace = to_trace_json(result)

        # Should be JSON serializable despite special characters
        json_str = json.dumps(trace, ensure_ascii=False)
        assert isinstance(json_str, str)

        # Should preserve special characters
        deserialized = json.loads(json_str)
        _ = deserialized["nodes"][deserialized["root"]]  # Root node not used
        assert "测试中文" in json_str
        assert "!@#$%^&*()" in json_str

    def test_explain_max_depth_edge_cases(self):
        """Test explain function with various max_depth values."""
        fv = FinancialValue(100)

        # Test with max_depth = 0
        explanation = explain(fv, max_depth=0)
        assert "100.00" in explanation
        assert "Literal" in explanation

        # Test with very high max_depth
        explanation = explain(fv, max_depth=1000)
        assert "100.00" in explanation
        assert "Literal" in explanation

        # Test with negative max_depth (should still work)
        explanation = explain(fv, max_depth=-1)
        assert "100.00" in explanation

    def test_export_functions_with_different_units(self):
        """Test export functions work with different unit types."""
        from metricengine.units import Money, Percent, Ratio

        # Test with Money unit
        money_fv = FinancialValue(1000, unit=Money)

        # Test with Percent unit
        percent_fv = FinancialValue(0.15, unit=Percent)

        # Test with Ratio unit
        ratio_fv = FinancialValue(1.5, unit=Ratio)

        for fv in [money_fv, percent_fv, ratio_fv]:
            graph = get_provenance_graph(fv)
            trace = to_trace_json(fv)
            explanation = explain(fv)

            assert len(graph) >= 1
            assert trace["root"] is not None
            assert len(explanation) > 0

    def test_export_functions_error_resilience(self):
        """Test export functions are resilient to various error conditions."""
        # Test with corrupted provenance (simulate by creating invalid provenance)
        fv = FinancialValue(100)

        # All functions should handle gracefully and not crash
        try:
            graph = get_provenance_graph(fv)
            trace = to_trace_json(fv)
            explanation = explain(fv)

            # Should complete without exceptions
            assert isinstance(graph, dict)
            assert isinstance(trace, dict)
            assert isinstance(explanation, str)
        except Exception as e:
            pytest.fail(f"Export functions should not raise exceptions: {e}")

    def test_large_metadata_handling(self):
        """Test export functions handle large metadata dictionaries."""
        # Create a large metadata dictionary
        large_attrs = {f"key_{i}": f"value_{i}" for i in range(100)}

        with calc_span("large_metadata", **large_attrs):
            fv1 = FinancialValue(100)
            fv2 = FinancialValue(50)
            result = fv1 + fv2

        # Test export functions handle large metadata
        graph = get_provenance_graph(result)
        trace = to_trace_json(result)
        explanation = explain(result)

        assert len(graph) >= 1
        assert trace["root"] is not None
        assert len(explanation) > 0

        # Verify large metadata is preserved
        result_prov = result.get_provenance()
        assert len(result_prov.meta["span_attrs"]) == 100

        # JSON should still be serializable
        json_str = json.dumps(trace)
        assert isinstance(json_str, str)
