"""Focused productization tests for the existing MPFB2 capability."""

from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / ".p2p" / "system"))

from p2p_capabilities import character_forge  # noqa: E402


def _valid_provenance(recipe: character_forge.CharacterRecipe, glb: bytes) -> dict[str, object]:
    return {
        "schema": "p2p-character-asset-provenance/1",
        "character_id": recipe.request.name,
        "recipe_sha256": recipe.recipe_sha256,
        "glb_sha256": hashlib.sha256(glb).hexdigest(),
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
                "sha256": "a" * 64,
                "commercial_use": True,
                "derivative_use": True,
                "redistribution": True,
            }
            for asset_id in recipe.recipe["assets"]
        ],
    }


class CharacterRequestTests(unittest.TestCase):
    def test_minimal_request_uses_safe_defaults_and_valid_recipe(self) -> None:
        request = character_forge.normalize_character_request({})
        recipe = character_forge.build_character_recipe(request)

        self.assertEqual(request.to_dict(), {
            "schema": "p2p-character-request/1",
            "name": "Character",
            "gender": "neutral",
            "age_class": "adult",
            "build": "default",
            "rig": True,
            "output_format": "glb",
        })
        self.assertEqual(recipe.recipe["character_id"], "Character")
        self.assertEqual(recipe.recipe["body"], {
            "gender": "neutral",
            "age": 0.45,
            "weight": 0.5,
            "muscle": 0.35,
        })
        self.assertEqual(recipe.recipe["rig"], {
            "preset": "GAMEENGINE",
            "skinning": "MPFB_BUILT_IN_WEIGHTS",
        })
        self.assertEqual(recipe.recipe["export"], {
            "format": "glb",
            "gltf_version": "2.0",
            "embed_resources": True,
        })
        self.assertEqual(recipe.deferred_fields, ())

    def test_same_semantic_request_has_same_recipe_and_hash(self) -> None:
        first = character_forge.build_character_recipe({
            "gender": "male",
            "age_class": "adult",
            "build": "slim",
            "name": "Issue59",
        })
        second = character_forge.build_character_recipe({
            "name": "Issue59",
            "build": "slim",
            "age_class": "adult",
            "gender": "male",
            "output_format": "glb",
            "rig": True,
        })

        self.assertEqual(first.to_dict(), second.to_dict())
        self.assertEqual(first.recipe_sha256, second.recipe_sha256)
        self.assertEqual(first.recipe["body"], {
            "gender": "male",
            "age": 0.45,
            "weight": 0.25,
            "muscle": 0.35,
        })

    def test_checked_in_request_schema_matches_runtime_constants(self) -> None:
        schema_path = REPO_ROOT / "docs/p2p-development/capability-catalog/game-asset-forge/character.request.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        self.assertEqual(schema["$id"], character_forge.REQUEST_SCHEMA)
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(
            set(schema["properties"]),
            set(character_forge.SUPPORTED_REQUEST_FIELDS) | {"schema"},
        )
        self.assertEqual(schema["properties"]["schema"]["const"], character_forge.REQUEST_SCHEMA)
        self.assertEqual(
            set(character_forge.SAFE_DEFAULT_FIELDS),
            set(character_forge.SUPPORTED_REQUEST_FIELDS),
        )
        self.assertTrue(set(character_forge.SAFE_DEFAULT_FIELDS).isdisjoint(
            character_forge.UNSUPPORTED_DEFERRED_FIELDS
        ))
        request = character_forge.normalize_character_request({})
        self.assertEqual(
            character_forge.normalize_character_request(request.to_dict()),
            request,
        )

    def test_invalid_height_type_and_range_fail_closed(self) -> None:
        for value in ("1.82", True, 0.49, 3.01):
            with self.subTest(value=value):
                with self.assertRaises(character_forge.CharacterRequestError):
                    character_forge.normalize_character_request({"height_m": value})

    def test_unsupported_material_fields_fail_closed(self) -> None:
        unsupported = {
            "height_m": 1.82,
            "age": 25,
            "age_years": 25,
            "hair": "long dark",
            "hair_intent": "long dark",
            "hair_color": "dark",
            "clothing": "neutral",
            "clothing_intent": "neutral",
        }
        for field, value in unsupported.items():
            with self.subTest(field=field):
                with self.assertRaisesRegex(character_forge.CharacterRequestError, field):
                    character_forge.normalize_character_request({field: value})

    def test_runtime_controls_and_unknown_fields_are_not_request_fields(self) -> None:
        for field, value in {
            "workspace_root": "D:/escape",
            "blender_executable": "evil.exe",
            "command": ["python", "evil.py"],
            "network_access": True,
            "manifest_sha256": "a" * 64,
        }.items():
            with self.subTest(field=field):
                with self.assertRaisesRegex(character_forge.CharacterRequestError, field):
                    character_forge.normalize_character_request({field: value})

    def test_output_format_and_unrigged_request_fail_closed(self) -> None:
        with self.assertRaises(character_forge.CharacterRequestError):
            character_forge.normalize_character_request({"output_format": "fbx"})
        with self.assertRaises(character_forge.CharacterRequestError):
            character_forge.normalize_character_request({"rig": False})


class CharacterForgeBindingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(dir=REPO_ROOT, prefix=".tmp-character-forge-test-")
        self.root = Path(self.temp.name)
        self.blender = self.root / "blender.exe"
        self.blender.write_bytes(b"test-only blender placeholder")
        self.runtime = character_forge.MpfbRuntimeBinding(self.root, self.blender)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_valid_request_binds_existing_adapter_and_returns_receipt(self) -> None:
        request = {"name": "Issue59", "gender": "male", "age_class": "adult", "build": "slim"}
        recipe = character_forge.build_character_recipe(request)
        output_root = self.root / f"output/p2p-character-forge-{recipe.recipe_sha256[:16]}"
        expected_outputs = ("Issue59.glb", "Issue59.asset-provenance.json")
        plan = SimpleNamespace(
            output_root=output_root,
            expected_outputs=expected_outputs,
            recipe_sha256=recipe.recipe_sha256,
        )
        glb = b"test GLB output"

        def build_plan(**kwargs: object) -> SimpleNamespace:
            self.assertEqual(kwargs["blender_executable"], self.blender)
            self.assertEqual(kwargs["workspace_root"], self.root)
            self.assertEqual(kwargs["job_id"], "Issue59")
            self.assertEqual(kwargs["network_access"], False)
            self.assertEqual(kwargs["mpfb_root"], "mpfb2")
            self.assertEqual(kwargs["mpfb_manifest"], "mpfb2/provisioning-manifest.json")
            self.assertEqual(kwargs["recipe_path"], f"p2p-character-forge-{recipe.recipe_sha256}.recipe.json")
            self.assertNotIn("workspace_root", request)
            return plan

        def execute_plan(received_plan: object, **kwargs: object) -> dict[str, object]:
            self.assertIs(received_plan, plan)
            self.assertTrue(kwargs["execution_authorized"])
            output_root.mkdir(parents=True)
            (output_root / expected_outputs[0]).write_bytes(glb)
            (output_root / expected_outputs[1]).write_text(
                json.dumps(_valid_provenance(recipe, glb)), encoding="utf-8"
            )
            return {
                "status": "EXECUTED_AND_STRUCTURALLY_VALID",
                "network_isolation": {"cleanup_result": "PASS"},
                "validation": {
                    "status": "STRUCTURALLY_VALID",
                    "rig_preset": "GAMEENGINE",
                    "skinning": "MPFB_BUILT_IN_WEIGHTS",
                },
            }

        with mock.patch.object(character_forge.mpfb_adapter, "build_execution_plan", side_effect=build_plan), mock.patch.object(
            character_forge.mpfb_adapter, "execute_plan", side_effect=execute_plan
        ):
            receipt = character_forge.forge_character(request, runtime=self.runtime, execution_authorized=True)

        self.assertEqual(receipt.capability_id, "game.character.generate")
        self.assertEqual(receipt.character_id, "Issue59")
        self.assertEqual(receipt.recipe_sha256, recipe.recipe_sha256)
        self.assertEqual(receipt.output_sha256, hashlib.sha256(glb).hexdigest())
        self.assertEqual(receipt.provenance_status, "PASS")
        self.assertEqual(receipt.structural_validation_status, "STRUCTURALLY_VALID")
        self.assertEqual(receipt.rig_status, "PASS")
        self.assertEqual(receipt.skin_status, "PASS")
        self.assertEqual(receipt.runtime_status, "EXECUTED_AND_STRUCTURALLY_VALID")
        self.assertEqual(receipt.firewall_cleanup_status, "PASS")
        self.assertEqual({item.name for item in output_root.iterdir()}, set(expected_outputs))
        self.assertFalse((self.root / f"p2p-character-forge-{recipe.recipe_sha256}.recipe.json").exists())
        self.assertEqual(character_forge.validate_character_forge_receipt(receipt), receipt.to_dict())

    def test_execution_requires_separate_internal_authorization(self) -> None:
        with mock.patch.object(character_forge.mpfb_adapter, "build_execution_plan") as build_plan:
            with self.assertRaisesRegex(character_forge.CharacterForgeError, "NOT_AUTHORIZED"):
                character_forge.forge_character({}, runtime=self.runtime)
            build_plan.assert_not_called()

    def test_unsupported_request_never_reaches_adapter(self) -> None:
        with mock.patch.object(character_forge.mpfb_adapter, "build_execution_plan") as build_plan:
            with self.assertRaises(character_forge.CharacterRequestError):
                character_forge.forge_character(
                    {"hair_intent": "long dark"},
                    runtime=self.runtime,
                    execution_authorized=True,
                )
            build_plan.assert_not_called()


class CharacterForgeReceiptTests(unittest.TestCase):
    def _receipt(self) -> character_forge.CharacterForgeReceipt:
        return character_forge.CharacterForgeReceipt(
            capability_id="game.character.generate",
            character_id="Issue59",
            recipe_sha256="a" * 64,
            output_path=r"D:\runtime\Issue59.glb",
            output_sha256="b" * 64,
            provenance_path=r"D:\runtime\Issue59.asset-provenance.json",
            provenance_status="PASS",
            structural_validation_status="STRUCTURALLY_VALID",
            rig_status="PASS",
            skin_status="PASS",
            runtime_status="EXECUTED_AND_STRUCTURALLY_VALID",
            firewall_cleanup_status="PASS",
        )

    def test_receipt_round_trips_and_validates(self) -> None:
        receipt = self._receipt()
        payload = receipt.to_dict()
        self.assertEqual(character_forge.CharacterForgeReceipt.from_dict(payload).to_dict(), payload)

    def test_receipt_rejects_wrong_capability_or_status(self) -> None:
        payload = self._receipt().to_dict()
        payload["capability_id"] = "game.character.rig"
        with self.assertRaises(character_forge.CharacterForgeError):
            character_forge.validate_character_forge_receipt(payload)
        payload = self._receipt().to_dict()
        payload["structural_validation_status"] = "UNKNOWN"
        with self.assertRaises(character_forge.CharacterForgeError):
            character_forge.validate_character_forge_receipt(payload)


if __name__ == "__main__":
    unittest.main()
