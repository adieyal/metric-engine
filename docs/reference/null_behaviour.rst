metricengine.null_behaviour
==============================

.. automodule:: metricengine.null_behaviour
   :members:
   :undoc-members:
   :show-inheritance:

Null Behaviour Enum
-------------------

.. autoclass:: NullBehaviour
   :members:
   :undoc-members:

   .. attribute:: RAISE

      Raise an exception when null values are encountered.

   .. attribute:: SKIP

      Skip null values in calculations.

   .. attribute:: PROPAGATE

      Propagate null values through calculations.

   .. attribute:: DEFAULT

      Use default values when nulls are encountered.

Null Handling Functions
-----------------------

.. autofunction:: handle_null

.. autofunction:: is_null

.. autofunction:: null_safe_operation
