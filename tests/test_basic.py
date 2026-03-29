from metricengine import (
    calc,
    format_currency,
    format_percent,
    list_calculations,
    load_plugins,
)
from metricengine.registry import Registry, clear_registry, default_registry


def test_register_and_calculate():
    @calc("add")
    def add(a: int, b: int) -> int:
        return a + b

    # Access registered function via internal API for now
    from metricengine.registry import get

    assert get("add")(a=2, b=3) == 5
    assert "add" in list_calculations()


def test_format_currency_without_babel():
    # Should not fail when Babel is not installed
    assert format_currency(1234.56, "USD").endswith("USD")


def test_format_percent_without_babel():
    assert format_percent(0.1234).endswith("%")


def test_load_plugins_tolerates_missing():
    processed = load_plugins()
    assert isinstance(processed, int)


def test_load_plugins_registers_calculations_into_explicit_registry(monkeypatch):
    class FakeEntryPoint:
        def load(self):
            class FakeCollection:
                def register_all(self, register):
                    @register("plugin_calc")
                    def plugin_calc():
                        return 7

            return FakeCollection

    def fake_load_entry_points(group: str):
        if group == "metricengine.calculations":
            return [FakeEntryPoint()]
        return []

    import metricengine.integrations as integrations

    clear_registry()
    registry = Registry()
    monkeypatch.setattr(integrations, "_load_entry_points", fake_load_entry_points)

    processed = integrations.load_plugins(registry=registry)

    assert processed == 1
    assert registry.is_registered("plugin_calc") is True
    assert "plugin_calc" not in list_calculations()


def test_global_calc_api_uses_default_registry_only():
    from metricengine import Engine

    clear_registry()

    @calc("legacy_only")
    def legacy_only():
        return 1

    engine = Engine(registry=Registry())

    assert default_registry.is_registered("legacy_only") is True
    assert engine.registry.is_registered("legacy_only") is False
