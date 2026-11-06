from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from . import __version__
from .client import OpenAICompatibleClient
from .doctor import doctor_report
from .runner import AgentRunner, measured_default_features
from .bench import run_benchmark, run_sweep


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="leancode", description="Local, token-frugal coding agent")
    parser.add_argument("--version", action="version", version=f"leancode {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor", help="detect hardware and recommend a local model")
    run = sub.add_parser("run", help="solve a coding task in a repository")
    run.add_argument("--repo", type=Path, default=Path.cwd())
    run.add_argument("--task", required=True)
    run.add_argument("--test-cmd")
    run.add_argument("--budget", type=int, default=6000)
    run.add_argument("--model")
    run.add_argument("--base-url")
    run.add_argument("--expert-workflow", action="store_true", help="also reproduce a failing test before patching")
    bench = sub.add_parser("bench", help="run the bundled benchmark")
    bench.add_argument("--budget", type=int, default=6000)
    bench.add_argument("--model")
    bench.add_argument("--base-url")
    bench.add_argument("--sweep", action="store_true", help="ablate expert workflow features across all benchmark tasks")
    bench.add_argument("--fresh", action="store_true", help="discard saved sweep progress and start from the first task")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "doctor":
        hardware, recommendation = doctor_report()
        print("Hardware:")
        print(json.dumps(asdict(hardware), indent=2))
        print("\nRecommendation:")
        print(f"  Model: {recommendation.model}")
        print(f"  Context: {recommendation.context}")
        print(f"  Pull: {recommendation.pull_command}")
        print(f"  Reason: {recommendation.reason}")
        return 0
    if args.command == "run":
        repo = args.repo.resolve()
        if not repo.is_dir():
            print(f"Repository does not exist: {repo}", file=sys.stderr)
            return 2
        try:
            features = measured_default_features()
            features.reproduce = args.expert_workflow
            result = AgentRunner(repo, args.task, test_cmd=args.test_cmd, budget=args.budget, model=args.model, base_url=args.base_url, features=features).run()
            summary = result.ledger.summary()
            print(f"{result.status}: {result.summary} ({result.reason})")
            print(f"steps={result.steps} tokens={summary['total_tokens']} (prompt={summary['prompt_tokens']}, completion={summary['completion_tokens']}, cached-prefix={summary['cached_prefix_tokens']})")
            print(f"usage log: {result.ledger.path}")
            if result.diff:
                print("\nPatch diff:\n" + result.diff)
            return 0 if result.status == "pass" else 1
        except (RuntimeError, OSError, ValueError) as exc:
            print(f"leancode: {exc}", file=sys.stderr)
            return 2
    if args.command == "bench":
        try:
            cwd = Path.cwd().resolve()
            project_root = cwd if (cwd / "bench" / "manifest.json").is_file() else Path(__file__).resolve().parents[2]
            if args.sweep:
                scores, output = run_sweep(project_root, model=args.model, base_url=args.base_url, budget=args.budget, resume=not args.fresh)
            else:
                scores, output = run_benchmark(project_root, model=args.model, base_url=args.base_url, budget=args.budget)
            print(f"\nWrote {output}")
            if args.sweep:
                failed_to_run = any(
                    score.error.startswith(("not run:", "in progress")) or "run error:" in score.error
                    for score in scores
                )
                return 0 if scores and not failed_to_run else 1
            return 0 if scores and not any(score.error for score in scores) else 1
        except (RuntimeError, OSError, ValueError, json.JSONDecodeError) as exc:
            print(f"benchmark failed: {exc}", file=sys.stderr)
            return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
