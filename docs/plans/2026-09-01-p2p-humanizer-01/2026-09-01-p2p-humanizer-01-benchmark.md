# P2P-HUMANIZER-01 Benchmark Ledger

## Metadata

- Date: `2026-09-01`
- Plan: `docs/plans/2026-09-01-p2p-humanizer-01/2026-09-01-p2p-humanizer-01-plan.md`
- Evidence: `docs/plans/2026-09-01-p2p-humanizer-01/2026-09-01-p2p-humanizer-01-evidence.md`
- Benchmark: `docs/plans/2026-09-01-p2p-humanizer-01/2026-09-01-p2p-humanizer-01-benchmark.md`
- Actual status: `docs/plans/2026-09-01-p2p-humanizer-01/2026-09-01-p2p-humanizer-01-actual-status.md`

## Benchmark Rules

The benchmark file records measurements.

It should contain:

- metadata and benchmark rules;
- benchmark sections by plan phase;
- inventory count;
- package/file-size/hash measurements when relevant;
- before/after numbers;
- no command-log narrative or design decisions.

Only measured counts/hashes are recorded here. Test pass/fail and reasoning
remain in the evidence ledger.

## B0 - P0 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P0 | Current capability registry records | records | 67 | 67 | pending | 68 after one new record | pending | `E0-P0A-REG1` |
| P0 | Existing local vendor-snapshot capabilities | records | 15 | 15 | pending | 16 after one new record | pending | `E0-P0A-REG1` |
| P0 | Selected upstream files | files | 2 available (`SKILL.md`, `LICENSE`) | 2 audited | pending | 2 | pending | `E0-P0A-UP1` |
| P0 | Anvien parse failures | files | 0 | 0 | pending | 0 | 0 | `E0-P0A-GRAPH1` |

## B1 - P1 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P1 | Humanizer vendor snapshot files | files | 0 | 2 | 2 | 2 | +2 | `E1-P1A-SRC1` |
| P1 | Humanizer declared references/assets/scripts | entries | 0 | 0 | 0 | 0 | 0 | `E1-P1A-REG1` |
| P1 | Humanizer network/credential/install flags | enabled flags | 0 | 0 | 0 | 0 | 0 | `E1-P1A-REG1` |
| P1 | Focused Issue #51 test cases | cases | 0 | pending | pending | 7 | pending | `E1-P1B-TEST1..E1-P1B-TEST7` |

## B2 - P2 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P2 | Independent Supervisor verdict | verdict | not run | pending | pending | independent review | pending | `E2-P2A-SUP1` |
| P2 | One branch / one PR | items | 0 / 0 | pending | pending | 1 / 1 | pending | `E2-P2C-PR1` |

## Non-Benchmarkable Notes

- Naturalness, no-fabrication, voice calibration, and protected-span behavior
  are bounded fixture assertions, not product-performance benchmarks.
- No model/provider runtime is invoked or installed by this Markdown-skill
  integration, so live rewrite quality is intentionally `NOT_APPLICABLE` for
  this candidate.
- The seven wider-suite baseline failures are validation evidence, not a
  Humanizer benchmark and are not averaged into these counts.
