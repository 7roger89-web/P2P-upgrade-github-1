from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_ROOT = REPO_ROOT / ".p2p" / "system"
REGISTRY_PATH = SYSTEM_ROOT / "p2p_capabilities" / "capabilities.json"
sys.path.insert(0, str(SYSTEM_ROOT))

from p2p_capabilities import load_registry  # noqa: E402
from p2p_capabilities.manus_skill_package import (  # noqa: E402
    BLOCKED,
    MANUS_MAPPING_STATUS,
    MANUS_RUNTIME_STATUS,
    READY,
    export_manus_skill_package,
    plan_manus_skill_package,
)
from p2p_capabilities.vendor_skill import load_vendor_skill  # noqa: E402


CAPABILITIES = (
    "creative.copywriting",
    "media.whiteboard_animation",
    "visual.gpt_image_2_style_library",
)


class P2PManusSkillPackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        registry = load_registry(REGISTRY_PATH)
        cls.manifests = {
            item.capability_id: item
            for item in registry["parsed"]
            if item.capability_id in CAPABILITIES
        }
        cls.loaded = {
            capability_id: load_vendor_skill(
                capability_id,
                registry_path=REGISTRY_PATH,
                repository_root=REPO_ROOT,
            )
            for capability_id in CAPABILITIES
        }

    def target(self, **extra: object) -> dict[str, object]:
        value: dict[str, object] = {"host_kind": "manus", "scope": "project"}
        value.update(extra)
        return value

    def context(self, capability_id: str, stage: str = "LOAD", **extra: object) -> dict[str, object]:
        loaded = self.loaded[capability_id]
        manifest = self.manifests[capability_id]
        value: dict[str, object] = {
            "load_stage": stage,
            "selected": True,
            "source_hash": manifest.upstream_provenance["snapshot_sha256"],
        }
        if stage in {"LOAD", "DEEP_LOAD"}:
            value.update({
                "entrypoint_content": loaded["skill"]["content"],
                "entrypoint_hash": loaded["skill"]["sha256"],
            })
        value.update(extra)
        return value

    def test_01_both_real_capabilities_map_to_manus_without_runtime_certification(self) -> None:
        for capability_id in CAPABILITIES:
            plan = plan_manus_skill_package(
                self.manifests[capability_id],
                self.context(capability_id),
                self.target(),
                registry_path=REGISTRY_PATH,
                repository_root=REPO_ROOT,
            )
            self.assertEqual(plan.status, READY)
            self.assertEqual(plan.host_kind, "manus")
            self.assertEqual(plan.mapping_status, MANUS_MAPPING_STATUS)
            self.assertEqual(plan.runtime_status, MANUS_RUNTIME_STATUS)
            self.assertEqual(plan.lifecycle_stage, "MAPPING_SUPPORTED")
            self.assertEqual([item.relative_path for item in plan.files], ["P2P-PROVENANCE.json", "SKILL.md"])
            self.assertTrue(plan.files[1].content_or_descriptor.startswith("---"))
            self.assertEqual(plan.files[0].content_or_descriptor["schema"], "p2p-manus-skill-provenance/1")

    def test_02_progressive_disclosure_is_preserved(self) -> None:
        discovery = plan_manus_skill_package(
            self.manifests["creative.copywriting"],
            self.context("creative.copywriting", "DISCOVERY"),
            self.target(),
            registry_path=REGISTRY_PATH,
            repository_root=REPO_ROOT,
        )
        self.assertEqual(discovery.status, READY)
        self.assertFalse(discovery.content_loaded)
        self.assertTrue(all(item.content_or_descriptor is None for item in discovery.files))
        match = plan_manus_skill_package(
            self.manifests["creative.copywriting"],
            self.context("creative.copywriting", "MATCH"),
            self.target(),
            registry_path=REGISTRY_PATH,
            repository_root=REPO_ROOT,
        )
        self.assertFalse(match.content_loaded)
        self.assertIn("MATCH_ENTRYPOINT_POINTER:SKILL.md", match.warnings)
        unselected = plan_manus_skill_package(
            self.manifests["creative.copywriting"],
            self.context("creative.copywriting", "LOAD", selected=False),
            self.target(),
            registry_path=REGISTRY_PATH,
            repository_root=REPO_ROOT,
        )
        self.assertEqual(unselected.blocked_reason, "CAPABILITY_NOT_SELECTED")

    def test_03_deep_load_is_declared_only_and_scripts_are_descriptors(self) -> None:
        capability_id = "creative.copywriting"
        loaded = load_vendor_skill(
            capability_id,
            registry_path=REGISTRY_PATH,
            repository_root=REPO_ROOT,
            references=("references/diction.md",),
        )
        reference = loaded["references"]["references/diction.md"]
        script_hash = "a" * 64
        plan = plan_manus_skill_package(
            self.manifests[capability_id],
            self.context(
                capability_id,
                "DEEP_LOAD",
                deep_load=[
                    {
                        "requested": True,
                        "kind": "reference",
                        "relative_path": "references/diction.md",
                        "source_hash": reference["sha256"],
                        "content": reference["content"],
                    },
                    {
                        "requested": True,
                        "kind": "script",
                        "relative_path": "assets/compose_canvas.js",
                        "source_hash": script_hash,
                        "content": None,
                        "size": 42,
                    },
                ],
            ),
            self.target(),
            registry_path=REGISTRY_PATH,
            repository_root=REPO_ROOT,
        )
        self.assertEqual(plan.status, READY)
        self.assertEqual(plan.files[-2].relative_path, "references/diction.md")
        self.assertEqual(plan.files[-1].format, "script-pointer")
        self.assertFalse(plan.files[-1].content_or_descriptor["executable"])
        self.assertEqual(
            plan_manus_skill_package(
                self.manifests[capability_id],
                self.context(capability_id, "DEEP_LOAD", deep_load=[{
                    "requested": True,
                    "kind": "reference",
                    "relative_path": "references/not-declared.md",
                    "source_hash": "b" * 64,
                    "content": "no",
                }]),
                self.target(),
                registry_path=REGISTRY_PATH,
                repository_root=REPO_ROOT,
            ).blocked_reason,
            "DECLARATION_MISMATCH",
        )

    def test_04_fail_closed_for_host_scope_hash_and_expansion(self) -> None:
        cases = (
            (self.target(host_kind="unknown"), "HOST_KIND_UNKNOWN"),
            (self.target(scope="global"), "HOST_SCOPE_MISMATCH"),
            (self.target(), "SOURCE_HASH_STALE"),
        )
        stale_context = self.context("creative.copywriting", source_hash="0" * 64)
        plan = plan_manus_skill_package(
            self.manifests["creative.copywriting"], stale_context, self.target(),
            registry_path=REGISTRY_PATH, repository_root=REPO_ROOT,
        )
        self.assertEqual(plan.blocked_reason, "SOURCE_HASH_STALE")
        for target, reason in cases[:2]:
            plan = plan_manus_skill_package(
                self.manifests["creative.copywriting"],
                self.context("creative.copywriting"),
                target,
                registry_path=REGISTRY_PATH,
                repository_root=REPO_ROOT,
            )
            self.assertEqual(plan.blocked_reason, reason)
        expanded = plan_manus_skill_package(
            self.manifests["creative.copywriting"],
            self.context("creative.copywriting", full_tree=True),
            self.target(),
            registry_path=REGISTRY_PATH,
            repository_root=REPO_ROOT,
        )
        self.assertEqual(expanded.blocked_reason, "CONTEXT_EXPANSION_UNAUTHORIZED")
        self.assertEqual(expanded.files, ())

    def test_05_plan_is_deterministic_and_non_mutating(self) -> None:
        before = {
            path.relative_to(REPO_ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (REPO_ROOT / ".p2p" / "system" / "p2p_capabilities").rglob("*")
            if path.is_file() and "__pycache__" not in path.parts
        }
        first = plan_manus_skill_package(
            self.manifests["creative.copywriting"], self.context("creative.copywriting"), self.target(),
            registry_path=REGISTRY_PATH, repository_root=REPO_ROOT,
        )
        second = plan_manus_skill_package(
            self.manifests["creative.copywriting"], self.context("creative.copywriting"), self.target(),
            registry_path=REGISTRY_PATH, repository_root=REPO_ROOT,
        )
        self.assertEqual(first.canonical_json(), second.canonical_json())
        self.assertTrue(all(not getattr(first, field) for field in (
            "writes_performed", "provider_mutated", "model_mutated", "auth_mutated",
            "permission_mutated", "task_state_mutated",
        )))
        after = {
            path.relative_to(REPO_ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (REPO_ROOT / ".p2p" / "system" / "p2p_capabilities").rglob("*")
            if path.is_file() and "__pycache__" not in path.parts
        }
        self.assertEqual(before, after)

    def test_06_export_is_repo_local_deterministic_and_carries_hashes(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT / ".tmp") as temp:
            output = Path(temp)
            first = export_manus_skill_package(
                self.manifests["creative.copywriting"], output / "one",
                repository_root=REPO_ROOT, registry_path=REGISTRY_PATH,
            )
            second = export_manus_skill_package(
                self.manifests["creative.copywriting"], output / "two",
                repository_root=REPO_ROOT, registry_path=REGISTRY_PATH,
            )
            self.assertEqual(first.archive_sha256, second.archive_sha256)
            self.assertEqual(first.plan.lifecycle_stage, "PACKAGE_FORMAT_PROVEN")
            self.assertEqual(first.plan.runtime_status, "NOT_CERTIFIED")
            self.assertEqual(first.plan.writes_performed, False)
            self.assertEqual(Path(first.archive_path).read_bytes(), Path(second.archive_path).read_bytes())
            provenance = json.loads((Path(first.package_directory) / "P2P-PROVENANCE.json").read_text(encoding="utf-8"))
            self.assertEqual(provenance["source_hash"], self.manifests["creative.copywriting"].upstream_provenance["snapshot_sha256"])
            self.assertEqual(provenance["entrypoint_hash"], self.manifests["creative.copywriting"].upstream_provenance["integration"]["entrypoint_sha256"])
            self.assertNotIn("provider", json.dumps(provenance).lower())
            self.assertNotIn("model", json.dumps(provenance).lower())
            self.assertIs(provenance["integration"]["credentials"], False)

    def test_07_export_rejects_outside_or_existing_output(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT / ".tmp") as temp:
            output = Path(temp)
            with self.assertRaisesRegex(ValueError, "OUTPUT_PATH_INVALID"):
                export_manus_skill_package(
                    self.manifests["creative.copywriting"], Path(tempfile.gettempdir()) / "outside",
                    repository_root=REPO_ROOT, registry_path=REGISTRY_PATH,
                )
            first = export_manus_skill_package(
                self.manifests["creative.copywriting"], output / "existing",
                repository_root=REPO_ROOT, registry_path=REGISTRY_PATH,
            )
            with self.assertRaisesRegex(ValueError, "OUTPUT_EXISTS"):
                export_manus_skill_package(
                    self.manifests["creative.copywriting"], output / "existing",
                    repository_root=REPO_ROOT, registry_path=REGISTRY_PATH,
                )
            self.assertTrue(Path(first.archive_path).is_file())

    def test_08_source_boundary_has_no_network_or_execution(self) -> None:
        source = (SYSTEM_ROOT / "p2p_capabilities" / "manus_skill_package.py").read_text(encoding="utf-8")
        for forbidden in ("urllib", "requests", "socket", "subprocess", "os.system", "ManusAdapter", "task.create"):
            self.assertNotIn(forbidden, source)
        self.assertNotIn("host_projection", source)


if __name__ == "__main__":
    unittest.main()
