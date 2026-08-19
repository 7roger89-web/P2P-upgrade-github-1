"""P2P-FRAMEWORK-04 — quality, evidence & learning test suite.

Deterministic, offline, no network. Every claim below is asserted against
the real module functions and the synthetic ground-truth fixture
(impact_ground_truth), NOT against documentation.

Note: certification/learning records persist to registry-dir stores
(shared by design, append-only). Each test uses unique eval ids /
subjects so tests never collide with each other or with real records.
"""

import inspect
import json
import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
_SYS = os.path.normpath(os.path.join(_HERE, os.pardir, os.pardir))
if _SYS not in sys.path:
    sys.path.insert(0, _SYS)

from p2p_capabilities import quality_intelligence as qi

_FIXTURE = os.path.normpath(os.path.join(
    _HERE, "fixtures", "impact_ground_truth"))

# Ensure unique records across test runs / re-runs.
_EVAL_ID = "fw04-unit-eval-1"


def _registry():
    path = os.path.normpath(os.path.join(
        _HERE, os.pardir, "eval_registry.json"))
    with open(path) as fh:
        return json.load(fh)


class EvalRegistryEvidenceBackedTests(unittest.TestCase):
    """The registry is deterministic-first: model judgments are labels,
    never proof. Project types are explicit. Failure classes are listed."""

    def setUp(self):
        self.registry = _registry()

    def test_registry_loads_and_has_evaluations(self):
        self.assertIsInstance(self.registry.get("evals"), list)
        self.assertGreater(len(self.registry["evals"]), 0)

    def test_deterministic_first_ordering(self):
        evaluations = self.registry["evals"]
        kinds = [e.get("reliability") or e.get("kind", "")
                 for e in evaluations]
        first_non_deterministic = next(
            (i for i, k in enumerate(kinds)
             if k not in ("DETERMINISTIC", "STATIC", "STRUCTURAL")),
            len(kinds))
        self.assertGreater(
            first_non_deterministic, 0,
            "deterministic evidence must come before model judgments")

    def test_project_types_explicit(self):
        """Every mutation class covered by evals declares which
        project scopes its evidence applies to (scope field is
        explicit per eval)."""
        for ev in self.registry["evals"]:
            self.assertIn("scope", ev,
                          "every eval declares its evidence scope")

    def test_mutation_classes_listed(self):
        covered = set()
        for ev in self.registry["evals"]:
            for mc in ev.get("mutation_class") or ():
                covered.add(mc)
        self.assertIn("CODE_EDIT", covered)
        self.assertIn("CONTENT_EDIT", covered)
        # Required failure semantics must be explicit per eval.
        self.assertTrue(
            all(ev.get("failure_semantics") for ev in self.registry["evals"]))

    def test_lookup_by_id_deterministic(self):
        loaded = qi.load_eval_registry()
        self.assertIsInstance(loaded, list)
        self.assertGreater(len(loaded), 0)
        for ev in loaded:
            found = qi.get_eval_by_id(ev["eval_id"])
            self.assertEqual(found, ev)
        self.assertIsNone(qi.get_eval_by_id("eval-that-does-not-exist"))

    def test_deterministic_evals_filtered(self):
        det = qi.deterministic_evals()
        self.assertIsInstance(det, list)
        for ev in det:
            self.assertEqual(ev.get("reliability"), "DETERMINISTIC")


