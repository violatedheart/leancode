from __future__ import annotations

import re
import subprocess
from collections import defaultdict
from pathlib import Path

from .index import SymbolIndex

PATH_LINE = re.compile(r"([\w./\\-]+\.(?:py|pyi|js|jsx|mjs|cjs|ts|tsx)):(\d+)")


def _git_diff(repo: Path) -> str:
    try:
        return subprocess.run(["git", "diff", "--", "."], cwd=repo, capture_output=True, text=True, timeout=3).stdout[:4000]
    except (OSError, subprocess.TimeoutExpired):
        return ""


def localize(index: SymbolIndex, task: str, failing_output: str = "", *, limit: int = 12) -> list[tuple[object, float]]:
    evidence = "\n".join(part for part in (task, failing_output, _git_diff(index.repo)) if part)
    scores: dict[tuple[str, str, int], float] = defaultdict(float)
    symbols = {(s.path, s.name, s.start_line): s for s in index.symbols}
    for symbol, score in index.rank(evidence, limit=max(limit * 3, 24)):
        scores[(symbol.path, symbol.name, symbol.start_line)] += score
    for match in PATH_LINE.finditer(evidence):
        path, line = match.group(1).replace("\\", "/"), int(match.group(2))
        for key, symbol in symbols.items():
            if symbol.path.endswith(path) and symbol.start_line <= line <= symbol.end_line:
                scores[key] += 8.0
    changed = set(re.findall(r"(?:\+\+\+ b/|--- a/)([^\n]+)", _git_diff(index.repo)))
    for key, symbol in symbols.items():
        if symbol.path in changed:
            scores[key] += 0.4
    ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0][0], item[0][2]))
    return [(symbols[key], score) for key, score in ranked[:limit]]


def read_symbol(repo: Path, symbol) -> str:
    lines = (repo / symbol.path).read_text(encoding="utf-8", errors="replace").splitlines()
    return "\n".join(f"{n}: {lines[n-1]}" for n in range(symbol.start_line, min(symbol.end_line, len(lines)) + 1))
