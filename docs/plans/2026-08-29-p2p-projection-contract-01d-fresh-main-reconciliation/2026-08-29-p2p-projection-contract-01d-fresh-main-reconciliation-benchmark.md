# P2P Projection Contract 01D Fresh-Main Reconciliation Benchmark Ledger

## Metadata

- Date: `2026-08-29`
- Plan: `docs/plans/2026-08-29-p2p-projection-contract-01d-fresh-main-reconciliation/2026-08-29-p2p-projection-contract-01d-fresh-main-reconciliation-plan.md`
- Evidence: `docs/plans/2026-08-29-p2p-projection-contract-01d-fresh-main-reconciliation/2026-08-29-p2p-projection-contract-01d-fresh-main-reconciliation-evidence.md`
- Benchmark: `docs/plans/2026-08-29-p2p-projection-contract-01d-fresh-main-reconciliation/2026-08-29-p2p-projection-contract-01d-fresh-main-reconciliation-benchmark.md`
- Actual status: `docs/plans/2026-08-29-p2p-projection-contract-01d-fresh-main-reconciliation/2026-08-29-p2p-projection-contract-01d-fresh-main-reconciliation-actual-status.md`

## Benchmark Rules

This task is primarily contract correctness, not product performance. Record
only counts, hashes, timings, and inventory measurements actually observed.
Build/test timing is validation evidence unless it is explicitly a target.

## B0 - P0 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P0 | Post-base canonical commits | commits | 0 | 3 | 3 | preserve all | 0 dropped | `E0-P0A-INT1..E0-P0A-INT3` |
| P0 | Fresh main object | SHA/tree | known base | `1c84bc4/a11a44b` | `1c84bc4/a11a44b` | direct fetch | exact | `E0-P0A-REMOTE2..E0-P0A-REMOTE3` |
| P0 | Anvien graph index | status | not run | unavailable | unavailable | PASS or explicit limitation | N/A | `E0-P0A-ANV1` |

## B1 - P1 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P1 | Projection focused tests | cases | 0 on fresh main | pending | pending | all required cases pass | pending | `E1-P1B-TEST1` |
| P1 | Projection implementation paths | paths | 0 new on fresh main | pending | pending | reviewed seam only | pending | `E1-P1A-SRC1..E1-P1B-SRC3` |

## B2 - P2 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P2 | Focused validation cases | cases | pending | pending | pending | all listed boundaries pass | pending | `E2-P2A-TEST1..E2-P2A-TEST9` |
| P2 | Candidate identity | SHA/tree | old 01C `b27dbe8/aa8255e` | pending | pending | new exact subject | pending | `E2-P2A-ID1..E2-P2A-ID3` |

## B3 - P3 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P3 | Remote push count | pushes | 0 | pending | pending | exactly 1 if all gates pass | pending | `E3-P3A-REMOTE4` |
| P3 | Post-promotion SHA/tree match | boolean | pending | pending | pending | YES | pending | `E3-P3A-REMOTE5..E3-P3A-REMOTE6` |

## Non-Benchmarkable Notes

- UI, browser, Docker, database, provider, secret, and runtime-installation
  metrics are not applicable to this offline Python contract task.
- Supervisor verdict, lineage, and cleanliness are acceptance evidence rather
  than performance benchmarks.
