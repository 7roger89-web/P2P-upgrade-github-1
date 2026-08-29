# P2P Reasoning/Execution Fresh Current-Canonical Reconciliation Benchmark Ledger

## Metadata

- Date: `2026-08-29`
- Plan: `docs/plans/2026-08-29-p2p-reasoning-execution-fresh-current-canonical-reconciliation/2026-08-29-p2p-reasoning-execution-fresh-current-canonical-reconciliation-plan.md`
- Evidence: `docs/plans/2026-08-29-p2p-reasoning-execution-fresh-current-canonical-reconciliation/2026-08-29-p2p-reasoning-execution-fresh-current-canonical-reconciliation-evidence.md`
- Benchmark: `docs/plans/2026-08-29-p2p-reasoning-execution-fresh-current-canonical-reconciliation/2026-08-29-p2p-reasoning-execution-fresh-current-canonical-reconciliation-benchmark.md`
- Actual status: `docs/plans/2026-08-29-p2p-reasoning-execution-fresh-current-canonical-reconciliation/2026-08-29-p2p-reasoning-execution-fresh-current-canonical-reconciliation-actual-status.md`

## Benchmark Rules

This ledger records measured path inventories, focused test counts, and affected
module counts. It does not turn technical PASS into promotion authority. No
broad regression benchmark is run.

## B0 - P0 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P0 | old-base-to-old-candidate changed paths | paths | 18 | 18 | 18 | 18 | 0 | E0-P0A-OVERLAP1 |
| P0 | old-base-to-current-main changed paths | paths | 9 | 9 | 9 | 9 | 0 | E0-P0A-OVERLAP1 |
| P0 | exact shared paths | paths | 0 | 0 | 0 | 0 | 0 | E0-P0A-OVERLAP1 |
| P0 | production/test shared paths | paths | 0 | 0 | 0 | 0 | 0 | E0-P0A-OVERLAP2 |
| P0 | later canonical 01D changed paths | paths | 9 | 9 | 9 | 9 preserved | 0 | E0-P0A-LATE1 |

## B1 - P1 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P1 | reviewed source/test delta paths | paths | 11 | pending | pending | 11 | pending | E1-P1A-SRC1 |
| P1 | direct Reasoning/Execution tests | tests | 17 | pending | pending | 17 pass | pending | E1-P1A-TEST1 |
| P1 | directly affected preservation tests passed | tests | 94 | pending | pending | no new failure | pending | E1-P1B-TEST1 |
| P1 | directly affected preservation tests skipped | tests | 14 | pending | pending | environment-only | pending | E1-P1B-TEST1 |
| P1 | affected modules compiled | files | 11 | pending | pending | all pass | pending | E1-P1B-COMPILE1 |

## B2 - P2 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P2 | independent Supervisor reviews | reviews | 0 | pending | pending | 1 | pending | E2-P2A-SUPERVISOR1 |

## Non-Benchmarkable Notes

- Browser, database, provider, remote-push, Council, MCP, Anvien, and broad
  regression execution are intentionally outside this lane.
- Candidate SHA/tree and ancestry are identity evidence, not performance
  metrics.
