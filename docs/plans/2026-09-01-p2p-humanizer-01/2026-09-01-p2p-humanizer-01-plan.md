# P2P-HUMANIZER-01 Plan

## Metadata

- Date: `2026-09-01`
- Status: `in_progress`
- Plan: `docs/plans/2026-09-01-p2p-humanizer-01/2026-09-01-p2p-humanizer-01-plan.md`
- Evidence: `docs/plans/2026-09-01-p2p-humanizer-01/2026-09-01-p2p-humanizer-01-evidence.md`
- Benchmark: `docs/plans/2026-09-01-p2p-humanizer-01/2026-09-01-p2p-humanizer-01-benchmark.md`
- Actual status: `docs/plans/2026-09-01-p2p-humanizer-01/2026-09-01-p2p-humanizer-01-actual-status.md`

## Goal

Integrate `blader/humanizer` version `2.11.2` as the smallest selective P2P
Markdown writing capability. Reuse the existing capability registry, single
router, vendor-skill loader, provenance, and progressive-disclosure boundary.
The candidate must stop before merge or promotion and expose a reviewable
one-branch/one-PR subject for Issue #51.

## Rules

- Complete P0 actual status before implementation work.
- Update each checklist item immediately when it is completed.
- Record evidence as work completes.
- Record benchmarkable counts or measurements when they are taken.
- Update later phase status assumptions, next actions, and work steps when actual-status evidence changes the repo state.
- After completing a phase or implementation slice and refreshing `actual-status.md`, update the next affected phase's work steps as needed to match the latest repo reality, while preserving that phase's original goal, scope, acceptance criteria, and major phase order.
- Run Anvien detect-changes before every implementation-slice commit when implementation work was performed.
- For public runtime or UI-facing changes, validate the real user-visible runtime with browser or Playwright evidence.
- This is a non-UI Markdown-skill integration; Docker and Playwright are N/A because no public runtime or UI is changed.
- Keep the standard planner structure. These detail rules only make phase checklist items concrete enough to implement safely.
- Every implementation phase must be decomposed into multiple implementation slices that are as small as practical. A phase is a grouping and ordering container; a slice is the executable implementation unit.
- Do not implement a phase directly. Work starts from a slice ID such as `P1-A`, `P1-B`, or `P2-C`.
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
- Hidden fallback is forbidden. Prefer a visible failure over a fallback that hides a broken primary path.
- Tests must prove product behavior. The focused fixture tests are bounded value/boundary evaluations for a Markdown prompt capability; they must not become a new rewrite engine.
- Any temporary fixture output is cleaned or quarantined under repo-local `.tmp/`; preserve-only package, release, and user paths are never mutation targets.

## Problem

P2P already has one active `creative.copywriting` vendor skill for advertising
and double-semantic marketing copy. It is not a general editing or
humanization capability. The requested Humanizer source is a standalone
Markdown skill, but copying the whole upstream repository or adding another
engine would violate P2P's existing vendor boundary. The integration must keep
the Humanizer prompt's no-fabrication and voice-calibration contracts while
making P2P's stricter machine/evidence preservation boundary explicit.

The current `origin/main` baseline also contains seven known pre-existing
failures in a wider legacy-focused suite (stale capability counts, stale
routing expectations, and an external-framework assertion). They are recorded
as baseline evidence, not silently repaired as part of this bounded issue.

## Scope

- Fresh-fetch and bind the current P2P `origin/main` subject.
- Audit the exact upstream Humanizer commit/tree, version, MIT license, and
  raw Git `SKILL.md` hash.
- Copy only upstream `SKILL.md` and `LICENSE` into one repo-local vendor
  snapshot.
- Add one noncanonical `SKILL` manifest entry using the existing registry and
  existing vendor-skill loader, with `USER_REQUESTED`/explicit selection,
  `ON_DEMAND` loading, no dependencies, no network, and no credentials.
- Reconcile against `creative.copywriting`; do not alter or duplicate it.
- Add a small focused test/fixture set proving routing, loading, provenance,
  no-fabrication, voice-sample precedence, Markdown protected spans, and
  technical evidence preservation.
