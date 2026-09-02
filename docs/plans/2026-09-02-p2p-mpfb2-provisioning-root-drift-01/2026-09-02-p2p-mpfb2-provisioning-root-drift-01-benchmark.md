# P2P-MPFB2 provisioning root drift ISSUE 56 Benchmark Ledger

## Metadata

- Date: `2026-09-02`
- Plan: `docs/plans/2026-09-02-p2p-mpfb2-provisioning-root-drift-01/2026-09-02-p2p-mpfb2-provisioning-root-drift-01-plan.md`
- Evidence: `docs/plans/2026-09-02-p2p-mpfb2-provisioning-root-drift-01/2026-09-02-p2p-mpfb2-provisioning-root-drift-01-evidence.md`
- Benchmark: `docs/plans/2026-09-02-p2p-mpfb2-provisioning-root-drift-01/2026-09-02-p2p-mpfb2-provisioning-root-drift-01-benchmark.md`
- Actual status: `docs/plans/2026-09-02-p2p-mpfb2-provisioning-root-drift-01/2026-09-02-p2p-mpfb2-provisioning-root-drift-01-actual-status.md`

## Benchmark Rules

Record measured numbers only. For this bounded issue, measurements include canonical SHA/tree, root hashes, delta path count, pinned source/asset byte counts, focused test counts, and one runtime execution count. Do not turn pass/fail narrative into a benchmark.

## B0 - P0 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P0 | User-reported root hash | sha256 | `10ebf09a8b425f6e1081f9624ccf9365e471522b01527820e89d27b20de705bf` | pending | pending | exact manifest hash | pending | `E0-P0A-USER1` |

## B1 - P1 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P1 | Canonical main commit | git SHA | user-declared | `e7c040d87dacf7b5cfee1e57536edc0b27f5768b` | `e7c040d87dacf7b5cfee1e57536edc0b27f5768b` | exact | 0 | `E0-P0A-REMOTE1` |
| P1 | Canonical main tree | git tree SHA | user-declared | `9649785f0104259bac05b244a2162e2a7321657f` | `9649785f0104259bac05b244a2162e2a7321657f` | exact | 0 | `E0-P0A-REMOTE1` |
| P1 | Root-delta paths | paths | 0 reported | 526 | 526 | exact complete inventory | +526 generated paths | `E1-P1B-DELTA1` |
| P1 | Pinned source/asset bytes changed | bytes | unknown | 0 | 0 | 0 | 0 | `E1-P1B-PIN1` |

## B2 - P2 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P2 | Root hash after reconciliation | sha256 | observed drift | `f6907ef03674ddc995e8b0fdd988e9a003cad61df0d4f707e2a7aaeda4d4e788` | pending | `f6907ef03674ddc995e8b0fdd988e9a003cad61df0d4f707e2a7aaeda4d4e788` | reconciled in candidate | `E2-P2A-ROOT1` |
| P2 | Focused tests | cases | 0 | 22 | 22 | all required cases | +22 total | `E2-P2B-TEST2` |

## B3 - P3 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P3 | Real canonical continuations | runs | 0 | pending | pending | exactly 1 | pending | pending |

## Non-Benchmarkable Notes

Runtime gate pass/fail, first downstream blocker, provenance validity, firewall cleanup, and Game Truyen mutation status belong in the evidence ledger and final report; record only their measured counts/hashes here when applicable.
