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
| P0 | age-expired AERG decision | enum | `SUPPORTED` | `SUPPORTED` | `STALE` | `STALE` | `SUPPORTED -> STALE` | `E0-P0A-PROBE1`, `E1-P1B-GREEN1` |
| P0 | explicit-stale AERG decision | enum | `SUPPORTED` | `SUPPORTED` | `STALE` | `STALE` | `SUPPORTED -> STALE` | `E0-P0A-PROBE1`, `E1-P1B-GREEN1` |
| P0 | expired result QI checkpoint | bool | `True` | `True` | `False` | `False` | `True -> False` | `E0-P0A-QI1`, `E1-P1C-QI1` |
| P0 | Anvien scan | files / parse failures | `894 / 0` | `898 / 0` | `898 / 0` | no parse failures | no parse failures | `E0-P0A-GRAPH1`, `E2-P2B-RUN4` |

## B1 - P1 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|---|---|---:|---|---|---|---|---|---|
| P1 | focused freshness tests | tests | `missing` | `17 run / 4 expected red` | `17 passed` | all required cases pass after repair | `17/17` | `E1-P1A-RED1`, `E1-P1B-GREEN2` |
| P1 | freshness-specific subset | tests | `missing` | `5 passed` | `5 passed` | all stale discriminators pass | `5/5` | `E2-P2A-RUN1` |
| P1 | production AERG SHA-256 | hash | `B6B9E6750F3ABEA0975B3F888EBEC7C43D54337482262287322CB4C309A36C36` | `0B14D04B3326D88FC8DDB4EE5FD8F8C7C570F517A262749BEF5F25F196D1BE2F` | `0B14D04B3326D88FC8DDB4EE5FD8F8C7C570F517A262749BEF5F25F196D1BE2F` | exact repair hash | changed only intended source | `E1-P1B-GREEN3` |

## B2 - P2 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|---|---|---:|---|---|---|---|---|---|
| P2 | reconstructed A-Z plus stale extensions | semantic cases | `26 baseline` | `26/26 baseline + 2 extensions` | `28 total pass` | report actual coverage | `+2 explicit stale cases` | `E2-P2A-RUN2` |
| P2 | full capability suite | passed / skipped | `347 / 6` | `352 / 6` | `352 / 6` | no new failure | `+5 tests, 0 failures` | `E2-P2B-RUN1` |
| P2 | focused QI suite | passed / skipped | `44 / 1` | `44 / 1` | `44 / 1` | no new failure | unchanged | `E2-P2A-RUN3` |
| P2 | focused FW01 checkpoint | passed | `6` | `6` | `6` | `6` | unchanged | `E2-P2A-RUN4` |
| P2 | C43 + RF01 orientation/packaging | passed | `18` | `18` | `18` | `18` | unchanged | `E2-P2B-RUN2` |

## Non-Benchmarkable Notes

No UI, Docker, package, deployment, or host-performance benchmark applies to
this offline Python semantic repair. Compile/test timings are recorded in the
evidence ledger when available, not treated as product performance claims.
