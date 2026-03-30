"""Tests for registry collection bookkeeping."""

from metricengine.registry import Registry
from metricengine.registry_collections import Collection


def test_collection_tracks_registered_functions_without_duplicates():
    """Collection bookkeeping should preserve order and deduplicate entries."""
    collection = Collection("test", registry=Registry())

    @collection.calc("alpha")
    def alpha():
        return 1

    assert collection.registered_functions() == (alpha,)
    assert alpha in collection._registered_function_set
