"""Fail-closed execution boundary for the pinned img2threejs workflow.

The upstream project is intentionally kept in an explicit external checkout. This
adapter does not download it, install dependencies, launch a shell, or expose the
upstream's network/plugin/renderer routes. It runs only the audited local workflow
and deterministic code-generation commands after binding the checkout to one
immutable commit and tree.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Final, Mapping


UPSTREAM_REPOSITORY: Final = "https://github.com/img2threejs/img2threejs.git"
UPSTREAM_VERSION: Final = "1.5.1"
UPSTREAM_SHA: Final = "dede5909be4e494b228c801a55dda47439143932"
UPSTREAM_TREE: Final = "25bcd4e1f1a487b9a61d69ade257342a3da767e3"
UPSTREAM_LICENSE: Final = "Apache-2.0"

NETWORK_POLICY: Final = "DENY"
CS2_METADATA_NETWORK: Final = "DISABLED"
ALLOWED_ENTRYPOINTS: Final = (
    "forge/state.py",
    "forge/next.py",
    "forge/stage1_intake/probe_image.py",
    "forge/stage2_spec/validate_sculpt_spec.py",
    "forge/stage3_build/generate_threejs_factory.py",
)
DENIED_ENTRYPOINTS: Final = (
    "forge/stage1_intake/fetch_cs2_metadata.py",
    "forge/stage1_intake/material_region_analysis.py",
    "forge/stage1_intake/run_vision_adapter.py",
)
MAX_TIMEOUT_SECONDS: Final = 120
MAX_IDENTIFIER_LENGTH: Final = 64
ALLOWED_PASS_IDS: Final = (
    "blockout",
    "structural-pass",
    "form-refinement",
    "material-pass",
    "surface-pass",
    "lighting-pass",
    "interaction-pass",
    "optimization-pass",
)
_HEX40: Final = re.compile(r"^[0-9a-f]{40}$")
_IDENTIFIER: Final = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")
_REPARSE_POINT: Final = 0x400

# ---------------------------------------------------------------------------
# Bounded static projection seam (P2P-IMG2THREEJS-STATIC-PROJECTION-01).
#
# This is an operation of THIS adapter, not a new capability identity. It
# composes already-allowlisted upstream entrypoints (strict spec validation,
# deterministic factory generation) with a P2P-owned contained bake harness
# and a deterministic Python projection into the already-promoted
# `p2p-static-glb-asset/1` input contract. The seam never emits GLB itself,
# never infers a relative-unit scale, and requires an explicit caller
# physical anchor (TARGET_MAJOR_EXTENT_METERS).
# ---------------------------------------------------------------------------

PROJECTION_OPERATION_ID: Final = "img2threejs.static_projection"
PROJECTION_OPERATION_VERSION: Final = "1.0.0"
RUNTIME_BAKE_SCHEMA: Final = "p2p-img2threejs-runtime-bake/1"
STATIC_PROJECTION_SCHEMA: Final = "p2p-img2threejs-static-projection/1"
STATIC_PROJECTION_CONTRACT: Final = "p2p-static-glb-asset/1"
VERIFIED_NODE_VERSION: Final = "v25.2.1"
VERIFIED_THREE_VERSION: Final = "0.169.0"
VERIFIED_THREE_REVISION: Final = "169"
STATIC_HARNESS_FILENAME: Final = "img2threejs_static_projection_harness.mjs"
MAX_BAKE_BYTES: Final = 64 * 1024 * 1024
MAX_SPEC_BYTES: Final = 8 * 1024 * 1024
MAX_STATIC_NODES: Final = 8192
MAX_STATIC_MESHES: Final = 2048
MAX_STATIC_TRIANGLES: Final = 1_000_000
_ASSET_NAME: Final = re.compile(r"^[a-z][a-z0-9_-]{1,63}$")
_STATIC_SUPPORTED_MATERIAL_TYPES: Final = frozenset(
    {
        "MeshBasicMaterial",
        "MeshLambertMaterial",
        "MeshPhongMaterial",
        "MeshStandardMaterial",
        "MeshPhysicalMaterial",
    }
)
# Material fields the canonical `p2p-static-glb-asset/1` standardizer can
# carry. Any runtime material property outside this set that differs from the
# material class's own runtime default is a hard rejection: the seam must not
# silently drop appearance (MeshPhysical transmission/clearcoat/sheen/
# iridescence/thickness, texture slots, emissive, Phong specular/shininess,
# flat shading, vertex colors, blending, and so on all fail closed here).
_STATIC_PROJECTABLE_MATERIAL_KEYS: Final = frozenset({"color", "opacity", "metalness", "roughness"})



class Img2ThreeJSAdapterError(ValueError):
    """A user-visible, fail-closed adapter rejection."""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _reparse_point(path: Path) -> bool:
    try:
        attributes = int(getattr(os.stat(path, follow_symlinks=False), "st_file_attributes", 0))
    except OSError:
        return False
    return bool(attributes & _REPARSE_POINT)


def _reject_reparse_components(root: Path, candidate: Path) -> None:
    try:
        relative = candidate.relative_to(root)
    except ValueError as exc:
        raise Img2ThreeJSAdapterError("PATH_OUTSIDE_WORKSPACE") from exc
    current = root
    for part in relative.parts:
        current /= part
        if current.exists() and (current.is_symlink() or _reparse_point(current)):
            raise Img2ThreeJSAdapterError("SYMLINK_OR_REPARSE_PATH_REJECTED")


def _workspace_root(value: str | Path) -> Path:
    root = Path(value).expanduser()
    if not root.is_absolute():
        raise Img2ThreeJSAdapterError("WORKSPACE_ROOT_MUST_BE_ABSOLUTE")
    if root.is_symlink() or _reparse_point(root):
        raise Img2ThreeJSAdapterError("WORKSPACE_ROOT_SYMLINK_OR_REPARSE")
    try:
        resolved = root.resolve(strict=True)
    except OSError as exc:
        raise Img2ThreeJSAdapterError("WORKSPACE_ROOT_UNAVAILABLE") from exc
    if not resolved.is_dir():
        raise Img2ThreeJSAdapterError("WORKSPACE_ROOT_NOT_DIRECTORY")
    if resolved.is_symlink() or _reparse_point(resolved):
        raise Img2ThreeJSAdapterError("WORKSPACE_ROOT_SYMLINK_OR_REPARSE")
    return resolved


def _relative(value: str | Path, *, field: str) -> PurePosixPath:
    if not isinstance(value, (str, Path)) or not str(value).strip():
        raise Img2ThreeJSAdapterError(f"{field.upper()}_INVALID")
    raw = str(value)
    if "\x00" in raw:
        raise Img2ThreeJSAdapterError(f"{field.upper()}_NUL_BYTE")
    if "\\" in raw:
        raise Img2ThreeJSAdapterError(f"{field.upper()}_BACKSLASH_REJECTED")
    if raw.startswith(("/", "~")) or re.match(r"^[A-Za-z]:", raw):
        raise Img2ThreeJSAdapterError(f"{field.upper()}_MUST_BE_WORKSPACE_RELATIVE")
    path = PurePosixPath(raw)
    if path.is_absolute() or "." in path.parts or ".." in path.parts:
        raise Img2ThreeJSAdapterError(f"{field.upper()}_PATH_TRAVERSAL")
    return path


def bounded_workspace_path(workspace_root: str | Path, relative_path: str | Path, *, field: str = "path") -> Path:
    """Resolve a relative path only if every existing component stays in the workspace."""

    root = _workspace_root(workspace_root)
    relative = _relative(relative_path, field=field)
    candidate = (root / Path(*relative.parts)).resolve(strict=False)
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise Img2ThreeJSAdapterError("PATH_OUTSIDE_WORKSPACE") from exc
    _reject_reparse_components(root, candidate)
    return candidate


def validate_identifier(value: str, *, field: str = "identifier") -> str:
    """Validate region/component/socket identifiers before any upstream call."""

    if not isinstance(value, str) or not value or len(value) > MAX_IDENTIFIER_LENGTH:
        raise Img2ThreeJSAdapterError(f"{field.upper()}_INVALID")
    if ".." in value or "\\" in value or "/" in value:
        raise Img2ThreeJSAdapterError(f"{field.upper()}_PATH_TRAVERSAL")
    if not _IDENTIFIER.fullmatch(value):
        raise Img2ThreeJSAdapterError(f"{field.upper()}_INVALID")
    return value


def _git(source_root: Path, *arguments: str) -> str:
    git = "git.exe" if os.name == "nt" else "git"
    environment = {
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_OPTIONAL_LOCKS": "0",
        "PATH": os.environ.get("PATH", ""),
    }
    result = subprocess.run(
        [git, *arguments],
        cwd=source_root,
        env=environment,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
        shell=False,
    )
    if result.returncode != 0:
        raise Img2ThreeJSAdapterError("UPSTREAM_GIT_VERIFICATION_FAILED")
    return result.stdout.strip()


def verify_upstream_checkout(source_root: str | Path) -> dict[str, str]:
    """Bind the executable source to the exact audited commit/tree and clean worktree."""

    source = Path(source_root).expanduser()
    if source.is_symlink() or _reparse_point(source):
        raise Img2ThreeJSAdapterError("UPSTREAM_SOURCE_SYMLINK_OR_REPARSE")
    try:
        resolved = source.resolve(strict=True)
    except OSError as exc:
        raise Img2ThreeJSAdapterError("UPSTREAM_SOURCE_UNAVAILABLE") from exc
    if not resolved.is_dir() or resolved.is_symlink() or _reparse_point(resolved):
        raise Img2ThreeJSAdapterError("UPSTREAM_SOURCE_INVALID")
    top_level = Path(_git(resolved, "rev-parse", "--show-toplevel")).resolve(strict=True)
    if top_level != resolved:
        raise Img2ThreeJSAdapterError("UPSTREAM_CHECKOUT_ROOT_MISMATCH")
    commit = _git(resolved, "rev-parse", "HEAD").lower()
    tree = _git(resolved, "show", "-s", "--format=%T", "HEAD").lower()
    # Ignore interpreter/build caches: they are not part of the pinned source tree and
    # are routinely created by a local smoke run. Tracked edits and ordinary untracked
    # files still fail the binding check.
    status = _git(resolved, "status", "--porcelain=v1", "--untracked-files=all")
    if commit != UPSTREAM_SHA or tree != UPSTREAM_TREE:
        raise Img2ThreeJSAdapterError("UPSTREAM_PIN_MISMATCH")
    if status:
        raise Img2ThreeJSAdapterError("UPSTREAM_CHECKOUT_DIRTY")
    for entrypoint in ALLOWED_ENTRYPOINTS:
        path = resolved / Path(*entrypoint.split("/"))
        if not path.is_file() or path.is_symlink() or _reparse_point(path):
            raise Img2ThreeJSAdapterError("UPSTREAM_ENTRYPOINT_UNAVAILABLE")
    return {
        "repository": UPSTREAM_REPOSITORY,
        "version": UPSTREAM_VERSION,
        "commit": commit,
        "tree": tree,
        "license": UPSTREAM_LICENSE,
        "network_policy": NETWORK_POLICY,
        "cs2_metadata_network": CS2_METADATA_NETWORK,
    }


def _relative_string(value: str | Path, *, field: str) -> str:
    return _relative(value, field=field).as_posix()


def _minimal_environment(workspace: Path) -> dict[str, str]:
    temporary_root = bounded_workspace_path(workspace, ".tmp/img2threejs", field="temporary")
    temporary_root.mkdir(parents=True, exist_ok=True)
    return {
        "PATH": os.environ.get("PATH", ""),
        "PYTHONIOENCODING": "utf-8",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONNOUSERSITE": "1",
        "TEMP": str(temporary_root),
        "TMP": str(temporary_root),
        "TMPDIR": str(temporary_root),
        **({"SystemRoot": os.environ["SystemRoot"]} if os.name == "nt" and "SystemRoot" in os.environ else {}),
    }


def _build_argv(
    entrypoint: str,
    source_root: Path,
    *,
    state_path: str,
    reference_path: str | None,
    profile: str,
    spec_path: str | None,
    output_path: str | None,
    pass_id: str | None,
) -> list[str]:
    if entrypoint not in ALLOWED_ENTRYPOINTS:
        raise Img2ThreeJSAdapterError("ENTRYPOINT_NOT_ALLOWLISTED")
    script = source_root / Path(*entrypoint.split("/"))
    if entrypoint == "forge/state.py":
        if reference_path is None:
            raise Img2ThreeJSAdapterError("REFERENCE_REQUIRED_FOR_STATE_INIT")
        argv = [sys.executable, str(script), "init", "--state", state_path, "--reference", reference_path, "--profile", profile]
        if spec_path is not None:
            argv.extend(("--spec", spec_path))
        return argv
    if entrypoint == "forge/next.py":
        argv = [sys.executable, str(script), "--state", state_path]
        if spec_path is not None:
            argv.append(spec_path)
        return argv
    if entrypoint == "forge/stage1_intake/probe_image.py":
        if reference_path is None:
            raise Img2ThreeJSAdapterError("REFERENCE_REQUIRED_FOR_PROBE")
        return [sys.executable, str(script), reference_path]
    if entrypoint == "forge/stage2_spec/validate_sculpt_spec.py":
        if spec_path is None:
            raise Img2ThreeJSAdapterError("SPEC_REQUIRED_FOR_VALIDATION")
        return [sys.executable, str(script), spec_path, "--strict-quality"]
    if spec_path is None or output_path is None:
        raise Img2ThreeJSAdapterError("SPEC_AND_OUTPUT_REQUIRED_FOR_GENERATION")
    argv = [sys.executable, str(script), spec_path, "--out", output_path]
    if pass_id is not None:
        argv.extend(("--pass-id", pass_id))
    return argv


def execute(
    entrypoint: str,
    *,
    source_root: str | Path,
    workspace_root: str | Path,
    reference_path: str | Path | None = None,
    state_path: str | Path = ".img2threejs/state.json",
    profile: str = "generic",
    spec_path: str | Path | None = None,
    output_path: str | Path | None = None,
    pass_id: str | None = None,
    timeout_seconds: int = 30,
    network_access: bool = False,
) -> dict[str, object]:
    """Run one allowlisted upstream control-plane command and return a redacted receipt."""

    if network_access:
        raise Img2ThreeJSAdapterError("NETWORK_NOT_PERMITTED")
    if entrypoint in DENIED_ENTRYPOINTS or entrypoint not in ALLOWED_ENTRYPOINTS:
        raise Img2ThreeJSAdapterError("ENTRYPOINT_NOT_ALLOWLISTED")
    if profile not in {"generic", "character"}:
        raise Img2ThreeJSAdapterError("PROFILE_NOT_ALLOWLISTED")
    if not isinstance(timeout_seconds, int) or not 1 <= timeout_seconds <= MAX_TIMEOUT_SECONDS:
        raise Img2ThreeJSAdapterError("TIMEOUT_OUT_OF_RANGE")
    if pass_id is not None and pass_id not in ALLOWED_PASS_IDS:
        raise Img2ThreeJSAdapterError("PASS_ID_NOT_ALLOWLISTED")

    workspace = _workspace_root(workspace_root)
    provenance = verify_upstream_checkout(source_root)
    source = Path(source_root).expanduser().resolve(strict=True)
    state_relative = _relative_string(state_path, field="state")
    state_target = bounded_workspace_path(workspace, state_relative, field="state")
    reference_relative = None
    if reference_path is not None:
        reference_relative = _relative_string(reference_path, field="reference")
        reference_target = bounded_workspace_path(workspace, reference_relative, field="reference")
        if not reference_target.is_file():
            raise Img2ThreeJSAdapterError("REFERENCE_NOT_FOUND")
    spec_relative = None
    if spec_path is not None:
        spec_relative = _relative_string(spec_path, field="spec")
        spec_target = bounded_workspace_path(workspace, spec_relative, field="spec")
        if entrypoint in {
            "forge/stage2_spec/validate_sculpt_spec.py",
            "forge/stage3_build/generate_threejs_factory.py",
        } and not spec_target.is_file():
            raise Img2ThreeJSAdapterError("SPEC_NOT_FOUND")
    output_relative = None
    output_target = None
    if output_path is not None:
        output_relative = _relative_string(output_path, field="output")
        output_target = bounded_workspace_path(workspace, output_relative, field="output")
    if entrypoint == "forge/stage3_build/generate_threejs_factory.py" and output_target is None:
        raise Img2ThreeJSAdapterError("OUTPUT_REQUIRED_FOR_GENERATION")
    argv = _build_argv(
        entrypoint,
        source,
        state_path=state_relative,
        reference_path=reference_relative,
        profile=profile,
        spec_path=spec_relative,
        output_path=output_relative,
        pass_id=pass_id,
    )
    result = subprocess.run(
        argv,
        cwd=workspace,
        env=_minimal_environment(workspace),
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
        shell=False,
        timeout=timeout_seconds,
    )
    if result.returncode != 0:
        raise Img2ThreeJSAdapterError("UPSTREAM_COMMAND_FAILED")
    expected_target = state_target if entrypoint in {"forge/state.py", "forge/next.py"} else output_target
    if expected_target is not None and not expected_target.is_file():
        raise Img2ThreeJSAdapterError("EXPECTED_OUTPUT_MISSING")
    if output_relative is not None:
        bounded_workspace_path(workspace, output_relative, field="output")
    return {
        "schema": "p2p-img2threejs-execution-receipt/1",
        "status": "EXECUTED",
        "entrypoint": entrypoint,
        "argv": ["<python>", *argv[2:]],
        "source": provenance,
        "workspace_relative_state": state_relative,
        "workspace_relative_output": output_relative,
        "network_used": False,
        "network_policy": NETWORK_POLICY,
        "cs2_metadata_network": CS2_METADATA_NETWORK,
        "shell": False,
        "secrets_inherited": False,
        "return_code": result.returncode,
        "stdout_sha256": _sha256(result.stdout.encode("utf-8")),
        "stderr_sha256": _sha256(result.stderr.encode("utf-8")),
    }


# ---------------------------------------------------------------------------
# Static projection seam: runtime bake manifest -> normalized static asset
# ---------------------------------------------------------------------------


def _static_number(value: object, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise Img2ThreeJSAdapterError(f"{field.upper()}: finite number required")
    return float(value)


def _static_mat4_mul(a: list[float], b: list[float]) -> list[float]:
    # Column-major 4x4 multiply, result = A x B, matching Object3D
    # (matrixWorld = parent.matrixWorld x matrix). Fixed arithmetic order keeps
    # the bake bitwise-deterministic across repeated calls.
    result = [0.0] * 16
    for column in range(4):
        for row in range(4):
            total = 0.0
            for k in range(4):
                total += a[row + 4 * k] * b[k + 4 * column]
            result[row + 4 * column] = total
    return result


def _static_mat4_point(m: list[float], point: list[float]) -> list[float]:
    x, y, z = point
    return [
        m[0] * x + m[4] * y + m[8] * z + m[12],
        m[1] * x + m[5] * y + m[9] * z + m[13],
        m[2] * x + m[6] * y + m[10] * z + m[14],
    ]


def _static_asset_name(value: object) -> str:
    if not isinstance(value, str) or not _ASSET_NAME.fullmatch(value):
        raise Img2ThreeJSAdapterError("ASSET_NAME_INVALID")
    return value


def _static_physical_anchor(value: object) -> float:
    """Validate TARGET_MAJOR_EXTENT_METERS. Required, finite, > 0, never inferred."""

    if value is None:
        raise Img2ThreeJSAdapterError("TARGET_MAJOR_EXTENT_METERS_REQUIRED")
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0.0:
        raise Img2ThreeJSAdapterError("TARGET_MAJOR_EXTENT_METERS_INVALID")
    return float(value)


def _static_material(material: object) -> tuple[dict[str, object], str]:
    if material is None:
        return {"type": "MeshStandardMaterial", "color": [1.0, 1.0, 1.0], "opacity": 1.0, "metalness": 0.0, "roughness": 1.0}, "default"
    if not isinstance(material, Mapping):
        raise Img2ThreeJSAdapterError("MATERIAL_INVALID")
    kind = material.get("type")
    if not isinstance(kind, str) or kind not in _STATIC_SUPPORTED_MATERIAL_TYPES:
        raise Img2ThreeJSAdapterError(f"MATERIAL_TYPE_UNSUPPORTED:{kind!r}")
    color = material.get("color")
    if not isinstance(color, (list, tuple)) or len(color) != 3:
        raise Img2ThreeJSAdapterError("MATERIAL_COLOR_INVALID")
    channels = [_static_number(value, f"material.color[{index}]") for index, value in enumerate(color)]
    if any(not 0.0 <= value <= 1.0 for value in channels):
        raise Img2ThreeJSAdapterError("MATERIAL_COLOR_OUT_OF_RANGE")
    opacity = _static_number(material.get("opacity", 1.0), "material.opacity")
    if not 0.0 <= opacity <= 1.0:
        raise Img2ThreeJSAdapterError("MATERIAL_OPACITY_OUT_OF_RANGE")
    metalness = _static_number(material.get("metalness", 0.0), "material.metalness")
    roughness = _static_number(material.get("roughness", 1.0), "material.roughness")
    if any(not 0.0 <= value <= 1.0 for value in (metalness, roughness)):
        raise Img2ThreeJSAdapterError("MATERIAL_FACTOR_OUT_OF_RANGE")
    drift = material.get("drift")
    if drift is None:
        drift = []
    if not isinstance(drift, list):
        raise Img2ThreeJSAdapterError("MATERIAL_DRIFT_INVALID")
    projected = {"color", "opacity", "metalness", "roughness"}
    for entry in drift:
        if not isinstance(entry, (list, tuple)) or len(entry) != 2 or not isinstance(entry[0], str):
            raise Img2ThreeJSAdapterError("MATERIAL_DRIFT_INVALID")
        key = entry[0]
        if key in projected:
            continue
        # transparent only rides on the projection when alpha is actually
        # present on the surviving opacity factor.
        if key == "transparent" and entry[1] is True and opacity < 1.0:
            continue
        raise Img2ThreeJSAdapterError(f"UNSUPPORTED_MATERIAL_FEATURE:{key}")
    if kind in {"MeshPhysicalMaterial", "MeshStandardMaterial"}:
        # Physical-only properties are guaranteed default here (any drift
        # failed closed above), so narrowing to the canonical Standard subset
        # is lossless for the fields the standardizer supports.
        projected_type = "MeshStandardMaterial"
        narrowing = "physical_to_standard" if kind == "MeshPhysicalMaterial" else "standard"
    elif kind == "MeshBasicMaterial":
        projected_type = "MeshBasicMaterial"
        narrowing = "unlit_to_pbr_approximation"
    else:
        projected_type = kind
        narrowing = "pass_through"
    out: dict[str, object] = {"type": projected_type, "color": channels, "opacity": opacity}
    if kind in {"MeshStandardMaterial", "MeshPhysicalMaterial"}:
        out["metalness"] = metalness
        out["roughness"] = roughness
    return out, narrowing


def bake_static_projection(manifest: object, *, asset_name: object, target_major_extent_meters: object) -> tuple[dict[str, object], dict[str, object]]:
    """Deterministically bake a runtime bake manifest into the static GLB input contract.

    Pure and offline: no subprocess, no runtime, no default physical scale.
    The caller anchor is REQUIRED and defines the single global
    relative->meter factor for the whole world-transform-baked aggregate.
    """

    name = _static_asset_name(asset_name)
    target = _static_physical_anchor(target_major_extent_meters)
    if not isinstance(manifest, Mapping):
        raise Img2ThreeJSAdapterError("BAKE_MANIFEST_INVALID")
    if manifest.get("schema") != RUNTIME_BAKE_SCHEMA:
        raise Img2ThreeJSAdapterError("BAKE_MANIFEST_SCHEMA_INVALID")
    if manifest.get("status") != "BAKED":
        raise Img2ThreeJSAdapterError("BAKE_MANIFEST_STATUS_INVALID")
    if manifest.get("up_axis") != "Y":
        raise Img2ThreeJSAdapterError("UP_AXIS_UNSUPPORTED")
    runtime = manifest.get("runtime")
    if not isinstance(runtime, Mapping) or runtime.get("node") != VERIFIED_NODE_VERSION or runtime.get("three") != VERIFIED_THREE_REVISION:
        raise Img2ThreeJSAdapterError("RUNTIME_PROFILE_MISMATCH")
    aggregate = manifest.get("aggregate")
    if not isinstance(aggregate, Mapping):
        raise Img2ThreeJSAdapterError("BAKE_AGGREGATE_MISSING")
    for flag, code in (("skinned_meshes", "STATIC_ASSET_MUST_NOT_REQUIRE_SKIN"), ("bones", "STATIC_ASSET_MUST_NOT_REQUIRE_SKIN"), ("skeletons", "STATIC_ASSET_MUST_NOT_REQUIRE_SKIN"), ("animations", "ANIMATIONS_UNSUPPORTED")):
        count = aggregate.get(flag)
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            raise Img2ThreeJSAdapterError("BAKE_AGGREGATE_INVALID")
        if count > 0:
            raise Img2ThreeJSAdapterError(code)
    nodes = manifest.get("nodes")
    if not isinstance(nodes, list) or not nodes or len(nodes) > MAX_STATIC_NODES:
        raise Img2ThreeJSAdapterError("BAKE_NODES_INVALID")

    worlds: dict[str, list[float]] = {}
    mesh_records: list[dict[str, object]] = []
    seen_ids: set[str] = set()
    bounds_min = [math.inf] * 3
    bounds_max = [-math.inf] * 3
    vertex_count = 0
    triangle_count = 0
    for node in nodes:
        if not isinstance(node, Mapping):
            raise Img2ThreeJSAdapterError("BAKE_NODE_INVALID")
        node_id = node.get("id")
        if not isinstance(node_id, str) or not node_id or node_id in seen_ids:
            raise Img2ThreeJSAdapterError("BAKE_NODE_ID_INVALID")  # duplicate identity rejection
        seen_ids.add(node_id)
        kind = node.get("kind")
        if kind not in {"group", "mesh"}:
            raise Img2ThreeJSAdapterError(f"BAKE_NODE_KIND_UNSUPPORTED:{kind!r}")
        matrix = node.get("matrix")
        if (
            not isinstance(matrix, (list, tuple))
            or len(matrix) != 16
            or any(isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) for value in matrix)
        ):
            raise Img2ThreeJSAdapterError("BAKE_NODE_MATRIX_INVALID")
        values = [float(value) for value in matrix]
        parent = node.get("parent")
        if parent is None:
            world = values
        elif not isinstance(parent, str) or parent not in worlds:
            # Reaching this point means the parent is missing, was duplicated,
            # or appears later than the child: unresolved hierarchy or cycle.
            raise Img2ThreeJSAdapterError("HIERARCHY_CYCLE_OR_MISSING_PARENT")
        else:
            world = _static_mat4_mul(worlds[parent], values)
        worlds[node_id] = world
        if kind != "mesh":
            continue
        payload = node.get("mesh")
        if not isinstance(payload, Mapping) or not isinstance(payload.get("geometry"), Mapping):
            raise Img2ThreeJSAdapterError("MESH_GEOMETRY_MISSING")
        geometry = payload["geometry"]
        if geometry.get("type") != "BufferGeometry":
            raise Img2ThreeJSAdapterError("GEOMETRY_UNSUPPORTED")
        positions = geometry.get("position")
        if not isinstance(positions, list) or not positions or len(positions) % 3:
            raise Img2ThreeJSAdapterError("GEOMETRY_POSITIONS_INVALID")
        if len(positions) > 3 * 1_000_000:
            raise Img2ThreeJSAdapterError("GEOMETRY_VERTEX_LIMIT_EXCEEDED")
        if any(isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) for value in positions):
            raise Img2ThreeJSAdapterError(f"GEOMETRY_NONFINITE:node {node_id}")
        baked: list[float] = []
        for index in range(0, len(positions), 3):
            point = [float(value) for value in positions[index : index + 3]]
            world_point = _static_mat4_point(world, point)
            for axis, value in enumerate(world_point):
                if not math.isfinite(value):
                    raise Img2ThreeJSAdapterError(f"GEOMETRY_NONFINITE:node {node_id}")
                bounds_min[axis] = min(bounds_min[axis], value)
                bounds_max[axis] = max(bounds_max[axis], value)
            baked.extend(world_point)
        count = len(positions) // 3
        indices = geometry.get("index")
        if indices is None:
            if count % 3:
                raise Img2ThreeJSAdapterError("GEOMETRY_TRIANGLE_COUNT_INVALID")
            triangles = count // 3
            projected_indices = None
        else:
            if not isinstance(indices, list) or not indices or len(indices) % 3:
                raise Img2ThreeJSAdapterError("GEOMETRY_INDEX_INVALID")
            projected_indices = []
            for value in indices:
                if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value < count:
                    raise Img2ThreeJSAdapterError("GEOMETRY_INDEX_INVALID")
                projected_indices.append(value)
            triangles = len(indices) // 3
        material, narrowing = _static_material(payload.get("material"))
        vertex_count += count
        triangle_count += triangles
        if triangle_count > MAX_STATIC_TRIANGLES:
            raise Img2ThreeJSAdapterError("GEOMETRY_TRIANGLE_LIMIT_EXCEEDED")
        mesh_records.append({"source_node": node_id, "baked": baked, "material": material, "indices": projected_indices, "narrowing": narrowing})
    if not mesh_records:
        raise Img2ThreeJSAdapterError("GEOMETRY_EMPTY")
    if len(mesh_records) > MAX_STATIC_MESHES:
        raise Img2ThreeJSAdapterError("MESH_COUNT_LIMIT_EXCEEDED")
    extents = [maximum - minimum for minimum, maximum in zip(bounds_min, bounds_max)]
    major_extent = max(extents)
    if not math.isfinite(major_extent) or major_extent <= 0.0:
        raise Img2ThreeJSAdapterError("BAKED_EXTENT_INVALID")
    # ONE global anchor for the whole aggregate; never per-mesh normalization
    # and never an implicit relative->meter assumption.
    scale = target / major_extent

    meshes: list[dict[str, object]] = []
    narrowings: dict[str, int] = {}
    for mesh_index, record in enumerate(mesh_records):
        mesh: dict[str, object] = {
            "name": f"mesh_{mesh_index:02d}",
            "positions": [value * scale for value in record["baked"]],
            "material": record["material"],
        }
        if record["indices"] is not None:
            mesh["indices"] = record["indices"]
        meshes.append(mesh)
        narrowings[record["narrowing"]] = narrowings.get(record["narrowing"], 0) + 1
    asset: dict[str, object] = {
        "name": name,
        "units": "meters",
        "up_axis": "Y",
        "transform": {"space": "flat", "position": [0.0, 0.0, 0.0], "rotation": [0.0, 0.0, 0.0], "scale": [1.0, 1.0, 1.0]},
        "meshes": meshes,
    }
    evidence: dict[str, object] = {
        "schema": STATIC_PROJECTION_SCHEMA,
        "operation": PROJECTION_OPERATION_ID,
        "operation_version": PROJECTION_OPERATION_VERSION,
        "output_contract": STATIC_PROJECTION_CONTRACT,
        "units": "meters",
        "up_axis": "Y",
        "transform_space": "flat",
        "asset_name": name,
        "target_major_extent_meters": target,
        "aggregate_major_extent_relative": major_extent,
        "relative_to_meter_scale": scale,
        "mesh_count": len(meshes),
        "vertex_count": vertex_count,
        "triangle_count": triangle_count,
        "baked_bounds_meters": {"min": [value * scale for value in bounds_min], "max": [value * scale for value in bounds_max]},
        "material_narrowing": narrowings,
        "hierarchy_nodes": len(nodes),
    }
    return asset, evidence


def verify_static_runtime_profile(runtime_root: str | Path, *, node_executable: str = "node") -> dict[str, str]:
    """Bind the pre-provisioned external runtime to the verified profile.

    Three.js and img2threejs are never bundled or installed here. A missing
    runtime, an unexpected Node version, an unexpected three version, or a
    missing module entrypoint is a hard failure. Broader Node/three
    compatibility is deliberately NOT claimed.
    """

    if not isinstance(node_executable, str) or not node_executable or not re.fullmatch(r"[A-Za-z0-9_.-]+", node_executable):
        raise Img2ThreeJSAdapterError("NODE_EXECUTABLE_INVALID")
    node = shutil.which(node_executable)
    if node is None:
        raise Img2ThreeJSAdapterError("NODE_RUNTIME_MISSING")
    try:
        result = subprocess.run(
            [node, "--version"],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            check=False,
            shell=False,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise Img2ThreeJSAdapterError("NODE_RUNTIME_UNAVAILABLE") from exc
    if result.returncode != 0 or result.stdout.strip() != VERIFIED_NODE_VERSION:
        raise Img2ThreeJSAdapterError(f"NODE_VERSION_UNVERIFIED:expected {VERIFIED_NODE_VERSION}")
    root = Path(runtime_root).expanduser()
    try:
        resolved = root.resolve(strict=True)
    except OSError as exc:
        raise Img2ThreeJSAdapterError("RUNTIME_ROOT_UNAVAILABLE") from exc
    three_root = resolved / "node_modules" / "three"
    package = three_root / "package.json"
    build = three_root / "build" / "three.module.js"
    if not package.is_file() or not build.is_file():
        raise Img2ThreeJSAdapterError("THREE_RUNTIME_MISSING")
    try:
        three_manifest = json.loads(package.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise Img2ThreeJSAdapterError("THREE_PACKAGE_MANIFEST_UNREADABLE") from exc
    if not isinstance(three_manifest, dict) or three_manifest.get("version") != VERIFIED_THREE_VERSION:
        raise Img2ThreeJSAdapterError(f"THREE_VERSION_UNVERIFIED:expected {VERIFIED_THREE_VERSION}")
    return {
        "node_executable": node,
        "node_version": VERIFIED_NODE_VERSION,
        "three_version": VERIFIED_THREE_VERSION,
        "three_revision": VERIFIED_THREE_REVISION,
        "three_entrypoint": str(build),
        "runtime_root": str(resolved),
    }


def project_static_asset(
    *,
    source_root: str | Path,
    workspace_root: str | Path,
    runtime_root: str | Path,
    spec_path: str | Path,
    asset_name: str,
    target_major_extent_meters: float,
    run_id: str,
    node_executable: str = "node",
    timeout_seconds: int = 120,
) -> dict[str, object]:
    """Run the bounded production seam: strict gate -> factory -> contained bake -> normalized projection.

    The returned ``asset`` object is exactly the promoted
    ``game.three.asset.static_glb_standardize`` input contract; the seam never
    writes GLB itself. ``target_major_extent_meters`` is REQUIRED (no default,
    never inferred from relative units). The generation route never exposes,
    accepts, or forwards the upstream test-only ``--allow-nonstrict`` escape
    hatch; a strict-quality gate failure aborts before any generation.
    The caller spec is captured once into a bounded buffer, bound by
    ``SPEC_SHA256``, and copied to an owned per-run path; the strict gate and
    the generator consume only that owned copy, whose hash is re-verified
    immediately before generation. The caller path is never reopened after
    capture, so post-capture mutation cannot alter the generated input.
    """

    name = _static_asset_name(asset_name)
    target = _static_physical_anchor(target_major_extent_meters)
    validate_identifier(run_id, field="run_id")
    if not isinstance(timeout_seconds, int) or not 1 <= timeout_seconds <= MAX_TIMEOUT_SECONDS:
        raise Img2ThreeJSAdapterError("TIMEOUT_OUT_OF_RANGE")
    workspace = _workspace_root(workspace_root)
    provenance = verify_upstream_checkout(source_root)
    profile = verify_static_runtime_profile(runtime_root, node_executable=node_executable)

    spec_relative = _relative_string(spec_path, field="spec")
    spec_target = bounded_workspace_path(workspace, spec_relative, field="spec")
    if not spec_target.is_file():
        raise Img2ThreeJSAdapterError("SPEC_NOT_FOUND")

    # TOCTOU closure: the caller-controlled spec is a trust dependency only
    # until the bytes are captured exactly once into a bounded buffer. From
    # here on every upstream subprocess consumes ONLY the owned per-run copy;
    # the caller path is never reopened during validation or generation, so
    # post-capture mutation, replacement, deletion, or symlink-swap of the
    # source cannot alter what is validated or generated.
    captured = spec_target.read_bytes()
    if len(captured) > MAX_SPEC_BYTES:
        raise Img2ThreeJSAdapterError("SPEC_INPUT_TOO_LARGE")
    spec_sha256 = _sha256(captured)

    run_relative = PurePosixPath("static-projection") / run_id
    run_dir = bounded_workspace_path(workspace, run_relative.as_posix(), field="run")
    if run_dir.exists():
        shutil.rmtree(run_dir)
    (run_dir / "node_modules").mkdir(parents=True, exist_ok=True)
    owned_spec_relative = (run_relative / "input-spec.json").as_posix()
    owned_spec_target = bounded_workspace_path(workspace, owned_spec_relative, field="owned_spec")
    owned_spec_target.write_bytes(captured)  # written once; never rewritten by the adapter
    three_source = Path(profile["runtime_root"]) / "node_modules" / "three"
    source_three_entrypoint = three_source / "build" / "three.module.js"
    if not source_three_entrypoint.is_file():
        raise Img2ThreeJSAdapterError("THREE_RUNTIME_MISSING")
    try:
        profile_entrypoint = Path(profile["three_entrypoint"]).resolve(strict=True)
        derived_source_entrypoint = source_three_entrypoint.resolve(strict=True)
    except OSError as exc:
        raise Img2ThreeJSAdapterError("THREE_RUNTIME_MISSING") from exc
    if profile_entrypoint != derived_source_entrypoint:
        raise Img2ThreeJSAdapterError("THREE_ENTRYPOINT_BINDING_MISMATCH")
    source_three_entry_sha256 = _sha256(derived_source_entrypoint.read_bytes())
    copied_three_root = run_dir / "node_modules" / "three"
    shutil.copytree(three_source, copied_three_root, symlinks=False)
    copied_three_package = copied_three_root / "package.json"
    copied_three_entrypoint = copied_three_root / "build" / "three.module.js"
    if not copied_three_package.is_file() or not copied_three_entrypoint.is_file():
        raise Img2ThreeJSAdapterError("THREE_RUNTIME_MISSING")
    try:
        copied_three_manifest = json.loads(copied_three_package.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise Img2ThreeJSAdapterError("THREE_PACKAGE_MANIFEST_UNREADABLE") from exc
    if not isinstance(copied_three_manifest, dict) or copied_three_manifest.get("version") != VERIFIED_THREE_VERSION:
        raise Img2ThreeJSAdapterError(f"THREE_VERSION_UNVERIFIED:expected {VERIFIED_THREE_VERSION}")
    copied_three_entry_sha256 = _sha256(copied_three_entrypoint.read_bytes())
    if copied_three_entry_sha256 != source_three_entry_sha256:
        raise Img2ThreeJSAdapterError("THREE_ENTRYPOINT_HASH_MISMATCH")
    (run_dir / "package.json").write_text(
        json.dumps({"name": f"p2p-img2threejs-static-{run_id}", "private": True, "type": "module"}, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if _sha256(owned_spec_target.read_bytes()) != spec_sha256:
        raise Img2ThreeJSAdapterError("SPEC_CONTENT_CHANGED")

    # Strict-quality production gate. _build_argv pins --strict-quality for
    # this entrypoint and has no parameter surface for the nonstrict hatch.
    validate_receipt = execute(
        "forge/stage2_spec/validate_sculpt_spec.py",
        source_root=source_root,
        workspace_root=workspace,
        spec_path=owned_spec_relative,
        timeout_seconds=timeout_seconds,
    )

    # Re-bind the exact validated bytes before generation. If the owned copy
    # drifted for any reason after validation, generation must not start.
    if _sha256(owned_spec_target.read_bytes()) != spec_sha256:
        raise Img2ThreeJSAdapterError("SPEC_CONTENT_CHANGED")

    factory_relative = (run_relative / "factory.ts").as_posix()
    generate_receipt = execute(
        "forge/stage3_build/generate_threejs_factory.py",
        source_root=source_root,
        workspace_root=workspace,
        spec_path=owned_spec_relative,
        output_path=factory_relative,
        timeout_seconds=timeout_seconds,
    )
    factory_target = bounded_workspace_path(workspace, factory_relative, field="factory")
    factory_bytes = factory_target.read_bytes()

    bake_relative = (run_relative / "bake-manifest.json").as_posix()
    bake_target = bounded_workspace_path(workspace, bake_relative, field="bake")
    harness = Path(__file__).with_name(STATIC_HARNESS_FILENAME)
    if not harness.is_file():
        raise Img2ThreeJSAdapterError("BAKE_HARNESS_UNAVAILABLE")
    bake_env = _minimal_environment(workspace)
    bake_env["NODE_OPTIONS"] = ""
    # --three-entry is adapter-derived from the per-run copied package. It is
    # not a public project/capability option and must never be caller-controlled.
    bake_result = subprocess.run(
        [
            profile["node_executable"],
            str(harness),
            "--factory",
            str(factory_target),
            "--out",
            str(bake_target),
            "--three-entry",
            str(copied_three_entrypoint),
        ],
        cwd=run_dir,
        env=bake_env,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
        shell=False,
        timeout=timeout_seconds,
    )
    if bake_result.returncode != 0 or not bake_target.is_file():
        raise Img2ThreeJSAdapterError("STATIC_BAKE_FAILED")
    if "P2P_IMG2THREEJS_BAKE_OK" not in (bake_result.stdout or ""):
        raise Img2ThreeJSAdapterError("STATIC_BAKE_ATTESTATION_MISSING")
    bake_bytes = bake_target.read_bytes()
    if len(bake_bytes) > MAX_BAKE_BYTES:
        raise Img2ThreeJSAdapterError("BAKE_OUTPUT_TOO_LARGE")
    try:
        bake_manifest = json.loads(bake_bytes.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise Img2ThreeJSAdapterError("BAKE_MANIFEST_INVALID") from exc
    if not isinstance(bake_manifest, dict) or bake_manifest.get("factory_sha256") != _sha256(factory_bytes):
        raise Img2ThreeJSAdapterError("BAKE_FACTORY_BINDING_MISMATCH")

    asset, evidence = bake_static_projection(bake_manifest, asset_name=name, target_major_extent_meters=target)
    projection_relative = (run_relative / "projection.json").as_posix()
    projection_target = bounded_workspace_path(workspace, projection_relative, field="projection")
    projection_target.write_text(json.dumps({"asset": asset, "evidence": evidence}, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return {
        "schema": "p2p-img2threejs-static-projection-receipt/1",
        "status": "PROJECTED",
        "operation": PROJECTION_OPERATION_ID,
        "operation_version": PROJECTION_OPERATION_VERSION,
        "generating_capability": "img2threejs",
        "run_id": run_id,
        "source": provenance,
        "runtime_profile": {
            **{key: profile[key] for key in ("node_version", "three_version", "three_revision")},
            "source_three_entrypoint": str(derived_source_entrypoint),
            "per_run_three_entrypoint": str(copied_three_entrypoint),
            "source_three_entry_sha256": source_three_entry_sha256,
            "copied_three_entry_sha256": copied_three_entry_sha256,
        },
        "spec_sha256": spec_sha256,
        "spec": {"workspace_relative_path": owned_spec_relative, "sha256": spec_sha256, "source_workspace_relative_path": spec_relative},
        "strict_quality_gate": {"entrypoint": "forge/stage2_spec/validate_sculpt_spec.py", "enforced": True, "receipt_status": validate_receipt["status"], "allow_nonstrict": "NEVER_EXPOSED"},
        "factory": {"entrypoint": "forge/stage3_build/generate_threejs_factory.py", "workspace_relative_path": factory_relative, "sha256": _sha256(factory_bytes), "receipt_status": generate_receipt["status"]},
        "bake": {"workspace_relative_path": bake_relative, "sha256": _sha256(bake_bytes), "stdout_sha256": _sha256(bake_result.stdout.encode("utf-8")), "stderr_sha256": _sha256(bake_result.stderr.encode("utf-8")), "shell": False, "network_policy": NETWORK_POLICY},
        "projection": {"workspace_relative_path": projection_relative, "contract": STATIC_PROJECTION_CONTRACT},
        "evidence": evidence,
        "asset": asset,
        "network_used": False,
        "dependencies_installed": False,
    }

__all__ = [
    "ALLOWED_ENTRYPOINTS",
    "CS2_METADATA_NETWORK",
    "DENIED_ENTRYPOINTS",
    "Img2ThreeJSAdapterError",
    "NETWORK_POLICY",
    "PROJECTION_OPERATION_ID",
    "PROJECTION_OPERATION_VERSION",
    "RUNTIME_BAKE_SCHEMA",
    "STATIC_PROJECTION_CONTRACT",
    "STATIC_PROJECTION_SCHEMA",
    "UPSTREAM_LICENSE",
    "UPSTREAM_REPOSITORY",
    "UPSTREAM_SHA",
    "UPSTREAM_TREE",
    "UPSTREAM_VERSION",
    "VERIFIED_NODE_VERSION",
    "VERIFIED_THREE_REVISION",
    "VERIFIED_THREE_VERSION",
    "bake_static_projection",
    "bounded_workspace_path",
    "execute",
    "project_static_asset",
    "validate_identifier",
    "verify_static_runtime_profile",
    "verify_upstream_checkout",
]
