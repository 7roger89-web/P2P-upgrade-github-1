# P2P-PB01 Current Canonical Reconciliation and Installed Contract Fix Benchmark Ledger

## Metadata

- Date: `2026-08-29`
- Plan: `docs/plans/2026-08-29-p2p-pb01-current-reconciled-installed-contract/2026-08-29-p2p-pb01-current-reconciled-installed-contract-plan.md`
- Evidence: `docs/plans/2026-08-29-p2p-pb01-current-reconciled-installed-contract/2026-08-29-p2p-pb01-current-reconciled-installed-contract-evidence.md`
- Benchmark: `docs/plans/2026-08-29-p2p-pb01-current-reconciled-installed-contract/2026-08-29-p2p-pb01-current-reconciled-installed-contract-benchmark.md`
- Actual status: `docs/plans/2026-08-29-p2p-pb01-current-reconciled-installed-contract/2026-08-29-p2p-pb01-current-reconciled-installed-contract-actual-status.md`

## Benchmark Rules

Record measured counts, sizes, hashes, and timings only. Pass/fail narrative is
kept in `evidence.md`. No benchmark regeneration or broad inventory is in scope.

## B0 - P0 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P0 | Current official main SHA | git | `6cc7555246905fce7b2fec1d4e48f5e46bfaf57e` | same | pending | exact fresh base | 0 | E0-P0A-AUTH1 |
| P0 | Current official main tree | git | `b308b9cf075aaeaef581a022202dcc428689b2ad` | same | pending | exact fresh base | 0 | E0-P0A-CLONE1 |
| P0 | PB01/current-main overlapping paths | paths | 0 | 0 | pending | 0 | 0 | E0-P0A-OVERLAP1 |

## B1 - P1 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P1 | Installed required launcher entries | entries | 0 | 1 | pending | 1 | +1 | E1-P1B-FIX1 |
| P1 | Current 02A paths overwritten | paths | 0 | 0 | pending | 0 | 0 | E1-P1A-02A1 |

## B2 - P2 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P2 | Focused PB01/contract tests | cases | 0 | 16 passed | pending | all focused cases | +16 passed | E2-P2A-INSTALL1 |
| P2 | Focused PB01/contract duration | seconds | N/A | 61.627 | pending | N/A | measured | E2-P2A-INSTALL1 |
| P2 | New candidate SHA | git | current base | pending | pending | exact candidate | pending | E2-P2A-ID1 |
| P2 | New candidate tree | git | current base tree | pending | pending | exact candidate | pending | E2-P2A-ID1 |

## Non-Benchmarkable Notes

- No UI, Docker, database, external provider, deployment, or live runtime is in
  scope.
- Broad regression counts, Anvien inventory, and benchmark regeneration are not
  run under the explicit verification ceiling.
