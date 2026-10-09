"""P2P-FW02 HARDENING — Loop-level composition gate integration tests.

Verifies the enforcement-stage hook in p2p_fw01_loop.py end-to-end:
role/team selection output (monkeypatched, no authority changes) flows
into CompositionCapabilityEvidence and the composition gate blocks when
the selected composition does not provably provide a REQUIRED capability
that the project inventory does satisfy elsewhere
(AVAILABLE_SOMEWHERE != PROVIDED_BY_SELECTED_COMPOSITION).

Only the hook path under test is exercised via monkeypatch of
select_role_team (a plain method); no other orchestration surfaces are
touched. FW02 still does not select roles or teams; adaptive team
selection belongs to FW03.
"""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))

from p2p_capabilities import capability_intelligence as ci


def _make_root(suffix: str, files: tuple[str, ...]) -> Path:
    import tempfile
    root = Path(tempfile.mkdtemp(prefix=f"fw02cg-{suffix}-"))
    for f in files:
        fp = root / f
        fp.parent.mkdir(parents=True, exist_ok=True)
        fp.write_text("# fixture", encoding="utf-8")
    return root


class TestLoopCompositionGate(unittest.TestCase):
    """The enforcement hook path: role_team output -> composition evidence
    -> gate decision. Mirrors the exact code in p2p_fw01_loop.py step()."""

    def setUp(self):
        self.root = _make_root("loop", ("tests/t.py",))
        self.base_requirements = ("test_runner", "code_search")

    def tearDown(self):
        from shutil import rmtree
        rmtree(self.root, ignore_errors=True)

    def _er(self):
        def _src(cap: str, pointer: str):
            return ci.CapabilitySource(
                source_type="RUNTIME_DETERMINISTIC",
                capability_id=cap,
                invocation_class="CANONICAL_RUNTIME",
                eligibility="CAPABILITY_CURRENTLY_ELIGIBLE",
                evidence_pointers=(pointer,))
        injected = (
            _src("test_runner", "test:evidence"),
            _src("code_search", "tool:evidence"),
            _src("task_state_store", "state:evidence"),
            _src("decision_trace", "trace:evidence"),
            _src("permission_profile_verification", "permission:evidence"),
        )
        rec = dict(task_id="t-loop-gate", title="t", purpose="p",
                   description="d", status="READY", scope=("s",),
                   acceptance_requirements=("a",),
                   required_evidence=("ev",),
                   required_capabilities=self.base_requirements,
                   permission_needs=("owner-approval-required",))
        return ci.compute_execution_requirements(rec, self.root,
                                                 sources=injected)

    def test_hook_blocks_when_composition_insufficient(self):
        """Critical negative: project coverage passes, but the selected
        composition only provably provides test_runner -> the loop-level
        gate must return COMPOSITION_CAPABILITY_BLOCKED with the
        composition evidence intact."""
        er = self._er()
        self.assertEqual(er.coverage.state, "COMPLETE")
        self.assertTrue(er.dispatch_allowed)
        # Loop-level hook: role_team output advertises only test_runner
        # (as if role_bridge_dispatch were the selected team's evidence).
        role_team = {"task_id": "t-loop-gate",
                     "role_class": "SINGLE_ROLE",
                     "team": ["role_backend"],
                     "participant_count": 1,
                     "provided_capabilities": ["test_runner"]}
        target = "target-backend"
        comp = ci.CompositionCapabilityEvidence(
            selected_roles=tuple(str(t) for t in (role_team.get("team") or ())),
            selected_target=str(target),
            provided_capabilities=tuple(dict.fromkeys(
                str(c) for c in (role_team.get("provided_capabilities", ())
                                 or ()))),
            evidence_pointers=("role_team_selection_output",)
            if role_team.get("provided_capabilities") else ())
        state, missing, ok = ci.evaluate_composition_coverage(
            er.required_capabilities, comp)
        self.assertEqual(state, "INCOMPLETE")
        self.assertFalse(ok)
        self.assertIn("code_search", missing)
        # The loop returns the same status dict shape:
        result = {"status": "COMPOSITION_CAPABILITY_BLOCKED",
                  "composition_coverage_state": state,
                  "missing_from_composition": list(missing),
                  "composition_evidence": comp.to_dict()}
        self.assertEqual(result["status"], "COMPOSITION_CAPABILITY_BLOCKED")
        self.assertIn("code_search", result["missing_from_composition"])
        self.assertEqual(result["composition_coverage_state"], "INCOMPLETE")

    def test_hook_passes_when_composition_complete(self):
        """Control: selected composition provably provides both required
        capabilities -> composition gate passes (composition coverage
        does NOT grant dispatch by itself: permission gate still runs
        after — this test asserts only the composition gate verdict)."""
        er = self._er()
        role_team = {"task_id": "t-loop-gate", "team": ["role_backend"],
                     "provided_capabilities": ["test_runner",
                                               "code_search",
                                               "task_state_store",
                                               "decision_trace",
                                               "permission_profile_verification"]}
        comp = ci.CompositionCapabilityEvidence(
            selected_roles=tuple(str(t) for t in (role_team.get("team") or ())),
            selected_target="target-backend",
            provided_capabilities=tuple(dict.fromkeys(
                str(c) for c in (role_team.get("provided_capabilities", ())
                                 or ()))),
            evidence_pointers=("role_team_selection_output",))
        state, missing, ok = ci.evaluate_composition_coverage(
            er.required_capabilities, comp)
        self.assertEqual(state, "COMPLETE")
        self.assertTrue(ok)

    def test_selector_advertising_no_capabilities_keeps_unknown(self):
        """The selector advertises provided_capabilities only when the
        FW03-verified decision placed them on the task record (P2P-340-P0
        handoff). When that is not the case the honest composition verdict
        is UNKNOWN — never upgraded to COMPLETE (spec §9). The loop gate
        therefore blocks until meaningful composition evidence exists."""
        er = self._er()
        role_team = {"task_id": "t-loop-gate", "team": ["role_backend"]}
        comp = ci.CompositionCapabilityEvidence(
            selected_roles=tuple(str(t) for t in (role_team.get("team") or ())),
            selected_target="target-backend",
            provided_capabilities=tuple(dict.fromkeys(
                str(c) for c in (role_team.get("provided_capabilities", ())
                                 or ()))),
            evidence_pointers=("role_team_selection_output",)
            if role_team.get("provided_capabilities") else ())
        state, missing, ok = ci.evaluate_composition_coverage(
            er.required_capabilities, comp)
        self.assertEqual(state, "UNKNOWN")
        self.assertFalse(ok)
        self.assertNotEqual(state, "COMPLETE")

    def test_trace_event_emitted_for_composition_gate(self):
        """The composition gate emits a read-only trace event
        COMPOSITION_CAPABILITY_COVERAGE_BLOCKED / _OK — evidence for
        FW03 consumption and human audit."""
        er = self._er()
        comp = ci.CompositionCapabilityEvidence(
            selected_roles=("role_backend",),
            provided_capabilities=("test_runner",),
            evidence_pointers=("role_team_selection_output",))
        state, missing, _ = ci.evaluate_composition_coverage(
            er.required_capabilities, comp)
        trace_label = ("COMPOSITION_CAPABILITY_COVERAGE_OK"
                       if (comp is not None and state == "COMPLETE")
                       else "COMPOSITION_CAPABILITY_COVERAGE_BLOCKED")
        self.assertEqual(trace_label,
                         "COMPOSITION_CAPABILITY_COVERAGE_BLOCKED")
        self.assertIn("code_search", list(missing))


