# P2P Beginner UIUX First-Decision & Release Acceptance Closure Benchmark

**Goal ID:** `goal-20260813-p2p-beginner-uiux-first-decision-release-acceptance`
**Date:** 2026-08-13
**Status:** BLOCKED — project trial measurements recorded; `.13` packaging measurements were not run because fresh native acceptance failed
**Plan:** `2026-08-13-p2p-beginner-uiux-first-decision-release-acceptance-plan.md`

## Measurement rules

- Evaluation-trial results are product-quality evidence, not performance claims. They must still use isolated runs, frozen fixtures, and exact evidence hashes.
- Record benchmarkable measurements only when the slice changes product/runtime performance, capacity, package/startup size, graph/DB throughput, or graph inventory. Build/test/e2e timings are validation evidence, not product benchmarks.
- Never average incomparable results or convert a missing baseline into a zero.
- Each run must include variant, run ID, case count, attempted/pass/partial/fail counts, outcome, fixture/evidence hashes, environment/surface, and timestamp.

## B0 — Frozen evaluation dimensions

| Dimension | Baseline | Current P2P | Required comparison |
|---|---|---|---|
| Inputs | Existing `.p2p/evals/suite.json` and five fixture hashes | Same | Exact equality |
| Isolation | Fresh temporary root per run under repository `.tmp` | Same | No cross-run memory |
| Trials | 2 | 2 | Policy minimum |
| Primary score | Passed cases / attempted cases | Same | P2P >= 0.8 |
| Regression | Baseline vs P2P case outcomes | Same | No prohibited regression |
| Spread | Per-case score spread | Same | <= 0.25 |

## B1 — Project evaluation trial ledger

| Run ID | Variant | Trial | Attempted | Passed | Partial | Failed | Outcome | Fixture hash set | Evidence artifact | Status |
|---|---|---:|---:|---:|---:|---:|---|---|---|---|
| baseline-trial-3 | baseline `.12` | 1 | 5 | 5 | 0 | 0 | PASS | frozen suite; all target fixture hashes match | `.p2p/evals/runs/baseline-trial-3/trial-record.json` | PASS |
| baseline-trial-4 | baseline `.12` | 2 | 5 | 5 | 0 | 0 | PASS | frozen suite; all target fixture hashes match | `.p2p/evals/runs/baseline-trial-4/trial-record.json` | PASS |
| p2p-trial-3 | current P2P | 1 | 5 | 5 | 0 | 0 | PASS | frozen suite; all target fixture hashes match | `.p2p/evals/runs/p2p-trial-3/trial-record.json` | PASS |
| p2p-trial-4 | current P2P | 2 | 5 | 5 | 0 | 0 | PASS | frozen suite; all target fixture hashes match | `.p2p/evals/runs/p2p-trial-4/trial-record.json` | PASS |

## B2 — Required acceptance calculations

| Metric | Formula | Required result | Status |
|---|---|---|---|
| Baseline completeness | two legitimate baseline run records | 2 | PASS |
| Current completeness | two legitimate current-P2P run records | 2 | PASS |
| P2P pass rate | passed / attempted across current trials | 1.00 >= 0.80 | PASS |
| Mean regression | current score minus baseline score under policy | 0.00 >= 0.00 | PASS |
| Case regressions | count of prohibited case regressions | 0 | PASS |
| Score spread | maximum permitted per-case spread | 0.00 <= 0.25 | PASS |

## B3 — Implementation and release measurements

No product/runtime performance benchmark is currently in scope. `.13` packaging was not reached; protected `.12` remains the only candidate and no release measurements are claimed.

## Non-benchmark validation notes

DW1–DW18, full unittest, Capability Foundation, DT1–DT24, secret scans, governance/drift, and host receipt checks are acceptance evidence. Their command durations may be retained in raw reports, but no performance conclusion should be drawn from them for this goal.
