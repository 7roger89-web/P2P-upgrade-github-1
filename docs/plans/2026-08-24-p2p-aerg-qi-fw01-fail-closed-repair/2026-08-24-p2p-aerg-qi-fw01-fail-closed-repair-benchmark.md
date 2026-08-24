# P2P AERG QI/FW01 Fail-Closed Repair Benchmark Ledger

## Metadata

- Date: `2026-08-24`
- Plan: `docs/plans/2026-08-24-p2p-aerg-qi-fw01-fail-closed-repair/2026-08-24-p2p-aerg-qi-fw01-fail-closed-repair-plan.md`
- Evidence: `docs/plans/2026-08-24-p2p-aerg-qi-fw01-fail-closed-repair/2026-08-24-p2p-aerg-qi-fw01-fail-closed-repair-evidence.md`
- Benchmark: `docs/plans/2026-08-24-p2p-aerg-qi-fw01-fail-closed-repair/2026-08-24-p2p-aerg-qi-fw01-fail-closed-repair-benchmark.md`
- Actual status: `docs/plans/2026-08-24-p2p-aerg-qi-fw01-fail-closed-repair/2026-08-24-p2p-aerg-qi-fw01-fail-closed-repair-actual-status.md`

## Benchmark Rules

- Record measured counts and exit codes only; narrative belongs in evidence.
- Do not treat prior report counts as current measurements.
- The validator target is preservation of exactly seven inherited failures, not whole-framework PASS.
- No performance claim is required; test counts, graph inventory, hashes, and validator counts are the relevant measurements.

## B0 - P0 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P0 | Anvien scanned files | files | n/a | 907 | 907 | source refreshed | 0 | E0-P0A-GRAPH1 |
| P0 | Anvien parsed code | files | n/a | 164 | 164 | failures=0 | 0 | E0-P0A-GRAPH1 |
| P0 | Anvien graph | nodes/relationships | n/a | 37559/43374 | 37628/43443 | recorded | n/a | E0-P0A-GRAPH1 |

## B1 - P1 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P1 | QI matrix cases | cases | 0 stored | 16 status/control cases + 4 actual-AERG mappings | 16 + 4 | all required statuses covered; optional distinction preserved | complete | E1-P1A-TEST1, E1-P1B-TEST1 |
| P1 | QI focused result | tests / skipped / exit | 44 / 1 / 0 prior | 44 / 1 / 0 | 44 / 1 / 0 | no new failures | 0 | E1-P1B-TEST1 |
| P1 | Freshness subset | tests / exit | 5 / 0 prior | 5 / 0 | 5 / 0 | stale/expired fail closed | 0 | E3-P3A-TEST1 |
| P1 | Independent A-Z reconstruction | cases / exit | 26 + 2 prior claim | 26/26 + 2/2 | 26/26 + 2/2 | semantic coverage, not count-only | complete | E3-P3A-TEST1 |

## B2 - P2 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P2 | FW01 compatibility matrix | cases | 0 stored | 7 unsafe/fresh shape checks | 7 | fresh allow; unsafe block | complete | E2-P2A-TEST1 |
| P2 | FW01 boundary result | tests / exit | 0 stored | 8 / 0 | 8 / 0 | actual AERG mapping and compatibility clamp green | complete | E2-P2B-TEST1 |
| P2 | FW01 focused result | tests / exit | 6 / 0 prior | 6 / 0 | 6 / 0 | no new failures | 0 | E2-P2B-TEST1 |

## B3 - P3 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P3 | Full capability suite | tests / skipped / exit | 352 / 6 / 0 prior | 360 / 6 / 0 | 360 / 6 / 0 | NEW_TEST_FAILURES=0 | 0 failures | E3-P3A-TEST1 |
| P3 | C43/RF01 suites | tests / exit | 18 / 0 prior | 18 / 0 | 18 / 0 | no new failures | 0 | E3-P3A-TEST1 |
| P3 | Compile boundary | exit | 0 prior | 0 | 0 | PASS | 0 | E3-P3A-TEST1 |
| P3 | Framework validator | passed / total / exit | 52 / 59 / 1 prior | 52 / 59 / 1 | 52 / 59 / 1 | exactly 7 inherited failures | 0 new classes | E3-P3A-TEST1 |
| P3 | Production repair files | files | 0 | 2 | 2 | exactly 2 | complete | E3-P3A-PROOF1 |

## Non-Benchmarkable Notes

- No UI, browser, Docker, network, database, release, promotion, or deployment benchmark applies to this narrow Python capability-boundary repair.
