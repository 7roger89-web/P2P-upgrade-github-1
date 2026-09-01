"""Policy-driven bounded budget model for the P2P Bounded AutoPilot (C33).

Defaults are CONFIG DATA (schema versioned), not hard-coded universal truth.
Budget exhaustion produces an exact durable resume point (BUDGET_BOUNDARY);
the caller never silently continues beyond budget.

No provider/model/vendor logic lives here. Optional cost fields are ready
for adapter evidence but carry no weight in C33 core decisions.
"""
from __future__ import annotations

import copy
import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping

BUDGET_POLICY_SCHEMA = "p2p-autopilot-budget-policy/1"

COST_UNITS_FIELD = "cost_units"
TOKEN_UNITS_FIELD = "token_units"
OPTIONAL_BUDGET_FIELDS = (COST_UNITS_FIELD, TOKEN_UNITS_FIELD)

DEFAULT_POLICY: Mapping[str, Any] = {
    "schema": BUDGET_POLICY_SCHEMA,
    "name": "default",
    "max_waves": 64,
    "max_internal_tasks": 64,
    "max_execution_attempts": 96,
    "max_retry_per_task": 2,
    "max_verification_attempts": 96,
    "max_changed_scope_items": 128,
    "max_concurrent_executions": 1,
    "max_wall_clock_seconds": 7200,
    COST_UNITS_FIELD: None,
    TOKEN_UNITS_FIELD: None,
}


class BudgetExhaustedError(Exception):
    pass


def _clamp(value: Any, minimum: int, maximum: int) -> int:
    try:
        value = int(value)
    except (TypeError, ValueError):
        return minimum
    return max(minimum, min(maximum, value))


def validate_budget_policy(policy: Mapping[str, Any] | None) -> Mapping[str, Any]:
    """Normalize and validate policy; unknown keys preserved, no silent drops. None yields defaults."""
    if policy is None:
        return dict(DEFAULT_POLICY)
    if not isinstance(policy, Mapping):
        raise ValueError("BUDGET_POLICY_INVALID_TYPE")
    if str(policy.get("schema", "")) != BUDGET_POLICY_SCHEMA:
        raise ValueError("BUDGET_POLICY_SCHEMA_INVALID")
    validated = dict(DEFAULT_POLICY)
    validated.update({k: v for k, v in policy.items() if k in DEFAULT_POLICY})
    # policy-only keys preserved under explicit namespace
    extra = {k: v for k, v in policy.items() if k not in DEFAULT_POLICY}
    if extra:
        validated["policy_extras"] = extra
    numeric_keys = (
        "max_waves", "max_internal_tasks", "max_execution_attempts",
        "max_retry_per_task", "max_verification_attempts",
        "max_changed_scope_items", "max_concurrent_executions",
        "max_wall_clock_seconds",
    )
    for key in numeric_keys:
        validated[key] = _clamp(validated[key], 1, 10 ** 9)
    for key in OPTIONAL_BUDGET_FIELDS:
        if validated[key] is not None:
            try:
                validated[key] = float(validated[key])
                if validated[key] < 0:
                    raise ValueError(f"negative {key}")
            except (TypeError, ValueError):
                validated[key] = None
    return validated


class ExecutionUsage:
    """Accumulator for one goal's budget consumption."""

    def __init__(self) -> None:
        self.waves_completed = 0
        self.internal_tasks_completed = 0
        self.execution_attempts = 0
        self.retries = 0
        self.verification_attempts = 0
        self.changed_scope_items = 0
        self.concurrent_executions = 0
        self.active_executions = 0
        self.wall_clock_seconds = 0.0
        self.cost_units = 0.0
        self.token_units = 0.0
        self.last_checkpoint_ref: str | None = None

    def add(self, other: "ExecutionUsage") -> None:
        self.waves_completed += other.waves_completed
        self.internal_tasks_completed += other.internal_tasks_completed
        self.execution_attempts += other.execution_attempts
        self.retries += other.retries
        self.verification_attempts += other.verification_attempts
        self.changed_scope_items += other.changed_scope_items
        self.concurrent_executions = max(self.concurrent_executions, other.concurrent_executions)
        self.active_executions = max(self.active_executions, other.active_executions)
        self.wall_clock_seconds += other.wall_clock_seconds
        self.cost_units += other.cost_units
        self.token_units += other.token_units

    def checkpoint(self, resume_point: str) -> None:
        self.last_checkpoint_ref = str(resume_point)

    def to_mapping(self) -> Mapping[str, Any]:
        return {
            "schema": "p2p-autopilot-usage/1",
            "waves_completed": self.waves_completed,
            "internal_tasks_completed": self.internal_tasks_completed,
            "execution_attempts": self.execution_attempts,
            "retries": self.retries,
            "verification_attempts": self.verification_attempts,
            "changed_scope_items": self.changed_scope_items,
            "concurrent_executions": self.concurrent_executions,
            "active_executions": self.active_executions,
            "wall_clock_seconds": round(self.wall_clock_seconds, 3),
            COST_UNITS_FIELD: round(self.cost_units, 4),
            TOKEN_UNITS_FIELD: round(self.token_units, 4),
            "last_checkpoint_ref": self.last_checkpoint_ref,
        }

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "ExecutionUsage":
        u = cls()
        for field in (
            "waves_completed", "internal_tasks_completed", "execution_attempts",
            "retries", "verification_attempts", "changed_scope_items",
            "concurrent_executions", "active_executions", "wall_clock_seconds",
            COST_UNITS_FIELD, TOKEN_UNITS_FIELD,
        ):
            setattr(u, field, payload.get(field, 0) or 0)
        u.last_checkpoint_ref = payload.get("last_checkpoint_ref")
        return u


