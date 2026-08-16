# AESTHETICA Evidence-Based Selective Routing Closure Evidence Ledger

## Metadata

- Date: `2026-08-13`
- Plan: `docs/plans/2026-08-13-aesthetica-evidence-based-selective-routing-closure/2026-08-13-aesthetica-evidence-based-selective-routing-closure-plan.md`
- Evidence: `docs/plans/2026-08-13-aesthetica-evidence-based-selective-routing-closure/2026-08-13-aesthetica-evidence-based-selective-routing-closure-evidence.md`
- Benchmark: `docs/plans/2026-08-13-aesthetica-evidence-based-selective-routing-closure/2026-08-13-aesthetica-evidence-based-selective-routing-closure-benchmark.md`
- Actual status: `docs/plans/2026-08-13-aesthetica-evidence-based-selective-routing-closure/2026-08-13-aesthetica-evidence-based-selective-routing-closure-actual-status.md`

## Evidence Rules

- Certification evidence is bounded source authority, not a universal fact.
- `.14` is preserve-only and its exact SHA is checked before and after candidate work.
- Test evidence must prove request -> router -> observable scope/eligibility/call output.
- Lifecycle tests use temporary roots inside repo `.tmp` and cannot mutate user projects.
- Unknown telemetry is reported as UNKNOWN; no fabricated performance claim is used.

## E0 - P0 Evidence

Matching plan item(s): `P0-A`

- `E0-P0A-SRC1` — Manual source inspection of `.p2p/system/p2p_uiux/router.py` lines 17–22 and 103–146 found broad `SPECIALIST_TERMS` and `needs_specialist = use_skill and bool(specialist_hits) and not trivial_cosmetic`.
- `E0-P0A-ROUTE1` — Fresh direct route probes showed generic dashboard, story/game, mobile, and responsive requests returned `call_aesthetica=true` when availability was forced true.
- `E0-P0A-SRC4` — `.p2p/system/scripts/p2p_eval.py` consumes `classify_request` and has old broad positive gates at DW5 and DW18.
- `E0-P0A-SRC5` — `.agents/skills/p2p-uiux/SKILL.md` and its capability extension instruct broad specialist use for responsive, design-system, visual-direction, and accessibility work.
- `E0-P0A-SRC6` — Root and runtime versions are `.14`; runtime manifest preserves canonical agents and quorum `8/8`.
- `E0-P0A-CANON1` — Approved release `.14` manifest/registry confirms exactly eight canonical identities, denominator 8, full quorum 8/8, and Aesthetica optional/noncanonical.
- `E0-P0A-ART1` — Approved artifact exists at `D:\AI\P2P_dev\P2P-8.4.7-C-Codex-Edition-v14.zip` with expected SHA `36ee7a23ccd3e3a2d90512ebd911306bb86e7c6cfcf1c0362842ce36f458d744`.
- `E0-P0A-PKG1` — No `.15` candidate exists at the requested sibling output path before implementation.
- `E0-P0A-ANV1` — `anvien analyze --force --skip-git` completed: 259 files scanned, 26 parsed code files, 0 failed, current graph.
- `E0-P0A-ANV2` — Anvien `file-detail p2p/system/p2p_uiux/router.py` could not resolve the hidden `.p2p` runtime path; this limitation is recorded and direct source/runtime checks are required.
- `E0-P0A-ANV3` — Anvien `file-detail` and impact for `tests/test_p2p_beginner_routing.py` completed; file-detail reports 23 symbols, 193 unresolved source-site rows, high file warning; impact found no linked flows/tests and low direct impact for the test file.

## E1 - P1 Evidence

Matching plan item(s): `P1-A`, `P1-B`

