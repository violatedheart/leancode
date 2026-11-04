import tempfile
import unittest
from pathlib import Path

from leancode.bench import SweepScore, _copy_task, _test, format_sweep, load_tasks


class ExpertBenchTests(unittest.TestCase):
    def test_six_harder_tasks_are_multi_file_and_start_green(self):
        root = Path(__file__).resolve().parents[1]
        tasks = [task for task in load_tasks(root) if task.id.startswith(("13-", "14-", "15-", "16-", "17-", "18-"))]
        self.assertEqual(len(tasks), 6)
        for task in tasks:
            sources = [p for p in task.repo.rglob("*") if p.is_file() and p.suffix in {".py", ".js"}]
            self.assertGreaterEqual(len(sources), 2)
            with tempfile.TemporaryDirectory(dir=root) as directory:
                copy = Path(directory) / "task"
                _copy_task(task, copy)
                visible, _ = _test(copy, task.test_cmd)
                self.assertTrue(visible, task.id)

    def test_sweep_reports_tokens_per_solved_task(self):
        text = format_sweep([SweepScore("all-on", 10, 5, 3000, 600.0, 12.3)], "small-model")
        self.assertIn("| all-on | 5/10 (50.0%) | 3000 | 600.0 | 12.3 |", text)


if __name__ == "__main__":
    unittest.main()
