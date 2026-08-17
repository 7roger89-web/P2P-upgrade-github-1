#!/usr/bin/env python3
"""Create PR #6 (p2p-c30-composable-execution-target -> p2p-c29-goal-closure-integrity)."""

import json
import subprocess

REPO = "7roger89-web/P2P-upgrade-github-1"
PAT = open("/tmp/pat.txt").read().strip()
HEAD = "p2p-c30-composable-execution-target"
BASE = "p2p-c29-goal-closure-integrity"

BODY = """## C30 — Composable Execution Target Foundation + Durable Provider-Neutral Architecture Intake

### Terminal verdict: PASS (machinery only)

After C30, P2P durably understands and deterministically validates that an execution target is NOT an AI brand, but a composition of independently replaceable components:

Harness + Provider + Model + Protocol + Tool Set + Workspace + Environment + Authentication + Permission + Evidence Freshness

**without yet routing, selecting, or executing that target** (no router, no autopilot, no background autonomy, no real execution).

### Deliverables
- `scripts/p2p_execution_target.py` — provider-neutral composable ExecutionTarget data model (profiles, eligibility, fingerprint, contract drift fail-closed, registry-enumerates-not-routes, health/ownership ladder, quiesce vocabulary)
- `tests/test_p2p_execution_target.py` — ET1–ET60, 60/60 PASS
- `docs/p2p-development/research/execution-target-pattern-research.md` — durable research intake artifact (9 sources, patterns A–O, no code copied)
- Capability ledger +17 records (13 FOUNDATION_READY, 4 PLANNED), 4 extensions; cycle-free deps, provenance honored
- Governance: C30 roadmap item PLANNED, likely_next=C30/PLANNED, current_development C30 CANDIDATE_UNPROMOTED (8.4.7-C-codex.24), candidate record, 5 enduring architectural invariants
- Charter: 5 enduring invariants (machine + human readable)
- `docs/p2p-development/current-roadmap.md` regenerated (153 records, 12 families, §3e C30 section)
- `docs/p2p-development/reports/P2P-C30-terminal-report.md` — 60-item terminal report

### Verification
- Full regression: **632 passed, 5 skipped, 0 failed** (pre-C30: 572)
- Framework validator: **64/64 PASS**
- Goal closure: `Goal C28: CONSISTENT`; dev-control PASS
- Candidate: `P2P-8.4.7-C-Codex-Edition-v24-c30-composable-execution-target-foundation-candidate-v1.zip` — verify PASS, embedded 8.4.7-C-codex.24, based on official baseline 8.4.7-C-codex.19 (immutable), **UNPROMOTED**
- C29 closure remains green (PR #5 untouched, unmerged)

### Claim boundary
C30 PASS does NOT mean: routing, AutoPilot, live support for any specific AI host, workspace isolation runtime, fallback automation, promotion, or merge. `COMPATIBILITY != CERTIFICATION`; `UNKNOWN != SUPPORTED`; `GOAL PASS != PROMOTION`. Terminal rule honored: PASS → STOP, C31 not started.

Owner approval required. No merge, no promotion, no auto-start of C31.
"""

payload = json.dumps({
    "title": "C30: Composable Execution Target Foundation + Durable Provider-Neutral Architecture Intake",
    "body": BODY,
    "head": HEAD,
    "base": BASE,
})

r = subprocess.run(
    ["curl", "-s", "-w", "\nHTTP:%{http_code}", "-X", "POST",
     f"https://api.github.com/repos/{REPO}/pulls",
     "-H", f"Authorization: Bearer {PAT}",
     "-H", "Accept: application/vnd.github+json",
     "-H", "Content-Type: application/json",
     "-d", payload],
    capture_output=True, text=True)
print(r.stdout)
print(r.stderr)
