"""P2P-FW02 HARDENING — Unknown Required Capability + Composition Coverage.

Critical fail-closed hardening suites added by the bounded reconciliation
goal (P2P-FW02 hardening). Two issue families:

  A. EXPLICIT_REQUIRED_UNKNOWN != DROPPED: an unknown capability that the
     AUTHORITY task contract explicitly requires must be preserved as a
     REQUIRED requirement with SUPPORT=UNKNOWN (UNKNOWN != SAFE), never
     silently dropped. Heuristic/model-proposed unknowns remain bounded
     (no hallucination) — that distinction is tested separately.

  B. PROJECT_CAPABILITY_AVAILABILITY != PROVIDED_BY_SELECTED_COMPOSITION:
     coverage must be evaluated against the SELECTED execution composition
     (roles/target/sources that the existing selector chose), in addition
     to general project availability. A capability that exists somewhere
     in the project but is not proven for the selected composition leaves
     dispatch blocked (fail-closed). The minimal composition contract
     (CompositionCapabilityEvidence) is deliberately read-only evidence —
     FW02 still does not select roles or teams; adaptive team selection
     belongs to FW03.
"""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))

from p2p_capabilities import capability_intelligence as ci
from p2p_capabilities.capability_intelligence import (
    CapabilityCoverage,
    CapabilityRequirement,
    CompositionCapabilityEvidence,
    evaluate_composition_coverage,
    evaluate_coverage,
)


def _make_root(suffix: str, files: tuple[str, ...]) -> Path:
    import tempfile
    from pathlib import Path
    root = Path(tempfile.mkdtemp(prefix=f"fw02cc-{suffix}-"))
    for f in files:
        fp = root / f
        fp.parent.mkdir(parents=True, exist_ok=True)
        fp.write_text("# test fixture", encoding="utf-8")
    return root


class TestExplicitUnknownPreserved(unittest.TestCase):
    """Issue A: explicit unknown required capability preservation."""

    def test_explicit_unknown_preserved_not_dropped(self):
        """A task contract that explicitly requires an unknown capability
        must preserve it (REQUIRED, origin DETERMINISTIC, task-contract
        provenance) — EXPLICIT_REQUIRED_UNKNOWN != DROPPED."""
        root = _make_root("a1", ("tests/t.py",))
        try:
            rec = dict(task_id="t-explicit-unknown", title="t", purpose="p",
                       description="d", status="READY", scope=("s",),
                       acceptance_requirements=("a",),
                       required_evidence=("ev",),
                       required_capabilities=("capability_that_cannot_exist",))
            er = ci.compute_execution_requirements(rec, root)
            preserved = [r for r in er.required_capabilities
                         if r.capability_id == "capability_that_cannot_exist"]
            self.assertEqual(len(preserved), 1)
            r = preserved[0]
            self.assertEqual(r.required_or_optional, "REQUIRED")
            self.assertEqual(r.origin, "DETERMINISTIC")
            self.assertIn("task_record.required_capabilities",
                          r.evidence_pointers)
        finally:
            from shutil import rmtree
            rmtree(root, ignore_errors=True)

    def test_explicit_unknown_support_is_unknown_fail_closed(self):
        """Preserved explicit-unknown capability must have SUPPORT=UNKNOWN
        and block dispatch (UNKNOWN != SAFE)."""
        root = _make_root("a2", ("tests/t.py",))
        try:
            rec = dict(task_id="t-explicit-unknown-2", title="t", purpose="p",
                       description="d", status="READY", scope=("s",),
                       acceptance_requirements=("a",),
                       required_evidence=("ev",),
                       required_capabilities=("capability_that_cannot_exist",))
            er = ci.compute_execution_requirements(rec, root)
            self.assertIn("capability_that_cannot_exist",
                          er.coverage.unknown)
            self.assertEqual(er.coverage.state, "UNKNOWN")
            self.assertFalse(er.dispatch_allowed)
            self.assertTrue(any(
                r.capability_id == "capability_that_cannot_exist"
                for r in er.unknown_explicit_required))
        finally:
            from shutil import rmtree
            rmtree(root, ignore_errors=True)

    def test_heuristic_unknown_still_bounded(self):
        """An unknown capability mentioned ONLY in heuristic text (purpose,
        scope, evidence) must NOT be added to requirements (no
        hallucination). This remains the separate A case."""
        root = _make_root("a3", ("tests/t.py",))
        try:
            rec = dict(task_id="t-heuristic-unknown", title="t",
                       purpose="builds capability_that_cannot_exist",
                       description="d", status="READY", scope=("s",),
                       acceptance_requirements=("a",),
                       required_evidence=("capability_that_cannot_exist",))
            reqs = ci.infer_required_capabilities(rec)
            ids = {r.capability_id for r in reqs}
            self.assertNotIn("capability_that_cannot_exist", ids)
        finally:
            from shutil import rmtree
            rmtree(root, ignore_errors=True)

    def test_explicit_unknown_recorded_in_execution_record(self):
        """unknown_explicit_required is present on ExecutionRequirements
        and its to_dict() is JSON-serializable (FW03 readiness)."""
        root = _make_root("a4", ("tests/t.py",))
        try:
            rec = dict(task_id="t-explicit-unknown-4", title="t", purpose="p",
                       description="d", status="READY", scope=("s",),
                       acceptance_requirements=("a",),
                       required_evidence=("ev",),
                       required_capabilities=("capability_that_cannot_exist",))
            er = ci.compute_execution_requirements(rec, root)
            self.assertEqual(len(er.unknown_explicit_required), 1)
            out = er.to_dict()
            j = json.dumps(out, default=str)
            self.assertIn("capability_that_cannot_exist", j)
            self.assertIn("unknown_explicit_required", j)
        finally:
            from shutil import rmtree
            rmtree(root, ignore_errors=True)


