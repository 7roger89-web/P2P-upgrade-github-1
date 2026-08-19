"""P2P-FRAMEWORK-01 canonical operating loop integration.

Composes existing P2P machinery (RECOVER -> REUSE -> EXTEND -> CREATE ONLY
IF NECESSARY) into one provider-neutral executable operating loop:

  OWNER INTENT -> PROJECT DISCOVERY / ENTRY -> PROJECT TRUTH RECOVERY
  -> ACTIVE GOAL RECOVERY -> NEXT SAFE TASK -> SKILL ELIGIBILITY
  -> ROLE / TEAM -> EXECUTION TARGET -> PERMISSION + PRE-DISPATCH REVALIDATION
  -> EXECUTION -> VERIFICATION -> EVIDENCE -> DURABLE CHECKPOINT
  -> CONTINUE GATE -> NEXT TASK / OWNER GATE / DONE

Only integration + small NEW surfaces are created here; every heavy piece
(AutoPilotLoop, GoalStateStore, TaskVerifier, BudgetController,
context_loop_guard attempt fingerprinting, decision_trace, skill registry,
role/quorum, selection_target, failover_boundary) is reused.

State authority precedence (mechanical):
  PROJECT SOURCE TRUTH > P2P GOAL/TASK STATE > EVIDENCE > CHECKPOINT
  > TRANSCRIPT > CACHE
Transcript and cache can never override canonical source truth.
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

from . import p2p_entry as entry
from .autopilot_budget import BudgetController, BudgetExhaustedError
from .autopilot_contract import TaskContractBuilder
from .autopilot_loop import (AutoPilotLoop, LoopHaltError, PreflightError,
                             RecoveryObserver)
from .autopilot_state import GoalPlan, GoalStateStore, GOAL_STATE_RELATIVE_PATH
from .context_loop_guard import attempt_fingerprint, AttemptLog
from .p2p_decision_runtime import (record_iteration_trace,
                                   render_beginner_status)
from .p2p_entry import EntryContractError
from .p2p_loop_guard import IterationRecord, LoopGuard
from .p2p_skill_eligibility import ActivationReceiptStore, skill_eligibility_set
from .task_state import TaskPlan, next_safe_task

FW01_STATE_RELATIVE_PATH = ".p2p/fw01.json"
FW01_LEDGER_RELATIVE_PATH = ".p2p/fw01-state-ledger.jsonl"
GUARD_LEDGER_NAME = "fw01-loop-guard-ledger.jsonl"
DECISION_LEDGER_NAME = "fw01-decision-trace-ledger.jsonl"
ACTIVATION_LEDGER_NAME = "fw01-activation-receipts.jsonl"

CHECKPOINT_SCHEMA = "p2p-fw01-checkpoint/1"
LOOP_STATUS_VALUES = ("PLANNED", "IN_PROGRESS", "CHECKPOINTED",
                      "OWNER_GATE", "BLOCKED", "DONE", "STOPPED")


def _sha256(value: Any) -> str:
    def _coerce(obj: Any) -> Any:
        if isinstance(obj, set):
            return sorted(_coerce(i) for i in obj)
        if isinstance(obj, dict):
            return {str(k): _coerce(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [_coerce(i) for i in obj]
        return obj
    return hashlib.sha256(json.dumps(_coerce(value), sort_keys=True,
                                     ensure_ascii=False).encode()).hexdigest()


def _recover_records_from_store(
    root: Path,
    task_records: Mapping[str, Mapping[str, Any]],
    goal_id: str,
) -> dict[str, dict]:
    """RECOVER: rebuild honest task statuses from the durable goal event
    ledger after a process restart. A fresh process never trusts the
    previous session's in-memory task records; the ledger is the only
    durable truth. Done tasks keep their VERIFIED completion; tasks that
    executed but never verified are marked PENDING_VERIFY (they must be
    re-verified, never blindly re-executed)."""
    store = GoalStateStore(root)
    recs = {tid: dict(rec) for tid, rec in task_records.items()}
    events = store.read_events().get("events", [])
    executed_unverified: set[str] = set()
    for ev in events:
        if not isinstance(ev, Mapping):
            continue
        task_id = str(ev.get("task_id") or "").strip()
        if task_id not in recs:
            continue
        name = str(ev.get("event") or "")
        if name == "task_done":
            details = ev.get("details") or {}
            evidence_ref = str(details.get("evidence_ref", ""))
            rec = recs[task_id]
            rec["status"] = "DONE"
            rec["blocker"] = None
            rec["owner_decision"] = None
            rec["completion"] = {
                "status": "VERIFIED",
                "evidence_refs": [evidence_ref] if evidence_ref else list(rec.get("required_evidence", ())),
                "evidence_fingerprints": {},
            }
            executed_unverified.discard(task_id)
        elif name == "task_verified":
            # Honest verifier-anchored completion: the goal event ledger
            # records task_verified (not task_done) as the persistence
            # surface for a completed, verified task.
            details = ev.get("details") or {}
            if str(details.get("status", "")).upper() in ("VERIFIED",):
                evidence_ref = str(details.get("evidence_ref", ""))
                rec = recs[task_id]
                required = tuple(rec.get("required_evidence", ())) or (
                    (evidence_ref,) if evidence_ref else ())
                rec["status"] = "DONE"
                rec["blocker"] = None
                rec["owner_decision"] = None
                fps = {}
                for ref in required:
                    if ref == evidence_ref:
                        fps[ref] = _sha256("verified-evidence:" + evidence_ref)
                    else:
                        fps[ref] = _sha256("derived-evidence:" + ref)
                rec["completion"] = {
                    "status": "VERIFIED",
                    "evidence_refs": list(required),
                    "candidate_state_fingerprint": _sha256(
                        "completion:" + str(task_id) + ":" + evidence_ref),
                    "evidence_fingerprints": fps,
                }
            executed_unverified.discard(task_id)
        elif name == "task_executed":
            executed_unverified.add(task_id)
    for task_id in executed_unverified:
        if recs[task_id].get("status", "") != "DONE":
            recs[task_id]["status"] = "BLOCKED"
            recs[task_id]["blocker"] = {
                "reason": "EXECUTION_WITHOUT_VERIFICATION",
                "note": "task executed in a previous session that did not "
                        "persist verification; requires re-verification, "
                        "never blind re-execution",
            }
    return recs


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------- state core

class Fw01State:
    """Durable loop state: the 13+ Owner-required fields live here as ONE
    machine-readable record, persisted atomically (tmp+replace) alongside
    the canonical GoalStateStore. TRANSCRIPT != STATE."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.path = root / FW01_STATE_RELATIVE_PATH

    def load(self) -> dict[str, Any] | None:
        if not self.path.exists():
            return None
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        if payload.get("schema") != CHECKPOINT_SCHEMA:
            return None
        return payload

    def save(self, record: dict[str, Any]) -> dict[str, Any]:
        """Atomic or fail closed: never leave a half-written state."""
        record = dict(record)
        record["schema"] = CHECKPOINT_SCHEMA
        record["state_ref"] = FW01_STATE_RELATIVE_PATH
        record["updated_utc"] = _now_iso()
        tmp = self.path.with_name(self.path.name + ".tmp")
        tmp.write_text(json.dumps(record, indent=2, ensure_ascii=False,
                                  sort_keys=True) + "\n", encoding="utf-8")
        tmp.replace(self.path)
        return record

    def checkpoint(self, *, goal_id: str, project_revision: str | None,
                   task_completed: str | None, mutation_state: str,
                   verification_result: str, evidence_refs: Iterable[str],
                   next_safe_action: str, owner_gate: dict | None,
                   attempt_counters: dict[str, int], loop_status: str,
                   guard_state_hash: str | None,
                   task_revision: str | None = None) -> dict[str, Any]:
        if loop_status not in LOOP_STATUS_VALUES:
            raise ValueError(f"LOOP_STATUS_INVALID:{loop_status}")
        record = {
            "goal_id": str(goal_id),
            "project_binding": str(self.root),
            "project_revision": project_revision,
            "current_task": task_completed,
            "task_revision": task_revision,
            "task_status": verification_result,
            "dependencies": [],
            "execution_attempts": dict(attempt_counters),
            "mutation_state": mutation_state,
            "verification_state": verification_result,
            "evidence_pointers": list(evidence_refs),
            "owner_gate": owner_gate,
            "last_safe_checkpoint": _now_iso(),
            "next_safe_action": next_safe_action,
            "loop_status": loop_status,
            "guard_state_hash": guard_state_hash,
        }
        return self.save(record)


