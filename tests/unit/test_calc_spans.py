"""Tests for calculation span context management."""

import pytest

from metricengine.provenance import (
    _get_current_span_info,
    _pop_calc_context,
    _push_calc_context,
    calc_span,
)
from metricengine.value import FinancialValue


class TestSpanContextManagement:
    """Test span context management functions."""

    def test_push_pop_calc_context(self):
        """Test basic push/pop functionality."""
        # Initially no spans
        assert _get_current_span_info() == {}

        # Push a span
        token = _push_calc_context("test_span", {"attr1": "value1"})

        # Should have span info now
        span_info = _get_current_span_info()
        assert span_info["span"] == "test_span"
        assert span_info["span_attrs"] == {"attr1": "value1"}
        assert "span_hierarchy" not in span_info  # Single span, no hierarchy

        # Pop the span
        _pop_calc_context(token)

        # Should be empty again
        assert _get_current_span_info() == {}

    def test_nested_spans(self):
        """Test nested span functionality."""
        # Push first span
        token1 = _push_calc_context("outer_span", {"level": "outer"})

        span_info = _get_current_span_info()
        assert span_info["span"] == "outer_span"
        assert "span_hierarchy" not in span_info

        # Push nested span
        token2 = _push_calc_context("inner_span", {"level": "inner"})

        span_info = _get_current_span_info()
        assert span_info["span"] == "inner_span"
        assert span_info["span_attrs"] == {"level": "inner"}
        assert span_info["span_hierarchy"] == ["outer_span", "inner_span"]
        assert span_info["span_depth"] == 2

        # Pop inner span
        _pop_calc_context(token2)

        span_info = _get_current_span_info()
        assert span_info["span"] == "outer_span"
        assert "span_hierarchy" not in span_info

        # Pop outer span
        _pop_calc_context(token1)

        assert _get_current_span_info() == {}

    def test_span_with_empty_attrs(self):
        """Test span with no attributes."""
        token = _push_calc_context("simple_span", {})

        span_info = _get_current_span_info()
        assert span_info["span"] == "simple_span"
        assert "span_attrs" not in span_info  # Empty attrs not included

        _pop_calc_context(token)

    def test_deeply_nested_spans(self):
        """Test deeply nested spans."""
        tokens = []

        # Create 5 nested spans
        for i in range(5):
            token = _push_calc_context(f"span_{i}", {"level": i})
            tokens.append(token)

        span_info = _get_current_span_info()
        assert span_info["span"] == "span_4"
        assert span_info["span_depth"] == 5
        expected_hierarchy = [f"span_{i}" for i in range(5)]
        assert span_info["span_hierarchy"] == expected_hierarchy

        # Pop all spans in reverse order
        for token in reversed(tokens):
            _pop_calc_context(token)

        assert _get_current_span_info() == {}


class TestCalcSpanContextManager:
    """Test the calc_span context manager."""

    def test_basic_context_manager(self):
        """Test basic context manager usage."""
        assert _get_current_span_info() == {}

        with calc_span("test_calculation"):
            span_info = _get_current_span_info()
            assert span_info["span"] == "test_calculation"
            assert "span_attrs" not in span_info

        # Should be cleaned up after context
        assert _get_current_span_info() == {}

    def test_context_manager_with_attrs(self):
        """Test context manager with attributes."""
        with calc_span("quarterly_analysis", quarter="Q1", year=2024):
            span_info = _get_current_span_info()
            assert span_info["span"] == "quarterly_analysis"
            assert span_info["span_attrs"] == {"quarter": "Q1", "year": 2024}

        assert _get_current_span_info() == {}

    def test_nested_context_managers(self):
        """Test nested context managers."""
        with calc_span("outer", level="outer"):
            with calc_span("inner", level="inner"):
                span_info = _get_current_span_info()
                assert span_info["span"] == "inner"
                assert span_info["span_hierarchy"] == ["outer", "inner"]
                assert span_info["span_depth"] == 2

            # Back to outer span
            span_info = _get_current_span_info()
            assert span_info["span"] == "outer"
            assert "span_hierarchy" not in span_info

        assert _get_current_span_info() == {}

    def test_context_manager_exception_handling(self):
        """Test that context manager cleans up even with exceptions."""
        with pytest.raises(ValueError):
            with calc_span("error_span"):
                span_info = _get_current_span_info()
                assert span_info["span"] == "error_span"
                raise ValueError("Test error")

        # Should still be cleaned up
        assert _get_current_span_info() == {}


