# Context Budget Protocol Plan

## Metadata

- Date: `2026-10-01`
- Status: `draft`
- Plan: `docs/plans/2026-10-01-context-budget-protocol/2026-10-01-context-budget-protocol-plan.md`
- Evidence: `docs/plans/2026-10-01-context-budget-protocol/2026-10-01-context-budget-protocol-evidence.md`
- Benchmark: `docs/plans/2026-10-01-context-budget-protocol/2026-10-01-context-budget-protocol-benchmark.md`
- Actual status: `docs/plans/2026-10-01-context-budget-protocol/2026-10-01-context-budget-protocol-actual-status.md`

## Goal

Extend the existing P2P context-hygiene, Control Tower rotation, Arena session, and installed-agent guidance so agents use bounded working context, thin durable handoffs, targeted rehydration, and explicit rotation heuristics without creating a new framework.

## Rules

- Complete P0 actual status before implementation work.
- Update each checklist item immediately when it is completed.
- Record evidence as work completes.
- Record benchmarkable counts or measurements when they are taken.
- Update later phase status assumptions, next actions, and work steps when actual-status evidence changes the repo state.
- After completing a phase or implementation slice and refreshing `actual-status.md`, update the next affected phase's work steps as needed to match the latest repo reality, while preserving that phase's original goal, scope, acceptance criteria, and major phase order.
- Run Anvien detect-changes before every implementation-slice commit when implementation work was performed.
- For public runtime or UI-facing changes, validate the real user-visible runtime with browser or Playwright evidence.
- For app/runtime validation, full build must include Docker image/container build. If Docker is missing or not run, full build is incomplete.
- Any Playwright validation must target the real built Docker/container runtime. Running Playwright against a host dev server, framework dev mode, mocked server, or source-run shortcut is not valid runtime evidence.
- If the Docker runtime cannot be built or started, the slice/plan is blocked; do not replace it with dev-server Playwright evidence.
- Playwright evidence must record the Docker build/run or compose command, container/service name, exposed URL, Playwright command, and screenshot/trace/result.
- Keep the standard planner structure. These detail rules only make phase checklist items concrete enough to implement safely.
- Every implementation phase must be decomposed into multiple implementation slices that are as small as practical. A phase is a grouping and ordering container; a slice is the executable implementation unit.
- Do not implement a phase directly. Work starts from a slice ID such as `P1-A`, `P1-B`, or `P2-C`.
- Prefer many narrow slices over one broad slice. A single-slice implementation phase is allowed only when the plan explicitly states why the phase cannot be split further without creating empty or non-executable slices.
- Each implementation slice must include:
  + Goal
  + Scope Boundary
  + Non-Goals when useful
  + Pre-flight Questions
  + Work Steps
  + Implementation Gate
  + Acceptance
  + Evidence Targets
  + Actual-status Update
  + Commit Boundary
- Split planned work into separate slices when it contains more than one primary user-visible behavior, user trigger, render location, permission or visibility rule, DB write target, DB state transition, API/CLI/MCP contract, async/event/webhook flow, external side effect, cleanup/quarantine domain, behavior test target, independent acceptance gate, or independent commit boundary.
-  Hidden fallback is forbidden. Prefer a visible failure over a fallback that hides a broken primary path.
- When touching DB-backed content, verify the full loop when applicable: UI input -> submit action -> DB write -> DB read after reload/new request -> correct UI render or omission. If there is no UI, replace UI steps with the real caller/consumer flow.
- Tests must prove product behavior. Delete or replace tests that only assert implementation details, helper output, static DOM existence, or mocked plumbing without proving trigger -> process -> observable result.
- If a planned item uses wording such as `and`, `also`, `then wire`, `plus update`, `both`, or `handle all`, check whether it is actually multiple slices.
- Do not write broad actionable items such as `Implement checkout, webhook, entitlement update, and billing UI`; split them into narrow slices such as `Create checkout session request`, `Persist checkout session state`, `Handle provider webhook`, `Update entitlement from webhook event`, and `Render billing status from entitlement`.
- Each slice work step must include UI flow, DB/data flow, render location, and evidence target checks. Use `N/A` with a reason when a check does not apply.
- If tests write DB rows, app state, files, queues, provider state, or other persistent data, the slice must define cleanup or quarantine before implementation.

