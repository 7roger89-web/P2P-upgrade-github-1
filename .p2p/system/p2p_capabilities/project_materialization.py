"""Bounded materialization of an already-validated host projection plan.

This module is intentionally a writer seam, not a router, installer, or
runtime bootstrapper.  It writes only declared project-local host files and
finalizes the v2 projection pin after all writes and bindings validate.
"""

from __future__ import annotations

import json
import hashlib
import os
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping

from .project_pin import (
    PROJECT_PIN_V2_SCHEMA,
    PROJECTION_ONLY,
    PROJECTED_FILE_OWNERSHIP,
    ProjectPinError,
    _assert_no_link_components,
    _canonical_relative,
    _is_reparse_or_symlink,
    _sha256,
    build_projection_pin,
    canonical_json,
    validate_pin,
    validate_projection_request,
    write_pin,
)


MATERIALIZATION_RESULT_SCHEMA = "p2p-project-materialization-result/1"
_PROJECTED_ROOTS = {".agents", ".claude", ".gemini", ".cursor", ".github"}


class ProjectionMaterializationError(ProjectPinError):
    """Raised when a projection cannot be safely materialized or recovered."""


def _target_path(root: Path, value: Any, label: str = "MATERIALIZATION_PATH") -> tuple[str, Path]:
    relative = _canonical_relative(value, label)
    if PurePosixPath(relative).parts[0] not in _PROJECTED_ROOTS:
        raise ProjectionMaterializationError(f"{label}_UNAPPROVED_ROOT")
    target = root / Path(*PurePosixPath(relative).parts)
    _assert_no_link_components(root, target, label)
    return relative, target


def _content_bytes(value: Any) -> bytes:
    if isinstance(value, bytes):
        return value
    if isinstance(value, str):
        return value.encode("utf-8")
    if isinstance(value, Mapping) and "content" in value:
        return _content_bytes(value["content"])
    raise ProjectionMaterializationError("MATERIALIZATION_CONTENT_UNAVAILABLE")


def _plan_files(root: Path, plan: Mapping[str, Any]) -> list[dict[str, Any]]:
    files = plan.get("files")
    if not isinstance(files, list) or not files:
        raise ProjectionMaterializationError("MATERIALIZATION_PLAN_FILES_INVALID")
    result: list[dict[str, Any]] = []
    for item in files:
        if not isinstance(item, Mapping):
            raise ProjectionMaterializationError("MATERIALIZATION_PLAN_FILE_INVALID")
        relative, target = _target_path(root, item.get("relative_target"), "MATERIALIZATION_PATH")
        content = _content_bytes(item.get("content_or_template"))
        expected_hash = str(item.get("content_hash", "")).lower()
        actual_hash = hashlib.sha256(content).hexdigest()
        if actual_hash != expected_hash:
            raise ProjectionMaterializationError("MATERIALIZATION_PLAN_CONTENT_HASH_MISMATCH")
        if item.get("ownership_class") != "P2P_PROJECT_MANAGED":
            raise ProjectionMaterializationError("MATERIALIZATION_PLAN_OWNERSHIP_INVALID")
        result.append(
            {
                "relative_path": relative,
                "target": target,
                "content": content,
                "content_sha256": actual_hash,
            }
        )
    return result


def _read_existing_pin(root: Path) -> tuple[dict[str, Any] | None, bytes | None]:
    path = root / ".p2p" / "project-pin.json"
    try:
        _assert_no_link_components(root, path, "EXISTING_PIN")
    except ProjectPinError as exc:
        raise ProjectionMaterializationError(str(exc)) from exc
    if not path.exists() and not path.is_symlink():
        return None, None
    if _is_reparse_or_symlink(path) or not path.is_file():
        raise ProjectionMaterializationError("EXISTING_PIN_LINK_OR_INVALID")
    try:
        raw = path.read_bytes()
        value = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ProjectionMaterializationError(f"EXISTING_PIN_UNREADABLE:{exc}") from exc
    if not isinstance(value, dict) or value.get("schema") != PROJECT_PIN_V2_SCHEMA or value.get("mode") != PROJECTION_ONLY:
        raise ProjectionMaterializationError("EXISTING_PIN_NOT_PROJECTION_ONLY")
    try:
        validate_pin(root)
    except ProjectPinError as exc:
        raise ProjectionMaterializationError(f"EXISTING_PIN_INVALID:{exc}") from exc
    return value, raw


