# Supervisor Report: P2P Reasoning/Execution Fresh Current-Canonical Reconciliation

Verdict: PASS

## Metadata

- Report file: `reports/supervisor/rp_supervisor_260829_165639_by_gpt-5-codex_re-exec.md`
- Review time: `2026-08-29 16:56:39 Asia/Saigon`
- Reviewer: `gpt-5-codex`
- Repo/project: `P2P-upgrade-github-1`
- Scope reviewed: fresh-main source checkpoint and evidence closure through
  review subject `8cac8c058deebeb7a7e33d98d129f8c0baf48f92`, tree
  `a26b0d2a2f3070aae22c0163b43cb3e520b849c1`
- Claim reviewed: the already-reviewed Reasoning/Execution implementation was
  carried coherently onto the newest official canonical main, with newer
  canonical behavior preserved, and is ready for the separate Owner gate.
- Authority used: current user acceptance contract; project governance rules;
  current 01D projection SPEC; existing C34/C35 contracts and tests; current
  source, Git object identity, path/blob comparison, focused verification, and
  coder report.
- Related artifacts:
  - coder report:
    `reports/coder/rp_coder_260829_165137_by_gpt-5-codex_p2p-reasoning-execution-fresh-current-canonical-reconciliation.md`
  - evidence ledger:
    `docs/plans/2026-08-29-p2p-reasoning-execution-fresh-current-canonical-reconciliation/2026-08-29-p2p-reasoning-execution-fresh-current-canonical-reconciliation-evidence.md`
  - source checkpoint: `01336e1e180fc42ec0c3da7ab7fbb8cffd7db90a`

## Executive Summary

- Problem: the reviewed candidate was based on stale canonical `1c84bc4`,
  while official main had advanced to `82d8a976` with later 01D projection
  work.
- Decision: PASS. The exact old-base path comparison has zero overlap; only
  the reviewed 11-file Reasoning/Execution source/test delta is present, all
  9 later official-main paths are byte-identical, focused evidence passes,
  and the source preserves the required independent identity/evidence and
  permission boundaries.
- Required outcome: accepted for the separate Owner gate only. No promotion,
  push, release, deployment, or live activation is authorized by this review.

## Source-Level Clearance Notes

- `backend_contract.py:127-225, 284-503`: clear. The exact operational
  vocabulary, claim-to-capability mapping, static-versus-execution invariant,
  adapter environment/workspace identity, health/auth/freshness, execution
  evidence pointers, and normalized result are explicit and fail closed.
- `backend_execution_bridge.py:68-82, 235-320`: clear. Request fingerprints
  include target, required capabilities, claims, and reasoning-provider
  identity; result/evidence/target bindings are propagated through the
  existing bridge.
- `fake_execution_backend.py:70-90`: clear. Test-only contract normalization
  carries the same fields; it does not establish a second execution plane.
- `agent_role.py:40-44, 80-96`: clear. Role capability vocabulary reuses the
  existing certification-scope surface; role/provider/target identities stay
  separate.
- `role_bridge.py:164-173, 300-350`: clear. Existing role bridge carries
  reasoning provider, required capabilities, execution claims, observed target,
  environment, and mechanical evidence without a new router or orchestrator.
- `role_contract.py:68-83, 109-190, 304-380`: clear. Task claims are
  normalized and bound to exact capabilities; provider identity is explicit,
  separately fingerprinted, and conflicting aliases fail closed.
- `role_eligibility.py:86-96, 161-356`: clear. Target certification is
  adapter-bound; task capabilities are included; current auth, environment,
  evidence expressibility, and permission composition are fail-closed and
  non-widening.
- `role_receipt.py:101-173, 278-350`: clear. Receipt serialization and parsing
  preserve reasoning-provider identity, environment, observed target, target
  fingerprint, and execution-evidence pointers; Owner authorization fields
  remain on the existing receipt/governance surface.
- `role_verifier.py:77-356`: clear. Independent verification checks provider,
  environment, permission, backend target/fingerprint, target certification,
  mechanical pointers, remote observation for `REMOTE_PUSHED`, and the
  `STATIC_REASONING != EXECUTION_EVIDENCE` invariant.
- `tests/test_p2p_reasoning_execution_decoupling.py:190-388`: clear. The
  focused 17-test proof covers positive and negative capability claims,
  provider/target separation, observed target, mechanical evidence, remote
  observation, capability non-implication, C35 neutrality, and Owner boundary.
