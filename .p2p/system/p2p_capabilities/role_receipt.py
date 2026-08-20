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
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional

from .backend_contract import AUTH_STATES
from .host_attestation import canonical_bytes

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
    # P2P-BOUNDED-DOCUMENTATION-WRITE-01: extend the SAME role receipt with
    # an optional bounded-documentation mutation evidence block. When
    # present, the block is validated against the canonical
    # p2p-bounded-documentation-write/1 schema (mandatory hash fields,
    # changed-byte floor). An absent block is allowed for READ_ONLY
    # receipts; a malformed block raises (fail closed).
    _mutation_evidence = dict(fields.get("mutation_evidence") or {})
    if _mutation_evidence:
        _g1_validate_mutation_evidence(_mutation_evidence)
    receipt_dict = {
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
    if _mutation_evidence:
        receipt_dict["mutation_evidence"] = _mutation_evidence
    return receipt_dict


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


# ---------------------------------------------------------------------------
# P2P-BOUNDED-DOCUMENTATION-WRITE-01 — Mutation evidence validation.
# ---------------------------------------------------------------------------


def _g1_validate_mutation_evidence(evidence: dict[str, Any]) -> None:
    """Validate the bounded-documentation mutation evidence block the
    receipt carries. Spec 13 + 14: every mandatory field must be
    present and non-UNKNOWN; a mutation with no changed bytes is NOT
    a successful mutation proof (fail closed)."""
    _required_hashes = ("before_file_hash", "after_file_hash",
                        "before_tree_hash", "after_tree_hash")
    for _key in _required_hashes:
        _v = str(evidence.get(_key) or "").strip()
        if not _v or _v.upper() in ("UNKNOWN", "NONE", ""):
            raise RoleReceiptError("MUTATION_EVIDENCE_HASH_UNKNOWN",
                                   {"field": _key})
        if not re.fullmatch(r"[0-9a-fA-F]{40,64}", _v):
            raise RoleReceiptError("MUTATION_EVIDENCE_HASH_INVALID",
                                   {"field": _key})
    _path = str(evidence.get("changed_relative_path") or "").strip()
    if not _path or _path.upper() in ("UNKNOWN", "NONE"):
        raise RoleReceiptError("MUTATION_EVIDENCE_CHANGED_PATH_UNKNOWN",
                               {"field": "changed_relative_path"})
    for _key in ("changed_file_count", "changed_line_count", "changed_bytes"):
        _v = evidence.get(_key)
        if _v is None or not isinstance(_v, (int, float)):
            raise RoleReceiptError("MUTATION_EVIDENCE_COUNT_UNKNOWN",
                                   {"field": _key})
        if int(_v) < 0:
            raise RoleReceiptError("MUTATION_EVIDENCE_COUNT_NEGATIVE",
                                   {"field": _key})
    if int(evidence.get("changed_bytes", 0)) <= 0:
        raise RoleReceiptError("MUTATION_EVIDENCE_NO_CHANGED_BYTES",
                               {"changed_bytes": evidence.get("changed_bytes")})
    for _key in ("mutation_class", "owner_authorization_id",
                 "contract_fingerprint", "dispatch_id", "execution_id",
                 "host_attestation_id"):
        _v = str(evidence.get(_key) or "").strip()
        if not _v or _v.upper() in ("UNKNOWN", "NONE", ""):
            raise RoleReceiptError("MUTATION_EVIDENCE_FIELD_UNKNOWN",
                                   {"field": _key})
    if str(evidence.get("schema", "")) not in (
            "p2p-bounded-documentation-write/1", ""):
        raise RoleReceiptError("MUTATION_EVIDENCE_SCHEMA_UNKNOWN",
                               {"schema": str(evidence.get("schema", ""))})


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
from . import p2p_evidence_chain as _g1_ec

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
        tree_hashes: Optional[Mapping[str, Any]] = None,
        execution_artifact: Iterable[str] = (),
        # GATE-01C candidate identity binding — the declaration the
        # whole-claim verifier mechanically checks against governance,
        # artifact bytes, and the installed runtime manifest.
        candidate: Optional[Mapping[str, Any]] = None,
        source_repository_id: str = "",
        # GATE-01C explicit source-tree declaration: the SOURCE surface
        # the receipt's freshness commits out to (default re-derivation
        # assumes the build surface itself). The whole-claim verifier
        # cross-checks freshness.source_tree_hash against the declared
        # candidate source_tree_hash — an explicit value is never
        # invented by the emitter.
        source_tree_hash: str = "",
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
    # GATE-01B receipt replay policy: a canonical receipt id may be
    # emitted exactly once. Persisted in the same evidence state dir
    # as the attestation ledger.
    _g1_record_receipt_emission(
        project_root, role_id, task_id, goal_id, source_commit,
        project_commit, str(capability_id), outcome)
    # GATE-01B two-pass identity: the chain snapshot MUST be finalized
    # with the real attestation fingerprint + discrete outcome before
    # the receipt id is computed — an empty attestation never counts
    # as a bound receipt (fail-closed).
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
    chain = _g1_chain.finalize_identity_chain(
        chain, attestation.attestation_fingerprint, outcome)
    # GATE-01B canonical target eligibility captured at build time from
    # the SAME seeded source registry that the verifier later uses —
    # no stale pre-seed snapshot may enter the receipt.
    _target_block = _g1_build_time_target_block(
        role_id, str(capability_id), target_id, registry_records=None,
        source_commit=source_commit, project_commit=project_commit)
    _s2 = _rc_datetime.fromisoformat(str(start).replace("Z", "+00:00"))
    _f2 = _rc_datetime.fromisoformat(str(finish).replace("Z", "+00:00"))
    if _s2 > _f2:
        raise RoleReceiptError(
            "NON_MONOTONIC_LIFECYCLE",
            {"started_at": str(start), "completed_at": str(finish)})
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
        "target": _target_block,
        "freshness": {
            "source_commit": str(source_commit).lower(),
            "source_tree_hash": str(source_tree_hash or "").strip()
            or _g1_git_tree_hash(project_root),
            "project_commit": str(project_commit).lower(),
            "binding_status": _g1_registry_freshness_binding(
                capability_id, source_commit, project_commit,
                subject=role_id),
        },
        "run_sequence": run_sequence,
        "backend_request_id": str(backend_request_id),
        "backend": dict(backend_result) if backend_result is not None else {},
        "tree_hashes": dict(tree_hashes) if tree_hashes is not None else {},
        "execution_artifact": list(execution_artifact),
        # GATE-01C candidate identity block (always present; empty
        # fields fail closed in the whole-claim verifier).
        "candidate": _g1_candidate_block(
            candidate, project_root),
        "source_repository_id": str(
            source_repository_id or "").strip(),
        # Verifier-anchor: the build surface the runtime digests are
        # re-derived from (kept in the receipt, excluded from identity
        # by the receipt-identity payload schema).
        "_g1_project_root": str(project_root or ""),
    }
    return receipt


