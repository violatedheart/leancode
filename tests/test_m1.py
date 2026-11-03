import tempfile
import unittest
from pathlib import Path

from leancode.index import Symbol, SymbolIndex
from leancode.tools import ProjectTools


class M1Tests(unittest.TestCase):
    def test_bm25_ranks_matching_symbol(self):
        index = SymbolIndex(Path.cwd())
        index.symbols = [
            Symbol("src/parser.py", "parse_csv", "function_definition", 1, 8, "def parse_csv(text):", ["parse", "csv", "delimiter"]),
            Symbol("src/users.py", "load_user", "function_definition", 1, 8, "def load_user(id):", ["user", "database"]),
        ]
        ranked = index.rank("fix csv delimiter parser", limit=2)
        self.assertEqual(ranked[0][0].name, "parse_csv")

    def test_index_updates_incrementally_and_detects_same_size_edit(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            repo = Path(directory)
            source = repo / "demo.py"
            source.write_text("def one(): pass\n", encoding="utf-8")
            symbol = Symbol("demo.py", "one", "function_definition", 1, 1, "def one():", ["one"])
            from unittest.mock import patch

            with patch("leancode.index.parse_symbols", return_value=([symbol], False)) as parse:
                first = SymbolIndex(repo).build()
                self.assertEqual(first.updated, 1)
                self.assertEqual(len(first.symbols), 1)
                second = SymbolIndex(repo).build()
                self.assertEqual(second.updated, 0)
                self.assertEqual(parse.call_count, 1)
                source.write_text("def two(): pass\n", encoding="utf-8")
                third = SymbolIndex(repo).build()
                self.assertEqual(third.updated, 1)
                self.assertEqual(parse.call_count, 2)

    def test_index_retries_files_when_grammar_was_missing(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            repo = Path(directory)
            (repo / "demo.py").write_text("def one(): pass\n", encoding="utf-8")
            symbol = Symbol("demo.py", "one", "function_definition", 1, 1, "def one():", ["one"])
            from unittest.mock import patch

            with patch("leancode.index.parse_symbols", side_effect=[([], None), ([symbol], False)]) as parse:
                first = SymbolIndex(repo).build()
                second = SymbolIndex(repo).build()
            self.assertEqual(first.symbols, [])
            self.assertEqual([item.name for item in second.symbols], ["one"])
            self.assertEqual(parse.call_count, 2)

    def test_edit_uses_fuzzy_whitespace_and_reindexes(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            repo = Path(directory)
            (repo / "sample.py").write_text("def add(a, b):\n    return a+b\n", encoding="utf-8")
            symbol = Symbol("sample.py", "add", "function_definition", 1, 2, "def add(a,b):", ["add"])
            from unittest.mock import patch

            with patch("leancode.tools.syntax_check", return_value=True):
                tools = ProjectTools(repo, None)
                result = tools.edit("sample.py", "return a + b", "return a - b")
                self.assertTrue(result.syntax_ok)
                self.assertIn("return a - b", (repo / "sample.py").read_text())

    def test_edit_refuses_ambiguous_search_and_path_escape(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            repo = Path(directory)
            (repo / "sample.py").write_text("x = 1\nx = 1\n", encoding="utf-8")
            from unittest.mock import patch

            with patch("leancode.tools.syntax_check", return_value=True):
                tools = ProjectTools(repo, None)
                result = tools.edit("sample.py", "x = 1", "x = 2")
                self.assertIn("found 2", result.text)
                self.assertEqual((repo / "sample.py").read_text(), "x = 1\nx = 1\n")
                with self.assertRaises(ValueError):
                    tools.read("../outside.py", 1, 2)

    def test_test_tool_never_runs_without_configured_command(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            result = ProjectTools(Path(directory), None).test()
            self.assertIn("not run", result.text)


if __name__ == "__main__":
    unittest.main()
