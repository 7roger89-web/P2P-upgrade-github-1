"""Focused static contract tests for P2P-GAME-TRUYEN-MPFB-ADAPTER-01."""

from __future__ import annotations

import hashlib
import json
import os
import re
import struct
import subprocess
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_ROOT = REPO_ROOT / ".p2p" / "system"
sys.path.insert(0, str(SYSTEM_ROOT))

from p2p_capabilities import asset_provenance, character_recipe, glb_validator, mpfb_adapter, mpfb_blender_entrypoint, windows_network_isolation  # noqa: E402


def recipe_fixture() -> dict[str, object]:
    return {
        "schema": "p2p-character-recipe/1",
        "character_id": "Oak",
        "body": {"gender": "neutral", "age": 0.45, "weight": 0.5, "muscle": 0.35},
        "proportions": {
            "head_scale": 1.0,
            "shoulder_width": 1.0,
            "torso_length": 1.0,
            "arm_length": 1.0,
            "leg_length": 1.0,
        },
        "base": {"model": "human_base", "asset_id": "mpfb2-core:base-mesh"},
        "skin": {"material_id": "mpfb2-core:skin-default"},
        "hair": {"asset_id": "mpfb2-core:hair-default"},
        "clothing": {"items": ["mpfb2-core:clothing-basic"]},
        "rig": {"preset": "GAMEENGINE", "skinning": "MPFB_BUILT_IN_WEIGHTS"},
        "scale": 1.0,
        "export": {"format": "glb", "gltf_version": "2.0", "embed_resources": True},
        "assets": [
            "mpfb2-core:base-mesh",
            "mpfb2-core:skin-default",
            "mpfb2-core:hair-default",
            "mpfb2-core:clothing-basic",
        ],
    }


def provenance_fixture(recipe: dict[str, object], glb_sha256: str) -> dict[str, object]:
    return {
        "schema": "p2p-character-asset-provenance/1",
        "character_id": recipe["character_id"],
        "recipe_sha256": character_recipe.recipe_sha256(recipe),
        "glb_sha256": glb_sha256,
        "rights_policy": "CORE_CC0_ONLY",
        "rigging": {
            "generator": "MPFB2",
            "generator_version": "2.0.17",
            "rig_preset": "GAMEENGINE",
            "skinning": "MPFB_BUILT_IN_WEIGHTS",
        },
        "resources": [],
        "assets": [
            {
                "asset_id": asset_id,
                "source": f"MPFB2 core assets/{asset_id.split(':', 1)[1]}",
                "license": "CC0-1.0",
                "sha256": hashlib.sha256(asset_id.encode("ascii")).hexdigest(),
                "commercial_use": True,
                "derivative_use": True,
                "redistribution": True,
            }
            for asset_id in recipe["assets"]
        ],
    }


def gltf_fixture(*, include_joints: bool = True, external_buffer: bool = False) -> dict[str, object]:
    attributes: dict[str, int] = {"POSITION": 0, "WEIGHTS_0": 2}
    if include_joints:
        attributes["JOINTS_0"] = 1
    document: dict[str, object] = {
        "asset": {"version": "2.0"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0, "skin": 0, "children": [1]}, {"name": "GameEngineRoot"}],
        "meshes": [{"primitives": [{"attributes": attributes}]}],
        "skins": [{"joints": [1], "skeleton": 1}],
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": 1, "type": "VEC3"},
            {"bufferView": 1, "componentType": 5123, "count": 1, "type": "VEC4"},
            {"bufferView": 2, "componentType": 5126, "count": 1, "type": "VEC4"},
        ],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0, "byteLength": 16},
            {"buffer": 0, "byteOffset": 16, "byteLength": 16},
            {"buffer": 0, "byteOffset": 32, "byteLength": 16},
        ],
        "buffers": [{"byteLength": 48, **({"uri": "mesh.bin"} if external_buffer else {})}],
    }
    return document


def write_glb(path: Path, document: dict[str, object]) -> None:
    json_chunk = json.dumps(document, separators=(",", ":")).encode("utf-8")
    json_chunk += b" " * ((-len(json_chunk)) % 4)
    binary = bytes(range(48))
    binary += b"\x00" * ((-len(binary)) % 4)
    chunks = struct.pack("<I4s", len(json_chunk), b"JSON") + json_chunk
    chunks += struct.pack("<I4s", len(binary), b"BIN\x00") + binary
    path.write_bytes(struct.pack("<4sII", b"glTF", 2, 12 + len(chunks)) + chunks)


