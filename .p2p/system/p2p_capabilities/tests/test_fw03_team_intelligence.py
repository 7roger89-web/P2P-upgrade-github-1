"""P2P-FRAMEWORK-03 — Adaptive Team & Council test suite.

Deterministic, fail-closed coverage of team_intelligence.py and the
FW01-loop FW03 hook contract. Never re-asserts what the FW02 suites
already prove; covers only the FW03 surface and its integration seam.
"""
import json
import unittest

from p2p_capabilities import team_intelligence as ti
from p2p_capabilities import capability_intelligence as ci


def _role(cid, requires=(), ev="", prov=None):
    return {"CAPABILITY_ID": cid, "TYPE": "role",
            "REQUIRES": tuple(requires),
            "EVIDENCE_CONTRACT": ev,
            "UPSTREAM_PROVENANCE": dict(prov) if prov else {}}


def _elig(**flags):
    return {"eligible": True, **flags}


CANON = ["p2p_iris", "p2p_tecton", "p2p_axiom", "p2p_vector",
         "p2p_datos", "p2p_anon", "p2p_architecton", "p2p_helios"]

RECORDS = [
    _role("p2p_iris"),
    _role("p2p_tecton", ["design_intelligence_nui"]),
    _role("p2p_axiom", ["unit_test_execution", "security_audit"]),
    _role("p2p_vector"),
    _role("p2p_datos", ["fact_ledger_writes"]),
    _role("p2p_anon", ["security_audit"]),
    _role("p2p_architecton", ["architecture_review"]),
    _role("p2p_helios", ["evidence_audit"]),
    _role("p2p_aesthetica", ["ux_design"]),
]

ELIG = {r["CAPABILITY_ID"]: _elig() for r in RECORDS}


def _req(cap):
    return ci.CapabilityRequirement(
        capability_id=cap, required_or_optional="REQUIRED",
        fallback_allowed="NO_DISPATCH", origin="INFERRED")


class TestFw03TeamDecision(unittest.TestCase):
    """Minimal sufficient team selection (section 5)."""

    def test_single_role_when_one_role_covers(self):
        d = ti.build_team_decision(
            required_capabilities=("design_intelligence_nui",),
            registry_records=RECORDS, eligibility_results=ELIG,
            fan_out_bound=8)
        self.assertEqual(d.team_mode, "SINGLE_ROLE")
        self.assertEqual(d.participant_roles, ("p2p_tecton",))
        self.assertEqual(d.provided_capabilities,
                         ("design_intelligence_nui",))
        self.assertEqual(d.failure_class, "")

    def test_small_team_when_coverage_splits(self):
        d = ti.build_team_decision(
            required_capabilities=("design_intelligence_nui",
                                   "unit_test_execution"),
            registry_records=RECORDS, eligibility_results=ELIG,
            fan_out_bound=8)
        self.assertIn(d.team_mode, ("SMALL_TEAM", "COUNCIL"))
        self.assertGreater(len(d.participant_roles), 1)
        self.assertTrue(
            set(d.provided_capabilities) >=
            {"design_intelligence_nui", "unit_test_execution"})

    def test_insufficient_team_capability_fail_closed(self):
        d = ti.build_team_decision(
            required_capabilities=("ghost_capability_x",),
            registry_records=RECORDS, eligibility_results=ELIG,
            fan_out_bound=8)
        self.assertEqual(d.failure_class, "INSUFFICIENT_TEAM_CAPABILITY")
        self.assertEqual(d.required_capabilities,
                         ("ghost_capability_x",))
        self.assertEqual(d.participant_roles, ())

    def test_no_eligible_role_fail_closed(self):
        elig = {r: _elig(eligible=False,
                         reasons=["scope-insufficient"])
                for r in CANON}
        d = ti.build_team_decision(
            required_capabilities=("design_intelligence_nui",),
            registry_records=RECORDS, eligibility_results=elig,
            fan_out_bound=8)
        self.assertEqual(d.failure_class, "NO_ELIGIBLE_ROLE")

    def test_ineligible_role_never_selected(self):
        elig = dict(ELIG)
        elig["p2p_tecton"] = _elig(eligible=False,
                                   reasons=["scope-insufficient:x"])
        elig["p2p_axiom"] = _elig(eligible=False,
                                  reasons=["scope-insufficient:y"])
        d = ti.build_team_decision(
            required_capabilities=("design_intelligence_nui",),
            registry_records=RECORDS, eligibility_results=elig,
            fan_out_bound=8)
        self.assertNotIn("p2p_tecton", d.participant_roles)
        self.assertNotIn("p2p_axiom", d.participant_roles)

    def test_architecture_risk_escalates_to_council(self):
        d = ti.build_team_decision(
            required_capabilities=("design_intelligence_nui",
                                   "unit_test_execution",
                                   "security_audit",
                                   "architecture_review"),
            registry_records=RECORDS, eligibility_results=ELIG,
            task_risk_class="ARCHITECTURE", fan_out_bound=8)
        self.assertEqual(d.team_mode, "COUNCIL")
        self.assertGreaterEqual(len(d.participant_roles), 3)
        self.assertLessEqual(len(d.participant_roles), 8)

    def test_fan_out_bound_enforced(self):
        d = ti.build_team_decision(
            required_capabilities=tuple(
                "cap_%d" % i for i in range(20)),
            registry_records=RECORDS, eligibility_results=ELIG,
            fan_out_bound=3)
        self.assertLessEqual(len(d.participant_roles), 3)

    def test_decision_trace_nonempty_and_deterministic(self):
        d1 = ti.build_team_decision(
            required_capabilities=("design_intelligence_nui",),
            registry_records=RECORDS, eligibility_results=ELIG,
            fan_out_bound=8)
        d2 = ti.build_team_decision(
            required_capabilities=("design_intelligence_nui",),
            registry_records=RECORDS, eligibility_results=ELIG,
            fan_out_bound=8)
        self.assertGreater(len(d1.decision_trace), 0)
        self.assertEqual(d1.to_dict(), d2.to_dict())

    def test_to_dict_json_roundtrip(self):
        d = ti.build_team_decision(
            required_capabilities=("design_intelligence_nui",),
            registry_records=RECORDS, eligibility_results=ELIG,
            fan_out_bound=8)
        blob = json.dumps(d.to_dict())
        self.assertEqual(json.loads(blob)["team_mode"], d.team_mode)

    def test_optional_specialist_excluded_from_canonical_team(self):
        # Governance: p2p_aesthetica is the OPTIONAL specialist role and
        # is never part of the canonical team selection surface.
        elig = dict(ELIG)
        elig["p2p_aesthetica"] = _elig(eligible=True)
        recs = list(RECORDS)
        d = ti.build_team_decision(
            required_capabilities=("ux_design",),
            registry_records=recs, eligibility_results=elig,
            fan_out_bound=8)
        # Even with the specialist eligible and its self-capability
        # carrying ux_design, the canonical team never includes
        # the optional specialist.
        self.assertNotIn("p2p_aesthetica", d.participant_roles)
        self.assertEqual(d.failure_class,
                         "INSUFFICIENT_TEAM_CAPABILITY")


