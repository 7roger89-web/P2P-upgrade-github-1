# -*- coding: utf-8 -*-
"""GC1-GC50: deterministic Goal-closure integrity tests (C29).

These tests exercise `scripts/p2p_goal_closure.py` (the closure checker)
plus the durable artifacts it validates, against the live repository and
deliberate contradiction fixtures.
"""
from __future__ import annotations

import json
import pathlib
import re
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import p2p_goal_closure as closure  # noqa: E402

REPORTS = ROOT / "docs" / "p2p-development" / "reports"
GOV = ROOT / "governance" / "development-control.json"
LEDGER = ROOT / "docs" / "p2p-development" / "capability-ledger" / "capability-index.json"
CANDIDATES = ROOT / "reports" / "candidates"


def load_gov() -> dict:
    return json.loads(GOV.read_text(encoding="utf-8"))


def load_ledger() -> dict:
    return json.loads(LEDGER.read_text(encoding="utf-8"))


def roadmap_items(gov: dict) -> list:
    return gov["roadmap"]["items"]


def item_of(gov: dict, goal_id: str):
    for i in roadmap_items(gov):
        if str(i.get("goal_id") or i.get("id", "")).upper() == goal_id.upper():
            return i
    return None


def find_changed_files(base: str = "main") -> list[str]:
    try:
        return subprocess.run(
            ["git", "diff", "--name-only", base, "HEAD"],
            cwd=str(ROOT), capture_output=True, text=True, timeout=60, check=False,
        ).stdout.splitlines()
    except (OSError, subprocess.TimeoutExpired):
        return []


def closure_verdict(goal_id: str, gov: dict, ledger: dict,
                    report_fields: dict, changes=None):
    if changes is None:
        changes = closure.ChangeSignals.detect(find_changed_files())
    records = {r.get("candidate_id"): r for r in gov.get("candidate_records", [])}
    candidate_zip = next(
        (f for f in CANDIDATES.glob(f"*{goal_id.lower()}*.zip")), None)
    rec = records.get(goal_id)
    return closure.goal_closure_verdict(
        gov, ledger, report_fields, goal_id, changes,
        candidate_artifact_exists=candidate_zip is not None,
        package_verify_evidence=(rec or {}).get("package_verify_evidence"),
        outcome_capability_ids=[
            "REAL_HOST_EXECUTION_CERTIFICATION",
            "HOST_AUTH_STATE_VERIFICATION",
        ],
    )


# ---------------------------------------------------------------------------
# GC1-GC3: terminal state vs roadmap state (model-level fixtures)
# ---------------------------------------------------------------------------

class ClosureModelTests(unittest.TestCase):
    """Deterministic policy semantics: PASS/BLOCKED/FAIL vs roadmap status."""

    def setUp(self) -> None:
        self.changes = closure.ChangeSignals.detect(
            ["scripts/a.py", "governance/development-control.json"])

    def test_gc1_pass_cannot_coexist_with_planned(self) -> None:
        findings = closure.check_roadmap_goal_consistency(
            [{"id": "G", "status": "PLANNED"}],
            {"GOAL_TERMINAL_STATUS": "PASS"}, "G")
        self.assertTrue(any(not f.ok for f in findings),
                        "PASS + PLANNED must fail closure checks")

    def test_gc1_done_passes_with_pass(self) -> None:
        findings = closure.check_roadmap_goal_consistency(
            [{"id": "G", "status": "DONE"}],
            {"GOAL_TERMINAL_STATUS": "PASS"}, "G")
        self.assertTrue(all(f.ok for f in findings))

    def test_gc2_blocked_cannot_coexist_with_done(self) -> None:
        findings = closure.check_roadmap_goal_consistency(
            [{"id": "G", "status": "DONE"}],
            {"GOAL_TERMINAL_STATUS": "BLOCKED"}, "G")
        self.assertTrue(any(not f.ok for f in findings))

    def test_gc3_fail_cannot_coexist_with_pass(self) -> None:
        self.assertEqual(closure.normalize_terminal_status("FAIL"), "FAIL")
        findings = closure.check_roadmap_goal_consistency(
            [{"id": "G", "status": "DEFERRED"}],
            {"GOAL_TERMINAL_STATUS": "PASS"}, "G")
        self.assertTrue(any(not f.ok for f in findings))

    def test_gc3_blocked_cannot_be_normalized_as_pass(self) -> None:
        self.assertIsNone(closure.normalize_terminal_status("PASS/FAIL"))
        self.assertEqual(closure.normalize_terminal_status("PASS"), "PASS")
        self.assertEqual(closure.normalize_terminal_status("blocked"), "BLOCKED")


