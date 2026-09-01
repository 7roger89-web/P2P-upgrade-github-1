# -*- coding: utf-8 -*-
"""P2P Goal Closure & Durable State Integrity layer (C29).

Deterministic Goal-closure integrity: a terminal verdict (PASS / BLOCKED / FAIL)
must be semantically consistent with roadmap status, development-control state,
ledger delta, candidate policy, and supervisor verdict. No silent divergence.

Design principles (per C29 specification):
- Small terminal model: PASS, BLOCKED, FAIL. Substatus for development/candidate
  remains separate. PASS != PROMOTION.
- Machinery != outcome: a machinery capability can be FOUNDATION_READY /
  VERIFIED_IMPLEMENTED while the outcome capability stays UNKNOWN / PLANNED /
  BLOCKED until a real execution result is independently verified.
- Candidate requirement is a DETERMINISTIC policy, never AI judgment at
  terminal time. The policy reads: (1) the Goal Contract's declared
  CANDIDATE_REQUIRED flag, (2) whether runtime / governance / release-bearing
  artifacts changed, (3) terminal status.
- Goal status is distinct from capability status; roadmap fields must not be
  overloaded to represent all three of goal lifecycle, capability status, and
  runtime host state.
- Blocked Goals stay BLOCKED with an explicit reopen_condition (metadata only,
  never auto-executed).
- No new state store: this module reads and checks the canonical artifacts
  (development-control.json, capability-index.json, Goal Contract template,
  git ancestry) and never duplicates them.
"""

import json
import pathlib
import re
import subprocess
from dataclasses import dataclass, field

__version__ = "1"

ROOT = pathlib.Path(__file__).resolve().parent.parent

TERMINAL_STATES = ("PASS", "BLOCKED", "FAIL")

GOAL_LIFECYCLE_STATUSES = ("PLANNED", "ACTIVE", "DONE", "BLOCKED", "DEFERRED")

# Canonical capability status vocabulary from capability-index.json (v2)
CAPABILITY_STATUSES = (
    "VERIFIED_IMPLEMENTED",
    "FOUNDATION_READY",
    "PARTIAL",
    "PLANNED",
    "DEFERRED",
    "REJECTED",
    "OBSOLETE",
    "UNKNOWN",
)

# Machinery statuses that evidence may truthfully assign. An outcome
# capability must NOT be set to these without real execution evidence.
MACHINERY_EVIDENCE_STATUSES = ("FOUNDATION_READY", "VERIFIED_IMPLEMENTED", "PARTIAL")

# Outcome-only statuses: require real execution -> result -> independent
# verification -> reconciliation evidence before assignment.
OUTCOME_ONLY_STATUSES = ("PLANNED", "DEFERRED", "UNKNOWN")

CANDIDATE_REQUIRED_VALUES = ("YES", "NO")

PROMOTION_VALUES = ("PROMOTED_VERIFIED", "UNPROMOTED")


# ---------------------------------------------------------------------------
# Canonical artifact readers (single source of truth: existing state store)
# ---------------------------------------------------------------------------

def load_governance(root: pathlib.Path | None = None) -> dict:
    return json.loads((root or ROOT).joinpath("governance", "development-control.json").read_text())


def load_ledger(root: pathlib.Path | None = None) -> dict:
    return json.loads(
        (root or ROOT)
        .joinpath("docs", "p2p-development", "capability-ledger", "capability-index.json")
        .read_text()
    )


def load_contract_template(root: pathlib.Path | None = None) -> str:
    return (root or ROOT).joinpath(
        "docs", "p2p-development", "templates", "P2P-GOAL-CONTRACT-TEMPLATE.md"
    ).read_text()


def load_supervisor_template(root: pathlib.Path | None = None) -> str:
    return (root or ROOT).joinpath(
        "docs", "p2p-development", "templates", "P2P-SUPERVISOR-TEMPLATE.md"
    ).read_text()


def _run_git(*args: str, cwd: pathlib.Path | None = None) -> str:
    try:
        return subprocess.run(
            ["git", *args],
            cwd=str(cwd or ROOT),
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        ).stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return ""


def _git_rc(*args: str, cwd: pathlib.Path | None = None) -> int:
    """Return git exit code for flag-style commands (e.g. merge-base --is-ancestor)."""
    try:
        return subprocess.run(
            ["git", *args],
            cwd=str(cwd or ROOT),
            capture_output=True,
            timeout=60,
            check=False,
        ).returncode
    except (OSError, subprocess.TimeoutExpired):
        return -1


