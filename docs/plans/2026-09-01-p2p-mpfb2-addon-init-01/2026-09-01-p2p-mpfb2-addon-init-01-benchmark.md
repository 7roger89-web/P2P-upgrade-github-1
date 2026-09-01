# P2P MPFB2 Addon Init 01 Benchmark Ledger

## Metadata

- Date: `2026-09-01`
- Plan: `docs/plans/2026-09-01-p2p-mpfb2-addon-init-01/2026-09-01-p2p-mpfb2-addon-init-01-plan.md`
- Evidence: `docs/plans/2026-09-01-p2p-mpfb2-addon-init-01/2026-09-01-p2p-mpfb2-addon-init-01-evidence.md`
- Benchmark: `docs/plans/2026-09-01-p2p-mpfb2-addon-init-01/2026-09-01-p2p-mpfb2-addon-init-01-benchmark.md`
- Actual status: `docs/plans/2026-09-01-p2p-mpfb2-addon-init-01/2026-09-01-p2p-mpfb2-addon-init-01-actual-status.md`

## Benchmark Rules

Record measured counts/sizes/hashes only. No performance campaign is
authorized; pass/fail narrative belongs in evidence.

## B0 - P0 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P0 | Anvien scanned files | files | 0 | 1109 | 1109 | fresh graph | +1109 | E0-P0A-GRAPH1 |
| P0 | Anvien parsed code files | files | 0 | 199 | 199 | 0 failures | +199 | E0-P0A-GRAPH1 |
| P0 | Anvien parse failures | files | 0 | 0 | 0 | 0 | 0 | E0-P0A-GRAPH1 |
| P0 | MPFB archive entries matched | files | 0 | 2810/2810 | 2810/2810 | exact | 2810 | E0-P0A-MPFB1 |
| P0 | Generated MPFB cache extras | files | 5 | 0 | pending | 0 before smoke | -5 | E1-P1B-CACHE1 |

## B1 - P1 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P1 | Real addon identities observed | identities | 0 | 1 | pending | one exact key | +1 | E1-P1A-RUNTIME2 |
| P1 | Canonical production files changed | files | 0 | 1 | pending | minimum | +1 | E1-P1B-SRC1 |
| P1 | Focused checks run | cases | 0 | pending | pending | affected only | pending | E1-P1B-TEST1 |

## B2 - P2 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|----------|-------|----------|
| P2 | Blender child processes spawned | processes | 0 | pending | pending | one | pending | E2-P2B-RUN1 |
| P2 | Character output files | files | 0 | pending | pending | two | pending | E2-P2B-ARTIFACT1..2 |
| P2 | GLB size | bytes | 0 | pending | pending | one measured file | pending | E2-P2B-ARTIFACT1 |
| P2 | GLB SHA-256 | digest | N/A | pending | pending | provenance-bound | pending | E2-P2B-ARTIFACT1..2 |
| P2 | Firewall rules after cleanup | rules | 0 | pending | pending | 0 | pending | E2-P2B-CLEAN1 |

## Non-Benchmarkable Notes

No performance, capacity, visual, browser, Docker, or broad-regression
benchmark is in scope.

