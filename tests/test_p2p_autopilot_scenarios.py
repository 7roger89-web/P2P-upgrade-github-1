"""C33 scenario proofs A-H for the Bounded AutoPilot core loop.

Each scenario is a deterministic proof over the fake execution backend,
the deterministic verifier, and the provider-neutral loop. No real provider
(Hermes/Manus/Codex) is involved; fixtures replace backend behaviour.

Research-only proof suite for branch p2p-c33-bounded-autopilot-core.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SYSTEM_ROOT = _REPO_ROOT / ".p2p" / "system"
if str(_SYSTEM_ROOT) not in sys.path:
    sys.path.insert(0, str(_SYSTEM_ROOT))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from p2p_capabilities.autopilot_state import GoalStateStore, GoalPlan
from p2p_capabilities.autopilot_loop import AutoPilotLoop
from p2p_capabilities.autopilot_gate import validate_owner_gate_reason
from p2p_capabilities.autopilot_budget import BudgetController
from p2p_capabilities.autopilot_contract import TaskContractBuilder
from p2p_capabilities.autopilot_verifier import TaskVerifier, VERDICT_ACCEPTABLE, VERDICT_UNACCEPTABLE
from p2p_capabilities.fake_execution_backend import (
    FakeDeterministicExecutionBackend,
    OUTCOME_PASS, OUTCOME_VERIFY_FAIL, OUTCOME_SCOPE_VIOLATION,
    OUTCOME_NO_ELIGIBLE_TARGET, OUTCOME_OWNER_GATE_REQUIRED,
)
from p2p_capabilities.autopilot_state import ExecutionBound

GOAL_ID = "goal-c33-scenario"
GOAL_VERSION = "v1"
GOAL_APPROVAL = "owner-approval-ref/c33"

_counter = [0]


def _new_root():
    return tempfile.mkdtemp(prefix="p2p-apc33-")


def _make_records(tasks, root, non_scope=("production",)):
    records = {}
    for tid, dep, scope, title, purpose, evid in tasks:
        records[tid] = {
            "task_id": tid, "goal_id": GOAL_ID, "title": title, "purpose": purpose,
            "status": "READY", "dependencies": tuple(dep), "scope": (scope,),
            "workspace": os.path.join(root, scope, tid),
            "execution_target": "fake-1",
            "expected_output": (f"{tid}.out",),
            "verify_spec": ("exists",),
            "acceptance_requirements": ("file exists",),
            "required_evidence": (evid,),
            "permission_needs": ("sandboxed-default",),
            "last_preflight": {"status": "PASS"},
            "required_capabilities": (),
        }
    return records


def _make_plan(records, root):
    scope_items = tuple(sorted({r["scope"][0] for r in records.values()}))
    return GoalPlan(
        goal_id=GOAL_ID, goal_version=GOAL_VERSION,
        title="C33 scenario goal", purpose="Scenario proof",
        owner_approval_ref=GOAL_APPROVAL,
        scope=scope_items, non_scope=("production",),
        plan_task_ids=tuple(records.keys()),
        execution_bound=ExecutionBound(max_workspace_changes=10),
    )


def _build(root, records, be_fixtures=None, verifier_fixtures=None,
           budget_policy=None, registry_targets=("fake-1",),
           evidence_conflict_fn=None, skip_init=False):
    plan = _make_plan(records, root)
    store = GoalStateStore(root)
    if skip_init:
        store.require()  # recovery session: load existing durable state
    else:
        store.initialize(plan)
        store.transition("APPROVED")  # initial session: owner approval
    be = FakeDeterministicExecutionBackend()
    if be_fixtures:
        be.set_fixtures(be_fixtures)
    verifier = TaskVerifier()
    if verifier_fixtures:
        verifier.set_fixtures(verifier_fixtures)
    else:
        # Scenario-neutral default: verifier accepts every backend PASS.
        verifier.set_fixtures({tid: (VERDICT_ACCEPTABLE,) for tid in records})
    policy = budget_policy if budget_policy is not None else dict(BudgetController().policy)
    budget = BudgetController(policy=policy)
    builder = TaskContractBuilder(
        goal_id=GOAL_ID, goal_scope=tuple(sorted({r["scope"][0] for r in records.values()})),
        goal_non_scope=("production",),
        registry_permissions=("read", "write"), registry_targets=registry_targets,
    )
    loop = AutoPilotLoop(
        store=store, budget=budget, backend=be, verifier=verifier,
        builder=builder, task_records=records,
        evidence_conflict_fn=evidence_conflict_fn,
    )
    return loop


def _events(store, name):
    return store.read_events().get("events", ()) or []


def _run(loop, max_iterations=60, stop_after=()):
    outcomes = []
    for _ in range(max_iterations):
        out = loop.step()
        outcomes.append(out)
        if stop_after and out.get("status") in stop_after:
            break
        if out.get("status") == "TERMINAL":
            break
    return outcomes


class ScenarioA_HappyPath(unittest.TestCase):
    """Task1 → Task2 → Task3 → Task4 → GOAL_DONE with zero owner confirmations."""

    def test_four_task_auto_continue(self):
        root = _new_root()
        records = _make_records([
            ("t1", (), "docs", "Write intro", "intro doc", "evidence:t1.md"),
            ("t2", ("t1",), "docs", "Write body", "body doc", "evidence:t2.md"),
            ("t3", ("t1",), "docs", "Write appendix", "appendix doc", "evidence:t3.md"),
            ("t4", ("t2", "t3"), "docs", "Assemble guide", "assemble guide", "evidence:t4.md"),
        ], root)
        loop = _build(root, records)
        outcomes = _run(loop)
        statuses = [o.get("status") for o in outcomes]
        self.assertEqual(statuses[-1], "TERMINAL")
        final = loop.store.require()
        self.assertEqual(final.status, "GOAL_DONE")
        owner_confirmations = sum(1 for o in outcomes if o.get("status") == "OWNER_GATE")
        self.assertEqual(owner_confirmations, 0)
        done = [tid for tid, r in loop._task_records.items()
                if r.get("completion") and r["completion"]["status"] == "VERIFIED"]
        self.assertEqual(sorted(done), ["t1", "t2", "t3", "t4"])


class ScenarioB_OwnerGate(unittest.TestCase):
    """Task 1 passes; Task 2 backend demands an owner decision → OWNER_GATE;
    Task 3 MUST NOT execute."""

    def test_owner_gate_stops_execution(self):
        root = _new_root()
        records = _make_records([
            ("t1", (), "docs", "Write intro", "intro doc", "evidence:t1.md"),
            ("t2", ("t1",), "docs", "Publish newsletter", "newsletter requires owner approval", "evidence:t2.md"),
            ("t3", ("t2",), "docs", "Follow-up", "follow-up doc", "evidence:t3.md"),
        ], root)
        loop = _build(root, records, be_fixtures={
            "t1": (OUTCOME_PASS,),
            "t2": (OUTCOME_OWNER_GATE_REQUIRED,),
            "t3": (OUTCOME_PASS,),
        })
        outcomes = _run(loop)
        statuses = [o.get("status") for o in outcomes]
        self.assertIn("OWNER_GATE_REQUIRED", statuses)
        # Goal state must persist the owner gate durably.
        final = loop.store.require()
        self.assertEqual(final.status, "OWNER_GATE")
        validate_owner_gate_reason(final.owner_gate["reason_class"])
        # Task 3 never executed.
        executed = [(e.get("task_id")) for e in _events(loop.store, "task_executed")]
        self.assertNotIn("t3", executed, "Task 3 MUST NOT execute after an owner gate")
        self.assertEqual(loop._task_records["t3"].get("status"), "READY")


class ScenarioC_VerifyFailure(unittest.TestCase):
    """Task executes, verifier rejects; bounded repair/retry → eventual PASS."""

    def test_bounded_repair_then_pass(self):
        root = _new_root()
        records = _make_records([
            ("t1", (), "docs", "Write intro", "intro doc", "evidence:t1.md"),
        ], root)
        loop = _build(root, records, be_fixtures={"t1": (OUTCOME_VERIFY_FAIL, OUTCOME_PASS)},
                      verifier_fixtures={"t1": (VERDICT_UNACCEPTABLE, VERDICT_ACCEPTABLE)})  # verifier consumes verdicts in order
        outcomes = _run(loop, max_iterations=20)
        statuses = [o.get("status") for o in outcomes]
        self.assertIn("VERIFY_FAILED_RETRY", statuses)
        self.assertEqual(statuses[-1], "TERMINAL")
        self.assertEqual(loop.store.require().status, "GOAL_DONE")
        self.assertGreaterEqual(loop.budget.usage.retries, 1)

    def test_retry_exhausted_terminal(self):
        root = _new_root()
        records = _make_records([
            ("t1", (), "docs", "Write intro", "intro doc", "evidence:t1.md"),
        ], root)
        policy = dict(BudgetController().policy)
        policy["max_retry_per_task"] = 2
        loop = _build(root, records, be_fixtures={"t1": (OUTCOME_VERIFY_FAIL,)},
                      verifier_fixtures={"t1": (VERDICT_UNACCEPTABLE, VERDICT_UNACCEPTABLE, VERDICT_UNACCEPTABLE)},
                      budget_policy=policy)
        outcomes = _run(loop, max_iterations=20)
        statuses = [o.get("status") for o in outcomes]
        self.assertIn("VERIFY_FAILED_TERMINAL", statuses)
        self.assertEqual(loop.store.require().terminal_state, "VERIFY_FAILED_TERMINAL")


class ScenarioD_Budget(unittest.TestCase):
    """Task sequence reaches budget boundary → stop exactly →
    durable resume pointer preserved."""

    def test_budget_boundary_resume_point(self):
        root = _new_root()
        records = _make_records([
            ("t1", (), "docs", "Write intro", "intro doc", "evidence:t1.md"),
            ("t2", ("t1",), "docs", "Write body", "body doc", "evidence:t2.md"),
            ("t3", ("t2",), "docs", "Write appendix", "appendix doc", "evidence:t3.md"),
        ], root)
        policy = dict(BudgetController().policy)
        policy["max_internal_tasks"] = 2
        loop = _build(root, records, budget_policy=policy)
        outcomes = _run(loop, max_iterations=40)
        statuses = [o.get("status") for o in outcomes]
        self.assertIn("BUDGET_BOUNDARY", statuses)
        boundary = next(o for o in outcomes if o.get("status") == "BUDGET_BOUNDARY")
        resume = boundary["resume_point"]
        if isinstance(resume, str):
            resume = json.loads(resume)
        self.assertEqual(resume["schema"], "p2p-autopilot-resume-point/1")
        self.assertIn("resume_ref", resume)
        final = loop.store.require()
        self.assertEqual(final.status, "BUDGET_BOUNDARY")
        self.assertEqual(final.resume_point["resume_ref"], resume["resume_ref"])
        self.assertEqual(loop._task_records["t3"].get("status"), "READY")
        done = sum(1 for r in loop._task_records.values()
                   if r.get("completion") and r["completion"]["status"] == "VERIFIED")
        self.assertEqual(done, 2)


class ScenarioE_CrashRecovery(unittest.TestCase):
    """Simulate process interruption between execution and verification;
    reload durable state and recover safely."""

    def test_interrupt_reverify_resume(self):
        root = _new_root()
        records = _make_records([
            ("t1", (), "docs", "Write intro", "intro doc", "evidence:t1.md"),
            ("t2", ("t1",), "docs", "Write body", "body doc", "evidence:t2.md"),
        ], root)
        # Session 1: t1 completes; t2 executes then the 'process dies'
        # before verification (task_done never recorded).
        loop1 = _build(root, records, be_fixtures={"t1": (OUTCOME_PASS,), "t2": (OUTCOME_PASS,)})
        out = loop1.step()
        self.assertEqual(out["status"], "TASK_DONE_CONTINUE")
        # Simulate the crash: t2 was executed but the process died before
        # verification completed. Persist that honestly in the ledger and
        # move the goal to a legal intermediate state.
        # Legal re-entry: VERIFIED -> APPROVED -> IN_PROGRESS (same path the
        # loop takes when a verified goal still has pending tasks).
        loop1.store.transition("APPROVED", next_task_id="t2")
        loop1.store.transition("IN_PROGRESS", current_task_id="t2")
        loop1.store.record_event("task_executed", task_id="t2",
                                 details={"contract_fingerprint": "sim-crash", "reason": "simulated interruption"})
        loop1.store.record_event("owner_interrupt", task_id=None,
                                 details={"note": "simulated process interruption before verify"})

        # Session 2: fresh loop over the same durable root.
        loop2 = _build(root, records, be_fixtures={"t1": (OUTCOME_PASS,), "t2": (OUTCOME_PASS,)},
                       skip_init=True)
        obs = loop2.recovery.observe()
        self.assertEqual(obs["disposition"], "NEEDS_REVERIFY")
        out = loop2.step()
        self.assertEqual(out["status"], "TASK_DONE_CONTINUE")
        out = loop2.step()
        # Second task now verifies clean; goal finishes.
        while out.get("status") != "TERMINAL":
            out = loop2.step()
        self.assertEqual(loop2.store.require().status, "GOAL_DONE")


class ScenarioF_ScopeViolation(unittest.TestCase):
    """Planner proposes work outside the approved goal scope → deterministic
    rejection; no execution happens."""

    def test_contract_builder_rejects_out_of_scope(self):
        root = _new_root()
        records = _make_records([
            ("t1", (), "docs", "Write intro", "intro doc", "evidence:t1.md"),
            ("t2", ("t1",), "docs", "Deploy production", "deploy production service", "evidence:t2.md"),
        ], root)
        loop = _build(root, records)
        outcomes = _run(loop)
        statuses = [o.get("status") for o in outcomes]
        # Honest deterministic rejection: the destructive, out-of-scope
        # task never executes. The continue gate blocks it first
        # (NO_DESTRUCTIVE_PRODUCTION_ACTION -> BLOCKED); if ever reached,
        # the contract preflight would also reject it.
        self.assertIn("BLOCKED", statuses)
        self.assertNotIn("PREFLIGHT_FAILED", statuses,
                         "gate must reject before any preflight attempt")
        executed = [e.get("task_id") for e in _events(loop.store, "task_executed")]
        self.assertNotIn("t2", executed, "out-of-scope task must never execute")

    def test_backend_scope_violation_blocked(self):
        root = _new_root()
        records = _make_records([
            ("t1", (), "docs", "Write intro", "intro doc", "evidence:t1.md"),
        ], root)
        loop = _build(root, records, be_fixtures={"t1": (OUTCOME_SCOPE_VIOLATION,)})
        outcomes = _run(loop)
        statuses = [o.get("status") for o in outcomes]
        self.assertIn("SCOPE_VIOLATION", statuses)
        self.assertEqual(loop.store.require().status, "BLOCKED")


class ScenarioG_EvidenceConflict(unittest.TestCase):
    """Conflicting evidence → fail closed / Owner Gate; no continuation."""

    def test_conflict_fail_closed_no_continuation(self):
        root = _new_root()
        records = _make_records([
            ("t1", (), "docs", "Write intro", "intro doc", "evidence:t1.md"),
            ("t2", ("t1",), "docs", "Conflicting update", "conflicting evidence detected in review", "evidence:t2.md"),
        ], root)
        conflict = {"t2"}
        loop = _build(root, records, evidence_conflict_fn=lambda tid: tid in conflict)
        outcomes = _run(loop)
        statuses = [o.get("status") for o in outcomes]
        self.assertIn("UNKNOWN_FAIL_CLOSED", statuses)
        final = loop.store.require()
        self.assertEqual(final.status, "BLOCKED")
        self.assertEqual(loop._task_records["t2"].get("status"), "READY")
        t1_done = loop._task_records["t1"].get("completion", {}).get("status") == "VERIFIED"
        self.assertTrue(t1_done, "prior clean task completed before the conflict surfaced")


class ScenarioH_NoEligibleTarget(unittest.TestCase):
    """Target unavailable → honest blocked; no fabricated backend."""

    def test_registry_empty_gate(self):
        root = _new_root()
        records = _make_records([
            ("t1", (), "docs", "Write intro", "intro doc", "evidence:t1.md"),
        ], root)
        loop = _build(root, records, registry_targets=())
        outcomes = _run(loop)
        statuses = [o.get("status") for o in outcomes]
        self.assertIn("BLOCKED", statuses)
        final = loop.store.require()
        self.assertEqual(final.status, "BLOCKED")
        self.assertIn("CONTINUE_GATE_FAILED", final.blocker.get("reason", ""))
        executed = [e.get("task_id") for e in _events(loop.store, "task_executed")]
        self.assertNotIn("t1", executed)

    def test_backend_no_eligible_target(self):
        root = _new_root()
        records = _make_records([
            ("t1", (), "docs", "Write intro", "intro doc", "evidence:t1.md"),
        ], root)
        loop = _build(root, records, be_fixtures={"t1": (OUTCOME_NO_ELIGIBLE_TARGET,)})
        outcomes = _run(loop)
        statuses = [o.get("status") for o in outcomes]
        self.assertIn("NO_ELIGIBLE_TARGET", statuses)
        self.assertEqual(loop.store.require().status, "BLOCKED")


if __name__ == "__main__":
    unittest.main()
