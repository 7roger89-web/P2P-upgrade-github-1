from __future__ import annotations

import copy
import hashlib
import json
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_ROOT = REPO_ROOT / ".p2p" / "system"
REGISTRY_PATH = SYSTEM_ROOT / "p2p_capabilities" / "capabilities.json"
sys.path.insert(0, str(SYSTEM_ROOT))

from p2p_capabilities import load_registry  # noqa: E402
from p2p_capabilities.host_projection import (  # noqa: E402
    BLOCKED,
    INPUT_SCHEMA,
    PLAN_SCHEMA,
    READY,
    REASON_CODES,
    HostSkillProjectionInput,
    canonical_json,
    project_host_skill,
)
from p2p_capabilities.vendor_skill import load_vendor_skill, snapshot_tree_sha256  # noqa: E402


VENDOR_ROOTS = {
    "creative.copywriting": REPO_ROOT / ".p2p" / "vendor" / "skill" / "xiaoma-durex-copywriter-main",
    "media.whiteboard_animation": REPO_ROOT / ".p2p" / "vendor" / "skill" / "srt-whiteboard-animation-main",
    "visual.gpt_image_2_style_library": REPO_ROOT / ".p2p" / "vendor" / "skill" / "gpt-image-2-style-library-9a7b2e9",
}
EXPECTED_VENDOR_HASHES = {
    "creative.copywriting": "5a02c082b531b6731dbdd6e55ccc8798ba2514bbb27df8e9c2ef74c88752830d",
    "media.whiteboard_animation": "55dbed4743cad90f80d1603ed639508c8e3a6e650a1abccfe7d4e8b2e148742c",
    "visual.gpt_image_2_style_library": "29121408bbfdd4994ec4738b6ee181c80ba123cb7554c297e8a07091faddc482",
}


