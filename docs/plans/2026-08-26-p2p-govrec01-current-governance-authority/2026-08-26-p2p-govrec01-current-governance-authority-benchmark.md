# P2P-GOVREC01 Current Governance Authority Reconciliation Benchmark Ledger

## Metadata

- Date: `2026-08-26`
- Plan: `docs/plans/2026-08-26-p2p-govrec01-current-governance-authority/2026-08-26-p2p-govrec01-current-governance-authority-plan.md`
- Evidence: `docs/plans/2026-08-26-p2p-govrec01-current-governance-authority/2026-08-26-p2p-govrec01-current-governance-authority-evidence.md`
- Benchmark: `docs/plans/2026-08-26-p2p-govrec01-current-governance-authority/2026-08-26-p2p-govrec01-current-governance-authority-benchmark.md`
- Actual status: `docs/plans/2026-08-26-p2p-govrec01-current-governance-authority/2026-08-26-p2p-govrec01-current-governance-authority-actual-status.md`

## Benchmark Rules

This file records measured counts, sizes, hashes, inventories, and timings only. Pass/fail narrative belongs in the evidence ledger. No benchmark is interpreted as live Council or provider behavior.

## B0 - P0 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|---|---|---:|---:|---:|---:|---:|---:|---|
| P0 | Anvien files scanned | files | 936 | 945 | 945 | 936+ | +9 | `E0-P0A-GRAPH1`, `E3-P3B-TEST8`, `E4-P4A-CLOSE6` |
| P0 | Anvien parsed code / failures | files / failures | 168 / 0 | 169 / 0 | 169 / 0 | 168 / 0 | +1 / 0 | `E0-P0A-GRAPH1`, `E3-P3B-TEST8` |
| P0 | Runtime lock protected files | files | 1,172 | 1,178 | 1,178 | exact current manifest | +6 | `E1-P1B-LOCK1`, `E4-P4A-GATE2` |
| P0 | Runtime virtual hashes | entries equal | equal | equal | equal | equal | unchanged | `E1-P1B-LOCK2`, `E4-P4A-GATE2` |
| P0 | Drift delta | added / changed | 6 / 11 | 0 / 0 after lock | 0 / 0 | 0 / 0 after justified lock regeneration | closed | `E1-P1B-LOCK2`, `E4-P4A-GATE2` |
| P0 | Scoped volatile policy entries | entries | 38 | 38 | 38 | 38 unless evidence requires a bounded change | unchanged | `E3-P3B-TEST2` |

## B1 - P1 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|---|---|---:|---:|---:|---:|---:|---:|---|
| P1 | Authority commit | SHA-1 | `2a71410…` | `2a71410afd1b29651016ef57a5d2da38938c3f68` | same | exact supplied commit | bound | `E1-P1A-AUTH1` |
| P1 | Authority tree | SHA-1 | `3e6ab12…` | `3e6ab12ff78a72c4a3ea2a418e11167a8649aaad` | same | exact supplied tree | bound | `E1-P1A-AUTH1` |
| P1 | Lock protected files | files | 1,172 | 1,178 | 1,178 | exact current manifest | +6 | `E1-P1B-LOCK1`, `E4-P4A-GATE2` |
| P1 | Unexplained protected drift | findings | 14 previewed / 17 total delta | 0 | 0 | 0 | closed | `E1-P1B-DRIFT1..E1-P1B-DRIFT17`, `E4-P4A-GATE2` |

## B2 - P2 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|---|---|---:|---:|---:|---:|---:|---:|---|
| P2 | Canonical Council current-proof status | boolean/status | ambiguous beside historical wording | `FALSE` / `NOT_PROVEN` | same | `FALSE` / `NOT_PROVEN` | resolved | `E2-P2A-COUNCIL1..8` |
| P2 | Edge-case families indexed | families | 0 dedicated canonical index | 8 | 8 | 8 required families | +8 | `E2-P2B-EDGE1..3` |
| P2 | Live evidence slots with fresh proof | slots | 0 in new index | 0 | 0 | 0 claimed; all unknown until receipts | unchanged by design | `E2-P2B-EDGE4..5` |

## B3 - P3 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|---|---|---:|---:|---:|---:|---:|---:|---|
| P3 | Doctor helper reader-thread decode errors | occurrences | 1 reproduced | 0 | 0 | 0 | -1 | `E3-P3A-DECODER2`, `E4-P4A-GATE9` |
| P3 | Malformed helper output accepted | cases | not covered | 0 | 0 | 0 | closed | `E3-P3A-DECODER4..5` |
| P3 | Drift-policy scoped findings assertion | entries/references | 10 / 35 expected by stale test | 38 / 366 current measured | 38 / 366 | current policy/reference truth | updated | `E3-P3B-TEST2` |

## B4 - P4 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|---|---|---:|---:|---:|---:|---:|---:|---|
| P4 | Vendor gate | cases | 22/22 historical receipt | 22/22 | 22/22 | 22/22 | pass | `E4-P4A-GATE1` |
| P4 | Host Projection gate | cases | 30/30 historical receipt | 30/30 | 30/30 | 30/30 | pass | `E4-P4A-GATE2` |
| P4 | Manus package gate | cases | 8/8 historical receipt | 8/8 | 8/8 | 8/8 | pass | `E4-P4A-GATE3` |
| P4 | Foundation gate | cases | 28/28 historical receipt | 28/28 | 28/28 | 28/28 | pass | `E4-P4A-GATE4` |
| P4 | C35 gate | cases | 57/57 historical receipt | 57/57 | 57/57 | 57/57 | pass | `E4-P4A-GATE5` |
| P4 | C43 gate | cases | 9/9 historical receipt | 9/9 | 9/9 | 9/9 | pass | `E4-P4A-GATE6` |
| P4 | Capability denominator/quorum | denominator / quorum | 8 / 8 | 8 / 8 | 8 / 8 | 8 / 8 configured; no live proof claim | unchanged | `E4-P4A-GATE7` |
| P4 | compileall | exit code | 0 historical receipt | 0 | 0 | 0 | pass | `E4-P4A-GATE8` |
| P4 | Final candidate tree | SHA-1 | `3e6ab12…` before changes | `3ad8ad2f8d0e7351c5cbd60ee3c7a15fed982dd7` | `3ad8ad2f8d0e7351c5cbd60ee3c7a15fed982dd7` | exact pre-Supervisor candidate tree recorded | bound | `E4-P4A-CLOSE3`, `E4-P4A-CLOSE7` |

## Non-Benchmarkable Notes

- UI layout, browser round trips, database writes, Docker image/container size, and external provider latency are not applicable to this governance/CLI reconciliation.
- A configured denominator/quorum is an inventory count, not a live Council benchmark.
- Historical counts are baseline references only; final rows must use fresh commands from the exact final candidate.
