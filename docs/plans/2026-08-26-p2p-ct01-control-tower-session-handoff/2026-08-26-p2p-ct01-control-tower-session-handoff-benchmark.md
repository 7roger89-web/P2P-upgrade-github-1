# P2P-CT01 Durable Control Tower Session Handoff Benchmark Ledger

## Metadata

- Date: 2026-08-26
- Plan: docs/plans/2026-08-26-p2p-ct01-control-tower-session-handoff/2026-08-26-p2p-ct01-control-tower-session-handoff-plan.md
- Evidence: docs/plans/2026-08-26-p2p-ct01-control-tower-session-handoff/2026-08-26-p2p-ct01-control-tower-session-handoff-evidence.md
- Benchmark: docs/plans/2026-08-26-p2p-ct01-control-tower-session-handoff/2026-08-26-p2p-ct01-control-tower-session-handoff-benchmark.md
- Actual status: docs/plans/2026-08-26-p2p-ct01-control-tower-session-handoff/2026-08-26-p2p-ct01-control-tower-session-handoff-actual-status.md

## Benchmark Rules

This is a Python protocol/documentation change. Record inventory and directly measured counts only; validation pass/fail belongs in evidence.

## B0 - P0 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|---|---|---|---:|---:|---:|---:|---:|---|
| P0 | CT01 protocol modules | files | 0 | 0 | 0 | 1 | 0 | E0-P0A-ARCH2 |
| P0 | CT01 focused test files | files | 0 | 0 | 0 | 1 | 0 | E0-P0A-ARCH2 |
| P0 | canonical base relation | exact SHA/tree | expected | matched | matched | matched | 0 | E0-P0A-SRC2 |

## B1 - P1 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|---|---|---|---:|---:|---:|---:|---:|---|
| P1 | protocol modules | files | 0 | 1 | 1 | 1 | +1 | E1-P1A-SRC1 |
| P1 | protocol regression tests | cases | 0 | 15 | 15 | 15 | +15 | E1-P1B-TEST1..E1-P1B-TEST15 |
| P1 | required A-H scenarios | cases | 0 | 8 | 8 | 8 | +8 | E1-P1B-TEST1..E1-P1B-TEST8 |
| P1 | negative/round-trip scenarios | cases | 0 | 6 | 6 | 3 | +6 | E1-P1B-TEST9..E1-P1B-TEST14 |

## B2 - P2 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|---|---|---|---:|---:|---:|---:|---:|---|
| P2 | durable CT01 guides | files | 0 | 1 | 1 | 1 | +1 | E2-P2A-DOC1 |
| P2 | capability ledger records | records | 175 | 176 | 176 | 176 | +1 | E2-P2A-LEDGER1 |
| P2 | projected MULTI-AI records | records | 31 | 32 | 32 | 32 | +1 | E2-P2A-ROADMAP1 |
| P2 | candidate commits | commits | 0 | 4 | 4 | 1 or more | +4 | E2-P2B-COMMIT1 |

## Non-Benchmarkable Notes

- No browser, Docker, live-provider, quorum, network, or host-performance benchmark applies.
- Broad line-ending-only worktree status is not a CT01 metric and must not enter the candidate diff.

## B3 - Owner Scope Addendum Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|---|---|---|---:|---:|---:|---:|---:|---|
| A1 | attachment-aware regression cases | cases | 0 | 7 | 7 | 7 | +7 | E3-P2A-TEST1 |
| A1 | total focused protocol regression cases | cases | 15 | 22 | 22 | 22 | +7 | E3-P2A-TEST1 |
| A1 | handoff artifacts selected as REQUIRED | files | 0 | 1 | 1 | 1 | +1 | E3-P2A-ARTIFACT1 |
| A1 | attachment classifications covered | classes | 0 | 3 | 3 | 3 | +3 | E3-P2A-TEST1 |
| A1 | attachment manifest schema | schema versions | 0 | 1 | 1 | 1 | +1 | E3-P2A-IMPL1 |

The addendum changes protocol/documentation inventory only. It does not create a live, network, host-performance, promotion, release, or deployment benchmark.

## B4 - Owner Scope Addendum Benchmarks — Rotatable Control Tower

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|---|---|---|---:|---:|---:|---:|---:|---|
| A2 | successor/rotation protocol classes | classes | 0 | 3 | 3 | 3 | +3 | E4-A2-IMPL1 |
| A2 | successor/rotation schema versions | schemas | 0 | 2 | 2 | 2 | +2 | E4-A2-IMPL1 |
| A2 | total focused protocol regression cases | cases | 22 | 28 | 28 | 28 | +6 | E4-A2-TEST1 |
| A2 | ROTATION A-F regression cases | cases | 0 | 6 | 6 | 6 | +6 | E4-A2-TEST1 |
| A2 | exact beginner rotation chat names emitted | names | 0 | 2 | 2 | 2 | +2 | E4-A2-TEST1 |

The rotatable addendum changes protocol/documentation inventory only. No benchmark result is a live-host, provider, quorum, promotion, release, deployment, or performance claim.

## B5 - P2P-CT01-R03 Governance Lock Reconciliation Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|---|---|---|---:|---:|---:|---:|---:|---|
| R03 | package protected runtime files | files | 1178 | 1180 | 1180 | existing manifest + intended protected docs | +2 | E5-P3C-LOCK1 |
| R03 | candidate-specific governance drift failures | failure groups | 2 | 0 | 0 | 0 | -2 | E5-P3D-NEGATIVE1, E5-P3E-DOCTOR1 |
| R03 | negative unexpected protected mutations proven | cases | 0 | 1 | 1 | 1 | +1 | E5-P3D-NEGATIVE1 |
| R03 | focused CT01 protocol regression cases | cases | 28 | 28 | 28 | 28 | 0 | E5-P3E-TEST1 |

The lock count delta is an inventory result: one intended durable guide and one dated
execution log are now represented by the existing package `docs` protection; charter,
ledger, and roadmap entries are hash refreshes. This is not a performance, live-host,
provider, quorum, promotion, release, deployment, or canonical-authority benchmark.
