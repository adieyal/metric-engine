class Unit:
    """Base unit class."""

    pass


class Dimensionless(Unit):
    """Unit for dimensionless values."""

    pass


class Ratio(Unit):
    """Unit for ratio values."""

    pass


class Percent(Ratio):
    """Unit for percentage values (inherits from Ratio)."""

    pass  # Inherits from Ratio since it's just display-tagged


class Money(Unit):
    """Unit for monetary values."""

    code: str = "USD"  # Default currency code

    def __init_subclass__(cls, code: str = "USD", **kwargs):
        super().__init_subclass__(**kwargs)
        cls.code = code


# Helper function to create Money units with specific currencies
def currency_unit(code: str) -> type[Money]:
    """Create a Money unit class with a specific currency code."""

    class CurrencyMoney(Money, code=code):
        pass

    CurrencyMoney.__name__ = f"Money_{code}"
    return CurrencyMoney


# Common currency units
USD = currency_unit("USD")
EUR = currency_unit("EUR")
GBP = currency_unit("GBP")
ZAR = currency_unit("ZAR")