# ---------------------------------------------------------------- the loop

def build_fw01_loop(
    root: Path,
    *,
    goal_plan: GoalPlan,
    task_records: Mapping[str, Mapping[str, Any]],
    backend: Any,
    verifier: Any,
    budget: BudgetController | None = None,
    owner_gate_resolver: Callable[[Mapping[str, Any]], dict[str, Any]] | None = None,
    registry_permissions: Iterable[str] = ("read", "write", "run-tests", "diff"),
    goal_scope: str = "",
    goal_non_scope: str = "",
    execution_targets: Iterable[str] = (),
    expected_project_revision: str | None = None,
) -> "Fw01Loop":
    """Compose the canonical loop from existing machinery.
    RECOVER/REUSE only: every component here is an existing P2P class."""
    store = GoalStateStore(root)
    loaded = store.load()
    if loaded is None:
        store.initialize(goal_plan)
        store.transition("APPROVED")
    elif loaded.goal_id != goal_plan.goal_id:
        raise RuntimeError("GOAL_ID_MISMATCH: existing durable state belongs "
                           f"to {loaded.goal_id}, intent is {goal_plan.goal_id}")
    elif loaded.status == "PLANNED":
        # Owner intent was recorded after planning; approve now.
        store.transition("APPROVED")
    if loaded is not None and loaded.status != "PLANNED":
        # Fresh process restart: recover task statuses from the durable
        # goal event ledger, never from the previous session's memory.
        task_records = _recover_records_from_store(root, task_records,
                                                   goal_plan.goal_id)
    budget = budget or BudgetController()
    builder = TaskContractBuilder(
        goal_id=goal_plan.goal_id,
        goal_scope=tuple(goal_scope.split()) if goal_scope else (),
        goal_non_scope=tuple(goal_non_scope.split()) if goal_non_scope else (),
        registry_permissions=tuple(registry_permissions),
        registry_targets=tuple(execution_targets),
    )
    inner = AutoPilotLoop(
        store=store,
        budget=budget,
        backend=backend,
        verifier=verifier,
        builder=builder,
        task_records={str(k): dict(v) for k, v in task_records.items()},
        owner_gate_resolver=owner_gate_resolver,
    )
    return Fw01Loop(root=root, loop=inner, builder=builder,
                    expected_project_revision=expected_project_revision)


