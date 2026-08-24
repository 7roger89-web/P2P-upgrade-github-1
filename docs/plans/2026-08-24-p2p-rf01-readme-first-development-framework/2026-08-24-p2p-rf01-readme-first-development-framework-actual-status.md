# RF01 README-First Project Orientation + Development Framework Revision Actual Status

Title: RF01 README-First Project Orientation + Development Framework Revision
Date: 2026-08-24
Status: P1-B Complete / P1-C Pending
Companion plan: `docs/plans/2026-08-24-p2p-rf01-readme-first-development-framework/2026-08-24-p2p-rf01-readme-first-development-framework-plan.md`
Companion evidence: `docs/plans/2026-08-24-p2p-rf01-readme-first-development-framework/2026-08-24-p2p-rf01-readme-first-development-framework-evidence.md`
Companion benchmark: `docs/plans/2026-08-24-p2p-rf01-readme-first-development-framework/2026-08-24-p2p-rf01-readme-first-development-framework-benchmark.md`

## Purpose

This file records the real current state before RF01 implementation. P0 is complete only for the new worktree and only for the scoped orientation/framework slice. It does not authorize release, promotion, host mutation, or edits to sealed `.74` material.

## Freshness / Refresh Rules

Refresh after every implementation slice and before the next slice. Preserve the R0 baseline row and append transitions; do not erase prior evidence.

## Scope

Target scope:

- Root README orientation and deterministic managed-block updater.
- Existing charter/framework/governance development-plane projection.
- Existing package/installer availability lists.
- Focused behavior tests and local validation.

Out of scope:

- `.19` canonical promotion state and `.74` sealed candidate/branch.
- CPT01-R2, CPT01-R3, GitHub host configuration, release build, deployment, publish, merge, external communication.
- `scripts/p2p_workflow.py` and `scripts/p2p_development_control.py` implementation changes.

## Relationship / Impact Evidence

| Unit / File / Surface | File Detail Evidence | Related File Count | Relationship Summary | Impact Note |
|-----------------------|----------------------|--------------------|----------------------|-------------|
| `scripts/p2p_workflow.py` | `E0-P0A-GR2` | 43 inbound refs; 48 linked flows | 301 symbols, 156 local relationships, 1,344 unresolved | HIGH; preserve-only |
| `scripts/p2p_development_control.py` | `E0-P0A-GR3` | 1 inbound ref; 17 linked flows | 151 symbols, 120 local relationships, 703 unresolved | HIGH; preserve-only |
| `scripts/package_release.py` | `E0-P0A-GR4` | 1 inbound ref; 7 linked flows | 92 symbols, 36 local relationships, 430 unresolved | HIGH; edit list entries only |
| `install.ps1` | `E0-P0A-GR5` | 0 graph relationships | parsed shell surface, no symbols/flows | LOW; narrow list entry only |
| `install.sh` | `E0-P0A-GR5` | 0 graph relationships | parsed shell surface, no symbols/flows | LOW; narrow list entry only |
| Root `README.md` | `E0-P0A-DOC1` | new file | missing before RF01 | missing; implement P1-A |
| `scripts/p2p_orientation.py` | `E0-P0A-DOC1` | new file | no existing symbol/consumer | missing; implement P1-A |
| `tests/test_p2p_orientation.py` | `E0-P0A-DOC1` | new file | no existing behavior coverage | missing; implement P1-A |
| Existing charter/framework docs | `E0-P0A-DOC1` | document links inspected | partial product-loop/OXP/RF01 projection | partial; edit P1-B |
| `governance/development-control.json` | `E0-P0A-AUTH1` | consumed by current validator | current reconciliation valid; RF01 plane absent | partial; additive P1-B |
| Historical `source/8.4.6-C/README*` | `E0-P0A-DOC1` | historical snapshot | source reference only | correct; do-not-touch |
| Sealed `.74` ZIP and candidate branch | `E0-P0A-SRC1..SRC3` | protected external subject | exact lineage/artifact verified | correct; do-not-touch |

## Status Rules

| Status | Meaning | Allowed next action |
|--------|---------|---------------------|
| `correct` | Already satisfies the scoped requirement. | Preserve; validate only. |
| `partial` | Existing surface is valid but lacks RF01 content/binding. | Add only missing projection/binding. |
| `missing` | Required RF01 surface does not exist. | Implement narrow missing piece. |
| `blocked` | Authority/evidence is insufficient. | Stop and report exact blocker. |

## Current Status Matrix

