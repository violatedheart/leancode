import tempfile
import unittest
from pathlib import Path

from leancode.client import OpenAICompatibleClient
from leancode.doctor import Hardware, recommend
from leancode.meter import RunLedger, TokenUsage


class M0Tests(unittest.TestCase):
    def test_token_usage_reads_openai_and_ollama_fields(self):
        usage = TokenUsage.from_response(
            {"usage": {"prompt_tokens": 120, "completion_tokens": 8, "prompt_tokens_details": {"cached_tokens": 40}}},
            "x" * 800,
            "y" * 40,
        )
        self.assertEqual((usage.prompt_tokens, usage.completion_tokens, usage.cached_prefix_tokens, usage.total_tokens), (120, 8, 40, 128))


    def test_token_usage_falls_back_to_char_estimate(self):
        usage = TokenUsage.from_response({}, "12345", "12345678")
        self.assertTrue(usage.estimated)
        self.assertEqual((usage.prompt_tokens, usage.completion_tokens), (2, 2))

    def test_ollama_usage_fields_are_counted(self):
        usage = TokenUsage.from_response({"prompt_eval_count": 31, "eval_count": 7}, "", "")
        self.assertEqual((usage.prompt_tokens, usage.completion_tokens, usage.total_tokens), (31, 7, 38))


    def test_ledger_records_and_summarizes(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            ledger = RunLedger(Path(directory), "abc")
            ledger.record(TokenUsage(10, 4, 2), step=1, mode="fast")
            ledger.record(TokenUsage(20, 5), step=2, mode="fallback")
            self.assertEqual(ledger.summary(), {"calls": 2, "prompt_tokens": 30, "completion_tokens": 9, "cached_prefix_tokens": 2, "total_tokens": 39})
            self.assertEqual(len(ledger.path.read_text().splitlines()), 2)


    def test_doctor_recommends_model_by_memory(self):
        self.assertIn("1.5b", recommend(Hardware("linux", 4, None, None, "cpu")).model)
        self.assertIn("3b", recommend(Hardware("linux", 6, "GPU", None, "rocm-unknown-vram")).model)
        self.assertIn("3b", recommend(Hardware("linux", 8, None, None, "cpu")).model)
        self.assertIn("7b", recommend(Hardware("linux", 16, "GPU", 10, "cuda")).model)


    def test_openai_compatible_defaults_and_path(self):
        client = OpenAICompatibleClient(base_url="http://localhost:11434/v1/", model="local")
        self.assertEqual(client.base_url, "http://localhost:11434/v1")
        self.assertEqual(client.model, "local")
