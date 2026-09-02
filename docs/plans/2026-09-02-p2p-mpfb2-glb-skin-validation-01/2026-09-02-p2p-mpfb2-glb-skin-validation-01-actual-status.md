# P2P-MPFB2-GLB-SKIN-VALIDATION-01 Actual Status

Title: P2P-MPFB2-GLB-SKIN-VALIDATION-01
Date: 2026-09-02
Status: P2-A PASS / P2-B Ready
Companion plan: `docs/plans/2026-09-02-p2p-mpfb2-glb-skin-validation-01/2026-09-02-p2p-mpfb2-glb-skin-validation-01-plan.md`
Companion evidence: `docs/plans/2026-09-02-p2p-mpfb2-glb-skin-validation-01/2026-09-02-p2p-mpfb2-glb-skin-validation-01-evidence.md`
Companion benchmark: `docs/plans/2026-09-02-p2p-mpfb2-glb-skin-validation-01/2026-09-02-p2p-mpfb2-glb-skin-validation-01-benchmark.md`

## Purpose

This file records the real current state before implementation. P0 is complete only after direct artifact/source/spec/impact evidence is recorded. It remains a living status record after implementation begins.

## Freshness / Refresh Rules

P0 is the baseline before the validator edit. Later status refreshes must update only rows affected by completed slices and append a refresh-log entry. Historical Issue 52 evidence does not override fresh Issue 55 artifact parsing.

## Scope

Target scope:

- `.p2p/system/p2p_capabilities/glb_validator.py` optional `skin.skeleton` handling.
- `tests/test_p2p_game_truyen_mpfb_adapter_01.py` directly affected structural cases.
- Existing Oak GLB read-only validation, then one conditional real rerun.

Out of scope:

- `windows_network_isolation.py`, MPFB2 addon lifecycle, `addon_utils.enable`, MPFB2 pin/version, adapter security, provenance model, Game Truyen, artifact mutation, and every later downstream blocker.

## Relationship / Impact Evidence

| Unit / File / Surface | File Detail Evidence | Related File Count | Relationship Summary | Impact Note |
|-----------------------|----------------------|--------------------|----------------------|-------------|
| `.p2p/system/p2p_capabilities/glb_validator.py` | `E0-P0A-GRAPH2` | 0 in isolated Anvien related-file projection | 54 symbols, 21 local call relationships, one linked validation flow; hidden package imports are an analyzer limitation | low blast-radius warning, high-risk source boundary |
| `_validate_mesh_skin` in `glb_validator.py` | `E0-P0A-IMPACT1` | 1 directly affected file | one source function, one `validate_glb_output` process path | LOW Anvien symbol impact; preserve same-function structural checks |
| `tests/test_p2p_game_truyen_mpfb_adapter_01.py` | `E0-P0A-TESTGRAPH1` | 0 in package projection | 139 symbols, 143 local relationships; `GlbValidationTests` directly calls validator | high file-risk warning; edit only direct GLB tests |

## Status Rules

| Status | Meaning | Allowed next action |
|--------|---------|---------------------|
| `correct` | Already behaves as required. | Preserve. |
| `partial` | Some required behavior exists, but gaps remain. | Change only the missing parts. |
| `wrong` | Current behavior conflicts with the contract. | Replace the exact wrong branch. |
| `missing` | Required behavior does not exist. | Implement only the missing piece. |
| `unbound` | Surface exists but is not wired to the real source/flow. | Bind to the real source only. |
| `fake-or-stub` | Prototype, mock, fallback, or placeholder is treated as real. | Remove or replace with truthful behavior. |
| `blocked` | Authority/evidence is unclear. | Stop until resolved. |

## Current Status Matrix

| Unit | Current State | Required State | Status | Relationship Count | Evidence | Next Plan Decision |
|------|---------------|----------------|--------|--------------------|----------|--------------------|
| Canonical source base | Fresh fetched `main` at `c8f4449977987a3288717f9a462dae8967f7246d`, tree `c8ce1ec46ed3399341b38817c5b138604fee1ac2` | exact supplied base/tree | correct | fresh clone; Anvien graph bound to same commit | E0-P0A-REMOTE1 | preserve; P1 edits descend from this base |
| Existing Oak.glb | 9,093,808-byte GLB with expected SHA; candidate validator returns `STRUCTURALLY_VALID`; bytes unchanged during validation | exact existing artifact remains hash-bound and unmutated through P2-A | correct | external preserve-only artifact | E2-P2A-ARTIFACT1..3 | preserve; P2-B may run once |
| Oak skin contract | `skins[0].joints` has 53 valid indices; all joints reachable; one inferred root 52; valid inverse-bind/accessor/skinning structure | retain all structural invariants | correct | artifact evidence; no source relationship | E0-P0A-ARTIFACT4, E0-P0A-SPEC1 | preserve; do not weaken |
| Oak skeleton property | JSON key is omitted; raw value is `ABSENT` | optional omission accepted; explicit malformed values rejected | correct artifact / blocked validator path | artifact-only | E0-P0A-ARTIFACT3 | edit validator branch only |
| Canonical `_validate_mesh_skin` | lines 141-149 now distinguish omitted from present, derive one joint root for omission, and allow nested joints while retaining common-root/connectivity validation | distinguish omitted from present; preserve root policy | correct for P1-A; focused matrix pending | 21 local file relationships; one validation flow | E1-P1A-SRC1..4 | proceed to P1-B |
| Direct GLB test matrix | explicit and omitted skeleton PASS cases plus null/negative/out-of-range/non-integer skeleton and empty/invalid-joint FAIL cases now pass in focused tests | requested focused pass/fail matrix | correct | 143 local test relationships | E1-P1B-TEST1..4 | proceed to P2-A |
| Provenance/recipe | existing sidecar and recipe bind Oak hash and exact recipe; no evidence of defect | remain unchanged and pass candidate validation | correct / preserve-only | inspect-only sibling surface | E0-P0A-ARTIFACT1, E0-P0A-HISTORY1 | preserve; P2-A validates |
| MPFB adapter/addon/firewall | prior bounded surfaces are proven but not revalidated as part of P0; current source is untouched | unchanged through Issue 55; fresh checks only in one conditional rerun | correct / preserve-only | inspect-only sibling surfaces | E0-P0A-HISTORY1 | do not edit; P2-B only if gated |
| Game Truyen | outside this repository/runtime source scope | no read/write/mutation | correct / preserve-only | protected external surface | E0-P0A-HISTORY1 | never touch |

