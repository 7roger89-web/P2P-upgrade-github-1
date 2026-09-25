from __future__ import annotations

import hashlib
import json
import re
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_ROOT = REPO_ROOT / ".p2p" / "system"
REGISTRY_PATH = SYSTEM_ROOT / "p2p_capabilities" / "capabilities.json"
SKILL_ROOT = REPO_ROOT / ".agents" / "skills" / "security-audit"
CAPABILITY_ID = "security.audit"
UPSTREAM_COMMIT = "c1c8a8c1471069fb0e188eeaff69b8e8db6564a8"
UPSTREAM_TREE = "8cd03bb3941496e441d6248aaae2429a35b93cc3"

sys.path.insert(0, str(SYSTEM_ROOT))

from p2p_capabilities import load_registry  # noqa: E402
from p2p_capabilities import vendor_skill  # noqa: E402
from p2p_capabilities.vendor_skill import (  # noqa: E402
    discover_vendor_skills,
    load_vendor_skill,
    snapshot_tree_sha256,
)


def canonical_sha256(path: Path) -> str:
    data = path.read_bytes()
    if b"\x00" not in data:
        data = data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(data).hexdigest()


class P2PSecurityAuditSkillTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        loaded = load_registry(REGISTRY_PATH)
        cls.manifest = next(item for item in loaded["parsed"] if item.capability_id == CAPABILITY_ID)
        cls.provenance = json.loads((SKILL_ROOT / "PROVENANCE.json").read_text(encoding="utf-8"))

    def route(self, request: str) -> dict:
        return discover_vendor_skills(
            request,
            registry_path=REGISTRY_PATH,
            repository_root=REPO_ROOT,
        )

    def test_01_registered_noncanonical_provider_neutral_three_mode_skill(self) -> None:
        self.assertEqual(self.manifest.type, "SKILL")
        self.assertFalse(self.manifest.canonical_quorum_member)
        self.assertFalse(self.manifest.optional_specialist)
        upstream = self.manifest.upstream_provenance
        self.assertEqual(upstream["mode"], "LOCAL_VENDOR_SNAPSHOT")
        self.assertEqual(upstream["vendor_path"], ".agents/skills/security-audit")
        self.assertEqual(upstream["upstream_commit"], UPSTREAM_COMMIT)
        self.assertEqual(upstream["upstream_tree"], UPSTREAM_TREE)
        self.assertEqual(
            upstream["integration"]["operating_modes"],
            ["FINDING_VALIDATION", "FOCUSED_REVIEW", "FULL_AUDIT"],
        )
        self.assertFalse(upstream["integration"]["network_runtime"])
        self.assertFalse(upstream["integration"]["credentials"])
        self.assertEqual(upstream["integration"]["install_mode"], "DISABLED")

    def test_02_security_requests_route_without_loading_content(self) -> None:
        for request in (
            "validate this suspected auth bypass in middleware",
            "security review this API for BOLA and access control vulnerability",
            "security audit this entire codebase",
            "find vulnerabilities in this API",
        ):
            with self.subTest(request=request):
                result = self.route(request)
                self.assertIn(CAPABILITY_ID, result["selected"])
                self.assertFalse(result["content_loaded"])

    def test_03_ordinary_authorization_or_unrelated_requests_do_not_route(self) -> None:
        for request in (
            "implement OAuth authorization code flow",
            "explain the HTTP Authorization header",
            "write a marketing slogan for a cafe",
        ):
            with self.subTest(request=request):
                self.assertNotIn(CAPABILITY_ID, self.route(request)["selected"])
        self.assertNotIn("authorization", self.manifest.triggers)
        self.assertIn("authorization vulnerability", self.manifest.triggers)

    def test_04_snapshot_and_entrypoint_hashes_are_bound(self) -> None:
        upstream = self.manifest.upstream_provenance
        self.assertEqual(snapshot_tree_sha256(SKILL_ROOT), upstream["snapshot_sha256"])
        self.assertEqual(
            vendor_skill._sha256_file(SKILL_ROOT / "SKILL.md"),
            upstream["integration"]["entrypoint_sha256"],
        )
        self.assertEqual(
            upstream["integration"]["entrypoint_sha256"],
            self.provenance["projection_entrypoint_sha256"],
        )
        loaded = load_vendor_skill(
            CAPABILITY_ID,
            registry_path=REGISTRY_PATH,
            repository_root=REPO_ROOT,
            references=("PROVENANCE.json", "upstream/WEB-PROTOCOL-AND-AUTH.md"),
        )
        self.assertEqual(loaded["status"], "LOADED")
        self.assertFalse(loaded["permission_grant"])
        self.assertFalse(loaded["network_used"])

    def test_05_exact_upstream_files_match_recorded_hashes(self) -> None:
        self.assertEqual(self.provenance["upstream_commit"], UPSTREAM_COMMIT)
        self.assertEqual(self.provenance["upstream_tree"], UPSTREAM_TREE)
        self.assertEqual(
            self.provenance["upstream_commit_verification"],
            {"verified": False, "reason": "unsigned"},
        )
        for item in self.provenance["source_files"]:
            with self.subTest(path=item["snapshot_path"]):
                path = SKILL_ROOT / item["snapshot_path"]
                self.assertTrue(path.is_file())
                self.assertEqual(canonical_sha256(path), item["sha256"])
                self.assertEqual(item["status"], "VENDORED_EXACT")

        subset_entries = [
            f'{item["snapshot_path"]}\n{item["sha256"]}'
            for item in sorted(self.provenance["source_files"], key=lambda item: item["snapshot_path"])
        ]
        subset_hash = hashlib.sha256("\n".join(subset_entries).encode("utf-8")).hexdigest()
        self.assertEqual(subset_hash, self.provenance["upstream_subset_sha256"])
        self.assertEqual(subset_hash, self.manifest.upstream_provenance["upstream_subset_sha256"])

    def test_06_wrapper_exposes_operating_and_result_contracts_with_safety(self) -> None:
        text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertLessEqual(len(text.splitlines()), 150)
        match = re.search(r"^description:\s*(.+)$", text, flags=re.MULTILINE)
        self.assertIsNotNone(match)
        self.assertLess(len(match.group(1)), 200)
        for required in (
            "FINDING_VALIDATION",
            "FOCUSED_REVIEW",
            "FULL_AUDIT",
            "SECURITY_AUDIT_MODE=",
            "SECURITY_AUDIT_SCOPE=",
            "RESULT=PASS_NO_CONFIRMED_FINDINGS",
            "FINDINGS_CONFIRMED",
            "BLOCKED_VALIDATION",
            "CONFIRMED_FINDINGS=",
            "NEEDS_VALIDATION=",
            "REJECTED_CANDIDATES=",
            "external networking disabled",
            "do not execute target code",
            "needs_validation",
            "Never probe deployed endpoints",
            "install dependencies",
            "hunter self-confirm",
        ):
            self.assertIn(required, text)

    def test_07_external_source_and_release_packaging_are_registered(self) -> None:
        external = json.loads((REPO_ROOT / "manifest" / "external-sources.json").read_text(encoding="utf-8"))
        record = next(item for item in external["sources"] if item["source_id"] == "P2P-EXT-0006")
        self.assertEqual(record["capability_id"], CAPABILITY_ID)
        self.assertEqual(record["upstream_commit"], UPSTREAM_COMMIT)
        self.assertEqual(record["sha256"], self.manifest.upstream_provenance["snapshot_sha256"])

        package_text = (REPO_ROOT / "scripts" / "package_release.py").read_text(encoding="utf-8")
        block = re.search(r"RELEASE_SKILLS = \((.*?)\)\nCOPYTREE_IGNORE", package_text, flags=re.DOTALL)
        self.assertIsNotNone(block)
        self.assertIn('"security-audit"', block.group(1))


if __name__ == "__main__":
    unittest.main()
