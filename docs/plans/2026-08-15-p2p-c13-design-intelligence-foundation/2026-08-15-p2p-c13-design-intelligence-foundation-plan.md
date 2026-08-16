# P2P-C13 Beginner-First Design Intelligence & NUI Faculty Routing Foundation Plan

## Metadata

- Date: `2026-08-15`
- Status: `P4 validation complete / development-source PASS with limitations`
- Plan: `docs/plans/2026-08-15-p2p-c13-design-intelligence-foundation/2026-08-15-p2p-c13-design-intelligence-foundation-plan.md`
- Evidence: `docs/plans/2026-08-15-p2p-c13-design-intelligence-foundation/2026-08-15-p2p-c13-design-intelligence-foundation-evidence.md`
- Benchmark: `docs/plans/2026-08-15-p2p-c13-design-intelligence-foundation/2026-08-15-p2p-c13-design-intelligence-foundation-benchmark.md`
- Actual status: `docs/plans/2026-08-15-p2p-c13-design-intelligence-foundation/2026-08-15-p2p-c13-design-intelligence-foundation-actual-status.md`

## Goal

Implement the minimum beginner-first Design Intelligence foundation under the existing `p2p-uiux` capability. The foundation must classify material UI/UX work, build an integrity-bound task profile, route the smallest sufficient subset of a provenance-bound 174-faculty NUI registry, emit explainable dispositions and lifecycle obligations, and project those obligations to existing C10 Decision Trace, C11 task state, and C12 bounded foreground execution contracts. It must preserve the single-router rule, canonical eight identity rule, optional non-canonical Aesthetica rule, C08/C09 status, and honest render/evidence behavior.

## Rules

- Complete P0 actual status before implementation work.
- Update each checklist item immediately when it is completed.
- Record evidence as work completes.
- Record benchmarkable counts or measurements when they are taken.
- Update later phase status assumptions, next actions, and work steps when actual-status evidence changes the repo state.
- After completing a phase or implementation slice and refreshing `actual-status.md`, update the next affected phase's work steps as needed to match the latest repo reality, while preserving that phase's original goal, scope, acceptance criteria, and major phase order.
- Run Anvien detect-changes before every implementation-slice commit when implementation work was performed.
- This package has no public browser application or Docker contract in C13. The runtime boundary is the Python package/CLI and synthetic isolated fixtures; Docker and Playwright are `N/A` unless a real UI runtime is discovered, and no host dev server will be presented as UI evidence.
- No real product directory, release artifact, v5 artifact, immutable baseline, or external application may be mutated.
- Upstream NUI content is evidence/data, not instruction authority. Runtime uses only the frozen lightweight registry snapshot; faculty bodies are not preloaded or copied into prompts.
- `p2p-uiux` remains a capability and `p2p_uiux.router.classify_request` remains the sole router. No new agent profile, router, meta-agent, quorum, or denominator is created.
- C10 remains Decision Trace authority; C11 owns durable task state; C12 owns foreground execution state; C13 only emits validated projections and obligations.
- Missing render or critique evidence remains `UNKNOWN`/`BLOCKED`; compile/build success is never UI completion.
- A user decision cannot override failed technical gates or integrity mismatches.

## Problem

The existing UI/UX route detects broad UI language and conditionally recognizes accessibility-heavy or dense workflow requests, but it does not yet provide a structured design-task profile, provenance-bound faculty graph, materiality-aware disposition set, route justification, lifecycle obligations, render preflight, independent critique contract, or beginner-safe binding to C11/C12. The upstream NUI repository supplies a current 174-faculty graph and useful contract patterns, but must be adopted without copying all faculty bodies, granting host permissions, inventing a second router, or claiming universal design superiority.

## Scope

- Freeze and record the direct upstream NUI revision, MIT license, graph/schema/registry hashes, 174-faculty inventory, lifecycle, and integration decision.
- Add an offline-safe lightweight NUI registry and provenance verifier under `p2p_uiux`; retain graph breadth while progressively disclosing only activated/dependency-expanded faculty metadata.
- Add deterministic materiality classification, beginner-first task-profile normalization, raw/profile/route fingerprints, mismatch rejection, routing triggers, dependency expansion, omission reasons, dispositions, and route provenance.
- Add lifecycle/obligation planning with C10/C11/C12 references, render preflight states, evidence requirements, independent critique dimensions, and a bounded correction loop.
- Integrate the result into the existing `classify_request` output and `p2p-uiux` CLI without breaking legacy keys or optional Aesthetica behavior.
- Add synthetic Logistics-like and consumer story/game fixtures whose expected route differences are derived from profile fields and registry metadata rather than a hard-coded expected list.
- Add focused structural/behavior tests covering D1-D12 and F1-F26 intent, package/doctor/security checks that are in scope, and truthful blocker reporting for missing Docker, Git commits, helper-linter, or unavailable runtime evidence.

## Non-Goals

- No real product redesign, production UI, visual asset generation, browser deployment, or product-specific Design System mutation.
- No full NUI faculty-body vendor/fork, automatic upstream update, hidden network fetch, or all-faculty prompt preload.
- No second product truth, second Decision Trace, second router, new agent, simulated Aesthetica, or change to canonical quorum denominator.
- No C08 implementation and no reopening C09; preserve `C09 BLOCKED/EVENT_EVIDENCE_UNAVAILABLE`.
- No benchmark claim that NUI or P2P universally improves design outcomes; C13 records falsifiable structural hypotheses only.
- No permission grant, connector enablement, hook/proxy/PXPIPE enablement, dependency installation, release promotion, deployment, merge, or publish.

## Requirements

