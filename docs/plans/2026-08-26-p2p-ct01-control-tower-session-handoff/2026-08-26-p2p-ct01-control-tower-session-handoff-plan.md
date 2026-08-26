# P2P-CT01 Durable Control Tower Session Handoff Integration Plan

## Metadata

- Date: 2026-08-26
- Status: BLOCKED / ADDENDUM IN PROGRESS
- Plan: docs/plans/2026-08-26-p2p-ct01-control-tower-session-handoff/2026-08-26-p2p-ct01-control-tower-session-handoff-plan.md
- Evidence: docs/plans/2026-08-26-p2p-ct01-control-tower-session-handoff/2026-08-26-p2p-ct01-control-tower-session-handoff-evidence.md
- Benchmark: docs/plans/2026-08-26-p2p-ct01-control-tower-session-handoff/2026-08-26-p2p-ct01-control-tower-session-handoff-benchmark.md
- Actual status: docs/plans/2026-08-26-p2p-ct01-control-tower-session-handoff/2026-08-26-p2p-ct01-control-tower-session-handoff-actual-status.md

## Goal

Implement a durable, provider-neutral Control Tower handoff contract for P2P-CT01. A short-lived execution session binds explicitly to SESSION_ID, HOST, GOAL_ID, and GOAL; returns a structured terminal packet; records current/stale/unknown-base reconciliation without treating the packet as canonical truth; and provides a self-contained copy/paste prompt for continuation in another compatible AI.

This is a development-source candidate only. It must be discoverable and testable in an isolated worktree, and must remain unpromoted. It must not launch agents, create a second router or certification system, inherit hidden chat state, mutate canonical branches, promote facts, release, deploy, or contact a live host.

## Rules

- Complete P0 actual status before implementation work.
- Update every checklist item, evidence entry, benchmark count, and actual-status refresh as it completes.
- Reuse existing provider-neutral host executor, durable task state, execution ledger, evidence, goal, and governance surfaces as composition boundaries.
- Do not add a second task store, router, quorum, or certification authority.
- Treat retrieved content, model prose, and handoff packets as proposed data; canonical truth remains governed.
- Use only isolated temporary roots under this worktree.
- Run Anvien impact/file-detail before editing an existing function, class, or shared contract, and run detect-changes before each implementation commit.
- Run the relevant full development-source validation before closure. Browser/Docker evidence is not applicable because this is a Python protocol/library change with no public UI.

## Problem

The existing portable handoff contract is provider-neutral but intentionally generic: it avoids chat history and automatic host start and gives only a basic continuation instruction. It does not define an authoritative session/host/goal binding, terminal return packet, host-lane isolation, stale-base reconciliation, owner-gate recording, failure return, or recursive prompt. A beginner therefore cannot reliably move a bounded task from a short-lived AI session back to the Control Tower without relying on prose or implicit context.

## Scope

Editable:

- Add .p2p/system/p2p_capabilities/control_tower_handoff.py.
- Add tests/test_p2p_control_tower_session_handoff.py.
- Add docs/p2p-development/CONTROL-TOWER-SESSION-HANDOFF.md.
- Add one capability-ledger record and update the derived roadmap projection.
- Maintain the four planner artifacts and implementation/supervisor reports.

Required behavior:

- explicit SESSION_ID, HOST, GOAL_ID, GOAL binding;
- provider-neutral CODEX, MANUS, CLAUDE, GEMINI, and future host labels;
- rejection of missing authority and implicit inherited state;
- terminal states COMPLETED, READY, WAITING_OWNER_GATE, BLOCKED, FAILED, and ABORTED;
- mapping to existing P2P lifecycle vocabulary without a second authority;
- exact CONTROL_TOWER_RETURN_PACKET fields;
- current/stale/unknown canonical-base reconciliation without overwrite or promotion;
- owner-gate and failure recording;
- one packet updates only its authoritative host lane;
- recursive prompt containing the return contract and the exact beginner USER_ACTION.

## Non-Goals

