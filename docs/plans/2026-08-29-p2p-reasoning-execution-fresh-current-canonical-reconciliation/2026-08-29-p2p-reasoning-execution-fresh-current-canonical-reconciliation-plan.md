# P2P Reasoning/Execution Fresh Current-Canonical Reconciliation Plan

## Metadata

- Date: `2026-08-29`
- Status: `ready_for_supervisor`
- Plan: `docs/plans/2026-08-29-p2p-reasoning-execution-fresh-current-canonical-reconciliation/2026-08-29-p2p-reasoning-execution-fresh-current-canonical-reconciliation-plan.md`
- Evidence: `docs/plans/2026-08-29-p2p-reasoning-execution-fresh-current-canonical-reconciliation/2026-08-29-p2p-reasoning-execution-fresh-current-canonical-reconciliation-evidence.md`
- Benchmark: `docs/plans/2026-08-29-p2p-reasoning-execution-fresh-current-canonical-reconciliation/2026-08-29-p2p-reasoning-execution-fresh-current-canonical-reconciliation-benchmark.md`
- Actual status: `docs/plans/2026-08-29-p2p-reasoning-execution-fresh-current-canonical-reconciliation/2026-08-29-p2p-reasoning-execution-fresh-current-canonical-reconciliation-actual-status.md`

## Goal

Reconcile the already-reviewed Reasoning/Execution implementation from old
base `1c84bc41421dcbe502d40b71fead5022231d0541` and candidate
`e1410fa28fab5b9c3d0d9f1c37ef68a20165bcef` onto the newest official `main`
without rebuilding the feature or rolling back later canonical work. Produce
one isolated, unpromoted candidate ready for the Owner gate.

## Rules

- Complete P0 actual status before implementation work.
- Freshly resolve official `main` before source mutation; if it advances again,
  rebind to the newest SHA/tree.
- Use the old candidate only as a reviewed source delta. Do not cherry-pick its
  stale history or copy its reconciliation-only docs as implementation.
- Current-main behavior wins wherever later work exists. Preserve all current
  01D projection, project-context, materialization, pin, spec, and test work.
- The exact path intersection determines whether overlap is `NONE`,
  `DOCUMENTATION_ONLY`, `COMPATIBLE_CODE_OVERLAP`, or
  `MATERIAL_SEMANTIC_CONFLICT`. Resolve only real overlap.
- The user explicitly prohibits Anvien, MCP, Council, provider installation,
  live browser/database actions, remote-push execution, promotion, release,
  deployment, and live activation. Exact Git/source evidence is the substitute
  for Anvien path/impact evidence.
- Do not add ArenaAdapter, a new execution framework, capability ontology,
  registry, router, verifier, risk engine, orchestrator, truth store, or MCP.
- Preserve the dirty protected worktrees and the old candidate branch. Work only
  in the isolated `.tmp/p2p-sec01-current-canonical` candidate branch.
- Do not rerun all 111 tests. Run the 17 direct tests, directly affected
  preservation tests only when needed, affected-module compilation, relevant
  registry/contract parsing, and `git diff --check`.
- No Owner approval is inferred. No push or promotion is authorized.

## Problem

Official `main` advanced from the previous reconciliation subject with a later
01D projection-contract slice. The old Reasoning/Execution candidate is
technically reviewed but based on the previous `1c84bc4` canonical. The safe
operation is to start from fresh `main`, prove that the old candidate's source
delta has no path overlap with later canonical files, port only the coherent
11-file source/test delta, and preserve all 01D behavior exactly.

## Scope

- P0: fresh remote/current-main identity, old candidate identity, exact path
  comparison, later-work source inspection, and P0 status/evidence.
- P1-A: the nine existing Reasoning/Execution runtime files and two reviewed
  test files:
  `agent_role.py`, `backend_contract.py`, `backend_execution_bridge.py`,
  `fake_execution_backend.py`, `role_bridge.py`, `role_contract.py`,
  `role_eligibility.py`, `role_receipt.py`, `role_verifier.py`,
  `tests/test_p2p_c34_real_backend_contract.py`, and
  `tests/test_p2p_reasoning_execution_decoupling.py`.
