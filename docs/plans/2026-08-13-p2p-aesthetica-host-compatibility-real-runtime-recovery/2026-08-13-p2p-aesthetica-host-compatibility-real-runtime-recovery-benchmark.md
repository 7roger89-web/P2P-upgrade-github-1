# P2P Aesthetica Host Compatibility and Real Runtime Recovery Benchmark Ledger

## Metadata

- Date: `2026-08-13`
- Plan: `Docs/plans/2026-08-13-p2p-aesthetica-host-compatibility-real-runtime-recovery/2026-08-13-p2p-aesthetica-host-compatibility-real-runtime-recovery-plan.md`
- Evidence: `Docs/plans/2026-08-13-p2p-aesthetica-host-compatibility-real-runtime-recovery/2026-08-13-p2p-aesthetica-host-compatibility-real-runtime-recovery-evidence.md`
- Benchmark: `Docs/plans/2026-08-13-p2p-aesthetica-host-compatibility-real-runtime-recovery/2026-08-13-p2p-aesthetica-host-compatibility-real-runtime-recovery-benchmark.md`
- Actual status: `Docs/plans/2026-08-13-p2p-aesthetica-host-compatibility-real-runtime-recovery/2026-08-13-p2p-aesthetica-host-compatibility-real-runtime-recovery-actual-status.md`

## Benchmark Rules

This ledger records measured counts, hashes, file sizes, and execution-attempt counts only. Pass/fail narrative belongs in the evidence ledger.

## B0 - P0 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P0 | Canonical identities | count | 8 | 8 | 8 | 8 | 0 | E0-P0A-SCHEMA1 / E2-P2-DOCTOR1 |
| P0 | Canonical denominator | integer | 8 | 8 | 8 | 8 | 0 | E0-P0A-SCHEMA1 / E2-P2-DOCTOR1 |

## B1 - P1 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P1 | Aesthetica profile schema errors | count | 1 known legacy shape | 0 | 0 | 0 | -1 | E1-P1A-SCHEMA2 / E1-P1A-FIX2 |

## B2 - P2 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P2 | Candidate artifact size | bytes | 2336913 | 2370637 | 2370637 | recorded | +33724 | E2-P2-PACKAGE1 |
| P2 | Candidate artifact SHA-256 | digest | b8689fb812a438f379fc1d84353f2e4e4c9c0c234c1e22539b2bc32fd15b8156 | d17ba240cb754d1c7349f8f6273f4785dc778e16c395bf49166e904899f84420 | d17ba240cb754d1c7349f8f6273f4785dc778e16c395bf49166e904899f84420 | recorded | changed by release | E2-P2-PACKAGE1 |
| P2 | Package file count | count | 397 candidate baseline | 397 | 397 | 397 | 0 | E2-P2-PACKAGE1 |
| P2 | Package checksum entries | count | 398 candidate baseline | 398 | 398 | 398 | 0 | E2-P2-PACKAGE1 |
| P2 | Release lifecycle tests | tests | not run | 2/2 | 2/2 | 2/2 | pass | E2-P2-LIFECYCLE1 |
| P2 | Full repository tests | tests | not run | 50/50 | 50/50 | 50/50 | pass | E2-P2-REGRESSION1 |

## B3 - P3 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|-------|-------|----------|
| P3 | Elevated sandbox attempts | count | 0 | 2 read-only child probes | 2 | >=1 | 2 | E3-P3-ELEVATED1 |
| P3 | Unelevated sandbox attempts | count | 0 | 1 read-only child probe | 1 | >=1 | 1 | E3-P3-UNELEVATED1 |
| P3 | Real Aesthetica child threads | count | 0 | 2 host-proven children | 2 | >=1 for PASS | 2 | E3-P3-MULTI1 |
| P3 | Host identity proofs | count | 0 | 2 `agent_role=p2p_aesthetica` | 2 | >=1 | 2 | E3-P3-UNELEVATED1 / E3-P3-ELEVATED1 |

## Non-Benchmarkable Notes

Trust activation, profile provenance, domain-boundary correctness, and fail-closed semantics are evidence-backed behavior decisions, not performance benchmarks.
