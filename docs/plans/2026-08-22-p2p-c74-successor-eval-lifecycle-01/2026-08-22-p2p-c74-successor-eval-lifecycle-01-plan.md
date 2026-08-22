# P2P C74 Successor Evaluator Lifecycle Plan

## Metadata

- Date: `2026-08-22`
- Status: `draft`
- Plan: `docs/plans/2026-08-22-p2p-c74-successor-eval-lifecycle-01/2026-08-22-p2p-c74-successor-eval-lifecycle-01-plan.md`
- Evidence: `docs/plans/2026-08-22-p2p-c74-successor-eval-lifecycle-01/2026-08-22-p2p-c74-successor-eval-lifecycle-01-evidence.md`
- Benchmark: `docs/plans/2026-08-22-p2p-c74-successor-eval-lifecycle-01/2026-08-22-p2p-c74-successor-eval-lifecycle-01-benchmark.md`
- Actual status: `docs/plans/2026-08-22-p2p-c74-successor-eval-lifecycle-01/2026-08-22-p2p-c74-successor-eval-lifecycle-01-actual-status.md`

## Goal

Repair the single promotion-blocking installed-project evaluation lifecycle defect reported against sealed candidate `.73`, then mint a new unpromoted successor candidate only if the source, clean-consumer lifecycle, regression, package, governance, and safety gates all pass. The canonical contract for an installed consumer is Option B: the project-eval helper under `<consumer>/.p2p/system/scripts/p2p_eval.py` is authoritative; an unpacked package/source checkout may use its packaged `scripts/p2p_eval.py` only as the equivalent package validation surface. No installed consumer may silently fall back to an ancestor checkout or reviewer hand-copy.

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
- Hidden fallback is forbidden. Prefer a visible failure over a fallback that hides a broken primary path.
- When touching DB-backed content, verify the full loop when applicable: UI input -> submit action -> DB write -> DB read after reload/new request -> correct UI render or omission. If there is no UI, replace UI steps with the real caller/consumer flow.
- Tests must prove product behavior. Delete or replace tests that only assert implementation details, helper output, static DOM existence, or mocked plumbing without proving trigger -> process -> observable result.
- If a planned item uses wording such as `and`, `also`, `then wire`, `plus update`, `both`, or `handle all`, check whether it is actually multiple slices.
- Do not write broad actionable items such as `Implement checkout, webhook, entitlement update, and billing UI`; split them into narrow slices such as `Create checkout session request`, `Persist checkout session state`, `Handle provider webhook`, `Update entitlement from webhook event`, and `Render billing status from entitlement`.
- Each slice work step must include UI flow, DB/data flow, render location, and evidence target checks. Use `N/A` with a reason when a check does not apply.
- If tests write DB rows, app state, files, queues, provider state, or other persistent data, the slice must define cleanup or quarantine before implementation.
- Preserve the official `.19` baseline, sealed `.72` rollback, and sealed `.73` candidate bytes exactly.
- Do not run approval, promote, finalize, merge, tag, release, deploy, or publish actions in this task.
- Do not touch C43, AERG, multi-AI certification, external projects, or user-owned root-worktree changes.

## Problem

The independent `.73` promotion-readiness review reproduced a clean installed-consumer failure: the completion case in `scripts/p2p_eval.py` constructs `<consumer>/scripts/p2p_eval.py`, while normal package installation provides the project-eval v2 helper under `<consumer>/.p2p/system/scripts/p2p_eval.py`. Four attempted trial slots exited with code `2`, produced no trial records, made the project-eval gate fail, made strict Doctor fail, and blocked `p2p_gate prepare` before approval. The `.73` ZIP is sealed and must not be repaired in place.

## Scope

