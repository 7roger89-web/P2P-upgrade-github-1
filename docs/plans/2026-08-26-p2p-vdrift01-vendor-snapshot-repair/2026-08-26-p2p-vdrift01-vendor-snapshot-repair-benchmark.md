# P2P-VDRIFT01 Canonical Vendor Snapshot Drift Repair Benchmark Ledger

## Metadata

- Date: `2026-08-26`
- Plan: `docs/plans/2026-08-26-p2p-vdrift01-vendor-snapshot-repair/2026-08-26-p2p-vdrift01-vendor-snapshot-repair-plan.md`
- Evidence: `docs/plans/2026-08-26-p2p-vdrift01-vendor-snapshot-repair/2026-08-26-p2p-vdrift01-vendor-snapshot-repair-evidence.md`
- Benchmark: `docs/plans/2026-08-26-p2p-vdrift01-vendor-snapshot-repair/2026-08-26-p2p-vdrift01-vendor-snapshot-repair-benchmark.md`
- Actual status: `docs/plans/2026-08-26-p2p-vdrift01-vendor-snapshot-repair/2026-08-26-p2p-vdrift01-vendor-snapshot-repair-actual-status.md`

## Benchmark Rules

Record measured hash/path/file/test counts only. Test pass/fail narrative belongs
in the evidence ledger. No benchmark number authorizes a registry hash rewrite.

## B0 - P0 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P0 | Fresh vendor integration tests | tests | 17 | 17 | 17 | 17 | 0 | E0-P0A-REPRO1 |
| P0 | Reproduced drifted capability IDs | IDs | 0 | 2 | 2 | 0 | +2 | E0-P0A-REPRO1 |

## B1 - P1 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P1 | `creative.copywriting` snapshot identity | SHA-256 | `146e5d767d8c960825d5a5765054fb9df4158ba9e9ee32913a179b6d5f7183f8` | pending | pending | `5a02c082b531b6731dbdd6e55ccc8798ba2514bbb27df8e9c2ef74c88752830d` | pending | E1-P1A-BYTES1 |
| P1 | `media.whiteboard_animation` snapshot identity | SHA-256 | `2d0b33ae493f4879805ce9b7618fab16f1737222e53c86403f471324387ad7d3` | pending | pending | `55dbed4743cad90f80d1603ed639508c8e3a6e650a1abccfe7d4e8b2e148742c` | pending | E1-P1A-BYTES1 |
| P1 | Snapshot path-set cardinality per capability | files | pending | pending | pending | stable | pending | E1-P1A-PATHS1 |

## B2 - P2 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P2 | Vendor suite | tests | 15/17 | pending | pending | 17/17 | pending | E2-P2A-REGRESSION1 |
| P2 | Host Projection | tests | blocked | pending | pending | 30/30 | pending | E2-P2A-REGRESSION1 |
| P2 | Manus Skill package | tests | blocked | pending | pending | 8/8 | pending | E2-P2A-REGRESSION1 |
| P2 | Foundation | tests | not run | pending | pending | 28/28 | pending | E2-P2A-REGRESSION1 |
| P2 | C35 | tests | not run | pending | pending | 57/57 | pending | E2-P2A-REGRESSION1 |

## Non-Benchmarkable Notes

Hash semantics, root cause, and Supervisor verdict are evidence/authority
decisions, not benchmark metrics.
