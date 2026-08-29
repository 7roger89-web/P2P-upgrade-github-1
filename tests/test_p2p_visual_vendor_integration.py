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
CAPABILITY_ID = "visual.gpt_image_2_style_library"
VENDOR_ROOT = REPO_ROOT / ".p2p" / "vendor" / "skill" / "gpt-image-2-style-library-9a7b2e9"
EXPECTED_SNAPSHOT_HASH = "29121408bbfdd4994ec4738b6ee181c80ba123cb7554c297e8a07091faddc482"
EXPECTED_FILES = (
    "LICENSE",
    "SKILL.md",
    "agents/openai.yaml",
    "docs/disclaimer.md",
    "references/style-library.md",
)
EXPECTED_SOURCE_HASHES = {
    "SKILL.md": "8c628df135c27ef4b7f7a085cdd60868eee2180c21401a89a140b321148f0b2e",
    "agents/openai.yaml": "592f53bfba40639571e45e534245615a453f866822b649cc993578eec442431a",
    "references/style-library.md": "c98f3d9a178670235dd6e37f0bb8ed07eb8d4bb77c56e7e300d44a4f6d50f8bc",
    "LICENSE": "70e109c69f4c92ca03a7d37ac045b4f5584e442004b5eb8b93329e7a1eec7c16",
    "docs/disclaimer.md": "acb1e6b8f0bfa58ff5964ce749a65af20269a8f57bb9d3b4aa849ba55e161e43",
}
EXPECTED_CANONICAL_SOURCE_HASHES = {
    "SKILL.md": "98519a3bfd28c5ab5630771a536f18fbe3627123cd7dd7a8801fa5da166a60f9",
    "agents/openai.yaml": "936761c14357498549796a193cd9243d4366b0a9db39c83492d85dba15abeae3",
    "references/style-library.md": "4d90087cf1dacf7114d063aa56d3d4a03e0097e52914a0bbce4df77907404dd7",
    "LICENSE": "27a75c48bac29eb78f43c19f75c4e175974c8f1046d848d5562eae1ead2f1176",
    "docs/disclaimer.md": "01483f1b50442bd378de9e8221b14bfdd4231008bbac70750521190a1a59c90e",
}
sys.path.insert(0, str(SYSTEM_ROOT))

from p2p_capabilities import CANONICAL_IDENTITIES, load_registry  # noqa: E402
from p2p_capabilities import vendor_skill  # noqa: E402
from p2p_capabilities.host_projection import READY as HOST_READY  # noqa: E402
from p2p_capabilities.host_projection import project_host_skill  # noqa: E402
from p2p_capabilities.manus_skill_package import (  # noqa: E402
    MANUS_MAPPING_STATUS,
    MANUS_RUNTIME_STATUS,
    READY as MANUS_READY,
    export_manus_skill_package,
    plan_manus_skill_package,
)
from p2p_capabilities.vendor_skill import (  # noqa: E402
    VendorSkillError,
    discover_vendor_skills,
    load_vendor_skill,
    optional_dependency_status,
    snapshot_tree_sha256,
    vendor_readiness_snapshot,
)