- Fresh successor worktree based on the sealed `.73` lineage.
- Inspect and minimally correct the completion-case evaluator resolution in `scripts/p2p_eval.py`.
- Add direct lifecycle tests in `tests/test_p2p_project_eval.py` proving installed-runtime ownership, package/source validation behavior, and fail-closed behavior when the installed helper is absent.
- Re-run the real normal packaged install/adoption path in a fresh disposable consumer, design/validate the project-owned suite, execute five cases x baseline/P2P x two trials, run the project-eval gate, strict installed Doctor, and technical `p2p_gate prepare`.
- Re-run the relevant regression, negative-boundary, package, provenance, security, governance, mutation, and seal checks; produce a new unpromoted candidate only after source freeze.
- Record all evidence in the four-file plan set and a coder/supervisor report under `reports/`.

## Non-Goals

- Modifying or reminting `.73`, `.72`, the official `.19` baseline, approval records, or protected governance history.
- Creating a project evaluator by hand in the consumer, copying a hidden source checkout into the consumer, or manufacturing synthetic trial records.
- Changing the project eval schema, policy thresholds, canonical identities, denominator, router, agent model, provider, or unrelated runtime behavior.
- Rebuilding or modifying the v5 artifact, immutable baseline, App Game Truyện, Logistics, or any user project.
- Approval, promotion, finalization, release, deployment, merge, tag, external communication, C43/AERG, or multi-AI QUORUM.
- Treating source-only tests, old C72 claims, stale receipts, or the C73 report as fresh successor lifecycle proof.

## Requirements

1. The installed consumer has exactly one canonical project-eval authority: `.p2p/system/scripts/p2p_eval.py`, installed by the normal package lifecycle.
2. Completion resolution selects the installed helper when `.p2p/system` is present and never falls back to a root or ancestor source checkout if it is absent.
3. Unpacked-package validation remains executable through the package's own `scripts/p2p_eval.py` surface; this is a package validation mode, not an installed-consumer fallback.
4. The project-owned `.p2p/evals/suite.json` remains project data and is created through the documented normal lifecycle; the installer does not fabricate a suite or trial evidence.
5. Every trial records its command, return code, parsed output, evidence hash, environment, and unexpected writes under a disposable target root.
6. The candidate remains `UNPROMOTED_SUCCESSOR_CANDIDATE`; no approval request is made after a failed technical gate, and no approval or promotion action is attempted.
7. Existing correct package/runtime role separation, strict Doctor semantics, canonical identities, and source/official/sealed artifact boundaries remain unchanged.

## Acceptance Criteria

- AC-01: Fresh target worktree is based on the current C72 successor lineage, with owner worktrees and sealed artifacts preserved; exact `.72` and `.73` hashes are recorded before and after.
- AC-02: Root cause is classified as `EVAL_OWNERSHIP_CONTRACT_MISMATCH` / wrong completion resolver, and Option B is recorded from source, installer, and bootstrap evidence.
- AC-03: A clean installed consumer created by the normal packaged lifecycle exposes the canonical project-eval helper at `.p2p/system/scripts/p2p_eval.py`; no hand-copy or ancestor fallback is used.
- AC-04: The project-owned suite is designed/reused and validates with the canonical installed helper; missing installed helper fails closed.
- AC-05: All ten required trial slots (five cases, baseline/P2P, two trials per variant) execute with real command output, zero unexpected writes, and complete trial records.
- AC-06: `p2p_eval gate` passes the completed suite with zero case regressions and policy thresholds intact.
- AC-07: Strict installed Doctor passes and `p2p_gate prepare` passes technically with exact successor subject and `.72` rollback hashes; approval remains not requested.
- AC-08: Direct evaluator tests, full unit/regression suites, negative boundary checks, package verification, and mutation/security checks pass or are explicitly disclosed as unavailable.
- AC-09: Candidate ZIP inventory/checksum/source/tree binding is complete; official `.19`, `.72`, `.73`, approvals, and unrelated projects are unchanged.
- AC-10: Final independent supervisor review returns `PASS`; the terminal handoff is exactly `P2P_EVAL_LIFECYCLE_SUCCESSOR_HANDOFF_SEALED_READY_FOR_INDEPENDENT_REVIEW` and the successor remains unpromoted.

## Checklist

