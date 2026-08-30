"""Fail-closed contracts for the MPFB2 parametric character recipe.

The visual reference pack and the executable recipe are deliberately separate
objects.  This module validates only the parametric recipe consumed by the
future forge boundary; image paths are not accepted as recipe inputs.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Final, Mapping


RECIPE_SCHEMA: Final = "p2p-character-recipe/1"
VISUAL_REFERENCE_PACK_SCHEMA: Final = "p2p-visual-reference-pack/1"
_IDENTIFIER: Final = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")
_ASSET_IDENTIFIER: Final = re.compile(r"^[a-z0-9][a-z0-9:_-]{0,95}$")
_SHA256: Final = re.compile(r"^[0-9a-f]{64}$")


class CharacterRecipeError(ValueError):
    """Raised when a recipe or visual-reference contract is invalid."""


def _mapping(value: object, field: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise CharacterRecipeError(f"{field}: expected object")
    if any(not isinstance(key, str) for key in value):
        raise CharacterRecipeError(f"{field}: keys must be strings")
    return dict(value)


def _reject_unknown(value: Mapping[str, object], allowed: set[str], field: str) -> None:
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise CharacterRecipeError(f"{field}: unknown keys: {', '.join(unknown)}")


def _require(value: Mapping[str, object], required: set[str], field: str) -> None:
    missing = sorted(required - set(value))
    if missing:
        raise CharacterRecipeError(f"{field}: missing keys: {', '.join(missing)}")


def _string(value: object, field: str, *, pattern: re.Pattern[str] | None = None) -> str:
    if not isinstance(value, str) or not value:
        raise CharacterRecipeError(f"{field}: expected non-empty string")
    if pattern is not None and not pattern.fullmatch(value):
        raise CharacterRecipeError(f"{field}: invalid value")
    return value


def _number(value: object, field: str, *, minimum: float, maximum: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise CharacterRecipeError(f"{field}: expected number")
    result = float(value)
    if result < minimum or result > maximum:
        raise CharacterRecipeError(f"{field}: outside allowed range")
    return result


def _boolean(value: object, field: str) -> bool:
    if not isinstance(value, bool):
        raise CharacterRecipeError(f"{field}: expected boolean")
    return value


def _asset_list(value: object, field: str) -> list[str]:
    if not isinstance(value, list) or not value:
        raise CharacterRecipeError(f"{field}: expected non-empty array")
    result = [_string(item, f"{field}[{index}]", pattern=_ASSET_IDENTIFIER) for index, item in enumerate(value)]
    if len(result) != len(set(result)):
        raise CharacterRecipeError(f"{field}: duplicate asset id")
    return result


def validate_recipe(recipe: Mapping[str, object]) -> dict[str, object]:
    """Validate and return a JSON-safe normalized recipe.

    Unknown keys are rejected recursively.  The returned mapping is suitable
    for canonical hashing and is not an execution command or Blender script.
    """

    root = _mapping(recipe, "recipe")
    allowed = {
        "schema",
        "character_id",
        "body",
        "proportions",
        "base",
        "skin",
        "hair",
        "clothing",
        "rig",
        "scale",
        "export",
        "assets",
    }
    _reject_unknown(root, allowed, "recipe")
    _require(root, allowed, "recipe")
    if root["schema"] != RECIPE_SCHEMA:
        raise CharacterRecipeError("recipe.schema: unsupported schema")
    character_id = _string(root["character_id"], "recipe.character_id", pattern=_IDENTIFIER)

    body = _mapping(root["body"], "recipe.body")
    _reject_unknown(body, {"gender", "age", "weight", "muscle"}, "recipe.body")
    _require(body, {"gender", "age", "weight", "muscle"}, "recipe.body")
    gender = _string(body["gender"], "recipe.body.gender")
    if gender not in {"female", "male", "neutral"}:
        raise CharacterRecipeError("recipe.body.gender: unsupported value")
    normalized_body = {
        "gender": gender,
        "age": _number(body["age"], "recipe.body.age", minimum=0.0, maximum=1.0),
        "weight": _number(body["weight"], "recipe.body.weight", minimum=0.0, maximum=1.0),
        "muscle": _number(body["muscle"], "recipe.body.muscle", minimum=0.0, maximum=1.0),
    }

    proportions = _mapping(root["proportions"], "recipe.proportions")
    proportion_keys = {"head_scale", "shoulder_width", "torso_length", "arm_length", "leg_length"}
    _reject_unknown(proportions, proportion_keys, "recipe.proportions")
    _require(proportions, proportion_keys, "recipe.proportions")
    normalized_proportions = {
        key: _number(proportions[key], f"recipe.proportions.{key}", minimum=0.5, maximum=1.5)
        for key in sorted(proportion_keys)
    }

    base = _mapping(root["base"], "recipe.base")
    _reject_unknown(base, {"model", "asset_id"}, "recipe.base")
    _require(base, {"model", "asset_id"}, "recipe.base")
    if _string(base["model"], "recipe.base.model") != "human_base":
        raise CharacterRecipeError("recipe.base.model: only human_base is allowed")
    normalized_base = {
        "model": "human_base",
        "asset_id": _string(base["asset_id"], "recipe.base.asset_id", pattern=_ASSET_IDENTIFIER),
    }

    skin = _mapping(root["skin"], "recipe.skin")
    _reject_unknown(skin, {"material_id"}, "recipe.skin")
    _require(skin, {"material_id"}, "recipe.skin")
    normalized_skin = {"material_id": _string(skin["material_id"], "recipe.skin.material_id", pattern=_ASSET_IDENTIFIER)}

    hair = _mapping(root["hair"], "recipe.hair")
    _reject_unknown(hair, {"asset_id"}, "recipe.hair")
    _require(hair, {"asset_id"}, "recipe.hair")
    normalized_hair = {"asset_id": _string(hair["asset_id"], "recipe.hair.asset_id", pattern=_ASSET_IDENTIFIER)}

    clothing = _mapping(root["clothing"], "recipe.clothing")
    _reject_unknown(clothing, {"items"}, "recipe.clothing")
    _require(clothing, {"items"}, "recipe.clothing")
    normalized_clothing = {"items": _asset_list(clothing["items"], "recipe.clothing.items")}

    rig = _mapping(root["rig"], "recipe.rig")
    _reject_unknown(rig, {"preset", "skinning"}, "recipe.rig")
    _require(rig, {"preset", "skinning"}, "recipe.rig")
    if _string(rig["preset"], "recipe.rig.preset") != "GAMEENGINE":
        raise CharacterRecipeError("recipe.rig.preset: only GAMEENGINE is allowed")
    if _string(rig["skinning"], "recipe.rig.skinning") != "MPFB_BUILT_IN_WEIGHTS":
        raise CharacterRecipeError("recipe.rig.skinning: only MPFB_BUILT_IN_WEIGHTS is allowed")

    scale = _number(root["scale"], "recipe.scale", minimum=0.01, maximum=100.0)

    export = _mapping(root["export"], "recipe.export")
    _reject_unknown(export, {"format", "gltf_version", "embed_resources"}, "recipe.export")
    _require(export, {"format", "gltf_version", "embed_resources"}, "recipe.export")
    if _string(export["format"], "recipe.export.format") != "glb":
        raise CharacterRecipeError("recipe.export.format: only glb is allowed")
    if _string(export["gltf_version"], "recipe.export.gltf_version") != "2.0":
        raise CharacterRecipeError("recipe.export.gltf_version: only 2.0 is allowed")
    if not _boolean(export["embed_resources"], "recipe.export.embed_resources"):
        raise CharacterRecipeError("recipe.export.embed_resources: must be true")

    assets = _asset_list(root["assets"], "recipe.assets")
    normalized = {
        "schema": RECIPE_SCHEMA,
        "character_id": character_id,
        "body": normalized_body,
        "proportions": normalized_proportions,
        "base": normalized_base,
        "skin": normalized_skin,
        "hair": normalized_hair,
        "clothing": normalized_clothing,
        "rig": {"preset": "GAMEENGINE", "skinning": "MPFB_BUILT_IN_WEIGHTS"},
        "scale": scale,
        "export": {"format": "glb", "gltf_version": "2.0", "embed_resources": True},
        "assets": assets,
    }
    try:
        json.dumps(normalized, ensure_ascii=False, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise CharacterRecipeError("recipe: not JSON-safe") from exc
    return normalized


def canonical_recipe_json(recipe: Mapping[str, object]) -> str:
    """Return deterministic JSON for a validated recipe."""

    normalized = validate_recipe(recipe)
    return json.dumps(normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def recipe_sha256(recipe: Mapping[str, object]) -> str:
    return hashlib.sha256(canonical_recipe_json(recipe).encode("utf-8")).hexdigest()


def load_recipe(path: str | Path) -> dict[str, object]:
    recipe_path = Path(path)
    try:
        parsed = json.loads(recipe_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CharacterRecipeError(f"recipe file unreadable: {recipe_path}") from exc
    return validate_recipe(parsed)


def validate_visual_reference_pack(pack: Mapping[str, object]) -> dict[str, object]:
    """Validate the non-executable six-view visual specification."""

    root = _mapping(pack, "visual_reference_pack")
    _reject_unknown(root, {"schema", "views"}, "visual_reference_pack")
    _require(root, {"schema", "views"}, "visual_reference_pack")
    if root["schema"] != VISUAL_REFERENCE_PACK_SCHEMA:
        raise CharacterRecipeError("visual_reference_pack.schema: unsupported schema")
    views = root["views"]
    if not isinstance(views, list) or len(views) != 6:
        raise CharacterRecipeError("visual_reference_pack.views: exactly six views required")
    expected = {"full_body_front", "full_body_three_quarter", "full_body_side", "full_body_back", "face_front", "face_three_quarter"}
    normalized_views: list[dict[str, str]] = []
    seen: set[str] = set()
    for index, raw_view in enumerate(views):
        view = _mapping(raw_view, f"visual_reference_pack.views[{index}]")
        _reject_unknown(view, {"view_id", "path", "sha256"}, f"visual_reference_pack.views[{index}]")
        _require(view, {"view_id", "path", "sha256"}, f"visual_reference_pack.views[{index}]")
        view_id = _string(view["view_id"], f"visual_reference_pack.views[{index}].view_id")
        if view_id not in expected or view_id in seen:
            raise CharacterRecipeError("visual_reference_pack.views: wrong or duplicate view_id")
        path = _string(view["path"], f"visual_reference_pack.views[{index}].path")
        if path.startswith(("http://", "https://")):
            raise CharacterRecipeError("visual_reference_pack.views: network paths are not allowed")
        digest = _string(view["sha256"], f"visual_reference_pack.views[{index}].sha256")
        if not _SHA256.fullmatch(digest):
            raise CharacterRecipeError("visual_reference_pack.views: invalid sha256")
        seen.add(view_id)
        normalized_views.append({"view_id": view_id, "path": path, "sha256": digest})
    if seen != expected:
        raise CharacterRecipeError("visual_reference_pack.views: six required views are incomplete")
    return {"schema": VISUAL_REFERENCE_PACK_SCHEMA, "views": normalized_views}


__all__ = [
    "CharacterRecipeError",
    "RECIPE_SCHEMA",
    "VISUAL_REFERENCE_PACK_SCHEMA",
    "canonical_recipe_json",
    "load_recipe",
    "recipe_sha256",
    "validate_recipe",
    "validate_visual_reference_pack",
]
