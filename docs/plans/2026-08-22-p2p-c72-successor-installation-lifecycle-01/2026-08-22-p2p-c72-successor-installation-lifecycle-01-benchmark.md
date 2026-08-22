# P2P C72 Successor Installation Lifecycle 01 Benchmark Ledger

## Metadata

- Date: `2026-08-22`
- Plan: `docs/plans/2026-08-22-p2p-c72-successor-installation-lifecycle-01/2026-08-22-p2p-c72-successor-installation-lifecycle-01-plan.md`
- Evidence: `docs/plans/2026-08-22-p2p-c72-successor-installation-lifecycle-01/2026-08-22-p2p-c72-successor-installation-lifecycle-01-evidence.md`
- Benchmark: `docs/plans/2026-08-22-p2p-c72-successor-installation-lifecycle-01/2026-08-22-p2p-c72-successor-installation-lifecycle-01-benchmark.md`
- Actual status: `docs/plans/2026-08-22-p2p-c72-successor-installation-lifecycle-01/2026-08-22-p2p-c72-successor-installation-lifecycle-01-actual-status.md`

## Benchmark Rules

Record measured counts, hashes, sizes, timings, and pass/fail counts only. Design decisions and validation narrative belong in evidence.

## B0 - P0 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|---|---|---:|---:|---:|---:|---:|---:|---|
| P0 | `.72` artifact SHA | hex | known immutable | pending | pending | unchanged | pending | `E0-P0A-SUBJECT1` |
| P0 | `.72` archive members | members | 491 | pending | pending | unchanged | pending | `E0-P0A-SUBJECT1` |
| P0 | canonical lineage head | commit | `4ce6a85f...` | pending | pending | exact source | pending | `E0-P0A-REF1` |

## B1 - P1 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|---|---|---:|---:|---:|---:|---:|---:|---|
| P1 | packaged pin producers | count | 0 in `.72` | pending | pending | 1 | pending | `E1-P1A-PACKAGE1` |
| P1 | fail-closed cases | pass/total | 0/6 | pending | pending | 6/6 | pending | `E1-P1B-NEG1..E1-P1B-NEG6` |

## B2 - P2 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|---|---|---:|---:|---:|---:|---:|---:|---|
| P2 | project-eval gate | pass/total | missing in `.72` pilot | pending | pending | PASS | pending | `E2-P2A-EVAL1` |
| P2 | governance drift failures | failures | 9 prior | pending | pending | 0 | pending | `E2-P2B-DRIFT1` |

## B3 - P3 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|---|---|---:|---:|---:|---:|---:|---:|---|
| P3 | successor artifact members | members | n/a | pending | pending | accounted=total | pending | `E3-P3A-MINT1` |
| P3 | artifact hash mechanisms | match | n/a | pending | pending | TRUE | pending | `E3-P3A-MINT1` |
| P3 | unexplained regression failures | failures | unknown | pending | pending | 0 | pending | `E3-P3B-GATE1` |

## Non-Benchmarkable Notes

Authority preservation, historical immutability, Manus C43 isolation, AERG non-implementation, approval state, and authoritative-project safety are evidence facts rather than benchmark metrics.
