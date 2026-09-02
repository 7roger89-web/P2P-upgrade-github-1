# P2P Character Forge Productization ISSUE 59 Benchmark Ledger

## Metadata

- Date: `2026-09-02`
- Plan: `docs/plans/2026-09-02-p2p-character-forge-productization-01/2026-09-02-p2p-character-forge-productization-01-plan.md`
- Evidence: `docs/plans/2026-09-02-p2p-character-forge-productization-01/2026-09-02-p2p-character-forge-productization-01-evidence.md`
- Benchmark: `docs/plans/2026-09-02-p2p-character-forge-productization-01/2026-09-02-p2p-character-forge-productization-01-benchmark.md`
- Actual status: `docs/plans/2026-09-02-p2p-character-forge-productization-01/2026-09-02-p2p-character-forge-productization-01-actual-status.md`

## Benchmark Rules

This file records measured counts, hashes, sizes, and runtime quantities only.
Pass/fail command narrative belongs in `evidence.md`. Existing Oak artifact
measurements are a baseline reference; ISSUE=59 must record its own output.

## B0 - P0 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P0 | Canonical capability identities for MPFB2 character lane | identities | 1 (`game.character.generate`) | 1 | 1 | 1 | 0 | E0-P0A-CAP1 |
| P0 | Canonical main commit | SHA | `0ee414147ae308ab1f6035d1e7776292752bd8da` | same | same | exact expected SHA | 0 | E0-P0A-GIT1 |
| P0 | Canonical main tree | SHA | `f34719776bee67a731c4049b79165bd3deaa3074` | same | same | exact expected tree | 0 | E0-P0A-GIT1 |
| P0 | Fresh capability-system graph nodes | nodes | 0 | 43138 | 43138 | graph refreshed | +43138 | E0-P0A-GRAPH1..5 |
| P0 | Existing Oak GLB size | bytes | 9093808 | 9093808 | 9093808 | reference only | 0 | E0-P0A-RUNTIME1 |

## B1 - P1 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P1 | Beginner request fields accepted | fields | 0 | pending | pending | 6 | pending | E1-P1A-SCHEMA1 |
| P1 | Duplicate character execution frameworks | frameworks | 0 | pending | pending | 0 | pending | E1-P1B-SRC1 |
| P1 | Focused productization tests | tests | 0 | pending | pending | focused set passes | pending | E1-P1A-TEST1..E1-P1B-TEST3 |

## B2 - P2 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P2 | ISSUE=59 real Blender child spawns | processes | 0 | pending | pending | exactly 1 | pending | E2-P2A-RUN1 |
| P2 | ISSUE=59 generated GLB outputs | files | 0 | pending | pending | exactly 1 | pending | E2-P2A-ARTIFACT1 |
| P2 | ISSUE=59 provenance sidecars | files | 0 | pending | pending | exactly 1 | pending | E2-P2A-ARTIFACT1 |
| P2 | ISSUE=59 output GLB size | bytes | 0 | pending | pending | >0 | pending | E2-P2B-ARTIFACT1 |
| P2 | Residual Blender processes after smoke | processes | 0 | pending | pending | 0 | pending | E2-P2B-CLEAN1 |
| P2 | Residual `P2P-MPFB-DENY-*` rules after smoke | rules | 0 | pending | pending | 0 | pending | E2-P2B-CLEAN1 |

## Non-Benchmarkable Notes

- Request normalization, receipt status, and fail-closed behavior are validated
  by focused tests rather than performance benchmarks.
- No UI, browser, Docker, database, package, or release-size benchmark applies
  to this native Windows productization slice.
