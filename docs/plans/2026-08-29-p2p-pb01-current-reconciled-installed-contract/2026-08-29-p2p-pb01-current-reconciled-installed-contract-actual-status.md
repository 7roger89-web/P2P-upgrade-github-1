# P2P-PB01 Current Canonical Reconciliation and Installed Contract Fix Actual Status

Title: P2P-PB01 Current Canonical Reconciliation and Installed Contract Fix
Date: 2026-08-29
Status: P2 Complete; P3-A in progress
Companion plan: `docs/plans/2026-08-29-p2p-pb01-current-reconciled-installed-contract/2026-08-29-p2p-pb01-current-reconciled-installed-contract-plan.md`
Companion evidence: `docs/plans/2026-08-29-p2p-pb01-current-reconciled-installed-contract/2026-08-29-p2p-pb01-current-reconciled-installed-contract-evidence.md`
Companion benchmark: `docs/plans/2026-08-29-p2p-pb01-current-reconciled-installed-contract/2026-08-29-p2p-pb01-current-reconciled-installed-contract-benchmark.md`

## Purpose

This file records current reality before implementation. It does not authorize
promotion, release, deployment, or live activation.

## Scope

Target scope:

- Fresh candidate from official current main.
- Disjoint PB01 carry-forward.
- Installed bootstrap launcher required-file correction.
- Focused acceptance and one independent Supervisor review.

Out of scope:

- Current 02A capability/provenance/vendor/test/report history.
- Broad tests, Anvien, graph/impact, benchmark regeneration, promotion, and live action.

## Relationship / Impact Evidence

Anvien file-detail/impact was not run because the current user explicitly set a
verification ceiling excluding Anvien and graph/impact analysis. Static Git path
comparison is the applicable scope evidence.

| Unit / File / Surface | File Detail Evidence | Related File Count | Relationship Summary | Impact Note |
|-----------------------|----------------------|--------------------|----------------------|-------------|
| Old PB01 delta | E0-P0A-OVERLAP1 | N/A | 9 PB01 paths vs 47 current-main paths | disjoint; carry only PB01 |
| Current 02A paths | E0-P0A-02A1 | 47 changed paths | capability/vendor/provenance/tests/reports | preserve-only |
| Installed required-file contract | Supervisor finding / E1-P1B-FIX1 | N/A | tuple gates installed runtime identity | edit one entry only |

## Current Status Matrix

| Unit | Current State | Required State | Status | Relationship Count | Evidence | Next Plan Decision |
|------|---------------|----------------|--------|--------------------|----------|--------------------|
| Official current `main` | `6cc7555...`, tree `b308b9cf...`, clean fresh clone | exact candidate base | correct | N/A | E0-P0A-AUTH1, E0-P0A-CLONE1 | preserve as base |
| Old PB01 implementation | valid source/evidence at `fa58949...` | carried onto current main | correct | 5 implementation paths carried; 0 overlap | E0-P0A-OLD1, E0-P0A-OVERLAP1, E1-P1A-CARRY1 | verify candidate identity |
| Current 02A history | present on current main | unchanged in candidate | correct | 47 delta paths | E0-P0A-02A1 | preserve-only |
| Installed required-file contract | launcher omitted from tuple | launcher required | correct | 1 tuple entry added | E1-P1B-FIX1, E2-P2A-INSTALL1 | independent review |
| BG01/EFF01/control plane | current-main behavior | unchanged | correct | N/A | E0-P0A-02A1 | preserve-only |

## Status Refresh Log

| Refresh | Date | Repo Basis | Changed Scope | Status Changes | Evidence | Next Phase Update |
|---------|------|------------|----------------|----------------|----------|-------------------|
| R0 | 2026-08-29 | fresh official clone at current main | authority and reconciliation scope | baseline established; PB01 `partial`, installed contract `partial`, 02A `correct` | E0-P0A-AUTH1..E0-P0A-SCOPE1 | proceed with disjoint P1-A |
| R1 | 2026-08-29 | isolated candidate from current main | PB01 carry-forward and installed contract fix | PB01 `partial -> correct`; installed contract `partial -> correct`; 02A remains `correct` | E1-P1A-CARRY1..E2-P2A-VERIFY1 | create checkpoint and request one Supervisor |

