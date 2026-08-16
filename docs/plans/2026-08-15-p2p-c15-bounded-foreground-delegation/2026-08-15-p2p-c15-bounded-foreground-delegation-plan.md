# P2P-C15 Bounded Foreground Delegation & Worker Handoff Controller Plan

## Metadata

- Date: `2026-08-15`
- Status: `PASS / BOUNDED_DELEGATION_FOUNDATION_READY`
- Plan: `docs/plans/2026-08-15-p2p-c15-bounded-foreground-delegation/2026-08-15-p2p-c15-bounded-foreground-delegation-plan.md`
- Evidence: `docs/plans/2026-08-15-p2p-c15-bounded-foreground-delegation/2026-08-15-p2p-c15-bounded-foreground-delegation-evidence.md`
- Benchmark: `docs/plans/2026-08-15-p2p-c15-bounded-foreground-delegation/2026-08-15-p2p-c15-bounded-foreground-delegation-benchmark.md`
- Actual status: `docs/plans/2026-08-15-p2p-c15-bounded-foreground-delegation/2026-08-15-p2p-c15-bounded-foreground-delegation-actual-status.md`

## Goal

Implement the smallest truthful C15 capability: a bounded foreground delegation controller that chooses `DIRECT`, `DELEGATE`, or `BLOCKED` deterministically before execution-class/profile selection; emits one narrow, fingerprinted child handoff; runs at most one real foreground child at depth one when the host provides a supported execution surface; and requires independent parent verification before the existing C11 task can become `DONE`.

## Rules

- Complete P0 actual status before implementation work.
- Update every checklist item immediately when it is completed and refresh actual status after every slice.
- Use the existing C11 task state, C10 evidence, C10 decision trace, C06 context, trust boundary, and C12 foreground execution primitives; do not create a second router, executor, ledger, or evidence system.
- Keep `DIRECT` first-class and preserve the existing C12 direct-only contract unless a focused compatibility change is proven necessary.
- Never delegate for a tiny/coherent task without material expected value; never choose a model/profile/execution class before the strategy decision.
- Enforce one child, depth one, no grandchildren, no parallelism, no background execution, no scheduler, no queue, no remote bridge, and no implicit host permission expansion.
- A child permission and scope envelope must be an explicit subset of the parent. Missing proof is `BLOCKED`, not an inferred grant.
- Worker output is a proposal. The parent independently verifies current candidate state and evidence before C11 completion.
- Preserve explicit `UNKNOWN` identity. Generic identity-not-required work may continue with `UNKNOWN`; identity-required work blocks without supported host proof.
- Retry only bounded transient, non-mutating child failures. Do not retry stale, permission, owner, scope, identity, unsupported, control-plane, or uncertain-mutation failures.
- Keep C09 at `BLOCKED / EVENT_EVIDENCE_UNAVAILABLE`, C08 at `DEFERRED`, and canonical quorum at exactly eight identities. AESTHETICA remains optional/noncanonical.
- The official `8.4.7-C-codex.19` artifact and its SHA-256 remain immutable and are not promoted or overwritten by this task.
- Use Anvien impact/file-detail before editing and detect-changes before each required commit. The repository has no `.git`, so commit evidence may be explicitly recorded as unavailable; do not initialize Git.
- This is a local Python runtime change, not a browser/UI app. Docker, browser, and Playwright checks are `N/A` unless the repository exposes a real app runtime; the nearest real boundary is the CLI/controller plus isolated filesystem state.

## Problem

C11 already provides durable task records, preflight, transition, checkpoint, resume, and completion gates. C12 provides bounded direct foreground execution and independent verification. The current system deliberately has no delegation path, so it cannot make a truthful bounded worker handoff when isolation or specialist analysis has material expected value. Adding an unconstrained worker would violate the existing safety boundaries; omitting the path leaves C15 incomplete. The change must therefore be additive, deterministic, and fail closed.

## Scope

