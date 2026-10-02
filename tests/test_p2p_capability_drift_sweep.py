"""Focused tests for the read-only capability drift revalidation sweep.

Covers the RM-PRIORITY-DRIFT-SWEEP contract: full-index coverage, an honest
closed classification vocabulary, fail-closed handling of malformed records,
deterministic output, ref-resolution semantics, and the invariant that a
historical certification can never be presented as current eligibility.

All fixtures are temporary; no test mutates the canonical capability index,
the roadmap, or the drift policy, and no test performs network access.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import p2p_capability_drift_sweep as sweep  # noqa: E402


LEDGER_DIR = REPO_ROOT / "docs/p2p-development/capability-ledger"
CAPABILITY_INDEX = LEDGER_DIR / "capability-index.json"
COMMITTED_SWEEP = LEDGER_DIR / "capability-drift-sweep.json"
FROZEN_TIME = "2026-10-02T00:00:00Z"


def _record(capability_id="FIXTURE", status="PLANNED", **overrides):
    record = {
        "capability_id": capability_id,
        "name": "Fixture capability",
        "family": "CONTEXT_AND_KNOWLEDGE",
        "beginner_value": "Fixture value.",
        "principle": "FIXTURE_PRINCIPLE",
        "origin_refs": ["governance/drift-policy.json"],
        "origin_type": "PROJECT_LEARNING",
        "dependencies": [],
        "status": status,
    }
    record.update(overrides)
    return record


def _tree(tracked=(), ignored=()):
    tracked = tuple(tracked) + ("governance/drift-policy.json",)
    return sweep.TreeIndex(tracked=tracked, ignored=ignored)


class RefResolutionTests(unittest.TestCase):
    def test_prose_and_provenance_labels_are_not_paths(self):
        tree = _tree()
        for raw in ("P2P-C27 terminal report (60 items)", "RA-EXT-021/022/019/023",
                    "branch c36-real-host-binding @ 8a1ad30", "role_bridge/role_receipt/role_verifier"):
            with self.subTest(raw=raw):
                self.assertEqual(sweep.resolve_ref(tree, raw).resolution, sweep.NON_PATH)

    def test_missing_repo_path_is_absent_not_silently_resolved(self):
        tree = _tree(tracked=["docs/KIEN-TRUC.md"])
        self.assertEqual(sweep.resolve_ref(tree, "reports/MISSING-EVIDENCE.md").resolution,
                         sweep.ABSENT)

    def test_gitignored_state_is_never_current_tree_evidence(self):
        tree = _tree(tracked=[], ignored=[".p2p/state/", ".tmp/"])
        self.assertEqual(sweep.resolve_ref(tree, ".p2p/state/capsule/").resolution,
                         sweep.NOT_CURRENT_TREE_NON_DURABLE)
        self.assertEqual(sweep.resolve_ref(tree, ".tmp/p2p-c19/candidates/x.zip").resolution,
                         sweep.NOT_CURRENT_TREE_NON_DURABLE)

    def test_documented_runtime_remap_and_unique_basename_resolution(self):
        tree = _tree(tracked=[".p2p/system/p2p_capabilities/manus_adapter.py",
                              "docs/p2p-development/reports/P2P-C38-terminal-report.md"])
        remapped = sweep.resolve_ref(tree, "runtime/p2p_capabilities/manus_adapter.py")
        self.assertEqual(remapped.resolution, sweep.RESOLVED_REMAP)
        self.assertEqual(remapped.resolved_path, ".p2p/system/p2p_capabilities/manus_adapter.py")
        moved = sweep.resolve_ref(tree, "P2P-C38-terminal-report.md")
        self.assertEqual(moved.resolution, sweep.RESOLVED_BASENAME)
        self.assertEqual(moved.resolved_path, "docs/p2p-development/reports/P2P-C38-terminal-report.md")

    def test_ambiguous_basename_fails_closed(self):
        tree = _tree(tracked=["a/REPORT.md", "b/REPORT.md"])
        self.assertEqual(sweep.resolve_ref(tree, "docs/REPORT.md").resolution, sweep.ABSENT)


class ClassificationTests(unittest.TestCase):
    def test_static_implementation_with_resolving_anchor_is_verified(self):
        tree = _tree(tracked=["scripts/p2p_safe_installer.py", "tests/test_safe_installer.py"])
        entry = sweep.classify_record(_record(
            "SAFE_INSTALLER_LIKE", "VERIFIED_IMPLEMENTED",
            implementation_refs=["scripts/p2p_safe_installer.py"],
            evidence_refs=["tests/test_safe_installer.py"],
        ), tree)
        self.assertEqual(entry["current_classification"], sweep.VERIFIED)
        self.assertEqual(entry["implementation_eligibility"], "STATICALLY_SUPPORTED")

    def test_absent_declared_anchor_is_unknown_and_stale(self):
        tree = _tree(tracked=["scripts/p2p_safe_installer.py"])
        entry = sweep.classify_record(_record(
            "SAFE_INSTALLER_LIKE", "VERIFIED_IMPLEMENTED",
            implementation_refs=["scripts/p2p_safe_installer.py"],
            evidence_refs=["reports/PILOT_INSTALLATION_EVIDENCE.md"],
        ), tree)
        self.assertEqual(entry["current_classification"], sweep.UNKNOWN)
        self.assertEqual(entry["reason"], "NO_CURRENT_TREE_EVIDENCE_ANCHOR")
        self.assertTrue(entry["stale_claim"])
        self.assertEqual(entry["stale_claim_action"], "PENDING_RECONCILIATION")

    def test_stale_claim_disclosed_in_record_is_marked_reconciled(self):
        tree = _tree(tracked=["scripts/p2p_safe_installer.py"])
        entry = sweep.classify_record(_record(
            "SAFE_INSTALLER_LIKE", "VERIFIED_IMPLEMENTED",
            implementation_refs=["scripts/p2p_safe_installer.py"],
            evidence_refs=["reports/PILOT_INSTALLATION_EVIDENCE.md"],
            known_gaps=["PILOT_INSTALLATION_EVIDENCE.md is not present in the current tree."],
        ), tree)
        self.assertTrue(entry["stale_claim"])
        self.assertTrue(entry["stale_claim_disclosed_in_record"])
        self.assertEqual(entry["stale_claim_action"], "DISCLOSED_IN_RECORD_HISTORY_PRESERVED")

    def test_live_eligibility_assertion_is_never_verified(self):
        tree = _tree(tracked=["scripts/p2p_certify.py"])
        entry = sweep.classify_record(_record(
            "PROVIDER_TARGET_LIKE", "VERIFIED_IMPLEMENTED",
            implementation_refs=["scripts/p2p_certify.py"],
            evidence_refs=["scripts/p2p_certify.py"],
            beginner_value="The provider is certified as a safe execution environment.",
        ), tree)
        self.assertTrue(entry["current_eligibility_claim"])
        self.assertEqual(entry["current_classification"], sweep.UNKNOWN)
        self.assertEqual(entry["reason"], "LIVE_ELIGIBILITY_NOT_FRESHLY_PROVABLE")

    def test_disclaimed_historical_certification_is_allowed(self):
        tree = _tree(tracked=["scripts/p2p_certify.py"])
        entry = sweep.classify_record(_record(
            "PROVIDER_TARGET_LIKE", "VERIFIED_IMPLEMENTED",
            implementation_refs=["scripts/p2p_certify.py"],
            evidence_refs=["scripts/p2p_certify.py"],
            beginner_value="The provider was certified at evidence time.",
            known_gaps=["CURRENT_AUTH_STATE = UNKNOWN_NOT_PROBED; the certification is historical."],
        ), tree)
        self.assertFalse(entry["current_eligibility_claim"])
        self.assertTrue(entry["explicit_disclaimer_present"])
        self.assertEqual(entry["current_classification"], sweep.VERIFIED)

    def test_non_implementation_status_never_claims_implementation(self):
        tree = _tree(tracked=["governance/p2p-development-roadmap.json"])
        for status in ("PLANNED", "DEFERRED", "REJECTED", "OBSOLETE", "UNKNOWN"):
            with self.subTest(status=status):
                entry = sweep.classify_record(_record("PLANNED_LIKE", status), tree)
                self.assertEqual(entry["claim_scope"], "RECORD_AND_PROVENANCE")
                self.assertEqual(entry["implementation_eligibility"], "NOT_CLAIMED")
                self.assertEqual(entry["current_classification"], sweep.VERIFIED)

    def test_non_durable_implementation_anchor_is_unknown(self):
        tree = _tree(tracked=["docs/KIEN-TRUC.md"], ignored=[".p2p/state/"])
        entry = sweep.classify_record(_record(
            "CAPSULE_LIKE", "PARTIAL",
            implementation_refs=[".p2p/state/capsule/"],
            evidence_refs=["docs/KIEN-TRUC.md"],
        ), tree)
        self.assertEqual(entry["current_classification"], sweep.UNKNOWN)
        self.assertEqual(entry["reason"], "DECLARED_IMPLEMENTATION_ANCHOR_IS_NON_DURABLE_STATE")


class FailClosedTests(unittest.TestCase):
    def _write_index(self, root, records):
        index = {
            "ledger_id": "capability-index",
            "schema_version": 2,
            "status_vocabulary": ["VERIFIED_IMPLEMENTED", "FOUNDATION_READY", "PARTIAL", "PLANNED",
                                  "DEFERRED", "REJECTED", "OBSOLETE", "UNKNOWN"],
            "families": {},
            "capabilities": records,
        }
        path = root / sweep.CAPABILITY_INDEX_REL
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(index), encoding="utf-8")
        policy = root / sweep.DRIFT_POLICY_REL
        policy.parent.mkdir(parents=True, exist_ok=True)
        policy.write_text("{}", encoding="utf-8")
        return root

    def test_duplicate_ids_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._write_index(Path(tmp), [_record("DUP"), _record("DUP")])
            with self.assertRaises(sweep.SweepError):
                sweep.build_sweep(root)

    def test_unknown_status_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._write_index(Path(tmp), [_record("BAD_STATUS", "INVENTED_STATUS")])
            with self.assertRaises(sweep.SweepError):
                sweep.build_sweep(root)

    def test_missing_identifier_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._write_index(Path(tmp), [_record(None)])
            with self.assertRaises(sweep.SweepError):
                sweep.build_sweep(root)

    def test_cli_reports_fail_closed_with_exit_2(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._write_index(Path(tmp), [_record("BAD_STATUS", "INVENTED_STATUS")])
            completed = subprocess.run(
                [sys.executable, str(REPO_ROOT / sweep.SWEEP_ENGINE), "--repo", str(root)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(completed.returncode, 2)
            self.assertIn("SWEEP_FAIL_CLOSED", completed.stderr)


class RealIndexSweepTests(unittest.TestCase):
    """Whole-index contract checks against the canonical capability index."""

    @classmethod
    def setUpClass(cls):
        cls.sweep = sweep.build_sweep(REPO_ROOT, generated_at=FROZEN_TIME)
        cls.index = json.loads(CAPABILITY_INDEX.read_text(encoding="utf-8"))

    def test_full_coverage_and_unique_ids(self):
        expected = [r["capability_id"] for r in self.index["capabilities"]]
        observed = [r["capability_id"] for r in self.sweep["records"]]
        self.assertEqual(observed, expected)
        self.assertEqual(len(set(observed)), len(observed))
        self.assertEqual(self.sweep["counts"]["total_records"], len(expected))
        self.assertEqual(self.sweep["counts"]["capability_index_records"], len(expected))

    def test_every_record_is_classified_from_the_closed_vocabulary(self):
        self.assertEqual(set(self.sweep["classification_vocabulary"]), set(sweep.CLASSIFICATIONS))
        for entry in self.sweep["records"]:
            with self.subTest(capability_id=entry["capability_id"]):
                self.assertIn(entry["current_classification"], sweep.CLASSIFICATIONS)
                self.assertTrue(entry["reason"])
                self.assertIn(entry["original_status"], self.index["status_vocabulary"])

    def test_no_historical_certification_is_presented_as_current_eligibility(self):
        for entry in self.sweep["records"]:
            if entry["current_eligibility_claim"]:
                with self.subTest(capability_id=entry["capability_id"]):
                    self.assertEqual(entry["current_classification"], sweep.UNKNOWN)
                    self.assertEqual(entry["implementation_eligibility"], "NOT_PROBED")

    def test_live_dependency_records_never_claim_static_current_eligibility_blindly(self):
        for entry in self.sweep["records"]:
            if entry["current_classification"] == sweep.VERIFIED and entry["live_dependency"]:
                with self.subTest(capability_id=entry["capability_id"]):
                    self.assertFalse(entry["current_eligibility_claim"])

    def test_sweep_is_read_only(self):
        before = sweep._sha256_file(CAPABILITY_INDEX)
        sweep.build_sweep(REPO_ROOT, generated_at=FROZEN_TIME)
        self.assertEqual(before, sweep._sha256_file(CAPABILITY_INDEX))

    def test_output_is_deterministic_apart_from_the_explicit_timestamp(self):
        first = sweep.build_sweep(REPO_ROOT, generated_at=FROZEN_TIME)
        second = sweep.build_sweep(REPO_ROOT, generated_at=FROZEN_TIME)
        self.assertEqual(json.dumps(first, sort_keys=True), json.dumps(second, sort_keys=True))

    def test_committed_sweep_artifact_reproduces(self):
        if not COMMITTED_SWEEP.is_file():
            self.skipTest("sweep artifact not present in this tree")
        committed = json.loads(COMMITTED_SWEEP.read_text(encoding="utf-8"))
        self.assertEqual(committed["schema"], sweep.SWEEP_SCHEMA)
        self.assertEqual(committed["counts"], self.sweep["counts"])
        self.assertEqual(committed["inputs"], self.sweep["inputs"])
        self.assertEqual(json.dumps(committed["records"], sort_keys=True),
                         json.dumps(self.sweep["records"], sort_keys=True))
        self.assertEqual(committed["stale_claims"], self.sweep["stale_claims"])

    def test_no_stale_claim_is_left_pending_reconciliation(self):
        pending = [entry["capability_id"] for entry in self.sweep["records"]
                   if entry["stale_claim"] and not entry["stale_claim_disclosed_in_record"]]
        self.assertEqual(pending, [],
                         "every stale current claim must be expired/disclosed, not silently kept")

    def test_drift_policy_hash_is_bound(self):
        self.assertEqual(self.sweep["inputs"]["drift_policy"]["sha256"],
                         sweep._sha256_file(REPO_ROOT / sweep.DRIFT_POLICY_REL))
        self.assertEqual(self.sweep["probe_policy"]["live_probes_run"], 0)


if __name__ == "__main__":
    unittest.main()
