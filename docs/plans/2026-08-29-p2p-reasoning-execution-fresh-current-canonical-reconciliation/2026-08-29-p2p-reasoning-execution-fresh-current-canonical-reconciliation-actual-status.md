# P2P Reasoning/Execution Fresh Current-Canonical Reconciliation Actual Status

Title: P2P Reasoning/Execution Fresh Current-Canonical Reconciliation
Date: 2026-08-29
Status: P0 Complete
Companion plan: `docs/plans/2026-08-29-p2p-reasoning-execution-fresh-current-canonical-reconciliation/2026-08-29-p2p-reasoning-execution-fresh-current-canonical-reconciliation-plan.md`
Companion evidence: `docs/plans/2026-08-29-p2p-reasoning-execution-fresh-current-canonical-reconciliation/2026-08-29-p2p-reasoning-execution-fresh-current-canonical-reconciliation-evidence.md`
Companion benchmark: `docs/plans/2026-08-29-p2p-reasoning-execution-fresh-current-canonical-reconciliation/2026-08-29-p2p-reasoning-execution-fresh-current-canonical-reconciliation-benchmark.md`

## Purpose

This file records the real current state before implementation. P0 binds the
newest official main, the reviewed candidate, the exact overlap result, and the
preserve-only later 01D projection surfaces. It does not replace the evidence
ledger.

## Freshness / Refresh Rules

P0 is the baseline before source mutation. After each implementation slice,
refresh affected rows and append a Status Refresh Log row with exact evidence
IDs. If official main changes before mutation, stop and rebind the whole P0
authority set.

## Scope

Target scope:

- Carry the already-reviewed Reasoning/Execution source/test delta from
  `e1410fa` onto the newest official main and stop at an unpromoted Owner-gate
  candidate.

Out of scope:

- 01D projection redesign, broad regression, Anvien, MCP, Council, providers,
  live external execution, remote push, promotion, release, deployment, and
  protected worktree repair.

## Relationship / Impact Evidence

Graph `file-detail` and impact commands were not run because the user explicitly
prohibited Anvien. Exact Git path-set comparison and source/spec inspection are
the authorized substitutes.

| Unit / File / Surface | File Detail Evidence | Related File Count | Relationship Summary | Impact Note |
|-----------------------|----------------------|--------------------|----------------------|-------------|
| Official current main | `E0-P0A-REMOTE1`, `E0-P0A-CURRENT1` | not measured; Anvien prohibited | fresh remote and clean isolated source at `82d8a976/ac2627b0` | high preserve boundary |
| Reviewed candidate | `E0-P0A-OLD1` | not measured; Anvien prohibited | proven Reasoning/Execution delta at `e1410fa/5cccc26` | medium port boundary |
| Exact overlap | `E0-P0A-OVERLAP1`, `E0-P0A-OVERLAP2` | exact path inventory | zero shared paths and zero production/test overlap | low; no conflict |
| Later 01D projection work | `E0-P0A-LATE1` | 9 current-main paths; graph count not measured | project context/materialization/pin/spec/test contract | critical preserve-only |
| Existing control plane | `E0-P0A-SPEC1` | not measured; Anvien prohibited | existing registry/router/verifier/runtime/governance | critical no-duplicate boundary |

## Status Rules

| Status | Meaning | Allowed next action |
|--------|---------|---------------------|
| `correct` | Already behaves as required. | Preserve or reuse evidence. |
| `partial` | Some required behavior exists, but gaps remain. | Change only missing parts. |
| `wrong` | Current behavior or contract conflicts. | Stop and resolve exact conflict. |
| `missing` | Required behavior does not exist. | Implement the missing piece only. |
| `unbound` | Surface exists but is not bound to the real source. | Bind to the real source only. |
| `fake-or-stub` | Placeholder or marketing state is presented as real. | Remove or replace truthfully. |
| `blocked` | Authority or evidence is unclear. | Stop until resolved. |

## Current Status Matrix

