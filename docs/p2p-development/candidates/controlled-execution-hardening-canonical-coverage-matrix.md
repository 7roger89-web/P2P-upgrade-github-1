# Controlled Execution Hardening — Canonical Candidate Coverage Matrix

Date: 2026-08-25  
Candidate branch: `codex/p2p-controlled-execution-canonical-candidate-03`  
Canonical base: `b26189daf33afadbf6fe3eeef4f773f1373ea751`  
Implementation commits: `669b97f15f83ffe80b5d611a678e8bb2eaae7f1f`,
`3f3ad28f7acb65f782c751bea78d039ebd59b5f2`

This matrix is candidate evidence, not merge, promotion, release, or authority
approval. Existing P2P primitives remain the authority. Upstream harness code
is not part of this candidate.

| Requirement | Existing canonical primitive | Current production call-site | Evidence | Outcome | Gap |
|---|---|---|---|---|---|
| C11 durable task-state binding | `TaskStateStore`, task-plan compatibility, durable transitions and recovery | `AutoPilotLoop.__init__`, `execute_task`; `build_fw01_loop` composition | `tests/test_p2p_controlled_execution_hardening.py:107-227`; `tests/test_p2p_bounded_delegation.py:438-461`; checkpoint suite 6/6 | `MINIMAL_HARDENING_IMPLEMENTED` | None at the candidate seam. Corrupt, mismatched, restarted, and executor-exception paths fail closed. |
| PRE_CODE_CONTRACT | `ExecutionIntent` carries task, goal, baseline, affected surface, acceptance, evidence, scope and material boundaries before mutation | `ForegroundExecutionController._persist_intent`, `_mutation_gate`, `execute` | `tests/test_p2p_foreground_execution.py:110-228,286-304,344-360` | `MINIMAL_HARDENING_IMPLEMENTED` | None at the candidate seam. |
| EXECUTION AUTHORITY; `ROLE != AUTHORITY` | Existing explicit permission binding and owner gate; role/handoff fields are data only | `ForegroundExecutionController._assert_write_binding`; CLI `--permissions` projection | `tests/test_p2p_foreground_execution.py:230-263`; `tests/test_p2p_host_executor.py:118-131` | `MINIMAL_HARDENING_IMPLEMENTED` | None. Role identity alone cannot create WRITE, AUDIT, or COORDINATE authority. |
| FW06 WRITE LEASE | Existing lease/permission gate is reused at the actual runtime write seam | `ForegroundExecutionController._acquire_write_lease`, `_assert_live_write_lease`, `_assert_write_binding`, `_mutation_gate` | `tests/test_p2p_foreground_execution.py:265-343`; `tests/test_p2p_controlled_execution_hardening.py:209-227` | `MINIMAL_HARDENING_IMPLEMENTED` | None for no lease, wrong baseline, expired/revoked lease, outside surface, and scope expansion. |
| `SCOPE_EXPANSION_REQUIRES_REPLAN` | Existing bounded scope and re-plan stop contract | `ForegroundExecutionController._validate_scope` | `tests/test_p2p_foreground_execution.py:344-360` | `MINIMAL_HARDENING_IMPLEMENTED` | Silent widening remains rejected. |
| FROZEN CANDIDATE / stale audit | Candidate state and audit/evidence fingerprint binding; successor mutation invalidates prior audit | `ForegroundExecutionController._candidate_state`, verification and resume paths | `tests/test_p2p_foreground_execution.py:466-516`; `tests/test_p2p_bounded_delegation.py:177-209` | `MINIMAL_HARDENING_IMPLEMENTED` | None at the runtime seam. Exact final candidate identity is bound separately in the freeze record. |
| COMPLEXITY × ASSURANCE RISK independence | Existing adaptive orchestration policy keeps effort/complexity independent from assurance/risk | `adaptive_orchestration` policy evaluation | `tests/test_p2p_adaptive_orchestration.py:60-77`; 54-test focused run | `ALREADY_PROVEN` | None. Provider/model names remain noncanonical data. |
| Task-scoped context | Existing C19 bounded context retrieval/materialization | `retrieve_task_context` and task-context test fixtures | `tests/test_p2p_task_targeted_context.py:191-214`; 54-test focused run | `ALREADY_PROVEN` | None. Parent transcript/history is not the worker contract. |
| STRUCTURED HANDOFF; `HANDOFF != AUTHORIZATION` | Existing bounded delegation and handoff fingerprints carry references/evidence, not permission | `BoundedDelegation` and existing delegation decision path | `tests/test_p2p_bounded_delegation.py:177-209,395-461`; role/handoff negative test above | `ALREADY_PROVEN` | None. No new handoff or permission engine added. |
| WORKTREE / EXECUTOR BINDING | Workspace snapshot, exact task/baseline/lease composition, and executor callback binding | `ForegroundExecutionController._workspace_snapshot`, `_assert_write_binding`, `execute` | `tests/test_p2p_foreground_execution.py:274-304`; `test_context_or_path_rebinding_cannot_replace_worktree_binding` | `MINIMAL_HARDENING_IMPLEMENTED` | None in production seam. Context isolation is not treated as filesystem isolation. |
| Termination / done conditions | Existing C11 completion evidence plus FW01 quality checkpoint; quality UNKNOWN/REJECTED is blocked | `Fw01Loop.step`, `TaskStateStore.complete` | `test_checkpoint_quality_gate.py:327-554` (6/6); 54+57 focused tests | `ALREADY_PROVEN` | None. Textual completion cannot bypass current evidence. |
| One P2P control plane / one loop | Existing AutoPilot/FW01 loop and bounded delegation; no second orchestrator/task store/router | `AutoPilotLoop`, `Fw01Loop`, foreground controller | `tests/test_p2p_foreground_execution.py` structural boundary test; 227-test affected run | `ALREADY_PROVEN` | None. Upstream harness was not vendored and no second loop was created. |
| Canonical FW01 quality-verdict repair | Canonical strict shape/type/literal-boolean validation | `p2p_fw01_loop._quality_verdict_shape_is_valid` and checkpoint gate | `git diff b26189d...` shows repair preserved; checkpoint suite 6/6 | `ALREADY_PROVEN` | None; no stale feature-branch repair overwrote canonical logic. |
| Independent Anvien symbol/impact evidence | Anvien refreshed graph; hidden runtime paths are not uniquely resolvable in duplicate registry entries | `anvien analyze --force`, `anvien detect-changes --repo <candidate>` | Scan: 914 files, 165 parsed code, 0 parse failures, 38,075 nodes, 43,990 relationships; detect-changes reports high-risk touched files | `BLOCKED_WITH_EXACT_GAP` | Tooling registry has duplicate/ambiguous repo entries and cannot supply unique file-detail/impact for hidden `.p2p` paths. Direct Git/source/runtime evidence is used; no graph result is treated as authority. |
| Development doctor / governance drift | Existing doctor and governance drift validator | `scripts/doctor.py --root . --role development`; `scripts/p2p_governance.py drift --root . --governance governance` | Candidate and clean `b26189d...` probe report the same inherited failures | `BLOCKED_WITH_EXACT_GAP` | Inherited governance drift: `notes_decisions_log_20260824.md`, `scripts/p2p_orientation.py`, and protected-file changes. Not repaired or attributed to this candidate. |

## Candidate-specific regression classification

The broad affected command ran 227 tests: 223 passed and four historical
failures reproduced. The same four were reproduced on a clean detached
`b26189daf33afadbf6fe3eeef4f773f1373ea751` probe with an empty `.tmp` workspace
directory so the lineage checks reached their subprocess boundary:

| Historical failure | Candidate | Clean canonical probe | Classification |
|---|---|---|---|
| `test_t18_c09_blocked_identity_state_remains_unknown` | missing `.p2p/state/project-status.json` | same missing file | `INHERITED_FIXTURE_RELATED` |
| `test_fill_script_never_calls_rev_parse_head` | missing `.tmp/fw01_fill_report.py` | same missing file | `INHERITED_FIXTURE_RELATED` |
| `test_lineage_file_referencing_ancestor_is_accepted` | exit 9009, `python3` unavailable | exit 9009, `python3` unavailable | `INHERITED_ENVIRONMENTAL` |
| `test_lineage_file_referencing_head_is_rejected` | no `SELF_REFERENCE_GUARD` because `python3` is unavailable | same | `INHERITED_ENVIRONMENTAL` |

No candidate-introduced broad-suite failure was observed. No fixture was
fabricated and no test was weakened.
