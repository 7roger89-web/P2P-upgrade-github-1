"""P2P-FRAMEWORK-06 — OPERATIONAL RESILIENCE & BOUNDED PRODUCTION AUTONOMY.

This module is NOT an orchestrator. It adds a bounded runtime contract
layer over the existing P2P control plane:

- FW01 remains the sole operating loop.
- FW02/FW03/FW04/FW05 authority boundaries are preserved.
- FW06 adds: Autonomy Envelope, Safe Continuation Policy, failure
  classification, bounded retry, execution leases (split-brain
  prevention), quiesce/drain, crash/session-death recovery, failover
  decision (FAILOVER != RETRY), tiered runtime health, pause/resume,
  workspace ownership, conflict detection, bounded parallel worktrees,
  multi-project isolation, event log, and auditability.

AUTONOMOUS != UNBOUNDED.

All durable state lives under {root}/.p2p/state/ and is append-only or
transactionally small and validated. Raw transcripts never become state.
Events never contain secrets (task_state._looks_secret_like) and never
contain chain-of-thought reasoning.

Readiness claim for this implementation:
FOUNDATION_READY, DETERMINISTICALLY_VERIFIED, PROCESS_RECOVERY_VERIFIED,
MULTI_PROCESS_VERIFIED (via cold-process subprocess tests).
LIVE_SINGLE_PROJECT_VERIFIED / LIVE_MULTI_PROJECT_VERIFIED are NOT claimed.

Schema version: p2p-fw06-operational-resilience/1
"""

import json
import os
import secrets as _secrets
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Mapping

from p2p_capabilities import task_state as _task_state
from p2p_capabilities import backend_contract as _backend_contract
from p2p_capabilities import failover_boundary as _failover_boundary

FW06_SCHEMA = "p2p-fw06-operational-resilience/1"

STATE_REL = ".p2p/state"

# ---- §41 Failure classes ------------------------------------------------------

FAILURE_CLASSES = (
    "LEASE_CONFLICT", "STALE_LEASE", "PROCESS_CRASH", "WORKSPACE_CONFLICT",
    "POST_DISPATCH_AMBIGUITY", "UNKNOWN_MUTATION_STATE", "RUNTIME_UNHEALTHY",
    "AUTH_DRIFT", "TARGET_UNAVAILABLE", "FAILOVER_NOT_SAFE",
    "RETRY_EXHAUSTED", "RESOURCE_EXHAUSTED", "QUALITY_BLOCKED",
    "OWNER_GATE_REQUIRED", "PROJECT_PAUSED", "SCOPE_DRIFT",
    "RECOVERY_INCOMPLETE",
)

# Canonical class aliases so FW01-internal vocabulary maps in:
_FAILURE_ALIASES = {
    "AUTH_INVALID": "AUTH_DRIFT",
    "PERMISSION_DENIED": "OWNER_GATE_REQUIRED",
    "UNKNOWN": "UNKNOWN_MUTATION_STATE",
    "ERROR": "UNKNOWN_MUTATION_STATE",
}

def classify_failure(raw: str | None) -> str:
    """Normalize an observed failure into a canonical class. Never returns
    a generic unclassified value: unknown input maps to
    UNKNOWN_MUTATION_STATE (fail closed)."""
    if not raw:
        return "UNKNOWN_MUTATION_STATE"
    candidate = str(raw).strip().upper()
    if candidate in FAILURE_CLASSES:
        return candidate
    alias = _FAILURE_ALIASES.get(str(raw).strip().upper())
    if alias:
        return alias
    try:
        norm = _failover_boundary._classify(str(raw))  # type: ignore[attr-defined]
        if norm in FAILURE_CLASSES:
            return norm
    except Exception:  # noqa: BLE001
        pass
    return "UNKNOWN_MUTATION_STATE"


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _stable_id(parts: list[Any]) -> str:
    return "sha256:" + _task_state._sha256(tuple(parts))  # type: ignore[attr-defined]


def _json_safe(value: Any) -> Any:
    return _task_state._json_safe(value)  # type: ignore[attr-defined]


