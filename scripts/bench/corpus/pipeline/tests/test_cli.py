import contextlib
import io
import unittest
from pathlib import Path

from pipeline import cli

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "data" / "sample.csv"


class CliMeanTest(unittest.TestCase):
    def test_mean_score(self):
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            cli.main([str(SAMPLE), "--column", "score"])
        self.assertEqual(buffer.getvalue().strip(), "mean\t8.0000")


if __name__ == "__main__":
    unittest.main()
