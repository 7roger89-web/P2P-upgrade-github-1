# P2P img2threejs executable projection Plan

## Metadata

- Date: `2026-08-29`
- Status: `complete_technical_pass_owner_gate_pending`
- Plan: `docs/plans/2026-08-29-p2p-img2threejs-exec-01/plan.md`
- Evidence: `docs/plans/2026-08-29-p2p-img2threejs-exec-01/evidence.md`
- Benchmark: `docs/plans/2026-08-29-p2p-img2threejs-exec-01/benchmark.md`
- Actual status: `docs/plans/2026-08-29-p2p-img2threejs-exec-01/actual-status.md`

## Goal

Enable the existing P2P img2threejs capability through a bounded, exact-SHA external
checkout adapter and selective project projection protocol for future Thiên Hạ Arena
work. The change must prove safe control-plane execution and discoverable protocols;
it must not implement Golden Character, a full animation system, or a second P2P
pipeline.

## Rules

- Complete P0 actual status before implementation work.
- Keep the upstream checkout external, exact-pinned, and clean; do not vendor the
  full upstream repository or floating `main`.
- The adapter is the only execution boundary. The existing projector remains pure
  projection and never becomes a launcher.
- Network, installation, credentials, arbitrary scripts, shell construction, CS2
  metadata fetching, and external renderers remain denied by default.
- Validate every untrusted path/identifier before upstream invocation and keep all
  state/evidence/output beneath a declared reconstruction workspace.
- Preserve the predecessor 02A provenance as historical evidence; do not erase it.
- Update each checklist item and evidence entry as it is completed.
- Run Anvien impact/file-detail before touching existing contracts and detect-changes
  before implementation commits.
- No browser evidence is claimed in this task: no Thiên Hạ project or visual runtime
  is changed. Browser evidence remains a future Golden Character/Asset Lab gate.

## Problem

P2P currently records img2threejs only as an audited, non-executable external
candidate. Fresh audit of upstream v1.5.1 shows the useful staged workflow is
available, but also confirms an unrestricted `--index-url` network route and
unsanitized material-region output identifiers. The current P2P registry has no
img2threejs capability and the existing 02A test encodes that old status. A safe
execution adapter and an on-demand protocol projection are missing.

## Scope

- Fresh origin/main and upstream release identity/provenance.
- A small Python adapter that verifies the exact external checkout, clean tree,
  allowlisted entrypoints, local reference paths, workspace/output containment,
  subprocess argv, timeout, and deny-by-default network policy.
- Allow only the audited upstream control-plane/local deterministic entrypoints
  `forge/state.py`, `forge/next.py`, `forge/stage1_intake/probe_image.py`,
  `forge/stage2_spec/validate_sculpt_spec.py`, and
  `forge/stage3_build/generate_threejs_factory.py`; leave CS2 fetching,
  vision/plugin adapters, renderer helpers, and other routes denied.
- A P2P-authored img2threejs projection contract containing when-to-use rules,
  character and asset-forge protocols, maturity limits, Arena routing fields, and
  visual-evidence law.
- Capability registry/provenance/external-source updates and route discovery,
  reusing the existing single router and host projection mechanism.
- Canonical project bootstrap read-order hook for the optional selective capability.
- Focused security, provenance, registry, route, projection, and unrelated-project
  regression tests.

## Non-Goals

- No P2P architecture redesign or second router/certification system.
- No full Thiên Hạ character implementation or Golden Character model.
- No Golden Weapon implementation, browser Character Lab, Playwright run, release,
  deployment, push, promotion, or canonical-main mutation.
- No package installation, network fetch, CS2 metadata route, arbitrary plugin/script,
  or automatic multi-view fusion.
- No claim of full production auto-rig, Mixamo compatibility, complete facial rig, or
  production animation pipeline.

## Requirements

- Pin upstream v1.5.1 at `dede5909be4e494b228c801a55dda47439143932` with tree
  `25bcd4e1f1a487b9a61d69ade257342a3da767e3`, license Apache-2.0, and record the
  fresh upstream main `9fbd0ca5bbcc3b13bebe712745d6784d33db0b85` separately.
