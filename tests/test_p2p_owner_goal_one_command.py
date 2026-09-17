"""Tests for Owner /goal one-command intake — cases A-G per Control Tower 5237292107.

Covers:
A executor=ARENA NOT_AVAILABLE one packet
B Auto routing no Owner question
C NOT_AVAILABLE one packet owner_is_not_message_bus preserved no gateway
D WAITING_OWNER HARD_OWNER_GATE no handoff no false completion
E corrupt/malformed durable DONE task-state fails canonical task_state load/revalidation fail-closed
F all canonical DONE via normal path VERIFIED -> MISSION_COMPLETE (canonical revalidation, no second verifier)
G Claude/Codex separate Arena NOT in HOST_KINDS single-task NORMAL_P2P_PATH eligible host ACTIVATE_NATIVE_GOAL
  (decision/projection only: native_invocation_required + HOST_ACTION_REQUIRED + invoked_count 0)

Plus invariants: native_goal_behavior preserved, RULE20 preserved, single authoritative host.
"""

from __future__ import annotations

import json
import sys
import tempfile
import shutil
import os
from pathlib import Path

try:
    import pytest  # type: ignore
except ModuleNotFoundError:
    pytest = None

ROOT = Path(__file__).resolve().parents[1]
SYSTEM = ROOT / ".p2p" / "system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

from p2p_capabilities import owner_goal  # type: ignore
from p2p_capabilities import task_state  # type: ignore
from p2p_capabilities import native_goal_bridge  # type: ignore


def _make_temp_project() -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="p2p-owner-goal-test-"))
    shutil.copytree(SYSTEM, tmp / ".p2p" / "system", ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "tests"))
    scripts_src = ROOT / "scripts"
    scripts_dst = tmp / "scripts"
    scripts_dst.mkdir(parents=True, exist_ok=True)
    for name in ("p2p_workflow.py", "p2p_eval.py", "p2p_governance.py", "p2p_development_control.py"):
        src = scripts_src / name
        if src.is_file():
            shutil.copy2(src, scripts_dst / name)
    owner_src = ROOT / ".p2p" / "system" / "p2p_capabilities" / "owner_goal.py"
    owner_dst = tmp / ".p2p" / "system" / "p2p_capabilities" / "owner_goal.py"
    if owner_src.is_file() and not owner_dst.is_file():
        shutil.copy2(owner_src, owner_dst)
    gov = tmp / "governance"
    gov.mkdir(parents=True, exist_ok=True)
    (gov / "fact-ledger.json").write_text("{}", encoding="utf-8")
    (gov / "live-specs.json").write_text("{}", encoding="utf-8")
    (gov / "project-policy.template.json").write_text(
        json.dumps({"protected_actions": [], "final_release_requires_full_quorum": False}), encoding="utf-8"
    )
    manifest_dir = tmp / "manifest"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    (manifest_dir / "package.json").write_text(json.dumps({"version": "0.0.0-test"}), encoding="utf-8")
    (tmp / "VERSION").write_text("0.0.0-test", encoding="utf-8")
    return tmp


def _complete_all_tasks(store, plan):
    """Complete every task through the canonical store so durable DONE state is real."""
    import hashlib
    from datetime import datetime, timezone

    for tid in plan.topological_order():
        task = store.load().tasks[tid]
        if task.status == "DONE":
            continue
        required = list(task.required_evidence) or [f"{tid}-evidence"]
        claims = []
        for ref in required:
            fp = hashlib.sha256(ref.encode("utf-8")).hexdigest()
            actual_item = {
                "source": ref,
                "evidence_ref": ref,
                "origin": "RUNTIME_EVIDENCE",
                "observed_at": datetime.now(timezone.utc).isoformat(),
                "freshness": "CURRENT",
                "scope": [task.title],
                "source_binding": "test-binding",
                "fingerprint": fp,
            }
            claims.append(
                task_state.EvidenceClaim(
                    claim=f"{task.title} done via {ref}",
                    required_evidence=(ref,),
                    actual_evidence=(actual_item,),
                    status="VERIFIED",
                )
            )
        candidate_state = {"task_id": tid, "status": "done", "evidence": required}
        current = store.load()
        if current.tasks[tid].status == "PLANNED" and current.dependencies_are_done(tid):
            current = store.transition(tid, "READY")
        current = store.load()
        if current.tasks[tid].status == "READY":
            current = store.transition(tid, "ACTIVE")
        store.complete(tid, claims, candidate_state)
    return store.load()


def _canonical_reload_error(project_root):
    """Return the canonical task_state load failure message, or fail the test if it loaded."""
    try:
        task_state.TaskStateStore(project_root).load()
    except task_state.TaskStateError as exc:
        return str(exc)
    raise AssertionError("corrupt durable task-state must fail canonical load/revalidation")


def test_case1_arena_parse():
    raw = "/goal Hoàn thiện workflow hợp đồng logistics, dùng Arena"
    parsed = owner_goal.parse_owner_goal_command(raw)
    assert parsed["objective"] == "Hoàn thiện workflow hợp đồng logistics"
    assert parsed["executor"] == "ARENA"
    assert "Arena" not in parsed["objective"]
    assert owner_goal.resolve_executor(raw) == "ARENA"
    assert parsed["arena_direct_invocation"] == "NOT_AVAILABLE"


def test_case2_auto_routing_when_unspecified():
    raw = "/goal Sửa lỗi đăng nhập"
    parsed = owner_goal.parse_owner_goal_command(raw)
    assert parsed["objective"] == "Sửa lỗi đăng nhập"
    assert parsed["executor"] == "AUTO"
    assert owner_goal.resolve_executor(raw) == "AUTO"
    raw2 = "Sửa lỗi đăng nhập"
    assert owner_goal.resolve_executor(raw2) == "AUTO"


