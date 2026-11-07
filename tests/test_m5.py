import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from leancode.client import OpenAICompatibleClient


class M5Tests(unittest.TestCase):
    def test_chat_request_is_constrained_and_sets_ollama_context(self):
        seen = {}

        class Response:
            def raise_for_status(self):
                pass

            def json(self):
                return {"choices": [{"message": {"content": "{}"}}], "usage": {"prompt_tokens": 10, "completion_tokens": 2}}

        def post(url, **kwargs):
            seen["url"] = url
            seen.update(kwargs)
            return Response()

        fake_httpx = SimpleNamespace(post=post)
        client = OpenAICompatibleClient("http://127.0.0.1:11434/v1", "local")
        with patch.dict(sys.modules, {"httpx": fake_httpx}):
            result = client.chat(messages=[{"role": "system", "content": "x"}], max_tokens=100, json_schema={"name": "a", "schema": {}})
        body = seen["json"]
        self.assertEqual(seen["url"], "http://127.0.0.1:11434/v1/chat/completions")
        self.assertEqual(body["temperature"], 0.0)
        self.assertEqual(body["max_tokens"], 100)
        self.assertEqual(body["options"]["num_ctx"], 4096)
        self.assertEqual(body["reasoning_effort"], "none")
        self.assertIn("response_format", body)
        self.assertEqual(result.content, "{}")

    def test_non_ollama_compatible_endpoint_keeps_base_url_swappable(self):
        seen = {}

        class Response:
            def raise_for_status(self):
                pass

            def json(self):
                return {"choices": [{"message": {"content": "{}"}}]}

        def post(url, **kwargs):
            seen.update(kwargs)
            return Response()

        fake_httpx = SimpleNamespace(post=post)
        client = OpenAICompatibleClient("http://localhost:8080/v1", "local")
        with patch.dict(sys.modules, {"httpx": fake_httpx}):
            client.chat(messages=[{"role": "user", "content": "x"}], max_tokens=20)
        self.assertNotIn("options", seen["json"])


if __name__ == "__main__":
    unittest.main()
