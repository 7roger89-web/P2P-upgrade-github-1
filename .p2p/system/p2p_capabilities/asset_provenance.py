"""Core-asset-only provenance contract for the MPFB2 adapter."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Final, Mapping


PROVENANCE_SCHEMA: Final = "p2p-character-asset-provenance/1"
CORE_ASSET_POLICY: Final = "CORE_CC0_ONLY"
CORE_ASSET_SOURCE_PREFIX: Final = "mpfb2-core:"
CORE_ASSET_LICENSE: Final = "CC0-1.0"
_SHA256: Final = re.compile(r"^[0-9a-f]{64}$")


class AssetProvenanceError(ValueError):
    """Raised when rights or output provenance is incomplete or unsafe."""


def _mapping(value: object, field: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise AssetProvenanceError(f"{field}: expected object")
    if any(not isinstance(key, str) for key in value):
        raise AssetProvenanceError(f"{field}: keys must be strings")
    return dict(value)


def _reject_unknown(value: Mapping[str, object], allowed: set[str], field: str) -> None:
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise AssetProvenanceError(f"{field}: unknown keys: {', '.join(unknown)}")


def _require(value: Mapping[str, object], required: set[str], field: str) -> None:
    missing = sorted(required - set(value))
    if missing:
        raise AssetProvenanceError(f"{field}: missing keys: {', '.join(missing)}")


def _string(value: object, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise AssetProvenanceError(f"{field}: expected non-empty string")
    return value


def _sha256(value: object, field: str) -> str:
    result = _string(value, field)
    if not _SHA256.fullmatch(result):
        raise AssetProvenanceError(f"{field}: invalid sha256")
    return result


def _true(value: object, field: str) -> bool:
    if value is not True:
        raise AssetProvenanceError(f"{field}: must be true for CORE_CC0_ONLY")
    return True


def validate_asset_provenance(provenance: Mapping[str, object]) -> dict[str, object]:
    """Validate an output manifest against the first-lane rights policy."""

    root = _mapping(provenance, "provenance")
    root_keys = {"schema", "character_id", "recipe_sha256", "glb_sha256", "rights_policy", "rigging", "resources", "assets"}
    _reject_unknown(root, root_keys, "provenance")
    _require(root, root_keys, "provenance")
    if root["schema"] != PROVENANCE_SCHEMA:
        raise AssetProvenanceError("provenance.schema: unsupported schema")
    character_id = _string(root["character_id"], "provenance.character_id")
    recipe_digest = _sha256(root["recipe_sha256"], "provenance.recipe_sha256")
    glb_digest = _sha256(root["glb_sha256"], "provenance.glb_sha256")
    if root["rights_policy"] != CORE_ASSET_POLICY:
        raise AssetProvenanceError("provenance.rights_policy: only CORE_CC0_ONLY is allowed")

    rigging = _mapping(root["rigging"], "provenance.rigging")
    rigging_keys = {"generator", "generator_version", "rig_preset", "skinning"}
    _reject_unknown(rigging, rigging_keys, "provenance.rigging")
    _require(rigging, rigging_keys, "provenance.rigging")
    expected_rigging = {
        "generator": "MPFB2",
        "generator_version": "2.0.17",
        "rig_preset": "GAMEENGINE",
        "skinning": "MPFB_BUILT_IN_WEIGHTS",
    }
    if rigging != expected_rigging:
        raise AssetProvenanceError("provenance.rigging: selected MPFB2 GameEngine contract is required")

    resources = root["resources"]
    if not isinstance(resources, list):
        raise AssetProvenanceError("provenance.resources: expected array")
    normalized_resources: list[dict[str, object]] = []
    resource_uris: set[str] = set()
    for index, raw_resource in enumerate(resources):
        resource = _mapping(raw_resource, f"provenance.resources[{index}]")
        resource_keys = {"uri", "sha256"}
        _reject_unknown(resource, resource_keys, f"provenance.resources[{index}]")
        _require(resource, resource_keys, f"provenance.resources[{index}]")
        uri = _string(resource["uri"], f"provenance.resources[{index}].uri")
        if uri.startswith(("http://", "https://")):
            raise AssetProvenanceError("provenance.resources: network resources are not allowed")
        if uri in resource_uris:
            raise AssetProvenanceError("provenance.resources: duplicate uri")
        resource_uris.add(uri)
        normalized_resources.append({"uri": uri, "sha256": _sha256(resource["sha256"], f"provenance.resources[{index}].sha256")})

    assets = root["assets"]
    if not isinstance(assets, list) or not assets:
        raise AssetProvenanceError("provenance.assets: expected non-empty array")
    normalized_assets: list[dict[str, object]] = []
    asset_ids: set[str] = set()
    for index, raw_asset in enumerate(assets):
        asset = _mapping(raw_asset, f"provenance.assets[{index}]")
        asset_keys = {"asset_id", "source", "license", "sha256", "commercial_use", "derivative_use", "redistribution"}
        _reject_unknown(asset, asset_keys, f"provenance.assets[{index}]")
        _require(asset, asset_keys, f"provenance.assets[{index}]")
        asset_id = _string(asset["asset_id"], f"provenance.assets[{index}].asset_id")
        if not asset_id.startswith(CORE_ASSET_SOURCE_PREFIX) or asset_id in asset_ids:
            raise AssetProvenanceError("provenance.assets: only unique mpfb2-core asset ids are allowed")
        source = _string(asset["source"], f"provenance.assets[{index}].source")
        if not source.startswith("MPFB2 core assets/"):
            raise AssetProvenanceError("provenance.assets: source must identify MPFB2 core assets")
        if asset["license"] != CORE_ASSET_LICENSE:
            raise AssetProvenanceError("provenance.assets: third-party or non-CC0 asset rejected")
        asset_ids.add(asset_id)
        normalized_assets.append(
            {
                "asset_id": asset_id,
                "source": source,
                "license": CORE_ASSET_LICENSE,
                "sha256": _sha256(asset["sha256"], f"provenance.assets[{index}].sha256"),
                "commercial_use": _true(asset["commercial_use"], f"provenance.assets[{index}].commercial_use"),
                "derivative_use": _true(asset["derivative_use"], f"provenance.assets[{index}].derivative_use"),
                "redistribution": _true(asset["redistribution"], f"provenance.assets[{index}].redistribution"),
            }
        )

    return {
        "schema": PROVENANCE_SCHEMA,
        "character_id": character_id,
        "recipe_sha256": recipe_digest,
        "glb_sha256": glb_digest,
        "rights_policy": CORE_ASSET_POLICY,
        "rigging": expected_rigging,
        "resources": normalized_resources,
        "assets": normalized_assets,
    }


def validate_recipe_asset_binding(recipe: Mapping[str, object], provenance: Mapping[str, object]) -> None:
    """Require exact recipe/provenance asset identity with no implicit clearance."""

    recipe_assets = recipe.get("assets")
    if not isinstance(recipe_assets, list) or any(not isinstance(item, str) for item in recipe_assets):
        raise AssetProvenanceError("recipe.assets: invalid asset list")
    normalized = validate_asset_provenance(provenance)
    manifest_assets = [asset["asset_id"] for asset in normalized["assets"]]
    if set(recipe_assets) != set(manifest_assets) or len(recipe_assets) != len(manifest_assets):
        raise AssetProvenanceError("provenance.assets: exact recipe asset binding is required")


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    try:
        with Path(path).open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise AssetProvenanceError(f"file unreadable: {path}") from exc
    return digest.hexdigest()


__all__ = [
    "AssetProvenanceError",
    "CORE_ASSET_LICENSE",
    "CORE_ASSET_POLICY",
    "CORE_ASSET_SOURCE_PREFIX",
    "PROVENANCE_SCHEMA",
    "sha256_file",
    "validate_asset_provenance",
    "validate_recipe_asset_binding",
]
