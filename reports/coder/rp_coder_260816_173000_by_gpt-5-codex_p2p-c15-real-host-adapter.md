# Coder Report: P2P-C15 Real Host Adapter Hardening

Status: PARTIAL / NOT READY FOR REAL-HOST CERTIFICATION

## Scope

Implement the minimum fail-closed C15 adapter from `WorkerHandoff` to the
existing supported host callback seam, preserve raw and normalized receipt
provenance, unify decision/handoff plan fingerprint semantics, and verify the
official `.19 + C15` temporary candidate without promotion or release.

## Invariant Family Map

- Authority: current P2P-C15 owner request, existing C11/C12/C09 runtime
  contracts, official `.19` ZIP hash, and project protection rules.
- Runtime family: `bounded_delegation.py`, `p2p_capabilities/__init__.py`,
  C09 `p2p_host_identity_hook.py`, C11 `task_state.py`, C12
  `foreground_execution.py`, C10 `decision_trace.py` and `evidence.py`.
- Sibling surfaces checked: C15 CLI, package/doctor inventory, C09 receipt
  parser, C12 live-execution host seam, C11 task transitions, C10 trace, C13/C14
  capability/context/beginner surfaces, release packaging, and official ZIP
  lineage.
- Forbidden fallback: no private host API, simulated receipt, replayed result,
  second executor/store/ledger/router, background/parallel worker, or version
  string-only lineage fix.
- Verify matrix: successful receipt normalization, missing receipt rejection,
  parent verification gate, direct control, no-grandchild, interruption/resume,
  C10-C14 regression, candidate doctor/import, and canonical package/lineage
  gates.

## Implementation

- Added `CodexHostAdapter` to the existing C15 module.
- Adapter sends only persisted handoff plus bounded context.
- Requires `codex_official_host`, completed execution, zero host child/depth,
  fresh allow-listed C09 identity receipt, and structured worker result.
- Preserves `RAW_HOST_RECEIPT` and `NORMALIZED_C15_RECEIPT`.
- Enforces `proposal_only=true` and `output_is_evidence=false`.
- Uses one semantic C15 plan-contract fingerprint for both decision and handoff.
- Exported the adapter through the existing capability barrel.

## Verification

- PASS: `python -B -m unittest tests.test_p2p_bounded_delegation` with
  `PYTHONPATH=scripts;.p2p/system` -> `26/26`.
- PASS: `python -B scripts/p2p_c15_field_test.py --output
  .tmp/p2p-c15-adapter-field-test-20260816.json` -> `all_checks_pass=true`.
- PASS: C12/live `tests.test_p2p_live_execution` -> `16/16`.
- PASS: C11/C12/Decision Trace -> `44/44`.
- PASS: host receipt/context/capability/beginner routing -> `61/61`.
- PASS: release packaging tests -> `2/2`.
- PASS: current development doctor (`--role development`) -> `ok=true`.
- PASS: official `.19` update inventory -> `408/408` reconciled,
  `inventory_gate=PASS`, `port_status=BLOCKED_PENDING_SEMANTIC_GATES`.
- PASS: temporary candidate portable doctor and runtime compile/import.
- PRE-EXISTING/ENVIRONMENT DRIFT: the full beginner certification evaluator
  reports `harness_status=FAIL` only because its protected runtime-tree check
  is `protected_paths_unchanged=false`; isolation, canonical 8/8, schema,
  zero user-project writes, and no external integration checks remain green.
- EXPECTED BLOCK: current source package build -> `LINEAGE_REGRESSION` because
  `.15 < .19`.
- EXPECTED BLOCK: candidate package build -> missing official `.19`
  `p2p_development_control.py` for the copied development-control-aware builder.
- BLOCKED: native C15 end-to-end real-host proof. The actual host worker
  completed, but no matching C09 receipt was written to the project ledger.

## Evidence / Provenance

- Official ZIP SHA-256:
  `3a9ee51321e1f5e40e35ce73eb90727cddb571a672aa095d16d76af2feb03dd8`.
- Temporary candidate tree SHA-256:
  `f165d7007cacae274a5f3a0e88125ab9011ad50c0ef599602e18c8050ecd4060`.
- Temporary raw integration ZIP SHA-256:
  `8e87369fb3f6427a239e87823562faf22e75525ab0ec40d5e399be1329ee3172`.
- Real host agent ID:
  `01a008ca-1c74-7592-a316-4e45894027ce`.
- Project ledger check: `18` existing host identity receipts;
  `has_real_worker_receipt=false` for that agent.
- No Git repository exists; no commit/checkpoint can be created.

## Residual Unverified Surfaces

- C15 native callback from the Codex desktop `multi_agent_v1` tool into the
  project runtime.
- Official `.19` plus C15 canonical package build/lineage promotion path.
- No Logistics surface was touched.
- Post-review correction: normalized receipt now carries the C15 plan-contract
  fingerprint. Fresh targeted verification remains `26/26 PASS`; final field
  artifact `.tmp/p2p-c15-final-field-test-20260816.json` SHA-256 is
  `cc02a61f1fd5069426c71dab221eed6e64eeda32f4c799bc6e1a8a156900c412`.
