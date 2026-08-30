# P2P Game Truyen MPFB Adapter 01 Actual Status

Title: P2P Game Truyen MPFB Adapter 01
Date: 2026-08-30
Status: P1 and P2-A complete. Candidate freeze and exact-subject Supervisor review remain.
Companion plan: `docs/plans/2026-08-30-p2p-game-truyen-mpfb-adapter-01/2026-08-30-p2p-game-truyen-mpfb-adapter-01-plan.md`
Companion evidence: `docs/plans/2026-08-30-p2p-game-truyen-mpfb-adapter-01/2026-08-30-p2p-game-truyen-mpfb-adapter-01-evidence.md`
Companion benchmark: `docs/plans/2026-08-30-p2p-game-truyen-mpfb-adapter-01/2026-08-30-p2p-game-truyen-mpfb-adapter-01-benchmark.md`

## Purpose

This file records the current state before implementation. The target is a
P2P-only adapter contract; Blender/MPFB2, Golden Character generation, and Game
Truyen remain explicitly not authorized.

## Freshness / Refresh Rules

P0 is the baseline. After each implementation slice, affected rows and the
Status Refresh Log must be updated from fresh source/test evidence.

## Scope

Target scope:

- MPFB2 v2.0.17 exact binding and rights split.
- P2P recipe/provenance/GLB validation and bounded command-plan adapter.
- Existing Asset Forge catalog, `game.character.generate` registry metadata,
  and selective project projection references.

Out of scope:

- Blender/MPFB2 install or execution, generated assets, Game Truyen, browser QA,
  visual match, replacement research, promotion, release, or deployment.

## Relationship / Impact Evidence

| Unit / File / Surface | File Detail Evidence | Related File Count | Relationship Summary | Impact Note |
|-----------------------|----------------------|--------------------|----------------------|-------------|
| `tests/test_p2p_game_asset_forge_01.py` | `E0-P0A-GRAPH1` | 10 local | Existing catalog/registry/routing assertions; high Anvien scope warning | high scope warning, focused test edit only |
| `.p2p/system/p2p_capabilities/img2threejs_adapter.py` | `E0-P0A-SRC3` | not projected by hidden-file Anvien query | Existing sibling bounded adapter; preserve-only security precedent | inspect-only |
| `.p2p/system/p2p_capabilities/capabilities.json` | `E0-P0A-SRC2` | not projected by hidden-file Anvien query | Existing single registry and `game.character.generate` identity | targeted metadata edit |
| `docs/p2p-development/capability-catalog/game-asset-forge/capability-catalog.json` | `E0-P0A-SRC1` | not projected by JSON/hidden-file Anvien query | Existing canonical Asset Forge candidate catalog; CAND-ASSET-FORGE-002 is stale | targeted metadata edit |
| `.p2p/system/p2p_capabilities/host_projection.py` | `E0-P0A-SRC2` | not projected by hidden-file Anvien query | Existing projection implementation; no edit planned | preserve-only |
| Game Truyen source | `E0-P0A-SRC2` | N/A, separate repository | Not in candidate worktree and prohibited | do-not-touch |

## Status Rules

| Status | Meaning | Allowed next action |
|--------|---------|---------------------|
| `correct` | Already behaves as required. | Preserve. Add evidence or tests only if needed. |
| `partial` | Some required behavior exists, but gaps remain. | Change only the missing parts. |
| `wrong` | Current behavior, source, or contract is incorrect. | Replace with required behavior. |
| `missing` | Required behavior, source, or contract does not exist. | Implement the missing piece only. |
| `unbound` | Surface exists but is not wired to the real source, flow, or contract. | Bind to the real source only. |
| `fake-or-stub` | Prototype, demo, mock, fallback, or placeholder data is being used as real behavior. | Remove fake behavior or replace it with an approved truthful state. |
| `blocked` | Source, authority, contract, or required evidence is unclear. | Stop. Do not implement until resolved. |

## Current Status Matrix

