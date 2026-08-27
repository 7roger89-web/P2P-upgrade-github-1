# P2P-CT01 R05 Durable Control Tower Candidate Convergence Benchmark Ledger

## Metadata

- Date: 2026-08-27
- Plan: docs/plans/2026-08-27-p2p-ct01-r05-candidate-convergence/2026-08-27-p2p-ct01-r05-candidate-convergence-plan.md
- Evidence: docs/plans/2026-08-27-p2p-ct01-r05-candidate-convergence/2026-08-27-p2p-ct01-r05-candidate-convergence-evidence.md
- Benchmark: docs/plans/2026-08-27-p2p-ct01-r05-candidate-convergence/2026-08-27-p2p-ct01-r05-candidate-convergence-benchmark.md
- Actual status: docs/plans/2026-08-27-p2p-ct01-r05-candidate-convergence/2026-08-27-p2p-ct01-r05-candidate-convergence-actual-status.md

## Benchmark Rules

This ledger records measurements only. Pass/fail narrative remains in the
evidence ledger. Historical A/B measurements remain distinct from fresh R05
candidate measurements.

## B0 - P0 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|---|---|---:|---:|---:|---:|---:|---:|---|
| P0 | Canonical protected files | files | 1180 | 1180 | pending | exact current lock | pending | E0-P0A-L1 |
| P0 | Canonical virtual hashes | hashes | 2 | 2 | pending | exact current lock | pending | E0-P0A-L1 |
| P0 | A/B relation left commits | commits | 3 | 3 | pending | record exact relation | 0 | E0-P0A-REL2 |
| P0 | A/B relation right commits | commits | 3 | 3 | pending | record exact relation | 0 | E0-P0A-REL2 |
| P0 | Anvien graph files scanned | files | N/A | 969 | pending | refresh before graph use | pending | E0-P0A-GR4 |
| P0 | Anvien graph relationships | relationships | N/A | 46925 | pending | refresh before graph use | pending | E0-P0A-GR4 |

## B1 - P1 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|---|---|---:|---:|---:|---:|---:|---:|---|
| P1 | Exact protected path additions | paths | 0 | 2 | pending | 2 | +2 | E1-P1A-GOV1 |
| P1 | Broad whitelist additions | paths | 0 | 0 | pending | 0 | 0 | E1-P1A-GOV2 |
| P1 | Candidate protected files after lock generation | files | 1180 | pending | pending | generated current count | pending | E1-P1C-LOCK2 |
| P1 | Candidate virtual hashes after lock generation | hashes | 2 | pending | pending | generated current count | pending | E1-P1C-LOCK2 |

## B2 - P2 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|---|---|---:|---:|---:|---:|---:|---:|---|
| P2 | Focused CT tests | tests | 37 reported | pending | pending | all applicable pass | pending | E2-P2A-TEST1 |
| P2 | Attachment cases | cases | 7 reported | pending | pending | 7/7 if applicable | pending | E2-P2A-TEST2 |
| P2 | Rotation cases | cases | 6 reported | pending | pending | 6/6 if applicable | pending | E2-P2A-TEST3 |
| P2 | Governance protected files | files | 1180 | pending | pending | verifier current | pending | E2-P2A-TEST7 |
| P2 | Baseline validator failures | failures | 7 inherited reported | pending | pending | attributed, not repaired | pending | E2-P2B-BASE1 |
| P2 | Candidate-caused failures | failures | N/A | pending | pending | 0 for READY | pending | E2-P2B-ATTR1 |
| P2 | Implementation tree identity | tree SHA | A tree | pending | pending | sealed exact tree | pending | E2-P2C-SEAL2 |
| P2 | Handoff bytes | bytes | N/A | pending | pending | non-empty Markdown packet | pending | E2-P2C-HANDOFF2 |

## Non-Benchmarkable Notes

- No public UI, browser, Docker, or Playwright surface is in scope for this
  control-tower library/CLI reconciliation.
- A missing applicable eval or fresh authority proof is recorded as NOT_PROVEN
  or UNKNOWN; it is never converted into a benchmark PASS.
