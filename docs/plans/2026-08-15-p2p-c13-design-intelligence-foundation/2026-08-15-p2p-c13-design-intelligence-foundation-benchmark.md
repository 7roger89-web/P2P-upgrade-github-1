# P2P-C13 Beginner-First Design Intelligence & NUI Faculty Routing Foundation Benchmark Ledger

## Metadata

- Date: `2026-08-15`
- Plan: `docs/plans/2026-08-15-p2p-c13-design-intelligence-foundation/2026-08-15-p2p-c13-design-intelligence-foundation-plan.md`
- Evidence: `docs/plans/2026-08-15-p2p-c13-design-intelligence-foundation/2026-08-15-p2p-c13-design-intelligence-foundation-evidence.md`
- Benchmark: `docs/plans/2026-08-15-p2p-c13-design-intelligence-foundation/2026-08-15-p2p-c13-design-intelligence-foundation-benchmark.md`
- Actual status: `docs/plans/2026-08-15-p2p-c13-design-intelligence-foundation/2026-08-15-p2p-c13-design-intelligence-foundation-actual-status.md`

## Benchmark Rules

The benchmark file records measurements only. It does not claim universal design superiority, and it does not treat build/test duration as a product-performance result. Exact hashes and counts are measured inventory evidence; efficacy claims require a separate matched empirical evaluation and are out of scope for C13.

## B0 - P0 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P0 | Package graph nodes | count | 13,368 | 13,368 | 13,368 | inventory only | 0 | `E0-P0A-GRAPH1` |
| P0 | Package graph relationships | count | 15,203 | 15,203 | 15,203 | inventory only | 0 | `E0-P0A-GRAPH1` |
| P0 | System graph nodes | count | 6,613 | 6,613 | 6,613 | inventory only | 0 | `E0-P0A-GRAPH2` |
| P0 | Upstream faculty bodies | count | 174 | 174 | 174 | preserve breadth | 0 | `E0-P0A-UP2` |
| P0 | Upstream graph raw SHA-256 | hash | `c90185bdda45ccd8d86716d4b565d2ac33c99644e732329ad7d8949a6a8117c6` | same | same | exact frozen revision | 0 | `E0-P0A-UP3` |
| P0 | Router local relationships | count | 6 | 6 | 6 | impact baseline | 0 | `E0-P0A-IMPACT1` |

## B1 - P1 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P1 | Valid registry entries | count | 0 local | 174 | 174 | 174 | +174 | `E1-P1A-VALID1` |
| P1 | Kernel faculties retained | count | 0 local | 13 | 13 | 13 | +13 | `E1-P1A-VALID1` |
| P1 | Registry faculty-body preload | count | 0 local | 0 | 0 | 0 | 0 | `E1-P1A-VALID2` |
| P1 | Parent graph cycles | count | unknown | 0 | 0 | 0 | resolved | `E1-P1A-VALID1` |
| P1 | Upstream strategies evaluated | count | 0 local | 6 | 6 | >=5 | +6 | `E1-P1B-STRAT1` |

## B2 - P2 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P2 | Profile fingerprint stages | count | 0 | 3 | 3 | 3 (raw/profile/route) | +3 | `E2-P2A-PROFILE2` |
| P2 | Disposition classes | count | 0 | 5 | 5 | 5 | +5 | `E2-P2B-DISP1` |
| P2 | Render preflight states | count | 0 | 4 | 4 | 4 | +4 | `E2-P2B-LIFE2` |
| P2 | Critique dimensions | count | 0 | 10 | 10 | vector/no universal score | +10 dimensions | `E2-P2B-LIFE3` |

## B3 - P3 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P3 | Router entry points | count | 1 | 1 | 1 | 1 | 0 | `E3-P3A-ROUTE1` |
| P3 | Synthetic fixture families | count | 0 | 2 | 2 | 2 contrasting families | +2 | `E3-P3C-FIX1` |
| P3 | Focused design cases | count | 0 | 12 | 12 | D1-D12 intent | +12 | `E3-P3C-FIX2` |
| P3 | Focused structural cases | count | 0 | 26 | 26 | F1-F26 intent | +26 | `E3-P3C-FIX2` |
| P3 | Focused tests | count | 0 | 15 passed | 15 passed | all focused assertions | +15 | `E3-P3C-D1-D12` |
| P3 | Activated faculty count, Logistics-like | count | unknown | 44 | 44 | bounded subset <174 | measured | `E3-P3C-FIX1` |
| P3 | Activated faculty count, consumer | count | unknown | 37 | 37 | bounded subset <174 and differs | measured | `E3-P3C-FIX1` |

## B4 - P4 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P4 | Full applicable test count | count | pending | 174/174 | 174/174 | record actual | PASS | `E4-P4A-TEST1` |
| P4 | Targeted C13 tests | count | pending | 15/15 | 15/15 | all focused assertions | PASS | `E4-P4A-TEST2` |
| P4 | Preserved regression tests | count | pending | 87/87 | 87/87 | affected regression groups | PASS | `E4-P4A-TEST2` |
| P4 | Package/doctor result | status | pending | PASS | PASS | PASS or exact blocker | PASS | `E4-P4A-GATE1`, `E4-P4A-GATE3` |
| P4 | Candidate package | size/hash | unavailable in P0 | 2,464,587 bytes / `c4be6ead139fd97570907f500b857a6d6bc0e4527067bd83337d4e04150d5339` | same | unpromoted evidence only | measured | `E4-P4A-GATE3` |
| P4 | Docker runtime evidence | status | unavailable in P0 | N/A | N/A | only if real runtime exists | unavailable | `E0-P0A-BLOCK1` |
| P4 | Git commit evidence | status | unavailable in P0 | BLOCKED: no Git metadata | BLOCKED: no Git metadata | exact hash or blocker | blocker | `E4-P4A-GATE4` |
| P4 | Workflow helper | status | unavailable in P0 | BLOCKED / C13 run timeout | BLOCKED / C13 run timeout | exact result | blocker | `E4-P4A-GATE5` |

## Non-Benchmarkable Notes

- C13 does not run an expensive external efficacy benchmark. Upstream V10 findings are used as design/evaluation principles only: falsifiable hypotheses, generation/evaluation isolation, mutation/ablation, blind comparison, matched units, and bounded claims.
- Render quality, accessibility completeness, and usability are not reduced to a scalar score in this foundation. They require actual artifact/evidence surfaces in a future runtime-enabled task.
- Test/build timings may be recorded in evidence if useful, but they are not benchmark targets for C13.
