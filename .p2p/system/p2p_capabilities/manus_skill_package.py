"""Provider-neutral Manus Skill package planning and repo-local export.

This module is deliberately separate from the canonical pure projection layer. Planning is pure data; export is an explicit, repo-local materialization boundary. Neither
path imports credentials, calls the network, executes scripts, installs
packages, mutates host configuration, or creates Manus tasks.
"""

from __future__ import annotations

import hashlib
import json
import zipfile
from dataclasses import dataclass, replace
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping

from .vendor_skill import VendorSkillError, is_vendor_skill, load_vendor_skill, vendor_skill_metadata


MANUS_HOST_KIND = "manus"
MANUS_PACKAGE_SCHEMA = "p2p-manus-skill-package/1"
MANUS_PROVENANCE_SCHEMA = "p2p-manus-skill-provenance/1"
MANUS_MAPPING_STATUS = "MAPPING_SUPPORTED"
MANUS_RUNTIME_STATUS = "NOT_CERTIFIED"
MANUS_LIFECYCLE = (
    "MAPPING_PLANNED",
    "PACKAGE_FORMAT_PROVEN",
    "MAPPING_SUPPORTED",
    "RUNTIME_PROOF",
    "HOST_RUNTIME_CERTIFIED",
)
READY, BLOCKED = "READY", "BLOCKED"
OWNERSHIP_CLASSES = ("P2P_PROJECT_MANAGED", "HOST_OWNED_PRESERVE", "OWNER_REVIEW_REQUIRED")
REASON_CODES = (
    "HOST_KIND_UNKNOWN",
    "HOST_SCOPE_MISMATCH",
    "CAPABILITY_NOT_SELECTED",
    "CONTEXT_EXPANSION_UNAUTHORIZED",
    "PROVENANCE_MISSING",
    "SOURCE_HASH_STALE",
    "ENTRYPOINT_HASH_MISMATCH",
    "PATH_TRAVERSAL",
    "SERIALIZATION_INVALID",
    "P2P_OWNERSHIP_CONFLICT",
    "P2P_OWNERSHIP_REVIEW_REQUIRED",
    "PACKAGE_STAGE_REQUIRED",
    "HOST_FORMAT_AMBIGUOUS",
    "BLOCKED_HOST_DRIFT",
    "OUTPUT_PATH_INVALID",
    "OUTPUT_EXISTS",
    "DECLARATION_MISMATCH",
    "SCRIPT_EXECUTION_FORBIDDEN",
    "VENDOR_SNAPSHOT_MISSING",
    "VENDOR_ENTRYPOINT_MISSING",
    "VENDOR_ENTRYPOINT_HASH_MISMATCH",
    "VENDOR_SNAPSHOT_HASH_MISMATCH",
)
_SHA256_LENGTH = 64


class ManusPackageError(ValueError):
    """Raised for an unsafe package request or export boundary."""


@dataclass(frozen=True)
class ManusPackageFile:
    relative_path: str
    format: str
    content_hash: str | None
    content_or_descriptor: Any
    ownership_class: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "relative_path": self.relative_path,
            "format": self.format,
            "content_hash": self.content_hash,
            "content_or_descriptor": self.content_or_descriptor,
            "ownership_class": self.ownership_class,
        }


@dataclass(frozen=True)
class ManusSkillPackagePlan:
    status: str
    host_kind: str
    mapping_status: str
    runtime_status: str
    lifecycle_stage: str
    capability_id: str
    source_hash: str
    entrypoint_hash: str
    load_stage: str
    package_format: str
    files: tuple[ManusPackageFile, ...]
    warnings: tuple[str, ...]
    blocked_reason: str | None
    content_loaded: bool
    writes_performed: bool = False
    provider_mutated: bool = False
    model_mutated: bool = False
    auth_mutated: bool = False
    permission_mutated: bool = False
    task_state_mutated: bool = False
    schema: str = MANUS_PACKAGE_SCHEMA

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "status": self.status,
            "host_kind": self.host_kind,
            "mapping_status": self.mapping_status,
            "runtime_status": self.runtime_status,
            "lifecycle_stage": self.lifecycle_stage,
            "capability_id": self.capability_id,
            "source_hash": self.source_hash,
            "entrypoint_hash": self.entrypoint_hash,
            "load_stage": self.load_stage,
            "package_format": self.package_format,
            "files": [item.to_dict() for item in self.files],
            "warnings": list(self.warnings),
            "blocked_reason": self.blocked_reason,
            "content_loaded": self.content_loaded,
            "writes_performed": self.writes_performed,
            "provider_mutated": self.provider_mutated,
            "model_mutated": self.model_mutated,
            "auth_mutated": self.auth_mutated,
            "permission_mutated": self.permission_mutated,
            "task_state_mutated": self.task_state_mutated,
        }

    def canonical_json(self) -> str:
        return _canonical_json(self.to_dict())


