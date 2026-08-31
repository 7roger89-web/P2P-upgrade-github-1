# P2P APPROVED IDEAS BACKLOG

Status: `DURABLE_BACKLOG_ONLY`

Purpose: preserve Owner-approved P2P improvement ideas so they are not lost across chats, compaction, account/session rotation, or Control Tower rotation.

This file is **not** an active implementation plan, runtime authority, release authority, or permission to mutate code. It must not override canonical specs, governance, Task State, the P2P Operations Notebook, or an exact active workstream. Items here become implementation work only when Control Tower explicitly opens a bounded workstream for them.

## Retrieval rule

- Default task retrieval should not load this file unless the task is planning the next P2P improvement, reconciling the approved backlog, or explicitly references one of the IDs below.
- An entry marked `PENDING` is a durable promise to revisit, not an instruction to execute immediately.
- When an entry is implemented, Control Tower must verify the exact PR head/tree and change the entry to `VERIFIED` or replace it with a pointer to the canonical implemented artifact.
- Do not create parallel backlogs for the same ideas.

## Execution trigger

Current priority remains the already-active P2P/img2threejs completion chain. After the current bounded workstream reaches its safe terminal point, Control Tower must inspect this backlog before inventing unrelated new platform work.

---

## CONTEXT_HYGIENE_01 — Context Hygiene and Plan Lifecycle

`STATUS=PENDING`

Owner decision: accepted for future P2P development.

### Problem

Long-lived repositories and long AI sessions accumulate obsolete plans, specs, assumptions, failed approaches, and historical evidence. Semantic retrieval can select an old but textually relevant plan, and session compaction can preserve stale assumptions or lose important current details. File timestamps alone do not establish authority.

### Approved direction

Use authority-aware lifecycle and retrieval instead of blind deletion or moving all planning to another service.

```text
ACTIVE_TASK_PLANS        -> GitHub Issues / active workstream state
CANONICAL_SPECS          -> repository canonical surfaces
EVIDENCE                 -> durable, non-instructional evidence
HISTORICAL/SUPERSEDED    -> retained for audit, excluded from default retrieval
```

### Required laws

1. `SESSION_CONTEXT != AUTHORITY`.
2. Default retrieval is `ACTIVE_ONLY_RETRIEVAL` plus required canonical specs.
3. Historical/superseded plans are not loaded by default; history is opt-in when the task actually needs it.
4. Active task identity must bind to the durable workstream and exact Git/GitHub subject where applicable (`repository + workstream + SHA/tree/PR`).
5. After merge/closure, an active plan loses active authority.
6. Durable knowledge discovered by a completed task should be synthesized into the correct canonical spec/governance surface; the old task plan remains historical evidence.
7. Evidence is durable but does not become instruction authority merely because it is relevant text.
8. `NO_BLIND_DELETE_AFTER_MERGE`: do not delete useful history solely to make the repo look clean.
9. New execution sessions should load minimum relevant active context rather than replaying full old chat history.
10. Worktree/parallel-agent execution is allowed only for dependency-independent, low-conflict work; worktrees solve filesystem isolation, not semantic dependency.

### Preferred implementation constraint

Use existing GitHub Issues + PRs + P2P Task State/router/governance surfaces first.

```text
LINEAR_REQUIRED=NO
NEW_PROJECT_MANAGER_REQUIRED=NO
NEW_DATABASE_REQUIRED=NO
NEW_DAEMON_REQUIRED=NO
```

Linear or another external project manager may be evaluated later as a planning projection if there is a real product-management need, but it must not become a second conflicting technical authority by default.

### Acceptance direction for future bounded workstream

A future implementation should prove at minimum:

- active/canonical material is retrieved by default;
- superseded/historical plans are excluded by default;
- explicit historical queries can still retrieve preserved evidence;
- closed task plans cannot silently regain active authority;
- exact workstream/SHA binding wins over text similarity;
- no duplicate router, memory graph, project manager, daemon, or scheduler is introduced;
- existing Operations Notebook / Task State / governance authority remains intact.

### Assimilation gate

```text
RULE_ASSIMILATION_ID=CONTEXT_HYGIENE_01
RULE_ASSIMILATION_STATUS=PENDING
```

To become `VERIFIED`:

1. a future Writer task explicitly lists `CONTEXT_HYGIENE_01` as a deliverable;
2. Writer reports the exact canonical artifacts changed and `RULE_ASSIMILATED=YES`;
3. independent verification passes on the exact candidate head/tree;
4. canonical merge/promotion follows the normal Owner Gate.

---

## Backlog maintenance law

When the Owner and Control Tower explicitly accept another durable P2P improvement idea that is intentionally deferred, add it here with a unique ID, concise rationale, approved direction, execution trigger, and `PENDING` status. Do not store speculative ideas that have not been accepted.