- [x] P0-A: Complete actual status before implementation work.
  - Goal: establish the real current state.
  - Work Steps: inspect source-of-truth files, classify each surface, record blocked or missing pieces, and update later phase status assumptions, next actions, and work steps from evidence.
  - Implementation Gate: no implementation or editing starts until `docs/plans/2026-08-22-p2p-c74-successor-eval-lifecycle-01/2026-08-22-p2p-c74-successor-eval-lifecycle-01-actual-status.md` has a final P0 decision.
  - Acceptance: actual status identifies correct, partial, missing/unbound, fake-or-stub, and blocked surfaces for this scope.

### P1: Correct the canonical completion resolver

- Phase Goal: make the completion oracle use the installed project-eval helper in a consumer while preserving package/source validation and fail-closed ownership.
- Phase Boundary:
  - In scope: `scripts/p2p_eval.py` completion path and direct behavior tests.
  - Out of scope: installer redesign, suite schema/policy changes, UIUX helper behavior, and unrelated package/gov changes.
  - Dependencies: P0 Option B decision, fresh Anvien impact, and no unresolved authority blocker.
- Phase Implementation Rule: do not implement `P1` directly. Implement `P1-A`, verify it, record evidence, refresh actual-status, commit when required, then continue to `P1-B`.
- Ordered Slice List:
  - P1-A: Route completion to installed canonical project-eval helper.
  - P1-B: Add direct installed/package/fail-closed lifecycle coverage.

- [x] P1-A: Route completion to installed canonical project-eval helper.
  - Goal: correct the one wrong path selection without weakening the evaluator contract.
  - Scope Boundary:
    - Editable: `scripts/p2p_eval.py` `_case_command` and the smallest resolver logic required by it.
    - Inspect-only: `scripts/p2p_workflow.py`, `scripts/p2p_gate.py`, `scripts/doctor.py`, installer scripts, package builder, bootstrap/adoption docs.
    - Preserve-only: UIUX runtime evaluator, suite schema/policy, all artifacts and governance.
    - Out of scope: new evaluator copies, root consumer scripts, schema changes, and fallback discovery.
  - Non-Goals: making the installed UIUX helper masquerade as project-eval; changing trial execution, grading, or write auditing.
  - Pre-flight Questions:
    - Data source: `scripts/p2p_eval.py`, installer scripts, `P2P-PROJECT-BOOTSTRAP.md`, `project-adoption-lifecycle.md`, and C73 rejection.
    - Display permission: N/A; CLI path resolution only.
    - DB read flow: N/A; suite JSON is read-only input during completion validation.
    - DB write flow: N/A; no persistent write in the resolver.
    - Render location: N/A; command argv and error output.
    - UI behavior flow: N/A; non-UI CLI contract.
    - Docker runtime: N/A; no Docker target exists for this Python CLI package.
    - Playwright target: N/A; no browser surface.
    - Behavior test: completion command path, package-mode path, and installed-missing-helper failure.
    - Cleanup/quarantine: only in-memory/temp test roots under repo-local `.tmp`.
    - External side effects: none.
    - N/A notes: release mint and fresh lifecycle are separate P2 slices.
  - Work Steps:
    1. Edit only the completion resolver after recording Anvien file-detail and CRITICAL impact evidence.
       - UI flow check: N/A; CLI-only.
       - DB/data flow check: confirm suite path is unchanged and no suite writes occur.
       - Render location check: confirm returned argv points to the selected helper.
       - Mini QA for each completed implementation slice (MUST)
          For Codex: When Mini QA must use plugins
            - Browser: Control the in-app browser
            - Chrome: Control the user's real Chrome browser
            - Computer Use: Control Windows apps or installed artifacts when mini QA requires real app interaction outside a browser.
            - Playwright: use as an automation arm for browser actions, control sweeps, screenshots, videos, traces, and reports.
          For Claude or other agents:
            - Use the equivalent browser, Chrome/session, or computer-control capability exposed by that agent/runtime or Playwright-like capability available in that environment.
       - Evidence target: `E1-P1A-ROUTE1`, `E1-P1A-DETECT1`.
    2. Run syntax and focused source-level checks, then refresh actual-status before the test slice.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: error remains visible and fail-closed when the installed helper is missing.
       - Mini QA for each completed implementation slice (MUST)
          For Codex: When Mini QA must use plugins
            - Browser: Control the in-app browser
            - Chrome: Control the user's real Chrome browser
            - Computer Use: Control Windows apps or installed artifacts when mini QA requires real app interaction outside a browser.
            - Playwright: use as an automation arm for browser actions, control sweeps, screenshots, videos, traces, and reports.
          For Claude or other agents:
            - Use the equivalent browser, Chrome/session, or computer-control capability exposed by that agent/runtime or Playwright-like capability available in that environment.
       - Evidence target: `E1-P1A-SYNTAX1`, `E1-P1A-STATUS1`.
  - Implementation Gate:
    - Before editing target files, run the relevant Anvien impact/file-detail command for files, symbols, routes, tools, or contracts touched by this slice, and record the evidence IDs.
    - The installed-package contract is confirmed by the normal installer copy list and the bootstrap/adoption commands; no source-checkout fallback is acceptable.
  - Acceptance:
    - Source: installed consumer selects `.p2p/system/scripts/p2p_eval.py`; package validation still selects `scripts/p2p_eval.py` only when no installed runtime exists.
    - Runtime/UI: N/A; CLI argv is the observable runtime behavior.
    - DB/data: suite argument remains `.p2p/evals/suite.json` and no data ownership changes.
    - Behavior test: focused route checks pass and missing installed helper raises a visible `ValueError`.
    - Cleanup/quarantine: no target-root writes from resolver tests.
    - Evidence IDs: `E1-P1A-ROUTE1..E1-P1A-STATUS1`.
    - Actual-status rows refreshed: installed resolver transitions `wrong -> correct`; package fallback remains `correct/preserve-only`.
  - Evidence Targets: `E1-P1A-ROUTE1`, `E1-P1A-SYNTAX1`, `E1-P1A-DETECT1`.
  - Actual-status Update: record the exact changed lines, selected path contract, and focused check result before P1-B.
  - Commit Boundary: commit after this slice when acceptance passes.

