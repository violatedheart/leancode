import json
import tempfile
import unittest
from pathlib import Path

from leancode.client import LLMResult
from leancode.index import Symbol, SymbolIndex
from leancode.meter import TokenUsage
from leancode.runner import ACTION_SCHEMA, SCHEMA_TOKENS_ESTIMATE, SYSTEM_PROMPT, AgentRunner
from leancode.tools import ProjectTools, ToolResult


class FakeClient:
    def __init__(self, actions):
        self.actions = list(actions)
        self.calls = []

    def count_tokens(self, text):
        return (len(text) + 3) // 4, True

    def chat(self, **kwargs):
        self.calls.append(kwargs)
        return LLMResult(json.dumps(self.actions.pop(0)), TokenUsage(100, 20, 0), {})


class FakeTools:
    def __init__(self, repo, outcomes):
        self.repo = repo
        self.test_cmd = "configured-test"
        self.index = SymbolIndex(repo)
        self.index.symbols = [Symbol("sample.py", "target", "function_definition", 1, 2, "def target():", ["target", "bug"])]
        self.outcomes = list(outcomes)
        self.test_calls = 0
        self.edits = []

    def test(self):
        self.test_calls += 1
        return ToolResult(self.outcomes.pop(0) if self.outcomes else "exit=0\n2 passed")

    def edit(self, path, search, replace):
        self.edits.append((path, search, replace))
        return ToolResult("edited", path, True)

    def find(self, query):
        return ToolResult("sample.py:1-2 target")

    def read(self, path, start, end):
        return ToolResult("1: def target():")


def action(name, **values):
    base = {"action": name, "path": None, "search": None, "replace": None, "query": None, "start": None, "end": None, "summary": None}
    base.update(values)
    return base