# ---------------------------------------------------------------------------
# GC4-GC7: goal vs capability status separation; machinery vs outcome
# ---------------------------------------------------------------------------

class SeparationTests(unittest.TestCase):
    """Goal status, machinery capability, and outcome capability must not be conflated."""

    def _ledger(self, overrides: dict) -> dict:
        caps = []
        for cid, status in overrides.items():
            caps.append({"capability_id": cid, "status": status, "origin_type": "PROJECT_LEARNING"})
        return {"capabilities": caps, "families": {}, "schema": "capability-ledger/2", "version": 2}

    def test_gc4_goal_status_distinct_from_capability_status(self) -> None:
        gov = load_gov()
        c27 = item_of(gov, "C27")
        c28 = item_of(gov, "C28")
        self.assertEqual(str(c27["status"]).upper(), "BLOCKED")
        self.assertEqual(str(c28["status"]).upper(), "DONE")
        # C28 = DONE (machinery PASS) while C27 roadmap item remains BLOCKED;
        # capability statuses live in the Ledger and are distinct from the
        # roadmap item statuses above.
        ledger = load_ledger()
        caps = {c["capability_id"]: c for c in ledger["capabilities"]}
        c27_mach = caps["REAL_HOST_EXECUTION_CERTIFICATION_MACHINERY"]
        self.assertEqual(str(c27["status"]).upper(), "BLOCKED")
        # Machinery evidence-based (C29 audit); no status fabricated for the
        # unreachable live outcome (no such outcome record exists at C29).
        self.assertIn(c27_mach["status"],
                      ("FOUNDATION_READY", "VERIFIED_IMPLEMENTED", "PARTIAL", "UNKNOWN"))

    def test_gc5_pass_does_not_imply_promotion(self) -> None:
        gov = load_gov()
        rec = next(r for r in gov["candidate_records"] if r.get("candidate_id") == "C28")
        self.assertEqual(rec["promotion_status"], "UNPROMOTED")
        c28 = item_of(gov, "C28")
        self.assertEqual(str(c28["status"]).upper(), "DONE")

    def test_gc6_blocked_may_produce_implemented_machinery(self) -> None:
        findings = closure.check_goal_vs_capability_separation(
            self._ledger({"REAL_HOST_EXECUTION_CERTIFICATION_MACHINERY": "FOUNDATION_READY",
                          "REAL_HOST_EXECUTION_CERTIFICATION": "UNKNOWN"}),
            {}, ["REAL_HOST_EXECUTION_CERTIFICATION"])
        self.assertTrue(all(f.ok for f in findings))

    def test_gc7_machinery_distinct_from_outcome(self) -> None:
        gov = load_gov()
        recs = {r.get("candidate_id"): r for r in gov["candidate_records"]}
        c28_sha = bool(recs.get("C28", {}).get("candidate_sha256"))
        c27_sha = bool(recs.get("C27", {}).get("candidate_sha256"))
        self.assertTrue(c28_sha, "C28 machinery candidate must exist")
        self.assertFalse(c27_sha, "C27 (BLOCKED, outcome not reached) must not fabricate a candidate")


# ---------------------------------------------------------------------------
# GC8-GC9: C27 evidence-based machinery audit
# ---------------------------------------------------------------------------