@dataclass(frozen=True)
class ManusSkillPackageExport:
    capability_id: str
    package_directory: str
    archive_path: str
    archive_sha256: str
    plan: ManusSkillPackagePlan



def _canonical_json(value: Any) -> str:
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ManusPackageError("SERIALIZATION_INVALID") from exc



def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()



def _safe_relative(value: Any, *, target: bool = False) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ManusPackageError("SERIALIZATION_INVALID")
    candidate = value.strip().replace("\\", "/")
    if candidate.startswith(("/", "~")) or (len(candidate) >= 3 and candidate[1] == ":" and candidate[2] == "/"):
        raise ManusPackageError("OUTPUT_PATH_INVALID" if target else "PATH_TRAVERSAL")
    if ".." in PurePosixPath(candidate).parts:
        raise ManusPackageError("PATH_TRAVERSAL")
    return candidate



def _hash_text(value: str) -> str:
    return _sha256(value.encode("utf-8"))



def _text(value: Any) -> str:
    return value if isinstance(value, str) else ""



def _sha256_is_valid(value: Any) -> bool:
    return isinstance(value, str) and len(value) == _SHA256_LENGTH and all(char in "0123456789abcdefABCDEF" for char in value)



def _manifest_value(manifest: Any, name: str, default: Any = None) -> Any:
    return getattr(manifest, name, default)



def _provenance_payload(manifest: Any, metadata: Mapping[str, Any], ownership_class: str) -> dict[str, Any]:
    provenance = _manifest_value(manifest, "upstream_provenance", {})
    if not isinstance(provenance, Mapping):
        raise ManusPackageError("PROVENANCE_MISSING")
    integration = provenance.get("integration", {})
    if not isinstance(integration, Mapping):
        raise ManusPackageError("PROVENANCE_MISSING")
    required = ("mode", "vendor_path", "snapshot_sha256", "license")
    if any(not provenance.get(key) for key in required):
        raise ManusPackageError("PROVENANCE_MISSING")
    if not _sha256_is_valid(provenance.get("snapshot_sha256")) or not _sha256_is_valid(integration.get("entrypoint_sha256")):
        raise ManusPackageError("PROVENANCE_MISSING")
    return {
        "schema": MANUS_PROVENANCE_SCHEMA,
        "capability_id": _manifest_value(manifest, "capability_id", ""),
        "source_hash": provenance["snapshot_sha256"],
        "entrypoint_hash": integration["entrypoint_sha256"],
        "ownership_class": ownership_class,
        "source": {
            "mode": provenance.get("mode"),
            "implementation": provenance.get("implementation", "UNKNOWN"),
            "vendor_path": _safe_relative(provenance.get("vendor_path")),
            "upstream_repository": provenance.get("upstream_repository", "UNKNOWN"),
            "upstream_commit": provenance.get("upstream_commit", "UNKNOWN"),
            "license": provenance.get("license"),
        },
        "integration": {
            "entrypoint": _safe_relative(integration.get("entrypoint")),
            "load_mode": integration.get("load_mode", "UNKNOWN"),
            "references": [_safe_relative(item) for item in integration.get("references", [])],
            "assets": [_safe_relative(item) for item in integration.get("assets", [])],
            "script_entrypoints": [_safe_relative(item) for item in integration.get("script_entrypoints", [])],
            "network_runtime": False,
            "credentials": False,
            "install_mode": "DISABLED",
            "external_render": "EXPLICIT_ONLY",
        },
        "package": {
            "format": "filesystem-skill",
            "metadata_source": "p2p-capability-registry",
            "runtime_status": MANUS_RUNTIME_STATUS,
        },
    }



