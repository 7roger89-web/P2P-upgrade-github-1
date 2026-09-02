from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_ROOT = REPO_ROOT / ".p2p" / "system"
REGISTRY_PATH = SYSTEM_ROOT / "p2p_capabilities" / "capabilities.json"
PROVENANCE_PATH = REPO_ROOT / ".p2p" / "vendor" / "provenance" / "p2p-social-content-skills-01.json"
PROJECTION_ROOTS = {
    "creative.social.voice_profile": REPO_ROOT / ".p2p" / "vendor" / "skill" / "charlie-social-voice-profile-d2e9487",
    "creative.social.post": REPO_ROOT / ".p2p" / "vendor" / "skill" / "charlie-social-post-d2e9487",
    "creative.social.hook": REPO_ROOT / ".p2p" / "vendor" / "skill" / "charlie-social-hook-d2e9487",
    "creative.social.content_matrix": REPO_ROOT / ".p2p" / "vendor" / "skill" / "charlie-social-content-matrix-d2e9487",
    "creative.social.post_format": REPO_ROOT / ".p2p" / "vendor" / "skill" / "charlie-social-post-format-d2e9487",
}
UPSTREAM_CONTENT_HASHES = {
    "creative.social.voice_profile": "7f47bd4b5c131331be274abed100d21e4021aa7d90ac29802f18f39891de2b5a",
    "creative.social.post": "a0c91645648df1cb933489fd3ef0c50fed196661c5374d95dadf637407866c1f",
    "creative.social.hook": "efe43558494cec04cf3dd1080c0e5560fee8cae1093f3082d2f7f2f1525e6e27",
    "creative.social.content_matrix": "dae28fbfc83e66afd2c8f90cb6eb396b0c0aaaddade999820b204dc273161ed6",
    "creative.social.post_format": "9af34ac7b8936dce15f6f7076bfcd06cd0bbac16ca35b6eaa81625e665685bc8",
}
EXPECTED_UPSTREAM_COMMIT = "d2e948719eafc8ed9e2436357ad18489bb371a81"
EXPECTED_UPSTREAM_TREE = "f11c2f93bc1ff3d927e36842f0bb40ea1b639650"
EXPECTED_LICENSE_HASH = "ed17713237d18555a34c208bf0cb1ce347faa937731d509e265ce91be660e218"

sys.path.insert(0, str(SYSTEM_ROOT))

from p2p_capabilities import ContextPointer, load_registry, resolve_context  # noqa: E402
from p2p_capabilities import vendor_skill  # noqa: E402
from p2p_capabilities.vendor_skill import (  # noqa: E402
    discover_vendor_skills,
    load_vendor_skill,
    optional_dependency_status,
    snapshot_tree_sha256,
)
from p2p_uiux.router import foundation_route  # noqa: E402