- Fresh P2P origin/main is `29291dae1f3101f3ace9546fb2b27e3d514bca61`, tree
  `e5e01a1a2d4ddad207aaab2e25752b571bd5fb9e`.
- SSRF-relevant CS2 route remains blocked by entrypoint deny policy; path traversal
  is rejected at the adapter boundary even if upstream remains unsafe.
- Project projection is selective and contains only contract/instructions/provenance
  pointers, not the full P2P runtime or upstream source tree.

## Acceptance Criteria

- `load_registry` is valid with canonical denominator 8 and one noncanonical
  `img2threejs` capability routed through the existing router.
- Exact upstream commit/tree/license and the earlier pending record are preserved.
- Adapter tests prove missing source, wrong SHA/tree, dirty checkout, unsupported
  entrypoint, URL/absolute/traversal reference, output escape, and CS2 route fail
  closed; no shell and no inherited secrets are used.
- Exact pinned checkout smoke executes only the five allowlisted local/control-plane
  entrypoints inside a repo-local temporary reconstruction workspace and returns a
  redacted receipt; no dependency install or network call occurs.
- Projection route loads only the selected contract and leaves unrelated vendor
  projectors/routing behavior unchanged.
- Contract explicitly separates character maturity from hard-surface asset maturity,
  requires six-view consistency for future Golden Character evidence, and requires
  actual browser screenshots before visual acceptance.
- Focused tests, `git diff --check`, final exact candidate SHA/tree, and clean branch
  are recorded. Terminal status is ready for exact-subject supervisor, not Owner
  approval or promotion.

## Checklist

- [x] P0-A: Complete actual status before implementation work.
  - Goal: establish the real current state.
  - Work Steps: inspect current P2P and upstream source, classify each surface,
    record the stale/unsafe/missing boundaries, and update phase decisions.
  - Implementation Gate: actual-status has a final P0 decision and Anvien evidence.
  - Acceptance: correct, partial, missing, wrong, and preserve-only surfaces are
    classified with evidence IDs.

### P1: Bounded execution and selective project projection

- Phase Goal: add the minimum executable adapter, projectable protocol, provenance,
  routing, and focused proof without broadening P2P runtime architecture.
- Phase Boundary:
  - In scope: adapter module, contract/protocol docs, registry/provenance/manifest,
    bootstrap read-order hook, focused tests and reports.
  - Out of scope: target Thiên Hạ repository, visual runtime, release/deployment,
    upstream patches, full vendor tree, and canonical main.
  - Dependencies: fresh P2P branch, exact upstream audit checkout, existing router,
    `vendor_skill`/host projection, and current capability schema.
- Phase Implementation Rule: implement `P1-A`, verify and refresh actual status,
  commit; then implement `P1-B`, verify and refresh actual status, commit.
- Ordered Slice List:
  - P1-A: Implement exact-source bounded execution adapter and security tests.
  - P1-B: Register and selectively project the operational character/asset contract.