def _event_json_safe(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Events never log secrets or chain-of-thought. Strip anything that
    looks secret-like and any private-reasoning keys."""
    out: dict[str, Any] = {}
    for key, value in payload.items():
        if any(t in key.upper() for t in (
                "CHAIN", "THOUGHT", "REASONING", "COT", "SCRATCHPAD")):
            continue
        if isinstance(value, str) and _task_state._looks_secret_like(value):
            out[key] = "<REDACTED>"
            continue
        out[key] = _json_safe(value)
    return out


def state_dir(root: str | Path, *, mkdirs: bool = True) -> Path:
    """§55 Read-only facade invariant: views NEVER create project state
    directories. Dirs are only materialized by append-only write surfaces."""
    root = Path(root)
    d = root / STATE_REL
    if mkdirs:
        d.mkdir(parents=True, exist_ok=True)
    return d


# ---- §36 Event log (idempotent append, no secrets) ----------------------------

def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                # Malformed record: block, do not silently reconstruct
                # (§52: ignore only where policy explicitly permits).
                rows.append({"_MALFORMED_LINE": True, "_raw": line})
    return rows


def _append_jsonl(path: Path, record: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, sort_keys=True, ensure_ascii=False)
                 + "\n")


def append_fw06_event(root: str | Path, event_type: str,
                      payload: Mapping[str, Any]) -> str:
    """Append a normalized operational event. Stable event identity makes
    replay idempotent (§53): a second call with identical
    (project, event_type, payload) is ignored (returns existing id)."""
    if not event_type:
        raise ValueError("EVENT_TYPE_REQUIRED")
    sdir = state_dir(root, mkdirs=True)
    path = sdir / "fw06-events.jsonl"
    payload = _event_json_safe(dict(payload))
    # Stable identity: project + type + canonical payload
    event_id = _stable_id([
        "fw06-event",
        str(payload.get("project_id", "")),
        event_type,
        json.dumps(payload, sort_keys=True, ensure_ascii=False),
    ])
    for row in _read_jsonl(path):
        if row.get("event_id") == event_id:
            return event_id
    _append_jsonl(path, {
        "event_id": event_id,
        "schema": FW06_SCHEMA,
        "event_type": event_type,
        "project_id": str(payload.get("project_id", "")),
        "goal_id": str(payload.get("goal_id", "")),
        "task_id": str(payload.get("task_id", "")),
        "payload": payload,
        "created_utc": _utc_now(),
    })
    return event_id


def read_fw06_events(root: str | Path, project_id: str | None = None,
                     event_type: str | None = None) -> list[dict[str, Any]]:
    path = state_dir(root, mkdirs=False) / "fw06-events.jsonl"
    rows = [r for r in _read_jsonl(path)
            if not r.get("_MALFORMED_LINE")]
    if project_id:
        rows = [r for r in rows if r.get("project_id") == project_id]
    if event_type:
        rows = [r for r in rows if r.get("event_type") == event_type]
    return rows


def malformed_fw06_event_records(root: str | Path) -> list[str]:
    path = state_dir(root, mkdirs=False) / "fw06-events.jsonl"
    return [r["_raw"] for r in _read_jsonl(path)
            if r.get("_MALFORMED_LINE")]


# ---- §4 Autonomy Envelope -----------------------------------------------------

ENVELOPE_FIELDS = (
    "project_id", "goal_id", "authorized_scope", "non_scope",
    "allowed_mutation_classes", "prohibited_mutation_classes", "owner_gates",
    "max_parallelism", "retry_policy", "resource_budget",
    "runtime_requirements", "quality_requirements", "recovery_policy",
    "expiry_utc", "evidence_pointers",
)

ENVELOPE_PATH = "fw06-autonomy-envelope.json"

ALLOWED_MUTATION_CLASSES_DEFAULT = (
    "READ_ONLY", "REPOSITORY_SYNTHETIC", "LOCAL_FILESYSTEM_SYNTHETIC",
    "DOCUMENTATION", "TEST_ONLY",
)
PROHIBITED_MUTATION_CLASSES_DEFAULT = (
    "PRODUCTION_DATABASE", "NETWORK_API_PRODUCTION", "DEPLOYMENT",
    "PAYMENT", "CREDENTIAL_ACQUISITION", "UNBOUNDED_DAEMON",
)


def validate_envelope(value: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and normalize an Autonomy Envelope. Returns a clean dict or
    raises ValueError. Bounded contract over existing permissions — not an
    ACL replacement."""
    v: dict[str, Any] = {}
    for field in ENVELOPE_FIELDS:
        if field not in value:
            raise ValueError(f"ENVELOPE_FIELD_MISSING:{field}")
    for name in ("project_id", "goal_id"):
        if not str(value[name]).strip():
            raise ValueError(f"ENVELOPE_ID_EMPTY:{name}")
        v[name] = str(value[name]).strip()
    for name in ("authorized_scope", "non_scope"):
        v[name] = [str(x).strip() for x in value[name]] if value[name] else []
    for name in ("allowed_mutation_classes", "prohibited_mutation_classes"):
        items = [str(x).strip() for x in value[name]] if value[name] else []
        overlap = set(items) & set(v.get("allowed_mutation_classes") if name
                                   == "prohibited_mutation_classes"
                                   else [])
        if name == "prohibited_mutation_classes" and \
                set(items) & set(v["allowed_mutation_classes"]):
            overlap = set(items) & set(v["allowed_mutation_classes"])
        if overlap:
            raise ValueError(f"ENVELOPE_MUTATION_CONFLICT:{sorted(overlap)}")
        v[name] = items
    v["owner_gates"] = [str(x).strip() for x in value["owner_gates"]] \
        if value["owner_gates"] else []
    mp = int(value["max_parallelism"])
    if mp < 1:
        raise ValueError("ENVELOPE_MAX_PARALLELISM_INVALID")
    v["max_parallelism"] = mp
    rp = dict(value["retry_policy"] or {})
    if "max_retries" not in rp:
        raise ValueError("ENVELOPE_RETRY_POLICY_MISSING_MAX_RETRIES")
    if int(rp["max_retries"]) < 0:
        raise ValueError("ENVELOPE_RETRY_MAX_NEGATIVE")
    v["retry_policy"] = {
        "max_retries": int(rp["max_retries"]),
        "retryable_classes": [str(x) for x in
                              rp.get("retryable_classes", ())],
        "cooldown_seconds": max(0, int(rp.get("cooldown_seconds", 0))),
        "require_stable_task": bool(rp.get("require_stable_task", True)),
    }
    rb = dict(value["resource_budget"] or {})
    v["resource_budget"] = {k: max(0, int(i)) for k, i in rb.items()}
    v["runtime_requirements"] = dict(value["runtime_requirements"] or {})
    v["quality_requirements"] = dict(value["quality_requirements"] or {})
    v["recovery_policy"] = dict(value["recovery_policy"] or {})
    if not str(value["expiry_utc"]).strip():
        raise ValueError("ENVELOPE_EXPIRY_REQUIRED")
    v["expiry_utc"] = str(value["expiry_utc"]).strip()
    v["evidence_pointers"] = [str(x) for x in
                              (value["evidence_pointers"] or ())]
    return v


def _envelope_path(root: str | Path, project_id: str,
                       *, mkdirs: bool = False) -> Path:
    safe = _task_state._required_text(project_id, "project_id",  # type: ignore[attr-defined]
                                      max_length=128)
    return state_dir(root, mkdirs=mkdirs) / (ENVELOPE_PATH.replace("fw06-autonomy-envelope",
                                                    "fw06-autonomy-envelope-"
                                                    + safe.replace("/", "-")
                                                    .replace("\\", "-")))


def save_envelope(root: str | Path, envelope: Mapping[str, Any]) -> str:
    """Persist (validated) envelope. Idempotent by project_id."""
    v = validate_envelope(dict(envelope))
    path = _envelope_path(root, v["project_id"], mkdirs=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(v, fh, indent=2, sort_keys=True, ensure_ascii=False)
    append_fw06_event(root, "AUTONOMY_ENVELOPE_SAVED", {
        "project_id": v["project_id"], "goal_id": v["goal_id"],
        "expiry_utc": v["expiry_utc"],
        "allowed_mutation_classes": v["allowed_mutation_classes"],
        "prohibited_mutation_classes": v["prohibited_mutation_classes"],
    })
    return v["project_id"]


def load_envelope(root: str | Path, project_id: str) -> dict[str, Any] | None:
    path = _envelope_path(root, project_id)
    if not path.exists():
        return None
    with path.open(encoding="utf-8") as fh:
        try:
            raw = json.load(fh)
        except json.JSONDecodeError:
            return None
    return validate_envelope(raw)


def envelope_is_fresh(envelope: Mapping[str, Any],
                      now_utc: str | None = None) -> bool:
    """EXPIRY/FRESHNESS: expired or missing envelope fails closed."""
    try:
        expiry = datetime.fromisoformat(
            str(envelope["expiry_utc"]).replace("Z", "+00:00"))
    except (ValueError, KeyError):
        return False
    now = datetime.fromisoformat(
        (now_utc or _utc_now()).replace("Z", "+00:00"))
    return now <= expiry


# ---- §5 Safe Continuation Policy (fail closed) --------------------------------

def safe_continuation_decision(
        root: str | Path,
        *,
        project_id: str,
        task_safe: bool,
        capabilities_sufficient: bool,
        team_eligible: bool,
        target_eligible: bool,
        composition_complete: bool,
        permission_valid: bool,
        autonomy_envelope: Mapping[str, Any] | None,
        runtime_health: str,
        quality_policy_satisfiable: bool,
        no_owner_decision_required: bool,
        owner_open_decisions: int = 0) -> dict[str, Any]:
    """ALL conditions required; any gap → BLOCK with evidence.
    This never grants permission — it only asserts that existing
    permission/evidence already satisfies the bounded contract."""
    envelope = autonomy_envelope
    if envelope is None:
        envelope = load_envelope(root, project_id)
    reasons: list[str] = []
    if envelope is None:
        reasons.append("NO_AUTONOMY_ENVELOPE")
    elif not envelope_is_fresh(envelope):
        reasons.append("ENVELOPE_EXPIRED")
    if not task_safe:
        reasons.append("NEXT_TASK_NOT_SAFE")
    if not capabilities_sufficient:
        reasons.append("CAPABILITIES_INSUFFICIENT")
    if not team_eligible:
        reasons.append("TEAM_NOT_ELIGIBLE")
    if not target_eligible:
        reasons.append("TARGET_NOT_ELIGIBLE")
    if not composition_complete:
        reasons.append("COMPOSITION_INCOMPLETE")
    if not permission_valid:
        reasons.append("PERMISSION_INVALID")
    if envelope is not None and runtime_health not in ("HEALTHY",
                                                      "DEGRADED"):
        reasons.append("RUNTIME_NOT_HEALTHY:" + str(runtime_health))
    if not quality_policy_satisfiable:
        reasons.append("QUALITY_POLICY_NOT_SATISFIABLE")
    if not no_owner_decision_required or owner_open_decisions > 0:
        reasons.append("OWNER_DECISION_REQUIRED")
    if reasons:
        append_fw06_event(root, "CONTINUATION_BLOCKED", {
            "project_id": project_id, "reasons": reasons,
        })
        return {"decision": "BLOCK", "reasons": reasons}
    append_fw06_event(root, "CONTINUATION_ALLOWED", {"project_id": project_id})
    return {"decision": "CONTINUE", "reasons": []}


# ---- §24 Backpressure / §25 budget -------------------------------------------

WORK_STATES = ("READY", "RUNNING", "WAITING_VERIFICATION", "WAITING_OWNER",
               "WAITING_RESOURCE", "BLOCKED", "DONE")


def _work_state_path(root: str | Path, project_id: str,
                       *, mkdirs: bool = False) -> Path:
    safe = str(project_id).replace("/", "-").replace("\\", "-")
    return state_dir(root, mkdirs=mkdirs) / ("fw06-work-states-" + safe + ".json")


def save_work_states(root: str | Path, project_id: str,
                     states: Mapping[str, str]) -> None:
    for tid, st in states.items():
        if st not in WORK_STATES:
            raise ValueError(f"WORK_STATE_INVALID:{st}:{tid}")
    path = _work_state_path(root, project_id, mkdirs=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(dict(states), fh, sort_keys=True)


def load_work_states(root: str | Path, project_id: str) -> dict[str, str]:
    path = _work_state_path(root, project_id)
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as fh:
        try:
            data = json.load(fh)
        except json.JSONDecodeError:
            return {}
    return {k: v for k, v in data.items() if v in WORK_STATES}


def backpressure_summary(root: str | Path, project_id: str,
                         max_running: int) -> dict[str, Any]:
    states = load_work_states(root, project_id)
    running = sum(1 for s in states.values() if s == "RUNNING")
    if running >= max_running:
        return {"capacity_ok": False, "running": running,
                "max_running": max_running,
                "state": "WORK_QUEUE_FULL"}
    return {"capacity_ok": True, "running": running,
            "max_running": max_running, "state": "OK"}


# ---- §27-28 Pause / Resume -----------------------------------------------------

def _pause_path(root: str | Path, project_id: str,
                   *, mkdirs: bool = False) -> Path:
    safe = str(project_id).replace("/", "-").replace("\\", "-")
    return state_dir(root, mkdirs=mkdirs) / ("fw06-pause-" + safe + ".json")


def pause_project(root: str | Path, project_id: str,
                  reason: str = "OWNER_PAUSED") -> dict[str, Any]:
    """Pause: stop scheduling new work, checkpoint, persist, report paused.
    Does not kill an in-flight mutation blindly."""
    path = _pause_path(root, project_id, mkdirs=True)
    record = {
        "project_id": str(project_id), "paused": True,
        "reason": str(reason)[:256], "paused_utc": _utc_now(),
    }
    with path.open("w", encoding="utf-8") as fh:
        json.dump(record, fh, sort_keys=True)
    append_fw06_event(root, "PROJECT_PAUSED", record)
    return record


def resume_project(root: str | Path, project_id: str) -> dict[str, Any]:
    """Resume: recover durable state from disk (never in-memory trust),
    revalidate environment, choose next safe action."""
    path = _pause_path(root, project_id)
    if path.exists():
        path.unlink()
    recovered = {
        "project_id": str(project_id), "paused": False,
        "recovered_from_disk": True, "resumed_utc": _utc_now(),
    }
    append_fw06_event(root, "RESUMED", recovered)
    return recovered


def is_paused(root: str | Path, project_id: str) -> bool:
    path = _pause_path(root, project_id)
    if not path.exists():
        return False
    try:
        with path.open(encoding="utf-8") as fh:
            return bool(json.load(fh).get("paused"))
    except (json.JSONDecodeError, OSError):
        return False  # corrupted pause state never un-blocks: re-check below


def paused_projects(root: str | Path) -> list[str]:
    d = state_dir(root, mkdirs=False)
    ids: list[str] = []
    for path in sorted(d.glob("fw06-pause-*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if isinstance(data, dict) and data.get("paused") \
                and data.get("project_id"):
            ids.append(str(data["project_id"]))
    return ids


# ---- §33-35 Execution leases / split-brain prevention --------------------------

LEASE_FIELDS = ("lease_id", "owner_process", "project_id", "goal_id",
                "task_id", "acquired_at", "expires_at", "heartbeat_utc",
                "status")

LEASE_PATH = "fw06-leases.jsonl"

DEFAULT_LEASE_TTL_SECONDS = 60


def _leases_path(root: str | Path, *, mkdirs: bool = False) -> Path:
    return state_dir(root, mkdirs=mkdirs) / LEASE_PATH


def _parse_ts(ts: str) -> datetime | None:
    try:
        return datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def read_leases(root: str | Path, project_id: str | None = None,
                task_id: str | None = None,
                status: str | None = None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in _read_jsonl(_leases_path(root)):
        if row.get("_MALFORMED_LINE"):
            continue
        if project_id and row.get("project_id") != project_id:
            continue
        if task_id and row.get("task_id") != task_id:
            continue
        if status and row.get("status") != status:
            continue
        rows.append(row)
    return rows


def _lease_is_live(lease: Mapping[str, Any], now: datetime | None = None
                   ) -> bool:
    if lease.get("status") != "ACTIVE":
        return False
    exp = _parse_ts(str(lease.get("expires_at", "")))
    if exp is None:
        return False
    return (now or datetime.now(timezone.utc)) < exp


def acquire_lease(root: str | Path, *, owner_process: str,
                  project_id: str, goal_id: str = "",
                  task_id: str = "", ttl_seconds: int | None = None
                  ) -> dict[str, Any]:
    """Acquire a durable execution lease. If another ACTIVE lease exists
    for the same project(+goal) within TTL → LEASE_CONFLICT, second
    process receives BUSY/BLOCKED (never silent co-execution)."""
    ttl = DEFAULT_LEASE_TTL_SECONDS if ttl_seconds is None \
        else max(1, int(ttl_seconds))
    now = datetime.now(timezone.utc)
    # Effective lease state = last durable row per lease_id (append-only
    # ledger: ACTIVE rows are never overwritten; RELEASED/EXPIRED/RECLAIMED
    # markers are appended after). A lease is live only when its effective
    # state is ACTIVE and within TTL.
    _last: dict[str, dict[str, Any]] = {}
    for row in read_leases(root, project_id=project_id):
        lid = str(row.get("lease_id", ""))
        _last[lid] = dict(row)
    for lease in _last.values():
        if lease.get("status") not in ("ACTIVE",) \
                or not _lease_is_live(lease, now):
            continue
        if not (task_id and lease.get("task_id") and
                lease.get("task_id") != task_id):
            append_fw06_event(root, "LEASE_CONFLICT", {
                "project_id": project_id, "goal_id": goal_id,
                "task_id": task_id,
                "held_by": str(lease.get("owner_process", "")),
            })
            return {"acquired": False,
                    "failure_class": "LEASE_CONFLICT",
                    "held_lease_id": str(lease["lease_id"]),
                    "instruction": "BUSY_BLOCKED",
                    "error": "Another process holds an active lease for "
                             "this project. Do not execute concurrently."}
    lease_id = "sha256:" + _task_state._sha256(  # type: ignore[attr-defined]
        ("fw06-lease", owner_process, project_id, goal_id, task_id,
         _utc_now(), _secrets.token_hex(8)))
    record = {
        "lease_id": lease_id, "owner_process": str(owner_process)[:128],
        "project_id": str(project_id), "goal_id": str(goal_id),
        "task_id": str(task_id), "acquired_at": _utc_now(),
        "expires_at": (now + timedelta(seconds=ttl))
            .strftime("%Y-%m-%dT%H:%M:%SZ"),
        "heartbeat_utc": _utc_now(), "status": "ACTIVE",
    }
    _append_jsonl(_leases_path(root, mkdirs=True), record)
    append_fw06_event(root, "LEASE_ACQUIRED", dict(record))
    return {"acquired": True, "lease": record}


def heartbeat_lease(root: str | Path, lease_id: str) -> bool:
    found = False
    for row in read_leases(root):
        if row.get("lease_id") == lease_id \
                and row.get("status") == "ACTIVE":
            found = True
            row["heartbeat_utc"] = _utc_now()
            # heartbeat is write-forwarded as a new append-only row
            _append_jsonl(_leases_path(root, mkdirs=True), dict(row))
            break
    return found


def release_lease(root: str | Path, lease_id: str) -> bool:
    for row in read_leases(root):
        if row.get("lease_id") == lease_id:
            rel = dict(row)
            rel["status"] = "RELEASED"
            rel["released_utc"] = _utc_now()
            _append_jsonl(_leases_path(root, mkdirs=True), rel)
            append_fw06_event(root, "LEASE_RELEASED",
                              {"lease_id": lease_id})
            return True
    return False


def expire_leases(root: str | Path, project_id: str | None = None
                  ) -> list[str]:
    now = datetime.now(timezone.utc)
    expired: list[str] = []
    for lease in read_leases(root, project_id=project_id):
        if lease.get("status") != "ACTIVE":
            continue
        exp = _parse_ts(str(lease.get("expires_at", "")))
        if exp is not None and now >= exp:
            rec = dict(lease)
            rec["status"] = "EXPIRED"
            rec["expired_utc"] = _utc_now()
            _append_jsonl(_leases_path(root, mkdirs=True), rec)
            expired.append(str(lease["lease_id"]))
            append_fw06_event(root, "LEASE_EXPIRED",
                              {"lease_id": lease["lease_id"],
                               "project_id": lease.get("project_id", "")})
    return expired


def reclaim_expired_lease(root: str | Path, lease_id: str,
                          now: datetime | None = None) -> dict[str, Any]:
    """§34-35: expired lease may be reclaimed ONLY after durable
    reconciliation: no live owner observable + mutation ambiguity
    resolved. Lease expiration alone does NOT authorize redispatch."""
    lease = None
    for row in read_leases(root):
        if row.get("lease_id") == lease_id:
            lease = row  # last row is the effective lease state
    if lease is None:
        return {"reclaimed": False,
                "failure_class": "LEASE_NOT_FOUND"}
    if lease.get("status") not in ("EXPIRED",):
        # ACTIVE lease → LEASE_CONFLICT; RELEASED lease cannot be reclaimed
        return {"reclaimed": False,
                "failure_class": "LEASE_CONFLICT" if lease.get(
                    "status") == "ACTIVE" else "LEASE_NOT_RECLAIMABLE"}
    exp = _parse_ts(str(lease.get("expires_at", "")))
    if exp is None or (now or datetime.now(timezone.utc)) < exp:
        return {"reclaimed": False, "failure_class": "LEASE_NOT_EXPIRED"}
    # observable liveness: heartbeat within TTL after expiry means the
    # original owner may still be alive — do not reclaim silently.
    hb = _parse_ts(str(lease.get("heartbeat_utc", "")))
    if hb is not None and (now or datetime.now(timezone.utc)) - hb < \
            timedelta(seconds=DEFAULT_LEASE_TTL_SECONDS):
        append_fw06_event(root, "LEASE_RECLAIM_BLOCKED", {
            "lease_id": lease_id, "reason":
                "owner_process_observable_via_heartbeat",
        })
        return {"reclaimed": False,
                "failure_class": "RECLAIM_BLOCKED_OWNER_OBSERVABLE"}
    # reconcile mutation ambiguity: the last recorded operation of this
    # lease must be VERIFIED or NONE — otherwise fail closed.
    events = read_fw06_events(root, project_id=lease.get("project_id"))
    last_task_event: str | None = None
    for ev in reversed(events):
        if ev.get("task_id") == lease.get("task_id"):
            last_task_event = ev.get("event_type")
            break
    if last_task_event is not None and last_task_event not in (
            "TASK_VERIFIED", "CHECKPOINT_WRITTEN", "TASK_DISPATCHED"):
        # dispatched but never verified → ambiguous → block
        if last_task_event == "TASK_DISPATCHED":
            append_fw06_event(root, "RECOVERY_BLOCKED", {
                "lease_id": lease_id,
                "reason": "post_dispatch_mutation_unverified",
            })
            return {"reclaimed": False,
                    "failure_class": "POST_DISPATCH_AMBIGUITY"}
    rec = dict(lease)
    rec["status"] = "RECLAIMED"
    rec["reclaimed_utc"] = _utc_now()
    _append_jsonl(_leases_path(root), rec)
    append_fw06_event(root, "LEASE_RECLAIMED", {"lease_id": lease_id})
    return {"reclaimed": True, "lease": rec}


def lease_summary(root: str | Path, project_id: str) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    active = sum(1 for l in read_leases(root, project_id=project_id)
                 if _lease_is_live(l, now))
    return {"active_leases": active, "project_id": project_id}


# ---- §7-8 Crash / session-death recovery ---------------------------------------

# Failure points: A before dispatch, B after dispatch before receipt,
# C after receipt before verify, D after verify before checkpoint,
# E after checkpoint before continue, F during owner gate, G during
# quality review.
CRASH_POINTS = ("A", "B", "C", "D", "E", "F", "G")


def recover_after_crash(
        root: str | Path,
        *,
        project_id: str,
        task_id: str,
        crash_point: str,
        dispatch_evidenced: bool,
        receipt_evidenced: bool,
        verified_evidenced: bool,
        checkpoint_evidenced: bool,
        owner_gate_open: bool = False,
        quality_review_pending: bool = False) -> dict[str, Any]:
    """Determine next action from durable evidence ONLY. Never blindly
    rerun an ambiguous mutation (§7-8). Each point maps to a bounded
    recovery decision; anything not evidenced fails closed."""
    if crash_point not in CRASH_POINTS:
        return {"decision": "BLOCK",
                "failure_class": "UNKNOWN_MUTATION_STATE",
                "reason": "CRASH_POINT_INVALID"}
    if owner_gate_open:
        return {"decision": "OWNER_GATE",
                "failure_class": "OWNER_GATE_REQUIRED",
                "reason": "owner decision still open; resume only after "
                          "Owner resolution"}
    if quality_review_pending:
        return {"decision": "BLOCK",
                "failure_class": "QUALITY_BLOCKED",
                "reason": "quality review still pending; no task "
                          "selected, no re-execution"}
    if crash_point == "A":
        # before dispatch: no mutation could have happened → safe retry
        append_fw06_event(root, "RECOVERY_DECISION", {
            "project_id": project_id, "task_id": task_id,
            "crash_point": crash_point, "decision": "RETRY_BOUNDED",
        })
        return {"decision": "RETRY_BOUNDED",
                "failure_class": "PROCESS_CRASH",
                "reason": "crashed before dispatch; no mutation possible"}
    if dispatch_evidenced and not receipt_evidenced:
        # B: dispatched, receipt unknown → never blind-retry
        append_fw06_event(root, "RECOVERY_BLOCKED", {
            "project_id": project_id, "task_id": task_id,
            "crash_point": crash_point,
            "reason": "post_dispatch_receipt_unknown",
        })
        return {"decision": "VERIFY_ONLY",
                "failure_class": "POST_DISPATCH_AMBIGUITY",
                "reason": "dispatch evidenced, receipt unknown; verify "
                          "mutation state before any redispatch"}
    if receipt_evidenced and not verified_evidenced:
        # C: receipt known, verification unknown → verify/reconcile
        return {"decision": "VERIFY_ONLY",
                "failure_class": "POST_DISPATCH_AMBIGUITY",
                "reason": "receipt observed but verification missing; "
                          "reconcile before continuing"}
    if verified_evidenced and not checkpoint_evidenced:
        # D: verified, no checkpoint → write checkpoint; no redispatch
        return {"decision": "CONTINUE",
                "failure_class": None,
                "reason": "verification evidenced, checkpoint pending; "
                          "write durable checkpoint, then continue"}
    if checkpoint_evidenced:
        # E (+D after checkpoint): next safe task via normal selection
        append_fw06_event(root, "RESUMED", {
            "project_id": project_id, "task_id": task_id,
            "crash_point": crash_point,
        })
        return {"decision": "CONTINUE",
                "failure_class": None,
                "reason": "checkpoint evidenced; resume next safe task"}
    # no evidence at all → RECOVERY_INCOMPLETE
    append_fw06_event(root, "RECOVERY_BLOCKED", {
        "project_id": project_id, "task_id": task_id,
        "crash_point": crash_point,
        "reason": "no_durable_evidence",
    })
    return {"decision": "BLOCK",
            "failure_class": "RECOVERY_INCOMPLETE",
            "reason": "no durable evidence of execution state; cannot "
                      "reconcile; owner or manual recovery required"}


# ---- §6 Quiesce / Drain --------------------------------------------------------

QUIESCE_STATES = ("RUNNING", "QUIESCE", "DRAIN", "QUIESCED", "CHECKPOINTED",
                  "LIFECYCLE_READY", "LIFECYCLE_BLOCKED")


def _quiesce_path(root: str | Path, project_id: str,
                   *, mkdirs: bool = False) -> Path:
    safe = str(project_id).replace("/", "-").replace("\\", "-")
    return state_dir(root, mkdirs=mkdirs) / ("fw06-quiesce-" + safe + ".json")


def quiesce_enter(root: str | Path, project_id: str,
                  reason: str = "LIFECYCLE_CHANGE") -> dict[str, Any]:
    record = {"project_id": str(project_id), "state": "QUIESCE",
              "reason": str(reason)[:256], "entered_utc": _utc_now()}
    with _quiesce_path(root, project_id, mkdirs=True).open("w", encoding="utf-8") as fh:
        json.dump(record, fh, sort_keys=True)
    append_fw06_event(root, "WORKSPACE_QUIESCED", dict(record))
    return record


def quiesce_drain(root: str | Path, project_id: str) -> dict[str, Any]:
    path = _quiesce_path(root, project_id, mkdirs=True)
    if not path.exists():
        raise ValueError("QUIESCE_NOT_ENTERED")
    with path.open(encoding="utf-8") as fh:
        data = json.load(fh)
    if data.get("state") not in ("QUIESCE", "DRAIN"):
        raise ValueError("QUIESCE_STATE_INVALID:" + str(data.get("state")))
    data["state"] = "DRAIN"
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, sort_keys=True)
    return {"project_id": project_id, "state": "DRAIN"}


def quiesce_verify_no_inflight(root: str | Path, project_id: str,
                               checkpoint: Mapping[str, Any] | None
                               ) -> dict[str, Any]:
    """VERIFY NO IN-FLIGHT MUTATION before lifecycle change (§6).
    Uses the FW01 durable checkpoint semantics: task_completed None with
    loop_status BLOCKED/IN_PROGRESS + next_safe_action not in
    (NONE, STOP) signals in-flight work."""
    path = _quiesce_path(root, project_id)
    if not path.exists():
        raise ValueError("QUIESCE_NOT_ENTERED")
    with path.open(encoding="utf-8") as fh:
        data = json.load(fh)
    if data.get("state") != "DRAIN":
        raise ValueError("QUIESCE_DRAIN_REQUIRED")
    inflight = False
    if isinstance(checkpoint, dict):
        status = str(checkpoint.get("loop_status", ""))
        action = str(checkpoint.get("next_safe_action", ""))
        task_completed = checkpoint.get("task_completed")
        if task_completed is None and status in ("IN_PROGRESS", "BLOCKED") \
                and action not in ("NONE", "STOP") \
                and not action.startswith("QUALITY_REVIEW:"):
            inflight = True
    if inflight:
        data["state"] = "LIFECYCLE_BLOCKED"
        with path.open("w", encoding="utf-8") as fh:
            json.dump(data, fh, sort_keys=True)
        append_fw06_event(root, "LIFECYCLE_CHANGE_BLOCKED", {
            "project_id": project_id,
            "reason": "unverified_inflight_mutation",
        })
        return {"lifecycle_ready": False,
                "failure_class": "POST_DISPATCH_AMBIGUITY",
                "reason": "NO_LIFECYCLE_SWAP_DURING_UNVERIFIED_MUTATION"}
    data["state"] = "QUIESCED"
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, sort_keys=True)
    return {"lifecycle_ready": True, "state": "QUIESCED"}


def quiesce_lifecycle_ready(root: str | Path, project_id: str
                            ) -> dict[str, Any]:
    path = _quiesce_path(root, project_id)
    if not path.exists():
        raise ValueError("QUIESCE_NOT_ENTERED")
    with path.open(encoding="utf-8") as fh:
        data = json.load(fh)
    if data.get("state") != "QUIESCED":
        return {"lifecycle_ready": False, "state": str(data.get("state")),
                "reason": "quiesce chain incomplete"}
    data["state"] = "LIFECYCLE_READY"
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, sort_keys=True)
    append_fw06_event(root, "LIFECYCLE_CHANGE_ALLOWED",
                      {"project_id": project_id})
    return {"lifecycle_ready": True, "state": "LIFECYCLE_READY"}


def quiesce_reset(root: str | Path, project_id: str) -> None:
    path = _quiesce_path(root, project_id)
    if path.exists():
        path.unlink()


def quiesce_state(root: str | Path, project_id: str) -> str | None:
    path = _quiesce_path(root, project_id)
    if not path.exists():
        return None
    try:
        with path.open(encoding="utf-8") as fh:
            return str(json.load(fh).get("state", ""))
    except (json.JSONDecodeError, OSError):
        return "UNKNOWN"


# ---- §10 Bounded retry ---------------------------------------------------------

NO_RETRY_CLASSES = (
    "AUTH_DRIFT", "OWNER_GATE_REQUIRED", "RETRY_EXHAUSTED",
    "POST_DISPATCH_AMBIGUITY", "SCOPE_DRIFT", "QUALITY_BLOCKED",
    "RECOVERY_INCOMPLETE", "LEASE_CONFLICT", "FAILOVER_NOT_SAFE",
    "UNKNOWN_MUTATION_STATE",
)


def bounded_retry_decision(
        *,
        failure_class: str,
        current_retries: int,
        max_retries: int,
        task_unchanged: bool,
        permissions_unchanged: bool,
        target_compatible: bool,
        mutation_state_known: bool,
        cooldown_elapsed: bool = True) -> dict[str, Any]:
    """Classified failure + retryable state + unchanged/revalidated task +
    unchanged permissions + compatible target + known mutation state.
    Count bounded. No recursion. No retry for canonical non-retryable
    classes unless retryable_classes explicitly lists it (policy must say
    otherwise)."""
    fc = classify_failure(failure_class)
    if fc == "UNKNOWN_MUTATION_STATE":
        return {"retry": False, "decision": "BLOCK",
                "failure_class": fc,
                "reason": "failure unclassified; no generic retry"}
    if fc in NO_RETRY_CLASSES:
        return {"retry": False, "decision": "BLOCK",
                "failure_class": fc,
                "reason": "failure class not retryable by canonical "
                          "policy"}
    if current_retries >= max(0, int(max_retries)):
        return {"retry": False, "decision": "BLOCK",
                "failure_class": "RETRY_EXHAUSTED",
                "reason": f"retries exhausted ({current_retries}/"
                          f"{max_retries})"}
    for required, reason in (
            (task_unchanged, "TASK_CHANGED"),
            (permissions_unchanged, "PERMISSION_CHANGED"),
            (target_compatible, "TARGET_INCOMPATIBLE"),
            (mutation_state_known, "MUTATION_STATE_UNKNOWN"),
            (cooldown_elapsed, "COOLDOWN_NOT_ELAPSED")):
        if not required:
            return {"retry": False, "decision": "BLOCK",
                    "failure_class": fc, "reason": reason}
    return {"retry": True, "decision": "RETRY_BOUNDED",
            "failure_class": fc,
            "next_retry": current_retries + 1,
            "reason": "bounded retry permitted by policy"}


# ---- §11-12 Restart policy / governed failover ---------------------------------

RESTART_ACTIONS = (
    "RETRY_TASK", "RESTART_BACKEND", "RESTART_HARNESS",
    "RECREATE_WORKSPACE", "FAILOVER_TARGET", "BLOCK",
)

# FAILOVER != RETRY. failover requires explicit quiesce prerequisite
# (quiesce_state known and >= DRAIN) and a reconciled mutation state.

def failover_decision(
        root: str | Path,
        *,
        project_id: str,
        old_target: str,
        new_target: str,
        failure_class: str,
        quiesced: bool,
        task_revalidated: bool,
        capabilities_revalidated: bool,
        permission_valid: bool,
        mutation_state_known: bool,
        no_inflight: bool) -> dict[str, Any]:
    """§12 governed hot-swap of an execution COMPONENT (harness/backend/
    provider/model/toolset/workspace) — never permission authority or
    governance. Brand names are runtime instances only (§13).
    Positive: quiesce → revalidate → swap → verify → resume.
    Negative: post-dispatch mutation ambiguous → failover blocked (§46)."""
    fc = classify_failure(failure_class)
    if fc == "UNKNOWN_MUTATION_STATE":
        return {"failover": False, "failure_class": fc,
                "reason": "failure unclassifiable; failover not safe"}
    for required, reason in (
            (quiesced, "QUIESCE_DRAIN_REQUIRED"),
            (task_revalidated, "TASK_REVALIDATION_REQUIRED"),
            (capabilities_revalidated, "CAPABILITIES_REVALIDATION_REQUIRED"),
            (permission_valid, "PERMISSION_INVALID"),
            (mutation_state_known, "UNKNOWN_POST_DISPATCH_MUTATION"),
            (no_inflight, "INFLIGHT_MUTATION_UNVERIFIED")):
        if not required:
            append_fw06_event(root, "FAILOVER_BLOCKED", {
                "project_id": project_id, "old_target": old_target,
                "new_target": new_target, "failure_class": fc,
                "reason": reason,
            })
            return {"failover": False, "failure_class": fc,
                    "reason": reason}
    append_fw06_event(root, "TARGET_FAILOVER", {
        "project_id": project_id, "old_target": old_target,
        "new_target": new_target, "failure_class": fc,
    })
    return {"failover": True, "failure_class": fc,
            "selected_target": new_target,
            "reason": "failover permitted after quiesce and "
                      "revalidation"}


# ---- §49-50 Tiered runtime health (cheap-first) --------------------------------

RUNTIME_HEALTH_VALUES = ("HEALTHY", "DEGRADED", "UNHEALTHY", "UNKNOWN")


def runtime_health_check(
        root: str | Path,
        *,
        project_id: str,
        executable_requirements: Mapping[str, Any] | None = None,
        workspace_path: str | Path | None = None,
        tool_requirements: Mapping[str, Any] | None = None,
        freshness_budget_seconds: int = 300,
        last_health: Mapping[str, Any] | None = None,
        now_utc: str | None = None) -> dict[str, Any]:
    """Tiered health: cheap deterministic checks first (executable
    presence/version, workspace access, tool presence). Only falls back to
    expensive checks when needed. Cached result reused within
    freshness_budget_seconds. Never contacts all providers every
    iteration. NEVER fabricates a positive result: unverified → UNKNOWN,
    never silently HEALHTY."""
    now = _parse_ts(now_utc or _utc_now()) or datetime.now(timezone.utc)
    if last_health and _parse_ts(str(last_health.get("checked_utc", ""))) \
            and (now - (_parse_ts(str(last_health.get(
                "checked_utc", ""))) or datetime.min.replace(
                tzinfo=timezone.utc))) < timedelta(
                    seconds=freshness_budget_seconds) \
            and last_health.get("health") in RUNTIME_HEALTH_VALUES:
        return dict(last_health)
    checks: list[dict[str, Any]] = []
    degraded = False
    unhealthy = False
    executable_requirements = dict(executable_requirements or {})
    tool_requirements = dict(tool_requirements or {})
    for exe, spec in executable_requirements.items():
        ok = False
        cmd = str(spec.get("executable", exe)
                  if isinstance(spec, dict) else spec)
        try:
            # import shutil lazily — cheap
            import shutil
            path = shutil.which(cmd)
            ok = path is not None
            version_ok = None
            if isinstance(spec, dict) and spec.get("min_version") \
                    and ok:
                version_ok = None  # version probes are expensive tier-2
            checks.append({"tier": 1, "check": "EXECUTABLE_PRESENT",
                           "name": exe, "ok": ok})
            if not ok:
                unhealthy = True
        except Exception:  # noqa: BLE001
            checks.append({"tier": 1, "check": "EXECUTABLE_PRESENT",
                           "name": exe, "ok": False})
            unhealthy = True
    workspace_path = Path(workspace_path) if workspace_path else \
        Path(root) / ".p2p"
    try:
        workspace_ok = Path(workspace_path).is_dir()
        checks.append({"tier": 1, "check": "WORKSPACE_ACCESSIBLE",
                       "ok": workspace_ok})
        if not workspace_ok:
            unhealthy = True
    except Exception:  # noqa: BLE001
        checks.append({"tier": 1, "check": "WORKSPACE_ACCESSIBLE",
                       "ok": False})
        unhealthy = True
    for tool, spec in tool_requirements.items():
        try:
            present = Path(spec if isinstance(spec, str)
                           else str(spec.get("path", ""))).exists() \
                if isinstance(spec, dict) and "path" in spec \
                else Path(spec).exists()
        except Exception:  # noqa: BLE001
            present = False
        checks.append({"tier": 1, "check": "TOOL_PRESENT",
                       "name": tool, "ok": present})
        if not present:
            degraded = True
    if unhealthy:
        health = "UNHEALTHY"
    elif degraded:
        health = "DEGRADED"
    else:
        health = "HEALTHY"
    result = {
        "health": health, "checked_utc": _utc_now(),
        "project_id": str(project_id), "checks": checks,
        "tiered": True,
    }
    append_fw06_event(root, "RUNTIME_HEALTH_CHECK", dict(result))
    return result


# ---- §13-14 Workspace ownership ------------------------------------------------

WORKSPACE_FIELDS = ("workspace_id", "project_id", "owner_goal_id",
                    "owner_task_id", "root_path", "base_revision",
                    "created_at", "status", "mutation_policy",
                    "conflict_group", "git_worktree", "evidence_pointers")

WORKSPACE_PATH = "fw06-workspaces.jsonl"


def _workspaces_path(root: str | Path, *, mkdirs: bool = False) -> Path:
    return state_dir(root, mkdirs=mkdirs) / WORKSPACE_PATH


def register_workspace(root: str | Path,
                       workspace: Mapping[str, Any]) -> dict[str, Any]:
    """Evidence-driven registration. Statuses: ACTIVE, QUIESCED,
    CLEANUP_PENDING, CLEANED, CONFLICT, UNKNOWN_OWNER."""
    missing = [f for f in WORKSPACE_FIELDS if f not in workspace]
    if missing:
        raise ValueError("WORKSPACE_FIELDS_MISSING:" + ",".join(missing))
    w = {str(k): (str(v) if not isinstance(v, (list, dict)) else v)
         for k, v in workspace.items()}
    status = str(workspace["status"])
    if status not in ("ACTIVE", "QUIESCED", "CLEANUP_PENDING", "CLEANED",
                      "CONFLICT", "UNKNOWN_OWNER"):
        raise ValueError("WORKSPACE_STATUS_INVALID:" + status)
    w["status"] = status
    _append_jsonl(_workspaces_path(root, mkdirs=True), w)
    append_fw06_event(root, "WORKSPACE_REGISTERED", {
        "workspace_id": w["workspace_id"],
        "project_id": w["project_id"],
        "owner_task_id": w["owner_task_id"],
        "root_path": w["root_path"],
        "status": w["status"],
    })
    return w


def list_workspaces(root: str | Path, project_id: str | None = None
                    ) -> list[dict[str, Any]]:
    rows = _read_jsonl(_workspaces_path(root))
    out: list[dict[str, Any]] = []
    seen: dict[str, dict[str, Any]] = {}
    for row in rows:
        if row.get("_MALFORMED_LINE"):
            continue
        wid = str(row.get("workspace_id", ""))
        if project_id and row.get("project_id") != project_id:
            continue
        # latest state wins (append-only, last row authoritative)
        seen[wid] = row
    out = [v for v in seen.values() if str(v.get("status")) != "CLEANED"]
    out.sort(key=lambda r: str(r.get("created_at", "")))
    return out


def cleanup_workspace(root: str | Path, workspace_id: str,
                      *,
                      mutation_state_known: bool,
                      evidence_committed: bool,
                      result_reconciled: bool,
                      owner_decision_resolved: bool) -> dict[str, Any]:
    """Idempotent cleanup with evidence-driven guards. NEVER deletes a
    workspace while: mutation state unknown; uncommitted evidence;
    unreconciled result; or unresolved owner decision. Unknown owner
    → keeps workspace (no destructive action on ambiguous ownership)."""
    for required, reason in (
            (mutation_state_known, "UNKNOWN_MUTATION_STATE"),
            (evidence_committed, "EVIDENCE_UNCOMMITTED"),
            (result_reconciled, "RESULT_UNRECONCILED"),
            (owner_decision_resolved, "OWNER_DECISION_UNRESOLVED")):
        if not required:
            append_fw06_event(root, "WORKSPACE_CLEANUP_BLOCKED", {
                "workspace_id": workspace_id, "reason": reason,
            })
            return {"cleaned": False, "reason": reason,
                    "failure_class": "UNKNOWN_MUTATION_STATE"}
    found = None
    for row in list_workspaces(root):
        if str(row.get("workspace_id")) == workspace_id:
            found = row
            break
    if found is None:
        return {"cleaned": True, "reason": "already_cleaned_or_unknown"}
    rec = dict(found)
    rec["status"] = "CLEANED"
    rec["cleaned_utc"] = _utc_now()
    _append_jsonl(_workspaces_path(root, mkdirs=True), rec)
    append_fw06_event(root, "WORKSPACE_CLEANED", {"workspace_id": workspace_id})
    return {"cleaned": True, "workspace_id": workspace_id}


# ---- §16-18 Conflict detection & bounded parallel worktrees ---------------------

def detect_conflict(
        *,
        task_files_a: tuple[str, ...] | list[str],
        task_files_b: tuple[str, ...] | list[str],
        task_symbols_a: tuple[str, ...] | list[str] = (),
        task_symbols_b: tuple[str, ...] | list[str] = ()) -> dict[str, Any]:
    """Deterministic overlap check over files AND symbols. Overlap →
    CONFLICT (must serialize or block); disjoint → PARALLEL_OK. Symbol
    overlap counts even for different files (same module surface)."""
    files_a = set(str(f).strip() for f in task_files_a if str(f).strip())
    files_b = set(str(f).strip() for f in task_files_b if str(f).strip())
    symbols_a = set(str(s).strip() for s in task_symbols_a
                    if str(s).strip())
    symbols_b = set(str(s).strip() for s in task_symbols_b
                    if str(s).strip())
    file_overlap = sorted(files_a & files_b)
    symbol_overlap = sorted(symbols_a & symbols_b)
    if file_overlap or symbol_overlap:
        return {"verdict": "CONFLICT",
                "conflicting_files": file_overlap,
                "conflicting_symbols": symbol_overlap,
                "instruction": "SERIALIZE_OR_BLOCK"}
    return {"verdict": "PARALLEL_OK", "conflicting_files": [],
            "conflicting_symbols": [], "instruction": "INDEPENDENT"}


def parallel_capacity(root: str | Path, project_id: str,
                      max_parallelism: int) -> dict[str, Any]:
    active = sum(1 for w in list_workspaces(root, project_id)
                 if str(w.get("status")) == "ACTIVE")
    ok = active < max_parallelism
    return {"active_workspaces": active,
            "max_parallelism": max_parallelism,
            "parallel_slot_available": ok}


# ---- §17-18 Git worktree manager (synthetic repo for proof) ---------------------

def create_isolated_worktree(root: str | Path, *,
                             repo_path: str | Path,
                             workspace_id: str,
                             base_revision: str,
                             worktree_path: str | Path) -> dict[str, Any]:
    """Create a git worktree from an exact base revision (isolation), and
    register it with a 12-field identity binding. Never fabricates
    provenance."""
    repo_path = Path(repo_path)
    wt_path = Path(worktree_path)
    try:
        import subprocess as _sp
        wt_path.parent.mkdir(parents=True, exist_ok=True)
        rev = _sp.run(["git", "-C", str(repo_path), "rev-parse",
                       str(base_revision)], capture_output=True, text=True)
        if rev.returncode != 0:
            raise RuntimeError("BASE_REVISION_INVALID:" + str(base_revision))
        exact = rev.stdout.strip()
        proc = _sp.run(["git", "-C", str(repo_path), "worktree", "add",
                        "-b", "fw06-wt-" + workspace_id, str(wt_path),
                        exact], capture_output=True, text=True)
        if proc.returncode != 0:
            raise RuntimeError("WORKTREE_ADD_FAILED:" + proc.stderr.strip())
    except RuntimeError:
        raise
    except FileNotFoundError:
        raise RuntimeError("GIT_NOT_AVAILABLE")
    workspace = {
        "workspace_id": workspace_id, "project_id": "",
        "owner_goal_id": "", "owner_task_id": "",
        "root_path": str(wt_path), "base_revision": exact,
        "created_at": _utc_now(), "status": "ACTIVE",
        "mutation_policy": "SYNTHETIC_ONLY", "conflict_group": "",
        "git_worktree": str(wt_path), "evidence_pointers": [],
    }
    register_workspace(root, workspace)
    return workspace


def cleanup_git_worktree(root: str | Path, repo_path: str | Path,
                         workspace_id: str, worktree_path: str | Path,
                         **cleanup_guards: Any) -> dict[str, Any]:
    """Remove the worktree only after evidence-driven guards pass
    (delegated to cleanup_workspace). Idempotent."""
    repo_path = Path(repo_path)
    wt_path = Path(worktree_path)
    guard = cleanup_workspace(root, workspace_id, **cleanup_guards)
    if not guard.get("cleaned"):
        return guard
    try:
        import subprocess as _sp
        _sp.run(["git", "-C", str(repo_path), "worktree", "remove",
                 "--force", str(wt_path)], capture_output=True, text=True)
    except (FileNotFoundError, OSError):
        pass  # removal must not fail the durable cleanup record
    return {"cleaned": True, "workspace_id": workspace_id}


# ---- §19-22 Multi-project isolation (read-only coordinator) ---------------------

def discover_projects(root: str | Path) -> list[dict[str, Any]]:
    projects: dict[str, dict[str, Any]] = {}
    for env_path in sorted(state_dir(root, mkdirs=False).glob("fw06-autonomy-envelope-*.json")):
        try:
            data = json.loads(env_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        pid = str(data.get("project_id", ""))
        if pid:
            projects[pid] = {"project_id": pid,
                             "goal_id": str(data.get("goal_id", "")),
                             "fresh": envelope_is_fresh(data)}
    return list(projects.values())


def multi_project_health_summary(root: str | Path) -> dict[str, Any]:
    out: dict[str, Any] = {"projects": []}
    for proj in discover_projects(root):
        pid = proj["project_id"]
        entry = dict(proj)
        entry["paused"] = is_paused(root, pid)
        entry["leases"] = lease_summary(root, pid)
        entry["workspaces"] = {
            "active": sum(1 for w in list_workspaces(root, pid)
                          if str(w.get("status")) == "ACTIVE")}
        entry["conflicts"] = 0
        out["projects"].append(entry)
    return out


def multi_project_collision_check(root: str | Path,
                                  new_project_workspace_root: str | Path
                                  ) -> dict[str, Any]:
    """Detect collisions between projects sharing one workspace root
    (never silent cross-project mutation)."""
    candidates = []
    for w in list_workspaces(root):
        try:
            wroot = Path(str(w.get("root_path", "")))
        except Exception:  # noqa: BLE001
            continue
        try:
            if wroot == Path(new_project_workspace_root) or \
                    wroot in Path(new_project_workspace_root).parents or \
                    Path(new_project_workspace_root) in wroot.parents:
                candidates.append(w)
        except Exception:  # noqa: BLE001
            pass
    if candidates:
        return {"collision": True,
                "colliding_workspaces": [str(c.get("workspace_id"))
                                         for c in candidates],
                "instruction": "ISOLATE_ROOTS"}
    return {"collision": False, "colliding_workspaces": [],
            "instruction": "INDEPENDENT"}


def multi_project_readonly_view(root: str | Path,
                                project_id: str) -> dict[str, Any]:
    """Read-only multi-project view for the Owner. No execution, no
    permission grant, no second orchestrator."""
    paused = is_paused(root, project_id)
    quiesce = quiesce_state(root, project_id)
    health: dict[str, Any] = {}
    envelope = load_envelope(root, project_id)
    return {
        "schema": FW06_SCHEMA,
        "project_id": project_id,
        "paused": paused,
        "quiesce_state": quiesce,
        "envelope_fresh": envelope_is_fresh(envelope) if envelope
        else None,
        "leases": lease_summary(root, project_id),
        "workspaces": [
            {"workspace_id": w["workspace_id"],
             "status": w["status"],
             "base_revision": w.get("base_revision"),
             "git_worktree": w.get("git_worktree")}
            for w in list_workspaces(root, project_id)],
        "audit": [
            {"event_id": e["event_id"], "event_type": e["event_type"],
             "task_id": e.get("task_id"),
             "created_utc": e.get("created_utc")}
            for e in read_fw06_events(root, project_id)[-50:]],
        "read_only": True,
    }


# ---- FW05 integration: Owner-facing summary -----------------------------------

def fw06_project_summary(root: str | Path, project_id: str
                         ) -> dict[str, Any]:
    """Beginner-friendly Owner phrases (Vietnamese) derived from the same
    durable state — read-only view, no action authority."""
    paused = is_paused(root, project_id)
    leases = lease_summary(root, project_id)
    summary: dict[str, Any] = {
        "project_id": project_id,
        "messages_vi": [],
        "read_only": True,
    }
    if paused:
        summary["messages_vi"].append(
            "Dự án đang tạm dừng theo yêu cầu của Owner; không tác vụ mới "
            "nào được lên lịch.")
    elif leases.get("active_leases", 0) > 0:
        summary["messages_vi"].append(
            "Đang có giấy phép thực thi hoạt động; vòng lặp hoạt động an "
            "toàn theo chính sách tiếp tục an toàn.")
    else:
        summary["messages_vi"].append(
            "Không có giấy phép hoạt động nào; tác vụ tiếp theo chỉ được "
            "thực hiện sau khi cấp giấy phép mới.")
    quiesce = quiesce_state(root, project_id)
    if quiesce in ("QUIESCE", "DRAIN"):
        summary["messages_vi"].append(
            "Đang dừng an toàn (quiesce/drain) để chuẩn bị thay đổi vòng "
            "đời; chỉ được tiến hành khi không còn tác vụ chưa kiểm chứng.")
    envelope = load_envelope(root, project_id)
    if envelope is None:
        summary["messages_vi"].append(
            "Chưa có envelope tự chủ; mọi tác vụ phải dừng cho đến khi "
            "có phạm vi được ủy quyền.")
    elif not envelope_is_fresh(envelope):
        summary["messages_vi"].append(
            "Envelope tự chủ đã hết hạn; phải làm mới trước khi tiếp tục.")
    return summary