def _ownership(target: Mapping[str, Any], role: str) -> str:
    value = target.get("ownership_class", "P2P_PROJECT_MANAGED")
    if isinstance(value, Mapping):
        value = value.get(role, value.get("default", "P2P_PROJECT_MANAGED"))
    if value not in OWNERSHIP_CLASSES:
        raise ManusPackageError("SERIALIZATION_INVALID")
    if value == "HOST_OWNED_PRESERVE":
        raise ManusPackageError("P2P_OWNERSHIP_CONFLICT")
    if value == "OWNER_REVIEW_REQUIRED" and target.get("deployment_requires_review") is True:
        raise ManusPackageError("P2P_OWNERSHIP_REVIEW_REQUIRED")
    return str(value)



def _target_check(target: Mapping[str, Any]) -> None:
    if _text(target.get("host_kind")).lower() != MANUS_HOST_KIND:
        raise ManusPackageError("HOST_KIND_UNKNOWN")
    scope = target.get("host_scope", target.get("scope", ()))
    if isinstance(scope, str):
        scope = (scope,)
    if not isinstance(scope, (list, tuple)) or set(str(item).lower() for item in scope) != {"project"}:
        raise ManusPackageError("HOST_SCOPE_MISMATCH")
    evidence = target.get("host_evidence", target.get("evidence", {}))
    if evidence is not None and not isinstance(evidence, Mapping):
        raise ManusPackageError("SERIALIZATION_INVALID")
    if isinstance(evidence, Mapping):
        status = _text(evidence.get("status")).upper()
        native_format = _text(evidence.get("native_format")).upper()
        if evidence.get("drift") is True or status in {"DRIFT", "CONFLICT", "MISMATCH", "STALE"}:
            raise ManusPackageError("BLOCKED_HOST_DRIFT")
        if native_format in {"AMBIGUOUS", "UNKNOWN_AMBIGUOUS"}:
            raise ManusPackageError("HOST_FORMAT_AMBIGUOUS")
        if native_format and native_format not in {"FILESYSTEM-SKILL", "FILESYSTEM_SKILL", "SKILL"}:
            raise ManusPackageError("HOST_FORMAT_AMBIGUOUS")
    if target.get("mapping_status") == "BLOCKED_HOST_DRIFT":
        raise ManusPackageError("BLOCKED_HOST_DRIFT")



def _entrypoint_content(context: Mapping[str, Any], expected_hash: str) -> tuple[bytes, str]:
    value = context.get("entrypoint_content")
    if isinstance(value, bytes):
        raw = value
        text = value.decode("utf-8")
    elif isinstance(value, str):
        text = value
        raw = value.encode("utf-8")
    else:
        raise ManusPackageError("SERIALIZATION_INVALID")
    if _sha256(raw) != expected_hash:
        raise ManusPackageError("ENTRYPOINT_HASH_MISMATCH")
    declared = context.get("entrypoint_hash", context.get("current_entrypoint_hash"))
    if declared is not None and _text(declared).lower() != expected_hash:
        raise ManusPackageError("ENTRYPOINT_HASH_MISMATCH")
    return raw, text



def _skill_markdown(manifest: Any, content: str) -> str:
    marker = "---"
    lines = content.splitlines()
    try:
        marker_index = next(index for index, line in enumerate(lines) if line.strip() == marker)
    except StopIteration as exc:
        raise ManusPackageError("SERIALIZATION_INVALID") from exc
    body = "\n".join(lines[marker_index + 1:]).lstrip("\n")
    name = _manifest_value(manifest, "capability_id", "")
    description = _manifest_value(manifest, "description", "")
    invocation = _manifest_value(manifest, "invocation_class", "")
    if not name or not _text(description).strip() or not invocation:
        raise ManusPackageError("SERIALIZATION_INVALID")
    metadata = {"p2p_capability_id": name, "p2p_invocation_policy": invocation}
    return "\n".join((
        "---",
        f"name: {json.dumps(str(name), ensure_ascii=False)}",
        f"description: {json.dumps(str(description).strip(), ensure_ascii=False)}",
        f"metadata: {json.dumps(metadata, ensure_ascii=False, sort_keys=True, separators=(',', ':'))}",
        "---",
        "",
        body,
        "",
    ))



def _declared_kind(relative: str, kind: str, metadata: Mapping[str, Any]) -> bool:
    declarations = metadata.get({"reference": "references", "asset": "assets", "script": "script_entrypoints", "template": "templates"}.get(kind, ""), [])
    if not isinstance(declarations, list):
        declarations = list(declarations or ())
    normalized = _safe_relative(relative)
    for item in declarations:
        declared = _safe_relative(item)
        if declared.endswith("/") and normalized.startswith(declared):
            return True
        if normalized == declared:
            return True
    return False



