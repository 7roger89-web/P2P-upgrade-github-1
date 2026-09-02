# P2P Social Content Skills Phase 1 Plan

## Metadata

- Date: `2026-09-02`
- Status: `draft`
- Plan: `Docs/plans/2026-09-02-p2p-social-content-skills-01/2026-09-02-p2p-social-content-skills-01-plan.md`
- Evidence: `Docs/plans/2026-09-02-p2p-social-content-skills-01/2026-09-02-p2p-social-content-skills-01-evidence.md`
- Benchmark: `Docs/plans/2026-09-02-p2p-social-content-skills-01/2026-09-02-p2p-social-content-skills-01-benchmark.md`
- Actual status: `Docs/plans/2026-09-02-p2p-social-content-skills-01/2026-09-02-p2p-social-content-skills-01-actual-status.md`

## Goal

Create the minimum provider-neutral P2P Content Studio capability layer from
the five skills at the exact upstream pin. The layer uses the existing single
router, registry, vendor loader, and context-pointer machinery. It exposes
separate on-demand capability identities for voice profiling, social drafting,
hook generation, content-matrix ideation, and strict post formatting without
installing providers or creating a second runtime authority.

## Rules

- Complete P0 actual status before implementation work.
- Update each checklist item immediately when it is completed.
- Record evidence as work completes.
- Record benchmarkable counts or measurements when they are taken.
- Update later phase status assumptions, next actions, and work steps when actual-status evidence changes the repo state.
- After completing a phase or implementation slice and refreshing `actual-status.md`, update the next affected phase's work steps as needed to match the latest repo reality, while preserving that phase's original goal, scope, acceptance criteria, and major phase order.
- Run Anvien detect-changes before every implementation-slice commit when implementation work was performed.
- This is a Python/JSON/Markdown capability-source change; no UI, database, Docker, external-service, or browser surface is introduced. Those checks are `N/A` and must not be replaced with fake runtime evidence.
- Any source or test temporary output stays below the repository-local `.tmp/` path.
- Preserve `creative.copywriting` as the marketing/double-semantic authority and preserve the separate Humanizer candidate boundary.
- Never copy upstream examples, references, assets, provider instructions, personal sample text, or host configuration into the canonical source.
- Never promote, merge, publish, deploy, or mutate Issue #59 or any other project.
- Every implementation phase is decomposed into executable slices; do not implement `P1` directly.
- Hidden fallback is forbidden. Missing user writing evidence, stale context, unsupported research, or an unavailable optional operation remains visible as `INCOMPLETE`, `UNKNOWN`, or a blocked result.

## Problem

The canonical registry currently has a marketing-only `creative.copywriting`
skill and separate visual/media capabilities, but no provider-neutral Content
Studio family. The upstream repository provides five useful but host-specific
workflows. Directly importing them would add Claude/Cowork/AskUserQuestion
assumptions, default sample data, external research expectations, and file or
publishing behavior that is outside this workstream. The capability family
must therefore be projected selectively and must not compete with existing
copywriting or Humanizer authority.

## Scope

- Repository: `7roger89-web/P2P-upgrade-github-1`, Issue `#60`.
- Workstream: `P2P-SOCIAL-CONTENT-SKILLS-01`.
- Isolated branch/worktree: `codex/p2p-social-content-skills-01` at `.tmp/p2p-social-content-skills-01`.
- Canonical base: commit `0ee414147ae308ab1f6035d1e7776292752bd8da`, tree `f34719776bee67a731c4049b79165bd3deaa3074`.
- Upstream source: `charlie947/social-media-skills`, commit `d2e948719eafc8ed9e2436357ad18489bb371a81`, tree `f11c2f93bc1ff3d927e36842f0bb40ea1b639650`, MIT.
- Exact source audit: `skills/voice-builder/SKILL.md`, `skills/post-writer/SKILL.md`, `skills/hook-generator/SKILL.md`, `skills/content-matrix/SKILL.md`, and `skills/post-formatter/SKILL.md`.
- Projected capability IDs, subject to registry validation: `creative.social.voice_profile`, `creative.social.post`, `creative.social.hook`, `creative.social.content_matrix`, and `creative.social.post_format`.
- Existing surfaces to reuse: `.p2p/system/p2p_capabilities/capabilities.json`, `.p2p/system/p2p_capabilities/vendor_skill.py`, `.p2p/system/p2p_capabilities/routing.py`, `.p2p/system/p2p_uiux/router.py`, and the existing context-pointer contract.
- The accepted projection is a sparse local snapshot consisting only of adapted provider-neutral entrypoints and the upstream MIT license. Each capability gets its own snapshot root so loading one entrypoint does not load the other four.

