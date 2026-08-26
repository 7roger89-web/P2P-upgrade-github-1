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
| P2 | candidate commits | commits | 0 | 3 | pending | 1 or more | pending | E2-P2B-COMMIT1 |

## Non-Benchmarkable Notes

- No browser, Docker, live-provider, quorum, network, or host-performance benchmark applies.
- Broad line-ending-only worktree status is not a CT01 metric and must not enter the candidate diff.
