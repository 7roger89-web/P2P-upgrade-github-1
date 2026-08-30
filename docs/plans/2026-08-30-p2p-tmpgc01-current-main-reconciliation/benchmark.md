# P2P-TMPGC01 Current Main Reconciliation Benchmark Ledger

## Metadata

- Date: `2026-08-30`
- Plan: `docs/plans/2026-08-30-p2p-tmpgc01-current-main-reconciliation/plan.md`
- Evidence: `docs/plans/2026-08-30-p2p-tmpgc01-current-main-reconciliation/evidence.md`
- Benchmark: `docs/plans/2026-08-30-p2p-tmpgc01-current-main-reconciliation/benchmark.md`
- Actual status: `docs/plans/2026-08-30-p2p-tmpgc01-current-main-reconciliation/actual-status.md`

## Benchmark Rules

This non-UI Python reconciliation has no product performance target. Record only
exact Git identity, scoped path counts, and focused test counts. Test timing is
validation evidence, not a performance claim.

## B0 - P0 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P0 | Fresh main tree | Git tree SHA | unknown | `92895a93a560221bdcd4664992ab16a4e8ec8cb4` | `92895a93a560221bdcd4664992ab16a4e8ec8cb4` | exact fresh ref | bound | `E0-P0A-GIT2` |
| P0 | TMPGC production/test/policy paths on fresh main | count | 0/5 | 0/5 | 5/5 | 5/5 candidate | +5 | `E0-P0A-SRC1`, `E1-P1B-TEST1` |

## B1 - P1 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P1 | Scoped implementation paths changed | count | 0 | 5 | pending | only 5 functional paths | +5 | `E1-P1A-DIFF2` |
| P1 | Focused TMPGC tests passed | tests | 0 | 67 | 67 | all selected tests | +67 | `E1-P1B-TEST2` |

## B2 - P2 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P2 | Candidate commit/tree frozen | SHA/tree pair | none | `2ec61632c1bfe78a685cb575eaf8495c658fa46b` / `051faf6438f24dd206d5401b78965215e5fa9dfb` | `2ec61632c1bfe78a685cb575eaf8495c658fa46b` / `051faf6438f24dd206d5401b78965215e5fa9dfb` | one exact pair; evidence-only closure permitted | bound | `E2-P2A-SUPERVISOR1` |

## Non-Benchmarkable Notes

No UI, database, network service, package, capacity, or product performance
benchmark is applicable. No scheduling or physical delete is a benchmark target.
