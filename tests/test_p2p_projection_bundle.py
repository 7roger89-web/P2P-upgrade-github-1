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
SCRIPTS_ROOT = REPO_ROOT / "scripts"
sys.path.insert(0, str(SYSTEM_ROOT))
sys.path.insert(0, str(SCRIPTS_ROOT))

import p2p_workflow  # noqa: E402
from p2p_capabilities import project_materialization as materialization  # noqa: E402
from p2p_capabilities.host_projection import HostSkillProjectionInput, project_host_skill  # noqa: E402
from p2p_capabilities.project_context import ProjectContextBootstrap  # noqa: E402
from p2p_capabilities.project_map import ProjectMapBuilder  # noqa: E402
from p2p_capabilities.project_pin import (  # noqa: E402
    PROJECT_PIN_V2_SCHEMA,
    PROJECTION_BUNDLE_SCHEMA,
    PROJECTION_ONLY,
    ProjectPinError,
    validate_pin,
)


SOURCE_REPOSITORY = "https://github.com/7roger89-web/P2P-upgrade-github-1.git"
SOURCE_COMMIT = "82d8a976381157aeece51fde33ef972496ff8ce7"
SOURCE_TREE = "ac2627b0a7ae1bfa8eef83992e4c76f325c0b905"
BOOTSTRAP_IDS = (
    "game.mengto.build_isometric_arpg",
    "game.mengto.camera_controls",
    "game.mengto.mobile_controls",
    "game.mengto.performance",
    "game.majid.threejs_qa_release",
)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


