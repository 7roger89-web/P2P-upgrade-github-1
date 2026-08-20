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
    CAPABILITY_EXECUTION_SCOPE_MAP,
    CERTIFICATION_SCOPES,
)

ELIGIBILITY_DECISIONS = ("ELIGIBLE", "INELIGIBLE", "UNKNOWN")

ELIGIBILITY_SCHEMA = "p2p-role-target-eligibility/1"

# Canonical permission grant ordering (never-widens: role <= task <=
# goal-approved envelope; actual executor permission must not exceed the
# composed envelope).
# P2P-BOUNDED-DOCUMENTATION-WRITE-01: WRITE_BOUNDED ranks between READ
# and WRITE. It is strictly weaker than WRITE — a profile containing
# only WRITE_BOUNDED never satisfies a WRITE ceiling, and a read-only
# role never gains it implicitly (it must be bound to the bounded
# documentation primitive explicitly).
PERMISSION_ORDER = ("NONE", "READ", "WRITE_BOUNDED", "WRITE", "EXECUTE", "NETWORK")

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
    registry_records: Iterable[Mapping[str, Any]] | None = None,
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
            # Closure seam (01A): bounded capability→execution-scope
            # bridge is EXPLICIT and registry-governed. Priority:
            #   1. registry record EXECUTION_SCOPE field (canonical),
            #   2. CAPABILITY_EXECUTION_SCOPE_MAP (module-level fallback),
            #   3. legacy PROVIDER_SCOPE field (backward compat),
            #   4. hard BLOCK — a capability with no certified scope
            #      mapping is never mapped implicitly (fail-closed).
            _cap_rec = None
            for _r in (registry_records or ()):
                if str(_r.get("CAPABILITY_ID", "")) == scope:
                    _cap_rec = _r
                    break
            _prov = None
            if _cap_rec and _cap_rec.get("EXECUTION_SCOPE"):
                _ps = str(_cap_rec["EXECUTION_SCOPE"])
                if _ps in CERTIFICATION_SCOPES:
                    _prov = _ps
            if not _prov and str(scope) in CAPABILITY_EXECUTION_SCOPE_MAP:
                _ps = str(CAPABILITY_EXECUTION_SCOPE_MAP[str(scope)])
                if _ps in CERTIFICATION_SCOPES:
                    _prov = _ps
            if not _prov and _cap_rec and _cap_rec.get("PROVIDER_SCOPE"):
                _ps = str(_cap_rec["PROVIDER_SCOPE"])
                if _ps in CERTIFICATION_SCOPES:
                    _prov = _ps
            if _prov:
                state = certification_for_scope(target, _prov)
                cap_results[scope] = state
                if state in ("UNKNOWN", "NOT_TESTED"):
                    unknown_flags.append(
                        f"capability-scope-unknown:{scope}"
                        f":{_prov}")
                continue
            cap_results[scope] = "UNKNOWN"
            unknown_flags.append(
                f"capability-scope-unknown:{scope}")
            continue
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
    # The bounded-write primitive is a separate authority surface — a
    # target claiming WRITE_BOUNDED availability without an explicit
    # task profile containing WRITE_BOUNDED is a widening attempt.
    _task_grants_bounded = any(
        str(item).strip().upper() == "WRITE_BOUNDED"
        for item in task_permission_profile)
    if target.current_auth_state.upper() == "WRITE_BOUNDED" and \
            not _task_grants_bounded:
        permission_widens = True
        reasons.append("bounded-write-claim-without-explicit-task-profile")

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



# P2P-CLOSURE-01 - persisted target certification registry (runtime
# state, write-only additive ledger; latest entry per target_id wins).
_P2P_TARGET_REGISTRY_SENTINEL = True
try:
    import os as _ti_os
    import pathlib as _ti_pathlib
    import datetime as _ti_datetime
except Exception:
    import os as _ti_os
    import pathlib as _ti_pathlib
    import datetime as _ti_datetime
TARGET_REGISTRY_PATH = _ti_pathlib.Path(_ti_os.environ.get(
    "P2P_STATE_DIR", "") or str(
        _ti_pathlib.Path(__file__).resolve().parents[1] / ".p2p" /
        "state")) / "target_registry.json"


def _p2p_target_registry_entries() -> list:
    try:
        if TARGET_REGISTRY_PATH.exists():
            return list(json.loads(TARGET_REGISTRY_PATH.read_text())
                        or [])
    except Exception:
        pass
    return []


def append_target_certification_record(target_id: str, adapter_id: str,
                                       scope_certifications: tuple = (),
                                       historical_certification:
                                       bool = False,
                                       current_auth_state:
                                       str = "UNKNOWN",
                                       environment_binding:
                                       str = "UNKNOWN") -> None:
    entry = {"target_id": str(target_id),
             "adapter_id": str(adapter_id),
             "scope_certifications": [dict(c) for c in
                                      scope_certifications],
             "historical_certification": bool(historical_certification),
             "current_auth_state": str(current_auth_state),
             "environment_binding": str(environment_binding),
             "registered_at": _ti_datetime.datetime.now(
                 _ti_datetime.timezone.utc).isoformat()}
    records = _p2p_target_registry_entries()
    records.append(entry)
    TARGET_REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    TARGET_REGISTRY_PATH.write_text(json.dumps(records, indent=2)
                                    + "\n")


