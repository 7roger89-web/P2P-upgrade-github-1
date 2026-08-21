# C36 CP0 EVIDENCE — Prompt Integrity Review + Git Truth + Baseline

Date: 2026-08-18 (GMT+7). Goal: C36 Evidence-Bound Context & Efficiency Intelligence.
Mode: LARGE IMPLEMENTATION GOAL, CONTINUOUS BOUNDED FOREGROUND EXECUTION, PROVIDER-NEUTRAL, BEGINNER-FIRST, EVIDENCE-FIRST. Owner approval: APPROVED FOR C36 IMPLEMENTATION.

## 1. PROMPT INTEGRITY REVIEW

The full C36 prompt (1777 lines) was read end-to-end before any mutation.
Reviewed against all 16 search categories:

| # | Category | Finding |
|---|----------|---------|
| 1 | Contradictory instructions inside prompt | None found. The prompt is internally consistent (e.g., "no model routing" aligns with C37 deferral; bounded retries align with loop guard). |
| 2 | Conflicts with repository truth | None material. Prompt expects starting branch p2p-c35r-zaofu-deep-audit @ 9dc0811 — Git truth CONFIRMS (see below). |
| 3 | Stale SHA/branch/version assumptions | None stale. 9dc0811 matches recovered HEAD. |
| 4 | Conflicting governance authority | None. Prompt explicitly defers to repository truth ("Do NOT assume these values if Git disagrees"). |
| 5 | Overwrite of canonical/source-of-truth data | Prompt forbids it (anti-overwrite gate); P2P governance (development-control.json rules, immutable evidence under docs/, candidate artifacts under .p2p/candidates/) must be respected. |
| 6 | Modifying derived projection instead of source | Not prompted. The prompt instructs following canonical regeneration rules (e.g., roadmap items, V18/gc22 syncs). |
| 7 | Silent permission widening | Not prompted; permission binding is explicit (context outside envelope → blocked). |
| 8 | Invalidating an existing candidate/artifact | Not prompted; C35 candidate must remain UNPROMOTED and untouched. |
| 9 | Destructive Git history changes | Forbidden by prompt (no force-push). |
| 10 | Infinite-loop retry instructions | Guarded by explicit ATTEMPT_FINGERPRINT/loop-guard semantics. |
| 11 | A→B→A→B oscillation | Guarded (oscillation guard; C35R normalization precedent: flaky validator tests handled once, not fought repeatedly). |
| 12 | Repeated work without changed inputs | Covered by loop-guard; regression comparison requires exact failure identity deltas. |
| 13 | Ambiguous ownership P2P/C19/C33/C34/C35/C35R/C36 | Boundaries are explicit: C19 retrieval reused-not-replaced; C34 usage evidence reused; C35 role runtime preserved; C35R research inputs accepted; no parallel context authority. |
| 14 | Requirements belonging to C37 | Explicitly excluded (routing, fallback, model selection, adaptive target selection — C37). |
| 15 | Fabrication encouragement | Prompt repeatedly FORBIDS fabrication (read evidence, delivery, cost, token, provider identity). No fabrication wording found. |
| 16 | Material alteration of runtime/governance/source-of-truth/candidate/roadmap | Allowed only through bounded implementation within C36 scope; candidate policy must run by machine; roadmap sync follows derivation rule. |

Result: **PROMPT_INTEGRITY_REVIEW = PROMPT_AUDIT_PASS**
One non-material note (non-blocking): the prompt says "no arbitrary file/task/time hard quota, but individual retry loops bounded" — consistent, no action.

## 2. GIT TRUTH RECOVERY

| Check | Expected | Recovered | Match |
|-------|----------|-----------|-------|
| Branch | p2p-c35r-zaofu-deep-audit | p2p-c35r-zaofu-deep-audit | YES |
| HEAD | 9dc0811 | 9dc0811 | YES |
| Remote HEAD | 9dc0811 | 9dc0811 | YES |
| Base lineage c35-provider-neutral-runtime | 7c9cb58 | 7c9cb58, ancestor of 9dc0811 | YES |
| Working tree | clean | 0 changes | YES |

Result: **GIT_TRUTH = CONFIRMED. No GIT_TRUTH_MISMATCH. May begin.**

## 3. BASELINE MEASUREMENT (9dc0811)

Full suite run 2x for stability; failure identity list saved to
`/home/ubuntu/analysis/c36_baseline_failures.txt` (30 failures, identical across runs, same set as the pre-existing base set confirmed at 7c9cb58 during C35R).

Baseline: **30 failed, 766 passed, 19 skipped** (pytest -q output).
The 30 failures are all PRE_EXISTING_BASELINE_FAILURE (validator subprocess
flakiness + env-dependent tests, unchanged since C35 base). C36 PASS criterion:
NEW_UNEXPLAINED_FAILURES = 0 against this exact identity list.
