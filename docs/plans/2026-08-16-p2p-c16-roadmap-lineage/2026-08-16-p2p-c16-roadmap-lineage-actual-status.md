# P2P-C16 Durable Development Roadmap and Release Lineage Foundation Actual Status

Title: P2P-C16 Durable Development Roadmap and Release Lineage Foundation
Date: 2026-08-16
Status: PASS — DURABLE_DEVELOPMENT_ROADMAP_AND_LINEAGE_READY
Companion plan: `docs/plans/2026-08-16-p2p-c16-roadmap-lineage/2026-08-16-p2p-c16-roadmap-lineage-plan.md`
Companion evidence: `docs/plans/2026-08-16-p2p-c16-roadmap-lineage/2026-08-16-p2p-c16-roadmap-lineage-evidence.md`
Companion benchmark: `docs/plans/2026-08-16-p2p-c16-roadmap-lineage/2026-08-16-p2p-c16-roadmap-lineage-benchmark.md`

## Purpose

This file records the real current state before C16 implementation. P0 is complete only for the narrow roadmap/lineage scope; it does not claim that the implementation or final supervisor review is complete.

## Freshness / Refresh Rules

Refresh affected rows after each implementation slice, preserve prior evidence IDs, and append a status-refresh row. Do not rewrite historical C14/C15 evidence or infer promotion from filenames.

## Scope

Target scope:

- one compact durable development-control record;
- fresh-session status projection and roadmap mutation provenance;
- explicit release lineage validation before package build writes;
- focused C16 tests and affected regression/evidence.

Out of scope:

- C15 implementation or live delegation certification;
- C17 parallel/background/remote work;
- official `.19` mutation or promotion;
- replacement of existing Goal, project-status, Execution Ledger, FACT_LEDGER, Live Specs, Decision Trace, approval, drift, or doctor authorities;
- external network/download/provider work.

## Relationship / Impact Evidence

| Unit / File / Surface | File Detail Evidence | Related File Count | Relationship Summary | Impact Note |
|-----------------------|----------------------|--------------------|----------------------|-------------|
| `scripts/package_release.py` | `E0-P0A-GRAPH2` | 1 direct affected file; 8 linked flows | version resolution, selected paths, runtime lock, stage, verify, archive | high scope warning; edit only build gate |
| `tests/test_p2p_release_packaging.py` | `E0-P0A-GRAPH3` | 0 upstream affected files; direct sibling suite | historical package/install lifecycle checks | high file warning; narrow tests only |
| `governance/development-control.json` | `E1-P1A-CONTROL1` | 3 provenance entries plus references | compact control record under existing governance authority | correct; preserve existing state |
| `scripts/p2p_development_control.py` | `E1-P1A-VALIDATE1`, `E1-P1B-TEST1` | 87 symbols; 75 local relationships | validator, fresh-session projection, atomic roadmap mutation | correct; no second ledger/router |
| `.p2p/state/project-status.json` | inspected as existing 12 MB state | existing workflow status authority | current workflow state and large trusted snapshot | preserve-only; unchanged |
| `.p2p/state/execution-ledger.jsonl` | inspected as existing append-only state | existing ledger authority | workflow/decision/evidence events | preserve-only; no second ledger |
| official `.19` ZIP outside project root | `E0-P0A-SRC3`/`E0-P0A-SRC4` | protected external artifact | promoted release and approval-bound bytes | do-not-touch |

## Status Rules

| Status | Meaning | Allowed next action |
|--------|---------|---------------------|
| `correct` | Already behaves as required. | Preserve. |
| `partial` | Some required behavior exists, but gaps remain. | Change only missing parts. |
| `wrong` | Current behavior conflicts with C16. | Replace exact unsafe behavior. |
| `missing` | Required C16 behavior does not exist. | Implement only the missing piece. |
| `unbound` | Existing surface is not connected to lineage/roadmap authority. | Bind to the real record only. |
| `fake-or-stub` | Demo/placeholder is represented as real. | Remove or make truthful. |
| `blocked` | Authority/evidence cannot support a safe action. | Stop and record the blocker. |

## Current Status Matrix