- [x] P1-B: Add direct installed/package/fail-closed lifecycle coverage.
  - Goal: prevent regression of the ownership boundary with behavior-focused tests.
  - Scope Boundary:
    - Editable: `tests/test_p2p_project_eval.py` only.
    - Inspect-only: existing test fixture suite and package lifecycle tests.
    - Preserve-only: current suite data and all source/runtime files after P1-A.
    - Out of scope: synthetic ten-trial proof and package mint.
  - Non-Goals: tests that merely assert a string or duplicate the implementation without a target layout.
  - Pre-flight Questions:
    - Data source: P1-A resolver and real target layout semantics.
    - Display permission: N/A.
    - DB read flow: temporary target layout only.
    - DB write flow: test-created files are quarantined under `.tmp` and removed by context cleanup.
    - Render location: assertion on command argv/error.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: installed runtime wins; package source works; installed absence does not fall back to root.
    - Cleanup/quarantine: `TemporaryDirectory(dir=repo/.tmp)`.
    - External side effects: none.
    - N/A notes: no browser or database.
  - Work Steps:
    1. Add target-layout tests after P1-A code is correct.
       - UI flow check: N/A.
       - DB/data flow check: assert no persistent repo data is touched.
       - Render location check: command path and error text are observable outputs.
       - Mini QA for each completed implementation slice (MUST)
          For Codex: When Mini QA must use plugins
            - Browser: Control the in-app browser
            - Chrome: Control the user's real Chrome browser
            - Computer Use: Control Windows apps or installed artifacts when mini QA requires real app interaction outside a browser.
            - Playwright: use as an automation arm for browser actions, control sweeps, screenshots, videos, traces, and reports.
          For Claude or other agents:
            - Use the equivalent browser, Chrome/session, or computer-control capability exposed by that agent/runtime or Playwright-like capability available in that environment.
       - Evidence target: `E1-P1B-TEST1`.
    2. Run the focused test file and full Python unit suite.
       - UI flow check: N/A.
       - DB/data flow check: verify temp cleanup and unchanged tracked source outside the intended files.
       - Render location check: test report and command output retained in repo-local reports.
       - Mini QA for each completed implementation slice (MUST)
          For Codex: When Mini QA must use plugins
            - Browser: Control the in-app browser
            - Chrome: Control the user's real Chrome browser
            - Computer Use: Control Windows apps or installed artifacts when mini QA requires real app interaction outside a browser.
            - Playwright: use as an automation arm for browser actions, control sweeps, screenshots, videos, traces, and reports.
          For Claude or other agents:
            - Use the equivalent browser, Chrome/session, or computer-control capability exposed by that agent/runtime or Playwright-like capability available in that environment.
       - Evidence target: `E1-P1B-TEST2`, `E1-P1B-DETECT1`.
  - Implementation Gate:
    - P1-A committed and actual-status refreshed; test target impact is recorded; tests use disposable repo-local roots.
    - No test hand-copies a helper into the installed consumer as a substitute for normal installation.
  - Acceptance:
    - Source: tests exercise the real `_case_command` behavior.
    - Runtime/UI: N/A.
    - DB/data: temporary files only and cleanup proven.
    - Behavior test: scoped project-eval tests pass; repository-wide baseline failures are compared and explicitly disclosed rather than treated as successor regressions.
    - Cleanup/quarantine: no `.tmp` test residue outside explicitly ignored disposable roots.
    - Evidence IDs: `E1-P1B-TEST1..E1-P1B-FULL1`, `E1-P1B-DETECT1`.
    - Actual-status rows refreshed: test coverage transitions `missing -> correct`; repository-wide non-green baseline is recorded as a limitation.
  - Evidence Targets: `E1-P1B-TEST1`, `E1-P1B-TEST2`, `E1-P1B-DETECT1`.
  - Actual-status Update: record test counts, unchanged protections, and any plan adjustment before P2.
  - Commit Boundary: commit after this slice when scoped acceptance passes; repository-wide baseline failures remain disclosed in the evidence ledger.

