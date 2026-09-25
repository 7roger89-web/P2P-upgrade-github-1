from __future__ import annotations

import copy
import json
import shutil
import sys
import tempfile
import types
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

    def check_runtime_layout(self, layout: str) -> doctor.Report:
        baseline = json.loads((REPO_ROOT / "manifest" / "external-sources.json").read_text(encoding="utf-8"))
        for item in baseline["sources"][:-1]:
            item["stored_path"] = None
            item["sha256"] = None
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self.write_manifest(root, baseline)
            if layout == "portable":
                package_dir = root / "runtime" / "p2p_capabilities"
                (root / "release-manifest.json").write_text("{}", encoding="utf-8")
            else:
                package_dir = root / ".p2p" / "system" / "p2p_capabilities"
                (root / "governance").mkdir()
                (root / "manifest" / "package.json").write_text("{}", encoding="utf-8")
                (root / "scripts").mkdir()
                (root / "scripts" / "package_release.py").write_text("", encoding="utf-8")
            package_dir.mkdir(parents=True)
            canonical_package = REPO_ROOT / ".p2p" / "system" / "p2p_capabilities"
            for name in ("vendor_skill.py", "model.py", "routing.py"):
                shutil.copy2(canonical_package / name, package_dir / name)
            snapshot_path = baseline["sources"][-1]["stored_path"]
            shutil.copytree(REPO_ROOT / snapshot_path, root / snapshot_path)
            if layout == "portable":
                cached = {
                    name: module
                    for name, module in sys.modules.items()
                    if name == "p2p_capabilities" or name.startswith("p2p_capabilities.")
                }
                for name in list(cached):
                    del sys.modules[name]
                decoy = types.ModuleType("p2p_capabilities")
                decoy.__path__ = []
                decoy_vendor = types.ModuleType("p2p_capabilities.vendor_skill")
                decoy_vendor.snapshot_tree_sha256 = lambda _path: "wrong-cached-runtime"
                sys.modules["p2p_capabilities"] = decoy
                sys.modules["p2p_capabilities.vendor_skill"] = decoy_vendor
                try:
                    report = self.check(root)
                finally:
                    for name in list(sys.modules):
                        if name == "p2p_capabilities" or name.startswith("p2p_capabilities."):
                            del sys.modules[name]
                    sys.modules.update(cached)
            else:
                report = self.check(root)
            if layout == "portable":
                self.assertFalse((root / ".p2p" / "system").exists())
        return report

    def test_current_six_source_manifest_and_stored_hashes_pass(self) -> None:
        report = self.check(REPO_ROOT)
        failures = [item for item in report.items if item["level"] == "FAIL"]
        self.assertEqual(failures, [])
        message = next(item["message"] for item in report.items if item["check"] == "external-sources")
        self.assertIn("6 external sources", message)

    def test_development_runtime_validates_security_audit_directory_snapshot(self) -> None:
        report = self.check_runtime_layout("development")
        self.assertFalse([item for item in report.items if item["level"] == "FAIL"])
        self.assertTrue(any(item["check"] == "external-sources" and item["level"] == "PASS" for item in report.items))

    def test_portable_runtime_validates_security_audit_directory_snapshot_without_system_tree(self) -> None:
        report = self.check_runtime_layout("portable")
        self.assertFalse([item for item in report.items if item["level"] == "FAIL"])
        self.assertTrue(any(item["check"] == "external-sources" and item["level"] == "PASS" for item in report.items))

    def test_missing_required_middle_id_fails_closed(self) -> None:
        data = json.loads((REPO_ROOT / "manifest" / "external-sources.json").read_text(encoding="utf-8"))
        data["sources"] = [item for item in data["sources"] if item["source_id"] != "P2P-EXT-0003"]
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self.write_manifest(root, data)
            report = self.check(root)
        self.assertTrue(any(item["level"] == "FAIL" for item in report.items))

    def test_missing_final_required_0006_fails_closed(self) -> None:
        data = json.loads((REPO_ROOT / "manifest" / "external-sources.json").read_text(encoding="utf-8"))
        data["sources"] = [item for item in data["sources"] if item["source_id"] != "P2P-EXT-0006"]
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self.write_manifest(root, data)
            report = self.check(root)
        failures = [item["message"] for item in report.items if item["level"] == "FAIL"]
        self.assertEqual(failures, ["External-source schema or IDs are incomplete"])

    def test_duplicate_or_malformed_id_fails_closed(self) -> None:
        baseline = json.loads((REPO_ROOT / "manifest" / "external-sources.json").read_text(encoding="utf-8"))
        for replacement in ("P2P-EXT-0001", "P2P-EXT-X006", ["P2P-EXT-0006"]):
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

    def test_missing_directory_snapshot_fails_closed(self) -> None:
        data = {
            "schema_version": "p2p-codex-external-sources/1",
            "sources": [
                {"source_id": f"P2P-EXT-{index:04d}", "stored_path": None, "sha256": None}
                for index in range(1, 7)
            ],
        }
        data["sources"][5].update({"stored_path": "missing-snapshot", "sha256": "e6746baf"})
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self.write_manifest(root, data)
            report = self.check(root)
        failures = [item["message"] for item in report.items if item["level"] == "FAIL"]
        self.assertTrue(any("P2P-EXT-0006:missing" in message for message in failures))

    def test_directory_tree_hash_mismatch_fails_closed(self) -> None:
        data = {
            "schema_version": "p2p-codex-external-sources/1",
            "sources": [
                {"source_id": f"P2P-EXT-{index:04d}", "stored_path": None, "sha256": None}
                for index in range(1, 7)
            ],
        }
        data["sources"][5].update({"stored_path": "snapshot-dir", "sha256": "0" * 64})
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self.write_manifest(root, data)
            (root / "snapshot-dir").mkdir()
            (root / "snapshot-dir" / "content.txt").write_text("different tree", encoding="utf-8")
            (root / ".p2p" / "system" / "p2p_capabilities").mkdir(parents=True)
            for name in ("vendor_skill.py", "model.py", "routing.py"):
                shutil.copy2(
                    REPO_ROOT / ".p2p" / "system" / "p2p_capabilities" / name,
                    root / ".p2p" / "system" / "p2p_capabilities" / name,
                )
            (root / "governance").mkdir()
            (root / "manifest" / "package.json").write_text("{}", encoding="utf-8")
            (root / "scripts").mkdir()
            (root / "scripts" / "package_release.py").write_text("", encoding="utf-8")
            report = self.check(root)
        failures = [item["message"] for item in report.items if item["level"] == "FAIL"]
        self.assertTrue(any("P2P-EXT-0006:hash" in message for message in failures))


if __name__ == "__main__":
    unittest.main()
