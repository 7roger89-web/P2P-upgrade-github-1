"""P2P-FRAMEWORK-03 — Adaptive Team & Council intelligence.

Deterministic, evidence-backed, fail-closed team-selection intelligence.
Plugs into the CANONICAL surfaces only:
  - agent_role.load_capability_registry / AgentRoleSpec  (registry truth)
  - role_eligibility.evaluate_role_target_eligibility    (eligibility truth)
  - role_quorum.evaluate_role_quorum / adaptive_participant_set
      (council quorum truth)
  - capability_intelligence.evaluate_composition_coverage +
      CompositionCapabilityEvidence  (FW02 fail-closed contract —
      semantics NEVER modified)
  - p2p_fw01_loop.select_role_team / pre_dispatch_revalidation
      (FW01 sole loop; FW03 never opens a second orchestration path)

Non-negotiable architecture:
  FW03 decides WHICH roles participate, bounded and trace-backed;
  FW02 decides WHICH capabilities are required; FW01 operates the loop;
  the permission gate remains the SOLE dispatch authority.
  FW03 is NOT a router. FW03 does NOT choose targets by vendor.
  FW03 does NOT widen permissions. FW03 does NOT certify roles.

Evidence tiers (section 6 vocabulary):
  DECLARED      — role claims a capability; registry entry only.
  VERIFIED      — deterministic, reproducible, independently checked.
  CERTIFIED     — formal certification record (spec/bound evidence).
  LIVE_CERTIFIED— live non-mutating proof through a compatible target.
  UNKNOWN       — no provable claim; fail-closed default.

ACTIVE != CERTIFIED. CERTIFIED != LIVE_CERTIFIED. UNKNOWN != SAFE.
GOAL_PASS != PROMOTION.
"""

from __future__ import annotations

import hashlib
import json
import re
import secrets
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence, Tuple

TEAM_INTELLIGENCE_SCHEMA = "p2p-team-intelligence/1"
TEAM_MODES = ("SINGLE_ROLE", "SMALL_TEAM", "COUNCIL")
EVIDENCE_TIERS = ("UNKNOWN", "DECLARED", "VERIFIED", "CERTIFIED",
                  "LIVE_CERTIFIED")
TIER_RANK = {t: i for i, t in enumerate(EVIDENCE_TIERS)}
# Minimum tier for a role capability to COUNT toward composition when
# live execution of the task is required. DECLARED is never enough for
# LIVE_REQUIRED tasks (section 6 + section 19 provider neutrality:
# capability must survive ROLE x TARGET x BACKEND x PROVIDER x MODEL x
# TOOLSET x WORKSPACE x AUTH x PERMISSION intersection; a registry claim
# alone proves none of those).
MIN_TIER_LIVE_REQUIRED = "VERIFIED"
MIN_TIER_READ_ONLY = "DECLARED"

# Canonical failure classes (section 14; reuse FW02 vocabulary where it
# exists; introduce only genuinely new ones; no aliases).
TEAM_FAILURE_CLASSES = (
    "REQUIRED_CAPABILITY_UNKNOWN",      # FW02 vocab: unknown required cap
    "NO_ELIGIBLE_ROLE",
    "INSUFFICIENT_TEAM_CAPABILITY",
    "COMPOSITION_CAPABILITY_UNKNOWN",   # FW02 vocab
    "COMPOSITION_CAPABILITY_INCOMPLETE",# FW02 vocab
    "TARGET_INELIGIBLE",
    "INDEPENDENCE_REQUIREMENT_UNMET",
    "COUNCIL_PARTICIPANT_UNAVAILABLE",
    "COUNCIL_RESULT_CONFLICT",
    "PERMISSION_BLOCKED",               # FW01/C39 vocab
    "POST_SELECTION_DRIFT",
    "POST_DISPATCH_AMBIGUITY",
)

MUTATION_CLASSES = ("READ_ONLY", "LOW_RISK_MUTATING",
                    "MATERIAL_MUTATING", "PROTECTED_MUTATING")
TASK_RISK_CLASSES = ("LOW", "MEDIUM", "HIGH", "ARCHITECTURE",
                     "COUNCIL_REQUIRED")


