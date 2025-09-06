"""Simple integration tests for provenance export functions."""
import json
from decimal import Decimal

from metricengine import (
    FinancialValue,
    calc_span,
    explain,
    get_provenance_graph,
    to_trace_json,
)


class TestProvenanceExportSimple:
    """Test provenance export functions with simple scenarios."""

    def test_arithmetic_with_spans_export(self):
        """Test export functions with arithmetic operations and spans."""

        with calc_span("test_calculation", purpose="testing", user="test_user"):
            # Create some values and perform operations
            base = FinancialValue(1000)
            rate = FinancialValue(0.15)
            tax = base * rate
            net = base - tax

        # Verify calculations
        assert tax.as_decimal() == Decimal("150.00")
        assert net.as_decimal() == Decimal("850.00")

        # Test provenance graph
        tax_graph = get_provenance_graph(tax)
        assert len(tax_graph) == 1

        tax_prov = tax.get_provenance()
        assert tax_prov.op == "*"
        assert "span" in tax_prov.meta
        assert tax_prov.meta["span"] == "test_calculation"
        assert tax_prov.meta["span_attrs"]["purpose"] == "testing"

        # Test JSON export
        tax_trace = to_trace_json(tax)
        assert tax_trace["root"] == tax_prov.id
        assert len(tax_trace["nodes"]) == 1

        tax_node = tax_trace["nodes"][tax_prov.id]
        assert tax_node["op"] == "*"
        assert tax_node["meta"]["span"] == "test_calculation"
        assert tax_node["meta"]["span_attrs"]["purpose"] == "testing"

        # Test explanation
        tax_explanation = explain(tax)
        assert "150.00" in tax_explanation
        assert "Operation: *" in tax_explanation
        assert "span: test_calculation" in tax_explanation

        # Test JSON serialization
        json_str = json.dumps(tax_trace)
        deserialized = json.loads(json_str)
        assert deserialized == tax_trace

    def test_nested_spans_export(self):
        """Test export functions with nested spans."""

        with calc_span("outer_span", level=1):
            outer_value = FinancialValue(100)

            with calc_span("inner_span", level=2):
                inner_value = FinancialValue(50)
                result = outer_value + inner_value

        # Verify calculation
        assert result.as_decimal() == Decimal("150.00")

        # Test provenance
        result_prov = result.get_provenance()
        assert result_prov.op == "+"
        assert "span" in result_prov.meta
        assert result_prov.meta["span"] == "inner_span"
        assert "span_hierarchy" in result_prov.meta
        assert result_prov.meta["span_hierarchy"] == ["outer_span", "inner_span"]

        # Test export functions
        graph = get_provenance_graph(result)
        trace = to_trace_json(result)
        explanation = explain(result)

        # Verify span information is preserved
        assert len(graph) == 1
        assert trace["nodes"][result_prov.id]["meta"]["span"] == "inner_span"
        assert "span: inner_span" in explanation

    def test_complex_arithmetic_chain_export(self):
        """Test export functions with a chain of arithmetic operations."""

        with calc_span("calculation_chain"):
            # Build a calculation chain
            start = FinancialValue(100)
            step1 = start * FinancialValue(2)  # 200
            step2 = step1 + FinancialValue(50)  # 250
            step3 = step2 / FinancialValue(5)  # 50
            final = step3 - FinancialValue(10)  # 40

        # Verify final result
        assert final.as_decimal() == Decimal("40.00")

        # Test each step has proper provenance
        for value, expected_op in [
            (step1, "*"),
            (step2, "+"),
            (step3, "/"),
            (final, "-"),
        ]:
            prov = value.get_provenance()
            assert prov.op == expected_op
            assert "span" in prov.meta
            assert prov.meta["span"] == "calculation_chain"

            # Test export functions work for each step
            graph = get_provenance_graph(value)
            trace = to_trace_json(value)
            explanation = explain(value)

            assert len(graph) == 1
            assert trace["root"] is not None
            assert "calculation_chain" in explanation

    def test_export_functions_error_handling(self):
        """Test export functions handle edge cases gracefully."""

        # Test with None value
        none_value = FinancialValue(None)

        graph = get_provenance_graph(none_value)
        trace = to_trace_json(none_value)
        explanation = explain(none_value)

        assert len(graph) == 1
        assert trace["root"] is not None
        assert len(explanation) > 0

        # Test with value without provenance
        no_prov_value = FinancialValue(100)
        object.__setattr__(no_prov_value, "_prov", None)

        graph = get_provenance_graph(no_prov_value)
        trace = to_trace_json(no_prov_value)
        explanation = explain(no_prov_value)

        assert graph == {}
        assert trace["root"] is None
        assert trace["nodes"] == {}
        assert "no provenance available" in explanation

    def test_export_functions_with_different_value_types(self):
        """Test export functions work with different value types and policies."""
        from metricengine import Policy

        # Test with custom policy
        policy = Policy(decimal_places=4)
        precise_value = FinancialValue(123.456789, policy=policy)

        # Test with percentage
        percentage = FinancialValue(0.15).as_percentage()

        # Test with large numbers
        large_value = FinancialValue(1000000)

        for value in [precise_value, percentage, large_value]:
            # All export functions should work
            graph = get_provenance_graph(value)
            trace = to_trace_json(value)
            explanation = explain(value)

            assert len(graph) >= 1
            assert trace["root"] is not None
            assert len(explanation) > 0

            # JSON should be serializable
            json_str = json.dumps(trace)
            assert isinstance(json_str, str)

    def test_real_world_scenario_export(self):
        """Test export functions with a realistic financial calculation."""

        with calc_span(
            "monthly_report", month="January", year=2024, department="Sales"
        ):
            # Monthly sales data
            gross_sales = FinancialValue(50000)
            returns = FinancialValue(2000)
            discounts = FinancialValue(3000)

            # Calculate net sales
            net_sales = gross_sales - returns - discounts

            # Calculate commission (5%)
            commission_rate = FinancialValue(0.05)
            commission = net_sales * commission_rate

            # Calculate final amount
            final_amount = net_sales - commission

        # Verify calculations
        assert net_sales.as_decimal() == Decimal("45000.00")
        assert commission.as_decimal() == Decimal("2250.00")
        assert final_amount.as_decimal() == Decimal("42750.00")

        # Test comprehensive export for final amount
        graph = get_provenance_graph(final_amount)
        trace = to_trace_json(final_amount)
        explanation = explain(final_amount)

        # Verify business context is captured
        final_prov = final_amount.get_provenance()
        assert final_prov.meta["span"] == "monthly_report"
        assert final_prov.meta["span_attrs"]["month"] == "January"
        assert final_prov.meta["span_attrs"]["department"] == "Sales"

        # Verify export formats
        assert len(graph) == 1
        assert trace["root"] == final_prov.id
        assert "monthly_report" in explanation
        assert "42,750.00" in explanation or "42750.00" in explanation

        # Test JSON export includes business context
        json_export = json.dumps(trace, indent=2)
        assert "monthly_report" in json_export
        assert "January" in json_export
        assert "Sales" in json_export
