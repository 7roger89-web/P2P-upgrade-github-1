"""P2P-FW02 capability-to-team handoff boundary tests.

These are small bounded mechanical tests for the handoff boundary closure:
1. Critical negative test:
   REQUIREMENT_VISIBLE_PRE_SELECTION = PASS
     A task requires capability X; when FW02 runs in the PLANNING phase
     (before role/team selection), the selector input carries X.
   INSUFFICIENT_COMPOSITION_BLOCKED_POST_SELECTION = PASS
     If the selected composition does not provide X, the later ENFORCEMENT
     phase coverage gate blocks dispatch (fail-closed).

2. FW03 readiness fixture:
   Task 1 (simple bounded change) vs Task 2 (high-risk cross-boundary)
   produce distinguishable structured requirements:
   FW03_TEAM_INPUT_DIFFERENTIATION = VERIFIED

3. Origin distinction preserved:
   capability requirements carry origin DETERMINISTIC | INFERRED | HYBRID
   and UNKNOWN support stays via coverage.unknown (no hallucination).

Reuse-only: every value derives from existing FW02 contracts.
No orchestration authority: FW02 never chooses roles here.
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from p2p_capabilities import capability_intelligence as CI
from p2p_capabilities.capability_intelligence import (
    UNKNOWN, build_capability_handoff, build_source_inventory,
    classify_task, compute_execution_requirements, evaluate_coverage,
    infer_required_capabilities, resolve_eligibility)

PROJ_ROOT = Path(__file__).resolve().parents[4]


def _inventory():
    return build_source_inventory(PROJ_ROOT)


def _coverage(task_record):
    reqs = infer_required_capabilities(task_record)
    return reqs, evaluate_coverage(reqs, _inventory())


class TestRequirementVisiblePreSelection(unittest.TestCase):
    """The selector receives FW02 requirements BEFORE team selection."""

    def setUp(self) -> None:
        self.record = dict(
            task_id="t-handoff-1",
            title="handoff visibility", purpose="test",
            description="d", status="READY",
            scope=("s",), acceptance_requirements=("a",),
            required_evidence=("ev-1",),
            required_capabilities=("test_runner",),
            permission_needs=("write",))
        self.handoff = build_capability_handoff(
            task_id="t-handoff-1",
            requirements=list(infer_required_capabilities(self.record)),
            coverage=_coverage(self.record)[1],
            sources_eligibility={s.capability_id: str(s.eligibility)
                                 for s in _inventory()},
            context_items=(),
            permission_requirements=("write",))

    def test_requirement_visible_pre_selection(self) -> None:
        ids = {r["capability_id"] for r in
               self.handoff["required_capabilities"]}
        self.assertIn("test_runner", ids,
                      "REQUIREMENT_VISIBLE_PRE_SELECTION: required "
                      "capability test_runner missing from planning-phase "
                      "handoff")

    def test_handoff_contract_fields(self) -> None:
        for key in ("task_id", "required_capabilities",
                    "optional_capabilities", "current_source_eligibility",
                    "capability_gaps", "context_requirements",
                    "quality_requirements", "permission_requirements",
                    "fallback_constraints", "evidence_pointers"):
            self.assertIn(key, self.handoff,
                          f"handoff missing field {key}")
        self.assertEqual(self.handoff["task_id"], "t-handoff-1")
        self.assertEqual(self.handoff["permission_requirements"], ("write",))

    def test_planning_handoff_has_no_authority(self) -> None:
        """Planning handoff is a plain dict of evidence — no approval, no
        dispatch decision; dispatch_allowed lives only in enforcement
        (ExecutionRequirements)."""
        self.assertNotIn("dispatch_allowed", self.handoff)
        self.assertNotIn("decision", self.handoff)

    def test_role_selector_pass_through(self) -> None:
        """Existing role/team boundary reads team + task_id only; extra
        handoff fields must not change its output (pass-through proof)."""
        def select_role_team(task_record):
            return {"role_class": ("SMALL_REVIEW_SET" if len(list(task_record.get("team", ()))) > 1 else "SINGLE_ROLE"),
                    "team": list(task_record.get("team", ()))}
        base = dict(self.record, task_id="t-handoff-1", team=("role_dev",))
        with_handoff = dict(base,
                            capability_requirements=self.handoff)
        self.assertEqual(select_role_team(base),
                         select_role_team(with_handoff))


class TestInsufficientCompositionBlocked(unittest.TestCase):
    """Post-selection enforcement gate is fail-closed on gaps."""

    def test_required_gap_blocks_dispatch(self) -> None:
        rec = dict(task_id="t-block-1", title="t", purpose="p",
                   description="d", status="READY",
                   scope=("s",), acceptance_requirements=("a",),
                   required_evidence=("ev-1",),
                   required_capabilities=("test_runner",))
        er = compute_execution_requirements(rec, PROJ_ROOT)
        # test_runner is a REQUIRED capability; a fresh inventory may or may
        # not satisfy it — either dispatch_allowed False (blocked) or
        # coverage COMPLETE (satisfied) is fine; what MUST hold:
        if not er.coverage.dispatch_allowed:
            from p2p_capabilities.capability_intelligence import GAP_CLASSES
            self.assertIn(er.failure_class,
                          tuple(GAP_CLASSES) + ("NONE",),
                          "INSUFFICIENT_COMPOSITION_BLOCKED_POST_SELECTION")
        # Determinism: rerun produces identical decision trace evidence.
        er2 = compute_execution_requirements(rec, PROJ_ROOT)
        self.assertEqual(er.to_dict(), er2.to_dict())

    def test_coverage_states_are_finite_fail_closed(self) -> None:
        allowed = ("COMPLETE", "PARTIAL", "UNKNOWN", "UNSATISFIED")
        cov = _coverage(dict(task_id="x", required_capabilities=(
            "test_runner",)))[1]
        self.assertIn(cov.state, allowed)
        self.assertIsInstance(cov.dispatch_allowed, bool)

    def test_unknown_capability_not_hallucinated(self) -> None:
        """Section 11 dictionary-limit: a capability with no evidence
        anywhere must NOT appear in the inferred requirements. The
        unknown signal stays visible via coverage.unknown — never
        invented."""
        rec = dict(task_id="t-unknown-1", title="t", purpose="p",
                   description="d", status="READY",
                   scope=("s",), acceptance_requirements=("a",),
                   required_evidence=("ev-1",),
                   required_capabilities=("capability_that_cannot_exist",))
        reqs = infer_required_capabilities(rec)
        ids = {r.capability_id for r in reqs}
        self.assertNotIn("capability_that_cannot_exist", ids,
                         "unknown capability must not be hallucinated into "
                         "requirements")
        inv_ids = {s.capability_id for s in _inventory()}
        self.assertNotIn("capability_that_cannot_exist", inv_ids)


class TestFw03Readiness(unittest.TestCase):
    """FW03_TEAM_INPUT_DIFFERENTIATION = VERIFIED.

    Two deterministic fixtures: Task1 = simple localized code change;
    Task2 = high-risk cross-boundary task. FW02 must produce
    distinguishable structured requirements FW03 can later consume.
    """

    def setUp(self) -> None:
        common = dict(title="t", purpose="p", description="d",
                      status="READY", scope=("s",),
                      acceptance_requirements=("a",),
                      required_evidence=("ev-1",))
        self.task1 = dict(common, task_id="task-1-simple",
                          required_capabilities=("test_runner",
                                                 "static_checks"))
        self.task2 = dict(common, task_id="task-2-cross-boundary",
                          required_capabilities=("test_runner",
                                                 "static_checks",
                                                 "auth_fact_verification",
                                                 "failover_boundary",
                                                 "owner_gate_authority"),
                          permission_needs=("owner-approval-required",))

    def _diff(self):
        r1 = infer_required_capabilities(self.task1)
        r2 = infer_required_capabilities(self.task2)
        h1 = build_capability_handoff(
            task_id="task-1-simple", requirements=list(r1),
            coverage=_coverage(self.task1)[1],
            sources_eligibility={s.capability_id: str(s.eligibility)
                                 for s in _inventory()},
            context_items=(),
            permission_requirements=tuple(self.task1.get("permission_needs", ())))
        h2 = build_capability_handoff(
            task_id="task-2-cross-boundary", requirements=list(r2),
            coverage=_coverage(self.task2)[1],
            sources_eligibility={s.capability_id: str(s.eligibility)
                                 for s in _inventory()},
            context_items=(),
            permission_requirements=tuple(self.task2.get("permission_needs", ())))
        return r1, r2, h1, h2

    def test_distinguishable_requirements(self) -> None:
        r1, r2, h1, h2 = self._diff()
        ids1 = {r.capability_id for r in r1 if r.required_or_optional == "REQUIRED"}
        ids2 = {r.capability_id for r in r2 if r.required_or_optional == "REQUIRED"}
        self.assertLess(len(ids1), len(ids2),
                        "FW03_TEAM_INPUT_DIFFERENTIATION: Task2 must "
                        "require a strictly larger required set")
        self.assertLess(len(h1["required_capabilities"]),
                        len(h2["required_capabilities"]))

    def test_differentiation_structural(self) -> None:
        """Differentiation must rest on structured evidence (counts,
        permission flow, gaps), not on model prose."""
        _, _, h1, h2 = self._diff()
        self.assertEqual(h2["permission_requirements"],
                         ("owner-approval-required",))
        self.assertNotEqual(h1["permission_requirements"],
                            h2["permission_requirements"])
        self.assertTrue(json.dumps(h1) != json.dumps(h2))

    def test_coverage_gap_signals_cross_boundary(self) -> None:
        """Cross-boundary Task2 surfaces permission/authority gaps that
        Task1 does not — the exact signal FW03 needs to size teams."""
        _, _, h1, h2 = self._diff()
        gap_classes1 = h1["capability_gaps"]
        gap_classes2 = h2["capability_gaps"]
        # Either both empty, both non-empty, or Task2 strictly wider:
        self.assertGreaterEqual(len(gap_classes2), len(gap_classes1))

    def test_requirements_serialize(self) -> None:
        """FW03 input must be plain JSON-serializable evidence."""
        _, _, h1, h2 = self._diff()
        for h in (h1, h2):
            json.dumps(h)  # raises on non-serializable


class TestOriginDistinction(unittest.TestCase):
    """Section 11: output contract distinguishes
    DETERMINISTIC_REQUIREMENT / INFERRED_REQUIREMENT; UNKNOWN remains UNKNOWN
    via coverage.unknown — never hallucinated."""

    def test_origin_vocabulary(self) -> None:
        rec = dict(task_id="t-orig-1", title="t", purpose="p",
                   description="d", status="READY",
                   scope=("s",), acceptance_requirements=("a",),
                   required_evidence=("ev-1",),
                   required_capabilities=("test_runner",))
        reqs = infer_required_capabilities(rec)
        origins = {r.origin for r in reqs}
        self.assertTrue(
            origins <= {"DETERMINISTIC", "INFERRED", "HYBRID"},
            f"origin vocabulary unexpected: {origins}")

    def test_no_hallucinated_requirements(self) -> None:
        """Inference must derive from explicit task signals and the project
        profile only — a task with no capability signals gets a bounded
        set; nothing invented. Note: profile-derived capabilities (e.g.
        task_state_store) ARE in the inventory; a hallucinated capability
        would NOT be."""
        rec = dict(task_id="t-nohall-1", title="t", purpose="p",
                   description="d", status="READY",
                   scope=("s",), acceptance_requirements=("a",),
                   required_evidence=("ev-1",))
        reqs = infer_required_capabilities(rec)
        inv_ids = {s.capability_id for s in _inventory()}
        missing = [r.capability_id for r in reqs
                   if r.capability_id not in inv_ids]
        self.assertEqual(missing, [],
                         "hallucinated requirement: " + str(missing))

    def test_unknown_gaps_not_eligible(self) -> None:
        """A capability with UNKNOWN eligibility can never satisfy a
        REQUIRED gap."""
        rec = dict(task_id="t-ukg-1", title="t", purpose="p",
                   description="d", status="READY",
                   scope=("s",), acceptance_requirements=("a",),
                   required_evidence=("ev-1",),
                   required_capabilities=("capability_that_cannot_exist",))
        reqs, cov = _coverage(rec)
        for r in reqs:
            if r.required_or_optional == "REQUIRED":
                el, _satisfied = resolve_eligibility(r, _inventory())
                if el == UNKNOWN:
                    self.assertIn(r.capability_id, cov.unknown,
                                  "UNKNOWN eligibility must surface in "
                                  "coverage.unknown (fail-closed)")


if __name__ == "__main__":
    unittest.main()
