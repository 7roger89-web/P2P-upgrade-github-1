from __future__ import annotations

import inspect
import json
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
    "visual.gpt_image_2_style_library": REPO_ROOT / ".p2p" / "vendor" / "skill" / "gpt-image-2-style-library-9a7b2e9",
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
        (REPO_ROOT / ".tmp").mkdir(parents=True, exist_ok=True)
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
                    vendor_skill._sha256_file(entrypoint),
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

    @staticmethod
    def _write_snapshot_fixture(root: Path, *, line_ending: bytes = b"\n") -> None:
        (root / "nested").mkdir(parents=True)
        (root / "text.txt").write_bytes(b"alpha" + line_ending + b"beta" + line_ending)
        (root / "nested" / "binary.bin").write_bytes(b"\x89PNG\r\n\x00\xff")

    def test_18_vendor_tree_hash_detects_missing_file(self) -> None:
        with tempfile.TemporaryDirectory(prefix="p2p-vendor-missing-", dir=REPO_ROOT / ".tmp") as raw:
            root = Path(raw) / "snapshot"
            self._write_snapshot_fixture(root)
            original_hash = snapshot_tree_sha256(root)
            (root / "text.txt").unlink()
            self.assertNotEqual(original_hash, snapshot_tree_sha256(root))

    def test_19_vendor_tree_hash_detects_unexpected_included_file(self) -> None:
        with tempfile.TemporaryDirectory(prefix="p2p-vendor-extra-", dir=REPO_ROOT / ".tmp") as raw:
            root = Path(raw) / "snapshot"
            self._write_snapshot_fixture(root)
            original_hash = snapshot_tree_sha256(root)
            (root / "unexpected.txt").write_bytes(b"unexpected\n")
            self.assertNotEqual(original_hash, snapshot_tree_sha256(root))

    def test_20_vendor_tree_hash_detects_path_set_drift(self) -> None:
        with tempfile.TemporaryDirectory(prefix="p2p-vendor-paths-", dir=REPO_ROOT / ".tmp") as raw:
            root = Path(raw) / "snapshot"
            self._write_snapshot_fixture(root)
            original_hash = snapshot_tree_sha256(root)
            (root / "text.txt").rename(root / "renamed.txt")
            self.assertNotEqual(original_hash, snapshot_tree_sha256(root))

    def test_21_stale_registry_identity_fails_closed(self) -> None:
        payload = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        for item in payload["capabilities"]:
            if item.get("CAPABILITY_ID") == "creative.copywriting":
                item["UPSTREAM_PROVENANCE"]["snapshot_sha256"] = "0" * 64
                break
        with tempfile.TemporaryDirectory(prefix="p2p-vendor-registry-", dir=REPO_ROOT / ".tmp") as raw:
            registry = Path(raw) / "capabilities.json"
            registry.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            with self.assertRaisesRegex(vendor_skill.VendorSkillError, "VENDOR_SNAPSHOT_HASH_MISMATCH"):
                load_vendor_skill(
                    "creative.copywriting",
                    registry_path=registry,
                    repository_root=REPO_ROOT,
                )

    def test_22_lf_and_crlf_materialize_same_canonical_snapshot_identity(self) -> None:
        with tempfile.TemporaryDirectory(prefix="p2p-vendor-eol-", dir=REPO_ROOT / ".tmp") as raw:
            root = Path(raw)
            lf_root = root / "lf"
            crlf_root = root / "crlf"
            self._write_snapshot_fixture(lf_root, line_ending=b"\n")
            self._write_snapshot_fixture(crlf_root, line_ending=b"\r\n")
            self.assertEqual(snapshot_tree_sha256(lf_root), snapshot_tree_sha256(crlf_root))

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