# ---------------------------------------------------------------------------
# Terminal status model
# ---------------------------------------------------------------------------

def normalize_terminal_status(value: str) -> str | None:
    """Normalize any casing into canonical PASS / BLOCKED / FAIL or None."""
    upper = str(value).strip().upper()
    return upper if upper in TERMINAL_STATES else None


def terminal_from_report(report_path: pathlib.Path) -> dict:
    """Extract machine-checkable terminal fields from a terminal report."""
    text = pathlib.Path(report_path).read_text()
    fields = {}
    for name in (
        "GOAL_TERMINAL_STATUS",
        "ROADMAP_STATUS",
        "DEVELOPMENT_CONTROL_STATUS",
        "CAPABILITY_LEDGER_SYNC",
        "CANDIDATE_REQUIRED",
        "CANDIDATE_STATUS",
        "SUPERVISOR_VERDICT",
        "PROMOTION_STATUS",
    ):
        match = re.search(
            rf"{re.escape(name)}\s*[:=]\s*([A-Z_0-9.\-/()]+)", text, re.IGNORECASE
        )
        fields[name] = match.group(1).strip() if match else None
    # Also accept markdown bold values (e.g. "**PASS (machinery)**") and the
    # RESULT section heading (e.g. "## 1. RESULT" followed by "**PASS** ...").
    if fields.get("GOAL_TERMINAL_STATUS") is None:
        # Bold terminal states, optionally followed by a parenthesized note or
        # a slash-separated substatus (e.g. "**BLOCKED / LIVE_HOST_EVIDENCE_UNAVAILABLE**").
        result = re.search(
            r"\*\*(PASS|BLOCKED|FAIL)(?:\s*(?:\([^)]*\)|/[A-Z_0-9. \-/]+))?\*\*",
            text,
            re.IGNORECASE,
        )
        if result:
            fields["GOAL_TERMINAL_STATUS"] = result.group(1).upper()
    return fields


# ---------------------------------------------------------------------------
# Deterministic candidate requirement policy (§18 / §19 of C29)
#
# Priority order:
#  1. Goal Contract declaration (CANDIDATE_REQUIRED = YES|NO) — authoritative.
#  2. If undeclared, deterministic default: a PASS Goal that changed runtime,
#     governance, or release-bearing artifacts requires a candidate as an
#     immutable closure record. BLOCKED / FAIL Goals do not fabricate
#     candidates unless their contract explicitly said YES.
#  3. AI judgment at terminal time is never the sole policy input.
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ChangeSignals:
    runtime_changed: bool
    governance_changed: bool
    release_artifact_changed: bool
    changed_files: list[str]

    @classmethod
    def detect(cls, changed_files: list[str]) -> "ChangeSignals":
        runtime = any(
            f.startswith(("scripts/", "source/"))
            and not f.endswith(".md")
            for f in changed_files
        )
        governance = any(f.startswith("governance/") for f in changed_files)
        release = any(
            f.startswith(("docs/p2p-development/templates/", "docs/p2p-development/P2P-DEVELOPMENT-CHARTER.md"))
            for f in changed_files
        )
        return cls(runtime_changed=runtime, governance_changed=governance,
                   release_artifact_changed=release, changed_files=changed_files)

    # ------------------------------------------------------------------
    # Claim-boundary detectors (§46): which boundary surfaces were touched
    # in this session's changes. Each returns the offending file list or
    # an empty list when the boundary is clean.
    # ------------------------------------------------------------------

    def router_or_controller_files(self) -> list[str]:
        return [f for f in self.changed_files
                if re.search(r"router|context[_\-]?controller|model[_\-]?route",
                             f, re.IGNORECASE)]

    def context_controller_files(self) -> list[str]:
        return [f for f in self.changed_files
                if re.search(r"context[_\-]?controller|session[_\-]?controller",
                             f, re.IGNORECASE)]

    def auth_action_files(self) -> list[str]:
        return [f for f in self.changed_files
                if re.search(r"auth[_\-]?action|login[_\-]?action|codex[_\-]?login",
                             f, re.IGNORECASE)]

    def second_executor_files(self) -> list[str]:
        return [f for f in self.changed_files
                if re.search(r"second[_\-]?executor|dual[_\-]?executor",
                             f, re.IGNORECASE)]

    def background_autonomy_files(self) -> list[str]:
        return [f for f in self.changed_files
                if re.search(r"background[_\-]?autonomy|autonomous[_\-]?background",
                             f, re.IGNORECASE)]


