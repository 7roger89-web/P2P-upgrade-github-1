# Supervisor Report: P2P-C14 External Release-Slot Collision

Verdict: REJECT

## Metadata

- Report file: `rp_supervisor_260815_090858_by_gpt-5-codex_p2p-c14-collision-resolution.md`
- Review time: `2026-08-15 09:08:58 +07:00`
- Reviewer: `gpt-5-codex`
- Repo/project: `P2P-8.4.6-C-Codex-Edition-v4`
- Scope reviewed: read-only classification and canonical-policy review of the external `.19` filename collision
- Claim reviewed: resolve the collision and promote the exact approved P2P-C14 `.19` candidate without changing its bytes or reusing approval
- Authority used: current P2P-C14 continuation request, repository `AGENTS.md`, approval policy, package builder, release gate, canonical records, and artifact metadata
- Related artifacts: approved C14 candidate, C14 approval/final gate, external conflicting ZIP, historical `.15` approval/final gate

## Executive Summary

- Problem: `D:\AI\P2P_dev\P2P-8.4.7-C-Codex-Edition-v19.zip` occupies the desired filename but is not the approved `.19` candidate.
- Decision: REJECT promotion at this time. The conflicting file is best classified as `STALE_DEVELOPMENT_ARTIFACT`, but the repository has no canonical collision-specific archive/quarantine operation and the current approval does not authorize moving it.
- Required outcome: obtain a separate, explicitly scoped owner decision for a reversible archive/quarantine of the exact conflicting path and SHA, or provide an existing canonical collision-resolution target. Then recheck all bindings before any promotion.

## Blocking Findings

### [P1] Canonical release destination is occupied by a different artifact

File: `D:\AI\P2P_dev\P2P-8.4.7-C-Codex-Edition-v19.zip`

Issue: The external file has SHA-256 `f1209c441edaff20ccc3e40f0be0b8b9baa5625ca5ae3599bcc81c3e42d55b61`, while the approved C14 subject has SHA-256 `3a9ee51321e1f5e40e35ce73eb90727cddb571a672aa095d16d76af2feb03dd8`.

Evidence: fresh hash recomputation; the external ZIP is 2,407,704 bytes, created `2026-08-14T11:46:06.673304Z`, modified `2026-08-14T11:46:07.123327Z`, and its `release-manifest.json` was generated at `2026-08-14T11:46:03Z`.

Why this blocks acceptance: replacing or relabeling the file would violate the current request's no-overwrite/no-delete/no-rebuild boundary and would not be covered by the C14 approval subject.

Fix direction: preserve the conflicting bytes and SHA, but do not move them until an explicit owner decision names a reversible archive/quarantine target or an existing canonical collision mechanism authorizes it.

Re-review evidence required: exact archive target, preservation/rollback proof, fresh approved-candidate hash, and a collision-resolution record bound to the operation.

### [P1] Conflicting artifact has no current authority binding

File: `D:\AI\P2P_dev\P2P-8.4.6-C-Codex-Edition-v4\.p2p\gates\records` and `D:\AI\P2P_dev\P2P-8.4.6-C-Codex-Edition-v4\.tmp\p2p-c14-final\records`

Issue: No canonical release record or current approval binds the conflicting SHA/path. The active C14 approval binds only the `.tmp` candidate subject and exact C14 SHA. The historical `.15` approval binds a different path/SHA and is expired.

Evidence: canonical record scan found no hit for the conflicting path/SHA; current `p2p_approval.py verify` passed only for the C14 subject; the historical `.15` approval verification reports `approval request has expired`.

Why this blocks acceptance: authority cannot be inferred from the filename, and the current owner approval cannot be reused for a different artifact or for relocating an unapproved artifact.

Fix direction: obtain owner-scoped authorization for the exact conflict-resolution operation, without changing the C14 candidate approval.

Re-review evidence required: explicit owner action naming the old artifact path/SHA and the exact reversible destination, plus a fresh collision-resolution technical record.

### [P1] Existing mechanism has no collision-specific archive/quarantine path

File: `scripts/package_release.py:408-412`; `scripts/p2p_gate.py:241-281`

Issue: The canonical builder refuses an existing output with `Output already exists; choose another path to preserve history`. The final gate rehashes the subject and validates approval/report bindings, but does not move, archive, quarantine, or deploy an occupied output.

Evidence: source inspection of the existing builder/finalizer and the release guide's statement that finalization proves the unchanged approved candidate but does not deploy it. Repository search found no canonical collision-specific promotion or quarantine command.

