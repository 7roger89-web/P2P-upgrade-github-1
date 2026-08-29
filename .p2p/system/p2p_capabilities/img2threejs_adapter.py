"""Fail-closed execution boundary for the pinned img2threejs workflow.

The upstream project is intentionally kept in an explicit external checkout. This
adapter does not download it, install dependencies, launch a shell, or expose the
upstream's network/plugin/renderer routes. It runs only the audited local workflow
and deterministic code-generation commands after binding the checkout to one
immutable commit and tree.
"""

from __future__ import annotations

import hashlib
import os
import re
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


__all__ = [
    "ALLOWED_ENTRYPOINTS",
    "CS2_METADATA_NETWORK",
    "DENIED_ENTRYPOINTS",
    "Img2ThreeJSAdapterError",
    "NETWORK_POLICY",
    "UPSTREAM_LICENSE",
    "UPSTREAM_REPOSITORY",
    "UPSTREAM_SHA",
    "UPSTREAM_TREE",
    "UPSTREAM_VERSION",
    "bounded_workspace_path",
    "execute",
    "validate_identifier",
    "verify_upstream_checkout",
]
