# AESTHETICA Evidence-Based Selective Routing Closure Plan

## Metadata

- Date: `2026-08-13`
- Status: `complete` — PASS; promotion intentionally not performed
- Plan: `docs/plans/2026-08-13-aesthetica-evidence-based-selective-routing-closure/2026-08-13-aesthetica-evidence-based-selective-routing-closure-plan.md`
- Evidence: `docs/plans/2026-08-13-aesthetica-evidence-based-selective-routing-closure/2026-08-13-aesthetica-evidence-based-selective-routing-closure-evidence.md`
- Benchmark: `docs/plans/2026-08-13-aesthetica-evidence-based-selective-routing-closure/2026-08-13-aesthetica-evidence-based-selective-routing-closure-benchmark.md`
- Actual status: `docs/plans/2026-08-13-aesthetica-evidence-based-selective-routing-closure/2026-08-13-aesthetica-evidence-based-selective-routing-closure-actual-status.md`

## Goal

Convert the completed bounded AESTHETICA behavioral certification into the smallest correction on the existing `p2p-uiux` routing surface. Keep `p2p-uiux` primary, make AESTHETICA selectively eligible only for material accessibility-heavy or dense workflow/form problems, preserve fallback and canonical 8/8 governance, build an immutable `.15` candidate, validate lifecycle paths, and stop before promotion.

## Rules

- Complete P0 actual status before implementation work.
- Update each checklist item immediately when it is completed.
- Record evidence as work completes.
- Record benchmarkable counts or measurements when they are taken.
- Do not modify the approved `.14` ZIP or App Game Truyện.
- Do not create a second router, specialist, manifest hierarchy, or scoring framework.
- Do not make product-category keywords (`game`, `story`, `mobile`, `responsive`, `dashboard`, `ecommerce`, `design system`) automatic AESTHETICA triggers.
- Do not hardcode the certification prompt sentences; use material signal classes and bilingual fixtures.
- Do not promote `.15` automatically; promotion remains a protected owner-approval action.
- Run Anvien detect-changes before every implementation-slice commit when implementation work was performed.
- For public runtime or UI-facing changes, validate the real user-visible runtime with browser or Playwright evidence.
- For app/runtime validation, full build must include Docker image/container build. This Python CLI/package change has no Docker runtime; the applicable package build and isolated installer lifecycle are the runtime boundary.
- Any Playwright validation must target the real built Docker/container runtime. No Playwright is required because this is a non-UI routing contract change.
- Keep the standard planner structure. These detail rules only make phase checklist items concrete enough to implement safely.

## Problem

The existing router treats broad UI/UX terms as sufficient specialist evidence. As a result, generic dashboards, story/game UI, mobile, responsive, ecommerce, design-system, visual-direction, and beginner UI requests can call the optional specialist even though certification found LOW, NEGATIVE, or NOT_APPLICABLE value. The correction must preserve UIUX routing and only narrow optional escalation.

## Scope

In scope:

- Existing `.p2p/system/p2p_uiux/router.py` materiality decision.
- Matching p2p-uiux/p2p capability-boundary wording and release metadata.
- Focused bilingual deterministic routing fixture with at least 30 cases.
- Existing beginner/first-material/40-case routing regression expectations.
- Existing UI/UX evaluator expectations and relevant package lifecycle assertions.
- Candidate `.15` package, fresh install, upgrade from `.14`, and same-version reinstall in isolated repo-local temporary roots.
- Evidence, benchmark, coder, and Supervisor reports.

## Non-Goals

- No redesign of AESTHETICA.
- No new router, agent, hook, identity architecture, quorum logic, or external dependency.
- No changes to the approved `.14` artifact, v5 artifact, immutable baseline, App Game Truyện, Logistics, or user projects.
- No promotion, installation into a real user project, or owner approval execution.
- No unrelated research, UI implementation, or optional hardening.

## Requirements

