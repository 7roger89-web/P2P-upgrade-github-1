"""C38 Stage B — first live role proof harness.

Binds ONE canonical P2P role (from the recovered C35 registry — the durable
capability registry loaded by build_role_spec) to ONE real backend (Manus,
AUTH_VALID per Stage-A recheck) for a bounded, NON_MUTATING, objectively
verifiable task. Writes a structured live receipt.

Usage:
    PYTHONPATH=. python3 docs/p2p-development/research/c38/harness/c38_stage_b_role_proof.py [--role p2p_iris]

Permissions: READ-ONLY research harness. Network: Manus API v2 only.
No secrets printed. Key loaded read-only from /home/ubuntu/.secrets/manus_api_key.
"""
from __future__ import annotations

import json
import sys
import time
import hashlib
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SYSTEM_ROOT = str(REPO / ".p2p" / "system")
sys.path.insert(0, SYSTEM_ROOT)

from p2p_capabilities.agent_role import (  # noqa: E402
    CANONICAL_ROLES, build_role_spec, load_capability_registry)
from p2p_capabilities.role_contract import RoleExecutionContract  # noqa: E402
from p2p_capabilities.manus_adapter import ManusAdapter  # noqa: E402
from p2p_capabilities.backend_contract import (  # noqa: E402
    BackendContractError, BackendExecutionResult)

GOAL_ID = "C38"
TASK_ID = "c38-stage-b-first-live-role-proof"
ROLE_ID = (sys.argv[sys.argv.index("--role") + 1]
           if "--role" in sys.argv else "p2p_iris")
EVIDENCE_DIR = Path(__file__).resolve().parents[1] / "evidence"
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)


def main() -> int:
    if ROLE_ID not in CANONICAL_ROLES:
        print(f"ERROR: {ROLE_ID} is not a canonical P2P role", file=sys.stderr)
        return 2

    registry_records = load_capability_registry()
    spec = build_role_spec(ROLE_ID, registry_records)
    print(f"ROLE {ROLE_ID} bound; role_spec_hash={spec.role_spec_hash}")

    contract = RoleExecutionContract(
        goal_id=GOAL_ID,
        task_id=TASK_ID,
        role_id=ROLE_ID,
        role_spec_hash=spec.role_spec_hash,
        project_binding="P2P-upgrade-github-1",
        environment_binding="LOCAL_PROJECT",
        workspace_binding="",
        objective="BOUNDED NON-MUTATING PROOF: Answer 'What is the capital of Vietnam?' with exactly the city name and nothing else.",
        approved_scope=("API_TRANSPORT", "SYNTHETIC_TEXT_EXECUTION", "NON_MUTATING_TASK"),
        dependencies=(),
        context_package=("SYNTHETIC_TEXT_EXECUTION",),
        context_digest=sha256hex("SYNTHETIC_TEXT_EXECUTION:capital-of-vietnam-proof"),
        permission_profile=("NON_MUTATING_TASK",),
        required_capabilities=(),  # verifier certifies CERTIFICATION_SCOPES members (CODE_MUTATION, TEST_EXECUTION, BROWSER_RUNTIME, LONG_HORIZON_EXECUTION); a SYNTHETIC_TEXT_EXECUTION non-mutating proof needs none — fail-closed by scope, not capability claim
        acceptance_criteria=("answer_is_capital_of_vietnam",),
        required_evidence=("role_binding", "target_attestation", "terminal_result"),
        verification_policy="INDEPENDENT",
        explicit_execution_target="manus-api-v2",
        target_fingerprint=sha256hex("manus-api-v2:task.create:p2p-c38-stage-b-proof"),
        requested_target_attestation="REQUESTED_ONLY",
        budget="BOUNDED",
        request_fingerprint=sha256hex("c38-stage-b-01"),
    )
    print("RoleExecutionContract created:", contract.task_id,
          contract.role_spec_hash[:16] + "...", contract.permission_profile)

    contract_path = EVIDENCE_DIR / "c38-stage-b-role-contract.json"
    contract_path.write_text(json.dumps(
        contract.to_dict(), indent=2, default=str), encoding="utf-8")
    print("Contract persisted:", contract_path)

    adapter = ManusAdapter()
    started = time.time()
    try:
        result: BackendExecutionResult = adapter.execute(
            request_id="c38-stage-b-01",
            request_fingerprint=sha256hex("c38-stage-b-01"),
            task_id=TASK_ID,
            goal_id=GOAL_ID,
            prompt="Answer the question: What is the capital of Vietnam? Reply with exactly the city name and nothing else.",
            max_turns=4,
            timeout_seconds=600,
            title="p2p-c38-stage-b-proof",
        )
    except BackendContractError as e:
        print("Adapter refused (expected if auth missing):", e)
        return 3
    elapsed = time.time() - started
    print("execution_status:", result.execution_status,
          "| verification_status:", result.verification_status,
          "| error_class:", result.error_class,
          "| auth_state_after:", result.auth_state_after,
          "| exit_status:", result.exit_status)

    receipt = {
        "schema": "p2p-live-execution-receipt/1",
        "goal_id": GOAL_ID,
        "task_id": TASK_ID,
        "requested_role": ROLE_ID,
        "verified_role": ROLE_ID,
        "role_spec_hash": spec.role_spec_hash,
        "requested_target": "manus-api-v2",
        "observed_target": result.target_fingerprint,
        "observed_model": "UNKNOWN (agent_profile manus-1.6 requested; model identity not observable at API layer)",
        "context_delivered": "SYNTHETIC_TEXT_EXECUTION",
        "read_evidence": "UNKNOWN",
        "permission": ",".join(contract.permission_profile),
        "execution_status": result.execution_status,
        "verification_status": result.verification_status,
        "exit_status": result.exit_status,
        "output_pointers": list(result.output_pointers),
        "mutation_status": "NO_MUTATION (bounded non-mutating task; possible_mutation=%s)" % result.possible_mutation,
        "started_at": result.started_at,
        "finished_at": result.finished_at,
        "latency_seconds": round(elapsed, 1),
        "cost": "UNKNOWN",
        "usage_evidence": dict(result.usage_evidence) if result.usage_evidence else "UNKNOWN",
        "execution_session_id": "manus-im-task:" + (result.raw_backend_receipt_pointer or "UNKNOWN"),
        "request_id": "c38-stage-b-01",
        "at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    receipt_path = EVIDENCE_DIR / "c38-stage-b-live-receipt.json"
    receipt_path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print("Receipt persisted:", receipt_path)
    return 0


def sha256hex(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


if __name__ == "__main__":
    sys.exit(main())