## Phase Touch Map

| Unit / File / Surface | Plan-Relevant Relationship File | Relationship to Target | Plan Item | Touch Mode | Evidence | Constraint |
|-----------------------|---------------------------------|------------------------|-----------|------------|----------|------------|
| `scripts/p2p_bootstrap.py` | existing workflow/BG01 | PB01 adapter | P1-A | edit/carry | E0-P0A-OLD1 | no new orchestration |
| `scripts/p2p_workflow.py` | PB01 adapter | existing control plane | P1-A | preserve-only | E0-P0A-02A1 | no edit |
| `install.ps1`, `install.sh`, `scripts/package_release.py` | bootstrap launcher | package/install inclusion | P1-A | carry/preserve | E0-P0A-OLD1 | no framework change |
| `INSTALLED_REQUIRED_FILES` | installed validator | required-file contract | P1-B | edit | E1-P1B-FIX1 | add launcher only |
| 02A capability/vendor/test/report paths | current main | unrelated current history | all | do-not-touch | E0-P0A-02A1 | preserve exact paths |

## Detailed Findings

### Current authority and overlap

Current official main was freshly cloned and verified before mutation. The old
PB01 delta and current-main delta have no common paths, so no semantic overlap is
manufactured. Current 02A history remains preserve-only.

Classification: `correct` for authority/02A preservation, PB01 carry-forward,
and installed launcher contract after focused verification.

Allowed next action: create the isolated candidate checkpoint and run the one
independent Supervisor review.

Forbidden next action: overwrite current-main files broadly, drop/revert 02A,
promote, rebase, or create a second control plane.

### Installed launcher contract

The reviewed PB01 source and package/install copy paths include the launcher,
but the installed required-file tuple does not. This is `partial`, not a
validator redesign requirement.

Implemented action: added `scripts/p2p_bootstrap.py` to the existing tuple and
proved accepted-present/rejected-missing cases.

Forbidden next action: silently accept an installed runtime missing the launcher
or redesign package validation.

## Next Phase Status Decisions

| Plan Item | Actual Status Finding | Required Status / Next-Action Update |
|-----------|-----------------------|--------------------------------------|
| P1-A | PB01 delta is disjoint from current 02A | complete; only PB01 source/package/install/test paths carried |
| P1-B | installed tuple omitted launcher | complete; one required-file entry and positive/negative outcomes pass |
| P2-A | focused verification ceiling | complete; 16/16, contract, compile, and diff checks pass |

## Implementation Gate

- [x] Target scope is listed in Current Status Matrix.
- [x] Each target unit has a status.
- [x] Each status has evidence IDs.
- [x] Phase Touch Map defines preserve/edit modes.
- [x] Correct current-main and 02A parts are preserve-only.
- [x] Partial PB01/installed parts have exact next actions.
- [x] Blockers are recorded, if any.
- [x] Next phase assumptions and work steps reflect fresh overlap evidence.
- [x] Status Refresh Log has an R0 baseline row.
- [x] Implementation slices have been refreshed after changes.

## Final P0 Decision

- [ ] P0 actual-status incomplete. Implementation is blocked.
- [x] P0 complete. Next phase can proceed with the recorded disjoint PB01 scope.
- [ ] P0 complete. Next phase status must be updated before implementation.
- [ ] P0 complete. Target scope is preserve-only.
- [ ] P0 complete. Implementation is blocked by missing authority or evidence.

Decision note:

Fresh official main is authoritative and clean. Old PB01/current-main path
overlap is zero. The installed required-file omission was corrected minimally;
focused acceptance and package/install/compile/diff checks pass while 02A and
all existing control-plane/safety surfaces remain preserve-only. The candidate
still requires independent Supervisor review and a separate Owner gate.
