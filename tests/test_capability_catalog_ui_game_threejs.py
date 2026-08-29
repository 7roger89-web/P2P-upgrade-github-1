"""P2P-GAME-UI-CAP-01: Capability catalog validation tests.

Validates:
- Catalog schema correctness
- Unique capability IDs
- Project-profile routing invariants
- Vanilla Three.js does not inherit R3F-only dependencies
- WEB_APP does not inherit game capabilities by default
- Gated candidates cannot become executable projection automatically
- License metadata preserved per candidate/package
- Theatre core/studio license distinction
- Penpot archived upstream not treated as current
- detect-gpu stale-data caveat preserved
- Bootstrap discovers relevant projected protocols
- Existing unrelated project profiles remain unchanged
"""

import json
import os
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
CATALOG_PATH = REPO_ROOT / "docs" / "p2p-development" / "capability-catalog" / "ui-game-threejs" / "capability-catalog.json"
ROUTING_PATH = REPO_ROOT / "docs" / "p2p-development" / "capability-catalog" / "ui-game-threejs" / "project-profile-routing.json"
CAPABILITIES_PATH = REPO_ROOT / ".p2p" / "system" / "p2p_capabilities" / "capabilities.json"
LEDGER_PATH = REPO_ROOT / "governance" / "research-adoption-ledger.json"
UI_DESIGN_PROTOCOL_PATH = REPO_ROOT / "docs" / "p2p-development" / "capability-catalog" / "protocols" / "ui-design-protocol.md"
GAME_UI_PROTOCOL_PATH = REPO_ROOT / "docs" / "p2p-development" / "capability-catalog" / "protocols" / "game-ui-protocol.md"
THREEJS_VISUAL_PROTOCOL_PATH = REPO_ROOT / "docs" / "p2p-development" / "capability-catalog" / "protocols" / "threejs-visual-protocol.md"
BOOTSTRAP_PATH = REPO_ROOT / "docs" / "p2p-development" / "capability-catalog" / "bootstrap-projection.md"


class TestCatalogSchema(unittest.TestCase):
    """Validate the capability catalog JSON schema."""

    def setUp(self):
        with open(CATALOG_PATH, "r", encoding="utf-8") as f:
            self.catalog = json.load(f)

    def test_catalog_loads(self):
        self.assertIn("schema", self.catalog)
        self.assertEqual(self.catalog["schema"], "p2p-capability-catalog/1")

    def test_catalog_has_candidates(self):
        self.assertIn("candidates", self.catalog)
        self.assertGreater(len(self.catalog["candidates"]), 0)

    def test_candidate_ids_unique(self):
        ids = [c["candidate_id"] for c in self.catalog["candidates"]]
        self.assertEqual(len(ids), len(set(ids)), f"Duplicate candidate IDs found: {[i for i in ids if ids.count(i) > 1]}")

    def test_all_required_candidate_fields(self):
        required_fields = [
            "candidate_id", "source_name", "source_type", "license",
            "capability_domains", "classification", "project_profiles_applicable",
            "global_install"
        ]
        for c in self.catalog["candidates"]:
            for field in required_fields:
                self.assertIn(field, c, f"Missing field '{field}' in {c['candidate_id']}")

    def test_classification_vocabulary(self):
        allowed = set(self.catalog["classification_vocabulary"])
        for c in self.catalog["candidates"]:
            self.assertIn(
                c["classification"], allowed,
                f"Invalid classification '{c['classification']}' for {c['candidate_id']}"
            )

    def test_no_global_install(self):
        for c in self.catalog["candidates"]:
            self.assertFalse(
                c["global_install"],
                f"{c['candidate_id']} must not be globally installed"
            )

    def test_project_profiles_valid(self):
        allowed_profiles = set(self.catalog["project_profiles"])
        for c in self.catalog["candidates"]:
            for p in c["project_profiles_applicable"]:
                self.assertIn(p, allowed_profiles, f"Invalid profile '{p}' in {c['candidate_id']}")


