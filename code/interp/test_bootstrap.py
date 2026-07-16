import numpy as np
from interp.bootstrap import micro_rate_ci

class TestMicroRateCi:

    def test_rate_is_micro_averaged(self):
        rate, low, high = micro_rate_ci([1, 3], [2, 6], np.random.default_rng(0))
        assert rate == 0.5
        assert low <= rate <= high

    def test_empty_denominator_returns_nan(self):
        rate, low, high = micro_rate_ci([0, 0], [0, 0], np.random.default_rng(0))
        assert np.isnan(rate) and np.isnan(low) and np.isnan(high)

    def test_degenerate_rate_has_zero_width_interval(self):
        rate, low, high = micro_rate_ci([2, 3], [2, 3], np.random.default_rng(0))
        assert rate == 1.0
        assert low == 1.0 and high == 1.0

    def test_same_seed_reproduces_interval(self):
        first = micro_rate_ci([1, 5, 2], [4, 8, 3], np.random.default_rng(0))
        second = micro_rate_ci([1, 5, 2], [4, 8, 3], np.random.default_rng(0))
        assert first == second
