# Supervisor Review — P2P-C15 Current Fix and Field Test

## Verdict

`PASS / BOUNDED_DELEGATION_FOUNDATION_READY`

This PASS is bounded to the local, callback-backed C15 capability and its
durable C11/C10 integration. It is not a release, promotion, live host-worker,
provider/model, or deployment approval.

## Authority reviewed

- Current user C15 brief from the attached pasted-text file.
- Project `AGENTS.md`.
- Existing C11/C12/C15 plan, evidence, benchmark, and actual-status ledgers.
- Existing C10 Decision Trace, C11 task-state, and C12 foreground-execution
  contracts.
- Official promoted artifact
  `D:\AI\P2P_dev\P2P-8.4.7-C-Codex-Edition-v19.zip`, SHA-256
  `3a9ee51321e1f5e40e35ce73eb90727cddb571a672aa095d16d76af2feb03dd8`.

## Scope accepted

The reviewed follow-up is limited to:

1. stable semantic plan/task handoff fingerprinting;
2. stable C15 decision-trace identity independent of `decided_at`;
3. explicit missing-candidate boundary coverage;
4. a reusable disposable project-style field harness A-F;
5. an 18-case evaluation matrix and evidence refresh.

No C11/C12 source rewrite, second execution architecture, second ledger,
router/model selection path, host identity simulation, Logistics change, or
release action is present.

## Source and invariant inspection

- `.p2p/system/p2p_capabilities/bounded_delegation.py` contains the semantic
  `_plan_contract_fingerprint` helper at line 1027, timestamp-independent
  decision trace identity at line 1445, and handoff binding at line 1493.
- The helper includes goal owner, plan scope/non-scope/revision, and task
  semantics; it excludes volatile plan/task timestamps and preflight state.
- The existing `WorkerHandoff` still excludes the random `handoff_id` from its
  fingerprint and retains the one-child/depth-one/proposal-only invariants.
- Parent verification still binds current candidate state and C10 evidence
  before using the existing C11 completion path.
- `scripts/p2p_c15_field_test.py` uses only the real local C11/C15 APIs and a
  repo-local disposable fixture. Its output path is checked to remain under
  the repository root.
- `tests/test_p2p_bounded_delegation.py` adds the explicit missing-candidate
  fail-closed case.

## Evidence accepted

- Focused C15: `24/24 PASS`.
- Affected C15+C11+C12: `64/64 PASS`.
- Full suite: `218/218 PASS`.
- Field A-F: `all_checks_pass=true`; JSON SHA-256
  `69fa8143c065d6960ec0ae4540aabcbc0ad8f4df8bffd05011ed024023437dc0`.
- Field outcomes prove DIRECT, DELEGATE, parent-only verification, failed
  verification staying non-DONE, child delegation rejection, and durable
  interruption/resume without automatic start.
- The field fixture reports `synthetic_host_identity=false` and
  `no_external_side_effects=true`.
- Fresh Anvien root/system analysis has zero parse failures. Current C15 file
  detail is parsed, `stale=false`, 283 symbols, 607 local relationships, 832
  unresolved references, 32 linked flows, and high warning. File-level impact
  reports 69 contained/impacted symbols. Direct symbol lookup for the two
  edited methods is unresolved by the current graph index; the review treats
  that as a graph-resolution limitation, not as zero impact.

## Failure and boundary review

- The fresh regression initially caught a real fingerprint instability; the
  correction is narrow and the rerun is green.
- `anvien detect-changes` returns Git exit 129 because `.git` is absent. No
  repository was initialized and no commit is claimed.
- Development doctor and governance drift are currently `FAIL` only at the
  governance-drift check because the existing protected
  `docs/notes_decisions_log/notes_decisions_log_20260816.md` is drifted. All
  relevant C15 runtime, canonical 8/8, installed-foundation, package metadata,
  and decision-trace checks pass. The protected notes log was not altered,
  deleted, or suppressed in this C15 follow-up.
- A fresh package build is rejected by the existing lineage guard because
  development `.15` is below promoted `.19`. This is the correct fail-closed
  result; no metadata rewrite or promotion was attempted.
- The prior `.15` candidate is historical/unpromoted and is not claimed to
  contain the current follow-up.
- Live host callback/identity receipt remains unsupported and unclaimed. The
  local field callback is the nearest real supported boundary.

## Invariant closure

| Invariant | Review result |
|---|---|
| Direct remains first-class | closed; field A and focused tests |
| Delegation requires material value and candidate proof | closed; field B and missing-boundary test |
| Parent remains durable owner | closed; C11 task state and field D/F |
| Child permissions/scope are subsets | closed; focused tests |
| One child/depth one/no grandchild | closed; field E and structural C12 regression |
| Proposal-only worker result | closed; field B/D |
| Parent independently verifies before DONE | closed; field C/D |
| Bounded retry/fallback and uncertain mutation fail closed | closed; focused regression |
| Decision trace uses existing ledger | closed; focused trace plus doctor |
| No provider/model/agent selection before strategy | closed; CLI/order tests |
| No live host identity inference | closed as explicit unsupported boundary |

No same-invariant required follow-up remains for the accepted local scope.

## Product and architecture decision

The C15 implementation is additive and composes C11/C12/C10 rather than
replacing them. The project-style field test is sufficient evidence that the
DIRECT-versus-DELEGATE policy is useful and stable within the supported local
foreground boundary. It supports proceeding to a separately bounded P2P-C16
goal, subject to C16's own scope and gates; C16 was not implemented here.

## Final acceptance

Accept C15 as `PASS / BOUNDED_DELEGATION_FOUNDATION_READY` with explicit
non-release, non-host, non-promotion limits. Stop now. Do not deploy, release,
promote `.19`, repair the protected notes log in this task, initialize Git, or
expand into C16 implementation.
