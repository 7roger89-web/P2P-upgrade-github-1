"""Dedicated, allowlisted Blender-side body for the MPFB2 character forge.

The parent adapter is the only caller that may construct the Blender argv.
This file accepts only the bounded recipe/job arguments after Blender's ``--``
separator.  It is intentionally not a generic Python runner and contains no
caller-controlled script or expression loading path.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Mapping, Sequence


BLENDER_ENTRYPOINT: Final = ".p2p/system/p2p_capabilities/mpfb_blender_entrypoint.py"
NETWORK_POLICY: Final = "DENY"
CORE_ASSET_POLICY: Final = "CORE_CC0_ONLY"
RIG_PRESET: Final = "GAMEENGINE"
SKINNING: Final = "MPFB_BUILT_IN_WEIGHTS"
MPFB_VERSION: Final = "2.0.17"
MPFB_VERSION_TUPLE: Final = (2, 0, 17)
MPFB_RELEASE_SHA: Final = "80919fa4682335c41847f761a4d79dcad4124732"
MPFB_RELEASE_TREE: Final = "189a1d6694515ecfbdc40067218c5024389b4e43"
CORE_ASSET_PREFIX: Final = "mpfb2-core:"
CORE_ASSET_LICENSE: Final = "CC0-1.0"
_SHA256: Final = re.compile(r"^[0-9a-f]{64}$")
_REPARSE_POINT: Final = 0x400
_ALLOWED_ARGUMENTS: Final = (
    "--recipe",
    "--output-root",
    "--mpfb-root",
    "--mpfb-manifest",
    "--character-id",
    "--mpfb-version",
    "--mpfb-release-sha",
    "--asset-policy",
    "--network",
)


def _ensure_p2p_import_path() -> None:
    """Bind imports to this checked-in runtime, not the job workspace."""

    system_root = Path(__file__).resolve().parents[1]
    if system_root.name != "system" or not (system_root / "p2p_capabilities" / "__init__.py").is_file():
        raise BlenderEntrypointError(3, "P2P_RUNTIME_BINDING_INVALID")
    system_root_text = str(system_root)
    if system_root_text not in sys.path:
        sys.path.insert(0, system_root_text)


class BlenderEntrypointError(RuntimeError):
    """Fail-closed dedicated-entrypoint error with a deterministic exit code."""

    def __init__(self, code: int, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class BlenderJob:
    workspace_root: Path
    recipe_path: Path
    output_root: Path
    mpfb_root: Path
    manifest_path: Path
    recipe: Mapping[str, object]
    manifest: Mapping[str, object]


def parse_blender_script_arguments(arguments: Sequence[str]) -> dict[str, str]:
    """Parse the exact allowlist; reject positional, unknown, and duplicate args."""

    if len(arguments) % 2:
        raise BlenderEntrypointError(2, "ARGUMENT_VALUE_MISSING")
    parsed: dict[str, str] = {}
    for index in range(0, len(arguments), 2):
        name = arguments[index]
        value = arguments[index + 1]
        if name not in _ALLOWED_ARGUMENTS:
            raise BlenderEntrypointError(2, "ARGUMENT_NOT_ALLOWLISTED")
        if name in parsed:
            raise BlenderEntrypointError(2, "ARGUMENT_DUPLICATE")
        if not isinstance(value, str) or not value or value.startswith("--"):
            raise BlenderEntrypointError(2, "ARGUMENT_VALUE_INVALID")
        parsed[name] = value
    if set(parsed) != set(_ALLOWED_ARGUMENTS):
        raise BlenderEntrypointError(2, "ARGUMENT_SET_INVALID")
    if parsed["--asset-policy"] != CORE_ASSET_POLICY or parsed["--network"] != "deny":
        raise BlenderEntrypointError(2, "EXECUTION_POLICY_INVALID")
    return parsed


def parse_blender_argv(argv: Sequence[str]) -> dict[str, str]:
    """Extract only the one argument block following Blender's ``--`` marker."""

    separators = [index for index, value in enumerate(argv) if value == "--"]
    if len(separators) != 1:
        raise BlenderEntrypointError(2, "BLENDER_ARGUMENT_SEPARATOR_INVALID")
    return parse_blender_script_arguments(argv[separators[0] + 1 :])


def _reparse_point(path: Path) -> bool:
    try:
        attributes = int(getattr(os.stat(path, follow_symlinks=False), "st_file_attributes", 0))
    except OSError:
        return False
    return bool(attributes & _REPARSE_POINT)