class M2Tests(unittest.TestCase):
    def test_find_and_read_localize_new_edit_targets(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            repo = Path(directory)
            (repo / "config.py").write_text("def parse_config(value):\n    return value\n", encoding="utf-8")
            tools = ProjectTools(repo, None)
            agent = AgentRunner(repo, "Update configuration parsing", client=FakeClient([]), tools=tools)
            found = agent._tool(action("find", query="parse_config"))
            self.assertIn("parse_config", found.text)
            self.assertIn("config.py", agent.selected_symbols)

            (repo / "other.py").write_text("def normalize_header(value):\n    return value\n", encoding="utf-8")
            agent.index = SymbolIndex(repo).build(force=True)
            agent.tools.index = agent.index
            read = agent._tool(action("read", path="other.py", start=1, end=2))
            self.assertIn("normalize_header", read.text)
            self.assertIn("other.py", agent.selected_symbols)

    def test_localized_patch_candidates_exclude_tests_but_keep_production_symbol(self):
        production = Symbol("src/palindrome.py", "is_palindrome", "function_definition", 1, 4, "def is_palindrome(text):", ["palindrome"])
        test_function = Symbol("tests/test_solution.py", "test_plain", "function_definition", 5, 6, "def test_plain(self):", ["test_plain"])
        js_test = Symbol("src/palindrome.test.ts", "isPalindrome", "function_declaration", 1, 4, "function isPalindrome():", ["palindrome"])
        test_named = Symbol("src/checks.py", "test_helpers", "function_definition", 1, 2, "def test_helpers():", ["test_helpers"])
        candidates = [(production, 2.0), (test_function, 1.5), (js_test, 1.25), (test_named, 1.0)]
        self.assertEqual(AgentRunner._production_candidates(candidates), [(production, 2.0)])

    def test_edit_repairs_wrong_model_path_only_on_unique_localized_match(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            repo = Path(directory)
            (repo / "sample.py").write_text("def target():\n    return 0\n", encoding="utf-8")
            tools = ProjectTools(repo, "python -c pass")
            symbol = Symbol("sample.py", "target", "function_definition", 1, 2, "def target():", ["target"])
            agent = AgentRunner(repo, "fix target", client=FakeClient([]), tools=tools)
            agent.selected_symbols = {symbol.path: symbol}
            result = agent._tool(action("edit", path="src/main.py", search="def target():\n    return 0", replace="def target():\n    return 1"))
            self.assertTrue(result.changed_path)
            self.assertEqual(result.changed_path, "sample.py")
            self.assertIn("return 1", (repo / "sample.py").read_text(encoding="utf-8"))

    def test_edit_rejects_test_paths_before_localization(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            repo = Path(directory)
            (repo / "tests").mkdir()
            (repo / "tests" / "test_case.py").write_text("def check():\n    return True\n", encoding="utf-8")
            tools = FakeTools(repo, [])
            agent = AgentRunner(repo, "fix target", client=FakeClient([]), tools=tools)
            result = agent._tool(action("edit", path="tests/test_case.py", search="return True", replace="return False"))
            self.assertIn("edits to existing tests", result.text)
            self.assertEqual(tools.edits, [])
            self.assertIn("return True", (repo / "tests" / "test_case.py").read_text(encoding="utf-8"))

    def test_prefix_and_schema_fit_budget(self):
        self.assertLessEqual((len(SYSTEM_PROMPT) + 3) // 4 + SCHEMA_TOKENS_ESTIMATE, 300)
        self.assertEqual(ACTION_SCHEMA["strict"], True)

    def test_fast_path_one_call_edits_then_stops_on_green(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            repo = Path(directory)
            (repo / "sample.py").write_text("def target():\n    return 0\n", encoding="utf-8")
            client = FakeClient([action("edit", path="sample.py", search="return 0", replace="return 1", summary="fixed")])
            tools = FakeTools(repo, ["exit=1\nFAILED test_target", "exit=0\n1 passed"])
            result = AgentRunner(repo, "fix target bug", client=client, tools=tools).run()
            self.assertEqual(result.status, "pass")
            self.assertEqual(result.steps, 1)
            self.assertEqual(len(client.calls), 1)
            self.assertEqual(tools.test_calls, 2)
            self.assertEqual(client.calls[0]["temperature"], 0.0)
            self.assertLessEqual(client.calls[0]["max_tokens"], 400)
            self.assertEqual(len(client.calls[0]["messages"]), 2)
            self.assertEqual(result.ledger.summary()["total_tokens"], 120)

    def test_fallback_is_stateless_and_uses_only_action_tools(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            repo = Path(directory)
            (repo / "sample.py").write_text("def target():\n    return 0\n", encoding="utf-8")
            client = FakeClient([
                action("find", query="target"),
                action("test"),
            ])
            tools = FakeTools(repo, ["exit=1\nFAILED test_target", "exit=0\n1 passed"])
            result = AgentRunner(repo, "fix target bug", client=client, tools=tools).run()
            self.assertEqual(result.status, "pass")
            self.assertEqual(result.steps, 2)
            self.assertTrue(all(len(call["messages"]) == 2 for call in client.calls))
            self.assertIn("Steps left", client.calls[1]["messages"][1]["content"])
            self.assertEqual(client.calls[0]["json_schema"], client.calls[1]["json_schema"])

    def test_prompt_that_would_exhaust_budget_is_never_sent(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            repo = Path(directory)
            client = FakeClient([action("finish")])
            tools = FakeTools(repo, ["exit=0"])
            result = AgentRunner(repo, "tiny task", budget=10, client=client, tools=tools).run()
            self.assertEqual(client.calls, [])
            self.assertEqual(result.reason, "token budget reached")

    def test_no_test_command_stops_after_one_verified_patch(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            repo = Path(directory)
            (repo / "sample.py").write_text("def target():\n    return 0\n", encoding="utf-8")
            client = FakeClient([action("edit", path="sample.py", search="return 0", replace="return 1")])
            tools = FakeTools(repo, [])
            tools.test_cmd = None
            result = AgentRunner(repo, "fix target bug", client=client, tools=tools).run()
            self.assertEqual(result.status, "unverified")
            self.assertEqual(result.reason, "tests not configured")
            self.assertEqual(result.steps, 1)


if __name__ == "__main__":
    unittest.main()