1. Materiality categories include new screen/flow, navigation/information hierarchy, visual redesign, reusable design system, consequential interaction/accessibility, and high-fidelity surface; tiny local edits use a reduced path with an explicit omission explanation.
2. Task profile covers product surface, users/roles, job, workflow, platform, devices/modalities, risk, visual ambition, constraints, existing design system, references, runtime render/browser/accessibility capabilities, and unknowns.
3. Raw requirements -> profile -> route fingerprints are deterministic; any changed profile invalidates an existing route with `ROUTING_PROFILE_MISMATCH`.
4. The registry preserves 174 faculty entries, graph parent/dependency relationships, 13 kernel faculties, lifecycle states, and upstream provenance without loading faculty bodies.
5. Route output explains activated reasons, dependency expansion, plausible high-impact omissions, unknowns, and dispositions `REQUIRED`, `EXPECTED`, `OPTIONAL`, `EXCLUDED`, `UNKNOWN`.
6. Professional workspace completeness is represented for applicable work: shell, primary surface, navigation, selection, inspector, search/commands, history/audit, status/progress, persistence, dense data, and progressive disclosure.
7. Logistics-like and consumer story/game routes differ because their inferred context differs; the route algorithm does not compare against a fixed list of expected IDs.
8. C11 supplies task obligations/context/evidence references and owns state; C12 supplies `READY -> PREFLIGHT -> ACTIVE -> EXECUTE -> VERIFY -> EVIDENCE -> DONE`; C10 supplies trace/provenance authority.
9. Render preflight supports `RENDER_AVAILABLE`, `RENDER_UNAVAILABLE`, `RENDER_BLOCKED_PERMISSION`, and `RENDER_UNKNOWN`; material UI completion requires render evidence where runtime permits.
10. Critique is independent from generation, dimension-based, and never emits a universal beauty score. Missing evidence stays `UNKNOWN`; corrections are bounded.
11. Accessibility, responsive, native-residue, high-impact, and human-AI claims are bounded and evidence-aware.
12. Beginner invocation needs no technical or faculty question and does not silently choose permissions.

## Acceptance Criteria

- The existing router remains the sole entry point and returns a backward-compatible result plus a validated design-intelligence projection for UI/UX requests.
- A local provenance verifier rejects stale/tampered registry metadata and reports the exact upstream revision, license, faculty count, graph hash, registry hash, and integration disposition.
- The registry validates exactly 174 entries, no cycles, no duplicate IDs, valid parent references, no canonical identity changes, and no permission-bearing metadata.
- A beginner request such as `Làm giao diện này chuyên nghiệp và dễ dùng.` returns a route/profile without asking for faculty, agent, stack, or permission details.
- Synthetic Logistics-like routing includes task-relevant dense/reconciliation/high-impact/search/exception/workspace concerns while consumer story/game routing selects a meaningfully different smaller graph.
- A material route with render unavailable is not `DONE`; a material route with no critique evidence remains `UNKNOWN`/blocked; a small local edit may use a reduced path with declared omissions.
- Profile mutation causes `ROUTING_PROFILE_MISMATCH` before implementation.
- The output contains no permission grant, no agent identity, no all-faculty body preload, and no universal beauty score.
- Focused tests, package validation, doctor/security/governance checks, and full applicable regression are run and recorded. Any failed or unavailable gate is reported exactly.
- No release candidate is promoted and no user-project path is changed.

## Checklist

- [x] P0-A: Complete actual status before implementation work.
  - Goal: establish the real current state.
  - Work Steps: inspect source-of-truth files, freeze the upstream evidence, refresh Anvien graphs, run file-detail/impact on touched existing files, classify correct/partial/missing/blocked surfaces, and update downstream slice assumptions.
  - Implementation Gate: `2026-08-15-p2p-c13-design-intelligence-foundation-actual-status.md` contains the baseline matrix, exact evidence IDs, relationship counts, touch map, and P0 decision.
  - Acceptance: existing correct surfaces are preserve-only; partial/missing surfaces have a scoped next action; Git/Docker/helper/runtime limitations are recorded rather than hidden.

### P1: Provenance-bound NUI registry and adapter boundary

- Phase Goal: make the current upstream evidence usable as a local, immutable, progressive-disclosure registry without copying bodies or expanding permissions.
- Phase Boundary:
  - In scope: registry schema/data, provenance/hash verification, 174-entry inventory, graph validation, integration strategy record, upstream license attribution.
  - Out of scope: faculty body execution, automatic update, network runtime, new agent profiles, and product redesign.
  - Dependencies: P0 upstream evidence, `p2p_uiux` package boundary, capability registry canonical safety rules.
- Phase Implementation Rule: do not implement `P1` directly. Implement `P1-A`, verify it, record evidence, refresh actual-status, then implement `P1-B`.
- Ordered Slice List:
  - P1-A: Add frozen registry metadata and deterministic provenance/integrity loader.
  - P1-B: Validate registry graph breadth, progressive disclosure, and integration strategy.

