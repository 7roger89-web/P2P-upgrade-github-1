# P2P-VDRIFT01 Canonical Vendor Snapshot Drift Repair Actual Status

Title: P2P-VDRIFT01 Canonical Vendor Snapshot Drift Repair
Date: 2026-08-26
Status: P0 Complete
Companion plan: `docs/plans/2026-08-26-p2p-vdrift01-vendor-snapshot-repair/2026-08-26-p2p-vdrift01-vendor-snapshot-repair-plan.md`
Companion evidence: `docs/plans/2026-08-26-p2p-vdrift01-vendor-snapshot-repair/2026-08-26-p2p-vdrift01-vendor-snapshot-repair-evidence.md`
Companion benchmark: `docs/plans/2026-08-26-p2p-vdrift01-vendor-snapshot-repair/2026-08-26-p2p-vdrift01-vendor-snapshot-repair-benchmark.md`

## Purpose

P0 records the actual state before any implementation edit. The mismatch is
reproduced on a new checkout, so the work is not classified as SFI-only
environment contamination.

## Scope

Target scope:

- `.p2p/system/p2p_capabilities/vendor_skill.py` snapshot semantics and direct tests, only if proven.
- `.p2p/system/p2p_capabilities/capabilities.json` and vendor trees as inspect-only evidence.
- Required downstream baseline validation.

Out of scope:

- SFI01 worktree and candidate `ecf58a8`.
- Manus R2 worktree/scripts/API/credentials.
- RampStack content and canonical registry expansion.
- Push, merge, promotion, release, deployment.

## Relationship / Impact Evidence

| Unit / File / Surface | File Detail Evidence | Related File Count | Relationship Summary | Impact Note |
|-----------------------|----------------------|--------------------|----------------------|-------------|
| `vendor_skill.py` | pending after `anvien analyze --force` | pending | snapshot hashing and vendor loader owner | high scope warning; edit only after proof |
| `tests/test_p2p_vendor_skill_integration.py` | pending after graph refresh | pending | direct vendor verification/falsification tests | medium scope warning |
| `capabilities.json` | inspect-only via source/registry | N/A | promoted expected identities and vendor provenance | preserve-only |
| two `.p2p/vendor/skill/*` trees | Git/tree forensic evidence | N/A | hashed source/path inputs | preserve-only |

## Status Rules

| Status | Meaning | Allowed next action |
|--------|---------|---------------------|
| `correct` | Already behaves as required. | Preserve. |
| `partial` | Some required behavior exists but has a gap. | Change only the gap. |
| `wrong` | Current behavior or contract is incorrect. | Replace only with evidence. |
| `missing` | Required evidence or behavior does not exist. | Establish it before implementation. |
| `blocked` | Authority or evidence is unclear. | Stop. |

## Current Status Matrix

| Unit | Current State | Required State | Status | Relationship Count | Evidence | Next Plan Decision |
|------|---------------|----------------|--------|--------------------|----------|--------------------|
| Fresh canonical checkout | `HEAD=af02170ac7ba180900ca78beb26a2972d80c73b6`; clean at baseline | exact canonical baseline | correct | N/A | E0-P0A-FP1 | preserve |
| Existing vendor verifier | rejects two promoted IDs on fresh checkout | deterministic canonical verification | partial | pending | E0-P0A-REPRO1 | diagnose P1-A |
| `creative.copywriting` snapshot | actual `146e5d...7183f8`; expected `5a02c...52830d` | promoted identity unless proven wrong | wrong/undetermined cause | N/A | E0-P0A-REPRO1 | inspect-only P1-A |
| `media.whiteboard_animation` snapshot | actual `2d0b33...ad7d3`; expected `55db...8742c` | promoted identity unless proven wrong | wrong/undetermined cause | N/A | E0-P0A-REPRO1 | inspect-only P1-A |
| Vendor test harness `.tmp` prerequisite | absent in fresh clone; test 16 errors before mutation assertion | isolated fixture root available | partial | N/A | E0-P0A-HARNESS1 | create repo-local test dir only |
| SFI01 candidate | separate existing worktree, not touched | unchanged | correct/preserve-only | N/A | boundary instruction | do-not-touch |
| Manus R2 | not used | unchanged | correct/preserve-only | N/A | boundary instruction | do-not-touch |

