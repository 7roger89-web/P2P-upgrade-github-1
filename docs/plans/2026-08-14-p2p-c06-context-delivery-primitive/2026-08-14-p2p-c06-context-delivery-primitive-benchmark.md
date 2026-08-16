# P2P-C06 Minimal Executable Context-Efficient Behavioral Primitive Benchmark Ledger

## Metadata

- Date: `2026-08-14`
- Plan: `docs/plans/2026-08-14-p2p-c06-context-delivery-primitive/2026-08-14-p2p-c06-context-delivery-primitive-plan.md`
- Evidence: `docs/plans/2026-08-14-p2p-c06-context-delivery-primitive/2026-08-14-p2p-c06-context-delivery-primitive-evidence.md`
- Benchmark: `docs/plans/2026-08-14-p2p-c06-context-delivery-primitive/2026-08-14-p2p-c06-context-delivery-primitive-benchmark.md`
- Actual status: `docs/plans/2026-08-14-p2p-c06-context-delivery-primitive/2026-08-14-p2p-c06-context-delivery-primitive-actual-status.md`

## Benchmark Rules

This ledger records measurements only. It does not claim provider tokens, cost, speed, or quality. Byte counts are explicitly `LOCAL_SERIALIZATION_PROXY` measurements of deterministic local JSON serialization. No provider/model A/B is run.

## B0 - P0 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P0 | Main workflow indexed source symbols | count | 267 | 267 | 267 | record current | 0 | E0-P0A-GRAPH1 |
| P0 | Context pointer module symbols | count | 21 | 21 | 21 | record current | 0 | E0-P0A-GRAPH2 |
| P0 | Existing artifact identities preserved | SHA-256 count | 2 | 2 | 2 | 2 | 0 | E0-P0A-BASE1, E0-P0A-CAND1 |

## B1 - P1 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P1 | Accepted context modes | count | 0 | 2 | 2 | exactly 2 | +2 | E1-P1A-CONTEXT1 |
| P1 | Scenarios with A fingerprint != B fingerprint | count | 0 | 12 | 12 | 12 | +12 | E2-P2A-SCENARIO1..E2-P2A-SCENARIO12 |
| P1 | A/B same legitimate source-binding count | count | N/A | equal in 12/12 | equal in 12/12 | equal | PASS | E1-P1A-CONTEXT3, E2-P2A-SCENARIO1..12 |
| P1 | B initial serialized view | bytes (`LOCAL_SERIALIZATION_PROXY`) | N/A | 3252-3991 across C1-C12 | 3252-3991 | less than A in 12/12 | PASS; delta 2821 bytes in each fixture | E2-P2A-SCENARIO1..E2-P2A-SCENARIO12 |

## B2 - P2 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P2 | Canonical scenario definitions exercised | count | 0 | 12 | 12 | 12 | +12 | E2-P2A-SCENARIO1..E2-P2A-SCENARIO12 |
| P2 | Required-fact preservation failures | count | N/A | 0 | 0 | 0 | PASS | E2-P2A-NEGATIVE1 |
| P2 | Unknown-mode silent fallbacks | count | N/A | 0 | 0 | 0 | PASS | E2-P2A-NEGATIVE6 |
| P2 | Canonical quorum denominator | count | 8 | 8 | 8 | 8 | 0 | existing capability tests, E2-P2B-REGRESSION3 |

## Non-Benchmarkable Notes

- Provider input tokens, cached tokens, output tokens, cost, latency, quality, and non-inferiority are not measured in this Goal and remain UNKNOWN.
- Docker, browser, UI, database, and Playwright metrics are not applicable to this Python package/runtime slice.
- Package candidate version/artifact/SHA-256 are not created by this Goal; existing `.15` and `.16-r2` hashes are preservation evidence only.

## B1 Measurement Detail

The deterministic in-memory C1-C12 fixture run reported `all_distinct=True`, `all_smaller=True`, baseline proxy sizes from 6073 to 6812 bytes, and experimental proxy sizes from 3252 to 3991 bytes. The fixture's deferred history block contributes a constant 2821-byte local JSON difference in this test data. These are structural serialization observations only; they are not provider tokens, cost, speed, quality, or live A/B results.
