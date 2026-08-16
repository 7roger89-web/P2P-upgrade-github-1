# P2P AESTHETICA — Final Behavioral Value Certification Benchmark Ledger

## Metadata

- Date: `2026-08-13`
- Plan: `docs/plans/2026-08-13-p2p-aesthetica-final-behavioral-value-certification/2026-08-13-p2p-aesthetica-final-behavioral-value-certification-plan.md`
- Evidence: `docs/plans/2026-08-13-p2p-aesthetica-final-behavioral-value-certification/2026-08-13-p2p-aesthetica-final-behavioral-value-certification-evidence.md`
- Benchmark: `docs/plans/2026-08-13-p2p-aesthetica-final-behavioral-value-certification/2026-08-13-p2p-aesthetica-final-behavioral-value-certification-benchmark.md`
- Actual status: `docs/plans/2026-08-13-p2p-aesthetica-final-behavioral-value-certification/2026-08-13-p2p-aesthetica-final-behavioral-value-certification-actual-status.md`

## Benchmark Rules

- Record measured values only; do not infer Aesthetica value from profile existence or successful process startup.
- No A/B benchmark is valid until P0 exact trust is PASS.
- `N/A` means the metric does not apply; `NOT RUN` means the gate prevented measurement.
- Runtime identity counts and trust state are host measurements, not product-quality measurements.

## B0 - P0 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P0 | exact persistent trusted-project entry | boolean | expected true | false | false | true | -1 | E0-P0A-TRUST3 |
| P0 | exact project-local config layer active | boolean | expected true | false | false | true | -1 | E0-P0A-HOST4 |
| P0 | project-local Aesthetica profile present | file count | 1 | 1 | 1 | 1 | 0 | E0-P0A-PROFILE1 |
| P0 | bounded real child in this Goal | executions | 0 | 0 | 0 | 1 | 0 | E0-P0A-GATE1 |
| P0 | A/B scenarios executed in this Goal | scenarios | 0 | 0 | 0 | 6 | 0 | E0-P0A-GATE1 |

## B1 - P1 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P1 | A/B scenario pairs | pairs | NOT RUN | NOT RUN | NOT RUN | 6 | NOT RUN | P0 blocked |
| P1 | blinded review packets | packets | NOT RUN | NOT RUN | NOT RUN | 12 | NOT RUN | P0 blocked |
| P1 | real Aesthetica outputs with USER NEED chain | outputs | NOT RUN | NOT RUN | NOT RUN | 6 | NOT RUN | P0 blocked |

## B2 - P2 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P2 | fallback runs | runs | NOT RUN | NOT RUN | NOT RUN | 1 | NOT RUN | P0 blocked |
| P2 | repeated real Aesthetica runs | runs | NOT RUN | NOT RUN | NOT RUN | 2 | NOT RUN | P0 blocked |
| P2 | canonical identities | count | 8 | 8 | 8 | 8 | 0 | verified baseline / scope preserved |
| P2 | canonical quorum denominator | count | 8 | 8 | 8 | 8 | 0 | verified baseline / scope preserved |

## Non-Benchmarkable Notes

- Quality dimensions, beginner benefit, feasibility, and routing value are not measured in this blocked run.
- No score or zero-missing-reference optimization is permitted; the value study was not started.

## B3 — Current behavioral certification measurements

| Metric | Result | Evidence |
|---|---:|---|
| frozen scenarios | 10 | `decoded-results.md` |
| rubric dimensions | 15 | `rubric.json` |
| real Aesthetica B receipts | 9/9 PASS | execution ledger / raw results |
| independent blind review | PASS | blind review report |
| UI aggregate A mean | 3.616 | decoded results |
| UI aggregate B mean | 3.659 | decoded results |
| UI aggregate delta | +0.043 | decoded results |
| HIGH_VALUE cases | 0 | decoded results |
| MODERATE_VALUE cases | 2 | S5, S7 |
| canonical identities | 8 | approved ZIP manifest |
| quorum denominator | 8 | approved ZIP manifest |
| full quorum | 8/8 | approved ZIP manifest |

Unknown telemetry remains explicitly unmeasured: wall time, token count, provider-call count, context operations, and output-length inflation.
