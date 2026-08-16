# P2P Aesthetica — Real Runtime Identity Certification Benchmark Ledger

## Metadata

- Date: `2026-08-13`
- Plan: `docs/plans/2026-08-13-p2p-aesthetica-real-runtime-identity-certification/2026-08-13-p2p-aesthetica-real-runtime-identity-certification-plan.md`
- Evidence: `docs/plans/2026-08-13-p2p-aesthetica-real-runtime-identity-certification/2026-08-13-p2p-aesthetica-real-runtime-identity-certification-evidence.md`
- Benchmark: `docs/plans/2026-08-13-p2p-aesthetica-real-runtime-identity-certification/2026-08-13-p2p-aesthetica-real-runtime-identity-certification-benchmark.md`
- Actual status: `docs/plans/2026-08-13-p2p-aesthetica-real-runtime-identity-certification/2026-08-13-p2p-aesthetica-real-runtime-identity-certification-actual-status.md`

## Benchmark Rules

This ledger records measured counts, sizes, hashes, and readiness outcomes only. Command narrative and pass/fail explanation belong in the evidence ledger.

## B0 - P0 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P0 | Baseline artifact size | bytes | 2,336,913 | 2,336,913 | 2,336,913 | 2,336,913 | 0 | `E0-P0A-PKG1` |
| P0 | Baseline artifact SHA-256 match | boolean | true | true | true | true | 0 | `E0-P0A-PKG1` |
| P0 | Canonical identity count in profile inventory | count | 8 | 8 | 8 | 8 | 0 | `E0-P0A-CAN1` |

## B1 - P1 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P1 | Package contains Aesthetica profile | boolean | true | true | true | true | 0 | `E1-P1A-PKG1` |
| P1 | Fresh-install profile resolution | boolean | not previously certified | true | true | N/A | N/A | `E1-P1B-RES3` |
| P1 | Required developer-only runtime references | count | 0 expected | 0 | 0 | 0 | 0 | `E1-P1A-PKG2` |

## B2 - P2 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P2 | Real custom-agent executions proven | count | 0 | 0 | 0 | >=1 for PASS | 0; blocker | `E2-P2A-EXEC1` |
| P2 | Host-selected Aesthetica profile proofs | count | 0 | 0 | 0 | >=1 for PASS | 0; blocker | `E2-P2A-HOST1` |
| P2 | Prompt-only identity proofs accepted | count | 0 | 0 | 0 | 0 | 0 | `E0-P0A-HOST1` |

## B3 - P3 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P3 | Positive UI/UX boundary probes | count | 0 | 1 package-router probe | 1 package-router probe; host runtime blocked | >=1 if P2 PASS | host proof unavailable | `E3-P3A-POS1` |
| P3 | Negative backend routing probes honestly rejected/rerouted | count | 0 | 1 package-router probe | 1 package-router probe; host runtime blocked | >=1 if P2 PASS | host proof unavailable | `E3-P3A-NEG1` |
| P3 | Canonical denominator | count | 8 | 8 | 8 | 8 | 0 | `E3-P3B-CAN3` |

## B4 - P4 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P4 | Relevant regression checks passed | count | prior baseline | 32 targeted tests + package scan | 32 targeted tests + package scan | all applicable | 0 failures | `E4-P4A-REG1..E4-P4A-REG4` |
| P4 | Unauthorized runtime source files changed | count | 0 | 0 | 0 | 0 | 0 | `E4-P4A-SCOPE1` |
| P4 | Residual-risk recommendations | count | 0 | 1 | 1 | exactly 1 | 1 | closure evidence |

## Non-Benchmarkable Notes

- Real host availability and profile-selector availability are categorical capability facts; they are recorded in evidence and actual status, not converted into a performance metric.
- No build, Docker, or browser metric is applicable unless the host exposes a real UI surface for this certification.
