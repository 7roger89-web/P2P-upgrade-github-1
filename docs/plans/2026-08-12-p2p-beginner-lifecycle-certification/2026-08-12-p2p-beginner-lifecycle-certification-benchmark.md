# P2P Beginner Lifecycle Behavioral Certification Benchmark Ledger

## Metadata

- Date: `2026-08-12`
- Plan: `docs/plans/2026-08-12-p2p-beginner-lifecycle-certification/2026-08-12-p2p-beginner-lifecycle-certification-plan.md`
- Evidence: `docs/plans/2026-08-12-p2p-beginner-lifecycle-certification/2026-08-12-p2p-beginner-lifecycle-certification-evidence.md`
- Benchmark: `docs/plans/2026-08-12-p2p-beginner-lifecycle-certification/2026-08-12-p2p-beginner-lifecycle-certification-benchmark.md`
- Actual status: `docs/plans/2026-08-12-p2p-beginner-lifecycle-certification/2026-08-12-p2p-beginner-lifecycle-certification-actual-status.md`

## Benchmark Rules

Record measured counts, statuses, hashes, and durations only. Narrative interpretation belongs in evidence and the certification report. `N/A` means the product surface is intentionally outside this CLI/state-only Goal.

## B0 - P0 Baseline Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|---|---|---:|---:|---:|---:|---:|---:|---|
| P0 | Corrected beginner prompts executed | prompts | 4 | 4 | pending | 4 | 0 | `E0-P0A-RUN1..E0-P0A-RUN4` |
| P0 | Longitudinal same-project journeys | journeys | 0 | 1 | 1 | >=1 | +1 | `E2-P2A-CERT5` |
| P0 | Dedicated certification harness | artifact | 0 | 1 | 1 | 1 | +1 | `E1-P1A-RUN1` |
| P0 | Goal contracts exposing technical question fields | fields | 0 | 0 | pending | 0 | 0 | `E0-P0A-RUN1..E0-P0A-RUN4` |
| P0 | Canonical denominator | agents | 8 | 8 | pending | 8 | 0 | `E0-P0A-DOCTOR1` |
| P0 | Full canonical quorum | ratio | 8/8 | 8/8 | pending | 8/8 | 0 | `E0-P0A-DOCTOR1` |
| P0 | Prior full regression | checks | 43/43 | 43/43 | pending | 43/43 | 0 | `E0-P0A-REG1` |
| P0 | Release artifact SHA-256 | hash | `1d1d00913b215e513a2441f194125b96e9e7999a0659ae713d3e10d2de4dcccb` | same | same | unchanged | 0 | `E2-P2B-REG4` |

## B1 - P1 Harness Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|---|---|---:|---:|---:|---:|---:|---:|---|
| P1 | Synthetic scenario count | scenarios | 0 | 4 | 4 | >=4 | +4 | `E2-P2A-CERT1` |
| P1 | Longitudinal stages on one project | stages | 0 | 15 | 15 | >=8 | +15 | `E2-P2A-CERT5` |
| P1 | Machine rows with minimum schema | rows | 0 | 205/205 | 205/205 | 100% | PASS | `E2-P2A-CERT6` |
| P1 | Reports containing secrets/CoT markers | reports | 0 | 0 | 0 | 0 | 0 | `E2-P2B-REG8` |
| P1 | Protected paths written by harness | paths | 0 | 0 | 0 | 0 | 0 | `E2-P2A-CERT8` |

## B2 - P2 Certification Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|---|---|---:|---:|---:|---:|---:|---:|---|
| P2 | Harness result | status | not-run | PASS | PASS | PASS | PASS | `E2-P2A-CERT1` |
| P2 | Beginner readiness | status | not-assessed | CERTIFIED_WITH_LIMITATIONS | CERTIFIED_WITH_LIMITATIONS | honest allowed class | classified | `E2-P2A-CERT2` |
| P2 | Critical failures | count | 0 observed | 0 | 0 | 0 for certification | 0 | `E2-P2A-CERT3` |
| P2 | Existing regression | checks | 43/43 | 45/45 | 45/45 | current suite total | +2 tests | `E2-P2B-REG1` |
| P2 | Canonical identities | count | 8 | 8 | 8 | 8 | 0 | `E2-P2B-REG2` |
| P2 | Aesthetica denominator inclusion | boolean | false | false | false | false | 0 | `E2-P2B-REG3` |
| P2 | Release SHA-256 changed | boolean | false | false | false | false | 0 | `E2-P2B-REG4` |
| P2 | User-project writes | count | 0 | 0 | 0 | 0 | 0 | `E2-P2B-REG5` |

## Non-Benchmarkable Notes

- Browser screenshots, Docker build/runtime, database round trips, and real deployment are `N/A` because this Goal evaluates the CLI/state-only P2P development source.
- Real code implementation quality is intentionally not represented by a synthetic fixture PASS; it is a readiness limitation unless fresh runtime evidence proves otherwise.
