# P2P-TMPGC01 Current Main Reconciliation Actual Status

Title: P2P-TMPGC01 Current Main Reconciliation
Date: 2026-08-30
Status: complete; READY_FOR_OWNER_REVIEW
Companion plan: `docs/plans/2026-08-30-p2p-tmpgc01-current-main-reconciliation/plan.md`
Companion evidence: `docs/plans/2026-08-30-p2p-tmpgc01-current-main-reconciliation/evidence.md`
Companion benchmark: `docs/plans/2026-08-30-p2p-tmpgc01-current-main-reconciliation/benchmark.md`

## Purpose

Classify the real fresh-main and previous-candidate state before implementation.
This is a living status record and must be refreshed after each implementation
slice.

## Scope

Target scope: fresh canonical main plus the five-file TMPGC invariant family.

Out of scope: owner checkout repair, MPFB, Fast Path, Arena, Game Truyen,
unrelated P2P surfaces, deletion runs, schedule activation, push, promotion,
release, deployment, and cleanup of historical workspaces.

## Relationship / Impact Evidence

Anvien file-detail/impact evidence was unavailable after two isolated refresh
attempts: the native graph loader crashed, then database initialization failed.
Direct Git ancestry, exact path inventory, source inspection, and AST/static
checks are the permitted fallback for this bounded reconciliation.

| Unit / File / Surface | File Detail Evidence | Related File Count | Relationship Summary | Impact Note |
|-----------------------|----------------------|--------------------|----------------------|-------------|
| `fw06_operational_resilience.py` | `E0-P0A-SRC1`, `E0-P0A-TOOL1`, `E1-P1A-SRC1`, `E1-P1B-TEST2` | N/A | Existing FW06 lease/workspace seam extended with exact reviewed TMPGC lifecycle, audit, serialization, and fail-closed delete boundary | high scope warning; verified surgical edit |
| `scripts/p2p_tmp_gc.py` | `E0-P0A-SRC1`, `E1-P1A-SRC1`, `E1-P1B-TEST2` | N/A | Reviewed dry-run-default CLI and inactive Owner-gated schedule preview carried exactly | low; verified |
| `scripts/p2p_live_certification.py` | `E0-P0A-SRC1`, `E1-P1A-SRC1` | N/A | Existing C27 reconcile sibling retains reviewed TMPGC archive/delegation guard | medium; verified scoped change |
| `governance/p2p-tmp-gc-policy.json` | `E0-P0A-SRC1`, `E1-P1A-SRC1`, `E1-P1B-TEST4` | N/A | Reviewed policy contract present with allowlisted `.tmp`, durable roots, grace/pressure, and Owner-gated schedule | low; verified |
| `tests/test_p2p_tmp_gc.py` | `E0-P0A-SRC1`, `E1-P1B-TEST1`, `E1-P1B-TEST2` | N/A | Reviewed focused behavior and fail-closed regression suite present and passing | low; verified |
| Fresh-main unrelated tree | `E0-P0A-GIT2` | N/A | Current canonical files outside TMPGC are preserve-only | preserve-only |

## Status Rules

| Status | Meaning | Allowed next action |
|--------|---------|---------------------|
| `correct` | Already behaves as required. | Preserve. |
| `partial` | Existing seam is correct but TMPGC extension is absent. | Add only missing TMPGC behavior. |
| `missing` | Required TMPGC path does not exist on fresh main. | Add exact reviewed path only. |
| `blocked` | Required authority/tooling is unavailable for a safe claim. | Record limitation; stop if semantic conflict appears. |

## Current Status Matrix

| Unit | Current State | Required State | Status | Relationship Count | Evidence | Next Plan Decision |
|------|---------------|----------------|--------|--------------------|----------|--------------------|
| Fresh `origin/main` | exact SHA/tree fetched and checked | fixed fresh base | correct | N/A | `E0-P0A-GIT2` | preserve as parent |
| FW06 baseline | existing lease/workspace seam without TMPGC extension | reviewed additive TMPGC seam | partial | N/A | `E0-P0A-SRC1` | edit P1-A |
| TMPGC CLI | absent | dry-run-default owner-gated CLI | missing | N/A | `E0-P0A-SRC1` | edit P1-A |
| C27 sibling guard | existing C27 reconcile path | preserve reviewed TMPGC delegation/guard only | partial-awaiting-compare | N/A | `E0-P0A-SRC1` | inspect/edit P1-A only if genuine diff |
| TMPGC policy | absent | reviewed policy JSON | missing | N/A | `E0-P0A-SRC1` | edit P1-A |
| TMPGC focused tests | absent | reviewed fail-closed regressions | missing | N/A | `E0-P0A-SRC1` | add P1-B after source |
| Unrelated current-main surfaces | present | byte/tree-preserved | correct | N/A | `E0-P0A-GIT2` | preserve-only |
| Anvien graph evidence | native refresh unavailable | graph evidence when available | blocked | N/A | `E0-P0A-TOOL1` | use direct fallback; no index repair |

## Status Refresh Log

| Refresh | Date | Repo Basis | Changed Scope | Status Changes | Evidence | Next Phase Update |
|---------|------|------------|----------------|----------------|----------|-------------------|
| R0 | 2026-08-30 | fresh isolated worktree at expected main | all TMPGC family units | initial classification above | `E0-P0A-GIT1..E0-P0A-SAFE1` | P1-A may proceed only with exact source diff |

## Phase Touch Map

