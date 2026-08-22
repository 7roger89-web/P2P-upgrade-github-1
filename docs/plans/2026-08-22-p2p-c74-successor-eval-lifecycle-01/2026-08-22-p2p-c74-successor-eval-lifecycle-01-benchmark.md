# P2P C74 Successor Evaluator Lifecycle Benchmark Ledger

## Metadata

- Date: `2026-08-22`
- Plan: `docs/plans/2026-08-22-p2p-c74-successor-eval-lifecycle-01/2026-08-22-p2p-c74-successor-eval-lifecycle-01-plan.md`
- Evidence: `docs/plans/2026-08-22-p2p-c74-successor-eval-lifecycle-01/2026-08-22-p2p-c74-successor-eval-lifecycle-01-evidence.md`
- Benchmark: `docs/plans/2026-08-22-p2p-c74-successor-eval-lifecycle-01/2026-08-22-p2p-c74-successor-eval-lifecycle-01-benchmark.md`
- Actual status: `docs/plans/2026-08-22-p2p-c74-successor-eval-lifecycle-01/2026-08-22-p2p-c74-successor-eval-lifecycle-01-actual-status.md`

## Benchmark Rules

The benchmark file records measurements.

It should contain:

- metadata and companion files;
- benchmark rules;
- benchmark sections such as `B0`, `B1`, or sections by phase/task;
- metric tables with unit, baseline, latest, final, target, and delta when needed;
- inventory count;
- runtime or performance metric;
- graph, coverage, or accuracy metric;
- package, bundle, file size, or hash metric;
- before/after numbers;
- UI, layout, or browser metric when the plan involves UI;
- command-surface or generated-output inventory when the plan involves generated documentation.

Benchmark records measured numbers only. Do not put command logs, design decisions, or validation narrative here. Build/test/e2e pass-fail belongs in evidence unless the timing, count, or size is the measured target.

Benchmark sections must follow the plan phases:

- `B0` corresponds to `P0`.
- `B1` corresponds to `P1`.
- `B2` corresponds to `P2`.
- Use item-level IDs such as `B-P1-A` when a checklist item needs separate benchmark evidence.
- Create a benchmark section only when the matching phase has benchmarkable measurements.
- Do not invent fixed metric categories; record the measurements required by the matching plan phase.

## B0 - P0 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P0 | Anvien files scanned | files | 857 | 857 | pending | fresh graph | 0 | E0-P0A-GRAPH1 |
| P0 | Anvien parsed code | files | 160 | 160 | pending | 0 parse failures | 0 | E0-P0A-GRAPH1 |
| P0 | Anvien graph nodes | nodes | 36567 | 36567 | pending | record fresh count | 0 | E0-P0A-GRAPH1 |
| P0 | Anvien graph relationships | relationships | 42272 | 42272 | pending | record fresh count | 0 | E0-P0A-GRAPH1 |
| P0 | Evaluator symbols | symbols | 175 | 175 | pending | preserve except scoped branch | 0 | E0-P0A-FD1 |
| P0 | Evaluator local relationships | relationships | 51 | 51 | pending | preserve/measure after edit | 0 | E0-P0A-FD1 |
| P0 | Evaluator linked flows | flows | 24 | 24 | pending | preserve/measure after edit | 0 | E0-P0A-FD1 |
| P0 | C73 completion attempts | attempts | 4 | 4 | pending | successor all 10 slots executable | 0 | E0-P0A-C73FAIL1 |
| P0 | C73 completion trial records | records | 0 | 0 | pending | successor 10 | 0 | E0-P0A-C73FAIL1 |
| P0 | Sealed `.73` ZIP | bytes | 2909357 | 2909357 | pending | exact hash unchanged | 0 | E0-P0A-SEAL1 |
| P0 | Sealed `.72` ZIP | bytes | recorded | recorded | pending | exact hash unchanged | 0 | E0-P0A-SEAL1 |

## B1 - P1 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P1 | Direct completion route checks | checks | 0 | pending | pending | installed/package/missing paths pass | pending | E1-P1A-ROUTE1 |
| P1 | Resolver source lines changed | lines | 0 | pending | pending | smallest branch only | pending | E1-P1A-DETECT1 |
| P1 | Focused lifecycle tests | tests | 0 | pending | pending | all pass | pending | E1-P1B-TEST1 |
| P1 | Full unit tests | tests | historical C73 335 capability tests | pending | pending | no new regression | pending | E1-P1B-TEST2 |

## B2 - P2 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P2 | Required eval cases | cases | 5 | pending | pending | 5 | pending | E2-P2A-EVAL1 |
| P2 | Required trial slots | slots | 0 executable in C73 | pending | pending | 10 | pending | E2-P2A-EVAL1 |
| P2 | Baseline trials | trials | 0 recorded in C73 | pending | pending | 10? | pending | E2-P2A-EVAL1 |
| P2 | P2P trials | trials | 0 recorded in C73 | pending | pending | 10? | pending | E2-P2A-EVAL1 |
| P2 | Unexpected writes | writes | C73 blocked before records | pending | pending | 0 | pending | E2-P2A-EVAL1 |
| P2 | P2P pass rate | ratio | unavailable | pending | pending | policy threshold | pending | E2-P2A-GATE1 |
| P2 | Case regressions | cases | unavailable | pending | pending | 0 | pending | E2-P2A-GATE1 |
| P2 | Strict Doctor | status | FAIL in C73 | pending | pending | PASS | pending | E2-P2A-INSTALL1 |
| P2 | Technical prepare | status | BLOCKED in C73 | pending | pending | PASS | pending | E2-P2A-GATE1 |
| P2 | Candidate inventory | members | 493 in `.73` | pending | pending | accounted=total | pending | E2-P2A-PACKAGE1 |
| P2 | Candidate ZIP | bytes | 2909357 in `.73` | pending | pending | exact full-byte hash recorded | pending | E2-P2B-SEAL1 |

## Non-Benchmarkable Notes

- No UI, browser, database, Docker, or network performance benchmark applies to this Python CLI/package lifecycle task.
- Approval, promotion, release, deployment, and external certification are prohibited and therefore have no benchmark row.
