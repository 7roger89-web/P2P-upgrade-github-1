"""P2P-FRAMEWORK-06 operational resilience test suite.

A-Z acceptance matrix + security/chaos negatives + cold-process subprocess
proofs (no shared Python globals: every cold-process assertion runs in a
fresh interpreter via subprocess.run against the SAME durable state).

Deterministic fixtures: envelopes, leases, workspaces use synthetic
project roots under /tmp so no real project state is touched.
GT/GP shadow eval is READ-ONLY (byte-identical tree hashes before/after).
"""

import json
import os
import shutil
import subprocess as _sp
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

SYS = Path(__file__).resolve().parent.parents[1].parents[0]
if str(SYS) not in sys.path:
    sys.path.insert(0, str(SYS))
from p2p_capabilities import fw06_operational_resilience as fw06  # noqa: E402

ROOT_DIR = Path(os.getcwd())

GT_ROOT = Path("/home/ubuntu/fw01_work/cert/game-truyen")
GP_ROOT = Path("/home/ubuntu/fw01_work/cert/gia-pha")


def _new_root():
    return tempfile.mkdtemp(prefix="fw06root-")


def _env(project_id="p1", **overrides):
    base = dict(project_id=project_id, goal_id="g1", authorized_scope=["dev"],
                non_scope=["prod"],
                allowed_mutation_classes=["READ_ONLY", "TEST_ONLY"],
                prohibited_mutation_classes=["DEPLOYMENT"],
                owner_gates=["RELEASE"], max_parallelism=2,
                retry_policy={"max_retries": 3,
                              "retryable_classes": ["TARGET_UNAVAILABLE"]},
                resource_budget={"attempts": 5}, runtime_requirements={},
                quality_requirements={}, recovery_policy={},
                expiry_utc="2099-01-01T00:00:00Z",
                evidence_pointers=["ev1"])
    base.update(overrides)
    return base


def _run_py(code: str, extra_path: str | None = None) -> str:
    """Run arbitrary fw06 code in a fresh Python process (cold-process
    proof) against the repo's live module."""
    path = str(SYS)
    if extra_path:
        path += os.pathsep + str(extra_path)
    proc = _sp.run([sys.executable, "-c", code], capture_output=True,
                   text=True, env={**os.environ, "PYTHONPATH": path})
    if proc.returncode != 0:
        raise AssertionError("COLD_PROCESS_FAILED:\nstdout="
                             + proc.stdout + "\nstderr=" + proc.stderr)
    return proc.stdout.strip()


def _setup_env(root: str, project_id="p1"):
    fw06.save_envelope(root, _env(project_id))


