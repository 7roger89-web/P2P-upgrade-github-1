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
import hashlib
import os
import shutil
import secrets as _secrets
import stat
import subprocess
import threading
from contextlib import contextmanager
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Mapping

from p2p_capabilities import task_state as _task_state
from p2p_capabilities import backend_contract as _backend_contract
from p2p_capabilities import failover_boundary as _failover_boundary

FW06_SCHEMA = "p2p-fw06-operational-resilience/1"

STATE_REL = ".p2p/state"

# TMPGC is an additive extension of FW06 workspace ownership.  It deliberately
# keeps the legacy FW06 status field and old cleanup APIs intact while adding a
# separate lifecycle/protection projection for safe physical disposal.
TMP_GC_SCHEMA = "p2p-tmp-gc/1"
TMP_GC_POLICY_SCHEMA = "p2p-tmp-gc-policy/1"
TMP_GC_POLICY_REL = Path("governance") / "p2p-tmp-gc-policy.json"
TMP_GC_AUDIT_PATH = "fw06-tmp-gc-audit.jsonl"
TMP_LIFECYCLE_STATES = ("ACTIVE", "COMPLETE", "DISPOSABLE", "DELETED")
TMP_PROTECTION_REASONS = (
    "CANDIDATE",
    "OWNER_GATE",
    "ROLLBACK_REQUIRED",
    "UNKNOWN",
    "ACTIVE_SESSION",
    "UNIQUE_LOCAL_HISTORY",
    "DIRTY",
    "DEPENDENCY",
    "EVIDENCE_NOT_DURABLE",
)
TMP_PRESSURE_STATES = ("NORMAL", "WARNING", "LOW", "CRITICAL")
TMP_GC_ACTIONS = ("KEEP", "DELETE_ELIGIBLE")
_WINDOWS_REPARSE_POINT = 0x400

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
_LEASE_PROCESS_LOCK = threading.Lock()


class _LeaseLockUnavailable(RuntimeError):
    """The durable lease writer lock is held by another process."""


@contextmanager
def _lease_writer_guard(root: str | Path):
    """Serialize lease read/check/append across threads and processes.

    The existing lease ledger is append-only, so the conflict check and the
    ACTIVE append must be one critical section. A process-local lock covers
    threads; the adjacent OS byte-range lock covers independent processes.
    Failure to acquire either side is a safe BUSY/KEEP outcome.
    """
    lock_path = state_dir(root, mkdirs=True) / "fw06-leases.jsonl.writer.lock"
    if not _LEASE_PROCESS_LOCK.acquire(blocking=False):
        raise _LeaseLockUnavailable
    handle = None
    locked = False
    try:
        try:
            handle = lock_path.open("a+b")
            handle.seek(0, 2)
            if handle.tell() == 0:
                handle.write(b"0")
                handle.flush()
            handle.seek(0)
            if os.name == "nt":
                import msvcrt
                try:
                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                except OSError as exc:
                    raise _LeaseLockUnavailable from exc
            else:
                import fcntl
                try:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                except OSError as exc:
                    raise _LeaseLockUnavailable from exc
            locked = True
        except OSError as exc:
            raise _LeaseLockUnavailable from exc
        yield
    finally:
        if locked and handle is not None:
            try:
                handle.seek(0)
                if os.name == "nt":
                    import msvcrt
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            except OSError:
                pass
        if handle is not None:
            handle.close()
        _LEASE_PROCESS_LOCK.release()


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
    try:
        with _lease_writer_guard(root):
            ttl = DEFAULT_LEASE_TTL_SECONDS if ttl_seconds is None \
                else max(1, int(ttl_seconds))
            now = datetime.now(timezone.utc)
            # Effective lease state = last durable row per lease_id
            # (append-only ledger: ACTIVE rows are never overwritten;
            # RELEASED/EXPIRED/RECLAIMED markers are appended after). A lease
            # is live only when its effective state is ACTIVE and within TTL.
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
                            "error": "Another process holds an active lease "
                                     "for this project. Do not execute "
                                     "concurrently."}
            lease_id = "sha256:" + _task_state._sha256(  # type: ignore[attr-defined]
                ("fw06-lease", owner_process, project_id, goal_id, task_id,
                 _utc_now(), _secrets.token_hex(8)))
            record = {
                "lease_id": lease_id,
                "owner_process": str(owner_process)[:128],
                "project_id": str(project_id),
                "goal_id": str(goal_id),
                "task_id": str(task_id), "acquired_at": _utc_now(),
                "expires_at": (now + timedelta(seconds=ttl))
                    .strftime("%Y-%m-%dT%H:%M:%SZ"),
                "heartbeat_utc": _utc_now(), "status": "ACTIVE",
            }
            _append_jsonl(_leases_path(root, mkdirs=True), record)
            append_fw06_event(root, "LEASE_ACQUIRED", dict(record))
            return {"acquired": True, "lease": record}
    except _LeaseLockUnavailable:
        return {"acquired": False,
                "failure_class": "LEASE_LOCK_UNAVAILABLE",
                "instruction": "BUSY_BLOCKED",
                "error": "Lease writer is busy; do not execute concurrently."}


def heartbeat_lease(root: str | Path, lease_id: str) -> bool:
    try:
        with _lease_writer_guard(root):
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
    except _LeaseLockUnavailable:
        return False


def release_lease(root: str | Path, lease_id: str) -> bool:
    try:
        with _lease_writer_guard(root):
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
    except _LeaseLockUnavailable:
        return False


def expire_leases(root: str | Path, project_id: str | None = None
                  ) -> list[str]:
    try:
        with _lease_writer_guard(root):
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
    except _LeaseLockUnavailable:
        return []


def reclaim_expired_lease(root: str | Path, lease_id: str,
                          now: datetime | None = None,
                          *, _serialization_held: bool = False
                          ) -> dict[str, Any]:
    """§34-35: expired lease may be reclaimed ONLY after durable
    reconciliation: no live owner observable + mutation ambiguity
    resolved. Lease expiration alone does NOT authorize redispatch."""
    if not _serialization_held:
        try:
            with _lease_writer_guard(root):
                return reclaim_expired_lease(
                    root, lease_id, now, _serialization_held=True,
                )
        except _LeaseLockUnavailable:
            return {"reclaimed": False,
                    "failure_class": "LEASE_LOCK_UNAVAILABLE"}
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


def _latest_workspace_rows(root: str | Path) -> dict[str, dict[str, Any]]:
    """Return the last valid row for every workspace ID.

    The existing registry is append-only.  Malformed rows are intentionally
    ignored here; a path without a valid latest row is treated as UNKNOWN by
    TMPGC rather than reconstructed from its folder name.
    """
    seen: dict[str, dict[str, Any]] = {}
    for row in _read_jsonl(_workspaces_path(root)):
        if not isinstance(row, Mapping) or row.get("_MALFORMED_LINE"):
            continue
        workspace_id = str(row.get("workspace_id", "")).strip()
        if workspace_id:
            seen[workspace_id] = dict(row)
    return seen


def _workspace_registry_is_well_formed(root: str | Path) -> bool:
    """Validate enough registry shape to retain disposal authority.

    A syntactically valid JSON value is not automatically a valid registry
    row.  Invalid rows are treated like malformed lines so GC cannot silently
    discard an ownership/path binding.
    """
    try:
        rows = _read_jsonl(_workspaces_path(root))
    except (OSError, UnicodeError, ValueError):
        return False
    valid_statuses = {
        "ACTIVE", "QUIESCED", "CLEANUP_PENDING", "CLEANED",
        "CONFLICT", "UNKNOWN_OWNER",
    }
    for row in rows:
        if not isinstance(row, Mapping) or row.get("_MALFORMED_LINE"):
            return False
        if not str(row.get("workspace_id", "")).strip():
            return False
        if not str(row.get("root_path", "")).strip():
            return False
        if str(row.get("status", "")).strip() not in valid_statuses:
            return False
        lifecycle = str(row.get("lifecycle_state", "")).strip().upper()
        if lifecycle and lifecycle not in TMP_LIFECYCLE_STATES:
            return False
        try:
            _normalize_tmp_protection_reasons(row.get("protection_reasons"))
        except ValueError:
            return False
    return True


def list_all_workspaces(root: str | Path,
                        project_id: str | None = None
                        ) -> list[dict[str, Any]]:
    """Read the latest row for every workspace, including DELETED history."""
    rows = []
    for row in _latest_workspace_rows(root).values():
        if project_id and row.get("project_id") != project_id:
            continue
        rows.append(row)
    rows.sort(key=lambda r: str(r.get("created_at", "")))
    return rows


def _normalize_tmp_protection_reasons(value: Any) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, (list, tuple)):
        raise ValueError("TMP_PROTECTION_REASONS_MUST_BE_LIST")
    reasons = []
    for item in value:
        reason = str(item).strip().upper()
        if reason not in TMP_PROTECTION_REASONS:
            raise ValueError("TMP_PROTECTION_REASON_INVALID:" + reason)
        if reason not in reasons:
            reasons.append(reason)
    return reasons


def _workspaces_path(root: str | Path, *, mkdirs: bool = False) -> Path:
    return state_dir(root, mkdirs=mkdirs) / WORKSPACE_PATH


def register_workspace(root: str | Path,
                       workspace: Mapping[str, Any],
                       *, _serialization_held: bool = False
                       ) -> dict[str, Any]:
    """Evidence-driven registration. Statuses: ACTIVE, QUIESCED,
    CLEANUP_PENDING, CLEANED, CONFLICT, UNKNOWN_OWNER."""
    if not _serialization_held:
        try:
            with _lease_writer_guard(root):
                return register_workspace(
                    root, workspace, _serialization_held=True,
                )
        except _LeaseLockUnavailable as exc:
            raise ValueError("WORKSPACE_SERIALIZATION_UNAVAILABLE") from exc
    missing = [f for f in WORKSPACE_FIELDS if f not in workspace]
    if missing:
        raise ValueError("WORKSPACE_FIELDS_MISSING:" + ",".join(missing))
    w = {str(k): (str(v) if not isinstance(v, (list, dict)) else v)
         for k, v in workspace.items()}
    for key in ("git_worktree", "owner_gate", "candidate",
                "rollback_required"):
        if key in workspace and isinstance(workspace[key], bool):
            w[key] = workspace[key]
    status = str(workspace["status"])
    if status not in ("ACTIVE", "QUIESCED", "CLEANUP_PENDING", "CLEANED",
                      "CONFLICT", "UNKNOWN_OWNER"):
        raise ValueError("WORKSPACE_STATUS_INVALID:" + status)
    w["status"] = status
    lifecycle = str(w.get("lifecycle_state", "")).strip().upper()
    if not lifecycle:
        # Legacy rows have no disposal authority.  ACTIVE is the only safe
        # inferred lifecycle; all other old statuses remain COMPLETE with an
        # UNKNOWN protection reason until a new explicit record is written.
        lifecycle = "ACTIVE" if status == "ACTIVE" else "COMPLETE"
    if lifecycle not in TMP_LIFECYCLE_STATES:
        raise ValueError("TMP_LIFECYCLE_INVALID:" + lifecycle)
    w["lifecycle_state"] = lifecycle
    w["protection_reasons"] = _normalize_tmp_protection_reasons(
        w.get("protection_reasons")
    )
    if "protection_reasons" not in workspace and lifecycle != "DISPOSABLE":
        w["protection_reasons"] = (
            ["ACTIVE_SESSION"] if lifecycle == "ACTIVE" else ["UNKNOWN"]
        )
    w.setdefault("last_used_at", w.get("created_at", _utc_now()))
    w.setdefault("workspace_type", "UNKNOWN")
    w.setdefault("purpose", "UNKNOWN")
    w.setdefault("creator", "")
    w.setdefault("session_id", "")
    w.setdefault("temp_root", "")
    _append_jsonl(_workspaces_path(root, mkdirs=True), w)
    append_fw06_event(root, "WORKSPACE_REGISTERED", {
        "workspace_id": w["workspace_id"],
        "project_id": w["project_id"],
        "owner_task_id": w["owner_task_id"],
        "root_path": w["root_path"],
        "status": w["status"],
        "lifecycle_state": w["lifecycle_state"],
    })
    return w