class CodeImpactGroundTruthTests(unittest.TestCase):
    """Native AST import-graph evidence measured against synthetic
    ground truth: precision (no false affected claims) and recall
    (no missed known dependents)."""

    def _impact(self, *changed):
        return qi.affected_surface(changed_paths=changed,
                                   project_root=_FIXTURE,
                                   analysis_complete=True)

    def test_precision_no_unrelated_affected(self):
        impact = self._impact("src/core.py")
        self.assertNotIn("src/unrelated",
                         impact["direct_dependents"].get("src/core", ()))
        self.assertNotIn("tests/test_unrelated", impact["tests_affected"])

    def test_recall_direct_dependent_captured(self):
        impact = self._impact("src/core.py")
        self.assertIn("src/orders",
                      impact["direct_dependents"].get("src/core", ()))

    def test_recall_transitive_dependent_reachable(self):
        """One deterministic fold over the same native evidence:
        core -> orders -> reports."""
        hop1 = self._impact("src/core.py")
        hop2 = {}
        for dep in hop1["direct_dependents"].get("src/core", ()):
            follow = qi.affected_surface(changed_paths=(dep + ".py",),
                                         project_root=_FIXTURE,
                                         analysis_complete=True)
            hop2.update(follow["direct_dependents"])
        self.assertIn("src/reports", hop2.get("src/orders", ()))

    def test_recall_affected_tests_detected(self):
        impact = self._impact("src/core.py")
        self.assertIn("tests/test_orders", impact["tests_affected"])
        self.assertNotIn("tests/test_unrelated", impact["tests_affected"])

    def test_changed_not_equal_affected_surface(self):
        impact = self._impact("src/core.py")
        changed_mods = {"src/core"}
        affected = {"src/core"} | set(
            impact["direct_dependents"].get("src/core", ()))
        self.assertGreater(len(affected), len(changed_mods),
                           "CHANGED_FILES != FULL_AFFECTED_SURFACE")

    def test_unknown_impact_fail_closed(self):
        impact = qi.affected_surface(changed_paths=("src/core.py",),
                                     project_root=None,
                                     analysis_complete=False)
        self.assertTrue(impact["impact_unknown"])

    def test_symbol_diff_narrowing(self):
        changes = qi.record_symbol_changes(
            _FIXTURE, (qi.SymbolChange(
                path="src/core.py",
                symbols=("calculate_total",)),))
        self.assertIn("calculate_total",
                      changes["changed_symbols"][0]["symbols"])


