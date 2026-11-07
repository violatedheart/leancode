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
from .runner import AgentRunner, RunFeatures, measured_default_features

def _write_report(path: Path, content: str) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(content)


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


@dataclass
class SweepScore:
    feature: str
    tasks: int
    passed: int
    tokens: int
    solved_tokens: float | None
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
                target_name = "hidden.test.js" if source.suffix == ".js" and command.startswith("node --test") else source.name
                target = destination / target_name
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


def run_benchmark(project_root: Path, *, model: str | None = None, base_url: str | None = None, budget: int = 6000, task_ids: list[str] | None = None) -> tuple[list[Score], Path]:
    project_root = project_root.resolve()
    chosen_model = model or OpenAICompatibleClient(base_url=base_url).model
    bench_root = project_root / "bench"
    temp_root = bench_root / ".tmp"
    temp_root.mkdir(parents=True, exist_ok=True)
    all_tasks = load_tasks(project_root)
    if task_ids:
        requested = list(dict.fromkeys(task_ids))
        known = {task.id for task in all_tasks}
        unknown = [task_id for task_id in requested if task_id not in known]
        if unknown:
            raise ValueError(f"Unknown benchmark task id(s): {', '.join(unknown)}")
        tasks = [task for task in all_tasks if task.id in requested]
    else:
        tasks = all_tasks
    output = project_root / ("RESULTS_FOCUSED.md" if task_ids else "RESULTS.md")
    scores: list[Score] = []
    if not _endpoint_available(base_url):
        error = "local OpenAI-compatible endpoint unavailable; start Ollama or llama-server and retry"
        scores = [Score(task.id, False, 0, False, 0, 0, 0.0, error) for task in tasks]
        _write_report(output, format_results(scores, chosen_model))
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
            result = AgentRunner(lean_copy, task.task, test_cmd=task.test_cmd, budget=budget, model=chosen_model, base_url=base_url, features=measured_default_features()).run()
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
    _write_report(output, format_results(scores, chosen_model))
    return scores, output


def format_sweep(rows: list[SweepScore], model: str) -> str:
    lines = [
        "# LeanCode feature ablation sweep", "",
        f"Model: `{model}`. Each lane runs the same tasks and budget; hidden tests are injected only after an agent run.", "",
        "| Feature set | Pass rate | Total tokens | Tokens per solved task | Time (s) |", "|---|---:|---:|---:|---:|",
    ]
    for row in rows:
        if row.error.startswith("not run:"):
            lines.append(f"| {row.feature} | n/a | n/a | n/a | n/a |")
            continue
        rate = f"{row.passed}/{row.tasks} ({100 * row.passed / row.tasks:.1f}%)" if row.tasks else "n/a"
        solved = f"{row.solved_tokens:.1f}" if row.solved_tokens is not None else "n/a"
        lines.append(f"| {row.feature} | {rate} | {row.tokens} | {solved} | {row.seconds:.1f} |")
    lines += ["", "Keep a feature enabled by default only when the all-on lane improves pass rate or tokens per solved task over the lane with that feature ablated."]
    errors = [row for row in rows if row.error]
    if errors:
        lines += ["", "## Run status", ""] + [f"- {row.feature}: {row.error}" for row in errors]
    return "\n".join(lines) + "\n"


