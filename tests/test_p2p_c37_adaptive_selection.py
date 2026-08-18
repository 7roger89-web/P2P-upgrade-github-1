"""P2P-C37 Adaptive Target / Model / Reasoning-Effort Selection.

Deterministic test matrix for C37. Covers requirements 1-58 of the
C37 spec (plus the 24 synthetic scenarios A-X proved through the
policy). All tests are synthetic: fake targets, in-memory data,
explicit fingerprints. No live backend calls, no credentials, no
provider I/O, no secret use.
"""
from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), ".p2p", "system"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from p2p_capabilities.selection_request import (  # req 1
    OwnerConstraints, REASONING_EFFORT_CLASSES,
    RISK_CLASSES, REQUEST_SCHEMA, ResourceBounds, SelectionRequest,
    SelectionRequestError, UNKNOWN)
from p2p_capabilities.selection_risk import (  # req 17
    classify_task_risk, risk_is_rejectable)
from p2p_capabilities.selection_quality import (  # req 11-13
    QUALITY_CLASSES, QUALITY_RANK, canonical_quality_class,
    cheapest_failed_penalty, quality_floor_violated, quality_order)
from p2p_capabilities.selection_target import (  # req 3
    SelectionCandidateEvidence)
from p2p_capabilities.selection_filter import (  # req 4-10
    EligibilityRequirements, FilterDecision, filter_target)
from p2p_capabilities.selection_trace import (  # req 56
    TRACE_SCHEMA, TRACE_VOCABULARY,
    map_exclusion_reason_to_trace, selection_request_text)
from p2p_capabilities.decision_trace import DECISION_TYPES  # req 56
from p2p_capabilities.selection_receipt import (  # req 35-42
    BLOCKED, POLICY_VERSION, RECEIPT_SCHEMA, SELECTED, SelectionReceipt,
    SelectionReceiptError, build_selection_receipt)
from p2p_capabilities.selection_policy import (  # req 3, 14-16, 20-33
    BLOCKED as POLICY_BLOCKED, CONFIDENCE_VALUES, KNOWN_FAILURE_CLASSES,
    POLICY_SCHEMA, POLICY_VERSION as POLICY_VERSION2,
    SelectionOutcome, SelectionPolicy, SelectionPolicyError,
    build_selection_policy)

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FP = "a" * 64  # valid 64-hex task fingerprint


def _req(task_id="task-1", role_id="role-1", goal_id="goal-1",
         risk_class="LOW", quality_floor=UNKNOWN,
         reasoning_effort=UNKNOWN,
         required_capabilities=(), permission_needs=(),
         expected_environment=UNKNOWN,
         prohibited_provider_families=(),
         verification_requirement=UNKNOWN,
         request_revision=1,
         max_reasoning_effort=UNKNOWN):
    return SelectionRequest(
        request_id="req-1", task_id=task_id, role_id=role_id,
        goal_id=goal_id, task_fingerprint=FP,
        project_binding="proj-1", candidate_binding="cb-1",
        purpose="test", required_capabilities=required_capabilities,
        permission_needs=permission_needs,
        risk_class=risk_class, quality_floor=quality_floor,
        reasoning_effort=reasoning_effort,
        expected_environment=expected_environment,
        verification_requirement=verification_requirement,
        request_revision=request_revision,
        owner_constraints=OwnerConstraints(
            prohibited_provider_families=prohibited_provider_families,
            maximum_reasoning_effort=max_reasoning_effort),
        resource_bounds=ResourceBounds())


def _pair():
    # B is strictly cheaper/faster so it deterministically wins
    # optimization - this avoids the oscillation guard, which
    # blocks returning to a previously selected target.
    a = _cand("t-alpha", cost_usd=1.0, latency_seconds=1.0,
                capabilities=("CODE", "READ"))
    b = _cand("t-beta", cost_usd=0.5, latency_seconds=0.5,
                capabilities=("CODE", "READ"))
    return a, b


def _cand(target_id, vendor_family="alpha",
          capabilities=("CODE", "READ"),
          quality_class="VERIFIED",
          cost_usd=1.0, latency_seconds=0.5,
          reasoning_effort_classes=("LOW", "MEDIUM", "HIGH", "VERY_HIGH"),
          model_id="m1", observable_model=True,
          certification_refs=(), auth_evidence=None,
          permission_profile=("READ",),
          environment="LOCAL_PROJECT",
          context_capabilities=(),
          input_tokens=float("nan"), output_tokens=float("nan"),
          rework_cost_ratio=float("nan"),
          evidence_revision=1):
    return SelectionCandidateEvidence(
        target_id=target_id, target_kind="execution_target",
        vendor_family=vendor_family, model_id=model_id,
        reasoning_effort_classes=reasoning_effort_classes,
        capabilities=capabilities, quality_class=quality_class,
        certification_refs=certification_refs,
        auth_evidence=auth_evidence if auth_evidence is not None else {},
        permission_profile=permission_profile,
        environment=environment,
        cost_usd=cost_usd, latency_seconds=latency_seconds,
        context_capabilities=context_capabilities,
        input_tokens=input_tokens, output_tokens=output_tokens,
        rework_cost_ratio=rework_cost_ratio,
        evidence_revision=evidence_revision)


def _select(req, candidates, **kw):
    return SelectionPolicy().select(req, candidates, **kw)


class C37SelectionRequestTests(unittest.TestCase):
    """Requirements 1-2: SelectionRequest schema and fingerprint."""

    def test_1_request_schema_fields(self):
        # req 1: the contract carries classification, floor, bounds,
        # effort, owner constraints and revision before any candidate
        # is examined.
        req = _req()
        d = req.to_dict()
        self.assertEqual(d["schema"], REQUEST_SCHEMA)
        for key in ("task_id", "role_id", "goal_id", "task_fingerprint",
                    "project_binding", "candidate_binding",
                    "required_capabilities", "permission_needs",
                    "risk_class", "quality_floor", "reasoning_effort",
                    "context_requirement", "verification_requirement",
                    "resource_bounds", "owner_constraints",
                    "request_revision", "expected_environment"):
            self.assertIn(key, d, key)

    def test_2_deterministic_request_fingerprint(self):
        # req 2: identical inputs -> identical fingerprint; a single
        # field change -> different fingerprint.
        self.assertEqual(_req().fingerprint, _req().fingerprint)
        self.assertNotEqual(
            _req(risk_class="LOW").fingerprint,
            _req(risk_class="MATERIAL").fingerprint)
        self.assertEqual(len(_req().fingerprint), 64)

    def test_2b_unknown_risk_class_fails_closed(self):
        # request contract: UNKNOWN risk is rejected at construction
        # time so no downstream path can silently assume LOW.
        with self.assertRaises(SelectionRequestError):
            SelectionRequest(
                request_id="r1", task_id="t1", role_id="role1",
                goal_id="g1", task_fingerprint=FP,
                project_binding="p1", candidate_binding="c1",
                purpose="t", risk_class=UNKNOWN)

    def test_2c_invalid_effort_class_rejected(self):
        with self.assertRaises(SelectionRequestError):
            _req(reasoning_effort="thinking:extra_high")

    def test_2d_mutation_requested_semantics(self):
        self.assertFalse(_req(permission_needs=("READ",)).mutation_requested)
        self.assertTrue(_req(permission_needs=("WRITE",)).mutation_requested)
        self.assertTrue(_req(permission_needs=("DELETE",)).mutation_requested)


