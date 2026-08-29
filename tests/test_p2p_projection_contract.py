from __future__ import annotations

import copy
import hashlib
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_ROOT = REPO_ROOT / ".p2p" / "system"
sys.path.insert(0, str(SYSTEM_ROOT))

from p2p_capabilities.host_projection import HostSkillProjectionInput, project_host_skill  # noqa: E402
from p2p_capabilities import project_materialization as materialization  # noqa: E402
from p2p_capabilities.context import MINIMAL, retrieve_task_context  # noqa: E402
from p2p_capabilities.project_context import ProjectContextBootstrap  # noqa: E402
from p2p_capabilities.project_map import ProjectMapBuilder  # noqa: E402
from p2p_capabilities.project_pin import (  # noqa: E402
    PROJECT_PIN_V2_SCHEMA,
    PROJECTION_ONLY,
    ProjectPinError,
    build_pin,
    build_projection_pin,
    validate_pin,
    write_pin,
)


SOURCE_REPOSITORY = "https://github.com/7roger89-web/P2P-upgrade-github-1.git"
SOURCE_COMMIT = "bc686845fbb5817e50958d91e0d382a72c219b78"
SOURCE_TREE = "68b16f0fd2116ec6e93bdb9dbecc31429a68ec6d"


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


class P2PProjectionContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="projection-contract-", dir=REPO_ROOT / ".tmp"))
        self.addCleanup(lambda: shutil.rmtree(self.root, ignore_errors=True))
        (self.root / "README.md").write_text("disposable projection fixture\n", encoding="utf-8")
        self.policy_path = self.root / ".p2p" / "project-policy.json"
        self.policy_path.parent.mkdir(parents=True, exist_ok=True)
        self.policy_path.write_text(
            json.dumps(
                {
                    "schema_version": "p2p-codex-project-policy/1",
                    "project": "projection-fixture",
                    "protected_actions": ["release_or_deploy"],
                },
                sort_keys=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        self.context_path = self.root / ".p2p" / "context" / "project_map.json"
        context = ProjectContextBootstrap(self.root)
        context.save_project_map(ProjectMapBuilder(str(self.root)).build_full_map())
        self.plan = self._make_plan()
        self.selected = [
            {
                "capability_id": "game.mengto.camera_controls",
                "state": "DISCOVERED",
                "readiness": "RESOLVED",
                "source_hash": self.plan.source_hash,
                "entrypoint_hash": self.plan.entrypoint_hash,
                "runtime_readiness": {"executable_registered": False},
            }
        ]

    def _make_plan(self, *, capability_id: str = "game.mengto.camera_controls", content: str = "camera instructions v1\n"):
        content_bytes = content.encode("utf-8")
        entrypoint_hash = _sha256(content_bytes)
        source_hash = _sha256(b"camera-source-snapshot")
        item = HostSkillProjectionInput(
            skill_id=capability_id,
            display_name="Mengto Camera Controls",
            description="Project camera instructions",
            invocation_class="USER_REQUESTED",
            invocation_policy="USER_REQUESTED",
            context_entrypoint="references/camera.md",
            context_refs=("references/camera.md",),
            provenance={
                "vendor_path": "vendor/camera",
                "source_class": "DEVELOPMENT_SOURCE",
                "license": "MIT",
                "snapshot_sha256": source_hash,
                "integration": {"entrypoint_sha256": entrypoint_hash},
            },
            source_hash=source_hash,
            entrypoint_hash=entrypoint_hash,
            host_kind="codex",
            host_scope=("project",),
            approval_boundary=("OWNER_REVIEW",),
            trust_level="TRUSTED_DATA",
            load_stage="LOAD",
        )
        plan = project_host_skill(
            item,
            {"selected": True, "source_hash": source_hash, "entrypoint_content": content},
            {"host_kind": "codex", "scope": "project"},
        )
        self.assertEqual(plan.status, "READY")
        return plan

    def _materialize(self, *, plan=None, selected=None, **extra):
        effective_plan = plan or self.plan
        plan_source_hash = effective_plan["source_hash"] if isinstance(effective_plan, dict) else effective_plan.source_hash
        plan_entrypoint_hash = effective_plan["entrypoint_hash"] if isinstance(effective_plan, dict) else effective_plan.entrypoint_hash
        if selected is None:
            selected = self.selected if plan is None else [
                {
                    **self.selected[0],
                    "source_hash": plan_source_hash,
                    "entrypoint_hash": plan_entrypoint_hash,
                }
            ]
        return materialization.materialize_projection(
            project_root=self.root,
            project_id="fixture-projection-01",
            project_name="Projection Fixture",
            project_version="0.1.0",
            source_repository=SOURCE_REPOSITORY,
            source_commit=SOURCE_COMMIT,
            source_tree=SOURCE_TREE,
            selected_capabilities=selected,
            projection_plan=effective_plan,
            policy_path=self.policy_path,
            context_path=self.context_path,
            **extra,
        )

    def _pin(self) -> dict:
        return json.loads((self.root / ".p2p" / "project-pin.json").read_text(encoding="utf-8"))

    def test_reference_fixture_is_ready_without_runtime_and_is_selective(self) -> None:
        result = self._materialize()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["mode"], PROJECTION_ONLY)
        self.assertEqual(validate_pin(self.root)["mode"], PROJECTION_ONLY)
        context = ProjectContextBootstrap(self.root)
        self.assertTrue(context.is_ready())
        self.assertEqual(context.get_full_model().project_identity["name"], "Projection Fixture")
        pin = self._pin()
        self.assertEqual(pin["schema"], PROJECT_PIN_V2_SCHEMA)
        self.assertEqual(pin["runtime_claim"], {"installed": False, "status": "NOT_INSTALLED"})
        self.assertFalse((self.root / ".p2p" / "system").exists())
        self.assertFalse((self.root / ".p2p" / "vendor").exists())
        self.assertFalse((self.root / "reports").exists())
        for forbidden in (
            ".p2p/evals",
            ".p2p/state",
            ".p2p/approvals",
            ".p2p/registry",
            ".p2p/capabilities",
            ".p2p/tests",
            "vendor",
            "tests",
        ):
            self.assertFalse((self.root / forbidden).exists(), forbidden)
        self.assertTrue((self.root / ".agents" / "skills" / "game.mengto.camera_controls" / "SKILL.md").is_file())

    def test_reference_fixture_retrieves_only_camera_context(self) -> None:
        self._materialize()
        catalog = [
            {
                "source_id": "camera-context",
                "path": "camera.md",
                "source_class": "AUTHORITATIVE_PROJECT_SOURCE",
                "retrieval_role": "DIRECT_AUTHORITATIVE_REFS",
                "coverage_ids": ["camera"],
                "scope": ["current-task"],
                "content": {"topic": "camera controls"},
            },
            {
                "source_id": "unrelated-context",
                "path": "lighting.md",
                "source_class": "AUTHORITATIVE_PROJECT_SOURCE",
                "retrieval_role": "TARGETED_SOURCE",
                "coverage_ids": ["lighting"],
                "scope": ["current-task"],
                "content": {"topic": "lighting"},
            },
        ]
        task = {
            "task_purpose": "camera task",
            "scope": ["current-task"],
            "direct_authoritative_refs": ["camera-context"],
            "acceptance": [
                {"coverage_id": "camera", "source_refs": ["camera-context"], "required": True}
            ],
        }
        result = retrieve_task_context(task, catalog, context_class=MINIMAL)
        self.assertEqual(result["status"], "SUFFICIENT")
        self.assertEqual(result["materialized_context"]["source_ids"], ["camera-context"])
        self.assertNotIn("unrelated-context", result["materialized_context"]["source_ids"])

    def test_v2_packaged_mode_keeps_legacy_metadata_and_doctor_requirements(self) -> None:
        system = self.root / ".p2p" / "system"
        system.mkdir(parents=True, exist_ok=True)
        version = "8.4.7-C-codex.73"
        (system / "VERSION").write_text(version + "\n", encoding="utf-8")
        (system / "CANDIDATE-DISTRIBUTION-MANIFEST.json").write_text(
            json.dumps(
                {
                    "schema_version": "p2p-codex-candidate-distribution/1",
                    "candidate_version": version,
                    "official_baseline_version": "8.4.7-C-codex.19",
                    "official_baseline_sha256": "c" * 64,
                    "candidate_vs_official": "UNPROMOTED_SUCCESSOR_CANDIDATE",
                }
            ),
            encoding="utf-8",
        )
        (system / "SOURCE-BINDING.json").write_text(
            json.dumps(
                {
                    "schema_version": "p2p-codex-source-binding/1",
                    "candidate_version": version,
                    "source_commit": "1" * 40,
                    "source_tree": "2" * 40,
                    "source_commit_object": "VERIFIED",
                    "source_tree_object": "VERIFIED",
                    "source_tree_bound_to_commit": "VERIFIED",
                }
            ),
            encoding="utf-8",
        )
        (system / "ARTIFACT-IDENTITY.json").write_text(json.dumps({"candidate_version": version}), encoding="utf-8")
        (system / "release.json").write_text(
            json.dumps({"candidate_version": version, "artifact_sha256": "a" * 64}), encoding="utf-8"
        )
        packaged = build_pin(
            project_root=self.root,
            metadata_root=system,
            artifact_sha256="a" * 64,
            installation_mode="PACKAGED_PROJECT",
            rollback_source=".p2p/install-backups/test",
            managed_files=["VERSION"],
        )
        packaged["schema"] = PROJECT_PIN_V2_SCHEMA
        packaged["mode"] = "PACKAGED_RUNTIME"
        write_pin(self.root, packaged)
        result = validate_pin(self.root, metadata_root=system)
        self.assertEqual(result["schema"], PROJECT_PIN_V2_SCHEMA)
        self.assertEqual(result["mode"], "PACKAGED_RUNTIME")
        self.assertEqual(result["doctor_result"], "HEALTHY")

    def test_idempotent_rerun_and_owned_update(self) -> None:
        first = self._materialize()
        second = self._materialize()
        self.assertEqual(first["changed_files"], 2)
        self.assertEqual(second["changed_files"], 0)
        self.assertTrue(second["idempotent"])
        old_skill_hash = self._pin()["projection"]["managed_files"][0]["content_sha256"]
        updated = self._make_plan(content="camera instructions v2\n")
        updated_result = self._materialize(plan=updated)
        self.assertEqual(updated_result["changed_files"], 1)
        new_record = self._pin()["projection"]["managed_files"][0]
        self.assertEqual(new_record["previous_state"]["state"], "PRESENT")
        self.assertEqual(new_record["previous_state"]["content_sha256"], old_skill_hash)
        self.assertTrue(ProjectContextBootstrap(self.root).is_ready())

    def test_unknown_mode_and_packaged_fields_fail_closed(self) -> None:
        self._materialize()
        pin_path = self.root / ".p2p" / "project-pin.json"
        pin = self._pin()
        pin["mode"] = "UNKNOWN"
        pin_path.write_text(json.dumps(pin), encoding="utf-8")
        self.assertFalse(ProjectContextBootstrap(self.root).is_ready())
        pin["mode"] = PROJECTION_ONLY
        pin["doctor_result"] = "HEALTHY"
        pin_path.write_text(json.dumps(pin), encoding="utf-8")
        with self.assertRaises(ProjectPinError):
            validate_pin(self.root)
        pin.pop("doctor_result")
        pin["artifact_sha256"] = "a" * 64
        pin_path.write_text(json.dumps(pin), encoding="utf-8")
        with self.assertRaises(ProjectPinError):
            validate_pin(self.root)

    def test_unsupported_schema_malformed_pin_and_stale_plan_fail_closed(self) -> None:
        unsupported = copy.deepcopy(self.plan.to_dict())
        unsupported["schema"] = "p2p-host-skill-projection-plan/0"
        with self.assertRaises(ProjectPinError):
            self._materialize(plan=unsupported)
        self.assertFalse((self.root / ".p2p" / "project-pin.json").exists())

        stale = copy.deepcopy(self.plan.to_dict())
        stale["files"][0]["content_or_template"] = "stale plan bytes\n"
        with self.assertRaises(ProjectPinError):
            self._materialize(plan=stale)
        self.assertFalse((self.root / ".p2p" / "project-pin.json").exists())
        self.assertFalse((self.root / ".agents").exists())

        self._materialize()
        (self.root / ".p2p" / "project-pin.json").write_text("{malformed", encoding="utf-8")
        self.assertFalse(ProjectContextBootstrap(self.root).is_ready())
        with self.assertRaises(materialization.ProjectionMaterializationError):
            self._materialize()

    def test_source_plan_and_file_bindings_reject_drift(self) -> None:
        self._materialize()
        with self.assertRaises(ProjectPinError):
            validate_pin(self.root, expected_source_commit="0" * 40)
        with self.assertRaises(ProjectPinError):
            validate_pin(self.root, expected_plan_sha256="0" * 64)
        projected = self.root / ".agents" / "skills" / "game.mengto.camera_controls" / "SKILL.md"
        projected.write_text("tampered owner content\n", encoding="utf-8")
        self.assertFalse(ProjectContextBootstrap(self.root).is_ready())
        with self.assertRaises(ProjectPinError):
            validate_pin(self.root)

    def test_policy_and_context_hash_drift_reject_readiness(self) -> None:
        self._materialize()
        original_policy = self.policy_path.read_bytes()
        self.policy_path.write_bytes(original_policy + b"\n")
        self.assertFalse(ProjectContextBootstrap(self.root).is_ready())
        self.policy_path.write_bytes(original_policy)
        self.context_path.write_bytes(self.context_path.read_bytes() + b"\n")
        self.assertFalse(ProjectContextBootstrap(self.root).is_ready())

    def test_absolute_traversal_separator_and_unmanaged_paths_are_rejected(self) -> None:
        for bad_path in ("../escape.md", "..\\escape.md", "/escape.md", "C:/escape.md", "README.md"):
            with self.subTest(bad_path=bad_path):
                plan = copy.deepcopy(self.plan.to_dict())
                plan["files"][0]["relative_target"] = bad_path
                with self.assertRaises(ProjectPinError):
                    self._materialize(plan=plan)
                self.assertFalse((self.root / ".p2p" / "project-pin.json").exists())

    def test_symlink_escape_is_rejected(self) -> None:
        outside = Path(tempfile.mkdtemp(prefix="projection-outside-", dir=REPO_ROOT / ".tmp"))
        self.addCleanup(lambda: shutil.rmtree(outside, ignore_errors=True))
        link_parent = self.root / ".agents" / "escape"
        link_parent.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.symlink(outside, link_parent, target_is_directory=True)
        except OSError as exc:
            self.fail(f"symlink test fixture unavailable: {exc}")
        plan = copy.deepcopy(self.plan.to_dict())
        plan["files"][0]["relative_target"] = ".agents/escape/SKILL.md"
        with self.assertRaises(ProjectPinError):
            self._materialize(plan=plan)
        self.assertFalse((self.root / ".p2p" / "project-pin.json").exists())

    def test_p2p_state_parent_symlink_is_rejected(self) -> None:
        outside = Path(tempfile.mkdtemp(prefix="projection-pin-outside-", dir=REPO_ROOT / ".tmp"))
        self.addCleanup(lambda: shutil.rmtree(outside, ignore_errors=True))
        shutil.rmtree(self.root / ".p2p")
        try:
            os.symlink(outside, self.root / ".p2p", target_is_directory=True)
        except OSError as exc:
            self.fail(f"symlink test fixture unavailable: {exc}")
        with self.assertRaises(materialization.ProjectionMaterializationError):
            self._materialize()
        self.assertFalse((outside / "project-pin.json").exists())

    def test_unmanaged_collision_and_tampered_owned_refresh_are_not_overwritten(self) -> None:
        target = self.root / ".agents" / "skills" / "game.mengto.camera_controls" / "SKILL.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("Owner content\n", encoding="utf-8")
        with self.assertRaises(ProjectPinError):
            self._materialize()
        self.assertFalse((self.root / ".p2p" / "project-pin.json").exists())
        target.unlink()
        self._materialize()
        target.write_text("tampered after adoption\n", encoding="utf-8")
        with self.assertRaises(ProjectPinError):
            self._materialize(plan=self.plan)
        self.assertEqual(target.read_text(encoding="utf-8"), "tampered after adoption\n")

    def test_partial_failure_rolls_back_files_and_does_not_pin_ready(self) -> None:
        real_write = materialization._atomic_write
        calls = {"count": 0}

        def fail_second(path: Path, content: bytes) -> None:
            calls["count"] += 1
            if calls["count"] == 2:
                raise OSError("injected partial failure")
            real_write(path, content)

        with mock.patch.object(materialization, "_atomic_write", side_effect=fail_second):
            with self.assertRaises(materialization.ProjectionMaterializationError) as raised:
                self._materialize()
        self.assertIn("rollback=PASS", str(raised.exception))
        self.assertFalse((self.root / ".p2p" / "project-pin.json").exists())
        self.assertFalse((self.root / ".agents").exists())

    def test_img2threejs_false_and_tripo_unactivated_are_preserved(self) -> None:
        plan = self._make_plan(capability_id="img2threejs")
        selected = [
            {
                "capability_id": "img2threejs",
                "state": "DISCOVERED",
                "readiness": "UNKNOWN",
                "source_hash": plan.source_hash,
                "entrypoint_hash": plan.entrypoint_hash,
                "runtime_readiness": {"executable_registered": False},
            },
            {
                "capability_id": "tripo",
                "state": "PENDING",
                "readiness": "UNKNOWN",
                "source_hash": "a" * 64,
                "entrypoint_hash": "b" * 64,
                "runtime_readiness": {"activated": False, "executable_registered": False},
            },
        ]
        self._materialize(plan=plan, selected=selected)
        pin = self._pin()
        by_id = {item["capability_id"]: item for item in pin["selected_capabilities"]}
        self.assertFalse(by_id["img2threejs"]["runtime_readiness"]["executable_registered"])
        self.assertFalse(by_id["tripo"]["runtime_readiness"]["activated"])
        self.assertFalse(by_id["tripo"]["runtime_readiness"]["executable_registered"])
        self.assertTrue(ProjectContextBootstrap(self.root).is_ready())

    def test_builder_rejects_missing_runtime_truth_and_requires_managed_hashes(self) -> None:
        with self.assertRaises(ProjectPinError):
            build_projection_pin(
                project_root=self.root,
                project_id="fixture-projection-01",
                project_name="Projection Fixture",
                source_repository=SOURCE_REPOSITORY,
                source_commit=SOURCE_COMMIT,
                source_tree=SOURCE_TREE,
                selected_capabilities=self.selected,
                projection_plan=self.plan,
            )


if __name__ == "__main__":
    unittest.main()
