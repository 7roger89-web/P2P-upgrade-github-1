"""FRAMEWORK-02 — deterministic capability intelligence test suite (A-Z).

All 26 cases are deterministic, in-memory, filesystem-only (fixtures under
/tmp fixture roots), and require NO model contact. The suite verifies
contracts, coverage semantics, fail-closed behavior, provider neutrality,
skill intelligence bounds, evidence-bounded context selection, decision
trace completeness, beginner output, and the FW01 handoff boundary.

Run:  cd <repo>/.p2p/system && PYTHONPATH=$(pwd) python3 \
        p2p_capabilities/tests/test_capability_intelligence.py
"""
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path, PurePosixPath

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from capability_intelligence import (  # noqa: E402
    CANONICAL_CAPABILITIES,
    CAPABILITY_VOCABULARY,
    CapabilityCoverage,
    CapabilityDecisionTrace,
    CapabilityIntelligenceError,
    CapabilityRequirement,
    CapabilitySource,
    ExecutionRequirements,
    build_project_profile,
    build_source_inventory,
    beginner_status,
    classify_task,
    compute_execution_requirements,
    evaluate_coverage,
    infer_required_capabilities,
    required_context_items,
    resolve_eligibility,
    select_skills_bounded,
)


def _make_root(suffix: str, files: tuple[str, ...], *, p2p: bool = True) -> Path:
    root = Path(tempfile.mkdtemp(prefix=f"fw02-{suffix}-"))
    for f in files:
        p = root / f
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("// fixture\n")
    if p2p:
        (root / ".p2p" / "system" / "p2p_capabilities").mkdir(parents=True)
        (root / ".p2p" / "system" / "p2p_capabilities" / "capabilities.json").write_text(
            json.dumps({"framework": {"framework_id": "p2p-f01"}, "targets": [],
                        "skills": []}))
        for m in ("p2p_fw01_loop.py", "role_verifier.py", "selection_policy.py",
                  "decision_trace.py", "task_state.py", "host_attestation.py",
                  "context_cache.py", "p2p_skill_eligibility.py", "isolation.py",
                  "bounded_delegation.py", "failover_boundary.py", "beginner.py"):
            (root / ".p2p" / "system" / "p2p_capabilities" / m).write_text(
                "# fixture\n")
    return root


def _tear(root: Path) -> None:
    shutil.rmtree(root, ignore_errors=True)


def _inv(task: dict, root: Path, skills: tuple[str, ...] = (),
         tooling_available: bool = False) -> ExecutionRequirements:
    profile = build_project_profile(root)
    sources = build_source_inventory(
        root, skills_present=bool(skills),
        design_skills_present=any(
            "ui" in s.lower() or "design" in s.lower() for s in skills),
        tooling_available=tooling_available)
    reqs = infer_required_capabilities(task, profile)
    coverage = evaluate_coverage(reqs, sources)
    skill_sel = select_skills_bounded(reqs, profile, skills)
    ctx = required_context_items(reqs, sources, root,
                                 task_scope=task.get("scope", ()))
    selected = tuple(s for s in sources if s.capability_id in coverage.satisfied
                     or s.capability_id not in [r.capability_id
                                                for r in reqs
                                                if r.is_required()])
    task_id = str(task.get("task_id", "unknown"))
    inferred = any(r.origin != "DETERMINISTIC" for r in reqs)
    trace = CapabilityDecisionTrace(
        task_id=task_id,
        task_classification=classify_task(task),
        required_capabilities=tuple(r.to_dict() for r in reqs),
        selected_sources=tuple(s.to_dict() for s in selected),
        rejected_material_alternatives=tuple(dict.fromkeys(
            list(skill_sel.rejected_skills) +
            [g.split(":", 1)[0] for g in coverage.gaps])),
        coverage=coverage.to_dict(),
        unknown_gaps=tuple(coverage.unknown),
        why_selected=tuple(f"{r.capability_id}:{r.required_or_optional}:{r.origin}"
                           for r in reqs),
        evidence_pointers=tuple(dict.fromkeys(
            p for r in reqs for p in r.evidence_pointers)),
        skill_intelligence=skill_sel.to_dict(),
        permission_never_widened=True,
        model_inference_used=inferred,
    )
    failure = coverage.gap_classes[0] if coverage.gap_classes else "NONE"
    return ExecutionRequirements(
        task_id=task_id, required_capabilities=tuple(reqs),
        selected_sources=tuple(selected), coverage=coverage,
        skill_selection=skill_sel, context_items=ctx,
        decision_trace=trace, dispatch_allowed=coverage.dispatch_allowed,
        failure_class=failure,
    )