| Unit / File / Surface | Plan-Relevant Relationship File | Relationship to Target | Plan Item | Touch Mode | Evidence | Constraint |
|-----------------------|---------------------------------|------------------------|-----------|------------|----------|------------|
| FW06 source | existing FW06 consumers | source-of-truth/runtime contract | P1-A | edit | `E0-P0A-SRC1` | only reviewed TMPGC additive delta |
| TMPGC CLI | FW06 `run_tmp_gc` seam | consumer/entrypoint | P1-A | edit | `E0-P0A-SRC1` | dry-run default; no activation |
| C27 live certification | FW06 cleanup seam | sibling consumer | P1-A | inspect/edit | `E0-P0A-SRC1` | only genuine reviewed change |
| TMPGC policy | CLI/FW06 policy reader | config contract | P1-A | edit | `E0-P0A-SRC1` | exact reviewed policy only |
| TMPGC tests | all five family paths | behavior test | P1-B | edit | `E0-P0A-SRC1` | isolated temp roots only |
| Unrelated current-main paths | all unrelated consumers | preserve-only | P1-A/P1-B | do-not-touch | `E0-P0A-GIT2` | no broad merge or cleanup |

## Detailed Findings

### Fresh canonical main

Current state: fresh fetch resolves exactly to the user-supplied SHA and tree.

Required state:

```text
Candidate parent must remain d661654746f090136f37370f76578ee345b74994.
```

Evidence:

- `E0-P0A-GIT1`: explicit fresh fetch completed in a separate clone.
- `E0-P0A-GIT2`: expected SHA/tree binding passed.

Classification: `correct` / preserve-only.

Allowed next action: create a descendant containing only scoped TMPGC changes.

Forbidden next action: rewrite, merge over, push, or promote canonical main.

### TMPGC implementation family

Current state: implementation is absent from fresh main, while the reviewed
candidate contains the exact scoped source/test/policy blobs.

Required state: carry the reviewed semantics without material change, including
KEEP protections, lifecycle ordering, dry-run defaults, disabled actions,
serialization, semantic audit validation, and C27 delegation boundary.

Classification: `partial` for the existing FW06/C27 seams; `missing` for the
TMPGC-specific CLI, policy, and tests.

Allowed next action: P1-A exact source reconciliation, then P1-B tests.

Forbidden next action: redesign, broad merge, deletion, schedule activation,
automatic GC, or unrelated surface changes.

### Tooling boundary

Current state: Anvien is unavailable in this isolated worktree after the forced
refresh and narrowed refresh failures.

Required state: direct Git/source/AST evidence must cover this bounded task.

Classification: `blocked` for Anvien-only graph claims, not for the scoped code
reconciliation itself.

Allowed next action: record exact limitation and use direct fallback checks.

Forbidden next action: repair the Anvien registry or claim graph counts.

## Next Phase Status Decisions

| Plan Item | Actual Status Finding | Required Status / Next-Action Update |
|-----------|-----------------------|--------------------------------------|
| P1-A | Exact reviewed source/policy/CLI delta applied and committed; no material conflict | complete; preserve exact source semantics |
| P1-B | Exact focused test file added; 67/67 focused tests plus compile/static checks pass | complete; hand exact subject to Supervisor |
| P2-A | no frozen descendant yet | remain pending until exact commit/tree and tests exist |

## Implementation Gate

- [x] Target scope is listed in Current Status Matrix.
- [x] Each target unit has a status.
- [x] Each status has evidence IDs.
- [x] Relationship counts are recorded as N/A with the Anvien failure evidence.
- [x] Phase Touch Map defines touch mode for every relevant unit.
- [x] Correct current-main parts are preserve-only.
- [x] Missing/partial parts have exact next actions.
- [x] Anvien limitation is recorded; no repair is authorized.
- [x] Status Refresh Log has an R0 baseline row.
- [x] P0 implementation gate is complete.

## Final P0 Decision

- [ ] P0 actual-status incomplete. Implementation is blocked.
- [x] P0 complete. Next phase can proceed unchanged.
- [ ] P0 complete. Next phase status, next action, or work steps must be updated before implementation.
- [ ] P0 complete. Target scope is preserve-only.
- [ ] P0 complete. Implementation is blocked by missing authority or evidence.

Decision note: exact fresh main identity is bound, the reviewed candidate scope
is known, fresh main lacks the TMPGC-specific paths, and no genuine conflict is
visible in the existing FW06/C27 baselines. Anvien failure is recorded as a
tooling limitation, with direct evidence required. Proceed to P1-A only; stop if
the applied source delta would alter reviewed semantics.

## Status Refresh R1 - P1 Reconciliation

- Source slice commit: `6b13123f92cd8f9090d138afc8a56f8b271f7273`, parent exactly
  `d661654746f090136f37370f76578ee345b74994`.
- Exact reviewed production blobs match the supplied previous candidate; no
  genuine reconciliation conflict or material semantic change was found.
- Focused result: `67 passed in 38.65s`.
- Compile, AST/JSON/static, and diff checks pass.
- Anvien detect-changes remains unavailable because the isolated worktree is
  not registered; direct Git/source evidence is recorded instead.
- No physical delete run, schedule activation, auto-GC, push, or promotion.
- Supervisor: PASS for exact functional subject `2ec61632c1bfe78a685cb575eaf8495c658fa46b`,
  tree `051faf6438f24dd206d5401b78965215e5fa9dfb`; report is recorded under
  `reports/supervisor/`.
- Closure is evidence-only. Final rebind must preserve the five functional
  blobs and the fresh-main path allowlist.
- Owner approval/promotion remains separate and not requested.

## Final Handoff Boundary

- Functional candidate subject reviewed: `2ec61632c1bfe78a685cb575eaf8495c658fa46b`.
- Functional candidate tree reviewed: `051faf6438f24dd206d5401b78965215e5fa9dfb`.
- Supervisor decision: `PASS` / `READY_FOR_OWNER_REVIEW`.
- Technical readiness does not authorize Owner approval, push, promotion,
  deletion, schedule activation, or automatic GC.