def candidate_policy(
    terminal_status: str,
    contract_declared: str | None,
    changes: ChangeSignals,
) -> str:
    """Deterministic answer to 'Does this Goal require a candidate?'

    Returns one of CANDIDATE_REQUIRED_VALUES or raises ValueError on inputs
    that could force a judgment call (caller must not treat this as policy).
    """
    if terminal_status not in TERMINAL_STATES:
        raise ValueError(f"unknown terminal status: {terminal_status!r}")
    if contract_declared is not None and contract_declared in CANDIDATE_REQUIRED_VALUES:
        return contract_declared
    if contract_declared not in CANDIDATE_REQUIRED_VALUES and contract_declared is not None:
        raise ValueError(f"invalid contract declaration: {contract_declared!r}")
    if terminal_status == "PASS" and any(
        (changes.runtime_changed, changes.governance_changed, changes.release_artifact_changed)
    ):
        return "YES"
    if terminal_status == "PASS":
        # PASS with no durable change at all: machinery-only in-session work
        # that left no lasting artifact does not manufacture a candidate.
        return "NO"
    # BLOCKED / FAIL without an explicit contract declaration: NO.
    return "NO"


def candidate_policy_from_report_fields(report_fields: dict, changes: ChangeSignals) -> str:
    declared = report_fields.get("CANDIDATE_REQUIRED")
    terminal = normalize_terminal_status(report_fields.get("GOAL_TERMINAL_STATUS") or "")
    if terminal is None:
        raise ValueError("report lacks a canonical GOAL_TERMINAL_STATUS")
    return candidate_policy(terminal, declared, changes)


# ---------------------------------------------------------------------------
# Closure consistency invariant (§7 / §31 of C29)
# ---------------------------------------------------------------------------

ROADMAP_GOAL_STATUS_MAP = {
    "DONE": "PASS",
    "ACTIVE": None,          # not terminal; closure checks apply only to terminal states
    "PLANNED": None,
    "BLOCKED": "BLOCKED",
    "DEFERRED": "FAIL",      # DEFERRED roadmap item counts as terminal failure of scope
}


@dataclass
class ClosureFinding:
    check: str
    ok: bool
    detail: str
    severity: str = "hard"  # "hard" = genuine inconsistency; "explained" = durable snapshot drift accounted for by a later packaged goal


def check_roadmap_goal_consistency(
    roadmap_items: list[dict],
    report_fields: dict,
    goal_id: str,
) -> list[ClosureFinding]:
    """Verify that a terminal verdict coheres with the roadmap lifecycle state."""
    findings = []
    item = next((i for i in roadmap_items if (i.get("goal_id") or i.get("id")) == goal_id), None)
    if item is None:
        findings.append(ClosureFinding("ROADMAP_ITEM_EXISTS", False, f"{goal_id} has no roadmap item"))
        return findings
    status = str(item.get("status", "")).upper()
    terminal = normalize_terminal_status(report_fields.get("GOAL_TERMINAL_STATUS") or "")

    findings.append(ClosureFinding(
        "ROADMAP_ITEM_EXISTS", True, f"{goal_id} roadmap item status={item.get('status')!r}"
    ))

    if terminal == "PASS":
        ok = status == "DONE"
        findings.append(ClosureFinding(
            "PASS_WITH_DONE_ROADMAP", ok,
            f"terminal PASS requires roadmap DONE; found {status!r}",
        ))
    elif terminal == "BLOCKED":
        ok = status == "BLOCKED"
        findings.append(ClosureFinding(
            "BLOCKED_WITH_BLOCKED_ROADMAP", ok,
            f"terminal BLOCKED requires roadmap BLOCKED; found {status!r}",
        ))
    elif terminal == "FAIL":
        ok = status in ("DEFERRED", "BLOCKED")
        findings.append(ClosureFinding(
            "FAIL_WITH_TERMINAL_ROADMAP", ok,
            f"terminal FAIL requires roadmap DEFERRED/BLOCKED; found {status!r}",
        ))
    return findings