class TestProjectProfileRouting(unittest.TestCase):
    """Validate project profile routing rules."""

    def setUp(self):
        with open(ROUTING_PATH, "r", encoding="utf-8") as f:
            self.routing = json.load(f)

    def test_routing_loads(self):
        self.assertIn("schema", self.routing)
        self.assertEqual(self.routing["schema"], "p2p-project-profile-routing/1")

    def test_all_profiles_present(self):
        expected = {"WEB_APP", "MOBILE_APP", "2D_GAME", "THREEJS_GAME", "R3F_GAME"}
        self.assertEqual(set(self.routing["profiles"].keys()), expected)

    def test_web_app_no_game_capabilities(self):
        """WEB_APP must not inherit game capabilities by default."""
        web = self.routing["profiles"]["WEB_APP"]
        excluded = set(web["excluded_capabilities"])
        game_caps = {
            "ui.game_hud", "ui.spatial",
            "game.three.visual", "game.three.asset", "game.three.cinematic",
            "game.three.spatial_query", "game.three.navigation",
            "game.three.adaptive_quality", "game.three.scene_authoring"
        }
        for cap in game_caps:
            self.assertIn(cap, excluded, f"WEB_APP must exclude {cap}")

    def test_threejs_game_no_r3f_only(self):
        """THREEJS_GAME must not automatically receive R3F-only capabilities."""
        threejs = self.routing["profiles"]["THREEJS_GAME"]
        excluded = set(threejs["excluded_capabilities"])
        self.assertIn("ui.spatial", excluded, "THREEJS_GAME must exclude ui.spatial (R3F-only)")

    def test_2d_game_no_threejs(self):
        """2D_GAME must not receive Three.js capabilities."""
        game2d = self.routing["profiles"]["2D_GAME"]
        excluded = set(game2d["excluded_capabilities"])
        threejs_caps = {
            "ui.spatial", "game.three.visual", "game.three.asset",
            "game.three.cinematic", "game.three.spatial_query",
            "game.three.navigation", "game.three.adaptive_quality",
            "game.three.scene_authoring"
        }
        for cap in threejs_caps:
            self.assertIn(cap, excluded, f"2D_GAME must exclude {cap}")

    def test_projection_invariants_present(self):
        invariants = self.routing["projection_invariants"]
        self.assertGreater(len(invariants), 0)
        # Check key invariants are present
        invariant_text = " ".join(invariants)
        self.assertIn("WEB_APP", invariant_text)
        self.assertIn("THREEJS_GAME", invariant_text)
        self.assertIn("R3F", invariant_text)

    def test_gated_capabilities_declared(self):
        """Each profile must declare gated capabilities."""
        for profile_name, profile in self.routing["profiles"].items():
            self.assertIn("gated_capabilities", profile,
                          f"{profile_name} must declare gated_capabilities")


