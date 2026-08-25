from __future__ import annotations

import hashlib
import inspect
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_ROOT = REPO_ROOT / ".p2p" / "system"
REGISTRY_PATH = SYSTEM_ROOT / "p2p_capabilities" / "capabilities.json"
VENDOR_ROOTS = {
    "creative.copywriting": REPO_ROOT / ".p2p" / "vendor" / "skill" / "xiaoma-durex-copywriter-main",
    "media.whiteboard_animation": REPO_ROOT / ".p2p" / "vendor" / "skill" / "srt-whiteboard-animation-main",
}
sys.path.insert(0, str(SYSTEM_ROOT))

from p2p_capabilities import load_registry  # noqa: E402
from p2p_capabilities import vendor_skill  # noqa: E402
from p2p_capabilities.vendor_skill import (  # noqa: E402
    discover_vendor_skills,
    load_vendor_skill,
    optional_dependency_status,
    snapshot_tree_sha256,
)
from p2p_uiux.router import foundation_route  # noqa: E402


class P2PVendorSkillIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = load_registry(REGISTRY_PATH)
        cls.manifests = {
            item.capability_id: item
            for item in cls.registry["parsed"]
            if item.capability_id in VENDOR_ROOTS
        }

    def route(self, request: str) -> dict:
        return discover_vendor_skills(
            request,
            registry_path=REGISTRY_PATH,
            repository_root=REPO_ROOT,
        )

    def test_01_copywriter_advertising_route(self) -> None:
        result = self.route("Write an advertising slogan and campaign headline for a new brand.")
        self.assertEqual(result["selected"], ["creative.copywriting"])
        self.assertFalse(result["content_loaded"])

    def test_02_whiteboard_srt_route(self) -> None:
        result = self.route("Turn this SRT into a whiteboard animation storyboard and render an MP4.")
        self.assertEqual(result["selected"], ["media.whiteboard_animation"])
        self.assertFalse(result["content_loaded"])

    def test_03_copywriter_code_refactor_is_negative(self) -> None:
        for request in ("Refactor this Python code", "Fix the coding issue in this function"):
            with self.subTest(request=request):
                self.assertNotIn("creative.copywriting", self.route(request)["selected"])

    def test_04_copywriter_technical_docs_is_negative(self) -> None:
        for request in ("Write technical documentation for the API", "Document the database schema"):
            with self.subTest(request=request):
                self.assertNotIn("creative.copywriting", self.route(request)["selected"])

    def test_05_copywriter_summary_translation_is_negative(self) -> None:
        for request in ("Summarize this article", "Translate this campaign copy into Vietnamese"):
            with self.subTest(request=request):
                self.assertNotIn("creative.copywriting", self.route(request)["selected"])

    def test_06_copywriter_database_legal_unrelated_is_negative(self) -> None:
        for request in (
            "Design the database migration",
            "Draft a legal contract",
            "Write an unrelated personal note",
        ):
            with self.subTest(request=request):
                self.assertNotIn("creative.copywriting", self.route(request)["selected"])

    def test_07_whiteboard_translation_and_reading_are_negative(self) -> None:
        for request in ("Translate the subtitle file", "Read the SRT aloud"):
            with self.subTest(request=request):
                self.assertNotIn("media.whiteboard_animation", self.route(request)["selected"])

    def test_08_whiteboard_summary_and_timestamp_edits_are_negative(self) -> None:
        for request in ("Summarize the subtitles", "Make a simple timestamp edit"):
            with self.subTest(request=request):
                self.assertNotIn("media.whiteboard_animation", self.route(request)["selected"])

    def test_09_unrelated_request_selects_no_vendor_skill(self) -> None:
        result = self.route("Explain how to choose a PostgreSQL index.")
        self.assertEqual(result["selected"], [])

    def test_10_discovery_is_metadata_only(self) -> None:
        with mock.patch.object(
            vendor_skill,
            "_sha256_file",
            side_effect=AssertionError("discovery must not read vendor content"),
        ):
            result = self.route("Create a brand slogan")
        selected = next(item for item in result["skills"] if item["capability_id"] == "creative.copywriting")
        self.assertTrue(selected["entrypoint_present"])
        self.assertFalse(selected["content_loaded"])

    def test_11_loads_only_selected_entrypoint_and_explicit_context(self) -> None:
        result = load_vendor_skill(
            "creative.copywriting",
            registry_path=REGISTRY_PATH,
            repository_root=REPO_ROOT,
            references=("references/diction.md",),
            assets=("assets/package.json",),
        )
        self.assertEqual(result["status"], "LOADED")
        self.assertEqual(
            result["loaded_paths"],
            ["SKILL.md", "references/diction.md", "assets/package.json"],
        )
        self.assertFalse(result["permission_grant"])
        self.assertFalse(result["network_used"])

    def test_12_core_load_does_not_require_optional_dependencies(self) -> None:
        for capability_id in VENDOR_ROOTS:
            with self.subTest(capability_id=capability_id):
                result = optional_dependency_status(
                    capability_id,
                    operation="load",
                    registry_path=REGISTRY_PATH,
                    repository_root=REPO_ROOT,
                )
                self.assertEqual(result["status"], "NOT_REQUIRED")
                self.assertTrue(result["checked_without_install"])

    def test_13_missing_whiteboard_render_dependency_blocks_closed(self) -> None:
        result = optional_dependency_status(
            "media.whiteboard_animation",
            operation="render",
            registry_path=REGISTRY_PATH,
            repository_root=REPO_ROOT,
        )
        self.assertEqual(result["status"], "BLOCKED_OPTIONAL_DEPENDENCY")
        self.assertIn("vendor-venv", result["missing"])
        self.assertFalse(result["network_used"])

    def test_14_missing_copywriter_render_dependency_blocks_closed(self) -> None:
        result = optional_dependency_status(
            "creative.copywriting",
            operation="render",
            registry_path=REGISTRY_PATH,
            repository_root=REPO_ROOT,
        )
        self.assertEqual(result["status"], "BLOCKED_OPTIONAL_DEPENDENCY")
        self.assertIn("@napi-rs/canvas", result["missing"])
        self.assertFalse(result["network_used"])

    def test_15_vendor_tree_and_entrypoint_hashes_match_registry(self) -> None:
        for capability_id, root in VENDOR_ROOTS.items():
            with self.subTest(capability_id=capability_id):
                manifest = self.manifests[capability_id]
                provenance = manifest.upstream_provenance
                entrypoint = root / "SKILL.md"
                self.assertEqual(snapshot_tree_sha256(root), provenance["snapshot_sha256"])
                self.assertEqual(
                    hashlib.sha256(entrypoint.read_bytes()).hexdigest(),
                    provenance["integration"]["entrypoint_sha256"],
                )

    def test_16_vendor_tree_hash_detects_isolated_mutation(self) -> None:
        source = VENDOR_ROOTS["creative.copywriting"]
        with tempfile.TemporaryDirectory(prefix="p2p-vendor-hash-", dir=REPO_ROOT / ".tmp") as raw:
            clone = Path(raw) / "copywriter"
            shutil.copytree(source, clone)
            original_hash = snapshot_tree_sha256(clone)
            readme = clone / "README.md"
            readme.write_text(readme.read_text(encoding="utf-8") + "\nlocal test mutation\n", encoding="utf-8")
            self.assertNotEqual(original_hash, snapshot_tree_sha256(clone))

    def test_17_provider_neutral_single_router_boundary(self) -> None:
        source = inspect.getsource(vendor_skill).lower()
        for forbidden in (
            "openai",
            "anthropic",
            "gemini",
            "vertex",
            "lumina_api_key",
            "https://",
            "pip install",
            "npm install",
        ):
            self.assertNotIn(forbidden, source)
        route = foundation_route("Create a whiteboard animation from an SRT and render an MP4")
        self.assertTrue(route["single_router"])
        self.assertNotIn("router-agent", repr(route))
        self.assertEqual(route["adaptive_quorum"]["canonical_denominator"], 8)
        self.assertEqual(route["adaptive_quorum"]["full_quorum"], "8/8")
        for item in route["vendor_skills"]["skills"]:
            self.assertFalse(item["network_runtime"])
            self.assertFalse(item["permission_grant"])


if __name__ == "__main__":
    unittest.main()
