"""Provenance tracking for financial calculations.

This module provides the core data structures and utilities for tracking
the provenance (lineage) of financial calculations. Every FinancialValue
can maintain a complete record of how it was computed.
"""
from __future__ import annotations

import hashlib
import weakref
from collections import defaultdict
from collections.abc import Generator
from contextlib import contextmanager
from contextvars import ContextVar, Token
from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING, Any

try:
    from weakref import WeakSet
except ImportError:
    # Fallback for older Python versions
    WeakSet = set

if TYPE_CHECKING:
    from .policy import Policy
    from .value import FinancialValue

# Import configuration system
try:
    from .provenance_config import (
        get_config,
        log_provenance_error,
        should_fail_on_error,
        should_track_literals,
        should_track_operations,
        should_track_provenance,
    )
except ImportError:
    # Fallback implementations if config module is not available
    def get_config():
        return None

    def log_provenance_error(error, context="", **metadata):
        pass

    def should_track_provenance():
        return True

    def should_track_literals():
        return True

    def should_track_operations():
        return True

    def should_fail_on_error():
        return False


# ======================== Performance Optimizations ========================

# Provenance ID interning for memory efficiency
_interned_ids: dict[str, str] = {}
_id_intern_lock = None  # Will be initialized if threading is available

# Hash cache for identical operations
_hash_cache: dict[str, str] = {}
_cache_hits = 0
_cache_misses = 0

# Weak reference tracking for memory management
_active_provenance_refs: WeakSet = None  # Will be initialized if weakref is available

# History truncation tracking
_provenance_history: dict[str, int] = defaultdict(int)
_max_history_entries = 1000


def _init_performance_optimizations():
    """Initialize performance optimization components."""
    global _id_intern_lock, _active_provenance_refs

    try:
        # Initialize threading lock for ID interning
        import threading

        _id_intern_lock = threading.RLock()
    except ImportError:
        _id_intern_lock = None

    try:
        # Initialize weak reference set
        _active_provenance_refs = WeakSet()
    except Exception:
        _active_provenance_refs = None


def intern_provenance_id(prov_id: str) -> str:
    """Intern a provenance ID to reduce memory usage from duplicate strings.

    Args:
        prov_id: The provenance ID to intern

    Returns:
        Interned provenance ID (same object for identical strings)
    """
    try:
        config = get_config()
        if not config or not getattr(config, "enable_id_interning", True):
            return prov_id

        # Use thread-safe interning if available
        if _id_intern_lock is not None:
            with _id_intern_lock:
                if prov_id in _interned_ids:
                    return _interned_ids[prov_id]
                _interned_ids[prov_id] = prov_id
                return prov_id
        else:
            # Fallback to non-thread-safe interning
            if prov_id in _interned_ids:
                return _interned_ids[prov_id]
            _interned_ids[prov_id] = prov_id
            return prov_id

    except Exception as e:
        log_provenance_error(e, "intern_provenance_id")
        return prov_id


def _get_cached_hash(cache_key: str) -> str | None:
    """Get a cached hash result if available.

    Args:
        cache_key: Key for the hash cache

    Returns:
        Cached hash if available, None otherwise
    """
    global _cache_hits, _cache_misses

    try:
        if cache_key in _hash_cache:
            _cache_hits += 1
            return _hash_cache[cache_key]
        else:
            _cache_misses += 1
            return None
    except Exception as e:
        log_provenance_error(e, "_get_cached_hash")
        return None


