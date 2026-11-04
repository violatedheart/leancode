import unittest

from server import server_config


class PortTests(unittest.TestCase):
    def test_default_and_trimmed_port(self):
        self.assertEqual(server_config({})["port"], 8000)
        self.assertEqual(server_config({"APP_PORT": " 9000 "})["port"], 9000)

    def test_blank_defaults_and_invalid_range_rejected(self):
        self.assertEqual(server_config({"APP_PORT": "  "})["port"], 8000)
        for value in ("0", "65536", "nope"):
            with self.assertRaises(ValueError):
                server_config({"APP_PORT": value})
