# P2P-C15 Bounded Foreground Delegation & Worker Handoff Controller Benchmark Ledger

## Metadata

- Date: `2026-08-16`
- Plan: `docs/plans/2026-08-15-p2p-c15-bounded-foreground-delegation/2026-08-15-p2p-c15-bounded-foreground-delegation-plan.md`
- Evidence: `docs/plans/2026-08-15-p2p-c15-bounded-foreground-delegation/2026-08-15-p2p-c15-bounded-foreground-delegation-evidence.md`
- Benchmark: `docs/plans/2026-08-15-p2p-c15-bounded-foreground-delegation/2026-08-15-p2p-c15-bounded-foreground-delegation-benchmark.md`
- Actual status: `docs/plans/2026-08-15-p2p-c15-bounded-foreground-delegation/2026-08-15-p2p-c15-bounded-foreground-delegation-actual-status.md`

## Benchmark Rules

Record measured counts, timings, hashes, inventories, and bounded-resource values only. Pass/fail narrative belongs in the evidence ledger. Baselines are from the refreshed P0 graph or pre-change source inspection; final values are added after the matching slice.

## B0 - P0 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P0 | Root files scanned | files | 359 | 359 | 359 | no unexplained loss | 0 | `E0-P0A-GRAPH1` |
| P0 | Root parsed code files | files | 36 | 36 | 36 | no parse failures | 0 | `E0-P0A-GRAPH1` |
| P0 | C12 local relationships | edges | 360 | 360 | 360 | preserve direct boundary | 0 | `E0-P0A-GRAPH2` |
| P0 | C11 local relationships | edges | 432 | 432 | 432 | preserve durable task boundary | 0 | `E0-P0A-GRAPH3` |
| P0 | Official `.19` SHA-256 | digest | `3a9ee51321e1f5e40e35ce73eb90727cddb571a672aa095d16d76af2feb03dd8` | same | same | unchanged | 0 | `E0-P0A-SRC5` |

## B1 - P1 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P1 | Delegation child limit | children | 0 supported path | 1 | 1 | 1 maximum | +1 bounded | `E1-P1B-EXEC1`, `E2-P2A-REG1` |
| P1 | Delegation depth limit | levels | 0 supported path | 1 | 1 | 1 maximum | +1 bounded | `E1-P1B-EXEC1` |
| P1 | Allowed retry attempts | attempts | C12 finite budget | 1 transient retry in bounded test; 0 boundary retries | same | bounded, non-mutating only | bounded | `E1-P1B-VERIFY1`, `E2-P2A-REG1` |
| P1 | New runtime modules in allowlist | modules | 0 C15 modules | 1 | 1 | 1 bounded module | +1 | `E1-P1A-SRC1`, `E2-P2B-PKG1` |

## B2 - P2 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P2 | Project paired eval trials per variant | trials | 2 existing | 2 | 2 | >=2 isolated trials | 0 | `E2-P2A-EVAL1` |
| P2 | Full affected test count | tests | 40 C11/C12 baseline | 64 C15+C11+C12; 218 full suite | 64 affected / 218 full | all affected tests pass | +178 full-suite inventory | `E1-P1C-REG1`, `E2-P2A-REG1`, `E2-P2C-REG2` |
| P2 | Focused C15 test count | tests | 23 | 24 | 24 | all C15 tests pass | +1 boundary case | `E1-P1A-TEST1`, `E2-P2C-REG2` |
| P2 | Project-style field acceptance checks | checks | 0 | 6 A-F | 6 A-F | all checks pass | +6 | `E2-P2C-FIELD1` |
| P2 | Evaluation matrix coverage | cases | 0 | 18 | 18 | all mapped cases pass | +18 | `E2-P2C-EVAL18` |
| P2 | Current C15 module graph symbols | symbols | 280 prior | 283 | 283 | parse succeeds; warning retained | +3 | `E2-P2C-ANVIEN2` |
| P2 | Current C15 module local relationships | edges | 605 prior | 607 | 607 | graph refresh succeeds | +2 | `E2-P2C-ANVIEN2` |
| P2 | Field evidence JSON size | bytes | N/A | 4,210 | 4,210 | repo-local artifact | recorded | `E2-P2C-FIELD1` |
| P2 | Real host subagent receipts | receipts | 0 | 1 | 1 | exactly one bounded receipt | +1 | `E2-P2C-HOST2` |
| P2 | Official entries compared to development tree | entries | N/A | 403 mapped | 403 mapped | complete path-mapped comparison | recorded | `E2-P2C-LINEAGE2` |
| P2 | Byte-identical official entries | entries | N/A | 390 | 390 | evidence only; no safe-lineage claim | recorded | `E2-P2C-LINEAGE2` |
| P2 | Official/development content mismatches | entries | N/A | 13 | 13 | must be classified before integration | recorded | `E2-P2C-LINEAGE2` |
| P2 | Candidate package SHA-256 | digest | N/A | `ae39b78972c03ca17855e0cc86e18fbd997f1eb4d62116e909674abc86d90b1e` | same | recorded without official overwrite | recorded | `E2-P2B-PKG1` |
| P2 | Official `.19` SHA-256 | digest | `3a9ee51321e1f5e40e35ce73eb90727cddb571a672aa095d16d76af2feb03dd8` | same | same | unchanged | 0 | `E2-P2B-PROTECT1` |

## Non-Benchmarkable Notes

- No browser/layout metric applies; this is a local Python control/runtime surface.
- Host child identity availability is a factual boundary and must not be averaged or inferred from synthetic runs.
- Git commit count cannot be measured because the repository has no `.git`; record the limitation in closure evidence.