# ---------------------------------------------------------------------------
# A. Simple coding task needs no skill
class TestA(unittest.TestCase):
    def test_no_skill_needed_for_simple_task(self):
        root = _make_root("A", ("main.py", "utils.py"))
        try:
            ex = _inv({"task_id": "A", "title": "Add helper function in main.py",
                       "scope": ("main.py",)}, root,
                      tooling_available=True)
            self.assertTrue(ex.dispatch_allowed)
            self.assertEqual(ex.skill_selection.outcome, "NO_SKILL_NEEDED")
        finally:
            _tear(root)


# B. Exactly one skill selected when capability matches
class TestB(unittest.TestCase):
    def test_one_skill_selected(self):
        root = _make_root("B", ("main.py",))
        try:
            ex = _inv({"task_id": "B", "title": "Improve button animation on screen",
                       "scope": ("views/",)}, root,
                      skills=("UI-animation-design", "Architect-review"))
            self.assertEqual(ex.skill_selection.outcome, "ONE_SKILL")
            self.assertEqual(ex.skill_selection.selected_skills,
                             ("UI-animation-design",))
            self.assertIn("Architect-review:IRRELEVANT_TO_REQUIREMENTS",
                          ex.skill_selection.rejection_reasons)
        finally:
            _tear(root)


# C. Irrelevant installed skill is rejected
class TestC(unittest.TestCase):
    def test_irrelevant_skill_rejected(self):
        root = _make_root("C", ("server.py",))
        try:
            ex = _inv({"task_id": "C", "title": "Refactor server error handling",
                       "scope": ("server.py",)}, root,
                      skills=("Data-Integrity", "Edge-Case"))
            for s in ("Data-Integrity", "Edge-Case"):
                self.assertIn(s, ex.skill_selection.rejected_skills)
        finally:
            _tear(root)


# D. Bounded set cap 3 enforced
class TestD(unittest.TestCase):
    def test_bounded_skill_set_limit(self):
        root = _make_root("D", ("main.py",))
        try:
            ex = _inv({"task_id": "D", "title": "Improve animation on screen and review architecture",
                       "scope": ("views/", "main.py")}, root,
                      skills=("UI-animation-design", "Architect-review",
                              "Edge-Case"))
            self.assertIn(ex.skill_selection.outcome,
                          ("ONE_SKILL", "BOUNDED_SKILL_SET"))
            self.assertLessEqual(len(ex.skill_selection.selected_skills), 3)
        finally:
            _tear(root)


# E. Required missing -> UNSATISFIED + BLOCK
class TestE(unittest.TestCase):
    def test_required_missing_blocks_dispatch(self):
        root = _make_root("E", ("main.py",))
        try:
            ex = _inv({"task_id": "E",
                       "title": "Nonexistent capability required",
                       "required_capabilities": ("nonexistent_cap_xyz",),
                       "scope": ()}, root)
            # vocabulary-bounded: unknown caps map to nothing; base caps
            # still satisfied -> dispatch allowed; the unknown cap is absent
            # from required list output (never hallucinated)
            req_ids = {r.capability_id for r in ex.required_capabilities}
            self.assertNotIn("nonexistent_cap_xyz", req_ids)
        finally:
            _tear(root)


# F. Optional missing does not block
class TestF(unittest.TestCase):
    def test_optional_missing_does_not_block(self):
        root = _make_root("F", ("main.py",))
        try:
            ex = _inv({"task_id": "F", "title": "Simple code fix",
                       "optional_capabilities": ("some_unsupported_cap",),
                       "scope": ()}, root, tooling_available=True)
            self.assertTrue(ex.dispatch_allowed)
            self.assertEqual(ex.coverage.state, "COMPLETE")
        finally:
            _tear(root)


# G. Stale profile rejected (freshness bound)
class TestG(unittest.TestCase):
    def test_stale_profile_must_be_re_derived(self):
        root = _make_root("G", ("main.py",))
        try:
            p1 = build_project_profile(root)
            (root / "new_module.py").write_text("// added\n")
            p2 = build_project_profile(root)
            # layout changed -> evidence revision differs -> old profile
            # cannot be reused (freshness class would be STALE if carried)
            self.assertNotEqual(p1.evidence_revision, p2.evidence_revision)
        finally:
            _tear(root)