- P1-B: focused validation and this reconciliation's four plan files plus
  decision/evidence/report records.
- P2: one independent Supervisor review focused on current-main ancestry,
  later canonical preservation, Reasoning/Execution invariants, host/surface
  awareness, evidence, permissions, duplicate control plane, and Owner gate.

## Non-Goals

- No rebuild or redesign of the reviewed implementation.
- No modification to current-main 01D projection files, projection SPEC,
  projection test, or any later canonical source outside the proven delta.
- No broad regression, full 111-test rerun, Anvien, Council/quorum, MCP,
  provider installation, live browser/database execution, remote push execution,
  promotion, release, deployment, or live activation.
- No new capability ontology or effective-capability engine. Existing
  host/surface/environment/permission-aware semantics remain authoritative.

## Requirements

- Preserve the normalized operational execution capability vocabulary and
  task-to-certified-target binding.
- Keep reasoning provider identity separate from execution target, including
  host/surface/environment/permission-aware effective capability semantics.
- Preserve `STATIC_REASONING != EXECUTION_EVIDENCE` and mechanical mappings:
  `TEST_PASS -> TEST_EXECUTE`, `BUILD_PASS -> BUILD_EXECUTE`,
  `BROWSER_PASS -> BROWSER_EXECUTE`, `DATABASE_PASS -> DATABASE_SANDBOX`, and
  `REMOTE_PUSHED -> REMOTE_PUSH` plus remote observation.
- Preserve actual observed execution-target binding, permission non-widening,
  stale/marketing capability fail-closed behavior, C35 provider neutrality, and
  current Owner/release governance.
- Preserve AUTO01, SEC01, APKiD, monetization and infrastructure seams, and all
  newer canonical work.
- Keep `MCP_REQUIRED_NOW=NO`, `OWNER_GATE_REQUIRED=YES`, and
  `CANONICAL_PROMOTED=NO`.

## Acceptance Criteria

- Fresh official remote resolves to the newest official `main`; the candidate's
  parent is that exact commit and its tree is recorded.
- Old-base-to-candidate and old-base-to-current-main path sets are compared;
  current expected classification is `NONE` with zero production/test overlap.
- Exactly the coherent Reasoning/Execution source/test delta is carried forward;
  no current-main later source is reverted or overwritten.
- Direct tests, directly affected preservation tests, affected compile, relevant
  JSON/contract parse, and diff checks pass within the stated ceiling.
- One focused Supervisor report passes the exact candidate and Owner boundary.
- Candidate remains unpromoted and terminates at
  `P2P_REASONING_EXECUTION_CURRENT_CANONICAL_RECONCILED_CANDIDATE_READY_FOR_OWNER_GATE`.

## Checklist

- [x] P0-A: Complete actual status before implementation work.
  - Goal: establish fresh authority, exact overlap, later canonical boundaries,
    and the smallest permitted port.
  - Work Steps: resolve official remote; verify clean isolated source clone;
    verify old candidate/base; compare exact path sets; inspect 01D projection
    source/spec/test; record classification and downstream plan decisions.
  - Implementation Gate: actual-status has evidence IDs, a final P0 decision,
    and explicitly permits only P1-A/P1-B below.
  - Acceptance: remote `82d8a976/ac2627b0`, old candidate `e1410fa/5cccc26`,
    and zero exact overlap are recorded; no source mutation occurred before P0.

### P1: Carry forward the reviewed delta onto newest current main

- Phase Goal: port only the already-reviewed Reasoning/Execution source/test
  delta while retaining every newer canonical path.
- Phase Boundary:
  - In scope: the 11 reviewed source/test paths, focused validation, and audit
    artifacts.
  - Out of scope: all 01D projection paths, unrelated current-main work, broad
    regression, live actions, and promotion.
  - Dependencies: completed P0-A actual status and clean branch from fresh main.