- Run nearest-boundary validation, a full Python compile/build-equivalent for
  this non-UI package, change detection, and create one linked PR without
  merging or promoting.

## Non-Goals

- No new runtime subsystem, rewrite engine, provider, daemon, database,
  service, second registry, router, prompt framework, or authorization
  architecture.
- No AI-detector evasion or detector-bypass claim.
- No upstream scripts, plugin metadata, README, agents, symlinks, or unrelated
  repository content in the P2P snapshot.
- No rewriting of source code, code blocks, shell commands, hashes, Git SHAs,
  URLs/link targets, citations, quoted evidence, JSON/YAML/TOML, structured
  tables/data, provenance, security evidence, QA packets, or Supervisor return
  packets.
- No global/default activation, dependency installation, network call, host
  configuration mutation, release, deployment, merge, promotion, or Owner
  approval execution.
- No broad regression repair unrelated to the Humanizer invariant family.

## Requirements

### Invariant Family Map

- Family: `selective-vendor-markdown-writing-capability`.
- SSOT: `docs/SPEC/P2P-CAPABILITY-MANIFEST-SPEC.md`,
  `P2P-CAPABILITY-ROUTING-READINESS-SPEC.md`,
  `P2P-CAPABILITY-CONTEXT-POINTER-SPEC.md`,
  `P2P-CAPABILITY-TRUST-DATA-INSTRUCTION-SPEC.md`,
  `P2P-CAPABILITY-EXECUTION-EVIDENCE-SPEC.md`, and
  `P2P-HOST-SKILL-PROJECTION-SPEC.md`.
- Authority source: current user Issue #51 request plus the existing P2P
  registry/model/router/vendor-skill implementation.
- Sibling runtime surfaces: `creative.copywriting`,
  `media.whiteboard_animation`, `visual.gpt_image_2_style_library`,
  `p2p_capabilities.vendor_skill`, `p2p_capabilities.routing`, and host
  projection consumers. They remain preserve-only or are verified unaffected.
- Forbidden alternate paths: a second skill engine, global skill injection,
  direct upstream execution, provider branch, dependency installer, full-tree
  load, content-to-permission path, or a second router.
- Stale artifacts to identify: hardcoded registry-count/routing tests and any
  report or plan that assumes Humanizer is already present.
- Verify matrix: explicit route; unrelated/no-default route; selected
  entrypoint load; snapshot/entrypoint hash; no-fabrication and voice fixture;
  mixed Markdown protected spans; technical exact values; no network/install;
  existing copywriting route remains marketing-only.

### Capability contract

- Final ID: `creative.prose.humanize`.
- Type: `SKILL`; `CANONICAL_QUORUM_MEMBER=false`;
  `OPTIONAL_SPECIALIST=false`; `STATUS=ACTIVE`.
- Invocation: `USER_REQUESTED`, upstream load mode `ON_DEMAND`, selection mode
  `EXPLICIT_OR_PROFILE_SELECTED`; no global default.
- Scope: articles, emails, explanatory docs, public-facing product copy,
  release prose, PR descriptions, user-facing summaries, and owner-visible
  natural prose when selected.
- Contracts: `NO_FABRICATION=YES`; supplied writer samples override generic
  style rules; preserve Humanizer's rewrite/audit/final-rewrite workflow where
  applicable; file mode is prose-only.
- Machine boundary: preserve code, code blocks, commands, hashes/SHA, URLs and
  targets, citations, quoted evidence, structured data/tables, frontmatter,
  provenance, exact contracts, security evidence, and QA/Supervisor packets.
- Technical/legal/compliance/security prose remains semantically precise. The
  capability is not an evasion feature and promises no detector bypass.

## Acceptance Criteria

- One exact current P2P base is recorded with SHA/tree and a clean worktree.
- One exact upstream Humanizer subject is recorded:
  repository `https://github.com/blader/humanizer.git`, commit
  `e2e92e7b4b8229253ed5c8e81dc65463fdeddda5`, tree
  `b8a8804ed9210e539531fc26c2d84fdb603960f4`, version `2.11.2`, MIT, and
  the exact `SKILL.md` hash.