def _deep_files(context: Mapping[str, Any], metadata: Mapping[str, Any], target: Mapping[str, Any]) -> list[ManusPackageFile]:
    values = context.get("deep_load")
    if values is None:
        return []
    if not isinstance(values, (list, tuple)):
        raise ManusPackageError("CONTEXT_EXPANSION_UNAUTHORIZED")
    result: list[ManusPackageFile] = []
    seen: set[str] = set()
    for item in values:
        if not isinstance(item, Mapping) or item.get("requested") is not True:
            raise ManusPackageError("CONTEXT_EXPANSION_UNAUTHORIZED")
        relative = _safe_relative(item.get("relative_path", item.get("path")))
        kind = _text(item.get("kind")).lower()
        if kind not in {"reference", "asset", "script", "template"} or not _declared_kind(relative, kind, metadata):
            raise ManusPackageError("DECLARATION_MISMATCH")
        if relative in seen:
            raise ManusPackageError("SERIALIZATION_INVALID")
        seen.add(relative)
        source_hash = _text(item.get("source_hash")).lower()
        if not _sha256_is_valid(source_hash):
            raise ManusPackageError("SOURCE_HASH_STALE")
        content = item.get("content")
        if isinstance(content, bytes):
            actual_hash = _sha256(content)
            size = len(content)
        elif isinstance(content, str):
            actual_hash = _hash_text(content)
            size = len(content.encode("utf-8"))
        elif content is None:
            actual_hash = source_hash
            size = item.get("size")
        else:
            raise ManusPackageError("SERIALIZATION_INVALID")
        if actual_hash != source_hash:
            raise ManusPackageError("SOURCE_HASH_STALE")
        if kind == "script":
            package_path = f"scripts/{PurePosixPath(relative).name}.json"
            descriptor = {"source_path": relative, "source_hash": source_hash, "size": size, "executable": False}
            result.append(ManusPackageFile(package_path, "script-pointer", source_hash, descriptor, _ownership(target, "scripts")))
            continue
        package_path = relative if kind in {"reference", "template"} else f"assets/{PurePosixPath(relative).name}"
        package_path = _safe_relative(package_path, target=True)
        if kind == "asset":
            if isinstance(content, (bytes, str)):
                result.append(ManusPackageFile(package_path, "asset", source_hash, content, _ownership(target, "assets")))
            else:
                descriptor = {"source_path": relative, "source_hash": source_hash, "size": size}
                result.append(ManusPackageFile(package_path, "asset-pointer", source_hash, descriptor, _ownership(target, "assets")))
        elif isinstance(content, str):
            result.append(ManusPackageFile(package_path, kind, source_hash, content, _ownership(target, kind)))
        else:
            descriptor = {"source_path": relative, "source_hash": source_hash, "size": size}
            result.append(ManusPackageFile(package_path, f"{kind}-pointer", source_hash, descriptor, _ownership(target, kind)))
    return result



def _blocked(capability_id: str = "", source_hash: str = "", entrypoint_hash: str = "", reason: str = "SERIALIZATION_INVALID", load_stage: str = "DISCOVERY") -> ManusSkillPackagePlan:
    return ManusSkillPackagePlan(
        status=BLOCKED,
        host_kind=MANUS_HOST_KIND,
        mapping_status="MAPPING_PLANNED",
        runtime_status=MANUS_RUNTIME_STATUS,
        lifecycle_stage="MAPPING_PLANNED",
        capability_id=capability_id,
        source_hash=source_hash,
        entrypoint_hash=entrypoint_hash,
        load_stage=load_stage,
        package_format="filesystem-skill",
        files=(),
        warnings=(),
        blocked_reason=reason,
        content_loaded=False,
    )