class TestCapabilityRegistry(unittest.TestCase):
    """Validate the extended capabilities.json registry."""

    def setUp(self):
        with open(CAPABILITIES_PATH, "r", encoding="utf-8") as f:
            self.caps = json.load(f)

    def test_capabilities_load(self):
        self.assertIn("capabilities", self.caps)
        self.assertGreater(len(self.caps["capabilities"]), 39)  # more than original 39

    def test_capability_ids_unique(self):
        ids = [c["CAPABILITY_ID"] for c in self.caps["capabilities"]]
        self.assertEqual(len(ids), len(set(ids)), f"Duplicate capability IDs found")

    def test_new_ui_capabilities_present(self):
        ids = {c["CAPABILITY_ID"] for c in self.caps["capabilities"]}
        expected_new = [
            "ui.design", "ui.design_system", "ui.frontend", "ui.motion",
            "ui.component_lab", "ui.game_hud", "ui.spatial", "ui.penpot_bridge",
            "game.three.visual", "game.three.asset", "game.three.cinematic",
            "game.three.spatial_query", "game.three.navigation",
            "game.three.adaptive_quality", "game.three.scene_authoring"
        ]
        for cap_id in expected_new:
            self.assertIn(cap_id, ids, f"Missing capability: {cap_id}")

    def test_no_canonical_quorum_member_added(self):
        """New capabilities must not be canonical quorum members."""
        for c in self.caps["capabilities"]:
            if c["CAPABILITY_ID"].startswith("ui.") or c["CAPABILITY_ID"].startswith("game.three."):
                self.assertFalse(
                    c.get("CANONICAL_QUORUM_MEMBER", False),
                    f"{c['CAPABILITY_ID']} must not be a canonical quorum member"
                )

    def test_theatre_license_split_preserved(self):
        """game.three.cinematic must preserve Theatre core/studio license distinction."""
        cinematic = None
        for c in self.caps["capabilities"]:
            if c["CAPABILITY_ID"] == "game.three.cinematic":
                cinematic = c
                break
        self.assertIsNotNone(cinematic, "game.three.cinematic must exist")
        prov = cinematic.get("UPSTREAM_PROVENANCE", {})
        license_text = prov.get("license", "")
        self.assertIn("Apache-2.0", license_text, "Must reference Apache-2.0 for core")
        self.assertIn("AGPL-3.0", license_text, "Must reference AGPL-3.0 for studio")
        self.assertIn("LICENSE SPLIT", prov.get("license_note", ""),
                       "Must note LICENSE SPLIT")

    def test_detect_gpu_stale_data_caveat(self):
        """game.three.adaptive_quality must preserve stale data caveat."""
        adaptive = None
        for c in self.caps["capabilities"]:
            if c["CAPABILITY_ID"] == "game.three.adaptive_quality":
                adaptive = c
                break
        self.assertIsNotNone(adaptive, "game.three.adaptive_quality must exist")
        prov = adaptive.get("UPSTREAM_PROVENANCE", {})
        caveat = prov.get("stale_data_caveat", "")
        self.assertIn("gfxbench.com", caveat, "Must reference gfxbench.com stale data")
        self.assertIn("December 2025", caveat, "Must reference December 2025")

    def test_penpot_security_gated(self):
        """ui.penpot_bridge must be security-gated."""
        penpot = None
        for c in self.caps["capabilities"]:
            if c["CAPABILITY_ID"] == "ui.penpot_bridge":
                penpot = c
                break
        self.assertIsNotNone(penpot, "ui.penpot_bridge must exist")
        self.assertIn("security-gate-mcp-review", penpot.get("APPROVAL_BOUNDARY", []))
        prov = penpot.get("UPSTREAM_PROVENANCE", {})
        self.assertIn("SECURITY_GATED", prov.get("security_note", ""))

    def test_existing_capabilities_unchanged(self):
        """Existing canonical capabilities must still be present."""
        ids = {c["CAPABILITY_ID"] for c in self.caps["capabilities"]}
        canonical = [
            "p2p_iris", "p2p_tecton", "p2p_axiom", "p2p_vector",
            "p2p_datos", "p2p_anon", "p2p_architecton", "p2p_helios",
            "p2p-uiux", "p2p_aesthetica"
        ]
        for cap_id in canonical:
            self.assertIn(cap_id, ids, f"Existing canonical capability missing: {cap_id}")


