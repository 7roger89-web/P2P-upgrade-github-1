"""C43 framework-reconciliation contract and fail-closed negative tests."""

from __future__ import annotations

import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import validate_p2p_development_framework as validator  # noqa: E402


VOCAB = {
    "VERIFIED_IMPLEMENTED",
    "FOUNDATION_READY",
    "PARTIAL",
    "PLANNED",
    "DEFERRED",
    "REJECTED",
    "OBSOLETE",
    "UNKNOWN",
}
FAMILIES = {"CONTEXT_AND_KNOWLEDGE": {}}


def _record(capability_id: str = "VALID_RECORD", **overrides):
    value = {
        "capability_id": capability_id,
        "name": "Fixture capability",
        "family": "CONTEXT_AND_KNOWLEDGE",
        "status": "PLANNED",
        "beginner_value": "Fixture only",
        "principle": "FIXTURE_INVARIANT",
        "origin_refs": ["C43 fixture"],
        "origin_type": "RECOVERED_LEGACY",
        "dependencies": [],
    }
    value.update(overrides)
    return value


class C43RecordDiagnosticTests(unittest.TestCase):
    def test_missing_capability_id_fails_closed(self):
        diagnostics = validator._record_diagnostics(
            [{"id": "LEGACY_ONLY", "family": "CONTEXT_AND_KNOWLEDGE", "status": "PLANNED"}],
            FAMILIES,
            VOCAB,
        )
        self.assertEqual(diagnostics["valid_ids"], [])
        self.assertEqual(len(diagnostics["missing_id"]), 1)
        self.assertIn("legacy_id=LEGACY_ONLY", diagnostics["missing_id"][0])

    def test_duplicate_capability_id_fails_closed(self):
        diagnostics = validator._record_diagnostics(
            [_record("DUPLICATE_ID"), _record("DUPLICATE_ID")],
            FAMILIES,
            VOCAB,
        )
        self.assertEqual(diagnostics["duplicates"], {"DUPLICATE_ID"})

    def test_unsupported_lifecycle_fails_closed(self):
        diagnostics = validator._record_diagnostics(
            [_record(status="SHIPPED")], FAMILIES, VOCAB
        )
        self.assertEqual(len(diagnostics["unknown_status"]), 1)
        self.assertIn("VALID_RECORD", diagnostics["unknown_status"])

    def test_stale_roadmap_count_is_detected(self):
        self.assertFalse(
            validator._roadmap_count_matches(
                "Counts per family in capability-index.json at regeneration time (159 records, 12 families):",
                174,
            )
        )
        self.assertTrue(
            validator._roadmap_count_matches(
                "Counts per family in capability-index.json at regeneration time (174 records, 12 families):",
                174,
            )
        )

    def test_malformed_record_does_not_raise_uncontrolled_exception(self):
        diagnostics = validator._record_diagnostics(
            [None, _record("MALFORMED_RECORD", dependencies=[{}])],
            FAMILIES,
            VOCAB,
        )
        self.assertEqual(len(diagnostics["non_object"]), 1)
        self.assertEqual(diagnostics["valid_ids"], ["MALFORMED_RECORD"])

        source = REPO_ROOT / "docs/p2p-development/capability-ledger/capability-index.json"
        mutated = json.loads(source.read_text(encoding="utf-8"))
        mutated["capabilities"].append(
            _record("MALFORMED_RECORD", dependencies=[{}], name=None)
        )
        with tempfile.TemporaryDirectory(
            dir=REPO_ROOT / ".tmp", prefix="p2p-c43-validator-fixture-"
        ) as raw:
            fixture = Path(raw) / "capability-index.json"
            fixture.write_text(json.dumps(mutated), encoding="utf-8")
            original_ledger = validator.LEDGER
            original_results = list(validator.results)
            validator.LEDGER = fixture
            validator.results.clear()
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    return_code = validator.main()
            finally:
                validator.LEDGER = original_ledger
                validator.results.clear()
                validator.results.extend(original_results)
        self.assertEqual(return_code, 1)

    def test_no_silent_capability_discard(self):
        records = [_record("RETAINED_ID"), {"id": "RETAINED_ID", "status": "PLANNED"}]
        diagnostics = validator._record_diagnostics(records, FAMILIES, VOCAB)
        self.assertEqual(len(diagnostics["entries"]), 2)
        self.assertEqual(len(diagnostics["missing_id"]), 1)
        self.assertEqual(diagnostics["valid_ids"], ["RETAINED_ID"])


