# P2P Game Truyen MPFB Runtime 01 Actual Status

Title: P2P Game Truyen MPFB Runtime 01
Date: 2026-08-30
Status: P1 Complete / P2 Candidate Freeze Pending
Companion plan: `docs/plans/2026-08-30-p2p-game-truyen-mpfb-runtime-01/2026-08-30-p2p-game-truyen-mpfb-runtime-01-plan.md`
Companion evidence: `docs/plans/2026-08-30-p2p-game-truyen-mpfb-runtime-01/2026-08-30-p2p-game-truyen-mpfb-runtime-01-evidence.md`
Companion benchmark: `docs/plans/2026-08-30-p2p-game-truyen-mpfb-runtime-01/2026-08-30-p2p-game-truyen-mpfb-runtime-01-benchmark.md`

## Purpose

This living record separates implementation readiness from actual Blender/MPFB
execution proof. It starts from the exact canonical subject requested by the
user and records all no-run boundaries.

## Freshness / Refresh Rules

P0 records the baseline before implementation. After each implementation slice,
refresh only affected rows and append a status log entry. The pre-existing
untracked promotion Supervisor report is user-owned and must be preserved.

## Scope

Target scope:

- bounded parent/orchestrator;
- dedicated Blender-side MPFB2 entrypoint;
- Windows exact-path outbound network denial lifecycle;
- focused mock/compile/diff validation and exact-subject Supervisor review.

Out of scope:

- Blender/MPFB2 installation or execution;
- Golden Character and GLB creation;
- Game Truyen source or runtime;
- visual proof, promotion, release, or deployment.

## Relationship / Impact Evidence

Anvien graph refresh succeeded, but the hidden `.p2p` source file is not exposed
as a file node by the current index. File-detail and symbol-impact attempts
therefore cannot provide a trustworthy source blast-radius count; unresolved
references from the focused test are not treated as impact evidence.

| Unit / File / Surface | File Detail Evidence | Related File Count | Relationship Summary | Impact Note |
|-----------------------|----------------------|--------------------|----------------------|-------------|
| `.p2p/system/p2p_capabilities/mpfb_adapter.py` | E0-P0A-IMPACT1 | unavailable: hidden source not indexed | parent/orchestrator and focused-test consumer inspected directly | graph coverage limitation; scope warning |
| new Blender entrypoint | N/A, new file | 0 before creation | dedicated Blender `--python` target | editable only in P1-A |
| new Windows isolation helper | N/A, new file | 0 before creation | parent execution security dependency | editable only in P1-B |
| `tests/test_p2p_game_truyen_mpfb_adapter_01.py` | direct source inspection | 1 focused test file | contract tests and mock boundary | validation-only except focused additions |
| exact MPFB2 snapshot | E0-P0A-MPFB1 | inspect-only external source | API/source authority | do not modify or execute |
| Game Truyen | E0-P0A-SMOKE1 | do-not-touch | downstream project | preserve-only |

## Status Rules

| Status | Meaning | Allowed next action |
|--------|---------|---------------------|
| `correct` | Already satisfies the requested boundary. | Preserve. |
| `partial` | Contract exists but required behavior is missing. | Edit only missing behavior. |
| `wrong` | Current behavior conflicts with the requirement. | Replace narrowly and record why. |
| `missing` | Required surface does not exist. | Add only the required surface. |
| `blocked` | Required authority or runtime prerequisite is unavailable. | Record blocker; do not execute. |
| `implementation-ready` | Code contract is ready but live runtime proof is absent. | Freeze/review; do not overclaim. |

## Current Status Matrix