- Phase Implementation Rule: do not implement `P1` directly. Implement P1-A,
  verify/checkpoint it, refresh actual-status, then perform P1-B.
- Ordered Slice List:
  - P1-A: Port the exact reviewed Reasoning/Execution source/test delta.
  - P1-B: Run the verification ceiling and record reconciliation evidence.

- [x] P1-A: Port the exact reviewed Reasoning/Execution source/test delta.
  - Goal: retain proven semantics without stale-history replay or later-main
    rollback.
  - Scope Boundary:
    - Editable: the nine runtime files and two reviewed test files named in
      Scope.
    - Inspect-only: current-main 01D projection files and SPEC/test surfaces.
    - Preserve-only: every current-main path outside the exact 11-file delta.
    - Out of scope: new abstractions, MCP, providers, live execution, and
      current-main projection changes.
  - Non-Goals: no semantic redesign; no copy of old reconciliation docs into
    runtime; no capability implication beyond the reviewed contract.
  - Pre-flight Questions:
    - Data source: old candidate's reviewed 11-file source/test delta.
    - Display permission: N/A; Python contract/runtime only.
    - DB read flow: N/A; no database path is touched.
    - DB write flow: N/A; tests use isolated state only.
    - Render location: N/A; no UI.
    - UI behavior flow: N/A; no UI.
    - Docker runtime: N/A; no app/Docker change.
    - Playwright target: N/A; no UI.
    - Behavior test: direct Reasoning/Execution test file and affected C34/C35
      preservation tests.
    - Cleanup/quarantine: repo-local `.tmp` test state only.
    - External side effects: none; no network write, push, or provider action.
    - N/A notes: affected-module Python compile is the build boundary.
  - Work Steps:
    1. Apply only the exact 11-file reviewed delta from old candidate onto the
       fresh-main branch; abort if any current-main source/test path overlaps.
       - UI flow check: N/A; no UI.
       - DB/data flow check: N/A; no DB.
       - Render location check: N/A; no render.
       - Mini QA: inspect diff and current 01D path hashes.
       - Evidence target: `E1-P1A-SRC1`.
    2. Run the direct 17 tests and checkpoint the verified source/test slice.
       - UI flow check: N/A; no UI.
       - DB/data flow check: N/A; no DB.
       - Render location check: N/A; no render.
       - Mini QA: verify no 01D source/test path changed.
       - Evidence target: `E1-P1A-TEST1`, `E1-P1A-DIFF1`.
  - Implementation Gate:
    - P0 overlap classification is `NONE` and production/test overlap is zero.
    - User-prohibited Anvien is replaced by exact Git path/source evidence.
    - Current-main projection files remain preserve-only.
  - Acceptance:
    - Source: only the reviewed 11-file source/test delta is present.
    - Runtime/UI: N/A; no UI/runtime surface.
    - DB/data: N/A; no DB/data surface.
    - Behavior test: direct 17-test suite passes.
    - Cleanup/quarantine: state remains under repo-local `.tmp`.
    - Evidence IDs: `E1-P1A-SRC1`, `E1-P1A-TEST1`, `E1-P1A-DIFF1`.
    - Actual-status rows refreshed: Reasoning/Execution and preservation rows.
  - Evidence Targets: exact source/test path list, direct test result, ancestry
    and diff boundary.
  - Actual-status Update: append R1 after the source/test checkpoint.
  - Commit Boundary: commit the verified source/test slice before P1-B.

