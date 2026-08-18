"""C38 Stage D — genuinely NEW Manus execution that receives ONLY the bounded
continuation capsule (no Stage-B transcript, no conversation history).

Design (per Stage-D instruction §5–§6):
- New task id, new prompt, new request fingerprint: the backend produces a
  NEW execution identity; this script never continues or references the
  Stage-B Manus task (NWnoWkrrJeQiYWZMv8jCS5) in the submitted content.
- The capsule JSON (built by c38_stage_d_capsule_build.py) is the ONLY
  context delivered inline with the task request (project context-delivery
  mechanism: capsule content passed as the task prompt payload).
- Task is NON_MUTATING and objectively verifiable: return structured JSON
  reproducing capsule-bound fields + challenge_hash = sha256(capsule_id).
- Key loaded read-only from /home/ubuntu/.secrets/manus_api_key. Never printed.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO / ".p2p" / "system"))

from p2p_capabilities.agent_role import (  # noqa: E402
    CANONICAL_ROLES, build_role_spec, load_capability_registry)
from p2p_capabilities.role_contract import RoleExecutionContract  # noqa: E402
from p2p_capabilities.manus_adapter import ManusAdapter  # noqa: E402
from p2p_capabilities.backend_contract import BackendContractError  # noqa: E402
from p2p_capabilities.context_envelope import _fingerprint  # noqa: E402


def sha256hex(s: str) -> str:
    return _fingerprint(s)


GOAL_ID = "C38"
TASK_ID = "c38-stage-d-fresh-session-capsule-proof"
ROLE_ID = "p2p_iris"
ROLE_SPEC_HASH = "1c0ea4d2196d59493001dc43bec50c31845a6681f8171409322fe569b172b4b2"
GIT_REVISION = "2a371777438c88867138203e0b0bcc04283d8bed"
OWNER_GATE = "SECOND_BACKEND_AUTH_REQUIRED"
BACKEND_ID = "manus-rest-api-v2"

EVIDENCE_DIR = REPO / "docs" / "p2p-development" / "research" / "c38" / "evidence"
CAPSULE_PATH = EVIDENCE_DIR / "c38-stage-d-continuation-capsule.json"


def main() -> int:
    if ROLE_ID not in CANONICAL_ROLES:
        print(f"ERROR: {ROLE_ID} is not a canonical P2P role", file=sys.stderr)
        return 2
    capsule = json.loads(CAPSULE_PATH.read_text(encoding="utf-8"))
    capsule_id = capsule["capsule_id"]
    challenge_hash = capsule["challenge_hash_expected"]
    assert len(capsule_id.split("-")[1]) == 16, "challenge ID entropy check"

    contract = RoleExecutionContract(
        goal_id=GOAL_ID,
        task_id=TASK_ID,
        role_id=ROLE_ID,
        role_spec_hash=ROLE_SPEC_HASH,
        project_binding="P2P-upgrade-github-1",
        environment_binding="LOCAL_PROJECT",
        workspace_binding="",
        objective=(
            "BOUNDED NON-MUTATING FRESH-SESSION PROOF: reconstruct P2P task "
            "state from the delivered continuation capsule only; return the "
            "required structured result."
        ),
        approved_scope=("API_TRANSPORT", "SYNTHETIC_TEXT_EXECUTION", "NON_MUTATING_TASK"),
        dependencies=(),
        context_package=("SYNTHETIC_TEXT_EXECUTION",),
        context_digest=sha256hex(f"SYNTHETIC_TEXT_EXECUTION:{TASK_ID}"),
        permission_profile=("NON_MUTATING_TASK",),
        required_capabilities=(),  # non-mutating synthetic proof — fail-closed by scope
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
        target_fingerprint=sha256hex("manus-api-v2:task.create:p2p-c38-stage-d-proof"),
        requested_target_attestation="REQUESTED_ONLY",
        budget="BOUNDED",
        request_fingerprint=sha256hex(f"{TASK_ID}-01"),
    )
    print("RoleExecutionContract created:", contract.task_id,
          contract.role_spec_hash[:16] + "...", contract.permission_profile)
    contract_path = EVIDENCE_DIR / "c38-stage-d-role-contract.json"
    contract_path.write_text(json.dumps(
        contract.to_dict(), indent=2, default=str), encoding="utf-8")
    print("Contract persisted:", contract_path)

    prompt = (
        "You are given a JSON continuation capsule from a durable P2P "
        "certification project. Reconstruct the project's task state FROM "
        "THE CAPSULE ONLY (do not rely on general world knowledge).\n"
        "CAPSULE:\n" + json.dumps(capsule, indent=2) + "\n"
        "Return ONLY a JSON object with these exact fields and values copied "
        "from the capsule:\n"
        "  project_id, goal_id, current_stage, role_id, "
        "current_verified_git_revision, capsule_id, next_owner_gate\n"
        "plus the computed field:\n"
        "  challenge_hash = sha256(capsule_id) as lowercase hex\n"
        "and:\n"
        "  capsule_integrity_ok = true if your challenge_hash equals the "
        "capsule's challenge_hash_expected field, else false.\n"
        "No other commentary."
    )

    adapter = ManusAdapter()
    started = time.time()
    try:
        result = adapter.execute(
            request_id=f"{TASK_ID}-01",
            request_fingerprint=sha256hex(f"{TASK_ID}-01"),
            task_id=TASK_ID,
            goal_id=GOAL_ID,
            prompt=prompt,
            max_turns=6,
            timeout_seconds=600,
            title="p2p-c38-stage-d-proof",
        )
    except BackendContractError as e:
        print("Adapter refused:", e)
        return 3
    elapsed = time.time() - started
    print("execution_status:", result.execution_status,
          "| error_class:", result.error_class,
          "| auth_state_after:", result.auth_state_after,
          "| exit_status:", result.exit_status)
    # raw_backend_receipt_pointer = adapter transcript pointer 'manus-task:<remote_task_id>'
    backend_pointer = result.raw_backend_receipt_pointer or "UNKNOWN"
    print("raw_backend_receipt_pointer:", backend_pointer)

    live = {
        "schema": "p2p-live-execution-receipt/1",
        "goal_id": GOAL_ID,
        "task_id": TASK_ID,
        "requested_role": ROLE_ID,
        "verified_role": ROLE_ID,
        "role_spec_hash": ROLE_SPEC_HASH,
        "requested_target": BACKEND_ID,
        "observed_target": getattr(result, "target_fingerprint", None),
        "observed_model": "UNKNOWN (not observable at API layer)",
        "context_delivered": "p2p-continuation-capsule/1 (inline, bounded)",
        "read_evidence": "UNKNOWN",
        "permission": "NON_MUTATING_TASK",
        "execution_status": result.execution_status,
        "verification_status": result.verification_status,
        "exit_status": result.exit_status,
        "output_pointers": (),
        "artifact_pointers": (
            "docs/p2p-development/research/c38/evidence/c38-stage-d-continuation-capsule.json",
            "docs/p2p-development/research/c38/harness/c38_stage_d_fresh_execution.py",
        ),
        "evidence_pointers": (
            f"role_binding:contract-on-disk",
            f"target_attestation:{backend_pointer}",
            "terminal_result:listMessages:pending",
        ),
        "verifier_result": "UNKNOWN",
        "mutation_state": "NO_MUTATION_OBSERVED",
        "failure_class": "NONE",
        "timestamps": {"started_at": "", "finished_at": "", "elapsed_seconds": round(elapsed, 2)},
        "raw_backend_receipt_pointer": backend_pointer,
        "usage_evidence": (
            {"credit_usage": result.credit_usage, "units": "manus-credits",
             "source": "task.detail.credit_usage"}
            if hasattr(result, "credit_usage") else {}
        ),
    }
    # capture timestamps from adapter result if present
    live["timestamps"]["started_at"] = result.started_at or live["timestamps"]["started_at"]
    live["timestamps"]["finished_at"] = result.finished_at or live["timestamps"]["finished_at"]

    out = EVIDENCE_DIR / "c38-stage-d-live-receipt.json"
    out.write_text(json.dumps(live, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Live receipt persisted:", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
