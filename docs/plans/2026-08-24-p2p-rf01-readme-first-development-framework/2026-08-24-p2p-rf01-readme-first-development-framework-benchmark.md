# RF01 README-First Project Orientation + Development Framework Revision Benchmark Ledger

## Metadata

- Date: `2026-08-24`
- Plan: `docs/plans/2026-08-24-p2p-rf01-readme-first-development-framework/2026-08-24-p2p-rf01-readme-first-development-framework-plan.md`
- Evidence: `docs/plans/2026-08-24-p2p-rf01-readme-first-development-framework/2026-08-24-p2p-rf01-readme-first-development-framework-evidence.md`
- Benchmark: `docs/plans/2026-08-24-p2p-rf01-readme-first-development-framework/2026-08-24-p2p-rf01-readme-first-development-framework-benchmark.md`
- Actual status: `docs/plans/2026-08-24-p2p-rf01-readme-first-development-framework/2026-08-24-p2p-rf01-readme-first-development-framework-actual-status.md`

## Benchmark Rules

- This is a documentation/standard-library tooling slice. Measurements are inventory, graph, hash, and test counts; they are not product-performance or host-authority proof.
- Do not build or hash a new release candidate in RF01. The sealed `.74` artifact hash is an immutability control only.
- Timing is not recorded unless it is material to this scope.

## B0 - P0 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P0 | Indexed files | files | 864 | 864 | pending | graph refresh succeeds | 0 | E0-P0A-GR1 |
| P0 | Parsed code files | files | 160 | 160 | pending | 0 parse failures | 0 | E0-P0A-GR1 |
| P0 | Graph nodes | nodes | 36,692 | 36,692 | pending | informational | 0 | E0-P0A-GR1 |
| P0 | Graph relationships | relationships | 42,410 | 42,410 | pending | informational | 0 | E0-P0A-GR1 |
| P0 | Sealed `.74` matching copies | copies | 3 | 3 | pending | all copies match expected SHA | 0 | E0-P0A-SRC2 |
| P0 | Root README orientation file | file | 0 | 0 | pending | one managed README after P1-A | 0 | E0-P0A-DOC1 |

## B1 - P1 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P1 | Managed README block line count | lines | 0 | 132 | PASS | <= 300 | +132 | E1-P1A-ORIENT2 |
| P1 | Orientation behavior cases passing | cases | 0 | 7 | PASS | all planned cases | +7 | E1-P1A-TEST1 |
| P1 | README bytes preserved outside managed block | fixtures | N/A | 2 | PASS | exact equality | PASS | E1-P1A-TEST2 |
| P1 | Package allowlist RF01 entries | entries | 0 | 2 | PASS | README + helper selected | +2 | E1-P1C-PKG1..E1-P1C-PKG2 |
| P1 | Installer helper copy bindings | installers | 0 | 2 | PASS | both existing installers | +2 | E1-P1C-INSTALL1..E1-P1C-INSTALL3 |
| P1 | Installer README write paths | paths | 0 | 0 | PASS | 0 | 0 | E1-P1C-INSTALL2 |
| P1 | New release/promotion artifacts | artifacts | 0 | 0 | 0 | 0 | 0 | plan boundary |

## B2 - P2 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P2 | Final graph parse failures | files | 0 | 0 | PASS | 0 | 0 | E2-P2A-ANV1 |
| P2 | Exact sealed `.74` SHA-256 changes | changes | 0 | 0 | PASS | 0 | 0 | E2-P2A-IMMUTABLE1..E2-P2A-IMMUTABLE2 |
| P2 | Unplanned changed files | files | 0 | 0 | PASS | 0 | 0 | E2-P2C-CLOSE1..E2-P2C-CLOSE2 |

## Non-Benchmarkable Notes

- Product human-outcome acceptance, host GitHub protection, promotion authority, and independent certification are not benchmarkable in this local RF01 development slice and remain explicitly deferred/blocked.