- Add one capability module under `.p2p/system/p2p_capabilities/` containing the strategy decision, narrow handoff contract, permission/scope subset checks, deterministic fingerprint, bounded child result, and parent-controlled verification flow.
- Reuse `TaskStateStore`/`TaskPlan` for task readiness and completion, `ForegroundExecutionController` for the direct path and its finite execution semantics, `EvidenceClaim`/`VerificationResult` for independent proof, and the existing Execution Ledger/artifact area for durable receipts.
- Add a thin supported CLI surface for inspect/decide/handoff/run/verify behavior without exposing shell, network, scheduler, or profile-selection controls.
- Wire the new runtime module into the capability package exports, package-release allowlist, doctor required-runtime inventory, and focused tests.
- Add isolated behavioral coverage for decision ordering, direct-first policy, delegation eligibility, subset and fingerprint checks, identity handling, one-child/depth bounds, result-versus-evidence separation, retry/fallback boundaries, uncertain mutation, stale state, control-plane failure, package/doctor inventory, and preservation of existing C11/C12 behavior.
- Produce an unpromoted candidate package only if the repository packaging gate requires it; never overwrite the official `.19` artifact.

## Non-Goals

- No change to C09 host event trust, C08 route-profile activation, canonical identities, quorum denominator, or official release promotion.
- No second router, second executor, model/profile resolver, provider bridge, remote transport, background worker, scheduler, queue, fan-out, parallel child, or nested delegation.
- No automatic retry on boundary failures and no blind direct fallback after uncertain or partial mutation.
- No new permissions, network access, hooks, proxying, connectors, persistent memory, or external communication.
- No Knowledge Delta 2.0, UX redesign, unrelated cleanup, or broad refactoring of the high-risk C12 module.

## Requirements

1. `DIRECT`, `DELEGATE`, and `BLOCKED` are explicit result states and are selected before any execution class/profile/model lookup.
2. Policy input is typed/validated and records why delegation has material expected value; absent value reasons resolve to `DIRECT` or `BLOCKED` according to readiness, not to delegation.
3. Handoff data contains only task purpose, scope/non-scope, acceptance, dependencies, relevant context/decision pointers, candidate/project fingerprint, permissions, bounded budget, risks/unknowns, and verification expectations; no transcript, secret, guessed identity, or hidden reasoning.
4. Handoff fingerprint is deterministic and binds plan/task/project/candidate/context/permission/scope/acceptance inputs. The parent rejects stale or mismatched handoffs.
5. Child permission names and explicit paths are subsets of the parent; child delegation is always false; one live child and depth one are enforced.
6. Missing supported host child surface returns a truthful unavailable/block state; no simulated child receipt is accepted as runtime evidence.
7. Child identity fields are observed-only. `UNKNOWN` is preserved; identity-required tasks block without proof or with mismatch.
8. Child output is a proposal. Parent verification uses the current candidate binding and actual evidence; only existing C11 completion can produce `DONE`.
9. Only bounded transient/non-mutating failures may retry. Boundary failures do not retry. Uncertain mutation yields `NEEDS_RECHECK`/`UNKNOWN` and suppresses direct fallback.
10. All durable output is written through existing state/artifact and ledger paths with secret-safe projections and no second truth store.

## Acceptance Criteria

- Focused C15 tests pass for all decision branches and failure boundaries, including at least two isolated trials for each paired eval variant where applicable.
- Existing C11 and C12 suites pass unchanged except for intentional C15 compatibility assertions; direct execution remains first-class and its existing deny/verify behavior is preserved.
- Package/doctor validation includes the new runtime module and CLI without mutating the protected official artifact or release baseline.
- Anvien graph is refreshed after edits; detect-changes evidence is recorded before closure. Any HIGH/CRITICAL blast radius is disclosed and scoped.
- Supervisor independently reviews source, tests, reports, generated output, and evidence and returns `PASS`, or the plan stops `BLOCKED`/`REJECT` with the exact reason.
- Final report starts with `CHAT ID: P2P-C15` and `CHAT NAME: Bounded Delegation — Tự quyết DIRECT hay DELEGATE`, then reports the terminal status, completed work, checks, real risks, and the no-Git limitation without claiming release/promotion.

## Checklist