# ---------------------------------------------------------------------------
# Evidence model — role capability evidence with provenance (truth source)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class RoleCapabilityEvidence:
    """Grounded per-role capability evidence. Never invented: every field
    must trace to a registry record, an eligibility evaluation, or a
    certification receipt. An unverifiable claim is tier UNKNOWN."""
    role_id: str
    capability_id: str
    evidence_tier: str            # one of EVIDENCE_TIERS
    provenance_pointers: Tuple[str, ...] = ()
    target_compatibility: str = "UNKNOWN"   # compatible | incompatible | UNKNOWN
    freshness_recorded_at: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "role_id", str(self.role_id))
        object.__setattr__(self, "capability_id", str(self.capability_id))
        if self.evidence_tier not in EVIDENCE_TIERS:
            raise ValueError(
                "EVIDENCE_TIER_INVALID",
                {"tier": self.evidence_tier})
        if self.target_compatibility not in (
                "compatible", "incompatible", "UNKNOWN"):
            raise ValueError(
                "TARGET_COMPATIBILITY_INVALID",
                {"value": self.target_compatibility})

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": TEAM_INTELLIGENCE_SCHEMA,
            "role_id": self.role_id,
            "capability_id": self.capability_id,
            "evidence_tier": self.evidence_tier,
            "provenance_pointers": list(self.provenance_pointers),
            "target_compatibility": self.target_compatibility,
            "freshness_recorded_at": self.freshness_recorded_at,
        }


def _as_tuple(values: Any) -> Tuple[str, ...]:
    if values is None:
        return ()
    if isinstance(values, tuple):
        return values
    return tuple(str(v) for v in values)


def load_registry() -> list[dict[str, Any]]:
    """Load the real canonical capability/role registry (single truth
    source). Never invent records."""
    from p2p_capabilities.agent_role import load_capability_registry
    try:
        return list(load_capability_registry())
    except Exception:
        return []


def registry_role_ids(registry_records: Iterable[Mapping[str, Any]],
                      include_optional_specialist: bool = False
                      ) -> Tuple[str, ...]:
    """Canonical role set recovered from the REAL registry records
    (CAPABILITY_ID entries that are canonical roles). Never invent a 9th
    canonical role; aesthetica stays optional-only per governance."""
    from p2p_capabilities.agent_role import (ALL_P2P_ROLES,
                                            OPTIONAL_SPECIALIST_ROLE)
    ids = [str(r.get("CAPABILITY_ID", "")) for r in registry_records
           if str(r.get("CAPABILITY_ID", "")).startswith("p2p_")]
    allowed = ALL_P2P_ROLES if include_optional_specialist else (
        tuple(id_ for id_ in ALL_P2P_ROLES
              if id_ != OPTIONAL_SPECIALIST_ROLE))
    return tuple(dict.fromkeys(id_ for id_ in ids if id_ in allowed))


