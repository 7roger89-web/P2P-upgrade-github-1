# Coder Report: Controlled Execution Canonical Candidate

Status: READY_FOR_INDEPENDENT_SUPERVISOR_REVIEW  
Date: 2026-08-25  
Branch: `codex/p2p-controlled-execution-canonical-candidate-03`  
Candidate implementation HEAD: `3f3ad28f7acb65f782c751bea78d039ebd59b5f2`  
Canonical base: `b26189daf33afadbf6fe3eeef4f773f1373ea751`  
Merge-base: `b26189daf33afadbf6fe3eeef4f773f1373ea751`

This is a development-candidate handoff. It does not authorize merge, Owner
approval, promotion, release, deployment, or permission widening.

## Scope and invariant family

The accepted semantic delta is limited to the existing P2P control plane:

- C11 durable task-state binding through `TaskStateStore` in AutoPilot/FW01.
- Pre-code `ExecutionIntent` binding for objective, baseline, affected surface,
  acceptance/evidence, scope, and material boundaries.
- Explicit execution authority and FW06 lease checks at the real mutation seam.
- Frozen candidate/audit fingerprints and stale successor behavior.
- Worktree, baseline, task, lease, permission, and executor composition.
- Necessary focused tests, CLI permission projection, and candidate evidence.

No upstream harness was vendored. No second orchestrator, agent loop, task store,
router, permission engine, canonical agent, or capability was added.

## Invariant Family Map

| Invariant | Production surface | Closure status |
|---|---|---|
| Durable task state is authoritative | `autopilot_loop.py`, `p2p_fw01_loop.py` | Closed by existing `TaskStateStore` seam and restart/corruption/exception tests. |
| Mutation is precontracted and authorized | `foreground_execution.py`, `scripts/p2p_foreground_execution.py` | Closed by `ExecutionIntent`, explicit permissions, owner gate, lease, baseline, scope, and executor-binding checks. |
| Candidate/audit identity is immutable for an audit | `foreground_execution.py` | Closed by candidate-state fingerprints and stale-audit tests. |
| Context/handoff does not grant authority | existing C19/bounded delegation plus foreground negative tests | Existing invariant verified; no duplicate mechanism added. |
| Quality and done state remain fail-closed | `p2p_fw01_loop.py`, checkpoint tests | Canonical FW01 quality-verdict repair preserved; 6/6 checkpoint suite passes. |

## Sibling surfaces checked

- AutoPilot/FW01 task-state composition.
- Foreground controller preflight and executor mutation callback.
- CLI permission projection.
- Existing C19 task-targeted context and bounded delegation handoff.
- Existing adaptive complexity/assurance policy.
- Existing FW01 quality checkpoint and self-reference guard tests.
- Canonical FW01 repair commits `1b22745`, `6c1746d`, and `b26189d` ancestry.

## Legacy fallback status

No legacy transcript, role-name, handoff, context-path, provider/model, or
upstream-permission fallback can create write authority. Existing P2P Permission
Gate/Authority Profile/FW06 semantics remain authoritative.

## Files changed by the semantic implementation

The two implementation checkpoints contain exactly these nine paths:

1. `.p2p/system/p2p_capabilities/autopilot_loop.py`
2. `.p2p/system/p2p_capabilities/foreground_execution.py`
3. `.p2p/system/p2p_capabilities/p2p_fw01_loop.py`
4. `.p2p/system/p2p_capabilities/tests/test_checkpoint_quality_gate.py`
5. `scripts/p2p_foreground_execution.py`
6. `tests/test_p2p_adaptive_orchestration.py`
7. `tests/test_p2p_controlled_execution_hardening.py`
8. `tests/test_p2p_foreground_execution.py`
9. `tests/test_p2p_task_targeted_context.py`

The coverage matrix and candidate evidence plan are separate candidate
documentation. Provisional RI-009, `.tmp/rr`, owner-dirty state, and the
external-harness research addendum are not in these commits.

## Verification

| Test or validator | Result | What it proves |
|---|---|---|
| `python -m unittest tests.test_p2p_foreground_execution tests.test_p2p_adaptive_orchestration tests.test_p2p_task_targeted_context -v` | PASS, 54/54 | Foreground positive/negative paths, complexity/assurance independence, C19 bounded context. |
| `python -m unittest tests.test_p2p_controlled_execution_hardening tests.test_p2p_bounded_delegation tests.test_p2p_host_executor -v` | PASS, 57/57 | C11 hardening, bounded handoff, host/executor capability-permission boundaries. |
| `python -u .p2p/system/p2p_capabilities/tests/test_checkpoint_quality_gate.py -v` | PASS, 6/6 | FW01 quality UNKNOWN/REJECTED stop and no blind resume mutation. |
| Affected broad command covering controlled execution, task state, delegation, parallel, host, AutoPilot, FW01 closure, C37, and C19 comparison | 223/227 PASS; four inherited failures | No candidate-specific broad regression; exact failure classification is in the coverage matrix. |
| `python -m compileall -q .p2p/system tests` | PASS, existing SyntaxWarning only | Python syntax/import compilation. |
| `anvien analyze --force` | PASS: 914 scanned, 165 parsed code, 0 parse failures, 38,075 nodes, 43,990 relationships | Fresh graph for candidate evidence. |
| `anvien detect-changes --repo <candidate> --scope all --json` | PASS with high-risk/unresolved analyzer gaps | Changed surface and graph limitation; not treated as authority. |
| `python scripts/doctor.py --root . --role development` | FAIL, same failures on clean canonical probe | Inherited governance drift, mechanically separated from candidate. |
| `python scripts/p2p_governance.py drift --root . --governance governance` | FAIL, same failures on clean canonical probe | Inherited governance drift and historical scoped references; not repaired. |

### Required negative paths

- No lease: PASS, actual mutation seam blocked.
- Wrong baseline: PASS, no runtime write.
- Expired/revoked lease: PASS, runtime mutation blocked.
- Outside authorized surface/scope expansion: PASS, re-plan required.
- Role name and handoff data as permission: PASS, fail closed.
- Context/path rebinding as worktree authority: PASS, fail closed.
- Candidate mutation after audit: PASS, prior audit stale/invalid.

## E2E flow

CLI permission input -> `ExecutionIntent` persisted before mutation -> existing
permission/owner/lease/baseline/worktree gates -> executor callback -> candidate
state/evidence verification -> durable C11 completion/checkpoint. The observed
output and ledger are bounded references; text alone cannot complete the task.

## Residual unverified surfaces

No residual same-invariant production surface is known. Two external evidence
limitations remain explicitly bounded:

1. Anvien cannot uniquely resolve hidden `.p2p` paths because its local registry
   has duplicate/ambiguous repository entries; direct source/runtime evidence
   is used instead.
2. Doctor/governance drift fails on the same pre-existing protected/unlocked
   files in the clean `b26189d...` probe; this candidate does not repair them.

These limitations are not silently converted to PASS and are not candidate
runtime regressions.

## Handoff

The implementation commits are complete and the candidate is ready for a fresh,
independent, read-only Supervisor review. Freeze identity must be written after
the final documentation commit; any later byte mutation invalidates that
review.
