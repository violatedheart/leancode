import unittest
from solution import sum_values

class TestSumValues(unittest.TestCase):
    def test_includes_last_item(self):
        self.assertEqual(sum_values([1, 2, 3]), 6)
    def test_empty(self):
        self.assertEqual(sum_values([]), 0)

if __name__ == "__main__": unittest.main()
