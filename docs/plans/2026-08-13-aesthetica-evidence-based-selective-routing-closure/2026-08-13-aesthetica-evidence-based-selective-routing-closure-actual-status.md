# AESTHETICA Evidence-Based Selective Routing Closure Actual Status

Title: AESTHETICA Evidence-Based Selective Routing Closure
Date: 2026-08-13
Status: Complete — PASS; promotion intentionally not performed
Companion plan: `docs/plans/2026-08-13-aesthetica-evidence-based-selective-routing-closure/2026-08-13-aesthetica-evidence-based-selective-routing-closure-plan.md`
Companion evidence: `docs/plans/2026-08-13-aesthetica-evidence-based-selective-routing-closure/2026-08-13-aesthetica-evidence-based-selective-routing-closure-evidence.md`
Companion benchmark: `docs/plans/2026-08-13-aesthetica-evidence-based-selective-routing-closure/2026-08-13-aesthetica-evidence-based-selective-routing-closure-benchmark.md`

## Purpose

This file records the real current state before implementation.

## Freshness / Refresh Rules

P0 is the baseline. After each implementation slice, append a refresh row and update only affected classifications.

## Scope

Target scope:

- Existing `.p2p/system/p2p_uiux/router.py` selective AESTHETICA materiality decision.
- Matching policy/evaluator/fixture/test consumers and candidate `.15` lifecycle.

Out of scope:

- `.14` ZIP, App Game Truyện, host hook, identity architecture, canonical quorum, new router/specialist, promotion.

## Relationship / Impact Evidence

| Unit / File / Surface | File Detail Evidence | Related File Count | Relationship Summary | Impact Note |
|-----------------------|----------------------|--------------------|----------------------|-------------|
| `.p2p/system/p2p_uiux/router.py` | `E0-P0A-ANV2` | unavailable; hidden runtime file not indexed | direct CLI router source; inspected manually | high caution; Anvien target not found |
| `tests/test_p2p_beginner_routing.py` | `E0-P0A-ANV3` | 0 linked tests; 193 unresolved source-site rows | consumes three routing fixtures and `classify_request` | HIGH file-detail warning; direct test evidence required |
| `.p2p/system/scripts/p2p_eval.py` | `E0-P0A-SRC4` | not graph-indexed | evaluator gate consumes router and suite | inspect/edit only affected route expectations |
| `.agents/skills/p2p-uiux/SKILL.md` | `E0-P0A-SRC5` | not graph-indexed | release policy wording | preserve workflow; edit specialist boundary only |
| `.p2p/system/p2p.manifest.json` / `.p2p/system/VERSION` | `E0-P0A-SRC6` | not graph-indexed | candidate package identity | `.14` artifact preserve-only; source candidate editable |

## Current Status Matrix

| Unit | Current State | Required State | Status | Relationship Count | Evidence | Next Plan Decision |
|------|---------------|----------------|--------|--------------------|----------|--------------------|
| Existing router materiality logic | broad category/keyword specialist eligibility | evidence-backed accessibility/dense eligibility | correct | unavailable | `E0-P0A-SRC1`, `E0-P0A-ROUTE1`, `E1-P1A-ROUTE1` | preserve for candidate |
| p2p-uiux specialist wording | calls specialist for broad material UI/UX wording | selective conditional boundary | correct | unavailable | `E0-P0A-SRC5`, `E1-P1A-CONTRACT1` | preserve for candidate |
| Existing routing fixtures/tests | assert broad calls for dashboard/story/mobile/responsive/etc. | assert selective policy and UIUX preservation | correct | 0 linked / unresolved rows | `E0-P0A-ANV3`, `E1-P1B-CASES1`, `E1-P1B-REGRESSION1` | preserve for candidate |
| Capability registry/quorum | canonical eight, Aesthetica optional/noncanonical | unchanged | correct | preserve-only | `E0-P0A-CANON1` | preserve |
| `.14` artifact | approved and immutable | unchanged | correct | preserve-only | `E0-P0A-ART1` | do not touch |
| Candidate `.15` | `8.4.7-C-codex.15`, SHA `af4d63a882dabfde20ac237574590ec584ee2944bc4cdc30b6a07bf7f681e195` | new immutable candidate after P1 PASS | correct | package manifest and ZIP evidence | `E2-P2A-PACKAGE1`, `E2-P2A-VERIFY1`, `E2-P2A-IMMUTABLE1` | preserve; do not promote |
| Lifecycle evidence for `.15` | fresh, upgrade from `.14`, same-version reinstall all PASS | fresh/upgrade/reinstall PASS | correct | isolated repo-local roots | `E2-P2B-LIFE1`, `E2-P2B-LIFE2`, `E2-P2B-LIFE3` | preserve evidence |
| Technical release gate | PASS; approval request PENDING | technical PASS before owner approval | correct | exact subject/report/rollback hashes | `E2-P2-GATE1` | stop before approval/finalize |
| Supervisor acceptance | PASS | independent review PASS | correct | report written | `E2-PN-SUP1` | close Goal |

## Status Refresh Log

