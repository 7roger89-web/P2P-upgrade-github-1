"""Pure, deterministic projection of selected P2P skill data into host plans."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any, Mapping

from .model import CapabilityManifest


INPUT_SCHEMA = "p2p-host-skill-projection-input/1"
PLAN_SCHEMA = "p2p-host-skill-projection-plan/1"
READY, BLOCKED = "READY", "BLOCKED"
HOST_KINDS = ("codex", "claude", "gemini", "cursor", "copilot", "antigravity")
LOAD_STAGES = ("DISCOVERY", "MATCH", "LOAD", "DEEP_LOAD")
INVOCATION_POLICIES = ("USER_REQUESTED", "MODEL_ROUTABLE", "GOVERNANCE_MANDATED")
OWNERSHIP_CLASSES = ("P2P_PROJECT_MANAGED", "HOST_OWNED_PRESERVE", "OWNER_REVIEW_REQUIRED")
MAPPING_STATUSES = ("MAPPING_SUPPORTED", "MAPPING_PLANNED", "HOST_UNKNOWN", "BLOCKED_HOST_DRIFT")
REASON_CODES = ("HOST_KIND_UNKNOWN", "PROVENANCE_MISSING", "SOURCE_HASH_STALE", "ENTRYPOINT_HASH_MISMATCH", "PATH_TRAVERSAL", "ABSOLUTE_TARGET_PATH", "INVOCATION_POLICY_UNSUPPORTED", "HOST_FORMAT_AMBIGUOUS", "BLOCKED_HOST_DRIFT", "SERIALIZATION_INVALID", "P2P_OWNERSHIP_CONFLICT", "CAPABILITY_NOT_SELECTED", "CONTEXT_EXPANSION_UNAUTHORIZED", "COPILOT_SCOPE_REQUIRED", "P2P_OWNERSHIP_REVIEW_REQUIRED", "MISSING_APPROVAL_BOUNDARY", "HOST_SCOPE_MISMATCH")
_SHA256 = re.compile(r"^[0-9a-fA-F]{64}$")
_HOSTS: dict[str, dict[str, Any]] = {
    "codex": {"status": "MAPPING_SUPPORTED", "implicit": True, "targets": (("skill", ".agents/skills/{id}/SKILL.md", "markdown"), ("metadata", ".agents/skills/{id}/agents/openai.yaml", "yaml"))},
    "claude": {"status": "MAPPING_PLANNED", "implicit": False, "targets": (("skill", ".claude/skills/{id}/SKILL.md", "claude-markdown"),)},
    "gemini": {"status": "MAPPING_PLANNED", "implicit": False, "targets": (("skill", ".gemini/skills/{id}/SKILL.md", "gemini-markdown"),)},
    "cursor": {"status": "MAPPING_PLANNED", "implicit": False, "targets": (("skill", ".cursor/rules/{id}.mdc", "cursor-mdc"),)},
    "copilot": {"status": "MAPPING_PLANNED", "implicit": False, "targets": (("skill", ".github/instructions/{id}.instructions.md", "copilot-instructions"),)},
}


def canonical_json(value: Any) -> str:
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ValueError("SERIALIZATION_INVALID") from exc


def _hash(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _tuple(value: Any) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value,) if value.strip() else ()
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(item for item in value if isinstance(item, str) and item.strip())


def _get(value: Mapping[str, Any], *names: str, default: Any = None) -> Any:
    for name in names:
        if name in value:
            return value[name]
    return default


def _text(value: Any) -> str:
    return value if isinstance(value, str) else ""


def _display(skill_id: str) -> str:
    return " ".join(part[:1].upper() + part[1:] for part in re.split(r"[._-]+", skill_id) if part)


def _clean(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


@dataclass(frozen=True)
class HostSkillProjectionInput:
    skill_id: str; display_name: str; description: str; invocation_class: str; invocation_policy: str
    context_entrypoint: str; context_refs: tuple[str, ...]; provenance: Mapping[str, Any] | None
    source_hash: str; entrypoint_hash: str; host_kind: str; host_scope: tuple[str, ...]
    approval_boundary: tuple[str, ...]; trust_level: str; load_stage: str
    schema: str = INPUT_SCHEMA

    def to_dict(self) -> dict[str, Any]:
        return {"schema": self.schema, "skill_id": self.skill_id, "display_name": self.display_name, "description": self.description, "invocation_class": self.invocation_class, "invocation_policy": self.invocation_policy, "context_entrypoint": self.context_entrypoint, "context_refs": list(self.context_refs), "provenance": dict(self.provenance) if isinstance(self.provenance, Mapping) else self.provenance, "source_hash": self.source_hash, "entrypoint_hash": self.entrypoint_hash, "host_kind": self.host_kind, "host_scope": list(self.host_scope), "approval_boundary": list(self.approval_boundary), "trust_level": self.trust_level, "load_stage": self.load_stage}


@dataclass(frozen=True)
class HostProjectionFile:
    relative_target: str; format: str; content_hash: str | None; content_or_template: Any; ownership_class: str

    def to_dict(self) -> dict[str, Any]:
        return {"relative_target": self.relative_target, "format": self.format, "content_hash": self.content_hash, "content_or_template": self.content_or_template, "ownership_class": self.ownership_class}


@dataclass(frozen=True)
class HostProjectionPlan:
    status: str; host_kind: str; capability_id: str; source_hash: str; entrypoint_hash: str
    load_stage: str; files: tuple[HostProjectionFile, ...]; warnings: tuple[str, ...]
    blocked_reason: str | None; content_loaded: bool
    writes_performed: bool = False; provider_mutated: bool = False; model_mutated: bool = False
    auth_mutated: bool = False; permission_mutated: bool = False; task_state_mutated: bool = False
    schema: str = PLAN_SCHEMA

    def to_dict(self) -> dict[str, Any]:
        return {"schema": self.schema, "status": self.status, "host_kind": self.host_kind, "capability_id": self.capability_id, "source_hash": self.source_hash, "entrypoint_hash": self.entrypoint_hash, "load_stage": self.load_stage, "files": [item.to_dict() for item in self.files], "warnings": list(self.warnings), "blocked_reason": self.blocked_reason, "content_loaded": self.content_loaded, "writes_performed": self.writes_performed, "provider_mutated": self.provider_mutated, "model_mutated": self.model_mutated, "auth_mutated": self.auth_mutated, "permission_mutated": self.permission_mutated, "task_state_mutated": self.task_state_mutated}

    def canonical_json(self) -> str:
        return canonical_json(self.to_dict())


def _raw_capability(capability: Any) -> Mapping[str, Any]:
    if isinstance(capability, CapabilityManifest):
        return capability.raw
    return capability if isinstance(capability, Mapping) else {}


def _normalise(capability: Any, context: Mapping[str, Any], target: Mapping[str, Any]) -> HostSkillProjectionInput:
    if isinstance(capability, HostSkillProjectionInput):
        return capability
    raw = _raw_capability(capability)
    provenance = _get(raw, "provenance", "UPSTREAM_PROVENANCE")
    provenance = provenance if isinstance(provenance, Mapping) else None
    integration = provenance.get("integration", {}) if provenance else {}
    integration = integration if isinstance(integration, Mapping) else {}
    skill_id = _text(_get(raw, "skill_id", "CAPABILITY_ID"))
    refs = list(_tuple(_get(raw, "context_refs", "CONTEXT_POINTERS", default=())))
    for key in ("references", "assets", "script_entrypoints"):
        refs.extend(_tuple(integration.get(key)))
    refs = tuple(dict.fromkeys(refs))
    host_kind = _text(target.get("host_kind")).lower()
    host_scope = _tuple(_get(target, "host_scope", "scope", default=()))
    invocation = _text(_get(raw, "invocation_class", "INVOCATION_CLASS"))
    return HostSkillProjectionInput(skill_id, _text(_get(raw, "display_name", "DISPLAY_NAME", default=_display(skill_id))), _text(_get(raw, "description", "DESCRIPTION")), invocation, _text(_get(raw, "invocation_policy", "INVOCATION_POLICY", default=invocation)), _text(_get(raw, "context_entrypoint", "CONTEXT_ENTRYPOINT", default=integration.get("entrypoint", ""))), refs, provenance, _text(_get(raw, "source_hash", "SOURCE_HASH", default=provenance.get("snapshot_sha256") if provenance else "")).lower(), _text(_get(raw, "entrypoint_hash", "ENTRYPOINT_HASH", default=integration.get("entrypoint_sha256"))).lower(), host_kind, host_scope, _tuple(_get(raw, "approval_boundary", "APPROVAL_BOUNDARY", default=())), _text(_get(raw, "trust_level", "TRUST_LEVEL")), _text(_get(context, "load_stage", default=_get(target, "load_stage", default="DISCOVERY"))).upper(), _text(_get(raw, "schema", "SCHEMA", default=INPUT_SCHEMA)) or INPUT_SCHEMA)


def _blocked(item: HostSkillProjectionInput | None, reason: str, warnings: tuple[str, ...] = ()) -> HostProjectionPlan:
    item = item or HostSkillProjectionInput("", "", "", "", "", "", (), None, "", "", "UNKNOWN", (), (), "", "DISCOVERY")
    return HostProjectionPlan(BLOCKED, item.host_kind or "UNKNOWN", item.skill_id, item.source_hash, item.entrypoint_hash, item.load_stage or "DISCOVERY", (), warnings, reason, False)


def _relative(value: Any, *, target: bool = False) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("SERIALIZATION_INVALID")
    value = value.strip().replace("\\", "/")
    if value.startswith(("/", "~")) or re.match(r"^[A-Za-z]:/", value):
        raise ValueError("ABSOLUTE_TARGET_PATH" if target else "PATH_TRAVERSAL")
    if ".." in PurePosixPath(value).parts:
        raise ValueError("PATH_TRAVERSAL")
    return value


def _provenance(item: HostSkillProjectionInput) -> str | None:
    p = item.provenance
    if not isinstance(p, Mapping) or not p:
        return "PROVENANCE_MISSING"
    path = p.get("vendor_path") or p.get("source_path") or p.get("path")
    if not path or not (p.get("source_class") or p.get("mode") or p.get("implementation")) or not p.get("license"):
        return "PROVENANCE_MISSING"
    try:
        _relative(path)
    except ValueError:
        return "PROVENANCE_MISSING"
    integration = p.get("integration", {})
    expected_entry = _text(integration.get("entrypoint_sha256")).lower() if isinstance(integration, Mapping) else ""
    if _text(p.get("snapshot_sha256")).lower() not in ("", item.source_hash):
        return "SOURCE_HASH_STALE"
    if expected_entry not in ("", item.entrypoint_hash):
        return "ENTRYPOINT_HASH_MISMATCH"
    return None


def _core(item: HostSkillProjectionInput) -> str | None:
    if item.schema != INPUT_SCHEMA:
        return "SERIALIZATION_INVALID"
    try:
        if not item.skill_id or not item.display_name.strip() or not item.description.strip():
            return "SERIALIZATION_INVALID"
        _relative(item.skill_id)
        _relative(item.context_entrypoint)
        for ref in item.context_refs:
            _relative(ref)
    except (AttributeError, ValueError) as exc:
        return str(exc) if str(exc) in REASON_CODES else "SERIALIZATION_INVALID"
    if item.load_stage not in LOAD_STAGES:
        return "SERIALIZATION_INVALID"
    if item.invocation_policy not in INVOCATION_POLICIES or item.invocation_class != item.invocation_policy:
        return "INVOCATION_POLICY_UNSUPPORTED"
    if not item.trust_level or not item.host_scope:
        return "HOST_SCOPE_MISMATCH"
    if not item.approval_boundary:
        return "MISSING_APPROVAL_BOUNDARY"
    if not _SHA256.fullmatch(item.source_hash) or not _SHA256.fullmatch(item.entrypoint_hash):
        return "PROVENANCE_MISSING"
    return None


def _target_check(item: HostSkillProjectionInput, target: Mapping[str, Any]) -> str | None:
    requested = _text(target.get("host_kind")).lower()
    if not requested or requested != item.host_kind:
        return "HOST_SCOPE_MISMATCH"
    requested_scope = {value.lower() for value in _tuple(_get(target, "host_scope", "scope", default=()))}
    if "project" not in requested_scope or requested_scope & {"global", "user", "home", "workspace-global"}: return "HOST_SCOPE_MISMATCH"
    scope = {value.lower() for value in item.host_scope}
    if "project" not in scope or scope & {"global", "user", "home", "workspace-global"}:
        return "HOST_SCOPE_MISMATCH"
    allowed = target.get("allowed_hosts")
    if allowed is not None and (not isinstance(allowed, (list, tuple)) or item.host_kind not in {str(value).lower() for value in allowed}):
        return "HOST_SCOPE_MISMATCH"
    evidence = target.get("host_evidence") if "host_evidence" in target else target.get("evidence", {})
    if not isinstance(evidence, Mapping):
        return "SERIALIZATION_INVALID"
    status = str(evidence.get("status", "")).upper()
    mapping = str(target.get("mapping_status", evidence.get("mapping_status", ""))).upper()
    if evidence.get("drift") is True or status in {"DRIFT", "CONFLICT", "MISMATCH", "STALE"} or mapping == "BLOCKED_HOST_DRIFT":
        return "BLOCKED_HOST_DRIFT"
    if str(target.get("native_format", evidence.get("native_format", ""))).upper() in {"AMBIGUOUS", "UNKNOWN_AMBIGUOUS"}:
        return "HOST_FORMAT_AMBIGUOUS"
    if item.host_kind == "copilot":
        apply_to = target.get("apply_to")
        if not isinstance(apply_to, str) or not apply_to.strip() or apply_to.strip() == "**" or apply_to.startswith(("/", "~")) or re.match(r"^[A-Za-z]:[/\\]", apply_to):
            return "COPILOT_SCOPE_REQUIRED"
    existing = target.get("existing_ownership", {})
    conflict = target.get("ownership_conflict") is True
    if isinstance(existing, Mapping):
        conflict = conflict or "HOST_OWNED_PRESERVE" in existing.values()
    else:
        conflict = conflict or existing == "HOST_OWNED_PRESERVE"
    return "P2P_OWNERSHIP_CONFLICT" if conflict else None


def _paths(item: HostSkillProjectionInput, target: Mapping[str, Any], host: Mapping[str, Any]) -> list[tuple[str, str, str]]:
    overrides = target.get("target_paths", {})
    if not isinstance(overrides, Mapping):
        raise ValueError("SERIALIZATION_INVALID")
    return [(role, _relative(overrides.get(role, template.format(id=item.skill_id)), target=True), fmt) for role, template, fmt in host["targets"]]


def _entrypoint(context: Mapping[str, Any], item: HostSkillProjectionInput) -> tuple[bytes, str]:
    value = context.get("entrypoint_content")
    if isinstance(value, bytes):
        raw, text = value, value.decode("utf-8")
    elif isinstance(value, str):
        text, raw = value, value.encode("utf-8")
    else:
        raise ValueError("SERIALIZATION_INVALID")
    current = context.get("entrypoint_hash") or context.get("current_entrypoint_hash")
    if _hash(raw) != item.entrypoint_hash or (current is not None and _text(current).lower() != item.entrypoint_hash):
        raise ValueError("ENTRYPOINT_HASH_MISMATCH")
    return raw, text


def _owner(target: Mapping[str, Any], role: str, path: str) -> str:
    value = target.get("ownership_class", "P2P_PROJECT_MANAGED")
    if isinstance(value, Mapping):
        value = value.get(path, value.get(role, "P2P_PROJECT_MANAGED"))
    if value not in OWNERSHIP_CLASSES:
        raise ValueError("SERIALIZATION_INVALID")
    if value == "OWNER_REVIEW_REQUIRED" and target.get("deployment_requires_review") is True:
        raise ValueError("P2P_OWNERSHIP_REVIEW_REQUIRED")
    return str(value)


def _implicit(item: HostSkillProjectionInput, target: Mapping[str, Any], host: Mapping[str, Any]) -> bool:
    if item.invocation_policy != "MODEL_ROUTABLE":
        return False
    value = target.get("supports_implicit_invocation", host["implicit"])
    if type(value) is not bool:
        raise ValueError("INVOCATION_POLICY_UNSUPPORTED")
    return value


def _yaml(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, allow_nan=False)


def _codex_metadata(item: HostSkillProjectionInput, implicit: bool) -> str:
    return "\n".join(("interface:", f"  display_name: {_yaml(_clean(item.display_name))}", f"  short_description: {_yaml(_clean(item.description))}", f"  allow_implicit_invocation: {'true' if implicit else 'false'}", ""))


def _planned_skill(item: HostSkillProjectionInput, content: str) -> str:
    return "\n".join(("---", f"name: {_yaml(item.skill_id)}", f"description: {_yaml(_clean(item.description))}", f"invocation_policy: {_yaml(item.invocation_policy)}", "---", "", content))


def _deep(item: HostSkillProjectionInput, target: Mapping[str, Any], base: str, values: Any) -> list[HostProjectionFile]:
    if values is None:
        return []
    if not isinstance(values, (list, tuple)):
        raise ValueError("CONTEXT_EXPANSION_UNAUTHORIZED")
    declared = set(item.context_refs) | set(_tuple(target.get("declared_context_refs")))
    result: list[HostProjectionFile] = []
    for value in values:
        if not isinstance(value, Mapping) or value.get("requested") is not True: raise ValueError("CONTEXT_EXPANSION_UNAUTHORIZED")
        relative = _relative(value.get("relative_path", value.get("path")))
        permitted = any(relative == ref or ref.endswith("/") and relative.startswith(ref) or ref.endswith(":references") and relative.startswith("references/") for ref in declared)
        if relative == item.context_entrypoint or not permitted: raise ValueError("CONTEXT_EXPANSION_UNAUTHORIZED")
        source_hash, content = _text(value.get("source_hash")).lower(), value.get("content")
        if not _SHA256.fullmatch(source_hash): raise ValueError("SOURCE_HASH_STALE")
        if isinstance(content, bytes): actual, template = _hash(content), {"source_path": relative, "source_hash": source_hash, "size": len(content), "executable": False}
        elif isinstance(content, str):
            actual, template = _hash(content.encode("utf-8")), content
        elif content is None: actual, template = source_hash, {"source_path": relative, "source_hash": source_hash, "executable": False}
        else:
            raise ValueError("SERIALIZATION_INVALID")
        if actual != source_hash: raise ValueError("SOURCE_HASH_STALE")
        path = _relative(f"{base}/{relative}", target=True); fmt = "script-pointer" if str(value.get("kind", "")).lower() == "script" else "context"; result.append(HostProjectionFile(path, fmt, actual, template, _owner(target, "context", path)))
    return result


def project_host_skill(capability: Any, resolved_context: Mapping[str, Any] | None = None, host_target: Mapping[str, Any] | None = None) -> HostProjectionPlan:
    """Build a pure plan from selected P2P data, resolved context, and host target."""
    context = resolved_context if isinstance(resolved_context, Mapping) else {}; target = host_target if isinstance(host_target, Mapping) else {}
    item: HostSkillProjectionInput | None = None
    try:
        item = _normalise(capability, context, target)
        if item.host_kind not in HOST_KINDS or item.host_kind == "antigravity": return _blocked(item, "HOST_KIND_UNKNOWN")
        reason = _provenance(item) or _core(item) or _target_check(item, target)
        if reason: return _blocked(item, reason)
        current_source = context.get("source_hash") or context.get("current_source_hash")
        if current_source is not None and _text(current_source).lower() != item.source_hash: return _blocked(item, "SOURCE_HASH_STALE")
        host = _HOSTS[item.host_kind]
        warnings = [str(host["status"])]
        if host["status"] == "MAPPING_PLANNED": warnings.append("MAPPING_PLANNED_NOT_RUNTIME_CERTIFIED")
        if item.load_stage == "DISCOVERY": warnings.append("DISCOVERY_METADATA_ONLY")
        elif item.load_stage == "MATCH": warnings.append(f"MATCH_ENTRYPOINT_POINTER:{item.context_entrypoint}")
        selected = context.get("selected")
        selected_id = context.get("selected_capability_id")
        if selected_id is not None and selected_id != item.skill_id: return _blocked(item, "CAPABILITY_NOT_SELECTED", tuple(warnings))
        if context.get("full_tree") is True or context.get("include_full_tree") is True: return _blocked(item, "CONTEXT_EXPANSION_UNAUTHORIZED", tuple(warnings))
        deep_values = context.get("deep_load")
        if item.load_stage == "LOAD" and deep_values: return _blocked(item, "CONTEXT_EXPANSION_UNAUTHORIZED", tuple(warnings))
        content_raw = content_text = None
        if item.load_stage in {"LOAD", "DEEP_LOAD"}:
            if selected is not True: return _blocked(item, "CAPABILITY_NOT_SELECTED", tuple(warnings))
            content_raw, content_text = _entrypoint(context, item)
        paths, implicit, files = _paths(item, target, host), _implicit(item, target, host), []
        for role, path, fmt in paths:
            owner = _owner(target, role, path)
            if item.load_stage in {"DISCOVERY", "MATCH"}:
                content_hash, template = None, None
            elif role == "metadata" and item.host_kind == "codex":
                template, content_hash = _codex_metadata(item, implicit), None
                content_hash = _hash(template.encode("utf-8"))
            else:
                assert content_raw is not None and content_text is not None
                template = content_text if item.host_kind == "codex" else _planned_skill(item, content_text)
                content_hash = _hash(content_raw if item.host_kind == "codex" else template.encode("utf-8"))
            files.append(HostProjectionFile(path, fmt, content_hash, template, owner))
        if item.load_stage == "DEEP_LOAD":
            base = f".agents/skills/{item.skill_id}" if item.host_kind == "codex" else paths[0][1].rsplit("/", 1)[0]
            files.extend(_deep(item, target, base, deep_values))
            warnings.append("DEEP_LOAD_EXPLICIT_DECLARED_ONLY")
        plan = HostProjectionPlan(READY, item.host_kind, item.skill_id, item.source_hash, item.entrypoint_hash, item.load_stage, tuple(files), tuple(warnings), None, item.load_stage in {"LOAD", "DEEP_LOAD"})
        canonical_json(plan.to_dict())
        return plan
    except (TypeError, AttributeError, KeyError, UnicodeError):
        return _blocked(item, "SERIALIZATION_INVALID")
    except ValueError as exc:
        return _blocked(item, str(exc) if str(exc) in REASON_CODES else "SERIALIZATION_INVALID")


__all__ = [
    "BLOCKED", "HOST_KINDS", "INPUT_SCHEMA", "LOAD_STAGES", "MAPPING_STATUSES",
    "OWNERSHIP_CLASSES", "PLAN_SCHEMA", "READY", "REASON_CODES",
    "HostProjectionFile", "HostProjectionPlan", "HostSkillProjectionInput",
    "canonical_json", "project_host_skill",
]