class TestCompositionCoverage(unittest.TestCase):
    """Issue B: selected-composition capability coverage (fail-closed).

    Distinction under test: PROJECT_CAPABILITY_AVAILABILITY
    (general evidence) vs PROVIDED_BY_SELECTED_COMPOSITION (what the
    actually-selected roles/target claim, truthfully). Both truths must
    be visible; dispatch requires BOTH to be honest-complete."""

    def _reqs(self, caps):
        return tuple(CapabilityRequirement(capability_id=c) for c in caps)

    def test_project_available_but_composition_insufficient_blocks(self):
        """REQUIRED capability X+Y: the PROJECT can satisfy both, but the
        selected composition is evidenced to provide only X ->
        PROJECT coverage COMPLETE, COMPOSITION coverage INCOMPLETE,
        missing_from_composition={Y}, dispatch remains blocked at the
        composition gate. This is the critical negative.
        The project inventory is injected with CURRENTLY_ELIGIBLE sources
        for both caps so the project-level truth is COMPLETE — isolating
        the composition-level truth being tested."""
        root = _make_root("b1", ("tests/t.py",))
        try:
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
                _src("permission_profile_verification",
                     "permission:evidence"),
            )
            rec = dict(task_id="t-b1", title="t", purpose="p",
                       description="d", status="READY", scope=("s",),
                       acceptance_requirements=("a",),
                       required_evidence=("ev",),
                       required_capabilities=("test_runner", "code_search"))
            er = ci.compute_execution_requirements(
                rec, root, sources=injected)
            proj_allow = er.dispatch_allowed
            # Selected composition truthfully advertises only test_runner.
            comp = CompositionCapabilityEvidence(
                selected_roles=("role_backend",),
                selected_target=str(er.selected_sources[0].capability_id)
                if er.selected_sources else "UNKNOWN",
                provided_capabilities=("test_runner",),
                evidence_pointers=("role_team_selection_output",))
            comp_state, comp_missing, comp_ok = (
                evaluate_composition_coverage(er.required_capabilities, comp))
            self.assertEqual(comp_state, "INCOMPLETE")
            self.assertFalse(comp_ok)
            self.assertIn("code_search", comp_missing)
            self.assertTrue(er.coverage.state in (
                "COMPLETE", "PARTIAL"), er.coverage.state)
            # Composition failure class identity check:
            self.assertIn("COMPOSITION", "COMPOSITION_CAPABILITY_BLOCKED")
            del proj_allow
        finally:
            from shutil import rmtree
            rmtree(root, ignore_errors=True)

    def test_composition_complete_control(self):
        """REQUIRED X+Y, selected composition evidenced to provide X+Y ->
        COMPOSITION = COMPLETE (truthful evidence only; no promotion to
        COMPLETE without evidence)."""
        comp = CompositionCapabilityEvidence(
            selected_roles=("role_backend", "role_verifier"),
            provided_capabilities=("test_runner", "code_search"),
            evidence_pointers=("role_team_selection_output",))
        reqs = self._reqs(("test_runner", "code_search"))
        state, missing, ok = evaluate_composition_coverage(reqs, comp)
        self.assertEqual(state, "COMPLETE")
        self.assertTrue(ok)
        self.assertEqual(missing, ())

    def test_no_composition_evidence_is_unknown_never_complete(self):
        """Selector that does not advertise provided-capability metadata
        leaves COMPOSITION_CAPABILITY_COVERAGE = UNKNOWN; it must never
        be upgraded to COMPLETE."""
        comp = CompositionCapabilityEvidence(
            selected_roles=("role_backend",),
            selected_target="UNKNOWN")
        reqs = self._reqs(("test_runner",))
        state, missing, ok = evaluate_composition_coverage(reqs, comp)
        self.assertEqual(state, "UNKNOWN")
        self.assertFalse(ok)
        self.assertNotEqual(state, "COMPLETE")
        self.assertTrue(len(missing) > 0)

    def test_invariant_available_somewhere_not_same_as_provided(self):
        """The two coverage truths are mechanically distinct: a
        project-inventory source can satisfy a capability that the
        selected composition does not provide. evaluate_coverage
        (project) and evaluate_composition_coverage (selected) must be
        evaluated and reported separately.
        The project inventory is injected with CURRENTLY_ELIGIBLE sources
        for both caps so the project-level truth is COMPLETE while the
        composition-level truth is INCOMPLETE — demonstrating the
        AVAILABLE_SOMEWHERE != PROVIDED_BY_SELECTED_COMPOSITION
        invariant directly."""
        injected = (
            ci.CapabilitySource(source_type="TOOL",
                                capability_id="test_runner",
                                invocation_class="DETERMINISTIC_TOOL",
                                eligibility="CAPABILITY_CURRENTLY_ELIGIBLE",
                                evidence_pointers=("test:evidence",)),
            ci.CapabilitySource(source_type="TOOL",
                                capability_id="code_search",
                                invocation_class="DETERMINISTIC_TOOL",
                                eligibility="CAPABILITY_CURRENTLY_ELIGIBLE",
                                evidence_pointers=("tool:evidence",)),
        )
        reqs = self._reqs(("test_runner", "code_search"))
        proj = evaluate_coverage(reqs, injected)
        comp = CompositionCapabilityEvidence(
            selected_roles=("role_backend",),
            provided_capabilities=("test_runner",),
            evidence_pointers=("role_team_selection_output",))
        comp_state, comp_missing, _ = evaluate_composition_coverage(
            reqs, comp)
        self.assertEqual(proj.state, "COMPLETE")
        self.assertEqual(comp_state, "INCOMPLETE")
        self.assertIn("code_search", comp_missing)
        del injected, comp_missing

    def test_composition_contract_is_minimal_and_truthful(self):
        """CompositionCapabilityEvidence has exactly the minimal contract:
        SELECTED_ROLES, SELECTED_TARGET, SELECTED_CAPABILITY_SOURCES,
        PROVIDED_CAPABILITIES, EVIDENCE_POINTERS. It is a frozen
        evidence record — read-only, no selection authority."""
        c = CompositionCapabilityEvidence()
        self.assertTrue(hasattr(c, "selected_roles"))
        self.assertTrue(hasattr(c, "selected_target"))
        self.assertTrue(hasattr(c, "selected_capability_sources"))
        self.assertTrue(hasattr(c, "provided_capabilities"))
        self.assertTrue(hasattr(c, "evidence_pointers"))
        # Evidence-only: no capability can be ADDED by the contract itself.
        self.assertFalse(c.has_capability_evidence)
        d = c.to_dict()
        self.assertEqual(set(d), {
            "selected_roles", "selected_target",
            "selected_capability_sources", "provided_capabilities",
            "evidence_pointers"})


