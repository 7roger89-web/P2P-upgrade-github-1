from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import p2p_workflow  # noqa: E402


class P2PWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture_root = REPO_ROOT / "tests" / "fixtures"
        self.package_root = REPO_ROOT

    def test_goal_contract_is_bounded_and_selects_small_team(self) -> None:
        with tempfile.TemporaryDirectory(prefix="p2p-goal-") as raw:
            project = Path(raw)
            (project / "app.py").write_text("READY_FOR_DEMO = True\n", encoding="utf-8")
            inspection = p2p_workflow.inspect_project(project, "Build and finish this small application", str(self.package_root))
            contract = p2p_workflow.build_goal_contract(project, "Build and finish this small application", inspection, {})
            self.assertGreaterEqual(len(contract["completion_criteria"]), 4)
            self.assertIn("PASS", contract["stop_conditions"])
            self.assertIn("BLOCKED", contract["stop_conditions"])
            self.assertIn("REJECT", contract["stop_conditions"])
            self.assertLessEqual(contract["agent_selection"]["quorum_size"], 2)
            self.assertFalse(contract["agent_selection"]["full_quorum_required"])

    def test_explicit_full_quorum_is_not_lowered(self) -> None:
        selection = p2p_workflow.select_agents("Run a full quorum with 8 agents for certification", {}, {})
        self.assertEqual(selection["selected_agents"], list(p2p_workflow.AGENTS))
        self.assertTrue(selection["full_quorum_required"])
        self.assertTrue(selection["explicit_requirement"])

    def test_eval_helper_resolution_uses_project_eval_v2_contract(self) -> None:
        candidates = p2p_workflow.eval_helper_candidates(self.package_root, str(self.package_root))
        self.assertEqual(candidates[0], self.package_root / "scripts" / "p2p_eval.py")
        self.assertNotIn(self.package_root / ".p2p" / "system" / "scripts" / "p2p_eval.py", candidates)
        self.assertTrue(p2p_workflow.helper_supports_project_eval(candidates[0]))

    def test_transient_helper_paths_are_not_implicit_candidates(self) -> None:
        self.assertTrue(p2p_workflow.helper_path_is_transient(self.package_root / ".tmp" / "p2p_eval.py"))
        self.assertTrue(p2p_workflow.helper_path_is_transient(self.package_root / "quarantine" / "p2p_eval.py"))
        self.assertFalse(p2p_workflow.helper_path_is_transient(self.package_root / "scripts" / "p2p_eval.py"))

    def test_installed_root_does_not_fall_back_to_ancestor_package(self) -> None:
        fixture_parent = self.package_root / ".tmp"
        fixture_parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=fixture_parent, prefix="p2p-helper-resolution-") as raw:
            installed = Path(raw)
            helper_dir = installed / ".p2p" / "system" / "scripts"
            helper_dir.mkdir(parents=True)
            canonical_helper = helper_dir / "p2p_eval.py"
            shutil.copy2(self.package_root / "scripts" / "p2p_eval.py", canonical_helper)
            self.assertEqual(p2p_workflow.eval_helper_candidates(installed), [canonical_helper.resolve()])
            shutil.copy2(self.package_root / ".p2p" / "system" / "scripts" / "p2p_eval.py", canonical_helper)
            self.assertEqual(p2p_workflow.eval_helper_candidates(installed), [])

    def test_new_project_bootstraps_and_passes_safe_acceptance_run(self) -> None:
        with tempfile.TemporaryDirectory(prefix="p2p-new-") as raw:
            project = Path(raw)
            source = self.fixture_root / "new-project"
            for source_file in source.iterdir():
                if not source_file.is_file():
                    continue
                (project / source_file.name).write_bytes(source_file.read_bytes())
            result = p2p_workflow.run_workflow(
                project,
                "Build and finish this small application and make sure it is ready.",
                package_hint=str(self.package_root),
                acceptance=True,
            )
            self.assertEqual(result["status"], "PASS")
            self.assertTrue((project / ".p2p" / "project-profile.json").is_file())
            self.assertTrue((project / ".p2p" / "project-policy.json").is_file())
            self.assertTrue((project / ".p2p" / "evals" / "suite.json").is_file())
            suite = json.loads((project / ".p2p" / "evals" / "suite.json").read_text(encoding="utf-8"))
            self.assertEqual({case["test_type"] for case in suite["cases"]}, {"positive", "negative", "regression", "completion", "reuse"})
            self.assertLessEqual(result["quorum_size"], 2)
            self.assertFalse(result["full_quorum_used"])
            self.assertTrue((project / ".p2p" / "state" / "execution-ledger.jsonl").is_file())
            self.assertTrue((project / ".p2p" / "state" / "project-status.json").is_file())

    def test_existing_project_reuses_unchanged_evidence_after_scoped_change(self) -> None:
        with tempfile.TemporaryDirectory(prefix="p2p-existing-") as raw:
            project = Path(raw)
            source = self.fixture_root / "existing-project"
            for source_file in source.iterdir():
                if not source_file.is_file():
                    continue
                (project / source_file.name).write_bytes(source_file.read_bytes())
            first = p2p_workflow.run_workflow(project, "Prepare this small application for a bounded baseline.", package_hint=str(self.package_root), acceptance=True)
            self.assertEqual(first["status"], "PASS")
            p2p_workflow.seed_synthetic_evidence(project)
            app = project / "app.py"
            app.write_text(app.read_text(encoding="utf-8").replace("Hello from the baseline", "Hello from the scoped update"), encoding="utf-8")
            second = p2p_workflow.run_workflow(project, "Update the small application's greeting and finish this scoped change.", package_hint=str(self.package_root), acceptance=True)
            self.assertEqual(second["status"], "PASS")
            self.assertEqual(second["changed_files"], ["app.py"])
            self.assertTrue(set(("package_doctor", "sandbox_probe", "eight_agent_runtime_proof", "project_eval", "drift_gate")) <= set(second["reused_controls"]))
            self.assertIn("project_wide_audit", second["rerun_controls"])
            self.assertNotIn("package_doctor", second["rerun_controls"])
            self.assertNotIn("drift_gate", second["rerun_controls"])
            self.assertEqual(set(second["safe_update_flow"]["verification"]["run_only"]), {"goal_completion", "project_wide_audit"})
            self.assertLess(second["quorum_size"], 8)
            self.assertFalse(second["full_quorum_used"])
            self.assertIn("no optional work started", second["stop_reason"])
            resumed = p2p_workflow.plan_workflow(project, "Update the small application's greeting and finish this scoped change.", str(self.package_root))
            self.assertEqual(resumed["changed_files"], [])
            self.assertIn("project_eval", resumed["evidence_plan"]["reused_controls"])


if __name__ == "__main__":
    unittest.main()