def _bounded_path(workspace: Path, value: str, *, field: str, directory: bool = False) -> Path:
    raw = value.replace("\\", "/")
    if raw.startswith(("/", "~")) or re.match(r"^[A-Za-z]:", raw):
        raise BlenderEntrypointError(3, f"{field.upper()}_MUST_BE_WORKSPACE_RELATIVE")
    parts = Path(raw).parts
    if not parts or any(part in {"", ".", ".."} for part in parts):
        raise BlenderEntrypointError(3, f"{field.upper()}_TRAVERSAL")
    current = workspace
    for part in parts:
        current = current / part
        if current.exists() and (current.is_symlink() or _reparse_point(current)):
            raise BlenderEntrypointError(3, f"{field.upper()}_SYMLINK_OR_REPARSE")
    try:
        resolved = current.resolve(strict=True)
    except OSError as exc:
        raise BlenderEntrypointError(3, f"{field.upper()}_UNAVAILABLE") from exc
    try:
        resolved.relative_to(workspace)
    except ValueError as exc:
        raise BlenderEntrypointError(3, f"{field.upper()}_OUTSIDE_WORKSPACE") from exc
    if resolved.is_symlink() or _reparse_point(resolved):
        raise BlenderEntrypointError(3, f"{field.upper()}_SYMLINK_OR_REPARSE")
    if directory and not resolved.is_dir():
        raise BlenderEntrypointError(3, f"{field.upper()}_NOT_DIRECTORY")
    if not directory and not resolved.is_file():
        raise BlenderEntrypointError(3, f"{field.upper()}_NOT_FILE")
    return resolved


def _manifest_asset_path(root: Path, relative_path: object) -> Path:
    if not isinstance(relative_path, str) or not relative_path.strip():
        raise BlenderEntrypointError(4, "MPFB_CORE_ASSET_PATH_INVALID")
    raw = relative_path.replace("\\", "/")
    if raw.startswith(("/", "~")) or re.match(r"^[A-Za-z]:", raw):
        raise BlenderEntrypointError(4, "MPFB_CORE_ASSET_PATH_NOT_RELATIVE")
    parts = Path(raw).parts
    if not parts or any(part in {"", ".", ".."} for part in parts):
        raise BlenderEntrypointError(4, "MPFB_CORE_ASSET_PATH_INVALID")
    current = root
    for part in parts:
        current = current / part
        if current.exists() and (current.is_symlink() or _reparse_point(current)):
            raise BlenderEntrypointError(4, "MPFB_CORE_ASSET_SYMLINK_OR_REPARSE")
    try:
        resolved = current.resolve(strict=True)
        resolved.relative_to(root.resolve(strict=True))
    except (OSError, ValueError) as exc:
        raise BlenderEntrypointError(4, "MPFB_CORE_ASSET_PATH_INVALID") from exc
    if resolved.is_symlink() or _reparse_point(resolved) or not resolved.is_file():
        raise BlenderEntrypointError(4, "MPFB_CORE_ASSET_FILE_INVALID")
    return resolved


def _validate_core_manifest_assets(manifest: Mapping[str, object], root: Path, recipe: Mapping[str, object]) -> None:
    assets = manifest.get("core_assets")
    recipe_assets = recipe.get("assets")
    if not isinstance(assets, dict) or not isinstance(recipe_assets, list) or not recipe_assets:
        raise BlenderEntrypointError(4, "MPFB_CORE_ASSET_MANIFEST_INVALID")
    expected = set(recipe_assets)
    if any(not isinstance(asset_id, str) or not asset_id.startswith(CORE_ASSET_PREFIX) for asset_id in expected):
        raise BlenderEntrypointError(4, "THIRD_PARTY_ASSET_REJECTED")
    if set(assets) != expected:
        raise BlenderEntrypointError(4, "MPFB_CORE_ASSET_RECIPE_BINDING_INVALID")
    for asset_id in sorted(expected):
        entry = assets[asset_id]
        if not isinstance(entry, dict) or set(entry) != {"relative_path", "sha256", "license"}:
            raise BlenderEntrypointError(4, "MPFB_CORE_ASSET_MANIFEST_INVALID")
        if entry["license"] != CORE_ASSET_LICENSE:
            raise BlenderEntrypointError(4, "THIRD_PARTY_ASSET_REJECTED")
        if not isinstance(entry["sha256"], str) or not _SHA256.fullmatch(entry["sha256"]):
            raise BlenderEntrypointError(4, "MPFB_CORE_ASSET_HASH_INVALID")
        asset_path = _manifest_asset_path(root, entry["relative_path"])
        digest = hashlib.sha256(asset_path.read_bytes()).hexdigest()
        if digest != entry["sha256"]:
            raise BlenderEntrypointError(4, "MPFB_CORE_ASSET_HASH_MISMATCH")


