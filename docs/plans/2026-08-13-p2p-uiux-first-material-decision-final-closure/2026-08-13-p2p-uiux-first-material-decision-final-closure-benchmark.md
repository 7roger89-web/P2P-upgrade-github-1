# P2P UIUX First-Material-Decision Final Closure Benchmark Ledger

## Metadata

- Date: `2026-08-13`
- Plan: `docs/plans/2026-08-13-p2p-uiux-first-material-decision-final-closure/2026-08-13-p2p-uiux-first-material-decision-final-closure-plan.md`
- Evidence: `docs/plans/2026-08-13-p2p-uiux-first-material-decision-final-closure/2026-08-13-p2p-uiux-first-material-decision-final-closure-evidence.md`
- Benchmark: `docs/plans/2026-08-13-p2p-uiux-first-material-decision-final-closure/2026-08-13-p2p-uiux-first-material-decision-final-closure-benchmark.md`
- Actual status: `docs/plans/2026-08-13-p2p-uiux-first-material-decision-final-closure/2026-08-13-p2p-uiux-first-material-decision-final-closure-actual-status.md`

## Benchmark Rules

- Record measured counts, hashes, and pass/fail totals only.
- Do not convert specialist prose into performance claims.
- Keep `.13` and any conditional `.14` measurements separate.

## B0 - P0 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P0 | Existing first-decision fixture | cases | 10 | 10 | 10 | preserved | 0 | `E0-P0A-SKILL1` |
| P0 | Existing routing fixture | cases | 40 | 40 | 40 | preserved | 0 | `E0-P0A-REUSE1` |
| P0 | Protected `.13` SHA unchanged | boolean | true | true | true | true | 0 | `E0-P0A-BASELINE1` |

## B1 - P1 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P1 | New first-material matrix | cases | 0 | 24 | 24 | >=20 | +24 | `E1-P1A-FIXTURE1` |
| P1 | Matrix languages | count | 0 | 2 | 2 | 2 | +2 | `E1-P1A-FIXTURE1` |
| P1 | Focused test methods | pass count | 0 | 8/8 | 8/8 | all | +8 | `E1-P1B-TEST1` |
| P1 | Existing routing cases | cases | 40 | 40 | 40 | 40 | 0 | `E1-P1B-TEST2` |

## B2 - P2 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P2 | Fresh native coordinator tasks | count | 0 post-fix | 1 | 1 | 1 | +1 | `E2-P2A-TRACE1` |
| P2 | Fresh AESTHETICA children | count | 0 post-fix | 1 | 1 | 1 if material | +1 | `E2-P2A-RECEIPT1` |
| P2 | Conditional `.14` lifecycle paths | pass count | not applicable | 5/5 | 5/5 | 5/5 if created | +5 | `E2-P2B-LIFE1` |
| P2 | `.14` package file/checksum count | count | not applicable | 398/399 | 398/399 | package build PASS | new | `E2-P2B-PKG1` |
| P2 | `.14` artifact SHA-256 | hash | not applicable | `36ee7a23ccd3e3a2d90512ebd911306bb86e7c6cfcf1c0362842ce36f458d744` | same | new | `E2-P2B-PKG1` |

## Non-Benchmarkable Notes

Root-cause classification, first/final semantic intent, fallback, security, canonical quorum, and supervisor verdict are acceptance evidence rather than performance benchmarks. Closed prior gate counts are reused unless affected inputs change. Lifecycle count is five required paths: fresh install, `.9`, `.10`, `.12`, `.13` upgrades, plus the separate same-version reinstall check.