- [x] P0-A: Complete actual status before implementation work.
  - Goal: establish the real current state.
  - Work Steps: inspect source-of-truth files, classify each surface, record blocked or missing pieces, and update later phase status assumptions, next actions, and work steps from evidence.
  - Implementation Gate: actual status has a final P0 decision and evidence IDs.
  - Acceptance: current C11/C12 boundaries, missing C15 surface, packaging surfaces, protected artifact, and no-Git constraint are classified.

### P1: Implement the bounded delegation controller

- Phase Goal: add one additive strategy/handoff/execution adapter while preserving direct execution and existing governance.
- Phase Boundary:
  - In scope: policy decision, handoff schema/fingerprint, subset validation, one-child foreground execution, parent verification, retry/fallback classification, exports, and focused runtime tests.
  - Out of scope: C12 broad refactor, host hook changes, background/remote execution, new routing/model selection, and release promotion.
  - Dependencies: C11 task state, C10 evidence/decision trace, C06 context/trust contracts, and a callable host child surface supplied by the caller.
- Phase Implementation Rule: do not implement `P1` directly. Implement `P1-A`, verify it, refresh actual status, then `P1-B`, then `P1-C`.
- Ordered Slice List:
  - P1-A: Deterministic strategy and handoff contract
  - P1-B: One-child execution and parent verification
  - P1-C: Public exports and focused regression surface

- [x] P1-A: Deterministic strategy and handoff contract
  - Goal: make strategy choice, freshness, scope, permission, identity, and bounded child rules explicit before execution-class/profile selection.
  - Scope Boundary:
    - Editable: new bounded delegation module and its focused unit tests.
    - Inspect-only: C11 task state, C10 evidence/decision trace, C06 context/trust modules, C09/C08 state.
    - Preserve-only: `foreground_execution.py` direct classes and existing C11 schemas.
    - Out of scope: child invocation, host integration, package/release mutation.
  - Non-Goals: no model/profile choice, no shell/network surface, no guessed identity, and no hidden fallback.
  - Pre-flight Questions:
    - Data source: typed request built from `TaskRecord` plus explicit candidate/context/permission snapshots.
    - Display permission: secret-safe projections only; no UI surface.
    - DB read flow: N/A; filesystem state is read through existing C11/C12 stores.
    - DB write flow: N/A; no durable write until a validated handoff is executed.
    - Render location: structured controller/CLI JSON only.
    - UI behavior flow: N/A; local Python control surface.
    - Docker runtime: N/A; no app/container runtime in scope.
    - Playwright target: N/A; no browser surface.
    - Behavior test: policy matrix, subset, stale, fingerprint, and identity tests.
    - Cleanup/quarantine: every test uses a repo-local temporary isolated root and removes/quarantines it after the test.
    - External side effects: none; network and remote bridges remain disabled.
    - N/A notes: `DIRECT` and `BLOCKED` must work without a host child surface.
  - Work Steps:
    1. Add validated enums/dataclasses for strategy, value reasons, permission envelope, handoff, decision, and result-safe fingerprints.
       - UI flow check: N/A; verify JSON fields are the public render surface.
       - DB/data flow check: verify inputs are read-only snapshots and no second state store is introduced.
       - Render location check: verify `to_dict` is secret-safe and contains explicit `UNKNOWN` values.
       - Mini QA: N/A; run focused Python behavior tests at the controller boundary.
       - Evidence target: `E1-P1A-SRC1`, `E1-P1A-TEST1`.
    2. Implement deterministic decision ordering and subset/fingerprint checks, then test direct-first, blocked-first, and delegation eligibility cases.
       - UI flow check: N/A; inspect structured decision output.
       - DB/data flow check: verify stale/owner/permission/scope/identity failures do not write task completion.
       - Render location check: verify reasons and decision trace references are observable.
       - Mini QA: N/A; run the isolated policy matrix.
       - Evidence target: `E1-P1A-TEST2`, `E1-P1A-IMPACT1`.
  - Implementation Gate:
    - Before editing, Anvien file-detail/impact evidence for C11/C12 dependencies is recorded; new module is additive and does not alter protected runtime files.
    - `DIRECT` remains valid when no host child surface exists; `DELEGATE` cannot be returned without explicit material value and a supported surface.
  - Acceptance:
    - Source: typed contract rejects forbidden identity/secrets and serializes deterministic fingerprints.
    - Runtime/UI: N/A; controller decision is the real boundary.
    - DB/data: no write on decision-only paths; no second ledger/store.
    - Behavior test: all policy and boundary cases pass.
    - Cleanup/quarantine: isolated temp roots are cleaned or quarantined.
    - Evidence IDs: `E1-P1A-SRC1..E1-P1A-IMPACT1`.
    - Actual-status rows refreshed: new module `missing -> partial/bound-correct`; C11/C12 `correct -> preserve-only`.
  - Evidence Targets: source diff, focused tests, Anvien impact, secret-safe serialization samples.
  - Actual-status Update: record exact transition and any policy reason discovered by tests.
  - Commit Boundary: commit after acceptance when Git is available; otherwise record commit blocked by missing `.git`.