class P2PSocialContentSkillsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = load_registry(REGISTRY_PATH)
        cls.manifests = {
            item.capability_id: item
            for item in cls.registry["parsed"]
            if item.capability_id in PROJECTION_ROOTS
        }

    def route(self, request: str) -> dict:
        return discover_vendor_skills(
            request,
            registry_path=REGISTRY_PATH,
            repository_root=REPO_ROOT,
        )

    def test_01_registry_has_five_unique_on_demand_capabilities(self) -> None:
        self.assertTrue(self.registry["valid"])
        self.assertEqual(self.registry["canonical_denominator"], 8)
        self.assertEqual(self.registry["full_quorum"], "8/8")
        self.assertEqual(set(PROJECTION_ROOTS), set(self.manifests))
        self.assertNotIn("creative.prose.humanize", self.registry["identities"])
        for capability_id, manifest in self.manifests.items():
            with self.subTest(capability_id=capability_id):
                self.assertEqual(manifest.type, "SKILL")
                self.assertEqual(manifest.invocation_class, "MODEL_ROUTABLE")
                self.assertFalse(manifest.canonical_quorum_member)
                self.assertFalse(manifest.optional_specialist)
                integration = manifest.upstream_provenance["integration"]
                self.assertEqual(integration["load_mode"], "ON_DEMAND")
                self.assertEqual(integration["selection_mode"], "ROUTE_SELECTED_ONLY")
                self.assertEqual(integration["dependency_mode"], "NONE")
                self.assertEqual(integration["references"], [])
                self.assertEqual(integration["assets"], [])
                self.assertEqual(integration["script_entrypoints"], [])
                self.assertFalse(integration["network_runtime"])
                self.assertFalse(integration["credentials"])
                self.assertFalse(integration["provider_runtime"])
                self.assertEqual(manifest.upstream_provenance["upstream_commit"], EXPECTED_UPSTREAM_COMMIT)
                self.assertEqual(manifest.upstream_provenance["upstream_tree"], EXPECTED_UPSTREAM_TREE)

    def test_02_expected_requests_select_one_smallest_capability(self) -> None:
        cases = (
            ("Learn my writing voice from these samples.", "creative.social.voice_profile"),
            ("Write a LinkedIn post about AI agents in my voice.", "creative.social.post"),
            ("Give me 6 hooks about AI agents.", "creative.social.hook"),
            ("Give me 20 content ideas.", "creative.social.content_matrix"),
            ("Format this as AIDA.", "creative.social.post_format"),
        )
        for request, expected in cases:
            with self.subTest(request=request):
                result = self.route(request)
                self.assertEqual(result["selected"], [expected])
                self.assertEqual(result["route"]["selected"], [expected])
                self.assertFalse(result["content_loaded"])
                selected = next(item for item in result["skills"] if item["capability_id"] == expected)
                self.assertTrue(selected["entrypoint_present"])
                self.assertFalse(selected["content_loaded"])

    def test_03_existing_marketing_copywriting_stays_separate(self) -> None:
        result = self.route("Write an advertising slogan and campaign headline for a new brand.")
        self.assertEqual(result["selected"], ["creative.copywriting"])
        self.assertNotIn("creative.social.post", result["selected"])
        self.assertNotIn("creative.social.hook", result["selected"])
        copywriting = self.registry["parsed"][
            self.registry["identities"].index("creative.copywriting")
        ]
        self.assertIn("marketing-copy-output", copywriting.authority)
        self.assertIn("double semantic", copywriting.raw["DESCRIPTION"] + " " + " ".join(copywriting.triggers))

    def test_04_discovery_is_metadata_only_and_does_not_read_entrypoints(self) -> None:
        with mock.patch.object(
            vendor_skill,
            "_sha256_file",
            side_effect=AssertionError("discovery must not read vendor content"),
        ):
            result = self.route("")
        self.assertEqual(result["selected"], [])
        self.assertFalse(result["content_loaded"])
        discovered = {item["capability_id"]: item for item in result["skills"]}
        for capability_id in PROJECTION_ROOTS:
            with self.subTest(capability_id=capability_id):
                self.assertTrue(discovered[capability_id]["entrypoint_present"])
                self.assertFalse(discovered[capability_id]["content_loaded"])
                self.assertFalse(discovered[capability_id]["permission_grant"])
                self.assertFalse(discovered[capability_id]["network_runtime"])

    def test_05_loading_one_selected_capability_does_not_read_other_roots(self) -> None:
        selected_id = "creative.social.post"
        selected_root = PROJECTION_ROOTS[selected_id].resolve()
        other_roots = tuple(root.resolve() for cid, root in PROJECTION_ROOTS.items() if cid != selected_id)
        calls: list[Path] = []
        original = vendor_skill._sha256_file

        def record(path: Path) -> str:
            calls.append(path.resolve())
            return original(path)

        with mock.patch.object(vendor_skill, "_sha256_file", side_effect=record):
            loaded = load_vendor_skill(
                selected_id,
                registry_path=REGISTRY_PATH,
                repository_root=REPO_ROOT,
            )
        self.assertEqual(loaded["loaded_paths"], ["SKILL.md"])
        self.assertTrue(loaded["content_loaded"])
        self.assertFalse(loaded["permission_grant"])
        self.assertFalse(loaded["network_used"])
        self.assertTrue(calls)
        self.assertTrue(all(path.is_relative_to(selected_root) for path in calls))
        self.assertFalse(any(path.is_relative_to(other) for path in calls for other in other_roots))

    def test_06_existing_context_pointer_can_feed_downstream_social_writer(self) -> None:
        pointer = ContextPointer(
            "creative.social.voice_profile",
            "Selected voice profile",
            ("voice", "social post"),
            "PROJECT_CONTEXT",
            ("content-studio",),
            "CURRENT",
            "OWNER",
            content_class="CONTENT",
            load_policy="ON_RESOLVE",
            sensitive=True,
            source_binding="synthetic-voice-profile",
            source_hash="a" * 64,
        )
        resolved = resolve_context(
            [pointer],
            "Draft a social post in my voice",
            scope="content-studio",
            now="2026-09-02T00:00:00+00:00",
        )
        self.assertEqual([item["pointer_id"] for item in resolved["selected"]], ["creative.social.voice_profile"])
        self.assertFalse(resolved["content_grants_permissions"])
        for capability_id in (
            "creative.social.post",
            "creative.social.hook",
            "creative.social.content_matrix",
            "creative.social.post_format",
        ):
            with self.subTest(capability_id=capability_id):
                self.assertIn("creative.social.voice_profile", self.manifests[capability_id].context_pointers)

    def test_07_voice_profile_requires_evidence_and_has_no_default_author(self) -> None:
        root = PROJECTION_ROOTS["creative.social.voice_profile"]
        content = (root / "SKILL.md").read_text(encoding="utf-8")
        for required in (
            "at least three",
            "user",
            "INCOMPLETE",
            "about-me",
            "voice-profile",
            "absence signals",
            "Private sample text stays",
        ):
            with self.subTest(required=required):
                self.assertIn(required, content)
        self.assertIn("Never load a starter corpus", content)
        self.assertNotIn("references/sample-content.md", content)
        self.assertNotIn("Charlie Hills", content)

    def test_08_humanizer_remains_distinct_optional_downstream_prose_polish(self) -> None:
        voice = self.manifests["creative.social.voice_profile"]
        self.assertNotIn("creative.prose.humanize", voice.requires)
        content = (PROJECTION_ROOTS["creative.social.voice_profile"] / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("creative.prose.humanize", content)
        self.assertIn("independent", content)
        self.assertIn("optional downstream", content)
        for capability_id in ("creative.social.post", "creative.social.hook", "creative.social.content_matrix", "creative.social.post_format"):
            with self.subTest(capability_id=capability_id):
                downstream = (PROJECTION_ROOTS[capability_id] / "SKILL.md").read_text(encoding="utf-8")
                self.assertIn("creative.prose.humanize", downstream)
                self.assertTrue("automatically" in downstream or "by default" in downstream)

    def test_09_projection_and_load_results_are_deterministic(self) -> None:
        for capability_id in PROJECTION_ROOTS:
            with self.subTest(capability_id=capability_id):
                first = load_vendor_skill(capability_id, registry_path=REGISTRY_PATH, repository_root=REPO_ROOT)
                second = load_vendor_skill(capability_id, registry_path=REGISTRY_PATH, repository_root=REPO_ROOT)
                self.assertEqual(
                    json.dumps(first, ensure_ascii=False, sort_keys=True),
                    json.dumps(second, ensure_ascii=False, sort_keys=True),
                )
                first_snapshot = snapshot_tree_sha256(PROJECTION_ROOTS[capability_id])
                second_snapshot = snapshot_tree_sha256(PROJECTION_ROOTS[capability_id])
                self.assertEqual(first_snapshot, second_snapshot)

    def test_10_optional_operations_are_offline_and_fail_closed(self) -> None:
        with mock.patch.object(vendor_skill.subprocess, "run", side_effect=AssertionError("no subprocess is allowed")):
            for capability_id in PROJECTION_ROOTS:
                with self.subTest(capability_id=capability_id):
                    result = optional_dependency_status(
                        capability_id,
                        operation="load",
                        registry_path=REGISTRY_PATH,
                        repository_root=REPO_ROOT,
                    )
                    self.assertEqual(result["status"], "NOT_REQUIRED")
                    self.assertTrue(result["checked_without_install"])
                    self.assertFalse(result["network_used"])

    def test_11_no_global_activation_and_single_router_boundary(self) -> None:
        for request in ("", "Explain how to choose a PostgreSQL index.", "Write a paragraph about clean code."):
            with self.subTest(request=request):
                result = self.route(request)
                self.assertFalse(set(result["selected"]) & set(PROJECTION_ROOTS))
                self.assertFalse(result["content_loaded"])
        routed = foundation_route("Give me 6 hooks about AI agents.")
        self.assertTrue(routed["single_router"])
        self.assertEqual(routed["selected"], ["creative.social.hook"])
        self.assertEqual(routed["vendor_skills"]["selected"], ["creative.social.hook"])
        self.assertEqual(routed["adaptive_quorum"]["canonical_denominator"], 8)
        self.assertEqual(routed["adaptive_quorum"]["full_quorum"], "8/8")

    def test_12_sparse_projection_excludes_raw_upstream_and_private_metadata(self) -> None:
        provenance = json.loads(PROVENANCE_PATH.read_text(encoding="utf-8"))
        self.assertFalse(provenance["projection_policy"]["raw_upstream_skill_files_vendored"])
        self.assertFalse(provenance["projection_policy"]["user_sample_text_in_metadata"])
        self.assertEqual(provenance["projection_policy"]["retained_upstream_files"], ["LICENSE"])
        for capability_id, root in PROJECTION_ROOTS.items():
            with self.subTest(capability_id=capability_id):
                self.assertEqual(
                    sorted(path.name for path in root.iterdir()),
                    ["LICENSE", "SKILL.md"],
                )
                projection = (root / "SKILL.md").read_text(encoding="utf-8")
                self.assertNotIn("AskUserQuestion", projection)
                self.assertNotIn("Cowork", projection)
                self.assertNotIn("Claude", projection)
                self.assertNotIn("Gemini", projection)
                self.assertNotIn("APIFY_API_TOKEN", projection)
                self.assertNotIn("GOOGLE_AI_API_KEY", projection)
                self.assertNotIn("pip install", projection.lower())
                self.assertNotIn("npm install", projection.lower())
                self.assertNotIn("git clone", projection.lower())
                self.assertNotEqual(
                    self.manifests[capability_id].upstream_provenance["adaptation"]["upstream_content_sha256"],
                    self.manifests[capability_id].upstream_provenance["integration"]["entrypoint_sha256"],
                )
                self.assertEqual(
                    self.manifests[capability_id].upstream_provenance["adaptation"]["upstream_content_sha256"],
                    UPSTREAM_CONTENT_HASHES[capability_id],
                )
                self.assertEqual(vendor_skill._sha256_file(root / "LICENSE"), EXPECTED_LICENSE_HASH)
        self.assertEqual(provenance["upstream"]["license"]["sha256"], EXPECTED_LICENSE_HASH)


if __name__ == "__main__":
    unittest.main()
