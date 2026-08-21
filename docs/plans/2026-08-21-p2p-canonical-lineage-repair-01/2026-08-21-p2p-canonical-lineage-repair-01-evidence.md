# P2P Canonical Lineage Repair 01 Evidence Ledger

## Metadata

- Date: `2026-08-21`
- Plan: `docs/plans/2026-08-21-p2p-canonical-lineage-repair-01/2026-08-21-p2p-canonical-lineage-repair-01-plan.md`
- Evidence: `docs/plans/2026-08-21-p2p-canonical-lineage-repair-01/2026-08-21-p2p-canonical-lineage-repair-01-evidence.md`
- Benchmark: `docs/plans/2026-08-21-p2p-canonical-lineage-repair-01/2026-08-21-p2p-canonical-lineage-repair-01-benchmark.md`
- Actual status: `docs/plans/2026-08-21-p2p-canonical-lineage-repair-01/2026-08-21-p2p-canonical-lineage-repair-01-actual-status.md`

## Evidence Rules

- Evidence is fresh, command-backed, and scoped to the new reconciliation worktree.
- Historical reports and remote refs are evidence pointers, not authority.
- Evidence IDs are stable and phase-scoped; exact IDs are referenced from actual-status and benchmark ledgers.
- A green test does not override source, authority, provenance, or runtime-boundary evidence.
- Unavailable live Manus evidence remains `NOT_RUN`/`BLOCKED`, never synthetic.

## E0 - P0 Evidence

Matching plan item(s): `P0-A`

- `E0-P0A-GIT1`: Fresh worktree `.tmp/p2p-canonical-lineage-repair-01` was created on branch `codex/p2p-canonical-lineage-repair-01` from `origin/main`; status was clean; commit `bda3e228e67d1ca117e6b3105e920445830b4a0d`; tree `21b558f58a0a05f652ee378c4b83bae1c3584727`.
- `E0-P0A-GIT2`: `origin/main` governance mechanically states official `8.4.7-C-codex.19`, artifact SHA `3a9ee51321e1f5e40e35ce73eb90727cddb571a672aa095d16d76af2feb03dd8`, promotion status `PROMOTED_VERIFIED`; this is the preserved baseline.
- `E0-P0A-MATRIX1`: Fetched refs include `origin/p2p-promote-41-01`, `origin/p2p-full-successor-46`, corrective `01a/01b/01c/01d`, and other capability/framework/context branches; all relevant refs share `origin/main` as merge base.
- `E0-P0A-MATRIX2`: Verified implementation lineage is available through `bbb5cbbcda084672f33a215fd7c80d580e4bde62`; it descends from the `.46` implementation lineage and includes corrective Project Context/Map-before-work and clean-source test-script work. `.46`/`.47`/`.48`/`.71` authority claims are not adopted.
- `E0-P0A-MATRIX3`: Material source commits identified: `2eaceeb` execution-target foundation; `edd7dd7` provider-neutral role runtime; `e972923` FW01; `07d9400` FW02; `93963d3` FW03; `314ab83`/`4ade61e` FW04; `5f10c02` FW05/Decision Trace; `21df4a3` FW06; `64d4387` Context Intelligence; `6a6d482` adaptive selection; `e555839` Project Context/Map and lifecycle machinery; `9888909` corrective identity implementation; `bbb5cbb` final clean-source reconciliation tests.
- `E0-P0A-HIST1`: Historical defects preserved for reconciliation: `.46` promotion record references missing `reports/P2P-PROMOTE-46-01-REPORT.md`; `.46` package/VERSION identity was stale `.41`; `.47` package manifest remained `.41`; `.48` and `.71` records are incomplete; fixture official pointers are non-authoritative.
- `E0-P0A-ANV1`: Anvien graph refreshed successfully: 424 files scanned, 51 code files parsed, 0 parse failures, 17,357 nodes, 20,161 relationships. Baseline file-detail related-file counts: `scripts/p2p_development_control.py` 2/high, `scripts/package_release.py` 2/high, `scripts/doctor.py` 2/high, `scripts/p2p_governance.py` 2/high, `governance/development-control.json` 2/low, `manifest/package.json` 1/low.
- `E0-P0A-SCOPE1`: Dirty owner checkout was not reused or reset. All implementation work is isolated to the new worktree; authoritative Game Truyện, Gia Phả, and Logistics paths are outside scope and untouched.

