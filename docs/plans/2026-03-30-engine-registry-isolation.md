---
last_updated: 2026-03-30
---

# Engine Registry Isolation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Refactor Metric Engine so each `Engine` owns an isolated calculation registry by default, while still allowing explicitly shared registries when callers want them.

**Architecture:** Replace the module-level calculation registry with a real `Registry` object and inject it into `Engine` as `registry: Registry | None = None`. When `registry` is `None`, the engine creates a fresh private registry and loads built-in calculations into that registry instance instead of relying on import-time global side effects. Keep a compatibility-oriented module-level default registry API only where needed so existing decorator-based usage can continue to work during migration.

**Tech Stack:** Python 3.11+, pytest, existing `metricengine` registry/engine/loading infrastructure.

---

### Task 1: Introduce a first-class `Registry` type

**Files:**
- Modify: `src/metricengine/registry.py`
- Test: `tests/unit/test_registry.py`

**Step 1: Write the failing tests**

Add tests covering:

```python
def test_registry_instances_do_not_share_state():
    registry_a = Registry()
    registry_b = Registry()

    @registry_a.calc("only_a")
    def only_a():
        return 1

    assert registry_a.is_registered("only_a") is True
    assert registry_b.is_registered("only_a") is False


def test_default_module_registry_still_works():
    clear_registry()

    @calc("legacy_calc")
    def legacy_calc():
        return 42

    assert get("legacy_calc") is legacy_calc
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_registry.py -q`
Expected: FAIL because `Registry` does not exist and tests assume instance methods.

**Step 3: Write minimal implementation**

Implement a `Registry` class in `src/metricengine/registry.py` that owns:

```python
self._registry: dict[str, Callable[..., Any]]
self._dependencies: dict[str, set[str]]
self._lock: RLock
```

Give it methods equivalent to today’s module-level API:

```python
calc()
get()
deps()
list_calculations()
clear()
is_registered()
unregister()
dependency_graph()
detect_cycles()
get_all()
```

Preserve function metadata assignment:

```python
fn._calc_name = name
fn._calc_depends_on = depends_on
```

Retain a module-level `default_registry = Registry()` and turn current top-level helpers into wrappers:

```python
def calc(...):
    return default_registry.calc(...)
```

Keep `clear_registry()` as a wrapper around `default_registry.clear()` for compatibility.

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_registry.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add src/metricengine/registry.py tests/unit/test_registry.py
git commit -m "refactor: introduce instance-based calculation registry"
```

### Task 2: Inject registry into `Engine`

**Files:**
- Modify: `src/metricengine/engine.py`
- Modify: `src/metricengine/engine.pyi`
- Test: `tests/unit/test_engine.py`

**Step 1: Write the failing tests**

Add tests covering default isolation and optional sharing:

```python
def test_engine_creates_private_registry_when_none_provided():
    engine_a = Engine()
    engine_b = Engine()

    @engine_a.registry.calc("engine_a_only")
    def engine_a_only():
        return 10

    assert engine_a.registry.is_registered("engine_a_only") is True
    assert engine_b.registry.is_registered("engine_a_only") is False


def test_engines_can_share_registry_when_explicitly_provided():
    shared = Registry()
    engine_a = Engine(registry=shared)
    engine_b = Engine(registry=shared)

    @shared.calc("shared_calc")
    def shared_calc():
        return 10

    assert engine_a.calculate("shared_calc").as_decimal() == Decimal("10")
    assert engine_b.calculate("shared_calc").as_decimal() == Decimal("10")
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_engine.py -q`
Expected: FAIL because `Engine` does not accept `registry` and has no `registry` attribute.

**Step 3: Write minimal implementation**

Update `Engine.__init__` to:

```python
def __init__(
    self,
    default_policy: Policy | None = None,
    registry: Registry | None = None,
):
    self.default_policy = default_policy or DEFAULT_POLICY
    self.registry = registry or Registry()
```

Replace all direct imports/usages of:

```python
get(...)
deps(...)
is_registered(...)
from .registry import _dependencies, _registry
```

with instance methods on `self.registry`, including `get_all_calculations()`.

Keep behavior unchanged apart from registry ownership.

Update the stub in `src/metricengine/engine.pyi` to include the new constructor parameter and `registry` attribute if the stub exposes attributes.

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_engine.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add src/metricengine/engine.py src/metricengine/engine.pyi tests/unit/test_engine.py
git commit -m "refactor: inject registry into engine"
```

### Task 3: Make built-in calculation loading target a specific registry

**Files:**
- Modify: `src/metricengine/calculations/__init__.py`
- Modify: `src/metricengine/registry_collections.py`
- Modify: `src/metricengine/engine.py`
- Test: `tests/unit/test_engine.py`
- Test: `tests/unit/test_typed_api_loading.py`

