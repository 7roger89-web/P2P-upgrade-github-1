# Real Context-Efficiency A/B Benchmark & Quality Non-Inferiority Certification Benchmark Ledger

## Metadata

- Date: `2026-08-14`
- Plan: `docs/plans/2026-08-14-real-context-efficiency-ab-quality-noninferiority/2026-08-14-real-context-efficiency-ab-quality-noninferiority-plan.md`
- Evidence: `docs/plans/2026-08-14-real-context-efficiency-ab-quality-noninferiority/2026-08-14-real-context-efficiency-ab-quality-noninferiority-evidence.md`
- Benchmark: `docs/plans/2026-08-14-real-context-efficiency-ab-quality-noninferiority/2026-08-14-real-context-efficiency-ab-quality-noninferiority-benchmark.md`
- Actual status: `docs/plans/2026-08-14-real-context-efficiency-ab-quality-noninferiority/2026-08-14-real-context-efficiency-ab-quality-noninferiority-actual-status.md`

## Benchmark Rules

- This ledger records measured values only.
- The canonical suite is the existing 12-scenario/48-proxy-trial suite; it is not duplicated.
- Historical proxy measurements are not live A/B measurements.
- No live paired trial was counted because the executable-condition gate failed.
- Unavailable values are `UNKNOWN`, never estimated.
- Quality rubric: Q1–Q10, fixed 0–4 scale.
- Pre-registered non-inferiority margin: B aggregate mean >= A aggregate mean - 0.25, with no critical acceptance or safety failure. Not applied without real outputs.

## B0 - P0 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P0 | Canonical scenarios | scenarios | 12 | 12 | 12 | 12 | 0 | E0-P0A-CANON1 |
| P0 | Historical proxy trials | trials | 48 | 48 | 48 | historical only | 0 | E0-P0A-PROXY1 |
| P0 | Historical `runtime_task_execution` | boolean | false | false | false | true for live evidence | UNKNOWN | E0-P0A-PROXY1 |

## B1 - P1 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P1 | Real paired scenarios executed | scenarios | 0 | 0 | 0 | 12 | 0 | E1-P1A-GATE1 |
| P1 | Real scored trials | trials | 0 | 0 | 0 | contract-defined paired trials | 0 | E1-P1A-GATE1 |
| P1 | A/B executable conditions proven | conditions | 0 | 0 | 0 | 2 | 0 | E1-P1A-RUNTIME1 |
| P1 | Input tokens | tokens | UNKNOWN | UNKNOWN | UNKNOWN | observed | UNKNOWN | E1-P1A-UNKNOWN1 |
| P1 | Cached input tokens | tokens | UNKNOWN | UNKNOWN | UNKNOWN | observed | UNKNOWN | E1-P1A-UNKNOWN1 |
| P1 | Output tokens | tokens | UNKNOWN | UNKNOWN | UNKNOWN | observed | UNKNOWN | E1-P1A-UNKNOWN1 |
| P1 | Total tokens | tokens | UNKNOWN | UNKNOWN | UNKNOWN | observed | UNKNOWN | E1-P1A-UNKNOWN1 |
| P1 | Provider/model calls | calls | UNKNOWN | UNKNOWN | UNKNOWN | observed | UNKNOWN | E1-P1A-UNKNOWN1 |
| P1 | Child-agent calls | calls | UNKNOWN | UNKNOWN | UNKNOWN | observed | UNKNOWN | E1-P1A-UNKNOWN1 |
| P1 | Tool calls per trial | calls | UNKNOWN | UNKNOWN | UNKNOWN | observed | UNKNOWN | E1-P1A-UNKNOWN1 |
| P1 | Provider wall time | duration | UNKNOWN | UNKNOWN | UNKNOWN | observed | UNKNOWN | E1-P1A-UNKNOWN1 |
| P1 | Retry/failure counts | attempts | UNKNOWN | UNKNOWN | UNKNOWN | observed | UNKNOWN | E1-P1A-UNKNOWN1 |
| P1 | Main-context growth | host units | UNKNOWN | UNKNOWN | UNKNOWN | observed | UNKNOWN | E1-P1A-UNKNOWN1 |
| P1 | Authoritative provider cost | currency | UNKNOWN | UNKNOWN | UNKNOWN | observed | UNKNOWN | E1-P1A-UNKNOWN1 |

## Non-Benchmarkable Notes

- No real A/B measurement exists for quality, input/cache/output/total tokens, tools, retrieval, delegation, wall time, retries, failures, compaction, context growth, or cost.
- The existing 48-trial proxy inventory remains useful only as evaluator-contract history and must not be used to certify efficiency or quality.
- The 12 canonical scenario slots are preserved and explicitly not executed for this Goal: C1–C12.
