# Controlled Execution Canonical Candidate Actual Status

Date: 2026-08-25  
Candidate: `codex/p2p-controlled-execution-canonical-candidate-03`  
Canonical: `codex/p2p-post74-development-01` at
`b26189daf33afadbf6fe3eeef4f773f1373ea751`

## P0 decision

P0 is complete. A fresh fetch found no canonical branch drift because the
reported local canonical HEAD and tree remain exact; the remote branch ref is
absent and therefore cannot supply a conflicting remote truth. Candidate-03 was
created directly from the exact local canonical commit.

The historical feature branch is semantic source only. The accepted source
commit is `33589cd15ed0a1e9b010b43319464e864d81dc63`, based on merge-base
`a716a5066db4b213af8ef44a392afbf0e4329ce6`; it is not merged directly.

## Scope status

| Surface | Canonical finding | Candidate action |
|---|---|---|
| AutoPilot/FW01 task state | partial C11 binding | port existing `TaskStateStore` seam |
| Foreground intent/write seam | partial authority/lease/candidate/worktree binding | port existing checks only |
| FW01 quality verdict | canonical strict shape/type/literal-bool guard present | preserve exactly |
| AERG/QI core | outside accepted delta | unchanged |
| Owner/provisional/governance state | protected/unrelated | not copied or repaired |

## P1/P2 status

- P1-A C11: implemented and committed in
  `669b97f15f83ffe80b5d611a678e8bb2eaae7f1f`.
- P1-B authority/lease/candidate/worktree: implemented and committed in
  `3f3ad28f7acb...`.
- P2 regression/classification: complete for the candidate; 223/227 broad
  tests passed and the four historical failures reproduced on the clean base
  probe as inherited fixture/environment failures.
- Freeze and independent Supervisor review: pending final documentation
  binding.

## Evidence/tool limitation

Anvien was refreshed, but file-detail/impact cannot resolve the hidden runtime
paths because the local registry contains duplicate/ambiguous repository
entries. This is recorded as a tooling limitation; direct Git/source/runtime
evidence remains required and no graph result is treated as authority.

## Stop rules

No source is changed outside the accepted semantic surface. No merge, Owner
approval, promotion, release, deployment, or host mutation is performed. Any
post-Supervisor byte mutation invalidates the review and blocks handoff.
