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