- `p2p-uiux` remains active for every UI/UX request, including requests where AESTHETICA is not eligible.
- Auto-eligible classes are only material `ACCESSIBILITY_HEAVY` and `DENSE_WORKFLOW_FORM` signals, subject to readiness and fallback.
- Responsive-only, story/game normal UI, mobile consumer, general dashboard, ecommerce, design-system-only, generic visual polish, cosmetic, and backend-only requests do not auto-call AESTHETICA.
- Mixed category plus material accessibility or dense workflow signals can still be eligible.
- Beginner-facing routing remains internal and does not expose specialist selection.
- Candidate version is exactly `8.4.7-C-codex.15`; `.14` remains immutable.
- Canonical set remains eight, denominator `8`, full quorum `8/8`, AESTHETICA optional/noncanonical.
- At least 30 deterministic bilingual routing cases pass.

## Acceptance Criteria

- SR1–SR16: existing router surface, selective policy, mixed cases, beginner experience, restraint, backend, and fallback are closed.
- SR17: 30+ selective routing tests pass.
- SR18: existing beginner UIUX and first-material routing suites pass.
- SR19–SR21: canonical count 8, denominator 8, AESTHETICA optional/noncanonical.
- SR22: security/secret checks pass.
- SR23: candidate fresh install, upgrade from `.14`, and reinstall pass.
- SR24: independent Supervisor report is PASS.
- No release promotion occurs in this Goal.

## Checklist

- [x] P0-A: Complete actual status before implementation work.
  - Goal: establish the real current state.
  - Work Steps: inspect source-of-truth files, classify each surface, record graph/impact limits, and update later phase assumptions.
  - Implementation Gate: actual status contains current source, tests, package, and protected-artifact classifications.
  - Acceptance: P0 actual-status decision is complete and permits the smallest edit.

### P1: Implement and test the selective materiality policy

- Phase Goal: correct the existing router and align its direct consumers without creating a second routing system.
- Phase Boundary:
  - In scope: router source, policy wording, evaluator/fixture expectations, focused routing tests.
  - Out of scope: release artifact, host hook, identity, quorum, App Game Truyện, unrelated product behavior.
  - Dependencies: certified evidence, P0 actual status, Anvien pre-edit checks.
- Phase Implementation Rule: implement P1-A, verify and record it, then implement P1-B, verify and record it.
- Ordered Slice List:
  - P1-A: replace broad specialist keyword eligibility with material accessibility/dense signal classes.
  - P1-B: add and align deterministic bilingual routing coverage and affected evaluator expectations.