class P2PProjectionBundleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(
            tempfile.mkdtemp(
                prefix="projection-bundle-",
                dir=REPO_ROOT / ".tmp",
            )
        )
        self.addCleanup(lambda: shutil.rmtree(self.root, ignore_errors=True))
        (self.root / "README.md").write_text(
            "disposable atomic projection bundle fixture\n",
            encoding="utf-8",
        )
        self.policy_path = self.root / ".p2p" / "project-policy.json"
        self.policy_path.parent.mkdir(parents=True, exist_ok=True)
        self.policy_path.write_text(
            json.dumps(
                {
                    "schema_version": "p2p-codex-project-policy/1",
                    "project": "projection-bundle-fixture",
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
        registry = json.loads(
            (SYSTEM_ROOT / "p2p_capabilities" / "capabilities.json").read_text(
                encoding="utf-8"
            )
        )
        rows = registry if isinstance(registry, list) else registry["capabilities"]
        by_id = {
            row["CAPABILITY_ID"]: row
            for row in rows
            if isinstance(row, dict) and row.get("CAPABILITY_ID")
        }
        self.assertTrue(set(BOOTSTRAP_IDS).issubset(by_id))
        self.registry = by_id

    def _make_plan(
        self,
        capability_id: str,
        *,
        content: str | None = None,
    ):
        row = self.registry.get(capability_id)
        source_hash = (
            row["UPSTREAM_PROVENANCE"]["snapshot_sha256"]
            if row is not None
            else _sha256_bytes(f"source:{capability_id}".encode("utf-8"))
        )
        skill_content = content or f"# {capability_id}\nfixture skill content\n"
        entrypoint_hash = _sha256_bytes(skill_content.encode("utf-8"))
        item = HostSkillProjectionInput(
            skill_id=capability_id,
            display_name=capability_id,
            description="Disposable current-registry projection fixture",
            invocation_class="MODEL_ROUTABLE",
            invocation_policy="MODEL_ROUTABLE",
            context_entrypoint=f"references/{capability_id}.md",
            context_refs=(f"references/{capability_id}.md",),
            provenance={
                "vendor_path": (
                    row["UPSTREAM_PROVENANCE"]["vendor_path"]
                    if row is not None
                    else f".p2p/vendor/skill/{capability_id}"
                ),
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
            trust_level="HOST_CODE",
            load_stage="LOAD",
        )
        plan = project_host_skill(
            item,
            {
                "selected": True,
                "source_hash": source_hash,
                "entrypoint_content": skill_content,
            },
            {"host_kind": "codex", "scope": "project"},
        )
        self.assertEqual(plan.status, "READY")
        return plan

    def _selected(self, plans) -> list[dict[str, object]]:
        selected = []
        for plan in plans:
            raw = plan.to_dict() if hasattr(plan, "to_dict") else plan
            selected.append(
                {
                    "capability_id": raw["capability_id"],
                    "state": "DISCOVERED",
                    "readiness": "RESOLVED",
                    "source_hash": raw["source_hash"],
                    "entrypoint_hash": raw["entrypoint_hash"],
                    "runtime_readiness": {
                        "executable_registered": False,
                        "activated": False,
                    },
                }
            )
        return selected

    def _build(
        self,
        plans,
        *,
        selected: list[dict[str, object]] | None = None,
    ) -> dict[str, object]:
        return materialization.build_projection_bundle(
            project_root=self.root,
            project_id="fixture-projection-bundle-01",
            source_repository=SOURCE_REPOSITORY,
            source_commit=SOURCE_COMMIT,
            source_tree=SOURCE_TREE,
            selected_capabilities=selected or self._selected(plans),
            projection_plans=plans,
            policy_path=self.policy_path,
            context_path=self.context_path,
        )

    def _materialize(
        self,
        plans,
        *,
        selected: list[dict[str, object]] | None = None,
        **extra,
    ) -> dict[str, object]:
        return materialization.materialize_projection_bundle(
            project_root=self.root,
            project_id="fixture-projection-bundle-01",
            project_name="Projection Bundle Fixture",
            project_version="0.1.0",
            source_repository=SOURCE_REPOSITORY,
            source_commit=SOURCE_COMMIT,
            source_tree=SOURCE_TREE,
            selected_capabilities=selected or self._selected(plans),
            projection_plans=plans,
            policy_path=self.policy_path,
            context_path=self.context_path,
            **extra,
        )

    def _pin(self) -> dict[str, object]:
        return json.loads(
            (self.root / ".p2p" / "project-pin.json").read_text(encoding="utf-8")
        )

    @staticmethod
    def _rewrite_file(
        plan,
        *,
        index: int,
        relative_path: str | None = None,
        content: str | None = None,
    ) -> dict[str, object]:
        raw = copy.deepcopy(plan.to_dict() if hasattr(plan, "to_dict") else plan)
        item = raw["files"][index]
        if relative_path is not None:
            item["relative_target"] = relative_path
        if content is not None:
            item["content_or_template"] = content
            item["content_hash"] = _sha256_bytes(content.encode("utf-8"))
        return raw

    def test_one_plan_bundle_is_projection_only_and_old_api_stays_available(self) -> None:
        plan = self._make_plan("game.mengto.camera_controls")
        result = self._materialize([plan])

        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["capability_ids"], ["game.mengto.camera_controls"])
        self.assertEqual(result["managed_file_count"], 2)
        pin = self._pin()
        self.assertEqual(pin["schema"], PROJECT_PIN_V2_SCHEMA)
        self.assertEqual(pin["mode"], PROJECTION_ONLY)
        self.assertEqual(pin["projection"]["bundle"]["schema"], PROJECTION_BUNDLE_SCHEMA)
        self.assertEqual(validate_pin(self.root)["status"], "PASS")
        self.assertTrue(ProjectContextBootstrap(self.root).is_ready())

    def test_legacy_single_plan_can_migrate_to_one_plan_bundle_without_rewriting_files(self) -> None:
        plan = self._make_plan("game.mengto.camera_controls")
        selected = self._selected([plan])
        materialization.materialize_projection(
            project_root=self.root,
            project_id="fixture-projection-bundle-01",
            project_name="Projection Bundle Fixture",
            project_version="0.1.0",
            source_repository=SOURCE_REPOSITORY,
            source_commit=SOURCE_COMMIT,
            source_tree=SOURCE_TREE,
            selected_capabilities=selected,
            projection_plan=plan,
            policy_path=self.policy_path,
            context_path=self.context_path,
        )
        before = {
            path: path.read_bytes()
            for path in (self.root / ".agents").rglob("*")
            if path.is_file()
        }
        result = self._materialize([plan], selected=selected)

        self.assertEqual(result["changed_files"], 0)
        self.assertTrue(result["idempotent"])
        self.assertIn("bundle", self._pin()["projection"])
        self.assertEqual(
            {
                path: path.read_bytes()
                for path in (self.root / ".agents").rglob("*")
                if path.is_file()
            },
            before,
        )

    def test_five_registry_capabilities_have_one_pin_and_complete_union_ownership(self) -> None:
        plans = [self._make_plan(capability_id) for capability_id in BOOTSTRAP_IDS]
        result = self._materialize(plans)

        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["managed_file_count"], 10)
        pin = self._pin()
        self.assertEqual(
            [item["capability_id"] for item in pin["selected_capabilities"]],
            sorted(BOOTSTRAP_IDS),
        )
        bundle = pin["projection"]["bundle"]
        self.assertEqual(bundle["schema"], PROJECTION_BUNDLE_SCHEMA)
        self.assertEqual(
            [item["capability_id"] for item in bundle["plans"]],
            sorted(BOOTSTRAP_IDS),
        )
        self.assertEqual(
            {item["relative_path"] for item in pin["projection"]["managed_files"]},
            {
                file["relative_target"]
                for plan in plans
                for file in plan.to_dict()["files"]
            },
        )
        self.assertFalse((self.root / ".p2p" / "system").exists())
        self.assertTrue(ProjectContextBootstrap(self.root).is_ready())
        self.assertEqual(validate_pin(self.root)["managed_file_count"], 10)

    def test_bundle_identity_is_order_independent_and_same_content_is_deduped(self) -> None:
        first = self._make_plan("game.mengto.camera_controls")
        second = self._make_plan("game.mengto.performance")
        first_raw = first.to_dict()
        shared_path = first_raw["files"][1]["relative_target"]
        shared_content = first_raw["files"][1]["content_or_template"]
        second_shared = self._rewrite_file(
            second,
            index=1,
            relative_path=shared_path,
            content=shared_content,
        )
        plans = [first, second_shared]
        forward = self._build(plans)
        reverse = self._build(list(reversed(plans)))

        self.assertEqual(
            forward["bundle"]["bundle_sha256"],
            reverse["bundle"]["bundle_sha256"],
        )
        self.assertEqual(len(forward["plan_items"]), 3)
        self.assertEqual(
            forward["bundle"]["managed_files"],
            reverse["bundle"]["managed_files"],
        )

    def test_different_content_and_parent_child_conflicts_fail_closed_before_write(self) -> None:
        first = self._make_plan("game.mengto.camera_controls")
        second = self._make_plan("game.mengto.performance")
        shared_path = first.to_dict()["files"][1]["relative_target"]
        conflicting = self._rewrite_file(
            second,
            index=1,
            relative_path=shared_path,
            content="different managed content\n",
        )
        with self.assertRaises(materialization.ProjectionMaterializationError) as raised:
            self._materialize([first, conflicting])
        message = str(raised.exception)
        self.assertIn("MATERIALIZATION_BUNDLE_PATH_CONFLICT", message)
        self.assertIn(shared_path, message)
        self.assertIn("game.mengto.camera_controls", message)
        self.assertIn("game.mengto.performance", message)
        self.assertFalse((self.root / ".p2p" / "project-pin.json").exists())

        parent = self._rewrite_file(
            second,
            index=1,
            relative_path=".agents/skills",
            content=second.to_dict()["files"][1]["content_or_template"],
        )
        with self.assertRaises((ProjectPinError, materialization.ProjectionMaterializationError)) as raised:
            self._build([first, parent])
        self.assertIn("HIERARCHY_CONFLICT", str(raised.exception))
        self.assertFalse((self.root / ".p2p" / "project-pin.json").exists())

    def test_pin_is_written_once_after_all_bundle_files_are_verified(self) -> None:
        plans = [
            self._make_plan("game.mengto.camera_controls"),
            self._make_plan("game.mengto.performance"),
        ]
        observed: dict[str, object] = {"calls": 0}
        real_write_pin = materialization.write_pin

        def spy_write_pin(root: Path, pin: dict[str, object]) -> Path:
            observed["calls"] = int(observed["calls"]) + 1
            self.assertFalse((self.root / ".p2p" / "project-pin.json").exists())
            for plan in plans:
                for item in plan.to_dict()["files"]:
                    target = self.root / Path(*Path(item["relative_target"]).parts)
                    self.assertTrue(target.is_file())
                    self.assertEqual(
                        _sha256_bytes(target.read_bytes()),
                        item["content_hash"],
                    )
            return real_write_pin(root, pin)

        with mock.patch.object(materialization, "write_pin", side_effect=spy_write_pin):
            result = self._materialize(plans)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(observed["calls"], 1)
        self.assertTrue(result["pin_finalized"])

    def test_failure_during_bundle_write_rolls_back_everything_and_leaves_no_pin(self) -> None:
        plans = [
            self._make_plan("game.mengto.camera_controls"),
            self._make_plan("game.mengto.performance"),
            self._make_plan("game.mengto.mobile_controls"),
        ]
        real_write = materialization._atomic_write
        calls = {"count": 0}

        def fail_second(path: Path, content: bytes) -> None:
            calls["count"] += 1
            if calls["count"] == 2:
                raise OSError("injected bundle failure")
            real_write(path, content)

        with mock.patch.object(materialization, "_atomic_write", side_effect=fail_second):
            with self.assertRaises(materialization.ProjectionMaterializationError) as raised:
                self._materialize(plans)
        self.assertIn("rollback=PASS", str(raised.exception))
        self.assertFalse((self.root / ".p2p" / "project-pin.json").exists())
        self.assertFalse((self.root / ".agents").exists())

    def test_failed_upgrade_preserves_prior_valid_pin_and_projection(self) -> None:
        first = [
            self._make_plan("game.mengto.camera_controls"),
            self._make_plan("game.mengto.performance"),
        ]
        self._materialize(first)
        pin_before = (self.root / ".p2p" / "project-pin.json").read_bytes()
        files_before = {
            path: path.read_bytes()
            for path in (self.root / ".agents").rglob("*")
            if path.is_file()
        }
        third = self._make_plan("game.mengto.mobile_controls")
        real_write = materialization._atomic_write
        calls = {"count": 0}

        def fail_second_new_file(path: Path, content: bytes) -> None:
            calls["count"] += 1
            if calls["count"] == 2:
                raise OSError("injected upgrade failure")
            real_write(path, content)

        with mock.patch.object(materialization, "_atomic_write", side_effect=fail_second_new_file):
            with self.assertRaises(materialization.ProjectionMaterializationError) as raised:
                self._materialize(first + [third])
        self.assertIn("rollback=PASS", str(raised.exception))
        self.assertEqual((self.root / ".p2p" / "project-pin.json").read_bytes(), pin_before)
        self.assertEqual(
            {
                path: path.read_bytes()
                for path in (self.root / ".agents").rglob("*")
                if path.is_file()
            },
            files_before,
        )
        self.assertTrue(ProjectContextBootstrap(self.root).is_ready())

    def test_pin_write_failure_rolls_back_new_bundle_and_preserves_prior_pin(self) -> None:
        first = [self._make_plan("game.mengto.camera_controls")]
        self._materialize(first)
        pin_before = (self.root / ".p2p" / "project-pin.json").read_bytes()
        files_before = {
            path: path.read_bytes()
            for path in (self.root / ".agents").rglob("*")
            if path.is_file()
        }
        second = self._make_plan("game.mengto.performance")
        real_write_pin = materialization.write_pin

        def fail_after_pin_write(root: Path, pin: dict[str, object]) -> Path:
            result = real_write_pin(root, pin)
            raise OSError("injected post-write pin failure")

        with mock.patch.object(
            materialization,
            "write_pin",
            side_effect=fail_after_pin_write,
        ):
            with self.assertRaises(materialization.ProjectionMaterializationError) as raised:
                self._materialize(first + [second])
        self.assertIn("rollback=PASS", str(raised.exception))
        self.assertEqual((self.root / ".p2p" / "project-pin.json").read_bytes(), pin_before)
        self.assertEqual(
            {
                path: path.read_bytes()
                for path in (self.root / ".agents").rglob("*")
                if path.is_file()
            },
            files_before,
        )
        self.assertTrue(ProjectContextBootstrap(self.root).is_ready())

    def test_add_and_remove_capability_update_only_proven_managed_state(self) -> None:
        first = [
            self._make_plan("game.mengto.camera_controls"),
            self._make_plan("game.mengto.performance"),
        ]
        self._materialize(first)
        third = self._make_plan("game.mengto.mobile_controls")
        added = self._materialize(first + [third])
        self.assertEqual(added["transitions"]["ADD"], 2)
        self.assertEqual(added["transitions"]["UNCHANGED"], 4)
        for plan in first + [third]:
            for item in plan.to_dict()["files"]:
                self.assertTrue((self.root / Path(*Path(item["relative_target"]).parts)).is_file())

        removed_plan_paths = {
            item["relative_target"] for item in third.to_dict()["files"]
        }
        removed = self._materialize(first)
        self.assertEqual(removed["transitions"]["REMOVE_MANAGED"], 2)
        self.assertEqual(removed["managed_file_count"], 4)
        for relative in removed_plan_paths:
            self.assertFalse((self.root / Path(*Path(relative).parts)).exists())
        self.assertTrue(ProjectContextBootstrap(self.root).is_ready())

    def test_tampered_managed_file_and_unmanaged_collision_fail_closed(self) -> None:
        plan = self._make_plan("game.mengto.camera_controls")
        target = self.root / Path(*Path(plan.to_dict()["files"][0]["relative_target"]).parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("owner content\n", encoding="utf-8")
        with self.assertRaises(materialization.ProjectionMaterializationError):
            self._materialize([plan])
        self.assertEqual(target.read_text(encoding="utf-8"), "owner content\n")
        self.assertFalse((self.root / ".p2p" / "project-pin.json").exists())

        target.unlink()
        self._materialize([plan])
        pin_before = (self.root / ".p2p" / "project-pin.json").read_bytes()
        target.write_text("tampered managed content\n", encoding="utf-8")
        with self.assertRaises(materialization.ProjectionMaterializationError) as raised:
            self._materialize([plan])
        self.assertRegex(
            str(raised.exception),
            r"(TAMPERED_MANAGED_FILE|MANAGED_FILE_CONTENT_MISMATCH)",
        )
        self.assertEqual(target.read_text(encoding="utf-8"), "tampered managed content\n")
        self.assertEqual((self.root / ".p2p" / "project-pin.json").read_bytes(), pin_before)

    def test_traversal_absolute_and_symlink_escape_fail_closed(self) -> None:
        plan = self._make_plan("game.mengto.camera_controls")
        for bad_path in ("../escape.md", "..\\escape.md", "/escape.md", "C:/escape.md"):
            with self.subTest(bad_path=bad_path):
                bad = self._rewrite_file(plan, index=0, relative_path=bad_path)
                with self.assertRaises(
                    (ProjectPinError, materialization.ProjectionMaterializationError)
                ):
                    self._materialize([bad])
                self.assertFalse((self.root / ".p2p" / "project-pin.json").exists())

        outside = Path(
            tempfile.mkdtemp(prefix="projection-bundle-outside-", dir=REPO_ROOT / ".tmp")
        )
        self.addCleanup(lambda: shutil.rmtree(outside, ignore_errors=True))
        link_parent = self.root / ".agents" / "escape"
        link_parent.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.symlink(outside, link_parent, target_is_directory=True)
        except OSError as exc:
            self.fail(f"symlink test fixture unavailable: {exc}")
        escaped = self._rewrite_file(
            plan,
            index=0,
            relative_path=".agents/escape/SKILL.md",
        )
        with self.assertRaises((ProjectPinError, materialization.ProjectionMaterializationError)):
            self._materialize([escaped])
        self.assertFalse((outside / "SKILL.md").exists())
        self.assertFalse((self.root / ".p2p" / "project-pin.json").exists())

    def test_cross_plan_symlink_introduced_during_write_rolls_back(self) -> None:
        first = self._make_plan("game.mengto.camera_controls")
        second = self._make_plan("game.mengto.performance")
        outside = Path(
            tempfile.mkdtemp(prefix="projection-bundle-race-outside-", dir=REPO_ROOT / ".tmp")
        )
        self.addCleanup(lambda: shutil.rmtree(outside, ignore_errors=True))
        real_write = materialization._atomic_write
        calls = {"count": 0}
        link = self.root / ".agents" / "skills" / "game.mengto.performance"

        def introduce_link(path: Path, content: bytes) -> None:
            calls["count"] += 1
            real_write(path, content)
            if calls["count"] == 1:
                link.parent.parent.mkdir(parents=True, exist_ok=True)
                os.symlink(outside, link, target_is_directory=True)

        with mock.patch.object(materialization, "_atomic_write", side_effect=introduce_link):
            with self.assertRaises(materialization.ProjectionMaterializationError) as raised:
                self._materialize([first, second])
        self.assertIn("rollback=PASS", str(raised.exception))
        self.assertFalse((self.root / ".p2p" / "project-pin.json").exists())
        self.assertFalse((outside / "SKILL.md").exists())
        self.assertTrue(link.is_symlink())

    def test_stale_bundle_hash_and_manifest_ownership_are_rejected(self) -> None:
        plan = self._make_plan("game.mengto.camera_controls")
        self._materialize([plan])
        pin_path = self.root / ".p2p" / "project-pin.json"
        valid_pin_bytes = pin_path.read_bytes()
        pin = self._pin()
        pin["projection"]["bundle"]["bundle_sha256"] = "0" * 64
        pin_path.write_text(json.dumps(pin), encoding="utf-8")
        with self.assertRaises(ProjectPinError):
            validate_pin(self.root)

        pin_path.write_bytes(valid_pin_bytes)
        self._materialize([plan])
        pin = self._pin()
        pin["projection"]["managed_files"][0]["ownership"] = "OWNER_OWNED"
        pin_path.write_text(json.dumps(pin), encoding="utf-8")
        with self.assertRaises(ProjectPinError):
            validate_pin(self.root)

    def test_missing_constituent_unknown_capability_and_stale_previous_pin_fail_closed(self) -> None:
        first = self._make_plan("game.mengto.camera_controls")
        second = self._make_plan("game.mengto.performance")
        selected = self._selected([first, second])
        with self.assertRaises(materialization.ProjectionMaterializationError) as raised:
            self._build([first], selected=selected)
        self.assertIn("CAPABILITY_SET_MISMATCH", str(raised.exception))

        unknown_selected = selected + [
            {
                "capability_id": "game.unknown.not_registered",
                "state": "DISCOVERED",
                "readiness": "RESOLVED",
                "source_hash": "a" * 64,
                "entrypoint_hash": "b" * 64,
                "runtime_readiness": {"executable_registered": False},
            }
        ]
        with self.assertRaises(materialization.ProjectionMaterializationError):
            self._build([first, second], selected=unknown_selected)

        unknown_plan = self._make_plan("game.unknown.not_registered")
        with self.assertRaises(materialization.ProjectionMaterializationError) as unknown_raised:
            self._build([unknown_plan], selected=self._selected([unknown_plan]))
        self.assertIn("UNKNOWN_CAPABILITY", str(unknown_raised.exception))

        self._materialize([first, second])
        stale_pin = copy.deepcopy(self._pin())
        stale_pin["projection"]["bundle"]["bundle_sha256"] = "f" * 64
        with self.assertRaises(materialization.ProjectionMaterializationError):
            self._materialize([first, second], previous_pin=stale_pin)
        self.assertTrue(ProjectContextBootstrap(self.root).is_ready())

    def test_projection_only_bundle_keeps_external_capability_truth_inactive(self) -> None:
        plans = [self._make_plan(capability_id) for capability_id in BOOTSTRAP_IDS]
        self._materialize(plans)
        pin = self._pin()
        for entry in pin["selected_capabilities"]:
            self.assertFalse(entry["runtime_readiness"]["executable_registered"])
            self.assertFalse(entry["runtime_readiness"]["activated"])
        self.assertFalse((self.root / ".p2p" / "system").exists())

    def test_c18_c19_fastpath_stay_narrow_and_architecture_replacement_stays_blocked(self) -> None:
        plans = [self._make_plan(capability_id) for capability_id in BOOTSTRAP_IDS]
        bundle = self._build(plans)
        self.assertEqual(
            [item["capability_id"] for item in bundle["bundle"]["selected_capabilities"]],
            sorted(BOOTSTRAP_IDS),
        )
        request = "Write a precise Arena Agent prompt to improve the third-person camera."
        requirement = p2p_workflow.derive_orchestration_requirement(
            request,
            {"project_root": str(REPO_ROOT)},
            package_hint=str(REPO_ROOT),
        )
        selection = p2p_workflow.select_agents(
            request,
            {"project_root": str(REPO_ROOT)},
            {},
            requirement,
        )
        self.assertEqual(requirement["profile"]["task_kind"], "PROMPT_COMPOSITION")
        self.assertEqual(requirement["worker_strategy"], "DIRECT")
        self.assertEqual(requirement["context_class"], "MINIMAL")
        self.assertEqual(requirement["reasoning_class"], "LOW")
        self.assertEqual(requirement["verification_class"], "DETERMINISTIC")
        self.assertEqual(selection["selected_agents"], [])

        architecture = p2p_workflow.derive_orchestration_requirement(
            "Replace the authoritative world-simulation architecture.",
            {"project_root": str(REPO_ROOT)},
            package_hint=str(REPO_ROOT),
        )
        self.assertEqual(architecture["verification_class"], "HIGH_RISK")
        self.assertEqual(architecture["worker_strategy"], "BLOCKED")
        self.assertEqual(architecture["status"], "BLOCKED")


if __name__ == "__main__":
    unittest.main()