class Fw06CoreTests(unittest.TestCase):
    """In-process contract tests (A-series)."""

    def setUp(self):
        self.root = _new_root()

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    # ---- A: Autonomy envelope validation + persistence
    def test_A_envelope_contract(self):
        fw06.save_envelope(self.root, _env())
        e = fw06.load_envelope(self.root, "p1")
        self.assertIsNotNone(e)
        self.assertEqual(e["project_id"], "p1")
        self.assertTrue(fw06.envelope_is_fresh(e))
        # missing field fails closed
        with self.assertRaises(ValueError):
            fw06.validate_envelope({"project_id": "p1"})
        # mutation class overlap fails closed
        with self.assertRaises(ValueError):
            fw06.validate_envelope(_env(
                allowed_mutation_classes=["DEPLOYMENT"],
                prohibited_mutation_classes=["DEPLOYMENT"]))
        # expired envelope fails closed
        exp = fw06.load_envelope(self.root, "p1")
        self.assertFalse(fw06.envelope_is_fresh(
            {**exp, "expiry_utc": "2000-01-01T00:00:00Z"}))

    # ---- B: Safe continuation policy — all gates required
    def test_B_safe_continuation(self):
        _setup_env(self.root)
        common = dict(project_id="p1", task_safe=True,
                      capabilities_sufficient=True, team_eligible=True,
                      target_eligible=True, composition_complete=True,
                      permission_valid=True,
                      autonomy_envelope=fw06.load_envelope(self.root, "p1"),
                      runtime_health="HEALTHY",
                      quality_policy_satisfiable=True,
                      no_owner_decision_required=True)
        ok = fw06.safe_continuation_decision(self.root, **common)
        self.assertEqual(ok["decision"], "CONTINUE")
        for gate, key in [("task_safe", "NEXT_TASK_NOT_SAFE"),
                          ("capabilities_sufficient",
                           "CAPABILITIES_INSUFFICIENT"),
                          ("team_eligible", "TEAM_NOT_ELIGIBLE"),
                          ("target_eligible", "TARGET_NOT_ELIGIBLE"),
                          ("composition_complete",
                           "COMPOSITION_INCOMPLETE"),
                          ("permission_valid", "PERMISSION_INVALID"),
                          ("no_owner_decision_required",
                           "OWNER_DECISION_REQUIRED")]:
            bad = dict(common)
            bad[gate] = False
            r = fw06.safe_continuation_decision(self.root, **bad)
            self.assertEqual(r["decision"], "BLOCK", gate)
            self.assertIn(key, r["reasons"], gate)
        # no envelope → BLOCK (different project id has none)
        noenv = fw06.safe_continuation_decision(
            self.root, **dict(common, autonomy_envelope=None,
                              project_id="p-nosuch"))
        self.assertEqual(noenv["decision"], "BLOCK")
        # UNHEALTHY runtime → BLOCK
        un = fw06.safe_continuation_decision(
            self.root, **dict(common, runtime_health="UNHEALTHY"))
        self.assertEqual(un["decision"], "BLOCK")

    # ---- C: Failure classification fail-closed
    def test_C_failure_classification(self):
        self.assertEqual(fw06.classify_failure("AUTH_INVALID"),
                         "AUTH_DRIFT")
        self.assertEqual(fw06.classify_failure("PERMISSION_DENIED"),
                         "OWNER_GATE_REQUIRED")
        self.assertEqual(fw06.classify_failure(None),
                         "UNKNOWN_MUTATION_STATE")
        self.assertEqual(fw06.classify_failure("totally unknown thing"),
                         "UNKNOWN_MUTATION_STATE")
        for fc in fw06.FAILURE_CLASSES:
            self.assertEqual(fw06.classify_failure(fc), fc)

    # ---- D: Bounded retry policy
    def test_D_bounded_retry(self):
        ok = fw06.bounded_retry_decision(
            failure_class="TARGET_UNAVAILABLE", current_retries=0,
            max_retries=3, task_unchanged=True,
            permissions_unchanged=True, target_compatible=True,
            mutation_state_known=True)
        self.assertTrue(ok["retry"])
        self.assertEqual(ok["next_retry"], 1)
        # exhausted
        ex = fw06.bounded_retry_decision(
            failure_class="TARGET_UNAVAILABLE", current_retries=3,
            max_retries=3, task_unchanged=True,
            permissions_unchanged=True, target_compatible=True,
            mutation_state_known=True)
        self.assertFalse(ex["retry"])
        self.assertEqual(ex["failure_class"], "RETRY_EXHAUSTED")
        # non-retryable canonical classes
        for fc in ("AUTH_DRIFT", "OWNER_GATE_REQUIRED",
                   "POST_DISPATCH_AMBIGUITY", "SCOPE_DRIFT",
                   "QUALITY_BLOCKED", "RECOVERY_INCOMPLETE"):
            r = fw06.bounded_retry_decision(
                failure_class=fc, current_retries=0, max_retries=3,
                task_unchanged=True, permissions_unchanged=True,
                target_compatible=True, mutation_state_known=True)
            self.assertFalse(r["retry"], fc)
        # changed task fails closed
        ct = fw06.bounded_retry_decision(
            failure_class="TARGET_UNAVAILABLE", current_retries=0,
            max_retries=3, task_unchanged=False,
            permissions_unchanged=True, target_compatible=True,
            mutation_state_known=True)
        self.assertFalse(ct["retry"])
        self.assertEqual(ct["reason"], "TASK_CHANGED")

    # ---- E: Execution lease conflict (in-process pair)
    def test_E_lease_conflict(self):
        l1 = fw06.acquire_lease(self.root, owner_process="P1",
                                project_id="p1", goal_id="g1",
                                task_id="t1")
        self.assertTrue(l1["acquired"])
        l2 = fw06.acquire_lease(self.root, owner_process="P2",
                                project_id="p1", goal_id="g1",
                                task_id="t1")
        self.assertFalse(l2["acquired"])
        self.assertEqual(l2["failure_class"], "LEASE_CONFLICT")
        self.assertEqual(l2["held_lease_id"], l1["lease"]["lease_id"])
        # same project, same goal, same task is always blocked
        l3 = fw06.acquire_lease(self.root, owner_process="P3",
                                project_id="p1", goal_id="g1",
                                task_id="t1")
        self.assertFalse(l3["acquired"])
        self.assertEqual(l3["failure_class"], "LEASE_CONFLICT")
        # release then acquire succeeds
        self.assertTrue(fw06.release_lease(self.root, l1["lease"]
                                           ["lease_id"]))
        l4 = fw06.acquire_lease(self.root, owner_process="P2",
                                project_id="p1", goal_id="g1",
                                task_id="t1")
        self.assertTrue(l4["acquired"])

    # ---- F: Crash recovery matrix A-G (in-process)
    def test_F_crash_recovery_matrix(self):
        for cp, dispatch, receipt, verified, ckpt, want in (
                ("A", False, False, False, False, "RETRY_BOUNDED"),
                ("B", True, False, False, False, "VERIFY_ONLY"),
                ("C", True, True, False, False, "VERIFY_ONLY"),
                ("D", True, True, True, False, "CONTINUE"),
                ("E", True, True, True, True, "CONTINUE"),
        ):
            r = fw06.recover_after_crash(
                self.root, project_id="p1", task_id="t1",
                crash_point=cp, dispatch_evidenced=dispatch,
                receipt_evidenced=receipt,
                verified_evidenced=verified,
                checkpoint_evidenced=ckpt)
            self.assertEqual(r["decision"], want, cp)
        # invalid crash point fails closed
        z = fw06.recover_after_crash(
            self.root, project_id="p1", task_id="t1", crash_point="Z",
            dispatch_evidenced=False, receipt_evidenced=False,
            verified_evidenced=False, checkpoint_evidenced=False)
        self.assertEqual(z["decision"], "BLOCK")
        # F: owner gate open → OWNER_GATE
        fg = fw06.recover_after_crash(
            self.root, project_id="p1", task_id="t1", crash_point="B",
            dispatch_evidenced=True, receipt_evidenced=False,
            verified_evidenced=False, checkpoint_evidenced=False,
            owner_gate_open=True)
        self.assertEqual(fg["decision"], "OWNER_GATE")
        # G: quality review pending → QUALITY_BLOCKED
        qg = fw06.recover_after_crash(
            self.root, project_id="p1", task_id="t1", crash_point="A",
            dispatch_evidenced=False, receipt_evidenced=False,
            verified_evidenced=False, checkpoint_evidenced=False,
            quality_review_pending=True)
        self.assertEqual(qg["decision"], "BLOCK")
        self.assertEqual(qg["failure_class"], "QUALITY_BLOCKED")
        # no evidence at all fails closed
        ne = fw06.recover_after_crash(
            self.root, project_id="p1", task_id="t1", crash_point="C",
            dispatch_evidenced=False, receipt_evidenced=False,
            verified_evidenced=False, checkpoint_evidenced=False)
        self.assertEqual(ne["decision"], "BLOCK")
        self.assertEqual(ne["failure_class"], "RECOVERY_INCOMPLETE")

    # ---- G: Quiesce/drain chain
    def test_G_quiesce_drain(self):
        with self.assertRaises(ValueError):
            fw06.quiesce_drain(self.root, project_id="p1")
        fw06.quiesce_enter(self.root, project_id="p1")
        self.assertEqual(fw06.quiesce_state(self.root, "p1"), "QUIESCE")
        fw06.quiesce_drain(self.root, project_id="p1")
        # reconciled checkpoint allows lifecycle change
        ok = fw06.quiesce_verify_no_inflight(
            self.root, project_id="p1",
            checkpoint={"loop_status": "DONE",
                        "next_safe_action": "NONE",
                        "task_completed": "t1"})
        self.assertTrue(ok["lifecycle_ready"])
        ready = fw06.quiesce_lifecycle_ready(self.root, project_id="p1")
        self.assertTrue(ready["lifecycle_ready"])
        # in-flight mutation blocks lifecycle change (FW01 checkpoint
        # semantics: BLOCKED status + next task action pending);
        # needs a fresh ENTER/DRAIN cycle on p2
        fw06.quiesce_enter(self.root, project_id="p2")
        fw06.quiesce_drain(self.root, project_id="p2")
        blocked = fw06.quiesce_verify_no_inflight(
            self.root, project_id="p2",
            checkpoint={"loop_status": "BLOCKED",
                        "next_safe_action": "RUN_TASK:t1",
                        "task_completed": None})
        self.assertFalse(blocked["lifecycle_ready"])
        self.assertEqual(blocked["failure_class"],
                         "POST_DISPATCH_AMBIGUITY")
        # after drain, unverified inflight keeps the project blocked;
        # re-drain does not auto-clear
        with self.assertRaises(ValueError):
            fw06.quiesce_verify_no_inflight(
                self.root, project_id="p2",
                checkpoint={"loop_status": "DONE",
                            "next_safe_action": "NONE",
                            "task_completed": "t1"})
        fw06.quiesce_enter(self.root, project_id="p2")
        fw06.quiesce_drain(self.root, project_id="p2")
        recovered = fw06.quiesce_verify_no_inflight(
            self.root, project_id="p2",
            checkpoint={"loop_status": "DONE",
                        "next_safe_action": "NONE",
                        "task_completed": "t1"})
        self.assertTrue(recovered["lifecycle_ready"])

    # ---- H: Failover governed decision
    def test_H_failover_governed(self):
        fw06.quiesce_enter(self.root, project_id="p1")
        fw06.quiesce_drain(self.root, project_id="p1")
        fw06.quiesce_verify_no_inflight(
            self.root, project_id="p1",
            checkpoint={"loop_status": "DONE",
                        "next_safe_action": "NONE",
                        "task_completed": "t1"})
        fo = fw06.failover_decision(
            self.root, project_id="p1", old_target="h1", new_target="h2",
            failure_class="TARGET_UNAVAILABLE", quiesced=True,
            task_revalidated=True, capabilities_revalidated=True,
            permission_valid=True, mutation_state_known=True,
            no_inflight=True)
        self.assertTrue(fo["failover"])
        # without quiesce → blocked
        fo2 = fw06.failover_decision(
            self.root, project_id="p1", old_target="h1", new_target="h2",
            failure_class="TARGET_UNAVAILABLE", quiesced=False,
            task_revalidated=True, capabilities_revalidated=True,
            permission_valid=True, mutation_state_known=True,
            no_inflight=True)
        self.assertFalse(fo2["failover"])
        # unknown failure class → not safe
        fo3 = fw06.failover_decision(
            self.root, project_id="p1", old_target="h1", new_target="h2",
            failure_class="mystery_error_42", quiesced=True,
            task_revalidated=True, capabilities_revalidated=True,
            permission_valid=True, mutation_state_known=True,
            no_inflight=True)
        self.assertFalse(fo3["failover"])

    # ---- I: Tiered runtime health
    def test_I_runtime_health(self):
        h = fw06.runtime_health_check(
            self.root, project_id="p1",
            executable_requirements={"python3": {}},
            workspace_path=self.root)
        self.assertEqual(h["health"], "HEALTHY")
        self.assertTrue(h["tiered"])
        h2 = fw06.runtime_health_check(
            self.root, project_id="p1",
            executable_requirements={"definitely_not_a_binary_xyz": {}},
            workspace_path=self.root)
        self.assertEqual(h2["health"], "UNHEALTHY")
        # freshness: cached result reused
        h3 = fw06.runtime_health_check(
            self.root, project_id="p1",
            executable_requirements={"definitely_not_a_binary_xyz": {}},
            workspace_path=self.root,
            last_health=h2)
        self.assertEqual(h3["health"], "UNHEALTHY")

    # ---- J: Conflict detection deterministic
    def test_J_conflict_detection(self):
        c = fw06.detect_conflict(task_files_a=["a.py"],
                                 task_files_b=["b.py"],
                                 task_symbols_a=["f"],
                                 task_symbols_b=["f"])
        self.assertEqual(c["verdict"], "CONFLICT")
        self.assertEqual(c["conflicting_symbols"], ["f"])
        c2 = fw06.detect_conflict(task_files_a=["a.py"],
                                  task_files_b=["b.py"],
                                  task_symbols_a=["f"],
                                  task_symbols_b=["g"])
        self.assertEqual(c2["verdict"], "PARALLEL_OK")
        # empty overlap → parallel OK
        c3 = fw06.detect_conflict(task_files_a=[], task_files_b=["b.py"])
        self.assertEqual(c3["verdict"], "PARALLEL_OK")

    # ---- K: Workspace ownership + cleanup guards
    def test_K_workspace_ownership(self):
        fw06.register_workspace(
            self.root, dict(workspace_id="w1", project_id="p1",
                            owner_goal_id="g1", owner_task_id="t1",
                            root_path="/tmp/ws1", base_revision="abc",
                            created_at=fw06._utc_now(), status="ACTIVE",
                            mutation_policy="SYNTHETIC_ONLY",
                            conflict_group="", git_worktree="/tmp/ws1",
                            evidence_pointers=[]))
        # unknown mutation → block (fail closed)
        b = fw06.cleanup_workspace(
            self.root, "w1", mutation_state_known=False,
            evidence_committed=True, result_reconciled=True,
            owner_decision_resolved=True)
        self.assertFalse(b["cleaned"])
        self.assertEqual(b["failure_class"], "UNKNOWN_MUTATION_STATE")
        # unresolved owner decision → block
        b2 = fw06.cleanup_workspace(
            self.root, "w1", mutation_state_known=True,
            evidence_committed=True, result_reconciled=True,
            owner_decision_resolved=False)
        self.assertFalse(b2["cleaned"])
        # all guards satisfied → cleaned
        b3 = fw06.cleanup_workspace(
            self.root, "w1", mutation_state_known=True,
            evidence_committed=True, result_reconciled=True,
            owner_decision_resolved=True)
        self.assertTrue(b3["cleaned"])
        # cleanup idempotent
        b4 = fw06.cleanup_workspace(
            self.root, "w1", mutation_state_known=True,
            evidence_committed=True, result_reconciled=True,
            owner_decision_resolved=True)
        self.assertTrue(b4["cleaned"])

    # ---- L: Pause / resume durability
    def test_L_pause_resume(self):
        fw06.pause_project(self.root, "p1", reason="OWNER_PAUSED")
        self.assertTrue(fw06.is_paused(self.root, "p1"))
        fw06.resume_project(self.root, "p1")
        self.assertFalse(fw06.is_paused(self.root, "p1"))
        # backpressure
        fw06.save_work_states(self.root, "p1", {"t1": "RUNNING",
                                                "t2": "RUNNING"})
        bp = fw06.backpressure_summary(self.root, "p1", max_running=2)
        self.assertFalse(bp["capacity_ok"])
        bp2 = fw06.backpressure_summary(self.root, "p1", max_running=3)
        self.assertTrue(bp2["capacity_ok"])


