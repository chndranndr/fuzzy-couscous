"""Hidden grader for t2-top-n. Injected after the agent session.

Pins exact top_n semantics and the --top CLI line format against cases
the prompt only names loosely (ties, n beyond count, n <= 0).
"""

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from pipeline import aggregate, cli


def run_cli(csv_text, *flags):
    with tempfile.TemporaryDirectory() as temporary:
        path = Path(temporary) / "hidden.csv"
        path.write_text(csv_text, encoding="utf-8")
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            cli.main([str(path), "--column", "score", *flags])
        return buffer.getvalue()


class TopNFunctionTest(unittest.TestCase):
    def test_descending(self):
        self.assertEqual(aggregate.top_n([1.0, 9.0, 5.0], 2), [9.0, 5.0])

    def test_ties_kept(self):
        self.assertEqual(aggregate.top_n([4.0, 7.0, 7.0], 3), [7.0, 7.0, 4.0])

    def test_n_exceeds_count(self):
        self.assertEqual(aggregate.top_n([3.0, 1.0], 5), [3.0, 1.0])

    def test_n_equals_count(self):
        self.assertEqual(aggregate.top_n([2.0], 1), [2.0])

    def test_zero_and_negative_n(self):
        self.assertEqual(aggregate.top_n([1.0, 2.0], 0), [])
        self.assertEqual(aggregate.top_n([1.0, 2.0], -3), [])


class TopNCliTest(unittest.TestCase):
    CSV = "id,score\n1,7\n2,\n3,9\n"

    def test_top_flag_line_format(self):
        output = run_cli(self.CSV, "--top", "2")
        self.assertEqual(
            output.strip().splitlines(),
            ["mean\t8.0000", "top_1\t9.0000", "top_2\t7.0000"],
        )

    def test_top_zero_prints_nothing_extra(self):
        output = run_cli(self.CSV, "--top", "0")
        self.assertEqual(output.strip().splitlines(), ["mean\t8.0000"])

    def test_top_beyond_count_prints_all(self):
        output = run_cli(self.CSV, "--top", "9")
        self.assertEqual(
            output.strip().splitlines(),
            ["mean\t8.0000", "top_1\t9.0000", "top_2\t7.0000"],
        )


if __name__ == "__main__":
    unittest.main()
