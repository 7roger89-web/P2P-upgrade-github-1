import json
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_ROOT = REPO_ROOT / ".p2p" / "system"
if str(SYSTEM_ROOT) not in sys.path:
    sys.path.insert(0, str(SYSTEM_ROOT))

from p2p_capabilities.orchestration_policy import derive_requirement  # noqa: E402


FIXTURE = REPO_ROOT / "tests" / "fixtures" / "p2p-c18-adaptive-orchestration.json"


class AdaptiveOrchestrationPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cases = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_ao1_to_ao20_match_frozen_policy_matrix(self) -> None:
        self.assertEqual([case["id"] for case in self.cases], [f"AO{index}" for index in range(1, 21)])
        for case in self.cases:
            with self.subTest(case=case["id"]):
                result = derive_requirement(case["profile"])
                for field, expected in case["expected"].items():
                    self.assertEqual(result[field], expected)

    def test_naive_policies_are_not_used_as_runtime_policy(self) -> None:
        expected = [case["expected"] for case in self.cases]
        mismatches = {
            "ALWAYS_DIRECT": sum(item["worker_strategy"] != "DIRECT" for item in expected),
            "ALWAYS_ONE_WORKER": sum(item["worker_strategy"] != "ONE_WORKER" for item in expected),
            "ALWAYS_TWO_WORKERS": sum(item["worker_strategy"] != "TWO_WORKERS" for item in expected),
            "ALWAYS_EXPANDED_CONTEXT": sum(item["context_class"] != "EXPANDED" for item in expected),
            "ALWAYS_HIGH_RIGOR": sum(item["reasoning_class"] != "HIGH" or item["verification_class"] != "HIGH_RISK" for item in expected),
        }
        self.assertTrue(all(value > 0 for value in mismatches.values()), mismatches)

    def test_quality_and_safety_boundaries_are_not_traded_for_worker_economy(self) -> None:
        for case in self.cases:
            result = derive_requirement(case["profile"])
            self.assertLessEqual(result["worker_count"], 2, case["id"])
            self.assertFalse(result["quality_gate"]["permission_expansion"], case["id"])
            self.assertEqual(result["provider_model_resolution"], "DEFERRED", case["id"])
            self.assertEqual(result["canonical_governance"]["full_quorum"], "8/8", case["id"])
            self.assertFalse(result["provenance"]["hidden_reasoning_stored"], case["id"])
            if case["expected"]["worker_strategy"] == "BLOCKED":
                self.assertEqual(result["status"], "BLOCKED", case["id"])
                self.assertEqual(result["worker_count"], 0, case["id"])

    def test_high_risk_verification_does_not_automatically_spawn_workers(self) -> None:
        result = derive_requirement({"task_size": "SMALL", "mutation_risk": "HIGH", "deterministic_verifier": True})
        self.assertEqual(result["verification_class"], "HIGH_RISK")
        self.assertEqual(result["worker_strategy"], "DIRECT")
        self.assertEqual(result["worker_count"], 0)

    def test_complexity_and_assurance_axes_are_independent(self) -> None:
        easy_critical = derive_requirement({
            "task_size": "SMALL",
            "dependency_complexity": "NONE",
            "ambiguity": "LOW",
            "mutation_risk": "DESTRUCTIVE",
            "deterministic_verifier": True,
        })
        hard_low = derive_requirement({
            "task_size": "LARGE",
            "dependency_complexity": "HIGH",
            "ambiguity": "HIGH",
            "mutation_risk": "LOW",
            "evidence_availability": "COMPLETE",
        })
        self.assertEqual(easy_critical["verification_class"], "HIGH_RISK")
        self.assertEqual(hard_low["reasoning_class"], "HIGH")
        self.assertNotEqual(hard_low["verification_class"], "HIGH_RISK")
        self.assertEqual(easy_critical["provider_model_resolution"], "DEFERRED")
        self.assertEqual(hard_low["provider_model_resolution"], "DEFERRED")

    def test_local_serialization_proxy_is_explicit_and_provider_neutral(self) -> None:
        result = derive_requirement({"task_size": "SMALL", "context_proxy_bytes": 1024, "context_refs": ["task:contract"]})
        self.assertEqual(result["context_measurement"]["label"], "LOCAL_SERIALIZATION_PROXY")
        self.assertEqual(result["context_measurement"]["bytes"], 1024)
        self.assertEqual(result["context_measurement"]["refs"], ["task:contract"])


if __name__ == "__main__":
    unittest.main()