- The P2P snapshot contains exactly `SKILL.md` and `LICENSE`, both unchanged
  from the pinned upstream subject, with a registry snapshot hash matching
  those bytes.
- Exactly one new ID, `creative.prose.humanize`, is added. Existing
  `creative.copywriting` remains singular and unchanged; no duplicate ID,
  router, registry, or skill engine is created.
- Discovery is metadata-only; explicit selection loads only `SKILL.md`; no
  references, assets, scripts, install, network, or credentials are used.
- Focused tests cover A-G from Issue #51, with fixture evidence clearly marked
  as bounded prompt/value evaluation rather than model-runtime certification.
- Nearest validation, compile/build-equivalent, JSON/registry validation,
  `git diff --check`, and Anvien `detect-changes` are recorded.
- One branch and one PR link Issue #51; no merge or promotion is performed.
- Candidate handoff ends `P2P_HUMANIZER_01_CANDIDATE_READY` with
  `NEXT_STEP=INDEPENDENT_SUPERVISOR`.

## Checklist

- [x] P0-A: Complete actual status before implementation work.
  - Goal: establish the real current state.
  - Work Steps: inspect source-of-truth files, classify each surface, record blocked or missing pieces, and update later phase status assumptions, next actions, and work steps from evidence.
  - Implementation Gate: no implementation or editing starts until `docs/plans/2026-09-01-p2p-humanizer-01/2026-09-01-p2p-humanizer-01-actual-status.md` has a final P0 decision.
  - Acceptance: actual status identifies correct, partial, missing/unbound, fake-or-stub, and blocked surfaces for this scope.

### P1: Integrate the pinned Markdown skill through the existing vendor boundary

- Phase Goal: add only the pinned Humanizer prompt/license and one validated
  registry declaration; do not change P2P runtime code.
- Phase Boundary:
  - In scope: `.p2p/vendor/skill/blader-humanizer-e2e92e7/{SKILL.md,LICENSE}` and the one appended `capabilities.json` record.
  - Out of scope: `vendor_skill.py`, router/model changes, host deployment, upstream execution, and unrelated registry normalization.
  - Dependencies: completed P0, exact upstream checkout, current main fetch, and current snapshot hash calculation.
- Phase Implementation Rule: do not implement `P1` directly. Implement `P1-A`, verify it, record evidence, refresh actual-status, commit when required, then continue to `P1-B`.
- Ordered Slice List:
  - P1-A: Vendor exact upstream files and add the minimal manifest record.
  - P1-B: Add focused value/boundary fixtures and direct integration tests.

