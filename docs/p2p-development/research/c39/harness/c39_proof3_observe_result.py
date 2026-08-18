# -*- coding: utf-8 -*-
"""C39 Proof 3 — independent observation of the capsule-continuity answer.

Reads ONLY the observed messages evidence (fetched independently from
GET /v2/task.listMessages) and verifies exact equality of every
capsule-bound field, the challenge hash, git revision, stage, and owner
gate. DELIVERED != READ: message retrieval proves the answer EXISTS;
behavioral recovery of the unpredictable challenge hash is the
read-evidence basis. SESSION_DEATH_RECOVERY stays NOT_PROVEN (API layer
cannot mechanically exclude hidden cross-task memory).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path("/home/ubuntu/p2p-repo")
sys.path.insert(0, str(REPO / ".p2p" / "system"))

from p2p_capabilities.context_envelope import _fingerprint  # noqa: E402

EVIDENCE = REPO / "docs" / "p2p-development" / "research" / "c39" / "evidence"
TASK_ID_PROOF_3 = (EVIDENCE / "c39-proof-3-live-evidence.json")
MANUS_TASK_ID_FILE = EVIDENCE / "c39-proof-3-messages-observed.json"


def main() -> int:
    live = json.loads(TASK_ID_PROOF_3.read_text())
    remote_task_id = live["manus_task_id"]
    msgs_path = MANUS_TASK_ID_FILE
    msgs = json.loads(msgs_path.read_text())["messages"]

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
    answer = None
    for raw in reversed(assistant_answers):
        if raw and str(raw).strip().startswith("{"):
            answer = json.loads(raw)
            break
    assert answer is not None, "no structured assistant answer observed"
    print("terminal answer keys:", sorted(answer.keys()))

    capsule = json.loads(
        (EVIDENCE / "c39-proof-3-continuation-capsule.json").read_text())
    git = live["git_revision"]

    checks = {
        "project_id": answer.get("project_id") == capsule["project_id"],
        "goal_id": answer.get("goal_id") == capsule["goal_id"],
        "current_stage": answer.get("current_stage") == "C39",
        "role_id": answer.get("role_id") == "p2p_iris",
        "current_verified_git_revision": (
            answer.get("current_verified_git_revision") == git),
        "capsule_id_exact": answer.get("capsule_id") == capsule["capsule_id"],
        "next_owner_gate": (answer.get("next_owner_gate")
                            == capsule["current_owner_gate"]),
        "proofs_bound_exact": (answer.get("proofs_bound")
                               == capsule["proofs_bound"]),
        "challenge_hash_exact": (
            answer.get("challenge_hash")
            == _fingerprint(capsule["capsule_id"])),
        "challenge_hash_vs_expected": (
            answer.get("challenge_hash") == capsule["challenge_hash_expected"]),
        "capsule_integrity_ok_true": answer.get("capsule_integrity_ok") is True,
    }
    for k, v in checks.items():
        print(f"{k}: {v}")
    all_ok = all(checks.values())
    print("ALL_FIELD_CHECKS:", all_ok)

    obs = {
        "schema": "p2p-c39-proof-3-observation/1",
        "observed_task_id": remote_task_id,
        "observation_method": "independent GET /v2/task.listMessages "
                              "(not executor self-claim)",
        "messages_observed": len(msgs),
        "assistant_answer_json": answer,
        "field_checks": checks,
        "all_field_checks_passed": all_ok,
        "git_revision_at_proof": git,
        "capsule_id": capsule["capsule_id"],
        "read_evidence_classification": "CONTEXT_READ_PROVEN_BEHAVIORAL",
        "read_evidence_note": (
            "The fresh execution reproduced the unpredictable "
            "CAPSULE_CHALLENGE_ID and computed challenge_hash=sha256 "
            "(C36 canonical fingerprint) exactly, which is only possible if "
            "the capsule content was read. No transcript or conversation "
            "history was delivered; the capsule was the sole durable "
            "context. Cross-task memory exclusion is NOT mechanically "
            "provable at the API layer -> SESSION_DEATH_RECOVERY = "
            "NOT_PROVEN."),
        "timestamps": timestamps,
    }
    out = EVIDENCE / "c39-proof-3-observation.json"
    out.write_text(json.dumps(obs, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Observation persisted:", out)
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
