# P2P-CT01 R05 Durable Control Tower Candidate Convergence Actual Status

Title: P2P-CT01 R05 Durable Control Tower Candidate Convergence
Date: 2026-08-27
Status: P0 Complete
Companion plan: docs/plans/2026-08-27-p2p-ct01-r05-candidate-convergence/2026-08-27-p2p-ct01-r05-candidate-convergence-plan.md
Companion evidence: docs/plans/2026-08-27-p2p-ct01-r05-candidate-convergence/2026-08-27-p2p-ct01-r05-candidate-convergence-evidence.md
Companion benchmark: docs/plans/2026-08-27-p2p-ct01-r05-candidate-convergence/2026-08-27-p2p-ct01-r05-candidate-convergence-benchmark.md

## Purpose

This file records the real current state before implementation in the R05
candidate worktree. It deliberately separates the functional A subject from
the governance B subject and from the historical broken Locus B root.

## Freshness / Refresh Rules

P0 is the baseline before implementation. After each R05 slice, refresh only
the affected rows and append a Status Refresh Log entry. Detailed command
outputs remain in the companion evidence ledger.

## Scope

Target scope:

- Valid authority repository and fresh canonical identity.
- Subject A functional superset and Subject B governance reconciliation.
- One A-derived candidate under the valid repository .tmp directory.

Out of scope:

- Historical broken Locus B repair or execution.
- Promotion, merge, release, deployment, live host, or approval action.
- P8D0A, full council, adaptive router, game/PDF/voice runtime, and inherited
  baseline failure repair.

## Relationship / Impact Evidence

| Unit / File / Surface | File Detail Evidence | Related File Count | Relationship Summary | Impact Note |
|---|---|---:|---|---|
| scripts/p2p_control_tower.py | E0-P0A-GR1 | 3 local relationships; 0 inbound/outbound in Anvien context | A CLI imports the handoff module and exposes start/snapshot/ingest/next | high scope warning; preserve source and validate CLI |
| .p2p/system/p2p_capabilities/control_tower_handoff.py | E0-P0A-GR2 | direct inspection required; hidden file not indexed by Anvien | A source is the durable session/packet/ledger/TaskState surface; B/base have the shorter source | high scope warning; no source edit in Case B |
| scripts/p2p_governance.py | E0-P0A-GR3 | high-risk graph context; existing governance consumers | Existing runtime lock generator and verifier | high scope warning; use existing mechanism only |
| governance/drift-policy.json | E0-P0A-CONFIG1 | configuration relationship, not a code symbol | B adds exactly two protected paths | narrow edit |
| governance/runtime-manifest.lock.json | E0-P0A-CONFIG2 | generated governance output | A lock is stale for A's added protected files; B lock proves hidden module only | regenerate after all intended files |
| tests/test_p2p_control_tower_session_handoff.py | E0-P0A-TEST1 | existing A/base test surface | attachment, rotation, owner-gate, recursive and fail-closed behavior | preserve and run in candidate |
| tests/test_p2p_control_tower_durable.py | E0-P0A-TEST2 | A-only test surface | durable parser, replay, idempotency, CLI, TaskState and next-safe behavior | preserve and run in candidate |
| tests/test_p2p_ct01_governance_lock_reconciliation.py | E0-P0A-TEST3 | B-only test surface | governance binding and fail-closed lock tests | missing in A; port into candidate |

## Status Rules

| Status | Meaning | Allowed next action |
|---|---|---|
| correct | Already behaves as required. | Preserve and prove. |
| partial | Some required behavior exists, but gaps remain. | Edit only the missing part. |
| wrong | Current behavior or contract is incorrect. | Replace the exact incorrect part. |
| missing | Required behavior or proof does not exist. | Add only the missing piece. |
| unbound | Surface exists but is not wired to the real source or contract. | Bind to the real source only. |
| fake-or-stub | Prototype, demo, mock, fallback, or placeholder is used as real behavior. | Remove or replace with truthful state. |
| blocked | Source, authority, contract, or required evidence is unclear. | Stop until resolved. |

## Current Status Matrix

