"""Tests for sample calculations module."""


from metricengine.calculations.sample import SampleCalculations


class TestSampleCalculations:
    """Test the sample calculations class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.calculations = SampleCalculations()
        self.registered_calcs = {}

        def mock_register(name):
            def decorator(func):
                self.registered_calcs[name] = func
                return func

            return decorator

        self.register = mock_register

    def test_register_all_creates_functions(self):
        """Test that register_all creates expected calculation functions."""
        self.calculations.register_all(self.register)

        # Check that both functions were registered
        assert "net_present_value" in self.registered_calcs
        assert "simple_interest" in self.registered_calcs

        # Check that registered items are callable
        assert callable(self.registered_calcs["net_present_value"])
        assert callable(self.registered_calcs["simple_interest"])

    def test_net_present_value_calculation(self):
        """Test net present value calculation."""
        self.calculations.register_all(self.register)
        npv_func = self.registered_calcs["net_present_value"]

        # Test with sample cash flows: [-100, 30, 30, 30, 30] at 10% rate
        cash_flows = [
            30,
            30,
            30,
            30,
        ]  # Initial investment not included in cash flows list
        rate = 0.10

        result = npv_func(cash_flows, rate)

        # Expected: 30/1.1 + 30/1.21 + 30/1.331 + 30/1.4641 ≈ 95.10
        expected = 30 / 1.1 + 30 / 1.21 + 30 / 1.331 + 30 / 1.4641
        assert abs(result - expected) < 0.01

    def test_net_present_value_zero_rate(self):
        """Test net present value with zero discount rate."""
        self.calculations.register_all(self.register)
        npv_func = self.registered_calcs["net_present_value"]

        cash_flows = [100, 100, 100]
        rate = 0.0

        result = npv_func(cash_flows, rate)

        # With 0% rate, NPV should equal sum of cash flows
        assert result == 300.0

    def test_net_present_value_empty_cash_flows(self):
        """Test net present value with empty cash flows."""
        self.calculations.register_all(self.register)
        npv_func = self.registered_calcs["net_present_value"]

        cash_flows = []
        rate = 0.10

        result = npv_func(cash_flows, rate)

        # Empty cash flows should result in 0
        assert result == 0.0

    def test_simple_interest_calculation(self):
        """Test simple interest calculation."""
        self.calculations.register_all(self.register)
        si_func = self.registered_calcs["simple_interest"]

        principal = 1000.0
        rate = 0.05  # 5%
        time = 2.0  # 2 years

        result = si_func(principal, rate, time)

        # Simple interest = P * R * T = 1000 * 0.05 * 2 = 100
        assert result == 100.0

    def test_simple_interest_zero_principal(self):
        """Test simple interest with zero principal."""
        self.calculations.register_all(self.register)
        si_func = self.registered_calcs["simple_interest"]

        result = si_func(0.0, 0.05, 2.0)
        assert result == 0.0

    def test_simple_interest_zero_rate(self):
        """Test simple interest with zero rate."""
        self.calculations.register_all(self.register)
        si_func = self.registered_calcs["simple_interest"]

        result = si_func(1000.0, 0.0, 2.0)
        assert result == 0.0

    def test_simple_interest_zero_time(self):
        """Test simple interest with zero time."""
        self.calculations.register_all(self.register)
        si_func = self.registered_calcs["simple_interest"]

        result = si_func(1000.0, 0.05, 0.0)
        assert result == 0.0

    def test_simple_interest_negative_values(self):
        """Test simple interest with negative values."""
        self.calculations.register_all(self.register)
        si_func = self.registered_calcs["simple_interest"]

        # Negative principal
        result = si_func(-1000.0, 0.05, 2.0)
        assert result == -100.0

        # Negative rate (e.g., deflation)
        result = si_func(1000.0, -0.05, 2.0)
        assert result == -100.0

        # Negative time (not realistic but mathematically valid)
        result = si_func(1000.0, 0.05, -2.0)
        assert result == -100.0

    def test_net_present_value_negative_rate(self):
        """Test net present value with negative discount rate."""
        self.calculations.register_all(self.register)
        npv_func = self.registered_calcs["net_present_value"]

        cash_flows = [100, 100]
        rate = -0.10  # -10% (deflationary scenario)

        result = npv_func(cash_flows, rate)

        # With negative rate, future cash flows are worth more
        # 100/0.9 + 100/0.81 ≈ 234.57
        expected = 100 / 0.9 + 100 / 0.81
        assert abs(result - expected) < 0.01