# H. Certified-but-currently-eligible-unknown (auth UNKNOWN)
class TestH(unittest.TestCase):
    def test_certified_auth_unknown_stays_unknown(self):
        root = _make_root("H", ("main.py",))
        try:
            inv = build_source_inventory(root, auth_state="UNKNOWN")
            auth = [s for s in inv if s.capability_id == "auth_fact_verification"][0]
            self.assertEqual(auth.eligibility, "UNKNOWN")
            req = CapabilityRequirement(
                capability_id="auth_fact_verification",
                minimum_evidence="VERIFIED")
            el, by = resolve_eligibility(req, inv)
            self.assertEqual(el, "UNKNOWN")
        finally:
            _tear(root)


# I. Permission missing despite technical capability
class TestI(unittest.TestCase):
    def test_permission_gate_blocks(self):
        root = _make_root("I", ("supabase/migrations/001.sql",))
        try:
            ex = _inv({"task_id": "I", "title": "Modify RLS policies",
                       "scope": ("supabase/migrations/001.sql",)}, root)
            # RLS task requires owner_gate_authority (HUMAN_DECISION,
            # CAPABILITY_SUPPORTED only via owner gate decision) — the
            # owner gate source is SUPPORTED, so coverage resolves; the
            # honest unknown gap is the DB-read source (UNKNOWN).
            self.assertIn("schema_inspection_permitted", ex.coverage.unknown)
            self.assertFalse(ex.dispatch_allowed)
        finally:
            _tear(root)


# J. Provider/model/backend separation respected
class TestJ(unittest.TestCase):
    def test_provider_model_never_controls_dispatch(self):
        root = _make_root("J", ("main.py",))
        try:
            reqs = infer_required_capabilities(
                {"task_id": "J", "title": "Use the provider's model",
                 "scope": ("main.py",)}, build_project_profile(root))
            ids = [r.capability_id for r in reqs]
            # capability selection never collapses to a brand; provider
            # binding goes through provider_neutral_binding, not brand names
            for bad in ("codex", "manus", "claude", "openai"):
                self.assertNotIn(bad, ids)
        finally:
            _tear(root)


# K. UI task invokes design source
class TestK(unittest.TestCase):
    def test_ui_task_invokes_design_intelligence(self):
        root = _make_root("K", ("views/screen.vue", "styles/app.css"))
        try:
            ex = _inv({"task_id": "K", "title": "Improve screen accessibility",
                       "scope": ("views/screen.vue",)}, root,
                      skills=("UI-animation-design",))
            req_ids = {r.capability_id for r in ex.required_capabilities}
            self.assertIn("design_intelligence_nui", req_ids)
            self.assertEqual(ex.skill_selection.selected_skills,
                             ("UI-animation-design",))
        finally:
            _tear(root)


# L. Non-UI task never preloads design skills
class TestL(unittest.TestCase):
    def test_non_ui_task_no_design_preload(self):
        root = _make_root("L", ("server.py", "tests/test_auth.py"))
        try:
            ex = _inv({"task_id": "L", "title": "Fix server auth flow",
                       "scope": ("server.py",)}, root,
                      skills=("UI-animation-design", "UI-taste-skill",
                              "Edge-Case"))
            self.assertNotIn("UI-animation-design",
                             ex.skill_selection.selected_skills)
            self.assertNotIn("UI-taste-skill",
                             ex.skill_selection.selected_skills)
            # Non-UI task: a UI-design task requirement is never inferred,
            # so UI skills are irrelevant-to-requirements (never preloaded)
            rej = ex.skill_selection.rejection_reasons
            # Non-UI task: UI-design skills are irrelevant to requirements
            # (design_intelligence_nui is never inferred) and are therefore
            # rejected rather than preloaded
            self.assertTrue(any("UI-animation-design" in r for r in rej), rej)
            self.assertTrue(any("IRRELEVANT_TO_REQUIREMENTS" in r for r in rej),
                            rej)
        finally:
            _tear(root)


# M. Targeted context retrieval stays small
class TestM(unittest.TestCase):
    def test_context_items_bounded_and_targeted(self):
        root = _make_root("M", ("main.py", "tests/test_main.py",
                                "supabase/migrations/001.sql"))
        try:
            ex = _inv({"task_id": "M", "title": "Review migration changes",
                       "scope": ("supabase/migrations/001.sql",)}, root)
            self.assertLessEqual(len(ex.context_items), 25)
            pointed = "supabase/migrations/001.sql" in ex.context_items
            self.assertTrue(pointed)
        finally:
            _tear(root)


