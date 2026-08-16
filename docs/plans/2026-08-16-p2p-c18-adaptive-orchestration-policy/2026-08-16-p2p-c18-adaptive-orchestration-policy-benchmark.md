# C18 Adaptive Orchestration Policy Foundation Benchmark Ledger

## Metadata

- Date: `2026-08-16`
- Plan: `docs/plans/2026-08-16-p2p-c18-adaptive-orchestration-policy/2026-08-16-p2p-c18-adaptive-orchestration-policy-plan.md`
- Evidence: `docs/plans/2026-08-16-p2p-c18-adaptive-orchestration-policy/2026-08-16-p2p-c18-adaptive-orchestration-policy-evidence.md`
- Benchmark: `docs/plans/2026-08-16-p2p-c18-adaptive-orchestration-policy/2026-08-16-p2p-c18-adaptive-orchestration-policy-benchmark.md`
- Actual status: `docs/plans/2026-08-16-p2p-c18-adaptive-orchestration-policy/2026-08-16-p2p-c18-adaptive-orchestration-policy-actual-status.md`

## Benchmark Rules

Only measured fixture counts, outcome counts, serialized-byte proxies, package counts, and hashes belong here. Synthetic policy results are not universal performance claims.

## B0 - P0 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|---|---|---:|---:|---:|---:|---:|---:|---|
| P0 | Required adaptive AO cases | cases | 0 | 20 | 20 | 20 | +20 | E0-P0A-DECISION1 |
| P0 | Maximum certified execution workers | workers | 2 | 2 | 2 | 2 | 0 | E0-P0A-SURFACE2 |

## B1 - P1 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|---|---|---:|---:|---:|---:|---:|---:|---|
| P1 | AO fixture count | cases | 20 | 20 | 20 | 20 | 0 | E1-P1B-AO1 |
| P1 | Naive policies compared | policies | 0 | 5 | 5 | 5 | +5 | E1-P1B-NAIVE1 |
| P1 | Local context measurement label | label | absent | LOCAL_SERIALIZATION_PROXY | LOCAL_SERIALIZATION_PROXY | LOCAL_SERIALIZATION_PROXY | added | E1-P1A-TEST1 |

## B2 - P2 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|---|---|---:|---:|---:|---:|---:|---:|---|
| P2 | Focused C18 test cases | tests | 5 | 5 | 5 | all pass | 0 | E2-P2-FOCUSED1 |
| P2 | Full regression tests | tests | 253 | 253 | 253 | all pass | 0 | E2-P2-FOCUSED1 |
| P2 | Official `.19` SHA changes | changes | 0 | 0 | 0 | 0 | 0 | E2-P2-LINEAGE1 |
| P2 | C17 candidate SHA changes | changes | 0 | 0 | 0 | 0 | 0 | E2-P2-LINEAGE1 |
| P2 | New C18 candidate package size | bytes | none | 2526510 | 2526510 | recorded | +2526510 | E2-P2-PACKAGE1 |
| P2 | Packaged file inventory | files | 412 | 413 | 413 | includes policy module | +1 | E2-P2-PACKAGE1 |

## Non-Benchmarkable Notes

- No real token, cost, latency, provider ranking, or model-quality benchmark is authorized by C18.
- No live host delegation or parallel benchmark is claimed.
