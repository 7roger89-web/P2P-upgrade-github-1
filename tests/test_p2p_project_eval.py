from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import p2p_eval  # noqa: E402


class P2PProjectEvalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        (REPO_ROOT / ".tmp").mkdir(parents=True, exist_ok=True)

    def test_completion_uses_installed_runtime_project_eval_helper(self) -> None:
        with tempfile.TemporaryDirectory(prefix="p2p-eval-route-", dir=REPO_ROOT / ".tmp") as raw:
            target = Path(raw)
            runtime = target / ".p2p" / "system"
            helper = runtime / "scripts" / "p2p_eval.py"
            helper.parent.mkdir(parents=True)
            helper.write_text("# installed project-eval fixture\n", encoding="utf-8")
            suite = target / ".p2p" / "evals" / "suite.json"
            suite.parent.mkdir(parents=True)
            suite.write_text("{}\n", encoding="utf-8")

            command, oracle = p2p_eval._case_command("completion-contract", target, runtime, suite)

            self.assertEqual(Path(command[1]), helper)
            self.assertEqual(oracle, "project_eval_schema")

    def test_completion_uses_packaged_source_helper_without_installed_runtime(self) -> None:
        with tempfile.TemporaryDirectory(prefix="p2p-eval-package-", dir=REPO_ROOT / ".tmp") as raw:
            target = Path(raw)
            (target / "governance").mkdir(parents=True)
            (target / "manifest").mkdir(parents=True)
            (target / "manifest" / "package.json").write_text("{}\n", encoding="utf-8")
            (target / "scripts").mkdir(parents=True)
            helper = target / "scripts" / "p2p_eval.py"
            helper.write_text("# packaged project-eval fixture\n", encoding="utf-8")
            suite = target / ".p2p" / "evals" / "suite.json"
            suite.parent.mkdir(parents=True)
            suite.write_text("{}\n", encoding="utf-8")
            (target / "scripts" / "package_release.py").write_text("# package producer fixture\n", encoding="utf-8")
            runtime = target / "runtime"
            runtime.mkdir()

            command, oracle = p2p_eval._case_command("completion-contract", target, runtime, suite)

            self.assertEqual(Path(command[1]), helper)
            self.assertEqual(oracle, "project_eval_schema")

    def test_installed_target_does_not_fall_back_to_root_source_helper(self) -> None:
        with tempfile.TemporaryDirectory(prefix="p2p-eval-no-fallback-", dir=REPO_ROOT / ".tmp") as raw:
            target = Path(raw)
            runtime = target / ".p2p" / "system"
            (runtime / "scripts").mkdir(parents=True)
            suite = target / ".p2p" / "evals" / "suite.json"
            suite.parent.mkdir(parents=True)
            suite.write_text("{}\n", encoding="utf-8")
            root_helper = target / "scripts" / "p2p_eval.py"
            root_helper.parent.mkdir(parents=True)
            root_helper.write_text("# source checkout fixture\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "missing canonical installed runtime project evaluator"):
                p2p_eval._case_command("completion-contract", target, runtime, suite)

    def test_trial_commands_are_part_of_the_existing_eval_helper(self) -> None:
        parser = p2p_eval.parser()
        run_args = parser.parse_args(
            [
                "run",
                "--suite",
                ".p2p/evals/suite.json",
                "--variant",
                "baseline",
                "--trial",
                "1",
                "--target-root",
                ".tmp/eval-target",
            ]
        )
        record_args = parser.parse_args(
            [
                "record",
                "--suite",
                ".p2p/evals/suite.json",
                "--trial-record",
                ".tmp/eval-record.json",
            ]
        )
        self.assertEqual(run_args.variant, "baseline")
        self.assertEqual(run_args.trial, 1)
        self.assertEqual(record_args.trial_record, ".tmp/eval-record.json")

    def test_current_suite_has_real_recorded_trial_pairs(self) -> None:
        suite = json.loads((REPO_ROOT / ".p2p" / "evals" / "suite.json").read_text(encoding="utf-8"))
        self.assertEqual(p2p_eval.validate(suite), [])
        self.assertEqual(
            [len(case["baseline_runs"]) for case in suite["cases"]],
            [2] * len(suite["cases"]),
        )
        self.assertEqual(
            [len(case["p2p_runs"]) for case in suite["cases"]],
            [2] * len(suite["cases"]),
        )
        failures, summary = p2p_eval.gate(suite, REPO_ROOT / ".p2p" / "evals" / "suite.json")
        self.assertEqual(failures, [])
        self.assertEqual(summary["completed_case_pairs"], 5)
        self.assertEqual(summary["p2p_pass_rate"], 1.0)
        self.assertEqual(summary["delta"], 0.0)


if __name__ == "__main__":
    unittest.main()