| Unit | Current State | Required State | Status | Relationship Count | Evidence | Next Plan Decision |
|------|---------------|---------------|--------|--------------------|----------|--------------------|
| Fresh canonical main | isolated worktree from fetched `origin/main` SHA/tree | exact fresh subject recorded | correct | N/A | E0-P0A-GIT1 | preserve in candidate lineage |
| MPFB2 upstream binding | tag resolves to exact v2.0.17 commit/tree; no source vendored | exact SHA/tree and license split bound in P2P metadata | correct | N/A | E0-P0A-UP1..E0-P0A-UP2 | edit P1-A metadata |
| MPFB catalog candidate 002 | old short SHA and `NOASSERTION` license | exact v2.0.17 pin, GPLv3 code, CC0 core assets, conditional status | correct-bound | not projected | E0-P0A-SRC1, E0-P0A-UP1..E0-P0A-UP2, E1-P1A-SRC3 | preserve in frozen candidate |
| `game.character.generate` registry record | existing knowledge-source identity, no adapter binding | same identity with selective adapter metadata, canonical registry unchanged | correct-bound | not projected | E0-P0A-SRC2, E1-P1A-SRC3, E2-P2A-SRC1 | preserve existing surface |
| Recipe schema/validator | absent | allowlisted parametric recipe, unknown-key rejection, no image execution | correct | new | E0-P0A-SRC1, E1-P1A-SRC1..E1-P1A-TEST1 | Supervisor review |
| Asset provenance schema/validator | absent for this lane | per-asset rights/hash fields, core CC0-only, third-party deny | correct | new | E0-P0A-UP2, E1-P1A-SRC2, E1-P1A-TEST1 | Supervisor review |
| MPFB bounded adapter | absent; sibling img2threejs adapter exists | explicit Blender argv/policy and default-deny execution contract | correct | new | E0-P0A-SRC3, E1-P1B-SRC1..E1-P1B-TEST1 | Supervisor review |
| GLB structural validator | absent for this lane | strict GLB/glTF 2.0 structure and resource binding | correct | new | E0-P0A-SRC1, E1-P1C-SRC1..E1-P1C-TEST1 | Supervisor review |
| Existing router/registry/projection | already canonical and shared | reuse exactly; no second architecture | correct/preserve-only | existing | E0-P0A-SRC2, E0-P0A-GRAPH1 | inspect in P2-A |
| Three.js GLTFLoader boundary | future contract only | record future smoke boundary; no execution claim | correct-future-only | N/A | E2-P2A-BOUNDARY1 | preserve as future-only |
| Game Truyen source | not in candidate worktree; prohibited | unchanged | correct/preserve-only | N/A | user scope | do not touch |

## Status Refresh Log

| Refresh | Date | Repo Basis | Changed Scope | Status Changes | Evidence | Next Phase Update |
|---------|------|------------|----------------|----------------|----------|-------------------|
| R0 | 2026-08-30 | fresh isolated worktree at `7763ded` | full adapter lane | baseline classifications above | E0-P0A-GIT1..E0-P0A-GRAPH1 | P1-A/P1-B/P1-C may proceed in order |
| R1 | 2026-08-30 | same isolated candidate; fresh Anvien and focused tests | P1-A/P1-B/P1-C/P2-A | all four slices implemented and focused evidence passes; execution remains unauthorized | E1-P1A-SRC1..E1-P1C-TEST1, E2-P2A-SRC1..E2-P2A-BOUNDARY1 | freeze candidate, run exact-subject Supervisor |

## Phase Touch Map

| Unit / File / Surface | Plan-Relevant Relationship File | Relationship to Target | Plan Item | Touch Mode | Evidence | Constraint |
|-----------------------|---------------------------------|------------------------|-----------|------------|----------|------------|
| recipe validator | `tests/test_p2p_game_asset_forge_01.py` | test consumer | P1-A | edit/add focused test | E0-P0A-GRAPH1, E1-P1A-TEST1 | no external dependency |
| provenance validator/schema | Asset Forge catalog | source-of-truth metadata | P1-A | edit/add | E0-P0A-SRC1, E1-P1A-SRC1..E1-P1A-SRC3 | preserve catalog identity |
| MPFB adapter | `img2threejs_adapter.py` | sibling security precedent | P1-B | add new bounded module; sibling preserve-only | E0-P0A-SRC3, E1-P1B-SRC1 | no semantic changes to img2threejs |
| registry metadata | `capabilities.json` | existing registry source | P1-A/P2-A | targeted edit | E0-P0A-SRC2, E1-P1A-SRC3 | no count/quorum/router change |
| projection metadata | `host_projection.py` | existing consumer | P2-A | preserve/inspect-only | E0-P0A-SRC2 | no second projection |
| Game Truyen | external repository | forbidden consumer | all | do-not-touch | user scope | zero files changed |

## Detailed Findings

### Canonical and upstream identity

Current state:

The requested root contains an incomplete `.git`; a real canonical clone was
fetched and the candidate worktree was created from `origin/main`. MPFB2
`v2.0.17` was resolved from the public tag to an exact commit/tree using a
read-only shallow metadata checkout. The external audit checkout is not part of
the P2P candidate.

