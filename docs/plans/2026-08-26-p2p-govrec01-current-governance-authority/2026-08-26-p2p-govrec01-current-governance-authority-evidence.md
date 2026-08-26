# P2P-GOVREC01 Current Governance Authority Reconciliation Evidence Ledger

## Metadata

- Date: `2026-08-26`
- Plan: `docs/plans/2026-08-26-p2p-govrec01-current-governance-authority/2026-08-26-p2p-govrec01-current-governance-authority-plan.md`
- Evidence: `docs/plans/2026-08-26-p2p-govrec01-current-governance-authority/2026-08-26-p2p-govrec01-current-governance-authority-evidence.md`
- Benchmark: `docs/plans/2026-08-26-p2p-govrec01-current-governance-authority/2026-08-26-p2p-govrec01-current-governance-authority-benchmark.md`
- Actual status: `docs/plans/2026-08-26-p2p-govrec01-current-governance-authority/2026-08-26-p2p-govrec01-current-governance-authority-actual-status.md`

## Evidence Rules

This ledger records exact source inspection, commands, classifications, implementation deltas, validation output, and final identity. It does not treat a log line, cached profile, configured quorum, or historical report as fresh live proof. Evidence IDs are stable and are referenced from the plan, actual-status, benchmark, coder report, and Supervisor report.

## E0 - P0 Evidence

Matching plan item(s): `P0-A`

- `E0-P0A-AUTH1`: Canonical checkout `D:\AI\P2P_dev\P2P-canonical-runtime-01` is clean on `main...origin/main` at `2a71410afd1b29651016ef57a5d2da38938c3f68`, tree `3e6ab12ff78a72c4a3ea2a418e11167a8649aaad`, parent/base `af02170ac7ba180900ca78beb26a2972d80c73b6`.
- `E0-P0A-AUTH2`: Candidate worktree `D:\AI\P2P_dev\P2P-upgrade-github\.tmp\p2p-govrec01-current-authority` was created clean from exact `2a71410…` on branch `codex/p2p-govrec01-current-authority`.
- `E0-P0A-AUTH3`: `governance/development-control.json` currently preserves official `.19` artifact SHA-256 `3a9ee51321e1f5e40e35ce73eb90727cddb571a672aa095d16d76af2feb03dd8`, `PROMOTED_VERIFIED`, approval `P2P-APR-20260815T013545Z-0068b3047f`, and an active unpromoted `.74` successor.
- `E0-P0A-DRIFT1`: Direct `python -X utf8 scripts/p2p_governance.py drift` fails with six unlocked runtime additions and protected-path changes; the runtime lock has 1,172 files while the current manifest has 1,178.
- `E0-P0A-DRIFT2`: Exact current manifest delta is six additions and eleven changed protected files; virtual hashes are equal.
- `E0-P0A-DRIFT3`: Six additions and the eleven changed paths exist in the supplied promoted main history and are not unexplained by filename alone; they require explicit path classification before lock regeneration.
- `E0-P0A-DOCTOR1`: `python -X utf8 scripts/doctor.py --root . --role development --json` returns exit 1; source/skill/foundation/decision-trace checks pass, governance-drift fails, and a Windows `UnicodeDecodeError` appears in the subprocess reader thread before the JSON report.
- `E0-P0A-TEST1`: `tests/test_p2p_governance_drift.py` is stale against the current policy: it expects 10 scoped paths and 35 references, while the current policy contains 38 scoped entries and the direct baseline observes 38 findings before classification.
- `E0-P0A-GRAPH1`: Anvien was refreshed with `anvien analyze --force`; candidate graph is current at `2a71410…`, 936 files scanned, 168 parsed code files, 0 parse failures, 39,123 nodes and 45,238 relationships.
- `E0-P0A-GRAPH2`: `anvien file-detail scripts/doctor.py --repo <candidate> --json` reports parsed/high-risk, 109 symbols, 3 inbound references, 78 local relationships, 14 linked flows, and `changedSinceAnalyze=false`.
- `E0-P0A-IMPACT1`: `anvien impact symbol check_governance --repo <candidate> --direction upstream --json` identifies the helper boundary and its `main`/doctor flow consumers; the change must remain localized.
- `E0-P0A-IMPACT2`: `anvien file-detail tests/test_p2p_governance_drift.py --repo <candidate> --json` reports 9 symbols, 2 outbound relationships, and a direct dependency on `p2p_governance.scan_volatile`.
- `E0-P0A-SCOPE1`: No UI, database, Docker, browser, provider, Manus, Council, remote write, promotion, release, deployment, or root Git-admin action was performed.
- P0 decision: `P0 complete; next phase status and work steps must be updated before implementation`.