**Step 1: Write the failing tests**

Add tests covering:

```python
def test_engine_autoload_populates_only_its_own_registry():
    engine_a = Engine()
    engine_b = Engine(registry=Registry())

    assert engine_a.registry.list_calculations()
    assert engine_b.registry.list_calculations()
    assert engine_a.registry is not engine_b.registry


def test_loading_builtins_does_not_require_global_registry_mutation():
    registry = Registry()
    engine = Engine(registry=registry)

    assert registry.is_registered("gross_profit")
    assert get("gross_profit") != registry.get("gross_profit")
```

Adjust the exact assertions to fit final API behavior, but ensure engine loading no longer depends on module-global mutation.

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_engine.py tests/unit/test_typed_api_loading.py -q`
Expected: FAIL because built-ins still register via import side effects into the global registry.

**Step 3: Write minimal implementation**

Refactor registration flow so built-ins can register into a passed registry:

1. Update `Collection` in `src/metricengine/registry_collections.py` to accept a registry:

```python
class Collection:
    def __init__(self, namespace: str = "", registry: Registry | None = None):
        self.registry = registry or default_registry
```

2. Add a function in `src/metricengine/calculations/__init__.py` like:

```python
def register_all(registry: Registry) -> None:
    ...
```

3. Replace import-time side effects with explicit registration entry points in each calculation module. Practical options:
   - Preferred: each module defines `register_into(registry: Registry) -> None`
   - Acceptable transitional option: each module exposes a factory that builds `Collection(..., registry=registry)` and decorates inner functions at call time

4. Change `Engine.__init__` autoload path to call the new registry-targeted registration function for `self.registry`.

Avoid any approach that imports modules once and “sticks” calculations into a process-global registry forever.

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_engine.py tests/unit/test_typed_api_loading.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add src/metricengine/calculations/__init__.py src/metricengine/registry_collections.py src/metricengine/engine.py tests/unit/test_engine.py tests/unit/test_typed_api_loading.py
git commit -m "refactor: load built-in calculations into engine-owned registries"
```

### Task 4: Update plugin and integration registration to be instance-aware

**Files:**
- Modify: `src/metricengine/integrations.py`
- Modify: `src/metricengine/engine.py`
- Test: `tests/unit/test_engine.py`
- Test: `metricengine_django/tests/test_plugin.py`

**Step 1: Write the failing tests**

Add tests for integration loading with explicit registries:

```python
def test_plugin_registration_targets_passed_registry():
    registry = Registry()
    load_plugins(context={"registry": registry})
    # Assert plugin-registered calculations land in registry
```

If current plugin tests are thin, add a small fake plugin/collection fixture rather than relying on real external entry points.

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_engine.py metricengine_django/tests/test_plugin.py -q`
Expected: FAIL because integrations still import and use module-level `calc`.

**Step 3: Write minimal implementation**

Refactor `load_plugins()` so calculation entry points can register against an explicit registry:

```python
def load_plugins(
    context: Optional[dict] = None,
    registry: Registry | None = None,
) -> int:
```

For `metricengine.calculations` entry points, pass a registration callback bound to the provided registry:

```python
target_registry = registry or default_registry
register_all(register=target_registry.calc)
```

If plugin objects support `initialize(context=...)`, make sure `context` includes the target registry so plugins can avoid global mutation.

If `Engine` is responsible for plugin loading, ensure it uses `self.registry`.

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_engine.py metricengine_django/tests/test_plugin.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add src/metricengine/integrations.py src/metricengine/engine.py tests/unit/test_engine.py metricengine_django/tests/test_plugin.py
git commit -m "refactor: make plugin registration registry-aware"
```

### Task 5: Decide and implement compatibility boundaries for global helpers

**Files:**
- Modify: `src/metricengine/__init__.py`
- Modify: `src/metricengine/_typed_forwarders.py`
- Modify: `src/metricengine/typed_api.py`
- Modify: `README.md`
- Modify: `docs/concepts/engine.md`
- Modify: `docs/reference/registry.rst`
- Test: `tests/unit/test_basic.py`
- Test: `tests/unit/test_typed_api_loading.py`

**Step 1: Write the failing tests**

Add tests locking down intended compatibility behavior:

```python
def test_global_calc_api_uses_default_registry_only():
    clear_registry()

    @calc("legacy_only")
    def legacy_only():
        return 1

    engine = Engine()

    assert get("legacy_only") is legacy_only
    assert engine.registry.is_registered("legacy_only") is False
```

And for typed forwarders, choose one of these directions explicitly:

1. Keep them global-only and document that clearly.
2. Rebuild them as registry-bound helpers obtained from an engine/registry.

