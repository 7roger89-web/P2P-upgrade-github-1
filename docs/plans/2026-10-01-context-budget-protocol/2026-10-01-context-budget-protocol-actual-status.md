# Context Budget Protocol Actual Status

Title: Context Budget Protocol
Date: 2026-10-01
Status: Draft / P0 Complete / Blocked
Companion plan: `docs/plans/2026-10-01-context-budget-protocol/2026-10-01-context-budget-protocol-plan.md`
Companion evidence: `docs/plans/2026-10-01-context-budget-protocol/2026-10-01-context-budget-protocol-evidence.md`
Companion benchmark: `docs/plans/2026-10-01-context-budget-protocol/2026-10-01-context-budget-protocol-benchmark.md`

## Purpose

This file records the real current state before implementation.

Implementation must not start until the target scope has a completed status row, evidence IDs, and a downstream plan decision.

This file does not replace `evidence.md`. It classifies current state from evidence.

Use exact evidence IDs from `evidence.md`, such as `E0-P0A-SRC1`, not broad section IDs such as `E0` or `E1`.

## Freshness / Refresh Rules

This actual-status file is a living current-state record, not a one-time P0 snapshot.

P0 records the baseline before implementation. After implementation begins, keep the Current Status Matrix updated so the next agent can trust it as the latest repo reality.

Update this file:

- after each completed implementation slice;
- before starting the next phase if repo state changed;
- whenever evidence changes a current-state classification;
- whenever the next phase's status assumptions, next action, or work steps need updating because reality differs from the previous status.

When refreshing status:

- update only the rows affected by the completed work or new evidence;
- use explicit transitions such as `missing -> correct`, `partial -> correct`, `fake-or-stub -> removed`, or `unbound -> bound-correct`;
- append a Status Refresh Log row instead of deleting history;
- keep detailed proof in `evidence.md`; store only classifications, evidence IDs, touch mode, and plan consequences here.

## Scope

Target scope:

- Issue #285 docs-only context-budget assimilation across canonical law, Control Tower handoff, Arena protocol, and installed-agent entrypoint.

Out of scope:

- Runtime Python, generated AGENTS.md direct edits, new packet/schema/state store/router, model-specific token metering.

## Relationship / Impact Evidence

For each target file, prefer:

```text
anvien file-detail <path> --repo <repo> --json
```

Record how many files the target is related to before deciding touch mode. A file with many relationships may still be editable, but the plan must narrow the exact phase, touch mode, and validation needed.

| Unit / File / Surface | File Detail Evidence | Related File Count | Relationship Summary | Impact Note |
|-----------------------|----------------------|--------------------|----------------------|-------------|
| Context Budget Protocol policy family | E0-P0A-SRC1..E0-P0A-SRC5 | N/A | The four docs are policy/discovery surfaces over existing runtime; no runtime behavior needs to change. | low / medium / high / critical scope warning |

## Status Rules

| Status | Meaning | Allowed next action |
|--------|---------|---------------------|
| `correct` | Already behaves as required. | Preserve. Add evidence or tests only if needed. |
| `partial` | Some required behavior exists, but gaps remain. | Change only the missing parts. Preserve correct parts. |
| `wrong` | Current behavior, source, or contract is incorrect. | Replace with required behavior. Record the exact reason. |
| `missing` | Required behavior, source, or contract does not exist. | Implement the missing piece only. |
| `unbound` | Surface exists but is not wired to the real source, flow, or contract. | Bind to the real source only. Preserve approved surface. |
| `fake-or-stub` | Prototype, demo, mock, fallback, or placeholder data is being used as real behavior. | Remove fake behavior or replace it with an approved truthful state. |
| `blocked` | Source, authority, contract, or required evidence is unclear. | Stop. Do not implement until resolved. |

## Current Status Matrix

| Unit | Current State | Required State | Status | Relationship Count | Evidence | Next Plan Decision |
|------|---------------|----------------|--------|--------------------|----------|--------------------|
| Context Budget Protocol policy family | Core context-hygiene and rotation mechanisms already exist, but explicit 70k/100k heuristic budgeting, targeted hydration order, thin-handoff semantics, do-not-carry list, and Supervisor hydration rules are incomplete across the docs. | Existing mechanisms remain authoritative while the missing operational context-budget semantics are explicit and consistent. | correct/partial/wrong/missing/unbound/fake-or-stub/blocked | N/A related files | E0-P0A-SRC1, E0-P0A-SRC2, E0-P0A-SRC3, E0-P0A-SRC4, E0-P0A-SRC5 | preserve / edit P1-A / update P2-B status / block |

## Status Refresh Log