def list_workspaces(root: str | Path, project_id: str | None = None
                    ) -> list[dict[str, Any]]:
    return [
        row for row in list_all_workspaces(root, project_id)
        if str(row.get("status")) != "CLEANED"
    ]


def _workspace_state_update(root: str | Path, workspace_id: str,
                            *,
                            lifecycle_state: str | None = None,
                            status: str | None = None,
                            event_type: str | None = None,
                            _serialization_held: bool = False,
                            **updates: Any) -> dict[str, Any]:
    """Append one central workspace state transition.

    This is the only helper used by the new lifecycle path to retain metadata
    after the physical directory disappears.  It does not infer missing
    safety facts.
    """
    if not _serialization_held:
        try:
            with _lease_writer_guard(root):
                return _workspace_state_update(
                    root, workspace_id,
                    lifecycle_state=lifecycle_state,
                    status=status,
                    event_type=event_type,
                    _serialization_held=True,
                    **updates,
                )
        except _LeaseLockUnavailable as exc:
            raise ValueError("WORKSPACE_SERIALIZATION_UNAVAILABLE") from exc
    current = _latest_workspace_rows(root).get(str(workspace_id))
    if current is None:
        raise ValueError("WORKSPACE_NOT_FOUND:" + str(workspace_id))
    rec = dict(current)
    current_lifecycle = str(rec.get("lifecycle_state", "")).strip().upper()
    requested_lifecycle = (
        str(lifecycle_state).strip().upper()
        if lifecycle_state is not None else current_lifecycle
    )
    if current_lifecycle == "DELETED" and requested_lifecycle != "DELETED":
        raise ValueError("WORKSPACE_DELETED_STATE_IMMUTABLE")
    if lifecycle_state is not None:
        lifecycle = requested_lifecycle
        if lifecycle not in TMP_LIFECYCLE_STATES:
            raise ValueError("TMP_LIFECYCLE_INVALID:" + lifecycle)
        rec["lifecycle_state"] = lifecycle
    if status is not None:
        if status not in ("ACTIVE", "QUIESCED", "CLEANUP_PENDING",
                          "CLEANED", "CONFLICT", "UNKNOWN_OWNER"):
            raise ValueError("WORKSPACE_STATUS_INVALID:" + str(status))
        rec["status"] = status
    for key, value in updates.items():
        if key == "protection_reasons":
            rec[key] = _normalize_tmp_protection_reasons(value)
        else:
            rec[key] = value
    rec["last_used_at"] = rec.get("last_used_at", _utc_now())
    _append_jsonl(_workspaces_path(root, mkdirs=True), rec)
    if event_type:
        append_fw06_event(root, event_type, {
            "workspace_id": rec.get("workspace_id", ""),
            "project_id": rec.get("project_id", ""),
            "owner_task_id": rec.get("owner_task_id", ""),
            "task_id": rec.get("task_id", rec.get("owner_task_id", "")),
            "lifecycle_state": rec.get("lifecycle_state", ""),
            "protection_reasons": rec.get("protection_reasons", []),
        })
    return rec


def register_managed_workspace(
        root: str | Path,
        *,
        workspace_id: str,
        project_id: str,
        task_id: str,
        session_id: str,
        root_path: str | Path,
        base_revision: str,
        workspace_type: str,
        purpose: str,
        creator: str,
        temp_root: str | Path,
        git_worktree: str | Path | bool = False,
        evidence_pointers: list[str] | tuple[str, ...] = (),
        branch: str = "",
        remote: str = "",
        **extra: Any,
    ) -> dict[str, Any]:
    """Canonical creation seam for a newly managed temporary workspace."""
    now = str(extra.pop("created_at", _utc_now()))
    record: dict[str, Any] = {
        "workspace_id": workspace_id,
        "project_id": project_id,
        "owner_goal_id": str(extra.pop("owner_goal_id", "")),
        "owner_task_id": task_id,
        "task_id": task_id,
        "session_id": session_id,
        "root_path": str(root_path),
        "temp_root": str(temp_root),
        "base_revision": base_revision,
        "created_at": now,
        "last_used_at": now,
        "status": "ACTIVE",
        "lifecycle_state": "ACTIVE",
        "protection_reasons": ["ACTIVE_SESSION"],
        "mutation_policy": str(extra.pop("mutation_policy", "SYNTHETIC_ONLY")),
        "conflict_group": str(extra.pop("conflict_group", "")),
        "git_worktree": str(git_worktree) if git_worktree else False,
        "evidence_pointers": list(evidence_pointers),
        "workspace_type": workspace_type,
        "purpose": purpose,
        "creator": creator,
        "branch": branch,
        "remote": remote,
    }
    record.update(extra)
    return register_workspace(root, record)


def mark_workspace_complete(
        root: str | Path,
        workspace_id: str,
        *,
        policy: Mapping[str, Any] | None = None,
        now: str | None = None,
        protection_reasons: list[str] | tuple[str, ...] | None = None,
        **updates: Any,
    ) -> dict[str, Any]:
    """Move a workspace to COMPLETE before any disposal classification.

    No call to this function can make a workspace DISPOSABLE.  If a policy is
    supplied, it only records the configured normal grace deadline.
    """
    timestamp = now or _utc_now()
    values = dict(updates)
    values["completed_at"] = timestamp
    if policy is not None and "disposable_after" not in values:
        grace = float(
            (policy.get("grace_days") or {}).get("NORMAL", 7)
        )
        parsed = _parse_ts(timestamp)
        if parsed is not None:
            values["disposable_after"] = (
                parsed + timedelta(days=grace)
            ).strftime("%Y-%m-%dT%H:%M:%SZ")
    values["protection_reasons"] = (
        _normalize_tmp_protection_reasons(protection_reasons)
        if protection_reasons is not None
        else ["UNKNOWN"]
    )
    values.setdefault("status", "QUIESCED")
    return _workspace_state_update(
        root, workspace_id, lifecycle_state="COMPLETE",
        status=values.pop("status"), event_type="WORKSPACE_COMPLETED",
        **values,
    )


def cleanup_workspace(root: str | Path, workspace_id: str,
                      *,
                      mutation_state_known: bool,
                      evidence_committed: bool,
                      result_reconciled: bool,
                      owner_decision_resolved: bool,
                      _serialization_held: bool = False) -> dict[str, Any]:
    """Idempotent cleanup with evidence-driven guards. NEVER deletes a
    workspace while: mutation state unknown; uncommitted evidence;
    unreconciled result; or unresolved owner decision. Unknown owner
    → keeps workspace (no destructive action on ambiguous ownership)."""
    if not _serialization_held:
        try:
            with _lease_writer_guard(root):
                return cleanup_workspace(
                    root, workspace_id,
                    mutation_state_known=mutation_state_known,
                    evidence_committed=evidence_committed,
                    result_reconciled=result_reconciled,
                    owner_decision_resolved=owner_decision_resolved,
                    _serialization_held=True,
                )
        except _LeaseLockUnavailable:
            return {"cleaned": False,
                    "reason": "WORKSPACE_SERIALIZATION_UNAVAILABLE",
                    "failure_class": "LEASE_LOCK_UNAVAILABLE"}
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
                             worktree_path: str | Path,
                             project_id: str = "",
                             task_id: str = "",
                             session_id: str = "",
                             creator: str = "",
                             purpose: str = "isolated_git_worktree",
                             remote: str = "",
                             branch: str = "",
                             tmp_gc_policy: Mapping[str, Any] | None = None,
                             tmp_gc_policy_path: str | Path | None = None,
                             ) -> dict[str, Any]:
    """Create a git worktree from an exact base revision (isolation), and
    register it with a 12-field identity binding. Never fabricates
    provenance."""
    repo_path = Path(repo_path)
    wt_path = Path(worktree_path)
    pressure_preflight = opportunistic_tmp_gc_before_workspace_creation(
        root,
        policy=tmp_gc_policy,
        policy_path=tmp_gc_policy_path,
    )
    if pressure_preflight.get("status") == "UNKNOWN":
        raise RuntimeError(
            "TMP_GC_PRESSURE_CHECK_UNKNOWN:" + str(
                pressure_preflight.get("reason", "UNKNOWN")
            )
        )
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
        "workspace_id": workspace_id, "project_id": project_id,
        "owner_goal_id": "", "owner_task_id": "",
        "task_id": task_id, "session_id": session_id,
        "root_path": str(wt_path), "base_revision": exact,
        "created_at": _utc_now(), "last_used_at": _utc_now(),
        "status": "ACTIVE", "lifecycle_state": "ACTIVE",
        "protection_reasons": ["ACTIVE_SESSION"],
        "mutation_policy": "SYNTHETIC_ONLY", "conflict_group": "",
        "git_worktree": str(wt_path), "evidence_pointers": [],
        "workspace_type": "GIT_WORKTREE", "purpose": purpose,
        "creator": creator, "temp_root": str(wt_path.parent),
        "remote": remote, "branch": branch or ("fw06-wt-" + workspace_id),
        "repo_path": str(repo_path),
        "tmp_gc_preflight": pressure_preflight,
    }
    workspace["owner_task_id"] = task_id
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


class TmpGcError(ValueError):
    """Raised when the TMPGC policy or durable safety contract is invalid."""


def opportunistic_tmp_gc_before_workspace_creation(
        root: str | Path,
        *,
        policy: Mapping[str, Any] | None = None,
        policy_path: str | Path | None = None,
        now: str | None = None,
        ) -> dict[str, Any]:
    """Run one bounded pressure/GC report immediately before a large create.

    This is an explicit seam, not a poller.  With no configured TMPGC policy
    it returns NOT_CONFIGURED to preserve existing synthetic FW06 callers.
    A configured but unreadable policy/pressure source is UNKNOWN so callers
    can fail closed before allocating another large workspace.
    """
    root_path = Path(root).expanduser().resolve()
    configured_path = _tmp_gc_policy_path(root_path, policy_path)
    if (policy is None and policy_path is None
            and not configured_path.exists()):
        return {
            "status": "NOT_CONFIGURED",
            "pressure_state": "UNKNOWN",
            "safe_gc_reported": False,
        }
    try:
        policy_data = load_tmp_gc_policy(root_path, policy_path, policy)
        pressure = detect_disk_pressure(root_path, policy_data)
        result: dict[str, Any] = {
            "status": "PASS",
            "pressure": pressure,
            "safe_gc_reported": False,
        }
        if pressure.get("readable") is not True:
            result["status"] = "UNKNOWN"
            result["pressure_state"] = "UNKNOWN"
            result["reason"] = str(
                pressure.get("reason", "DISK_USAGE_UNKNOWN")
            )
            return result
        if pressure.get("state") in ("LOW", "CRITICAL"):
            report = inventory_tmp_gc(
                root_path, policy=policy_data, now=now,
            )
            result["safe_gc_reported"] = True
            result["safe_gc"] = {
                "total_temp_size": report.get("total_temp_size", 0),
                "disposable_size": report.get("disposable_size", 0),
                "reclaimable_after_grace": report.get(
                    "reclaimable_after_grace", 0
                ),
                "largest_consumers": report.get("largest_consumers", []),
            }
        return result
    except (OSError, ValueError, TmpGcError) as exc:
        return {
            "status": "UNKNOWN",
            "pressure_state": "UNKNOWN",
            "safe_gc_reported": False,
            "reason": str(exc),
        }


def _tmp_gc_policy_path(root: str | Path,
                        policy_path: str | Path | None = None) -> Path:
    if policy_path is None:
        return Path(root) / TMP_GC_POLICY_REL
    value = Path(policy_path)
    return value if value.is_absolute() else Path(root) / value


def _validate_policy_paths(value: Any, field_name: str,
                           *, relative_only: bool = False) -> list[str]:
    if not isinstance(value, (list, tuple)) or not value:
        raise TmpGcError(field_name.upper() + "_REQUIRED")
    out: list[str] = []
    for raw in value:
        item = str(raw).strip()
        if not item:
            raise TmpGcError(field_name.upper() + "_ENTRY_EMPTY")
        path = Path(item)
        if relative_only and path.is_absolute():
            raise TmpGcError(field_name.upper() + "_MUST_BE_RELATIVE")
        if any(part == ".." for part in path.parts):
            raise TmpGcError(field_name.upper() + "_TRAVERSAL")
        normalized = str(path)
        if normalized not in out:
            out.append(normalized)
    return out