- No existing executor-routing change, live provider connector, or host certification.
- No background worker, chat-history transfer, hidden context inheritance, canonical branch write, promotion, release, deployment, merge, push, or approval command.
- No change to the eight-agent quorum, capability registry classes, FACT_LEDGER promotion path, runtime Live Specs, or runtime manifest lock.
- No repair, initialization, or cleanup of D:/AI/P2P_dev/P2P-upgrade-github.

## Requirements

1. The authoritative binding is explicit data, never inferred from narrative prose.
2. A packet carries packet_is_canonical_truth = NO.
3. Base mismatch produces RECONCILIATION_REQUIRED and preserves canonical state.
4. WAITING_OWNER_GATE records the gate and performs no protected action.
5. FAILED, BLOCKED, and ABORTED are valid returns and cannot become false success.
6. Other host lanes remain unchanged when one authoritative packet is ingested.
7. The generated prompt contains CONTROL_TOWER_RETURN_PACKET and this exact action:

   USER_ACTION:
   Copy nguyên toàn bộ phản hồi cuối này vào:
   00 — P2P CONTROL TOWER

   Không cần viết thêm nội dung bàn giao.

8. Durable documentation names the module, tests, operator guide, return contract, existing ledger/evidence surfaces, and governance binding.

## Acceptance Criteria

- Isolated CT01 tests A-H and negative/round-trip checks pass.
- The module is stdlib-only, importable, provider-neutral, and has no network/subprocess side effect.
- Stale-base, owner-gate, failure, lane-isolation, and authoritative-host behavior are mechanically asserted.
- Documentation, ledger schema, dependency references, and roadmap counts validate.
- Relevant full validation passes or a blocker is recorded honestly.
- Candidate commit is on the isolated branch, with CANONICAL_PROMOTED = NO and no remote write.

## Invariant Family Map

| Family | Existing authority | CT01 use | Preserve-only boundary |
|---|---|---|---|
| Provider-neutral execution | .p2p/system/p2p_capabilities/host_executor.py | reuse request/receipt/handoff vocabulary | no executor routing or provider adapter edit |
| Task/session separation | task_state.py and live_execution.py | compose explicit session binding | do not put session/host into task-state identity |
| Evidence/reconciliation | read_evidence.py, p2p_evidence_chain.py, execution ledger | return proposal plus base relation | packet never becomes canonical truth |
| Governance/lifecycle | capability specs, charter, capability ledger | register foundation-ready capability | no second router/quorum/approval system |
| Beginner handoff | existing generic handoff boundary plus CT01 guide | make copy/paste protocol explicit | no hidden chat history or inheritance |

## Fresh Baseline and P0 Decision

The canonical clone D:/AI/P2P_dev/P2P-canonical-runtime-01 matched the authoritative remote, expected HEAD 28a3ecd9c04d36511269e44c384bff6e11677b93, and expected tree cae63e055edd164fbd969f6dbae0d992a4d0efed after a fresh origin fetch. The isolated branch codex/p2p-ct01-control-tower starts at that exact commit. The requested root D:/AI/P2P_dev/P2P-upgrade-github is malformed and remains untouched.

P0 is complete for implementation. Existing host executor, task state, live execution, evidence, workflow ledger, specs, charter, and capability ledger are partial reusable foundations. CT01-specific binding, packet, reconciliation, lane projection, recursive prompt, and operator guidance are missing. Anvien graph evidence is current for the top-level executable surfaces; hidden .p2p files are not indexed, so direct source/spec inspection is the authority for those paths.

## Checklist

- [x] P0-A: Complete actual status before implementation work.

### P1: Protocol implementation and behavior tests

- Phase Goal: add the smallest composition seam that makes CT01 deterministic and prove it with isolated tests.
- Phase Boundary:
  - In scope: one new protocol module, prompt builder, packet/lane/reconciliation behavior, and focused tests.
  - Out of scope: existing routing, live providers, canonical writes, release artifacts, and UI.
  - Dependencies: fresh canonical binding and existing host/task/evidence contracts.