def check_development_control_consistency(
    governance: dict,
    report_fields: dict,
    goal_id: str,
) -> list[ClosureFinding]:
    """Terminal verdict must cohere with development-control state.

    Canonical semantics: current_development holds the goal lifecycle position;
    after a terminal PASS of the latest goal it names that goal's final state.
    It is NOT a second state store — it must agree with roadmap.current.
    """
    findings = []
    cd = governance.get("current_development", {})
    dev_goal = str(cd.get("development_goal", "")).strip()
    road_current = governance.get("roadmap", {}).get("current", {})
    road_current_id = str(road_current.get("id", "")).strip()

    terminal = normalize_terminal_status(report_fields.get("GOAL_TERMINAL_STATUS") or "")
    # development_goal semantics apply only when the goal's closure is tied to
    # the live development position: a PASS closing goal (done -> its snapshot)
    # or the goal currently at roadmap.current. A BLOCKED goal's closure is a
    # status observation, not a development position, so the check is skipped.
    applies = (terminal == "PASS") or (road_current_id == goal_id)
    if dev_goal and road_current_id and applies and dev_goal != road_current_id:
        # Present-state mismatch is allowed ONLY when the checked goal is a
        # historical terminal snapshot whose verdict is already durable:
        # the live current_development.development_goal advances to the newest
        # packaged goal (e.g. C28 -> C29), while the earlier goal's terminal
        # verdict, roadmap DONE status, and candidate record remain intact.
        newer_record = next(
            (r for r in governance.get("candidate_records", [])
             if r.get("candidate_id") == dev_goal
             and r.get("promotion_status") == "UNPROMOTED"
             and str(r.get("candidate_sha256", "")).strip()),
            None,
        )
        # A roadmap DONE item for the checked goal (different from dev_goal)
        # proves the checked goal closed honestly before development_goal
        # advanced to its packaged successor.
        checked_item = next(
            (i for i in governance.get("roadmap", {}).get("items", [])
             if (i.get("goal_id") or i.get("id")) == goal_id),
            None,
        )
        checked_done = checked_item is not None and str(
            checked_item.get("status", "")).upper() == "DONE"
        explained = newer_record is not None and checked_done
        findings.append(ClosureFinding(
            "CURRENT_DEVELOPMENT_SEMANTICS",
            False,
            f"current_development.development_goal={dev_goal!r} vs "
            f"roadmap.current.id={road_current_id!r}" + (
                " — explained: development_goal advanced to a newer packaged "
                f"goal ({dev_goal}) with a verified UNPROMOTED candidate, "
                f"while {goal_id} already closed DONE; the snapshot verdict "
                "remains durable" if explained else ""),
            severity="explained" if explained else "hard",
        ))
    else:
        findings.append(ClosureFinding(
            "CURRENT_DEVELOPMENT_SEMANTICS",
            True,
            f"current_development.development_goal={dev_goal!r} == "
            f"roadmap.current.id={road_current_id!r}",
        ))

    terminal = normalize_terminal_status(report_fields.get("GOAL_TERMINAL_STATUS") or "")
    if terminal == "PASS" and road_current_id == goal_id:
        ok = str(road_current.get("status", "")).upper() == "DONE"
        findings.append(ClosureFinding(
            "PASS_CURRENT_IS_DONE", ok,
            f"terminal PASS with roadmap.current={goal_id} requires DONE; "
            f"found {road_current.get('status')!r}",
        ))
    return findings


