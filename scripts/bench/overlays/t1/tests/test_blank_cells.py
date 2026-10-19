import unittest

from pipeline import transform


class BlankCellsTest(unittest.TestCase):
    def test_blank_cells_are_dropped(self):
        rows = [["7"], [""], ["9"]]
        self.assertEqual(transform.normalize_range(rows, 0), [7.0, 9.0])


if __name__ == "__main__":
    unittest.main()
