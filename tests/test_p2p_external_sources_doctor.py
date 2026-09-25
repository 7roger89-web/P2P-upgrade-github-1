from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import doctor  # noqa: E402


class ExternalSourcesDoctorTests(unittest.TestCase):
    def check(self, root: Path) -> doctor.Report:
        report = doctor.Report()
        doctor.check_external_sources(root, report)
        return report

    def write_manifest(self, root: Path, data: dict) -> None:
        manifest = root / "manifest" / "external-sources.json"
        manifest.parent.mkdir(parents=True, exist_ok=True)
        manifest.write_text(json.dumps(data), encoding="utf-8")

    def test_current_six_source_manifest_and_stored_hashes_pass(self) -> None:
        report = self.check(REPO_ROOT)
        failures = [item for item in report.items if item["level"] == "FAIL"]
        self.assertEqual(failures, [])
        message = next(item["message"] for item in report.items if item["check"] == "external-sources")
        self.assertIn("6 external sources", message)

    def test_missing_required_middle_id_fails_closed(self) -> None:
        data = json.loads((REPO_ROOT / "manifest" / "external-sources.json").read_text(encoding="utf-8"))
        data["sources"] = [item for item in data["sources"] if item["source_id"] != "P2P-EXT-0003"]
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self.write_manifest(root, data)
            report = self.check(root)
        self.assertTrue(any(item["level"] == "FAIL" for item in report.items))

    def test_duplicate_or_malformed_id_fails_closed(self) -> None:
        baseline = json.loads((REPO_ROOT / "manifest" / "external-sources.json").read_text(encoding="utf-8"))
        for replacement in ("P2P-EXT-0001", "P2P-EXT-X006"):
            with self.subTest(source_id=replacement), tempfile.TemporaryDirectory() as raw:
                data = copy.deepcopy(baseline)
                data["sources"][5]["source_id"] = replacement
                root = Path(raw)
                self.write_manifest(root, data)
                report = self.check(root)
                self.assertTrue(any(item["level"] == "FAIL" for item in report.items))

    def test_wrong_schema_fails_closed(self) -> None:
        data = json.loads((REPO_ROOT / "manifest" / "external-sources.json").read_text(encoding="utf-8"))
        data["schema_version"] = "wrong/2"
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self.write_manifest(root, data)
            report = self.check(root)
        self.assertTrue(any(item["level"] == "FAIL" for item in report.items))

    def test_stored_snapshot_hash_mismatch_still_fails_closed(self) -> None:
        data = {
            "schema_version": "p2p-codex-external-sources/1",
            "sources": [
                {"source_id": f"P2P-EXT-{index:04d}", "stored_path": None, "sha256": None}
                for index in range(1, 7)
            ],
        }
        data["sources"][0].update({"stored_path": "snapshot.bin", "sha256": "0" * 64})
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self.write_manifest(root, data)
            (root / "snapshot.bin").write_bytes(b"changed snapshot")
            report = self.check(root)
        failures = [item["message"] for item in report.items if item["level"] == "FAIL"]
        self.assertTrue(any("P2P-EXT-0001:hash" in message for message in failures))


if __name__ == "__main__":
    unittest.main()