class C43BoundaryTests(unittest.TestCase):
    def test_development_plane_reconciled_without_promotion(self):
        control = json.loads(
            (REPO_ROOT / "governance/development-control.json").read_text(encoding="utf-8")
        )
        plane = control["development_plane"]
        self.assertEqual(plane["goal_id"], "RF01")
        self.assertEqual(plane["status"], "CLOSED_VERIFIED_NO_PROMOTION")
        self.assertEqual(plane["official_canonical_baseline"]["version"], "8.4.7-C-codex.19")
        self.assertEqual(plane["cpt01_r2"]["blocker"], "EXTERNAL_HOST_CAPABILITY_LIMITATION")
        self.assertTrue(plane["cpt01_r2"]["historical"])
        self.assertFalse(plane["promotion"]["allowed"])
        self.assertEqual(
            plane["next_safe_goals"],
            ["FRAMEWORK-03_COUNCIL_FULL_CERTIFICATION_WHEN_LIVE_SUBAGENT_HOST_AVAILABLE"],
        )
        self.assertEqual(plane["closure"]["rf01"], "INDEPENDENTLY_VERIFIED")
        self.assertEqual(plane["closure"]["aerg"], "CURRENT_GITHUB_CI_VERIFIED")
        fw03 = plane["closure"]["framework_03"]
        self.assertEqual(fw03["status"], "IN_PROGRESS")
        self.assertEqual(fw03["third_project_pilot"]["status"], "PASS")
        self.assertEqual(
            fw03["third_project_pilot"]["target_repository"],
            "7roger89-web/child-learning-lab",
        )
        self.assertEqual(
            fw03["third_project_pilot"]["skill_consumption_v1_receipt"],
            "NOT_CLAIMED_PRE_CONTRACT_PRODUCT_EXECUTION",
        )
        self.assertEqual(
            fw03["council_full_certification"]["status"],
            "NOT_PROVEN",
        )
        self.assertFalse(
            fw03["council_full_certification"]["current_lineage_full_council_live_proven"]
        )
        self.assertEqual(
            fw03["council_full_certification"]["observed_host_quorum_status_at_evidence_time"],
            "UNAVAILABLE_IN_THIS_HOST",
        )

    def test_current_lineage_reconciliation_has_no_historical_promotion_target(self):
        control = json.loads(
            (REPO_ROOT / "governance/development-control.json").read_text(encoding="utf-8")
        )
        current = control["current_development"]
        self.assertEqual(current["development_goal"], "P2P-CANONICAL-LINEAGE-REPAIR-01")
        self.assertEqual(current["status"], "RECONCILED_NO_ACTIVE_PROMOTION_CANDIDATE")
        self.assertEqual(current["source_version_status"], "LINEAGE_RECONCILED")
        binding = current["candidate_identity_binding"]
        self.assertEqual(binding["status"], "HISTORICAL_SEALED_UNPROMOTED_REFERENCE")
        self.assertFalse(binding["current_promotion_target"])
        self.assertIn("fresh candidate minted from current main", current["owner_action_required"])

    def test_sealed_c74_boundary_unchanged(self):
        control = json.loads(
            (REPO_ROOT / "governance/development-control.json").read_text(encoding="utf-8")
        )
        base = control["development_plane"]["development_base"]
        self.assertEqual(base["version"], "8.4.7-C-codex.74")
        self.assertEqual(base["status"], "SEALED_UNPROMOTED")
        self.assertEqual(
            base["artifact_sha256"],
            "2b82dea10695abb1c99253be1205728335a114df42cececde2fcca5c1727fd12",
        )
        self.assertEqual(base["closure_commit"], "54d15cb02b04a0fea35fb7d2fd0af1fd564bb264")
        self.assertFalse(control["development_plane"]["promotion"]["allowed"])

    def test_current_validator_returns_bounded_failure(self):
        proc = subprocess.run(
            [sys.executable, "scripts/validate_p2p_development_framework.py"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        self.assertNotEqual(proc.returncode, 0)
        self.assertNotIn("Traceback", proc.stderr)
        self.assertIn("[FAIL] V01-schema-valid", proc.stdout)


if __name__ == "__main__":
    unittest.main()