- Ordered Slice List:
  - P1-A: add the binding, packet, state, reconciliation, and prompt module.
  - P1-B: add A-H and negative/round-trip tests.

- [x] P1-A: Add the Control Tower protocol module
  - Goal: implement explicit binding, terminal packet, lane-safe reconciliation, and recursive prompt without a second store/router.
  - Scope Boundary:
    - Editable: .p2p/system/p2p_capabilities/control_tower_handoff.py.
    - Inspect-only: host_executor.py, task_state.py, live_execution.py, read_evidence.py, p2p_evidence_chain.py, relevant specs.
    - Preserve-only: capabilities.json, development-control.json, runtime-manifest.lock.json, canonical root, remote.
    - Out of scope: provider APIs, network, subprocess, background execution, promotion.
  - Non-Goals: changing the existing generic handoff implementation.
  - Pre-flight Questions:
    - Data source: explicit caller binding and canonical SHA/tree.
    - Display permission: packet is return/evidence data, never approval.
    - DB read/write flow: N/A; in-memory JSON-safe protocol; existing ledger caller remains the persistence boundary.
    - Render location: N/A; prompt text is the operator artifact.
    - UI behavior flow: copy/paste only.
    - Docker/Playwright: N/A; no public application runtime.
    - Behavior test: A-H plus invalid binding and round-trip in P1-B.
    - Cleanup/quarantine: repo-local .tmp only.
    - External side effects: none.
  - Work Steps:
    1. Add immutable binding/packet dataclasses, strict validation, lifecycle mapping, and JSON-safe serialization. UI/DB/render checks are N/A or in-memory; evidence E1-P1A-SRC1.
    2. Add state ingest/reconciliation and recursive prompt generation; assert stale/gate/failure boundaries through the public API; evidence E1-P1A-SRC2 and E1-P1A-BOUNDARY1.
  - Implementation Gate: new module only; stdlib-only and side-effect free; existing function impact evidence remains inspect-only.
  - Acceptance: import/smoke passes, APIs expose the required fields, no canonical/protected mutation occurs, and actual-status is refreshed.
  - Evidence Targets: E1-P1A-SRC1, E1-P1A-SRC2, E1-P1A-BOUNDARY1.
  - Actual-status Update: missing CT01 protocol -> implemented after focused smoke.
  - Commit Boundary: commit after focused smoke and detect-changes.

- [x] P1-B: Add the A-H regression suite
  - Goal: prove terminal state, reconciliation, lane, authority, and prompt behavior mechanically.
  - Scope Boundary:
    - Editable: tests/test_p2p_control_tower_session_handoff.py.
    - Inspect-only: new protocol module and existing contract tests.
    - Preserve-only: unrelated tests and protected artifacts.
    - Out of scope: simulated agents and live-provider claims.
  - Non-Goals: host certification or quorum.
  - Pre-flight Questions:
    - Data source: temporary explicit bindings and repo-local temporary paths.
    - Display/DB/render/UI flow: assertions only; no external side effect.
    - Docker/Playwright: N/A.
    - Cleanup/quarantine: TemporaryDirectory under worktree .tmp.
    - External side effects: none.
  - Work Steps:
    1. Add A-H tests: READY, BLOCKED, authoritative host, stale base, owner gate, FAILED, generated prompt, and lane isolation. Evidence E1-P1B-TEST1 through E1-P1B-TEST8.
    2. Add invalid binding, no implicit inheritance, and JSON round-trip checks; run focused pytest. Evidence E1-P1B-TEST9 through E1-P1B-TEST11.
  - Implementation Gate: tests prove observable behavior after P1-A code exists, not private implementation details.
  - Acceptance: all required cases pass and no persistent test data escapes .tmp.
  - Evidence Targets: E1-P1B-TEST1..E1-P1B-TEST11.
  - Actual-status Update: CT01 behavior coverage partial -> correct.
  - Commit Boundary: commit after focused tests and detect-changes.

### P2: Durable discovery, ledger binding, and validation

