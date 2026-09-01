# P2P MPFB2 Addon Init 01 Plan

## Metadata

- Date: `2026-09-01`
- Status: `P1-B implementation in progress`
- Plan: `docs/plans/2026-09-01-p2p-mpfb2-addon-init-01/2026-09-01-p2p-mpfb2-addon-init-01-plan.md`
- Evidence: `docs/plans/2026-09-01-p2p-mpfb2-addon-init-01/2026-09-01-p2p-mpfb2-addon-init-01-evidence.md`
- Benchmark: `docs/plans/2026-09-01-p2p-mpfb2-addon-init-01/2026-09-01-p2p-mpfb2-addon-init-01-benchmark.md`
- Actual status: `docs/plans/2026-09-01-p2p-mpfb2-addon-init-01/2026-09-01-p2p-mpfb2-addon-init-01-actual-status.md`

## Goal

Close only the MPFB2 addon-initialization blocker for issue 52 after the
canonical Windows firewall sequence passed. Use fresh canonical main
`b65948b00ed2a8969fed70ab59f68b5d9b53858d`, reuse Blender 4.2.23 LTS and
MPFB2 2.0.17 at `80919fa4682335c41847f761a4d79dcad4124732`, prove the real
extension identity/preferences/register lifecycle, and run exactly one neutral
character through the existing canonical route.

## Rules

- Keep the Owner checkout untouched; use only this fresh branch/worktree.
- Do not reinstall/download Blender or MPFB2, edit upstream MPFB2, fake addon
  state, inject preferences, use an arbitrary Python/shell route, or add a
  plugin manager.
- Preserve the promoted firewall profile normalization, DisplayName/rule
  verification, outbound BLOCK, exact executable binding, verify-before-Popen,
  cleanup, and post-cleanup absence check.
- Preserve adapter, output, provenance, rights, and network-deny contracts;
  do not redesign them.
- Stop at the first real new downstream blocker; no retry with a different
  version/recipe, extra characters, hardening, broad regression, Game Truyen,
  release, promotion, deployment, or merge.
- Update plan/evidence/status as each slice completes and run Anvien
  detect-changes before any implementation commit.

## Problem

The child currently adds `<mpfb-root>\\src` to `sys.path`, imports bare `mpfb`,
and calls `mpfb.register()`. Pinned MPFB2's `get_preference()` uses
`__package__` as a key in `bpy.context.preferences.addons`; the bare module is
not a real Blender addon identity and fails at initialization.

## Scope

- Fresh subject and exact runtime/source identity proof.
- Blender 4.2 local extension repository loading, isolated user resources,
  and bounded child-entrypoint remediation.
- Directly affected focused checks and one real Windows character smoke with
  independent artifact/provenance/cleanup proof.
- Plan/evidence/benchmark/actual-status and Supervisor report.

## Non-Goals

- No adapter/firewall redesign or changes to the canonical security sequence.
- No upstream source edits, alternate versions, fake state, arbitrary runner,
  Game Truyen mutation, visual QA, release/promotion/deployment/merge, broad
  regression, or extra character.

## Requirements

- Fresh origin/main equals the expected SHA; branch is based on exact SHA/tree.
- Existing Blender/MPFB2 identities and source bytes are exact; generated
  cache is handled deterministically so the provisioned root hash passes.
- Supported loading uses a local extension repository containing the pinned
  `blender_manifest.toml`, discovers `bl_ext.<repo_module>.mpfb`, uses
  `addon_utils.enable(..., default_set=True, persistent=False)`, and leaves
  user data in the runtime's portable/resources boundary.
- Real child output proves `MPFB_ADDON_IDENTITY_PRESENT=YES`, successful
  `mpfb.get_preference("mpfb_user_data")`, and `MPFB_REGISTER_PASS=YES` before
  `HumanService.create_human()`.
- Exactly one neutral character follows firewall -> Blender -> MPFB2 -> rig ->
  skin -> GLB -> provenance -> structural validation -> cleanup.

## Acceptance Criteria

- Exact base/candidate SHA/tree, remediation type, source mutation, and PR
  state are recorded.
- The three addon gates are proven by a real Blender child, without fabricated
  `bpy` state.
- One neutral route fully passes or stops at the first exact downstream blocker
  with later fields `NOT_RUN`.
- Firewall cleanup leaves no rule; Game Truyen mutations are `NO`.
- Supervisor performs an independent PASS/REJECT review; no merge occurs.

## Checklist

- [x] P0-A: Complete actual status before implementation work.
  - Goal: classify the fresh subject, runtime, source contract, old failure,
    security boundary, and downstream ownership.
  - Work Steps: fresh-fetch origin; bind SHA/tree; inspect source/archive,
    Blender loader, prior logs, adapter/firewall, and graph relationships; fill
    actual status and evidence before editing.
  - Implementation Gate: actual-status has matrix, evidence IDs, touch modes,
    relationship counts/limitations, and P0 decision.
  - Acceptance: bare import is partial/wrong; extension contract is the sole
    remediation decision; firewall/adapter/pins/Game Truyen are preserve-only.