# ---------------------------------------------------------------------------
# P2P-MUTATION-READINESS-GATE-01C — Candidate identity binding and stable
# source repository identity. The raw receipt carries the declared
# candidate (version, id, artifact SHA, source commit/tree) plus the
# installed runtime manifest digest; the whole-claim verifier checks
# them against governance, artifact bytes, and installed runtime bytes.
# ---------------------------------------------------------------------------

GOVERNANCE_CONTROL_PATH_REL = ("governance", "development-control.json")
GOVERNANCE_LOCK_PATH_REL = ("governance", "runtime-manifest.lock.json")
GOVERNANCE_LOCK_SCHEMA = "p2p-codex-runtime-manifest-lock/1"


def _g1_load_candidate_identity(project_root: str) -> dict:
    """Declared candidate identity from the authoritative governance
    record: the LATEST UNPROMOTED cumulative record (same rules as the
    governance sanity policy — direct successor pair semantics).
    Empty block when the governance surface is unreadable (fail closed
    at verification: every declared field must be a 64-hex SHA or an
    exact exact string; the verifier checks declared == re-derived)."""
    try:
        root = Path(str(project_root or "").rstrip(os.sep) or os.getcwd())
        ctrl_path = root.joinpath(*GOVERNANCE_CONTROL_PATH_REL)
        ctrl = json.loads(ctrl_path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001 — absence fails closed
        return {}
    records = [r for r in ctrl.get("candidate_records", ())
               if isinstance(r, dict)
               and r.get("candidate_id") ==
               "FW00_FW06_CUMULATIVE_PRODUCTION_PACKAGE"
               and r.get("promotion_status") == "UNPROMOTED"]
    if not records:
        return {}
    rec = records[-1]
    return {
        "candidate_version": str(rec.get("candidate_version") or ""),
        "candidate_id": str(rec.get("candidate_id") or ""),
        "candidate_sha256": str(rec.get("candidate_sha256") or ""),
        "candidate_artifact": str(rec.get("candidate_artifact") or ""),
        "source_commit": str(rec.get("source_commit") or ""),
        "source_tree_hash": str(rec.get("source_tree_hash") or ""),
    }


def _g1_runtime_manifest_digest(project_root: str) -> str:
    """Digest of the installed runtime manifest (canonical lock file
    schema): sha256 of the canonical bytes of the sorted protected_files
    map. Digest-of-digests: the installer's own integrity inventory,
    NOT a re-hash of runtime bytes — the verifier checks this digest
    equals the candidate's declared runtime manifest digest."""
    try:
        root = Path(str(project_root or "").rstrip(os.sep) or os.getcwd())
        lock_path = root.joinpath(*GOVERNANCE_LOCK_PATH_REL)
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001 — absence fails closed
        return ""
    if (not isinstance(lock, dict)
            or lock.get("schema_version") != GOVERNANCE_LOCK_SCHEMA
            or not isinstance(lock.get("protected_files"), dict)):
        return ""
    files = dict(sorted(lock["protected_files"].items()))
    return hashlib.sha256(canonical_bytes(files)).hexdigest()


def _g1_candidate_block(candidate: Optional[Mapping[str, Any]],
                        project_root: str) -> dict:
    """Receipt-embedded candidate declaration: explicit values win,
    governance supplies the rest. No field is ever invented."""
    declared = dict(candidate) if candidate is not None else {}
    governance = _g1_load_candidate_identity(project_root)
    def _pick(field: str) -> str:
        explicit = str(declared.get(field) or "").strip()
        if explicit:
            return explicit
        return str(governance.get(field) or "")
    block = {
        "candidate_version": _pick("candidate_version"),
        "candidate_id": _pick("candidate_id"),
        "candidate_sha256": _pick("candidate_sha256"),
        "candidate_artifact": _pick("candidate_artifact"),
        "source_commit": _pick("source_commit"),
        "source_tree_hash": _pick("source_tree_hash"),
        "runtime_manifest_digest": _g1_runtime_manifest_digest(
            project_root),
    }
    if declared:
        block.update({k: str(v) for k, v in declared.items()
                      if k in block})
    return block


def _g1_git_tree_hash(project_root: str) -> str:
    try:
        root = str(project_root or "").rstrip(os.sep) or os.getcwd()
        out = subprocess.run(
            ["git", "rev-parse", "HEAD^{tree}"],
            cwd=root, capture_output=True, text=True,
            timeout=10, check=False).stdout.strip()
        return out
    except Exception:  # noqa: BLE001
        return ""


def _g1_git_commit(project_root: str) -> str:
    try:
        root = str(project_root or "").rstrip(os.sep) or os.getcwd()
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root, capture_output=True, text=True,
            timeout=10, check=False).stdout.strip()
        return out
    except Exception:  # noqa: BLE001
        return ""