def plan_manus_skill_package(
    capability: Any,
    resolved_context: Mapping[str, Any] | None = None,
    host_target: Mapping[str, Any] | None = None,
    *,
    registry_path: str | Path | None = None,
    repository_root: str | Path | None = None,
) -> ManusSkillPackagePlan:
    """Build a pure Manus package plan without writing or contacting Manus."""
    context = resolved_context if isinstance(resolved_context, Mapping) else {}
    target = host_target if isinstance(host_target, Mapping) else {}
    capability_id = _text(_manifest_value(capability, "capability_id", ""))
    load_stage = _text(context.get("load_stage", "DISCOVERY")).upper()
    try:
        if not is_vendor_skill(capability):
            return _blocked(capability_id, reason="PROVENANCE_MISSING", load_stage=load_stage)
        _target_check(target)
        metadata = vendor_skill_metadata(capability, registry_path=registry_path, repository_root=repository_root)
        source_hash = _text(metadata.get("snapshot_sha256")).lower()
        entrypoint_hash = _text(metadata.get("entrypoint_sha256")).lower()
        if not _sha256_is_valid(source_hash) or not _sha256_is_valid(entrypoint_hash):
            return _blocked(capability_id, source_hash, entrypoint_hash, "PROVENANCE_MISSING", load_stage)
        if context.get("source_hash") is not None and _text(context.get("source_hash")).lower() != source_hash:
            return _blocked(capability_id, source_hash, entrypoint_hash, "SOURCE_HASH_STALE", load_stage)
        if context.get("current_source_hash") is not None and _text(context.get("current_source_hash")).lower() != source_hash:
            return _blocked(capability_id, source_hash, entrypoint_hash, "SOURCE_HASH_STALE", load_stage)
        selected_id = context.get("selected_capability_id")
        if selected_id is not None and selected_id != capability_id:
            return _blocked(capability_id, source_hash, entrypoint_hash, "CAPABILITY_NOT_SELECTED", load_stage)
        if load_stage not in {"DISCOVERY", "MATCH", "LOAD", "DEEP_LOAD"}:
            return _blocked(capability_id, source_hash, entrypoint_hash, "SERIALIZATION_INVALID", load_stage)
        if load_stage in {"LOAD", "DEEP_LOAD"} and context.get("selected") is not True:
            return _blocked(capability_id, source_hash, entrypoint_hash, "CAPABILITY_NOT_SELECTED", load_stage)
        if context.get("full_tree") is True or context.get("include_full_tree") is True:
            return _blocked(capability_id, source_hash, entrypoint_hash, "CONTEXT_EXPANSION_UNAUTHORIZED", load_stage)
        if load_stage == "LOAD" and context.get("deep_load"):
            return _blocked(capability_id, source_hash, entrypoint_hash, "CONTEXT_EXPANSION_UNAUTHORIZED", load_stage)
        ownership = _ownership(target, "skill")
        provenance = _provenance_payload(capability, metadata, ownership)
        provenance_text = _canonical_json(provenance) + "\n"
        materialize_metadata = load_stage in {"LOAD", "DEEP_LOAD"}
        files: list[ManusPackageFile] = [
            ManusPackageFile("SKILL.md", "markdown", None, None, ownership),
            ManusPackageFile(
                "P2P-PROVENANCE.json",
                "json",
                _hash_text(provenance_text) if materialize_metadata else None,
                provenance if materialize_metadata else None,
                ownership,
            ),
        ]
        warnings = ["MAPPING_SUPPORTED", "HOST_RUNTIME_NOT_CERTIFIED", "PROGRESSIVE_DISCLOSURE_PRESERVED"]
        if load_stage == "DISCOVERY":
            warnings.append("DISCOVERY_METADATA_ONLY")
        elif load_stage == "MATCH":
            warnings.append(f"MATCH_ENTRYPOINT_POINTER:{metadata['entrypoint']}")
        else:
            _, entrypoint_text = _entrypoint_content(context, entrypoint_hash)
            skill_text = _skill_markdown(capability, entrypoint_text)
            files[0] = ManusPackageFile("SKILL.md", "markdown", _hash_text(skill_text), skill_text, ownership)
            files.extend(_deep_files(context, metadata, target))
        files.sort(key=lambda item: item.relative_path)
        plan = ManusSkillPackagePlan(
            status=READY,
            host_kind=MANUS_HOST_KIND,
            mapping_status=MANUS_MAPPING_STATUS,
            runtime_status=MANUS_RUNTIME_STATUS,
            lifecycle_stage="MAPPING_SUPPORTED",
            capability_id=capability_id,
            source_hash=source_hash,
            entrypoint_hash=entrypoint_hash,
            load_stage=load_stage,
            package_format="filesystem-skill",
            files=tuple(files),
            warnings=tuple(warnings),
            blocked_reason=None,
            content_loaded=load_stage in {"LOAD", "DEEP_LOAD"},
        )
        plan.canonical_json()
        return plan
    except (AttributeError, TypeError, UnicodeError, VendorSkillError):
        return _blocked(capability_id, reason="SERIALIZATION_INVALID", load_stage=load_stage)
    except ManusPackageError as exc:
        return _blocked(capability_id, reason=str(exc), load_stage=load_stage)



