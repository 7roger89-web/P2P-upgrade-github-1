from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_ROOT = REPO_ROOT / ".p2p" / "system"
REGISTRY_PATH = SYSTEM_ROOT / "p2p_capabilities" / "capabilities.json"
PROVENANCE_PATH = REPO_ROOT / ".p2p" / "vendor" / "provenance" / "p2p-openmaic-intake-01.json"
EXTERNAL_MANIFEST_PATH = REPO_ROOT / "manifest" / "external-sources.json"
CATALOG_PATH = REPO_ROOT / "docs" / "p2p-development" / "capability-catalog" / "education-course" / "capability-catalog.json"

OPENMAIC_COMMIT = "dfebbcf33f3a56064129903faeab70a9e4243146"
OPENMAIC_TREE = "bb8972cb6fa5e4d6c5a7eff6f2357e79bf930b45"
RELEASE_TAG_COMMIT = "aa2bfb3c1d406c47100c6744d90e788abdf1f6d5"

PROJECTED_IDS = (
    "education.course_generation",
    "education.interactive_classroom",
    "education.course_editing",
    "education.quiz_assessment",
    "education.interactive_simulation",
    "education.course_export",
)

sys.path.insert(0, str(SYSTEM_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from p2p_capabilities import load_registry  # noqa: E402


class P2POpenMAICIntake01Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = load_registry(REGISTRY_PATH)
        cls.manifests = {item.capability_id: item for item in cls.registry["parsed"]}
        cls.provenance = json.loads(PROVENANCE_PATH.read_text(encoding="utf-8"))
        cls.external_manifest = json.loads(EXTERNAL_MANIFEST_PATH.read_text(encoding="utf-8"))
        cls.catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))

    def test_01_provenance_pins_verified_upstream_identity_and_license_boundaries(self) -> None:
        upstream = self.provenance["upstream"]
        self.assertEqual(upstream["repository"], "https://github.com/THU-MAIC/OpenMAIC.git")
        self.assertEqual(upstream["current_commit"], OPENMAIC_COMMIT)
        self.assertEqual(upstream["current_tree"], OPENMAIC_TREE)
        self.assertEqual(upstream["release_tag"], "v1.0.0")
        self.assertEqual(upstream["release_commit"], RELEASE_TAG_COMMIT)
        self.assertEqual(upstream["main_vs_release_tag"], "MAIN_IS_8_COMMITS_AHEAD_OF_TAG")
        self.assertEqual(upstream["root_license"], "MIT")
        boundaries = {
            item["component"]: item.get("license") or item.get("licenses")
            for item in self.provenance["third_party_license_boundaries"]
        }
        self.assertEqual(boundaries["packages/mathml2omml"], "LGPL-3.0-or-later")
        self.assertEqual(boundaries["packages/pptxgenjs"], "MIT")
        self.assertEqual(boundaries["render-service"], "UNSPECIFIED")

    def test_02_intake_only_no_install_no_runtime_no_vendoring(self) -> None:
        installation = self.provenance["installation"]
        self.assertFalse(installation["installed"])
        self.assertFalse(installation["pnpm_install_run"])
        self.assertFalse(installation["runtime_started"])
        self.assertFalse(installation["classroom_generated"])
        self.assertFalse(installation["downstream_projects_modified"])
        self.assertFalse(self.provenance["vendor_tree_copied"])
        self.assertIsNone(self.provenance["vendor_snapshot_path"])
        self.assertIsNone(self.provenance["vendor_snapshot_sha256"])
        self.assertEqual(self.provenance["execution_status"], "NOT_EXECUTED")
        self.assertEqual(self.provenance["integration_status"], "INTAKE_AUDITED_PROJECTABLE_PENDING_EXECUTION_REGISTRATION")
        self.assertEqual(self.provenance["owner_gate_status"], "PENDING_EXACT_SUBJECT_REVIEW")
        self.assertTrue(self.provenance["readiness_boundary"]["static_inspection_is_not_runtime_proof"])
        self.assertFalse(self.provenance["readiness_boundary"]["runtime_smoke_required"] == "EXECUTED")
        self.assertEqual(self.provenance["authority_boundary"]["openmaic_multi_agent_authority"], "VENDOR_INTERNAL_ONLY")

    def test_03_registry_entries_are_discovered_projectable_not_registered(self) -> None:
        self.assertEqual(self.registry["capability_count"], 71)
        self.assertTrue(self.registry["valid"])
        registry_ids = [item.capability_id for item in self.registry["parsed"]]
        self.assertEqual(len(registry_ids), len(set(registry_ids)))
        for cap_id in PROJECTED_IDS:
            manifest = self.manifests[cap_id]
            self.assertEqual(manifest.type, "BACKEND_PROVIDER")
            self.assertEqual(manifest.semantic_kind, "EXTERNAL_RUNTIME")
            self.assertEqual(manifest.status, "DISCOVERED")
            self.assertFalse(manifest.canonical_quorum_member)
            self.assertFalse(manifest.optional_specialist)
            self.assertIn("existing-p2p-router", manifest.authority)
            self.assertIn("promote-without-owner-gate", manifest.prohibited_actions)
            provenance = manifest.raw["UPSTREAM_PROVENANCE"]
            self.assertEqual(provenance["mode"], "EXTERNAL_VENDOR_INTAKE_ONLY")
            self.assertEqual(provenance["upstream_commit"], OPENMAIC_COMMIT)
            self.assertEqual(provenance["upstream_tree"], OPENMAIC_TREE)
            self.assertFalse(provenance["vendored"])
            self.assertFalse(provenance["execution_registered"])
            self.assertFalse(provenance["execution_authorized"])
            self.assertFalse(provenance["runtime_proven"])
            self.assertEqual(provenance["execution_status"], "NOT_EXECUTED")
            self.assertEqual(provenance["root_license"], "MIT")
            self.assertIn("packages/mathml2omml: LGPL-3.0-or-later", provenance["third_party_license_boundaries"])
            self.assertEqual(provenance["source_manifest"], ".p2p/vendor/provenance/p2p-openmaic-intake-01.json")

    def test_04_external_source_candidate_and_catalog_are_bound(self) -> None:
        candidate = next(
            item for item in self.external_manifest["candidate_sources"]
            if item["source_id"] == "P2P-EXT-CANDIDATE-OPENMAIC-01"
        )
        self.assertEqual(candidate["url"], "https://github.com/THU-MAIC/OpenMAIC.git")
        self.assertEqual(candidate["upstream_commit"], OPENMAIC_COMMIT)
        self.assertEqual(candidate["upstream_tree"], OPENMAIC_TREE)
        self.assertFalse(candidate["vendored"])
        self.assertEqual(candidate["integration_status"], "INTAKE_AUDITED_PROJECTABLE_PENDING_EXECUTION_REGISTRATION")
        self.assertEqual(candidate["execution_status"], "NOT_EXECUTED")
        self.assertEqual(tuple(candidate["projected_capability_ids"]), PROJECTED_IDS)

        self.assertEqual(self.catalog["vendor"]["pinned_commit"], OPENMAIC_COMMIT)
        self.assertEqual(self.catalog["vendor"]["pinned_tree"], OPENMAIC_TREE)
        self.assertEqual(self.catalog["vendor"]["vendored"], False)
        for projected in self.catalog["projected_capabilities"]:
            self.assertTrue(projected["discovered"])
            self.assertTrue(projected["projectable"])
            self.assertFalse(projected["execution_registered"])
            self.assertFalse(projected["execution_authorized"])
            self.assertFalse(projected["runtime_proven"])
            self.assertEqual(projected["registry_status"], "DISCOVERED")

    def test_05_static_inspection_never_claims_runtime_proven(self) -> None:
        statuses = set(
            f"{cap_id}:{item.raw['UPSTREAM_PROVENANCE']['execution_status']}"
            for cap_id, item in self.manifests.items()
            if cap_id in PROJECTED_IDS
        )
        self.assertEqual(statuses, {f"{cap_id}:NOT_EXECUTED" for cap_id in PROJECTED_IDS})
        self.assertNotIn("RUNTIME_PROVEN", json.dumps(self.provenance["selective_projection"]))
        self.assertIn("selective_projection", self.provenance)


if __name__ == "__main__":
    unittest.main()
