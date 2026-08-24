# P2P AERG Expired-Evidence Fail-Closed Repair Benchmark Ledger

## Metadata

- Date: `2026-08-24`
- Plan: `Docs/plans/2026-08-24-p2p-aerg-stale-evidence-repair/2026-08-24-p2p-aerg-stale-evidence-repair-plan.md`
- Evidence: `Docs/plans/2026-08-24-p2p-aerg-stale-evidence-repair/2026-08-24-p2p-aerg-stale-evidence-repair-evidence.md`
- Benchmark: `Docs/plans/2026-08-24-p2p-aerg-stale-evidence-repair/2026-08-24-p2p-aerg-stale-evidence-repair-benchmark.md`
- Actual status: `Docs/plans/2026-08-24-p2p-aerg-stale-evidence-repair/2026-08-24-p2p-aerg-stale-evidence-repair-actual-status.md`

## Benchmark Rules

Record measured behavior and timings only. Pass/fail narrative belongs in the
evidence ledger. No release, package, or host benchmark is in scope.

## B0 - P0 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|---|---|---:|---|---|---|---|---|---|
| P0 | age-expired AERG decision | enum | `SUPPORTED` | `SUPPORTED` | pending | `STALE` | pending | `E0-P0A-PROBE1` |
| P0 | explicit-stale AERG decision | enum | `SUPPORTED` | `SUPPORTED` | pending | `STALE` | pending | `E0-P0A-PROBE1` |
| P0 | expired result QI checkpoint | bool | `True` | `True` | pending | `False` | pending | `E0-P0A-QI1` |
| P0 | Anvien scan | files / parse failures | `894 / 0` | `894 / 0` | pending | no parse failures | pending | `E0-P0A-GRAPH1` |

## B1 - P1 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|---|---|---:|---|---|---|---|---|---|
| P1 | focused freshness tests | tests | `missing` | `17 run / 4 expected red` | pending | all required cases pass after repair | pending | `E1-P1A-RED1`, `E1-P1A-RED2` |
| P1 | production AERG SHA-256 | hash | current hash | pending | pending | exact repair hash | pending | `E1-P1B-GREEN3` |

## B2 - P2 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|---|---|---:|---|---|---|---|---|---|
| P2 | full capability suite | passed / skipped | `347 / 6` | pending | pending | no new failure | pending | `E2-P2B-RUN1` |
| P2 | focused FW01 checkpoint | passed | `6` | pending | pending | `6` | pending | `E2-P2A-RUN4` |

## Non-Benchmarkable Notes

No UI, Docker, package, deployment, or host-performance benchmark applies to
this offline Python semantic repair. Compile/test timings are recorded in the
evidence ledger when available, not treated as product performance claims.
