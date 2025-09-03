from . import __doc__  # noqa: F401


class SampleCalculations:
    @staticmethod
    def register_all(register):
        @register("net_present_value")
        def net_present_value(cash_flows, rate: float):
            total = 0.0
            for i, cf in enumerate(cash_flows, start=1):
                total += cf / ((1 + rate) ** i)
            return total

        @register("simple_interest")
        def simple_interest(principal: float, rate: float, time: float):
            return principal * rate * time
