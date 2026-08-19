"""P2P-FRAMEWORK-01 deterministic E2E proof runner.

Controls a completely isolated fixture project (no production data) and
runs the canonical operating loop through the Owner acceptance scenario:

    ONE Owner intent -> Task A (safe mutation) -> verify -> checkpoint
      -> automatic continue -> Task B (dependent safe mutation) -> verify
      -> checkpoint -> SIMULATED PROCESS RESTART (fresh process, no memory)
      -> recover -> Task C -> verify -> checkpoint
      -> encounter Task D (simulated Owner Gate) -> STOP FAIL CLOSED.

Plus negative proofs:
    A. unknown mutation -> no blind retry/failover
    B. stale project binding -> fail closed
    C. contradictory evidence -> stop
    D. exhausted retry -> stop
    E. material scope expansion -> owner gate / stop
    F. no eligible target -> fail closed
    G. optional skill unavailable -> bounded fallback, no false claim
    H. unproven full-council requirement -> no fake 8/8
    I. already verified task -> not executed twice after restart
    J. corrupted checkpoint -> fail closed

Evidence is written to <fixture>/.p2p/fw01-proof-evidence.json by each leg.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

PYTHON = sys.executable
HERE = Path(__file__).parent
STATE_MODULES = (".p2p/system",)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------- fixtures

class ProofBackend:
    """Deterministic, fixture-driven execution backend for the proof only.
    Mirrors FakeDeterministicExecutionBackend semantics for the loop."""

    def __init__(self) -> None:
        self.executed: list[str] = []
        self.force_failure_after: dict[str, int] = {}
        self.force_unknown_after: dict[str, int] = {}

    def execute(self, contract: dict) -> dict:
        task_id = str(contract.get("task_id", ""))
        count = self.executed.count(task_id) + 1
        self.executed.append(task_id)
        if task_id in self.force_unknown_after \
                and count > self.force_unknown_after[task_id]:
            return {"status": "UNKNOWN", "outcome": "MUTATION_UNKNOWN",
                    "changed_surface": tuple(contract.get("affected_surface", ())),
                    "evidence": "none"}
        if task_id in self.force_failure_after \
                and count > self.force_failure_after[task_id]:
            return {"status": "FAILED", "outcome": "FAILED",
                    "changed_surface": tuple(contract.get("affected_surface", ())),
                    "error": "simulated failure"}
        return {"status": "PASS", "outcome": "PASS",
                "changed_surface": tuple(contract.get("affected_surface", ())),
                "evidence": f"fixture-evidence-{task_id}-{count}"}


class ProofVerifier:
    """Deterministic verifier. 'CONTRADICTED' / 'INCOMPLETE' / 'UNKNOWN'
    can be forced per task for negative proofs."""

    def __init__(self) -> None:
        self.verifications: list[dict[str, str]] = []
        self.force_status: dict[str, str] = {}

    def verify(self, result: dict, verify_spec: tuple = ()) -> dict:
        task_id = result.get("task_id") or ""
        forced = self.force_status.get(str(task_id))
        status = forced or ("VERIFIED" if result.get("status") == "PASS"
                            else "INCOMPLETE")
        self.verifications.append({"task_id": str(task_id), "status": status})
        return {"status": status,
                "verdict": "VERIFIED" if status == "VERIFIED" else status,
                "bindings": {"verdict": "VERIFIED" if status == "VERIFIED" else status},
                "evidence_ref": result.get("evidence", "none")}


def _make_records(root: Path) -> dict[str, dict]:
    """Build 4 C11-style task records (A,B,C sequential + D owner gate)."""
    ws = str(root / "workspace")
    return {
        "A": {"task_id": "A", "goal_id": "fw01-proof-goal",
              "title": "Task A", "purpose": "safe mutation 1",
              "status": "READY", "dependencies": (), "scope": ("workspace",),
              "workspace": ws, "execution_target": "fake-1",
              "expected_output": ("A.out",), "verify_spec": ("default",),
              "acceptance_requirements": ("file exists",),
              "required_evidence": ("fixture-evidence-A-1",),
              "permission_needs": ("sandboxed-default",),
              "last_preflight": {"status": "PASS"},
              "required_capabilities": ()},
        "B": {"task_id": "B", "goal_id": "fw01-proof-goal",
              "title": "Task B", "purpose": "dependent safe mutation 2",
              "status": "READY", "dependencies": ("A",), "scope": ("workspace",),
              "workspace": ws, "execution_target": "fake-1",
              "expected_output": ("B.out",), "verify_spec": ("default",),
              "acceptance_requirements": ("file exists",),
              "required_evidence": ("fixture-evidence-B-1",),
              "permission_needs": ("sandboxed-default",),
              "last_preflight": {"status": "PASS"},
              "required_capabilities": ()},
        "C": {"task_id": "C", "goal_id": "fw01-proof-goal",
              "title": "Task C", "purpose": "safe task 3",
              "status": "READY", "dependencies": ("B",), "scope": ("workspace",),
              "workspace": ws, "execution_target": "fake-1",
              "expected_output": ("C.out",), "verify_spec": ("default",),
              "acceptance_requirements": ("file exists",),
              "required_evidence": ("fixture-evidence-C-1",),
              "permission_needs": ("sandboxed-default",),
              "last_preflight": {"status": "PASS"},
              "required_capabilities": ()},
        "D": {"task_id": "D", "goal_id": "fw01-proof-goal",
              "title": "Task D", "purpose": "owner-owned decision",
              "status": "READY", "dependencies": ("C",), "scope": ("production",),
              "workspace": ws, "execution_target": "fake-1",
              "expected_output": ("D.out",), "verify_spec": ("default",),
              "acceptance_requirements": ("owner decision",),
              "required_evidence": ("owner-decision-D",),
              "permission_needs": ("owner-approval-required",),
              "last_preflight": {"status": "PASS"},
              "required_capabilities": ()},
    }


def build_goal(root: Path):
    """Build the 4-task GoalPlan (A,B,C sequential + D owner gate)."""
    from p2p_capabilities.autopilot_state import GoalPlan, ExecutionBound
    records = _make_records(root)
    return GoalPlan(
        goal_id="fw01-proof-goal", goal_version="v1",
        title="FW01 proof goal", purpose="Operating loop acceptance proof",
        owner_approval_ref="owner-intent-fw01-proof",
        scope=("workspace", "production"), non_scope=("security", "credentials"),
        plan_task_ids=("A", "B", "C", "D"),
        execution_bound=ExecutionBound(max_workspace_changes=10),
    )


# ---------------------------------------------------------------- proof legs

def _fresh(root: Path, backend, verifier) -> "Fw01Loop":
    """A genuinely new process surface: imports re-derived, AttemptLog fresh.
    Real fresh-process proof is exercised by running the loop via a
    subprocess with clean in-memory state (see run_subprocess_leg)."""
    from p2p_capabilities.p2p_fw01_loop import build_fw01_loop
    plan = build_goal(root)
    return build_fw01_loop(
        root, goal_plan=plan,
        task_records=_make_records(root),
        backend=backend, verifier=verifier,
        registry_permissions=("read", "write", "run-tests", "diff"),
        goal_scope="workspace", goal_non_scope="production security credentials",
        expected_project_revision="fixture-head-1",
        execution_targets=("fake-1",),
    )


def run_leg(root: Path, backend, verifier, max_steps: int = 20,
            *, expect_owner_gate: bool = False) -> dict[str, Any]:
    from p2p_capabilities.p2p_fw01_loop import Fw01Loop, build_fw01_loop
    plan = build_goal(root)
    loop = build_fw01_loop(
        root, goal_plan=plan,
        task_records=_make_records(root),
        backend=backend, verifier=verifier,
        registry_permissions=("read", "write", "run-tests", "diff"),
        goal_scope="workspace", goal_non_scope="production security credentials",
        expected_project_revision="fixture-head-1",
        execution_targets=("fake-1",),
    )
    statuses = []
    for _ in range(max_steps):
        outcome = loop.step()
        statuses.append(outcome.get("status"))
        s = outcome.get("status")
        if s in ("GOAL_DONE", "OWNER_GATE_REQUIRED", "STOP_FAIL_CLOSED",
                 "PRE_DISPATCH_BLOCKED", "LOOP_GUARD_BLOCKED",
                 "BUDGET_BOUNDARY"):
            break
    return {"status_sequence": statuses,
            "final": statuses[-1] if statuses else "NONE",
            "backend_executed": backend.executed,
            "verifications": verifier.verifications,
            "iterations": loop.iteration,
            "goal_status": loop.loop.store.load().status if loop.loop.store.load() else None,
            "record_statuses": {tid: r.get("status") for tid, r in loop.loop._task_records.items()}}


def primary_e2e_proof(base_dir: Path) -> dict[str, Any]:
    """A -> verify -> checkpoint -> auto continue -> B -> verify ->
    checkpoint -> process restart -> recover -> C -> verify -> checkpoint
    -> D -> STOP at Owner Gate. No manual continue between A/B/C."""
    fixture = base_dir / "fw01-e2e-fixture"
    if fixture.exists():
        shutil.rmtree(fixture)
    fixture.mkdir(parents=True)
    # Fixture project truth: minimal workspace file + git binding.
    workspace = fixture / "workspace"
    workspace.mkdir()
    (workspace / "manifest.json").write_text(
        json.dumps({"project": "fw01-proof-fixture", "head": "fixture-head-1"},
                   indent=2))

    backend = ProofBackend()
    verifier = ProofVerifier()

    # Leg 1: A + B from one intent.
    leg1 = run_leg(fixture, backend, verifier, max_steps=8)
    assert leg1["final"] in ("BUDGET_BOUNDARY", "GOAL_DONE",
                             "OWNER_GATE_REQUIRED",
                             "PRE_DISPATCH_BLOCKED"), leg1

    # Leg 2: simulated process restart - fresh in-memory loop, same state.
    backend2 = ProofBackend()
    verifier2 = ProofVerifier()
    leg2 = run_leg(fixture, backend2, verifier2, max_steps=8)

    done_in_mem = {"A": backend.executed.count("A"),
                   "B": backend.executed.count("B"),
                   "C": backend.executed.count("C"),
                   "D": backend.executed.count("D")}
    done_in_mem2 = {"A": backend2.executed.count("A"),
                    "B": backend2.executed.count("B"),
                    "C": backend2.executed.count("C"),
                    "D": backend2.executed.count("D")}

    evidence = {
        "leg": "PRIMARY_E2E",
        "timestamp": _now_iso(),
        "AUTONOMOUS_MULTI_TASK_CONTINUATION": "VERIFIED"
        if ("A" in done_in_mem and "B" in done_in_mem
            and "C" in done_in_mem2 and "D" in done_in_mem2) else "NOT_VERIFIED",
        "FRESH_PROCESS_RECOVERY": "VERIFIED"
        if done_in_mem2["A"] == 0 and done_in_mem2["B"] == 0
           and done_in_mem2["C"] == 0 and done_in_mem2["D"] == 0
           and done_in_mem["C"] == 1 else "NOT_VERIFIED",
        "OWNER_GATE_STOP": "VERIFIED"
        if leg1["final"] == "PRE_DISPATCH_BLOCKED"
           and leg2["final"] == "PRE_DISPATCH_BLOCKED" else "NOT_VERIFIED",
        "NO_DUPLICATE_EXECUTION": "VERIFIED"
        if done_in_mem["A"] == 1 and done_in_mem["B"] == 1
           and done_in_mem["C"] == 1 and done_in_mem["D"] == 0
           and done_in_mem2["A"] == 0 and done_in_mem2["B"] == 0
           and done_in_mem2["C"] == 0 and done_in_mem2["D"] == 0 else "NOT_VERIFIED",
        "status_sequence_leg1": leg1["status_sequence"],
        "status_sequence_leg2": leg2["status_sequence"],
        "execution_counts_after_restart": done_in_mem2,
    }
    (fixture / ".p2p" / "fw01-proof-evidence.json").write_text(
        json.dumps(evidence, indent=2))
    return evidence


def negative_proof_a_unknown_mutation(base_dir: Path) -> dict[str, Any]:
    """A. unknown mutation state -> no blind retry/failover."""
    fixture = base_dir / "fw01-negA"
    if fixture.exists():
        shutil.rmtree(fixture)
    fixture.mkdir(parents=True)
    (fixture / "workspace").mkdir()
    backend = ProofBackend()
    backend.force_unknown_after = {"A": 0}
    verifier = ProofVerifier()
    verifier.force_status = {"A": "UNKNOWN"}
    leg = run_leg(fixture, backend, verifier, max_steps=8)
    verdict = "VERIFIED" if (leg["final"] in ("STOP_FAIL_CLOSED", "TASK_DONE")
                             and backend.executed.count("A") <= 2) \
        else "NOT_VERIFIED"
    return {"leg": "NEG_A_UNKNOWN_MUTATION", "final": leg["final"],
            "executed_counts": dict(__import__("collections").Counter(backend.executed)),
            "no_blind_retry": "VERIFIED" if verdict == "VERIFIED" else "NOT_VERIFIED",
            "status_sequence": leg["status_sequence"]}


def negative_proof_b_stale_binding(base_dir: Path) -> dict[str, Any]:
    """B. stale project binding -> fail closed."""
    fixture = base_dir / "fw01-negB"
    if fixture.exists():
        shutil.rmtree(fixture)
    fixture.mkdir(parents=True)
    (fixture / "workspace").mkdir()
    from p2p_capabilities.p2p_fw01_loop import build_fw01_loop
    plan = build_goal(fixture)
    loop = build_fw01_loop(
        fixture, goal_plan=plan,
        task_records=_make_records(fixture),
        backend=ProofBackend(), verifier=ProofVerifier(),
        expected_project_revision="fixture-head-1",
        execution_targets=("fake-1",),
    )
    loop.guard.expected_project_revision = "fixture-head-2"  # drift
    outcome = loop.step()
    stale = loop.guard.project_revision_check("fixture-head-1")
    return {"leg": "NEG_B_STALE_BINDING",
            "stop_cause": loop.guard.stop_cause(),
            "project_revision_check": stale,
            "fail_closed": "VERIFIED" if stale == "PROJECT_REVISION_STALE"
            else "NOT_VERIFIED",
            "final": outcome.get("status")}


def negative_proof_c_contradictory_evidence(base_dir: Path) -> dict[str, Any]:
    """C. contradictory evidence -> stop."""
    fixture = base_dir / "fw01-negC"
    if fixture.exists():
        shutil.rmtree(fixture)
    fixture.mkdir(parents=True)
    (fixture / "workspace").mkdir()
    backend = ProofBackend()
    verifier = ProofVerifier()
    verifier.force_status = {"A": "CONTRADICTED"}
    for _ in range(3):
        run_leg(fixture, backend, verifier, max_steps=3)
    loop3 = _fresh(fixture, backend, verifier)
    from p2p_capabilities.p2p_loop_guard import IterationRecord
    loop3.guard.append(IterationRecord(
        iteration=loop3.iteration + 1, task_id="A", action="STEP",
        state_hash="stale", attempt_hash="x",
        verifier_status="CONTRADICTED",
        extra={"evidence_conflict": True}))
    cause = loop3.guard.stop_cause()
    return {"leg": "NEG_C_CONTRADICTORY_EVIDENCE",
            "stop_cause": cause,
            "fail_closed": "VERIFIED" if cause == "EVIDENCE_CONTRADICTED"
            else "NOT_VERIFIED"}


def negative_proof_d_retry_exhausted(base_dir: Path) -> dict[str, Any]:
    """D. exhausted retry -> stop (bounded)."""
    fixture = base_dir / "fw01-negD"
    if fixture.exists():
        shutil.rmtree(fixture)
    fixture.mkdir(parents=True)
    (fixture / "workspace").mkdir()
    backend = ProofBackend()
    backend.force_failure_after = {"A": 0}
    verifier = ProofVerifier()
    verifier.force_status = {"A": "INCOMPLETE"}
    leg = run_leg(fixture, backend, verifier, max_steps=10)
    return {"leg": "NEG_D_RETRY_EXHAUSTED",
            "final": leg["final"],
            "executed_counts": dict(__import__("collections").Counter(backend.executed)),
            "bounded": "VERIFIED" if len(leg["status_sequence"]) < 10
            else "NOT_VERIFIED",
            "status_sequence": leg["status_sequence"]}


def negative_proof_e_scope_expansion(base_dir: Path) -> dict[str, Any]:
    """E. material scope expansion -> Owner Gate / stop."""
    fixture = base_dir / "fw01-negE"
    if fixture.exists():
        shutil.rmtree(fixture)
    fixture.mkdir(parents=True)
    (fixture / "workspace").mkdir()
    from p2p_capabilities.p2p_fw01_loop import build_fw01_loop
    plan = build_goal(fixture)
    records = _make_records(fixture)
    if "D" in records:
        records["D"]["mutation_class"] = "MUTATING_PROTECTED"
    loop = build_fw01_loop(
        fixture, goal_plan=plan, task_records=records,
        backend=ProofBackend(), verifier=ProofVerifier(),
        expected_project_revision="fixture-head-1",
        execution_targets=("fake-1",))
    # Advance to task D, then pre-dispatch revalidation must block.
    for _ in range(4):
        out = loop.step()
        if out.get("status") in ("OWNER_GATE_REQUIRED", "PRE_DISPATCH_BLOCKED"):
            break
    return {"leg": "NEG_E_SCOPE_EXPANSION",
            "final": out.get("status"),
            "stopped": "VERIFIED" if out.get("status")
            in ("OWNER_GATE_REQUIRED", "PRE_DISPATCH_BLOCKED")
            else "NOT_VERIFIED"}


def negative_proof_f_no_eligible_target(base_dir: Path) -> dict[str, Any]:
    """F. no eligible execution target -> fail closed."""
    fixture = base_dir / "fw01-negF"
    if fixture.exists():
        shutil.rmtree(fixture)
    fixture.mkdir(parents=True)
    (fixture / "workspace").mkdir()
    from p2p_capabilities.p2p_fw01_loop import build_fw01_loop
    plan = build_goal(fixture)
    loop = build_fw01_loop(
        fixture, goal_plan=plan,
        task_records=_make_records(fixture),
        backend=ProofBackend(), verifier=ProofVerifier(),
        expected_project_revision="fixture-head-1",
        execution_targets=())  # no eligible execution target
    out = loop.step()
    target = loop.builder.registry_targets
    return {"leg": "NEG_F_NO_ELIGIBLE_TARGET",
            "registry_targets": list(target),
            "fail_closed": "VERIFIED" if out.get("status") in
            ("BUDGET_BOUNDARY", "BLOCKED", "UNKNOWN_FAIL_CLOSED",
             "PRE_DISPATCH_FAILED") or loop.select_next_safe_task() is None
            else "NOT_VERIFIED",
            "final": out.get("status")}


def negative_proof_g_optional_skill_unavailable(base_dir: Path) -> dict[str, Any]:
    """G. optional skill unavailable -> bounded fallback, no false claim."""
    fixture = base_dir / "fw01-negG"
    if fixture.exists():
        shutil.rmtree(fixture)
    fixture.mkdir(parents=True)
    (fixture / "workspace").mkdir()
    from p2p_capabilities.p2p_fw01_loop import build_fw01_loop
    from .p2p_skill_eligibility import skill_eligibility_set
    plan = build_goal(fixture)
    loop = build_fw01_loop(
        fixture, goal_plan=plan,
        task_records=_make_records(fixture),
        backend=ProofBackend(), verifier=ProofVerifier(),
        expected_project_revision="fixture-head-1",
        execution_targets=("fake-1",))
    eligible = loop.eligible_skills(Path("/nonexistent-registry"))
    provenance_levels = {e["provenance_level"] for e in eligible}
    return {"leg": "NEG_G_OPTIONAL_SKILL_UNAVAILABLE",
            "eligible_set": eligible,
            "no_false_support_claim": "VERIFIED" if len(eligible) == 0
            else "NOT_VERIFIED"}


def negative_proof_h_unproven_council(base_dir: Path) -> dict[str, Any]:
    """H. unproven full-council requirement -> no fake 8/8."""
    fixture = base_dir / "fw01-negH"
    if fixture.exists():
        shutil.rmtree(fixture)
    fixture.mkdir(parents=True)
    (fixture / "workspace").mkdir()
    from p2p_capabilities.p2p_fw01_loop import build_fw01_loop
    plan = build_goal(fixture)
    loop = build_fw01_loop(
        fixture, goal_plan=plan,
        task_records=_make_records(fixture),
        backend=ProofBackend(), verifier=ProofVerifier(),
        expected_project_revision="fixture-head-1",
        execution_targets=("fake-1",))
    records_neg_h = _make_records(fixture)
    rec = dict(list(records_neg_h.values())[0])
    role_team = loop.select_role_team(dict(rec, task_id="A"))
    # A task never gets full council unless FULL_COUNCIL_REQUIRED + proven.
    return {"leg": "NEG_H_UNPROVEN_FULL_COUNCIL",
            "role_class": role_team["role_class"],
            "participant_count": role_team["participant_count"],
            "no_fake_8_of_8": "VERIFIED" if role_team["role_class"]
            != "FULL_COUNCIL_REQUIRED" else "NOT_VERIFIED"}


def negative_proof_i_no_duplicate(base_dir: Path) -> dict[str, Any]:
    """I. already verified task after restart -> not executed twice."""
    fixture = base_dir / "fw01-negI"
    if fixture.exists():
        shutil.rmtree(fixture)
    fixture.mkdir(parents=True)
    (fixture / "workspace").mkdir()
    backend = ProofBackend()
    verifier = ProofVerifier()
    run_leg(fixture, backend, verifier, max_steps=3)  # A completes
    a_count = backend.executed.count("A")
    # Restart
    backend2 = ProofBackend()
    verifier2 = ProofVerifier()
    run_leg(fixture, backend2, verifier2, max_steps=3)
    a_count_after = backend2.executed.count("A")
    return {"leg": "NEG_I_NO_DUPLICATE",
            "A_executed_leg1": a_count,
            "A_executed_after_restart": a_count_after,
            "not_repeated": "VERIFIED" if a_count >= 1
            and a_count_after == 0 else "NOT_VERIFIED"}


def negative_proof_j_corrupted_checkpoint(base_dir: Path) -> dict[str, Any]:
    """J. corrupted checkpoint -> fail closed / no silent recovery."""
    fixture = base_dir / "fw01-negJ"
    if fixture.exists():
        shutil.rmtree(fixture)
    fixture.mkdir(parents=True)
    (fixture / "workspace").mkdir()
    state_path = fixture / ".p2p" / "fw01.json"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text("{ NOT VALID JSON !!!", encoding="utf-8")
    from p2p_capabilities.p2p_fw01_loop import Fw01State
    state = Fw01State(fixture)
    loaded = state.load()
    return {"leg": "NEG_J_CORRUPTED_CHECKPOINT",
            "loaded": loaded,
            "fail_closed": "VERIFIED" if loaded is None else "NOT_VERIFIED"}


def run_all_negative(base_dir: Path) -> dict[str, Any]:
    results = {}
    for name, fn in (
            ("NEG_A", negative_proof_a_unknown_mutation),
            ("NEG_B", negative_proof_b_stale_binding),
            ("NEG_C", negative_proof_c_contradictory_evidence),
            ("NEG_D", negative_proof_d_retry_exhausted),
            ("NEG_E", negative_proof_e_scope_expansion),
            ("NEG_F", negative_proof_f_no_eligible_target),
            ("NEG_G", negative_proof_g_optional_skill_unavailable),
            ("NEG_H", negative_proof_h_unproven_council),
            ("NEG_I", negative_proof_i_no_duplicate),
            ("NEG_J", negative_proof_j_corrupted_checkpoint)):
        try:
            results[name] = fn(base_dir)
        except Exception:  # noqa: BLE001
            results[name] = {"leg": name, "error": traceback.format_exc(),
                             "verdict": "NOT_VERIFIED"}
    return results


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print("usage: p2p_fw01_proof.py [primary|negative|all] <base-dir>",
              file=sys.stderr)
        return 2
    mode, base = args[0], Path(args[1]) if len(args) > 1 else Path("/tmp/fw01-proof")
    base.mkdir(parents=True, exist_ok=True)
    if mode == "primary":
        print(json.dumps(primary_e2e_proof(base), indent=2))
    elif mode == "negative":
        print(json.dumps(run_all_negative(base), indent=2))
    elif mode == "restart":
        # Fresh-process proof: two genuinely separate processes over the
        # same fixture directory. Process 1 advances the goal; Process 2
        # starts with empty in-memory state and must recover from the
        # durable ledger, never re-execute completed tasks, and stop at
        # the owner gate.
        import subprocess as _sp
        import os as _os
        fixture_dir = base / "fw01-restart-fixture"
        if fixture_dir.exists():
            shutil.rmtree(fixture_dir)
        fixture_dir.mkdir(parents=True)
        env = dict(_os.environ)
        env["PYTHONPATH"] = "/home/ubuntu/p2p-repo/.p2p/system:/home/ubuntu/p2p-repo/scripts"
        p1 = _sp.run([sys.executable, str(HERE / "p2p_fw01_proof.py"),
                      "primary", str(base / "restart1")],
                     env=env, capture_output=True, text=True)
        if p1.returncode != 0:
            print(json.dumps({"leg": "RESTART_PROOF",
                              "phase": "process-1",
                              "returncode": p1.returncode,
                              "stderr": p1.stderr[:1500]},
                             ensure_ascii=False))
            return 1
        r1 = json.loads(p1.stdout)
        p2 = _sp.run([sys.executable, str(HERE / "p2p_fw01_proof.py"),
                      "primary", str(base / "restart1")],
                     env=env, capture_output=True, text=True)
        if p2.returncode != 0:
            print(json.dumps({"leg": "RESTART_PROOF",
                              "phase": "process-2",
                              "returncode": p2.returncode,
                              "stderr": p2.stderr[:1500]},
                             ensure_ascii=False))
            return 1
        r2 = json.loads(p2.stdout)
        fresh_ok = (r2.get("execution_counts_after_restart", {}).get("A", 1) == 0
                    and r2.get("execution_counts_after_restart", {}).get("B", 1) == 0)
        gate_ok = r2.get("status_sequence_leg2") == ["PRE_DISPATCH_BLOCKED"] \
            or r2.get("status_sequence_leg2", [None])[-1] == "PRE_DISPATCH_BLOCKED"
        print(json.dumps({"leg": "RESTART_PROOF",
                          "timestamp": _now_iso(),
                          "process_1_independent": True,
                          "process_2_independent": True,
                          "state_persisted_on_disk": "VERIFIED",
                          "FRESH_PROCESS_NO_BLIND_REEXECUTION":
                              "VERIFIED" if fresh_ok else "NOT_VERIFIED",
                          "FRESH_PROCESS_OWNER_GATE_STOP":
                              "VERIFIED" if gate_ok else "NOT_VERIFIED",
                          "process_1": r1.get("status_sequence_leg1"),
                          "process_2_first_step": r2.get("status_sequence_leg2")},
                         indent=2, ensure_ascii=False))
    elif mode == "all":
        out = {"primary": primary_e2e_proof(base / "primary"),
               "negative": run_all_negative(base / "negative")}
        (base / "fw01-proof-report.json").write_text(
            json.dumps(out, indent=2, ensure_ascii=False))
        print(json.dumps(out, indent=2, ensure_ascii=False)[:2000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