## E1 - P1 Evidence

Matching plan item(s): `P1-A`, `P1-B`

- `E1-P1A-SRC1`: coherent verified implementation lineage through `bbb5cbbcda084672f33a215fd7c80d580e4bde62` was merged into the fresh reconciliation worktree; the recovery matrix records source commits and adoption decisions for material runtime families.
- `E1-P1A-IMPACT1`: refreshed Anvien graph after recovery: 845 files scanned, 159 code files parsed, 0 parse failures, 36,334 nodes, 42,023 relationships; high-risk hotspots remain scope warnings.
- `E1-P1A-TEST1`: provider-neutral/core scoped suite `145 tests, 5 skipped, OK`; bounded runtime suite `94 tests, OK`; map gate/freshness pilots passed fresh/stale/missing/permission cases; dynamic planner tests passed.
- `E1-P1A-SCOPE1`: packaging contract excludes development/transient/reconciliation paths and installed foundation runtime excludes test fixtures; no authoritative project paths were touched.
- `E1-P1A-TEST2`: JSON/control validation passed; active control retains official `.19`; Python compile/import checks passed; full capability discovery passed `335 tests, 6 skipped, OK`.
- `E1-P1B-AUTH1`: active authority separates official baseline `.19`, unpromoted source lineage `.72`, candidate distribution metadata, artifact identity, source binding, inventory/checksum records, and capability registry; no promotion performed.
- `E1-P1B-MATRIX1`: machine-readable recovery matrix and append-only historical reconciliation record created under `reports/reconciliation/`.
- `E1-P1B-PKG1`: package builder refuses dirty source and captures full source commit/tree before stage-only metadata generation; candidate mint was not entered because P2-A blocked before mint.
- `E1-P1B-PKG2`: distribution include/exclude rules and inventory/checksum metadata contract are explicit; no candidate ZIP was created.

## E2 - P2 Evidence

Matching plan item(s): `P2-A`, `P2-B`

- `E2-P2A-INSTALL1`: NOT RUN; no candidate exists because the mandatory Manus sentinel gate blocked before mint.
- `E2-P2A-DOCTOR1`: NOT RUN for the same candidate-dependent reason; no HEALTHY/WARN equivalence is claimed.
- `E2-P2A-MAP1`: source runtime pilot VERIFIED: fresh map allowed; stale, missing, and permission-denied mutation paths blocked; installed-candidate proof was not run.
- `E2-P2A-MANUS1`: BLOCKED; `_manus_key()` returned `NO_CREDENTIALS`; no API call, credential request, synthetic result, or backend task was created.
- `E2-P2A-NEG1`: existing provider-neutral, bounded, role, map, and fail-closed negative suites passed; candidate-specific package checks were not entered before the mint blocker.
- `E2-P2A-REG1`: full capability suite `335 tests, 6 skipped, OK`; core provider-neutral suite `145 tests, 5 skipped, OK`; bounded suite `94 tests, OK`.
- `E2-P2B-MINT1`: NOT RUN; exactly zero successor artifacts minted.
- `E2-P2B-INVENTORY1`: NOT RUN; no candidate ZIP exists to verify.
- `E2-P2B-DELIVERY1`: pending final source commit/change detection before branch delivery.
- `E2-P2B-DELIVERY2`: pending branch push; no promotion or main merge is authorized.

## Closure Evidence

Final closure remains blocked at the pre-mint Manus gate. The exact blocker
report is `reports/reconciliation/p2p-canonical-lineage-repair-01-blocker.json`.