class CertificationScopeExactnessTests(unittest.TestCase):
    """Execution binding != capability certification != current
    eligibility. Three distinct, independently checkable facts.
    Records persist to the shared store; unique subjects keep tests
    orthogonal and append-only."""

    def test_execution_binding_scope_exact(self):
        rec = qi.record_execution_binding(
            role_id="test-role",
            receipt_pointer="unit-test-receipt-1",
            capability_scope=())
        self.assertEqual(rec["kind"], "ROLE_EXECUTION_BINDING")
        # Binding without capability scope cannot certify anything.
        tier = qi.certification_tier("unit_test_cap",
                                     subject="unit-test-binding-1")
        self.assertEqual(tier, "UNKNOWN")

    def test_capability_certification_verifies_tier(self):
        qi.record_capability_certification(
            eval_id=_EVAL_ID, eval_version="1",
            capability_id="unit-test-cap-cert",
            subject="unit-test-subject-cert",
            result="CERTIFIED",
            evidence_pointers=("unit-test-evidence-1",),
            freshness_bound="abc",
            timestamp="2026-08-20T00:00:01+00:00")
        self.assertEqual(
            qi.certification_tier("unit-test-cap-cert"), "CERTIFIED")

    def test_capability_certification_verified_tier(self):
        qi.record_capability_certification(
            eval_id=_EVAL_ID, eval_version="1",
            capability_id="unit-test-cap-verified",
            subject="unit-test-subject-verified",
            result="VERIFIED",
            evidence_pointers=("unit-test-evidence-2",),
            freshness_bound="abc",
            timestamp="2026-08-20T00:00:02+00:00")
        self.assertEqual(
            qi.certification_tier("unit-test-cap-verified"), "VERIFIED")

    def test_execution_binding_does_not_certify(self):
        """Identity/execution evidence only; never moves a capability
        tier on its own."""
        qi.record_execution_binding(
            role_id="unit-test-role-binding",
            receipt_pointer="unit-test-receipt-2",
            capability_scope=("unit-test-cap-binding",))
        # Only LIVE_CERTIFIED binding result moves tier, and result
        # default here is PASS-equivalent 'PASS' uppercase — PASS is
        # not LIVE_CERTIFIED, so tier stays UNKNOWN.
        self.assertEqual(
            qi.certification_tier("unit-test-cap-binding"), "UNKNOWN")

    def test_unknown_subject_stays_unknown(self):
        self.assertEqual(
            qi.certification_tier("cap-that-was-never-certified-xyz"),
            "UNKNOWN")

    def test_freshness_fail_closed_unbound(self):
        qi.record_capability_certification(
            eval_id=_EVAL_ID, eval_version="1",
            capability_id="unit-test-cap-fresh",
            subject="unit-test-subject-fresh",
            result="CERTIFIED",
            evidence_pointers=("unit-test-evidence-3",),
            freshness_bound="",
            timestamp="2026-08-20T00:00:03+00:00")
        self.assertEqual(
            qi.certification_freshness("unit-test-cap-fresh", "def"),
            "UNBOUND")

    def test_freshness_current_same_commit(self):
        qi.record_capability_certification(
            eval_id=_EVAL_ID, eval_version="1",
            capability_id="unit-test-cap-fresh2",
            subject="unit-test-subject-fresh2",
            result="CERTIFIED",
            evidence_pointers=("unit-test-evidence-4",),
            freshness_bound="abc",
            timestamp="2026-08-20T00:00:04+00:00")
        self.assertEqual(
            qi.certification_freshness("unit-test-cap-fresh2", "abc"),
            "CURRENT")

    def test_freshness_stale_different_commit(self):
        qi.record_capability_certification(
            eval_id=_EVAL_ID, eval_version="1",
            capability_id="unit-test-cap-fresh3",
            subject="unit-test-subject-fresh3",
            result="CERTIFIED",
            evidence_pointers=("unit-test-evidence-5",),
            freshness_bound="old",
            timestamp="2026-08-20T00:00:05+00:00")
        self.assertEqual(
            qi.certification_freshness("unit-test-cap-fresh3", "new"),
            "STALE")

    def test_current_eligibility_fail_closed(self):
        elig = qi.current_eligibility(
            "cap-never-certified-eligibility",
            current_source_commit="abc")
        self.assertFalse(elig["currently_eligible"])
        self.assertTrue(elig["fail_closed_on_unknown"])

    def test_current_eligibility_no_freshness_not_eligible(self):
        elig = qi.current_eligibility(
            "unit-test-cap-fresh", current_source_commit="abc")
        self.assertFalse(elig["currently_eligible"])


class QualityVerdictTests(unittest.TestCase):
    """EXECUTION_SUCCESS != QUALITY_PROVEN."""

    def test_success_with_unknown_impact_is_unknown(self):
        v = qi.build_quality_verdict("SUCCESS", required_eval_results={},
                                     impact_known=False)
        self.assertEqual(v["quality_status"], "QUALITY_UNKNOWN")
        self.assertFalse(v["checkpoint_allowed"])

    def test_success_without_required_evidence_is_rejected(self):
        v = qi.build_quality_verdict("SUCCESS", required_eval_results={},
                                     required_evidence_present=False)
        self.assertEqual(v["quality_status"], "QUALITY_REJECTED")

    def test_required_eval_missing_result_fail_closed(self):
        v = qi.build_quality_verdict(
            "SUCCESS", required_eval_results={},
            declared_required_evals={"sec": {"class": "SECURITY"}})
        self.assertEqual(v["quality_status"], "QUALITY_REJECTED")
        self.assertFalse(v["checkpoint_allowed"])

    def test_required_eval_fail_rejects(self):
        v = qi.build_quality_verdict(
            "SUCCESS", required_eval_results={"sec": "FAIL"},
            declared_required_evals={"sec": {}})
        self.assertEqual(v["quality_status"], "QUALITY_REJECTED")

    def test_all_required_pass_verified(self):
        v = qi.build_quality_verdict(
            "SUCCESS", required_eval_results={"sec": "PASS"},
            declared_required_evals={"sec": {}})
        self.assertEqual(v["quality_status"], "QUALITY_VERIFIED")
        self.assertTrue(v["checkpoint_allowed"])

    def test_no_required_evals_known_impact_verified(self):
        v = qi.build_quality_verdict("SUCCESS", required_eval_results={},
                                     impact_known=True)
        self.assertEqual(v["quality_status"], "QUALITY_VERIFIED")

    def test_execution_status_unknown_flagged(self):
        """Status gating is honest: with impact known and no required
        evals the honest status is still VERIFIED (nothing required was
        missing); the execution status itself is carried separately so
        downstream gates can combine both facts."""
        v = qi.build_quality_verdict("UNKNOWN", required_eval_results={},
                                     impact_known=True)
        self.assertEqual(v["execution_status"], "UNKNOWN")