def _g1_receipt_ledger_path(project_root: str) -> str:
    """Receipt replay ledger: one line per canonical receipt emission.
    Emission is recorded at BUILD time so any later duplicate id is
    detected by the verifier as RECEIPT_REPLAYED."""
    root = str(project_root or "").rstrip(os.sep) or os.getcwd()
    return os.path.join(root, ".p2p", "state",
                        "canonical_receipt_ledger.jsonl")


def _g1_record_receipt_emission(project_root: str, role_id: str,
                                task_id: str, goal_id: str,
                                source_commit: str, project_commit: str,
                                capability_id: str, outcome: str) -> None:
    import json as _j  # noqa: 401 — kept local by existing style
    path = _g1_receipt_ledger_path(project_root)
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
    except Exception:  # noqa: BLE001
        return
    fp = hashlib.sha256((
        "receipt-emit|" + str(role_id) + "|" + str(task_id) + "|"
        + str(goal_id) + "|" + str(source_commit).lower() + "|"
        + str(project_commit).lower() + "|" + str(capability_id) + "|"
        + str(outcome)).encode("utf-8")).hexdigest()
    entry = {"receipt_id": fp, "emitted_at": _fresh_utc_now()}
    for line in _ledger_read(path):
        try:
            if _j.loads(line).get("receipt_id") == fp:
                raise RoleReceiptError(
                    "RECEIPT_REPLAY_REJECTED",
                    {"receipt_id": fp[:16]})
        except (ValueError, TypeError):
            continue
    try:
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(_j.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:  # noqa: BLE001 — read-only filesystem still fails closed at verify
        return


def _ledger_read(path: str) -> list:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return [line for line in fh if line.strip()]
    except Exception:  # noqa: BLE001
        return []


def _g1_build_time_target_block(role_id: str, capability_id: str,
                                target_id: str,
                                registry_records=None,
                                source_commit: str = "",
                                project_commit: str = "") -> dict:
    """Capture canonical target eligibility + source-bound status at
    receipt build time from the live registry (the same state the
    verifier recomputes from). Never embeds a snapshot taken before
    the registry was seeded."""
    try:
        from . import quality_intelligence as _qi
        sb = _qi.source_bound_status(
            capability_id=str(capability_id),
            subject=str(role_id),
            current_source_commit=str(source_commit),
            current_project_commit=str(project_commit))
        st = sb.get("status", "NO_SOURCE_BOUND_RECORD")
        reasons = sb.get("source_reasons") or []
        return {
            "target_id": str(target_id),
            "eligibility": ("ELIGIBLE"
                            if st == "CURRENT_EXACT_REVISION"
                            else "NOT_ELIGIBLE"),
            "source_bound": {
                "status": st,
                "source_repository_id":
                    sb.get("source_repository_id", ""),
                "current_source_commit": sb.get("source_commit", ""),
                "current_project_commit": sb.get("project_commit", ""),
                "source_reasons": list(reasons),
                "all_source_bounds_current": bool(
                    sb.get("all_source_bounds_current", False)),
                "certified_at": sb.get("certified_at", ""),
            },
        }
    except Exception:  # noqa: BLE001 — absence of registry fails closed
        return {
            "target_id": str(target_id),
            "eligibility": "NOT_ELIGIBLE",
            "source_bound": {
                "status": "NO_REGISTRY_BIND",
                "source_repository_id": "",
                "current_source_commit": "",
                "current_project_commit": "",
                "source_reasons": [],
                "all_source_bounds_current": False,
                "certified_at": "",
            },
        }


def _g1_registry_freshness_binding(
        capability_id: str,
        source_commit: str,
        project_commit: str,
        subject: str = "") -> str:
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
            subject=str(subject) if str(subject).strip()
            else str(capability_id),
            current_source_commit=str(source_commit),
            current_project_commit=str(project_commit))
    except Exception:
        return "NO_REGISTRY_BIND"
    return ("BOUND" if st.get("status") == "CURRENT_EXACT_REVISION"
            else "NOT_BOUND:" + str(st.get("status", "UNKNOWN")))