class TestFw03EvidenceTiers(unittest.TestCase):
    """Evidence tier semantics (section 6): UNKNOWN != SAFE."""

    def test_declared_only_causes_unknown_when_live_required(self):
        ev = ti.role_capability_evidence(
            "p2p_axiom", RECORDS, live_required=True)
        # no verified/certified surface on the real registry record
        for e in ev:
            self.assertIn(e.evidence_tier,
                          ("UNKNOWN", "DECLARED", "VERIFIED"))
        # live-required counting: DECLARED does not count
        for e in ev:
            if e.evidence_tier == "DECLARED":
                self.assertEqual(
                    e.capability_id in set(), True)

    def test_no_hallucination_unknown_role(self):
        ev = ti.role_capability_evidence("ghost_role", RECORDS)
        self.assertEqual(len(ev), 1)
        self.assertEqual(ev[0].evidence_tier, "UNKNOWN")

    def test_verified_uplift_requires_evidence_surface(self):
        # No evidence contract surface -> tier stays DECLARED.
        recs = [_role("p2p_iris", ev="")]
        ev = ti.role_capability_evidence("p2p_iris", recs)
        self.assertEqual(ev[0].evidence_tier, "DECLARED")
        recs2 = [_role("p2p_iris", prov={"audit": "CERTIFIED"})]
        ev2 = ti.role_capability_evidence("p2p_iris", recs2)
        self.assertIn(ev2[0].evidence_tier,
                      ("CERTIFIED", "LIVE_CERTIFIED"))

    def test_target_incompatibility_does_not_count(self):
        elig_res = {"eligible": False, "reasons": ["UNKNOWN_scope:x"]}
        ev = ti.role_capability_evidence(
            "p2p_axiom", RECORDS, live_required=False,
            target_eligibility_result=elig_res)
        for e in ev:
            self.assertEqual(e.target_compatibility, "incompatible")

    def test_invariant_unknown_never_counts_in_provided(self):
        elig = {"p2p_axiom": _elig()}
        d = ti.build_team_decision(
            required_capabilities=("ghost_capability",),
            registry_records=RECORDS, eligibility_results=elig,
            live_required=True, fan_out_bound=8)
        self.assertEqual(d.provided_capabilities, ())