- [x] P1-A: Vendor exact upstream files and add the minimal manifest record
  - Goal: make `creative.prose.humanize` discoverable through the existing P2P registry and vendor loader while preserving exact upstream bytes and strict P2P boundaries.
  - Scope Boundary:
    - Editable: `.p2p/vendor/skill/blader-humanizer-e2e92e7/SKILL.md`, `.p2p/vendor/skill/blader-humanizer-e2e92e7/LICENSE`, and the one new `capabilities.json` record.
    - Inspect-only: upstream detached checkout, existing `creative.copywriting`, existing `vendor_skill.py`, existing router, host projection, and all release artifacts.
    - Preserve-only: all existing vendor snapshots, registry records, canonical identities, quorum fields, and router code.
    - Out of scope: any upstream file other than the two selected files; any new production module.
  - Non-Goals: no adapter branch, dependency probe, runtime executor, prompt transformation, provider selection, or default activation.
  - Pre-flight Questions:
    - Data source: exact detached upstream commit/tree and raw Git blobs.
    - Display permission: N/A; this is a validated data/skill manifest, not a permission grant.
    - DB read flow: N/A; no database exists in this boundary.
    - DB write flow: N/A; no persistent application data is touched.
    - Render location: N/A; the skill returns prompt content only.
    - UI behavior flow: N/A; no public UI is changed.
    - Docker runtime: N/A; this is a non-UI Python/Markdown package slice.
    - Playwright target: N/A; there is no user-visible runtime target.
    - Behavior test: load/route/hash tests in P1-B after production bytes are correct.
    - Cleanup/quarantine: all scratch copies/logs stay under repo-local `.tmp/` and are removed or retained only as debug evidence.
    - External side effects: no upstream writes, installs, network calls after audit, or host mutations.
    - N/A notes: exact upstream checkout is inspect-only and must remain detached/clean.
  - Work Steps:
    1. Copy exactly the upstream `SKILL.md` and `LICENSE` bytes into the allowlisted P2P vendor root, compute raw/canonical entrypoint and tree hashes, and confirm no unrelated upstream files were copied.
       - UI flow check: N/A; no UI surface.
       - DB/data flow check: verify only the two intended vendor files exist and registry source remains parseable.
       - Render location check: N/A; no render path.
       - Mini QA for each completed implementation slice (MUST) 
          For Codex: When Mini QA must use plugins
            - Browser: N/A because no browser behavior exists.
            - Chrome: N/A because no browser behavior exists.
            - Computer Use: N/A because no desktop app behavior exists.
            - Playwright: N/A because no browser behavior exists.
          For Claude or other agents:
            - Use the equivalent browser, Chrome/session, or computer-control capability exposed by that agent/runtime or Playwright-like capability available in that environment.
       - Evidence target: exact file list, upstream comparison, `snapshot_tree_sha256`, and entrypoint hash.
    2. Append one manifest record with `creative.prose.humanize`, upstream provenance, MIT license, `USER_REQUESTED`, `ON_DEMAND`, no dependencies/network/credentials, no-fabrication, voice, and prose-only preservation fields; validate it through the existing loader.
       - UI flow check: N/A; route output is the observable boundary.
       - DB/data flow check: `load_registry` and `discover_vendor_skills` must accept the record without changing canonical 8/8 or the existing registry invariant.
       - Render location check: N/A; no host materialization.
       - Mini QA for each completed implementation slice (MUST) 
          For Codex: When Mini QA must use plugins
            - Browser: N/A because no browser behavior exists.
            - Chrome: N/A because no browser behavior exists.
            - Computer Use: N/A because no desktop app behavior exists.
            - Playwright: N/A because no browser behavior exists.
          For Claude or other agents:
            - Use the equivalent browser, Chrome/session, or computer-control capability exposed by that agent/runtime or Playwright-like capability available in that environment.
       - Evidence target: registry parse, exact metadata, explicit route selection, no-default route, and no permission/network flags.
  - Implementation Gate:
    - Before editing target files, run the relevant Anvien impact/file-detail command for files, symbols, routes, tools, or contracts touched by this slice, and record the evidence IDs.
    - P0 actual status is complete; exact upstream subject and license are bound; existing capability reconciliation proves no duplicate; current vendor adapter is reusable without code changes.
  - Acceptance:
    - Source: the two snapshot files match the exact upstream subject and the registry has one valid new record.
    - Runtime/UI: `discover_vendor_skills` is metadata-only; explicit route selects the new capability; empty/unrelated request does not select it.
    - DB/data: N/A; no database or application data is changed.
    - Behavior test: the direct P1-B tests can load the new entrypoint and verify all declared hashes/boundaries.
    - Cleanup/quarantine: no scratch file is outside repo-local `.tmp/`; no upstream checkout is modified.
    - Evidence IDs: `E1-P1A-SRC1..E1-P1A-ROUTE2`.
    - Actual-status rows refreshed: Humanizer snapshot/manifest transition `missing -> correct`; adapter/copywriting remain `correct`.
  - Evidence Targets: `E1-P1A-SRC1`, `E1-P1A-REG1`, `E1-P1A-HASH1`, `E1-P1A-ROUTE1`, `E1-P1A-ROUTE2`.
  - Actual-status Update: mark the new vendor snapshot and manifest `correct` only after exact hashes, registry parse, and route/load evidence pass; append R1 and update P1-B assumptions if any field differs.
  - Commit Boundary: commit after this slice when acceptance passes. P1-A acceptance passed with the exact two-file snapshot, registry parse, explicit route, no-default route, selected `SKILL.md` load, and zero network/permission flags.

