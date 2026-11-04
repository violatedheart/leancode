import unittest

from report import total_amount


class SmokeTests(unittest.TestCase):
    def test_entry_point_exists(self):
        self.assertTrue(callable(total_amount))