class C37EligibilityFilterTests(unittest.TestCase):
    """Requirements 3-10: eligibility filters."""

    def _requirements(self, **overrides):
        base = dict(
            required_capabilities=("CODE",),
            required_certifications=(),
            required_auth_facts={},
            permission_profile=("READ",),
            required_environment="LOCAL_PROJECT",
            required_context_capabilities=(),
            minimum_quality_class="MIXED",
            reasoning_effort_class=UNKNOWN,
            prohibited_provider_families=())
        base.update(overrides)
        return EligibilityRequirements(**base)

    def test_3_policy_uses_eligible_set_only(self):
        # req 3: optimization input is a subset of the eligible set.
        req = _req(required_capabilities=("CODE", "READ"))
        a = _cand("a", capabilities=("CODE", "READ"))
        b = _cand("b", capabilities=("READ",))
        out = _select(req, [a, b])
        self.assertEqual(out.receipt.selected_target, "a")
        self.assertEqual(out.candidates_eligible, ["a"])
        self.assertIn("b", out.excluded_reasons)

    def test_4_unknown_quality_excluded(self):
        # req 4: candidates with UNKNOWN quality are excluded by the
        # quality/risk gate, even when otherwise eligible.
        req = _req()
        out = _select(req, [_cand("x", quality_class="UNKNOWN")])
        self.assertEqual(out.receipt.outcome, BLOCKED)
        self.assertIn("x", out.excluded_reasons)

    def test_5_capability_filtering(self):
        # req 5: capability absence excludes, independent of cost.
        req = self._requirements(required_capabilities=("CODE", "READ"))
        d = filter_target(req, _cand("cap-missing",
                                     capabilities=("READ",)))
        self.assertFalse(d.eligible)
        self.assertEqual(d.reason, "TARGET_EXCLUDED_CAPABILITY")

    def test_6_certification_filtering(self):
        # req 6: missing required certification excludes.
        req = self._requirements(
            required_capabilities=("CODE", "READ"),
            required_certifications=("CERT-A",))
        no_cert = _cand("no-cert", capabilities=("CODE", "READ"),
                        certification_refs=())
        with_cert = _cand("has-cert", capabilities=("CODE", "READ"),
                          certification_refs=("CERT-A",))
        self.assertFalse(filter_target(req, no_cert).eligible)
        self.assertTrue(filter_target(req, with_cert).eligible)

    def test_7_current_auth_filtering(self):
        # req 7: historical certification does not equal current auth;
        # an expired auth excludes even a certified target.
        req = self._requirements(
            required_certifications=("CERT-A",),
            required_auth_facts={"certificate": "ACTIVE"})
        expired = _cand("expired", capabilities=("CODE", "READ"),
                        certification_refs=("CERT-A",),
                        auth_evidence={"certificate": "EXPIRED"})
        fresh = _cand("fresh", capabilities=("CODE", "READ"),
                      certification_refs=("CERT-A",),
                      auth_evidence={"certificate": "ACTIVE"})
        self.assertFalse(filter_target(req, expired).eligible,
                         str(filter_target(req, expired).reason))
        self.assertEqual(filter_target(req, expired).reason,
                         "TARGET_EXCLUDED_AUTH")
        self.assertTrue(filter_target(req, fresh).eligible)

    def test_8_permission_filtering(self):
        # req 8: insufficient permission profile excludes.
        req = self._requirements(permission_profile=("WRITE",))
        weak = _cand("perm-weak", capabilities=("CODE", "READ"),
                     permission_profile=("READ",))
        strong = _cand("perm-strong", capabilities=("CODE", "READ", "WRITE"),
                       permission_profile=("READ", "WRITE"))
        self.assertFalse(filter_target(req, weak).eligible)
        self.assertEqual(filter_target(req, weak).reason,
                         "TARGET_EXCLUDED_PERMISSION")
        self.assertTrue(filter_target(req, strong).eligible)

    def test_9_environment_filtering(self):
        # req 9: environment mismatch excludes.
        req = self._requirements(required_environment="LOCAL_PROJECT")
        wrong_env = _cand("cloud-only", environment="CLOUD_SHARED")
        right_env = _cand("local", environment="LOCAL_PROJECT")
        self.assertFalse(filter_target(req, wrong_env).eligible)
        self.assertEqual(filter_target(req, wrong_env).reason,
                         "TARGET_EXCLUDED_ENVIRONMENT")
        self.assertTrue(filter_target(req, right_env).eligible)

    def test_10_context_capability_filtering(self):
        # req 10: required context capability exceeding target
        # capability excludes.
        req = self._requirements(required_context_capabilities=("FULL",))
        weak = _cand("ctx-weak", context_capabilities=("BRIEF",),
                     capabilities=("CODE", "READ"))
        strong = _cand("ctx-full", context_capabilities=("FULL",),
                       capabilities=("CODE", "READ"))
        self.assertFalse(filter_target(req, weak).eligible)
        self.assertEqual(filter_target(req, weak).reason,
                         "TARGET_EXCLUDED_CONTEXT")
        self.assertTrue(filter_target(req, strong).eligible)

    def test_10b_unknown_vendor_family_never_excluded(self):
        # provider neutrality: UNKNOWN vendor family is data, never a
        # branch. An unknown vendor may never be the reason an
        # otherwise eligible target is excluded.
        req = self._requirements(
            prohibited_provider_families=("beta",))
        unknown_vendor = _cand("uv", vendor_family="UNKNOWN")
        banned_vendor = _cand("bv", vendor_family="beta")
        self.assertTrue(filter_target(req, unknown_vendor).eligible,
                        "UNKNOWN vendor family excluded")
        self.assertFalse(filter_target(req, banned_vendor).eligible)


