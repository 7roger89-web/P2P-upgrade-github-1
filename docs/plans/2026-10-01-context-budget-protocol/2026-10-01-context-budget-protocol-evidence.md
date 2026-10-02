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

- `E1-P1A-DOC1`: Branch read-back confirms canonical RULE 16 now contains the 70k soft / 100k rotation heuristics, targeted hydration order, thin-handoff fields, evidence-over-history, do-not-carry rules, Writer stop conditions, independent Supervisor hydration, and mutable-state re-verification.
- `E1-P1A-DOC2`: Control Tower handoff guide now explicitly reuses `P2P_CONTROL_TOWER_SUCCESSOR_PACKET` as the compaction mechanism, keeps `FULL_CHAT_HISTORY_INCLUDED=NO`, identifies rehydration references, excludes disposable history, and requires fresh verification of mutable Git/test claims.
- `E1-P1A-DOC3`: Arena protocol now applies the same heuristic budget and relevance-driven hydration without a provider-specific framework; installed-agent entrypoint carries only a thin digest of the canonical rule.
- `E1-P1A-SCENARIO1`: Structural branch read-back mapped all four required scenarios to explicit policy text: A bounded Writer/targeted verification = PASS; B successor-packet compaction/rotation = PASS; C independent Supervisor hydration = PASS; D mutable Git/test state re-verification and noncanonical packet semantics = PASS.
- `E1-P1A-DIFF1`: Compare from base `4ce35d4559edb9f83023568ef7e6089132c54a8d` to implementation head `e69bfdd34884f71e09b6cdc52470fcb2a0af7790` showed only eight docs/plan files changed, branch ahead by 8 and behind by 0; no runtime source, schema, dependency, generated AGENTS.md, or state-store file changed.
- `E1-P1A-RUNNER1`: Direct container Git access was unavailable because the environment could not resolve github.com, so repository tests were NOT_RUN rather than reported failed. Validation therefore uses authenticated GitHub branch read-back and compare evidence for this docs-only slice.


- `E1-P1A-DRIFT1`: Fresh Supervisor precheck found current main `135dcf845b59c5fa09a0737a68fbf7b6b957778a` while candidate HEAD `d30636b0998c740660f937475ea62ba8ef4bd9b7` was `behind_by=6`; exact-head acceptance was rejected and recorded in `reports/supervisor/rp_supervisor_261001_174500_by_gpt-5-6-sol_context-budget-protocol-pr286-drift.md`.
- `E1-P1A-MERGE1`: Writer repair verified the six main-side commits touched only `docs/RESEARCH-ADOPTION-LEDGER.md`, `docs/p2p-development/research/P2P-KONG-REVERSE-INTAKE-01.md`, and `governance/research-adoption-ledger.json`, disjoint from the context-budget policy paths. A non-force two-parent merge commit `e512364c4333f400f5640869334d695a4edb094e` merged current main into the existing PR branch while preserving both histories.

- `E1-P1A-CAP1`: Fresh capability-ledger/source inspection found `ADAPTIVE_CONTEXT_BUDGET` remains `PARTIAL` and `.p2p/system/p2p_capabilities/adaptive_budget.py` implements separate task-level dynamic soft/hard budgets. The policy now explicitly states that 70k/100k session heuristics do not promote, replace, or reconfigure that runtime capability.

## E2 - P2 Evidence

Matching plan item(s): `P2-A`

N/A — this plan has one docs-only implementation phase.

## Closure Evidence

Use this section for final detect-changes, commit hash, and closure evidence when the plan reaches completion.

- `E-CLOSE-SUP1`: Independent Arena Supervisor review on PR #286 returned APPROVED/PASS at exact HEAD `c37ba6fa9f01af67e3c81083242837fe48296042` / tree `30319ef0154d9bcce11579b2e396337a1766cc59`, with no blocking findings. The reviewer independently re-read law, reverified Git identity, ran 11 challenge-test modules, and confirmed exact-head Shield success.
- `E-CLOSE-MERGE1`: PR #286 merged to `main` as merge commit `e3eabbd3a1bd157d20c5bd5938a7a0cca979d24a`; Issue #285 is closed as completed.
- `E-CLOSE-DEAD1`: Closure cleanup removes the orphan `B2 - P2 Benchmarks` section because the plan has no P2 implementation phase. The earlier drift-rejection report is intentionally preserved as durable evidence of Scenario D rather than deleted as dead work.
- `E-CLOSE-SCOPE1`: Closure remains docs-only. Runtime/unit implementation, Docker, Playwright, generated-output regeneration, promotion, release, deployment, secret, and infrastructure actions are not part of this closure.
- `E-CLOSE-LEARN1`: `LEARNING_RECONCILIATION=NONE` — the drift lesson is already embodied by the new mutable-state rule and no additional reusable experience candidate is necessary for this routine successful closure.