| Refresh | Date | Repo Basis | Changed Scope | Status Changes | Evidence | Next Phase Update |
|---------|------|------------|----------------|----------------|----------|-------------------|
| R0 | 2026-08-13 | certification evidence and current source inspection | router, policy, tests, package | initial wrong/partial/correct/missing classifications | `E0-P0A-SRC1..E0-P0A-PKG1` | proceed to P1-A after this P0 decision |
| R1 | 2026-08-13 | P1-A source edit and direct probes | router, policy contracts | router and wording transitioned to correct; `.14` still preserve-only | `E1-P1A-ROUTE1`, `E1-P1A-CONTRACT1`, `E1-P1-ANV1` | proceed to P1-B |
| R2 | 2026-08-13 | P1-B fixture and regression runs | selective fixture, existing routing, capability, decision trace | 36 focused cases and affected suites PASS | `E1-P1B-CASES1`, `E1-P1B-REGRESSION1` | proceed to P2-A |
| R3 | 2026-08-14 | `.15` package build, verify, gate, and lifecycle | candidate, rollback, technical report, install roots | candidate and all lifecycle/security/governance gates PASS; `.14` unchanged | `E2-P2A-PACKAGE1`, `E2-P2A-VERIFY1`, `E2-P2A-IMMUTABLE1`, `E2-P2B-LIFE1..3`, `E2-P2-GATE1` | proceed to Supervisor |
| R4 | 2026-08-14 | independent Supervisor and final stop | source, tests, hashes, canonical/quorum, approval state | Supervisor PASS; promotion not performed | `E2-PN-SUP1`, `E2-PN-ANV1`, `E2-PN-STOP1` | close Goal |

## Phase Touch Map

| Unit / File / Surface | Plan-Relevant Relationship File | Relationship to Target | Plan Item | Touch Mode | Evidence | Constraint |
|-----------------------|---------------------------------|------------------------|-----------|------------|----------|------------|
| `.p2p/system/p2p_uiux/router.py` | `.p2p/system/scripts/p2p_router.py` | runtime CLI consumer | P1-A | edit | `E0-P0A-SRC1` | no second router |
| `.agents/skills/p2p-uiux/SKILL.md` | `.agents/skills/p2p/SKILL.md` | policy contract | P1-A | edit | `E0-P0A-SRC5` | wording must match runtime |
| `tests/fixtures/*routing*.json` | `tests/test_p2p_beginner_routing.py` | test/fixture consumers | P1-B | edit | `E0-P0A-ANV3` | no exact certification sentences |
| `.p2p/system/p2p.manifest.json` / `VERSION` | `scripts/package_release.py` | package/generated output | P2-A | edit/regenerate | `E0-P0A-SRC6` | source candidate only |
| `.14` ZIP | none | protected release artifact | all | do-not-touch | `E0-P0A-ART1` | SHA must remain exact |

## Detailed Findings

### Existing router

Current state before P1: `classify_request` computed `needs_specialist` from broad `SPECIALIST_TERMS` and called AESTHETICA whenever a profile was available. P1 replaces that active decision with bounded material classes; the historical vocabulary is retained only as unused legacy data.

Required state: retain one router and `use_skill=true` for UIUX, but set specialist eligibility only for material `ACCESSIBILITY_HEAVY` or `DENSE_WORKFLOW_FORM` signal combinations.

Evidence:

- `E0-P0A-SRC1`: source lines 17–22 and 103–146 show broad terms and direct call logic.
- `E0-P0A-ROUTE1`: fresh probes show generic dashboard/story/responsive requests call AESTHETICA.

Relationship and impact:

- Related file count: unavailable in Anvien because hidden runtime is not indexed.
- Relationship summary: imported by CLI wrapper, tests, evaluator, and package runtime.
- Impact note: high caution; direct runtime tests are required.

Classification: correct after P1 and candidate packaging

Allowed next action: none within this Goal; candidate is ready for a separate owner approval decision, but no approval or promotion is executed here.

Forbidden next action: modify host hook, create another router, or touch `.14`.

## Next Phase Status Decisions

| Plan Item | Actual Status Finding | Required Status / Next-Action Update |
|-----------|-----------------------|--------------------------------------|
| P1-A | router is wrong; policy text partial | edit the existing surface only |
| P1-B | current fixtures assert old broad behavior | update affected expectations and add 30+ focused cases after P1-A |
| P2-A | `.15` absent; `.14` correct | build new candidate only after tests |
| P2-B | lifecycle not run for `.15` | use repo-local isolated roots |

## Implementation Gate

- [x] Target scope is listed in Current Status Matrix.
- [x] Each status has evidence IDs.
- [x] Relationship/index limitations are recorded.
- [x] Phase Touch Map defines edit/preserve/do-not-touch modes.
- [x] Correct parts are preserve-only.
- [x] Wrong/partial/missing parts have exact next actions.
- [x] Blocker is not present after source inspection.
- [x] Status Refresh Log has an R0 baseline row.

## Final P0 Decision

- [ ] P0 actual-status incomplete. Implementation is blocked.
- [ ] P0 complete. Next phase can proceed unchanged.
- [x] P0 complete. Next phase status, next action, or work steps must be updated before implementation.
- [ ] P0 complete. Target scope is preserve-only.
- [ ] P0 complete. Implementation is blocked by missing authority or evidence.

Decision note:

The certification evidence is explicit and the existing router is identifiable. The smallest safe correction is a narrow materiality predicate in the existing router, followed by focused regression updates. `.14` is preserve-only and no protected action is needed until the separate candidate technical gates are complete.
