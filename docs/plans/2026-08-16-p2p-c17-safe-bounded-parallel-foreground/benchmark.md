# P2P-C17 Safe Bounded Parallel Foreground Execution Benchmark Ledger

## Metadata

- Date: `2026-08-16`
- Plan: `docs/plans/2026-08-16-p2p-c17-safe-bounded-parallel-foreground/plan.md`
- Evidence: `docs/plans/2026-08-16-p2p-c17-safe-bounded-parallel-foreground/evidence.md`
- Benchmark: `docs/plans/2026-08-16-p2p-c17-safe-bounded-parallel-foreground/benchmark.md`
- Actual status: `docs/plans/2026-08-16-p2p-c17-safe-bounded-parallel-foreground/actual-status.md`

## Benchmark Rules

Only measured counts, sizes, hashes, limits, and timings belong here. Pass/fail narrative belongs in `evidence.md`. No benchmark is treated as proof that P2P improves a project.

## B0 - P0 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P0 | Official `.19` package size | bytes | 2,432,518 | 2,432,518 | 2,432,518 | unchanged | 0 | E0-P0A-BASE1 |
| P0 | Official package members | members | 408 | 408 | 408 | unchanged | 0 | E0-P0A-BASE1 |
| P0 | Anvien root file projection | files | 388 | 400 | 400 | no unexplained loss | +12 source/test/report files | E0-P0A-ANVIEN1/E3-P3A-DETECT1 |
| P0 | Anvien root relationship graph | relationships | 17,622 | 18,576 | 18,576 | no unexplained loss | +954 | E0-P0A-ANVIEN1/E3-P3A-DETECT1 |
| P0 | Anvien system graph | files / relationships | N/A | 51 / 12,731 | 51 / 12,731 | parsed, no failures | N/A | E3-P3A-DETECT1 |
| P0 | Existing C15 child ceiling | children per controller | 1 | 1 | 1 | preserve | 0 | source inspection |

## B1 - P1 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P1 | Active source version | version | 8.4.7-C-codex.15 | 8.4.7-C-codex.20 | 8.4.7-C-codex.20 | 8.4.7-C-codex.20 | reconciled | E1-P1A-LINEAGE1 |
| P1 | Official baseline SHA | SHA-256 | 3a9ee51321e1f5e40e35ce73eb90727cddb571a672aa095d16d76af2feb03dd8 | 3a9ee51321e1f5e40e35ce73eb90727cddb571a672aa095d16d76af2feb03dd8 | 3a9ee51321e1f5e40e35ce73eb90727cddb571a672aa095d16d76af2feb03dd8 | unchanged | 0 | E0-P0A-BASE1/E1-P1B-HASH2 |
| P1 | Candidate package size | bytes | N/A | 2,518,543 | 2,518,543 | recorded, not promoted | N/A | E1-P1B-FINAL2-HASH |
| P1 addendum | Cognitive-economy candidate package size | bytes | 2,518,543 | 2,521,253 | 2,521,253 | new immutable candidate, not promoted | +2,710 | E4-CE-CANDIDATE-PACKAGE |

## B2 - P2 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P2 | Maximum parallel children | children | 1 | 2 | 2 | 2 | +1 bounded cap | E2-P2A-GATE4 |
| P2 | Maximum delegation depth | levels | 1 | 1 | 1 | 1 | 0 | E2-P2A-GATE5 |
| P2 | Group child handoffs | distinct bindings | N/A | 2 | 2 | one per selected child, max 2 | N/A | E2-P2B-RUN1 |
| P2 | Group foreground concurrency | active callbacks | N/A | 2 peak | 2 peak | <=2, no background | bounded | E2-P2B-RUN2 |
| P2 | Rescue children after failure | children | N/A | 0 | 0 | 0 | 0 | E2-P2B-VERIFY4/E2-P2B-VERIFY6 |

## B3 - P3 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P3 | Focused C17 tests | tests | 0 | 14/14 | 14/14 | all pass | PASS | E3-P3A-VALIDATE1 |
| P3 | Full unit/eval tests | tests | prior C10-C16 suite | 236/236 | 236/236 | no regression | PASS | E3-P3A-VALIDATE1 |
| P3 | Live parallel certification | boolean | NO | false | false | truthful; likely NO | unchanged | E3-P3A-STATE2 |

## Non-Benchmarkable Notes

- UI layout, browser, Docker, database throughput, and network metrics are not applicable to this Python foreground-runtime slice.
- C17 performance value is bounded concurrency and safety behavior, not a claim of throughput improvement; timing evidence will only show that two supplied callbacks overlapped when the real supported callback path exists.

## B4 - Cognitive Economy / Spawn Economy measurements

| Metric | Unit | Measured value | Boundary | Evidence |
|---|---:|---:|---|---|
| Economy profiles per evaluated pair | profiles | 2 | max-two C17 group | E4-CE-SPAWN |
| Economy work signal | fixed units | 1/2/4/8 by TINY/SMALL/MODERATE/LARGE default | policy signal only | E4-CE-GATE |
| Handoff + verification signal | fixed units | recorded per candidate | coordination gate only | E4-CE-GATE |
| Large-context rejection threshold | bytes | 65,536 | local proxy gate, not tokens | E4-CE-GATE/E4-CE3 |
| Context measurement label | label | `LOCAL_SERIALIZATION_PROXY` | no cost/time conversion | E4-CE-CONTEXT/E4-CE9 |
| CE9 baseline local serialized proxy | bytes | N/A | 103,041 | 103,041 | measured fixture | N/A | E4-CE9 |
| CE9 efficient local serialized proxy | bytes | N/A | 3,020 | 3,020 | measured fixture | lower than baseline | E4-CE9 |
| Spawn outcomes exercised | cases | 0 / 1 / 2 workers | 0 blocked/no-start; 1 sequential; 2 bounded parallel | E4-CE-SPAWN |
| Worker output contract | field | `output_is_evidence=false` | parent must verify | E4-CE5/E4-CE-SEAMS |
| Addendum focused C17 + CE tests | tests | 14/14 | 26/26 | 26/26 | all pass | +12 controlled cases | E4-CE-REGRESSION |
| Addendum full repository tests | tests | 236/236 | 248/248 | 248/248 | no regression | +12 CE tests | E4-CE-REGRESSION |

The addendum intentionally records no token count, API price, provider cost,
wall-clock saving, throughput, or universal optimum. Local serialized bytes,
fixed policy signals, and test counts are structural evidence only.
