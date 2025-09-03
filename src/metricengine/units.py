class Unit:
    pass


class Dimensionless(Unit):
    pass


class Ratio(Unit):
    pass


class Percent(Ratio):
    pass  # Inherits from Ratio since it's just display-tagged


class Money(Unit):
    pass