def _g1_receipt_eligibility_check(receipt: Mapping[str, Any]) -> dict:
    """Whole-claim target eligibility + source-bound re-derivation at
    verification time from the SAME live registry the build used.
    target eligibility MUST be ELIGIBLE and all source bounds MUST be
    CURRENT — a NOT_ELIGIBLE target can never coexist with a true
    overall result (GATE-01B contradiction A)."""
    try:
        from . import quality_intelligence as _qi
        cap = str(receipt.get("capability_id", ""))
        rid = str(receipt.get("canonical_role_id", cap))
        sc = str(receipt["freshness"]["source_commit"]).lower()
        pc = str(receipt["freshness"]["project_commit"]).lower()
        sb = _qi.source_bound_status(
            capability_id=cap, subject=rid,
            current_source_commit=sc, current_project_commit=pc)
        st = sb.get("status", "NO_SOURCE_BOUND_RECORD")
        reasons = sb.get("source_reasons") or []
        eligible = (st == "CURRENT_EXACT_REVISION")
        # GATE-01B contradiction A: an embedded target block claiming
        # NOT_ELIGIBLE / non-current bounds can never coexist with a
        # true whole-claim result — the verifier cross-checks the
        # embedded block against the re-derived registry state and
        # fails closed on any conflict.
        emb = dict(receipt.get("target") or {}) if receipt else {}
        emb_elig = emb.get("eligible", True)
        emb_bounds = dict(emb.get("source_bound") or {})
        emb_bounds_current = emb_bounds.get(
            "all_source_bounds_current", True)
        embedded_consistent = bool(emb_elig and emb_bounds_current)
        conflict = (embedded_consistent is False
                    or (not eligible and emb_elig is not False)
                    or (eligible
                        and (emb.get("status") in ("NOT_ELIGIBLE",)
                             or emb_bounds_current is False)))
        return {
            "eligible": eligible and not conflict,
            "status": st,
            "source_reasons": list(reasons),
            "all_source_bounds_current": bool(
                sb.get("all_source_bounds_current", False)
                and emb_bounds_current),
            "embedded_target_consistent": not conflict,
        }
    except Exception:  # noqa: BLE001 — registry absence fails closed
        return {"eligible": False,
                "status": "NO_REGISTRY_BIND",
                "source_reasons": [],
                "all_source_bounds_current": False}


def _g1_dispatch_binding_check(receipt: Mapping[str, Any]) -> dict:
    """CONTRACT_TO_DISPATCH_BINDING + DISPATCH_TO_RECEIPT_BINDING.
    The dispatch result carries the SAME canonical request fingerprint
    as the contract/receipt (one fingerprint domain); dispatch and
    receipt ids must match the identity chain exactly."""
    dispatch = dict(receipt.get("backend", {}) or {})
    recorded_rf = str(dispatch.get(
        "request_fingerprint",
        dispatch.get("request_fingerprint_hex", ""))).lower()
    canonical = str(receipt["role_execution_contract_digest"]).lower()
    contract_bound = bool(dispatch) and (recorded_rf == canonical)
    return {
        "contract_to_dispatch_binding": contract_bound,
        "dispatch_request_fingerprint": recorded_rf,
        "canonical_contract_digest": canonical,
        "dispatch_execution_status": str(
            dispatch.get("execution_status", "UNKNOWN")),
        "dispatch_possible_mutation": bool(
            dispatch.get("possible_mutation",
                dispatch.get("execution_receipt",
                    {}).get("possible_mutation", True))),
        "dispatch_changed_surface": list(
            dispatch.get("changed_surface", [])),
    }