Required state:

```text
FRESH_MAIN_SHA=7763ded3476b51acc09bccdfc6cb0c1720f28ba2
FRESH_MAIN_TREE=6a4f7dba5ffb86a6e5da6659ba3a0ae09b1a443b
MPFB_VERSION=2.0.17
MPFB_RELEASE_SHA=80919fa4682335c41847f761a4d79dcad4124732
MPFB_RELEASE_TREE=189a1d6694515ecfbdc40067218c5024389b4e43
MPFB_CODE_LICENSE=GPL-3.0-or-later
MPFB_CORE_ASSET_LICENSE=CC0-1.0
```

Evidence:

- `E0-P0A-GIT1`: fresh remote fetch and isolated worktree identity.
- `E0-P0A-UP1`: exact MPFB commit/tree.
- `E0-P0A-UP2`: code/assets/output license split.

Relationship and impact:

- Related file count: N/A for external binding.
- Relationship summary: external evidence feeds catalog/provenance metadata only.
- Impact note: no upstream source is vendored or executed.

Classification:

correct for P0 authority; implementation metadata is still missing.

Allowed next action:

Bind exact identity and rights metadata in P1-A.

Forbidden next action:

Do not install, execute, vendor, or imply downstream visual proof.

### P2P adapter and output contract

Current state:

Only the img2threejs sibling adapter has bounded execution controls. This lane
has no MPFB recipe, provenance, command-plan, or GLB structural validator.

Required state:

```text
recipe -> validated rights -> bounded Blender command plan -> explicit GLB/provenance output validation
```

Evidence:

- `E0-P0A-SRC1`: existing Asset Forge catalog and missing lane-specific contract.
- `E0-P0A-SRC3`: sibling adapter security controls to preserve.

Relationship and impact:

- Related file count: existing test file has 10 local relationships; hidden `.p2p` surfaces are not projected by Anvien and are direct-inspection targets.
- Relationship summary: new modules are consumed only by new focused tests and selected metadata.
- Impact note: medium/high security scope; keep modules dependency-free and narrow.

Classification:

missing.

Allowed next action:

Implement P1-A, P1-B, and P1-C in order, refreshing this matrix after each slice.

Forbidden next action:

Do not add a generic executor, second registry/router/projection, or real forge call.

## Next Phase Status Decisions

| Plan Item | Actual Status Finding | Required Status / Next-Action Update |
|-----------|-----------------------|--------------------------------------|
| P1-A | recipe/provenance and exact MPFB rights binding implemented and tested | complete; preserve strict schemas and core-only policy |
| P1-B | bounded MPFB adapter implemented; execution default false and no process launched | complete; preserve sibling and authorization boundary |
| P1-C | GLB structural validator implemented and synthetic fixture tested; downstream loader future-only | complete; keep runtime unexecuted |
| P2-A | selective metadata/projection binding passes; registry remains 65 with quorum 8 | complete; freeze exact candidate |

## Implementation Gate

- [x] Target scope is listed in Current Status Matrix.
- [x] Each target unit has a status.
- [x] Each status has evidence IDs.
- [x] Each target file has relationship count evidence from `file-detail` when applicable; hidden `.p2p` projections are explicitly recorded as unavailable.
- [x] Phase Touch Map lists plan-relevant relationship files that can affect the current phase/slice.
- [x] Phase Touch Map defines touch mode for every plan-relevant relationship unit that may be affected.
- [x] Correct parts are marked preserve-only.
- [x] Partial, missing, wrong, unbound, and fake-or-stub parts have exact next actions.
- [x] Blockers are recorded where authorization forbids actual external execution.
- [x] Next phase status assumptions, next action, and work steps have been updated from this status file.
- [x] Status Refresh Log has an R0 baseline row.
- [x] If implementation has started, affected Current Status Matrix rows have been refreshed from latest evidence.
- [x] If refreshed statuses changed next work, only the stale next-phase status assumptions, next action, or work steps have been updated before the next phase.

## Final P0 Decision

- [ ] P0 actual-status incomplete. Implementation is blocked.
- [ ] P0 complete. Next phase status, next action, or work steps must be updated before implementation.
- [ ] P0 complete. Target scope is preserve-only.
- [ ] P0 complete. Implementation is blocked by missing authority or evidence.

Decision note:

P0 is complete. The malformed requested root was not trusted; fresh canonical
main and exact MPFB upstream identity are bound. The lane may implement only
the three P1 slices in the isolated worktree. External forge execution remains
not authorized, and that is a deliberate boundary rather than a blocker to
static adapter certification.
