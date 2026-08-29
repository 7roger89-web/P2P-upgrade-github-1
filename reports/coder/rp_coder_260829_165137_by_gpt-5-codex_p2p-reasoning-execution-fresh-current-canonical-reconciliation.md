# Coder Report — P2P Reasoning/Execution Fresh Current-Canonical Reconciliation

Date: 2026-08-29 16:51 Asia/Saigon
Scope: carry the already-reviewed Reasoning/Execution delta onto fresh
official `main`
Lane: STANDARD / minimum sufficient work
Status: READY FOR FOCUSED SUPERVISOR REVIEW

## Git boundary

- Official remote `refs/heads/main`: `82d8a976381157aeece51fde33ef972496ff8ce7`
- Official-main tree: `ac2627b0a7ae1bfa8eef83992e4c76f325c0b905`
- Old base: `1c84bc41421dcbe502d40b71fead5022231d0541`
- Reviewed source candidate: `e1410fa28fab5b9c3d0d9f1c37ef68a20165bcef`
  / tree `5cccc26ab65ae525a43ee9b41557cf47f0cbf3db`
- New source checkpoint: `01336e1e180fc42ec0c3da7ab7fbb8cffd7db90a`
  / tree `f3940503a4d9da4bb9d950bc8177384bdd4a94c6`
- New source checkpoint parent: `02b2806875a3a83a1bb7af274dc2c571674391ae`
- Working branch: `p2p/reasoning-execution-current-canonical-reconciled-20260829-r2`
- Worktree: repo-local isolated `.tmp/p2p-sec01-current-canonical`

The supplied workspace root is not a Git checkout. The protected canonical
worktree and the old reviewed candidate were not repaired, reset, or modified.
No push, promotion, release, deployment, or live activation was performed.

## Invariant Family Map

| Family | SSOT / authority | Sibling runtime surfaces | Forbidden fallback | Verification |
|---|---|---|---|---|
| Operational execution capability and evidence | `Docs/SPEC/P2P-CAPABILITY-*-SPEC.md`; existing backend/role contracts | `backend_contract.py`, `backend_execution_bridge.py`, `fake_execution_backend.py`, `role_bridge.py`, `role_contract.py`, `role_eligibility.py`, `role_receipt.py`, `role_verifier.py` | static reasoning, prose, marketing/stale capability, adjacent capability implication | direct 17 tests; C34/C35 preservation; compile/contract parse |
| Target and provider identity separation | existing role contract/receipt/verifier authority | `agent_role.py`, role contract/bridge/receipt/verifier | provider identity standing in for execution target; requested target standing in for observed target | direct binding/attestation tests; C35 target identity tests |
| Host/surface/environment/permission boundary | existing C34/C35 backend identity, health, environment/workspace and permission contracts | backend identity/result, eligibility, request receipt, C35 certification/governance | historical certification, unknown auth, stale source, or permission claim widening authority | source inspection; direct/C34/C35 environment, permission, stale and target tests |
| Current canonical preservation | fresh official `main`; current 01D projection contract | `project_context.py`, `project_materialization.py`, `project_pin.py`, projection SPEC/test and four 01D plan artifacts | rollback or overwrite of later current-main work | exact path intersection and all 9 current-main blob comparisons |
| Control-plane and Owner boundary | existing registry/router/verifier/runtime and project governance | registry, eligibility, verifier, C35 runtime, Owner/release records | second registry/router/verifier/orchestrator/risk/truth store; inferred Owner approval | path inventory, source inspection, focused architecture/governance tests |

## Work performed

1. Freshly resolved the official remote twice; it remained `82d8a976` before
   source mutation and after the source checkpoint.
2. Compared `1c84bc4 -> e1410fa` against `1c84bc4 -> 82d8a976`:
   18 old-candidate paths versus 9 later current-main paths, exact intersection
   zero, production/test intersection zero. Classification: `NONE`.
3. Applied only the 11 reviewed Reasoning/Execution source/test paths with
   three-way Git application. No current-main 01D file was touched.
4. Preserved the normalized operational vocabulary, claim-to-capability
   mechanical mapping, target certification/eligibility binding, separate
   reasoning provider identity, observed-target attestation, host/surface/
   environment/permission checks, fail-closed stale/unknown handling,
   provider-neutral C35 runtime, and Owner/release boundary.
5. Preserved the newer 01D projection contract and all nine exact current-main
   paths byte-for-byte. No duplicate control plane or MCP surface was added.

## Sibling surfaces checked

- `agent_role.py`: role identity and permission ceiling remain separate from
  task, provider, harness, and execution target.
- `backend_contract.py`: operational vocabulary, execution-claim map,
  mechanical evidence pointers, adapter environment/workspace identity,
  health/auth/freshness, execution result, and mutation-surface contract.
