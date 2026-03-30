metricengine.registry_collections
===================================

.. automodule:: metricengine.registry_collections
   :members:
   :undoc-members:
   :show-inheritance:

Collection Class
----------------

.. autoclass:: Collection
   :members:
   :special-members: __init__

Registry Context Helpers
------------------------

.. autofunction:: using_registry

.. autofunction:: get_active_registry

Notes
-----

Collections bind decorators to a concrete registry. Built-in calculation
modules expose their collections via ``__collections__`` so
``metricengine.calculations.load_all(...)`` can register them into any
``Registry`` instance.
