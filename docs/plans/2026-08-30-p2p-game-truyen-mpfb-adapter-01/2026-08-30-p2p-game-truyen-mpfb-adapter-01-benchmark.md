# P2P Game Truyen MPFB Adapter 01 Benchmark Ledger

## Metadata

- Date: `2026-08-30`
- Plan: `docs/plans/2026-08-30-p2p-game-truyen-mpfb-adapter-01/2026-08-30-p2p-game-truyen-mpfb-adapter-01-plan.md`
- Evidence: `docs/plans/2026-08-30-p2p-game-truyen-mpfb-adapter-01/2026-08-30-p2p-game-truyen-mpfb-adapter-01-evidence.md`
- Benchmark: `docs/plans/2026-08-30-p2p-game-truyen-mpfb-adapter-01/2026-08-30-p2p-game-truyen-mpfb-adapter-01-benchmark.md`
- Actual status: `docs/plans/2026-08-30-p2p-game-truyen-mpfb-adapter-01/2026-08-30-p2p-game-truyen-mpfb-adapter-01-actual-status.md`

## Benchmark Rules

This lane has no product/runtime performance target. Only deterministic
inventory, hash, relationship, and focused-test counts are recorded here.
Build/test pass-fail belongs in the evidence ledger.

## B0 - P0 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P0 | Anvien parsed code files | files | 190 | 190 | 190 | no unexplained failure | 0 | E0-P0A-GRAPH1 |
| P0 | Existing focused catalog test local relationships | relationships | 10 | 10 | 10 | inspected before edit | 0 | E0-P0A-GRAPH1 |

## B1 - P1 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P1 | New implementation slices | slices | 0 | 3 | 3 | 3 | +3 | E1-P1A-TEST1, E1-P1B-TEST1, E1-P1C-TEST1 |
| P1 | Anvien parsed code files after implementation | files | 190 | 191 | 191 | no parse failure | +1 | E2-P2A-GRAPH1 |
| P1 | Focused tests across adapter and existing catalog | tests | 0 | 28 | 28 | all pass | +28 | E2-P2A-TEST1 |
| P1 | Real Blender/MPFB executions | processes | 0 | 0 | 0 | 0 | 0 | execution authority |

## B2 - P2 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P2 | New registry/router/projection systems | systems | 0 | 0 | 0 | 0 | 0 | E2-P2A-SRC1, E2-P2A-TEST1 |
| P2 | Game Truyen files changed | files | 0 | 0 | 0 | 0 | 0 | candidate diff |

## Non-Benchmarkable Notes

Visual quality, GLTFLoader/browser loading, actual forge execution, package
startup, and runtime performance are intentionally not benchmarked or claimed
in this adapter-certification lane.
