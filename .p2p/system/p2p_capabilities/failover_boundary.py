# failover_boundary.py — P2P-C39
#
# Failover-boundary decision surface.  The ONLY new runtime surface in C39.
#
# It decides the next safe action for a bounded live target using:
#   - the C37 selection receipt (selection authority — consumed, never duplicated)
#   - the C34 backend contract error taxonomy + execution/verification statuses
#   - the C36 context capsule evidence (mutation state, evidence pointers)
#   - the C35 verifier verdict (verification authority — consumed, never duplicated)
#   - the C33 Continue Gate's owner-gate semantics (OWNER_GATE reuse)
#
# Authority boundaries preserved (no duplication):
#   REGISTRY != ROUTER :: SELECTION != EXECUTION :: FAILOVER != RETRY
#   CLAIM != EVIDENCE  :: TRANSCRIPT != STATE :: UNKNOWN != SAFE
#
# Decision outputs (exactly one):
#   RETRY_SAME_TARGET   - retry against the SAME target (material retry evidence)
#   RESELECT_TARGET     - safe reselection onto another currently-eligible target
#   REVERIFY_REQUIRED   - must reverify/inspect before anything else
#   OWNER_GATE          - decision requires an Owner action (credential/etc.)
#   STOP_FAIL_CLOSED    - stop; do not switch, do not retry, do not claim safety
#
# Fail-closed rules:
#   * UNKNOWN inputs fail closed.
#   * UNKNOWN never silently becomes RESELECT_TARGET.
#   * MUTATION_UNKNOWN / RESULT_UNKNOWN after dispatch -> REVERIFY_REQUIRED or
#     STOP_FAIL_CLOSED.  Backend B MUST NOT execute in these states.
#   * A silent switch is always a policy violation (no_switch violation).

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

from p2p_capabilities.backend_contract import (
    BackendContractError,
    EXECUTION_ERROR_CLASSES,
    _limited_text,
    _hex64,
)

# ---------------------------------------------------------------------------
# Taxonomy: input failure classes (superset of backend_contract classes)

FAILOVER_FAILURE_CLASSES = (
    # pre-dispatch failure classes
    "PRE_DISPATCH_FAILURE",
    "PRE_DISPATCH_REJECTED",
    "AUTH_FAILED_BEFORE_MODEL_CONTACT",
    "TARGET_INELIGIBLE_BEFORE_EXECUTION",
    "CONTEXT_STALE_BEFORE_DISPATCH",
    "PERMISSION_CHANGED_BEFORE_DISPATCH",
    "CAPABILITY_CHANGED_BEFORE_DISPATCH",
    # post-dispatch failure classes
    "POST_DISPATCH_FAILURE",
    # auth / drift classes
    "AUTH_DRIFT",
    "AUTH_INVALID",          # from backend_contract EXECUTION_ERROR_CLASSES
    "AUTH_REQUIRED",
    "TARGET_DRIFT",
    "PERMISSION_DRIFT",
    "CONTEXT_STALE",
    "PERMISSION_CHANGED",
    "CAPABILITY_CHANGED",
    # environment classes
    "NETWORK_FAILURE",
    "RATE_LIMIT",
    "TIMEOUT",
    "UNAVAILABLE",
    # verification classes
    "VERIFICATION_FAILURE",
    "VERIFIED_NON_MUTATING_TERMINAL_FAILURE",
    # unknown classes
    "MUTATION_UNKNOWN",
    "RESULT_UNKNOWN",
    "RESULT_UNKNOWN_AFTER_DISPATCH",
    "TIMEOUT_AFTER_POSSIBLE_MUTATION",
    "WORKSPACE_STATE_UNKNOWN",
    "UNVERIFIED_WRITE",
    "EXTERNAL_SIDE_EFFECT_UNKNOWN",
    "PERMISSION_STATE_UNKNOWN",
    "CONTRADICTED_EVIDENCE",
    # adapter error classes pass through
    "CONTRACT_REJECTED",
    "PERMISSION_DENIED",
)

# ---------------------------------------------------------------------------
# Decision outputs

