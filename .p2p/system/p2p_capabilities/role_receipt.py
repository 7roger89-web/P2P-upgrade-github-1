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
    return {
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

    def to_dict(self) -> dict[str, Any]:
        return role_receipt_to_dict(self)

# ---------------------------------------------------------------------------
# P2P-MUTATION-READINESS-GATE-01 — Fresh real-timestamp, evidence-bound
# role receipts, plus a mutation-ready receipt builder that wires the
# identity chain (p2p_evidence_chain) and the canonical host attestation
# (host_attestation.make_canonical_host_attestation) into one receipt.
# Timestamps are real UTC wall-clock from the live clock, never
# placeholders; lifecycle evidence is lifecycle evidence, never identity.
# ---------------------------------------------------------------------------

from datetime import datetime as _rc_datetime
from datetime import timezone as _rc_timezone

from .host_attestation import make_canonical_host_attestation
from . import p2p_evidence_chain as _g1_chain

RECEIPT_UTC_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

MUTATION_READY_RECEIPT_SCHEMA = "p2p-role-receipt/1"


def _fresh_utc_now() -> str:
    """Real wall-clock UTC timestamp at second precision.
    Never UNKNOWN, never a placeholder."""
    return _rc_datetime.now(_rc_timezone.utc).strftime(RECEIPT_UTC_FORMAT)


def gate01_receipt_identity(
        *,
        identity_chain: Mapping[str, Any],
        outcome: str,
        started_at: str,
        completed_at: str,
        attestation_fingerprint: str,
        execution_status: str = "SUCCEEDED",
        verification_status: str = "VERIFIED",
) -> str:
    """Deterministic receipt identity bound to the identity chain, the
    canonical contract digest, the host attestation, and the discrete
    OUTCOME. Lifecycle timestamps are lifecycle EVIDENCE — they are
    carried in the receipt but never contribute to its identity (wall-
    clock must not be identity: two fresh emissions of the same
    execution share one canonical receipt id; ledger + attestation
    replay detection handle reuse policy)."""
    payload = {
        "schema": MUTATION_READY_RECEIPT_SCHEMA,
        "execution_id": identity_chain["execution_id"],
        "contract_digest": identity_chain["role_execution_contract_digest"],
        "request_fingerprint": identity_chain["request_fingerprint"],
        "attestation_fingerprint": str(attestation_fingerprint),
        "outcome": str(outcome),
    }
    import hashlib as _g1_h
    from .host_attestation import canonical_bytes
    return _g1_h.sha256(canonical_bytes(payload)).hexdigest()


def build_mutation_ready_receipt(
        *,
        role_id: str,
        capability_id: str,
        task_id: str,
        goal_id: str,
        contract: Mapping[str, Any],
        target_id: str,
        backend_request_id: str,
        source_commit: str,
        project_commit: str,
        outcome: str,
        execution_status: str = "SUCCEEDED",
        verification_status: str = "VERIFIED",
        project_root: str = "",
        started_at: str = "",
        completed_at: str = "",
        run_sequence: int = 1,
        adapter_provider: str = "manus",
        adapter_model: str = "manus-models",
        adapter_harness: str = "manus-fw00-fw06-candidate",
        backend_result: Optional[Mapping[str, Any]] = None,
        host_metadata: str = "",
) -> dict:
    """Build a fresh role execution receipt bound to the single canonical
    contract digest, one identity chain, one real host attestation, and
    real UTC lifecycle timestamps.

    The receipt carries:
      - canonical chain ids (run/dispatch/execution/receipt id)
      - role_execution_contract_digest = the ONE request fingerprint domain
      - host attestation witness (fresh, ledger-recorded, replay-detected)
      - freshness source binding (source + project commit)
      - real UTC started_at / completed_at (lifecycle evidence)
      - backend result pass-through (usage evidence, request ids)
    """
    # Evidence-integrity: lifecycle timestamps are evidence, never
    # placeholders. Empty or UNKNOWN-ish placeholders fail closed.
    for _ts_name, _ts_value in (("started_at", started_at),
                                ("completed_at", completed_at)):
        _tv = str(_ts_value or "").strip()
        if not _tv:
            raise RoleReceiptError(
                "PLACEHOLDER_TIMESTAMP_REJECTED",
                {"field": _ts_name, "value": str(_ts_value)})
        if _tv.upper() in ("UNKNOWN", "PLACEHOLDER", ""):
            raise RoleReceiptError(
                "PLACEHOLDER_TIMESTAMP_REJECTED",
                {"field": _ts_name, "value": _tv})
        try:
            _rc_datetime.fromisoformat(_tv.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            raise RoleReceiptError(
                "PLACEHOLDER_TIMESTAMP_REJECTED",
                {"field": _ts_name, "value": _tv})
    start = started_at or _fresh_utc_now()
    finish = completed_at or _fresh_utc_now()
    _s = _rc_datetime.fromisoformat(str(start).replace("Z", "+00:00"))
    _f = _rc_datetime.fromisoformat(str(finish).replace("Z", "+00:00"))
    if _s > _f:
        raise RoleReceiptError(
            "NON_MONOTONIC_LIFECYCLE",
            {"started_at": str(start), "completed_at": str(finish)})
    chain = _g1_chain.build_identity_chain(
        goal_id=goal_id, task_id=task_id, role_id=role_id,
        contract=contract, target_id=target_id,
        backend_request_id=backend_request_id,
        source_commit=source_commit,
        project_commit=project_commit,
        run_sequence=run_sequence)
    attestation = make_canonical_host_attestation(
        adapter_id=target_id,
        run_id=chain["run_id"],
        dispatch_id=chain["dispatch_id"],
        execution_contract_digest=chain["role_execution_contract_digest"],
        project_root=project_root,
        provider=adapter_provider,
        model=adapter_model,
        harness=adapter_harness,
        attested_at=_fresh_utc_now(),
        host_metadata=host_metadata,
    )
    receipt = {
        "schema": MUTATION_READY_RECEIPT_SCHEMA,
        "role_receipt_id": gate01_receipt_identity(
            identity_chain=chain, outcome=outcome,
            started_at=start, completed_at=finish,
            attestation_fingerprint=attestation.attestation_fingerprint,
            execution_status=execution_status,
            verification_status=verification_status),
        "goal_id": goal_id,
        "task_id": task_id,
        "run_id": chain["run_id"],
        "dispatch_id": chain["dispatch_id"],
        "execution_id": chain["execution_id"],
        "canonical_role_id": role_id,
        "capability_id": str(capability_id),
        "role_execution_contract_digest":
            chain["role_execution_contract_digest"],
        "request_fingerprint": chain["request_fingerprint"],
        "target_id": target_id,
        "host_execution_identity": chain["host_execution_identity"],
        "outcome": outcome,
        "execution_status": execution_status,
        "verification_status": verification_status,
        "started_at": start,
        "completed_at": finish,
        "attestation": attestation.to_dict(),
        "attestation_fingerprint": attestation.attestation_fingerprint,
        "freshness": {
            "source_commit": str(source_commit).lower(),
            "project_commit": str(project_commit).lower(),
            "binding_status": _g1_registry_freshness_binding(
                capability_id, source_commit, project_commit),
        },
        "run_sequence": run_sequence,
        "backend_request_id": str(backend_request_id),
        "backend": dict(backend_result) if backend_result is not None else {},
    }
    return receipt


def _g1_registry_freshness_binding(
        capability_id: str,
        source_commit: str,
        project_commit: str) -> str:
    """Registry-anchored freshness: the receipt is only FRESHLY BOUND when
    the source registry carries a source-bound certification record for
    this capability whose commits match the runtime truth EXACTLY
    (CURRENT_EXACT_REVISION). Any stale or absent certification makes
    the receipt buildable but NOT freshness-bound — the verifier then
    fail-closes the whole chain."""
    try:
        from . import quality_intelligence as _qi
        st = _qi.source_bound_status(
            capability_id=str(capability_id),
            subject=str(capability_id),
            current_source_commit=str(source_commit),
            current_project_commit=str(project_commit))
    except Exception:
        return "NO_REGISTRY_BIND"
    return ("BOUND" if st.get("status") == "CURRENT_EXACT_REVISION"
            else "NOT_BOUND:" + str(st.get("status", "UNKNOWN")))


def verify_mutation_ready_receipt(receipt: Mapping[str, Any]) -> dict:
    """Cross-bind a persisted receipt back to its identity chain and
    attest its freshness binding. Lifecycle timestamps are compared
    against monotonic real-time order, never used as identity."""
    chain = receipt.get("run_id") and {
        "schema": _g1_chain.CHAIN_SCHEMA,
        "goal_id": receipt["goal_id"],
        "task_id": receipt["task_id"],
        "run_id": receipt["run_id"],
        "dispatch_id": receipt["dispatch_id"],
        "execution_id": receipt["execution_id"],
        "role_id": receipt["canonical_role_id"],
        "role_execution_contract_digest":
            receipt["role_execution_contract_digest"],
        "request_fingerprint": receipt["request_fingerprint"],
        "backend_request_id": str(receipt.get("backend_request_id",
            receipt.get("backend", {}).get("request_id", ""))),
        "target_id": receipt["target_id"],
        "host_execution_identity": receipt["host_execution_identity"],
        "role_receipt_id": receipt["role_receipt_id"],
        "attestation_fingerprint": str(receipt.get(
            "attestation_fingerprint", "")),
        "outcome": str(receipt.get("outcome", "")),
        "source_commit": receipt["freshness"]["source_commit"],
        "project_commit": receipt["freshness"]["project_commit"],
        "run_sequence": receipt["run_sequence"],
    }
    chain_check = _g1_chain.verify_identity_chain(chain)
    started = _rc_datetime.fromisoformat(
        receipt["started_at"].replace("Z", "+00:00"))
    completed = _rc_datetime.fromisoformat(
        receipt["completed_at"].replace("Z", "+00:00"))
    lifecycle_valid = started <= completed
    freshness_bound = receipt["freshness"]["binding_status"] == "BOUND"
    return {
        "schema": MUTATION_READY_RECEIPT_SCHEMA,
        "identity_chain": chain_check,
        "lifecycle_timestamps_monotonic": lifecycle_valid,
        "freshness_source_bound": freshness_bound,
        "overall": (chain_check["overall"]
                    and lifecycle_valid and freshness_bound),
    }