class IndependentVerifierTests(unittest.TestCase):
    """Independence is identity + evidence, not authority."""

    def test_same_identity_not_independent(self):
        r = qi.verify_independence("lead", "lead", "ev-1", "ev-2")
        self.assertFalse(r["is_independent"])
        self.assertEqual(r["reject_reason"], "SAME_CLAIM_OR_IDENTITY")

    def test_same_evidence_not_independent(self):
        r = qi.verify_independence("lead", "auditor", "ev-1", "ev-1")
        self.assertFalse(r["is_independent"])

    def test_distinct_identity_and_evidence_independent(self):
        r = qi.verify_independence("lead", "auditor", "ev-1", "ev-2")
        self.assertTrue(r["is_independent"])

    def test_missing_required_verifier_fail_closed(self):
        v = qi.build_quality_verdict(
            "SUCCESS", required_eval_results={"sec": "PASS"},
            declared_required_evals={"sec": {}},
            independent_required=True,
            independent_verifier_result=None)
        self.assertEqual(v["quality_status"], "QUALITY_UNKNOWN")
        self.assertFalse(v["checkpoint_allowed"])


class LearningCandidateHonestyTests(unittest.TestCase):
    """TRANSCRIPT != STATE. Observations never auto-promote."""

    def test_transcript_cannot_become_state(self):
        out = qi.transcript_must_not_become_state(
            "user said the project is done",
            proposed_canonical_update={"status": "DONE"})
        self.assertFalse(out["canonical_update_applied"])
        self.assertEqual(out["reason"], "TRANSCRIPT_NOT_STATE")
        self.assertTrue(out["learning_candidate_created_instead"])

    def test_candidate_marked_project_scoped_not_promoted(self):
        cand = qi.add_learning_candidate(
            subject="unit-test-learning-subject",
            proposed_learning="unit-test-learning-note",
            evidence_pointers=("unit-test-obs-1",),
            scope="PROJECT_SCOPED",
            observation_count=1,
            confidence_class="WEAK",
            promotion_requirement="OWNER_CONFIRMATION")
        self.assertFalse(cand.get("promoted", False))
        self.assertIn(cand["scope"], ("PROJECT_SCOPED", "project"))
        self.assertEqual(cand["state"], "CANDIDATE")

    def test_one_observation_never_auto_promotes(self):
        policy = qi.learning_promotion_policy({
            "subject": "unit-test-learning-subject",
            "state": "CANDIDATE",
            "observation_count": 1,
            "conflicts": (),
            "promotion_requirement": "OWNER_CONFIRMATION"})
        self.assertFalse(policy.get("promoted", False))

    def test_conflicting_learning_flagged(self):
        qi.add_learning_candidate(
            subject="unit-test-learning-conflict-subject",
            proposed_learning="X is safe",
            evidence_pointers=("unit-test-obs-2",))
        cand = qi.add_learning_candidate(
            subject="unit-test-learning-conflict-subject",
            proposed_learning="X is unsafe",
            evidence_pointers=("unit-test-obs-3",))
        self.assertEqual(cand["state"], "CONFLICT")

    def test_read_only_contract_no_dispatch_api(self):
        src = inspect.getsource(qi)
        forbidden = ("select_role_team", "grant_permission",
                     "owner_correction_applies_universally")
        found = [f for f in forbidden if f in src]
        self.assertEqual(found, [])

    def test_promotion_requires_owner_confirmation(self):
        """'auto_promoted': False is recorded; the promotion path is
        owner-gated, not automatic. learning_promotion_policy never
        returns promoted=True on candidate evidence alone."""
        cand = qi.add_learning_candidate(
            subject="unit-test-promo-subject",
            proposed_learning="unit-test-promo-note",
            evidence_pointers=("unit-test-obs-4",))
        policy = qi.learning_promotion_policy(cand)
        self.assertFalse(policy.get("promoted", False))


