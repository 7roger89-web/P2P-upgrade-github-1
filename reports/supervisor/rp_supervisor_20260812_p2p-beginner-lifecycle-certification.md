# Supervisor Report — P2P Beginner Lifecycle Behavioral Certification

Date: 2026-08-12
Reviewer lane: independent supervisor / zero-trust acceptance
Scope reviewed: evaluator, direct behavior tests, persistent certification report, governance boundary, and final claims.

## Verdict

`PASS`

This PASS applies to the implemented evaluator/evidence package. It does not convert the measured beginner readiness result into an unconditional PASS. The persistent certification result is `HARNESS PASS` plus `CERTIFIED_WITH_LIMITATIONS`.

## Source inspection

- `scripts/p2p_beginner_certification.py` is a standard-library-only evaluator. It invokes the existing workflow/router/doctor/UIUX CLIs, uses public trust/context/evidence contracts as supplements, creates temporary synthetic projects, and does not edit existing runtime implementation files.
- `tests/test_p2p_beginner_certification.py` contains two direct behavior tests: full isolated certification and false-PASS/schema/readiness guards.
- Approved capability/test-eval SPECs, `AGENTS.md`, planner artifacts, and the System Architect report were inspected before acceptance.
- Anvien was queried; the target unpacked path is not registered. The configured indexed repository is unrelated (`app_game_truyen`), which was not touched.

## Runtime evidence re-run

| Check | Result |
|---|---|
| Full test suite | `45/45 PASS` |
| Final certification | `HARNESS PASS`, `CERTIFIED_WITH_LIMITATIONS` |
| Scenarios / machine rows | `4 / 205` |
| Critical failures | `0` |
| Report schema / row schema | `PASS / PASS` |
| Capability doctor | `PASS` |
| Canonical identities / denominator | exact 8 / 8 |
| Full canonical quorum | `8/8` |
| Aesthetica | profile resolved, `simulated=false`, identity not verified; never counted |
| Governance drift | `PASS` |
| Release artifact SHA-256 | unchanged: `1d1d00913b215e513a2441f194125b96e9e7999a0659ae713d3e10d2de4dcccb` |
| Immutable source inventory | `152` files |
| User-project writes | `0` |
| External integrations | `none` |
| Report secret/CoT scan | `PASS` |

## Behavioral acceptance

- Four required project shapes execute: internal business tool, customer-facing mobile product, interactive content experience, and backend-heavy non-UI.
- Scenario A preserves one synthetic project across 15 lifecycle stages and includes changed requirements, debugging pressure, controlled recovery, maintenance, migration marker, and WHY.
- The broken acceptance marker produces `BLOCKED`; the evaluator does not accept a false completion. The later synthetic repair is observable and does not erase the earlier blocker.
- No unnecessary framework/database/API/ORM/Docker choices were delegated to the beginner in observed outputs.
- The current runtime does not persist beginner discovery questions in its Goal contract and some colloquial/incomplete prompts are blocked by current Goal classification. These are correctly reported as limitations, not silently repaired.
- UI/UX routing is recorded for mobile/content/internal prompts; the non-UI backend case does not invoke UIUX. No Aesthetica output is simulated.
- Deployment remains unproven, upgrade is synthetic-project-state-only, and WHY remains distributed across Goal/report/ledger artifacts. These are partial dimensions, not unsupported success claims.

## Boundary checks

- No change was made to `scripts/p2p_workflow.py`, the router, capability contracts, canonical profiles, UIUX runtime, Aesthetica profile, `source/`, release ZIP, v5 artifact, App Game Truyện, Logistics, or any user project.
- The two new development evaluator surfaces were registered in the existing runtime lock; no release was rebuilt or published.
- No second governance system, new specialist, provider, router, Decision Trace, or Code-Impact capability was introduced.
- The final temporary harness root was removed automatically; earlier baseline/dry-run outputs were moved to the recoverable `.tmp/p2p-beginner-certification-quarantine/` folder rather than deleted.
- The source is not a Git worktree; commit hash is therefore `N/A`. Closure uses file hashes, runtime lock, test output, and report paths.

Final revalidation after the last runtime-lock refresh: `python -B -m unittest discover -s tests -p 'test_*.py' -q` -> `45/45 PASS`; capability doctor -> `PASS`; governance drift -> `PASS`; release SHA-256 remains the expected value.

## Required handoff

`PASS — evaluator/evidence package accepted; readiness remains CERTIFIED_WITH_LIMITATIONS; runtime gaps are preserved for one future Goal only.`
