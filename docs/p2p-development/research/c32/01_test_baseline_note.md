<!-- RESEARCH_ONLY / NON_CANONICAL / PROPOSAL / NOT_IMPLEMENTATION / NOT_PROMOTED -->

# C32 Test baseline note (research artifact)

Running full suite at C31 head (commit 40d9441) on C31 lineage:

- Focused governance suite (development_control + goal_closure + c31_live_certification): **83 passed, 2 skipped** (after creating `.tmp/` and registering local tracking branches — the two earlier failures were env-artifacts: missing .tmp dir and unresolvable ref names in shallow clone, not code defects).
- Full suite: 635 passed / 9 failed / 5 skipped / 105 subtests.

The 9 failures are **host-environment-dependent**, not regressions against C31:
1. test_p2p_secure_onboarding ho21/ho31/ho33/ho35/ho39/ho40/ho46 — the C31 session's sandbox had Codex CLI 0.147.0 installed (visible in evidence/c31_live_probe.json: run in /home/ubuntu with codex on PATH). The C32 sandbox has **no `codex` binary on PATH**, so `host_binary_available()` → NOT_INSTALLED and the onboarding machinery correctly reports `connection_status=NOT_INSTALLED`, `AUTH_CONFIG_ABSENT`, `owner_action_required=true`. Tests asserting the durable AUTH_INVALID acceptance case fail only because the durable-evidence path now short-circuits at binary absence in this environment. Reproduction (repro_ho31.py) confirms the machinery behaves correctly per contract: durable state preserved, no fabrication, zero model calls.
2. test_p2p_project_eval test_current_suite_has_real_recorded_trial_pairs — eval-fixture environmental dependency.
3. test_p2p_task_state test_t18_c09_blocked_identity_state_remains_unknown — rerun to classify.

4. test_t18 (.p2p/state/project-status.json) and test_current_suite_has_real_recorded_trial_pairs (.p2p/evals/suite.json) — both fixture files are **MISSING on every branch in the lineage** (verified C25–C31). These tests reference durable-state fixtures that were never checked in; they fail in any fresh clone, not just this sandbox. Classification: pre-existing fixture gap in the repository, not a C31 regression and not caused by this C32 session.

Implication for C32: no C31/C30 code defect detected. The secure-onboarding failures are expected machine-state differences between the C31 sandbox and the C32 sandbox; per policy I do NOT weaken tests and do NOT fabricate fixes to governance machinery during research-only work. Recorded as a finding.

Closure checker at C31 head: `Goal C28: CONSISTENT` (same verdict as C30/C31 terminals); claim boundaries PASS (no CONTEXT_CONTROLLER, no AUTH_ACTION, no SECOND_EXECUTOR, no BACKGROUND_AUTONOMY introduced).
