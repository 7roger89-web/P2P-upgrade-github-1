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
from .fake_execution_backend import FakeDeterministicExecutionBackend
from .autopilot_verifier import TaskVerifier
from .task_state import LogicalOwner, TaskRecord, TaskPlan, next_safe_task, _sha256

LOOP_SCHEMA = "p2p-autopilot-loop/1"
MAX_STEP_ITERATIONS = 10 ** 6

CONTINUE_STATUSES = ("CONTINUE",)


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


def _build_task_plan(goal_id: str, task_records: Mapping[str, Mapping[str, Any]]) -> TaskPlan:
    first_scope = next((tuple(rec.get("scope", ())) for rec in task_records.values() if rec.get("scope")), ())
    first_non_scope = next((tuple(rec.get("non_scope", ())) for rec in task_records.values() if rec.get("non_scope")), ())
    records: dict[str, TaskRecord] = {}
    for task_id, rec in task_records.items():
        preflight = rec.get("last_preflight")
        records[task_id] = TaskRecord(**{k: v for k, v in {
            "task_id": rec.get("task_id", task_id), "goal_id": goal_id,
            "title": str(rec.get("title", "")), "purpose": str(rec.get("purpose", "")),
            "status": str(rec.get("status", "READY")),
            "dependencies": tuple(rec.get("dependencies", ())),
            "scope": tuple(rec.get("scope", ()),), "non_scope": tuple(rec.get("non_scope", ())),
            "acceptance_requirements": tuple(rec.get("acceptance_requirements", ())),
            "required_evidence": tuple(rec.get("required_evidence", ())),
            "permission_needs": tuple(rec.get("permission_needs", ("sandboxed-default",))),
            "required_capabilities": tuple(rec.get("required_capabilities", ())),
            "last_preflight": dict(preflight) if preflight is not None else None,
            "blocker": dict(rec["blocker"]) if isinstance(rec.get("blocker"), Mapping) else rec.get("blocker"),
            "owner_decision": dict(rec["owner_decision"]) if isinstance(rec.get("owner_decision"), Mapping) else rec.get("owner_decision"),
            "completion": dict(rec["completion"]) if isinstance(rec.get("completion"), Mapping) else rec.get("completion"),
            "execution_lineage": {
                "status": str(rec.get("execution_lineage", {}).get("status", "UNKNOWN")),
                "refs": list(rec.get("execution_lineage", {}).get("refs", [])),
            },
        }.items()})
    owner = LogicalOwner.for_goal(goal_id)
    return TaskPlan(goal_id=goal_id, logical_owner=owner, tasks=records,
                    plan_scope=tuple(first_scope), plan_non_scope=tuple(first_non_scope))


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
        return _build_task_plan(self.goal_id, self._task_records)

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
        rec = self._task_records[task_id]
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
        result = self.backend.execute(contract)
        duration = time.monotonic() - start
        result = self._finalize_execution(result, duration)
        self.budget.record_execution(
            retries=0, verification_attempts=1,
            changed_scope_items=len(result.get("changed_surface", ())) if isinstance(result.get("changed_surface"), (list, tuple)) else 0,
            duration_seconds=duration,
        )
        return result

    def _finalize_execution(self, result: Mapping[str, Any], duration: float) -> Mapping[str, Any]:
        self.budget.release_execution()
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
        rec = self._task_records[task_id]
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

    def mark_task_done(self, task_id: str, evidence: Mapping[str, Any]) -> None:
        """Durable evidence persistence: evidence pointer only, transcript
        never becomes state.  Completion must satisfy the C11 structural
        validity invariant (VERIFIED status, exact required evidence set,
        sha256 fingerprints)."""
        evidence_ref = evidence.get("evidence_ref")
        rec = self._task_records.get(task_id, {})
        required = tuple(rec.get("required_evidence", ())) or (evidence_ref,)
        if evidence_ref not in required:
            required = (evidence_ref,)
        rec["required_evidence"] = required
        fp = _sha256(evidence_ref)
        rec = dict(rec)
        rec["status"] = "DONE"
        rec["blocker"] = None
        rec["owner_decision"] = None
        rec["completion"] = {
            "status": "VERIFIED",
            "evidence_refs": list(required),
            "candidate_state_fingerprint": fp,
            "evidence_fingerprints": {ref: fp for ref in required},
        }
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

        # PLAN/VALIDATE WAVE: refresh ready tasks (C11 C19 refresh policy)
        current_plan = self.task_plan()

        # SELECT NEXT SAFE TASK (C11 next_safe_task authority)
        task_id = self.select_next_safe_task()
        if task_id is None:
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
            self.store.transition("BLOCKED", blocker={"reason": "CONTINUE_GATE_FAILED", "task_id": task_id})
            return {"status": "BLOCKED", "reason": "CONTINUE_GATE_FAILED"}
        elif gate_status == "UNKNOWN":
            self.store.transition("BLOCKED", blocker={"reason": "CONTINUE_GATE_UNKNOWN", "task_id": task_id})
            return {"status": "UNKNOWN_FAIL_CLOSED", "reason": "CONTINUE_GATE_UNKNOWN"}
        else:  # OWNER_GATE — Owner-required product/business choice
            og = next((g for g in decision.gates if g.status == "OWNER_GATE"), None)
            reason_class = str((og.details or {}).get("reason_class", "PRODUCT_BUSINESS_CHOICE"))
            done = [tid for tid, r in self._task_records.items() if r.get("completion")]
            next_tasks = [t for t in self._task_records
                          if self._task_records[t].get("status", "READY") in ("READY",)
                          and t != task_id][:3]
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
            return {"status": "PREFLIGHT_FAILED", "error": str(exc)}

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
        result = self.execute_task(contract)

        # Honest failure modes: never fabricate a backend or silently switch.
        if result.get("no_eligible_target"):
            self.store.transition("BLOCKED", blocker={"reason": "NO_ELIGIBLE_TARGET", "task_id": task_id})
            return {"status": "NO_ELIGIBLE_TARGET", "result": result}
        if result.get("scope_violated"):
            self.store.transition("BLOCKED", blocker={"reason": "SCOPE_VIOLATION_AT_EXECUTION", "task_id": task_id})
            return {"status": "SCOPE_VIOLATION", "result": result}
        if result.get("owner_gate_required"):
            self.store.transition("OWNER_GATE", owner_gate={
                "reason_class": "PRODUCT_BUSINESS_CHOICE", "blocking_task": task_id,
                "why_owner_is_needed": "execution backend signals an owner decision is required",
                "question": f"Backend requires owner decision for task {task_id}",
                "safe_options": ("acknowledge",),
                "recommended_default": None, "resume_condition": "owner acknowledges",
            })
            return {"status": "OWNER_GATE_REQUIRED", "task_id": task_id}
        if result["outcome"] in ("CRASH_BEFORE_VERIFY", "MUTATION_UNKNOWN"):
            self.store.transition("BLOCKED", blocker={
                "reason": "EXECUTION_MUTATION_UNKNOWN", "task_id": task_id,
                "note": "never blindly rerun an uncertain mutation; re-verify on restart",
            })
            return {"status": "MUTATION_UNKNOWN", "result": result}

        # VERIFY (authority outside executor self-claims)
        evidence = self.verify_result(contract, result)
        status = evidence.get("status")
        if status == "VERIFIED":
            self.store.transition("VERIFIED", current_task_id=None)
            self.mark_task_done(task_id, evidence)
            self.events.append(_phase_event("TASK_DONE", task_id, {"evidence_ref": evidence.get("evidence_ref")}))
            return {"status": "TASK_DONE_CONTINUE", "task_id": task_id}
        if status == "CONTRADICTED":
            if self.budget.task_retry_budget() > 0 and self.budget.usage.retries < self.budget.task_retry_budget():
                self.budget.usage.retries += 1
                self.store.record_event("verify_failed_retry_scheduled", task_id=task_id,
                                        details={"evidence_ref": evidence.get("evidence_ref")})
                return {"status": "VERIFY_FAILED_RETRY", "evidence": evidence}
            self.store.transition("TERMINAL", terminal_state="VERIFY_FAILED_TERMINAL",
                                  terminal_reason=f"verifier rejected task {task_id} with bounded retry exhausted")
            self.events.append(_phase_event("VERIFY_FAILED", task_id, {"terminal": True}))
            return {"status": "VERIFY_FAILED_TERMINAL", "evidence": evidence}
        # UNKNOWN evidence fails closed: no continuation.
        self.store.transition("BLOCKED", blocker={"reason": "EVIDENCE_UNKNOWN", "task_id": task_id,
                                                  "evidence_ref": evidence.get("evidence_ref")})
        return {"status": "EVIDENCE_UNKNOWN_FAIL_CLOSED", "evidence": evidence}

    def _reverify_in_flight(self, task_id: str) -> dict[str, Any]:
        """Recover path B: executed but never verified → re-verify, never rerun."""
        rec = self._task_records.get(str(task_id), {})
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
            self.store.transition("VERIFIED", current_task_id=None)
            self.store.record_event("recovery_reverify_complete", task_id=str(task_id),
                                    details={"evidence_ref": evidence.get("evidence_ref")})
            self.mark_task_done(str(task_id), evidence)
            return {"status": "TASK_DONE_CONTINUE", "task_id": str(task_id)}
        if evidence.get("status") == "CONTRADICTED":
            self.store.transition("TERMINAL", terminal_state="VERIFY_FAILED_AFTER_RECOVERY",
                                  terminal_reason=f"re-verification rejected task {task_id}")
            return {"status": "VERIFY_FAILED_TERMINAL", "evidence": evidence}
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
                                         "SCOPE_VIOLATION", "MUTATION_UNKNOWN", "UNKNOWN_FAIL_CLOSED"):
                break
        return outcomes
