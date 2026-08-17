from __future__ import annotations

import copy
import hashlib
import importlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CONTROL_PATH = REPO_ROOT / "governance" / "development-control.json"
OFFICIAL_ARTIFACT = REPO_ROOT.parent / "P2P-8.4.7-C-Codex-Edition-v19.zip"
sys.path.insert(0, str(REPO_ROOT / "scripts"))
control = importlib.import_module("p2p_development_control")
package_release = importlib.import_module("package_release")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_record() -> dict[str, object]:
    return json.loads(CONTROL_PATH.read_text(encoding="utf-8"))


class P2PDevelopmentControlTests(unittest.TestCase):
    def temp_root(self) -> tempfile.TemporaryDirectory[str]:
        return tempfile.TemporaryDirectory(prefix="p2p-c16-control-", dir=str(REPO_ROOT / ".tmp"))

    def copy_control(self, root: Path, value: dict[str, object] | None = None) -> Path:
        destination = root / "governance" / "development-control.json"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(value or load_record(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return destination

    def make_source_root(self, version: str, value: dict[str, object] | None = None) -> tuple[tempfile.TemporaryDirectory[str], Path, Path]:
        temporary = self.temp_root()
        root = Path(temporary.name)
        (root / "manifest").mkdir(parents=True)
        (root / "VERSION").write_text(version + "\n", encoding="utf-8")
        (root / "manifest" / "package.json").write_text(json.dumps({"version": version}) + "\n", encoding="utf-8")
        record = copy.deepcopy(value or load_record())
        record["current_development"]["source_version"] = version  # type: ignore[index]
        control_file = self.copy_control(root, record)
        return temporary, root, control_file

    def make_reconcilable_root(self) -> tuple[tempfile.TemporaryDirectory[str], Path, Path]:
        temporary = self.temp_root()
        root = Path(temporary.name)
        surfaces = [
            Path("VERSION"),
            Path("manifest/package.json"),
            Path(".p2p/system/VERSION"),
            Path(".p2p/system/p2p.manifest.json"),
            Path(".p2p/system/p2p_uiux/__init__.py"),
            Path(".p2p/system/p2p_capabilities/capabilities.json"),
            Path("RELEASE-NOTES.md"),
        ]
        for relative in surfaces:
            destination = root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            content = (REPO_ROOT / relative).read_text(encoding="utf-8")
            destination.write_text(content.replace("8.4.7-C-codex.21", "8.4.7-C-codex.15").replace("8.4.7-C-codex.20", "8.4.7-C-codex.15"), encoding="utf-8")
        record = copy.deepcopy(load_record())
        roadmap = record["roadmap"]  # type: ignore[index]
        items = roadmap["items"]
        c16 = next(item for item in items if item["id"] == "C16")
        c17 = next(item for item in items if item["id"] == "C17")
        c18 = next(item for item in items if item["id"] == "C18")
        c16["status"] = "ACTIVE"
        c17.update({"status": "PLANNED", "evidence_ref": "C16 roadmap only; no implementation"})
        c18.update({"status": "PLANNED", "evidence_ref": "C17 roadmap only; no implementation"})
        roadmap["current"] = {"id": "C16", "status": "ACTIVE", "title": c16["title"]}
        roadmap["likely_next"] = {"id": "C17", "status": "PLANNED", "title": c17["title"]}
        roadmap["stop_rule"] = "After roadmap, lineage, and version-drift protection verify PASS, stop before C17."
        record["capability_status"] = [item for item in record["capability_status"] if item.get("id") != "C17"]  # type: ignore[index]
        record["capability_status"] = [item for item in record["capability_status"] if item.get("id") != "C18"]  # type: ignore[index]
        record["capability_status"] = [item for item in record["capability_status"] if item.get("id") != "C19"]  # type: ignore[index]
        record["capability_status"] = [item for item in record["capability_status"] if item.get("id") != "C20"]  # type: ignore[index]
        record["capability_status"] = [item for item in record["capability_status"] if item.get("id") != "C21"]  # type: ignore[index]
        record["candidate_records"] = [item for item in record["candidate_records"] if item.get("candidate_id") != "C17"]  # type: ignore[index]
        record["candidate_records"] = [item for item in record["candidate_records"] if item.get("candidate_id") != "C19"]  # type: ignore[index]
        record["candidate_records"] = [item for item in record["candidate_records"] if item.get("candidate_id") != "C20"]  # type: ignore[index]
        record["candidate_records"] = [item for item in record["candidate_records"] if item.get("candidate_id") != "C21"]  # type: ignore[index]
        roadmap["items"] = [item for item in items if item.get("id") not in {"C19", "C20", "C21", "C25", "C26", "C27", "C28"}]
        record["current_development"]["source_version"] = "8.4.7-C-codex.15"  # type: ignore[index]
        record["current_development"]["source_version_status"] = "STALE_BLOCKED_BELOW_OFFICIAL"  # type: ignore[index]
        record["current_development"]["source_drift_classification"] = {  # type: ignore[index]
            "primary": "RELEASE_BASELINE_NOT_PROPAGATED",
            "contributors": ["TEST_STALE_SOURCE"],
            "implementation_bug": False,
            "evidence_refs": ["TEST-RECONCILE"],
        }
        control_file = self.copy_control(root, record)
        return temporary, root, control_file

    def test_r01_official_version_is_recovered(self) -> None:
        result = control.validate_path(CONTROL_PATH)
        self.assertEqual(result["official_baseline"], "8.4.7-C-codex.19")

    def test_r02_official_hash_is_recovered(self) -> None:
        result = control.validate_path(CONTROL_PATH)
        self.assertEqual(result["official_baseline_sha256"], control.OFFICIAL_BASELINE_SHA256)

    def test_r03_c10_to_c15_statuses_are_preserved(self) -> None:
        projection = control.status_projection(load_record())
        self.assertEqual(projection["completed"][:6], ["C10", "C11", "C12", "C13", "C14", "C15"])

    def test_r04_c08_remains_deferred(self) -> None:
        self.assertEqual(control.status_projection(load_record())["deferred"], ["C08"])

    def test_r05_c09_remains_blocked_for_missing_event_evidence(self) -> None:
        record = load_record()
        self.assertEqual(record["capability_status"][1]["blocker"], "EVENT_EVIDENCE_UNAVAILABLE")  # type: ignore[index]
        self.assertEqual(control.status_projection(record)["blocked"], ["C09"])

    def test_r06_c15_foundation_and_live_certification_are_separate(self) -> None:
        c15 = next(item for item in load_record()["capability_status"] if item["id"] == "C15")  # type: ignore[index]
        self.assertEqual(c15["foundation_status"], "BOUNDED_DELEGATION_FOUNDATION_READY")
        self.assertFalse(c15["live_delegation_certified"])
        self.assertEqual(c15["live_delegation_status"], "NOT_CERTIFIED")

    def test_r07_task_is_not_agent_invariant_is_durable(self) -> None:
        ids = {item["id"] for item in load_record()["architectural_invariants"]}  # type: ignore[index]
        self.assertIn("task-is-not-agent", ids)

    def test_r08_goal_pass_is_not_promotion_invariant_is_durable(self) -> None:
        ids = {item["id"] for item in load_record()["architectural_invariants"]}  # type: ignore[index]
        self.assertIn("goal-pass-is-not-promotion", ids)

    def test_r09_research_decision_registry_is_preserved_without_vendoring(self) -> None:
        decisions = load_record()["research_decisions"]  # type: ignore[index]
        self.assertEqual({item["name"] for item in decisions}, {"Comp AI CRM", "Semantica", "TencentDB Agent Memory", "Zimster", "Agent TaskGraph Protocol", "DeepSeek Harness", "Nolane UI Intelligence", "Superlearn"})
        self.assertTrue(all(item["vendored"] is False for item in decisions))

    def test_r10_status_projection_is_deterministic(self) -> None:
        record = load_record()
        self.assertEqual(control.status_projection(record), control.status_projection(copy.deepcopy(record)))

    def test_r11_candidate_lineage_names_official_version_and_hash(self) -> None:
        c15 = next(item for item in load_record()["candidate_records"] if item["candidate_id"] == "C15")  # type: ignore[index]
        self.assertEqual(c15["based_on_official_version"], control.OFFICIAL_BASELINE_VERSION)
        self.assertEqual(c15["based_on_official_sha256"], control.OFFICIAL_BASELINE_SHA256)
        self.assertEqual(c15["promotion_status"], "UNPROMOTED")

    def test_r12_stale_source_is_rejected_before_package_side_effects(self) -> None:
        temporary, root, control_file = self.make_source_root("8.4.7-C-codex.18")
        try:
            sentinel = root / "sentinel.txt"
            sentinel.write_text("unchanged\n", encoding="utf-8")
            record = json.loads(control_file.read_text(encoding="utf-8"))
            record["current_development"]["source_version_status"] = "STALE_BLOCKED_BELOW_OFFICIAL"
            control_file.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            with self.assertRaises(control.ControlError) as raised:
                control.validate_lineage_for_build(root, "8.4.7-C-codex.18", control_file=control_file)
            self.assertEqual(raised.exception.code, "LINEAGE_REGRESSION")
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "unchanged\n")
        finally:
            temporary.cleanup()

    def test_r13_filename_only_claim_cannot_replace_authority(self) -> None:
        record = load_record()
        record["official_baseline"]["artifact_path"] = "../P2P-8.4.7-C-Codex-Edition-v999.zip"  # type: ignore[index]
        self.assertEqual(control.validate_control(record)["official_baseline"], control.OFFICIAL_BASELINE_VERSION)
        record["official_baseline"]["artifact_sha256"] = "0" * 64  # type: ignore[index]
        with self.assertRaises(control.ControlError) as raised:
            control.validate_control(record)
        self.assertEqual(raised.exception.code, "OFFICIAL_HASH_MISMATCH")

    def test_r14_roadmap_mutation_appends_provenance(self) -> None:
        temporary = self.temp_root()
        try:
            path = self.copy_control(Path(temporary.name))
            result = control.record_roadmap_mutation(path, "OWNER_APPROVAL", "DEFERRED", "owner decision remains required", ["C16-test-evidence"], changed_at="2026-08-16T02:00:00+00:00", changed_by="test")
            self.assertEqual(result["status"], "PASS")
            updated = json.loads(path.read_text(encoding="utf-8"))
            item = next(item for item in updated["roadmap"]["items"] if item["id"] == "OWNER_APPROVAL")
            self.assertEqual(item["status"], "DEFERRED")
            self.assertEqual(updated["provenance_log"][-1]["what_changed"], "roadmap.OWNER_APPROVAL.status: DONE -> DEFERRED")
        finally:
            temporary.cleanup()

    def test_r15_invalid_roadmap_status_does_not_write(self) -> None:
        temporary = self.temp_root()
        try:
            path = self.copy_control(Path(temporary.name))
            before = sha256(path)
            with self.assertRaises(control.ControlError) as raised:
                control.record_roadmap_mutation(path, "OWNER_APPROVAL", "UNKNOWN", "invalid test", [])
            self.assertEqual(raised.exception.code, "ROADMAP_STATUS")
            self.assertEqual(sha256(path), before)
        finally:
            temporary.cleanup()

    def test_r16_fresh_process_status_needs_no_chat_transcript(self) -> None:
        temporary = self.temp_root()
        try:
            root = Path(temporary.name)
            path = self.copy_control(root)
            result = subprocess.run(
                [sys.executable, str(REPO_ROOT / "scripts" / "p2p_development_control.py"), "status", "--root", str(root), "--control", str(path), "--json"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            projection = json.loads(result.stdout)
            c25_done = any(item.get("id") == "C25" and item.get("status") == "DONE" for item in load_record()["roadmap"]["items"])  # type: ignore[index]
            c21_done = any(item.get("id") == "C21" and item.get("status") == "DONE" for item in load_record()["capability_status"])  # type: ignore[index]
            c20_done = any(item.get("id") == "C20" and item.get("status") == "DONE" for item in load_record()["capability_status"])  # type: ignore[index]
            c19_done = any(item.get("id") == "C19" and item.get("status") == "DONE" for item in load_record()["capability_status"])  # type: ignore[index]
            c26_done = any(item.get("id") == "C26" and item.get("status") == "DONE" for item in load_record()["roadmap"]["items"])  # type: ignore[index]
            if c26_done:
                record = load_record()
                live_current = record["roadmap"]["current"]  # type: ignore[index]
                live_next = record["roadmap"]["likely_next"]  # type: ignore[index]
                self.assertEqual(projection["current"]["id"], live_current["id"])
                self.assertEqual(projection["current"]["status"], live_current["status"])
                self.assertEqual(projection["likely_next"]["id"], live_next["id"])
                self.assertEqual(projection["likely_next"]["status"], live_next["status"])
            elif c25_done:
                self.assertEqual(projection["current"]["id"], "C25")
                self.assertEqual(projection["current"]["status"], "DONE")
                self.assertEqual(projection["likely_next"]["id"], "C26")
                self.assertEqual(projection["likely_next"]["status"], "PLANNED")
            elif c21_done:
                self.assertEqual(projection["current"]["id"], "C21")
                self.assertEqual(projection["likely_next"]["id"], "C21")
            elif c20_done:
                self.assertEqual(projection["current"]["id"], "C20")
                self.assertEqual(projection["likely_next"]["id"], "C20")
            elif c19_done:
                self.assertEqual(projection["current"]["id"], "C19")
                self.assertEqual(projection["likely_next"]["id"], "C19")
            else:
                self.assertEqual(projection["current"]["id"], "C16")
                self.assertEqual(projection["likely_next"]["id"], "C17")
        finally:
            temporary.cleanup()

    def test_r17_official_artifact_is_unchanged(self) -> None:
        if not OFFICIAL_ARTIFACT.is_file():
            self.skipTest(f"official artifact missing: {OFFICIAL_ARTIFACT}")
        before = sha256(OFFICIAL_ARTIFACT)
        control.validate_path(CONTROL_PATH)
        self.assertEqual(before, control.OFFICIAL_BASELINE_SHA256)
        self.assertEqual(sha256(OFFICIAL_ARTIFACT), before)

    def test_r18_canonical_denominator_remains_eight(self) -> None:
        canonical = load_record()["canonical_capability_set"]  # type: ignore[index]
        self.assertEqual(canonical["denominator"], 8)
        self.assertEqual(len(canonical["members"]), 8)
        self.assertEqual(canonical["quorum"], "8/8")

    def test_r19_lineage_reconciliation_updates_active_surfaces_without_promotion(self) -> None:
        temporary, root, control_file = self.make_reconcilable_root()
        try:
            result = control.reconcile_development_lineage(
                root,
                target_version="8.4.7-C-codex.20",
                control_file=control_file,
                evidence_refs=["TEST-RECONCILE"],
            )
            self.assertEqual(result["status"], "PASS")
            self.assertEqual((root / "VERSION").read_text(encoding="utf-8").strip(), "8.4.7-C-codex.20")
            updated = json.loads(control_file.read_text(encoding="utf-8"))
            self.assertEqual(updated["current_development"]["source_version_status"], "LINEAGE_RECONCILED")  # type: ignore[index]
            self.assertEqual(updated["roadmap"]["current"]["id"], "C16")  # type: ignore[index]
            self.assertEqual(updated["roadmap"]["current"]["status"], "ACTIVE")  # type: ignore[index]
            control.validate_lineage_for_build(root, "8.4.7-C-codex.20", control_file=control_file)
            self.assertEqual(updated["candidate_records"][-1]["promotion_status"], "UNPROMOTED")  # type: ignore[index]
        finally:
            temporary.cleanup()

    def test_r20_c17_completion_projection_keeps_live_certification_separate(self) -> None:
        temporary, root, control_file = self.make_reconcilable_root()
        try:
            control.reconcile_development_lineage(
                root,
                target_version="8.4.7-C-codex.20",
                control_file=control_file,
                evidence_refs=["TEST-RECONCILE"],
            )
            result = control.record_c17_completion(
                control_file,
                candidate_sha256="a" * 64,
                candidate_label="test-c17-candidate",
                candidate_artifact_path=".tmp/test-c17-candidate.zip",
                evidence_refs=["TEST-C17"],
            )
            self.assertEqual(result["status"], "PASS")
            refreshed = control.refresh_c17_candidate_artifact(
                control_file,
                candidate_sha256="b" * 64,
                candidate_label="test-c17-candidate-final",
                candidate_artifact_path=".tmp/test-c17-candidate-final.zip",
                evidence_refs=["TEST-C17-REFRESH"],
            )
            self.assertEqual(refreshed["status"], "PASS")
            updated = json.loads(control_file.read_text(encoding="utf-8"))
            projection = control.status_projection(updated)
            self.assertEqual(projection["current"]["id"], "C17")
            self.assertEqual(projection["current"]["status"], "DONE")
            self.assertIn("C17", projection["completed"])
            self.assertFalse(projection["parallel_execution"]["certified"])
            self.assertEqual(projection["parallel_execution"]["status"], "NOT_CERTIFIED")
            self.assertIn("UNPROMOTED", updated["current_development"]["owner_action_required"])  # type: ignore[index]
            candidate = next(item for item in updated["candidate_records"] if item["candidate_id"] == "C17")  # type: ignore[index]
            self.assertEqual(candidate["candidate_sha256"], "b" * 64)
        finally:
            temporary.cleanup()

    def test_embedded_control_record_is_strictly_checked(self) -> None:
        if not OFFICIAL_ARTIFACT.is_file():
            self.skipTest(f"official artifact missing: {OFFICIAL_ARTIFACT}")
        temporary = self.temp_root()
        try:
            stage = Path(temporary.name) / "package"
            stage.mkdir()
            with zipfile.ZipFile(OFFICIAL_ARTIFACT) as archive:
                for member in archive.infolist():
                    relative = Path(member.filename)
                    self.assertFalse(relative.is_absolute() or ".." in relative.parts)
                archive.extractall(stage)
            record = load_record()
            record["current_development"]["source_version"] = "8.4.7-C-codex.19"  # type: ignore[index]
            self.copy_control(stage, record)
            (stage / "release-manifest.json").unlink()
            (stage / "RELEASE-SHA256SUMS.txt").unlink()
            package_release.write_release_metadata(stage, "8.4.7-C-codex.19", [])
            result = package_release.verify_stage(stage)
            self.assertEqual(result["status"], "PASS")
            self.assertEqual(result["development_control"]["status"], "PASS")  # type: ignore[index]

            record["official_baseline"]["artifact_sha256"] = "0" * 64  # type: ignore[index]
            self.copy_control(stage, record)
            (stage / "release-manifest.json").unlink()
            (stage / "RELEASE-SHA256SUMS.txt").unlink()
            package_release.write_release_metadata(stage, "8.4.7-C-codex.19", [])
            with self.assertRaises(ValueError) as raised:
                package_release.verify_stage(stage)
            self.assertIn("embedded development-control validation failed", str(raised.exception))
        finally:
            temporary.cleanup()


if __name__ == "__main__":
    unittest.main()