| Refresh | Date | Repo Basis | Changed Scope | Status Changes | Evidence | Next Phase Update |
|---------|------|------------|----------------|----------------|----------|-------------------|
| R0 | 2026-10-01 | baseline before P0 | Issue #285 docs-only context-budget assimilation across canonical law, Control Tower handoff, Arena protocol, and installed-agent entrypoint. | initial classification | E0-P0A-SRC1, E0-P0A-SRC2, E0-P0A-SRC3, E0-P0A-SRC4, E0-P0A-SRC5 | Proceed with one docs-only P1-A slice; preserve runtime. |
| R1 | 2026-10-01 | after P1-A | four docs-only authority/guidance surfaces | partial -> correct (pending P1 evidence) | E0-P0A-SRC1, E0-P0A-SRC2, E0-P0A-SRC3, E0-P0A-SRC4, E0-P0A-SRC5 | close after Supervisor review; no runtime follow-up unless evidence disproves docs-only sufficiency. |

## Phase Touch Map

Use this map to prevent accidental edits. A related file is not automatically editable.

`Plan-Relevant Relationship File` lists only a relationship file that can directly affect or be affected by the planned phase or slice. Do not copy the full `file-detail` relationship inventory into this map. Include only files whose relationship can affect the phase/slice decision, touch mode, or validation.

| Unit / File / Surface | Plan-Relevant Relationship File | Relationship to Target | Plan Item | Touch Mode | Evidence | Constraint |
|-----------------------|---------------------------------|------------------------|-----------|------------|----------|------------|
| Context Budget Protocol policy family | docs/p2p-development/CONTROL-TOWER-SESSION-HANDOFF.md; docs/ARENA_AGENT_MODE_PROTOCOL.md; docs/p2p-development/P2P-AGENTS-INSTALL.md | source-of-truth / consumer / generated output / test / config / dependency | P1-A | preserve-only / inspect-only / edit / regenerate / validate-only / block / do-not-touch | E0-P0A-SRC1, E0-P0A-SRC2, E0-P0A-SRC3, E0-P0A-SRC4, E0-P0A-SRC5 | Extend existing RULE 16 and successor/rotation architecture; no second framework. |

## Detailed Findings

### Context Budget Protocol policy family

Current state:

RULE 16 already excludes historical context by default. Control Tower already has a compact successor packet and no-full-history rotation. Arena already rotates on context exhaustion and rehydrates from durable state. Installed-agent guidance already uses progressive disclosure and task-delta prompts. Missing pieces are explicit operational budget heuristics, one targeted hydration sequence, thin-handoff field semantics, do-not-carry examples, and explicit Writer/Supervisor context separation.

Required state:

```text
Context is working memory, not durable storage. Use 70k soft / 100k rotation heuristics where exact measurement is available or qualitative equivalents otherwise. Rehydrate from authoritative durable refs only. Carry only live state that cannot be reliably rediscovered. Reverify mutable Git/test facts. Keep Supervisor independent of Writer chat.
```

Evidence:

- E0-P0A-SRC1: Existing RULE 16 proves the core invariant is already canonical.
- E0-P0A-SRC2: Existing successor/rotation packet proves a new compaction packet is unnecessary.

Relationship and impact:

- Related file count: N/A
- Relationship summary: The four docs are policy/discovery surfaces over existing runtime; no runtime behavior needs to change.
- Impact note: medium policy-scope warning: inconsistent wording could create drift, so the four surfaces must be edited atomically on one branch.

Classification:

partial

Allowed next action:

Edit only the missing policy semantics in the four docs; preserve existing runtime and packet schemas.

Forbidden next action:

Do not create a new context framework, packet, state store, token-metering service, or edit generated AGENTS.md directly.

## Next Phase Status Decisions

| Plan Item | Actual Status Finding | Required Status / Next-Action Update |
|-----------|-----------------------|--------------------------------------|
| P1-A | Existing runtime and core invariants are correct; only docs/policy detail is partial. | keep / change / remove / block |

## Implementation Gate

- [x] Target scope is listed in Current Status Matrix.
- [x] Each target unit has a status.
- [x] Each status has evidence IDs.
- [x] Each target file has relationship count evidence from `file-detail` when applicable. N/A for docs-only per AGENTS.md.
- [x] Phase Touch Map lists plan-relevant relationship files that can affect the current phase/slice.
- [x] Phase Touch Map defines touch mode for every plan-relevant relationship unit that may be affected.
- [x] Correct parts are marked preserve-only.
- [x] Partial parts have exact next actions.
- [x] Blockers are recorded, if any: none.
- [x] Next phase status assumptions, next action, and work steps have been updated from this status file when needed.
- [x] Status Refresh Log has an R0 baseline row.
- [ ] If implementation has started, affected Current Status Matrix rows have been refreshed from latest evidence.
- [ ] If refreshed statuses changed next work, only the stale next-phase status assumptions, next action, or work steps have been updated before the next phase.

## Final P0 Decision

Choose one:

- [ ] P0 actual-status incomplete. Implementation is blocked.
- [x] P0 complete. Next phase can proceed unchanged.
- [ ] P0 complete. Next phase status, next action, or work steps must be updated before implementation.
- [ ] P0 complete. Target scope is preserve-only.
- [ ] P0 complete. Implementation is blocked by missing authority or evidence.

Decision note:

P0 complete. Proceed with one docs-only P1-A slice. Runtime code is preserve-only; Anvien is not required for doc-only commits under AGENTS.md.