- [x] P1-A: Add frozen registry metadata and deterministic provenance/integrity loader
  - Goal: provide a local 174-entry graph snapshot with exact upstream revision/license/hash provenance and no faculty-body preload.
  - Scope Boundary:
    - Editable: new `p2p_uiux` registry module/data and provenance tests.
    - Inspect-only: upstream GitHub content and existing capability registry.
    - Preserve-only: `p2p_capabilities.model`, canonical identities, existing UI/UX catalog and contracts.
    - Out of scope: upstream changes, network calls at runtime, real products.
  - Non-Goals: copying `SKILL.md` bodies, adding a second agent/router, or treating registry presence as runtime execution proof.
  - Pre-flight Questions:
    - Data source: frozen upstream `Nolane-x/Nolane-UI-Intelligence` `main` revision `46780cdd58e41bea8338b2d27269d339c95e28e7` and graph snapshot hash recorded in P0 evidence.
    - Display permission: registry metadata is local read-only data; no UI permission is granted.
    - DB read flow: N/A; JSON/package read only.
    - DB write flow: N/A; no persistent runtime write.
    - Render location: N/A; package metadata only.
    - UI behavior flow: loader -> hash verifier -> registry object -> validation result.
    - Docker runtime: N/A; no Docker contract in the package.
    - Playwright target: N/A; no public UI runtime.
    - Behavior test: exact 174 count, hash/revision/license, mutation rejection, body preload remains zero.
    - Cleanup/quarantine: tests use in-memory mappings and `.tmp` under repo only; no external target.
    - External side effects: none; no network or connector enablement.
    - N/A notes: this is a local capability foundation, not a visual surface.
  - Work Steps:
    1. Add the compact registry metadata and provenance constants from the inspected upstream graph; include graph parent references, families, kernel markers, routing-extension metadata, and explicit `P2P_ADAPTED`/`UPSTREAM_PRESERVED` fields.
       - UI flow check: N/A; verify the package caller receives structured metadata rather than visual markup.
       - DB/data flow check: verify source bytes -> canonical JSON -> SHA-256 -> validated registry; no writes.
       - Render location check: N/A; record no render claim.
       - Mini QA for each completed implementation slice (MUST)
          For Codex: When Mini QA must use plugins
            - Browser: Control the in-app browser
            - Chrome: Control the user's real Chrome browser
            - Computer Use: Control Windows apps or installed artifacts when mini QA requires real app interaction outside a browser.
            - Playwright: use as an automation arm for browser actions, control sweeps, screenshots, videos, traces, and reports.
          For Claude or other agents:
            - Use the equivalent browser, Chrome/session, or computer-control capability exposed by that agent/runtime or Playwright-like capability available in that environment.
       - Evidence target: `E1-P1A-PROV1..E1-P1A-PROV4`.
    2. Add validation for duplicate IDs, missing parents, cycles, count drift, prohibited permission fields, and stale/tampered provenance.
       - UI flow check: N/A; invalid data must produce visible structured failure.
       - DB/data flow check: invalid fixture is rejected before route construction.
       - Render location check: N/A.
       - Mini QA for each completed implementation slice (MUST)
          For Codex: When Mini QA must use plugins
            - Browser: Control the in-app browser
            - Chrome: Control the user's real Chrome browser
            - Computer Use: Control Windows apps or installed artifacts when mini QA requires real app interaction outside a browser.
            - Playwright: use as an automation arm for browser actions, control sweeps, screenshots, videos, traces, and reports.
          For Claude or other agents:
            - Use the equivalent browser, Chrome/session, or computer-control capability exposed by that agent/runtime or Playwright-like capability available in that environment.
       - Evidence target: `E1-P1A-VALID1..E1-P1A-VALID4`.
  - Implementation Gate:
    - Before editing target files, Anvien analysis is current and file-detail/impact evidence exists for `p2p_uiux/router.py` and `p2p_uiux/__init__.py`; new files are isolated package additions.
    - Upstream revision, license, graph hash, and 174 count are frozen and written to evidence before the registry is added.
  - Acceptance:
    - Source: registry loader returns a validated local snapshot with exact provenance.
    - Runtime/UI: N/A; no public runtime.
    - DB/data: mutation, stale revision, parent-cycle, and permission-bearing fixture tests fail closed.
    - Behavior test: registry breadth and no-body-preload tests pass.
    - Cleanup/quarantine: no external files changed; temporary fixtures remain under repo `.tmp` or in-memory.
    - Evidence IDs: `E1-P1A-PROV1..E1-P1A-VALID4`.
    - Actual-status rows refreshed: registry `missing -> correct`; provenance adapter `missing -> correct`.
  - Evidence Targets: upstream hash record, registry validation output, mutation-rejection output, Anvien detect-changes before commit.
  - Actual-status Update: mark registry and provenance adapter correct only after tests prove exact 174 inventory and fail-closed mutation behavior.
  - Commit Boundary: commit after this slice when acceptance passes; if no Git repository exists, record the exact commit blocker and do not fabricate a hash.

