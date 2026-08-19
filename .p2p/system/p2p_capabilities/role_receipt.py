"""C35 RoleExecutionReceipt — normalized role execution evidence.

A role receipt binds: ROLE_ID / ROLE_SPEC_HASH / GOAL_ID / TASK_ID /
PROJECT_BINDING / ENVIRONMENT_BINDING / CONTEXT_DIGEST / PERMISSION
profile fingerprint / REQUEST_FINGERPRINT / REQUESTED_TARGET /
OBSERVED_TARGET (attestation status) / TARGET_FINGERPRINT /
EXECUTION_STATUS / OUTPUT_POINTERS / ARTIFACT_POINTERS /
EVIDENCE_POINTERS / VERIFIER_RESULT / MUTATION_STATE / FAILURE_CLASS /
TIMESTAMPS / RAW_BACKEND_RECEIPT_POINTER.

No receipt counts as verified merely because it is structurally complete
(RECEIPT_COMPLETE != ROLE_EXECUTED != ROLE_VERIFIED).

MUTATION STATE must be one of the canonical states; UNKNOWN fails closed.
"""
from __future__ import annotations

import re
from typing import Any, Mapping

from .backend_contract import AUTH_STATES

ROLE_RECEIPT_SCHEMA = "p2p-role-execution-receipt/1"

EXECUTION_STATUSES = (
    "SUCCEEDED", "FAILED", "INTERRUPTED", "UNKNOWN", "BLOCKED",
    "CANCELLED", "PARTIAL_MUTATION_UNKNOWN",
)
VERIFICATION_STATUSES = ("VERIFIED", "FAILED", "INCOMPLETE", "UNKNOWN")

MUTATION_STATES = (
    "NO_MUTATION_OBSERVED",      # read-only / no file changes observed
    "BOUNDED_MUTATION_OBSERVED", # only approved scope changed, evidence bound
    "MUTATION_OBSERVED",         # changes observed, scope to be verified
    "PARTIAL_MUTATION_UNKNOWN",  # cannot prove what changed
    "MUTATION_UNKNOWN",          # mutation status genuinely unknown
)

FAILURE_CLASSES = (
    "NONE",
    "BINDING_MISMATCH",
    "STALE_ROLE_SPEC",
    "PERMISSION_WIDENING",
    "CAPABILITY_MISSING",
    "AUTH_UNAVAILABLE",
    "TARGET_ATTESTATION_MISSING",
    "TARGET_MISMATCH",
    "BACKEND_RESULT_UNVERIFIED",
    "MUTATION_STATE_UNKNOWN",
    "EVIDENCE_MISSING",
    "UNSUPPORTED_CAPABILITY",
    "CERTIFICATION_STALE",
    "UNKNOWN_FAILURE",
)

TIMESTAMP_FIELDS = ("executed_at", "finished_at", "verified_at")


class RoleReceiptError(ValueError):
    """Raised only when a role receipt cannot be safely used."""

    def __init__(self, code: str, details: Mapping[str, Any] | None = None):
        self.code = code
        self.details = details or {}
        super().__init__("ROLE_RECEIPT_ERROR:" + code)


def role_receipt_to_dict(receipt: "RoleExecutionReceipt") -> dict[str, Any]:
    # an absent host_attestation keeps the C35 serialization
    # byte-identical (dict equality with C35 receipts).
    result = {
        "schema": ROLE_RECEIPT_SCHEMA,
        "role_id": receipt.role_id,
        "role_spec_hash": receipt.role_spec_hash,
        "goal_id": receipt.goal_id,
        "task_id": receipt.task_id,
        "project_binding": receipt.project_binding,
        "environment_binding": receipt.environment_binding,
        "context_digest": receipt.context_digest,
        "permission_profile": receipt.permission_profile,
        "permission_profile_fingerprint": receipt.permission_profile_fingerprint,
        "request_fingerprint": receipt.request_fingerprint,
        "task_fingerprint": receipt.task_fingerprint,
        "requested_target": receipt.requested_target,
        "observed_target": receipt.observed_target,
        "target_attestation_status": receipt.target_attestation_status,
        "target_fingerprint": receipt.target_fingerprint,
        "execution_status": receipt.execution_status,
        "output_pointers": list(receipt.output_pointers),
        "artifact_pointers": list(receipt.artifact_pointers),
        "evidence_pointers": list(receipt.evidence_pointers),
        "verifier_result": receipt.verifier_result,
        "verifier_reasons": list(receipt.verifier_reasons),
        "mutation_state": receipt.mutation_state,
        "failure_class": receipt.failure_class,
        "timestamps": dict(receipt.timestamps),
        "raw_backend_receipt_pointer": receipt.raw_backend_receipt_pointer,
    }
    if receipt.host_attestation is not None:
        result["host_attestation"] = receipt.host_attestation
    if receipt.dispatch_id:
        result["dispatch_id"] = receipt.dispatch_id
    return result


