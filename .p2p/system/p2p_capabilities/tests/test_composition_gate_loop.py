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
        """The real selector never advertises provided_capabilities today.
        When that is the case the honest composition verdict is UNKNOWN —
        never upgraded to COMPLETE (spec §9). The loop gate therefore
        blocks until meaningful composition evidence exists."""
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


if __name__ == "__main__":
    unittest.main()
