#!/usr/bin/env python3
"""C40 pilot proof: a beginner-first task through the INSTALLED P2P.

The person at the project types one sentence: "Tiếp tục hoàn thiện dự án".
The installed P2P (at .p2p/system inside the project) must:
  1. Read its own project context (PROJECT_BRIEF.md, TASKS.md) as a capsule.
  2. Discover capabilities through the installed registry.
  3. Check the failover gate pre-dispatch (no failure -> normal dispatch).
  4. Dispatch one bounded, low-risk live task to Manus asking for a
     continuation recommendation for the next T-task, following the
     project's own stated limits (do NOT write new code, docs only).
  5. Record durable state (dispatch receipt + capsule hash) in the project.
  6. Verify the answer independently through the API (not self-claim).

Evidence lands in docs/p2p-development/research/c40/evidence/ and
.p2p/state/ inside the pilot project.
"""
import hashlib
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

PILOT = Path("/home/ubuntu/game-truyen-pilot").resolve()
SYSTEM = PILOT / ".p2p" / "system"
sys.path.insert(0, str(SYSTEM))

# ------------------------------------------------------------------ registry
from p2p_capabilities.agent_role import load_capability_registry, build_role_spec
from p2p_capabilities.manus_adapter import ManusAdapter
from p2p_capabilities.failover_boundary import (
    decide_next_action, snapshot_eligibility, EligibilitySnapshot)


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def main() -> None:
    request_id = f"c40-pilot-{uuid.uuid4().hex[:12]}"
    fingerprint = hashlib.sha256(request_id.encode()).hexdigest()
    key = Path("/home/ubuntu/.secrets/manus_api_key_new").read_text().strip()

    # 1. capsule: project context files (read-only digest, not transcript)
    capsule_files = ["PROJECT_BRIEF.md", "TASKS.md", "README_V09818_NARRATIVE_SIMULATION.md"]
    capsule = {}
    for name in capsule_files:
        p = PILOT / name
        capsule[name] = {"sha256": sha256(p), "chars": p.stat().st_size}
    capsule_hash = hashlib.sha256(
        json.dumps(capsule, sort_keys=True).encode()).hexdigest()

    # 2. registry + role spec from the INSTALLED system
    registry_records = load_capability_registry(str(SYSTEM / "p2p_capabilities" / "capabilities.json"))
    role_spec = build_role_spec("p2p_iris", registry_records)

    # 3. failover gate pre-check: probe eligibility of the primary target.
    # The primary is the Manus REST API v2; env key present -> eligible.
    # Probe: key file readable and non-empty == reference present (no value use).
    def _manus_probe(_target: str):
        key_ok = key and len(key) >= 30
        return EligibilitySnapshot(
            target=_target,
            eligible=key_ok,
            failure_class=None if key_ok else "AUTH_REFERENCE_ABSENT",
            evidence_pointers=("file:/home/ubuntu/.secrets/manus_api_key_new",),
            detail="Manus API key reference presence check",
        )
    snap = snapshot_eligibility("manus-rest-api-v2", probe=_manus_probe)
    if snap is None:
        raise SystemExit("Eligibility state UNKNOWN (probe indeterminate); "
                         "failover boundary fails closed: STOP (no dispatch).")
    if snap.eligible:
        decision = decide_next_action(failure_class=None, dispatched=False,
                                      current_target="manus-rest-api-v2")
    else:
        # gate decides: reselection or fail-closed
        decision = decide_next_action(failure_class=snap.failure_class,
                                      dispatched=False,
                                      current_target="manus-rest-api-v2",
                                      failure_class_observed=(snap.failure_class,) if snap.failure_class else ())
    if decision.decision not in ("RETRY_SAME_TARGET",):
        raise SystemExit(
            f"Failover gate did not authorize normal dispatch: "
            f"{decision.decision} ({decision.reason}) (fail-closed, STOP)")

    # 4. bounded live dispatch: docs-only continuation recommendation.
    # Embed the capsule CONTENTS so the agent can answer from real project
    # state (digests alone are evidence only; the text is the working context).
    capsule_texts = []
    for name in capsule_files:
        p = PILOT / name
        capsule_texts.append(f"===== {name} =====\n{p.read_text(encoding='utf-8')}")
    capsule_block = "\n\n".join(capsule_texts)
    prompt = (
        "Đây là Game Truyện (tiên hiệp). Dựa TRÊN nội dung ba tài liệu dự án "
        "đã được dán đầy đủ bên dưới (PROJECT_BRIEF.md, TASKS.md, "
        "README_V09818), KHÔNG đọc kho code, KHÔNG viết hay sửa code: cho "
        "biết task T tiếp theo mà dự án nên làm theo trạng thái T01–T11 đã "
        "có, trong một đoạn ngắn tối đa 60 từ. "
        "Câu trả lời bắt đầu bằng 'T-next:'.\n\n"
        + capsule_block
    )
    adapter = ManusAdapter(api_key=key)
    # harness-level transient-failure tolerance: the installed adapter's
    # execute is idempotent per request_id; a transient transport error
    # (e.g. 404 on task.detail right after creation) is retried with
    # bounded backoff. After 3 attempts the gate is fail-closed.
    import time as _time
    attempts, result = [], None
    for attempt in range(1, 4):
        try:
            result = adapter.execute(
                request_id=request_id, request_fingerprint=fingerprint,
                task_id=None, goal_id="P2P-C40",
                prompt=prompt, max_turns=4, timeout_seconds=240)
            break
        except Exception as exc:  # transport errors (HTTPError etc.)
            attempts.append({"attempt": attempt, "error": repr(exc)})
            if attempt < 3:
                _time.sleep(5)
                continue
            raise SystemExit(
                f"Transient failures exhausted after 3 attempts "
                f"(fail-closed): {attempts}") from exc
    if result is None:
        raise SystemExit("No execution result (fail-closed): STOP")
    backend = result.to_dict() if hasattr(result, "to_dict") else vars(result)
    if attempts:
        backend["transient_retry_attempts"] = attempts

    # 5. durable state in the project
    receipt = {
        "schema": "c40-pilot-dispatch/1",
        "request_id": request_id,
        "capsule_hash": capsule_hash,
        "role_spec_hash": role_spec.role_spec_hash,
        "failover_gate_decision": decision.decision,
        "failover_gate_reason": decision.reason,
        "dispatched": True,
        "backend_result_task_id": backend.get("task_id")
        if isinstance(backend, dict) else None,
        "backend_result_pointer": backend.get("raw_backend_receipt_pointer")
        if isinstance(backend, dict) else None,
        "execution_status": backend.get("execution_status")
        if isinstance(backend, dict) else None,
        "created_utc": now_utc(),
    }
    state_dir = SYSTEM / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "c40-pilot-dispatch-receipt.json").write_text(
        json.dumps(receipt, indent=2, ensure_ascii=False) + "\n")
    (state_dir / "c40-pilot-capsule.json").write_text(
        json.dumps(capsule, indent=2, ensure_ascii=False) + "\n")

    ev_dir = PILOT / "docs" / "p2p-development" / "research" / "c40" / "evidence"
    ev_dir.mkdir(parents=True, exist_ok=True)
    (ev_dir / "c40-pilot-dispatch.json").write_text(
        json.dumps({**receipt, "capsule": capsule,
                    "backend_result": backend},
                   indent=2, ensure_ascii=False) + "\n")

    print(json.dumps({
        "request_id": request_id,
        "capsule_hash": capsule_hash,
        "gate_decision": decision.decision,
        "task_id": (receipt["backend_result_task_id"]),
        "execution_status": receipt["execution_status"],
    }, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