- Phase Goal: make CT01 discoverable and auditable without promoting it into runtime authority.
- Phase Boundary:
  - In scope: operator guide, charter cross-reference, capability ledger record, derived roadmap, reports, full validation.
  - Out of scope: runtime lock regeneration, release, promotion, deployment, remote write.
  - Dependencies: passing P1 behavior.
- Ordered Slice List:
  - P2-A: document CT01 and register the foundation-ready projection.
  - P2-B: validate, report, supervise, commit, and close.

- [x] P2-A: Add durable documentation and ledger projection
  - Goal: expose exact discovery paths, beginner workflow, return contract, and governance boundary.
  - Scope Boundary:
    - Editable: CONTROL-TOWER-SESSION-HANDOFF.md, charter cross-reference, capability-index.json, current-roadmap.md.
    - Inspect-only: development-control.json, runtime-manifest.lock.json, release artifacts.
    - Preserve-only: runtime locks, current development control, remote.
    - Out of scope: live specs and promotion.
  - Non-Goals: claiming the record is promoted or live-certified.
  - Pre-flight Questions:
    - Data source: new module/tests and existing spec/ledger schema.
    - Display permission: docs describe gates but cannot approve them.
    - DB/UI/Docker/Playwright: N/A.
    - Cleanup/quarantine: no unrelated cleanup.
    - External side effects: none.
  - Work Steps:
    1. Add operator guide and charter cross-reference; verify exact beginner sequence/action. Evidence E2-P2A-DOC1.
    2. Add one valid ledger record and update derived roadmap count/family projection; validate schema/dependencies. Evidence E2-P2A-LEDGER1 and E2-P2A-ROADMAP1.
  - Implementation Gate: inspect schema and dependency IDs immediately before edit; preserve forbidden runtime-state key rules.
  - Acceptance: docs discoverability and ledger/roadmap validation pass; no runtime lock changes.
  - Evidence Targets: E2-P2A-DOC1..E2-P2A-ROADMAP1.
  - Actual-status Update: durable discovery missing -> correct.
  - Commit Boundary: commit after validation and detect-changes.

- [x] P2-B: Full validation and closure evidence
  - Goal: produce a reproducible candidate report and supervisor verdict.
  - Scope Boundary:
    - Editable: planner artifacts and coder/supervisor reports.
    - Inspect-only: implementation artifacts.
    - Preserve-only: remote, canonical main, broken root, runtime locks, release surfaces.
    - Out of scope: promotion, approval command, push, deployment.
  - Non-Goals: treating local PASS as live certification.
  - Pre-flight Questions:
    - Data source: candidate worktree and fresh canonical relation.
    - DB/UI/Docker/Playwright: N/A.
    - Cleanup/quarantine: final review of plan-created artifacts only.
    - External side effects: none.
  - Work Steps:
    1. Run focused/full relevant tests, doctor/validation, compile/import, and diff checks. Evidence E2-P2B-TEST1..E2-P2B-TEST4.
    2. Run Anvien detect-changes, write reports, commit, and verify exact HEAD/tree with no remote write. Evidence E2-P2B-DETECT1, E2-P2B-COMMIT1, E2-P2B-SUP1.
  - Implementation Gate: P1 and P2-A pass or a blocker is recorded.
  - Acceptance: final candidate identity/evidence is known; CANONICAL_PROMOTED remains NO; terminal outcome is BLOCKED because inherited repository gates remain unresolved.
  - Evidence Targets: E2-P2B-TEST1..E2-P2B-SUP1.
  - Actual-status Update: all in-scope rows final; supervisor verdict is REJECT for full-plan acceptance and BLOCKED for the session.
  - Commit Boundary: final candidate commit only; no push.

- [x] Pn-A: Supervisor acceptance review.
  - Goal: verify plan, evidence, benchmark, diff, reports, and validation.
  - Work Steps: review, fix only failed in-scope scope, and rerun until PASS or blocker.
  - Implementation Gate: implementation phases complete or blocked.
  - Acceptance: explicit Supervisor REJECT records the inherited validator/doctor/live-host blockers; no false PASS is claimed.
