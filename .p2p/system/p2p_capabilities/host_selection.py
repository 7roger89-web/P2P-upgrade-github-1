from __future__ import annotations

"""C21 deterministic host discovery and selection policy.

This module consumes C20 neutral host/executor contracts. It never launches a
host, grants permission, selects a model/provider, or performs background work.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Iterable, Mapping, Sequence

from .host_executor import (
    SUPPORTED,
    UNKNOWN,
    HostCapabilityProfile,
    PortableExecutionRequest,
    build_portable_handoff,
    evaluate_host_preflight,
)

AVAILABLE = "KNOWN_AVAILABLE"
UNAVAILABLE = "KNOWN_UNAVAILABLE"
AVAILABILITY_UNKNOWN = UNKNOWN
AVAILABILITY_STATES = (AVAILABLE, UNAVAILABLE, AVAILABILITY_UNKNOWN)
REQUIREMENT_SCHEMA = "p2p-host-requirement-profile/1"
DISCOVERY_SCHEMA = "p2p-host-discovery-record/1"
DECISION_SCHEMA = "p2p-host-selection-decision/1"

SELECTED = "SELECTED"
NO_COMPATIBLE_HOST = "NO_COMPATIBLE_HOST"
HOST_EVIDENCE_INSUFFICIENT = "HOST_EVIDENCE_INSUFFICIENT"
BLOCKED = "BLOCKED"

REASON_SELECTED_MINIMUM = "HOST_SELECTED_MINIMUM_SUFFICIENT"
REASON_REJECTED_CAPABILITY = "HOST_REJECTED_CAPABILITY"
REASON_REJECTED_PERMISSION = "HOST_REJECTED_PERMISSION"
REASON_REJECTED_ENVIRONMENT = "HOST_REJECTED_ENVIRONMENT"
REASON_REJECTED_IDENTITY = "HOST_REJECTED_IDENTITY"
REASON_REJECTED_PROJECT = "HOST_REJECTED_PROJECT_BINDING"
REASON_REJECTED_STALE = "HOST_REJECTED_STALE_PROFILE"
REASON_REJECTED_UNAVAILABLE = "HOST_REJECTED_UNAVAILABLE"
REASON_AVAILABILITY_UNKNOWN = "HOST_AVAILABILITY_UNKNOWN"
REASON_CONTEXT_UNSUPPORTED = "HOST_REJECTED_CONTEXT_MATERIALIZATION"
REASON_MUTATION_RECONCILIATION = "HOST_REJECTED_MUTATION_RECONCILIATION"
REASON_SWITCH_NOT_MATERIAL = "HOST_SWITCH_NOT_MATERIAL"
REASON_STABLE_TIE_BREAK = "HOST_STABLE_TIE_BREAK"
REASON_NO_COMPATIBLE = "NO_COMPATIBLE_HOST"


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field}_INVALID")
    return value.strip()


def _tuple(values: Iterable[str] | None, field: str) -> tuple[str, ...]:
    if values is None:
        return ()
    if isinstance(values, str):
        raise ValueError(f"{field}_MUST_BE_LIST")
    result = tuple(_text(value, f"{field}_ITEM") for value in values)
    if len(result) != len(set(result)):
        raise ValueError(f"{field}_DUPLICATE")
    return result


def _stable_id(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class HostRequirementProfile:
    """Smallest bounded host requirement derived from a C20 request."""

    required_capabilities: tuple[str, ...] = ()
    permission_needs: tuple[str, ...] = ()
    granted_permissions: tuple[str, ...] = ()
    expected_environment: str = UNKNOWN
    context_required: bool = False
    identity_required: bool = False
    verification_expectations: tuple[str, ...] = ()
    requires_same_environment_verification: bool = False
    mutation_requested: bool = False
    owner_local_only: bool = False
    project_binding: str | None = None
    candidate_binding: str | None = None
    freshness_seconds: int | None = None
    task_id: str | None = None
    reasoning_class: str | None = None
    context_class: str | None = None
    verification_class: str | None = None

    @classmethod
    def from_request(
        cls,
        request: PortableExecutionRequest,
        *,
        owner_local_only: bool = False,
        reasoning_class: str | None = None,
        context_class: str | None = None,
        verification_class: str | None = None,
        requires_same_environment_verification: bool = False,
        freshness_seconds: int | None = None,
    ) -> "HostRequirementProfile":
        return cls(
            required_capabilities=_tuple(request.required_capabilities, "required_capabilities"),
            permission_needs=_tuple(request.permission_needs, "permission_needs"),
            granted_permissions=_tuple(request.granted_permissions, "granted_permissions"),
            expected_environment=request.expected_environment,
            context_required=bool(request.context_refs or request.context_materialization_refs),
            identity_required=bool(request.identity_required),
            verification_expectations=_tuple(request.verification_expectations, "verification_expectations"),
            requires_same_environment_verification=requires_same_environment_verification,
            mutation_requested=request.mutation_requested,
            owner_local_only=owner_local_only,
            project_binding=request.project_binding,
            candidate_binding=request.candidate_binding,
            freshness_seconds=freshness_seconds,
            task_id=request.task_id,
            reasoning_class=reasoning_class,
            context_class=context_class,
            verification_class=verification_class,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": REQUIREMENT_SCHEMA,
            "required_capabilities": list(self.required_capabilities),
            "permission_needs": list(self.permission_needs),
            "granted_permissions": list(self.granted_permissions),
            "expected_environment": self.expected_environment,
            "context_required": self.context_required,
            "identity_required": self.identity_required,
            "verification_expectations": list(self.verification_expectations),
            "requires_same_environment_verification": self.requires_same_environment_verification,
            "mutation_requested": self.mutation_requested,
            "owner_local_only": self.owner_local_only,
            "project_binding": self.project_binding,
            "candidate_binding": self.candidate_binding,
            "freshness_seconds": self.freshness_seconds,
            "task_id": self.task_id,
            "reasoning_class": self.reasoning_class,
            "context_class": self.context_class,
            "verification_class": self.verification_class,
        }


@dataclass(frozen=True)
class HostDiscoveryRecord:
    """Bounded declarative discovery evidence; discovery is not certification."""

    host_id: str
    profile: HostCapabilityProfile
    availability: str = AVAILABILITY_UNKNOWN
    observed_at: str = field(default_factory=_now)
    provenance: str = "DECLARED_PROFILE"
    environment_binding: str | None = None
    project_binding: str | None = None
    profile_version: str = "1"
    active: bool = False
    reconciliation_burden: int = 0
    execution_transport_available: bool = False

    def __post_init__(self) -> None:
        _text(self.host_id, "host_id")
        if self.availability not in AVAILABILITY_STATES:
            raise ValueError("AVAILABILITY_STATE_INVALID")
        _text(self.observed_at, "observed_at")
        _text(self.provenance, "provenance")
        if self.reconciliation_burden < 0:
            raise ValueError("RECONCILIATION_BURDEN_INVALID")

    def freshness(self, *, now: str | None = None) -> int | None:
        try:
            observed = datetime.fromisoformat(self.observed_at.replace("Z", "+00:00"))
            current = datetime.fromisoformat((now or _now()).replace("Z", "+00:00"))
            return max(0, int((current - observed).total_seconds()))
        except ValueError:
            return None

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": DISCOVERY_SCHEMA,
            "host_id": self.host_id,
            "profile": self.profile.to_dict(),
            "availability": self.availability,
            "observed_at": self.observed_at,
            "provenance": self.provenance,
            "environment_binding": self.environment_binding,
            "project_binding": self.project_binding,
            "profile_version": self.profile_version,
            "active": self.active,
            "reconciliation_burden": self.reconciliation_burden,
            "execution_transport_available": self.execution_transport_available,
        }


@dataclass(frozen=True)
class HostCandidate:
    host_id: str
    record: HostDiscoveryRecord
    requirement: HostRequirementProfile
    preflight: Mapping[str, Any]
    capability_excess: int
    freshness_seconds: int | None


@dataclass(frozen=True)
class HostSelectionDecision:
    status: str
    task_id: str
    request_fingerprint: str
    required_capabilities: tuple[str, ...]
    candidate_host_ids: tuple[str, ...]
    rejected_candidates: tuple[Mapping[str, Any], ...]
    selected_host_id: str | None = None
    selection_reason_codes: tuple[str, ...] = ()
    availability_evidence_refs: tuple[str, ...] = ()
    environment_binding: str = UNKNOWN
    decision_timestamp: str = field(default_factory=_now)
    freshness: Mapping[str, Any] = field(default_factory=dict)
    handoff: Mapping[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": DECISION_SCHEMA,
            "status": self.status,
            "task_id": self.task_id,
            "request_fingerprint": self.request_fingerprint,
            "required_capabilities": list(self.required_capabilities),
            "candidate_host_ids": list(self.candidate_host_ids),
            "rejected_candidates": [dict(item) for item in self.rejected_candidates],
            "selected_host_id": self.selected_host_id,
            "selection_reason_codes": list(self.selection_reason_codes),
            "availability_evidence_refs": list(self.availability_evidence_refs),
            "environment_binding": self.environment_binding,
            "decision_timestamp": self.decision_timestamp,
            "freshness": dict(self.freshness),
            "handoff": dict(self.handoff) if self.handoff else None,
        }


def discover_host_profiles(
    records: Sequence[HostDiscoveryRecord], *, source: str | None = None
) -> tuple[HostDiscoveryRecord, ...]:
    """Return only explicitly supplied records; never scan or certify hosts."""
    result = tuple(record for record in records if source is None or record.provenance == source)
    if len({record.host_id for record in result}) != len(result):
        raise ValueError("DUPLICATE_HOST_ID")
    return result


def _rejection(reason: str, detail: Mapping[str, Any] | None = None) -> dict[str, Any]:
    result = {"reason": reason}
    if detail:
        result.update(detail)
    return result


def _gate(
    record: HostDiscoveryRecord,
    requirement: HostRequirementProfile,
    request: PortableExecutionRequest,
    *,
    now: str | None,
    parent_permission_grants: Iterable[str] | None,
) -> tuple[str, dict[str, Any] | None]:
    if record.availability == UNAVAILABLE:
        return REASON_REJECTED_UNAVAILABLE, _rejection(REASON_REJECTED_UNAVAILABLE, {"availability": record.availability})
    if record.availability == AVAILABILITY_UNKNOWN:
        return REASON_AVAILABILITY_UNKNOWN, _rejection(REASON_AVAILABILITY_UNKNOWN, {"availability": record.availability})
    if requirement.owner_local_only and record.profile.environment not in ("LOCAL_PROJECT", "LOCAL_AUTHORITATIVE_PROJECT"):
        return REASON_REJECTED_ENVIRONMENT, _rejection(REASON_REJECTED_ENVIRONMENT, {"actual_environment": record.profile.environment})
    if requirement.project_binding and record.project_binding and record.project_binding != requirement.project_binding:
        return REASON_REJECTED_PROJECT, _rejection(REASON_REJECTED_PROJECT)
    if requirement.project_binding and record.project_binding is None and requirement.mutation_requested:
        return REASON_REJECTED_PROJECT, _rejection(REASON_REJECTED_PROJECT, {"binding": "UNKNOWN"})
    age = record.freshness(now=now)
    if requirement.freshness_seconds is not None and (age is None or age > requirement.freshness_seconds):
        return REASON_REJECTED_STALE, _rejection(REASON_REJECTED_STALE, {"age_seconds": age})
    preflight = evaluate_host_preflight(record.profile, request, parent_permission_grants=parent_permission_grants)
    if preflight["status"] != "READY":
        reason = preflight.get("reason")
        if reason == "CAPABILITY_UNAVAILABLE":
            return REASON_REJECTED_CAPABILITY, _rejection(REASON_REJECTED_CAPABILITY, {"preflight": preflight})
        if reason == "PERMISSION_BLOCKED":
            return REASON_REJECTED_PERMISSION, _rejection(REASON_REJECTED_PERMISSION, {"preflight": preflight})
        if reason == "IDENTITY_EVIDENCE_UNAVAILABLE":
            return REASON_REJECTED_IDENTITY, _rejection(REASON_REJECTED_IDENTITY, {"preflight": preflight})
        if reason == "RECONCILIATION_REQUIRED":
            return REASON_REJECTED_ENVIRONMENT, _rejection(REASON_REJECTED_ENVIRONMENT, {"preflight": preflight})
        return reason or BLOCKED, _rejection(reason or BLOCKED, {"preflight": preflight})
    if requirement.context_required and record.profile.state("can_receive_context_refs") != SUPPORTED:
        return REASON_CONTEXT_UNSUPPORTED, _rejection(REASON_CONTEXT_UNSUPPORTED)
    if requirement.requires_same_environment_verification and record.profile.state("can_run_tests") != SUPPORTED:
        return REASON_REJECTED_CAPABILITY, _rejection(REASON_REJECTED_CAPABILITY, {"verification": "same_environment"})
    if requirement.mutation_requested and requirement.expected_environment == "LOCAL_PROJECT" and record.profile.environment != "LOCAL_PROJECT":
        return REASON_MUTATION_RECONCILIATION, _rejection(REASON_MUTATION_RECONCILIATION)
    return "READY", None


class HostSelector:
    """Deterministic hard-gate selector; it performs no execution."""

    def __init__(self, *, now: str | None = None):
        self.now = now

    def select(
        self,
        request: PortableExecutionRequest,
        records: Sequence[HostDiscoveryRecord],
        *,
        requirement: HostRequirementProfile | None = None,
        current_host_id: str | None = None,
        parent_permission_grants: Iterable[str] | None = None,
    ) -> HostSelectionDecision:
        requirement = requirement or HostRequirementProfile.from_request(request)
        discovered = discover_host_profiles(records)
        rejected: list[dict[str, Any]] = []
        candidates: list[HostCandidate] = []
        candidate_ids = tuple(record.host_id for record in discovered)
        for record in discovered:
            reason, detail = _gate(record, requirement, request, now=self.now, parent_permission_grants=parent_permission_grants)
            if reason != "READY":
                rejected.append({"host_id": record.host_id, **(detail or {"reason": reason})})
                continue
            excess = sum(
                1
                for name, state in record.profile.capabilities.items()
                if state == SUPPORTED and name not in requirement.required_capabilities
            )
            candidates.append(
                HostCandidate(
                    record.host_id,
                    record,
                    requirement,
                    {"status": "READY"},
                    excess,
                    record.freshness(now=self.now),
                )
            )
        if not candidates:
            rejection_reasons = {item["reason"] for item in rejected}
            evidence_only = rejection_reasons and rejection_reasons.issubset({REASON_AVAILABILITY_UNKNOWN, REASON_REJECTED_STALE})
            status = HOST_EVIDENCE_INSUFFICIENT if evidence_only else NO_COMPATIBLE_HOST
            reason_codes = (REASON_AVAILABILITY_UNKNOWN,) if status == HOST_EVIDENCE_INSUFFICIENT else (REASON_NO_COMPATIBLE,)
            return HostSelectionDecision(
                status,
                request.task_id,
                request.fingerprint,
                requirement.required_capabilities,
                candidate_ids,
                tuple(rejected),
                selection_reason_codes=reason_codes,
                environment_binding=requirement.expected_environment,
                freshness={"observed_at": self.now or _now()},
            )
        candidates.sort(
            key=lambda item: (
                item.capability_excess,
                0 if item.host_id == current_host_id else 1,
                item.record.reconciliation_burden,
                item.host_id,
            )
        )
        selected = candidates[0]
        reasons = [REASON_SELECTED_MINIMUM]
        if current_host_id and selected.host_id == current_host_id:
            reasons.append(REASON_SWITCH_NOT_MATERIAL)
        if len(candidates) > 1 and candidates[0].capability_excess == candidates[1].capability_excess:
            reasons.append(REASON_STABLE_TIE_BREAK)
        handoff = None
        if current_host_id and selected.host_id != current_host_id:
            handoff = build_portable_handoff(
                request,
                checkpoint_ref=f".p2p/state/host-selection/{request.fingerprint}.json",
                next_step="open selected compatible executor and continue from the authoritative project",
                verification_required=("project binding", "candidate binding"),
                unfinished_safe_work=(),
            ).to_dict()
        return HostSelectionDecision(
            SELECTED,
            request.task_id,
            request.fingerprint,
            requirement.required_capabilities,
            candidate_ids,
            tuple(rejected),
            selected.host_id,
            tuple(reasons),
            (f"{selected.record.provenance}:{selected.record.host_id}",),
            selected.record.profile.environment,
            self.now or _now(),
            {selected.host_id: selected.freshness_seconds},
            handoff,
        )


def safe_reselection_allowed(
    *,
    prior_receipt: Mapping[str, Any],
    previous_request: PortableExecutionRequest,
    current_request: PortableExecutionRequest,
    project_binding_unchanged: bool,
    permissions_unchanged: bool,
    context_fresh: bool,
) -> bool:
    if not project_binding_unchanged or not permissions_unchanged or not context_fresh:
        return False
    if previous_request.fingerprint != current_request.fingerprint:
        return False
    status = str(prior_receipt.get("status", ""))
    possible_mutation = bool(prior_receipt.get("possible_mutation", False))
    return status in ("HOST_UNAVAILABLE", "FAILED") and not possible_mutation


def compare_naive_policies(
    records: Sequence[HostDiscoveryRecord],
    decision: HostSelectionDecision,
    *,
    current_host_id: str | None = None,
) -> dict[str, Any]:
    available = [record.host_id for record in records if record.availability == AVAILABLE]
    strongest = max(
        records,
        key=lambda record: sum(state == SUPPORTED for state in record.profile.capabilities.values()),
        default=None,
    )
    cheapest_estimate = min(records, key=lambda record: record.reconciliation_burden, default=None)
    return {
        "minimum_sufficient": decision.selected_host_id,
        "always_current": current_host_id if current_host_id in available else None,
        "first_available": available[0] if available else None,
        "always_strongest": strongest.host_id if strongest else None,
        "cheapest_estimate": cheapest_estimate.host_id if cheapest_estimate else None,
        "use_all_hosts": tuple(available),
        "authoritative_cost": UNKNOWN,
    }


__all__ = [
    "AVAILABLE",
    "UNAVAILABLE",
    "AVAILABILITY_UNKNOWN",
    "AVAILABILITY_STATES",
    "SELECTED",
    "NO_COMPATIBLE_HOST",
    "HOST_EVIDENCE_INSUFFICIENT",
    "BLOCKED",
    "HostRequirementProfile",
    "HostDiscoveryRecord",
    "HostCandidate",
    "HostSelectionDecision",
    "HostSelector",
    "discover_host_profiles",
    "safe_reselection_allowed",
    "compare_naive_policies",
    "REASON_SELECTED_MINIMUM",
    "REASON_REJECTED_CAPABILITY",
    "REASON_REJECTED_PERMISSION",
    "REASON_REJECTED_ENVIRONMENT",
    "REASON_REJECTED_IDENTITY",
    "REASON_REJECTED_PROJECT",
    "REASON_REJECTED_STALE",
    "REASON_REJECTED_UNAVAILABLE",
    "REASON_AVAILABILITY_UNKNOWN",
    "REASON_CONTEXT_UNSUPPORTED",
    "REASON_MUTATION_RECONCILIATION",
    "REASON_SWITCH_NOT_MATERIAL",
    "REASON_STABLE_TIE_BREAK",
    "REASON_NO_COMPATIBLE",
]
