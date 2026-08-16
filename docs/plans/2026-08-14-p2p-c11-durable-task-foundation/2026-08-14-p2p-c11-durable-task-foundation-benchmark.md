# P2P-C11 Durable Task State and Minimal Dependency Graph Foundation Benchmark Ledger

## Metadata

- Date: `2026-08-14`
- Plan: `docs/plans/2026-08-14-p2p-c11-durable-task-foundation/2026-08-14-p2p-c11-durable-task-foundation-plan.md`
- Evidence: `docs/plans/2026-08-14-p2p-c11-durable-task-foundation/2026-08-14-p2p-c11-durable-task-foundation-evidence.md`
- Benchmark: `docs/plans/2026-08-14-p2p-c11-durable-task-foundation/2026-08-14-p2p-c11-durable-task-foundation-benchmark.md`
- Actual status: `docs/plans/2026-08-14-p2p-c11-durable-task-foundation/2026-08-14-p2p-c11-durable-task-foundation-actual-status.md`

## Benchmark Rules

- Record measured counts, hashes, and timings only; pass/fail narrative belongs in the evidence ledger.
- Use the same isolated fixture/evidence hashes for paired task-state trials.
- Do not treat unit-test timing as product/runtime performance; it is validation evidence unless explicitly recorded as a test metric.
- Do not measure or claim background execution, agent throughput, provider cost, or host identity.
- Preserve prior artifact hashes; any new candidate hash is separate from the embedded package version.

## B0 - P0 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P0 | Root Anvien scanned files | files | `324` | `334` | `334` | record | `+10` | `E0-P0A-IMPACT1`, `E4-P4B-SUP1` |
| P0 | Root Anvien parsed code files | files | `31` | `33` | `33` | record | `+2` | `E0-P0A-IMPACT1`, `E4-P4B-SUP1` |
| P0 | Root Anvien graph nodes | nodes | `12015` | `12707` | `12707` | record | `+692` | `E0-P0A-IMPACT1`, `E4-P4B-SUP1` |
| P0 | Root Anvien graph relationships | relationships | `13659` | `14434` | `14434` | record | `+775` | `E0-P0A-IMPACT1`, `E4-P4B-SUP1` |
| P0 | Durable task modules present before C11 | files | `0` | `0` | `0` | `1` | `+0` | `E0-P0A-TASK1` |
| P0 | Existing canonical identities | identities | `8` | `8` | `8` | `8` | `0` | `E0-P0A-CANON1` |

## B1 - P1 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P1 | Task contract runtime files | files | `0` | `1` | `1` | `1` | `+1` | `E1-P1A-CONTRACT1` |
| P1 | New external dependencies | packages | `0` | `0` | `0` | `0` | `0` | `E1-P1A-CONTRACT1` |
| P1 | Canonical identities added by task foundation | identities | `0` | `0` | `0` | `0` | `0` | `E1-P1A-TEST1` |

## B2 - P2 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P2 | Task-state projection paths defined | paths | `0` | `1` | `1` | `1` | `+1` | `E2-P2A-STORE1` |
| P2 | Additional ledger files | files | `0` | `0` | `0` | `0` | `0` | `E2-P2A-LEDGER1` |
| P2 | Fresh reconstruction trials | trials | `0` | `2` | `2` | `2` | `+2` | `E2-P2B-RESUME1` |

## B3 - P3 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P3 | Focused task-state test cases | cases | `0` | `20` | `20` | `20` | `+20` | `E3-P3A-TEST1` |
| P3 | Beginner scenarios | cases | `0` | `10` | `10` | `10` | `+10` | `E3-P3B-BEGINNER1` |
| P3 | Full canonical quorum denominator | identities | `8` | `8` | `8` | `8` | `0` | `E3-P3B-PRESERVE1` |

## B4 - P4 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P4 | Official `.15` SHA-256 | hash | `af4d63a882dabfde20ac237574590ec584ee2944bc4cdc30b6a07bf7f681e195` | `af4d63a882dabfde20ac237574590ec584ee2944bc4cdc30b6a07bf7f681e195` | `af4d63a882dabfde20ac237574590ec584ee2944bc4cdc30b6a07bf7f681e195` | unchanged | `0` | `E4-P4A-HASH1` |
| P4 | Existing `.20` SHA-256 | hash | `0cc5d18cd01eb28a4ef914dca09d2530bef7c072d53e7dd194dd82fb4037a6f6` | `0cc5d18cd01eb28a4ef914dca09d2530bef7c072d53e7dd194dd82fb4037a6f6` | `0cc5d18cd01eb28a4ef914dca09d2530bef7c072d53e7dd194dd82fb4037a6f6` | unchanged | `0` | `E4-P4A-HASH1` |
| P4 | New C11 candidate SHA-256 | hash | `none` | `684018d1a563e35e32eed2e06bbfee3e9625d9caef95771bf04a848fa3868926` | `684018d1a563e35e32eed2e06bbfee3e9625d9caef95771bf04a848fa3868926` | new only if package gates PASS | `new` | `E4-P4A-HASH1` |
| P4 | Full unit suite validation time | seconds | `0` | `162.323` | `162.323` | record only | `+162.323` | `E4-P4A-TEST1` |
| P4 | Candidate package content files | files | `0` | `401` | `401` | package verify PASS | `+401` | `E4-P4A-PACK1` |
| P4 | Candidate package checksum entries | entries | `0` | `402` | `402` | package verify PASS | `+402` | `E4-P4A-PACK1` |

## Non-Benchmarkable Notes

- Logical owner, task/agent separation, fail-closed transitions, evidence binding, owner prompts, and C09 preservation are behavioral correctness claims, not performance benchmarks.
- Background execution, scheduler behavior, worker throughput, automatic recovery, and host identity are intentionally not measured because they are out of scope.
