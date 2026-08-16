# P2P Native Decision Trace - Governance Reference Normalization Benchmark Ledger

## Metadata

- Date: `2026-08-13`
- Plan: `docs/plans/2026-08-13-p2p-native-decision-trace-governance-reference-normalization/2026-08-13-p2p-native-decision-trace-governance-reference-normalization-plan.md`
- Evidence: `docs/plans/2026-08-13-p2p-native-decision-trace-governance-reference-normalization/2026-08-13-p2p-native-decision-trace-governance-reference-normalization-evidence.md`
- Benchmark: `docs/plans/2026-08-13-p2p-native-decision-trace-governance-reference-normalization/2026-08-13-p2p-native-decision-trace-governance-reference-normalization-benchmark.md`
- Actual status: `docs/plans/2026-08-13-p2p-native-decision-trace-governance-reference-normalization/2026-08-13-p2p-native-decision-trace-governance-reference-normalization-actual-status.md`

## Benchmark Rules

Record measured values only. The target is valid references resolved and
invalid references still missing, not zero missing references globally.

## B0 - P0 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|---|---|---:|---:|---:|---:|---|---:|---|
| P0 | Present structured links | count | 9 | 9 | 9 | reproduce | 0 | E0-P0A-REPRO1 |
| P0 | False missing policy links | count | 2 | 2 | 2 | reproduce | 0 | E0-P0A-REPRO1 |
| P0 | Canonical identities | count | 8 | 8 | 8 | 8 | 0 | E0-P0A-AUTH1 |
| P0 | Quorum denominator | integer | 8 | 8 | 8 | 8 | 0 | E0-P0A-AUTH1 |
| P0 | .5 ZIP size | bytes | 2329263 | 2329263 | 2329263 | unchanged | 0 | E0-P0A-BASE1 |

## B1 - P1 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Evidence |
|---|---|---:|---:|---:|---:|---|---|
| P1 | New canonical policy refs | count | 0 | 2 | 2 | 2 | 2 |
| P1 | Legacy bare policy refs resolved | count | 0 | 1 | 1 | 1 | 1 |
| P1 | Deliberately invalid policy refs | count | n/a | 1 | 1 | 1 missing | 1 |
| P1 | Runtime files changed | count | 0 | 1 | 1 | minimal | 1 |

## B2 - P2 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Evidence |
|---|---|---:|---:|---:|---:|---|---|
| P2 | Fresh valid policy refs resolved | count | 0 | 2 | 2 | 2 | +2 | E2-P2B-FRESH1 |
| P2 | Fresh invalid refs missing | count | n/a | 1 | 1 | 1 missing | 1 honest missing | E2-P2C-PORTNEG1 |
| P2 | Upgrade ledger preservation | boolean | n/a | true | true | true | pass | E2-P2B-UPGRADE1 |
| P2 | Reinstall ledger mutation | count | n/a | 0 | 0 | 0 | 0 | E2-P2B-REINSTALL1 |
| P2 | Candidate ZIP size/hash/count | recorded | n/a | 2,336,913 / b8689fb8... / 399 | 2,336,913 / b8689fb8... / 399 | recorded | recorded | E2-P2A-ARTIFACT1 |

## Non-Benchmarkable Notes

Temporal, supersession, contradiction, redaction, canonical safety, and
no-user-project claims are status assertions in the evidence ledger.

## Final Certification

| Acceptance family | Result | Evidence |
|---|---|---|
| RN1-RN6: reproduce, root cause, exact normalization, honest invalid failure | PASS | E0-P0A-REPRO1, E0-P0A-ROOTCAUSE1, E1-P1B-NEG1, E2-P2C-PORTNEG1 |
| RN7-RN12: Windows/POSIX, legacy, fresh WHY, upgrade, reinstall | PASS | E2-P2B-FRESH1, E2-P2B-UPGRADE1, E2-P2B-REINSTALL1, E2-P2C-PORTNEG1 |
| RN13-RN15: temporal/supersession/contradiction, security, package doctor | PASS | E2-P2A-DOCTOR1, E2-P2C-REGRESS1 |
| RN16-RN19: canonical 8/8, no external dependency, no user project | PASS | E2-P2C-REGRESS1, E3-P3A-BOUNDARY1 |
| RN20: exactly one fresh residual-risk recommendation | PASS | E2-P2C-NEXT1, E3-P3A-NEXT1 |
| Independent supervisor | PASS | E3-P3A-SUPERVISOR1 |
