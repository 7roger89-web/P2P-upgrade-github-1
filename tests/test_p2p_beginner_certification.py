from __future__ import annotations

import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]

import sys

sys.path.insert(0, str(REPO_ROOT / "scripts"))

import p2p_beginner_certification as certification  # noqa: E402


class P2PBeginnerCertificationTests(unittest.TestCase):
    def test_full_behavioral_certification_is_isolated_and_honest(self) -> None:
        with tempfile.TemporaryDirectory(prefix="p2p-cert-report-test-") as raw:
            result = certification.run_certification(REPO_ROOT, Path(raw))

        self.assertEqual(result["harness_status"], "PASS")
        self.assertEqual(result["beginner_readiness"], "CERTIFIED_WITH_LIMITATIONS")
        self.assertEqual({item["scenario_id"] for item in result["SCENARIOS"]}, {"A", "B", "C", "D"})
        self.assertTrue(any(item["longitudinal"] and item["stage_count"] >= 8 for item in result["SCENARIOS"]))
        self.assertEqual(result["FAILURES"], [])
        self.assertEqual(result["ACTUAL_STATUS"]["canonical_safety"], "PASS")
        self.assertEqual(result["ACTUAL_STATUS"]["aesthetica_safety"], "PASS")
        self.assertEqual(result["ACTUAL_STATUS"]["machine_schema"], "PASS")
        self.assertTrue(result["ENVIRONMENT_ISOLATION"]["protected_paths_unchanged"])
        self.assertEqual(result["ENVIRONMENT_ISOLATION"]["user_project_writes"], 0)
        self.assertEqual(result["ENVIRONMENT_ISOLATION"]["external_integrations"], "none")
        self.assertEqual(result["RECOMMENDED_NEXT_GAP"]["goal"], "P2P Native Decision Trace")

        minimum = {"scenario_id", "stage", "dimension", "expected", "actual_status", "evidence_ref", "critical", "notes"}
        self.assertTrue(result["records"])
        self.assertTrue(all(minimum <= set(item) for item in result["records"]))
        self.assertTrue(all(item["actual_status"] in certification.ALLOWED_STATUSES for item in result["records"]))

        stage_records = {(item["scenario_id"], item["stage"], item["dimension"]): item for item in result["records"]}
        self.assertEqual(stage_records[("A", "DEBUGGING", "G")]["actual_status"], "PASS")
        self.assertEqual(stage_records[("B", "UI/UX", "K")]["actual_status"], "PASS")
        self.assertEqual(stage_records[("C", "UI/UX", "K")]["actual_status"], "PASS")
        self.assertNotIn("chain_of_thought", str(result).lower())

    def test_machine_schema_and_readiness_guards_do_not_false_certify(self) -> None:
        invalid = {"records": [{"scenario_id": "A"}], "CERTIFICATION_VERSION": certification.CERTIFICATION_VERSION}
        validation = certification.validate_machine_result(invalid)
        self.assertFalse(validation["valid"])
        self.assertTrue(validation["missing_top_fields"])
        self.assertTrue(validation["bad_rows"])

        critical_result, failures, _ = certification.readiness_class(
            [{"actual_status": "FAIL", "critical": True, "scenario_id": "A", "stage": "DEBUGGING", "dimension": "I", "notes": "false completion"}],
            "PASS",
        )
        self.assertEqual(critical_result, "NOT_CERTIFIED")
        self.assertEqual(len(failures), 1)

        limited_result, failures, _ = certification.readiness_class(
            [{"actual_status": "PARTIAL", "critical": False, "scenario_id": "A", "stage": "WHY", "dimension": "N", "notes": "distributed evidence"}],
            "PASS",
        )
        self.assertEqual(limited_result, "CERTIFIED_WITH_LIMITATIONS")
        self.assertEqual(failures, [])


if __name__ == "__main__":
    unittest.main()