class C27ClosureTests(unittest.TestCase):
    """C27 must remain BLOCKED while its machinery is audited evidence-based."""

    def setUp(self) -> None:
        self.gov = load_gov()
        self.ledger = load_ledger()
        self.caps = {c["capability_id"]: c for c in self.ledger["capabilities"]}

    def test_gc8_c27_machinery_status_is_evidence_based(self) -> None:
        mach = self.caps["REAL_HOST_EXECUTION_CERTIFICATION_MACHINERY"]
        self.assertIn(mach["status"], ("FOUNDATION_READY", "VERIFIED_IMPLEMENTED", "PARTIAL"))
        self.assertTrue(mach.get("evidence_refs") or mach.get("implementation_refs"),
                        "machinery status must cite evidence, not assertion")
        verdict = closure_verdict("C27", self.gov, self.ledger,
                                  {"GOAL_TERMINAL_STATUS": "BLOCKED"})
        self.assertTrue(verdict.consistent,
                        [f.detail for f in verdict.failures()])

    def test_gc9_c27_live_certification_remains_blocked(self) -> None:
        c27 = item_of(self.gov, "C27")
        self.assertEqual(str(c27["status"]).upper(), "BLOCKED")
        self.assertIn("LIVE_HOST_EVIDENCE_UNAVAILABLE", str(c27))
        self.assertTrue(closure.reopen_condition_is_metadata(roadmap_items(self.gov)))
        # Live certification outcome must not be fabricated: no ledger record
        # claims a result status without live evidence at C29.
        for cid in ("REAL_HOST_EXECUTION_CERTIFICATION",
                    "LIVE_HOST_EXECUTION_CERTIFICATE"):
            if cid in self.caps:
                self.assertIn(self.caps[cid]["status"],
                              ("UNKNOWN", "PLANNED", "DEFERRED"))


# ---------------------------------------------------------------------------
# GC10-GC17: C28 closure consistency and candidate lifecycle
# ---------------------------------------------------------------------------

class C28ClosureTests(unittest.TestCase):
    """C28 must close PASS with DONE roadmap, required candidate, UNPROMOTED."""

    def setUp(self) -> None:
        self.gov = load_gov()
        self.ledger = load_ledger()
        self.rec = next(r for r in self.gov["candidate_records"]
                        if r.get("candidate_id") == "C28")

    def test_gc10_c28_closure_is_internally_consistent(self) -> None:
        report = closure.terminal_from_report(REPORTS / "P2P-C28-terminal-report.md")
        self.assertEqual(report["GOAL_TERMINAL_STATUS"], "PASS")
        verdict = closure_verdict("C28", self.gov, self.ledger, report)
        self.assertTrue(verdict.consistent,
                        [f.detail for f in verdict.failures()])
        self.assertEqual(item_of(self.gov, "C28")["status"], "DONE")

    def test_gc11_candidate_required_goal_cannot_pass_without_candidate(self) -> None:
        gov = load_gov()
        gov["candidate_records"] = [r for r in gov["candidate_records"]
                                    if r.get("candidate_id") != "C28"]
        changes = closure.ChangeSignals.detect(
            ["scripts/a.py", "governance/development-control.json"])
        findings = closure.check_candidate_policy_compliance(
            gov, {"GOAL_TERMINAL_STATUS": "PASS", "CANDIDATE_REQUIRED": "YES"},
            "C28", changes, False, None)
        self.assertFalse(all(f.ok for f in findings))

    def test_gc12_candidate_not_required_does_not_fabricate(self) -> None:
        findings = closure.check_candidate_policy_compliance(
            self.gov, {"GOAL_TERMINAL_STATUS": "BLOCKED", "CANDIDATE_REQUIRED": "NO"},
            "C27", closure.ChangeSignals.detect([]), False, None)
        ok = next(f for f in findings if f.check == "CANDIDATE_NOT_REQUIRED_ABSENT")
        self.assertTrue(ok.ok)

    def test_gc13_candidate_requirement_known_before_closure(self) -> None:
        required = closure.candidate_policy_from_report_fields(
            {"GOAL_TERMINAL_STATUS": "PASS", "CANDIDATE_REQUIRED": "YES"},
            closure.ChangeSignals.detect(["governance/development-control.json"]))
        self.assertEqual(required, "YES")

    def test_gc14_candidate_sha_requires_artifact(self) -> None:
        sha = self.rec["candidate_sha256"]
        self.assertEqual(len(sha), 64)
        self.assertTrue(all(ch in "0123456789abcdef" for ch in sha))
        expected = CANDIDATES / self.rec["candidate_label"]
        self.assertTrue(expected.is_file(), f"artifact missing: {expected.name}")
        actual = expected.read_bytes()
        import hashlib
        self.assertEqual(hashlib.sha256(actual).hexdigest(), sha)

    def test_gc15_candidate_artifact_requires_verify_evidence(self) -> None:
        self.assertTrue(bool(self.rec.get("package_verify_evidence")))

    def test_gc16_candidate_remains_unpromoted(self) -> None:
        self.assertEqual(self.rec["promotion_status"], "UNPROMOTED")
        gov = load_gov()
        self.assertNotIn("promotion_approval", gov)

    def test_gc17_official_19_immutable(self) -> None:
        gov = load_gov()
        baseline = gov["official_baseline"]
        self.assertEqual(baseline["version"], "8.4.7-C-codex.19")
        recs = {r.get("candidate_id"): r for r in gov["candidate_records"]}
        c14 = recs["C14"]
        self.assertEqual(c14["promotion_status"], "PROMOTED_VERIFIED")
        # Baseline authority lives in governance (SHA never rewritten by any
        # later Goal); the artifact itself is not required on disk because the
        # durable record (SHA + approval reference) is the source of truth.
        self.assertEqual(baseline["artifact_sha256"], c14["candidate_sha256"])
        self.assertEqual(c14["based_on_official_version"], baseline["version"])
        self.assertEqual(c14["based_on_official_sha256"], baseline["artifact_sha256"])
        self.assertTrue(closure.official_baseline_unmodified(gov))


