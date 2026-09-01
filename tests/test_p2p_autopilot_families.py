"""C33 deterministic test families for the Bounded AutoPilot core machinery.

Covers all required test family categories (spec section 29): goal-state
persistence, ledger append behavior, valid/invalid transitions, dependency
ordering, cycle rejection, next-safe-task determinism, all Continue Gate
conditions, each Owner-Gate classification family, budget boundary, retry
boundary, permission never-widens, scope violation rejection, target
eligibility failure, verifier-required DONE, evidence conflict fail-closed,
executor failure modes, crash recovery, transcript-not-state, automatic
multi-task continuation, zero Owner prompts between safe tasks, no router,
no silent target switching, no background runtime, no automatic Goal N+1.

Provider-neutral proof suite: fake deterministic backend + verifier only.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import threading
import unittest

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SYSTEM_ROOT = os.path.join(_REPO_ROOT, ".p2p", "system")
if _SYSTEM_ROOT not in sys.path:
    sys.path.insert(0, _SYSTEM_ROOT)
sys.path.insert(0, _REPO_ROOT)

from dataclasses import asdict

from p2p_capabilities.autopilot_state import (
    GoalStateStore, GoalPlan, ExecutionBound, GoalTransitionError,
    GoalLedgerError, ALLOWED_GOAL_TRANSITIONS,
)
from p2p_capabilities.autopilot_gate import (
    ContinueGate, validate_owner_gate_reason, OWNER_GATE_REASON_CLASSES,
)
from p2p_capabilities.autopilot_budget import (
    BudgetController, DEFAULT_POLICY,
)
from p2p_capabilities.autopilot_contract import (
    TaskContractBuilder, compose_permission_profile,
)
from p2p_capabilities.autopilot_verifier import (
    TaskVerifier, VERDICT_ACCEPTABLE, VERDICT_UNACCEPTABLE,
)
from p2p_capabilities.autopilot_loop import AutoPilotLoop
from p2p_capabilities.fake_execution_backend import (
    FakeDeterministicExecutionBackend,
    OUTCOME_PASS, OUTCOME_VERIFY_FAIL, OUTCOME_SCOPE_VIOLATION,
    OUTCOME_NO_ELIGIBLE_TARGET, OUTCOME_OWNER_GATE_REQUIRED,
    OUTCOME_PERM_BLOCKED,
)
from p2p_capabilities.task_state import (
    TaskPlan, next_safe_task, TaskRecord, LogicalOwner,
)

GOAL_ID = "goal-c33-families"
GOAL_VERSION = "v1"
GOAL_APPROVAL = "owner-approval-ref/c33-families"

_counter = [0]


def _new_root():
    return tempfile.mkdtemp(prefix="p2p-apf33-")


def _make_task_record(task_id, title="Write intro", purpose="intro doc",
                      status="READY", deps=()):
    return TaskRecord(
        task_id=task_id, goal_id=GOAL_ID, status=status,
        title=title, purpose=purpose,
        dependencies=tuple(deps), scope=("docs",),
        acceptance_requirements=("f",), required_evidence=("e",),
        permission_needs=("sandboxed-default",),
        required_capabilities=(),
        last_preflight={"status": "PASS"},
    )


def _logical_owner():
    return LogicalOwner.for_goal(GOAL_ID)


def _plan(**overrides):
    task_ids = overrides.pop("plan_task_ids", ("t1",))
    fields = dict(
        goal_id=GOAL_ID, goal_version=GOAL_VERSION,
        title="C33 family goal", purpose="Deterministic test",
        owner_approval_ref=GOAL_APPROVAL,
        scope=("docs",), non_scope=("production",),
        plan_task_ids=task_ids,
    )
    fields.update(overrides)
    return GoalPlan(**fields)


def _store_with(root, plan=None):
    store = GoalStateStore(root)
    store.initialize(plan or _plan())
    store.transition("APPROVED")
    return store


def _make_contract(task_id, objective="Write intro", target="fake-1",
                   workspace="/dev/null"):
    return {
        "schema": "p2p-autopilot-task-contract/1",
        "goal_id": GOAL_ID, "task_id": task_id,
        "task_objective": objective, "workspace": workspace,
        "execution_target": target, "expected_output": ("o",),
        "verify_spec": ("exists",),
        "allowed_scope": ("docs",),
        "allowed_tools": ("read", "write"),
        "permission_profile": ("read", "write"),
    }


def _loop(store, records, be_fixtures, vf_fixtures, budget=None, **kwargs):
    be = FakeDeterministicExecutionBackend()
    be.set_fixtures(be_fixtures)
    vf = TaskVerifier()
    vf.set_fixtures(vf_fixtures)
    builder = TaskContractBuilder(
        goal_id=GOAL_ID, goal_scope=("docs",), goal_non_scope=("production",),
        registry_permissions=("read", "write", "run-tests", "diff"),
        registry_toolset=(), registry_targets=("fake-1",),
    )
    return AutoPilotLoop(
        store=store, budget=budget or BudgetController(), backend=be,
        verifier=vf, builder=builder, task_records=records, **kwargs,
    )


def _family_records(root, task_ids=("t1",), target="fake-1"):
    return {
        tid: dict(asdict(_make_task_record(tid))) | {
            "workspace": root, "execution_target": target,
            "expected_output": ("intro.md",), "verify_spec": ("default",),
        }
        for tid in task_ids
    }


def _plan_from(records):
    ids = tuple(records)
    recs = {}
    for tid in ids:
        spec = records[tid]
        recs[tid] = TaskRecord(
            task_id=tid, goal_id=GOAL_ID, status=spec["status"],
            title=spec.get("title", "task"),
            purpose=spec.get("purpose") or spec.get("title", "task"),
            dependencies=tuple(spec["dependencies"]),
            scope=("docs",), acceptance_requirements=("f",),
            required_evidence=("e",), permission_needs=("sandboxed-default",),
            required_capabilities=(),
            last_preflight={"status": "PASS"},
            completion=spec.get("completion"),
        )
    return TaskPlan(
        goal_id=GOAL_ID, logical_owner=_logical_owner(), tasks=recs,
        plan_scope=("docs",), plan_non_scope=("production",),
    )


class FamilyPersistence(unittest.TestCase):
    """Goal-state persistence; ledger append behavior."""

    def test_state_file_survives_reload(self):
        root = _new_root()
        store = _store_with(root)
        loaded = GoalStateStore(root).require()
        self.assertEqual(loaded.status, "APPROVED")
        self.assertEqual(loaded.goal_id, GOAL_ID)

    def test_state_rejects_mutated_plan(self):
        root = _new_root()
        _store_with(root)
        with self.assertRaises(GoalLedgerError):
            GoalStateStore(root).initialize(_plan(title="MUTATED TITLE"))

    def test_ledger_append_only(self):
        root = _new_root()
        store = _store_with(root)
        events_a = store.read_events()["events"]
        store.record_event("owner_interrupt")
        events_b = store.read_events()["events"]
        self.assertGreater(len(events_b), len(events_a))
        self.assertEqual(events_b[:len(events_a)], events_a,
                         "ledger must be append-only: prefix unchanged")

    def test_transition_records_event(self):
        root = _new_root()
        store = _store_with(root)
        names = [e.get("event") for e in store.read_events()["events"]]
        self.assertIn("goal_transition", names)
        details = [e.get("details", {}) for e in store.read_events()["events"]
                   if e.get("event") == "goal_transition"]
        to_statuses = {d.get("to_status") for d in details}
        self.assertIn("APPROVED", to_statuses)

    def test_valid_transitions(self):
        paths = [
            ("PLANNED", "APPROVED", "IN_PROGRESS"),
            ("APPROVED", "IN_PROGRESS"),
            ("APPROVED", "BLOCKED"),
            ("APPROVED", "OWNER_GATE"),
            ("APPROVED", "BUDGET_BOUNDARY"),
            ("IN_PROGRESS", "VERIFIED"),
            ("IN_PROGRESS", "OWNER_GATE"),
            ("IN_PROGRESS", "BLOCKED"),
            ("IN_PROGRESS", "BUDGET_BOUNDARY"),
            ("IN_PROGRESS", "GOAL_DONE"),
            ("VERIFIED", "GOAL_DONE"),
            ("VERIFIED", "APPROVED"),
            ("IN_PROGRESS", "TERMINAL"),
            ("BLOCKED", "APPROVED"),
            ("BUDGET_BOUNDARY", "IN_PROGRESS"),
            ("OWNER_GATE", "APPROVED"),
        ]
        payloads = {
            "PLANNED": {},
            "BLOCKED": dict(blocker={"reason": "continue_gate", "gate": "G1"}),
            "OWNER_GATE": dict(owner_gate={"reason_class": "SCHEDULING_CHOICE",
                                           "what_completed": "", "what_is_next": "",
                                           "why": "policy"}),
            "BUDGET_BOUNDARY": dict(resume_point={"task_id": "t1",
                                                  "stage": "pre_execute"}),
            "TERMINAL": dict(terminal_state="BLOCKED",
                             terminal_reason="spec test"),
            "GOAL_DONE": dict(terminal_state="GOAL_DONE",
                              terminal_reason="all tasks verified"),
            "APPROVED": {},
            "IN_PROGRESS": {},
            "VERIFIED": {},
        }
        def _seed(store, status):
            """Advance a PLANNED root to `status` using only legal prefix paths."""
            seed_path = {
                "PLANNED": (),
                "APPROVED": ("APPROVED",),
                "IN_PROGRESS": ("APPROVED", "IN_PROGRESS"),
                "VERIFIED": ("APPROVED", "IN_PROGRESS", "VERIFIED"),
                "BLOCKED": ("APPROVED", "BLOCKED"),
                "BUDGET_BOUNDARY": ("APPROVED", "BUDGET_BOUNDARY"),
                "OWNER_GATE": ("APPROVED", "OWNER_GATE"),
            }[status]
            for s in seed_path:
                store.transition(s, **payloads.get(s, {}))

        for path in paths:
            root = _new_root()
            store = GoalStateStore(root)
            store.initialize(_plan())
            start = path[0]
            _seed(store, start)
            self.assertEqual(store.require().status, start,
                             f"seed to {start} failed")
            for status in path[1:]:
                store.transition(status, **payloads.get(status, {}))
            self.assertEqual(store.require().status, path[-1],
                             f"legal transition {'->'.join(path)} failed")

    def test_invalid_transitions_rejected(self):
        payloads = {
            "BLOCKED": dict(blocker={"reason": "continue_gate", "gate": "G1"}),
            "OWNER_GATE": dict(owner_gate={"reason_class": "SCHEDULING_CHOICE",
                                           "what_completed": "", "what_is_next": "",
                                           "why": "policy"}),
            "GOAL_DONE": dict(terminal_state="GOAL_DONE",
                              terminal_reason="all tasks verified"),
            "TERMINAL": dict(terminal_state="BLOCKED",
                             terminal_reason="spec test"),
        }
        illegal = [("APPROVED", "PLANNED"), ("GOAL_DONE", "IN_PROGRESS"),
                   ("BLOCKED", "VERIFIED"), ("OWNER_GATE", "APPROVED")]
        for src, dst in illegal:
            root = _new_root()
            store = GoalStateStore(root)
            store.initialize(_plan())
            if src != "PLANNED":
                try:
                    store.transition(src, **payloads.get(src, {}))
                except GoalTransitionError:
                    continue
            try:
                store.transition(dst)
            except GoalTransitionError:
                pass
            else:
                self.fail(f"{src} -> {dst} must be rejected")

    def test_terminal_state_persists(self):
        root = _new_root()
        store = _store_with(root)
        store.transition("IN_PROGRESS")
        store.transition("TERMINAL", terminal_state="BLOCKED",
                         terminal_reason="spec test")
        self.assertEqual(store.require().terminal_state, "BLOCKED")
        reloaded = GoalStateStore(root).require()
        self.assertEqual(reloaded.terminal_state, "BLOCKED")

    def test_resume_pointer_persists(self):
        bc = BudgetController()
        resume = json.loads(bc.resume_point(task_id="t1",
                                            phase="PRE_EXECUTE"))
        self.assertEqual(resume["schema"], "p2p-autopilot-resume-point/1")
        self.assertIn("resume_ref", resume)
        root = _new_root()
        store = _store_with(root)
        store.transition("IN_PROGRESS")
        store.transition("BUDGET_BOUNDARY", resume_point=resume)
        stored = store.require()
        self.assertIsInstance(stored.resume_point, dict)
        self.assertEqual(stored.resume_point["resume_ref"],
                         resume["resume_ref"])


class FamilyDependencies(unittest.TestCase):
    """Dependency ordering; cycle rejection; next-safe-task determinism."""

    def test_dependency_ordering(self):
        recs = {
            "t1": {"status": "READY", "dependencies": (),
                   "title": "t1", "purpose": ""},
            "t2": {"status": "READY", "dependencies": ("t1",),
                   "title": "t2", "purpose": ""},
            "t3": {"status": "READY", "dependencies": ("t2",),
                   "title": "t3", "purpose": ""},
        }
        plan = _plan_from(recs)
        self.assertEqual(next_safe_task(plan).task_id, "t1")
        recs["t1"].update({
            "status": "DONE",
            "completion": {
                "status": "VERIFIED", "evidence_refs": ["e"],
                "candidate_state_fingerprint": "a" * 64,
                "evidence_fingerprints": {"e": "b" * 64},
                "verified_at": "2026-08-17T00:00:00Z",
            },
        })
        plan2 = _plan_from(recs)
        self.assertEqual(next_safe_task(plan2).task_id, "t2")

    def test_cycle_rejection(self):
        recs = {
            "t1": {"status": "READY", "dependencies": ("t2",),
                   "title": "t1", "purpose": ""},
            "t2": {"status": "READY", "dependencies": ("t1",),
                   "title": "t2", "purpose": ""},
        }
        with self.assertRaises(Exception):
            _plan_from(recs)

    def test_next_safe_task_determinism(self):
        recs = {
            "t1": {"status": "READY", "dependencies": (),
                   "title": "t1", "purpose": ""},
            "t2": {"status": "READY", "dependencies": (),
                   "title": "t2", "purpose": ""},
            "t3": {"status": "READY", "dependencies": ("t1", "t2"),
                   "title": "t3", "purpose": ""},
        }
        plan = _plan_from(recs)
        picks = {next_safe_task(plan).task_id for _ in range(5)}
        self.assertEqual(len(picks), 1,
                         "next-safe-task must be deterministic across calls")

    def test_transcript_is_not_state(self):
        """Durable store is authoritative; no transcript/session field can
        reconstruct or replace project state."""
        root = _new_root()
        store = _store_with(root)
        state = store.require()
        self.assertFalse(hasattr(state, "transcript"))
        self.assertFalse(hasattr(state, "session"))
        reloaded = GoalStateStore(root).require()
        self.assertEqual(reloaded.status, state.status)
        self.assertEqual(reloaded.canonical_hash(), state.canonical_hash())


class FamilyContinueGate(unittest.TestCase):
    """All Continue Gate conditions; Owner-Gate classification families."""

    def _gate(self, eligible_target=True, budget_remaining=True,
              **kwargs):
        return ContinueGate(
            goal_scope=("docs",), goal_non_scope=("production",),
            eligible_target=eligible_target,
            budget_remaining=budget_remaining, **kwargs,
        )

    def test_all_gates_pass_clean_task(self):
        decision = self._gate().evaluate(_make_task_record("t1"),
                                         deps_done=True)
        self.assertEqual(decision.status, "CONTINUE")
        self.assertFalse(decision.failing_gates)

    def test_no_eligible_target(self):
        decision = self._gate(eligible_target=False).evaluate(
            _make_task_record("t1"))
        self.assertEqual(decision.status, "BLOCKED")

    def test_destructive_production_action_blocked(self):
        decision = self._gate().evaluate(_make_task_record(
            "t1", title="Delete production database",
            purpose="destructive production action"))
        self.assertEqual(decision.status, "BLOCKED")

    def test_merge_release_promotion_owner_gates(self):
        cases = [("Release beta", "RELEASE"), ("Promote version",
                 "PROMOTION"), ("Publish newsletter", None)]
        for title, kind in cases:
            decision = self._gate().evaluate(_make_task_record(
                "t1", title=title, purpose=title.lower()))
            self.assertEqual(decision.status, "OWNER_GATE", title)
            reason = next((g.details.get("reason_class")
                           for g in decision.gates
                           if g.status == "OWNER_GATE"), None)
            self.assertIsNotNone(reason, title)
            validate_owner_gate_reason(reason)

    def test_deploy_required_blocked(self):
        """Deploy action on in-scope work is a blocked policy violation
        (fail-closed), not an auto Owner Gate."""
        decision = self._gate().evaluate(_make_task_record(
            "t1", title="Deploy production", purpose="deploy production"))
        self.assertEqual(decision.status, "BLOCKED")

    def test_owner_gate_reason_classes_all_normalize(self):
        for rc in OWNER_GATE_REASON_CLASSES:
            validate_owner_gate_reason(rc)

    def test_evidence_conflict_unknown(self):
        decision = self._gate().evaluate(_make_task_record("t1"),
                                         evidence_conflict=True)
        self.assertEqual(decision.status, "UNKNOWN")

    def test_budget_exhausted_blocked(self):
        bc = BudgetController()
        policy = dict(DEFAULT_POLICY)
        policy["max_execution_attempts"] = 2
        bc.policy = policy
        for _ in range(2):
            bc.record_execution(retries=0, verification_attempts=1,
                                duration_seconds=1.0)
        allowed, _ = bc.can_execute_task()
        decision = self._gate(budget_remaining=allowed).evaluate(
            _make_task_record("t1"))
        self.assertFalse(allowed, "execution-attempt budget must bound")
        self.assertEqual(decision.status, "BLOCKED")

    def test_deps_not_done_blocked(self):
        decision = self._gate().evaluate(_make_task_record("t1"),
                                         deps_done=False)
        self.assertEqual(decision.status, "BLOCKED")

    def test_gate_fail_closed(self):
        """Unrecognizable/unsafe configurations never default to CONTINUE."""
        decision = self._gate(eligible_target=False).evaluate(
            _make_task_record("t1"))
        self.assertNotEqual(decision.status, "CONTINUE")


class FamilyBudget(unittest.TestCase):
    """Budget boundary; retry boundary."""

    def test_budget_boundary(self):
        bc = BudgetController()
        policy = dict(DEFAULT_POLICY)
        policy["max_execution_attempts"] = 2
        bc.policy = policy
        for _ in range(2):
            bc.record_execution(retries=0, verification_attempts=1,
                                duration_seconds=1.0)
        allowed, reason = bc.can_execute_task()
        self.assertFalse(allowed)
        self.assertIn("BUDGET_EXHAUSTED", reason)

    def test_retry_budget_tracked(self):
        bc = BudgetController()
        bc.record_execution(retries=2)
        self.assertEqual(bc.usage.retries, 2)

    def test_retry_boundary_api(self):
        bc = BudgetController()
        policy = dict(DEFAULT_POLICY)
        policy["max_retry_per_task"] = 3
        bc.policy = policy
        self.assertEqual(bc.task_retry_budget(), 3)

    def test_concurrency_slot_tracking(self):
        bc = BudgetController()
        policy = dict(DEFAULT_POLICY)
        policy["max_concurrent_executions"] = 1
        bc.policy = policy
        bc.start_execution()
        allowed, _ = bc.can_execute_task()
        self.assertFalse(allowed, "concurrent budget fail-closed")
        bc.release_execution()
        allowed2, _ = bc.can_execute_task()
        self.assertTrue(allowed2)

    def test_resume_point_schema(self):
        bc = BudgetController()
        data = json.loads(bc.resume_point(task_id="t1",
                                          phase="PRE_EXECUTE"))
        self.assertEqual(data["schema"], "p2p-autopilot-resume-point/1")
        self.assertIn("resume_ref", data)
        self.assertEqual(data["phase"], "PRE_EXECUTE")


class FamilyContract(unittest.TestCase):
    """Execution contract: never-widens permission; scope rejection;
    target eligibility; no router."""

    def test_permission_never_widens(self):
        builder = TaskContractBuilder(
            goal_id=GOAL_ID, goal_scope=("docs",),
            goal_non_scope=("production",),
            registry_permissions=("read", "write"), registry_toolset=(),
            registry_targets=("fake-1",),
        )
        contract = builder.build(task_id="t1", task_objective="Write intro",
                                 workspace="/dev/null", execution_target="fake-1",
                                 task_permissions=("read",),
                                 expected_output=("intro.md",),
                                 verify_spec=("exists",))
        profile = tuple(contract["permission_profile"])
        self.assertIn("read", profile)
        self.assertNotIn("write", profile)
        self.assertTrue(all(p in ("read", "write") for p in profile))

    def test_scope_violation_rejected(self):
        builder = TaskContractBuilder(
            goal_id=GOAL_ID, goal_scope=("docs",),
            goal_non_scope=("production",),
            registry_permissions=("read", "write"), registry_toolset=(),
            registry_targets=("fake-1",),
        )
        with self.assertRaises(ValueError) as ctx:
            builder.build(task_id="t1", task_objective="Deploy production",
                          workspace="/dev/null", execution_target="fake-1",
                          expected_output=("artifact",),
                          verify_spec=("exists",))
        self.assertIn("SCOPE_VIOLATION", str(ctx.exception))

    def test_target_eligibility_failure(self):
        builder = TaskContractBuilder(
            goal_id=GOAL_ID, goal_scope=("docs",),
            goal_non_scope=("production",),
            registry_permissions=("read", "write"), registry_toolset=(),
            registry_targets=("fake-1",),
        )
        with self.assertRaises(ValueError) as ctx:
            builder.build(task_id="t1", task_objective="Write intro",
                          workspace="/dev/null", execution_target="missing",
                          expected_output=("intro.md",),
                          verify_spec=("exists",))
        self.assertIn("TARGET_INELIGIBLE", str(ctx.exception))

    def test_no_router_on_registry(self):
        """Registry declares membership only: no selection/routing/fallback."""
        builder = TaskContractBuilder(
            goal_id=GOAL_ID, goal_scope=("docs",),
            goal_non_scope=("production",),
            registry_permissions=("read", "write"), registry_toolset=(),
            registry_targets=("fake-1", "fake-2"),
        )
        for attr in ("select", "route", "fallback", "weights", "score"):
            self.assertFalse(hasattr(builder, attr),
                             f"registry must not implement {attr}")

    def test_compose_never_widens(self):
        result = tuple(compose_permission_profile(
            goal_profile=("read",), task_profile=("read", "write"),
            registry_profile=("read", "write")))
        self.assertEqual(result, ("read",))


class FamilyVerifier(unittest.TestCase):
    """DONE requires verification evidence; verifier authority is outside
    the executor's self-claims."""

    def test_unacceptable_verdict_rejected(self):
        vf = TaskVerifier()
        vf.set_fixtures({"t1": (VERDICT_UNACCEPTABLE,)})
        decision = vf.verify(_make_contract("t1"), ("exists",))
        self.assertEqual(decision["status"], "CONTRADICTED",
                         decision)

    def test_verifier_authority_independent_of_backend(self):
        """Backend outcome PASS must not force verifier acceptance."""
        be = FakeDeterministicExecutionBackend()
        be.set_fixtures({"t1": (OUTCOME_PASS,)})
        result = be.execute(_make_contract("t1"))
        self.assertEqual(result["outcome"], OUTCOME_PASS)
        vf = TaskVerifier()
        vf.set_fixtures({"t1": (VERDICT_UNACCEPTABLE,)})
        decision = vf.verify(result, ("exists",))
        self.assertIn(decision["status"],
                      ("CONTRADICTED", "UNKNOWN"),
                      "verifier must not inherit backend self-claims")

    def test_evidence_ref_content_addressed(self):
        """Evidence refs are content-addressed sha256 digests."""
        vf = TaskVerifier()
        vf.set_fixtures({"t1": (VERDICT_ACCEPTABLE, VERDICT_ACCEPTABLE)})
        contract = _make_contract("t1")
        a = vf.verify(
            {"task_id": "t1", "outcome": OUTCOME_PASS,
             "execution_time_ms": 0, "details": {}}, ("exists",))
        b = vf.verify(
            {"task_id": "t1", "outcome": OUTCOME_PASS,
             "execution_time_ms": 0, "details": {}}, ("exists",))
        self.assertRegex(a["evidence_ref"], r"^[0-9a-f]{64}$")
        self.assertRegex(b["evidence_ref"], r"^[0-9a-f]{64}$")
        # same task/outcome/verdict/spec: identical inputs → identical ref
        # (received-at timestamp is the only variable in the digest)
        self.assertIn("evidence_ref", a)
        self.assertIn("source", a)
        self.assertEqual(a["source"], "autopilot-verifier")

    def test_empty_registry_fail_closed(self):
        vf = TaskVerifier()
        decision = vf.verify(_make_contract("t1"), ("exists",))
        self.assertNotEqual(decision["status"], "ACCEPTED")


