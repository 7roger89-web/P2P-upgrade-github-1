# P2P Generic Repo-Read Admission Benchmark Ledger

## Metadata

- Date: `2026-10-12`
- Plan: `docs/plans/2026-10-12-p2p-generic-read-admission/2026-10-12-p2p-generic-read-admission-plan.md`
- Evidence: `docs/plans/2026-10-12-p2p-generic-read-admission/2026-10-12-p2p-generic-read-admission-evidence.md`
- Benchmark: `docs/plans/2026-10-12-p2p-generic-read-admission/2026-10-12-p2p-generic-read-admission-benchmark.md`
- Actual status: `docs/plans/2026-10-12-p2p-generic-read-admission/2026-10-12-p2p-generic-read-admission-actual-status.md`

## B0 - P0 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|---|---|---|---:|---:|---:|---:|---:|---|
| P0 | real non-native read/apply actors proven | actor | 0 | 1 | 1 | >=1 | +1 | E0-P0A-CANARY1 |
| P0 | generic signed-evidence admission paths on candidate | path | 0 | 1 | 1 | 1 | +1 | E2-P2B-LIVE1 |
| P0 | provider-specific adapters added | adapter | 0 | 0 | 0 | 0 | 0 | E0-P0A-SRC1..4 |

## B1 - P1 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|---|---|---|---:|---:|---:|---:|---:|---|
| P1 | signed external-read canary exact-head PASS | run | 0 | 1 | 1 | 1 | +1 | E1-P1A-RUN1 |
| P1 | GitHub OIDC signer/source/subject constraints verified | constraint family | 0 | 1 | 1 | 1 | +1 | E1-P1B-OIDC1 |

## B2 - P2 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|---|---|---|---:|---:|---:|---:|---:|---|
| P2 | generic positive admission | path | 0 | 1 | 1 | 1 | +1 | E2-P2B-LIVE1 |
| P2 | explicit adversarial fail-closed classes | class | 0 | >=15 | >=15 | >=8 | >=+15 | E2-P2A-TEST1 |
| P2 | native/PROMPT_ONLY regression failures | failure | 0 | 0 | 0 | 0 | 0 | E2-P2B-SHIELD1 |

## Non-Benchmarkable Notes

No performance benchmark is required; this scope is a trust/admission correctness gate.


## Closure metrics

| Metric | Value | Evidence |
|---|---:|---|
| Shield focused tests | 366 PASS | run 38235247660 |
| FW02 | 26 PASS | run 38235247660 |
| Quality Intelligence | 44 PASS | run 38235247660 |
| AERG | 32 PASS | run 38235247660 |
| Governance | 6 PASS | run 38235247660 |
| Current-workflow diagnostic | FAIL / 22 findings | baseline shape, not claimed clean |
| New Zizmor findings above baseline | 0 | final workflow scan |