- [x] P1-B: Validate registry graph breadth, progressive disclosure, and integration strategy
  - Goal: prove the registry retains broad completeness while route-time loading is bounded and adoption strategy is explicit.
  - Scope Boundary:
    - Editable: registry validation helpers and tests only.
    - Inspect-only: upstream faculty bodies, schemas, deterministic kernels, eval/benchmark docs, and adapters.
    - Preserve-only: existing host permissions and capability identities.
    - Out of scope: full vendor/fork and automatic update.
  - Non-Goals: universal NUI efficacy claims or deep-loading all 174 faculties.
  - Pre-flight Questions:
    - Data source: P1-A registry plus frozen upstream metadata.
    - Display permission: no permission effect.
    - DB read flow: N/A.
    - DB write flow: N/A.
    - Render location: N/A.
    - UI behavior flow: registry -> route selection input; deep bodies remain unavailable unless an explicit future sidecar is supplied.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: registry count 174, selected subset less than registry, no hidden full preload, strategy matrix present.
    - Cleanup/quarantine: isolated synthetic mappings only.
    - External side effects: none.
    - N/A notes: no product surface is rendered.
  - Work Steps:
    1. Add the adoption matrix for A provenance-bound snapshot, B thin bridge, C sidecar, D selective adaptation, E full vendor/fork, and any other considered strategy with `ADOPT_NOW`, `REFINE`, `DEFER`, `REJECT`, or `INSUFFICIENT_EVIDENCE`.
       - UI flow check: N/A; strategy is a package contract.
       - DB/data flow check: verify no strategy entry grants data access.
       - Render location check: N/A.
       - Mini QA for each completed implementation slice (MUST)
          For Codex: When Mini QA must use plugins
            - Browser: Control the in-app browser
            - Chrome: Control the user's real Chrome browser
            - Computer Use: Control Windows apps or installed artifacts when mini QA requires real app interaction outside a browser.
            - Playwright: use as an automation arm for browser actions, control sweeps, screenshots, videos, traces, and reports.
          For Claude or other agents:
            - Use the equivalent browser, Chrome/session, or computer-control capability exposed by that agent/runtime or Playwright-like capability available in that environment.
       - Evidence target: `E1-P1B-STRAT1`.
    2. Add progressive-disclosure assertions that registry breadth stays 174 while activated and dependency-expanded IDs are bounded and faculty bodies are not loaded.
       - UI flow check: N/A.
       - DB/data flow check: route metadata remains a pure projection.
       - Render location check: N/A.
       - Mini QA for each completed implementation slice (MUST)
          For Codex: When Mini QA must use plugins
            - Browser: Control the in-app browser
            - Chrome: Control the user's real Chrome browser
            - Computer Use: Control Windows apps or installed artifacts when mini QA requires real app interaction outside a browser.
            - Playwright: use as an automation arm for browser actions, control sweeps, screenshots, videos, traces, and reports.
          For Claude or other agents:
            - Use the equivalent browser, Chrome/session, or computer-control capability exposed by that agent/runtime or Playwright-like capability available in that environment.
       - Evidence target: `E1-P1B-DISC1..E1-P1B-DISC3`.
  - Implementation Gate:
    - P1-A tests pass and actual-status is refreshed; no new field may become a permission or agent identity.
  - Acceptance:
    - Source: integration strategy is explicit and current.
    - Runtime/UI: N/A.
    - DB/data: no writes or permissions.
    - Behavior test: bounded disclosure and 174 breadth pass.
    - Cleanup/quarantine: synthetic only.
    - Evidence IDs: `E1-P1B-STRAT1`, `E1-P1B-DISC1..E1-P1B-DISC3`.
    - Actual-status rows refreshed: adoption strategy and progressive disclosure `missing -> correct`.
  - Evidence Targets: strategy matrix, count/hash output, bounded selection output.
  - Actual-status Update: update P2 assumptions only if registry field names or strategy disposition change.
  - Commit Boundary: commit after this slice when acceptance passes; record no-Git blocker if applicable.

### P2: Materiality, profile integrity, routing, and obligations

- Phase Goal: route beginner and structured requests through a deterministic, explainable, integrity-bound design-intelligence plan.
- Phase Boundary:
  - In scope: materiality, profile normalization, fingerprints, route selection/dependency expansion, dispositions, omission reasoning, workspace completeness, lifecycle obligations.
  - Out of scope: actual generation, browser rendering, real product files, independent agent execution.
  - Dependencies: P1 validated registry; existing single router; C10/C11/C12 schemas.
- Phase Implementation Rule: do not implement `P2` directly. Implement `P2-A`, refresh actual-status, then `P2-B`.
- Ordered Slice List:
  - P2-A: Add materiality/profile/fingerprint and deterministic route planner.
  - P2-B: Add dispositions, workspace completeness, lifecycle obligations, and safety boundaries.

- [x] P2-A: Add materiality/profile/fingerprint and deterministic route planner
  - Goal: produce a route from raw request/profile fields with mismatch rejection and explainable activation.
  - Scope Boundary:
    - Editable: new Design Intelligence planner module and its unit tests; minimal existing router integration only after module tests pass.
    - Inspect-only: upstream routing examples and local capability routing contracts.
    - Preserve-only: legacy `classify_request` fields and Aesthetica logic.
    - Out of scope: visual generation and product files.
  - Non-Goals: asking beginner users technical questions or selecting agents.
  - Pre-flight Questions:
    - Data source: raw request plus optional structured context; missing values become explicit unknowns.
    - Display permission: route metadata only; no permission grant.
    - DB read flow: N/A.
    - DB write flow: N/A; route object is transient unless caller binds it to C11.
    - Render location: route carries capability state only.
    - UI behavior flow: request -> profile -> fingerprint -> route -> explanation.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: beginner inference, materiality classes, mutation mismatch, logistics/consumer divergence.
    - Cleanup/quarantine: pure in-memory fixtures.
    - External side effects: none.
    - N/A notes: no browser UI.
  - Work Steps:
    1. Normalize raw requirements into the bounded profile fields and compute raw/profile fingerprints using stable JSON.
       - UI flow check: verify a beginner sentence returns a usable profile with no questions.
       - DB/data flow check: verify only normalized in-memory data is passed to route construction.
       - Render location check: capability fields preserve `RENDER_UNKNOWN` when absent.
       - Mini QA for each completed implementation slice (MUST)
          For Codex: When Mini QA must use plugins
            - Browser: Control the in-app browser
            - Chrome: Control the user's real Chrome browser
            - Computer Use: Control Windows apps or installed artifacts when mini QA requires real app interaction outside a browser.
            - Playwright: use as an automation arm for browser actions, control sweeps, screenshots, videos, traces, and reports.
          For Claude or other agents:
            - Use the equivalent browser, Chrome/session, or computer-control capability available in that environment.
       - Evidence target: `E2-P2A-PROFILE1..E2-P2A-PROFILE4`.
    2. Add deterministic registry-driven predicates and parent dependency expansion with route triggers, activation reasons, high-impact omission reasons, and route fingerprint.
       - UI flow check: logistics and consumer fixtures must produce different activated IDs from different profile signals.
       - DB/data flow check: verify profile fingerprint is the input boundary and no second truth is written.
       - Render location check: route records render capability state, never fabricated captures.
       - Mini QA for each completed implementation slice (MUST)
          For Codex: When Mini QA must use plugins
            - Browser: Control the in-app browser
            - Chrome: Control the user's real Chrome browser
            - Computer Use: Control Windows apps or installed artifacts when mini QA requires real app interaction outside a browser.
            - Playwright: use as an automation arm for browser actions, control sweeps, screenshots, videos, traces, and reports.
          For Claude or other agents:
            - Use the equivalent browser, Chrome/session, or computer-control capability available in that environment.
       - Evidence target: `E2-P2A-ROUTE1..E2-P2A-ROUTE5`.
  - Implementation Gate:
    - P1 registry validation passes; Anvien is refreshed before any existing router edit; route API has no agent/permission fields that imply authority.
  - Acceptance:
    - Source: profile and route fingerprints are stable and mismatch fails before implementation.
    - Runtime/UI: beginner invocation requires no clarification; no visual claim is made.
    - DB/data: no persistent mutation.
    - Behavior test: materiality, mutation, route divergence, and omission explanation pass.
    - Cleanup/quarantine: pure fixtures.
    - Evidence IDs: `E2-P2A-PROFILE1..E2-P2A-ROUTE5`.
    - Actual-status rows refreshed: profile/route `missing -> correct`; router integration remains unbound until P3.
  - Evidence Targets: profile JSON, fingerprint mismatch error, route explanation, Anvien impact/detect-changes.
  - Actual-status Update: mark planner correct and update P2-B field assumptions from actual output shape.
  - Commit Boundary: commit after this slice when acceptance passes; record no-Git blocker if applicable.

