import unittest
from stats import median

class TestMedian(unittest.TestCase):
    def test_even(self):
        self.assertEqual(median([1, 2, 8, 9]), 5)
    def test_odd(self):
        self.assertEqual(median([9, 1, 3]), 3)

if __name__ == "__main__": unittest.main()