class BudgetController:
    """Fail-closed budget controller. Every exhaustion surfaces as a durable
    BUDGET_BOUNDARY resume point via GoalStateStore.transition.
    """

    def __init__(self, policy: Mapping[str, Any] | None = None, usage: ExecutionUsage | None = None) -> None:
        self.policy = validate_budget_policy(policy or DEFAULT_POLICY)
        self.usage = usage if usage is not None else ExecutionUsage()

    # ---- consumption accounting -----------------------------------------

    def record_wave(self, duration_seconds: float = 0.0) -> None:
        self.usage.waves_completed += 1
        self.usage.wall_clock_seconds += float(duration_seconds)

    def record_execution(self, *, retries: int = 0, verification_attempts: int = 0,
                         changed_scope_items: int = 0, duration_seconds: float = 0.0,
                         cost_units: float = 0.0, token_units: float = 0.0) -> None:
        self.usage.execution_attempts += 1
        self.usage.retries += max(0, retries)
        self.usage.verification_attempts += max(0, verification_attempts)
        self.usage.changed_scope_items += max(0, changed_scope_items)
        self.usage.wall_clock_seconds += float(duration_seconds)
        self.usage.cost_units += float(cost_units)
        self.usage.token_units += float(token_units)

    def register_concurrency(self, count: int) -> None:
        self.usage.concurrent_executions = max(self.usage.concurrent_executions, int(count))

    def start_execution(self) -> None:
        """Claim one active in-flight execution slot (fail-closed against the
        concurrent budget)."""
        self.usage.active_executions = max(0, int(self.usage.active_executions) + 1)
        self.usage.concurrent_executions = max(
            int(self.usage.concurrent_executions), self.usage.active_executions)

    def release_execution(self) -> None:
        """Release a claimed slot; never drops below zero."""
        self.usage.active_executions = max(0, int(self.usage.active_executions) - 1)

    # ---- boundary checks -------------------------------------------------

    def can_execute_task(self) -> tuple[bool, str]:
        policy, usage = self.policy, self.usage
        checks = (
            ("max_execution_attempts", usage.execution_attempts),
            ("max_internal_tasks", usage.internal_tasks_completed),
            ("max_waves", usage.waves_completed),
            ("max_verification_attempts", usage.verification_attempts),
            ("max_changed_scope_items", usage.changed_scope_items),
        )
        for key, value in checks:
            limit = policy.get(key)
            if isinstance(limit, int) and value >= limit:
                return False, f"BUDGET_EXHAUSTED:{key}"
        limit = policy.get("max_concurrent_executions")
        if isinstance(limit, int) and usage.active_executions >= limit:
            return False, "BUDGET_EXHAUSTED:max_concurrent_executions"
        limit = policy.get("max_wall_clock_seconds")
        if isinstance(limit, int) and usage.wall_clock_seconds >= float(limit):
            return False, "BUDGET_EXHAUSTED:max_wall_clock_seconds"
        return True, "OK"

    def task_retry_budget(self) -> int:
        return max(0, int(self.policy.get("max_retry_per_task", 0)))

    def resume_point(self, *, task_id: str | None = None, phase: str = "SELECT_NEXT_SAFE_TASK",
                     evidence_ref: str | None = None) -> str:
        ref = {
            "schema": "p2p-autopilot-resume-point/1",
            "phase": phase,
            "task_id": task_id,
            "evidence_ref": evidence_ref,
            "usage_snapshot": dict(self.usage.to_mapping()),
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        }
        ref["resume_ref"] = "resume-" + hashlib.sha256(json.dumps({k: v for k, v in ref.items()}, sort_keys=True).encode()).hexdigest()[:16]
        return json.dumps(ref, sort_keys=True)

    def boundary(self, task_id: str, phase: str) -> str:
        ok, reason = self.can_execute_task()
        if ok:
            raise ValueError("NOT_EXHAUSTED")
        resume = self.resume_point(task_id=task_id, phase=phase)
        self.usage.checkpoint(json.loads(resume)["resume_ref"])
        return resume  # caller persists via GoalStateStore.transition("BUDGET_BOUNDARY", resume_point=...)

    def to_mapping(self) -> Mapping[str, Any]:
        return {"schema": "p2p-autopilot-budget-state/1", "policy": dict(self.policy), "usage": self.usage.to_mapping()}
