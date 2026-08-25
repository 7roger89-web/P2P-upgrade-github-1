# P2P-VDRIFT01 Canonical Vendor Snapshot Drift Repair Plan

## Metadata

- Date: `2026-08-26`
- Status: `in_progress`
- Plan: `docs/plans/2026-08-26-p2p-vdrift01-vendor-snapshot-repair/2026-08-26-p2p-vdrift01-vendor-snapshot-repair-plan.md`
- Evidence: `docs/plans/2026-08-26-p2p-vdrift01-vendor-snapshot-repair/2026-08-26-p2p-vdrift01-vendor-snapshot-repair-evidence.md`
- Benchmark: `docs/plans/2026-08-26-p2p-vdrift01-vendor-snapshot-repair/2026-08-26-p2p-vdrift01-vendor-snapshot-repair-benchmark.md`
- Actual status: `docs/plans/2026-08-26-p2p-vdrift01-vendor-snapshot-repair/2026-08-26-p2p-vdrift01-vendor-snapshot-repair-actual-status.md`

## Goal

Determine the byte-level cause of the canonical vendor snapshot drift for
`creative.copywriting` and `media.whiteboard_animation`, then repair only the
canonical verifier defect if the repository evidence justifies it. Preserve the
two promoted identities unless their historical source is conclusively proven
wrong; in that case stop for Owner decision.

## Rules

- Complete P0 actual status before implementation work.
- SFI01, Manus R2, RampStack content, registry expansion, and upstream vendor content are preserve-only.
- Never make tests pass by replacing expected hashes, disabling verification, or adding capability-specific/platform-specific exceptions.
- Compare Git blob bytes, raw checkout bytes, path sets, modes, links, attributes, and historical promoted inputs before editing.
- Use the smallest deterministic fix supported by evidence.
- Record evidence and benchmarkable hash/path counts as they are obtained.
- Run Anvien freshness, file-detail/impact before production edits, and detect-changes before any implementation commit.
- Do not push, merge, promote, release, deploy, use credentials, or call Manus API.

## Problem

On the reported SFI01 baseline, the existing vendor verification rejects two
registry identities even though SFI-owned tests pass. The same mismatch must be
reproduced on a fresh untouched canonical checkout and classified as checkout
contamination, canonical source/path-set drift, or verifier/hash-semantic drift.

## Scope

- Fresh checkout from `af02170ac7ba180900ca78beb26a2972d80c73b6`.
- Existing vendor verification and its direct owner `vendor_skill.py`.
- Registry provenance for the two named capabilities.
- Git attributes, checkout filters, path sets, bytes, modes, symlinks, ignored files, and historical snapshot evidence.
- Focused falsification/regression tests for snapshot invariants.
- Full baseline validation after a justified repair.
- Separate candidate commit/tree and fresh Supervisor review.

## Non-Goals

- No SFI01 implementation changes or integration.
- No Manus R2 changes, API calls, credentials, or upstream content mutation.
- No registry hash rewrite unless historical identities are conclusively wrong; then stop before changing them.
- No release, promotion, deployment, push, merge, or cleanup of unrelated worktrees.
- No broad refactor of capability loading or unrelated baseline failures.

## Requirements

1. Record fresh commit/tree/status/config/attributes.
2. Run only `python -m unittest -q tests.test_p2p_vendor_skill_integration` before broader analysis.
3. Report every differing file and test hypotheses A-K from the request.
4. Determine whether the implementation defines Git-object, normalized logical, exact working-tree, or upstream-package semantics.
5. Add falsification tests for mutation, missing file, unexpected file, stale identity, and path-set drift; add LF/CRLF equivalence only if proven material.
6. Require Vendor 17/17, Host Projection 30/30, Manus 8/8, Foundation 28/28, C35 57/57, doctor PASS, denominator 8, quorum 8/8, and compileall PASS after repair.

## Acceptance Criteria

- Fresh baseline reproduction is classified with exact evidence.
- Root cause is byte/path/attribute proven, not inferred from the observed hash alone.
- The repaired verifier preserves fail-closed behavior and the two promoted identities unless Owner decision is explicitly required.
- Focused falsification tests and the required full regression matrix pass.
- The candidate has a known commit/tree, clean scoped diff, and a fresh independent Supervisor PASS. Any missing gate yields a blocked terminal verdict.