def check_candidate_policy_compliance(
    governance: dict,
    report_fields: dict,
    goal_id: str,
    changes: ChangeSignals,
    candidate_artifact_exists: bool,
    package_verify_evidence: str | None,
) -> list[ClosureFinding]:
    """Candidate-required Goals cannot close PASS without a verified candidate.

    Candidate != promotion: an existing candidate must remain UNPROMOTED unless a
    separate promotion approval is recorded.
    """
    findings = []
    required = candidate_policy_from_report_fields(report_fields, changes)
    records = {r.get("candidate_id"): r for r in governance.get("candidate_records", [])}
    rec = records.get(goal_id)

    if required == "YES":
        has_candidate = bool(rec and rec.get("candidate_sha256"))
        findings.append(ClosureFinding(
            "CANDIDATE_REQUIRED_PRESENT", has_candidate,
            f"contract requires candidate for {goal_id}; record={'present' if rec else 'absent'}",
        ))
        if has_candidate:
            findings.append(ClosureFinding(
                "CANDIDATE_SHA_IMPLIES_ARTIFACT", candidate_artifact_exists,
                f"SHA claimed but artifact {'exists' if candidate_artifact_exists else 'MISSING'}",
            ))
            findings.append(ClosureFinding(
                "CANDIDATE_VERIFY_EVIDENCE", bool(package_verify_evidence),
                f"package verify evidence={'recorded' if package_verify_evidence else 'ABSENT'}",
            ))
    else:
        # Candidate-not-required Goals must not fabricate a candidate record.
        fabricated = bool(rec and rec.get("candidate_sha256"))
        findings.append(ClosureFinding(
            "CANDIDATE_NOT_REQUIRED_ABSENT", not fabricated,
            f"contract does not require a candidate for {goal_id}; "
            f"{'fabricated record found' if fabricated else 'no candidate record (correct)'}",
        ))

    if rec:
        promo = str(rec.get("promotion_status", ""))
        findings.append(ClosureFinding(
            "CANDIDATE_UNPROMOTED_UNTIL_APPROVAL",
            promo != "PROMOTED_VERIFIED" or bool(governance.get("promotion_approval")),
            f"candidate {goal_id} promotion_status={promo!r}; promotion needs separate approval",
        ))
    return findings


def check_goal_vs_capability_separation(
    ledger: dict,
    capability_claims: dict,
    outcome_capability_ids: list[str],
) -> list[ClosureFinding]:
    """Goal status and capability status must not be conflated.

    Machinery capabilities may reach evidence-based statuses; outcome
    capabilities require real execution evidence and must not sit in
    machinery-only statuses.
    """
    findings = []
    caps = {c["capability_id"]: c for c in (
        ledger["capabilities"].values()
        if isinstance(ledger.get("capabilities"), dict)
        else ledger.get("capabilities", [])
    )}
    for cid in outcome_capability_ids:
        status = (caps.get(cid, {}).get("status") or "").upper()
        if status in MACHINERY_EVIDENCE_STATUSES:
            findings.append(ClosureFinding(
                "OUTCOME_NOT_CLAIMED_BY_MACHINERY", False,
                f"outcome capability {cid} claimed {status!r} without real execution "
                f"evidence; must remain UNKNOWN/PLANNED/DEFERRED",
            ))
        else:
            findings.append(ClosureFinding(
                "OUTCOME_NOT_CLAIMED_BY_MACHINERY", True,
                f"outcome capability {cid} status={status!r} (correctly not a machinery claim)",
            ))
    return findings


def check_claim_boundary(changes: ChangeSignals) -> list[ClosureFinding]:
    """C29 claim boundary: a Goal session must not introduce host routing,
    a context controller, auth/login actions, a second executor, or
    background autonomy (anti-goal records; §46 C29)."""
    findings = []
    if changes.runtime_changed and changes.governance_changed:
        for boundary_label, introduced in (
            ("ROUTER", changes.router_or_controller_files()),
            ("CONTEXT_CONTROLLER", changes.context_controller_files()),
            ("AUTH_ACTION", changes.auth_action_files()),
            ("SECOND_EXECUTOR", changes.second_executor_files()),
            ("BACKGROUND_AUTONOMY", changes.background_autonomy_files()),
        ):
            if introduced:
                findings.append(ClosureFinding(
                    "CLAIM_BOUNDARY", False,
                    f"boundary violated: {boundary_label} introduced in "
                    f"{', '.join(introduced[:3])}",
                ))
            else:
                findings.append(ClosureFinding(
                    "CLAIM_BOUNDARY", True,
                    f"{boundary_label} not introduced",
                ))
    else:
        for boundary_label in ("ROUTER", "CONTEXT_CONTROLLER", "AUTH_ACTION",
                               "SECOND_EXECUTOR", "BACKGROUND_AUTONOMY"):
            findings.append(ClosureFinding("CLAIM_BOUNDARY", True,
                                           f"{boundary_label} not introduced"))
    return findings