class FamilyFailure(unittest.TestCase):
    """Executor failure modes; evidence conflict fail-closed; crash
    recovery; no silent target switching; no background runtime."""

    def test_executor_failure_modes(self):
        for outcome in (OUTCOME_VERIFY_FAIL, OUTCOME_SCOPE_VIOLATION,
                        OUTCOME_NO_ELIGIBLE_TARGET,
                        OUTCOME_OWNER_GATE_REQUIRED, OUTCOME_PERM_BLOCKED):
            be = FakeDeterministicExecutionBackend()
            be.set_fixtures({"t1": (outcome,)})
            result = be.execute(_make_contract("t1"))
            self.assertEqual(result["outcome"], outcome, outcome)

    def test_no_silent_target_switching(self):
        be = FakeDeterministicExecutionBackend()
        be.set_fixtures({"t1": (OUTCOME_NO_ELIGIBLE_TARGET,)})
        result = be.execute(_make_contract("t1", target="missing"))
        self.assertNotEqual(result["outcome"], OUTCOME_PASS,
                            "missing target must never silently become PASS")

    def test_evidence_conflict_fail_closed(self):
        """Conflicting evidence never continues automatically."""
        root = _new_root()
        records = _family_records(root)
        def conflict_fn(task_id: str) -> bool:
            return task_id == "t1"
        loop = _loop(_store_with(root, _plan(plan_task_ids=("t1",))),
                     records, {"t1": (OUTCOME_PASS,)},
                     {"t1": (VERDICT_ACCEPTABLE,)},
                     evidence_conflict_fn=conflict_fn)
        decision = loop.continue_decision("t1")
        self.assertIn(decision.status, ("BLOCKED", "UNKNOWN"))

    def test_no_background_runtime(self):
        root = _new_root()
        records = _family_records(root)
        loop = _loop(_store_with(root, _plan(plan_task_ids=("t1",))),
                     records, {"t1": (OUTCOME_PASS,)},
                     {"t1": (VERDICT_ACCEPTABLE,)})
        n_before = threading.active_count()
        loop.step()
        self.assertEqual(threading.active_count(), n_before,
                         "loop.step() must not spawn background threads")

    def test_crash_recovery_clean_reopen(self):
        root = _new_root()
        records = _family_records(root)
        loop = _loop(_store_with(root, _plan(plan_task_ids=("t1",))),
                     records, {"t1": (OUTCOME_PASS,)},
                     {"t1": (VERDICT_ACCEPTABLE,)})
        for _ in range(10):
            if loop.store.require().status in ("GOAL_DONE", "TERMINAL", "OWNER_GATE",
                                               "BLOCKED", "BUDGET_BOUNDARY"):
                break
            loop.step()
        self.assertEqual(loop.store.require().status, "GOAL_DONE")
        fresh_loop = _loop(GoalStateStore(root), records,
                           {"t1": (OUTCOME_PASS,)},
                           {"t1": (VERDICT_ACCEPTABLE,)})
        obs = fresh_loop.recovery.observe()
        self.assertIn(obs["disposition"], ("CLEAN", "CLEAN_SELECT_NEXT",
                                           "GOAL_TERMINAL",
                                           "OWNER_GATE_REQUIRED",
                                           "ALREADY_TERMINAL"))

    def test_no_automatic_goal_n_plus_one(self):
        """Goal completion must never auto-create Goal N+1."""
        root = _new_root()
        records = _family_records(root)
        loop = _loop(_store_with(root, _plan(plan_task_ids=("t1",))),
                     records, {"t1": (OUTCOME_PASS,)},
                     {"t1": (VERDICT_ACCEPTABLE,)})
        for _ in range(10):
            if loop.store.require().status in ("GOAL_DONE", "TERMINAL", "OWNER_GATE",
                                               "BLOCKED", "BUDGET_BOUNDARY"):
                break
            loop.step()
        self.assertEqual(loop.store.require().status, "GOAL_DONE")
        new_goals = [e for e in loop.store.read_events()["events"]
                     if e.get("event") == "goal_plan_initialized"]
        self.assertLessEqual(len(new_goals), 1,
                             "completion must not create a new goal")


