# P2P reusable release packaging Benchmark Ledger

## Metadata

- Date: `2026-08-10`
- Plan: `docs/plans/2026-08-10-p2p-release-packaging/2026-08-10-p2p-release-packaging-plan.md`
- Evidence: `docs/plans/2026-08-10-p2p-release-packaging/2026-08-10-p2p-release-packaging-evidence.md`
- Benchmark: `docs/plans/2026-08-10-p2p-release-packaging/2026-08-10-p2p-release-packaging-benchmark.md`
- Actual status: `docs/plans/2026-08-10-p2p-release-packaging/2026-08-10-p2p-release-packaging-actual-status.md`

## Benchmark Rules

Record measured inventory, artifact size/hash, file counts, and acceptance counts only.
Do not treat safe fixtures as real project-quality or live-agent performance scores.

## B0 - P0 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|---|---|---:|---:|---:|---:|---:|---:|---|
| P0 | Current release version | string | `8.4.6-C-codex.4` | `8.4.6-C-codex.5` | `8.4.6-C-codex.5` | `8.4.6-C-codex.5` | +1 release increment | `E0-P0A-META1`, `E1-P1A-META1` |
| P0 | Root archive exclusion rules | count | 0 | 6 forbidden fragments | 6 forbidden fragments | >=1 explicit allowlist | +6 | `E0-P0A-PKG1`, `E1-P1B-CODE1` |

## B1 - P1 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|---|---|---:|---:|---:|---:|---:|---:|---|
| P1 | Required release metadata surfaces | count | 0 new | 5 (`VERSION`, manifest, build report, notes, guide) |  | 5 | +5 | `E1-P1A-META1`, `E1-P1A-DOC1` |
| P1 | Package content inventory | files | unknown | 342 content / 343 checksums | 342 content / 343 checksums | internal manifest consistency | verified | `E1-P1B-CODE1`, Closure |
| P1 | Final artifact | bytes / SHA-256 | none | 2,217,368 / `0c5db0f9…e0be44b` | 2,217,368 / `0c5db0f9…e0be44b` | reproducible local handoff | built and verified | `E2` Closure |

## B2 - P2 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|---|---|---:|---:|---:|---:|---:|---:|---|
| P2 | Fresh-project acceptance | result | not run | PASS | PASS | PASS | verified | `E2-P2B-FRESH1` |
| P2 | Existing-project upgrade acceptance | result | not run | PASS | PASS | PASS | verified | `E2-P2B-UPGRADE1` |
| P2 | Same-version reinstall acceptance | result | not run | PASS | PASS | PASS | verified | `E2-P2B-REINSTALL1` |
| P2 | Protected project-state categories preserved | count | 0 | 9 protected paths/categories | 9 protected paths/categories | 7 minimum | +9 | `E2-P2A-INSTALL2` |
| P2 | Regression suite | tests | 17 | 19 | 19 | all PASS | +2 release tests | `E2` Closure |

## Non-Benchmarkable Notes

No real application project quality, public release approval, or live eight-thread runtime is measured by this plan.