class RecipeAndProvenanceTests(unittest.TestCase):
    def test_checked_in_schema_ids_match_runtime_contracts(self) -> None:
        recipe_schema = json.loads((REPO_ROOT / "docs/p2p-development/capability-catalog/game-asset-forge/character.recipe.schema.json").read_text(encoding="utf-8"))
        reference_schema = json.loads((REPO_ROOT / "docs/p2p-development/capability-catalog/game-asset-forge/visual-reference-pack.schema.json").read_text(encoding="utf-8"))
        provenance_schema = json.loads((REPO_ROOT / "docs/p2p-development/capability-catalog/game-asset-forge/asset-provenance.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(recipe_schema["$id"], character_recipe.RECIPE_SCHEMA)
        self.assertEqual(reference_schema["$id"], character_recipe.VISUAL_REFERENCE_PACK_SCHEMA)
        self.assertEqual(provenance_schema["$id"], asset_provenance.PROVENANCE_SCHEMA)

    def test_recipe_is_allowlisted_and_images_are_not_executable_input(self) -> None:
        recipe = recipe_fixture()
        self.assertEqual(character_recipe.validate_recipe(recipe)["character_id"], "Oak")
        recipe["reference_images"] = ["front.png"]
        with self.assertRaises(character_recipe.CharacterRecipeError):
            character_recipe.validate_recipe(recipe)

    def test_unknown_nested_recipe_field_is_rejected(self) -> None:
        recipe = recipe_fixture()
        recipe["rig"]["extra"] = "arbitrary"  # type: ignore[index]
        with self.assertRaises(character_recipe.CharacterRecipeError):
            character_recipe.validate_recipe(recipe)

    def test_visual_reference_pack_has_exact_six_non_executable_views(self) -> None:
        names = [
            "full_body_front",
            "full_body_three_quarter",
            "full_body_side",
            "full_body_back",
            "face_front",
            "face_three_quarter",
        ]
        pack = {
            "schema": "p2p-visual-reference-pack/1",
            "views": [{"view_id": name, "path": f"references/{name}.png", "sha256": "a" * 64} for name in names],
        }
        self.assertEqual(len(character_recipe.validate_visual_reference_pack(pack)["views"]), 6)

    def test_core_cc0_provenance_and_exact_recipe_binding(self) -> None:
        recipe = recipe_fixture()
        provenance = provenance_fixture(recipe, "b" * 64)
        normalized = asset_provenance.validate_asset_provenance(provenance)
        asset_provenance.validate_recipe_asset_binding(recipe, normalized)
        self.assertEqual(normalized["rights_policy"], "CORE_CC0_ONLY")

    def test_third_party_asset_without_manifest_is_rejected(self) -> None:
        recipe = recipe_fixture()
        recipe["assets"] = ["third-party:hair-pack"]
        provenance = provenance_fixture(recipe, "b" * 64)
        provenance["assets"][0]["asset_id"] = "third-party:hair-pack"  # type: ignore[index]
        provenance["assets"][0]["license"] = "CC-BY-4.0"  # type: ignore[index]
        with self.assertRaises(asset_provenance.AssetProvenanceError):
            asset_provenance.validate_recipe_asset_binding(recipe, provenance)

    def test_custom_asset_requires_separate_rights_gate(self) -> None:
        recipe = recipe_fixture()
        recipe["assets"] = ["user-custom:hair"]
        provenance = provenance_fixture(recipe, "b" * 64)
        provenance["assets"][0]["asset_id"] = "user-custom:hair"  # type: ignore[index]
        with self.assertRaises(asset_provenance.AssetProvenanceError):
            asset_provenance.validate_asset_provenance(provenance)


class AdapterBoundaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(dir=REPO_ROOT, prefix=".tmp-mpfb-adapter-test-")
        self.workspace = Path(self.temp.name)
        self.blender = self.workspace / "blender.exe"
        self.blender.write_bytes(b"static blender fixture; never executed")
        self.mpfb_root = self.workspace / "mpfb2"
        self.mpfb_root.mkdir()
        core_assets = {
            "mpfb2-core:base-mesh": "core-assets/base-mesh.obj",
            "mpfb2-core:skin-default": "core-assets/skin-default.mhmat",
            "mpfb2-core:hair-default": "core-assets/hair-default.blend",
            "mpfb2-core:clothing-basic": "core-assets/clothing-basic.mhclo",
        }
        core_manifest: dict[str, object] = {}
        for asset_id, relative_path in core_assets.items():
            asset_path = self.mpfb_root / relative_path
            asset_path.parent.mkdir(parents=True, exist_ok=True)
            asset_path.write_bytes(asset_id.encode("ascii"))
            core_manifest[asset_id] = {
                "relative_path": relative_path,
                "sha256": hashlib.sha256(asset_path.read_bytes()).hexdigest(),
                "license": "CC0-1.0",
            }
        root_hash = mpfb_adapter.hash_provisioned_root(self.mpfb_root)
        (self.mpfb_root / "provisioning-manifest.json").write_text(
            json.dumps(
                {
                    "schema": "p2p-mpfb2-provisioning/1",
                    "version": mpfb_adapter.MPFB_VERSION,
                    "release_sha": mpfb_adapter.MPFB_RELEASE_SHA,
                    "release_tree": mpfb_adapter.MPFB_RELEASE_TREE,
                    "root_sha256": root_hash,
                    "core_assets": core_manifest,
                }
            ),
            encoding="utf-8",
        )
        (self.workspace / "character.recipe.json").write_text(json.dumps(recipe_fixture()), encoding="utf-8")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _plan(self, **kwargs: object) -> mpfb_adapter.MpfbExecutionPlan:
        return mpfb_adapter.build_execution_plan(
            blender_executable=self.blender,
            workspace_root=self.workspace,
            job_id="Oak",
            **kwargs,
        )

    def test_command_is_explicit_background_allowlisted_and_shell_free(self) -> None:
        old_secret = os.environ.get("P2P_TEST_SECRET")
        os.environ["P2P_TEST_SECRET"] = "must-not-inherit"
        try:
            plan = self._plan(timeout_seconds=42)
        finally:
            if old_secret is None:
                os.environ.pop("P2P_TEST_SECRET", None)
            else:
                os.environ["P2P_TEST_SECRET"] = old_secret
        self.assertEqual(plan.argv[1:5], ("--background", "--python", plan.argv[3], "--"))
        self.assertEqual(plan.argv[3], (REPO_ROOT / mpfb_adapter.BLENDER_ENTRYPOINT).as_posix())
        self.assertIn("--asset-policy", plan.argv)
        self.assertIn("CORE_CC0_ONLY", plan.argv)
        self.assertIn("--network", plan.argv)
        self.assertNotIn("P2P_TEST_SECRET", plan.environment)
        self.assertFalse(any("PROXY" in key.upper() or "SECRET" in key.upper() for key in plan.environment))
        self.assertFalse(plan.execution_authorized)

    def test_dedicated_entrypoint_rejects_unknown_duplicate_and_arbitrary_script_arguments(self) -> None:
        arguments = ["--recipe", "character.recipe.json", "--output-root", "output"]
        with self.assertRaisesRegex(mpfb_blender_entrypoint.BlenderEntrypointError, "ARGUMENT_SET_INVALID"):
            mpfb_blender_entrypoint.parse_blender_script_arguments(arguments)
        with self.assertRaisesRegex(mpfb_blender_entrypoint.BlenderEntrypointError, "ARGUMENT_NOT_ALLOWLISTED"):
            mpfb_blender_entrypoint.parse_blender_script_arguments(["--python", "other.py"])
        with self.assertRaisesRegex(mpfb_blender_entrypoint.BlenderEntrypointError, "ARGUMENT_DUPLICATE"):
            mpfb_blender_entrypoint.parse_blender_script_arguments(["--network", "deny", "--network", "deny"])

    def test_dedicated_entrypoint_binds_recipe_and_exact_mpfb_pin(self) -> None:
        output = self.workspace / "output"
        output.mkdir()
        arguments = {
            "--recipe": "character.recipe.json",
            "--output-root": "output",
            "--mpfb-root": "mpfb2",
            "--mpfb-manifest": "mpfb2/provisioning-manifest.json",
            "--character-id": "Oak",
            "--mpfb-version": mpfb_adapter.MPFB_VERSION,
            "--mpfb-release-sha": mpfb_adapter.MPFB_RELEASE_SHA,
            "--asset-policy": "CORE_CC0_ONLY",
            "--network": "deny",
        }
        job = mpfb_blender_entrypoint.validate_job(arguments, workspace_root=self.workspace)
        self.assertEqual(job.recipe["character_id"], "Oak")
        self.assertEqual(job.manifest["release_tree"], mpfb_adapter.MPFB_RELEASE_TREE)
        arguments["--mpfb-release-sha"] = "0" * 40
        with self.assertRaisesRegex(mpfb_blender_entrypoint.BlenderEntrypointError, "MPFB_PIN_MISMATCH"):
            mpfb_blender_entrypoint.validate_job(arguments, workspace_root=self.workspace)

    def test_network_request_and_traversal_fail_closed(self) -> None:
        with self.assertRaises(mpfb_adapter.MpfbAdapterError):
            self._plan(network_access=True)
        with self.assertRaises(mpfb_adapter.MpfbAdapterError):
            self._plan(recipe_path="../escape.json")
        with self.assertRaises(mpfb_adapter.MpfbAdapterError):
            self._plan(output_root="../outside")

    def test_symlink_escape_is_rejected_when_platform_supports_symlinks(self) -> None:
        link = self.workspace / "mpfb-link"
        try:
            link.symlink_to(self.mpfb_root, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("symlink creation is unavailable")
        with self.assertRaises(mpfb_adapter.MpfbAdapterError):
            self._plan(mpfb_root="mpfb-link")

    def test_wrong_pinned_provisioning_manifest_is_rejected(self) -> None:
        manifest = self.mpfb_root / "provisioning-manifest.json"
        document = json.loads(manifest.read_text(encoding="utf-8"))
        document["release_sha"] = "d" * 40
        manifest.write_text(json.dumps(document), encoding="utf-8")
        with self.assertRaises(mpfb_adapter.MpfbAdapterError):
            self._plan()

    def test_core_asset_manifest_hash_and_recipe_binding_are_required(self) -> None:
        manifest = self.mpfb_root / "provisioning-manifest.json"
        document = json.loads(manifest.read_text(encoding="utf-8"))
        document["core_assets"]["mpfb2-core:skin-default"]["sha256"] = "e" * 64
        manifest.write_text(json.dumps(document), encoding="utf-8")
        with self.assertRaisesRegex(mpfb_adapter.MpfbAdapterError, "MPFB_CORE_ASSET_HASH_MISMATCH"):
            self._plan()

    def test_execution_requires_explicit_authorization_and_does_not_launch(self) -> None:
        plan = self._plan()
        popen = mock.Mock(side_effect=AssertionError("Blender must not launch in this workstream"))
        with self.assertRaisesRegex(mpfb_adapter.MpfbAdapterError, "NOT_AUTHORIZED"):
            mpfb_adapter.execute_plan(plan, popen_factory=popen)
        popen.assert_not_called()

    def test_undeclared_outputs_fail_closed(self) -> None:
        output = self.workspace / "output"
        output.mkdir()
        (output / "Oak.glb").write_bytes(b"fixture")
        (output / "Oak.asset-provenance.json").write_text("{}", encoding="utf-8")
        (output / "unexpected.log").write_text("fixture", encoding="utf-8")
        with self.assertRaisesRegex(mpfb_adapter.MpfbAdapterError, "UNDECLARED"):
            mpfb_adapter.validate_output_directory(output, ("Oak.glb", "Oak.asset-provenance.json"))

    def test_timeout_uses_process_tree_termination_without_shell(self) -> None:
        process = mock.Mock(pid=4321)
        runner = mock.Mock()
        mpfb_adapter._terminate_process_tree(process, platform_name="nt", termination_runner=runner)
        runner.assert_called_once()
        args, kwargs = runner.call_args
        self.assertEqual(args[0], ["taskkill", "/PID", "4321", "/T", "/F"])
        self.assertFalse(kwargs["shell"])

    def test_timeout_path_terminates_tree_and_never_reports_execution(self) -> None:
        plan = self._plan()
        events: list[str] = []

        class FakeIsolation:
            receipt = windows_network_isolation.NetworkIsolationReceipt(
                identity="fixture",
                mechanism="fixture",
                executable_path=str(plan.argv[0]),
                rule_name="fixture",
                platform="nt",
                privilege_required="fixture",
            )

            def __enter__(self):
                events.append("network-enter")
                self.receipt.setup_result = "PASS"
                self.receipt.enforcement_result = "PASS"
                return self

            def __exit__(self, exc_type, exc_value, traceback):
                events.append("network-exit")
                self.receipt.cleanup_result = "PASS"
                return False

        def isolation_factory(*args: object, **kwargs: object) -> FakeIsolation:
            events.append("network-create")
            return FakeIsolation()

        class TimeoutProcess:
            pid = 4321
            returncode = None

            def communicate(self, *, timeout: int) -> tuple[str, str]:
                raise subprocess.TimeoutExpired(cmd=list(plan.argv), timeout=timeout)

        popen = mock.Mock(return_value=TimeoutProcess())
        runner = mock.Mock()
        with self.assertRaises(mpfb_adapter.MpfbExecutionTimeout):
            mpfb_adapter.execute_plan(
                plan,
                execution_authorized=True,
                popen_factory=popen,
                termination_runner=runner,
                platform_name="nt",
                network_isolation_factory=isolation_factory,
            )
        popen.assert_called_once()
        runner.assert_called_once()
        self.assertEqual(events, ["network-create", "network-enter", "network-exit"])

    def test_network_isolation_failure_happens_before_spawn(self) -> None:
        plan = self._plan()
        popen = mock.Mock(side_effect=AssertionError("spawn must not happen"))
        events: list[str] = []

        class FailedIsolation:
            def __enter__(self):
                events.append("network-enter")
                raise windows_network_isolation.NetworkIsolationError("fixture unavailable")

            def __exit__(self, exc_type, exc_value, traceback):
                events.append("network-exit")
                return False

        def isolation_factory(*args: object, **kwargs: object) -> FailedIsolation:
            events.append("network-create")
            return FailedIsolation()

        with self.assertRaises(windows_network_isolation.NetworkIsolationError):
            mpfb_adapter.execute_plan(
                plan,
                execution_authorized=True,
                popen_factory=popen,
                network_isolation_factory=isolation_factory,
            )
        popen.assert_not_called()
        self.assertEqual(events, ["network-create", "network-enter"])

    def test_network_isolation_is_released_after_blender_failure(self) -> None:
        plan = self._plan()
        events: list[str] = []

        class FakeIsolation:
            receipt = windows_network_isolation.NetworkIsolationReceipt(
                identity="fixture",
                mechanism="fixture",
                executable_path=str(plan.argv[0]),
                rule_name="fixture",
                platform="nt",
                privilege_required="fixture",
            )

            def __enter__(self):
                events.append("network-enter")
                self.receipt.setup_result = "PASS"
                self.receipt.enforcement_result = "PASS"
                return self

            def __exit__(self, exc_type, exc_value, traceback):
                events.append("network-exit")
                self.receipt.cleanup_result = "PASS"
                return False

        class FailedProcess:
            returncode = 17

            def communicate(self, *, timeout: int) -> tuple[str, str]:
                events.append("communicate")
                return "", ""

        def isolation_factory(*args: object, **kwargs: object) -> FakeIsolation:
            events.append("network-create")
            return FakeIsolation()

        def popen(*args: object, **kwargs: object) -> FailedProcess:
            events.append("spawn")
            return FailedProcess()

        with self.assertRaisesRegex(mpfb_adapter.MpfbAdapterError, "BLENDER_COMMAND_FAILED"):
            mpfb_adapter.execute_plan(
                plan,
                execution_authorized=True,
                popen_factory=popen,
                network_isolation_factory=isolation_factory,
            )
        self.assertEqual(events, ["network-create", "network-enter", "spawn", "communicate", "network-exit"])

    def test_network_isolation_is_released_after_success_and_receipt_is_returned(self) -> None:
        plan = self._plan()
        events: list[str] = []

        class FakeIsolation:
            receipt = windows_network_isolation.NetworkIsolationReceipt(
                identity="fixture",
                mechanism="fixture",
                executable_path=str(plan.argv[0]),
                rule_name="fixture",
                platform="nt",
                privilege_required="fixture",
            )

            def __enter__(self):
                events.append("network-enter")
                self.receipt.setup_result = "PASS"
                self.receipt.enforcement_result = "PASS"
                return self

            def __exit__(self, exc_type, exc_value, traceback):
                events.append("network-exit")
                self.receipt.cleanup_result = "PASS"
                return False

        class SuccessProcess:
            returncode = 0

            def communicate(self, *, timeout: int) -> tuple[str, str]:
                events.append("communicate")
                glb = plan.output_root / "Oak.glb"
                write_glb(glb, gltf_fixture())
                provenance = provenance_fixture(recipe_fixture(), hashlib.sha256(glb.read_bytes()).hexdigest())
                (plan.output_root / "Oak.asset-provenance.json").write_text(json.dumps(provenance), encoding="utf-8")
                return "stdout", "stderr"

        def isolation_factory(*args: object, **kwargs: object) -> FakeIsolation:
            events.append("network-create")
            return FakeIsolation()

        def popen(*args: object, **kwargs: object) -> SuccessProcess:
            events.append("spawn")
            return SuccessProcess()

        result = mpfb_adapter.execute_plan(
            plan,
            execution_authorized=True,
            popen_factory=popen,
            network_isolation_factory=isolation_factory,
        )
        self.assertEqual(result["status"], "EXECUTED_AND_STRUCTURALLY_VALID")
        self.assertEqual(result["network_isolation"]["enforcement_result"], "PASS")
        self.assertEqual(result["network_isolation"]["cleanup_result"], "PASS")
        self.assertEqual(events, ["network-create", "network-enter", "spawn", "communicate", "network-exit"])

    def test_arbitrary_python_entrypoint_is_rejected_before_network_setup(self) -> None:
        plan = self._plan()
        tampered = replace(plan, argv=plan.argv[:3] + (str(self.workspace / "arbitrary.py"),) + plan.argv[4:])
        popen = mock.Mock(side_effect=AssertionError("spawn must not happen"))
        network_factory = mock.Mock(side_effect=AssertionError("network must not start"))
        with self.assertRaisesRegex(mpfb_adapter.MpfbAdapterError, "ENTRYPOINT_NOT_ALLOWLISTED"):
            mpfb_adapter.execute_plan(
                tampered,
                execution_authorized=True,
                popen_factory=popen,
                network_isolation_factory=network_factory,
            )
        popen.assert_not_called()
        network_factory.assert_not_called()

    def test_recipe_change_after_plan_is_rejected_before_network_setup(self) -> None:
        plan = self._plan()
        recipe = recipe_fixture()
        recipe["body"]["age"] = 0.46  # type: ignore[index]
        (self.workspace / "character.recipe.json").write_text(json.dumps(recipe), encoding="utf-8")
        popen = mock.Mock(side_effect=AssertionError("spawn must not happen"))
        network_factory = mock.Mock(side_effect=AssertionError("network must not start"))
        with self.assertRaisesRegex(mpfb_adapter.MpfbAdapterError, "RECIPE_CHANGED_AFTER_PLAN"):
            mpfb_adapter.execute_plan(
                plan,
                execution_authorized=True,
                popen_factory=popen,
                network_isolation_factory=network_factory,
            )
        popen.assert_not_called()
        network_factory.assert_not_called()


class GlbValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(dir=REPO_ROOT, prefix=".tmp-mpfb-glb-test-")
        self.root = Path(self.temp.name)
        self.recipe = recipe_fixture()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _write_valid_output(self, *, include_joints: bool = True, external_buffer: bool = False) -> tuple[Path, Path]:
        glb = self.root / "Oak.glb"
        write_glb(glb, gltf_fixture(include_joints=include_joints, external_buffer=external_buffer))
        provenance = self.root / "Oak.asset-provenance.json"
        document = provenance_fixture(self.recipe, hashlib.sha256(glb.read_bytes()).hexdigest())
        if external_buffer:
            document["resources"] = [{"uri": "mesh.bin", "sha256": "e" * 64}]
        provenance.write_text(json.dumps(document), encoding="utf-8")
        return glb, provenance

    def test_rigged_glb_requires_glb20_scene_mesh_skin_joints_weights_and_root(self) -> None:
        glb, provenance = self._write_valid_output()
        result = glb_validator.validate_glb_output(glb, provenance, self.recipe)
        self.assertEqual(result["status"], "STRUCTURALLY_VALID")
        self.assertEqual(result["rig_preset"], "GAMEENGINE")

    def test_missing_joints_or_external_resource_binding_is_rejected(self) -> None:
        glb, provenance = self._write_valid_output(include_joints=False)
        with self.assertRaises(glb_validator.GlbStructuralError):
            glb_validator.validate_glb_output(glb, provenance, self.recipe)
        glb, provenance = self._write_valid_output(external_buffer=True)
        provenance_document = json.loads(provenance.read_text(encoding="utf-8"))
        provenance_document["resources"] = []
        provenance.write_text(json.dumps(provenance_document), encoding="utf-8")
        with self.assertRaises(glb_validator.GlbStructuralError):
            glb_validator.validate_glb_output(glb, provenance, self.recipe)

    def test_glb_hash_and_output_naming_are_bound_to_provenance(self) -> None:
        glb, provenance = self._write_valid_output()
        glb.write_bytes(glb.read_bytes() + b"x")
        with self.assertRaisesRegex(glb_validator.GlbStructuralError, "HASH_MISMATCH"):
            glb_validator.validate_glb_output(glb, provenance, self.recipe)


class ProjectionAndSourceBindingTests(unittest.TestCase):
    def test_selected_catalog_and_existing_projection_are_bound_without_new_registry(self) -> None:
        catalog = json.loads((REPO_ROOT / "docs/p2p-development/capability-catalog/game-asset-forge/capability-catalog.json").read_text(encoding="utf-8"))
        candidate = next(item for item in catalog["candidates"] if item["candidate_id"] == "CAND-ASSET-FORGE-002")
        self.assertEqual(candidate["pinned_sha_or_version"], mpfb_adapter.MPFB_RELEASE_SHA)
        self.assertEqual(candidate["pinned_release_tree"], mpfb_adapter.MPFB_RELEASE_TREE)
        self.assertEqual(candidate["static_production_clearance"], "SAFE_CONDITIONAL")
        self.assertEqual(candidate["third_party_asset_policy"], "DENY_BY_DEFAULT")

        capabilities = json.loads((SYSTEM_ROOT / "p2p_capabilities/capabilities.json").read_text(encoding="utf-8"))
        ids = [item["CAPABILITY_ID"] for item in capabilities["capabilities"]]
        self.assertEqual(len(ids), 65)
        self.assertEqual(len(ids), len(set(ids)))
        selected = next(item for item in capabilities["capabilities"] if item["CAPABILITY_ID"] == "game.character.generate")
        self.assertEqual(selected["TYPE"], "KNOWLEDGE_SOURCE")
        self.assertEqual(selected["SEMANTIC_KIND"], "ADAPTER")
        self.assertEqual(selected["UPSTREAM_PROVENANCE"]["release_sha"], mpfb_adapter.MPFB_RELEASE_SHA)
        self.assertEqual(selected["UPSTREAM_PROVENANCE"]["release_tree"], mpfb_adapter.MPFB_RELEASE_TREE)

        routing = json.loads((REPO_ROOT / "docs/p2p-development/capability-catalog/ui-game-threejs/project-profile-routing.json").read_text(encoding="utf-8"))
        self.assertIn("game.character.generate", routing["profiles"]["THREEJS_GAME"]["optional_capabilities"])
        self.assertIn("game.character.generate", routing["profiles"]["R3F_GAME"]["optional_capabilities"])
        self.assertEqual((REPO_ROOT / ".p2p/vendor/provenance/p2p-game-truyen-mpfb-adapter-01.json").exists(), True)


def isolation_command_kind(command: list[str]) -> str:
    """Classify one canonical isolation command so tests can assert exact order."""
    if command[0] == "powershell.exe" and "Get-NetFirewallProfile" in command[-1]:
        return "profile-probe"
    if command[0] == "powershell.exe" and "Get-NetFirewallRule" in command[-1]:
        return "rule-verify"
    if command[0] == "netsh.exe":
        return f"netsh-{command[3]}"
    raise AssertionError(f"unexpected command {command}")


def display_name_from_verify_command(command: list[str]) -> str:
    """Return the exact rule name the canonical verification queries.

    The canonical verify command must query the netsh-created rule through
    its ``-DisplayName`` surface (the legacy ``-Name`` parameter queries
    InstanceID, which does not match the netsh rule name).  A verify command
    that no longer carries the exact ``-DisplayName '<rule>'`` literal is a
    contract break, so the helper fails loudly instead of guessing.
    """
    match = re.search(r"Get-NetFirewallRule -DisplayName '([^']+)'", command[-1])
    assert match is not None, "canonical verification must query the exact -DisplayName surface"
    return match.group(1)


class NetworkIsolationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(dir=REPO_ROOT, prefix=".tmp-mpfb-network-test-")
        self.root = Path(self.temp.name)
        self.blender = self.root / "blender.exe"
        self.blender.write_bytes(b"static blender fixture; never executed")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_firewall_rule_is_exact_path_bound_and_released(self) -> None:
        commands: list[list[str]] = []
        rule_present = False

        def runner(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
            nonlocal rule_present
            commands.append(command)
            if command[0] == "powershell.exe" and "Get-NetFirewallProfile" in command[-1]:
                return subprocess.CompletedProcess(command, 0, "[true,true,true]", "")
            if command[0] == "powershell.exe" and "Get-NetFirewallRule" in command[-1]:
                payload = {
                    "DisplayName": display_name_from_verify_command(command),
                    "Enabled": True,
                    "Direction": "Outbound",
                    "Action": "Block",
                    "Program": str(self.blender.resolve()),
                }
                return subprocess.CompletedProcess(command, 0, json.dumps(payload), "")
            if command[0] == "netsh.exe" and command[3] == "show":
                return subprocess.CompletedProcess(command, 0 if rule_present else 1, "", "")
            if command[0] == "netsh.exe" and command[3] == "add":
                rule_present = True
                return subprocess.CompletedProcess(command, 0, "Ok.", "")
            if command[0] == "netsh.exe" and command[3] == "delete":
                rule_present = False
                return subprocess.CompletedProcess(command, 0, "Ok.", "")
            raise AssertionError(command)

        resolved = self.blender.resolve()
        with mock.patch.object(windows_network_isolation, "_validate_executable", return_value=resolved):
            lease = windows_network_isolation.create_network_isolation(
                self.blender,
                "Oak:fixture",
                platform_name="nt",
                runner=runner,
            )
        with lease:
            self.assertEqual(lease.receipt.enforcement_result, "PASS")
            add_command = next(command for command in commands if command[0] == "netsh.exe" and command[3] == "add")
            self.assertIn("dir=out", add_command)
            self.assertIn("action=block", add_command)
            self.assertIn(f"program={self.blender.resolve()}", add_command)
        self.assertEqual(lease.receipt.cleanup_result, "PASS")
        self.assertFalse(rule_present)
        self.assertLess(
            next(index for index, command in enumerate(commands) if command[0] == "netsh.exe" and command[3] == "add"),
            next(index for index, command in enumerate(commands) if command[0] == "powershell.exe" and "Get-NetFirewallRule" in command[-1]),
        )

    def test_disabled_firewall_fails_closed_before_rule_creation(self) -> None:
        commands: list[list[str]] = []

        def runner(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
            commands.append(command)
            if command[0] == "powershell.exe" and "Get-NetFirewallProfile" in command[-1]:
                return subprocess.CompletedProcess(command, 0, "[true,false,true]", "")
            raise AssertionError("rule creation must not be attempted")

        resolved = self.blender.resolve()
        with mock.patch.object(windows_network_isolation, "_validate_executable", return_value=resolved):
            lease = windows_network_isolation.create_network_isolation(
                self.blender,
                "Oak:fixture",
                platform_name="nt",
                runner=runner,
            )
        with self.assertRaisesRegex(windows_network_isolation.NetworkIsolationError, "FIREWALL_DISABLED"):
            lease.__enter__()
        self.assertFalse(any(command[0] == "netsh.exe" and command[3] == "add" for command in commands))

    def test_cleanup_failure_is_reported_and_never_silenced(self) -> None:
        delete_failed = False
        rule_present = False

        def runner(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
            nonlocal delete_failed, rule_present
            if command[0] == "powershell.exe" and "Get-NetFirewallProfile" in command[-1]:
                return subprocess.CompletedProcess(command, 0, "[true,true,true]", "")
            if command[0] == "powershell.exe" and "Get-NetFirewallRule" in command[-1]:
                payload = {
                    "DisplayName": display_name_from_verify_command(command),
                    "Enabled": True,
                    "Direction": "Outbound",
                    "Action": "Block",
                    "Program": str(self.blender.resolve()),
                }
                return subprocess.CompletedProcess(command, 0, json.dumps(payload), "")
            if command[0] == "netsh.exe" and command[3] == "show":
                return subprocess.CompletedProcess(command, 0 if rule_present else 1, "", "")
            if command[0] == "netsh.exe" and command[3] == "add":
                rule_present = True
                return subprocess.CompletedProcess(command, 0, "Ok.", "")
            if command[0] == "netsh.exe" and command[3] == "delete":
                delete_failed = True
                return subprocess.CompletedProcess(command, 1, "", "access denied")
            raise AssertionError(command)

        resolved = self.blender.resolve()
        with mock.patch.object(windows_network_isolation, "_validate_executable", return_value=resolved):
            lease = windows_network_isolation.create_network_isolation(
                self.blender,
                "Oak:fixture",
                platform_name="nt",
                runner=runner,
            )
        lease.__enter__()
        with self.assertRaisesRegex(windows_network_isolation.NetworkIsolationError, "RULE_DELETE_FAILED"):
            lease.release()
        self.assertTrue(delete_failed)
        self.assertEqual(lease.receipt.cleanup_result, "FAIL")

    def _drive_profile_check(
        self, payload: str
    ) -> tuple[windows_network_isolation.NetworkIsolationLease, list[list[str]], dict[str, int | bool]]:
        """Build a lease whose PowerShell profile probe returns ``payload``.

        Only ``_validate_executable`` is stubbed, and only because it refuses
        to run on a non-Windows review host.  The profile probe, the strict
        normalization, the rule-name collision check, exact rule creation, the
        post-create verification, and cleanup all run the canonical code path,
        including the exact-path comparison against the lease executable.
        """
        commands: list[list[str]] = []
        state: dict[str, int | bool] = {"rule_present": False, "add_count": 0, "delete_count": 0, "verify_count": 0}

        def runner(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
            commands.append(command)
            if command[0] == "powershell.exe" and "Get-NetFirewallProfile" in command[-1]:
                return subprocess.CompletedProcess(command, 0, payload, "")
            if command[0] == "powershell.exe" and "Get-NetFirewallRule" in command[-1]:
                state["verify_count"] += 1
                verified = {
                    "DisplayName": display_name_from_verify_command(command),
                    "Enabled": True,
                    "Direction": "Outbound",
                    "Action": "Block",
                    "Program": str(self.blender.resolve()),
                }
                return subprocess.CompletedProcess(command, 0, json.dumps(verified), "")
            if command[0] == "netsh.exe" and command[3] == "show":
                return subprocess.CompletedProcess(command, 0 if state["rule_present"] else 1, "", "")
            if command[0] == "netsh.exe" and command[3] == "add":
                state["rule_present"] = True
                state["add_count"] += 1
                return subprocess.CompletedProcess(command, 0, "Ok.", "")
            if command[0] == "netsh.exe" and command[3] == "delete":
                state["rule_present"] = False
                state["delete_count"] += 1
                return subprocess.CompletedProcess(command, 0, "Ok.", "")
            raise AssertionError(command)

        resolved = self.blender.resolve()
        with mock.patch.object(windows_network_isolation, "_validate_executable", return_value=resolved):
            lease = windows_network_isolation.create_network_isolation(
                self.blender,
                "Oak:fixture",
                platform_name="nt",
                runner=runner,
            )
        return lease, commands, state

    def _drive_verify(
        self,
        *,
        verify_payload: dict[str, object] | None = None,
        verify_stdout: str | None = None,
        verify_returncode: int = 0,
        verify_stderr: str = "",
    ) -> tuple[windows_network_isolation.NetworkIsolationLease, list[list[str]], dict[str, int | bool]]:
        """Build a lease that drives the canonical post-create verification path.

        The profile probe, the strict normalization, the rule-name collision
        check, exact rule creation, the post-create verification, and cleanup
        all run the canonical code path.  Only ``_validate_executable`` is
        stubbed (non-Windows review host) and the PowerShell verify response
        is configurable, so each negative proof is driven at the exact
        Python/PowerShell boundary the module sees.  With no override the
        verify response is the exact single display-name rule (enabled,
        outbound, block, exact program) with its DisplayName echoed from the
        canonical verify command itself.
        """
        commands: list[list[str]] = []
        state: dict[str, int | bool] = {
            "rule_present": False,
            "add_count": 0,
            "delete_count": 0,
            "verify_count": 0,
        }

        def runner(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
            commands.append(command)
            if command[0] == "powershell.exe" and "Get-NetFirewallProfile" in command[-1]:
                return subprocess.CompletedProcess(command, 0, "[true,true,true]", "")
            if command[0] == "powershell.exe" and "Get-NetFirewallRule" in command[-1]:
                state["verify_count"] += 1
                if verify_stdout is not None or verify_returncode != 0:
                    return subprocess.CompletedProcess(
                        command, verify_returncode, verify_stdout or "", verify_stderr
                    )
                payload = verify_payload
                if payload is None:
                    payload = {
                        "DisplayName": display_name_from_verify_command(command),
                        "Enabled": True,
                        "Direction": "Outbound",
                        "Action": "Block",
                        "Program": str(self.blender.resolve()),
                    }
                return subprocess.CompletedProcess(command, 0, json.dumps(payload), "")
            if command[0] == "netsh.exe" and command[3] == "show":
                return subprocess.CompletedProcess(command, 0 if state["rule_present"] else 1, "", "")
            if command[0] == "netsh.exe" and command[3] == "add":
                state["rule_present"] = True
                state["add_count"] += 1
                return subprocess.CompletedProcess(command, 0, "Ok.", "")
            if command[0] == "netsh.exe" and command[3] == "delete":
                state["rule_present"] = False
                state["delete_count"] += 1
                return subprocess.CompletedProcess(command, 0, "Ok.", "")
            raise AssertionError(command)

        resolved = self.blender.resolve()
        with mock.patch.object(windows_network_isolation, "_validate_executable", return_value=resolved):
            lease = windows_network_isolation.create_network_isolation(
                self.blender,
                "Oak:fixture",
                platform_name="nt",
                runner=runner,
            )
        return lease, commands, state

    def _assert_verify_fail_closed(
        self,
        lease: windows_network_isolation.NetworkIsolationLease,
        commands: list[list[str]],
        state: dict[str, int | bool],
    ) -> None:
        """Assert the shared fail-closed outcome of one verification failure.

        Encodes PROCESS_SPAWN_ALLOWED=NO: setup raised before any child could
        be spawned.  Encodes CLEANUP_ATTEMPTED_IF_RULE_CREATED=YES: the
        just-created rule is deleted and its absence re-verified.
        """
        self.assertEqual(state["add_count"], 1)
        self.assertEqual(
            [isolation_command_kind(command) for command in commands],
            ["profile-probe", "netsh-show", "netsh-add", "rule-verify", "netsh-delete", "netsh-show"],
            "a failed verification must stop before spawn and attempt cleanup of the created rule",
        )
        self.assertEqual(state["verify_count"], 1)
        self.assertEqual(state["delete_count"], 1)
        self.assertFalse(state["rule_present"])
        self.assertEqual(lease.receipt.setup_result, "FAIL")
        self.assertEqual(lease.receipt.enforcement_result, "NOT_VERIFIED")
        self.assertEqual(lease.receipt.cleanup_result, "NOT_STARTED")
        self.assertFalse(lease.receipt.rule_created)

    def test_enabled_profiles_accept_boolean_and_integer_serialization(self) -> None:
        for payload in ("[true,true,true]", "[1,1,1]", "[true,1,true]"):
            with self.subTest(payload=payload):
                lease, commands, state = self._drive_profile_check(payload)
                with lease:
                    self.assertEqual(lease.receipt.setup_result, "PASS")
                    self.assertEqual(lease.receipt.enforcement_result, "PASS")
                    self.assertTrue(lease.receipt.rule_created)
                self.assertEqual(lease.receipt.cleanup_result, "PASS")
                self.assertFalse(state["rule_present"])
                self.assertEqual(
                    [isolation_command_kind(command) for command in commands],
                    ["profile-probe", "netsh-show", "netsh-add", "rule-verify", "netsh-delete", "netsh-show"],
                    "isolation must be verified before release and the profile probe must precede any rule mutation",
                )
                self.assertEqual(
                    commands[0][-1],
                    "@(Get-NetFirewallProfile -All | Select-Object -ExpandProperty Enabled) | ConvertTo-Json -Compress",
                )
                add_command = commands[2]
                self.assertIn(f"name={lease.rule_name}", add_command)
                self.assertIn("dir=out", add_command)
                self.assertIn("action=block", add_command)
                self.assertIn("enable=yes", add_command)
                self.assertIn("profile=any", add_command)
                self.assertIn(f"program={self.blender.resolve()}", add_command)

    def test_unsupported_profile_values_fail_closed_before_any_rule_mutation(self) -> None:
        cases = {
            "[1,1,0]": "NETWORK_ISOLATION_FIREWALL_DISABLED",
            "[true,false,true]": "NETWORK_ISOLATION_FIREWALL_DISABLED",
            "[1,1,2]": "NETWORK_ISOLATION_FIREWALL_DISABLED",
            "[-1,1,1]": "NETWORK_ISOLATION_FIREWALL_DISABLED",
            "[1.0,1,1]": "NETWORK_ISOLATION_FIREWALL_DISABLED",
            "[1,1,0.9999]": "NETWORK_ISOLATION_FIREWALL_DISABLED",
            '["1",1,1]': "NETWORK_ISOLATION_FIREWALL_DISABLED",
            '["true",true,true]': "NETWORK_ISOLATION_FIREWALL_DISABLED",
            "[null,true,true]": "NETWORK_ISOLATION_FIREWALL_DISABLED",
            '[{"Enabled":true},1,1]': "NETWORK_ISOLATION_FIREWALL_DISABLED",
            "[[1],1,1]": "NETWORK_ISOLATION_FIREWALL_DISABLED",
            "[1,1]": "NETWORK_ISOLATION_FIREWALL_DISABLED",
            "[1,1,1,1]": "NETWORK_ISOLATION_FIREWALL_DISABLED",
            "[]": "NETWORK_ISOLATION_FIREWALL_DISABLED",
            "true": "NETWORK_ISOLATION_FIREWALL_DISABLED",
            "1": "NETWORK_ISOLATION_FIREWALL_DISABLED",
            '{"Enabled":[true,true,true]}': "NETWORK_ISOLATION_FIREWALL_DISABLED",
            "[true,true,": "NETWORK_ISOLATION_FIREWALL_PROFILE_CHECK_FAILED",
            "": "NETWORK_ISOLATION_FIREWALL_PROFILE_CHECK_FAILED",
            "not-json": "NETWORK_ISOLATION_FIREWALL_PROFILE_CHECK_FAILED",
        }
        for payload, error_code in cases.items():
            with self.subTest(payload=payload):
                lease, commands, state = self._drive_profile_check(payload)
                with self.assertRaises(windows_network_isolation.NetworkIsolationError) as caught:
                    lease.__enter__()
                self.assertEqual(str(caught.exception), error_code)
                self.assertEqual(
                    [isolation_command_kind(command) for command in commands],
                    ["profile-probe"],
                    "a rejected profile payload must stop setup before any rule mutation",
                )
                self.assertFalse(state["rule_present"])
                self.assertEqual(lease.receipt.setup_result, "FAIL")
                self.assertEqual(lease.receipt.enforcement_result, "NOT_VERIFIED")
                self.assertFalse(lease.receipt.rule_created)

    def test_verify_exact_single_displayname_rule_passes(self) -> None:
        lease, commands, state = self._drive_verify()
        with lease:
            self.assertEqual(lease.receipt.setup_result, "PASS")
            self.assertEqual(lease.receipt.enforcement_result, "PASS")
            self.assertTrue(lease.receipt.rule_created)
        self.assertEqual(lease.receipt.cleanup_result, "PASS")
        self.assertFalse(state["rule_present"])
        verify = next(command for command in commands if isolation_command_kind(command) == "rule-verify")
        script = verify[-1]
        self.assertIn(f"Get-NetFirewallRule -DisplayName '{lease.rule_name}' -ErrorAction Stop", script)
        self.assertIn("if ($rules.Count -ne 1) { throw", script)
        self.assertIn("$rule = $rules[0]", script)
        self.assertIn("Get-NetFirewallApplicationFilter -ErrorAction Stop", script)
        self.assertIn("DisplayName=[string]$rule.DisplayName", script)
        self.assertNotIn("Get-NetFirewallRule -Name", script)
        self.assertNotIn("*", script)
        self.assertNotIn("?", script)
        self.assertEqual(
            [isolation_command_kind(command) for command in commands],
            ["profile-probe", "netsh-show", "netsh-add", "rule-verify", "netsh-delete", "netsh-show"],
        )

    def test_verify_zero_matching_rules_fails_closed(self) -> None:
        lease, commands, state = self._drive_verify(
            verify_returncode=1,
            verify_stderr=(
                "Get-NetFirewallRule : No MSFT_NetFirewallRule objects found with property "
                "'DisplayName' equal to 'P2P-MPFB-DENY-<rule>'.\n"
                "    + CategoryInfo : ObjectNotFound: (P2P-MPFB-DENY-<rule>:String) [Get-NetFirewallRule]"
            ),
        )
        with self.assertRaisesRegex(
            windows_network_isolation.NetworkIsolationError, "NETWORK_ISOLATION_RULE_VERIFY_FAILED"
        ):
            lease.__enter__()
        self._assert_verify_fail_closed(lease, commands, state)

    def test_verify_multiple_matching_rules_fail_closed(self) -> None:
        lease, commands, state = self._drive_verify(
            verify_returncode=1,
            verify_stderr="P2P_RULE_DISPLAYNAME_NOT_EXACTLY_ONE (two rules matched the P2P display name)",
        )
        with self.assertRaisesRegex(
            windows_network_isolation.NetworkIsolationError, "NETWORK_ISOLATION_RULE_VERIFY_FAILED"
        ):
            lease.__enter__()
        self._assert_verify_fail_closed(lease, commands, state)

    def test_verify_wrong_displayname_fails_closed(self) -> None:
        probe, _, _ = self._drive_verify()
        wrong_name = probe.rule_name[:-1] + ("0" if probe.rule_name[-1] != "0" else "1")
        lease, commands, state = self._drive_verify(
            verify_payload={
                "DisplayName": wrong_name,
                "Enabled": True,
                "Direction": "Outbound",
                "Action": "Block",
                "Program": str(self.blender.resolve()),
            }
        )
        with self.assertRaisesRegex(
            windows_network_isolation.NetworkIsolationError, "NETWORK_ISOLATION_RULE_NOT_EXACT"
        ):
            lease.__enter__()
        self._assert_verify_fail_closed(lease, commands, state)

    def _verify_payload(self, **overrides: object) -> dict[str, object]:
        """Exact passing verify payload with one field overridden per test.

        The correct DisplayName comes from a probe lease: the lease never
        enters (no commands run), and because the fixture path and job
        identity are stable, the probe rule name equals the test rule name.
        Each negative proof therefore differs from the passing payload by
        exactly one field, so the failure is attributable to that field.
        """
        probe, _, _ = self._drive_verify()
        payload: dict[str, object] = {
            "DisplayName": probe.rule_name,
            "Enabled": True,
            "Direction": "Outbound",
            "Action": "Block",
            "Program": str(self.blender.resolve()),
        }
        payload.update(overrides)
        return payload

    def test_verify_disabled_rule_fails_closed(self) -> None:
        lease, commands, state = self._drive_verify(verify_payload=self._verify_payload(Enabled=False))
        with self.assertRaisesRegex(
            windows_network_isolation.NetworkIsolationError, "NETWORK_ISOLATION_RULE_NOT_EXACT"
        ):
            lease.__enter__()
        self._assert_verify_fail_closed(lease, commands, state)

    def test_verify_inbound_rule_fails_closed(self) -> None:
        lease, commands, state = self._drive_verify(verify_payload=self._verify_payload(Direction="Inbound"))
        with self.assertRaisesRegex(
            windows_network_isolation.NetworkIsolationError, "NETWORK_ISOLATION_RULE_NOT_EXACT"
        ):
            lease.__enter__()
        self._assert_verify_fail_closed(lease, commands, state)

    def test_verify_allow_rule_fails_closed(self) -> None:
        lease, commands, state = self._drive_verify(verify_payload=self._verify_payload(Action="Allow"))
        with self.assertRaisesRegex(
            windows_network_isolation.NetworkIsolationError, "NETWORK_ISOLATION_RULE_NOT_EXACT"
        ):
            lease.__enter__()
        self._assert_verify_fail_closed(lease, commands, state)

    def test_verify_wrong_program_fails_closed(self) -> None:
        lease, commands, state = self._drive_verify(
            verify_payload=self._verify_payload(Program=str(self.root / "other.exe"))
        )
        with self.assertRaisesRegex(
            windows_network_isolation.NetworkIsolationError, "NETWORK_ISOLATION_RULE_NOT_EXACT"
        ):
            lease.__enter__()
        self._assert_verify_fail_closed(lease, commands, state)

    def test_verify_powershell_command_failure_fails_closed(self) -> None:
        lease, commands, state = self._drive_verify(
            verify_returncode=1,
            verify_stderr="powershell.exe exited without verification output",
        )
        with self.assertRaisesRegex(
            windows_network_isolation.NetworkIsolationError, "NETWORK_ISOLATION_RULE_VERIFY_FAILED"
        ):
            lease.__enter__()
        self._assert_verify_fail_closed(lease, commands, state)

    def test_verify_malformed_response_fails_closed(self) -> None:
        for stdout in ("", "not-json", "null", "[1,1,1]", "1", "{broken json"):
            with self.subTest(stdout=stdout):
                lease, commands, state = self._drive_verify(verify_stdout=stdout)
                with self.assertRaisesRegex(
                    windows_network_isolation.NetworkIsolationError, "NETWORK_ISOLATION_RULE_VERIFY_FAILED"
                ):
                    lease.__enter__()
                self._assert_verify_fail_closed(lease, commands, state)

    def test_verify_dict_missing_exact_displayname_fails_closed(self) -> None:
        lease, commands, state = self._drive_verify(
            verify_payload={
                "Enabled": True,
                "Direction": "Outbound",
                "Action": "Block",
                "Program": str(self.blender.resolve()),
            }
        )
        with self.assertRaisesRegex(
            windows_network_isolation.NetworkIsolationError, "NETWORK_ISOLATION_RULE_NOT_EXACT"
        ):
            lease.__enter__()
        self._assert_verify_fail_closed(lease, commands, state)


if __name__ == "__main__":
    unittest.main()
