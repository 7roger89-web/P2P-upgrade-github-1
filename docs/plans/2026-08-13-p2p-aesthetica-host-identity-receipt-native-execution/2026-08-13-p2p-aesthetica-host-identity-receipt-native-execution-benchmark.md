# P2P Aesthetica — Host Identity Receipt and Native Execution Completion Benchmark Ledger

## Metadata

- Date: `2026-08-13`
- Plan: `docs/plans/2026-08-13-p2p-aesthetica-host-identity-receipt-native-execution/2026-08-13-p2p-aesthetica-host-identity-receipt-native-execution-plan.md`
- Evidence: `docs/plans/2026-08-13-p2p-aesthetica-host-identity-receipt-native-execution/2026-08-13-p2p-aesthetica-host-identity-receipt-native-execution-evidence.md`
- Benchmark: `docs/plans/2026-08-13-p2p-aesthetica-host-identity-receipt-native-execution/2026-08-13-p2p-aesthetica-host-identity-receipt-native-execution-benchmark.md`
- Actual status: `docs/plans/2026-08-13-p2p-aesthetica-host-identity-receipt-native-execution/2026-08-13-p2p-aesthetica-host-identity-receipt-native-execution-actual-status.md`

## Benchmark Rules

- Record measured counts, sizes, hashes, and timings only; pass/fail narrative
  belongs in the evidence ledger.
- Baselines are pre-implementation measurements from this checkout. “Final”
  remains `pending` until the slice is complete.
- Host identity is binary evidence, not a performance average. The measured
  host proof count must be one exact official receipt or zero.

## B0 - P0 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P0 | Installed Codex version | version | 0.147.0 | 0.147.0 | 0.147.0 | 0.147.0 | 0 | `E0-P0A-HOST1` |
| P0 | Anvien indexed files | files | 221 | 227 | 227 | current graph | +6 | `E5-CLOSE-DETECT1` |
| P0 | Anvien graph nodes | nodes | 9,123 | 9,321 | 9,321 | no unexplained failure | +198 | `E5-CLOSE-DETECT1` |
| P0 | Anvien graph relationships | relationships | 10,424 | 10,663 | 10,663 | no unexplained failure | +239 | `E5-CLOSE-DETECT1` |
| P0 | Canonical denominator | identities | 8 | 8 | 8 | 8 | 0 | `E0-P0A-QUORUM1` |
| P0 | Full quorum | ratio | 8/8 | 8/8 | 8/8 | 8/8 | 0 | `E0-P0A-QUORUM1` |
| P0 | Existing execution ledger lines | lines | 0 | 0 | 0 | no synthetic lines | 0 | `E2-P2A-HOST2` |
| P0 | Prior `.9` artifact content | files | 397 | 397 | 397 | preserve baseline | 0 | `E4-P4-PKG1` |

## B1 - P1 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P1 | Hook receipt schema | schemas | 0 | 1 | 1 | 1 | +1 | `E1-P1A-SRC1` |
| P1 | Synthetic parser cases | cases | 0 | 8/8 | 8/8 | 6/6 minimum | +8 | `E1-P1A-TEST1` |
| P1 | Sensitive fields persisted | fields | 0 | 0 | 0 | 0 | 0 | `E1-P1B-TEST2` |
| P1 | Duplicate receipt lines from one replay | lines | 0 | 1 | 1 | 1 | +1 | `E1-P1B-TEST3` |
| P1 | External dependencies imported by hook | packages | 0 | 0 | 0 | 0 | 0 | `E1-P1A-SRC1` |

## B2 - P2 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P2 | Official native Aesthetica identity receipts | receipts | 0 | 0 | 0 | 1 | 0 | `E2-P2B-REAL3` |
| P2 | Exact child IDs verified | IDs | 0 | 0 | 0 | 1 | 0 | `E2-P2A-HOST3` |
| P2 | Synthetic receipts counted as host proof | receipts | 0 | 0 | 0 | 0 | 0 | `E2-P2B-REAL4` |
| P2 | Host hook external network calls | calls | 0 | 0 | 0 | 0 | 0 | `E1-P1B-TEST2` |

## B3 - P3 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P3 | Routers after change | routers | 1 | 1 | 1 | 1 | 0 | `E3-P3B-SEC1` |
| P3 | Canonical quorum denominator | identities | 8 | 8 | 8 | 8 | 0 | `E3-P3C-TEST5` |
| P3 | Optional Aesthetica denominator contribution | identities | 0 | 0 | 0 | 0 | 0 | `E3-P3C-TEST5` |
| P3 | Truth-table request classes | cases | 0 | not_run | not_run | 4 | not_run | `E3-P3C-TEST1..E3-P3C-TEST4` |

## B4 - P4 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P4 | Package candidate content files | files | 397 | 398 | 398 | manifest-consistent | +1 | `E4-P4-PKG1` |
| P4 | Package candidate checksum entries | entries | 398 | 399 | 399 | manifest + 1 | +1 | `E4-P4-PKG1` |
| P4 | Changed protected runtime/config/instruction files | files | 0 | 8 | 8 | exact scoped list | +8 | `E4-P4-REG1` |
| P4 | UIUX DW1-DW18 candidate gates | gates | 0 | 18/18 | 18/18 | 18/18 | +18 | `E4-P4-DW1` |

## Non-Benchmarkable Notes

- Official source/documentation provenance, trust decisions, routing semantics,
  and final classification are qualitative acceptance evidence; see the
  evidence ledger.
- Docker/browser metrics are not applicable to this local hook/CLI contract.
- Git commit count is not measurable because this checkout has no `.git`
  directory; the limitation is recorded in `E0-P0A-GIT1` and closure evidence.