### P2: Prove clean installed lifecycle and seal a successor

- Phase Goal: prove the corrected contract at the real package/install boundary and preserve all protected identities.
- Phase Boundary:
  - In scope: fresh package build, consumer install/adoption, ten trial slots, gates, regressions, security, provenance, and new candidate seal.
  - Out of scope: approval, promotion, release, deployment, external certification, and unrelated project runtime.
  - Dependencies: P1 commits, full build, and fresh candidate-only output paths under `.tmp`.
- Phase Implementation Rule: P2 is evidence work split into independently checked lifecycle and closure slices; no direct source changes are allowed in P2 unless a new P1 plan decision is recorded.
- Ordered Slice List:
  - P2-A: Fresh packaged consumer lifecycle and ten trial slots.
  - P2-B: Regression, package/provenance/security closure, and candidate seal.

- [ ] P2-A: Fresh packaged consumer lifecycle and ten trial slots.
  - Goal: reproduce the installed project lifecycle from a clean consumer without hand-copy or source dependency.
  - Scope Boundary:
    - Editable: disposable consumer and evidence/report files under target `.tmp` only.
    - Inspect-only: package source and installer behavior.
    - Preserve-only: all source commits and sealed artifacts.
    - Out of scope: approval and promotion.
  - Non-Goals: fabricating eval records or using historical C72 5/5 evidence.
  - Pre-flight Questions:
    - Data source: fresh successor candidate and project-owned suite design.
    - Display permission: N/A.
    - DB read flow: installed helper reads consumer `.p2p/evals/suite.json`.
    - DB write flow: trial evidence/records only in disposable consumer.
    - Render location: report JSON/MD under `reports/` and plan evidence.
    - UI behavior flow: N/A.
    - Docker runtime: N/A; Python package lifecycle.
    - Playwright target: N/A.
    - Behavior test: design, validate, run ten slots, record, summarize, gate.
    - Cleanup/quarantine: fresh consumer under repo-local `.tmp`; no user project.
    - External side effects: none; no network or cloud connector.
    - N/A notes: provider-neutral deterministic local runner only.
  - Work Steps:
    1. Build and verify a new unpromoted package, install it through the canonical packaged path, and record exact hashes/pin/Doctor.
       - UI flow check: N/A.
       - DB/data flow check: verify project-local `.p2p` state and no source checkout path in command argv.
       - Render location check: candidate identity, install evidence, and strict Doctor reports.
       - Mini QA for each completed implementation slice (MUST)
          For Codex: When Mini QA must use plugins
            - Browser: Control the in-app browser
            - Chrome: Control the user's real Chrome browser
            - Computer Use: Control Windows apps or installed artifacts when mini QA requires real app interaction outside a browser.
            - Playwright: use as an automation arm for browser actions, control sweeps, screenshots, videos, traces, and reports.
          For Claude or other agents:
            - Use the equivalent browser, Chrome/session, or computer-control capability exposed by that agent/runtime or Playwright-like capability available in that environment.
       - Evidence target: `E2-P2A-PACKAGE1`, `E2-P2A-INSTALL1`.
    2. Design/reuse the suite through normal setup, execute exactly ten slots, record evidence, and run gate/Doctor/prepare.
       - UI flow check: N/A.
       - DB/data flow check: every command uses consumer-local suite/evidence; unexpected writes are zero.
       - Render location check: retain trial records, summary, eval gate, Doctor, and prepare reports.
       - Mini QA for each completed implementation slice (MUST)
          For Codex: When Mini QA must use plugins
            - Browser: Control the in-app browser
            - Chrome: Control the user's real Chrome browser
            - Computer Use: Control Windows apps or installed artifacts when mini QA requires real app interaction outside a browser.
            - Playwright: use as an automation arm for browser actions, control sweeps, screenshots, videos, traces, and reports.
          For Claude or other agents:
            - Use the equivalent browser, Chrome/session, or computer-control capability exposed by that agent/runtime or Playwright-like capability available in that environment.
       - Evidence target: `E2-P2A-EVAL1`, `E2-P2A-GATE1`.
  - Implementation Gate:
    - P1 source/tests are committed; candidate output is new; `.72` and `.73` hashes are captured; no approval commands are scheduled.
    - The consumer is disposable and the canonical installer, not a hand-copy, creates the installed helper.
  - Acceptance:
    - Source: new candidate binds to the post-P1 source commit/tree.
    - Runtime/UI: clean installed runtime resolves the helper and strict Doctor passes.
    - DB/data: ten trial records are complete and no unexpected writes occur.
    - Behavior test: eval gate and technical prepare pass.
    - Cleanup/quarantine: disposable consumer and temporary stage remain under repo `.tmp`; user/root worktrees untouched.
    - Evidence IDs: `E2-P2A-PACKAGE1..E2-P2A-GATE1`.
    - Actual-status rows refreshed: installed lifecycle `partial/wrong -> correct` only after fresh proof.
  - Evidence Targets: `E2-P2A-PACKAGE1`, `E2-P2A-INSTALL1`, `E2-P2A-EVAL1`, `E2-P2A-GATE1`.
  - Actual-status Update: record final consumer paths, ten-slot counts, gate outcomes, and exact technical report hashes.
  - Commit Boundary: evidence-only updates may be committed with P2-B after source is frozen; do not amend source commits.