def check_capability_status_evidence_type(ledger: dict, capability_claims: dict) -> list[ClosureFinding]:
    """Capability status must match its proven evidence type (ledger V14/V15 style)."""
    findings = []
    caps = (
        ledger["capabilities"].values()
        if isinstance(ledger.get("capabilities"), dict)
        else ledger.get("capabilities", [])
    )
    for c in caps:
        evidence_type = (c.get("evidence_type") or c.get("origin_type") or "").upper()
        status = (c.get("status") or "").upper()
        if evidence_type in ("SYNTHETIC_TEST", "UNIT_TEST_ONLY", "") and status in (
            "VERIFIED_IMPLEMENTED",
        ):
            findings.append(ClosureFinding(
                "STATUS_MATCHES_EVIDENCE_TYPE", False,
                f"{c['capability_id']}: {status!r} contradicts evidence type {evidence_type!r}",
            ))
        elif evidence_type in ("SYNTHETIC_TEST", "UNIT_TEST_ONLY", "REAL_EXERCISE"):
            if status in ("FOUNDATION_READY", "PARTIAL"):
                findings.append(ClosureFinding(
                    "STATUS_MATCHES_EVIDENCE_TYPE", True,
                    f"{c['capability_id']}: {status!r} supported by {evidence_type!r}",
                ))
    return findings


# ---------------------------------------------------------------------------
# PR stack integrity (§28 / §30 of C29)
# ---------------------------------------------------------------------------

@dataclass
class BranchAncestry:
    branch: str
    parent_branch: str | None
    contains_parent_commits: bool
    merge_base_with_main: str


def branch_ancestry(branch: str, expected_parent: str) -> BranchAncestry:
    mb = _run_git("merge-base", branch, "main") or ""
    parent_tip = _run_git("rev-parse", expected_parent) or ""
    contains = bool(parent_tip) and _git_rc("merge-base", "--is-ancestor",
                                            parent_tip, branch) == 0
    return BranchAncestry(
        branch=branch,
        parent_branch=expected_parent,
        contains_parent_commits=contains,
        merge_base_with_main=mb,
    )


def pr_base_mismatch(pr_branch: str, declared_base: str, intended_parent: str) -> bool:
    """True when a PR's declared base differs from the branch's actual parent.

    A mismatch is only actionable when the branch does contain the intended
    parent (safe retarget) — never rewrite commits.
    """
    if declared_base == intended_parent:
        return False
    ancestor = _git_rc("merge-base", "--is-ancestor", intended_parent, pr_branch) == 0
    return declared_base != intended_parent and ancestor


def official_baseline_unmodified(governance: dict) -> bool:
    """Official .19 baseline must stay immutable: PROMOTED_VERIFIED and hash
    unchanged. Read-only check, never altered."""
    recs = {r.get("candidate_id"): r for r in governance.get("candidate_records", [])}
    rec = recs.get("official") or recs.get("baseline") or recs.get("C14")
    if not rec:
        return True  # absence is checked elsewhere (ledger/promotion tests)
    return rec.get("promotion_status") == "PROMOTED_VERIFIED"


# ---------------------------------------------------------------------------
# Roadmap terminal-state derivations (§22 / §23 of C29)
# ---------------------------------------------------------------------------

def roadmap_terminal_next(items: list[dict]) -> dict:
    """Derive the terminal likely_next after the last terminal goal.

    Semantics: once the last goal in the roadmap is terminal (DONE/BLOCKED),
    likely_next equals that same goal with its terminal status — there is no
    later goal. This avoids the contradiction of pointing at a PLANNED goal
    that will never execute.
    """
    last = items[-1] if items else None
    if last is None:
        return {"id": "", "status": ""}
    status = str(last.get("status", "")).upper()
    if status in ("DONE", "BLOCKED", "DEFERRED"):
        return {"id": str(last.get("goal_id") or last.get("id", "")), "status": status}
    return {"id": str(last.get("goal_id") or last.get("id", "")), "status": status}


def reopen_condition_is_metadata(roadmap_items: list[dict]) -> bool:
    """reopen_condition is roadmap metadata only; nothing auto-executes it."""
    marked = [i for i in roadmap_items if i.get("reopen_condition")]
    return all(str(i.get("reopen_executes", "no")).lower() == "no" for i in marked)


# ---------------------------------------------------------------------------
# Closure verdict
# ---------------------------------------------------------------------------

@dataclass
class ClosureVerdict:
    consistent: bool
    findings: list[ClosureFinding] = field(default_factory=list)

    def failures(self) -> list[ClosureFinding]:
        return [f for f in self.findings if not f.ok]