- `tests/test_p2p_c34_real_backend_contract.py:642-787`: clear. The existing
  C34 policy audit explicitly includes the carried consumers and the new
  focused test in its approved tracked-change boundary.

## Current-main and preservation clearance

- Fresh official remote resolve: `82d8a976381157aeece51fde33ef972496ff8ce7`;
  local `origin/main` matches; no drift was observed before or after source
  mutation and before review.
- Current-main tree: `ac2627b0a7ae1bfa8eef83992e4c76f325c0b905`.
- `git merge-base --is-ancestor 82d8a976 HEAD`: PASS.
- Old-base-to-old-candidate: 18 paths. Old-base-to-current-main: 9 paths.
  Exact overlap: 0. Production/test overlap: 0. Classification: `NONE`.
- Every one of the 9 later 01D current-main paths has an identical blob in
  the candidate (`LATER_CURRENT_MAIN_HASH_MISMATCHES=0`): project context,
  materialization, project pin, projection SPEC, four 01D plan artifacts, and
  projection test.
- Seven preservation anchors covering APKiD, AUTO01, SEC01, capability
  registry, governance/research-adoption, and external-source seams have
  `PRESERVATION_ANCHOR_MISMATCHES=0` against fresh main.
- The current 01D SPEC explicitly retains the existing registry/router and
  says projection metadata, `NOT_INSTALLED`, stale/marketing state, and
  projection readiness do not grant executable authority. Its writer source
  remains a bounded projection writer, not a router or installer.
- The candidate has no new runtime file, no MCP/ArenaAdapter surface, and no
  second registry, router, verifier, execution plane, risk engine,
  orchestrator, or truth store.

## Evidence Checked

Passed:

- Fresh remote `git ls-remote ... refs/heads/main` -> exact
  `82d8a976381157aeece51fde33ef972496ff8ce7`; freshness is current at review.
- Worktree status -> clean before review; final source/evidence checkpoint is
  committed and no implementation/test drift exists after focused testing.
- Direct focused suite -> `17 passed in 0.37s`.
- Directly affected C34/C35 preservation suite -> `94 passed, 14 skipped,
  7 warnings in 1.87s`. The pre-checkpoint allowlist failure was resolved by
  committing the new direct test; the post-checkpoint identical suite passed.
- Affected Python compile -> `COMPILE=PASS FILES=11`.
- Registry/contract parse -> `REGISTRY_JSON=PASS KEYS=3 CONTRACT_PARSE=PASS`.
- Exact carried-blob mismatch count -> `0`.
- Exact later-current-main blob mismatch count -> `0`.
- `git diff --check 82d8a976..HEAD` -> PASS.
- Source/diff inspection and focused sibling sweep -> all required boundary
  claims cleared above.

Failed:

- None in the reviewed post-checkpoint state.

Not run:

- Broad regression and the full 111-test run were intentionally not run under
  the user-defined verification ceiling because there is no material
  current-main production/test overlap.
- Anvien, Council/quorum, MCP, provider installation, live browser/database
  execution, remote-push execution, push, promotion, release, deployment, and
  activation were intentionally not run or enabled. The user explicitly
  prohibited them, and none is needed to prove this bounded reconciliation.

## Invariant Closure

- Affected invariant: provider/reasoning identity is not execution authority;
  execution authority is task-bound, target-certified, environment/surface/
  permission-aware, mechanically evidenced, and independently verified.
- Sibling surfaces checked: role spec, backend contract, backend bridge, fake
  test backend, role bridge, role contract, eligibility, receipt, verifier,
  C34 policy audit, C35 provider-neutral runtime, current 01D projection
  source/SPEC/test, and preservation anchors for AUTO01/SEC01/APKiD/seams.
- Residual unverified same-invariant surfaces: `none` within the assigned
  reconciliation lane.

## Overall Evaluation

The implementation is an exact coherent carry-forward from the reviewed
candidate onto fresh official main, not a stale-history replay or a rebuild.
The source review confirms the mechanical evidence invariant, actual observed
target binding, host/surface/environment/permission awareness, stale/marketing
fail-closed behavior, and existing Owner boundary. Current-main 01D behavior
and the named AUTO01/SEC01/APKiD/extension seams are preserved by exact blob
and source inspection. Technical PASS does not equal Owner approval.

`OWNER_GATE_REQUIRED=YES`
`CANONICAL_PROMOTED=NO`