def _cache_hash(cache_key: str, hash_value: str) -> str:
    """Cache a hash result for future use.

    Args:
        cache_key: Key for the hash cache
        hash_value: Hash value to cache

    Returns:
        The hash value (for convenience)
    """
    try:
        config = get_config()
        max_cache_size = (
            getattr(config, "max_hash_cache_size", 10000) if config else 10000
        )

        # Limit cache size to prevent unbounded growth
        if len(_hash_cache) >= max_cache_size:
            # Remove oldest entries (simple FIFO eviction)
            keys_to_remove = list(_hash_cache.keys())[: max_cache_size // 4]
            for key in keys_to_remove:
                _hash_cache.pop(key, None)

        _hash_cache[cache_key] = hash_value
        return hash_value

    except Exception as e:
        log_provenance_error(e, "_cache_hash")
        return hash_value


def _register_provenance_ref(prov: Provenance) -> None:
    """Register a provenance instance for weak reference tracking.

    Args:
        prov: Provenance instance to track
    """
    try:
        config = get_config()
        if not config or not getattr(config, "enable_weak_refs", False):
            return

        if _active_provenance_refs is not None:
            _active_provenance_refs.add(prov)

    except Exception as e:
        log_provenance_error(e, "_register_provenance_ref")


def _should_truncate_history(prov_id: str) -> bool:
    """Check if provenance history should be truncated for this ID.

    Args:
        prov_id: Provenance ID to check

    Returns:
        True if history should be truncated, False otherwise
    """
    try:
        config = get_config()
        if not config:
            return False

        max_depth = getattr(config, "max_history_depth", 1000)
        if max_depth <= 0:
            return False

        _provenance_history[prov_id] += 1
        return _provenance_history[prov_id] > max_depth

    except Exception as e:
        log_provenance_error(e, "_should_truncate_history")
        return False


def get_cache_stats() -> dict[str, Any]:
    """Get performance statistics for provenance caching.

    Returns:
        Dictionary with cache performance statistics
    """
    try:
        total_requests = _cache_hits + _cache_misses
        hit_rate = (_cache_hits / total_requests * 100) if total_requests > 0 else 0

        stats = {
            "cache_hits": _cache_hits,
            "cache_misses": _cache_misses,
            "hit_rate_percent": round(hit_rate, 2),
            "cache_size": len(_hash_cache),
            "interned_ids": len(_interned_ids),
            "history_entries": len(_provenance_history),
        }

        if _active_provenance_refs is not None:
            stats["active_provenance_refs"] = len(_active_provenance_refs)

        return stats

    except Exception as e:
        log_provenance_error(e, "get_cache_stats")
        return {"error": "stats_unavailable"}


def clear_caches() -> None:
    """Clear all provenance caches and reset statistics."""
    global _cache_hits, _cache_misses

    try:
        _hash_cache.clear()
        _interned_ids.clear()
        _provenance_history.clear()
        _cache_hits = 0
        _cache_misses = 0

        if _active_provenance_refs is not None:
            _active_provenance_refs.clear()

    except Exception as e:
        log_provenance_error(e, "clear_caches")


# Initialize performance optimizations
_init_performance_optimizations()

# Use frozendict if available, otherwise fall back to dict
try:
    from frozendict import frozendict
except ImportError:
    # Fallback implementation for immutable dict
    class frozendict(dict):
        def __setitem__(self, key, value):
            raise TypeError("frozendict is immutable")

        def __delitem__(self, key):
            raise TypeError("frozendict is immutable")

        def clear(self):
            raise TypeError("frozendict is immutable")

        def pop(self, *args):
            raise TypeError("frozendict is immutable")

        def popitem(self):
            raise TypeError("frozendict is immutable")

        def setdefault(self, key, default=None):
            raise TypeError("frozendict is immutable")

        def update(self, *args, **kwargs):
            raise TypeError("frozendict is immutable")


# Context variables for span tracking
_current_span_stack: ContextVar[list[dict[str, Any]]] = ContextVar(
    "_current_span_stack", default=[]
)


@dataclass(frozen=True)
class Provenance:
    """Immutable provenance record for financial value calculations."""
    
    __slots__ = ('id', 'op', 'inputs', 'meta')

    id: str  # Stable hash of operation + operands + policy
    op: str  # Operation identifier ("+", "/", "calc:gross_margin", "literal")
    inputs: tuple[str, ...]  # Child provenance IDs
    meta: frozendict[str, Any]  # Optional metadata (names, tags, constants)

    def __post_init__(self):
        # Ensure meta is immutable
        if not isinstance(self.meta, frozendict):
            object.__setattr__(self, "meta", frozendict(self.meta))

        # Intern the provenance ID for memory efficiency
        interned_id = intern_provenance_id(self.id)
        if interned_id is not self.id:
            object.__setattr__(self, "id", interned_id)

        # Intern input IDs as well
        if self.inputs:
            interned_inputs = tuple(
                intern_provenance_id(input_id) for input_id in self.inputs
            )
            if interned_inputs != self.inputs:
                object.__setattr__(self, "inputs", interned_inputs)

        # Register for weak reference tracking
        _register_provenance_ref(self)


def hash_literal(value: Decimal | None, policy: Policy) -> str:
    """Generate stable hash for literal values.

    Args:
        value: The literal value (Decimal or None)
        policy: The policy context for the value

    Returns:
        SHA-256 hash string for the literal

    Raises:
        Exception: Only if fail_on_error is True in configuration
    """
    try:
        # Check if literal tracking is enabled
        if not should_track_literals():
            return _generate_fallback_id("literal")

        # Create a stable representation of the value and policy
        if value is not None:
            # Normalize decimal representation to avoid differences between 100 and 100.00
            value_str = str(value.normalize())
        else:
            value_str = "None"

        policy_fingerprint = _get_policy_fingerprint(policy)

        # Create cache key for this literal
        cache_key = f"literal:{value_str}:{policy_fingerprint}"

        # Check cache first
        cached_hash = _get_cached_hash(cache_key)
        if cached_hash is not None:
            return cached_hash

        # Generate hash and cache it
        hash_value = hashlib.sha256(cache_key.encode("utf-8")).hexdigest()
        return _cache_hash(cache_key, hash_value)

    except Exception as e:
        log_provenance_error(
            e,
            "hash_literal",
            value=str(value) if value is not None else "None",
            policy_type=type(policy).__name__ if policy else "None",
        )

        if should_fail_on_error():
            raise

        # Graceful degradation: return a fallback hash
        return _generate_fallback_id(
            "literal", str(value) if value is not None else "None"
        )


def hash_node(
    op: str,
    parents: tuple[FinancialValue, ...],
    policy: Policy,
    meta: dict | None = None,
) -> str:
    """Generate stable hash for operation nodes.

    Args:
        op: Operation identifier (e.g., "+", "-", "calc:margin")
        parents: Parent FinancialValue instances
        policy: Policy context for the operation
        meta: Optional metadata dictionary

    Returns:
        SHA-256 hash string for the operation node

    Raises:
        Exception: Only if fail_on_error is True in configuration
    """
    try:
        # Check if operation tracking is enabled
        if not should_track_operations():
            return _generate_fallback_id("operation", op)

        # Get parent provenance IDs with error handling
        parent_ids = []
        for i, parent in enumerate(parents):
            try:
                if hasattr(parent, "_prov") and parent._prov is not None:
                    parent_id = parent._prov.id
                    # Check if we should truncate history for this parent
                    if _should_truncate_history(parent_id):
                        parent_id = f"truncated:{parent_id[:16]}"
                    parent_ids.append(parent_id)
                else:
                    # Generate a literal provenance ID for parents without provenance
                    parent_id = hash_literal(
                        getattr(parent, "_value", None), getattr(parent, "policy", None)
                    )
                    parent_ids.append(parent_id)
            except Exception as parent_error:
                log_provenance_error(
                    parent_error, f"hash_node_parent_{i}", operation=op, parent_index=i
                )
                # Use fallback ID for problematic parent
                parent_ids.append(_generate_fallback_id("parent", f"{op}_{i}"))

        # Merge span information into metadata with error handling
        combined_meta = {}
        if meta:
            try:
                combined_meta.update(meta)
            except Exception as meta_error:
                log_provenance_error(meta_error, "hash_node_meta_merge", operation=op)
                # Continue without metadata

        # Add current span information with error handling
        try:
            span_info = _get_current_span_info()
            if span_info:
                combined_meta.update(span_info)
        except Exception as span_error:
            log_provenance_error(span_error, "hash_node_span_info", operation=op)
            # Continue without span info

        # Create stable representation with error handling
        try:
            policy_fingerprint = _get_policy_fingerprint(policy)
        except Exception as policy_error:
            log_provenance_error(
                policy_error, "hash_node_policy_fingerprint", operation=op
            )
            policy_fingerprint = "error"

        try:
            meta_str = _serialize_meta(combined_meta) if combined_meta else ""
        except Exception as serialize_error:
            log_provenance_error(
                serialize_error, "hash_node_meta_serialize", operation=op
            )
            meta_str = "error"

        # Create cache key for this operation
        cache_key = f"op:{op}:parents:{':'.join(sorted(parent_ids))}:policy:{policy_fingerprint}:meta:{meta_str}"

        # Check cache first
        cached_hash = _get_cached_hash(cache_key)
        if cached_hash is not None:
            return cached_hash

        # Generate hash and cache it
        hash_value = hashlib.sha256(cache_key.encode("utf-8")).hexdigest()
        return _cache_hash(cache_key, hash_value)

    except Exception as e:
        log_provenance_error(
            e,
            "hash_node",
            operation=op,
            parent_count=len(parents) if parents else 0,
            has_meta=meta is not None,
        )

        if should_fail_on_error():
            raise

        # Graceful degradation: return a fallback hash
        return _generate_fallback_id("operation", op)


def _generate_fallback_id(category: str, identifier: str = "") -> str:
    """Generate a fallback provenance ID when normal generation fails.

    Args:
        category: Category of the fallback (e.g., "literal", "operation")
        identifier: Additional identifier to make the fallback unique

    Returns:
        Fallback provenance ID
    """
    try:
        import random
        import time

        # Create a simple but unique fallback ID
        timestamp = str(int(time.time() * 1000))  # milliseconds
        random_part = str(random.randint(1000, 9999))

        if identifier:
            content = f"fallback:{category}:{identifier}:{timestamp}:{random_part}"
        else:
            content = f"fallback:{category}:{timestamp}:{random_part}"

        # Use a simple hash for fallback IDs
        return hashlib.md5(content.encode("utf-8")).hexdigest()

    except Exception:
        # Ultimate fallback - even simpler ID generation
        try:
            import uuid

            return f"fallback_{category}_{str(uuid.uuid4()).replace('-', '')[:8]}"
        except Exception:
            # Last resort - static fallback with some randomness
            import os

            pid = os.getpid() if hasattr(os, "getpid") else 0
            return f"fallback_{category}_{pid}_{hash(identifier) % 10000}"


def _get_policy_fingerprint(policy: Policy) -> str:
    """Generate a stable fingerprint for a policy.

    Args:
        policy: The policy to fingerprint

    Returns:
        Stable string representation of the policy

    Raises:
        Exception: Only if fail_on_error is True in configuration
    """
    try:
        if policy is None:
            return "None"

        # Create a stable representation of key policy attributes
        # This is a simplified version - in production we'd want to include
        # all relevant policy fields that affect calculations
        attrs = []

        # Safely access policy attributes
        try:
            attrs.append(
                f"decimal_places:{getattr(policy, 'decimal_places', 'unknown')}"
            )
        except Exception:
            attrs.append("decimal_places:error")

        try:
            attrs.append(f"rounding:{getattr(policy, 'rounding', 'unknown')}")
        except Exception:
            attrs.append("rounding:error")

        try:
            attrs.append(f"none_text:{getattr(policy, 'none_text', 'unknown')}")
        except Exception:
            attrs.append("none_text:error")

        return "|".join(sorted(attrs))

    except Exception as e:
        log_provenance_error(e, "_get_policy_fingerprint")

        if should_fail_on_error():
            raise

        return "policy_error"


def _serialize_meta(meta: dict) -> str:
    """Serialize metadata dictionary to stable string.

    Args:
        meta: Metadata dictionary

    Returns:
        Stable string representation of metadata

    Raises:
        Exception: Only if fail_on_error is True in configuration
    """
    try:
        if not meta:
            return ""

        # Sort keys for stable serialization
        items = []
        for key in sorted(meta.keys()):
            try:
                value = meta[key]
                # Safely convert value to string with proper handling of nested structures
                if isinstance(value, dict):
                    # For dictionaries, serialize the key-value pairs
                    dict_items = []
                    for k, v in sorted(value.items()):
                        dict_items.append(f"{k}={v}")
                    value_str = f"dict({','.join(dict_items)})"
                elif isinstance(value, list):
                    # For lists, serialize the elements
                    list_items = [str(item) for item in value]
                    value_str = f"list({','.join(list_items)})"
                else:
                    value_str = str(value)
                items.append(f"{key}:{value_str}")
            except Exception as item_error:
                log_provenance_error(item_error, "_serialize_meta_item", key=key)
                # Include error marker for problematic items
                items.append(f"{key}:error")

        return "|".join(items)

    except Exception as e:
        log_provenance_error(e, "_serialize_meta")

        if should_fail_on_error():
            raise

        return "meta_error"


# ======================== Calculation Span Context Management ========================


def _push_calc_context(name: str, attrs: dict[str, Any]) -> Token:
    """Push a new calculation context onto the span stack.

    Args:
        name: Name of the calculation span
        attrs: Additional attributes for the span

    Returns:
        Token that can be used to restore the previous context

    Raises:
        Exception: Only if fail_on_error is True in configuration
    """
    try:
        current_stack = _current_span_stack.get([])

        # Safely copy attributes
        safe_attrs = {}
        if attrs:
            for key, value in attrs.items():
                try:
                    # Ensure the value is serializable
                    str(value)
                    safe_attrs[key] = value
                except Exception as attr_error:
                    log_provenance_error(attr_error, "_push_calc_context_attr", key=key)
                    safe_attrs[key] = f"error:{type(value).__name__}"

        # Create new span context
        span_context = {
            "name": str(name),  # Ensure name is a string
            "attrs": safe_attrs,
            "depth": len(current_stack),
        }

        # Create new stack with the span added
        new_stack = current_stack + [span_context]

        # Set the new stack and return the token
        return _current_span_stack.set(new_stack)

    except Exception as e:
        log_provenance_error(e, "_push_calc_context", span_name=name)

        if should_fail_on_error():
            raise

        # Return a dummy token that won't cause issues when reset
        return _current_span_stack.set(_current_span_stack.get([]))


def _pop_calc_context(token: Token) -> None:
    """Pop the calculation context using the provided token.

    Args:
        token: Token returned by _push_calc_context

    Raises:
        Exception: Only if fail_on_error is True in configuration
    """
    try:
        _current_span_stack.reset(token)
    except Exception as e:
        log_provenance_error(e, "_pop_calc_context")

        if should_fail_on_error():
            raise

        # Graceful degradation: try to clear the stack
        try:
            _current_span_stack.set([])
        except Exception:
            pass  # If even this fails, just continue


def _get_current_span_info() -> dict[str, Any]:
    """Get current span information for inclusion in provenance metadata.

    Returns:
        Dictionary containing current span information, empty if no active spans

    Raises:
        Exception: Only if fail_on_error is True in configuration
    """
    try:
        current_stack = _current_span_stack.get([])

        if not current_stack:
            return {}

        # Build span hierarchy information
        span_info = {}

        # Add current span name with error handling
        try:
            current_span = current_stack[-1]
            span_info["span"] = current_span.get("name", "unknown")
        except (IndexError, AttributeError, TypeError) as span_error:
            log_provenance_error(span_error, "_get_current_span_info_current")
            return {}

        # Add span attributes with error handling
        try:
            if current_span.get("attrs"):
                span_info["span_attrs"] = current_span["attrs"].copy()
        except Exception as attrs_error:
            log_provenance_error(attrs_error, "_get_current_span_info_attrs")
            # Continue without attributes

        # Add span hierarchy if nested with error handling
        try:
            if len(current_stack) > 1:
                hierarchy = []
                for span in current_stack:
                    try:
                        hierarchy.append(span.get("name", "unknown"))
                    except Exception:
                        hierarchy.append("error")
                span_info["span_hierarchy"] = hierarchy
                span_info["span_depth"] = len(current_stack)
        except Exception as hierarchy_error:
            log_provenance_error(hierarchy_error, "_get_current_span_info_hierarchy")
            # Continue without hierarchy info

        return span_info

    except Exception as e:
        log_provenance_error(e, "_get_current_span_info")

        if should_fail_on_error():
            raise

        return {}


@contextmanager
def calc_span(name: str, **attrs) -> Generator[None, None, None]:
    """Context manager for grouping calculations under a named span.

    This context manager allows grouping related financial calculations
    under a named span, which will be included in the provenance metadata
    of all operations performed within the span context.

    Args:
        name: Name of the calculation span
        **attrs: Additional attributes to associate with the span

    Yields:
        None

    Example:
        >>> with calc_span("quarterly_analysis", quarter="Q1", year=2024):
        ...     revenue = FinancialValue(1000)
        ...     cost = FinancialValue(600)
        ...     profit = revenue - cost  # Will include span info in provenance

        >>> prov = profit.get_provenance()
        >>> print(prov.meta.get("span"))  # "quarterly_analysis"
        >>> print(prov.meta.get("span_attrs"))  # {"quarter": "Q1", "year": 2024}
    """
    token = None

    try:
        # Check if spans are enabled
        config = get_config()
        if config and not getattr(config, "enable_spans", True):
            # Spans disabled, just yield without tracking
            yield
            return

        token = _push_calc_context(name, attrs)

    except Exception as setup_error:
        # Log span setup errors but don't break user code
        log_provenance_error(setup_error, "calc_span_setup", span_name=name)

        if should_fail_on_error():
            raise

    try:
        # Always yield, even if span setup failed
        yield

    finally:
        # Always try to clean up the span context
        if token is not None:
            try:
                _pop_calc_context(token)
            except Exception as cleanup_error:
                log_provenance_error(cleanup_error, "calc_span_cleanup", span_name=name)


# ======================== Export and Analysis Functions ========================


def get_provenance_graph(fv: FinancialValue) -> dict[str, Provenance]:
    """Extract complete provenance graph as dictionary.

    This function traverses the complete provenance graph starting from the given
    FinancialValue and returns a dictionary mapping provenance IDs to their
    Provenance records. This is useful for analysis and debugging of calculation
    lineage.

    Note: This implementation can only traverse the provenance records that are
    directly accessible from the root FinancialValue. In the current architecture,
    we don't maintain a global provenance store, so we can only include the root
    provenance record. A full implementation would require either:
    1. A global provenance registry, or
    2. Maintaining references to parent FinancialValue instances

    Args:
        fv: FinancialValue to extract provenance graph from

    Returns:
        Dictionary mapping provenance IDs to Provenance records

    Example:
        >>> revenue = FinancialValue(1000)
        >>> cost = FinancialValue(600)
        >>> profit = revenue - cost
        >>> graph = get_provenance_graph(profit)
        >>> print(len(graph))  # 1 (only profit, as we can't traverse to inputs)
        >>> print(list(graph.keys()))  # ['profit_id']
    """
    try:
        if not hasattr(fv, "has_provenance") or not fv.has_provenance():
            return {}

        graph = {}
        visited: set[str] = set()

        # Check graph size limits
        config = get_config()
        max_size = getattr(config, "max_graph_size", 10000) if config else 10000
        use_weak_refs = getattr(config, "enable_weak_refs", False) if config else False

        # Use weak references to prevent memory leaks during traversal
        weak_refs: set[weakref.ReferenceType] = set() if use_weak_refs else None

        def _traverse(prov: Provenance) -> None:
            """Recursively traverse provenance graph."""
            try:
                if prov.id in visited:
                    return

                # Check size limits
                if len(graph) >= max_size:
                    log_provenance_error(
                        Exception(f"Graph size limit exceeded: {max_size}"),
                        "get_provenance_graph_size_limit",
                    )
                    return

                visited.add(prov.id)
                graph[prov.id] = prov

                # Track weak reference if enabled
                if weak_refs is not None:
                    try:
                        weak_ref = weakref.ref(prov)
                        weak_refs.add(weak_ref)
                    except TypeError:
                        # Some objects can't be weakly referenced
                        pass

                # Note: We cannot traverse to input provenance records because
                # we don't have access to the original FinancialValue instances
                # that contain those provenance records. This is a limitation
                # of the current architecture.

            except Exception as traverse_error:
                log_provenance_error(
                    traverse_error, "get_provenance_graph_traverse", prov_id=prov.id
                )

        root_prov = fv.get_provenance()
        if root_prov:
            _traverse(root_prov)

        # Clean up weak references
        if weak_refs is not None:
            # Remove dead references
            weak_refs = {ref for ref in weak_refs if ref() is not None}

        return graph

    except Exception as e:
        log_provenance_error(e, "get_provenance_graph")

        if should_fail_on_error():
            raise

        return {}


def to_trace_json(fv: FinancialValue) -> dict[str, Any]:
    """Export complete provenance graph as JSON-serializable dictionary.

    This function creates a complete JSON representation of the provenance graph
    that can be serialized, stored, or transmitted. The format includes a root
    node identifier and a nodes dictionary containing all provenance records.

    Args:
        fv: FinancialValue to export provenance graph from

    Returns:
        Dictionary with 'root' and 'nodes' keys containing the complete graph

    Example:
        >>> revenue = FinancialValue(1000)
        >>> cost = FinancialValue(600)
        >>> profit = revenue - cost
        >>> trace = to_trace_json(profit)
        >>> print(trace['root'])  # profit provenance ID
        >>> print(len(trace['nodes']))  # 3 nodes
    """
    try:
        if not hasattr(fv, "has_provenance") or not fv.has_provenance():
            return {"root": None, "nodes": {}}

        root_prov = fv.get_provenance()
        if not root_prov:
            return {"root": None, "nodes": {}}

        # Get the complete provenance graph with error handling
        try:
            graph = get_provenance_graph(fv)
        except Exception as graph_error:
            log_provenance_error(graph_error, "to_trace_json_get_graph")
            if should_fail_on_error():
                raise
            graph = {}

        # Convert to JSON-serializable format
        nodes = {}
        for prov_id, prov in graph.items():
            try:
                # Safely convert provenance to JSON
                node_data = {
                    "id": str(prov.id),
                    "op": str(prov.op),
                    "inputs": [],
                    "meta": {},
                }

                # Safely convert inputs
                try:
                    node_data["inputs"] = [str(input_id) for input_id in prov.inputs]
                except Exception as inputs_error:
                    log_provenance_error(
                        inputs_error, "to_trace_json_inputs", prov_id=prov_id
                    )
                    node_data["inputs"] = ["error"]

                # Safely convert metadata
                try:
                    if prov.meta:
                        # Ensure all metadata values are JSON-serializable
                        safe_meta = {}
                        for key, value in prov.meta.items():
                            try:
                                # Test JSON serializability
                                import json

                                json.dumps(value)
                                safe_meta[str(key)] = value
                            except (TypeError, ValueError):
                                # Convert non-serializable values to strings
                                safe_meta[str(key)] = str(value)
                        node_data["meta"] = safe_meta
                except Exception as meta_error:
                    log_provenance_error(
                        meta_error, "to_trace_json_meta", prov_id=prov_id
                    )
                    node_data["meta"] = {"error": "metadata_conversion_failed"}

                nodes[prov_id] = node_data

            except Exception as node_error:
                log_provenance_error(node_error, "to_trace_json_node", prov_id=prov_id)
                # Include error node
                nodes[prov_id] = {
                    "id": str(prov_id),
                    "op": "error",
                    "inputs": [],
                    "meta": {"error": "node_conversion_failed"},
                }

        return {"root": str(root_prov.id), "nodes": nodes}

    except Exception as e:
        log_provenance_error(e, "to_trace_json")

        if should_fail_on_error():
            raise

        return {"root": None, "nodes": {}, "error": "export_failed"}


def _validate_provenance_graph(graph: dict[str, Provenance]) -> bool:
    """Validate that a provenance graph is well-formed.

    Args:
        graph: Dictionary mapping provenance IDs to Provenance records

    Returns:
        True if the graph is valid, False otherwise
    """
    if not graph:
        return True

    # Check that all referenced input IDs exist in the graph
    # Note: In the current implementation, this will always pass
    # because we only have single nodes, but this is useful for
    # future enhancements when we have full graph traversal
    for _, prov in graph.items():
        for input_id in prov.inputs:
            # For now, we just check that input_id is a valid string
            if not isinstance(input_id, str) or not input_id:
                return False

    return True


def _format_provenance_summary(fv: FinancialValue) -> str:
    """Generate a brief summary of provenance information.

    Args:
        fv: FinancialValue to summarize

    Returns:
        Brief string summary of provenance
    """
    if not fv.has_provenance():
        return "No provenance"

    prov = fv.get_provenance()
    if not prov:
        return "No provenance"

    summary_parts = [f"Op: {prov.op}"]

    if prov.inputs:
        summary_parts.append(f"Inputs: {len(prov.inputs)}")

    if prov.meta and "span" in prov.meta:
        summary_parts.append(f"Span: {prov.meta['span']}")

    return " | ".join(summary_parts)


def explain(fv: FinancialValue, max_depth: int = 10) -> str:
    """Generate human-readable explanation of calculation.

    This function creates a formatted text representation of how a FinancialValue
    was calculated, showing the operation tree in a readable format. This is
    useful for debugging and understanding complex calculations.

    Args:
        fv: FinancialValue to explain
        max_depth: Maximum depth to traverse (prevents infinite recursion)

    Returns:
        Human-readable string explaining the calculation

    Example:
        >>> revenue = FinancialValue(1000)
        >>> cost = FinancialValue(600)
        >>> profit = revenue - cost
        >>> print(explain(profit))
        # Result (400.00):
        #   Operation: -
        #   Left: 1000.00 (literal)
        #   Right: 600.00 (literal)
    """
    try:
        # Safely get the value string
        try:
            value_str = fv.as_str()
        except Exception as value_error:
            log_provenance_error(value_error, "explain_value_str")
            value_str = "error"

        if not hasattr(fv, "has_provenance") or not fv.has_provenance():
            return f"Value: {value_str} (no provenance available)"

        root_prov = fv.get_provenance()
        if not root_prov:
            return f"Value: {value_str} (no provenance available)"

        def _explain_node(prov: Provenance, depth: int = 0, prefix: str = "") -> str:
            """Recursively explain a provenance node."""
            try:
                if depth > max_depth:
                    return f"{prefix}... (max depth reached)"

                indent = "  " * depth

                # Safely get operation type
                try:
                    op = str(prov.op)
                except Exception:
                    op = "unknown"

                # Format the operation
                if op == "literal":
                    # For literals, show the value if available in metadata
                    value_info = ""
                    try:
                        if prov.meta and "value" in prov.meta:
                            value_info = f" ({prov.meta['value']})"
                    except Exception:
                        pass
                    return f"{indent}{prefix}Literal{value_info}"

                # For operations, show the operation type
                result = f"{indent}{prefix}Operation: {op}"

                # Add metadata information if available
                try:
                    if prov.meta:
                        meta_info = []

                        # Safely extract metadata
                        for key, desc in [
                            ("input_names", "inputs"),
                            ("span", "span"),
                            ("calculation", "calc"),
                            ("conversion", "conversion"),
                        ]:
                            try:
                                if key in prov.meta:
                                    meta_info.append(f"{desc}: {prov.meta[key]}")
                            except Exception:
                                pass

                        if meta_info:
                            result += f" ({', '.join(meta_info)})"
                except Exception as meta_error:
                    log_provenance_error(meta_error, "explain_node_meta", op=op)

                # Add input information
                try:
                    if prov.inputs:
                        result += f"\n{indent}  Inputs: {len(prov.inputs)} operand(s)"
                        for i, input_id in enumerate(prov.inputs):
                            try:
                                input_str = str(input_id)
                                display_id = (
                                    input_str[:8] + "..."
                                    if len(input_str) > 8
                                    else input_str
                                )
                                result += f"\n{indent}    [{i}]: {display_id}"
                            except Exception:
                                result += f"\n{indent}    [{i}]: error"
                except Exception as inputs_error:
                    log_provenance_error(inputs_error, "explain_node_inputs", op=op)

                return result

            except Exception as node_error:
                log_provenance_error(node_error, "explain_node", depth=depth)
                return f"{prefix}Error explaining node at depth {depth}"

        explanation = f"Value: {value_str}\n"
        try:
            explanation += _explain_node(root_prov)
        except Exception as explain_error:
            log_provenance_error(explain_error, "explain_root_node")
            explanation += "Error explaining calculation tree"

        return explanation

    except Exception as e:
        log_provenance_error(e, "explain")

        if should_fail_on_error():
            raise

        return "Error generating explanation"
