# P2P AERG/FW01 Compatibility Verdict Shape Repair Benchmark Ledger

## Metadata

- Date: 2026-08-24
- Plan: docs/plans/2026-08-24-aerg-fw01-compatibility-verdict-shape-repair/2026-08-24-aerg-fw01-compatibility-verdict-shape-repair-plan.md
- Evidence: docs/plans/2026-08-24-aerg-fw01-compatibility-verdict-shape-repair/2026-08-24-aerg-fw01-compatibility-verdict-shape-repair-evidence.md
- Benchmark: docs/plans/2026-08-24-aerg-fw01-compatibility-verdict-shape-repair/2026-08-24-aerg-fw01-compatibility-verdict-shape-repair-benchmark.md
- Actual status: docs/plans/2026-08-24-aerg-fw01-compatibility-verdict-shape-repair/2026-08-24-aerg-fw01-compatibility-verdict-shape-repair-actual-status.md

## Benchmark Rules

Only measured counts, durations, hashes, and inventories are recorded here. Pass/fail narrative belongs in the evidence ledger.

## B0 - P0 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P0 | full capability authoritative run | tests | 362 pass / 6 skip | 367 pass / 6 skip | 367 pass / 6 skip | no failures; five new tests included | +5 tests | E2-P2B-REG1 |
| P0 | validator | checks | 52/59 | 52/59 | 52/59 | inherited 52/59; seven named failures | 0 | E2-P2B-REG1 |
| P0 | malformed compatibility | cases | 1 fail-open | 0 fail-open | 0 fail-open | 0 fail-open | -1 | E2-P2A-RUNTIME1 |
| P0 | production source files changed in repair window | files | 1 | 1 | 1 | 1 | 0 | E2-P2A-SRC1 |

## B1 - P1 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P1 | malformed matrix cases | cases | 1 known | 18 subcases | 18 subcases blocked | all fail closed | +17 covered cases | E1-P1A-RED1, E2-P2A-RUNTIME1 |
| P1 | RED test commit | commits | 0 | 1 | 1 test-only | 1 test-only | +1 | E1-P1B-COMMIT1 |

## B2 - P2 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P2 | malformed matrix | cases | 1 known | 18/18 blocked | 18/18 blocked | 0 fail-open | closed | E2-P2A-RUNTIME1 |
| P2 | full capability UTF-8 | tests | 362 pass / 6 skip | 367 pass / 6 skip | 367 pass / 6 skip | 0 failures | +5 new tests | E2-P2B-REG1 |
| P2 | new runtime findings | findings | 1 | 0 | 0 | 0 | -1 | E2-P2B-REG1 |

## Final measured regression counts

| Surface | Result |
|---------|--------|
| FW01/AERG/QI fail-closed module | 15/15 |
| FW01 durable checkpoint gate | 6/6 |
| QI | 44 pass / 1 skip |
| AERG focused | 17/17 |
| Full capability, UTF-8 | 367 pass / 6 skip |
| C43 | 9/9 |
| RF01 orientation | 7/7 |
| RF01 packaging | 2/2 |
| Compile boundary | PASS |
| Framework validator | 52/59; seven inherited failures |

## Non-Benchmarkable Notes

No UI, database, Docker, performance, or external-host benchmark is in scope. Windows cp1252 runner errors remain an out-of-scope portability observation.
