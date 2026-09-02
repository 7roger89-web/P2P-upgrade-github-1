# P2P-MPFB2-GLB-SKIN-VALIDATION-01 Benchmark Ledger

## Metadata

- Date: `2026-09-02`
- Plan: `docs/plans/2026-09-02-p2p-mpfb2-glb-skin-validation-01/2026-09-02-p2p-mpfb2-glb-skin-validation-01-plan.md`
- Evidence: `docs/plans/2026-09-02-p2p-mpfb2-glb-skin-validation-01/2026-09-02-p2p-mpfb2-glb-skin-validation-01-evidence.md`
- Benchmark: `docs/plans/2026-09-02-p2p-mpfb2-glb-skin-validation-01/2026-09-02-p2p-mpfb2-glb-skin-validation-01-benchmark.md`
- Actual status: `docs/plans/2026-09-02-p2p-mpfb2-glb-skin-validation-01/2026-09-02-p2p-mpfb2-glb-skin-validation-01-actual-status.md`

## Benchmark Rules

This task is a structural correctness repair, not a performance optimization. Only measured artifact, graph, test-count, and runtime inventory values are recorded here. Pass/fail narratives belong in the evidence ledger.

## B0 - P0 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P0 | Oak.glb size | bytes | 9093808 | 9093808 | 9093808 | unchanged | 0 | E0-P0A-ARTIFACT1 |
| P0 | Oak.glb SHA-256 | digest | 5f96f86f...949c0c4 | 5f96f86f...949c0c4 | 5f96f86f...949c0c4 | exact expected | 0 | E0-P0A-ARTIFACT1 |
| P0 | GLB JSON skin count | skins | 1 | 1 | 1 | 1 | 0 | E0-P0A-ARTIFACT2 |
| P0 | Oak scene nodes | nodes | 55 | 55 | 55 | all reachable | 0 | E0-P0A-ARTIFACT4 |
| P0 | Oak skin joints | joints | 53 | 53 | 53 | non-empty/in-range | 0 | E0-P0A-ARTIFACT4 |
| P0 | Full package graph scan | files | 1118 | 1118 | 1118 | fresh/zero parse failures | 0 | E0-P0A-GRAPH1 |
| P0 | Capability subtree graph scan | files | 127 | 127 | 127 | fresh/zero parse failures | 0 | E0-P0A-GRAPH2 |

## B1 - P1 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P1 | Focused structural test methods | methods | 3 existing direct GLB methods | 6 | 6 | all direct GLB methods pass | +3 | E1-P1B-TEST4 |
| P1 | Skeleton/joints matrix subcases | cases | 3 existing scenarios | 8 | 8 | omitted/valid plus 6 fail-closed cases | +5 | E1-P1B-TEST1..3 |

## B2 - P2 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P2 | Exact existing Oak validation | result | GLB_skeleton blocker | PASS | PASS | PASS | resolved | E2-P2A-ARTIFACT1..3 |
| P2 | Real MPFB2 reruns | runs | 1 prior Issue 52 run | 0 in Issue 55 | pending | at most 1 | pending | E2-P2B-RUN1..6 |
| P2 | Game Truyen mutations | files | 0 | 0 | pending | 0 | 0 | E2-P2B-RUN5 |

## Non-Benchmarkable Notes

- glTF contract interpretation, validator defect classification, source scope, and stop-law decisions are correctness evidence, not performance benchmarks.
- Docker, browser, and visual metrics are not applicable to this non-UI Python structural-validation slice.
