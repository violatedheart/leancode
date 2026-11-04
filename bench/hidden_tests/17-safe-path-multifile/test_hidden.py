import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from downloads import download_path


class SafePathTests(unittest.TestCase):
    def test_rejects_escape_and_absolute_paths(self):
        with TemporaryDirectory(dir=Path.cwd()) as root:
            for name in ("../secret", "%2e%2e/secret", str(Path(root).parent / "secret")):
                with self.assertRaises(ValueError):
                    download_path(root, name)

    def test_accepts_nested_path_under_root(self):
        with TemporaryDirectory(dir=Path.cwd()) as root:
            self.assertEqual(download_path(root, "images/a.png"), Path(root) / "images" / "a.png")