Do not leave this ambiguous.

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_basic.py tests/unit/test_typed_api_loading.py -q`
Expected: FAIL until compatibility rules are made explicit in code and docs.

**Step 3: Write minimal implementation**

Recommended compatibility policy:

1. Keep module-level `calc/get/...` backed by `default_registry`.
2. Keep `_typed_forwarders.py` global-only for now.
3. Document clearly that:
   - `Engine()` creates an isolated registry by default
   - top-level registry helpers operate on `default_registry`
   - callers wanting the same calculations in an engine must pass `registry=default_registry` or register into that engine’s registry explicitly

Export `Registry` and `default_registry` from `metricengine.__init__`.

Update docs and examples to show the new preferred pattern:

```python
engine = Engine()

@engine.registry.calc("monthly_revenue", depends_on=("annual_revenue",))
def monthly_revenue(annual_revenue):
    return annual_revenue / 12
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_basic.py tests/unit/test_typed_api_loading.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add src/metricengine/__init__.py src/metricengine/_typed_forwarders.py src/metricengine/typed_api.py README.md docs/concepts/engine.md docs/reference/registry.rst tests/test_basic.py tests/unit/test_typed_api_loading.py
git commit -m "docs: clarify isolated engine registries and global compatibility API"
```

### Task 6: Add regression coverage for isolation semantics

**Files:**
- Modify: `tests/unit/test_engine.py`
- Modify: `tests/unit/test_registry.py`
- Modify: `tests/unit/test_calculations.py`

**Step 1: Write the failing tests**

Add regression tests for:

```python
def test_unregistering_from_one_engine_registry_does_not_affect_another():
    ...


def test_shared_registry_mutation_is_visible_to_all_engines_using_it():
    ...


def test_dependency_validation_uses_engine_registry_only():
    ...
```

Also add one test ensuring built-in registration can happen twice into two separate registries without duplicate-registration failures.

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_engine.py tests/unit/test_registry.py tests/unit/test_calculations.py -q`
Expected: FAIL until duplicate-registration and isolation edge cases are handled.

**Step 3: Write minimal implementation**

Fix whichever edge cases appear:
- duplicate built-in registration into separate registries
- accidental fallback to `default_registry`
- dependency traversal reading global state
- shared helper code still closing over the wrong registry

Prefer small targeted fixes over widening the API surface.

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_engine.py tests/unit/test_registry.py tests/unit/test_calculations.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/unit/test_engine.py tests/unit/test_registry.py tests/unit/test_calculations.py
git commit -m "test: add registry isolation regression coverage"
```

### Task 7: Run full verification

**Files:**
- Modify: none
- Test: `tests/unit/test_engine.py`
- Test: `tests/unit/test_registry.py`
- Test: `tests/unit/test_typed_api_loading.py`
- Test: `tests/unit/test_calculations.py`
- Test: `tests/test_basic.py`
- Test: `metricengine_django/tests/test_plugin.py`

**Step 1: Run targeted verification**

Run:

```bash
pytest tests/unit/test_registry.py -q
pytest tests/unit/test_engine.py -q
pytest tests/unit/test_typed_api_loading.py -q
pytest tests/unit/test_calculations.py -q
pytest tests/test_basic.py -q
pytest metricengine_django/tests/test_plugin.py -q
```

Expected: PASS

**Step 2: Run broader suite**

Run:

```bash
pytest -q
```

Expected: PASS

**Step 3: Sanity-check package API manually**

Run:

```bash
python - <<'PY'
from metricengine import Engine, Registry, calc, get, default_registry

engine = Engine()

@engine.registry.calc("local_metric")
def local_metric():
    return 1

@calc("global_metric")
def global_metric():
    return 2

print(engine.calculate("local_metric").as_decimal())
print(get("global_metric")())
print(engine.registry.is_registered("global_metric"))
print(default_registry.is_registered("global_metric"))
PY
```

Expected:
- `local_metric` resolves in the engine
- `global_metric` resolves from the module-level registry
- the engine’s private registry does not report `global_metric`
- `default_registry` does report `global_metric`

**Step 4: Commit**

```bash
git add .
git commit -m "chore: verify isolated engine registries end to end"
```

## Notes For Implementation

- The riskiest part of this refactor is built-in calculation loading, because current modules register on import and assume one process-wide registry.
- Prefer explicit `register_into(registry)` style APIs over import-time side effects.
- Keep compatibility wrappers thin and obvious. Do not let `Engine` silently read from `default_registry`.
- Be careful with tests that currently snapshot `_registry` and `_dependencies`; they should migrate to public `Registry` instances where possible.
- Update any generated or stubbed typing surfaces only after runtime behavior is correct.
