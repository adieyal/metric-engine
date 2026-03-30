"""Regression tests for provenance config fixture isolation."""

from metricengine.provenance_config import ProvenanceConfig, _context_config, get_config


def test_context_override_can_leak_within_test():
    """Set a context-local override without cleaning it up."""
    _context_config.set(ProvenanceConfig(enabled=False))

    assert get_config().enabled is False


def test_fixture_clears_context_override_between_tests():
    """The autouse fixture should clear leaked context-local overrides."""
    assert get_config().enabled is True
