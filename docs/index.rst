Metric Engine Documentation
=============================

**Metric Engine** is a robust Python library designed for precision financial calculations with strong typing, policy-driven behavior, and bulletproof error handling.

Overview
--------

Metric Engine provides a comprehensive foundation for building financial applications that require:

* **Type-safe financial calculations** with units (Money, Ratios, Percentages)
* **Policy-driven formatting** and rounding behavior
* **Null-safe operations** that gracefully handle missing data
* **Extensible calculation registry** for domain-specific financial models
* **Decimal precision** throughout to avoid floating-point errors

Whether you're building accounting software, financial analytics, or business intelligence tools, Metric Engine gives you the building blocks to handle money, percentages, and ratios with confidence.

Key Features
------------

**🏷️ Strongly Typed Financial Values**
   Financial values carry their unit type (Money, Ratio, Percent) and policy information, preventing unit mismatches and ensuring consistent formatting.

**🔒 Immutable & Safe**
   All operations return new instances. Division by zero and invalid operations return ``None`` instead of crashing, with policy controls for strict vs. lenient behavior.

**📐 Decimal Precision**
   Built on Python's ``Decimal`` type to eliminate floating-point precision issues that plague financial calculations.

**🔍 Complete Calculation Traceability**
   Automatic provenance tracking creates complete audit trails for every calculation. Generate human-readable explanations, export JSON graphs for compliance, and trace exactly how any value was derived.

**🔧 Extensible Calculation Engine**
   Register custom calculations in organized collections. The dependency engine automatically resolves calculation graphs and handles circular dependencies.

**🌐 Internationalization Ready**
   Optional Babel integration for currency and percentage formatting in multiple locales.

Quick Example
-------------

.. code-block:: python

   from metricengine import FV
   from metricengine.units import Money, Percent
   from metricengine.provenance import explain, to_trace_json

   # Type-safe financial calculations
   revenue = FV(150000, Money)
   tax_rate = FV(0.25, Percent)  # 25%

   # Safe arithmetic with automatic type handling
   taxes = revenue * tax_rate    # Returns FV[Money]
   net_income = revenue - taxes  # Returns FV[Money]

   print(f"Revenue: {revenue}")           # Revenue: $150,000.00
   print(f"Net Income: {net_income}")     # Net Income: $112,500.00

   # 🔍 Automatic calculation traceability
   print("\nHow was net income calculated?")
   print(explain(net_income))
   # Output:
   # subtract(150000.00, 37500.00) = 112500.00
   #   ├─ literal(150000.00)
   #   └─ multiply(150000.00, 0.25) = 37500.00
   #     ├─ literal(150000.00)
   #     └─ literal(0.25)

   # Export complete audit trail as JSON
   audit_trail = to_trace_json(net_income)
   print(f"Audit trail contains {len(audit_trail['nodes'])} calculation steps")

   # Graceful handling of missing data
   missing_data = None
   safe_calc = revenue * missing_data     # Returns FV.none(), doesn't crash

What Makes It Different
-----------------------

Unlike basic financial libraries, Metric Engine is designed for **production financial software** where correctness, safety, and maintainability are paramount:

* **No silent errors**: Invalid operations return ``None`` or raise clear exceptions
* **Policy consistency**: Rounding, formatting, and error handling follow configurable policies
* **Complete audit trails**: Every calculation maintains tamper-evident provenance for debugging and compliance
* **Framework integration**: Optional Django plugins and extensible architecture

.. toctree::
   :maxdepth: 2
   :caption: Getting Started:

   quickstart

.. toctree::
   :maxdepth: 2
   :caption: User Guide:

   concepts/financial_value
   concepts/policy
   concepts/policy_context
   concepts/formatting
   concepts/null_behaviour
   concepts/units
   concepts/registry_collections
   concepts/engine
   concepts/reductions_utils
   concepts/provenance

.. toctree::
   :maxdepth: 2
   :caption: Tutorials:

   tutorials/tour
   tutorials/money_tax_percent
   tutorials/domain_package
   tutorials/strict_vs_safe
   tutorials/formatting

.. toctree::
   :maxdepth: 2
   :caption: How-To Guides:

   howto/new_calc
   howto/cross_package_deps
   howto/custom_reducers
   howto/new_unit
   howto/custom_policy
   howto/internationalization
   howto/custom_rendering
   howto/zero_denominator
   howto/testing_calcs
   howto/provenance_configuration
   howto/provenance_usage
   howto/provenance_best_practices

.. toctree::
   :maxdepth: 2
   :caption: API Reference:

   reference/api_index

.. toctree::
   :maxdepth: 2
   :caption: Design Documentation:

   design/policy_resolution
   design/null_strategy
   design/unit_algebra
   design/equality_hashing
   design/performance

.. toctree::
   :maxdepth: 1
   :caption: Development:

   contributing
   testing
   changelog
   faq
   glossary
   license

Legacy Documentation
-------------------

.. toctree::
   :maxdepth: 1
   :caption: Legacy:

   usage
   calc_collections_migration
   api
