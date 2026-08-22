# Coder Handoff Report — P2P C74 Successor Evaluator Lifecycle

## Result

The single sealed `.73` promotion-readiness defect was repaired in a fresh successor worktree. The `.74` candidate is sealed, verified, unpromoted, and ready for independent review.

Terminal handoff:

`P2P_EVAL_LIFECYCLE_SUCCESSOR_HANDOFF_SEALED_READY_FOR_INDEPENDENT_REVIEW`

## Scope and root cause

- Root cause: `EVAL_OWNERSHIP_CONTRACT_MISMATCH` / `WRONG_EVALUATOR_PATH_CONTRACT`.
- The `.73` completion case built `<consumer>/scripts/p2p_eval.py`, but normal installation owns the project evaluator at `<consumer>/.p2p/system/scripts/p2p_eval.py`.
- Contract selected: `CANONICAL_INSTALLED_EVALUATOR` (Option B).
- No suite schema, grading policy, router, identity, provider, permission, or installer-copy behavior was changed.

## Source change

- Worktree: `D:/AI/P2P_dev/P2P-upgrade-github/.tmp/p2p-c74-successor-eval-lifecycle-20260822`
- Branch: `codex/p2p-c74-successor-eval-lifecycle-01`
- Source freeze commit: `4eafc3ccb6de52f2b5f9b9b75b754c9d9a2a9b53`
- Source tree: `064d52121cd6220602fbd455614bccc0c3b3dd2b`
- Implementation commits: `2fc5d43` (resolver), `38ab208` (focused lifecycle tests), `4eafc3c` (successor metadata freeze).
- Resolver behavior: installed targets use `runtime_root/scripts/p2p_eval.py`; package/source targets use root `scripts/p2p_eval.py` only when package markers are present; absent installed helpers fail closed.

## Fresh candidate and consumer proof

- Candidate: `reports/candidates/P2P-8.4.7-C-Codex-Edition-v74.zip`
- Candidate size: `2,899,886` bytes
- Candidate SHA-256: `2b82dea10695abb1c99253be1205728335a114df42cececde2fcca5c1727fd12`
- Mint count: 1; no rebuild or overwrite after mint.
- Exact package extraction/verify: PASS; 493 members, all accounted, no unsafe or duplicate paths.
- Normal project install: `FRESH_INSTALL` PASS into the disposable consumer; no root `scripts/p2p_eval.py`; installed canonical helper exists at `.p2p/system/scripts/p2p_eval.py`.
- Normal bootstrap created `.p2p/evals/suite.json`; no hand-copy or source-checkout dependency was used.
- Eval matrix: five cases x baseline/P2P x two trials = 20 case executions across 10 trial slots; 20/20 passed and recorded; unexpected writes `0`.
- Eval gate: PASS; P2P mean `1.0`, baseline mean `1.0`, delta `0.0`, case regressions `0`.
- Strict installed Doctor: PASS, `ok=true`.
- Technical prepare: `TECHNICAL_GATES_PASS_USER_APPROVAL_REQUIRED`; subject is bound to the exact candidate SHA, rollback is exact sealed `.72`, technical report SHA is `1e1cd20068d69072f0ffc0091328c67a402f148979dbd16a76942b63d53871f5`.

## Regression and security evidence

- Runtime capability suite: `335/335 PASS`, 6 declared skips.
- Provider-neutral C35: `57/57 PASS`.
- Bounded suite: `94/94 PASS`.
- FW05/A–Z owner-experience suite: `29/29 PASS`, 1 declared skip.
- Focused project-eval suite: `5/5 PASS`.
- Security unit suite: `2/2 PASS`; package and extracted-runtime scans: zero findings.
- MAP-before-work and MAP-freshness suites: PASS.
- Protected `.72`, `.73`, and official `.19` identities: unchanged.

## Disclosures

- The full repository unit suite is not green in either comparison: C74 `703 tests, 15 failures, 25 errors, 3 skips`; clean parent `700 tests, 14 failures, 27 errors, 3 skips`. The same legacy FW01/C27-C28/governance/registry/task-state/workflow family is present; this is disclosed, not claimed as a full-suite PASS.
- The focused workflow file retains one known pre-existing `transient_helper_paths` failure.
- The first package-build wrapper returned a Windows Unicode encoding error after writing the valid artifact. The artifact was independently extracted and verified, then preserved without overwrite.
- Historical `test_exact_fresh_machine.py` and `fw05_supervisor.py` command wrappers contain non-portable hard-coded path handling on this Windows host. Their relevant package/install and 29-test matrix evidence is recorded separately; these wrapper failures are not hidden.

## Boundary confirmation

No approval, promotion, finalize, release, deployment, merge, tag, external communication, C43, AERG, multi-AI certification, root owner worktree edit, C72/C73 artifact edit, official `.19` edit, or unrelated project mutation was performed.

The candidate remains `MINTED_UNPROMOTED_CANDIDATE`. The next action is independent review, not promotion.
