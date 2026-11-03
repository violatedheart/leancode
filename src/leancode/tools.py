from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .index import EXTENSIONS, SKIP_DIRS, SymbolIndex, syntax_check

MAX_TOOL_CHARS = 1600  # about 400 tokens at the conservative four-characters/token estimate


def _safe_path(repo: Path, raw: str) -> Path:
    path = (repo / raw).resolve()
    if path != repo and repo not in path.parents:
        raise ValueError("path escapes repository")
    if any(part in SKIP_DIRS for part in path.relative_to(repo).parts):
        raise ValueError("path is excluded")
    return path


def _cap(text: str) -> str:
    suffix = "\n[output capped]"
    return text[:MAX_TOOL_CHARS - len(suffix)] + suffix if len(text) > MAX_TOOL_CHARS else text


@dataclass
class ToolResult:
    text: str
    changed_path: str | None = None
    syntax_ok: bool | None = None


class ProjectTools:
    """Only find/read/edit/test are exposed to the model; no arbitrary shell."""

    def __init__(self, repo: Path, test_cmd: str | None, *, timeout: int = 120):
        self.repo = repo.resolve()
        self.test_cmd = test_cmd
        self.timeout = timeout
        self.index = SymbolIndex(self.repo).build()

    def find(self, query: str) -> ToolResult:
        ranked = self.index.rank(query, limit=12)
        if not ranked:
            return ToolResult("No indexed symbols matched.")
        rows = [f"{s.path}:{s.start_line}-{s.end_line} {s.kind} {s.name} | {s.signature}" for s, _score in ranked]
        return ToolResult(_cap("\n".join(rows)))

    def read(self, path: str, start: int, end: int) -> ToolResult:
        resolved = _safe_path(self.repo, path)
        if not resolved.is_file():
            return ToolResult("File not found.")
        lines = resolved.read_text(encoding="utf-8", errors="replace").splitlines()
        lo, hi = max(1, start), min(len(lines), max(start, end))
        return ToolResult(_cap("\n".join(f"{line}: {lines[line-1]}" for line in range(lo, hi + 1))))

    @staticmethod
    def _flex_pattern(search: str) -> str:
        pieces = re.split(r"(\s+)", search.strip())
        active = [piece for piece in pieces if piece]
        pattern: list[str] = []
        for index, piece in enumerate(active):
            if piece.isspace():
                left = active[index - 1][-1:]
                right = active[index + 1][:1]
                words_touching = (left.isalnum() or left == "_") and (right.isalnum() or right == "_")
                pattern.append(r"\s+" if words_touching else r"\s*")
            else:
                pattern.append(re.escape(piece))
        return "".join(pattern)

    def edit(self, path: str, search: str, replace: str) -> ToolResult:
        resolved = _safe_path(self.repo, path)
        if resolved.suffix.lower() not in EXTENSIONS:
            return ToolResult("Only Python and JavaScript/TypeScript source files can be edited.")
        content = resolved.read_text(encoding="utf-8")
        matches = list(re.finditer(re.escape(search), content)) if search else []
        if len(matches) != 1:
            matches = list(re.finditer(self._flex_pattern(search), content)) if search else []
        if len(matches) != 1:
            return ToolResult(f"Edit needs one unique match; found {len(matches)}. No change made.")
        match = matches[0]
        newline = "\r\n" if "\r\n" in content else "\n"
        replace = replace.replace("\r\n", "\n").replace("\n", newline)
        updated = content[:match.start()] + replace + content[match.end():]
        valid = syntax_check(resolved, updated)
        if valid is False:
            repaired = self._repair_indentation(content, match.start(), replace, newline)
            updated = content[:match.start()] + repaired + content[match.end():]
            valid = syntax_check(resolved, updated)
        if valid is not True:
            reason = "Syntax check failed" if valid is False else "No offline syntax grammar available"
            return ToolResult(f"{reason}; edit discarded.", syntax_ok=False)
        resolved.write_text(updated, encoding="utf-8")
        self.index = SymbolIndex(self.repo).build(force=True)
        return ToolResult(f"Edited {path}; syntax check passed.", path, True)

    @staticmethod
    def _repair_indentation(content: str, start: int, replacement: str, newline: str) -> str:
        line_start = content.rfind("\n", 0, start) + 1
        prefix = content[line_start:start]
        if prefix.strip() or newline not in replacement:
            return replacement
        base = len(prefix.expandtabs(4))
        lines = replacement.splitlines()
        if len(lines) < 2:
            return replacement
        repaired = [lines[0]]
        previous_indent = base
        previous_text = lines[0].strip()
        for line in lines[1:]:
            stripped = line.lstrip()
            if not stripped:
                repaired.append("")
                continue
            if previous_text.endswith(":"):
                desired = previous_indent + 4
            else:
                desired = base
            current_indent = len(line) - len(stripped)
            repaired.append(" " * max(desired, base + current_indent) + stripped)
            previous_indent = len(repaired[-1]) - len(stripped)
            previous_text = stripped
        return newline.join(repaired)

    def test(self) -> ToolResult:
        if not self.test_cmd:
            return ToolResult("No --test-cmd was configured; test was not run.")
        try:
            proc = subprocess.run(self.test_cmd, cwd=self.repo, shell=True, capture_output=True, text=True, timeout=self.timeout)
            output = compress_test_output(proc.stdout + "\n" + proc.stderr, self.repo)
            return ToolResult(f"exit={proc.returncode}\n{output}")
        except subprocess.TimeoutExpired as exc:
            output = (exc.stdout or b"").decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
            return ToolResult(f"test timed out after {self.timeout}s\n{compress_test_output(output, self.repo)}")


def compress_test_output(output: str, repo: Path) -> str:
    lines = output.splitlines()
    root = str(repo.resolve()).replace("\\", "/").rstrip("/").lower()
    names = [line for line in lines if re.search(r"(?:FAILED|ERROR|FAIL):?\s+\S+|^\s*test_[\w.]+.*(?:FAIL|ERROR)|===\s*(?:short test summary|failures)", line, re.I)]
    assertions = [line for line in lines if re.search(r"AssertionError|AssertionFailed|Expected|Actual|assert\s|^E\s+|Error:|Exception:", line, re.I)]
    frames = []
    for index, line in enumerate(lines):
        normalized = line.replace("\\", "/").lower()
        is_frame = bool(re.search(r"File ['\"].*\.(?:py|js|jsx|ts|tsx)|\bat\s+.*\.(?:js|jsx|ts|tsx):\d+", line))
        if is_frame and (root in normalized or not re.search(r"site-packages|node_modules|/lib/python", normalized)):
            frames.append((index, line))
    frames = frames[:8]
    picked = list(dict.fromkeys(names[:10] + assertions[:10] + [line for _, line in frames]))
    return _cap("\n".join(picked) if picked else "No failure lines found; test command returned no recognizable diagnostics.")