- [x] P1-B: Run the verification ceiling and record reconciliation evidence.
  - Goal: prove the carried-forward invariant at its nearest real boundaries.
  - Scope Boundary:
    - Editable: four plan artifacts, decision log entry, coder report, and
      focused evidence only.
    - Inspect-only: all implementation source after P1-A.
    - Preserve-only: all current-main 01D source/spec/test files.
    - Out of scope: broad tests, live actions, and promotion.
  - Non-Goals: no new implementation or cleanup outside plan-created artifacts.
  - Pre-flight Questions:
    - Data source: current branch source, prior focused evidence, and Git objects.
    - Display permission: N/A; audit artifact only.
    - DB read/write flow: N/A; no DB.
    - Render/UI location: N/A; no UI.
    - Docker runtime: N/A; Python-only source.
    - Playwright target: N/A; no UI.
    - Behavior test: direct 17; C34/C35 only if directly affected.
    - Cleanup/quarantine: no failed clone or stale generated artifact enters the
      candidate diff.
    - External side effects: none.
    - N/A notes: parse `capabilities.json` and import/compile affected contract
      modules where relevant.
  - Work Steps:
    1. Run direct tests; run only directly affected C34/C35 preservation tests;
       compile affected modules; parse registry/contract; run diff checks.
       - UI flow check: N/A; no UI.
       - DB/data flow check: N/A; no DB.
       - Render location check: N/A; no render.
       - Mini QA: compare every current-main changed path to fresh main.
       - Evidence target: `E1-P1B-TEST1`, `E1-P1B-COMPILE1`,
         `E1-P1B-PARSE1`, `E1-P1B-DIFF1`.
    2. Write the coder report and append the current-lineage decision entry.
       - UI flow check: N/A; audit docs only.
       - DB/data flow check: N/A; no DB.
       - Render location check: N/A; no render.
       - Mini QA: inspect no stale-base claim and explicit Owner boundary.
       - Evidence target: `E1-P1B-REPORT1`, `E1-P1B-IDENTITY1`.
  - Implementation Gate: P1-A checkpoint is verified and source/test behavior
    is unchanged while documentation is recorded.
  - Acceptance:
    - Source: no source change beyond P1-A.
    - Runtime/UI: N/A; no UI.
    - DB/data: N/A; no DB.
    - Behavior test: focused ceiling passes.
    - Cleanup/quarantine: candidate diff contains only scoped artifacts.
    - Evidence IDs: `E1-P1B-TEST1..E1-P1B-IDENTITY1`.
    - Actual-status rows refreshed: all affected rows and R2.
  - Evidence Targets: focused commands, parse/compile, final candidate identity,
    and coder report.
  - Actual-status Update: append R2 before Supervisor.
  - Commit Boundary: commit the evidence/log/report slice before P2.

### P2: Independent acceptance and Owner-gate stop

- [ ] P2-A: Run one focused independent Supervisor review.
  - Goal: verify exact ancestry, all newer canonical preservation, required
    Reasoning/Execution/host-surface/evidence/permission invariants, duplicate
    control-plane absence, and Owner boundary.
  - Work Steps: inspect candidate source/diff first; verify current-main path
    hashes; verify focused results and exact candidate identity; write one PASS
    or REJECT report. Do not repair during review.
  - Implementation Gate: P1-A/P1-B complete and no unresolved same-invariant
    surface remains.
  - Acceptance: one Supervisor report records `PASS`; no promotion follows.

- [ ] Pn-A: Close the plan and stop at Owner Gate.
  - Goal: record final SHA/tree, clean status, evidence, benchmark counts, and
    the separate Owner decision boundary.
  - Work Steps: refresh actual status/evidence/benchmark; inspect candidate diff;
    verify no stale temporary artifact; commit closure docs; do not push/promote.
  - Implementation Gate: P2-A PASS and no source/test drift after review.
  - Acceptance: terminal verdict is ready for Owner Gate with
    `CANONICAL_PROMOTED=NO`.

## Risk Notes

- Current-main 01D projection files are a high-sensitivity preserve-only
  boundary; path non-overlap and post-change exact hashes are mandatory.
- The supplied root is not a Git checkout and the protected canonical runtime is
  dirty; neither is a mutation target.
- A technical PASS is not Owner approval, promotion authority, release, or live
  activation.
- If official main advances again before mutation or candidate closure, rebind to
  the newest SHA/tree and redo only the necessary overlap checks.