- [x] P1-A: Implement exact-source bounded execution adapter and security tests
  - Goal: make only the audited upstream local/control-plane path executable and fail closed
    for unsafe routes.
  - Scope Boundary:
    - Editable: `.p2p/system/p2p_capabilities/img2threejs_adapter.py`, focused
      adapter tests, and execution/provenance evidence.
    - Inspect-only: pinned upstream source, existing `vendor_skill`, projection
      helpers, and all non-allowlisted upstream scripts.
    - Preserve-only: P2P router semantics, existing vendors, current P2P state, and
      historical 02A records.
    - Out of scope: upstream source patching, network sandbox implementation,
      renderer/vision execution, and project files.
  - Non-Goals: this slice does not generate geometry or claim visual acceptance.
  - Pre-flight Questions:
    - Data source: exact clean local checkout at the pinned upstream SHA/tree.
    - Display permission: adapter receipts expose hashes/status only; no secrets or
      raw untrusted subprocess output.
    - DB read flow: N/A; no database.
    - DB write flow: N/A; state JSON is quarantined beneath reconstruction workspace.
    - Render location: N/A; control-plane state only.
    - UI behavior flow: N/A; no UI surface is changed.
    - Docker runtime: N/A; no app/runtime container is changed.
    - Playwright target: N/A; visual proof is future project scope.
    - Behavior test: exact checkout state init plus fail-closed hostile inputs.
    - Cleanup/quarantine: all test workspaces under repo `.tmp`; no project paths.
    - External side effects: none; subprocess is local and allowlisted only.
    - N/A notes: network deny is enforced by route/allowlist and static audit, not by
      claiming OS-level sandboxing.
  - Work Steps:
    1. Add exact source/provenance constants, path/identifier validation, clean-tree
       verification, and explicit allowlist dispatch.
       - UI flow check: N/A, non-UI adapter.
       - DB/data flow check: verify reference -> bounded workspace -> state receipt.
       - Render location check: verify no output outside declared workspace.
       - Mini QA: run focused adapter unit tests and exact-checkout smoke.
       - Evidence target: `E1-P1A-SEC1..E1-P1A-SEC8`.
    2. Prove denial of SSRF/path traversal/unsupported execution and redacted process
       policy, then refresh actual status.
       - UI flow check: N/A.
       - DB/data flow check: hostile input never creates outside files.
       - Render location check: output-root containment and visible error status.
       - Mini QA: inspect subprocess argv and environment in a mocked runner.
       - Evidence target: `E1-P1A-TEST1..E1-P1A-TEST6`.
  - Implementation Gate:
    - Before editing, Anvien file-detail/impact evidence exists for the affected
      existing test/contract surfaces; new module is reviewed as a new boundary.
    - The adapter must never accept a caller-supplied arbitrary script path or URL.
  - Acceptance:
    - Source: adapter validates exact SHA/tree, clean checkout, and allowlist.
    - Runtime/UI: bounded local subprocess smoke only; no UI claim.
    - DB/data: state/output paths remain beneath workspace.
    - Behavior test: all security cases pass and no-network route is not invocable.
    - Cleanup/quarantine: repo-local temp roots are removed or excluded from commit.
    - Evidence IDs: `E1-P1A-SEC1..E1-P1A-TEST6`.
    - Actual-status rows refreshed: adapter missing -> correct; unsafe upstream route
      contained -> correct for the P2P boundary.
  - Evidence Targets: exact subprocess receipt, source hashes, security test output,
    and diff check.
  - Actual-status Update: append R1 with adapter implementation and security result.
  - Commit Boundary: commit after focused acceptance passes.

- [x] P1-B: Register and selectively project the operational character/asset contract
  - Goal: make the capability discoverable and projectable for future Thiên Hạ Arena
    sessions without copying the full runtime or upstream repository.
  - Scope Boundary:
    - Editable: capability registry, provenance/external manifest, P2P-authored
      contract and selective skill snapshot, bootstrap read-order hook, and existing
      02A assertions that encode the superseded state.
    - Inspect-only: host projection implementation and project pin/identity specs.
    - Preserve-only: canonical identities/quorum, host projector purity, existing
      non-img2threejs vendors, and no target project checkout.
    - Out of scope: Thiên Hạ integration, browser lab, visual screenshots, release,
      and Owner Gate execution.
  - Non-Goals: no actual Golden Character/Weapon asset is produced.
  - Pre-flight Questions:
    - Data source: P2P contract plus exact upstream provenance record.
    - Display permission: selected skill text is on-demand; unselected vendor text
      remains unread.
    - DB read flow: N/A; JSON registry/provenance only.
    - DB write flow: N/A; tracked metadata only.
    - Render location: future project browser runtime, not this branch.
    - UI behavior flow: future Arena prompt routing only.
    - Docker runtime: N/A; no public runtime changed.
    - Playwright target: N/A; no visual acceptance in this setup slice.
    - Behavior test: registry validity, explicit route selection, projection payload,
      historical record, and unrelated route regression.
    - Cleanup/quarantine: no project files or persistent external state.
    - External side effects: none; no push/promote/release.
    - N/A notes: actual browser evidence is a future acceptance gate, not faked here.
  - Work Steps:
    1. Add the operational contract and metadata with explicit when-to-use/not-use,
       character/asset protocols, maturity and evidence boundaries.
       - UI flow check: future Arena read order is documented; no current UI.
       - DB/data flow check: registry -> selective route -> contract content.
       - Render location check: future project must render in its own workspace.
       - Mini QA: load selected contract through existing projection helper.
       - Evidence target: `E1-P1B-PROJ1..E1-P1B-PROJ4`.
    2. Update registry, bootstrap hook, external manifest, and focused prior tests;
       run route/projection/unrelated-project checks.
       - UI flow check: verify explicit Arena prompt fields are present in contract.
       - DB/data flow check: validate registry schema and unchanged quorum count.
       - Render location check: verify no full vendor tree is projected.
       - Mini QA: route explicit img2threejs prompts and old camera/combat prompts.
       - Evidence target: `E1-P1B-ROUTE1..E1-P1B-TEST6`.
  - Implementation Gate:
    - Existing projection remains a pure data projection; no launcher is added to it.
    - New capability is noncanonical, non-optional-specialist, and does not alter 8/8.
  - Acceptance:
    - Source: registry/provenance/external manifest and contract are internally bound.
    - Runtime/UI: future-project bootstrap discovery is explicit; no browser claim.
    - DB/data: N/A beyond JSON schema/data integrity.
    - Behavior test: selected contract loads; unrelated project routing is unchanged.
    - Cleanup/quarantine: no temp artifacts are tracked.
    - Evidence IDs: `E1-P1B-PROJ1..E1-P1B-TEST6`.
    - Actual-status rows refreshed: registry/projection partial -> correct; future
      visual protocol remains unproven by design.
  - Evidence Targets: registry count/validity, route results, projection hashes,
    bootstrap read-order, focused tests, and diff check.
  - Actual-status Update: append R2 with selective projection and routing result.
  - Commit Boundary: commit after focused acceptance passes.

