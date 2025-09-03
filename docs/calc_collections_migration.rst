Migration guidelines for converting calculation collections to the new format
=============================================================================

These instructions are for an LLM (or human) to migrate existing calculations to **namespaced, typed** registrations using ``Collection``, phantom units, and policy-aware semantics.

-----------------------------------------------------------------------

0) Goals (what "done" looks like)
---------------------------------

- **Namespaced registration**: Every calculation is registered via a namespaced ``Collection`` (e.g., ``pricing.gross_profit``).
- **String dependencies**: Dependencies use string names with relative or absolute qualification (see §3).
- **Phantom units**: Public signatures use phantom units (``FinancialValue[Money]``, ``FinancialValue[Ratio]``, etc.).
- **Ratios over percents**: Calculations return ratios for rate-like results; provide a separate ``..._percent`` wrapper only when needed.
- **Precision**: No float math for precision-sensitive ops; favor ``Decimal`` (and ``Context.ln/exp`` for pow/root).
- **Policy-driven None/invalid handling**: Handling is policy-driven (``arithmetic_strict``) and otherwise returns ``FV.none(policy)``.
- **Graph hygiene**: Cross-package deps compile & resolve; the graph is cycle-free.

1) File & import layout
-----------------------

1. Keep a single canonical ``units.py``, ``value.py``, ``policy.py``, ``registry.py``, ``registry_collections.py`` at the package root.
2. Place calculations under ``calculations/``:

.. code-block:: text

   metricengine/
     calculations/
       __init__.py     # contains load_all()
       pricing.py
       growth.py
       profitability.py
       ...

3. Do not import all calculations from package ``__init__.py``. Instead, expose a loader:

.. code-block:: python

   # calculations/__init__.py
   def load_all() -> None:
       from . import pricing, growth, profitability  # noqa: F401

4. Use relative imports inside calculation modules:

.. code-block:: python

   from ..registry_collections import Collection
   from ..value import FinancialValue
   from ..units import Money, Ratio, Percent, Dimensionless
   from ..policy import DEFAULT_POLICY
   from ..policy_context import get_policy
   from ..exceptions import CalculationError

2) Registering calculations via ``Collection``
----------------------------------------------

- Create a collection per module:

.. code-block:: python

   pricing = Collection("pricing")

- Register each function with ``@pricing.calc("name", depends_on=(...))``.
- Dependencies are strings; the collection auto-prefixes relative names.

Template:

.. code-block:: python

   pricing = Collection("pricing")

   @pricing.calc("gross_profit", depends_on=("sales", "cost"))
   def gross_profit(sales: FinancialValue[Money],
                    cost:  FinancialValue[Money]) -> FinancialValue[Money]:
       return sales - cost

3) Dependency naming rules (critical)
-------------------------------------

- Relative name (no dot): ``"sales"`` → auto-qualified to ``pricing.sales``.
- Absolute name (has dot or starts with ``":"``): ``"growth.compound_growth_rate"`` or ``":growth.compound_growth_rate"`` → no re-prefixing. Use for cross-package deps.

Examples:

.. code-block:: python

   @sales.calc("total_cost", depends_on=("pricing.unit_cost", "quantity"))
   # "quantity" -> "sales.quantity" (relative)
   # "pricing.unit_cost" stays absolute

4) Function signatures & phantom units
--------------------------------------

- Use phantom types at API boundaries:
  - **Money amounts**: ``FinancialValue[Money]``
  - **Rates/ratios**: ``FinancialValue[Ratio]``
  - **Percent display**: ``FinancialValue[Percent]`` (convert at the end)
  - **Counts/time**: ``FinancialValue[Dimensionless]``

- Prefer returning Ratio for growth/margins; provide a ``..._percent`` sibling that converts.

Examples:

.. code-block:: python

   def gross_margin(gross_profit: FinancialValue[Money],
                    sales:        FinancialValue[Money]) -> FinancialValue[Ratio]:
       return (gross_profit / sales).ratio()

   def gross_margin_percent(gross_margin: FinancialValue[Ratio]) -> FinancialValue[Percent]:
       return gross_margin.as_percentage()

5) Policy resolution & None handling
------------------------------------

- Resolve a concrete policy for results:

.. code-block:: python

   pol = (a.policy or b.policy or get_policy() or DEFAULT_POLICY)

- If any input is None, return ``FinancialValue.none(pol)`` (or the unit-aware variant).
- For invalid domain (e.g., division by zero, non-positive inputs for CAGR):
  - If ``pol.arithmetic_strict``: ``raise CalculationError("...")``
  - Else: return ``FinancialValue.none(pol)``.

6) Precision rules
------------------

- Never do ``Decimal(float)`` directly. Let the engine/inputs provide ``FinancialValue``; operate on ``FinancialValue`` where possible.
- For exponentiation with fractional exponents (CAGR, geometric means), avoid float pow. Use ``Decimal`` context:

.. code-block:: python

   from decimal import getcontext, Decimal

   ctx = getcontext().copy(); ctx.prec = max(28, pol.decimal_places + 10)
   ratio = f / i                     # Decimal > 0
   cagr  = ctx.exp(ctx.ln(ratio) / n) - Decimal(1)

- Prefer existing reducers (``fv_sum``, ``fv_mean``, ``fv_weighted_mean``) for aggregations.

7) Percent vs ratio
-------------------

- Store and compute as ratios (0..1).
- Convert to percent only in presentation or in a convenience calc:

.. code-block:: python

   return ratio_value.as_percentage()

- Let ``Policy.percent_display`` control string rendering, not the underlying math.

8) Example migration (before → after)
-------------------------------------

Before:

.. code-block:: python

   from .registry import calc

   @calc("gross_margin_percentage", depends_on=("gross_profit", "sales"))
   def gross_margin_percentage(gross_profit, sales):
       if sales is None or sales == 0:
           return None
       return (gross_profit / sales) * 100

After:

.. code-block:: python

   from ..registry_collections import Collection
   from ..units import Money, Ratio, Percent, Dimensionless
   from ..value import FinancialValue
   from ..policy_context import get_policy
   from ..policy import DEFAULT_POLICY
   from ..exceptions import CalculationError

   profitability = Collection("profitability")

   @profitability.calc("gross_margin_ratio", depends_on=("gross_profit", "sales"))
   def gross_margin_ratio(gross_profit: FinancialValue[Money],
                          sales:        FinancialValue[Money]) -> FinancialValue[Ratio]:
       pol = gross_profit.policy or sales.policy or get_policy() or DEFAULT_POLICY
       if gross_profit.is_none() or sales.is_none():
           return FinancialValue.none(pol).ratio()
       # engine's FV division handles domain; still guard sales == 0 if you prefer:
       if sales._value == 0:
           return FinancialValue.none(pol).ratio()
       return (gross_profit / sales).ratio()

   @profitability.calc("gross_margin_percent", depends_on=("gross_margin_ratio",))
   def gross_margin_percent(gmr: FinancialValue[Ratio]) -> FinancialValue[Percent]:
       pol = gmr.policy or get_policy() or DEFAULT_POLICY
       if gmr.is_none():
           return FinancialValue.none(pol).as_percentage()
       return gmr.as_percentage()

9) Decorators / business rules
------------------------------

- Keep generic math in ``reductions.py``.
- Put domain guards like ``skip_if_negative_sales`` in ``calculations/rules.py`` (not in generic utilities). Re-export if needed.
- Make guards policy-aware and argument-named:

.. code-block:: python

   def skip_if_negative_sales(arg="sales"):
       return skip_if(arg=arg, policy_flag="negative_sales_is_none",
                      predicate=lambda fv: fv < 0)

10) Cross-package dependencies
------------------------------

- Use absolute names in ``depends_on`` for cross-package links: ``"pricing.unit_cost"``.
- Ensure packages are registered before use:

.. code-block:: python

   from metricengine.calculations import load_all
   load_all()

- (Optional) add a bootstrap that auto-imports known namespaces, or an entry-point loader for plugins.

11) Validation & acceptance checks (add to CI)
----------------------------------------------

- Cycle detection: run a registry cycle check after ``load_all()`` and fail CI on cycles.
- Existence: assert every dependency name resolves to a registered calc.
- Smoke run: call ``Engine().get_all_calculations()`` and ensure expected names appear.
- Type check: run mypy/pyright with stricter settings to enforce phantom types at boundaries.

12) Common pitfalls (avoid these)
---------------------------------

- Returning Percent for intermediate rates; prefer Ratio until the edge.
- Using float pow for CAGR; use Decimal + ln/exp.
- Forgetting policy resolution (``pol = a.policy or b.policy or get_policy() or DEFAULT_POLICY``).
- Mixing units silently; rely on ``FinancialValue`` runtime checks, and keep overloads for common Money/Ratio ops for dev ergonomics.
- Using duplicate module names (``units.py`` in multiple places). Keep a single canonical source.

13) Boilerplate you can reuse
-----------------------------

Collection:

.. code-block:: python

   # registry_collections.py
   from .registry import calc as _calc

   class Collection:
       def __init__(self, namespace: str = ""):
           self.ns = namespace.strip(".")
       def _qualify(self, name: str) -> str:
           if name.startswith(":") or "." in name:
               return name.lstrip(":")
           return f"{self.ns}.{name}" if self.ns else name
       def calc(self, name: str, *, depends_on: tuple[str, ...] = ()):
           return _calc(self._qualify(name),
                        depends_on=tuple(self._qualify(d) for d in depends_on))

Policy-aware result policy:

.. code-block:: python

   pol = (a.policy if isinstance(a, FinancialValue) else None) \
      or (b.policy if isinstance(b, FinancialValue) else None) \
      or get_policy() or DEFAULT_POLICY

-----------------------------------------------------------------------

If you follow this checklist for each module—namespacing, typed signatures, policy/None handling, precision rules—you'll end up with a coherent, strongly-typed, and cross-package-friendly calculation graph.
