"""Tests for Owner /goal one-command intake — 7 UX acceptance cases.

Covers:
1. Arena parse — /goal ... dùng Arena
2. Auto routing — /goal without executor
3. Reuse compatible active Goal
4. Real Owner Gate honest stop
5. Single-task normal path
6. Arena DONE without evidence not promoted
7. Host cannot invoke Arena -> one explicit beginner handoff packet

Plus invariants: native_goal_behavior preserved, RULE20 preserved.
"""

from __future__ import annotations

import json
import sys
import tempfile
import shutil
from pathlib import Path

try:
    import pytest  # type: ignore
except ModuleNotFoundError:
    pytest = None  # fallback for environments without pytest

ROOT = Path(__file__).resolve().parents[1]
SYSTEM = ROOT / ".p2p" / "system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

from p2p_capabilities import owner_goal  # type: ignore
from p2p_capabilities import task_state  # type: ignore
from p2p_capabilities import native_goal_bridge  # type: ignore


def test_case1_arena_parse():
    """Case 1: /goal Hoàn thiện workflow hợp đồng logistics, dùng Arena"""
    raw = "/goal Hoàn thiện workflow hợp đồng logistics, dùng Arena"
    parsed = owner_goal.parse_owner_goal_command(raw)
    assert parsed["objective"] == "Hoàn thiện workflow hợp đồng logistics"
    assert parsed["executor"] == "ARENA"
    assert "Arena" not in parsed["objective"]  # executor hint stripped
    # Check resolver
    assert owner_goal.resolve_executor(raw) == "ARENA"


def test_case2_auto_routing_when_unspecified():
    """Case 2: /goal without executor -> Auto routing"""
    raw = "/goal Sửa lỗi đăng nhập"
    parsed = owner_goal.parse_owner_goal_command(raw)
    assert parsed["objective"] == "Sửa lỗi đăng nhập"
    assert parsed["executor"] == "AUTO"
    assert owner_goal.resolve_executor(raw) == "AUTO"

    # Also test bare objective without /goal prefix via CLI path
    raw2 = "Sửa lỗi đăng nhập"
    # resolve should default to AUTO
    assert owner_goal.resolve_executor(raw2) == "AUTO"


def _make_temp_project() -> Path:
    """Create a minimal project with .p2p/system and scripts copied from repo."""
    tmp = Path(tempfile.mkdtemp(prefix="p2p-owner-goal-test-"))
    # Copy .p2p/system
    shutil.copytree(SYSTEM, tmp / ".p2p" / "system", ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "tests"))
    # Copy scripts/p2p_workflow.py and p2p_eval.py (needed by bootstrap)
    scripts_src = ROOT / "scripts"
    scripts_dst = tmp / "scripts"
    scripts_dst.mkdir(parents=True, exist_ok=True)
    for name in ("p2p_workflow.py", "p2p_eval.py", "p2p_governance.py", "p2p_development_control.py"):
        src = scripts_src / name
        if src.is_file():
            shutil.copy2(src, scripts_dst / name)
    # Ensure owner_goal.py is in the copied system (it should be, but copytree may have excluded tests only)
    # Explicitly copy owner_goal if missing
    owner_src = ROOT / ".p2p" / "system" / "p2p_capabilities" / "owner_goal.py"
    owner_dst = tmp / ".p2p" / "system" / "p2p_capabilities" / "owner_goal.py"
    if owner_src.is_file() and not owner_dst.is_file():
        shutil.copy2(owner_src, owner_dst)
    # Create minimal governance template for workflow
    gov = tmp / "governance"
    gov.mkdir(parents=True, exist_ok=True)
    (gov / "fact-ledger.json").write_text("{}", encoding="utf-8")
    (gov / "live-specs.json").write_text("{}", encoding="utf-8")
    (gov / "project-policy.template.json").write_text(
        json.dumps({"protected_actions": [], "final_release_requires_full_quorum": False}), encoding="utf-8"
    )
    # Create minimal manifest/package.json for version checks if needed
    manifest_dir = tmp / "manifest"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    (manifest_dir / "package.json").write_text(json.dumps({"version": "0.0.0-test"}), encoding="utf-8")
    (tmp / "VERSION").write_text("0.0.0-test", encoding="utf-8")
    return tmp