### P1: Supported addon contract and bounded remediation

- Phase Goal: prove the supported path and bind the canonical child to it.
- Phase Boundary:
  - In scope: local extension repo, `addon_utils`, preference identity,
    isolated resources, and one entrypoint source fix.
  - Out of scope: character generation, firewall changes, upstream edits, and
    unrelated capabilities.
  - Dependencies: P0 complete; existing runtime identities verified.
- Phase Implementation Rule: P1-A proof precedes P1-B source edit.
- Ordered Slice List:
  - P1-A: Real Blender identity/preference/register proof.
  - P1-B: Minimum supported entrypoint binding.

- [x] P1-A: Real Blender identity/preference/register proof.
  - Goal: prove the exact namespace and lifecycle in real Blender.
  - Scope Boundary:
    - Editable: dedicated runtime probe and evidence ledgers only.
    - Inspect-only: P2P source, MPFB2 archive/source, Blender loader/docs.
    - Preserve-only: adapter, firewall helper, executable, Owner checkout.
    - Out of scope: character creation and Game Truyen.
  - Non-Goals: no source fix, fake registry, arbitrary expression, or network.
  - Pre-flight Questions:
    - Data source: pinned archive/source plus Blender 4.2 loader.
    - Display/DB/render/UI/Docker/Playwright: N/A for native background Blender.
    - Behavior test: old bare probe and extension probe with no mocked bpy.
    - Cleanup/quarantine: runtime-local config/resources and exact generated
      cache quarantine only.
    - External side effects: isolated local preferences only.
  - Work Steps:
    1. Compare the existing archive/source; inspect manifest id, package,
       preference lookup, register, `addon_utils.enable`, and resource paths.
       - UI/DB/render checks: N/A.
       - Mini QA: source and loader evidence inspected.
       - Evidence target: `E1-P1A-SRC1`, `E1-P1A-DOC1`.
    2. Run bare and local-extension probes in fresh offline Blender processes;
       print addon key, preference, register, module, and isolated paths.
       - UI/DB/render checks: N/A.
       - Mini QA: downstream remains NOT_RUN.
       - Evidence target: `E1-P1A-RUNTIME1..2`, `E1-P1A-DECISION1`.
  - Implementation Gate: source remains unedited until extension proof passes;
    `addon_utils.enable`'s one real `mod.register()` call is confirmed.
  - Acceptance:
    - Source/runtime: exact source and binary identity; extension proof PASS.
    - Behavior: bare failure and extension success are separately recorded.
    - Evidence IDs: `E1-P1A-*`.
    - Actual-status rows refreshed: entrypoint, runtime, pin, remediation.
  - Evidence Targets: `E1-P1A-SRC*`, `E1-P1A-DOC*`, `E1-P1A-RUNTIME*`.
  - Actual-status Update: select `BOUNDED_SOURCE_FIX` because canonical child
    remains bare-imported.
  - Commit Boundary: no source commit.

- [ ] P1-B: Minimum supported entrypoint binding.
  - Goal: use the proven extension lifecycle without changing other invariants.
  - Scope Boundary:
    - Editable: only `.p2p/system/p2p_capabilities/mpfb_blender_entrypoint.py`
      and directly affected focused tests if evidence requires them.
    - Inspect-only: upstream MPFB2 and unrelated P2P capabilities.
    - Preserve-only: adapter, firewall, output/provenance, and Game Truyen.
    - Out of scope: adapter redesign, fallback, second identity, or security.
  - Non-Goals: no bare-import fallback or preference injection.
  - Pre-flight Questions:
    - Data source: P1-A real namespace/lifecycle evidence.
    - Display/DB/render/UI/Docker/Playwright: N/A.
    - Behavior test: compile plus directly affected focused tests and real
      pre-character proof.
    - Cleanup/quarantine: no generated runtime files in Git.
    - External side effects: one branch/PR; no merge.
  - Work Steps:
    1. Record Anvien file-detail/impact result and the high/unknown blast-radius
       warning for the hidden capability source.
       - UI/DB/render checks: N/A.
       - Mini QA: inspect exact target diff.
       - Evidence target: `E1-P1B-IMPACT1`.
    2. Replace only the bare import/service import with repository discovery,
       refresh, `addon_utils.enable`, identity/preference checks, and dynamic
       extension service import; keep real MPFB register lifecycle.
       - UI/DB/render checks: N/A; verify addon registry instead.
       - Mini QA: compile, focused tests, and source review.
       - Evidence target: `E1-P1B-SRC1`, `E1-P1B-TEST1`.
  - Implementation Gate: P1-A PASS; adapter/firewall source unchanged.
  - Acceptance:
    - Source: one bounded entrypoint diff; no upstream or sibling mutation.
    - Runtime: changed path passes all addon gates.
    - Behavior: focused checks/compile pass; no broad claim.
    - Evidence IDs: `E1-P1B-*`.
    - Actual-status rows refreshed: source subject/remediation.
  - Evidence Targets: `E1-P1B-*`.
  - Actual-status Update: record candidate SHA/tree and frozen diff.
  - Commit Boundary: one commit after focused checks and detect-changes.

