from __future__ import annotations

import copy
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_ROOT = REPO_ROOT / ".p2p" / "system"
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "p2p-c13-design-intelligence.json"
sys.path.insert(0, str(SYSTEM_ROOT))

from p2p_uiux.design_intelligence import (  # noqa: E402
    DISPOSITIONS,
    RENDER_STATES,
    build_obligation_plan,
    build_task_profile,
    classify_materiality,
    correction_loop,
    design_intelligence_route,
    evaluate_completion,
    load_registry,
    route_design_task,
    validate_registry,
    validate_task_profile,
)
from p2p_uiux.router import classify_request  # noqa: E402


class P2PDesignIntelligenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        cls.registry = load_registry()
        cls.logistics = cls.fixture["synthetic_fixtures"][0]
        cls.consumer = cls.fixture["synthetic_fixtures"][1]

    def test_registry_preserves_upstream_breadth_and_provenance(self) -> None:
        validation = validate_registry(self.registry)
        self.assertTrue(validation["valid"], validation["errors"])
        self.assertEqual(validation["faculty_count"], 174)
        self.assertEqual(validation["kernel_count"], 13)
        self.assertEqual(self.registry["provenance"]["upstream_license"], "MIT")
        self.assertEqual(self.registry["provenance"]["upstream_revision"], "46780cdd58e41bea8338b2d27269d339c95e28e7")
        self.assertEqual(len(self.registry["provenance"]["registry_sha256"]), 64)

    def test_registry_lock_rejects_tampered_provenance_snapshot(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT / ".tmp", prefix="p2p-c14-registry-lock-") as raw:
            root = Path(raw)
            registry_path = root / "nui_registry.json"
            shutil.copy2(SYSTEM_ROOT / "p2p_uiux" / "nui_registry.json", registry_path)
            shutil.copy2(SYSTEM_ROOT / "p2p_uiux" / "nui_registry.lock.json", root / "nui_registry.lock.json")
            payload = json.loads(registry_path.read_text(encoding="utf-8"))
            payload["provenance"]["upstream_revision"] = "0" * 40
            registry_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "NUI_REGISTRY_FINGERPRINT_MISMATCH"):
                load_registry(registry_path)

    def test_registry_is_graph_valid_and_bodies_are_not_preloaded(self) -> None:
        for skill_id, entry in self.registry["skills"].items():
            parent = entry.get("parent")
            self.assertTrue(parent is None or parent in self.registry["skills"], skill_id)
            self.assertEqual(entry["source_state"], "UPSTREAM_PRESERVED")
        result = design_intelligence_route(self.logistics["request"], self.logistics["context"])
        self.assertEqual(result["route"]["registry_faculty_count"], 174)
        self.assertEqual(result["route"]["loaded_faculty_count"], 0)
        self.assertEqual(result["route"]["loaded_faculty_content"], [])
        self.assertLess(result["route"]["activated_count"], 174)

    def test_beginner_request_needs_no_faculty_or_technical_questions(self) -> None:
        result = design_intelligence_route("Làm giao diện này chuyên nghiệp và dễ dùng.")
        self.assertEqual(result["status"], "READY")
        self.assertTrue(result["profile"]["beginner_ready"])
        self.assertEqual(result["profile"]["questions"], [])
        self.assertEqual(result["profile"]["permission_requests"], [])
        self.assertFalse(result["profile"]["recommendations_grant_permissions"])

    def test_materiality_has_reduced_path_for_tiny_local_edit(self) -> None:
        result = classify_materiality("Change the padding on this button.")
        self.assertFalse(result["material"])
        self.assertTrue(result["reduced_path"])
        self.assertIn("full_information_architecture", result["omitted_concerns"])
        route = design_intelligence_route("Change the padding on this button.")
        self.assertEqual(route["status"], "READY")
        self.assertEqual(route["route"]["status"], "REDUCED_PATH")

    def test_profile_mutation_fails_before_routing(self) -> None:
        profile = build_task_profile(self.logistics["request"], self.logistics["context"])
        profile["job"] = "mutated after routing"
        with self.assertRaisesRegex(ValueError, "ROUTING_PROFILE_MISMATCH"):
            route_design_task(profile, self.registry)
        with self.assertRaisesRegex(ValueError, "ROUTING_PROFILE_MISMATCH"):
            validate_task_profile(profile)

    def test_logistics_and_consumer_routes_diverge_from_profile_signals(self) -> None:
        logistics = design_intelligence_route(self.logistics["request"], self.logistics["context"])
        consumer = design_intelligence_route(self.consumer["request"], self.consumer["context"])
        logistics_rules = {item["rule_id"] for item in logistics["route"]["matched_rules"]}
        consumer_rules = {item["rule_id"] for item in consumer["route"]["matched_rules"]}
        self.assertIn("professional-workspace", logistics_rules)
        self.assertIn("consequential-decisions", logistics_rules)
        self.assertNotIn("professional-workspace", consumer_rules)
        self.assertIn("consumer-visual-direction", consumer_rules)
        self.assertIn("game-surface", consumer_rules)
        self.assertNotEqual(logistics["route"]["activated_count"], consumer["route"]["activated_count"])
        logistics_ids = {item["id"] for item in logistics["route"]["activated_faculties"]}
        consumer_ids = {item["id"] for item in consumer["route"]["activated_faculties"]}
        self.assertIn("designing-data-dense-interfaces", logistics_ids)
        self.assertNotIn("designing-data-dense-interfaces", consumer_ids)
        self.assertIn("designing-game-hud-and-menus", consumer_ids)

    def test_dependency_expansion_and_route_provenance_are_complete(self) -> None:
        result = design_intelligence_route(self.logistics["request"], self.logistics["context"])
        route = result["route"]
        activated = {item["id"] for item in route["activated_faculties"]}
        for item in route["activated_faculties"]:
            self.assertTrue(item["parent"] is None or item["parent"] in activated, item["id"])
        provenance = route["route_provenance"]
        self.assertEqual(provenance["profile_fingerprint"], result["profile"]["profile_fingerprint"])
        self.assertEqual(provenance["activated_set"], [item["id"] for item in route["activated_faculties"]])
        self.assertEqual(route["route_fingerprint"], result["route"]["route_fingerprint"])
        self.assertTrue(route["single_router"].endswith("classify_request"))

    def test_dispositions_workspace_and_omissions_are_explicit(self) -> None:
        result = design_intelligence_route(self.logistics["request"], self.logistics["context"])
        route = result["route"]
        self.assertEqual(set(route["dispositions_supported"]), set(DISPOSITIONS))
        self.assertTrue(all(item["disposition"] in DISPOSITIONS for item in route["activated_faculties"]))
        self.assertTrue(route["high_impact_omissions"])
        workspace = route["workspace_completeness"]
        self.assertIn(workspace["dense_data"]["disposition"], {"REQUIRED", "EXPECTED"})
        self.assertIn(workspace["search_commands"]["disposition"], {"REQUIRED", "EXPECTED"})
        self.assertFalse(route["optional_specialist"]["activated"])
        self.assertEqual(route["optional_specialist"]["id"], "p2p_aesthetica")

    def test_render_preflight_is_honest_for_all_states(self) -> None:
        for state in RENDER_STATES:
            context = copy.deepcopy(self.consumer["context"])
            context["runtime_capabilities"] = {"render_state": state}
            result = design_intelligence_route(self.consumer["request"], context)
            plan = result["plan"]
            self.assertEqual(plan["render_preflight"]["state"], state)
            self.assertFalse(plan["render_preflight"]["invented_capture_allowed"])
            if state == "RENDER_AVAILABLE":
                self.assertEqual(plan["ui_done"]["status"], "UNKNOWN")
            elif state in {"RENDER_UNAVAILABLE", "RENDER_BLOCKED_PERMISSION"}:
                self.assertEqual(plan["ui_done"]["status"], "BLOCKED")
            else:
                self.assertEqual(plan["ui_done"]["status"], "UNKNOWN")

    def test_completion_requires_render_and_independent_critique(self) -> None:
        context = copy.deepcopy(self.consumer["context"])
        context["runtime_capabilities"] = {"render_state": "RENDER_AVAILABLE"}
        result = design_intelligence_route(self.consumer["request"], context)
        plan = result["plan"]
        incomplete = evaluate_completion(plan, {})
        self.assertEqual(incomplete["status"], "UNKNOWN")
        self.assertIn("rendered_ui", incomplete["missing_evidence"])
        self.assertNotIn("beauty_score", incomplete)
        evidence = {item: {"evidence_ref": item} for item in plan["required_evidence"]}
        evidence["generator"] = "generator-a"
        evidence["independent_critique"] = {"producer": "critic-b", "findings": []}
        complete = evaluate_completion(plan, evidence)
        self.assertEqual(complete["status"], "PASS")
        bad = dict(evidence)
        bad["independent_critique"] = {"producer": "generator-a", "findings": []}
        self.assertEqual(evaluate_completion(plan, bad)["status"], "BLOCKED")

    def test_correction_loop_is_bounded(self) -> None:
        result = design_intelligence_route(self.consumer["request"], self.consumer["context"])
        plan = result["plan"]
        self.assertEqual(correction_loop(plan, [{"dimension": "hierarchy"}], 0)["status"], "CORRECT")
        self.assertEqual(correction_loop(plan, [{"dimension": "hierarchy"}], 2)["reason"], "CORRECTION_BUDGET_EXHAUSTED")
        self.assertEqual(plan["correction_loop"]["max_iterations"], 2)

    def test_c10_c11_c12_projection_and_permission_boundary(self) -> None:
        result = design_intelligence_route(self.logistics["request"], self.logistics["context"])
        plan = result["plan"]
        self.assertEqual(plan["c10_decision_trace"]["authority"], "C10")
        self.assertTrue(plan["c10_decision_trace"]["reuse_existing_trace"])
        self.assertFalse(plan["c10_decision_trace"]["second_trace"])
        self.assertEqual(plan["c11_task_projection"]["authority"], "C11")
        self.assertEqual(plan["c12_execution_projection"]["authority"], "C12")
        self.assertEqual(tuple(plan["c12_execution_projection"]["state_path"]), ("READY", "PREFLIGHT", "ACTIVE", "EXECUTE", "VERIFY", "EVIDENCE", "DONE"))
        self.assertFalse(plan["c12_execution_projection"]["execute"])
        self.assertEqual(plan["permission_policy"]["permission_requests"], [])
        self.assertFalse(plan["permission_policy"]["recommendations_grant_permissions"])
        self.assertEqual(result["route"]["agent_selection"], [])

    def test_fallback_is_truthful_when_nui_registry_is_unavailable(self) -> None:
        result = design_intelligence_route(
            "Design a new interface for a small app.",
            {},
            registry_source=REPO_ROOT / ".tmp" / "c13-missing-registry.json",
        )
        self.assertEqual(result["status"], "NUI_UNAVAILABLE")
        self.assertEqual(result["design_mode"], "P2P_NATIVE_DESIGN")
        self.assertEqual(result["fallback"], "P2P_NATIVE_DESIGN")
        self.assertEqual(result["permission_requests"], [])

    def test_existing_single_router_exposes_additive_design_projection(self) -> None:
        result = classify_request("Design a new logistics dashboard with dense tables and exception review.")
        self.assertTrue(result["use_skill"])
        self.assertEqual(result["design_intelligence"]["status"], "READY")
        self.assertEqual(result["design_intelligence"]["design_mode"], "NUI_BACKED_DESIGN")
        self.assertEqual(result["adaptive_quorum"]["canonical_denominator"], 8)
        self.assertNotIn("router-agent", json.dumps(result))

    def test_focused_eval_inventory_is_present(self) -> None:
        self.assertEqual(self.fixture["design_cases"], [f"D{i}" for i in range(1, 13)])
        self.assertEqual(self.fixture["structural_cases"], [f"F{i}" for i in range(1, 27)])


if __name__ == "__main__":
    unittest.main()