def _previous_records(previous_pin: Mapping[str, Any] | None) -> dict[str, Mapping[str, Any]]:
    if previous_pin is None:
        return {}
    projection = previous_pin.get("projection")
    records = projection.get("managed_files") if isinstance(projection, Mapping) else None
    if not isinstance(records, list):
        raise ProjectionMaterializationError("EXISTING_PIN_MANAGED_FILES_INVALID")
    result: dict[str, Mapping[str, Any]] = {}
    for record in records:
        if not isinstance(record, Mapping):
            raise ProjectionMaterializationError("EXISTING_PIN_MANAGED_FILE_INVALID")
        relative = str(record.get("relative_path", ""))
        if relative in result:
            raise ProjectionMaterializationError("EXISTING_PIN_MANAGED_FILE_DUPLICATE")
        result[relative] = record
    return result


def _check_parent_components(root: Path, target: Path) -> None:
    try:
        relative = target.absolute().relative_to(root.resolve())
    except ValueError as exc:
        raise ProjectionMaterializationError("MATERIALIZATION_PATH_OUTSIDE_ROOT") from exc
    current = root.resolve()
    for component in relative.parts[:-1]:
        current = current / component
        if _is_reparse_or_symlink(current):
            raise ProjectionMaterializationError("MATERIALIZATION_PARENT_SYMLINK_ESCAPE")
        if current.exists() and not current.is_dir():
            raise ProjectionMaterializationError("MATERIALIZATION_PARENT_NOT_DIRECTORY")