- [ ] P1-B: Add focused value/boundary fixtures and direct integration tests
  - Goal: prove the requested value and preservation boundary without implementing a rewrite engine or invoking an external model.
  - Scope Boundary:
    - Editable: `tests/test_p2p_humanizer_integration.py` and `tests/fixtures/p2p-humanizer/*` only, plus the P1 evidence/actual-status documents.
    - Inspect-only: production registry/vendor files after P1-A, existing vendor tests, and all unrelated legacy tests.
    - Preserve-only: existing tests unless a directly affected stale invariant is proven.
    - Out of scope: broad regression repair, provider/runtime integration, network/model calls, and UI/browser tests.
  - Non-Goals: fixture pairs are not a claim of model-runtime certification; they only make the bounded writing contract and protected-span expectations executable.
  - Pre-flight Questions:
    - Data source: local before/after fixtures and loaded pinned `SKILL.md`.
    - Display permission: assert `permission_grant=false`; no content grants authority.
    - DB read flow: N/A.
    - DB write flow: N/A; temporary test copies only.
    - Render location: N/A.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: seven focused cases covering naturalness, no fabrication, voice sample, mixed Markdown, technical evidence, default exclusion, and explicit selection.
    - Cleanup/quarantine: use `TemporaryDirectory(..., dir=REPO_ROOT / '.tmp')` for mutable copies; fixtures are static tracked inputs.
    - External side effects: none.
    - N/A notes: no model is called, installed, or substituted.
  - Work Steps:
    1. Add a compact fixture set with an obvious AI-style prose pair, supplied writer sample, mixed Markdown pair, and technical evidence pair; make all protected spans byte-identical between input and expected output.
       - UI flow check: N/A.
       - DB/data flow check: compare frontmatter, fences, inline commands/hashes, URLs, citations, quoted evidence, and structured tables exactly.
       - Render location check: N/A.
       - Mini QA for each completed implementation slice (MUST) 
          For Codex: When Mini QA must use plugins
            - Browser: N/A because no browser behavior exists.
            - Chrome: N/A because no browser behavior exists.
            - Computer Use: N/A because no desktop app behavior exists.
            - Playwright: N/A because no browser behavior exists.
          For Claude or other agents:
            - Use the equivalent browser, Chrome/session, or computer-control capability exposed by that agent/runtime or Playwright-like capability available in that environment.
       - Evidence target: fixture hashes and test assertions proving prose-only change and exact protected content.
    2. Add one direct test module that routes and loads the selected capability through existing P2P surfaces, checks loaded prompt contracts, and runs the fixture value checks; run the focused module before broader validation.
       - UI flow check: N/A; route/load response is the observable flow.
       - DB/data flow check: no persistent writes; temp roots are cleaned/quarantined.
       - Render location check: N/A.
       - Mini QA for each completed implementation slice (MUST) 
          For Codex: When Mini QA must use plugins
            - Browser: N/A because no browser behavior exists.
            - Chrome: N/A because no browser behavior exists.
            - Computer Use: N/A because no desktop app behavior exists.
            - Playwright: N/A because no browser behavior exists.
          For Claude or other agents:
            - Use the equivalent browser, Chrome/session, or computer-control capability exposed by that agent/runtime or Playwright-like capability available in that environment.
       - Evidence target: named test results for A-G, compile/build, `git diff --check`, and Anvien detect-changes.
  - Implementation Gate:
    - Before editing tests, P1-A exact source/registry acceptance must pass and actual-status must show the production surfaces `correct`.
    - Tests must exercise existing `discover_vendor_skills`/`load_vendor_skill`; no helper may become a second production engine.
  - Acceptance:
    - Source: focused tests and fixtures are small, deterministic, and no placeholders or external calls exist.
    - Runtime/UI: route -> existing vendor loader -> observable loaded contract passes for explicit selection and remains absent by default.
    - DB/data: all mutable test roots are under `.tmp` and are cleaned/quarantined.
    - Behavior test: all focused A-G cases pass; the test report names each case and path.
    - Cleanup/quarantine: `git status` contains no test-generated cache or untracked debug output.
    - Evidence IDs: `E1-P1B-TEST1..E1-P1B-TEST7`, `E1-P1B-BUILD1`, `E1-P1B-DETECT1`.
    - Actual-status rows refreshed: focused test surface `missing -> correct`; baseline legacy failures remain explicitly pre-existing/out of scope.
  - Evidence Targets: focused test output, fixture comparison output, package/registry validation, compileall, diff check, and detect-changes.
  - Actual-status Update: append R2 with test evidence and keep any unverified model-runtime claim explicitly `NOT_APPLICABLE`.
  - Commit Boundary: commit after this slice when acceptance passes.