FAILOVER_DECISIONS = (
    "RETRY_SAME_TARGET",
    "RESELECT_TARGET",
    "REVERIFY_REQUIRED",
    "OWNER_GATE",
    "STOP_FAIL_CLOSED",
)

# Classes that can NEVER yield RESELECT_TARGET (unsafe evidence set)
_UNSAFE_FOR_RESELECTION = frozenset((
    "MUTATION_UNKNOWN",
    "RESULT_UNKNOWN",
    "RESULT_UNKNOWN_AFTER_DISPATCH",
    "TIMEOUT_AFTER_POSSIBLE_MUTATION",
    "WORKSPACE_STATE_UNKNOWN",
    "UNVERIFIED_WRITE",
    "EXTERNAL_SIDE_EFFECT_UNKNOWN",
    "PERMISSION_STATE_UNKNOWN",
    "CONTRADICTED_EVIDENCE",
    "POST_DISPATCH_FAILURE",
))

# Classes that ARE safe evidence for automatic reselection (not-dispatched proofs)
_SAFE_RESELECTION_EVIDENCE = frozenset((
    "PRE_DISPATCH_FAILURE",
    "PRE_DISPATCH_REJECTED",
    "AUTH_FAILED_BEFORE_MODEL_CONTACT",
    "TARGET_INELIGIBLE_BEFORE_EXECUTION",
    "VERIFIED_NON_MUTATING_TERMINAL_FAILURE",
    "AUTH_DRIFT",            # drift detected BEFORE dispatch is safe to reselect on
    "AUTH_INVALID",
    "AUTH_REQUIRED",
    "TARGET_INELIGIBLE_BEFORE_EXECUTION",
))

# Retry-relevant transient classes: same target may be retried WITH LoopGuard.
_RETRY_SAME_TARGET_EVIDENCE = frozenset((
    "NETWORK_FAILURE",
    "RATE_LIMIT",
    "TIMEOUT",
    "UNAVAILABLE",
))


_ALL_KNOWN_CLASSES = frozenset(FAILOVER_FAILURE_CLASSES) | {"FAILURE_CLASS_UNKNOWN"}

@dataclass(frozen=True)
class FailoverDecision:
    """Failover-boundary decision record.  Unknown inputs fail closed."""

    decision: str
    failure_class: str | None
    failure_class_observed: tuple[str, ...] = ()
    revision: str = ""
    old_target: str = ""
    new_target: str = ""
    old_receipt_pointer: str = ""
    new_receipt_pointer: str = ""
    reason: str = ""
    mutation_status: str = ""
    evidence_pointers: tuple[str, ...] = ()
    details: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.decision not in FAILOVER_DECISIONS:
            raise BackendContractError(f"FAILOVER_DECISION_INVALID:{self.decision}")
        _limited_text(self.decision, "decision", 64)
        if self.failure_class is not None and self.failure_class not in _ALL_KNOWN_CLASSES:
            raise BackendContractError(f"FAILOVER_FAILURE_CLASS_INVALID:{self.failure_class}")
        for fc in self.failure_class_observed:
            if fc not in _ALL_KNOWN_CLASSES:
                raise BackendContractError(f"FAILOVER_FAILURE_CLASS_INVALID:{fc}")
        if self.old_target:
            _limited_text(self.old_target, "old_target", 256)
        if self.new_target:
            _limited_text(self.new_target, "new_target", 256)
        if self.mutation_status and self.mutation_status not in (
            "NO_MUTATION_OBSERVED", "MUTATION_OBSERVED", "MUTATION_UNKNOWN",
            "MUTATION_POSSIBLE", "NON_MUTATING_BOUNDED"):
            raise BackendContractError(f"FAILOVER_MUTATION_STATUS_INVALID:{self.mutation_status}")
        if not isinstance(self.evidence_pointers, tuple):
            raise BackendContractError("FAILOVER_EVIDENCE_MUST_BE_TUPLE")
        if not isinstance(self.details, Mapping):
            raise BackendContractError("FAILOVER_DETAILS_MUST_BE_OBJECT")

    # ------------------------------------------------------------------
    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "p2p-failover-decision/1",
            "decision": self.decision,
            "failure_class": self.failure_class,
            "failure_class_observed": list(self.failure_class_observed),
            "revision": self.revision,
            "old_target": self.old_target,
            "new_target": self.new_target,
            "old_receipt_pointer": self.old_receipt_pointer,
            "new_receipt_pointer": self.new_receipt_pointer,
            "reason": self.reason,
            "mutation_status": self.mutation_status,
            "evidence_pointers": list(self.evidence_pointers),
            "details": {k: v for k, v in self.details.items()},
        }