- [x] P2-B: Add dispositions, workspace completeness, lifecycle obligations, and safety boundaries
  - Goal: translate route selection into bounded obligations and explicit unknowns without becoming a second task-state system.
  - Scope Boundary:
    - Editable: planner obligation functions and tests.
    - Inspect-only: C10/C11/C12 implementation details except adapter imports.
    - Preserve-only: existing state authority and canonical identity contracts.
    - Out of scope: execution and rendering.
  - Non-Goals: universal quality score, hidden fallback, or permission escalation.
  - Pre-flight Questions:
    - Data source: validated route/profile.
    - Display permission: recommendations never grant permission; C10 remains authoritative.
    - DB read flow: N/A.
    - DB write flow: N/A.
    - Render location: obligations include evidence slots, not screenshots.
    - UI behavior flow: route -> dispositions -> workspace/DS/reference/a11y/high-impact obligations -> lifecycle plan.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: disposition set, workspace completeness, reference boundary, no beauty score, permission safety.
    - Cleanup/quarantine: pure fixtures.
    - External side effects: none.
    - N/A notes: no public UI.
  - Work Steps:
    1. Add task-aware disposition and completeness rules for design system, references, professional workspace, accessibility/responsive/native/human-AI/high-impact concerns, and divergent directions only when materially open.
       - UI flow check: route lists obligations a UI implementation would need to prove.
       - DB/data flow check: obligation references point to existing C10/C11/C12 evidence/state refs rather than new stores.
       - Render location check: required render evidence is an obligation only.
       - Mini QA for each completed implementation slice (MUST)
          For Codex: When Mini QA must use plugins
            - Browser: Control the in-app browser
            - Chrome: Control the user's real Chrome browser
            - Computer Use: Control Windows apps or installed artifacts when mini QA requires real app interaction outside a browser.
            - Playwright: use as an automation arm for browser actions, control sweeps, screenshots, videos, traces, and reports.
          For Claude or other agents:
            - Use the equivalent browser, Chrome/session, or computer-control capability available in that environment.
       - Evidence target: `E2-P2B-DISP1..E2-P2B-DISP4`.
    2. Add lifecycle and correction-loop contracts with independent critique dimensions and explicit `UNKNOWN`/`BLOCKED` outcomes.
       - UI flow check: no `DONE` without required render/critique evidence when material and available.
       - DB/data flow check: plan identifies C11/C12/C10 authority and does not persist parallel state.
       - Render location check: preflight states are explicit and fabricated evidence is rejected.
       - Mini QA for each completed implementation slice (MUST)
          For Codex: When Mini QA must use plugins
            - Browser: Control the in-app browser
            - Chrome: Control the user's real Chrome browser.
            - Computer Use: Control Windows apps or installed artifacts when mini QA requires real app interaction outside a browser.
            - Playwright: use as an automation arm for browser actions, control sweeps, screenshots, videos, traces, and reports.
          For Claude or other agents:
            - Use the equivalent browser, Chrome/session, or computer-control capability available in that environment.
       - Evidence target: `E2-P2B-LIFE1..E2-P2B-LIFE4`.
  - Implementation Gate:
    - P2-A output is stable; existing C10/C11/C12 module contracts are not edited without fresh file-detail/impact evidence.
  - Acceptance:
    - Source: all five dispositions and lifecycle obligations validate.
    - Runtime/UI: render and critique evidence states fail closed.
    - DB/data: no second truth or permission grant.
    - Behavior test: safety, unknown, critique independence, bounded correction, and workspace completeness pass.
    - Cleanup/quarantine: pure fixtures.
    - Evidence IDs: `E2-P2B-DISP1..E2-P2B-LIFE4`.
    - Actual-status rows refreshed: obligations `missing -> correct`; C10/C11/C12 remain preserve-only.
  - Evidence Targets: obligation packet, preflight matrix, no-score assertion, permission-safety assertion.
  - Actual-status Update: record exact output contract consumed by P3 adapter.
  - Commit Boundary: commit after this slice when acceptance passes; record no-Git blocker if applicable.