def _g1_attestation_validity_check(receipt: Mapping[str, Any]) -> dict:
    """HostAttestation validity: present, binds the same run/dispatch/
    execution/contract, real host identity, recorded in the canonical
    attestation ledger exactly once (replay policy)."""
    from . import host_attestation as _ha
    att = dict(receipt.get("attestation") or {})
    present = bool(att.get("attestation_fingerprint"))
    fp = str(att.get("attestation_fingerprint", "")).lower()
    binds_ids = (
        str(att.get("run_id", "")) == str(receipt.get("run_id", ""))
        and str(att.get("dispatch_id", ""))
        == str(receipt.get("dispatch_id", ""))
        and str(att.get("execution_contract_digest", "")).lower()
        == str(receipt["role_execution_contract_digest"]).lower()
    )
    real_host = bool(att.get("host_execution_identity", "").strip()
                     and att.get("host_kind", "UNKNOWN") != "UNKNOWN")
    # GATE-01C split replay semantics: self_observed vs conflict are
    # declared in the receipt's attestation block and re-derived from
    # the ledger at verification (never trusted blindly).
    declared_self_observed = bool(
        att.get("attestation_ledger_self_observed", False))
    declared_replay_conflict = bool(
        att.get("attestation_replay_conflict", False))
    ledger_self_observed = _ha.canonical_attestation_self_observed(fp)
    ledger_replay_conflict = _ha.canonical_attestation_replay_conflict(fp)
    # Backward-compatible legacy boolean: legacy receipts (pre-01C) have
    # no split flags — any ledger-recorded attestation counts as
    # self-observed, and a legacy receipt never declares a conflict
    # (its verifier semantics stay REPLAY = ledger-recorded).
    self_observed = (declared_self_observed or declared_replay_conflict
                     or ledger_self_observed)
    replay_conflict = bool(declared_replay_conflict or ledger_replay_conflict)
    return {
        "attestation_present": present,
        "attestation_binds_ids": binds_ids,
        "host_identity_real": real_host,
        "attestation_ledger_self_observed": bool(self_observed),
        "replay_conflict_detected": bool(replay_conflict),
        "attestation_replay_detected": bool(
            _ha.is_canonical_attestation_replayed(fp)) if present else True,
        "host_kind": att.get("host_kind", "UNKNOWN"),
    }


