# P2P-VDRIFT01 Canonical Vendor Snapshot Drift Repair Evidence Ledger

## Metadata

- Date: `2026-08-26`
- Plan: `docs/plans/2026-08-26-p2p-vdrift01-vendor-snapshot-repair/2026-08-26-p2p-vdrift01-vendor-snapshot-repair-plan.md`
- Evidence: `docs/plans/2026-08-26-p2p-vdrift01-vendor-snapshot-repair/2026-08-26-p2p-vdrift01-vendor-snapshot-repair-evidence.md`
- Benchmark: `docs/plans/2026-08-26-p2p-vdrift01-vendor-snapshot-repair/2026-08-26-p2p-vdrift01-vendor-snapshot-repair-benchmark.md`
- Actual status: `docs/plans/2026-08-26-p2p-vdrift01-vendor-snapshot-repair/2026-08-26-p2p-vdrift01-vendor-snapshot-repair-actual-status.md`

## Evidence Rules

- Evidence is current to this isolated checkout and exact candidate head.
- Test output is runtime evidence; source/history inspection establishes semantics.
- A passing test does not replace byte-level proof.
- SFI01 and Manus evidence is preserve-only context, not evidence that this candidate changed them.

## E0 - P0 Evidence

Matching plan item(s): `P0-A`

- `E0-P0A-FP1`: Fresh checkout fingerprint recorded before analysis: expected `HEAD=af02170ac7ba180900ca78beb26a2972d80c73b6`; exact tree/status/config/attributes to be recorded in the final forensic ledger.
- `E0-P0A-REPRO1`: `python -m unittest -q tests.test_p2p_vendor_skill_integration` reproduced the two reported snapshot failures: copywriter actual `146e5d...7183f8` vs expected `5a02c...52830d`; whiteboard actual `2d0b33...ad7d3` vs expected `55dbed...8742c`.
- `E0-P0A-HARNESS1`: The same suite also raised two independent errors: `test_11...` stops at snapshot mismatch and `test_16...` cannot create its temporary fixture because fresh clone lacks `.tmp`. This is tracked separately from the vendor mismatch.

## E1 - P1 Evidence

Matching plan item(s): `P1-A`, `P1-B`

- `E1-P1A-BYTES1`: pending per-file Git blob versus raw working-tree comparison.
- `E1-P1A-PATHS1`: pending path-set and ignored/untracked comparison.
- `E1-P1A-ATTR1`: pending `.gitattributes`, `core.autocrlf`, `core.eol`, mode, and symlink evidence.
- `E1-P1A-HISTORY1`: pending historical provenance comparison for the two promoted identities.
- `E1-P1B-IMPACT1`: pending Anvien file-detail and impact evidence if a production verifier edit is justified.
- `E1-P1B-TEST1`: pending falsification/regression test evidence.

## E2 - P2 Evidence

Matching plan item(s): `P2-A`, `P2-B`

- `E2-P2A-REGRESSION1`: pending full baseline validation matrix.
- `E2-P2A-CHANGES1`: pending Anvien detect-changes and diff summary.
- `E2-P2A-SUPERVISOR1`: pending fresh independent exact-head Supervisor result.

## Closure Evidence

Pending until the isolated candidate either reaches a justified repair plus fresh Supervisor PASS or records a terminal blocked/Owner-decision verdict.