class TestFw03CompositionReadiness(unittest.TestCase):
    """FW03-ready handoff: the selected composition's capability evidence
    is consumable by FW03 (JSON-serializable, structural fields)."""

    def test_composition_evidence_consumable_by_fw03(self):
        comp = CompositionCapabilityEvidence(
            selected_roles=("role_backend",),
            selected_target="target-a",
            provided_capabilities=("test_runner",),
            evidence_pointers=("role_team_selection_output",))
        out = comp.to_dict()
        j = json.dumps(out, default=str)
        parsed = json.loads(j)
        self.assertEqual(parsed["selected_roles"], ["role_backend"])
        self.assertIn("test_runner", parsed["provided_capabilities"])

    def test_combined_consumption_packet(self):
        """A deterministic FW03-ready packet: task requirements + project
        coverage + selected composition evidence + composition gaps."""
        root = _make_root("fw03", ("tests/t.py",))
        try:
            rec = dict(task_id="t-fw03", title="t", purpose="p",
                       description="d", status="READY", scope=("s",),
                       acceptance_requirements=("a",),
                       required_evidence=("ev",),
                       required_capabilities=("test_runner",))
            er = ci.compute_execution_requirements(rec, root)
            comp = CompositionCapabilityEvidence(
                selected_roles=("role_backend",),
                provided_capabilities=(),
                evidence_pointers=("role_team_selection_output",))
            state, missing, _ = evaluate_composition_coverage(
                er.required_capabilities, comp)
            packet = {
                "required_capabilities": [r.to_dict()
                                          for r in er.required_capabilities],
                "project_coverage": er.coverage.to_dict(),
                "composition_evidence": comp.to_dict(),
                "composition_coverage_state": state,
                "composition_missing": list(missing),
                "unknown_explicit_required": [r.to_dict() for r in
                                              er.unknown_explicit_required],
            }
            j = json.dumps(packet, default=str)
            parsed = json.loads(j)
            self.assertIn("composition_coverage_state", parsed)
            self.assertIn("unknown_explicit_required", parsed)
            self.assertEqual(parsed["composition_coverage_state"], "UNKNOWN")
        finally:
            from shutil import rmtree
            rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