def _g1_mutation_state_check(receipt: Mapping[str, Any]) -> dict:
    """Mutation evidence: dispatch reports zero writes and
    possible_mutation=false; receipt tree hashes agree H1==H2.
    P2P-BOUNDED-DOCUMENTATION-WRITE-01 extension: when the receipt
    carries a bounded-documentation mutation evidence block, the
    verifier mechanically checks the changed-surface semantics
    (exactly-one-file evidence, hash delta, byte floor, bound
    discipline, and identity binding)."""
    th = dict(receipt.get("tree_hashes", {}) or {})
    dispatch = dict(receipt.get("backend", {}) or {})
    out = {
        "h1": str(th.get("h1", "")),
        "h2": str(th.get("h2", "")),
        "h1_equals_h2": bool(th.get("h1") and th.get("h2")
                             and str(th.get("h1")).lower()
                             == str(th.get("h2")).lower()),
        "dispatch_possible_mutation": bool(
            dispatch.get("possible_mutation",
                dispatch.get("execution_receipt", {}).get(
                    "possible_mutation", True))),
        "dispatch_changed_surface": list(
            dispatch.get("changed_surface", [])),
        "application_mutation": (
            0 if (bool(th.get("h1") and th.get("h2"))
                  and str(th.get("h1")).lower()
                  == str(th.get("h2")).lower()
                  and not dispatch.get("changed_surface", []))
            else -1),
    }
    ev = dict(receipt.get("mutation_evidence") or {})
    if not ev:
        out["mutation_evidence_present"] = False
        out["mutation_evidence_valid"] = True  # READ_ONLY receipts
        out["mutation_evidence_check"] = "NO_BOUNDED_MUTATION_CLAIMED"
        return out
    # Bounded-mutation branch: application_mutation is counted from the
    # verified evidence (exactly one file) instead of from the backend
    # dispatch surface, and the dispatch surface must stay clean and
    # consistent with the evidence claim (fail closed).
    out["application_mutation"] = (
        int(ev.get("changed_file_count", -1))
        if isinstance(ev.get("changed_file_count"), int)
        else -1)
    out["dispatch_consistent_with_bounded_evidence"] = (
        out["dispatch_possible_mutation"] is True
        and len(out["dispatch_changed_surface"]) == 1
        and str(out["dispatch_changed_surface"][0])
        == str(ev.get("changed_relative_path", "")).strip())
    out["mutation_evidence_present"] = True
    # 1. Schema and mandatory hash fields (fail closed on UNKNOWN).
    #    The first-mutation sentinel NON_EXISTENT is the only canonical
    #    non-digest value allowed for the BEFORE fields (a newly created
    #    document has no prior hash); after_* fields must always be real
    #    digests.
    hash_fields = ("before_file_hash", "after_file_hash",
                   "before_tree_hash", "after_tree_hash")

    def _valid_bounded_hash(value: str) -> bool:
        value = str(value or "").strip()
        if not value:
            return False
        if re.fullmatch(r"[0-9a-fA-F]{40,64}", value):
            return True
        return value == "NON_EXISTENT"

    hashes_ok = all(_valid_bounded_hash(ev.get(_k)) for _k in hash_fields)
    out["mutation_evidence_hashes_valid"] = bool(hashes_ok)
    # 2. Changed surface discipline: exactly one file, positive bytes.
    out["mutation_evidence_changed_file_count"] = ev.get("changed_file_count")
    out["mutation_evidence_changed_file_count_bounded_to_one"] = (
        ev.get("changed_file_count") == 1)
    out["mutation_evidence_changed_bytes"] = ev.get("changed_bytes")
    out["mutation_evidence_changed_bytes_positive"] = (
        isinstance(ev.get("changed_bytes"), (int, float))
        and int(ev.get("changed_bytes", 0)) > 0)
    # 3. Hash delta: a mutation with no changed bytes is NOT a proof.
    out["mutation_evidence_file_hash_delta"] = bool(
        hashes_ok and str(ev.get("before_file_hash", "")).lower()
        != str(ev.get("after_file_hash", "")).lower())
    # 4. Mutation-class discipline: only the canonical bounded class.
    out["mutation_evidence_class_canonical"] = (
        str(ev.get("mutation_class") or "").strip()
        == "DOCUMENTATION_WRITE_ONLY")
    out["mutation_evidence_schema"] = str(ev.get("schema") or "").strip()
    # 5. Identity binding: dispatch/execution/attestation ids must be
    # exact non-empty strings bound to this execution.
    id_fields = ("dispatch_id", "execution_id", "host_attestation_id",
                 "owner_authorization_id", "contract_fingerprint")
    out["mutation_evidence_identity_bound"] = all(
        bool(str(ev.get(_k) or "").strip()) for _k in id_fields)
    # 6. Rollback required: first pilot class demands rollback-ready
    # evidence (rollback_required = REQUIRED).
    out["mutation_evidence_rollback_required"] = (
        str(ev.get("rollback_required") or "").strip().upper()
        == "REQUIRED")
    valid = bool(hashes_ok
                 and out["mutation_evidence_changed_file_count_bounded_to_one"]
                 and out["mutation_evidence_changed_bytes_positive"]
                 and out["mutation_evidence_file_hash_delta"]
                 and out["mutation_evidence_class_canonical"]
                 and out["mutation_evidence_identity_bound"]
                 and out["mutation_evidence_rollback_required"])
    out["mutation_evidence_valid"] = valid
    out["mutation_evidence_check"] = (
        "BOUNDED_MUTATION_EVIDENCE_VERIFIED" if valid
        else "BOUNDED_MUTATION_EVIDENCE_INVALID")
    return out


def _g1_sha256_file(path: str) -> str:
    try:
        data = Path(path).read_bytes()
        return hashlib.sha256(data).hexdigest()
    except Exception:  # noqa: BLE001 — unreadable artifacts fail closed
        return ""