# ---------------------------------------------------------------------------
# Role capability resolution (registry truth, evidence tier derivation)
# ---------------------------------------------------------------------------
def role_capability_evidence(
        role_id: str,
        registry_records: Iterable[Mapping[str, Any]],
        *,
        live_required: bool = False,
        target_adapter_id: str | None = None,
        target_eligibility_result: Mapping[str, Any] | None = None,
) -> Tuple[RoleCapabilityEvidence, ...]:
    """Resolve what capability evidence a role carries, tiered.

    Rules (fail-closed):
      1. Only capabilities present in the registry records count.
         A role claiming something absent from the registry is NOT counted
         (section 6: never trust a self-declared field alone).
      2. Tier starts at DECLARED when the registry record exists and the
         role's CAPABILITY_ID matches.
      3. VERIFIED+ requires an explicit entry in the record's
         EVIDENCE_CONTRACT / UPSTREAM_PROVENANCE surface — absent evidence
         stays DECLARED.
      4. For LIVE_REQUIRED tasks a capability counts toward composition
         only at MIN_TIER_LIVE_REQUIRED and with a compatible target.
      5. If the target is incompatible or the role is ineligible for the
         target, target_compatibility is "incompatible" and the
         capability still counts only at the applicable tier rule.
    """
    record: dict[str, Any] | None = None
    for r in registry_records:
        if str(r.get("CAPABILITY_ID", "")) == str(role_id):
            record = dict(r)
            break
    out: list[RoleCapabilityEvidence] = []
    if record is None:
        # No registry truth at all -> capability surface UNKNOWN.
        out.append(RoleCapabilityEvidence(
            role_id=role_id, capability_id=role_id,
            evidence_tier="UNKNOWN",
            provenance_pointers=(),
            target_compatibility="UNKNOWN"))
        return tuple(out)
    prov = record.get("UPSTREAM_PROVENANCE") or {}
    ev = record.get("EVIDENCE_CONTRACT") or ""
    pointers = tuple(dict.fromkeys(
        ["capabilities.json/" + str(role_id)]
        + (["evidence-contract:" + str(ev)] if ev else [])
        + (["provenance:" + str(k) + "=" + str(v)
            for k, v in dict(prov).items()] if prov else [])))
    # Tier uplift: any explicit verified/certified evidence surface.
    tier = "DECLARED"
    if ev and str(ev).strip():
        tier = "VERIFIED"
    for key in ("VERIFIED", "CERTIFIED", "LIVE_CERTIFIED",
                "LIVE"):
        if any(str(v).strip().upper() == key
               for v in (prov.values() if prov else ())):
            tier = "CERTIFIED" if key in ("VERIFIED", "CERTIFIED") \
                else "LIVE_CERTIFIED"
    caps: list[str] = [str(role_id)]
    requires = record.get("REQUIRES") or ()
    caps += [str(c) for c in requires]
    compat = "compatible"
    if target_eligibility_result is not None:
        reasons = (target_eligibility_result.get("reasons") or ())
        unknowns = (target_eligibility_result.get("unknown_flags") or ())
        if unknowns or any("UNKNOWN" in str(r) or "unknown" in str(r).lower()
                           for r in reasons):
            compat = "incompatible"
        if not (target_eligibility_result.get("eligible") is True):
            compat = "incompatible"
    effective_tier = tier
    if live_required:
        effective_tier = tier if (TIER_RANK.get(tier, 0) >=
                                  TIER_RANK[MIN_TIER_LIVE_REQUIRED]) \
            else "UNKNOWN"
    return tuple(
        RoleCapabilityEvidence(
            role_id=role_id, capability_id=cap,
            evidence_tier=effective_tier,
            provenance_pointers=pointers,
            target_compatibility=compat)
        for cap in dict.fromkeys(caps))


# ---------------------------------------------------------------------------
# Minimal sufficient team selection (deterministic, bounded, trace-backed)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class TeamDecisionTraceItem:
    step: str
    fact: str
    rationale: str
    tie_breaker: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "step": self.step, "fact": self.fact,
            "rationale": self.rationale,
            "tie_breaker": self.tie_breaker,
        }


@dataclass(frozen=True)
class TeamDecision:
    """Deterministic adaptive team decision. The decision is fully
    derivable from its trace; no selection is based on role names
    'sounding right'."""
    team_mode: str                    # SINGLE_ROLE | SMALL_TEAM | COUNCIL
    participant_roles: Tuple[str, ...] = ()
    required_capabilities: Tuple[str, ...] = ()
    selected_capability_sources: Tuple[str, ...] = ()
    provided_capabilities: Tuple[str, ...] = ()
    decision_trace: Tuple[TeamDecisionTraceItem, ...] = ()
    mode_reason: str = ""
    escalation_factors: Tuple[str, ...] = ()
    failure_class: str = ""
    role_capability_evidence: Tuple[RoleCapabilityEvidence, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": TEAM_INTELLIGENCE_SCHEMA,
            "team_mode": self.team_mode,
            "participant_roles": list(self.participant_roles),
            "required_capabilities": list(self.required_capabilities),
            "selected_capability_sources": list(
                self.selected_capability_sources),
            "provided_capabilities": list(self.provided_capabilities),
            "decision_trace": [t.to_dict() for t in self.decision_trace],
            "mode_reason": self.mode_reason,
            "escalation_factors": list(self.escalation_factors),
            "failure_class": self.failure_class,
            "role_capability_evidence": [
                e.to_dict() for e in self.role_capability_evidence],
        }