- [x] P1-A: Replace broad specialist eligibility with evidence-backed materiality
  - Actual status: COMPLETE; direct route probes and contract wording checks PASS.
  - Goal: make optional AESTHETICA eligibility selective while preserving UIUX primary routing and readiness fallback.
  - Scope Boundary:
    - Editable: `.p2p/system/p2p_uiux/router.py`, matching runtime policy text, version metadata required for candidate.
    - Inspect-only: capability registry/foundation routing, host identity hook, canonical quorum code.
    - Preserve-only: `.14` ZIP, App Game Truyện, canonical agent profiles.
    - Out of scope: new router, new specialist, scoring framework, hook/identity changes.
  - Non-Goals: no automatic invocation guarantee; eligibility remains subject to profile availability and health.
  - Pre-flight Questions:
    - Data source: frozen certification report and current router source.
    - Display permission: N/A; CLI decision output only.
    - DB read flow: N/A; no database.
    - DB write flow: N/A; no persistent product data.
    - Render location: N/A; observable route JSON.
    - UI behavior flow: request -> existing router -> UIUX primary + optional eligibility/call decision.
    - Docker runtime: N/A for this Python package surface.
    - Playwright target: N/A; no user-visible UI changed.
    - Behavior test: selective fixture and existing routing tests.
    - Cleanup/quarantine: candidate/lifecycle roots under repo `.tmp` only.
    - External side effects: none; no network, hook, promotion, or real project install.
    - N/A notes: capability readiness and identity architecture are preserved.
  - Work Steps:
    1. Add bounded material signal groups and return explainable class/reason fields without category-wide triggers.
       - UI flow check: N/A; route JSON remains stable and `use_skill` stays true for UIUX.
       - DB/data flow check: N/A.
       - Render location check: N/A; inspect CLI output.
       - Evidence target: `E1-P1A-ROUTE1`.
    2. Update policy text and candidate version metadata while preserving canonical/quorum contracts.
       - UI flow check: N/A; wording must match runtime policy.
       - DB/data flow check: N/A.
       - Render location check: N/A.
       - Evidence target: `E1-P1A-CONTRACT1`.
  - Implementation Gate:
    - Anvien file-detail/impact attempted for the hidden runtime and completed for affected visible tests; high-risk warning is recorded.
    - P0 actual status is complete; `.14` SHA is recorded as preserve-only.
  - Acceptance:
    - Source: generic category requests no longer set `call_aesthetica` true solely from keywords.
    - Runtime/UI: `use_skill=true` remains for UIUX and profile-unavailable fallback remains fail-safe.
    - DB/data: N/A.
    - Behavior test: direct positive/negative/mixed probes pass.
    - Cleanup/quarantine: no candidate or user-project path is mutated.
    - Evidence IDs: `E1-P1A-ROUTE1`, `E1-P1A-CONTRACT1`.
    - Actual-status rows refreshed: router partial -> correct; policy docs partial -> correct.
  - Evidence Targets: source diff, route JSON, policy text, canonical manifest inspection.
  - Actual-status Update: append R1 with the source transition and affected consumers.
  - Commit Boundary: checkpoint after P1-A verification.

- [x] P1-B: Add 30+ deterministic selective-routing cases and align regressions
  - Actual status: COMPLETE; 36 bilingual cases and affected regression suites PASS.
  - Goal: prove positive, negative, mixed, bilingual, fallback, UIUX-preservation, and governance cases without exact certification sentence reuse.
  - Scope Boundary:
    - Editable: new selective fixture/test, existing routing/evaluator expectations that encode old broad behavior.
    - Inspect-only: existing package/lifecycle test helpers.
    - Preserve-only: release artifact and unrelated project fixtures.
    - Out of scope: new routing engine or product UI.
  - Non-Goals: no statistical claim beyond deterministic routing contract coverage.
  - Pre-flight Questions:
    - Data source: policy classes and representative bilingual intents.
    - Display permission: N/A.
    - DB read/write flow: N/A.
    - Render location: N/A.
    - UI behavior flow: fixture request -> router -> expected scope/use_skill/eligibility/call.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: `tests/test_p2p_aesthetica_selective_routing.py` plus existing suites.
    - Cleanup/quarantine: Python temp roots only where existing tests require them.
    - External side effects: none.
    - N/A notes: no exact certification prompt copied into the fixture.
  - Work Steps:
    1. Create at least 30 bilingual cases spanning all required classes and mixed conditions.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: N/A.
       - Evidence target: `E1-P1B-CASES1`.
    2. Update existing 40-case, first-decision, first-material, capability, evaluator, and package assertions to the new policy.
       - UI flow check: `p2p-uiux` stays active in every UI case.
       - DB/data flow check: N/A.
       - Render location check: N/A.
       - Evidence target: `E1-P1B-REGRESSION1`.
  - Implementation Gate:
    - P1-A route behavior passes before fixture expectations are updated.
  - Acceptance:
    - Source: no broad specialist trigger remains in the active router.
    - Runtime/UI: 30+ cases pass, including mixed accessibility/dense cases.
    - DB/data: N/A.
    - Behavior test: existing routing and evaluator suites pass.
    - Cleanup/quarantine: no out-of-scope mutation.
    - Evidence IDs: `E1-P1B-CASES1`, `E1-P1B-REGRESSION1`.
    - Actual-status rows refreshed: test contract partial -> correct.
  - Evidence Targets: test output, fixture hash, 40-case count, existing suite output.
  - Actual-status Update: append R2 with test contract transition.
  - Commit Boundary: checkpoint after P1-B verification.