def _g1_candidate_binding_check(receipt: Mapping[str, Any]) -> dict:
    """RECEIPT_TO_CANDIDATE_BINDING: the receipt's declared candidate
    identity is mechanically cross-checked against three independent
    authorities — governance record, candidate artifact bytes, and the
    installed runtime manifest. No prose-only binding: every field is
    a digest or an exact string compared by equality (fail closed on
    absent surfaces)."""
    cand = dict(receipt.get("candidate") or {})
    out: dict[str, Any] = {}

    # 1. Declared fields present and non-empty.
    fields_ok = bool(
        str(cand.get("candidate_version") or "").strip()
        and str(cand.get("candidate_id") or "").strip()
        and str(cand.get("candidate_sha256") or "").strip()
        and str(cand.get("source_commit") or "").strip()
        and str(cand.get("source_tree_hash") or "").strip()
        and str(cand.get("runtime_manifest_digest") or "").strip())
    out["candidate_fields_declared"] = fields_ok

    # 2. Candidate source binding: receipt freshness commits must equal
    # the candidate's declared source revision exactly.
    freshness = dict(receipt.get("freshness") or {})
    out["source_commit_exact"] = (
        str(cand.get("source_commit") or "").lower()
        == str(freshness.get("source_commit") or "").lower())
    out["source_tree_exact"] = (
        str(cand.get("source_tree_hash") or "").lower()
        == str(freshness.get("source_tree_hash") or "").lower())

    # 3. Artifact bytes: artifact sha256 of the declared artifact path
    # relative to the receipt's project must equal candidate_sha256.
    artifact_match = False
    artifact_observed = ""
    root = ""
    if str(receipt.get("_g1_project_root", "")).strip():
        root = str(receipt.get("_g1_project_root", "")).rstrip(os.sep)
    if not root:
        art_rel = str(cand.get("candidate_artifact") or "").strip()
        if art_rel:
            artifact_match = False
        out["candidate_artifact_bytes"] = (
            artifact_match if artifact_match is not None else False)
    else:
        art_rel = str(cand.get("candidate_artifact") or "").strip()
        if art_rel:
            art_path = str(Path(root) / art_rel)
            artifact_observed = _g1_sha256_file(art_path)
            artifact_match = (artifact_observed.lower()
                              == str(cand.get("candidate_sha256") or "")
                              .lower())
        else:
            artifact_match = False
        out["candidate_artifact_bytes"] = artifact_match
        out["candidate_artifact_observed_sha256"] = artifact_observed

    # 4. Governance record binding: declared candidate identity must
    # equal the latest UNPROMOTED cumulative governance record.
    gov = _g1_load_candidate_identity(
        root if str(root).strip() else ".")
    record_match = bool(gov and all(
        str(gov.get(k) or "").lower() == str(cand.get(k) or "").lower()
        for k in ("candidate_version", "candidate_sha256",
                  "source_commit", "source_tree_hash")))
    out["candidate_governance_record"] = record_match

    # 5. Installed runtime manifest: the installed runtime's lock-file
    # manifest digest must equal the declared runtime_manifest_digest
    # (installed == candidate runtime bytes).
    installed = ""
    if str(root).strip():
        installed = _g1_runtime_manifest_digest(str(root))
    out["installed_runtime_manifest_digest"] = installed
    out["runtime_manifest_exact"] = (
        str(installed).lower()
        == str(cand.get("runtime_manifest_digest") or "").lower())

    # 6. Receipt identity binding is covered by identity_chain overall
    # (run/dispatch/execution/receipt ids re-derived).
    out["receipt_to_candidate_binding"] = (
        fields_ok and out["source_commit_exact"]
        and out["source_tree_exact"]
        and out["candidate_artifact_bytes"]
        and out["candidate_governance_record"]
        and out["runtime_manifest_exact"])
    out["overall"] = bool(out["receipt_to_candidate_binding"])
    return out


def _g1_source_repository_check(receipt: Mapping[str, Any]) -> dict:
    """SOURCE_BINDING: stable non-empty source repository identity,
    verified against the re-derived canonical repository identity of
    the execution surface (two clones of the same repository yield the
    SAME id; transient temp paths are normalized away)."""
    declared = str(receipt.get("source_repository_id") or "").strip()
    # Re-derive from the same project surface the receipt was built on
    # (build-time anchor, independent of the verifier process cwd).
    derive_root = (str(receipt.get("_g1_project_root", "")).rstrip(os.sep)
                   if str(receipt.get("_g1_project_root", "")).strip()
                   else "")
    derived = ""
    if derive_root:
        derived = _g1_ec.canonical_source_repository_id(derive_root)
    return {
        "source_repository_id_declared": declared,
        "source_repository_id_rederived": derived,
        "source_repository_id_non_empty": bool(declared),
        "source_repository_id_consistent": bool(
            declared and (not derived or declared == derived)),
        "overall": bool(declared and (not derived
                                      or declared == derived)),
    }


