"""Hidden grader for t1-blank-cells. Injected after the agent session.

Behavioral contract only: blank cells must behave as missing data in
parsing, clipping, aggregation, and the CLI. Both a parse-layer fix
(to_float returns None) and a caller-layer skip satisfy this; downstream
zero-clamping does not.
"""

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from pipeline import aggregate, cli, transform


class BlankCellContractTest(unittest.TestCase):
    def test_blank_cells_dropped_with_bounds(self):
        rows = [["7"], [""], ["9"]]
        self.assertEqual(transform.normalize_range(rows, 0, lo=0, hi=10), [7.0, 9.0])

    def test_all_blank_column_is_empty(self):
        self.assertEqual(transform.normalize_range([[""], [""]], 0), [])

    def test_mean_over_all_blank_raises(self):
        with self.assertRaises(ValueError):
            aggregate.mean(transform.normalize_range([[""]], 0))

    def test_blank_not_clamped_to_zero(self):
        rows = [[""], ["-3"]]
        self.assertEqual(transform.normalize_range(rows, 0, lo=0), [0.0])


class BlankCellCliTest(unittest.TestCase):
    def test_cli_mean_ignores_blank(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "hidden.csv"
            path.write_text("id,score\n1,\n2,5\n3,10\n4,\n", encoding="utf-8")
            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer):
                cli.main([str(path), "--column", "score"])
            self.assertEqual(buffer.getvalue().strip(), "mean\t7.5000")


if __name__ == "__main__":
    unittest.main()