- [ ] P2-B: Regression, package/provenance/security closure, and candidate seal.
  - Goal: prove no protected regression and produce a new sealed-but-unpromoted successor handoff.
  - Scope Boundary:
    - Editable: new candidate/report/evidence outputs and plan files only.
    - Inspect-only: `.72`, `.73`, official `.19`, approvals, and unrelated worktrees.
    - Preserve-only: existing sealed bytes and historical reports.
    - Out of scope: promotion, approval, release, deployment, and external communication.
  - Non-Goals: optional hardening after PASS.
  - Pre-flight Questions:
    - Data source: source commit, candidate ZIP, clean extraction, regression harness, governance drift.
    - Display permission: N/A.
    - DB read flow: N/A; package and source evidence only.
    - DB write flow: only new candidate/report outputs.
    - Render location: `reports/`, plan ledgers, candidate output under `.tmp`.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: capability/full unit, negative/security, package verify, mutation audit, drift, seal.
    - Cleanup/quarantine: keep only accepted plan/report/candidate artifacts; remove dead intermediate outputs created by this plan.
    - External side effects: none.
    - N/A notes: external Manus/C43/AERG lanes are disclosed only.
  - Work Steps:
    1. Run full build, Anvien detect-changes, regression/negative/security/package/drift/mutation checks, and compare protected hashes.
       - UI flow check: N/A.
       - DB/data flow check: no user or protected project writes.
       - Render location check: reports and benchmark ledger contain exact measured counts.
       - Mini QA for each completed implementation slice (MUST)
          For Codex: When Mini QA must use plugins
            - Browser: Control the in-app browser
            - Chrome: Control the user's real Chrome browser
            - Computer Use: Control Windows apps or installed artifacts when mini QA requires real app interaction outside a browser.
            - Playwright: use as an automation arm for browser actions, control sweeps, screenshots, videos, traces, and reports.
          For Claude or other agents:
            - Use the equivalent browser, Chrome/session, or computer-control capability exposed by that agent/runtime or Playwright-like capability available in that environment.
       - Evidence target: `E2-P2B-REG1`, `E2-P2B-SEC1`, `E2-P2B-DETECT1`.
    2. Record the candidate identity, exact ZIP hash, source binding, unpromoted state, and final handoff report; do not request approval.
       - UI flow check: N/A.
       - DB/data flow check: confirm no protected state was rewritten.
       - Render location check: final report and terminal verdict are self-contained.
       - Mini QA for each completed implementation slice (MUST)
          For Codex: When Mini QA must use plugins
            - Browser: Control the in-app browser
            - Chrome: Control the user's real Chrome browser
            - Computer Use: Control Windows apps or installed artifacts when mini QA requires real app interaction outside a browser.
            - Playwright: use as an automation arm for browser actions, control sweeps, screenshots, videos, traces, and reports.
          For Claude or other agents:
            - Use the equivalent browser, Chrome/session, or computer-control capability exposed by that agent/runtime or Playwright-like capability available in that environment.
       - Evidence target: `E2-P2B-SEAL1`.
  - Implementation Gate:
    - P2-A is technically PASS; all protected artifact hashes remain exact; source tree is frozen before mint.
    - A failed technical gate stops the task with a truthful blocker and no approval request.
  - Acceptance:
    - Source: package source/tree binding is verified and candidate is unpromoted.
    - Runtime/UI: N/A; real CLI/package evidence is complete.
    - DB/data: mutation audit shows no protected target changed.
    - Behavior test: regressions and negative/security gates pass or are explicitly disclosed.
    - Cleanup/quarantine: no dead plan-created artifacts remain in final diff.
    - Evidence IDs: `E2-P2B-REG1..E2-P2B-SEAL1`.
    - Actual-status rows refreshed: candidate `unbound -> bound-correct`; protected artifacts remain `correct/preserve-only`.
  - Evidence Targets: `E2-P2B-REG1`, `E2-P2B-SEC1`, `E2-P2B-DETECT1`, `E2-P2B-SEAL1`.
  - Actual-status Update: append final source/candidate/approval boundary and supervisor handoff state.
  - Commit Boundary: commit only the accepted source/evidence/plan scope; never amend or rewrite sealed candidate bytes.

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

- The target evaluator file has a CRITICAL Anvien impact warning and a large unresolved inventory; the edit is intentionally limited to one branch in `_case_command`, with direct layout tests and full regression.
- The worktree has pre-existing CRLF/LF status noise across tracked documentation/skill files. Those files are not part of this task and must not be staged; only intended paths may enter commits.
- The C73 report is an independent blocker report, not proof of the successor. Fresh consumer evidence is mandatory.
- A technical PASS does not authorize approval or promotion. The successor remains unpromoted and requires a separate independent review/Owner process.