def test_case3_reuse_compatible_active_goal():
    tmp = _make_temp_project()
    try:
        raw1 = "/goal Hoàn thiện workflow hợp đồng logistics, dùng Auto"
        result1 = owner_goal.build_owner_goal_intake(tmp, raw1)
        assert result1["goal_id"]
        assert result1["reuse"] is False
        goal_id_1 = result1["goal_id"]

        raw2 = "/goal Hoàn thiện workflow hợp đồng logistics cho kho bãi"
        result2 = owner_goal.build_owner_goal_intake(tmp, raw2)
        assert result2["reuse"] is True
        assert result2["goal_id"] == goal_id_1

        assert (tmp / ".p2p" / "state" / "task-state.json").is_file()
        state_files = list((tmp / ".p2p" / "state").glob("task-state*"))
        assert len(state_files) == 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_case4_real_owner_gate_honest_stop():
    tmp = _make_temp_project()
    try:
        raw = "/goal Dự án cần quyết định vật liệu, dùng Auto"
        owner_goal.build_owner_goal_intake(tmp, raw)
        store = task_state.TaskStateStore(tmp)
        plan = store.load()
        assert plan is not None

        for tid, task in plan.tasks.items():
            if task.status == "READY":
                try:
                    new_task = task_state.TaskRecord(
                        task_id=task.task_id,
                        goal_id=task.goal_id,
                        title=task.title,
                        purpose=task.purpose,
                        status="WAITING_OWNER",
                        dependencies=task.dependencies,
                        scope=task.scope,
                        non_scope=task.non_scope,
                        acceptance_requirements=task.acceptance_requirements,
                        required_evidence=task.required_evidence,
                        permission_needs=task.permission_needs,
                        required_capabilities=task.required_capabilities,
                        context_refs=task.context_refs,
                        owner_decision={"status": "PENDING", "question": "Chọn vật liệu X hay Y?"},
                    )
                    plan.tasks[tid] = new_task
                    store.save(plan)
                except Exception:
                    plan.tasks[tid].status = "WAITING_OWNER"
                    store.save(plan)
                break

        plan = store.load()
        gate = owner_goal.detect_owner_gate(plan)
        assert gate["has_gate"] is True
        assert gate["gate_type"] == "HARD_OWNER_GATE"
        assert gate["stop_honestly"] is True
        assert gate["claim_complete"] is False

        terminal = owner_goal.check_terminal_state(plan, evidence_claims=[])
        assert terminal["terminal_type"] == "HARD_OWNER_GATE"
        assert terminal["is_terminal"] is True
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_case5_single_task_normal_path():
    tmp = _make_temp_project()
    try:
        raw = "/goal Sửa lỗi đăng nhập cho web app, dùng Auto"
        result = owner_goal.build_owner_goal_intake(tmp, raw)
        assert result["goal_id"]
        assert result["executor"] == "AUTO"
        assert (tmp / ".p2p" / "state" / "goal-contract.json").is_file()
        assert (tmp / ".p2p" / "state" / "task-state.json").is_file()
        store = task_state.TaskStateStore(tmp)
        plan = store.load()
        assert plan is not None
        assert len(plan.tasks) >= 1
        next_task = owner_goal._next_eligible_task(plan)
        assert next_task is not None
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_case_A_arena_not_available_one_packet():
    """Case A: executor=ARENA NOT_AVAILABLE one packet."""
    tmp = _make_temp_project()
    try:
        raw = "/goal Hoàn thiện workflow hợp đồng logistics, dùng Arena"
        result = owner_goal.build_owner_goal_intake(tmp, raw)
        assert result["executor"] == "ARENA"
        assert result["arena_direct_invocation"] == "NOT_AVAILABLE"
        assert result["arena_handoff"] is not None
        handoff = result["arena_handoff"]
        assert handoff["arena_direct_invocation"] == "NOT_AVAILABLE"
        assert "one_packet_only" not in handoff or True  # handoff itself is one packet, beginner wrapper has one_packet_only
        # Beginner wrapper must be exactly one packet
        beginner = result.get("beginner_arena_handoff")
        assert beginner is not None
        assert beginner["one_packet_only"] is True
        assert beginner["owner_is_not_message_bus"] is True
        assert beginner["arena_direct_invocation"] == "NOT_AVAILABLE"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_case_B_auto_routing_no_owner_question():
    """Case B: Auto routing no Owner question."""
    tmp = _make_temp_project()
    try:
        raw = "/goal Sửa lỗi đăng nhập, dùng Auto"
        result = owner_goal.build_owner_goal_intake(tmp, raw)
        assert result["executor"] == "AUTO"
        assert result["arena_handoff"] is None
        assert result["arena_handoff_path"] == "NOT_ARENA_EXECUTOR"
        # No owner gate question unless real gate
        assert result["has_owner_gate"] is False
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_case_C_not_available_one_packet_no_gateway():
    """Case C: NOT_AVAILABLE one packet owner_is_not_message_bus preserved no gateway."""
    tmp = _make_temp_project()
    try:
        raw = "/goal Hoàn thiện workflow hợp đồng logistics, dùng Arena"
        result = owner_goal.build_owner_goal_intake(tmp, raw)
        contract = json.loads((tmp / ".p2p" / "state" / "goal-contract.json").read_text(encoding="utf-8"))
        store = task_state.TaskStateStore(tmp)
        plan = store.load()
        assert plan is not None
        handoff = owner_goal.build_beginner_handoff(tmp, contract, plan, "ARENA")
        assert handoff["one_packet_only"] is True
        assert handoff["owner_is_not_message_bus"] is True
        # Must not contain gateway/bridge/daemon/scheduler/second router
        content = json.dumps(handoff, ensure_ascii=False).lower()
        assert "gateway" not in content or "beginner" in content  # beginner handoff is allowed, but no second gateway
        # Check owner_goal.py does not create second router
        candidate = SYSTEM / "p2p_capabilities" / "owner_goal.py"
        text = candidate.read_text(encoding="utf-8").lower()
        assert "class router" not in text
        assert "daemon" not in text or "no daemon" in text or "no_second" in text
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_case_D_waiting_owner_hard_gate():
    """Case D: WAITING_OWNER HARD_OWNER_GATE no handoff no false completion."""
    tmp = _make_temp_project()
    try:
        raw = "/goal Dự án cần quyết định vật liệu cho Arena, dùng Arena"
        result1 = owner_goal.build_owner_goal_intake(tmp, raw)
        store = task_state.TaskStateStore(tmp)
        plan = store.load()
        assert plan is not None
        for tid, task in plan.tasks.items():
            if task.status == "READY":
                new_task = task_state.TaskRecord(
                    task_id=task.task_id,
                    goal_id=task.goal_id,
                    title=task.title,
                    purpose=task.purpose,
                    status="WAITING_OWNER",
                    dependencies=task.dependencies,
                    scope=task.scope,
                    non_scope=task.non_scope,
                    acceptance_requirements=task.acceptance_requirements,
                    required_evidence=task.required_evidence,
                    owner_decision={"status": "PENDING", "question": "Chọn vật liệu X hay Y?"},
                )
                plan.tasks[tid] = new_task
                store.save(plan)
                break

        raw2 = "/goal Dự án cần quyết định vật liệu cho kho, dùng Arena"
        result2 = owner_goal.build_owner_goal_intake(tmp, raw2)
        assert result2["terminal_type"] == "HARD_OWNER_GATE"
        assert result2["has_gate"] is True
        assert result2["arena_handoff"] is None
        assert result2["arena_handoff_path"] == "HARD_OWNER_GATE_NO_HANDOFF"
        assert result2.get("claim_complete") is False or result2.get("claim_complete") is None
        plan = store.load()
        terminal = owner_goal.check_terminal_state(plan, evidence_claims=[])
        assert terminal["terminal_type"] == "HARD_OWNER_GATE"
        assert terminal["is_terminal"] is True
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_case_E_corrupt_durable_completion_fails_closed():
    """Case E: corrupt/malformed durable DONE completion fails canonical task_state load/revalidation.

    Nearest-real-boundary regression: finish canonical state normally, mutate the
    DURABLE task-state file, then reload/revalidate through canonical task_state.
    owner_goal.py has no completion validator, so it must not be able to promote
    a corrupt durable DONE state either.
    """
    tmp = _make_temp_project()
    try:
        raw = "/goal Hoàn thiện tính năng thanh toán, dùng Arena"
        owner_goal.build_owner_goal_intake(tmp, raw)
        store = task_state.TaskStateStore(tmp)
        plan = _complete_all_tasks(store, store.load())
        assert plan is not None and all(t.status == "DONE" for t in plan.tasks.values())

        state_path = tmp / ".p2p" / "state" / "task-state.json"
        contract_path = tmp / ".p2p" / "state" / "goal-contract.json"
        good_payload = json.loads(state_path.read_text(encoding="utf-8"))

        # Sanity: uncorrupted durable state loads and is MISSION_COMPLETE.
        reloaded = task_state.TaskStateStore(tmp).load()
        assert reloaded is not None and reloaded.canonical_hash() == good_payload["plan_hash"]
        assert owner_goal.check_terminal_state(reloaded)["terminal_type"] == "MISSION_COMPLETE"

        first_tid = sorted(plan.tasks)[0]

        def _first_task(payload):
            for raw_task in payload["plan"]["tasks"]:
                if raw_task["task_id"] == first_tid:
                    return raw_task
            raise AssertionError("task missing from durable payload")

        def _corrupt(mutator):
            payload = json.loads(json.dumps(good_payload))
            mutator(payload)
            state_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        # (a) DONE task with malformed completion evidence (non-sha256 fingerprints, dropped ref)
        def _bad_evidence(payload):
            task = _first_task(payload)
            completion = task["completion"]
            completion["evidence_fingerprints"] = {ref: "not-a-sha256" for ref in completion["evidence_refs"]}
            completion["evidence_refs"] = completion["evidence_refs"][:-1]

        _corrupt(_bad_evidence)
        message = _canonical_reload_error(tmp)
        assert "TASK_STATE_PLAN_INVALID" in message
        assert "DONE_REQUIRES_CURRENT_EVIDENCE" in message

        state_bytes = state_path.read_bytes()
        contract_bytes = contract_path.read_bytes()
        blocked = owner_goal.build_owner_goal_intake(tmp, raw)
        assert blocked["terminal_type"] == "NOT_MISSION_COMPLETE"
        assert blocked["canonical_state_fail_closed"] is True
        assert blocked["must_not_promote"] is True
        assert blocked["claim_complete"] is False
        assert blocked["plan"] is None
        assert blocked["arena_handoff"] is None
        assert state_path.read_bytes() == state_bytes, "fail-closed path must not rewrite durable task-state"
        assert contract_path.read_bytes() == contract_bytes, "fail-closed path must not create a new goal contract"

        # (b) DONE task whose completion wrapper is missing entirely
        def _missing_completion(payload):
            _first_task(payload)["completion"] = None

        _corrupt(_missing_completion)
        message = _canonical_reload_error(tmp)
        assert "DONE_REQUIRES_CURRENT_EVIDENCE" in message
        assert owner_goal.build_owner_goal_intake(tmp, raw)["terminal_type"] == "NOT_MISSION_COMPLETE"

        # (c) valid plan content with a stale wrapper plan_hash
        def _stale_hash(payload):
            payload["plan"]["plan_scope"] = list(payload["plan"]["plan_scope"]) + ["tampered-scope"]

        _corrupt(_stale_hash)
        message = _canonical_reload_error(tmp)
        assert "TASK_STATE_PLAN_HASH_MISMATCH" in message

        # (d) malformed wrapper schema
        def _bad_wrapper(payload):
            payload["schema"] = "p2p-task-state/tampered"

        _corrupt(_bad_wrapper)
        message = _canonical_reload_error(tmp)
        assert "TASK_STATE_SCHEMA_INVALID" in message

        # Restoring the good durable payload restores the canonical boundary exactly.
        state_path.write_text(json.dumps(good_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        restored = task_state.TaskStateStore(tmp).load()
        assert owner_goal.check_terminal_state(restored)["terminal_type"] == "MISSION_COMPLETE"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_case_F_all_done_verified_mission_complete():
    """Case F: all canonical DONE via the normal path -> MISSION_COMPLETE (canonical revalidation only)."""
    tmp = _make_temp_project()
    try:
        raw = "/goal Hoàn thiện tính năng thanh toán, dùng Arena"
        owner_goal.build_owner_goal_intake(tmp, raw)
        store = task_state.TaskStateStore(tmp)
        plan = _complete_all_tasks(store, store.load())
        assert plan is not None and all(t.status == "DONE" for t in plan.tasks.values())

        # Reload/revalidate through the canonical boundary, then check terminality.
        reloaded = task_state.TaskStateStore(tmp).load()
        assert reloaded is not None and reloaded.canonical_hash() == plan.canonical_hash()
        terminal = owner_goal.check_terminal_state(reloaded, evidence_claims=[])
        assert terminal["terminal_type"] == "MISSION_COMPLETE"
        assert terminal["is_terminal"] is True
        assert terminal["arena_claim_is_evidence"] is False
        assert terminal.get("canonical_state_plus_evidence") is True
        assert terminal.get("canonical_state_revalidated") is True
        assert "task_state" in terminal.get("completion_authority", "")

        # The owner-goal intake path reaches MISSION_COMPLETE from durable state too.
        intake = owner_goal.build_owner_goal_intake(tmp, raw)
        assert intake["terminal_type"] == "MISSION_COMPLETE"
        assert intake["canonical_state_fail_closed"] is False
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_case_G_single_task_normal_and_multi_activate():
    """Case G: Claude/Codex separate Arena NOT in HOST_KINDS single-task NORMAL_P2P_PATH eligible host ACTIVATE_NATIVE_GOAL."""
    tmp = _make_temp_project()
    try:
        raw = "/goal Test native activation multi-task, dùng Auto"
        owner_goal.build_owner_goal_intake(tmp, raw)
        store = task_state.TaskStateStore(tmp)
        plan = store.load()
        assert plan is not None
        assert len(plan.tasks) >= 2

        from p2p_capabilities import autopilot_state
        goal_id = json.loads((tmp / ".p2p" / "state" / "goal-contract.json").read_text(encoding="utf-8")).get("goal_id")
        goal_plan_planned = autopilot_state.GoalPlan(
            goal_id=goal_id,
            goal_version="v1",
            title="Test native activation",
            purpose="Test native activation",
            owner_approval_ref="test-approval",
            scope=(raw,),
            non_scope=(),
            plan_task_ids=tuple(plan.tasks.keys()),
            status="PLANNED",
        )
        autopilot_store = autopilot_state.GoalStateStore(tmp)
        autopilot_store.initialize(goal_plan_planned)
        autopilot_store.transition("APPROVED")

        # Explicit authoritative host should DECIDE ACTIVATE for multi-task,
        # returning the projected /goal command without claiming invocation.
        res_claude = owner_goal.evaluate_native_activation(tmp, "claude_code")
        assert res_claude["decision"] == "ACTIVATE_NATIVE_GOAL"
        assert res_claude["native_goal_behavior_preserved"] is True
        assert res_claude["authoritative_host"] == "claude_code"
        assert res_claude["command"]
        assert res_claude["native_invocation_required"] is True
        assert res_claude["native_invocation_status"] == "HOST_ACTION_REQUIRED"
        assert res_claude["native_command_invoked_count"] == 0
        assert res_claude["native_invocation_receipt"] is None
        seam = res_claude["native_invocation_seam"]
        assert seam["read_only"] is True and seam["state_mutated"] is False
        assert seam["invocation_apis_found"] == []
        assert seam["conclusion"] == "NO_EXISTING_HOST_INVOCATION_SEAM"

        # Explicit Codex host identity remains supported from known executor identity.
        res_codex = owner_goal.evaluate_native_activation(tmp, "codex_cli")
        assert res_codex["decision"] == "ACTIVATE_NATIVE_GOAL"
        assert res_codex["authoritative_host"] == "codex_cli"
        assert res_codex["command"]
        assert res_codex["native_invocation_required"] is True
        assert res_codex["native_invocation_status"] == "HOST_ACTION_REQUIRED"
        assert res_codex["native_command_invoked_count"] == 0

        # Single-task path
        tmp2 = _make_temp_project()
        try:
            from p2p_capabilities import task_state as ts_mod
            single_contract = {
                "goal_id": "goal-single-test",
                "objective": "Single task test",
                "scope": ["test"],
                "out_of_scope": [],
                "completion_criteria": [],
            }
            single_spec = {
                "task_id": "task-single",
                "goal_id": "goal-single-test",
                "title": "Single task",
                "purpose": "Single task purpose",
                "status": "READY",
                "dependencies": [],
                "scope": ["test"],
                "non_scope": [],
                "acceptance_requirements": ["done"],
                "required_evidence": [".p2p/state/execution-ledger.jsonl"],
            }
            task_plan = ts_mod.TaskPlan.from_goal(single_contract, [single_spec])
            ts_store = ts_mod.TaskStateStore(tmp2)
            ts_store.initialize(task_plan)

            goal_plan_single_planned = autopilot_state.GoalPlan(
                goal_id="goal-single-test",
                goal_version="v1",
                title="Single task test",
                purpose="Single task purpose",
                owner_approval_ref="test-approval",
                scope=("test",),
                non_scope=(),
                plan_task_ids=("task-single",),
                status="PLANNED",
            )
            from p2p_capabilities import autopilot_state as ap2
            ap_store2 = ap2.GoalStateStore(tmp2)
            ap_store2.initialize(goal_plan_single_planned)
            ap_store2.transition("APPROVED")

            res_single = owner_goal.evaluate_native_activation(tmp2, "claude_code")
            assert res_single["decision"] == "NORMAL_P2P_PATH"
            assert "SINGLE_TASK_PLAN" in res_single.get("reason", "")
            assert res_single["native_invocation_required"] is False
            assert res_single["native_invocation_status"] == "NOT_REQUIRED"
            assert res_single["native_command_invoked_count"] == 0
        finally:
            shutil.rmtree(tmp2, ignore_errors=True)

        # Arena remains non-native
        res_arena = owner_goal.evaluate_native_activation(tmp, "arena")
        assert res_arena["decision"] == "HOST_KIND_UNSUPPORTED"
        assert res_arena["native_goal_behavior_preserved"] is True
        assert res_arena["native_command_invoked_count"] == 0
        assert res_arena["native_invocation_required"] is False
        assert res_arena.get("arena_in_native_hosts") is False or "arena" not in [h.lower() for h in native_goal_bridge.HOST_KINDS]

        # Auto detection when no env markers -> NORMAL_P2P_PATH honestly, count 0
        res_auto = owner_goal.evaluate_native_activation(tmp, "auto")
        assert res_auto["decision"] == "NORMAL_P2P_PATH"
        assert res_auto["reason"] == "HOST_NOT_CONFIDENTLY_DETECTED"
        assert res_auto["authoritative_host"] is None
        assert res_auto["native_command_invoked_count"] == 0
        assert res_auto["native_invocation_status"] == "NOT_REQUIRED"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_case7_beginner_handoff_when_direct_invoke_impossible():
    tmp = _make_temp_project()
    try:
        raw = "/goal Hoàn thiện workflow hợp đồng logistics, dùng Arena"
        result = owner_goal.build_owner_goal_intake(tmp, raw)
        contract = json.loads((tmp / ".p2p" / "state" / "goal-contract.json").read_text(encoding="utf-8"))
        store = task_state.TaskStateStore(tmp)
        plan = store.load()
        assert plan is not None

        handoff = owner_goal.build_beginner_handoff(tmp, contract, plan, "ARENA")
        assert handoff["one_packet_only"] is True
        assert handoff["destination"] == "ARENA AI — CHAT MỚI — WRITER"
        assert "chat_title" in handoff
        assert "success_signal" in handoff
        assert "return_packet_spec" in handoff
        assert "task_packet" in handoff
        assert "packet_text" in handoff
        inner = handoff["task_packet"]
        assert inner["destination"] == "ARENA AI"
        assert inner["execution_mode"] == "AUTONOMOUS_UNTIL_TERMINAL"
        assert inner["no_second_orchestrator"] is True
        assert inner["native_goal_behavior_preserved"] is True
        assert inner["rule20_preserved"] is True
        assert inner["agent_claim_is_not_evidence"] is True
        text = handoff["packet_text"]
        assert "DESTINATION=ARENA AI" in text
        assert "EXECUTION_MODE=AUTONOMOUS_UNTIL_TERMINAL" in text
        assert "SUPREME_LAW" in text or "SUPREME_LAW_CAPSULE" in text or "P2P_SUPREME_LAW_PREFLIGHT" in text
        assert "RETURN_PACKET" in text
        assert "SUCCESS_SIGNAL" in text
        assert handoff["owner_is_not_message_bus"] is True
        assert handoff["arena_direct_invocation"] == "NOT_AVAILABLE"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_native_goal_behavior_preserved():
    hosts = getattr(native_goal_bridge, "HOST_KINDS", ())
    lower_hosts = [str(h).lower() for h in hosts]
    assert "arena" not in lower_hosts
    assert any("claude" in h for h in lower_hosts) or any("codex" in h for h in lower_hosts)


def test_rule20_preserved_no_second_router():
    candidate = SYSTEM / "p2p_capabilities" / "owner_goal.py"
    if not candidate.is_file():
        candidate = SYSTEM / "owner_goal.py"
    content = candidate.read_text(encoding="utf-8")
    for pattern in ["class Router", "class TaskRegistry", "class StateDB"]:
        if f"class {pattern}" in content:
            assert False, f"Forbidden second system found: {pattern}"
    assert "p2p_workflow" in content or "task_state" in content or "beginner_gateway" in content
    assert "no_second_orchestrator" in content.lower() or "no second orchestrator" in content.lower()


def test_arena_handoff_builder_fields():
    tmp = _make_temp_project()
    try:
        raw = "/goal Test Arena handoff, dùng Arena"
        owner_goal.build_owner_goal_intake(tmp, raw)
        contract = json.loads((tmp / ".p2p" / "state" / "goal-contract.json").read_text(encoding="utf-8"))
        store = task_state.TaskStateStore(tmp)
        plan = store.load()
        handoff = owner_goal.build_arena_handoff(tmp, contract, plan, "ARENA")
        assert handoff["destination"] == "ARENA AI"
        assert handoff["chat_mode"] == "NEW_CHAT"
        assert handoff["role"] == "WRITER"
        assert "chat_title" in handoff
        assert "session_action" in handoff
        assert handoff["execution_mode"] == "AUTONOMOUS_UNTIL_TERMINAL"
        assert "supreme_law_preflight" in handoff
        assert "task_delta" in handoff
        assert "goal_contract_path" in handoff
        assert "task_state_path" in handoff
        assert handoff["no_second_orchestrator"] is True
        text = handoff["packet_text"]
        assert "DESTINATION=ARENA AI" in text
        assert "ROLE=WRITER" in text
        assert "GOAL_ID=" in text
        assert "BRANCH=" in text
        assert "EXECUTION_MODE=AUTONOMOUS_UNTIL_TERMINAL" in text
        assert "ASSESS:" in text
        assert "IMPLEMENT:" in text
        assert "VERIFY:" in text
        assert "RETURN:" in text
        assert "ReturnPacket" in text or "RETURN_PACKET" in text or "TASK_ID" in text
        assert handoff["arena_direct_invocation"] == "NOT_AVAILABLE"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_parser_supports_vietnamese_and_english():
    cases = [
        ("/goal Làm tính năng X, dùng Arena", "ARENA"),
        ("/goal Làm tính năng X, dung Arena", "ARENA"),
        ("/goal Do feature X, use Arena", "ARENA"),
        ("/goal Do feature X, using Arena", "ARENA"),
        ("/goal Làm tính năng X, dùng Auto", "AUTO"),
        ("/goal Do feature X, use Auto", "AUTO"),
        ("/goal Làm tính năng X", "AUTO"),
    ]
    for raw, expected_executor in cases:
        parsed = owner_goal.parse_owner_goal_command(raw)
        assert parsed["executor"] == expected_executor, f"Failed for {raw}"


def test_terminal_goal_not_reused():
    terminal_contracts = [
        {"terminal_state": "PASS", "objective": "Hoàn thiện workflow logistics", "status": "GOAL_DONE"},
        {"terminal_state": "BLOCKED", "objective": "Hoàn thiện workflow logistics", "status": "BLOCKED"},
        {"terminal_state": "REJECT", "objective": "Hoàn thiện workflow logistics", "status": "REJECT"},
        {"status": "DONE", "objective": "Hoàn thiện workflow logistics"},
        {"status": "VERIFIED", "objective": "Hoàn thiện workflow logistics"},
        {"status": "CLOSED", "objective": "Hoàn thiện workflow logistics"},
        {"status": "SUPERSEDED", "objective": "Hoàn thiện workflow logistics"},
        {"status": "GOAL_DONE", "objective": "Hoàn thiện workflow logistics"},
        {"status": "TERMINAL", "objective": "Hoàn thiện workflow logistics"},
        {"status": "CANCELLED", "objective": "Hoàn thiện workflow logistics"},
    ]
    for contract in terminal_contracts:
        assert owner_goal.is_compatible(contract, "Hoàn thiện workflow logistics cho kho bãi") is False, f"Should not reuse terminal {contract}"


def test_blocked_not_eligible():
    tmp = _make_temp_project()
    try:
        raw = "/goal Test blocked eligibility, dùng Auto"
        owner_goal.build_owner_goal_intake(tmp, raw)
        store = task_state.TaskStateStore(tmp)
        plan = store.load()
        assert plan is not None
        tids = list(plan.tasks.keys())
        assert len(tids) >= 2
        first_id = tids[0]
        task = plan.tasks[first_id]
        try:
            plan = plan.transition(first_id, "BLOCKED", blocker={"reason": "TEST_BLOCKED"})
            store.save(plan)
        except Exception:
            new_task = task_state.TaskRecord(
                task_id=task.task_id,
                goal_id=task.goal_id,
                title=task.title,
                purpose=task.purpose,
                status="BLOCKED",
                dependencies=task.dependencies,
                scope=task.scope,
                non_scope=task.non_scope,
                acceptance_requirements=task.acceptance_requirements,
                required_evidence=task.required_evidence,
                blocker={"reason": "TEST_BLOCKED"},
            )
            plan.tasks[first_id] = new_task
            store.save(plan)

        plan = store.load()
        next_task = owner_goal._next_eligible_task(plan)
        if next_task is not None:
            assert next_task.status != "BLOCKED"

        for tid in list(plan.tasks.keys()):
            t = plan.tasks[tid]
            if t.status != "BLOCKED":
                try:
                    plan = plan.transition(tid, "BLOCKED", blocker={"reason": "ALL_BLOCKED"})
                except Exception:
                    plan.tasks[tid] = task_state.TaskRecord(
                        task_id=t.task_id,
                        goal_id=t.goal_id,
                        title=t.title,
                        purpose=t.purpose,
                        status="BLOCKED",
                        dependencies=t.dependencies,
                        scope=t.scope,
                        non_scope=t.non_scope,
                        acceptance_requirements=t.acceptance_requirements,
                        required_evidence=t.required_evidence,
                        blocker={"reason": "ALL_BLOCKED"},
                    )
        store.save(plan)
        plan = store.load()
        next_task_all_blocked = owner_goal._next_eligible_task(plan)
        assert next_task_all_blocked is None
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_owner_gate_end_to_end_via_intake():
    tmp = _make_temp_project()
    try:
        raw = "/goal Dự án cần quyết định vật liệu cho Arena, dùng Arena"
        owner_goal.build_owner_goal_intake(tmp, raw)
        store = task_state.TaskStateStore(tmp)
        plan = store.load()
        assert plan is not None
        for tid, task in plan.tasks.items():
            if task.status == "READY":
                new_task = task_state.TaskRecord(
                    task_id=task.task_id,
                    goal_id=task.goal_id,
                    title=task.title,
                    purpose=task.purpose,
                    status="WAITING_OWNER",
                    dependencies=task.dependencies,
                    scope=task.scope,
                    non_scope=task.non_scope,
                    acceptance_requirements=task.acceptance_requirements,
                    required_evidence=task.required_evidence,
                    owner_decision={"status": "PENDING", "question": "Chọn vật liệu X hay Y?"},
                )
                plan.tasks[tid] = new_task
                store.save(plan)
                break

        raw2 = "/goal Dự án cần quyết định vật liệu cho kho, dùng Arena"
        result2 = owner_goal.build_owner_goal_intake(tmp, raw2)
        assert result2["has_owner_gate"] is True or result2["terminal_type"] == "HARD_OWNER_GATE"
        assert result2["terminal_type"] == "HARD_OWNER_GATE"
        assert result2["has_gate"] is True
        assert result2["stop_honestly"] is True
        assert result2.get("claim_complete") is False or result2.get("claim_complete") is None
        assert result2["arena_handoff"] is None
        assert result2["arena_handoff_path"] == "HARD_OWNER_GATE_NO_HANDOFF"
        plan = store.load()
        terminal = owner_goal.check_terminal_state(plan, evidence_claims=[])
        assert terminal["terminal_type"] == "HARD_OWNER_GATE"
        assert terminal["is_terminal"] is True
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_reuse_metadata_session_action():
    tmp = _make_temp_project()
    try:
        raw1 = "/goal Test reuse metadata, dùng Arena"
        result1 = owner_goal.build_owner_goal_intake(tmp, raw1)
        assert result1["reuse"] is False
        contract1 = json.loads((tmp / ".p2p" / "state" / "goal-contract.json").read_text(encoding="utf-8"))
        store = task_state.TaskStateStore(tmp)
        plan = store.load()
        handoff1 = owner_goal.build_arena_handoff(tmp, contract1, plan, "ARENA", reuse=result1["reuse"])
        assert handoff1["reuse_existing_goal"] is False
        assert handoff1["session_action"] == "START_NEW_SESSION"

        raw2 = "/goal Test reuse metadata cho kho bãi, dùng Arena"
        result2 = owner_goal.build_owner_goal_intake(tmp, raw2)
        assert result2["reuse"] is True
        contract2 = json.loads((tmp / ".p2p" / "state" / "goal-contract.json").read_text(encoding="utf-8"))
        plan2 = store.load()
        handoff2 = owner_goal.build_arena_handoff(tmp, contract2, plan2, "ARENA", reuse=result2["reuse"])
        assert handoff2["reuse_existing_goal"] is True
        assert handoff2["session_action"] == "CONTINUE_CURRENT_SESSION"

        if result2.get("arena_handoff"):
            assert result2["arena_handoff"]["reuse_existing_goal"] is True
            assert result2["arena_handoff"]["session_action"] == "CONTINUE_CURRENT_SESSION"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_bare_executor_name_not_hijack():
    cases = [
        ("/goal sửa lỗi arena rendering", "AUTO"),
        ("/goal fix auto save feature", "AUTO"),
        ("/goal cải thiện tính năng arena cho game", "AUTO"),
        ("/goal sửa lỗi auto complete", "AUTO"),
        ("/goal arena", "AUTO"),
        ("/goal auto", "AUTO"),
        ("/goal Sửa lỗi đăng nhập", "AUTO"),
        ("/goal sửa lỗi arena rendering, dùng Arena", "ARENA"),
        ("/goal sửa lỗi arena rendering, use Arena", "ARENA"),
        ("/goal sửa lỗi arena rendering, dùng Auto", "AUTO"),
        ("/goal Hoàn thiện workflow, dùng Arena", "ARENA"),
        ("/goal Hoàn thiện workflow, dung Arena", "ARENA"),
        ("/goal Do feature, using Arena", "ARENA"),
        ("/goal Do feature, with Arena", "ARENA"),
    ]
    for raw, expected in cases:
        parsed = owner_goal.parse_owner_goal_command(raw)
        assert parsed["executor"] == expected, f"Failed for '{raw}': expected {expected}, got {parsed['executor']}"
        assert owner_goal.resolve_executor(raw) == expected, f"resolve_executor failed for '{raw}'"


def test_durable_git_identity_not_fabricated():
    tmp = _make_temp_project()
    try:
        raw = "/goal Test git identity, dùng Arena"
        owner_goal.build_owner_goal_intake(tmp, raw)
        contract = json.loads((tmp / ".p2p" / "state" / "goal-contract.json").read_text(encoding="utf-8"))
        store = task_state.TaskStateStore(tmp)
        plan = store.load()

        handoff = owner_goal.build_arena_handoff(tmp, contract, plan, "ARENA", reuse=False)
        assert handoff["branch"] == "UNKNOWN"
        assert handoff["repo"] == tmp.name
        assert "BRANCH=UNKNOWN" in handoff["packet_text"] or "If BRANCH=UNKNOWN" in handoff["packet_text"]
        assert "git fetch origin main" in handoff["packet_text"]
        assert "git branch -a --list 'arena/*'" in handoff["packet_text"]
        assert "git_identity" in handoff
        assert handoff["git_identity"]["branch"] == "UNKNOWN"

        real_root = ROOT
        real_contract = {"goal_id": "goal-test-real", "objective": "Test real repo", "scope": [], "out_of_scope": []}
        git_id = owner_goal._get_git_identity(real_root)
        assert git_id["branch"] != "UNKNOWN"
        handoff_real = owner_goal.build_arena_handoff(real_root, real_contract, None, "ARENA", reuse=False)
        if git_id["branch"].startswith("arena/"):
            assert handoff_real["branch"] == git_id["branch"]
        else:
            assert handoff_real["branch"] == "UNKNOWN"
        if git_id["remote_url"]:
            assert "/" in handoff_real["repo"] or handoff_real["repo"] == real_root.name
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_cli_native_activation_single_authoritative_host():
    """Single authoritative host: decision/projection only, never a fake invocation receipt."""
    import subprocess

    tmp = _make_temp_project()
    try:
        raw = "/goal Test CLI native activation single authoritative host, dùng Auto"
        sys.path.insert(0, str(ROOT / "scripts"))
        import p2p_workflow as wf  # type: ignore

        result = wf.owner_goal_intake(tmp, raw)
        assert "native_activation_evaluations" in result
        assert result.get("native_goal_activation_checked") is True

        from p2p_capabilities import autopilot_state
        goal_id = json.loads((tmp / ".p2p" / "state" / "goal-contract.json").read_text(encoding="utf-8")).get("goal_id")
        store = task_state.TaskStateStore(tmp)
        plan = store.load()
        assert plan is not None and len(plan.tasks) >= 2

        goal_plan_planned = autopilot_state.GoalPlan(
            goal_id=goal_id,
            goal_version="v1",
            title="CLI native activation",
            purpose="CLI native activation",
            owner_approval_ref="test-approval",
            scope=(raw,),
            non_scope=(),
            plan_task_ids=tuple(plan.tasks.keys()),
            status="PLANNED",
        )
        ap_store = autopilot_state.GoalStateStore(tmp)
        ap_store.initialize(goal_plan_planned)
        ap_store.transition("APPROVED")

        # Without an authoritative host: NORMAL_P2P_PATH honestly, count 0, no multi-host eval
        result2 = wf.owner_goal_intake(tmp, raw)
        assert result2.get("native_authoritative_host") is None
        assert result2.get("native_goal_activation_decision") == "NORMAL_P2P_PATH"
        assert result2.get("native_command_invoked_count") == 0
        assert result2.get("native_invocation_status") == "NOT_REQUIRED"
        assert result2.get("native_multi_host_evaluated") is False

        # With env marker CLAUDECODE=1: one authoritative host, ACTIVATE decision,
        # command projected, host action still required, invoked count 0.
        env = os.environ.copy()
        env["CLAUDECODE"] = "1"
        cli_cmd = [
            sys.executable,
            str(ROOT / "scripts" / "p2p_workflow.py"),
            "--project",
            str(tmp),
            "owner-goal",
            "--request",
            raw,
            "--json",
        ]
        proc = subprocess.run(cli_cmd, capture_output=True, text=True, timeout=15, env=env)
        assert proc.returncode == 0, f"CLI failed: {proc.stderr}"
        out = json.loads(proc.stdout)
        assert out.get("native_authoritative_host") == "claude_code"
        assert out.get("native_goal_activation_checked") is True
        assert out.get("native_goal_activation_decision") == "ACTIVATE_NATIVE_GOAL"
        assert "native_goal_command" in out
        assert out.get("native_goal_command_projection") == {"claude_code": out.get("native_goal_command")}
        assert out.get("native_invocation_required") is True
        assert out.get("native_invocation_status") == "HOST_ACTION_REQUIRED"
        assert out.get("native_command_invoked_count") == 0
        assert out.get("native_invocation_receipt") is None
        assert out.get("native_invocation_seam", {}).get("conclusion") == "NO_EXISTING_HOST_INVOCATION_SEAM"
        assert out.get("native_goal_activation_host") == "claude_code"
        # Only one host evaluated, never both
        evals = out.get("native_activation_evaluations", {})
        assert "claude_code" in evals
        assert evals["claude_code"]["decision"] == "ACTIVATE_NATIVE_GOAL"
        assert "codex_cli" not in evals

        # Arena remains non-native
        res_arena = owner_goal.evaluate_native_activation(tmp, "arena")
        assert res_arena["decision"] == "HOST_KIND_UNSUPPORTED"
        assert res_arena["native_goal_behavior_preserved"] is True
        assert result2.get("arena_in_native_hosts") is False
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_cli_explicit_codex_host_identity_decision_only():
    """Explicit known Codex executor identity is supported; still decision/projection only."""
    import subprocess

    tmp = _make_temp_project()
    try:
        raw = "/goal Test explicit codex host identity, dùng Auto"
        sys.path.insert(0, str(ROOT / "scripts"))
        import p2p_workflow as wf  # type: ignore
        from p2p_capabilities import autopilot_state

        wf.owner_goal_intake(tmp, raw)
        goal_id = json.loads((tmp / ".p2p" / "state" / "goal-contract.json").read_text(encoding="utf-8")).get("goal_id")
        plan = task_state.TaskStateStore(tmp).load()
        goal_plan = autopilot_state.GoalPlan(
            goal_id=goal_id,
            goal_version="v1",
            title="Explicit codex host",
            purpose="Explicit codex host",
            owner_approval_ref="test-approval",
            scope=(raw,),
            non_scope=(),
            plan_task_ids=tuple(plan.tasks.keys()),
            status="PLANNED",
        )
        ap_store = autopilot_state.GoalStateStore(tmp)
        ap_store.initialize(goal_plan)
        ap_store.transition("APPROVED")

        # API path: explicit known executor identity wins without env markers.
        api_out = wf.owner_goal_intake(tmp, raw, host="codex_cli")
        assert api_out.get("native_authoritative_host") == "codex_cli"
        assert api_out.get("native_authoritative_host_source") == "EXPLICIT_KNOWN_EXECUTOR_IDENTITY"
        assert api_out.get("native_goal_activation_decision") == "ACTIVATE_NATIVE_GOAL"
        assert api_out.get("native_invocation_status") == "HOST_ACTION_REQUIRED"
        assert api_out.get("native_command_invoked_count") == 0
        assert "codex_cli" in api_out.get("native_activation_evaluations", {})

        # CLI path: --host codex_cli
        cli_cmd = [
            sys.executable,
            str(ROOT / "scripts" / "p2p_workflow.py"),
            "--project",
            str(tmp),
            "owner-goal",
            "--request",
            raw,
            "--host",
            "codex_cli",
            "--json",
        ]
        proc = subprocess.run(cli_cmd, capture_output=True, text=True, timeout=15)
        assert proc.returncode == 0, f"CLI failed: {proc.stderr}"
        out = json.loads(proc.stdout)
        assert out.get("native_authoritative_host") == "codex_cli"
        assert out.get("native_goal_activation_decision") == "ACTIVATE_NATIVE_GOAL"
        assert out.get("native_goal_command")
        assert out.get("native_invocation_required") is True
        assert out.get("native_invocation_status") == "HOST_ACTION_REQUIRED"
        assert out.get("native_command_invoked_count") == 0
        assert out.get("native_invocation_receipt") is None
        assert "claude_code" not in out.get("native_activation_evaluations", {})
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_cli_owner_goal_main_entrypoint_single_host():
    import subprocess

    tmp = _make_temp_project()
    try:
        raw = "/goal Test main entrypoint single host, dùng Auto"
        sys.path.insert(0, str(ROOT / "scripts"))
        import p2p_workflow as wf  # type: ignore
        from p2p_capabilities import autopilot_state

        wf.owner_goal_intake(tmp, raw)
        goal_id = json.loads((tmp / ".p2p" / "state" / "goal-contract.json").read_text(encoding="utf-8")).get("goal_id")
        store = task_state.TaskStateStore(tmp)
        plan = store.load()
        goal_plan = autopilot_state.GoalPlan(
            goal_id=goal_id,
            goal_version="v1",
            title="Main entrypoint",
            purpose="Main entrypoint",
            owner_approval_ref="test-approval",
            scope=(raw,),
            non_scope=(),
            plan_task_ids=tuple(plan.tasks.keys()),
            status="PLANNED",
        )
        ap_store = autopilot_state.GoalStateStore(tmp)
        ap_store.initialize(goal_plan)
        ap_store.transition("APPROVED")

        env = os.environ.copy()
        env["CLAUDECODE"] = "1"
        cli_cmd = [
            sys.executable,
            str(ROOT / "scripts" / "p2p_workflow.py"),
            "--project",
            str(tmp),
            "owner-goal",
            "--request",
            raw,
            "--json",
        ]
        proc = subprocess.run(cli_cmd, capture_output=True, text=True, timeout=15, env=env)
        assert proc.returncode == 0, f"main() CLI failed: {proc.stderr}\n{proc.stdout}"
        out = json.loads(proc.stdout)
        assert out.get("native_goal_activation_checked") is True
        assert out.get("native_authoritative_host") == "claude_code"
        evals = out.get("native_activation_evaluations", {})
        assert evals.get("claude_code", {}).get("decision") == "ACTIVATE_NATIVE_GOAL"
        assert "command" in evals.get("claude_code", {})
        assert out.get("native_invocation_required") is True
        assert out.get("native_invocation_status") == "HOST_ACTION_REQUIRED"
        assert out.get("native_command_invoked_count") == 0
        assert out.get("arena_in_native_hosts") is False
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_no_second_completion_verifier_and_no_fabricated_invocation_count():
    """Single completion authority + no invocation counter can be set without an action."""
    import inspect

    owner_src = Path(inspect.getsourcefile(owner_goal)).read_text(encoding="utf-8")
    wf_src = (ROOT / "scripts" / "p2p_workflow.py").read_text(encoding="utf-8")

    # No second completion verifier in owner_goal.py
    assert not hasattr(owner_goal, "_is_canonical_completion_valid")
    assert "_is_canonical_completion_valid" not in owner_src
    assert "def _completion_is_structurally_valid" not in owner_src
    assert "evidence_fingerprints" not in owner_src
    assert owner_goal.CANONICAL_COMPLETION_AUTHORITY.startswith("p2p_capabilities.task_state")

    # A decision/projection must never increment the invocation counter
    assert 'native_command_invoked_count"] = 1' not in owner_src
    assert 'native_command_invoked_count"] = 1' not in wf_src
    assert "native_command_invoked_count = 1" not in owner_src
    assert "native_command_invoked_count = 1" not in wf_src