def test_case3_reuse_compatible_active_goal():
    """Case 3: If project already has compatible active Goal/Task Plan, reuse it."""
    tmp = _make_temp_project()
    try:
        # First intake creates Goal
        raw1 = "/goal Hoàn thiện workflow hợp đồng logistics, dùng Auto"
        result1 = owner_goal.build_owner_goal_intake(tmp, raw1)
        assert result1["goal_id"]
        assert result1["reuse"] is False
        goal_id_1 = result1["goal_id"]

        # Second intake with compatible objective should reuse
        raw2 = "/goal Hoàn thiện workflow hợp đồng logistics cho kho bãi"
        result2 = owner_goal.build_owner_goal_intake(tmp, raw2)
        # Should reuse existing active goal
        assert result2["reuse"] is True
        assert result2["goal_id"] == goal_id_1

        # Check no second state DB created
        assert (tmp / ".p2p" / "state" / "task-state.json").is_file()
        # Only one task-state file
        state_files = list((tmp / ".p2p" / "state").glob("task-state*"))
        assert len(state_files) == 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_case4_real_owner_gate_honest_stop():
    """Case 4: Real Owner Gate (WAITING_OWNER) stops honestly, does not claim complete."""
    tmp = _make_temp_project()
    try:
        raw = "/goal Dự án cần quyết định vật liệu, dùng Auto"
        result = owner_goal.build_owner_goal_intake(tmp, raw)
        store = task_state.TaskStateStore(tmp)
        plan = store.load()
        assert plan is not None

        # Simulate a WAITING_OWNER task
        # Find a READY task and set it to WAITING_OWNER with owner decision pending
        for tid, task in plan.tasks.items():
            if task.status == "READY":
                # Use mark_waiting_owner if available, else direct mutation via to_dict then from_dict?
                # TaskRecord has with_status? Check API
                try:
                    # Try to use store to update? We'll use plan mutation via task_state module
                    # Create new task with WAITING_OWNER
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
                    # Fallback: direct dict manipulation
                    plan.tasks[tid].status = "WAITING_OWNER"
                    store.save(plan)
                break

        plan = store.load()
        gate = owner_goal.detect_owner_gate(plan)
        assert gate["has_gate"] is True
        assert gate["gate_type"] == "HARD_OWNER_GATE"
        assert gate["stop_honestly"] is True
        assert gate["claim_complete"] is False

        # Terminal check should return HARD_OWNER_GATE, not MISSION_COMPLETE
        terminal = owner_goal.check_terminal_state(plan, evidence_claims=[])
        assert terminal["terminal_type"] == "HARD_OWNER_GATE"
        assert terminal["is_terminal"] is True
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_case5_single_task_normal_path():
    """Case 5: Single-task goal: after inspecting existing project state, init missing state, create/reuse plan, route."""
    tmp = _make_temp_project()
    try:
        raw = "/goal Sửa lỗi đăng nhập cho web app, dùng Auto"
        result = owner_goal.build_owner_goal_intake(tmp, raw)
        assert result["goal_id"]
        assert result["executor"] == "AUTO"
        # Check state initialized
        assert (tmp / ".p2p" / "state" / "goal-contract.json").is_file()
        assert (tmp / ".p2p" / "state" / "task-state.json").is_file()
        # Plan exists
        store = task_state.TaskStateStore(tmp)
        plan = store.load()
        assert plan is not None
        assert len(plan.tasks) >= 1
        # Next eligible task should be selectable
        next_task = owner_goal._next_eligible_task(plan)
        assert next_task is not None
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_case6_verifier_missing_not_promoted():
    """Case 6: If verifier and required evidence do not yet exist, system must not promote Arena self-reported DONE/PASS to accepted DONE."""
    import hashlib
    from datetime import datetime, timezone

    tmp = _make_temp_project()
    try:
        raw = "/goal Hoàn thiện tính năng thanh toán, dùng Arena"
        result = owner_goal.build_owner_goal_intake(tmp, raw)
        store = task_state.TaskStateStore(tmp)
        plan = store.load()
        assert plan is not None

        # Properly complete all tasks with valid evidence so task_state validation passes
        # Then test check_terminal_state with empty evidence_claims -> must not promote
        for tid in plan.topological_order():
            task = store.load().tasks[tid]
            if task.status == "DONE":
                continue
            # Build evidence matching required_evidence
            # task_state expects number of claims >= len(required), each claim verified
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
                c = task_state.EvidenceClaim(
                    claim=f"{task.title} done via {ref}",
                    required_evidence=(ref,),
                    actual_evidence=(actual_item,),
                    status="VERIFIED",
                )
                claims.append(c)
            candidate_state = {"task_id": tid, "status": "done", "evidence": required}
            # Transition to ACTIVE if needed, then complete
            current = store.load()
            cur_task = current.tasks[tid]
            if cur_task.status == "PLANNED":
                # Ensure dependencies done (topological order already)
                # PLANNED -> READY -> ACTIVE
                if current.dependencies_are_done(tid):
                    current = store.transition(tid, "READY")
            current = store.load()
            cur_task = current.tasks[tid]
            if cur_task.status == "READY":
                current = store.transition(tid, "ACTIVE")
            # Now complete
            store.complete(tid, claims, candidate_state)

        plan = store.load()
        assert all(t.status == "DONE" for t in plan.tasks.values())

        # Arena claims DONE, but evidence_claims empty for terminal check
        terminal = owner_goal.check_terminal_state(plan, evidence_claims=[])
        # Must NOT be MISSION_COMPLETE, must be evidence missing
        assert terminal["terminal_type"] in {"EVIDENCE_MISSING", "EVIDENCE_INCOMPLETE"}
        assert terminal["is_terminal"] is False
        assert terminal["arena_claim_is_evidence"] is False
        assert terminal.get("must_not_promote") is True

        # Even with fake Arena DONE claims, without independent evidence, not promoted
        fake_evidence = [{"task_id": "fake", "status": "PASS", "claim": "Arena says DONE"}]
        terminal2 = owner_goal.check_terminal_state(plan, evidence_claims=fake_evidence)
        assert terminal2["arena_claim_is_evidence"] is False
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_case7_beginner_handoff_when_direct_invoke_impossible():
    """Case 7: If current host cannot directly invoke Arena, return exactly one explicit beginner handoff packet."""
    tmp = _make_temp_project()
    try:
        raw = "/goal Hoàn thiện workflow hợp đồng logistics, dùng Arena"
        result = owner_goal.build_owner_goal_intake(tmp, raw)
        contract = json.loads((tmp / ".p2p" / "state" / "goal-contract.json").read_text(encoding="utf-8"))
        store = task_state.TaskStateStore(tmp)
        plan = store.load()
        assert plan is not None

        # Build beginner handoff
        handoff = owner_goal.build_beginner_handoff(tmp, contract, plan, "ARENA")
        # Must be exactly one packet
        assert handoff["one_packet_only"] is True
        assert handoff["destination"] == "ARENA AI — CHAT MỚI — WRITER"
        assert "chat_title" in handoff
        assert "success_signal" in handoff
        assert "return_packet_spec" in handoff
        assert "task_packet" in handoff
        assert "packet_text" in handoff
        # Task packet inside must have DESTINATION=ARENA AI, EXECUTION_MODE, etc.
        inner = handoff["task_packet"]
        assert inner["destination"] == "ARENA AI"
        assert inner["execution_mode"] == "AUTONOMOUS_UNTIL_TERMINAL"
        assert inner["no_second_orchestrator"] is True
        assert inner["native_goal_behavior_preserved"] is True
        assert inner["rule20_preserved"] is True
        assert inner["agent_claim_is_not_evidence"] is True
        # Packet text must include required fields
        text = handoff["packet_text"]
        assert "DESTINATION=ARENA AI" in text
        assert "EXECUTION_MODE=AUTONOMOUS_UNTIL_TERMINAL" in text
        assert "SUPREME_LAW" in text or "SUPREME_LAW_CAPSULE" in text or "P2P_SUPREME_LAW_PREFLIGHT" in text
        assert "RETURN_PACKET" in text
        assert "SUCCESS_SIGNAL" in text
        # Check owner_is_not_message_bus
        assert handoff["owner_is_not_message_bus"] is True
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_native_goal_behavior_preserved():
    """Arena not falsely added as Claude/Codex native /goal host."""
    hosts = getattr(native_goal_bridge, "HOST_KINDS", ())
    lower_hosts = [str(h).lower() for h in hosts]
    assert "arena" not in lower_hosts
    # Ensure only claude_code and codex_cli (or similar) are present
    assert any("claude" in h for h in lower_hosts) or any("codex" in h for h in lower_hosts)


