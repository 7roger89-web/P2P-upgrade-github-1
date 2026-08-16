# P2P Native Decision Trace — Release / Install Integration Benchmark Ledger

## Metadata

- Date: `2026-08-12`
- Plan: `docs/plans/2026-08-12-p2p-native-decision-trace-release-install/2026-08-12-p2p-native-decision-trace-release-install-plan.md`
- Evidence: `docs/plans/2026-08-12-p2p-native-decision-trace-release-install/2026-08-12-p2p-native-decision-trace-release-install-evidence.md`
- Benchmark: `docs/plans/2026-08-12-p2p-native-decision-trace-release-install/2026-08-12-p2p-native-decision-trace-release-install-benchmark.md`
- Actual status: `docs/plans/2026-08-12-p2p-native-decision-trace-release-install/2026-08-12-p2p-native-decision-trace-release-install-actual-status.md`

## Benchmark Rules

Record measured counts, sizes, hashes, lifecycle counts, and before/after
behavior only. Do not treat fixtures as real project quality or live quorum
performance. Pass/fail narrative belongs in evidence.

## B0 - P0 Baseline Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|---|---|---:|---:|---:|---:|---:|---:|---|
| P0 | baseline release version | string | `8.4.7-C-codex.4` | `8.4.7-C-codex.4` |  | preserve | 0 | `E0-P0A-VERSION1` |
| P0 | old artifact Decision Trace members | count | 0 | 0 |  | new artifact >0 | 0 | `E0-P0A-GAP1` |
| P0 | old artifact package doctor | result | PASS | PASS |  | PASS | 0 | `E0-P0A-BASELINE1` |
| P0 | canonical denominator | count | 8 | 8 |  | 8 | 0 | `E0-P0A-GOV1` |
| P0 | full quorum | ratio | `8/8` | `8/8` |  | `8/8` | 0 | `E0-P0A-GOV1` |

## B1 - P1 Package Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|---|---|---:|---:|---:|---:|---:|---:|---|
| P1 | release revision | string | `.4` |  |  | `.5` | +1 | `E1-P1B-META1` |
| P1 | runtime Decision Trace module members | count | 0 |  |  | >=2 | +2 | `E1-P1A-PAYLOAD1` |
| P1 | package doctor | result | PASS old ZIP |  |  | PASS new ZIP | measured | `E1-P1A-DOCTOR1` |
| P1 | new artifact content files | count | N/A |  |  | manifest-consistent | measured | `E1-P1B-PACKAGE1` |
| P1 | new artifact ZIP members | count | N/A |  |  | manifest-consistent | measured | `E1-P1B-PACKAGE1` |
| P1 | new artifact size | bytes | N/A |  |  | recorded | measured | `E1-P1B-PACKAGE1` |
| P1 | new artifact SHA-256 | digest | N/A |  |  | recorded | measured | `E1-P1B-PACKAGE1` |

## B2 - P2 Lifecycle Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|---|---|---:|---:|---:|---:|---:|---:|---|
| P2 | fresh install | result | not run |  |  | PASS | measured | `E2-P2B-FRESH1` |
| P2 | upgrade | result | not run |  |  | PASS | measured | `E2-P2B-UPGRADE1` |
| P2 | same-version reinstall | result | not run |  |  | PASS | measured | `E2-P2B-REINSTALL1` |
| P2 | protected state categories preserved | count | 0 |  |  | all declared | measured | `E2-P2A-IDEMPOTENCE1` |
| P2 | old ledger bytes preserved | boolean | N/A |  |  | true | measured | `E2-P2B-UPGRADE1` |
| P2 | reinstall-created duplicate trace records | count | N/A |  |  | 0 | measured | `E2-P2B-REINSTALL1` |
| P2 | material capture | ratio | 0/1 |  |  | 1/1 | measured | `E2-P2C-TRACE1` |
| P2 | routine trace spam | count | 0 |  |  | 0 | measured | `E2-P2C-TRACE1` |

## B3 - P3 Certification Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|---|---|---:|---:|---:|---:|---:|---:|---|
| P3 | RI-DT cases | count | 0/35 |  |  | 35/35 | measured | `E3-P3A-RI1` |
| P3 | full unittest regression | count | 48/48 native trace baseline |  |  | all PASS | measured | `E3-P3B-CLOSURE1` |
| P3 | package boundary forbidden members | count | N/A |  |  | 0 | measured | `E3-P3A-ARTIFACT1` |
| P3 | secret findings | count | 0 |  |  | 0 | measured | `E3-P3B-CLOSURE1` |
| P3 | next Goal recommendations | count | N/A |  |  | exactly 1 or STOP | measured | `E3-P3B-NEXT1` |

## Non-Benchmarkable Notes

Browser, Docker, public publication, real user project quality, and real
eight-thread host quorum are not measured by this CLI/package lifecycle Goal.

## Final measured values

| Metric | Final | Evidence |
|---|---:|---|
| Release version | 8.4.7-C-codex.5 | final artifact and metadata |
| Artifact size | 2,329,263 bytes | release-boundary-certification.json |
| Content files / ZIP members | 397 / 399 | release-boundary-certification.json |
| Final SHA-256 | f88dbf706c4ac85a8aadf38960923cdc8e4ba6e415b83f3f1726692fb3ad8dda | release-boundary-certification.json |
| Old .4 SHA-256 unchanged | true | supervisor-audit.json |
| Fresh PowerShell install | PASS | installer output and fresh fixture |
| Fresh POSIX install | PASS | POSIX installer output and runtime doctor |
| Upgrade ledger byte preservation | true | upgrade-verification-before-trace.json |
| Post-upgrade native trace count | 1 | upgrade-post-trace.json |
| Same-version reinstall duplicate trace delta | 0 | same-version-reinstall.json |
| Runtime behavior cases | 24/24 PASS | decision-trace-runtime-certification.json |
| UIUX regression gates | DW1–DW18 PASS | uiux-regression.json |
| Core unittest regression | 48/48 PASS | supervisor-full-regression.log |
| Boundary forbidden members | 0 | release-boundary-certification.json |
| Package secret findings | 0 | p2p-secret-scan/1 |
| Beginner WHY native records before/after | 0 → 1 | beginner-why-before-after.json |
| Beginner WHY Decision ID required before/after | yes → no | beginner-why-before-after.json |
| Exactly one next Goal | 1 | supervisor acceptance report |