| Unit | Current State | Required State | Status | Relationship Count | Evidence | Next Plan Decision |
|------|---------------|----------------|--------|--------------------|----------|--------------------|
| Official main | remote/current clone resolve to `82d8a976/ac2627b0` and clone is clean | exact fresh canonical ancestor | correct | not measured; Anvien prohibited | `E0-P0A-REMOTE1`, `E0-P0A-CURRENT1` | create candidate branch from exact main |
| Reviewed Reasoning/Execution candidate | `e1410fa/5cccc26`, based on `1c84bc4` | same 11-file implementation semantics on newest main | correct/reviewed | not measured; Anvien prohibited | `E0-P0A-OLD1` | port only reviewed delta in P1-A |
| Old-base/current-main overlap | empty; current main has 9 later 01D paths | no source/test conflict | correct | exact path inventory | `E0-P0A-OVERLAP1`, `E0-P0A-OVERLAP2` | classification `NONE`; no conflict resolution |
| Later 01D projection work | current source/spec/test files exist on fresh main | preserve exactly; current main wins | correct | 9 paths; graph count not measured | `E0-P0A-LATE1` | preserve-only; never edit in P1 |
| Reasoning/Execution source family | reviewed source/test delta exists only in old candidate | port 11 coherent paths without rebuilding | reviewed/unported | 11 candidate paths; graph count not measured | `E0-P0A-OLD1`, `E0-P0A-SPEC1` | edit only P1-A |
| Control-plane/Owner boundary | existing registry/router/verifier/runtime and Owner governance | no duplicate control plane or permission widening | correct | not measured; Anvien prohibited | `E0-P0A-SPEC1`, `E0-P0A-BOUNDARY1` | preserve; validate in P1/P2 |

## Status Refresh Log

| Refresh | Date | Repo Basis | Changed Scope | Status Changes | Evidence | Next Phase Update |
|---------|------|------------|----------------|----------------|----------|-------------------|
| R0 | 2026-08-29 | fresh remote and isolated current-main source before mutation | authority, old candidate, overlap, 01D later work | current main correct; candidate reviewed; overlap none; implementation unported | `E0-P0A-REMOTE1..E0-P0A-TOOL1` | P1-A may port exact 11-file delta; P1-B runs focused ceiling |

## Phase Touch Map

| Unit / File / Surface | Plan-Relevant Relationship File | Relationship to Target | Plan Item | Touch Mode | Evidence | Constraint |
|-----------------------|---------------------------------|------------------------|-----------|------------|----------|------------|
| Reasoning/Execution runtime | `.p2p/system/p2p_capabilities/backend_contract.py` and sibling role/bridge/receipt/verifier files | source contract and consumers | P1-A | edit | `E0-P0A-OLD1`, `E0-P0A-SPEC1` | exact reviewed delta only |
| Direct/preservation tests | `tests/test_p2p_reasoning_execution_decoupling.py`, `tests/test_p2p_c34_real_backend_contract.py` | behavior/preservation tests | P1-A/P1-B | edit | `E0-P0A-OLD1` | focused ceiling only |
| Later 01D source/spec/test | `project_context.py`, `project_materialization.py`, `project_pin.py`, projection SPEC/test | later canonical contract/consumers | P1-A/P2 | preserve-only | `E0-P0A-LATE1` | current main wins; do not touch |
| Decision/evidence docs | current plan/log/report surfaces | audit evidence | P1-B/P2 | edit | `E0-P0A-OVERLAP1` | append/update only; no source semantics |

## Detailed Findings

### Fresh authority and overlap

Current state:

Fresh official remote and isolated current main resolve to `82d8a976` / tree
`ac2627b0`. The old candidate is `e1410fa` / tree `5cccc26` from old base
`1c84bc4`. The old candidate changed 18 paths; current main changed 9 paths
from the same base; their intersection is empty.

Required state:

```text
Start one candidate from 82d8a976 and port only the 11 reviewed source/test paths.
```

Evidence:

- `E0-P0A-REMOTE1`: fresh official remote authority.
- `E0-P0A-CURRENT1`: clean isolated current-main identity.
- `E0-P0A-OLD1`: old reviewed candidate/base identity.
- `E0-P0A-OVERLAP1..2`: exact empty overlap and classification `NONE`.

Relationship and impact:

- Related file count: not measured; Anvien explicitly prohibited.
- Relationship summary: no shared path; no semantic conflict is indicated by
  path topology.
- Impact note: high for identity, low for conflict resolution.

Classification:

`correct` and ready for P1-A.

Allowed next action:

Create/use the fresh-main branch and apply the exact reviewed 11-file delta.

Forbidden next action:

Do not use stale `1c84bc4` as candidate base, cherry-pick old history, or modify
current 01D source/spec/test files.

### Later canonical 01D boundary

Current state:

Current main adds project context, materialization, project pin, projection SPEC,
plan/evidence/status, and projection tests. The projection SPEC explicitly
retains the existing capability registry/router and says projection metadata,
stale/marketing state, and `NOT_INSTALLED` do not grant executable authority.

Required state:

```text
NEWER_CANONICAL_WORK_PRESERVED=YES
```

Evidence:

- `E0-P0A-LATE1`: nine exact current-main paths are outside the old candidate
  delta and remain preserve-only.
- `E0-P0A-SPEC1`: current projection contract preserves existing routing,
  readiness, permission, and Owner-gate boundaries.

Relationship and impact:

- Related file count: 9 exact later paths; graph count not measured.
- Relationship summary: independent project identity/materialization lifecycle,
  no shared source/test path with Reasoning/Execution delta.
- Impact note: critical if touched; no touch is authorized.

Classification:

`correct` and preserve-only.

Allowed next action:

Carry these exact current-main blobs forward and verify them after porting.

Forbidden next action:

Do not rollback 01D files or introduce a second capability/permission/control
plane to connect the two contracts.

## Next Phase Status Decisions

| Plan Item | Actual Status Finding | Required Status / Next-Action Update |
|-----------|-----------------------|--------------------------------------|
| P1-A | The old reviewed 11-file source/test delta has zero current-main overlap and current main is clean/fresh. | proceed with exact port only |
| P1-B | Focused evidence has not yet been run on the new lineage. | run direct/affected ceiling, compile, parse, diff |
| P2-A | No new-candidate Supervisor evidence exists yet. | require one focused independent review |

## Implementation Gate

- [x] Target scope is listed in Current Status Matrix.
- [x] Each target unit has a status.
- [x] Each status has evidence IDs.
- [x] Relationship count evidence is recorded as not measured where Anvien is
  explicitly prohibited.
- [x] Phase Touch Map lists plan-relevant relationship files and touch modes.
- [x] Correct parts are marked preserve-only.
- [x] Partial/missing/wrong/unbound/fake-or-stub parts have exact next actions.
- [x] Blockers are recorded: none; Anvien is an explicit user prohibition, not a
  task blocker.
- [x] Next-phase assumptions and work steps reflect the empty overlap result.
- [x] Status Refresh Log has an R0 baseline row.
- [x] No source implementation was edited before this P0 gate.

## Final P0 Decision

Choose one:

- [ ] P0 actual-status incomplete. Implementation is blocked.
- [x] P0 complete. Next phase can proceed unchanged.
- [ ] P0 complete. Next phase status, next action, or work steps must be updated
  before implementation.
- [ ] P0 complete. Target scope is preserve-only.
- [ ] P0 complete. Implementation is blocked by missing authority or evidence.

Decision note:

Fresh official main is bound at `82d8a976/ac2627b0`; old candidate identity is
bound at `e1410fa/5cccc26`; old-base/current-main path overlap is empty and the
production/test overlap is zero. P1 may carry forward only the reviewed
Reasoning/Execution source/test delta. Current 01D projection work is
preserve-only. No Anvien/MCP/live/promotion action is permitted.