### P2: One real character smoke

- Phase Goal: run the frozen canonical route once and stop at first new blocker.
- Phase Boundary:
  - In scope: exact preflight, addon gates, firewall, one neutral character,
    GLB/provenance validators, cleanup, and Game Truyen immutability.
  - Out of scope: retries, extra characters, hardening, visual/browser QA,
    integration, release, or promotion.
  - Dependencies: P1-B source commit and root-hash-valid runtime.
- Phase Implementation Rule: no downstream PASS is inferred after a failure.
- Ordered Slice List:
  - P2-A: Frozen preflight and addon gates.
  - P2-B: One character and artifact/cleanup proof.

- [ ] P2-A: Frozen preflight and addon gates.
  - Goal: prove the final launch subject before generation.
  - Scope Boundary: logs/evidence only; all source/runtime inputs frozen.
  - Non-Goals: no character call if any addon gate fails.
  - Pre-flight Questions: native runtime; UI/DB/Docker/Playwright N/A; output
    empty; exact pins/security source revalidated.
  - Work Steps:
    1. Revalidate subject, pins, root hash, recipe, executable, output, and
       unchanged firewall/adapter files.
       - UI/DB/render checks: N/A.
       - Mini QA: independent precondition output.
       - Evidence target: `E2-P2A-BIND1`.
    2. Run the final child until identity, preference, and register markers;
       stop before character creation on the first failure.
       - UI/DB/render checks: N/A.
       - Mini QA: classify downstream NOT_RUN if blocked.
       - Evidence target: `E2-P2A-ADDON1..2`.
  - Implementation Gate: P1-B frozen and exact.
  - Acceptance: all addon gates PASS or exact blocker recorded.
  - Evidence Targets: `E2-P2A-*`.
  - Actual-status Update: mark P2-B ready only after PASS.
  - Commit Boundary: no source commit.

- [ ] P2-B: One character and artifact/cleanup proof.
  - Goal: execute one neutral recipe through the existing canonical route.
  - Scope Boundary: isolated outputs/logs/receipts; source and Game Truyen
    inspect-only; firewall/adapter preserve-only.
  - Non-Goals: no retry or scope expansion.
  - Pre-flight Questions: core assets and one neutral recipe; native runtime;
    independent artifact/provenance validation; exact firewall cleanup.
  - Work Steps:
    1. Run adapter with authorization, firewall isolation, shell-free Blender,
       and one neutral character.
       - UI/DB/render checks: N/A.
       - Mini QA: stop at first real failure.
       - Evidence target: `E2-P2B-RUN1`, `E2-P2B-STOP1`.
    2. If files exist, validate GLB/provenance bytes independently, output
       allowlist, size/hash, cleanup/absence, and Game Truyen fingerprint.
       - UI/DB/render checks: N/A.
       - Mini QA: independent disk validation.
       - Evidence target: `E2-P2B-ARTIFACT1..2`, `E2-P2B-CLEAN1`,
         `E2-P2B-IMMUT1`.
  - Implementation Gate: P2-A PASS.
  - Acceptance: full route PASS or first exact downstream blocker.
  - Evidence Targets: `E2-P2B-*`.
  - Actual-status Update: final terminal verdict is only set from direct proof.
  - Commit Boundary: no source commit.

- [ ] P3-A: Call supervisor for the implemented-plan acceptance loop.
  - Goal: independently review exact subject, source, runtime, and evidence.
  - Work Steps: review source/diff, ledgers, logs, artifacts, cleanup, and old
    blocker; on REJECT return only to failed bounded slice and re-review.
  - Implementation Gate: all in-scope slices complete or blocked exactly.
  - Acceptance: one Supervisor PASS or evidence-backed REJECT.

- [ ] P3-B: Remove dead work created during this plan.
  - Goal: keep only useful bounded artifacts and preserve historical evidence.
  - Work Steps: inspect plan-created files, remove only exact dead artifacts,
    then run Supervisor cleanup review.
  - Implementation Gate: no unrelated/rejected source remains.
  - Acceptance: final diff has no dead plan-created artifact.

- [ ] P3-C: Close the plan.
  - Goal: finalize evidence, benchmark, change detection, commit/PR state, and
    exact return fields without merge.
  - Work Steps: record final native runtime proof, source subject, security and
    immutability checks, and terminal verdict.
  - Implementation Gate: P3-A/P3-B pass or record blocker.
  - Acceptance: evidence complete and worktree/PR state known.

## Risk Notes

- `.git` in the supplied root is invalid; it is untouched. All subject identity
  comes from the fresh clone.
- Direct probes created five `.pyc` files; they were quarantined only after
  exact archive comparison, restoring the manifest root hash.
- `BLENDER_USER_CONFIG`/`SCRIPTS` are valid overrides, but extension user data
  also needs `BLENDER_USER_EXTENSIONS` or Blender's supported portable folder.
- A real MPFB downstream failure is not a second fix opportunity; stop and
  report it exactly.
