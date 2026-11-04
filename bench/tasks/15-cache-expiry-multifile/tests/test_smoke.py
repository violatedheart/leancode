import unittest

from cache_api import lookup


class SmokeTests(unittest.TestCase):
    def test_entry_point_exists(self):
        self.assertTrue(callable(lookup))