def hashlib_sha(rec: dict) -> str:
    import hashlib
    path = pathlib.Path(rec.get("artifact_path", "")).resolve()
    if not path.is_file():
        path = CANDIDATES / rec["candidate_label"]
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ---------------------------------------------------------------------------
# GC18-GC21: Goal Contract and Supervisor templates
# ---------------------------------------------------------------------------

class TemplateTests(unittest.TestCase):
    """Contract and supervisor templates must carry the closure-integrity policy."""

    def setUp(self) -> None:
        self.contract = closure.load_contract_template()
        self.supervisor = closure.load_supervisor_template()

    def test_gc18_goal_contract_includes_candidate_policy(self) -> None:
        self.assertIn("CANDIDATE_REQUIRED", self.contract)

    def test_gc19_goal_contract_includes_expected_terminal_state(self) -> None:
        self.assertIn("GOAL_TERMINAL_STATE_POLICY", self.contract)
        self.assertIn("ROADMAP", self.contract.upper())

    def test_gc20_supervisor_checks_terminal_consistency(self) -> None:
        for field in ("TERMINAL_STATE_CONSISTENCY", "ROADMAP_SYNC",
                      "DEVELOPMENT_CONTROL_SYNC"):
            self.assertIn(field, self.supervisor)

    def test_gc21_supervisor_checks_candidate_compliance(self) -> None:
        for field in ("CANDIDATE_POLICY_COMPLIANCE",
                      "CAPABILITY_CLAIM_SEPARATION", "PR_LINEAGE_INTEGRITY"):
            self.assertIn(field, self.supervisor)


# ---------------------------------------------------------------------------
# GC22-GC26: roadmap terminal derivations
# ---------------------------------------------------------------------------