## Problem

P2P already treats chat state as ephemeral and durable repository/evidence state as authoritative, but the policy is distributed and does not yet state one operational context budget, one targeted hydration order, one explicit do-not-carry rule, or one thin-handoff rule. The missing guidance can cause agents to carry stale logs, duplicate durable material, or overhydrate future sessions.

## Scope

Docs-only update to the canonical operations notebook, Control Tower handoff guide, Arena Agent Mode protocol, and P2P installed-agent entry point. Reuse existing successor packet, rotation handoff, durable evidence/state, exact-head reconciliation, and prompt-size guard.

## Non-Goals

No runtime/Python changes; no new packet/schema/state store/router; no dependency changes; no model-specific hard limit assumptions; no fixed docs/code ratio; no chain-of-thought storage; no weakening of Supervisor independence, exact-HEAD verification, evidence, or Owner Gates.

## Requirements

Add soft 70k and rotation 100k token heuristics as non-hard operational defaults; qualitative rotation triggers; thin-handoff fields by reference; targeted hydration order; evidence-over-history/do-not-carry rules; Writer stop conditions; independent Supervisor hydration; mutable Git facts must be freshly reverified. Extend existing RULE 16 and successor/rotation semantics rather than inventing a parallel protocol.

## Acceptance Criteria

Scenario A: bounded Writer task hydrates only relevant law/docs/code and returns compact durable refs. Scenario B: long-lived Control Tower compacts through the existing successor packet and rotates without full history. Scenario C: Supervisor reconstructs independently from task contract + exact HEAD + durable evidence, not Writer chat. Scenario D: successor re-verifies mutable Git/test state and never treats packet as canonical truth.

## Checklist

- [ ] P0-A: Complete actual status before implementation work.
  - Goal: establish the real current state.
  - Work Steps: inspect source-of-truth files, classify each surface, record blocked or missing pieces, and update later phase status assumptions, next actions, and work steps from evidence.
  - Implementation Gate: no implementation or editing starts until `docs/plans/2026-10-01-context-budget-protocol/2026-10-01-context-budget-protocol-actual-status.md` has a final P0 decision.
  - Acceptance: actual status identifies correct, partial, missing/unbound, fake-or-stub, and blocked surfaces for this scope.

### P1: Assimilate Context Budget Protocol into existing policy surfaces

- Phase Goal: Make the existing context-hygiene and rotation architecture explicit, thin, and operational without runtime redesign.
- Phase Boundary:
  - In scope: P2P-OPERATIONS-NOTEBOOK.md; CONTROL-TOWER-SESSION-HANDOFF.md; ARENA_AGENT_MODE_PROTOCOL.md; P2P-AGENTS-INSTALL.md.
  - Out of scope: Python runtime, generated AGENTS.md, task-state schemas, router, execution ledger implementation, new packet types.
  - Dependencies: Issue #285; current canonical Supreme Law; existing RULE 16; existing successor packet/rotation contract.
- Phase Implementation Rule: do not implement `P1` directly. Implement `P1-A`, verify it, record evidence, refresh actual-status, commit when required, then continue to `P1-B`.
- Ordered Slice List:
  - P1-A: Extend existing docs-only context policy
  - P1-B: N/A — one atomic docs-only policy slice; splitting the four linked authority surfaces would leave inconsistent instructions.

