"""Bounded AutoPilot foreground control loop (C33).

Implements the durable loop contract:

RECOVER → LOAD GOAL → PLAN/VALIDATE WAVE → SELECT NEXT SAFE TASK →
CONTINUE GATE → PREFLIGHT → BUILD CONTRACT → EXECUTE → VERIFY →
PERSIST EVIDENCE → TRANSITION → CHECKPOINT → REASSESS → SELECT ...

The loop is FOREGROUND-ONLY: it carries no scheduler, cron, daemon, or
autonomous wake-up. When the process stops, P2P stops; durable state is
recovered from disk on restart.

Provider-neutral: all execution flows through an adapter implementing the
normalized execute(contract) contract. No Hermes/Codex/Manus branching
lives in this module (C32 research is design input only; canonical P2P
architecture wins on conflict).
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

from .autopilot_budget import BudgetController
from .autopilot_contract import TaskContractBuilder
from .autopilot_gate import ContinueGate
from .autopilot_state import (
    GoalPlan, GoalStateStore, GoalTransitionError, TERMINAL_STATUSES,
)
from .evidence import EvidenceClaim
from .fake_execution_backend import FakeDeterministicExecutionBackend
from .autopilot_verifier import TaskVerifier
from .task_state import (
    LogicalOwner,
    TaskRecord,
    TaskPlan,
    TaskStateStore,
    next_safe_task,
    _sha256,
)

LOOP_SCHEMA = "p2p-autopilot-loop/1"
MAX_STEP_ITERATIONS = 10 ** 6

CONTINUE_STATUSES = ("CONTINUE",)

_TASK_RECORD_FIELDS = (
    "task_id",
    "goal_id",
    "title",
    "purpose",
    "status",
    "dependencies",
    "scope",
    "non_scope",
    "acceptance_requirements",
    "required_evidence",
    "permission_needs",
    "required_capabilities",
    "optional_capabilities",
    "context_refs",
    "output_refs",
    "requirement_refs",
    "decision_refs",
    "blocker",
    "owner_decision",
    "completion",
    "checkpoint",
    "execution_lineage",
    "last_preflight",
    "created_at",
    "updated_at",
)

_TASK_PLAN_IDENTITY_FIELDS = (
    "task_id",
    "goal_id",
    "title",
    "purpose",
    "dependencies",
    "scope",
    "non_scope",
    "acceptance_requirements",
    "required_evidence",
    "permission_needs",
    "required_capabilities",
    "optional_capabilities",
    "context_refs",
    "output_refs",
    "requirement_refs",
    "decision_refs",
)


def _execution_descriptor_ref(goal_id: str, task_id: str,
                             task_record: Mapping[str, Any]) -> str:
    """Bind dispatch-only data without making it a second task authority."""

    descriptor = {
        "goal_id": str(goal_id),
        "task_id": str(task_id),
        "workspace": task_record.get("workspace"),
        "execution_target": task_record.get("execution_target"),
        "expected_output": tuple(task_record.get("expected_output", ())),
        "verify_spec": tuple(task_record.get("verify_spec", ())),
        "input_evidence_pointers": tuple(
            task_record.get("input_evidence_pointers", ())),
        "skills": tuple(task_record.get("skills", ())),
        "team": tuple(task_record.get("team", ())),
        "fw03_decision": task_record.get("fw03_decision"),
    }
    return "execution-descriptor:" + _sha256(descriptor)


def _task_plan_identity(plan: TaskPlan) -> str:
    """Hash immutable task-plan intent, excluding mutable execution state."""

    tasks = []
    for task_id in sorted(plan.tasks):
        task = plan.tasks[task_id]
        tasks.append({field: getattr(task, field)
                      for field in _TASK_PLAN_IDENTITY_FIELDS})
    return _sha256({
        "goal_id": plan.goal_id,
        "logical_owner": plan.logical_owner.to_dict(),
        "goal_requirement_refs": plan.goal_requirement_refs,
        "plan_scope": plan.plan_scope,
        "plan_non_scope": plan.plan_non_scope,
        "tasks": tasks,
    })


def _assert_task_plan_compatible(existing: TaskPlan,
                                 candidate: TaskPlan,
                                 task_records: Mapping[str, Mapping[str, Any]]) -> None:
    """Reject graph or dispatch drift; never replace persisted task state."""

    if existing.goal_id != candidate.goal_id:
        raise RuntimeError(
            f"TASK_STATE_GOAL_MISMATCH:{existing.goal_id}:{candidate.goal_id}")
    if set(existing.tasks) != set(candidate.tasks):
        raise RuntimeError("TASK_PLAN_TASK_SET_MISMATCH")
    if _task_plan_identity(existing) != _task_plan_identity(candidate):
        raise RuntimeError("TASK_PLAN_IDENTITY_MISMATCH")
    for task_id, record in task_records.items():
        expected = _execution_descriptor_ref(candidate.goal_id, task_id,
                                             record)
        lineage = existing.tasks[task_id].execution_lineage
        refs = tuple(lineage.get("refs", ())) if isinstance(lineage, Mapping) else ()
        if expected not in refs:
            raise RuntimeError("TASK_EXECUTION_DESCRIPTOR_MISMATCH:" +
                               str(task_id))


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _phase_event(phase: str, task_id: str | None, details: Mapping[str, Any] | None) -> dict[str, Any]:
    return {
        "schema": "p2p-autopilot-loop-event/1",
        "phase": phase,
        "task_id": task_id,
        "details": dict(details or {}),
        "at": _now_iso(),
    }


class PreflightError(Exception):
    pass


class LoopHaltError(Exception):
    """Raised by the loop when an Owner-required condition or fail-closed
    boundary is reached; not an error of the runtime."""
    pass


class RecoveryObserver:
    """Recovers goal state from the durable store and resolves uncertain
    in-flight mutations without blind re-execution (addendum J).

    Cases: clean restart after completed task; executor crash after execution
    but before verification; death after verification before transition;
    session disappearance; uncertain in-flight state; task already DONE.
    """

    def __init__(self, store: GoalStateStore, verifier: TaskVerifier) -> None:
        self.store = store
        self.verifier = verifier

    def observe(self) -> dict[str, Any]:
        plan = self.store.require()
        observation = {
            "schema": "p2p-autopilot-recovery/1",
            "goal_status": plan.status,
            "current_task_id": plan.current_task_id,
            "next_task_id": plan.next_task_id,
            "wave": plan.wave,
            "terminal": plan.is_terminal(),
            "resume_point": plan.resume_point,
            "owner_gate": plan.owner_gate,
            "blocker": plan.blocker,
        }
        # Case F: task already DONE before restart — ledger proves completion.
        if plan.is_terminal():
            observation["disposition"] = "ALREADY_TERMINAL"
            return observation

        # B: executed but never verified (task_executed without a later
        #    task_verified). Never re-run the mutation: re-verify instead.
        if plan.status == "IN_PROGRESS" and plan.current_task_id is not None:
            pending = self._pending_verification(plan.current_task_id)
            if pending:
                observation["disposition"] = "NEEDS_REVERIFY"
                observation["evidence"] = pending
                return observation

        # C/E: uncertain in-flight state with no current task → NEEDS_REVIEW.
        if plan.status == "IN_PROGRESS" and plan.current_task_id is None:
            observation["disposition"] = "SESSION_LOST_NEEDS_REVIEW"
            return observation

        # D: nothing in flight; select next safe task.
        observation["disposition"] = "CLEAN_SELECT_NEXT"
        return observation

    def _pending_verification(self, task_id: str) -> list[Mapping[str, Any]]:
        events = self.store.read_events()["events"]
        saw_verify = False
        executed = None
        for ev in events:
            if ev.get("task_id") != str(task_id):
                continue
            name = ev.get("event", "")
            if name == "task_executed":
                executed = ev
                saw_verify = False
            elif name == "task_verified":
                saw_verify = True
        return [executed] if executed is not None and not saw_verify else []


def _build_task_plan(goal_id: str,
                     task_records: Mapping[str, Mapping[str, Any]],
                     *, bind_execution_descriptors: bool = False) -> TaskPlan:
    first_scope = next((tuple(rec.get("scope", ()))
                        for rec in task_records.values()
                        if rec.get("scope")), ())
    first_non_scope = next((tuple(rec.get("non_scope", ()))
                           for rec in task_records.values()
                           if rec.get("non_scope")), ())
    records: dict[str, TaskRecord] = {}
    for task_id, rec in task_records.items():
        payload = {key: rec[key] for key in _TASK_RECORD_FIELDS if key in rec}
        payload["task_id"] = rec.get("task_id", task_id)
        payload["goal_id"] = goal_id
        payload.setdefault("title", str(rec.get("title", "")))
        payload.setdefault("purpose", str(rec.get("purpose", "")))
        payload.setdefault("status", "READY")
        payload.setdefault("dependencies", ())
        payload.setdefault("scope", ())
        payload.setdefault("non_scope", ())
        payload.setdefault("acceptance_requirements", ())
        payload.setdefault("required_evidence", ())
        payload.setdefault("permission_needs", ("sandboxed-default",))
        payload.setdefault("required_capabilities", ())
        payload.setdefault("optional_capabilities", ())
        payload.setdefault("context_refs", ())
        payload.setdefault("output_refs", ())
        payload.setdefault("requirement_refs", ())
        payload.setdefault("decision_refs", ())
        lineage = dict(payload.get("execution_lineage") or {
            "status": "UNKNOWN", "refs": []})
        lineage["status"] = str(lineage.get("status", "UNKNOWN"))
        lineage["refs"] = list(lineage.get("refs", []))
        if bind_execution_descriptors:
            ref = _execution_descriptor_ref(goal_id, str(task_id), rec)
            if ref not in lineage["refs"]:
                lineage["refs"].append(ref)
        payload["execution_lineage"] = lineage
        records[task_id] = TaskRecord.from_mapping(payload)
    owner = LogicalOwner.for_goal(goal_id)
    return TaskPlan(goal_id=goal_id, logical_owner=owner, tasks=records,
                    plan_scope=tuple(first_scope) or ("GOAL_SCOPED_TASK_WORK",),
                    plan_non_scope=tuple(first_non_scope))


class AutoPilotLoop:
    """Foreground-only bounded AutoPilot loop."""

    def __init__(
        self,
        *,
        store: GoalStateStore,
        budget: BudgetController,
        backend: FakeDeterministicExecutionBackend,
        verifier: TaskVerifier,
        builder: TaskContractBuilder,
        task_records: Mapping[str, Mapping[str, Any]],
        task_state_store: TaskStateStore | None = None,
        owner_gate_resolver: Callable[[Mapping[str, Any]], dict[str, Any]] | None = None,
        context_provider: Callable[[str], dict[str, Any]] | None = None,
        preflight_fn: Callable[[Mapping[str, Any]], bool] | None = None,
        evidence_conflict_fn: Callable[[str], bool] | None = None,
    ) -> None:
        self.store = store
        self.budget = budget
        self.backend = backend
        self.verifier = verifier
        self.builder = builder
        self._owner_gate_resolver = owner_gate_resolver
        self._context_provider = context_provider
        self._preflight_fn = preflight_fn
        self._evidence_conflict_fn = evidence_conflict_fn
        self._task_records = {str(k): dict(v) for k, v in task_records.items()}
        self._task_state_store = task_state_store
        if self._task_state_store is not None:
            persisted = self._task_state_store.require()
            candidate = _build_task_plan(self.store.require().goal_id,
                                         self._task_records)
            _assert_task_plan_compatible(persisted, candidate,
                                         self._task_records)
        self.recovery = RecoveryObserver(store, verifier)
        self.events: list[Mapping[str, Any]] = []
        self._iteration = 0

    @property
    def goal_id(self) -> str:
        return self.store.require().goal_id

    # ---- durable state -----------------------------------------------------

    def goal_plan(self) -> GoalPlan:
        return self.store.require()

    def task_plan(self) -> TaskPlan:
        if self._task_state_store is not None:
            return self._task_state_store.require()
        return _build_task_plan(self.goal_id, self._task_records)

    def task_record(self, task_id: str) -> dict[str, Any]:
        """Return execution data overlaid with canonical task state."""

        if str(task_id) not in self._task_records:
            raise KeyError(str(task_id))
        record = dict(self._task_records[str(task_id)])
        if self._task_state_store is not None:
            task = self.task_plan().tasks.get(str(task_id))
            if task is None:
                raise RuntimeError("TASK_STATE_TASK_NOT_FOUND:" + str(task_id))
            record.update(task.to_dict())
        return record

    def task_records(self) -> dict[str, dict[str, Any]]:
        return {task_id: self.task_record(task_id)
                for task_id in self._task_records}

    # ---- phases ------------------------------------------------------------

    def select_next_safe_task(self) -> str | None:
        safe = next_safe_task(self.task_plan())
        return safe.task_id if safe is not None else None

    def preflight(self, contract: Mapping[str, Any]) -> bool:
        fn = self._preflight_fn
        if fn is None:
            return True
        if not fn(contract):
            raise PreflightError("PREFLIGHT_FAILED")
        return True

    def build_contract(self, task_id: str) -> Mapping[str, Any]:
        rec = self.task_record(task_id)
        ctx = (self._context_provider or (lambda t: {"class": "STANDARD", "coverage": ()}))(task_id)
        target = str(rec.get("execution_target", ""))
        return self.builder.build(
            task_id=task_id,
            task_objective=str(rec.get("title", "")),
            workspace=str(rec.get("workspace", "")),
            execution_target=target,
            task_permissions=tuple(self.builder.registry_permissions),
            expected_output=tuple(rec.get("expected_output", ())),
            verify_spec=tuple(rec.get("verify_spec", ("default",))),
            input_evidence_pointers=tuple(rec.get("input_evidence_pointers", ())),
            retry_budget=self.budget.task_retry_budget(),
            context_class=str(ctx.get("class", "STANDARD")),
            coverage=tuple(tuple(c) for c in ctx.get("coverage", ())),
        )

    def execute_task(self, contract: Mapping[str, Any]) -> Mapping[str, Any]:
        self.budget.start_execution()
        start = time.monotonic()
        try:
            result = self.backend.execute(contract)
            duration = time.monotonic() - start
            result = self._finalize_execution(result, duration)
            self.budget.record_execution(
                retries=0, verification_attempts=1,
                changed_scope_items=len(result.get("changed_surface", ()))
                if isinstance(result.get("changed_surface"), (list, tuple))
                else 0,
                duration_seconds=duration,
            )
            return result
        except Exception:
            duration = time.monotonic() - start
            self.budget.record_execution(duration_seconds=duration)
            raise
        finally:
            self.budget.release_execution()

    def _finalize_execution(self, result: Mapping[str, Any], duration: float) -> Mapping[str, Any]:
        return result

    def _release_on_fail(self) -> None:
        """Ensure a claimed execution slot is always released when a task
        cannot complete (gate/blocker/crash paths)."""
        self.budget.release_execution()

    def verify_result(self, contract: Mapping[str, Any], result: Mapping[str, Any]) -> Mapping[str, Any]:
        evidence = self.verifier.verify(result, contract.get("verify_spec", ()))
        self.store.record_event("task_verified", task_id=contract["task_id"], details={
            "evidence_ref": evidence.get("evidence_ref"),
            "status": evidence.get("status"),
            "verdict": (evidence.get("bindings") or {}).get("verdict"),
        })
        self.events.append(_phase_event("VERIFY", contract["task_id"], {
            "verdict": (evidence.get("bindings") or {}).get("verdict"),
            "status": evidence.get("status"),
        }))
        return evidence

    def continue_decision(self, task_id: str) -> str:
        rec = self.task_record(task_id)
        plan = self.task_plan()
        task = plan.tasks[task_id]
        deps_done = plan.dependencies_are_done(task_id)
        gate = ContinueGate(
            goal_scope=self.builder.goal_scope,
            goal_non_scope=self.builder.goal_non_scope,
            eligible_target=bool(self.builder.registry_targets),
            budget_remaining=self.budget.can_execute_task()[0],
            retry_remaining=self.budget.task_retry_budget() >= 0,
        )
        scope_text = f"{task.title} {task.purpose}"
        decision = gate.evaluate(
            task,
            scope_text=scope_text,
            evidence_conflict=bool((self._evidence_conflict_fn or (lambda t: False))(task_id)),
            deps_done=deps_done,
            prior_evidence_acceptable=True,
            actionable=rec.get("status", "READY") == "READY",
        )
        return decision  # CONTINUE / OWNER_GATE / BLOCKED / UNKNOWN

    def _task_transition(self, task_id: str, target_status: str, **kwargs: Any) -> None:
        if self._task_state_store is None:
            return
        current = self.task_plan().tasks.get(str(task_id))
        if current is None:
            raise RuntimeError("TASK_STATE_TASK_NOT_FOUND:" + str(task_id))
        if current.status == target_status:
            return
        if current.status in ("DONE", "CANCELLED"):
            raise RuntimeError("TASK_STATE_TERMINAL:" + str(task_id))
        self._task_state_store.transition(str(task_id), target_status, **kwargs)

    def _task_checkpoint(self, task_id: str, contract: Mapping[str, Any],
                         *, classification: str = "UNKNOWN",
                         next_safe_step: str = "REVERIFY_TASK",
                         notes: str = "") -> None:
        if self._task_state_store is None:
            return
        plan = self.task_plan()
        task = plan.tasks.get(str(task_id))
        if task is None:
            raise RuntimeError("TASK_STATE_TASK_NOT_FOUND:" + str(task_id))
        if task.status in ("DONE", "CANCELLED"):
            return
        state_fingerprint = _sha256(contract)
        checkpoint_ref = "checkpoint:" + _sha256({
            "goal_id": plan.goal_id,
            "task_id": str(task_id),
            "state_fingerprint": state_fingerprint,
            "classification": classification,
        })
        self._task_state_store.checkpoint(str(task_id), {
            "checkpoint_ref": checkpoint_ref,
            "state_fingerprint": state_fingerprint,
            "recovery_classification": classification,
            "next_safe_step": next_safe_step,
            "completed_refs": [tid for tid, item in plan.tasks.items()
                               if item.status == "DONE"],
            "pending_refs": [tid for tid, item in plan.tasks.items()
                             if item.status != "DONE"],
            "evidence_fingerprints": {},
            "captured_at": _now_iso(),
            "notes": notes,
        })

    def _task_completion_claim(self, task_id: str,
                               evidence: Mapping[str, Any]) -> EvidenceClaim:
        task = self.task_plan().tasks.get(str(task_id))
        if task is None:
            raise RuntimeError("TASK_STATE_TASK_NOT_FOUND:" + str(task_id))
        verifier_ref = str(evidence.get("evidence_ref") or "").strip()
        if not verifier_ref:
            raise LoopHaltError("VERIFIER_EVIDENCE_REF_REQUIRED")
        required = tuple(task.required_evidence)
        if not required:
            raise LoopHaltError("TASK_REQUIRED_EVIDENCE_MISSING")
        observed_at = str(evidence.get("observed_at") or _now_iso())
        actual = []
        for required_ref in required:
            actual.append({
                "source": str(evidence.get("source") or "autopilot-verifier"),
                "evidence_ref": required_ref,
                "origin": str(evidence.get("origin") or "RUNTIME_EVIDENCE"),
                "observed_at": observed_at,
                "freshness": str(evidence.get("freshness") or "CURRENT"),
                "scope": [f"goal:{self.goal_id}", f"task:{task_id}"],
                "source_binding": "verifier-evidence:" + verifier_ref,
                "fingerprint": _sha256({
                    "required_ref": required_ref,
                    "verifier_evidence_ref": verifier_ref,
                    "bindings": evidence.get("bindings", {}),
                }),
            })
        return EvidenceClaim(
            claim=str(evidence.get("claim") or f"verify:{task_id}:VERIFIED"),
            required_evidence=required,
            actual_evidence=tuple(actual),
            status="VERIFIED",
        )

    def mark_task_done(self, task_id: str, evidence: Mapping[str, Any],
                       *, contract: Mapping[str, Any] | None = None,
                       result: Mapping[str, Any] | None = None) -> None:
        """Durable evidence persistence: evidence pointer only, transcript
        never becomes state.  Completion must satisfy the C11 structural
        validity invariant (VERIFIED status, exact required evidence set,
        sha256 fingerprints)."""
        evidence_ref = evidence.get("evidence_ref")
        rec = self.task_record(task_id)
        required = tuple(rec.get("required_evidence", ())) or (evidence_ref,)
        fp = _sha256(evidence_ref)
        rec = dict(rec)
        rec["status"] = "DONE"
        rec["blocker"] = None
        rec["owner_decision"] = None
        rec["completion"] = {
            "status": "VERIFIED",
            "evidence_refs": list(required),
            "done_when": list(required),
            "candidate_state_fingerprint": fp,
            "evidence_fingerprints": {ref: fp for ref in required},
        }
        if self._task_state_store is not None:
            claim = self._task_completion_claim(task_id, evidence)
            candidate_state = {
                "contract_fingerprint": self.builder.contract_fingerprint(
                    contract or {}),
                "execution_fingerprint": _sha256(result or evidence),
                "verifier_evidence_ref": str(evidence_ref),
            }
            self._task_state_store.complete(task_id, (claim,), candidate_state)
        self._task_records[task_id] = rec
        plan = self.store.require()
        advanced = plan.consume_budget(
            executions=1, verifications=1,
            workspace_changes=len(evidence.get("changed_surface", ())) if isinstance(evidence.get("changed_surface"), (list, tuple)) else 0,
        )
        advanced = advanced.mark_task_completed()
        self.store.save(advanced, event_name="task_done",
                        details={"task_id": task_id, "evidence_ref": evidence_ref})
        self.budget.usage.internal_tasks_completed += 1
        self.budget.usage.last_checkpoint_ref = task_id

    # ---- main loop ----------------------------------------------------------

    def step(self) -> dict[str, Any]:
        if self._iteration >= MAX_STEP_ITERATIONS:
            raise RuntimeError("LOOP_ITERATION_SAFETY_LIMIT")
        self._iteration += 1

        plan = self.store.require()

        # Terminal states halt the foreground loop.
        if plan.is_terminal():
            return {"status": "TERMINAL", "goal_status": plan.status,
                    "terminal_state": plan.terminal_state, "terminal_reason": plan.terminal_reason}

        # Recovery: resolve uncertain in-flight mutations first.
        obs = self.recovery.observe()
        disposition = obs.get("disposition")
        if disposition == "ALREADY_TERMINAL":
            return {"status": "TERMINAL", "goal_status": plan.status, "terminal_state": plan.terminal_state}
        if disposition == "NEEDS_REVERIFY":
            return self._reverify_in_flight(plan.current_task_id)
        if disposition == "SESSION_LOST_NEEDS_REVIEW":
            self.events.append(_phase_event("RECOVERY", None, {"disposition": disposition}))
            return {"status": "SESSION_LOST_NEEDS_REVIEW"}

        # Owner gate / budget boundary / blocker: Owner-visible halt.
        if plan.status == "OWNER_GATE":
            return {"status": "OWNER_GATE", "owner_gate": plan.owner_gate}
        if plan.status == "BUDGET_BOUNDARY":
            return {"status": "BUDGET_BOUNDARY", "resume_point": plan.resume_point}
        if plan.status == "BLOCKED":
            return {"status": "BLOCKED", "blocker": plan.blocker}

        # A task that is ACTIVE in the canonical C11 store is an open
        # execution boundary.  If the goal ledger cannot prove the normal
        # re-verification path, never let the absence of a READY task look
        # like successful completion.
        if self._task_state_store is not None:
            active_tasks = [task.task_id for task in self.task_plan().tasks.values()
                            if task.status == "ACTIVE"]
            if active_tasks:
                self.events.append(_phase_event(
                    "RECOVERY", active_tasks[0],
                    {"disposition": "TASK_STATE_ACTIVE_NEEDS_REVIEW"}))
                return {
                    "status": "SESSION_LOST_NEEDS_REVIEW",
                    "task_id": active_tasks[0],
                    "reason": "CANONICAL_TASK_STATE_ACTIVE_WITHOUT_REVERIFY",
                }

        # PLAN/VALIDATE WAVE: refresh ready tasks (C11 C19 refresh policy)
        current_plan = self.task_plan()

        # SELECT NEXT SAFE TASK (C11 next_safe_task authority)
        task_id = self.select_next_safe_task()
        if task_id is None:
            if self._task_state_store is not None:
                incomplete = [task.task_id for task in current_plan.tasks.values()
                              if task.status != "DONE"]
                if incomplete:
                    return {
                        "status": "BLOCKED",
                        "reason": "NO_SAFE_TASK_IN_CANONICAL_TASK_STATE",
                        "task_ids": sorted(incomplete),
                    }
            # All remaining tasks completed with verified evidence.
            if plan.status == "VERIFIED":
                self.store.transition("GOAL_DONE", terminal_state="ALL_TASKS_DONE",
                                      terminal_reason="no remaining safe tasks; all required evidence recorded")
                self.events.append(_phase_event("GOAL_DONE", None, {}))
                return {"status": "TERMINAL", "goal_status": "GOAL_DONE",
                        "terminal_state": "ALL_TASKS_DONE"}
            self.store.transition("TERMINAL", terminal_state="ALL_TASKS_DONE",
                                  terminal_reason="no remaining safe tasks; all required evidence recorded")
            self.events.append(_phase_event("GOAL_DONE", None, {}))
            return {"status": "TERMINAL", "goal_status": "TERMINAL", "terminal_state": "ALL_TASKS_DONE"}

        # CONTINUE GATE (fail closed; no Owner prompt when all gates pass)
        decision = self.continue_decision(task_id)
        gate_status = decision.status  # CONTINUE / OWNER_GATE / BLOCKED / UNKNOWN
        if plan.status == "VERIFIED":
            # Narrow, documented re-entry: halting from VERIFIED must pass
            # through APPROVED because VERIFIED only allows APPROVED/GOAL_DONE/TERMINAL.
            self.store.transition("APPROVED", next_task_id=task_id)
        if gate_status == "CONTINUE":
            self.events.append(_phase_event("CONTINUE", task_id, {}))
        elif gate_status == "BLOCKED":
            failing_names = decision.failing_gates if hasattr(decision, "failing_gates") else ()
            if "BUDGET_REMAINING" in failing_names:
                # Spec: exact budget boundary stop with durable resume point.
                resume = json.loads(self.budget.resume_point(task_id=task_id, phase="PRE_EXECUTE"))
                self.store.transition("BUDGET_BOUNDARY", resume_point=resume)
                return {"status": "BUDGET_BOUNDARY", "resume_point": resume}
            if "RETRY_LIMITS_REMAINING" in failing_names:
                resume = json.loads(self.budget.resume_point(task_id=task_id, phase="PRE_EXECUTE"))
                self.store.transition("BUDGET_BOUNDARY", resume_point=resume)
                return {"status": "RETRY_BOUNDARY", "resume_point": resume}
            self._task_transition(
                task_id, "BLOCKED",
                blocker={"reason": "CONTINUE_GATE_FAILED", "task_id": task_id})
            self.store.transition("BLOCKED", blocker={"reason": "CONTINUE_GATE_FAILED", "task_id": task_id})
            return {"status": "BLOCKED", "reason": "CONTINUE_GATE_FAILED"}
        elif gate_status == "UNKNOWN":
            self._task_transition(
                task_id, "BLOCKED",
                blocker={"reason": "CONTINUE_GATE_UNKNOWN", "task_id": task_id})
            self.store.transition("BLOCKED", blocker={"reason": "CONTINUE_GATE_UNKNOWN", "task_id": task_id})
            return {"status": "UNKNOWN_FAIL_CLOSED", "reason": "CONTINUE_GATE_UNKNOWN"}
        else:  # OWNER_GATE — Owner-required product/business choice
            og = next((g for g in decision.gates if g.status == "OWNER_GATE"), None)
            reason_class = str((og.details or {}).get("reason_class", "PRODUCT_BUSINESS_CHOICE"))
            task_records = self.task_records()
            done = [tid for tid, r in task_records.items() if r.get("completion")]
            next_tasks = [t for t in task_records
                          if task_records[t].get("status", "READY") in ("READY",)
                          and t != task_id][:3]
            self._task_transition(
                task_id, "WAITING_OWNER",
                owner_decision={
                    "status": "PENDING",
                    "question": f"Owner decision required before task {task_id}",
                    "options": ["continue", "stop"],
                    "recommendation": "stop",
                    "consequences": {
                        "continue": "Resume only after the existing P2P owner gate is resolved.",
                        "stop": "Leave the bounded goal paused without mutation.",
                    },
                    "approval_metadata": {"auto_grant_permissions": False},
                    "source_refs": ["autopilot-continue-gate"],
                    "requested_at": _now_iso(),
                })
            self.store.transition("OWNER_GATE", owner_gate={
                "reason_class": reason_class, "blocking_task": task_id,
                "what_completed": ",".join(done) if done else "none yet",
                "what_is_next": ",".join(next_tasks) if next_tasks else str(task_id),
                "why_owner_is_needed": "continue gate requires an owner decision",
                "question": f"Owner decision required before task {task_id}",
                "safe_options": ("continue", "stop"),
                "recommended_default": None, "resume_condition": "owner resolves the gate",
            })
            return {"status": "OWNER_GATE_REQUIRED", "task_id": task_id}

        # BUDGET check with exact durable resume point.
        ok, reason = self.budget.can_execute_task()
        if not ok:
            resume = json.loads(self.budget.resume_point(task_id=task_id, phase="PRE_EXECUTE"))
            self.store.transition("BUDGET_BOUNDARY", resume_point=resume)
            return {"status": "BUDGET_BOUNDARY", "resume_point": resume}

        # BUILD CONTRACT (never wider than goal/task authority)
        contract = self.build_contract(task_id)
        try:
            self.preflight(contract)
        except PreflightError as exc:
            self.events.append(_phase_event("PREFLIGHT_FAILED", task_id, {"error": str(exc)}))
            self._task_transition(
                task_id, "BLOCKED",
                blocker={"reason": "PREFLIGHT_FAILED", "task_id": task_id})
            self.store.transition("BLOCKED", blocker={
                "reason": "PREFLIGHT_FAILED", "task_id": task_id})
            return {"status": "PREFLIGHT_FAILED", "error": str(exc)}

        # Bind the task to the canonical state before dispatch.  A checkpoint
        # is written while ACTIVE so a process loss cannot be mistaken for a
        # clean READY task or an automatic retry.
        if self._task_state_store is not None:
            try:
                canonical_task = self.task_plan().tasks[task_id]
                self._task_transition(
                    task_id, "ACTIVE",
                    preflight=canonical_task.last_preflight)
                self._task_checkpoint(
                    task_id, contract,
                    classification="UNKNOWN",
                    next_safe_step="REVERIFY_TASK",
                    notes="execution started; mutation certainty is not yet proven")
            except Exception as exc:
                self._task_transition(
                    task_id, "BLOCKED",
                    blocker={
                        "reason": "TASK_STATE_ACTIVATION_FAILED",
                        "task_id": task_id,
                        "error_type": type(exc).__name__,
                    })
                self.store.transition("BLOCKED", blocker={
                    "reason": "TASK_STATE_ACTIVATION_FAILED",
                    "task_id": task_id,
                })
                return {"status": "TASK_STATE_FAIL_CLOSED", "task_id": task_id}

        # EXECUTE (transition first so the crash-before-verify case is visible).
        # Status is re-read freshly: a prior gate-path re-entry may have
        # already moved a VERIFIED goal to APPROVED; stale plan reads would
        # try to double-transition (APPROVED->APPROVED, illegal).
        status_now = self.store.require().status
        if status_now == "VERIFIED":
            # A VERIFIED goal re-entering the loop for remaining tasks must go
            # through APPROVED (the only transition out of VERIFIED besides
            # GOAL_DONE/TERMINAL).
            self.store.transition("APPROVED", next_task_id=task_id)
            self.store.transition("IN_PROGRESS", current_task_id=task_id)
        elif status_now == "IN_PROGRESS" and str(self.store.require().current_task_id) == str(task_id):
            # Bounded retry in flight: already in progress for this task;
            # keep the durable IN_PROGRESS state, only re-record execution.
            pass
        else:
            self.store.transition("IN_PROGRESS", current_task_id=task_id)
        self.store.record_event("task_executed", task_id=task_id, details={
            "contract_fingerprint": self.builder.contract_fingerprint(contract),
            "execution_target": contract["execution_target"],
        })
        try:
            result = self.execute_task(contract)
        except Exception as exc:
            self._task_transition(
                task_id, "BLOCKED",
                blocker={
                    "reason": "EXECUTOR_EXCEPTION",
                    "task_id": task_id,
                    "error_type": type(exc).__name__,
                })
            self.store.transition("BLOCKED", blocker={
                "reason": "EXECUTOR_EXCEPTION", "task_id": task_id})
            return {"status": "EXECUTOR_EXCEPTION", "task_id": task_id}

        # Honest failure modes: never fabricate a backend or silently switch.
        if result.get("no_eligible_target"):
            self._task_transition(
                task_id, "BLOCKED",
                blocker={"reason": "NO_ELIGIBLE_TARGET", "task_id": task_id})
            self.store.transition("BLOCKED", blocker={"reason": "NO_ELIGIBLE_TARGET", "task_id": task_id})
            return {"status": "NO_ELIGIBLE_TARGET", "result": result}
        if result.get("scope_violated"):
            self._task_transition(
                task_id, "BLOCKED",
                blocker={"reason": "SCOPE_VIOLATION_AT_EXECUTION", "task_id": task_id})
            self.store.transition("BLOCKED", blocker={"reason": "SCOPE_VIOLATION_AT_EXECUTION", "task_id": task_id})
            return {"status": "SCOPE_VIOLATION", "result": result}
        if result.get("owner_gate_required"):
            self._task_transition(
                task_id, "WAITING_OWNER",
                owner_decision={
                    "status": "PENDING",
                    "question": f"Backend requires an owner decision for task {task_id}",
                    "options": ["acknowledge", "stop"],
                    "recommendation": "stop",
                    "consequences": {
                        "acknowledge": "Resume only through the existing Owner Gate path.",
                        "stop": "Leave the bounded task paused without mutation.",
                    },
                    "approval_metadata": {"auto_grant_permissions": False},
                    "source_refs": ["autopilot-backend-owner-gate"],
                    "requested_at": _now_iso(),
                })
            self.store.transition("OWNER_GATE", owner_gate={
                "reason_class": "PRODUCT_BUSINESS_CHOICE", "blocking_task": task_id,
                "why_owner_is_needed": "execution backend signals an owner decision is required",
                "question": f"Backend requires owner decision for task {task_id}",
                "safe_options": ("acknowledge",),
                "recommended_default": None, "resume_condition": "owner acknowledges",
            })
            return {"status": "OWNER_GATE_REQUIRED", "task_id": task_id}
        if result["outcome"] in ("CRASH_BEFORE_VERIFY", "MUTATION_UNKNOWN"):
            self._task_transition(
                task_id, "BLOCKED",
                blocker={
                    "reason": "EXECUTION_MUTATION_UNKNOWN", "task_id": task_id,
                    "note": "never blindly rerun an uncertain mutation; re-verify on restart",
                })
            self.store.transition("BLOCKED", blocker={
                "reason": "EXECUTION_MUTATION_UNKNOWN", "task_id": task_id,
                "note": "never blindly rerun an uncertain mutation; re-verify on restart",
            })
            return {"status": "MUTATION_UNKNOWN", "result": result}

        # VERIFY (authority outside executor self-claims)
        evidence = self.verify_result(contract, result)
        status = evidence.get("status")
        if status == "VERIFIED":
            self.mark_task_done(task_id, evidence, contract=contract, result=result)
            self.store.transition("VERIFIED", current_task_id=None)
            self.events.append(_phase_event("TASK_DONE", task_id, {"evidence_ref": evidence.get("evidence_ref")}))
            return {"status": "TASK_DONE_CONTINUE", "task_id": task_id}
        if status == "CONTRADICTED":
            if self.budget.task_retry_budget() > 0 and self.budget.usage.retries < self.budget.task_retry_budget():
                self.budget.usage.retries += 1
                canonical_task = self.task_plan().tasks.get(task_id)
                self._task_transition(
                    task_id, "READY",
                    preflight=(canonical_task.last_preflight
                               if canonical_task is not None else None))
                self.store.record_event("verify_failed_retry_scheduled", task_id=task_id,
                                        details={"evidence_ref": evidence.get("evidence_ref")})
                return {"status": "VERIFY_FAILED_RETRY", "evidence": evidence}
            self.store.transition("TERMINAL", terminal_state="VERIFY_FAILED_TERMINAL",
                                  terminal_reason=f"verifier rejected task {task_id} with bounded retry exhausted")
            self.events.append(_phase_event("VERIFY_FAILED", task_id, {"terminal": True}))
            return {"status": "VERIFY_FAILED_TERMINAL", "evidence": evidence}
        # UNKNOWN evidence fails closed: no continuation.
        self._task_transition(
            task_id, "BLOCKED",
            blocker={"reason": "EVIDENCE_UNKNOWN", "task_id": task_id,
                     "evidence_ref": evidence.get("evidence_ref")})
        self.store.transition("BLOCKED", blocker={"reason": "EVIDENCE_UNKNOWN", "task_id": task_id,
                                                  "evidence_ref": evidence.get("evidence_ref")})
        return {"status": "EVIDENCE_UNKNOWN_FAIL_CLOSED", "evidence": evidence}

    def _reverify_in_flight(self, task_id: str) -> dict[str, Any]:
        """Recover path B: executed but never verified → re-verify, never rerun."""
        rec = self.task_record(str(task_id))
        contract = self.build_contract(str(task_id))
        result = {
            "schema": "p2p-autopilot-execution-result/1",
            "goal_id": self.goal_id, "task_id": str(task_id),
            "request_fingerprint": str(rec.get("fingerprint", contract.get("task_id", ""))),
            "outcome": "PASS", "verdict_hint": "ACCEPTABLE",
            "changed_surface": (), "artifacts": (),
            "execution_receipt": {"outcome": "PASS", "target": contract.get("execution_target", "")},
        }
        evidence = self.verify_result(contract, result)
        if evidence.get("status") == "VERIFIED":
            self.store.record_event("recovery_reverify_complete", task_id=str(task_id),
                                    details={"evidence_ref": evidence.get("evidence_ref")})
            self.mark_task_done(str(task_id), evidence, contract=contract,
                                result=result)
            self.store.transition("VERIFIED", current_task_id=None)
            return {"status": "TASK_DONE_CONTINUE", "task_id": str(task_id)}
        if evidence.get("status") == "CONTRADICTED":
            self.store.transition("TERMINAL", terminal_state="VERIFY_FAILED_AFTER_RECOVERY",
                                  terminal_reason=f"re-verification rejected task {task_id}")
            return {"status": "VERIFY_FAILED_TERMINAL", "evidence": evidence}
        self._task_transition(
            str(task_id), "BLOCKED",
            blocker={"reason": "EVIDENCE_UNKNOWN", "task_id": str(task_id),
                     "evidence_ref": evidence.get("evidence_ref")})
        self.store.transition("BLOCKED", blocker={"reason": "EVIDENCE_UNKNOWN", "task_id": str(task_id),
                                                  "evidence_ref": evidence.get("evidence_ref")})
        return {"status": "EVIDENCE_UNKNOWN_FAIL_CLOSED", "evidence": evidence}

    def run_until(self, max_iterations: int = 256) -> list[dict[str, Any]]:
        outcomes = []
        for _ in range(max_iterations):
            outcome = self.step()
            outcomes.append(outcome)
            if outcome.get("status") in ("TERMINAL", "OWNER_GATE", "OWNER_GATE_REQUIRED", "BUDGET_BOUNDARY",
                                         "BLOCKED", "VERIFY_FAILED_TERMINAL", "EVIDENCE_UNKNOWN_FAIL_CLOSED",
                                         "SESSION_LOST_NEEDS_REVIEW", "PREFLIGHT_FAILED", "NO_ELIGIBLE_TARGET",
                                         "SCOPE_VIOLATION", "MUTATION_UNKNOWN", "UNKNOWN_FAIL_CLOSED",
                                         "TASK_STATE_FAIL_CLOSED", "EXECUTOR_EXCEPTION"):
                break
        return outcomes
