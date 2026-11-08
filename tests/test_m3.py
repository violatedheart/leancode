import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from leancode.index import syntax_check
from leancode.tools import MAX_TOOL_CHARS, ProjectTools, compress_test_output


class M3Tests(unittest.TestCase):
    def test_invalid_syntax_is_not_written(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            repo = Path(directory)
            file = repo / "sample.py"
            original = "def f():\n    return 1\n"
            file.write_text(original, encoding="utf-8")
            with patch("leancode.tools.syntax_check", side_effect=[False, False]):
                result = ProjectTools(repo, None).edit("sample.py", "return 1", "return (")
            self.assertFalse(result.syntax_ok)
            self.assertEqual(file.read_text(), original)

    def test_indentation_repair_is_attempted_once_before_write(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            repo = Path(directory)
            file = repo / "sample.py"
            file.write_text("def f():\n    if ok:\n        return 1\n", encoding="utf-8")
            with patch("leancode.tools.syntax_check", side_effect=[False, True]) as check:
                result = ProjectTools(repo, None).edit("sample.py", "if ok:\nreturn 1", "if ok:\nreturn 2")
            self.assertTrue(result.syntax_ok)
            self.assertEqual(check.call_count, 2)
            self.assertIn("        return 2", file.read_text())

    def test_test_output_keeps_failures_assertions_and_at_most_eight_frames(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            repo = Path(directory)
            output = "FAILED tests/test_math.py::test_sum - assert 2 == 3\nE AssertionError: wanted 3\n"
            output += "".join(f'  File "{repo}/module{i}.py", line {i}, in run\n' for i in range(12))
            output += "x" * 5000
            compressed = compress_test_output(output, repo)
            self.assertLessEqual(len(compressed), MAX_TOOL_CHARS)
            self.assertIn("FAILED tests/test_math.py::test_sum", compressed)
            self.assertIn("AssertionError", compressed)
            self.assertLessEqual(sum("File \"" in line for line in compressed.splitlines()), 8)

    def test_compressed_python_failure_includes_the_failing_source_line(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            repo = Path(directory)
            test_file = repo / "tests" / "test_value.py"
            test_file.parent.mkdir()
            test_file.write_text('self.assertEqual(parse(" YES "), True)\n', encoding="utf-8")
            output = f'ERROR: test_value\n  File "{test_file}", line 1, in test_value\nValueError: invalid input'
            compressed = compress_test_output(output, repo)
            self.assertIn('source tests/test_value.py:1: self.assertEqual(parse(" YES "), True)', compressed)

    def test_no_parser_is_offline_unavailable_instead_of_network_download(self):
        self.assertIsNone(syntax_check(Path("example.ts"), "const x: number = 1;"))


if __name__ == "__main__":
    unittest.main()
