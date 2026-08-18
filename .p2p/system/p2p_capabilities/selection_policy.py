"""C37 Selection Policy — stateless, provider-neutral, evidence-bound
selection pipeline (CORRECTED).

Mandatory pipeline order (spec-mandated):
  ROLE REQUIREMENTS + TASK REQUIREMENTS + TARGET CAPABILITIES +
  CERTIFICATION + AUTH + PERMISSION + ENVIRONMENT + CONTEXT
  -> ELIGIBILITY (eligible set) -> QUALITY/RISK GATE -> OPTIMIZATION ->
  MODEL BINDING -> REASONING-EFFORT BINDING -> SELECTION RECEIPT

Selection never happens before eligibility is proven. UNKNOWN fails
closed everywhere. There is NO silent fallback, NO unbounded provider
retry, NO vendor-name branching - vendor families are DATA, never
control flow. Reasoning-effort vocabulary is strictly the four
provider-neutral classes; core never mentions vendor flags.
"""

from __future__ import annotations

import time
from typing import Any, Iterable, Mapping, Sequence

from . import context_loop_guard as _loop_guard
from .context_efficiency import ExecutionTelemetry
from .decision_trace import capture_material_decision
from .selection_filter import (EligibilityRequirements, FilterDecision,
                               filter_target)
from .selection_quality import (canonical_quality_class,
                                cheapest_failed_penalty, quality_order,
                                quality_floor_violated)
from .selection_request import (REASONING_EFFORT_CLASSES, RISK_CLASSES,
                                SelectionRequest, UNKNOWN)
LOW_EFFORT, MEDIUM_EFFORT, HIGH_EFFORT, VERY_HIGH_EFFORT = "LOW", "MEDIUM", "HIGH", "VERY_HIGH"
from .selection_target import SelectionCandidateEvidence
from .selection_trace import (NO_ELIGIBLE_TARGET, RESELECTION_BLOCKED_LOOP,
                              RESELECTION_BLOCKED_MUTATION_UNKNOWN,
                              RESELECTION_REQUESTED, TARGET_ELIGIBLE,
                              TARGET_SELECTED, MODEL_SELECTED,
                              REASONING_EFFORT_SELECTED,
                              map_exclusion_reason_to_trace,
                              selection_request_text, TRACE_SCHEMA,
                              TRACE_VOCABULARY)
from .selection_receipt import (BLOCKED, SELECTED, SelectionReceipt,
                                SelectionReceiptError,
                                build_selection_receipt, POLICY_VERSION)

POLICY_SCHEMA = "p2p-selection-policy-c37/1"

# Confidence vocabulary (recovered canonical: same as host_selection).
CONFIDENCE_HIGH = "HIGH"
CONFIDENCE_MEDIUM = "MEDIUM"
CONFIDENCE_LOW = "LOW"
CONFIDENCE_UNKNOWN = UNKNOWN
CONFIDENCE_VALUES = (CONFIDENCE_HIGH, CONFIDENCE_MEDIUM, CONFIDENCE_LOW,
                     CONFIDENCE_UNKNOWN)

DEFAULT_RESELECTION_CAP = 3

# Failure classification vocabulary - must be one of these; anything
# else is RESELECTION_BLOCKED_MUTATION_UNKNOWN (fail closed).
KNOWN_FAILURE_CLASSES = (
    "NO_ELIGIBLE_TARGET",
    "CAPABILITY_EXCLUSION",
    "QUALITY_EXCLUSION",
    "CERTIFICATION_EXCLUSION",
    "AUTH_EXCLUSION",
    "PERMISSION_EXCLUSION",
    "CONTEXT_EXCLUSION",
    "ENVIRONMENT_EXCLUSION",
    "OWNER_CONSTRAINT_EXCLUSION",
    "EXECUTION_FAILURE_VERIFIED_SAFE",
    "RESOURCE_BUDGET_INSUFFICIENT",
)


class SelectionPolicyError(Exception):
    """Policy-level failure (configuration/reselection violations)."""


def _as_set(v: Any) -> tuple[str, ...]:
    if v is None:
        return ()
    return tuple({str(x) for x in v})