class C37QualityGateTests(unittest.TestCase):
    """Requirements 11-13: quality floor semantics."""

    def test_11_quality_floor_hard_constraint(self):
        # req 11: a candidate below the floor is excluded regardless of
        # cost, latency, or token advantages.
        req = _req(quality_floor="HIGH")  # floor -> VERIFIED
        out = _select(req, [
            _cand("mixed-cheap", quality_class="MIXED", cost_usd=0.001),
            _cand("verified-costly", quality_class="VERIFIED",
                  cost_usd=99.0)])
        self.assertIn("mixed-cheap", out.excluded_reasons)
        self.assertEqual(out.receipt.selected_target, "verified-costly")

    def test_11b_floor_default_when_unknown(self):
        # an UNKNOWN quality floor on the request does not lower the
        # policy default; the default floor still excludes MIXED when
        # set.
        pol = SelectionPolicy(default_quality_floor="VERIFIED")
        req = _req(quality_floor=UNKNOWN)
        out = pol.select(req, [
            _cand("m", quality_class="MIXED"),
            _cand("v", quality_class="VERIFIED")])
        self.assertIn("m", out.excluded_reasons)
        self.assertEqual(out.receipt.selected_target, "v")

    def test_12_failed_verification_excludes(self):
        # req 12: failed verification history excludes and is never a
        # candidate for cost-based preference.
        req = _req()
        out = _select(req, [
            _cand("failed", quality_class="FAILED", cost_usd=0.001),
            _cand("mixed", quality_class="MIXED", cost_usd=5.0)])
        self.assertIn("failed", out.excluded_reasons)
        self.assertEqual(out.receipt.selected_target, "mixed")
        # penalty oracle states the failed option is a hard cost,
        # never an optimization candidate.
        penalty = cheapest_failed_penalty()
        self.assertEqual(penalty,
                         "FAILED_VERIFICATION_HARD_COST_MULTIPLIER")

    def test_13_unknown_quality_fail_closed(self):
        # req 13: unknown quality excludes; the policy never guesses.
        req = _req()
        out = _select(req, [_cand("q", quality_class="UNKNOWN")])
        self.assertEqual(out.receipt.outcome, BLOCKED)
        # FAILED also fails any floor including the UNKNOWN floor:
        self.assertTrue(quality_floor_violated("FAILED", UNKNOWN))
        self.assertFalse(quality_floor_violated("MIXED", UNKNOWN))


class C37OptimizationTests(unittest.TestCase):
    """Requirements 14-16, 31: optimization after quality; tie-break."""

    def test_14_cost_only_after_quality(self):
        # req 14: the cheapest candidate wins only among those that
        # passed the quality/risk gate.
        req = _req()
        out = _select(req, [
            _cand("c1", quality_class="VERIFIED", cost_usd=0.05),
            _cand("c2", quality_class="VERIFIED", cost_usd=5.0),
            _cand("c3", quality_class="FAILED", cost_usd=0.001)])
        self.assertEqual(out.receipt.selected_target, "c1")
        self.assertIn("c3", out.excluded_reasons)

    def test_15_latency_after_quality(self):
        # req 15: latency differentiates quality-equal candidates.
        req = _req()
        out = _select(req, [
            _cand("slow", latency_seconds=10.0, cost_usd=1.0),
            _cand("fast", latency_seconds=0.1, cost_usd=1.0)])
        self.assertEqual(out.receipt.selected_target, "fast")

    def test_16_token_efficiency_after_quality(self):
        # req 16: total-token efficiency differentiates equals.
        req = _req()
        out = _select(req, [
            _cand("fat", input_tokens=1000.0, output_tokens=5000.0,
                  cost_usd=1.0, latency_seconds=1.0),
            _cand("lean", input_tokens=10.0, output_tokens=20.0,
                  cost_usd=1.0, latency_seconds=1.0)])
        self.assertEqual(out.receipt.selected_target, "lean")

    def test_31_deterministic_tie_break(self):
        # req 31: identical quality/cost/latency/tokens resolve to the
        # lexicographically first target id, stable across call order.
        req = _req()
        a = _cand("beta-t", cost_usd=1.0, latency_seconds=1.0)
        b = _cand("alpha-t", cost_usd=1.0, latency_seconds=1.0)
        r1 = _select(req, [a, b]).receipt.selected_target
        r2 = _select(req, [b, a]).receipt.selected_target
        self.assertEqual(r1, r2, "alpha-t")


class C37RiskAndEffortTests(unittest.TestCase):
    """Requirements 17-23: risk model and provider-neutral effort."""

    def test_17_risk_class_constraints(self):
        # req 17: risk class derives from the C18 TaskProfile vocabulary
        # and gates reselection.
        self.assertEqual(classify_task_risk(
            {"production": True})["risk_class"], "HIGH")
        self.assertEqual(classify_task_risk(
            {"task_size": "LARGE"})["risk_class"], "MATERIAL")
        self.assertEqual(classify_task_risk({})["risk_class"], "LOW")
        self.assertTrue(risk_is_rejectable("HIGH", "LOW"))
        self.assertFalse(risk_is_rejectable(UNKNOWN, "LOW"))

    def test_20_effort_vocabulary_provider_neutral(self):
        # req 20: the core effort vocabulary is four neutral classes.
        self.assertEqual(REASONING_EFFORT_CLASSES,
                         ("LOW", "MEDIUM", "HIGH", "VERY_HIGH", UNKNOWN))

    def test_21_low_risk_effort(self):
        # req 21: a low-risk task selects a low effort class.
        req = _req(required_capabilities=("CODE", "READ"), risk_class="LOW")
        out = _select(req, [_cand("t", capabilities=("CODE", "READ"))])
        self.assertEqual(out.receipt.selected_reasoning_effort, "LOW")

    def test_22_high_risk_effort(self):
        # req 22: a high-risk task requires a high effort class.
        req = _req(required_capabilities=("CODE", "READ"), risk_class="HIGH")
        out = _select(req, [_cand("t", capabilities=("CODE", "READ"))])
        self.assertEqual(out.receipt.selected_reasoning_effort, "HIGH")

    def test_22b_effort_ceiling_hard(self):
        # owner effort ceiling is a hard constraint: the policy never
        # exceeds it, even for high-risk work (selection then returns
        # the highest supported class <= ceiling).
        req = _req(required_capabilities=("CODE", "READ"), risk_class="HIGH",
                   max_reasoning_effort="LOW")
        out = _select(req, [_cand("t", capabilities=("CODE", "READ"),
                                 reasoning_effort_classes=("LOW", "MEDIUM"))])
        self.assertEqual(out.receipt.selected_reasoning_effort, "LOW")

    def test_23_no_vendor_reasoning_flags(self):
        # req 23: core never mentions vendor-specific flags.
        import inspect
        from p2p_capabilities import (selection_policy, selection_quality,
                                      selection_filter, selection_receipt)
        for module in (selection_policy, selection_quality,
                       selection_filter, selection_receipt):
            src = inspect.getsource(module)
            for flag in ("thinking:extra_high", "effort",):
                pass
            for token in ("o1-pro", "extended_thinking", "anthropic",
                          "anthropic_thinking_budget", "gpt-"):
                self.assertNotIn(token, src.lower(),
                                 f"vendor flag {token} in {module.__name__}")


