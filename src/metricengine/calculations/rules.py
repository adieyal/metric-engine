# calculations/rules.py
from __future__ import annotations

from functools import wraps
from inspect import signature
from typing import Callable

from ..policy import DEFAULT_POLICY
from ..policy_context import get_policy
from ..value import FV as FV


def skip_if(
    *,
    arg: str,
    policy_flag: str,
    predicate: Callable[[FV], bool],
    none_is_skip: bool = False,
):
    """
    Generic guard: if the policy has `policy_flag` True and `predicate(arg)` is True,
    return FV.none(policy) instead of calling the function.

    - arg: name of the function argument to inspect (expects FV)
    - policy_flag: attribute name on Policy (e.g. 'negative_sales_is_none')
    - predicate: function taking the FV and returning True to skip
    - none_is_skip: if True, treat arg=None (or FV(None)) as a skip
    """

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            bound = signature(fn).bind(*args, **kwargs)
            bound.apply_defaults()
            fv = bound.arguments.get(arg)

            # Only act on FV; otherwise pass through
            if isinstance(fv, FV):
                pol = fv.policy or get_policy() or DEFAULT_POLICY
                if getattr(pol, policy_flag, False):
                    if (fv.is_none() and none_is_skip) or (
                        not fv.is_none() and predicate(fv)
                    ):
                        # preserve type and policy
                        return type(fv).none(pol)
            return fn(*args, **kwargs)

        return wrapper

    return decorator


# Specialization for negative sales
def skip_if_negative_sales(arg: str = "sales"):
    return skip_if(
        arg=arg,
        policy_flag="negative_sales_is_none",
        predicate=lambda x: x < 0,  # strictly negative; adjust if you want <= 0
        none_is_skip=False,
    )
