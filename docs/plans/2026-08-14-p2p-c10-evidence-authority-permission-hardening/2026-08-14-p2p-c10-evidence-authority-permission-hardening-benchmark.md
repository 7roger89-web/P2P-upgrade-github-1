# P2P-C10 Evidence Authority and Permission Hardening Benchmark Ledger

## Metadata

- Date: `2026-08-14`
- Plan: `docs/plans/2026-08-14-p2p-c10-evidence-authority-permission-hardening/2026-08-14-p2p-c10-evidence-authority-permission-hardening-plan.md`
- Evidence: `docs/plans/2026-08-14-p2p-c10-evidence-authority-permission-hardening/2026-08-14-p2p-c10-evidence-authority-permission-hardening-evidence.md`
- Benchmark: `docs/plans/2026-08-14-p2p-c10-evidence-authority-permission-hardening/2026-08-14-p2p-c10-evidence-authority-permission-hardening-benchmark.md`
- Actual status: `docs/plans/2026-08-14-p2p-c10-evidence-authority-permission-hardening/2026-08-14-p2p-c10-evidence-authority-permission-hardening-actual-status.md`

## Benchmark Rules

Only measured graph, test, package, hash, or runtime counts belong here. Pass/fail narrative belongs in `evidence.md`.

## B0 - P0 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P0 | Anvien graph nodes | nodes | N/A | 11,863 | 12,004 | current graph | +141 | `E2-P2C-CLOSE1` |
| P0 | Anvien relationships | edges | N/A | 13,475 | 13,648 | current graph | +173 | `E2-P2C-CLOSE1` |
| P0 | Source files scanned | files | N/A | 318 | 323 | current workspace | +5 | `E2-P2C-CLOSE1` |

## B1 - P1 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P1 | Evidence contract focused tests | tests | historical 27 | 28 | 28 | all direct cases | +1 | `E1-P1A-TEST1` |
| P1 | Live permission focused tests | tests | historical 16 | 16 | 16 | all direct cases | 0 | `E1-P1B-EDGE1` |
| P1 | Security scanner focused tests | tests | N/A | 2 | 2 | placeholder ignored, real token detected | measured | `E2-P2A-SEC1` |

## B2 - P2 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P2 | Full regression | tests / seconds | historical 111 | 119 / 118.001s | 119 / 118.001s | no regression | +8 tests | `E2-P2A-TEST1` |
| P2 | Candidate package | SHA-256 | `.18` preserved | `.20` / `0cc5d18c…03c9` | `.20` / `0cc5d18cd01eb28a4ef914dca09d2530bef7c072d53e7dd194dd82fb4037a6f6` | new unpromoted only if required | new candidate | `E2-P2C-CLOSE1` |

## Non-Benchmarkable Notes

- C09 host identity availability is evidence state, not a performance benchmark; it remains `UNKNOWN/BLOCKED`.
- No release or promotion is a benchmark target in this Goal.