def build_team_decision(
        *,
        required_capabilities: Iterable[str],
        registry_records: Iterable[Mapping[str, Any]],
        live_required: bool = False,
        task_risk_class: str = "LOW",
        mutation_class: str = "READ_ONLY",
        independence_required: bool = False,
        verification_required: bool = False,
        target_adapter_id: str | None = None,
        target_eligibility_results: Mapping[str, Mapping[str, Any]] | None = None,
        council_explicitly_required: bool = False,
        fan_out_bound: int = 8,
        eligibility_results: Mapping[str, Mapping[str, Any]] | None = None,
) -> TeamDecision:
    """Deterministic minimal-sufficient team policy.

    Algorithm (set cover, greedy, bounded):
      1. Required capability set R (only explicit task-contract caps;
         unknown caps are NOT invented here — FW02 carries them).
      2. For every registry role compute its PROVIDE set: registry
         CAPABILITY_ID (self capability) + REQUIRES surface, tiered by
         evidence, with target compatibility enforced when a target
         record is supplied.
      3. Eligibility filter: roles failing
         role_eligibility.evaluate_role_target_eligibility are excluded
         with a trace item (never silently dropped — recorded).
      4. Greedy minimum cover of R; tie-break by the evidence-backed
         policy order: capability completeness > eligibility strength >
         certification evidence > least privilege > independence > least
         fan-out > target compatibility > resource cost.
      5. Mode derivation: 1 participant -> SINGLE_ROLE; 2..3 (or a
         verifier/independent-specialty need) -> SMALL_TEAM;
         multiple-independent-judgments / architecture /
         council_explicitly_required -> COUNCIL (bounded adaptive size,
         never auto 8).
    Fail-closed: if R cannot be covered -> INSUFFICIENT_TEAM_CAPABILITY
    with the missing set recorded; if no eligible role exists ->
    NO_ELIGIBLE_ROLE.
    """
    records = [dict(r) for r in registry_records]
    reqs = tuple(dict.fromkeys(str(c) for c in required_capabilities))
    target_results = dict(target_eligibility_results or {})
    elig_results = dict(eligibility_results or {})
    trace: list[TeamDecisionTraceItem] = []
    escalation: list[str] = []

    # --- 1. required capability set ------------------------------------
    trace.append(TeamDecisionTraceItem(
        step="REQUIRED_SET",
        fact="required_capabilities=" + str(reqs),
        rationale="Only explicit task-contract requirements enter the "
                  "team-selection set; capability intelligence (FW02) "
                  "remains the authority on what is required.",
        tie_breaker=""))

    # --- 2. per-role provide sets ---------------------------------------
    from p2p_capabilities.agent_role import CANONICAL_ROLES
    role_ids = tuple(dict.fromkeys(
        str(r.get("CAPABILITY_ID", "")) for r in records
        if str(r.get("CAPABILITY_ID", "")).startswith("p2p_")
        and str(r.get("CAPABILITY_ID", "")) in CANONICAL_ROLES))
    provide: dict[str, set[str]] = {}
    role_evidence: list[RoleCapabilityEvidence] = []
    for role in role_ids:
        evid = role_capability_evidence(
            role, records,
            live_required=live_required,
            target_adapter_id=target_adapter_id,
            target_eligibility_result=(
                target_results.get(role) or elig_results.get(role)))
        role_evidence.extend(evid)
        # Capabilities that count: tier UNKNOWN never counts; and for
        # live-required work only VERIFIED+ counts; incompatible target
        # never counts.
        covers = set()
        for e in evid:
            if e.evidence_tier == "UNKNOWN":
                continue
            if e.target_compatibility != "compatible":
                continue
            if live_required and (TIER_RANK.get(e.evidence_tier, 0) <
                                  TIER_RANK[MIN_TIER_LIVE_REQUIRED]):
                continue
            covers.add(e.capability_id)
        provide[role] = covers
        trace.append(TeamDecisionTraceItem(
            step="ROLE_PROVIDE",
            fact=f"{role} provides={sorted(covers)}",
            rationale="Provision computed from registry REQUIRES surface "
                      "plus eligibility and target compatibility; no "
                      "self-declared claim is trusted without evidence.",
            tie_breaker=""))

    # --- 3. eligibility filter -------------------------------------------
    eligible_roles: list[str] = []
    for role in role_ids:
        res = elig_results.get(role) or target_results.get(role) or {}
        eligible = bool(res.get("eligible", False)) if res else False
        if not eligible:
            if res:
                trace.append(TeamDecisionTraceItem(
                    step="ELIGIBILITY_FILTERED",
                    fact=f"{role} ineligible: reasons="
                         + str(res.get("reasons", ()))[:200],
                    rationale="A role that cannot legally operate the "
                              "target never enters the team (fail "
                              "closed at selection time).",
                    tie_breaker=""))
            continue
        eligible_roles.append(role)
    if not eligible_roles and reqs:
        return TeamDecision(
            team_mode="SINGLE_ROLE",
            required_capabilities=reqs,
            decision_trace=tuple(trace),
            mode_reason="no eligible role for required capabilities",
            failure_class="NO_ELIGIBLE_ROLE",
            role_capability_evidence=tuple(role_evidence))

    # --- 4. greedy minimum cover -----------------------------------------
    uncovered = set(reqs)
    selected: list[str] = []
    while uncovered and len(selected) < min(fan_out_bound, len(role_ids)):
        best, best_score = None, None
        for role in eligible_roles:
            if role in selected:
                continue
            newly_covered = provide.get(role, set()) & uncovered
            if not newly_covered:
                continue
            score = (len(newly_covered),
                     len(provide.get(role, set()) & set(reqs)),
                     # independence: prefer a role different in class if
                     # independence is required
                     (1 if independence_required
                      and any((role_eligibility_results or {}).get(
                          role, {}).get("independence_class")) else 0),
                     # least privilege: prefer fewer extra capabilities
                     -len(provide.get(role, set()) - set(reqs)),
                     # least fan-out (already minimized by greedy length)
                     -len(selected))
            if best_score is None or score > best_score:
                best, best_score = role, score
        if best is None:
            break
        selected.append(best)
        uncovered -= provide.get(best, set())
    # Independence requirement: team >1 must not be nominal duplicates —
    # participants sharing identical capability AND target profiles are
    # flagged (section 9).
    independence_unmet = False
    if independence_required and len(selected) > 1:
        sigs = {tuple(sorted(provide.get(r, set()))) for r in selected}
        if len(sigs) < len(selected):
            independence_unmet = True

    # --- 5. mode derivation ------------------------------------------------
    mode: str
    reason: str
    if council_explicitly_required or task_risk_class in (
            "ARCHITECTURE", "COUNCIL_REQUIRED") \
            or len(selected) >= 4:
        mode = "COUNCIL"
        reason = ("multiple independent judgments required; adaptive "
                  "council size bounded by evidence")
    elif len(selected) <= 1 or (not verification_required
                                and len(selected) == 2
                                and not uncovered):
        mode = "SINGLE_ROLE" if len(selected) <= 1 else "SMALL_TEAM"
        reason = "single role covers required set; no escalation trigger"
    else:
        mode = "SMALL_TEAM"
        reason = "coverage split across specialties or independent " \
                 "verification required"
    if independence_required and len(selected) < 2:
        escalation.append("independence-needs-multiple")
    if verification_required and len(selected) < 2:
        escalation.append("verification-needs-verifier")

    # Failure reporting
    failure = ""
    if independence_unmet:
        failure = "INDEPENDENCE_REQUIREMENT_UNMET"
    elif uncovered:
        failure = "INSUFFICIENT_TEAM_CAPABILITY"
    elif not eligible_roles and reqs:
        failure = "NO_ELIGIBLE_ROLE"

    provided = tuple(dict.fromkeys(
        cap for r in selected for cap in sorted(provide.get(r, set()))
        if cap in set(reqs)))
    trace.append(TeamDecisionTraceItem(
        step="SELECTION_RESULT",
        fact=(f"mode={mode} selected={selected} provided="
              f"{sorted(provided)} uncovered={sorted(uncovered)}"),
        rationale="Minimal sufficient cover; each selection is trace "
                  "backed and nothing is chosen by name plausibility.",
        tie_breaker="evidence policy order (completeness, eligibility, "
                    "certification, privilege, independence, fan-out)"))
    return TeamDecision(
        team_mode=mode,
        participant_roles=tuple(selected),
        required_capabilities=reqs,
        selected_capability_sources=tuple(dict.fromkeys(
            f"capabilities.json/{r}" for r in selected)),
        provided_capabilities=provided,
        decision_trace=tuple(trace),
        mode_reason=reason,
        escalation_factors=tuple(escalation),
        failure_class=failure,
        role_capability_evidence=tuple(role_evidence))