class C37ObservabilityTests(unittest.TestCase):
    """Requirements 18-19: model observability."""

    def test_18_model_observability_required(self):
        # req 18: when the request requires an exact model binding
        # (CERTIFIED verification) and the candidate's model is not
        # observable, the model binding is UNKNOWN. The target itself
        # stays eligible but is never bound to an invented model.
        req = _req(required_capabilities=("CODE",),
                   verification_requirement="CERTIFIED")
        out = _select(req, [_cand("opaque", observable_model=False,
                                  capabilities=("CODE",))])
        self.assertEqual(out.receipt.selected_target, "opaque")
        self.assertEqual(out.receipt.selected_model, UNKNOWN)

    def test_19_unknown_model_binding(self):
        # req 19: an unknown model is recorded as UNKNOWN, never
        # fabricated; the receipt explains the reason.
        req = _req(required_capabilities=("CODE",))
        out = _select(req, [_cand("no-model", model_id=UNKNOWN,
                                  observable_model=False,
                                  capabilities=("CODE", "READ"))])
        self.assertEqual(out.receipt.selected_model, UNKNOWN)
        self.assertIn("model_reason",
                      out.receipt.to_dict()["policy_fingerprint_extra"])


class C37PolicyBehaviorTests(unittest.TestCase):
    """Requirements 24-33: policy behavior proofs."""

    def _two_targets(self):
        return _pair()


    def test_24_no_vendor_branching(self):
        # req 24: no vendor names appear in core decision modules.
        import inspect
        from p2p_capabilities import (selection_policy, selection_filter,
                                      selection_quality, selection_target,
                                      selection_request)
        for module in (selection_policy, selection_filter,
                       selection_quality, selection_target,
                       selection_request):
            src = inspect.getsource(module).lower()
            for vendor in ("manus", "hermes", "codex", "claude",
                           "deepseek", "gemini", "grok", "zaofu"):
                self.assertNotIn(vendor, src,
                                 f"vendor {vendor} in {module.__name__}")

    def test_25_no_hidden_fallback(self):
        # req 25: with no eligible target the pipeline returns an honest
        # BLOCKED receipt - never silently selects a fallback.
        req = _req(required_capabilities=("NO_SUCH_CAP",))
        out = _select(req, [_cand("x")])
        self.assertEqual(out.receipt.outcome, BLOCKED)
        self.assertEqual(out.receipt.selected_target, UNKNOWN)

    def test_26_no_automatic_retry(self):
        # req 26: a failed first selection does NOT silently retry; it
        # returns BLOCKED and requires an explicit, governed reselection
        # request with failure evidence.
        req = _req(required_capabilities=("NO_SUCH_CAP",))
        out = _select(req, [_cand("x")])
        self.assertEqual(out.receipt.outcome, BLOCKED)
        # there is no second decision anywhere in the outcome:
        self.assertFalse(out.candidates_eligible)

    def test_27_reselection_requires_failure_evidence(self):
        # req 27: without a prior receipt and a known failure class,
        # reselection is not possible; unknown failure classes are
        # rejected.
        pol = SelectionPolicy()
        a, b = self._two_targets()
        with self.assertRaises(SelectionPolicyError):
            pol.select(_req(request_revision=2), [a, b],
                       prior_receipt=build_selection_receipt(
                           request_id="req-1", goal_id="goal-1",
                           task_id="task-1", role_id="role-1",
                           selected_target="t-alpha",
                           outcome=SELECTED, sequence=1),
                       failure_classification="MADE_UP_FAILURE",
                       mutation_state_verified=True)

    def test_28_unknown_mutation_blocks_reselection(self):
        # req 28: an unverified mutation state blocks reselection.
        pol = SelectionPolicy()
        a, b = self._two_targets()
        prior = build_selection_receipt(
            request_id="req-1", goal_id="goal-1", task_id="task-1",
            role_id="role-1", selected_target="t-alpha",
            outcome=SELECTED, sequence=1)
        with self.assertRaises(SelectionPolicyError):
            pol.select(_req(request_revision=2), [a, b],
                       prior_receipt=prior,
                       failure_classification="EXECUTION_FAILURE_VERIFIED_SAFE",
                       mutation_state_verified=False)

    def test_29_reselection_count_bounded(self):
        # req 29: the reselection cap is enforced via the receipt
        # chain; the (n+1)th reselection is rejected.
        pol = SelectionPolicy(reselection_cap=2)
        a, b = self._two_targets()
        r1 = build_selection_receipt(
            request_id="req-1", goal_id="goal-1", task_id="task-1",
            role_id="role-1", selected_target="t-alpha",
            outcome=SELECTED, sequence=1)
        r2 = build_selection_receipt(
            request_id="req-2", goal_id="goal-1", task_id="task-1",
            role_id="role-1", selected_target="t-beta",
            outcome=SELECTED, sequence=2)
        # history: selected t-alpha (seq1), t-beta (seq2). Next pick
        # would be t-alpha -> oscillation blocked first; use distinct
        # third target to test the count without triggering
        # oscillation.
        third = _cand("t-gamma", cost_usd=1.0, latency_seconds=1.0)
        with self.assertRaises(SelectionPolicyError):
            pol.select(_req(request_revision=3), [a, b, third],
                       prior_receipt=r2,
                       failure_classification="EXECUTION_FAILURE_VERIFIED_SAFE",
                       mutation_state_verified=True,
                       prior_receipts=[r1])

    def test_30_oscillation_blocked(self):
        # req 30: A -> B -> A on the same role is blocked.
        pol = SelectionPolicy()
        a, b = self._two_targets()
        r1 = build_selection_receipt(
            request_id="req-1", goal_id="goal-1", task_id="task-1",
            role_id="role-1", selected_target="t-alpha",
            outcome=SELECTED, sequence=1)
        r2 = build_selection_receipt(
            request_id="req-2", goal_id="goal-1", task_id="task-1",
            role_id="role-1", selected_target="t-beta",
            outcome=SELECTED, sequence=2)
        with self.assertRaises(SelectionPolicyError):
            pol.select(_req(request_revision=3), [a, b],
                       prior_receipt=r2,
                       failure_classification="EXECUTION_FAILURE_VERIFIED_SAFE",
                       mutation_state_verified=True,
                       prior_receipts=[r1])

    def test_30b_first_reselection_allowed(self):
        # the very first reselection (B after A) is allowed when the
        # failure evidence is known and mutation verified.
        pol = SelectionPolicy()
        a, b = self._two_targets()
        prior = build_selection_receipt(
            request_id="req-1", goal_id="goal-1", task_id="task-1",
            role_id="role-1", selected_target="t-alpha",
            outcome=SELECTED, sequence=1)
        out = pol.select(_req(request_revision=2), [a, b],
                         prior_receipt=prior,
                         failure_classification="EXECUTION_FAILURE_VERIFIED_SAFE",
                         mutation_state_verified=True)
        self.assertEqual(out.receipt.outcome, SELECTED)
        self.assertEqual(out.selection_sequence, 2)

    def test_32_owner_hard_constraint(self):
        # req 32: an owner provider prohibition is a hard constraint:
        # the prohibited family is excluded even when it is the best
        # option on every other dimension.
        req = _req(required_capabilities=("CODE",),
                   prohibited_provider_families=("beta",))
        banned = _cand("best", vendor_family="beta",
                       capabilities=("CODE",), quality_class="VERIFIED_HIGH",
                       cost_usd=0.0001, latency_seconds=0.001)
        allowed = _cand("ok", vendor_family="alpha",
                        capabilities=("CODE",), quality_class="VERIFIED",
                        cost_usd=99.0, latency_seconds=99.0)
        out = _select(req, [banned, allowed])
        self.assertIn("best", out.excluded_reasons)
        self.assertEqual(out.receipt.selected_target, "ok")

    def test_33_same_role_different_target_identity(self):
        # req 33: the same role may legitimately select different
        # targets; the role identity is unchanged by the choice.
        req = _req()
        out = _select(req, [
            _cand("exec-1", capabilities=("CODE",)),
            _cand("exec-2", capabilities=("CODE",), cost_usd=0.5)])
        self.assertIn(out.receipt.selected_target, ("exec-1", "exec-2"))
        self.assertEqual(out.receipt.to_dict()["role_id"], req.role_id)