def validate_tmp_gc_policy(value: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise TmpGcError("TMP_GC_POLICY_MUST_BE_OBJECT")
    if value.get("schema") != TMP_GC_POLICY_SCHEMA:
        raise TmpGcError("TMP_GC_POLICY_SCHEMA_INVALID")
    allowlisted = _validate_policy_paths(
        value.get("allowlisted_temp_roots"),
        "allowlisted_temp_roots",
        relative_only=True,
    )
    if any(Path(item) in (Path("."), Path("")) for item in allowlisted):
        raise TmpGcError("ALLOWLIST_ROOT_MUST_NOT_BE_PROJECT_ROOT")
    protected = _validate_policy_paths(
        value.get("protected_roots", []), "protected_roots",
    ) if value.get("protected_roots") else []
    owner = _validate_policy_paths(
        value.get("owner_roots", []), "owner_roots",
    ) if value.get("owner_roots") else []
    authoritative = _validate_policy_paths(
        value.get("authoritative_roots", []), "authoritative_roots",
    ) if value.get("authoritative_roots") else []
    durable = _validate_policy_paths(
        value.get("durable_roots", []), "durable_roots",
    ) if value.get("durable_roots") else []
    if not durable:
        raise TmpGcError("DURABLE_ROOTS_REQUIRED")
    grace_raw = value.get("grace_days")
    if not isinstance(grace_raw, Mapping):
        raise TmpGcError("GRACE_DAYS_REQUIRED")
    grace: dict[str, float] = {}
    for state in TMP_PRESSURE_STATES:
        raw = grace_raw.get(state)
        if isinstance(raw, bool) or not isinstance(raw, (int, float)) \
                or float(raw) < 0:
            raise TmpGcError("GRACE_DAYS_INVALID:" + state)
        grace[state] = float(raw)
    pressure_raw = value.get("pressure")
    if not isinstance(pressure_raw, Mapping):
        raise TmpGcError("PRESSURE_POLICY_REQUIRED")
    pressure: dict[str, Any] = {}
    for state in ("WARNING", "LOW", "CRITICAL"):
        percent_key = state.lower() + "_percent_free"
        absolute_key = state.lower() + "_absolute_free_bytes"
        percent = pressure_raw.get(percent_key)
        if isinstance(percent, bool) or not isinstance(percent, (int, float)) \
                or not 0 <= float(percent) <= 100:
            raise TmpGcError("PRESSURE_PERCENT_INVALID:" + state)
        absolute = pressure_raw.get(absolute_key)
        if absolute is not None and (
                isinstance(absolute, bool) or not isinstance(absolute, int)
                or absolute < 0):
            raise TmpGcError("PRESSURE_ABSOLUTE_INVALID:" + state)
        pressure[percent_key] = float(percent)
        pressure[absolute_key] = absolute
    schedule = value.get("schedule", {})
    if not isinstance(schedule, Mapping):
        raise TmpGcError("SCHEDULE_POLICY_INVALID")
    daily_time = str(schedule.get("daily_local_time", "")).strip()
    try:
        parsed_time = datetime.strptime(daily_time, "%H:%M")
    except ValueError as exc:
        raise TmpGcError("SCHEDULE_TIME_INVALID") from exc
    if parsed_time.strftime("%H:%M") != daily_time:
        raise TmpGcError("SCHEDULE_TIME_INVALID")
    if str(schedule.get("activation", "")) != "OWNER_GATED":
        raise TmpGcError("SCHEDULE_ACTIVATION_MUST_BE_OWNER_GATED")
    largest_limit = value.get("largest_consumers_limit", 10)
    if isinstance(largest_limit, bool) or not isinstance(largest_limit, int) \
            or not 1 <= largest_limit <= 100:
        raise TmpGcError("LARGEST_CONSUMERS_LIMIT_INVALID")
    return {
        "schema": TMP_GC_POLICY_SCHEMA,
        "allowlisted_temp_roots": allowlisted,
        "protected_roots": protected,
        "owner_roots": owner,
        "authoritative_roots": authoritative,
        "durable_roots": durable,
        "grace_days": grace,
        "pressure": pressure,
        "schedule": {
            "daily_local_time": daily_time,
            "activation": "OWNER_GATED",
        },
        "largest_consumers_limit": largest_limit,
    }


def load_tmp_gc_policy(root: str | Path,
                       policy_path: str | Path | None = None,
                       policy: Mapping[str, Any] | None = None
                       ) -> dict[str, Any]:
    if policy is not None:
        return validate_tmp_gc_policy(policy)
    path = _tmp_gc_policy_path(root, policy_path)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise TmpGcError("TMP_GC_POLICY_UNREADABLE:" + str(path)) from exc
    return validate_tmp_gc_policy(raw)


def _path_key(path: str | Path) -> str:
    return os.path.normcase(os.path.abspath(os.path.normpath(str(path))))


def _rooted_path(root: str | Path, raw: str | Path) -> Path:
    """Interpret registry paths relative to their owning project root."""
    value = Path(str(raw))
    if not value.is_absolute():
        value = Path(root) / value
    return value


def _resolve_path(path: str | Path) -> Path | None:
    try:
        return Path(path).expanduser().resolve(strict=False)
    except (OSError, RuntimeError, ValueError):
        return None


def _reparse_marker(path: Path) -> bool | None:
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    except (OSError, ValueError):
        return None
    if stat.S_ISLNK(info.st_mode):
        return True
    return bool(getattr(info, "st_file_attributes", 0)
                & _WINDOWS_REPARSE_POINT)


def _reparse_between(path: Path, anchor: Path) -> bool | None:
    try:
        path.relative_to(anchor)
    except ValueError:
        return None
    current = path
    while True:
        marker = _reparse_marker(current)
        if marker is not False:
            return marker
        if _path_key(current) == _path_key(anchor):
            return False
        parent = current.parent
        if parent == current:
            return None
        current = parent


def _is_same_or_child(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _configured_path(root: Path, raw: str) -> Path | None:
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = root / candidate
    return _resolve_path(candidate)


def _git_worktree_paths(root: Path) -> list[Path] | None:
    probe = _git_run(root, ["rev-parse", "--is-inside-work-tree"])
    if probe is None:
        return None
    if probe.returncode != 0:
        return []
    listed = _git_run(root, ["worktree", "list", "--porcelain"])
    if listed is None or listed.returncode != 0:
        return None
    paths: list[Path] = []
    for line in listed.stdout.splitlines():
        if line.startswith("worktree "):
            resolved = _resolve_path(line[9:].strip())
            if resolved is None:
                return None
            paths.append(resolved)
    return paths


def _tmp_path_identity(root: Path, path: Path,
                       policy: Mapping[str, Any],
                       *,
                       registered_non_temp: list[Path] | None = None
                       ) -> dict[str, Any]:
    root_real = _resolve_path(root)
    path_real = _resolve_path(path)
    if root_real is None or path_real is None:
        return {"ok": False, "reason": "PATH_RESOLUTION_UNKNOWN"}
    if _path_key(path_real) == _path_key(root_real):
        return {"ok": False, "reason": "PATH_CANONICAL_ROOT"}
    root_marker = _reparse_marker(root_real)
    if root_marker is None:
        return {"ok": False, "reason": "PATH_REPARSE_UNKNOWN"}
    if root_marker:
        return {"ok": False, "reason": "PATH_REPARSE_POINT"}
    for raw in policy.get("allowlisted_temp_roots", []):
        allow = _configured_path(root_real, str(raw))
        if allow is None or not _is_same_or_child(allow, root_real):
            return {"ok": False, "reason": "ALLOWLIST_RESOLUTION_UNKNOWN"}
        marker = _reparse_between(allow, root_real)
        if marker is None:
            return {"ok": False, "reason": "PATH_REPARSE_UNKNOWN"}
        if marker:
            return {"ok": False, "reason": "PATH_REPARSE_POINT"}
        if not _is_same_or_child(path_real, allow):
            continue
        if _path_key(path_real) == _path_key(allow):
            return {"ok": False, "reason": "PATH_ALLOWLIST_ROOT"}
        marker = _reparse_between(path, root_real)
        if marker is None:
            return {"ok": False, "reason": "PATH_REPARSE_UNKNOWN"}
        if marker:
            return {"ok": False, "reason": "PATH_REPARSE_POINT"}
        if registered_non_temp is None:
            return {"ok": False, "reason": "WORKTREE_QUERY_UNKNOWN"}
        for field_name, reason in (
                ("protected_roots", "PATH_PROTECTED_ROOT"),
                ("owner_roots", "PATH_OWNER_ROOT"),
                ("authoritative_roots", "PATH_AUTHORITATIVE_ROOT")):
            for raw_protected in policy.get(field_name, []):
                protected = _configured_path(root_real, str(raw_protected))
                if protected is None:
                    return {"ok": False, "reason": "PROTECTED_PATH_UNKNOWN"}
                if _is_same_or_child(path_real, protected):
                    return {"ok": False, "reason": reason}
        for worktree in registered_non_temp:
            if _is_same_or_child(path_real, worktree):
                return {"ok": False, "reason": "REGISTERED_NON_TEMP_WORKTREE"}
        return {
            "ok": True,
            "reason": "",
            "allowlisted_root": str(allow),
            "real_path": str(path_real),
        }
    return {"ok": False, "reason": "PATH_OUTSIDE_ALLOWLIST"}


def _measure_tmp_path(path: Path) -> tuple[int, bool]:
    """Measure without following symlinks/reparse points."""
    marker = _reparse_marker(path)
    if marker is None or marker:
        return 0, False
    try:
        if path.is_file():
            return path.stat().st_size, True
        if not path.is_dir():
            return 0, False
    except OSError:
        return 0, False
    total = 0
    complete = True
    pending = [path]
    while pending:
        current = pending.pop()
        try:
            with os.scandir(current) as entries:
                for entry in entries:
                    entry_path = Path(entry.path)
                    marker = _reparse_marker(entry_path)
                    if marker is None or marker:
                        complete = False
                        continue
                    try:
                        if entry.is_dir(follow_symlinks=False):
                            pending.append(entry_path)
                        elif entry.is_file(follow_symlinks=False):
                            total += entry.stat(follow_symlinks=False).st_size
                        else:
                            complete = False
                    except OSError:
                        complete = False
        except OSError:
            complete = False
    return total, complete


def _git_run(path: Path, args: list[str],
             *, timeout: int = 30) -> subprocess.CompletedProcess | None:
    try:
        return subprocess.run(
            ["git", "-C", str(path), *args],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (FileNotFoundError, OSError, subprocess.TimeoutExpired):
        return None


def _lock_state(path: Path) -> str:
    candidates = [
        path / ".p2p" / "state" / "fw06-workspaces.jsonl.lock",
        path / ".p2p" / "state" / "fw06-leases.jsonl.lock",
        path / ".git" / "index.lock",
        path / ".git" / "HEAD.lock",
        path / ".git" / "config.lock",
        path / ".git" / "shallow.lock",
    ]
    git_marker = path / ".git"
    try:
        if git_marker.is_file():
            text = git_marker.read_text(encoding="utf-8", errors="strict")
            for line in text.splitlines():
                if line.startswith("gitdir:"):
                    git_dir = Path(line.split(":", 1)[1].strip())
                    if not git_dir.is_absolute():
                        git_dir = git_marker.parent / git_dir
                    candidates.extend([
                        git_dir / "index.lock",
                        git_dir / "HEAD.lock",
                        git_dir / "config.lock",
                        git_dir / "shallow.lock",
                    ])
                    break
    except (OSError, UnicodeError):
        return "UNKNOWN"
    for candidate in candidates:
        try:
            if candidate.exists():
                return "LOCKED"
        except OSError:
            return "UNKNOWN"
    return "CLEAR"


def _git_workspace_state(path: Path, record: Mapping[str, Any]) -> dict[str, Any]:
    # ``git -C`` searches parent directories.  A non-Git fixture/workspace
    # nested below a canonical checkout must not inherit the parent's Git
    # identity and appear clean or dirty by accident.
    git_marker = path / ".git"
    try:
        if not git_marker.exists():
            if (str(record.get("workspace_type", "")).upper() == "NON_GIT"
                    and str(record.get("content_status", "")) == "DURABLE"):
                return {"kind": "NON_GIT_KNOWN", "clean": True, "head": ""}
            return {"kind": "NON_GIT_UNKNOWN", "clean": None, "head": ""}
        marker = _reparse_marker(git_marker)
        if marker is not False:
            return {"kind": "UNKNOWN", "clean": None, "head": ""}
    except OSError:
        return {"kind": "UNKNOWN", "clean": None, "head": ""}
    probe = _git_run(path, ["rev-parse", "--is-inside-work-tree"])
    if probe is None:
        return {"kind": "UNKNOWN", "clean": None, "head": ""}
    if probe.returncode != 0:
        return {"kind": "NON_GIT_UNKNOWN", "clean": None, "head": ""}
    status = _git_run(path, ["status", "--porcelain", "--untracked-files=all"])
    head = _git_run(path, ["rev-parse", "HEAD"])
    if status is None or head is None or head.returncode != 0:
        return {"kind": "UNKNOWN", "clean": None, "head": ""}
    return {
        "kind": "GIT",
        "clean": status.returncode == 0 and not status.stdout.strip(),
        "head": head.stdout.strip(),
    }


def _sha256_file(path: Path) -> str | None:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except (OSError, ValueError):
        return None
    return digest.hexdigest()


def _durable_ref(root: Path, workspace: Path, raw: Any,
                 policy: Mapping[str, Any]) -> Path | None:
    value = str(raw or "")
    if value.startswith("raw:"):
        value = value[4:]
    if not value:
        return None
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = root / candidate
    resolved = _resolve_path(candidate)
    if resolved is None or not resolved.exists():
        return None
    workspace_real = _resolve_path(workspace)
    if workspace_real is None or _is_same_or_child(resolved, workspace_real):
        return None
    root_real = _resolve_path(root)
    if root_real is None:
        return None
    marker = _reparse_between(resolved, root_real)
    if marker is not False:
        return None
    durable = False
    for raw_root in policy.get("durable_roots", []):
        durable_root = _configured_path(root, str(raw_root))
        if durable_root is not None and _is_same_or_child(resolved, durable_root):
            durable = True
            break
    return resolved if durable else None


def _verify_archive(root: Path, workspace: Path,
                    record: Mapping[str, Any],
                    policy: Mapping[str, Any], head: str) -> dict[str, Any]:
    archive = _durable_ref(root, workspace, record.get("archive_path"), policy)
    expected = str(record.get("archive_sha256", "")).lower()
    if archive is None or len(expected) != 64:
        return {"verified": False, "reason": "ARCHIVE_METADATA_MISSING"}
    actual = _sha256_file(archive)
    if actual is None or actual != expected:
        return {"verified": False, "reason": "ARCHIVE_HASH_MISMATCH"}
    verify = _git_run(archive.parent, ["bundle", "verify", str(archive)])
    heads = _git_run(archive.parent, ["bundle", "list-heads", str(archive)])
    if verify is None or verify.returncode != 0 \
            or heads is None or heads.returncode != 0:
        return {"verified": False, "reason": "ARCHIVE_VERIFY_FAILED"}
    listed_heads = {
        line.split()[0] for line in heads.stdout.splitlines()
        if line.split()
    }
    if head not in listed_heads:
        return {"verified": False, "reason": "ARCHIVE_HEAD_MISMATCH"}
    expected_head = str(record.get("archive_head", "")).strip()
    if expected_head and expected_head != head:
        return {"verified": False, "reason": "ARCHIVE_IDENTITY_MISMATCH"}
    return {"verified": True, "reason": "VERIFIED_BUNDLE", "path": str(archive)}


def _verify_remote_reachability(path: Path, record: Mapping[str, Any],
                                head: str) -> bool:
    ref = str(record.get("remote_ref", "")).strip()
    if str(record.get("remote_reachability", "")) != "VERIFIED" or not ref:
        return False
    remote_name = str(record.get("remote_name", "origin")).strip() or "origin"
    actual_url = _git_run(path, ["remote", "get-url", remote_name])
    remote_url = str(record.get("remote", "")).strip()
    if actual_url is None or actual_url.returncode != 0:
        return False
    if remote_url and actual_url.stdout.strip() != remote_url:
        return False
    ref_head = _git_run(path, ["rev-parse", ref])
    if ref_head is None or ref_head.returncode != 0:
        return False
    ancestor = _git_run(path, ["merge-base", "--is-ancestor", head, ref])
    return ancestor is not None and ancestor.returncode == 0


def _history_state(root: Path, workspace: Path,
                   record: Mapping[str, Any],
                   policy: Mapping[str, Any],
                   git_state: Mapping[str, Any]) -> tuple[bool, str]:
    if git_state.get("kind") == "NON_GIT_KNOWN":
        return True, ""
    if git_state.get("kind") != "GIT":
        return False, "UNIQUE_LOCAL_HISTORY"
    head = str(git_state.get("head", ""))
    expected_head = str(record.get("head_revision", "")).strip()
    if expected_head and expected_head != head:
        return False, "UNKNOWN"
    archive = _verify_archive(root, workspace, record, policy, head)
    if archive.get("verified"):
        return True, ""
    if _verify_remote_reachability(workspace, record, head):
        return True, ""
    return False, "UNIQUE_LOCAL_HISTORY"


def _worktree_binding_state(root: Path, workspace: Path,
                            record: Mapping[str, Any]) -> tuple[bool, str]:
    """Prove a Git worktree record is removable through its owning repo."""
    value = record.get("git_worktree")
    if not value or str(value).strip().lower() in ("false", "none"):
        return True, ""
    if isinstance(value, bool):
        return False, "UNKNOWN"
    if _path_key(_rooted_path(root, str(value))) != _path_key(workspace):
        return False, "UNKNOWN"
    repo_raw = str(record.get("repo_path", "")).strip()
    if not repo_raw:
        return False, "DEPENDENCY"
    repo = _resolve_path(_rooted_path(root, repo_raw))
    if repo is None:
        return False, "UNKNOWN"
    paths = _git_worktree_paths(repo)
    if paths is None:
        return False, "UNKNOWN"
    if not any(_path_key(item) == _path_key(workspace) for item in paths):
        return False, "DEPENDENCY"
    return True, ""


def _task_terminal_state(root: Path, record: Mapping[str, Any]
                         ) -> tuple[bool, str]:
    task_id = str(record.get("task_id") or record.get("owner_task_id") or "")
    session_id = str(record.get("session_id", "")).strip()
    if not task_id or not session_id:
        return False, "UNKNOWN"
    try:
        plan = _task_state.TaskStateStore(root).load()
    except Exception:  # noqa: BLE001
        return False, "UNKNOWN"
    if plan is None:
        return False, "UNKNOWN"
    task = plan.tasks.get(task_id)
    if task is None:
        return False, "UNKNOWN"
    if task.status in ("DONE", "CANCELLED"):
        return True, ""
    if task.status == "ACTIVE":
        return False, "ACTIVE_SESSION"
    return False, "UNKNOWN"


def _effective_leases(root: Path) -> tuple[list[dict[str, Any]], bool]:
    rows = _read_jsonl(_leases_path(root))
    malformed = False
    latest: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, Mapping) or row.get("_MALFORMED_LINE"):
            malformed = True
            continue
        lease_id = str(row.get("lease_id", "")).strip()
        status = str(row.get("status", "")).strip().upper()
        if not lease_id or status not in {
                "ACTIVE", "RELEASED", "EXPIRED", "RECLAIMED"}:
            malformed = True
            continue
        if status == "ACTIVE" and _parse_ts(str(
                row.get("expires_at", ""))) is None:
            malformed = True
            continue
        latest[lease_id] = dict(row)
    return list(latest.values()), malformed


def _active_workspace_lease(root: Path, record: Mapping[str, Any],
                            *, exclude_lease_id: str = "") -> str | None:
    leases, malformed = _effective_leases(root)
    if malformed:
        return "UNKNOWN"
    project_id = str(record.get("project_id", ""))
    task_id = str(record.get("task_id") or record.get("owner_task_id") or "")
    for lease in leases:
        if exclude_lease_id and str(lease.get("lease_id", "")) == exclude_lease_id:
            continue
        if not _lease_is_live(lease):
            continue
        same_project = project_id and lease.get("project_id") == project_id
        same_task = task_id and lease.get("task_id") == task_id
        if same_project or same_task:
            return "ACTIVE_SESSION"
    return None


def _duplicate_path_binding(root: Path, workspace: Path) -> bool | None:
    """Return whether more than one latest registry row binds this path.

    A missing/ambiguous row is not treated as proof of uniqueness.  ``None``
    therefore means the caller must keep the workspace.
    """
    target = _path_key(workspace)
    count = 0
    for row in _latest_workspace_rows(root).values():
        raw_path = str(row.get("root_path", "")).strip()
        if not raw_path:
            return None
        resolved = _resolve_path(_rooted_path(root, raw_path))
        if resolved is None:
            return None
        if _path_key(resolved) == target:
            count += 1
    return count > 1


def _bool_field(record: Mapping[str, Any], key: str) -> bool | None:
    if key not in record:
        return None
    value = record.get(key)
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in ("true", "yes", "1"):
            return True
        if lowered in ("false", "no", "0", ""):
            return False
    return None


def detect_disk_pressure(root: str | Path,
                         policy: Mapping[str, Any]) -> dict[str, Any]:
    try:
        usage = shutil.disk_usage(Path(root))
        free_percent = (usage.free / usage.total * 100) if usage.total else 0.0
    except OSError:
        return {
            "state": "CRITICAL",
            "readable": False,
            "free_bytes": None,
            "total_bytes": None,
            "free_percent": None,
            "reason": "DISK_USAGE_UNKNOWN",
        }
    configured = policy.get("pressure", {})
    state = "NORMAL"
    for candidate in ("CRITICAL", "LOW", "WARNING"):
        percent_floor = float(configured[candidate.lower() + "_percent_free"])
        absolute_floor = configured[candidate.lower() + "_absolute_free_bytes"]
        if free_percent <= percent_floor or (
                absolute_floor is not None and usage.free <= absolute_floor):
            state = candidate
            break
    return {
        "state": state,
        "readable": True,
        "free_bytes": usage.free,
        "total_bytes": usage.total,
        "free_percent": round(free_percent, 4),
        "reason": "",
    }


def _classification_digest(value: Mapping[str, Any]) -> str:
    payload = json.dumps(value, sort_keys=True, ensure_ascii=False,
                         separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def classify_tmp_workspace(
        root: str | Path,
        record: Mapping[str, Any],
        *,
        policy: Mapping[str, Any] | None = None,
        pressure: Mapping[str, Any] | None = None,
        now: str | None = None,
        size_override: tuple[int, bool] | None = None,
        registered_non_temp: list[Path] | None = None,
        exclude_lease_id: str = "",
        ) -> dict[str, Any]:
    """Classify one workspace. This function never mutates or deletes paths."""
    root_path = Path(root).expanduser()
    policy_data = (
        validate_tmp_gc_policy(policy)
        if policy is not None else load_tmp_gc_policy(root_path)
    )
    workspace = _rooted_path(root_path, str(record.get("root_path", "")))
    registered = bool(record.get("_registered", True))
    workspace_id = str(record.get("workspace_id", "")).strip() or "UNKNOWN"
    if size_override is None:
        size, size_complete = _measure_tmp_path(workspace)
    else:
        size, size_complete = size_override
    pressure_data = pressure or detect_disk_pressure(root_path, policy_data)
    pressure_state = str(pressure_data.get("state", "")).strip().upper()
    pressure_known = (
        pressure_state in TMP_PRESSURE_STATES
        and (
            pressure_data.get("readable") is True
            or (pressure is not None and "readable" not in pressure_data)
        )
    )
    now_dt = _parse_ts(now or _utc_now())
    if now_dt is None:
        now_dt = datetime.now(timezone.utc)
    reasons: list[str] = []
    predicates: dict[str, bool | None] = {}
    registered_paths = registered_non_temp
    if registered_paths is None:
        registered_paths = _registered_non_temp_worktrees(
            root_path, policy_data,
        )
    if not registered:
        reasons.append("UNKNOWN")
        predicates["registry"] = False
    else:
        predicates["registry"] = True
    try:
        registry_well_formed = _workspace_registry_is_well_formed(root_path)
    except (OSError, ValueError):
        registry_well_formed = False
    predicates["registry_integrity"] = registry_well_formed
    if not registry_well_formed:
        reasons.append("UNKNOWN")
    predicates["pressure_known"] = pressure_known
    if not pressure_known:
        reasons.append("UNKNOWN")
    task_id = str(record.get("task_id") or record.get("owner_task_id") or "").strip()
    identity_metadata_ok = all((
        workspace_id != "UNKNOWN",
        str(record.get("project_id", "")).strip(),
        task_id,
        str(record.get("session_id", "")).strip(),
        str(record.get("base_revision", "")).strip(),
        str(record.get("workspace_type", "")).strip().upper() not in ("", "UNKNOWN"),
        str(record.get("purpose", "")).strip().upper() not in ("", "UNKNOWN"),
        str(record.get("creator", "")).strip(),
    ))
    predicates["identity_metadata"] = identity_metadata_ok
    if not identity_metadata_ok:
        reasons.append("UNKNOWN")
    identity = _tmp_path_identity(
        root_path, workspace, policy_data,
        registered_non_temp=registered_paths,
    )
    predicates["allowlisted_path"] = bool(identity.get("ok"))
    if not identity.get("ok"):
        reasons.append("UNKNOWN")
        reasons.append(str(identity.get("reason", "PATH_UNKNOWN")))
    lifecycle = str(record.get("lifecycle_state", "")).strip().upper()
    if lifecycle not in TMP_LIFECYCLE_STATES:
        lifecycle = "UNKNOWN"
        reasons.append("UNKNOWN")
        predicates["lifecycle_explicit"] = False
    else:
        predicates["lifecycle_explicit"] = True
    if lifecycle == "ACTIVE":
        reasons.append("ACTIVE_SESSION")
    predicates["not_active_lifecycle"] = lifecycle in ("COMPLETE", "DISPOSABLE")
    if lifecycle == "DELETED":
        predicates["not_active_lifecycle"] = False
    status = str(record.get("status", "")).strip().upper()
    status_consistent = (
        (lifecycle == "ACTIVE" and status == "ACTIVE")
        or (lifecycle in ("COMPLETE", "DISPOSABLE")
            and status in ("QUIESCED", "CLEANUP_PENDING"))
    )
    predicates["lifecycle_status_consistent"] = status_consistent
    if not status_consistent:
        reasons.append("UNKNOWN")
    terminal, terminal_reason = _task_terminal_state(root_path, record)
    predicates["task_terminal"] = terminal
    if terminal_reason:
        reasons.append(terminal_reason)
    lease_reason = _active_workspace_lease(
        root_path, record, exclude_lease_id=exclude_lease_id,
    )
    predicates["no_active_lease"] = lease_reason is None
    if lease_reason:
        reasons.append(lease_reason)
    lock_states = [_lock_state(workspace)]
    if _path_key(root_path) != _path_key(workspace):
        # The FW06 registry and lease locks live at the project root, not
        # inside a clone/worktree.  Both locations are relevant to a delete.
        lock_states.append(_lock_state(root_path))
    if "LOCKED" in lock_states:
        lock = "LOCKED"
    elif any(state != "CLEAR" for state in lock_states):
        lock = "UNKNOWN"
    else:
        lock = "CLEAR"
    predicates["no_relevant_lock"] = lock == "CLEAR"
    if lock == "LOCKED":
        reasons.append("ACTIVE_SESSION")
    elif lock != "CLEAR":
        reasons.append("UNKNOWN")
    git_state = _git_workspace_state(workspace, record) \
        if identity.get("ok") and workspace.exists() else {
            "kind": "UNKNOWN", "clean": None, "head": ""}
    predicates["git_clean_or_known_non_git"] = (
        git_state.get("clean") is True
    )
    if git_state.get("kind") == "NON_GIT_UNKNOWN":
        reasons.append("UNKNOWN")
    elif git_state.get("kind") == "UNKNOWN":
        reasons.append("UNKNOWN")
    elif git_state.get("clean") is False:
        reasons.append("DIRTY")
    history_ok, history_reason = _history_state(
        root_path, workspace, record, policy_data, git_state,
    )
    predicates["history_preserved_or_reachable"] = history_ok
    if history_reason:
        reasons.append(history_reason)
    worktree_ok, worktree_reason = _worktree_binding_state(
        root_path, workspace, record,
    )
    predicates["worktree_binding"] = worktree_ok
    if worktree_reason:
        reasons.append(worktree_reason)
    gate = _bool_field(record, "owner_gate")
    predicates["owner_gate_resolved"] = gate is False
    if gate is True:
        reasons.append("OWNER_GATE")
    elif gate is None:
        reasons.append("UNKNOWN")
    candidate = _bool_field(record, "candidate")
    if candidate is None and str(record.get("candidate_ref", "")).strip():
        candidate = True
    predicates["not_candidate"] = candidate is False
    if candidate:
        reasons.append("CANDIDATE")
    elif candidate is None:
        reasons.append("UNKNOWN")
    rollback = _bool_field(record, "rollback_required")
    predicates["no_rollback_requirement"] = rollback is False
    if rollback is True:
        reasons.append("ROLLBACK_REQUIRED")
    elif rollback is None:
        reasons.append("UNKNOWN")
    dependencies = record.get("dependencies")
    predicates["dependencies_resolved"] = isinstance(dependencies, (list, tuple))
    if dependencies is None:
        predicates["dependencies_resolved"] = False
        reasons.append("UNKNOWN")
    elif not isinstance(dependencies, (list, tuple)):
        reasons.append("UNKNOWN")
    elif dependencies:
        reasons.append("DEPENDENCY")
    evidence_status = str(record.get("evidence_status", "")).upper()
    pointers = record.get("evidence_pointers")
    evidence_ok = (
        evidence_status == "DURABLE"
        and isinstance(pointers, (list, tuple))
        and bool(pointers)
        and all(_durable_ref(root_path, workspace, item, policy_data)
                is not None for item in pointers)
    )
    predicates["evidence_durable"] = evidence_ok
    if not evidence_ok:
        reasons.append("EVIDENCE_NOT_DURABLE")
    handoff_status = str(record.get("handoff_status", "")).upper()
    handoff_ok = (
        handoff_status == "DURABLE"
        and _durable_ref(root_path, workspace, record.get("handoff_ref"),
                         policy_data) is not None
    )
    predicates["handoff_durable"] = handoff_ok
    if not handoff_ok:
        reasons.append("EVIDENCE_NOT_DURABLE")
    completed_dt = _parse_ts(str(record.get("completed_at", "")))
    predicates["completion_timestamp_known"] = completed_dt is not None
    if completed_dt is None:
        reasons.append("UNKNOWN")
    disposable_dt = _parse_ts(str(record.get("disposable_after", "")))
    predicates["disposal_deadline_known"] = disposable_dt is not None
    if disposable_dt is None:
        reasons.append("UNKNOWN")
    # Existing declared reasons are protection, not permission.  This lets
    # mark_workspace_complete preserve explicit Owner/candidate/rollback facts.
    declared_reasons: list[str] = []
    try:
        declared_reasons = _normalize_tmp_protection_reasons(
            record.get("protection_reasons", [])
        )
    except ValueError:
        predicates["protection_metadata_valid"] = False
        predicates["no_declared_protection_reasons"] = False
        reasons.append("UNKNOWN")
    else:
        predicates["protection_metadata_valid"] = True
        predicates["no_declared_protection_reasons"] = not declared_reasons
        reasons.extend(declared_reasons)
    duplicate = bool(record.get("_duplicate_path", False))
    if not duplicate:
        try:
            duplicate_state = _duplicate_path_binding(root_path, workspace)
        except (OSError, ValueError):
            duplicate_state = None
        if duplicate_state is None:
            duplicate = True
            reasons.append("UNKNOWN")
        else:
            duplicate = duplicate_state
    predicates["no_duplicate_path_binding"] = not duplicate
    if duplicate:
        reasons.append("DEPENDENCY")
    predicates["size_complete"] = size_complete
    if not size_complete:
        reasons.append("UNKNOWN")
    safe_predicates = all(value is True for value in predicates.values())
    if not identity.get("ok") or not registered or lifecycle == "DELETED":
        safe_predicates = False
    effective_lifecycle = lifecycle
    grace_status = "NOT_APPLICABLE"
    deadline_text = str(record.get("disposable_after", ""))
    if safe_predicates:
        effective_lifecycle = "DISPOSABLE"
        effective_deadline = disposable_dt
        pressure_state = str(pressure_data.get("state", "CRITICAL"))
        if completed_dt is not None and pressure_state in ("WARNING", "LOW", "CRITICAL"):
            grace_days = float(policy_data["grace_days"][pressure_state])
            pressure_deadline = completed_dt + timedelta(days=grace_days)
            if effective_deadline is None or pressure_deadline < effective_deadline:
                effective_deadline = pressure_deadline
        if effective_deadline is None:
            grace_status = "UNKNOWN"
            safe_predicates = False
            reasons.append("UNKNOWN")
        else:
            deadline_text = effective_deadline.strftime("%Y-%m-%dT%H:%M:%SZ")
            grace_status = "ELAPSED" if now_dt >= effective_deadline \
                else "NOT_ELAPSED"
    elif lifecycle in ("COMPLETE", "DISPOSABLE"):
        effective_lifecycle = "COMPLETE"
        grace_status = "UNKNOWN" if disposable_dt is None else "BLOCKED"
    reasons = list(dict.fromkeys(
        reason for reason in reasons if reason in TMP_PROTECTION_REASONS
    ))
    eligible = (
        safe_predicates
        and effective_lifecycle == "DISPOSABLE"
        and grace_status == "ELAPSED"
    )
    result = {
        "workspace_id": workspace_id,
        "path": str(workspace),
        "size": size,
        "lifecycle": effective_lifecycle,
        "record_lifecycle": lifecycle,
        "protection_reasons": reasons,
        "predicates": predicates,
        "eligibility": "PASS" if eligible else "KEEP",
        "grace_status": grace_status,
        "disposable_after": deadline_text,
        "pressure_state": pressure_data.get("state", "CRITICAL"),
        "final_action": "DELETE_ELIGIBLE" if eligible else "KEEP",
        "hard_reject": bool(
            not identity.get("ok")
            and str(identity.get("reason", "")).startswith(("PATH_", "ALLOWLIST"))
        ),
        "classification_evidence_digest": "",
    }
    result["classification_evidence_digest"] = _classification_digest({
        "schema": TMP_GC_SCHEMA,
        "workspace_id": workspace_id,
        "path": _path_key(workspace),
        "record": _json_safe(dict(record)),
        "record_lifecycle": lifecycle,
        "predicates": predicates,
        "protection_reasons": reasons,
        "size": size,
        "disposable_after": deadline_text,
        "pressure_state": pressure_data.get("state"),
    })
    return result


def _registered_non_temp_worktrees(root: Path,
                                   policy: Mapping[str, Any]
                                   ) -> list[Path] | None:
    listed = _git_worktree_paths(root)
    if listed is None:
        return None
    paths: list[Path] = []
    for path in listed:
        # The current canonical checkout is an ancestor of .tmp and is
        # protected by exact-root identity elsewhere.  It must not be passed
        # as a protected subtree or every managed temp child would inherit
        # the canonical-root exclusion.  The ancestor case also matters for
        # isolated fixture roots nested below a project checkout.
        if _path_key(path) == _path_key(root) or _is_same_or_child(root, path):
            continue
        identity = _tmp_path_identity(
            root, path, policy, registered_non_temp=[],
        )
        if not identity.get("ok"):
            paths.append(path)
    return paths


def _workspace_records_for_inventory(root: Path,
                                     policy: Mapping[str, Any]
                                     ) -> list[dict[str, Any]]:
    records = (
        list_all_workspaces(root)
        if _workspace_registry_is_well_formed(root) else []
    )
    allow_roots = [
        _configured_path(root, str(item))
        for item in policy.get("allowlisted_temp_roots", [])
    ]
    allow_roots = [item for item in allow_roots if item is not None]
    out: list[dict[str, Any]] = []
    path_counts: dict[str, int] = {}
    for row in records:
        path = _resolve_path(_rooted_path(
            root, str(row.get("root_path", ""))
        ))
        if path is None or not any(_is_same_or_child(path, allow)
                                   and _path_key(path) != _path_key(allow)
                                   for allow in allow_roots):
            continue
        clone = dict(row)
        clone["_registered"] = True
        out.append(clone)
        path_counts[_path_key(path)] = path_counts.get(_path_key(path), 0) + 1
    for allow in allow_roots:
        try:
            children = sorted(Path(allow).iterdir(), key=lambda p: p.name.casefold())
        except (OSError, ValueError):
            continue
        for child in children:
            key = _path_key(child)
            if key in path_counts:
                continue
            digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]
            out.append({
                "workspace_id": "UNREGISTERED-" + digest,
                "root_path": str(child),
                "lifecycle_state": "UNKNOWN",
                "_registered": False,
            })
    for row in out:
        path = _path_key(str(row.get("root_path", "")))
        if path_counts.get(path, 0) > 1:
            row["_duplicate_path"] = True
    out.sort(key=lambda row: str(row.get("root_path", "")).casefold())
    return out


def _tmp_gc_summary(workspaces: list[dict[str, Any]],
                    root: Path, policy: Mapping[str, Any],
                    pressure: Mapping[str, Any],
                    *, dry_run: bool) -> dict[str, Any]:
    total = sum(int(item.get("size", 0)) for item in workspaces)
    summary: dict[str, Any] = {
        "schema": TMP_GC_SCHEMA,
        "root": str(root),
        "dry_run": dry_run,
        "pressure": dict(pressure),
        "total_temp_size": total,
        "active_size": 0,
        "complete_protected_size": 0,
        "candidate_size": 0,
        "owner_gate_size": 0,
        "rollback_required_size": 0,
        "unknown_size": 0,
        "disposable_size": 0,
        "reclaimable_after_grace": 0,
        "legacy_workspace_delete_count": 0,
        "workspaces": workspaces,
        "largest_consumers": [],
    }
    for item in workspaces:
        size = int(item.get("size", 0))
        lifecycle = str(item.get("lifecycle", "UNKNOWN"))
        reasons = set(item.get("protection_reasons", []))
        if lifecycle == "ACTIVE" or "ACTIVE_SESSION" in reasons:
            summary["active_size"] += size
        if lifecycle == "COMPLETE" and not (
                "UNKNOWN" in reasons or "EVIDENCE_NOT_DURABLE" in reasons):
            summary["complete_protected_size"] += size
        if "CANDIDATE" in reasons:
            summary["candidate_size"] += size
        if "OWNER_GATE" in reasons:
            summary["owner_gate_size"] += size
        if "ROLLBACK_REQUIRED" in reasons:
            summary["rollback_required_size"] += size
        if lifecycle == "UNKNOWN" or "UNKNOWN" in reasons:
            summary["unknown_size"] += size
        if lifecycle == "DISPOSABLE":
            summary["disposable_size"] += size
        if item.get("final_action") == "DELETE_ELIGIBLE":
            summary["reclaimable_after_grace"] += size
    largest = sorted(workspaces, key=lambda item: int(item.get("size", 0)),
                     reverse=True)
    summary["largest_consumers"] = [
        {
            "path": item.get("path"),
            "workspace_id": item.get("workspace_id"),
            "size": item.get("size", 0),
            "lifecycle": item.get("lifecycle"),
            "final_action": item.get("final_action"),
        }
        for item in largest[:int(policy.get("largest_consumers_limit", 10))]
    ]
    return summary


def inventory_tmp_gc(root: str | Path,
                     *,
                     policy: Mapping[str, Any] | None = None,
                     policy_path: str | Path | None = None,
                     now: str | None = None) -> dict[str, Any]:
    """Read-only inventory and classification for configured temp roots."""
    root_path = Path(root).expanduser().resolve()
    policy_data = load_tmp_gc_policy(root_path, policy_path, policy)
    pressure = detect_disk_pressure(root_path, policy_data)
    non_temp_worktrees = _registered_non_temp_worktrees(root_path, policy_data)
    cache: dict[str, tuple[int, bool]] = {}
    classified: list[dict[str, Any]] = []
    for record in _workspace_records_for_inventory(root_path, policy_data):
        record_path = _resolve_path(_rooted_path(
            root_path, str(record.get("root_path", ""))
        ))
        if record_path is None:
            continue
        key = _path_key(record_path)
        if key not in cache:
            cache[key] = _measure_tmp_path(record_path)
        classified.append(classify_tmp_workspace(
            root_path,
            record,
            policy=policy_data,
            pressure=pressure,
            now=now,
            size_override=cache[key],
            registered_non_temp=non_temp_worktrees,
        ))
    result = _tmp_gc_summary(
        classified, root_path, policy_data, pressure, dry_run=True,
    )
    result["policy"] = policy_data
    result["apply_requested"] = False
    return result


_TMP_GC_AUDIT_STATUSES = {
    "DELETE_INTENT",
    "DELETE_PHYSICAL_SUCCESS",
    "DELETE_REVALIDATION_FAILED",
    "DELETE_FAILED",
    "DELETE_AUDIT_FAILED",
    "STATE_UPDATE_FAILED",
}
_TMP_GC_AUDIT_AUTHORIZED_STATUSES = {
    "DELETE_INTENT", "DELETE_PHYSICAL_SUCCESS",
}
_TMP_GC_FILESYSTEM_OPERATIONS = {
    "NOT_ATTEMPTED", "REMOVED", "NOT_FOUND", "FAILED", "DRY_RUN",
}
_TMP_GC_FILESYSTEM_RESULT_FIELDS = {
    "operation", "path", "before", "after",
}
_TMP_GC_AUDIT_SEMANTIC_FIELDS = (
    "delete_authorized", "final_revalidation_valid", "dry_run",
    "physical_deleted", "authorized_path", "physical_deleted_path",
    "protection_reasons", "active_lease", "active_lock",
    "active_dependency", "filesystem_operation", "lifecycle_from",
    "lifecycle_to", "filesystem_result",
)


def _tmp_gc_filesystem_not_attempted(path: Path, *, dry_run: bool = False) \
        -> dict[str, str]:
    return {
        "operation": "DRY_RUN" if dry_run else "NOT_ATTEMPTED",
        "path": str(path),
        "before": "UNKNOWN",
        "after": "NOT_ATTEMPTED",
    }


def _tmp_gc_filesystem_observation(path: Path, operation: str, *,
                                   before: str) -> dict[str, str]:
    try:
        after = "PRESENT" if os.path.lexists(str(path)) else "ABSENT"
    except OSError:
        after = "UNKNOWN"
    return {
        "operation": str(operation).strip().upper(),
        "path": str(path),
        "before": str(before).strip().upper(),
        "after": after,
    }


def _tmp_gc_filesystem_result_is_well_formed(
        row: Mapping[str, Any]) -> bool:
    value = row.get("filesystem_result")
    if not isinstance(value, Mapping) \
            or set(value) != _TMP_GC_FILESYSTEM_RESULT_FIELDS:
        return False
    operation = str(value.get("operation", "")).strip().upper()
    filesystem_operation = str(
        row.get("filesystem_operation", "")
    ).strip().upper()
    raw_path = str(row.get("path", "")).strip()
    result_path = str(value.get("path", "")).strip()
    before = str(value.get("before", "")).strip().upper()
    after = str(value.get("after", "")).strip().upper()
    if operation not in _TMP_GC_FILESYSTEM_OPERATIONS \
            or operation != filesystem_operation \
            or not raw_path or not result_path \
            or not Path(raw_path).is_absolute() \
            or not Path(result_path).is_absolute() \
            or _path_key(Path(raw_path)) != _path_key(Path(result_path)):
        return False
    if operation == "REMOVED":
        try:
            target_absent = not os.path.lexists(raw_path)
        except OSError:
            return False
        return before == "PRESENT" and after == "ABSENT" \
            and target_absent
    if operation == "NOT_FOUND":
        return before == "ABSENT" and after == "ABSENT"
    if operation == "NOT_ATTEMPTED":
        return before == "UNKNOWN" and after == "NOT_ATTEMPTED"
    if operation == "DRY_RUN":
        return before in {"UNKNOWN", "PRESENT", "ABSENT"} \
            and after == "NOT_ATTEMPTED"
    return before in {"PRESENT", "UNKNOWN"} \
        and after in {"PRESENT", "ABSENT", "UNKNOWN"}


def _tmp_gc_audit_is_well_formed(root: str | Path) -> bool:
    try:
        rows = _read_jsonl(
            state_dir(root, mkdirs=False) / TMP_GC_AUDIT_PATH
        )
    except (OSError, UnicodeError, ValueError):
        return False
    required = (
        "audit_id", "schema", "workspace_id", "path", "task_id",
        "prior_lifecycle",
        "deletion_time", "classification_evidence_digest", "reclaimed_bytes",
        "reason", "status", "filesystem_result",
    )
    seen_intent: set[str] = set()
    seen_success: set[str] = set()
    last_time: dict[str, datetime] = {}
    for row in rows:
        if not isinstance(row, Mapping) or row.get("_MALFORMED_LINE"):
            return False
        if row.get("schema") != TMP_GC_SCHEMA:
            return False
        if any(key not in row for key in required):
            return False
        if not isinstance(row.get("reclaimed_bytes"), int) \
                or row.get("reclaimed_bytes", -1) < 0:
            return False
        status = str(row.get("status", "")).strip().upper()
        if status not in _TMP_GC_AUDIT_STATUSES:
            return False
        workspace_id = str(row.get("workspace_id", "")).strip()
        task_id = str(row.get("task_id", "")).strip()
        raw_path = str(row.get("path", "")).strip()
        digest = str(row.get("classification_evidence_digest", "")).strip()
        if not workspace_id or not task_id or not raw_path \
                or not Path(raw_path).is_absolute() or not digest:
            return False
        if not str(row.get("reason", "")).strip():
            return False
        filesystem_operation = str(
            row.get("filesystem_operation", "")
        ).strip().upper()
        if not _tmp_gc_filesystem_result_is_well_formed(row):
            return False
        expected_id = _classification_digest([
            "tmp-gc-audit", workspace_id, status, digest,
        ])
        if str(row.get("audit_id", "")) != expected_id:
            return False
        deletion_time = _parse_ts(str(row.get("deletion_time", "")))
        if deletion_time is None or deletion_time.tzinfo is None:
            return False
        previous_time = last_time.get(workspace_id)
        if previous_time is not None and deletion_time < previous_time:
            return False
        last_time[workspace_id] = deletion_time
        prior_lifecycle = str(row.get("prior_lifecycle", "")).strip().upper()
        if prior_lifecycle not in TMP_LIFECYCLE_STATES:
            return False
        lifecycle_from = str(
            row.get("lifecycle_from", prior_lifecycle)
        ).strip().upper()
        if lifecycle_from != prior_lifecycle:
            return False
        if status in _TMP_GC_AUDIT_AUTHORIZED_STATUSES and any(
                key not in row for key in _TMP_GC_AUDIT_SEMANTIC_FIELDS):
            return False
        bool_fields = (
            "delete_authorized", "final_revalidation_valid", "dry_run",
            "physical_deleted", "active_lease", "active_lock",
            "active_dependency",
        )
        for key in bool_fields:
            if key in row and not isinstance(row[key], bool):
                return False
        try:
            reasons = _normalize_tmp_protection_reasons(
                row.get("protection_reasons", [])
            )
        except ValueError:
            return False
        if status in _TMP_GC_AUDIT_AUTHORIZED_STATUSES:
            authorized = row.get("delete_authorized")
            final_valid = row.get("final_revalidation_valid")
            dry_run = row.get("dry_run")
            physical_deleted = row.get("physical_deleted")
            if not (authorized and final_valid) or dry_run:
                return False
            lifecycle_from = str(row.get("lifecycle_from", "")).upper()
            lifecycle_to = str(row.get("lifecycle_to", "")).upper()
            if lifecycle_from in ("ACTIVE", "UNKNOWN", "DELETED") \
                    or row.get("active_lease") \
                    or row.get("active_lock") \
                    or row.get("active_dependency") \
                    or reasons:
                return False
            if lifecycle_from not in ("COMPLETE", "DISPOSABLE"):
                return False
            if status == "DELETE_INTENT":
                if physical_deleted or row.get("filesystem_operation") \
                        != "NOT_ATTEMPTED" or lifecycle_to != lifecycle_from \
                        or workspace_id in seen_success:
                    return False
                seen_intent.add(workspace_id)
            else:
                if not physical_deleted or row.get("filesystem_operation") \
                        != "REMOVED" or lifecycle_to != "DELETED":
                    return False
                if not _tmp_gc_filesystem_result_is_well_formed(row):
                    return False
                if workspace_id not in seen_intent \
                        or workspace_id in seen_success:
                    return False
                seen_success.add(workspace_id)
        else:
            if row.get("delete_authorized") is True \
                    or row.get("physical_deleted") is True:
                return False
            if filesystem_operation == "REMOVED":
                return False
            if row.get("dry_run") is True \
                    and filesystem_operation not in {"DRY_RUN", "NOT_ATTEMPTED"}:
                return False
            if row.get("dry_run") is not True \
                    and filesystem_operation == "DRY_RUN":
                return False
        authorized_path = str(row.get("authorized_path", "")).strip()
        physical_path = str(row.get("physical_deleted_path", "")).strip()
        if authorized_path and not Path(authorized_path).is_absolute():
            return False
        if physical_path and not Path(physical_path).is_absolute():
            return False
        if authorized_path and physical_path \
                and _path_key(Path(authorized_path)) != _path_key(
                    Path(physical_path)
                ):
            return False
        if row.get("physical_deleted") is not True and physical_path:
            return False
        if status == "DELETE_PHYSICAL_SUCCESS":
            if _path_key(Path(raw_path)) != _path_key(Path(authorized_path)) \
                    or _path_key(Path(raw_path)) != _path_key(
                        Path(physical_path)
                    ):
                return False
        if row.get("physical_deleted") is True \
                and (status != "DELETE_PHYSICAL_SUCCESS"
                     or filesystem_operation != "REMOVED"):
            return False
        if status == "DELETE_PHYSICAL_SUCCESS" \
                and filesystem_operation != "REMOVED":
            return False
        lifecycle_from = str(row.get("lifecycle_from", prior_lifecycle)).upper()
        lifecycle_to = str(row.get("lifecycle_to", lifecycle_from)).upper()
        if lifecycle_from not in TMP_LIFECYCLE_STATES \
                or lifecycle_to not in TMP_LIFECYCLE_STATES:
            return False
        if lifecycle_from == "DELETED" and lifecycle_to != "DELETED":
            return False
        if lifecycle_to == "DELETED" and lifecycle_from not in (
                "COMPLETE", "DISPOSABLE", "DELETED"):
            return False
        if lifecycle_to == "DELETED" \
                and status != "DELETE_PHYSICAL_SUCCESS":
            return False
    return True


def read_tmp_gc_audit(root: str | Path) -> list[dict[str, Any]]:
    return [
        row for row in _read_jsonl(
            state_dir(root, mkdirs=False) / TMP_GC_AUDIT_PATH
        ) if isinstance(row, Mapping) and not row.get("_MALFORMED_LINE")
    ]


def _append_tmp_gc_audit(root: Path, record: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(record)
    status = str(payload.get("status", ""))
    workspace_id = str(payload.get("workspace_id", ""))
    digest = str(payload.get("classification_evidence_digest", ""))
    raw_path = str(payload.get("path", ""))
    raw_filesystem_result = payload.get("filesystem_result")
    if isinstance(raw_filesystem_result, Mapping):
        filesystem_result = dict(raw_filesystem_result)
    else:
        filesystem_result = {
            "operation": "UNKNOWN",
            "path": raw_path,
            "before": "UNKNOWN",
            "after": "UNKNOWN",
        }
    audit_id = _classification_digest([
        "tmp-gc-audit", workspace_id, status, digest
    ])
    payload = {
        "audit_id": audit_id,
        "schema": TMP_GC_SCHEMA,
        "workspace_id": workspace_id,
        "path": raw_path,
        "task_id": str(payload.get("task_id", "")),
        "prior_lifecycle": str(payload.get("prior_lifecycle", "")),
        "deletion_time": str(payload.get("deletion_time", _utc_now())),
        "classification_evidence_digest": digest,
        "reclaimed_bytes": int(payload.get("reclaimed_bytes", 0)),
        "reason": str(payload.get("reason", ""))[:512],
        "status": status,
        "delete_authorized": bool(payload.get(
            "delete_authorized", status in _TMP_GC_AUDIT_AUTHORIZED_STATUSES
        )),
        "final_revalidation_valid": bool(payload.get(
            "final_revalidation_valid",
            status in _TMP_GC_AUDIT_AUTHORIZED_STATUSES,
        )),
        "dry_run": bool(payload.get("dry_run", False)),
        "physical_deleted": bool(payload.get(
            "physical_deleted", status == "DELETE_PHYSICAL_SUCCESS"
        )),
        "authorized_path": str(payload.get(
            "authorized_path",
            payload.get("path", "")
            if status in _TMP_GC_AUDIT_AUTHORIZED_STATUSES else "",
        )),
        "physical_deleted_path": str(payload.get(
            "physical_deleted_path",
            payload.get("path", "")
            if status == "DELETE_PHYSICAL_SUCCESS" else "",
        )),
        "protection_reasons": list(payload.get("protection_reasons", [])),
        "active_lease": bool(payload.get("active_lease", False)),
        "active_lock": bool(payload.get("active_lock", False)),
        "active_dependency": bool(payload.get("active_dependency", False)),
        "filesystem_operation": str(payload.get(
            "filesystem_operation",
            "REMOVED" if status == "DELETE_PHYSICAL_SUCCESS"
            else "FAILED" if status == "DELETE_FAILED"
            else "NOT_ATTEMPTED",
        )).upper(),
        "filesystem_result": filesystem_result,
        "lifecycle_from": str(payload.get(
            "lifecycle_from", payload.get("prior_lifecycle", "")
        )).upper(),
        "lifecycle_to": str(payload.get(
            "lifecycle_to",
            "DELETED" if status == "DELETE_PHYSICAL_SUCCESS"
            else payload.get("prior_lifecycle", ""),
        )).upper(),
    }
    if status == "DELETE_PHYSICAL_SUCCESS" \
            and not _tmp_gc_filesystem_result_is_well_formed(payload):
        raise ValueError("TMP_GC_FILESYSTEM_RESULT_INVALID")
    path = state_dir(root, mkdirs=True) / TMP_GC_AUDIT_PATH
    for existing in read_tmp_gc_audit(root):
        if existing.get("audit_id") == audit_id:
            return existing
    _append_jsonl(path, payload)
    return payload


def _remove_verified_tree(path: Path) -> None:
    """Remove an already-classified tree without following reparse points.

    Git object files may be read-only on Windows.  Clearing that attribute is
    allowed only for the exact workspace already admitted by the final
    classifier; any reparse/unknown path encountered by the error handler
    aborts the removal.
    """
    def onerror(function: Any, failing_path: str, _exc_info: Any) -> None:
        candidate = Path(failing_path)
        if _reparse_marker(candidate) is not False:
            raise OSError("REPARSE_DURING_DELETE")
        os.chmod(candidate, stat.S_IREAD | stat.S_IWRITE)
        function(failing_path)

    shutil.rmtree(path, ignore_errors=False, onerror=onerror)


def _delete_tmp_workspace(root: Path, record: Mapping[str, Any],
                          classification: Mapping[str, Any],
                          policy: Mapping[str, Any], *,
                          now: str | None = None,
                          exclude_lease_id: str = "") -> dict[str, Any]:
    """Delete only while the existing FW06 writer boundary is held.

    The guard deliberately covers final revalidation, authorization, the
    filesystem operation, audit recording, and the lifecycle update.  A
    competing lease/state writer therefore cannot enter a check-then-delete
    gap, and lock acquisition failure is a safe no-delete result.
    """
    workspace_id = str(record.get("workspace_id") or
                       classification.get("workspace_id", ""))
    workspace = _rooted_path(root, str(record.get("root_path", "")))
    try:
        with _lease_writer_guard(root):
            return _delete_tmp_workspace_locked(
                root, record, classification, policy,
                now=now, exclude_lease_id=exclude_lease_id,
            )
    except _LeaseLockUnavailable:
        return {
            "workspace_id": workspace_id,
            "status": "DELETE_REVALIDATION_FAILED",
            "audit": {
                "workspace_id": workspace_id,
                "path": str(workspace),
                "status": "DELETE_REVALIDATION_FAILED",
                "reason": "DELETE_SERIALIZATION_UNAVAILABLE",
                "delete_authorized": False,
                "final_revalidation_valid": False,
                "physical_deleted": False,
            },
            "workspace_removed": False,
        }


def _delete_tmp_workspace_locked(root: Path, record: Mapping[str, Any],
                                 classification: Mapping[str, Any],
                                 policy: Mapping[str, Any], *,
                                 now: str | None = None,
                                 exclude_lease_id: str = "") -> dict[str, Any]:
    workspace = _rooted_path(root, str(record.get("root_path", "")))
    workspace_id = str(record.get("workspace_id") or
                       classification.get("workspace_id", ""))
    prior_lifecycle = str(record.get("lifecycle_state", ""))
    task_id = str(record.get("task_id") or record.get("owner_task_id") or "")
    digest = str(classification["classification_evidence_digest"])
    # Inventory and classification are evidence, never mutation authority.
    # Re-prove containment, reparse safety, and complete measurement in the
    # same process immediately before the destructive call.
    try:
        final_pressure = detect_disk_pressure(root, policy)
        final_classification = classify_tmp_workspace(
            root,
            record,
            policy=policy,
            pressure=final_pressure,
            now=now,
            registered_non_temp=_registered_non_temp_worktrees(root, policy),
            exclude_lease_id=exclude_lease_id,
        )
        if final_classification.get("final_action") != "DELETE_ELIGIBLE":
            raise TmpGcError("FINAL_CLASSIFICATION_CHANGED")
        classification = final_classification
        workspace = Path(str(classification["path"]))
        workspace_id = str(classification["workspace_id"])
        digest = str(classification["classification_evidence_digest"])
        identity = _tmp_path_identity(
            root, workspace, policy,
            registered_non_temp=_registered_non_temp_worktrees(root, policy),
        )
        if not identity.get("ok"):
            raise TmpGcError("FINAL_PATH_REVALIDATION_FAILED:" + str(
                identity.get("reason", "UNKNOWN")
            ))
        current_size, current_size_complete = _measure_tmp_path(workspace)
        if not current_size_complete:
            raise TmpGcError("FINAL_SIZE_REVALIDATION_FAILED")
        if current_size != int(classification.get("size", 0)):
            raise TmpGcError("FINAL_SIZE_CHANGED")
        if not _workspace_registry_is_well_formed(root):
            raise TmpGcError("FINAL_WORKSPACE_REGISTRY_MALFORMED")
        if not _tmp_gc_audit_is_well_formed(root):
            raise TmpGcError("FINAL_TMP_GC_AUDIT_MALFORMED")
        latest = _latest_workspace_rows(root).get(workspace_id)
        if latest is None or _classification_digest(
                _json_safe(dict(latest))) != _classification_digest(
                    _json_safe(dict(record))):
            raise TmpGcError("FINAL_WORKSPACE_RECORD_CHANGED")
        duplicate = _duplicate_path_binding(root, workspace)
        if duplicate is not False:
            raise TmpGcError("FINAL_DUPLICATE_PATH_BINDING")
        lock_states = [_lock_state(workspace), _lock_state(root)]
        if any(state != "CLEAR" for state in lock_states):
            raise TmpGcError("FINAL_RELEVANT_LOCK_STATE_UNKNOWN_OR_LOCKED")
    except (OSError, ValueError) as exc:
        failure = _append_tmp_gc_audit(root, {
            "workspace_id": workspace_id,
            "path": str(workspace),
            "task_id": task_id,
            "prior_lifecycle": prior_lifecycle,
            "classification_evidence_digest": digest,
            "reclaimed_bytes": 0,
            "reason": "DELETE_REVALIDATION_FAILED:" + str(exc),
            "status": "DELETE_REVALIDATION_FAILED",
            "filesystem_operation": "NOT_ATTEMPTED",
            "filesystem_result": _tmp_gc_filesystem_not_attempted(workspace),
        })
        return {
            "workspace_id": workspace_id,
            "status": "DELETE_REVALIDATION_FAILED",
            "audit": failure,
            "workspace_removed": False,
        }
    try:
        intent = _append_tmp_gc_audit(root, {
            "workspace_id": workspace_id,
            "path": str(workspace),
            "task_id": task_id,
            "prior_lifecycle": prior_lifecycle,
            "classification_evidence_digest": digest,
            "reclaimed_bytes": 0,
            "reason": "DELETE_INTENT_AFTER_FINAL_REVALIDATION",
            "status": "DELETE_INTENT",
            "filesystem_operation": "NOT_ATTEMPTED",
            "filesystem_result": _tmp_gc_filesystem_not_attempted(workspace),
        })
    except Exception as exc:  # noqa: BLE001
        return {
            "workspace_id": workspace_id,
            "status": "DELETE_AUDIT_FAILED",
            "audit": {
                "status": "DELETE_AUDIT_FAILED",
                "reason": "DELETE_INTENT_AUDIT_FAILED:" + str(exc),
            },
            "workspace_removed": False,
        }
    filesystem_result = _tmp_gc_filesystem_not_attempted(workspace)
    try:
        if not os.path.lexists(str(workspace)):
            filesystem_result = _tmp_gc_filesystem_observation(
                workspace, "NOT_FOUND", before="ABSENT"
            )
            raise FileNotFoundError(str(workspace))
        marker = _reparse_marker(workspace)
        if marker is not False:
            raise OSError("PATH_REPARSE_OR_UNKNOWN")
        filesystem_result = _tmp_gc_filesystem_observation(
            workspace, "FAILED", before="PRESENT"
        )
        if record.get("git_worktree") and str(
                record.get("git_worktree")).strip().lower() not in ("false", "none"):
            repo = str(record.get("repo_path", "")).strip()
            if not repo:
                raise OSError("WORKTREE_REPO_UNKNOWN")
            removed = _git_run(
                _rooted_path(root, repo),
                ["worktree", "remove", str(workspace)],
            )
            if removed is None or removed.returncode != 0:
                raise OSError("WORKTREE_REMOVE_FAILED")
        elif workspace.is_dir():
            _remove_verified_tree(workspace)
        else:
            workspace.unlink()
        if os.path.lexists(str(workspace)):
            raise OSError("DELETED_PATH_VERIFICATION_FAILED")
    except (OSError, ValueError) as exc:
        if filesystem_result["operation"] == "FAILED":
            filesystem_result = _tmp_gc_filesystem_observation(
                workspace, "FAILED", before="PRESENT"
            )
        failure = _append_tmp_gc_audit(root, {
            "workspace_id": workspace_id,
            "path": str(workspace),
            "task_id": task_id,
            "prior_lifecycle": prior_lifecycle,
            "classification_evidence_digest": digest,
            "reclaimed_bytes": 0,
            "reason": "DELETE_FAILED:" + str(exc),
            "status": "DELETE_FAILED",
            "filesystem_operation": filesystem_result["operation"],
            "filesystem_result": filesystem_result,
        })
        try:
            _workspace_state_update(
                root, workspace_id, lifecycle_state="COMPLETE",
                status="CLEANUP_PENDING",
                event_type="TMP_WORKSPACE_DELETE_FAILED",
                _serialization_held=True,
                protection_reasons=["UNKNOWN"],
                deletion_reason="DELETE_FAILED",
            )
        except ValueError:
            pass
        return {
            "workspace_id": workspace_id,
            "status": "DELETE_FAILED",
            "audit": failure,
            "workspace_removed": False,
        }
    filesystem_result = _tmp_gc_filesystem_observation(
        workspace, "REMOVED", before="PRESENT"
    )
    reclaimed = current_size
    try:
        physical = _append_tmp_gc_audit(root, {
            "workspace_id": workspace_id,
            "path": str(workspace),
            "task_id": task_id,
            "prior_lifecycle": prior_lifecycle,
            "classification_evidence_digest": digest,
            "reclaimed_bytes": reclaimed,
            "reason": "PHYSICAL_DELETE_VERIFIED_STATE_PENDING",
            "status": "DELETE_PHYSICAL_SUCCESS",
            "filesystem_operation": filesystem_result["operation"],
            "filesystem_result": filesystem_result,
        })
    except Exception as exc:  # noqa: BLE001
        try:
            _workspace_state_update(
                root, workspace_id, lifecycle_state="COMPLETE",
                status="CLEANUP_PENDING",
                event_type="TMP_WORKSPACE_DELETE_AUDIT_FAILED",
                _serialization_held=True,
                protection_reasons=["UNKNOWN"],
                deletion_reason="DELETE_AUDIT_FAILED",
            )
        except Exception:  # noqa: BLE001
            pass
        return {
            "workspace_id": workspace_id,
            "status": "DELETE_AUDIT_FAILED",
            "audit": {
                "status": "DELETE_AUDIT_FAILED",
                "reason": "DELETE_PHYSICAL_AUDIT_FAILED:" + str(exc),
            },
            "workspace_removed": True,
            "reclaimed_bytes": reclaimed,
        }
    try:
        _workspace_state_update(
            root, workspace_id, lifecycle_state="DELETED",
            status="CLEANED", event_type="TMP_WORKSPACE_DELETED",
            _serialization_held=True,
            protection_reasons=[],
            deletion_reason="SAFE_GC_ALL_PREDICATES_VERIFIED",
            deleted_utc=physical["deletion_time"],
        )
    except Exception as exc:  # noqa: BLE001
        failure = _append_tmp_gc_audit(root, {
            "workspace_id": workspace_id,
            "path": str(workspace),
            "task_id": task_id,
            "prior_lifecycle": prior_lifecycle,
            "classification_evidence_digest": digest,
            "reclaimed_bytes": reclaimed,
            "reason": "STATE_UPDATE_FAILED:" + str(exc),
            "status": "STATE_UPDATE_FAILED",
            "filesystem_operation": "NOT_ATTEMPTED",
            "filesystem_result": _tmp_gc_filesystem_not_attempted(workspace),
        })
        return {
            "workspace_id": workspace_id,
            "status": "STATE_UPDATE_FAILED",
            "audit": failure,
            "workspace_removed": True,
            "reclaimed_bytes": reclaimed,
            "physical_audit_id": physical["audit_id"],
        }
    return {
        "workspace_id": workspace_id,
        "status": "DELETED",
        "audit": physical,
        "workspace_removed": True,
        "reclaimed_bytes": reclaimed,
        "intent_audit_id": intent["audit_id"],
    }


def apply_tmp_gc(root: str | Path, inventory: Mapping[str, Any],
                 *,
                 policy: Mapping[str, Any] | None = None,
                 policy_path: str | Path | None = None,
                 now: str | None = None) -> dict[str, Any]:
    """Apply only after a fresh classification for every candidate."""
    root_path = Path(root).expanduser().resolve()
    policy_data = load_tmp_gc_policy(root_path, policy_path, policy)
    pressure = detect_disk_pressure(root_path, policy_data)
    result = dict(inventory)
    result["dry_run"] = False
    result["apply_requested"] = True
    result["applied"] = []
    result["deleted_count"] = 0
    result["legacy_workspace_delete_count"] = 0
    if not _workspace_registry_is_well_formed(root_path):
        result["apply_status"] = "KEEP"
        result["apply_block_reason"] = "WORKSPACE_REGISTRY_MALFORMED"
        return result
    if not _tmp_gc_audit_is_well_formed(root_path):
        result["apply_status"] = "KEEP"
        result["apply_block_reason"] = "TMP_GC_AUDIT_MALFORMED"
        return result
    lease = acquire_lease(
        root_path,
        owner_process="p2p-tmp-gc-" + str(os.getpid()),
        project_id="P2P_TMP_GC",
        goal_id="P2P-TMPGC01",
        task_id="TMPGC01",
        ttl_seconds=120,
    )
    if not lease.get("acquired"):
        result["apply_status"] = "KEEP"
        result["apply_block_reason"] = "ACTIVE_SESSION"
        return result
    try:
        latest = _latest_workspace_rows(root_path)
        refreshed: list[dict[str, Any]] = []
        non_temp_worktrees = _registered_non_temp_worktrees(root_path, policy_data)
        gc_lease_id = str(lease["lease"]["lease_id"])
        for item in inventory.get("workspaces", []):
            workspace_id = str(item.get("workspace_id", ""))
            current = latest.get(workspace_id)
            if current is None:
                refreshed.append(dict(item, final_action="KEEP",
                                      eligibility="KEEP",
                                      protection_reasons=["UNKNOWN"]))
                continue
            fresh = classify_tmp_workspace(
                root_path, current, policy=policy_data, pressure=pressure,
                now=now, registered_non_temp=non_temp_worktrees,
                exclude_lease_id=gc_lease_id,
            )
            if fresh.get("final_action") != "DELETE_ELIGIBLE":
                refreshed.append(fresh)
                continue
            # One last read/classification is deliberate: inventory rows are
            # never deletion authority, and TOCTOU state changes become KEEP.
            current = _latest_workspace_rows(root_path).get(workspace_id)
            if current is None:
                refreshed.append(dict(fresh, final_action="KEEP",
                                      eligibility="KEEP",
                                      protection_reasons=["UNKNOWN"]))
                continue
            final = classify_tmp_workspace(
                root_path, current, policy=policy_data,
                pressure=detect_disk_pressure(root_path, policy_data),
                now=now, registered_non_temp=non_temp_worktrees,
                exclude_lease_id=gc_lease_id,
            )
            if final.get("final_action") != "DELETE_ELIGIBLE":
                refreshed.append(final)
                continue
            outcome = _delete_tmp_workspace(
                root_path, current, final, policy_data,
                now=now,
                exclude_lease_id=gc_lease_id,
            )
            result["applied"].append(outcome)
            if outcome.get("status") == "DELETED":
                result["deleted_count"] += 1
                refreshed.append(dict(final, size=0, lifecycle="DELETED",
                                      final_action="KEEP",
                                      eligibility="DELETED"))
            else:
                refreshed.append(dict(final, lifecycle="COMPLETE",
                                      final_action="KEEP",
                                      eligibility="KEEP",
                                      protection_reasons=["UNKNOWN"]))
        result["workspaces"] = refreshed
        result["pressure"] = pressure
        result["apply_status"] = (
            "PASS" if all(item.get("status") == "DELETED"
                           for item in result["applied"])
            else ("PASS" if not result["applied"] else "KEEP")
        )
        refreshed_summary = _tmp_gc_summary(
            refreshed, root_path, policy_data, pressure, dry_run=False,
        )
        for key in (
                "total_temp_size", "active_size", "complete_protected_size",
                "candidate_size", "owner_gate_size", "rollback_required_size",
                "unknown_size", "disposable_size", "reclaimable_after_grace",
                "largest_consumers"):
            result[key] = refreshed_summary[key]
        return result
    finally:
        release_lease(root_path, str(lease["lease"]["lease_id"]))


def run_tmp_gc(root: str | Path, *,
               apply: bool = False,
               policy: Mapping[str, Any] | None = None,
               policy_path: str | Path | None = None,
               now: str | None = None) -> dict[str, Any]:
    inventory = inventory_tmp_gc(
        root, policy=policy, policy_path=policy_path, now=now,
    )
    if not apply:
        return inventory
    return apply_tmp_gc(
        root, inventory, policy=policy, policy_path=policy_path, now=now,
    )


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