## Status Refresh Log

| Refresh | Date | Repo Basis | Changed Scope | Status Changes | Evidence | Next Phase Update |
|---------|------|------------|----------------|----------------|----------|-------------------|
| R0 | 2026-09-02 | canonical fresh fetch plus direct artifact/source/spec inspection | full Issue 55 scope | initial classifications above | E0-P0A-REMOTE1..HISTORY1 | P1-A may edit only the optional-skeleton branch; P1-B adds direct cases; P2 remains gated |
| R1 | 2026-09-02 | after P1-A source candidate and exact Oak direct validation | `_validate_mesh_skin` selected branch | wrong -> correct for optional selection and nested rooted hierarchy; test matrix remains partial | E1-P1A-SRC1..4 | continue to P1-B; P2-A remains gated on focused tests |
| R2 | 2026-09-02 | after P1-B focused structural tests and compileall | GLB fixture/test matrix | partial -> correct; P1 source/test slices complete | E1-P1B-TEST1..4 | P2-A may run read-only against exact Oak; P2-B remains gated on P2-A |
| R3 | 2026-09-02 | after P2-A exact Oak candidate validation | existing artifact gate | blocked -> PASS; artifact remains byte-identical | E2-P2A-ARTIFACT1..4 | P2-B is runnable exactly once; stop at first new blocker |

## Phase Touch Map

| Unit / File / Surface | Plan-Relevant Relationship File | Relationship to Target | Plan Item | Touch Mode | Evidence | Constraint |
|-----------------------|---------------------------------|------------------------|-----------|------------|----------|------------|
| `glb_validator.py` | `asset_provenance.py` | provenance dependency | P1-A/P2-A | preserve-only / inspect-only | E0-P0A-SRC3 | no provenance change |
| `glb_validator.py` | `character_recipe.py` | recipe dependency | P2-A | preserve-only / inspect-only | E0-P0A-HISTORY1 | use normalized recipe; no recipe change |
| `glb_validator.py` | `tests/test_p2p_game_truyen_mpfb_adapter_01.py` | direct behavior tests | P1-A/P1-B | edit test cases only | E0-P0A-TESTGRAPH1 | no unrelated adapter/firewall test edits |
| `glb_validator.py` | `mpfb_adapter.py` | runtime caller/consumer | P2-A/P2-B | preserve-only / inspect-only | E0-P0A-IMPACT1 | no adapter changes |
| `glb_validator.py` | `windows_network_isolation.py` | runtime security dependency | P2-B | do-not-touch | E0-P0A-HISTORY1 | no firewall reopening |
| existing Oak GLB | runtime output directory | external artifact input/output | P2-A/P2-B | validate-only then one runtime-owned rerun | E0-P0A-ARTIFACT1..4 | no initial mutation; stop at first next blocker |
| Game Truyen | protected external project | immutability boundary | P2-B | do-not-touch | E0-P0A-HISTORY1 | mutation must remain NO |

## Detailed Findings

### Existing Oak GLB and glTF skin

Current state:

The exact artifact hash matches. Its JSON chunk has one skin, 53 joints, 55 nodes, one skin-referencing node `(53, 0)`, and no `skeleton` key. All requested independent structural checks pass, including the inferred common root node 52 and inverse-bind/accessor/skinning attributes.

Required state:

```text
Accept omitted optional skeleton without writing or normalizing the artifact; keep required joints and rooted hierarchy validation.
```

Evidence:

- `E0-P0A-ARTIFACT1`: exact hash/size.
- `E0-P0A-ARTIFACT2..4`: direct JSON and independent structural checks.
- `E0-P0A-SPEC1`: Khronos semantics.

Relationship and impact:

- Related file count: external artifact; no Anvien file relationship.
- Relationship summary: consumed by `validate_glb_output` at runtime, not source-owned.
- Impact note: preserve-only until P2-A; no artifact repair is justified.

Classification:

`correct` / preserve-only artifact; `blocked` only at the current validator boundary.

Allowed next action:

Run P1-A/P1-B source/test repair, then P2-A exact validation.

Forbidden next action:

Do not regenerate or mutate Oak.glb before exact candidate validation.

### Canonical structural validator

Current state:

`_validate_mesh_skin` correctly checks joints, node/mesh/skin references, rooted connectivity, and JOINTS_0/WEIGHTS_0 accessors, but it unconditionally indexes `skin.get("skeleton")`.

Required state:

```text
Absent skeleton: use the hierarchy to preserve rooted-skeleton policy without requiring the optional key.
Present valid integer: range-check and apply existing root/ancestor policy.
Present null or malformed: fail closed.
```

Evidence:

- `E0-P0A-SRC1..3`: direct source lines.
- `E0-P0A-REPRO1`: exact current failure.
- `E0-P0A-IMPACT1`: Anvien impact.

Relationship and impact:

- Related file count: 0 in isolated capability projection; one direct source file and one linked process.
- Relationship summary: `validate_glb_output -> _validate_mesh_skin`; hidden imports are separately inspected.
- Impact note: LOW direct blast-radius warning but high-risk validation boundary; keep the edit surgical.

Classification:

`wrong`; `VALIDATOR_DEFECT=YES` is the current evidence-backed classification.

Allowed next action:

Edit only the existing branch and add direct tests.

Forbidden next action:

Do not add a second validator, export postprocessor, or relax explicit invalid values.

### Direct tests

Current state:

The existing fixture uses an explicit valid skeleton and directly proves missing JOINTS/resource rejection, but does not distinguish omitted from null or cover explicit skeleton edge values and joint-index failures.

Required state:

```text
Focused tests cover omitted and valid skeleton PASS plus explicit null, negative, out-of-range, non-integer, empty-joints, and invalid-joint FAIL cases.
```

Evidence:

- `E0-P0A-TESTGRAPH1`: existing class/file topology.
- `E0-P0A-SRC1`: current validator behavior requires the new matrix.

Relationship and impact:

- Related file count: 0 in package graph projection; 143 local test relationships.
- Relationship summary: `GlbValidationTests` builds temporary GLB/provenance files and calls the canonical validator.
- Impact note: edit only direct fixture/test rows.

Classification:

`partial`.

Allowed next action:

Implement P1-B after P1-A source behavior is present.

Forbidden next action:

Do not broaden into unrelated suite or change the real artifact in tests.

## Next Phase Status Decisions

| Plan Item | Actual Status Finding | Required Status / Next-Action Update |
|-----------|-----------------------|--------------------------------------|
| P1-A | Validator is wrong only for omitted optional skeleton; artifact is structurally coherent and rooted by inference | proceed with surgical source edit; preserve all existing structural checks |
| P1-B | Direct matrix now covers all requested cases and passes | complete; proceed to exact artifact validation |
| P2-A | Candidate validator passes the exact existing Oak GLB and hash/size are unchanged | complete; preserve artifact and proceed to one conditional rerun |
| P2-B | P2-A is PASS; no Issue 55 rerun has occurred | run the existing canonical sequence once and stop at the first different blocker |

## Implementation Gate

- [x] Target scope is listed in Current Status Matrix.
- [x] Each target unit has a status.
- [x] Each status has evidence IDs.
- [x] Each target file has relationship count evidence from `file-detail` when applicable.
- [x] Phase Touch Map lists plan-relevant relationship files that can affect the current phase/slice.
- [x] Phase Touch Map defines touch mode for every plan-relevant relationship unit that may be affected.
- [x] Correct parts are marked preserve-only.
- [x] Partial, missing, wrong, unbound, and fake-or-stub parts have exact next actions.
- [x] Blockers are recorded, if any.
- [x] Next phase status assumptions, next action, and work steps have been updated from this status file when needed.
- [x] Status Refresh Log has an R0 baseline row.
- [x] If implementation has started, affected Current Status Matrix rows have been refreshed from latest evidence.
- [x] If refreshed statuses changed next work, only the stale next-phase status assumptions, next action, or work steps have been updated before the next phase.

## Final P0 Decision

- [ ] P0 actual-status incomplete. Implementation is blocked.
- [x] P0 complete. Next phase status, next action, or work steps must be updated before implementation.
- [ ] P0 complete. Next phase can proceed unchanged.
- [ ] P0 complete. Target scope is preserve-only.
- [ ] P0 complete. Implementation is blocked by missing authority or evidence.

Decision note:

P2-A is PASS. Fresh artifact evidence proves the skeleton property is absent, not null, and the artifact's joints/hierarchy/accessor/skinning structure is coherent. Khronos makes `skin.skeleton` optional; the local P2P rooted-skeleton policy is intentional and is preserved by deriving the unique joint root only when the optional field is omitted. P1-A/P1-B are complete, and the candidate validator passes the exact existing Oak GLB without changing its bytes or hash. P2-B is now permitted exactly once; the rerun must stop at the first different blocker.