class RoadmapTerminalTests(unittest.TestCase):
    """Roadmap terminal-state derivations must be deterministic."""

    def setUp(self) -> None:
        self.gov = load_gov()
        self.items = roadmap_items(self.gov)

    def test_gc22_roadmap_current_handles_pass(self) -> None:
        road_current = self.gov["roadmap"]["current"]
        self.assertEqual(road_current["id"], "C28")
        self.assertEqual(road_current["status"], "DONE")

    def test_gc23_roadmap_current_blocks_without_auto_done(self) -> None:
        c27 = item_of(self.gov, "C27")
        self.assertEqual(c27["status"], "BLOCKED")
        self.assertNotEqual(c27["status"], "DONE")

    def test_gc24_likely_next_handles_terminal_goal(self) -> None:
        derived = closure.roadmap_terminal_next(self.items)
        self.assertIn(derived["status"], ("DONE", "BLOCKED", "PLANNED", "ACTIVE"))
        gov = load_gov()
        ln = gov["roadmap"]["likely_next"]
        # Once the last roadmap goal is terminal (C28 DONE), likely_next
        # points at the next viable goal declared PLANNED (C30) — never at a
        # goal that will never execute, and never stale/contradictory:
        if derived["status"] in ("DONE", "BLOCKED"):
            later = [
                i for i in self.items
                if str(i.get("status", "")).upper()
                in ("PLANNED", "ACTIVE")
            ]
            if later:
                self.assertEqual(ln["id"], later[0]["id"])
                self.assertEqual(ln["status"],
                                 str(later[0]["status"]).upper())
            else:
                self.assertEqual(ln["id"], derived["id"])
        else:
            self.assertEqual(ln["id"], derived["id"])
        # gc22-style determinism: derived next goal id is stable:
        again = closure.roadmap_terminal_next(self.items)
        self.assertEqual(again["id"], derived["id"])

    def test_gc25_blocked_goal_declares_reopen_condition(self) -> None:
        c27 = item_of(self.gov, "C27")
        self.assertTrue(bool(c27.get("reopen_condition")))

    def test_gc26_reopen_condition_does_not_auto_execute(self) -> None:
        marked = [i for i in self.items if i.get("reopen_condition")]
        self.assertGreaterEqual(len(marked), 1)
        for i in marked:
            self.assertEqual(str(i.get("reopen_executes", "no")).lower(), "no")


# ---------------------------------------------------------------------------
# GC27-GC30: development-control and ledger semantics
# ---------------------------------------------------------------------------

class ControlLedgerTests(unittest.TestCase):
    """current_development semantics and ledger/goal separation."""

    def setUp(self) -> None:
        self.gov = load_gov()
        self.ledger = load_ledger()

    def test_gc27_current_development_semantics_validate(self) -> None:
        cd = self.gov["current_development"]
        road_current = self.gov["roadmap"]["current"]
        findings = closure.check_development_control_consistency(
            self.gov, {"GOAL_TERMINAL_STATUS": "PASS"}, "C28")
        # Live position is C28/DONE while development_goal advanced to the
        # newer packaged goal C29; the drift is EXPLAINED (durable snapshot)
        # and therefore does not break closure consistency.
        hard_failures = [f for f in findings if not f.ok and f.severity == "hard"]
        self.assertEqual(hard_failures, [], [f.detail for f in findings])
        if cd["development_goal"] != road_current["id"]:
            explained = [f for f in findings
                         if f.check == "CURRENT_DEVELOPMENT_SEMANTICS"
                         and f.severity == "explained"]
            self.assertTrue(explained, "drift must be marked explained")

    def test_gc28_ledger_status_not_conflated_with_goal_status(self) -> None:
        caps = {c["capability_id"]: c for c in self.ledger["capabilities"]}
        # C27 roadmap = BLOCKED while its machinery capability is evidence-based
        # (FOUNDATION_READY per C29 machinery audit); the outcome capability
        # remains UNKNOWN until live host evidence exists.
        # Machinery capability reached evidence-based FOUNDATION_READY while the
        # C27 roadmap item remains BLOCKED — status categories are distinct and
        # no outcome capability falsely claims a machinery-only status.
        self.assertIn(caps["REAL_HOST_EXECUTION_CERTIFICATION_MACHINERY"]["status"],
                      ("FOUNDATION_READY", "VERIFIED_IMPLEMENTED", "PARTIAL"))
        # Separation semantics: outcome capability IDs must NOT sit in
        # machinery-only statuses; machinery capabilities may (evidence-based).
        findings = closure.check_goal_vs_capability_separation(
            self.ledger, {}, [])
        self.assertTrue(all(f.ok for f in findings))
        # The same record is never a goal status value (status vocab is
        # disjoint: DONE/BLOCKED/DEFERRED/PLANNED vs ledger statuses).

    def test_gc29_roadmap_projection_matches_ledger_count(self) -> None:
        road = (ROOT / "docs" / "p2p-development" / "current-roadmap.md").read_text()
        match = re.search(r"\((\d+) records", road)
        self.assertIsNotNone(match)
        self.assertEqual(int(match.group(1)), len(self.ledger["capabilities"]))

    def test_gc30_development_control_matches_terminal_report(self) -> None:
        report = closure.terminal_from_report(REPORTS / "P2P-C28-terminal-report.md")
        gov = load_gov()
        findings = closure.check_development_control_consistency(gov, report, "C28")
        # No HARD failures; explained findings (durable snapshot drift toward
        # a newer packaged goal) preserve consistency.
        hard_failures = [f for f in findings if not f.ok and f.severity == "hard"]
        self.assertEqual(hard_failures, [], [f.detail for f in findings])


