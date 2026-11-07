from __future__ import annotations

import json
import os
import math
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

from .meter import TokenUsage


@dataclass
class LLMResult:
    content: str
    usage: TokenUsage
    raw: dict[str, Any]


class OpenAICompatibleClient:
    """Small client for Ollama, llama-server, and compatible gateways."""

    def __init__(self, base_url: str | None = None, model: str | None = None, api_key: str | None = None, timeout: float = 120):
        self.base_url = (base_url or os.getenv("LEANCODE_BASE_URL", "http://127.0.0.1:11434/v1")).rstrip("/")
        if model or os.getenv("LEANCODE_MODEL"):
            self.model = model or os.environ["LEANCODE_MODEL"]
        else:
            from .doctor import doctor_report

            self.model = doctor_report()[1].model
        self.api_key = api_key or os.getenv("LEANCODE_API_KEY", "ollama")
        self.timeout = timeout

    def chat(self, *, messages: list[dict[str, str]], max_tokens: int, temperature: float = 0.0, json_schema: dict[str, Any] | None = None) -> LLMResult:
        body: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
            "stop": ["<|im_end|>", "</s>"],
        }
        if urlparse(self.base_url).port == 11434:
            body["options"] = {"num_ctx": 4096}
            # Ollama's OpenAI-compatible endpoint does not consistently honor
            # the native `think` flag. `reasoning_effort: none` disables
            # thinking there, leaving the completion budget for the action.
            body["reasoning_effort"] = "none"
        if json_schema:
            body["response_format"] = {"type": "json_schema", "json_schema": json_schema}
        prompt_text = "\n".join(m.get("content", "") for m in messages)
        if json_schema:
            prompt_text += json.dumps(json_schema, separators=(",", ":"))
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        try:
            import httpx

            response = httpx.post(f"{self.base_url}/chat/completions", json=body, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            raw = response.json()
        except ImportError:
            raw = self._stdlib_post(body, headers)
        except Exception as exc:
            if exc.__class__.__module__.startswith("httpx"):
                raise RuntimeError(f"LLM request failed: {exc}") from exc
            raise
        choices = raw.get("choices") or []
        if not choices:
            raise RuntimeError(f"LLM returned no choices: {json.dumps(raw)[:600]}")
        message = choices[0].get("message") or {}
        content = message.get("content") or ""
        if isinstance(content, list):
            content = "".join(part.get("text", "") for part in content if isinstance(part, dict))
        usage = TokenUsage.from_response(raw, prompt_text, str(content))
        return LLMResult(str(content), usage, raw)

    def count_tokens(self, text: str) -> tuple[int, bool]:
        """Use a local server tokenizer when exposed; otherwise conservatively estimate chars/4."""
        try:
            import httpx

            root = self.base_url[:-3] if self.base_url.endswith("/v1") else self.base_url
            headers = {"Authorization": f"Bearer {self.api_key}"}
            probes = [
                (f"{root}/tokenize", {"content": text}),
                (f"{root}/api/tokenize", {"model": self.model, "prompt": text}),
            ]
            for url, payload in probes:
                try:
                    response = httpx.post(url, json=payload, headers=headers, timeout=min(self.timeout, 3))
                    if response.is_success:
                        body = response.json()
                        value = body.get("count", body.get("token_count"))
                        if value is None and isinstance(body.get("tokens"), list):
                            value = len(body["tokens"])
                        if isinstance(value, int) and value >= 0:
                            return value, False
                except Exception:
                    continue
        except ImportError:
            pass
        return max(1, math.ceil(len(text) / 4)), True

    def _stdlib_post(self, body: dict[str, Any], headers: dict[str, str]) -> dict[str, Any]:
        from urllib.error import HTTPError, URLError
        from urllib.request import Request, urlopen

        request = Request(f"{self.base_url}/chat/completions", data=json.dumps(body).encode(), headers=headers, method="POST")
        try:
            with urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read())
        except (HTTPError, URLError, TimeoutError) as exc:
            raise RuntimeError(f"LLM request failed: {exc}") from exc
