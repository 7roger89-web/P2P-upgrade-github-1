# P2P-C14 Design Intelligence Release Readiness & Portable Project Integration Benchmark Ledger

## Metadata

- Date: `2026-08-15`
- Plan: `docs/plans/2026-08-15-p2p-c14-design-intelligence-release-readiness/2026-08-15-p2p-c14-design-intelligence-release-readiness-plan.md`
- Evidence: `docs/plans/2026-08-15-p2p-c14-design-intelligence-release-readiness/2026-08-15-p2p-c14-design-intelligence-release-readiness-evidence.md`
- Benchmark: `docs/plans/2026-08-15-p2p-c14-design-intelligence-release-readiness/2026-08-15-p2p-c14-design-intelligence-release-readiness-benchmark.md`
- Actual status: `docs/plans/2026-08-15-p2p-c14-design-intelligence-release-readiness/2026-08-15-p2p-c14-design-intelligence-release-readiness-actual-status.md`

## Benchmark Rules

This ledger records measured counts, sizes, hashes, and observed lifecycle/runtime
values only. It does not turn package tests into universal UI quality, accessibility
certification, real-project quality, or eight-thread QUORUM proof. Build/test time is
not a product-performance benchmark unless the scope explicitly measures it.

## B0 - P0 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P0 | Root graph files scanned | count | 350 (C13) | 355 | 355 | inventory | +5 | `E1-P1A-SRC1..8` |
| P0 | Root graph nodes | count | 13,639 (C13) | 13,717 | 13,717 | inventory | +78 | `E1-P1A-SRC1..8` |
| P0 | Root graph relationships | count | 15,490 (C13) | 15,570 | 15,570 | inventory | +80 | `E1-P1A-SRC1..8` |
| P0 | C13 registry faculties | count | 174 | 174 | 174 | 174 | 0 | `E3-P3A-INSTALL1..RENDER1` |
| P0 | Default faculty bodies loaded | count | 0 | 0 | 0 | 0 | 0 | `E4-P4A-FIXTURE1..BOUNDARY3` |
| P0 | Canonical identities | count | 8 | 8 | 8 | 8 | 0 | `E4-P4B-TEST1..GOV1` |
| P0 | Quorum denominator | count | 8 | 8 | 8 | 8 | 0 | `E4-P4B-TEST1..GOV1` |

## B1 - P1 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P1 | Full-root secret findings | count | incomplete | 1 known-safe fixture | 1 known-safe fixture; package 0 | no unclassified findings | classified | `E1-P1A-SEC1` |
| P1 | Helper attempts | count | 1 prior C13 | 1 bounded C14 retry | 1 bounded C14 retry | <=1 retry | within bound | `E1-P1A-HELPER1` |
| P1 | Helper elapsed | seconds | 184 prior C13 | 180 bound | 180 bound; control-plane timeout | bounded | classified | `E1-P1A-HELPER1` |
| P1 | C10/C11/C12 parallel stores/runners | count | 0 | 0 | 0 | 0 | 0 | `E1-P1A-SRC1..8` |

## B2 - P2 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P2 | Candidate package files | count | 405 (C13 candidate) | 406 | 406 | record actual | +1 | `E2-P2B-PACK1..PACK4` |
| P2 | Candidate checksums | count | 406 (C13 candidate) | 407 | 407 | record actual | +1 | `E2-P2B-PACK1..PACK4` |
| P2 | Candidate size | bytes | 2,464,587 (C13 candidate) | 2,432,518 | 2,432,518 | record actual | -32,069 | `E2-P2B-PACK1..PACK4` |
| P2 | Candidate artifact SHA-256 | hash | C13 hash preserved | `3a9ee51321e1f5e40e35ce73eb90727cddb571a672aa095d16d76af2feb03dd8` | same | 64 hex chars | bound | `E2-P2B-PACK1..PACK4` |
| P2 | Version-bearing source markers | count | mixed/stale release marker | all checked markers | all `.19` | all candidate markers agree | PASS | `E2-P2A-VERSION1..COPY3` |

## B3 - P3 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P3 | Fresh install result | status | not run for C14 | PASS | PASS | PASS | 0 | `E3-P3A-INSTALL1` |
| P3 | `.15` upgrade result | status | not run for C14 | PASS | PASS | PASS | 0 | `E3-P3B-UPGRADE1` |
| P3 | Same-version reinstall result | status | not run for C14 | PASS | PASS | PASS | 0 | `E3-P3B-REINSTALL1` |
| P3 | Duplicate router/capability/store surfaces | count | 0 expected | 0 | 0 | 0 | 0 | `E3-P3B-REINSTALL2` |

## B4 - P4 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P4 | Non-UI faculty bodies loaded | count | 0 | 0 | 0 | 0 | 0 | `E4-P4A-ROUTE1..DORMANT2` |
| P4 | Beginner UI activated faculties | count | C13 synthetic known | 0 body loads; questions 0 | 0 body loads; questions 0 | bounded <174 | PASS | `E4-P4A-ROUTE1..DORMANT2` |
| P4 | Logistics-like activated faculties | count | 44 (C13 synthetic) | 44 | 44 | bounded and professional breadth | 0 | `E4-P4A-FIXTURE1` |
| P4 | Consumer activated faculties | count | 37 (C13 synthetic) | 37 | 37 | bounded and different | 0 | `E4-P4A-FIXTURE1` |
| P4 | Focused C13 tests | count | 15/15 | 44/44 | 44/44 | all pass | PASS | `E1-P1B-FIX1`, `E4-P4B-TEST1` |
| P4 | Full suite tests | count | 174/174 C13 | 175/175 | 175/175 | all applicable pass | PASS | `E4-P4B-TEST1` |
| P4 | Supervisor verdict | status | C13 development PASS | PASS | PASS | PASS or exact blocker | PASS | `E4-P4B-SUP1` |

## Non-Benchmarkable Notes

- Browser/Docker rendering is not a C14 benchmark; only the packaged render capability
  state contract is verified.
- No measurement in this plan proves beauty, universal UI quality, accessibility
  certification, or real Logistics redesign quality.
- No full eight-agent QUORUM metric is recorded because C14 does not authorize or require
  delegation and the host identity boundary remains preserved.

## Final Measured Release Gate

- Candidate version: `8.4.7-C-codex.19`.
- Candidate SHA-256: `3a9ee51321e1f5e40e35ce73eb90727cddb571a672aa095d16d76af2feb03dd8`.
- Technical report SHA-256: `a85e83faffcb1f10efd5a772019c877ff8c8e85e3aae5a38e73a5e933671cf46`.
- Official `.15` rollback SHA-256: `af4d63a882dabfde20ac237574590ec584ee2944bc4cdc30b6a07bf7f681e195`.
- Technical gate: `PASS`; project eval: `5` cases, `1.0` P2P pass rate, `0` regressions;
  RAG: `NOT_APPLICABLE`; approval request: `PENDING`.