- [ ] P1-A: Extend existing docs-only context policy
  - Goal: Add explicit context-budget, thin-handoff, targeted-hydration, do-not-carry, rotation, Writer, and Supervisor guidance while preserving existing mechanisms.
  - Scope Boundary:
    - Editable: docs/p2p-development/P2P-OPERATIONS-NOTEBOOK.md; docs/p2p-development/CONTROL-TOWER-SESSION-HANDOFF.md; docs/ARENA_AGENT_MODE_PROTOCOL.md; docs/p2p-development/P2P-AGENTS-INSTALL.md.
    - Inspect-only: AGENTS.md; .p2p/system/p2p_capabilities/control_tower_handoff.py; tests/test_p2p_control_tower_session_handoff.py; .agents/skills/coder/SKILL.md; .agents/skills/supervisor/SKILL.md.
    - Preserve-only: Existing successor packet schema, rotation handoff schema, execution ledger, exact-head reconciliation, Owner Gates, Supervisor zero-trust review.
    - Out of scope: Runtime code, generated AGENTS.md direct edits, additional context manifest/schema, new automation/daemon.
  - Non-Goals: No token metering subsystem; no automatic context counter; no whole-repo preload; no fixed 90/10 docs/code ratio.
  - Pre-flight Questions:
    - Data source: Canonical P2P docs + existing durable repo/Git/PR/task/evidence state.
    - Display permission: N/A — internal operations policy only.
    - DB read flow: N/A — no database.
    - DB write flow: N/A — no database.
    - Render location: N/A — Markdown policy surfaces.
    - UI behavior flow: N/A — no UI behavior.
    - Docker runtime: N/A — docs-only.
    - Playwright target: N/A — docs-only.
    - Behavior test: Structural read-back plus scenario mapping against existing successor/rotation/Arena contracts.
    - Cleanup/quarantine: N/A — no persistent runtime data.
    - External side effects: GitHub branch commits and draft PR only; no merge/deploy/promotion.
    - N/A notes: AGENTS.md explicitly says doc-only commits do not use Anvien; no code-bearing surface is edited.
  - Work Steps:
    1. Extend RULE 16 in the canonical notebook with context budget heuristics, targeted hydration, thin handoff, evidence-over-history, do-not-carry, and actor-specific stop/review rules; keep existing authority boundaries unchanged.
       - UI flow check: N/A — docs-only.
       - DB/data flow check: N/A — docs-only.
       - Render location check: Markdown section remains under existing RULE 16.
       - Mini QA for each completed implementation slice (MUST) 
          For Codex: When Mini QA must use plugins
            - Browser: Control the in-app browser
            - Chrome: Control the user's real Chrome browser
            - Computer Use: Control Windows apps or installed artifacts when mini QA requires real app interaction outside a browser.
            - Playwright: use as an automation arm for browser actions, control sweeps, screenshots, videos, traces, and reports.
          For Claude or other agents:
            - Use the equivalent browser, Chrome/session, or computer-control capability exposed by that agent/runtime or Playwright-like capability available in that environment.
       - Evidence target: E1-P1A-DOC1
    2. Align Control Tower, Arena, and install entrypoint guidance to the same rule by reference; explicitly reuse successor packet/rotation and fresh mutable-state verification; avoid duplicating the full canonical rule body.
       - UI flow check: N/A — docs-only.
       - DB/data flow check: N/A — docs-only.
       - Render location check: Markdown operator/discovery sections only.
       - Mini QA for each completed implementation slice (MUST) 
          For Codex: When Mini QA must use plugins
            - Browser: Control the in-app browser
            - Chrome: Control the user's real Chrome browser
            - Computer Use: Control Windows apps or installed artifacts when mini QA requires real app interaction outside a browser.
            - Playwright: use as an automation arm for browser actions, control sweeps, screenshots, videos, traces, and reports.
          For Claude or other agents:
            - Use the equivalent browser, Chrome/session, or computer-control capability exposed by that agent/runtime or Playwright-like capability available in that environment.
       - Evidence target: E1-P1A-DOC2
  - Implementation Gate:
    - Before editing target files, run the relevant Anvien impact/file-detail command for files, symbols, routes, tools, or contracts touched by this slice, and record the evidence IDs.
    - P0 actual status proves existing runtime is preserve-only and docs-only is sufficient; no runtime file is edited.
  - Acceptance:
    - Source: All four authority/guidance docs contain consistent bounded-context semantics without introducing a parallel framework.
    - Runtime/UI: N/A — no runtime/UI change.
    - DB/data: N/A — no DB/data change.
    - Behavior test: Scenario A-D map to existing durable state, successor packet, Arena rotation, and Supervisor independence.
    - Cleanup/quarantine: No second packet/schema/state store added.
    - Evidence IDs: E1-P1A-DOC1, E1-P1A-DOC2, E1-P1A-SCENARIO1
    - Actual-status rows refreshed: RULE16, CT-HANDOFF, ARENA-PROTOCOL, INSTALL-ENTRYPOINT
  - Evidence Targets: Canonical doc read-back, cross-surface consistency, scenario A-D mapping, branch diff review.
  - Actual-status Update: partial -> correct for the four doc surfaces; runtime remains correct/preserve-only.
  - Commit Boundary: commit after this slice when acceptance passes.
