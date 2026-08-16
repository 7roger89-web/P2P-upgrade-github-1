# P2P-C15 Real Host Field Proof

## Host capability discovery

The current Codex host exposed a real `multi_agent_v1` subagent surface. One
and only one bounded subagent was created:

- Agent ID: `01a008ca-1c74-7592-a316-4e45894027ce`
- Host nickname: `Lagrange`
- Host status: `completed`
- Model override: none
- Parallel/grandchild/background execution: none

The worker was instructed to perform a read-only C15 contract and `.19` versus
`.15` content inspection. It did not access Logistics, mutate files, use
network/subprocesses, or claim parent verification/DONE.

## Real worker result

The worker returned a bounded proposal containing file hashes, contract
coherence findings, shared C10-C12 hash matches, and explicit FACT/INFERENCE/
UNKNOWN separation. It identified that official `.19` contains no
`bounded_delegation.py` entry and that `.15` is a development descendant with
additive C15 exports.

This is a real host subagent receipt and real worker result. It is not a
simulation.

## Parent verification

The parent independently verified the worker proposal against source and ZIP
content:

- shared `task_state.py`, `foreground_execution.py`, `decision_trace.py`, and
  `evidence.py` hashes match official runtime mappings;
- the full remapped comparison covered 403 official entries: 390 matched and
  13 differed;
- official `.19` has no `runtime/p2p_capabilities/bounded_delegation.py` and no
  `scripts/p2p_delegation.py`;
- current C15 controls remain green: direct control `3/3 PASS`, field A-F
  `all_checks_pass=true`;
- current field artifact:
  `.tmp/p2p-c15-hardening-field-test-20260816.json`, SHA-256
  `bf87e67561193f95496437774601127346654deebf1cf14b6662de0dcc5d6b52`.

## Boundary decision

`REAL_HOST_SUBAGENT_SURFACE = AVAILABLE_AND_PROVEN`

`LIVE_HOST_DELEGATION = BLOCKED_BY_HOST_CAPABILITY`

The second status is specific to the C15 native callback/receipt adapter: the
local C15 controller has no callable bridge that turns a `WorkerHandoff` into
the host subagent invocation and then feeds the exact receipt through the C15
parent-verification transition. The generic host subagent proof must therefore
not be relabeled as end-to-end C15 live delegation proof.

## Adapter implementation and fresh boundary result

The bounded adapter is now implemented in
`.p2p/system/p2p_capabilities/bounded_delegation.py` as `CodexHostAdapter`.
It extends the existing C15 callback seam; it does not add an executor, task
store, ledger, scheduler, or host-private API. It sends only the persisted
handoff plus the bounded execution context, requires an official
`codex_official_host` result, requires a fresh C09 identity receipt from the
existing execution ledger, and preserves both `RAW_HOST_RECEIPT` and
`NORMALIZED_C15_RECEIPT` while forcing `proposal_only=true` and
`output_is_evidence=false`.

Local adapter contract tests pass, including successful normalization and the
missing-receipt rejection path. The existing C15 field harness also remains
green. However, the supported project runtime still has no callable bridge to
the desktop `multi_agent_v1` tool. The real worker above completed outside the
adapter, and the project ledger contains 18 prior host identity receipts but
none for agent `01a008ca-1c74-7592-a316-4e45894027ce`.

Therefore:

`REAL_HOST_ADAPTER_CONTRACT = IMPLEMENTED_AND_FAIL_CLOSED`

`C15_NATIVE_REAL_HOST_END_TO_END = NOT_PROVEN`

The generic host run must not be relabeled as C15 end-to-end proof. The local
C15 foundation remains PASS, while real-host certification remains BLOCKED.