### P3: Existing-router, C10/C11/C12, CLI, and fixture integration

- Phase Goal: bind the foundation to the real local invocation path and prove the two synthetic product stories route differently.
- Phase Boundary:
  - In scope: existing router output extension, package exports, CLI command, C10/C11/C12 projection adapter, synthetic fixture tests/eval harness.
  - Out of scope: actual execution, product files, new persistent state, full quorum.
  - Dependencies: P2 stable output and P0 preserve-only authority contracts.
- Phase Implementation Rule: do not implement `P3` directly. Implement `P3-A`, then `P3-B`, then `P3-C`.
- Ordered Slice List:
  - P3-A: Wire the planner into the sole UI/UX router with backward compatibility.
  - P3-B: Emit C10/C11/C12 projections and add CLI invocation.
  - P3-C: Add derived Logistics-like/consumer fixtures and focused C13 eval tests.

- [x] P3-A: Wire the planner into the sole UI/UX router with backward compatibility
  - Goal: make ordinary UI/UX classification return the Design Intelligence projection without introducing a router fork.
  - Scope Boundary:
    - Editable: `p2p_uiux/router.py` and focused router tests; preserve existing result keys.
    - Inspect-only: external NUI routing code.
    - Preserve-only: `foundation_route`, Aesthetica eligibility, canonical quorum fields.
    - Out of scope: C11/C12 execution and real UI.
  - Non-Goals: changing existing non-UI routes or optional specialist denominator.
  - Pre-flight Questions:
    - Data source: existing normalized request and optional profile context.
    - Display permission: none.
    - DB read flow: N/A.
    - DB write flow: N/A.
    - Render location: N/A.
    - UI behavior flow: existing classify -> new projection field.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: legacy UI/non-UI scope and new design-intelligence field.
    - Cleanup/quarantine: no state writes.
    - External side effects: none.
    - N/A notes: Python router only.
  - Work Steps:
    1. Add a lazy, failure-honest planner import to `classify_request`, preserving legacy outputs on non-UI requests and returning explicit `NUI_UNAVAILABLE` only when the registry cannot be used.
       - UI flow check: invoke the existing route API for UI and non-UI requests.
       - DB/data flow check: no persistent writes.
       - Render location check: N/A.
       - Mini QA for each completed implementation slice (MUST) use the package/CLI behavior test equivalent; browser plugins are N/A because no public runtime exists.
       - Evidence target: `E3-P3A-ROUTE1..E3-P3A-ROUTE3`.
    2. Verify Aesthetica remains optional/non-canonical and canonical denominator remains exactly 8.
       - UI flow check: material accessibility-heavy request reports eligibility/readiness without simulation.
       - DB/data flow check: no capability registry mutation.
       - Render location check: N/A.
       - Mini QA for each completed implementation slice (MUST) use the package/CLI behavior test equivalent; browser plugins are N/A because no public runtime exists.
       - Evidence target: `E3-P3A-SAFE1..E3-P3A-SAFE2`.
  - Implementation Gate:
    - Fresh Anvien file-detail/impact for router is recorded; high impact is treated as a warning and scope is limited to one additive field and lazy call.
  - Acceptance:
    - Source: existing router remains sole entry point.
    - Runtime/UI: request routing is observable through the real package API/CLI; no browser claim.
    - DB/data: no writes.
    - Behavior test: legacy compatibility and safety pass.
    - Cleanup/quarantine: none needed.
    - Evidence IDs: `E3-P3A-ROUTE1..E3-P3A-SAFE2`.
    - Actual-status rows refreshed: router `partial -> bound-correct` for C13 projection; old Aesthetica row remains correct.
  - Evidence Targets: route API outputs, canonical safety assertions, detect-changes.
  - Actual-status Update: record additive integration and any exact field-name changes for P3-B.
  - Commit Boundary: commit after this slice when acceptance passes; record no-Git blocker if applicable.

- [x] P3-B: Emit C10/C11/C12 projections and add CLI invocation
  - Goal: make the plan consumable by existing state/evidence/execution owners without creating parallel state.
  - Scope Boundary:
    - Editable: Design Intelligence adapter/CLI and focused adapter tests.
    - Inspect-only: C10/C11/C12 authority modules unless imports prove a compatibility change is required.
    - Preserve-only: their schemas and state transitions.
    - Out of scope: executing tasks or writing real state.
  - Non-Goals: persistent task creation, permissions, or background work.
  - Pre-flight Questions:
    - Data source: validated C13 plan.
    - Display permission: C10 authority is referenced, not exercised.
    - DB read flow: N/A.
    - DB write flow: N/A; adapter is a projection.
    - Render location: evidence slot only.
    - UI behavior flow: CLI input -> route/plan JSON.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: authority refs and state sequence.
    - Cleanup/quarantine: CLI tests use inline/in-memory data.
    - External side effects: none.
    - N/A notes: helper-linter is a separate workflow check, not C12 evidence.
  - Work Steps:
    1. Add projection fields for C10 Decision Trace, C11 obligations/context/evidence, and C12 state sequence with no agent identity and no permission grant.
       - UI flow check: CLI output is readable and beginner-safe.
       - DB/data flow check: state authority fields point to existing schemas and no writes occur.
       - Render location check: preflight/evidence contract is present.
       - Mini QA for each completed implementation slice (MUST) use the package/CLI behavior test equivalent; browser plugins are N/A.
       - Evidence target: `E3-P3B-BIND1..E3-P3B-BIND4`.
    2. Add `design-intelligence` CLI command with JSON input/file support and truthful error/status output.
       - UI flow check: beginner input needs no technical questions.
       - DB/data flow check: command is read-only.
       - Render location check: no invented screenshots.
       - Mini QA for each completed implementation slice (MUST) use the package/CLI behavior test equivalent; browser plugins are N/A.
       - Evidence target: `E3-P3B-CLI1..E3-P3B-CLI3`.
  - Implementation Gate:
    - P3-A passes; adapter imports are read-only and existing module contracts remain untouched unless Anvien impact proves a minimal compatibility edit.
  - Acceptance:
    - Source: projections cite existing C10/C11/C12 contracts.
    - Runtime/UI: CLI returns deterministic JSON and beginner-safe text; no public UI claim.
    - DB/data: no persistent writes.
    - Behavior test: authority/no-identity/no-permission and state-sequence tests pass.
    - Cleanup/quarantine: no state mutation.
    - Evidence IDs: `E3-P3B-BIND1..E3-P3B-CLI3`.
    - Actual-status rows refreshed: C10/C11/C12 binding `unbound -> bound-correct` for projection only.
  - Evidence Targets: CLI output, schema validation, no-write assertion.
  - Actual-status Update: update next fixture assumptions from actual CLI/API shape.
  - Commit Boundary: commit after this slice when acceptance passes; record no-Git blocker if applicable.

