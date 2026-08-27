"""Focused P2P-CT01 protected-runtime reconciliation tests."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TEMP_PARENT = REPO_ROOT / ".tmp"
CONTROL_TOWER_MODULE = ".p2p/system/p2p_capabilities/control_tower_handoff.py"
CONTROL_TOWER_GUIDE = "docs/p2p-development/CONTROL-TOWER-SESSION-HANDOFF.md"
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import p2p_governance  # noqa: E402


class P2PCT01GovernanceLockReconciliationTests(unittest.TestCase):
    @staticmethod
    def _temporary_directory(prefix: str) -> tempfile.TemporaryDirectory[str]:
        TEMP_PARENT.mkdir(parents=True, exist_ok=True)
        return tempfile.TemporaryDirectory(dir=TEMP_PARENT, prefix=prefix)

    def test_exact_control_tower_binding_is_present_and_current(self) -> None:
        policy = json.loads((REPO_ROOT / "governance" / "drift-policy.json").read_text(encoding="utf-8"))
        self.assertIn(CONTROL_TOWER_MODULE, policy["package_protected_paths"])
        self.assertIn(CONTROL_TOWER_MODULE, policy["installed_protected_paths"])
        self.assertNotIn(".p2p/system", policy["package_protected_paths"])
        self.assertNotIn(".p2p/system/p2p_capabilities", policy["package_protected_paths"])
        self.assertNotIn(".p2p/system", policy["installed_protected_paths"])
        self.assertNotIn(".p2p/system/p2p_capabilities", policy["installed_protected_paths"])

        lock = json.loads((REPO_ROOT / "governance" / "runtime-manifest.lock.json").read_text(encoding="utf-8"))
        manifest = p2p_governance.runtime_manifest(REPO_ROOT, REPO_ROOT / "governance")
        self.assertEqual(len(lock["protected_files"]), len(manifest["protected_files"]))
        self.assertEqual(len(lock["virtual_hashes"]), len(manifest["virtual_hashes"]))
        for relative in (CONTROL_TOWER_MODULE, CONTROL_TOWER_GUIDE):
            path = REPO_ROOT / Path(relative)
            self.assertEqual(lock["protected_files"][relative], p2p_governance.sha256(path), relative)

        self.assertEqual(
            p2p_governance.verify_runtime_manifest(REPO_ROOT, REPO_ROOT / "governance"),
            [],
        )

    def test_installed_mode_uses_the_same_exact_module_binding(self) -> None:
        policy = json.loads((REPO_ROOT / "governance" / "drift-policy.json").read_text(encoding="utf-8"))
        with self._temporary_directory("ct01-installed-lock-") as temp_name:
            root = Path(temp_name)
            governance = root / ".p2p" / "system" / "governance"
            module = root / Path(CONTROL_TOWER_MODULE)
            governance.mkdir(parents=True)
            module.parent.mkdir(parents=True)
            (governance / "drift-policy.json").write_text(
                json.dumps(policy) + "\n",
                encoding="utf-8",
            )
            module.write_text("provider-neutral test module\n", encoding="utf-8")

            manifest = p2p_governance.runtime_manifest(root, governance)

            self.assertEqual(manifest["root_mode"], "installed")
            self.assertIn(CONTROL_TOWER_MODULE, manifest["protected_files"])
            self.assertEqual(
                manifest["protected_files"][CONTROL_TOWER_MODULE],
                p2p_governance.sha256(module),
            )
            self.assertIn(".p2p/system/governance/drift-policy.json", manifest["protected_files"])

    def _package_fixture(self) -> tuple[tempfile.TemporaryDirectory[str], Path, Path]:
        temporary = self._temporary_directory("ct01-fail-closed-")
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

    def test_changed_protected_file_is_rejected_fail_closed(self) -> None:
        temporary, root, governance = self._package_fixture()
        try:
            (root / "runtime" / "seed.txt").write_text("changed\n", encoding="utf-8")
            failures = p2p_governance.verify_runtime_manifest(root, governance)
            self.assertTrue(any("protected runtime files changed" in item for item in failures))
        finally:
            temporary.cleanup()

    def test_added_unlocked_file_is_rejected_fail_closed(self) -> None:
        temporary, root, governance = self._package_fixture()
        try:
            (root / "runtime" / "unexpected.txt").write_text("unauthorized\n", encoding="utf-8")
            failures = p2p_governance.verify_runtime_manifest(root, governance)
            self.assertTrue(any("unlocked runtime files added" in item for item in failures))
        finally:
            temporary.cleanup()


if __name__ == "__main__":
    unittest.main()
