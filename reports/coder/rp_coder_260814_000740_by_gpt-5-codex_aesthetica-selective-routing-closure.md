# Coder Report — AESTHETICA Evidence-Based Selective Routing Closure

## Outcome

Implementation and candidate packaging are complete for the requested scope.
The runtime correction is on the existing `p2p-uiux` router. No second router,
specialist, hook, identity architecture, quorum change, App Game Truyện change,
or `.14` artifact mutation was made. Promotion was intentionally not performed.

## Invariant Family Map

| Invariant family | Source of truth | Result |
|---|---|---|
| Primary UI/UX route | `.p2p/system/p2p_uiux/router.py` | `p2p-uiux` remains active for UI/UX requests |
| Optional specialist materiality | Existing `classify_request` predicate | Only material `ACCESSIBILITY_HEAVY` and `DENSE_WORKFLOW_FORM` are eligible |
| Default restraint | Same predicate and focused fixture | Dashboard, normal story/game, mobile, ecommerce, responsive-only, design-system-only, visual-polish, and cosmetic requests do not auto-call |
| Fallback | `force_profile_available=False` and invalid-profile paths | Eligible work continues with `p2p-uiux`; no simulation |
| Governance | `.p2p/system/p2p_capabilities/capabilities.json` and manifest | Canonical count 8, denominator 8, full quorum 8/8; AESTHETICA optional/noncanonical |
| Release integrity | Candidate ZIP, rollback ZIP, technical gate | `.15` is a new candidate; `.14` remains rollback and immutable |

## Changed Surfaces

- `.p2p/system/p2p_uiux/router.py`: bounded material signal classes, explainable eligibility fields, UIUX-preserving category recognition, and Vietnamese negated-interface handling.
- `.agents/skills/p2p-uiux/SKILL.md`, `.agents/skills/p2p-uiux/P2P-CORE-EXTENSION.md`, `.agents/skills/p2p/SKILL.md`: selective specialist boundary and fallback contract.
- `.p2p/system/scripts/p2p_eval.py` and `.p2p/system/docs/evals/p2p-uiux-eval-suite.json`: affected positive/negative evaluator cases.
- `tests/fixtures/p2p-aesthetica-selective-routing.json`: 36 bilingual deterministic cases.
- `tests/test_p2p_aesthetica_selective_routing.py`: seven focused tests covering the 36-case matrix, fallback, UIUX preservation, governance, and single-router safety.
- Existing routing/foundation/package tests and fixtures: only expectations that encoded the old broad specialist behavior were aligned.
- Candidate metadata and release notes: version `8.4.7-C-codex.15` and bounded certification provenance.

## Sibling Surface and Legacy-Fallback Review

The capability foundation and host identity contract were inspected but not
rearchitected. The historical broad vocabulary is marked legacy and is not
used by the active eligibility predicate. The only active decision function is
the existing `classify_request`; `foundation_route` remains its existing
capability-readiness companion, not a second router. If AESTHETICA is missing,
invalid, or unavailable, the route reports `PROFILE_UNAVAILABLE` for an
eligible material class and keeps `use_skill=true` with `call_aesthetica=false`.

## Verification Evidence

- Focused selective suite: `python -m unittest tests.test_p2p_aesthetica_selective_routing -v` — 7/7 PASS.
- Existing beginner/first-material route suite: `python -m unittest tests.test_p2p_beginner_routing -v` — 8/8 PASS.
- Capability foundation suite: 25/25 PASS.
- Decision trace suite: 4/4 PASS.
- Full regression: `python -m unittest discover -s tests -p 'test_*.py' -v` — 76/76 PASS.
- Candidate package build: `8.4.7-C-codex.15`, 398 packaged files, 399 checksums, build PASS.
- Candidate package verification and package doctor: PASS.
- Installed candidate UI/UX evaluation DW1–DW18: all PASS.
- Installed candidate doctor, drift, secret scan, capability doctor, and governance validation: PASS.
- Lifecycle: fresh `.15` PASS; upgrade from `.14` PASS with sentinel preservation; same-version reinstall PASS.
- Technical release gate: PASS; approval request is pending and was not approved.
- Anvien graph refresh: PASS (264 scanned, 27 parsed, 0 failed). Change detection was attempted and returned the recorded repository limitation `Git diff failed: exit status 129` because this workspace has no Git metadata; no commit was claimed.

## Hashes

- Candidate `.15`: `af4d63a882dabfde20ac237574590ec584ee2944bc4cdc30b6a07bf7f681e195`.
- Approved rollback `.14`: `36ee7a23ccd3e3a2d90512ebd911306bb86e7c6cfcf1c0362842ce36f458d744`, unchanged before/after candidate work.
- Technical gate report SHA-256: `b3310d5dc46da94f5db1b25191d562fd4b0a059f767fd0b2c2ae6926834359b2`.

## Residual Boundaries

- This Goal does not execute the owner approval phrase, finalize approval, or promote `.15`.
- The candidate package does not claim a new host AESTHETICA execution receipt; existing identity rules remain fail-closed and the host identity contract regression passes.
- No statistical or universal value claim is made; the policy is explicitly tied to the bounded ten-scenario behavioral certification and may be revisited with stronger evidence.
