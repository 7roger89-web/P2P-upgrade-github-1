# P2P img2threejs executable projection Benchmark Ledger

## Metadata

- Date: `2026-08-29`
- Plan: `docs/plans/2026-08-29-p2p-img2threejs-exec-01/plan.md`
- Evidence: `docs/plans/2026-08-29-p2p-img2threejs-exec-01/evidence.md`
- Benchmark: `docs/plans/2026-08-29-p2p-img2threejs-exec-01/benchmark.md`
- Actual status: `docs/plans/2026-08-29-p2p-img2threejs-exec-01/actual-status.md`

## Benchmark Rules

Only measured counts, sizes, hashes, and timings belong here. Pass/fail narrative
belongs in `evidence.md`.

## B0 - P0 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P0 | P2P graph files scanned | files | 1042 | 1042 | 1042 | 1042 | 0 | E0-P0A-GRAPH1 |
| P0 | P2P graph relationships | edges | 52841 | 52841 | 52841 | record only | 0 | E0-P0A-GRAPH1 |
| P0 | current capability registry | entries | 39 | 39 | 39 | preserve until P1-B | 0 | E0-P0A-SRC3 |
| P0 | canonical quorum denominator | identities | 8 | 8 | 8 | 8 | 0 | E0-P0A-SRC3 |

## B1 - P1 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P1 | capability registry entries | entries | 39 | 40 | 40 | 40 after one noncanonical addition | +1 | E1-P1B-REG1 |
| P1 | allowed upstream entrypoints | entrypoints | 0 | 5 | 5 | 5 exact paths | +5 | E1-P1A-SEC2 |
| P1 | full upstream tree copied into P2P | files | 0 | 0 | 0 | 0 | 0 | E1-P1B-PROJ1 |
| P1 | network-enabled adapter routes | routes | 0 | 0 | 0 | 0 | 0 | E1-P1A-SEC3 |

## B2 - P2 Benchmarks

No P2 phase is planned for this strict lane.

## Non-Benchmarkable Notes

Browser visual quality, screenshot durability, and future Thiên Hạ project runtime
are intentionally not benchmarked here because no target project or UI runtime is
in scope.
