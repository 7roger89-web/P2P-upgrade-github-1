from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_ROOT = REPO_ROOT / ".p2p" / "system"
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "p2p-aesthetica-selective-routing.json"
REGISTRY = SYSTEM_ROOT / "p2p_capabilities" / "capabilities.json"
ROUTER_SOURCE = SYSTEM_ROOT / "p2p_uiux" / "router.py"
sys.path.insert(0, str(SYSTEM_ROOT))

from p2p_uiux.router import classify_request  # noqa: E402


class P2PAestheticaSelectiveRoutingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        cls.cases = cls.fixture["cases"]

    def test_fixture_is_bilingual_and_has_at_least_thirty_cases(self) -> None:
        self.assertEqual(self.fixture["schema"], "p2p-aesthetica-selective-routing-fixture/1")
        self.assertEqual(self.fixture["certification_basis"], "bounded_10_scenario_behavioral_certification")
        self.assertGreaterEqual(len(self.cases), 30)
        self.assertEqual({case["language"] for case in self.cases}, {"en", "vi"})
        self.assertEqual(len({case["id"] for case in self.cases}), len(self.cases))

    def test_user_requests_do_not_choose_internal_specialist_names(self) -> None:
        forbidden = ("p2p_", "aesthetica", "canonical", "quorum", "router-agent")
        for case in self.cases:
            request = case["request"].lower()
            self.assertFalse(any(token in request for token in forbidden), case["id"])

    def test_selective_policy_matrix(self) -> None:
        for case in self.cases:
            available = case.get("profile_available", True)
            route = classify_request(case["request"], force_profile_available=available)
            with self.subTest(case=case["id"], request=case["request"]):
                self.assertEqual(route["scope"], case["expected_scope"])
                self.assertEqual(route["use_skill"], case["expected_use_skill"])
                self.assertEqual(route["specialist_eligible"], case["expected_eligible"])
                self.assertEqual(route["call_aesthetica"], case["expected_call"])
                self.assertEqual(route["specialist_classes"], case["expected_classes"])

    def test_optional_fallback_keeps_primary_uiux_active(self) -> None:
        fallback_cases = [case for case in self.cases if case.get("profile_available") is False]
        self.assertGreaterEqual(len(fallback_cases), 2)
        for case in fallback_cases:
            route = classify_request(case["request"], force_profile_available=False)
            with self.subTest(case=case["id"]):
                self.assertTrue(route["use_skill"])
                self.assertTrue(route["specialist_eligible"])
                self.assertFalse(route["call_aesthetica"])
                self.assertIn("PROFILE_UNAVAILABLE", route["reason"])

    def test_uiux_primary_is_not_suppressed_for_any_ui_case(self) -> None:
        for case in self.cases:
            if case["expected_scope"] == "NON_UI":
                continue
            route = classify_request(case["request"], force_profile_available=True)
            with self.subTest(case=case["id"]):
                self.assertTrue(route["use_skill"])

    def test_canonical_quorum_and_optional_identity_are_unchanged(self) -> None:
        registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        canonical = [item["CAPABILITY_ID"] for item in registry["capabilities"] if item["CANONICAL_QUORUM_MEMBER"]]
        self.assertEqual(len(canonical), 8)
        self.assertEqual(f"{len(canonical)}/{len(canonical)}", "8/8")
        optional = next(item for item in registry["capabilities"] if item["CAPABILITY_ID"] == "p2p_aesthetica")
        self.assertTrue(optional["OPTIONAL_SPECIALIST"])
        self.assertFalse(optional["CANONICAL_QUORUM_MEMBER"])

    def test_existing_single_router_surface_remains_the_only_decision_function(self) -> None:
        source = ROUTER_SOURCE.read_text(encoding="utf-8")
        self.assertEqual(source.count("def classify_request("), 1)
        self.assertIn('"adaptive_quorum"', source)
        self.assertNotIn("def aesthetica_router(", source)


if __name__ == "__main__":
    unittest.main()
