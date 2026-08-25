# P2P Vendor Skills — Reconstruct Candidate on Valid Git Authority Benchmark Ledger

## Metadata

- Date: `2026-08-25`
- Plan: `docs/plans/2026-08-25-p2p-vendor-skills-reconstructed/2026-08-25-p2p-vendor-skills-reconstructed-plan.md`
- Evidence: `docs/plans/2026-08-25-p2p-vendor-skills-reconstructed/2026-08-25-p2p-vendor-skills-reconstructed-evidence.md`
- Benchmark: `docs/plans/2026-08-25-p2p-vendor-skills-reconstructed/2026-08-25-p2p-vendor-skills-reconstructed-benchmark.md`
- Actual status: `docs/plans/2026-08-25-p2p-vendor-skills-reconstructed/2026-08-25-p2p-vendor-skills-reconstructed-actual-status.md`

## Benchmark Rules

This ledger records measured counts, hashes, graph inventory, and test totals.
Pass/fail narrative belongs in the evidence ledger. Baseline and candidate
values are kept separate; no synthetic benchmark or simulated provider is used.

## B0 - P0 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P0 | Verified reference tree | SHA-256 | `2bd89d97f8877d372f0444218ec9c7339da14d7f` | `2bd89d97f8877d372f0444218ec9c7339da14d7f` | `2bd89d97f8877d372f0444218ec9c7339da14d7f` | exact supplied tree | `0` | `E0-P0A-AUTH2` |
| P0 | C35 provider-neutral suite | tests | `57/57` | `57/57` | `57/57` | `57/57` | `0` | `E0-P0A-C351`, `E3-P3A-TEST1` |
| P0 | Candidate Anvien graph | files / parsed / failed | `922/165/0` | `927/166/0` | `927/166/0` | failed `0` | `+5/+1/0` | `E0-P0A-ANV1`, `E3-P3B-ANV1` |
| P0 | Clean base registry | capabilities | `13` | `13` | `13` | valid canonical `8/8` | `0` | `E0-P0A-DOCTOR1` |

## B1 - P1 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P1 | Broken-root protected artifact recheck | hashes | `7/7` supplied | `7/7` matched | `7/7` matched | `7/7` matched | `0` | `E0-P0A-HASH1` |
| P1 | Editable source surface | files/classes | `0` | frozen vendor seam | `3 tracked + new adapter/test/trees` | no unrelated drift | scoped | `E1-P1B-SCOPE2`, `E3-P3B-GIT1` |

## B2 - P2 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P2 | Vendor snapshot integrity | trees | `2/2` source reference | `2/2` exact | `2/2` exact | `2/2` exact | `0` | `E2-P2A-HASH1`, `E3-P3A-DIFF1` |
| P2 | Vendor integration suite | tests | `0` in base | `17/17` | `17/17` | `17/17` | `+17` | `E2-P2B-TEST1`, `E3-P3A-TEST1` |
| P2 | Capability foundation suite | tests | `28/28` base | `28/28` | `28/28` | `28/28` | `0` regression | `E2-P2B-TEST1`, `E3-P3A-TEST1` |
| P2 | Combined focused suites | tests | `28/28` base | `45/45` | `45/45` | `45/45` | `+17` | `E2-P2B-TEST1`, `E3-P3A-TEST1` |

## B3 - P3 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P3 | Capability doctor | exit/status | `0/PASS; 13; 8/8` | `0/PASS; 15; 8/8` | `0/PASS; 15; 8/8` | exit `0`, canonical `8/8` | `+2 vendor records` | `E0-P0A-DOCTOR1`, `E3-P3A-DOCTOR1` |
| P3 | Compile/build | exit | `N/A` | `0` | `0` | `0` | `0` | `E3-P3A-TEST1` |
| P3 | Anvien detect-changes | exit / changed / affected | `N/A` | `0 / 44 / 6` | `0 / 44 / 6` | exit `0` | `0` | `E3-P3B-ANV1` |

## Non-Benchmarkable Notes

The package/development doctor role mismatch and inherited governance drift are
classification evidence, not performance metrics. Optional renderer execution,
external image generation, browser behavior, Docker runtime, and network
provider performance are intentionally not benchmarked in this offline slice.
