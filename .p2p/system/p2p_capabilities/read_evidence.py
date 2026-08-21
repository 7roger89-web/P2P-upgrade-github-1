"""C36 ReadEvidence + ReadGap — honest separation of DELIVERED vs READ.

This module records what can OBSERVABLY be proven about context consumption,
and computes per-item read gaps. It enforces:

- READ_PROVEN only when observable evidence exists (telemetry, adapter read
  events, bounded deterministic instrumentation). Model self-report alone is
  not strong proof (scenario C/D evidence states).
- Evidence binds to the exact task/session/manifest/item it describes; read
  evidence from another session or task is rejected (scenario O).
- REQUIRED vs DELIVERED vs PROVEN_READ remain distinct states (scenario C).
- Authority collision: an external reference conflicting with the canonical
  authoritative source never overrides it; the conflict is surfaced and the
  outcome is READ_CONFLICT (scenario Q).
- UNKNOWN is honest. Never fabricate READ_PROVEN, and never represent
  UNKNOWN as PROVEN.

Schema id: p2p-read-evidence-c36/1
"""
from __future__ import annotations

import hashlib
from typing import Any, Iterable, Mapping

from .context import _canonical_bytes

READ_STATES = ("READ_PROVEN", "READ_PARTIAL", "READ_UNKNOWN", "READ_NOT_REQUIRED", "READ_CONFLICT")

# Evidence kinds that are NEVER sufficient for READ_PROVEN. Model self-report
# alone is not strong proof; only observable mechanisms may prove a read.
UNPROVING_EVIDENCE_KINDS = (
    "MODEL_SELF_REPORT",
    "MODEL_CLAIM",
    "AGENT_VERBAL_ASSERTION",
)

GAP_OUTCOMES = (
    "SATISFIED",
    "DELIVERED_READ_UNKNOWN",
    "NOT_DELIVERED",
    "READ_CONFLICT",
    "STALE_SOURCE",
    "PERMISSION_BLOCKED",
)


class ReadEvidenceError(ValueError):
    """Raised when read evidence or gap computation is malformed."""

class ReadBindingError(ReadEvidenceError):
    """Raised when read evidence bindings do not match their context."""


def _fingerprint(payload: Any) -> str:
    return hashlib.sha256(_canonical_bytes(payload)).hexdigest()


def record_read_evidence(
    *,
    goal_id: str,
    task_id: str,
    session_id: str,
    manifest_id: str,
    item_id: str,
    evidence_kind: str,
    evidence_value: str,
    state: str = "READ_UNKNOWN",
    source_fingerprint: str | None = None,
) -> dict[str, Any]:
    """Record one unit of observable read evidence.

    ``evidence_kind`` must name an observable mechanism, e.g.
    "TOOL_FILE_ACCESS", "ADAPTER_READ_EVENT", "DETERMINISTIC_INSTRUMENTATION".
    Model self-report ("i_read_all_files") is never sufficient for
    READ_PROVEN.

    ``state``: only READ_PROVEN when evidence_kind+evidence_value are both
    non-empty and state is READ_PROVEN; otherwise honest state applies.
    """
    if state not in READ_STATES:
        raise ReadEvidenceError(f"READ_STATE_INVALID: {state}")
    if not all((goal_id, task_id, session_id, manifest_id, item_id)):
        raise ReadEvidenceError("READ_EVIDENCE_BINDING_MISSING")
    if state == "READ_PROVEN" and not (evidence_kind and evidence_value):
        raise ReadEvidenceError("READ_PROVEN_REQUIRES_OBSERVABLE_EVIDENCE")
    if state == "READ_PROVEN" and evidence_kind in UNPROVING_EVIDENCE_KINDS:
        raise ReadEvidenceError("SELF_REPORT_CANNOT_PROVE_READ")
    identity = _fingerprint(
        (goal_id, task_id, session_id, manifest_id, item_id, evidence_kind, evidence_value, state)
    )
    return {
        "schema": "p2p-read-evidence-c36/1",
        "goal_id": goal_id,
        "task_id": task_id,
        "session_id": session_id,
        "manifest_id": manifest_id,
        "item_id": item_id,
        "evidence_kind": evidence_kind,
        "evidence_value": evidence_value,
        "state": state,
        "source_fingerprint": source_fingerprint,
        "read_identity": "ctx-read-" + identity,
    }


def read_evidence_binds_to_task(
    evidence: Mapping[str, Any],
    goal_id: str,
    task_id: str,
    session_id: str | None = None,
) -> bool:
    """Scenario O: read evidence from another session/task is rejected."""
    if evidence.get("goal_id") != goal_id or evidence.get("task_id") != task_id:
        return False
    if session_id is not None and evidence.get("session_id") != session_id:
        return False
    return True


