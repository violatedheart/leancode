import unittest
from collections_ext import unique_items

class HiddenUniqueTests(unittest.TestCase):
    def test_mixed_hashable_values(self):
        self.assertEqual(unique_items(["x", 1, "x", 1.0]), ["x", 1])