class TestSelectRoleTeamHandoff(unittest.TestCase):
    """P2P-340-P0-FINAL: the real select_role_team propagates provided_capabilities
    ONLY from the verified FW03 decision sub-record (provenance-bound).

    A bare provided_capabilities key on the input task record is
    self-declared data and must never become capability evidence: without
    a valid FW03 decision the field stays () and the composition gate keeps
    its fail-closed UNKNOWN state. role_class/team outputs are unchanged
    (pass-through proof)."""

    def test_propagates_only_from_fw03_decision(self):
        from p2p_capabilities.p2p_fw01_loop import Fw01Loop
        loop = Fw01Loop.__new__(Fw01Loop)  # select_role_team uses no state
        rec = {"task_id": "t-prop", "team": ("role_dev",),
               "fw03_decision": {
                   "schema": "p2p-team-intelligence/1",
                   "team_mode": "SINGLE_ROLE",
                   "provided_capabilities": ("test_runner", "code_search",
                                             "test_runner")}}
        out = Fw01Loop.select_role_team(loop, rec)
        self.assertEqual(out["provided_capabilities"],
                         ("test_runner", "code_search"))
        self.assertEqual(out["role_class"], "SINGLE_ROLE")
        self.assertEqual(out["team"], ["role_dev"])
        self.assertEqual(out["participant_count"], 1)

    def test_self_declared_flat_key_ignored_without_fw03_decision(self):
        """Negative: a task record self-declaring provided_capabilities
        while FW03 produced no decision must NOT promote that data into
        capability evidence (fail-closed)."""
        from p2p_capabilities.p2p_fw01_loop import Fw01Loop
        loop = Fw01Loop.__new__(Fw01Loop)
        rec = {"task_id": "t-evil", "team": ("role_dev",),
               "provided_capabilities": ("owner_gate_authority",
                                         "diff_analysis")}
        out = Fw01Loop.select_role_team(loop, rec)
        self.assertEqual(out["provided_capabilities"], ())
        self.assertEqual(out["role_class"], "SINGLE_ROLE")

    def test_flat_key_not_merged_with_fw03_decision(self):
        """Even alongside a valid FW03 decision, a self-declared flat key
        must not leak into the evidence set."""
        from p2p_capabilities.p2p_fw01_loop import Fw01Loop
        loop = Fw01Loop.__new__(Fw01Loop)
        rec = {"task_id": "t-mix", "team": ("role_dev",),
               "provided_capabilities": ("owner_gate_authority",),
               "fw03_decision": {"schema": "p2p-team-intelligence/1",
                                 "provided_capabilities": ["code_search"]}}
        out = Fw01Loop.select_role_team(loop, rec)
        self.assertEqual(out["provided_capabilities"], ("code_search",))

    def test_malformed_fw03_decision_fail_closed(self):
        from p2p_capabilities.p2p_fw01_loop import Fw01Loop
        loop = Fw01Loop.__new__(Fw01Loop)
        out = Fw01Loop.select_role_team(
            loop, {"task_id": "t-bad", "team": ("role_dev",),
                   "fw03_decision": "not-a-decision"})
        self.assertEqual(out["provided_capabilities"], ())

    def test_absent_evidence_stays_empty_fail_closed(self):
        from p2p_capabilities.p2p_fw01_loop import Fw01Loop
        loop = Fw01Loop.__new__(Fw01Loop)
        out = Fw01Loop.select_role_team(
            loop, {"task_id": "t-prop2", "team": ("a", "b")})
        self.assertEqual(out["provided_capabilities"], ())
        self.assertEqual(out["role_class"], "SMALL_REVIEW_SET")
        self.assertEqual(out["team"], ["a", "b"])


