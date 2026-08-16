# Coder Report — P2P-C17 Safe Bounded Parallel Foreground Execution

## Scope

Implemented the requested C17 foundation as an additive bounded foreground
composition of the existing C11 task state and C15 delegation surfaces.

- maximum parallel children: `2`;
- default strategy: sequential when independence, value, identity, or control
  evidence is uncertain;
- no scheduler, queue, daemon, remote bridge, persistent worker pool, second
  router, second ledger, or simulated eight-agent quorum;
- official `.19` remains preserve-only and no promotion/release was attempted.

## Durable state and lineage

- Reconciled active source metadata from stale `.15` to unpromoted
  `8.4.7-C-codex.20` through the guarded `reconcile-lineage` operation.
- Exact official baseline retained: `.19`, SHA-256
  `3a9ee51321e1f5e40e35ce73eb90727cddb571a672aa095d16d76af2feb03dd8`.
- Recorded C17 as `DONE/PASS` with
  `PARALLEL_EXECUTION_FOUNDATION_READY`.
- Kept `LIVE_PARALLEL_EXECUTION_CERTIFIED=false` and
  `NOT_CERTIFIED`; no native host child callback was available, and tests did
  not claim live certification.
- C08 remains `DEFERRED`; C09 remains
  `BLOCKED/EVENT_EVIDENCE_UNAVAILABLE`; canonical capability denominator is
  still `8/8` and Aesthetica remains optional/noncanonical.

## Implementation

- `.p2p/system/p2p_capabilities/parallel_execution.py`
  - recovers existing READY tasks only;
  - checks DAG dependency direction, isolated contexts, read/write/delete
    scopes, shared resources, aggregate permission/budget limits, and value;
  - composes two distinct C15 controllers with explicit group context;
  - persists group and child bindings under the existing foreground state root
    and appends events to the existing execution ledger;
  - independently verifies children, then requires parent combined verification
    for mutation groups;
  - preserves partial success, freezes unknown mutation/control-plane states,
    records truthful cancellation, and never starts a third rescue child.
- `.p2p/system/p2p_capabilities/task_state.py`
  - adds per-root re-entrant locking for concurrent state/ledger writes;
  - adds `record_event` without introducing a second ledger.
- `.p2p/system/p2p_capabilities/bounded_delegation.py`
  - adds only the explicit C17 group/scope context; ordinary C15 remains
    single-child and depth-one.
- `scripts/p2p_parallel.py`, package inventory, doctor inventory, exports, and
  focused tests were added/updated.
- `scripts/p2p_development_control.py` now has guarded C17 lineage transitions,
  final state projection, and no-promotion candidate recording.

## Verification

- Focused C17 suite: `14/14 PASS`, including the beginner P1-P12 cases.
- Development-control suite: `21/21 PASS`.
- Affected C11/C12/C15/development-control/C17 subset: `96/96 PASS`.
- Full repository discovery: `236/236 PASS`.
- `python -m compileall -q scripts .p2p/system/p2p_capabilities tests`: PASS.
- Source doctor (`--root . --role development`): PASS.
- Candidate package build: PASS, version `.20`, 412 package files.
- Extracted candidate package verify and package doctor: PASS; baseline source
  inventory `152/152`.
- Governance validation, protected runtime lock, and drift: PASS with no
  failures or warnings.
- Root and `p2p-system` Anvien graphs refreshed. File-level warnings are
  recorded as scope warnings: C17 is HIGH, task state/C15 remain high/critical
  impact surfaces, and they were handled with additive changes.
- `anvien detect-changes --scope all` cannot produce a diff because this
  checkout has no `.git`; no repository was initialized and no commit is
  claimed.

## Candidate and artifact boundary

Final candidate:
`.tmp/p2p-c17/candidates/P2P-8.4.7-C-Codex-Edition-v20-c17-final2-candidate.zip`

Final candidate SHA-256:
`7c05c1d0fe2c2d33470d1487a07cfc66aebc0a96d610b9d2a238e76d0fcb0664`

Final candidate size: `2,518,543` bytes. The earlier final candidate remains
historical provenance only; the final2 record is the current unpromoted
candidate binding.

Candidate status is `UNPROMOTED`. The official `.19` ZIP was not overwritten,
rebuilt, installed over, or modified.

## Handoff

The local C17 foundation is ready for supervisor acceptance. The truthful
terminal claim is `PASS / PARALLEL_EXECUTION_FOUNDATION_READY`; it is not a
claim of live host parallel certification, release approval, promotion,
deployment, or Git commit.
