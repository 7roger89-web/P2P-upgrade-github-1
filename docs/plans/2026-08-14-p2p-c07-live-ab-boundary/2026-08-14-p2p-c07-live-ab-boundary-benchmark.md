# P2P-C07 Supported Live A/B Context Boundary Benchmark Ledger

## Metadata

- Date: `2026-08-14`
- Plan: `docs/plans/2026-08-14-p2p-c07-live-ab-boundary/2026-08-14-p2p-c07-live-ab-boundary-plan.md`
- Evidence: `docs/plans/2026-08-14-p2p-c07-live-ab-boundary/2026-08-14-p2p-c07-live-ab-boundary-evidence.md`
- Benchmark: `docs/plans/2026-08-14-p2p-c07-live-ab-boundary/2026-08-14-p2p-c07-live-ab-boundary-benchmark.md`
- Actual status: `docs/plans/2026-08-14-p2p-c07-live-ab-boundary/2026-08-14-p2p-c07-live-ab-boundary-actual-status.md`

## Benchmark Rules

- Record measured counts, sizes, hashes, and observed timers only.
- Do not turn local bytes, characters, words, or tokenizer estimates into
  provider token usage.
- Do not score output quality or infer that one context mode is better.
- Provider/model/cache/cost values remain `UNKNOWN` unless the supported host
  exposes authoritative values with provenance.
- Live wall time is an end-to-end local monotonic observation, not provider
  compute time.
- Keep all trial outputs and receipts in isolated repository-local `.tmp` roots.

## B0 - P0 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|---|---|---|---:|---:|---:|---:|---:|---|
| P0 | Official `.15` ZIP size | bytes | 2,385,951 | 2,385,951 | 2,385,951 | unchanged | 0 | `E0-P0A-ART1` |
| P0 | Official `.15` ZIP SHA-256 | digest | `af4d63a882dabfde20ac237574590ec584ee2944bc4cdc30b6a07bf7f681e195` | same | same | unchanged | 0 | `E0-P0A-ART1` |
| P0 | Existing `.16-r2` ZIP size | bytes | 2,387,476 | 2,387,476 | 2,387,476 | unchanged | 0 | `E0-P0A-ART2` |
| P0 | Existing `.16-r2` ZIP SHA-256 | digest | `410572d73aa06dadbd8fe1da068fe217eabeb7efc11cf35fc9576c750a4ee8cf` | same | same | unchanged | 0 | `E0-P0A-ART2` |
| P0 | Packaged context runtime in `.15` | bytes | 2,470 | 2,470 | 2,470 | preserve-only | 0 | `E0-P0A-ART3` |
| P0 | Packaged context runtime in `.16-r2` | bytes | 2,470 | 2,470 | 2,470 | preserve-only/pre-C06 | 0 | `E0-P0A-ART3` |
| P0 | C06 packaged mode markers in `.16-r2` | count | 0 | 0 | 0 | 0 before candidate | 0 | `E0-P0A-ART3` |

## B1 - P1 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|---|---|---|---:|---:|---:|---:|---:|---|
| P1 | Candidate version | text | N/A | `8.4.7-C-codex.17` | `8.4.7-C-codex.17` | canonical next revision | N/A | `E1-P1B-PACK1` |
| P1 | Candidate artifact size | bytes | N/A | 2,395,280 | 2,395,280 | new immutable artifact | N/A | `E1-P1B-PACK1` |
| P1 | Candidate artifact SHA-256 | digest | N/A | `50eb59740034fb724dfe23d19d7f700c8143cfb9efd07f6cdf0a33d0ed041197` | same | recorded and stable | N/A | `E1-P1B-PACK1` |
| P1 | Package file inventory | files | N/A | 398 files / 399 checksums | 398 files / 399 checksums | package verification PASS | N/A | `E1-P1B-PACK1` |
| P1 | Candidate lifecycle classes | runs | N/A | `FRESH_INSTALL`, `.15 -> .17`, `.17 reinstall` | all PASS | all supported lifecycle paths | N/A | `E1-P1B-LIFE1` |

## B2 - P2 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|---|---|---|---:|---:|---:|---:|---:|---|
| P2 | Direct live-boundary test count | tests | N/A | 6/6 PASS | 6/6 PASS | all focused cases PASS | N/A | `E2-P2A-TEST1` |
| P2 | Supported host workers per trial | workers | N/A | 1 | 1 | at most 1 | N/A | `E2-P2B-HOST1` |
| P2 | Delegation depth | levels | N/A | 0 requested/observed | 0 requested/observed | <= 1 | N/A | `E2-P2B-HOST1` |

## B3 - P3 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|---|---|---|---:|---:|---:|---:|---:|---|
| P3 | Live trials executed | trials | 0 | 4 accepted (+2 discarded host-capture attempts) | 4 accepted | exactly 4 accepted | N/A | `E3-P3A-LIVE1`, `E3-P3B-LIVE1` |
| P3 | C1 A/B context fingerprint equality | boolean | N/A | false | false | false | N/A | `E3-P3A-CONTEXT1` |
| P3 | C7 A/B context fingerprint equality | boolean | N/A | false | false | false | N/A | `E3-P3B-CONTEXT1` |
| P3 | C1 live receipts with true status | count | 0 | 2 | 2 | 2 | N/A | `E3-P3A-LIVE1` |
| P3 | C7 live receipts with true status | count | 0 | 2 | 2 | 2 | N/A | `E3-P3B-LIVE1` |
| P3 | Provider token telemetry | values | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN allowed | N/A | `E3-P3A-LIVE1`, `E3-P3B-LIVE1` |
| P3 | Provider cost telemetry | values | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN allowed | N/A | `E3-P3A-LIVE1`, `E3-P3B-LIVE1` |
| P3 | Local monotonic wall time | ms | N/A | C1 A 105625; C1 B 51625; C7 A 52781; C7 B 56234 | same | observed only | N/A | `E3-P3A-LIVE1`, `E3-P3B-LIVE1` |

## B4 - P4 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|---|---|---|---:|---:|---:|---:|---:|---|
| P4 | Focused C07/context/identity tests | tests | N/A | 28/28 PASS | 28/28 PASS | all focused cases PASS | N/A | `E4-P4A-TEST1` |
| P4 | Full affected regression result | status | N/A | 101 tests PASS | 101 tests PASS | PASS or real blocker | N/A | `E4-P4A-TEST1` |
| P4 | Decision Trace cases | cases | N/A | 24/24 PASS | 24/24 PASS | DT1-DT24 PASS | N/A | `E4-P4A-TEST1` |
| P4 | Build-check artifact | bytes / SHA-256 | N/A | 2,403,894 / `8c5cfaf60e71d16dea72e4079c4afb1ff433a65d831efba8963292d019e3337d` | same | verify/doctor PASS | N/A | `E4-P4A-GATE1` |
| P4 | Canonical identities | count | 8 | 8 | 8 | 8 | 0 | `E0-P0A-GOV1`, `E4-P4A-GATE1` |
| P4 | Quorum denominator | count | 8 | 8 | 8 | 8 | 0 | `E0-P0A-GATE1` |
| P4 | Supported Supervisor verdict | status | N/A | PASS | PASS | PASS | N/A | `E4-P4B-SUP1` |

## Non-Benchmarkable Notes

- Output quality, context efficiency, token reduction, provider cost, and
  non-inferiority are intentionally not benchmarked in P2P-C07.
- A `LOCAL_SERIALIZATION_PROXY` byte measurement is descriptive only and is
  never presented as provider token usage.
- `UNKNOWN` telemetry is an acceptable final value when the supported host does
  not expose authoritative provider-owned fields.
