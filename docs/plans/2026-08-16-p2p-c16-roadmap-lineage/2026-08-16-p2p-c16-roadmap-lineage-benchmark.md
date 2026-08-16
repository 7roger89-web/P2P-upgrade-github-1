# P2P-C16 Durable Development Roadmap and Release Lineage Foundation Benchmark Ledger

## Metadata

- Date: `2026-08-16`
- Plan: `docs/plans/2026-08-16-p2p-c16-roadmap-lineage/2026-08-16-p2p-c16-roadmap-lineage-plan.md`
- Evidence: `docs/plans/2026-08-16-p2p-c16-roadmap-lineage/2026-08-16-p2p-c16-roadmap-lineage-evidence.md`
- Benchmark: `docs/plans/2026-08-16-p2p-c16-roadmap-lineage/2026-08-16-p2p-c16-roadmap-lineage-benchmark.md`
- Actual status: `docs/plans/2026-08-16-p2p-c16-roadmap-lineage/2026-08-16-p2p-c16-roadmap-lineage-actual-status.md`

## Benchmark Rules

The benchmark file records measured counts, hashes, sizes, and inventory values only. Pass/fail narrative belongs in the evidence ledger. No benchmark claim is inferred from a filename or prior report.

## B0 - P0 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P0 | Root graph files scanned | files | 370 | 379 | 379 | current graph | +9 | `E0-P0A-GRAPH1`, `E3-P3A-GRAPH1` |
| P0 | Package builder local relationships | relationships | 33 | 33 | 33 | scope recorded | 0 | `E0-P0A-GRAPH2`, `E3-P3A-GRAPH1` |
| P0 | Official baseline revision | revision | `.19` | `.19` | `.19` | `.19` | 0 | `E0-P0A-SRC3` |
| P0 | Official artifact SHA-256 | hash | `3a9ee51321e1f5e40e35ce73eb90727cddb571a672aa095d16d76af2feb03dd8` | same | same | exact supplied hash | 0 | `E0-P0A-SRC3` |
| P0 | Current development source revision | revision | `.15` | `.15` | `.15` before C16 candidate prep | explicit stale block | 0 | `E0-P0A-SRC2` |

## B1 - P1 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P1 | Durable roadmap items | items | 0 machine-readable C16 values | 26 | 26 | C08-C17 plus preserved roadmap families | +26 | `E1-P1A-CONTROL1`, `E1-P1A-VALIDATE1` |
| P1 | Durable roadmap status enum | values | 0 | 6 | 6 | fixed enum | +6 | `E1-P1A-VALIDATE1` |
| P1 | Canonical identities | identities | 8 | 8 | 8 | exactly 8 | 0 | `E1-P1B-TEST1` |
| P1 | Roadmap mutation provenance fields | fields/event | 0 | 4 required fields plus actor/id | 4 required fields plus actor/id | what/why/evidence/when | added | `E1-P1B-TEST1` |
| P1 | Research decisions | decisions | 0 | 8 | 8 | requested registry retained without vendoring | +8 | `E1-P1A-CONTROL1` |

## B2 - P2 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P2 | Stale lineage packaging result | result | not guarded | explicit `LINEAGE_REGRESSION` block | explicit `LINEAGE_REGRESSION` block | BLOCK/FAIL closed | guarded | `E2-P2A-BLOCK1`, `E2-P2B-TEST1` |
| P2 | Filename-only authority result | result | not tested | hash mismatch rejected; filename ignored | hash mismatch rejected; filename ignored | reject/UNKNOWN | guarded | `E2-P2B-TEST1` |
| P2 | Official `.19` artifact SHA | hash | supplied hash | `3a9ee51321e1f5e40e35ce73eb90727cddb571a672aa095d16d76af2feb03dd8` | same | unchanged | 0 | `E2-P2B-TEST1` |

## B3 - P3 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P3 | Focused C16 tests | tests | 0 | 19/19 | 19/19 | R1-R18 plus embedded-control compatibility | +19 | `E1-P1B-TEST1`, `E2-P2B-TEST1`, `E3-P3A-REG1` |
| P3 | Affected C10-C15/governance/package tests | tests | prior suite | 116/116 | 116/116 | no affected regressions | PASS | `E3-P3A-REG1` |
| P3 | Full unittest regression | tests | 198 prior evidence | 218/218 | 218/218 | no C16 regressions | +20 tests; all pass | `E3-P3A-REG1` |

## Non-Benchmarkable Notes

- Roadmap wording, invariant references, research decisions, and supervisor judgment are evidence/authority facts, not performance benchmarks.
- Live delegation certification, parallel execution, and C17 are out of scope and must not be represented as benchmark targets.