## Non-Goals

- No bulk import of the upstream repository.
- No raw upstream `SKILL.md` copy, upstream references, sample data, examples, assets, scripts, or default Charlie Hills voice.
- No Claude, Cowork, AskUserQuestion, Claude for Chrome, Gemini, interactive-chart, or host-specific runtime requirement.
- No new router, agent, meta-agent, content orchestrator, interactive-form engine, context daemon, memory platform, database, provider, package, or external service.
- No APIFY token, Google AI API key, social account, browser automation, scraping, publishing, analytics, niche research, video/image/carousel/graphic integration, or paid account.
- No changes to Issue #51 / PR #53 implementation, no Humanizer repair/merge, and no change to Humanizer authority.
- No Issue #59 Character Forge mutation and no mutations to Game Truyện, Gia Phả, or Logistics.
- No Phase 2 upstream skills: scorer, research, reels, analytics dashboard, profile optimizer, graphic designer, Gemini infographic/carousel, quote post, thumbnail, pinned comment, or newsletter voice.

## Requirements

### Invariant Family Map

- Family: provider-neutral on-demand vendor capability boundary.
- SSOT: the approved capability foundation, manifest, routing/readiness, context-pointer, trust-boundary, execution-evidence, provider-abstraction, and host-projection SPECs under `Docs/SPEC/`.
- Authority: the existing registry/model, existing single router, existing vendor loader, existing context machinery, and user-supplied content. Upstream prose is reference data only.
- Sibling surfaces: existing `creative.copywriting`, `media.whiteboard_animation`, `visual.gpt_image_2_style_library`, the Humanizer PR #53 candidate, `routing.py`, `vendor_skill.py`, `p2p_uiux/router.py`, context-pointer code, vendor integration tests, and host projection code.
- Forbidden fallback: global activation, loading all vendor content, fabricated voice without required samples, external research/provider execution, auto-publishing, implicit Humanizer invocation, or a new router/orchestrator.
- Verify matrix: exact source hashes and license; registry validity; one-capability route selection; metadata-only discovery; selected-only load; voice-context pointer linkage; Humanizer distinction; source snapshot determinism; negative external-service/host-assumption cases; clean isolation.

### Capability boundaries

- `creative.social.voice_profile`: adapt the upstream voice-analysis workflow. Require user-provided evidence for a complete profile, preserve `about-me` and `voice-profile` as bounded context outputs, and never persist a separate memory platform or use a starter sample as user truth.
- `creative.social.post`: adapt voice-aware social drafting. It consumes a selected, resolved voice context when the user asks for their voice, uses only supplied facts/context, and produces a reviewable draft rather than a published post.
- `creative.social.hook`: adapt six independent hook variations with bounded lines and explicit no-fabrication for metrics, names, and claims. It is distinct from advertising/double-semantic copywriting.
- `creative.social.content_matrix`: adapt pillar-by-format ideation using shared context or explicit user pillars. It emits a bounded table/read model and does not require a chart, file write, or external research service.
- `creative.social.post_format`: adapt strict framework formatting for PAS/AIDA/BAB/STAR/SLAY. It is a formatter, not a freeform voice writer, and does not publish or automatically humanize.

### Shared voice context model

