"""Deterministic helpers for per-repository workflow state."""
from __future__ import annotations

import re
import json
import re
from pathlib import Path

MAX_NOTE_TOKENS = 150


def acceptance_criteria(task: str) -> list[str]:
    parts = [re.sub(r"\s+", " ", part).strip(" .;-") for part in re.split(r"\n|(?<=[.!?])\s+|;", task)]
    return [part[:180] for part in parts if part][:3]


def write_repo_notes(repo: Path, task: str, test_cmd: str | None, language: str = "unknown") -> str:
    path = repo / ".leancode" / "notes.md"
    try:
        existing = path.read_text(encoding="utf-8")
    except OSError:
        existing = ""
    command = f"- Test command: `{test_cmd}`" if test_cmd else "- Test command: not configured"
    criteria = acceptance_criteria(task)
    criteria_line = "- Acceptance: " + "; ".join(criteria) if criteria else "- Acceptance: see current task"
    identifiers = list(dict.fromkeys(re.findall(r"`([A-Za-z_]\w*)`|\b([A-Za-z_][A-Za-z_0-9]{2,})\b", task)))
    flat_ids = list(dict.fromkeys(a or b for a, b in identifiers if (a or b).lower() not in {"the", "and", "for", "with", "from", "when", "must", "return", "task", "make", "fix"}))[:8]
    identifiers_line = "- Key identifiers: " + ", ".join(flat_ids) if flat_ids else "- Key identifiers: none extracted"
    past = []
    traces = repo / ".leancode" / "traces.jsonl"
    try:
        rows = [json.loads(line) for line in traces.read_text(encoding="utf-8").splitlines()[-3:]]
        past = ["- Past fix: " + " ".join(row.get("task", "").split())[:100] for row in rows if row.get("task")]
    except (OSError, ValueError, TypeError):
        pass
    past_line = "\n".join(past)
    body = "# LeanCode repo notes\n\n" + command + f"\n- Language: {language}\n" + criteria_line + "\n" + identifiers_line + "\n- Conventions: preserve the surrounding style; prefer the smallest local edit.\n" + (past_line + "\n" if past_line else "")
    if existing and "Conventions:" in existing:
        body = "# LeanCode repo notes\n\n" + command + f"\n- Language: {language}\n" + criteria_line + "\n" + identifiers_line + "\n" + existing.split("\n", 2)[-1]
    # Bound durable context; notes are advisory and never treated as instructions.
    words = body.split()
    if len(words) > MAX_NOTE_TOKENS:
        body = " ".join(words[:MAX_NOTE_TOKENS]) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return body


def read_repo_notes(repo: Path, *, relevant: bool) -> str:
    if not relevant:
        return ""
    path = repo / ".leancode" / "notes.md"
    try:
        return " ".join(path.read_text(encoding="utf-8").split())[:600]
    except OSError:
        return ""


def passing_trace(repo: Path, run_id: str, task: str, pairs: list[dict[str, str]]) -> None:
    if not pairs:
        return
    import json

    path = repo / ".leancode" / "traces.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        for pair in pairs:
            row = {"run_id": run_id, "task": task, **pair}
            stream.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