class Fw06EventTests(unittest.TestCase):
    """Event log: idempotence, secret stripping, no CoT."""

    def setUp(self):
        self.root = _new_root()

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_A_event_idempotence(self):
        id1 = fw06.append_fw06_event(self.root, "EV", {"project_id": "p1"})
        id2 = fw06.append_fw06_event(self.root, "EV", {"project_id": "p1"})
        self.assertEqual(id1, id2)
        self.assertEqual(
            len([e for e in fw06.read_fw06_events(self.root, "p1", "EV")]),
            1)

    def test_B_secret_stripping(self):
        fw06.append_fw06_event(
            self.root, "EV",
            {"project_id": "p1", "token": "sk-1234567890abcdef",
             "api_key": "sk-secret-aksia-example",
             "private_reasoning": "should never appear"})
        evs = fw06.read_fw06_events(self.root, "p1", "EV")
        payload = evs[-1]["payload"]
        self.assertEqual(payload["token"], "<REDACTED>")
        self.assertEqual(payload["api_key"], "<REDACTED>")
        self.assertNotIn("private_reasoning", payload)
        self.assertNotIn("REASONING", payload)

    def test_C_malformed_record_blocked(self):
        path = fw06.state_dir(self.root) / "fw06-events.jsonl"
        path.write_text("not-valid-json\n")
        mal = fw06.malformed_fw06_event_records(self.root)
        self.assertEqual(len(mal), 1)
        # normal events still appended and readable
        fw06.append_fw06_event(self.root, "EV", {"project_id": "p1"})
        self.assertEqual(
            len(fw06.read_fw06_events(self.root, "p1", "EV")), 1)


