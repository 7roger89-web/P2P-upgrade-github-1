"""Beginner-facing facade for the existing ``game.character.generate`` route.

This module is intentionally a productization seam, not a second character
engine.  It accepts a small structured request, maps only proven semantics to
the existing ``p2p-character-recipe/1`` contract, and delegates all process,
manifest, provenance, GLB, and Windows-isolation work to the canonical MPFB2
adapter.  Natural-language interpretation belongs to the caller above this
boundary.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Final, Mapping

from . import asset_provenance as provenance_contract
from . import character_recipe as recipe_contract
from . import mpfb_adapter


CAPABILITY_ID: Final = "game.character.generate"
PRODUCTIZATION_TYPE: Final = "BEGINNER_FACING_FACADE_OVER_EXISTING_CAPABILITY"
REQUEST_SCHEMA: Final = "p2p-character-request/1"
RECEIPT_SCHEMA: Final = "p2p-character-forge-receipt/1"

SUPPORTED_REQUEST_FIELDS: Final = (
    "name",
    "gender",
    "age_class",
    "build",
    "rig",
    "output_format",
)
SAFE_DEFAULT_FIELDS: Final = (
    "name",
    "gender",
    "age_class",
    "build",
    "rig",
    "output_format",
)
UNSUPPORTED_DEFERRED_FIELDS: Final = (
    "height_m",
    "age",
    "age_years",
    "hair",
    "hair_intent",
    "hair_color",
    "clothing",
    "clothing_intent",
)

FIELD_SUPPORT: Final = {
    "name": "SUPPORTED_BY_SAFE_DEFAULT",
    "gender": "SUPPORTED_BY_SAFE_DEFAULT",
    "age_class": "SUPPORTED_BY_SAFE_DEFAULT",
    "build": "SUPPORTED_BY_SAFE_DEFAULT",
    "rig": "SUPPORTED_BY_SAFE_DEFAULT",
    "output_format": "SUPPORTED_BY_SAFE_DEFAULT",
    "height_m": "NOT_CURRENTLY_SUPPORTED",
    "age": "NOT_CURRENTLY_SUPPORTED",
    "age_years": "NOT_CURRENTLY_SUPPORTED",
    "hair": "NOT_CURRENTLY_SUPPORTED",
    "hair_intent": "NOT_CURRENTLY_SUPPORTED",
    "hair_color": "NOT_CURRENTLY_SUPPORTED",
    "clothing": "NOT_CURRENTLY_SUPPORTED",
    "clothing_intent": "NOT_CURRENTLY_SUPPORTED",
}

_IDENTIFIER: Final = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")
_SHA256: Final = re.compile(r"^[0-9a-f]{64}$")
_SUPPORTED_FIELDS: Final = frozenset(SUPPORTED_REQUEST_FIELDS)
_UNSUPPORTED_FIELDS: Final = frozenset(UNSUPPORTED_DEFERRED_FIELDS)
_REQUEST_METADATA_FIELDS: Final = frozenset({"schema"})
_AGE_CLASS_VALUES: Final = {"young": 0.35, "adult": 0.45, "old": 0.75}
_BUILD_VALUES: Final = {
    "default": (0.50, 0.35),
    "slim": (0.25, 0.35),
    "average": (0.50, 0.50),
    "athletic": (0.45, 0.75),
}
_DEFAULT_ASSETS: Final = {
    "base": "mpfb2-core:base-mesh",
    "skin": "mpfb2-core:skin-default",
    "hair": "mpfb2-core:hair-default",
    "clothing": "mpfb2-core:clothing-basic",
}


class CharacterForgeError(ValueError):
    """Raised for a fail-closed productization contract violation."""


class CharacterRequestError(CharacterForgeError):
    """Raised when a beginner-facing request is invalid or unsupported."""


def _mapping(value: object, field: str) -> dict[str, object]:
    if not isinstance(value, Mapping):
        raise CharacterRequestError(f"{field}: expected JSON object")
    result = dict(value)
    if any(not isinstance(key, str) for key in result):
        raise CharacterRequestError(f"{field}: keys must be strings")
    return result


def _required_text(value: object, field: str, *, pattern: re.Pattern[str] | None = None) -> str:
    if not isinstance(value, str) or not value:
        raise CharacterRequestError(f"{field}: expected non-empty string")
    if pattern is not None and not pattern.fullmatch(value):
        raise CharacterRequestError(f"{field}: invalid identifier")
    return value


def _enum(value: object, field: str, choices: set[str]) -> str:
    result = _required_text(value, field)
    if result not in choices:
        raise CharacterRequestError(f"{field}: unsupported value")
    return result


def _number(value: object, field: str, *, minimum: float, maximum: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise CharacterRequestError(f"{field}: expected number")
    result = float(value)
    if result != result or result < minimum or result > maximum:
        raise CharacterRequestError(f"{field}: outside allowed range")
    return result


def _validate_unsupported_field(field: str, value: object) -> None:
    """Validate the shape before rejecting unsupported material intent.

    Shape validation keeps type/range failures deterministic while the final
    reason remains explicit: the current MPFB2 producer does not execute this
    material field.
    """

    if field == "height_m":
        _number(value, field, minimum=0.5, maximum=3.0)
    elif field in {"age", "age_years"}:
        _number(value, field, minimum=0.0, maximum=120.0)
    elif field in {"hair", "hair_intent", "hair_color", "clothing", "clothing_intent"}:
        _required_text(value, field)
    raise CharacterRequestError(f"{field}: NOT_CURRENTLY_SUPPORTED")


@dataclass(frozen=True)
class CharacterRequest:
    """Normalized, beginner-facing request with no runtime controls."""

    name: str = "Character"
    gender: str = "neutral"
    age_class: str = "adult"
    build: str = "default"
    rig: bool = True
    output_format: str = "glb"

    @classmethod
    def from_mapping(cls, value: Mapping[str, object]) -> "CharacterRequest":
        raw = _mapping(value, "request")
        unknown = sorted(set(raw) - _SUPPORTED_FIELDS - _UNSUPPORTED_FIELDS - _REQUEST_METADATA_FIELDS)
        if unknown:
            raise CharacterRequestError(f"request: unknown keys: {', '.join(unknown)}")
        if "schema" in raw and raw["schema"] != REQUEST_SCHEMA:
            raise CharacterRequestError("request: schema invalid")
        for field in sorted(set(raw) & _UNSUPPORTED_FIELDS):
            _validate_unsupported_field(field, raw[field])

        name = "Character" if "name" not in raw else _required_text(raw["name"], "name", pattern=_IDENTIFIER)
        gender = "neutral" if "gender" not in raw else _enum(raw["gender"], "gender", {"female", "male", "neutral"})
        age_class = "adult" if "age_class" not in raw else _enum(raw["age_class"], "age_class", set(_AGE_CLASS_VALUES))
        build = "default" if "build" not in raw else _enum(raw["build"], "build", set(_BUILD_VALUES))

        rig = True if "rig" not in raw else raw["rig"]
        if not isinstance(rig, bool):
            raise CharacterRequestError("rig: expected boolean")
        if rig is not True:
            raise CharacterRequestError("rig: only true is supported by this capability")

        output_format = "glb" if "output_format" not in raw else _required_text(raw["output_format"], "output_format")
        if output_format != "glb":
            raise CharacterRequestError("output_format: only glb is supported")

        return cls(
            name=name,
            gender=gender,
            age_class=age_class,
            build=build,
            rig=True,
            output_format="glb",
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": REQUEST_SCHEMA,
            "name": self.name,
            "gender": self.gender,
            "age_class": self.age_class,
            "build": self.build,
            "rig": self.rig,
            "output_format": self.output_format,
        }


def normalize_character_request(value: Mapping[str, object]) -> CharacterRequest:
    """Normalize the small request boundary; never interpret natural language."""

    return CharacterRequest.from_mapping(value)


@dataclass(frozen=True)
class CharacterRecipe:
    """Deterministic execution-ready projection over the existing recipe schema."""

    request: CharacterRequest
    recipe: Mapping[str, object]
    deferred_fields: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        normalized = recipe_contract.validate_recipe(self.recipe)
        object.__setattr__(self, "recipe", normalized)
        deferred = tuple(sorted(set(self.deferred_fields)))
        if any(field not in _UNSUPPORTED_FIELDS for field in deferred):
            raise CharacterForgeError("recipe: deferred field is not classified")
        object.__setattr__(self, "deferred_fields", deferred)

    @classmethod
    def from_request(cls, request: CharacterRequest) -> "CharacterRecipe":
        weight, muscle = _BUILD_VALUES[request.build]
        payload: dict[str, object] = {
            "schema": recipe_contract.RECIPE_SCHEMA,
            "character_id": request.name,
            "body": {
                "gender": request.gender,
                "age": _AGE_CLASS_VALUES[request.age_class],
                "weight": weight,
                "muscle": muscle,
            },
            "proportions": {
                "head_scale": 1.0,
                "shoulder_width": 1.0,
                "torso_length": 1.0,
                "arm_length": 1.0,
                "leg_length": 1.0,
            },
            "base": {"model": "human_base", "asset_id": _DEFAULT_ASSETS["base"]},
            "skin": {"material_id": _DEFAULT_ASSETS["skin"]},
            "hair": {"asset_id": _DEFAULT_ASSETS["hair"]},
            "clothing": {"items": [_DEFAULT_ASSETS["clothing"]]},
            "rig": {"preset": "GAMEENGINE", "skinning": "MPFB_BUILT_IN_WEIGHTS"},
            "scale": 1.0,
            "export": {"format": "glb", "gltf_version": "2.0", "embed_resources": True},
            "assets": list(_DEFAULT_ASSETS.values()),
        }
        return cls(request=request, recipe=payload)

    def to_dict(self) -> dict[str, object]:
        return json.loads(json.dumps(self.recipe, ensure_ascii=False, sort_keys=True))

    @property
    def recipe_sha256(self) -> str:
        return recipe_contract.recipe_sha256(self.recipe)

    @property
    def canonical_json(self) -> str:
        return recipe_contract.canonical_recipe_json(self.recipe)


def build_character_recipe(value: Mapping[str, object] | CharacterRequest) -> CharacterRecipe:
    request = value if isinstance(value, CharacterRequest) else normalize_character_request(value)
    return CharacterRecipe.from_request(request)


@dataclass(frozen=True)
class MpfbRuntimeBinding:
    """P2P-owned runtime context; never part of ``CharacterRequest``."""

    workspace_root: Path
    blender_executable: Path
    mpfb_root: str = "mpfb2"
    mpfb_manifest: str = "mpfb2/provisioning-manifest.json"
    timeout_seconds: int = 900

    def __post_init__(self) -> None:
        workspace = Path(self.workspace_root)
        blender = Path(self.blender_executable)
        if not workspace.is_absolute() or not blender.is_absolute():
            raise CharacterForgeError("runtime binding: absolute P2P paths are required")
        if self.mpfb_root != "mpfb2" or self.mpfb_manifest != "mpfb2/provisioning-manifest.json":
            raise CharacterForgeError("runtime binding: MPFB2 paths are fixed")
        if not isinstance(self.timeout_seconds, int) or not 1 <= self.timeout_seconds <= mpfb_adapter.MAX_TIMEOUT_SECONDS:
            raise CharacterForgeError("runtime binding: timeout out of range")
        object.__setattr__(self, "workspace_root", workspace)
        object.__setattr__(self, "blender_executable", blender)

    @classmethod
    def from_provisioned_root(cls, runtime_root: str | Path) -> "MpfbRuntimeBinding":
        root = Path(runtime_root).expanduser().resolve(strict=True)
        return cls(
            workspace_root=root,
            blender_executable=root / "blender" / "blender-4.2.23-windows-x64" / "blender.exe",
        )


@dataclass(frozen=True)
class CharacterForgeReceipt:
    """Concise, validated product result; no receipt sidecar is written."""

    capability_id: str
    character_id: str
    recipe_sha256: str
    output_path: str
    output_sha256: str
    provenance_path: str
    provenance_status: str
    structural_validation_status: str
    rig_status: str
    skin_status: str
    runtime_status: str
    firewall_cleanup_status: str
    deferred_fields: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> dict[str, object]:
        if self.capability_id != CAPABILITY_ID:
            raise CharacterForgeError("receipt: capability identity mismatch")
        if not _SHA256.fullmatch(self.recipe_sha256) or not _SHA256.fullmatch(self.output_sha256):
            raise CharacterForgeError("receipt: invalid sha256")
        if not isinstance(self.character_id, str) or not _IDENTIFIER.fullmatch(self.character_id):
            raise CharacterForgeError("receipt: invalid character identity")
        if not isinstance(self.output_path, str) or not self.output_path or not self.output_path.lower().endswith(".glb"):
            raise CharacterForgeError("receipt: output GLB path invalid")
        if Path(self.output_path).stem != self.character_id:
            raise CharacterForgeError("receipt: output character binding mismatch")
        expected_provenance_name = f"{self.character_id}.asset-provenance.json"
        if not isinstance(self.provenance_path, str) or Path(self.provenance_path).name != expected_provenance_name:
            raise CharacterForgeError("receipt: provenance path invalid")
        if self.provenance_status != "PASS":
            raise CharacterForgeError("receipt: provenance is not PASS")
        if self.structural_validation_status != "STRUCTURALLY_VALID":
            raise CharacterForgeError("receipt: structural validation is not PASS")
        if self.rig_status != "PASS" or self.skin_status != "PASS":
            raise CharacterForgeError("receipt: rig/skin status is not PASS")
        if self.runtime_status != "EXECUTED_AND_STRUCTURALLY_VALID":
            raise CharacterForgeError("receipt: runtime status invalid")
        if self.firewall_cleanup_status != "PASS":
            raise CharacterForgeError("receipt: firewall cleanup is not PASS")
        deferred = tuple(sorted(set(self.deferred_fields)))
        if any(field not in _UNSUPPORTED_FIELDS for field in deferred):
            raise CharacterForgeError("receipt: unsupported deferred field invalid")
        return self.to_dict()

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": RECEIPT_SCHEMA,
            "capability_id": self.capability_id,
            "character_id": self.character_id,
            "recipe_sha256": self.recipe_sha256,
            "output_path": self.output_path,
            "output_sha256": self.output_sha256,
            "provenance_path": self.provenance_path,
            "provenance_status": self.provenance_status,
            "structural_validation_status": self.structural_validation_status,
            "rig_status": self.rig_status,
            "skin_status": self.skin_status,
            "runtime_status": self.runtime_status,
            "firewall_cleanup_status": self.firewall_cleanup_status,
            "deferred_fields": list(self.deferred_fields),
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, object]) -> "CharacterForgeReceipt":
        raw = _mapping(value, "receipt")
        expected = {
            "schema",
            "capability_id",
            "character_id",
            "recipe_sha256",
            "output_path",
            "output_sha256",
            "provenance_path",
            "provenance_status",
            "structural_validation_status",
            "rig_status",
            "skin_status",
            "runtime_status",
            "firewall_cleanup_status",
            "deferred_fields",
        }
        if set(raw) != expected:
            raise CharacterForgeError("receipt: keys invalid")
        if raw["schema"] != RECEIPT_SCHEMA:
            raise CharacterForgeError("receipt: schema invalid")
        deferred = raw["deferred_fields"]
        if not isinstance(deferred, list) or any(not isinstance(field, str) for field in deferred):
            raise CharacterForgeError("receipt: deferred_fields must be an array")
        return cls(
            capability_id=_required_text(raw["capability_id"], "receipt.capability_id"),
            character_id=_required_text(raw["character_id"], "receipt.character_id"),
            recipe_sha256=_required_text(raw["recipe_sha256"], "receipt.recipe_sha256"),
            output_path=_required_text(raw["output_path"], "receipt.output_path"),
            output_sha256=_required_text(raw["output_sha256"], "receipt.output_sha256"),
            provenance_path=_required_text(raw["provenance_path"], "receipt.provenance_path"),
            provenance_status=_required_text(raw["provenance_status"], "receipt.provenance_status"),
            structural_validation_status=_required_text(raw["structural_validation_status"], "receipt.structural_validation_status"),
            rig_status=_required_text(raw["rig_status"], "receipt.rig_status"),
            skin_status=_required_text(raw["skin_status"], "receipt.skin_status"),
            runtime_status=_required_text(raw["runtime_status"], "receipt.runtime_status"),
            firewall_cleanup_status=_required_text(raw["firewall_cleanup_status"], "receipt.firewall_cleanup_status"),
            deferred_fields=tuple(deferred),
        )


def validate_character_forge_receipt(value: Mapping[str, object] | CharacterForgeReceipt) -> dict[str, object]:
    receipt = value if isinstance(value, CharacterForgeReceipt) else CharacterForgeReceipt.from_dict(value)
    return receipt.validate()


def _output_root_name(recipe: CharacterRecipe) -> str:
    return f"output/p2p-character-forge-{recipe.recipe_sha256[:16]}"


def forge_character(
    value: Mapping[str, object] | CharacterRequest,
    *,
    runtime: MpfbRuntimeBinding,
    execution_authorized: bool = False,
    popen_factory: Callable[..., object] | None = None,
) -> CharacterForgeReceipt:
    """Run one normalized request through the existing MPFB2 adapter.

    ``runtime`` and ``execution_authorized`` are P2P-owned internal context;
    neither can be supplied through the beginner request.  The optional
    ``popen_factory`` exists only for focused boundary tests and real-smoke
    child observation; it is never request-controlled.
    """

    if execution_authorized is not True:
        raise CharacterForgeError("CHARACTER_FORGE_EXECUTION_NOT_AUTHORIZED")
    recipe = build_character_recipe(value)
    workspace = Path(runtime.workspace_root)
    recipe_filename = f"p2p-character-forge-{recipe.recipe_sha256}.recipe.json"
    output_relative = _output_root_name(recipe)
    recipe_path = workspace / recipe_filename
    output_path = workspace / Path(output_relative)
    if recipe_path.exists():
        raise CharacterForgeError("CHARACTER_RECIPE_INPUT_ALREADY_EXISTS")
    if output_path.exists():
        raise CharacterForgeError("CHARACTER_OUTPUT_ROOT_ALREADY_EXISTS")

    try:
        recipe_path.write_text(recipe.canonical_json, encoding="utf-8")
        plan = mpfb_adapter.build_execution_plan(
            blender_executable=runtime.blender_executable,
            workspace_root=runtime.workspace_root,
            job_id=recipe.request.name,
            recipe_path=recipe_filename,
            output_root=output_relative,
            mpfb_root=runtime.mpfb_root,
            mpfb_manifest=runtime.mpfb_manifest,
            timeout_seconds=runtime.timeout_seconds,
            network_access=False,
        )
        if plan.recipe_sha256 != recipe.recipe_sha256:
            raise CharacterForgeError("CHARACTER_FORGE_PLAN_RECIPE_MISMATCH")
        if plan.expected_outputs != (
            f"{recipe.request.name}.glb",
            f"{recipe.request.name}.asset-provenance.json",
        ):
            raise CharacterForgeError("CHARACTER_FORGE_PLAN_OUTPUT_BINDING_INVALID")
        execute_kwargs: dict[str, object] = {"execution_authorized": True}
        if popen_factory is not None:
            execute_kwargs["popen_factory"] = popen_factory
        result = mpfb_adapter.execute_plan(plan, **execute_kwargs)
        validation = result.get("validation") if isinstance(result, Mapping) else None
        isolation = result.get("network_isolation") if isinstance(result, Mapping) else None
        if not isinstance(validation, Mapping) or not isinstance(isolation, Mapping):
            raise CharacterForgeError("CHARACTER_FORGE_RESULT_SHAPE_INVALID")
        if validation.get("status") != "STRUCTURALLY_VALID":
            raise CharacterForgeError("CHARACTER_FORGE_STRUCTURAL_VALIDATION_FAILED")
        if validation.get("rig_preset") != "GAMEENGINE" or validation.get("skinning") != "MPFB_BUILT_IN_WEIGHTS":
            raise CharacterForgeError("CHARACTER_FORGE_RIG_SKIN_RESULT_INVALID")
        if isolation.get("cleanup_result") != "PASS":
            raise CharacterForgeError("CHARACTER_FORGE_FIREWALL_CLEANUP_FAILED")

        glb_path = Path(plan.output_root) / plan.expected_outputs[0]
        provenance_path = Path(plan.output_root) / plan.expected_outputs[1]
        try:
            provenance_document = json.loads(provenance_path.read_text(encoding="utf-8"))
            normalized_provenance = provenance_contract.validate_asset_provenance(provenance_document)
            provenance_contract.validate_recipe_asset_binding(recipe.recipe, normalized_provenance)
            output_sha256 = provenance_contract.sha256_file(glb_path)
        except (OSError, UnicodeError, json.JSONDecodeError, provenance_contract.AssetProvenanceError) as exc:
            raise CharacterForgeError("CHARACTER_FORGE_PROVENANCE_VALIDATION_FAILED") from exc
        if output_sha256 != normalized_provenance["glb_sha256"]:
            raise CharacterForgeError("CHARACTER_FORGE_OUTPUT_HASH_MISMATCH")

        return CharacterForgeReceipt(
            capability_id=CAPABILITY_ID,
            character_id=recipe.request.name,
            recipe_sha256=recipe.recipe_sha256,
            output_path=str(glb_path),
            output_sha256=output_sha256,
            provenance_path=str(provenance_path),
            provenance_status="PASS",
            structural_validation_status=str(validation["status"]),
            rig_status="PASS",
            skin_status="PASS",
            runtime_status=str(result.get("status")),
            firewall_cleanup_status=str(isolation["cleanup_result"]),
            deferred_fields=recipe.deferred_fields,
        )
    finally:
        try:
            recipe_path.unlink()
        except FileNotFoundError:
            pass
        except OSError as exc:
            raise CharacterForgeError("CHARACTER_RECIPE_INPUT_CLEANUP_FAILED") from exc


__all__ = [
    "CAPABILITY_ID",
    "FIELD_SUPPORT",
    "PRODUCTIZATION_TYPE",
    "REQUEST_SCHEMA",
    "RECEIPT_SCHEMA",
    "SAFE_DEFAULT_FIELDS",
    "SUPPORTED_REQUEST_FIELDS",
    "UNSUPPORTED_DEFERRED_FIELDS",
    "CharacterForgeError",
    "CharacterForgeReceipt",
    "CharacterRecipe",
    "CharacterRequest",
    "CharacterRequestError",
    "MpfbRuntimeBinding",
    "build_character_recipe",
    "forge_character",
    "normalize_character_request",
    "validate_character_forge_receipt",
]
