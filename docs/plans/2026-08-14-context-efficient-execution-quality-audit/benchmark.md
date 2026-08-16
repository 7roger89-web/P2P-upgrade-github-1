# Context-Efficient Execution & Quality Audit — Foundation for Durable Orchestration Benchmark Ledger

## Metadata

- Date: `2026-08-14`
- Plan: `docs/plans/2026-08-14-context-efficient-execution-quality-audit/plan.md`
- Evidence: `docs/plans/2026-08-14-context-efficient-execution-quality-audit/evidence.md`
- Benchmark: `docs/plans/2026-08-14-context-efficient-execution-quality-audit/benchmark.md`
- Actual status: `docs/plans/2026-08-14-context-efficient-execution-quality-audit/actual-status.md`

## Benchmark Rules

- Numbers below are measured command or deterministic serialization results.
- `DETERMINISTIC_PROXY` values are not token, cache, time, or provider-cost
  measurements.
- Unknown host metrics are not converted into zero.
- Quality scores in the proxy suite measure only evidence-shape compliance;
  they are not real task-quality scores.

## B0 - P0 Baseline Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P0 | Official artifact size | bytes | 2,385,951 | 2,385,951 | 2,385,951 | unchanged | 0 | `E0-P0A-BASE2` |
| P0 | Official artifact SHA-256 | hash | `af4d63a8…e195` | `af4d63a8…e195` | `af4d63a8…e195` | unchanged | 0 | `E0-P0A-BASE2` |
| P0 | Anvien files scanned | files | 266 | 266 | 266 | inventory refreshed | 0 | `E0-P0A-GRAPH1` |
| P0 | Anvien graph nodes | nodes | 10,439 | 10,439 | 10,439 | graph refreshed | 0 | `E0-P0A-GRAPH1` |
| P0 | Anvien relationships | edges | 11,861 | 11,861 | 11,861 | graph refreshed | 0 | `E0-P0A-GRAPH1` |

## B1 - P1 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P1 | Workflow source symbols | symbols | 258 | 258 | 258 | inspect-only | 0 | `E0-P0A-GRAPH2` |
| P1 | Workflow linked flows | flows | 44 | 44 | 44 | inspect-only | 0 | `E0-P0A-GRAPH2` |
| P1 | Decision Trace cases | cases | 24 | 24 | 24 | 24 PASS | 0 | `E3-P3A-TEST2` |
| P1 | Core unit tests | tests | 76 | 76 | 76 | all PASS | 0 | `E3-P3A-TEST1` |
| P1 | Historical host receipt records | records | 14 | 14 | 14 | do not treat as current worker proof | 0 | `E1-P1B-TELEM1` |

## B2 - P2 Benchmarks

| Phase | Metric | Unit | Baseline A | Latest B | Final B | Target | Delta B-A | Evidence |
|-------|--------|------------|------------|----------|---------|--------|-----------|----------|
| P2 | Frozen scenarios | scenarios | 12 | 12 | 12 | >=12 | 0 | `E2-P2A-BENCH1` |
| P2 | Trials per condition | trials | 24 | 24 | 24 | 24 | 0 | `E2-P2A-BENCH3` |
| P2 | Total paired proxy trials | trials | 24 | 24 | 24 | 48 total | 0 | `E2-P2A-BENCH3` |
| P2 | Serialized explicit context | bytes | 122,260 | 109,110 | 109,110 | measure only; quality first | -13,150 (-10.76%) | `E2-P2A-BENCH5` |
| P2 | Mean serialized explicit context | bytes/trial | 5,094.17 | 4,546.25 | 4,546.25 | proxy only | -547.92 (-10.76%) | `E2-P2A-BENCH5` |
| P2 | Candidate Knowledge Delta | bytes | N/A | 12,042 total | 12,042 total | compact return proxy | N/A | `E2-P2A-BENCH5` |
| P2 | Contract-proxy evidence score | score | 1.0 | 1.0 | 1.0 | >=0.8 | 0.0 | audit suite gate |
| P2 | Real Q1-Q12 quality observations | observations | 0 | 0 | 0 | required before PASS | 0 | `E2-P2B-QUALITY1` |

## B3 - Validation Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P3 | Governance drift failures | failures | 0 | 0 | 0 | 0 | 0 | `E3-P3A-TEST3` |
| P3 | Foundation capability doctor failures | failures | 0 | 0 | 0 | 0 | 0 | `E3-P3A-TEST4` |
| P3 | Subtree secret-scan findings | findings | 0 | 0 | 0 | 0 | 0 | `E3-P3A-SECURITY1..2` |
| P3 | Whole-repository secret-scan findings | findings | 5 | 5 | 5 | 0 | 0 | `E3-P3A-SECURITY3` |
| P3 | Package-doctor missing payload groups | groups | 2 | 2 | 2 | 0 | 0 | `E3-P3A-TEST7` |

## Non-Benchmarkable Notes

- Model input tokens, cached input tokens, output tokens, provider calls,
  child-worker calls, tool calls, raw tool-output volume, duplicate retrieval,
  repair/retry cost, model wall time, and provider cost are UNKNOWN or
  UNAVAILABLE in the current host/runtime.
- Existing `.p2p/evals/suite.json` is a five-case UI/UX suite for a different
  project and is excluded from these benchmark numbers.
- The proxy suite passing its structural gate does not satisfy quality
  non-inferiority.