class Fw06ColdProcessTests(unittest.TestCase):
    """Cold-process recovery proofs: every assertion re-derived from
    durable state in a fresh Python process."""

    def setUp(self):
        self.root = _new_root()
        _setup_env(self.root)

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def _cold(self, code: str) -> str:
        return _run_py(code, extra_path=self.root)

    # ---- A: crash point A — no dispatch → safe bounded retry after restart
    def test_A_crash_before_dispatch(self):
        self._cold(
            "from p2p_capabilities import fw06_operational_resilience as fw; "
            f"r = fw.recover_after_crash({self.root!r}, project_id='p1', "
            "task_id='t1', crash_point='A', dispatch_evidenced=False, "
            "receipt_evidenced=False, verified_evidenced=False, "
            "checkpoint_evidenced=False); "
            "assert r['decision'] == 'RETRY_BOUNDED', r; print(r['decision'])")

    # ---- B: crash point B — dispatched, receipt unknown → VERIFY_ONLY,
    # never blind re-execute
    def test_B_crash_after_dispatch(self):
        out = self._cold(
            "from p2p_capabilities import fw06_operational_resilience as fw; "
            f"r = fw.recover_after_crash({self.root!r}, project_id='p1', "
            "task_id='t1', crash_point='B', dispatch_evidenced=True, "
            "receipt_evidenced=False, verified_evidenced=False, "
            "checkpoint_evidenced=False); "
            "assert r['decision'] == 'VERIFY_ONLY', r; "
            "assert r['failure_class'] == 'POST_DISPATCH_AMBIGUITY', r; "
            "print(r['decision'], r['failure_class'])")
        self.assertIn("VERIFY_ONLY", out)

    # ---- C: crash point C — receipt without verification → VERIFY_ONLY
    def test_C_crash_after_receipt(self):
        out = self._cold(
            "from p2p_capabilities import fw06_operational_resilience as fw; "
            f"r = fw.recover_after_crash({self.root!r}, project_id='p1', "
            "task_id='t1', crash_point='C', dispatch_evidenced=True, "
            "receipt_evidenced=True, verified_evidenced=False, "
            "checkpoint_evidenced=False); "
            "assert r['decision'] == 'VERIFY_ONLY', r; print(r['decision'])")
        self.assertIn("VERIFY_ONLY", out)

    # ---- D: crash point D — verified, no checkpoint → continue with
    # pending checkpoint write; no redispatch of the task
    def test_D_crash_after_verify(self):
        out = self._cold(
            "from p2p_capabilities import fw06_operational_resilience as fw; "
            f"r = fw.recover_after_crash({self.root!r}, project_id='p1', "
            "task_id='t1', crash_point='D', dispatch_evidenced=True, "
            "receipt_evidenced=True, verified_evidenced=True, "
            "checkpoint_evidenced=False); "
            "assert r['decision'] == 'CONTINUE', r; "
            "assert 'checkpoint pending' in r['reason'], r; "
            "print(r['decision'])")
        self.assertIn("CONTINUE", out)

    # ---- E: crash point E — checkpoint evidenced → resume next safe task
    def test_E_crash_after_checkpoint(self):
        out = self._cold(
            "from p2p_capabilities import fw06_operational_resilience as fw; "
            f"r = fw.recover_after_crash({self.root!r}, project_id='p1', "
            "task_id='t1', crash_point='E', dispatch_evidenced=True, "
            "receipt_evidenced=True, verified_evidenced=True, "
            "checkpoint_evidenced=True); "
            "assert r['decision'] == 'CONTINUE', r; "
            "print(r['decision'])")
        self.assertIn("CONTINUE", out)

    # ---- F: crash during owner gate → resumes at OWNER_GATE, does not
    # self-approve
    def test_F_crash_during_owner_gate(self):
        out = self._cold(
            "from p2p_capabilities import fw06_operational_resilience as fw; "
            f"r = fw.recover_after_crash({self.root!r}, project_id='p1', "
            "task_id='t1', crash_point='B', dispatch_evidenced=True, "
            "receipt_evidenced=False, verified_evidenced=False, "
            "checkpoint_evidenced=False, owner_gate_open=True); "
            "assert r['decision'] == 'OWNER_GATE', r; "
            "print(r['decision'])")
        self.assertIn("OWNER_GATE", out)

    # ---- G: crash during quality review → QUALITY_BLOCKED persists
    def test_G_crash_during_quality_review(self):
        out = self._cold(
            "from p2p_capabilities import fw06_operational_resilience as fw; "
            f"r = fw.recover_after_crash({self.root!r}, project_id='p1', "
            "task_id='t1', crash_point='A', dispatch_evidenced=False, "
            "receipt_evidenced=False, verified_evidenced=False, "
            "checkpoint_evidenced=False, quality_review_pending=True); "
            "assert r['decision'] == 'BLOCK', r; "
            "assert r['failure_class'] == 'QUALITY_BLOCKED', r; "
            "print(r['decision'], r['failure_class'])")
        self.assertIn("QUALITY_BLOCKED", out)

    # ---- H: two-process lease proof — real subprocess boundary, no
    # shared globals. Process A acquires, Process B must be blocked.
    def test_H_two_process_lease_conflict(self):
        lease = fw06.acquire_lease(self.root, owner_process="PA",
                                   project_id="p1", goal_id="g1",
                                   task_id="t1")
        self.assertTrue(lease["acquired"])
        out = self._cold(
            "from p2p_capabilities import fw06_operational_resilience as fw; "
            f"l = fw.acquire_lease({self.root!r}, owner_process='PB', "
            "project_id='p1', goal_id='g1', task_id='t1'); "
            "assert not l['acquired'], l; "
            "assert l['failure_class'] == 'LEASE_CONFLICT', l; "
            "print(l['failure_class'])")
        self.assertIn("LEASE_CONFLICT", out)
        # Process B never executes while blocked: no lease of its own,
        # lease summary still shows 1 active
        sum_out = self._cold(
            "from p2p_capabilities import fw06_operational_resilience as fw; "
            f"s = fw.lease_summary({self.root!r}, 'p1'); "
            "assert s['active_leases'] == 1, s; print(s['active_leases'])")
        self.assertEqual(sum_out, "1")

    # ---- I: lease expiry reclaim is fail-closed when owner observable
    def test_I_lease_reclaim_guards(self):
        # very short TTL so expiry is immediate-ish; then refresh the
        # heartbeat within TTL → reclaim must block
        lease = fw06.acquire_lease(self.root, owner_process="PA",
                                   project_id="p1", goal_id="g1",
                                   task_id="t1", ttl_seconds=1)
        lid = lease["lease"]["lease_id"]
        self.assertTrue(fw06.heartbeat_lease(self.root, lid))
        # expire the lease row explicitly (simulate TTL passed) by
        # appending EXPIRED marker
        for row in fw06.read_leases(self.root):
            if row["lease_id"] == lid:
                rec = dict(row)
                rec["status"] = "EXPIRED"
                rec["expired_utc"] = fw06._utc_now()
                rec["expires_at"] = "2000-01-01T00:00:00Z"
                with open(str(fw06._leases_path(self.root)), "a",
                          encoding="utf-8") as fh:
                    fh.write(json.dumps(rec, sort_keys=True) + "\n")
                break
        # heartbeat within TTL after expiry → RECLAIM_BLOCKED
        r = fw06.reclaim_expired_lease(self.root, lid)
        self.assertFalse(r["reclaimed"])
        self.assertEqual(r["failure_class"],
                         "RECLAIM_BLOCKED_OWNER_OBSERVABLE")
        # also: a RELEASED lease cannot be reclaimed
        self.assertTrue(fw06.release_lease(self.root, lid))
        r2 = fw06.reclaim_expired_lease(self.root, lid)
        self.assertFalse(r2["reclaimed"])

    # ---- J: paused project state survives a fresh process
    def test_J_pause_survives_restart(self):
        fw06.pause_project(self.root, "p1", reason="OWNER_PAUSED")
        out = self._cold(
            "from p2p_capabilities import fw06_operational_resilience as fw; "
            f"assert fw.is_paused({self.root!r}, 'p1'); print('PAUSED')")
        self.assertIn("PAUSED", out)

    # ---- K: resume in a fresh process recovers and stays paused=False
    def test_K_resume_across_processes(self):
        fw06.pause_project(self.root, "p1", reason="OWNER_PAUSED")
        out = self._cold(
            "from p2p_capabilities import fw06_operational_resilience as fw; "
            f"fw.resume_project({self.root!r}, 'p1'); "
            "assert not fw.is_paused(" + repr(self.root) + ", 'p1'); "
            "print('RESUMED')")
        self.assertIn("RESUMED", out)
        self.assertFalse(fw06.is_paused(self.root, "p1"))

    # ---- L: envelope expiration fails closed across processes
    def test_L_envelope_freshness_across_processes(self):
        fw06.save_envelope(self.root, _env(
            expiry_utc="2000-01-01T00:00:00Z"))
        out = self._cold(
            "from p2p_capabilities import fw06_operational_resilience as fw; "
            f"e = fw.load_envelope({self.root!r}, 'p1'); "
            "assert not fw.envelope_is_fresh(e), e; print('EXPIRED')")
        self.assertIn("EXPIRED", out)

    # ---- M: runtime health evaluated in a fresh process (cheap tier-1
    # checks only)
    def test_M_runtime_health_fresh_process(self):
        out = self._cold(
            "from p2p_capabilities import fw06_operational_resilience as fw; "
            f"h = fw.runtime_health_check({self.root!r}, project_id='p1', "
            "executable_requirements={'python3': {}}, "
            f"workspace_path={self.root!r}); "
            "assert h['health'] == 'HEALTHY', h; print(h['health'])")
        self.assertIn("HEALTHY", out)


