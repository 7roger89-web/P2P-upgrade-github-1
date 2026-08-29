"""Canonical project-pin producer and validator for P2P projects.

Schema ``p2p-project-pin/1`` remains the packaged-runtime adoption contract.
Schema ``p2p-project-pin/2`` adds an explicit ``PROJECTION_ONLY`` branch for
selected, project-local host instructions.  The v2 branch is deliberately
offline and does not certify or install a P2P runtime.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping
from urllib.parse import urlsplit


PROJECT_PIN_SCHEMA = "p2p-project-pin/1"
PROJECT_PIN_V2_SCHEMA = "p2p-project-pin/2"
PROJECT_PIN_SCHEMAS = (PROJECT_PIN_SCHEMA, PROJECT_PIN_V2_SCHEMA)
PACKAGED_RUNTIME = "PACKAGED_RUNTIME"
PROJECTION_ONLY = "PROJECTION_ONLY"
PROJECT_PIN_MODES = (PACKAGED_RUNTIME, PROJECTION_ONLY)
MODE_PACKAGED_RUNTIME = PACKAGED_RUNTIME
MODE_PROJECTION_ONLY = PROJECTION_ONLY

CANDIDATE_MANIFEST_NAME = "CANDIDATE-DISTRIBUTION-MANIFEST.json"
SOURCE_BINDING_NAME = "SOURCE-BINDING.json"
ARTIFACT_IDENTITY_NAME = "ARTIFACT-IDENTITY.json"
VERSION_NAME = "VERSION"
PROJECTION_BINDING_SCHEMA = "p2p-project-projection-binding/1"
PROJECTION_MATERIALIZATION_VERSION = "p2p-project-materialization/1"
PROJECT_SOURCE_BINDING_SCHEMA = "p2p-project-source-binding/1"
PROJECTED_FILE_OWNERSHIP = "P2P_MANAGED_PROJECTED_FILE"
HEX64 = re.compile(r"^[0-9a-fA-F]{64}$")
HEX40 = re.compile(r"^[0-9a-fA-F]{40}$")
_DRIVE_PATH = re.compile(r"^[A-Za-z]:/")
_SECRET_KEY = re.compile(
    r"(?:password|passwd|secret|token|api[_-]?key|private[_-]?key|credential|access[_-]?key)",
    re.IGNORECASE,
)
_PROJECTED_ROOTS = {".agents", ".claude", ".gemini", ".cursor", ".github"}
_PROJECTION_PIN_KEYS = {
    "schema",
    "mode",
    "project_id",
    "project_name",
    "project_version",
    "project_fingerprint",
    "source_binding",
    "selected_capabilities",
    "projection",
    "runtime_claim",
    "rollback",
    "verification_status",
    "producer",
}
_PROJECTION_BINDING_KEYS = {
    "schema",
    "materialization_version",
    "host_kind",
    "plan_sha256",
    "plan_snapshot",
    "managed_files",
    "policy_binding",
    "context_binding",
}


class ProjectPinError(ValueError):
    """Raised when a project pin or its candidate binding is invalid."""


def canonical_json(value: Any) -> str:
    """Serialize JSON values deterministically for binding hashes."""

    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ProjectPinError("SERIALIZATION_INVALID") from exc


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ProjectPinError(f"{label}_UNREADABLE: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ProjectPinError(f"{label}_OBJECT_REQUIRED: {path}")
    return value


def _require_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ProjectPinError(f"{label}_REQUIRED")
    return value.strip()


def _require_hex(value: Any, label: str, pattern: re.Pattern[str]) -> str:
    text = _require_text(value, label).lower()
    if pattern.fullmatch(text) is None:
        raise ProjectPinError(f"{label}_INVALID")
    return text


def _bytes_sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
    except OSError as exc:
        raise ProjectPinError(f"FILE_UNREADABLE: {path}: {exc}") from exc
    return digest.hexdigest()


def _managed_project_path(relative: str) -> bool:
    parts = Path(relative).parts
    if not parts:
        return True
    if parts[0] in {".p2p", ".git", ".agents", ".codex"}:
        return True
    return parts[0] in {"AGENTS.md", "CLAUDE.md"}


def project_fingerprint(project_root: Path) -> str:
    """Fingerprint project-owned files, excluding P2P-managed surfaces."""

    root = project_root.resolve()
    entries: list[str] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        if _managed_project_path(relative):
            continue
        entries.append(f"{relative}:{_sha256(path)}")
    return _bytes_sha256("\n".join(entries).encode("utf-8"))


def _reject_secret_fields(value: Any, location: str = "VALUE") -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            if isinstance(key, str) and _SECRET_KEY.search(key):
                raise ProjectPinError(f"{location}_SECRET_FIELD_FORBIDDEN:{key}")
            _reject_secret_fields(nested, f"{location}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, nested in enumerate(value):
            _reject_secret_fields(nested, f"{location}[{index}]")


def _canonical_relative(value: Any, label: str = "RELATIVE_PATH") -> str:
    raw = _require_text(value, label).replace("\\", "/")
    if "\x00" in raw:
        raise ProjectPinError(f"{label}_INVALID")
    if raw.startswith(("/", "~")) or _DRIVE_PATH.match(raw):
        raise ProjectPinError(f"{label}_ABSOLUTE")
    parts = PurePosixPath(raw).parts
    if not parts or any(part in {"", ".", ".."} for part in parts):
        raise ProjectPinError(f"{label}_TRAVERSAL")
    if ":" in parts[0]:
        raise ProjectPinError(f"{label}_INVALID")
    return "/".join(parts)


def _project_identifier(value: Any) -> str:
    text = _require_text(value, "PROJECT_ID")
    if "\x00" in text or "/" in text or "\\" in text or text in {".", ".."}:
        raise ProjectPinError("PROJECT_ID_PATH_LIKE")
    if len(text) > 200:
        raise ProjectPinError("PROJECT_ID_TOO_LONG")
    return text


def _is_reparse_or_symlink(path: Path) -> bool:
    if path.is_symlink() or os.path.islink(path):
        return True
    try:
        attributes = path.lstat().st_file_attributes
    except (AttributeError, FileNotFoundError, OSError):
        return False
    return bool(attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))


def _assert_no_link_components(root: Path, target: Path, label: str) -> None:
    root = root.resolve()
    try:
        relative = target.absolute().relative_to(root)
    except ValueError as exc:
        raise ProjectPinError(f"{label}_OUTSIDE_ROOT") from exc
    current = root
    for component in relative.parts:
        current = current / component
        if _is_reparse_or_symlink(current):
            raise ProjectPinError(f"{label}_SYMLINK_ESCAPE")


def _projected_path(root: Path, relative: Any, label: str = "PROJECTED_PATH") -> tuple[str, Path]:
    normal = _canonical_relative(relative, label)
    first = PurePosixPath(normal).parts[0]
    if first not in _PROJECTED_ROOTS:
        raise ProjectPinError(f"{label}_UNAPPROVED_ROOT")
    target = root / Path(*PurePosixPath(normal).parts)
    _assert_no_link_components(root, target, label)
    return normal, target


def _source_binding(repository: Any, commit: Any, tree: Any) -> dict[str, str]:
    repo = _require_text(repository, "SOURCE_REPOSITORY")
    parsed = urlsplit(repo)
    if (
        parsed.scheme.lower() != "https"
        or not parsed.netloc
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or any(character.isspace() for character in repo)
        or parsed.path in {"", "/"}
    ):
        raise ProjectPinError("SOURCE_REPOSITORY_INVALID")
    return {
        "schema": PROJECT_SOURCE_BINDING_SCHEMA,
        "repository": repo,
        "commit": _require_hex(commit, "SOURCE_COMMIT", HEX40),
        "tree": _require_hex(tree, "SOURCE_TREE", HEX40),
        "status": "VERIFIED",
    }


def _normalise_capabilities(selected_capabilities: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    if isinstance(selected_capabilities, (str, bytes, Mapping)):
        raise ProjectPinError("SELECTED_CAPABILITIES_LIST_REQUIRED")
    try:
        entries = list(selected_capabilities)
    except TypeError as exc:
        raise ProjectPinError("SELECTED_CAPABILITIES_LIST_REQUIRED") from exc
    if not entries:
        raise ProjectPinError("SELECTED_CAPABILITIES_EMPTY")
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in entries:
        if not isinstance(raw, Mapping):
            raw_value = getattr(raw, "raw", None)
            if not isinstance(raw_value, Mapping):
                raise ProjectPinError("SELECTED_CAPABILITY_OBJECT_REQUIRED")
            raw = raw_value
        _reject_secret_fields(raw, "SELECTED_CAPABILITY")
        capability_id = _require_text(raw.get("capability_id"), "CAPABILITY_ID")
        if capability_id in seen:
            raise ProjectPinError("SELECTED_CAPABILITIES_DUPLICATE")
        seen.add(capability_id)
        state = _require_text(raw.get("state", "UNKNOWN"), "CAPABILITY_STATE")
        readiness = _require_text(raw.get("readiness", "UNKNOWN"), "CAPABILITY_READINESS")
        source_hash = _require_hex(raw.get("source_hash"), "CAPABILITY_SOURCE_HASH", HEX64)
        entrypoint_hash = _require_hex(raw.get("entrypoint_hash"), "CAPABILITY_ENTRYPOINT_HASH", HEX64)
        runtime = raw.get("runtime_readiness", {})
        if runtime is None:
            runtime = {}
        if not isinstance(runtime, Mapping):
            raise ProjectPinError("CAPABILITY_RUNTIME_READINESS_INVALID")
        runtime = dict(runtime)
        for field in ("executable_registered", "executable", "activated"):
            if field in runtime and type(runtime[field]) is not bool:
                raise ProjectPinError("CAPABILITY_RUNTIME_READINESS_INVALID")
        lowered_id = capability_id.lower()
        if "img2threejs" in lowered_id:
            if runtime.get("executable_registered") is True or runtime.get("executable") is True:
                raise ProjectPinError("CAPABILITY_EXECUTABLE_UPGRADE_FORBIDDEN")
        if "tripo" in lowered_id:
            if runtime.get("activated") is True or runtime.get("executable_registered") is True or runtime.get("executable") is True:
                raise ProjectPinError("CAPABILITY_TRIPO_ACTIVATION_FORBIDDEN")
            if state.upper() in {"ACTIVATED", "EXECUTABLE", "HEALTHY"}:
                raise ProjectPinError("CAPABILITY_TRIPO_ACTIVATION_FORBIDDEN")
        result.append(
            {
                "capability_id": capability_id,
                "state": state,
                "readiness": readiness,
                "source_hash": source_hash,
                "entrypoint_hash": entrypoint_hash,
                "runtime_readiness": runtime,
            }
        )
    return result


def _plan_mapping(projection_plan: Any) -> dict[str, Any]:
    if hasattr(projection_plan, "to_dict"):
        raw = projection_plan.to_dict()
    elif isinstance(projection_plan, Mapping):
        raw = dict(projection_plan)
    else:
        raise ProjectPinError("PROJECTION_PLAN_OBJECT_REQUIRED")
    if not isinstance(raw, dict):
        raise ProjectPinError("PROJECTION_PLAN_OBJECT_REQUIRED")
    _reject_secret_fields(raw, "PROJECTION_PLAN")
    return raw


def _validate_plan(projection_plan: Any) -> dict[str, Any]:
    plan = _plan_mapping(projection_plan)
    if plan.get("schema") != "p2p-host-skill-projection-plan/1":
        raise ProjectPinError("PROJECTION_PLAN_SCHEMA_INVALID")
    if plan.get("status") != "READY" or plan.get("blocked_reason") is not None:
        raise ProjectPinError("PROJECTION_PLAN_NOT_READY")
    if plan.get("content_loaded") is not True:
        raise ProjectPinError("PROJECTION_PLAN_CONTENT_NOT_LOADED")
    for field in (
        "writes_performed",
        "provider_mutated",
        "model_mutated",
        "auth_mutated",
        "permission_mutated",
        "task_state_mutated",
    ):
        if plan.get(field) is not False:
            raise ProjectPinError(f"PROJECTION_PLAN_{field.upper()}_FORBIDDEN")
    _require_text(plan.get("host_kind"), "PLAN_HOST_KIND")
    _require_text(plan.get("capability_id"), "PLAN_CAPABILITY_ID")
    _require_hex(plan.get("source_hash"), "PLAN_SOURCE_HASH", HEX64)
    _require_hex(plan.get("entrypoint_hash"), "PLAN_ENTRYPOINT_HASH", HEX64)
    files = plan.get("files")
    if not isinstance(files, list) or not files:
        raise ProjectPinError("PROJECTION_PLAN_FILES_INVALID")
    seen: set[str] = set()
    for item in files:
        if not isinstance(item, Mapping):
            raise ProjectPinError("PROJECTION_PLAN_FILE_INVALID")
        relative = _canonical_relative(item.get("relative_target"), "PLAN_TARGET_PATH")
        if PurePosixPath(relative).parts[0] not in _PROJECTED_ROOTS:
            raise ProjectPinError("PLAN_TARGET_PATH_UNAPPROVED_ROOT")
        if relative in seen:
            raise ProjectPinError("PROJECTION_PLAN_TARGET_DUPLICATE")
        seen.add(relative)
        if item.get("ownership_class") != "P2P_PROJECT_MANAGED":
            raise ProjectPinError("PROJECTION_PLAN_OWNERSHIP_INVALID")
        _require_hex(item.get("content_hash"), "PLAN_CONTENT_HASH", HEX64)
    return plan


def _validate_projection_request(
    *,
    source_repository: Any,
    source_commit: Any,
    source_tree: Any,
    selected_capabilities: Iterable[Mapping[str, Any]],
    projection_plan: Any,
) -> tuple[dict[str, str], list[dict[str, Any]], dict[str, Any]]:
    source = _source_binding(source_repository, source_commit, source_tree)
    capabilities = _normalise_capabilities(selected_capabilities)
    plan = _validate_plan(projection_plan)
    selected = {item["capability_id"]: item for item in capabilities}
    capability_id = plan["capability_id"]
    if capability_id not in selected:
        raise ProjectPinError("PLAN_CAPABILITY_NOT_SELECTED")
    if _require_hex(plan["source_hash"], "PLAN_SOURCE_HASH", HEX64) != selected[capability_id]["source_hash"]:
        raise ProjectPinError("PLAN_CAPABILITY_SOURCE_HASH_MISMATCH")
    if _require_hex(plan["entrypoint_hash"], "PLAN_ENTRYPOINT_HASH", HEX64) != selected[capability_id]["entrypoint_hash"]:
        raise ProjectPinError("PLAN_CAPABILITY_ENTRYPOINT_HASH_MISMATCH")
    return source, capabilities, plan


def validate_projection_request(
    *,
    source_repository: str,
    source_commit: str,
    source_tree: str,
    selected_capabilities: Iterable[Mapping[str, Any]],
    projection_plan: Any,
) -> dict[str, Any]:
    """Validate projection inputs before any target file is materialized."""

    source, capabilities, plan = _validate_projection_request(
        source_repository=source_repository,
        source_commit=source_commit,
        source_tree=source_tree,
        selected_capabilities=selected_capabilities,
        projection_plan=projection_plan,
    )
    return {
        "source_binding": source,
        "selected_capabilities": capabilities,
        "plan": plan,
    }


def _normalise_previous_state(value: Any) -> dict[str, str]:
    if not isinstance(value, Mapping):
        raise ProjectPinError("MANAGED_FILE_PREVIOUS_STATE_INVALID")
    state = _require_text(value.get("state"), "MANAGED_FILE_PREVIOUS_STATE").upper()
    if state == "ABSENT":
        if len(value) != 1:
            raise ProjectPinError("MANAGED_FILE_PREVIOUS_STATE_INVALID")
        return {"state": "ABSENT"}
    if state == "PRESENT":
        previous_hash = value.get("content_sha256", value.get("sha256"))
        return {"state": "PRESENT", "content_sha256": _require_hex(previous_hash, "PREVIOUS_CONTENT_SHA256", HEX64)}
    raise ProjectPinError("MANAGED_FILE_PREVIOUS_STATE_INVALID")


def _normalise_managed_files(
    root: Path,
    plan: Mapping[str, Any],
    managed_files: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    if isinstance(managed_files, (str, bytes, Mapping)):
        raise ProjectPinError("MANAGED_FILES_LIST_REQUIRED")
    try:
        records = list(managed_files)
    except TypeError as exc:
        raise ProjectPinError("MANAGED_FILES_LIST_REQUIRED") from exc
    plan_files = plan.get("files", [])
    expected_paths = [
        _canonical_relative(item.get("relative_target"), "PLAN_TARGET_PATH")
        for item in plan_files
    ]
    if [record.get("relative_path") if isinstance(record, Mapping) else None for record in records] != expected_paths:
        raise ProjectPinError("MANAGED_FILES_PLAN_ORDER_MISMATCH")
    result: list[dict[str, Any]] = []
    for record, expected in zip(records, expected_paths):
        if not isinstance(record, Mapping):
            raise ProjectPinError("MANAGED_FILE_INVALID")
        relative, target = _projected_path(root, record.get("relative_path"), "MANAGED_FILE_PATH")
        if relative != expected:
            raise ProjectPinError("MANAGED_FILES_PLAN_ORDER_MISMATCH")
        if record.get("ownership") != PROJECTED_FILE_OWNERSHIP:
            raise ProjectPinError("MANAGED_FILE_OWNERSHIP_INVALID")
        content_hash = _require_hex(record.get("content_sha256"), "MANAGED_FILE_CONTENT_SHA256", HEX64)
        previous_state = _normalise_previous_state(record.get("previous_state"))
        if not target.is_file() or _is_reparse_or_symlink(target):
            raise ProjectPinError("MANAGED_FILE_MISSING_OR_LINK")
        if _sha256(target) != content_hash:
            raise ProjectPinError("MANAGED_FILE_CONTENT_MISMATCH")
        result.append(
            {
                "relative_path": relative,
                "ownership": PROJECTED_FILE_OWNERSHIP,
                "content_sha256": content_hash,
                "previous_state": previous_state,
            }
        )
    return result


def _surface_binding(root: Path, path: Path | None, expected_relative: str, label: str, expected_schema: str) -> dict[str, str] | None:
    if path is None:
        return None
    candidate = path if path.is_absolute() else root / path
    try:
        relative_raw = candidate.absolute().relative_to(root).as_posix()
    except ValueError as exc:
        raise ProjectPinError(f"{label}_PATH_OUTSIDE_ROOT") from exc
    relative = _canonical_relative(relative_raw, f"{label}_PATH")
    if relative != expected_relative:
        raise ProjectPinError(f"{label}_PATH_INVALID")
    _assert_no_link_components(root, candidate, label)
    if not candidate.is_file():
        raise ProjectPinError(f"{label}_MISSING")
    payload = _read_json(candidate, label)
    schema = payload.get("schema") or payload.get("schema_version")
    if schema != expected_schema:
        raise ProjectPinError(f"{label}_SCHEMA_INVALID")
    return {"relative_path": expected_relative, "schema": expected_schema, "sha256": _sha256(candidate)}


def _validate_surface_binding(root: Path, binding: Any, expected_relative: str, label: str, expected_schema: str) -> None:
    if not isinstance(binding, Mapping):
        raise ProjectPinError(f"{label}_BINDING_INVALID")
    relative = _canonical_relative(binding.get("relative_path"), f"{label}_PATH")
    if relative != expected_relative:
        raise ProjectPinError(f"{label}_PATH_INVALID")
    target = root / Path(*PurePosixPath(relative).parts)
    _assert_no_link_components(root, target, label)
    if not target.is_file() or _is_reparse_or_symlink(target):
        raise ProjectPinError(f"{label}_MISSING_OR_LINK")
    if binding.get("schema") != expected_schema:
        raise ProjectPinError(f"{label}_SCHEMA_INVALID")
    expected_hash = binding.get("sha256", binding.get("content_sha256"))
    if _sha256(target) != _require_hex(expected_hash, f"{label}_SHA256", HEX64):
        raise ProjectPinError(f"{label}_SHA256_MISMATCH")
    payload = _read_json(target, label)
    if (payload.get("schema") or payload.get("schema_version")) != expected_schema:
        raise ProjectPinError(f"{label}_SCHEMA_INVALID")


def _candidate_metadata(metadata_root: Path) -> tuple[str, dict[str, Any], dict[str, Any], dict[str, Any]]:
    root = metadata_root.resolve()
    version = _require_text((root / VERSION_NAME).read_text(encoding="utf-8"), "PACKAGE_VERSION")
    candidate = _read_json(root / CANDIDATE_MANIFEST_NAME, "CANDIDATE_MANIFEST")
    binding = _read_json(root / SOURCE_BINDING_NAME, "SOURCE_BINDING")
    identity = _read_json(root / ARTIFACT_IDENTITY_NAME, "ARTIFACT_IDENTITY")
    if candidate.get("schema_version") != "p2p-codex-candidate-distribution/1":
        raise ProjectPinError("CANDIDATE_MANIFEST_SCHEMA_INVALID")
    if candidate.get("candidate_version") != version:
        raise ProjectPinError("CANDIDATE_VERSION_MISMATCH")
    if candidate.get("candidate_vs_official") != "UNPROMOTED_SUCCESSOR_CANDIDATE":
        raise ProjectPinError("CANDIDATE_PROMOTION_STATE_INVALID")
    if not isinstance(candidate.get("official_baseline_version"), str):
        raise ProjectPinError("OFFICIAL_BASELINE_VERSION_MISSING")
    _require_hex(candidate.get("official_baseline_sha256"), "OFFICIAL_BASELINE_SHA256", HEX64)
    if binding.get("schema_version") != "p2p-codex-source-binding/1":
        raise ProjectPinError("SOURCE_BINDING_SCHEMA_INVALID")
    if binding.get("candidate_version") != version:
        raise ProjectPinError("SOURCE_BINDING_VERSION_MISMATCH")
    _require_hex(binding.get("source_commit"), "SOURCE_COMMIT", HEX40)
    _require_hex(binding.get("source_tree"), "SOURCE_TREE", HEX40)
    if (
        binding.get("source_commit_object") != "VERIFIED"
        or binding.get("source_tree_object") != "VERIFIED"
        or binding.get("source_tree_bound_to_commit") != "VERIFIED"
    ):
        raise ProjectPinError("SOURCE_BINDING_OBJECTS_UNVERIFIED")
    if identity.get("candidate_version") != version:
        raise ProjectPinError("ARTIFACT_IDENTITY_VERSION_MISMATCH")
    return version, candidate, binding, identity


def _write_json_atomic(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    try:
        temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporary.replace(path)
    finally:
        if temporary.exists():
            try:
                temporary.unlink()
            except OSError:
                pass


def build_pin(
    *,
    project_root: Path,
    metadata_root: Path,
    artifact_sha256: str,
    installation_mode: str,
    rollback_source: str,
    managed_files: Iterable[str],
    doctor_result: str = "HEALTHY",
) -> dict[str, Any]:
    """Build one canonical pin from packaged candidate metadata."""

    artifact_sha = _require_hex(artifact_sha256, "CANDIDATE_ARTIFACT_SHA256", HEX64)
    version, candidate, binding, _identity = _candidate_metadata(metadata_root)
    mode = _require_text(installation_mode, "INSTALLATION_MODE")
    rollback = _require_text(rollback_source, "ROLLBACK_SOURCE")
    if doctor_result not in {"HEALTHY", "UNHEALTHY", "EXECUTION_FAILED"}:
        raise ProjectPinError("DOCTOR_RESULT_INVALID")
    files = sorted({_require_text(item, "MANAGED_FILE") for item in managed_files})
    baseline_version = _require_text(candidate.get("official_baseline_version"), "OFFICIAL_BASELINE_VERSION")
    if baseline_version == version:
        raise ProjectPinError("CANDIDATE_EQUALS_OFFICIAL_BASELINE")
    return {
        "schema": PROJECT_PIN_SCHEMA,
        "project_fingerprint": project_fingerprint(project_root),
        "p2p_official_baseline_version": baseline_version,
        "p2p_official_baseline_sha256": _require_hex(candidate.get("official_baseline_sha256"), "OFFICIAL_BASELINE_SHA256", HEX64),
        "p2p_candidate_version": version,
        "p2p_candidate_artifact_sha256": artifact_sha,
        "install_timestamp_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "installation_mode": mode,
        "permission_envelope": {
            "file_read": "PROJECT_ROOT",
            "file_write": "PROJECT_LOCAL_P2P_STATE",
            "network": "EXECUTION_TARGET_ONLY",
        },
        "execution_target_requirements": {"min_roles": 8, "certified_only": True},
        "rollback_source": rollback,
        "managed_files": files,
        "candidate_vs_official": "UNPROMOTED_SUCCESSOR_CANDIDATE",
        "source_commit": binding["source_commit"],
        "source_tree": binding["source_tree"],
        "source_binding_status": "VERIFIED",
        "doctor_result": doctor_result,
        "verification_status": "VERIFIED" if doctor_result == "HEALTHY" else "INSTALLED_UNVERIFIED",
        "producer": "scripts/p2p_safe_installer.py -> p2p_capabilities.project_pin",
    }


def build_projection_pin(
    *,
    project_root: Path,
    project_id: str,
    source_repository: str,
    source_commit: str,
    source_tree: str,
    selected_capabilities: Iterable[Mapping[str, Any]],
    projection_plan: Any,
    managed_files: Iterable[Mapping[str, Any]] | None = None,
    policy_path: Path | None = None,
    context_path: Path | None = None,
    project_name: str | None = None,
    project_version: str | None = None,
) -> dict[str, Any]:
    """Build a truthful v2 ``PROJECTION_ONLY`` pin after materialization."""

    root = project_root.resolve()
    if not root.is_dir():
        raise ProjectPinError("PROJECT_ROOT_NOT_FOUND")
    source, capabilities, plan = _validate_projection_request(
        source_repository=source_repository,
        source_commit=source_commit,
        source_tree=source_tree,
        selected_capabilities=selected_capabilities,
        projection_plan=projection_plan,
    )
    if managed_files is None:
        default_records: list[dict[str, Any]] = []
        for item in plan["files"]:
            relative = _canonical_relative(item.get("relative_target"), "PLAN_TARGET_PATH")
            _normal, target = _projected_path(root, relative, "MANAGED_FILE_PATH")
            default_records.append(
                {
                    "relative_path": relative,
                    "ownership": PROJECTED_FILE_OWNERSHIP,
                    "content_sha256": _require_hex(item.get("content_hash"), "PLAN_CONTENT_HASH", HEX64),
                    "previous_state": {"state": "ABSENT"},
                }
            )
            if not target.is_file():
                raise ProjectPinError("MANAGED_FILE_MISSING_OR_LINK")
        managed_files = default_records
    records = _normalise_managed_files(root, plan, managed_files)
    policy = _surface_binding(
        root,
        policy_path,
        ".p2p/project-policy.json",
        "POLICY_BINDING",
        "p2p-codex-project-policy/1",
    )
    context = _surface_binding(
        root,
        context_path,
        ".p2p/context/project_map.json",
        "CONTEXT_BINDING",
        "p2p-project-map/3",
    )
    identity_name = _require_text(project_name or root.name, "PROJECT_NAME")
    pin: dict[str, Any] = {
        "schema": PROJECT_PIN_V2_SCHEMA,
        "mode": PROJECTION_ONLY,
        "project_id": _project_identifier(project_id),
        "project_name": identity_name,
        "project_fingerprint": project_fingerprint(root),
        "source_binding": source,
        "selected_capabilities": capabilities,
        "projection": {
            "schema": PROJECTION_BINDING_SCHEMA,
            "materialization_version": PROJECTION_MATERIALIZATION_VERSION,
            "host_kind": plan["host_kind"],
            "plan_sha256": _bytes_sha256(canonical_json(plan).encode("utf-8")),
            "plan_snapshot": plan,
            "managed_files": records,
        },
        "runtime_claim": {"installed": False, "status": "NOT_INSTALLED"},
        "rollback": {"scope": "PROJECTED_FILES_ONLY", "prior_state_recorded": True},
        "verification_status": "VERIFIED",
        "producer": "p2p_capabilities.project_pin",
    }
    if project_version is not None:
        pin["project_version"] = _require_text(project_version, "PROJECT_VERSION")
    if policy is not None:
        pin["projection"]["policy_binding"] = policy
    if context is not None:
        pin["projection"]["context_binding"] = context
    _validate_projection_pin(root, pin)
    return pin


def write_pin(project_root: Path, pin: dict[str, Any]) -> Path:
    if not isinstance(pin, dict) or pin.get("schema") not in PROJECT_PIN_SCHEMAS:
        raise ProjectPinError("PROJECT_PIN_SCHEMA_INVALID")
    if pin.get("schema") == PROJECT_PIN_V2_SCHEMA and pin.get("mode") not in PROJECT_PIN_MODES:
        raise ProjectPinError("PROJECT_PIN_MODE_INVALID")
    if pin.get("schema") == PROJECT_PIN_SCHEMA and pin.get("mode") not in {None, PACKAGED_RUNTIME}:
        raise ProjectPinError("PROJECT_PIN_V1_MODE_INVALID")
    root = project_root.resolve()
    path = root / ".p2p" / "project-pin.json"
    _assert_no_link_components(root, path, "PROJECT_PIN")
    if pin.get("schema") == PROJECT_PIN_V2_SCHEMA and pin.get("mode") == PROJECTION_ONLY:
        _validate_projection_pin(root, pin)
    _write_json_atomic(path, pin)
    return path


def _validate_packaged_pin(
    root: Path,
    pin: Mapping[str, Any],
    *,
    metadata_root: Path,
    expected_artifact_sha256: str | None,
    expected_version: str | None,
) -> dict[str, Any]:
    if pin.get("schema") == PROJECT_PIN_V2_SCHEMA and pin.get("mode") != PACKAGED_RUNTIME:
        raise ProjectPinError("PROJECT_PIN_MODE_INVALID")
    if pin.get("verification_status") != "VERIFIED":
        raise ProjectPinError("PROJECT_PIN_NOT_VERIFIED")
    if pin.get("doctor_result") != "HEALTHY":
        raise ProjectPinError("PROJECT_PIN_DOCTOR_NOT_HEALTHY")
    version, candidate, binding, _identity = _candidate_metadata(metadata_root)
    if expected_version is not None and version != _require_text(expected_version, "EXPECTED_VERSION"):
        raise ProjectPinError("PROJECT_PIN_VERSION_MISMATCH")
    if pin.get("p2p_candidate_version") != version:
        raise ProjectPinError("PROJECT_PIN_CANDIDATE_VERSION_MISMATCH")
    pin_artifact = _require_hex(pin.get("p2p_candidate_artifact_sha256"), "PIN_ARTIFACT_SHA256", HEX64)
    if expected_artifact_sha256 is not None and pin_artifact != _require_hex(expected_artifact_sha256, "EXPECTED_ARTIFACT_SHA256", HEX64):
        raise ProjectPinError("PROJECT_PIN_ARTIFACT_SHA256_MISMATCH")
    marker_path = root / ".p2p" / "system" / "release.json"
    if marker_path.is_file():
        marker = _read_json(marker_path, "RELEASE_MARKER")
        marker_sha = marker.get("artifact_sha256")
        if marker_sha is not None and pin_artifact != _require_hex(marker_sha, "RELEASE_MARKER_ARTIFACT_SHA256", HEX64):
            raise ProjectPinError("PROJECT_PIN_RELEASE_MARKER_SHA256_MISMATCH")
        marker_version = marker.get("candidate_version") or marker.get("package_version")
        if marker_version is not None and marker_version != version:
            raise ProjectPinError("PROJECT_PIN_RELEASE_MARKER_VERSION_MISMATCH")
    if pin.get("p2p_official_baseline_version") != candidate.get("official_baseline_version"):
        raise ProjectPinError("PROJECT_PIN_OFFICIAL_VERSION_MISMATCH")
    if pin.get("p2p_official_baseline_sha256") != candidate.get("official_baseline_sha256"):
        raise ProjectPinError("PROJECT_PIN_OFFICIAL_SHA256_MISMATCH")
    _require_hex(pin.get("project_fingerprint"), "PROJECT_FINGERPRINT", HEX64)
    if pin["project_fingerprint"] != project_fingerprint(root):
        raise ProjectPinError("PROJECT_PIN_PROJECT_FINGERPRINT_MISMATCH")
    if pin.get("candidate_vs_official") != "UNPROMOTED_SUCCESSOR_CANDIDATE":
        raise ProjectPinError("PROJECT_PIN_PROMOTION_STATE_INVALID")
    if pin.get("source_commit") != binding.get("source_commit") or pin.get("source_tree") != binding.get("source_tree"):
        raise ProjectPinError("PROJECT_PIN_SOURCE_BINDING_MISMATCH")
    if pin.get("source_binding_status") != "VERIFIED":
        raise ProjectPinError("PROJECT_PIN_SOURCE_BINDING_UNVERIFIED")
    envelope = pin.get("permission_envelope")
    if envelope != {"file_read": "PROJECT_ROOT", "file_write": "PROJECT_LOCAL_P2P_STATE", "network": "EXECUTION_TARGET_ONLY"}:
        raise ProjectPinError("PROJECT_PIN_PERMISSION_ENVELOPE_INVALID")
    _require_text(pin.get("installation_mode"), "INSTALLATION_MODE")
    _require_text(pin.get("rollback_source"), "ROLLBACK_SOURCE")
    if not isinstance(pin.get("managed_files"), list):
        raise ProjectPinError("PROJECT_PIN_MANAGED_FILES_INVALID")
    return {
        "status": "PASS",
        "schema": pin.get("schema"),
        "mode": PACKAGED_RUNTIME if pin.get("schema") == PROJECT_PIN_V2_SCHEMA else None,
        "candidate_version": version,
        "artifact_sha256": pin_artifact,
        "project_fingerprint": pin["project_fingerprint"],
        "source_commit": binding["source_commit"],
        "source_tree": binding["source_tree"],
        "verification_status": pin["verification_status"],
        "doctor_result": pin["doctor_result"],
    }


def _validate_projection_pin(
    root: Path,
    pin: Mapping[str, Any],
    *,
    expected_source_repository: str | None = None,
    expected_source_commit: str | None = None,
    expected_source_tree: str | None = None,
    expected_plan_sha256: str | None = None,
) -> dict[str, Any]:
    if pin.get("schema") != PROJECT_PIN_V2_SCHEMA:
        raise ProjectPinError("PROJECT_PIN_SCHEMA_INVALID")
    if pin.get("mode") != PROJECTION_ONLY:
        raise ProjectPinError("PROJECT_PIN_MODE_INVALID")
    if pin.get("verification_status") != "VERIFIED":
        raise ProjectPinError("PROJECT_PIN_NOT_VERIFIED")
    _reject_secret_fields(pin, "PROJECT_PIN")
    unexpected_pin_fields = set(pin).difference(_PROJECTION_PIN_KEYS)
    if unexpected_pin_fields:
        raise ProjectPinError(
            f"PROJECT_PIN_V2_FIELD_FORBIDDEN:{next(iter(unexpected_pin_fields))}"
        )
    forbidden = {
        "p2p_official_baseline_version",
        "p2p_official_baseline_sha256",
        "p2p_candidate_version",
        "p2p_candidate_artifact_sha256",
        "install_timestamp_utc",
        "installation_mode",
        "permission_envelope",
        "execution_target_requirements",
        "rollback_source",
        "candidate_vs_official",
        "doctor_result",
    }
    present = forbidden.intersection(pin.keys())
    if present:
        raise ProjectPinError(f"PROJECT_PIN_PACKAGED_FIELD_FORBIDDEN:{sorted(present)[0]}")
    if (root / ".p2p" / "system").exists() or (root / ".p2p" / "system").is_symlink():
        raise ProjectPinError("PROJECT_PIN_PROJECTION_RUNTIME_PRESENT")
    _project_identifier(pin.get("project_id"))
    _require_text(pin.get("project_name"), "PROJECT_NAME")
    if "project_version" in pin:
        _require_text(pin.get("project_version"), "PROJECT_VERSION")
    fingerprint = _require_hex(pin.get("project_fingerprint"), "PROJECT_FINGERPRINT", HEX64)
    if fingerprint != project_fingerprint(root):
        raise ProjectPinError("PROJECT_PIN_PROJECT_FINGERPRINT_MISMATCH")
    source = pin.get("source_binding")
    if not isinstance(source, Mapping) or source.get("schema") != PROJECT_SOURCE_BINDING_SCHEMA or source.get("status") != "VERIFIED":
        raise ProjectPinError("PROJECT_PIN_SOURCE_BINDING_INVALID")
    source_values = _source_binding(source.get("repository"), source.get("commit"), source.get("tree"))
    if source_values != dict(source):
        raise ProjectPinError("PROJECT_PIN_SOURCE_BINDING_NONCANONICAL")
    if expected_source_repository is not None and source_values["repository"] != _require_text(expected_source_repository, "EXPECTED_SOURCE_REPOSITORY"):
        raise ProjectPinError("PROJECT_PIN_SOURCE_REPOSITORY_MISMATCH")
    if expected_source_commit is not None and source_values["commit"] != _require_hex(expected_source_commit, "EXPECTED_SOURCE_COMMIT", HEX40):
        raise ProjectPinError("PROJECT_PIN_SOURCE_COMMIT_MISMATCH")
    if expected_source_tree is not None and source_values["tree"] != _require_hex(expected_source_tree, "EXPECTED_SOURCE_TREE", HEX40):
        raise ProjectPinError("PROJECT_PIN_SOURCE_TREE_MISMATCH")
    capabilities = _normalise_capabilities(pin.get("selected_capabilities", []))
    projection = pin.get("projection")
    if not isinstance(projection, Mapping):
        raise ProjectPinError("PROJECT_PIN_PROJECTION_INVALID")
    unexpected_projection_fields = set(projection).difference(_PROJECTION_BINDING_KEYS)
    if unexpected_projection_fields:
        raise ProjectPinError(
            f"PROJECT_PIN_PROJECTION_FIELD_FORBIDDEN:{next(iter(unexpected_projection_fields))}"
        )
    if projection.get("schema") != PROJECTION_BINDING_SCHEMA:
        raise ProjectPinError("PROJECT_PIN_PROJECTION_SCHEMA_INVALID")
    if projection.get("materialization_version") != PROJECTION_MATERIALIZATION_VERSION:
        raise ProjectPinError("PROJECT_PIN_MATERIALIZATION_VERSION_INVALID")
    plan = _validate_plan(projection.get("plan_snapshot"))
    plan_hash = _require_hex(projection.get("plan_sha256"), "PLAN_SHA256", HEX64)
    actual_plan_hash = _bytes_sha256(canonical_json(plan).encode("utf-8"))
    if plan_hash != actual_plan_hash:
        raise ProjectPinError("PROJECT_PIN_PLAN_SHA256_MISMATCH")
    if expected_plan_sha256 is not None and plan_hash != _require_hex(expected_plan_sha256, "EXPECTED_PLAN_SHA256", HEX64):
        raise ProjectPinError("PROJECT_PIN_PLAN_SHA256_MISMATCH")
    if projection.get("host_kind") != plan.get("host_kind"):
        raise ProjectPinError("PROJECT_PIN_HOST_KIND_MISMATCH")
    selected = {item["capability_id"]: item for item in capabilities}
    capability_id = plan["capability_id"]
    if capability_id not in selected:
        raise ProjectPinError("PLAN_CAPABILITY_NOT_SELECTED")
    if plan["source_hash"].lower() != selected[capability_id]["source_hash"] or plan["entrypoint_hash"].lower() != selected[capability_id]["entrypoint_hash"]:
        raise ProjectPinError("PLAN_CAPABILITY_HASH_MISMATCH")
    records = _normalise_managed_files(root, plan, projection.get("managed_files", []))
    for key, expected_relative, label, expected_schema in (
        ("policy_binding", ".p2p/project-policy.json", "POLICY_BINDING", "p2p-codex-project-policy/1"),
        ("context_binding", ".p2p/context/project_map.json", "CONTEXT_BINDING", "p2p-project-map/3"),
    ):
        if key in projection:
            _validate_surface_binding(root, projection[key], expected_relative, label, expected_schema)
    if pin.get("runtime_claim") != {"installed": False, "status": "NOT_INSTALLED"}:
        raise ProjectPinError("PROJECT_PIN_RUNTIME_CLAIM_INVALID")
    if pin.get("rollback") != {"scope": "PROJECTED_FILES_ONLY", "prior_state_recorded": True}:
        raise ProjectPinError("PROJECT_PIN_ROLLBACK_INVALID")
    return {
        "status": "PASS",
        "schema": PROJECT_PIN_V2_SCHEMA,
        "mode": PROJECTION_ONLY,
        "project_id": pin["project_id"],
        "project_name": pin["project_name"],
        "project_fingerprint": fingerprint,
        "source_repository": source_values["repository"],
        "source_commit": source_values["commit"],
        "source_tree": source_values["tree"],
        "plan_sha256": plan_hash,
        "managed_file_count": len(records),
        "verification_status": pin["verification_status"],
        "runtime_installed": False,
    }


def validate_pin(
    project_root: Path,
    *,
    metadata_root: Path | None = None,
    expected_artifact_sha256: str | None = None,
    expected_version: str | None = None,
    expected_source_repository: str | None = None,
    expected_source_commit: str | None = None,
    expected_source_tree: str | None = None,
    expected_plan_sha256: str | None = None,
) -> dict[str, Any]:
    """Validate either the legacy packaged pin or the explicit v2 branch."""

    root = project_root.resolve()
    pin_path = root / ".p2p" / "project-pin.json"
    _assert_no_link_components(root, pin_path, "PROJECT_PIN")
    pin = _read_json(pin_path, "PROJECT_PIN")
    schema = pin.get("schema")
    if schema == PROJECT_PIN_SCHEMA:
        if pin.get("mode") not in {None, PACKAGED_RUNTIME}:
            raise ProjectPinError("PROJECT_PIN_V1_MODE_INVALID")
        return _validate_packaged_pin(
            root,
            pin,
            metadata_root=metadata_root or (root / ".p2p" / "system"),
            expected_artifact_sha256=expected_artifact_sha256,
            expected_version=expected_version,
        )
    if schema == PROJECT_PIN_V2_SCHEMA:
        if pin.get("mode") == PACKAGED_RUNTIME:
            return _validate_packaged_pin(
                root,
                pin,
                metadata_root=metadata_root or (root / ".p2p" / "system"),
                expected_artifact_sha256=expected_artifact_sha256,
                expected_version=expected_version,
            )
        if pin.get("mode") == PROJECTION_ONLY:
            return _validate_projection_pin(
                root,
                pin,
                expected_source_repository=expected_source_repository,
                expected_source_commit=expected_source_commit,
                expected_source_tree=expected_source_tree,
                expected_plan_sha256=expected_plan_sha256,
            )
        raise ProjectPinError("PROJECT_PIN_MODE_INVALID")
    raise ProjectPinError("PROJECT_PIN_SCHEMA_INVALID")


__all__ = [
    "PACKAGED_RUNTIME",
    "PROJECT_PIN_MODES",
    "PROJECT_PIN_SCHEMA",
    "PROJECT_PIN_V2_SCHEMA",
    "PROJECT_PIN_SCHEMAS",
    "PROJECTION_BINDING_SCHEMA",
    "PROJECTION_ONLY",
    "PROJECTION_MATERIALIZATION_VERSION",
    "PROJECTED_FILE_OWNERSHIP",
    "ProjectPinError",
    "build_pin",
    "build_projection_pin",
    "canonical_json",
    "project_fingerprint",
    "validate_projection_request",
    "validate_pin",
    "write_pin",
]