Why this blocks acceptance: inventing an alternate filename or moving the conflicting file would expand the release convention and scope beyond the existing mechanism.

Fix direction: use an existing canonical policy if one is supplied; otherwise obtain owner approval for the exact non-destructive archive/quarantine operation before implementation.

Re-review evidence required: canonical operation or owner-approved target/preservation record; no candidate rebuild or approval transfer.

## Source-Level Clearance Notes

- `scripts/package_release.py`: clear for the reviewed behavior; source was inspected only. It explicitly refuses to overwrite an existing output.
- `scripts/p2p_gate.py`: clear for the reviewed behavior; finalization validates bindings and writes a final gate report but does not resolve an external filename collision.
- Production runtime/source: not applicable; no code, candidate, or artifact was modified.

## Evidence Checked

Passed:

- Approved C14 candidate hash: `3a9ee51321e1f5e40e35ce73eb90727cddb571a672aa095d16d76af2feb03dd8`.
- C14 technical report hash: `a85e83faffcb1f10efd5a772019c877ff8c8e85e3aae5a38e73a5e933671cf46`.
- C14 approval verification: `PASS`, request `P2P-APR-20260815T013545Z-0068b3047f`.
- C14 final gate: `PASS / APPROVED`, exact subject/report hashes preserved.
- Conflicting ZIP embedded `VERSION`: `8.4.7-C-codex.15`.
- Conflicting ZIP `manifest/package.json` version: `8.4.7-C-codex.15`.
- Conflicting ZIP `runtime/p2p.manifest.json` package version: `8.4.7-C-codex.15`.
- Conflicting ZIP `RELEASE-NOTES.md` heading: `.15`.
- Conflicting ZIP `release-manifest.json`: package version `.15`, generated at `2026-08-14T11:46:03Z`, file count `399`.
- Conflicting ZIP `manifest/build-report.json`: package version `.9`, further evidence of stale packaging metadata.
- Official `.15` record: exact approved path/SHA is different (`af4d63a882dabfde20ac237574590ec584ee2944bc4cdc30b6a07bf7f681e195`).
- Verification freshness: fresh for the collision artifact, current C14 approval/final gate, canonical record scan, and policy/source inspection.

Failed:

- Canonical promotion of the exact C14 candidate to the occupied external `.19` slot was not safe to execute under the current authority and mechanism.

Not run:

- Archive/quarantine, move, delete, overwrite, copy, promotion, post-promotion doctor, Design Intelligence discovery, 174-faculty check, NUI provenance check, and quorum check; all require a safe promoted artifact and/or additional owner authority.
- Protected external user projects were not inspected or modified; repository scope was used for project/install-manifest search.

## Invariant Closure

- affected invariant: exact artifact identity, approval subject binding, immutable history, and canonical release-slot ownership.
- sibling surfaces checked: external ZIP metadata, embedded version/release manifests, package builder, final gate, approval policy, canonical gate/approval records, current C14 approval, historical `.15` approval, and repo-owned lifecycle references.
- residual unverified same-invariant surfaces: the external filesystem's owner intent and any out-of-repository release registry are unavailable; this is why promotion remains blocked.

## Required Fix List For Resubmission

1. Owner must explicitly authorize a reversible archive/quarantine of the exact conflicting artifact `D:\AI\P2P_dev\P2P-8.4.7-C-Codex-Edition-v19.zip` with SHA-256 `f1209c441edaff20ccc3e40f0be0b8b9baa5625ca5ae3599bcc81c3e42d55b61`, naming the destination and rollback/preservation requirements, or identify an existing canonical collision mechanism.
2. Recompute the approved C14 candidate SHA and verify request `P2P-APR-20260815T013545Z-0068b3047f` plus technical-report binding immediately before any authorized promotion. Do not transfer approval to another path/version.
3. After a safe resolution, verify the promoted artifact itself and record the final path, SHA, embedded version, release manifest, package/doctor checks, Design Intelligence discovery, 174-faculty registry, NUI provenance, canonical 8/quorum, and approval linkage.

## Overall Evaluation

The approved C14 candidate and its release gate are valid, but the requested collision resolution cannot be accepted under current authority. The old `.19`-named file is not official by the available records and is strongly evidenced as a stale development artifact; nevertheless, moving it is a new protected external mutation. No artifact was deleted, overwritten, moved, rebuilt, or promoted during this review.
