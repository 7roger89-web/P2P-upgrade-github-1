#!/usr/bin/env python3
"""Portable, beginner-safe P2P bootstrap adapter.

This module is intentionally a thin boundary around the existing project
workflow.  It discovers a source package or a fully marked installed runtime,
preflights the existing project state, and then delegates Goal/Task/ledger,
Control Tower, and Beginner Gateway work to ``p2p_workflow``.  It never copies
runtime files, starts a host, grants permission, or performs a protected
release/promotion/deployment action.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping


SCHEMA = "p2p-portable-bootstrap/1"
STATUS_READY = "READY"
STATUS_NEEDS_DECISION = "NEEDS USER DECISION"
STATUS_BLOCKED = "BLOCKED"
DEFAULT_REQUEST = "Start P2P safely for this project."

SOURCE_MANIFEST_SCHEMA = "p2p-codex-project-bundle/1"
SYSTEM_MANIFEST_SCHEMA = "p2p-capability-manifest/1"
INSTALL_MANIFEST_SCHEMA = "p2p-install-manifest/1"
RELEASE_SCHEMA = "p2p-install-release/1"
GOAL_SCHEMA = "p2p-goal-contract/1"
BEGINNER_GATEWAY_SCHEMA = "p2p-beginner-gateway/1"
BEGINNER_MODE = "BEGINNER"

SOURCE_REQUIRED_FILES = (
    "scripts/p2p_bootstrap.py",
    "scripts/p2p_workflow.py",
    "scripts/p2p_eval.py",
    ".p2p/system/p2p_capabilities/beginner_gateway.py",
    ".p2p/system/p2p_capabilities/task_state.py",
    ".p2p/system/p2p_capabilities/control_tower_handoff.py",
    ".p2p/system/p2p_capabilities/orchestration_policy.py",
    "governance/fact-ledger.json",
    "governance/live-specs.json",
    "governance/project-policy.template.json",
)

INSTALLED_REQUIRED_FILES = (
    "VERSION",
    "p2p_capabilities/beginner_gateway.py",
    "p2p_capabilities/task_state.py",
    "p2p_capabilities/control_tower_handoff.py",
    "p2p_capabilities/orchestration_policy.py",
    "scripts/p2p_eval.py",
    "scripts/p2p_bootstrap.py",
    "governance/fact-ledger.json",
    "governance/live-specs.json",
)

OPTIONAL_PROJECT_JSON = (
    ".p2p/project-policy.json",
    ".p2p/project-profile.json",
    ".p2p/state/project-status.json",
    ".p2p/state/trusted-evidence.json",
    ".p2p/evals/suite.json",
)


class BootstrapFailure(ValueError):
    """A user-facing, fail-closed bootstrap outcome."""

    def __init__(
        self,
        status: str,
        code: str,
        message: str,
        safe_next_action: str,
        *,
        details: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(code)
        self.status = status
        self.code = code
        self.message = message
        self.safe_next_action = safe_next_action
        self.details = dict(details or {})


def _present(path: Path) -> bool:
    """Return true for normal paths and broken symlinks alike."""

    return path.exists() or path.is_symlink()


def _resolve_path(value: str | Path) -> Path:
    return Path(value).expanduser().resolve()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _identity_hash(paths: Iterable[Path]) -> str:
    resolved = sorted(
        (item.resolve() for item in paths),
        key=lambda item: item.as_posix(),
    )
    common_root = Path(os.path.commonpath([str(item) for item in resolved]))
    digest = hashlib.sha256()
    for path in resolved:
        digest.update(path.relative_to(common_root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(_sha256_file(path).encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def _read_text(path: Path, code: str) -> str:
    if path.is_symlink() or not path.is_file():
        raise ValueError(code)
    try:
        value = path.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeError) as exc:
        raise ValueError(code) from exc
    if not value:
        raise ValueError(code)
    return value


def _read_object(path: Path, code: str) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise ValueError(code)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(code) from exc
    if not isinstance(value, dict):
        raise ValueError(code)
    return value


def _optional_object(path: Path, code: str) -> dict[str, Any] | None:
    if not _present(path):
        return None
    return _read_object(path, code)


def _normalise_request(value: str) -> str:
    request = " ".join(str(value).split()).strip()
    if not request:
        return DEFAULT_REQUEST
    if len(request) > 12000:
        raise BootstrapFailure(
            STATUS_BLOCKED,
            "REQUEST_TOO_LONG",
            "P2P chưa thể đọc yêu cầu này một cách an toàn.",
            "Rút gọn yêu cầu thành một mục tiêu đầu tiên rồi chạy lại.",
        )
    return request


def _schema_value(value: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in value:
            return value.get(key)
    return None


def _source_signal(root: Path) -> bool:
    return any(
        _present(root / relative)
        for relative in (
            "VERSION",
            "manifest/package.json",
            ".p2p/system/VERSION",
            ".p2p/system/p2p.manifest.json",
            "scripts/p2p_workflow.py",
        )
    )


def _validate_source_package(root: Path) -> tuple[dict[str, Any] | None, str, dict[str, Any]]:
    """Validate a source package using only local marker/filesystem evidence."""

    root = root.resolve()
    if not root.is_dir():
        return None, "NOT_A_DIRECTORY", {}
    if not _source_signal(root):
        return None, "NOT_A_PACKAGE", {}

    errors: list[str] = []
    version_path = root / "VERSION"
    try:
        version = _read_text(version_path, "SOURCE_VERSION_INVALID")
    except ValueError as exc:
        return None, str(exc), {"errors": [str(exc)]}

    manifest_path = root / "manifest" / "package.json"
    system_manifest_path = root / ".p2p" / "system" / "p2p.manifest.json"
    try:
        manifest = _read_object(manifest_path, "SOURCE_MANIFEST_INVALID")
    except ValueError as exc:
        errors.append(str(exc))
        manifest = {}
    try:
        system_manifest = _read_object(system_manifest_path, "SOURCE_SYSTEM_MANIFEST_INVALID")
    except ValueError as exc:
        errors.append(str(exc))
        system_manifest = {}

    if manifest.get("schema_version") != SOURCE_MANIFEST_SCHEMA:
        errors.append("SOURCE_MANIFEST_SCHEMA_INVALID")
    if manifest.get("version") != version:
        errors.append("SOURCE_VERSION_MANIFEST_MISMATCH")
    if system_manifest.get("manifest_schema") != SYSTEM_MANIFEST_SCHEMA:
        errors.append("SOURCE_SYSTEM_MANIFEST_SCHEMA_INVALID")
    if system_manifest.get("package_version") != version:
        errors.append("SOURCE_SYSTEM_VERSION_MANIFEST_MISMATCH")
    try:
        system_version = _read_text(root / ".p2p" / "system" / "VERSION", "SOURCE_SYSTEM_VERSION_INVALID")
    except ValueError as exc:
        errors.append(str(exc))
        system_version = ""
    if system_version != version:
        errors.append("SOURCE_SYSTEM_VERSION_MISMATCH")

    missing = [
        relative
        for relative in SOURCE_REQUIRED_FILES
        if (root / relative).is_symlink() or not (root / relative).is_file()
    ]
    errors.extend(f"SOURCE_REQUIRED_FILE_MISSING:{relative}" for relative in missing)
    if errors:
        return None, "SOURCE_PACKAGE_INVALID", {"errors": sorted(set(errors))}

    identity_files = [
        version_path,
        manifest_path,
        system_manifest_path,
        root / ".p2p" / "system" / "VERSION",
        *(root / relative for relative in SOURCE_REQUIRED_FILES),
    ]
    return (
        {
            "status": "VALID",
            "mode": "SOURCE_PACKAGE",
            "root": root,
            "package_version": version,
            "identity_sha256": _identity_hash(identity_files),
            "required_file_count": len(SOURCE_REQUIRED_FILES),
        },
        "VALID",
        {},
    )


def _validate_installed_project(project: Path) -> dict[str, Any]:
    """Return a mechanical installed-runtime result without changing files."""

    system = project / ".p2p" / "system"
    if not _present(system):
        return {"status": "ABSENT"}
    if system.is_symlink() or not system.is_dir():
        return {"status": "INVALID", "code": "INSTALLED_SYSTEM_PATH_INVALID"}

    source_value, source_status, _ = _validate_source_package(project)
    install_manifest_path = system / "p2p-install-manifest.json"
    release_path = system / "release.json"
    if not install_manifest_path.is_file() and source_value is not None:
        return {"status": "SOURCE_PROJECT", "source": source_value}

    if not install_manifest_path.is_file() or not release_path.is_file():
        code = "INSTALLED_MARKER_SET_INCOMPLETE"
        if source_status not in {"NOT_A_PACKAGE", "VALID"}:
            code = "INSTALLED_OR_SOURCE_AUTHORITY_INVALID"
        return {"status": "INVALID", "code": code}

    try:
        install_manifest = _read_object(install_manifest_path, "INSTALL_MANIFEST_INVALID")
        release = _read_object(release_path, "RELEASE_MARKER_INVALID")
    except ValueError as exc:
        return {"status": "INVALID", "code": str(exc)}

    if install_manifest.get("schema") != INSTALL_MANIFEST_SCHEMA:
        return {"status": "INVALID", "code": "INSTALL_MANIFEST_SCHEMA_INVALID"}
    if _schema_value(release, "schema", "schema_version") != RELEASE_SCHEMA:
        return {"status": "INVALID", "code": "RELEASE_MARKER_SCHEMA_INVALID"}
    package_version = str(install_manifest.get("package_version") or "").strip()
    release_version = str(release.get("package_version") or "").strip()
    try:
        runtime_version = _read_text(system / "VERSION", "INSTALLED_RUNTIME_VERSION_INVALID")
    except ValueError as exc:
        return {"status": "INVALID", "code": str(exc)}
    if not package_version or package_version != release_version or package_version != runtime_version:
        return {"status": "INVALID", "code": "INSTALLED_VERSION_MISMATCH"}

    missing = [
        relative
        for relative in INSTALLED_REQUIRED_FILES
        if (system / relative).is_symlink() or not (system / relative).is_file()
    ]
    if missing:
        return {
            "status": "INVALID",
            "code": "INSTALLED_REQUIRED_FILE_MISSING",
            "missing": missing,
        }
    identity = _identity_hash(
        [install_manifest_path, release_path, *(system / relative for relative in INSTALLED_REQUIRED_FILES)]
    )
    return {
        "status": "VALID",
        "mode": "INSTALLED_PROJECT",
        "root": project,
        "package_version": package_version,
        "identity_sha256": identity,
        "required_file_count": len(INSTALLED_REQUIRED_FILES),
    }


def _upward_paths(start: Path) -> list[Path]:
    start = start.resolve()
    return [start, *start.parents]


def _default_candidate_paths(project: Path) -> list[Path]:
    launcher_root = Path(__file__).resolve().parents[1]
    launcher_value, _, _ = _validate_source_package(launcher_root)
    # A valid package containing the launcher is the direct authority.  Do not
    # walk past it into an unrelated parent workspace that happens to contain
    # an old/incomplete P2P-looking directory.
    if launcher_value is not None:
        return [launcher_root]
    paths: list[Path] = []
    installed_project_root = (
        _present(project / ".p2p" / "system")
        and _validate_source_package(project)[0] is None
    )
    for start in (project, Path.cwd()):
        for path in _upward_paths(start):
            # An installed project is a valid runtime authority, not a source
            # package candidate. Do not turn its runtime marker into a false
            # invalid-source conflict when no source checkout is nearby.
            if installed_project_root and path == project.resolve():
                continue
            paths.append(path)
    result: list[Path] = []
    seen: set[Path] = set()
    for path in paths:
        path = path.resolve()
        if path not in seen:
            seen.add(path)
            result.append(path)
    return result


def discover_package(
    project: str | Path,
    package_hint: str | Path | None = None,
    *,
    candidate_roots: Iterable[str | Path] | None = None,
) -> dict[str, Any]:
    """Resolve one source package or return a beginner-safe decision/block."""

    project_path = _resolve_path(project)
    if package_hint is not None:
        package_path = _resolve_path(package_hint)
        value, status, details = _validate_source_package(package_path)
        if value is None:
            raise BootstrapFailure(
                STATUS_BLOCKED,
                "EXPLICIT_PACKAGE_INVALID",
                "P2P không thể xác minh thư mục đã chọn một cách an toàn.",
                "Giữ nguyên dữ liệu và chọn một thư mục P2P hợp lệ trong chế độ nâng cao.",
                details={"package_root": str(package_path), "validation": status, **details},
            )
        return value

    roots = list(candidate_roots) if candidate_roots is not None else _default_candidate_paths(project_path)
    valid: list[dict[str, Any]] = []
    invalid: list[dict[str, Any]] = []
    seen: set[Path] = set()
    for raw in roots:
        path = _resolve_path(raw)
        if path in seen:
            continue
        seen.add(path)
        value, status, details = _validate_source_package(path)
        if value is not None:
            valid.append(value)
        elif status not in {"NOT_A_PACKAGE", "NOT_A_DIRECTORY"}:
            invalid.append({"root": str(path), "status": status, **details})
    if len(valid) > 1:
        raise BootstrapFailure(
            STATUS_NEEDS_DECISION,
            "MULTIPLE_VALID_PACKAGES",
            "P2P tìm thấy nhiều thư mục có thể là nguồn chính.",
            "Chọn một thư mục P2P duy nhất trong chế độ nâng cao rồi chạy lại.",
            details={"packages": [str(item["root"]) for item in valid]},
        )
    if not valid and invalid:
        raise BootstrapFailure(
            STATUS_BLOCKED,
            "PACKAGE_AUTHORITY_INVALID",
            "P2P tìm thấy dấu hiệu của một nguồn P2P nhưng không thể xác minh nguồn đó.",
            "Giữ nguyên thư mục hiện tại và nhờ người phụ trách kiểm tra nguồn P2P.",
            details={"invalid_candidates": invalid},
        )
    if not valid:
        raise BootstrapFailure(
            STATUS_NEEDS_DECISION,
            "PACKAGE_NOT_FOUND",
            "P2P chưa tìm thấy nguồn P2P hợp lệ để bắt đầu.",
            "Chọn thư mục P2P đã tải trong chế độ nâng cao rồi chạy lại.",
        )
    return valid[0]


def resolve_environment(
    project: str | Path,
    package_hint: str | Path | None = None,
    *,
    candidate_roots: Iterable[str | Path] | None = None,
) -> dict[str, Any]:
    """Prefer a valid installed project, otherwise resolve a source package."""

    project_path = _resolve_path(project)
    installed = _validate_installed_project(project_path)
    if installed.get("status") == "INVALID":
        raise BootstrapFailure(
            STATUS_BLOCKED,
            str(installed.get("code") or "INSTALLED_RUNTIME_INVALID"),
            "P2P đã thấy một môi trường cũ nhưng môi trường đó không nhất quán.",
            "Giữ nguyên dữ liệu hiện tại và nhờ người phụ trách kiểm tra môi trường cũ.",
            details=installed,
        )
    if installed.get("status") == "VALID":
        return installed

    if installed.get("status") == "SOURCE_PROJECT":
        source = installed.get("source")
        if isinstance(source, dict):
            return source
    return discover_package(project_path, package_hint, candidate_roots=candidate_roots)


def _runtime_hint(project: Path, environment: Mapping[str, Any]) -> str:
    if environment.get("mode") == "INSTALLED_PROJECT":
        return str(project)
    return str(environment.get("root") or "")


def _state_file_checks(project: Path) -> None:
    p2p_dir = project / ".p2p"
    if _present(p2p_dir) and (p2p_dir.is_symlink() or not p2p_dir.is_dir()):
        raise BootstrapFailure(
            STATUS_BLOCKED,
            "P2P_DIRECTORY_INVALID",
            "P2P không thể dùng thư mục dữ liệu hiện tại một cách an toàn.",
            "Giữ nguyên dữ liệu hiện tại và nhờ người phụ trách kiểm tra thư mục dự án.",
        )
    for relative in (".p2p/state", ".p2p/state/goals", ".p2p/evals"):
        path = project / relative
        if _present(path) and (path.is_symlink() or not path.is_dir()):
            raise BootstrapFailure(
                STATUS_BLOCKED,
                "STATE_DIRECTORY_INVALID",
                "P2P không thể xác minh một thư mục trạng thái hiện có.",
                "Giữ nguyên dữ liệu hiện tại và nhờ người phụ trách kiểm tra trạng thái dự án.",
                details={"path": str(path)},
            )
    ledger_path = project / ".p2p" / "state" / "execution-ledger.jsonl"
    if _present(ledger_path) and (ledger_path.is_symlink() or not ledger_path.is_file()):
        raise BootstrapFailure(
            STATUS_BLOCKED,
            "EXECUTION_LEDGER_INVALID",
            "P2P không thể xác minh sổ theo dõi đang có.",
            "Giữ nguyên dữ liệu hiện tại và nhờ người phụ trách kiểm tra sổ theo dõi.",
            details={"path": str(ledger_path)},
        )
    for relative in OPTIONAL_PROJECT_JSON + (
        ".p2p/state/goal-contract.json",
        ".p2p/state/task-state.json",
    ):
        path = project / relative
        if _present(path) and (path.is_symlink() or not path.is_file()):
            raise BootstrapFailure(
                STATUS_BLOCKED,
                "STATE_FILE_INVALID",
                "P2P không thể xác minh một tệp trạng thái hiện có.",
                "Giữ nguyên dữ liệu hiện tại và nhờ người phụ trách kiểm tra trạng thái dự án.",
                details={"path": str(path)},
            )


def _goal_files(project: Path) -> list[Path]:
    goals = project / ".p2p" / "state" / "goals"
    if not goals.is_dir() or goals.is_symlink():
        return []
    return sorted(path for path in goals.rglob("*") if path.is_file())


def _load_existing_task_plan(project: Path, workflow: Any, runtime_hint: str) -> Any | None:
    task_path = project / ".p2p" / "state" / "task-state.json"
    if not task_path.exists():
        return None
    try:
        task_state = workflow.capability_api(project, runtime_hint, "task_state")
        return task_state.TaskStateStore(project).load()
    except Exception as exc:
        raise BootstrapFailure(
            STATUS_BLOCKED,
            "TASK_STATE_UNREADABLE",
            "P2P không thể đọc việc đang được giữ lại để tiếp tục.",
            "Giữ nguyên trạng thái hiện tại và nhờ người phụ trách kiểm tra trước khi chạy lại.",
            details={"error_type": type(exc).__name__},
        ) from exc


def _read_existing_ledger(project: Path, workflow: Any, runtime_hint: str) -> dict[str, Any]:
    ledger_path = project / ".p2p" / "state" / "execution-ledger.jsonl"
    if not _present(ledger_path):
        return {"status": "ABSENT", "event_count": 0}
    try:
        task_state = workflow.capability_api(project, runtime_hint, "task_state")
        result = task_state.TaskStateStore(project).read_events()
    except Exception as exc:
        raise BootstrapFailure(
            STATUS_BLOCKED,
            "EXECUTION_LEDGER_UNREADABLE",
            "P2P không thể xác minh sổ theo dõi đang có.",
            "Giữ nguyên dữ liệu hiện tại và nhờ người phụ trách kiểm tra sổ theo dõi.",
            details={"error_type": type(exc).__name__},
        ) from exc
    if str(result.get("status") or "") == "PARTIAL":
        raise BootstrapFailure(
            STATUS_BLOCKED,
            "EXECUTION_LEDGER_INVALID",
            "P2P không thể xác minh sổ theo dõi đang có.",
            "Giữ nguyên dữ liệu hiện tại và nhờ người phụ trách kiểm tra sổ theo dõi.",
        )
    events = result.get("events") if isinstance(result.get("events"), list) else []
    return {"status": str(result.get("status") or "UNKNOWN"), "event_count": len(events)}


def _binding_status(binding: Any, expected: Mapping[str, Any]) -> str:
    if not isinstance(binding, dict):
        return "INVALID"
    if binding.get("schema_version") != "p2p-bootstrap-binding/1":
        return "INVALID"
    if binding.get("gateway") != expected.get("gateway"):
        return "INVALID"
    if binding.get("recovery") != expected.get("recovery"):
        return "CONFLICT"
    locator = binding.get("locator")
    if not isinstance(locator, dict) or locator.get("kind") not in {
        "PROJECT_RUNTIME",
        "RELATIVE_PACKAGE",
        "REDISCOVER_PACKAGE",
    }:
        return "INVALID"
    locator_path = locator.get("path")
    if locator_path is not None and (
        not isinstance(locator_path, str)
        or os.path.isabs(locator_path)
        or Path(locator_path).is_absolute()
    ):
        return "INVALID"
    return "MATCH" if dict(binding) == dict(expected) else "CONFLICT"


def _preflight_project(
    project: Path,
    environment: Mapping[str, Any],
    request: str,
    workflow: Any,
) -> dict[str, Any]:
    """Reject unsafe existing state before any workflow write is reached."""

    _state_file_checks(project)
    goal_path = project / ".p2p" / "state" / "goal-contract.json"
    task_path = project / ".p2p" / "state" / "task-state.json"
    try:
        for relative in OPTIONAL_PROJECT_JSON:
            _optional_object(project / relative, "PROJECT_STATE_UNREADABLE")
        existing_goal = _optional_object(goal_path, "GOAL_CONTRACT_UNREADABLE")
    except ValueError as exc:
        raise BootstrapFailure(
            STATUS_BLOCKED,
            str(exc),
            "P2P không thể xác minh một tệp trạng thái hiện có.",
            "Giữ nguyên dữ liệu hiện tại và nhờ người phụ trách kiểm tra trạng thái trước khi chạy lại.",
        ) from exc
    runtime_hint = _runtime_hint(project, environment)
    ledger = _read_existing_ledger(project, workflow, runtime_hint)
    existing_plan = _load_existing_task_plan(project, workflow, runtime_hint)
    goal_files = _goal_files(project)
    normalized = " ".join(request.split()).strip()

    if existing_goal is not None:
        if existing_goal.get("schema_version") != GOAL_SCHEMA:
            raise BootstrapFailure(
                STATUS_BLOCKED,
                "GOAL_CONTRACT_SCHEMA_INVALID",
                "P2P tìm thấy một kế hoạch cũ không thuộc định dạng an toàn hiện tại.",
                "Giữ nguyên kế hoạch cũ và nhờ người phụ trách kiểm tra trước khi chạy lại.",
            )
        gateway = existing_goal.get("beginner_gateway")
        if not isinstance(gateway, dict) or gateway.get("schema_version") != BEGINNER_GATEWAY_SCHEMA or gateway.get("mode") != BEGINNER_MODE:
            raise BootstrapFailure(
                STATUS_NEEDS_DECISION,
                "EXISTING_GOAL_REQUIRES_RECONCILIATION",
                "Dự án đã có một kế hoạch cũ cần được xác nhận trước khi bắt đầu lại.",
                "Chọn tiếp tục kế hoạch cũ hoặc dừng yêu cầu này trong chế độ nâng cao.",
            )
        old_request = " ".join(str(gateway.get("request") or "").split()).strip()
        if old_request != normalized:
            raise BootstrapFailure(
                STATUS_NEEDS_DECISION,
                "EXISTING_GOAL_REQUIRES_RECONCILIATION",
                "Dự án đang giữ một yêu cầu khác.",
                "Xác nhận yêu cầu đang giữ lại trước khi bắt đầu một yêu cầu mới.",
            )
        if existing_plan is not None and existing_plan.goal_id != str(existing_goal.get("goal_id") or ""):
            raise BootstrapFailure(
                STATUS_BLOCKED,
                "GOAL_TASK_MISMATCH",
                "P2P không thể ghép an toàn kế hoạch và trạng thái đang giữ lại.",
                "Giữ nguyên trạng thái hiện tại và nhờ người phụ trách kiểm tra hai phần này.",
            )
    elif existing_plan is not None or goal_files or ledger.get("event_count", 0):
        raise BootstrapFailure(
            STATUS_NEEDS_DECISION,
            "EXISTING_STATE_REQUIRES_RECONCILIATION",
            "Dự án đã có trạng thái cần được xác nhận trước khi P2P tiếp tục.",
            "Xác nhận trạng thái đang giữ lại trước khi bắt đầu bootstrap.",
        )

    binding = existing_goal.get("portable_bootstrap_binding") if isinstance(existing_goal, dict) else None
    if binding is not None:
        binding_expected = _binding_for(project, environment)
        binding_status = _binding_status(binding, binding_expected)
        if binding_status == "INVALID":
            raise BootstrapFailure(
                STATUS_BLOCKED,
                "BOOTSTRAP_BINDING_INVALID",
                "P2P không thể xác minh liên kết môi trường cũ.",
                "Giữ nguyên trạng thái hiện tại và nhờ người phụ trách kiểm tra liên kết môi trường.",
            )
        if binding_status == "CONFLICT":
            raise BootstrapFailure(
                STATUS_NEEDS_DECISION,
                "BOOTSTRAP_BINDING_CONFLICT",
                "Liên kết môi trường cũ không trùng với nguồn P2P hiện tại.",
                "Chọn đúng nguồn P2P đã dùng trước đây trong chế độ nâng cao.",
            )

    ledger_path = project / ".p2p" / "state" / "execution-ledger.jsonl"
    return {
        "existing_goal": existing_goal,
        "existing_plan": existing_plan,
        "goal_file_count": len(goal_files),
        "ledger_event_count_before": _count_events(ledger_path, "beginner_gateway_ingested"),
    }


def _portable_locator(project: Path, environment: Mapping[str, Any]) -> dict[str, Any]:
    if environment.get("mode") == "INSTALLED_PROJECT":
        return {"kind": "PROJECT_RUNTIME", "path": ".p2p/system"}
    package_root = Path(str(environment.get("root"))).resolve()
    try:
        relative = os.path.relpath(str(package_root), str(project)).replace(os.sep, "/")
    except ValueError:
        relative = ""
    if relative and not Path(relative).is_absolute():
        return {"kind": "RELATIVE_PACKAGE", "path": relative}
    return {"kind": "REDISCOVER_PACKAGE", "path": None}


def _binding_for(project: Path, environment: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "p2p-bootstrap-binding/1",
        "runtime_mode": environment.get("mode"),
        "package_version": environment.get("package_version"),
        "package_identity_sha256": environment.get("identity_sha256"),
        "locator": _portable_locator(project, environment),
        "gateway": {
            "schema_version": BEGINNER_GATEWAY_SCHEMA,
            "mode": BEGINNER_MODE,
        },
        "recovery": {
            "goal_contract": ".p2p/state/goal-contract.json",
            "task_state": ".p2p/state/task-state.json",
            "execution_ledger": ".p2p/state/execution-ledger.jsonl",
            "rediscover_package": environment.get("mode") != "INSTALLED_PROJECT",
        },
    }


def _bind_goal_contract(project: Path, environment: Mapping[str, Any], workflow: Any) -> dict[str, Any]:
    path = project / ".p2p" / "state" / "goal-contract.json"
    try:
        contract = workflow.load_current_contract(project)
    except Exception as exc:
        raise BootstrapFailure(
            STATUS_BLOCKED,
            "GOAL_CONTRACT_BINDING_FAILED",
            "P2P không thể giữ lại liên kết Beginner Gateway một cách an toàn.",
            "Giữ nguyên trạng thái hiện tại và nhờ người phụ trách kiểm tra kế hoạch.",
            details={"error_type": type(exc).__name__},
        ) from exc
    if not isinstance(contract, dict) or contract.get("schema_version") != GOAL_SCHEMA:
        raise BootstrapFailure(
            STATUS_BLOCKED,
            "GOAL_CONTRACT_BINDING_INVALID",
            "P2P không thể xác minh kế hoạch để tiếp tục.",
            "Giữ nguyên trạng thái hiện tại và nhờ người phụ trách kiểm tra kế hoạch.",
        )
    expected = _binding_for(project, environment)
    existing = contract.get("portable_bootstrap_binding")
    if existing is not None:
        binding_status = _binding_status(existing, expected)
        if binding_status == "INVALID":
            raise BootstrapFailure(
                STATUS_BLOCKED,
                "BOOTSTRAP_BINDING_INVALID",
                "P2P không thể xác minh liên kết môi trường cũ.",
                "Giữ nguyên trạng thái hiện tại và nhờ người phụ trách kiểm tra liên kết môi trường.",
            )
        if binding_status == "CONFLICT":
            raise BootstrapFailure(
                STATUS_NEEDS_DECISION,
                "BOOTSTRAP_BINDING_CONFLICT",
                "Liên kết môi trường cũ không trùng với nguồn P2P hiện tại.",
                "Chọn đúng nguồn P2P đã dùng trước đây trong chế độ nâng cao.",
            )
        return {"status": "REUSED", "binding": existing, "path": ".p2p/state/goal-contract.json"}

    before = path.read_bytes() if path.is_file() else None
    updated = dict(contract)
    updated["portable_bootstrap_binding"] = expected
    if before is not None and path.read_bytes() != before:
        raise BootstrapFailure(
            STATUS_BLOCKED,
            "GOAL_CONTRACT_CHANGED_DURING_BOOTSTRAP",
            "Kế hoạch đã thay đổi trong lúc P2P đang chuẩn bị.",
            "Chạy lại sau khi kế hoạch đã ổn định; P2P chưa thay thế dữ liệu.",
        )
    try:
        workflow.write_goal(project, updated)
    except Exception as exc:
        raise BootstrapFailure(
            STATUS_BLOCKED,
            "GOAL_CONTRACT_BINDING_FAILED",
            "P2P không thể giữ lại liên kết Beginner Gateway một cách an toàn.",
            "Giữ nguyên trạng thái hiện tại và nhờ người phụ trách kiểm tra kế hoạch.",
            details={"error_type": type(exc).__name__},
        ) from exc
    return {"status": "CREATED", "binding": expected, "path": ".p2p/state/goal-contract.json"}


def _count_events(path: Path, event_name: str) -> int:
    if not path.is_file() or path.is_symlink():
        return 0
    count = 0
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError):
        return 0
    for line in lines:
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict) and value.get("event") == event_name:
            count += 1
    return count


def _safety_projection() -> dict[str, Any]:
    return {
        "automatic_host_start": False,
        "promote": False,
        "release": False,
        "deploy": False,
        "production_change": False,
        "secret_creation_or_exposure": False,
        "git_force_reset_clean": False,
        "permission_expansion": False,
        "owner_gates_unchanged": True,
    }


def _json_safe(value: Any) -> Any:
    """Project advanced diagnostics without leaking non-JSON path objects."""

    if isinstance(value, Path):
        return str(value)
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    return value


def _failure_result(project: Path, request: str, failure: BootstrapFailure) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA,
        "status": failure.status,
        "project": project.name,
        "message": failure.message,
        "safe_next_action": failure.safe_next_action,
        "beginner_gateway": {"status": "NOT_BOUND"},
        "state_initialization": {"status": "NOT_STARTED"},
        "idempotency": {"status": "NOT_APPLICABLE"},
        "safety": _safety_projection(),
        "delegation": {"status": "NOT_STARTED", "orchestrator": "existing p2p_workflow"},
        "details": {
            "code": failure.code,
            "request": request,
            **failure.details,
        },
    }


def _success_result(
    project: Path,
    request: str,
    environment: Mapping[str, Any],
    preflight: Mapping[str, Any],
    gateway_result: Mapping[str, Any],
    state_result: Mapping[str, Any],
    binding_result: Mapping[str, Any],
    support_hint: str,
) -> dict[str, Any]:
    persistence = gateway_result.get("persistence") if isinstance(gateway_result.get("persistence"), dict) else {}
    charter = gateway_result.get("charter") if isinstance(gateway_result.get("charter"), dict) else {}
    gateway_status = str(charter.get("status") or "")
    question = str(charter.get("question") or "").strip()
    eval_value = state_result.get("eval") if isinstance(state_result.get("eval"), dict) else {}
    eval_status = str(eval_value.get("status") or "")
    if eval_status not in {"CREATED", "REUSED"}:
        raise BootstrapFailure(
            STATUS_BLOCKED,
            "PROJECT_STATE_INITIALIZATION_INCOMPLETE",
            "P2P chưa thể hoàn tất phần chuẩn bị an toàn cho dự án.",
            "Giữ nguyên dữ liệu hiện tại và nhờ người phụ trách kiểm tra trạng thái chuẩn bị.",
            details={"eval_status": eval_status},
        )
    status = STATUS_NEEDS_DECISION if question else STATUS_READY
    action = str(charter.get("safe_next_action") or "Tiếp tục theo bước an toàn tiếp theo.")
    if status == STATUS_READY:
        message = "P2P đã sẵn sàng và đã kết nối Beginner Gateway."
    else:
        message = "P2P đã kết nối Beginner Gateway và đang chờ một lựa chọn an toàn của bạn."
    ledger_path = project / ".p2p" / "state" / "execution-ledger.jsonl"
    before_count = int(preflight.get("ledger_event_count_before") or 0)
    after_count = _count_events(ledger_path, "beginner_gateway_ingested")
    return {
        "schema_version": SCHEMA,
        "status": status,
        "project": project.name,
        "message": message,
        "safe_next_action": action,
        "beginner_gateway": {
            "status": "BOUND",
            "gateway_status": gateway_status,
            "question_required": bool(question),
            "saved_for_resume": persistence.get("status") in {"CREATED", "REUSED"},
        },
        "state_initialization": {
            "status": "CREATED" if state_result.get("created") else "REUSED",
            "created": list(state_result.get("created") or []),
            "reused": list(state_result.get("reused") or []),
            "eval_status": eval_status,
        },
        "idempotency": {
            "status": "PASS",
            "beginner_gateway_ingested_before": before_count,
            "beginner_gateway_ingested_after": after_count,
            "duplicate_event_added": max(0, after_count - before_count - (1 if persistence.get("status") == "CREATED" else 0)),
        },
        "safety": _safety_projection(),
        "delegation": {
            "status": "DELEGATED",
            "orchestrator": "existing p2p_workflow",
            "gateway": "existing BG01 beginner_gateway",
            "task_state": "existing TaskStateStore",
            "recovery": "existing Control Tower recommendation",
            "execution_started": False,
        },
        "details": {
            "request": request,
            "environment": dict(environment),
            "preflight": {
                "existing_goal": bool(preflight.get("existing_goal")),
                "existing_task": bool(preflight.get("existing_plan")),
            },
            "gateway_result": dict(gateway_result),
            "state_result": dict(state_result),
            "binding": dict(binding_result),
            "runtime_hint": _runtime_hint(project, environment),
            "support_hint": support_hint,
        },
    }


def bootstrap(
    project: str | Path = ".",
    request: str | None = None,
    package_hint: str | Path | None = None,
    *,
    candidate_roots: Iterable[str | Path] | None = None,
) -> dict[str, Any]:
    """Perform one portable bootstrap action and return a structured result."""

    project_path = _resolve_path(project)
    request_value = DEFAULT_REQUEST
    try:
        request_value = _normalise_request(request if request is not None else DEFAULT_REQUEST)
        if not project_path.is_dir() or project_path.is_symlink():
            raise BootstrapFailure(
                STATUS_BLOCKED,
                "PROJECT_DIRECTORY_INVALID",
                "P2P không thể xác minh thư mục dự án.",
                "Chọn một thư mục dự án hiện có rồi chạy lại.",
            )
        environment = resolve_environment(project_path, package_hint, candidate_roots=candidate_roots)
        package_root = environment.get("root")
        if environment.get("mode") == "SOURCE_PACKAGE" and package_root and project_path == Path(package_root).resolve():
            raise BootstrapFailure(
                STATUS_NEEDS_DECISION,
                "PACKAGE_AND_PROJECT_ARE_SAME",
                "Thư mục P2P và thư mục dự án đang là cùng một nơi.",
                "Chọn một thư mục dự án riêng để P2P không thay đổi mã nguồn P2P.",
            )

        script_dir = Path(__file__).resolve().parent
        if str(script_dir) not in sys.path:
            sys.path.insert(0, str(script_dir))
        import p2p_workflow as workflow  # local canonical workflow; no second orchestrator

        runtime_hint = _runtime_hint(project_path, environment)
        # Resolve any optional source support before the canonical workflow
        # gets a chance to write Goal/Task/ledger state. Installed runtimes
        # stay authoritative; the source package is only a compatibility
        # helper for the existing project-eval/template seam.
        support_hint = runtime_hint
        compatible_helpers: list[Path] | None = None
        if environment.get("mode") == "INSTALLED_PROJECT":
            if package_hint is not None:
                # An explicit advanced choice is always validated, even when
                # the installed runtime can complete the task by itself.
                support_package = discover_package(
                    project_path,
                    package_hint,
                    candidate_roots=candidate_roots,
                )
                support_hint = str(support_package.get("root") or runtime_hint)
            try:
                # A complete installed runtime should be self-sufficient. Do
                # not let an unrelated parent directory decide its fate when
                # the runtime already contains a compatible eval helper.
                compatible_helpers = workflow.eval_helper_candidates(project_path, runtime_hint)
            except Exception as exc:
                raise BootstrapFailure(
                    STATUS_BLOCKED,
                    "PROJECT_EVAL_HELPER_DISCOVERY_FAILED",
                    "P2P chưa thể xác minh bộ kiểm tra tối thiểu cho dự án.",
                    "Giữ nguyên dữ liệu hiện tại và nhờ người phụ trách kiểm tra nguồn P2P.",
                    details={"error_type": type(exc).__name__},
                ) from exc
            if not compatible_helpers and package_hint is None:
                try:
                    support_package = discover_package(
                        project_path,
                        package_hint,
                        candidate_roots=candidate_roots,
                    )
                    support_hint = str(support_package.get("root") or runtime_hint)
                except BootstrapFailure as failure:
                    if package_hint is not None or failure.code != "PACKAGE_NOT_FOUND":
                        raise

        if not compatible_helpers:
            try:
                compatible_helpers = workflow.eval_helper_candidates(project_path, support_hint)
            except Exception as exc:
                raise BootstrapFailure(
                    STATUS_BLOCKED,
                    "PROJECT_EVAL_HELPER_DISCOVERY_FAILED",
                    "P2P chưa thể xác minh bộ kiểm tra tối thiểu cho dự án.",
                    "Giữ nguyên dữ liệu hiện tại và nhờ người phụ trách kiểm tra nguồn P2P.",
                    details={"error_type": type(exc).__name__},
                ) from exc
        if not compatible_helpers:
            raise BootstrapFailure(
                STATUS_BLOCKED,
                "PROJECT_EVAL_HELPER_UNAVAILABLE",
                "P2P chưa tìm thấy bộ kiểm tra tối thiểu tương thích để chuẩn bị dự án.",
                "Chọn một nguồn P2P hợp lệ có hỗ trợ project-eval rồi chạy lại.",
            )

        preflight = _preflight_project(project_path, environment, request_value, workflow)
        gateway_result = workflow.beginner_entrypoint(
            project_path,
            request_value,
            package_hint=runtime_hint,
        )
        persistence = gateway_result.get("persistence") if isinstance(gateway_result.get("persistence"), dict) else {}
        if persistence.get("status") == "BLOCKED":
            reason = str(persistence.get("reason") or "TASK_STATE_BINDING_FAILED")
            status = STATUS_NEEDS_DECISION if "RECONCILIATION" in reason else STATUS_BLOCKED
            raise BootstrapFailure(
                status,
                reason,
                "Dự án đang có một trạng thái cần được xác nhận trước khi P2P tiếp tục." if status == STATUS_NEEDS_DECISION else "P2P không thể giữ lại trạng thái dự án một cách an toàn.",
                "Xác nhận trạng thái đang giữ lại trước khi tiếp tục." if status == STATUS_NEEDS_DECISION else "Giữ nguyên dữ liệu hiện tại và nhờ người phụ trách kiểm tra trạng thái.",
                details={"gateway_result": gateway_result},
            )

        inspection = workflow.inspect_project(project_path, request_value, runtime_hint)
        contract = workflow.load_current_contract(project_path)
        state_result = workflow.bootstrap_project(
            project_path,
            inspection,
            contract,
            support_hint,
        )
        binding_result = _bind_goal_contract(project_path, environment, workflow)
        return _success_result(
            project_path,
            request_value,
            environment,
            preflight,
            gateway_result,
            state_result,
            binding_result,
            support_hint,
        )
    except BootstrapFailure as failure:
        return _failure_result(project_path, request_value, failure)
    except Exception as exc:
        failure = BootstrapFailure(
            STATUS_BLOCKED,
            "BOOTSTRAP_UNEXPECTED_FAILURE",
            "P2P chưa thể hoàn tất bootstrap một cách an toàn.",
            "Giữ nguyên dữ liệu hiện tại và nhờ người phụ trách kiểm tra trước khi chạy lại.",
            details={"error_type": type(exc).__name__},
        )
        return _failure_result(project_path, request_value, failure)


def public_result(result: Mapping[str, Any], *, advanced: bool = False) -> dict[str, Any]:
    """Return the beginner projection; technical details require explicit mode."""

    gateway = result.get("beginner_gateway") if isinstance(result.get("beginner_gateway"), dict) else {}
    public: dict[str, Any] = {
        "schema_version": SCHEMA,
        "status": result.get("status"),
        "project": result.get("project"),
        "message": result.get("message"),
        "beginner_gateway": gateway.get("status", "NOT_BOUND"),
        "saved_for_resume": bool(gateway.get("saved_for_resume")),
        "safe_next_action": result.get("safe_next_action"),
    }
    if advanced:
        public["advanced"] = {
            "details": _json_safe(result.get("details", {})),
            "state_initialization": _json_safe(result.get("state_initialization", {})),
            "idempotency": _json_safe(result.get("idempotency", {})),
            "safety": _json_safe(result.get("safety", {})),
            "delegation": _json_safe(result.get("delegation", {})),
        }
    return public


def render_beginner(result: Mapping[str, Any]) -> str:
    return "\n".join(
        (
            "P2P",
            f"TRẠNG THÁI\n{result.get('status', STATUS_BLOCKED)}",
            f"\n{result.get('message', '')}",
            f"\nBEGINNER GATEWAY\n{'Đã kết nối' if result.get('beginner_gateway') == 'BOUND' else 'Chưa kết nối'}",
            f"\nBƯỚC TIẾP THEO AN TOÀN\n{result.get('safe_next_action', '')}",
        )
    )


def parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", default=".", help="Project folder; defaults to the current folder")
    parser.add_argument("--package", dest="package_hint", help="Advanced/debug: explicit P2P source folder")
    parser.add_argument("--request", help="Optional first project request")
    parser.add_argument("--json", action="store_true", help="Print the structured beginner result")
    parser.add_argument("--advanced", "--debug", dest="advanced", action="store_true", help="Show bounded technical details")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    result = bootstrap(args.project, args.request, args.package_hint)
    output = public_result(result, advanced=bool(args.advanced))
    if args.json:
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print(render_beginner(output))
        if args.advanced:
            print("\nCHI TIẾT NÂNG CAO")
            print(json.dumps(output.get("advanced", {}), ensure_ascii=False, indent=2))
    return 2 if result.get("status") == STATUS_BLOCKED else 0


if __name__ == "__main__":
    raise SystemExit(main())
