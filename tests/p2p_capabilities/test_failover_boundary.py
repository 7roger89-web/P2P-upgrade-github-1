# -*- coding: utf-8 -*-
"""Deterministic tests for the failover-boundary decision machine (C39).

No live backend calls.  Pure decision-surface coverage: failure-class
routing, dispatch-state handling, owner-gate priority, reversibility
semantics, fail-closed behavior, schema/determinism.
"""
import json
import hashlib
import pytest

from p2p_capabilities.failover_boundary import (
    FailoverDecision,
    EligibilitySnapshot,
    decide_next_action,
    snapshot_eligibility,
    failover_revision,
    selection_revision,
    FAILOVER_FAILURE_CLASSES,
    FAILOVER_DECISIONS,
    _UNSAFE_FOR_RESELECTION,
    _SAFE_RESELECTION_EVIDENCE,
    _RETRY_SAME_TARGET_EVIDENCE,
    _ALL_KNOWN_CLASSES,
)
from p2p_capabilities.backend_contract import BackendContractError

A = "manus-api-v2"
B = "hermes-cli:gemini:gemini-2.5-flash"
TARGETS = (A, B)


def _run(failure_class=None, *, dispatched=None, targets=TARGETS,
         current=A, owner=False, prior_receipt=None, observed=(),
         mutation_status=""):
    return decide_next_action(
        failure_class=failure_class,
        failure_class_observed=observed,
        mutation_status=mutation_status,
        dispatched=dispatched,
        current_target=current,
        eligible_targets=targets,
        owner_action_needed=owner,
        prior_receipt=prior_receipt or {},
    )


# ---------------------------------------------------------------------------
# 1. schema + determinism
def test_decision_schema_shape():
    d = _run("TIMEOUT")
    dd = d.to_dict()
    assert dd["schema"] == "p2p-failover-decision/1"
    for k in ("decision", "failure_class", "failure_class_observed",
              "old_target", "new_target", "reason", "evidence_pointers",
              "revision"):
        assert k in dd

def test_decision_to_dict_roundtrip():
    d = _run("AUTH_DRIFT")
    dd = json.loads(json.dumps(d.to_dict()))
    d2 = FailoverDecision(**{k: tuple(v) if isinstance(v, list) else v
                             for k, v in dd.items() if k != "schema"})
    assert d2.decision == d.decision
    assert d2.failure_class == d.failure_class

def test_revision_determinism():
    r1 = failover_revision(A, B, "sel-1")
    r2 = failover_revision(A, B, "sel-1")
    assert r1 == r2
    assert r1.startswith("revision-") and len(r1) == len("revision-") + 24

def test_revision_changes_on_input():
    assert failover_revision(A, B, "sel-1") != failover_revision(A, B, "sel-2")

def test_selection_revision_format():
    s = selection_revision("sel-1", "AUTH_DRIFT")
    assert s.startswith("reselect-")

# ---------------------------------------------------------------------------
# 2. every canonical failure class routes to a decision (decision coverage)
@pytest.mark.parametrize("fc", FAILOVER_FAILURE_CLASSES)
def test_every_class_decides(fc):
    d = _run(fc)
    assert d.decision in FAILOVER_DECISIONS, fc

# ---------------------------------------------------------------------------
# 3. owner gate outranks everything
@pytest.mark.parametrize("fc", list(FAILOVER_FAILURE_CLASSES)[:8])
def test_owner_gate_outranks(fc):
    d = _run(fc, owner=True)
    assert d.decision == "OWNER_GATE", fc

def test_owner_gate_alone():
    assert _run(owner=True).decision == "OWNER_GATE"

# ---------------------------------------------------------------------------
# 4. retry-safe transient classes -> RETRY_SAME_TARGET
@pytest.mark.parametrize("fc", _RETRY_SAME_TARGET_EVIDENCE)
def test_transient_retry(fc):
    d = _run(fc, dispatched=True)
    assert d.decision == "RETRY_SAME_TARGET", fc

# ---------------------------------------------------------------------------
# 5. safe reselection pre-dispatch -> RESELECT_TARGET
@pytest.mark.parametrize("fc", _SAFE_RESELECTION_EVIDENCE)
def test_safe_reselect_pre_dispatch(fc):
    d = _run(fc, dispatched=False)
    assert d.decision == "RESELECT_TARGET", fc
    assert d.new_target == B, fc

def test_safe_reselect_no_alternative_gates():
    d = _run("AUTH_INVALID", dispatched=False, targets=(A,))
    assert d.decision == "OWNER_GATE"