# ---------------------------------------------------------------------------
# Decision-revision tracking (oscillation guard + no-silent-switch)

def failover_revision(old_target: str, new_target: str, reason: str) -> str:
    """Deterministic revision id for a failover decision."""
    _limited_text(old_target, "old_target", 256)
    _limited_text(new_target, "new_target", 256)
    _limited_text(reason, "reason", 1024)
    payload = json.dumps([old_target, new_target, reason], sort_keys=True, ensure_ascii=False)
    return "revision-" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


def selection_revision(selection_receipt_id: str, reason: str) -> str:
    """Deterministic revision id for a new selection receipt (reselection)."""
    _limited_text(selection_receipt_id, "selection_receipt_id", 256)
    _limited_text(reason, "reason", 1024)
    payload = json.dumps([selection_receipt_id, reason], sort_keys=True, ensure_ascii=False)
    return "reselect-" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


# ---------------------------------------------------------------------------
# Pre-dispatch revalidation

class EligibilityProbeError(RuntimeError):
    """Raised when an eligibility probe cannot establish a definite state."""


@dataclass(frozen=True)
class EligibilitySnapshot:
    """Point-in-time eligibility evidence for a backend target.

    A probe records a definite state (eligible / ineligible) with evidence
    pointers.  If the probe cannot determine a state, snapshot_eligible()
    returns None -> callers treat it as UNKNOWN and fail closed.
    """

    target: str
    eligible: bool
    failure_class: str | None = None
    evidence_pointers: tuple[str, ...] = ()
    detail: str = ""

    def __post_init__(self) -> None:
        _limited_text(self.target, "target", 256)
        for fc in (self.failure_class,) if self.failure_class else ():
            if fc not in _ALL_KNOWN_CLASSES:
                raise BackendContractError(f"FAILOVER_FAILURE_CLASS_INVALID:{fc}")
        if not isinstance(self.evidence_pointers, tuple):
            raise BackendContractError("ELIGIBILITY_EVIDENCE_MUST_BE_TUPLE")


def snapshot_eligibility(
    target: str,
    probe: Any | None = None,
) -> EligibilitySnapshot | None:
    """Probe a target for current eligibility via a C39-provided probe callable.

    probe(target) must return either an EligibilitySnapshot or None when the
    state cannot be established (treated as UNKNOWN -> fail closed).
    """
    if probe is None:
        return None
    try:
        result = probe(target)
    except Exception:
        return None
    if result is None or not isinstance(result, EligibilitySnapshot):
        return None
    return result


# ---------------------------------------------------------------------------
# The decision machine.

def _classify(fc: str) -> str:
    """Normalize an observed failure class into a canonical one.

    Classes the machine does not recognize are NOT silently accepted as
    canonical; they are mapped to a fail-closed UNKNOWN holder so the
    decision record stays within the schema.  Callers can still inspect
    failure_class_observed for the raw value.
    """
    if fc in FAILOVER_FAILURE_CLASSES:
        return fc
    return "FAILURE_CLASS_UNKNOWN"