### P2: Build and lifecycle-verify candidate `.15`

- Phase Goal: package only the approved source correction into `8.4.7-C-codex.15` and prove isolated lifecycle behavior.
- Phase Boundary:
  - In scope: source version metadata, package builder, clean candidate ZIP, fresh install, upgrade from `.14`, same-version reinstall.
  - Out of scope: promotion, real project installation, `.14` mutation, App Game Truyện.
  - Dependencies: P1 tests PASS and package source doctor/gates.

- [x] P2-A: Build and verify immutable `.15` candidate
  - Actual status: COMPLETE; package verification, doctor, drift, secret, governance, and exact hash binding PASS.
  - Goal: create a new ZIP without rebuilding or altering `.14`.
  - Work Steps: update candidate version metadata, run `scripts/package_release.py build` to a new sibling path, verify SHA/inventory/doctor/drift and compare `.14` SHA.
  - Implementation Gate: P1-B PASS and output path does not exist.
  - Acceptance: candidate reports `8.4.7-C-codex.15`, package checks pass, `.14` hash unchanged.

- [x] P2-B: Run isolated lifecycle matrix
  - Actual status: COMPLETE; fresh install, upgrade from `.14`, and same-version reinstall PASS.
  - Goal: verify fresh install, upgrade from `.14`, and same-version reinstall using repo-local temporary roots.
  - Work Steps: extract candidate and `.14`, run supported installer into fresh/upgrade/reinstall fixtures, validate version, policy behavior, protected-state preservation, canonical 8/8, fallback, doctor, drift, and secret scan.
  - Implementation Gate: candidate package verification PASS.
  - Acceptance: all three lifecycle paths PASS; no real user project is touched.

### Pn: Supervisor and closure

- [x] Pn-A: Call supervisor for the implemented-plan acceptance loop.
  - Actual status: COMPLETE; independent Supervisor report PASS.
  - Goal: independently verify evidence, source, routing behavior, lifecycle, canonical safety, security, and no over-generalization.
  - Work Steps: inspect the actual source/diff, run relevant checks, write the Supervisor report, and reject or pass the exact scope.
  - Implementation Gate: P1/P2 evidence complete.
  - Acceptance: Supervisor PASS report exists.
- [x] Pn-B: Remove dead work created during this plan.
  - Actual status: COMPLETE; retained repo-local extraction/lifecycle roots are evidence fixtures; no historical or user-project paths were removed.
  - Goal: retain only candidate/evidence artifacts required by the Goal.
  - Work Steps: inspect generated candidate/lifecycle roots and remove only plan-created dead artifacts after verification; do not remove historical artifacts.
  - Implementation Gate: candidate and reports are hashed and linked.
  - Acceptance: no dead plan-created artifact remains in the final scope.
- [x] Pn-C: Close the plan.
  - Actual status: COMPLETE; final checks, reports, hashes, gate state, and stop rule recorded. No promotion.
  - Goal: record final validation, benchmark, detect-changes, commit, and stop before promotion.
  - Work Steps: run final checks, update evidence/benchmark/actual-status, run detect-changes, write coder report, and stop.
  - Implementation Gate: Supervisor PASS or explicit blocker.
  - Acceptance: final result is PASS/BLOCKED/REJECT and no promotion is attempted.

## Risk Notes

- Runtime `.p2p` files are hidden from Anvien's indexed file projection; source review and direct tests are the authoritative runtime proof, with the indexing limitation recorded.
- Existing tests intentionally encode the previous broad policy and must be updated only where they assert the changed contract.
- Candidate packaging may refresh runtime lock/checksum metadata in development source; the approved `.14` artifact remains a preserve-only target.
- Exact host execution overhead is not part of this routing contract; readiness and fallback remain required.