class TestFw03CompositionIntegration(unittest.TestCase):
    """FW03 composition evidence honors the FW02 fail-closed contract
    (section 7): FW03 grounds provided_capabilities; FW02's gate keeps
    authority; no upgrade path to COMPLETE without grounded evidence."""

    def setUp(self):
        elig = {"p2p_tecton": _elig()}
        self.decision = ti.build_team_decision(
            required_capabilities=("design_intelligence_nui",),
            registry_records=RECORDS, eligibility_results=elig,
            fan_out_bound=8)
        self.evidence = ti.composition_evidence_from_team_decision(
            self.decision)

    def test_evidence_grounded(self):
        self.assertEqual(self.evidence.selected_roles,
                         self.decision.participant_roles)
        self.assertEqual(self.evidence.provided_capabilities,
                         self.decision.provided_capabilities)

    def test_project_available_but_composition_insufficient_blocks(self):
        # project coverage is not what the composition gate measures;
        # when the selected composition provides nothing, coverage over
        # required caps is not COMPLETE regardless of inventory.
        reqs = [_req("design_intelligence_nui"),
                _req("unit_test_execution")]
        state, missing, ok = ci.evaluate_composition_coverage(
            reqs, self.evidence)
        self.assertIn(state, ("UNKNOWN", "INCOMPLETE"))
        self.assertFalse(ok)

    def test_provided_matches_reqs_completes(self):
        reqs = [_req("design_intelligence_nui")]
        state, missing, ok = ci.evaluate_composition_coverage(
            reqs, self.evidence)
        self.assertEqual(state, "COMPLETE")
        self.assertTrue(ok)

    def test_no_empty_evidence_points_claim_complete(self):
        empty = ci.CompositionCapabilityEvidence(
            selected_roles=(), selected_target=ci.UNKNOWN,
            provided_capabilities=(), evidence_pointers=())
        reqs = [_req("design_intelligence_nui")]
        state, missing, ok = ci.evaluate_composition_coverage(
            reqs, empty)
        self.assertIn(state, ("UNKNOWN", "INCOMPLETE"))
        self.assertFalse(ok)


class TestFw03Council(unittest.TestCase):
    """Bounded adaptive council (section 8): never auto-8."""

    def test_adaptive_sizing_low(self):
        s = ti.adaptive_council_size(
            task_risk_class="LOW", eligible_roles=CANON,
            receipts_with_verification=0, fan_out_bound=8)
        self.assertEqual(s["adaptive_size"], 2)
        self.assertTrue(s["bounded"])

    def test_adaptive_sizing_medium(self):
        s = ti.adaptive_council_size(
            task_risk_class="MEDIUM", eligible_roles=CANON,
            receipts_with_verification=2, fan_out_bound=8)
        self.assertEqual(s["adaptive_size"], 3)

    def test_honest_n_over_8_reporting(self):
        q = {"decision": "INCOMPLETE",
             "required_roles": CANON,
             "satisfied_roles": ["p2p_datos", "p2p_anon"],
             "missing_roles": ["p2p_iris"],
             "disqualified_receipts": [1],
             "duplicate_receipts": []}
        r = ti.council_integrity_report(q)
        self.assertEqual(r["honest_report"], "2/8")
        self.assertFalse(r["claims_live_council_8_of_8"])
        self.assertEqual(r["disqualified_count"], 1)

    def test_full_canonical_only_when_all_evidenced(self):
        q = {"decision": "COMPLETE", "required_roles": CANON,
             "satisfied_roles": CANON, "missing_roles": [],
             "disqualified_receipts": [], "duplicate_receipts": []}
        r = ti.council_integrity_report(q)
        self.assertEqual(r["honest_report"], "8/8")
        self.assertTrue(r["claims_live_council_8_of_8"])

    def test_live_council_claim_rejected_when_disqualified(self):
        q = {"decision": "COMPLETE", "required_roles": CANON,
             "satisfied_roles": CANON, "missing_roles": [],
             "disqualified_receipts": [1], "duplicate_receipts": []}
        r = ti.council_integrity_report(q)
        self.assertFalse(r["claims_live_council_8_of_8"])