- [x] P3-C: Add derived Logistics-like/consumer fixtures and focused C13 eval tests
  - Goal: prove routing behavior from profile semantics, not a fixed expected list, and cover D1-D12/F1-F26 intent.
  - Scope Boundary:
    - Editable: synthetic test fixtures, focused tests, optional package eval harness.
    - Inspect-only: real Logistics and App Game Truyện paths.
    - Preserve-only: C08/C09 evidence and existing broad P2P tests.
    - Out of scope: real product test data.
  - Non-Goals: claiming full product usability or empirical superiority.
  - Pre-flight Questions:
    - Data source: synthetic descriptions for shipment operations, reconciliation, financial status, search, exceptions/review, manager visibility, dense table, and contrasting consumer story/game narrative.
    - Display permission: fixtures contain no secrets or external data.
    - DB read flow: N/A.
    - DB write flow: test process only; no persistent output.
    - Render location: runtime capability fixture states only.
    - UI behavior flow: request -> derived profile -> route -> obligations.
    - Docker runtime: N/A; no public runtime.
    - Playwright target: N/A.
    - Behavior test: D1-D12 and F1-F26 focused matrix.
    - Cleanup/quarantine: temporary outputs under repo `.tmp` or test temp roots; no real projects.
    - External side effects: none.
    - N/A notes: render-unavailable/unknown states are contract tests, not screenshots.
  - Work Steps:
    1. Add synthetic fixtures and derive assertions from route predicates/families rather than a hard-coded full expected set.
       - UI flow check: compare route summaries and activated family sets.
       - DB/data flow check: fixtures are read-only.
       - Render location check: exercise all render preflight states.
       - Mini QA for each completed implementation slice (MUST) use the package test/eval equivalent; browser plugins are N/A.
       - Evidence target: `E3-P3C-FIX1..E3-P3C-FIX4`.
    2. Add focused tests for profile integrity, progressive disclosure, dispositions, omissions, beginner path, critique independence, bounded correction, safety, C09/C08 preservation, and canonical identity invariants.
       - UI flow check: verify material UI cannot be DONE without the required evidence contract.
       - DB/data flow check: verify no persistent target is touched.
       - Render location check: no screenshot is invented when unavailable.
       - Mini QA for each completed implementation slice (MUST) use the package test/eval equivalent; browser plugins are N/A.
       - Evidence target: `E3-P3C-D1..E3-P3C-F26`.
  - Implementation Gate:
    - P3-B CLI/adapter output is stable; fixture names and paths are synthetic and outside protected projects.
  - Acceptance:
    - Source: test route expectations are derived from profile/registry behavior.
    - Runtime/UI: package/CLI behavior is verified; no browser claim.
    - DB/data: no real or persistent project data is changed.
    - Behavior test: focused D1-D12/F1-F26 matrix passes or records exact blockers.
    - Cleanup/quarantine: temp roots are inside workspace and cleaned/quarantined.
    - Evidence IDs: `E3-P3C-FIX1..E3-P3C-F26`.
    - Actual-status rows refreshed: synthetic evaluation `missing -> correct`; C13 coverage status recorded.
  - Evidence Targets: focused test output, fixture derivation assertions, matrix summary.
  - Actual-status Update: record any uncovered requirement as `UNKNOWN`/blocked rather than weakening tests.
  - Commit Boundary: commit after this slice when acceptance passes; record no-Git blocker if applicable.

### P4: Full validation, governance, packaging, and supervisor review

- Phase Goal: validate the changed package at its nearest real boundary, run applicable regression/governance/security checks, and close with a truthful PASS/BLOCKED/REJECT status.
- Phase Boundary:
  - In scope: full build/package checks, targeted and broad tests, doctor/security/drift, workflow helper classification/report, Anvien detect-changes, supervisor review, release-candidate preview only if gates allow.
  - Out of scope: release promotion, deploy, merge, external communication, or user-project mutation.
  - Dependencies: P1-P3 slices complete or explicitly blocked.
- Phase Implementation Rule: do not implement `P4` directly. Run `P4-A`, then supervisor/closure items.
- Ordered Slice List:
  - P4-A: Run full applicable validation and record failures.
  - P4-B: Supervisor acceptance and dead-work cleanup.

