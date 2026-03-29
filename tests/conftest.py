"""Pytest configuration and fixtures for all tests.

This module provides global test fixtures and configuration to ensure test isolation
and consistent test behavior across the entire test suite.
"""

import gc

import pytest

from metricengine.provenance_config import (
    ProvenanceConfig,
    _context_config,
    get_config,
    set_global_config,
)


@pytest.fixture(autouse=True)
def reset_provenance_config():
    """Reset provenance configuration before each test to ensure isolation.

    This fixture is automatically used for all tests to prevent test pollution
    from global provenance configuration changes.
    """
    # Clear any leaked context-local override before reading or resetting config.
    _context_config.set(None)

    # Save the original configuration
    original_config = get_config()

    # Reset to default configuration before each test
    default_config = ProvenanceConfig()
    set_global_config(default_config)

    yield

    # Clear any leaked context-local override before restoring global config.
    _context_config.set(None)

    # Restore the original configuration after each test
    set_global_config(original_config)


@pytest.fixture(autouse=True)
def reset_caches():
    """Clear any caches before and after each test to ensure isolation.

    This ensures that cached values from one test don't affect another.
    """
    try:
        from metricengine.provenance import clear_caches

        clear_caches()
    except (ImportError, AttributeError):
        # If clear_caches doesn't exist, skip silently
        pass

    yield

    # Clear caches after test as well
    try:
        from metricengine.provenance import clear_caches

        clear_caches()
    except (ImportError, AttributeError):
        pass

    # Force garbage collection to clean up any weakrefs
    gc.collect()


# Mark slow tests
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "performance: marks tests as performance tests")