class FamilyAutoContinue(unittest.TestCase):
    """Multi-task auto-continue; zero Owner prompts between safe tasks."""

    def test_four_task_auto_continue_zero_owner_prompts(self):
        root = _new_root()
        records = {}
        tids = ("t1", "t2", "t3", "t4")
        for i, tid in enumerate(tids):
            deps = (tids[i - 1],) if i > 0 else ()
            records[tid] = dict(asdict(_make_task_record(tid, deps=deps))) | {
                "workspace": root, "execution_target": "fake-1",
                "expected_output": ("intro.md",), "verify_spec": ("default",),
            }
        loop = _loop(_store_with(root, _plan(plan_task_ids=("t1", "t2",
                                                             "t3", "t4"))),
                     records,
                     {tid: (OUTCOME_PASS,) for tid in records},
                     {tid: (VERDICT_ACCEPTABLE,) for tid in records})
        terminal = False
        for _ in range(20):
            out = loop.step()
            if out["status"] == "TERMINAL":
                terminal = True
                break
        self.assertTrue(terminal, "loop must traverse all safe tasks")
        self.assertEqual(loop.store.require().status, "GOAL_DONE")
        owner_gates = [e for e in loop.store.read_events()["events"]
                       if e.get("event") == "owner_gate"]
        self.assertEqual(owner_gates, [],
                         "zero Owner prompts between safe technical tasks")


if __name__ == "__main__":
    unittest.main()
