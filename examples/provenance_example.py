#!/usr/bin/env python3
"""
Provenance Tracking Example

This example demonstrates how to use provenance tracking in MetricEngine
to understand and audit financial calculations.
"""


from metricengine import Engine, FinancialValue
from metricengine.provenance import calc_span, explain, to_trace_json
from metricengine.provenance_config import (
    provenance_config,
    set_debug_mode,
    update_global_config,
)


def basic_provenance_example():
    """Demonstrate basic provenance tracking."""
    print("=== Basic Provenance Example ===")

    # Create financial values - provenance is tracked automatically
    revenue = FinancialValue(1000, "Q1 Revenue")
    cost = FinancialValue(600, "Q1 Cost")

    # Perform calculation
    margin = revenue - cost

    # Access provenance information
    if margin.has_provenance():
        prov = margin.get_provenance()
        print(f"Operation: {prov.op}")
        print(f"Number of inputs: {len(prov.inputs)}")
        print(f"Provenance ID: {prov.id[:16]}...")

        # Generate human-readable explanation
        explanation = explain(margin)
        print(f"\nCalculation tree:\n{explanation}")

    print()


def engine_calculation_example():
    """Demonstrate provenance with engine calculations."""
    print("=== Engine Calculation Example ===")

    # Create engine - calculations are already registered
    engine = Engine()

    # Calculate with named inputs using existing calculation
    result = engine.calculate(
        "gross_margin_ratio",
        {
            "gross_profit": 400,  # revenue - cost
            "sales": 1000,
        },
    )

    # Examine provenance
    if result.has_provenance():
        prov = result.get_provenance()
        print(f"Calculation: {prov.op}")
        print(f"Input names: {prov.meta.get('input_names', {})}")

        # Export complete provenance graph
        trace_data = to_trace_json(result)
        print(f"Total provenance nodes: {len(trace_data['nodes'])}")

    print()


def calculation_spans_example():
    """Demonstrate calculation spans for grouping operations."""
    print("=== Calculation Spans Example ===")

    # Use spans to group related calculations
    with calc_span("quarterly_analysis", quarter="Q1", year=2025, analyst="Alice"):
        revenue = FinancialValue(1000)
        cost = FinancialValue(600)
        margin = revenue - cost

        # Nested span for detailed analysis
        with calc_span("margin_analysis", metric="gross_margin"):
            margin_percent = margin / revenue

    # Examine span information in provenance
    if margin_percent.has_provenance():
        prov = margin_percent.get_provenance()
        print(f"Span: {prov.meta.get('span', 'None')}")
        print(f"Quarter: {prov.meta.get('quarter', 'None')}")
        print(f"Analyst: {prov.meta.get('analyst', 'None')}")

        # Generate detailed explanation
        explanation = explain(margin_percent, max_depth=10)
        print(f"\nDetailed calculation tree:\n{explanation}")

    print()


def configuration_example():
    """Demonstrate provenance configuration options."""
    print("=== Configuration Example ===")

    # Show current configuration
    from metricengine.provenance_config import get_config

    config = get_config()
    print(f"Provenance enabled: {config.enabled}")
    print(f"Track literals: {config.track_literals}")
    print(f"Max history depth: {config.max_history_depth}")

    # Temporary configuration change
    print("\nCalculating with provenance disabled:")
    with provenance_config(enabled=False):
        result_no_prov = FinancialValue(100) + FinancialValue(50)
        print(f"Has provenance: {result_no_prov.has_provenance()}")

    # Back to normal
    result_with_prov = FinancialValue(100) + FinancialValue(50)
    print(f"Has provenance (normal): {result_with_prov.has_provenance()}")

    print()


def export_example():
    """Demonstrate provenance export functionality."""
    print("=== Export Example ===")

    # Create a complex calculation using existing calculations
    engine = Engine()

    # Calculate with named inputs
    with calc_span("annual_calculation", year=2025):
        # First calculate gross margin
        gross_margin = engine.calculate(
            "gross_margin_ratio",
            {
                "gross_profit": 4000,  # 10000 - 6000
                "sales": 10000,
            },
        )

        # Then convert to percentage
        result = engine.calculate(
            "gross_margin_percentage", {"gross_margin_ratio": gross_margin}
        )

    # Export as JSON
    trace_data = to_trace_json(result)

    # Save to file (optional)
    # with open("provenance_trace.json", "w") as f:
    #     json.dump(trace_data, f, indent=2)

    print(f"Exported {len(trace_data['nodes'])} provenance nodes")
    print(f"Root node operation: {trace_data['nodes'][trace_data['root']]['op']}")

    # Generate human-readable explanation
    explanation = explain(result)
    print(f"\nCalculation explanation:\n{explanation}")

    print()


def performance_example():
    """Demonstrate performance considerations."""
    print("=== Performance Example ===")

    import time

    def benchmark_calculation():
        """Simple benchmark calculation."""
        total = FinancialValue(0)
        for i in range(100):
            total = total + FinancialValue(i)
        return total

    # Benchmark with provenance
    start = time.time()
    result_with = benchmark_calculation()
    time_with = time.time() - start

    # Benchmark without provenance
    with provenance_config(enabled=False):
        start = time.time()
        _ = benchmark_calculation()  # Result not used, just measuring time
        time_without = time.time() - start

    # Calculate overhead
    if time_without > 0:
        overhead = (time_with - time_without) / time_without * 100
        print(f"Provenance overhead: {overhead:.2f}%")
    else:
        print("Calculation too fast to measure overhead accurately")

    print(
        f"Result with provenance has {len(result_with.get_provenance().inputs) if result_with.has_provenance() else 0} direct inputs"
    )

    print()


def error_handling_example():
    """Demonstrate error handling and graceful degradation."""
    print("=== Error Handling Example ===")

    # Configure for graceful degradation
    update_global_config(fail_on_error=False, log_errors=True)

    # This should work even if provenance has issues
    try:
        result = FinancialValue(100) + FinancialValue(50)
        print(f"Calculation succeeded: {result}")
        print(f"Has provenance: {result.has_provenance()}")
    except Exception as e:
        print(f"Calculation failed: {e}")

    print()


def main():
    """Run all examples."""
    print("MetricEngine Provenance Tracking Examples")
    print("=" * 50)

    # Enable debug mode for detailed information
    set_debug_mode()

    # Run examples
    basic_provenance_example()
    engine_calculation_example()
    calculation_spans_example()
    configuration_example()
    export_example()
    performance_example()
    error_handling_example()

    print("All examples completed successfully!")


if __name__ == "__main__":
    main()