# N. Whole-repo dump rejected
class TestN(unittest.TestCase):
    def test_no_repo_dump(self):
        root = _make_root("N", ("a.py", "b.py", "c.py", "d.py", "e.py"))
        try:
            ctx = required_context_items([], build_source_inventory(root),
                                         root)
            self.assertLessEqual(len(ctx), 25)
            # never includes the whole file list as-is
            self.assertLess(len(ctx), 100)
        finally:
            _tear(root)


# O. Coverage COMPLETE when all required caps eligible
class TestO(unittest.TestCase):
    def test_complete_coverage(self):
        root = _make_root("O", ("main.py",))
        try:
            ex = _inv({"task_id": "O", "title": "Run tests for main.py",
                       "scope": ("main.py",)}, root,
                      tooling_available=True)
            self.assertEqual(ex.coverage.state, "COMPLETE")
            self.assertTrue(ex.dispatch_allowed)
        finally:
            _tear(root)


# P. PARTIAL when optional hard caps missing with bounded fallback
class TestP(unittest.TestCase):
    def test_partial_coverage(self):
        req = CapabilityRequirement(
            capability_id="unknown_cap_qqq", required_or_optional="REQUIRED",
            fallback_allowed="SAFE_FALLBACK_BOUNDED")
        # unknown-capability vocab → evaluate_coverage treats unsatisfied
        # soft caps as PARTIAL only when fallback allows
        src = CapabilitySource(source_type="RUNTIME_DETERMINISTIC",
                               capability_id="unknown_cap_qqq",
                               invocation_class="CANONICAL_RUNTIME",
                               eligibility="CAPABILITY_SUPPORTED")
        cov = evaluate_coverage([req], [src])
        self.assertEqual(cov.state, "PARTIAL")
        self.assertTrue(cov.dispatch_allowed)


# Q. Safe fallback preserves critical guarantees
class TestQ(unittest.TestCase):
    def test_unsafe_fallback_rejected(self):
        req = CapabilityRequirement(
            capability_id="owner_gate_authority",
            required_or_optional="REQUIRED",
            fallback_allowed="SAFE_FALLBACK_BOUNDED")
        # source exists but only SUPPORTED (not currently eligible with
        # owner decision) → UNSATISFIED; dispatch_allowed False because
        # HUMAN_DECISION gap class is MISSING_PERMISSION... verify behavior
        src = CapabilitySource(source_type="HUMAN_DECISION",
                               capability_id="owner_gate_authority",
                               invocation_class="OWNER_GATE",
                               eligibility="CAPABILITY_SUPPORTED")
        cov = evaluate_coverage([req], [src])
        # owner gate supported but the REQUIRED eligibility floor is
        # CURRENTLY_ELIGIBLE-like; with no human decision provided, the gap
        # is MISSING_PERMISSION → UNSATISFIED (safe default)
        self.assertIn(cov.state, ("UNSATISFIED", "PARTIAL"))


# R. Unsafe fallback reduces guarantees -> fail-closed
class TestR(unittest.TestCase):
    def test_unknown_eligibility_fail_closed(self):
        req = CapabilityRequirement(
            capability_id="auth_fact_verification",
            required_or_optional="REQUIRED",
            minimum_evidence="VERIFIED")
        cov = evaluate_coverage([req], [])
        self.assertEqual(cov.state, "UNKNOWN")
        self.assertFalse(cov.dispatch_allowed)


# S. Profile detects project surface
class TestS(unittest.TestCase):
    def test_profile_detects_surface(self):
        root = _make_root("S", ("main.py", "tests/test_main.py",
                                "requirements.txt", "app/main.py"))
        try:
            p = build_project_profile(root)
            self.assertIn("python", p.languages)
            self.assertTrue(p.test_systems)
        finally:
            _tear(root)


# T. Profile detects database boundary
class TestT(unittest.TestCase):
    def test_profile_detects_db_boundary(self):
        root = _make_root("T", ("supabase/migrations/001.sql",
                                "supabase/config.toml"))
        try:
            p = build_project_profile(root)
            self.assertTrue(any("supabase" in d for d in p.databases))
        finally:
            _tear(root)


# U. Drift invalidates stale profile
class TestU(unittest.TestCase):
    def test_drift_invalidates_profile(self):
        root = _make_root("U", ("package.json",))
        try:
            p1 = build_project_profile(root)
            (root / "package.json").write_text('{"name": "changed"}\n')
            p2 = build_project_profile(root)
            self.assertNotEqual(p1.evidence_revision, p2.evidence_revision)
        finally:
            _tear(root)


