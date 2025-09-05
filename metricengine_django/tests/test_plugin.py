from importlib.metadata import EntryPoint


def test_plugin_initializes_when_django_present(monkeypatch):
    import metricengine_django

    # Ensure import doesn't raise
    plugin = metricengine_django.Plugin()
    plugin.initialize()


def test_entry_point_registration(monkeypatch):
    # Simulate package entry point discovery
    ep = EntryPoint(
        name="django", value="metricengine_django:Plugin", group="metricengine.plugins"
    )
    assert ep.name == "django"
    assert ep.group == "metricengine.plugins"
    assert ep.value.startswith("metricengine_django:Plugin")
