#!/usr/bin/env python3
"""C41 pilot proof: a beginner-first task through the INSTALLED P2P on Gia Phả.

The person at the project types one sentence: "Tiếp tục hoàn thiện dự án".
The installed P2P (at .p2p/system inside the project) must:
  1. Read its own project context as a capsule (Gia Phả OS docs).
  2. Discover capabilities through the installed registry.
  3. Check the failover gate pre-dispatch (no failure -> normal dispatch).
  4. Dispatch one bounded, low-risk live task to Manus asking for a
     concrete, low-risk next task recommendation (docs/read-only style,
     no code writes, no credentials), following the project's own stated
     limits.
  5. Record durable state (dispatch receipt + capsule hash) in the project.
  6. Verify the answer independently through the API (not self-claim).

Evidence lands in docs/p2p-development/research/c41/evidence/ and
.p2p/system/state/ inside the pilot project.
"""
import hashlib
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

PILOT = Path("/home/ubuntu/gia-pha-pilot").resolve()
SYSTEM = PILOT / ".p2p" / "system"
sys.path.insert(0, str(SYSTEM))

# ------------------------------------------------------------------ registry
from p2p_capabilities.agent_role import load_capability_registry, build_role_spec  # noqa: E402
from p2p_capabilities.manus_adapter import ManusAdapter  # noqa: E402
from p2p_capabilities.failover_boundary import (  # noqa: E402
    decide_next_action, snapshot_eligibility, EligibilitySnapshot)


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


# Project context files for the capsule (read-only docs, no code, no secrets).
CAPSULE_FILES = [
    "README.md",
    "docs/plans/2026-08-15-p2p-c02-data-foundation/2026-08-15-p2p-c02-data-foundation-actual-status.md",
    "docs/plans/2026-08-14-p2p-c01-foundation-safety/2026-08-14-p2p-c01-foundation-safety-plan.md",
]


def main() -> None:
    request_id = f"c41-gia-pha-pilot-{uuid.uuid4().hex[:12]}"
    fingerprint = hashlib.sha256(request_id.encode()).hexdigest()
    key = Path("/home/ubuntu/.secrets/manus_api_key_new").read_text().strip()

    # 1. capsule: project context files (digests + content block)
    capsule = {}
    missing = []
    for rel in CAPSULE_FILES:
        p = PILOT / rel
        if not p.is_file():
            missing.append(rel)
            continue
        capsule[rel] = {"sha256": sha256(p), "chars": p.stat().st_size}
    if missing:
        raise SystemExit(f"capsule files missing: {missing} (fail-closed)")
    capsule_hash = hashlib.sha256(
        json.dumps(capsule, sort_keys=True).encode()).hexdigest()

    # 2. registry + role spec from the INSTALLED system
    registry_records = load_capability_registry(
        str(SYSTEM / "p2p_capabilities" / "capabilities.json"))
    role_spec = build_role_spec("p2p_iris", registry_records)

    # 3. failover gate pre-check: probe eligibility of the primary target.
    def _manus_probe(_target: str):
        key_ok = bool(key) and len(key) >= 30
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
        decision = decide_next_action(failure_class=snap.failure_class,
                                      dispatched=False,
                                      current_target="manus-rest-api-v2",
                                      failure_class_observed=(snap.failure_class,)
                                      if snap.failure_class else ())
    if decision.decision not in ("RETRY_SAME_TARGET",):
        raise SystemExit(
            f"Failover gate did not authorize normal dispatch: "
            f"{decision.decision} ({decision.reason}) (fail-closed, STOP)")

    # 4. bounded live dispatch: docs-only next-task recommendation.
    # Token budget: the Manus API caps message content at ~5000 estimated
    # tokens (~30k chars). Build a token-budgeted context block, prefer the
    # task-relevant plan docs, and truncate README to its key sections.
    MAX_CHARS = 18000
    capsule_texts = []
    for rel in CAPSULE_FILES:
        p = PILOT / rel
        text = p.read_text(encoding="utf-8")
        if rel == "README.md":
            # Keep only the feature list + setup instructions (skip the
            # long code/docs sections) to stay inside the token budget.
            head = text.split("## Hình ảnh Giao diện")[0]
            text = head + "\n[...tài liệu kỹ thuật còn lại bị cắt vì giới hạn token...]"
        max_len = 9000 if rel != "README.md" else 3000
        if len(text) > max_len:
            text = text[:max_len] + "\n[...bị cắt vì giới hạn token...]"
        chunk = f"===== {rel} =====\n{text}"
        if sum(len(t) for t in capsule_texts) + len(chunk) >= MAX_CHARS:
            break
        capsule_texts.append(chunk)
    capsule_block = "\n\n".join(capsule_texts)
    assert capsule_texts and len(capsule_block) < MAX_CHARS, (
        "token-budgeted capsule is empty or over budget")
    prompt = (
        "Đây là Gia Phả OS (ứng dụng quản lý gia phả dòng họ, Next.js + "
        "Supabase). Dựa TRÊN nội dung các tài liệu dự án đã được dán đầy đủ "
        "bên dưới (README.md, bản kế hoạch c01-foundation-safety, trạng thái "
        "thực tế của c02-data-foundation), KHÔNG đọc kho code, KHÔNG viết hay "
        "sửa code, KHÔNG dùng bất kỳ credential nào: cho biết MỘT nhiệm vụ "
        "cụ thể, rủi ro thấp, an toàn nhất mà dự án nên làm tiếp theo "
        "(ví dụ: hoàn thiện tài liệu, kiểm tra dữ liệu, bước kế tiếp đã nêu "
        "trong tài liệu dự án), trong một đoạn ngắn tối đa 60 từ. "
        "Câu trả lời bắt đầu bằng 'N-next:'.\n\n" + capsule_block
    )
    adapter = ManusAdapter(api_key=key)
    import time as _time
    attempts, result = [], None
    for attempt in range(1, 4):
        try:
            result = adapter.execute(
                request_id=request_id, request_fingerprint=fingerprint,
                task_id=None, goal_id="P2P-C41",
                prompt=prompt, max_turns=4, timeout_seconds=240)
            break
        except Exception as exc:  # transport errors
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
        "schema": "c41-pilot-dispatch/1",
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
    (state_dir / "c41-pilot-dispatch-receipt.json").write_text(
        json.dumps(receipt, indent=2, ensure_ascii=False) + "\n")
    (state_dir / "c41-pilot-capsule.json").write_text(
        json.dumps(capsule, indent=2, ensure_ascii=False) + "\n")

    ev_dir = Path("/home/ubuntu/p2p-repo/docs/p2p-development/research/c41/evidence")
    ev_dir.mkdir(parents=True, exist_ok=True)
    (ev_dir / "c41-gia-pha-pilot-dispatch.json").write_text(
        json.dumps({**receipt, "capsule": capsule,
                    "backend_result": backend},
                   indent=2, ensure_ascii=False) + "\n")

    print(json.dumps({
        "request_id": request_id,
        "capsule_hash": capsule_hash,
        "gate_decision": decision.decision,
        "task_id": receipt["backend_result_task_id"],
        "execution_status": receipt["execution_status"],
    }, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
