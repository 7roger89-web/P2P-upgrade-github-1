# P2P Goal subsystem refinement Benchmark Ledger

## Metadata

- Date: `2026-08-10`
- Plan: `docs/plans/2026-08-10-p2p-goal-refinement/2026-08-10-p2p-goal-refinement-plan.md`
- Evidence: `docs/plans/2026-08-10-p2p-goal-refinement/2026-08-10-p2p-goal-refinement-evidence.md`
- Benchmark: `docs/plans/2026-08-10-p2p-goal-refinement/2026-08-10-p2p-goal-refinement-benchmark.md`
- Actual status: `docs/plans/2026-08-10-p2p-goal-refinement/2026-08-10-p2p-goal-refinement-actual-status.md`

## Benchmark Rules

Record measured inventories and acceptance counts only. Do not treat synthetic case results as real project quality scores or live agent runtime measurements.

## B0 - P0 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|---|---|---:|---:|---:|---:|---:|---:|---|
| P0 | Goal eligibility classes implemented | count | 0 | 4 | 4 | 4 | +4 | `E1-P1A-CODE1`, `E3-SUPERVISOR1` |
| P0 | Mandatory criteria with verification oracles | count | 0/5 | 5/5 | 5/5 | 5/5 | +5 | `E1-P1A-CODE2`, `E3-TEST1` |
| P0 | Goal acceptance cases | count | 0 | 10 | 10 | 10 | +10 | `E1-P1B-TEST1`, `E3-ACCEPT1` |

## B1 - P1 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|---|---|---:|---:|---:|---:|---:|---:|---|
| P1 | Eligibility classes | count | 0 | 4 | 4 | 4 | +4 | `E1-P1A-TEST1`, `E3-TEST1` |
| P1 | Persisted Goal discipline fields | count | 0 | 8 (`context`, `eligibility`, `linter`, `work_type`, `exploration`, `mutations`, `backlog`, `oracles`) | 8 | 8 | +8 | `E1-P1A-CODE2`, `E1-P1B-CODE2`, `E3-SUPERVISOR1` |
| P1 | Direct Goal behavior tests | count | 4 existing | 17 total | 17 | 17 | +13 | `E1-P1B-TEST1`, `E1-P1B-TEST2`, `E3-TEST1` |

## B2 - P2 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|---|---|---:|---:|---:|---:|---:|---:|---|
| P2 | Goal acceptance cases PASS | count | 0 | 10 | 10 | 10 | +10 | `E1-P1B-TEST1`, `E3-ACCEPT1` |
| P2 | Existing workflow regression tests PASS | count | 4 | 4 | 4 | 4 | 0 | `E1-P1B-TEST2`, `E3-TEST1` |
| P2 | Duplicate Goal/governance subsystems | count | 0 | 0 | 0 | 0 | 0 | `E0-P0A-BOUND1`, `E3-SCOPE1` |

## Non-Benchmarkable Notes

Real project quality, wall-clock efficiency, and host-level eight-thread runtime are not measured by these safe fixtures.
