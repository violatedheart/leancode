import unittest
from solution import sum_values

class HiddenSumTests(unittest.TestCase):
    def test_singleton_and_negative(self):
        self.assertEqual(sum_values([8]), 8)
        self.assertEqual(sum_values([-1, -3]), -4)
