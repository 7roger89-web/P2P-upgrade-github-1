<!-- RESEARCH_ONLY / NON_CANONICAL / PROPOSAL / NOT_IMPLEMENTATION / NOT_PROMOTED -->

# C33 Fresh Test Baseline Note

**Date:** 2026-08-17 (GMT+7) · **Branch:** `p2p-c33-bounded-autopilot-core` @ `835421d` (C32 head, parent C31 `40d9441`)

## Fresh full-suite run on C33 branch (before any C33 implementation)

`635 passed / 9 failed / 5 skipped / 105 subtests` in ~60s. Every failure reproduced and re-classified individually (tracebacks captured):

| # | Test | Failure mode | Classification |
|---|---|---|---|
| 1 | `test_p2p_secure_onboarding::test_ho21_binary_availability_read_only` | `host_binary_available(codex) is False` — no `codex` binary on PATH in this sandbox (`shutil.which('codex')` → None) | PRE-EXISTING env artifact: test assumes the C31-session sandbox's Codex CLI 0.147.0 installation |
| 2 | `test_ho31_codex_stays_auth_invalid_with_c27_evidence` | Assertion against durable AUTH_INVALID evidence path | Same env artifact (binary absent → NOT_INSTALLED short-circuit) |
| 3 | `test_ho33_uninstalled_hosts_are_discovered_as_not_installed` | `NOT_INSTALLED == AUTH_INVALID` mismatch | Same env artifact |
| 4 | `test_ho35_preflight_uses_no_model_calls` | `KeyError: 'owner_action_reason'` (fixture expects C31-session state) | Same env artifact |
| 5 | `test_ho39_doctor_output_is_machine_readable` | `KeyError: 'owner_action_reason'` | Same env artifact |
| 6 | `test_ho40_doctor_has_recommendation` | `KeyError: 'owner_action_reason'` | Same env artifact |
| 7 | `test_ho46_core_flow_has_no_vendor_branches` | `KeyError: 'owner_action_reason'` | Same env artifact |
| 8 | `test_p2p_project_eval::test_current_suite_has_real_recorded_trial_pairs` | `FileNotFoundError: .p2p/evals/suite.json` | PRE-EXISTING fixture gap: file missing on every lineage branch (verified C25–C32), never committed |
| 9 | `test_p2p_task_state::test_t18_c09_blocked_identity_state_remains_unknown` | `FileNotFoundError: .p2p/state/project-status.json` | PRE-EXISTING fixture gap: file missing on every lineage branch, never committed |

## Classification verdict

All 9 failures are **PRE_EXISTING_BASELINE_FAILURE**: seven are host-environment dependencies (Codex CLI binary presence / C31-session durable evidence state) and two are missing durable fixtures that were never checked into the repository. None is a C33 regression — the branch contained no C33 code at baseline time. The C32 preservation report's classification is **confirmed** by independent reproduction; the C32 report quoted the focused governance subset (572 passed / 2 failed when excluding the onboarding suite).

## C33 regression policy

C33 introduces **zero unexplained new regression**. After each checkpoint, the suite is re-run and each new failure must either be traced to a documented cause or STOP the goal. Pre-existing failures above are tracked separately and never used to mask regressions. Tests are not weakened; fixtures are not fabricated; missing `.p2p/state/project-status.json` and `.p2p/evals/suite.json` are not created just to green these tests (no manufactured history per policy §23).
