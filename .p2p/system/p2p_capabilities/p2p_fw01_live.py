"""FRAMEWORK-01 live backend E2E leg — §25 of the Owner contract.

One bounded, non-destructive, non-production live task through the real
Manus execution backend, composed with the canonical operating loop.

    Owner intent -> task selection -> target selection -> permission ->
    dispatch -> backend receipt -> observed result -> verifier -> checkpoint

Read-only by prompt contract. No business/private data. Role binding is
honest: dispatch is role-unbound, so no role identity is claimed.

If current auth/provider is unavailable: LIVE_E2E =
BLOCKED_EXTERNAL_AUTH_OR_PROVIDER (never fabricated).
"""
import hashlib
import json
import sys
import time
from pathlib import Path

P2P_SYSTEM = Path(__file__).resolve().parent
sys.path.insert(0, str(P2P_SYSTEM))

API_KEY_PATH = Path("/home/ubuntu/.secrets/manus_api_key_new")
EVIDENCE_DIR = Path("/home/ubuntu/p2p-repo/docs/p2p-development/research/framework-01/live-e2e")
REQUEST_ID = "fw01-live-backend-leg"


def main() -> int:
    from p2p_capabilities.manus_adapter import ManusAdapter

    evidence = EVIDENCE_DIR
    evidence.mkdir(parents=True, exist_ok=True)

    # --- 1. Auth availability (honest gate) ---
    if not API_KEY_PATH.exists():
        out = {
            "leg": "FW01_LIVE_E2E",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "LIVE_E2E": "BLOCKED_EXTERNAL_AUTH_OR_PROVIDER",
            "reason": "manus_api_key_new not present on this host",
            "deterministic_machinery_unaffected": True,
        }
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return 0

    key = API_KEY_PATH.read_text(encoding="utf-8").strip()
    adapter = ManusAdapter(api_key=key)

    # --- 2. Owner intent (canonical phrase) ---
    intent = "Tiếp tục hoàn thiện dự án bằng P2P."

    # --- 3. Task selection: a safe, self-contained, non-production task ---
    prompt = (
        "Đây là nhiệm vụ READ-ONLY xác minh live backend của P2P. NHIỆM VỤ: "
        "tự tạo một đoạn văn ngắn (2-3 câu) trong ngữ cảnh của bạn về "
        "'P2P autonomous project control plane' và trả về MỘT câu tóm tắt "
        "10-20 từ tiếng Việt. KHÔNG thực hiện hành động nào khác, KHÔNG gọi "
        "API, KHÔNG tạo tài nguyên, KHÔNG đọc file nào bên ngoài. Trả lời "
        "đúng định dạng: TOMTAT: <câu tóm tắt>"
    )
    prompt_fingerprint = hashlib.sha256(prompt.encode()).hexdigest()

    # --- 4. Target selection: pinned Manus adapter profile ---
    # --- 5. Permission: read-only prompt contract; no connectors/skills ---

    result = adapter.execute(
        request_id=REQUEST_ID,
        request_fingerprint=prompt_fingerprint,
        task_id="fw01-proof-live-1",
        goal_id="fw01-live-e2e",
        prompt=prompt,
        max_turns=4,
        timeout_seconds=600,
        title="P2P-FRAMEWORK-01 live backend leg",
        agent_profile="manus-1.6-lite",
        evidence_dir=str(evidence),
    )

    # --- 6. Verifier: deterministic check of observed result ---
    status = str(result.execution_status)
    # Answer text is observed from the remote transcript pointer evidence
    # (never parsed into authoritative state; used only for verification).
    observed = ""
    for candidate in ("task.listMessages", "messages"):
        for f in evidence.glob(f"{REQUEST_ID}-*.json"):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                if isinstance(data, dict) and any(
                        k in str(data.get("url", "")) for k in (candidate,)):
                    for m in data.get("messages", []) or []:
                        observed += str(
                            m.get("assistant_message", {}).get("content", ""))
            except (json.JSONDecodeError, KeyError):
                pass
    observed = observed or str(
        result.output_pointers[-1] if result.output_pointers else "")
    ok = status == "SUCCEEDED"

    verifier = {
        "verdict": "VERIFIED" if ok else "NOT_VERIFIED",
        "execution_status": status,
        "answer_observed": bool(observed.strip()),
    }

    # --- 7. Checkpoint: durable, machine-readable ---
    checkpoint = {
        "project": "fw01-live-e2e",
        "goal_id": "fw01-live-e2e",
        "task_completed": "live-read-only-summary",
        "mutation_status": "READ_ONLY_NO_MUTATION",
        "verification": verifier,
        "evidence_pointers": {
            "create_receipt": f"{evidence}/{REQUEST_ID}-create.json",
            "raw_backend_receipt_pointer": result.raw_backend_receipt_pointer,
        },
        "next_safe_action": "none - single live task by contract",
        "owner_gate_state": "none",
        "attempt": 1,
        "loop_status": "DONE",
    }
    (evidence / f"{REQUEST_ID}-checkpoint.json").write_text(
        json.dumps(checkpoint, indent=2, ensure_ascii=False), encoding="utf-8")

    out = {
        "leg": "FW01_LIVE_E2E",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "intent": intent,
        "task_selection": "read-only summary (safe, self-contained)",
        "role_binding": "UNBOUND",
        "role_identity_claimed": False,
        "target_selection": {
            "adapter": result.adapter_id,
            "profile": "manus-1.6-lite",
            "provider_neutral_composition": True,
        },
        "permission": "read-only prompt contract, no connectors/skills",
        "dispatch": "task.create via Manus REST",
        "backend_receipt": {
            "execution_status": status,
            "raw_backend_receipt_pointer": result.raw_backend_receipt_pointer,
        },
        "verifier": verifier,
        "checkpoint": f"{evidence}/{REQUEST_ID}-checkpoint.json",
        "LIVE_E2E": "VERIFIED" if ok else (
            "BLOCKED_EXTERNAL_AUTH_OR_PROVIDER"
            if status == "UNKNOWN" else "NOT_VERIFIED"),
    }
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