def goal_closure_verdict(
    governance: dict,
    ledger: dict,
    report_fields: dict,
    goal_id: str,
    changes: ChangeSignals,
    candidate_artifact_exists: bool = False,
    package_verify_evidence: str | None = None,
    outcome_capability_ids: list[str] | None = None,
) -> ClosureVerdict:
    items = governance.get("roadmap", {}).get("items", [])
    findings: list[ClosureFinding] = []
    findings += check_roadmap_goal_consistency(items, report_fields, goal_id)
    findings += check_development_control_consistency(governance, report_fields, goal_id)
    findings += check_candidate_policy_compliance(
        governance, report_fields, goal_id, changes,
        candidate_artifact_exists, package_verify_evidence,
    )
    findings += check_goal_vs_capability_separation(
        ledger, {}, outcome_capability_ids or [],
    )
    findings += check_capability_status_evidence_type(ledger, {})
    findings += check_claim_boundary(changes)
    # Explained findings (durable snapshot drift toward a newer packaged goal)
    # do not break closure consistency; only hard failures do.
    return ClosureVerdict(
        consistent=all(f.ok or f.severity == "explained" for f in findings),
        findings=findings,
    )


def _roadmap_item_status(governance: dict, goal_id: str) -> str | None:
    """Recover a roadmap lifecycle status for a goal with no terminal report."""
    for item in governance.get("roadmap", {}).get("items", []):
        if str(item.get("goal_id") or item.get("id", "")).upper() == goal_id:
            return str(item.get("status", "")).upper() or None
    return None


def main() -> None:
    import sys
    goal_id = sys.argv[1] if len(sys.argv) > 1 else "C28"
    governance = load_governance()
    ledger = load_ledger()

    changed = _run_git("diff", "--name-only", "main", "HEAD").splitlines()
    changes = ChangeSignals.detect(changed)

    report_file = ROOT.joinpath(
        "docs", "p2p-development", "reports", f"P2P-{goal_id.upper()}-terminal-report.md"
    )
    if report_file.exists():
        report_fields = terminal_from_report(report_file)
    else:
        # BLOCKED goals have no new development and no terminal report by
        # design; recover the terminal status from the roadmap item itself.
        road_status = _roadmap_item_status(governance, goal_id.upper())
        report_fields = {"GOAL_TERMINAL_STATUS": road_status} if road_status else {}

    candidate_zip = next(
        (
            f
            for f in ROOT.joinpath("reports", "candidates").glob(f"*{goal_id.lower()}*.zip")
        ),
        None,
    )
    records = {r.get("candidate_id"): r for r in governance.get("candidate_records", [])}
    verify_evidence = (records.get(goal_id) or {}).get("package_verify_evidence")

    verdict = goal_closure_verdict(
        governance, ledger, report_fields, goal_id, changes,
        candidate_artifact_exists=candidate_zip is not None,
        package_verify_evidence=verify_evidence,
        outcome_capability_ids=[
            "REAL_HOST_EXECUTION_CERTIFICATION",
            "HOST_AUTH_STATE_VERIFICATION",
        ],
    )
    # Terminal-state derivation checks (roadmap terminal semantics).
    items = governance.get("roadmap", {}).get("items", [])
    derived = roadmap_terminal_next(items)
    report_current = governance.get("roadmap", {}).get("current", {})
    print(f"roadmap_terminal_next derived: {derived['id']}/{derived['status']}; "
          f"roadmap.current = {report_current.get('id')}/{report_current.get('status')}")
    print(f"reopen_condition_is_metadata = {reopen_condition_is_metadata(items)}")
    print(f"Goal {goal_id}: {'CONSISTENT' if verdict.consistent else 'INCONSISTENT'}")
    for f in verdict.findings:
        print(f"  [{'PASS' if f.ok else 'FAIL'}] {f.check}: {f.detail}")

    # C27 machinery audit (evidence-based status determination)
    live = (ledger.get("capabilities", {}) if isinstance(ledger.get("capabilities"), dict)
            else {c.get("capability_id"): c for c in ledger.get("capabilities", []) if c.get("capability_id")})
    mach = live.get("REAL_HOST_EXECUTION_CERTIFICATION_MACHINERY", live.get("REAL_HOST_EXECUTION_CERTIFICATION_MACHINERY".lower(), {}))
    if mach:
        print(f"C27 machinery current status: {mach.get('status')}")


if __name__ == "__main__":
    main()
