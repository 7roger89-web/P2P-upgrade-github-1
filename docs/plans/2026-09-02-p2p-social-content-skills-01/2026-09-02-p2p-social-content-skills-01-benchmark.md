# P2P Social Content Skills Phase 1 Benchmark Ledger

## Metadata

- Date: `2026-09-02`
- Plan: `Docs/plans/2026-09-02-p2p-social-content-skills-01/2026-09-02-p2p-social-content-skills-01-plan.md`
- Evidence: `Docs/plans/2026-09-02-p2p-social-content-skills-01/2026-09-02-p2p-social-content-skills-01-evidence.md`
- Benchmark: `Docs/plans/2026-09-02-p2p-social-content-skills-01/2026-09-02-p2p-social-content-skills-01-benchmark.md`
- Actual status: `Docs/plans/2026-09-02-p2p-social-content-skills-01/2026-09-02-p2p-social-content-skills-01-actual-status.md`

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
| P0 | Canonical main identity | commit | `0ee414147ae308ab1f6035d1e7776292752bd8da` | `0ee414147ae308ab1f6035d1e7776292752bd8da` | pending | exact expected | `0` | `E0-P0A-GIT1` |
| P0 | Canonical tree identity | tree | `f34719776bee67a731c4049b79165bd3deaa3074` | `f34719776bee67a731c4049b79165bd3deaa3074` | pending | exact expected | `0` | `E0-P0A-GIT1` |
| P0 | Upstream skills audited | skill files | `5` | `5` | pending | `5` | `0` | `E0-P0A-UP2` |
| P0 | Canonical registry records | records | `67` | `67` | pending | preserve plus accepted family | `0` | `E0-P0A-SRC1` |
| P0 | Anvien graph nodes | nodes | `50,011` | `50,011` | pending | fresh current graph | `0` | `E0-P0A-ANV1` |
| P0 | Anvien graph relationships | relationships | `58,998` | `58,998` | pending | fresh current graph | `0` | `E0-P0A-ANV1` |

## B1 - P1 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P1 | Accepted capability projections | capabilities | `0` | `5` | pending | `5` | `+5` | `E1-P1A-SRC3` |
| P1 | Raw upstream SKILL.md files vendored | files | `0` | `0` | pending | `0` | `0` | `E1-P1A-SRC1` |
| P1 | Adapted entrypoints | files | `0` | `5` | pending | `5` | `+5` | `E1-P1A-SRC1` |
| P1 | Per-capability snapshot roots | roots | `0` | `5` | pending | `5` | `+5` | `E1-P1A-SRC1` |
| P1 | Full family content loaded during discovery | entrypoints | `0` | `0` | pending | `0` | `0` | `E1-P1A-ROUTE1..E1-P1A-ROUTE4` |
| P1 | Selected capability entrypoints loaded for one-capability test | entrypoints | `0` | `1` | pending | `1` | `+1` | `E1-P1B-TEST4` |
| P1 | Focused test cases | tests | `0` | `12` | pending | `12` | `+12` | `E1-P1B-TEST1` |
| P1 | Anvien graph nodes after final refresh | nodes | `50,011` | `51,347` | pending | fresh current graph | `+1,336` | `E1-P1B-DETECT1` |
| P1 | Anvien graph relationships after final refresh | relationships | `58,998` | `59,357` | pending | fresh current graph | `+359` | `E1-P1B-DETECT1` |

## B2 - P2 Benchmarks

No P2 phase is authorized for Issue #60.

## Non-Benchmarkable Notes

- UI, browser, Docker, database, network, provider, publishing, and social-account metrics are not applicable to this source-only capability projection.
- Supervisor verdict, registry validity, route behavior, and fail-closed behavior are validation evidence, not performance benchmarks.
