"""Hidden grader for t3-clip-refactor. Injected after the agent session.

Pins the extracted clip function and boundary behavior that a sloppy
refactor would drift on.
"""

import unittest

from pipeline import transform


class ClipFunctionTest(unittest.TestCase):
    def test_clip_exists_and_clips(self):
        self.assertEqual(transform.clip([6.0, 2.0, -1.0], 0, 5), [5.0, 2.0, 0.0])

    def test_clip_none_bounds_is_identity(self):
        self.assertEqual(transform.clip([1.5, -2.0], None, None), [1.5, -2.0])

    def test_clip_equal_bounds_collapses(self):
        self.assertEqual(transform.clip([0.0, 9.0], 3, 3), [3.0, 3.0])

    def test_clip_empty(self):
        self.assertEqual(transform.clip([], 0, 5), [])


class NormalizeRangePreservedTest(unittest.TestCase):
    def test_bounds_still_route_through_clipping(self):
        rows = [["6"], ["2"], ["-1"]]
        self.assertEqual(transform.normalize_range(rows, 0, lo=0, hi=5), [5.0, 2.0, 0.0])

    def test_blank_cells_still_dropped(self):
        self.assertEqual(transform.normalize_range([["1"], [""], ["2"]], 0), [1.0, 2.0])

    def test_negative_bounds(self):
        rows = [["-5"], ["0"], ["5"]]
        self.assertEqual(transform.normalize_range(rows, 0, lo=-2, hi=2), [-2.0, 0.0, 2.0])


if __name__ == "__main__":
    unittest.main()
