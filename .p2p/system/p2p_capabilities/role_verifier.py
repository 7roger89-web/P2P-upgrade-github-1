"""C35 Role receipt verification (independent P2P verifier authority).

REQUESTED ROLE != VERIFIED ROLE EXECUTION. The verifier independently
re-checks every binding before any role receipt can count as verified.

Reject at minimum:
    wrong ROLE_ID / stale ROLE_SPEC_HASH / wrong GOAL_ID / wrong TASK_ID /
    wrong PROJECT / wrong ENVIRONMENT / wrong CONTEXT_DIGEST /
    permission mismatch / wider observed permission /
    wrong REQUEST_FINGERPRINT / wrong TARGET_FINGERPRINT /
    requested-observed target mismatch without valid attestation /
    unverified backend result / unknown mutation state /
    missing required evidence / unsupported capability /
    expired-stale certification where freshness required.

UNKNOWN fails closed. RECEIPT_COMPLETE != ROLE_EXECUTED != ROLE_VERIFIED.
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Iterable, Mapping

from .backend_contract import (
    BackendAdapterIdentity,
    BackendExecutionResult,
    BackendCapabilityCertification,
    EXECUTION_CLAIM_REQUIREMENTS,
    STATIC_REASONING_EXECUTION_EVIDENCE_INVARIANT,
    mechanical_evidence_matches,
    normalized_execution_claims,
)
from .role_contract import (
    ROLE_CONTRACT_SCHEMA,
    RoleExecutionContract,
    role_contract_fingerprint,
)
from .role_receipt import (
    MUTATION_STATES,
    RoleExecutionReceipt,
    RoleReceiptError,
    VERIFICATION_STATUSES,
)

ROLE_VERIFIER_SCHEMA = "p2p-role-execution-verifier/1"
VERDICTS = ("VERIFIED", "REJECTED", "UNKNOWN")

# Decision-trace-friendly structured vocabulary (maps to existing
# GOVERNANCE / OTHER_MATERIAL decision types; no hidden chain-of-thought).
DECISION_CODES = (
    "ROLE_SELECTED", "ROLE_NOT_REQUIRED", "ROLE_CONTRACT_BUILT",
    "ROLE_TARGET_ELIGIBLE", "ROLE_TARGET_INELIGIBLE", "ROLE_TARGET_UNKNOWN",
    "ROLE_DISPATCHED", "ROLE_RECEIPT_REJECTED", "ROLE_EXECUTION_VERIFIED",
    "ROLE_QUORUM_ACCEPTED", "ROLE_QUORUM_INCOMPLETE",
    "ROLE_PERMISSION_BLOCKED", "ROLE_CAPABILITY_BLOCKED",
)


class RoleVerifierError(ValueError):
    """Raised only when verification cannot proceed safely."""

    def __init__(self, code: str, details: Mapping[str, Any] | None = None):
        self.code = code
        self.details = details or {}
        super().__init__("ROLE_VERIFIER_ERROR:" + code)


def _check_binding(expected: str, actual: str, code: str, reasons: list[str]) -> bool:
    """Return True when binding holds; append reason when it does not."""
    ok = bool(expected) and str(expected).strip() == str(actual).strip()
    if not ok:
        reasons.append(code)
    return ok


def verify_role_execution_receipt(
    *,
    receipt: RoleExecutionReceipt,
    expected_contract: RoleExecutionContract,
    expected_role_spec_hash: str,
    expected_permission_profile: Iterable[str],
    backend_result: BackendExecutionResult | None = None,
    required_evidence: Iterable[str] = (),
    observed_target_evidence_pointers: Iterable[str] = (),
    certification_records: Iterable[BackendCapabilityCertification] = (),
    require_fresh_certification: bool = False,
) -> dict[str, Any]:
    """Independent verification of a role execution receipt.

    Every check is fail-closed: anything UNKNOWN or absent rejects with a
    BINDING_MISMATCH / relevant failure class. The verifier NEVER trusts
    a backend self-claim: BackendExecutionResult.verification_status
    alone is not sufficient — independent evidence pointers must bind
    the observed execution."""
    reasons: list[str] = []
    failure_class: str | None = None
    required_evidence_items = tuple(str(item).strip()
                                    for item in required_evidence)
    certification_items = tuple(certification_records)

    # 1. Role identity bindings.
    if not _check_binding(expected_contract.role_id, receipt.role_id,
                          "WRONG_ROLE_ID", reasons):
        failure_class = failure_class or "BINDING_MISMATCH"
    if not _check_binding(expected_role_spec_hash, receipt.role_spec_hash,
                          "STALE_ROLE_SPEC_HASH", reasons):
        failure_class = failure_class or "STALE_ROLE_SPEC"

    # 2. Goal / task / project / environment bindings.
    if not _check_binding(expected_contract.goal_id, receipt.goal_id,
                          "WRONG_GOAL_ID", reasons):
        failure_class = failure_class or "BINDING_MISMATCH"
    if not _check_binding(expected_contract.task_id, receipt.task_id,
                          "WRONG_TASK_ID", reasons):
        failure_class = failure_class or "BINDING_MISMATCH"
    if not _check_binding(expected_contract.project_binding, receipt.project_binding,
                          "WRONG_PROJECT_BINDING", reasons):
        failure_class = failure_class or "BINDING_MISMATCH"
    if not _check_binding(expected_contract.environment_binding, receipt.environment_binding,
                          "WRONG_ENVIRONMENT_BINDING", reasons):
        failure_class = failure_class or "BINDING_MISMATCH"

    # 3. Context binding.
    if not _check_binding(expected_contract.context_digest, receipt.context_digest,
                          "WRONG_CONTEXT_DIGEST", reasons):
        failure_class = failure_class or "BINDING_MISMATCH"

    # 4. Request fingerprint binding (request is a declaration; receipt
    # must bind to the same fingerprint the contract produced).
    if not _check_binding(expected_contract.request_fingerprint, receipt.request_fingerprint,
                          "WRONG_REQUEST_FINGERPRINT", reasons):
        failure_class = failure_class or "BINDING_MISMATCH"

    # Reasoning provenance is deliberately separate from the execution
    # target. It is an optional input binding, never an authority grant.
    expected_reasoning_provider = str(
        getattr(expected_contract, "reasoning_provider_id", "") or "").strip()
    observed_reasoning_provider = str(
        getattr(receipt, "reasoning_provider_id", "") or "").strip()
    if expected_reasoning_provider:
        if not _check_binding(expected_reasoning_provider,
                              observed_reasoning_provider,
                              "WRONG_REASONING_PROVIDER", reasons):
            failure_class = failure_class or "BINDING_MISMATCH"
    elif observed_reasoning_provider:
        reasons.append("UNEXPECTED_REASONING_PROVIDER")
        failure_class = failure_class or "BINDING_MISMATCH"

    # 5. Target binding: requested vs observed, attested only.
    if not _check_binding(expected_contract.target_fingerprint, receipt.target_fingerprint,
                          "WRONG_TARGET_FINGERPRINT", reasons):
        failure_class = failure_class or "BINDING_MISMATCH"
    observed_ok = bool(receipt.observed_target) and bool(observed_target_evidence_pointers)
    target_match = (str(receipt.requested_target).strip() ==
                    str(receipt.observed_target).strip())
    if not target_match and receipt.target_attestation_status not in (
            "ATTESTED_MATCH", "ATTESTED_DIFFERS", "PROFILE_BOUND", "MODEL_BOUND"):
        reasons.append("TARGET_MISMATCH_WITHOUT_ATTESTATION")
        failure_class = failure_class or "TARGET_ATTESTATION_MISSING"
    if not observed_ok and receipt.target_attestation_status == "UNKNOWN":
        reasons.append("TARGET_ATTESTATION_UNKNOWN")
        failure_class = failure_class or "TARGET_ATTESTATION_MISSING"

    # 6. Backend result: self-claim is not verification.
    if backend_result is None:
        reasons.append("NO_BACKEND_RESULT")
        failure_class = failure_class or "BACKEND_RESULT_UNVERIFIED"
    else:
        if backend_result.execution_status != "SUCCEEDED":
            reasons.append("BACKEND_EXECUTION_NOT_SUCCEEDED")
            failure_class = failure_class or "BACKEND_RESULT_UNVERIFIED"
        # The backend result is bound to the TASK contract (C30/C22
        # request fingerprint); the receipt mirrors that task binding on
        # receipt.task_fingerprint so both sides of the SAME request can
        # be cross-checked by the independent verifier.
        if not receipt.task_fingerprint or backend_result.request_fingerprint != receipt.task_fingerprint:
            reasons.append("BACKEND_RESULT_FINGERPRINT_MISMATCH")
            failure_class = failure_class or "BINDING_MISMATCH"
        if backend_result.adapter_id != receipt.observed_target:
            reasons.append("BACKEND_RESULT_TARGET_MISMATCH")
            failure_class = failure_class or "BINDING_MISMATCH"
        if (not backend_result.target_fingerprint or
                backend_result.target_fingerprint != receipt.target_fingerprint):
            reasons.append("BACKEND_RESULT_TARGET_FINGERPRINT_MISMATCH")
            failure_class = failure_class or "BINDING_MISMATCH"
        if backend_result.verification_status != "VERIFIED":
            reasons.append("BACKEND_RESULT_SELF_CLAIM_ONLY")
            failure_class = failure_class or "BACKEND_RESULT_UNVERIFIED"

    # 7. Mutation state: unknown fails closed.
    if receipt.mutation_state not in MUTATION_STATES:
        reasons.append("MUTATION_STATE_INVALID")
        failure_class = failure_class or "MUTATION_STATE_UNKNOWN"
    elif receipt.mutation_state == "MUTATION_UNKNOWN":
        reasons.append("MUTATION_STATE_UNKNOWN")
        failure_class = failure_class or "MUTATION_STATE_UNKNOWN"

    # 8. Permission never-widens: observed profile must not exceed the
    # composed envelope.
    expected_permissions = set(str(item) for item in expected_permission_profile)
    observed_permissions = set(receipt.permission_profile)
    permission_widens = bool(observed_permissions - expected_permissions)
    if permission_widens:
        reasons.append("OBSERVED_PERMISSION_WIDER_THAN_COMPOSED")
        failure_class = failure_class or "PERMISSION_WIDENING"
    if receipt.permission_profile_fingerprint:
        expected_fp = permission_profile_fingerprint(expected_permission_profile)
        if expected_fp and receipt.permission_profile_fingerprint != expected_fp:
            reasons.append("PERMISSION_PROFILE_FINGERPRINT_MISMATCH")
            failure_class = failure_class or "PERMISSION_WIDENING"

    # 9. Required evidence present and bound.
    missing_evidence: list[str] = []
    for requirement in required_evidence_items:
        if not requirement:
            continue
        receipt_evidence = (tuple(receipt.evidence_pointers)
                            + tuple(receipt.artifact_pointers)
                            + tuple(receipt.execution_evidence_pointers))
        found = any(requirement in pointer for pointer in receipt_evidence)
        if not found:
            missing_evidence.append(requirement)
    if missing_evidence:
        reasons.append("MISSING_REQUIRED_EVIDENCE:" + ",".join(missing_evidence))
        failure_class = failure_class or "EVIDENCE_MISSING"
    if (not (receipt.evidence_pointers or receipt.artifact_pointers or
             receipt.execution_evidence_pointers) and required_evidence_items):
        reasons.append("NO_EVIDENCE_POINTERS")
        failure_class = failure_class or "EVIDENCE_MISSING"

    # 10. Capability scope: every contract-required capability must hold
    # a certified record for the observed adapter; otherwise unsupported.
    for capability in expected_contract.required_capabilities:
        capability = str(capability).strip()
        if capability in ("FACT_LEDGER", "evidence-contract",
                          "EXISTING_P2P_ROUTER", "real-profile-readiness"):
            continue  # P2P-state satisfaction
        certified = any(
            cert.adapter_id == receipt.observed_target and
            cert.scope == capability and
            cert.status == "LIVE_CERTIFIED_FOR_CAPABILITY"
            for cert in certification_items
        )
        if not certified:
            reasons.append(f"UNSUPPORTED_OR_UNCERTIFIED_CAPABILITY:{capability}")
            failure_class = failure_class or "UNSUPPORTED_CAPABILITY"

    # Execution claims are a stricter layer on the same verifier path:
    # certification says what the target may do; the normalized result and
    # role receipt must still carry the same mechanical observation. A
    # static/reasoning pointer is intentionally not a mechanical pointer.
    claim_inputs = (
        tuple(getattr(expected_contract, "execution_claims", ()))
        + tuple(expected_contract.acceptance_criteria)
        + tuple(expected_contract.required_evidence)
        + required_evidence_items
    )
    execution_claims = normalized_execution_claims(claim_inputs)
    execution_claim_results: dict[str, dict[str, Any]] = {}
    for claim in execution_claims:
        requirement = EXECUTION_CLAIM_REQUIREMENTS[claim]
        capability = str(requirement["required_capability"])
        cap_bound = capability in tuple(expected_contract.required_capabilities)
        target_certified = any(
            cert.adapter_id == receipt.observed_target and
            cert.scope == capability and
            cert.status == "LIVE_CERTIFIED_FOR_CAPABILITY"
            for cert in certification_items
        )
        backend_pointers: set[str] = set()
        if backend_result is not None:
            backend_pointers.update(
                str(pointer) for pointer in
                (tuple(getattr(backend_result,
                              "execution_evidence_pointers", ()))
                 + tuple(backend_result.output_pointers)
                 + tuple(backend_result.artifact_pointers)))
        receipt_pointers = set(
            str(pointer) for pointer in
            (tuple(getattr(receipt, "execution_evidence_pointers", ()))
             + tuple(receipt.evidence_pointers)
             + tuple(receipt.output_pointers)
             + tuple(receipt.artifact_pointers)))
        observed_pointers = backend_pointers & receipt_pointers
        mechanical_ok = any(
            mechanical_evidence_matches(pointer, capability)
            for pointer in observed_pointers)
        remote_prefix = requirement.get("remote_observation_prefix")
        remote_observation_ok = (
            remote_prefix is None or
            any(pointer.startswith(str(remote_prefix))
                for pointer in observed_pointers))
        claim_reasons: list[str] = []
        if not cap_bound:
            claim_reasons.append("CAPABILITY_NOT_BOUND_TO_TASK")
            reasons.append(
                f"EXECUTION_CLAIM_CAPABILITY_NOT_BOUND:{claim}:{capability}")
            failure_class = failure_class or "UNSUPPORTED_CAPABILITY"
        if not target_certified:
            claim_reasons.append("TARGET_CAPABILITY_NOT_CERTIFIED")
            reasons.append(
                f"EXECUTION_CLAIM_TARGET_CAPABILITY_NOT_CERTIFIED:{claim}:{capability}")
            failure_class = failure_class or "UNSUPPORTED_CAPABILITY"
        if not mechanical_ok:
            claim_reasons.append("MECHANICAL_EVIDENCE_MISSING_OR_MISMATCHED")
            reasons.append(f"EXECUTION_CLAIM_MECHANICAL_EVIDENCE_MISSING:{claim}")
            failure_class = failure_class or "EVIDENCE_MISSING"
        if not remote_observation_ok:
            claim_reasons.append("REMOTE_OBSERVATION_MISSING")
            reasons.append(f"EXECUTION_CLAIM_REMOTE_OBSERVATION_MISSING:{claim}")
            failure_class = failure_class or "EVIDENCE_MISSING"
        claim_status = "VERIFIED" if not claim_reasons else "NOT_PROVEN"
        execution_claim_results[claim] = {
            "claim": claim,
            "required_capability": capability,
            "target": receipt.observed_target,
            "capability_bound_to_task": cap_bound,
            "target_capability_certified": target_certified,
            "mechanical_evidence": mechanical_ok,
            "remote_observation": remote_observation_ok,
            "status": claim_status,
            "reasons": claim_reasons,
        }
        if claim_reasons:
            reasons.append(f"EXECUTION_CLAIM_NOT_PROVEN:{claim}")

    # 11. Certification freshness where policy requires it.
    if require_fresh_certification and certification_items:
        stale = any(not cert.certified_at for cert in certification_items
                    if cert.status == "LIVE_CERTIFIED_FOR_CAPABILITY")
        if stale:
            reasons.append("CERTIFICATION_STALE_NO_TIMESTAMP")
            failure_class = failure_class or "CERTIFICATION_STALE"

    if reasons:
        verdict = "REJECTED"
    else:
        verdict = "VERIFIED"
    return {
        "schema": ROLE_VERIFIER_SCHEMA,
        "verdict": verdict,
        "receipt_role_id": receipt.role_id,
        "receipt_task_id": receipt.task_id,
        "receipt_goal_id": receipt.goal_id,
        "reasons": reasons,
        "failure_class": failure_class if reasons else "NONE",
        "verifier_authority": "INDEPENDENT",
        "evidence_invariant": STATIC_REASONING_EXECUTION_EVIDENCE_INVARIANT,
        "execution_claim_status": (
            "NOT_REQUIRED" if not execution_claim_results else
            ("VERIFIED" if all(
                result["status"] == "VERIFIED"
                for result in execution_claim_results.values())
             else "NOT_PROVEN")),
        "execution_claims": execution_claim_results,
    }


def permission_profile_fingerprint(permission_profile: Iterable[str]) -> str:
    """Deterministic fingerprint of a permission profile (binding proof)."""
    payload = json.dumps(sorted(str(item) for item in permission_profile),
                         sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def decision_record(code: str, **fields: Any) -> dict[str, Any]:
    """Structured decision trace record for C35 transitions. No hidden
    chain-of-thought — only structured transition metadata."""
    if code not in DECISION_CODES:
        raise RoleVerifierError("DECISION_CODE_INVALID", {"code": code})
    return {"decision_type": "GOVERNANCE", "code": code, **{
        key: value for key, value in fields.items() if key not in ("__builtin__",)}}
