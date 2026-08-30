"""P2P-OPENMONTAGE-VENDOR-01 focused tests.

Offline, deterministic. Verifies the pinned reference-only vendor intake:
exact upstream pin, AGPL license boundary, selective projection into the
existing capability registry/single router, and fail-closed readiness
(no installation, no execution, no runtime-proven claims).
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_ROOT = REPO_ROOT / ".p2p" / "system"
REGISTRY_PATH = SYSTEM_ROOT / "p2p_capabilities" / "capabilities.json"
PROVENANCE_PATH = REPO_ROOT / ".p2p" / "vendor" / "provenance" / "openmontage-vendor-01.json"
CATALOG_PATH = REPO_ROOT / "docs/p2p-development/capability-catalog/openmontage-vendor/capability-catalog.json"

sys.path.insert(0, str(SYSTEM_ROOT))

from p2p_capabilities import load_registry  # noqa: E402
from p2p_capabilities.vendor_skill import (  # noqa: E402
    discover_vendor_skills,
    external_runtime_reference_metadata,
    is_external_runtime_reference,
    load_vendor_skill,
    VendorSkillError,
)

OPENMONTAGE_COMMIT = "cd9f3c1f03368be87b140af494914b8ee4e3c7a4"
OPENMONTAGE_TREE = "6cd1961d552dd9d2bcfba990b80ac06edfe4b061"
OPENMONTAGE_LICENSE = "AGPL-3.0"

SELECTED_IDS = [
    "media.openmontage",
    "media.openmontage.documentary",
    "media.openmontage.explainer",
    "media.openmontage.composition",
    "media.openmontage.audio",
    "media.openmontage.sourcing",
    "media.openmontage.quality",
]

DISCOVERED_ONLY_READINESS = {
    "INSTALLED": False,
    "DISCOVERED": True,
    "ELIGIBLE": False,
    "RESOLVED": False,
    "EXECUTABLE": False,
    "HEALTHY": False,
}


class P2POpenMontageVendor01Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = load_registry(REGISTRY_PATH)
        cls.registry_raw = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        cls.manifests = {item.capability_id: item for item in cls.registry["parsed"]}
        cls.provenance = json.loads(PROVENANCE_PATH.read_text(encoding="utf-8"))
        cls.catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))

    def test_01_exact_upstream_pin_and_license(self) -> None:
        vendor = self.provenance["vendor"]
        self.assertEqual(vendor["upstream_commit"], OPENMONTAGE_COMMIT)
        self.assertEqual(vendor["upstream_tree"], OPENMONTAGE_TREE)
        self.assertEqual(self.provenance["license"]["spdx"], OPENMONTAGE_LICENSE)
        self.assertEqual(self.provenance["license"]["file"], "LICENSE")
        self.assertFalse(self.provenance["license_boundary"]["p2p_core_code_copied"])
        self.assertFalse(self.provenance["license_boundary"]["upstream_source_vendored"])
        self.assertFalse(self.provenance["license_boundary"]["upstream_license_copied_into_p2p"])
        self.assertEqual(self.provenance["vendor_classification"]["canonical_registry_mode"], "PINNED_REFERENCE_ADAPTER")
        self.assertEqual(self.provenance["vendor_classification"]["vendor_class"], "REFERENCE_ONLY_EXTERNAL_RUNTIME_VENDOR")

    def test_02_selected_projection_registered_in_existing_registry(self) -> None:
        self.assertTrue(self.registry["valid"])
        self.assertEqual(self.registry["capability_count"], 72)
        self.assertEqual(tuple(item["CAPABILITY_ID"] for item in self.registry_raw["capabilities"][-7:]), tuple(SELECTED_IDS))
        for capability_id in SELECTED_IDS:
            manifest = self.manifests[capability_id]
            self.assertEqual(manifest.type, "SKILL")
            self.assertEqual(manifest.semantic_kind, "EXTERNAL_RUNTIME")
            self.assertEqual(manifest.status, "DISCOVERED")
            self.assertEqual(manifest.trust_level, "EXTERNAL_SERVICE")
            self.assertFalse(manifest.canonical_quorum_member)
            self.assertFalse(manifest.optional_specialist)
            provenance = manifest.raw["UPSTREAM_PROVENANCE"]
            self.assertEqual(provenance["mode"], "PINNED_REFERENCE_ADAPTER")
            self.assertEqual(provenance["upstream_commit"], OPENMONTAGE_COMMIT)
            self.assertEqual(provenance["upstream_tree"], OPENMONTAGE_TREE)
            self.assertIsNone(provenance["vendor_path"])
            self.assertEqual(provenance["license"]["kind"], OPENMONTAGE_LICENSE)
            self.assertEqual(provenance["integration"]["dependency_mode"], "EXTERNAL_RUNTIME_NOT_INSTALLED")
            self.assertIsNone(provenance["integration"]["entrypoint"])
            self.assertEqual(provenance["integration"]["install_mode"], "DISABLED")
            self.assertIn("owner-gate-before-runtime-invocation", manifest.requires)
            self.assertIn("claim-runtime-proven", manifest.prohibited_actions)
            self.assertIn("vendor-agpl-source-into-p2p-core", manifest.prohibited_actions)

    def test_03_fail_closed_discovery_and_no_execution_path(self) -> None:
        self.assertTrue(all(is_external_runtime_reference(self.manifests[cid]) for cid in SELECTED_IDS))
        # Reference adapters must not be loadable as local vendor skills.
        for capability_id in SELECTED_IDS:
            with self.assertRaises(VendorSkillError):
                load_vendor_skill(
                    capability_id,
                    registry_path=REGISTRY_PATH,
                    repository_root=REPO_ROOT,
                )
            metadata = external_runtime_reference_metadata(self.manifests[capability_id])
            self.assertEqual(metadata["source_state"], "NOT_VENDORED")
            self.assertFalse(metadata["content_loaded"])
            self.assertFalse(metadata["entrypoint_present"])

        result = discover_vendor_skills(
            "Open a documentary montage from archive.org with piper narration",
            registry_path=REGISTRY_PATH,
            repository_root=REPO_ROOT,
        )
        self.assertEqual(result["selected"], [])
        self.assertFalse(result["content_loaded"])
        for skill in result["skills"]:
            if skill["capability_id"] in SELECTED_IDS:
                self.assertEqual(skill["classification"], "NOT_APPLICABLE")
                states = skill["readiness"]["states"]
                self.assertEqual(
                    {name: bool(states[name]) for name in DISCOVERED_ONLY_READINESS},
                    DISCOVERED_ONLY_READINESS,
                )
                self.assertFalse(skill["readiness"]["profile_presence_is_runtime_proof"])

    def test_04_no_agpl_upstream_source_vendored(self) -> None:
        skill_vendor_root = REPO_ROOT / ".p2p" / "vendor" / "skill"
        vendored_openmontage = [path for path in skill_vendor_root.iterdir() if "openmontage" in path.name.lower()]
        self.assertEqual(vendored_openmontage, [])
        for capability_id in SELECTED_IDS:
            manifest = self.manifests[capability_id]
            self.assertIsNone(manifest.raw["UPSTREAM_PROVENANCE"]["vendor_path"])
        self.assertEqual(self.provenance["vendor_classification"]["source_state"], "NOT_VENDORED")

    def test_05_catalog_projection_consistency(self) -> None:
        self.assertEqual(self.catalog["upstream"]["commit"], OPENMONTAGE_COMMIT)
        self.assertEqual(self.catalog["upstream"]["tree"], OPENMONTAGE_TREE)
        self.assertEqual(self.catalog["upstream"]["license"], OPENMONTAGE_LICENSE)
        registered = [group["capability_id"] for group in self.catalog["projected_groups"]]
        self.assertEqual(registered, SELECTED_IDS)
        self.assertEqual(self.catalog["selected_p2p_capabilities"], SELECTED_IDS)
        for group in self.catalog["projected_groups"]:
            lifecycle = group["lifecycle"]
            self.assertFalse(lifecycle["EXECUTION_REGISTERED"])
            self.assertFalse(lifecycle["EXECUTION_AUTHORIZED"])
            self.assertFalse(lifecycle["RUNTIME_PROVEN"])
            self.assertTrue(lifecycle["DISCOVERED"])
            self.assertTrue(lifecycle["PROJECTABLE"])
            self.assertTrue(group["upstream_tools"])
        self.assertTrue(self.catalog["zero_paid_key_route"]["sources"])
        self.assertTrue(self.catalog["zero_paid_key_route"]["runtime"])
        self.assertTrue(self.catalog["deferred_groups"])
        for deferred in self.catalog["deferred_groups"]:
            self.assertIsNone(deferred["capability_id"])

    def test_06_p2p_authority_boundary_preserved(self) -> None:
        boundary = self.catalog["p2p_authority_boundary"]
        self.assertFalse(boundary["second_authority_layer_imported"])
        self.assertFalse(boundary["execution_registered"])
        self.assertFalse(boundary["execution_authorized"])
        for retained in (
            "Control Tower",
            "Work Factory",
            "risk lanes",
            "capability routing",
            "ReturnPacket",
            "Supervisor",
            "Owner Gate",
        ):
            self.assertIn(retained, boundary["p2p_retains"])
        no_execution = self.provenance["no_execution_evidence"]
        self.assertFalse(no_execution["video_rendered"])
        self.assertFalse(no_execution["pip_install"])
        self.assertFalse(no_execution["npm_install"])
        self.assertFalse(no_execution["api_keys_used"])
        self.assertFalse(no_execution["paid_providers_called"])


if __name__ == "__main__":
    unittest.main()
