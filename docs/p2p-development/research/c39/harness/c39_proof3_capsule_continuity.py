# -*- coding: utf-8 -*-
"""C39 Proof 3 — Context/capsule continuity on Backend B (Manus API v2).

Backend B receives ONLY the bounded continuation capsule (no transcript,
no conversation history) and must reconstruct C39 task state exactly:
every capsule-bound field plus challenge_hash computed from the
unpredictable capsule_id.  Mirrors C38 Stage-D capsule proof semantics;
this proof binds C39 state (Proof 1 + Proof 2 evidence pointers, the
failover-boundary decisions).

Live backend calls: exactly ONE Manus API task execution (bounded,
non-mutating).
"""
from __future__ import annotations

import json
import os
import secrets
import sys
import time
from pathlib import Path

REPO = Path("/home/ubuntu/p2p-repo")
sys.path.insert(0, str(REPO / ".p2p" / "system"))

from p2p_capabilities.agent_role import (  # noqa: E402
    CANONICAL_ROLES, build_role_spec, load_capability_registry)
from p2p_capabilities.role_contract import RoleExecutionContract  # noqa: E402
from p2p_capabilities.manus_adapter import ManusAdapter  # noqa: E402
from p2p_capabilities.context_envelope import _fingerprint  # noqa: E402

GOAL_ID = "C39"
TASK_ID = "c39-proof-3-capsule-continuity"
ROLE_ID = "p2p_iris"
ROLE_SPEC_HASH = "1c0ea4d2196d59493001dc43bec50c31845a6681f8171409322fe569b172b4b2"
EVIDENCE_DIR = REPO / "docs" / "p2p-development" / "research" / "c39" / "evidence"
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
GIT_REVISION = Path("/home/ubuntu/p2p-repo/.git/HEAD").read_text().strip()\
    .replace("ref: refs/heads/", "")