| Unit | Current State | Required State | Status | Relationship Count | Evidence | Next Plan Decision |
|------|---------------|----------------|--------|--------------------|----------|--------------------|
| canonical checkout | detached exact `31647b2f...`, tree `c2154652...` | same exact base before edits | correct | N/A | E0-P0A-GIT1 | preserve subject; do not reset |
| parent adapter | validates recipe/pin, binds dedicated body, and gates spawn behind isolation | parent remains bounded and points to dedicated body | implementation-ready | unavailable from graph | E0-P0A-IMPACT1, E1-P1C-TEST1..TEST4 | freeze/review only |
| dedicated Blender body | strict bounded MPFB2 body added; not executed | strict bounded MPFB2 body | implementation-ready | new file | E1-P1A-SRC1..TEST3 | freeze/review only; Blender remains NOT_RUN |
| MPFB pin | source snapshot exact 2.0.17 SHA/tree | exact pin verified by parent and body | correct | inspect-only | E0-P0A-MPFB1 | preserve; revalidate in P1-A |
| network denial | exact-path Windows Defender Firewall lifecycle added; live host rule not created | exact-path OS/process enforcement before spawn | implementation-ready/live-proof-pending | unavailable from graph | E1-P1B-TEST1..TEST4, E1-P1C-TEST3 | downstream Administrator-bound execution only |
| output allowlist | parent preflights empty root and postflights exactly GLB + sidecar; body enforces same | preflight and postflight exact two outputs | implementation-ready | unavailable from graph | E1-P1A-TEST2, E1-P1C-TEST1..TEST2 | freeze/review only |
| provenance | dedicated body binds recipe and GLB hashes and writes one validated sidecar | body writes exactly one bound sidecar | implementation-ready | unavailable from graph | E1-P1A-TEST2..TEST3 | freeze/review only |
| `CORE_CC0_ONLY` | existing recipe/provenance contract | body rejects non-core assets by default | correct/needs recheck | unavailable from graph | E0-P0A-SRC1 | preserve and revalidate |
| Blender host | no executable found in smoke | downstream compatible Blender host | blocked/out of scope | N/A | E0-P0A-SMOKE1 | remain NOT_RUN |
| Game Truyen | untouched by smoke | untouched in this workstream | correct/preserve-only | N/A | E0-P0A-SMOKE1 | do not touch |

## Status Refresh Log

| Refresh | Date | Repo Basis | Changed Scope | Status Changes | Evidence | Next Phase Update |
|---------|------|------------|---------------|----------------|----------|-------------------|
| R0 | 2026-08-30 | exact base checkout and smoke receipt | two requested blockers | initial correct/partial/missing/wrong/blocked classifications | E0-P0A-GIT1..E0-P0A-WORKFLOW1 | P1-A/P1-B/P1-C implement only missing pieces |
| R1 | 2026-08-30 | implementation worktree after focused checks | dedicated body, Windows isolation, parent binding | missing/wrong/partial -> implementation-ready; live execution remains unproven | E1-P1A-SRC1..E1-P1C-TEST4, E2-P2A-TEST1..TEST3 | freeze exact candidate and obtain fresh Supervisor |

## Phase Touch Map

| Unit / File / Surface | Plan-Relevant Relationship File | Relationship to Target | Plan Item | Touch Mode | Evidence | Constraint |
|-----------------------|---------------------------------|------------------------|-----------|------------|----------|------------|
| parent adapter | focused test | consumer/validation | P1-C | edit | E0-P0A-SRC1 | preserve public contract and no-spawn defaults |
| parent adapter | new Blender entrypoint | source-of-truth/child process target | P1-A/P1-C | edit/bind | E0-P0A-SRC1 | exact path only |
| parent adapter | new isolation helper | security dependency | P1-B/P1-C | bind | E0-P0A-SRC1 | setup before spawn; cleanup always |
| focused tests | parent and helpers | validation | P1-A/P1-B/P1-C | edit focused only | E0-P0A-IMPACT1 | no broad suite |
| exact MPFB2 source | none | external API authority | P1-A | inspect-only | E0-P0A-MPFB1, E0-P0A-API1 | no install/edit/execute |
| Game Truyen | downstream project | protected project | all | do-not-touch | E0-P0A-SMOKE1 | zero mutation |

## Detailed Findings

### Parent adapter

Current state:

The parent already validates bounded workspace-relative paths, recipe/job
identity, exact MPFB provisioning pin/root hash, minimal environment, shell-free
argv, timeout, process-tree termination, output naming, and GLB/provenance
validation. Its Blender target is itself, which is not an executable Blender
body, and its network deny is only an argument/constant.

Required state:

```text
parent -> exact dedicated Blender entrypoint
parent -> setup verified Windows outbound block -> Blender spawn
parent -> cleanup -> output/provenance validation
```

Evidence:

- E0-P0A-SRC1
- E0-P0A-SMOKE1

Classification: `partial`.

Allowed next action: edit only P1-C integration points.

Forbidden next action: remove authorization, weaken `NETWORK_POLICY=DENY`, or
spawn Blender during this workstream.

### Dedicated Blender body

Current state: missing.

Required state: a strict Blender-side script that imports the verified MPFB2
package, calls only supported APIs, creates the parametric human, applies the
actual built-in GameEngine-compatible rig and weights, exports one embedded GLB,
and writes one provenance sidecar.

Evidence:

- E0-P0A-API1
- E0-P0A-MPFB1

Classification: `missing`.

Allowed next action: add P1-A and validate only with mocks/static checks.

Forbidden next action: invent API names or run Blender/MPFB2.

### Windows network denial

Current state: declarative only.

Required state: an exact-path Windows Defender Firewall outbound program rule
created and verified before process spawn, with Administrator privilege required,
collision rejection, and deterministic cleanup on every execution path.

Evidence:

- E0-P0A-SMOKE1
- E0-P0A-SRC1

Classification: `wrong`.

Allowed next action: add P1-B/P1-C and mock the command lifecycle.

Forbidden next action: claim a proxy, flag, or environment variable is OS
enforcement; enable a live host rule during validation.

## Next Phase Status Decisions

| Plan Item | Actual Status Finding | Required Status / Next-Action Update |
|-----------|-----------------------|--------------------------------------|
| P1-A | dedicated body implemented from inspected MPFB2 API; parser, pin, asset, output, and provenance tests pass | mark implementation-ready; keep execution NOT_RUN |
| P1-B | exact-path Windows Firewall lifecycle implemented with Administrator requirement, verification, and cleanup tests | mark implementation-ready/live-proof-pending; no live rule during validation |
| P1-C | parent binds dedicated entrypoint and isolation context before Popen; no-spawn and teardown tests pass | mark implementation-ready |
| P2-A | focused validation passed; candidate freeze and exact-subject review remain | run final change detection, freeze exact subject, request Supervisor |

## Implementation Gate

- [x] Target scope is listed in Current Status Matrix.
- [x] Each target unit has a status and exact evidence IDs.
- [x] Relationship-count limitation is recorded rather than inferred away.
- [x] Phase Touch Map defines preserve-only, inspect-only, edit, and do-not-touch surfaces.
- [x] Correct parts are preserve-only.
- [x] Missing/wrong/partial parts have exact next actions.
- [x] Blockers are recorded, including Blender downstream.
- [x] Status Refresh Log has an R0 baseline row.
- [x] P0 artifacts and downstream plan decision are complete before implementation.

## Final P0 Decision

- [ ] P0 actual-status incomplete. Implementation is blocked.
- [ ] P0 complete. Next phase can proceed unchanged.
- [ ] P0 complete. Next phase status, next action, or work steps must be updated before implementation.
- [ ] P0 complete. Target scope is preserve-only.
- [ ] P0 complete. Target scope is blocked by missing authority or evidence.

Decision note:

P0 is complete. The exact checkout and MPFB pin are verified, the two requested
implementation gaps are concrete, and all downstream execution/visual/Game
Truyen work remains explicitly blocked or out of scope. P1 may proceed with
static and mocked validation only.

## P1 Completion Decision

- [ ] P1 blocked by a failed implementation gate.
- [x] P1 implementation-ready; live Blender/MPFB2 execution and live firewall
  enforcement remain unproven and downstream.
- [ ] P1 actual runtime proven.

Decision note:

The dedicated entrypoint now uses only APIs inspected in the exact MPFB2
2.0.17 source. The parent verifies the six-key provisioning manifest,
including the `core_assets` hash/license map, and the child enforces the same
pin and asset policy. Windows denial is represented by an exact executable
path-bound Defender Firewall outbound rule with verification and deterministic
cleanup; inability to establish it blocks process spawn. All validation was
mocked/static. No Blender or MPFB2 process ran, no GLB was created, and no
Game Truyen or host firewall state was changed.
