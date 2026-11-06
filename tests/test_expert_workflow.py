import json
import tempfile
import unittest
from pathlib import Path

from leancode.localize import expand_symbol_graph
from leancode.index import Symbol, SymbolIndex
from leancode.playbook import retrieve
from leancode.runner import measured_default_features
from leancode.tools import ProjectTools
from leancode.workflow import acceptance_criteria, passing_trace, read_repo_notes, write_repo_notes


class ExpertWorkflowTests(unittest.TestCase):
    def test_measured_default_features_keep_reproduction_opt_in(self):
        features = measured_default_features()
        self.assertFalse(features.reproduce)
        self.assertTrue(features.hypothesize)
        self.assertTrue(features.best_of_three)
        self.assertTrue(features.playbook)
        self.assertTrue(features.notes)

    def test_understand_and_notes_are_bounded_and_cached(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            repo = Path(directory)
            task = "Fix median. Preserve the input. Handle empty values. Also keep API compatibility."
            self.assertLessEqual(len(acceptance_criteria(task)), 3)
            note = write_repo_notes(repo, task, "python -m unittest", "python")
            self.assertIn("Test command", note)
            self.assertLessEqual(len(note.split()), 150)
            self.assertIn("python", read_repo_notes(repo, relevant=True))
            self.assertEqual(read_repo_notes(repo, relevant=False), "")

    def test_playbook_retrieval_uses_a_small_relevant_prefix(self):
        result = retrieve("off by one loop missing last item", max_tokens=250)
        self.assertIn("off-by-one", result)
        self.assertLessEqual(len(result), 1000)

    def test_playbook_retrieves_unicode_accent_normalization(self):
        result = retrieve("case insensitive palindrome accented unicode letters", limit=1)
        self.assertIn("unicodedata.normalize('NFD'", result)
        self.assertIn("combining marks", result)

    def test_symbol_graph_adds_direct_caller_without_llm(self):
        index = SymbolIndex(Path.cwd())
        target = Symbol("a.py", "normalize", "function_definition", 1, 3, "def normalize():", ["normalize"])
        caller = Symbol("b.py", "load", "function_definition", 1, 4, "def load():", ["load", "normalize"])
        index.symbols = [target, caller]
        rows = expand_symbol_graph(index, [(target, 2.0)])
        self.assertEqual([row[0].name for row in rows], ["normalize", "load"])

    def test_edit_review_refuses_tests_and_edits_outside_symbol(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            repo = Path(directory)
            (repo / "tests").mkdir()
            (repo / "tests" / "test_x.py").write_text("assert True\n")
            (repo / "mod.py").write_text("def one():\n    return 1\n\ndef two():\n    return 2\n")
            tools = ProjectTools(repo, None)
            self.assertIn("Review rejected", tools.edit("tests/test_x.py", "True", "False").text)
            self.assertIn("outside the selected symbol", tools.edit("mod.py", "return 2", "return 3", within=(1, 2)).text)

    def test_reproduction_test_is_temporary_and_confirms_assertion_failure(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            repo = Path(directory)
            (repo / "tests").mkdir()
            tools = ProjectTools(repo, "python -m unittest discover -s tests -q")
            source = "import unittest\nclass Repro(unittest.TestCase):\n def test_bug(self):\n  self.assertEqual(1, 2)"
            result = tools.reproduce(source)
            self.assertIn("Reproduction confirmed", result.text)
            self.assertTrue((repo / result.changed_path).is_file())
            tools.cleanup_reproduction()
            self.assertEqual(list((repo / "tests").iterdir()), [])

    def test_passing_traces_are_jsonl_prompt_completion_pairs(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            repo = Path(directory)
            passing_trace(repo, "abc", "fix bug", [{"prompt": "small task", "completion": "edit"}])
            row = json.loads((repo / ".leancode" / "traces.jsonl").read_text().strip())
            self.assertEqual(row["task"], "fix bug")
            self.assertEqual(row["prompt"], "small task")


if __name__ == "__main__":
    unittest.main()