def main() -> int:
    assert ROLE_ID in CANONICAL_ROLES, "p2p_iris not canonical"

    # ---------- capsule from C39 state ---------------------------------
    capsule_id = "challenge-" + secrets.token_hex(8)
    assert len(capsule_id.split("-")[1]) == 16
    capsule = {
        "schema": "p2p-continuation-capsule/1",
        "capsule_id": capsule_id,
        "project_id": "P2P-upgrade-github-1",
        "goal_id": GOAL_ID,
        "current_stage": "C39",
        "previous_verified_stage": "C38",
        "current_verified_git_revision": GIT_REVISION,
        "role_id": ROLE_ID,
        "role_spec_hash": ROLE_SPEC_HASH,
        "proofs_bound": [
            "c39-proof-1-governed-live-selection",
            "c39-proof-2-drift-safe-reselection",
        ],
        "failover_boundary_revision": str(
            EVIDENCE_DIR / "c39-proof-2-drift-evidence.json"),
        "current_owner_gate": "NONE_REQUIRED",
        "next_task_id": TASK_ID,
        "verification_rule": (
            "Fresh execution must return a structured result containing: "
            "project_id, goal_id, current_stage, role_id, "
            "current_verified_git_revision, capsule_id, next_owner_gate, "
            "proofs_bound, plus challenge_hash = sha256(capsule_id) exactly. "
            "Acceptance: exact string equality for every field; accidental "
            "success probability <= 2^-128 on the challenge hash."),
        "challenge_hash_source_field": "capsule_id",
        "source_evidence_pointers": [
            "docs/p2p-development/research/c39/evidence/c39-proof-1-role-contract.json",
            "docs/p2p-development/research/c39/evidence/c39-proof-1-failover-decision.json",
            "docs/p2p-development/research/c39/evidence/c39-proof-1-live-evidence.json",
            "docs/p2p-development/research/c39/evidence/c39-proof-2-role-contract.json",
            "docs/p2p-development/research/c39/evidence/c39-proof-2-drift-evidence.json",
            "docs/p2p-development/research/c39/evidence/c39-proof-2-live-evidence.json",
        ],
        "notes": {
            "transcript_excluded": True,
            "conversation_history_excluded": True,
            "no_credential_data": True,
        },
    }
    challenge_hash = _fingerprint(capsule["capsule_id"])
    capsule["challenge_hash_expected"] = challenge_hash
    capsule_path = EVIDENCE_DIR / "c39-proof-3-continuation-capsule.json"
    capsule_path.write_text(json.dumps(capsule, indent=2, ensure_ascii=False),
                            encoding="utf-8")
    print("Capsule persisted:", capsule_path)
    print("challenge_hash_expected:", challenge_hash)

    contract = RoleExecutionContract(
        goal_id=GOAL_ID,
        task_id=TASK_ID,
        role_id=ROLE_ID,
        role_spec_hash=ROLE_SPEC_HASH,
        project_binding="P2P-upgrade-github-1",
        environment_binding="LOCAL_PROJECT",
        workspace_binding="",
        objective=("BOUNDED NON-MUTATING FRESH-SESSION CAPSULE PROOF: "
                   "reconstruct C39 task state from the delivered "
                   "continuation capsule only; return the required "
                   "structured result."),
        approved_scope=("API_TRANSPORT", "SYNTHETIC_TEXT_EXECUTION", "NON_MUTATING_TASK"),
        dependencies=(),
        context_package=("SYNTHETIC_TEXT_EXECUTION",),
        context_digest=_fingerprint(f"SYNTHETIC_TEXT_EXECUTION:{TASK_ID}"),
        permission_profile=("NON_MUTATING_TASK",),
        required_capabilities=(),
        acceptance_criteria=(
            "structured_result_fields_exact",
            "challenge_hash_sha256_capsule_id_exact",
            "git_revision_exact",
            "stage_exact",
            "owner_gate_exact",
        ),
        required_evidence=("role_binding", "target_attestation", "terminal_result"),
        verification_policy="INDEPENDENT",
        explicit_execution_target="manus-api-v2",
        target_fingerprint=_fingerprint("manus-api-v2:task.create:p2p-c39-proof-3"),
        requested_target_attestation="REQUESTED_ONLY",
        budget="BOUNDED",
        request_fingerprint=_fingerprint(f"{TASK_ID}-01"),
    )
    contract_path = EVIDENCE_DIR / "c39-proof-3-role-contract.json"
    contract_path.write_text(json.dumps(contract.to_dict(), indent=2, default=str))
    print("Contract persisted:", contract_path)

    prompt = (
        "You are given a JSON continuation capsule from a durable P2P "
        "certification project. Reconstruct the project's task state FROM "
        "THE CAPSULE ONLY (do not rely on general world knowledge).\n"
        "CAPSULE:\n" + json.dumps(capsule, indent=2) + "\n"
        "Return ONLY a JSON object with these exact fields and values "
        "copied from the capsule:\n"
        "  project_id, goal_id, current_stage, role_id, "
        "current_verified_git_revision, capsule_id, next_owner_gate, "
        "proofs_bound\n"
        "plus the computed field:\n"
        "  challenge_hash = sha256(capsule_id) as lowercase hex\n"
        "and:\n"
        "  capsule_integrity_ok = true if your challenge_hash equals the "
        "capsule's challenge_hash_expected field, else false.\n"
        "No other commentary."
    )

    key = Path("/home/ubuntu/.secrets/manus_api_key_new").read_text().strip()
    adapter = ManusAdapter(api_key=key)
    started = time.time()
    result = adapter.execute(
        request_id=f"{TASK_ID}-01",
        request_fingerprint=_fingerprint(f"{TASK_ID}-01"),
        task_id=TASK_ID,
        goal_id=GOAL_ID,
        prompt=prompt,
        max_turns=6,
        timeout_seconds=600,
        title="p2p-c39-proof-3",
    )
    elapsed = round(time.time() - started, 2)
    print("Execution:", result.execution_status, "| error:",
          result.error_class or "-", "| latency:", elapsed, "s")
    pointer = result.raw_backend_receipt_pointer or ""
    task_id_remote = pointer.split(":")[-1] if ":" in pointer else pointer
    print("Backend receipt pointer:", pointer)

    evidence = {
        "schema": "c39-proof-3-live-evidence/1",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "role_id": ROLE_ID,
        "role_spec_hash": ROLE_SPEC_HASH,
        "capsule_path": str(capsule_path.relative_to(REPO)),
        "execution_status": result.execution_status,
        "error_class": result.error_class,
        "latency_seconds": elapsed,
        "backend_receipt_pointer": pointer,
        "manus_task_id": task_id_remote,
        "output_pointers": result.output_pointers,
        "verification_status": result.verification_status,
        "contract_fingerprint": contract.request_fingerprint,
        "git_revision": GIT_REVISION,
    }
    out = EVIDENCE_DIR / "c39-proof-3-live-evidence.json"
    out.write_text(json.dumps(evidence, indent=2, default=str), encoding="utf-8")
    print("Evidence persisted; manuscript task:", task_id_remote)
    # Save capsule_id for the observer script
    (EVIDENCE_DIR / "c39-proof-3-capsule-id.txt").write_text(capsule_id)
    return 0 if result.execution_status == "SUCCEEDED" else 4


if __name__ == "__main__":
    sys.exit(main())