The projection uses existing context pointers, not a second memory system. The
voice capability may produce a deterministic context payload with bounded
fields: `about_me`, `voice_profile`, `audience`, `topic_pillars`, `point_of_view`,
`brand_promise`, `off_limits`, `tone`, `sentence_rhythm`, `hook_patterns`,
`opening_patterns`, `closing_patterns`, `signature_phrases`,
`absence_signals`, and `prohibited_constructions`. The payload is complete only
when the required user sample evidence is present. Metadata stores counts,
hashes, scope, and provenance, never full private samples. Downstream writing
capabilities reference the pointer by ID and resolve only selected, fresh
content.

## Acceptance Criteria

- All five pinned upstream skills have a per-skill audit with content SHA-256, license boundary, dependencies, host assumptions, overlap, decision, proposed capability ID, source-vendoring decision, and rationale.
- The registry remains valid with the exact eight canonical identities, denominator `8`, and full quorum `8/8`.
- The five accepted capabilities are separate `SKILL` records, noncanonical, non-optional, `MODEL_ROUTABLE`, `ON_DEMAND`, offline-safe, and backed by exact provenance.
- `creative.copywriting` remains singular and marketing-only for its domain; social hook/post requests do not select it as an accidental secondary authority.
- Discovery returns metadata only. Loading one selected capability loads only that capability's adapted entrypoint and its local license; the other four remain unloaded.
- The voice contract requires user evidence for a complete profile, preserves sample precedence, exposes bounded shared context pointers, and forbids default personal voice fabrication.
- Post drafting, hooks, matrix, and formatting remain independently selectable and do not auto-load the complete family.
- Humanizer compatibility is `VOICE_BUILDER_HUMANIZER_CONFLICT=NO`: Humanizer remains optional downstream prose polishing, and no Humanizer source/authority is changed.
- Focused tests pass for discovery, selection, selected-only loading, context linkage, deterministic projection, provider neutrality, forbidden actions, and fail-closed cases.
- `GLOBAL_ACTIVATION=NO`, `SECOND_ROUTER_CREATED=NO`, `SECOND_ORCHESTRATOR_CREATED=NO`, `EXTERNAL_SERVICE_EXECUTION=NO`, and all three other-repository mutation flags remain `NO`.
- One stable candidate commit/branch and one draft PR are prepared; no merge or promotion is performed. One independent Supervisor reviews the stable candidate.

## Checklist

- [x] P0-A: Complete actual status before implementation work.
  - Goal: establish the real current state.
  - Work Steps: verify canonical SHA/tree and isolated worktree; inspect registry, vendor loader, router, context, existing copywriting, visual/media entries, Humanizer PR #53, upstream pin, and Anvien relationship evidence; classify preserve/edit/inspect-only surfaces and update P1 assumptions.
  - Implementation Gate: no implementation or editing starts until `Docs/plans/2026-09-02-p2p-social-content-skills-01/2026-09-02-p2p-social-content-skills-01-actual-status.md` has a completed P0 decision.
  - Acceptance: actual status identifies correct, partial, missing/unbound, fake-or-stub, and blocked surfaces for this scope.

### P1: Selective provider-neutral capability projection

- Phase Goal: add only the five justified adapted capability entrypoints, local MIT license copies, exact upstream/projection provenance, valid registry records, and narrow conflict boundaries around existing marketing copywriting.
- Phase Boundary:
  - In scope: five adapted Markdown entrypoints, five isolated snapshot roots, registry records, provenance, and targeted copywriting trigger exclusions needed to prevent social-content overlap.
  - Out of scope: loader/router/context implementation changes unless a focused failing test proves an existing field cannot express the contract; all external services, user data, host configuration, publishing, Phase 2 skills, and other repositories.
  - Dependencies: P0-A complete; exact canonical/upstream pins verified; existing vendor loader and context machinery proven reusable.
- Phase Implementation Rule: do not implement `P1` directly. Implement `P1-A`, verify it, record evidence, refresh actual-status, commit when required, then implement `P1-B`.
- Ordered Slice List:
  - P1-A: Create sparse adapted snapshots, provenance, and registry boundaries.
  - P1-B: Add focused behavior and fail-closed tests for the complete family.

