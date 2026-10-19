import unittest

from pipeline import stats


class WeightedMeanCrashTest(unittest.TestCase):
    def test_reported_crash_case(self):
        # Reported symptom: this call crashes with ZeroDivisionError.
        with self.assertRaises(ValueError):
            stats.weighted_mean([1.0, 2.0, 3.0], [0.0, 0.0, 0.0])


if __name__ == "__main__":
    unittest.main()
