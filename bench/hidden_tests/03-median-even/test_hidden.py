import unittest
from stats import median

class HiddenMedianTests(unittest.TestCase):
    def test_does_not_mutate(self):
        values = [4, 1, 3, 2]
        self.assertEqual(median(values), 2.5)
        self.assertEqual(values, [4, 1, 3, 2])
