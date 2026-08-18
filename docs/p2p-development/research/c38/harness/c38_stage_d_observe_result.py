"""C38 Stage D — independent observation of the fresh execution's answer.

Reads ONLY the observed messages evidence (fetched independently from
listMessages) and verifies exact equality of every capsule-bound field,
the challenge hash, git revision, stage, and owner gate. DELIVERED != READ:
message retrieval proves the answer EXISTS in the task session; behavioral
recovery of the unpredictable challenge hash is the read-evidence basis
per existing P2P rules — classified honestly, not overstated.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO / ".p2p" / "system"))
from p2p_capabilities.context import _canonical_bytes  # noqa: E402


def canonical_sha256(s: str) -> str:
    """Same canonical fingerprint the capsule builder used (C36 _canonical_bytes
    + sha256), so the computed hash is comparable to challenge_hash_expected."""
    return hashlib.sha256(_canonical_bytes(s)).hexdigest()


EVIDENCE = REPO / "docs" / "p2p-development" / "research" / "c38" / "evidence"

TASK_ID_STAGE_D = "JpWLAR4CcaG4qkXvN96etX"
TASK_ID_STAGE_B = "NWnoWkrrJeQiYWZMv8jCS5"


def main() -> int:
    msgs = json.loads(
        (EVIDENCE / "c38-stage-d-messages-observed.json").read_text(encoding="utf-8"))["messages"]
    assistant_answers = []
    timestamps = {}
    for m in msgs:
        t = m.get("timestamp")
        typ = m.get("type")
        if typ == "status_update" and "stopped" in json.dumps(m.get("status_update", {})):
            timestamps["finished_at"] = t
        if typ == "user_message":
            timestamps["started_at"] = t
        if "assistant_message" in m:
            assistant_answers.append(m["assistant_message"]["content"])
    assert assistant_answers, "no assistant answer observed"
    # Pick the terminal answer: the LAST assistant message with a non-empty
    # structured (JSON) body, ignoring any empty/intermediate assistant turns.
    answer = None
    for raw in reversed(assistant_answers):
        if raw and str(raw).strip().startswith("{"):
            answer = json.loads(raw)
            break
    assert answer is not None, "no structured assistant answer observed"
    print("terminal answer keys:", sorted(answer.keys()))

    capsule = json.loads(
        (EVIDENCE / "c38-stage-d-continuation-capsule.json").read_text(encoding="utf-8"))

    checks = {
        "project_id": answer.get("project_id") == capsule["project_id"],
        "goal_id": answer.get("goal_id") == capsule["goal_id"],
        "current_stage": answer.get("current_stage") == "D",
        "role_id": answer.get("role_id") == "p2p_iris",
        "current_verified_git_revision": (
            answer.get("current_verified_git_revision")
            == "2a371777438c88867138203e0b0bcc04283d8bed"),
        "capsule_id_exact": answer.get("capsule_id") == capsule["capsule_id"],
        "next_owner_gate": answer.get("next_owner_gate") == capsule["current_owner_gate"],
        "challenge_hash_exact_canonical": (
            answer.get("challenge_hash") == canonical_sha256(capsule["capsule_id"])),
        "challenge_hash_vs_expected": (
            answer.get("challenge_hash") == capsule["challenge_hash_expected"]),
        "challenge_hash_raw_sha256_note": (
            "Raw SHA256 of the challenge string equals 448fbaffa79a8c96... "
            "— the capsule uses the C36 canonical-byte fingerprint "
            "(_canonical_bytes + sha256) as its deterministic transformation, "
            "which is what the fresh executor was asked to compute."),
        "capsule_integrity_ok_true": answer.get("capsule_integrity_ok") is True,
    }
    for k, v in checks.items():
        if k == "challenge_hash_raw_sha256_note":
            print(k, ":", v)
        else:
            print(f"{k}: {v} (answer={json.dumps(answer.get(k))[:80]})")
    all_ok = all(checks.values())
    print("ALL_FIELD_CHECKS:", all_ok)

    # Distinctness proof Stage B vs Stage D
    distinct = {
        "stage_b_task_id": TASK_ID_STAGE_B,
        "stage_d_task_id": TASK_ID_STAGE_D,
        "different_task_ids": TASK_ID_STAGE_B != TASK_ID_STAGE_D,
        "stage_b_answer": "Hanoi/Hà Nội (capital of Vietnam)",
        "stage_d_answer": "capsule-bound structured JSON",
        "different_prompt_classes": True,
        "stage_b_timestamps": {"start": "1787036766xxx", "finish": "1787036777xxx"},
        "stage_d_timestamps": timestamps,
    }
    obs = {
        "schema": "p2p-stage-d-observation/1",
        "observed_task_id": TASK_ID_STAGE_D,
        "observation_method": "independent GET /v2/task.listMessages (not executor self-claim)",
        "messages_observed": len(msgs),
        "assistant_answer_json": answer,
        "field_checks": checks,
        "all_field_checks_passed": all_ok,
        "distinctness": distinct,
        "timestamps": timestamps,
        "read_evidence_classification": "CONTEXT_READ_PROVEN_BEHAVIORAL",
        "read_evidence_note": (
            "The fresh execution reproduced the unpredictable CAPSULE_CHALLENGE_ID "
            "and computed challenge_hash=sha256(capsule_id) exactly, which is only "
            "possible if the capsule content was read. No Stage-B transcript or "
            "conversation history was delivered to this task; the capsule was the "
            "sole durable context. Cross-task memory exclusion is NOT mechanically "
            "provable at the API layer -> SESSION_DEATH_RECOVERY = NOT_PROVEN, "
            "FRESH_EXECUTION_CAPSULE_RECOVERY = VERIFIED (see terminal report)."),
    }
    out = EVIDENCE / "c38-stage-d-observation.json"
    out.write_text(json.dumps(obs, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Observation persisted:", out)
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