| Unit | Current State | Required State | Status | Relationship Count | Evidence | Next Plan Decision |
|------|---------------|----------------|--------|--------------------|----------|--------------------|
| Root `README.md` | managed block present, 132 lines, one marker pair, exact disclaimer and deep links | compact managed orientation block plus preserved owner text | correct | new | `E0-P0A-DOC1`, `E1-P1A-ORIENT2` | preserve |
| Orientation updater | explicit-content replacement/append/idempotence/fail-closed behavior implemented | deterministic updater with no authority invention | correct | `E1-P1A-ORIENT1` | preserve and validate |
| Orientation tests | 7 focused behavior tests pass | trigger/process/observable preservation and marker safety cases | correct | `E1-P1A-TEST1..E1-P1A-TEST2` | preserve and reuse |
| Charter/framework docs | RF01 loop/OXP/state/risk/execution projection recorded in existing surfaces | one RF01 projection with no duplicate governance | correct | document links | `E1-P1B-DOC1`, `E1-P1B-DETECT1` | preserve |
| Development-control JSON | additive `development_plane` parses; current `.19`/`.74` reconciliation unchanged | additive noncanonical RF01 development-plane record, current validator semantics unchanged | correct | 2 inbound refs | `E1-P1B-GOV1..E1-P1B-GR1` | preserve |
| Package allowlists | root README/helper not selected | selected without release build | partial | `E0-P0A-GR4` | edit P1-C |
| Installers | existing installer does not write project README; helper not copied | helper available; no README auto-write | partial | `E0-P0A-GR5` | edit P1-C |
| `scripts/p2p_workflow.py` | current inspected workflow surface is high blast radius | unchanged for RF01 | correct/preserve-only | `E0-P0A-GR2` | preserve |
| `scripts/p2p_development_control.py` | current validator surface is high blast radius and current C-line compatible | unchanged for RF01 | correct/preserve-only | `E0-P0A-GR3` | preserve |
| `.19` canonical baseline | official `.19` with existing SHA and promotion state | unchanged and still canonical | correct/preserve-only | `E0-P0A-AUTH1` | preserve |
| Sealed `.74` source/closure/artifact | exact subject recovered and linked | unchanged; no RF01 mutation | correct/preserve-only | `E0-P0A-SRC1..SRC3` | preserve |
| CPT01-R2 | implemented but host capability blocked | preserved; no R3/bypass | correct/preserve-only | `E0-P0A-AUTH1` | preserve |

## Status Refresh Log

| Refresh | Date | Repo Basis | Changed Scope | Status Changes | Evidence | Next Phase Update |
|---------|------|------------|----------------|----------------|----------|-------------------|
| R0 | 2026-08-24 | closure `54d15cb02b04a0fea35fb7d2fd0af1fd564bb264` in new worktree before RF01 implementation | full RF01 target scope | initial classifications recorded | `E0-P0A-SRC1..E0-P0A-WF1` | P1-A/P1-B/P1-C proceed in order; preserve high-risk surfaces |
| R1 | 2026-08-24 | commits `579a711` plus staged P1-B scope in RF01 worktree | README/updater/tests and framework/governance projection | missing/partial -> correct for P1-A/P1-B; package/install remain partial | `E1-P1A-ORIENT1..E1-P1B-BASELINE1` | P1-C remains list-only; inherited ledger gate remains explicit blocker |

## Phase Touch Map

| Unit / File / Surface | Plan-Relevant Relationship File | Relationship to Target | Plan Item | Touch Mode | Evidence | Constraint |
|-----------------------|---------------------------------|------------------------|-----------|------------|----------|------------|
| Root `README.md` | deep charter/framework links | projection | P1-A | edit | `E0-P0A-DOC1` | managed block only; no authority claim |
| `scripts/p2p_orientation.py` | `tests/test_p2p_orientation.py` | helper/behavior test | P1-A | edit | `E0-P0A-SPEC1` | standard-library; fail closed |
| Existing charter/framework docs | `governance/development-control.json` | source/projection | P1-B | edit | `E0-P0A-DOC1`, `E0-P0A-AUTH1` | no duplicate governance |
| `governance/development-control.json` | `scripts/p2p_development_control.py` | validator consumer | P1-B | edit JSON only | `E0-P0A-GR3` | preserve current validator-compatible fields |
| `scripts/package_release.py` | root README/helper | package allowlist | P1-C | edit list entries only | `E0-P0A-GR4` | no release build |
| `install.ps1` / `install.sh` | existing AGENTS managed block | installer | P1-C | edit list entries only | `E0-P0A-GR5` | no README writer |
| `source/8.4.6-C/README*` | root README | historical reference | P1-A/P1-B | do-not-touch | `E0-P0A-DOC1` | immutable historical source |
| `.74` branch/ZIP | all RF01 files | sealed subject | all | do-not-touch | `E0-P0A-SRC1..SRC3` | exact hash and branch preserved |
| `scripts/p2p_workflow.py` | RF01 orientation | high-risk workflow consumer | all | preserve-only | `E0-P0A-GR2` | no runtime integration in RF01 |

## Detailed Findings

### Exact sealed `.74` development base

Current state:

The exact source/closure commits and artifact hash are locally recoverable in a valid recovery repository. A new worktree was created at the closure commit. The root checkout’s incomplete Git metadata is not used as authority.

Required state:

