import tempfile
import unittest
from pathlib import Path

from leancode.bench import Score, format_results, load_tasks
from leancode.cli import build_parser


class M4Tests(unittest.TestCase):
    def test_benchmark_has_twelve_tasks_and_multifile_cases(self):
        root = Path(__file__).resolve().parents[1]
        tasks = load_tasks(root)
        self.assertGreaterEqual(len(tasks), 12)
        self.assertTrue((tasks[8].repo / "invoice.py").exists())
        self.assertTrue((tasks[8].repo / "money.py").exists())
        self.assertTrue((tasks[0].hidden).exists())

    def test_results_include_totals_and_token_reduction(self):
        text = format_results([Score("one", True, 1000, True, 700, 1, 2.5)], "local-model")
        self.assertIn("Token reduction: 30.0%", text)
        self.assertIn("Naive pass rate: 1/1", text)
        self.assertIn("| Task | Naive pass | Naive tokens | LeanCode pass | LeanCode tokens | Steps | Time (s) |", text)

    def test_zero_baseline_tokens_reports_na(self):
        text = format_results([Score("one", False, 0, False, 0, 0, 0)], "local-model")
        self.assertIn("Token reduction: n/a", text)

    def test_no_endpoint_is_reported_as_not_run(self):
        text = format_results([Score("one", False, 0, False, 0, 0, 0, "endpoint unavailable")], "local-model")
        self.assertIn("| one | n/a | 0 | n/a | 0 | 0 | 0.00 |", text)
        self.assertIn("pass rate: n/a (no model runs)", text)

    def test_benchmark_can_select_tasks_without_changing_full_benchmark(self):
        args = build_parser().parse_args(["bench", "--task", "02-palindrome-normalize", "--task", "07-parse-bool"])
        self.assertEqual(args.task_ids, ["02-palindrome-normalize", "07-parse-bool"])
        self.assertFalse(args.sweep)

    def test_sweep_task_filter_conflict_is_parsed(self):
        args = build_parser().parse_args(["bench", "--sweep", "--task", "01-sum-last-item"])
        self.assertTrue(args.sweep)
        self.assertEqual(args.task_ids, ["01-sum-last-item"])


if __name__ == "__main__":
    unittest.main()
