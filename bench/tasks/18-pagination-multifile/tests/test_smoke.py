import unittest

from api import list_items


class SmokeTests(unittest.TestCase):
    def test_entry_point_exists(self):
        self.assertTrue(callable(list_items))
