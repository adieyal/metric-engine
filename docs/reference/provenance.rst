Provenance API Reference
========================

This section provides detailed API documentation for the provenance tracking system in MetricEngine.

Core Classes
------------

.. autoclass:: metricengine.provenance.Provenance
   :members:
   :undoc-members:
   :show-inheritance:

Configuration
-------------

.. autoclass:: metricengine.provenance_config.ProvenanceConfig
   :members:
   :undoc-members:
   :show-inheritance:

Configuration Functions
-----------------------

.. autofunction:: metricengine.provenance_config.get_config

.. autofunction:: metricengine.provenance_config.set_global_config

.. autofunction:: metricengine.provenance_config.update_global_config

.. autofunction:: metricengine.provenance_config.enable_provenance

.. autofunction:: metricengine.provenance_config.disable_provenance

.. autofunction:: metricengine.provenance_config.set_performance_mode

.. autofunction:: metricengine.provenance_config.set_debug_mode

Context Manager
---------------

.. autoclass:: metricengine.provenance_config.provenance_config
   :members:
   :undoc-members:
   :show-inheritance:

Utility Functions
-----------------

.. autofunction:: metricengine.provenance_config.should_track_provenance

.. autofunction:: metricengine.provenance_config.should_track_literals

.. autofunction:: metricengine.provenance_config.should_track_operations

.. autofunction:: metricengine.provenance_config.should_track_calculations

.. autofunction:: metricengine.provenance_config.is_provenance_available

.. autofunction:: metricengine.provenance_config.log_provenance_error

Hashing Functions
-----------------

.. autofunction:: metricengine.provenance.hash_literal

.. autofunction:: metricengine.provenance.hash_node

Export Functions
----------------

.. autofunction:: metricengine.provenance.to_trace_json

.. autofunction:: metricengine.provenance.explain

.. autofunction:: metricengine.provenance.get_provenance_graph

Span Management
---------------

.. autofunction:: metricengine.provenance.calc_span

FinancialValue Provenance Methods
---------------------------------

The following methods are added to the :class:`metricengine.value.FinancialValue` class for provenance access:

.. method:: FinancialValue.has_provenance()

   Check if this FinancialValue has provenance information.

   :returns: True if provenance is available, False otherwise
   :rtype: bool

.. method:: FinancialValue.get_provenance()

   Get the provenance record for this FinancialValue.

   :returns: The provenance record, or None if not available
   :rtype: Provenance or None
   :raises: ValueError if provenance is not available

.. method:: FinancialValue.get_operation()

   Get the operation type that created this FinancialValue.

   :returns: Operation type string (e.g., "+", "calc:gross_margin", "literal")
   :rtype: str or None

.. method:: FinancialValue.get_inputs()

   Get the provenance IDs of inputs used to create this FinancialValue.

   :returns: Tuple of input provenance IDs
   :rtype: tuple[str, ...] or None

Examples
--------

Basic Usage
~~~~~~~~~~~

.. code-block:: python

   from metricengine import FinancialValue

   # Create values with automatic provenance tracking
   revenue = FinancialValue(1000)
   cost = FinancialValue(600)
   margin = revenue - cost

   # Access provenance information
   if margin.has_provenance():
       prov = margin.get_provenance()
       print(f"Operation: {prov.op}")
       print(f"Inputs: {prov.inputs}")

Configuration
~~~~~~~~~~~~~

.. code-block:: python

   from metricengine.provenance_config import update_global_config, provenance_config

   # Global configuration
   update_global_config(
       track_literals=False,  # Disable literal tracking
       max_history_depth=500  # Limit history depth
   )

   # Temporary configuration
   with provenance_config(enabled=False):
       # Provenance disabled in this block
       result = expensive_calculation()

Export and Analysis
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from metricengine.provenance import to_trace_json, explain

   # Export provenance as JSON
   trace_data = to_trace_json(result)

   # Generate human-readable explanation
   explanation = explain(result, max_depth=5)
   print(explanation)

Calculation Spans
~~~~~~~~~~~~~~~~~

.. code-block:: python

   from metricengine.provenance import calc_span

   # Group calculations under a named span
   with calc_span("quarterly_analysis", quarter="Q1"):
       revenue = FinancialValue(1000)
       cost = FinancialValue(600)
       margin = revenue - cost

   # Span information is included in provenance metadata
   prov = margin.get_provenance()
   print(prov.meta["span"])  # "quarterly_analysis"

Error Handling
~~~~~~~~~~~~~~

.. code-block:: python

   from metricengine.provenance_config import log_provenance_error

   try:
       # Some operation that might fail
       result = risky_calculation()
   except Exception as e:
       # Log the error with provenance context
       log_provenance_error(e, "risky_calculation", input_value=input_val)
       # Handle the error appropriately
       result = fallback_calculation()

Performance Optimization
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from metricengine.provenance_config import set_performance_mode, provenance_config

   # Global performance optimization
   set_performance_mode()

   # Or selective optimization
   with provenance_config(
       track_literals=False,
       enable_spans=False,
       max_history_depth=100
   ):
       # Optimized calculation
       result = performance_critical_calculation()
