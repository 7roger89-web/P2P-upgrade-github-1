"""P2P-GOVREC01 authority, drift, and fail-closed regression tests."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[1]
TEMP_PARENT = REPO_ROOT / ".tmp"
PROMOTED_COMMIT = "2a71410afd1b29651016ef57a5d2da38938c3f68"
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import doctor  # noqa: E402
import p2p_governance  # noqa: E402


class P2PGovrec01ReconciliationTests(unittest.TestCase):
    def test_authority_separates_historical_official_and_unpromoted_successor(self) -> None:
        control = json.loads((REPO_ROOT / "governance" / "development-control.json").read_text(encoding="utf-8"))
        official = control["official_baseline"]
        current = control["current_development"]
        promoted = control["authority"]["current_promoted_source"]
        self.assertEqual(official["version"], "8.4.7-C-codex.19")
        self.assertEqual(official["promotion_status"], "PROMOTED_VERIFIED")
        self.assertEqual(current["source_version"], "8.4.7-C-codex.74")
        self.assertEqual(current["source_version_status"], "ACTIVE_UNPROMOTED")
        self.assertEqual(promoted["ref"], "origin/main")
        self.assertEqual(promoted["status"], "PROMOTED_CANONICAL_SOURCE")
        self.assertEqual(promoted["commit"], PROMOTED_COMMIT)
        self.assertEqual(promoted["tree"], "3e6ab12ff78a72c4a3ea2a418e11167a8649aaad")
        self.assertEqual(promoted["baseline_ancestor"], "af02170ac7ba180900ca78beb26a2972d80c73b6")
        self.assertTrue(promoted["historical_official_artifact_preserved"])
        self.assertTrue(promoted["unpromoted_successor_separate"])

    def test_current_council_cannot_upgrade_from_historical_or_configured_quorum(self) -> None:
        roadmap = json.loads((REPO_ROOT / "governance" / "p2p-development-roadmap.json").read_text(encoding="utf-8"))
        council = next(item for item in roadmap["items"] if item["roadmap_id"] == "RM-PRIORITY-MULTIHOST-COUNCIL")
        self.assertTrue(council["historical_single_host_live_council_8_of_8"])
        self.assertFalse(council["current_lineage_full_council_live_proven"])
        self.assertEqual(council["current_lineage_full_council_status"], "NOT_PROVEN")
        self.assertIn("HISTORICAL_ONLY", council["current_evidence"])
        self.assertIn("current-lineage full Council is not proven", council["current_evidence"])
        for relative in (
            "docs/p2p-development/framework/capability-skill-map.md",
            "docs/p2p-development/framework/master-roadmap.md",
            "docs/p2p-development/framework/product-architecture.md",
        ):
            text = (REPO_ROOT / relative).read_text(encoding="utf-8")
            self.assertNotIn("CURRENT_LINEAGE_FULL_COUNCIL_LIVE_PROVEN=TRUE", text)
            self.assertIn("CURRENT_LINEAGE_FULL_COUNCIL_LIVE_PROVEN=FALSE", text)

    def test_edge_index_has_all_required_families_and_open_live_slots(self) -> None:
        text = (REPO_ROOT / "reports" / "Edge-Case" / "QA+EDGE_CASE_TEST_PLAN.md").read_text(encoding="utf-8")
        for family in ("retry", "duplicate", "stale", "partial", "quorum", "host failure", "resume", "process interruption"):
            self.assertIn(family, text.lower())
        for slot in (
            "LIVE-EC-RETRY-01",
            "LIVE-EC-DUPLICATE-01",
            "LIVE-EC-STALE-01",
            "LIVE-EC-PARTIAL-01",
            "LIVE-EC-QUORUM-01",
            "LIVE-EC-HOST-FAILURE-01",
            "LIVE-EC-RESUME-01",
            "LIVE-EC-INTERRUPTION-01",
        ):
            self.assertIn(slot, text)
        self.assertIn("LIVE_EVIDENCE_NOT_RUN", text)
        self.assertIn("UNKNOWN", text)
        self.assertIn("NOT_PROVEN", text)

    def test_drift_exclusions_are_not_widened_from_promoted_source(self) -> None:
        current = json.loads((REPO_ROOT / "governance" / "drift-policy.json").read_text(encoding="utf-8"))
        result = subprocess.run(
            ["git", "show", f"{PROMOTED_COMMIT}:governance/drift-policy.json"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        promoted = json.loads(result.stdout)
        for key in ("runtime_lock_excluded_fragments", "excluded_path_fragments"):
            self.assertEqual(current[key], promoted[key], key)
            self.assertNotIn("*", json.dumps(current[key]))

    def _runtime_fixture(self) -> tuple[tempfile.TemporaryDirectory[str], Path, Path]:
        temporary = tempfile.TemporaryDirectory(dir=TEMP_PARENT)
        root = Path(temporary.name)
        governance = root / "governance"
        runtime = root / "runtime"
        governance.mkdir()
        runtime.mkdir()
        (governance / "drift-policy.json").write_text(
            json.dumps(
                {
                    "schema_version": "p2p-codex-drift-policy/2",
                    "package_protected_paths": ["runtime"],
                    "runtime_lock_excluded_fragments": [],
                }
            )
            + "\n",
            encoding="utf-8",
        )
        (runtime / "seed.txt").write_text("seed\n", encoding="utf-8")
        manifest = p2p_governance.runtime_manifest(root, governance)
        (governance / "runtime-manifest.lock.json").write_text(
            json.dumps(
                {
                    "schema_version": p2p_governance.RUNTIME_LOCK_SCHEMA,
                    "protected_files": manifest["protected_files"],
                    "virtual_hashes": manifest["virtual_hashes"],
                }
            )
            + "\n",
            encoding="utf-8",
        )
        return temporary, root, governance

    def test_new_unlocked_runtime_file_is_rejected(self) -> None:
        temporary, root, governance = self._runtime_fixture()
        try:
            (root / "runtime" / "new.txt").write_text("unauthorized\n", encoding="utf-8")
            failures = p2p_governance.verify_runtime_manifest(root, governance)
            self.assertTrue(any("unlocked runtime files added" in item for item in failures))
        finally:
            temporary.cleanup()

    def test_changed_lock_identity_is_rejected(self) -> None:
        temporary, root, governance = self._runtime_fixture()
        try:
            lock_path = governance / "runtime-manifest.lock.json"
            lock = json.loads(lock_path.read_text(encoding="utf-8"))
            lock["protected_files"]["runtime/seed.txt"] = "0" * 64
            lock_path.write_text(json.dumps(lock) + "\n", encoding="utf-8")
            failures = p2p_governance.verify_runtime_manifest(root, governance)
            self.assertTrue(any("protected runtime files changed" in item for item in failures))
        finally:
            temporary.cleanup()

    def _run_doctor_helper(self, returncode: int, stdout: bytes, stderr: bytes):
        completed = subprocess.CompletedProcess(
            args=["p2p_governance.py", "drift"],
            returncode=returncode,
            stdout=stdout,
            stderr=stderr,
        )
        report = doctor.Report()
        with patch.object(doctor.subprocess, "run", return_value=completed) as mocked:
            doctor.check_governance(REPO_ROOT, report, package_mode=True)
        return report, mocked

    def test_doctor_sets_explicit_utf8_environment_and_accepts_valid_json_pass(self) -> None:
        report, mocked = self._run_doctor_helper(
            0,
            b'{"schema_version":"p2p-codex-drift-report/1","status":"PASS"}\n',
            b"",
        )
        self.assertFalse(report.failed)
        kwargs = mocked.call_args.kwargs
        self.assertFalse(kwargs["text"])
        self.assertEqual(kwargs["env"]["PYTHONIOENCODING"], "utf-8")
        self.assertEqual(kwargs["env"]["PYTHONUTF8"], "1")

    def test_doctor_rejects_malformed_utf8_and_malformed_json_helper_output(self) -> None:
        malformed_bytes, _ = self._run_doctor_helper(0, b"\x97", b"")
        self.assertTrue(malformed_bytes.failed)
        malformed_bytes_item = next(item for item in malformed_bytes.items if item["check"] == "governance-drift")
        self.assertIn("not valid UTF-8", malformed_bytes_item["message"])

        malformed_json, _ = self._run_doctor_helper(0, b"not-json\n", b"")
        self.assertTrue(malformed_json.failed)
        malformed_json_item = next(item for item in malformed_json.items if item["check"] == "governance-drift")
        self.assertIn("malformed JSON", malformed_json_item["message"])

    def test_doctor_preserves_nonzero_helper_failure(self) -> None:
        report, _ = self._run_doctor_helper(
            2,
            b'{"schema_version":"p2p-codex-drift-report/1","status":"FAIL"}\n',
            "protected runtime files changed".encode("utf-8"),
        )
        self.assertTrue(report.failed)
        failure_item = next(item for item in report.items if item["check"] == "governance-drift")
        self.assertIn('"status":"FAIL"', failure_item["message"])


if __name__ == "__main__":
    unittest.main()
