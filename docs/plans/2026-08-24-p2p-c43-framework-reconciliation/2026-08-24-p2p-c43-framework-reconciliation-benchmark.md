# P2P C43 Framework Reconciliation Benchmark Ledger

## Metadata

- Date: `2026-08-24`
- Plan: `docs/plans/2026-08-24-p2p-c43-framework-reconciliation/2026-08-24-p2p-c43-framework-reconciliation-plan.md`
- Evidence: `docs/plans/2026-08-24-p2p-c43-framework-reconciliation/2026-08-24-p2p-c43-framework-reconciliation-evidence.md`
- Benchmark: `docs/plans/2026-08-24-p2p-c43-framework-reconciliation/2026-08-24-p2p-c43-framework-reconciliation-benchmark.md`
- Actual status: `docs/plans/2026-08-24-p2p-c43-framework-reconciliation/2026-08-24-p2p-c43-framework-reconciliation-actual-status.md`

## Benchmark Rules

- Record measured counts, hashes, exit codes, and timings only when they are actually observed.
- Build/test pass-fail narrative belongs in `evidence.md`; this file records only the measurable values.
- Do not interpret a count, graph inventory, or report count as behavioral proof.

## B0 - P0 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P0 | Capability ledger entries | records | 176 | 174 | 174 | final unique membership | -2 | `E0-P0A-SRC3`, `E1-P1A-AFTER1` |
| P0 | Registered ledger families | families | 12 | 12 | pending | source registry captured | pending | `E0-P0A-SRC3` |
| P0 | Schema validation errors | errors | 54 | 17 | 17 | 0 for accepted touched scope; residuals explicit | -37 | `E0-P0A-DRIFT1..E0-P0A-DRIFT6`, `E1-P1A-AFTER2` |
| P0 | Anvien scanned files | files | 875 | 875 | 875 | fresh graph | 0 | `E0-P0A-GRAPH1` |
| P0 | Anvien parsed code files | files | 163 | 163 | 163 | no parse failures | 0 | `E0-P0A-GRAPH1` |
| P0 | Anvien graph nodes | nodes | 37058 | 37058 | 37058 | informational | 0 | `E0-P0A-GRAPH1` |
| P0 | Anvien graph relationships | relationships | 42835 | 42835 | 42835 | informational | 0 | `E0-P0A-GRAPH1` |

## B1 - P1 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P1 | Canonical ledger entries | records | 176 | 174 | 174 | exact final membership | -2 | `E1-P1A-AFTER1` |
| P1 | Duplicate canonical IDs | IDs | 2 lineage duplicates | 0 | 0 | 0 | resolved | `E1-P1A-NODISCARD1` |
| P1 | Unsupported capability statuses | statuses | 3 | 0 | 0 | 0 in touched scope | -3 | `E1-P1A-AFTER1` |
| P1 | Roadmap/ledger count delta | records | 17 | 0 | 0 | 0 | -17 | `E1-P1B-AFTER1` |

## B2 - P2 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P2 | Required negative/boundary cases observed | cases | 0 | 9 | 9 | 8 minimum | +9 | `E2-P2A-NEG1..E2-P2A-NEG9` |
| P2 | Uncontrolled validator exceptions | exceptions | 1 known TypeError/KeyError path | 0 | 0 | 0 | -1 | `E2-P2A-NEG5`, `E2-P2A-NEG9` |
| P2 | Framework/charter test discovery | tests | 0 counted before C43 | 40 charter functions | 40 charter functions | nonzero and reported | observed | `E2-P2B-CHARTER1` |
| P2 | C43 changed paths before reports | paths | pending | 8 | 8 before report artifacts | exact approved scope | observed | `E1-P1-DIFF1`, `E2-P2B-ANVIEN1` |
| P2 | C36 regression tests | tests | not measured in P0 | 69 | 69 | all observed tests pass | observed | `E2-P2B-REG1` |
| P2 | Targeted-context regression tests | tests | not measured in P0 | 19 | 19 | all observed tests pass | observed | `E2-P2B-REG1` |
| P2 | Targeted-context comparison tests | tests | not measured in P0 | 1 | 1 | all observed tests pass | observed | `E2-P2B-REG1` |
| P2 | C35 provider-neutral regression tests | tests | not measured in P0 | 57 | 57 | all observed tests pass | observed | `E2-P2B-REG1` |
| P2 | Fresh Anvien scanned files | files | 875 | 880 | pending | fresh graph | +5 | `E0-P0A-GRAPH1`, `E2-P2B-ANVIEN1` |
| P2 | Fresh Anvien parsed code files | files | 163 | 164 | pending | zero parse failures | +1 | `E0-P0A-GRAPH1`, `E2-P2B-ANVIEN1` |
| P2 | Fresh Anvien graph nodes | nodes | 37058 | 37294 | pending | informational | +236 | `E0-P0A-GRAPH1`, `E2-P2B-ANVIEN1` |
| P2 | Fresh Anvien graph relationships | relationships | 42835 | 43109 | pending | informational | +274 | `E0-P0A-GRAPH1`, `E2-P2B-ANVIEN1` |

## Non-Benchmarkable Notes

- UI/browser/Docker/application-runtime metrics are not applicable to this development-plane ledger/validator reconciliation.
- RF01 orientation and `.74` sealing are boundary proofs, not performance benchmarks; their exact hashes and verdicts belong in `evidence.md`.
