from metricengine import (
    calc,
    format_currency,
    format_percent,
    list_calculations,
    load_plugins,
)


def test_register_and_calculate():
    results = {}

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
