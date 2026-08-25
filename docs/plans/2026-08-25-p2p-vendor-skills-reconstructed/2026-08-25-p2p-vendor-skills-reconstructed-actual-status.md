# P2P Vendor Skills — Reconstruct Candidate on Valid Git Authority Actual Status

Title: P2P Vendor Skills — Reconstruct Candidate on Valid Git Authority
Date: 2026-08-25
Status: Owner approval recorded; exact checkpoint unpromoted
Companion plan: `docs/plans/2026-08-25-p2p-vendor-skills-reconstructed/2026-08-25-p2p-vendor-skills-reconstructed-plan.md`
Companion evidence: `docs/plans/2026-08-25-p2p-vendor-skills-reconstructed/2026-08-25-p2p-vendor-skills-reconstructed-evidence.md`
Companion benchmark: `docs/plans/2026-08-25-p2p-vendor-skills-reconstructed/2026-08-25-p2p-vendor-skills-reconstructed-benchmark.md`

## Purpose

This is the living current-state record before implementation and after each
slice. It classifies the broken snapshot, verified base, new candidate, and
validation surfaces without treating reports or profiles as authority.

## Freshness / Refresh Rules

- P0 is the fresh state captured before source reconstruction.
- Refresh affected rows after each implementation slice.
- Preserve the history of transitions; do not erase earlier blockers.
- `UNKNOWN` remains honest when Anvien cannot index hidden `.p2p` files or when
  a live identity/optional operation is not proven.

## Current Status Matrix

| Surface | Status | Evidence IDs | Touch mode | Next action / plan consequence |
|---|---|---|---|---|
| Broken root `.git` | `wrong` / `blocked` | `E0-P0A-AUTH1` | inspect-only | Never use as worktree; reconstruct from valid Git. |
| Valid remote and verified reference `557b502…` | `correct` for reconstruction base; not called promoted | `E0-P0A-AUTH2` | preserve-only | Use exact SHA/tree and record base reason. |
| New candidate worktree/branch | `correct` and clean pre-change | `E0-P0A-BASE1` | editable | Apply only frozen vendor seam. |
| Broken-root protected artifact hashes | `correct` reverified | `E0-P0A-HASH1` | inspect-only | Use as source material; verify again after copy. |
| Baseline C35 provider-neutral runtime | `correct` (`57/57`) | `E0-P0A-C351` | validation-only | Candidate must remain `57/57`; do not fix role hashes. |
| Clean-base package doctor | `partial` / inherited role mismatch | `E0-P0A-DOCTOR1` | validation-only | Classify as expected development-vs-portable mismatch. |
| Clean-base development doctor | `partial` / inherited governance drift | `E0-P0A-DOCTOR1` | validation-only | Candidate may not introduce an attributable new failure. |
| Clean-base capability doctor | `correct` (`PASS`, registry 13, canonical 8/8) | `E0-P0A-DOCTOR1` | validation-only | Re-run after vendor records; preserve optional Aesthetica honesty. |
| Base canonical identities/quorum | `correct` | `E0-P0A-DOCTOR1` | preserve-only | Must remain exact eight and `8/8`. |
| Base `.codex` profiles/configuration | `correct` and protected | `E0-P0A-DOCTOR1` | preserve-only | Do not copy broken-root absence or fabricate profiles. |
| Vendor adapter in base | `correct` reconstructed | `E2-P2A-SRC1` | editable new file | Preserve hash-bound adapter; validate in P3. |
| Vendor registry records in base | `correct` reconstructed | `E2-P2A-SRC1` | additive hunk | Preserve base 13 plus exactly two vendor records. |
| Vendor snapshots in base | `correct` reconstructed | `E2-P2A-HASH1` | exact copy verified | Keep both trees preserve-only after hash proof. |
| Existing router | `correct` with additive vendor projection | `E2-P2B-SRC1` | additive hunk | Preserve all non-vendor logic; run final differential. |
| Foundation test expectations | `correct` for vendor registry/adapter boundary | `E2-P2B-TEST1` | vendor-specific assertions only | Keep C35 and role surfaces untouched. |
| Vendor focused tests | `correct` (`17/17`) | `E2-P2B-TEST1`, `E3-P3A-TEST1` | validation-only after addition | Supervisor recheck and final closure. |
| Anvien graph | `correct` for indexed source, `.p2p` file-detail `UNKNOWN`; detect exit `0` | `E0-P0A-ANV1`, `E0-P0A-ANV2`, `E3-P3B-ANV1` | validation-only | Use direct source diff for hidden/untracked paths; semantic coverage is partial but Git authority is valid. |
| Owner approval/promotion | `Owner approval recorded` for exact checkpoint; promotion `missing` by design | `E3-P3B-COMMIT1`, `E4-OWNER-APPROVAL1` | preserve-only | Stop at approved-unpromoted state; do not promote. |

## P0 Decision

P0 is complete. The base is `557b502758581812a8845355ed6b426ba75372ec` with
tree `2bd89d97f8877d372f0444218ec9c7339da14d7f` because it is the explicitly
verified clean reference and no newer descendant canonical/owner-promoted ref
was proven in current valid Git/remote inspection. Implementation may proceed
only in the new valid branch/worktree.

## Status Refresh Log

| Time | Transition | Evidence | Plan consequence |
|---|---|---|---|
| `2026-08-25 P0` | broken root authority `unknown -> blocked`; candidate worktree `missing -> correct`; vendor seam `missing -> editable-unbound` | `E0-P0A-AUTH1..E0-P0A-ANV2` | P1 scope freeze and P2 minimal reconstruction permitted. |
| `2026-08-25 P2-A` | vendor trees/adapter/records `unbound -> correct` | `E2-P2A-HASH1`, `E2-P2A-SRC1` | P2-B completed; proceed to full differential. |
| `2026-08-25 P2-B` | router/tests `partial -> correct` | `E2-P2B-SRC1`, `E2-P2B-TEST1` | P3 differential gate. |
| `2026-08-25 P3-A` | technical candidate `partial -> technically ready pending supervisor` | `E3-P3A-TEST1`, `E3-P3A-DOCTOR1`, `E3-P3A-DIFF1` | P3-B source-scope, report, and supervisor gate. |
| `2026-08-25 P3-B-precheck` | Git/Anvien authority `unknown -> usable`; candidate remains unpromoted | `E3-P3B-GIT1`, `E3-P3B-ANV1` | Supervisor review completed; create one local checkpoint only. |
| `2026-08-25 P3-B-supervisor` | technical candidate `ready pending checkpoint -> supervisor PASS` | `E3-P3B-SUP1` | Checkpoint identity confirmed; retain Owner gate separate. |
| `2026-08-25 Owner closure` | exact checkpoint `unclosed -> Owner approved/unpromoted` | `E3-P3B-COMMIT1`, `E4-OWNER-APPROVAL1`, `E4-HASH-CLOSURE1` | Stop; no merge, push, promotion, or source mutation. |
