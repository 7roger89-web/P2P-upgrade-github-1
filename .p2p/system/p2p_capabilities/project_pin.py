"""Canonical project-pin producer and validator for installed P2P projects.

The pin is project-local adoption state.  It is never an official-release
authority: the candidate distribution metadata binds the candidate to the
official baseline, while this record binds one installed candidate to one
project and one external artifact hash.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


PROJECT_PIN_SCHEMA = "p2p-project-pin/1"
CANDIDATE_MANIFEST_NAME = "CANDIDATE-DISTRIBUTION-MANIFEST.json"
SOURCE_BINDING_NAME = "SOURCE-BINDING.json"
ARTIFACT_IDENTITY_NAME = "ARTIFACT-IDENTITY.json"
VERSION_NAME = "VERSION"
HEX64 = re.compile(r"^[0-9a-fA-F]{64}$")
HEX40 = re.compile(r"^[0-9a-fA-F]{40}$")


class ProjectPinError(ValueError):
    """Raised when a project pin or its candidate binding is invalid."""


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
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


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
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
    return hashlib.sha256("\n".join(entries).encode("utf-8")).hexdigest()


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
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


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
    pin = {
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
    return pin


def write_pin(project_root: Path, pin: dict[str, Any]) -> Path:
    if pin.get("schema") != PROJECT_PIN_SCHEMA:
        raise ProjectPinError("PROJECT_PIN_SCHEMA_INVALID")
    path = project_root.resolve() / ".p2p" / "project-pin.json"
    _write_json_atomic(path, pin)
    return path


def validate_pin(
    project_root: Path,
    *,
    metadata_root: Path | None = None,
    expected_artifact_sha256: str | None = None,
    expected_version: str | None = None,
) -> dict[str, Any]:
    """Validate pin, installed candidate metadata, and project binding."""

    root = project_root.resolve()
    pin = _read_json(root / ".p2p" / "project-pin.json", "PROJECT_PIN")
    if pin.get("schema") != PROJECT_PIN_SCHEMA:
        raise ProjectPinError("PROJECT_PIN_SCHEMA_INVALID")
    if pin.get("verification_status") != "VERIFIED":
        raise ProjectPinError("PROJECT_PIN_NOT_VERIFIED")
    if pin.get("doctor_result") != "HEALTHY":
        raise ProjectPinError("PROJECT_PIN_DOCTOR_NOT_HEALTHY")
    version, candidate, binding, _identity = _candidate_metadata(metadata_root or (root / ".p2p" / "system"))
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
        "schema": PROJECT_PIN_SCHEMA,
        "candidate_version": version,
        "artifact_sha256": pin_artifact,
        "project_fingerprint": pin["project_fingerprint"],
        "source_commit": binding["source_commit"],
        "source_tree": binding["source_tree"],
        "verification_status": pin["verification_status"],
        "doctor_result": pin["doctor_result"],
    }