- [ ] Pn-A: Call supervisor for the implemented-plan acceptance loop.
  - Goal: verify the completed plan work against the accepted plan, actual-status decisions, evidence, benchmark, changed files, generated output, and validation results before closure.
  - Work Steps:
    1. Call the supervisor skill to review the full completed plan work.
    2. If supervisor fails the work, return to the responsible implementation workflow/skill for the failed scope only.
    3. Re-run supervisor review after the fix.
    4. Repeat until supervisor passes or records a blocker.
  - Implementation Gate: all planned implementation phases must be completed or explicitly blocked before this review.
  - Acceptance: supervisor review passes, or the plan records a blocker with evidence and no closure is performed.
- [ ] Pn-B: Remove dead work created during this plan.
  - Goal: ensure the final diff contains only artifacts that still serve the accepted plan.
  - Work Steps:
    1. Review files, sections, generated output, tests, temp files, and plan artifacts created or modified during this plan.
    2. Remove or rewrite any artifact made obsolete by actual-status findings, user corrections, failed approaches, or phase status updates.
    3. Verify no rejected approach, stale placeholder, unused generated output, or dead helper artifact remains in the final diff.
    4. Call supervisor to review the dead-work cleanup.
    5. If supervisor fails the cleanup, return to the responsible implementation workflow/skill for the failed cleanup scope only, then re-run supervisor review.
  - Implementation Gate: only remove artifacts created by this plan unless the user explicitly approves broader cleanup.
  - Acceptance: final `git diff/status` contains no dead plan-created artifacts, supervisor passes the cleanup, and evidence records what was removed or preserved.
- [ ] Pn-C: Close the plan.
  - Goal: finish validation, evidence, benchmark, detect-changes, commit, and final status.
  - Work Steps:
    1. Run the required final validation for the accepted scope, including full build before final runtime validation. For app/runtime scopes, full build must include Docker image/container build.
    2. Start the real built Docker/container runtime for app/runtime validation. If Docker cannot be built or started, record the blocker and do not substitute a host dev server.
    3. Validate public runtime or UI-facing changes with browser or Playwright evidence against the real built Docker/container runtime. Playwright evidence must include Docker build/run or compose command, container/service name, exposed URL, Playwright command, and screenshot/trace/result.
    4. Regenerate generated outputs if source-of-truth changes require it.
    5. Run Anvien detect-changes before commit when implementation work was performed.
    6. Record final validation, detect-changes, benchmark, and commit evidence.
    7. Commit the completed scope and verify the worktree state.
  - Implementation Gate: Pn-A and Pn-B must pass or record blockers.
  - Acceptance: final evidence is recorded, required commits exist, and the worktree state is known.

## Risk Notes

Main risk is policy duplication or drift. Mitigation: extend RULE 16, point subordinate docs to the same semantics, do not create a new compaction packet, and keep numeric limits explicitly heuristic rather than hard model assumptions.