def new_role_receipt(**fields: Any) -> dict[str, Any]:
    """Build a normalized role receipt dict with honest defaults.

    Unknown mutation state defaults to MUTATION_UNKNOWN (fail closed).
    Missing timestamps default to UNKNOWN (never invented)."""
    timestamps = dict(fields.get("timestamps") or {})
    for key in TIMESTAMP_FIELDS:
        timestamps.setdefault(key, "UNKNOWN")
    return {
        "schema": ROLE_RECEIPT_SCHEMA,
        "role_id": str(fields.get("role_id", "")),
        "role_spec_hash": str(fields.get("role_spec_hash", "")),
        "goal_id": str(fields.get("goal_id", "")),
        "task_id": str(fields.get("task_id", "")),
        "project_binding": str(fields.get("project_binding", "")),
        "environment_binding": str(fields.get("environment_binding", "LOCAL_PROJECT")),
        "context_digest": str(fields.get("context_digest", "")),
        "permission_profile": tuple(fields.get("permission_profile") or ()),
        "permission_profile_fingerprint": str(fields.get("permission_profile_fingerprint", "")),
        "request_fingerprint": str(fields.get("request_fingerprint", "")),
        "task_fingerprint": str(fields.get("task_fingerprint", "")),
        "requested_target": str(fields.get("requested_target", "")),
        "observed_target": str(fields.get("observed_target") or ""),
        "target_attestation_status": str(
            fields.get("target_attestation_status") or "REQUESTED_ONLY"),
        "target_fingerprint": str(fields.get("target_fingerprint", "")),
        "execution_status": str(fields.get("execution_status") or "UNKNOWN"),
        "output_pointers": tuple(fields.get("output_pointers") or ()),
        "artifact_pointers": tuple(fields.get("artifact_pointers") or ()),
        "evidence_pointers": tuple(fields.get("evidence_pointers") or ()),
        "verifier_result": str(fields.get("verifier_result") or "UNKNOWN"),
        "verifier_reasons": tuple(fields.get("verifier_reasons") or ()),
        "mutation_state": str(fields.get("mutation_state") or "MUTATION_UNKNOWN"),
        "failure_class": str(fields.get("failure_class") or "NONE"),
        "timestamps": timestamps,
        "raw_backend_receipt_pointer": fields.get("raw_backend_receipt_pointer") or "",
        # Optional C36 fields: absent by default (C35 byte-identical).
        "host_attestation": fields.get("host_attestation"),
        "dispatch_id": fields.get("dispatch_id") or "",
    }


def _validate_text(value: str, field_name: str, max_length: int = 256) -> str:
    text = str(value or "")
    if len(text) > max_length:
        raise RoleReceiptError("RECEIPT_FIELD_TOO_LONG", {"field": field_name})
    return text


def _validate_hash(value: str, field_name: str) -> str:
    text = str(value or "").strip()
    if not re.fullmatch(r"[0-9a-fA-F]{64}", text):
        raise RoleReceiptError("RECEIPT_HASH_FIELD_INVALID", {"field": field_name})
    return text.lower()