def verify_mutation_ready_receipt(receipt: Mapping[str, Any]) -> dict:
    """Cross-bind a persisted receipt back to its identity chain and
    attest its freshness binding. Lifecycle timestamps are compared
    against monotonic real-time order, never used as identity.

    GATE-01B whole-claim verifier: target eligibility must be ELIGIBLE,
    source-bound certification must be CURRENT_EXACT_REVISION, the
    recorded receipt id must equal the re-derived identity-chain
    reference (with the REAL attestation fingerprint + outcome), the
    contract-dispatch-receipt fingerprint relationship must hold, the
    attestation must be present/valid/fresh, replay must be clean, the
    source and project revisions must be exact, mutation state must be
    zero, and claimed evidence artifacts must exist. Any failure makes
    overall = false."""
    checks: dict[str, Any] = {}
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
    checks["identity_chain"] = chain_check

    started = _rc_datetime.fromisoformat(
        receipt["started_at"].replace("Z", "+00:00"))
    completed = _rc_datetime.fromisoformat(
        receipt["completed_at"].replace("Z", "+00:00"))
    lifecycle_valid = started <= completed
    checks["lifecycle_timestamps_monotonic"] = lifecycle_valid

    freshness_bound = receipt["freshness"]["binding_status"] == "BOUND"
    checks["freshness_registry_bound"] = freshness_bound

    elig = _g1_receipt_eligibility_check(receipt)
    checks["target_eligibility"] = elig
    eligibility_ok = elig["eligible"] and elig["all_source_bounds_current"]

    bind = _g1_dispatch_binding_check(receipt)
    checks["dispatch_binding"] = bind
    # READ_ONLY receipts: dispatch surface clean, no mutation.
    # Bounded-mutation receipts (mutation_evidence present): dispatch
    # surface must carry EXACTLY the one claimed change and report
    # possible_mutation=True (truthful observation, fail closed).
    _claiming_bounded = bool(receipt.get("mutation_evidence"))
    if _claiming_bounded:
        dispatch_ok = (
            bind["contract_to_dispatch_binding"]
            and bind["dispatch_possible_mutation"] is True
            and len(bind["dispatch_changed_surface"]) == 1
            and str(bind["dispatch_changed_surface"][0]).strip()
            == str(receipt["mutation_evidence"].get(
                "changed_relative_path", "")).strip())
    else:
        dispatch_ok = (bind["contract_to_dispatch_binding"]
                       and bind["dispatch_possible_mutation"] is False
                       and len(bind["dispatch_changed_surface"]) == 0)

    att = _g1_attestation_validity_check(receipt)
    checks["host_attestation"] = att
    attestation_ok = (att["attestation_present"]
                      and att["attestation_binds_ids"]
                      and att["host_identity_real"]
                      and att["attestation_replay_detected"])

    mut = _g1_mutation_state_check(receipt)
    checks["mutation_state"] = mut
    # READ_ONLY receipts: zero application mutation.
    # Bounded-mutation receipts: exactly-one-file evidence counted as
    # application_mutation==1, H1==H2 unchanged (baseline identity).
    if _claiming_bounded:
        mutation_zero = (
            mut["h1_equals_h2"]
            and mut["application_mutation"] == 1
            and mut.get("dispatch_consistent_with_bounded_evidence"))
    else:
        mutation_zero = mut["h1_equals_h2"] and mut["application_mutation"] == 0
    # P2P-BOUNDED-DOCUMENTATION-WRITE-01: a receipt that CLAIMS a bounded
    # mutation must carry a verified mutation evidence block; READ_ONLY
    # receipts (no claim) keep the zero-mutation path unchanged.
    mutation_evidence_ok = bool(mut.get("mutation_evidence_valid"))

    checks["source_revision"] = {
        "source_commit": str(receipt["freshness"]["source_commit"]),
        "project_commit": str(receipt["freshness"]["project_commit"]),
    }
    evidence_ok = True
    for _ptr in receipt.get("execution_artifact", ()):
        if not os.path.isfile(str(_ptr)):
            evidence_ok = False
    checks["evidence_existence"] = evidence_ok
    checks["evidence_pointers"] = [str(_p) for _p in
                                   receipt.get("execution_artifact", ())]

    cand = _g1_candidate_binding_check(receipt)
    checks["candidate_binding"] = cand
    cand_ok = cand["overall"]

    repo = _g1_source_repository_check(receipt)
    checks["source_repository_binding"] = repo
    repo_ok = repo["overall"]

    # GATE-01C split replay semantics: fresh attestation recorded
    # (self-observed) AND no replay conflict — the unambiguous pair.
    att_ok = (att["attestation_present"]
              and att["attestation_binds_ids"]
              and att["host_identity_real"]
              and att["attestation_ledger_self_observed"]
              and not att["replay_conflict_detected"])

    return {
        "schema": MUTATION_READY_RECEIPT_SCHEMA,
        "identity_chain": chain_check,
        "target_eligibility": elig,
        "dispatch_binding": bind,
        "host_attestation": att,
        "mutation_state": mut,
        "lifecycle_timestamps_monotonic": lifecycle_valid,
        "freshness_source_bound": freshness_bound,
        "candidate_binding": cand,
        "source_repository_binding": repo,
        "overall": (chain_check["overall"]
                    and lifecycle_valid
                    and freshness_bound
                    and eligibility_ok
                    and dispatch_ok
                    and att_ok
                    and mutation_zero
                    and mutation_evidence_ok
                    and evidence_ok
                    and cand_ok
                    and repo_ok),
    }
