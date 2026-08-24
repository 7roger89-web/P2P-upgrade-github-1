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
| P0 | Anvien scanned files | files | n/a | 901 | pending | source refreshed | pending | E0-P0A-GRAPH1 |
| P0 | Anvien parsed code | files | n/a | 164 | pending | failures=0 | pending | E0-P0A-GRAPH1 |
| P0 | Anvien graph | nodes/relationships | n/a | 37559/43374 | pending | recorded | pending | E0-P0A-GRAPH1 |

## B1 - P1 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P1 | QI matrix cases | cases | pending | pending | pending | all required statuses covered | pending | E1-P1A-TEST1 |
| P1 | QI focused result | tests / exit | 44 / 0 prior | pending | pending | no new failures | pending | E1-P1B-TEST1 |

## B2 - P2 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P2 | FW01 compatibility matrix | cases | 0 stored | pending | pending | fresh allow; unsafe block | pending | E2-P2A-TEST1 |
| P2 | FW01 focused result | tests / exit | 6 / 0 prior | pending | pending | no new failures | pending | E2-P2B-TEST1 |

## B3 - P3 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P3 | Full capability suite | tests / skipped / exit | 352 / 6 / 0 prior | pending | pending | NEW_TEST_FAILURES=0 | pending | E3-P3A-TEST1 |
| P3 | Framework validator | passed / total | 52 / 59 prior | pending | pending | exactly 7 inherited failures | pending | E3-P3A-TEST1 |
| P3 | Production repair files | files | 0 | pending | pending | exactly 2 | pending | E3-P3A-PROOF1 |

## Non-Benchmarkable Notes

- No UI, browser, Docker, network, database, release, promotion, or deployment benchmark applies to this narrow Python capability-boundary repair.