# ---------------------------------------------------------------------------
# Composition evidence provider — real integration with FW02 contract
# ---------------------------------------------------------------------------
def composition_evidence_from_team_decision(
        decision: TeamDecision,
        *,
        selected_target: str = "UNKNOWN",
        live_execution_required: bool = False,
) -> "object":
    """Produce CompositionCapabilityEvidence (FW02 contract) from a team
    decision. Semantics of FW02's composition coverage gate are NOT
    modified: no evidence -> UNKNOWN, missing -> INCOMPLETE, complete
    + grounded evidence -> COMPLETE.

    Grounding rule: a capability is listed in provided_capabilities ONLY
    when a RoleCapabilityEvidence exists with tier UNKNOWN-excluding and
    target compatibility proven. This is the truth source FW02's gate
    consumes (section 7).
    """
    from p2p_capabilities import capability_intelligence as _ci
    provided: list[str] = []
    pointers: list[str] = []
    for e in decision.role_capability_evidence:
        if e.capability_id in set(decision.provided_capabilities):
            provided.append(e.capability_id)
            pointers.append("/".join(e.provenance_pointers[:1])
                            if e.provenance_pointers else
                            "registry/" + e.role_id)
    evidence = _ci.CompositionCapabilityEvidence(
        selected_roles=decision.participant_roles,
        selected_target=selected_target,
        selected_capability_sources=decision.selected_capability_sources,
        provided_capabilities=tuple(dict.fromkeys(provided)),
        evidence_pointers=tuple(dict.fromkeys(pointers))
        if provided else (),
    )
    return evidence


