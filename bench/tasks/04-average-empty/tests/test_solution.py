import unittest
from averages import safe_average

class TestAverage(unittest.TestCase):
    def test_mean(self):
        self.assertEqual(safe_average([2, 4]), 3)
    def test_empty(self):
        self.assertIsNone(safe_average([]))

if __name__ == "__main__": unittest.main()
