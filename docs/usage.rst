Usage
=====

Installation::

   pip install metric-engine

With extras (Babel only in core)::

   pip install "metric-engine[babel]"

Quick start::

   from metricengine import format_currency, register_calculation, calculate

   print(format_currency(1234.5, "USD"))

   @register_calculation("add")
   def add(a: int, b: int) -> int:
       return a + b

   print(calculate("add", a=1, b=2))