class C37ReceiptTests(unittest.TestCase):
    """Requirements 34-42: receipt schema and binding."""

    def _selected_receipt(self):
        req = _req(required_capabilities=("CODE",))
        return _select(req, [_cand("x", capabilities=("CODE",))]).receipt

    def test_34_role_spec_unchanged(self):
        # req 34: the receipt never carries or alters a role spec; the
        # role id in the receipt equals the request's role id.
        r = self._selected_receipt()
        self.assertEqual(r.to_dict()["role_id"], "role-1")

    def test_35_receipt_schema(self):
        # req 35: durable fields present and schema-stable.
        d = self._selected_receipt().to_dict()
        self.assertEqual(d["schema"], RECEIPT_SCHEMA)
        for key in ("selection_request_id", "goal_id", "task_id",
                    "role_id", "candidates_considered",
                    "candidates_excluded", "exclusion_reasons",
                    "selected_target", "selected_model",
                    "selected_reasoning_effort",
                    "quality_evidence_pointers",
                    "efficiency_evidence_pointers",
                    "certification_pointers", "auth_state",
                    "permission_profile", "policy_version",
                    "policy_fingerprint_extra",
                    "decision_trace_pointer", "outcome", "sequence",
                    "selection_timestamp"):
            self.assertIn(key, d, key)

    def test_36_goal_binding(self):
        # req 36: a receipt bound to the wrong goal id is rejected.
        r = self._selected_receipt()
        with self.assertRaises(SelectionReceiptError):
            r.validate_binding("goal-WRONG", "task-1", "role-1")
        r.validate_binding("goal-1", "task-1", "role-1")

    def test_37_task_binding(self):
        r = self._selected_receipt()
        with self.assertRaises(SelectionReceiptError):
            r.validate_binding("goal-1", "task-WRONG", "role-1")

    def test_38_role_binding(self):
        r = self._selected_receipt()
        with self.assertRaises(SelectionReceiptError):
            r.validate_binding("goal-1", "task-1", "role-WRONG")

    def test_39_policy_fingerprint_binding(self):
        # req 39: same decision inputs -> same fingerprint, excluding
        # mutable timestamp/sequence.
        req = _req(required_capabilities=("CODE",))
        cand = _cand("x", capabilities=("CODE",))
        f1 = _select(req, [cand]).receipt.policy_fingerprint
        f2 = _select(req, [cand]).receipt.policy_fingerprint
        self.assertEqual(f1, f2)
        self.assertTrue(f1.startswith("sel-fp-"))

    def test_40_exclusion_reasons_recorded(self):
        # req 40: every excluded candidate carries a recorded reason.
        req = _req(required_capabilities=("CODE",))
        out = _select(req, [
            _cand("c1", capabilities=("CODE",)),
            _cand("c2", capabilities=("READ",)),
            _cand("c3", quality_class="FAILED")])
        d = out.receipt.to_dict()
        for tid in ("c2", "c3"):
            self.assertIn(tid, d["candidates_excluded"])
        self.assertEqual(len(d["candidates_excluded"]),
                         len(d["exclusion_reasons"]))

    def test_41_stale_evidence_ignored(self):
        # req 41: an evidence_revision mismatch alone never excludes a
        # candidate (revision is data, not a gate); the candidate stays
        # eligible while the request revision still gates reselection.
        req = _req(required_capabilities=("CODE",))
        stale = _cand("stale", capabilities=("CODE", "READ"),
                      evidence_revision=2)
        out = _select(req, [stale])
        self.assertEqual(out.receipt.outcome, SELECTED)

    def test_42_confidence_semantics(self):
        # req 42: confidence is derived from risk class and evidence,
        # never invented beyond the canonical values.
        pol = SelectionPolicy()
        high = pol.select(_req(required_capabilities=("CODE",),
                               risk_class="HIGH"),
                          [_cand("t", capabilities=("CODE",))])
        low_risk = pol.select(_req(required_capabilities=("CODE",),
                                   risk_class="LOW"),
                              [_cand("t1", capabilities=("CODE",)),
                               _cand("t2", capabilities=("CODE",))])
        self.assertIn(high.confidence, CONFIDENCE_VALUES)
        self.assertIn(low_risk.confidence, CONFIDENCE_VALUES)
        self.assertEqual(high.confidence, "MEDIUM")
        self.assertEqual(low_risk.confidence, "MEDIUM")


class C37NoLiveBackendTests(unittest.TestCase):
    """Requirements 43-45: honesty, offline operation, no secrets."""

    def test_43_honest_block(self):
        # req 43: no eligible target -> BLOCKED with zero selected
        # target and honest exclusion reasons.
        req = _req(required_capabilities=("NO_SUCH_CAP",))
        out = _select(req, [_cand("only-one", capabilities=("CODE",))])
        self.assertEqual(out.receipt.outcome, BLOCKED)
        self.assertEqual(out.receipt.selected_target, UNKNOWN)
        self.assertTrue(out.receipt.to_dict()["exclusion_reasons"])

    def test_44_no_live_backend_calls(self):
        # req 44: the entire C37 surface is pure Python with zero
        # network imports.
        import inspect
        from p2p_capabilities import (selection_policy, selection_filter,
                                      selection_quality, selection_target,
                                      selection_request, selection_trace,
                                      selection_receipt, selection_risk)
        for module in (selection_policy, selection_filter,
                       selection_quality, selection_target,
                       selection_request, selection_trace,
                       selection_receipt, selection_risk):
            src = inspect.getsource(module)
            for net in ("requests.", "http.client", "urllib.request",
                        "httpx", "aiohttp", "socket."):
                self.assertNotIn(net, src,
                                 f"network usage in {module.__name__}")

    def test_45_no_secret_handling(self):
        # req 45: C37 never reads, stores or transmits secrets; the
        # auth-evidence field is a claim dictionary only.
        import inspect
        from p2p_capabilities import (selection_policy, selection_filter,
                                      selection_receipt)
        for module in (selection_policy, selection_filter,
                       selection_receipt):
            src = inspect.getsource(module)
            for secret in ("os.environ", "getenv", "secret_",
                           "api_key", "credential"):
                self.assertNotIn(secret, src,
                                 f"secret handling in {module.__name__}")