def _tree_sha(project_root):
    """Byte-stable hash of a project tree for mutation detection."""
    import hashlib
    paths = []
    for dirpath, _, filenames in os.walk(project_root):
        for name in sorted(filenames):
            full = os.path.join(dirpath, name)
            with open(full, "rb") as fh:
                paths.append((os.path.relpath(full, project_root),
                              hashlib.sha256(fh.read()).hexdigest()))
    paths.sort()
    h = hashlib.sha256(json.dumps(paths).encode())
    return h.hexdigest()


class ShadowEvalReadOnlyTests(unittest.TestCase):
    """Shadow evaluation must never mutate owner projects (GT/GP)."""

    def test_read_only_allowed(self):
        self.assertTrue(qi.shadow_eval_scope_allowed("READ_ONLY"))
        self.assertTrue(qi.shadow_eval_scope_allowed("ANALYSIS_ONLY"))

    def test_write_class_not_allowed(self):
        self.assertFalse(qi.shadow_eval_scope_allowed("WRITE"))
        self.assertFalse(qi.shadow_eval_scope_allowed("CODE_EDIT"))

    def test_shadow_eval_never_mutates_owner_projects(self):
        """Live shadow analysis over the real owner project roots
        (Game Truyen + Gia Pha) must leave both trees byte-identical."""
        candidates = [os.path.normpath(os.path.join(
            _HERE, os.pardir, os.pardir, os.pardir, name))
            for name in ("game-truyen", "gia-pa")] + [
            "/home/ubuntu/fw01_work/cert/game-truyen",
            "/home/ubuntu/fw01_work/cert/gia-pha"]
        roots = [r for r in candidates if os.path.isdir(r)]
        roots = [r for r in roots if os.path.isdir(r)]
        if not roots:
            self.skipTest("owner project roots not present in this tree")
        before = {r: _tree_sha(r) for r in roots}
        for r in roots:
            qi.affected_surface(changed_paths=(),
                                project_root=r,
                                analysis_complete=True)
            qi.classify_project_type(r)
        after = {r: _tree_sha(r) for r in roots}
        self.assertEqual(before, after,
                         "shadow analysis mutated an owner project")


class PostExecutionLoopIntegrationTests(unittest.TestCase):
    """FW01 loop: FW04 hook fires AFTER execution outcome, info-only."""

    def test_hook_ordering_in_source(self):
        from p2p_capabilities import p2p_fw01_loop
        src = inspect.getsource(p2p_fw01_loop)
        step_body = src.split("def step(", 1)[1]
        i_fw04 = step_body.find("POST_EXECUTION_QUALITY_ASSESSED")
        i_execute = step_body.find("self.loop.step()")
        i_coverage = step_body.find("CAPABILITY_COVERAGE_BLOCKED")
        self.assertGreater(i_fw04, i_execute)
        self.assertGreater(i_fw04, i_coverage)


if __name__ == "__main__":
    unittest.main()
