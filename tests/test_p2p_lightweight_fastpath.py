from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import p2p_workflow  # noqa: E402


class P2PLightweightFastpathTests(unittest.TestCase):
    def _requirement(self, request: str) -> dict[str, object]:
        return p2p_workflow.derive_orchestration_requirement(
            request,
            {"project_root": str(REPO_ROOT)},
            package_hint=str(REPO_ROOT),
        )

    def _selection(self, request: str, requirement: dict[str, object]) -> dict[str, object]:
        return p2p_workflow.select_agents(
            request,
            {"project_root": str(REPO_ROOT)},
            {},
            requirement,
        )

    def test_prompt_composition_uses_c18_direct_minimal_route(self) -> None:
        request = "Write a precise Arena Agent prompt to improve the Three.js camera."
        requirement = self._requirement(request)
        selection = self._selection(request, requirement)

        self.assertEqual(p2p_workflow.classify_work_type(request), "AI-BOUND")
        self.assertEqual(p2p_workflow.classify_goal_eligibility(request)["classification"], "DIRECT TASK")
        self.assertEqual(requirement["profile"]["task_kind"], "PROMPT_COMPOSITION")
        self.assertEqual(requirement["worker_strategy"], "DIRECT")
        self.assertEqual(requirement["context_class"], "MINIMAL")
        self.assertEqual(requirement["reasoning_class"], "LOW")
        self.assertEqual(requirement["verification_class"], "DETERMINISTIC")
        self.assertEqual(selection["selected_agents"], [])
        self.assertEqual(selection["quorum_size"], 0)
        self.assertFalse(selection["full_quorum_required"])

    def test_read_only_transformation_uses_same_minimum_route(self) -> None:
        request = "Summarize this session report into five actionable points."
        requirement = self._requirement(request)
        selection = self._selection(request, requirement)

        self.assertEqual(requirement["profile"]["task_kind"], "READ_ONLY_TRANSFORMATION")
        self.assertEqual(requirement["worker_strategy"], "DIRECT")
        self.assertEqual(requirement["context_class"], "MINIMAL")
        self.assertEqual(requirement["verification_class"], "DETERMINISTIC")
        self.assertEqual(selection["quorum_size"], 0)

    def test_local_implementation_uses_one_existing_worker(self) -> None:
        request = "Fix this isolated combat cooldown bug and run focused tests."
        requirement = self._requirement(request)
        selection = self._selection(request, requirement)

        self.assertEqual(requirement["profile"]["task_kind"], "IMPLEMENTATION")
        self.assertEqual(requirement["worker_strategy"], "ONE_WORKER")
        self.assertEqual(requirement["verification_class"], "DETERMINISTIC")
        self.assertEqual(selection["selected_agents"], ["p2p_tecton"])
        self.assertEqual(selection["quorum_size"], 1)
        self.assertFalse(selection["full_quorum_required"])

    def test_system_design_keeps_expanded_architecture_semantics(self) -> None:
        request = "Design the system architecture for this project."
        requirement = self._requirement(request)
        selection = self._selection(request, requirement)

        self.assertEqual(requirement["profile"]["task_kind"], "ARCHITECTURE")
        self.assertEqual(requirement["context_class"], "EXPANDED")
        self.assertEqual(requirement["reasoning_class"], "HIGH")
        self.assertEqual(requirement["worker_strategy"], "ONE_WORKER")
        self.assertEqual(selection["selected_agents"], ["p2p_architecton"])

    def test_subsystem_design_is_not_downgraded_to_low_reasoning(self) -> None:
        requirement = self._requirement("Design a new combat subsystem for the game.")

        self.assertEqual(requirement["profile"]["task_kind"], "ARCHITECTURE")
        self.assertEqual(requirement["context_class"], "EXPANDED")
        self.assertEqual(requirement["reasoning_class"], "HIGH")
        self.assertEqual(requirement["verification_class"], "STANDARD")

    def test_two_worker_requirement_uses_existing_roles_without_full_quorum(self) -> None:
        requirement = self._requirement("Implement two independent local checks with focused tests.")
        profile = dict(requirement["profile"])
        profile.update(
            {
                "task_size": "SMALL",
                "dependency_complexity": "NONE",
                "independent_ready_pair": True,
                "parallel_economy_passes": True,
                "material_worker_value": True,
            }
        )
        two_worker_requirement = p2p_workflow.orchestration_api(REPO_ROOT, str(REPO_ROOT)).derive_requirement(profile)
        selection = self._selection("Implement two independent local checks with focused tests.", two_worker_requirement)

        self.assertEqual(two_worker_requirement["worker_strategy"], "TWO_WORKERS")
        self.assertEqual(selection["selected_agents"], ["p2p_tecton", "p2p_axiom"])
        self.assertEqual(selection["quorum_size"], 2)
        self.assertFalse(selection["full_quorum_required"])

    def test_high_impact_architecture_remains_owner_blocked(self) -> None:
        request = "Design a production architecture and prepare deployment with owner approval."
        requirement = self._requirement(request)
        selection = self._selection(request, requirement)

        self.assertEqual(requirement["verification_class"], "HIGH_RISK")
        self.assertEqual(requirement["worker_strategy"], "BLOCKED")
        self.assertEqual(requirement["status"], "BLOCKED")
        self.assertEqual(selection["selected_agents"], [])
        self.assertEqual(selection["quorum_size"], 0)

    def test_authoritative_architecture_replacement_remains_high_impact(self) -> None:
        requirement = self._requirement("Replace the authoritative world-simulation architecture.")

        self.assertEqual(requirement["profile"]["task_kind"], "ARCHITECTURE")
        self.assertEqual(requirement["profile"]["owner_gate"], "REQUIRED")
        self.assertEqual(requirement["verification_class"], "HIGH_RISK")
        self.assertEqual(requirement["worker_strategy"], "BLOCKED")

    def test_upstream_integration_remains_owner_and_network_blocked(self) -> None:
        request = "Integrate the P2P upstream GitHub repository."
        requirement = self._requirement(request)
        selection = self._selection(request, requirement)

        self.assertTrue(requirement["profile"]["network_or_secret"])
        self.assertEqual(requirement["profile"]["owner_gate"], "REQUIRED")
        self.assertEqual(requirement["verification_class"], "HIGH_RISK")
        self.assertEqual(requirement["worker_strategy"], "BLOCKED")
        self.assertEqual(selection["selected_agents"], [])

    def test_explicit_full_quorum_is_not_lowered_by_c18_requirement(self) -> None:
        request = "Run a full quorum with 8 agents for certification."
        requirement = self._requirement(request)
        selection = self._selection(request, requirement)

        self.assertEqual(selection["selected_agents"], list(p2p_workflow.AGENTS))
        self.assertEqual(selection["quorum_size"], 8)
        self.assertTrue(selection["full_quorum_required"])
        self.assertTrue(selection["explicit_requirement"])

    def test_goal_contract_persists_c18_requirement_and_direct_zero_worker_guard(self) -> None:
        request = "Write a precise prompt for the local camera behavior."
        temp_parent = REPO_ROOT / ".tmp"
        temp_parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=temp_parent, prefix="fastpath-03-contract-") as raw:
            contract = p2p_workflow.build_goal_contract(
                Path(raw),
                request,
                {"project_type": "fixture", "project_root": raw},
                {},
                package_hint=str(REPO_ROOT),
            )

        self.assertEqual(contract["orchestration_requirement"]["worker_strategy"], "DIRECT")
        self.assertEqual(contract["context_class"], "MINIMAL")
        self.assertEqual(contract["agent_selection"]["quorum_size"], 0)
        self.assertEqual(contract["guards"]["max_agent_calls"], 0)
        self.assertEqual(contract["goal_eligibility"]["classification"], "DIRECT TASK")

    def _context_module(self):
        return p2p_workflow.context_api(REPO_ROOT, str(REPO_ROOT))

    def _fixture_project(self, prefix: str):
        temp_parent = REPO_ROOT / ".tmp"
        temp_parent.mkdir(parents=True, exist_ok=True)
        temporary = tempfile.TemporaryDirectory(dir=temp_parent, prefix=prefix)
        project = Path(temporary.name)
        shutil.copytree(REPO_ROOT / "tests" / "fixtures" / "new-project", project, dirs_exist_ok=True)
        return temporary, project

    @staticmethod
    def _source(source_id: str, role: str | None = None, required: bool = True) -> dict[str, object]:
        binding: dict[str, object] = {
            "source_id": source_id,
            "source_hash": "a" * 64,
            "source_class": "AUTHORITATIVE_PROJECT_SOURCE",
            "required": required,
        }
        if role:
            binding["retrieval_role"] = role
        return binding

    def test_c19_uses_minimal_context_for_lightweight_task_without_escalation(self) -> None:
        requirement = self._requirement("Write a precise prompt for the local camera behavior.")
        contract = {
            "objective": "write a precise prompt",
            "orchestration_requirement": requirement,
            "task_profile": requirement["profile"],
            "context_retrieval": {"context_class": "MINIMAL"},
        }
        result = p2p_workflow.task_targeted_context_metadata(
            self._context_module(),
            contract,
            [
                self._source("goal-contract"),
                self._source("project-status", required=False),
                self._source("project-eval", "DEPENDENCY_OUTPUTS", required=False),
            ],
        )

        self.assertEqual(result["status"], "SUFFICIENT")
        self.assertEqual(result["context_class"], "MINIMAL")
        self.assertEqual(result["escalation_count"], 0)
        self.assertEqual(result["source_selection"]["required_source_ids"], ["goal-contract"])
        self.assertEqual(result["source_selection"]["selected_source_count"], 1)

    def test_c19_missing_required_lightweight_source_fails_closed(self) -> None:
        requirement = self._requirement("Write a precise prompt for the local camera behavior.")
        contract = {
            "objective": "write a precise prompt",
            "orchestration_requirement": requirement,
            "task_profile": requirement["profile"],
            "context_retrieval": {"context_class": "MINIMAL"},
        }
        result = p2p_workflow.task_targeted_context_metadata(
            self._context_module(),
            contract,
            [self._source("project-status", required=False)],
        )

        self.assertIn(result["status"], {"INSUFFICIENT", "BLOCKED"})
        self.assertIn("goal-contract", result["source_selection"]["required_source_ids"])
        self.assertNotIn("goal-contract", result.get("selected_source_ids", []))
        self.assertEqual(result["workflow_escalation"]["max_attempts"], 1)

    def test_c19_escalates_exactly_once_when_next_tier_covers_obligation(self) -> None:
        contract = {
            "objective": "bounded context test",
            "task_profile": {"task_kind": "CUSTOM", "context_escalation_available": True},
            "context_retrieval": {"context_class": "MINIMAL"},
        }
        result = p2p_workflow.task_targeted_context_metadata(
            self._context_module(),
            contract,
            [
                self._source("goal-contract"),
                self._source("project-eval", "DEPENDENCY_OUTPUTS"),
            ],
        )

        self.assertEqual(result["initial_context_class"], "MINIMAL")
        self.assertEqual(result["context_class"], "STANDARD")
        self.assertEqual(result["status"], "SUFFICIENT")
        self.assertEqual(result["escalation_count"], 1)
        self.assertEqual(result["workflow_escalation"]["max_attempts"], 1)
        self.assertEqual(result["source_selection"]["selected_source_count"], 2)

    def test_c19_ceiling_stays_insufficient_after_one_bounded_escalation(self) -> None:
        contract = {
            "objective": "bounded context ceiling test",
            "task_profile": {"task_kind": "CUSTOM", "context_escalation_available": True},
            "context_retrieval": {"context_class": "MINIMAL"},
        }
        result = p2p_workflow.task_targeted_context_metadata(
            self._context_module(),
            contract,
            [self._source("unmapped-target", "TARGETED_SOURCE")],
        )

        self.assertEqual(result["status"], "INSUFFICIENT")
        self.assertEqual(result["escalation_count"], 1)
        self.assertEqual(result["workflow_escalation"]["final_status"], "INSUFFICIENT")
        self.assertEqual(result["workflow_escalation"]["max_attempts"], 1)
        self.assertEqual(result["next_context_class"], "EXPANDED")

    def test_workflow_result_and_receipt_expose_prompt_fast_path(self) -> None:
        temporary, project = self._fixture_project("fastpath-03-workflow-prompt-")
        try:
            result = p2p_workflow.run_workflow(
                project,
                "Write a precise Arena Agent prompt to improve the Three.js camera.",
                package_hint=str(REPO_ROOT),
                acceptance=True,
            )
            self.assertEqual(result["status"], "PASS")
            self.assertEqual(result["context_mode"], "CONTEXT_EFFICIENT_V1")
            self.assertEqual(result["worker_strategy"], "DIRECT")
            self.assertEqual(result["worker_count"], 0)
            self.assertEqual(result["requested_context_class"], "MINIMAL")
            self.assertEqual(result["final_context_class"], "MINIMAL")
            self.assertEqual(result["context_sufficiency_status"], "SUFFICIENT")
            self.assertEqual(result["context_source_count"], 1)
            self.assertEqual(result["context_escalation_count"], 0)
            self.assertFalse(result["council_entered"])
            self.assertFalse(result["quorum_entered"])
            self.assertTrue(result["verification_surface"]["proportional_route"])
            self.assertFalse(result["verification_surface"]["broad_controls_entered"])
            manifest = json.loads((project / result["context_manifest_pointer"]).read_text(encoding="utf-8"))
            self.assertEqual(manifest["task_targeted_context"]["status"], "SUFFICIENT")
            self.assertEqual(manifest["task_targeted_context"]["escalation_count"], 0)
            self.assertTrue(manifest["excluded_or_deferred_items"])
            events = [
                json.loads(line)
                for line in (project / result["ledger"]).read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertTrue(any(event.get("orchestration", {}).get("worker_strategy") == "DIRECT" for event in events))
        finally:
            temporary.cleanup()

    def test_workflow_uses_one_existing_worker_for_local_implementation(self) -> None:
        temporary, project = self._fixture_project("fastpath-03-workflow-implementation-")
        try:
            result = p2p_workflow.run_workflow(
                project,
                "Fix this isolated combat cooldown bug and run focused tests.",
                package_hint=str(REPO_ROOT),
                acceptance=True,
            )
            self.assertEqual(result["status"], "PASS")
            self.assertEqual(result["worker_strategy"], "ONE_WORKER")
            self.assertEqual(result["selected_agents"], ["p2p_tecton"])
            self.assertEqual(result["quorum_size"], 1)
            self.assertEqual(result["requested_context_class"], "STANDARD")
            self.assertEqual(result["context_sufficiency_status"], "SUFFICIENT")
            self.assertEqual(result["verification_class"], "DETERMINISTIC")
            self.assertFalse(result["full_quorum_used"])
        finally:
            temporary.cleanup()

    def test_workflow_blocks_high_impact_route_without_owner_bypass(self) -> None:
        temporary, project = self._fixture_project("fastpath-03-workflow-owner-")
        try:
            result = p2p_workflow.run_workflow(
                project,
                "Design a high-impact production architecture and prepare deployment with owner approval.",
                package_hint=str(REPO_ROOT),
                acceptance=True,
            )
            self.assertEqual(result["status"], "BLOCKED")
            self.assertEqual(result["worker_strategy"], "BLOCKED")
            self.assertEqual(result["verification_class"], "HIGH_RISK")
            self.assertEqual(result["selected_agents"], [])
            self.assertIn("Owner", result["decision_required"])
            self.assertFalse(result["council_entered"])
            self.assertFalse(result["quorum_entered"])
            blocked = [item for item in result["criteria"] if item.get("name") == "minimum_sufficient_orchestration"]
            self.assertEqual(blocked[0]["status"], "BLOCKED")
        finally:
            temporary.cleanup()


if __name__ == "__main__":
    unittest.main()