- `backend_execution_bridge.py`: contract fingerprint, target/capability/
  claim binding, result and evidence propagation, and permission boundary.
- `fake_execution_backend.py`: test-only backend follows the same target and
  evidence shape; it is not a second runtime.
- `role_bridge.py` / `role_contract.py`: task-to-role and task-to-certified
  target binding; `reasoning_provider_id` remains distinct.
- `role_eligibility.py`: capability-scoped certification, actual environment
  compatibility, current auth, evidence expressibility, and never-widen
  permission composition fail closed.
- `role_receipt.py` / `role_verifier.py`: observed execution target and
  mechanical evidence are verified independently of static reasoning.
- C34/C35 tests: existing environment, permission, stale/auth, target
  attestation, provider-neutral, registry/router, quorum and Owner-gate
  boundaries remain exercised.

## Legacy fallback status

No legacy fallback was introduced or relied on for the carried semantics.
Unknown/stale/marketing capability claims do not grant execution authority.
The existing C34 compatibility behavior remains bounded and provider-neutral;
no new ontology, router, registry, verifier, risk engine, orchestrator, or
truth store was created.

## Stale tests/helpers/plans

The pre-checkpoint C34 policy audit correctly rejected the uncommitted new
direct test as an unapproved tracked change. After the required source/test
checkpoint, the same preservation command passed. No stale helper or plan
contract was changed to hide a behavior failure. Reconciliation evidence and
this report are audit-only artifacts.

## Files changed in the source checkpoint

- `.p2p/system/p2p_capabilities/agent_role.py`
- `.p2p/system/p2p_capabilities/backend_contract.py`
- `.p2p/system/p2p_capabilities/backend_execution_bridge.py`
- `.p2p/system/p2p_capabilities/fake_execution_backend.py`
- `.p2p/system/p2p_capabilities/role_bridge.py`
- `.p2p/system/p2p_capabilities/role_contract.py`
- `.p2p/system/p2p_capabilities/role_eligibility.py`
- `.p2p/system/p2p_capabilities/role_receipt.py`
- `.p2p/system/p2p_capabilities/role_verifier.py`
- `tests/test_p2p_c34_real_backend_contract.py`
- `tests/test_p2p_reasoning_execution_decoupling.py`

The nine later official-main paths were verified unchanged and remain
preserve-only:

- `.p2p/system/p2p_capabilities/project_context.py`
- `.p2p/system/p2p_capabilities/project_materialization.py`
- `.p2p/system/p2p_capabilities/project_pin.py`
- `docs/SPEC/P2P-PROJECTION-ONLY-PROJECT-IDENTITY-SPEC.md`
- the four `docs/plans/2026-08-29-p2p-projection-contract-01d-fresh-main-reconciliation/` artifacts
- `tests/test_p2p_projection_contract.py`

## Verify outputs

- `[PASS]` Direct behavior: `py -3.12 -m pytest -q tests/test_p2p_reasoning_execution_decoupling.py`
  -> `17 passed in 0.37s`.
- `[PASS]` Preservation: `py -3.12 -m pytest -q tests/test_p2p_c34_real_backend_contract.py tests/test_p2p_c35_provider_neutral_runtime.py`
  -> `94 passed, 14 skipped, 7 warnings in 1.87s`.
- `[PASS]` Compile: no-write Python compilation of 11 affected files
  -> `COMPILE=PASS FILES=11`.
- `[PASS]` Registry/contract parse: JSON and bounded claim/evidence helpers
  -> `REGISTRY_JSON=PASS KEYS=3 CONTRACT_PARSE=PASS`.
- `[PASS]` Git/source boundary: exact old/new path intersection zero;
  carried blob mismatches zero; current-main blob mismatches zero; current
  main is an ancestor; `git diff --check` passes.
- `[PASS]` Fresh authority after checkpoint: remote still
  `82d8a976381157aeece51fde33ef972496ff8ce7`.

## E2E Verification

  `[PASS]` Compiled: affected Python compile -> all 11 files pass.
  `[PASS]` Runtime: not applicable; this is a bounded contract/runtime-source
  reconciliation with no live external execution.
  `[PASS]` Happy path: explicit certified target with matching mechanical
  evidence -> direct Reasoning/Execution suite passes.
  `[PASS]` Edge case: missing/incorrect evidence, target mismatch, stale/auth
  uncertainty, capability mismatch, and permission widening -> focused direct
  and C34/C35 preservation suites pass.

Residual unverified surfaces: `none` within the assigned reconciliation lane.
Live browser/database/remote execution and provider activation are explicitly
out of scope and were not represented as proven.

## Result and handoff

Technical result: PASS for the scoped fresh-current-canonical reconciliation.
`MCP_REQUIRED_NOW=NO`. `OWNER_GATE_REQUIRED=YES`. `CANONICAL_PROMOTED=NO`.
One independent Supervisor review is required before closure at the Owner gate.
