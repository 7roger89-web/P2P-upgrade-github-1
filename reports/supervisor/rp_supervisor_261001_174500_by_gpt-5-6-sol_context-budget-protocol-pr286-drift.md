# Supervisor Report: PR #286 context-budget protocol drift precheck

Verdict: REJECT

## Metadata
- Report file: rp_supervisor_261001_174500_by_gpt-5-6-sol_context-budget-protocol-pr286-drift.md
- Review time: 261001 174500 Asia/Bangkok
- Reviewer: gpt-5-6-sol
- Repo/project: 7roger89-web/P2P-upgrade-github-1
- Scope reviewed: PR #286 exact HEAD `d30636b0998c740660f937475ea62ba8ef4bd9b7`
- Claim reviewed: PR #286 is ready for acceptance/review against current main.
- Authority used: Owner continuation request; AGENTS.md; P2P_SUPREME_OPERATING_LAW_V1; Issue #285; .agents/skills/supervisor/SKILL.md; current GitHub PR/main/compare state.
- Related artifacts: Issue #285; PR #286; P2P Shield workflow run 36844938638.

## Executive Summary
- Problem: the candidate was created from main `4ce35d4559edb9f83023568ef7e6089132c54a8d`, but current main advanced during the task.
- Decision: REJECT this exact HEAD for acceptance because fresh compare reports `diverged`, `ahead_by=12`, `behind_by=6`.
- Required outcome: update the existing PR branch from fresh main without losing the bounded docs-only changes, then review the new exact HEAD.

## Blocking Findings

### [HIGH] Candidate exact HEAD is stale against current main
File: N/A
Issue: current main is `135dcf845b59c5fa09a0737a68fbf7b6b957778a`, while PR #286 HEAD is `d30636b0998c740660f937475ea62ba8ef4bd9b7`. Fresh compare reports the PR branch is six commits behind.
Evidence:
- GitHub current main read: `135dcf845b59c5fa09a0737a68fbf7b6b957778a`.
- GitHub compare `main...ct/context-budget-protocol-285`: `status=diverged`, `ahead_by=12`, `behind_by=6`.
- The six main-side commits change only `docs/RESEARCH-ADOPTION-LEDGER.md`, `docs/p2p-development/research/P2P-KONG-REVERSE-INTAKE-01.md`, and `governance/research-adoption-ledger.json`; these do not overlap the eight PR #286 paths.
Why this blocks acceptance: Issue #285 and RULE 16 explicitly require mutable Git state to be freshly reverified; the exact candidate cannot be accepted from a stale base.
Fix direction: merge current main into the existing PR branch, preserving both histories and the eight bounded PR paths, then re-run exact-HEAD review.
Re-review evidence required: new PR HEAD; fresh main comparison with `behind_by=0`; PR mergeability; required checks; source/doc review of the new exact HEAD.

## Source-Level Clearance Notes
- PR #286 eight changed paths: not rejected on content in this precheck; content review is deferred until the drift blocker is repaired.
- Current-main six commits: clear for merge-base repair because their changed paths do not overlap PR #286 changed paths.

## Evidence Checked
Passed:
- P2P Shield - BASE acceptance on old exact HEAD: workflow run 36844938638, conclusion `success`.
- PR metadata: open, draft, GitHub reports mergeable.
- Scope overlap check: current-main delta paths and PR #286 paths are disjoint.
- Verification freshness: fresh for current GitHub state at review time.

Failed:
- Fresh main relation: candidate is six commits behind.
- Verification freshness: fresh.

Not run:
- Runtime/unit tests: not needed to prove the drift blocker; the candidate is docs-only and content acceptance is deferred until updated HEAD.
- Anvien: not required for this docs-only drift precheck.

## Invariant Closure
- affected invariant: exact durable Git identity must be current before acceptance; mutable handoff claims are not authority.
- sibling surfaces checked: current main SHA, PR exact HEAD, compare relation, changed-path overlap, workflow run.
- residual unverified same-invariant surfaces: content acceptance at the future updated HEAD.

## Required Fix List For Resubmission
1. Merge current main `135dcf845b59c5fa09a0737a68fbf7b6b957778a` into `ct/context-budget-protocol-285` without dropping either side.
2. Re-review the new exact HEAD from fresh GitHub state.

## Overall Evaluation
The content is not rejected here; the exact candidate identity is. The repository advanced during the task, and accepting the stale head would violate the very mutable-state rule this PR introduces.