## E1 - P1 Evidence

Matching plan item(s): `P1-A`, `P1-B`

- `E1-P1A-AUTH1`: Added `authority.current_promoted_source` to the existing development-control projection with exact `origin/main` ref, commit `2a71410afd1b29651016ef57a5d2da38938c3f68`, tree `3e6ab12ff78a72c4a3ea2a418e11167a8649aaad`, parent/base `af02170ac7ba180900ca78beb26a2972d80c73b6`, and explicit non-release scope.
- `E1-P1A-AUTH2`: JSON parse/assertion confirms the new current source projection, unchanged official `.19` artifact SHA/promotion status, and unchanged `.74` `ACTIVE_UNPROMOTED` status.
- `E1-P1A-AUTH3`: `py -3 -X utf8 scripts/p2p_development_control.py validate` returns `PASS` on the candidate.
- `E1-P1A-AUTH4`: `py -3 -X utf8 scripts/p2p_development_control.py status` returns `P2P DEVELOPMENT STATUS: PASS` and retains canonical capability set `8/8`.
- `E1-P1A-AUTH5`: No `VERSION`, artifact, approval, promotion, release, or remote authority file was changed by P1-A.
- `E1-P1A-AUTH6`: Existing `tests.test_p2p_development_control` ran 21 tests with 15 passing, 2 skipped, and 2 fixture errors because `make_reconcilable_root()` does not normalize the current `.74` source version; this inherited test-fixture defect is assigned to P3-B and is not evidence against the authority projection.
- `E1-P1A-AUTH7`: `git diff` is limited to the new authority projection plus planner artifacts; no provider, Manus, Council, or remote process was invoked.
- `E1-P1B-DRIFT1..E1-P1B-DRIFT17`: Pending P1-B path-by-path classification.
- `E1-P1B-LOCK1..E1-P1B-LOCK4`: To be filled after deterministic lock regeneration, direct drift, lock identity negative test, and diff check.

## E2 - P2 Evidence

Matching plan item(s): `P2-A`, `P2-B`

- `E2-P2A-COUNCIL1..E2-P2A-COUNCIL8`: To be filled with canonical historical/current Council wording and C36/C43 negative evidence.
- `E2-P2B-EDGE1..E2-P2B-EDGE5`: To be filled with edge-case index path, family completeness, and UNKNOWN live slots.

## E3 - P3 Evidence

Matching plan item(s): `P3-A`, `P3-B`

- `E3-P3A-DECODER1..E3-P3A-DECODER7`: To be filled with explicit UTF-8 child environment, strict byte decode implementation, valid-output behavior, malformed-output failure, and doctor reproduction.
- `E3-P3B-TEST1..E3-P3B-TEST8`: To be filled with governance negative tests, refreshed current-policy counts, focused suites, and regression comparison.

## E4 - P4 Evidence

Matching plan item(s): `P4-A`, `P4-B`

- `E4-P4A-GATE1..E4-P4A-GATE12`: To be filled with compileall, drift, doctor, Vendor, Host Projection, Manus package, Foundation, C35, C43, capability, and regression receipts.
- `E4-P4A-CLOSE1..E4-P4A-CLOSE5`: To be filled with Anvien detect-changes, diff check, final status, exact commit/tree/base, and no-provider/Council boundary.
- `E4-P4B-SUP1..E4-P4B-SUP6`: To be filled with the fresh exact-head Supervisor review; the report must name the exact reviewed commit and tree and contain one PASS or REJECT verdict.

## Closure Evidence

Pending implementation and validation. No release/promotion/remote mutation evidence is permitted in this plan.
