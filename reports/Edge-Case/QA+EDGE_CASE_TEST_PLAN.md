# P2P-GOVREC01 Canonical Edge-Case Test Plan

Status: `INDEX_ONLY / LIVE_EVIDENCE_NOT_RUN`
Date: `2026-08-26`
Scope: current promoted-source governance reconciliation at `origin/main`
candidate `2a71410afd1b29651016ef57a5d2da38938c3f68`

## Authority boundary

This is the canonical index for the failure families that must be exercised
before any current-lineage Council or host-certification claim is accepted. It
is an index over existing P2P contracts, tests, and reports; it is not a new
test framework, runner, quorum, router, or certification system.

The following distinction is mandatory throughout this plan:

```text
HISTORICAL_SINGLE_HOST_LIVE_COUNCIL_8_OF_8 = TRUE
CURRENT_LINEAGE_FULL_COUNCIL_LIVE_PROVEN = FALSE
CURRENT_LINEAGE_FULL_COUNCIL_STATUS = NOT_PROVEN
```

The retained C36 single-host evidence is historical reference only. C43 is a
bounded framework/smoke surface and cannot upgrade that historical fact into
current full-Council evidence. Configured profiles, a denominator of 8, a
configured quorum of 8/8, logs, and repeated reports are not live evidence.

## Evidence states and live-slot rule

Every `LIVE-*` slot below is unfilled on this candidate. A slot may become
`VERIFIED` only from fresh execution against the exact current candidate head,
with the relevant output, identity/provenance, timestamp, and independent
verification recorded in the existing evidence/ledger surfaces. Until then it
remains `UNKNOWN` or `NOT_PROVEN`; no slot may be closed from configuration or
historical wording.

| State | Meaning |
|---|---|
| `UNKNOWN` | The failure path has not been executed with sufficient current evidence. |
| `NOT_PROVEN` | The contract or historical boundary is known, but the requested current live claim is not established. |
| `VERIFIED` | Fresh exact-head execution and independent evidence satisfy the existing contract. |
| `CONTRADICTED` | Fresh evidence conflicts; preserve both sides and stop the claim. |

## Canonical failure-family index