## Status Refresh Log

| Refresh | Date | Repo Basis | Changed Scope | Status Changes | Evidence | Next Phase Update |
|---------|------|------------|----------------|----------------|----------|-------------------|
| R0 | 2026-08-26 | fresh canonical checkout and first vendor suite | baseline, verifier, two vendor roots, harness prerequisite | mismatch reproduced; SFI contamination ruled out; harness prerequisite isolated | E0-P0A-FP1, E0-P0A-REPRO1, E0-P0A-HARNESS1 | P1-A must finish byte/path/history semantics before any edit |

## Phase Touch Map

| Unit / File / Surface | Plan-Relevant Relationship File | Relationship to Target | Plan Item | Touch Mode | Evidence | Constraint |
|-----------------------|---------------------------------|------------------------|-----------|------------|----------|------------|
| `vendor_skill.py` | `tests/test_p2p_vendor_skill_integration.py` | source owner / direct test | P1-B | edit only if proven | E1-P1B-IMPACT1 | no semantic weakening |
| `capabilities.json` | vendor roots | registry / source inputs | P1-A | inspect-only | E1-P1A-BYTES1 | expected hashes preserve-only |
| vendor roots | Git history and `.gitattributes` | source/path inputs | P1-A | preserve-only | E1-P1A-PATHS1, E1-P1A-ATTR1 | no content mutation |
| SFI01 candidate | none | unrelated candidate | all | do-not-touch | boundary instruction | no integration in this task |
| Manus R2 | none | unrelated blocked workstream | all | do-not-touch | boundary instruction | no API/credentials |

## Detailed Findings

### Fresh baseline and reproduction

Current state:

- Fresh clone uses exact canonical commit `af02170ac7ba180900ca78beb26a2972d80c73b6`.
- The first permitted suite reproduced both named hash mismatches.
- The suite also exposed a separate missing `.tmp` fixture directory error.

Required state:

```text
The canonical verifier must compare the correct deterministic snapshot identity
to the promoted registry identity and retain fail-closed mutation/path checks.
```

Evidence:

- E0-P0A-FP1: fresh checkout fingerprint.
- E0-P0A-REPRO1: two mismatch assertions.
- E0-P0A-HARNESS1: independent test prerequisite error.

Relationship and impact:

- Related file count: pending until graph refresh.
- Relationship summary: verifier -> vendor loader -> host/manus downstream gates -> direct integration tests.
- Impact note: high scope warning; no edit authorized yet.

Classification:

`partial` for verifier behavior; root cause is not yet classified.

Allowed next action:

Run P1-A forensic comparison and historical reconstruction.

Forbidden next action:

Do not update registry hashes, alter vendor content, or touch SFI01/Manus.

## Next Phase Status Decisions

| Plan Item | Actual Status Finding | Required Status / Next-Action Update |
|-----------|-----------------------|--------------------------------------|
| P1-A | fresh reproduction is confirmed; cause remains open | continue unchanged, but classify bytes/path/history before P1-B |
| P1-B | no edit yet | blocked until P1-A proves a canonical verifier defect |
| P2 | no candidate yet | pending |

## Implementation Gate

- [x] Target scope is listed in Current Status Matrix.
- [x] Each baseline target unit has a status.
- [x] Each baseline status has evidence IDs.
- [ ] Target file relationship counts from Anvien file-detail recorded.
- [x] Phase Touch Map defines preserve-only/do-not-touch boundaries.
- [x] Correct parts are marked preserve-only.
- [x] Partial/wrong parts have exact next actions.
- [x] Blockers and independent harness error are recorded.
- [x] Status Refresh Log has an R0 baseline row.
- [x] Next phase status assumptions are updated from baseline evidence.

## Final P0 Decision

- [ ] P0 actual-status incomplete. Implementation is blocked.
- [ ] P0 complete. Next phase can proceed unchanged.
- [x] P0 complete. Next phase status, next action, or work steps must be updated before implementation.
- [ ] P0 complete. Target scope is preserve-only.
- [ ] P0 complete. Implementation is blocked by missing authority or evidence.

Decision note:

P0 is complete for diagnosis: the mismatch is an inherited canonical-baseline
defect, not SFI-only contamination. P1-A must now determine whether the correct
repair is in the verifier, checkout contract, path set, or historical identity.