class TestResearchAdoptionLedger(unittest.TestCase):
    """Validate extended research adoption ledger."""

    def setUp(self):
        with open(LEDGER_PATH, "r", encoding="utf-8") as f:
            self.ledger = json.load(f)

    def test_ledger_loads(self):
        self.assertIn("records", self.ledger)

    def test_new_records_present(self):
        ids = {r["research_id"] for r in self.ledger["records"]}
        for i in range(32, 50):
            self.assertIn(f"RA-EXT-{i:03d}", ids, f"Missing RA-EXT-{i:03d}")

    def test_theatre_license_split_in_ledger(self):
        theatre_record = None
        for r in self.ledger["records"]:
            if r["research_id"] == "RA-EXT-038":
                theatre_record = r
                break
        self.assertIsNotNone(theatre_record)
        notes = theatre_record.get("notes", "")
        self.assertIn("Apache-2.0", notes)
        self.assertIn("AGPL-3.0", notes)
        combined = " ".join([
            theatre_record.get("p2p_translation", ""),
            theatre_record.get("notes", ""),
            " ".join(theatre_record.get("rejected_ideas", []))
        ])
        self.assertTrue(
            "Do NOT flatten" in combined or "flatten" in combined.lower(),
            "Theatre record must preserve license split warning"
        )

    def test_penpot_archived_not_current(self):
        penpot_record = None
        for r in self.ledger["records"]:
            if r["research_id"] == "RA-EXT-044":
                penpot_record = r
                break
        self.assertIsNotNone(penpot_record)
        self.assertIn("archived", penpot_record.get("notes", "").lower())
        self.assertIn("SECURITY_GATED", penpot_record.get("owner_decision_status", ""))

    def test_detect_gpu_stale_caveat_in_ledger(self):
        detect_gpu_record = None
        for r in self.ledger["records"]:
            if r["research_id"] == "RA-EXT-040":
                detect_gpu_record = r
                break
        self.assertIsNotNone(detect_gpu_record)
        notes = detect_gpu_record.get("notes", "")
        self.assertIn("gfxbench.com", notes)
        self.assertIn("December 2025", notes)


class TestProtocols(unittest.TestCase):
    """Validate protocol documents exist and contain required content."""

    def test_ui_design_protocol_exists(self):
        self.assertTrue(UI_DESIGN_PROTOCOL_PATH.exists())

    def test_ui_design_protocol_content(self):
        content = UI_DESIGN_PROTOCOL_PATH.read_text(encoding="utf-8")
        self.assertIn("VISUAL DIRECTION", content)
        self.assertIn("CODE_PASS != VISUAL_PASS", content)
        self.assertIn("COMPONENT_FOUNDATION != VISUAL_DIRECTION", content)

    def test_game_ui_protocol_exists(self):
        self.assertTrue(GAME_UI_PROTOCOL_PATH.exists())

    def test_game_ui_protocol_content(self):
        content = GAME_UI_PROTOCOL_PATH.read_text(encoding="utf-8")
        self.assertIn("GAMEPLAY-CRITICAL HUD", content)
        self.assertIn("CONTEXTUAL HUD", content)
        self.assertIn("WORLD/GAME_VIEW", content)
        self.assertTrue("DOM overlay" in content or "dom overlay" in content.lower())

    def test_threejs_visual_protocol_exists(self):
        self.assertTrue(THREEJS_VISUAL_PROTOCOL_PATH.exists())

    def test_threejs_visual_protocol_content(self):
        content = THREEJS_VISUAL_PROTOCOL_PATH.read_text(encoding="utf-8")
        self.assertIn("game.three.visual", content)
        self.assertIn("game.three.spatial_query", content)
        self.assertIn("game.three.navigation", content)
        self.assertIn("game.three.adaptive_quality", content)
        self.assertIn("game.three.cinematic", content)
        self.assertIn("GPU_TIER = HEURISTIC", content)


class TestBootstrapProjection(unittest.TestCase):
    """Validate bootstrap/projection guidance."""

    def test_bootstrap_exists(self):
        self.assertTrue(BOOTSTRAP_PATH.exists())

    def test_bootstrap_content(self):
        content = BOOTSTRAP_PATH.read_text(encoding="utf-8")
        self.assertIn("WEB_APP", content)
        self.assertIn("MOBILE_APP", content)
        self.assertIn("2D_GAME", content)
        self.assertIn("THREEJS_GAME", content)
        self.assertIn("R3F_GAME", content)
        self.assertIn("PROJECTED_BUNDLE", content)


if __name__ == "__main__":
    unittest.main()
