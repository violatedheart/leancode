from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class TokenUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cached_prefix_tokens: int = 0
    estimated: bool = False

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens

    @classmethod
    def from_response(cls, response: dict[str, Any], prompt: str, completion: str) -> "TokenUsage":
        usage = response.get("usage") or {}
        prompt_tokens = usage.get("prompt_tokens", usage.get("input_tokens", response.get("prompt_eval_count")))
        completion_tokens = usage.get("completion_tokens", usage.get("output_tokens", response.get("eval_count")))
        details = usage.get("prompt_tokens_details") or usage.get("input_tokens_details") or {}
        cached = details.get("cached_tokens", details.get("cache_read_input_tokens", 0)) or 0
        if prompt_tokens is None:
            prompt_tokens = max(1, (len(prompt) + 3) // 4)
            estimate = True
        else:
            estimate = False
        if completion_tokens is None:
            completion_tokens = max(1, (len(completion) + 3) // 4)
            estimate = True
        return cls(int(prompt_tokens), int(completion_tokens), int(cached), estimate)


class RunLedger:
    def __init__(self, repo: Path, run_id: str):
        self.repo = repo.resolve()
        self.run_id = run_id
        self.path = self.repo / ".leancode" / "runs" / f"{run_id}.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.calls: list[dict[str, Any]] = []

    def record(self, usage: TokenUsage, *, step: int, mode: str) -> None:
        entry = {"run_id": self.run_id, "step": step, "mode": mode, **asdict(usage), "total_tokens": usage.total_tokens}
        self.calls.append(entry)
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(entry, separators=(",", ":")) + "\n")

    def summary(self) -> dict[str, int]:
        return {
            "calls": len(self.calls),
            "prompt_tokens": sum(x["prompt_tokens"] for x in self.calls),
            "completion_tokens": sum(x["completion_tokens"] for x in self.calls),
            "cached_prefix_tokens": sum(x["cached_prefix_tokens"] for x in self.calls),
            "total_tokens": sum(x["total_tokens"] for x in self.calls),
        }

    def finish(self, *, task: str, status: str, steps: int, elapsed_seconds: float) -> None:
        entry = {
            "run_id": self.run_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "task": task,
            "status": status,
            "steps": steps,
            "elapsed_seconds": round(elapsed_seconds, 3),
            "summary": self.summary(),
        }
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(entry, separators=(",", ":")) + "\n")
