# P2P-BG01 Current-Canonical Reconciliation Benchmark Ledger

## Metadata

- Date: 2026-08-28
- Plan: docs/plans/2026-08-28-p2p-bg01-current-canonical-reconciliation/2026-08-28-p2p-bg01-current-canonical-reconciliation-plan.md
- Evidence: docs/plans/2026-08-28-p2p-bg01-current-canonical-reconciliation/2026-08-28-p2p-bg01-current-canonical-reconciliation-evidence.md
- Benchmark: docs/plans/2026-08-28-p2p-bg01-current-canonical-reconciliation/2026-08-28-p2p-bg01-current-canonical-reconciliation-benchmark.md
- Actual status: docs/plans/2026-08-28-p2p-bg01-current-canonical-reconciliation/2026-08-28-p2p-bg01-current-canonical-reconciliation-actual-status.md

## Benchmark Rules

Record only measured identity, file, test, and scope counts. Pass/fail narratives belong in evidence.

## B0 - P0 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|---|---|---:|---:|---:|---:|---:|---:|---|
| P0 | Current canonical HEAD | SHA | 34ece1d1 | 34ece1d1 | 34ece1d1 | exact | 0 | E0-P0A-ID1 |
| P0 | Current canonical tree | SHA | b3f541df | b3f541df | b3f541df | exact | 0 | E0-P0A-ID1 |
| P0 | Current source-worktree status | lines | 0 | 0 | 0 | 0 | 0 | E0-P0A-ID1 |
| P0 | Old candidate status | lines | 1133 | 1133 | 1133 | evidence-only | 0 | E0-P0A-ID3 |

## B1 - P1 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|---|---|---:|---:|---:|---:|---:|---:|---|
| P1 | BG01 focused tests | tests | 0 | 8 | 8 | all focused cases pass | +8 | E1-P1C-TEST1 |
| P1 | Direct workflow tests | tests | 0 | 7 | 7 | existing workflow suite passes | +7 | E1-P1C-TEST1 |
| P1 | Lightweight-fastpath tests | tests | 18 | 18 | 18 | existing suite passes | 0 | E1-P1C-TEST1 |
| P1 | EFF01 policy smoke tests | tests | 0 | 7 | 7 | relevant policy smoke passes | +7 | E1-P1C-TEST1 |
| P1 | Changed source files | files | 1 overlapping path | 3 | 3 | narrow allowlist | +2 | E1-P1B-DIFF1 |

## B2 - P2 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|---|---|---:|---:|---:|---:|---:|---:|---|
| P2 | Candidate identity | SHA/tree | current base | current base plus focused source | pending | exact new candidate | pending | closure evidence |

## Non-Benchmarkable Notes

No browser, Docker, provider, host, quorum, deployment, or live-runtime benchmark applies to this bounded Python gateway reconciliation. Anvien inventory is intentionally not collected under the user boundary.