def _output_root(output_dir: str | Path, repository_root: str | Path) -> tuple[Path, Path]:
    repo = Path(repository_root).expanduser().resolve()
    output = Path(output_dir).expanduser().resolve()
    try:
        output.relative_to(repo)
    except ValueError as exc:
        raise ManusPackageError("OUTPUT_PATH_INVALID") from exc
    if output == repo:
        raise ManusPackageError("OUTPUT_PATH_INVALID")
    return repo, output



def _write_bytes(path: Path, content: Any) -> None:
    if isinstance(content, bytes):
        path.write_bytes(content)
    elif isinstance(content, str):
        path.write_text(content, encoding="utf-8", newline="\n")
    else:
        raise ManusPackageError("SERIALIZATION_INVALID")



def _archive(package_directory: Path, archive_path: Path) -> str:
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as handle:
        for path in sorted(item for item in package_directory.rglob("*") if item.is_file()):
            relative = path.relative_to(package_directory).as_posix()
            info = zipfile.ZipInfo(relative, date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            handle.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    return _sha256(archive_path.read_bytes())



def export_manus_skill_package(
    capability: Any,
    output_dir: str | Path,
    *,
    repository_root: str | Path,
    target: Mapping[str, Any] | None = None,
    include_deep_load: Iterable[Mapping[str, Any]] = (),
    registry_path: str | Path | None = None,
) -> ManusSkillPackageExport:
    """Materialize one selected skill under an approved repo-local output path."""
    repo, output = _output_root(output_dir, repository_root)
    target_value = dict(target or {"host_kind": MANUS_HOST_KIND, "scope": "project"})
    capability_id = _text(_manifest_value(capability, "capability_id", ""))
    if not capability_id:
        raise ManusPackageError("SERIALIZATION_INVALID")
    loaded = load_vendor_skill(capability_id, registry_path=registry_path, repository_root=repo)
    metadata = vendor_skill_metadata(capability, registry_path=registry_path, repository_root=repo)
    deep = list(include_deep_load)
    stage = "DEEP_LOAD" if deep else "LOAD"
    context: dict[str, Any] = {
        "load_stage": stage,
        "selected": True,
        "source_hash": metadata["snapshot_sha256"],
        "entrypoint_content": loaded["skill"]["content"],
        "entrypoint_hash": loaded["skill"].get("sha256"),
    }
    if deep:
        context["deep_load"] = deep
    plan = plan_manus_skill_package(
        capability,
        context,
        target_value,
        registry_path=registry_path,
        repository_root=repo,
    )
    if plan.status != READY or not plan.content_loaded:
        raise ManusPackageError(plan.blocked_reason or "PACKAGE_STAGE_REQUIRED")
    package_directory = output / capability_id
    archive_path = output / f"{capability_id}.skill"
    if package_directory.exists() or archive_path.exists():
        raise ManusPackageError("OUTPUT_EXISTS")
    package_directory.mkdir(parents=True, exist_ok=False)
    for item in plan.files:
        if item.content_or_descriptor is None:
            raise ManusPackageError("PACKAGE_STAGE_REQUIRED")
        destination = package_directory / _safe_relative(item.relative_path, target=True)
        destination.parent.mkdir(parents=True, exist_ok=True)
        _write_bytes(destination, item.content_or_descriptor if item.format != "json" or isinstance(item.content_or_descriptor, str) else _canonical_json(item.content_or_descriptor) + "\n")
    archive_hash = _archive(package_directory, archive_path)
    proven_plan = replace(plan, lifecycle_stage="PACKAGE_FORMAT_PROVEN")
    return ManusSkillPackageExport(capability_id, str(package_directory), str(archive_path), archive_hash, proven_plan)


__all__ = [
    "BLOCKED",
    "MANUS_HOST_KIND",
    "MANUS_LIFECYCLE",
    "MANUS_MAPPING_STATUS",
    "MANUS_PACKAGE_SCHEMA",
    "MANUS_PROVENANCE_SCHEMA",
    "MANUS_RUNTIME_STATUS",
    "ManusPackageError",
    "ManusPackageFile",
    "ManusSkillPackageExport",
    "ManusSkillPackagePlan",
    "OWNERSHIP_CLASSES",
    "READY",
    "REASON_CODES",
    "export_manus_skill_package",
    "plan_manus_skill_package",
]