## Checklist

- [x] P0-A: Complete actual status before implementation work.
  - Goal: establish fresh canonical reality and reproduce the reported symptom.
  - Work Steps: record exact commit/tree/status/config/attributes; run only the vendor suite; classify the reproduction and harness prerequisites.
  - Implementation Gate: no production edit before the actual-status file records the baseline and evidence IDs.
  - Acceptance: baseline is either contamination-only or inherited defect with exact command output.

### P1: Byte-level diagnosis and semantic reconstruction

- Phase Goal: identify the exact file/path/byte cause and the historical meaning of the promoted hashes.
- Phase Boundary:
  - In scope: verifier, registry provenance, vendor trees, Git objects, attributes, history, and isolated diagnostic fixtures.
  - Out of scope: SFI01, Manus R2, registry replacement, and upstream content.
  - Dependencies: P0 reproduction and fresh baseline fingerprint.
- Phase Implementation Rule: do not implement P1 directly. Complete P1-A diagnosis, record evidence and refresh status, then proceed to P1-B only if a canonical verifier defect is proven.
- Ordered Slice List:
  - P1-A: Build byte/path/attribute evidence and determine semantics.
  - P1-B: Run Anvien impact and implement only the proven canonical verifier correction.

- [ ] P1-A: Build byte/path/attribute evidence and determine semantics.
  - Goal: distinguish checkout conversion, path-set drift, actual mutation, historical source mismatch, and nondeterminism.
  - Scope Boundary:
    - Editable: none; diagnostic artifacts and plan ledgers only.
    - Inspect-only: vendor trees, registry, verifier, Git history, attributes, and SFI01 comparison.
    - Preserve-only: SFI01 and Manus worktrees.
    - Out of scope: changing expected hashes or verifier behavior.
  - Non-Goals: no semantic guess based on Windows alone.
  - Pre-flight Questions:
    - Data source: Git blobs, fresh working tree, registry provenance, and historical commits.
    - Display permission: N/A; no UI.
    - DB read flow: N/A; file/hash integrity only.
    - DB write flow: N/A; diagnostic outputs are isolated.
    - Render location: N/A.
    - UI behavior flow: N/A.
    - Docker runtime: N/A; no app runtime.
    - Playwright target: N/A.
    - Behavior test: existing vendor verification plus deterministic fixture probes.
    - Cleanup/quarantine: all temporary fixtures under this checkout's `.tmp`.
    - External side effects: none.
    - N/A notes: host projection and Manus package are downstream validation only.
  - Work Steps:
    1. Enumerate registry roots, all tracked files, raw checkout files, ignored/untracked files, Git blob IDs, bytes, sizes, line endings, BOM/Unicode, modes, links, and attributes.
       - UI flow check: N/A.
       - DB/data flow check: verify path-set and byte-set inputs to the snapshot function.
       - Render location check: N/A.
       - Evidence target: per-file table plus hypotheses A-K result.
    2. Compare historical promoted inputs and rerun the snapshot function repeatedly and on controlled LF/CRLF checkouts.
       - UI flow check: N/A.
       - DB/data flow check: prove the semantic category and deterministic ordering.
       - Render location check: N/A.
       - Evidence target: expected-hash provenance, repeatability, and cross-platform comparison.
  - Implementation Gate:
    - P0 actual status is complete; no verifier edit is allowed until the exact owner and root cause are recorded.
    - Any candidate production file must receive Anvien file-detail and impact evidence after graph refresh.
  - Acceptance:
    - Source: all relevant source and history paths inspected.
    - Runtime/UI: N/A.
    - DB/data: path and byte invariants are explicit.
    - Behavior test: original mismatch is reproduced or contamination is conclusively isolated.
    - Cleanup/quarantine: fixtures are repo-local and removed or excluded from the candidate diff.
    - Evidence IDs: `E0-P0A-*`, `E1-P1A-*`.
    - Actual-status rows refreshed: vendor verifier, registry, vendor trees, and test harness.
  - Evidence Targets: baseline fingerprint, failure output, per-file forensic table, history and semantics conclusion.
  - Actual-status Update: mark diagnosis as proven, ambiguous, or blocked before any P1-B edit.
  - Commit Boundary: no implementation commit; diagnostic evidence may remain only in the plan/report.