| Unit | Current State | Required State | Status | Relationship Count | Evidence | Next Plan Decision |
|------|---------------|----------------|--------|--------------------|----------|--------------------|
| Official baseline | C14 reports and supplied artifact identify `.19` with exact SHA and approval/promotion references | one explicit hash-bound official baseline | correct | protected external artifact | `E0-P0A-SRC3`, `E0-P0A-SRC4` | preserve-only |
| Root/runtime/manifest version | all three source metadata surfaces still say `.15` | development source must declare explicit lineage and block below official | partial/wrong for C16 | package builder flow | `E0-P0A-SRC2`, `E0-P0A-SRC5` | edit P2-A; do not rewrite C15 |
| C15 candidate | unpromoted `.15`, supplied SHA, clean prior verify; base relation to official not durably encoded | explicit candidate lineage with stale regression status | partial | candidate outside source graph | `E0-P0A-SRC4` | record in P1-A; preserve artifact |
| C10-C15 capability state | present in prior reports but not one compact machine-readable recovery record | durable status with C15 foundation/live split | partial | reports/state references | `E0-P0A-SRC4`, `E0-P0A-REG1` | edit P1-A |
| C08 | previous C15 evidence says deferred | `DEFERRED` | correct | prior evidence | `E0-P0A-SRC4` | preserve-only |
| C09 | previous C15 evidence says blocked/unavailable | `BLOCKED / EVENT_EVIDENCE_UNAVAILABLE` | correct | host boundary | `E0-P0A-SRC4` | preserve-only |
| Roadmap | durable C08-C17 and original-family status record now validates | status-enum roadmap with provenance | correct | 25 roadmap items; 3 provenance entries | `E1-P1A-CONTROL1`, `E1-P1B-TEST1` | preserve; C17 remains planned |
| Research decisions | eight named decisions now have explicit status and no vendoring | decision status + pattern-only provenance | correct | 8 registry entries | `E1-P1A-CONTROL1`, `E1-P1B-TEST1` | preserve-only |
| Beginner status surface | deterministic CLI JSON/plain-text projection works in a fresh subprocess | fresh-process JSON/plain-text status | correct | 1 CLI boundary | `E1-P1B-STATUS1`, `E1-P1B-TEST1` | preserve-only |
| Packaging lineage gate | builder now rejects root `.15` before side effects | strict pre-write lineage validation | correct for guard; root intentionally blocked | package flow plus optional embedded validation | `E2-P2A-SRC1`, `E2-P2A-BLOCK1` | preserve guard; owner must rebase metadata before build |
| Filename authority | official hash/version are required; artifact path is informational | filename alone cannot establish authority | correct | package/control boundary | `E2-P2B-TEST1` | preserve-only |
| Canonical identities | existing foundation/doctor/report evidence says exact 8, denominator 8 | retain exact 8/8; Aesthetica optional | correct | existing capability registry | `E0-P0A-SRC4`, `E0-P0A-REG1` | preserve-only |
| Official artifact immutability | `.19` report says unchanged; no source output targets it | unchanged after C16 | correct | protected external artifact | `E0-P0A-SRC3`, `E0-P0A-SRC4` | do-not-touch |
| Git checkpoint | `.git` absent; Anvien detect-changes cannot produce Git diff | record limitation; do not initialize Git | blocked | repository control | `E0-P0A-SRC4`, `E0-P0A-GRAPH1` | report only |

## Status Refresh Log

| Refresh | Date | Repo Basis | Changed Scope | Status Changes | Evidence | Next Phase Update |
|---------|------|------------|----------------|----------------|----------|-------------------|
| R0 | 2026-08-16 | current source, state, reports, Anvien graph/impact before C16 edits | roadmap/lineage/packaging scope | initial classifications above | `E0-P0A-SRC1..E0-P0A-REG1` | P1-A control record; P2-A strict build gate; preserve `.19`/C15 |
| R1 | 2026-08-16 | new control/validator/tests plus fresh Anvien graph | P1-A/P1-B/P2-A/P2-B first implementation slice | missing roadmap/status/guard moved to correct; root remains stale-blocked | `E1-P1A-CONTROL1..E2-P2B-TEST1` | run historical package verification, full regression, drift/doctor/security, supervisor |
| R2 | 2026-08-16 | final source, tests, lock, reports, and Anvien graph | closure and supervisor review | one stale-lock precheck rejected, lock refreshed, final supervisor PASS | `E3-P3A-REG1..E3-P3C-CLOSE1` | stop; no C17 |

## Phase Touch Map

| Unit / File / Surface | Plan-Relevant Relationship File | Relationship to Target | Plan Item | Touch Mode | Evidence | Constraint |
|-----------------------|---------------------------------|------------------------|-----------|------------|----------|------------|
| new `governance/development-control.json` | existing `governance/fact-ledger.json`, Live Specs/locks | governance reference boundary | P1-A/P1-B | edit | `E0-P0A-SRC6` | reference only; no copied authority |
| new `scripts/p2p_development_control.py` | `scripts/p2p_workflow.py`, existing state paths | reader/projection/mutation helper | P1-A/P1-B | edit | `E0-P0A-SRC6` | no second workflow/ledger |
| `scripts/package_release.py` | `governance/development-control.json`, `manifest/package.json`, `VERSION` | packager consumer/source metadata | P2-A | edit | `E0-P0A-SRC2`, `E0-P0A-SRC5`, `E0-P0A-IMPACT1` | validate before writes |
| `tests/test_p2p_development_control.py` | new control module | behavior tests | P1/P2 | edit | `E0-P0A-SRC1` | isolated temp roots |
| `tests/test_p2p_release_packaging.py` | package builder | historical sibling tests | P2-B | inspect/edit only if needed | `E0-P0A-GRAPH3` | do not change old artifact fixtures |
| `.p2p/state/project-status.json` | `scripts/p2p_workflow.py` | existing workflow status authority | all | preserve-only | `E0-P0A-SRC6` | no large rewrite |
| official `.19` ZIP | release/approval reports | protected artifact | all | do-not-touch | `E0-P0A-SRC3` | exact hash must remain |