- `E1-P1A-ROUTE1` — Direct route probes after the bounded predicate change: generic dashboard, normal story/game, mobile consumer, responsive-only, design-system-only, visual polish, and cosmetic requests returned `use_skill=true`, `specialist_eligible=false`, `call_aesthetica=false`; material accessibility and dense workflow/form requests returned the matching class and `call_aesthetica=true` when availability was forced true; backend-only returned `NON_UI` with both route flags false.
- `E1-P1A-CONTRACT1` — The existing `p2p-uiux` skill, core extension, and dispatcher extension now state that AESTHETICA is optional and automatically eligible only for material `ACCESSIBILITY_HEAVY` or `DENSE_WORKFLOW_FORM`; fallback, official receipt, canonical 8/8, and beginner-internal selection remain unchanged.
- `E1-P1B-CASES1` — `tests/fixtures/p2p-aesthetica-selective-routing.json` contains 36 unique bilingual cases, including positive classes, mixed story/accessibility, mixed dashboard/dense workflow, all required no-auto-call categories, backend negatives, and two unavailable-profile fallback cases.
- `E1-P1B-REGRESSION1` — Passing commands: `python -m unittest tests.test_p2p_aesthetica_selective_routing -v` (7 tests), `python -m unittest tests.test_p2p_beginner_routing -v` (8 tests), `python -m unittest tests.test_p2p_capability_foundation -v` (25 tests), and `python -m unittest tests.test_p2p_decision_trace -v` (4 tests). The affected package assertion now uses a material dense workflow request.
- `E1-P1-ANV1` — After the P1 edits, `anvien analyze --force --skip-git` completed with 264 files scanned, 27 parsed code files, 0 failed, and a current graph. `anvien detect-changes --scope all` was attempted and returned the repository limitation `Git diff failed: exit status 129` because this workspace has no Git metadata; no commit was claimed.

## E2 - P2 Evidence

Matching plan item(s): `P2-A`, `P2-B`

- `E2-P2A-PACKAGE1` — Existing `scripts/package_release.py build` created `D:\AI\P2P_dev\P2P-8.4.7-C-Codex-Edition-v15.zip` with version `8.4.7-C-codex.15`, 398 packaged files, 399 checksums, and artifact SHA-256 `af4d63a882dabfde20ac237574590ec584ee2944bc4cdc30b6a07bf7f681e195`.
- `E2-P2A-VERIFY1` — Candidate package verification and package doctor PASS; installed-candidate UI/UX doctor, drift check, secret scan, capability doctor, governance validation, and DW1–DW18 evaluator all PASS.
- `E2-P2A-IMMUTABLE1` — Recomputed candidate SHA remains `af4d63a882dabfde20ac237574590ec584ee2944bc4cdc30b6a07bf7f681e195`; approved `.14` rollback SHA remains `36ee7a23ccd3e3a2d90512ebd911306bb86e7c6cfcf1c0362842ce36f458d744`.
- `E2-P2B-LIFE1` — Fresh install of `.15` into an isolated repo-local fixture returned `FRESH_INSTALL`, version `.15`, and `RESULT: PASS`.
- `E2-P2B-LIFE2` — `.14` seed followed by `.15` returned `UPGRADE_FROM_8.4.7-C-codex.14`, version `.15`, `RESULT: PASS`, and preserved the owner sentinel.
- `E2-P2B-LIFE3` — Two `.15` installs into an isolated fixture returned `SAME_VERSION_REINSTALL` on the second run, version `.15`, and `RESULT: PASS`.
- `E2-P2-GATE1` — `p2p_gate.py prepare` technical report is `PASS`; subject and rollback hashes are bound exactly; approval request is `PENDING`, so no approval/finalize/promotion was performed.

## Closure Evidence

- `E2-PN-SUP1` — Independent Supervisor report is `PASS` at `reports/supervisor/rp_supervisor_260814_000903_by_gpt-5-codex_aesthetica-selective-routing-closure.md`.
- `E2-PN-CODER1` — Coder evidence report is present at `reports/coder/rp_coder_260814_000740_by_gpt-5-codex_aesthetica-selective-routing-closure.md`.
- `E2-PN-ANV1` — Final Anvien refresh completed with 264 scanned, 27 parsed, 0 failed; final `detect-changes` attempt returned `Git diff failed: exit status 129` because no Git metadata exists. No commit was claimed.
- `E2-PN-STOP1` — Promotion remains out of scope for this Goal; no `.14` mutation, App Game Truyện change, approval phrase, or next project work was started.
