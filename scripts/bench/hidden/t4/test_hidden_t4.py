"""Hidden grader for t4-weighted-mean. Injected after the agent session.

Pins the full validation contract stated in the module docstring,
including the cases the crash report never mentions. A crash-only fix
(guard the zero sum) passes the visible repro but fails here.
"""

import unittest

from pipeline import stats


class ValidationContractTest(unittest.TestCase):
    def test_zero_sum_raises_value_error(self):
        with self.assertRaises(ValueError):
            stats.weighted_mean([1.0, 2.0], [0.0, 0.0])

    def test_negative_weight_raises(self):
        with self.assertRaises(ValueError):
            stats.weighted_mean([1.0, 2.0], [1.0, -0.5])

    def test_all_negative_weights_raise(self):
        with self.assertRaises(ValueError):
            stats.weighted_mean([1.0, 2.0], [-1.0, -2.0])

    def test_single_zero_weight_is_legal(self):
        # A lone zero weight contributes nothing; the sum is still positive.
        self.assertAlmostEqual(stats.weighted_mean([2.0, 4.0], [0.0, 1.0]), 4.0)

    def test_length_mismatch_raises(self):
        with self.assertRaises(ValueError):
            stats.weighted_mean([1.0, 2.0], [1.0])

    def test_weighted_value_is_correct(self):
        self.assertAlmostEqual(stats.weighted_mean([1.0, 3.0], [3.0, 1.0]), 1.5)

    def test_empty_input_raises(self):
        with self.assertRaises(ValueError):
            stats.weighted_mean([], [])


if __name__ == "__main__":
    unittest.main()
