# P2P-C19 Task-Targeted Context Retrieval, Coverage & Reuse Foundation Benchmark Ledger

## Metadata

- Date: `2026-08-16`
- Plan: `docs/plans/2026-08-16-p2p-c19-task-targeted-context/2026-08-16-p2p-c19-task-targeted-context-plan.md`
- Evidence: `docs/plans/2026-08-16-p2p-c19-task-targeted-context/2026-08-16-p2p-c19-task-targeted-context-evidence.md`
- Benchmark: `docs/plans/2026-08-16-p2p-c19-task-targeted-context/2026-08-16-p2p-c19-task-targeted-context-benchmark.md`
- Actual status: `docs/plans/2026-08-16-p2p-c19-task-targeted-context/2026-08-16-p2p-c19-task-targeted-context-actual-status.md`

## Benchmark Rules

Measurements are limited to deterministic local proxies and fixture counts. They are not tokens, cost, latency, quality, or universal optimization claims.

## B0 - P0 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P0 | Anvien scanned files | files | N/A | 415 | 415 | inventory recorded | N/A | E0-P0A-ANVIEN |
| P0 | Anvien graph relationships | relationships | N/A | 19451 | 19451 | inventory recorded | N/A | E0-P0A-ANVIEN |

## B1 - P1 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P1 | materialized context | LOCAL_SERIALIZATION_PROXY bytes | fixture-dependent | 243 targeted policy | 243 targeted policy | smallest sufficient | strategy comparison | E2-P2-COMPARISON |
| P1 | available source refs | refs | fixture-dependent | 7 targeted-policy steps | 7 | deterministic | bounded | E2-P2-COMPARISON |
| P1 | retrieval steps | steps | fixture-dependent | 7 targeted policy | 7 | bounded | strategy comparison | E2-P2-COMPARISON |

## B2 - P2 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P2 | CR cases | cases | 20 | 20 | 20 | 20 | 0 | E2-P2-CR1-CR20 |
| P2 | required coverage ratio | ratio | fixture-dependent | 1.0 on sufficient cases | 1.0 | 1.0 when sufficient | pass/fail | E2-P2-CR1-CR20 |
| P2 | duplicate materialized bytes | LOCAL_SERIALIZATION_PROXY bytes | fixture-dependent | 0 in reuse-valid case | 0 | bounded reuse | invalidation tested | E1-P1-REUSE |

## B3 - P3 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P3 | candidate artifact | SHA-256 | C18 `.21` historical | `4c8e80f658b233c36c4cab0f660ec72149b763ba6fcaf03bb7185f3c32ec2220` | same | new immutable candidate if source changed | new unpromoted artifact | E3-P3-CANDIDATE-HASH |
| P3 | candidate artifact size | bytes | C18 historical | 2532915 | 2532915 | recorded | N/A | E3-P3-PACKAGE |

## Non-Benchmarkable Notes

- Acceptance, security, contradiction, permission, and regression are pass/fail evidence, not benchmark metrics.
- No token, cost, provider, web, or live-host measurement is authorized by C19.