def _number(v: Any) -> float:
    if v is None:
        return float("nan")
    try:
        f = float(v)
    except (TypeError, ValueError):
        return float("nan")
    return f


def _is_nan(v: float) -> bool:
    return v != v


def _quality_floor_for(request_floor: str, default_floor: str) -> str:
    """Map the SelectionRequest quality_floor vocabulary
    (LOW/MEDIUM/HIGH/UNKNOWN) onto the canonical quality-class floor
    used by the quality gate. UNKNOWN fails closed only at the request
    contract (risk_class UNKNOWN is rejected); here UNKNOWN means the
    owner asserted no floor, so the policy default (MIXED) applies."""
    if request_floor == UNKNOWN or not request_floor:
        return default_floor
    mapping = {"LOW": UNKNOWN, "MEDIUM": "MIXED", "HIGH": "VERIFIED"}
    return mapping.get(request_floor, default_floor)


class SelectionOutcome:
    __slots__ = ("receipt", "candidates_eligible",
                 "excluded_reasons", "policy_fingerprint",
                 "selection_sequence", "confidence")

    def __init__(self, receipt: SelectionReceipt,
                 candidates_eligible: Sequence[str],
                 excluded_reasons: Mapping[str, str],
                 policy_fingerprint: str,
                 selection_sequence: int,
                 confidence: str) -> None:
        self.receipt = receipt
        self.candidates_eligible = list(candidates_eligible)
        self.excluded_reasons = dict(excluded_reasons)
        self.policy_fingerprint = policy_fingerprint
        self.selection_sequence = int(selection_sequence)
        self.confidence = confidence


def _confidence_for(task_risk: str, candidates_eligible: Sequence[str],
                    quality_evidence_present: bool) -> str:
    """Canonical confidence semantics (recovered): HIGH risk with
    insufficient quality evidence fails closed at LOW confidence so the
    caller knows the selection is not trustworthy for high-risk work."""
    if not candidates_eligible:
        return CONFIDENCE_LOW
    if not quality_evidence_present:
        return CONFIDENCE_LOW
    if task_risk == "HIGH":
        return CONFIDENCE_MEDIUM if quality_evidence_present else CONFIDENCE_LOW
    if len(candidates_eligible) >= 2:
        return CONFIDENCE_HIGH
    return CONFIDENCE_MEDIUM


