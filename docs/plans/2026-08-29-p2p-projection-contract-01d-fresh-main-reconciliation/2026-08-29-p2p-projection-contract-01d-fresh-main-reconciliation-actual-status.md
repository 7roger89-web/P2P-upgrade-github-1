# P2P Projection Contract 01D Fresh-Main Reconciliation Actual Status

Title: P2P Projection Contract 01D Fresh-Main Reconciliation
Date: 2026-08-29
Status: P1-A Complete / P1-B Pending
Companion plan: `docs/plans/2026-08-29-p2p-projection-contract-01d-fresh-main-reconciliation/2026-08-29-p2p-projection-contract-01d-fresh-main-reconciliation-plan.md`
Companion evidence: `docs/plans/2026-08-29-p2p-projection-contract-01d-fresh-main-reconciliation/2026-08-29-p2p-projection-contract-01d-fresh-main-reconciliation-evidence.md`
Companion benchmark: `docs/plans/2026-08-29-p2p-projection-contract-01d-fresh-main-reconciliation/2026-08-29-p2p-projection-contract-01d-fresh-main-reconciliation-benchmark.md`

## Purpose

This is the P0 current-state decision before implementation. The workspace is
the isolated `01d-reconcile-20260829` clone. Owner checkout, old 01C
workspace, Thiên Hạ repositories, and unrelated worktrees are preserve-only.

## Freshness / Refresh Rules

Fresh remote fetch and exact status refresh are required before reconciliation,
before freeze, immediately after Supervisor PASS, and after promotion.

## Scope

Target scope:

- v1/v2 project pin and mode-aware project readiness;
- bounded projection materializer;
- projection-only SPEC and focused tests;
- exact current-main reconciliation and FF promotion gates.

Out of scope:

- SEC01 redesign, provider activation, UI/DB/runtime work, Thiên Hạ, Owner
  state, old 01C mutation, broad unrelated tests, and post-promotion work.

## Relationship / Impact Evidence

Anvien was invoked after `anvien --help` and `anvien analyze --help`, but
`anvien analyze --force` failed while writing the isolated `.anvien` temporary
index: `relations.csv: There is not enough space on the disk`. No graph
relationship count is claimed. Direct Git source/diff/import evidence is used
as the fallback and this limitation remains explicit.

| Unit / File / Surface | File Detail Evidence | Related File Count | Relationship Summary | Impact Note |
|-----------------------|----------------------|--------------------|----------------------|-------------|
| `.p2p/system/p2p_capabilities/project_pin.py` | `E0-P0A-ANV1` | UNKNOWN (Anvien unavailable) | Existing v1 pin validator; old reviewed 01C adds v2 mode/binding branch | high scope warning; edit only reviewed seam |
| `.p2p/system/p2p_capabilities/project_context.py` | `E0-P0A-ANV1` | UNKNOWN (Anvien unavailable) | Existing context readiness gate; old reviewed 01C adds mode dispatch | medium scope warning; preserve v1 path |
| `.p2p/system/p2p_capabilities/project_materialization.py` | `E0-P0A-SRC5` | missing | No current-main file; old reviewed 01C provides one bounded writer | high scope warning; add only bounded writer |
| `.p2p/system/p2p_capabilities/host_projection.py` | `E0-P0A-SRC4` | direct inspected | Existing pure plan surface unchanged after base | preserve-only |
| SEC01 capability/security surfaces | `E0-P0A-INT1..E0-P0A-INT3` | direct inspected | Post-base implementation touches registry/model/orchestration and tests | preserve-only; compatible adjacent |
| Projection SPEC/tests | `E0-P0A-SRC5..E0-P0A-SRC6` | missing on fresh main | Old 01C has reviewed contract/test, current main does not | add in P1-B |

## Current Status Matrix

