"""Bounded KP01 repo-backed knowledge lifecycle.

This additive module deliberately uses Markdown files with JSON front matter and
never creates a second database, router, control tower, or autonomous writer.
Retrieved records are projections; only an explicitly authorized promotion can
create canonical knowledge, and Control Tower reconstruction reads canonical
records only.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Iterable, Mapping

from .isolation import assert_isolated_target
from .trust import FACT_ORIGINS

KNOWLEDGE_SCHEMA = "p2p-knowledge-record/1"
STORAGE_RELATIVE_PATH = ".p2p/knowledge"
LIFECYCLE_STATES = ("OBSERVATION", "CANDIDATE", "VERIFIED", "CANONICAL", "SUPERSEDED")
KNOWLEDGE_TYPES = ("OWNER_DECISION", "PROMOTION_RESULT", "ARCHITECTURE_DECISION")
PROPOSAL_ORIGINS = {"RETRIEVED_SOURCE", "TOOL_OUTPUT", "MODEL_INFERENCE", "SPECIALIST_OPINION"}
CANONICAL_ORIGINS = {"OWNER", "RUNTIME_EVIDENCE", "OFFICIAL_SOURCE"}
SCOPE_KEYS = ("ORG", "PROJECT", "WORKSTREAM")
_SECRET_KEY = re.compile(r"(?i)(?:secret|token|password|credential|api[_-]?key|private[_-]?key|authorization|chain[_ -]?of[_ -]?thought|chat[_ -]?history)")
_SECRET_VALUE = re.compile(r"(?i)(?:sk-[A-Za-z0-9_-]{16,}|(?:secret|token|password|api[_-]?key|authorization)\s*[:=]\s*[^\s,;]+)")
_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_SCOPE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


class KnowledgeError(ValueError):
    """Raised when a knowledge record cannot be used safely."""


@dataclass(frozen=True)
class KnowledgeRecord:
    record_id: str
    knowledge_type: str
    subject: str
    statement: str
    scope: Mapping[str, str]
    lifecycle: str
    authority: Mapping[str, Any]
    evidence_refs: tuple[str, ...]
    provenance_refs: tuple[str, ...]
    created_at: str
    valid_from: str
    valid_until: str | None = None
    supersedes: tuple[str, ...] = ()
    superseded_by: tuple[str, ...] = ()
    execution_authorization: str = "NOT_GRANTED"

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": KNOWLEDGE_SCHEMA,
            "record_id": self.record_id,
            "knowledge_type": self.knowledge_type,
            "subject": self.subject,
            "statement": self.statement,
            "scope": dict(self.scope),
            "lifecycle": self.lifecycle,
            "authority": dict(self.authority),
            "evidence_refs": list(self.evidence_refs),
            "provenance_refs": list(self.provenance_refs),
            "created_at": self.created_at,
            "valid_from": self.valid_from,
            "valid_until": self.valid_until,
            "supersedes": list(self.supersedes),
            "superseded_by": list(self.superseded_by),
            "execution_authorization": self.execution_authorization,
        }


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _text(value: Any, field: str, *, max_length: int = 4096) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > max_length:
        raise KnowledgeError(f"{field}_INVALID")
    normalized = value.strip()
    if _SECRET_VALUE.search(normalized) or re.search(r"(?i)private[_ -]?reasoning|scratchpad|chain[_ -]?of[_ -]?thought", normalized):
        raise KnowledgeError(f"{field}_SECRET_OR_PRIVATE_REASONING")
    return normalized


def _safe_id(value: Any, field: str) -> str:
    normalized = _text(value, field, max_length=128)
    if not _ID.fullmatch(normalized):
        raise KnowledgeError(f"{field}_INVALID")
    return normalized


def _scope(value: Any) -> dict[str, str]:
    if not isinstance(value, Mapping) or set(value) != set(SCOPE_KEYS):
        raise KnowledgeError("SCOPE_MUST_HAVE_ORG_PROJECT_WORKSTREAM")
    result: dict[str, str] = {}
    for key in SCOPE_KEYS:
        item = _text(value.get(key), f"scope_{key.lower()}", max_length=64)
        if not _SCOPE.fullmatch(item):
            raise KnowledgeError(f"scope_{key.lower()}_INVALID")
        result[key] = item
    return result


def _refs(value: Any, field: str) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or value is None:
        raise KnowledgeError(f"{field}_MUST_BE_LIST")
    try:
        items = list(value)
    except TypeError as exc:
        raise KnowledgeError(f"{field}_MUST_BE_LIST") from exc
    result: list[str] = []
    for item in items:
        normalized = _text(item, f"{field}_ITEM", max_length=2048)
        if normalized not in result:
            result.append(normalized)
    return tuple(result)


def _safe_mapping(value: Any, path: str = "authority") -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise KnowledgeError(f"{path}_MUST_BE_OBJECT")
    result: dict[str, Any] = {}
    for raw_key, raw_value in value.items():
        key = _text(str(raw_key), f"{path}_KEY", max_length=128)
        if _SECRET_KEY.search(key):
            raise KnowledgeError(f"{path}_SECRET_FIELD")
        if isinstance(raw_value, Mapping):
            result[key] = _safe_mapping(raw_value, f"{path}.{key}")
        elif isinstance(raw_value, (list, tuple)):
            result[key] = [_text(item, f"{path}.{key}_ITEM", max_length=2048) if isinstance(item, str) else item for item in raw_value]
        elif isinstance(raw_value, str):
            result[key] = _text(raw_value, f"{path}.{key}", max_length=4096)
        elif raw_value is None or isinstance(raw_value, (bool, int, float)):
            result[key] = raw_value
        else:
            raise KnowledgeError(f"{path}.{key}_TYPE_INVALID")
    return result


def _time(value: Any, field: str) -> str:
    normalized = _text(value, field, max_length=64)
    try:
        parsed = datetime.fromisoformat(normalized.replace("Z", "+00:00"))
    except ValueError as exc:
        raise KnowledgeError(f"{field}_INVALID") from exc
    if parsed.tzinfo is None:
        raise KnowledgeError(f"{field}_TIMEZONE_REQUIRED")
    return normalized


def _check_authority(authority: Mapping[str, Any], statement: str, lifecycle: str) -> dict[str, Any]:
    clean = _safe_mapping(authority)
    origin = clean.get("origin")
    source = clean.get("source")
    if origin not in FACT_ORIGINS:
        raise KnowledgeError("AUTHORITY_ORIGIN_INVALID")
    _text(source, "authority_source", max_length=2048)
    if lifecycle in {"VERIFIED", "CANONICAL"} and not clean.get("evidence_bound", False):
        raise KnowledgeError("VERIFIED_TRUTH_REQUIRES_BOUND_EVIDENCE")
    if lifecycle == "CANONICAL" and origin not in CANONICAL_ORIGINS:
        raise KnowledgeError("CANONICAL_AUTHORITY_ORIGIN_INVALID")
    if lifecycle in {"OBSERVATION", "CANDIDATE"} and origin in PROPOSAL_ORIGINS:
        clean["canonical_write"] = False
    else:
        clean["canonical_write"] = lifecycle == "CANONICAL"
    clean["statement_sha256"] = hashlib.sha256(statement.encode("utf-8")).hexdigest()
    return clean


def make_record(
    *,
    record_id: str,
    knowledge_type: str,
    subject: str,
    statement: str,
    scope: Mapping[str, Any],
    lifecycle: str,
    authority: Mapping[str, Any],
    evidence_refs: Iterable[str],
    provenance_refs: Iterable[str] = (),
    created_at: str | None = None,
    valid_from: str | None = None,
    valid_until: str | None = None,
    supersedes: Iterable[str] = (),
    superseded_by: Iterable[str] = (),
) -> dict[str, Any]:
    record_id = _safe_id(record_id, "record_id")
    knowledge_type = _text(knowledge_type, "knowledge_type", max_length=64).upper()
    if knowledge_type not in KNOWLEDGE_TYPES:
        raise KnowledgeError("KNOWLEDGE_TYPE_INVALID")
    subject = _text(subject, "subject", max_length=512)
    statement = _text(statement, "statement", max_length=8192)
    lifecycle = _text(lifecycle, "lifecycle", max_length=32).upper()
    if lifecycle not in LIFECYCLE_STATES:
        raise KnowledgeError("LIFECYCLE_INVALID")
    scope_value = _scope(scope)
    evidence = _refs(evidence_refs, "evidence_refs")
    provenance = _refs(provenance_refs, "provenance_refs")
    if lifecycle in {"CANDIDATE", "VERIFIED", "CANONICAL"} and not evidence:
        raise KnowledgeError("PROMOTION_EVIDENCE_REQUIRED")
    authority_value = _check_authority(authority, statement, lifecycle)
    created = _time(created_at or _now(), "created_at")
    start = _time(valid_from or created, "valid_from")
    end = _time(valid_until, "valid_until") if valid_until is not None else None
    if end is not None and end < start:
        raise KnowledgeError("VALIDITY_WINDOW_INVALID")
    supersedes_refs = _refs(supersedes, "supersedes")
    superseded_by_refs = _refs(superseded_by, "superseded_by")
    return KnowledgeRecord(
        record_id=record_id,
        knowledge_type=knowledge_type,
        subject=subject,
        statement=statement,
        scope=scope_value,
        lifecycle=lifecycle,
        authority=authority_value,
        evidence_refs=evidence,
        provenance_refs=provenance,
        created_at=created,
        valid_from=start,
        valid_until=end,
        supersedes=supersedes_refs,
        superseded_by=superseded_by_refs,
    ).as_dict()


def validate_record(record: Mapping[str, Any]) -> dict[str, Any]:
    try:
        rebuilt = make_record(
            record_id=record.get("record_id"), knowledge_type=record.get("knowledge_type"), subject=record.get("subject"),
            statement=record.get("statement"), scope=record.get("scope"), lifecycle=record.get("lifecycle"),
            authority=record.get("authority"), evidence_refs=record.get("evidence_refs"), provenance_refs=record.get("provenance_refs", ()),
            created_at=record.get("created_at"), valid_from=record.get("valid_from"), valid_until=record.get("valid_until"),
            supersedes=record.get("supersedes", ()), superseded_by=record.get("superseded_by", ()),
        )
    except (KnowledgeError, TypeError, AttributeError) as exc:
        return {"valid": False, "errors": [str(exc)]}
    if record.get("schema") not in (None, KNOWLEDGE_SCHEMA):
        return {"valid": False, "errors": ["SCHEMA_INVALID"]}
    if rebuilt["authority"].get("statement_sha256") != record.get("authority", {}).get("statement_sha256"):
        return {"valid": False, "errors": ["STATEMENT_INTEGRITY_MISMATCH"]}
    if record.get("execution_authorization", "NOT_GRANTED") != "NOT_GRANTED":
        return {"valid": False, "errors": ["EXECUTION_AUTHORIZATION_MUST_NOT_BE_GRANTED"]}
    return {"valid": True, "errors": [], "record": rebuilt}


def _record_path(root: Path, record: Mapping[str, Any]) -> Path:
    scope = record["scope"]
    directory = root / STORAGE_RELATIVE_PATH / scope["ORG"] / scope["PROJECT"] / scope["WORKSTREAM"]
    return directory / f"{record['record_id']}.md"


def _markdown(record: Mapping[str, Any]) -> str:
    front = json.dumps({**record, "schema": KNOWLEDGE_SCHEMA}, ensure_ascii=False, indent=2, sort_keys=True)
    return f"---json\n{front}\n---\n\n# {record['subject']}\n\n{record['statement']}\n"


def _parse_markdown(path: Path) -> dict[str, Any] | None:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---json\n"):
        return None
    marker = "\n---\n"
    end = text.find(marker, len("---json\n"))
    if end < 0:
        return None
    try:
        value = json.loads(text[len("---json\n"):end])
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None


def write_record(root: str | Path, record: Mapping[str, Any], *, protected_roots: Iterable[str | Path] = ()) -> dict[str, Any]:
    project = Path(root).expanduser().resolve()
    if not project.is_dir():
        raise KnowledgeError("PROJECT_ROOT_MISSING")
    checked = validate_record(record)
    if not checked["valid"]:
        raise KnowledgeError("INVALID_RECORD:" + ";".join(checked["errors"]))
    target = _record_path(project, checked["record"])
    assert_isolated_target(target, protected_roots)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        existing = _parse_markdown(target)
        if existing != checked["record"]:
            raise KnowledgeError("RECORD_IMMUTABLE_CONFLICT")
        return {"status": "ALREADY_PRESENT", "record_id": checked["record"]["record_id"], "path": str(target.relative_to(project))}
    target.write_text(_markdown(checked["record"]), encoding="utf-8", newline="\n")
    return {"status": "APPENDED", "record_id": checked["record"]["record_id"], "path": str(target.relative_to(project))}


def read_records(root: str | Path) -> dict[str, Any]:
    project = Path(root).expanduser().resolve()
    directory = project / STORAGE_RELATIVE_PATH
    if not directory.is_dir():
        return {"status": "NOT_INITIALIZED", "records": [], "diagnostics": []}
    records: list[dict[str, Any]] = []
    diagnostics: list[dict[str, Any]] = []
    for path in sorted(directory.rglob("*.md")):
        try:
            raw = _parse_markdown(path)
        except (OSError, UnicodeError) as exc:
            diagnostics.append({"path": str(path), "error": str(exc)})
            continue
        if raw is None:
            diagnostics.append({"path": str(path), "error": "FRONT_MATTER_INVALID"})
            continue
        result = validate_record(raw)
        if not result["valid"]:
            diagnostics.append({"path": str(path), "error": result["errors"]})
            continue
        records.append(result["record"])
    return {"status": "PASS" if not diagnostics else "PARTIAL", "records": records, "diagnostics": diagnostics}


def _scope_matches(record: Mapping[str, Any], scope: Mapping[str, Any] | None) -> bool:
    return scope is None or all(record.get("scope", {}).get(key) == scope.get(key) for key in SCOPE_KEYS)


def _parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _live_at(records: list[dict[str, Any]], at: str) -> list[dict[str, Any]]:
    moment = _parse_dt(at)
    eligible = [item for item in records if _parse_dt(item["valid_from"]) <= moment and (item["valid_until"] is None or _parse_dt(item["valid_until"]) >= moment)]
    superseded: set[str] = set()
    for item in eligible:
        superseded.update(str(ref) for ref in item.get("supersedes", []))
    return [item for item in eligible if item["record_id"] not in superseded and item["lifecycle"] != "SUPERSEDED"]


def _query(root: str | Path, *, subject: str, scope: Mapping[str, Any] | None, as_of: str) -> dict[str, Any]:
    loaded = read_records(root)
    if loaded["status"] == "NOT_INITIALIZED":
        return {"schema": "p2p-knowledge-query/1", "status": "NOT_INITIALIZED", "results": [], "canonical": False, "authority_conflict": False}
    try:
        selected = _live_at([item for item in loaded["records"] if item["subject"] == subject and _scope_matches(item, scope)], as_of)
    except (KnowledgeError, ValueError) as exc:
        return {"schema": "p2p-knowledge-query/1", "status": "PARTIAL", "results": [], "error": str(exc), "canonical": False, "authority_conflict": False}
    canonical = [item for item in selected if item["lifecycle"] == "CANONICAL"]
    conflict = len(canonical) > 1 and len({item["statement"] for item in canonical}) > 1
    if conflict:
        return {"schema": "p2p-knowledge-query/1", "status": "AUTHORITY_CONFLICT", "results": selected, "canonical": False, "authority_conflict": True, "verified_truth": False}
    candidates = canonical or [item for item in selected if item["lifecycle"] in {"VERIFIED", "CANDIDATE", "OBSERVATION"}]
    candidates.sort(key=lambda item: (item["valid_from"], item["created_at"], item["record_id"]), reverse=True)
    chosen = candidates[:1]
    return {
        "schema": "p2p-knowledge-query/1",
        "status": "PARTIAL" if loaded["status"] == "PARTIAL" else ("PASS" if chosen else "NOT_FOUND"),
        "results": chosen,
        "all_live_results": selected,
        "canonical": bool(chosen and chosen[0]["lifecycle"] == "CANONICAL"),
        "verified_truth": bool(chosen and chosen[0]["lifecycle"] == "CANONICAL"),
        "retrieved_knowledge": bool(chosen),
        "agent_memory": False,
        "authority_conflict": False,
        "as_of": as_of,
    }


def query_current(root: str | Path, *, subject: str, scope: Mapping[str, Any] | None = None) -> dict[str, Any]:
    return _query(root, subject=_text(subject, "subject", max_length=512), scope=scope, as_of=_now())


def query_as_of(root: str | Path, *, subject: str, as_of: str, scope: Mapping[str, Any] | None = None) -> dict[str, Any]:
    return _query(root, subject=_text(subject, "subject", max_length=512), scope=scope, as_of=_time(as_of, "as_of"))


def provenance_lookup(root: str | Path, reference: str) -> dict[str, Any]:
    ref = _text(reference, "reference", max_length=2048)
    loaded = read_records(root)
    matches = [item for item in loaded["records"] if ref in item["provenance_refs"] or ref in item["evidence_refs"] or ref == item["record_id"]]
    return {"schema": "p2p-knowledge-provenance/1", "status": "PASS" if matches else "NOT_FOUND", "reference": ref, "records": matches}


def reconstruct_control_tower(root: str | Path, *, scope: Mapping[str, Any]) -> dict[str, Any]:
    loaded = read_records(root)
    canonical = [item for item in loaded["records"] if item["lifecycle"] == "CANONICAL" and _scope_matches(item, scope)]
    return {
        "schema": "p2p-control-tower-reconstruction/1",
        "status": "PASS" if canonical else "NO_CANONICAL_KNOWLEDGE",
        "records": canonical,
        "source": "CANONICAL_KNOWLEDGE_ONLY",
        "retrieved_knowledge_is_verified_truth": bool(canonical),
        "execution_authorization": "NOT_GRANTED",
        "autonomous_promotion": "NOT_CREATED",
    }


def promote_record(
    root: str | Path,
    *,
    candidate_id: str,
    owner_decision_ref: str,
    evidence_ref: str,
    approved_by: str = "OWNER",
) -> dict[str, Any]:
    """Create a separate canonical record only after explicit approval evidence."""
    loaded = read_records(root)
    candidate = next((item for item in loaded["records"] if item["record_id"] == candidate_id), None)
    if candidate is None:
        raise KnowledgeError("CANDIDATE_NOT_FOUND")
    if candidate["lifecycle"] not in {"CANDIDATE", "VERIFIED"}:
        raise KnowledgeError("LIFECYCLE_GATE_REJECTED")
    if not owner_decision_ref.strip() or not evidence_ref.strip() or approved_by != "OWNER":
        raise KnowledgeError("EXPLICIT_AUTHORITY_EVIDENCE_REQUIRED")
    canonical = make_record(
        record_id=f"{candidate_id}-canonical",
        knowledge_type="PROMOTION_RESULT",
        subject=candidate["subject"],
        statement=candidate["statement"],
        scope=candidate["scope"],
        lifecycle="CANONICAL",
        authority={"origin": "OWNER", "source": owner_decision_ref, "evidence_bound": True, "approval_reference": owner_decision_ref},
        evidence_refs=tuple(candidate["evidence_refs"]) + (evidence_ref, owner_decision_ref),
        provenance_refs=tuple(candidate["provenance_refs"]) + (candidate_id,),
        created_at=_now(),
        supersedes=(candidate_id,),
    )
    result = write_record(root, canonical)
    return {"status": "PASS", "candidate_id": candidate_id, "canonical_record_id": canonical["record_id"], "storage": result, "execution_authorization": "NOT_GRANTED"}


__all__ = [
    "KNOWLEDGE_SCHEMA", "KNOWLEDGE_TYPES", "LIFECYCLE_STATES", "KnowledgeError", "KnowledgeRecord",
    "make_record", "validate_record", "write_record", "read_records", "query_current", "query_as_of",
    "provenance_lookup", "reconstruct_control_tower", "promote_record",
]
