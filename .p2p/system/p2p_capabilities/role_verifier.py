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
from datetime import datetime, timezone

import hashlib
import json
import re
from typing import Any, Iterable, Mapping

from .backend_contract import (
    BackendAdapterIdentity,
    BackendExecutionResult,
    BackendCapabilityCertification,
    CERTIFICATION_SCOPES,
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
    attestation_policy: str = "STANDARD",
    now_reference: str = "",
) -> dict[str, Any]:
    """Independent verification of a role execution receipt.

    Every check is fail-closed: anything UNKNOWN or absent rejects with a
    BINDING_MISMATCH / relevant failure class. The verifier NEVER trusts
    a backend self-claim: BackendExecutionResult.verification_status
    alone is not sufficient — independent evidence pointers must bind
    the observed execution."""
    reasons: list[str] = []
    failure_class: str | None = None

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
    for requirement in required_evidence:
        requirement = str(requirement).strip()
        if not requirement:
            continue
        found = any(requirement in pointer for pointer in receipt.evidence_pointers) \
            or any(requirement in pointer for pointer in receipt.artifact_pointers)
        if not found:
            missing_evidence.append(requirement)
    if missing_evidence:
        reasons.append("MISSING_REQUIRED_EVIDENCE:" + ",".join(missing_evidence))
        failure_class = failure_class or "EVIDENCE_MISSING"
    if not receipt.evidence_pointers and required_evidence:
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
            cert.scope == capability and
            cert.status == "LIVE_CERTIFIED_FOR_CAPABILITY"
            for cert in certification_records
        )
        if capability in CERTIFICATION_SCOPES and not certified:
            reasons.append(f"UNSUPPORTED_OR_UNCERTIFIED_CAPABILITY:{capability}")
            failure_class = failure_class or "UNSUPPORTED_CAPABILITY"

    # 11. Certification freshness where policy requires it.
    if require_fresh_certification and certification_records:
        stale = any(not cert.certified_at for cert in certification_records
                    if cert.status == "LIVE_CERTIFIED_FOR_CAPABILITY")
        if stale:
            reasons.append("CERTIFICATION_STALE_NO_TIMESTAMP")
            failure_class = failure_class or "CERTIFICATION_STALE"


    # ------------------------------------------------------------------
    # 12. Real host attestation (Owner condition; only under REAL_REQUIRED).
    # STANDARD keeps the C35 behavior byte-identical.
    # ------------------------------------------------------------------
    if attestation_policy == "REAL_REQUIRED":
        from .host_attestation import (  # noqa: PLC0415
            verify_all_attestation_sources, attestation_already_used)
        record_value = receipt.host_attestation if receipt.host_attestation else None
        if record_value is None:
            reasons.append("REAL_HOST_ATTESTATION_ABSENT")
            failure_class = failure_class or "REAL_ATTESTATION_MISSING"
        else:
            from .host_attestation import HostAttestationRecord  # noqa: PLC0415
            try:
                attestation = HostAttestationRecord.from_mapping(record_value)
            except Exception as exc:  # fail closed: any malformed record rejects
                reasons.append("REAL_ATTESTATION_RECORD_MALFORMED:" + str(exc)[:128])
                failure_class = failure_class or "REAL_ATTESTATION_MISSING"
                attestation = None
            if attestation is not None:
                # 12a. Contract/run/dispatch binding (Owner amendment 1).
                if attestation.execution_contract_digest != receipt.request_fingerprint:
                    reasons.append("REAL_ATTESTATION_CONTRACT_MISMATCH")
                    failure_class = failure_class or "REPLAY_CONTRACT_MISMATCH"
                if attestation.run_id and f"c36:{expected_contract.goal_id}" != str(attestation.run_id):
                    reasons.append("REAL_ATTESTATION_RUN_MISMATCH")
                    failure_class = failure_class or "REPLAY_RUN_MISMATCH"
                # 12b. Identity surface fingerprint re-derivation.
                identity_surface = {
                    "adapter_id": attestation.adapter_id,
                    "harness": attestation.harness,
                    "provider": attestation.provider,
                    "model": attestation.model,
                    "host_execution_identity": attestation.host_execution_identity,
                }
                recomputed = hashlib.sha256(canonical_identity_bytes(
                    identity_surface)).hexdigest()
                if recomputed != attestation.host_identity_fingerprint:
                    reasons.append("REAL_ATTESTATION_IDENTITY_FINGERPRINT_MISMATCH")
                    failure_class = failure_class or "BINDING_MISMATCH"
                # 12c. Evidence sources must really exist and bind
                # (Owner amendment 2): pointer strings self-authored by
                # the executor are verified, never assumed.
                source_check = verify_all_attestation_sources(attestation)
                if not source_check["all_sources_present"]:
                    reasons.append("REAL_ATTESTATION_EVIDENCE_SOURCE_ABSENT")
                    failure_class = failure_class or "EVIDENCE_SOURCE_UNVERIFIABLE"
                elif source_check["digest_mismatch"]:
                    reasons.append("REAL_ATTESTATION_EVIDENCE_DIGEST_MISMATCH")
                    failure_class = failure_class or "EVIDENCE_SOURCE_UNVERIFIABLE"
                # 12d. Observation must bind to the attestation record,
                # not float freely.
                attestation_pointer_set = set(attestation.attestation_evidence_pointers)
                observed_binding = any(pointer in attestation_pointer_set
                                       for pointer in observed_target_evidence_pointers)
                if not observed_binding:
                    reasons.append("REAL_ATTESTATION_OBSERVATION_NOT_BOUND")
                    failure_class = failure_class or "REAL_ATTESTATION_MISSING"
                # 12e. Freshness window (replay part of Owner amendment 3).
                if attestation.attested_at:
                    try:
                        attested_dt = datetime.fromisoformat(
                            attestation.attested_at.replace("Z", "+00:00"))
                        ref = datetime.now(timezone.utc)
                        if now_reference:
                            ref = datetime.fromisoformat(
                                now_reference.replace("Z", "+00:00"))
                        if abs((attested_dt - ref).total_seconds()) > 3600:
                            reasons.append("REAL_ATTESTATION_STALE")
                            failure_class = failure_class or "CERTIFICATION_STALE"
                    except (TypeError, ValueError):
                        reasons.append("REAL_ATTESTATION_TIMESTAMP_UNPARSEABLE")
                        failure_class = failure_class or "CERTIFICATION_STALE"

    # ------------------------------------------------------------------
    # 13. Replay protection (Owner amendment 3): attestations that were
    # already consumed by any prior run/dispatch reject. STANDARD never
    # consults the ledger, so C35 behavior stays byte-identical.
    # ------------------------------------------------------------------
    if attestation_policy == "REAL_REQUIRED" and receipt.host_attestation:
        from .host_attestation import (  # noqa: PLC0415
            HostAttestationRecord, attestation_already_used)
        try:
            attestation2 = HostAttestationRecord.from_mapping(receipt.host_attestation)
            fp = attestation2.attestation_fingerprint
            from .host_attestation import load_attestation_ledger  # noqa: PLC0415
            ledger_entries = load_attestation_ledger()
            matching = [e for e in ledger_entries
                        if e.get("attestation_fingerprint") == fp]
            own = attestation2.to_dict()
            foreign = [e for e in matching
                       if not (e.get("run_id") == own.get("run_id")
                               and e.get("dispatch_id") == own.get("dispatch_id")
                               and e.get("execution_contract_digest")
                               == own.get("execution_contract_digest"))]
            if len(matching) > 1 or foreign:
                reasons.append("REAL_ATTESTATION_REPLAYED")
                failure_class = failure_class or "REPLAY_ALREADY_USED"
        except Exception:
            pass  # malformed records already rejected by group 12

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
    }


def canonical_identity_bytes(mapping: Mapping[str, Any]) -> bytes:
    return json.dumps(mapping, sort_keys=True, ensure_ascii=False).encode("utf-8")


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