# ---------------------------------------------------------------------------
# Bounded adaptive council
# ---------------------------------------------------------------------------
def adaptive_council_size(
        *,
        task_risk_class: str = "LOW",
        eligible_roles: Iterable[str] = (),
        receipts_with_verification: int = 0,
        council_explicitly_required: bool = False,
        fan_out_bound: int = 8,
) -> dict[str, Any]:
    """Bounded adaptive council sizing. Council is never auto-8: the size
    adapts to task need and honest evidence availability. A canonical
    8-role council is only reportable when 8 independent VERIFIED role
    receipts exist (section 8)."""
    from p2p_capabilities.agent_role import CANONICAL_ROLES
    eligible = [str(r) for r in eligible_roles
                if str(r) in CANONICAL_ROLES]
    if task_risk_class == "LOW":
        size = min(2, len(eligible))
        label = "2-role independent review"
    elif task_risk_class == "MEDIUM":
        size = min(3, len(eligible))
        label = "3-role specialist panel"
    else:
        size = min(len(eligible), fan_out_bound)
        label = "N-role council"
    if council_explicitly_required:
        label = "canonical council requested"
    honest_cap = min(size, receipts_with_verification)
    return {
        "schema": TEAM_INTELLIGENCE_SCHEMA,
        "requested_class": str(task_risk_class).upper(),
        "eligible_roles": sorted(dict.fromkeys(eligible)),
        "adaptive_size": int(size),
        "honest_verified_participant_cap": int(honest_cap),
        "council_label": label,
        "canonical_denominator": 8,
        "full_canonical_possible": (len(eligible) >= 8
                                    and receipts_with_verification >= 8),
        "bounded": size <= fan_out_bound,
    }


def council_integrity_report(
        quorum_result: Mapping[str, Any]) -> dict[str, Any]:
    """Honest N/8 reporting helper. Never claims LIVE_COUNCIL_8_OF_8:
    the claim is only true when quorum decision COMPLETE with all 8
    canonical slots satisfied by independent VERIFIED receipts."""
    decision = quorum_result.get("decision", "UNKNOWN")
    satisfied = list(quorum_result.get("satisfied_roles", ()))
    required = list(quorum_result.get("required_roles", ()))
    n = len(satisfied)
    denom = int(quorum_result.get("canonical_denominator", 8) or 8)
    disqualified = list(quorum_result.get("disqualified_receipts", ()))
    claim_8 = (decision == "COMPLETE" and n == 8
               and len(required) == 8
               and len(disqualified) == 0)
    return {
        "schema": TEAM_INTELLIGENCE_SCHEMA,
        "council_decision": decision,
        "honest_report": (f"{n}/{denom}" if n < 8 or decision != "COMPLETE"
                          else f"8/{denom}"),
        "satisfied_roles": satisfied,
        "missing_roles": list(quorum_result.get("missing_roles", ())),
        "disqualified_count": len(
            quorum_result.get("disqualified_receipts", ())),
        "duplicate_count": len(
            quorum_result.get("duplicate_receipts", ())),
        "claims_live_council_8_of_8": bool(claim_8),
    }