def validate_job(arguments: Mapping[str, str], *, workspace_root: str | Path | None = None) -> BlenderJob:
    """Validate all bounded paths, pin fields, recipe binding, and core rights."""

    _ensure_p2p_import_path()
    try:
        workspace = Path(workspace_root or Path.cwd()).resolve(strict=True)
    except OSError as exc:
        raise BlenderEntrypointError(3, "WORKSPACE_UNAVAILABLE") from exc
    if not workspace.is_dir() or workspace.is_symlink() or _reparse_point(workspace):
        raise BlenderEntrypointError(3, "WORKSPACE_INVALID")
    required = {"--recipe", "--output-root", "--mpfb-root", "--mpfb-manifest", "--character-id", "--mpfb-version", "--mpfb-release-sha", "--asset-policy", "--network"}
    if set(arguments) != required:
        raise BlenderEntrypointError(2, "ARGUMENT_SET_INVALID")
    if arguments["--mpfb-version"] != MPFB_VERSION or arguments["--mpfb-release-sha"] != MPFB_RELEASE_SHA:
        raise BlenderEntrypointError(4, "MPFB_PIN_MISMATCH")
    recipe_path = _bounded_path(workspace, arguments["--recipe"], field="recipe")
    mpfb_root = _bounded_path(workspace, arguments["--mpfb-root"], field="mpfb_root", directory=True)
    manifest_path = _bounded_path(workspace, arguments["--mpfb-manifest"], field="mpfb_manifest")
    output_root = _bounded_path(workspace, arguments["--output-root"], field="output_root", directory=True)
    try:
        if manifest_path.parent != mpfb_root and mpfb_root not in manifest_path.parents:
            raise BlenderEntrypointError(4, "MPFB_MANIFEST_OUTSIDE_ROOT")
        document = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not isinstance(document, dict):
            raise BlenderEntrypointError(4, "MPFB_PROVISIONING_MANIFEST_INVALID")
        required_manifest = {"schema", "version", "release_sha", "release_tree", "root_sha256", "core_assets"}
        if set(document) != required_manifest:
            raise BlenderEntrypointError(4, "MPFB_PROVISIONING_MANIFEST_KEYS_INVALID")
        if document["schema"] != "p2p-mpfb2-provisioning/1" or document["version"] != MPFB_VERSION:
            raise BlenderEntrypointError(4, "MPFB_PROVISIONING_VERSION_INVALID")
        if document["release_sha"] != MPFB_RELEASE_SHA or document["release_tree"] != MPFB_RELEASE_TREE:
            raise BlenderEntrypointError(4, "MPFB_PROVISIONING_PIN_MISMATCH")
        if not isinstance(document["root_sha256"], str) or not _SHA256.fullmatch(document["root_sha256"]):
            raise BlenderEntrypointError(4, "MPFB_PROVISIONING_HASH_INVALID")
        from p2p_capabilities.character_recipe import load_recipe
        from p2p_capabilities.mpfb_adapter import hash_provisioned_root

        recipe = load_recipe(recipe_path)
        if recipe["character_id"] != arguments["--character-id"]:
            raise BlenderEntrypointError(3, "JOB_RECIPE_ID_MISMATCH")
        if hash_provisioned_root(mpfb_root, exclude=manifest_path) != document["root_sha256"]:
            raise BlenderEntrypointError(4, "MPFB_PROVISIONING_ROOT_HASH_MISMATCH")
        _validate_core_manifest_assets(document, mpfb_root, recipe)
    except BlenderEntrypointError:
        raise
    except (OSError, UnicodeError, ValueError, TypeError, json.JSONDecodeError) as exc:
        raise BlenderEntrypointError(4, "MPFB_INPUT_VALIDATION_FAILED") from exc
    if any(output_root.iterdir()):
        raise BlenderEntrypointError(5, "OUTPUT_ROOT_NOT_EMPTY")
    return BlenderJob(workspace, recipe_path, output_root, mpfb_root, manifest_path, recipe, document)


