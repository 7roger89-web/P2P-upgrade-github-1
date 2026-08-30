"""P2P-GAME-ASSET-FORGE-01 focused tests."""

from __future__ import annotations

import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = REPO_ROOT / "docs/p2p-development/capability-catalog/game-asset-forge/capability-catalog.json"
UI_CATALOG_PATH = REPO_ROOT / "docs/p2p-development/capability-catalog/ui-game-threejs/capability-catalog.json"
ROUTING_PATH = REPO_ROOT / "docs/p2p-development/capability-catalog/ui-game-threejs/project-profile-routing.json"
CAPABILITIES_PATH = REPO_ROOT / ".p2p/system/p2p_capabilities/capabilities.json"
LEDGER_PATH = REPO_ROOT / "governance/research-adoption-ledger.json"
PROTOCOL_PATH = REPO_ROOT / "docs/p2p-development/capability-catalog/protocols/asset-forge-protocol.md"
BOOTSTRAP_PATH = REPO_ROOT / "docs/p2p-development/capability-catalog/bootstrap-projection.md"
ARENA_BOOTSTRAP_PATH = REPO_ROOT / "docs/p2p-development/P2P-PROJECT-BOOTSTRAP.md"

NEW_IDS = [
    "game.character.generate",
    "game.character.rig",
    "game.character.runtime",
    "game.character.expression",
    "game.animation.motion_forge",
    "game.animation.retarget",
    "game.vfx.particles",
    "game.vfx.shader",
    "game.world.terrain",
    "game.world.vegetation",
]
REUSED = [
    "img2threejs",
    "visual.gpt_image_2_style_library",
    "game.three.asset",
    "game.mengto.hybrid_assets",
    "game.mengto.rigged_assets",
    "game.mengto.performance",
]