- [ ] P1-B: Implement the proven canonical verifier correction.
  - Goal: close only the identified canonical invariant defect.
  - Scope Boundary:
    - Editable: the smallest canonical verifier/test surface proven responsible.
    - Inspect-only: registry identities unless Owner decision is required.
    - Preserve-only: vendor source content, SFI01, Manus, and unrelated tests.
    - Out of scope: platform/capability special cases and verification weakening.
  - Non-Goals: no hash replacement without historical proof.
  - Pre-flight Questions:
    - Data source: canonical repository content and existing verifier contract.
    - Display permission: N/A.
    - DB read flow: N/A.
    - DB write flow: N/A.
    - Render location: N/A.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: direct snapshot falsification/regression tests.
    - Cleanup/quarantine: temporary fixture roots only.
    - External side effects: none.
    - N/A notes: no host/browser evidence applies.
  - Work Steps:
    1. Patch the canonical verifier and direct tests after file-detail/impact evidence.
       - UI flow check: N/A.
       - DB/data flow check: verify canonical path/byte/mode/link semantics at the hash boundary.
       - Render location check: N/A.
       - Evidence target: diff, impact, direct focused tests.
    2. Run full build/compile and required baseline suites, then refresh plan ledgers.
       - UI flow check: N/A.
       - DB/data flow check: run vendor, Host Projection, Manus package, Foundation, C35, doctor, denominator/quorum checks.
       - Render location check: N/A.
       - Evidence target: complete regression matrix and clean scoped diff.
  - Implementation Gate:
    - Root cause must be proven and historical identities must remain justified.
  - Acceptance:
    - Source: canonical verifier implements the proven semantics without capability/platform exception.
    - Runtime/UI: N/A.
    - DB/data: all required snapshot falsifications pass.
    - Behavior test: full requested regression matrix passes.
    - Cleanup/quarantine: no diagnostic fixture or transient state is in the candidate.
    - Evidence IDs: `E1-P1B-*`, `E2-P2A-*`.
    - Actual-status rows refreshed: verifier, tests, and candidate status.
  - Evidence Targets: source diff, focused test output, full regression output, compileall, doctor/quorum, detect-changes.
  - Actual-status Update: mark repaired or blocked with exact remaining gate.
  - Commit Boundary: one small implementation checkpoint after focused verification; later review/fix commits separate.

### P2: Supervisor and closure

- Phase Goal: independently verify the exact candidate head and close only with fresh evidence.
- Phase Boundary:
  - In scope: exact candidate diff/tree, reports, required regression results, and Supervisor review.
  - Out of scope: merge, promotion, release, deployment, push, SFI integration.
  - Dependencies: P1-B repair and all technical gates.

- [ ] P2-A: Fresh independent Supervisor review.
  - Goal: verify the repair claim against current source and evidence.
  - Work Steps: inspect source/diff; rerun targeted evidence; verify same-invariant surfaces; write fresh PASS/REJECT report.
  - Implementation Gate: candidate head and technical report hashes are fixed.
  - Acceptance: Supervisor result is fresh and exact-head bound; otherwise terminal verdict remains blocked.

- [ ] P2-B: Close the isolated candidate without integration.
  - Goal: provide required report and stop before SFI merge/replay.
  - Work Steps: record commit/tree/diff summary and explicit SFI next sequence; do not merge or promote.
  - Implementation Gate: P2-A PASS or explicit blocker.
  - Acceptance: terminal verdict is one of the user-authorized VDRIFT01 verdicts and all requested report fields are present.

## Risk Notes

- The fresh baseline may expose a pre-existing repository/test-harness defect in addition to vendor drift; keep these classifications separate.
- The current Windows checkout has `core.autocrlf=true`; this is an observation, not a root-cause conclusion.
- Running the doctor may mutate an adapter state file; use isolated state or restore only the exact state file created by this candidate before final status.
- Full baseline validation may remain blocked by independent host/Manus requirements; report exact blockers instead of substituting local passes.
