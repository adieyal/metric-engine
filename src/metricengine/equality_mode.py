# equality_mode.py
from contextvars import ContextVar
from enum import Enum, auto


class EqualityMode(Enum):
    VALUE_ONLY = auto()
    VALUE_AND_UNIT = auto()
    VALUE_UNIT_AND_POLICY = auto()


fv_equality_mode = ContextVar("fv_equality_mode", default=EqualityMode.VALUE_AND_UNIT)
