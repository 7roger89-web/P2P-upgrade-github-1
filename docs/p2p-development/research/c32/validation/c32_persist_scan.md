<!-- RESEARCH_ONLY / NON_CANONICAL / PROPOSAL / NOT_IMPLEMENTATION / NOT_PROMOTED -->

# C32 Durable Preservation — Secret Scan & Validator Record

**Date:** 2026-08-17 (GMT+7) · **Branch:** `p2p-c32-hermes-audit` @ C31 head `40d9441` (base)

## Secret scan (gitleaks 8.18.4, custom config `/tmp/gl.toml`, JSON report)
- Worktree (full repo, including new `docs/p2p-development/research/c32/`): **0 findings** (`no leaks found`)
- Branch history (`--log-opts p2p-c32-hermes-audit`): **0 findings**
- Post-range `p2p-c32-hermes-audit..HEAD` (C31 lineage): **0 findings**

Persisted-artifact guard: the persistence script rejects any file containing secret-like patterns (`ghp_`, `github_pat_`, `Bearer`, credential refs) — all 9 files passed before write. Explicitly excluded from preservation: PAT files, `/home/ubuntu/upload/*`, sandbox operational notes (`04_session_notes.md`), vendored Hermes source tree, and the Hermes tarball.

## Validator run (pytest on worktree; only new files are under `docs/.../research/c32/`)
- Full suite minus secure-onboarding (env artifact, see C32 terminal report §25): **572 passed, 2 failed, 5 skipped, 105 subtests passed**
- The 2 failures (`test_t18_c09...` in `test_p2p_task_state.py`, `test_current_suite_has_real_recorded_trial_pairs` in `test_p2p_project_eval.py`) are the same pre-existing fixture gaps classified at C31 baseline — they fail on C31 head *without* the new research files and are unrelated to the `docs/` research additions (verified: `git diff --stat -- docs/` empty before commit; the failures touch task-state fixtures, not docs).
- Governance-critical suites: development_control, ledger_provenance, development_charter, goal_closure, goal_subsystem — all passing.
- No test was weakened; no governance file was modified; canonical governance/roadmap/runtime untouched.

## Candidate policy
Research-only documentation under `docs/` does not change code or candidates; existing deterministic candidate policy requires no new candidate. No candidate minted. Official baseline remains `8.4.7-C-codex.19`.