- [x] P1-A: Create sparse adapted snapshots, provenance, and registry boundaries.
  - Goal: make the five accepted capabilities discoverable and loadable through the existing P2P vendor mechanism without raw bulk import or global activation.
  - Scope Boundary:
    - Editable: `.p2p/system/p2p_capabilities/capabilities.json`, `.p2p/vendor/skill/<five-isolated-projection-roots>/SKILL.md`, `.p2p/vendor/skill/<five-isolated-projection-roots>/LICENSE`, and `.p2p/vendor/provenance/p2p-social-content-skills-01.json`.
    - Inspect-only: upstream audit checkout, `vendor_skill.py`, `routing.py`, `p2p_uiux/router.py`, existing context machinery, `creative.prose.humanize` PR #53 candidate, visual/media vendors, Issue #59 worktrees.
    - Preserve-only: canonical identities/quorum fields, existing `creative.copywriting` meaning and non-social behavior, all existing vendor snapshots, and all non-P2P projects.
    - Out of scope: runtime module/engine, new router, persistent voice storage, provider/API, research/publishing path, and raw upstream files.
  - Non-Goals: no user-specific samples, default author profile, external research, interactive form/chart implementation, file publication, or Humanizer modification.
  - Pre-flight Questions:
    - Data source: exact pinned upstream SKILL.md content as reference plus user request and existing P2P contracts.
    - Display permission: metadata may expose IDs, hashes, license, scope, and readiness; never private sample text.
    - DB read flow: N/A; no database is touched.
    - DB write flow: N/A; registry/vendor source files are the only bounded code-repository writes.
    - Render location: N/A; no UI surface is changed.
    - UI behavior flow: N/A; user-visible route semantics are covered by direct Python behavior tests.
    - Docker runtime: N/A; no app/runtime/container surface is changed.
    - Playwright target: N/A; no browser-visible behavior is changed.
    - Behavior test: deferred to P1-B after source behavior is correct.
    - Cleanup/quarantine: upstream audit checkout remains under repo-local `.tmp`; no user/project files are test targets.
    - External side effects: none; no network/provider/API/social account execution.
    - N/A notes: source-only projection has no UI, DB, browser, Docker, or deployment boundary.
  - Work Steps:
    1. Create one provider-neutral adapted entrypoint and MIT license in an isolated snapshot root for each accepted upstream skill; include explicit input/output/failure boundaries, no host tool names, no default sample, no publishing, and no automatic Humanizer.
       - UI flow check: N/A; verify the entrypoint is host-neutral text and does not define a new interaction engine.
       - DB/data flow check: N/A; verify no private sample text or persistent user voice data enters the snapshot.
       - Render location check: N/A; verify no UI/render asset exists.
       - Evidence target: per-entrypoint projection hash, file list, forbidden-marker scan, and license hash.
    2. Add exact registry/provenance records and only the narrow existing-copywriting trigger exclusions required to make social post/hook requests select the specialist capability without changing advertising behavior.
       - UI flow check: N/A; route output is the observable boundary.
       - DB/data flow check: N/A; validate registry JSON and provenance without external writes.
       - Render location check: N/A; no render output.
       - Evidence target: registry validation, exact upstream/projection/source hashes, snapshot hashes, route boundary checks, and `git diff --check`.
  - Implementation Gate:
    - P0-A is complete; exact pins still match fresh fetches; all target source files have pre-edit impact evidence or are new bounded files.
    - The five capability IDs remain unique and all fields satisfy the six-class manifest contract.
    - The existing loader and router can express isolated on-demand snapshots without source changes.
  - Acceptance:
    - Source: five isolated adapted entrypoints and licenses exist; provenance maps each upstream path and hash; no raw examples/references/assets/scripts are vendored.
    - Runtime/UI: existing `discover_vendor_skills` and `foundation_route` expose metadata/readiness while content remains unloaded; no UI runtime applies.
    - DB/data: N/A; no DB state changes.
    - Behavior test: P1-B covers the source contract after this slice; source-only smoke confirms registry loads.
    - Cleanup/quarantine: audit checkout and test outputs stay below `.tmp`; no unrelated worktree changes remain.
    - Evidence IDs: `E1-P1A-SRC1..E1-P1A-SRC8` and `E1-P1A-ROUTE1..E1-P1A-ROUTE4`.
    - Actual-status rows refreshed: registry/projection rows transition `missing/partial -> correct` only after direct evidence.
  - Evidence Targets: exact hashes, registry validity, isolated file inventories, route metadata, no raw upstream file inventory, and clean diff boundary.
  - Actual-status Update: record each projection root, registry, and overlap boundary as correct/partial with exact evidence; update P1-B assumptions before tests.
  - Commit Boundary: commit after this slice when source smoke, registry validation, and diff checks pass.