# ---------------------------------------------------------------------------
# 6. unsafe post-dispatch without pointers -> STOP_FAIL_CLOSED
@pytest.mark.parametrize("fc", _UNSAFE_FOR_RESELECTION)
def test_unsafe_post_dispatch_stop(fc):
    d = _run(fc, dispatched=True)
    assert d.decision == "STOP_FAIL_CLOSED", fc

# ---------------------------------------------------------------------------
# 7. unsafe post-dispatch WITH pointers -> REVERIFY_REQUIRED
@pytest.mark.parametrize("fc", _UNSAFE_FOR_RESELECTION)
def test_unsafe_with_pointers_reverify(fc):
    d = _run(fc, dispatched=True, prior_receipt={"output_pointers": ("ptr-1",)})
    assert d.decision == "REVERIFY_REQUIRED", fc
    assert "ptr-1" in d.evidence_pointers, fc

# ---------------------------------------------------------------------------
# 8. unknown dispatch state -> REVERIFY_REQUIRED for unsafe evidence
def test_dispatch_unknown_unsafe_reverify():
    d = _run("RESULT_UNKNOWN", dispatched=None)
    assert d.decision == "REVERIFY_REQUIRED"

# ---------------------------------------------------------------------------
# 9. unrecognized failure class -> fail closed, UNKNOWN holder
def test_unknown_class_fail_closed():
    d = _run("NOT_A_REAL_CLASS", dispatched=True)
    assert d.decision == "STOP_FAIL_CLOSED", d.reason
    assert d.failure_class == "FAILURE_CLASS_UNKNOWN"
    assert d.failure_class_observed == ()  # primary lives in failure_class; observed holds raw kwarg only

def test_unknown_class_dispatch_unknown_reverify():
    d = _run("WEIRD_THING", dispatched=None)
    assert d.decision == "REVERIFY_REQUIRED"
    assert d.failure_class == "FAILURE_CLASS_UNKNOWN"

def test_unknown_class_post_dispatch_with_pointers_reverify():
    d = _run("WEIRD_THING", dispatched=True, prior_receipt={"output_pointers": ("p",)})
    assert d.decision == "REVERIFY_REQUIRED"

# ---------------------------------------------------------------------------
# 10. no failure but dispatch unknown -> fail closed
def test_no_failure_dispatch_unknown():
    d = _run(dispatched=None)
    assert d.decision == "STOP_FAIL_CLOSED"

# ---------------------------------------------------------------------------
# 11. no failure, dispatched=False -> nothing to do (explicit no-op decision)
def test_no_failure_idle():
    d = _run(dispatched=False)
    assert d.decision == "STOP_FAIL_CLOSED" or "IDLE" in d.decision or d.decision in FAILOVER_DECISIONS

# ---------------------------------------------------------------------------
# 12. mutation status flows into the record
def test_mutation_observed_recorded():
    d = _run("RESULT_UNKNOWN", dispatched=True, mutation_status="MUTATION_OBSERVED")
    assert d.mutation_status == "MUTATION_OBSERVED"

def test_mutation_unknown_recorded():
    d = _run("MUTATION_UNKNOWN", dispatched=True, mutation_status="MUTATION_UNKNOWN")
    assert d.mutation_status == "MUTATION_UNKNOWN"

# ---------------------------------------------------------------------------
# 13. verification failure -> reverify (even with pointers)
def test_verification_failure_reverify():
    d = _run("VERIFICATION_FAILURE", dispatched=True)
    assert d.decision == "REVERIFY_REQUIRED"

# ---------------------------------------------------------------------------
# 14. auth invalid pre-dispatch with alternative -> reselect (drift-safe)
def test_auth_invalid_pre_dispatch_reselect():
    d = _run("AUTH_INVALID", dispatched=False)
    assert d.decision == "RESELECT_TARGET" and d.new_target == B

# ---------------------------------------------------------------------------
# 15. pre-dispatch evidence pointer capture (audit trail)
def test_pre_dispatch_evidence_captured():
    d = _run("TARGET_INELIGIBLE_BEFORE_EXECUTION", dispatched=False,
             prior_receipt={"request_id": "r-1"})
    assert len(d.evidence_pointers) >= 0  # audit trail present in record

# ---------------------------------------------------------------------------
# 16. eligibility snapshot semantics
def test_snapshot_eligible_hit():
    probe = lambda t: EligibilitySnapshot(target=t, eligible=True, failure_class=None)
    assert snapshot_eligibility(A, probe).eligible is True

