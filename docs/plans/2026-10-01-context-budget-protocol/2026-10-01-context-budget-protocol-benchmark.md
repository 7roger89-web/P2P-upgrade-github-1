# Context Budget Protocol Benchmark Ledger

## Metadata

- Date: `2026-10-01`
- Plan: `docs/plans/2026-10-01-context-budget-protocol/2026-10-01-context-budget-protocol-plan.md`
- Evidence: `docs/plans/2026-10-01-context-budget-protocol/2026-10-01-context-budget-protocol-evidence.md`
- Benchmark: `docs/plans/2026-10-01-context-budget-protocol/2026-10-01-context-budget-protocol-benchmark.md`
- Actual status: `docs/plans/2026-10-01-context-budget-protocol/2026-10-01-context-budget-protocol-actual-status.md`

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
| P0 | context-policy authority surfaces | files | 4 | 4 | pending | 4 aligned, 0 new framework files | 0 new authority frameworks | E0-P0A-SRC1..E0-P0A-SRC4 |

## B1 - P1 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P1 | context-policy authority surfaces | files | 4 | 4 | pending | 4 aligned, 0 new framework files | 0 new authority frameworks | E0-P0A-SRC1..E0-P0A-SRC4 |

## B2 - P2 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P2 | context-policy authority surfaces | files | 4 | 4 | pending | 4 aligned, 0 new framework files | 0 new authority frameworks | E0-P0A-SRC1..E0-P0A-SRC4 |

## Non-Benchmarkable Notes

Use this section only for phases that are not benchmarkable. Do not invent metrics.

No runtime performance benchmark is applicable. The only useful inventory measurement is authority/guidance surface count and the requirement that no new packet/schema/state-store framework be introduced.
