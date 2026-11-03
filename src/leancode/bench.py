from __future__ import annotations

import json
import shutil
import subprocess
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .client import OpenAICompatibleClient
from .meter import RunLedger
from .runner import AgentRunner

NAIVE_SYSTEM = "You are a coding agent. Read the complete repository and tests, then rewrite complete source files to solve the task. Return only JSON."
NAIVE_SCHEMA = {
    "name": "naive_file_rewrite",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "content": {"type": "string"},
            "summary": {"type": "string"},
        },
        "required": ["path", "content", "summary"],
        "additionalProperties": False,
    },
}


@dataclass
class BenchTask:
    id: str
    repo: Path
    task: str
    test_cmd: str
    hidden: Path | None = None


@dataclass
class Score:
    task: str
    naive_pass: bool
    naive_tokens: int
    leancode_pass: bool
    leancode_tokens: int
    steps: int
    seconds: float
    error: str = ""


def load_tasks(project_root: Path) -> list[BenchTask]:
    manifest = project_root / "bench" / "manifest.json"
    rows = json.loads(manifest.read_text(encoding="utf-8"))
    tasks = []
    for row in rows:
        repo = (manifest.parent / row["dir"]).resolve()
        if manifest.parent.resolve() not in repo.parents or not repo.is_dir():
            raise ValueError(f"Invalid benchmark task directory: {row['dir']}")
        hidden = project_root / "bench" / "hidden_tests" / row["hidden"] if row.get("hidden") else None
        tasks.append(BenchTask(row["id"], repo, row["task"], row["test_cmd"], hidden))
    return tasks


def _copy_task(task: BenchTask, target: Path) -> None:
    shutil.copytree(task.repo, target, ignore=shutil.ignore_patterns(".git", ".leancode", "__pycache__", ".pytest_cache", "node_modules"))


def _test(repo: Path, command: str, hidden: Path | None = None) -> tuple[bool, str]:
    copied: list[Path] = []
    try:
        if hidden and hidden.exists():
            destination = repo / "tests"
            destination.mkdir(exist_ok=True)
            sources = hidden.glob("test_*.py") if hidden.is_dir() else [hidden]
            for source in sources:
                target = destination / source.name
                if target.exists():
                    raise ValueError(f"hidden test would overwrite {target}")
                shutil.copy2(source, target)
                copied.append(target)
        result = subprocess.run(command, cwd=repo, shell=True, capture_output=True, text=True, timeout=120)
        return result.returncode == 0, (result.stdout + "\n" + result.stderr)[:10_000]
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, str(exc)
    finally:
        for path in copied:
            path.unlink(missing_ok=True)


def _repo_text(repo: Path) -> str:
    parts = []
    for path in sorted(repo.rglob("*")):
        if not path.is_file() or any(part in {".git", ".leancode", "__pycache__", "node_modules"} for part in path.parts):
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        parts.append(f"\n--- {path.relative_to(repo).as_posix()} ---\n{content}")
    return "".join(parts)


class NaiveBaseline:
    """Deliberately wasteful baseline: full files + full conversation + full-file rewrites."""

    def __init__(self, repo: Path, task: str, test_cmd: str, *, client: Any, budget: int, max_steps: int = 6):
        self.repo, self.task, self.test_cmd = repo.resolve(), task, test_cmd
        self.client, self.budget, self.max_steps = client, budget, max_steps
        self.ledger = RunLedger(self.repo, f"naive-{uuid.uuid4().hex[:8]}")

    def run(self) -> tuple[bool, int, int]:
        history: list[dict[str, str]] = [{"role": "system", "content": NAIVE_SYSTEM}]
        last_test = _test(self.repo, self.test_cmd)[1]
        steps = 0
        for step in range(1, self.max_steps + 1):
            source = _repo_text(self.repo)
            prompt = f"Task: {self.task}\nFull repository files:\n{source}\nFull previous test output:\n{last_test}\nRewrite one complete source file now."
            history.append({"role": "user", "content": prompt})
            count, _estimated = self.client.count_tokens("\n".join(m["content"] for m in history) + json.dumps(NAIVE_SCHEMA, separators=(",", ":")))
            spent = self.ledger.summary()["total_tokens"]
            remaining = self.budget - spent - count
            if count > 4096 or remaining <= 0:
                break
            try:
                response = self.client.chat(messages=history, max_tokens=min(400, remaining), temperature=0.0, json_schema=NAIVE_SCHEMA)
            except Exception as exc:
                last_test = str(exc)[:1200]
                break
            steps += 1
            self.ledger.record(response.usage, step=step, mode="naive")
            history.append({"role": "assistant", "content": response.content})
            try:
                rewrite = json.loads(response.content)
                target = (self.repo / rewrite["path"]).resolve()
                if target != self.repo and self.repo not in target.parents:
                    raise ValueError("baseline path escaped repository")
                if target.suffix.lower() not in {".py", ".pyi", ".js", ".jsx", ".ts", ".tsx"}:
                    raise ValueError("baseline only rewrites source files")
                target.write_text(rewrite["content"], encoding="utf-8")
            except (ValueError, KeyError, OSError, json.JSONDecodeError) as exc:
                last_test = f"invalid rewrite: {exc}"
                history.append({"role": "user", "content": last_test})
                continue
            passed, last_test = _test(self.repo, self.test_cmd)
            history.append({"role": "user", "content": f"Full test output:\n{last_test}\nPassed={passed}."})
            if passed:
                break
        passed, _output = _test(self.repo, self.test_cmd)
        self.ledger.finish(task=self.task, status="pass" if passed else "fail", steps=steps, elapsed_seconds=0)
        return passed, steps, self.ledger.summary()["total_tokens"]