- [x] P1-B: Add focused behavior and fail-closed tests for the complete family.
  - Goal: prove the five capabilities are independently selectable, on-demand, provider-neutral, context-compatible, deterministic, and distinct from Humanizer/copywriting.
  - Scope Boundary:
    - Editable: new `tests/test_p2p_social_content_skills.py` and the four plan/evidence/status ledgers.
    - Inspect-only: P1-A source, existing vendor tests, existing foundation tests, Humanizer candidate, and all out-of-scope projects.
    - Preserve-only: all production capability/runtime source from P0 except the already-reviewed registry boundary.
    - Out of scope: broad regression, Docker/Playwright, external-service tests, browser automation, and Phase 2 capabilities.
  - Non-Goals: do not manufacture social output, user samples, provider receipts, or runtime certification; tests use synthetic fixtures only.
  - Pre-flight Questions:
    - Data source: synthetic samples/context and current registry/projection bytes.
    - Display permission: assertions use bounded synthetic values, IDs, hashes, and route metadata only.
    - DB read flow: N/A.
    - DB write flow: temporary test directories only; cleanup/quarantine is mandatory.
    - Render location: N/A.
    - UI behavior flow: N/A; direct trigger/process/observable-result tests cover the contract.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: `python -m unittest -q tests.test_p2p_social_content_skills` plus focused compile/hash checks.
    - Cleanup/quarantine: every temporary fixture is under the worktree `.tmp` and removed by context managers.
    - External side effects: none; assert no network/credential/permission path.
    - N/A notes: no UI, DB, server, or container path exists in the changed surface.
  - Work Steps:
    1. Write behavior tests for route selection, metadata-only discovery, selected-only loading, shared voice pointer references, Humanizer distinction, copywriting non-overlap, and stable snapshot/registry projection.
       - UI flow check: N/A; test the existing router return object.
       - DB/data flow check: N/A; synthetic context only and no persistent data.
       - Render location check: N/A.
       - Evidence target: named test methods with direct trigger -> route/load -> observable result assertions.
    2. Write negative tests for global auto-activation, missing voice evidence, unsupported provider/service execution, Claude-specific runtime assumptions, second router/orchestrator markers, raw private sample metadata, and accidental loading of all five capabilities.
       - UI flow check: N/A.
       - DB/data flow check: N/A; verify temporary cleanup and no protected path writes.
       - Render location check: N/A.
       - Evidence target: fail-closed test results, temporary-root cleanup, source marker scan, and no-mutation assertions.
  - Implementation Gate:
    - P1-A is committed and actual-status has been refreshed.
    - Tests assert behavior rather than file existence alone and use no real user/private data.
    - No existing stale test needs adjustment; if a direct registry count test fails only because it encodes an unrelated baseline, record it as out of scope instead of broadening this change.
  - Acceptance:
    - Source: test file is direct, bounded, and contains no provider/API credentials or private samples.
    - Runtime/UI: all route/load assertions pass; no UI/runtime applies.
    - DB/data: N/A; temporary fixture cleanup passes.
    - Behavior test: all named positive and negative cases pass.
    - Cleanup/quarantine: no test output escapes `.tmp`; worktree status contains only intentional plan/source/test files.
    - Evidence IDs: `E1-P1B-TEST1..E1-P1B-TEST12` and `E1-P1B-NEG1..E1-P1B-NEG8`.
    - Actual-status rows refreshed: all accepted capability rows become `correct` only when tests and source hashes agree.
  - Evidence Targets: focused test output, compile output, clean status, and direct proof of each fail-closed invariant.
  - Actual-status Update: append a refresh row with source-to-test status transitions and record any unrelated stale baseline as out of scope.
  - Commit Boundary: commit after all focused tests, compile, hash, and diff checks pass.

