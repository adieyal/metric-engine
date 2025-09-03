from typing import Optional

from .policy import Policy
from .units import Dimensionless, Money, Percent, Ratio
from .utils import SupportsDecimal
from .value import FinancialValue

# ---- Public exports ----------------------------------------------------------
__all__ = [
    "ratio",
    "percent",
    "money",
    "dimensionless",
    "RatioFV",
    "PercentFV",
    "MoneyFV",
    "zero_money",
    "zero_ratio",
    "zero_percent",
    "zero_dimensionless",
]

# ---- Type aliases ------------------------------------------------------------
RatioFV = FinancialValue[Ratio]
PercentFV = FinancialValue[Percent]
MoneyFV = FinancialValue[Money]

# ---- Factories ---------------------------------------------------------------


def ratio(x: Optional[SupportsDecimal], *, policy: Optional[Policy] = None) -> RatioFV:
    """Create a ratio-valued FV (numeric stored as 0..1)."""
    return FinancialValue(x, policy=policy, unit=Ratio)


def percent(
    x: Optional[SupportsDecimal],
    *,
    policy: Optional[Policy] = None,
    input: str = "ratio",  # "ratio" (0..1) or "percent" (0..100)
    strict: bool = False,
) -> PercentFV:
    """
    Create a percent-valued FV.
    - input="ratio": x is 0..1
    - input="percent": x is 0..100 and will be converted to 0..1
    """
    if x is None:
        return FinancialValue(None, policy=policy, unit=Percent)
    # convert to ratio storage if needed
    if input == "percent":
        try:
            from .utils import to_decimal

            decimal_val = to_decimal(x)
            if decimal_val is not None:
                x = decimal_val / 100
            else:
                x = None
        except Exception:
            if strict:
                raise
    elif input != "ratio":
        raise ValueError("percent(input=...) must be 'ratio' or 'percent'")

    # Do NOT poke private args; use public API if needed
    return FinancialValue(
        x, policy=policy, unit=Percent
    )  # formatting handled by Policy/FV


def money(x: Optional[SupportsDecimal], *, policy: Optional[Policy] = None) -> MoneyFV:
    return FinancialValue(x, policy=policy, unit=Money)


def dimensionless(
    x: Optional[SupportsDecimal], *, policy: Optional[Policy] = None
) -> FinancialValue[Dimensionless]:
    return FinancialValue(x, policy=policy, unit=Dimensionless)


# Back-compat alias (optional)
dimless = dimensionless

# ---- Ergonomic zeros ---------------------------------------------------------


def zero_money(*, policy: Optional[Policy] = None) -> MoneyFV:
    return FinancialValue(0, policy=policy, unit=Money)


def zero_ratio(*, policy: Optional[Policy] = None) -> RatioFV:
    return FinancialValue(0, policy=policy, unit=Ratio)


def zero_percent(*, policy: Optional[Policy] = None) -> PercentFV:
    # stored as ratio
    return FinancialValue(0, policy=policy, unit=Percent)


def zero_dimensionless(
    *, policy: Optional[Policy] = None
) -> FinancialValue[Dimensionless]:
    return FinancialValue(0, policy=policy, unit=Dimensionless)
