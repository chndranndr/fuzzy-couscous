import unittest
from pathlib import Path

from pipeline import ingest

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "data" / "sample.csv"


class ReadRecordsTest(unittest.TestCase):
    def test_reads_sample(self):
        header, rows = ingest.read_records(SAMPLE)
        self.assertEqual(header, ["id", "score", "weight"])
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0], ["1", "7", "0.5"])


class ColumnIndexTest(unittest.TestCase):
    def test_finds_column(self):
        header, _ = ingest.read_records(SAMPLE)
        self.assertEqual(ingest.column_index(header, "weight"), 2)

    def test_missing_column_raises(self):
        with self.assertRaises(ValueError):
            ingest.column_index(["a", "b"], "c")


if __name__ == "__main__":
    unittest.main()
