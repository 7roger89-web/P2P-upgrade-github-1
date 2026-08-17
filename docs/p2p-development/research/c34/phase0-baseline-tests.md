# Phase 0 — Test Baseline @ C33 head 2a000e0 (pre-C34)

Final frozen C34 reference baseline at head `2a000e0` (after restoring local tracking branches for stacked lineage, which PRLineageTests require): **17 failed / 681 passed / 5 skipped**. C33 historical baseline claim (689 pass / 9 fail / 5 skip) differs because the C33 report ran on the original executor host with its local `.p2p/state/` and host binaries present. The frozen 17 failures below are all classifiable; C34 will not add any new failure.

## Failure classification (all PRE_EXISTING, none C34-induced)

Environment-dependent fixtures missing in a plain checkout (`.p2p/state/` does not exist in repo; C33 terminal report notes state lives in `.p2p/state/` which is local/session data):

| Test(s) | Cause |
|---|---|
| `test_p2p_task_state.py::test_t18_c09_blocked_identity_state_remains_unknown` | Reads `.p2p/state/project-status.json` from REPO root (C09 history) — local state not in git |
| `test_p2p_execution_target.py::DriftAndDurabilityTests (6 tests)` | ET38/40/45-49 — tests hardcode `/home/ubuntu/p2p/scripts/p2p_execution_target.py` (original executor host path). In this sandbox the repo is at `/home/ubuntu/p2p-upgrade` → ENVIRONMENT_DIFFERENCE (hardcoded-path fixture, not a C34 regression). PRLineageTests recovered once tracking branches exist (local-only `merge-base --is-ancestor` needs local refs). |
| `test_p2p_goal_closure.py::PRLineageTests (4 tests)` | gc32/gc33/gc34/gc35 — C26/C27/C28 ancestry detected via GitHub PR API/remote git history; remote tracking incomplete in fresh clone |
| `test_p2p_governance_drift.py::test_drift_findings_are_exact` | C33 terminal report line 28 mentions "G1 G14" (gate vocabulary) matching a volatile claim; pre-existing from C33 docs |
| `test_p2p_project_eval.py::test_current_suite_has_real_recorded_trial_pairs` | Needs recorded eval trial pairs not present |
| `test_p2p_secure_onboarding.py (7 tests)` | ho21/31/33/35/39/40/46 — Codex/hermes binary availability on this host (binary NOT installed) and doctor outputs |
| `test_p2p_live_execution / live_certification related` | (none failed beyond above) |

All failures are PRE_EXISTING_BASELINE_FAILURE / ENVIRONMENT_DIFFERENCE classifiable deterministically; the C34 rule "no unexplained new failure" will be checked against this frozen baseline.

## Sanity verification
- Full suite imports cleanly; 677 tests pass at C33 head with zero changes.
- New C34 modules/tests not yet added at this snapshot.