class TestFw03CouncilContract(unittest.TestCase):
    """Council execution contract bounds (section 10)."""

    def test_valid_read_only_contract(self):
        c = ti.CouncilExecutionContract(
            task_id="t1", participant_ids=("a", "b"),
            role_identities=("r1", "r2"),
            retry_bound=1, mutation_permission="READ_ONLY")
        self.assertEqual(c.retry_bound, 1)
        self.assertTrue(c.council_id.startswith("council-"))
        self.assertTrue(c.cancellation_token.startswith("cancel-"))

    def test_participant_bound(self):
        with self.assertRaises(ValueError) as ctx:
            ti.CouncilExecutionContract(
                task_id="t1",
                participant_ids=tuple("x%d" % i for i in range(9)),
                role_identities=tuple("r%d" % i for i in range(9)))
        self.assertIn("BOUND", str(ctx.exception))

    def test_retry_bound(self):
        with self.assertRaises(ValueError):
            ti.CouncilExecutionContract(
                task_id="t1", participant_ids=("a",),
                role_identities=("r1",), retry_bound=5)

    def test_task_id_required(self):
        with self.assertRaises(TypeError):
            ti.CouncilExecutionContract(
                participant_ids=("a",), role_identities=("r1",))

    def test_aggregation_must_be_task_aware(self):
        with self.assertRaises(ValueError):
            ti.CouncilExecutionContract(
                task_id="t1", participant_ids=("a",),
                role_identities=("r1",),
                aggregation_policy="MAJORITY_WINS")


class TestFw03Aggregation(unittest.TestCase):
    """Task-aware aggregation (section 12): conflicts never wash out."""

    def test_unanimous_fact_verification(self):
        a = ti.aggregate_council_results(
            task_type="FACT_VERIFICATION",
            results=[{"claim": "X", "confidence": 2,
                      "evidence_refs": ("e1",)}] * 3)
        self.assertEqual(a["aggregated_verdict"], "VERIFIED")
        self.assertFalse(a["conflict"])

    def test_fact_conflict_recorded(self):
        a = ti.aggregate_council_results(
            task_type="FACT_VERIFICATION",
            results=[{"claim": "X", "confidence": 2,
                      "evidence_refs": ("e1",)},
                     {"claim": "Y", "confidence": 2,
                      "evidence_refs": ("e2",)}])
        self.assertEqual(a["aggregated_verdict"], "FACT_CONFLICT")
        self.assertEqual(a["failure_class"], "COUNCIL_RESULT_CONFLICT")
        self.assertEqual(set(a["claims"]), {"X", "Y"})

    def test_design_divergence_never_washed(self):
        a = ti.aggregate_council_results(
            task_type="DESIGN_JUDGMENT",
            results=[{"claim": "option-a", "confidence": 1,
                      "evidence_refs": ("e1",)},
                     {"claim": "option-b", "confidence": 1,
                      "evidence_refs": ("e2",)}])
        self.assertEqual(a["aggregated_verdict"], "CONFLICT")
        self.assertEqual(len(a["unresolved_items"]), 1)

    def test_no_claims_flagged(self):
        a = ti.aggregate_council_results(
            task_type="FACT_VERIFICATION",
            results=[{"claim": "", "confidence": 0,
                      "evidence_refs": ()},
                     {"claim": "", "confidence": 0,
                      "evidence_refs": ()}])
        self.assertEqual(a["aggregated_verdict"], "NO_CLAIMS")

    def test_unknown_task_type_fails_closed(self):
        with self.assertRaises(ValueError):
            ti.aggregate_council_results(
                task_type="GHOST_TYPE", results=[])


class TestFw03Revalidation(unittest.TestCase):
    """Pre-dispatch revalidation of the selection evidence (section 15)."""

    def test_preserved_when_unchanged(self):
        elig = {"p2p_tecton": _elig()}
        d = ti.build_team_decision(
            required_capabilities=("design_intelligence_nui",),
            registry_records=RECORDS, eligibility_results=elig,
            fan_out_bound=8)
        st = ti.revalidate_selection(
            decision=d,
            current_required_capabilities=("design_intelligence_nui",),
            current_role_eligibility={"p2p_tecton": _elig()},
            current_target_id="t")
        self.assertTrue(st["decision_preserved"])
        self.assertEqual(st["failure_class"], "")

    def test_drift_detected(self):
        elig = {"p2p_tecton": _elig()}
        d = ti.build_team_decision(
            required_capabilities=("design_intelligence_nui",),
            registry_records=RECORDS, eligibility_results=elig,
            fan_out_bound=8)
        st = ti.revalidate_selection(
            decision=d,
            current_required_capabilities=("ghost_capability",),
            current_role_eligibility={"p2p_tecton": _elig()},
            current_target_id="t")
        self.assertFalse(st["decision_preserved"])
        self.assertEqual(st["failure_class"], "POST_SELECTION_DRIFT")
        self.assertTrue(st["reselect_bounded"])