| ID | Failure family | Required perturbation | Existing contract / tests / report seam | Expected fail-closed result | Live evidence slot | Current status |
|---|---|---|---|---|---|---|
| `EC-01` | Retry / no-progress | Repeat the same governed operation after an unchanged failure; combine retry with a stale request or unknown mutation outcome. | `P2P-CAPABILITY-EXECUTION-EVIDENCE-SPEC.md` (bounded no-progress, no infinite retry); `tests/test_p2p_capability_foundation.py::test_no_progress_is_diagnostic_not_infinite_retry`; `tests/test_p2p_secure_onboarding.py::test_ho49_preflight_is_idempotent_and_safe_to_retry`. | No blind retry, no infinite loop, and no PASS without new evidence. Return a bounded diagnostic such as `INCOMPLETE`, `UNKNOWN`, or the existing failure result. | `LIVE-EC-RETRY-01`: exact-head repeated-attempt receipt with mutation certainty and unchanged-failure proof. | `UNKNOWN` |
| `EC-02` | Duplicate / replay / out-of-order event | Deliver the same task/event/identity payload twice, then deliver an older event after a newer one. | `tests/test_p2p_task_state.py::test_t1_unique_task_ids_fail_closed`; `tests/test_p2p_c43_framework_reconciliation.py::test_duplicate_capability_id_fails_closed`; `tests/test_p2p_host_identity_receipt.py::test_f_duplicate_payload_is_deterministic`; decision-trace contradiction/supersession contract. | Reject duplicate identity or preserve idempotent state; never double-apply, overwrite newer state with stale replay, or create a second canonical identity. | `LIVE-EC-DUPLICATE-01`: duplicate and out-of-order replay receipt with before/after state hashes. | `UNKNOWN` |
| `EC-03` | Stale state / stale evidence / stale context | Resume or retry with an old project fingerprint, old evidence pointer, old source hash, or stale permission/context snapshot. | `tests/test_p2p_task_targeted_context.py::test_cr4_stale_map_fails_closed`; `tests/test_p2p_task_targeted_context.py::test_pointer_resolves_and_stale_binding_is_rejected`; `tests/test_p2p_task_state.py::test_t7_stale_evidence_cannot_complete_task`; host executor stale-request tests. | Reject before mutation and surface `STALE`, `UNKNOWN`, or the existing explicit reason. Never silently refresh or treat an old receipt as current. | `LIVE-EC-STALE-01`: stale-input rejection receipt bound to exact current candidate and input fingerprint. | `UNKNOWN` |
| `EC-04` | Partial output / partial apply | Interrupt after a helper or host operation has emitted partial output, or after possible mutation but before acknowledgement/persistence. | `tests/test_p2p_host_executor.py::test_hn08_possible_mutation_unknown_requires_recheck_without_retry`; `tests/test_p2p_host_skill_projection.py::test_28_blocked_plans_never_leak_partial_file_descriptors`; `tests/test_p2p_c43_framework_reconciliation.py::test_malformed_record_does_not_raise_uncontrolled_exception`. | Do not claim success from partial output. Preserve `UNKNOWN`/`PARTIAL`, require recheck or rollback through existing safeguards, and avoid a blind retry. | `LIVE-EC-PARTIAL-01`: partial-output and mutation-uncertainty receipt with final state comparison. | `UNKNOWN` |
| `EC-05` | Quorum / Council boundary | Remove one canonical role, substitute an optional role, or present configured 8/8 without eight fresh exact-head role receipts; compare historical C36 and current candidate. | `docs/SPEC/P2P-CAPABILITY-FOUNDATION-ARCHITECTURE-SPEC.md`; `docs/SPEC/P2P-DECISION-TRACE-SPEC.md`; `tests/test_p2p_workflow.py::test_explicit_full_quorum_is_not_lowered`; `tests/test_p2p_capability_foundation.py::test_cf19_full_quorum_is_always_eight_of_eight`; C36 historical evidence and C43 bounded smoke. | Full Council remains `NOT_PROVEN`; denominator remains 8; missing/optional/substituted roles fail closed. Never upgrade current proof from history, profiles, config, or C43. | `LIVE-EC-QUORUM-01`: eight distinct canonical identity receipts plus aggregate/quorum result, all bound to exact current head and independent verification. | `NOT_PROVEN` |
| `EC-06` | Host failure / unavailable identity | Fail the host adapter, remove identity evidence, return malformed helper output, or make the selected host unavailable before and after a possible mutation. | `tests/test_p2p_host_executor.py::test_hn07_host_unavailable_before_mutation_is_recoverable`; `tests/test_p2p_host_executor.py::test_hn05_identity_required_without_evidence_blocks`; `tests/test_p2p_host_selection.py::test_hs08_identity_evidence_required_rejects`; `tests/test_p2p_host_identity_receipt.py::test_unknown_host_agent_type_fails_closed_without_a_receipt`. | Block or return a bounded recoverable failure; do not substitute a host, identity, provider, or success state without explicit authority and evidence. | `LIVE-EC-HOST-FAILURE-01`: host failure, identity absence, and recovery/recheck receipt. | `UNKNOWN` |
| `EC-07` | Resume / recovery | Resume from a checkpoint after reconnect or handoff with changed project fingerprint, stale checkpoint, or missing evidence; verify that the prior task remains bounded. | `tests/test_p2p_task_state.py::test_revision_checkpoint_resume_and_handoff_preserve_provenance`; `tests/test_p2p_task_state.py::test_t11_interrupted_active_task_never_becomes_done`; `tests/test_p2p_task_state.py::test_t12_missing_checkpoint_is_unknown`; `tests/test_p2p_context_delivery.py` interrupted-resume coverage. | Resume only from a valid authoritative checkpoint with matching provenance. Changed or missing state remains `UNKNOWN`/requires recheck; no auto-start or silent completion. | `LIVE-EC-RESUME-01`: process restart/reconnect receipt with checkpoint, fingerprint, and post-resume state hash. | `UNKNOWN` |
| `EC-08` | Process interruption / crash recovery | Terminate between lock, write, projection, sync, acknowledgement, and release; then restart and inspect durable state and lock ownership. | `tests/test_p2p_task_state.py::test_store_is_atomic_durable_and_fail_closed`; `tests/test_p2p_task_state.py::test_t11_interrupted_active_task_never_becomes_done`; `tests/test_p2p_task_state.py::test_t12_missing_checkpoint_is_unknown`; existing lock/recovery contracts. | No half-applied state may become `DONE` or PASS. Recover deterministically, preserve audit locality, or stop with `UNKNOWN`/`PARTIAL`; do not leak a stale lock or duplicate the operation. | `LIVE-EC-INTERRUPTION-01`: forced interruption point, restart receipt, lock/state reconciliation, and independent verification. | `UNKNOWN` |

## Compound perturbation matrix

The live runs must include both human-chaos and system-chaos combinations,
not only isolated malformed inputs:

| Axis | Minimum compound case | Invariant under test |
|---|---|---|
| Timing | Retry while reconnecting and while a stale store still exposes an action. | No blind retry; stale state cannot arm a protected action. |
| Ordering | Duplicate relay after local apply but before acknowledgement, followed by an older replay. | Idempotency and monotonic replay; no double apply. |
| Stale state | Revoke identity/permission while a protected operation remains mounted, then resume. | Permission and evidence are revalidated before mutation. |
| Isolation/auth | Use a valid receipt for the wrong host, project, scope, or canonical role. | Scope/identity binding fails closed; no cross-boundary authority. |
| Crash/recovery | Interrupt between lock acquisition and durable acknowledgement, then retry. | Atomic/recoverable state; no silent partial success or duplicate operation. |

## Closure rule

This index is complete as a map, not as live certification. The current
candidate remains `CURRENT_LINEAGE_FULL_COUNCIL_LIVE_PROVEN=FALSE` until
`LIVE-EC-QUORUM-01` and the relevant host/recovery slots have fresh evidence.
No provider, Manus, Council execution, promotion, release, deployment, or
remote write is authorized by this document.