| Unit | Current State | Required State | Status | Relationship Count | Evidence | Next Plan Decision |
|------|---------------|----------------|--------|--------------------|----------|--------------------|
| Fresh remote/main | `1c84bc41421dcbe502d40b71fead5022231d0541`, tree `a11a44b676401d8a424db8ed05632c8d22952d26` | Fresh directly fetched authority | correct | N/A | `E0-P0A-REMOTE1..E0-P0A-REMOTE3` | preserve base |
| Post-base SEC01 commits | 3 commits after `bc686845...` | All preserved in new candidate | correct/adjacent | N/A | `E0-P0A-INT1..E0-P0A-INT3` | inspect-only |
| `project_pin.py` | reviewed v2 branch reconciled onto fresh main; source blob equals reviewed 01C | v1 preserved plus v2 closed modes, pending behavior tests | partial | UNKNOWN | `E0-P0A-SRC1`, `E1-P1A-SRC1`, `E1-P1A-VAL1` | validate P1-B |
| `project_context.py` | mode-aware v1/v2 readiness dispatch reconciled; source blob equals reviewed 01C | mode-aware v1/v2 readiness, pending behavior tests | partial | UNKNOWN | `E0-P0A-SRC2`, `E1-P1A-SRC2`, `E1-P1A-VAL1` | validate P1-B |
| `project_materialization.py` | bounded controlled writer added; source blob equals reviewed 01C | one bounded writer proven by behavior tests | partial | N/A | `E1-P1A-SRC3`, `E1-P1A-VAL1` | validate P1-B |
| `host_projection.py` | existing pure-plan implementation | pure plan preserved | correct | direct | `E0-P0A-SRC4` | preserve-only |
| Projection-only SPEC | absent on fresh main | explicit v2 contract | missing | N/A | `E0-P0A-SRC5` | edit P1-B |
| Projection focused tests | absent on fresh main | behavioral security/lifecycle coverage | missing | N/A | `E0-P0A-SRC5..E0-P0A-SRC6` | edit P1-B |
| C18/C19/FASTPATH/AUTO/workflow | current-main implementations present | preserved and focused-tested | correct/preserve | direct | `E0-P0A-SRC7` | validate P2-A |
| img2threejs/Tripo/providers/secrets | no activation/execution requested or present in projection contract | false/zero/not executed | correct | direct | `E0-P0A-BOUND1` | preserve-only |
| Anvien graph index | analyze failed on disk while writing relations | graph evidence if available | blocked tooling | N/A | `E0-P0A-ANV1` | direct evidence fallback |
| Owner/Thiên Hạ state | outside isolated workspace | zero mutation | preserve-only | N/A | `E0-P0A-ISO1` | do-not-touch |

## Status Refresh Log

| Refresh | Date | Repo Basis | Changed Scope | Status Changes | Evidence | Next Phase Update |
|---------|------|------------|----------------|----------------|----------|-------------------|
| R0 | 2026-08-29 | fresh remote/main before implementation | all 01D scope | initial classification: projection partial/missing; SEC01 preserve-only; Anvien blocked | `E0-P0A-REMOTE1..E0-P0A-ISO1` | P1-A semantic reconciliation allowed; P1-B after source slice |
| R1 | 2026-08-29 | after P1-A source reconciliation | pin/context missing/partial -> implemented pending behavior proof; materializer missing -> present pending behavior proof | `E1-P1A-SRC1..E1-P1A-VAL3` | P1-B focused SPEC/test work is next; no freeze yet |

## Phase Touch Map

| Unit / File / Surface | Plan-Relevant Relationship File | Relationship to Target | Plan Item | Touch Mode | Evidence | Constraint |
|-----------------------|---------------------------------|------------------------|-----------|------------|----------|------------|
| `project_pin.py` | `project_context.py` | consumer | P1-A | edit | `E0-P0A-SRC1..E0-P0A-SRC2` | preserve v1 path |
| `project_pin.py` | `project_materialization.py` | source-of-truth/dependency | P1-A | edit/add | `E0-P0A-SRC5` | one bounded writer only |
| `project_pin.py` | `host_projection.py` | contract dependency | P1-A | inspect-only | `E0-P0A-SRC4` | pure plan unchanged |
| `project_pin.py` | projection SPEC | contract | P1-B | inspect/add | `E0-P0A-SRC5` | exact v2 invariants |
| `project_materialization.py` | `tests/test_p2p_projection_contract.py` | behavior test | P1-B | add | `E0-P0A-SRC6` | isolated temp roots |
| SEC01 surfaces | `.p2p/system/p2p_capabilities/orchestration_policy.py` | adjacent dependency | P1-A/P2-A | preserve-only | `E0-P0A-INT1` | no overwrite/replay |
| current regressions | `tests/test_p2p_adaptive_orchestration.py`, C19, FASTPATH, AUTO, workflow | validation consumer | P2-A | validate-only | `E0-P0A-SRC7` | focused only |
| protected state | Owner checkout/Thiên Hạ/unrelated worktrees | external protected state | all | do-not-touch | `E0-P0A-ISO1` | mutation count zero |