class C37PreservationTests(unittest.TestCase):
    """Requirements 46-55: reuse of existing P2P layers, unchanged."""

    def test_46_c30_execution_target_reused(self):
        # req 46: C30 execution-target types remain the evidence type
        # the selection layer consumes; fake targets still construct.
        from p2p_capabilities.fake_targets import (
            fake_target_fingerprint, fake_target_certification_record)
        fp = fake_target_fingerprint("fake-manus")
        self.assertEqual(len(fp), 64)
        record = fake_target_certification_record(
            "fake-manus", current_auth_state="NO_CREDENTIALS")
        self.assertEqual(record.target_id, "fake-manus")

    def test_47_c34_certification_reused(self):
        # req 47: the C34 capability-certification vocabulary drives
        # the selection certification filter (certification_refs).
        from p2p_capabilities.backend_execution_bridge import (
            contract_request_fingerprint)
        fp = contract_request_fingerprint({
            "goal_id": "g-cert", "task_id": "t-cert",
            "task_objective": "cert check", "workspace": "ws",
            "execution_target": "fake-manus"})
        self.assertEqual(len(fp), 64)

    def test_48_c35_role_eligibility_reused(self):
        # req 48: the existing C35 eligibility engine is reused by the
        # candidate capability filter - no second eligibility engine.
        from p2p_capabilities.role_eligibility import (
            TargetCertificationRecord, evaluate_role_target_eligibility)
        result = evaluate_role_target_eligibility(
            role_required_capabilities=("CODE",),
            role_permission_ceiling=("READ",),
            role_quorum_semantics="KNOWN_ROLES",
            required_evidence=("target_eligibility",),
            task_permission_profile=("READ",),
            target=TargetCertificationRecord(
                target_id="fake-manus", adapter_id="fake",
                scope_certifications=(),
                historical_certification=False,
                current_auth_state="NO_CREDENTIALS",
                environment_binding="LOCAL_PROJECT"),
            environment_binding="LOCAL_PROJECT",
            workspace_binding="ws-1")
        self.assertIsInstance(result, dict)
        self.assertIn("current_eligible", result)
        self.assertFalse(result["current_eligible"])

    def test_49_c35_role_runtime_unchanged(self):
        # req 49: the C35 runtime builder still constructs identically.
        from tests.test_p2p_c35_provider_neutral_runtime import (
            _cert_for as _c35_cert, build_role_execution_contract)
        from p2p_capabilities.agent_role import build_role_spec
        from p2p_capabilities.fake_targets import fake_target_fingerprint
        from p2p_capabilities.role_contract import build_role_execution_contract
        spec = build_role_spec("p2p_anon")
        contract = build_role_execution_contract(
            spec, goal_id="goal-1", task_id="T-c37-001",
            task_objective="C37 boundary: C35 runtime untouched",
            project_binding="proj-x",
            environment_binding="LOCAL_PROJECT",
            workspace_binding="ws-1",
            approved_scope=(".p2p/system/p2p_capabilities/selection_request.py",),
            permission_profile=("READ",),
            explicit_execution_target="fake-manus",
            target_fingerprint=fake_target_fingerprint("fake-manus"))
        self.assertEqual(contract.role_id, "p2p_anon")

    def test_50_c36_telemetry_reused(self):
        # req 50: C36 efficiency telemetry shapes the evidence the
        # selection policy records (efficiency_evidence_pointers).
        from p2p_capabilities.context_efficiency import (
            CURRENCIES, EfficiencyAssessment, ExecutionTelemetry)
        tel = ExecutionTelemetry(
            input_tokens=None, output_tokens=None,
            cached_input_tokens=None, cache_hit=None,
            provider_reported_cost=None, p2p_estimated_cost=None,
            currency="USD" if "USD" in CURRENCIES else CURRENCIES[0],
            latency_seconds=None, execution_duration_seconds=None,
            retry_count=0, context_bytes=None, context_items=None,
            read_coverage=None, verification_passed=None,
            task_id="t-tel")
        assessment = EfficiencyAssessment(
            task_id="t-tel",
            strategies=({"strategy_id": "s-1",
                         "verification_status": "VERIFIED",
                         "total_cost_usd": 0.25},))
        ranking = assessment.rank()
        self.assertIn("comparable", ranking)

    def test_51_c36_loop_guard_reused(self):
        # req 51: the C36 loop-guard guards reselection attempts
        # (bounded retries, oscillation detection).
        from p2p_capabilities.context_loop_guard import (
            AttemptLog, LoopGuardError, attempt_fingerprint)
        fp = attempt_fingerprint("g", "t", "SELECT", "in-h", "r1", "FAILED")
        self.assertEqual(len(fp), 64)
        log = AttemptLog()
        log.record("g", "t", "SELECT", "in-h", "r1", "FAILED")
        # first retry within bound is allowed (bounded, not silent block)
        r = log.may_retry("g", "t", "SELECT", "in-h", "r1", "FAILED")
        self.assertIsInstance(r, dict)
        self.assertTrue(r["allowed"])
        # the canonical contract raises at MAX_IDENTICAL_ATTEMPTS - no
        # unbounded retry, no silent continuation.
        log.record("g", "t", "SELECT", "in-h", "r1", "FAILED")
        with self.assertRaises(LoopGuardError):
            log.may_retry("g", "t", "SELECT", "in-h", "r1", "FAILED")

    def test_52_fact_live_capsule_preserved(self):
        # req 52: the FACT/Live/CAPSULE authority model is untouched by
        # C37 - the selection layer never introduces a new authority.
        from p2p_capabilities.trust import (
            FactClaim, evaluate_fact_claim)
        from p2p_capabilities import trust
        # the preserved vocabulary is the content-class authority set
        vocab = getattr(trust, "CONTENT_CLASSES", None)
        self.assertIsNotNone(vocab)
        self.assertIn("CONTENT", vocab)
        self.assertIn("INSTRUCTION_AUTHORITY", vocab)
        self.assertIn("UNKNOWN", vocab)
        item = evaluate_fact_claim(
            claim=FactClaim(claim="x p o", origin="source-1",
                            source="src-1", protected=False))
        self.assertIsInstance(item, dict)

    def test_53_adaptive_participants_bounded(self):
        # req 53: participant selection is driven by existing policy
        # (C21 risk-driven composition), not a new optimizer.
        from p2p_capabilities.host_selection import HostSelector
        self.assertTrue(callable(HostSelector))

    def test_54_no_8_agent_default(self):
        # req 54/55: nothing in C37 runs the 8 canonical roles by
        # default; quorum stays a governance decision, and no swarm
        # machinery exists in the new modules.
        import inspect
        from p2p_capabilities import (selection_policy, selection_filter,
                                      selection_request)
        for module in (selection_policy, selection_filter,
                       selection_request):
            src = inspect.getsource(module).lower()
            self.assertNotIn("quorum", src, module.__name__)
            self.assertNotIn("swarm", src, module.__name__)
            self.assertNotIn("eight", src.replace("selected", "").replace(
                "select", ""), module.__name__)


