# AESTHETICA Evidence-Based Selective Routing Closure Benchmark Ledger

## Metadata

- Date: `2026-08-13`
- Plan: `docs/plans/2026-08-13-aesthetica-evidence-based-selective-routing-closure/2026-08-13-aesthetica-evidence-based-selective-routing-closure-plan.md`
- Evidence: `docs/plans/2026-08-13-aesthetica-evidence-based-selective-routing-closure/2026-08-13-aesthetica-evidence-based-selective-routing-closure-evidence.md`
- Benchmark: `docs/plans/2026-08-13-aesthetica-evidence-based-selective-routing-closure/2026-08-13-aesthetica-evidence-based-selective-routing-closure-benchmark.md`
- Actual status: `docs/plans/2026-08-13-aesthetica-evidence-based-selective-routing-closure/2026-08-13-aesthetica-evidence-based-selective-routing-closure-actual-status.md`

## Benchmark Rules

Record measured counts, hashes, lifecycle results, and test totals only. Do not infer universal value from routing counts.

## B0 - P0 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P0 | certification scenarios | count | 10 | 10 | 10 | 10 | 0 | prior certification report |
| P0 | canonical identities | count | 8 | 8 | 8 | 8 | 0 | `E0-P0A-CANON1` |
| P0 | quorum denominator | count | 8 | 8 | 8 | 8 | 0 | `E0-P0A-CANON1` |

## B1 - P1 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P1 | focused selective routing cases | count | 0 | 36 | 36 | >=30 | +36 | `E1-P1B-CASES1` |
| P1 | languages represented | count | 0 | 2 | 2 | 2 | +2 | `E1-P1B-CASES1` |
| P1 | UIUX-preserving UI cases | count | 0 | 32 | 32 | all UI cases | +32 | `E1-P1B-REGRESSION1` |

## B2 - P2 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P2 | candidate version | string | `.14` | `.15` | `.15` | `.15` | +patch | `E2-P2A-PACKAGE1` |
| P2 | `.14` artifact SHA changes | boolean | false | false | false | false | 0 | `E2-P2A-IMMUTABLE1` |
| P2 | fresh install | lifecycle path | not run | PASS | PASS | PASS | verified | `E2-P2B-LIFE1` |
| P2 | upgrade from `.14` | lifecycle path | not run | PASS | PASS | PASS | verified | `E2-P2B-LIFE2` |
| P2 | same-version reinstall | lifecycle path | not run | PASS | PASS | PASS | verified | `E2-P2B-LIFE3` |

## Non-Benchmarkable Notes

Exact specialist execution time/tokens are not part of this routing contract. No new performance claim is made.
