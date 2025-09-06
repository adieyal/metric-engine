"""Configuration system for provenance tracking.

This module provides global configuration options for controlling provenance
tracking behavior, including performance optimizations and error handling.
"""
from __future__ import annotations

import logging
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any

# Logger for provenance-related issues
_logger = logging.getLogger(__name__)


@dataclass
class ProvenanceConfig:
    """Configuration for provenance tracking behavior."""

    # Core feature toggles
    enabled: bool = True
    track_literals: bool = True
    track_operations: bool = True
    track_calculations: bool = True

    # Error handling
    fail_on_error: bool = (
        False  # If True, raise exceptions; if False, degrade gracefully
    )
    log_errors: bool = True  # Whether to log provenance errors
    log_level: int = logging.WARNING  # Log level for provenance errors

    # Performance controls
    max_history_depth: int = 1000
    enable_spans: bool = True
    enable_id_interning: bool = True  # Intern provenance IDs to save memory
    max_hash_cache_size: int = 10000  # Maximum entries in hash cache

    # Memory management
    enable_weak_refs: bool = False  # Use weak references in graph traversal
    max_graph_size: int = 10000  # Maximum nodes in a provenance graph
    enable_history_truncation: bool = True  # Enable provenance history truncation

    # Debugging
    debug_mode: bool = False  # Enable additional debug information
    include_stack_traces: bool = False  # Include stack traces in error metadata


# Global configuration instance
_global_config = ProvenanceConfig()

# Context variable for thread-local configuration overrides
_context_config: ContextVar[ProvenanceConfig | None] = ContextVar(
    "_context_config", default=None
)


def get_config() -> ProvenanceConfig:
    """Get the current provenance configuration.

    Returns the context-specific configuration if set, otherwise the global configuration.

    Returns:
        Current ProvenanceConfig instance
    """
    context_config = _context_config.get()
    return context_config if context_config is not None else _global_config


def set_global_config(config: ProvenanceConfig) -> None:
    """Set the global provenance configuration.

    Args:
        config: New global configuration
    """
    global _global_config
    _global_config = config


def update_global_config(**kwargs: Any) -> None:
    """Update specific fields in the global configuration.

    Args:
        **kwargs: Configuration fields to update
    """
    global _global_config
    for key, value in kwargs.items():
        if hasattr(_global_config, key):
            setattr(_global_config, key, value)
        else:
            raise ValueError(f"Unknown configuration option: {key}")


def disable_provenance() -> None:
    """Disable all provenance tracking globally."""
    update_global_config(enabled=False)


def enable_provenance() -> None:
    """Enable provenance tracking globally."""
    update_global_config(enabled=True)


def set_performance_mode() -> None:
    """Configure for performance-critical environments.

    Disables expensive features while maintaining basic provenance tracking.
    """
    update_global_config(
        track_literals=False,  # Skip literal tracking for performance
        enable_spans=False,  # Disable span tracking
        fail_on_error=False,  # Always degrade gracefully
        log_errors=False,  # Reduce logging overhead
        max_history_depth=100,  # Limit history depth
        enable_id_interning=True,  # Enable memory optimizations
        max_hash_cache_size=1000,  # Smaller cache for performance
        enable_weak_refs=True,  # Use weak refs to prevent memory leaks
        enable_history_truncation=True,  # Enable history truncation
    )


def set_debug_mode() -> None:
    """Configure for debugging and development.

    Enables all features and detailed error reporting.
    """
    update_global_config(
        enabled=True,
        track_literals=True,
        track_operations=True,
        track_calculations=True,
        fail_on_error=False,  # Still degrade gracefully but log everything
        log_errors=True,
        log_level=logging.DEBUG,
        debug_mode=True,
        include_stack_traces=True,
        max_history_depth=10000,
    )


class provenance_config:
    """Context manager for temporary configuration changes.

    Example:
        >>> with provenance_config(enabled=False):
        ...     # Provenance tracking disabled in this block
        ...     result = FinancialValue(100) + FinancialValue(50)
        >>> # Provenance tracking restored to previous state
    """

    def __init__(self, **kwargs: Any):
        """Initialize with configuration overrides.

        Args:
            **kwargs: Configuration fields to override
        """
        self.overrides = kwargs
        self.token = None

    def __enter__(self) -> ProvenanceConfig:
        """Enter the context with modified configuration."""
        current_config = get_config()

        # Create new config with overrides
        new_config = ProvenanceConfig(
            **{
                field.name: getattr(current_config, field.name)
                for field in current_config.__dataclass_fields__.values()
            }
        )

        # Apply overrides
        for key, value in self.overrides.items():
            if hasattr(new_config, key):
                setattr(new_config, key, value)
            else:
                raise ValueError(f"Unknown configuration option: {key}")

        # Set context configuration
        self.token = _context_config.set(new_config)
        return new_config

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context and restore previous configuration."""
        if self.token is not None:
            _context_config.reset(self.token)


def log_provenance_error(error: Exception, context: str = "", **metadata: Any) -> None:
    """Log a provenance-related error with appropriate detail level.

    Args:
        error: The exception that occurred
        context: Additional context about where the error occurred
        **metadata: Additional metadata to include in the log
    """
    config = get_config()

    if not config.log_errors:
        return

    # Build error message
    error_msg = f"Provenance error in {context}: {error}"

    # Add metadata if in debug mode
    if config.debug_mode and metadata:
        metadata_str = ", ".join(f"{k}={v}" for k, v in metadata.items())
        error_msg += f" (metadata: {metadata_str})"

    # Include stack trace if configured
    exc_info = config.include_stack_traces

    _logger.log(config.log_level, error_msg, exc_info=exc_info)


def should_track_provenance() -> bool:
    """Check if provenance tracking is currently enabled.

    Returns:
        True if provenance should be tracked, False otherwise
    """
    return get_config().enabled


def should_track_literals() -> bool:
    """Check if literal provenance tracking is enabled.

    Returns:
        True if literal provenance should be tracked, False otherwise
    """
    config = get_config()
    return config.enabled and config.track_literals


def should_track_operations() -> bool:
    """Check if operation provenance tracking is enabled.

    Returns:
        True if operation provenance should be tracked, False otherwise
    """
    config = get_config()
    return config.enabled and config.track_operations


def should_track_calculations() -> bool:
    """Check if calculation provenance tracking is enabled.

    Returns:
        True if calculation provenance should be tracked, False otherwise
    """
    config = get_config()
    return config.enabled and config.track_calculations


def should_fail_on_error() -> bool:
    """Check if provenance errors should cause exceptions.

    Returns:
        True if errors should raise exceptions, False for graceful degradation
    """
    return get_config().fail_on_error


def is_provenance_available() -> bool:
    """Check if provenance tracking is available and functional.

    Returns:
        True if provenance can be used, False if it should be disabled
    """
    try:
        config = get_config()
        if not config.enabled:
            return False

        # Test basic functionality
        import hashlib

        hashlib.sha256(b"test")

        return True
    except Exception:
        return False


def get_error_context(error: Exception, operation: str = "") -> dict:
    """Get standardized error context for logging.

    Args:
        error: The exception that occurred
        operation: The operation that was being performed

    Returns:
        Dictionary with error context information
    """
    try:
        context = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "operation": operation,
        }

        config = get_config()
        if config.debug_mode:
            context["error_module"] = getattr(error, "__module__", "unknown")

        if config.include_stack_traces:
            import traceback

            context["stack_trace"] = traceback.format_exc()

        return context
    except Exception:
        # Fallback context if even this fails
        return {
            "error_type": "unknown",
            "error_message": "error_context_generation_failed",
            "operation": operation,
        }
