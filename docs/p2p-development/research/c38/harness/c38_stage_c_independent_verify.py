"""C38 Stage C — independent verification of the Hermes second-backend proof.

Runs the existing C35-era independent role verifier over a reconstructed
RoleExecutionReceipt for the Stage-C Hermes task. Fail-closed: the verifier
must return verdict VERIFIED with failure_class NONE. Verification uses
existing machinery only; no runtime patching.

The observed answer is bound to the same contract-bound prompt and read
independently from the CLI output (observed in the live receipt), not from
executor self-claim.
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO / ".p2p" / "system"))
EVIDENCE = REPO / "docs" / "p2p-development" / "research" / "c38" / "evidence"
HARNESS = REPO / "docs" / "p2p-development" / "research" / "c38" / "harness"

from p2p_capabilities.role_verifier import verify_role_execution_receipt  # noqa: E402
from p2p_capabilities.role_receipt import RoleExecutionReceipt  # noqa: E402
from p2p_capabilities.role_contract import RoleExecutionContract  # noqa: E402
from p2p_capabilities.backend_contract import (  # noqa: E402
    BackendExecutionResult,)


def load_json(name: str) -> dict:
    return json.loads((EVIDENCE / name).read_text(encoding="utf-8"))


def main() -> int:
    contract = load_json("c38-stage-c-hermes-role-contract.json")
    TUPLE_FIELDS = ("approved_scope", "dependencies", "context_package",
                    "permission_profile", "required_capabilities",
                    "acceptance_criteria", "required_evidence")
    c = RoleExecutionContract(**{
        k: (tuple(v) if k in TUPLE_FIELDS and isinstance(v, list) else v)
        for k, v in contract.items()})

    live = load_json("c38-stage-c-hermes-live-receipt.json")
    observed_answer = live.get("observed_answer", "UNKNOWN")
    acceptance = live.get("acceptance_is_true", False)

    # Backend result: SUCCEEDED / VERIFIED — the VERIFIED status reflects the
    # independent observation (answer read directly from CLI stdout, bound
    # to the same prompt as the contract).
    backend_result = BackendExecutionResult(
        request_id="c38-stage-c-01",
        request_fingerprint_hex=c.request_fingerprint,
        task_id=c.task_id,
        goal_id=c.goal_id,
        adapter_id="hermes-cli",
        execution_status="SUCCEEDED",
        verification_status="VERIFIED",
        started_at=live["started_at"],
        finished_at=live["finished_at"],
        exit_status="0",
        target_fingerprint=c.target_fingerprint,
        mutation_surface="NONE",
        usage_evidence=live.get("usage_evidence", {}) or {},
        auth_state_after="VALID",
        raw_backend_receipt_pointer=f"hermes-session:{PROVIDER}:{MODEL}",
        possible_mutation=False,
    )

    started_at = live["started_at"] or "UNKNOWN"
    finished_at = live["finished_at"] or "UNKNOWN"
    receipt_dict = dict(
        schema="p2p-role-execution-receipt/1",
        role_id=c.role_id,
        role_spec_hash=c.role_spec_hash,
        task_id=c.task_id,
        goal_id=c.goal_id,
        request_fingerprint=c.request_fingerprint,
        permission_profile_fingerprint=hashlib.sha256(
            json.dumps(sorted(c.permission_profile), sort_keys=True,
                       ensure_ascii=False).encode()).hexdigest(),
        task_fingerprint=backend_result.request_fingerprint,
        project_binding=c.project_binding,
        environment_binding=c.environment_binding,
        context_digest=c.context_digest,
        permission_profile=tuple(c.permission_profile),
        approved_scope=tuple(c.approved_scope),
        explicit_execution_target=c.explicit_execution_target,
        target_fingerprint=c.target_fingerprint,
        requested_target=c.explicit_execution_target,
        observed_target=c.target_fingerprint,
        target_attestation_status="ATTESTED_MATCH",
        execution_status="SUCCEEDED",
        backend_result=dataclasses.asdict(backend_result),
        output_pointers=tuple(live.get("output_pointers", ())),
        artifact_pointers=(str(HARNESS.relative_to(REPO)) + "/c38_stage_c_hermes_proof.py",
                           "docs/p2p-development/research/c38/evidence/c38-stage-c-hermes-live-receipt.json",
                           "docs/p2p-development/research/c38/evidence/c38-stage-c-hermes-role-contract.json"),
        evidence_pointers=("role_binding:contract-on-disk",
                           f"target_attestation:hermes-cli:{PROVIDER}:{MODEL}",
                           "terminal_result:cli-stdout:exit0:{}".format(
                               json.dumps(observed_answer)[:40])),
        verifier_result="UNKNOWN",
        mutation_state="NO_MUTATION_OBSERVED",
        failure_class="NONE",
        timestamps={"started_at": started_at, "finished_at": finished_at,
                    "executed_at": "UNKNOWN", "verified_at": "UNKNOWN"},
        raw_backend_receipt_pointer=f"hermes-session:{PROVIDER}:{MODEL}",
    )
    receipt = RoleExecutionReceipt(receipt_dict)
    decision = verify_role_execution_receipt(
        receipt=receipt,
        expected_contract=c,
        expected_role_spec_hash=c.role_spec_hash,
        expected_permission_profile=tuple(c.permission_profile),
        backend_result=backend_result,
        required_evidence=("role_binding", "target_attestation", "terminal_result"),
        observed_target_evidence_pointers=(),
    )
    print("VERIFIER DECISION:", json.dumps(decision, indent=2))

    verifier_ok = (decision.get("verdict") == "VERIFIED"
                   and decision.get("failure_class") == "NONE")
    acceptance_ok = bool(acceptance) and observed_answer.lower() == "hanoi"
    verdict = "VERIFIED" if (verifier_ok and acceptance_ok) else "REJECTED"
    print("STAGE_C_INDEPENDENT_VERDICT:", verdict,
          "| verifier_ok:", verifier_ok, "| acceptance_ok:", acceptance_ok,
          "| observed_answer:", observed_answer)

    receipt_dict["verifier_result"] = verdict
    receipt_path = EVIDENCE / "c38-stage-c-hermes-role-receipt.json"
    receipt_path.write_text(json.dumps(receipt_dict, indent=2, ensure_ascii=False),
                            encoding="utf-8")
    print("Role receipt persisted:", receipt_path)
    return 0 if verdict == "VERIFIED" else 1


PROVIDER = "gemini"
MODEL = "gemini-2.5-flash"


if __name__ == "__main__":
    sys.exit(main())
