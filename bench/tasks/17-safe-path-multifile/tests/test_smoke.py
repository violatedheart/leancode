import unittest

from downloads import download_path


class SmokeTests(unittest.TestCase):
    def test_entry_point_exists(self):
        self.assertTrue(callable(download_path))