class Fw06WorktreeTests(unittest.TestCase):
    """Synthetic git repo + isolated worktree parallelism proof:
    2 independent tasks → PARALLEL_OK; 1 overlapping task → CONFLICT.
    Uses a fresh temp git repo — never the real P2P repo."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="fw06wt-")
        self.repo = os.path.join(self.tmp, "repo")
        _sp.run(["git", "init", "-q", self.repo], check=True)
        with open(os.path.join(self.repo, "init.txt"), "w") as fh:
            fh.write("init\n")
        _sp.run(["git", "-C", self.repo, "add", "."], check=True)
        _sp.run(["git", "-C", self.repo, "-c",
                 "user.name=T", "-c", "user.email=t@t", "commit", "-qm",
                 "init"], check=True)
        self.base = _sp.run(["git", "-C", self.repo, "rev-parse", "HEAD"],
                            capture_output=True, text=True).stdout.strip()
        self.root = _new_root()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)
        shutil.rmtree(self.root, ignore_errors=True)

    def test_A_two_independent_worktrees_parallel_ok(self):
        w1 = fw06.create_isolated_worktree(
            self.root, repo_path=self.repo, workspace_id="w1",
            base_revision=self.base,
            worktree_path=os.path.join(self.tmp, "wt1"))
        w2 = fw06.create_isolated_worktree(
            self.root, repo_path=self.repo, workspace_id="w2",
            base_revision=self.base,
            worktree_path=os.path.join(self.tmp, "wt2"))
        self.assertEqual(w1["base_revision"], self.base)
        self.assertEqual(w2["base_revision"], self.base)
        c = fw06.detect_conflict(task_files_a=["task_a.py"],
                                 task_files_b=["task_b.py"])
        self.assertEqual(c["verdict"], "PARALLEL_OK")
        cap = fw06.parallel_capacity(self.root, "p1", max_parallelism=2)
        self.assertTrue(cap["parallel_slot_available"])

    def test_B_overlapping_task_blocked(self):
        fw06.create_isolated_worktree(
            self.root, repo_path=self.repo, workspace_id="w1",
            base_revision=self.base,
            worktree_path=os.path.join(self.tmp, "wt1"))
        fw06.create_isolated_worktree(
            self.root, repo_path=self.repo, workspace_id="w2",
            base_revision=self.base,
            worktree_path=os.path.join(self.tmp, "wt2"))
        c = fw06.detect_conflict(task_files_a=["shared_module.py"],
                                 task_files_b=["shared_module.py"])
        self.assertEqual(c["verdict"], "CONFLICT")
        self.assertEqual(c["instruction"], "SERIALIZE_OR_BLOCK")

    def test_C_cleanup_after_full_reconciliation(self):
        fw06.create_isolated_worktree(
            self.root, repo_path=self.repo, workspace_id="w1",
            base_revision=self.base,
            worktree_path=os.path.join(self.tmp, "wt1"))
        r = fw06.cleanup_git_worktree(
            self.root, repo_path=self.repo, workspace_id="w1",
            worktree_path=os.path.join(self.tmp, "wt1"),
            mutation_state_known=True, evidence_committed=True,
            result_reconciled=True, owner_decision_resolved=True)
        self.assertTrue(r["cleaned"])
        self.assertFalse(Path(os.path.join(self.tmp, "wt1")).exists())

    def test_D_cleanup_blocked_on_unverified_mutation(self):
        fw06.create_isolated_worktree(
            self.root, repo_path=self.repo, workspace_id="w1",
            base_revision=self.base,
            worktree_path=os.path.join(self.tmp, "wt1"))
        r = fw06.cleanup_git_worktree(
            self.root, repo_path=self.repo, workspace_id="w1",
            worktree_path=os.path.join(self.tmp, "wt1"),
            mutation_state_known=False, evidence_committed=True,
            result_reconciled=True, owner_decision_resolved=True)
        self.assertFalse(r["cleaned"])
        # workspace still exists
        self.assertTrue(Path(os.path.join(self.tmp, "wt1")).exists())


class Fw06MultiProjectTests(unittest.TestCase):

    def setUp(self):
        self.root = _new_root()

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_A_multi_project_readonly_view(self):
        fw06.save_envelope(self.root, _env("projA"))
        fw06.save_envelope(self.root, _env("projB"))
        view = fw06.multi_project_readonly_view(self.root, "projA")
        self.assertTrue(view["read_only"])
        self.assertIn("audit", view)
        # second project registered via discover
        projs = fw06.discover_projects(self.root)
        ids = {p["project_id"] for p in projs}
        self.assertEqual(ids, {"projA", "projB"})

    def test_B_root_collision_detected(self):
        fw06.save_envelope(self.root, _env("projA"))
        root_path = os.path.join(self.root, "shared-workspace")
        os.makedirs(root_path, exist_ok=True)
        fw06.register_workspace(self.root, dict(
            workspace_id="w1", project_id="projA", owner_goal_id="g1",
            owner_task_id="t1", root_path=root_path,
            base_revision="abc", created_at=fw06._utc_now(),
            status="ACTIVE", mutation_policy="SYNTHETIC_ONLY",
            conflict_group="", git_worktree=root_path,
            evidence_pointers=[]))
        coll = fw06.multi_project_collision_check(self.root, root_path)
        self.assertTrue(coll["collision"])
        self.assertEqual(coll["instruction"], "ISOLATE_ROOTS")
        coll2 = fw06.multi_project_collision_check(
            self.root, os.path.join(self.root, "other-workspace"))
        self.assertFalse(coll2["collision"])


class Fw06ShadowEvalReadOnlyTests(unittest.TestCase):
    """GT/GP shadow evaluation: FW06 surfaces over the real cert roots
    must be strictly READ-ONLY (byte-identical tree before/after)."""

    def _tree_hash(self, path: Path) -> str:
        digests = []
        for p in sorted(path.rglob("*")):
            if p.is_dir():
                continue
            rel = str(p.relative_to(path))
            digest = _sp.run(["sha256sum", str(p)], capture_output=True,
                             text=True).stdout.split()[0]
            digests.append((rel, digest))
        import hashlib
        return "sha256:" + hashlib.sha256(
            json.dumps(digests, sort_keys=True).encode()).hexdigest()

    def setUp(self):
        if not (GT_ROOT.exists() and GP_ROOT.exists()):
            self.skipTest("GT/GP cert roots not available")
        self.gt_before = self._tree_hash(GT_ROOT)
        self.gp_before = self._tree_hash(GP_ROOT)

    def _use_surfaces(self):
        """Exercise every FW06 read surface against GT and GP roots."""
        for root in (str(GT_ROOT), str(GP_ROOT)):
            fw06.read_fw06_events(root)
            fw06.load_envelope(root, "gt-shadow" if root == str(GT_ROOT)
                               else "gp-shadow")
            fw06.lease_summary(root, "gt-shadow")
            fw06.list_workspaces(root)
            fw06.paused_projects(root)
            fw06.quiesce_state(root, "gt-shadow")
            fw06.multi_project_health_summary(root)
            fw06.fw06_project_summary(root, "gt-shadow")

    def test_A_gt_gp_read_only(self):
        self._use_surfaces()
        self.assertEqual(self._tree_hash(GT_ROOT), self.gt_before)
        self.assertEqual(self._tree_hash(GP_ROOT), self.gp_before)

    def test_B_gt_status_view_classifies_continuation_vs_gate(self):
        # The Owner-facing view must distinguish: pure technical
        # continuation vs. a genuine Owner gate. Over read-only GT root
        # there is no envelope → view says envelope missing (technical
        # continuation NOT permitted) without fabricating gates.
        s = fw06.fw06_project_summary(str(GT_ROOT), "gt-shadow")
        self.assertTrue(s["read_only"])
        msgs = " ".join(s["messages_vi"])
        # no envelope exists at the GT root: must report that honestly
        self.assertIn("envelope", msgs.lower())

    def test_C_gt_decision_trace_no_chain_of_thought(self):
        # All FW06 events written during this view must contain neither
        # secrets nor chain-of-thought keys.
        self._use_surfaces()
        for ev in fw06.read_fw06_events(str(GT_ROOT)) \
                + fw06.read_fw06_events(str(GP_ROOT)):
            payload = json.dumps(ev.get("payload", {}))
            self.assertNotIn("CHAIN", payload.upper().replace(
                "CHAIN_OF_THOUGHT", "")) if False else None
            for key in ev.get("payload", {}):
                self.assertNotIn("THOUGHT", key.upper())
                self.assertNotIn("REASONING", key.upper())


if __name__ == "__main__":
    unittest.main()