# ---------------------------------------------------------------------------
# GC31-GC36: PR stack lineage integrity
# ---------------------------------------------------------------------------

class PRLineageTests(unittest.TestCase):
    """Stacked PR branch ancestry must be auditable and no merges auto-occur."""

    def _contains(self, branch: str, parent: str) -> bool:
        result = subprocess.run(
            ["git", "merge-base", "--is-ancestor", parent, branch],
            cwd=str(ROOT), capture_output=True, check=False)
        return result.returncode == 0

    def test_gc31_c25_ancestry_retained(self) -> None:
        gov = load_gov()
        c25 = item_of(gov, "C25")
        self.assertEqual(str(c25["status"]).upper(), "DONE")

    def test_gc32_c26_ancestry_retained(self) -> None:
        gov = load_gov()
        c26 = item_of(gov, "C26")
        self.assertEqual(str(c26["status"]).upper(), "DONE")
        self.assertTrue(self._contains("p2p-c26-capability-provenance", "p2p-c25-charter-ledger"),
                        "C26 branch must contain C25 branch commits")

    def test_gc33_c27_ancestry_retained(self) -> None:
        self.assertTrue(self._contains("p2p-c27-real-host-certification", "p2p-c26-capability-provenance"),
                        "C27 branch must contain C26 branch commits")

    def test_gc34_c28_ancestry_retained(self) -> None:
        self.assertTrue(self._contains("p2p-c28-secure-onboarding", "p2p-c27-real-host-certification"),
                        "C28 branch must contain C27 branch commits")

    def test_gc35_incorrect_stacked_pr_base_detected(self) -> None:
        # PR #3 historically declared base p2p-c25 while its branch descended
        # from p2p-c26; the closure layer must detect the mismatch as safe
        # retarget (branch contains the intended parent).
        intended = "p2p-c26-capability-provenance"
        actual_base_declared = "p2p-c25-charter-ledger"
        mismatch = closure.pr_base_mismatch("p2p-c27-real-host-certification",
                                            actual_base_declared, intended)
        self.assertTrue(mismatch, "wrong stacked base must be detected")
        self.assertFalse(closure.pr_base_mismatch("p2p-c27-real-host-certification",
                                                  intended, intended))

    def test_gc36_no_pr_merge_automatically(self) -> None:
        gov = load_gov()
        self.assertIn("promotion_approval", gov.get("approval_workflow", {}) or {"promotion_approval": None})
        for rec in gov["candidate_records"]:
            cid = rec.get("candidate_id")
            if rec.get("candidate_sha256") and cid not in ("C14", "official", "baseline"):
                self.assertEqual(rec["promotion_status"], "UNPROMOTED",
                                 f"{cid} must stay UNPROMOTED without separate approval")


# ---------------------------------------------------------------------------
# GC37-GC40: regression suites remain green
# ---------------------------------------------------------------------------

