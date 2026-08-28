# P2P-LIGHTWEIGHT-FASTPATH-03 Current-Canonical Reconciliation and Clean Verification Benchmark Ledger

## Metadata

- Date: `2026-08-28`
- Plan: `docs/plans/2026-08-28-p2p-lightweight-fastpath-03-current-canonical/2026-08-28-p2p-lightweight-fastpath-03-current-canonical-plan.md`
- Evidence: `docs/plans/2026-08-28-p2p-lightweight-fastpath-03-current-canonical/2026-08-28-p2p-lightweight-fastpath-03-current-canonical-evidence.md`
- Benchmark: `docs/plans/2026-08-28-p2p-lightweight-fastpath-03-current-canonical/2026-08-28-p2p-lightweight-fastpath-03-current-canonical-benchmark.md`
- Actual status: `docs/plans/2026-08-28-p2p-lightweight-fastpath-03-current-canonical/2026-08-28-p2p-lightweight-fastpath-03-current-canonical-actual-status.md`

## Benchmark Rules

This ledger records measured counts, timings, graph inventory, and exact hashes only. Pass/fail narrative belongs in the evidence ledger.

## B0 - P0 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P0 | Current remote main | SHA | `230769...` known prior | `28a85bc6f69ab992c44f96770ab2f513bbc34f94` | `28a85bc6f69ab992c44f96770ab2f513bbc34f94` | fresh remote truth | 0 | `E0-P0A-REMOTE1`, `E2-P2C-ID1` |
| P0 | Current main tree | SHA | `af290ed1...` known prior | `42734b3c55e8db7ce3936428fd0841f7e6106ea2` | `42734b3c55e8db7ce3936428fd0841f7e6106ea2` | exact current tree | 0 | `E0-P0A-CANON1`, `E2-P2C-ID1` |
| P0 | Commits between old base and current main | commits | 0 | 4 | 4 | all relevant commits classified | +4 | `E0-P0A-ANCESTRY1` |
| P0 | Candidate files scanned by Anvien | files | n/a | 988 | 993 | current candidate graph | +5 | `E0-P0A-GRAPH1`, `E2-P2A-ANVIEN1` |
| P0 | Parsed code files | files | n/a | 176 | 177 | 0 parse failures | +1 | `E0-P0A-GRAPH1`, `E2-P2A-ANVIEN1` |
| P0 | Initial candidate status | lines | 1127 old candidate noise | 0 content changes | 0 content changes | 0 unrelated content changes | 0 | `E0-P0A-CLEAN1`, `E2-P2C-CLEAN1` |

## B1 - P1 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P1 | Workflow production files changed | files | 0 | 1 | 1 | 1 | +1 | `E1-P1A-SRC1`, `E2-P2C-ID1` |
| P1 | Focused FASTPATH test files changed | files | 0 | 1 | 1 | 1 | +1 | `E1-P1B-TEST1`, `E2-P2C-ID1` |
| P1 | C18 policy files changed | files | 0 | 0 | 0 | 0 | 0 | `E0-P0A-EFF2`, `E2-P2C-ID1` |

## B2 - P2 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P2 | Focused FASTPATH tests | tests | 0 | 18 | 18 | all required scenarios | +18 | `E1-P1B-TEST1` |
| P2 | Current EFF01/C18/C19 tests | tests | 61 | 61 | 61 | no regression | 0 | `E2-P2A-TEST1` |
| P2 | Workflow/path-sensitive tests | tests | 8 | 8 | 8 | both path-sensitive pass outside `.tmp` | 0 | `E2-P2A-TEST1` |
| P2 | Candidate commits after implementation | commits | 0 | pending | pending | isolated checkpoint(s) | pending | pending |
| P2 | Candidate tree identity | SHA | pending | pending | pending | exact reviewed subject | pending | pending |

## Non-Benchmarkable Notes

- No production latency, token cost, model quality, or host-runtime certification claim is measured by this offline standard-library workflow task.
- EFF01 lane/test-ceiling behavior is reused and asserted; it is not reimplemented or counted as a new policy benchmark.
- Broad/full repository testing is intentionally not a target unless a material new failure requires it.