| Unit | Current State | Required State | Status | Relationship Count | Evidence | Next Plan Decision |
|---|---|---|---|---:|---|---|
| Canonical authority | origin main resolves to 28a3ecd9c04d36511269e44c384bff6e11677b93 with tree cae63e055edd164fbd969f6dbae0d992a4d0efed | exact fresh SHA/tree and origin | correct | N/A | E0-P0A-AUTH1..E0-P0A-AUTH3 | preserve |
| Candidate isolation | new worktree at the valid repo .tmp path, branch codex/p2p-ct01-r05-candidate-convergence-7c3d1a92, clean before edits | isolated A-derived worktree | correct | N/A | E0-P0A-ISO1..E0-P0A-ISO2 | preserve |
| Subject A durable functionality | A has the functional source, CLI, durable test, existing-ledger reuse, TaskState, replay, attachment, rotation, and boundary tests | all justified A functionality | correct | see relationship table | E0-P0A-A1..E0-P0A-A6 | preserve |
| Subject B governance binding | A policy lacks the two exact hidden-module protected entries that B adds | exact package and installed entries, no broad whitelist | partial | configuration | E0-P0A-B1..E0-P0A-B3 | edit P1-A |
| Subject B governance test | test exists in B only and has not been run in B | candidate-local test proves exact binding and fail-closed lock | missing | B-only surface | E0-P0A-B4 | edit P1-B |
| Runtime lock | A lock is stale for A's added protected source/CLI/test-related state; B lock covers the hidden module but not A functionality | one generated lock covering the final candidate | partial | generated output | E0-P0A-L1..E0-P0A-L3 | regenerate P1-C |
| A/B Git relation | merge base 57c4cfc2fd3bbad2c52e40b66be730aeb7ff7f47; left/right counts 3/3; neither ancestor | exact relation recorded | correct | N/A | E0-P0A-REL1..E0-P0A-REL3 | Case B minimal convergence |
| Functional conflict | B removes A CLI/source/durable test and adds only governance plan/test/policy/lock | preserve A and add exact B governance | correct | 19 A/B changed paths | E0-P0A-MAT1..E0-P0A-MAT4 | no conflict decision |
| Existing authority path | existing execution ledger and existing governance verifier are present | reuse only existing authority | correct | existing consumers | E0-P0A-AUTH4..E0-P0A-AUTH5 | preserve |
| Approval/promotion boundary | A source explicitly rejects approval/credential inheritance and does not promote | READY_FOR_OWNER_GATE distinct from PROMOTED | correct | boundary surface | E0-P0A-GATE1..E0-P0A-GATE3 | preserve |
| Historical Locus B | broken/non-Git root with no authority | evidence-only, no execution or repair | blocked for action, preserve-only for evidence | N/A | E0-P0A-LOCUS1..E0-P0A-LOCUS3 | do not touch |
| Dedicated handoff SPEC | dedicated named SPEC absent in valid repo | user contract plus existing handoff/governance specs are the current basis | partial, not blocking | documentation | E0-P0A-SPEC1..E0-P0A-SPEC3 | record, do not invent |
| EOL/stat-cache noise | canonical checkout reports 1127 status rows, but raw and semantic content path diffs are empty | do not treat EOL noise as content drift | correct | N/A | E0-P0A-NOISE1..E0-P0A-NOISE2 | preserve |
| Anvien graph | refreshed successfully; hidden module is not indexed, CLI is indexed and stale=false | graph evidence where available plus direct inspection where not | partial | graph-dependent | E0-P0A-GRAPH1..E0-P0A-GRAPH4 | record limitation |

## Status Refresh Log

| Refresh | Date | Repo Basis | Changed Scope | Status Changes | Evidence | Next Phase Update |
|---|---|---|---|---|---|---|
| R0 | 2026-08-27 | fresh A-derived R05 worktree before implementation | all P2P-CT01 R05 surfaces | initial classifications above | E0-P0A-AUTH1..E0-P0A-NOISE2 | P0 complete; proceed with P1-A, P1-B, P1-C |

## Phase Touch Map

| Unit / File / Surface | Plan-Relevant Relationship File | Relationship to Target | Plan Item | Touch Mode | Evidence | Constraint |
|---|---|---|---|---|---|---|
| governance/drift-policy.json | scripts/p2p_governance.py | governance consumer | P1-A | edit | E0-P0A-GR3, E0-P0A-B1 | add two exact paths only |
| governance/runtime-manifest.lock.json | scripts/p2p_governance.py | generated output | P1-C | regenerate | E0-P0A-L1..E0-P0A-L3 | existing generator only |
| .p2p/system/p2p_capabilities/control_tower_handoff.py | scripts/p2p_control_tower.py; tests | source-of-truth/consumer/test | P1-C/P2-A | preserve-only | E0-P0A-GR1..E0-P0A-A6 | no source mutation |
| tests/test_p2p_control_tower_session_handoff.py | handoff module | behavior test | P2-A | validate-only | E0-P0A-TEST1 | run in candidate only |
| tests/test_p2p_control_tower_durable.py | handoff module and CLI | behavior test | P2-A | validate-only | E0-P0A-TEST2 | run in candidate only |
| tests/test_p2p_ct01_governance_lock_reconciliation.py | p2p_governance.py | behavior test | P1-B/P2-A | edit/validate | E0-P0A-TEST3 | port exact B proof; do not run B |
| historical Locus B root | none | evidence-only | all | do-not-touch | E0-P0A-LOCUS1..E0-P0A-LOCUS3 | no Git repair or tests |

## Detailed Findings

### Subject A functional surface

Current state:

Subject A is the functional superset at SHA f479cc97b31f62f0d006e8465b26ef568e242998,
tree edab113b058478fee4fdd253eec254c18b1e342b. It includes the durable handoff
source, CLI, durable test, existing execution-ledger reuse, replay/idempotency,
TaskState and next-safe-task, attachment/rotation/recursive continuation, and
Owner Gate/non-promotion boundaries.