def _collect_run_logs(repo: Path, project_root: Path, task_id: str) -> None:
    source = repo / ".leancode" / "runs"
    if not source.exists():
        return
    destination = project_root / ".leancode" / "runs"
    destination.mkdir(parents=True, exist_ok=True)
    for path in source.glob("*.jsonl"):
        shutil.copy2(path, destination / f"bench-{task_id}-{path.name}")


def _endpoint_available(base_url: str | None) -> bool:
    import os

    base = (base_url or os.getenv("LEANCODE_BASE_URL", "http://127.0.0.1:11434/v1")).rstrip("/")
    request = Request(f"{base}/models", headers={"Authorization": f"Bearer {os.getenv('LEANCODE_API_KEY', 'ollama')}"})
    try:
        with urlopen(request, timeout=1):
            return True
    except HTTPError:
        return True  # Auth-protected compatible endpoint is alive.
    except (URLError, TimeoutError, OSError):
        return False


def format_results(scores: list[Score], model: str) -> str:
    rows = [
        "# LeanCode benchmark results",
        "",
        f"Model: `{model}`. Every lane runs in a fresh temporary copy. Hidden tests are injected only while scoring.",
        "",
        "| Task | Naive pass | Naive tokens | LeanCode pass | LeanCode tokens | Steps | Time (s) |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for score in scores:
        not_run = bool(score.error and score.naive_tokens == 0 and score.leancode_tokens == 0 and score.steps == 0)
        naive_label = "n/a" if not_run else "yes" if score.naive_pass else "no"
        lean_label = "n/a" if not_run else "yes" if score.leancode_pass else "no"
        rows.append(f"| {score.task} | {naive_label} | {score.naive_tokens} | {lean_label} | {score.leancode_tokens} | {score.steps} | {score.seconds:.2f} |")
    naive_total = sum(x.naive_tokens for x in scores)
    lean_total = sum(x.leancode_tokens for x in scores)
    reduction = f"{(naive_total - lean_total) / naive_total * 100:.1f}%" if naive_total else "n/a"
    attempted = [x for x in scores if not (x.error and x.naive_tokens == 0 and x.leancode_tokens == 0 and x.steps == 0)]
    naive_passes = sum(x.naive_pass for x in attempted)
    lean_passes = sum(x.leancode_pass for x in attempted)
    rows += [
        "",
        f"- Tasks: {len(scores)}",
        f"- Naive pass rate: {naive_passes}/{len(attempted)} ({naive_passes / len(attempted) * 100:.1f}%)" if attempted else "- Naive pass rate: n/a (no model runs)",
        f"- LeanCode pass rate: {lean_passes}/{len(attempted)} ({lean_passes / len(attempted) * 100:.1f}%)" if attempted else "- LeanCode pass rate: n/a (no model runs)",
        f"- Naive total tokens: {naive_total}",
        f"- LeanCode total tokens: {lean_total}",
        f"- Token reduction: {reduction}",
    ]
    errors = [x for x in scores if x.error]
    if errors:
        rows += ["", "## Run errors", ""] + [f"- {item.task}: {item.error}" for item in errors]
    return "\n".join(rows) + "\n"


def run_benchmark(project_root: Path, *, model: str | None = None, base_url: str | None = None, budget: int = 6000) -> tuple[list[Score], Path]:
    project_root = project_root.resolve()
    chosen_model = model or OpenAICompatibleClient(base_url=base_url).model
    bench_root = project_root / "bench"
    temp_root = bench_root / ".tmp"
    temp_root.mkdir(parents=True, exist_ok=True)
    tasks = load_tasks(project_root)
    scores: list[Score] = []
    if not _endpoint_available(base_url):
        error = "local OpenAI-compatible endpoint unavailable; start Ollama or llama-server and retry"
        scores = [Score(task.id, False, 0, False, 0, 0, 0.0, error) for task in tasks]
        output = project_root / "RESULTS.md"
        output.write_text(format_results(scores, chosen_model), encoding="utf-8")
        return scores, output
    for task in tasks:
        run_dir = temp_root / f"{task.id}-{uuid.uuid4().hex[:6]}"
        naive_copy, lean_copy = run_dir / "naive", run_dir / "leancode"
        run_dir.mkdir(parents=True)
        start = time.monotonic()
        error = ""
        naive_pass = lean_pass = False
        naive_tokens = lean_tokens = steps = 0
        try:
            _copy_task(task, naive_copy)
            naive = NaiveBaseline(naive_copy, task.task, task.test_cmd, client=OpenAICompatibleClient(base_url, chosen_model), budget=budget)
            naive_pass, _naive_steps, naive_tokens = naive.run()
            if task.hidden:
                naive_pass, _ = _test(naive_copy, task.test_cmd, task.hidden)
            _collect_run_logs(naive_copy, project_root, task.id)

            _copy_task(task, lean_copy)
            result = AgentRunner(lean_copy, task.task, test_cmd=task.test_cmd, budget=budget, model=chosen_model, base_url=base_url).run()
            steps = result.steps
            lean_tokens = result.ledger.summary()["total_tokens"]
            lean_pass = result.status == "pass"
            if task.hidden:
                lean_pass, _ = _test(lean_copy, task.test_cmd, task.hidden)
            _collect_run_logs(lean_copy, project_root, task.id)
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
        finally:
            shutil.rmtree(run_dir, ignore_errors=True)
        scores.append(Score(task.id, naive_pass, naive_tokens, lean_pass, lean_tokens, steps, time.monotonic() - start, error))
        print(f"{task.id}: naive={'pass' if naive_pass else 'fail'} ({naive_tokens}), leancode={'pass' if lean_pass else 'fail'} ({lean_tokens})")
    output = project_root / "RESULTS.md"
    output.write_text(format_results(scores, chosen_model), encoding="utf-8")
    return scores, output