class TestAssetForgeCatalog(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        self.ui_catalog = json.loads(UI_CATALOG_PATH.read_text(encoding="utf-8"))
        self.routing = json.loads(ROUTING_PATH.read_text(encoding="utf-8"))
        self.caps = json.loads(CAPABILITIES_PATH.read_text(encoding="utf-8"))
        self.ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))

    def test_identity_uniqueness(self) -> None:
        ids = [c["candidate_id"] for c in self.catalog["candidates"]]
        self.assertEqual(len(ids), 19)
        self.assertEqual(len(ids), len(set(ids)))
        cap_ids = [c["CAPABILITY_ID"] for c in self.caps["capabilities"]]
        self.assertEqual(len(cap_ids), len(set(cap_ids)))

    def test_no_ontology_duplication(self) -> None:
        self.assertEqual(self.catalog["schema"], self.ui_catalog["schema"])
        self.assertEqual(self.catalog["parent_catalog"], "docs/p2p-development/capability-catalog/ui-game-threejs/capability-catalog.json")
        self.assertNotIn("game.asset.reference", {c["CAPABILITY_ID"] for c in self.caps["capabilities"]})
        self.assertNotIn("game.asset.image_to_3d", {c["CAPABILITY_ID"] for c in self.caps["capabilities"]})
        self.assertEqual(self.catalog["conceptual_aliases"]["game.asset.reference"], "visual.gpt_image_2_style_library")
        self.assertEqual(self.catalog["conceptual_aliases"]["game.asset.image_to_3d"], "img2threejs")
        self.assertEqual(self.catalog["conceptual_aliases"]["game.asset.optimization"], "game.mengto.performance")

    def test_classification_correctness(self) -> None:
        by_id = {c["candidate_id"]: c for c in self.catalog["candidates"]}
        self.assertEqual(by_id["CAND-ASSET-FORGE-007"]["verdict"], "ACCEPT")
        self.assertEqual(by_id["CAND-ASSET-FORGE-008"]["verdict"], "ACCEPT")
        self.assertEqual(by_id["CAND-ASSET-FORGE-015"]["verdict"], "ACCEPT")
        self.assertEqual(by_id["CAND-ASSET-FORGE-018"]["verdict"], "ACCEPT")
        self.assertEqual(by_id["CAND-ASSET-FORGE-017"]["verdict"], "REFERENCE_ONLY")
        self.assertEqual(by_id["CAND-ASSET-FORGE-019"]["verdict"], "REFERENCE_ONLY")
        self.assertEqual(by_id["CAND-ASSET-FORGE-013"]["verdict"], "CONDITIONAL")
        self.assertEqual(by_id["CAND-ASSET-FORGE-014"]["verdict"], "CONDITIONAL")
        self.assertFalse(any(c["verdict"] == "REJECT" for c in self.catalog["candidates"]))
        self.assertFalse(any(c["global_install"] for c in self.catalog["candidates"]))
        counts = {}
        for c in self.catalog["candidates"]:
            counts[c["verdict"]] = counts.get(c["verdict"], 0) + 1
        self.assertEqual(counts["ACCEPT"], 4)
        self.assertEqual(counts["CONDITIONAL"], 13)
        self.assertEqual(counts["REFERENCE_ONLY"], 2)

    def test_license_model_weight_dataset_security_gates(self) -> None:
        gates = self.catalog["gates"]
        self.assertIn("LICENSE_GATES", gates)
        self.assertIn("MODEL_WEIGHT_GATES", gates)
        self.assertIn("DATASET_GATES", gates)
        self.assertIn("SECURITY_GATES", gates)
        img = next(c for c in self.catalog["candidates"] if c["candidate_id"] == "CAND-ASSET-FORGE-008")
        self.assertFalse(img["img2threejs_security_semantics_altered"])
        self.assertIn("do_not_alter_img2threejs_security_semantics", gates["SECURITY_GATES"])
        char = next(c for c in self.catalog["candidates"] if c["candidate_id"] == "CAND-ASSET-FORGE-001")
        self.assertIn("Cannot redistribute raw VRM", char["dataset_license_dependencies"])
        frog = next(c for c in self.catalog["candidates"] if c["candidate_id"] == "CAND-ASSET-FORGE-017")
        self.assertEqual(frog["code_license"], "UNKNOWN")

    def test_routing(self) -> None:
        web = self.routing["profiles"]["WEB_APP"]["excluded_capabilities"]
        for cap in NEW_IDS + ["img2threejs"]:
            self.assertIn(cap, web)
        three = self.routing["profiles"]["THREEJS_GAME"]["optional_capabilities"]
        r3f = self.routing["profiles"]["R3F_GAME"]["optional_capabilities"]
        for cap in NEW_IDS:
            self.assertIn(cap, three)
            self.assertIn(cap, r3f)
            self.assertNotIn(cap, self.routing["profiles"]["THREEJS_GAME"]["required_capabilities"])

    def test_offline_forge_runtime_separation(self) -> None:
        contract = self.catalog["offline_forge_contract"]
        self.assertFalse(contract["heavy_ai_in_shipped_runtime"])
        self.assertIn("GLB", contract["durable_outputs"])
        self.assertIn("VRM", contract["durable_outputs"])
        runtime = next(c for c in self.catalog["candidates"] if c["candidate_id"] == "CAND-ASSET-FORGE-007")
        self.assertEqual(runtime["integration_mode"], "LIGHTWEIGHT_GAME_RUNTIME")
        trellis = next(c for c in self.catalog["candidates"] if c["candidate_id"] == "CAND-ASSET-FORGE-011")
        self.assertEqual(trellis["integration_mode"], "OFFLINE_ASSET_FORGE_METADATA_ONLY")

    def test_pipelines_and_boundary(self) -> None:
        p = self.catalog["pipelines"]
        self.assertEqual(p["CHARACTER_PIPELINE"][0], "IMAGEGEN_REFERENCE")
        self.assertIn("RIG_SKIN", p["CHARACTER_PIPELINE"])
        self.assertIn("IMG2THREEJS_OR_APPROVED_RECONSTRUCTION", p["WEAPON_PROP_PIPELINE"])
        self.assertIn("APPROVED_MOTION_SOURCE", p["MOTION_PIPELINE"])
        self.assertIn("PERFORMANCE_GATE", p["VFX_PIPELINE"])
        self.assertIn("VEGETATION_INSTANCING", p["TERRAIN_PIPELINE"])
        boundary = self.catalog["threejs_procedural_boundary"]
        self.assertIn("terrain", boundary["appropriate"])
        self.assertIn("hero characters", boundary["not_default_final_asset"])
        protocol = PROTOCOL_PATH.read_text(encoding="utf-8")
        self.assertIn("GENERATION != RIGGING != SKINNING != RUNTIME != MOTION != EXPRESSION", protocol)
        self.assertIn("Do not alter img2threejs security semantics", protocol)

    def test_img2threejs_and_style_library_preserved(self) -> None:
        by_id = {c["CAPABILITY_ID"]: c for c in self.caps["capabilities"]}
        img = by_id["img2threejs"]
        self.assertEqual(img["UPSTREAM_PROVENANCE"]["upstream_commit"], "dede5909be4e494b228c801a55dda47439143932")
        self.assertFalse(img["UPSTREAM_PROVENANCE"]["execution"]["shell"])
        self.assertTrue(img["UPSTREAM_PROVENANCE"]["execution"]["state_evidence_workspace_only"])
        style = by_id["visual.gpt_image_2_style_library"]
        self.assertEqual(style["UPSTREAM_PROVENANCE"]["rights_review"]["commercial_clearance"], "UNKNOWN")
        for reused in REUSED:
            self.assertIn(reused, by_id)
        for new in NEW_IDS:
            self.assertIn(new, by_id)
            self.assertFalse(by_id[new]["CANONICAL_QUORUM_MEMBER"])
            self.assertEqual(by_id[new]["TYPE"], "KNOWLEDGE_SOURCE")

    def test_ledger_and_arena_bootstrap(self) -> None:
        ids = {r["research_id"] for r in self.ledger["records"]}
        for i in range(50, 69):
            self.assertIn(f"RA-EXT-{i:03d}", ids)
        bootstrap = BOOTSTRAP_PATH.read_text(encoding="utf-8")
        self.assertIn("Asset Forge Protocol", bootstrap)
        arena = ARENA_BOOTSTRAP_PATH.read_text(encoding="utf-8")
        self.assertIn("game-asset-forge/capability-catalog.json", arena)
        self.assertIn("asset-forge-protocol.md", arena)


if __name__ == "__main__":
    unittest.main()