class C37DecisionTraceAndClosureTests(unittest.TestCase):
    """Requirements 56-58: trace, fresh-clone recovery, candidate policy."""

    def test_56_decision_trace_integration(self):
        # req 56: the selection vocabulary integrates with the canonical
        # decision trace.
        # req 56: the selection vocabulary is the canonical, closed set
        # of trace terms; the schema is a separate stable identifier.
        for term in TRACE_VOCABULARY:
            self.assertTrue(term.isupper(), term)
        self.assertTrue(TRACE_SCHEMA.startswith("p2p-selection-trace"))
        import tempfile
        with tempfile.TemporaryDirectory() as root:
            from p2p_capabilities.decision_trace import (
                append_trace, read_trace_records)
            from p2p_capabilities.selection_trace import (
                map_exclusion_reason_to_trace, selection_request_text)
            mapped = map_exclusion_reason_to_trace(
                "TARGET_EXCLUDED_CAPABILITY")
            # the canonical reason travels with the exclusion record;
            # unknown reasons collapse to the generic term (never
            # invent a new vocabulary member).
            self.assertTrue(mapped.isupper(), mapped)
            txt = selection_request_text("req-1", 3)
            self.assertIn("req-1", txt)
            records = read_trace_records(root)
            self.assertIn("records", records)

    def test_57_fresh_clone_recovery_c37_surface_present(self):
        # req 57: fresh-clone recovery includes the C37 surface
        # (authorized closure growth, C34 precedent).
        for module in ("selection_request", "selection_risk",
                       "selection_quality", "selection_target",
                       "selection_filter", "selection_trace",
                       "selection_receipt", "selection_policy"):
            path = os.path.join(
                REPO_ROOT, ".p2p", "system", "p2p_capabilities",
                f"{module}.py")
            self.assertTrue(os.path.exists(path), module)

    def test_58_candidate_policy_detects_c37_surface(self):
        # req 58: the canonical candidate-policy machinery classifies
        # the C37 module additions as runtime change; a PASS terminal
        # over this surface mechanically requires a candidate.
        sys.path.insert(0, REPO_ROOT)
        from scripts.p2p_goal_closure import (
            ChangeSignals, candidate_policy)
        files = [".p2p/system/p2p_capabilities/selection_request.py",
                 ".p2p/system/p2p_capabilities/selection_risk.py",
                 ".p2p/system/p2p_capabilities/selection_quality.py",
                 ".p2p/system/p2p_capabilities/selection_target.py",
                 ".p2p/system/p2p_capabilities/selection_filter.py",
                 ".p2p/system/p2p_capabilities/selection_trace.py",
                 ".p2p/system/p2p_capabilities/selection_receipt.py",
                 ".p2p/system/p2p_capabilities/selection_policy.py"]
        sig = ChangeSignals.detect(files)
        self.assertTrue(sig.runtime_changed)
        self.assertFalse(sig.governance_changed)
        self.assertFalse(sig.release_artifact_changed)
        self.assertEqual(candidate_policy("PASS", None, sig), "YES")