Required state:

Preserve all justified A functionality in the final candidate.

Evidence:

- E0-P0A-A1: exact A SHA/tree and parent.
- E0-P0A-A2: A-only source/CLI/durable-test diff versus the merge base.
- E0-P0A-A3: A durable test inventory.
- E0-P0A-A4: existing session-handoff test inventory.
- E0-P0A-A5: source boundary/nonclaim inspection.
- E0-P0A-A6: A reported focused/attachment/rotation/CLI evidence, to be
  freshly re-run in the candidate.

Relationship and impact:

- Related file count: CLI has 3 local relationships and no indexed inbound or
  outbound relationships; the hidden module requires direct inspection.
- Relationship summary: one existing handoff source consumed by CLI/tests and
  existing ledger/governance helpers.
- Impact note: high scope warning; source is preserve-only in Case B.

Classification:

correct

Allowed next action:

Preserve and freshly prove; do not redesign.

Forbidden next action:

Do not replace with B, copy a whole worktree, or add a second authority path.

### Subject B governance reconciliation

Current state:

Subject B at SHA 9086ca4be9874fb256195d26655022907665208f, tree
91d1b467483fdb65b87d9459d3792a5253cdae68, adds exactly the hidden-module
protected path to package and installed policy arrays and carries a focused
governance test. B does not contain A's durable source, CLI, or durable test.

Required state:

Port only the exact policy entries and the focused governance proof into the
A-derived candidate, then regenerate the existing lock.

Evidence:

- E0-P0A-B1: exact B policy diff versus A.
- E0-P0A-B2: B test source inventory and five proof cases.
- E0-P0A-B3: B lock includes the hidden module hash and exact guide hash.
- E0-P0A-B4: A/B path diff proves A functionality is absent in B.

Relationship and impact:

- Related file count: configuration and generated-output paths; no new router,
  registry, or truth store.
- Relationship summary: policy controls the existing runtime-manifest generator
  and verifier.
- Impact note: narrow governance/configuration change.

Classification:

partial

Allowed next action:

Add exact policy entries, port test, regenerate lock.

Forbidden next action:

Do not wholesale-copy B plans or remove A functionality.

### Historical Locus B

Current state:

The original user cwd is a broken/non-Git historical root. It has no authority
for this candidate and is evidence-only.

Required state:

No mutation, no repair, no test execution, and no authority claim.

Evidence:

- E0-P0A-LOCUS1: root identity and broken Git state.
- E0-P0A-LOCUS2: prior evidence forbidding repair/copy/initialization.
- E0-P0A-LOCUS3: valid canonical repository and isolated worktree paths.

Relationship and impact:

- Related file count: N/A.
- Relationship summary: no authority relationship to candidate.
- Impact note: blocked for action; preserve-only.

Classification:

blocked for action / preserve-only

Allowed next action:

Mention as non-authority in the report and handoff.

Forbidden next action:

Do not repair, initialize, replace, clean, copy .git, run B tests, or use its
files as canonical truth.

## Next Phase Status Decisions

| Plan Item | Actual Status Finding | Required Status / Next-Action Update |
|---|---|---|
| P1-A | A is missing the exact two B protected-path entries | keep; edit only those entries |
| P1-B | B proof is absent in A | keep; port narrowly and execute only in candidate |
| P1-C | A lock is stale for the A-derived final tree | keep; regenerate with existing command |
| P2-A | A functionality is present but fresh candidate proof is pending | keep; run focused suite after P1-C |
| P2-B | baseline attribution is pending | keep; compare without repairing |
| P2-C | implementation identity is not sealed yet | keep; seal only after P1/P2 gates |

## Implementation Gate

- [x] Target scope is listed in Current Status Matrix.
- [x] Each target unit has a status.
- [x] Each status has evidence IDs.
- [x] Target files have relationship-count evidence where graph evidence applies.
- [x] Phase Touch Map lists relevant relationship files and touch modes.
- [x] Correct parts are preserve-only.
- [x] Partial/missing/blocked parts have exact next actions.
- [x] Historical Locus B blocker is recorded.
- [x] Next-phase decisions are updated from P0 evidence.
- [x] Status Refresh Log has an R0 baseline row.
- [ ] Post-implementation rows will be refreshed after each slice.

## Final P0 Decision

- [ ] P0 actual-status incomplete. Implementation is blocked.
- [x] P0 complete. Next phase status, next action, and work steps are explicit.
- [x] P0 complete. Correct Subject A functionality is preserve-only.
- [ ] P0 complete. Implementation is blocked by missing authority or evidence.

Decision note:

P0 is complete for Case B minimal convergence. The user-supplied contract,
existing handoff/governance specs, exact Git evidence, and the A/B source diffs
are sufficient authority to make the narrow candidate change. Fresh proof still
remains required before any Owner Gate recommendation.