def _macro_detail_dict(recipe: Mapping[str, object]) -> dict[str, object]:
    body = recipe["body"]
    proportions = recipe["proportions"]
    if not isinstance(body, dict) or not isinstance(proportions, dict):
        raise BlenderEntrypointError(4, "RECIPE_BODY_INVALID")
    values = [float(proportions[key]) for key in ("head_scale", "shoulder_width", "torso_length", "arm_length", "leg_length")]
    if len({round(value, 12) for value in values}) != 1:
        raise BlenderEntrypointError(4, "RECIPE_PROPORTIONS_NOT_REPRESENTABLE_BY_MPFB2")
    return {
        "gender": {"female": 0.0, "neutral": 0.5, "male": 1.0}[str(body["gender"])],
        "age": float(body["age"]),
        "weight": float(body["weight"]),
        "muscle": float(body["muscle"]),
        "proportions": values[0] - 0.5,
        "race": {"asian": 0.33, "caucasian": 0.33, "african": 0.33},
    }


def _core_asset_entry(job: BlenderJob, asset_id: str) -> Mapping[str, object]:
    assets = job.manifest["core_assets"]
    if not isinstance(assets, dict) or asset_id not in assets or not isinstance(assets[asset_id], dict):
        raise BlenderEntrypointError(4, "MPFB_CORE_ASSET_NOT_DECLARED")
    return assets[asset_id]


def _core_asset_path(job: BlenderJob, asset_id: str) -> Path:
    return _manifest_asset_path(job.mpfb_root, _core_asset_entry(job, asset_id)["relative_path"])


def _clear_scene(bpy: object) -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def _build_provenance(job: BlenderJob, glb_path: Path) -> dict[str, object]:
    from p2p_capabilities.asset_provenance import validate_asset_provenance, validate_recipe_asset_binding
    from p2p_capabilities.character_recipe import recipe_sha256

    asset_records = []
    for asset_id in job.recipe["assets"]:
        entry = _core_asset_entry(job, asset_id)
        asset_records.append(
            {
                "asset_id": asset_id,
                "source": f"MPFB2 core assets/{entry['relative_path']}",
                "license": CORE_ASSET_LICENSE,
                "sha256": entry["sha256"],
                "commercial_use": True,
                "derivative_use": True,
                "redistribution": True,
            }
        )
    provenance = {
        "schema": "p2p-character-asset-provenance/1",
        "character_id": job.recipe["character_id"],
        "recipe_sha256": recipe_sha256(job.recipe),
        "glb_sha256": hashlib.sha256(glb_path.read_bytes()).hexdigest(),
        "rights_policy": CORE_ASSET_POLICY,
        "rigging": {
            "generator": "MPFB2",
            "generator_version": MPFB_VERSION,
            "rig_preset": RIG_PRESET,
            "skinning": SKINNING,
        },
        "resources": [],
        "assets": asset_records,
    }
    normalized = validate_asset_provenance(provenance)
    validate_recipe_asset_binding(job.recipe, normalized)
    return normalized