- [x] P1-B: One-child execution and parent verification
  - Goal: execute one real child handoff through a supplied bounded host callback, persist a proposal receipt, and complete only after independent parent verification.
  - Scope Boundary:
    - Editable: bounded delegation module and its integration tests; minimal C12 compatibility edit only if a test proves it is required.
    - Inspect-only: existing C12 direct action path and C11 completion implementation.
    - Preserve-only: direct execution, existing ledger schema, official artifact, C09/C08.
    - Out of scope: parallel/background/scheduler/remote execution and host hook installation.
  - Non-Goals: no child-created grandchild, no worker self-certification, no retry after uncertain mutation, and no direct fallback after unknown state.
  - Pre-flight Questions:
    - Data source: validated handoff and current parent task state.
    - Display permission: host execution reference and observed identity only; `UNKNOWN` is explicit.
    - DB read flow: N/A; reread current C11/C12 state before parent verification.
    - DB write flow: existing task state/ledger/artifact paths only, after validation gates.
    - Render location: structured handoff/result/verification receipt.
    - UI behavior flow: N/A; callable child surface is the runtime boundary.
    - Docker runtime: N/A; local Python runtime.
    - Playwright target: N/A.
    - Behavior test: success, proposal-only, stale, identity, retry, uncertain mutation, and fallback matrix.
    - Cleanup/quarantine: child callback writes only to an isolated disposable root; receipts stay in the test root.
    - External side effects: callback is injected and bounded; no unrestricted subprocess or network.
    - N/A notes: real host probe is optional and only valid if the host exposes a supported child callback; otherwise record unavailable.
  - Work Steps:
    1. Add bounded child invocation with an in-flight child counter, depth/child-delegation guards, freshness recheck, permission/scope subset checks, and host reference fields.
       - UI flow check: N/A; inspect the result JSON.
       - DB/data flow check: verify handoff and proposal are durable through the existing execution artifact/ledger path.
       - Render location check: verify one child, depth one, no background/parallel flags.
       - Mini QA: N/A; run callback-backed integration tests.
       - Evidence target: `E1-P1B-EXEC1`, `E1-P1B-TEST1`.
    2. Add parent independent verification, C11 completion gating, retry/fallback classification, and uncertain-mutation handling.
       - UI flow check: N/A; verification receipt is the observable output.
       - DB/data flow check: verify only verified evidence can transition to `DONE`; uncertain mutation becomes `NEEDS_RECHECK`/`UNKNOWN`.
       - Render location check: verify worker output is marked proposal, not evidence.
       - Mini QA: N/A; run the full C15 execution matrix.
       - Evidence target: `E1-P1B-VERIFY1`, `E1-P1B-TEST2`.
  - Implementation Gate:
    - Anvien impact for any touched C12/C11 symbol is rerun immediately before editing; no host callback is accepted unless it is explicitly supplied by the caller.
    - No child completion can call C11 `complete` without a parent verification result containing fresh evidence claims.
  - Acceptance:
    - Source: one-child/depth-one guards and no hidden executor/router are visible in the contract.
    - Runtime/UI: N/A; callback -> receipt -> verification -> task state is the real flow.
    - DB/data: task remains active/needs recheck on proposal-only or uncertain outcomes; only verified evidence yields `DONE`.
    - Behavior test: success, unavailable, stale, identity, retry, boundary failure, and fallback cases pass.
    - Cleanup/quarantine: isolated callback state is removed/quarantined.
    - Evidence IDs: `E1-P1B-EXEC1..E1-P1B-TEST2`.
    - Actual-status rows refreshed: new module `partial -> bound-correct` if all gates pass; C11/C12 remain preserve-only.
  - Evidence Targets: execution receipts, ledger tail, task-state projection, verification claims, focused integration tests.
  - Actual-status Update: record whether host binding is `available` or `unsupported/unknown`; never infer identity.
  - Commit Boundary: commit after acceptance when Git is available; otherwise record the repository limitation.

