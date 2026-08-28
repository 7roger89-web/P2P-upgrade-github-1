# P2P-BG01 Current-Canonical Reconciliation Actual Status

Title: P2P-BG01 Current-Canonical Reconciliation
Date: 2026-08-28
Status: P1 Complete
Companion plan: docs/plans/2026-08-28-p2p-bg01-current-canonical-reconciliation/2026-08-28-p2p-bg01-current-canonical-reconciliation-plan.md
Companion evidence: docs/plans/2026-08-28-p2p-bg01-current-canonical-reconciliation/2026-08-28-p2p-bg01-current-canonical-reconciliation-evidence.md
Companion benchmark: docs/plans/2026-08-28-p2p-bg01-current-canonical-reconciliation/2026-08-28-p2p-bg01-current-canonical-reconciliation-benchmark.md

## Purpose

This file records the current state before BG01 reconciliation implementation.

## Freshness / Refresh Rules

P0 binds the candidate to current canonical 34ece1d1 and tree b3f541df. Later implementation refreshes will append rows rather than erase baseline history.

## Scope

Target scope:

- New isolated candidate from current canonical.
- Old BG01 gateway behavior and its narrow workflow/CLI seam.
- Directly affected fastpath and EFF01 safety evidence.

Out of scope:

- Canonical/remote mutation, promotion, push, deployment, live activation, Anvien, and broad regression.

## Relationship / Impact Evidence

Anvien relationship counts were not collected because the user explicitly prohibited Anvien for this task. Direct source inspection and repository search are the bounded substitute; this is recorded as a validation limitation, not as a claim of low fan-in.

| Unit / File / Surface | File Detail Evidence | Related File Count | Relationship Summary | Impact Note |
|---|---|---:|---|---|
| scripts/p2p_workflow.py | E0-P0A-SRC1 | NOT MEASURED | Current fastpath workflow plus old BG01 integration overlap in this high-fan-in file. | high scope warning |
| .p2p/system/p2p_capabilities/beginner_gateway.py | E0-P0A-SRC2 | 0 in current canonical; old candidate source exists | Missing in current canonical; standalone gateway source in old evidence candidate. | narrow new surface |
| tests/test_p2p_bg01_beginner_gateway.py | E0-P0A-SRC2 | 0 in current canonical; old candidate source exists | Missing in current canonical; focused behavior tests in old evidence candidate. | validation surface |
| tests/test_p2p_lightweight_fastpath.py | E0-P0A-SRC3 | NOT MEASURED | Current canonical fastpath evidence surface. | preserve-only |

## Status Rules

| Status | Meaning | Allowed next action |
|---|---|---|
| correct | already satisfies the required contract | preserve |
| partial | some required behavior exists | edit only missing part |
| missing | required surface does not exist | implement narrowly |
| preserve-only | current behavior is authoritative for this task | inspect and validate only |
| blocked | authority or evidence is insufficient | stop |

## Current Status Matrix

| Unit | Current State | Required State | Status | Relationship Count | Evidence | Next Plan Decision |
|---|---|---|---|---:|---|---|
| Current canonical authority | Clean isolated worktree at 34ece1d1 / b3f541df; official remote main freshly matches 34ece1d1 | exact current canonical source | correct | N/A | E0-P0A-ID1 | use as source |
| Owner canonical checkout | local clone at 28a85bc6 with 1133 dirty lines | untouched historical/Owner checkout | preserve-only | N/A | E0-P0A-ID2 | do not touch |
| Old BG01 candidate | 86def933 / 470aa768; dirty and based on 28a85bc | evidence/source only | preserve-only | N/A | E0-P0A-ID3 | never use as base |
| Current lightweight-fastpath | 82d6bffc -> 34ece1d; current scripts and focused test are present | unchanged behavior | correct | NOT MEASURED | E0-P0A-SRC3 | preserve and test |
| Beginner gateway | added in isolated candidate; pure charter/projection behavior | bounded module | correct | N/A | E0-P0A-SRC2, E1-P1A-SRC1 | preserve |
| Workflow beginner entrypoint | added at one existing-workflow/CLI seam | one existing-workflow seam | bound-correct | NOT MEASURED | E0-P0A-SRC1, E1-P1B-SRC1 | preserve |
| BG01 focused tests | eight focused acceptance cases present and passing | focused behavior coverage | correct | N/A | E0-P0A-SRC2, E1-P1A-TEST1, E1-P1C-TEST1 | preserve |
| Safety/state boundaries | existing Goal Contract, Task State, Control Tower, ledger, C18/C19 | unchanged and reused | correct | NOT MEASURED | E0-P0A-SRC3 | preserve |