def load_target_registry() -> dict:
    latest = {}
    for rec in _p2p_target_registry_entries():
        tid = str(rec.get("target_id", ""))
        if tid and tid != "unregistered":
            latest[tid] = rec
    out = {}
    for tid, rec in latest.items():
        try:
            out[tid] = target_certification_record_from_adapter_identity(
                target_id=tid,
                adapter_id=str(rec.get("adapter_id", "")),
                scope_certifications=tuple(
                    BackendCapabilityCertification(
                        adapter_id=tid,
                        scope=str(c.get("scope", "")),
                        status=str(c.get("status", "UNKNOWN")),
                        evidence_pointers=tuple(c.get(
                            "evidence_pointers", ()) or ()))
                    for c in rec.get("scope_certifications") or ()),
                historical_certification=bool(
                    rec.get("historical_certification", False)),
                current_auth_state=str(
                    rec.get("current_auth_state", "UNKNOWN")),
                environment_binding=str(
                    rec.get("environment_binding", "UNKNOWN")))
        except Exception:
            continue
    return out


# ---------------------------------------------------------------------------
# GATE01-SOURCE-BOUND-ELIGIBILITY
# Source-and-project revision binding on top of the closure seam. Eligibility
# is RE-GATED by the live source/project revision status of the
# (capability_id, subject) certification. Revision drift, wrong subject, or
# expiry all fail closed BEFORE any dispatch path uses the eligibility
# result. This is a narrow gate addition: it wraps the existing
# evaluate_role_target_eligibility and never widens certification scope.
# ---------------------------------------------------------------------------
from p2p_capabilities.quality_intelligence import (
    source_bound_status as _gate01_source_bound_status,
)


def evaluate_source_bound_role_eligibility(
    *,
    role_id: str,
    role_required_capabilities: Iterable[str],
    role_permission_ceiling: Iterable[str],
    role_quorum_semantics: str,
    required_evidence: Iterable[str],
    task_permission_profile: Iterable[str],
    goal_permission_envelope: Iterable[str] = ("NONE",),
    target: "TargetCertificationRecord",
    environment_binding: str = "LOCAL_PROJECT",
    workspace_binding: str = "",
    registry_records: "Iterable[Mapping[str, Any]] | None" = None,
    source_repository_id: str = "",
    current_source_commit: str = "",
    current_project_commit: str = "",
) -> dict[str, Any]:
    """Canonical eligibility with source/project revision gating.

    Returns the standard eligibility decision dict with one added gate:
    every REQUIRED capability's (capability_id, subject) pair must be
    CURRENT_EXACT_REVISION against the declared source and project
    commits. Subject here is the role identity that consumes the
    capability (the narrow certification subject). Any non-current
    status is surfaced as a dedicated BLOCKED reason and the decision
    becomes NOT_ELIGIBLE regardless of backend-scope state.
    """
    for name, value in (("source_repository_id", source_repository_id),
                        ("current_source_commit", current_source_commit),
                        ("current_project_commit", current_project_commit)):
        if not str(value or "").strip():
            raise ValueError(
                "source-bound eligibility missing " + name)
    inner = evaluate_role_target_eligibility(
        role_required_capabilities=role_required_capabilities,
        role_permission_ceiling=role_permission_ceiling,
        role_quorum_semantics=role_quorum_semantics,
        required_evidence=required_evidence,
        task_permission_profile=task_permission_profile,
        goal_permission_envelope=goal_permission_envelope,
        target=target,
        environment_binding=environment_binding,
        workspace_binding=workspace_binding,
        registry_records=registry_records,
    )
    source_reasons: list[str] = []
    for capability_id in tuple(str(item) for item in
                               role_required_capabilities):
        status = _gate01_source_bound_status(
            capability_id=capability_id,
            subject=str(role_id),
            current_source_commit=current_source_commit,
            current_project_commit=current_project_commit)
        if status.get("status") != "CURRENT_EXACT_REVISION":
            source_reasons.append(
                f"source-bound:{capability_id}:"
                + str(status.get("status",
                                 "NO_SOURCE_BOUND_RECORD")))
    decision = dict(inner)
    if source_reasons:
        decision["decision"] = "NOT_ELIGIBLE"
        decision["reasons"] = (list(inner.get("reasons", ()))
                               + source_reasons)
    decision["source_bound"] = {
        "source_repository_id": str(source_repository_id),
        "current_source_commit": str(current_source_commit).lower(),
        "current_project_commit": str(current_project_commit).lower(),
        "source_reasons": source_reasons,
        "all_source_bounds_current": len(source_reasons) == 0,
    }
    return decision
# GATE01-SOURCE-BOUND-ELIGIBILITY-MARKER-ADDED
