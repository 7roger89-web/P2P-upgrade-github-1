"""P2P-native decision trace over the existing execution ledger.

The trace is deliberately a small reference projection. It does not replace
Goal, FACT_LEDGER, approval, trust, routing, or execution-ledger authority.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping


TRACE_SCHEMA = "p2p-decision-trace/1"
QUERY_SCHEMA = "p2p-decision-trace-query/1"
TRACE_EVENT = "decision_trace_record"
LEDGER_RELATIVE_PATH = ".p2p/state/execution-ledger.jsonl"
DECISION_TYPES = (
    "ARCHITECTURE",
    "PRODUCT",
    "SECURITY",
    "DATA",
    "DESIGN",
    "DEPENDENCY",
    "MIGRATION",
    "DEPLOYMENT",
    "GOVERNANCE",
    "EXCEPTION",
    "OTHER_MATERIAL",
)
TRACE_STATUSES = (
    "RECORDED",
    "PENDING_APPROVAL",
    "APPROVED",
    "REJECTED",
    "SUPERSEDED",
    "CONTRADICTED",
    "PARTIAL",
    "UNKNOWN",
)
REFERENCE_FIELDS = (
    "FACT_REFS",
    "EVIDENCE_REFS",
    "SOURCE_REFS",
    "CONSTRAINT_REFS",
    "POLICY_REFS",
    "CHANGE_REFS",
    "ARTIFACT_REFS",
)
RELATION_FIELDS = ("SUPERSEDES", "SUPERSEDED_BY", "CONTRADICTS")
RELATIONSHIP_TYPES = ("SUPPORTS", "CONTRADICTS", "UNKNOWN")
CANONICAL_IDENTITIES = (
    "p2p_iris",
    "p2p_tecton",
    "p2p_axiom",
    "p2p_vector",
    "p2p_datos",
    "p2p_anon",
    "p2p_architecton",
    "p2p_helios",
)
CANONICAL_DENOMINATOR = 8
SUPPORTING_SPECIALISTS = {"p2p_aesthetica"}
GOVERNANCE_REFERENCE_PREFIX = "governance/"
_GOVERNANCE_PATH_PREFIXES = (
    ".p2p/system/governance/",
    "governance/",
)

_SENSITIVE_PATTERNS = (
    re.compile(r"(?i)\b(?:sk|pk|rk)-[A-Za-z0-9_-]{12,}\b"),
    re.compile(r"(?i)\b(?:ghp|github_pat|xoxb|xoxp|glpat)-[A-Za-z0-9_-]{12,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._-]{12,}\b"),
    re.compile(r"(?i)\b(?:api[_-]?key|access[_-]?token|secret|password|credential)\s*[:=]\s*[^\s,;]+"),
)
_PRIVATE_TERMS = re.compile(
    r"(?i)\b(?:chain[_ -]?of[_ -]?thought|private[_ -]?reasoning|scratchpad|raw[_ -]?prompt|full[_ -]?prompt|hidden[_ -]?deliberation)\b"
)
_MATERIAL_TERMS = {
    "ARCHITECTURE": ("architecture", "architectural", "kiến trúc", "topology"),
    "PRODUCT": ("product decision", "business rule", "retention", "persona", "product", "nghiệp vụ"),
    "SECURITY": ("security", "auth", "permission", "privacy", "secret", "bảo mật", "quyền"),
    "DATA": ("data policy", "database", "data model", "retention", "pii", "dữ liệu"),
    "DESIGN": ("design system", "ui", "ux", "accessibility", "visual", "thiết kế"),
    "DEPENDENCY": ("dependency", "package", "provider", "framework", "phụ thuộc"),
    "MIGRATION": ("migration", "migrate", "schema change", "migrate", "di trú"),
    "DEPLOYMENT": ("deployment", "deploy", "release", "publish", "production", "triển khai"),
    "GOVERNANCE": ("governance", "approval", "policy", "quorum", "approval boundary", "decision", "decision trace", "choose", "select", "quản trị"),
    "EXCEPTION": ("exception", "override", "waiver", "ngoại lệ"),
}
_PROTECTED_DECISION_TERMS = (
    "release",
    "deploy",
    "publish",
    "promote",
    "approval",
    "approve",
    "destructive",
    "delete",
    "migration",
    "migrate",
    "external",
    "connector",
    "secret",
)


class DecisionTraceError(ValueError):
    """A safe, user-facing trace contract error."""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _stable_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256(value: object) -> str:
    return hashlib.sha256(_stable_json(value).encode("utf-8")).hexdigest()


def _safe_text(value: object) -> tuple[str, bool]:
    text = str(value)
    changed = False
    if _PRIVATE_TERMS.search(text):
        text = _PRIVATE_TERMS.sub("[REDACTED_PRIVATE_REASONING]", text)
        changed = True
    for pattern in _SENSITIVE_PATTERNS:
        replaced = pattern.sub("[REDACTED_SECRET]", text)
        changed = changed or replaced != text
        text = replaced
    return text, changed


def _sanitize(value: object, path: str = "") -> tuple[object, list[str]]:
    if isinstance(value, str):
        safe, changed = _safe_text(value)
        return safe, [path or "value"] if changed else []
    if isinstance(value, list):
        result: list[object] = []
        fields: list[str] = []
        for index, item in enumerate(value):
            safe, changed_fields = _sanitize(item, f"{path}[{index}]")
            result.append(safe)
            fields.extend(changed_fields)
        return result, fields
    if isinstance(value, dict):
        result: dict[str, object] = {}
        fields: list[str] = []
        for key, item in value.items():
            key_text = str(key)
            if _PRIVATE_TERMS.search(key_text) or re.search(r"(?i)(?:api[_-]?key|token|password|secret|credential)", key_text):
                result[key_text] = "[REDACTED_SECRET]"
                fields.append(f"{path}.{key_text}" if path else key_text)
                continue
            safe, changed_fields = _sanitize(item, f"{path}.{key_text}" if path else key_text)
            result[key_text] = safe
            fields.extend(changed_fields)
        return result, fields
    return value, []


def _unique_strings(values: Iterable[object] | None) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()
    for value in values or []:
        if value is None:
            continue
        text, _ = _safe_text(value)
        text = text.strip()
        if text and text not in seen:
            output.append(text)
            seen.add(text)
    return output


def _as_list(value: object) -> list[object]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _root_path(root: str | Path) -> Path:
    path = Path(root).expanduser().resolve()
    if not path.is_dir():
        raise DecisionTraceError(f"Project directory does not exist: {path}")
    return path


def ledger_path(root: str | Path) -> Path:
    return _root_path(root) / LEDGER_RELATIVE_PATH.replace("/", "/")


def _relative_path(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def _read_json(path: Path) -> object | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None


def _canonical_policy_relative_reference(reference: object) -> str | None:
    """Return a safe path relative to the governed policy root.

    POLICY_REFS deliberately has a smaller path language than ordinary
    evidence references.  It accepts a portable relative path, an explicit
    logical ``governance/`` prefix, or the installed-tree prefix for legacy
    records.  It never resolves a drive, home directory, traversal, or URI.
    """
    if reference is None:
        return None
    text, _ = _safe_text(reference)
    text = text.strip().replace("\\", "/")
    while text.startswith("./"):
        text = text[2:]
    if not text or text.startswith(("/", "~")) or re.match(r"^[A-Za-z]:/", text):
        return None
    for prefix in _GOVERNANCE_PATH_PREFIXES:
        if text.startswith(prefix):
            text = text[len(prefix):]
            break
    parts = text.split("/")
    if not parts or any(not part or part in {".", ".."} or ":" in part for part in parts):
        return None
    return "/".join(parts)


def _normalize_policy_references(values: Iterable[object] | None) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()
    for value in values or []:
        if value is None:
            continue
        relative = _canonical_policy_relative_reference(value)
        if relative is None:
            raise DecisionTraceError(
                "POLICY_REFS must use a portable relative governance reference"
            )
        canonical = f"{GOVERNANCE_REFERENCE_PREFIX}{relative}"
        if canonical not in seen:
            output.append(canonical)
            seen.add(canonical)
    return output


def _governance_roots(root: Path) -> list[Path]:
    candidates = [root / ".p2p" / "system" / "governance", root / "governance"]
    return [path for path in candidates if (path / "fact-ledger.json").is_file()]


def _reference_catalog(root: Path, events: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    catalog: dict[str, dict[str, object]] = {}

    def add(ref: object, **metadata: object) -> None:
        if not isinstance(ref, str) or not ref.strip():
            return
        catalog.setdefault(ref.strip(), {}).update(metadata)

    for relative in (
        ".p2p/project-profile.json",
        ".p2p/project-policy.json",
        ".p2p/state/goal-contract.json",
        ".p2p/state/project-status.json",
        ".p2p/state/trusted-evidence.json",
        LEDGER_RELATIVE_PATH,
    ):
        if (root / relative).is_file():
            add(relative, kind="project_state", status="PRESENT")
    all_events: list[dict[str, object]] = []
    ledger = root / LEDGER_RELATIVE_PATH
    if ledger.is_file():
        try:
            for line in ledger.read_text(encoding="utf-8").splitlines():
                try:
                    value = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(value, dict):
                    all_events.append(value)
        except (OSError, UnicodeError):
            all_events = []
    all_events.extend(dict(item.get("raw", {})) for item in events if isinstance(item.get("raw"), dict))
    for event in all_events:
        raw = event.get("raw", {})
        if not isinstance(raw, dict) or not raw:
            raw = event
        trace = event.get("trace")
        if isinstance(trace, dict):
            decision_id = trace.get("DECISION_ID")
            if decision_id:
                add(str(decision_id), kind="decision", status="PRESENT")
                add(f"decision:{decision_id}", kind="decision", status="PRESENT")
        for key in ("run_id", "goal_id", "event_id"):
            value = raw.get(key)
            if value:
                add(str(value), kind=key, status="PRESENT")
                add(f"{key.removesuffix('_id')}:{value}", kind=key, status="PRESENT")
        for key in ("report_json", "report_markdown", "ledger", "contract", "capsule"):
            if raw.get(key):
                reference = str(raw[key])
                add(reference, kind="artifact", status="PRESENT")
                if (root / reference).is_file():
                    add(reference, kind="artifact", status="PRESENT")

    for governance in _governance_roots(root):
        ledger = _read_json(governance / "fact-ledger.json")
        if isinstance(ledger, dict):
            for claim in ledger.get("claims", []):
                if not isinstance(claim, dict):
                    continue
                claim_id = claim.get("claim_id")
                if claim_id:
                    add(str(claim_id), kind="fact", status="PRESENT", checked_at=claim.get("checked_at"), expires_at=claim.get("expires_at"))
                    add(f"fact:{claim_id}", kind="fact", status="PRESENT", checked_at=claim.get("checked_at"), expires_at=claim.get("expires_at"))
                if claim.get("source_url"):
                    add(str(claim["source_url"]), kind="source", status="PRESENT", checked_at=claim.get("checked_at"), expires_at=claim.get("expires_at"))
    return catalog


def _resolve_policy_reference(root: Path, reference: str) -> dict[str, object]:
    ref = str(reference).strip()
    relative = _canonical_policy_relative_reference(ref)
    if relative is None:
        return {
            "REF": ref,
            "STATUS": "MISSING_REFERENCE",
            "DETAIL": "policy reference is not a safe governed logical reference",
        }
    normalized = f"{GOVERNANCE_REFERENCE_PREFIX}{relative}"
    for governance in _governance_roots(root):
        candidate = (governance / Path(*relative.split("/"))).resolve()
        try:
            safe = candidate.is_relative_to(governance.resolve())
        except AttributeError:
            safe = str(candidate).startswith(str(governance.resolve()))
        except ValueError:
            safe = False
        if safe and candidate.is_file():
            detail = "policy reference resolved from governed local state"
            if ref != normalized:
                detail = "legacy policy reference normalized and resolved from governed local state"
            return {
                "REF": ref,
                "NORMALIZED_REF": normalized,
                "STATUS": "PRESENT",
                "KIND": "policy",
                "DETAIL": detail,
            }
    return {
        "REF": ref,
        "NORMALIZED_REF": normalized,
        "STATUS": "MISSING_REFERENCE",
        "DETAIL": "policy reference was not found in governed policy roots",
    }


def _resolve_reference(
    root: Path,
    reference: str,
    catalog: Mapping[str, Mapping[str, object]],
    *,
    field: str | None = None,
) -> dict[str, object]:
    ref = str(reference).strip()
    if field == "POLICY_REFS":
        return _resolve_policy_reference(root, ref)
    metadata = dict(catalog.get(ref, {}))
    if not metadata and ref.startswith("fact:"):
        metadata = dict(catalog.get(ref[5:], {}))
    if not metadata and ref.startswith("artifact:"):
        metadata = dict(catalog.get(ref[9:], {}))
    if not metadata:
        candidate = Path(ref)
        if not candidate.is_absolute():
            candidate = root / candidate
        try:
            safe = candidate.resolve().is_relative_to(root.resolve())
        except AttributeError:
            safe = str(candidate.resolve()).startswith(str(root.resolve()))
        except ValueError:
            safe = False
        if safe and candidate.is_file():
            metadata = {"kind": "path", "status": "PRESENT"}
    if not metadata:
        return {"REF": ref, "STATUS": "MISSING_REFERENCE", "DETAIL": "reference was not found in governed local state"}
    status = str(metadata.get("status", "PRESENT"))
    expires = metadata.get("expires_at")
    if expires:
        try:
            expiry = datetime.fromisoformat(str(expires)).date()
            if expiry < datetime.now(timezone.utc).date():
                status = "STALE"
        except ValueError:
            status = "UNKNOWN"
    result: dict[str, object] = {"REF": ref, "STATUS": status, "KIND": metadata.get("kind", "unknown")}
    for key in ("checked_at", "expires_at", "valid_from", "valid_until"):
        if metadata.get(key) is not None:
            result[key.upper()] = metadata[key]
    if status == "PRESENT":
        result["DETAIL"] = "reference resolved from governed local state"
    elif status == "STALE":
        result["DETAIL"] = "reference exists but its freshness window has expired"
    return result


def _normalize_review_refs(values: object, *, canonical: bool) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for item in _as_list(values):
        if isinstance(item, str):
            if ":" not in item:
                raise DecisionTraceError("review reference must contain identity and evidence reference")
            identity, reference = item.split(":", 1)
            item = {"identity": identity, "ref": reference}
        if not isinstance(item, dict):
            raise DecisionTraceError("review reference must be an object")
        identity = str(item.get("identity") or item.get("agent_id") or "").strip()
        reference = str(item.get("ref") or item.get("review_ref") or "").strip()
        if not identity or not reference:
            raise DecisionTraceError("review reference needs identity and ref")
        if canonical and identity not in CANONICAL_IDENTITIES:
            raise DecisionTraceError(f"non-canonical identity in CANONICAL_REVIEW_REFS: {identity}")
        if not canonical and identity in CANONICAL_IDENTITIES:
            raise DecisionTraceError(f"canonical identity must not be supporting-only: {identity}")
        safe, _ = _sanitize({"identity": identity, "ref": reference, **{str(k): v for k, v in item.items() if k not in {"identity", "agent_id", "ref", "review_ref"}}})
        if isinstance(safe, dict):
            output.append(safe)
    return output


def _trace_payload(trace: Mapping[str, object]) -> dict[str, object]:
    payload = copy.deepcopy(dict(trace))
    payload.pop("INTEGRITY_METADATA", None)
    return payload


def _integrity(trace: Mapping[str, object]) -> dict[str, object]:
    return {"algorithm": "sha256", "payload_sha256": _sha256(_trace_payload(trace))}


def _status_from_workflow(status: str, protected: bool, approval_ref: object | None) -> str:
    if protected and approval_ref is None:
        return "PENDING_APPROVAL"
    if status == "PASS":
        return "RECORDED"
    if status == "REJECT":
        return "REJECTED"
    return "PARTIAL"


def infer_decision_type(request: str) -> str:
    text = str(request or "").lower()
    for decision_type, terms in _MATERIAL_TERMS.items():
        if any(term in text for term in terms):
            return decision_type
    return "OTHER_MATERIAL"


def materiality(request: str, decision_type: str | None = None) -> dict[str, object]:
    text = str(request or "").strip()
    normalized = str(decision_type or "").upper().strip()
    if normalized and normalized not in DECISION_TYPES:
        return {"material": False, "decision_type": "OTHER_MATERIAL", "reason": "INVALID_DECISION_TYPE"}
    if normalized and normalized != "OTHER_MATERIAL":
        return {"material": True, "decision_type": normalized, "reason": "EXPLICIT_MATERIAL_CATEGORY"}
    lowered = text.lower()
    for candidate, terms in _MATERIAL_TERMS.items():
        hits = sorted(term for term in terms if term in lowered)
        if hits:
            return {"material": True, "decision_type": candidate, "reason": "MATERIAL_TERM", "matched_terms": hits}
    if any(term in lowered for term in _PROTECTED_DECISION_TERMS):
        return {"material": True, "decision_type": "OTHER_MATERIAL", "reason": "PROTECTED_ACTION_TERM"}
    return {"material": False, "decision_type": None, "reason": "ROUTINE_ACTIVITY"}


def make_trace(
    *,
    decision_id: str | None = None,
    goal_id: str | None = None,
    decision_type: str,
    status: str = "RECORDED",
    outcome: str,
    decision_basis: Mapping[str, object] | str,
    fact_refs: Iterable[object] = (),
    evidence_refs: Iterable[object] = (),
    source_refs: Iterable[object] = (),
    constraint_refs: Iterable[object] = (),
    policy_refs: Iterable[object] = (),
    alternatives: Iterable[object] = (),
    canonical_review_refs: object = (),
    supporting_specialist_refs: object = (),
    owner_approval_ref: object | None = None,
    change_refs: Iterable[object] = (),
    artifact_refs: Iterable[object] = (),
    created_at: str | None = None,
    valid_from: str | None = None,
    valid_until: str | None = None,
    supersedes: Iterable[object] = (),
    superseded_by: Iterable[object] = (),
    contradicts: Iterable[object] = (),
    supports: Iterable[object] = (),
    relationship: str = "UNKNOWN",
) -> dict[str, object]:
    decision_type = str(decision_type).upper().strip()
    status = str(status).upper().strip()
    if decision_type not in DECISION_TYPES:
        raise DecisionTraceError(f"invalid decision type: {decision_type}")
    if status not in TRACE_STATUSES:
        raise DecisionTraceError(f"invalid trace status: {status}")
    relationship = str(relationship).upper().strip()
    if relationship not in RELATIONSHIP_TYPES:
        raise DecisionTraceError(f"invalid relationship: {relationship}")
    if isinstance(decision_basis, str):
        decision_basis = {"summary": decision_basis}
    if not isinstance(decision_basis, Mapping):
        raise DecisionTraceError("DECISION_BASIS must be a structured object or safe summary")
    safe_basis, redacted = _sanitize(dict(decision_basis), "DECISION_BASIS")
    if not isinstance(safe_basis, dict):
        raise DecisionTraceError("DECISION_BASIS must be an object")
    if not str(safe_basis.get("summary", "")).strip():
        raise DecisionTraceError("DECISION_BASIS.summary is required")
    created_at = str(created_at or utc_now())
    base_id = decision_id or f"D-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{_sha256({'goal': goal_id, 'type': decision_type, 'created': created_at})[:12]}"
    approval = None
    if owner_approval_ref is not None:
        if isinstance(owner_approval_ref, bool):
            raise DecisionTraceError("OWNER_APPROVAL_REF cannot be a boolean")
        approval, approval_redacted = _sanitize(owner_approval_ref, "OWNER_APPROVAL_REF")
        redacted.extend(approval_redacted)
        if not isinstance(approval, dict) or not str(approval.get("ref", "")).strip():
            raise DecisionTraceError("OWNER_APPROVAL_REF must contain an actual evidence ref")
    trace: dict[str, object] = {
        "DECISION_ID": str(base_id),
        "GOAL_ID": str(goal_id) if goal_id else None,
        "DECISION_TYPE": decision_type,
        "STATUS": status,
        "OUTCOME": _safe_text(outcome)[0],
        "DECISION_BASIS": safe_basis,
        "FACT_REFS": _unique_strings(fact_refs),
        "EVIDENCE_REFS": _unique_strings(evidence_refs),
        "SOURCE_REFS": _unique_strings(source_refs),
        "CONSTRAINT_REFS": _unique_strings(constraint_refs),
        "POLICY_REFS": _normalize_policy_references(policy_refs),
        "ALTERNATIVES_CONSIDERED": list(alternatives or []),
        "CANONICAL_REVIEW_REFS": _normalize_review_refs(canonical_review_refs, canonical=True),
        "SUPPORTING_SPECIALIST_REFS": _normalize_review_refs(supporting_specialist_refs, canonical=False),
        "OWNER_APPROVAL_REF": approval,
        "CHANGE_REFS": _unique_strings(change_refs),
        "ARTIFACT_REFS": _unique_strings(artifact_refs),
        "CREATED_AT": created_at,
        "VALID_FROM": valid_from,
        "VALID_UNTIL": valid_until,
        "SUPERSEDES": _unique_strings(supersedes),
        "SUPERSEDED_BY": _unique_strings(superseded_by),
        "CONTRADICTS": _unique_strings(contradicts),
        "SUPPORTS": _unique_strings(supports),
        "RELATIONSHIP": relationship,
        "REDACTION_STATE": {"status": "REDACTED" if redacted else "CLEAN", "fields": sorted(set(redacted))},
    }
    safe_trace, trace_redacted = _sanitize(trace)
    if not isinstance(safe_trace, dict):
        raise DecisionTraceError("trace sanitization failed")
    redaction = safe_trace.get("REDACTION_STATE")
    if isinstance(redaction, dict):
        fields = set(str(item) for item in redaction.get("fields", []))
        fields.update(trace_redacted)
        redaction["fields"] = sorted(fields)
        redaction["status"] = "REDACTED" if fields else "CLEAN"
    safe_trace["INTEGRITY_METADATA"] = _integrity(safe_trace)
    errors = validate_trace(safe_trace).get("errors", [])
    if errors:
        raise DecisionTraceError("invalid trace: " + "; ".join(str(item) for item in errors))
    return safe_trace


def validate_trace(trace: Mapping[str, object]) -> dict[str, object]:
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(trace, Mapping):
        return {"valid": False, "errors": ["trace must be an object"], "warnings": []}
    required = ("DECISION_ID", "DECISION_TYPE", "STATUS", "OUTCOME", "DECISION_BASIS", "CREATED_AT", "REDACTION_STATE")
    for key in required:
        if key not in trace or trace.get(key) in (None, ""):
            errors.append(f"missing required field: {key}")
    if trace.get("DECISION_TYPE") not in DECISION_TYPES:
        errors.append("invalid DECISION_TYPE")
    if trace.get("STATUS") not in TRACE_STATUSES:
        errors.append("invalid STATUS")
    basis = trace.get("DECISION_BASIS")
    if not isinstance(basis, Mapping) or not str(basis.get("summary", "")).strip():
        errors.append("DECISION_BASIS.summary is required")
    for field in REFERENCE_FIELDS + RELATION_FIELDS + ("SUPPORTS",):
        if field in trace and not isinstance(trace.get(field), list):
            errors.append(f"{field} must be a list")
    if trace.get("RELATIONSHIP", "UNKNOWN") not in RELATIONSHIP_TYPES:
        errors.append("RELATIONSHIP is invalid")
    for field in REFERENCE_FIELDS:
        if field not in trace:
            warnings.append(f"legacy trace missing optional-compatible list: {field}")
    canonical = trace.get("CANONICAL_REVIEW_REFS", [])
    if not isinstance(canonical, list):
        errors.append("CANONICAL_REVIEW_REFS must be a list")
    else:
        for item in canonical:
            identity = item.get("identity") if isinstance(item, Mapping) else None
            if identity not in CANONICAL_IDENTITIES:
                errors.append(f"invalid canonical review identity: {identity}")
            if not isinstance(item, Mapping) or not str(item.get("ref", "")).strip():
                errors.append("canonical review ref is missing")
    supporting = trace.get("SUPPORTING_SPECIALIST_REFS", [])
    if not isinstance(supporting, list):
        errors.append("SUPPORTING_SPECIALIST_REFS must be a list")
    else:
        for item in supporting:
            if not isinstance(item, Mapping):
                errors.append("supporting specialist ref must be an object")
                continue
            identity = str(item.get("identity", ""))
            if identity in CANONICAL_IDENTITIES:
                errors.append(f"canonical identity in supporting specialist refs: {identity}")
            if identity == "p2p_aesthetica" and item.get("identity_verified") is not True:
                errors.append("Aesthetica identity is not verified")
    approval = trace.get("OWNER_APPROVAL_REF")
    if isinstance(approval, bool):
        errors.append("OWNER_APPROVAL_REF cannot be boolean")
    if approval is not None and (not isinstance(approval, Mapping) or not str(approval.get("ref", "")).strip()):
        errors.append("OWNER_APPROVAL_REF needs an actual evidence ref")
    redaction = trace.get("REDACTION_STATE")
    if not isinstance(redaction, Mapping) or redaction.get("status") not in {"CLEAN", "REDACTED"}:
        errors.append("REDACTION_STATE is invalid")
    serialized = _stable_json(trace)
    if _PRIVATE_TERMS.search(serialized) or any(pattern.search(serialized) for pattern in _SENSITIVE_PATTERNS):
        errors.append("trace contains private reasoning or secret-like material")
    integrity = trace.get("INTEGRITY_METADATA")
    integrity_status = "NOT_PRESENT"
    if integrity is not None:
        if not isinstance(integrity, Mapping) or integrity.get("algorithm") != "sha256" or not integrity.get("payload_sha256"):
            errors.append("INTEGRITY_METADATA is invalid")
        elif integrity.get("payload_sha256") != _integrity(trace).get("payload_sha256"):
            errors.append("integrity payload checksum mismatch")
        else:
            integrity_status = "VERIFIED"
    return {"valid": not errors, "errors": errors, "warnings": warnings, "integrity_status": integrity_status}


def read_trace_records(root: str | Path) -> dict[str, object]:
    project = _root_path(root)
    path = ledger_path(project)
    records: list[dict[str, object]] = []
    diagnostics: list[dict[str, object]] = []
    if not path.is_file():
        return {"records": records, "diagnostics": diagnostics, "status": "NOT_INITIALIZED", "ledger": _relative_path(path, project)}
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        return {"records": records, "diagnostics": [{"line": 0, "status": "UNKNOWN", "detail": str(exc)}], "status": "UNKNOWN", "ledger": _relative_path(path, project)}
    for line_number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict) or event.get("event") != TRACE_EVENT:
            continue
        trace = event.get("trace")
        validation = validate_trace(trace) if isinstance(trace, Mapping) else {"valid": False, "errors": ["trace payload is not an object"]}
        if not validation.get("valid"):
            diagnostics.append({"line": line_number, "status": "INVALID_TRACE", "errors": validation.get("errors", [])})
            continue
        records.append({"trace": dict(trace), "line": line_number, "raw": event, "validation": validation})
    status = "PASS" if not diagnostics else "PARTIAL"
    return {"records": records, "diagnostics": diagnostics, "status": status, "ledger": _relative_path(path, project)}


def append_trace(root: str | Path, trace: Mapping[str, object]) -> dict[str, object]:
    project = _root_path(root)
    validation = validate_trace(trace)
    if not validation.get("valid"):
        raise DecisionTraceError("invalid trace: " + "; ".join(str(item) for item in validation.get("errors", [])))
    existing = read_trace_records(project)
    decision_id = str(trace.get("DECISION_ID"))
    if any(str(item.get("trace", {}).get("DECISION_ID")) == decision_id for item in existing.get("records", [])):
        return {"status": "ALREADY_PRESENT", "decision_id": decision_id, "ledger": existing.get("ledger"), "integrity_status": validation.get("integrity_status")}
    path = ledger_path(project)
    path.parent.mkdir(parents=True, exist_ok=True)
    event = {"event": TRACE_EVENT, "trace_schema": TRACE_SCHEMA, "trace": dict(trace)}
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(_stable_json(event) + "\n")
    return {"status": "APPENDED", "decision_id": decision_id, "ledger": _relative_path(path, project), "integrity_status": validation.get("integrity_status")}


def capture_material_decision(
    root: str | Path,
    *,
    request: str,
    goal_id: str | None,
    run_id: str | None,
    workflow_status: str,
    outcome: str,
    changes: Iterable[object] = (),
    artifact_refs: Iterable[object] = (),
    evidence_refs: Iterable[object] = (),
    source_refs: Iterable[object] = (),
    constraint_refs: Iterable[object] = (),
    policy_refs: Iterable[object] = (),
    decision_type: str | None = None,
    owner_approval_ref: object | None = None,
    canonical_review_refs: object = (),
    supporting_specialist_refs: object = (),
) -> dict[str, object]:
    decision = materiality(request, decision_type)
    if not decision.get("material"):
        return {"captured": False, "status": "NOT_MATERIAL", "reason": decision.get("reason"), "decision_type": None}
    chosen_type = str(decision.get("decision_type") or decision_type or "OTHER_MATERIAL")
    protected = any(term in str(request).lower() for term in _PROTECTED_DECISION_TERMS)
    trace_status = _status_from_workflow(workflow_status, protected, owner_approval_ref)
    run_ref = f"run:{run_id}" if run_id else None
    goal_ref = f"goal:{goal_id}" if goal_id else None
    trace = make_trace(
        decision_id=f"D-{run_id}" if run_id else None,
        goal_id=goal_id,
        decision_type=chosen_type,
        status=trace_status,
        outcome=outcome,
        decision_basis={
            "summary": f"P2P recorded the material {chosen_type.lower()} choice inside the existing Goal and governance boundaries.",
            "selection_rule": str(decision.get("reason", "material decision")),
            "workflow_status": workflow_status,
            "uncertainty": "Approval or review is shown only when an actual reference exists.",
        },
        evidence_refs=list(evidence_refs) + ([run_ref] if run_ref else []),
        source_refs=list(source_refs) + [".p2p/state/goal-contract.json", LEDGER_RELATIVE_PATH],
        constraint_refs=list(constraint_refs) + ([goal_ref] if goal_ref else []),
        policy_refs=policy_refs,
        canonical_review_refs=canonical_review_refs,
        supporting_specialist_refs=supporting_specialist_refs,
        owner_approval_ref=owner_approval_ref,
        change_refs=changes,
        artifact_refs=artifact_refs,
    )
    stored = append_trace(root, trace)
    return {"captured": True, "decision_type": chosen_type, "trace": trace, "storage": stored}


def _successor_map(records: list[dict[str, object]]) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    superseded_by: dict[str, list[str]] = {}
    contradictions: dict[str, list[str]] = {}
    for item in records:
        trace = item.get("trace", {})
        if not isinstance(trace, Mapping):
            continue
        decision_id = str(trace.get("DECISION_ID"))
        for predecessor in trace.get("SUPERSEDES", []) if isinstance(trace.get("SUPERSEDES"), list) else []:
            superseded_by.setdefault(str(predecessor), []).append(decision_id)
        for contradicted in trace.get("CONTRADICTS", []) if isinstance(trace.get("CONTRADICTS"), list) else []:
            contradictions.setdefault(decision_id, []).append(str(contradicted))
            contradictions.setdefault(str(contradicted), []).append(decision_id)
    return superseded_by, contradictions


def _beginner_why(resolved: Mapping[str, object]) -> str:
    trace = resolved.get("trace", {})
    if not isinstance(trace, Mapping):
        return "P2P chưa tìm thấy bản ghi đủ tin cậy để giải thích quyết định này."
    basis = trace.get("DECISION_BASIS", {})
    summary = basis.get("summary") if isinstance(basis, Mapping) else None
    summary = str(summary or trace.get("OUTCOME") or "P2P chưa có phần giải thích an toàn.").strip().rstrip(".")
    lines = [f"P2P chọn cách này vì {summary}."]
    links = resolved.get("links", {})
    if isinstance(links, Mapping):
        present = sum(1 for group in links.values() if isinstance(group, list) for item in group if isinstance(item, Mapping) and item.get("STATUS") == "PRESENT")
        missing = sum(1 for group in links.values() if isinstance(group, list) for item in group if isinstance(item, Mapping) and item.get("STATUS") in {"MISSING_REFERENCE", "UNKNOWN", "STALE"})
        if present:
            lines.append(f"P2P đã nối quyết định này với {present} nguồn thông tin hoặc kiểm tra đã có trong hồ sơ.")
        if missing:
            lines.append(f"Có {missing} tham chiếu chưa đủ hoặc đã cũ, nên phần giải thích này vẫn có giới hạn.")
    if trace.get("OWNER_APPROVAL_REF"):
        lines.append("Có một tham chiếu phê duyệt được ghi lại; trạng thái của tham chiếu được hiển thị riêng.")
    elif trace.get("STATUS") == "PENDING_APPROVAL":
        lines.append("Quyết định này chưa có bằng chứng phê duyệt riêng, nên P2P không coi nó là đã được duyệt.")
    contradictions = resolved.get("contradictions", [])
    if contradictions:
        lines.append("Có thông tin mâu thuẫn liên quan; P2P giữ cả hai phía và không giả vờ rằng mọi thứ đã chắc chắn.")
    if resolved.get("superseding_decisions"):
        lines.append("Đã có quyết định mới hơn thay thế quyết định này.")
    temporal = resolved.get("temporal_reconstruction", {})
    if isinstance(temporal, Mapping) and temporal.get("issues"):
        lines.append("Có điểm cần kiểm tra về thời điểm của thông tin được dùng, nên P2P giữ trạng thái chưa chắc chắn.")
    return "\n".join(lines)


def resolve_trace(root: str | Path, record: Mapping[str, object], all_records: list[dict[str, object]], catalog: Mapping[str, Mapping[str, object]]) -> dict[str, object]:
    trace = record.get("trace", {})
    if not isinstance(trace, Mapping):
        return {"status": "UNKNOWN", "trace": {}, "links": {}, "contradictions": [], "beginner_why": "P2P chưa tìm thấy bản ghi hợp lệ."}
    links: dict[str, list[dict[str, object]]] = {}
    states: list[str] = []
    for field in REFERENCE_FIELDS + ("SUPPORTS",):
        resolved = [
            _resolve_reference(_root_path(root), ref, catalog, field=field)
            for ref in trace.get(field, [])
            if isinstance(trace.get(field), list)
        ]
        links[field] = resolved
        states.extend(str(item.get("STATUS")) for item in resolved)
    by_id = {str(item.get("trace", {}).get("DECISION_ID")): item.get("trace", {}) for item in all_records}
    superseded_by, contradiction_map = _successor_map(all_records)
    decision_id = str(trace.get("DECISION_ID"))
    superseding = superseded_by.get(decision_id, [])
    superseded = [str(item) for item in trace.get("SUPERSEDES", [])] if isinstance(trace.get("SUPERSEDES"), list) else []
    contradiction_ids = sorted(set(contradiction_map.get(decision_id, [])) | set(str(item) for item in trace.get("CONTRADICTS", []) if isinstance(trace.get("CONTRADICTS"), list)))
    contradictions = [{"DECISION_ID": ref, "TRACE": by_id.get(ref), "STATUS": "PRESENT" if ref in by_id else "MISSING_REFERENCE"} for ref in contradiction_ids]
    temporal_issues: list[dict[str, object]] = []
    created_at = str(trace.get("CREATED_AT", ""))
    try:
        created_date = datetime.fromisoformat(created_at.replace("Z", "+00:00")).date()
    except ValueError:
        created_date = None
        temporal_issues.append({"status": "UNKNOWN", "detail": "decision creation time is invalid"})
    if created_date:
        for field, entries in links.items():
            for entry in entries:
                checked_at = entry.get("CHECKED_AT")
                if checked_at:
                    try:
                        checked_date = datetime.fromisoformat(str(checked_at).replace("Z", "+00:00")).date()
                        if checked_date > created_date:
                            temporal_issues.append({"field": field, "ref": entry.get("REF"), "status": "REFERENCE_AFTER_DECISION", "detail": "reference was checked after the decision was created"})
                    except ValueError:
                        temporal_issues.append({"field": field, "ref": entry.get("REF"), "status": "UNKNOWN", "detail": "reference check time is invalid"})
        valid_until = trace.get("VALID_UNTIL")
        if valid_until:
            try:
                if datetime.fromisoformat(str(valid_until).replace("Z", "+00:00")).date() < datetime.now(timezone.utc).date():
                    temporal_issues.append({"field": "VALID_UNTIL", "status": "STALE", "detail": "decision validity window has expired"})
            except ValueError:
                temporal_issues.append({"field": "VALID_UNTIL", "status": "UNKNOWN", "detail": "decision validity time is invalid"})
    temporal_status = "PASS" if not temporal_issues else "PARTIAL"
    if str(trace.get("STATUS")) == "CONTRADICTED" or contradictions:
        status = "CONTRADICTED"
    elif any(state == "MISSING_REFERENCE" for state in states) or temporal_issues:
        status = "PARTIAL"
    elif any(state in {"STALE", "UNKNOWN"} for state in states):
        status = "PARTIAL"
    elif str(trace.get("STATUS")) == "UNKNOWN":
        status = "UNKNOWN"
    else:
        status = "PASS"
    resolved: dict[str, object] = {
        "status": status,
        "trace": dict(trace),
        "links": links,
        "contradictions": contradictions,
        "superseding_decisions": superseding,
        "superseded_decisions": superseded,
        "temporal_reconstruction": {"status": temporal_status, "decision_created_at": trace.get("CREATED_AT"), "issues": temporal_issues},
        "integrity_status": record.get("validation", {}).get("integrity_status") if isinstance(record.get("validation"), Mapping) else "UNKNOWN",
    }
    resolved["beginner_why"] = _beginner_why(resolved)
    return resolved


def query_trace(root: str | Path, *, decision_id: str | None = None, artifact_ref: str | None = None) -> dict[str, object]:
    project = _root_path(root)
    loaded = read_trace_records(project)
    records = loaded.get("records", []) if isinstance(loaded.get("records"), list) else []
    catalog = _reference_catalog(project, records)
    selected: list[dict[str, object]] = []
    for record in records:
        trace = record.get("trace", {})
        if not isinstance(trace, Mapping):
            continue
        if decision_id and str(trace.get("DECISION_ID")) != decision_id:
            continue
        if artifact_ref and artifact_ref not in [str(item) for item in trace.get("ARTIFACT_REFS", []) if isinstance(trace.get("ARTIFACT_REFS"), list)]:
            continue
        selected.append(resolve_trace(project, record, records, catalog))
    diagnostics = loaded.get("diagnostics", []) if isinstance(loaded.get("diagnostics"), list) else []
    if not selected:
        status = "NOT_INITIALIZED" if loaded.get("status") == "NOT_INITIALIZED" else "UNKNOWN"
    elif any(item.get("status") == "CONTRADICTED" for item in selected):
        status = "CONTRADICTED"
    elif any(item.get("status") == "PARTIAL" for item in selected) or diagnostics:
        status = "PARTIAL"
    else:
        status = "PASS"
    result: dict[str, object] = {
        "schema": QUERY_SCHEMA,
        "status": status,
        "ledger": loaded.get("ledger", LEDGER_RELATIVE_PATH),
        "decision_id": decision_id,
        "artifact_ref": artifact_ref,
        "results": selected,
        "decision_ids": [str(item.get("trace", {}).get("DECISION_ID")) for item in selected],
        "diagnostics": diagnostics,
        "canonical_governance": {"identities": list(CANONICAL_IDENTITIES), "denominator": CANONICAL_DENOMINATOR, "full_quorum": "8/8"},
    }
    if len(selected) == 1:
        result["beginner_why"] = selected[0].get("beginner_why")
    return result


def render_markdown(query: Mapping[str, object]) -> str:
    lines = ["# P2P Decision Trace Export", "", f"- Status: `{query.get('status', 'UNKNOWN')}`", f"- Ledger: `{query.get('ledger', LEDGER_RELATIVE_PATH)}`", ""]
    results = query.get("results", []) if isinstance(query.get("results"), list) else []
    for item in results:
        trace = item.get("trace", {}) if isinstance(item, Mapping) else {}
        if not isinstance(trace, Mapping):
            continue
        lines.extend(
            [
                f"## {trace.get('DECISION_ID', 'unknown')}",
                "",
                f"- Decision type: `{trace.get('DECISION_TYPE', 'UNKNOWN')}`",
                f"- Status: `{item.get('status', trace.get('STATUS', 'UNKNOWN'))}`",
                f"- Created: `{trace.get('CREATED_AT', 'UNKNOWN')}`",
                f"- Outcome: {trace.get('OUTCOME', 'UNKNOWN')}",
                "",
                "### Beginner WHY",
                "",
                str(item.get("beginner_why", "P2P chưa có lời giải thích an toàn.")),
                "",
                "### Structured basis",
                "",
                "```json",
                json.dumps(trace.get("DECISION_BASIS", {}), ensure_ascii=False, indent=2, sort_keys=True),
                "```",
                "",
                "### References",
                "",
            ]
        )
        for field in REFERENCE_FIELDS:
            refs = trace.get(field, [])
            if refs:
                lines.append(f"- `{field}`: " + ", ".join(f"`{item}`" for item in refs))
        if item.get("contradictions"):
            lines.append("- `CONTRADICTIONS`: preserved and unresolved")
        if item.get("superseding_decisions"):
            lines.append("- `SUPERSEDING_DECISIONS`: " + ", ".join(f"`{value}`" for value in item["superseding_decisions"]))
        lines.append("")
    diagnostics = query.get("diagnostics", [])
    if diagnostics:
        lines.extend(["## Diagnostics", "", "```json", json.dumps(diagnostics, ensure_ascii=False, indent=2, sort_keys=True), "```", ""])
    return "\n".join(lines)


def _write_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(content, encoding="utf-8", newline="\n")
    temporary.replace(path)


def export_trace(root: str | Path, *, output: str | Path, fmt: str, decision_id: str | None = None, artifact_ref: str | None = None) -> dict[str, object]:
    project = _root_path(root)
    query = query_trace(project, decision_id=decision_id, artifact_ref=artifact_ref)
    destination = Path(output).expanduser().resolve()
    if fmt == "json":
        content = json.dumps(query, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    elif fmt in {"md", "markdown"}:
        content = render_markdown(query)
    else:
        raise DecisionTraceError("export format must be json or markdown")
    _write_atomic(destination, content)
    return {"status": "PASS" if query.get("status") in {"PASS", "PARTIAL", "NOT_INITIALIZED"} else query.get("status"), "output": str(destination), "format": "markdown" if fmt in {"md", "markdown"} else "json", "query_status": query.get("status"), "query": query}


def doctor(root: str | Path) -> dict[str, object]:
    project = _root_path(root)
    loaded = read_trace_records(project)
    errors: list[str] = []
    for item in loaded.get("diagnostics", []) if isinstance(loaded.get("diagnostics"), list) else []:
        errors.append(f"line {item.get('line')}: invalid trace")
    return {
        "schema": "p2p-decision-trace-doctor/1",
        "status": "PASS" if not errors else "PARTIAL",
        "ledger": loaded.get("ledger", LEDGER_RELATIVE_PATH),
        "trace_count": len(loaded.get("records", [])) if isinstance(loaded.get("records"), list) else 0,
        "errors": errors,
        "canonical_denominator": CANONICAL_DENOMINATOR,
        "full_quorum": "8/8",
        "aesthetica_canonical": False,
        "external_dependencies": [],
    }


def _parse_refs(values: list[str] | None) -> list[str]:
    output: list[str] = []
    for value in values or []:
        output.extend(part.strip() for part in value.split(",") if part.strip())
    return output


def cli_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", default=".", help="Project root")
    parser.add_argument("--json", action="store_true", help="Print JSON output")
    sub = parser.add_subparsers(dest="command", required=True)

    capture = sub.add_parser("capture", help="Capture one material decision with actual references")
    capture.add_argument("--goal-id")
    capture.add_argument("--decision-type", required=True, choices=DECISION_TYPES)
    capture.add_argument("--status", default="RECORDED", choices=TRACE_STATUSES)
    capture.add_argument("--outcome", required=True)
    capture.add_argument("--basis", required=True)
    capture.add_argument("--fact-ref", action="append")
    capture.add_argument("--evidence-ref", action="append")
    capture.add_argument("--source-ref", action="append")
    capture.add_argument("--constraint-ref", action="append")
    capture.add_argument("--policy-ref", action="append")
    capture.add_argument("--change-ref", action="append")
    capture.add_argument("--artifact-ref", action="append")
    capture.add_argument("--supersedes", action="append")
    capture.add_argument("--contradicts", action="append")
    capture.add_argument("--owner-approval-ref", help="JSON object or ref string; never a boolean")

    query = sub.add_parser("query", help="Reconstruct a decision or artifact WHY")
    query.add_argument("--decision-id")
    query.add_argument("--artifact-ref")
    query.add_argument("--why", action="store_true", help="Print beginner-facing WHY")

    export = sub.add_parser("export", help="Export a deterministic JSON or Markdown trace")
    export.add_argument("--format", choices=("json", "markdown", "md"), default="json")
    export.add_argument("--out", required=True)
    export.add_argument("--decision-id")
    export.add_argument("--artifact-ref")

    sub.add_parser("doctor", help="Validate trace records without changing state")
    material = sub.add_parser("materiality", help="Explain whether a request is material")
    material.add_argument("--request", required=True)
    material.add_argument("--decision-type", choices=DECISION_TYPES)
    for child in (capture, query, export, sub.choices["doctor"], material):
        child.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)

    args = parser.parse_args(argv)
    try:
        if args.command == "capture":
            approval: object | None = None
            if args.owner_approval_ref:
                try:
                    approval = json.loads(args.owner_approval_ref)
                except json.JSONDecodeError:
                    approval = {"ref": args.owner_approval_ref, "status": "UNKNOWN"}
            trace = make_trace(
                goal_id=args.goal_id,
                decision_type=args.decision_type,
                status=args.status,
                outcome=args.outcome,
                decision_basis=args.basis,
                fact_refs=_parse_refs(args.fact_ref),
                evidence_refs=_parse_refs(args.evidence_ref),
                source_refs=_parse_refs(args.source_ref),
                constraint_refs=_parse_refs(args.constraint_ref),
                policy_refs=_parse_refs(args.policy_ref),
                owner_approval_ref=approval,
                change_refs=_parse_refs(args.change_ref),
                artifact_refs=_parse_refs(args.artifact_ref),
                supersedes=_parse_refs(args.supersedes),
                contradicts=_parse_refs(args.contradicts),
            )
            output: object = {"schema": TRACE_SCHEMA, "trace": trace, "storage": append_trace(args.project, trace)}
        elif args.command == "query":
            output = query_trace(args.project, decision_id=args.decision_id, artifact_ref=args.artifact_ref)
            if args.why and not args.json:
                print(output.get("beginner_why", "P2P chưa tìm thấy bản ghi đủ tin cậy để giải thích quyết định này."))
                return 0 if output.get("status") in {"PASS", "PARTIAL"} else 2
        elif args.command == "export":
            output = export_trace(args.project, output=args.out, fmt=args.format, decision_id=args.decision_id, artifact_ref=args.artifact_ref)
        elif args.command == "doctor":
            output = doctor(args.project)
        else:
            output = materiality(args.request, args.decision_type)
    except (DecisionTraceError, OSError, ValueError) as exc:
        output = {"schema": QUERY_SCHEMA, "status": "REJECT", "error": str(exc)}
        if not args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        return 2
    if isinstance(output, str):
        print(output)
    else:
        print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
    if isinstance(output, Mapping) and output.get("status") == "REJECT":
        return 2
    return 0


__all__ = [
    "CANONICAL_DENOMINATOR",
    "CANONICAL_IDENTITIES",
    "DECISION_TYPES",
    "DecisionTraceError",
    "TRACE_EVENT",
    "TRACE_SCHEMA",
    "append_trace",
    "capture_material_decision",
    "cli_main",
    "doctor",
    "export_trace",
    "infer_decision_type",
    "make_trace",
    "materiality",
    "query_trace",
    "read_trace_records",
    "render_markdown",
    "resolve_trace",
    "RELATIONSHIP_TYPES",
    "validate_trace",
]