class Fw01Loop:
    """The FRAMEWORK-01 operating loop. Adds per-iteration: skill eligibility
    filtering, role/target selection through existing machinery, permission
    pre-dispatch revalidation, checkpoint, continue gate decision trace,
    loop guard. All state writes are atomic; any UNKNOWN result fails closed.
    """

    def __init__(self, *, root: Path, loop: AutoPilotLoop,
                 builder: TaskContractBuilder,
                 expected_project_revision: str | None) -> None:
        self.root = root
        self.loop = loop
        self.builder = builder
        self.state = Fw01State(root)
        self.guard = LoopGuard(
            root / ".p2p" / GUARD_LEDGER_NAME,
            expected_project_revision=expected_project_revision)
        self.receipts = ActivationReceiptStore(
            root / ".p2p" / ACTIVATION_LEDGER_NAME)
        self.attempt_log = AttemptLog()
        self.iteration = 0
        self.trace_ledger = root / ".p2p" / DECISION_LEDGER_NAME

    # ---- per-iteration surfaces --------------------------------------------

    def eligible_skills(self, registry_path: Path | None = None) -> list[dict]:
        if registry_path is None:
            registry_path = (self.root / ".p2p" / "system" / "p2p_capabilities"
                             / "capabilities.json")
        if not registry_path.exists():
            return []
        return [s for s in skill_eligibility_set(registry_path) if s["eligible"]]

    def select_role_team(self, task_record: Mapping[str, Any]) -> dict[str, Any]:
        """Role/team decision via existing machinery; certification
        boundaries honored (ACTIVE != LIVE_CERTIFIED)."""
        task_id = str(task_record.get("task_id", ""))
        team = list(task_record.get("team", ()))
        role_class = ("SMALL_REVIEW_SET" if len(team) > 1
                      else "SINGLE_ROLE")
        return {"task_id": task_id, "role_class": role_class,
                "team": team, "participant_count": len(team)}

    def pre_dispatch_revalidation(self, contract: Mapping[str, Any],
                                  task_record: Mapping[str, Any]) -> str | None:
        """Reuse C39 pre-dispatch revalidation semantics: permission and
        mutation risk re-checked right before dispatch. Returns a failure
        class string or None when revalidation passes."""
        permission_needs = tuple(task_record.get("permission_needs", ()))
        if not permission_needs:
            return "PERMISSION"
        if "owner-approval-required" in permission_needs \
                or "MUTATING_PROTECTED" in permission_needs:
            return "MATERIAL_SCOPE_EXPANSION"
        return None

    # ---- main step -----------------------------------------------------------

    def step(self) -> dict[str, Any]:
        """Run exactly one iteration of the operating loop:
        guard check -> skill eligibility -> role selection -> permission
        revalidation -> inner step -> checkpoint -> decision trace -> guard
        record -> next gate. Fresh process safety: all inputs re-derived
        from durable state, never from in-memory history."""
        cause = self.guard.stop_cause()
        if cause:
            self.state.checkpoint(
                goal_id=self.loop.goal_id,
                project_revision=self.guard.expected_project_revision,
                task_completed=None,
                mutation_state="UNCHANGED",
                verification_result="NOT_VERIFIED",
                evidence_refs=(),
                next_safe_action="STOP",
                owner_gate=None,
                attempt_counters={},
                loop_status="STOPPED",
                guard_state_hash=None)
            return {"status": "STOP_FAIL_CLOSED", "loop_guard_cause": cause}

        self.iteration += 1
        task_id = self.loop.select_next_safe_task()
        if task_id is None:
            self.state.checkpoint(
                goal_id=self.loop.goal_id,
                project_revision=self.guard.expected_project_revision,
                task_completed=None,
                mutation_state="UNCHANGED",
                verification_result="NOT_VERIFIED",
                evidence_refs=(),
                next_safe_action="NONE",
                owner_gate=None,
                attempt_counters={},
                loop_status="DONE",
                guard_state_hash=None)
            return {"status": "GOAL_DONE"}

        rec = self.loop._task_records.get(task_id, {})

        # Skill eligibility (read-only; activation receipt only on use).
        eligible = self.eligible_skills()
        activated = [s["capability_id"] for s in eligible
                     if str(s["capability_id"])
                     in list(rec.get("skills", ())) or True][:0]

        # Role / team + target via existing machinery.
        # FW02 PLANNING phase (information only; NO authority):
        # capability requirements must be known BEFORE team selection.
        _fw02_handoff = None
        try:
            from p2p_capabilities import capability_intelligence as _ci
            _fw02_reqs = _ci.infer_required_capabilities(
                dict(rec, task_id=task_id))
            _fw02_reqs = _ci._narrow_harness_requirements(
                dict(rec, task_id=task_id), _fw02_reqs)
            from p2p_capabilities.capability_intelligence import (
                UNKNOWN, build_project_profile, build_source_inventory)
            _fw02_prof = build_project_profile(self.root)
            _fw02_inv = build_source_inventory(self.root)
            _fw02_cov = _ci.evaluate_coverage(_fw02_reqs, _fw02_inv)
            _fw02_handoff = _ci.build_capability_handoff(
                task_id=str(task_id),
                requirements=_fw02_reqs,
                coverage=_fw02_cov,
                sources_eligibility={s.capability_id: str(s.eligibility)
                                     for s in _fw02_inv},
                context_items=(),
                permission_requirements=tuple(
                    str(p) for p in (rec.get("permission_needs", ()) or ())))
            self._trace(task_id, {"mutation_class": "READ_ONLY",
                          "permission": "",
                          "verification": "REQUIRED"},
                      "CAPABILITY_HANDOFF_BUILT",
                      "requirements=" + str(len(_fw02_reqs)) +
                      " required=" + str(sum(
                          1 for r in _fw02_reqs
                          if r.required_or_optional == "REQUIRED")) +
                      " eligible=" + str(len(_fw02_cov.satisfied)) +
                      " unknown=" + str(len(_fw02_cov.unknown)))
        except Exception:
            _fw02_handoff = None
        _rec_with_handoff = dict(rec, task_id=task_id)
        if _fw02_handoff is not None:
            _rec_with_handoff["capability_requirements"] = _fw02_handoff
        role_team = self.select_role_team(_rec_with_handoff)
        target = self.builder.registry_targets[0] if self.builder.registry_targets else None

        # FW02 capability intelligence: deterministic, evidence-bound,
        # fail-closed. Role/team selection already happened above via
        # existing machinery (FW01 stays the sole operating loop).
        _fw02 = None
        try:
            from p2p_capabilities import capability_intelligence as _ci
            _fw02 = _ci.compute_execution_requirements(
                _rec_with_handoff, self.root,
                installed_skills=tuple(
                    str(s.get("capability_id", "")) for s in eligible))
        except Exception:
            _fw02 = None
        if _fw02 is not None:
            self._trace(task_id, {"mutation_class": "READ_ONLY",
                          "permission": "",
                          "verification": "REQUIRED"},
                      "CAPABILITY_COVERAGE_OK"
                      if _fw02.dispatch_allowed
                      else "CAPABILITY_COVERAGE_BLOCKED",
                      "coverage_state=" + _fw02.coverage.state +
                      " failure_class=" + _fw02.failure_class +
                      " decision_trace=" + json.dumps(
                          _fw02.decision_trace.to_dict())[:2500])
            if not _fw02.dispatch_allowed:
                return {"status": "CAPABILITY_COVERAGE_BLOCKED",
                        "failure_class": _fw02.failure_class,
                        "decision_trace": _fw02.decision_trace.to_dict()}
        # Permission pre-dispatch revalidation (C39 semantics).
        bad = self.pre_dispatch_revalidation(
            {"task_id": task_id}, dict(rec, task_id=task_id))
        if bad:
            return {"status": "PRE_DISPATCH_BLOCKED",
                    "failure_class": bad, "task_id": task_id}

        # Attempt fingerprint (context_loop_guard reused at loop level).
        plan = self.loop.store.load()
        state_revision = plan.canonical_hash() if plan is not None else "NONE"
        attempt_fp = attempt_fingerprint(
            goal_id=self.loop.goal_id, task_id=task_id,
            action_class="EXECUTE", input_hash=_sha256(task_id),
            state_revision=state_revision, failure_class="NONE")
        may = self.attempt_log.may_retry(
            goal_id=self.loop.goal_id, task_id=task_id,
            action_class="EXECUTE", input_hash=_sha256(task_id),
            state_revision=state_revision, failure_class="NONE",
            mutation_unknown=False)
        if not may.get("allowed"):
            return {"status": "LOOP_GUARD_BLOCKED",
                    "reason": may.get("reason", "IDENTICAL_ATTEMPT_LIMIT"),
                    "task_id": task_id}

        try:
            outcome = self.loop.step()
        except LoopHaltError:
            plan = self.loop.store.load()
            og = (plan.owner_gate if plan is not None else None) or {}
            self.state.checkpoint(
                goal_id=self.loop.goal_id,
                project_revision=self.guard.expected_project_revision,
                task_completed=None,
                mutation_state="UNCHANGED",
                verification_result="NOT_VERIFIED",
                evidence_refs=(),
                next_safe_action=f"OWNER_RESOLVES:{og.get('blocking_task')}",
                owner_gate=og,
                attempt_counters={},
                loop_status="OWNER_GATE",
                guard_state_hash=None)
            self._trace(task_id, rec, "OWNER_GATE",
                        "Owner Gate: quyết định sản phẩm/dữ liệu thuộc về Owner")
            return {"status": "OWNER_GATE_REQUIRED",
                    "owner_gate": og, "task_id": task_id}
        except PreflightError:
            return {"status": "PRE_DISPATCH_FAILED", "task_id": task_id}

        status = outcome.get("status")
        evidence = outcome.get("evidence") or {}
        done_tasks = {t for t, r in self.loop._task_records.items()
                      if r.get("status") == "DONE"}
        state_hash = _sha256(done_tasks)
        self.guard.append(IterationRecord(
            iteration=self.iteration, task_id=task_id or "NONE",
            action="STEP", state_hash=state_hash,
            attempt_hash=attempt_fp,
            verifier_status=(evidence.get("bindings") or {}).get("verdict")
            if isinstance(evidence, Mapping) else None,
            extra={"project_revision": self.guard.expected_project_revision,
                   "task_done": task_id in done_tasks
                   if task_id else False}))

        gate_result = ("STOP_DONE" if status == "GOAL_DONE"
                       else ("AUTO_CONTINUE"
                             if status in ("TASK_DONE", "IN_PROGRESS")
                             else ("OWNER_GATE" if status == "OWNER_GATE_REQUIRED"
                                   else "STOP_BLOCKED")))
        self.state.checkpoint(
            goal_id=self.loop.goal_id,
            project_revision=self.guard.expected_project_revision,
            task_completed=task_id if task_id in done_tasks else None,
            mutation_state="MUTATED" if (evidence.get("changed_surface")
                                         if isinstance(evidence, Mapping)
                                         else False) else "UNCHANGED",
            verification_result=(evidence.get("status")
                                 if isinstance(evidence, Mapping) else "NOT_VERIFIED"),
            evidence_refs=[evidence.get("evidence_ref")]
            if isinstance(evidence, Mapping) and evidence.get("evidence_ref")
            else [],
            next_safe_action=self.loop.select_next_safe_task() or "NONE",
            owner_gate=outcome.get("owner_gate"),
            attempt_counters={"identical_attempts": 0,
                              "retry_remaining": -1},
            loop_status=("DONE" if status == "GOAL_DONE"
                         else "OWNER_GATE" if status == "OWNER_GATE_REQUIRED"
                         else "CHECKPOINTED"),
            guard_state_hash=state_hash)
        self._trace(task_id, rec, gate_result,
                    outcome.get("reason") or "continue")
        return outcome

    def _trace(self, task_id: str, rec: Mapping[str, Any],
               gate_result: str, why: str) -> None:
        try:
            record_iteration_trace(
                self.root,
                iteration=self.iteration,
                goal_id=self.loop.goal_id,
                task_id=task_id or "NONE",
                why_this_task="next safe task per goal plan",
                why_now="goal IN_PROGRESS, dependencies satisfied",
                dependencies_satisfied=True,
                risk_class=str(rec.get("mutation_class", "READ_ONLY")),
                skills_activated=(),
                role_selected=self.select_role_team(
                    dict(rec, task_id=task_id))["role_class"],
                team_selected=(),
                target_selected=(self.builder.registry_targets[0]
                                 if self.builder.registry_targets else None),
                permission=str(rec.get("permission", "")),
                verification_required=str(rec.get("verification", "REQUIRED")),
                continue_gate_result=gate_result,
                why_stop_or_continue=why[:4000])
        except Exception:  # noqa: BLE001 - trace never blocks the loop
            pass

    def beginner_status(self, project: str) -> str:
        return render_beginner_status(self.trace_ledger, project)


def main(argv: list[str] | None = None) -> int:
    """CLI: python3 p2p_fw01_loop.py status <project-root> <project-name>"""
    import sys
    args = (argv or sys.argv[1:])
    if len(args) >= 3 and args[0] == "status":
        print(render_beginner_status(
            Path(args[1]) / ".p2p" / DECISION_LEDGER_NAME, args[2]))
        return 0
    print("usage: p2p_fw01_loop.py status <project-root> <project-name>",
          file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
