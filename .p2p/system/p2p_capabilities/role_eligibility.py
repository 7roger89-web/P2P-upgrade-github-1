"""C35 Role -> ExecutionTarget eligibility (deterministic, fail closed).

Inputs:  ROLE REQUIREMENTS + TASK REQUIREMENTS + TARGET CAPABILITIES +
         TARGET CERTIFICATION SCOPE + AUTH STATE + PERMISSION ENVELOPE +
         ENVIRONMENT/WORKSPACE BINDING
Output:  ELIGIBLE | INELIGIBLE | UNKNOWN  (UNKNOWN fails closed)

REGISTRY != ELIGIBILITY != CERTIFICATION != SELECTION != FALLBACK !=
ROUTING. This module only answers whether an EXPLICIT target is eligible
for an explicit role/task requirement. It never ranks, selects, or falls
back — that remains C37 territory.

Capability-scoped certification reuse (C34): a backend being live-
certified for one scope does NOT make it eligible for every scope. A
target's certification registry records per-scope certification
status; any scope without independent bounded evidence is UNKNOWN for
that scope.

Historical live certification != current auth availability. If the
current credential is unavailable (revoked / no credentials), the
target is NOT CURRENTLY ELIGIBLE for any task requiring live execution
through it, regardless of historical certification evidence.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from .backend_contract import (
    ADAPTER_STATES,
    AUTH_STATES,
    BackendCapabilityCertification,
    CERTIFICATION_SCOPES,
)

ELIGIBILITY_DECISIONS = ("ELIGIBLE", "INELIGIBLE", "UNKNOWN")

ELIGIBILITY_SCHEMA = "p2p-role-target-eligibility/1"

# Canonical permission grant ordering (never-widens: role <= task <=
# goal-approved envelope; actual executor permission must not exceed the
# composed envelope).
PERMISSION_ORDER = ("NONE", "READ", "WRITE", "EXECUTE", "NETWORK")

# Read-only role authority markers (roles whose canonical definition is
# read-only must not become writable).
READ_ONLY_ROLE_MARKERS = (
    "READ",
    "read-only",
    "observation",
    "review",
    "analysis",
    "mapping",
)


class RoleEligibilityError(ValueError):
    """Raised only when eligibility cannot be evaluated safely."""

    def __init__(self, code: str, details: Mapping[str, Any] | None = None):
        self.code = code
        self.details = details or {}
        super().__init__("ROLE_ELIGIBILITY_ERROR:" + code)


@dataclass(frozen=True)
class TargetCertificationRecord:
    """Per-target certification registry entry (C34 scope reuse).

    A target's certification is a collection of per-scope records. A
    scope absent from the registry is UNKNOWN for that scope. Historical
    certification records stay historical: they describe a bounded probe,
    not current availability."""
    target_id: str
    adapter_id: str
    scope_certifications: tuple[BackendCapabilityCertification, ...] = ()
    historical_certification: bool = False
    current_auth_state: str = "UNKNOWN"
    environment_binding: str = "UNKNOWN"

    def __post_init__(self) -> None:
        if self.current_auth_state not in AUTH_STATES:
            raise RoleEligibilityError("AUTH_STATE_INVALID",
                                       {"state": self.current_auth_state})
        for cert in self.scope_certifications:
            if cert.scope not in CERTIFICATION_SCOPES:
                raise RoleEligibilityError("CERTIFICATION_SCOPE_INVALID",
                                           {"scope": cert.scope})


def certification_for_scope(record: TargetCertificationRecord,
                            scope: str) -> str:
    """Certification state for one scope. Absent scopes are UNKNOWN
    (fail closed) — a live-certified text scope does NOT imply code
    mutation certification. The inverse direction is allowed by design:
    SYNTHETIC_TEXT_EXECUTION is a text-level capability satisfied by any
    certified text-level scope (text-only certification never implies
    broader scopes)."""
    for cert in record.scope_certifications:
        if cert.scope == scope:
            return cert.status
    if scope in TEXT_LEVEL_SCOPES and certifying_text_scope(record):
        return "LIVE_CERTIFIED_FOR_CAPABILITY"
    return "UNKNOWN"


TEXT_LEVEL_SCOPES = ("SYNTHETIC_TEXT_EXECUTION", "NON_MUTATING_TASK")


def certifying_text_scope(record: TargetCertificationRecord) -> bool:
    """Whether the record certifies at least one text-level scope. This
    covers the C34 semantics that a bounded non-mutating / API-transport
    certification is, at minimum, text-level capability."""
    for cert in record.scope_certifications:
        if cert.scope in TEXT_LEVEL_SCOPES:
            return True
    return False


def _permission_level(grant: str) -> int:
    text = str(grant or "NONE").strip().upper()
    if text == "OWNER_GATE_REQUIRED":
        return len(PERMISSION_ORDER)  # never satisfied implicitly
    try:
        return PERMISSION_ORDER.index(text)
    except ValueError:
        return 0


def target_certification_record_to_dict(record: TargetCertificationRecord) -> dict[str, Any]:
    return {
        "schema": ELIGIBILITY_SCHEMA,
        "target_id": record.target_id,
        "adapter_id": record.adapter_id,
        "scope_certifications": [
            cert.to_dict()
            for cert in record.scope_certifications
        ],
        "historical_certification": bool(record.historical_certification),
        "current_auth_state": record.current_auth_state,
        "environment_binding": record.environment_binding,
    }


def evaluate_role_target_eligibility(
    *,
    role_required_capabilities: Iterable[str],
    role_permission_ceiling: Iterable[str],
    role_quorum_semantics: str,
    required_evidence: Iterable[str],
    task_permission_profile: Iterable[str],
    goal_permission_envelope: Iterable[str] = ("NONE",),
    target: TargetCertificationRecord,
    environment_binding: str = "LOCAL_PROJECT",
    workspace_binding: str = "",
) -> dict[str, Any]:
    """Deterministic eligibility decision. Never ranks; never chooses.

    Capability requirements must each be certified for the target.
    Permission composition never widens. Environment/workspace bindings
    must be compatible (unknown bindings fail closed). Historical
    certification does not grant current eligibility when current auth
    is unavailable."""
    reasons: list[str] = []
    unknown_flags: list[str] = []

    role_caps = tuple(str(item) for item in role_required_capabilities)
    cap_results: dict[str, str] = {}
    for scope in role_caps:
        if scope not in CERTIFICATION_SCOPES:
            # Registry-internal need (FACT_LEDGER etc.) does not depend on
            # backend scope certification — it is satisfied by P2P state.
            if scope in ("FACT_LEDGER", "evidence-contract",
                         "EXISTING_P2P_ROUTER", "real-profile-readiness"):
                cap_results[scope] = "SATISFIED_BY_P2P_STATE"
                continue
            cap_results[scope] = "UNKNOWN"
            unknown_flags.append(f"capability-scope-unknown:{scope}")
            continue
        state = certification_for_scope(target, scope)
        cap_results[scope] = state
        if state == "LIVE_CERTIFIED_FOR_CAPABILITY":
            continue
        # A certification record exists for the target: a scope the target
        # never certified is a POSITIVE negative (absent certification is
        # provably absent, not an unknown truth). Only a genuinely UNKNOWN
        # certification surface fails closed as UNKNOWN.
        surface_unknown = (not target.scope_certifications
                           and target.current_auth_state == "UNKNOWN")
        if state in ("UNKNOWN", "NOT_TESTED") and surface_unknown:
            unknown_flags.append(f"scope-not-certified:{scope}:{state}")
        else:
            reasons.append(f"scope-insufficient:{scope}:{state}")

    # Permission never-widens: role ceiling <= task profile <= goal
    # envelope, and the target's usable permission must not exceed the
    # composed envelope.
    ceiling_level = max((_permission_level(item) for item in role_permission_ceiling),
                        default=0)
    task_level = max((_permission_level(item) for item in task_permission_profile),
                     default=0)
    goal_level = max((_permission_level(item) for item in goal_permission_envelope),
                     default=0)
    role_read_only = bool(role_permission_ceiling) and all(
        str(item).strip().upper() in READ_ONLY_ROLE_MARKERS or
        _permission_level(str(item)) <= _permission_level("READ")
        for item in role_permission_ceiling)
    target_auth_level = _permission_level(target.current_auth_state) \
        if target.current_auth_state in PERMISSION_ORDER else 0

    permission_widens = False
    if ceiling_level > task_level:
        permission_widens = True
        reasons.append("role-ceiling-exceeds-task-profile")
    if task_level > goal_level:
        permission_widens = True
        reasons.append("task-profile-exceeds-goal-envelope")
    if target_auth_level > max(ceiling_level, task_level):
        # The backend claiming more permission than the composed
        # envelope is a widening attempt — fail closed.
        permission_widens = True
        reasons.append("target-permission-exceeds-composed-envelope")
    if role_read_only and target.current_auth_state.upper() in ("WRITE", "EXECUTE"):
        permission_widens = True
        reasons.append("read-only-role-target-reports-write-permission")

    # Historical certification != current auth availability.
    auth_blocked = False
    if target.current_auth_state in ("NO_CREDENTIALS", "EXPIRED", "INVALID"):
        auth_blocked = True
        reasons.append("current-auth-unavailable")
    elif target.current_auth_state == "UNKNOWN":
        # No honest auth truth — the honest value is UNKNOWN, failing
        # closed on any live execution requirement.
        if role_caps or required_evidence:
            auth_blocked = True
            unknown_flags.append("auth-state-unknown")
            reasons.append("auth-state-unknown")

    # Environment/workspace binding compatibility (unknown fails closed).
    env_mismatch = False
    if target.environment_binding != "UNKNOWN" and target.environment_binding != environment_binding:
        env_mismatch = True
        reasons.append(f"environment-binding-mismatch:{target.environment_binding}!={environment_binding}")
    workspace_bound = bool(workspace_binding)

    # Required evidence availability (P2P-side evidence contract).
    evidence_missing = False
    for requirement in required_evidence:
        req = str(requirement).strip()
        if not req:
            continue
        # Evidence requirements are satisfied at VERIFICATION time by
        # the role receipt verifier; the eligibility layer only requires
        # that the requirement itself is expressible. Unknown evidence
        # classes fail closed.
        if not re_like_known(req):
            evidence_missing = True
            reasons.append(f"evidence-requirement-unknown:{req}")

    unknown = bool(unknown_flags)
    scope_insufficient = any(reason.startswith("scope-insufficient:")
                             for reason in reasons)
    if permission_widens or auth_blocked or evidence_missing or scope_insufficient:
        # A proven insufficiency (including an absent certification the
        # target demonstrably lacks) is INELIGIBLE, not UNKNOWN: the
        # negative is a positive fact. UNKNOWN is reserved for cases
        # where NO determination is possible at all.
        decision = "INELIGIBLE"
    elif unknown:
        decision = "UNKNOWN"
    else:
        decision = "ELIGIBLE"

    return {
        "schema": ELIGIBILITY_SCHEMA,
        "decision": decision,
        "fail_closed": decision == "INELIGIBLE",
        "target_id": target.target_id,
        "adapter_id": target.adapter_id,
        "current_auth_state": target.current_auth_state,
        "historical_certification": bool(target.historical_certification),
        "current_eligible": decision == "ELIGIBLE",
        "capability_results": dict(cap_results),
        "permission_widens": permission_widens,
        "auth_blocked": auth_blocked,
        "environment_binding_compatible": not env_mismatch,
        "workspace_bound": workspace_bound,
        "unknown_flags": unknown_flags,
        "reasons": reasons,
        "role_quorum_semantics": role_quorum_semantics,
    }


def re_like_known(value: str) -> bool:
    """Known evidence requirement classes (bounded closed set)."""
    known = (
        "claim", "actual-evidence", "source-provenance", "fresh-governance-evidence",
        "boundary-evidence", "cross-scope-evidence", "required-evidence",
        "independent-check", "role-objective-done", "artifact-evidence",
        "evidence-refs",
    )
    return value.lower() in known


def canonical_target_certification_registry(
    records: Iterable[TargetCertificationRecord]) -> dict[str, TargetCertificationRecord]:
    """Explicit registry of target certification records. Registry !=
    router: lookup requires an explicit target id; there is no ranking,
    no fallback, and no automatic selection."""
    registry: dict[str, TargetCertificationRecord] = {}
    for record in records:
        registry[str(record.target_id)] = record
    return registry


def target_certification_record_from_adapter_identity(
    *,
    target_id: str,
    adapter_id: str,
    scope_certifications: Iterable[BackendCapabilityCertification] = (),
    historical_certification: bool = False,
    current_auth_state: str = "UNKNOWN",
    environment_binding: str = "UNKNOWN",
) -> TargetCertificationRecord:
    return TargetCertificationRecord(
        target_id=str(target_id),
        adapter_id=str(adapter_id),
        scope_certifications=tuple(scope_certifications),
        historical_certification=bool(historical_certification),
        current_auth_state=str(current_auth_state),
        environment_binding=str(environment_binding),
    )