def test_rule20_preserved_no_second_router():
    """RULE 20 preserved: no second router/daemon/state DB/task registry/acceptance authority."""
    # Check that owner_goal.py does not import or create second router/state
    # SYSTEM is .p2p/system, owner_goal is in p2p_capabilities subdir
    candidate = SYSTEM / "p2p_capabilities" / "owner_goal.py"
    if not candidate.is_file():
        candidate = SYSTEM / "owner_goal.py"
    content = candidate.read_text(encoding="utf-8")
    # Must not contain forbidden patterns
    forbidden = ["class Router", "class TaskRegistry", "class StateDB", "daemon", "second_router", "new_state_db"]
    for pattern in forbidden:
        # Allow comments mentioning them as forbidden, but not actual creation
        # Check for actual class definition or instantiation that would be second
        if f"class {pattern}" in content:
            assert False, f"Forbidden second system found: {pattern}"
    # Must reuse existing workflow
    assert "p2p_workflow" in content or "task_state" in content or "beginner_gateway" in content
    assert "no_second_orchestrator" in content.lower() or "no second orchestrator" in content.lower()


def test_arena_handoff_builder_fields():
    """Verify Arena handoff packet contains required fields per spec."""
    tmp = _make_temp_project()
    try:
        raw = "/goal Test Arena handoff, dùng Arena"
        result = owner_goal.build_owner_goal_intake(tmp, raw)
        contract = json.loads((tmp / ".p2p" / "state" / "goal-contract.json").read_text(encoding="utf-8"))
        store = task_state.TaskStateStore(tmp)
        plan = store.load()
        handoff = owner_goal.build_arena_handoff(tmp, contract, plan, "ARENA")
        # Required fields
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
        # Packet text checks
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
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_parser_supports_vietnamese_and_english():
    """Parser supports Vietnamese and English executor hints."""
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
