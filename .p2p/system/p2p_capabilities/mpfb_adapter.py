"""Bounded P2P-side execution contract for the selected MPFB2 forge stack.

This module builds and, only when a separately supplied authorization is true,
executes one pinned Blender background command. The current workstream keeps
that authorization false, so no Blender or MPFB process is launched here.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import signal
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Final, Mapping, Sequence

from .asset_provenance import CORE_ASSET_POLICY
from .character_recipe import CharacterRecipeError, load_recipe
from .img2threejs_adapter import Img2ThreeJSAdapterError, bounded_workspace_path


UPSTREAM_REPOSITORY: Final = "https://github.com/makehumancommunity/mpfb2.git"
MPFB_VERSION: Final = "2.0.17"
MPFB_RELEASE_SHA: Final = "80919fa4682335c41847f761a4d79dcad4124732"
MPFB_RELEASE_TREE: Final = "189a1d6694515ecfbdc40067218c5024389b4e43"
MPFB_CODE_LICENSE: Final = "GPL-3.0-or-later"
MPFB_CORE_ASSET_LICENSE: Final = "CC0-1.0"
ADAPTER_ENTRYPOINT: Final = ".p2p/system/p2p_capabilities/mpfb_adapter.py"
NETWORK_POLICY: Final = "DENY"
THIRD_PARTY_ASSET_POLICY: Final = "DENY"
THIRD_PARTY_ASSET_DEFAULT: Final = "DENY"
EXECUTION_AUTHORIZED: Final = False
MAX_TIMEOUT_SECONDS: Final = 1800
_IDENTIFIER: Final = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")
_SHA256: Final = re.compile(r"^[0-9a-f]{64}$")
_REPARSE_POINT: Final = 0x400


class MpfbAdapterError(ValueError):
    """Raised for a fail-closed adapter contract violation."""


class MpfbExecutionTimeout(MpfbAdapterError):
    """Raised after a timed-out process tree has been terminated."""


@dataclass(frozen=True)
class MpfbExecutionPlan:
    workspace_root: Path
    recipe_path: Path
    output_root: Path
    mpfb_root: Path
    argv: tuple[str, ...]
    environment: Mapping[str, str]
    timeout_seconds: int
    expected_outputs: tuple[str, ...]
    network_policy: str
    third_party_asset_policy: str
    execution_authorized: bool


def _reparse_point(path: Path) -> bool:
    try:
        attributes = int(getattr(os.stat(path, follow_symlinks=False), "st_file_attributes", 0))
    except OSError:
        return False
    return bool(attributes & _REPARSE_POINT)


def _safe_local_file(path: Path, field: str) -> Path:
    if path.is_symlink() or _reparse_point(path):
        raise MpfbAdapterError(f"{field.upper()}_SYMLINK_OR_REPARSE")
    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise MpfbAdapterError(f"{field.upper()}_UNAVAILABLE") from exc
    if resolved.is_symlink() or _reparse_point(resolved) or not resolved.is_file():
        raise MpfbAdapterError(f"{field.upper()}_INVALID")
    return resolved


def _safe_local_directory(path: Path, field: str) -> Path:
    if path.is_symlink() or _reparse_point(path):
        raise MpfbAdapterError(f"{field.upper()}_SYMLINK_OR_REPARSE")
    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise MpfbAdapterError(f"{field.upper()}_UNAVAILABLE") from exc
    if resolved.is_symlink() or _reparse_point(resolved) or not resolved.is_dir():
        raise MpfbAdapterError(f"{field.upper()}_INVALID")
    return resolved


def _validate_identifier(value: object, field: str) -> str:
    if not isinstance(value, str) or not _IDENTIFIER.fullmatch(value):
        raise MpfbAdapterError(f"{field.upper()}_INVALID")
    return value


def _validate_pinned_manifest(path: Path) -> dict[str, str]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise MpfbAdapterError("MPFB_PROVISIONING_MANIFEST_UNREADABLE") from exc
    if not isinstance(document, dict):
        raise MpfbAdapterError("MPFB_PROVISIONING_MANIFEST_INVALID")
    required = {"schema", "version", "release_sha", "release_tree", "root_sha256"}
    if set(document) != required:
        raise MpfbAdapterError("MPFB_PROVISIONING_MANIFEST_KEYS_INVALID")
    if document["schema"] != "p2p-mpfb2-provisioning/1" or document["version"] != MPFB_VERSION:
        raise MpfbAdapterError("MPFB_PROVISIONING_VERSION_INVALID")
    if document["release_sha"] != MPFB_RELEASE_SHA or document["release_tree"] != MPFB_RELEASE_TREE:
        raise MpfbAdapterError("MPFB_PROVISIONING_PIN_MISMATCH")
    if not isinstance(document["root_sha256"], str) or not _SHA256.fullmatch(document["root_sha256"]):
        raise MpfbAdapterError("MPFB_PROVISIONING_HASH_INVALID")
    return {key: str(value) for key, value in document.items()}


def hash_provisioned_root(root: str | Path, *, exclude: str | Path | None = None) -> str:
    """Hash every regular file in a provisioned root by stable relative path."""

    root_path = _safe_local_directory(Path(root), "mpfb_root")
    excluded = Path(exclude).resolve(strict=True) if exclude is not None else None
    digest = hashlib.sha256()
    files: list[Path] = []
    for directory, directories, filenames in os.walk(root_path, topdown=True, followlinks=False):
        current = Path(directory)
        for name in (*directories, *filenames):
            candidate = current / name
            if candidate.is_symlink() or _reparse_point(candidate):
                raise MpfbAdapterError("MPFB_ROOT_SYMLINK_OR_REPARSE")
        files.extend(current / name for name in filenames)
    for file_path in sorted(files, key=lambda item: item.relative_to(root_path).as_posix()):
        if excluded is not None and file_path.resolve(strict=True) == excluded:
            continue
        if not file_path.is_file():
            raise MpfbAdapterError("MPFB_ROOT_FILE_INVALID")
        try:
            relative = file_path.relative_to(root_path).as_posix().encode("utf-8")
            content = file_path.read_bytes()
        except (OSError, UnicodeError) as exc:
            raise MpfbAdapterError("MPFB_ROOT_FILE_UNREADABLE") from exc
        digest.update(relative)
        digest.update(b"\x00")
        digest.update(content)
    return digest.hexdigest()


def _minimal_environment(workspace: Path) -> dict[str, str]:
    try:
        temporary_root = bounded_workspace_path(workspace, ".tmp/mpfb2", field="temporary")
        temporary_root.mkdir(parents=True, exist_ok=True)
    except (OSError, Img2ThreeJSAdapterError) as exc:
        raise MpfbAdapterError("TEMPORARY_ROOT_INVALID") from exc
    environment = {
        "PATH": os.environ.get("PATH", ""),
        "PYTHONIOENCODING": "utf-8",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONNOUSERSITE": "1",
        "TEMP": str(temporary_root),
        "TMP": str(temporary_root),
        "TMPDIR": str(temporary_root),
    }
    if os.name == "nt" and "SystemRoot" in os.environ:
        environment["SystemRoot"] = os.environ["SystemRoot"]
    return environment


def _relative(workspace: Path, value: str | Path, field: str) -> tuple[str, Path]:
    try:
        target = bounded_workspace_path(workspace, value, field=field)
    except Img2ThreeJSAdapterError as exc:
        raise MpfbAdapterError(str(exc)) from exc
    raw = str(value).replace("\\", "/")
    if raw.startswith(("/", "~")) or re.match(r"^[A-Za-z]:", raw):
        raise MpfbAdapterError(f"{field.upper()}_MUST_BE_WORKSPACE_RELATIVE")
    current = workspace
    for part in Path(raw).parts:
        current = current / part
        if current.exists() and (current.is_symlink() or _reparse_point(current)):
            raise MpfbAdapterError(f"{field.upper()}_SYMLINK_OR_REPARSE")
    return Path(raw).as_posix(), target


def build_execution_plan(
    *,
    blender_executable: str | Path,
    workspace_root: str | Path,
    job_id: str,
    recipe_path: str | Path = "character.recipe.json",
    output_root: str | Path = "output",
    mpfb_root: str | Path = "mpfb2",
    mpfb_manifest: str | Path = "mpfb2/provisioning-manifest.json",
    timeout_seconds: int = 600,
    network_access: bool = False,
) -> MpfbExecutionPlan:
    """Construct one explicit, shell-free Blender command without launching it."""

    if network_access:
        raise MpfbAdapterError("NETWORK_NOT_PERMITTED")
    if not isinstance(timeout_seconds, int) or not 1 <= timeout_seconds <= MAX_TIMEOUT_SECONDS:
        raise MpfbAdapterError("TIMEOUT_OUT_OF_RANGE")
    normalized_job_id = _validate_identifier(job_id, "job_id")
    try:
        workspace = Path(workspace_root).expanduser().resolve(strict=True)
    except OSError as exc:
        raise MpfbAdapterError("WORKSPACE_UNAVAILABLE") from exc
    if not workspace.is_dir() or workspace.is_symlink() or _reparse_point(workspace):
        raise MpfbAdapterError("WORKSPACE_INVALID")
    blender = _safe_local_file(Path(blender_executable).expanduser(), "blender")
    recipe_relative, recipe_target = _relative(workspace, recipe_path, "recipe")
    recipe = load_recipe(recipe_target)
    if recipe["character_id"] != normalized_job_id:
        raise MpfbAdapterError("JOB_RECIPE_ID_MISMATCH")
    output_relative, output_target = _relative(workspace, output_root, "output_root")
    if output_target.exists() and not output_target.is_dir():
        raise MpfbAdapterError("OUTPUT_ROOT_NOT_DIRECTORY")
    if not output_target.parent.is_dir():
        raise MpfbAdapterError("OUTPUT_ROOT_PARENT_INVALID")
    mpfb_relative, mpfb_target = _relative(workspace, mpfb_root, "mpfb_root")
    mpfb_directory = _safe_local_directory(mpfb_target, "mpfb_root")
    manifest_relative, manifest_target = _relative(workspace, mpfb_manifest, "mpfb_manifest")
    if manifest_target.parent != mpfb_directory and mpfb_directory not in manifest_target.parents:
        raise MpfbAdapterError("MPFB_MANIFEST_OUTSIDE_ROOT")
    manifest_file = _safe_local_file(manifest_target, "mpfb_manifest")
    manifest = _validate_pinned_manifest(manifest_file)
    if hash_provisioned_root(mpfb_directory, exclude=manifest_file) != manifest["root_sha256"]:
        raise MpfbAdapterError("MPFB_PROVISIONING_ROOT_HASH_MISMATCH")
    source_file = Path(__file__).resolve()
    repository_root = source_file.parents[3]
    if source_file.relative_to(repository_root).as_posix() != ADAPTER_ENTRYPOINT:
        raise MpfbAdapterError("ENTRYPOINT_BINDING_INVALID")
    entrypoint = source_file.as_posix()
    environment = _minimal_environment(workspace)
    argv = (
        str(blender),
        "--background",
        "--python",
        entrypoint,
        "--",
        "--recipe",
        recipe_relative,
        "--output-root",
        output_relative,
        "--mpfb-root",
        mpfb_relative,
        "--mpfb-manifest",
        manifest_relative,
        "--character-id",
        normalized_job_id,
        "--mpfb-version",
        manifest["version"],
        "--mpfb-release-sha",
        manifest["release_sha"],
        "--asset-policy",
        CORE_ASSET_POLICY,
        "--network",
        "deny",
    )
    expected_outputs = (f"{normalized_job_id}.glb", f"{normalized_job_id}.asset-provenance.json")
    return MpfbExecutionPlan(
        workspace_root=workspace,
        recipe_path=recipe_target,
        output_root=output_target,
        mpfb_root=mpfb_directory,
        argv=argv,
        environment=environment,
        timeout_seconds=timeout_seconds,
        expected_outputs=expected_outputs,
        network_policy=NETWORK_POLICY,
        third_party_asset_policy=THIRD_PARTY_ASSET_POLICY,
        execution_authorized=EXECUTION_AUTHORIZED,
    )


def validate_output_directory(output_root: str | Path, expected_outputs: Sequence[str]) -> None:
    """Require exactly the two declared output files and nothing else."""

    root = Path(output_root)
    if not root.is_dir() or root.is_symlink() or _reparse_point(root):
        raise MpfbAdapterError("OUTPUT_ROOT_INVALID")
    actual = {entry.name for entry in root.iterdir()}
    expected = set(expected_outputs)
    if actual != expected:
        raise MpfbAdapterError("UNDECLARED_OUTPUTS_OR_MISSING_OUTPUTS")
    for name in expected:
        path = root / name
        if path.is_symlink() or _reparse_point(path) or not path.is_file():
            raise MpfbAdapterError("OUTPUT_FILE_INVALID")


def _terminate_process_tree(
    process: object,
    *,
    platform_name: str | None = None,
    termination_runner: Callable[..., object] = subprocess.run,
    killpg: Callable[[int, int], None] | None = None,
) -> None:
    """Terminate the complete child tree using a fixed, shell-free mechanism."""

    platform_name = platform_name or os.name
    pid = getattr(process, "pid", None)
    if not isinstance(pid, int) or pid <= 0:
        raise MpfbAdapterError("PROCESS_ID_INVALID")
    if platform_name == "nt":
        termination_runner(
            ["taskkill", "/PID", str(pid), "/T", "/F"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            shell=False,
        )
        return
    if killpg is None:
        killpg = getattr(os, "killpg", None)
    if killpg is None or not hasattr(os, "getpgid"):
        raise MpfbAdapterError("PROCESS_GROUP_TERMINATION_UNAVAILABLE")
    killpg(os.getpgid(pid), signal.SIGTERM)
    wait = getattr(process, "wait", None)
    if callable(wait):
        try:
            wait(timeout=5)
        except subprocess.TimeoutExpired:
            killpg(os.getpgid(pid), signal.SIGKILL)
            wait()


def execute_plan(
    plan: MpfbExecutionPlan,
    *,
    execution_authorized: bool = False,
    popen_factory: Callable[..., object] = subprocess.Popen,
    termination_runner: Callable[..., object] = subprocess.run,
    platform_name: str | None = None,
) -> dict[str, object]:
    """Run the already-built plan only with explicit separate authorization."""

    if not execution_authorized:
        raise MpfbAdapterError("CHARACTER_FORGE_EXECUTION_NOT_AUTHORIZED")
    if plan.network_policy != NETWORK_POLICY or plan.third_party_asset_policy != THIRD_PARTY_ASSET_POLICY:
        raise MpfbAdapterError("EXECUTION_POLICY_MISMATCH")
    if len(plan.argv) < 5 or plan.argv[1:5] != ("--background", "--python", plan.argv[3], "--"):
        raise MpfbAdapterError("ENTRYPOINT_COMMAND_INVALID")
    if plan.argv[3] != Path(__file__).resolve().as_posix() or any(flag in plan.argv for flag in ("--python-expr", "-c")):
        raise MpfbAdapterError("ENTRYPOINT_NOT_ALLOWLISTED")
    if set(plan.environment) - {"PATH", "PYTHONIOENCODING", "PYTHONDONTWRITEBYTECODE", "PYTHONNOUSERSITE", "TEMP", "TMP", "TMPDIR", "SystemRoot"}:
        raise MpfbAdapterError("ENVIRONMENT_NOT_MINIMAL")
    popen_kwargs: dict[str, object] = {
        "cwd": str(plan.workspace_root),
        "env": dict(plan.environment),
        "stdin": subprocess.DEVNULL,
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
        "text": True,
        "shell": False,
    }
    if os.name == "nt":
        popen_kwargs["creationflags"] = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    else:
        popen_kwargs["start_new_session"] = True
    process = popen_factory(list(plan.argv), **popen_kwargs)
    try:
        stdout, stderr = process.communicate(timeout=plan.timeout_seconds)
    except subprocess.TimeoutExpired as exc:
        _terminate_process_tree(process, platform_name=platform_name, termination_runner=termination_runner)
        raise MpfbExecutionTimeout("TIMEOUT_PROCESS_TREE_TERMINATED") from exc
    if getattr(process, "returncode", None) != 0:
        raise MpfbAdapterError("BLENDER_COMMAND_FAILED")
    validate_output_directory(plan.output_root, plan.expected_outputs)
    from .glb_validator import validate_glb_output

    glb_path = plan.output_root / plan.expected_outputs[0]
    provenance_path = plan.output_root / plan.expected_outputs[1]
    validation = validate_glb_output(glb_path, provenance_path, load_recipe(plan.recipe_path))
    return {
        "status": "EXECUTED_AND_STRUCTURALLY_VALID",
        "argv": list(plan.argv),
        "network_policy": NETWORK_POLICY,
        "network_used": False,
        "shell": False,
        "secrets_inherited": False,
        "stdout_sha256": hashlib.sha256(str(stdout).encode("utf-8")).hexdigest(),
        "stderr_sha256": hashlib.sha256(str(stderr).encode("utf-8")).hexdigest(),
        "validation": validation,
    }


__all__ = [
    "ADAPTER_ENTRYPOINT",
    "EXECUTION_AUTHORIZED",
    "MAX_TIMEOUT_SECONDS",
    "MPFB_CODE_LICENSE",
    "MPFB_CORE_ASSET_LICENSE",
    "MPFB_RELEASE_SHA",
    "MPFB_RELEASE_TREE",
    "MPFB_VERSION",
    "MpfbAdapterError",
    "MpfbExecutionPlan",
    "MpfbExecutionTimeout",
    "NETWORK_POLICY",
    "THIRD_PARTY_ASSET_POLICY",
    "THIRD_PARTY_ASSET_DEFAULT",
    "UPSTREAM_REPOSITORY",
    "build_execution_plan",
    "execute_plan",
    "hash_provisioned_root",
    "validate_output_directory",
]