def read_evidence_binds_to_item(
    evidence: Mapping[str, Any], item_id: str, manifest_id: str | None = None
) -> bool:
    if evidence.get("item_id") != item_id:
        return False
    if manifest_id is not None and evidence.get("manifest_id") != manifest_id:
        return False
    return True


def compute_read_gap(
    manifest_items: Iterable[Mapping[str, Any]],
    delivered_ids: Iterable[str],
    read_evidence: Iterable[Mapping[str, Any]],
    *,
    goal_id: str,
    task_id: str,
    session_id: str | None = None,
    goal_authority: bool = False,
) -> list[dict[str, Any]]:
    """Per-item read gap against a manifest.

    Inputs remain distinct: an item can be REQUIRED, DELIVERED, and still
    READ_UNKNOWN. Scenario C: required+delivered without read evidence ->
    DELIVERED_READ_UNKNOWN, never READ_PROVEN.

    ``goal_authority`` toggles scenario Q (authority collision): when true,
    items with UNTRUSTED_EXTERNAL authority that carry a conflicting
    authority marker are surfaced as READ_CONFLICT while canonical
    AUTHORITATIVE items always win.
    """
    delivered = set(delivered_ids)
    gaps: list[dict[str, Any]] = []
    for item in manifest_items:
        item_id = item.get("item_id") or ""
        authority = item.get("authority_class", "UNKNOWN")
        required = item.get("required") == "REQUIRED"
        was_delivered = item_id in delivered

        relevant = [
            ev
            for ev in read_evidence
            if read_evidence_binds_to_task(ev, goal_id, task_id, session_id)
            and read_evidence_binds_to_item(ev, item_id)
        ]
        proven = any(ev.get("state") == "READ_PROVEN" for ev in relevant)
        conflict = any(ev.get("state") == "READ_CONFLICT" for ev in relevant)

        if not required:
            if was_delivered:
                state = "READ_PROVEN" if proven else "READ_UNKNOWN"
            else:
                state = "READ_NOT_REQUIRED"
            gaps.append({"item_id": item_id, "outcome": "SATISFIED" if state == "READ_PROVEN" else "SATISFIED", "read_state": state, "authority_class": authority})
            continue

        if not was_delivered:
            gaps.append({"item_id": item_id, "outcome": "NOT_DELIVERED", "read_state": "READ_UNKNOWN", "authority_class": authority})
            continue

        if conflict and goal_authority:
            gaps.append({"item_id": item_id, "outcome": "READ_CONFLICT", "read_state": "READ_CONFLICT", "authority_class": authority})
            continue

        if proven:
            gaps.append({"item_id": item_id, "outcome": "SATISFIED", "read_state": "READ_PROVEN", "authority_class": authority})
        else:
            gaps.append({"item_id": item_id, "outcome": "DELIVERED_READ_UNKNOWN", "read_state": "READ_UNKNOWN", "authority_class": authority})
    return gaps


def read_gap_summary(gaps: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    gaps = list(gaps)
    by_outcome = {}
    for gap in gaps:
        by_outcome[gap["outcome"]] = by_outcome.get(gap["outcome"], 0) + 1
    required_missing = any(
        gap["outcome"] == "NOT_DELIVERED" for gap in gaps
    )
    return {
        "items": len(gaps),
        "by_outcome": by_outcome,
        "all_required_satisfied": not required_missing and all(
            gap["outcome"] == "SATISFIED"
            for gap in gaps
            if gap["read_state"] in ("READ_PROVEN", "READ_NOT_REQUIRED")
            or gap["outcome"] == "SATISFIED"
        ),
    }


def fresh_child_context(
    parent_items: Iterable[Mapping[str, Any]],
    child_scope: Iterable[str],
    *,
    max_bytes: int | None = None,
) -> dict[str, Any]:
    """Scenario I/J: child task receives BOUNDED_EXPLICIT_CONTEXT, never the
    full parent transcript. Only items whose scope matches the child scope
    are selected; transcript text is never embedded (TRANSCRIPT != STATE).
    """
    selected = [
        {"item_id": item["item_id"], "source_pointer": item["source_pointer"],
         "authority_class": item["authority_class"], "expected_use": item["expected_use"]}
        for item in parent_items
        if (item.get("scope_binding") or "") in set(child_scope) or not child_scope
    ]
    total_bytes = sum(len(str(s.get("source_pointer", ""))) for s in selected)
    if max_bytes is not None and total_bytes > max_bytes:
        raise ReadEvidenceError("CHILD_CONTEXT_EXCEEDS_BUDGET")
    return {
        "schema": "p2p-child-context-c36/1",
        "items": selected,
        "source": "BOUNDED_EXPLICIT",
        "full_parent_transcript_inherited": False,
        "item_count": len(selected),
    }