# ---------------------------------------------------------------------------
# Council execution contract (bounded; read-only first)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class CouncilExecutionContract:
    """Bounded council execution contract (section 10). No daemon, no
    unbounded delegation, no role self-spawning."""
    task_id: str
    council_id: str = ""
    participant_ids: Tuple[str, ...] = ()
    role_identities: Tuple[str, ...] = ()
    execution_targets: Tuple[str, ...] = ()
    required_capabilities: Tuple[str, ...] = ()
    per_participant_assignments: Tuple[Mapping[str, Any], ...] = ()
    mutation_permission: str = "READ_ONLY"
    evidence_contract: Tuple[str, ...] = ()
    retry_bound: int = 1
    timeout_budget_seconds: int = 300
    cancellation_token: str = ""
    aggregation_policy: str = "TASK_AWARE"

    def __post_init__(self) -> None:
        if not str(self.task_id).strip():
            raise ValueError("COUNCIL_TASK_ID_REQUIRED")
        n_part = len(self.participant_ids)
        if not (1 <= n_part <= 8):
            raise ValueError("COUNCIL_PARTICIPANT_BOUND_VIOLATED")
        if not (0 <= int(self.retry_bound) <= 3):
            raise ValueError("COUNCIL_RETRY_BOUND_VIOLATED")
        if self.mutation_permission not in ("READ_ONLY",
                                            "LOW_RISK_MUTATING"):
            raise ValueError("COUNCIL_MUTATION_BOUND_VIOLATED")
        if self.aggregation_policy != "TASK_AWARE":
            raise ValueError("COUNCIL_AGGREGATION_MUST_BE_TASK_AWARE")
        if not self.council_id:
            object.__setattr__(self, "council_id",
                               "council-" + hashlib.sha256(
                                   (str(self.task_id) + "|"
                                    + "|".join(self.role_identities)
                                    + "|" + secrets.token_hex(8)).encode()
                               ).hexdigest()[:16])
        if not self.cancellation_token:
            object.__setattr__(self, "cancellation_token",
                               "cancel-" + hashlib.sha256(
                                   (self.council_id + "|"
                                    + secrets.token_hex(8)).encode()
                               ).hexdigest()[:16])

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": TEAM_INTELLIGENCE_SCHEMA,
            "task_id": self.task_id,
            "council_id": self.council_id,
            "participant_ids": list(self.participant_ids),
            "role_identities": list(self.role_identities),
            "execution_targets": list(self.execution_targets),
            "required_capabilities": list(self.required_capabilities),
            "per_participant_assignments": [dict(a)
                                            for a in
                                            self.per_participant_assignments],
            "mutation_permission": self.mutation_permission,
            "evidence_contract": list(self.evidence_contract),
            "retry_bound": self.retry_bound,
            "timeout_budget_seconds": self.timeout_budget_seconds,
            "cancellation_token": self.cancellation_token,
            "aggregation_policy": self.aggregation_policy,
        }


# ---------------------------------------------------------------------------
# Task-aware result aggregation (section 12)
# ---------------------------------------------------------------------------
AGGREGATION_TASK_TYPES = ("FACT_VERIFICATION", "DESIGN_JUDGMENT",
                          "CODE_REVIEW", "IMPLEMENTATION_VERIFIER")