- [x] P1-C: Public exports and focused regression surface
  - Goal: expose the capability through the supported package/CLI surfaces and prove C11/C12/canonical preservation.
  - Scope Boundary:
    - Editable: package exports, thin delegation CLI, package/doctor inventories, focused tests.
    - Inspect-only: release ZIP and historical source baselines.
    - Preserve-only: official `.19` artifact, manifest baseline, C09/C08/canonical registry.
    - Out of scope: release promotion, installing external dependencies, or changing version facts.
  - Non-Goals: no broad CLI redesign and no generic agent simulation.
  - Pre-flight Questions:
    - Data source: new controller and existing C11/C12 stores.
    - Display permission: JSON only, secret-safe.
    - DB read flow: N/A; filesystem state.
    - DB write flow: existing isolated state paths.
    - Render location: CLI stdout and reports.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: CLI, package inventory, doctor, C11/C12 regression.
    - Cleanup/quarantine: CLI tests use repo-local disposable roots.
    - External side effects: none.
    - N/A notes: full candidate packaging is a separate P2 slice.
  - Work Steps:
    1. Wire exports, CLI, package-release allowlist, and doctor required paths; verify help/inspect/decision output.
       - UI flow check: N/A; CLI JSON is the public surface.
       - DB/data flow check: verify CLI uses existing state roots and does not create a second store.
       - Render location check: verify no worker/model identity is guessed in output.
       - Mini QA: N/A; run CLI subprocess tests.
       - Evidence target: `E1-P1C-CLI1`.
    2. Run focused C11/C12 and registry regression tests, then refresh graph evidence.
       - UI flow check: N/A.
       - DB/data flow check: verify old task and direct execution semantics remain intact.
       - Render location check: verify package/doctor inventory includes the module.
       - Mini QA: N/A; nearest real runtime is the test/CLI boundary.
       - Evidence target: `E1-P1C-REG1`, `E1-P1C-GRAPH1`.
  - Implementation Gate:
    - Package/doctor changes are limited to allowlisting the new source and CLI; official artifact and baseline files are not targets.
  - Acceptance:
    - Source: imports and CLI are valid.
    - Runtime/UI: CLI behavior is observable and passes.
    - DB/data: existing C11/C12 state flow passes regression.
    - Behavior test: focused plus prior suites pass.
    - Cleanup/quarantine: disposable CLI roots are cleaned/quarantined.
    - Evidence IDs: `E1-P1C-CLI1..E1-P1C-GRAPH1`.
    - Actual-status rows refreshed: package/doctor `partial -> correct` for C15 inventory.
  - Evidence Targets: CLI output, test results, package/doctor validation, graph refresh.
  - Actual-status Update: record any generated-file or package lock changes as in-scope or revert them if not required.
  - Commit Boundary: commit after acceptance when Git is available; otherwise record no-Git limitation.

### P2: Regression, packaging, and lifecycle evidence

- Phase Goal: validate the complete C15 slice at the nearest real boundaries and preserve release/governance constraints.
- Phase Boundary:
  - In scope: paired evals, full Python build/test/doctor validation, candidate package if needed, official artifact hash check, and evidence reports.
  - Out of scope: release approval, promotion, deployment, host hook changes, and optional hardening after PASS.
  - Dependencies: all P1 slices pass and actual status is refreshed.