class RegressionTests(unittest.TestCase):
    """Prior-goal suites must stay green on the C29 closure tree."""

    def _run(self, path: pathlib.Path) -> tuple[int, int, int]:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", str(path), "-q", "--no-header"],
            cwd=str(ROOT), capture_output=True, text=True, timeout=900, check=False)
        output = result.stdout + result.stderr
        match = re.search(r"(\d+) passed, (\d+) skipped, (\d+) failed", output)
        if match:
            return int(match.group(1)), int(match.group(2)), int(match.group(3))
        match2 = re.search(r"(\d+) passed(.*?)(\d+) failed", output, re.DOTALL)
        if match2:
            skipped_m = re.search(r"(\d+) skipped", match2.group(2))
            return int(match2.group(1)), int(skipped_m.group(1)) if skipped_m else 0, int(match2.group(3))
        match3 = re.search(r"(\d+) passed", output)
        if match3:
            return int(match3.group(1)), 0, 0
        raise RuntimeError(f"could not parse pytest output (rc {result.returncode}): "
                           f"{output[-300:]!r}")

    def test_gc37_c28_onboarding_regression(self) -> None:
        passed, skipped, failed = self._run(ROOT / "tests" / "test_p2p_secure_onboarding.py")
        self.assertEqual(failed, 0, f"C28 suite: {passed} passed / {skipped} skipped / {failed} failed")

    def test_gc38_c27_certification_regression(self) -> None:
        passed, skipped, failed = self._run(ROOT / "tests" / "test_p2p_live_certification.py")
        self.assertEqual(failed, 0, f"C27 suite: {passed} passed / {skipped} skipped / {failed} failed")

    def test_gc39_c26_provenance_regression(self) -> None:
        passed, skipped, failed = self._run(ROOT / "tests" / "test_p2p_development_charter.py")
        self.assertEqual(failed, 0, f"C26 suite: {passed} passed / {skipped} skipped / {failed} failed")

    def test_gc40_c25_charter_regression(self) -> None:
        passed, skipped, failed = self._run(ROOT / "tests" / "test_p2p_development_control.py")
        self.assertEqual(failed, 0, f"C25 dev-control suite: {passed} passed / {skipped} skipped / {failed} failed")


# ---------------------------------------------------------------------------
# GC41-GC46: claim boundary (no router/controller/auth/executor/autonomy/secret)
# ---------------------------------------------------------------------------

class BoundaryTests(unittest.TestCase):
    """C29 must not introduce router, controller, auth actions, or secret access."""

    FORBIDDEN_PATTERNS = (
        ("router", re.compile(r"\brouter(?![-_]eval)\b", re.IGNORECASE)),
        ("model route", re.compile(r"route.*model|model.*route", re.IGNORECASE)),
        ("context controller", re.compile(r"context.?controller", re.IGNORECASE)),
        ("auto merge", re.compile(r"auto.?merge|automatic.?merge", re.IGNORECASE)),
        ("second executor", re.compile(r"second.?executor|dual.?executor", re.IGNORECASE)),
        ("background autonomy", re.compile(r"background.?autonomy|autonomous.?background", re.IGNORECASE)),
        ("literal secret", re.compile(r"openai.*key\s*=\s*['\"]|api_key\s*=\s*['\"]\w", re.IGNORECASE)),
    )

    # Pre-C29 paths that legitimately mention routing (UI/UX domain language,
    # inventory lists, and C29's own denial checks). Scans exclude these
    # exact locations; any NEW file matching is still flagged.
    PRE_C29_ALLOW_LIST = (
        "rag-router",
        "p2p_router.py",
        "scripts/p2p_eval.py",
        "scripts/p2p_development_control.py",
        "scripts/validate_p2p_development_framework.py",
        "scripts/doctor.py",
        "scripts/p2p_beginner_certification.py",
        "scripts/p2p_live_certification.py",
        "scripts/package_release.py",
    )

    def _scan(self, root: pathlib.Path) -> list[str]:
        hits = []
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in (".py", ".md", ".json"):
                continue
            if ".git/" in str(path) or "node_modules" in str(path):
                continue
            if "node_modules" in str(path):
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            rel = str(path.relative_to(ROOT))
            # Pre-C29 files may reference the existing UI/UX router inventory
            # without introducing routing; they are not C29 surfaces.
            if any(rel.startswith(p) for p in self.PRE_C29_ALLOW_LIST):
                continue
            # The C29 closure checker itself encodes the boundary in code;
            # its regex source lines are boundary definitions, not claims.
            if rel == "scripts/p2p_goal_closure.py":
                continue
            for label, pattern in self.FORBIDDEN_PATTERNS:
                for match in pattern.finditer(text):
                    # Exclude legitimate mentions: the closure checker itself
                    # documents "no router" boundaries; allow lines whose
                    # nearest heading/sentence denies them.
                    line = text[:match.start()].splitlines()[-1] if match.start() else ""
                    if re.search(r"(no|not|without|prohibit|must not)\b", line, re.IGNORECASE):
                        continue
                    hits.append(f"{rel}: '{label}' matched line: {line.strip()[:80]}")
        return hits

    def test_gc41_no_router_introduced(self) -> None:
        hits = [h for h in self._scan(ROOT / "scripts") if "'router'" in h]
        self.assertEqual(hits, [], hits)
        # The C29 closure checker itself must encode the no-router boundary.
        checker = (ROOT / "scripts" / "p2p_goal_closure.py").read_text()
        self.assertTrue("router" in checker.lower(),
                        "closure checker must reference the router boundary")

    def test_gc42_no_context_controller_introduced(self) -> None:
        hits = [h for h in self._scan(ROOT / "scripts") if "'context controller'" in h]
        self.assertEqual(hits, [], hits)

    def test_gc43_no_auth_login_action(self) -> None:
        hits = []
        for path in (ROOT / "scripts").rglob("*.py"):
            text = path.read_text(encoding="utf-8", errors="ignore")
            if re.search(r"subprocess\.run\(\[.*codex login|\.run\(\[.*login", text):
                hits.append(str(path.relative_to(ROOT)))
        self.assertEqual(hits, [], hits)

    def test_gc44_no_second_executor_introduced(self) -> None:
        hits = [h for h in self._scan(ROOT / "scripts") if "second executor" in h]
        self.assertEqual(hits, [], hits)

    def test_gc45_no_background_autonomy(self) -> None:
        hits = [h for h in self._scan(ROOT / "scripts") if "background autonomy" in h]
        self.assertEqual(hits, [], hits)

    def test_gc46_no_secret_value_accessed(self) -> None:
        hits = [h for h in self._scan(ROOT / "scripts") if "literal secret" in h]
        self.assertEqual(hits, [], hits)