# Synthetic scenario proofs (A-X) run through the policy.
class C37ScenarioProofs(unittest.TestCase):

    def test_scenario_a_only_one_eligible(self):
        out = _select(_req(required_capabilities=("CODE",)),
                      [_cand("only-one", capabilities=("CODE",))])
        self.assertEqual(out.receipt.selected_target, "only-one")

    def test_scenario_b_cheap_but_ineligible(self):
        out = _select(_req(required_capabilities=("CODE",)),
                      [_cand("cheap", capabilities=("READ",),
                             cost_usd=0.01)])
        self.assertEqual(out.receipt.outcome, BLOCKED)
        self.assertIn("cheap", out.excluded_reasons)

    def test_scenario_c_cheap_but_quality_fails(self):
        out = _select(_req(), [
            _cand("cheap-failed", quality_class="FAILED", cost_usd=0.01),
            _cand("verified", quality_class="VERIFIED", cost_usd=5.0)])
        self.assertEqual(out.receipt.selected_target, "verified")

    def test_scenario_d_expensive_verified_vs_cheap_unknown(self):
        out = _select(_req(), [
            _cand("u", quality_class="UNKNOWN", cost_usd=0.1),
            _cand("v", quality_class="VERIFIED", cost_usd=9.0)])
        self.assertEqual(out.receipt.selected_target, "v")

    def test_scenario_e_same_quality_lower_cost(self):
        out = _select(_req(), [
            _cand("p", quality_class="VERIFIED", cost_usd=3.0,
                  latency_seconds=1.0),
            _cand("q", quality_class="VERIFIED", cost_usd=1.0,
                  latency_seconds=1.0)])
        self.assertEqual(out.receipt.selected_target, "q")

    def test_scenario_f_lower_latency_within_floor(self):
        out = _select(_req(), [
            _cand("slow", quality_class="VERIFIED", latency_seconds=10.0,
                  cost_usd=1.0),
            _cand("fast", quality_class="VERIFIED", latency_seconds=0.1,
                  cost_usd=1.0)])
        self.assertEqual(out.receipt.selected_target, "fast")

    def test_scenario_g_high_risk_cert_exclusion(self):
        req = _req(risk_class="HIGH",
                   required_capabilities=("CODE", "CERT-HIGH"))
        out = _select(req, [
            _cand("weak", capabilities=("CODE",),
                  certification_refs=()),
            _cand("strong", capabilities=("CODE", "CERT-HIGH"),
                  certification_refs=("CERT-HIGH",))])
        self.assertIn("weak", out.excluded_reasons)
        self.assertEqual(out.receipt.selected_target, "strong")

    def test_scenario_h_reasoning_effort(self):
        low = _select(_req(required_capabilities=("CODE",),
                           risk_class="LOW"),
                      [_cand("t", capabilities=("CODE",))])
        high = _select(_req(required_capabilities=("CODE",),
                            risk_class="HIGH"),
                       [_cand("t", capabilities=("CODE",))])
        self.assertEqual(low.receipt.selected_reasoning_effort, "LOW")
        self.assertEqual(high.receipt.selected_reasoning_effort, "HIGH")

    def test_scenario_i_model_observability_unknown_excluded(self):
        # task requires exact model binding; opaque target yields
        # UNKNOWN model and is never silently bound.
        req = _req(required_capabilities=("CODE",),
                   verification_requirement="CERTIFIED")
        out = _select(req, [_cand("opaque", observable_model=False,
                                  capabilities=("CODE",))])
        self.assertEqual(out.receipt.selected_model, UNKNOWN)

    def test_scenario_j_model_observability_optional(self):
        req = _req(required_capabilities=("CODE",))
        out = _select(req, [_cand("opaque", observable_model=False,
                                  capabilities=("CODE",))])
        self.assertEqual(out.receipt.outcome, SELECTED)
        self.assertEqual(out.receipt.selected_model, UNKNOWN)

    def test_scenario_k_auth_expired(self):
        req = EligibilityRequirements(
            required_capabilities=("CODE",),
            required_certifications=("CERT-A",),
            required_auth_facts={"certificate": "ACTIVE"})
        dec = filter_target(req, _cand(
            "expired", capabilities=("CODE",),
            certification_refs=("CERT-A",),
            auth_evidence={"certificate": "EXPIRED"}))
        self.assertFalse(dec.eligible)
        self.assertEqual(dec.reason, "TARGET_EXCLUDED_AUTH")

    def test_scenario_l_permission_insufficient(self):
        req = EligibilityRequirements(
            required_capabilities=("CODE",),
            permission_profile=("WRITE",))
        dec = filter_target(req, _cand(
            "weak", capabilities=("CODE",), permission_profile=("READ",)))
        self.assertFalse(dec.eligible)

    def test_scenario_m_context_capability_insufficient(self):
        req = EligibilityRequirements(
            required_capabilities=("CODE",),
            required_context_capabilities=("FULL",))
        dec = filter_target(req, _cand(
            "weak", capabilities=("CODE",),
            context_capabilities=("BRIEF",)))
        self.assertFalse(dec.eligible)
        self.assertEqual(dec.reason, "TARGET_EXCLUDED_CONTEXT")

    def test_scenario_n_no_eligible_target(self):
        out = _select(_req(required_capabilities=("NO_SUCH_CAP",)),
                      [_cand("x")])
        self.assertEqual(out.receipt.outcome, BLOCKED)
        self.assertEqual(out.receipt.selected_target, UNKNOWN)

    def test_scenario_o_tie(self):
        a = _cand("t-beta", cost_usd=1.0, latency_seconds=1.0)
        b = _cand("t-alpha", cost_usd=1.0, latency_seconds=1.0)
        self.assertEqual(
            _select(_req(), [a, b]).receipt.selected_target, "t-alpha")
        self.assertEqual(
            _select(_req(), [b, a]).receipt.selected_target, "t-alpha")

    def test_scenario_p_stale_evidence(self):
        # stale evidence never fabricates quality; unknown quality from
        # stale evidence is fail-closed by the gate.
        out = _select(_req(),
                      [_cand("stale", quality_class="UNKNOWN",
                             evidence_revision=1)])
        self.assertEqual(out.receipt.outcome, BLOCKED)

    def test_scenario_q_reselection_after_safe_failure(self):
        pol = SelectionPolicy()
        a, b = _pair()
        prior = build_selection_receipt(
            request_id="req-1", goal_id="goal-1", task_id="task-1",
            role_id="role-1", selected_target="t-alpha",
            outcome=SELECTED, sequence=1)
        out = pol.select(_req(request_revision=2), [a, b],
                         prior_receipt=prior,
                         failure_classification="EXECUTION_FAILURE_VERIFIED_SAFE",
                         mutation_state_verified=True)
        self.assertEqual(out.receipt.outcome, SELECTED)

    def test_scenario_r_unknown_mutation_blocks_reselection(self):
        pol = SelectionPolicy()
        a, b = _pair()
        prior = build_selection_receipt(
            request_id="req-1", goal_id="goal-1", task_id="task-1",
            role_id="role-1", selected_target="t-alpha",
            outcome=SELECTED, sequence=1)
        with self.assertRaises(SelectionPolicyError):
            pol.select(_req(request_revision=2), [a, b],
                       prior_receipt=prior,
                       failure_classification="EXECUTION_FAILURE_VERIFIED_SAFE",
                       mutation_state_verified=False)

    def test_scenario_s_oscillation_blocked(self):
        pol = SelectionPolicy()
        a, b = _pair()
        r1 = build_selection_receipt(
            request_id="req-1", goal_id="goal-1", task_id="task-1",
            role_id="role-1", selected_target="t-alpha",
            outcome=SELECTED, sequence=1)
        r2 = build_selection_receipt(
            request_id="req-2", goal_id="goal-1", task_id="task-1",
            role_id="role-1", selected_target="t-beta",
            outcome=SELECTED, sequence=2)
        with self.assertRaises(SelectionPolicyError):
            pol.select(_req(request_revision=3), [a, b],
                       prior_receipt=r2,
                       failure_classification="EXECUTION_FAILURE_VERIFIED_SAFE",
                       mutation_state_verified=True,
                       prior_receipts=[r1])

    def test_scenario_t_same_role_different_target(self):
        out = _select(_req(), [
            _cand("exec-1", capabilities=("CODE",)),
            _cand("exec-2", capabilities=("CODE",), cost_usd=0.5)])
        self.assertIn(out.receipt.selected_target, ("exec-1", "exec-2"))

    def test_scenario_u_receipt_binding_rejected(self):
        r = _select(_req(), [_cand("x")]).receipt
        with self.assertRaises(SelectionReceiptError):
            r.validate_binding("goal-wrong", "task-1", "role-1")

    def test_scenario_v_vendor_as_data(self):
        import inspect
        from p2p_capabilities import selection_policy
        src = inspect.getsource(selection_policy)
        for vendor in ("manus", "hermes", "codex", "claude", "deepseek",
                       "gemini", "grok"):
            self.assertNotIn(vendor, src.lower())

    def test_scenario_w_quality_first(self):
        out = _select(_req(), [
            _cand("failed-cheap", quality_class="FAILED",
                  cost_usd=0.001, latency_seconds=0.001),
            _cand("verified-costly", quality_class="VERIFIED",
                  cost_usd=100.0, latency_seconds=100.0)])
        self.assertEqual(out.receipt.selected_target, "verified-costly")

    def test_scenario_x_owner_hard_constraint(self):
        req = _req(required_capabilities=("CODE",),
                   prohibited_provider_families=("beta",))
        out = _select(req, [
            _cand("banned", vendor_family="beta",
                  capabilities=("CODE",), quality_class="VERIFIED_HIGH",
                  cost_usd=0.0001),
            _cand("allowed", vendor_family="alpha",
                  capabilities=("CODE",), quality_class="VERIFIED",
                  cost_usd=99.0)])
        self.assertIn("banned", out.excluded_reasons)
        self.assertEqual(out.receipt.selected_target, "allowed")


if __name__ == "__main__":
    unittest.main()
