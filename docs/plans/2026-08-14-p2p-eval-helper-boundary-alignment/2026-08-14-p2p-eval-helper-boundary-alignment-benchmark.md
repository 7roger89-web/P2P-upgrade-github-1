# P2P Eval Helper Boundary Alignment — Prerequisite for Real Context-Efficiency Benchmark Benchmark Ledger

## Metadata

- Date: `2026-08-14`
- Plan: `docs/plans/2026-08-14-p2p-eval-helper-boundary-alignment/2026-08-14-p2p-eval-helper-boundary-alignment-plan.md`
- Evidence: `docs/plans/2026-08-14-p2p-eval-helper-boundary-alignment/2026-08-14-p2p-eval-helper-boundary-alignment-evidence.md`
- Benchmark: `docs/plans/2026-08-14-p2p-eval-helper-boundary-alignment/2026-08-14-p2p-eval-helper-boundary-alignment-benchmark.md`
- Actual status: `docs/plans/2026-08-14-p2p-eval-helper-boundary-alignment/2026-08-14-p2p-eval-helper-boundary-alignment-actual-status.md`

## Benchmark Rules

- Record only measured counts, sizes, hashes, and deterministic lifecycle outcomes.
- Do not translate character/byte counts into fake tokens or costs.
- Do not report wall-clock or provider metrics unless the host exposes them exactly.
- This Goal measures boundary readiness and package consistency; it does not benchmark context efficiency.

## B0 - P0 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P0 | Current development checkout doctor failing payload groups | check count | 2 | 1 role mismatch | 0 portable-payload false positives | 0 misleading payload checks | -2 groups | E0-P0A-FAIL2; E2-P2B-TEST2 |
| P0 | Helper contract mismatch reproduced | boolean | true | true | false after resolver | false | -1 | E0-P0A-FAIL1; E2-P2A-TEST3 |

## B1 - P1 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P1 | Candidate paths before incompatible-contract filtering | count | 2 | 2 | 2 | measured | 0 | E1-P1A-RESOLVE1 |
| P1 | Compatible project-eval v2 candidates | count | 1 | 1 | 1 | one deterministic compatible helper per role | 0 | E1-P1A-RESOLVE2 |
| P1 | Helper implementations with distinct CLI contracts | count | 2 | 2 | 2 | explicitly classified | 0 | E1-P1A-CONTRACT1..E1-P1A-CONTRACT3 |
| P1 | Official `.15` artifact SHA-256 preserved | hash | af4d63a882dabfde20ac237574590ec584ee2944bc4cdc30b6a07bf7f681e195 | same | same | exact match | 0 | E1-P1B-PACKAGE1 |

## B2 - P2 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P2 | Focused helper/doctor regression tests | tests | 0 | 9 | 9 | all affected tests pass | +9 | E2-P2A-TEST1; E2-P2A-TEST2; E2-P2A-TEST5 |
| P2 | Full repository unit/regression tests | tests | 76 | 81 | 81 | all pass | +5 tests | E2-P2A-TEST4 |
| P2 | Production candidates under `.tmp`/quarantine | count | UNKNOWN | 0 | 0 | 0 | UNKNOWN -> 0 | E2-P2A-TEST2; E3-P3A-REG3 |
| P2 | New eval systems introduced | count | 0 | 0 | 0 | 0 | 0 | E2-P2A-CODE1 |

## B3 - P3 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P3 | Lifecycle cases A–E completed | cases | 0 | 5 | 5 | 5 | +5 | E3-P3A-LIFE1..E3-P3A-LIFE5 |
| P3 | Candidate package content files | files | 398 | 398 | 398 | manifest match | 0 | E2-P2B-TEST3; E3-P3A-REG3; E3-P3A-LIFE6 |
| P3 | Candidate package checksum entries | entries | 399 | 399 | 399 | manifest match | 0 | E2-P2B-TEST3; E3-P3A-LIFE6 |
| P3 | Canonical identity count | identities | 8 | 8 | 8 | 8 | 0 | E3-P3A-REG5 |
| P3 | Quorum denominator | identities | 8 | 8 | 8 | 8 | 0 | E3-P3A-REG5 |
| P3 | Full quorum | fraction | 8/8 | 8/8 | 8/8 | 8/8 | 0 | E3-P3A-REG5 |

## Non-Benchmarkable Notes

- Real model input tokens, cached input tokens, output tokens, provider cost, child-agent calls, and host wall-clock latency are not certified by this boundary Goal unless exact host telemetry is available. Report `UNKNOWN`.
- Real worker/provider execution is intentionally out of scope. `REAL_AB_BENCHMARK_READY` is a boundary-readiness decision, not evidence that the future benchmark has run.
- UI/browser/Docker metrics are not applicable to this Python CLI/package task.
- Current project-eval v2 suite validation/gate: `PASS`; preserved 12-case proxy validation/gate: `PASS`. These are contract/evidence-structure checks, not real worker/provider quality or token-savings proof.
- Whole-repo secret scan: `FAIL` with 7 reference/documentation findings; changed-surface scans pass. This is tracked as separate secret-hygiene work and is not silently converted into a source-change failure.
- Git diff/change detection: `UNKNOWN/UNAVAILABLE` because Anvien reports `Git diff failed: exit status 129`; no commit was claimed.
- The first `.16` candidate remains immutable; the post-review installed-root isolation fix is represented by the separately named `.16-r2` artifact with the same package version and a new SHA-256.