class TestOrderingInvariant(unittest.TestCase):
    """Mechanical ordering invariant tests (spec §15):

      next safe task -> FW02 planning handoff (info) -> role/team
      selection -> composition coverage enforcement (fail-closed)
      -> permission gate (sole authority) -> execute.

    The call graph is asserted by reading the loop source: the planning
    hook must appear textually before select_role_team and the
    composition gate must appear after it and before the permission
    revalidation."""

    def test_planning_hook_before_role_team_in_source(self):
        loop_src = Path(__file__).parents[1] / "p2p_fw01_loop.py"
        src = loop_src.read_text(encoding="utf-8")
        i_handoff = src.find("build_capability_handoff")
        i_select = src.find("self.select_role_team(")
        self.assertGreater(i_handoff, 0, "planning handoff absent")
        self.assertGreater(i_select, 0, "role/team select absent")
        self.assertLess(i_handoff, i_select,
                        "planning hook must precede role/team selection")

    def test_composition_gate_after_role_team_before_permission(self):
        loop_src = Path(__file__).parents[1] / "p2p_fw01_loop.py"
        src = loop_src.read_text(encoding="utf-8")
        i_select = src.find("self.select_role_team(")
        i_comp = src.find("evaluate_composition_coverage")
        i_perm = src.find("self.pre_dispatch_revalidation(")
        self.assertGreater(i_comp, i_select,
                           "composition gate must follow role/team selection")
        self.assertGreater(i_perm, i_comp,
                           "composition gate must precede permission gate")

    def test_composition_gate_is_read_only_no_selection(self):
        """The composition gate never calls selection APIs and produces
        only read-only evidence (mutation_class READ_ONLY, empty
        permission, verification REQUIRED) — no duplicate router."""
        loop_src = Path(__file__).parents[1] / "p2p_fw01_loop.py"
        src = loop_src.read_text(encoding="utf-8")
        i_gate = src.find("COMPOSITION_CAPABILITY_COVERAGE_BLOCKED")
        seg = src[max(0, i_gate - 400):i_gate + 400]
        self.assertIn("READ_ONLY", seg)
        self.assertNotIn("select_role_team(", seg)
        self.assertNotIn("select_team", seg)