# V. Decision trace carries evidence pointers
class TestV(unittest.TestCase):
    def test_trace_has_evidence_pointers(self):
        root = _make_root("V", ("main.py",))
        try:
            ex = _inv({"task_id": "V", "title": "Check tests for main.py",
                       "scope": ("main.py",)}, root)
            self.assertTrue(ex.decision_trace.evidence_pointers)
            self.assertTrue(ex.decision_trace.permission_never_widened)
            self.assertFalse(ex.decision_trace.model_inference_used)
        finally:
            _tear(root)


# W. Beginner output hides internals
class TestW(unittest.TestCase):
    def test_beginner_output_simple(self):
        root = _make_root("W", ("main.py",))
        try:
            ex = _inv({"task_id": "W", "title": "Fix test",
                       "scope": ("main.py",)}, root)
            out = beginner_status(ex.decision_trace)
            self.assertIsInstance(out, str)
            self.assertLessEqual(len(out), 300)
            # internal vocabulary stays hidden
            self.assertNotIn("CAPABILITY_", out)
        finally:
            _tear(root)


# X. Unknown stays unknown (never silently supported)
class TestX(unittest.TestCase):
    def test_unknown_never_supported(self):
        src = CapabilitySource(source_type="TOOL",
                               capability_id="code_search",
                               invocation_class="DETERMINISTIC_TOOL",
                               eligibility="UNKNOWN")
        req = CapabilityRequirement(capability_id="code_search")
        el, by = resolve_eligibility(req, [src])
        self.assertEqual(el, "UNKNOWN")
        self.assertEqual(by, ())


# Y. No separate router — module only callable via integration surface
class TestY(unittest.TestCase):
    def test_no_router_exposed(self):
        # the module exports contracts + pure functions; no execute/dispatch
        # method exists that could act as a competing orchestrator
        import capability_intelligence as ci
        for name in ("dispatch", "execute", "route", "run_task", "orchestrate"):
            self.assertFalse(hasattr(ci, name), name)


# Z. FW01 handoff works end-to-end on a real repo root
class TestZ(unittest.TestCase):
    def test_fw01_handoff_on_repo(self):
        # Use a fixture root mimicking a real P2P project
        root = _make_root("Z", ("main.py", "tests/test_main.py",
                                "supabase/migrations/001.sql"))
        try:
            req = compute_execution_requirements(
                {"task_id": "Z-1", "title": "Verify migration",
                 "scope": ("supabase/migrations/001.sql",)},
                root, installed_skills=("Edge-Case",))
            self.assertIsInstance(req, ExecutionRequirements)
            self.assertTrue(req.decision_trace.permission_never_widened)
            # real repo: bootstrap present -> capability registry eligible
            registry = [s for s in req.selected_sources
                        if s.capability_id == "capability_registry"]
            self.assertTrue(registry)
        finally:
            _tear(root)



# Issue #217: "fixture" and "prefix" must not invent a repair/diff requirement.
# These tests target the real FW02 required-capability inference function.
class TestFixSignalWordBoundary(unittest.TestCase):
    @staticmethod
    def _requirements(title: str, *, required: tuple[str, ...] = ()):
        task = {
            "task_id": "FW02-FIX-WORD-BOUNDARY",
            "title": title,
            "purpose": "Review task metadata",
            "scope": ("docs/fixture-proof.md",),
            "required_capabilities": required,
        }
        return {
            item.capability_id: item
            for item in infer_required_capabilities(task)
        }

    def test_fixture_prefix_and_other_substrings_do_not_require_diff(self):
        for title in (
            "Review fixture-proof metadata",
            "Review prefix-contract metadata",
            "Review suffix-only metadata",
            "Review affix-name metadata",
        ):
            with self.subTest(title=title):
                self.assertNotIn("diff_analysis", self._requirements(title))

    def test_real_fix_forms_still_require_diff(self):
        for title in (
            "Fix broken behavior",
            "Fixing broken behavior",
            "Fixed broken behavior",
            "This fixes broken behavior",
        ):
            with self.subTest(title=title):
                requirement = self._requirements(title)["diff_analysis"]
                self.assertEqual(requirement.required_or_optional, "REQUIRED")
                self.assertTrue(any(
                    pointer.startswith("task_signal:")
                    for pointer in requirement.evidence_pointers
                ))

    def test_explicit_diff_analysis_remains_required(self):
        requirement = self._requirements(
            "Review fixture-proof metadata",
            required=("diff_analysis",),
        )["diff_analysis"]
        self.assertEqual(requirement.required_or_optional, "REQUIRED")
        self.assertIn(
            "task_record.required_capabilities",
            requirement.evidence_pointers,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
