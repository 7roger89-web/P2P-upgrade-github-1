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
| P0 | generic signed-evidence admission paths on main | path | 0 | 0 | pending | 1 | 0 | E0-P0A-SRC1..4 |
| P0 | provider-specific adapters added | adapter | 0 | 0 | 0 | 0 | 0 | E0-P0A-SRC1..4 |

## B1 - P1 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|---|---|---|---:|---:|---:|---:|---:|---|
| P1 | signed external-read canary exact-head PASS | run | 0 | pending | pending | 1 | pending | E1-P1A-RUN1 |
| P1 | independent signer/source/subject constraints verified | constraint family | 0 | pending | pending | 1 | pending | E1-P1A-ATTEST1 |

## B2 - P2 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|---|---|---|---:|---:|---:|---:|---:|---|
| P2 | generic positive admission | path | 0 | pending | pending | 1 | pending | E2-P2A-TEST1 |
| P2 | required adversarial fail-closed classes | class | 0 | pending | pending | >=8 | pending | E2-P2A-TEST1 |
| P2 | native ARENA/CODEX regressions | failure | 0 | pending | pending | 0 | pending | E2-P2B-* |

## Non-Benchmarkable Notes

No performance benchmark is required; this scope is a trust/admission correctness gate.
