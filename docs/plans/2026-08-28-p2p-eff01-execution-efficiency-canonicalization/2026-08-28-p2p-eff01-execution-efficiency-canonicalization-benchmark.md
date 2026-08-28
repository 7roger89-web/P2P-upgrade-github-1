# P2P-EFF01 Execution Efficiency Canonicalization Benchmark Ledger

## Metadata

- Date: `2026-08-28`
- Plan: `docs/plans/2026-08-28-p2p-eff01-execution-efficiency-canonicalization/2026-08-28-p2p-eff01-execution-efficiency-canonicalization-plan.md`
- Evidence: `docs/plans/2026-08-28-p2p-eff01-execution-efficiency-canonicalization/2026-08-28-p2p-eff01-execution-efficiency-canonicalization-evidence.md`
- Benchmark: `docs/plans/2026-08-28-p2p-eff01-execution-efficiency-canonicalization/2026-08-28-p2p-eff01-execution-efficiency-canonicalization-benchmark.md`
- Actual status: `docs/plans/2026-08-28-p2p-eff01-execution-efficiency-canonicalization/2026-08-28-p2p-eff01-execution-efficiency-canonicalization-actual-status.md`

## Benchmark Rules

This ledger records measured counts and hashes only. Test pass/fail narrative belongs in the evidence ledger.

## B0 - P0 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P0 | Candidate source files scanned by Anvien | files | 980 | 985 | pending | current candidate graph | +5 | E0-P0A-GRAPH1, E2-P2A-DETECT1 |
| P0 | Parsed code files | files | 175 | 176 | pending | 0 parse failures | +1 | E0-P0A-GRAPH1, E2-P2A-DETECT1 |
| P0 | Candidate base commit | SHA | 23076954e89dec58dbcf0f14bdce15843226acbc | 23076954e89dec58dbcf0f14bdce15843226acbc | 23076954e89dec58dbcf0f14bdce15843226acbc | exact live origin/main | 0 | E0-P0A-AUTH1 |

## B1 - P1 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P1 | Production policy files changed | files | 0 | 1 | 1 | 1 | +1 | E1-P1A-IMPL1 |
| P1 | Direct acceptance test files added | files | 0 | 1 | 1 | 1 | +1 | E1-P1B-TEST1 |
| P1 | Execution lanes covered | lanes | 0 | 4 | 4 | 4 | +4 | E1-P1B-TEST1 |

## B2 - P2 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P2 | Candidate commit count after implementation | commits | 0 | 3 | 4 | exact isolated checkpoint(s) | +4 | E1-P1A-IMPL1, E2-CLOSE-SHA1 |
| P2 | Candidate tree identity | SHA | pending | 6cdd0a330cd0c06fcc102e879ca5a5ed599dc57e | emitted in terminal packet | exact reviewed subject plus closure artifacts | n/a | E2-CLOSE-SHA1 |

## Non-Benchmarkable Notes

- Efficiency gain is a policy-selection reduction claim, not a measured production latency/cost benchmark in this offline pure module. The candidate will report the expected qualitative gain and will not invent token, price, latency, or quality numbers.
- No broad/full regression count is a target; it is conditional on material evidence.