class TestSpanProvenanceIntegration:
    """Test integration of spans with provenance tracking."""

    def test_arithmetic_with_span(self):
        """Test that arithmetic operations capture span information."""
        with calc_span("test_calculation", operation="addition"):
            a = FinancialValue(100)
            b = FinancialValue(50)
            result = a + b

        # Check that span information is in provenance
        prov = result.get_provenance()
        assert prov is not None
        assert prov.meta.get("span") == "test_calculation"
        assert prov.meta.get("span_attrs") == {"operation": "addition"}

    def test_nested_spans_in_provenance(self):
        """Test that nested spans are captured in provenance."""
        with calc_span("outer_calc", level="outer"):
            a = FinancialValue(100)

            with calc_span("inner_calc", level="inner"):
                b = FinancialValue(50)
                result = a + b

        prov = result.get_provenance()
        assert prov.meta.get("span") == "inner_calc"
        assert prov.meta.get("span_hierarchy") == ["outer_calc", "inner_calc"]
        assert prov.meta.get("span_depth") == 2
        assert prov.meta.get("span_attrs") == {"level": "inner"}

    def test_operations_outside_span_no_span_info(self):
        """Test that operations outside spans don't have span info."""
        a = FinancialValue(100)
        b = FinancialValue(50)
        result = a + b

        prov = result.get_provenance()
        assert "span" not in prov.meta
        assert "span_attrs" not in prov.meta
        assert "span_hierarchy" not in prov.meta

    def test_mixed_span_and_no_span_operations(self):
        """Test mixing operations with and without spans."""
        # Operation outside span
        a = FinancialValue(100)
        b = FinancialValue(50)

        # Operation inside span
        with calc_span("calculation", step="addition"):
            result1 = a + b  # Should have span info

        # Operation outside span again
        result2 = result1 * FinancialValue(2)  # Should not have span info

        # Check first result has span info
        prov1 = result1.get_provenance()
        assert prov1.meta.get("span") == "calculation"
        assert prov1.meta.get("span_attrs") == {"step": "addition"}

        # Check second result doesn't have span info
        prov2 = result2.get_provenance()
        assert "span" not in prov2.meta

    def test_span_with_complex_calculation(self):
        """Test span tracking with complex multi-step calculation."""
        with calc_span(
            "profit_calculation", analysis_type="quarterly", department="sales"
        ):
            revenue = FinancialValue(10000)
            cost_of_goods = FinancialValue(6000)
            operating_expenses = FinancialValue(2000)

            gross_profit = revenue - cost_of_goods
            net_profit = gross_profit - operating_expenses

        # All intermediate results should have span info
        gross_prov = gross_profit.get_provenance()
        assert gross_prov.meta.get("span") == "profit_calculation"
        assert gross_prov.meta.get("span_attrs") == {
            "analysis_type": "quarterly",
            "department": "sales",
        }

        net_prov = net_profit.get_provenance()
        assert net_prov.meta.get("span") == "profit_calculation"
        assert net_prov.meta.get("span_attrs") == {
            "analysis_type": "quarterly",
            "department": "sales",
        }

    def test_span_info_in_literal_provenance(self):
        """Test that literal values created within spans don't get span info."""
        # Literal values should not include span information
        # as they are not operations
        with calc_span("test_span"):
            value = FinancialValue(100)

        prov = value.get_provenance()
        assert prov.op == "literal"
        # Literals should not have span info since they're not operations
        assert "span" not in prov.meta

    def test_span_with_special_characters(self):
        """Test span names and attributes with special characters."""
        with calc_span(
            "test-span_with.special@chars", attr_with_special="value:with|special&chars"
        ):
            a = FinancialValue(100)
            b = FinancialValue(50)
            result = a + b

        prov = result.get_provenance()
        assert prov.meta.get("span") == "test-span_with.special@chars"
        assert prov.meta.get("span_attrs") == {
            "attr_with_special": "value:with|special&chars"
        }


class TestSpanThreadSafety:
    """Test thread safety of span context management."""

    def test_context_var_isolation(self):
        """Test that context variables provide proper isolation."""
        import threading
        import time

        results = {}

        def worker(worker_id, span_name):
            with calc_span(span_name, worker_id=worker_id):
                # Small delay to ensure threads overlap
                time.sleep(0.01)

                a = FinancialValue(100)
                b = FinancialValue(worker_id)
                result = a + b

                prov = result.get_provenance()
                results[worker_id] = {
                    "span": prov.meta.get("span"),
                    "worker_id": prov.meta.get("span_attrs", {}).get("worker_id"),
                }

        # Start multiple threads with different spans
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker, args=(i, f"worker_span_{i}"))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify each thread had its own span context
        for i in range(5):
            assert results[i]["span"] == f"worker_span_{i}"
            assert results[i]["worker_id"] == i