def run_sweep(project_root: Path, *, model: str | None = None, base_url: str | None = None, budget: int = 6000, resume: bool = True) -> tuple[list[SweepScore], Path]:
    """Run an all-on lane and one-feature-at-a-time ablations, checkpointing each completed task."""
    from dataclasses import replace

    project_root = project_root.resolve()
    chosen_model = model or OpenAICompatibleClient(base_url=base_url).model
    tasks = load_tasks(project_root)
    output = project_root / "SWEEP_RESULTS.md"
    state_dir = project_root / ".leancode"
    state_dir.mkdir(parents=True, exist_ok=True)
    checkpoint = state_dir / "sweep-progress.json"
    base = measured_default_features()
    base.reproduce = True
    variants = [("all-on", base)]
    for feature in ("reproduce", "hypothesize", "best_of_three", "playbook", "notes"):
        variants.append((f"without-{feature.replace('_', '-')}", replace(base, **{feature: False})))
    if not _endpoint_available(base_url):
        rows = [SweepScore(name, len(tasks), 0, 0, None, 0.0, "not run: local OpenAI-compatible endpoint unavailable") for name, _ in variants]
        _write_report(output, format_sweep(rows, chosen_model))
        return rows, output
    rows: list[SweepScore] = []
    saved: dict[str, Any] = {}
    if resume and checkpoint.exists():
        try:
            saved = json.loads(checkpoint.read_text(encoding="utf-8"))
            if saved.get("model") != chosen_model or saved.get("budget") != budget or saved.get("task_ids") != [task.id for task in tasks]:
                saved = {}
        except (OSError, json.JSONDecodeError):
            saved = {}
    temp_root = project_root / "bench" / ".sweep"
    temp_root.mkdir(parents=True, exist_ok=True)
    for name, features in variants:
        prior = saved.get("lanes", {}).get(name, {})
        completed = dict(prior.get("tasks", {}))
        passed = sum(bool(item.get("passed")) for item in completed.values())
        token_total = sum(int(item.get("tokens", 0)) for item in completed.values())
        seconds_total = sum(float(item.get("seconds", 0.0)) for item in completed.values())
        started = time.monotonic()
        errors = [item["error"] for item in completed.values() if item.get("error")]
        for task in tasks:
            if task.id in completed:
                continue
            run_dir = temp_root / f"{name}-{task.id}-{uuid.uuid4().hex[:5]}"
            task_started = time.monotonic()
            task_tokens = 0
            okay = False
            error = ""
            try:
                _copy_task(task, run_dir)
                result = AgentRunner(run_dir, task.task, test_cmd=task.test_cmd, budget=budget, model=chosen_model, base_url=base_url, features=features).run()
                task_tokens = result.ledger.summary()["total_tokens"]
                okay = result.status == "pass"
                if task.hidden:
                    hidden_pass, detail = _test(run_dir, task.test_cmd, task.hidden)
                    okay = okay and hidden_pass
                    if not hidden_pass:
                        error = f"{task.id}: hidden tests failed: {detail[:180]}"
            except Exception as exc:
                error = f"run error: {task.id}: {type(exc).__name__}: {exc}"
            finally:
                shutil.rmtree(run_dir, ignore_errors=True)
            elapsed = time.monotonic() - task_started
            completed[task.id] = {"passed": okay, "tokens": task_tokens, "seconds": elapsed, "error": error}
            passed += int(okay)
            token_total += task_tokens
            seconds_total += elapsed
            if error:
                errors.append(error)
            saved = {"model": chosen_model, "budget": budget, "task_ids": [item.id for item in tasks], "lanes": saved.get("lanes", {})}
            saved["lanes"][name] = {"tasks": completed, "seconds": seconds_total}
            checkpoint.write_text(json.dumps(saved, indent=2), encoding="utf-8")
            partial = [SweepScore(lane_name, len(tasks), sum(bool(v.get("passed")) for v in lane.get("tasks", {}).values()), sum(int(v.get("tokens", 0)) for v in lane.get("tasks", {}).values()), None, float(lane.get("seconds", 0.0)), "in progress" if len(lane.get("tasks", {})) < len(tasks) else "") for lane_name, lane in saved["lanes"].items()]
            _write_report(output, format_sweep(partial, chosen_model))
            print(f"{name}/{task.id}: pass={int(okay)} tokens={task_tokens}", flush=True)
        solved_tokens = token_total / passed if passed else None
        rows.append(SweepScore(name, len(tasks), passed, token_total, solved_tokens, seconds_total, "; ".join(errors[:4])))
        print(f"{name}: pass={passed}/{len(tasks)} tokens={token_total} solved_tokens={solved_tokens}")
    _write_report(output, format_sweep(rows, chosen_model))
    checkpoint.unlink(missing_ok=True)
    return rows, output
