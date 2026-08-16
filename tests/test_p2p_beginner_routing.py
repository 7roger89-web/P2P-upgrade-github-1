from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_ROOT = REPO_ROOT / ".p2p" / "system"
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "p2p-beginner-routing.json"
FIRST_DECISION_FIXTURE = REPO_ROOT / "tests" / "fixtures" / "p2p-first-decision-routing.json"
FIRST_MATERIAL_FIXTURE = REPO_ROOT / "tests" / "fixtures" / "p2p-first-material-decision-routing.json"
sys.path.insert(0, str(SYSTEM_ROOT))

from p2p_uiux.router import classify_request  # noqa: E402


class P2PBeginnerRoutingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        cls.cases = cls.fixture["cases"]
        cls.first_decision_fixture = json.loads(FIRST_DECISION_FIXTURE.read_text(encoding="utf-8"))
        cls.first_decision_cases = cls.first_decision_fixture["cases"]
        cls.first_material_fixture = json.loads(FIRST_MATERIAL_FIXTURE.read_text(encoding="utf-8"))
        cls.first_material_cases = cls.first_material_fixture["cases"]
        cls.coordinator_text = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")
        cls.dispatcher_text = (REPO_ROOT / ".agents" / "skills" / "p2p" / "SKILL.md").read_text(encoding="utf-8")
        cls.idea_text = (REPO_ROOT / ".agents" / "skills" / "p2p-idea" / "SKILL.md").read_text(encoding="utf-8")
        cls.uiux_text = (REPO_ROOT / ".agents" / "skills" / "p2p-uiux" / "SKILL.md").read_text(encoding="utf-8")

    def test_fixture_has_bilingual_a_to_j_coverage(self) -> None:
        self.assertEqual(self.fixture["schema"], "p2p-beginner-routing-fixture/1")
        self.assertGreaterEqual(len(self.cases), 30)
        self.assertEqual({case["id"][0] for case in self.cases}, set("ABCDEFGHIJ"))
        self.assertEqual({case["language"] for case in self.cases}, {"vi", "en"})
        self.assertEqual(len({case["id"] for case in self.cases}), len(self.cases))

    def test_user_examples_contain_no_internal_route_names(self) -> None:
        forbidden = ("p2p-", "aesthetica", "capability", "canonical", "quorum", "router-agent")
        for case in self.cases:
            request = case["request"].lower()
            self.assertFalse(any(token in request for token in forbidden), case["id"])

    def test_dispatcher_contract_states_outcome_precedence(self) -> None:
        self.assertIn("Beginner wording or uncertainty does not choose the route.", self.coordinator_text)
        self.assertIn("a concrete existing or proposed interface outcome routes to", self.coordinator_text)
        self.assertIn("an undeveloped product or feature direction routes to", self.coordinator_text)
        self.assertIn("Do not begin an IDEA plan and self-correct later", self.coordinator_text)
        self.assertNotIn("For a beginner with a rough idea, prefer `$p2p-idea`", self.coordinator_text)
        self.assertIn("Primary-intent precedence", self.dispatcher_text)
        self.assertIn("requested outcome", self.dispatcher_text)
        self.assertIn("concrete interface outcome", self.dispatcher_text)
        self.assertIn("Undeveloped product/feature idea with no concrete interface outcome", self.dispatcher_text)
        self.assertIn("Concrete interface, usability, accessibility, responsive, or visual outcome", self.dispatcher_text)
        self.assertIn("Do not use phrase or keyword matching as the decision authority", self.dispatcher_text)
        self.assertIn("First material planning decision", self.dispatcher_text)
        self.assertIn("INITIAL_PLANNING_CLASSIFICATION", self.dispatcher_text)
        self.assertIn("FINAL_ROUTING_CLASSIFICATION", self.dispatcher_text)
        self.assertIn("Before selecting or loading any specialist skill", self.dispatcher_text)
        self.assertIn("This is not a generic beginner-uncertainty", self.idea_text)
        self.assertIn("Entry gate", self.idea_text)
        self.assertIn("INITIAL_PLANNING_CLASSIFICATION: IDEA", self.idea_text)
        self.assertIn("First-decision handoff", self.uiux_text)
        self.assertIn("INITIAL_PLANNING_CLASSIFICATION: UIUX", self.uiux_text)
        self.assertIn("Boundary with UI/UX work", self.idea_text)
        self.assertIn("p2p-uiux", self.idea_text)
        self.assertIn("Routing boundary", self.uiux_text)
        self.assertIn("Do not use keyword-only routing", self.uiux_text)
        self.assertIn("Native specialist handoff", self.uiux_text)
        self.assertIn("current native coordinator", self.uiux_text)
        self.assertIn("exact", self.uiux_text)

    def test_first_decision_records_initial_and_final_classifications_separately(self) -> None:
        self.assertEqual(self.first_decision_fixture["schema"], "p2p-first-decision-routing-fixture/1")
        self.assertEqual(
            self.first_decision_fixture["classification_fields"],
            ["INITIAL_PLANNING_CLASSIFICATION", "FINAL_ROUTING_CLASSIFICATION"],
        )
        self.assertEqual(len(self.first_decision_cases), 10)
        required_categories = {
            "clear_uiux",
            "clear_idea",
            "mixed_uiux_primary",
            "mixed_idea_primary",
            "beginner_uncertain_concrete_uiux",
            "backend",
            "cosmetic",
            "accessibility",
            "responsive",
            "greenfield_visual_direction",
        }
        self.assertEqual({case["category"] for case in self.first_decision_cases}, required_categories)
        for case in self.first_decision_cases:
            self.assertIn(case["INITIAL_PLANNING_CLASSIFICATION"], {"UIUX", "IDEA", "BACKEND", "COSMETIC_UIUX"}, case["id"])
            self.assertIn(case["FINAL_ROUTING_CLASSIFICATION"], {"UIUX", "IDEA", "MIXED", "BACKEND", "COSMETIC_UIUX"}, case["id"])
            route = classify_request(case["request"], force_profile_available=True)
            if case["category"].startswith("mixed_"):
                self.assertIn(route["scope"], {"UI_UX", "MIXED"}, case["id"])
                if case["category"] == "mixed_uiux_primary":
                    self.assertTrue(route["use_skill"], case["id"])
            else:
                self.assertEqual(route["scope"], case["expected_scope"], case["id"])
                self.assertEqual(route["call_aesthetica"], case["expected_aesthetica"], case["id"])
        for case in self.first_decision_cases:
            if case["category"] in {
                "clear_uiux",
                "beginner_uncertain_concrete_uiux",
                "accessibility",
                "responsive",
                "greenfield_visual_direction",
            }:
                self.assertEqual(case["INITIAL_PLANNING_CLASSIFICATION"], "UIUX", case["id"])
        self.assertEqual(
            [case["INITIAL_PLANNING_CLASSIFICATION"] for case in self.first_decision_cases if case["category"] == "clear_idea"],
            ["IDEA"],
        )

    def test_first_material_decision_has_bilingual_20_plus_matrix(self) -> None:
        self.assertEqual(self.first_material_fixture["schema"], "p2p-first-material-decision-routing-fixture/1")
        self.assertGreaterEqual(len(self.first_material_cases), 20)
        self.assertEqual({case["language"] for case in self.first_material_cases}, {"vi", "en"})
        required_categories = {
            "beginner_uiux",
            "clear_uiux",
            "accessibility",
            "responsive",
            "readability",
            "navigation",
            "genuine_idea",
            "gameplay_ideation",
            "mixed_uiux_primary",
            "mixed_idea_primary",
            "backend_non_ui",
        }
        self.assertTrue(required_categories.issubset({case["category"] for case in self.first_material_cases}))
        for case in self.first_material_cases:
            self.assertIn(case["INITIAL_PLANNING_CLASSIFICATION"], {"UIUX", "IDEA", "BACKEND", "COSMETIC_UIUX"}, case["id"])
            self.assertIn(case["FINAL_ROUTING_CLASSIFICATION"], {"UIUX", "IDEA", "MIXED", "BACKEND", "COSMETIC_UIUX"}, case["id"])
            self.assertFalse(
                case["INITIAL_PLANNING_CLASSIFICATION"] == "IDEA"
                and case["FINAL_ROUTING_CLASSIFICATION"] == "UIUX",
                case["id"],
            )
            route = classify_request(case["request"], force_profile_available=True)
            if case["category"].startswith("mixed_"):
                self.assertIn(route["scope"], {"UI_UX", "MIXED"}, case["id"])
                if case["category"] == "mixed_uiux_primary":
                    self.assertTrue(route["use_skill"], case["id"])
            else:
                self.assertEqual(route["scope"], case["expected_scope"], case["id"])
                self.assertEqual(route["call_aesthetica"], case["expected_aesthetica"], case["id"])

        uiux_categories = {
            "beginner_uiux",
            "clear_uiux",
            "accessibility",
            "responsive",
            "readability",
            "navigation",
        }
        for case in self.first_material_cases:
            if case["category"] in uiux_categories:
                self.assertEqual(case["INITIAL_PLANNING_CLASSIFICATION"], "UIUX", case["id"])
                self.assertEqual(case["FINAL_ROUTING_CLASSIFICATION"], "UIUX", case["id"])
        for case in self.first_material_cases:
            if case["category"] in {"genuine_idea", "gameplay_ideation", "mixed_idea_primary"}:
                self.assertEqual(case["INITIAL_PLANNING_CLASSIFICATION"], "IDEA", case["id"])

    def test_runtime_boundary_and_specialist_restraint(self) -> None:
        for case in self.cases:
            route = classify_request(case["request"], force_profile_available=True)
            primary = case["expected_primary"]
            expected_scope = case["expected_scope"]

            if primary in {"UI_UX", "DIRECT_UI"}:
                self.assertTrue(route["use_skill"], case["id"])
                if expected_scope == "UI_UX":
                    self.assertEqual(route["scope"], "UI_UX", case["id"])
                else:
                    self.assertIn(route["scope"], {"UI_UX", "MIXED"}, case["id"])
                if case["expected_aesthetica"]:
                    self.assertTrue(route["call_aesthetica"], case["id"])
                else:
                    self.assertFalse(route["call_aesthetica"], case["id"])
            elif primary == "TECHNICAL":
                self.assertEqual(route["scope"], "NON_UI", case["id"])
                self.assertFalse(route["use_skill"], case["id"])
                self.assertFalse(route["call_aesthetica"], case["id"])
            elif primary == "IDEA":
                if expected_scope == "NON_UI":
                    self.assertEqual(route["scope"], "NON_UI", case["id"])
                    self.assertFalse(route["use_skill"], case["id"])
                    self.assertFalse(route["call_aesthetica"], case["id"])
                else:
                    self.assertIn(route["scope"], {"UI_UX", "MIXED"}, case["id"])
            else:
                self.fail(f"Unknown expected primary route: {primary}")

    def test_mixed_cases_have_one_primary_and_one_secondary_outcome(self) -> None:
        mixed = [case for case in self.cases if case["category"] == "mixed_product_and_ui"]
        self.assertEqual(len(mixed), 4)
        for case in mixed:
            self.assertIn(case["expected_primary"], {"UI_UX", "IDEA"})
            self.assertIn(case["expected_secondary"], {"UI_UX", "IDEA"})
            self.assertNotEqual(case["expected_primary"], case["expected_secondary"])
            self.assertEqual(case["expected_scope"], "MIXED")

    def test_manifest_keeps_single_router_and_eight_member_governance(self) -> None:
        manifest = json.loads(
            (SYSTEM_ROOT / "p2p_capabilities" / "capabilities.json").read_text(encoding="utf-8")
        )
        capabilities = manifest["capabilities"]
        canonical = [
            item["CAPABILITY_ID"]
            for item in capabilities
            if item["CANONICAL_QUORUM_MEMBER"]
        ]
        self.assertEqual(len(canonical), 8)
        aesthetica = next(item for item in capabilities if item["CAPABILITY_ID"] == "p2p_aesthetica")
        self.assertFalse(aesthetica["CANONICAL_QUORUM_MEMBER"])
        self.assertTrue(aesthetica["OPTIONAL_SPECIALIST"])
        uiux = next(item for item in capabilities if item["CAPABILITY_ID"] == "p2p-uiux")
        self.assertIn("giao diện", uiux["TRIGGERS"])
        self.assertIn("giao diện", aesthetica["TRIGGERS"])


if __name__ == "__main__":
    unittest.main()