class P2PVisualVendorIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        (REPO_ROOT / ".tmp").mkdir(parents=True, exist_ok=True)
        cls.registry = load_registry(REGISTRY_PATH)
        cls.manifest = next(
            item for item in cls.registry["parsed"] if item.capability_id == CAPABILITY_ID
        )

    def route(self, request: str) -> dict:
        return discover_vendor_skills(
            request,
            registry_path=REGISTRY_PATH,
            repository_root=REPO_ROOT,
        )

    def test_01_registry_record_is_noncanonical_discovered_and_provider_neutral(self) -> None:
        raw = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        records = [item for item in raw["capabilities"] if item["CAPABILITY_ID"] == CAPABILITY_ID]
        self.assertEqual(len(records), 1)
        record = records[0]
        self.assertEqual(self.registry["capability_count"], 40)
        self.assertEqual(record["TYPE"], "SKILL")
        self.assertEqual(record["INVOCATION_CLASS"], "MODEL_ROUTABLE")
        self.assertFalse(record["CANONICAL_QUORUM_MEMBER"])
        self.assertFalse(record["OPTIONAL_SPECIALIST"])
        self.assertNotIn("PROVIDES", record)
        self.assertEqual(record["STATUS"], "DISCOVERED")
        self.assertEqual(record["UPSTREAM_PROVENANCE"]["mode"], "LOCAL_VENDOR_SNAPSHOT")
        self.assertEqual(record["UPSTREAM_PROVENANCE"]["upstream_commit"], "9a7b2e9c39f816d6c699c2a133e11b6d8bfdc464")
        self.assertEqual(record["UPSTREAM_PROVENANCE"]["upstream_tree"], "56b103dad637a95b9ec366eb7215459f28feb73e")
        self.assertEqual(record["UPSTREAM_PROVENANCE"]["upstream_tag"], "gpt-image-2-style-library-v1.0.4")
        self.assertEqual(record["UPSTREAM_PROVENANCE"]["upstream_tag_binding"], "OBSERVED_TAG_DOES_NOT_EQUAL_PIN")
        self.assertEqual(record["UPSTREAM_PROVENANCE"]["integration"]["load_mode"], "ON_DEMAND")
        self.assertFalse(record["UPSTREAM_PROVENANCE"]["integration"]["network_runtime"])
        self.assertFalse(record["UPSTREAM_PROVENANCE"]["integration"]["credentials"])
        self.assertEqual(record["UPSTREAM_PROVENANCE"]["integration"]["install_mode"], "DISABLED")
        self.assertEqual(record["UPSTREAM_PROVENANCE"]["integration"]["external_render"], "EXPLICIT_ONLY")
        self.assertEqual(
            tuple(self.registry["canonical_identities"]),
            CANONICAL_IDENTITIES,
        )
        self.assertEqual(self.registry["canonical_denominator"], 8)
        self.assertEqual(self.registry["full_quorum"], "8/8")

    def test_02_snapshot_contains_only_allowlisted_files_and_excludes_png(self) -> None:
        actual = tuple(
            sorted(
                path.relative_to(VENDOR_ROOT).as_posix()
                for path in VENDOR_ROOT.rglob("*")
                if path.is_file()
            )
        )
        self.assertEqual(actual, tuple(sorted(EXPECTED_FILES)))
        self.assertFalse((VENDOR_ROOT / "assets" / "city-life-system-map.png").exists())
        self.assertFalse((VENDOR_ROOT / "data").exists())
        self.assertFalse((VENDOR_ROOT / "gallery").exists())
        self.assertFalse((VENDOR_ROOT / "scripts").exists())
        rights = self.manifest.upstream_provenance["rights_review"]
        self.assertEqual(rights["status"], "UNRESOLVED")
        self.assertEqual(rights["png_status"], "EXCLUDED_OR_INACTIVE_RIGHTS_UNRESOLVED")
        source_asset = next(
            item
            for item in self.manifest.upstream_provenance["source_files"]
            if item["role"] == "conditional-asset"
        )
        self.assertIsNone(source_asset["snapshot_path"])
        self.assertEqual(source_asset["status"], "EXCLUDED_OR_INACTIVE_RIGHTS_UNRESOLVED")
        self.assertIn("assets/city-life-system-map.png", (VENDOR_ROOT / "SKILL.md").read_text(encoding="utf-8"))

    def test_03_snapshot_and_declared_source_hashes_match(self) -> None:
        self.assertEqual(snapshot_tree_sha256(VENDOR_ROOT), EXPECTED_SNAPSHOT_HASH)
        self.assertEqual(
            snapshot_tree_sha256(VENDOR_ROOT),
            self.manifest.upstream_provenance["snapshot_sha256"],
        )
        for relative, expected in EXPECTED_SOURCE_HASHES.items():
            with self.subTest(relative=relative):
                self.assertEqual(
                    vendor_skill._sha256_file(VENDOR_ROOT / relative),
                    EXPECTED_CANONICAL_SOURCE_HASHES[relative],
                )
        declared = {
            item["snapshot_path"]: item["canonical_sha256"]
            for item in self.manifest.upstream_provenance["source_files"]
            if item["status"] == "VENDORED"
        }
        self.assertEqual(declared, EXPECTED_CANONICAL_SOURCE_HASHES)
        raw_declared = {
            item["snapshot_path"]: item["sha256"]
            for item in self.manifest.upstream_provenance["source_files"]
            if item["status"] == "VENDORED"
        }
        self.assertEqual(raw_declared, EXPECTED_SOURCE_HASHES)

    def test_04_discovery_is_metadata_only_and_load_is_explicit(self) -> None:
        with mock.patch.object(
            vendor_skill,
            "_sha256_file",
            side_effect=AssertionError("discovery must not read vendor content"),
        ):
            result = self.route("Use the GPT-Image2 style library to make an image prompt.")
        self.assertIn(CAPABILITY_ID, result["selected"])
        selected = next(item for item in result["skills"] if item["capability_id"] == CAPABILITY_ID)
        self.assertTrue(selected["entrypoint_present"])
        self.assertFalse(selected["content_loaded"])
        self.assertFalse(selected["permission_grant"])
        loaded = load_vendor_skill(
            CAPABILITY_ID,
            registry_path=REGISTRY_PATH,
            repository_root=REPO_ROOT,
            references=("agents/openai.yaml", "references/style-library.md"),
        )
        self.assertEqual(
            loaded["loaded_paths"],
            ["SKILL.md", "agents/openai.yaml", "references/style-library.md"],
        )
        self.assertTrue(loaded["content_loaded"])
        self.assertFalse(loaded["permission_grant"])
        self.assertFalse(loaded["network_used"])
        self.assertIn("Template Index", loaded["references"]["references/style-library.md"]["content"])
        with self.assertRaisesRegex(VendorSkillError, "ASSET_NOT_DECLARED"):
            load_vendor_skill(
                CAPABILITY_ID,
                registry_path=REGISTRY_PATH,
                repository_root=REPO_ROOT,
                assets=("assets/city-life-system-map.png",),
            )

    def test_05_mandatory_routing_collision_matrix(self) -> None:
        cases = (
            (
                "Design a cultivation game UI image prompt.",
                {"p2p-uiux", CAPABILITY_ID},
                {CAPABILITY_ID},
            ),
            (
                "Implement the cultivation game UI in code.",
                {"p2p-uiux"},
                set(),
            ),
            (
                "Create a storyboard image prompt.",
                {"media.whiteboard_animation", CAPABILITY_ID},
                {"media.whiteboard_animation", CAPABILITY_ID},
            ),
            (
                "Create/render a whiteboard animation.",
                {"media.whiteboard_animation"},
                {"media.whiteboard_animation"},
            ),
            (
                "Write marketing copy for an image-generation product.",
                {"creative.copywriting"},
                {"creative.copywriting"},
            ),
        )
        for request, expected_route_selected, expected_vendor_selected in cases:
            with self.subTest(request=request):
                result = self.route(request)
                self.assertEqual(set(result["route"]["selected"]), expected_route_selected)
                self.assertEqual(set(result["selected"]), expected_vendor_selected)
                visual = next(
                    item
                    for item in result["route"]["results"]
                    if item["capability_id"] == CAPABILITY_ID
                )
                if request == "Design a cultivation game UI image prompt.":
                    self.assertEqual(visual["classification"], "PRIMARY")
                    self.assertTrue(visual["collision"])
                    self.assertIn("SCOPE_COLLISION_RECORDED", visual["reason_codes"])
                elif request == "Implement the cultivation game UI in code.":
                    self.assertEqual(visual["classification"], "NOT_APPLICABLE")
                    self.assertIn("NEGATIVE_TRIGGER_MATCH", visual["reason_codes"])
                elif request == "Create/render a whiteboard animation.":
                    self.assertEqual(visual["classification"], "NOT_APPLICABLE")
                    self.assertIn("NEGATIVE_TRIGGER_MATCH", visual["reason_codes"])
                elif request == "Write marketing copy for an image-generation product.":
                    self.assertEqual(visual["classification"], "NOT_APPLICABLE")
                    self.assertIn("NEGATIVE_TRIGGER_MATCH", visual["reason_codes"])

        storyboard = self.route("Create a storyboard image prompt.")["route"]["results"]
        whiteboard = next(item for item in storyboard if item["capability_id"] == "media.whiteboard_animation")
        self.assertEqual(whiteboard["classification"], "SECONDARY")
        self.assertFalse(whiteboard["collision"])

    def test_06_progressive_readiness_and_render_boundary_are_closed(self) -> None:
        readiness = vendor_readiness_snapshot(
            self.manifest,
            repository_root=REPO_ROOT,
            registry_path=REGISTRY_PATH,
        )
        self.assertEqual(readiness["state"], "HEALTHY")
        self.assertIn("CONTENT_LOAD_ON_DEMAND", readiness["reasons"])
        self.assertFalse(readiness["profile_presence_is_runtime_proof"])
        with mock.patch.object(
            vendor_skill.subprocess,
            "run",
            side_effect=AssertionError("new visual skill must not execute render subprocesses"),
        ):
            render = optional_dependency_status(
                CAPABILITY_ID,
                operation="render",
                registry_path=REGISTRY_PATH,
                repository_root=REPO_ROOT,
            )
        self.assertEqual(render["status"], "BLOCKED_OPTIONAL_DEPENDENCY")
        self.assertEqual(render["missing"], ["unsupported-optional-operation"])
        self.assertTrue(render["checked_without_install"])
        self.assertFalse(render["network_used"])

    def test_07_snapshot_drift_fails_closed_in_isolated_fixture(self) -> None:
        payload = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory(prefix="p2p-visual-drift-", dir=REPO_ROOT / ".tmp") as raw:
            root = Path(raw)
            fixture = root / "vendor"
            shutil.copytree(VENDOR_ROOT, fixture)
            (fixture / "SKILL.md").write_text(
                (fixture / "SKILL.md").read_text(encoding="utf-8") + "\nfixture drift\n",
                encoding="utf-8",
            )
            record = next(item for item in payload["capabilities"] if item["CAPABILITY_ID"] == CAPABILITY_ID)
            record["UPSTREAM_PROVENANCE"]["vendor_path"] = "vendor"
            registry = root / "capabilities.json"
            registry.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            with self.assertRaisesRegex(VendorSkillError, "VENDOR_SNAPSHOT_HASH_MISMATCH"):
                load_vendor_skill(
                    CAPABILITY_ID,
                    registry_path=registry,
                    repository_root=root,
                )

    def test_08_existing_adapter_stays_provider_neutral_and_single_router(self) -> None:
        source = inspect.getsource(vendor_skill).lower()
        for forbidden in (
            "openai",
            "anthropic",
            "gemini",
            "vertex",
            "lumina_api_key",
            "pip install",
            "npm install",
        ):
            self.assertNotIn(forbidden, source)
        result = self.route("Design a cultivation game UI image prompt.")
        self.assertTrue(result["route"]["single_router"])
        self.assertEqual(result["route"]["adaptive_quorum"]["canonical_denominator"], 8)
        self.assertEqual(result["route"]["adaptive_quorum"]["full_quorum"], "8/8")
        self.assertTrue(all(not item["permission_grant"] for item in result["skills"]))
        self.assertTrue(all(not item["network_runtime"] for item in result["skills"]))

    def test_09_existing_host_projection_preserves_stages_and_mapping_truth(self) -> None:
        loaded = load_vendor_skill(
            CAPABILITY_ID,
            registry_path=REGISTRY_PATH,
            repository_root=REPO_ROOT,
            references=("references/style-library.md",),
        )

        def project(host_kind: str, stage: str, *, target_extra: dict[str, object] | None = None, **extra: object):
            context: dict[str, object] = {
                "load_stage": stage,
                "selected": True,
                "source_hash": EXPECTED_SNAPSHOT_HASH,
            }
            if stage in {"LOAD", "DEEP_LOAD"}:
                context["entrypoint_content"] = loaded["skill"]["content"]
                context["entrypoint_hash"] = loaded["skill"]["sha256"]
            context.update(extra)
            return project_host_skill(
                self.manifest,
                context,
                {"host_kind": host_kind, "scope": "project", **(target_extra or {})},
            )

        discovery = project("codex", "DISCOVERY")
        self.assertEqual(discovery.status, HOST_READY)
        self.assertFalse(discovery.content_loaded)
        self.assertIn("MAPPING_SUPPORTED", discovery.warnings)
        self.assertIn("DISCOVERY_METADATA_ONLY", discovery.warnings)
        match = project("codex", "MATCH")
        self.assertEqual(match.status, HOST_READY)
        self.assertFalse(match.content_loaded)
        self.assertIn("MATCH_ENTRYPOINT_POINTER:SKILL.md", match.warnings)
        loaded_plan = project("codex", "LOAD")
        self.assertEqual(loaded_plan.status, HOST_READY)
        self.assertTrue(loaded_plan.content_loaded)
        self.assertEqual(loaded_plan.source_hash, EXPECTED_SNAPSHOT_HASH)
        self.assertEqual(loaded_plan.entrypoint_hash, "98519a3bfd28c5ab5630771a536f18fbe3627123cd7dd7a8801fa5da166a60f9")
        self.assertTrue(all(not getattr(loaded_plan, field) for field in (
            "writes_performed",
            "provider_mutated",
            "model_mutated",
            "auth_mutated",
            "permission_mutated",
            "task_state_mutated",
        )))
        reference = loaded["references"]["references/style-library.md"]
        deep = project(
            "codex",
            "DEEP_LOAD",
            deep_load=[{
                "requested": True,
                "kind": "reference",
                "relative_path": "references/style-library.md",
                "source_hash": reference["sha256"],
                "content": reference["content"],
            }],
        )
        self.assertEqual(deep.status, HOST_READY)
        self.assertIn("DEEP_LOAD_EXPLICIT_DECLARED_ONLY", deep.warnings)
        self.assertEqual(deep.files[-1].relative_target, ".agents/skills/visual.gpt_image_2_style_library/references/style-library.md")
        self.assertNotIn("data/style-library.json", [item.relative_target for item in deep.files])
        for host_kind in ("claude", "gemini", "cursor", "copilot"):
            extra = {"apply_to": "docs/**/*.md"} if host_kind == "copilot" else {}
            planned = project(host_kind, "LOAD", target_extra=extra)
            self.assertEqual(planned.status, HOST_READY)
            self.assertIn("MAPPING_PLANNED", planned.warnings)
            self.assertIn("MAPPING_PLANNED_NOT_RUNTIME_CERTIFIED", planned.warnings)

    def test_10_existing_manus_projection_stays_not_certified_at_runtime(self) -> None:
        loaded = load_vendor_skill(
            CAPABILITY_ID,
            registry_path=REGISTRY_PATH,
            repository_root=REPO_ROOT,
        )
        context = {
            "load_stage": "LOAD",
            "selected": True,
            "source_hash": EXPECTED_SNAPSHOT_HASH,
            "entrypoint_content": loaded["skill"]["content"],
            "entrypoint_hash": loaded["skill"]["sha256"],
        }
        target = {"host_kind": "manus", "scope": "project"}
        plan = plan_manus_skill_package(
            self.manifest,
            context,
            target,
            registry_path=REGISTRY_PATH,
            repository_root=REPO_ROOT,
        )
        self.assertEqual(plan.status, MANUS_READY)
        self.assertEqual(plan.mapping_status, MANUS_MAPPING_STATUS)
        self.assertEqual(plan.runtime_status, MANUS_RUNTIME_STATUS)
        self.assertEqual(plan.lifecycle_stage, "MAPPING_SUPPORTED")
        self.assertEqual(
            [item.relative_path for item in plan.files],
            ["P2P-PROVENANCE.json", "SKILL.md"],
        )
        provenance = plan.files[0].content_or_descriptor
        self.assertEqual(provenance["source_hash"], EXPECTED_SNAPSHOT_HASH)
        self.assertEqual(provenance["entrypoint_hash"], loaded["skill"]["sha256"])
        self.assertNotIn("provider", json.dumps(provenance).lower())
        self.assertNotIn("model", json.dumps(provenance).lower())
        self.assertFalse(provenance["integration"]["credentials"])
        with tempfile.TemporaryDirectory(prefix="p2p-visual-manus-", dir=REPO_ROOT / ".tmp") as raw:
            exported = export_manus_skill_package(
                self.manifest,
                Path(raw) / "package",
                repository_root=REPO_ROOT,
                registry_path=REGISTRY_PATH,
            )
            self.assertEqual(exported.plan.runtime_status, "NOT_CERTIFIED")
            self.assertTrue(Path(exported.archive_path).is_file())


if __name__ == "__main__":
    unittest.main()