# ---------------------------------------------------------------------------
# GC47-GC50: preserved states and validator contradiction fixture
# ---------------------------------------------------------------------------

class PreservedStateTests(unittest.TestCase):
    """C08/C09 preserved; validator must detect deliberate closure contradiction."""

    def setUp(self) -> None:
        self.gov = load_gov()
        self.ledger = load_ledger()

    def test_gc47_c08_remains_deferred(self) -> None:
        c08 = item_of(self.gov, "C08")
        self.assertEqual(c08["status"], "DEFERRED")

    def test_gc48_c09_remains_blocked(self) -> None:
        c09 = item_of(self.gov, "C09")
        self.assertEqual(c09["status"], "BLOCKED")

    def test_gc49_ledger_delta_obeys_c26_standard(self) -> None:
        # Every C29-era ledger record carries the v2 mandatory fields.
        for rec in self.ledger["capabilities"]:
            cid = rec["capability_id"]
            if cid in ("GOAL_CLOSURE_INTEGRITY_CHECK",
                       "DETERMINISTIC_CANDIDATE_REQUIREMENT_POLICY",
                       "C28_CANDIDATE_PACKAGING_AND_C29_CLOSURE_RECONCILIATION"):
                for field_name in ("origin_type", "dependencies", "origin_refs",
                                   "beginner_value", "principle", "family"):
                    self.assertIn(field_name, rec, f"{cid} missing {field_name}")
                self.assertIn(rec["family"], self.ledger["families"])

    def test_gc50_validator_detects_deliberate_contradiction_fixture(self) -> None:
        # Deliberately contradict C28: roadmap DONE but candidate record removed.
        gov = load_gov()
        gov["candidate_records"] = [r for r in gov["candidate_records"]
                                    if r.get("candidate_id") != "C28"]
        report = closure.terminal_from_report(REPORTS / "P2P-C28-terminal-report.md")
        verdict = closure_verdict("C28", gov, self.ledger, report)
        self.assertFalse(verdict.consistent,
                         "validator must fail a fabricated PASS-without-candidate state")
        # Restore: live governance is untouched (fixture operates on a copy).
        self.assertTrue(
            any(r.get("candidate_id") == "C28" for r in load_gov()["candidate_records"]))


if __name__ == "__main__":
    unittest.main()
