from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]

import sys

sys.path.insert(0, str(REPO_ROOT / "scripts"))

import p2p_workflow  # noqa: E402


class P2PGoalSubsystemTests(unittest.TestCase):
    def test_vague_request_is_plan_first(self) -> None:
        result = p2p_workflow.classify_goal_eligibility("Optimize this app a little.")
        self.assertEqual(result["classification"], "PLAN FIRST")
        self.assertTrue(result["bounded_interpretation_required"])

    def test_clear_long_running_request_is_goal(self) -> None:
        result = p2p_workflow.classify_goal_eligibility(
            "Migrate this project to the target stack while preserving behavior and stop only when build and required regression tests pass."
        )
        self.assertEqual(result["classification"], "GOAL")
        self.assertTrue(result["goal_required"])

    def test_open_ended_backlog_is_bounded_before_execution(self) -> None:
        result = p2p_workflow.classify_goal_eligibility("Fix everything you can find and keep improving the project.")
        self.assertEqual(result["classification"], "PLAN FIRST")
        self.assertIn("smallest", result["next_action"])

    def test_unrelated_discovery_is_out_of_scope(self) -> None:
        self.assertEqual(p2p_workflow.classify_work_item("unrelated UI improvement", related=False), "OUT OF SCOPE")

    def test_failed_primary_allows_only_one_alternative(self) -> None:
        contract = {"goal_id": "goal-test", "work_type": "AI-BOUND", "exploration_policy": p2p_workflow.exploration_policy_for("AI-BOUND")}
        first = p2p_workflow.register_approach_result(contract, "primary", "FAILED", "primary failed", "lowest-risk alternative")
        second = p2p_workflow.register_approach_result(first["contract"], "alternative", "FAILED", "alternative failed")
        self.assertEqual(first["status"], "ALTERNATIVE_ALLOWED")
        self.assertEqual(second["status"], "BLOCKED")
        self.assertEqual(len(second["failed_approaches"]), 2)

    def test_failed_approach_is_persisted_in_execution_ledger(self) -> None:
        with tempfile.TemporaryDirectory(prefix="p2p-goal-approach-") as raw:
            project = Path(raw)
            source = REPO_ROOT / "tests" / "fixtures" / "new-project"
            for source_file in source.iterdir():
                if not source_file.is_file():
                    continue
                (project / source_file.name).write_bytes(source_file.read_bytes())
            request = "Build and finish this small application and make sure it is ready."
            inspection = p2p_workflow.inspect_project(project, request, str(REPO_ROOT))
            contract = p2p_workflow.build_goal_contract(project, request, inspection, {})
            p2p_workflow.write_goal(project, contract)
            p2p_workflow.bootstrap_project(project, inspection, contract, str(REPO_ROOT))
            result = p2p_workflow.record_approach_result(project, "primary", "FAILED", "primary lane failed in the deterministic check", "one alternative")
            self.assertEqual(result["status"], "ALTERNATIVE_ALLOWED")
            ledger = (project / ".p2p" / "state" / "execution-ledger.jsonl").read_text(encoding="utf-8")
            self.assertIn('"event": "approach_result"', ledger)
            self.assertIn("primary lane failed in the deterministic check", ledger)

    def test_tool_bound_work_is_not_treated_as_model_waiting(self) -> None:
        self.assertEqual(p2p_workflow.classify_work_type("Run the deterministic build script and wait for completion."), "TOOL-BOUND")

    def test_goal_linter_requires_oracle_for_every_mandatory_criterion(self) -> None:
        with tempfile.TemporaryDirectory(prefix="p2p-goal-linter-") as raw:
            project = Path(raw)
            inspection = p2p_workflow.inspect_project(project, "Migrate this project while preserving behavior", str(REPO_ROOT))
            contract = p2p_workflow.build_goal_contract(project, "Migrate this project while preserving behavior", inspection, {})
            self.assertEqual(contract["goal_linter"]["status"], "PASS")
            invalid = copy.deepcopy(contract)
            del invalid["completion_criteria"][0]["verification_oracle"]
            self.assertEqual(p2p_workflow.lint_goal_contract(invalid)["status"], "BLOCKED")

    def test_verified_evidence_reuse_and_pass_stop(self) -> None:
        self.assertTrue(p2p_workflow.can_reuse_pass_evidence("PASS", True, False))
        self.assertFalse(p2p_workflow.can_reuse_pass_evidence("PASS", False, False))
        result = p2p_workflow.register_approach_result(
            {"work_type": "TOOL-BOUND", "exploration_policy": p2p_workflow.exploration_policy_for("TOOL-BOUND")},
            "primary",
            "PASS",
            "mandatory criteria satisfied",
        )
        self.assertEqual(result["status"], "STOP_IF_MANDATORY_PASS")

    def test_real_blocker_returns_exactly_one_decision(self) -> None:
        decision = p2p_workflow.one_blocked_decision(["Choose the business retention period.", "Choose a color."])
        self.assertEqual(decision, "Choose the business retention period.")

    def test_mutation_and_separate_goal_are_not_silently_absorbed(self) -> None:
        update = p2p_workflow.classify_goal_update("Fix the login timeout.", "Also redesign the unrelated UI")
        self.assertEqual(update["classification"], "NEW OBJECTIVE")
        self.assertFalse(update["silent_expand"])
        self.assertEqual(p2p_workflow.classify_goal_eligibility("Fix the API and redesign the unrelated UI")["classification"], "SEPARATE GOALS")

    def test_contract_and_capsule_persist_goal_discipline_state(self) -> None:
        with tempfile.TemporaryDirectory(prefix="p2p-goal-capsule-") as raw:
            project = Path(raw)
            source = REPO_ROOT / "tests" / "fixtures" / "new-project"
            for source_file in source.iterdir():
                if not source_file.is_file():
                    continue
                (project / source_file.name).write_bytes(source_file.read_bytes())
            result = p2p_workflow.run_workflow(
                project,
                "Build and finish this small application and make sure it is ready.",
                package_hint=str(REPO_ROOT),
                acceptance=True,
            )
            self.assertEqual(result["status"], "PASS")
            self.assertEqual(
                p2p_workflow.record_approach_result(project, "primary", "FAILED", "late optional idea" )["status"],
                "PASS_STOPPED",
            )
            contract = json.loads((project / ".p2p" / "state" / "goal-contract.json").read_text(encoding="utf-8"))
            self.assertEqual(contract["goal_linter"]["status"], "PASS")
            self.assertIn("authoritative_project_evidence", contract["context"])
            self.assertTrue(contract["protected_decisions"])
            self.assertIn("fingerprints", contract["evidence_reuse_rule"])
            self.assertEqual(contract["work_item_classes"][0]["class"], "MANDATORY FOR GOAL")
            capsule_paths = list((project / ".p2p" / "state" / "capsules").glob("*.md"))
            self.assertEqual(len(capsule_paths), 1)
            capsule = capsule_paths[0].read_text(encoding="utf-8")
            for marker in ("Eligibility:", "Work type:", "Mandatory criteria:", "PASS criteria:", "Reusable evidence:", "Failed approaches:", "OUT-OF-SCOPE / BACKLOG:"):
                self.assertIn(marker, capsule)

    def test_all_goal_acceptance_cases_are_pass(self) -> None:
        result = p2p_workflow.goal_acceptance_cases()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(len(result["cases"]), 10)
        self.assertTrue(all(case["pass"] for case in result["cases"].values()))


if __name__ == "__main__":
    unittest.main()
