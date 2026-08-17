"""C33 — Provider-neutral bounded AutoPilot goal-state contracts.

This module is the durable goal-level control plane for the Bounded
AutoPilot.  It is deliberately a structured-data boundary: it does not start
work, select an agent, install a capability, route providers, run a scheduler,
or keep a process alive after the current session.  It extends the C11
task-state contracts (.p2p/system/p2p_capabilities/task_state.py) and the C30
execution-target contracts (.p2p/system/p2p_capabilities/execution_target.py)
and never duplicates their authority:

    - Task plans, transitions, evidence binding, preflight, checkpoints and
      resume classification remain the single authority of task_state.py.
    - Execution-target eligibility remains the single authority of
      execution_target.py.

New durable surface introduced here (goal-level, append-only):

    .p2p/state/autopilot-goal-state.json   GoalPlan projection (single goal)
    .p2p/state/goal-ledger.jsonl           append-only goal event stream

The chat transcript is never authoritative state.  Chat output may optionally
exist as execution evidence with a durable reference.  Evidence pointers, not
transcripts, are persisted.

Safety invariants preserved:

    PROJECT STATE != CHAT HISTORY
    TASK != AGENT
    GOAL PASS != PROMOTION
    PERMISSION COMPOSITION NEVER WIDENS AUTHORITY
    UNKNOWN FAILS CLOSED
    DONE REQUIRES ACCEPTABLE EVIDENCE
    NO BACKGROUND AUTONOMY
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
import hashlib
import json
import re
import threading
from pathlib import Path
from typing import Any, Iterable, Mapping

from .task_state import (
    LogicalOwner,
    TaskContractError,
    TaskStateError,
    TaskTransitionError,
    _required_text,
    _safe_text,
    _tuple_refs,
    _unique_refs,
    _sha256,
    _assert_sha256,
    _safe_mapping,
    _assert_no_identity_fields,
    _check_timestamp,
    utc_now,
    TASK_STATES,
)


GOAL_PLAN_SCHEMA = "p2p-autopilot-goal/1"
GOAL_EVENT_SCHEMA = "p2p-goal-event/1"
GOAL_STATE_RELATIVE_PATH = ".p2p/state/autopilot-goal-state.json"
GOAL_LEDGER_RELATIVE_PATH = ".p2p/state/goal-ledger.jsonl"

GOAL_STATUS_STATES = (
    "PLANNED",
    "APPROVED",
    "IN_PROGRESS",
    "OWNER_GATE",
    "BLOCKED",
    "BUDGET_BOUNDARY",
    "VERIFIED",
    "GOAL_DONE",
    "TERMINAL",
    "CANCELLED",
)

TERMINAL_STATUSES = ("GOAL_DONE", "TERMINAL", "CANCELLED")
ACTIVE_STATUSES = ("APPROVED", "IN_PROGRESS", "OWNER_GATE", "BLOCKED", "BUDGET_BOUNDARY")

GOAL_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")
GOAL_VERSION_RE = re.compile(r"^v[0-9]{1,8}$")


class GoalContractError(TaskStateError):
    """Raised when a goal or goal-event record violates its contract."""


class GoalTransitionError(TaskStateError):
    """Raised when a goal state transition is not explicitly allowed."""


class GoalLedgerError(TaskStateError):
    """Raised when the append-only goal ledger cannot be maintained."""


_GOAL_STATE_LOCKS: dict[str, threading.RLock] = {}
_GOAL_STATE_LOCKS_GUARD = threading.Lock()

ALLOWED_GOAL_TRANSITIONS: dict[str, tuple[str, ...]] = {
    "PLANNED": ("APPROVED", "BLOCKED", "CANCELLED"),
    "APPROVED": ("IN_PROGRESS", "OWNER_GATE", "BLOCKED", "BUDGET_BOUNDARY", "CANCELLED"),
    "IN_PROGRESS": ("OWNER_GATE", "BLOCKED", "BUDGET_BOUNDARY", "VERIFIED", "GOAL_DONE", "TERMINAL", "CANCELLED"),
    "OWNER_GATE": ("APPROVED", "IN_PROGRESS", "BLOCKED", "TERMINAL", "CANCELLED"),
    "BLOCKED": ("APPROVED", "IN_PROGRESS", "BUDGET_BOUNDARY", "TERMINAL", "CANCELLED"),
    "BUDGET_BOUNDARY": ("APPROVED", "IN_PROGRESS", "TERMINAL", "CANCELLED"),
    # VERIFIED re-entry to APPROVED is deliberate and narrow: the goal has
    # completed every known task with verified evidence, yet the wave has
    # remaining READY tasks (new tasks discovered in refresh). No pending
    # mutation is open, so re-entry cannot hide an unverified change.
    "VERIFIED": ("APPROVED", "GOAL_DONE", "TERMINAL"),
    "GOAL_DONE": (),
    "TERMINAL": (),
    "CANCELLED": (),
}


def _goal_id(value: Any) -> str:
    text = _required_text(value, "goal_id", max_length=128)
    if not GOAL_ID_RE.fullmatch(text):
        raise GoalContractError("GOAL_ID_INVALID")
    return text


def _goal_version(value: Any) -> str:
    text = _required_text(value, "goal_version", max_length=16)
    if not GOAL_VERSION_RE.fullmatch(text):
        raise GoalContractError("GOAL_VERSION_INVALID")
    return text


@dataclass(frozen=True)
class ExecutionBound:
    """Bounded, identity-free execution envelope for one goal run."""

    max_tasks: int = 64
    max_executions_per_task: int = 16
    max_retries_per_task: int = 4
    max_workspace_changes: int = 1024
    max_verifications_per_task: int = 8
    wall_clock_seconds: float = 7200.0
    model_cost_units: float = 0.0
    model_token_units: float = 0.0

    def __post_init__(self) -> None:
        for field_name, value, bounds in (
            ("max_tasks", self.max_tasks, (1, 64)),
            ("max_executions_per_task", self.max_executions_per_task, (1, 64)),
            ("max_retries_per_task", self.max_retries_per_task, (0, 16)),
            ("max_workspace_changes", self.max_workspace_changes, (1, 10_000)),
            ("max_verifications_per_task", self.max_verifications_per_task, (1, 64)),
            ("wall_clock_seconds", self.wall_clock_seconds, (1.0, 86400.0)),
            ("model_cost_units", self.model_cost_units, (0.0, 1_000_000.0)),
            ("model_token_units", self.model_token_units, (0.0, 1_000_000_000.0)),
        ):
            low, high = bounds
            if not isinstance(value, (int, float)) or not (low <= float(value) <= high):
                raise GoalContractError(f"EXECUTION_BOUND_{field_name.upper()}_INVALID")

    def to_dict(self) -> dict[str, Any]:
        return {
            "max_tasks": int(self.max_tasks),
            "max_executions_per_task": int(self.max_executions_per_task),
            "max_retries_per_task": int(self.max_retries_per_task),
            "max_workspace_changes": int(self.max_workspace_changes),
            "max_verifications_per_task": int(self.max_verifications_per_task),
            "wall_clock_seconds": float(self.wall_clock_seconds),
            "model_cost_units": float(self.model_cost_units),
            "model_token_units": float(self.model_token_units),
        }

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any] | None) -> "ExecutionBound":
        if value is None:
            return cls()
        if not isinstance(value, Mapping):
            raise GoalContractError("EXECUTION_BOUND_MUST_BE_OBJECT")
        allowed = {
            "max_tasks",
            "max_executions_per_task",
            "max_retries_per_task",
            "max_workspace_changes",
            "max_verifications_per_task",
            "wall_clock_seconds",
            "model_cost_units",
            "model_token_units",
        }
        unknown = sorted(str(key) for key in value if str(key) not in allowed)
        if unknown:
            raise GoalContractError("EXECUTION_BOUND_FIELDS_INVALID:" + ",".join(unknown))
        return cls(
            max_tasks=int(value.get("max_tasks", 64)),
            max_executions_per_task=int(value.get("max_executions_per_task", 16)),
            max_retries_per_task=int(value.get("max_retries_per_task", 4)),
            max_workspace_changes=int(value.get("max_workspace_changes", 1024)),
            max_verifications_per_task=int(value.get("max_verifications_per_task", 8)),
            wall_clock_seconds=float(value.get("wall_clock_seconds", 7200.0)),
            model_cost_units=float(value.get("model_cost_units", 0.0)),
            model_token_units=float(value.get("model_token_units", 0.0)),
        )


@dataclass(frozen=True)
class GoalPlan:
    """Approved, bounded, provider-neutral Goal projection.

    The durable projection of one Owner-approved Goal that the AutoPilot core
    loop may traverse.  Every field is validated deterministically.  Task
    identities are C11 task records, not agent/provider/model identities.
    """

    goal_id: str
    goal_version: str
    title: str
    purpose: str
    owner_approval_ref: str
    scope: tuple[str, ...] = ()
    non_scope: tuple[str, ...] = ()
    plan_task_ids: tuple[str, ...] = ()
    status: str = "PLANNED"
    execution_bound: ExecutionBound = field(default_factory=ExecutionBound)
    budget_usage: dict[str, Any] = field(default_factory=lambda: {
        "tasks_completed": 0,
        "executions_used": 0,
        "retries_used": 0,
        "workspace_changes": 0,
        "verifications_used": 0,
        "wall_clock_seconds_used": 0.0,
        "model_cost_units_used": 0.0,
        "model_token_units_used": 0.0,
    })
    current_task_id: str | None = None
    next_task_id: str | None = None
    wave: int = 1
    terminal_state: str | None = None
    terminal_reason: str | None = None
    resume_point: dict[str, Any] | None = None
    owner_gate: dict[str, Any] | None = None
    blocker: dict[str, Any] | None = None
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        _goal_id(self.goal_id)
        _goal_version(self.goal_version)
        _required_text(self.title, "goal.title", max_length=4096)
        _required_text(self.purpose, "goal.purpose", max_length=8192)
        _required_text(self.owner_approval_ref, "goal.owner_approval_ref", max_length=1024)
        for field_name, value, required in (
            ("scope", self.scope, True),
            ("non_scope", self.non_scope, False),
            ("plan_task_ids", self.plan_task_ids, True),
        ):
            if not isinstance(value, tuple):
                raise GoalContractError(f"goal.{field_name}_MUST_BE_TUPLE")
            normalized = _unique_refs(value, field_name, required=required)
            if tuple(value) != normalized:
                raise GoalContractError(f"goal.{field_name}_MUST_BE_UNIQUE_AND_ORDERED")
        if self.status not in GOAL_STATUS_STATES:
            raise GoalContractError("GOAL_STATUS_INVALID")
        if not isinstance(self.execution_bound, ExecutionBound):
            raise GoalContractError("GOAL_EXECUTION_BOUND_INVALID")
        if len(self.plan_task_ids) > int(self.execution_bound.max_tasks):
            raise GoalContractError("GOAL_EXCEEDS_MAX_TASKS")
        if not isinstance(self.budget_usage, Mapping):
            raise GoalContractError("GOAL_BUDGET_USAGE_MUST_BE_OBJECT")
        _assert_no_identity_fields(self.budget_usage, path="goal.budget_usage")
        if self.current_task_id is not None:
            _required_text(self.current_task_id, "goal.current_task_id", max_length=128)
        if self.next_task_id is not None:
            _required_text(self.next_task_id, "goal.next_task_id", max_length=128)
        if not isinstance(self.wave, int) or self.wave < 1:
            raise GoalContractError("GOAL_WAVE_INVALID")
        if self.terminal_state is not None:
            _required_text(self.terminal_state, "goal.terminal_state", max_length=256)
        if self.terminal_reason is not None:
            _required_text(self.terminal_reason, "goal.terminal_reason", max_length=4096)
        _check_timestamp(self.created_at, "goal.created_at")
        _check_timestamp(self.updated_at, "goal.updated_at")
        if self.resume_point is not None:
            _assert_no_identity_fields(self.resume_point, path="goal.resume_point")
        if self.owner_gate is not None:
            _assert_no_identity_fields(self.owner_gate, path="goal.owner_gate")
        if self.blocker is not None:
            _assert_no_identity_fields(self.blocker, path="goal.blocker")

    def is_terminal(self) -> bool:
        return self.status in TERMINAL_STATUSES

    def is_active(self) -> bool:
        return self.status in ACTIVE_STATUSES

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": GOAL_PLAN_SCHEMA,
            "goal_id": self.goal_id,
            "goal_version": self.goal_version,
            "title": self.title,
            "purpose": self.purpose,
            "owner_approval_ref": self.owner_approval_ref,
            "scope": list(self.scope),
            "non_scope": list(self.non_scope),
            "plan_task_ids": list(self.plan_task_ids),
            "status": self.status,
            "execution_bound": self.execution_bound.to_dict(),
            "budget_usage": dict(self.budget_usage),
            "current_task_id": self.current_task_id,
            "next_task_id": self.next_task_id,
            "wave": self.wave,
            "terminal_state": self.terminal_state,
            "terminal_reason": self.terminal_reason,
            "resume_point": dict(self.resume_point) if isinstance(self.resume_point, Mapping) else None,
            "owner_gate": dict(self.owner_gate) if isinstance(self.owner_gate, Mapping) else None,
            "blocker": dict(self.blocker) if isinstance(self.blocker, Mapping) else None,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "automatic_start": False,
            "background_execution": False,
            "process_survives_session": False,
        }

    def canonical_hash(self) -> str:
        return _sha256(self.to_dict())

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "GoalPlan":
        if not isinstance(value, Mapping):
            raise GoalContractError("GOAL_PLAN_MUST_BE_OBJECT")
        if str(value.get("schema", "")) != GOAL_PLAN_SCHEMA:
            raise GoalContractError("GOAL_PLAN_SCHEMA_INVALID")
        allowed = {
            "schema", "goal_id", "goal_version", "title", "purpose",
            "owner_approval_ref", "scope", "non_scope", "plan_task_ids",
            "status", "execution_bound", "budget_usage", "current_task_id",
            "next_task_id", "wave", "terminal_state", "terminal_reason",
            "resume_point", "owner_gate", "blocker", "created_at", "updated_at",
            "automatic_start", "background_execution", "process_survives_session",
        }
        unknown = sorted(str(key) for key in value if str(key) not in allowed)
        if unknown:
            raise GoalContractError("GOAL_PLAN_FIELDS_INVALID:" + ",".join(unknown))
        _assert_no_identity_fields(value, path="goal")
        return cls(
            goal_id=str(value.get("goal_id", "")),
            goal_version=str(value.get("goal_version", "")),
            title=str(value.get("title", "")),
            purpose=str(value.get("purpose", "")),
            owner_approval_ref=str(value.get("owner_approval_ref", "")),
            scope=tuple(value.get("scope", [])),
            non_scope=tuple(value.get("non_scope", [])),
            plan_task_ids=tuple(value.get("plan_task_ids", [])),
            status=str(value.get("status", "PLANNED")),
            execution_bound=ExecutionBound.from_mapping(value.get("execution_bound")),
            budget_usage=dict(value.get("budget_usage", {})) or {
                "tasks_completed": 0,
                "executions_used": 0,
                "retries_used": 0,
                "workspace_changes": 0,
                "verifications_used": 0,
                "wall_clock_seconds_used": 0.0,
                "model_cost_units_used": 0.0,
                "model_token_units_used": 0.0,
            },
            current_task_id=value.get("current_task_id"),
            next_task_id=value.get("next_task_id"),
            wave=int(value.get("wave", 1)),
            terminal_state=value.get("terminal_state"),
            terminal_reason=value.get("terminal_reason"),
            resume_point=value.get("resume_point"),
            owner_gate=value.get("owner_gate"),
            blocker=value.get("blocker"),
            created_at=str(value.get("created_at", "")),
            updated_at=str(value.get("updated_at", "")),
        )

    def transition(
        self,
        target_status: str,
        *,
        terminal_state: str | None = None,
        terminal_reason: str | None = None,
        resume_point: Mapping[str, Any] | None = None,
        owner_gate: Mapping[str, Any] | None = None,
        blocker: Mapping[str, Any] | None = None,
        current_task_id: str | None = "UNCHANGED",
        next_task_id: str | None = "UNCHANGED",
        wave: int | None = None,
        now: str | None = None,
    ) -> "GoalPlan":
        """Deterministic goal transition with fail-closed validation."""
        if target_status not in ALLOWED_GOAL_TRANSITIONS[self.status]:
            raise GoalTransitionError(
                f"GOAL_TRANSITION_NOT_ALLOWED:{self.status}->{target_status}"
            )
        if target_status in TERMINAL_STATUSES:
            if not isinstance(terminal_state, str) or not terminal_state.strip():
                raise GoalTransitionError("GOAL_TERMINAL_STATE_REQUIRED")
            _required_text(terminal_state, "terminal_state", max_length=256)
        if target_status == "OWNER_GATE":
            if not isinstance(owner_gate, Mapping):
                raise GoalTransitionError("GOAL_OWNER_GATE_PAYLOAD_REQUIRED")
            if not owner_gate.get("reason_class"):
                raise GoalTransitionError("GOAL_OWNER_GATE_REASON_REQUIRED")
        if target_status == "BUDGET_BOUNDARY":
            if not isinstance(resume_point, Mapping):
                raise GoalTransitionError("GOAL_BUDGET_BOUNDARY_RESUME_POINT_REQUIRED")
        if target_status == "BLOCKED":
            if not isinstance(blocker, Mapping):
                raise GoalTransitionError("GOAL_BLOCKER_PAYLOAD_REQUIRED")
        timestamp = _check_timestamp(now or utc_now(), "goal.transition_at")
        new_next = None if next_task_id == "UNCHANGED" else next_task_id
        new_current = None if current_task_id == "UNCHANGED" else current_task_id
        cleared_gate = None if target_status != "OWNER_GATE" else (
            dict(self.owner_gate) if isinstance(self.owner_gate, Mapping) else None
        )
        cleared_blocker = None if target_status != "BLOCKED" else (
            dict(self.blocker) if isinstance(self.blocker, Mapping) else None
        )
        return replace(
            self,
            status=target_status,
            terminal_state=terminal_state,
            terminal_reason=terminal_reason,
            resume_point=dict(resume_point) if resume_point is not None else (
                None if target_status != "BUDGET_BOUNDARY" else self.resume_point
            ),
            owner_gate=dict(owner_gate) if owner_gate is not None else None,
            blocker=dict(blocker) if blocker is not None else None,
            current_task_id=new_current,
            next_task_id=new_next,
            wave=wave if wave is not None else (self.wave + 1 if target_status == "IN_PROGRESS" else self.wave),
            updated_at=timestamp,
        )

    def consume_budget(self, *, executions: int = 0, retries: int = 0, verifications: int = 0,
                       workspace_changes: int = 0, wall_seconds: float = 0.0,
                       cost_units: float = 0.0, token_units: float = 0.0) -> "GoalPlan":
        usage = dict(self.budget_usage)
        for field_name, increment in (
            ("executions_used", executions),
            ("retries_used", retries),
            ("verifications_used", verifications),
            ("workspace_changes", workspace_changes),
        ):
            if not isinstance(increment, int) or increment < 0:
                raise GoalContractError(f"BUDGET_USAGE_{field_name.upper()}_INVALID")
            usage[field_name] = int(usage.get(field_name, 0)) + increment
        for field_name, increment in (
            ("wall_clock_seconds_used", wall_seconds),
            ("model_cost_units_used", cost_units),
            ("model_token_units_used", token_units),
        ):
            if not isinstance(increment, (int, float)) or increment < 0:
                raise GoalContractError(f"BUDGET_USAGE_{field_name.upper()}_INVALID")
            usage[field_name] = float(usage.get(field_name, 0.0)) + float(increment)
        tasks_done = int(usage.get("tasks_completed", 0))
        return replace(
            self,
            budget_usage=usage,
            updated_at=utc_now(),
            **({"current_task_id": None} if tasks_done == int(self.budget_usage.get("tasks_completed", 0)) + 0 else {}),
        )

    def mark_task_completed(self) -> "GoalPlan":
        usage = dict(self.budget_usage)
        usage["tasks_completed"] = int(usage.get("tasks_completed", 0)) + 1
        return replace(self, budget_usage=usage, updated_at=utc_now())


class GoalStateStore:
    """Durable adapter over autopilot-goal-state.json and goal-ledger.jsonl.

    Append-only goal ledger.  A corrupt or mismatched state file is a
    control-plane error and is never silently repaired.
    """

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.state_path = self.root / GOAL_STATE_RELATIVE_PATH
        self.ledger_path = self.root / GOAL_LEDGER_RELATIVE_PATH
        self._lock = _goal_state_lock(self)

    @classmethod
    def for_path(cls, path: Path) -> "GoalStateStore":
        return cls(path)

    def _lock_guard(self) -> threading.RLock:
        return self._lock

    def load(self) -> GoalPlan | None:
        if not self.state_path.exists():
            return None
        try:
            payload = json.loads(self.state_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise GoalLedgerError(f"GOAL_STATE_CORRUPT:{exc}") from exc
        if not isinstance(payload, Mapping):
            raise GoalLedgerError("GOAL_STATE_CORRUPT")
        if str(payload.get("schema", "")) != GOAL_PLAN_SCHEMA:
            raise GoalLedgerError("GOAL_STATE_SCHEMA_MISMATCH")
        inner = payload.get("plan", payload)
        if not isinstance(inner, Mapping):
            raise GoalLedgerError("GOAL_STATE_PLAN_MISSING")
        return GoalPlan.from_mapping(inner)

    def require(self) -> GoalPlan:
        plan = self.load()
        if plan is None:
            raise GoalLedgerError("GOAL_STATE_NOT_INITIALIZED")
        return plan

    def _append_event(
        self,
        plan: GoalPlan,
        event_name: str,
        *,
        task_id: str | None = None,
        details: Mapping[str, Any] | None = None,
        at: str | None = None,
    ) -> None:
        if not isinstance(event_name, str) or not event_name.strip():
            raise GoalLedgerError("GOAL_EVENT_NAME_REQUIRED")
        safe_details: dict[str, Any] = {}
        if details is not None:
            if not isinstance(details, Mapping):
                raise GoalLedgerError("GOAL_EVENT_DETAILS_MUST_BE_OBJECT")
            _assert_no_identity_fields(details, path="goal_event.details")
            safe_details = _safe_mapping(dict(details), "goal_event.details") or {}
        event = {
            "schema_version": GOAL_EVENT_SCHEMA,
            "at": _check_timestamp(at or utc_now(), "goal_event.at"),
            "event": _required_text(event_name, "goal_event.event", max_length=256),
            "goal_id": plan.goal_id,
            "goal_version": plan.goal_version,
            "goal_hash": plan.canonical_hash(),
            "state_ref": GOAL_STATE_RELATIVE_PATH,
            "task_id": task_id,
            "details": safe_details,
            "automatic_start": False,
            "background_execution": False,
            "process_survives_session": False,
        }
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with self.ledger_path.open("a", encoding="utf-8", newline="\n") as handle:
                handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
        except OSError as exc:
            raise GoalLedgerError(f"GOAL_EVENT_APPEND_FAILED:{exc}") from exc

    def save(
        self,
        plan: GoalPlan,
        *,
        event_name: str = "goal_plan_saved",
        task_id: str | None = None,
        details: Mapping[str, Any] | None = None,
        at: str | None = None,
    ) -> GoalPlan:
        with self._lock:
            if not isinstance(plan, GoalPlan):
                raise GoalLedgerError("GOAL_PLAN_REQUIRED")
            existing = self.load()
            if existing is not None and existing.goal_id != plan.goal_id:
                raise GoalLedgerError(f"GOAL_STATE_GOAL_MISMATCH:{existing.goal_id}:{plan.goal_id}")
            if existing is not None and existing.canonical_hash() == plan.canonical_hash() and existing.status == plan.status:
                return existing
            saved_at = _check_timestamp(at or utc_now(), "goal_state.saved_at")
            payload = {
                "schema": GOAL_PLAN_SCHEMA,
                "state_ref": GOAL_STATE_RELATIVE_PATH,
                "plan": plan.to_dict(),
                "goal_hash": plan.canonical_hash(),
                "saved_at": saved_at,
            }
            self.state_path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.state_path.with_name(self.state_path.name + ".tmp")
            try:
                temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
                temporary.replace(self.state_path)
            except OSError as exc:
                raise GoalLedgerError(f"GOAL_STATE_WRITE_FAILED:{exc}") from exc
            self._append_event(plan, event_name, task_id=task_id, details=details, at=saved_at)
            return plan

    def initialize(self, plan: GoalPlan, *, at: str | None = None) -> GoalPlan:
        with self._lock:
            if self.state_path.exists():
                existing = self.load()
                if existing is None:
                    raise GoalLedgerError("GOAL_STATE_EXISTS_BUT_EMPTY")
                if existing.canonical_hash() != plan.canonical_hash():
                    raise GoalLedgerError("GOAL_STATE_ALREADY_INITIALIZED")
                return existing
            if plan.status != "PLANNED":
                raise GoalTransitionError("GOAL_INIT_REQUIRES_PLANNED")
            return self.save(plan, event_name="goal_plan_initialized", at=at)

    def transition(
        self,
        target_status: str,
        *,
        now: str | None = None,
        **kwargs: Any,
    ) -> GoalPlan:
        with self._lock:
            current = self.require()
            updated = current.transition(target_status, now=now, **kwargs)
            return self.save(
                updated,
                event_name="goal_transition",
                details={
                    "from_status": current.status,
                    "to_status": target_status,
                },
                at=now,
            )

    def record_event(
        self,
        event_name: str,
        *,
        task_id: str | None = None,
        details: Mapping[str, Any] | None = None,
        at: str | None = None,
    ) -> dict[str, Any]:
        """Append a bounded event to the append-only goal ledger."""
        with self._lock:
            plan = self.require()
            timestamp = _check_timestamp(at or utc_now(), "goal_event.at")
            self._append_event(plan, event_name, task_id=task_id, details=details, at=timestamp)
            return {
                "status": "PASS",
                "event": event_name,
                "task_id": task_id,
                "goal_hash": plan.canonical_hash(),
                "at": timestamp,
            }

    def read_events(self) -> dict[str, Any]:
        with self._lock:
            if not self.ledger_path.exists():
                return {
                    "schema": "p2p-goal-event-query/1",
                    "status": "NOT_INITIALIZED",
                    "events": [],
                    "ledger": GOAL_LEDGER_RELATIVE_PATH,
                }
            events: list[dict[str, Any]] = []
            for line in self.ledger_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError:
                    raise GoalLedgerError("GOAL_LEDGER_CORRUPT")
                if not isinstance(payload, Mapping):
                    raise GoalLedgerError("GOAL_LEDGER_CORRUPT")
                events.append(dict(payload))
            return {
                "schema": "p2p-goal-event-query/1",
                "status": "OK",
                "events": events,
                "count": len(events),
                "ledger": GOAL_LEDGER_RELATIVE_PATH,
            }


def _goal_state_lock(store: GoalStateStore) -> threading.RLock:
    key = str(store.state_path.resolve())
    with _GOAL_STATE_LOCKS_GUARD:
        lock = _GOAL_STATE_LOCKS.get(key)
        if lock is None:
            lock = threading.RLock()
            _GOAL_STATE_LOCKS[key] = lock
        return lock
