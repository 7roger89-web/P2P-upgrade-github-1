# P2P Native Decision Trace Benchmark Ledger

## Metadata

- Date: `2026-08-12`
- Plan: `docs/plans/2026-08-12-p2p-native-decision-trace/2026-08-12-p2p-native-decision-trace-plan.md`
- Evidence: `docs/plans/2026-08-12-p2p-native-decision-trace/2026-08-12-p2p-native-decision-trace-evidence.md`
- Benchmark: `docs/plans/2026-08-12-p2p-native-decision-trace/2026-08-12-p2p-native-decision-trace-benchmark.md`
- Actual status: `docs/plans/2026-08-12-p2p-native-decision-trace/2026-08-12-p2p-native-decision-trace-actual-status.md`

## Benchmark Rules

Record measured counts and hashes only. CLI/state-only scope has no browser,
layout, service, or Docker benchmark. Baseline values come from fresh local
inspection or the historical certification report.

## B0 - P0 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P0 | canonical denominator | count | 8 | 8 | 8 | 8 | 0 | E0-P0A-SAFE1 |
| P0 | full quorum | ratio | 8/8 | 8/8 | 8/8 | 8/8 | 0 | E0-P0A-SAFE1 |
| P0 | native decision trace records in baseline report | count | 0 | 0 | 0 | baseline documented | 0 | E0-P0A-GAP1 |
| P0 | Anvien registration for target | boolean | false | false | false | limitation recorded | 0 | E0-P0A-ANVIEN1 |

## B1 - P1 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P1 | Decision Trace SPEC files | count | 0 | 1 | 1 | 1 | +1 | E1-P1A-SPEC1 |
| P1 | architecture review verdict | count | 0 | 1 PASS | 1 PASS | 1 PASS | +1 PASS | E1-P1A-ARCH1 |

## B2 - P2 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P2 | durable trace stores | count | 0 separate / 1 existing ledger | 0 separate / 1 existing ledger | 0 separate / 1 existing ledger | 0 separate / 1 existing ledger | 0 | E2-P2A-CORE1 |
| P2 | material workflow trace capture | ratio | 0/1 | 1/1 | 1/1 | 1/1 | +1 | E2-P2B-CAPTURE1 |
| P2 | routine trace spam | count | 0 | 0 | 0 | 0 | 0 | E2-P2B-CAPTURE1 |
| P3 | DT behavioral cases | count | 0/24 | 24/24 | 24/24 | 24/24 | +24 | E3-P3A-DT1..DT24 |
| P3 | existing unittest regression | count | 45/45 baseline | 48/48 | 48/48 | all pass | +3 tests | E3-P3B-REG1 |
| P3 | secret scan findings | count | 0 | 0 | 0 | 0 | 0 | E3-P3B-REG1 |

## Non-Benchmarkable Notes

- Browser, Playwright, Docker, UI, graph database, and service metrics are not
  applicable to this CLI/state-only capability.
- Full eight-thread runtime quorum is not a local benchmark and must not be
  inferred from deterministic tests.
