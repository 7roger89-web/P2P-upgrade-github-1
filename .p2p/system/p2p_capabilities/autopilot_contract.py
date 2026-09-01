"""Bounded per-task execution contract builder for the C33 AutoPilot.

Builds the contract from durable state (goal plan, task record, policy).
The executor never receives authority wider than the goal/task contract:
composition NEVER widens permission (C15 never-widen subset semantics).

Decision-trace integration: material contract decisions emit a
decision_trace_record-compatible structured event (reuse of
.p2p.system.p2p_capabilities.decision_trace DECISION_TYPES vocabulary plus
the bounded C33 reason set), never hidden chain-of-thought.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping

from .autopilot_budget import validate_budget_policy
from .fake_execution_backend import (
    CONTRACT_SCHEMA, FORBIDDEN_ACTIONS_DEFAULT, ALLOWED_TOOLS_DEFAULT,
)

CONTRACT_BUILDER_SCHEMA = "p2p-autopilot-contract-builder/1"
REASON_SET = (
    "TASK_SELECTED", "TASK_REJECTED_SCOPE", "DEPENDENCY_BLOCKED",
    "TARGET_INELIGIBLE", "PERMISSION_BLOCKED", "OWNER_GATE_SELECTED",
    "CONTINUE_SELECTED", "BUDGET_BOUNDARY", "VERIFY_FAILED",
    "RECOVERY_REVERIFY", "PORTABLE_HANDOFF_SELECTED", "TASK_DONE", "GOAL_DONE",
)

# Reuse existing decision-trace decision types where equivalent
DECISION_TYPE_FOR_REASON = {
    "TASK_SELECTED": "DATA",
    "TASK_REJECTED_SCOPE": "SECURITY",
    "DEPENDENCY_BLOCKED": "DATA",
    "TARGET_INELIGIBLE": "DEPENDENCY",
    "PERMISSION_BLOCKED": "SECURITY",
    "OWNER_GATE_SELECTED": "PRODUCT",
    "CONTINUE_SELECTED": "DATA",
    "BUDGET_BOUNDARY": "DEPENDENCY",
    "VERIFY_FAILED": "EXCEPTION",
    "RECOVERY_REVERIFY": "EXCEPTION",
    "PORTABLE_HANDOFF_SELECTED": "DEPENDENCY",
    "TASK_DONE": "DATA",
    "GOAL_DONE": "GOVERNANCE",
}


class ContractDecisionTrace:
    """Bounded structured decision-trace recorder for AutoPilot decisions."""

    def __init__(self) -> None:
        self._events: list[Mapping[str, Any]] = []

    def record(self, *, reason: str, inputs: Iterable[str] = (), evidence_refs: Iterable[str] = (),
               outcome: str, gate: str | None = None, decision_id: str | None = None) -> Mapping[str, Any]:
        if reason not in REASON_SET:
            raise ValueError(f"CONTRACT_REASON_INVALID:{reason}")
        now = datetime.now(timezone.utc).isoformat()
        payload = {
            "schema": "p2p-decision-trace/1",
            "decision_type": DECISION_TYPE_FOR_REASON[reason],
            "decision": reason,
            "decision_id": decision_id or hashlib.sha256(
                json.dumps({"reason": reason, "outcome": outcome, "at": now}, sort_keys=True).encode()
            ).hexdigest()[:16],
            "inputs": tuple(str(x) for x in inputs),
            "evidence_refs": tuple(str(x) for x in evidence_refs),
            "outcome": outcome,
            "gate_ref": gate,
            "recorded_at": now,
            "notes": "",  # structured codes only; no hidden chain-of-thought
        }
        self._events.append(payload)
        return payload

    @property
    def events(self) -> list[Mapping[str, Any]]:
        return list(self._events)

    def reset(self) -> None:
        self._events = []


def _subset_of(child: tuple, parent: tuple) -> bool:
    return all(item in parent for item in child)


def compose_permission_profile(goal_profile: Iterable[str], task_profile: Iterable[str],
                               registry_profile: Iterable[str]) -> tuple[str, ...]:
    """Compose permission envelope: equal or NARROWER than its parent. Never wider."""
    parent = tuple(registry_profile)
    allowed = tuple(item for item in tuple(goal_profile) if item in parent)
    allowed = tuple(item for item in tuple(task_profile) if item in allowed)
    if not allowed:
        raise ValueError("PERMISSION_COMPOSITION_EMPTY:goal profile allows nothing")
    return allowed


class TaskContractBuilder:
    """Builds bounded per-task contracts from durable goal/task state."""

    def __init__(self, *, goal_id: str, goal_scope: tuple[str, ...],
                 goal_non_scope: tuple[str, ...] = (),
                 registry_permissions: tuple[str, ...] = ("read", "write", "run-tests", "diff"),
                 registry_toolset: tuple[str, ...] = tuple(ALLOWED_TOOLS_DEFAULT),
                 registry_targets: tuple[str, ...] = (),
                 budget_policy: Mapping[str, Any] | None = None) -> None:
        self.goal_id = str(goal_id)
        self.goal_scope = tuple(goal_scope)
        self.goal_non_scope = tuple(goal_non_scope)
        self.registry_permissions = tuple(registry_permissions)
        self.registry_toolset = tuple(registry_toolset)
        self.registry_targets = tuple(registry_targets)
        self.budget_policy = validate_budget_policy(budget_policy)
        self.tracer = ContractDecisionTrace()

    # ---- C18/C19 context consumption -------------------------------------

    def context_sufficient(self, context_class: str, coverage: tuple[tuple[str, str], ...] = ()) -> bool:
        """Fail closed: only MINIMAL/STANDARD/EXPANDED are sufficient.
        CONTEXT_INSUFFICIENT/BLOCKED always fail closed (section E addendum)."""
        if context_class in ("CONTEXT_INSUFFICIENT", "BLOCKED"):
            return False
        if context_class not in ("MINIMAL", "STANDARD", "EXPANDED"):
            return False
        for requirement, status in coverage:
            if status not in ("COVERED", "NOT_APPLICABLE") and requirement in ("REQUIRED",):
                return False
        return True

    # ---- contract building ------------------------------------------------

    def build(self, task_id: str, task_objective: str, *,
              workspace: str, execution_target: str,
              task_permissions: tuple[str, ...] = (),
              task_toolset: tuple[str, ...] = (),
              expected_output: tuple[str, ...] = (),
              verify_spec: tuple[str, ...] = (),
              input_evidence_pointers: tuple[str, ...] = (),
              retry_budget: int | None = None,
              context_class: str = "STANDARD",
              coverage: tuple[tuple[str, str], ...] = ()) -> Mapping[str, Any]:
        if not self.context_sufficient(context_class, coverage):
            self.tracer.record(
                reason="TASK_REJECTED_SCOPE",
                inputs=(task_id, f"context:{context_class}"),
                outcome="REJECTED_CONTEXT_INSUFFICIENT",
            )
            raise ValueError("TASK_CONTEXT_INSUFFICIENT:planner may not guess; fail closed")

        # scope enforcement: task objective text vs approved scope
        objective_lower = task_objective.lower()
        for fragment in self.goal_non_scope:
            if str(fragment).lower() in objective_lower:
                self.tracer.record(reason="TASK_REJECTED_SCOPE", inputs=(task_id,),
                                   outcome="REJECTED_SCOPE_VIOLATION", gate="NO_SCOPE_EXPANSION")
                raise ValueError("TASK_REJECTED_SCOPE_VIOLATION")

        allowed_permissions = compose_permission_profile(
            goal_profile=tuple(task_permissions) or self.registry_permissions,
            task_profile=tuple(task_permissions) or self.registry_permissions,
            registry_profile=self.registry_permissions,
        )
        allowed_toolset = tuple(task_toolset) if task_toolset and _subset_of(task_toolset, self.registry_toolset) else self.registry_toolset

        target_eligible = bool(self.registry_targets) and execution_target in self.registry_targets
        if not target_eligible:
            self.tracer.record(reason="TARGET_INELIGIBLE", inputs=(task_id, execution_target),
                               outcome="BLOCKED_NO_ELIGIBLE_TARGET")
            raise ValueError("TARGET_INELIGIBLE:registry only; no routing")

        budget = {
            "execution_attempts": int(self.budget_policy.get("max_execution_attempts", 96)),
            "retry": max(0, int(self.budget_policy.get("max_retry_per_task", 2))),
            "verification_attempts": int(self.budget_policy.get("max_verification_attempts", 96)),
        }
        if retry_budget is not None:
            budget["retry"] = max(0, min(budget["retry"], int(retry_budget)))

        contract = {
            "schema": CONTRACT_SCHEMA,
            "goal_id": self.goal_id,
            "task_id": str(task_id),
            "task_objective": str(task_objective),
            "allowed_scope": tuple(self.goal_scope),
            "allowed_toolset": allowed_toolset,
            "workspace": str(workspace),
            "permission_profile": tuple(allowed_permissions),
            "execution_target": str(execution_target),
            "input_evidence_pointers": tuple(input_evidence_pointers),
            "expected_output": tuple(expected_output),
            "verify_spec": tuple(verify_spec),
            "task_budget": budget,
            "retry_budget": budget["retry"],
            "forbidden_actions": tuple(FORBIDDEN_ACTIONS_DEFAULT),
            "context_class": context_class,
        }
        self.tracer.record(reason="TASK_SELECTED", inputs=(task_id, execution_target),
                           evidence_refs=tuple(input_evidence_pointers), outcome="CONTRACT_BUILT")
        return contract

    def contract_fingerprint(self, contract: Mapping[str, Any]) -> str:
        keys = ("goal_id", "task_id", "workspace", "permission_profile", "execution_target",
                "verify_spec", "allowed_scope", "forbidden_actions", "schema")
        return hashlib.sha256(json.dumps({k: contract[k] for k in keys}, sort_keys=True).encode()).hexdigest()[:32]