def aggregate_council_results(
        *,
        task_type: str,
        results: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    """Deterministic task-aware aggregation. Majority-wins is NOT the
    rule. Conflicts are never washed away: they are recorded with claims,
    evidence, confidence, and unresolved items. Unresolvable material
    conflict escalates to OWNER_GATE (section 12)."""
    if task_type not in AGGREGATION_TASK_TYPES:
        raise ValueError("AGGREGATION_TASK_TYPE_UNKNOWN")
    rows = [dict(r) for r in results]
    claims = [str(r.get("claim", "")) for r in rows]
    confidences = [int(r.get("confidence", 0)) for r in rows]
    evidence_refs = [tuple(str(e) for e in (r.get("evidence_refs") or ()))
                     for r in rows]
    # Material conflict detection: non-empty claims that differ.
    distinct = [c for c in dict.fromkeys(c for c in claims if c)]
    conflict = len(distinct) > 1
    # Fact verification: unanimous only when confident and evidenced.
    # Design judgment: record divergence, never majority-wash.
    # Code review / implementation verifier: verifier veto stands.
    verdict = "UNKNOWN"
    unresolved: list[str] = []
    if not conflict:
        if claims and claims[0]:
            unanimous = all(c == claims[0] for c in claims)
            all_confident = all(x >= 1 for x in confidences)
            any_evidenced = any(bool(e) for e in evidence_refs)
            if unanimous and all_confident and any_evidenced:
                verdict = "CONSENSUS" if task_type in (
                    "DESIGN_JUDGMENT", "CODE_REVIEW") else "VERIFIED"
            elif unanimous:
                verdict = "WEAK_CONSENSUS"
            else:
                verdict = "INSUFFICIENT_EVIDENCE"
                unresolved.append("no independent evidence")
        else:
            verdict = "NO_CLAIMS"
            unresolved.append("participants issued no claims")
    else:
        verdict = "CONFLICT"
        if task_type == "FACT_VERIFICATION":
            verdict = "FACT_CONFLICT"
        unresolved = [f"conflicting claims: {distinct}"]
    return {
        "schema": TEAM_INTELLIGENCE_SCHEMA,
        "task_type": task_type,
        "aggregated_verdict": verdict,
        "claims": claims,
        "confidences": confidences,
        "evidence_refs": [list(e) for e in evidence_refs],
        "conflict": conflict,
        "unresolved_items": unresolved,
        "failure_class": ("COUNCIL_RESULT_CONFLICT" if conflict else ""),
    }


# ---------------------------------------------------------------------------
# Revalidation before dispatch (section 15)
# ---------------------------------------------------------------------------
def revalidate_selection(
        *,
        decision: TeamDecision,
        current_required_capabilities: Iterable[str],
        current_role_eligibility: Mapping[str, Mapping[str, Any]],
        current_target_id: str,
        max_reselect_attempts: int = 1,
) -> dict[str, Any]:
    """Deterministic pre-dispatch revalidation of the selection evidence.
    If the selected composition drifted after selection, the result is
    POST_SELECTION_DRIFT with bounded re-selection (never infinite loop;
    max_reselect_attempts <= 1)."""
    drift: list[str] = []
    cur_reqs = tuple(dict.fromkeys(str(c) for c in
                                   current_required_capabilities))
    if cur_reqs != decision.required_capabilities:
        drift.append("required_capabilities_changed")
    for role in decision.participant_roles:
        res = current_role_eligibility.get(role) or {}
        if res and not bool(res.get("eligible", False)):
            drift.append(f"role_no_longer_eligible:{role}")
    state: dict[str, Any] = {
        "schema": TEAM_INTELLIGENCE_SCHEMA,
        "decision_preserved": not drift,
        "failure_class": "POST_SELECTION_DRIFT" if drift else "",
        "drift_factors": drift,
        "reselect_bounded": bool(drift) and max_reselect_attempts <= 1,
    }
    return state


# ---------------------------------------------------------------------------
# Beginner-first owner summary (section 13)
# ---------------------------------------------------------------------------
def owner_summary(decision: TeamDecision) -> dict[str, Any]:
    """Non-technical summary for the Owner. No jargon."""
    n = len(decision.participant_roles)
    if decision.failure_class:
        text = ("P2P không thể chọn đội an toàn: "
                + str(decision.failure_class))
    elif decision.team_mode == "SINGLE_ROLE":
        text = ("P2P dùng 1 chuyên gia vì một người đã đủ năng lực.")
    elif decision.team_mode == "SMALL_TEAM":
        text = (f"P2P dùng {n} chuyên gia vì nhiệm vụ cần "
                f"{len(decision.provided_capabilities)} loại kỹ năng "
                f"khác nhau và kiểm chứng độc lập.")
    else:
        text = (f"P2P dùng nhóm hội đồng {n} chuyên gia vì nhiệm vụ "
                "quan trọng, cần nhiều góc nhìn độc lập.")
    return {"schema": TEAM_INTELLIGENCE_SCHEMA,
            "team_mode": decision.team_mode,
            "participant_count": n,
            "owner_facing_summary": text}
