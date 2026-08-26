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
| P0 | Anvien files scanned | files | 936 | 936 | pending | 936+ | pending | `E0-P0A-GRAPH1` |
| P0 | Anvien parsed code / failures | files / failures | 168 / 0 | 168 / 0 | pending | 168 / 0 | pending | `E0-P0A-GRAPH1` |
| P0 | Runtime lock protected files | files | 1,172 | 1,178 current manifest | pending | exact current manifest | pending | `E0-P0A-DRIFT2` |
| P0 | Runtime virtual hashes | entries equal | equal | equal | pending | equal | pending | `E0-P0A-DRIFT2` |
| P0 | Drift delta | added / changed | 6 / 11 | 6 / 11 | pending | 0 / 0 after justified lock regeneration | pending | `E0-P0A-DRIFT2` |
| P0 | Scoped volatile policy entries | entries | 38 | 38 | pending | 38 unless evidence requires a bounded change | pending | `E0-P0A-TEST1` |

## B1 - P1 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|---|---|---:|---:|---:|---:|---:|---:|---|
| P1 | Authority commit | SHA-1 | `2a71410…` | pending | pending | exact supplied commit | pending | `E1-P1A-AUTH1` |
| P1 | Authority tree | SHA-1 | `3e6ab12…` | pending | pending | exact supplied tree | pending | `E1-P1A-AUTH1` |
| P1 | Lock protected files | files | 1,172 | pending | pending | exact current manifest | pending | `E1-P1B-LOCK1` |
| P1 | Unexplained protected drift | findings | 14 previewed / 17 total delta | pending | pending | 0 | pending | `E1-P1B-DRIFT1..E1-P1B-DRIFT17` |

## B2 - P2 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|---|---|---:|---:|---:|---:|---:|---:|---|
| P2 | Canonical Council current-proof status | boolean/status | ambiguous beside historical wording | pending | pending | `FALSE` / `NOT_PROVEN` | pending | `E2-P2A-COUNCIL1..8` |
| P2 | Edge-case families indexed | families | 0 dedicated canonical index | pending | pending | 8 required families | pending | `E2-P2B-EDGE1` |
| P2 | Live evidence slots with fresh proof | slots | 0 in new index | pending | pending | 0 claimed; all unknown until receipts | pending | `E2-P2B-EDGE4` |

## B3 - P3 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|---|---|---:|---:|---:|---:|---:|---:|---|
| P3 | Doctor helper reader-thread decode errors | occurrences | 1 reproduced | pending | pending | 0 | pending | `E3-P3A-DECODER7` |
| P3 | Malformed helper output accepted | cases | not covered | pending | pending | 0 | pending | `E3-P3B-TEST1..5` |
| P3 | Drift-policy scoped findings assertion | entries/references | 10 / 35 expected by stale test | 38 / 35 current measured | pending | current policy/reference truth | pending | `E3-P3B-TEST1` |

## B4 - P4 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|---|---|---:|---:|---:|---:|---:|---:|---|
| P4 | Vendor gate | cases | 22/22 historical receipt | pending | pending | 22/22 | pending | `E4-P4A-GATE1` |
| P4 | Host Projection gate | cases | 30/30 historical receipt | pending | pending | 30/30 | pending | `E4-P4A-GATE2` |
| P4 | Manus package gate | cases | 8/8 historical receipt | pending | pending | 8/8 | pending | `E4-P4A-GATE3` |
| P4 | Foundation gate | cases | 28/28 historical receipt | pending | pending | 28/28 | pending | `E4-P4A-GATE4` |
| P4 | C35 gate | cases | 57/57 historical receipt | pending | pending | 57/57 | pending | `E4-P4A-GATE5` |
| P4 | C43 gate | cases | 9/9 historical receipt | pending | pending | 9/9 | pending | `E4-P4A-GATE6` |
| P4 | Capability denominator/quorum | denominator / quorum | 8 / 8 | pending | pending | 8 / 8 configured; no live proof claim | pending | `E4-P4A-GATE7` |
| P4 | compileall | exit code | 0 historical receipt | pending | pending | 0 | pending | `E4-P4A-GATE8` |
| P4 | Final candidate tree | SHA-1 | `3e6ab12…` before changes | pending | pending | exact final tree recorded | pending | `E4-P4A-CLOSE3` |

## Non-Benchmarkable Notes

- UI layout, browser round trips, database writes, Docker image/container size, and external provider latency are not applicable to this governance/CLI reconciliation.
- A configured denominator/quorum is an inventory count, not a live Council benchmark.
- Historical counts are baseline references only; final rows must use fresh commands from the exact final candidate.