def _preflight(
    root: Path,
    plan_files: Iterable[Mapping[str, Any]],
    previous: Mapping[str, Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    operations: list[dict[str, Any]] = []
    declared: set[str] = set()
    for item in plan_files:
        relative = str(item["relative_path"])
        target = item["target"]
        declared.add(relative)
        _check_parent_components(root, target)
        if _is_reparse_or_symlink(target):
            raise ProjectionMaterializationError("MATERIALIZATION_TARGET_SYMLINK_ESCAPE")
        prior = previous.get(relative)
        exists = target.exists()
        if exists and not target.is_file():
            raise ProjectionMaterializationError("MATERIALIZATION_UNMANAGED_COLLISION")
        current_bytes: bytes | None = None
        current_hash: str | None = None
        if exists:
            try:
                current_bytes = target.read_bytes()
            except OSError as exc:
                raise ProjectionMaterializationError(f"MATERIALIZATION_TARGET_UNREADABLE:{exc}") from exc
            current_hash = _sha256(target)
        desired = item["content"]
        desired_hash = item["content_sha256"]
        if exists:
            if current_hash == desired_hash:
                if prior is not None:
                    if prior.get("ownership") != PROJECTED_FILE_OWNERSHIP or str(prior.get("content_sha256", "")).lower() != current_hash:
                        raise ProjectionMaterializationError("MATERIALIZATION_PREVIOUS_OWNERSHIP_MISMATCH")
                    previous_state = dict(prior.get("previous_state", {}))
                else:
                    previous_state = {"state": "PRESENT", "content_sha256": current_hash}
                needs_write = False
            else:
                if prior is None:
                    raise ProjectionMaterializationError("MATERIALIZATION_UNMANAGED_COLLISION")
                if prior.get("ownership") != PROJECTED_FILE_OWNERSHIP or str(prior.get("content_sha256", "")).lower() != current_hash:
                    raise ProjectionMaterializationError("MATERIALIZATION_TAMPERED_MANAGED_FILE")
                previous_state = {"state": "PRESENT", "content_sha256": current_hash}
                needs_write = True
        else:
            if prior is not None:
                raise ProjectionMaterializationError("MATERIALIZATION_MANAGED_FILE_MISSING")
            previous_state = {"state": "ABSENT"}
            needs_write = True
        operations.append(
            {
                "relative_path": relative,
                "target": target,
                "content": desired,
                "content_sha256": desired_hash,
                "previous_state": previous_state,
                "before_exists": exists,
                "before_bytes": current_bytes,
                "needs_write": needs_write,
            }
        )
    dropped = sorted(set(previous) - declared)
    if dropped:
        raise ProjectionMaterializationError(f"MATERIALIZATION_OWNERSHIP_DROPPED:{dropped[0]}")
    records = [
        {
            "relative_path": item["relative_path"],
            "ownership": PROJECTED_FILE_OWNERSHIP,
            "content_sha256": item["content_sha256"],
            "previous_state": item["previous_state"],
        }
        for item in operations
    ]
    return operations, records


def _ensure_parent_dirs(root: Path, target: Path) -> list[Path]:
    relative = target.absolute().relative_to(root.resolve())
    current = root.resolve()
    created: list[Path] = []
    for component in relative.parts[:-1]:
        current = current / component
        if _is_reparse_or_symlink(current):
            raise ProjectionMaterializationError("MATERIALIZATION_PARENT_SYMLINK_ESCAPE")
        if current.exists():
            if not current.is_dir():
                raise ProjectionMaterializationError("MATERIALIZATION_PARENT_NOT_DIRECTORY")
        else:
            current.mkdir()
            created.append(current)
    _assert_no_link_components(root, target, "MATERIALIZATION_PATH")
    return created


def _atomic_write(path: Path, content: bytes) -> None:
    """Write exact bytes through a same-directory replace."""

    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.p2p-",
        suffix=".tmp",
        dir=str(path.parent),
    )
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
    finally:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass


def _rollback_files(changed: list[dict[str, Any]], created_dirs: list[Path]) -> None:
    for operation in reversed(changed):
        target = operation["target"]
        if _is_reparse_or_symlink(target):
            raise ProjectionMaterializationError("MATERIALIZATION_ROLLBACK_SYMLINK_BLOCKED")
        if not target.is_file() or _sha256(target) != operation["content_sha256"]:
            raise ProjectionMaterializationError("MATERIALIZATION_ROLLBACK_STATE_CHANGED")
        if operation["before_exists"]:
            before = operation["before_bytes"]
            if not isinstance(before, bytes):
                raise ProjectionMaterializationError("MATERIALIZATION_ROLLBACK_BYTES_MISSING")
            _atomic_write(target, before)
        else:
            target.unlink()
    for directory in reversed(created_dirs):
        if _is_reparse_or_symlink(directory):
            continue
        try:
            directory.rmdir()
        except OSError:
            pass


def _restore_pin(path: Path, before: bytes | None, expected_new: bytes | None) -> None:
    if not path.exists() and not path.is_symlink():
        if before is None:
            return
        raise ProjectionMaterializationError("MATERIALIZATION_PIN_ROLLBACK_MISSING")
    if _is_reparse_or_symlink(path):
        raise ProjectionMaterializationError("MATERIALIZATION_PIN_ROLLBACK_SYMLINK_BLOCKED")
    current = path.read_bytes()
    if expected_new is not None and current != expected_new:
        raise ProjectionMaterializationError("MATERIALIZATION_PIN_STATE_CHANGED")
    if before is None:
        path.unlink()
    else:
        _atomic_write(path, before)


def materialize_projection(
    *,
    project_root: Path,
    project_id: str,
    source_repository: str,
    source_commit: str,
    source_tree: str,
    selected_capabilities: Iterable[Mapping[str, Any]],
    projection_plan: Any,
    policy_path: Path | None = None,
    context_path: Path | None = None,
    project_name: str | None = None,
    project_version: str | None = None,
    previous_pin: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Materialize one READY host plan and write its v2 pin last."""

    root = project_root.resolve()
    if not root.is_dir():
        raise ProjectionMaterializationError("PROJECT_ROOT_NOT_FOUND")
    request = validate_projection_request(
        source_repository=source_repository,
        source_commit=source_commit,
        source_tree=source_tree,
        selected_capabilities=selected_capabilities,
        projection_plan=projection_plan,
    )
    plan = request["plan"]
    existing, pin_before = _read_existing_pin(root)
    if previous_pin is not None:
        if existing is None or canonical_json(dict(previous_pin)) != canonical_json(existing):
            raise ProjectionMaterializationError("PREVIOUS_PIN_MISMATCH")
        previous = dict(previous_pin)
    else:
        previous = existing
    if existing is not None:
        if project_id != existing.get("project_id"):
            raise ProjectionMaterializationError("PROJECT_ID_IMMUTABLE")
        prior_projection = existing.get("projection", {})
        if policy_path is None and isinstance(prior_projection, Mapping) and "policy_binding" in prior_projection:
            policy_path = root / str(prior_projection["policy_binding"].get("relative_path", ""))
        if context_path is None and isinstance(prior_projection, Mapping) and "context_binding" in prior_projection:
            context_path = root / str(prior_projection["context_binding"].get("relative_path", ""))
    previous_records = _previous_records(previous)
    plan_items = _plan_files(root, plan)
    operations, managed_records = _preflight(root, plan_items, previous_records)
    pin_path = root / ".p2p" / "project-pin.json"
    changed: list[dict[str, Any]] = []
    created_dirs: list[Path] = []
    pin_expected: bytes | None = None
    pin_written = False
    try:
        for operation in operations:
            if not operation["needs_write"]:
                continue
            created_dirs.extend(_ensure_parent_dirs(root, operation["target"]))
            _atomic_write(operation["target"], operation["content"])
            changed.append(operation)
        for operation in operations:
            target = operation["target"]
            if not target.is_file() or _sha256(target) != operation["content_sha256"]:
                raise ProjectionMaterializationError("MATERIALIZATION_POSTWRITE_HASH_MISMATCH")
        pin = build_projection_pin(
            project_root=root,
            project_id=project_id,
            source_repository=source_repository,
            source_commit=source_commit,
            source_tree=source_tree,
            selected_capabilities=request["selected_capabilities"],
            projection_plan=plan,
            managed_files=managed_records,
            policy_path=policy_path,
            context_path=context_path,
            project_name=project_name,
            project_version=project_version,
        )
        pin_expected = (json.dumps(pin, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        if existing is None or canonical_json(pin) != canonical_json(existing):
            if existing is None and pin_path.exists():
                raise ProjectionMaterializationError("MATERIALIZATION_PIN_COLLISION")
            write_pin(root, pin)
            pin_written = True
        validate_pin(
            root,
            expected_source_repository=source_repository,
            expected_source_commit=source_commit,
            expected_source_tree=source_tree,
            expected_plan_sha256=pin["projection"]["plan_sha256"],
        )
        return {
            "schema": MATERIALIZATION_RESULT_SCHEMA,
            "status": "PASS",
            "mode": PROJECTION_ONLY,
            "host_kind": plan["host_kind"],
            "capability_id": plan["capability_id"],
            "plan_sha256": pin["projection"]["plan_sha256"],
            "managed_files": managed_records,
            "changed_files": len(changed),
            "idempotent": not changed,
            "rollback_status": "READY_FOR_PROJECTION_ROLLBACK",
            "pin_finalized": True,
        }
    except Exception as exc:
        rollback_errors: list[str] = []
        if pin_written or (pin_expected is not None and pin_path.exists() and pin_before is None):
            try:
                _restore_pin(pin_path, pin_before, pin_expected)
            except ProjectionMaterializationError as rollback_exc:
                rollback_errors.append(str(rollback_exc))
        try:
            _rollback_files(changed, created_dirs)
        except ProjectionMaterializationError as rollback_exc:
            rollback_errors.append(str(rollback_exc))
        suffix = f"; rollback={','.join(rollback_errors)}" if rollback_errors else "; rollback=PASS"
        if isinstance(exc, ProjectionMaterializationError):
            raise ProjectionMaterializationError(f"{exc}{suffix}") from exc
        if isinstance(exc, ProjectPinError):
            raise ProjectionMaterializationError(f"{exc}{suffix}") from exc
        raise ProjectionMaterializationError(f"MATERIALIZATION_FAILED:{exc}{suffix}") from exc


__all__ = [
    "MATERIALIZATION_RESULT_SCHEMA",
    "ProjectionMaterializationError",
    "materialize_projection",
]