- [ ] P2-A: Call supervisor for the implemented-plan acceptance loop.
  - Goal: verify the completed plan work against the accepted plan, actual-status decisions, evidence, benchmark, changed files, generated output, and validation results before closure.
  - Work Steps:
    1. Call the supervisor skill in a new independent chat to review the full completed plan work.
    2. If supervisor fails the work, return to the responsible implementation workflow/skill for the failed scope only.
    3. Re-run supervisor review after the fix.
    4. Repeat until supervisor passes or records a blocker.
  - Implementation Gate: all planned implementation phases must be completed or explicitly blocked before this review.
  - Acceptance: supervisor review passes, or the plan records a blocker with evidence and no closure is performed.
- [ ] P2-B: Remove dead work created during this plan.
  - Goal: ensure the final diff contains only artifacts that still serve the accepted plan.
  - Work Steps:
    1. Review files, sections, generated output, tests, temp files, and plan artifacts created or modified during this plan.
    2. Remove or rewrite any artifact made obsolete by actual-status findings, user corrections, failed approaches, or phase status updates.
    3. Verify no rejected approach, stale placeholder, unused generated output, or dead helper artifact remains in the final diff.
    4. Call supervisor to review the dead-work cleanup.
    5. If supervisor fails the cleanup, return to the responsible implementation workflow/skill for the failed cleanup scope only, then re-run supervisor review.
  - Implementation Gate: only remove artifacts created by this plan unless the user explicitly approves broader cleanup.
  - Acceptance: final `git diff/status` contains no dead plan-created artifacts, supervisor passes the cleanup, and evidence records what was removed or preserved.
- [ ] P2-C: Close the plan.
  - Goal: finish validation, evidence, benchmark, detect-changes, commit, and final status.
  - Work Steps:
    1. Run the required final validation for the accepted scope, including the non-UI Python compile/build-equivalent before final focused validation.
    2. Regenerate generated outputs if source-of-truth changes require it; none are expected for this vendor/registry slice.
    3. Run Anvien detect-changes before commit when implementation work was performed.
    4. Record final validation, detect-changes, benchmark, and commit evidence.
    5. Commit the completed scope and verify the worktree state.
  - Implementation Gate: P2-A and P2-B must pass or record blockers.
  - Acceptance: final evidence is recorded, required commits exist, and the worktree state is known.

## Risk Notes

- The unpacked parent workspace has unusable Git metadata; all Git authority is
  bound to the fresh clone under repo-local `.tmp`, and that parent workspace
  is not repaired.
- The current main baseline has seven known wider-suite failures. They are
  evidence of baseline drift, not silently counted as Humanizer regressions.
- Anvien intentionally does not project ignored `.p2p` JSON/Python files in
  the current graph; this is recorded, while source and nearest runtime
  validation remain authoritative for those static surfaces.
- The upstream source is prompt content. No test can certify a live model
  rewrite without invoking a provider; the focused fixture tests make that
  limitation explicit rather than fabricating runtime evidence.
- Creating a PR is authorized by the user; merge, release, promotion, and
  approval execution remain out of scope. The handoff must remain
  `NEXT_STEP=INDEPENDENT_SUPERVISOR`.