class P2PHostSkillProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = load_registry(REGISTRY_PATH)
        cls.manifests = {
            item.capability_id: item
            for item in cls.registry["parsed"]
            if item.capability_id in VENDOR_ROOTS
        }
        cls.loaded = {
            capability_id: load_vendor_skill(
                capability_id,
                registry_path=REGISTRY_PATH,
                repository_root=REPO_ROOT,
            )
            for capability_id in VENDOR_ROOTS
        }

    def target(self, host_kind: str = "codex", **extra: object) -> dict:
        value = {"host_kind": host_kind, "scope": "project"}
        value.update(extra)
        return value

    def context(self, capability_id: str, stage: str = "LOAD", *, selected: bool = True, **extra: object) -> dict:
        manifest = self.manifests[capability_id]
        value: dict[str, object] = {
            "load_stage": stage,
            "selected": selected,
            "source_hash": manifest.upstream_provenance["snapshot_sha256"],
        }
        if stage in {"LOAD", "DEEP_LOAD"}:
            value["entrypoint_content"] = self.loaded[capability_id]["skill"]["content"]
        value.update(extra)
        return value

    def project(self, capability_id: str = "creative.copywriting", stage: str = "LOAD", *, selected: bool = True, target: dict | None = None, capability: object | None = None, **context_overrides: object):
        return project_host_skill(
            capability or self.manifests[capability_id],
            self.context(capability_id, stage, selected=selected, **context_overrides),
            target or self.target(),
        )

    def fingerprint(self, paths: tuple[str, ...] = (".agents", ".claude", ".gemini", ".cursor", ".github", ".p2p/system/p2p_capabilities")) -> dict[str, str]:
        result: dict[str, str] = {}
        for relative_root in paths:
            root = REPO_ROOT / relative_root
            if not root.exists():
                result[relative_root] = "ABSENT"
                continue
            entries: list[str] = []
            for path in sorted(root.rglob("*")):
                if path.is_file() and "__pycache__" not in path.parts:
                    entries.append(f"{path.relative_to(REPO_ROOT).as_posix()}\n{hashlib.sha256(path.read_bytes()).hexdigest()}")
            result[relative_root] = hashlib.sha256("\n".join(entries).encode("utf-8")).hexdigest()
        return result

    def test_01_codex_copywriting_mapping_supported(self) -> None:
        plan = self.project()
        self.assertEqual(plan.status, READY)
        self.assertEqual(plan.host_kind, "codex")
        self.assertEqual(plan.capability_id, "creative.copywriting")
        self.assertEqual(plan.files[0].relative_target, ".agents/skills/creative.copywriting/SKILL.md")
        self.assertEqual(plan.files[1].relative_target, ".agents/skills/creative.copywriting/agents/openai.yaml")
        self.assertIn("allow_implicit_invocation: true", plan.files[1].content_or_template)
        self.assertIn("short_description", plan.files[1].content_or_template)
        self.assertNotIn(".codex/config.toml", repr(plan))

    def test_02_codex_whiteboard_mapping_preserves_frozen_hashes(self) -> None:
        plan = self.project("media.whiteboard_animation")
        self.assertEqual(plan.status, READY)
        self.assertEqual(plan.files[0].relative_target, ".agents/skills/media.whiteboard_animation/SKILL.md")
        self.assertEqual(plan.source_hash, EXPECTED_VENDOR_HASHES["media.whiteboard_animation"])
        self.assertEqual(plan.entrypoint_hash, self.manifests["media.whiteboard_animation"].upstream_provenance["integration"]["entrypoint_sha256"])
        self.assertEqual(snapshot_tree_sha256(VENDOR_ROOTS["media.whiteboard_animation"]), EXPECTED_VENDOR_HASHES["media.whiteboard_animation"])

    def test_03_claude_planned_and_drift_blocks(self) -> None:
        ready = self.project(target=self.target("claude"))
        self.assertEqual(ready.status, READY)
        self.assertIn("MAPPING_PLANNED", ready.warnings)
        self.assertEqual(ready.files[0].relative_target, ".claude/skills/creative.copywriting/SKILL.md")
        blocked = self.project(target=self.target("claude", host_evidence={"status": "DRIFT"}))
        self.assertEqual((blocked.status, blocked.blocked_reason, blocked.files), (BLOCKED, "BLOCKED_HOST_DRIFT", ()))

    def test_04_gemini_planned_and_drift_blocks(self) -> None:
        ready = self.project("media.whiteboard_animation", target=self.target("gemini"))
        self.assertEqual(ready.status, READY)
        self.assertIn("MAPPING_PLANNED", ready.warnings)
        self.assertEqual(ready.files[0].relative_target, ".gemini/skills/media.whiteboard_animation/SKILL.md")
        blocked = self.project("media.whiteboard_animation", target=self.target("gemini", evidence={"mapping_status": "BLOCKED_HOST_DRIFT"}))
        self.assertEqual(blocked.blocked_reason, "BLOCKED_HOST_DRIFT")
        self.assertEqual(blocked.files, ())

    def test_05_cursor_planned_and_drift_blocks(self) -> None:
        ready = self.project(target=self.target("cursor"))
        self.assertEqual(ready.status, READY)
        self.assertEqual(ready.files[0].relative_target, ".cursor/rules/creative.copywriting.mdc")
        blocked = self.project(target=self.target("cursor", native_format="ambiguous"))
        self.assertEqual(blocked.blocked_reason, "HOST_FORMAT_AMBIGUOUS")

    def test_06_copilot_requires_explicit_safe_scope(self) -> None:
        ready = self.project(target=self.target("copilot", apply_to="docs/**/*.md"))
        self.assertEqual(ready.status, READY)
        self.assertEqual(ready.files[0].relative_target, ".github/instructions/creative.copywriting.instructions.md")
        self.assertEqual(self.project(target=self.target("copilot")).blocked_reason, "COPILOT_SCOPE_REQUIRED")
        self.assertEqual(self.project(target=self.target("copilot", apply_to="**")).blocked_reason, "COPILOT_SCOPE_REQUIRED")

    def test_07_antigravity_is_host_unknown(self) -> None:
        plan = self.project(target=self.target("antigravity"))
        self.assertEqual((plan.status, plan.blocked_reason, plan.files), (BLOCKED, "HOST_KIND_UNKNOWN", ()))

    def test_08_unlisted_host_is_host_unknown(self) -> None:
        plan = self.project(target=self.target("future-host"))
        self.assertEqual(plan.blocked_reason, "HOST_KIND_UNKNOWN")
        self.assertEqual(plan.files, ())

    def test_09_missing_provenance_blocks(self) -> None:
        capability = copy.deepcopy(self.manifests["creative.copywriting"].raw)
        capability["UPSTREAM_PROVENANCE"] = {}
        plan = self.project(capability=capability)
        self.assertEqual(plan.blocked_reason, "PROVENANCE_MISSING")
        self.assertEqual(plan.files, ())

    def test_10_stale_source_hash_blocks_without_refresh(self) -> None:
        plan = self.project(source_hash="0" * 64)
        self.assertEqual(plan.blocked_reason, "SOURCE_HASH_STALE")
        self.assertEqual(plan.files, ())

    def test_11_entrypoint_hash_mismatch_blocks(self) -> None:
        plan = self.project(entrypoint_content="changed entrypoint")
        self.assertEqual(plan.blocked_reason, "ENTRYPOINT_HASH_MISMATCH")
        self.assertEqual(plan.files, ())

    def test_12_path_traversal_blocks(self) -> None:
        plan = self.project(target=self.target(target_paths={"skill": "../escape/SKILL.md"}))
        self.assertEqual(plan.blocked_reason, "PATH_TRAVERSAL")
        self.assertEqual(plan.files, ())

    def test_13_absolute_target_blocks(self) -> None:
        plan = self.project(target=self.target(target_paths={"skill": "/home/user/SKILL.md"}))
        self.assertEqual(plan.blocked_reason, "ABSOLUTE_TARGET_PATH")
        self.assertEqual(plan.files, ())

    def test_14_unsupported_invocation_policy_blocks(self) -> None:
        capability = copy.deepcopy(self.manifests["creative.copywriting"].raw)
        capability["INVOCATION_CLASS"] = "HOST_PRIMITIVE"
        plan = self.project(capability=capability)
        self.assertEqual(plan.blocked_reason, "INVOCATION_POLICY_UNSUPPORTED")
        self.assertEqual(plan.files, ())

    def test_15_ambiguous_format_blocks(self) -> None:
        plan = self.project(target=self.target(native_format="AMBIGUOUS"))
        self.assertEqual(plan.blocked_reason, "HOST_FORMAT_AMBIGUOUS")
        self.assertEqual(plan.files, ())

    def test_16_invalid_serialization_blocks(self) -> None:
        plan = self.project(target=self.target(target_paths=[]))
        self.assertEqual(plan.blocked_reason, "SERIALIZATION_INVALID")
        self.assertEqual(plan.files, ())

    def test_17_ownership_conflict_and_review_fail_closed(self) -> None:
        conflict = self.project(target=self.target(existing_ownership={"skill": "HOST_OWNED_PRESERVE"}))
        self.assertEqual((conflict.status, conflict.blocked_reason, conflict.files), (BLOCKED, "P2P_OWNERSHIP_CONFLICT", ()))
        review = self.project(target=self.target(ownership_class="OWNER_REVIEW_REQUIRED", deployment_requires_review=True))
        self.assertEqual((review.status, review.blocked_reason, review.files), (BLOCKED, "P2P_OWNERSHIP_REVIEW_REQUIRED", ()))

    def test_18_progressive_disclosure_is_selected_and_declared_only(self) -> None:
        discovery = self.project(stage="DISCOVERY")
        self.assertEqual(discovery.status, READY)
        self.assertFalse(discovery.content_loaded)
        self.assertTrue(all(item.content_or_template is None for item in discovery.files))
        match = self.project(stage="MATCH")
        self.assertIn("MATCH_ENTRYPOINT_POINTER:SKILL.md", match.warnings)
        unselected = self.project(stage="LOAD", selected=False)
        self.assertEqual(unselected.blocked_reason, "CAPABILITY_NOT_SELECTED")
        implicit_deep = self.project(stage="LOAD", deep_load=[{"requested": True, "relative_path": "references/diction.md"}])
        self.assertEqual(implicit_deep.blocked_reason, "CONTEXT_EXPANSION_UNAUTHORIZED")
        loaded = self.loaded["creative.copywriting"]
        reference = load_vendor_skill(
            "creative.copywriting",
            registry_path=REGISTRY_PATH,
            repository_root=REPO_ROOT,
            references=("references/diction.md",),
        )["references"]["references/diction.md"]
        deep = self.project(
            stage="DEEP_LOAD",
            deep_load=[
                {
                    "requested": True,
                    "kind": "reference",
                    "relative_path": "references/diction.md",
                    "source_hash": reference["sha256"],
                    "content": reference["content"],
                }
            ],
        )
        self.assertEqual(deep.status, READY)
        self.assertEqual(deep.files[-1].relative_target, ".agents/skills/creative.copywriting/references/diction.md")
        self.assertEqual(deep.files[-1].content_hash, reference["sha256"])
        self.assertNotIn("references/corpus.md", [item.relative_target for item in deep.files])

    def test_19_exact_additional_codes_determinism_and_nonmutation(self) -> None:
        before = self.fingerprint()
        first = self.project()
        second = self.project()
        self.assertEqual(first.canonical_json(), second.canonical_json())
        self.assertEqual(json.loads(first.canonical_json()), first.to_dict())
        for field in ("writes_performed", "provider_mutated", "model_mutated", "auth_mutated", "permission_mutated", "task_state_mutated"):
            self.assertIs(getattr(first, field), False)
        after = self.fingerprint()
        self.assertEqual(before, after)
        missing_boundary = copy.deepcopy(self.manifests["creative.copywriting"].raw)
        missing_boundary["APPROVAL_BOUNDARY"] = []
        self.assertEqual(self.project(capability=missing_boundary).blocked_reason, "MISSING_APPROVAL_BOUNDARY")
        self.assertEqual(self.project(target=self.target(scope="global")).blocked_reason, "HOST_SCOPE_MISMATCH")
        self.assertEqual(self.project(target=self.target(host_evidence={"status": "CONFLICT"})).blocked_reason, "BLOCKED_HOST_DRIFT")
        self.assertEqual(len(REASON_CODES), 17)
        self.assertEqual(len(set(REASON_CODES)), 17)

    def test_20_schema_shape_and_normalized_input_round_trip(self) -> None:
        plan = self.project()
        payload = plan.to_dict()
        self.assertEqual(payload["schema"], PLAN_SCHEMA)
        self.assertEqual(set(payload), {
            "schema", "status", "host_kind", "capability_id", "source_hash",
            "entrypoint_hash", "load_stage", "files", "warnings", "blocked_reason",
            "content_loaded", "writes_performed", "provider_mutated", "model_mutated",
            "auth_mutated", "permission_mutated", "task_state_mutated",
        })
        normalized = HostSkillProjectionInput(
            skill_id="example.skill",
            display_name="Example Skill",
            description="Canonical description",
            invocation_class="USER_REQUESTED",
            invocation_policy="USER_REQUESTED",
            context_entrypoint="SKILL.md",
            context_refs=(),
            provenance={
                "vendor_path": ".p2p/vendor/example",
                "mode": "LOCAL_VENDOR_SNAPSHOT",
                "license": {"kind": "MIT"},
            },
            source_hash="a" * 64,
            entrypoint_hash="b" * 64,
            host_kind="codex",
            host_scope=("project",),
            approval_boundary=("owner-review",),
            trust_level="HOST_CODE",
            load_stage="DISCOVERY",
        )
        self.assertEqual(normalized.to_dict()["schema"], INPUT_SCHEMA)
        self.assertEqual(normalized.to_dict()["host_scope"], ["project"])

    def test_21_wrong_input_schema_and_invalid_target_shape_block(self) -> None:
        capability = copy.deepcopy(self.manifests["creative.copywriting"].raw)
        capability["schema"] = "p2p-host-skill-projection-input/999"
        self.assertEqual(self.project(capability=capability).blocked_reason, "SERIALIZATION_INVALID")
        self.assertEqual(
            self.project(target={"host_kind": "codex"}).blocked_reason,
            "HOST_SCOPE_MISMATCH",
        )
        self.assertEqual(
            self.project(target=self.target(allowed_hosts=["claude"])).blocked_reason,
            "HOST_SCOPE_MISMATCH",
        )
        self.assertEqual(
            self.project(target=self.target(host_evidence=[])).blocked_reason,
            "SERIALIZATION_INVALID",
        )

    def test_22_policy_derives_codex_implicit_invocation_without_host_default(self) -> None:
        user_requested = copy.deepcopy(self.manifests["creative.copywriting"].raw)
        user_requested["INVOCATION_CLASS"] = "USER_REQUESTED"
        explicit = self.project(capability=user_requested)
        self.assertEqual(explicit.status, READY)
        self.assertIn("allow_implicit_invocation: false", explicit.files[1].content_or_template)
        blocked = self.project(target=self.target(supports_implicit_invocation="yes"))
        self.assertEqual(blocked.blocked_reason, "INVOCATION_POLICY_UNSUPPORTED")

    def test_23_planned_host_serialization_is_canonical_data(self) -> None:
        plan = self.project(target=self.target("claude"))
        self.assertEqual(plan.status, READY)
        self.assertTrue(plan.content_loaded)
        self.assertIsInstance(plan.files[0].content_or_template, str)
        self.assertIn("invocation_policy", plan.files[0].content_or_template)
        self.assertIn("description", plan.files[0].content_or_template)
        self.assertEqual(plan.files[0].ownership_class, "P2P_PROJECT_MANAGED")
        self.assertNotIn(".claude/CLAUDE.md", plan.files[0].content_or_template)

    def test_24_owner_review_class_is_descriptive_until_deployment(self) -> None:
        plan = self.project(target=self.target(ownership_class="OWNER_REVIEW_REQUIRED"))
        self.assertEqual(plan.status, READY)
        self.assertEqual(
            {item.ownership_class for item in plan.files},
            {"OWNER_REVIEW_REQUIRED"},
        )
        self.assertTrue(all(not getattr(plan, field) for field in (
            "writes_performed", "provider_mutated", "model_mutated",
            "auth_mutated", "permission_mutated", "task_state_mutated",
        )))

    def test_25_deep_load_script_is_pointer_data_and_requires_declaration(self) -> None:
        script = "assets/compose_canvas.js"
        deep = self.project(
            stage="DEEP_LOAD",
            deep_load=[{
                "requested": True,
                "kind": "script",
                "relative_path": script,
                "source_hash": "c" * 64,
                "content": None,
            }],
        )
        self.assertEqual(deep.status, READY)
        descriptor = deep.files[-1]
        self.assertEqual(descriptor.format, "script-pointer")
        self.assertEqual(descriptor.content_hash, "c" * 64)
        self.assertEqual(descriptor.content_or_template["executable"], False)
        undeclared = self.project(
            stage="DEEP_LOAD",
            deep_load=[{
                "requested": True,
                "relative_path": "unrelated/not-declared.md",
                "source_hash": "d" * 64,
                "content": None,
            }],
        )
        self.assertEqual(undeclared.blocked_reason, "CONTEXT_EXPANSION_UNAUTHORIZED")

    def test_26_progressive_disclosure_does_not_consume_entrypoint_for_discovery(self) -> None:
        context = self.context("creative.copywriting", "DISCOVERY")
        context["entrypoint_content"] = object()
        plan = project_host_skill(self.manifests["creative.copywriting"], context, self.target())
        self.assertEqual(plan.status, READY)
        self.assertFalse(plan.content_loaded)
        self.assertTrue(all(item.content_or_template is None for item in plan.files))
        blocked = self.project(stage="LOAD", include_full_tree=True)
        self.assertEqual(blocked.blocked_reason, "CONTEXT_EXPANSION_UNAUTHORIZED")

    def test_27_freshness_scope_and_serialization_fail_closed(self) -> None:
        self.assertEqual(
            self.project(entrypoint_hash="e" * 64).blocked_reason,
            "ENTRYPOINT_HASH_MISMATCH",
        )
        self.assertEqual(
            self.project(target=self.target(scope=["project", "global"])).blocked_reason,
            "HOST_SCOPE_MISMATCH",
        )
        self.assertEqual(
            self.project(target=self.target(target_paths={"skill": r"C:\Users\owner\SKILL.md"})).blocked_reason,
            "ABSOLUTE_TARGET_PATH",
        )
        self.assertEqual(
            self.project(target=self.target(target_paths={"skill": None})).blocked_reason,
            "SERIALIZATION_INVALID",
        )

    def test_28_blocked_plans_never_leak_partial_file_descriptors(self) -> None:
        blocked = [
            self.project(target=self.target(native_format="AMBIGUOUS")),
            self.project(target=self.target(existing_ownership="HOST_OWNED_PRESERVE")),
            self.project(stage="LOAD", selected=False),
            self.project(target=self.target(host_evidence={"drift": True})),
        ]
        for plan in blocked:
            self.assertEqual(plan.status, BLOCKED)
            self.assertEqual(plan.files, ())
            self.assertIsNotNone(plan.blocked_reason)
            self.assertTrue(all(not getattr(plan, field) for field in (
                "writes_performed", "provider_mutated", "model_mutated",
                "auth_mutated", "permission_mutated", "task_state_mutated",
            )))

    def test_29_source_is_free_of_writer_and_runtime_imports(self) -> None:
        source = (SYSTEM_ROOT / "p2p_capabilities" / "host_projection.py").read_text(encoding="utf-8")
        for forbidden in ("subprocess", "socket", "urllib", "requests", "write_text", "write_bytes"):
            self.assertNotIn(forbidden, source)
        self.assertIn("CapabilityManifest", source)
        self.assertNotIn("HostCapabilityRouter", source)

    def test_30_both_real_capabilities_cover_codex_claude_and_gemini(self) -> None:
        for capability_id in VENDOR_ROOTS:
            for host_kind in ("codex", "claude", "gemini"):
                plan = self.project(
                    capability_id,
                    target=self.target(host_kind),
                )
                self.assertEqual(plan.status, READY)
                self.assertEqual(plan.capability_id, capability_id)
                self.assertEqual(
                    plan.source_hash,
                    EXPECTED_VENDOR_HASHES[capability_id],
                )
                self.assertTrue(plan.files)
                self.assertTrue(
                    plan.files[0].relative_target.startswith(
                        f".{host_kind}/"
                    )
                    if host_kind != "codex"
                    else plan.files[0].relative_target.startswith(".agents/")
                )


if __name__ == "__main__":
    unittest.main()