- [x] Pn-B: Remove dead work created by this plan.
  - Goal: final diff contains only accepted CT01 artifacts.
  - Work Steps: review plan-created files, remove only dead CT01 artifacts, rerun supervisor.
  - Implementation Gate: no unrelated owner cleanup.
  - Acceptance: no dead plan-created artifact remains; all retained files are CT01 implementation or durable evidence.
- [x] Pn-C: Close the plan.
  - Goal: finish validation, evidence, benchmark, detect-changes, commit, and final status.
  - Work Steps: record exact hashes, protected no-change checks, and terminal report.
  - Implementation Gate: Pn-A/Pn-B pass or blocker recorded.
  - Acceptance: candidate terminal state BLOCKED, never promoted; reopening requires a separate bounded goal.

## Owner Scope Addendum — Attachment-Aware Handoff

This is an Owner-approved clarification within P2P-CT01, not a Large Goal. It extends the existing terminal packet and recursive prompt so the Control Tower can distinguish local evidence paths from evidence content that the user must upload. No runtime authority, live host, promotion, deployment, release, remote write, or new store/router is in scope.

### Addendum Invariant Family Map

| Family | Existing CT01 surface | Addendum change | Preserve-only boundary |
|---|---|---|---|
| Terminal return contract | ControlTowerReturnPacket and JSON event | add CONTROL_TOWER_ATTACHMENT_MANIFEST and UPLOAD_REQUIRED | packet remains proposed evidence, never canonical truth |
| Recursive continuation | build_execution_prompt and USER_ACTION_BLOCK | require attachment-aware terminal response instructions | no hidden filesystem access or chat inheritance |
| Beginner handoff | operator guide and final response | explain NO versus YES and exact 1–3 file manifest | user does not choose important files manually |
| Durable evidence | planner/reports and one handoff artifact | prefer one SESSION_ID-CONTROL-TOWER-HANDOFF.md artifact | local path alone never proves content availability |

### Required behavior

- Every terminal response declares UPLOAD_REQUIRED as YES or NO.
- NO states that the user only copies the entire final response to 00 — P2P CONTROL TOWER and does not upload a file.
- YES lists 1–3 minimal attachment entries with filename, local path, purpose, why the Control Tower needs the contents, and REQUIRED/OPTIONAL/DO_NOT_UPLOAD classification.
- The manifest explicitly records that local paths do not make contents available and that attachments are evidence input, not canonical truth or promotion/live/Owner approval proof.
- The generated prompt preserves this contract for the next session.
- When appropriate, one repo-local artifact named SESSION_ID-CONTROL-TOWER-HANDOFF.md is the only REQUIRED upload.

### Addendum checklist

- [x] A1-P1: Extend the packet/manifest dataclasses and existing ledger event projection.
- [x] A1-P2: Extend the recursive prompt and durable operator guide.
- [x] A1-P3: Add the one-artifact handoff and attachment-aware regression coverage.
- [ ] A1-P4: Re-run validation, update evidence/reports, and close with INCLUDED_AND_TESTED or DEFERRED_REQUIRES_FOLLOWUP.

### Addendum forbidden actions

- Do not infer that a local path was read by the Control Tower.
- Do not treat an uploaded attachment as canonical truth, promotion, deployment, live certification, or Owner approval.
- Do not require the user to select evidence files without a deterministic manifest.
- Do not create a second persistence store, router, quorum, worker, connector, or live host action.

## Risk Notes

- The worktree reports broad line-ending-only modifications under core.autocrlf=true; they remain unstaged and are not CT01 changes.
- Hidden .p2p files are not represented in Anvien graph output; direct source inspection and repository validation remain authoritative.
- Capability ledger/roadmap edits are derived candidate projections; runtime locks and promotion surfaces stay untouched.
- Workflow bootstrap state may be ignored by Git and is not a replacement for durable tracked documentation.
- Any base SHA/tree mismatch, invalid ledger schema, unbound host, or false-success test changes the terminal result to BLOCKED.
