"""Tests for typed API calculation loading behavior."""

import importlib

import pytest

from metricengine.exceptions import CalculationError


@pytest.fixture(autouse=True)
def manage_registry_and_autoload():
    """Save and restore registry state and autoload configuration."""
    from metricengine import set_default_calculations_autoload
    from metricengine.registry import _dependencies, _registry, clear_registry

    original_registry = _registry.copy()
    original_dependencies = _dependencies.copy()

    clear_registry()
    set_default_calculations_autoload(True)

    yield

    clear_registry()
    set_default_calculations_autoload(True)
    _registry.update(original_registry)
    _dependencies.update(original_dependencies)


def test_typed_api_respects_disabled_default_calculation_autoload():
    """Typed API should not import built-in calculations when autoload is disabled."""
    from metricengine import set_default_calculations_autoload
    from metricengine.registry import list_calculations

    set_default_calculations_autoload(False)

    typed_api = importlib.import_module("metricengine.typed_api")
    importlib.reload(typed_api)

    assert list_calculations() == {}
    assert typed_api.calc_names() == []

    with pytest.raises(CalculationError, match="gross_margin"):
        typed_api.get_calc("gross_margin")
