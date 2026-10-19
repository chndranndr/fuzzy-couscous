import unittest

from pipeline import transform


class ToFloatTest(unittest.TestCase):
    def test_parses_whitespace(self):
        self.assertEqual(transform.to_float(" 3.5 "), 3.5)

    def test_parses_negative(self):
        self.assertEqual(transform.to_float("-2"), -2.0)


class NormalizeRangeTest(unittest.TestCase):
    def test_clips_bounds(self):
        rows = [["6"], ["2"], ["-1"]]
        self.assertEqual(transform.normalize_range(rows, 0, lo=0, hi=5), [5.0, 2.0, 0.0])

    def test_parses_numeric(self):
        rows = [["1.5"], ["2.5"]]
        self.assertEqual(transform.normalize_range(rows, 0), [1.5, 2.5])


if __name__ == "__main__":
    unittest.main()