- Phase Implementation Rule: do not implement `P2` directly. Implement `P2-A`, then `P2-B`.
- Ordered Slice List:
  - P2-A: C15 paired regression/eval matrix
  - P2-B: Package candidate and lifecycle validation

- [x] P2-A: C15 paired regression/eval matrix
  - Goal: prove behavior with isolated positive, negative, stale, injection, identity, evidence, and boundary cases.
  - Scope Boundary:
    - Editable: C15 tests/eval fixtures and evidence only.
    - Inspect-only: source modules after P1.
    - Preserve-only: official artifact, baseline release, C09/C08.
    - Out of scope: feature changes not caused by a failing mandatory case.
  - Non-Goals: no benchmark optimization or full-quorum simulation.
  - Pre-flight Questions:
    - Data source: frozen task/candidate/context/permission fixtures.
    - Display permission: test outputs are scrubbed of secrets.
    - DB read flow: N/A; isolated JSON state.
    - DB write flow: test roots only; cleanup/quarantine required.
    - Render location: test reports/evidence.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: at least two trials per paired variant.
    - Cleanup/quarantine: reject protected roots and clean `.tmp` fixtures.
    - External side effects: none.
    - N/A notes: no host identity claim without real receipt.
  - Work Steps:
    1. Run project-specific C15 evals with frozen hashes and isolated roots.
       - UI flow check: N/A.
       - DB/data flow check: verify no protected root mutation and correct task-state transitions.
       - Render location check: verify evidence/report fields are traceable.
       - Mini QA: N/A.
       - Evidence target: `E2-P2A-EVAL1`.
    2. Run full affected Python tests, doctor, governance/registry checks, and inspect the official artifact hash.
       - UI flow check: N/A.
       - DB/data flow check: verify existing ledgers and release files are not overwritten.
       - Render location check: verify report paths and evidence IDs.
       - Mini QA: N/A.
       - Evidence target: `E2-P2A-REG1`, `E2-P2A-PROTECT1`.
  - Implementation Gate:
    - Any failing mandatory behavior returns to the responsible slice only; no optional hardening starts.
  - Acceptance:
    - Source: no unexplained test-only bypasses.
    - Runtime/UI: N/A.
    - DB/data: fixture state transitions and cleanup pass.
    - Behavior test: paired eval and affected suites pass.
    - Cleanup/quarantine: protected-root rejection passes.
    - Evidence IDs: `E2-P2A-EVAL1..E2-P2A-PROTECT1`.
    - Actual-status rows refreshed: test/eval surfaces `partial -> correct` or blocker recorded.
  - Evidence Targets: eval JSON/MD, unittest output, doctor output, artifact hash.
  - Actual-status Update: refresh mandatory status and residual risks.
  - Commit Boundary: validation-only; no commit if no source changes.

