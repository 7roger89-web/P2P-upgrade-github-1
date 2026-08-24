# Controlled Execution Canonical Candidate Preparation Plan

## Goal

Create a frozen candidate descended from the freshly fetched canonical
`b26189daf33afadbf6fe3eeef4f773f1373ea751`, porting only the accepted
Controlled Execution hardening seams. Preserve the canonical FW01 quality
verdict repair and stop before merge, approval, promotion, release, or deploy.

## Scope

- C11 durable task-state binding through the existing AutoPilot/FW01 seam.
- Pre-code `ExecutionIntent`, execution authority, FW06 lease, frozen-candidate
  stale-audit, and worktree/executor binding at the existing foreground write seam.
- Narrow CLI permission projection and necessary tests/docs/evidence.
- Candidate-specific regressions, validators, deterministic freeze, and a fresh
  read-only Supervisor review.

## Non-goals and protected boundaries

- Do not merge the historical feature branch directly.
- Do not copy owner-dirty files, `.tmp/rr`, provisional RI-009, or unrelated
  research/governance state.
- Do not modify AERG/QI core or weaken/delete canonical FW01 safety tests.
- Do not add a router, scheduler, queue, database, second task store, second
  executor, permission engine, or capability.
- Do not repair inherited validator debt or Windows harness encoding.
- Do not merge, obtain Owner approval, promote, release, deploy, or mutate host state.

## Ordered gates

### P0 — canonical binding and status

- Fetch current truth and record branch, commit, tree, ancestry, and no remote-ref drift.
- Create the candidate worktree directly from the exact resolved canonical commit.
- Read the relevant approved execution/evidence, foundation, trust-boundary, and
  test/eval contracts; record the Anvien hidden-path limitation.
- Inventory the accepted feature commit as semantic input only and define the
  preserve/edit surface.

### P1-A — C11 task state

- Port only the existing `TaskStateStore` binding, descriptor/goal compatibility,
  durable restart/checkpoint/completion transitions, and fail-closed exception paths.
- Verify restart, drift, goal mismatch, corruption, and executor exception behavior.

### P1-B — authority and mutation seam

- Port only the existing intent, explicit permission, live FW06 lease, baseline,
  candidate, workspace, scope, and executor binding checks.
- Verify positive mutation and negative lease/authority/candidate/worktree paths.

### P2 — candidate regression and freeze

- Run focused/affected/broad tests, compile, doctor, and validator observation.
- Re-run the four prior broad-suite failures on canonical base and candidate and
  classify each as inherited/environmental/fixture-related or introduced.
- Commit evidence before freeze; compute candidate/canonical/tree/matrix/surface/
  evidence hashes; then run a fresh read-only Supervisor against that exact commit.
- After Supervisor review, perform only read-only byte/tree/status verification.

## Acceptance

The success terminal is permitted only when exact ancestry, narrow semantic port,
candidate-specific regression evidence, inherited-vs-introduced classification,
deterministic frozen identity, independent Supervisor PASS, and no post-freeze
mutation are all proven:

`CONTROLLED_EXECUTION_HARDENING_READY_FOR_OWNER_MERGE_GATE`

Otherwise stop with:

`CONTROLLED_EXECUTION_HARDENING_CANONICALIZATION_BLOCKED_<REASON>`

## Status

- [x] P0 actual status and candidate binding recorded.
- [x] P1 semantic port and focused verification committed.
- [x] P2 regressions and inherited-failure classification complete.
- [ ] Frozen identity bound.
- [ ] Independent read-only Supervisor PASS.
- [ ] Post-review immutability verified.
