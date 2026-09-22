import unittest

from pipeline import aggregate


class MeanTest(unittest.TestCase):
    def test_mean(self):
        self.assertEqual(aggregate.mean([1.0, 2.0, 3.0]), 2.0)

    def test_empty_raises(self):
        with self.assertRaises(ValueError):
            aggregate.mean([])


if __name__ == "__main__":
    unittest.main()