- [x] P2-B: Package candidate and lifecycle validation
  - Goal: validate that the new module can be packaged without touching the official release.
  - Scope Boundary:
    - Editable: generated candidate output under repo-local `.tmp/p2p-c15/candidates/` only if packaging requires it.
    - Inspect-only: `D:/AI/P2P_dev/P2P-8.4.7-C-Codex-Edition-v19.zip`.
    - Preserve-only: official `.19` file/hash and immutable baselines.
    - Out of scope: approval, finalization, promotion, or publishing.
  - Non-Goals: no version bump inferred from the user request and no release artifact overwrite.
  - Pre-flight Questions:
    - Data source: source package and package-release allowlist.
    - Display permission: hashes and inventory only.
    - DB read flow: N/A.
    - DB write flow: candidate ZIP/temp state only; cleanup after hash capture if not retained as evidence.
    - Render location: package/doctor reports.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: package build/validate and doctor.
    - Cleanup/quarantine: candidate is repo-local, uniquely named, and never replaces official artifact.
    - External side effects: none.
    - N/A notes: release gate remains unrequested and unexecuted.
  - Work Steps:
    1. Run the full package validation/build command required by the repository and record candidate path/hash.
       - UI flow check: N/A.
       - DB/data flow check: verify generated state remains scoped to candidate/package validation.
       - Render location check: verify package inventory lists C15 module/CLI.
       - Mini QA: N/A.
       - Evidence target: `E2-P2B-PKG1`.
    2. Run final doctor/drift/Anvien detect-changes checks and verify official `.19` hash unchanged.
       - UI flow check: N/A.
       - DB/data flow check: verify no protected baseline mutation.
       - Render location check: verify final evidence/report paths.
       - Mini QA: N/A.
       - Evidence target: `E2-P2B-CLOSE1`, `E2-P2B-PROTECT1`.
  - Implementation Gate:
    - Stop at candidate validation. No approval or promotion command is allowed in this plan.
  - Acceptance:
    - Source: package validates with required runtime target present.
    - Runtime/UI: N/A.
    - DB/data: no protected mutation.
    - Behavior test: package/doctor/drift checks pass or a real environment blocker is recorded.
    - Cleanup/quarantine: candidate path/hash is recorded and official file is unchanged.
    - Evidence IDs: `E2-P2B-PKG1..E2-P2B-PROTECT1`.
    - Actual-status rows refreshed: candidate lifecycle classified as `correct`, `blocked`, or `deferred` without promotion.
  - Evidence Targets: candidate archive/hash, doctor, drift, detect-changes, official hash.
  - Actual-status Update: record package/lifecycle result and no-Git limitation.
  - Commit Boundary: no release commit; repository has no Git metadata.

- [x] Pn-A: Call supervisor for the implemented-plan acceptance loop.
  - Goal: verify completed C15 work independently against this plan, actual status, evidence, benchmark, source, tests, and generated output.
  - Work Steps:
    1. Call the supervisor skill for the full completed plan.
    2. If it rejects, return to the responsible implementation slice only.
    3. Re-run the supervisor after any fix until `PASS` or a real blocker is recorded.
  - Implementation Gate: P1/P2 are complete or explicitly blocked.
  - Acceptance: supervisor report is `PASS`, or closure is `BLOCKED/REJECT` with evidence.

- [x] Pn-B: Remove dead work created during this plan.
  - Goal: ensure only accepted C15 artifacts remain.
  - Work Steps:
    1. Review changed source, tests, plan/evidence/benchmark/status, reports, generated output, and `.tmp` candidates.
    2. Remove or quarantine only plan-created dead artifacts; preserve unrelated user work.
    3. Re-run supervisor review for cleanup.
  - Implementation Gate: no broad cleanup or protected deletion.
  - Acceptance: no stale placeholder/dead helper remains and cleanup evidence is recorded.

- [x] Pn-C: Close the plan.
  - Goal: finish validation, evidence, benchmark, detect-changes, and final status.
  - Work Steps:
    1. Run final affected tests and full package/doctor validation; Docker/browser are N/A for this local Python surface.
    2. Regenerate only required generated outputs.
    3. Run Anvien detect-changes before any commit attempt.
    4. Record final evidence, benchmark, supervisor verdict, official artifact hash, and no-Git limitation.
    5. Stop at `PASS`, `BLOCKED`, or `REJECT`; do not start optional hardening.
  - Implementation Gate: Pn-A and Pn-B pass or have a documented blocker.
  - Acceptance: final evidence is self-contained and the worktree/repository state is known.

## Risk Notes

- C12 `foreground_execution.py` and C11 `task_state.py` are high-risk graph hotspots. The implementation is intentionally additive and should avoid edits to their direct paths.
- The host may not expose a supported child callback or identity receipt. In that case delegation remains truthfully unavailable/blocked; no synthetic runtime claim is made.
- The repository has no `.git`; required commit/detect-changes evidence may be limited to the Anvien graph and filesystem inspection. Do not initialize Git.
- Existing workflow state contains a direct-task goal-contract artifact created by the project helper; it is not used as permission to expand this task and is preserved unless the project’s own closure requires a bounded status update.
- Packaging may update generated checksums/locks. If so, validate the generated diff and keep any candidate archive under repo-local `.tmp`; never overwrite the user-specified official `.19` artifact.
