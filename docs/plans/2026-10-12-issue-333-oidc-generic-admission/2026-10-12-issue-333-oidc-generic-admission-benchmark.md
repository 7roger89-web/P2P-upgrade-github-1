# Issue 333 OIDC Generic Admission Benchmark Ledger

## Metadata

- Date: `2026-10-12`
- Plan: `docs/plans/2026-10-12-issue-333-oidc-generic-admission/2026-10-12-issue-333-oidc-generic-admission-plan.md`
- Evidence: `docs/plans/2026-10-12-issue-333-oidc-generic-admission/2026-10-12-issue-333-oidc-generic-admission-evidence.md`
- Benchmark: `docs/plans/2026-10-12-issue-333-oidc-generic-admission/2026-10-12-issue-333-oidc-generic-admission-benchmark.md`
- Actual status: `docs/plans/2026-10-12-issue-333-oidc-generic-admission/2026-10-12-issue-333-oidc-generic-admission-actual-status.md`

## Benchmark Rules

Only measured counts are recorded.

## B0 - P0 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P0 | Real non-Arena/non-Codex actor read-and-apply canary | passing actors | 0 | 1 | 1 | >=1 | +1 | E0-P0A-CANARY1 |
| P0 | GitHub-signed evidence binding mechanisms proven | passing mechanisms | 0 | 1 (OIDC) | 1 | >=1 | +1 | E0-P0A-CANARY2 |
| P0 | Artifact-attestation mechanisms usable on this repo | passing mechanisms | 0 | 0 | 0 | N/A | 0 | E0-P0A-PROVIDER1 |

## B1 - P1 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P1 | Generic trusted execution-admission positive paths | paths | 0 | 0 | TBD | 1 | TBD | pending |
| P1 | Required negative trust controls | cases | 0 | 0 | TBD | >=10 | TBD | pending |
| P1 | Native Arena/Codex regressions introduced | failures | 0 | 0 | TBD | 0 | TBD | pending |

## B2 - P2 Benchmarks

N/A — no P2 phase.

## Non-Benchmarkable Notes

Security meaning is not reduced to counts; source/claim binding and fail-closed behavior are recorded in the evidence ledger.
