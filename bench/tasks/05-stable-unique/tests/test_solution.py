import unittest
from collections_ext import unique_items

class TestUnique(unittest.TestCase):
    def test_keeps_first_order(self):
        self.assertEqual(unique_items([3, 1, 3, 2, 1]), [3, 1, 2])

if __name__ == "__main__": unittest.main()
