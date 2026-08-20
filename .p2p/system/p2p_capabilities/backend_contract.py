"""P2P backend execution adapter conformance contract (C34).

Extends the C30 structured-headless / portable-execution seam
(host_executor.py) with the minimum surfaces a real execution backend
adapter must expose so the C33 AutoPilot core can run through it with
ZERO vendor-specific branching.

    ADAPTER_ID / ADAPTER_VERSION / HARNESS / PROVIDER / MODEL identity
    PROTOCOL / TOOLSET_CAPABILITIES / WORKSPACE / ENVIRONMENT binding
    AUTH_STATE / PERMISSION_PROFILE / HEALTH / FRESHNESS
    EXECUTE(task_contract) -> NORMALIZED_EVENTS / NORMALIZED_RESULT
    ARTIFACT_POINTERS / RECEIPT REQUEST BINDING
    CANCEL / INTERRUPT / USAGE evidence

Every field beyond the normalized result is either optional or MUST carry
an honest UNKNOWN / UNAVAILABLE value. An adapter MUST NOT invent a
concept that only its own backend possesses.

The normalized result reuses the C30 PortableExecutionReceipt vocabulary
(request_id, request_fingerprint (64-hex SHA-256), task_id,
host_adapter_class, execution_status, verification_status, error_class,
artifact_refs, evidence_refs, telemetry, possible_mutation) and adds a
bounded BackendExecutionResult envelope carrying started_at / finished_at,
exit status, output pointers, mutation surface, usage evidence,
auth_state_after, and a raw_backend_receipt_pointer.

RAW backend transcripts / message histories may be retained as OPTIONAL
execution evidence (pointers only). They MUST NEVER become authoritative
P2P state.

Authoritative registries/vocabularies reused:
    - host_executor: ERROR_CLASSES, _EXECUTION_STATUSES, _VERIFICATION_STATUSES,
      normalize_host_error, validate_binding, reconcile_receipt
    - task_state: single task authority; evidence.py: evidence statuses

Backend self-report ("DONE") is NOT task verification: the P2P verifier
(autopilot_verifier) decides.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

from .host_executor import (
    ERROR_CLASSES,
    PORTABLE_RECEIPT_SCHEMA,
    _EXECUTION_STATUSES,
    _VERIFICATION_STATUSES,
    normalize_host_error,
)

BACKEND_CONTRACT_SCHEMA = "p2p-backend-execution-contract/1"
BACKEND_RESULT_SCHEMA = "p2p-backend-execution-result/1"
BACKEND_STATE_FAMILIES = (
    "p2p-task-state/1",
    "p2p-task-event/1",
    "p2p-autopilot-goal/1",
    "p2p-goal-event/1",
    "p2p-autopilot-resume-point/1",
    BACKEND_RESULT_SCHEMA,
)

AUTH_STATES = ("UNKNOWN", "NO_CREDENTIALS", "CONFIGURED", "VALID", "INVALID", "EXPIRED")

EXECUTION_ERROR_CLASSES = (
    "AUTH_REQUIRED",
    "AUTH_INVALID",
    "RATE_LIMIT",
    "UNAVAILABLE",
    "TIMEOUT",
    "PERMISSION_DENIED",
    "CONTRACT_REJECTED",
) + ERROR_CLASSES

ADAPTER_STATES = (
    "ARCHITECTURALLY_COMPATIBLE",
    "ADAPTER_IMPLEMENTED",
    "ADAPTER_TESTED",
    "LIVE_CERTIFIED",
    "CURRENTLY_ELIGIBLE",
)

# ---------------------------------------------------------------------------
# C34 closure-reconciliation: capability-scoped certification.
#
# LIVE_CERTIFIED is NOT a blanket property of an adapter. It is always scoped
# to a bounded capability. A backend certified for a bounded, non-mutating,
# single-turn text task is NOT certified for code mutation, file-workspace
# operation, browser runtime, or long-horizon execution. Any scope without
# independent bounded evidence is UNKNOWN for that scope.
#
# The five-state chain is architectural, not declarative:
#   ARCHITECTURALLY_COMPATIBLE -> ADAPTER_IMPLEMENTED -> ADAPTER_TESTED ->
#   LIVE_CERTIFIED_FOR_CAPABILITY (per scope) ->
#   CURRENTLY_ELIGIBLE_FOR_TASK (task-gated; never pre-declared).
# An adapter must never claim CURRENTLY_ELIGIBLE before a task contract is
# bound to it; eligibility is evaluated against task requirements and
# capabilities at task-gate time (owner gate applies when a required
# capability is UNKNOWN).
# ---------------------------------------------------------------------------

# P2P-BOUNDED-DOCUMENTATION-WRITE-01A: explicit capability→execution-scope
# mapping table (registry-backed). The capability registry record is the
# canonical source (EXECUTION_SCOPE field); this module-level table is the
# second-tier data-driven fallback so the eligibility layer never
# synthesizes a mapping from unverified input. An unknown capability
# mapping is a hard BLOCK (fail-closed).
CAPABILITY_EXECUTION_SCOPE_MAP: dict[str, str] = {
    "bounded_documentation_write": "DOCUMENTATION_MUTATION_BOUNDED",
}

CERTIFICATION_SCOPES = (
    "SYNTHETIC_TEXT_EXECUTION",        # single-turn bounded text Q&A
    "API_TRANSPORT",                   # request/response transport works
    "NON_MUTATING_TASK",               # no filesystem/code mutation observed
    "FILE_WORKSPACE_OPERATION",        # file read/write in a task workspace
    "CODE_MUTATION",                   # code edit/generation execution
    "TEST_EXECUTION",                  # running test suites
    "BROWSER_RUNTIME",                 # browser automation
    "LONG_HORIZON_EXECUTION",          # multi-step / multi-wave autonomy
    "DOCUMENTATION_MUTATION_BOUNDED",  # P2P-BW01: bounded documentation write
)


@dataclass(frozen=True)
class BackendCapabilityCertification:
    """Per-scope certification record. Unknown scopes stay UNKNOWN."""

    adapter_id: str
    scope: str               # CERTIFICATION_SCOPES member
    status: str              # LIVE_CERTIFIED_FOR_CAPABILITY | UNKNOWN | NOT_TESTED
    evidence_pointers: tuple[str, ...] = ()
    certified_at: str | None = None

    def __post_init__(self) -> None:
        _limited_text(self.adapter_id, "adapter_id", 128)
        if self.scope not in CERTIFICATION_SCOPES:
            raise BackendContractError("CERTIFICATION_SCOPE_INVALID")
        if self.status not in ("LIVE_CERTIFIED_FOR_CAPABILITY", "UNKNOWN", "NOT_TESTED"):
            raise BackendContractError("CERTIFICATION_STATUS_INVALID")
        if not isinstance(self.evidence_pointers, tuple) or not all(
            isinstance(p, str) for p in self.evidence_pointers
        ):
            raise BackendContractError("CERTIFICATION_EVIDENCE_INVALID")

    def to_dict(self) -> dict[str, Any]:
        return {
            "adapter_id": self.adapter_id,
            "scope": self.scope,
            "status": self.status,
            "evidence_pointers": list(self.evidence_pointers),
            "certified_at": self.certified_at,
        }

_BACKEND_EXECUTION_STATUSES = _EXECUTION_STATUSES
_BACKEND_VERIFICATION_STATUSES = _VERIFICATION_STATUSES


def _hex64(value: str, field_name: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or not re.fullmatch(r"[0-9a-f]{64}", value):
        raise BackendContractError(f"{field_name}_INVALID")
    return value


def _limited_text(value: str | None, field_name: str, max_length: int = 256) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or len(value.strip()) == 0:
        raise BackendContractError(f"{field_name}_REQUIRED")
    if len(value) > max_length:
        raise BackendContractError(f"{field_name}_TOO_LONG")
    return value.strip()


class BackendContractError(Exception):
    """Contract violation inside a backend adapter envelope."""


@dataclass(frozen=True)
class BackendAdapterIdentity:
    """Static identity surface every conformant adapter must provide."""

    adapter_id: str
    adapter_version: str
    adapter_state: str  # ADAPTER_STATES member
    harness_identity: str | None = None
    provider_identity: str | None = None
    model_identity: str | None = None
    protocol: str | None = None
    toolset_capabilities: tuple[str, ...] = ()
    workspace_binding: str | None = None
    environment_binding: str | None = None

    def __post_init__(self) -> None:
        _limited_text(self.adapter_id, "adapter_id", 128)
        _limited_text(self.adapter_version, "adapter_version", 64)
        if self.adapter_state not in ADAPTER_STATES:
            raise BackendContractError("ADAPTER_STATE_INVALID")
        for name in ("harness_identity", "provider_identity", "model_identity",
                     "protocol", "workspace_binding", "environment_binding"):
            if getattr(self, name) is not None:
                _limited_text(getattr(self, name), name, 256)
        if not isinstance(self.toolset_capabilities, tuple) or not all(
            isinstance(cap, str) for cap in self.toolset_capabilities
        ):
            raise BackendContractError("TOOLSET_CAPABILITIES_MUST_BE_TUPLE")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": BACKEND_CONTRACT_SCHEMA,
            "adapter_id": self.adapter_id,
            "adapter_version": self.adapter_version,
            "adapter_state": self.adapter_state,
            "harness_identity": self.harness_identity,
            "provider_identity": self.provider_identity,
            "model_identity": self.model_identity,
            "protocol": self.protocol,
            "toolset_capabilities": list(self.toolset_capabilities),
            "workspace_binding": self.workspace_binding,
            "environment_binding": self.environment_binding,
        }

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "BackendAdapterIdentity":
        if not isinstance(raw, Mapping):
            raise BackendContractError("IDENTITY_MUST_BE_OBJECT")
        return cls(
            adapter_id=str(raw["adapter_id"]),
            adapter_version=str(raw.get("adapter_version", "0")),
            adapter_state=str(raw.get("adapter_state", "ARCHITECTURALLY_COMPATIBLE")).upper(),
            harness_identity=raw.get("harness_identity"),
            provider_identity=raw.get("provider_identity"),
            model_identity=raw.get("model_identity"),
            protocol=raw.get("protocol"),
            toolset_capabilities=tuple(raw.get("toolset_capabilities") or ()),
            workspace_binding=raw.get("workspace_binding"),
            environment_binding=raw.get("environment_binding"),
        )


@dataclass(frozen=True)
class AdapterHealthState:
    """Foreground health/availability observation. UNKNOWN fails closed."""

    healthy: bool | None = None  # None == UNKNOWN
    auth_state: str = "UNKNOWN"
    auth_state_after: str = "UNKNOWN"
    availability: str = "UNKNOWN"
    freshness: str = "UNKNOWN"
    last_observed_at: str | None = None

    def __post_init__(self) -> None:
        if self.auth_state not in AUTH_STATES:
            raise BackendContractError("AUTH_STATE_INVALID")
        if self.auth_state_after not in AUTH_STATES:
            raise BackendContractError("AUTH_STATE_AFTER_INVALID")
        if self.availability not in ("UNKNOWN", "AVAILABLE", "DEGRADED", "UNAVAILABLE"):
            raise BackendContractError("AVAILABILITY_INVALID")
        if self.freshness not in ("UNKNOWN", "CURRENT", "FRESH", "STALE"):
            raise BackendContractError("FRESHNESS_INVALID")
        if self.last_observed_at is not None:
            _limited_text(self.last_observed_at, "last_observed_at", 128)

    def usable(self) -> bool:
        """Honest availability gate: only explicit truth counts."""
        return self.healthy is True and self.auth_state in ("VALID", "CONFIGURED")


@dataclass(frozen=True)
class BackendExecutionResult:
    """Normalized P2P-side result produced by any conformant adapter.

    Mirrors PortableExecutionReceipt plus the C34 minimum conceptual result
    (started_at/finished_at, exit status, output pointers, mutation surface,
    usage evidence, auth_state_after, raw_backend_receipt_pointer).
    """

    request_id: str
    request_fingerprint_hex: str  # 64-hex, bound to task contract via C22/C30 semantics
    task_id: str
    goal_id: str
    adapter_id: str
    execution_status: str          # _EXECUTION_STATUSES
    verification_status: str       # _VERIFICATION_STATUSES (P2P verifier authority)
    started_at: str | None = None
    finished_at: str | None = None
    exit_status: str | None = None  # backend terminal status (exit code text)
    target_fingerprint: str | None = None
    output_pointers: tuple[str, ...] = ()
    artifact_pointers: tuple[str, ...] = ()
    mutation_surface: str | None = None  # e.g. workspace path / scope touched
    usage_evidence: Mapping[str, Any] = field(default_factory=dict)
    error_class: str | None = None
    auth_state_after: str = "UNKNOWN"
    raw_backend_receipt_pointer: str | None = None  # evidence pointer, NEVER authority
    possible_mutation: bool = False

    def __post_init__(self) -> None:
        _limited_text(self.request_id, "request_id", 128)
        object.__setattr__(self, "_request_fingerprint", _hex64(self.request_fingerprint_hex, "request_fingerprint"))
        _limited_text(self.task_id, "task_id", 256)
        _limited_text(self.goal_id, "goal_id", 256)
        _limited_text(self.adapter_id, "adapter_id", 128)
        if self.execution_status not in _EXECUTION_STATUSES:
            raise BackendContractError("EXECUTION_STATUS_INVALID")
        if self.verification_status not in _VERIFICATION_STATUSES:
            raise BackendContractError("VERIFICATION_STATUS_INVALID")
        for name in ("started_at", "finished_at", "exit_status", "target_fingerprint"):
            value = getattr(self, name)
            if value is not None:
                _limited_text(value, name, 128)
        if not isinstance(self.output_pointers, tuple) or not all(isinstance(p, str) for p in self.output_pointers):
            raise BackendContractError("OUTPUT_POINTERS_INVALID")
        if not isinstance(self.artifact_pointers, tuple) or not all(isinstance(p, str) for p in self.artifact_pointers):
            raise BackendContractError("ARTIFACT_POINTERS_INVALID")
        if not isinstance(self.mutation_surface, (str, type(None))):
            raise BackendContractError("MUTATION_SURFACE_INVALID")
        if self.mutation_surface is not None:
            _limited_text(self.mutation_surface, "mutation_surface", 512)
        if self.auth_state_after not in AUTH_STATES:
            raise BackendContractError("AUTH_STATE_AFTER_INVALID")
        if self.raw_backend_receipt_pointer is not None:
            _limited_text(self.raw_backend_receipt_pointer, "raw_backend_receipt_pointer", 512)
        if not isinstance(self.usage_evidence, Mapping):
            raise BackendContractError("USAGE_EVIDENCE_INVALID")
        if self.error_class is not None and self.error_class not in EXECUTION_ERROR_CLASSES:
            raise BackendContractError("ERROR_CLASS_INVALID")
        if not isinstance(self.possible_mutation, bool):
            raise BackendContractError("POSSIBLE_MUTATION_INVALID")

    @property
    def request_fingerprint(self) -> str:  # type: ignore[override]
        return self._request_fingerprint

    @property
    def completion_status(self) -> str:
        if self.execution_status == "SUCCEEDED" and self.verification_status == "VERIFIED":
            return "DONE"
        if self.execution_status == "BLOCKED":
            return "BLOCKED"
        if self.execution_status == "PARTIAL_MUTATION_UNKNOWN" or (
            self.possible_mutation and self.execution_status == "UNKNOWN"
        ):
            return "NEEDS_RECHECK"
        return "NOT_DONE"

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": BACKEND_RESULT_SCHEMA,
            "request_id": self.request_id,
            "request_fingerprint": self.request_fingerprint,
            "task_id": self.task_id,
            "goal_id": self.goal_id,
            "adapter_id": self.adapter_id,
            "execution_status": self.execution_status,
            "verification_status": self.verification_status,
            "completion_status": self.completion_status,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "exit_status": self.exit_status,
            "target_fingerprint": self.target_fingerprint,
            "output_pointers": list(self.output_pointers),
            "artifact_pointers": list(self.artifact_pointers),
            "mutation_surface": self.mutation_surface,
            "usage_evidence": json.loads(json.dumps(self.usage_evidence)),
            "error_class": self.error_class,
            "auth_state_after": self.auth_state_after,
            "raw_backend_receipt_pointer": self.raw_backend_receipt_pointer,
            "possible_mutation": self.possible_mutation,
        }

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "BackendExecutionResult":
        if not isinstance(raw, Mapping):
            raise BackendContractError("RESULT_MUST_BE_OBJECT")
        if str(raw.get("schema", "")) != BACKEND_RESULT_SCHEMA:
            raise BackendContractError("RESULT_SCHEMA_MISMATCH")
        return cls(
            request_id=str(raw["request_id"]),
            request_fingerprint_hex=str(raw["request_fingerprint"]),
            task_id=str(raw["task_id"]),
            goal_id=str(raw["goal_id"]),
            adapter_id=str(raw["adapter_id"]),
            execution_status=str(raw.get("execution_status", "UNKNOWN")).upper(),
            verification_status=str(raw.get("verification_status", "UNKNOWN")).upper(),
            started_at=raw.get("started_at"),
            finished_at=raw.get("finished_at"),
            exit_status=raw.get("exit_status"),
            target_fingerprint=raw.get("target_fingerprint"),
            output_pointers=tuple(raw.get("output_pointers") or ()),
            artifact_pointers=tuple(raw.get("artifact_pointers") or ()),
            mutation_surface=raw.get("mutation_surface"),
            usage_evidence=raw.get("usage_evidence") or {},
            error_class=raw.get("error_class"),
            auth_state_after=str(raw.get("auth_state_after", "UNKNOWN")).upper(),
            raw_backend_receipt_pointer=raw.get("raw_backend_receipt_pointer"),
            possible_mutation=bool(raw.get("possible_mutation", False)),
        )


def normalize_adapter_error(message: str, *, backend_error_tags: Iterable[str] = ()) -> str | None:
    """Map vendor-specific failure text into the P2P canonical error classes.

    Adapter-specific keyword precedence is applied first (only when the
    adapter knows its own vendor vocabulary), then the canonical
    normalize_host_error semantics. Returns None when nothing matches.
    UNKNOWN fails closed (caller treats None as UNKNOWN/EXECUTION_FAILED).
    """
    text = (str(message) or "").strip().lower()
    if not text:
        return None
    # C34: credential-absence is an auth-gating fact, not a crash — classify
    # it AUTH_REQUIRED / AUTH_INVALID BEFORE any generic fallback, so the
    # honest "no provider credentials" path reaches the auth gate.
    if any(token in text for token in ("no credentials", "no api key",
                                       "no anthropic", "no openai",
                                       "missing api", "not configured",
                                       "not found in", "credential")):
        return "AUTH_INVALID" if any(
            token in text for token in ("invalid", "expired", "401",
                                        "unauthorized", "denied", "403",
                                        "forbidden")) else "AUTH_REQUIRED"
    if any(token in text for token in ("invalid api key", "invalid token",
                                       "unauthorized", "401")):
        return "AUTH_INVALID"
    if any(token in text for token in ("access denied", "forbidden", "403",
                                       "permission")):
        return "PERMISSION_DENIED"
    if any(token in text for token in ("rate limit", "429", "too many requests",
                                       "throttl")):
        return "RATE_LIMIT"
    # Adapter-supplied vendor keywords decide the vendor-agnostic class of the
    # failure BEFORE the message text is inspected. Each keyword maps to a
    # single vendor-neutral class; the message then refines within that class.
    for tag in backend_error_tags:
        tag_lower = str(tag).strip().lower()
        if not tag_lower:
            continue
        if tag_lower in ("rate_limit", "ratelimit", "429", "too many requests", "quota"):
            return "RATE_LIMIT"
        if tag_lower in ("auth", "auth_required", "no_credentials", "credential"):
            return "AUTH_REQUIRED"
        if tag_lower in ("auth_invalid", "invalid_token", "bad_auth", "401", "unauthorized"):
            return "AUTH_INVALID"
        if tag_lower in ("permission", "denied", "forbidden", "403"):
            return "PERMISSION_DENIED"
        if tag_lower in ("cancelled", "canceled", "interrupt", "killed"):
            return "EXECUTION_INTERRUPTED"
        if tag_lower in ("timeout", "timed_out"):
            return "TIMEOUT"
        if tag_lower in ("unavailable", "unreachable", "connection_error"):
            return "UNAVAILABLE"
        if tag_lower in ("contract", "invalid_request", "rejected", "bad_request", "400"):
            return "CONTRACT_REJECTED"
        return "EXECUTION_FAILED"
    return normalize_host_error(message)


def verify_request_receipt_binding(
    result: BackendExecutionResult,
    *,
    expected_request_fingerprint: str,
    expected_task_id: str,
    expected_goal_id: str,
) -> dict[str, Any]:
    """Prove a receipt belongs to the intended task. NEVER blind-accept."""
    reasons: list[str] = []
    if result.request_fingerprint != expected_request_fingerprint:
        reasons.append("REQUEST_FINGERPRINT_MISMATCH")
    if result.task_id != expected_task_id:
        reasons.append("TASK_ID_MISMATCH")
    if result.goal_id != expected_goal_id:
        reasons.append("GOAL_ID_MISMATCH")
    if reasons:
        return {"status": "REJECTED", "reasons": reasons, "retry_allowed": False,
                "verification_required": True}
    return {"status": "BOUND", "reasons": [], "retry_allowed": True, "verification_required": True}


def state_family_schema_for(path: str) -> str | None:
    """Deterministic schema identification for a durable state path.

    Maps a filename/path to the exact schema identity it belongs to, so a
    fresh-clone recovery can identify the correct state family without
    ambiguity. Matched on the family's durable surface name, not the schema
    id string itself.
    """
    base = str(path).strip().lower()
    if not base:
        return None
    ordered = (
        ("task-state.json", "p2p-task-state/1"),
        ("execution-ledger.jsonl", "p2p-task-event/1"),
        ("autopilot-goal-state.json", "p2p-autopilot-goal/1"),
        ("goal-ledger.jsonl", "p2p-goal-event/1"),
        ("resume-point.json", "p2p-autopilot-resume-point/1"),
    )
    for suffix, schema in ordered:
        if base.endswith(suffix) or "/" + suffix in "/" + base:
            return schema
    return None


# ---------------------------------------------------------------------------
# C34 closure-reconciliation: requested-vs-observed profile attestation.
#
# The profile/model the task contract requests (REQUESTED_TARGET) is a
# declaration. What the backend actually ran (OBSERVED_EFFECTIVE) must come
# from runtime evidence (receipt, usage log, message history) — never from
# the request echo. The two are separate fields; they are only equal when
# runtime evidence independently binds them. Where the receipt gives only
# profile granularity (no independent model identifier), model binding is
# UNKNOWN_FOR_MODEL and is reported honestly instead of copied.
# ---------------------------------------------------------------------------

ATTESTATION_PROFILES = ("UNKNOWN", "PROFILE_BOUND", "MODEL_BOUND")


def validate_attestation_binding(
    requested: str | None,
    observed: str | None,
    evidence_pointers: tuple[str, ...] = (),
) -> tuple[bool, dict[str, Any]]:
    """Validate the REQUESTED vs OBSERVED profile attestation.

    Returns (ok, detail). ok is True only when an OBSERVED value exists and
    is anchored in at least one evidence pointer. Requested-only or
    copy-equal claims without evidence are REJECTED.
    """
    if not isinstance(evidence_pointers, tuple) or not evidence_pointers:
        return False, {"reason": "NO_OBSERVATION_EVIDENCE",
                       "attestation_profile": "UNKNOWN"}
    if not observed or not isinstance(observed, str):
        return False, {"reason": "OBSERVED_PROFILE_MISSING",
                       "attestation_profile": "UNKNOWN"}
    profile = (ATTESTATION_PROFILES[1] if len(observed) <= 64
               else ATTESTATION_PROFILES[2])
    match = (requested is not None and str(requested).strip() == str(observed).strip())
    return True, {
        "reason": "REQUEST_MATCHES_OBSERVED" if match else "REQUEST_OBSERVED_DISTINCT",
        "requested_target": requested,
        "observed_effective": observed,
        "attestation_profile": profile,
        "evidence_pointers": list(evidence_pointers),
    }
