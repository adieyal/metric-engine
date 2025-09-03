from contextvars import ContextVar, Token
from enum import Enum, auto
from typing import TYPE_CHECKING, Optional

# NOTE: no import of DEFAULT_POLICY here

if TYPE_CHECKING:
    from .policy import Policy  # only for type checking


class PolicyResolution(Enum):
    CONTEXT = auto()
    LEFT_OPERAND = auto()
    STRICT_MATCH = auto()


# Store None in context by default; resolve lazily when needed
_current_policy: ContextVar[Optional["Policy"]] = ContextVar(
    "_current_policy", default=None
)
_current_resolution: ContextVar[PolicyResolution] = ContextVar(
    "_policy_resolution", default=PolicyResolution.CONTEXT
)


def _default_policy() -> "Policy":
    # Late import to avoid circulars during package init
    from .policy import DEFAULT_POLICY

    return DEFAULT_POLICY


def get_policy() -> Optional["Policy"]:
    """May return None if no ambient policy has been set."""
    return _current_policy.get()


def get_active_policy() -> "Policy":
    """Always returns a Policy (falls back to DEFAULT_POLICY if none ambient)."""
    return _current_policy.get() or _default_policy()


def get_resolution() -> PolicyResolution:
    return _current_resolution.get()


class use_policy:
    def __init__(self, policy: "Policy"):
        self._policy = policy
        self._token: Optional[Token[Optional[Policy]]] = None

    def __enter__(self) -> "use_policy":
        self._token = _current_policy.set(self._policy)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._token is not None:
            _current_policy.reset(self._token)
            self._token = None
        else:
            # If token was lost/None, ensure context doesn't leak
            try:
                _current_policy.set(None)
            except LookupError:
                pass


class use_policy_resolution:
    def __init__(self, mode: PolicyResolution):
        self._mode = mode
        self._token: Optional[Token[PolicyResolution]] = None

    def __enter__(self) -> "use_policy_resolution":
        self._token = _current_resolution.set(self._mode)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._token is not None:
            _current_resolution.reset(self._token)
            self._token = None