## Detailed Findings

### Fresh authority and intervening commits

Current state: direct fetch and `ls-remote` agree on main SHA/tree. The actual
post-base commits are:

- `76901b24f30988159ebc1b96076512623d09eabd`: `COMPATIBLE_ADJACENT_CHANGE`.
  It adds SEC01 security/reverse capability model, adapter, registry entries,
  orchestration policy binding, manifest evidence, and tests. No projection
  implementation path is touched; preserve all of it.
- `61d51e16628ebdfe156b750a54ca8759b45634a7`:
  `UNRELATED` to implementation, docs-only SEC01 evidence binding. Preserve
  the commit history and do not copy its report into the new candidate.
- `1c84bc41421dcbe502d40b71fead5022231d0541`: `UNRELATED` to implementation,
  one SEC01 Supervisor report. Preserve history; do not use it as projection
  authority and do not copy it into the candidate subject.

Required state: fresh-main descendant candidate retaining all three commits.
Classification: correct; allowed action is semantic projection-only addition.

### Projection surfaces

Current state: fresh main has v1 project pin/context and pure host projection;
the reviewed old 01C source adds the closed v2 branch, one materializer, SPEC,
and focused tests. Required state is the same behavior on fresh main without
copying old reports/plans or overwriting SEC01. Classification: partial/missing.

### External capability boundary

Current state: no task action invokes img2threejs, Tripo, providers, secrets,
or Thiên Hạ. Required state is unchanged false/zero/not executed. Classification:
correct/preserve-only.

## Next Phase Status Decisions

| Plan Item | Actual Status Finding | Required Status / Next-Action Update |
|-----------|-----------------------|--------------------------------------|
| P1-A | v2 pin/context branch and materializer are now reconciled and statically import/compile clean | mark P1-A complete; preserve exact source seam |
| P1-B | SPEC and focused projection/security test are still missing | keep P1-B; add behavioral proof only |
| P2-A | current regressions exist and must be preserved | validate-only; no broad suite |
| P3-A | remote is currently stable but can drift | defer until exact Supervisor PASS, fresh fetch |

## Implementation Gate

- [x] Target scope is listed in Current Status Matrix.
- [x] Each target unit has a status.
- [x] Each status has evidence IDs.
- [x] Relationship count evidence is marked UNKNOWN where Anvien failed.
- [x] Phase Touch Map lists relevant relationship units and touch modes.
- [x] Correct parts are preserve-only.
- [x] Missing/partial parts have exact next actions.
- [x] Anvien blocker is recorded honestly.
- [x] Status Refresh Log has R0 baseline and R1 source-slice refresh rows.
- [x] Protected paths are do-not-touch.

## Final P0 Decision

- [ ] P0 actual-status incomplete. Implementation is blocked.
- [x] P0 complete. Next phase can proceed unchanged.
- [ ] P0 complete. Next phase status, next action, or work steps must be updated before implementation.
- [ ] P0 complete. Target scope is preserve-only.
- [ ] P0 complete. Implementation is blocked by missing authority or evidence.

Decision note:

Fresh remote authority is available and the exact post-base commit set is
understood. The projection contract is missing/partial only on fresh main;
the old reviewed candidate is inspect-only evidence. Semantic reconciliation
may proceed on a new branch from fresh main. Anvien is unavailable because the
isolated index build exhausted disk space, so direct source/diff/test evidence
is required and no graph PASS may be claimed.

P1-A refresh: the reviewed source seam is now present with exact reviewed
source blobs and no SEC01 diff. Behavioral validation remains intentionally
owned by P1-B before the candidate can be frozen.
