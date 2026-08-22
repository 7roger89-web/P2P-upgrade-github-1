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
| P0 | `.72` artifact SHA | hex | known immutable | `70613080d2ddbb92a52d2d79186e125439ec7f5ba8a6fa87bda9208d1b39d872` | same | unchanged | 0 | `E0-CLOSE-HISTORY1` |
| P0 | `.72` archive members | members | 491 | 491 | 491 | unchanged | 0 | `E0-CLOSE-HISTORY1` |
| P0 | canonical lineage head | commit | `4ce6a85f...` | `4ce6a85f5991b6d6c464fb4b59e177114698947e` | same base | exact source | 0 | `E0-P0A-REF1` |

## B1 - P1 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|---|---|---:|---:|---:|---:|---:|---:|---|
| P1 | packaged pin producers | count | 0 in `.72` | 1 | 1 | 1 | +1 | `E1-CLOSE-PIN1` |
| P1 | fail-closed pin cases | pass/total | 0/6 | 5/5 | 5/5 | all exercised cases pass | +5 | `E1-CLOSE-TEST1` |
| P1 | MAP-BEFORE-WORK negative cases | pass/total | 0/4 | 4/4 blocked | 4/4 blocked | fail closed | +4 | `E1-CLOSE-MAP1` |

## B2 - P2 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|---|---|---:|---:|---:|---:|---:|---:|---|
| P2 | project-eval gate | pass/total | missing in `.72` pilot | `5/5` case pairs; 2+2 trials each | same | PASS | 0 regressions | `E2-CLOSE-EVAL1` |
| P2 | governance drift failures | failures | 9 prior | 0 | 0 | 0 | -9 | `E2-CLOSE-DRIFT1` |

## B3 - P3 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|---|---|---:|---:|---:|---:|---:|---:|---|
| P3 | successor artifact members | members | n/a | 493 total / 493 accounted | same | accounted=total | 0 unaccounted | `E3-CLOSE-PACKAGE1` |
| P3 | artifact hash mechanisms | match | n/a | 2/2 | 2/2 | TRUE | 0 mismatch | `E3-CLOSE-ARTIFACT1` |
| P3 | unexplained regression failures | failures | unknown | 0 | 0 | 0 | 0 | `E3-CLOSE-GATE1` |

## Non-Benchmarkable Notes

Authority preservation, historical immutability, Manus C43 isolation, AERG non-implementation, approval state, and authoritative-project safety are evidence facts rather than benchmark metrics.

## Final measured values

- Candidate: `8.4.7-C-codex.73`; ZIP SHA `72bfbef935a41b68ebe3c7fc5464d99d2a47e849cb77e85507ceb90cdf19ef1a`; size `2909357` bytes.
- Source at mint: commit `4fba15e47f8c7290d71992dc0f44356321080c1b`; tree `dff1ccbbcab439f806c4f391e3a62ac857a1e1d3`.
- Metadata: manifest SHA `c5c305e0561a29d77aee214e056fe7f237d6217d0a25255573dd737619b354d9`; inventory digest `b4e657fb8e7acb5519acc933e89cda2b47bff4bc3ff66ceda5c8ed10739f0005`; checksum-set digest `02ef2f3f1c772f89a2e6714bd90a9f048d1155777c801ccff1e94e9ec68139ea`.
- Installed pilot: strict Doctor `ok=true`; project eval baseline/p2p means `1.0/1.0`; delta `0.0`; case regressions `0`; p2p pass rate `1.0`.
- FW05 owner-experience matrix: `29` tests, `OK`, `1` unrelated shadow-project skip. Targeted lifecycle suites: `4/4` scripts PASS plus pin lifecycle PASS.
- Regression suites: capability discovery `335/335 PASS` with `6` skips; C35 provider-neutral `57/57 PASS`; bounded FW `94/94 PASS`; new unexplained failures `0`.
- Technical prepare: `PASS`; approval state `PENDING`; no promotion.