- [x] Pn-A: Call supervisor for the implemented-plan acceptance loop.
  - Goal: exact-subject zero-trust review of code, metadata, security proof, and
    candidate identity before Owner Gate.
  - Work Steps: inspect source and diff independently, rerun focused gates, write a
    supervisor report, and fix only any rejected scope.
  - Implementation Gate: P1-A and P1-B are complete and candidate is frozen.
  - Acceptance: supervisor PASS or explicit blocker; no Owner approval inferred.
    Exact reviewed subject is `8799112e7153657ec5600cd2c0510ec4a02e3cf1`.

- [x] Pn-B: Remove dead work created during this plan.
  - Goal: leave only accepted plan artifacts; remove temp clones/output and stale
    attempts made by this plan, preserving historical source records.
  - Work Steps: review status, remove only plan-created dead temp artifacts where
    permitted, rerun diff check, and record what remains.
  - Implementation Gate: never clean unrelated user temp data or mutate canonical
    runtime.
  - Acceptance: candidate diff has no dead implementation artifacts. The exact
    upstream audit checkout remains outside the candidate as the declared source
    prerequisite for verification; no plan-created dead implementation artifact
    is tracked.

- [x] Pn-C: Close the plan.
  - Goal: record final validation, detect-changes, exact candidate SHA/tree, clean
    worktree, and terminal verdict.
  - Work Steps: run focused suites and doctor/registry checks applicable to the
    changed surfaces; Docker/browser are N/A because no app runtime changed; run
    detect-changes, diff check, commit and final identity checks.
  - Implementation Gate: supervisor review is PASS or a blocker is recorded.
  - Acceptance: `P2P_IMG2THREEJS_EXEC_01_READY_FOR_EXACT_SUBJECT_SUPERVISOR` after
    the independent supervisor report is written and the final candidate identity
    is recorded. Owner Gate remains pending.

## Risk Notes

- Upstream v1.5.1 still contains unsafe network/path behavior. The adapter must not
  expose those entrypoints; Apache-2.0 is provenance, not a security verdict.
- The exact checkout is an external prerequisite. Missing, dirty, or drifted source
  must return `BLOCKED`, never fetch or silently substitute another revision.
- This task can prove bounded control-plane execution, not visual reconstruction or
  browser character quality. Those remain future evidence gates.
- Disk pressure from existing repository candidate artifacts is an environment risk;
  only plan-created temp clones may be quarantined/removed.