## Detailed Findings

### Version drift root cause

Current state:

The C14 `.19` promotion was byte-preserving from an isolated candidate; root development metadata remained `.15`. C15 then built from the root checkout. The existing builder correctly mirrored that stale source input and had no explicit official-baseline/lineage guard.

Required state:

```text
RELEASE_BASELINE_NOT_PROPAGATED
  contributing factors: PACKAGER_INPUT_STALE, DEVELOPMENT_BRANCH_METADATA_DRIFT
  response: record the drift; fail future stale builds closed; do not rewrite C15.
```

Evidence:

- `E0-P0A-SRC2`: current source metadata is `.15`.
- `E0-P0A-SRC3`: `.19` promotion was from an isolated candidate and root `.15` remained separate.
- `E0-P0A-SRC4`: C15 candidate is `.15` and unpromoted.
- `E0-P0A-SRC5`: packager reads source version only.

Classification:

`partial/wrong` at the packaging boundary; the prior C15 implementation and artifact are preserve-only historical outputs.

Allowed next action:

Implement an explicit control record and pre-write lineage guard.

Forbidden next action:

Do not rename or mutate the C15 artifact, infer authority from `v15`/`v19` filenames, or promote any candidate.

### Existing authority boundary

Current state:

Existing Goal/project status/Execution Ledger/FACT/Live Specs/Decision Trace/approval/drift/doctor surfaces are authoritative for their own domains. The missing piece is a compact cross-surface development-control projection.

Required state:

```text
one governance control record -> references existing authority -> derived status output
```

Classification:

`missing`, with all existing sources preserve-only.

Allowed next action:

Add only the minimal record/validator/projection and use references.

Forbidden next action:

Do not copy full project status/ledger/FACT content or create a second certification system.

## Next Phase Status Decisions

| Plan Item | Actual Status Finding | Required Status / Next-Action Update |
|-----------|-----------------------|--------------------------------------|
| P1-A | control record and validator now validate official `.19`, roadmap, capability, research, invariant, and canonical boundaries | complete; preserve existing authority |
| P1-B | deterministic status and atomic provenance mutation now exist and are tested in a fresh process | complete; no second ledger/router |
| P2-A | packager now has official baseline/lineage check before build writes; root `.15` is explicitly blocked | complete; owner must update source metadata in a future scoped action |
| P2-B | isolated R1-R18 tests cover control, lineage, mutation, subprocess status, protected hash, and embedded compatibility | complete; regression closure PASS |
| P3 | closure evidence and final supervisor PASS are recorded; one stale-lock precheck was resolved | complete; stop before C17 |

## Implementation Gate

- [x] Target scope is listed in Current Status Matrix.
- [x] Each target unit has a status.
- [x] Each status has evidence IDs.
- [x] Target files have relationship/impact evidence where applicable.
- [x] Phase Touch Map defines touch mode for every plan-relevant unit.
- [x] Correct parts are marked preserve-only.
- [x] Missing/partial/blocked parts have exact next actions.
- [x] Blockers are recorded.
- [x] Next phase status assumptions, next action, and work steps reflect the baseline.
- [x] Status Refresh Log has an R0 baseline row.
- [x] Affected rows refreshed after implementation slices.
- [x] Final supervisor/closure evidence recorded.

## Final P0 Decision

- [ ] P0 actual-status incomplete. Implementation is blocked.
- [x] P0 complete. Next phase status, next action, and work steps must proceed from this evidence.
- [ ] P0 complete. Target scope is preserve-only.
- [ ] P0 complete. Implementation is blocked by missing authority or evidence.

Decision note:

P0 is complete. The requested official `.19` authority is supported by local promotion/approval reports and the exact protected artifact hash; the current `.15` source/candidate drift is real and attributable to an isolated promoted candidate not being propagated into the development packager input. Existing governance/state surfaces are preserved. P1 may implement only the compact control record/projection, and P2 may add the pre-write lineage guard. The current source must remain a truthful stale-blocked development input until a future explicitly bound candidate is prepared.

## Final C16 Decision

- Terminal status: `DURABLE_DEVELOPMENT_ROADMAP_AND_LINEAGE_READY`.
- Supervisor verdict: `PASS` in `reports/supervisor/rp_supervisor_260816_091822_by_gpt-5-codex_p2p-c16-roadmap-lineage.md`.
- C16 boundary: roadmap, fresh-session projection, provenance mutation, and pre-write lineage guard are complete; official `.19` and C15 `.15` candidate remain preserve-only.
- Remaining owner action: for a future release candidate, explicitly rebase/update source metadata from official `.19` and record its lineage. Current `.15` packaging remains blocked by design.
- Stop rule: stop here; do not begin C17 safe bounded parallel foreground execution.
