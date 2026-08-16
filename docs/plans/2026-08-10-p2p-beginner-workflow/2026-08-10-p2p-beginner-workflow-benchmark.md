# P2P beginner workflow Benchmark Ledger

## Metadata

- Date: `2026-08-10`
- Plan: `docs/plans/2026-08-10-p2p-beginner-workflow/2026-08-10-p2p-beginner-workflow-plan.md`
- Evidence: `docs/plans/2026-08-10-p2p-beginner-workflow/2026-08-10-p2p-beginner-workflow-evidence.md`
- Benchmark: `docs/plans/2026-08-10-p2p-beginner-workflow/2026-08-10-p2p-beginner-workflow-benchmark.md`
- Actual status: `docs/plans/2026-08-10-p2p-beginner-workflow/2026-08-10-p2p-beginner-workflow-actual-status.md`

## Benchmark rules

Record measured inventory and workflow counts only. Real project quality scores and real multi-agent runtime claims remain out of scope for synthetic acceptance.

## B0 - P0 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|---|---|---:|---:|---:|---:|---:|---:|---|
| P0 | Canonical P2P skills | count | 22 | 22 | 22 | 22 or intentionally unchanged | 0 | `E0-P0A-GATE1`, `E2-P2A-PACKAGE1` |
| P0 | Named P2P agents | count | 8 | 8 | 8 | 8 | 0 | `E0-P0A-GATE1`, `E2-P2A-PACKAGE1` |
| P0 | Immutable source files | count | 152 | 152 | 152 | 152 | 0 | `E0-P0A-GATE1`, `E2-P2A-PACKAGE1` |
| P0 | Full-quorum calls for ordinary baseline tasks | count | not implemented | 0 | 0 | 0 | 0 | `E1-P1A-ACCEPT1` |

## B1 - P1 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|---|---|---:|---:|---:|---:|---:|---:|---|
| P1 | Workflow helper commands | count | 0 | 7 | 7 | 7 (`inspect`, `goal`, `bootstrap`, `plan`, `run`, `report`, `acceptance`) | +7 | `E1-P1A-CODE1` |
| P1 | Generated eval case types | count | 0 | 5 | 5 | 5 including positive, negative, regression, completion, reuse/boundary | +5 | `E1-P1A-CODE2` |

## B2 - P2 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|---|---|---:|---:|---:|---:|---:|---:|---|
| P2 | New-project acceptance fixtures | count | 0 | 1 | 1 | 1 PASS | +1 | `E1-P1A-ACCEPT1`, `E2-P2A-WORKFLOW1` |
| P2 | Existing-project reuse acceptance fixtures | count | 0 | 1 | 1 | 1 PASS | +1 | `E1-P1A-ACCEPT1` |
| P2 | Unrelated audits rerun after scoped fixture change | count | not implemented | 0 | 0 | 0 | 0 | `E1-P1A-ACCEPT1` |
| P2 | Full quorum used for ordinary scoped fixture change | count | not implemented | 0 | 0 | 0 | 0 | `E1-P1A-ACCEPT1` |

## Non-benchmarkable notes

Real project eval trial scores and host-level eight-thread runtime evidence require a user project and Codex host. The acceptance command must not fabricate those results.