class RoleExecutionReceipt:
    """Normalized role execution evidence. Validation is intentionally
    explicit: unknown mutation/verification states raise only when the
    receipt is claimed as verified (verifier layer enforces it)."""

    def __init__(self, raw: Mapping[str, Any]) -> None:
        raw = dict(raw)
        if str(raw.get("schema", "")) != ROLE_RECEIPT_SCHEMA:
            raise RoleReceiptError("RECEIPT_SCHEMA_MISMATCH", {"schema": str(raw.get("schema", ""))})
        self.role_id = _validate_text(raw.get("role_id") or "", "role_id", 128)
        self.role_spec_hash = _validate_hash(raw.get("role_spec_hash") or "", "role_spec_hash")
        self.goal_id = _validate_text(raw.get("goal_id") or "", "goal_id")
        self.task_id = _validate_text(raw.get("task_id") or "", "task_id")
        self.project_binding = _validate_text(raw.get("project_binding") or "", "project_binding")
        self.environment_binding = _validate_text(
            raw.get("environment_binding") or "LOCAL_PROJECT", "environment_binding", 128)
        self.context_digest = _validate_hash(raw.get("context_digest") or "", "context_digest")
        self.permission_profile = tuple(str(item) for item in (raw.get("permission_profile") or ()))
        self.permission_profile_fingerprint = _validate_hash(
            raw.get("permission_profile_fingerprint") or "", "permission_profile_fingerprint")
        self.request_fingerprint = _validate_hash(raw.get("request_fingerprint") or "", "request_fingerprint")
        # The task-contract fingerprint bound to the dispatched request —
        # the verifier uses it to cross-check the backend result's own
        # request fingerprint (C30 task-binding semantics).
        # Optional task-binding fingerprint: an absent value is allowed
        # (the verifier then fails closed on any backend fingerprint
        # cross-check) — validation only applies to declared values.
        task_fp = str(raw.get("task_fingerprint") or "").strip()
        self.task_fingerprint = (_validate_hash(task_fp, "task_fingerprint")
                                 if task_fp else "")
        self.requested_target = _validate_text(raw.get("requested_target") or "", "requested_target", 128)
        self.observed_target = _validate_text(raw.get("observed_target") or "", "observed_target", 128)
        self.target_attestation_status = _validate_text(
            raw.get("target_attestation_status") or "REQUESTED_ONLY",
            "target_attestation_status", 64)
        self.target_fingerprint = _validate_hash(raw.get("target_fingerprint") or "", "target_fingerprint")
        self.execution_status = _validate_text(raw.get("execution_status") or "UNKNOWN", "execution_status", 64)
        if self.execution_status not in EXECUTION_STATUSES:
            raise RoleReceiptError("RECEIPT_EXECUTION_STATUS_INVALID", {"value": self.execution_status})
        self.output_pointers = tuple(str(item) for item in (raw.get("output_pointers") or ()))
        self.artifact_pointers = tuple(str(item) for item in (raw.get("artifact_pointers") or ()))
        self.evidence_pointers = tuple(str(item) for item in (raw.get("evidence_pointers") or ()))
        self.verifier_result = _validate_text(raw.get("verifier_result") or "UNKNOWN", "verifier_result", 64)
        if self.verifier_result not in VERIFICATION_STATUSES:
            raise RoleReceiptError("RECEIPT_VERIFICATION_STATUS_INVALID", {"value": self.verifier_result})
        self.verifier_reasons = tuple(str(item) for item in (raw.get("verifier_reasons") or ()))
        self.mutation_state = _validate_text(raw.get("mutation_state") or "MUTATION_UNKNOWN", "mutation_state", 64)
        if self.mutation_state not in MUTATION_STATES:
            raise RoleReceiptError("RECEIPT_MUTATION_STATE_INVALID", {"value": self.mutation_state})
        self.failure_class = _validate_text(raw.get("failure_class") or "NONE", "failure_class", 128)
        if self.failure_class not in FAILURE_CLASSES:
            raise RoleReceiptError("RECEIPT_FAILURE_CLASS_INVALID", {"value": self.failure_class})
        timestamps = dict(raw.get("timestamps") or {})
        for key in TIMESTAMP_FIELDS:
            if key not in timestamps:
                timestamps[key] = "UNKNOWN"
            else:
                timestamps[key] = str(timestamps[key])[:128]
        self.timestamps = timestamps
        self.raw_backend_receipt_pointer = _validate_text(
            raw.get("raw_backend_receipt_pointer") or "", "raw_backend_receipt_pointer", 512)
        # Optional C36 fields (declared-only validation, fail closed
        # when a value IS declared):
        host_attestation_value = raw.get("host_attestation")
        if host_attestation_value is not None:
            from .host_attestation import HostAttestationRecord
            if not isinstance(host_attestation_value, dict):
                raise RoleReceiptError("RECEIPT_HOST_ATTESTATION_NOT_A_MAPPING", {})
            self.host_attestation = HostAttestationRecord.from_mapping(
                host_attestation_value).to_dict()
        else:
            self.host_attestation = None
        self.dispatch_id = _validate_text(
            raw.get("dispatch_id") or "", "dispatch_id", 128)

    def to_dict(self) -> dict[str, Any]:
        return role_receipt_to_dict(self)