class SelectionPolicy:
    """Stateless per-call policy; reselection state is carried in the
    prior receipt chain (no hidden mutable service)."""
    def __init__(
        self,
        *,
        reasoning_effort_classes: Sequence[str] = REASONING_EFFORT_CLASSES,
        reselection_cap: int = DEFAULT_RESELECTION_CAP,
        default_quality_floor: str = "MIXED",
        default_effort: str = UNKNOWN,
    ) -> None:
        for c in reasoning_effort_classes:
            if c not in REASONING_EFFORT_CLASSES:
                raise SelectionPolicyError(
                    f"REASONING_EFFORT_CLASS_INVALID: {c}")
        self.reasoning_effort_classes = tuple(reasoning_effort_classes)
        if int(reselection_cap) < 1:
            raise SelectionPolicyError("RESELECTION_CAP_TOO_SMALL")
        self.reselection_cap = int(reselection_cap)
        if default_quality_floor not in ("VERIFIED_HIGH", "VERIFIED",
                                         "MIXED", UNKNOWN, "FAILED"):
            raise SelectionPolicyError("DEFAULT_QUALITY_FLOOR_INVALID")
        self.default_quality_floor = default_quality_floor
        if default_effort not in REASONING_EFFORT_CLASSES:
            if default_effort != UNKNOWN:
                raise SelectionPolicyError("DEFAULT_EFFORT_INVALID")
        self.default_effort = default_effort

    # -----------------------------------------------------------------
    # Reselection gate (scenario Q/R/S)
    # -----------------------------------------------------------------
    def validate_reselection(
        self,
        *,
        request: SelectionRequest,
        prior_receipt: SelectionReceipt | None,
        failure_classification: str | None,
        mutation_state_verified: bool,
        stale_revision_ok: bool,
        prior_receipts: Sequence[SelectionReceipt] | None = None,
        next_target_id: str | None = None,
    ) -> SelectionReceipt | None:
        """Scenario Q/R/S: structured reselection only. Without a prior
        receipt this is a first selection (returns None). With a prior
        receipt, all reselection preconditions must hold or the policy
        fails closed. Follows the C21 safe_reselection_allowed pattern
        and reuses the C36 loop-guard spirit (count cap + oscillation)."""
        if prior_receipt is None:
            return None  # first selection, no reselection gate
        if failure_classification not in KNOWN_FAILURE_CLASSES:
            raise SelectionPolicyError(
                "RESELECTION_BLOCKED_MUTATION_UNKNOWN")
        if not mutation_state_verified:
            raise SelectionPolicyError(
                "RESELECTION_BLOCKED_MUTATION_UNKNOWN")
        # reselection count cap (C36 loop-guard reuse: bounded attempts)
        count = self._reselection_count(prior_receipt,
                                        prior_receipts)
        if count >= self.reselection_cap:
            raise SelectionPolicyError("RESELECTION_BLOCKED_LOOP")
        # oscillation guard (scenario S): A -> B -> A on the same role.
        # Prior receipts (oldest first) carry the visible history plus
        # the most recent prior selection. The INTENDED next selection
        # (next_target_id) is the deterministic optimization winner of
        # the same candidate set - if it already appears in that
        # history we would be returning to a previously selected
        # target and the loop is blocked.
        history_targets = {r.selected_target
                           for r in [prior_receipt] + list(prior_receipts or ())
                           if r.selected_target not in ("", UNKNOWN, None)}
        if next_target_id is not None and next_target_id in history_targets:
            raise SelectionPolicyError("RESELECTION_BLOCKED_LOOP")
        # stale revision guard: the request must be newer than the prior
        # receipt; a stale/identical revision is fail-closed unless the
        # owner explicitly allowed stale revisions.
        if not stale_revision_ok:
            prior_sequence = prior_receipt.to_dict().get("sequence", 1)
            if request.request_revision <= prior_sequence:
                raise SelectionPolicyError(
                    "RESELECTION_BLOCKED_MUTATION_UNKNOWN")
        return prior_receipt

    @staticmethod
    def _reselection_count(
            prior_receipt: SelectionReceipt,
            prior_receipts: Sequence[SelectionReceipt] | None = None
    ) -> int:
        """Reselection count = number of prior governed selection
        runs visible in the receipt chain (the current prior plus
        its ancestors). First reselection therefore produces
        sequence 2."""
        if prior_receipt is None:
            return 0
        return 1 + len(list(prior_receipts or ()))

    # -----------------------------------------------------------------
    # Eligibility stage
    # -----------------------------------------------------------------
    def eligibility_requirements(
            self, request: SelectionRequest) -> EligibilityRequirements:
        """Derive the eligibility requirements strictly from the
        request. Never invented, never inherited from vendor data."""
        oc = request.owner_constraints
        return EligibilityRequirements(
            required_capabilities=request.required_capabilities,
            required_certifications=(),
            required_auth_facts={},
            permission_profile=request.permission_needs,
            required_environment=str(
                getattr(request, "expected_environment", "") or UNKNOWN),
            required_context_capabilities=(),
            prohibited_provider_families=oc.prohibited_provider_families,
            minimum_quality_class=_quality_floor_for(
                request.quality_floor, self.default_quality_floor),
            reasoning_effort_class=request.reasoning_effort
            if request.reasoning_effort != UNKNOWN else UNKNOWN,
        )

    def filter_candidates(
            self,
            requirements: EligibilityRequirements,
            candidates: Sequence[SelectionCandidateEvidence]) -> tuple[
                list[SelectionCandidateEvidence], dict[str, str]]:
        """Eligibility stage. Returns (eligible, excluded_map).
        UNKNOWN vendor families are NEVER excluded (provider
        neutrality). A candidate eligible only because of an UNKNOWN
        field stays eligible but confidence degrades downstream."""
        eligible, excluded = [], {}
        for cand in candidates:
            decision: FilterDecision = filter_target(requirements, cand)
            if decision.eligible:
                eligible.append(cand)
            else:
                excluded[cand.target_id] = decision.reason
        return eligible, excluded

    # -----------------------------------------------------------------
    # Quality / risk gate
    # -----------------------------------------------------------------
    def next_selection_target(
            self,
            request: SelectionRequest,
            candidates: Sequence[SelectionCandidateEvidence]) -> str:
        """Deterministic optimization winner WITHOUT side effects.
        Used by the oscillation guard; selection itself re-runs the full
        pipeline (same inputs -> same winner, deterministic)."""
        requirements = self.eligibility_requirements(request)
        eligible, _ = self.filter_candidates(requirements, candidates)
        gated, _ = self.quality_risk_gate(request, eligible)
        ordered = self.optimize_order(gated)
        return ordered[0].target_id if ordered else UNKNOWN

    def quality_risk_gate(
            self,
            request: SelectionRequest,
            eligible: Sequence[SelectionCandidateEvidence]) -> tuple[
                list[SelectionCandidateEvidence], dict[str, str]]:
        """Hard quality floor + task-risk sufficiency. Candidates failing
        the gate are EXCLUDED with a quality reason - never demoted
        silently. High risk + no quality evidence -> fail closed."""
        remaining, excluded = [], {}
        floor = _quality_floor_for(request.quality_floor,
                                   self.default_quality_floor)
        task_risk = request.risk_class
        for cand in eligible:
            qc = cand.quality_class
            if qc == UNKNOWN:
                excluded[cand.target_id] = (
                    "QUALITY_UNKNOWN: no observed quality evidence")
                continue
            if quality_floor_violated(qc, floor):
                excluded[cand.target_id] = (
                    f"QUALITY_BELOW_FLOOR: {qc} below {floor}")
                continue
            remaining.append(cand)
        return remaining, excluded

    # -----------------------------------------------------------------
    # Optimization: lexicographic, inspectable, no opaque score
    # -----------------------------------------------------------------
    @staticmethod
    def optimize_order(
            eligible: Sequence[SelectionCandidateEvidence]) -> list[
                SelectionCandidateEvidence]:
        """VERIFIED QUALITY -> RELIABILITY (rework cost asc) ->
        TIME-TO-DONE (latency asc) -> COST (asc) -> TOKEN EFFICIENCY.
        Ties break on target_id lexicographically - stable,
        non-vendor, deterministic (scenario O)."""
        def _key(c: SelectionCandidateEvidence):
            q = quality_order(c.quality_class) if \
                c.quality_class in ("VERIFIED_HIGH", "VERIFIED",
                                    "MIXED", UNKNOWN, "FAILED") else 0
            rc = _number(getattr(c, "rework_cost_ratio", float("nan")))
            lt = _number(getattr(c, "latency_seconds", float("nan")))
            co = _number(c.cost_usd)
            te = _number(getattr(c, "input_tokens", float("nan"))) \
                + _number(getattr(c, "output_tokens", float("nan")))
            return (-q,
                    rc if not _is_nan(rc) else float("inf"),
                    lt if not _is_nan(lt) else float("inf"),
                    co if not _is_nan(co) else float("inf"),
                    te if not _is_nan(te) else float("-inf"),
                    c.target_id)
        return sorted(eligible, key=_key)

    # -----------------------------------------------------------------
    # Model binding (scenario I/J)
    # -----------------------------------------------------------------
    @staticmethod
    def bind_model(request: SelectionRequest,
                   candidate: SelectionCandidateEvidence,
                   *,
                   model_binding_required: bool = False,
                   ) -> tuple[str, str]:
        """Return (selected_model, decision_reason). UNKNOWN models are
        never invented. If the request REQUIRES exact model binding and
        the candidate offers no observable model -> UNKNOWN with an
        excluded-level reason (caller excludes) (scenario I). When
        binding is optional, an unobservable candidate remains eligible
        with model UNKNOWN (scenario J)."""
        if model_binding_required and not candidate.observable_model:
            return UNKNOWN, "MODEL_OBSERVABILITY_REQUIRED_MISSING"
        if candidate.observable_model:
            return (candidate.model_id
                    if candidate.model_id not in ("", UNKNOWN)
                    else UNKNOWN), "MODEL_FROM_CANDIDATE_EVIDENCE"
        return UNKNOWN, "MODEL_NOT_BOUND"

    # -----------------------------------------------------------------
    # Reasoning effort binding (provider-neutral classes only)
    # -----------------------------------------------------------------
    def bind_reasoning_effort(
            self,
            request: SelectionRequest,
            candidate: SelectionCandidateEvidence,
            task_risk: str) -> tuple[str, str]:
        """Return (effort, decision_reason). Effort is always one of the
        four neutral classes and must be supported by the candidate;
        owner ceiling and task risk shape the choice, never vendor
        flags."""
        supported = _as_set(candidate.reasoning_effort_classes)
        ceiling = str(request.owner_constraints.maximum_reasoning_effort)
        if ceiling == UNKNOWN:
            ceiling = self.default_effort
        if task_risk == "HIGH":
            desired = HIGH_EFFORT
        elif task_risk == "MATERIAL":
            desired = MEDIUM_EFFORT
        else:
            desired = (request.reasoning_effort
                       if request.reasoning_effort != UNKNOWN
                       else LOW_EFFORT)
        order = {LOW_EFFORT: 0, MEDIUM_EFFORT: 1,
                 HIGH_EFFORT: 2, VERY_HIGH_EFFORT: 3}
        if ceiling in order and desired in order \
                and order[desired] > order[ceiling]:
            desired = ceiling
        if desired not in (supported if supported else
                           REASONING_EFFORT_CLASSES):
            if supported:
                chosen = sorted(supported, key=lambda e: order.get(e, 9))[0]
                return chosen, "EFFORT_LOWEST_SUPPORTED"
            return UNKNOWN, "EFFORT_NOT_BOUND"
        return desired, "EFFORT_FROM_RISK_AND_OWNER"

    # -----------------------------------------------------------------
    # The pipeline
    # -----------------------------------------------------------------
    def select(
        self,
        request: SelectionRequest,
        candidates: Sequence[SelectionCandidateEvidence],
        *,
        prior_receipt: SelectionReceipt | None = None,
        failure_classification: str | None = None,
        mutation_state_verified: bool = True,
        stale_revision_ok: bool = False,
        decision_trace_root: str | None = None,
        run_id: str | None = None,
        owner_approval_ref: Any = None,
        prior_receipts: Sequence[SelectionReceipt] | None = None,
    ) -> SelectionOutcome:
        """Full evidence-bound selection pipeline. Scenario A-X."""
        # 0. Reselection gate (first selection when prior is None)
        # Deterministic next target is computed once and passed to the
        # gate so the oscillation check and the final decision are
        # byte-for-byte identical (no two optimization passes can
        # disagree on sorted input).
        next_target = (self.next_selection_target(request, candidates)
                       if prior_receipt is not None else None)
        self.validate_reselection(
            request=request, prior_receipt=prior_receipt,
            failure_classification=failure_classification,
            mutation_state_verified=mutation_state_verified,
            stale_revision_ok=stale_revision_ok,
            prior_receipts=prior_receipts,
            next_target_id=next_target)

        requirements = self.eligibility_requirements(request)
        eligible, excluded = self.filter_candidates(requirements, candidates)

        # 1. Quality/risk gate
        gated, quality_excluded = self.quality_risk_gate(request, eligible)
        excluded.update(quality_excluded)

        # 2. Optimization
        ordered = self.optimize_order(gated)

        # 3. Decide
        sequence = (self._reselection_count(prior_receipt,
                                            prior_receipts) + 1)
        if decision_trace_root:
            capture_material_decision(
                decision_trace_root,
                request=selection_request_text(
                    request.request_id, request.request_revision),
                goal_id=request.goal_id, run_id=run_id,
                workflow_status="SELECTING",
                outcome=TARGET_ELIGIBLE if ordered else NO_ELIGIBLE_TARGET,
                evidence_refs=[f"candidate:{c.target_id}" for c in candidates],
                policy_refs=[POLICY_VERSION],
                decision_type="ARCHITECTURE",
                owner_approval_ref=owner_approval_ref,
            )

        if not ordered:
            trace_pointer = decision_trace_root or ""
            receipt = build_selection_receipt(
                request_id=request.request_id,
                goal_id=request.goal_id, task_id=request.task_id,
                role_id=request.role_id,
                candidates_considered=[c.target_id for c in candidates],
                candidates_excluded=list(excluded),
                exclusion_reasons=[NO_ELIGIBLE_TARGET] if not excluded
                else list(excluded.values()),
                decision_trace_pointer=trace_pointer,
                outcome=BLOCKED, sequence=sequence)
            task_risk = request.risk_class
            confidence = CONFIDENCE_LOW if task_risk != "HIGH" \
                else CONFIDENCE_UNKNOWN
            return SelectionOutcome(
                receipt=receipt, candidates_eligible=[],
                excluded_reasons=excluded,
                policy_fingerprint=receipt.policy_fingerprint,
                selection_sequence=sequence, confidence=confidence)

        chosen = ordered[0]
        model_binding_required = request.verification_requirement in (
            "INDEPENDENT", "CERTIFIED")
        model, model_reason = self.bind_model(
            request, chosen, model_binding_required=model_binding_required)
        task_risk = request.risk_class
        effort, effort_reason = self.bind_reasoning_effort(
            request, chosen, task_risk)

        quality_ptrs = [f"quality:{chosen.target_id}"] if \
            chosen.quality_class not in ("", UNKNOWN) else []
        cert_ptrs = list(chosen.certification_refs)
        eff_ptrs = [f"efficiency:{chosen.target_id}"] if not \
            _is_nan(_number(chosen.cost_usd)) else []
        if decision_trace_root:
            capture_material_decision(
                decision_trace_root,
                request=f"{TARGET_SELECTED}: {chosen.target_id}",
                goal_id=request.goal_id, run_id=run_id,
                workflow_status="SELECTING", outcome=TARGET_SELECTED,
                evidence_refs=[f"candidate:{chosen.target_id}"],
                policy_refs=[POLICY_VERSION],
                decision_type="ARCHITECTURE",
                owner_approval_ref=owner_approval_ref)
            if model != UNKNOWN:
                capture_material_decision(
                    decision_trace_root,
                    request=f"{MODEL_SELECTED}: {model}",
                    goal_id=request.goal_id, run_id=run_id,
                    workflow_status="SELECTING", outcome=MODEL_SELECTED,
                    evidence_refs=[f"candidate:{chosen.target_id}"],
                    policy_refs=[POLICY_VERSION],
                    decision_type="ARCHITECTURE",
                    owner_approval_ref=owner_approval_ref)
            capture_material_decision(
                decision_trace_root,
                request=f"{REASONING_EFFORT_SELECTED}: {effort}",
                goal_id=request.goal_id, run_id=run_id,
                workflow_status="SELECTING",
                outcome=REASONING_EFFORT_SELECTED,
                evidence_refs=[f"candidate:{chosen.target_id}"],
                policy_refs=[POLICY_VERSION],
                decision_type="ARCHITECTURE",
                owner_approval_ref=owner_approval_ref)

        receipt = build_selection_receipt(
            request_id=request.request_id,
            goal_id=request.goal_id, task_id=request.task_id,
            role_id=request.role_id,
            candidates_considered=[c.target_id for c in candidates],
            candidates_excluded=list(excluded),
            exclusion_reasons=list(excluded.values()),
            selected_target=chosen.target_id,
            selected_model=model,
            selected_reasoning_effort=effort,
            quality_evidence_pointers=quality_ptrs,
            efficiency_evidence_pointers=eff_ptrs,
            certification_pointers=cert_ptrs,
            auth_state=str(
                "VERIFIED" if chosen.auth_evidence else UNKNOWN),
            permission_profile=list(chosen.permission_profile),
            decision_trace_pointer=decision_trace_root or "",
            outcome=SELECTED, sequence=sequence,
            policy_fingerprint_extra={"model_reason": model_reason,
                                      "effort_reason": effort_reason})
        confidence = _confidence_for(task_risk, [chosen.target_id],
                                     bool(quality_ptrs))
        return SelectionOutcome(
            receipt=receipt, candidates_eligible=[c.target_id for c in ordered],
            excluded_reasons=excluded,
            policy_fingerprint=receipt.policy_fingerprint,
            selection_sequence=sequence, confidence=confidence)


def build_selection_policy(**kwargs: Any) -> SelectionPolicy:
    return SelectionPolicy(**kwargs)
