# P2P Reasoning/Execution Fresh Current-Canonical Reconciliation Evidence Ledger

## Metadata

- Date: `2026-08-29`
- Plan: `docs/plans/2026-08-29-p2p-reasoning-execution-fresh-current-canonical-reconciliation/2026-08-29-p2p-reasoning-execution-fresh-current-canonical-reconciliation-plan.md`
- Evidence: `docs/plans/2026-08-29-p2p-reasoning-execution-fresh-current-canonical-reconciliation/2026-08-29-p2p-reasoning-execution-fresh-current-canonical-reconciliation-evidence.md`
- Benchmark: `docs/plans/2026-08-29-p2p-reasoning-execution-fresh-current-canonical-reconciliation/2026-08-29-p2p-reasoning-execution-fresh-current-canonical-reconciliation-benchmark.md`
- Actual status: `docs/plans/2026-08-29-p2p-reasoning-execution-fresh-current-canonical-reconciliation/2026-08-29-p2p-reasoning-execution-fresh-current-canonical-reconciliation-actual-status.md`

## Evidence Rules

This ledger binds claims to current Git/source reality. Prior Reasoning/Execution
evidence is reusable only for unchanged protected inputs. No Anvien was run
because the user explicitly prohibited it; exact Git path sets, source
inspection, focused behavior tests, compile/parse, and diff checks are used.

### Evidence ID Naming

Evidence IDs use `E<phase>-<item>-<kind><n>` and remain stable across the four
companion files.

## E0 - P0 Evidence

Matching plan item(s): `P0-A`

- `E0-P0A-REMOTE1`: fresh direct `git ls-remote` against the official URL
  returned `82d8a976381157aeece51fde33ef972496ff8ce7 refs/heads/main` before
  mutation.
- `E0-P0A-CURRENT1`: isolated clone fetched and resolved official `main` to
  SHA `82d8a976381157aeece51fde33ef972496ff8ce7`, tree
  `ac2627b0a7ae1bfa8eef83992e4c76f325c0b905`, with a clean worktree before
  candidate creation.
- `E0-P0A-OLD1`: reviewed candidate resolved to SHA
  `e1410fa28fab5b9c3d0d9f1c37ef68a20165bcef`, tree
  `5cccc26ab65ae525a43ee9b41557cf47f0cbf3db`, based on old base
  `1c84bc41421dcbe502d40b71fead5022231d0541` / tree
  `a11a44b676401d8a424db8ed05632c8d22952d26`.
- `E0-P0A-OVERLAP1`: old-base-to-old-candidate has 18 changed paths;
  old-base-to-current-main has 9 changed paths; exact path intersection is
  empty.
- `E0-P0A-OVERLAP2`: production/test intersection is empty. Classification is
  `NONE`; there is no documentation-only, compatible-code, or material
  semantic overlap to resolve.
- `E0-P0A-LATE1`: current main's later delta is the 01D projection contract:
  project context, project materialization, project pin, projection SPEC,
  projection plan/evidence/benchmark/status, and projection test. These paths
  are preserve-only and are not part of the Reasoning/Execution port.
- `E0-P0A-SPEC1`: the relevant capability foundation, execution/evidence,
  provider abstraction, routing/readiness, trust-data, and current 01D
  projection SPEC surfaces were read for the authority boundary.
- `E0-P0A-BOUNDARY1`: supplied root is not a Git checkout; the protected
  canonical runtime remains a separate dirty worktree. Neither was repaired or
  mutated. Candidate work stays in the isolated `.tmp` clone/branch.
- `E0-P0A-TOOL1`: Anvien was not run because the user explicitly prohibited it;
  exact Git/source evidence is the documented substitute.

## E1 - P1 Evidence

Matching plan item(s): `P1-A`, `P1-B`

- `E1-P1A-SRC1`: the exact reviewed 11-file delta was applied with
  `git apply --3way` from old candidate `e1410fa` onto the fresh-main branch.
  The source checkpoint is `01336e1e180fc42ec0c3da7ab7fbb8cffd7db90a`, tree
  `f3940503a4d9da4bb9d950bc8177384bdd4a94c6`, parent
  `02b2806875a3a83a1bb7af274dc2c571674391ae`. All 11 carried blobs match the
  old candidate, and all 9 later current-main blobs match `82d8a976`.
  No current-main path overlaps the carried delta.
- `E1-P1A-TEST1`: the direct suite
  `tests/test_p2p_reasoning_execution_decoupling.py` passed `17 passed` in
  `0.37s` on the fresh-main lineage.
- `E1-P1A-DIFF1`: the source checkpoint has exactly the scoped 11 source/test
  paths, `git diff --cached --check` passed before commit, and the committed
  source slice has no whitespace error against fresh main.
- `E1-P1B-TEST1`: directly affected preservation command
  `tests/test_p2p_c34_real_backend_contract.py tests/test_p2p_c35_provider_neutral_runtime.py`
  passed `94 passed, 14 skipped, 7 warnings` in `1.87s`. The first pre-checkpoint
  run exposed only the expected C34 tracked-change allowlist for the not-yet-
  committed new direct test (`93 passed, 14 skipped, 1 failed`); the identical
  suite passed after the source/test checkpoint. No behavior failure remains.
- `E1-P1B-COMPILE1`: no-write Python compilation passed for all 11 affected
  source/test Python files: `COMPILE=PASS FILES=11`.
- `E1-P1B-PARSE1`: `capabilities.json` parsed as a non-empty object with 3
  top-level keys; the imported backend contract recognized the bounded claim
  mapping and mechanical evidence pointer shape: `REGISTRY_JSON=PASS`
  and `CONTRACT_PARSE=PASS`.
- `E1-P1B-DIFF1`: exact Git verification reports 18 old-candidate paths, 9
  later current-main paths, zero shared paths, zero carried-blob mismatches,
  zero current-main-blob mismatches, `CURRENT_MAIN_ANCESTOR=TRUE`, and
  `DIFF_CHECK_CURRENT_MAIN=PASS`. A fresh remote resolve after the checkpoint
  still returned `82d8a976381157aeece51fde33ef972496ff8ce7`; no drift occurred.
- `E1-P1B-REPORT1`: current-lineage coder report is recorded at
  `reports/coder/rp_coder_260829_165137_by_gpt-5-codex_p2p-reasoning-execution-fresh-current-canonical-reconciliation.md`.
- `E1-P1B-IDENTITY1`: the candidate remains directly descended from fresh
  official main `82d8a976381157aeece51fde33ef972496ff8ce7` / tree
  `ac2627b0a7ae1bfa8eef83992e4c76f325c0b905`; source checkpoint ancestry and
  tree are recorded in `E1-P1A-SRC1`.

## E2 - P2 Evidence

Matching plan item(s): `P2-A`

- `E2-P2A-SUPERVISOR1`: pending one independent focused Supervisor report.

## Closure Evidence

- `E3-PNA-CLOSE1`: pending final candidate identity, clean status, Owner-gate
  stop, and `CANONICAL_PROMOTED=NO` confirmation.