- [x] Pn-A: Call the supervisor for the implemented-plan acceptance loop.
  - Goal: independently review the stable candidate against Issue #60, the exact base/upstream pins, plan, source, tests, provenance, and isolation boundaries.
  - Work Steps:
    1. Provide one independent Supervisor the exact candidate commit/tree, worktree path, plan/evidence, source diff, focused test output, and required return fields.
    2. If Supervisor rejects, create a separate fix slice/commit for the material finding only, rerun direct verification, and request one re-review; do not loop without a material issue.
  - Implementation Gate: P1-A and P1-B are complete, reports are written, and no unresolved same-invariant surface remains. The first PASS was recorded for the pre-reconciliation subject; the remote main movement required one fresh exact-subject review.
  - Acceptance: one independent Supervisor returns `PASS` for the reconciled candidate, or a documented blocker stops the work honestly.

- [x] Pn-B: Remove dead work created during this plan.
  - Goal: ensure the final diff contains only artifacts serving the accepted selective intake.
  - Work Steps:
    1. Review every plan-created source, test, provenance entry, report, and temporary output.
    2. Remove only dead artifacts created by this plan; preserve the upstream audit checkout until report evidence is complete, then leave it quarantined under `.tmp` or explicitly record its retention.
    3. Run a final status/diff boundary check and have the Supervisor include cleanup in the same single review package.
  - Implementation Gate: cleanup targets are plan-created and exact; no user or concurrent worktree is a target.
  - Acceptance: final diff has no rejected raw import, stale placeholder, unused helper, or out-of-scope integration.

- [ ] Pn-C: Close the plan.
  - Goal: record final evidence, benchmark counts, detect-changes, commit identity, PR identity, Supervisor verdict, and stop at `OWNER_GATE`.
  - Work Steps:
    1. Run focused final validation and compile checks; no broad unrelated suite or Docker/Playwright substitution is required for this source-only scope.
    2. Run Anvien `detect-changes` after the final graph refresh and before the closing implementation commit; preserve the command/result in evidence.
    3. Record final candidate head/tree and PR without merge, release, promotion, deployment, or publication.
  - Implementation Gate: Pn-A and Pn-B pass or have an explicit blocker.
  - Acceptance: all return fields are populated, the candidate is stable, one Supervisor verdict is recorded, and `NEXT_STEP=OWNER_GATE`.

## Risk Notes

- Registry routing is a shared contract with a high graph warning in the existing test family. Keep the mutation limited to new records and precise social-overlap exclusions; do not rewrite router code.
- The existing root `.git` is malformed. Git authority is the valid `p2p-humanizer-01` clone and the isolated Issue #60 worktree; do not repair root metadata.
- Current Anvien indexes do not expose the hidden `.p2p/system` files through normal file-detail, so source reading plus indexed sibling-test detail are used and the limitation is recorded. Never treat an ambiguous alias as evidence.
- Upstream `post-writer` asks for research; this projection must not turn that into an external web/provider requirement. User-supplied context is the only accepted fact source in Phase 1.
- Upstream `voice-builder` contains a starter sample path. It is explicitly excluded so no third-party or Charlie Hills voice becomes a default user profile.
- The Humanizer PR #53 is open/draft and unmerged. Compatibility is a boundary assertion only; no candidate repair or merge is allowed here.
