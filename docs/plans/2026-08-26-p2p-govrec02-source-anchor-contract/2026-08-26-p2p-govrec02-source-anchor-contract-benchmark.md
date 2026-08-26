# P2P-GOVREC02 Governance Source Anchor Contract Correction Benchmark Ledger

## Metadata

- Date: `2026-08-26`
- Plan: `docs/plans/2026-08-26-p2p-govrec02-source-anchor-contract/2026-08-26-p2p-govrec02-source-anchor-contract-plan.md`
- Evidence: `docs/plans/2026-08-26-p2p-govrec02-source-anchor-contract/2026-08-26-p2p-govrec02-source-anchor-contract-evidence.md`
- Benchmark: `docs/plans/2026-08-26-p2p-govrec02-source-anchor-contract/2026-08-26-p2p-govrec02-source-anchor-contract-benchmark.md`
- Actual status: `docs/plans/2026-08-26-p2p-govrec02-source-anchor-contract/2026-08-26-p2p-govrec02-source-anchor-contract-actual-status.md`

## Benchmark Rules

This task is a governance contract and validator correction. Record measured graph/inventory counts and validation matrix counts; do not treat command duration or green output alone as a product-performance benchmark.

## B0 - P0 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P0 | Anvien files scanned | files | 946 | 946 | 946 | current graph | 0 | E0-P0A-GRAPH1 |
| P0 | Anvien parsed code files | files | 169 | 169 | 169 | current graph | 0 | E0-P0A-GRAPH1 |
| P0 | Anvien graph nodes | nodes | 39,380 | 39,380 | 39,380 | current graph | 0 | E0-P0A-GRAPH1 |
| P0 | Anvien graph relationships | relationships | 45,526 | 45,526 | 45,526 | current graph | 0 | E0-P0A-GRAPH1 |
| P0 | `validate_control` impacted symbols | symbols | 9 | 9 | pending | reviewed before edit | 0 | E0-P0A-GRAPH3 |

## B1 - P1 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P1 | Anchor semantic fields present | fields | 0 | 8 | pending | 8 | +8 | E1-P1A-CONTRACT1 |
| P1 | Static fail-closed authority reason-code classes | classes | 0 | 5 | pending | 5 | +5 | E1-P1A-CONTRACT2 |
| P1 | Anchor relationship classes covered | classes | 0 | pending | pending | 3 | pending | E1-P1B-GIT1 |
| P1 | Fail-closed authority reason-code classes | classes | 0 | pending | pending | 7 | pending | E1-P1A-CONTRACT2 / E1-P1B-GIT2 |

## B2 - P2 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P2 | Positive/negative anchor simulation cases | cases | 0 | pending | pending | 4 | pending | E2-P2A-TEST2 |
| P2 | Regression suite count | tests | 0 | pending | pending | required matrix | pending | E2-P2A-TEST1 |

## Non-Benchmarkable Notes

- No UI, database, browser, Docker, provider, Manus, Council, release, or deployment surface is in scope.
- Compile/test timings are validation evidence, not performance claims.
