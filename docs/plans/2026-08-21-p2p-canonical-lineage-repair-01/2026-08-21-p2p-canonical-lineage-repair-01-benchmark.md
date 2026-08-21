# P2P Canonical Lineage Repair 01 Benchmark Ledger

## Metadata

- Date: `2026-08-21`
- Plan: `docs/plans/2026-08-21-p2p-canonical-lineage-repair-01/2026-08-21-p2p-canonical-lineage-repair-01-plan.md`
- Evidence: `docs/plans/2026-08-21-p2p-canonical-lineage-repair-01/2026-08-21-p2p-canonical-lineage-repair-01-evidence.md`
- Benchmark: `docs/plans/2026-08-21-p2p-canonical-lineage-repair-01/2026-08-21-p2p-canonical-lineage-repair-01-benchmark.md`
- Actual status: `docs/plans/2026-08-21-p2p-canonical-lineage-repair-01/2026-08-21-p2p-canonical-lineage-repair-01-actual-status.md`

## Benchmark Rules

- Record measured counts only; validation narratives belong in evidence.
- Preserve baseline/latest/final values and exact evidence IDs.
- Do not claim performance or runtime proof from synthetic fixtures.

## B0 - P0 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P0 | Graph scanned files | files | 424 | 424 | 424 | 424 | 0 | E0-P0A-ANV1 |
| P0 | Parsed code files | files | 51 | 51 | 51 | 51 | 0 | E0-P0A-ANV1 |
| P0 | Graph nodes | nodes | 17357 | 17357 | 17357 | 17357 | 0 | E0-P0A-ANV1 |
| P0 | Graph relationships | relationships | 20161 | 20161 | 20161 | 20161 | 0 | E0-P0A-ANV1 |
| P0 | Canonical official baseline | version | 8.4.7-C-codex.19 | 8.4.7-C-codex.19 | 8.4.7-C-codex.19 | unchanged | 0 | E0-P0A-GIT2 |

## B1 - P1 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P1 | Recovered implementation source commits | commits | 0 | 18 material refs/commits recorded | 18 material refs/commits recorded | all verified required commits | +18 | E0-P0A-MATRIX3, E1-P1A-SRC1 |
| P1 | Active authority files with official drift | files | 0 | 0 | 0 | 0 | 0 | E1-P1B-AUTH1 |
| P1 | Package source mutations during build | mutations | unknown | not run before Manus blocker | not run before Manus blocker | 0 | N/A | E1-P1B-PKG1 |

## B2 - P2 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P2 | Candidate artifacts minted | artifacts | 0 | 0 | 0 | exactly 1 | blocked before mint | E2-P2B-MINT1 |
| P2 | Archive members | members | unknown | not run | not run | accounted exactly | blocked before mint | E2-P2B-INVENTORY1 |
| P2 | Unaccounted members | members | unknown | not run | not run | 0 | blocked before mint | E2-P2B-INVENTORY1 |
| P2 | Duplicate paths | paths | unknown | not run | not run | 0 | blocked before mint | E2-P2B-INVENTORY1 |
| P2 | Unsafe archive paths | paths | unknown | not run | not run | 0 | blocked before mint | E2-P2B-INVENTORY1 |
| P2 | A-Z negative matrix | cases | 0 | candidate-specific not run | candidate-specific not run | 26/26 | blocked before mint | E2-P2A-NEG1 |
| P2 | New unexplained failures | failures | unknown | 0 in scoped regression; 6 safe skips | 0 in scoped regression; 6 safe skips | 0 | 0 unexplained | E2-P2A-REG1 |
| P2 | Authoritative project mutations | mutations | 0 | 0 | 0 | 0 | 0 | E2-P2A-MAP1 |

## Non-Benchmarkable Notes

- Live Manus availability, authority classification, and historical truth are evidence claims, not performance benchmarks.
- Docker/Playwright metrics are not applicable to this non-UI Python package task.
