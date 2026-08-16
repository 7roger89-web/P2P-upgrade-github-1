# P2P AESTHETICA Synthetic Beginner Acceptance Final Closure Benchmark Ledger

## Metadata

- Date: `2026-08-13`
- Plan: `docs/plans/2026-08-13-p2p-aesthetica-synthetic-beginner-acceptance-final-closure/2026-08-13-p2p-aesthetica-synthetic-beginner-acceptance-final-closure-plan.md`
- Evidence: `docs/plans/2026-08-13-p2p-aesthetica-synthetic-beginner-acceptance-final-closure/2026-08-13-p2p-aesthetica-synthetic-beginner-acceptance-final-closure-evidence.md`
- Benchmark: `docs/plans/2026-08-13-p2p-aesthetica-synthetic-beginner-acceptance-final-closure/2026-08-13-p2p-aesthetica-synthetic-beginner-acceptance-final-closure-benchmark.md`
- Actual status: `docs/plans/2026-08-13-p2p-aesthetica-synthetic-beginner-acceptance-final-closure/2026-08-13-p2p-aesthetica-synthetic-beginner-acceptance-final-closure-actual-status.md`

## Benchmark Rules

- Record measured artifact, inventory, lifecycle, and acceptance counts only.
- Do not turn design-review output into a product-performance claim.
- Keep `.12` and `.13` measurements separate.

## B0 - P0 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P0 | Fresh official specialist child | child count | 0 in prior failed acceptance | 1 | 1 | 1 | +1 | `E0-P0A-CHILD1` |
| P0 | Exact official receipt match | boolean | false | true | true | true | +1 | `E0-P0A-RECEIPT1` |
| P0 | Strict first-decision invariant | boolean | false in fresh trace | false | false | true | 0 | `E0-P0A-TRACE1`, `E0-P0A-SUP2` |

## B1 - P1 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P1 | Release artifact version | version | `.12` | `.13` candidate | `.13` candidate | `.13` | candidate created | `E1-P1B-PKG1` |
| P1 | Protected baseline SHA unchanged | boolean | true | true | true | true | 0 | `E1-P1A-META2` |
| P1 | Candidate package file count | files | N/A | 398 | 398 | recorded | N/A | `E1-P1B-PKG1` |
| P1 | Candidate checksum count | checksums | N/A | 399 | 399 | recorded | N/A | `E1-P1B-PKG1` |

## B2 - P2 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P2 | Lifecycle paths | pass count | inherited `.12` PASS | 0/4 run | 0/4 run | 4/4 | not run | `E2-P2A-LIFE1..E2-P2A-LIFE2` |
| P2 | Technical release gate | status | not prepared | not prepared | not prepared | PASS | not run | `E2-P2B-GATE1` |

## Non-Benchmarkable Notes

The `.13` measurements are candidate-only because strict first-decision acceptance was rejected; no lifecycle or technical-gate PASS is implied.

The specialist’s design review, supervisor verdict, routing classification, fallback behavior, and security/canonical checks are acceptance evidence rather than performance benchmarks. Existing verified 10/10, 40-case, 68/68, DT1–DT24, DW1–DW18, and paired-eval measurements are reused unless a material change invalidates them.