def decide_next_action(
    *,
    failure_class: str | None,
    failure_class_observed: Iterable[str] = (),
    mutation_status: str = "",
    verification_status: str = "",
    dispatched: bool | None = None,
    prior_receipt: Mapping[str, Any] | None = None,
    current_target: str = "",
    eligible_targets: Iterable[str] = (),
    owner_action_needed: bool = False,
    revalidation_snapshot: EligibilitySnapshot | None = None,
) -> FailoverDecision:
    """The failover-boundary decision machine.  Fail-closed by construction.

    Decision order (each rule is deterministic, no floating logic):

    1. No failure given -> RETRY_SAME_TARGET is NOT emitted.  The machine only
       responds to recorded failure classes; absence of failure is a no-op
       caller case (caller dispatches normally).
    2. OWNER action needed -> OWNER_GATE.
    3. Unknown failure class / unknown mutation / unknown dispatch state ->
       STOP_FAIL_CLOSED when dispatch occurred; REVERIFY_REQUIRED otherwise.
    4. Unsafe evidence set (MUTATION_UNKNOWN / RESULT_UNKNOWN after dispatch) ->
       REVERIFY_REQUIRED if prior_receipt shows a verifiable result pointer,
       else STOP_FAIL_CLOSED.  Backend B MUST NOT execute.
    5. Safe reselection evidence (not-dispatched proofs) -> RESELECT_TARGET
       when an eligible alternative exists; else OWNER_GATE if auth failure,
       else STOP_FAIL_CLOSED.
    6. Transient environment failures -> RETRY_SAME_TARGET (caller applies
       LoopGuard + backoff; retries require material new evidence).
    7. Verification failure -> REVERIFY_REQUIRED.
    8. Drift detected pre-dispatch -> RESELECT_TARGET on eligible alternative.
    """
    observed = tuple(str(fc) for fc in failure_class_observed)
    primary = _classify(str(failure_class)) if failure_class else None

    # Rule 2: Owner gate outranks everything else.
    if owner_action_needed:
        return FailoverDecision(
            decision="OWNER_GATE",
            failure_class=primary,
            failure_class_observed=observed,
            reason="OWNER_ACTION_REQUIRED:" + str(primary or "unknown"),
            mutation_status=mutation_status,
            old_target=current_target,
        )

    unsafe = bool((set(observed) | ({primary} if primary else set())) & _UNSAFE_FOR_RESELECTION) or primary == "FAILURE_CLASS_UNKNOWN"

    # Rule 3: unclassifiable failure class with known dispatch state fails
    # closed (dispatch occurred) or requires re-verification (dispatch
    # unknown).  With dispatched=None the unknown-class case falls through
    # to the dispatch-unknown block below, which emits REVERIFY_REQUIRED.
    if dispatched is not None and dispatched and primary == "FAILURE_CLASS_UNKNOWN":
        pointers = ()
        if isinstance(prior_receipt, Mapping):
            op = prior_receipt.get("output_pointers", ()) or ()
            pointers = tuple(str(p) for p in (op if not isinstance(op, str) else (op,)))
        if pointers:
            return FailoverDecision(
                decision="REVERIFY_REQUIRED",
                failure_class=primary,
                failure_class_observed=observed,
                reason="UNRECOGNIZED_FAILURE_CLASS_AFTER_DISPATCH_WITH_POINTERS",
                mutation_status=mutation_status,
                old_target=current_target,
                evidence_pointers=pointers,
            )
        return FailoverDecision(
            decision="STOP_FAIL_CLOSED",
            failure_class=primary,
            failure_class_observed=observed,
            reason="FAILURE_CLASS_UNRECOGNIZED_AFTER_DISPATCH",
            mutation_status=mutation_status,
            old_target=current_target,
        )
    if dispatched is None:
        # Dispatch state unknown -> anything that touched dispatch is unsafe.
        if unsafe:
            return FailoverDecision(
                decision="REVERIFY_REQUIRED",
                failure_class=primary,
                failure_class_observed=observed,
                reason="DISPATCH_STATE_UNKNOWN_WITH_UNSAFE_EVIDENCE",
                mutation_status=mutation_status,
                old_target=current_target,
            )
        if primary is None:
            return FailoverDecision(
                decision="STOP_FAIL_CLOSED",
                failure_class=None,
                failure_class_observed=observed,
                reason="NO_ACTION_WITHOUT_RECORDED_FAILURE_AND_UNKNOWN_DISPATCH_STATE",
                mutation_status=mutation_status,
                old_target=current_target,
            )
        # fall through with dispatched=False semantics for transient classes
        dispatched = False

    # Rule 4: unsafe post-dispatch states.
    if unsafe:
        pointers = ()
        if isinstance(prior_receipt, Mapping):
            pointers = tuple(
                str(p) for p in prior_receipt.get("output_pointers", ()) or ()
            )
            if isinstance(prior_receipt.get("output_pointers", ()), str):
                pointers = (prior_receipt["output_pointers"],)
        if pointers:
            return FailoverDecision(
                decision="REVERIFY_REQUIRED",
                failure_class=primary,
                failure_class_observed=observed,
                reason="UNSAFE_AFTER_DISPATCH_WITH_RESULT_POINTERS",
                mutation_status=mutation_status,
                old_target=current_target,
                evidence_pointers=pointers,
            )
        return FailoverDecision(
            decision="STOP_FAIL_CLOSED",
            failure_class=primary,
            failure_class_observed=observed,
            reason="UNSAFE_AFTER_DISPATCH_NO_VERIFICATION_POSSIBLE",
            mutation_status=mutation_status,
            old_target=current_target,
        )

    # Rule 7: verification failure.
    if primary in ("VERIFICATION_FAILURE",) or "VERIFICATION_FAILURE" in observed:
        return FailoverDecision(
            decision="REVERIFY_REQUIRED",
            failure_class=primary,
            failure_class_observed=observed,
            reason="INDEPENDENT_VERIFICATION_REJECTED_EXECUTION",
            mutation_status=mutation_status,
            old_target=current_target,
        )

    # Rule 5: safe reselection evidence (not dispatched / auth failed before
    # model contact / target ineligible / verified non-mutating terminal).
    if primary in _SAFE_RESELECTION_EVIDENCE or bool(set(observed) & _SAFE_RESELECTION_EVIDENCE):
        eligible = [t for t in eligible_targets if str(t) != str(current_target)]
        if eligible:
            return FailoverDecision(
                decision="RESELECT_TARGET",
                failure_class=primary,
                failure_class_observed=observed,
                reason="SAFE_RESELECTION_EVIDENCE",
                mutation_status=mutation_status or "NO_MUTATION_OBSERVED",
                old_target=current_target,
                new_target=eligible[0],
                revision=selection_revision(str(current_target), str(primary)),
            )
        # No alternative -> owner gate when auth, else stop fail-closed.
        auth_fail = bool((set(observed) | ({primary} if primary else set()))
                         & {"AUTH_INVALID", "AUTH_REQUIRED", "AUTH_DRIFT"})
        if auth_fail:
            return FailoverDecision(
                decision="OWNER_GATE",
                failure_class=primary,
                failure_class_observed=observed,
                reason="AUTH_FAILURE_NO_ALTERNATIVE_TARGET",
                mutation_status=mutation_status or "NO_MUTATION_OBSERVED",
                old_target=current_target,
            )
        return FailoverDecision(
            decision="STOP_FAIL_CLOSED",
            failure_class=primary,
            failure_class_observed=observed,
            reason="SAFE_RESELECTION_EVIDENCE_NO_ELIGIBLE_ALTERNATIVE",
            mutation_status=mutation_status or "NO_MUTATION_OBSERVED",
            old_target=current_target,
        )

    # Rule 6: transient environment failures -> retry same target.
    if primary in _RETRY_SAME_TARGET_EVIDENCE or bool(set(observed) & _RETRY_SAME_TARGET_EVIDENCE):
        return FailoverDecision(
            decision="RETRY_SAME_TARGET",
            failure_class=primary,
            failure_class_observed=observed,
            reason="TRANSIENT_ENVIRONMENT_FAILURE_RETRY_WITH_LOOPGUARD",
            mutation_status=mutation_status or "NO_MUTATION_OBSERVED",
            old_target=current_target,
        )

    # Default: fail closed.
    return FailoverDecision(
        decision="STOP_FAIL_CLOSED",
        failure_class=primary,
        failure_class_observed=observed,
        reason="NO_KNOWN_SAFE_ACTION",
        mutation_status=mutation_status,
        old_target=current_target,
    )
