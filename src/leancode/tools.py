from __future__ import annotations

import re
import shlex
import shutil
import sys
import subprocess
import difflib
import uuid
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
        self._temporary_repros: list[tuple[Path, Path, bool]] = []

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

    def edit(self, path: str, search: str, replace: str, *, within: tuple[int, int] | None = None, max_changed_lines: int = 40) -> ToolResult:
        resolved = _safe_path(self.repo, path)
        if resolved.suffix.lower() not in EXTENSIONS:
            return ToolResult("Only Python and JavaScript/TypeScript source files can be edited.")
        if any(part.lower() in {"test", "tests", "__tests__"} for part in resolved.relative_to(self.repo).parts) or resolved.name.startswith("test_"):
            return ToolResult("Review rejected edits to existing tests.")
        content = resolved.read_text(encoding="utf-8")
        matches = list(re.finditer(re.escape(search), content)) if search else []
        if len(matches) != 1:
            matches = list(re.finditer(self._flex_pattern(search), content)) if search else []
        if within and len(matches) == 1:
            lines_before = content.count("\n", 0, matches[0].start()) + 1
            lines_after = content.count("\n", 0, matches[0].end()) + 1
            if lines_before < within[0] or lines_after > within[1]:
                return ToolResult("Edit rejected: search block is outside the selected symbol.")
        if len(matches) != 1:
            return ToolResult(f"Edit needs one unique match; found {len(matches)}. No change made.")
        match = matches[0]
        newline = "\r\n" if "\r\n" in content else "\n"
        replace = replace.replace("\r\n", "\n").replace("\n", newline)
        updated = content[:match.start()] + replace + content[match.end():]
        diff = list(difflib.unified_diff(content.splitlines(), updated.splitlines(), lineterm=""))
        changed_lines = sum(line.startswith(("+", "-")) and not line.startswith(("+++", "---")) for line in diff)
        if changed_lines > max_changed_lines:
            return ToolResult(f"Edit rejected: {changed_lines} changed lines exceeds the {max_changed_lines}-line cap.")
        if any(re.search(r"(?:skip|xfail)\s*=|pytest\.mark\.(?:skip|xfail)|unittest\.skip", line, re.I) for line in diff if line.startswith("+")):
            return ToolResult("Review rejected a skip/xfail change.")
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

    def reproduce(self, source: str, *, extension: str = ".py") -> ToolResult:
        """Run one temporary, bounded regression test and always remove it."""
        if not self.test_cmd:
            return ToolResult("Reproduction skipped: no configured test command.")
        lines = source.splitlines()
        if not lines or len(lines) > 30:
            return ToolResult("Reproduction rejected: test must contain 1-30 lines.")
        if not any(word in source for word in ("assert", "expect(", "toBe(", "toEqual(")):
            return ToolResult("Reproduction rejected: test needs an assertion.")
        if extension not in {".py", ".js"}:
            return ToolResult("Reproduction rejected: unsupported test language.")
        tests = self.repo / "tests"
        tests.mkdir(exist_ok=True)
        suffix = f".test{extension}" if extension == ".js" else ".py"
        prefix = "leancode_repro_" if extension == ".js" else "test_leancode_repro_"
        path = tests / f"{prefix}{uuid.uuid4().hex[:8]}{suffix}"
        cache_path = tests / "__pycache__"
        had_cache = cache_path.exists()
        keep = False
        if path.exists():
            return ToolResult("Reproduction rejected: temporary path collision.")
        try:
            path.write_text(source + "\n", encoding="utf-8")
            result = subprocess.run(self.test_cmd, cwd=self.repo, shell=True, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=self.timeout)
            compressed = compress_test_output(result.stdout + "\n" + result.stderr, self.repo)
            if result.returncode == 0:
                return ToolResult("Reproduction did not fail; no patch should be made from it.\n" + compressed)
            if not re.search(r"FAILED|FAIL|AssertionError|assert\s", result.stdout + result.stderr, re.I):
                return ToolResult("Reproduction failed for an unrelated setup/runtime reason.\n" + compressed)
            keep = True
            self._temporary_repros.append((path, cache_path, had_cache))
            return ToolResult("Reproduction confirmed: the new assertion fails.\n" + compressed, path.relative_to(self.repo).as_posix())
        except (OSError, subprocess.TimeoutExpired) as exc:
            return ToolResult(f"Reproduction error: {exc}")
        finally:
            if not keep:
                path.unlink(missing_ok=True)
            if not keep and not had_cache and cache_path.is_dir():
                shutil.rmtree(cache_path, ignore_errors=True)

    def cleanup_reproduction(self) -> None:
        for test_path, cache_path, had_cache in self._temporary_repros:
            test_path.unlink(missing_ok=True)
            if not had_cache and cache_path.is_dir():
                shutil.rmtree(cache_path, ignore_errors=True)
        self._temporary_repros.clear()

    def test_target(self, failure: str) -> ToolResult | None:
        """Run one reported pytest node before the configured full suite when possible."""
        if not self.test_cmd:
            return None
        try:
            parts = shlex.split(self.test_cmd)
        except ValueError:
            return None
        if not any("pytest" in part for part in parts):
            return None
        match = re.search(r"([\w./\\-]+\.py)(?:::(\w+))?", failure)
        if not match:
            return None
        selector = match.group(1).replace("\\", "/")
        try:
            resolved = _safe_path(self.repo, selector)
        except ValueError:
            return None
        if not resolved.is_file():
            return None
        if match.group(2):
            selector += "::" + match.group(2)
        try:
            proc = subprocess.run([sys.executable, "-m", "pytest", "-q", selector], cwd=self.repo, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=self.timeout)
            return ToolResult(f"exit={proc.returncode}\n{compress_test_output(proc.stdout + chr(10) + proc.stderr, self.repo)}")
        except (OSError, subprocess.TimeoutExpired) as exc:
            return ToolResult(f"target test failed to run: {exc}")

    def verify_lints(self, paths: list[str]) -> ToolResult:
        """Run installed, deterministic linters/type checkers on edited files."""
        results = []
        python_files = [p for p in paths if p.endswith((".py", ".pyi"))]
        js_files = [p for p in paths if p.endswith((".js", ".jsx", ".ts", ".tsx"))]
        checks = []
        if python_files:
            for binary, label in (("ruff", "ruff check"), ("pyflakes", "pyflakes")):
                if shutil.which(binary):
                    checks.append(([binary, *(python_files if binary == "pyflakes" else ["check", *python_files])], label))
            if shutil.which("mypy"):
                checks.append((["mypy", *python_files], "mypy"))
        if js_files and shutil.which("tsc") and (self.repo / "tsconfig.json").is_file():
            checks.append((["tsc", "--noEmit"], "tsc --noEmit"))
        for command, label in checks:
            try:
                proc = subprocess.run(command, cwd=self.repo, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
                text = _cap((proc.stdout + "\n" + proc.stderr).strip())
                results.append(f"{label}: exit={proc.returncode}\n{text}")
                if proc.returncode:
                    return ToolResult("\n".join(results))
            except (OSError, subprocess.TimeoutExpired) as exc:
                results.append(f"{label}: unavailable ({exc})")
        return ToolResult("\n".join(results) if results else "No supported linter/type checker installed for edited files.")

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
            proc = subprocess.run(self.test_cmd, cwd=self.repo, shell=True, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=self.timeout)
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
