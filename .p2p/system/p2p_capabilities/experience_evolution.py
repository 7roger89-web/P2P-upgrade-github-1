"""Evidence-grounded reusable experience for P2P.

Lifecycle: CANDIDATE -> VERIFIED -> ACTIVE -> SUPERSEDED | QUARANTINED.
The existing .p2p/state/execution-ledger.jsonl is the only durable local store.
ACTIVE experience is non-authoritative context: it never grants permission,
acceptance, promotion, provider choice, law change, or skill mutation.
Promoted shared experience may be read from the packaged curated catalog, but
retrieval remains read-only and local quarantine/supersession always wins.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

# The installed entrypoint intentionally supports direct-file execution. Give
# that mode a real package context so lazy federation imports behave exactly as
# they do when Control Tower imports this module normally.
if not __package__:
    _runtime_root = Path(__file__).resolve().parents[1]
    if str(_runtime_root) not in sys.path:
        sys.path.insert(0, str(_runtime_root))
    __package__ = "p2p_capabilities"

SCHEMA = "p2p-experience-evolution/1"
LEDGER_SCHEMA = "p2p-execution-event/1"
LEDGER_RELATIVE_PATH = Path(".p2p") / "state" / "execution-ledger.jsonl"
KINDS = ("STRATEGIC", "PROCEDURAL", "TOOL")
USE_OUTCOMES = ("HELPED", "NEUTRAL", "HARMED")
EVENT_CANDIDATE = "EXPERIENCE_CANDIDATE_CREATED"
EVENT_VERIFIED = "EXPERIENCE_VERIFIED"
EVENT_ACTIVATED = "EXPERIENCE_ACTIVATED"
EVENT_QUARANTINED = "EXPERIENCE_QUARANTINED"
EVENT_SUPERSEDED = "EXPERIENCE_SUPERSEDED"
EVENT_USE = "EXPERIENCE_USE_RECORDED"
EXPERIENCE_EVENTS = frozenset({EVENT_CANDIDATE, EVENT_VERIFIED, EVENT_ACTIVATED,
                               EVENT_QUARANTINED, EVENT_SUPERSEDED, EVENT_USE})
NON_PROVING_EVIDENCE_KINDS = frozenset({
    "MODEL_SELF_REPORT", "MODEL_CLAIM", "AGENT_CLAIM",
    "AGENT_VERBAL_ASSERTION", "CHAT_SUMMARY_ONLY", "PRIVATE_CHAIN_OF_THOUGHT",
})
REQUIRED_VERIFICATION_ROLES = ("BEHAVIOR_PROOF", "REGRESSION_PROOF", "CHALLENGE_PROOF")
MAX_TRIGGER_TOKENS = 24
MAX_RESULTS = 5
MAX_TEXT = 4096
_SECRET_RE = re.compile(
    r"(?i)(?:api[_-]?key|password|token|secret|authorization|private[_-]?key)"
    r"\s*[:=]\s*[^\s,;]+|(?:sk|ghp|github_pat|xox[bp])-[A-Za-z0-9_-]{12,}"
)
_TOKEN_RE = re.compile(r"[a-z0-9_.:/+-]{2,64}")


class ExperienceEvolutionError(ValueError):
    """Fail-closed lifecycle contract error."""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _clean(value: object, limit: int = MAX_TEXT) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if _SECRET_RE.search(text):
        raise ExperienceEvolutionError("SECRET_LIKE_VALUE_REJECTED")
    return text[:limit]


def _stable(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _ledger(root: str | Path) -> Path:
    path = Path(root).expanduser().resolve()
    return path if path.suffix.lower() == ".jsonl" else path / LEDGER_RELATIVE_PATH


def _triggers(values: Iterable[object]) -> tuple[str, ...]:
    out: list[str] = []
    for raw in values:
        for token in _TOKEN_RE.findall(_clean(raw, 128).lower()):
            if token not in out:
                out.append(token)
            if len(out) >= MAX_TRIGGER_TOKENS:
                return tuple(out)
    if not out:
        raise ExperienceEvolutionError("TRIGGER_TOKENS_REQUIRED")
    return tuple(out)


def _evidence(items: Iterable[Mapping[str, object]], roles: Sequence[str] = ()) -> tuple[dict[str, str], ...]:
    out: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in items:
        if not isinstance(item, Mapping):
            raise ExperienceEvolutionError("EVIDENCE_ITEM_INVALID")
        kind = _clean(item.get("kind"), 96).upper()
        ref = _clean(item.get("ref"), 1024)
        role = _clean(item.get("role"), 96).upper()
        verdict = _clean(item.get("verdict", "PROVEN"), 32).upper()
        if not kind or not ref:
            raise ExperienceEvolutionError("EVIDENCE_KIND_AND_REF_REQUIRED")
        if kind in NON_PROVING_EVIDENCE_KINDS or verdict not in {"PROVEN", "PASS", "VERIFIED"}:
            continue
        if role:
            seen.add(role)
        out.append({"kind": kind, "ref": ref, "role": role, "verdict": verdict})
    if not out:
        raise ExperienceEvolutionError("INDEPENDENT_EVIDENCE_REQUIRED")
    missing = [role for role in roles if role not in seen]
    if missing:
        raise ExperienceEvolutionError("VERIFICATION_ROLE_MISSING:" + ",".join(missing))
    return tuple(out)


def _event(event_type: str, eid: str, payload: Mapping[str, object], task_id: str = "") -> dict[str, Any]:
    return {
        "schema_version": LEDGER_SCHEMA, "event_type": event_type, "at": utc_now(),
        "task_id": _clean(task_id, 256),
        "experience": {"schema": SCHEMA, "experience_id": eid, **dict(payload)},
    }


def _append(root: str | Path, event: Mapping[str, object]) -> None:
    path = _ledger(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(_stable(dict(event)) + "\n")


def _events(root: str | Path) -> list[dict[str, Any]]:
    path = _ledger(root)
    if not path.is_file():
        return []
    out: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            value = json.loads(line)
        except (json.JSONDecodeError, TypeError):
            continue
        if (isinstance(value, dict) and value.get("schema_version") == LEDGER_SCHEMA
                and value.get("event_type") in EXPERIENCE_EVENTS
                and isinstance(value.get("experience"), Mapping)):
            out.append(value)
    return out


def derive_experiences(root: str | Path) -> dict[str, dict[str, Any]]:
    state: dict[str, dict[str, Any]] = {}
    for event in _events(root):
        exp = dict(event["experience"])
        eid = str(exp.get("experience_id") or "")
        et = event["event_type"]
        if not eid:
            continue
        if et == EVENT_CANDIDATE:
            state[eid] = dict(exp)
            state[eid].update(history=[et], created_at=event.get("at"), last_event_at=event.get("at"))
            continue
        if eid not in state:
            continue
        cur = state[eid]
        cur.setdefault("history", []).append(et)
        cur["last_event_at"] = event.get("at")
        if et == EVENT_VERIFIED:
            cur.update(state="VERIFIED", verification_evidence=exp.get("verification_evidence", []))
        elif et == EVENT_ACTIVATED:
            cur.update(state="ACTIVE", activated_at=event.get("at"))
        elif et == EVENT_QUARANTINED:
            cur.update(state="QUARANTINED", quarantine_reason=exp.get("reason", ""),
                       quarantine_evidence=exp.get("evidence", []))
        elif et == EVENT_SUPERSEDED:
            cur.update(state="SUPERSEDED", superseded_by=exp.get("superseded_by", ""),
                       supersede_evidence=exp.get("evidence", []))
        elif et == EVENT_USE:
            cur.setdefault("use_history", []).append({
                "outcome": exp.get("use_outcome"), "task_id": event.get("task_id"),
                "evidence_ref": exp.get("evidence_ref"), "at": event.get("at"),
            })
    return state


def create_candidate(root: str | Path, *, task_id: str, kind: str,
                     trigger_tokens: Iterable[object], lesson: str,
                     evidence: Iterable[Mapping[str, object]], outcome: str,
                     failure_class: str = "", correction: str = "",
                     source_revision: str = "") -> dict[str, Any]:
    kind = _clean(kind, 32).upper()
    task_id = _clean(task_id, 256)
    if kind not in KINDS:
        raise ExperienceEvolutionError("EXPERIENCE_KIND_INVALID")
    if not task_id:
        raise ExperienceEvolutionError("TASK_ID_REQUIRED")
    trigger_tokens = _triggers(trigger_tokens)
    lesson = _clean(lesson)
    if len(lesson) < 12:
        raise ExperienceEvolutionError("LESSON_TOO_VAGUE")
    proof = _evidence(evidence)
    outcome = _clean(outcome, 128).upper()
    if not outcome:
        raise ExperienceEvolutionError("OUTCOME_REQUIRED")
    eid = "exp-" + hashlib.sha256(_stable({
        "kind": kind, "trigger_tokens": trigger_tokens, "lesson": lesson,
    }).encode("utf-8")).hexdigest()[:24]
    current = derive_experiences(root).get(eid)
    if current and current.get("state") not in {"SUPERSEDED", "QUARANTINED"}:
        return {"status": "EXISTS", **current}
    record = {
        "kind": kind, "state": "CANDIDATE", "trigger_tokens": list(trigger_tokens),
        "lesson": lesson, "outcome": outcome, "failure_class": _clean(failure_class, 256),
        "correction": _clean(correction), "source_task_id": task_id,
        "source_revision": _clean(source_revision, 256), "evidence": list(proof),
        "authority": "NON_AUTHORITATIVE_VERIFIED_EXPERIENCE",
        "permission_effect": "NONE", "acceptance_authority": False,
    }
    _append(root, _event(EVENT_CANDIDATE, eid, record, task_id))
    return {"status": "CREATED", "experience_id": eid, **record}


def verify_candidate(root: str | Path, experience_id: str, *, task_id: str,
                     verification_evidence: Iterable[Mapping[str, object]]) -> dict[str, Any]:
    eid = _clean(experience_id, 128)
    current = derive_experiences(root).get(eid)
    if not current:
        raise ExperienceEvolutionError("EXPERIENCE_NOT_FOUND")
    if current.get("state") != "CANDIDATE":
        raise ExperienceEvolutionError("VERIFY_REQUIRES_CANDIDATE")
    proof = _evidence(verification_evidence, REQUIRED_VERIFICATION_ROLES)
    payload = {"state": "VERIFIED", "verification_evidence": list(proof),
               "authority": "NON_AUTHORITATIVE_VERIFIED_EXPERIENCE",
               "permission_effect": "NONE", "acceptance_authority": False}
    _append(root, _event(EVENT_VERIFIED, eid, payload, task_id))
    return {"status": "VERIFIED", "experience_id": eid, **payload}


def activate_verified(root: str | Path, experience_id: str, *, task_id: str = "") -> dict[str, Any]:
    eid = _clean(experience_id, 128)
    current = derive_experiences(root).get(eid)
    if not current:
        raise ExperienceEvolutionError("EXPERIENCE_NOT_FOUND")
    if current.get("state") != "VERIFIED":
        raise ExperienceEvolutionError("ACTIVATE_REQUIRES_VERIFIED")
    payload = {"state": "ACTIVE", "authority": "NON_AUTHORITATIVE_VERIFIED_EXPERIENCE",
               "permission_effect": "NONE", "acceptance_authority": False,
               "may_modify_law_or_skill": False}
    _append(root, _event(EVENT_ACTIVATED, eid, payload, task_id))
    return {"status": "ACTIVE", "experience_id": eid, **payload}


def quarantine_experience(root: str | Path, experience_id: str, *, reason: str,
                          evidence: Iterable[Mapping[str, object]], task_id: str = "") -> dict[str, Any]:
    eid = _clean(experience_id, 128)
    current = derive_experiences(root).get(eid)
    if not current:
        raise ExperienceEvolutionError("EXPERIENCE_NOT_FOUND")
    if current.get("state") not in {"CANDIDATE", "VERIFIED", "ACTIVE"}:
        raise ExperienceEvolutionError("QUARANTINE_STATE_INVALID")
    reason = _clean(reason)
    if len(reason) < 8:
        raise ExperienceEvolutionError("QUARANTINE_REASON_TOO_VAGUE")
    payload = {"state": "QUARANTINED", "reason": reason, "evidence": list(_evidence(evidence)),
               "authority": "NON_AUTHORITATIVE_VERIFIED_EXPERIENCE"}
    _append(root, _event(EVENT_QUARANTINED, eid, payload, task_id))
    return {"status": "QUARANTINED", "experience_id": eid, **payload}


def supersede_experience(root: str | Path, old_experience_id: str, new_experience_id: str,
                         *, evidence: Iterable[Mapping[str, object]], task_id: str = "") -> dict[str, Any]:
    states = derive_experiences(root)
    old_id, new_id = _clean(old_experience_id, 128), _clean(new_experience_id, 128)
    if old_id not in states or new_id not in states:
        raise ExperienceEvolutionError("EXPERIENCE_NOT_FOUND")
    if states[old_id].get("state") != "ACTIVE" or states[new_id].get("state") != "ACTIVE":
        raise ExperienceEvolutionError("SUPERSEDE_REQUIRES_ACTIVE_PAIR")
    payload = {"state": "SUPERSEDED", "superseded_by": new_id,
               "evidence": list(_evidence(evidence)),
               "authority": "NON_AUTHORITATIVE_VERIFIED_EXPERIENCE"}
    _append(root, _event(EVENT_SUPERSEDED, old_id, payload, task_id))
    return {"status": "SUPERSEDED", "experience_id": old_id, "superseded_by": new_id}


def _task_tokens(task: Mapping[str, object] | str) -> set[str]:
    if isinstance(task, Mapping):
        text = " ".join(str(v) for v in (
            task.get("task_id", ""), task.get("title", ""), task.get("purpose", ""),
            " ".join(str(x) for x in (task.get("scope", ()) or ())),
            " ".join(str(x) for x in (task.get("tags", ()) or ())),
        ))
    else:
        text = str(task)
    return set(_TOKEN_RE.findall(text.lower()))


def retrieve_active_experiences(root: str | Path, task: Mapping[str, object] | str,
                                *, max_results: int = 3) -> tuple[dict[str, Any], ...]:
    limit = max(0, min(int(max_results), MAX_RESULTS))
    tokens = _task_tokens(task)
    ranked: list[tuple[int, str, dict[str, Any]]] = []
    for eid, exp in derive_experiences(root).items():
        if exp.get("state") != "ACTIVE":
            continue
        matched = tokens.intersection(str(x).lower() for x in exp.get("trigger_tokens", ()))
        if matched:
            ranked.append((len(matched), eid, exp))
    ranked.sort(key=lambda item: (-item[0], item[1]))
    out: list[dict[str, Any]] = []
    for score, eid, exp in ranked[:limit]:
        triggers = set(str(x).lower() for x in exp.get("trigger_tokens", ()))
        out.append({
            "schema": SCHEMA, "experience_id": eid, "kind": exp.get("kind"), "state": "ACTIVE",
            "match_score": score, "matched_triggers": sorted(tokens.intersection(triggers)),
            "lesson": exp.get("lesson"), "correction": exp.get("correction"),
            "failure_class": exp.get("failure_class"), "source_task_id": exp.get("source_task_id"),
            "source_revision": exp.get("source_revision"),
            "source": "PROJECT_LOCAL_LEDGER",
            "authority": "NON_AUTHORITATIVE_VERIFIED_EXPERIENCE",
            "permission_effect": "NONE", "acceptance_authority": False,
            "must_revalidate_against_current_state": True,
        })
    return tuple(out)


def _retrieve_promoted_shared_experiences(
    root: str | Path,
    task: Mapping[str, object] | str,
    *,
    max_results: int = 3,
) -> tuple[tuple[dict[str, Any], ...], str]:
    """Read matching promoted shared experience without mutating project state."""

    catalog = None
    try:
        from p2p_capabilities import experience_federation as federation
        catalog = federation.load_catalog()
    except Exception:
        try:
            from . import experience_federation as federation
            catalog = federation.load_catalog()
        except Exception:
            catalog = None

    if catalog is None or not catalog.get("records"):
        portable_capsule_path = Path(root) / ".p2p" / "portable" / "P2P-EXPERIENCE-CAPSULE.json"
        if portable_capsule_path.is_file() and not portable_capsule_path.is_symlink():
            res = retrieve_portable_experience(root, task, max_results=max_results)
            if res.get("decision") == "USE_ACTIVE_EXPERIENCE":
                return tuple(res.get("experiences") or ()), "USE_ACTIVE_EXPERIENCE"
            return (), res.get("decision", "UNAVAILABLE")

    if not catalog or not isinstance(catalog, Mapping):
        return (), "UNAVAILABLE"

    limit = max(0, min(int(max_results), MAX_RESULTS))
    tokens = _task_tokens(task)
    local = derive_experiences(root)
    ranked: list[tuple[int, str, Mapping[str, object]]] = []
    for record in catalog.get("records") or ():
        if not isinstance(record, Mapping) or record.get("state") != "ACTIVE":
            continue
        scope = str(record.get("scope") or "").upper()
        if scope == "DOMAIN":
            domain = str(record.get("domain") or "").lower()
            if not domain or domain not in tokens:
                continue
        elif scope != "CROSS_PROJECT":
            continue
        source_eid = str(record.get("source_experience_id") or "")
        local_state = local.get(source_eid, {}).get("state") if source_eid else None
        if local_state in {"ACTIVE", "QUARANTINED", "SUPERSEDED"}:
            continue
        triggers = {str(x).lower() for x in (record.get("trigger_tokens") or ())}
        matched = tokens.intersection(triggers)
        if matched:
            ranked.append((len(matched), str(record.get("record_id") or source_eid), record))
    ranked.sort(key=lambda item: (-item[0], item[1]))

    out: list[dict[str, Any]] = []
    for score, record_id, record in ranked[:limit]:
        triggers = {str(x).lower() for x in (record.get("trigger_tokens") or ())}
        out.append({
            "schema": SCHEMA,
            "experience_id": str(record.get("source_experience_id") or record_id),
            "shared_record_id": record_id,
            "kind": record.get("kind"),
            "state": "ACTIVE",
            "scope": record.get("scope"),
            "domain": record.get("domain"),
            "match_score": score,
            "matched_triggers": sorted(tokens.intersection(triggers)),
            "lesson": record.get("lesson"),
            "correction": record.get("correction"),
            "failure_class": record.get("failure_class"),
            "source_task_id": record.get("source_task_id"),
            "source_revision": record.get("source_revision"),
            "source": "P2P_SHARED_PROMOTED_CATALOG",
            "authority": "NON_AUTHORITATIVE_VERIFIED_EXPERIENCE",
            "permission_effect": "NONE",
            "acceptance_authority": False,
            "must_revalidate_against_current_state": True,
        })
    return tuple(out), "AVAILABLE"


def record_use_result(root: str | Path, experience_id: str, *, task_id: str,
                      outcome: str, evidence_ref: str) -> dict[str, Any]:
    eid = _clean(experience_id, 128)
    current = derive_experiences(root).get(eid)
    if not current or current.get("state") != "ACTIVE":
        raise ExperienceEvolutionError("USE_REQUIRES_ACTIVE_EXPERIENCE")
    outcome = _clean(outcome, 32).upper()
    if outcome not in USE_OUTCOMES:
        raise ExperienceEvolutionError("USE_OUTCOME_INVALID")
    ref = _clean(evidence_ref, 1024)
    if not ref:
        raise ExperienceEvolutionError("USE_EVIDENCE_REQUIRED")
    _append(root, _event(EVENT_USE, eid, {"state": "ACTIVE", "use_outcome": outcome,
             "evidence_ref": ref, "authority": "NON_AUTHORITATIVE_VERIFIED_EXPERIENCE"}, task_id))
    return {"status": "RECORDED", "experience_id": eid, "use_outcome": outcome,
            "review_recommended": outcome == "HARMED", "auto_quarantined": False}


def retrieve_portable_experience(
    project_root: str | Path,
    task: Mapping[str, object] | str,
    *,
    max_results: int = 3,
) -> dict[str, Any]:
    """Standalone read-only retrieval from .p2p/portable/P2P-EXPERIENCE-CAPSULE.json."""

    def _fail_closed(reason: str = "UNAVAILABLE") -> dict[str, Any]:
        return {
            "schema": "p2p-portable-experience-capsule/1",
            "decision": "UNAVAILABLE",
            "reason": reason,
            "experiences": [],
            "authority": "NON_AUTHORITATIVE_VERIFIED_EXPERIENCE",
            "current_state_wins": True,
            "law_and_task_contract_win": True,
            "permission_effect": "NONE",
            "acceptance_authority": False,
        }

    root_path = Path(project_root).resolve()
    capsule_path = root_path / ".p2p" / "portable" / "P2P-EXPERIENCE-CAPSULE.json"
    if not capsule_path.is_file() or capsule_path.is_symlink():
        return _fail_closed("CAPSULE_MISSING_OR_INVALID_PATH")

    try:
        capsule_bytes = capsule_path.read_bytes()
        capsule_sha = hashlib.sha256(capsule_bytes).hexdigest()
        data = json.loads(capsule_bytes.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return _fail_closed(f"CAPSULE_UNREADABLE_OR_JSON_INVALID:{exc}")

    # Transport integrity: check bound hash in portable notebook or AGENTS if present
    portable_notebook = root_path / ".p2p" / "portable" / "P2P-OPERATIONS-NOTEBOOK.md"
    if portable_notebook.is_file() and not portable_notebook.is_symlink():
        try:
            head_text = portable_notebook.read_text(encoding="utf-8")[:1500]
            match = re.search(r"(?m)^PORTABLE_EXPERIENCE_CONTENT_SHA256=([0-9a-fA-F]{64})$", head_text)
            if match and match.group(1).lower() != capsule_sha:
                return _fail_closed("PORTABLE_EXPERIENCE_TRANSPORT_HASH_MISMATCH")
        except (OSError, UnicodeError):
            pass

    agents_file = root_path / "AGENTS.md"
    if agents_file.is_file() and not agents_file.is_symlink():
        try:
            agents_text = agents_file.read_text(encoding="utf-8")
            match = re.search(r"PORTABLE_EXPERIENCE_SHA256`?:\s*`?([0-9a-fA-F]{64})`?", agents_text)
            if match and match.group(1).lower() != capsule_sha:
                return _fail_closed("PORTABLE_EXPERIENCE_TRANSPORT_HASH_MISMATCH")
        except (OSError, UnicodeError):
            pass

    # Exact capsule schema and metadata invariants
    if data.get("schema") != "p2p-portable-experience-capsule/1":
        return _fail_closed("CAPSULE_SCHEMA_INVALID")
    if data.get("generated") is not True:
        return _fail_closed("CAPSULE_GENERATED_MARKER_INVALID")
    if data.get("canonical_source") not in (
        "7roger89-web/P2P-upgrade-github-1@main:.p2p/system/p2p_capabilities/shared_experience_catalog.json",
        "p2p_capabilities.shared_experience_catalog",
    ):
        return _fail_closed("CAPSULE_CANONICAL_SOURCE_INVALID")
    source_sha = str(data.get("source_content_sha256") or "")
    if not re.fullmatch(r"^[0-9a-fA-F]{64}$", source_sha):
        return _fail_closed("CAPSULE_SOURCE_SHA256_INVALID")
    if data.get("authority") != "NON_AUTHORITATIVE_VERIFIED_EXPERIENCE":
        return _fail_closed("CAPSULE_AUTHORITY_INVALID")
    if data.get("permission_effect") != "NONE":
        return _fail_closed("CAPSULE_PERMISSION_EFFECT_INVALID")
    if data.get("acceptance_authority") is not False:
        return _fail_closed("CAPSULE_ACCEPTANCE_AUTHORITY_INVALID")
    if data.get("current_state_wins") is not True or data.get("law_and_task_contract_win") is not True:
        return _fail_closed("CAPSULE_PRECEDENCE_INVALID")

    records = data.get("records")
    if not isinstance(records, (list, tuple)):
        return _fail_closed("CAPSULE_RECORDS_INVALID")

    # Record authority and scope invariants (fail-closed on any unauthorized or corrupted record)
    for rec in records:
        if not isinstance(rec, Mapping):
            return _fail_closed("CAPSULE_RECORD_NOT_MAPPING")
        if rec.get("state") != "ACTIVE":
            return _fail_closed("CAPSULE_RECORD_NOT_ACTIVE")
        scope = str(rec.get("scope") or "").upper()
        if scope not in ("DOMAIN", "CROSS_PROJECT"):
            return _fail_closed("CAPSULE_RECORD_SCOPE_INVALID")
        if rec.get("authority") != "NON_AUTHORITATIVE_VERIFIED_EXPERIENCE":
            return _fail_closed("CAPSULE_RECORD_AUTHORITY_INVALID")
        if rec.get("permission_effect") != "NONE":
            return _fail_closed("CAPSULE_RECORD_PERMISSION_EFFECT_INVALID")
        if rec.get("acceptance_authority") is not False:
            return _fail_closed("CAPSULE_RECORD_ACCEPTANCE_AUTHORITY_INVALID")
        if not rec.get("lesson") or not rec.get("trigger_tokens"):
            return _fail_closed("CAPSULE_RECORD_CONTENT_INCOMPLETE")

    limit = max(0, min(int(max_results), MAX_RESULTS))
    tokens = _task_tokens(task)
    ranked: list[tuple[int, str, Mapping[str, object]]] = []
    for record in records:
        scope = str(record.get("scope") or "").upper()
        if scope == "DOMAIN":
            domain = str(record.get("domain") or "").lower()
            if not domain or domain not in tokens:
                continue
        triggers = {str(x).lower() for x in (record.get("trigger_tokens") or ())}
        matched = tokens.intersection(triggers)
        if matched:
            record_id = str(record.get("record_id") or record.get("source_experience_id") or "")
            ranked.append((len(matched), record_id, record))

    ranked.sort(key=lambda item: (-item[0], item[1]))
    matches: list[dict[str, Any]] = []
    for score, rec_id, rec in ranked[:limit]:
        triggers = {str(x).lower() for x in (rec.get("trigger_tokens") or ())}
        matches.append({
            "experience_id": str(rec.get("source_experience_id") or rec_id),
            "record_id": rec_id,
            "kind": rec.get("kind"),
            "state": "ACTIVE",
            "scope": rec.get("scope"),
            "domain": rec.get("domain"),
            "match_score": score,
            "matched_triggers": sorted(tokens.intersection(triggers)),
            "lesson": rec.get("lesson"),
            "correction": rec.get("correction"),
            "failure_class": rec.get("failure_class"),
            "source": ".p2p/portable/P2P-EXPERIENCE-CAPSULE.json",
            "authority": "NON_AUTHORITATIVE_VERIFIED_EXPERIENCE",
            "permission_effect": "NONE",
            "acceptance_authority": False,
        })

    return {
        "schema": "p2p-portable-experience-capsule/1",
        "decision": "USE_ACTIVE_EXPERIENCE" if matches else "NO_MATCH",
        "experiences": matches,
        "authority": "NON_AUTHORITATIVE_VERIFIED_EXPERIENCE",
        "current_state_wins": True,
        "law_and_task_contract_win": True,
        "permission_effect": "NONE",
        "acceptance_authority": False,
    }


def activation_summary(root: str | Path, task: Mapping[str, object] | str,
                       *, max_results: int = 3) -> dict[str, Any]:
    limit = max(0, min(int(max_results), MAX_RESULTS))
    local_matches = list(retrieve_active_experiences(root, task, max_results=limit))
    remaining = max(0, limit - len(local_matches))
    shared_matches: list[dict[str, Any]] = []
    shared_status = "AVAILABLE"
    if remaining:
        shared, shared_status = _retrieve_promoted_shared_experiences(
            root, task, max_results=remaining
        )
        shared_matches = list(shared)
    matches = local_matches + shared_matches
    return {
        "schema": SCHEMA,
        "decision": "USE_ACTIVE_EXPERIENCE" if matches else "NO_MATCH",
        "experiences": matches,
        "authority": "NON_AUTHORITATIVE_VERIFIED_EXPERIENCE",
        "current_state_wins": True,
        "law_and_task_contract_win": True,
        "permission_effect": "NONE",
        "acceptance_authority": False,
        "mutated": False,
        "local_match_count": len(local_matches),
        "shared_match_count": len(shared_matches),
        "shared_catalog_status": shared_status,
    }


def _json(value: str) -> Any:
    try:
        return json.loads(value)
    except json.JSONDecodeError as exc:
        raise ExperienceEvolutionError("JSON_ARGUMENT_INVALID") from exc


def _evidence_json(value: str) -> tuple[Mapping[str, object], ...]:
    parsed = _json(value)
    if not isinstance(parsed, list) or not all(isinstance(x, Mapping) for x in parsed):
        raise ExperienceEvolutionError("EVIDENCE_JSON_ARRAY_REQUIRED")
    return tuple(parsed)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("retrieve")
    p.add_argument("--task-text", default="")
    p.add_argument("--task-json", default="")
    p.add_argument("--max-results", type=int, default=3)
    p.add_argument("--portable", action="store_true", default=False)
    p = sub.add_parser("status"); p.add_argument("--experience-id", default="")
    p = sub.add_parser("candidate"); p.add_argument("--task-id", required=True); p.add_argument("--kind", choices=KINDS, required=True); p.add_argument("--trigger", action="append", required=True); p.add_argument("--lesson", required=True); p.add_argument("--evidence-json", required=True); p.add_argument("--outcome", required=True); p.add_argument("--failure-class", default=""); p.add_argument("--correction", default=""); p.add_argument("--source-revision", default="")
    p = sub.add_parser("verify"); p.add_argument("--experience-id", required=True); p.add_argument("--task-id", required=True); p.add_argument("--evidence-json", required=True)
    p = sub.add_parser("activate"); p.add_argument("--experience-id", required=True); p.add_argument("--task-id", default="")
    p = sub.add_parser("use"); p.add_argument("--experience-id", required=True); p.add_argument("--task-id", required=True); p.add_argument("--outcome", choices=USE_OUTCOMES, required=True); p.add_argument("--evidence-ref", required=True)
    p = sub.add_parser("quarantine"); p.add_argument("--experience-id", required=True); p.add_argument("--task-id", default=""); p.add_argument("--reason", required=True); p.add_argument("--evidence-json", required=True)
    p = sub.add_parser("supersede"); p.add_argument("--old-experience-id", required=True); p.add_argument("--new-experience-id", required=True); p.add_argument("--task-id", default=""); p.add_argument("--evidence-json", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "retrieve":
            task: Mapping[str, object] | str = args.task_text
            if args.task_json:
                task = _json(args.task_json)
                if not isinstance(task, Mapping):
                    raise ExperienceEvolutionError("TASK_JSON_OBJECT_REQUIRED")
            if getattr(args, "portable", False):
                value = retrieve_portable_experience(args.root, task, max_results=args.max_results)
            else:
                value = activation_summary(args.root, task, max_results=args.max_results)
        elif args.command == "status":
            states = derive_experiences(args.root); value = states.get(args.experience_id, {}) if args.experience_id else {"schema": SCHEMA, "experiences": states}
        elif args.command == "candidate":
            value = create_candidate(args.root, task_id=args.task_id, kind=args.kind, trigger_tokens=args.trigger, lesson=args.lesson, evidence=_evidence_json(args.evidence_json), outcome=args.outcome, failure_class=args.failure_class, correction=args.correction, source_revision=args.source_revision)
        elif args.command == "verify":
            value = verify_candidate(args.root, args.experience_id, task_id=args.task_id, verification_evidence=_evidence_json(args.evidence_json))
        elif args.command == "activate":
            value = activate_verified(args.root, args.experience_id, task_id=args.task_id)
        elif args.command == "use":
            value = record_use_result(args.root, args.experience_id, task_id=args.task_id, outcome=args.outcome, evidence_ref=args.evidence_ref)
        elif args.command == "quarantine":
            value = quarantine_experience(args.root, args.experience_id, reason=args.reason, evidence=_evidence_json(args.evidence_json), task_id=args.task_id)
        else:
            value = supersede_experience(args.root, args.old_experience_id, args.new_experience_id, evidence=_evidence_json(args.evidence_json), task_id=args.task_id)
        print(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)); return 0
    except (OSError, ExperienceEvolutionError) as exc:
        print(json.dumps({"schema": SCHEMA, "status": "BLOCKED", "error": str(exc)}, ensure_ascii=False, sort_keys=True)); return 2


if __name__ == "__main__":
    raise SystemExit(main())