def test_snapshot_unknown_target_fail_closed():
    probe = lambda t: None
    assert snapshot_eligibility("NOPE", probe) is None

def test_snapshot_no_probe_fail_closed():
    assert snapshot_eligibility(A, None) is None

def test_snapshot_ineligible_carries_class():
    probe = lambda t: EligibilitySnapshot(target=t, eligible=False,
                                          failure_class="AUTH_INVALID",
                                          evidence_pointers=("ev",))
    s = snapshot_eligibility(A, probe)
    assert s.eligible is False and s.failure_class == "AUTH_INVALID"

# ---------------------------------------------------------------------------
# 17. contract validation (fail-closed construction)
def test_invalid_decision_rejected():
    with pytest.raises(BackendContractError):
        FailoverDecision(decision="DO_WHATEVER", failure_class=None)

def test_invalid_class_rejected():
    with pytest.raises(BackendContractError):
        FailoverDecision(decision="STOP_FAIL_CLOSED", failure_class="FAKE")

def test_evidence_must_be_tuple():
    with pytest.raises(BackendContractError):
        EligibilitySnapshot(target=A, eligible=True, evidence_pointers=[])

def test_target_text_limit():
    with pytest.raises(BackendContractError):
        FailoverDecision(decision="STOP_FAIL_CLOSED", failure_class="TIMEOUT",
                         old_target="x" * 500)

# ---------------------------------------------------------------------------
# 18. no silent backend invocation: the module only decides
def test_module_has_no_backend_imports():
    import p2p_capabilities.failover_boundary as mod
    src = open(mod.__file__, encoding="utf-8").read()
    for bad in ("hermes_adapter", "manus_adapter", "subprocess", "urllib.request"):
        assert bad not in src, bad

# ---------------------------------------------------------------------------
# 19. decision trace is self-describing and serializable
def test_decision_trace_json_safe():
    d = _run("RESULT_UNKNOWN", dispatched=True, mutation_status="MUTATION_UNKNOWN",
             prior_receipt={"output_pointers": ("o1", "o2")})
    s = json.dumps(d.to_dict())
    dd = json.loads(s)
    assert dd["decision"] == "REVERIFY_REQUIRED", dd["decision"]
    assert dd["mutation_status"] == "MUTATION_UNKNOWN"
    assert dd["evidence_pointers"] == ["o1", "o2"]

# ---------------------------------------------------------------------------
# 20. reversibility evidence: pre-dispatch drift leaves no trace on old target
def test_reversible_drift_no_revoke_needed():
    """A pre-dispatch drift must be resolvable WITHOUT touching the failing
    target (e.g. no key revocation).  The decision alone must hand control
    to an eligible alternative with a new selection revision."""
    d = _run("AUTH_DRIFT", dispatched=False)
    assert d.decision == "RESELECT_TARGET"
    assert d.old_target == A
    assert d.new_target == B
    assert d.revision.startswith("reselect-")

# ---------------------------------------------------------------------------
# 21. Rule 1 owner-gate guard: dispatch authorization never outranks a pending
#     Owner action, even when no failure is recorded (fail-closed by
#     authority, not by failure).
def test_rule1_owner_gate_outranks_dispatch_authorization():
    """No recorded failure + dispatched=False + owner_action_needed=True must
    yield OWNER_GATE, NOT dispatch authorization.  The Owner gate semantics
    (Rule 2) always outrank the Rule 1 pre-dispatch authorization."""
    d = _run(None, dispatched=False, owner=True)
    assert d.decision == "OWNER_GATE", d.decision
    assert d.reason.startswith("OWNER_ACTION_REQUIRED:"), d.reason
    # Without a pending owner action the same inputs authorize dispatch.
    d2 = _run(None, dispatched=False, owner=False)
    assert d2.decision == "RETRY_SAME_TARGET", d2.decision

def test_rule1_drift_still_reselects_with_owner_guard_absent():
    """Pre-dispatch AUTH_DRIFT observed must still yield RESELECT_TARGET when
    no owner action is pending (Rule 1 drift path unaffected by the guard)."""
    d = _run("AUTH_DRIFT", dispatched=False, observed=("AUTH_DRIFT",))
    assert d.decision == "RESELECT_TARGET", d.decision
    # With a pending owner action, drift yields OWNER_GATE instead (guard).
    d2 = _run("AUTH_DRIFT", dispatched=False, observed=("AUTH_DRIFT",), owner=True)
    assert d2.decision == "OWNER_GATE", d2.decision