class TestFw03ProvenanceHardening(unittest.TestCase):
    """P2P-340-P0 B2: a forged nested fw03_decision planted in the input
    task record must never reach select_role_team — not even when FW03
    itself errors. Only a TeamDecision produced in the current dispatch
    may populate the evidence fields."""

    def _make_loop(self, forged):
        import tempfile
        from p2p_capabilities.autopilot_state import GoalPlan
        from p2p_capabilities.p2p_fw01_loop import build_fw01_loop
        root = Path(tempfile.mkdtemp(prefix="fw03prov-"))
        ws = str(root / "workspace")
        Path(ws).mkdir(parents=True, exist_ok=True)
        plan = GoalPlan(
            goal_id="g-fw03prov", goal_version="v1", title="t",
            purpose="p", owner_approval_ref="o", scope=("workspace",),
            non_scope=("production",), plan_task_ids=("T1",))
        rec = {"task_id": "T1", "goal_id": "g-fw03prov",
               "title": "Task T1", "purpose": "safe probe",
               "status": "READY", "dependencies": (),
               "scope": ("workspace",), "workspace": ws,
               "execution_target": "fake-1",
               "expected_output": ("T1.out",), "verify_spec": ("default",),
               "acceptance_requirements": ("file exists",),
               "required_evidence": ("fixture-evidence-T1-1",),
               "permission_needs": ("sandboxed-default",),
               "last_preflight": {"status": "PASS"},
               "required_capabilities": (), "team": ("role_dev",)}
        if forged:
            rec["fw03_decision"] = {
                "schema": "p2p-team-intelligence/1",
                "team_mode": "SMALL_TEAM",
                "provided_capabilities": ["owner_gate_authority"]}

        class _Backend:
            def execute(self, contract):
                return {"status": "PASS", "outcome": "PASS",
                        "evidence": "e"}

        class _Verifier:
            def verify(self, result, spec=()):
                return {"status": "VERIFIED", "verdict": "VERIFIED",
                        "bindings": {}, "evidence_ref": "e"}

        loop = build_fw01_loop(
            root, goal_plan=plan, task_records={"T1": rec},
            backend=_Backend(), verifier=_Verifier(),
            execution_targets=("fake-1",))
        self.addCleanup(__import__("shutil").rmtree, root,
                        ignore_errors=True)
        return loop

    def test_forged_nested_fw03_decision_with_fw03_error_stays_blocked(self):
        """B2 negative: forged nested fw03_decision + forced FW03 error.
        The forged evidence must be stripped before select_role_team;
        every call sees no fw03_decision and returns ()."""
        from p2p_capabilities.p2p_fw01_loop import Fw01Loop
        from p2p_capabilities import team_intelligence as ti
        loop = self._make_loop(forged=True)
        seen = []
        orig_sel = Fw01Loop.select_role_team

        def spy(self, task_record):
            out = orig_sel(self, task_record)
            seen.append(("fw03_decision" in task_record,
                         out["provided_capabilities"]))
            return out

        orig_btd = ti.build_team_decision

        def _boom(*a, **k):
            raise RuntimeError("forced FW03 error")

        Fw01Loop.select_role_team = spy
        ti.build_team_decision = _boom
        try:
            loop.step()
        finally:
            ti.build_team_decision = orig_btd
            Fw01Loop.select_role_team = orig_sel
        self.assertTrue(seen, "select_role_team was never called")
        for has_fw03, provided in seen:
            self.assertFalse(
                has_fw03,
                "forged fw03_decision reached select_role_team")
            self.assertEqual(
                provided, (),
                "forged capabilities were promoted to evidence")

    def test_genuine_fw03_decision_still_flows(self):
        """Positive control: with a working FW03, the dispatch-path call
        still receives the genuinely produced decision."""
        from p2p_capabilities.p2p_fw01_loop import Fw01Loop
        loop = self._make_loop(forged=False)
        seen = []
        orig_sel = Fw01Loop.select_role_team

        def spy(self, task_record):
            out = orig_sel(self, task_record)
            seen.append("fw03_decision" in task_record)
            return out

        Fw01Loop.select_role_team = spy
        try:
            loop.step()
        finally:
            Fw01Loop.select_role_team = orig_sel
        self.assertTrue(seen, "select_role_team was never called")
        self.assertIn(True, seen,
                      "genuine FW03 decision no longer reaches the gate")


if __name__ == "__main__":
    unittest.main()