## Status Refresh Log

| Refresh | Date | Repo Basis | Changed Scope | Status Changes | Evidence | Next Phase Update |
|---|---|---|---|---|---|---|
| R0 | 2026-08-28 | current canonical and old BG01 evidence | full BG01 reconciliation scope | initial classifications above | E0-P0A-ID1..E0-P0A-SRC3 | implement P1-A then P1-B |
| R1 | 2026-08-28 | isolated candidate at current canonical base after focused validation | gateway, workflow seam, tests, fastpath preservation | missing -> correct/bound-correct; fastpath remains correct | E1-P1A-SRC1..E1-P1C-SAFETY1 | Owner-gate review and closure only |

## Phase Touch Map

| Unit / File / Surface | Plan-Relevant Relationship File | Relationship to Target | Plan Item | Touch Mode | Evidence | Constraint |
|---|---|---|---|---|---|---|
| beginner_gateway.py | orchestration_policy.py | policy dependency | P1-A | edit gateway, preserve policy | E0-P0A-SRC2 | do not duplicate policy |
| test_p2p_bg01_beginner_gateway.py | scripts/p2p_workflow.py | behavior caller | P1-A/P1-C | edit test | E0-P0A-SRC2 | temporary roots only |
| scripts/p2p_workflow.py | tests/test_p2p_lightweight_fastpath.py | shared workflow/test consumer | P1-B/P1-C | surgical edit | E0-P0A-SRC1/E0-P0A-SRC3 | preserve fastpath |
| task_state.py | control_tower_handoff.py | durable recovery surfaces | P1-B | preserve-only | E0-P0A-SRC3 | reuse only |

## Detailed Findings

### Current canonical and overlap

Current state:

The fresh official remote is 34ece1d1 with tree b3f541df. A clean local worktree contains the same exact commit/tree. The remote advance includes 82d6bffc and 34ece1d1 and modifies scripts/p2p_workflow.py, which is also modified by old BG01.

Required state:

Use 34ece1d1 as the new candidate base and preserve lightweight-fastpath code and tests.

Evidence:

- E0-P0A-ID1: exact remote and clean source-worktree identity.
- E0-P0A-SRC1: current workflow and old BG01 integration points.
- E0-P0A-SRC3: current fastpath source/test presence.

Relationship and impact:

- Related file count: not measured by explicit user boundary.
- Relationship summary: high fan-in workflow file shared by C18/C19 fastpath and BG01.
- Impact note: high; limit edits to the existing seams.

Classification:

correct for current canonical; overlap is material but bounded.

Allowed next action:

Create the isolated candidate and implement the smallest integration.

Forbidden next action:

Overwrite current workflow with the old BG01 blob or modify canonical/remote.

### BG01 source

Current state:

The old gateway module and focused tests are complete source/evidence material in 86def933 but absent from current canonical.

Required state:

Port the standalone gateway and tests, then adapt only the workflow seam.

Evidence:

- E0-P0A-SRC2: old gateway/test source and exact old candidate identity.

Relationship and impact:

- Related file count: standalone new files; current canonical has none.
- Relationship summary: gateway imports existing derive_requirement; tests call existing workflow entrypoint.
- Impact note: low for new module, medium at caller integration.

Classification:

missing in current canonical.

Allowed next action:

Implement P1-A.

Forbidden next action:

Treat old commit or approval as the new promotion subject.

## Next Phase Status Decisions

| Plan Item | Actual Status Finding | Required Status / Next-Action Update |
|---|---|---|
| P1-A | gateway and focused tests are missing in current canonical but available in old evidence candidate | implement narrowly |
| P1-B | workflow path is correct for fastpath but missing BG01 entrypoint | update only the missing seam |
| P1-C | fastpath overlap is material | run fastpath tests in addition to BG01 tests |

## Implementation Gate

- [x] Target scope is listed in Current Status Matrix.
- [x] Each target unit has a status.
- [x] Each status has evidence IDs.
- [x] Relationship limitation is explicit because Anvien is forbidden by user.
- [x] Phase Touch Map defines touch mode for relevant units.
- [x] Correct parts are marked preserve-only.
- [x] Missing parts have exact next actions.
- [x] Status Refresh Log has an R0 baseline row.
- [x] Next phase assumptions and work steps are updated from current evidence.

## Final P0 Decision

- [x] P0 complete. Next phase status, next action, or work steps must be updated before implementation.

Decision note:

Proceed from the clean 34ece1d worktree only. The current canonical lightweight-fastpath is authoritative and preserve-only. The old BG01 implementation is source material, not a subject or approval.