```text
RF01 edits occur only in codex/p2p-post74-development-01 at closure 54d15cb...
The sealed .74 source/closure branch and artifact remain unchanged.
```

Evidence:

- `E0-P0A-SRC1`: exact commit types, parent relation, and ancestry.
- `E0-P0A-SRC2`: exact artifact SHA-256.
- `E0-P0A-SRC3`: new clean editable worktree.

Relationship and impact:

- Related file count: protected subject, not an editable relationship set.
- Relationship summary: source/closure plus sealed artifact.
- Impact note: any mutation invalidates the RF01 basis and is forbidden.

Classification:

`correct` / preserve-only.

Allowed next action:

Recheck hash/commit/status after implementation; edit only new worktree files.

Forbidden next action:

No sealed candidate edits, branch rewrites, release rebuild, promotion, or CPT01-R3.

### README orientation and updater

Current state:

No root README or dedicated managed-block updater exists. Historical README files are not valid edit targets.

Required state:

```text
One root README projection with exact markers; one deterministic updater that preserves all outside content and fails closed on ambiguous markers.
```

Evidence:

- `E0-P0A-DOC1`: root README/helper missing; historical source present.
- `E0-P0A-SPEC1`: evidence, trust, single-router, no-second-authority constraints.

Relationship and impact:

- Related file count: new files; no existing callers.
- Relationship summary: README links to existing deep authority surfaces; tests call the new helper.
- Impact note: low local scope, but authority wording is sensitive.

Classification:

`missing`.

Allowed next action:

Implement P1-A with explicit content and behavior tests.

Forbidden next action:

Do not put canonical facts, approvals, host claims, or hidden fallback into the README/helper.

### Existing workflow/control/package/install surfaces

Current state:

Workflow and development-control executors are HIGH blast-radius and already carry validated project behavior. Package builder is HIGH but only needs list-entry changes; installers are low-risk parsed surfaces that currently do not auto-write README.

Required state:

```text
RF01 does not integrate into workflow/control executors; package/install availability is explicit and README mutation remains opt-in.
```

Evidence:

- `E0-P0A-GR2`: workflow graph/impact.
- `E0-P0A-GR3`: development-control graph.
- `E0-P0A-GR4`: package builder graph/impact.
- `E0-P0A-GR5`: installer file detail.

Relationship and impact:

- Related file count: workflow 43 inbound refs/48 flows; control 1 inbound/17 flows; package 1 inbound/7 flows; installers 0 graph relationships.
- Relationship summary: shared executors and package/install surfaces.
- Impact note: preserve high-risk code; narrow list edits only.

Classification:

`partial` for package/install binding; `correct` / preserve-only for workflow/control.

Allowed next action:

P1-C list-only edits after the planned gate.

Forbidden next action:

Do not run release builder, installer, deployment, or workflow integration in RF01.

## Next Phase Status Decisions

| Plan Item | Actual Status Finding | Required Status / Next-Action Update |
|-----------|-----------------------|--------------------------------------|
| P1-A | root README/updater/tests are missing | keep P1-A; implement narrowly |
| P1-B | existing framework/governance surfaces are partial; current reconciliation is valid | keep P1-B; additive projection only |
| P1-C | package/install lists are partial; package builder is HIGH | keep P1-C; list-only, no release build |
| P2 | no implementation evidence yet | pending; run only after P1 slices |

## Implementation Gate

- [x] Target scope is listed in Current Status Matrix.
- [x] Each target unit has a status.
- [x] Each status has evidence IDs.
- [x] Each applicable target has relationship count evidence from `file-detail`.
- [x] Phase Touch Map defines touch mode for every plan-relevant relationship unit.
- [x] Correct parts are marked preserve-only.
- [x] Partial and missing parts have exact next actions.
- [x] Blockers are recorded: host authority remains externally blocked and out of scope.
- [x] Next phase status assumptions, actions, and work steps are updated from this file.
- [x] Status Refresh Log has an R0 baseline row.
- [x] If implementation has started, affected rows have been refreshed from latest evidence.

## Final P0 Decision

- [ ] P0 actual-status incomplete. Implementation is blocked.
- [x] P0 complete. Next phase status, next action, and work steps are explicitly defined; P1 can proceed.
- [x] P0 complete. Protected/sealed/high-risk surfaces are preserve-only.
- [ ] P0 complete. Implementation is blocked by missing authority or evidence.

Decision note:

P0 is complete and P1-A/P1-B are complete at scoped implementation level. Exact `.74` subject recovery, branch/worktree isolation, relevant SPEC review, fresh Anvien evidence after generated-index recovery, file-detail/impact evidence, and current authority preservation are recorded. The full legacy framework gate remains blocked by pre-existing capability-ledger defects proven in the parent commit; RF01 does not broaden scope to repair them. P1-C may proceed only as a list-only package/installer binding with no release build. The `.74` development base remains noncanonical and unpromoted; the exact external blocker is `EXTERNAL_HOST_CAPABILITY_LIMITATION`.
