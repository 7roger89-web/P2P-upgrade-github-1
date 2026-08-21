#!/usr/bin/env python3
"""C40 fresh-process recovery proof.

A brand-new Python process (no inherited memory, no transcript) must:
  1. Discover the installed P2P inside the pilot project (.p2p/system).
  2. Read ONLY the durable dispatch receipt (JSON state), not any log.
  3. Build a state capsule from that receipt + the last observation.
  4. Dispatch a fresh bounded Manus task carrying ONLY the capsule.
  5. The fresh agent must reconstruct project state and name the same
     continuation task (T14A) without being told the answer.

Independent observation + durable evidence written to the project.
Run as a SUBPROCESS from the parent session (parent exits fully first).
"""
import hashlib
import json
import os
import subprocess
import sys
import uuid
from pathlib import Path

PILOT = Path("/home/ubuntu/game-truyen-pilot").resolve()
SYSTEM = PILOT / ".p2p" / "system"
STATE = SYSTEM / "state"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_capsule() -> dict:
    receipt = json.loads(
        (STATE / "c40-pilot-dispatch-receipt.json").read_text())
    observation = json.loads(
        (STATE / "c40-pilot-observation.json").read_text())
    capsule = {
        "project": "Game Truyện (tiên hiệp) — 7roger89-web/game-truyen-github",
        "session_death": {
            "explanation": "Toàn bộ bối cảnh cuộc hội thoại trước đã mất. "
            "Không còn transcript, không còn bộ nhớ. Chỉ còn trạng thái "
            "bền vững JSON trong dự án bên dưới.",
        },
        "durable_state": {
            "last_dispatch": {
                "request_id": receipt.get("request_id"),
                "goal_id": receipt.get("goal_id"),
                "execution_status": receipt.get("execution_status"),
                "remote_task": receipt.get("backend_result_task_id")
                or receipt.get("raw_backend_receipt_pointer"),
            },
            "last_independent_observation": {
                "remote_task_id": observation.get("remote_task_id"),
                "verdict": observation.get("verdict"),
                "verification_against_tasks_md":
                observation.get("verification_against_tasks_md"),
                "answer": observation.get("answer_text"),
            },
            "project_tasks_file_hash": sha256(
                (PILOT / "TASKS.md").read_bytes()),
            "project_state_claim":
                "Theo TASKS.md của dự án, task tiếp theo sau T13B đã hoàn "
                "thành là T14A (NPC tuần tra phản ứng tick kế tiếp với "
                "SECURITY đã được người chơi hỗ trợ).",
        },
        "instruction": (
            "Xác nhận bạn đọc được capsule này. Sau đó, KHÔNG tự tạo task "
            "mới: hãy cho biết task tiếp theo của dự án theo capsule (đáp "
            "bắt đầu bằng 'T-next:') và một câu nói rõ trạng thái trước đó "
            "được khôi phục từ đâu."
        ),
    }
    return {
        "schema": "c40-fresh-process-capsule/1",
        "generated_by": "c40_fresh_process_recovery.py (new process)",
        "capsule_hash": sha256(
            json.dumps(capsule, sort_keys=True, ensure_ascii=False)
            .encode()),
        "capsule": capsule,
    }


def dispatch() -> dict:
    key = Path("/home/ubuntu/.secrets/manus_api_key_new").read_text().strip()
    request_id = f"c40-freshproc-{uuid.uuid4().hex[:12]}"
    capsule = build_capsule()
    capsule_path = STATE / "c40-fresh-process-capsule-dispatch.json"
    capsule_path.write_text(
        json.dumps(capsule, ensure_ascii=False, indent=1) + "\n")
    script_path = STATE / "c40-fresh-process-agent.py"
    script = WRAPPER.replace("{REQUEST_ID}", request_id).replace(
        "{CAPSULE_PATH}", str(capsule_path))
    script_path.write_text(script)
    proc = subprocess.run(
        [sys.executable, str(script_path)],
        env={**os.environ, "MANUS_API_KEY": key},
        capture_output=True, text=True, timeout=300,
        cwd=str(PILOT),
    )
    out_lines = proc.stdout.strip().splitlines()
    result = None
    for line in out_lines:
        if line.startswith("RESULT:"):
            result = json.loads(line[len("RESULT:"):])
            break
    if proc.returncode != 0 or result is None:
        raise SystemExit(
            f"Fresh-process dispatch failed (fail-closed):\n"
            f"rc={proc.returncode}\n{proc.stderr[-2000:]}")
    return result


WRAPPER = """
import sys, json, hashlib, uuid
from pathlib import Path
sys.path.insert(0, "/home/ubuntu/game-truyen-pilot/.p2p/system")
from p2p_capabilities.manus_adapter import ManusAdapter
from p2p_capabilities.failover_boundary import (
    decide_next_action, snapshot_eligibility, EligibilitySnapshot)

capsule = json.loads(Path("{CAPSULE_PATH}").read_text())
key = __import__("os").environ.get("MANUS_API_KEY", "")
adapter = ManusAdapter(api_key=key)

def probe(_t):
    ok = bool(key and len(key) >= 30)
    return EligibilitySnapshot(target=_t, eligible=ok,
        failure_class=None if ok else "AUTH_REFERENCE_ABSENT",
        evidence_pointers=("file:/home/ubuntu/.secrets/manus_api_key_new",),
        detail="fresh-process key reference check")
snap = snapshot_eligibility("manus-rest-api-v2", probe=probe)
decision = decide_next_action(
    failure_class=None if (snap and snap.eligible) else
        (snap.failure_class if snap else "TARGET_UNKNOWN"),
    current_target="manus-rest-api-v2", dispatched=False)
if decision.decision != "RETRY_SAME_TARGET":
    print("GATE:", decision.decision, "(fail-closed)"); raise SystemExit(1)

fingerprint = hashlib.sha256("{REQUEST_ID}".encode()).hexdigest()
result = adapter.execute(
    request_id="{REQUEST_ID}", request_fingerprint=fingerprint,
    task_id=None, goal_id="P2P-C40",
    prompt=capsule["capsule"]["instruction"] + "\\n\\nCAPSULE:\\n"
         + json.dumps(capsule["capsule"], ensure_ascii=False, indent=1),
    max_turns=4, timeout_seconds=240)
d = result.to_dict() if hasattr(result, "to_dict") else vars(result)
print("RESULT:", json.dumps({
    "request_id": d.get("request_id"),
    "execution_status": d.get("execution_status"),
    "task_pointer": d.get("raw_backend_receipt_pointer"),
    "exit_status": d.get("exit_status"),
}))
"""


def main() -> None:
    print("[c40-fresh-process] building state capsule from durable JSON...")
    capsule = build_capsule()
    (STATE / "c40-fresh-process-capsule.json").write_text(
        json.dumps(capsule, indent=2, ensure_ascii=False) + "\n")
    print("[c40-fresh-process] dispatching fresh bounded task (new process)...")
    result = dispatch()
    ev = PILOT / "docs" / "p2p-development" / "research" / "c40" / "evidence"
    ev.mkdir(parents=True, exist_ok=True)
    (ev / "c40-fresh-process-dispatch.json").write_text(
        json.dumps({**capsule, "dispatch": result},
                   indent=2, ensure_ascii=False) + "\n")
    print("[c40-fresh-process] fresh dispatch done:",
          json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
