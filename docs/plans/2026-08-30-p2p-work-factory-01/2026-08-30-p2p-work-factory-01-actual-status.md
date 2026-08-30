# Actual status — P2P-WORK-FACTORY-01: minimum durable multi-executor work-item and handoff flow

## Authority and isolation

- Fresh canonical `origin/main` matched the expected SHA
  `348d13014f07ff98491997039be6966068b747dc` (tree
  `058073c5478ccd56ebc80e0a075a691f8a86b81e`). No drift.
- Work stayed on the session branch
  `arena/01a051ee-p2p-upgrade-github-1` (one branch, one PR, no merge).
- MPFB, TMPGC, Game Truyen, Fast Path redesign, Control Tower behavior,
  and the authority framework were not touched. No Execution Host was
  built. No merge/promote/release/deploy was performed.

## What was added (minimum glue only)

- `.p2p/system/p2p_capabilities/work_item_handoff.py`
  - `WorkItem` minimum durable identity: `WORK_ITEM_ID, PROJECT, WORKSTREAM,
    BASE_SHA, BASE_TREE, EXECUTOR, SCOPE, DEPENDENCIES, EXPECTED_OUTPUT,
    SESSION_ID` + runtime `CANDIDATE_SHA, CANDIDATE_TREE, VERDICT, NEXT_GATE`.
  - Three event types appended to the existing `.p2p/state/execution-ledger.jsonl`
    through the existing ledger writer (the same surface the Control Tower
    uses): `WORK_ITEM_REGISTERED`, `WORK_ITEM_LANE_STARTED`, `WORK_ITEM_RETURN`.
  - `WorkItemHandoff` coordinator: `register_work_item`, `start_lane`,
    `ingest_return`, `integration_queue`, `verify_integration_queue`.
  - The execution lane is the executor's existing Control Tower host lane;
    the Control Tower session is registered through the existing
    `ControlTower.start_session`, and the return packet is parsed/checked by
    the existing `ControlTower.ingest_response` (binding enforcement,
    idempotent replay, stale-base reconciliation) before the work-item layer
    binds explicit candidate identity and appends the work-item return event.
  - Fail-closed detection: duplicate/conflicting work-item identity
    (`WORK_ITEM_IDENTITY_CONFLICT`), ambiguous project/workstream binding
    (`AMBIGUOUS_PROJECT_WORKSTREAM_BINDING`), stale base (`STALE_BASE` /
    `WORK_ITEM_BASE_MISMATCH`), missing candidate identity
    (`CANDIDATE_SHA_MUST_BE_EXPLICIT`), candidate mismatch, scope overlap
    (`WORK_ITEM_SCOPE_OVERLAP`), orphan returns, lane-order violations, and
    dependency cycles.
- `scripts/p2p_work_item.py` — thin foreground CLI
  (`register` / `lane` / `return` / `queue` / `verify`).
- `tests/test_p2p_work_item_handoff.py` — focused acceptance suite.

## Acceptance result (two parallel fixtures)

Two non-overlapping fixture work items (`fixture-alpha` on executor `CODEX`,
`fixture-beta` on executor `GEMINI`) in project `P2P` / workstream
`P2P-WORK-FACTORY-01`:

1. Both start from explicit base identity (`BASE_SHA`/`BASE_TREE` required,
   `UNKNOWN` refused).
2. Both return independent result packets (distinct session bindings,
   distinct packet fingerprints).
3. Provenance is retained: base/candidate SHA+tree, session id, packet
   fingerprint, executor/lane, and the raw Control Tower return packet in
   the same durable ledger.
4. Both enter the integration queue without ambiguity: explicit
   PROJECT/WORKSTREAM/EXECUTOR per entry, deterministic topological order,
   one lane per executor, `LANES = {CODEX: [fixture-alpha], GEMINI:
   [fixture-beta]}`.
5. Owner/review gates are preserved: an owner-gated return stays
   `WAITING_OWNER_GATE` through queue and verify (the gate object is carried
   verbatim and never executed); a clean return verifies to `VERIFIED` with
   `NEXT_GATE=OWNER_REVIEW`. `PROMOTED/MERGED/DEPLOYED/RELEASED` are always
   NO in every projection.

## Focused tests

- `python3 -m unittest tests.test_p2p_work_item_handoff` — 14/14 PASS,
  including the two-parallel-fixture acceptance flow, owner-gate
  preservation, duplicate/conflicting identity, ambiguous binding,
  stale base, return-from-different-base, missing candidate identity,
  scope overlap, lane ordering, orphan return, dependency ordering,
  durability across instances (no second store), and CLI smoke.
- Adjacent shared suites green: `test_p2p_control_tower_durable` 9/9,
  `test_p2p_control_tower_session_handoff` 28/28,
  `test_p2p_parallel_execution` 14/14.
- Pre-existing/environment, not caused by this change:
  `tests.test_p2p_task_state.P2PTaskStateTests.test_t18_c09_blocked_identity_state_remains_unknown`
  fails identically on the unmodified `origin/main` baseline in a fresh
  clone (it reads the gitignored runtime file
  `.p2p/state/project-status.json`, absent from a clean checkout).

## Terminal state

Minimum durable flow proven. No promotion, merge, release, deployment, or
Owner Gate execution performed.
