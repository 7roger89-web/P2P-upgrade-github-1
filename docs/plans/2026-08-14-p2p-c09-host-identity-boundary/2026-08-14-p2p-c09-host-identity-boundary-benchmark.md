# P2P-C09 Supported Generic Host Identity and Route Observation Boundary Benchmark Ledger

## Metadata

- Date: `2026-08-14`
- Plan: `docs/plans/2026-08-14-p2p-c09-host-identity-boundary/2026-08-14-p2p-c09-host-identity-boundary-plan.md`
- Evidence: `docs/plans/2026-08-14-p2p-c09-host-identity-boundary/2026-08-14-p2p-c09-host-identity-boundary-evidence.md`
- Benchmark: `docs/plans/2026-08-14-p2p-c09-host-identity-boundary/2026-08-14-p2p-c09-host-identity-boundary-benchmark.md`
- Actual status: `docs/plans/2026-08-14-p2p-c09-host-identity-boundary/2026-08-14-p2p-c09-host-identity-boundary-actual-status.md`

## Benchmark Rules

This ledger records measured inventory, identity, artifact, and bounded live
probe counts only. It does not score output quality, compare A/B conditions,
estimate tokens/cost, calculate non-inferiority, or claim context efficiency.
C08 scored trials remain `0`.

## B0 - P0 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P0 | Frozen route scenarios inspected | scenarios | 12 | 12 | 12 | 12 | 0 | `E0-P0A-SRC1` |
| P0 | Canonical quorum identities | identities | 8 | 8 | 8 | 8 | 0 | `E0-P0A-REG1` |
| P0 | Full quorum denominator | ratio | 8/8 | 8/8 | 8/8 | 8/8 | 0 | `E0-P0A-REG1` |
| P0 | C08 scored trials executed | trials | 0 | 0 | 0 | 0 for C09 | 0 | `E0-P0A-SRC1` |
| P0 | Hook linked flows | flows | 8 | 8 | 8 | observe current | 0 | `E0-P0A-GRAPH1` |
| P0 | Live boundary linked flows | flows | 11 | 11 | 11 | preserve current | 0 | `E0-P0A-GRAPH1` |

## B1 - P1 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P1 | Allow-listed host identity classes | classes | 1 observed | 3 configured (`HOST_DEFAULT / GENERIC`, `CUSTOM_PROFILE`, optional Aesthetica) | 3 configured; real generic/canonical host observation still unavailable | canonical + optional + supported generic | configured boundary complete; live observation blocked | `E1-P1A-HOOK1`, `E1-P1A-CONFIG1`, `E2-HOST-BLOCKER1` |
| P1 | Focused identity/route test count | tests | 14 | 24 | 24 | all required positive/negative cases | +10 | `E1-P1C-IDENTITYTEST1`, `E1-P1C-LIVETEST1` |

## B2 - P2 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P2 | Accepted standard/non-UI live proofs | proofs | 0 | 0 accepted; 1 real attempt without receipt | 0 | 1 | blocked by official default receipt absence | `E2-P2A-NONUI1`, `E2-HOST-BLOCKER1` |
| P2 | Accepted normal UI live proofs without AESTHETICA | proofs | 0 | 0 | 0 | 1 | blocked by the same official default receipt absence | `E2-P2A-NORMALUI1` |
| P2 | Accepted accessibility-heavy AESTHETICA proofs | proofs | 0 fresh C09 proofs; historical C07 retained separately | 0 fresh C09 proofs | 0 fresh C09 proofs | 1 | blocked/not run; historical evidence not relabeled | `E2-P2B-A11Y1`, `E0-P0A-C07-1` |
| P2 | Accepted canonical custom-profile proofs | proofs | 0 | 0 accepted; 1 real attempt without receipt | 0 | 1 where supported | blocked by official canonical receipt absence | `E2-P2B-CANONICAL1`, `E2-HOST-BLOCKER1` |
| P2 | C08 scored trials | trials | 0 | 0 | 0 | 0 for C09 | 0 | `E2-HOST-BLOCKER1` |

## B3 - P3 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P3 | Protected `.15` SHA-256 | hash | `af4d63a882dabfde20ac237574590ec584ee2944bc4cdc30b6a07bf7f681e195` | `af4d63a882dabfde20ac237574590ec584ee2944bc4cdc30b6a07bf7f681e195` | unchanged | unchanged | 0 | `E3-P3A-PACKAGE1` |
| P3 | Protected `.16-r2` SHA-256 | hash | `410572d73aa06dadbd8fe1da068fe217eabeb7efc11cf35fc9576c750a4ee8cf` | `410572d73aa06dadbd8fe1da068fe217eabeb7efc11cf35fc9576c750a4ee8cf` | unchanged | unchanged | 0 | `E3-P3A-PACKAGE1` |
| P3 | Protected `.17` SHA-256 | hash | `50eb59740034fb724dfe23d19d7f700c8143cfb9efd07f6cdf0a33d0ed041197` | `50eb59740034fb724dfe23d19d7f700c8143cfb9efd07f6cdf0a33d0ed041197` | unchanged | unchanged | 0 | `E3-P3A-PACKAGE1` |
| P3 | New candidate SHA-256 | hash | N/A | `5dd547319a4d5ed0d529017d2514470c81e9456d4c448c7820b4adc9868f02c8` | `5dd547319a4d5ed0d529017d2514470c81e9456d4c448c7820b4adc9868f02c8` | new immutable candidate if affected | recorded; unpromoted | `E3-P3A-PACKAGE1` |
| P3 | Full repository regression | tests/time | N/A | 111/111 in 257.196s | 111/111 | PASS | PASS | `E3-P3A-REGRESSION1` |

## Non-Benchmarkable Notes

- Route correctness, fail-closed behavior, receipt provenance, security, and Supervisor acceptance are validation evidence, not performance benchmarks.
- Provider token/cost telemetry remains UNKNOWN unless the official host exposes it; no inference is permitted.
