import tempfile
import unittest
from pathlib import Path

from leancode.index import Symbol, SymbolIndex, parse_symbols, syntax_check
from leancode.tools import ProjectTools


class M1Tests(unittest.TestCase):
    def test_python_bom_file_is_indexed_and_syntax_checked(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            repo = Path(directory)
            source = repo / "sample.py"
            source.write_text("\ufeffdef format_duration(seconds):\n    return f'{seconds}s'\n", encoding="utf-8")
            symbols, has_error = parse_symbols(source, repo)
            self.assertFalse(has_error)
            self.assertEqual([symbol.name for symbol in symbols], ["format_duration"])
            self.assertTrue(syntax_check(source, source.read_text(encoding="utf-8")))

    def test_old_index_cache_is_rebuilt_after_index_format_update(self):
        import json
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            repo = Path(directory)
            source = repo / "sample.py"
            source.write_text("\ufeffdef format_duration(seconds):\n    return seconds\n", encoding="utf-8")
            cache = repo / ".leancode" / "index.json"
            cache.parent.mkdir()
            cache.write_text(json.dumps({"version": 1, "files": {}}), encoding="utf-8")
            index = SymbolIndex(repo).build()
            self.assertIn("format_duration", [symbol.name for symbol in index.symbols])
            self.assertEqual(json.loads(cache.read_text(encoding="utf-8"))["version"], 2)

    def test_javascript_syntax_uses_node_when_tree_sitter_is_unavailable(self):
        import shutil
        if not shutil.which("node"):
            self.skipTest("node is not installed")
        path = Path.cwd() / "syntax-check.mjs"
        self.assertTrue(syntax_check(path, "export function answer() { return 42; }"))
        self.assertFalse(syntax_check(path, "export function answer( {"))

    def test_javascript_symbols_are_indexed_without_a_grammar_pack(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            repo = Path(directory)
            source = repo / "retry.js"
            source.write_text(
                "function retry(attempt) {\n    if (attempt > 2) return false;\n    return true;\n}\n",
                encoding="utf-8",
            )
            symbols, _syntax = parse_symbols(source, repo)
            self.assertEqual([(item.name, item.start_line, item.end_line) for item in symbols], [("retry", 1, 4)])

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