class TestFw03OwnerSummary(unittest.TestCase):
    """Beginner-first summary (section 13)."""

    def test_summary_single(self):
        elig = {"p2p_tecton": _elig()}
        d = ti.build_team_decision(
            required_capabilities=("design_intelligence_nui",),
            registry_records=RECORDS, eligibility_results=elig,
            fan_out_bound=8)
        s = ti.owner_summary(d)
        self.assertIn("1", s["owner_facing_summary"])
        self.assertIn("chuyên gia", s["owner_facing_summary"])

    def test_summary_failure(self):
        d = ti.build_team_decision(
            required_capabilities=("ghost",),
            registry_records=RECORDS, eligibility_results=ELIG,
            fan_out_bound=8)
        s = ti.owner_summary(d)
        self.assertIn("không thể chọn đội", s["owner_facing_summary"])


class TestFw03LoopHookContract(unittest.TestCase):
    """The FW03 hook contract inside the real FW01 loop (section 11):
    info-only at decision time, enforcement keeps authority."""

    def test_hook_event_order(self):
        import sys
        import tempfile
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parents[4]))
        from p2p_capabilities.autopilot_state import GoalPlan
        from p2p_capabilities.p2p_fw01_loop import build_fw01_loop
        from p2p_capabilities.fake_execution_backend import (
            FakeDeterministicExecutionBackend)
        from p2p_capabilities.autopilot_verifier import TaskVerifier
        tmp = Path(tempfile.mkdtemp(prefix="fw03_lhc_"))
        (tmp / ".p2p" / "system").mkdir(parents=True)
        (tmp / ".p2p" / "state").mkdir()
        plan = GoalPlan(goal_id="fw03-lhc", goal_version="v1",
                        title="fw03 loop hook contract", purpose="t",
                        owner_approval_ref="oref-1", scope=("s",),
                        non_scope=(), plan_task_ids=("T1",))
        rec = {"T1": dict(status="READY", title="t1", description="d",
                          purpose="p", scope=("s",),
                          acceptance_requirements=("a",),
                          required_evidence=("ev-1",),
                          last_preflight={
                              "status": "PASS",
                              "checked_at":
                                  "2026-08-19T00:00:00Z",
                              "scope": (), "non_scope": (),
                              "acceptance_requirements": (),
                              "required_evidence": (),
                              "permission_needs": (),
                              "required_capabilities": (),
                              "context_refs": (), "output_refs": (),
                              "requirement_refs": (),
                              "decision_refs": ()},
                          skills=("skill_a",), team=("role_dev",),
                          permission_needs=("write",))}
        loop = build_fw01_loop(
            tmp, goal_plan=plan, task_records=rec,
            backend=FakeDeterministicExecutionBackend(),
            verifier=TaskVerifier())
        captured = []
        loop._trace = lambda tid, meta, kind, msg: captured.append(kind)
        loop.step()
        self.assertIn("ADAPTIVE_TEAM_DECISION", captured)
        i_h = captured.index("CAPABILITY_HANDOFF_BUILT")
        i_f = captured.index("ADAPTIVE_TEAM_DECISION")
        i_c = next(i for i, k in enumerate(captured)
                   if "CAPABILITY_COVERAGE" in k)
        self.assertLess(i_h, i_f)
        self.assertLess(i_f, i_c)
        self.assertEqual(captured[-1], "CAPABILITY_COVERAGE_BLOCKED")

    def test_no_duplicate_router(self):
        """FW03 must not import or instantiate any selection/dispatch
        machinery: only info + canonical surfaces. Comments in the module
        docstring that name the surfaces are excluded from the check."""
        import inspect
        src = inspect.getsource(ti)
        code = src.split('"""', 2)[-1]
        forbidden = ["select_role_team", "dispatch_role",
                     "select_next_safe_task"]
        for f in forbidden:
            self.assertNotIn(f, code)

    def test_no_fw02_semantic_change(self):
        """FW03 must not alter FW02 gate behavior or semantics."""
        import inspect
        src = inspect.getsource(ti)
        self.assertNotIn("evaluate_coverage(", src)
        self.assertNotIn("evaluate_composition_coverage(", src)
        # FW03 only CONSUMES the FW02 evidence type; never redefines it
        self.assertIn("CompositionCapabilityEvidence", src)


if __name__ == "__main__":
    unittest.main()
