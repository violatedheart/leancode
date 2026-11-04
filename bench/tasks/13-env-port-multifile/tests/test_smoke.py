import unittest

from server import server_config


class SmokeTests(unittest.TestCase):
    def test_entry_point_exists(self):
        self.assertTrue(callable(server_config))
