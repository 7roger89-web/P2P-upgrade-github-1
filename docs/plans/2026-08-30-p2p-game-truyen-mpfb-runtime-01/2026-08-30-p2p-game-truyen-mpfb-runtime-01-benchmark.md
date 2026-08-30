# P2P Game Truyen MPFB Runtime 01 Benchmark Ledger

## Metadata

- Date: `2026-08-30`
- Plan: `docs/plans/2026-08-30-p2p-game-truyen-mpfb-runtime-01/2026-08-30-p2p-game-truyen-mpfb-runtime-01-plan.md`
- Evidence: `docs/plans/2026-08-30-p2p-game-truyen-mpfb-runtime-01/2026-08-30-p2p-game-truyen-mpfb-runtime-01-evidence.md`
- Benchmark: `docs/plans/2026-08-30-p2p-game-truyen-mpfb-runtime-01/2026-08-30-p2p-game-truyen-mpfb-runtime-01-benchmark.md`
- Actual status: `docs/plans/2026-08-30-p2p-game-truyen-mpfb-runtime-01/2026-08-30-p2p-game-truyen-mpfb-runtime-01-actual-status.md`

## Benchmark Rules

Record measurements only. Test pass/fail and design rationale belong in the
evidence ledger. Blender/MPFB runtime measurements are intentionally absent.

## B0 - P0 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P0 | Anvien scanned files | files | 1,074 | 1,079 | 1,079 | known baseline plus workstream artifacts | +5 | E2-P2A-CHANGE1 |
| P0 | Anvien parsed code files | files | 191 | 191 | 191 | 191 | 0 | E2-P2A-CHANGE1 |
| P0 | Anvien parse failures | files | 0 | 0 | 0 | 0 | 0 | E2-P2A-CHANGE1 |
| P0 | MPFB source commit | SHA | 80919fa... | 80919fa... | 80919fa... | exact pin | 0 | E0-P0A-MPFB1 |

## B1 - P1 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P1 | Focused test cases | cases | 19 | 30 | 30 | all requested focused cases | +11 | E2-P2A-TEST1 |
| P1 | Dedicated entrypoint files | files | 0 | 1 | 1 | 1 | +1 | E1-P1A-SRC1 |
| P1 | Network isolation mechanisms | mechanisms | 0 enforced | 1 implemented | 1 implemented | 1 exact-path Windows mechanism | +1 implementation | E1-P1B-TEST1..TEST4 |

## B2 - P2 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P2 | Candidate subject SHA/tree | pair | base `31647b2f...` / `c2154652...` | frozen after commit | frozen after commit | one exact frozen pair | implementation delta | E2-P2A-FREEZE1 |
| P2 | Blender processes spawned | processes | 0 | 0 | 0 | 0 | 0 | user stop contract |
| P2 | GLBs created | files | 0 | 0 | 0 | 0 | 0 | user stop contract |

## Non-Benchmarkable Notes

Actual Blender/MPFB execution, network denial live proof, GLB creation, and
visual proof are explicitly not run in this workstream.