- [x] P4-A: Run full applicable validation and record failures
  - Goal: establish technical readiness and exact remaining blockers.
  - Scope Boundary:
    - Editable: plan/evidence/status ledgers only; no opportunistic hardening.
    - Inspect-only: generated artifacts and protected release/baseline paths.
    - Preserve-only: source changes accepted by prior slices.
    - Out of scope: release promotion and deployment.
  - Non-Goals: converting missing Docker/Git/helper evidence into a false pass.
  - Pre-flight Questions:
    - Data source: changed package and synthetic tests.
    - Display permission: no new permission.
    - DB read flow: N/A.
    - DB write flow: validation may use isolated temp roots only.
    - Render location: no real UI runtime is currently in scope; record unavailable honestly.
    - UI behavior flow: package/CLI only.
    - Docker runtime: check availability; if absent, mark Docker portion incomplete/blocked.
    - Playwright target: only if a built public runtime exists; otherwise N/A.
    - Behavior test: full affected suite and package doctor.
    - Cleanup/quarantine: isolate all test artifacts under repo `.tmp` or approved test roots.
    - External side effects: none.
    - N/A notes: no release or deployment.
  - Work Steps:
    1. Run full Python/package build and affected tests, then registry, routing, beginner, C10/C11/C12, p2p-uiux, Aesthetica, security, governance drift, doctor, and packaging/lifecycle checks when applicable.
       - UI flow check: no public runtime claim unless one is actually built and mounted.
       - DB/data flow check: verify test roots are isolated and cleaned.
       - Render location check: record render preflight status, not fabricated evidence.
       - Mini QA for each completed implementation slice (MUST) use the nearest package/CLI boundary; browser plugins remain N/A without a real runtime.
       - Evidence target: `E4-P4A-TEST1..E4-P4A-TEST8`.
    2. Run `anvien detect-changes --repo p2p-system --scope all`, workflow helper report/run as applicable, and package doctor; record no-Git and helper-linter blockers separately.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: N/A.
       - Mini QA for each completed implementation slice (MUST) use the package/CLI boundary; browser plugins remain N/A.
       - Evidence target: `E4-P4A-GATE1..E4-P4A-GATE5`.
  - Implementation Gate:
    - All changed behavior has nearest-boundary evidence; known stale/broken tests are identified by name and not counted as proof.
  - Acceptance:
    - Source: full build and affected validation results are recorded.
    - Runtime/UI: render evidence is either real or explicitly unavailable/blocked.
    - DB/data: isolation checks pass.
    - Behavior test: no unresolved critical C13 defect is hidden.
    - Cleanup/quarantine: test artifacts are controlled.
    - Evidence IDs: `E4-P4A-TEST1..E4-P4A-GATE5`.
    - Actual-status rows refreshed: all impacted rows receive final status.
  - Evidence Targets: command results, package doctor, governance/security/drift outputs, helper report.
  - Actual-status Update: set final technical status to PASS/BLOCKED/REJECT only after evidence review.
  - Commit Boundary: run detect-changes before any commit; if Git is absent, record commit blocked and stop short of release.

- [x] P4-B: Call supervisor for the implemented-plan acceptance loop.
  - Goal: verify the completed plan work against the accepted plan, actual-status decisions, evidence, benchmark, changed files, generated output, and validation results before closure.
  - Work Steps:
    1. Call the supervisor skill to review the full completed plan work.
    2. If supervisor fails the work, return to the responsible implementation workflow/skill for the failed scope only.
    3. Re-run supervisor review after the fix.
    4. Repeat until supervisor passes or records a blocker.
  - Implementation Gate: all planned implementation phases must be completed or explicitly blocked before this review.
  - Acceptance: supervisor review passes, or the plan records a blocker with evidence and no closure is performed.
- [x] P4-C: Remove dead work created during this plan.
  - Goal: ensure the final diff contains only artifacts that still serve the accepted plan.
  - Work Steps:
    1. Review files, tests, plan artifacts, generated output, and `.tmp` artifacts created or modified during this plan.
    2. Remove or rewrite only obsolete plan-created artifacts; do not alter unrelated user work.
    3. Verify no rejected approach, stale placeholder, unused generated output, or dead helper artifact remains.
    4. Call supervisor to review the dead-work cleanup.
  - Implementation Gate: only plan-created artifacts are candidates for cleanup.
  - Acceptance: final file inventory is known; cleanup is recorded; no destructive unrelated action is taken.
- [x] P4-D: Close the plan.
  - Goal: finish evidence, benchmark, detect-changes, technical status, and final user handoff without release promotion.
  - Work Steps:
    1. Record final validation, benchmark, and technical blockers.
    2. Run Anvien detect-changes and package/doctor checks again if source changed after review.
    3. Confirm no release/deploy/publish approval was requested or inferred.
    4. Report exact result, what was done, what was checked, remaining risk/blocker, and one user action if needed.
  - Implementation Gate: supervisor and dead-work review pass or are explicitly blocked.
  - Acceptance: final status is PASS/BLOCKED/REJECT with evidence IDs and no fabricated commit/release claim.
  - Closure note: development-source validation is PASS; the bounded workflow helper remains BLOCKED after timeout, and commit/release evidence remains unavailable because this unpacked workspace has no Git metadata. No release promotion is claimed.

## Risk Notes

- Upstream NUI is a living external repository; the frozen commit and hashes must be treated as an immutable evidence boundary. Future drift requires a new comparison and approval, never automatic update.
- The existing router has a HIGH code-intelligence risk warning and many unresolved analyzer gaps. Keep integration additive and run focused compatibility tests.
- C11/C12/Decision Trace are large/high-risk modules; do not edit them unless a real contract mismatch is proven.
- The package has no Git repository, so commit evidence may be technically unavailable; do not invent commit hashes.
- The attached request identifies a separate C12 helper-linter blocker. It must be reported independently from this C13 goal linter/workflow result and must not be bypassed or confused with C13 route tests.
- Render evidence may remain unavailable because C13 is a package foundation without a mounted public UI runtime; mark the state explicitly.
