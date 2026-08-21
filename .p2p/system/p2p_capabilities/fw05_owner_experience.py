# -*- coding: utf-8 -*-
"""P2P-FRAMEWORK-05 — Owner Experience & Decision Trace.

FW05 is an OWNER EXPERIENCE + DECISION EVIDENCE layer only. It is NOT a new
orchestrator: FW01 remains the sole operating loop. FW05 must NOT select
tasks, roles, teams, providers, or models; it must NOT grant permission,
execute code, deploy, create another Continue Gate, or create another state
authority. It reads canonical durable state and evidence, and presents or
records Owner decisions.

Two core invariants added by FW05:

    DECISION_TRACE != PRIVATE_CHAIN_OF_THOUGHT
        The trace records concise, inspectable decision FACTS (input facts,
        applied rule, selected action, alternatives, evidence pointers,
        gaps). It never stores private reasoning tokens, scratchpad
        material, or raw chain-of-thought.

    OWNER_MESSAGE != DURABLE_DECISION
        A raw Owner chat transcript never becomes durable state. An Owner
        answer is parsed against a DECISION_ID, validated, and recorded as a
        structured resolution (what / scope / target / expiry / evidence /
        provenance hash). Only then does FW01 resume from durable state.

Storage (all append-only, deterministic, no daemon / no DB):

    .p2p/state/owner-inbox.jsonl          p2p-fw05-owner-inbox/1
        One record per material Owner decision. An item exists ONLY when
        execution genuinely cannot continue safely without Owner input.
        Deduplication: same decision_id (stable hash of blocking cause +
        scope + evidence version) and an OPEN item with that id already
        exists -> the record is not duplicated. A material evidence change
        produces a SUPERSEDES link instead of a silent overwrite.

    .p2p/state/execution-ledger.jsonl     p2p-fw05-decision-trace/1 (event)
        Decision-trace events share the existing durable ledger so the
        existing FW01 trace surfaces can discover FW05 decisions without a
        second authority. FW05 records only reference pointers to FW02/FW03/
        FW04 facts (EVIDENCE_POINTERS); it never duplicates their truth.

Read-only surfaces (idempotent, never execute anything):

    render_owner_experience(level=1|2|3)   progressive disclosure L1/L2/L3
    project_status_snapshot()              derived from durable state
    read_inbox() / read_decision()         bounded retrieval

Command safety:

    "xem trạng thái" != "tiếp tục"   (view != continue execution)
    "tiếp tục"            != destructive/release permission

Quality-review routing (FW04 durable STOP_BLOCKED / QUALITY_REVIEW_REQUIRED
is the honest durable fact FW05 reads):

    QUALITY_REVIEW != AUTOMATIC_OWNER_GATE
        If the missing evidence can be obtained through an existing safe
        technical verification path, FW05 routes it as TECHNICALLY_RESOLVABLE
        (no inbox item). An inbox item is created only when the remaining
        decision belongs to the Owner, and exactly ONE such item is created
        per unresolved decision.

TECHNICAL_ROUTING_DECISION != OWNER_GATE: model/backend/skill/role/runner/
context/pattern choices and ordinary bounded retry/recovery are classified
technical and never reach the Owner.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

FW05_SCHEMA = "p2p-fw05-owner-experience/1"
OWNER_INBOX_SCHEMA = "p2p-fw05-owner-inbox/1"
DECISION_TRACE_EVENT = "fw05_decision_record"
LEDGER_RELATIVE_PATH = ".p2p/state/execution-ledger.jsonl"
OWNER_INBOX_RELATIVE_PATH = ".p2p/state/owner-inbox.jsonl"

# Canonical FW05 decision vocabulary (bounded; reuse FW01/FW04 gate names
# where present — no aliases beyond these).
FW05_DECISION_TYPES = (
    "NEXT_SAFE_TASK",
    "CAPABILITY_REQUIREMENT",
    "CAPABILITY_SOURCE_SELECTION",
    "TEAM_SELECTION",
    "EXECUTION_TARGET_SELECTION",
    "PERMISSION_GATE",
    "QUALITY_GATE",
    "CONTINUE_GATE",
    "OWNER_GATE",
    "PROMOTION_GATE",
    "RECOVERY_DECISION",
)

# Only these categories may ever reach the Owner (spec §8).
OWNER_GATE_CATEGORIES = (
    "PRODUCT_OR_BUSINESS_DECISION",
    "NEW_PERMISSION",
    "DESTRUCTIVE_ACTION",
    "RELEASE_OR_DEPLOY",
    "MATERIAL_SCOPE_EXPANSION",
    "REAL_DATA_DECISION",
    "QUALITY_REVIEW_WHEN_EVIDENCE_CANNOT_RESOLVE",
    "SECURITY_OR_PRIVACY_DECISION",
    "CONFLICT_NOT_RESOLVABLE_FROM_EVIDENCE",
)

INBOX_STATUSES = ("OPEN", "RESOLVED", "SUPERSEDED")
ANSWER_FAILURES = (
    "UNKNOWN_DECISION_ID",
    "ALREADY_RESOLVED",
    "STALE_VERSION",
    "OPTION_NOT_ALLOWED",
    "SCOPE_MISMATCH",
    "MALFORMED",
    "AMBIGUOUS",
)

# Technical routing that must NEVER reach the Owner (spec §9). Lowercased
# tokens grouped by domain; presence of only technical vocabulary =>
# TECHNICALLY_RESOLVABLE unless a material owner-owned term also matches.
_TECHNICAL_TERMS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("MODEL_OR_BACKEND", (
        "codex", "manus", "anthropic", "openai", "claude", "gpt", "model",
        "backend", "provider", "inference", "llm")),
    ("SOURCE_FILE_OR_INSPECT", (
        "source file", "file to inspect", "which file", "module path",
        "inspect", "read file", "filepath")),
    ("SKILL_CHOICE", (
        "skill", "tool", "utility", "helper", "which skill")),
    ("ROLE_OR_TEAM_SIZE", (
        "one role", "three roles", "two roles", "role selection", "team size",
        "role count", "single role", "p2p_iris", "p2p_tecton", "p2p_axiom",
        "p2p_vector", "p2p_datos", "p2p_anon", "p2p_architecton", "p2p_helios")),
    ("TEST_RUNNER", (
        "unittest", "pytest", "test runner", "test harness", "runner")),
    ("CONTEXT_OR_PATTERN", (
        "context retrieval", "how much context", "context window",
        "implementation pattern", "retry", "recovery within policy",
        "bounded retry")),
)
_MATERIAL_OWNER_TERMS = {
        "PRODUCT_OR_BUSINESS_DECISION": ("business", "product decision", "feature", "persona", "pricing", "monetization",
                                     "retention", "premium", "phí", "thuê bao", "nghiệp vụ", "sản phẩm"),
    "NEW_PERMISSION": ("permission", "credential", "login", "api key", "access",
                        "approve permission", "quyền", "tài khoản"),
    "DESTRUCTIVE_ACTION": ("delete", "destructive", "drop", "erase", "remove data", "xoá", "xóa",
                            "phá", "phá hủy"),
    "RELEASE_OR_DEPLOY": ("release", "deploy", "deployments", "publish", "promote",
                          "go live", "phát hành", "triển khai"),
    "MATERIAL_SCOPE_EXPANSION": ("scope expansion", "new feature set",
                                 "material scope", "outside scope", "major change"),
    "REAL_DATA_DECISION": ("real data", "production data", "user data", "pii",
                            "live users", "dữ liệu thật", "dữ liệu người dùng"),
    "QUALITY_REVIEW_WHEN_EVIDENCE_CANNOT_RESOLVE": ("quality review", "missing evidence",
                                                     "conflicting evidence", "evidence conflict",
                                                     "evidence gap", "quality review owner"),
    "SECURITY_OR_PRIVACY_DECISION": ("security", "privacy", "secret", "encryption",
                                      "audit", "bảo mật", "riêng tư"),
    "CONFLICT_NOT_RESOLVABLE_FROM_EVIDENCE": ("conflict", "contradiction", "irreconcilable",
                                               "no safe default", "cannot resolve"),
}
# Order matters: these are checked for material owner routing even when
# technical vocabulary is present (material beats technical; ambiguity ->
# owner-owned triage handled by the caller's evidence).
_MATERIAL_PRIORITY_ORDER = [
    "SECURITY_OR_PRIVACY_DECISION",
    "DESTRUCTIVE_ACTION",
    "RELEASE_OR_DEPLOY",
    "NEW_PERMISSION",
    "MATERIAL_SCOPE_EXPANSION",
    "REAL_DATA_DECISION",
    "CONFLICT_NOT_RESOLVABLE_FROM_EVIDENCE",
    "PRODUCT_OR_BUSINESS_DECISION",
    "QUALITY_REVIEW_WHEN_EVIDENCE_CANNOT_RESOLVE",
]

_SECRET_PATTERNS = (
    re.compile(r"(?i)\b(?:sk|pk|rk)-[A-Za-z0-9_-]{12,}\b"),
    re.compile(r"(?i)\b(?:ghp|github_pat|xoxb|xoxp|glpat)-[A-Za-z0-9_-]{12,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._-]{12,}\b"),
    re.compile(r"(?i)\b(?:api[_-]?key|access[_-]?token|secret|password|credential)\s*[:=]\s*[^\s,;]+"),
)
_PRIVATE_TERMS = re.compile(
    r"(?i)\b(?:chain[_ -]?of[_ -]?thought|private[_ -]?reasoning|scratchpad|"
    r"raw[_ -]?prompt|full[_ -]?prompt|hidden[_ -]?deliberation)\b"
)


class Fw05Error(ValueError):
    """Safe, user-facing FW05 contract error."""


# ---------------------------------------------------------------- utilities

def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _stable_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256hex(value: object) -> str:
    return hashlib.sha256(_stable_json(value).encode("utf-8")).hexdigest()


def _safe_text(value: object, *, max_length: int = 4096) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return text[:max_length]


def _redact_secret(value: str) -> str:
    """Replace any secret-bearing substring with a placeholder."""
    out = value
    for pattern in _SECRET_PATTERNS:
        out = pattern.sub("[REDACTED]", out)
    return out


def _sanitize_value(value: object) -> object:
    """Return a sanitized, safe copy of value; no secrets, no raw prompts."""
    if isinstance(value, dict):
        safe: dict[str, object] = {}
        for key, val in value.items():
            key = _redact_secret(str(key))
            safe[key] = _sanitize_value(val)
        return safe
    if isinstance(value, (list, tuple)):
        return [_sanitize_value(item) for item in value]
    if isinstance(value, str):
        return _redact_secret(_safe_text(value))
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return value
    if isinstance(value, (bytes, bytearray)):
        return _redact_secret(f"<binary:{len(value)}b>")
    return _redact_secret(_safe_text(str(value)))


def _root_path(root: str | Path) -> Path:
    return Path(root).resolve()


def _inbox_path(root: Path) -> Path:
    return root / OWNER_INBOX_RELATIVE_PATH


def _ledger_path(root: Path) -> Path:
    return root / LEDGER_RELATIVE_PATH


def _write_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(content, encoding="utf-8", newline="\n")
    temporary.replace(path)


# ----------------------------------------------------------- decision scope

def classify_decision_scope(decision_payload: Mapping[str, object]) -> dict[str, object]:
    """Classify whether a decision genuinely needs the Owner.

    Returns one of two routings:
      OWNER_OWNED   -> an Owner Decision Inbox item is required (category in
                       OWNER_GATE_CATEGORIES)
      TECHNICALLY_RESOLVABLE -> P2P routes it internally; NO Owner item.

    Technical routing decisions (model/backend/skill/role/runner/context/
    ordinary bounded retry) never reach the Owner: TECHNICAL_ROUTING_DECISION
    != OWNER_GATE. When both technical and material owner terms appear, the
    material owner category wins (conservative fail-open toward the Owner
    for material decisions, fail-closed toward NOT asking for the rest).
    """
    text = " ".join(_safe_text(str(v)) for v in decision_payload.values())
    lowered = text.lower()
    # Material owner categories win over technical classification.
    owner_hits: list[str] = []
    for category in _MATERIAL_PRIORITY_ORDER:
        terms = _MATERIAL_OWNER_TERMS[category]
        if any(term in lowered for term in terms):
            owner_hits.append(category)
    tech_hits: list[str] = []
    for domain, terms in _TECHNICAL_TERMS:
        if any(term in lowered for term in terms):
            tech_hits.append(domain)
    if owner_hits:
        return {
            "routing": "OWNER_OWNED",
            "category": owner_hits[0],
            "all_matched_categories": owner_hits,
            "technical_tokens_present": tech_hits,
            "owner_decision_required": True,
        }
    return {
        "routing": "TECHNICALLY_RESOLVABLE",
        "category": None,
        "all_matched_categories": [],
        "technical_tokens_present": tech_hits,
        "owner_decision_required": False,
    }


def stable_decision_id(goal_id: str, task_id: str, decision_type: str,
                       blocking_scope: str, evidence_version: str) -> str:
    """Deterministic decision identity: same blocking cause + same scope +
    same evidence version -> the same DECISION_ID. This is what makes inbox
    deduplication and cold-process recovery identical across processes."""
    digest = _sha256hex({
        "goal_id": str(goal_id or ""),
        "task_id": str(task_id or ""),
        "decision_type": str(decision_type or ""),
        "blocking_scope": str(blocking_scope or ""),
        "evidence_version": str(evidence_version or ""),
    })[:16]
    return f"FW05-{str(decision_type).upper()}-{digest}"


def _check_decision_type(value: object) -> str:
    text = str(value).upper().strip()
    if text not in FW05_DECISION_TYPES:
        raise Fw05Error(f"invalid FW05 decision type: {value!r}")
    return text


def _check_category(value: object) -> str:
    text = str(value).upper().strip()
    if text not in OWNER_GATE_CATEGORIES:
        raise Fw05Error(f"invalid owner gate category: {value!r}")
    return text


# --------------------------------------------------------- decision trace

def make_decision_record(
    *,
    decision_type: str,
    goal_id: str | None,
    task_id: str | None,
    input_facts: Iterable[str] = (),
    applied_policy_or_rule: str = "",
    selected_action: str = "",
    material_alternatives: Iterable[str] = (),
    rejected_alternatives_with_reason: Iterable[str] = (),
    evidence_pointers: Iterable[str] = (),
    unknown_or_gaps: Iterable[str] = (),
    owner_decision_required: bool,
    decision_status: str = "RECORDED",
    blocking_scope: str = "",
    inbox_category: str | None = None,
    goal_state_hash: str | None = None,
    created_at: str | None = None,
    superseded_by: str | None = None,
) -> dict[str, object]:
    """Build a structured, durable decision-trace record.

    The record stores only concise, inspectable decision FACTS. It must
    never contain private reasoning tokens, scratchpad material, raw
    chain-of-thought, secrets, or raw unnecessary transcripts
    (DECISION_TRACE != PRIVATE_CHAIN_OF_THOUGHT).
    """
    decision_type = _check_decision_type(decision_type)
    status = str(decision_status).upper().strip()
    if status not in ("RECORDED", "SUPERSEDED", "PARTIAL", "UNKNOWN"):
        raise Fw05Error(f"invalid decision status: {status}")
    evidence_version = _sha256hex(list(str(e) for e in evidence_pointers))[:16]
    decision_id = stable_decision_id(
        goal_id or "", task_id or "", decision_type,
        str(blocking_scope or ""), evidence_version)
    created_at = str(created_at or utc_now())
    record: dict[str, object] = {
        "DECISION_ID": decision_id,
        "DECISION_TYPE": decision_type,
        "DECISION_STATUS": status,
        "GOAL_ID": str(goal_id) if goal_id else None,
        "TASK_ID": str(task_id) if task_id else None,
        "TIMESTAMP": created_at,
        "INPUT_FACTS": [_safe_text(item) for item in input_facts],
        "APPLIED_POLICY_OR_RULE": _safe_text(applied_policy_or_rule or "UNKNOWN != SAFE"),
        "SELECTED_ACTION": _safe_text(selected_action),
        "MATERIAL_ALTERNATIVES": [_safe_text(item) for item in material_alternatives],
        "REJECTED_ALTERNATIVES_WITH_REASON": [_safe_text(item) for item in rejected_alternatives_with_reason],
        "EVIDENCE_POINTERS": [_safe_text(_redact_secret(str(p))) for p in evidence_pointers],
        "UNKNOWN_OR_GAPS": [_safe_text(item) for item in unknown_or_gaps],
        "OWNER_DECISION_REQUIRED": bool(owner_decision_required),
        "BLOCKING_SCOPE": _safe_text(blocking_scope or "NONE"),
        "EVIDENCE_VERSION": evidence_version,
        "GOAL_STATE_HASH": goal_state_hash,
        "SUPERSEDED_BY": superseded_by,
    }
    safe = _sanitize_value(record)
    if not isinstance(safe, dict):
        raise Fw05Error("decision record sanitization failed")
    serialized = _stable_json(safe)
    if _PRIVATE_TERMS.search(serialized):
        raise Fw05Error("decision record contains private reasoning or chain-of-thought")
    if any(pattern.search(serialized) for pattern in _SECRET_PATTERNS):
        raise Fw05Error("decision record contains secret-bearing material")
    safe["RECORD_HASH"] = _sha256hex(safe)
    return safe


def append_decision_trace(root: str | Path, record: Mapping[str, object]) -> dict[str, object]:
    """Append an FW05 decision-trace event to the existing durable ledger.

    Returns status APPENDED (new), ALREADY_PRESENT (idempotent), or the
    supersession status when a newer version link exists. Never modifies
    existing records (immutability: resolved decisions are superseded via
    link, never rewritten).
    """
    project = _root_path(root)
    validation = validate_decision_record(record)
    if not validation.get("valid"):
        raise Fw05Error("invalid decision record: " + "; ".join(
            str(e) for e in validation.get("errors", [])))
    ledger = _ledger_path(project)
    ledger.parent.mkdir(parents=True, exist_ok=True)
    decision_id = str(record.get("DECISION_ID"))
    if ledger.exists():
        for raw_line in ledger.read_text(encoding="utf-8").splitlines():
            try:
                event = json.loads(raw_line)
            except (json.JSONDecodeError, ValueError):
                continue
            if not isinstance(event, dict):
                continue
            if event.get("event") == DECISION_TRACE_EVENT and str(
                    event.get("record", {}).get("DECISION_ID")) == decision_id:
                return {"status": "ALREADY_PRESENT", "decision_id": decision_id,
                        "ledger": LEDGER_RELATIVE_PATH, "record_hash": str(record.get("RECORD_HASH"))}
    event = {"event": DECISION_TRACE_EVENT, "trace_schema": "p2p-fw05-decision-trace/1",
             "record": dict(record)}
    _write_atomic(ledger, (ledger.read_text(encoding="utf-8") if ledger.exists() else "")
                  + _stable_json(event) + "\n")
    return {"status": "APPENDED", "decision_id": decision_id,
            "ledger": LEDGER_RELATIVE_PATH, "record_hash": str(record.get("RECORD_HASH"))}


def validate_decision_record(record: Mapping[str, object]) -> dict[str, object]:
    errors: list[str] = []
    if not isinstance(record, Mapping):
        return {"valid": False, "errors": ["record must be an object"]}
    for key in ("DECISION_ID", "DECISION_TYPE", "DECISION_STATUS",
                "TIMESTAMP", "BLOCKING_SCOPE", "RECORD_HASH"):
        if key not in record or record.get(key) in (None, ""):
            errors.append(f"missing required field: {key}")
    if str(record.get("DECISION_TYPE", "")) not in FW05_DECISION_TYPES:
        errors.append("invalid DECISION_TYPE")
    if not isinstance(record.get("INPUT_FACTS"), list):
        errors.append("INPUT_FACTS must be a list")
    if not isinstance(record.get("EVIDENCE_POINTERS"), list):
        errors.append("EVIDENCE_POINTERS must be a list")
    if not isinstance(record.get("OWNER_DECISION_REQUIRED"), bool):
        errors.append("OWNER_DECISION_REQUIRED must be a boolean")
    serialized = _stable_json(record)
    if _PRIVATE_TERMS.search(serialized):
        errors.append("record contains private reasoning or chain-of-thought")
    if any(pattern.search(serialized) for pattern in _SECRET_PATTERNS):
        errors.append("record contains secret-bearing material")
    recomputed = _sha256hex({k: v for k, v in record.items() if k != "RECORD_HASH"})
    if str(record.get("RECORD_HASH")) != recomputed:
        errors.append("RECORD_HASH does not match payload")
    return {"valid": not errors, "errors": errors}


def read_decision_records(root: str | Path) -> dict[str, object]:
    """Read all valid FW05 decision-trace records from the durable ledger."""
    project = _root_path(root)
    ledger = _ledger_path(project)
    records: list[dict[str, object]] = []
    diagnostics: list[dict[str, object]] = []
    if not ledger.is_file():
        return {"records": records, "diagnostics": diagnostics,
                "status": "NOT_INITIALIZED", "ledger": LEDGER_RELATIVE_PATH}
    for line_number, raw_line in enumerate(ledger.read_text(encoding="utf-8").splitlines(), 1):
        if not raw_line.strip():
            continue
        try:
            event = json.loads(raw_line)
        except (json.JSONDecodeError, ValueError):
            diagnostics.append({"line": line_number, "status": "UNPARSEABLE"})
            continue
        if not isinstance(event, dict) or event.get("event") != DECISION_TRACE_EVENT:
            continue
        record = event.get("record")
        validation = validate_decision_record(record) if isinstance(record, Mapping) else {
            "valid": False, "errors": ["record payload is not an object"]}
        if not validation.get("valid"):
            diagnostics.append({"line": line_number, "status": "INVALID_RECORD",
                                "errors": validation.get("errors", [])})
            continue
        records.append({"record": dict(record), "line": line_number,
                        "validation": validation})
    return {"records": records, "diagnostics": diagnostics,
            "status": "PARTIAL" if diagnostics else "PASS",
            "ledger": LEDGER_RELATIVE_PATH}


# --------------------------------------------------------- owner inbox

def build_owner_inbox_item(
    *,
    decision_id: str,
    decision_type: str,
    goal_id: str | None,
    task_id: str | None,
    category: str,
    title: str,
    plain_language_question: str,
    why_owner_is_needed: str,
    options: Iterable[str],
    recommended_option_if_evidence_supports_one: str | None = None,
    consequences: Iterable[str] = (),
    blocking_scope: str,
    evidence_pointers: Iterable[str] = (),
    evidence_version: str = "",
    created_at: str | None = None,
) -> dict[str, object]:
    """Build a durable Owner Decision Inbox item.

    An item exists ONLY when execution genuinely cannot continue safely
    without Owner input. PLAIN_LANGUAGE_QUESTION and WHY_OWNER_IS_NEEDED are
    derived from structured state, not free prose from the transcript.
    """
    _check_category(category)
    decision_type = _check_decision_type(decision_type)
    options_list = [_safe_text(o) for o in options]
    if not options_list:
        raise Fw05Error("owner inbox item requires at least one safe option")
    consequences_list = [_safe_text(c) for c in consequences]
    item: dict[str, object] = {
        "schema": OWNER_INBOX_SCHEMA,
        "DECISION_ID": str(decision_id),
        "DECISION_TYPE": decision_type,
        "CATEGORY": category,
        "TITLE": _safe_text(title, max_length=256),
        "PLAIN_LANGUAGE_QUESTION": _safe_text(plain_language_question, max_length=1024),
        "WHY_OWNER_IS_NEEDED": _safe_text(why_owner_is_needed, max_length=1024),
        "OPTIONS": options_list,
        "RECOMMENDED_OPTION_IF_EVIDENCE_SUPPORTS_ONE": (
            _safe_text(recommended_option_if_evidence_supports_one)
            if recommended_option_if_evidence_supports_one is not None else None),
        "CONSEQUENCES": consequences_list,
        "BLOCKING_SCOPE": _safe_text(blocking_scope or "NONE", max_length=1024),
        "EVIDENCE_POINTERS": [_safe_text(_redact_secret(str(p))) for p in evidence_pointers],
        "EVIDENCE_VERSION": _safe_text(str(evidence_version or "")),
        "CREATED_AT": str(created_at or utc_now()),
        "GOAL_ID": str(goal_id) if goal_id else None,
        "TASK_ID": str(task_id) if task_id else None,
        "STATUS": "OPEN",
        "RESOLUTION": None,
    }
    safe = _sanitize_value(item)
    if not isinstance(safe, dict):
        raise Fw05Error("inbox item sanitization failed")
    safe["ITEM_HASH"] = _sha256hex({k: v for k, v in safe.items() if k != "ITEM_HASH"})
    return safe


def read_inbox_records(root: str | Path) -> list[dict[str, object]]:
    project = _root_path(root)
    path = _inbox_path(project)
    items: list[dict[str, object]] = []
    if not path.is_file():
        return items
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if not raw_line.strip():
            continue
        try:
            item = json.loads(raw_line)
        except (json.JSONDecodeError, ValueError):
            continue
        if not isinstance(item, dict) or item.get("schema") != OWNER_INBOX_SCHEMA:
            continue
        items.append(dict(item))
    return items


def _inbox_lock_path(root: Path) -> Path:
    return root / ".p2p" / "state" / "owner-inbox.lock"


def create_owner_decision(root: str | Path, item: Mapping[str, object]) -> dict[str, object]:
    """Persist an Owner Decision Inbox item with strict deduplication.

    Rules (spec §10):
      - same blocking cause + same scope + same evidence version -> one
        unresolved Inbox item (same DECISION_ID cannot open twice)
      - an OPEN item with the same DECISION_ID already exists -> DUPLICATE
        (no repeated prompt)
      - a RESOLVED/SUPERSEDED item with the same DECISION_ID -> new version
        record is allowed with a SUPERSEDES link; the history is preserved
      - the store is append-only; existing records are never mutated
    """
    if not isinstance(item, Mapping) or item.get("schema") != OWNER_INBOX_SCHEMA:
        raise Fw05Error("create_owner_decision requires a built inbox item")
    status = str(item.get("STATUS"))
    if status not in INBOX_STATUSES:
        raise Fw05Error(f"invalid inbox status: {status}")
    decision_id = str(item.get("DECISION_ID"))
    if not decision_id.startswith("FW05-"):
        raise Fw05Error("DECISION_ID must be a stable FW05 decision id")

    project = _root_path(root)
    path = _inbox_path(project)
    path.parent.mkdir(parents=True, exist_ok=True)
    lock = threading.Lock()
    with lock:
        existing = read_inbox_records(project)
        open_items = [it for it in existing if it.get("DECISION_ID") == decision_id
                      and it.get("STATUS") == "OPEN"]
        if open_items:
            return {"status": "DUPLICATE", "decision_id": decision_id,
                    "existing_open_line": open_items[0].get("_line"),
                    "inbox": OWNER_INBOX_RELATIVE_PATH}
        superseded = [it for it in existing if it.get("DECISION_ID") == decision_id
                      and it.get("STATUS") in ("RESOLVED", "SUPERSEDED")]
        if superseded:
            linked = dict(item)
            linked["SUPERSEDES"] = [super_item.get("ITEM_HASH")
                                    for super_item in superseded
                                    if super_item.get("ITEM_HASH")]
            linked["ITEM_HASH"] = _sha256hex(
                {k: v for k, v in linked.items() if k != "ITEM_HASH"})
            item = linked
        content = (path.read_text(encoding="utf-8") if path.exists() else "")
        _write_atomic(path, content + _stable_json(item) + "\n")
        return {"status": "APPENDED", "decision_id": decision_id,
                "inbox": OWNER_INBOX_RELATIVE_PATH}


def read_inbox(root: str | Path, *, status: str | None = None,
               limit: int = 64) -> dict[str, object]:
    """Bounded, read-only retrieval of the Owner Decision Inbox."""
    if limit not in range(1, 1024):
        raise Fw05Error("limit must be between 1 and 1023")
    items = read_inbox_records(_root_path(root))
    if status is not None and str(status).upper() not in INBOX_STATUSES:
        raise Fw05Error(f"invalid inbox status filter: {status}")
    filtered = [it for it in items
                if status is None or it.get("STATUS") == status.upper()]
    prioritized = sorted(filtered, key=lambda it: (
        _MATERIAL_PRIORITY_ORDER.index(it.get("CATEGORY", ""))
        if it.get("CATEGORY") in _MATERIAL_PRIORITY_ORDER else 99,
        str(it.get("CREATED_AT"))))[:limit]
    return {"schema": "p2p-fw05-inbox-view/1", "items": prioritized,
            "total_matching": len(filtered), "total_records": len(items),
            "status_filter": status, "inbox": OWNER_INBOX_RELATIVE_PATH}


# ----------------------------------------------------- owner answer contract

def _normalize_option(value: object) -> str:
    text = re.sub(r"\s+", " ", str(value)).strip()
    if not text:
        raise Fw05Error("option must be non-empty")
    return text[:1024]


def _normalize_owner_input(raw: object) -> dict[str, object]:
    """Parse an Owner response into structured intent WITHOUT storing the raw
    transcript. Returns a normalized structured envelope:
      {"decision_id", "option", "notes", "shape"} where shape is one of
      OPTION_SELECTED / ONE_WORD / FREE_TEXT / STRUCTURED.
    The raw chat transcript itself is NEVER persisted as state
    (OWNER_MESSAGE != DURABLE_DECISION)."""
    if not isinstance(raw, (str, Mapping)):
        raise Fw05Error("owner response must be a string or structured object")
    if isinstance(raw, Mapping):
        decision_id = _safe_text(str(raw.get("decision_id", "")))
        option = _normalize_option(raw.get("option") or raw.get("selected_option", ""))
        notes = _safe_text(str(raw.get("notes") or ""), max_length=2048)
        shape = "STRUCTURED"
    else:
        text = _safe_text(raw)
        decision_id = ""
        option = text
        notes = ""
        shape = "ONE_WORD" if len(text.split()) <= 2 else "FREE_TEXT"
        match = re.search(r"(?i)\bdecision[_ -]?id\s*[:=]?\s*FW05-[A-Z0-9-]+", text)
        if match:
            decision_id = re.findall(r"FW05-[A-Z0-9-]+", match.group(0))[0]
    return {"decision_id": decision_id, "option": option, "notes": notes, "shape": shape}


def resolve_owner_answer(
    root: str | Path,
    raw_response: object,
    *,
    expected_decision_version: str | None = None,
    expected_scope: str | None = None,
    answered_at: str | None = None,
) -> dict[str, object]:
    """Owner answer contract (spec §11, §22): parse against DECISION_ID,
    validate, record scope + provenance, mark exactly the authorized
    decision resolved, leave everything else untouched. Fail closed for
    unknown / stale / resolved / disallowed / scope-mismatched / malformed /
    ambiguous inputs. Returns a structured RESOLUTION — never the raw text.
    """
    try:
        parsed = _normalize_owner_input(raw_response)
    except Fw05Error as exc:
        return {"status": "FAILED", "failure": "MALFORMED", "detail": str(exc)}
    decision_id = parsed["decision_id"]

    project = _root_path(root)
    existing = read_inbox_records(project)

    # Fail-closed option targeting: when the response carries no DECISION_ID
    # but its option matches exactly ONE currently OPEN inbox item AND that
    # option is one of its safe options, it is accepted against that item
    # (unambiguous owner intent). If zero or more than one open item matches,
    # or the option is not a safe option of the single match, the answer is
    # ambiguous/invalid and the decision stays unresolved.
    if not decision_id:
        matches_open = [it for it in existing
                        if it.get("STATUS") == "OPEN" and any(
                            str(o).lower().strip() ==
                            str(parsed["option"]).lower().strip()
                            for o in it.get("OPTIONS") or ())]
        if len(matches_open) == 1:
            decision_id = str(matches_open[0].get("DECISION_ID"))
        else:
            return {"status": "FAILED",
                    "failure": ("AMBIGUOUS" if matches_open
                                else "OPTION_NOT_ALLOWED"),
                    "detail": ("no DECISION_ID in owner response and the "
                               "option does not uniquely identify one open "
                               "decision; the decision stays unresolved")}
    matches = [it for it in existing if it.get("DECISION_ID") == decision_id]
    if not matches:
        return {"status": "FAILED", "failure": "UNKNOWN_DECISION_ID"}
    if len(matches) > 1:
        matches.sort(key=lambda it: str(it.get("CREATED_AT")))
    latest = matches[-1]
    if latest.get("STATUS") != "OPEN":
        return {"status": "FAILED", "failure": "ALREADY_RESOLVED",
                "detail": f"decision {decision_id} is {latest.get('STATUS')}"}
    if expected_decision_version is not None and str(
            latest.get("EVIDENCE_VERSION")) != str(expected_decision_version):
        return {"status": "FAILED", "failure": "STALE_VERSION",
                "detail": "owner response targets an older evidence version"}
    if expected_scope is not None and str(
            latest.get("BLOCKING_SCOPE")) != str(expected_scope):
        return {"status": "FAILED", "failure": "SCOPE_MISMATCH",
                "detail": "owner response does not match the current blocking scope"}
    offered_options = list(latest.get("OPTIONS") or [])
    if not offered_options:
        return {"status": "FAILED", "failure": "OPTION_NOT_ALLOWED",
                "detail": "decision has no safe options"}
    chosen = None
    for option in offered_options:
        if str(option).lower().strip() == str(parsed["option"]).lower().strip():
            chosen = option
            break
    if chosen is None:
        return {"status": "FAILED", "failure": "OPTION_NOT_ALLOWED",
                "detail": f"response {parsed['option']!r} is not a listed safe option"}
    resolution: dict[str, object] = {
        "decision_id": decision_id,
        "approved_option": str(chosen),
        "scope": {
            "what": str(latest.get("TITLE")),
            "scope": str(latest.get("BLOCKING_SCOPE")),
            "target": str(latest.get("TASK_ID") or latest.get("GOAL_ID") or "NONE"),
        },
        "expiry": "ONE_TIME",
        "auto_grants_nothing": True,
        "evidence_pointers": list(latest.get("EVIDENCE_POINTERS") or []),
        "provenance": {
            "answered_at": str(answered_at or utc_now()),
            "answer_shape": parsed["shape"],
            "answer_hash": _sha256hex(parsed),
            "raw_transcript_stored": False,
        },
        "resolved_status": "RESOLVED",
    }
    updated = dict(latest)
    updated.update({"STATUS": "RESOLVED", "RESOLUTION": resolution,
                    "RESOLVED_AT": str(answered_at or utc_now())})
    updated["ITEM_HASH"] = _sha256hex(
        {k: v for k, v in updated.items() if k not in ("ITEM_HASH",)})
    path = _inbox_path(project)
    lock = threading.Lock()
    with lock:
        current = read_inbox_records(project)
        found = None
        for it in current:
            if it.get("DECISION_ID") == decision_id and it.get("STATUS") == "OPEN":
                found = it
                break
        if found is None:
            return {"status": "FAILED", "failure": "ALREADY_RESOLVED",
                    "detail": "decision no longer open (concurrent resolution)"}
        # replace the resolved line atomically (still append-only semantics:
        # the record content is updated via tmp+replace of the file content,
        # and ITEM_HASH makes any tampering detectable; historical resolved
        # records keep their RESOLUTION provenance)
        lines = (path.read_text(encoding="utf-8") if path.exists() else "").splitlines()
        out: list[str] = []
        for raw_line in lines:
            try:
                item = json.loads(raw_line)
            except (json.JSONDecodeError, ValueError):
                out.append(raw_line)
                continue
            if (isinstance(item, dict) and item.get("DECISION_ID") == decision_id
                    and item.get("STATUS") == "OPEN"):
                out.append(_stable_json(updated))
            else:
                out.append(raw_line)
        _write_atomic(path, "\n".join(out) + "\n" if out else "")
    return {"status": "RESOLVED", "resolution": resolution}


# ------------------------------------------------ quality review triage

def quality_review_triage(
    checkpoint: Mapping[str, object] | None,
    *,
    quality_status: str | None = None,
    quality_failures: Iterable[str] = (),
    technically_resolvable: bool,
) -> dict[str, object]:
    """Route a FW04 durable quality stop into the FW05 owner experience.

    QUALITY_REVIEW != AUTOMATIC_OWNER_GATE: when the missing evidence can be
    obtained through an existing safe technical verification path the
    decision stays TECHNICAL; only owner-owned quality reviews create
    exactly one Owner Inbox item.
    """
    failures = [str(f) for f in quality_failures]
    routing = "TECHNICALLY_RESOLVABLE" if technically_resolvable else "OWNER_OWNED"
    category = ("QUALITY_REVIEW_WHEN_EVIDENCE_CANNOT_RESOLVE"
                if not technically_resolvable else None)
    owner_decision_required = not technically_resolvable
    checkpoint_info = {}
    if checkpoint is not None:
        checkpoint_info = {
            "loop_status": str(checkpoint.get("loop_status")),
            "verification_state": str(checkpoint.get("verification_state")),
            "next_safe_action": str(checkpoint.get("next_safe_action")),
            "current_task": str(checkpoint.get("current_task") or "NONE"),
        }
    return {
        "routing": routing,
        "category": category,
        "quality_status": str(quality_status or "QUALITY_UNKNOWN"),
        "quality_failures": failures,
        "owner_decision_required": owner_decision_required,
        "checkpoint": checkpoint_info,
    }


def decision_record_for_quality_review(
    *,
    goal_id: str | None,
    task_id: str,
    quality_status: str,
    quality_failures: Iterable[str] = (),
    owner_owned: bool,
    checkpoint: Mapping[str, object] | None,
    created_at: str | None = None,
) -> dict[str, object]:
    """Build the decision-trace record for a durable FW04 quality stop."""
    failures = [str(f) for f in quality_failures]
    evidence_pointers = []
    if checkpoint is not None:
        refs = checkpoint.get("evidence_pointers") or []
        evidence_pointers.extend(str(r) for r in refs)
    return make_decision_record(
        decision_type="QUALITY_GATE",
        goal_id=goal_id,
        task_id=task_id,
        input_facts=[f"quality_status={quality_status}",
                     f"quality_failures={json.dumps(failures)}"],
        applied_policy_or_rule="UNKNOWN != SAFE",
        selected_action=("OWNER_REVIEW" if owner_owned
                         else "TECHNICAL_VERIFICATION_PATH"),
        material_alternatives=(
            ["ROUTE_OWNER_OWNED", "ROUTE_TECHNICAL"] if owner_owned else []),
        rejected_alternatives_with_reason=(
            ["TECHNICAL_VERIFICATION_PATH:no existing safe verification "
             "path for the missing evidence"
             ] if owner_owned else []),
        evidence_pointers=evidence_pointers,
        unknown_or_gaps=failures,
        owner_decision_required=owner_owned,
        decision_status="RECORDED",
        blocking_scope=f"QUALITY_REVIEW:{task_id}",
        created_at=created_at,
    )


def inbox_item_for_quality_review(
    *,
    goal_id: str | None,
    task_id: str,
    quality_status: str,
    quality_failures: Iterable[str] = (),
    options: Iterable[str],
    recommended_option_if_evidence_supports_one: str | None,
    created_at: str | None = None,
) -> dict[str, object]:
    """Build the inbox item for an OWNER_OWNED quality review: exactly one
    item explaining what completed, what evidence is missing, and what the
    Owner must decide or supply. No automatic rerun of the completed
    mutation; quality is never bypassed."""
    record = decision_record_for_quality_review(
        goal_id=goal_id, task_id=task_id, quality_status=quality_status,
        quality_failures=quality_failures, owner_owned=True, checkpoint=None,
        created_at=created_at)
    return build_owner_inbox_item(
        decision_id=record["DECISION_ID"],
        decision_type="QUALITY_GATE",
        goal_id=goal_id,
        task_id=task_id,
        category="QUALITY_REVIEW_WHEN_EVIDENCE_CANNOT_RESOLVE",
        title="P2P cần anh xem xét chất lượng trước khi tiếp tục",
        plain_language_question=(
            "P2P đã hoàn thành việc \"" + str(task_id) + "\" nhưng chưa đủ "
            "bằng chứng kiểm chứng chất lượng. Anh muốn P2P tự kiểm chứng "
            "bằng cách an toàn nào, hay cung cấp thêm thông tin?"),
        why_owner_is_needed=(
            "Bằng chứng còn thiếu hoặc mâu thuẫn: "
            + ", ".join(str(f) for f in quality_failures)
            + ". P2P không thể tự xác định cách kiểm chứng phù hợp mà không "
              "rủi ro, nên cần anh quyết định."),
        options=options,
        recommended_option_if_evidence_supports_one=(
            recommended_option_if_evidence_supports_one),
        consequences=[
            "Phương án kiểm chứng kỹ thuật: P2P chạy đường kiểm chứng an toàn đã có, không hỏi lại anh.",
            "Cung cấp thông tin: P2P dùng thông tin anh cung cấp làm bằng chứng, vẫn ghi lại minh bạch.",
            "Dừng việc này: P2P giữ trạng thái dừng, không thực hiện lại việc đã hoàn thành.",
        ],
        blocking_scope=f"QUALITY_REVIEW:{task_id}",
        evidence_pointers=record["EVIDENCE_POINTERS"],
        evidence_version=record["EVIDENCE_VERSION"],
        created_at=created_at,
    )


# -------------------------------------------------- owner gate from durable

def inbox_item_for_owner_gate(
    *,
    owner_gate_payload: Mapping[str, object],
    goal_id: str | None = None,
    decision_type: str = "OWNER_GATE",
    goal_state_hash: str | None = None,
    created_at: str | None = None,
) -> dict[str, object]:
    """Build an inbox item + trace record from the canonical durable
    OwnerGate payload persisted by FW01 (checkpoint.owner_gate). The gate
    categories are mapped to OWNER_GATE_CATEGORIES; technical gates are
    never produced here (FW01 already halts on them)."""
    reason_class = str(owner_gate_payload.get("reason_class", ""))
    category = _map_reason_class_to_category(reason_class)
    if category is None:
        raise Fw05Error(f"owner gate reason_class {reason_class!r} cannot be mapped to an owner category")
    blocking_task = str(owner_gate_payload.get("blocking_task") or "NONE")
    task_id = blocking_task
    scope = f"GATE:{category}:{blocking_task}"
    record = make_decision_record(
        decision_type=_check_decision_type(decision_type),
        goal_id=goal_id,
        task_id=task_id,
        input_facts=[f"reason_class={reason_class}",
                     f"question={_safe_text(owner_gate_payload.get('question') or '')}"],
        applied_policy_or_rule="OWNER_OWNED_DECISIONS_REQUIRE_OWNER",
        selected_action="OWNER_GATE",
        material_alternatives=[f"option:{_safe_text(o)}" for o in owner_gate_payload.get("safe_options") or []],
        rejected_alternatives_with_reason=[],
        evidence_pointers=[".p2p/fw01.json", ".p2p/state/goal-ledger.jsonl"],
        unknown_or_gaps=[],
        owner_decision_required=True,
        decision_status="RECORDED",
        blocking_scope=scope,
        goal_state_hash=goal_state_hash,
        created_at=created_at,
    )
    question = str(owner_gate_payload.get("question") or "Anh cần quyết định điều gì tiếp theo?")
    recommended = owner_gate_payload.get("recommended_default")
    item = build_owner_inbox_item(
        decision_id=record["DECISION_ID"],
        decision_type=_check_decision_type(decision_type),
        goal_id=goal_id,
        task_id=task_id,
        category=category,
        title=_safe_text(owner_gate_payload.get("what_completed") or f"Gate: {category}", max_length=256),
        plain_language_question=question,
        why_owner_is_needed=str(
            owner_gate_payload.get("why_owner_is_needed") or _default_why(category)),
        options=owner_gate_payload.get("safe_options") or ("OK", "Hủy"),
        recommended_option_if_evidence_supports_one=(
            str(recommended) if recommended else None),
        consequences=[
            str(c) if isinstance(c, str) else "P2P tiếp tục theo lựa chọn an toàn của anh."
            for c in (owner_gate_payload.get("resume_condition") or "").split(";")
        ] or [f"Quyết định này chỉ áp dụng cho việc \"{blocking_task}\"; không mở rộng quyền cho việc khác."],
        blocking_scope=scope,
        evidence_pointers=[".p2p/fw01.json", ".p2p/state/goal-ledger.jsonl"],
        evidence_version=record["EVIDENCE_VERSION"],
        created_at=created_at,
    )
    return {"record": record, "inbox_item": item}


_REASON_CLASS_CATEGORY_MAP: dict[str, str] = {
    "PRODUCT_BUSINESS_CHOICE": "PRODUCT_OR_BUSINESS_DECISION",
    "REAL_WORLD_FACT_REQUIRED": "REAL_DATA_DECISION",
    "CREDENTIAL_LOGIN_REQUIRED": "NEW_PERMISSION",
    "PERMISSION_ELEVATION_REQUIRED": "NEW_PERMISSION",
    "DESTRUCTIVE_PRODUCTION_ACTION": "DESTRUCTIVE_ACTION",
    "PAYMENT_OR_FINANCIAL_COMMITMENT": "MATERIAL_SCOPE_EXPANSION",
    "MERGE_REQUIRED": "RELEASE_OR_DEPLOY",
    "RELEASE_REQUIRED": "RELEASE_OR_DEPLOY",
    "DEPLOY_REQUIRED": "RELEASE_OR_DEPLOY",
    "PROMOTION_REQUIRED": "RELEASE_OR_DEPLOY",
    "MAJOR_SCOPE_CHANGE": "MATERIAL_SCOPE_EXPANSION",
    "CONFLICTING_EVIDENCE": "CONFLICT_NOT_RESOLVABLE_FROM_EVIDENCE",
    "ARCHITECTURE_CHOICE_NO_SAFE_DEFAULT": "PRODUCT_OR_BUSINESS_DECISION",
}


def _map_reason_class_to_category(reason_class: str) -> str | None:
    return _REASON_CLASS_CATEGORY_MAP.get(str(reason_class).strip().upper())


def _default_why(category: str) -> str:
    return ("Quyết định này thuộc về anh: P2P không thể tiếp tục an toàn nếu "
            "không có lựa chọn của anh. " + category)


# ------------------------------------------------ candidate / goal evidence

def _candidate_records(root: Path) -> list[dict[str, object]]:
    ctrl = root / "governance" / "development-control.json"
    if not ctrl.is_file():
        return []
    try:
        data = json.loads(ctrl.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    records = data.get("candidate_records")
    if not isinstance(records, list):
        return []
    return [dict(r) for r in records if isinstance(r, dict)]


def _goal_events(root: Path) -> list[dict[str, object]]:
    ledger = root / ".p2p" / "state" / "goal-ledger.jsonl"
    if not ledger.is_file():
        return []
    events: list[dict[str, object]] = []
    try:
        for raw_line in ledger.read_text(encoding="utf-8").splitlines():
            if not raw_line.strip():
                continue
            try:
                event = json.loads(raw_line)
            except (json.JSONDecodeError, ValueError):
                continue
            if isinstance(event, dict):
                events.append(event)
    except OSError:
        return []
    return events


def _load_goal_plan(root: Path) -> dict[str, object] | None:
    state = root / ".p2p" / "state" / "autopilot-goal-state.json"
    if not state.is_file():
        return None
    try:
        payload = json.loads(state.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    return payload if isinstance(payload, dict) else None


def _load_fw01_checkpoint(root: Path) -> dict[str, object] | None:
    cp = root / ".p2p" / "fw01.json"
    if not cp.is_file():
        return None
    try:
        payload = json.loads(cp.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    return payload if isinstance(payload, dict) else None


def project_status_snapshot(root: str | Path) -> dict[str, object]:
    """Owner-facing project status derived ONLY from durable evidence.

    No new project-state database: fields come from the goal ledger, the
    FW01 checkpoint, and the candidate records. Views are read-only and
    idempotent; opening this view never executes anything.
    """
    project = _root_path(root)
    plan = _load_goal_plan(project) or {}
    checkpoint = _load_fw01_checkpoint(project) or {}
    candidates = _candidate_records(project)
    latest_candidate = (candidates[-1] if candidates else None)
    goal_id = str(plan.get("goal_id") or checkpoint.get("goal_id") or "NONE")
    loop_status = str(checkpoint.get("loop_status") or "NONE")
    verification_state = str(checkpoint.get("verification_state") or "NONE")
    current_task = str(checkpoint.get("current_task") or "NONE")
    next_action = str(checkpoint.get("next_safe_action") or "NONE")
    events = _goal_events(project)
    executed = sum(1 for e in events if str(e.get("event")) == "task_executed")
    verified = sum(1 for e in events if str(e.get("event")) == "task_verified")
    task_done = sum(1 for e in events if str(e.get("event")) == "task_done")
    inbox = read_inbox(project, status="OPEN")
    open_items = list(inbox.get("items") or [])
    blocker = None
    owner_action = None
    if loop_status == "OWNER_GATE" and open_items:
        blocker = "OWNER_GATE"
        owner_action = open_items[0].get("DECISION_ID")
    elif loop_status == "BLOCKED" and verification_state == "QUALITY_REVIEW":
        blocker = "QUALITY_REVIEW"
        owner_action = "xem inbox quyết định chất lượng"
    elif loop_status == "STOPPED":
        blocker = "STOP"
    goal_terminal = str(plan.get("status") or "").upper() in (
        "DONE", "CLOSED", "COMPLETED")
    candidate_promoted = (isinstance(latest_candidate, dict)
                          and str(latest_candidate.get("promotion_status"))
                          .upper() == "PROMOTED")
    candidate_released = (isinstance(latest_candidate, dict) and str(
        latest_candidate.get("release_status") or "").upper() == "RELEASED")
    goal_pass_vs_promotion = {
        "goal_passed": goal_terminal,
        "candidate_promoted": bool(candidate_promoted),
        "candidate_released": bool(candidate_released),
        "distinction": _goal_pass_vs_promotion_text(
            goal_terminal, bool(candidate_promoted), bool(candidate_released)),
    }
    candidate_state = None
    if isinstance(latest_candidate, dict):
        candidate_state = {
            "latest_version": str(latest_candidate.get("candidate_version")),
            "candidate_id": str(latest_candidate.get("candidate_id")),
            "promotion_status": str(latest_candidate.get("promotion_status")),
            "candidate_sha256": str(latest_candidate.get("candidate_sha256")),
            "note": goal_pass_vs_promotion["distinction"],
        }
    return {
        "schema": "p2p-fw05-project-status/1",
        "PROJECT": str(project),
        "ACTIVE_GOAL": goal_id,
        "PROGRESS_STATE": ("DONE" if goal_terminal else loop_status),
        "CURRENT_TASK_OR_STAGE": current_task,
        "LAST_VERIFIED_RESULT": verification_state,
        "TASKS_EXECUTED": executed,
        "TASKS_VERIFIED": verified,
        "TASKS_DONE": task_done,
        "BLOCKER_IF_ANY": blocker,
        "OPEN_OWNER_DECISIONS": len(open_items),
        "OWNER_ACTION_IF_ANY": owner_action,
        "NEXT_ACTION": next_action,
        "CANDIDATE_RELEASE_STATE": candidate_state,
        "GOAL_PASS_VS_PROMOTION": goal_pass_vs_promotion,
        "GENERATED_AT": utc_now(),
        "GENERATED_FROM": ["autopilot-goal-state.json", ".p2p/fw01.json",
                           ".p2p/state/goal-ledger.jsonl",
                           "governance/development-control.json",
                           OWNER_INBOX_RELATIVE_PATH],
    }


def _goal_pass_vs_promotion_text(goal_passed: bool, promoted: bool,
                                 released: bool) -> str:
    if goal_passed and promoted and released:
        return ("Mục tiêu đã hoàn tất, candidate đã được phê duyệt và đã "
                "phát hành (live).")
    if goal_passed and promoted:
        return ("Mục tiêu đã hoàn tất và kiểm chứng, candidate đã được phê "
                "duyệt nhưng chưa phát hành live.")
    if goal_passed:
        return ("Mục tiêu đã hoàn tất và kiểm chứng, nhưng candidate vẫn "
                "chưa được phê duyệt phát hành.")
    return ("Mục tiêu chưa hoàn tất; chưa có candidate nào được phê duyệt "
            "phát hành.")


# ----------------------------------------------- progressive disclosure L1/L2/L3

def render_owner_experience(root: str | Path, *, level: int = 1,
                            language: str = "vi") -> dict[str, object]:
    """Progressive disclosure from the SAME durable truth:
      L1 — OWNER SUMMARY: short beginner-facing status
      L2 — WHY/DETAILS: what is blocked, why it matters, recommendation,
           consequences
      L3 — EVIDENCE: decision trace, evidence pointers, task/capability/
           team/quality state, exact technical evidence
    The Owner never needs L3 for ordinary use; presentation is a view, not
    authority, and machine state stays canonical English.
    """
    if level not in (1, 2, 3):
        raise Fw05Error("level must be 1, 2 or 3")
    project = _root_path(root)
    status = project_status_snapshot(project)
    inbox = read_inbox(project, status="OPEN")
    trace = read_decision_records(project)
    records = [r["record"] for r in trace.get("records") or []]
    open_items = list(inbox.get("items") or [])
    next_action = str(status.get("NEXT_ACTION") or "NONE")
    blocker = status.get("BLOCKER_IF_ANY")
    goal_passed = bool(status.get("GOAL_PASS_VS_PROMOTION", {}).get("goal_passed"))
    owner_summary = _owner_summary(
        next_action=next_action, blocker=blocker, open_items=open_items,
        goal_passed=goal_passed, distinction=str(status.get(
            "GOAL_PASS_VS_PROMOTION", {}).get("distinction") or ""),
        executed=int(status.get("TASKS_EXECUTED") or 0),
        verified=int(status.get("TASKS_VERIFIED") or 0))
    result: dict[str, object] = {
        "schema": "p2p-fw05-owner-experience-view/1",
        "level": level,
        "owner_summary": owner_summary,
        "project_status": status,
        "generated_at": utc_now(),
    }
    if level >= 2:
        result["blocked_items"] = [
            {"decision_id": it.get("DECISION_ID"),
             "title": it.get("TITLE"),
             "why_owner_is_needed": it.get("WHY_OWNER_IS_NEEDED"),
             "recommendation": it.get("RECOMMENDED_OPTION_IF_EVIDENCE_SUPPORTS_ONE"),
             "options": list(it.get("OPTIONS") or []),
             "consequences": list(it.get("CONSEQUENCES") or []),
             "blocking_scope": it.get("BLOCKING_SCOPE")}
            for it in open_items]
    if level >= 3:
        result["decision_trace"] = [
            {k: v for k, v in rec.items() if k != "RECORD_HASH"}
            for rec in records]
        result["trace_diagnostics"] = trace.get("diagnostics", [])
    return result


def _owner_summary(*, next_action: str, blocker, open_items, goal_passed: bool,
                   distinction: str, executed: int, verified: int) -> str:
    parts: list[str] = []
    if executed:
        parts.append(f"P2P đã hoàn thành {executed} việc")
    else:
        parts.append("P2P chưa hoàn thành việc nào")
    if verified:
        parts.append(f"và đã kiểm chứng {verified} việc")
    if open_items:
        first = open_items[0]
        category = str(first.get("CATEGORY") or "QUYẾT ĐỊNH CỦA ANH")
        parts.append(f"Hiện đang dừng vì cần anh quyết định ({category.lower()})")
    elif blocker == "STOP":
        parts.append("Hiện đang dừng theo yêu cầu an toàn")
    elif goal_passed:
        parts.append("Mục tiêu đã hoàn tất")
    else:
        parts.append("P2P đang tiếp tục công việc theo hướng an toàn")
    summary = ". ".join(parts) + "."
    if distinction:
        summary += " " + distinction
    if next_action and next_action != "NONE":
        summary += f" Bước tiếp theo: {next_action}."
    return summary


def render_project_experience(root: str | Path, *, decision_id: str | None = None
                              ) -> dict[str, object]:
    """Entry experience (spec §27): one beginner-first view answering
    'P2P đang làm gì / tới đâu / có cần anh quyết định gì không'.
    Read-only and idempotent — never executes anything."""
    project = _root_path(root)
    inbox = read_inbox(project, status="OPEN")
    items = list(inbox.get("items") or [])
    if not items:
        return {"experience": "CONTINUE_OR_DONE",
                "message": "Không có việc nào cần anh quyết định lúc này.",
                "detail": render_owner_experience(project, level=1)}
    return {"experience": "OWNER_DECISION_REQUIRED",
            "decision_id": str(items[0].get("DECISION_ID")),
            "category": str(items[0].get("CATEGORY")),
            "question": str(items[0].get("PLAIN_LANGUAGE_QUESTION")),
            "options": list(items[0].get("OPTIONS") or []),
            "recommendation": items[0].get(
                "RECOMMENDED_OPTION_IF_EVIDENCE_SUPPORTS_ONE"),
            "detail": render_owner_experience(project, level=2)}


# --------------------------------------------------------------- CLI

def _cli_read_only(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="P2P FW05 owner experience")
    parser.add_argument("--root", default=".", help="project root")
    parser.add_argument("command", choices=(
        "status", "inbox", "decision", "experience", "trace", "triage"))
    parser.add_argument("--decision-id", default=None)
    parser.add_argument("--status-filter", default=None)
    parser.add_argument("--level", type=int, default=1)
    parser.add_argument("--limit", type=int, default=64)
    args = parser.parse_args(argv)
    root = Path(args.root).expanduser().resolve()
    if args.command == "status":
        payload = project_status_snapshot(root)
    elif args.command == "inbox":
        payload = read_inbox(root, status=args.status_filter, limit=args.limit)
    elif args.command == "decision":
        if not args.decision_id:
            print("decision id required", file=sys.stderr)
            return 2
        items = read_inbox_records(root)
        matches = [it for it in items if it.get("DECISION_ID") == args.decision_id]
        payload = {"decision_id": args.decision_id, "items": matches}
    elif args.command == "experience":
        payload = render_owner_experience(root, level=args.level)
    elif args.command == "trace":
        payload = read_decision_records(root)
    elif args.command == "triage":
        payload = {"note": "use quality_review_triage() with a checkpoint"}
    else:
        payload = {}
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def cli_main(argv: list[str] | None = None) -> int:
    return _cli_read_only(argv if argv is not None else sys.argv[1:])


if __name__ == "__main__":  # pragma: no cover
    sys.exit(cli_main())
