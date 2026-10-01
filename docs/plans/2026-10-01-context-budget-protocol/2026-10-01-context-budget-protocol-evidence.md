# Context Budget Protocol Evidence Ledger

## Metadata

- Date: `2026-10-01`
- Plan: `docs/plans/2026-10-01-context-budget-protocol/2026-10-01-context-budget-protocol-plan.md`
- Evidence: `docs/plans/2026-10-01-context-budget-protocol/2026-10-01-context-budget-protocol-evidence.md`
- Benchmark: `docs/plans/2026-10-01-context-budget-protocol/2026-10-01-context-budget-protocol-benchmark.md`
- Actual status: `docs/plans/2026-10-01-context-budget-protocol/2026-10-01-context-budget-protocol-actual-status.md`

## Evidence Rules

The evidence file explains why the work is known to be correct.

It should contain:

- metadata and companion files;
- evidence rules or evidence template;
- evidence sections such as `E0`, `E1`, or sections by phase/task;
- user report or problem evidence;
- source inspection, codebase facts, and document facts;
- commands run and pass/fail result;
- impact or blast-radius evidence when code/graph behavior changes;
- implementation evidence: files changed and behavior changed;
- validation evidence: build, tests, e2e, screenshots, or traces;
- failures encountered and how they were handled;
- detect-changes before commit;
- commit hash and closure evidence.

Evidence can reference short metric traces, but long metric tables belong in the benchmark file.

### Evidence ID Naming

Use stable, phase-scoped evidence IDs so `plan.md`, `actual-status.md`, `benchmark.md`, and later agents can reference exact proof without ambiguity.

Format:

```text
E<phase>-<item>-<kind><n>
```

Rules:

- `E<phase>` matches the plan phase number: `E0` for `P0`, `E1` for `P1`, `E2` for `P2`, and so on.
- `<item>` matches the checklist item without the dash: `P0A`, `P1A`, `P2B`.
- `<kind>` is plan-local. Choose a short uppercase token that is meaningful for this repo and this plan.
- `<n>` is a 1-based sequence number within that phase item and kind.
- Keep the same `<kind>` meaning stable inside one plan.
- Do not reuse an evidence ID for different facts.
- Reference exact evidence IDs from `actual-status.md` and `benchmark.md`; avoid referencing only broad section IDs such as `E1`.
- Use ranges such as `E0-P0A-FD1..E0-P0A-FD17` only for compact inventory summaries; use exact IDs when a specific status decision depends on a specific fact.
- If nearby plans already use a clear local evidence naming style, follow that style instead of inventing a new one.

Examples only:

- `E0-P0A-SRC1`
- `E0-P0A-GRAPH1`
- `E1-P1A-ROUTE1`
- `E2-P2B-KEYBOARD1`
- `E2-P2B-DETECT1`

Evidence sections must follow the plan phases:

- `E0` corresponds to `P0`.
- `E1` corresponds to `P1`.
- `E2` corresponds to `P2`.
- Use exact evidence IDs inside each section, not broad section IDs as proof.
- Each evidence section must name the plan phase or checklist item it supports.
- Do not invent fixed evidence categories; record the evidence required by the matching plan phase.

## E0 - P0 Evidence

Matching plan item(s): `P0-A`

- `E0-P0A-SRC1`: `AGENTS.md` already defines `RULE 16 CONTEXT_HYGIENE_AND_PLAN_LIFECYCLE`: session context is not authority; default retrieval is active task + required canonical specs; historical/superseded/closed material is excluded by default.
- `E0-P0A-SRC2`: `CONTROL-TOWER-SESSION-HANDOFF.md` already defines compact `P2P_CONTROL_TOWER_SUCCESSOR_PACKET`, `FULL_CHAT_HISTORY_INCLUDED=NO`, durable-evidence reconciliation, and qualitative rotation.
- `E0-P0A-SRC3`: `ARENA_AGENT_MODE_PROTOCOL.md` already rotates on context exhaustion/degradation and reconstructs new sessions from durable GitHub/project state.
- `E0-P0A-SRC4`: `P2P-AGENTS-INSTALL.md` already requires progressive disclosure, task-delta prompts, minimum useful independently verifiable slices, and no whole-law prompt duplication.
- `E0-P0A-SRC5`: `.p2p/system/p2p_capabilities/control_tower_handoff.py` already has successor/rotation data structures and a `max_prompt_chars` fail-closed prompt guard; runtime is preserve-only for this task.
- `E0-P0A-DEC1`: P0 decision: docs-only is the smallest sufficient path. AGENTS.md says doc-only commits do not use Anvien; therefore no Anvien pre-edit evidence is required for this slice.

## E1 - P1 Evidence

Matching plan item(s): `P1-A`

Pending implementation read-back on branch `ct/context-budget-protocol-285`.

## E2 - P2 Evidence

Matching plan item(s): `P2-A`

N/A — this plan has one docs-only implementation phase.

## Closure Evidence

Use this section for final detect-changes, commit hash, and closure evidence when the plan reaches completion.

Pending final branch diff, commit SHA, draft PR, and independent Supervisor handoff.