def execute_job(job: BlenderJob) -> int:
    """Run the actual bounded MPFB2 body; called only inside Blender."""

    _ensure_p2p_import_path()
    import bpy
    import addon_utils

    source_root = (job.mpfb_root / "src").resolve(strict=True)
    if not (source_root / "mpfb" / "__init__.py").is_file() or not (
        source_root / "mpfb" / "blender_manifest.toml"
    ).is_file():
        raise BlenderEntrypointError(4, "MPFB_SOURCE_PACKAGE_MISSING")

    repo_module: str | None = None
    for repo in bpy.context.preferences.extensions.repos:
        try:
            repo_path = Path(repo.directory).resolve(strict=True)
        except (OSError, RuntimeError):
            continue
        if repo_path == source_root:
            repo.enabled = True
            repo_module = str(repo.module)
            break
    if repo_module is None:
        result = bpy.ops.preferences.extension_repo_add(
            name="P2P MPFB2 Local",
            type="LOCAL",
            use_custom_directory=True,
            custom_directory=str(source_root),
        )
        if "FINISHED" not in result:
            raise BlenderEntrypointError(4, f"MPFB_EXTENSION_REPOSITORY_ADD_FAILED:{result!r}")
        for repo in bpy.context.preferences.extensions.repos:
            try:
                repo_path = Path(repo.directory).resolve(strict=True)
            except (OSError, RuntimeError):
                continue
            if repo_path == source_root:
                repo.enabled = True
                repo_module = str(repo.module)
                break
    if not repo_module or not repo_module.isidentifier():
        raise BlenderEntrypointError(4, "MPFB_EXTENSION_REPOSITORY_MODULE_INVALID")

    addon_utils.extensions_refresh()
    module_name = f"bl_ext.{repo_module}.mpfb"
    # Blender's supported addon lifecycle calls exactly one module.register()
    # inside addon_utils.enable(), after default_set creates the preference key.
    mpfb = addon_utils.enable(module_name, default_set=True, persistent=False)
    if mpfb is None:
        raise BlenderEntrypointError(4, "MPFB_EXTENSION_ENABLE_FAILED")
    if str(getattr(mpfb, "__name__", "")) != module_name or str(
        getattr(mpfb, "__package__", "")
    ) != module_name:
        raise BlenderEntrypointError(4, "MPFB_EXTENSION_IDENTITY_MISMATCH")
    if module_name not in bpy.context.preferences.addons:
        raise BlenderEntrypointError(4, "MPFB_EXTENSION_IDENTITY_MISSING")
    print("MPFB_ADDON_IDENTITY_PRESENT=YES")

    if tuple(getattr(mpfb, "VERSION", ())) != MPFB_VERSION_TUPLE:
        raise BlenderEntrypointError(4, "MPFB_RUNTIME_VERSION_MISMATCH")
    try:
        mpfb.get_preference("mpfb_user_data")
    except Exception as exc:
        raise BlenderEntrypointError(
            4,
            f"MPFB_PREFERENCE_INITIALIZATION_FAILED:{type(exc).__name__}:{exc}",
        ) from exc
    print("MPFB_GET_PREFERENCE_PASS=YES")
    if not getattr(mpfb, "MPFB_CONTEXTUAL_INFORMATION", None) or not getattr(
        mpfb, "__addon_enabled__", False
    ):
        raise BlenderEntrypointError(4, "MPFB_REGISTER_NOT_CONFIRMED")
    print("MPFB_REGISTER_PASS=YES")
    HumanService = importlib.import_module(f"{module_name}.services").HumanService

    skin_asset_id = str(job.recipe["skin"]["material_id"])
    skin_path = _core_asset_path(job, skin_asset_id)
    _clear_scene(bpy)
    basemesh = HumanService.create_human(
        mask_helpers=True,
        detailed_helpers=True,
        extra_vertex_groups=True,
        feet_on_ground=True,
        scale=float(job.recipe["scale"]),
        macro_detail_dict=_macro_detail_dict(job.recipe),
    )
    basemesh.name = f"{job.recipe['character_id']}.body"
    armature = HumanService.add_builtin_rig(basemesh, "game_engine", import_weights=True)
    if armature is None or getattr(armature, "type", None) != "ARMATURE":
        raise BlenderEntrypointError(4, "GAMEENGINE_RIG_CREATION_FAILED")
    HumanService.set_character_skin(str(skin_path), basemesh, skin_type="GAMEENGINE", material_instances=False)

    glb_path = job.output_root / f"{job.recipe['character_id']}.glb"
    provenance_path = job.output_root / f"{job.recipe['character_id']}.asset-provenance.json"
    if glb_path.exists() or provenance_path.exists():
        raise BlenderEntrypointError(5, "OUTPUT_ALREADY_EXISTS")
    bpy.ops.object.select_all(action="DESELECT")
    basemesh.select_set(True)
    armature.select_set(True)
    bpy.context.view_layer.objects.active = armature
    bpy.ops.export_scene.gltf(filepath=str(glb_path), export_format="GLB", use_selection=True)
    if {entry.name for entry in job.output_root.iterdir()} != {glb_path.name}:
        raise BlenderEntrypointError(5, "UNDECLARED_OUTPUTS_AFTER_GLTF")
    provenance = _build_provenance(job, glb_path)
    provenance_path.write_text(json.dumps(provenance, ensure_ascii=False, sort_keys=True, separators=(",", ":")), encoding="utf-8")
    if {entry.name for entry in job.output_root.iterdir()} != {glb_path.name, provenance_path.name}:
        raise BlenderEntrypointError(5, "UNDECLARED_OUTPUTS_AFTER_PROVENANCE")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    try:
        arguments = parse_blender_argv(sys.argv if argv is None else argv)
        job = validate_job(arguments)
        return execute_job(job)
    except BlenderEntrypointError as exc:
        print(f"MPFB_ENTRYPOINT_ERROR={exc}", file=sys.stderr)
        return exc.code
    except Exception:
        print("MPFB_ENTRYPOINT_ERROR=UNEXPECTED_RUNTIME_FAILURE", file=sys.stderr)
        return 70


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "BLENDER_ENTRYPOINT",
    "BlenderEntrypointError",
    "BlenderJob",
    "CORE_ASSET_POLICY",
    "MPFB_RELEASE_SHA",
    "MPFB_RELEASE_TREE",
    "MPFB_VERSION",
    "MPFB_VERSION_TUPLE",
    "execute_job",
    "main",
    "parse_blender_argv",
    "parse_blender_script_arguments",
    "validate_job",
]
